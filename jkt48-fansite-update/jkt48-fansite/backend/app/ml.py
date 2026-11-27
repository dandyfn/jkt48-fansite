# ml.py
# Otak machine learning (ML) JKT48 Fan Board. Ada 3 model:
#
#   1. PREDIKSI SENBATSU  -> menebak peluang tiap member masuk lineup single berikutnya.
#                            Jenis: klasifikasi ("masuk" / "tidak masuk"), algoritma Logistic Regression.
#   2. PREDIKSI SSK       -> menebak urutan member di pemilihan member (SSK) berikutnya.
#                            Jenis: regresi (menebak angka skor), algoritma Ridge Regression.
#   3. KELOMPOK MEMBER    -> mengelompokkan member yang pola kariernya mirip + mencari "member mirip".
#                            Jenis: clustering (tanpa kunci jawaban), algoritma K-Means.
#
# Alurnya seperti murid belajar dari soal-soal lama:
#   - "Soal lama"   = keadaan tiap member SEBELUM sebuah single/SSK diumumkan (fitur)
#   - "Kunci jawab" = siapa yang akhirnya masuk senbatsu / peringkat berapa (label)
#   - Model mencari pola fitur -> label, lalu dipakai menebak single/SSK berikutnya.
#
# Hasil latihan disimpan di backend/ml/model_jkt48.joblib.
# Kalau data diubah lewat admin (edit show, tambah projek, dll), model TIDAK otomatis tahu.
# Karena itu ada "sidik data" (seperti sidik jari isi database): kalau sidiknya beda dengan
# saat model dilatih, halaman admin menampilkan "perlu dilatih ulang".

import hashlib
import threading
from datetime import date, datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import silhouette_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sqlalchemy import text
from sqlalchemy.orm import Session

FOLDER_MODEL = Path(__file__).resolve().parent.parent / "ml"
FILE_MODEL = FOLDER_MODEL / "model_jkt48.joblib"
VERSI = 1

# Single dengan lineup lebih dari ini dianggap "lagu seluruh member" (contoh: Ayo Senyumlah = 40 orang),
# jadi tidak dipakai sebagai soal latihan senbatsu karena hampir semua member masuk.
BATAS_LINEUP_NORMAL = 20

# Daftar fitur: (nama kolom, keterangan yang ditampilkan ke pengunjung)
FITUR = [
    ("lama_bulan", "lama di JKT48"),
    ("umur", "umur"),
    ("show_90", "show 3 bulan terakhir"),
    ("show_365", "show 1 tahun terakhir"),
    ("show_total", "total show"),
    ("lagu_365", "lagu & unit 1 tahun terakhir"),
    ("senbatsu_total", "total senbatsu"),
    ("senbatsu_3", "senbatsu di 3 single terakhir"),
    ("center_total", "total center"),
    ("ssk_terbaik", "hasil SSK terbaik"),
    ("ssk_terakhir", "hasil SSK terakhir"),
]
KOLOM_FITUR = [k for k, _ in FITUR]
LABEL_FITUR = dict(FITUR)

# Fitur untuk pengelompokan (dihitung sepanjang karier, bukan per tanggal)
FITUR_KELOMPOK = [
    ("show_per_bulan", "show per bulan"),
    ("lagu_per_tahun", "lagu & unit per tahun"),
    ("rasio_senbatsu", "persentase masuk senbatsu"),
    ("center_total", "jumlah center"),
    ("ssk_terbaik", "hasil SSK terbaik"),
    ("lama_bulan", "lama di JKT48"),
]
NAMA_KELOMPOK = {   # nama kelompok berdasarkan ciri yang paling menonjol
    "show_per_bulan": "Pejuang teater",
    "lagu_per_tahun": "Langganan unit & lagu",
    "rasio_senbatsu": "Senbatsu reguler",
    "center_total": "Wajah utama (center)",
    "ssk_terbaik": "Favorit SSK",
    "lama_bulan": "Senior berpengalaman",
}

_kunci_latih = threading.RLock()
_cache = {"mtime": None, "isi": None}


# =====================================================================
# 1. AMBIL DATA DARI DATABASE
# =====================================================================

def _baca(db: Session, sql: str) -> pd.DataFrame:
    hasil = db.execute(text(sql))
    return pd.DataFrame(hasil.fetchall(), columns=list(hasil.keys()))


