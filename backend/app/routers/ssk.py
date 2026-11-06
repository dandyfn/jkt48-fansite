# routers/ssk.py
# Pemilihan member (SSK) untuk sebuah lagu.
#   GET    /api/ssk          -> daftar SSK
#   GET    /api/ssk/{id}     -> detail SSK + peringkat
#   POST   /api/ssk          -> input hasil SSK + otomatis catat poin
#   DELETE /api/ssk/{id}     -> hapus SSK + poinnya

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..keamanan import admin_saja
from ..poin import catat, hapus_dari_sumber, pastikan_member_ada
from ..schemas import SskCreate, SskOut
from ..utils import poin_ssk

router = APIRouter(prefix="/api/ssk", tags=["SSK"])


@router.get("", response_model=list[SskOut])
def daftar_ssk(db: Session = Depends(get_db)):
    return db.scalars(select(models.SskEvent)
                      .order_by(models.SskEvent.tanggal_pengumuman.desc())).all()


@router.get("/{ssk_id}", response_model=SskOut)
def detail_ssk(ssk_id: int, db: Session = Depends(get_db)):
    ssk = db.get(models.SskEvent, ssk_id)
    if ssk is None:
        raise HTTPException(404, "SSK tidak ditemukan")
    return ssk


@router.post("", response_model=SskOut, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(admin_saja)])
def tambah_ssk(data: SskCreate, db: Session = Depends(get_db)):
    pastikan_member_ada(db, [h.member_id for h in data.hasil])
    peringkat = [h.peringkat for h in data.hasil]
    if len(peringkat) != len(set(peringkat)):
        raise HTTPException(400, "Ada peringkat yang dipakai lebih dari satu member")
    if data.projek_id is not None and db.get(models.Projek, data.projek_id) is None:
        raise HTTPException(400, f"Projek dengan id {data.projek_id} tidak ditemukan")

    ssk = models.SskEvent(judul=data.judul, tanggal_pengumuman=data.tanggal_pengumuman,
                          projek_id=data.projek_id)
    db.add(ssk)
    db.flush()

    for h in data.hasil:
        ssk.hasil.append(models.SskHasil(member_id=h.member_id, peringkat=h.peringkat))
        catat(db, member_id=h.member_id, kode="ssk", tanggal=data.tanggal_pengumuman,
              sumber_tabel="ssk", sumber_id=ssk.id, nilai=h.peringkat,
              poin=poin_ssk(h.peringkat), keterangan=f"{data.judul} (peringkat {h.peringkat})")

    db.commit()
    db.refresh(ssk)
    return ssk


@router.delete("/{ssk_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(admin_saja)])
def hapus_ssk(ssk_id: int, db: Session = Depends(get_db)):
    ssk = db.get(models.SskEvent, ssk_id)
    if ssk is None:
        raise HTTPException(404, "SSK tidak ditemukan")
    hapus_dari_sumber(db, "ssk", ssk_id)
    db.delete(ssk)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
