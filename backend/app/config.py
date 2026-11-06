# config.py
# Membaca pengaturan dari file .env (password admin, alamat database, token IG).
# Dengan cara ini, hal rahasia tidak ditulis langsung di dalam kode.

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Nilai di kanan adalah nilai cadangan kalau tidak ada di .env
    secret_key: str = "dev-secret-ganti-di-env"
    admin_username: str = "admin"
    # Password admin TIDAK disimpan apa adanya, tapi dalam bentuk hash.
    # Buat hash-nya dengan: .venv\Scripts\python.exe buat_hash_password.py
    admin_password_hash: str = ""
    token_berlaku_menit: int = 480  # token login berlaku 8 jam
    database_url: str = "sqlite:///./data/jkt48.db"
    ig_user_id: str = ""
    ig_access_token: str = ""

    # Baca dari file .env; abaikan isi .env yang tidak dikenal
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# Objek ini yang dipakai di file lain: from app.config import settings
settings = Settings()