def ambil_data(db: Session) -> dict[str, pd.DataFrame]:
    """Semua tabel yang dibutuhkan ML, dalam bentuk tabel pandas (DataFrame)."""
    d = {
        "member": _baca(db, "SELECT id, generasi, status, tanggal_lahir, tanggal_bergabung, tanggal_lulus FROM members"),
        "show": _baca(db, "SELECT s.id, s.tanggal, sm.member_id FROM show s JOIN show_member sm ON sm.show_id = s.id"),
        "projek": _baca(db, """SELECT p.id, p.kategori, p.tanggal_rilis AS tanggal, mp.member_id, mp.is_center
                                FROM projek p JOIN member_projek mp ON mp.projek_id = p.id"""),
        "ssk": _baca(db, """SELECT e.id, e.tanggal_pengumuman AS tanggal, e.jumlah_peringkat, e.jumlah_senbatsu,
                                   h.member_id, h.peringkat
                            FROM ssk_event e JOIN ssk_hasil h ON h.ssk_event_id = e.id"""),
    }
    for nama, tabel in d.items():
        for kolom in ("tanggal", "tanggal_lahir", "tanggal_bergabung", "tanggal_lulus"):
            if kolom in tabel:
                tabel[kolom] = pd.to_datetime(tabel[kolom])
    if len(d["ssk"]):
        j = d["ssk"]["jumlah_peringkat"].fillna(32)
        # Skor SSK 0..1: peringkat 1 = 1.0, peringkat terakhir mendekati 0
        d["ssk"]["skor"] = (j + 1 - d["ssk"]["peringkat"]) / j
    return d


def sidik_data(db: Session) -> str:
    """'Sidik jari' isi database yang dipakai ML. Berubah kalau ada data yang ditambah/diedit/dihapus."""
    h = hashlib.sha256()
    for sql in [
        "SELECT id, generasi, status, tanggal_lahir, tanggal_bergabung, tanggal_lulus FROM members ORDER BY id",
        "SELECT show_id, member_id FROM show_member ORDER BY show_id, member_id",
        "SELECT id, tanggal FROM show ORDER BY id",
        "SELECT id, kategori, tanggal_rilis FROM projek ORDER BY id",
        "SELECT projek_id, member_id, is_center FROM member_projek ORDER BY projek_id, member_id",
        "SELECT id, tanggal_pengumuman, jumlah_peringkat FROM ssk_event ORDER BY id",
        "SELECT ssk_event_id, member_id, peringkat FROM ssk_hasil ORDER BY ssk_event_id, member_id",
    ]:
        for baris in db.execute(text(sql)):
            h.update(repr(tuple(baris)).encode())
    return h.hexdigest()[:16]


def _single_normal(d) -> pd.DataFrame:
    """Daftar single (id, tanggal, jumlah lineup) yang lineup-nya 'normal' (bukan lagu seluruh member)."""
    s = d["projek"][d["projek"]["kategori"] == "single"]
    ringkas = s.groupby("id").agg(tanggal=("tanggal", "first"), lineup=("member_id", "count")).reset_index()
    return ringkas[ringkas["lineup"] <= BATAS_LINEUP_NORMAL].sort_values("tanggal")


# =====================================================================
# 2. FITUR: "keadaan member pada tanggal t" (hanya memakai data SEBELUM t)
# =====================================================================

def kandidat_pada(d, t: pd.Timestamp) -> list[int]:
    """Member yang sudah bergabung dan belum lulus pada tanggal t."""
    m = d["member"]
    aktif = (m["tanggal_bergabung"] <= t) & (m["tanggal_lulus"].isna() | (m["tanggal_lulus"] > t))
    return m.loc[aktif, "id"].tolist()


