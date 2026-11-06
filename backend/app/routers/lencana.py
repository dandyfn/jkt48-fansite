# routers/lencana.py
# Kapten, wakil kapten, dll.
#   GET    /api/lencana          -> daftar lencana (bisa filter member_id)
#   POST   /api/lencana          -> tambah lencana (kapten -> poin "diangkat jadi kapten")
#   PUT    /api/lencana/{id}     -> ubah, misalnya isi tanggal_selesai saat jabatan berakhir
#   DELETE /api/lencana/{id}     -> hapus lencana + poinnya
#
# Catatan: poin mingguan "masih menjabat kapten" dihitung saat membuat leaderboard,
# bukan disimpan di sini.

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..keamanan import admin_saja
from ..poin import catat, hapus_dari_sumber, pastikan_member_ada
from ..schemas import LencanaCreate, LencanaOut, LencanaUpdate

router = APIRouter(prefix="/api/lencana", tags=["Lencana"])


def _catat_poin_lencana(db: Session, lencana: models.Lencana) -> None:
    if lencana.jenis == "kapten":
        catat(db, member_id=lencana.member_id, kode="kapten_baru",
              tanggal=lencana.tanggal_mulai, sumber_tabel="lencana", sumber_id=lencana.id,
              keterangan=f"Diangkat kapten {lencana.keterangan or ''}".strip())


def _cek_tanggal(mulai, selesai) -> None:
    if selesai is not None and selesai < mulai:
        raise HTTPException(400, "tanggal_selesai tidak boleh sebelum tanggal_mulai")


@router.get("", response_model=list[LencanaOut])
def daftar_lencana(member_id: int | None = None, db: Session = Depends(get_db)):
    query = select(models.Lencana).order_by(models.Lencana.tanggal_mulai.desc())
    if member_id:
        query = query.where(models.Lencana.member_id == member_id)
    return db.scalars(query).all()


@router.post("", response_model=LencanaOut, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(admin_saja)])
def tambah_lencana(data: LencanaCreate, db: Session = Depends(get_db)):
    pastikan_member_ada(db, [data.member_id])
    _cek_tanggal(data.tanggal_mulai, data.tanggal_selesai)
    lencana = models.Lencana(**data.model_dump())
    db.add(lencana)
    db.flush()
    _catat_poin_lencana(db, lencana)
    db.commit()
    db.refresh(lencana)
    return lencana


@router.put("/{lencana_id}", response_model=LencanaOut, dependencies=[Depends(admin_saja)])
def ubah_lencana(lencana_id: int, data: LencanaUpdate, db: Session = Depends(get_db)):
    lencana = db.get(models.Lencana, lencana_id)
    if lencana is None:
        raise HTTPException(404, "Lencana tidak ditemukan")
    for kolom, nilai in data.model_dump(exclude_unset=True).items():
        setattr(lencana, kolom, nilai)
    _cek_tanggal(lencana.tanggal_mulai, lencana.tanggal_selesai)
    # Tanggal mulai bisa berubah -> catat ulang poinnya supaya tanggalnya ikut benar
    hapus_dari_sumber(db, "lencana", lencana.id)
    _catat_poin_lencana(db, lencana)
    db.commit()
    db.refresh(lencana)
    return lencana


@router.delete("/{lencana_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(admin_saja)])
def hapus_lencana(lencana_id: int, db: Session = Depends(get_db)):
    lencana = db.get(models.Lencana, lencana_id)
    if lencana is None:
        raise HTTPException(404, "Lencana tidak ditemukan")
    hapus_dari_sumber(db, "lencana", lencana_id)
    db.delete(lencana)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
