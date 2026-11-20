# sosmed.py
# Fungsi bantu media sosial yang dipakai router dan penarik Instagram.

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models

# Perubahan follower lebih dari ini (%) dianggap mencurigakan (mungkin salah ketik).
# Nanti diganti dengan model ML deteksi anomali.
BATAS_PERINGATAN_PERSEN = 30


def simpan_snapshot(db: Session, akun_id: int, tanggal: date, followers: int) -> str:
    """Simpan follower pada tanggal tertentu. Kalau tanggal itu sudah ada, diperbarui."""
    S = models.SnapshotSosmed
    lama = db.scalar(select(S).where(S.akun_id == akun_id, S.tanggal == tanggal))
    if lama:
        lama.followers = followers
        return "diperbarui"
    db.add(S(akun_id=akun_id, tanggal=tanggal, followers=followers))
    return "baru"


def follower_sebelum(db: Session, akun_id: int, tanggal: date) -> int | None:
    """Follower terakhir SEBELUM tanggal tertentu."""
    S = models.SnapshotSosmed
    return db.scalar(select(S.followers).where(S.akun_id == akun_id, S.tanggal < tanggal)
                     .order_by(S.tanggal.desc()).limit(1))


def persen_perubahan(sebelum: int | None, sekarang: int) -> float | None:
    if not sebelum:
        return None
    return round((sekarang - sebelum) / sebelum * 100, 2)