def fitur_pada(d, t: pd.Timestamp, member_ids: list[int]) -> pd.DataFrame:
    """Satu baris per member: angka-angka yang 'diketahui' tepat sebelum tanggal t."""
    m = d["member"].set_index("id").loc[member_ids]
    sh = d["show"][d["show"]["tanggal"] < t]
    pj = d["projek"][d["projek"]["tanggal"] < t]
    ss = d["ssk"][d["ssk"]["tanggal"] < t] if len(d["ssk"]) else d["ssk"]

    def hitung(df, mulai=None):
        if mulai is not None:
            df = df[df["tanggal"] >= mulai]
        return df.groupby("member_id").size()

    f = pd.DataFrame(index=pd.Index(member_ids, name="member_id"))
    f["lama_bulan"] = ((t - m["tanggal_bergabung"]).dt.days / 30.44).clip(lower=0).values
    f["umur"] = ((t - m["tanggal_lahir"]).dt.days / 365.25).values
    f["show_90"] = hitung(sh, t - pd.Timedelta(days=90))
    f["show_365"] = hitung(sh, t - pd.Timedelta(days=365))
    f["show_total"] = hitung(sh)
    lagu = pj[pj["kategori"].isin(["lagu", "projek_grup", "single"])]
    f["lagu_365"] = hitung(lagu, t - pd.Timedelta(days=365))

    single = _single_normal(d)
    single = single[single["tanggal"] < t]
    pj_single = pj[pj["id"].isin(single["id"])]
    f["senbatsu_total"] = pj_single.groupby("member_id").size()
    tiga = single.tail(3)["id"]
    f["senbatsu_3"] = pj_single[pj_single["id"].isin(tiga)].groupby("member_id").size()
    f["center_total"] = pj[pj["is_center"] == 1].groupby("member_id").size()

    if len(ss):
        f["ssk_terbaik"] = ss.groupby("member_id")["skor"].max()
        terakhir_id = ss.sort_values("tanggal")["id"].iloc[-1]
        f["ssk_terakhir"] = ss[ss["id"] == terakhir_id].set_index("member_id")["skor"]
    else:
        f["ssk_terbaik"] = 0.0
        f["ssk_terakhir"] = 0.0

    f = f.fillna(0)
    f["umur"] = f["umur"].replace(0, np.nan).fillna(f["umur"].replace(0, np.nan).median() or 20)
    return f[KOLOM_FITUR].astype(float)


def _alasan(model, baris: pd.Series, jumlah=2) -> list[dict]:
    """Fitur yang paling MENDORONG tebakan naik untuk satu member.
    Untuk model garis lurus (logistic/ridge): sumbangan = bobot fitur x nilai fitur (yang sudah diskalakan)."""
    skala = model.named_steps["standardscaler"]
    inti = model[-1]
    bobot = inti.coef_[0] if inti.coef_.ndim == 2 else inti.coef_
    z = (baris.values - skala.mean_) / np.where(skala.scale_ == 0, 1, skala.scale_)
    sumbangan = bobot * z
    # "lama di JKT48" dan "umur" tetap dipakai model, tapi tidak dijadikan alasan
    # karena hampir semua member senior akan mendapat alasan yang sama.
    urut = [i for i in np.argsort(-sumbangan) if KOLOM_FITUR[i] not in ("lama_bulan", "umur")]
    return [{"fitur": KOLOM_FITUR[i], "label": LABEL_FITUR[KOLOM_FITUR[i]], "nilai": _format_nilai(KOLOM_FITUR[i], baris.iloc[i])}
            for i in urut[:jumlah] if sumbangan[i] > 0]


def _format_nilai(kolom: str, nilai: float) -> str:
    if kolom == "lama_bulan":
        return f"{nilai / 12:.1f} tahun".replace(".", ",")
    if kolom == "umur":
        return f"{nilai:.0f} tahun"
    if kolom.startswith("ssk"):
        return "belum pernah masuk" if nilai == 0 else f"skor {nilai * 100:.0f}/100"
    return f"{nilai:.0f}x"


# =====================================================================
# 3. MODEL 1: PREDIKSI SENBATSU
# =====================================================================

def _data_latih_senbatsu(d, daftar_single) -> tuple[pd.DataFrame, pd.Series]:
    X, y = [], []
    for _, s in daftar_single.iterrows():
        kandidat = kandidat_pada(d, s["tanggal"])
        if not kandidat:
            continue
        f = fitur_pada(d, s["tanggal"], kandidat)
        lineup = set(d["projek"].loc[d["projek"]["id"] == s["id"], "member_id"])
        X.append(f)
        y.append(pd.Series([1 if i in lineup else 0 for i in f.index], index=f.index))
    return pd.concat(X), pd.concat(y)


def _model_senbatsu():
    return make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, class_weight="balanced"))


