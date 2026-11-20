# buat_tabel.py
# Jalankan SEKALI untuk membuat semua tabel + mengisi aturan poin awal.
# Aman dijalankan ulang: tabel/data yang sudah ada tidak akan dobel.
#
# Cara jalan (dari folder backend):
#   .venv\Scripts\python.exe buat_tabel.py

from datetime import date
from pathlib import Path

from sqlalchemy import inspect, text

from app import models
from app.database import Base, SessionLocal, engine

# Aturan poin yang sudah kita sepakati. Bisa diubah nanti dari web admin.
ATURAN_POIN = [
    # kode,            nama,                         poin, keterangan
    ("lagu_baru",      "Lagu/projek JKT48 baru",     10,   None),
    ("center",         "Bonus center lagu lain",     15,   "B-side, album, digital single, projek grup. Ditambahkan di atas poin lagu baru"),
    ("center_single",  "Bonus center single",        30,   "Center lagu utama single (A-side). Ditambahkan di atas poin lagu baru"),
    ("show",           "Tampil di show",             2,    "Per show"),
    ("film",           "Projek luar: film",          20,   None),
    ("iklan",          "Projek luar: iklan",         12,   None),
    ("kapten_baru",    "Diangkat jadi kapten",       25,   "Sekali, saat diangkat"),
    ("kapten_aktif",   "Masih menjabat kapten",      2,    "Per minggu"),
    ("ssk",            "Peringkat SSK",              0,    "Rumus: (jumlah peringkat + 1 - peringkat) + 10 jika masuk senbatsu (jumlah senbatsu diisi per SSK)"),
    ("follower",       "Pertumbuhan follower",       30,   "Poin maksimal, dibagi relatif ke pertumbuhan tertinggi"),
]


def tambah_kolom_baru() -> list[str]:
    """create_all hanya membuat TABEL baru; kolom baru di tabel lama tidak ikut dibuat.
    Fungsi ini menambahkan kolom yang ada di models.py tapi belum ada di database,
    tanpa menghapus data yang sudah ada."""
    ditambah = []
    with engine.begin() as conn:
        periksa = inspect(conn)
        for tabel in Base.metadata.sorted_tables:
            if not periksa.has_table(tabel.name):
                continue
            sudah_ada = {k["name"] for k in periksa.get_columns(tabel.name)}
            for kolom in tabel.columns:
                if kolom.name in sudah_ada:
                    continue
                tipe = kolom.type.compile(dialect=engine.dialect)
                conn.execute(text(f'ALTER TABLE "{tabel.name}" ADD COLUMN "{kolom.name}" {tipe}'))
                ditambah.append(f"{tabel.name}.{kolom.name}")
    return ditambah


def main():
    Path("data").mkdir(exist_ok=True)

    # 1) Buat semua tabel yang ada di models.py, lalu lengkapi kolom yang belum ada
    Base.metadata.create_all(engine)
    kolom_baru = tambah_kolom_baru()

    # 2) Isi aturan poin (hanya yang belum ada)
    with SessionLocal() as db:
        baru = 0
        for kode, nama, poin, ket in ATURAN_POIN:
            if db.get(models.JenisPoin, kode) is None:
                db.add(models.JenisPoin(kode=kode, nama=nama, poin=poin, keterangan=ket))
                baru += 1

        # Profil grup awal (hanya kalau belum ada). Bisa diubah dari web admin -> Pengaturan.
        if db.query(models.InfoGrup).first() is None:
            db.add(models.InfoGrup(
                nama="JKT48", tanggal_dibentuk=date(2011, 9, 11),
                deskripsi=("Idol group asal Jakarta yang dibentuk pada 2011 sebagai sister group "
                           "pertama AKB48 di luar Jepang. Mengusung konsep idol yang bisa ditemui, "
                           "JKT48 rutin tampil di JKT48 Theater, fX Sudirman, Jakarta.")))
            print("Profil grup awal ditambahkan.")
        db.commit()

    # 3) Tampilkan hasilnya
    daftar = inspect(engine).get_table_names()
    print(f"Database siap di: {engine.url.database}")
    print(f"{len(daftar)} tabel:")
    for nama in daftar:
        print("  -", nama)
    print(f"Aturan poin baru ditambahkan: {baru}")
    print("Kolom baru ditambahkan:", ", ".join(kolom_baru) if kolom_baru else "tidak ada")


if __name__ == "__main__":
    main()
