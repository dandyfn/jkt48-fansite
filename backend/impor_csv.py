# impor_csv.py
# Memasukkan data dari file Excel (.xlsx) atau CSV ke database,
# sekaligus menghitung poinnya seperti input dari web admin.
#
# Cara jalan (dari folder backend):
#   .venv\Scripts\python.exe impor_csv.py <jenis> <file>          -> simpan
#   .venv\Scripts\python.exe impor_csv.py <jenis> <file> --cek    -> cek saja, TIDAK disimpan
#
# Jenis: member | akun | show | projek | follower
# Contoh dengan file Excel (sheet yang dibaca = sheet bernama sama dengan jenis):
#   .venv\Scripts\python.exe impor_csv.py member data_impor\data_jkt48.xlsx --cek
# Contoh dengan file CSV:
#   .venv\Scripts\python.exe impor_csv.py member data_impor\member.csv --cek
#
# Aturan isi CSV:
#   - Baris pertama = nama kolom (lihat template di folder data_impor)
#   - Tanggal boleh 2026-05-03 atau 03/05/2026
#   - Daftar member dalam satu sel dipisah tanda |   contoh: Freya|Christy|Olla
#   - Member ditulis dengan nama panggilan (huruf besar/kecil bebas)
#   - Pemisah kolom koma atau titik koma dikenali otomatis
#   - Aman dijalankan ulang: data yang sudah ada dilewati / diperbarui, tidak dobel

import csv
import sys
from collections import Counter
from datetime import date, datetime
from pathlib import Path

from pydantic import ValidationError
from sqlalchemy import select

from app import models
from app.database import SessionLocal
from app.poin import KATEGORI_KE_KODE, catat
from app.schemas import MemberCreate
from app.sosmed import simpan_snapshot


class BarisSalah(Exception):
    pass


# ---------------------------------------------------------------------
# Fungsi bantu
# ---------------------------------------------------------------------

def baca_csv(path: str) -> list[dict]:
    teks = Path(path).read_text(encoding="utf-8-sig")       # utf-8-sig: buang BOM dari Excel
    try:
        dialek = csv.Sniffer().sniff(teks.splitlines()[0], delimiters=",;\t")
    except csv.Error:
        dialek = csv.excel
    baris = list(csv.DictReader(teks.splitlines(), dialect=dialek))
    # rapikan: nama kolom huruf kecil, buang spasi; sel kosong -> None
    return [{(k or "").strip().lower(): (v.strip() if v and v.strip() else None)
             for k, v in b.items()} for b in baris]


def baca_excel(path: str, nama_sheet: str) -> list[dict]:
    """Baca satu sheet dari file .xlsx. Baris 1 = judul kolom."""
    from openpyxl import load_workbook

    buku = load_workbook(path, read_only=True, data_only=True)
    if nama_sheet not in buku.sheetnames:
        raise SystemExit(f"Sheet '{nama_sheet}' tidak ada di {path}. Sheet yang ada: {', '.join(buku.sheetnames)}")
    semua = list(buku[nama_sheet].iter_rows(values_only=True))
    buku.close()
    if not semua:
        return []

    def jadikan_teks(nilai):
        if nilai is None:
            return None
        if isinstance(nilai, datetime):                 # sel tanggal di Excel
            return nilai.date().isoformat()
        if isinstance(nilai, date):
            return nilai.isoformat()
        if isinstance(nilai, float) and nilai.is_integer():
            return str(int(nilai))                     # 158.0 -> "158"
        teks = str(nilai).strip()
        return teks or None

    judul = [str(j).strip().lower() if j is not None else "" for j in semua[0]]
    return [{judul[i]: jadikan_teks(v) for i, v in enumerate(baris) if i < len(judul) and judul[i]}
            for baris in semua[1:]]


def tanggal(teks: str | None, kolom: str, wajib: bool = False) -> date | None:
    if not teks:
        if wajib:
            raise BarisSalah(f"kolom '{kolom}' wajib diisi")
        return None
    for format_ in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(teks, format_).date()
        except ValueError:
            pass
    raise BarisSalah(f"tanggal '{teks}' di kolom '{kolom}' tidak dikenali (pakai 2026-05-03 atau 03/05/2026)")


def angka(teks: str | None, kolom: str) -> int | None:
    if not teks:
        return None
    bersih = teks.replace(".", "").replace(",", "").replace(" ", "")
    if not bersih.isdigit():
        raise BarisSalah(f"'{teks}' di kolom '{kolom}' bukan angka")
    return int(bersih)


def wajib(b: dict, kolom: str) -> str:
    if not b.get(kolom):
        raise BarisSalah(f"kolom '{kolom}' wajib diisi")
    return b[kolom]


