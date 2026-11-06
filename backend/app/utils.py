# utils.py
# Fungsi bantu untuk data yang DIHITUNG, bukan disimpan di database.

from datetime import date

# Tanggal mulai tiap zodiak (bulan, tanggal, nama)
_AWAL_ZODIAK = [
    (1, 20, "Aquarius"), (2, 19, "Pisces"), (3, 21, "Aries"),
    (4, 20, "Taurus"), (5, 21, "Gemini"), (6, 21, "Cancer"),
    (7, 23, "Leo"), (8, 23, "Virgo"), (9, 23, "Libra"),
    (10, 23, "Scorpio"), (11, 22, "Sagittarius"), (12, 22, "Capricorn"),
]


def hitung_umur(tanggal_lahir: date | None, hari_ini: date | None = None) -> int | None:
    if tanggal_lahir is None:
        return None
    hari_ini = hari_ini or date.today()
    umur = hari_ini.year - tanggal_lahir.year
    # Kurangi 1 kalau tahun ini belum ulang tahun
    if (hari_ini.month, hari_ini.day) < (tanggal_lahir.month, tanggal_lahir.day):
        umur -= 1
    return umur


def hitung_zodiak(tanggal_lahir: date | None) -> str | None:
    if tanggal_lahir is None:
        return None
    hasil = "Capricorn"  # 1-19 Januari masih Capricorn
    for bulan, tanggal, nama in _AWAL_ZODIAK:
        if (tanggal_lahir.month, tanggal_lahir.day) >= (bulan, tanggal):
            hasil = nama
    return hasil


def hitung_lama(mulai: date | None, selesai: date | None = None) -> str | None:
    """Contoh hasil: '4 tahun 2 bulan'. Kalau belum lulus, dihitung sampai hari ini."""
    if mulai is None:
        return None
    selesai = selesai or date.today()
    total_bulan = (selesai.year - mulai.year) * 12 + (selesai.month - mulai.month)
    if selesai.day < mulai.day:
        total_bulan -= 1
    total_bulan = max(total_bulan, 0)
    tahun, bulan = divmod(total_bulan, 12)
    if tahun == 0:
        return f"{bulan} bulan"
    return f"{tahun} tahun {bulan} bulan"
