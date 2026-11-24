# routers/show.py
#   GET    /api/show          -> daftar show (bisa filter rentang tanggal)
#   POST   /api/show          -> tambah show + otomatis catat poin tiap member yang tampil
#   PUT    /api/show/{id}     -> ubah show (nama, tanggal, lokasi, member) + hitung ulang poinnya
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


def _isi_member(db: Session, show: models.Show, data: ShowCreate) -> None:
    """Pasang member yang tampil + tulis nota poin show (dipakai saat tambah dan saat edit)."""
    for member_id in data.member_ids:
        show.peserta.append(models.ShowMember(member_id=member_id))
        catat(db, member_id=member_id, kode="show", tanggal=data.tanggal,
              sumber_tabel="show", sumber_id=show.id, keterangan=data.nama)


@router.post("", response_model=ShowOut, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(admin_saja)])
def tambah_show(data: ShowCreate, db: Session = Depends(get_db)):
    pastikan_member_ada(db, data.member_ids)
    show = models.Show(nama=data.nama, tanggal=data.tanggal, lokasi=data.lokasi)
    db.add(show)
    db.flush()
    _isi_member(db, show, data)
    db.commit()
    db.refresh(show)
    return show


@router.put("/{show_id}", response_model=ShowOut, dependencies=[Depends(admin_saja)])
def ubah_show(show_id: int, data: ShowCreate, db: Session = Depends(get_db)):
    """Ganti seluruh isi show. Nota poin lama dihapus lalu ditulis ulang."""
    show = db.get(models.Show, show_id)
    if show is None:
        raise HTTPException(404, "Show tidak ditemukan")
    pastikan_member_ada(db, data.member_ids)

    hapus_dari_sumber(db, "show", show_id)              # 1. buang nota poin lama
    show.peserta.clear()                                # 2. buang daftar member lama
    db.flush()
    show.nama, show.tanggal, show.lokasi = data.nama, data.tanggal, data.lokasi   # 3. ganti isinya
    _isi_member(db, show, data)                         # 4. pasang member baru + nota baru
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
