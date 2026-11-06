# main.py
# Pintu masuk API. Uvicorn menjalankan objek "app" di file ini.
#
# Cara jalan (dari folder backend):
#   .venv\Scripts\python.exe -m uvicorn app.main:app --reload
# Lalu buka: http://127.0.0.1:8000/docs

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import auth, members

app = FastAPI(
    title="JKT48 Fan Board API",
    description="Backend untuk web user dan web admin fansite JKT48.",
    version="0.1.0",
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


@app.get("/", tags=["Umum"])
def cek_api():
    return {"pesan": "API JKT48 Fan Board berjalan", "dokumentasi": "/docs"}
