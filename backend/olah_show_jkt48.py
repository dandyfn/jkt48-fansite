"""
Mengolah file show yang kamu simpan sendiri dari browser menjadi sheet "show" di data_jkt48.xlsx.

Cara mengumpulkan file (manual, lewat Chrome seperti biasa):
  1. Buka  https://jkt48.com/api/v1/theater-shows/OSH2-1?lang=id  di Chrome
  2. Tekan Ctrl + S, simpan ke folder  backend\\data_impor\\simpanan_show\\  dengan nama  OSH2-1.json
  3. Ganti angka di alamat (OSH2-2, OSH2-3, ...) lalu ulangi

Lalu jalankan dari folder backend:
    .venv\\Scripts\\python.exe olah_show_jkt48.py

Skrip ini TIDAK mengakses internet. Ia hanya:
  - membaca semua file .json di data_impor\\simpanan_show\\
  - mencocokkan nama lengkap member (dari jkt48.com) ke nama panggilan di Excel kita
  - menulis hasilnya ke sheet "show" + sheet "show_belum_cocok" di data_impor\\data_jkt48.xlsx
  - memberi tahu nomor kode mana yang belum kamu simpan (supaya tidak ada yang terlewat)
"""
import json
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

from openpyxl import load_workbook

FOLDER = Path(__file__).parent / "data_impor"
SIMPANAN = FOLDER / "simpanan_show"
FILE_AKTIF = FOLDER / "data_jkt48.xlsx"
FILE_EKS = FOLDER / "member_eks.xlsx"

# Nama di jkt48.com yang ejaannya beda dengan nama_lengkap di Excel kita.
# Format:  "nama persis di jkt48.com": "nama_panggilan di Excel"
NAMA_MANUAL = {
    "Desy Natalia": "Daisy",
    "Jesslyn Elly": "Jesslyn",
    "Freya Jayawardana": "Freya",
    "Celline Thefani": "Elin",
    "Fakhiryani Shafariyanti": "Shafa",
    "Alicia Chanzia": "Acha",
    "Jennifer Hanna": "Hanna",
    "Flora Shafiq": "Flora",
    "Christi": "Christi",
    "Febi Komaril": "Febi",
    "Shaffa Nabila": "Afa",
}

# Bukan member JKT48 (tamu / pertukaran sementara dari grup lain) -> dilewati, tidak dilaporkan
NAMA_DILEWATI = {
    "Saya Kawamoto",      # member AKB48, tampil sementara di JKT48 (Sep-Okt 2018)
}


