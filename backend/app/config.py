# config.py
# Membaca pengaturan dari file .env (password admin, alamat database, token IG).
# Dengan cara ini, hal rahasia tidak ditulis langsung di dalam kode.

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Nilai di kanan adalah nilai cadangan kalau tidak ada di .env
    secret_key: str = "dev-secret-ganti-di-env"
    admin_username: str = "admin"
    admin_password: str = "admin"
    database_url: str = "sqlite:///./data/jkt48.db"
    ig_user_id: str = ""
    ig_access_token: str = ""

    # Baca dari file .env; abaikan isi .env yang tidak dikenal
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# Objek ini yang dipakai di file lain: from app.config import settings
settings = Settings()
