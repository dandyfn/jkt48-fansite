# models.py
# Rancangan semua tabel database. Setiap class = satu tabel,
# setiap atribut = satu kolom.
#
# Catatan: umur, zodiak, dan "lama di JKT48" sengaja TIDAK disimpan,
# karena bisa dihitung dari tanggal_lahir dan tanggal_bergabung.

from datetime import date, datetime

from sqlalchemy import (Boolean, Date, DateTime, Float, ForeignKey, Integer,
                        String, Text, UniqueConstraint, func)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


# =====================================================================
# 1. DATA MEMBER & GRUP
# =====================================================================

class Member(Base):
    __tablename__ = "members"

    id: Mapped[int] = mapped_column(primary_key=True)
    nama_lengkap: Mapped[str] = mapped_column(String(120))
    nama_panggilan: Mapped[str] = mapped_column(String(50))
    stage_name: Mapped[str | None] = mapped_column(String(50))
    tempat_lahir: Mapped[str | None] = mapped_column(String(80))
    tanggal_lahir: Mapped[date | None] = mapped_column(Date)
    hometown: Mapped[str | None] = mapped_column(String(80))
    tinggi_cm: Mapped[int | None] = mapped_column(Integer)
    golongan_darah: Mapped[str | None] = mapped_column(String(3))     # A, B, AB, O
    generasi: Mapped[int] = mapped_column(Integer)
    team: Mapped[str | None] = mapped_column(String(30))              # Love, Dream, Passion, kosong = trainee
    status: Mapped[str] = mapped_column(String(10), default="aktif")  # trainee / aktif / eks
    tanggal_bergabung: Mapped[date | None] = mapped_column(Date)
    tanggal_lulus: Mapped[date | None] = mapped_column(Date)          # diisi kalau sudah eks
    foto_url: Mapped[str | None] = mapped_column(String(255))
    dibuat_pada: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relasi: memudahkan mengambil data terkait, misalnya member.lencana
    lencana: Mapped[list["Lencana"]] = relationship(back_populates="member")
    akun_sosmed: Mapped[list["AkunSosmed"]] = relationship(back_populates="member")
    aktivitas: Mapped[list["AktivitasMember"]] = relationship(back_populates="member")


class InfoGrup(Base):
    """Profil JKT48 untuk section 2. Biasanya hanya berisi 1 baris."""
    __tablename__ = "info_grup"

    id: Mapped[int] = mapped_column(primary_key=True)
    nama: Mapped[str] = mapped_column(String(50), default="JKT48")
    deskripsi: Mapped[str | None] = mapped_column(Text)
    tanggal_dibentuk: Mapped[date | None] = mapped_column(Date)
    logo_url: Mapped[str | None] = mapped_column(String(255))


class MemberBaseline(Base):
    """'Saldo awal': total show/lagu/center sebelum kita mulai mencatat."""
    __tablename__ = "member_baseline"

    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"), primary_key=True)
    tanggal_cutoff: Mapped[date] = mapped_column(Date)
    total_show_awal: Mapped[int] = mapped_column(Integer, default=0)
    total_lagu_awal: Mapped[int] = mapped_column(Integer, default=0)
    total_center_awal: Mapped[int] = mapped_column(Integer, default=0)


class Lencana(Base):
    """Kapten, wakil kapten, dll. Bertanggal supaya riwayat lama tetap tersimpan."""
    __tablename__ = "lencana"

    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"))
    jenis: Mapped[str] = mapped_column(String(30))                 # kapten / wakil_kapten / ...
    keterangan: Mapped[str | None] = mapped_column(String(100))    # contoh: "Team Love"
    tanggal_mulai: Mapped[date] = mapped_column(Date)
    tanggal_selesai: Mapped[date | None] = mapped_column(Date)     # kosong = masih menjabat

    member: Mapped["Member"] = relationship(back_populates="lencana")


# =====================================================================
# 2. PROJEK, SHOW, SSK
# =====================================================================

class Projek(Base):
    """Single, lagu, projek grup, serta projek luar (film, iklan)."""
    __tablename__ = "projek"

    id: Mapped[int] = mapped_column(primary_key=True)
    judul: Mapped[str] = mapped_column(String(150))
    kategori: Mapped[str] = mapped_column(String(20))   # single / lagu / projek_grup / film / iklan / lainnya
    tanggal_rilis: Mapped[date] = mapped_column(Date)
    deskripsi: Mapped[str | None] = mapped_column(Text)
    cover_url: Mapped[str | None] = mapped_column(String(255))

    peserta: Mapped[list["MemberProjek"]] = relationship(back_populates="projek")


