# schemas.py
# "Bentuk" data yang keluar-masuk lewat API (format JSON).
# - MemberCreate : data yang WAJIB dikirim saat menambah member
# - MemberUpdate : data yang BOLEH dikirim saat mengubah member (semua opsional)
# - MemberOut    : data yang DIKIRIM BALIK oleh API, termasuk umur & zodiak

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field

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