class CariMember:
    """Mencari member dari nama panggilan (tidak peduli huruf besar/kecil)."""

    def __init__(self, db):
        self.peta: dict[str, list[models.Member]] = {}
        for m in db.scalars(select(models.Member)):
            self.peta.setdefault(m.nama_panggilan.lower(), []).append(m)

    def satu(self, nama: str) -> models.Member:
        hasil = self.peta.get(nama.strip().lower(), [])
        if not hasil:
            raise BarisSalah(f"member '{nama}' tidak ditemukan (sudah diimport di tabel member?)")
        if len(hasil) > 1:
            raise BarisSalah(f"ada {len(hasil)} member bernama '{nama}', ubah salah satu nama panggilannya")
        return hasil[0]

    def banyak(self, teks: str | None) -> list[models.Member]:
        if not teks:
            return []
        nama = [n for n in teks.split("|") if n.strip()]
        members = [self.satu(n) for n in nama]
        if len({m.id for m in members}) != len(members):
            raise BarisSalah("ada nama member yang ditulis dua kali")
        return members


# ---------------------------------------------------------------------
# Import per jenis. Setiap fungsi mengembalikan teks hasil satu baris.
# ---------------------------------------------------------------------

KOLOM_MEMBER = ["nama_lengkap", "nama_panggilan", "stage_name", "nama_jepang", "jiko", "tempat_lahir", "tanggal_lahir",
                "hometown", "tinggi_cm", "golongan_darah", "generasi", "team", "status",
                "tanggal_bergabung", "tanggal_lulus", "foto_url"]


def impor_member(db, b: dict, _cari) -> str:
    data = {k: b.get(k) for k in KOLOM_MEMBER}
    for k in ("tanggal_lahir", "tanggal_bergabung", "tanggal_lulus"):
        data[k] = tanggal(data[k], k)
    data["tinggi_cm"] = angka(data["tinggi_cm"], "tinggi_cm")
    data["generasi"] = angka(data["generasi"], "generasi")
    if data["golongan_darah"]:
        data["golongan_darah"] = data["golongan_darah"].upper()
    data["status"] = (data["status"] or "aktif").lower()
    try:
        valid = MemberCreate(**{k: v for k, v in data.items() if v is not None})
    except ValidationError as e:
        pesan = "; ".join(f"{'.'.join(map(str, x['loc']))}: {x['msg']}" for x in e.errors())
        raise BarisSalah(pesan)

    member = db.scalar(select(models.Member).where(models.Member.nama_lengkap == valid.nama_lengkap))
    aksi = "diperbarui" if member else "ditambahkan"
    if member is None:
        member = models.Member()
        db.add(member)
    for k, v in valid.model_dump().items():
        setattr(member, k, v)
    db.flush()

    # Saldo awal (opsional)
    awal = {k: angka(b.get(k), k) for k in ("total_show_awal", "total_lagu_awal", "total_center_awal")}
    if any(v is not None for v in awal.values()):
        baseline = db.get(models.MemberBaseline, member.id) or models.MemberBaseline(member_id=member.id)
        baseline.tanggal_cutoff = tanggal(b.get("tanggal_cutoff"), "tanggal_cutoff") or date.today()
        for k, v in awal.items():
            setattr(baseline, k, v or 0)
        db.add(baseline)
    return f"{valid.nama_panggilan} {aksi}"


def impor_akun(db, b: dict, cari: CariMember) -> str:
    member = cari.satu(wajib(b, "nama_panggilan"))
    platform = wajib(b, "platform").lower()
    if platform not in ("instagram", "tiktok", "x", "youtube"):
        raise BarisSalah(f"platform '{platform}' tidak dikenal (instagram/tiktok/x/youtube)")
    username = wajib(b, "username").lstrip("@")
    sumber = (b.get("sumber") or "manual").lower()
    if sumber not in ("manual", "api"):
        raise BarisSalah("sumber harus 'manual' atau 'api'")
    A = models.AkunSosmed
    akun = db.scalar(select(A).where(A.member_id == member.id, A.platform == platform))
    if akun:
        akun.username, akun.sumber = username, sumber
        return f"{member.nama_panggilan} {platform} diperbarui"
    db.add(A(member_id=member.id, platform=platform, username=username, sumber=sumber))
    return f"{member.nama_panggilan} {platform} @{username} ditambahkan"


_show_di_db: Counter | None = None


def impor_show(db, b: dict, cari: CariMember) -> str:
    global _show_di_db
    tgl = tanggal(b.get("tanggal"), "tanggal", wajib=True)
    nama = wajib(b, "nama")
    members = cari.banyak(wajib(b, "member"))
    kunci = (tgl, nama.lower(), frozenset(m.id for m in members))

    # Lewati show yang sama persis (tanggal + nama + lineup) yang sudah ada di database
    if _show_di_db is None:
        _show_di_db = Counter((s.tanggal, s.nama.lower(), frozenset(p.member_id for p in s.peserta))
                              for s in db.scalars(select(models.Show)))
    if _show_di_db[kunci] > 0:
        _show_di_db[kunci] -= 1
        return f"{tgl} {nama} sudah ada, dilewati"

    show = models.Show(nama=nama, tanggal=tgl, lokasi=b.get("lokasi"))
    db.add(show)
    db.flush()
    for m in members:
        show.peserta.append(models.ShowMember(member_id=m.id))
        catat(db, member_id=m.id, kode="show", tanggal=tgl, sumber_tabel="show",
              sumber_id=show.id, keterangan=nama)
    return f"{tgl} {nama} ({len(members)} member)"