def latih_senbatsu(d, hari_ini: pd.Timestamp) -> dict:
    single = _single_normal(d)
    if len(single) < 6:
        return {"siap": False, "pesan": "Butuh minimal 6 single untuk melatih model senbatsu."}

    # --- Uji jujur (backtest): pura-pura belum tahu 5 single terakhir, lalu cek tebakannya ---
    uji = []
    for i in range(max(5, len(single) - 5), len(single)):
        lama, target = single.iloc[:i], single.iloc[i]
        X, y = _data_latih_senbatsu(d, lama)
        model = _model_senbatsu().fit(X, y)
        kandidat = kandidat_pada(d, target["tanggal"])
        f = fitur_pada(d, target["tanggal"], kandidat)
        peluang = pd.Series(model.predict_proba(f)[:, 1], index=f.index)
        k = int(target["lineup"])
        tebakan = set(peluang.nlargest(k).index)
        asli = set(d["projek"].loc[d["projek"]["id"] == target["id"], "member_id"])
        uji.append({"projek_id": int(target["id"]), "tanggal": target["tanggal"].date().isoformat(),
                    "kursi": k, "benar": len(tebakan & asli)})

    # --- Model final: belajar dari SEMUA single ---
    X, y = _data_latih_senbatsu(d, single)
    model = _model_senbatsu().fit(X, y)

    kandidat = d["member"].loc[d["member"]["status"] != "eks", "id"].tolist()
    f = fitur_pada(d, hari_ini, kandidat)
    peluang = pd.Series(model.predict_proba(f)[:, 1], index=f.index).sort_values(ascending=False)
    kursi = int(single.tail(5)["lineup"].median())

    prediksi = [{"member_id": int(mid), "peluang": round(float(p) * 100, 1),
                 "masuk": i < kursi, "alasan": _alasan(model, f.loc[mid])}
                for i, (mid, p) in enumerate(peluang.items())]

    benar = sum(u["benar"] for u in uji)
    total = sum(u["kursi"] for u in uji)
    return {
        "siap": True, "model": model, "kursi": kursi, "prediksi": prediksi,
        "jumlah_soal": int(len(single)), "jumlah_baris": int(len(X)),
        "uji": uji, "akurasi": round(benar / total * 100, 1) if total else None,
        "bobot": _bobot(model),
    }


def _bobot(model) -> list[dict]:
    """Seberapa besar pengaruh tiap fitur (positif = menaikkan tebakan)."""
    inti = model[-1]
    bobot = inti.coef_[0] if inti.coef_.ndim == 2 else inti.coef_
    urut = sorted(zip(KOLOM_FITUR, bobot), key=lambda x: -abs(x[1]))
    return [{"fitur": k, "label": LABEL_FITUR[k], "bobot": round(float(b), 3)} for k, b in urut]


# =====================================================================
# 4. MODEL 2: PREDIKSI SSK
# =====================================================================

def _data_latih_ssk(d, daftar_event) -> tuple[pd.DataFrame, pd.Series]:
    X, y = [], []
    for _, e in daftar_event.iterrows():
        kandidat = kandidat_pada(d, e["tanggal"])
        f = fitur_pada(d, e["tanggal"], kandidat)
        skor = d["ssk"][d["ssk"]["id"] == e["id"]].set_index("member_id")["skor"]
        X.append(f)
        y.append(pd.Series([float(skor.get(i, 0.0)) for i in f.index], index=f.index))
    return pd.concat(X), pd.concat(y)


def _model_ssk():
    return make_pipeline(StandardScaler(), Ridge(alpha=3.0))


