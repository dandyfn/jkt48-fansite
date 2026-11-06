# schemas.py
# "Bentuk" data yang keluar-masuk lewat API (format JSON).
# - MemberCreate : data yang WAJIB dikirim saat menambah member
# - MemberUpdate : data yang BOLEH dikirim saat mengubah member (semua opsional)
# - MemberOut    : data yang DIKIRIM BALIK oleh API, termasuk umur & zodiak

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from .utils import hitung_lama, hitung_umur, hitung_zodiak

Status = Literal["trainee", "aktif", "eks"]
GolDarah = Literal["A", "B", "AB", "O"]


class MemberBase(BaseModel):
    nama_lengkap: str = Field(min_length=1, max_length=120)
    nama_panggilan: str = Field(min_length=1, max_length=50)
    stage_name: str | None = None
    tempat_lahir: str | None = None
    tanggal_lahir: date | None = None
    hometown: str | None = None
    tinggi_cm: int | None = Field(default=None, ge=100, le=220)
    golongan_darah: GolDarah | None = None
    generasi: int = Field(ge=1)
    team: str | None = None
    status: Status = "aktif"
    tanggal_bergabung: date | None = None
    tanggal_lulus: date | None = None
    foto_url: str | None = None


class MemberCreate(MemberBase):
    pass


class MemberUpdate(BaseModel):
    # Semua opsional: kirim hanya kolom yang mau diubah
    nama_lengkap: str | None = None
    nama_panggilan: str | None = None
    stage_name: str | None = None
    tempat_lahir: str | None = None
    tanggal_lahir: date | None = None
    hometown: str | None = None
    tinggi_cm: int | None = Field(default=None, ge=100, le=220)
    golongan_darah: GolDarah | None = None
    generasi: int | None = Field(default=None, ge=1)
    team: str | None = None
    status: Status | None = None
    tanggal_bergabung: date | None = None
    tanggal_lulus: date | None = None
    foto_url: str | None = None


class MemberOut(MemberBase):
    # from_attributes: boleh dibuat langsung dari objek tabel (models.Member)
    model_config = ConfigDict(from_attributes=True)

    id: int

    # Kolom hitungan: tidak ada di database, dihitung setiap kali dikirim
    @computed_field
    @property
    def umur(self) -> int | None:
        return hitung_umur(self.tanggal_lahir)

    @computed_field
    @property
    def zodiak(self) -> str | None:
        return hitung_zodiak(self.tanggal_lahir)

    @computed_field
    @property
    def lama_di_jkt48(self) -> str | None:
        return hitung_lama(self.tanggal_bergabung, self.tanggal_lulus)


# =====================================================================
# PROJEK (single, lagu, projek grup, film, iklan)
# =====================================================================

KategoriProjek = Literal["single", "lagu", "projek_grup", "film", "iklan"]


class PesertaProjekIn(BaseModel):
    member_id: int
    is_center: bool = False


class PesertaProjekOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    member_id: int
    nama_panggilan: str
    is_center: bool


class ProjekCreate(BaseModel):
    judul: str = Field(min_length=1, max_length=150)
    kategori: KategoriProjek
    tanggal_rilis: date
    deskripsi: str | None = None
    cover_url: str | None = None
    peserta: list[PesertaProjekIn] = []


class ProjekOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    judul: str
    kategori: str
    tanggal_rilis: date
    deskripsi: str | None
    cover_url: str | None
    peserta: list[PesertaProjekOut]


# =====================================================================
# SHOW
# =====================================================================

class ShowCreate(BaseModel):
    nama: str = Field(min_length=1, max_length=150)
    tanggal: date
    lokasi: str | None = None
    member_ids: list[int] = Field(min_length=1)


class PesertaShowOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    member_id: int
    nama_panggilan: str


class ShowOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nama: str
    tanggal: date
    lokasi: str | None
    peserta: list[PesertaShowOut]


# =====================================================================
# SSK (pemilihan member)
# =====================================================================

class HasilSskIn(BaseModel):
    member_id: int
    peringkat: int = Field(ge=1, le=32)


class HasilSskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    member_id: int
    nama_panggilan: str
    peringkat: int
    poin: float


class SskCreate(BaseModel):
    judul: str = Field(min_length=1, max_length=150)
    tanggal_pengumuman: date
    projek_id: int | None = None
    hasil: list[HasilSskIn] = Field(min_length=1, max_length=32)


class SskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    judul: str
    tanggal_pengumuman: date
    projek_id: int | None
    hasil: list[HasilSskOut]


