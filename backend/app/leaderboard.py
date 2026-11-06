# leaderboard.py
# "Mesin hitung" leaderboard. Tidak menyimpan apa-apa; hanya menghitung.
#
# Skor satu member dalam satu periode =
#     jumlah poin aktivitas di periode itu (show, lagu, center, SSK, iklan, film, kapten baru)
#   + poin kapten aktif   (per minggu selama menjabat)
#   + poin follower       (pertumbuhan % dibanding pertumbuhan tertinggi, maks 30)
#
# Streak = berapa minggu berturut-turut member masuk Top 5 (sampai minggu acuan).

from calendar import monthrange
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from . import models
from .poin import nilai_poin

TOP_STREAK = 5          # masuk Top berapa supaya streak bertambah
BATAS_STREAK = 104      # maksimal menghitung mundur 2 tahun


# ---------------------------------------------------------------------
# Periode
# ---------------------------------------------------------------------

def rentang_periode(jenis: str, tanggal: date) -> tuple[date, date]:
    """Minggu = Senin s/d Minggu. Bulan = tanggal 1 s/d akhir bulan."""
    if jenis == "minggu":
        mulai = tanggal - timedelta(days=tanggal.weekday())
        return mulai, mulai + timedelta(days=6)
    mulai = tanggal.replace(day=1)
    akhir = tanggal.replace(day=monthrange(tanggal.year, tanggal.month)[1])
    return mulai, akhir


def periode_sebelumnya(jenis: str, mulai: date) -> tuple[date, date]:
    return rentang_periode(jenis, mulai - timedelta(days=1))


# ---------------------------------------------------------------------
# Bagian-bagian skor
# ---------------------------------------------------------------------

def _poin_aktivitas(db: Session, mulai: date, selesai: date) -> dict[int, dict[str, float]]:
    """{member_id: {kode: total_poin}} untuk aktivitas di dalam periode."""
    A = models.AktivitasMember
    baris = db.execute(
        select(A.member_id, A.jenis_kode, func.sum(A.poin))
        .where(A.tanggal >= mulai, A.tanggal <= selesai)
        .group_by(A.member_id, A.jenis_kode)
    ).all()
    hasil: dict[int, dict[str, float]] = {}
    for member_id, kode, total in baris:
        hasil.setdefault(member_id, {})[kode] = float(total)
    return hasil


def _minggu_menjabat(jabatan: list[models.Lencana], mulai: date, selesai: date) -> int:
    """Berapa minggu (Senin-Minggu) di dalam periode yang dilalui sebagai kapten."""
    jumlah = 0
    awal_minggu = mulai - timedelta(days=mulai.weekday())
    while awal_minggu <= selesai:
        a = max(awal_minggu, mulai)
        b = min(awal_minggu + timedelta(days=6), selesai)
        for l in jabatan:
            if l.tanggal_mulai <= b and (l.tanggal_selesai or date.max) >= a:
                jumlah += 1
                break
        awal_minggu += timedelta(days=7)
    return jumlah


def _pertumbuhan_follower(db: Session, mulai: date, selesai: date) -> dict[int, float]:
    """
    {member_id: pertumbuhan %}. Follower semua akun aktif dijumlahkan.
      awal  = snapshot terakhir SEBELUM periode dimulai
      akhir = snapshot terakhir DI DALAM periode
    Member tanpa data lengkap tidak dihitung (tidak dapat poin follower).
    """
    S = models.SnapshotSosmed
    akun_aktif = db.scalars(select(models.AkunSosmed).where(models.AkunSosmed.aktif.is_(True))).all()
    total: dict[int, list[int]] = {}
    for akun in akun_aktif:
        awal = db.scalar(select(S.followers).where(S.akun_id == akun.id, S.tanggal < mulai)
                         .order_by(S.tanggal.desc()).limit(1))
        akhir = db.scalar(select(S.followers).where(S.akun_id == akun.id, S.tanggal >= mulai,
                                                    S.tanggal <= selesai)
                          .order_by(S.tanggal.desc()).limit(1))
        if awal is None or akhir is None or awal <= 0:
            continue
        t = total.setdefault(akun.member_id, [0, 0])
        t[0] += awal
        t[1] += akhir
    return {mid: max((akhir - awal) / awal * 100, 0.0) for mid, (awal, akhir) in total.items()}


