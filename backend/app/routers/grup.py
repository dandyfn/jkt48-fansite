# routers/grup.py
#   GET /api/grup  -> profil JKT48 + statistik + rilis terbaru + projek terbaru (section 2)
#   PUT /api/grup  -> ubah profil grup (admin)

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..keamanan import admin_saja
from ..schemas import GrupOut, GrupUpdate

router = APIRouter(prefix="/api/grup", tags=["Profil Grup"])


def _jumlah_projek(db: Session, kategori: list[str]) -> int:
    return db.scalar(select(func.count(models.Projek.id))
                     .where(models.Projek.kategori.in_(kategori))) or 0


def _jumlah_member(db: Session, status: str) -> int:
    return db.scalar(select(func.count(models.Member.id))
                     .where(models.Member.status == status)) or 0


def _terbaru(db: Session, kategori: list[str]):
    return db.scalar(select(models.Projek).where(models.Projek.kategori.in_(kategori))
                     .order_by(models.Projek.tanggal_rilis.desc()).limit(1))


@router.get("", response_model=GrupOut)
def profil_grup(db: Session = Depends(get_db)):
    info = db.scalar(select(models.InfoGrup).limit(1))
    return {
        "info": {
            "nama": info.nama if info else "JKT48",
            "deskripsi": info.deskripsi if info else None,
            "tanggal_dibentuk": info.tanggal_dibentuk if info else None,
            "logo_url": info.logo_url if info else None,
        },
        "statistik": {
            "jumlah_single": _jumlah_projek(db, ["single"]),
            "jumlah_lagu": _jumlah_projek(db, ["single", "lagu"]),
            "member_aktif": _jumlah_member(db, "aktif"),
            "member_trainee": _jumlah_member(db, "trainee"),
            "member_eks": _jumlah_member(db, "eks"),
        },
        "rilis_terbaru": _terbaru(db, ["single", "lagu"]),
        "projek_terbaru": _terbaru(db, ["projek_grup"]),
    }


@router.put("", response_model=GrupOut, dependencies=[Depends(admin_saja)])
def ubah_profil_grup(data: GrupUpdate, db: Session = Depends(get_db)):
    info = db.scalar(select(models.InfoGrup).limit(1))
    if info is None:
        info = models.InfoGrup()
        db.add(info)
    for kolom, nilai in data.model_dump(exclude_unset=True).items():
        setattr(info, kolom, nilai)
    db.commit()
    return profil_grup(db)
