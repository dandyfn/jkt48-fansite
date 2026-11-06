# routers/show.py
#   GET    /api/show          -> daftar show (bisa filter rentang tanggal)
#   POST   /api/show          -> tambah show + otomatis catat poin tiap member yang tampil
#   DELETE /api/show/{id}     -> hapus show + poinnya

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..keamanan import admin_saja
from ..poin import catat, hapus_dari_sumber, pastikan_member_ada
from ..schemas import ShowCreate, ShowOut

router = APIRouter(prefix="/api/show", tags=["Show"])


@router.get("", response_model=list[ShowOut])
def daftar_show(dari: date | None = None, sampai: date | None = None,
                db: Session = Depends(get_db)):
    query = select(models.Show).order_by(models.Show.tanggal.desc())
    if dari:
        query = query.where(models.Show.tanggal >= dari)
    if sampai:
        query = query.where(models.Show.tanggal <= sampai)
    return db.scalars(query).all()


@router.post("", response_model=ShowOut, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(admin_saja)])
def tambah_show(data: ShowCreate, db: Session = Depends(get_db)):
    pastikan_member_ada(db, data.member_ids)

    show = models.Show(nama=data.nama, tanggal=data.tanggal, lokasi=data.lokasi)
    db.add(show)
    db.flush()

    for member_id in data.member_ids:
        show.peserta.append(models.ShowMember(member_id=member_id))
        catat(db, member_id=member_id, kode="show", tanggal=data.tanggal,
              sumber_tabel="show", sumber_id=show.id, keterangan=data.nama)

    db.commit()
    db.refresh(show)
    return show


@router.delete("/{show_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(admin_saja)])
def hapus_show(show_id: int, db: Session = Depends(get_db)):
    show = db.get(models.Show, show_id)
    if show is None:
        raise HTTPException(404, "Show tidak ditemukan")
    hapus_dari_sumber(db, "show", show_id)
    db.delete(show)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
