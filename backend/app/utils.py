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


def poin_ssk(peringkat: int, jumlah_peringkat: int | None = 32, jumlah_senbatsu: int | None = 16) -> float:
    """Rumus SSK: (jumlah peringkat + 1 - peringkat) + bonus 10 kalau masuk senbatsu.
    Contoh SSK 32 peringkat, senbatsu 16 : peringkat 1 = 32 + 10 = 42, peringkat 17 = 16.
    Contoh SSK 24 peringkat, senbatsu 12 : peringkat 1 = 24 + 10 = 34, peringkat 13 = 12."""
    jumlah_peringkat = jumlah_peringkat or 32      # data lama (sebelum kolom ini ada) = 32 / 16
    jumlah_senbatsu = jumlah_senbatsu or 16
    return (jumlah_peringkat + 1 - peringkat) + (10 if peringkat <= jumlah_senbatsu else 0)


# Nama team resmi, ditulis dengan huruf besar/kecil yang benar.
# Kunci = versi huruf kecil tanpa kata "team", supaya "team kiii", "K3", "KIII" jadi sama.
TEAM_RESMI = {"love": "Love", "dream": "Dream", "passion": "Passion",
              "j": "J", "t": "T", "kiii": "KIII", "k3": "KIII"}


def rapikan_team(team: str | None) -> str | None:
    """'team kiii' -> 'KIII', 'love' -> 'Love'. Kosong -> None (trainee).
    Nama team lain yang belum dikenal dibiarkan apa adanya."""
    if team is None:
        return None
    t = team.strip()
    if t.lower().startswith("team "):
        t = t[5:].strip()
    if not t or t.lower() == "team":
        return None
    return TEAM_RESMI.get(t.lower(), t)
