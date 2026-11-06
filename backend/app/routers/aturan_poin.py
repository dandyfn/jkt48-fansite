# routers/aturan_poin.py
#   GET /api/aturan-poin          -> lihat semua aturan poin
#   PUT /api/aturan-poin/{kode}   -> ubah nilai poin (admin)
#
# Saat nilai poin diubah, semua aktivitas lama dengan kode yang sama
# ikut dihitung ulang, supaya leaderboard tetap adil.

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..keamanan import admin_saja
from ..schemas import JenisPoinOut, JenisPoinUpdate

router = APIRouter(prefix="/api/aturan-poin", tags=["Aturan Poin"])

# Kode yang poinnya dihitung pakai rumus, bukan angka tetap
KODE_RUMUS = {"ssk", "follower"}


@router.get("", response_model=list[JenisPoinOut])
def daftar_aturan(db: Session = Depends(get_db)):
    return db.scalars(select(models.JenisPoin)).all()


@router.put("/{kode}", response_model=JenisPoinOut, dependencies=[Depends(admin_saja)])
def ubah_aturan(kode: str, data: JenisPoinUpdate, db: Session = Depends(get_db)):
    aturan = db.get(models.JenisPoin, kode)
    if aturan is None:
        raise HTTPException(404, "Aturan poin tidak ditemukan")
    for kolom, nilai in data.model_dump(exclude_unset=True).items():
        setattr(aturan, kolom, nilai)

    if data.poin is not None and kode not in KODE_RUMUS:
        db.execute(update(models.AktivitasMember)
                   .where(models.AktivitasMember.jenis_kode == kode)
                   .values(poin=data.poin))
    db.commit()
    db.refresh(aturan)
    return aturan
