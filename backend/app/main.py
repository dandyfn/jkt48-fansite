# main.py
# Pintu masuk API. Uvicorn menjalankan objek "app" di file ini.
#
# Cara jalan (dari folder backend):
#   .venv\Scripts\python.exe -m uvicorn app.main:app --reload
# Lalu buka: http://127.0.0.1:8000/docs

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .penjadwal import hentikan_penjadwal, mulai_penjadwal
from .routers import (aktivitas, aturan_poin, auth, grup, infografis, leaderboard, lencana,
                      members, ml, projek, show, sosmed, ssk)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Dijalankan SEKALI saat API menyala ...
    if settings.fitur_follower:
        mulai_penjadwal()      # tarik follower IG otomatis tiap Minggu
    yield
    # ... dan sekali saat API dimatikan
    hentikan_penjadwal()


app = FastAPI(
    title="JKT48 Fan Board API",
    description="Backend untuk web user dan web admin fansite JKT48.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS: izinkan web-user & web-admin (dibuka lewat Live Server) memanggil API ini.
# Saat development semua alamat diizinkan; nanti dibatasi saat deploy.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Daftarkan kelompok endpoint
app.include_router(auth.router)
app.include_router(members.router)
app.include_router(projek.router)
app.include_router(show.router)
app.include_router(ssk.router)
app.include_router(lencana.router)
app.include_router(aktivitas.router)
app.include_router(aturan_poin.router)
app.include_router(leaderboard.router)
if settings.fitur_follower:
    app.include_router(sosmed.router)
app.include_router(grup.router)
app.include_router(infografis.router)
app.include_router(ml.router)


@app.get("/", tags=["Umum"])
def cek_api():
    return {"pesan": "API JKT48 Fan Board berjalan", "dokumentasi": "/docs"}
