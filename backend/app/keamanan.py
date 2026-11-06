# keamanan.py
# Semua urusan login admin:
#   1. cek_password   : mencocokkan password yang diketik dengan hash di .env
#   2. buat_token     : membuat "tiket masuk" (JWT) setelah login berhasil
#   3. admin_saja     : "satpam" yang memeriksa tiket di setiap request
#                       tambah/ubah/hapus. Tanpa tiket valid -> ditolak (401).

import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash

from .config import settings

ALGORITMA = "HS256"
_hasher = PasswordHash.recommended()  # memakai argon2

# Memberi tahu FastAPI/Swagger: token didapat dari endpoint login ini
skema_oauth2 = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def buat_hash(password: str) -> str:
    return _hasher.hash(password)


def cek_login(username: str, password: str) -> bool:
    if not settings.admin_password_hash:
        return False  # hash belum diisi di .env -> tidak ada yang bisa login
    # compare_digest: membandingkan teks dengan aman (tahan serangan timing)
    username_cocok = secrets.compare_digest(username, settings.admin_username)
    try:
        password_cocok = _hasher.verify(password, settings.admin_password_hash)
    except Exception:
        password_cocok = False
    return username_cocok and password_cocok


def buat_token(username: str) -> str:
    kedaluwarsa = datetime.now(timezone.utc) + timedelta(minutes=settings.token_berlaku_menit)
    isi_token = {"sub": username, "exp": kedaluwarsa}
    return jwt.encode(isi_token, settings.secret_key, algorithm=ALGORITMA)


def admin_saja(token: str = Depends(skema_oauth2)) -> str:
    """Dipasang di endpoint yang hanya boleh dipakai admin."""
    ditolak = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token tidak valid atau sudah kedaluwarsa. Silakan login lagi.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        isi = jwt.decode(token, settings.secret_key, algorithms=[ALGORITMA])
    except jwt.PyJWTError:
        raise ditolak
    if isi.get("sub") != settings.admin_username:
        raise ditolak
    return isi["sub"]
