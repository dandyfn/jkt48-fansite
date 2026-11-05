# buat_tabel.py
# Jalankan SEKALI untuk membuat semua tabel + mengisi aturan poin awal.
# Aman dijalankan ulang: tabel/data yang sudah ada tidak akan dobel.
#
# Cara jalan (dari folder backend):
#   .venv\Scripts\python.exe buat_tabel.py

from pathlib import Path

from sqlalchemy import inspect

from app import models
from app.database import Base, SessionLocal, engine

# Aturan poin yang sudah kita sepakati. Bisa diubah nanti dari web admin.
ATURAN_POIN = [
    # kode,            nama,                         poin, keterangan
    ("lagu_baru",      "Lagu/projek JKT48 baru",     10,   None),
    ("center",         "Bonus posisi center",        15,   "Ditambahkan di atas poin lagu baru"),
    ("show",           "Tampil di show",             2,    "Per show"),
    ("film",           "Projek luar: film",          20,   None),
    ("iklan",          "Projek luar: iklan",         12,   None),
    ("kapten_baru",    "Diangkat jadi kapten",       25,   "Sekali, saat diangkat"),
    ("kapten_aktif",   "Masih menjabat kapten",      2,    "Per minggu"),
    ("ssk",            "Peringkat SSK",              0,    "Rumus: (33 - peringkat) + 10 jika peringkat 1-16"),
    ("follower",       "Pertumbuhan follower",       30,   "Poin maksimal, dibagi relatif ke pertumbuhan tertinggi"),
]


def main():
    Path("data").mkdir(exist_ok=True)

    # 1) Buat semua tabel yang ada di models.py
    Base.metadata.create_all(engine)

    # 2) Isi aturan poin (hanya yang belum ada)
    with SessionLocal() as db:
        baru = 0
        for kode, nama, poin, ket in ATURAN_POIN:
            if db.get(models.JenisPoin, kode) is None:
                db.add(models.JenisPoin(kode=kode, nama=nama, poin=poin, keterangan=ket))
                baru += 1
        db.commit()

    # 3) Tampilkan hasilnya
    daftar = inspect(engine).get_table_names()
    print(f"Database siap di: {engine.url.database}")
    print(f"{len(daftar)} tabel:")
    for nama in daftar:
        print("  -", nama)
    print(f"Aturan poin baru ditambahkan: {baru}")


if __name__ == "__main__":
    main()