class MemberProjek(Base):
    """Siapa saja yang ikut sebuah projek, dan siapa center-nya."""
    __tablename__ = "member_projek"

    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"), primary_key=True)
    projek_id: Mapped[int] = mapped_column(ForeignKey("projek.id"), primary_key=True)
    is_center: Mapped[bool] = mapped_column(Boolean, default=False)

    projek: Mapped["Projek"] = relationship(back_populates="peserta")


class Show(Base):
    __tablename__ = "show"

    id: Mapped[int] = mapped_column(primary_key=True)
    nama: Mapped[str] = mapped_column(String(150))      # nama setlist / acara
    tanggal: Mapped[date] = mapped_column(Date)
    lokasi: Mapped[str | None] = mapped_column(String(100))


class ShowMember(Base):
    """Member yang tampil di sebuah show."""
    __tablename__ = "show_member"

    show_id: Mapped[int] = mapped_column(ForeignKey("show.id"), primary_key=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"), primary_key=True)


class SskEvent(Base):
    """Lagu yang diadakan pemilihan member (SSK)."""
    __tablename__ = "ssk_event"

    id: Mapped[int] = mapped_column(primary_key=True)
    judul: Mapped[str] = mapped_column(String(150))
    tanggal_pengumuman: Mapped[date] = mapped_column(Date)
    projek_id: Mapped[int | None] = mapped_column(ForeignKey("projek.id"))  # diisi setelah lagunya rilis


class SskHasil(Base):
    __tablename__ = "ssk_hasil"

    ssk_event_id: Mapped[int] = mapped_column(ForeignKey("ssk_event.id"), primary_key=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"), primary_key=True)
    peringkat: Mapped[int] = mapped_column(Integer)     # 1 - 32


# =====================================================================
# 3. SISTEM POIN & LEADERBOARD
# =====================================================================

class JenisPoin(Base):
    """Tabel aturan poin. Nilainya bisa diubah dari web admin."""
    __tablename__ = "jenis_poin"

    kode: Mapped[str] = mapped_column(String(30), primary_key=True)   # contoh: "show"
    nama: Mapped[str] = mapped_column(String(80))
    poin: Mapped[float] = mapped_column(Float)
    keterangan: Mapped[str | None] = mapped_column(String(200))


class AktivitasMember(Base):
    """
    INTI LEADERBOARD. Setiap kejadian yang memberi poin dicatat di sini
    (otomatis dibuat backend saat admin input show, projek, SSK, dll).
    """
    __tablename__ = "aktivitas_member"

    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"))
    jenis_kode: Mapped[str] = mapped_column(ForeignKey("jenis_poin.kode"))
    tanggal: Mapped[date] = mapped_column(Date, index=True)
    nilai: Mapped[float | None] = mapped_column(Float)   # contoh: peringkat SSK
    poin: Mapped[float] = mapped_column(Float)           # poin yang didapat
    keterangan: Mapped[str | None] = mapped_column(String(200))

    member: Mapped["Member"] = relationship(back_populates="aktivitas")


class SkorLeaderboard(Base):
    """Hasil perhitungan leaderboard per periode. Juga menjadi dataset ML."""
    __tablename__ = "skor_leaderboard"
    __table_args__ = (UniqueConstraint("member_id", "periode_jenis", "periode_mulai"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"))
    periode_jenis: Mapped[str] = mapped_column(String(10))   # minggu / bulan
    periode_mulai: Mapped[date] = mapped_column(Date)
    periode_selesai: Mapped[date] = mapped_column(Date)
    skor: Mapped[float] = mapped_column(Float)
    peringkat: Mapped[int] = mapped_column(Integer)


# =====================================================================
# 4. MEDIA SOSIAL
# =====================================================================

class AkunSosmed(Base):
    __tablename__ = "akun_sosmed"

    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"))
    platform: Mapped[str] = mapped_column(String(20))        # instagram / tiktok / x
    username: Mapped[str] = mapped_column(String(80))
    sumber: Mapped[str] = mapped_column(String(10), default="manual")  # api / manual
    aktif: Mapped[bool] = mapped_column(Boolean, default=True)

    member: Mapped["Member"] = relationship(back_populates="akun_sosmed")
    snapshot: Mapped[list["SnapshotSosmed"]] = relationship(back_populates="akun")


class SnapshotSosmed(Base):
    """Jumlah follower pada tanggal tertentu (dari API maupun input manual)."""
    __tablename__ = "snapshot_sosmed"
    __table_args__ = (UniqueConstraint("akun_id", "tanggal"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    akun_id: Mapped[int] = mapped_column(ForeignKey("akun_sosmed.id"))
    tanggal: Mapped[date] = mapped_column(Date)
    followers: Mapped[int] = mapped_column(Integer)

    akun: Mapped["AkunSosmed"] = relationship(back_populates="snapshot")
