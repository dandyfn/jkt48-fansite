# penjadwal.py
# "Alarm otomatis": setiap Minggu jam 23:00 (waktu laptop), tarik follower Instagram.
# Alarm hanya berbunyi selama API menyala. Kalau hari Minggu laptop mati,
# saat API dinyalakan lagi dan data sudah lebih dari 6 hari, langsung ditarik saat itu.

from apscheduler.schedulers.background import BackgroundScheduler

from .database import SessionLocal
from .instagram import ig_siap, perlu_kejar, tarik_semua

_penjadwal: BackgroundScheduler | None = None


def _tugas_tarik_ig() -> None:
    with SessionLocal() as db:
        hasil = tarik_semua(db)
    print(f"[Penjadwal] Tarik follower Instagram: {hasil['pesan']}")


def mulai_penjadwal() -> None:
    global _penjadwal
    if not ig_siap():
        print("[Penjadwal] IG_USER_ID / IG_ACCESS_TOKEN belum diisi -> tarik otomatis IG nonaktif")
        return
    _penjadwal = BackgroundScheduler()
    _penjadwal.add_job(_tugas_tarik_ig, "cron", day_of_week="sun", hour=23, minute=0,
                       id="tarik_ig_mingguan")
    with SessionLocal() as db:
        if perlu_kejar(db):
            _penjadwal.add_job(_tugas_tarik_ig, id="kejar_ig")  # tanpa jadwal = jalan sekarang
            print("[Penjadwal] Data IG sudah lama, menarik sekarang...")
    _penjadwal.start()
    print("[Penjadwal] Aktif: tarik follower IG setiap Minggu 23:00")


def hentikan_penjadwal() -> None:
    global _penjadwal
    if _penjadwal and _penjadwal.running:
        _penjadwal.shutdown(wait=False)
    _penjadwal = None