def latih_ssk(d, hari_ini: pd.Timestamp) -> dict:
    if not len(d["ssk"]):
        return {"siap": False, "pesan": "Belum ada data SSK."}
    event = (d["ssk"].groupby("id")
             .agg(tanggal=("tanggal", "first"), peringkat=("jumlah_peringkat", "first"),
                  senbatsu=("jumlah_senbatsu", "first"))
             .reset_index().sort_values("tanggal"))
    if len(event) < 3:
        return {"siap": False, "pesan": "Butuh minimal 3 SSK untuk melatih model SSK."}

    # --- Uji jujur: latih dengan SSK lama, tebak SSK terakhir ---
    lama, target = event.iloc[:-1], event.iloc[-1]
    X, y = _data_latih_ssk(d, lama)
    model = _model_ssk().fit(X, y)
    kandidat = kandidat_pada(d, target["tanggal"])
    f = fitur_pada(d, target["tanggal"], kandidat)
    tebak = pd.Series(model.predict(f), index=f.index).sort_values(ascending=False)
    asli = d["ssk"][d["ssk"]["id"] == target["id"]].sort_values("peringkat")
    k = int(target["senbatsu"] or 16)
    benar = len(set(tebak.head(k).index) & set(asli.head(k)["member_id"]))
    # Korelasi urutan (Spearman): 1 = urutannya sama persis, 0 = tidak berhubungan
    gabung = pd.DataFrame({"tebak": tebak.rank(ascending=False)}).join(
        asli.set_index("member_id")["peringkat"], how="inner")
    korelasi = float(gabung["tebak"].corr(gabung["peringkat"], method="spearman")) if len(gabung) > 2 else None

    # --- Model final dari SEMUA SSK ---
    X, y = _data_latih_ssk(d, event)
    model = _model_ssk().fit(X, y)
    kandidat = d["member"].loc[d["member"]["status"] != "eks", "id"].tolist()
    f = fitur_pada(d, hari_ini, kandidat)
    skor = pd.Series(model.predict(f), index=f.index).sort_values(ascending=False)
    jumlah_peringkat = int(event.iloc[-1]["peringkat"] or 32)
    kursi = int(event.iloc[-1]["senbatsu"] or 16)

    prediksi = [{"member_id": int(mid), "peringkat": i + 1, "skor": round(float(s) * 100, 1),
                 "senbatsu": i < kursi, "alasan": _alasan(model, f.loc[mid])}
                for i, (mid, s) in enumerate(skor.head(jumlah_peringkat).items())]
    return {
        "siap": True, "model": model, "prediksi": prediksi, "kursi": kursi,
        "jumlah_peringkat": jumlah_peringkat, "jumlah_soal": int(len(event)), "jumlah_baris": int(len(X)),
        "uji": {"tanggal": target["tanggal"].date().isoformat(), "kursi": k, "benar": benar,
                "korelasi": round(korelasi, 2) if korelasi is not None else None},
        "bobot": _bobot(model),
    }


# =====================================================================
# 5. MODEL 3: KELOMPOK MEMBER (clustering) + MEMBER MIRIP
# =====================================================================

def fitur_karier(d, hari_ini: pd.Timestamp) -> pd.DataFrame:
    """Satu baris per member (aktif & eks): ringkasan sepanjang kariernya."""
    m = d["member"].set_index("id")
    akhir = m["tanggal_lulus"].fillna(hari_ini)
    bulan = ((akhir - m["tanggal_bergabung"]).dt.days / 30.44).clip(lower=1)

    f = pd.DataFrame(index=m.index)
    f.index.name = "member_id"
    f["lama_bulan"] = bulan
    show = d["show"].groupby("member_id").size()
    f["show_per_bulan"] = show.reindex(f.index).fillna(0) / bulan
    lagu = d["projek"][d["projek"]["kategori"].isin(["lagu", "projek_grup", "single"])].groupby("member_id").size()
    f["lagu_per_tahun"] = lagu.reindex(f.index).fillna(0) / (bulan / 12)

    single = _single_normal(d)
    pj_single = d["projek"][d["projek"]["id"].isin(single["id"])]
    masuk = pj_single.groupby("member_id").size().reindex(f.index).fillna(0)
    peluang = pd.Series(
        [((single["tanggal"] >= m.at[i, "tanggal_bergabung"]) & (single["tanggal"] <= akhir[i])).sum() for i in f.index],
        index=f.index)
    f["rasio_senbatsu"] = np.where(peluang > 0, masuk / peluang.clip(lower=1), 0).clip(max=1)
    f["center_total"] = d["projek"][d["projek"]["is_center"] == 1].groupby("member_id").size().reindex(f.index).fillna(0)
    f["ssk_terbaik"] = (d["ssk"].groupby("member_id")["skor"].max().reindex(f.index).fillna(0)
                        if len(d["ssk"]) else 0.0)
    return f[[k for k, _ in FITUR_KELOMPOK]].astype(float)