def impor_projek(db, b: dict, cari: CariMember) -> str:
    judul = wajib(b, "judul")
    kategori = wajib(b, "kategori").lower()
    if kategori not in KATEGORI_KE_KODE:
        raise BarisSalah(f"kategori '{kategori}' tidak dikenal ({', '.join(KATEGORI_KE_KODE)})")
    tgl = tanggal(b.get("tanggal_rilis"), "tanggal_rilis", wajib=True)
    peserta = cari.banyak(b.get("peserta"))
    center = {m.id for m in cari.banyak(b.get("center"))}
    if not center <= {m.id for m in peserta}:
        raise BarisSalah("member di kolom 'center' harus juga ada di kolom 'peserta'")

    P = models.Projek
    if db.scalar(select(P.id).where(P.judul == judul, P.tanggal_rilis == tgl)):
        return f"{judul} sudah ada, dilewati"
    projek = P(judul=judul, kategori=kategori, tanggal_rilis=tgl,
               deskripsi=b.get("deskripsi"), cover_url=b.get("cover_url"))
    db.add(projek)
    db.flush()
    kode = KATEGORI_KE_KODE[kategori]
    for m in peserta:
        is_center = m.id in center
        projek.peserta.append(models.MemberProjek(member_id=m.id, is_center=is_center))
        catat(db, member_id=m.id, kode=kode, tanggal=tgl, sumber_tabel="projek",
              sumber_id=projek.id, keterangan=judul)
        if is_center and kode == "lagu_baru":
            catat(db, member_id=m.id, kode="center", tanggal=tgl, sumber_tabel="projek",
                  sumber_id=projek.id, keterangan=f"Center: {judul}")
    return f"{judul} ({len(peserta)} peserta, {len(center)} center)"


def impor_follower(db, b: dict, cari: CariMember) -> str:
    member = cari.satu(wajib(b, "nama_panggilan"))
    platform = wajib(b, "platform").lower()
    akun = db.scalar(select(models.AkunSosmed).where(models.AkunSosmed.member_id == member.id,
                                                     models.AkunSosmed.platform == platform))
    if akun is None:
        raise BarisSalah(f"{member.nama_panggilan} belum punya akun {platform} (import 'akun' dulu)")
    tgl = tanggal(b.get("tanggal"), "tanggal", wajib=True)
    jumlah = angka(wajib(b, "followers"), "followers")
    hasil = simpan_snapshot(db, akun.id, tgl, jumlah)
    return f"{member.nama_panggilan} {platform} {tgl}: {jumlah:,} ({hasil})".replace(",", ".")


PENGIMPOR = {"member": impor_member, "akun": impor_akun, "show": impor_show,
             "projek": impor_projek, "follower": impor_follower}


# ---------------------------------------------------------------------

def main():
    argumen = [a for a in sys.argv[1:] if not a.startswith("--")]
    cek_saja = "--cek" in sys.argv
    if len(argumen) != 2 or argumen[0] not in PENGIMPOR:
        print(__doc__ if __doc__ else "")
        print("Pemakaian: impor_csv.py <member|akun|show|projek|follower> <file.xlsx atau file.csv> [--cek]")
        sys.exit(1)
    jenis, path = argumen
    if not Path(path).exists():
        print(f"File tidak ditemukan: {path}")
        sys.exit(1)

    if path.lower().endswith((".xlsx", ".xlsm")):
        try:
            semua = baca_excel(path, jenis)
        except PermissionError:
            raise SystemExit("File Excel sedang terkunci. Simpan (Ctrl + S) lalu TUTUP Excel, kemudian jalankan lagi.")
        sumber = f"{path} (sheet '{jenis}')"
    else:
        semua = baca_csv(path)
        sumber = path
    terisi = sum(1 for b in semua if any(b.values()))
    print(f"Membaca {terisi} baris berisi dari {sumber} ({'CEK SAJA, tidak disimpan' if cek_saja else 'akan DISIMPAN'})\n")
    berhasil, gagal = 0, []
    with SessionLocal() as db:
        cari = CariMember(db) if jenis != "member" else None
        for nomor, b in enumerate(semua, start=2):           # baris 1 = judul kolom
            if not any(b.values()):
                continue                                     # baris kosong
            try:
                with db.begin_nested():                      # satu baris gagal tidak merusak yang lain
                    pesan = PENGIMPOR[jenis](db, b, cari)
                berhasil += 1
                print(f"  baris {nomor:>4}  OK     {pesan}")
            except BarisSalah as e:
                gagal.append(nomor)
                print(f"  baris {nomor:>4}  GAGAL  {e}")
        if cek_saja:
            db.rollback()
        else:
            db.commit()

    print(f"\nSelesai: {berhasil} berhasil, {len(gagal)} gagal.")
    if gagal:
        print(f"Perbaiki baris {', '.join(map(str, gagal))} di file Excel/spreadsheet, simpan, lalu jalankan lagi.")
    if cek_saja:
        print("Ini hanya pengecekan. Jalankan tanpa --cek untuk menyimpan.")


if __name__ == "__main__":
    main()
