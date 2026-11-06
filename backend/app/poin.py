# poin.py
# "Mesin pencatat poin". Dipakai oleh router projek, show, SSK, dan lencana.
# Setiap kali admin menginput sesuatu, fungsi catat() menulis satu baris
# di tabel aktivitas_member. Leaderboard nanti tinggal menjumlahkan tabel itu.

from datetime import date

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from . import models

# Kategori projek -> kode aturan poin yang dipakai
KATEGORI_KE_KODE = {
    "single": "lagu_baru",
    "lagu": "lagu_baru",
    "projek_grup": "lagu_baru",
    "film": "film",
    "iklan": "iklan",
}


def nilai_poin(db: Session, kode: str) -> float:
    """Ambil nilai poin terbaru dari tabel jenis_poin."""
    aturan = db.get(models.JenisPoin, kode)
    if aturan is None:
        raise HTTPException(500, f"Aturan poin '{kode}' belum ada. Jalankan buat_tabel.py.")
    return aturan.poin


def catat(db: Session, *, member_id: int, kode: str, tanggal: date,
          sumber_tabel: str, sumber_id: int, keterangan: str | None = None,
          nilai: float | None = None, poin: float | None = None) -> None:
    """Tulis satu aktivitas. Kalau poin tidak diberikan, ambil dari aturan poin."""
    if poin is None:
        poin = nilai_poin(db, kode)
    db.add(models.AktivitasMember(
        member_id=member_id, jenis_kode=kode, tanggal=tanggal,
        nilai=nilai, poin=poin, keterangan=keterangan,
        sumber_tabel=sumber_tabel, sumber_id=sumber_id,
    ))


def hapus_dari_sumber(db: Session, sumber_tabel: str, sumber_id: int) -> None:
    """Hapus semua poin yang berasal dari satu data (misal show #12 dihapus)."""
    db.execute(delete(models.AktivitasMember).where(
        models.AktivitasMember.sumber_tabel == sumber_tabel,
        models.AktivitasMember.sumber_id == sumber_id,
    ))


def pastikan_member_ada(db: Session, member_ids: list[int]) -> None:
    """Tolak request kalau ada id member yang salah ketik / tidak ada."""
    if len(member_ids) != len(set(member_ids)):
        raise HTTPException(400, "Ada member yang dimasukkan lebih dari sekali")
    ada = set(db.scalars(select(models.Member.id).where(models.Member.id.in_(member_ids))))
    hilang = sorted(set(member_ids) - ada)
    if hilang:
        raise HTTPException(400, f"Member dengan id {hilang} tidak ditemukan")
