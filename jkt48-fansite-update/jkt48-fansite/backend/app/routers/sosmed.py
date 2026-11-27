# routers/sosmed.py
#   GET    /api/sosmed/akun                  -> daftar akun (filter platform/sumber/member).
#                                               Dipakai halaman "input cepat" di web admin.
#   POST   /api/sosmed/akun                  -> daftarkan akun sosmed member (admin)
#   PUT    /api/sosmed/akun/{id}             -> ubah username/sumber/aktif (admin)
#   DELETE /api/sosmed/akun/{id}             -> hapus akun + riwayat follower-nya (admin)
#   GET    /api/sosmed/akun/{id}/riwayat     -> riwayat follower satu akun
#   POST   /api/sosmed/follower/massal       -> input follower banyak akun sekaligus (admin)
#   GET    /api/sosmed/ratecard/{member_id}  -> rate card untuk halaman detail member
#   POST   /api/sosmed/instagram/tarik       -> tarik follower IG sekarang juga (admin)

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..instagram import tarik_semua
from ..keamanan import admin_saja
from ..poin import pastikan_member_ada
from ..schemas import (AkunSosmedCreate, AkunSosmedOut, AkunSosmedUpdate, RateCardItem,
                       SnapshotMassalIn, SnapshotMassalOut, SnapshotOut)
from ..sosmed import (BATAS_PERINGATAN_PERSEN, follower_sebelum, persen_perubahan,
                      simpan_snapshot)

router = APIRouter(prefix="/api/sosmed", tags=["Media Sosial"])


def _akun_atau_404(db: Session, akun_id: int) -> models.AkunSosmed:
    akun = db.get(models.AkunSosmed, akun_id)
    if akun is None:
        raise HTTPException(404, "Akun sosmed tidak ditemukan")
    return akun


@router.get("/akun", response_model=list[AkunSosmedOut])
def daftar_akun(platform: str | None = None, sumber: str | None = None,
                member_id: int | None = None, hanya_aktif: bool = True,
                db: Session = Depends(get_db)):
    A, M = models.AkunSosmed, models.Member
    query = select(A).join(M).order_by(M.nama_panggilan, A.platform)
    if platform:
        query = query.where(A.platform == platform)
    if sumber:
        query = query.where(A.sumber == sumber)
    if member_id:
        query = query.where(A.member_id == member_id)
    if hanya_aktif:
        query = query.where(A.aktif.is_(True))
    return db.scalars(query).all()


@router.post("/akun", response_model=AkunSosmedOut, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(admin_saja)])
def tambah_akun(data: AkunSosmedCreate, db: Session = Depends(get_db)):
    pastikan_member_ada(db, [data.member_id])
    A = models.AkunSosmed
    sudah_ada = db.scalar(select(A.id).where(A.member_id == data.member_id,
                                             A.platform == data.platform))
    if sudah_ada:
        raise HTTPException(400, f"Member ini sudah punya akun {data.platform} (id {sudah_ada})")
    akun = A(**data.model_dump())
    db.add(akun)
    db.commit()
    db.refresh(akun)
    return akun


@router.put("/akun/{akun_id}", response_model=AkunSosmedOut, dependencies=[Depends(admin_saja)])
def ubah_akun(akun_id: int, data: AkunSosmedUpdate, db: Session = Depends(get_db)):
    akun = _akun_atau_404(db, akun_id)
    for kolom, nilai in data.model_dump(exclude_unset=True).items():
        if kolom == "username" and nilai:
            nilai = nilai.strip().lstrip("@")
        setattr(akun, kolom, nilai)
    db.commit()
    db.refresh(akun)
    return akun


@router.delete("/akun/{akun_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(admin_saja)])
def hapus_akun(akun_id: int, db: Session = Depends(get_db)):
    db.delete(_akun_atau_404(db, akun_id))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/akun/{akun_id}/riwayat", response_model=list[SnapshotOut])
def riwayat_follower(akun_id: int, db: Session = Depends(get_db)):
    return _akun_atau_404(db, akun_id).snapshot


@router.post("/follower/massal", response_model=SnapshotMassalOut,
             dependencies=[Depends(admin_saja)])
def input_follower_massal(data: SnapshotMassalIn, db: Session = Depends(get_db)):
    """Isi follower banyak akun sekaligus untuk satu tanggal (halaman input cepat)."""
    baru = diperbarui = 0
    peringatan = []
    for isi in data.data:
        akun = _akun_atau_404(db, isi.akun_id)
        sebelum = follower_sebelum(db, akun.id, data.tanggal)
        persen = persen_perubahan(sebelum, isi.followers)
        if persen is not None and abs(persen) > BATAS_PERINGATAN_PERSEN:
            peringatan.append({"akun_id": akun.id, "nama_panggilan": akun.nama_panggilan,
                               "platform": akun.platform, "sebelumnya": sebelum,
                               "sekarang": isi.followers, "perubahan_persen": persen})
        if simpan_snapshot(db, akun.id, data.tanggal, isi.followers) == "baru":
            baru += 1
        else:
            diperbarui += 1
    db.commit()
    return {"baru": baru, "diperbarui": diperbarui, "peringatan": peringatan}


@router.get("/ratecard/{member_id}", response_model=list[RateCardItem])
def rate_card(member_id: int, db: Session = Depends(get_db)):
    pastikan_member_ada(db, [member_id])
    hasil = []
    for akun in daftar_akun(member_id=member_id, db=db):
        terakhir = akun.snapshot[-1] if akun.snapshot else None
        sebelum = akun.snapshot[-2].followers if len(akun.snapshot) >= 2 else None
        info = AkunSosmedOut.model_validate(akun)
        hasil.append({
            "platform": akun.platform, "username": akun.username,
            "link_profil": info.link_profil, "sumber": akun.sumber,
            "followers": terakhir.followers if terakhir else None,
            "tanggal": terakhir.tanggal if terakhir else None,
            "pertumbuhan_persen": persen_perubahan(sebelum, terakhir.followers) if terakhir else None,
        })
    return hasil


@router.post("/instagram/tarik", dependencies=[Depends(admin_saja)])
def tarik_instagram_sekarang(db: Session = Depends(get_db)):
    return tarik_semua(db)
