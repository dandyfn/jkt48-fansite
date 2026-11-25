# routers/ml.py
# Endpoint machine learning. Otaknya ada di app/ml.py.
#
#   GET  /api/ml/status            -> kapan model dilatih, hasil uji, dan apakah data sudah berubah
#   POST /api/ml/latih             -> (admin) latih ulang ketiga model dari data terbaru
#   GET  /api/ml/senbatsu          -> prediksi peluang masuk senbatsu single berikutnya
#   GET  /api/ml/ssk               -> prediksi urutan SSK berikutnya
#   GET  /api/ml/kelompok          -> kelompok member (clustering) beserta anggotanya
#   GET  /api/ml/mirip/{member_id} -> 5 member dengan pola karier paling mirip
#
# Model TIDAK dilatih ulang otomatis setiap ada data baru, supaya halaman tetap cepat.
# Admin menekan tombol "Latih ulang" di web admin (halaman Model AI) setelah mengedit data.

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .. import ml, models
from ..database import get_db
from ..keamanan import admin_saja

router = APIRouter(prefix="/api/ml", tags=["Machine Learning"])


def _info_member(db: Session) -> dict[int, dict]:
    """Nama, foto, team, dll. diambil langsung dari database (bukan dari file model),
    supaya perubahan nama/foto langsung tampil tanpa melatih ulang."""
    hasil = {}
    for m in db.scalars(select(models.Member).options(selectinload(models.Member.lencana))):
        hasil[m.id] = {"id": m.id, "nama_panggilan": m.nama_panggilan, "foto_url": m.foto_url,
                       "generasi": m.generasi, "team": m.team, "status": m.status, "kapten": m.kapten}
    return hasil


def _ringkas_status(isi: dict, db: Session) -> dict:
    s, k, g = isi["senbatsu"], isi["ssk"], isi["kelompok"]
    sidik_sekarang = ml.sidik_data(db)
    return {
        "dilatih_pada": isi["dilatih_pada"],
        "durasi_detik": isi.get("durasi_detik"),
        "jumlah_data": isi["jumlah_data"],
        "perlu_latih_ulang": sidik_sekarang != isi["sidik"],
        "senbatsu": {"siap": s["siap"], "pesan": s.get("pesan"), "akurasi": s.get("akurasi"),
                     "jumlah_soal": s.get("jumlah_soal"), "jumlah_baris": s.get("jumlah_baris"),
                     "uji": s.get("uji"), "bobot": s.get("bobot")},
        "ssk": {"siap": k["siap"], "pesan": k.get("pesan"), "uji": k.get("uji"),
                "jumlah_soal": k.get("jumlah_soal"), "jumlah_baris": k.get("jumlah_baris"), "bobot": k.get("bobot")},
        "kelompok": {"siap": g["siap"], "silhouette": g.get("silhouette"),
                     "jumlah_kelompok": len(g.get("kelompok", []))},
    }


@router.get("/status")
def status_model(db: Session = Depends(get_db)):
    return _ringkas_status(ml.muat(db), db)


@router.post("/latih")
def latih_ulang(db: Session = Depends(get_db), _admin: str = Depends(admin_saja)):
    return _ringkas_status(ml.latih_semua(db), db)


@router.get("/senbatsu")
def prediksi_senbatsu(db: Session = Depends(get_db)):
    isi = ml.muat(db)
    s = isi["senbatsu"]
    if not s["siap"]:
        raise HTTPException(404, s["pesan"])
    info = _info_member(db)
    return {
        "dilatih_pada": isi["dilatih_pada"], "kursi": s["kursi"], "akurasi": s["akurasi"],
        "uji": s["uji"],
        "prediksi": [{**p, "member": info[p["member_id"]]} for p in s["prediksi"] if p["member_id"] in info],
    }


@router.get("/ssk")
def prediksi_ssk(db: Session = Depends(get_db)):
    isi = ml.muat(db)
    k = isi["ssk"]
    if not k["siap"]:
        raise HTTPException(404, k["pesan"])
    info = _info_member(db)
    return {
        "dilatih_pada": isi["dilatih_pada"], "kursi": k["kursi"], "jumlah_peringkat": k["jumlah_peringkat"],
        "uji": k["uji"],
        "prediksi": [{**p, "member": info[p["member_id"]]} for p in k["prediksi"] if p["member_id"] in info],
    }


@router.get("/kelompok")
def kelompok_member(db: Session = Depends(get_db)):
    isi = ml.muat(db)
    g = isi["kelompok"]
    info = _info_member(db)
    anggota = {c["id"]: [] for c in g["kelompok"]}
    for mid, label in zip(g["member_ids"], g["label"]):
        if mid in info:
            anggota[label].append({**info[mid], "fitur": g["fitur"][mid]})
    # Member aktif & trainee ditaruh di depan, lalu urut nama
    for daftar in anggota.values():
        daftar.sort(key=lambda m: (m["status"] == "eks", m["nama_panggilan"].lower()))
    return {
        "dilatih_pada": isi["dilatih_pada"], "silhouette": g["silhouette"],
        "kelompok": [{**c, "anggota": anggota[c["id"]]} for c in g["kelompok"]],
    }


@router.get("/mirip/{member_id}")
def member_mirip(member_id: int, db: Session = Depends(get_db)):
    isi = ml.muat(db)
    g = isi["kelompok"]
    info = _info_member(db)
    if member_id not in info:
        raise HTTPException(404, "Member tidak ditemukan")
    if member_id not in g["member_ids"]:
        raise HTTPException(404, "Member ini belum ada saat model dilatih. Latih ulang model dulu.")
    nama_kelompok = {c["id"]: c["nama"] for c in g["kelompok"]}
    label_saya = g["label"][g["member_ids"].index(member_id)]
    return {
        "member": {**info[member_id], "fitur": g["fitur"][member_id], "kelompok": nama_kelompok[label_saya]},
        "mirip": [{**m, "member": {**info[m["member_id"]], "fitur": g["fitur"][m["member_id"]]},
                   "nama_kelompok": nama_kelompok[m["kelompok"]]}
                  for m in ml.cari_mirip(g, member_id) if m["member_id"] in info],
    }
