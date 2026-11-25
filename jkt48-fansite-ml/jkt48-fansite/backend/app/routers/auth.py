# routers/auth.py
# Endpoint login admin:
#   POST /api/auth/login -> kirim username & password, dapat token
#   GET  /api/auth/saya  -> cek token masih berlaku atau tidak

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from ..keamanan import admin_saja, buat_token, cek_login

router = APIRouter(prefix="/api/auth", tags=["Login Admin"])


@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends()):
    if not cek_login(form.username, form.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username atau password salah",
        )
    return {"access_token": buat_token(form.username), "token_type": "bearer"}


@router.get("/saya")
def siapa_saya(username: str = Depends(admin_saja)):
    return {"username": username, "pesan": "Token masih berlaku"}
