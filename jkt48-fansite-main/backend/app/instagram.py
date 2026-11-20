# instagram.py
# Mengambil jumlah follower Instagram lewat Instagram Graph API (Business Discovery).
# Hanya bisa untuk akun Business/Creator. Butuh IG_USER_ID dan IG_ACCESS_TOKEN di .env.

from datetime import date

import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models
from .config import settings
from .sosmed import simpan_snapshot

GRAPH_URL = "https://graph.facebook.com/v25.0"


class GagalAmbilIG(Exception):
    pass


def ig_siap() -> bool:
    """True kalau IG_USER_ID dan IG_ACCESS_TOKEN sudah diisi di .env."""
    return bool(settings.ig_user_id and settings.ig_access_token)


def ambil_follower(username: str) -> int:
    """Tanya ke Instagram: berapa follower akun ini sekarang?"""
    try:
        jawaban = requests.get(
            f"{GRAPH_URL}/{settings.ig_user_id}",
            params={
                "fields": f"business_discovery.username({username}){{followers_count}}",
                "access_token": settings.ig_access_token,
            },
            timeout=20,
        )
        data = jawaban.json()
    except requests.RequestException as e:
        raise GagalAmbilIG(f"Tidak bisa terhubung ke Instagram: {e}")
    except ValueError:
        raise GagalAmbilIG("Jawaban Instagram tidak bisa dibaca")

    if "error" in data:
        # Penyebab paling umum: akun masih akun pribadi, username salah, atau token kedaluwarsa
        raise GagalAmbilIG(data["error"].get("message", "Error tidak dikenal"))
    try:
        return int(data["business_discovery"]["followers_count"])
    except (KeyError, TypeError):
        raise GagalAmbilIG("Jawaban Instagram tidak berisi followers_count")


def tarik_semua(db: Session) -> dict:
    """Ambil follower semua akun Instagram yang sumbernya 'api', lalu simpan."""
    if not ig_siap():
        return {"berhasil": [], "gagal": [], "pesan": "IG_USER_ID / IG_ACCESS_TOKEN belum diisi di .env"}

    A = models.AkunSosmed
    daftar = db.scalars(select(A).where(A.platform == "instagram", A.sumber == "api",
                                        A.aktif.is_(True))).all()
    hari_ini = date.today()
    berhasil, gagal = [], []
    for akun in daftar:
        try:
            jumlah = ambil_follower(akun.username)
            simpan_snapshot(db, akun.id, hari_ini, jumlah)
            berhasil.append({"akun_id": akun.id, "username": akun.username, "followers": jumlah})
        except GagalAmbilIG as e:
            gagal.append({"akun_id": akun.id, "username": akun.username, "alasan": str(e)})
    db.commit()
    return {"berhasil": berhasil, "gagal": gagal,
            "pesan": f"{len(berhasil)} berhasil, {len(gagal)} gagal (yang gagal perlu diisi manual)"}


def perlu_kejar(db: Session) -> bool:
    """True kalau data IG terakhir sudah lebih dari 6 hari (misal laptop mati hari Minggu)."""
    A, S = models.AkunSosmed, models.SnapshotSosmed
    ada_akun = db.scalar(select(A.id).where(A.platform == "instagram", A.sumber == "api",
                                            A.aktif.is_(True)).limit(1))
    if ada_akun is None:
        return False
    terakhir = db.scalar(select(S.tanggal).join(A).where(A.platform == "instagram", A.sumber == "api")
                         .order_by(S.tanggal.desc()).limit(1))
    return terakhir is None or (date.today() - terakhir).days > 6