# ---------------------------------------------------------------------
# 1) Membaca file simpanan
# ---------------------------------------------------------------------
def baca_simpanan() -> tuple[list[dict], list[str]]:
    """Kembalikan (daftar data show, daftar file yang tidak bisa dibaca)."""
    data, rusak = {}, []
    for f in sorted(SIMPANAN.glob("*.json")):
        try:
            isi = json.loads(f.read_text(encoding="utf-8-sig"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            rusak.append(f.name)
            continue
        # File per bulan (dari bookmarklet halaman jadwal) berisi DAFTAR show -> proses satu per satu
        for item in (isi if isinstance(isi, list) else [isi]):
            # Halaman "Theater show tidak ditemukan" -> bukan rusak, cukup dilewati
            if isinstance(item, dict) and item.get("status") is False:
                continue
            # File dari Chrome berisi {"status":..., "message":..., "data": {...}} -> ambil bagian "data"
            d = item.get("data") if isinstance(item, dict) and isinstance(item.get("data"), dict) else item
            if not isinstance(d, dict) or not d.get("code") or not d.get("date"):
                rusak.append(f.name)
                continue
            data[d["code"]] = d                   # kalau tersimpan dua kali, cukup dihitung sekali
    return list(data.values()), rusak


def laporan_bolong(kode: list[str]) -> None:
    """Tunjukkan nomor yang belum disimpan, per awalan (mis. "OSH2-" atau "SH")."""
    per_awalan: dict[str, set[int]] = {}
    for k in kode:
        m = re.fullmatch(r"(.+-)(\d+)", k)           # hanya kode berurutan "OSH2-3079"; kode acak (SHBE48) tidak dicek
        if m:
            per_awalan.setdefault(m.group(1), set()).add(int(m.group(2)))
    for awalan, nomor in sorted(per_awalan.items()):
        awal, akhir = min(nomor), max(nomor)
        bolong = [n for n in range(awal, akhir + 1) if n not in nomor]
        print(f"   {awalan}{awal} s/d {awalan}{akhir}: {len(nomor)} show berisi data")
        if bolong:
            contoh = ", ".join(f"{awalan}{n}" for n in bolong[:20])
            print(f"      nomor tanpa data / belum disimpan ({len(bolong)}): {contoh}{' ...' if len(bolong) > 20 else ''}")
        print(f"      berikutnya: {awalan}{akhir + 1}")


# ---------------------------------------------------------------------
# 2) Mencocokkan nama lengkap -> nama panggilan
# ---------------------------------------------------------------------
def kata(nama: str) -> set[str]:
    """'Ayana Shahab' -> {'ayana', 'shahab'} (huruf kecil, tanpa tanda baca/aksen)."""
    nama = unicodedata.normalize("NFKD", nama).encode("ascii", "ignore").decode()
    return set(re.sub(r"[^a-z ]", " ", nama.lower()).split())


def daftar_member() -> list[tuple[str, str]]:
    """[(nama_lengkap, nama_panggilan)] dari sheet member di kedua file Excel."""
    hasil = []
    for f in (FILE_AKTIF, FILE_EKS):
        if not f.exists():
            continue
        baris = list(load_workbook(f, read_only=True)["member"].iter_rows(values_only=True))
        kol = {k: i for i, k in enumerate(baris[0])}
        for b in baris[1:]:
            if b[kol["nama_lengkap"]] and b[kol["nama_panggilan"]]:
                hasil.append((str(b[kol["nama_lengkap"]]).strip(), str(b[kol["nama_panggilan"]]).strip()))
    return hasil


class Pencocok:
    def __init__(self):
        self.member = daftar_member()
        self.persis: dict[str, set[str]] = {}
        for lengkap, panggilan in self.member:
            self.persis.setdefault(" ".join(sorted(kata(lengkap))), set()).add(panggilan)
        self.belum: dict[str, int] = {}          # nama jkt48.com yang gagal dicocokkan -> jumlah show

    def cocokkan(self, nama: str) -> str | None:
        if nama in NAMA_DILEWATI:
            return None
        if nama in NAMA_MANUAL:
            return NAMA_MANUAL[nama]
        k = kata(nama)
        hasil = self.persis.get(" ".join(sorted(k)), set())                     # 1. kata-katanya sama persis
        if len(hasil) != 1 and len(k) >= 2:                                     # 2. nama jkt48.com ada di dalam nama kita
            hasil = {p for l, p in self.member if k <= kata(l)}
        if len(hasil) != 1 and len(k) >= 2:                                     # 3. nama kita ada di dalam nama jkt48.com
            hasil = {p for l, p in self.member if len(kata(l)) >= 2 and kata(l) <= k}
        if len(hasil) == 1:
            return next(iter(hasil))
        self.belum[nama] = self.belum.get(nama, 0) + 1
        return None


# ---------------------------------------------------------------------
# 3) Menulis ke Excel
# ---------------------------------------------------------------------
def tulis_excel(daftar: list[dict], pencocok: Pencocok) -> int:
    baris, sudah = [], set()
    hari_ini = date.today().isoformat()
    lewat = {"tanpa member": 0, "belum terjadi": 0, "dobel": 0}
    for d in daftar:
        if d["date"] > hari_ini:                                    # show yang belum terjadi tidak dihitung
            lewat["belum terjadi"] += 1
            continue
        nama_member = [m.get("name", "") for m in d.get("jkt48_member") or []]
        cocok = list(dict.fromkeys(p for p in (pencocok.cocokkan(n) for n in nama_member) if p))
        if not cocok:
            lewat["tanpa member"] += 1
            continue
        jam = (d.get("start_time") or "")[:5]
        kunci = (d["date"], jam, d.get("title") or "Show", frozenset(cocok))
        if kunci in sudah:                                          # show yang sama dari dua sumber -> sekali saja
            lewat["dobel"] += 1
            continue
        sudah.add(kunci)
        baris.append((d["date"], jam, d.get("title") or "Show", cocok))
    baris.sort()
    print("Dilewati: " + ", ".join(f"{k} {v}" for k, v in lewat.items()))

    wb = load_workbook(FILE_AKTIF)
    ws = wb["show"]
    ws.delete_rows(2, ws.max_row)                                   # isi lama dihapus, judul kolom tetap
    for tgl, _jam, judul, member in baris:
        ws.append([tgl, judul, "JKT48 Theater", "|".join(member)])
    ws.column_dimensions["B"].width = 34
    ws.column_dimensions["D"].width = 120

    if "show_belum_cocok" in wb.sheetnames:
        del wb["show_belum_cocok"]
    wb2 = wb.create_sheet("show_belum_cocok")
    wb2.append(["nama di jkt48.com", "jumlah show", "tambahkan ke NAMA_MANUAL di olah_show_jkt48.py"])
    for nama, n in sorted(pencocok.belum.items(), key=lambda x: -x[1]):
        wb2.append([nama, n])
    wb2.column_dimensions["A"].width = 36
    wb2.column_dimensions["C"].width = 60
    wb.save(FILE_AKTIF)
    return len(baris)


def main():
    SIMPANAN.mkdir(exist_ok=True)
    daftar, rusak = baca_simpanan()
    print(f"Folder simpanan: {SIMPANAN}")
    print(f"{len(daftar)} show terbaca")
    if rusak:
        rusak = list(dict.fromkeys(rusak))
        print(f"{len(rusak)} file tidak bisa dibaca (simpan ulang dari Chrome): {', '.join(rusak[:10])}")
    if not daftar:
        print("Belum ada file .json di folder simpanan_show.")
        return
    laporan_bolong([d["code"] for d in daftar])
    acak = [d for d in daftar if not re.fullmatch(r".+-\d+", d["code"])]
    if acak:
        bulan = sorted({d["date"][:7] for d in acak})
        print(f"   kode lain (SH..., dokumen): {len(acak)} show, bulan: {', '.join(bulan)}")

    pencocok = Pencocok()
    n = tulis_excel(daftar, pencocok)
    print(f"\nTertulis {n} show ke sheet 'show' di {FILE_AKTIF.name}")
    if pencocok.belum:
        print(f"{len(pencocok.belum)} nama belum cocok (lihat sheet 'show_belum_cocok'):")
        for nama, jml in sorted(pencocok.belum.items(), key=lambda x: -x[1])[:15]:
            print(f"   {nama} ({jml} show)")


if __name__ == "__main__":
    try:
        main()
    except PermissionError:
        sys.exit("\nFile Excel sedang terbuka. Tutup data_jkt48.xlsx di Excel, lalu jalankan lagi.")