def latih_kelompok(d, hari_ini: pd.Timestamp) -> dict:
    f = fitur_karier(d, hari_ini)
    # log1p meredam angka yang "meledak" (misal center 20x vs 0x) supaya tidak mendominasi jarak
    olah = f.copy()
    olah["center_total"] = np.log1p(olah["center_total"])
    skala = StandardScaler().fit(olah)
    Z = skala.transform(olah)

    # Coba 4, 5, 6 kelompok; ambil yang paling "rapi" (silhouette tertinggi)
    terbaik = None
    for k in (4, 5, 6):
        km = KMeans(n_clusters=k, n_init=20, random_state=42).fit(Z)
        nilai = silhouette_score(Z, km.labels_)
        if terbaik is None or nilai > terbaik[1]:
            terbaik = (km, nilai)
    km, silhouette = terbaik

    # Beri nama tiap kelompok dari ciri yang paling menonjol (pusat kelompok, dalam skala z)
    kelompok, terpakai = [], set()
    kolom = list(f.columns)
    for c in range(km.n_clusters):
        pusat = km.cluster_centers_[c]
        anggota = f.index[km.labels_ == c]
        if pusat.max() < 0.25:
            nama = "Member baru / karier singkat"
        else:
            urut = [kolom[i] for i in np.argsort(-pusat)]
            ciri = next((u for u in urut if NAMA_KELOMPOK[u] not in terpakai), urut[0])
            nama = NAMA_KELOMPOK[ciri]
        if nama in terpakai:
            nama = f"{nama} {sum(1 for t in terpakai if t.startswith(nama)) + 1}"
        terpakai.add(nama)
        menonjol = [{"fitur": kolom[i], "label": dict(FITUR_KELOMPOK)[kolom[i]]}
                    for i in np.argsort(-pusat)[:2] if pusat[i] > 0.25]
        rata = f.loc[anggota].mean()
        kelompok.append({
            "id": int(c), "nama": nama, "menonjol": menonjol, "jumlah": int(len(anggota)),
            "rata": {k: round(float(v), 2) for k, v in rata.items()},
        })

    return {
        "siap": True, "kmeans": km, "skala": skala, "Z": Z,
        "member_ids": [int(i) for i in f.index], "label": [int(x) for x in km.labels_],
        "fitur": {int(i): {k: round(float(v), 2) for k, v in f.loc[i].items()} for i in f.index},
        "kelompok": kelompok, "silhouette": round(float(silhouette), 3),
    }


def cari_mirip(hasil_kelompok: dict, member_id: int, jumlah=5) -> list[dict]:
    """Member lain yang jaraknya paling dekat di 'peta' fitur karier."""
    ids = hasil_kelompok["member_ids"]
    if member_id not in ids:
        return []
    Z = hasil_kelompok["Z"]
    i = ids.index(member_id)
    jarak = np.linalg.norm(Z - Z[i], axis=1)
    urut = [j for j in np.argsort(jarak) if j != i][:jumlah]
    return [{"member_id": ids[j], "kemiripan": round(float(100 / (1 + jarak[j])), 1),
             "kelompok": hasil_kelompok["label"][j]} for j in urut]


# =====================================================================
# 6. LATIH SEMUA + SIMPAN + MUAT
# =====================================================================

def latih_semua(db: Session) -> dict:
    with _kunci_latih:
        mulai = datetime.now()
        hari_ini = pd.Timestamp(date.today()) + pd.Timedelta(days=1)   # +1: data hari ini ikut terhitung
        d = ambil_data(db)
        isi = {
            "versi": VERSI,
            "dilatih_pada": mulai.isoformat(timespec="seconds"),
            "sidik": sidik_data(db),
            "jumlah_data": {"member": int(len(d["member"])), "show": int(d["show"]["id"].nunique()),
                            "projek": int(d["projek"]["id"].nunique()),
                            "ssk": int(d["ssk"]["id"].nunique()) if len(d["ssk"]) else 0},
            "senbatsu": latih_senbatsu(d, hari_ini),
            "ssk": latih_ssk(d, hari_ini),
            "kelompok": latih_kelompok(d, hari_ini),
        }
        isi["durasi_detik"] = round((datetime.now() - mulai).total_seconds(), 1)
        FOLDER_MODEL.mkdir(exist_ok=True)
        joblib.dump(isi, FILE_MODEL)
        _cache.update(mtime=FILE_MODEL.stat().st_mtime, isi=isi)
        return isi


def muat(db: Session) -> dict:
    """Ambil model yang sudah dilatih. Kalau filenya belum ada (misal server baru/di-reset),
    model otomatis dilatih dulu, jadi halaman prediksi tidak pernah kosong."""
    if FILE_MODEL.exists():
        mtime = FILE_MODEL.stat().st_mtime
        if _cache["mtime"] != mtime:
            isi = joblib.load(FILE_MODEL)
            if isi.get("versi") != VERSI:
                return latih_semua(db)
            _cache.update(mtime=mtime, isi=isi)
        return _cache["isi"]
    with _kunci_latih:   # kalau 4 permintaan datang bersamaan, cukup 1 yang melatih
        if FILE_MODEL.exists():
            return muat(db)
        return latih_semua(db)
