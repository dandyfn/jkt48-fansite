# routers/aktivitas.py
#   GET /api/aktivitas  -> daftar semua poin yang tercatat (bisa difilter)
#
# Endpoint ini hanya untuk MELIHAT. Aktivitas dibuat otomatis oleh
# router projek, show, SSK, dan lencana, bukan diinput langsung.

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..schemas import AktivitasOut

router = APIRouter(prefix="/api/aktivitas", tags=["Aktivitas & Poin"])


@router.get("", response_model=list[AktivitasOut])
def daftar_aktivitas(
    member_id: int | None = None,
    jenis: str | None = None,
    dari: date | None = None,
    sampai: date | None = None,
    batas: int = Query(default=200, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    A = models.AktivitasMember
    query = select(A).order_by(A.tanggal.desc(), A.id.desc()).limit(batas)
    if member_id:
        query = query.where(A.member_id == member_id)
    if jenis:
        query = query.where(A.jenis_kode == jenis)
    if dari:
        query = query.where(A.tanggal >= dari)
    if sampai:
        query = query.where(A.tanggal <= sampai)
    return db.scalars(query).all()
