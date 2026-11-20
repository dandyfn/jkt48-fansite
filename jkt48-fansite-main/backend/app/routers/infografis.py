# routers/infografis.py
# Data untuk halaman Infografis (web-user/infografis.html).
#
#   GET /api/infografis -> satu baris per member aktif & trainee, berisi semua angka
#                          yang dibandingkan: tinggi, umur, total show, lagu, center,
#                          projek luar, dan senbatsu.
#
# Kenapa dikirim per member, bukan sudah dirangkum per generasi?
# Karena halaman infografis bisa diganti-ganti (semua member / per generasi,
# tertua / termuda) tanpa minta data ulang. Merangkumnya cukup di JavaScript.

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..schemas import InfografisMember
from ..utils import hitung_umur

router = APIRouter(prefix="/api/infografis", tags=["Infografis"])

LAGU_JKT = ["single", "lagu", "projek_grup"]     # dihitung sebagai "lagu"
PROJEK_LUAR = ["film", "iklan", "lainnya"]        # dihitung sebagai "projek"


def _jumlah_per_member(db: Session, query) -> dict[int, int]:
    """Jalankan query (member_id, jumlah) -> {member_id: jumlah}."""
    return {member_id: jumlah for member_id, jumlah in db.execute(query).all()}


@router.get("", response_model=list[InfografisMember])
def data_infografis(db: Session = Depends(get_db)):
    MP, P, SM = models.MemberProjek, models.Projek, models.ShowMember

    members = db.scalars(
        select(models.Member)
        .where(models.Member.status.in_(["aktif", "trainee"]))
        .order_by(models.Member.generasi, models.Member.nama_panggilan)
    ).all()

    # Hitung sekaligus untuk SEMUA member (5 query), bukan 1 query per member
    show = _jumlah_per_member(db, select(SM.member_id, func.count()).group_by(SM.member_id))
    lagu = _jumlah_per_member(db, select(MP.member_id, func.count()).join(P)
                              .where(P.kategori.in_(LAGU_JKT)).group_by(MP.member_id))
    center = _jumlah_per_member(db, select(MP.member_id, func.count()).join(P)
                                .where(P.kategori.in_(LAGU_JKT), MP.is_center.is_(True))
                                .group_by(MP.member_id))
    projek = _jumlah_per_member(db, select(MP.member_id, func.count()).join(P)
                                .where(P.kategori.in_(PROJEK_LUAR)).group_by(MP.member_id))
    # Senbatsu = ikut lineup lagu utama single (kategori "single")
    senbatsu = _jumlah_per_member(db, select(MP.member_id, func.count()).join(P)
                                  .where(P.kategori == "single").group_by(MP.member_id))
    saldo = {b.member_id: b for b in db.scalars(select(models.MemberBaseline))}

    hasil = []
    for m in members:
        awal = saldo.get(m.id)
        hasil.append({
            "id": m.id,
            "nama_panggilan": m.nama_panggilan,
            "generasi": m.generasi,
            "team": m.team,
            "status": m.status,
            "foto_url": m.foto_url,
            "tanggal_lahir": m.tanggal_lahir,
            "umur": hitung_umur(m.tanggal_lahir),
            "tinggi_cm": m.tinggi_cm,
            # total = saldo awal (dari Excel) + yang tercatat di web
            "total_show": show.get(m.id, 0) + ((awal.total_show_awal or 0) if awal else 0),
            "total_lagu": lagu.get(m.id, 0) + ((awal.total_lagu_awal or 0) if awal else 0),
            "total_center": center.get(m.id, 0) + ((awal.total_center_awal or 0) if awal else 0),
            "total_projek": projek.get(m.id, 0),
            "total_senbatsu": senbatsu.get(m.id, 0),
        })
    return hasil
