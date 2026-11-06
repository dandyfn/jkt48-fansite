# routers/leaderboard.py
#   GET  /api/leaderboard                     -> leaderboard minggu/bulan (dihitung langsung)
#   GET  /api/leaderboard/riwayat/{member_id} -> skor beberapa periode terakhir (untuk grafik)
#   POST /api/leaderboard/simpan              -> simpan hasil ke tabel skor_leaderboard (admin)
#
# "simpan" berguna untuk: grafik riwayat di halaman detail, dan dataset ML nanti.
# Bisa juga dipakai mengisi riwayat mundur, misalnya 6 bulan ke belakang sekaligus.

from datetime import date, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..keamanan import admin_saja
from ..leaderboard import hitung, hitung_streak, periode_sebelumnya, rentang_periode
from ..schemas import LeaderboardOut, RiwayatSkorOut

router = APIRouter(prefix="/api/leaderboard", tags=["Leaderboard"])

Periode = Literal["minggu", "bulan"]


@router.get("", response_model=LeaderboardOut)
def lihat_leaderboard(
    periode: Periode = "minggu",
    tanggal: date | None = Query(default=None, description="Tanggal mana saja di dalam periode. Kosong = hari ini"),
    db: Session = Depends(get_db),
):
    tanggal = tanggal or date.today()
    mulai, selesai, baris = hitung(db, periode, tanggal)

    # Peringkat periode sebelumnya -> untuk tanda naik/turun
    _, _, baris_lalu = hitung(db, periode, periode_sebelumnya(periode, mulai)[0])
    ada_data_lalu = any(r["skor"] > 0 for r in baris_lalu)
    peringkat_lalu = {r["member"].id: r["peringkat"] for r in baris_lalu}

    streak = hitung_streak(db, selesai)

    data = []
    for r in baris:
        m = r["member"]
        lalu = peringkat_lalu.get(m.id)
        data.append({
            "peringkat": r["peringkat"],
            "member_id": m.id,
            "nama_panggilan": m.nama_panggilan,
            "generasi": m.generasi,
            "team": m.team,
            "foto_url": m.foto_url,
            "kapten": m.kapten,
            "skor": r["skor"],
            "rincian": r["rincian"],
            "pertumbuhan_follower_persen": r["pertumbuhan_follower_persen"],
            "streak_minggu": streak.get(m.id, 0),
            # positif = naik, negatif = turun, 0 = tetap
            "perubahan_peringkat": (lalu - r["peringkat"]) if (ada_data_lalu and lalu) else None,
        })
    return {"periode": periode, "mulai": mulai, "selesai": selesai, "data": data}


@router.get("/riwayat/{member_id}", response_model=list[RiwayatSkorOut])
def riwayat_member(member_id: int, periode: Periode = "minggu",
                   batas: int = Query(default=8, ge=1, le=104),
                   db: Session = Depends(get_db)):
    S = models.SkorLeaderboard
    baris = db.scalars(select(S).where(S.member_id == member_id, S.periode_jenis == periode)
                       .order_by(S.periode_mulai.desc()).limit(batas)).all()
    return list(reversed(baris))  # urut dari yang paling lama ke terbaru (enak untuk grafik)


@router.post("/simpan", dependencies=[Depends(admin_saja)])
def simpan_leaderboard(
    periode: Periode = "minggu",
    dari: date | None = Query(default=None, description="Kosong = hari ini"),
    sampai: date | None = Query(default=None, description="Kosong = sama dengan 'dari'"),
    db: Session = Depends(get_db),
):
    dari = dari or date.today()
    sampai = sampai or dari
    if sampai < dari:
        raise HTTPException(400, "'sampai' tidak boleh sebelum 'dari'")

    S = models.SkorLeaderboard
    jumlah_periode = jumlah_baris = 0
    tanggal = dari
    while tanggal <= sampai:
        mulai, selesai, baris = hitung(db, periode, tanggal)
        # Hapus hasil lama periode ini (kalau pernah disimpan), lalu tulis ulang
        db.execute(delete(S).where(S.periode_jenis == periode, S.periode_mulai == mulai))
        for r in baris:
            db.add(S(member_id=r["member"].id, periode_jenis=periode, periode_mulai=mulai,
                     periode_selesai=selesai, skor=r["skor"], peringkat=r["peringkat"]))
        jumlah_periode += 1
        jumlah_baris += len(baris)
        tanggal = selesai + timedelta(days=1)
    db.commit()
    return {"pesan": "Leaderboard tersimpan", "jumlah_periode": jumlah_periode,
            "jumlah_baris": jumlah_baris}