def _beri_peringkat(baris: list[dict]) -> None:
    """Urutkan skor tertinggi dulu. Skor sama = peringkat sama (1, 1, 3, ...)."""
    baris.sort(key=lambda r: (-r["skor"], r["member"].nama_panggilan.lower()))
    for i, r in enumerate(baris):
        if i > 0 and r["skor"] == baris[i - 1]["skor"]:
            r["peringkat"] = baris[i - 1]["peringkat"]
        else:
            r["peringkat"] = i + 1


# ---------------------------------------------------------------------
# Fungsi utama
# ---------------------------------------------------------------------

def hitung(db: Session, jenis: str, tanggal: date) -> tuple[date, date, list[dict]]:
    """Hitung skor & peringkat semua member aktif/trainee untuk satu periode."""
    mulai, selesai = rentang_periode(jenis, tanggal)
    members = db.scalars(select(models.Member)
                         .where(models.Member.status.in_(["aktif", "trainee"]))).all()

    poin = _poin_aktivitas(db, mulai, selesai)
    pertumbuhan = _pertumbuhan_follower(db, mulai, selesai)
    tertinggi = max(pertumbuhan.values(), default=0.0)
    poin_kapten_aktif = nilai_poin(db, "kapten_aktif")
    poin_follower_maks = nilai_poin(db, "follower")

    L = models.Lencana
    jabatan_kapten: dict[int, list] = {}
    for l in db.scalars(select(L).where(L.jenis == "kapten", L.tanggal_mulai <= selesai)):
        if (l.tanggal_selesai or date.max) >= mulai:
            jabatan_kapten.setdefault(l.member_id, []).append(l)

    baris = []
    for m in members:
        rincian = dict(poin.get(m.id, {}))
        minggu = _minggu_menjabat(jabatan_kapten.get(m.id, []), mulai, selesai)
        if minggu:
            rincian["kapten_aktif"] = minggu * poin_kapten_aktif
        persen = pertumbuhan.get(m.id)
        if persen is not None and tertinggi > 0:
            rincian["follower"] = round(persen / tertinggi * poin_follower_maks, 2)
        baris.append({
            "member": m,
            "skor": round(sum(rincian.values()), 2),
            "rincian": rincian,
            "pertumbuhan_follower_persen": round(persen, 2) if persen is not None else None,
        })
    _beri_peringkat(baris)
    return mulai, selesai, baris


def hitung_streak(db: Session, tanggal_acuan: date) -> dict[int, int]:
    """{member_id: jumlah minggu berturut-turut di Top 5}, dihitung mundur dari minggu acuan."""
    data_pertama = db.scalar(select(func.min(models.AktivitasMember.tanggal)))
    if data_pertama is None:
        return {}
    streak: dict[int, int] = {}
    masih_jalan: set[int] | None = None
    tanggal = tanggal_acuan
    for _ in range(BATAS_STREAK):
        mulai, selesai = rentang_periode("minggu", tanggal)
        if selesai < data_pertama:
            break
        _, _, baris = hitung(db, "minggu", tanggal)
        top = {r["member"].id for r in baris if r["peringkat"] <= TOP_STREAK and r["skor"] > 0}
        masih_jalan = top if masih_jalan is None else (masih_jalan & top)
        if not masih_jalan:
            break
        for mid in masih_jalan:
            streak[mid] = streak.get(mid, 0) + 1
        tanggal = mulai - timedelta(days=1)
    return streak