# =====================================================================
# LENCANA (kapten, wakil kapten, dll)
# =====================================================================

JenisLencana = Literal["kapten", "wakil_kapten", "lainnya"]


class LencanaCreate(BaseModel):
    member_id: int
    jenis: JenisLencana
    keterangan: str | None = None       # contoh: "Team Love"
    tanggal_mulai: date
    tanggal_selesai: date | None = None


class LencanaUpdate(BaseModel):
    keterangan: str | None = None
    tanggal_mulai: date | None = None
    tanggal_selesai: date | None = None


class LencanaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    member_id: int
    nama_panggilan: str
    jenis: str
    keterangan: str | None
    tanggal_mulai: date
    tanggal_selesai: date | None

    @computed_field
    @property
    def masih_menjabat(self) -> bool:
        return self.tanggal_selesai is None


# =====================================================================
# ATURAN POIN & AKTIVITAS
# =====================================================================

class JenisPoinOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    kode: str
    nama: str
    poin: float
    keterangan: str | None


class JenisPoinUpdate(BaseModel):
    nama: str | None = None
    poin: float | None = Field(default=None, ge=0)
    keterangan: str | None = None


class AktivitasOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    member_id: int
    nama_panggilan: str
    jenis_kode: str
    tanggal: date
    nilai: float | None
    poin: float
    keterangan: str | None


# =====================================================================
# LEADERBOARD
# =====================================================================

class LeaderboardItem(BaseModel):
    peringkat: int
    member_id: int
    nama_panggilan: str
    generasi: int
    team: str | None
    foto_url: str | None
    skor: float
    rincian: dict[str, float]                 # contoh: {"show": 4, "center": 15}
    pertumbuhan_follower_persen: float | None
    streak_minggu: int                         # minggu berturut-turut di Top 5
    perubahan_peringkat: int | None            # + naik, - turun, None = belum ada data lalu


class LeaderboardOut(BaseModel):
    periode: str
    mulai: date
    selesai: date
    data: list[LeaderboardItem]


class RiwayatSkorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    periode_mulai: date
    periode_selesai: date
    skor: float
    peringkat: int


# =====================================================================
# MEDIA SOSIAL
# =====================================================================

Platform = Literal["instagram", "tiktok", "x", "youtube"]
SumberData = Literal["api", "manual"]

_LINK_PROFIL = {
    "instagram": "https://www.instagram.com/{}/",
    "tiktok": "https://www.tiktok.com/@{}",
    "x": "https://x.com/{}",
    "youtube": "https://www.youtube.com/@{}",
}


class AkunSosmedCreate(BaseModel):
    member_id: int
    platform: Platform
    username: str = Field(min_length=1, max_length=80)
    sumber: SumberData = "manual"
    aktif: bool = True

    @field_validator("username")
    @classmethod
    def _buang_at(cls, v: str) -> str:
        return v.strip().lstrip("@")   # "@hana.jkt48" -> "hana.jkt48"


class AkunSosmedUpdate(BaseModel):
    username: str | None = None
    sumber: SumberData | None = None
    aktif: bool | None = None


class AkunSosmedOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    member_id: int
    nama_panggilan: str
    platform: str
    username: str
    sumber: str
    aktif: bool
    follower_terakhir: int | None
    tanggal_terakhir: date | None

    @computed_field
    @property
    def link_profil(self) -> str:
        return _LINK_PROFIL.get(self.platform, "{}").format(self.username)

    @computed_field
    @property
    def perlu_update(self) -> bool:
        """True kalau belum pernah diisi atau data terakhir lebih dari 7 hari lalu."""
        if self.tanggal_terakhir is None:
            return True
        return (date.today() - self.tanggal_terakhir).days > 7


class SnapshotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    tanggal: date
    followers: int


class IsiFollowerIn(BaseModel):
    akun_id: int
    followers: int = Field(ge=0)


class SnapshotMassalIn(BaseModel):
    tanggal: date = Field(default_factory=date.today)
    data: list[IsiFollowerIn] = Field(min_length=1)


class PeringatanFollower(BaseModel):
    akun_id: int
    nama_panggilan: str
    platform: str
    sebelumnya: int
    sekarang: int
    perubahan_persen: float


class SnapshotMassalOut(BaseModel):
    baru: int
    diperbarui: int
    peringatan: list[PeringatanFollower]


class RateCardItem(BaseModel):
    platform: str
    username: str
    link_profil: str
    sumber: str
    followers: int | None
    tanggal: date | None
    pertumbuhan_persen: float | None   # dibanding data sebelumnya
