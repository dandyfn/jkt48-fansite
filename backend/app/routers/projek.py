# routers/projek.py
# Single, lagu, projek grup, dan projek luar (film, iklan).
#   GET    /api/projek          -> daftar projek (bisa filter kategori & member_id)
#   GET    /api/projek/{id}     -> detail projek + peserta
#   POST   /api/projek          -> tambah projek + otomatis catat poin peserta
#   DELETE /api/projek/{id}     -> hapus projek + poinnya

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..keamanan import admin_saja
from ..poin import KATEGORI_KE_KODE, catat, hapus_dari_sumber, pastikan_member_ada
from ..schemas import ProjekCreate, ProjekOut

router = APIRouter(prefix="/api/projek", tags=["Projek"])


@router.get("", response_model=list[ProjekOut])
def daftar_projek(kategori: str | None = None, member_id: int | None = None,
                  batas: int | None = None, db: Session = Depends(get_db)):
    query = select(models.Projek).order_by(models.Projek.tanggal_rilis.desc())
    if kategori:
        query = query.where(models.Projek.kategori == kategori)
    if member_id:
        query = query.join(models.MemberProjek).where(models.MemberProjek.member_id == member_id)
    if batas:
        query = query.limit(batas)
    return db.scalars(query).all()


@router.get("/{projek_id}", response_model=ProjekOut)
def detail_projek(projek_id: int, db: Session = Depends(get_db)):
    projek = db.get(models.Projek, projek_id)
    if projek is None:
        raise HTTPException(404, "Projek tidak ditemukan")
    return projek


@router.post("", response_model=ProjekOut, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(admin_saja)])
def tambah_projek(data: ProjekCreate, db: Session = Depends(get_db)):
    pastikan_member_ada(db, [p.member_id for p in data.peserta])

    projek = models.Projek(**data.model_dump(exclude={"peserta"}))
    db.add(projek)
    db.flush()  # minta database memberi id dulu, karena dipakai di bawah

    kode = KATEGORI_KE_KODE[data.kategori]
    for p in data.peserta:
        projek.peserta.append(models.MemberProjek(member_id=p.member_id, is_center=p.is_center))
        catat(db, member_id=p.member_id, kode=kode, tanggal=data.tanggal_rilis,
              sumber_tabel="projek", sumber_id=projek.id, keterangan=data.judul)
        # Bonus center hanya untuk lagu/single JKT48, bukan film/iklan
        if p.is_center and kode == "lagu_baru":
            catat(db, member_id=p.member_id, kode="center", tanggal=data.tanggal_rilis,
                  sumber_tabel="projek", sumber_id=projek.id, keterangan=f"Center: {data.judul}")

    db.commit()
    db.refresh(projek)
    return projek


@router.delete("/{projek_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(admin_saja)])
def hapus_projek(projek_id: int, db: Session = Depends(get_db)):
    projek = db.get(models.Projek, projek_id)
    if projek is None:
        raise HTTPException(404, "Projek tidak ditemukan")
    hapus_dari_sumber(db, "projek", projek_id)
    # Lepas tautan dari SSK yang menunjuk ke projek ini (kalau ada)
    db.execute(update(models.SskEvent).where(models.SskEvent.projek_id == projek_id)
               .values(projek_id=None))
    db.delete(projek)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
