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
    # SQLite secara default TIDAK mengecek relasi antar tabel (foreign key).
    # Baris ini menyalakannya, supaya misalnya tidak bisa mencatat show
    # untuk member yang tidak ada.
    @event.listens_for(engine, "connect")
    def _nyalakan_foreign_key(dbapi_conn, _record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

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
