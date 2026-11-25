# database.py
# Menyiapkan koneksi ke database. Semua file lain cukup memakai:
#   - engine       : "kabel" penghubung ke file database
#   - SessionLocal : pembuka "sesi" untuk membaca/menulis data
#   - Base         : induk dari semua tabel di models.py

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings

pakai_sqlite = settings.database_url.startswith("sqlite")

engine = create_engine(
    settings.database_url,
    # SQLite butuh opsi ini supaya bisa dipakai FastAPI (banyak request sekaligus)
    connect_args={"check_same_thread": False} if pakai_sqlite else {},
)

if pakai_sqlite:
    @event.listens_for(engine, "connect")
    def _atur_koneksi(dbapi_conn, _record):
        # 1) SQLite secara default TIDAK mengecek relasi antar tabel (foreign key).
        #    Baris ini menyalakannya, supaya misalnya tidak bisa mencatat show
        #    untuk member yang tidak ada.
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
        # 2) Matikan pengaturan transaksi bawaan driver sqlite3 Python, karena
        #    tidak mendukung SAVEPOINT dengan benar. Transaksi diatur SQLAlchemy
        #    (lihat _mulai_transaksi). Ini resep resmi dari dokumentasi SQLAlchemy.
        dbapi_conn.isolation_level = None

    @event.listens_for(engine, "begin")
    def _mulai_transaksi(conn):
        conn.exec_driver_sql("BEGIN")

SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db():
    """Dipakai FastAPI nanti: buka sesi saat ada request, tutup setelah selesai."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
