# routers/members.py
# Semua endpoint untuk data member:
#   GET    /api/members        -> daftar member (bisa difilter status & team)
#   GET    /api/members/{id}   -> detail satu member
#   POST   /api/members        -> tambah member
#   PUT    /api/members/{id}   -> ubah member
#   DELETE /api/members/{id}   -> hapus member
#
# GET terbuka untuk umum (dipakai web user).
# POST/PUT/DELETE dikunci: hanya admin yang sudah login (punya token).

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..keamanan import admin_saja
from ..schemas import MemberCreate, MemberOut, MemberUpdate

router = APIRouter(prefix="/api/members", tags=["Member"])


def _ambil_atau_404(db: Session, member_id: int) -> models.Member:
    member = db.get(models.Member, member_id)
    if member is None:
        raise HTTPException(status_code=404, detail="Member tidak ditemukan")
    return member


@router.get("", response_model=list[MemberOut])
def daftar_member(
    status_member: str | None = Query(default=None, alias="status"),
    team: str | None = None,
    db: Session = Depends(get_db),
):
    query = select(models.Member).order_by(models.Member.generasi, models.Member.nama_panggilan)
    if status_member:
        query = query.where(models.Member.status == status_member)
    if team:
        query = query.where(models.Member.team == team)
    return db.scalars(query).all()


@router.get("/{member_id}", response_model=MemberOut)
def detail_member(member_id: int, db: Session = Depends(get_db)):
    return _ambil_atau_404(db, member_id)


@router.post("", response_model=MemberOut, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(admin_saja)])
def tambah_member(data: MemberCreate, db: Session = Depends(get_db)):
    member = models.Member(**data.model_dump())
    db.add(member)
    db.commit()
    db.refresh(member)  # ambil ulang supaya id yang baru dibuat ikut terisi
    return member


@router.put("/{member_id}", response_model=MemberOut, dependencies=[Depends(admin_saja)])
def ubah_member(member_id: int, data: MemberUpdate, db: Session = Depends(get_db)):
    member = _ambil_atau_404(db, member_id)
    # exclude_unset: hanya kolom yang benar-benar dikirim yang diubah
    for kolom, nilai in data.model_dump(exclude_unset=True).items():
        setattr(member, kolom, nilai)
    db.commit()
    db.refresh(member)
    return member


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(admin_saja)])
def hapus_member(member_id: int, db: Session = Depends(get_db)):
    member = _ambil_atau_404(db, member_id)
    db.delete(member)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Member masih punya data terkait (show, projek, dll). Ubah statusnya menjadi 'eks' saja.",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
