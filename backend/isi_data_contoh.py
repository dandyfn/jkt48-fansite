# isi_data_contoh.py
# Mengisi database dengan DATA CONTOH FIKTIF supaya web user bisa dicoba.
# Semua nama member di sini KARANGAN, bukan member JKT48 asli.
#
# PERHATIAN: script ini MENGHAPUS SEMUA ISI DATABASE lalu mengisinya ulang.
# Saat nanti mau memakai data asli: hapus data/jkt48.db, lalu jalankan buat_tabel.py.
#
# Cara jalan (dari folder backend, API boleh menyala):
#   .venv\Scripts\python.exe isi_data_contoh.py

import random
from datetime import date, timedelta

from app import models
from app.database import Base, SessionLocal, engine
from app.leaderboard import hitung, rentang_periode
from app.poin import KATEGORI_KE_KODE, catat
from app.utils import poin_ssk
from buat_tabel import ATURAN_POIN

acak = random.Random(48)          # angka acak yang selalu sama setiap dijalankan
hari_ini = date.today()
senin_ini = hari_ini - timedelta(days=hari_ini.weekday())

MEMBER = [
    # panggilan, nama lengkap, lahir, kota, tinggi, darah, gen, team, status, gabung
    ("Hana", "Hana Prameswari", date(2005, 3, 12), "Bandung", 158, "O", 10, "Love", "aktif", date(2022, 8, 1)),
    ("Yuki", "Yuki Larasati", date(2004, 1, 2), "Jakarta", 161, "A", 9, "Dream", "aktif", date(2021, 3, 14)),
    ("Rin", "Rinjani Putri", date(2007, 8, 21), "Malang", 155, "B", 11, "Passion", "aktif", date(2023, 5, 20)),
    ("Mei", "Meilani Sasmita", date(2003, 5, 30), "Surabaya", 160, "AB", 8, "Love", "aktif", date(2020, 2, 9)),
    ("Sora", "Soraya Anggraini", date(2006, 11, 4), "Depok", 157, "O", 10, "Dream", "aktif", date(2022, 8, 1)),
    ("Kiko", "Kirana Kusuma", date(2006, 6, 17), "Semarang", 159, "A", 10, "Passion", "aktif", date(2022, 8, 1)),
    ("Nana", "Nadia Natalia", date(2005, 9, 9), "Bekasi", 156, "B", 9, "Love", "aktif", date(2021, 3, 14)),
    ("Aya", "Ayana Lestari", date(2007, 2, 25), "Bogor", 162, "O", 11, "Dream", "aktif", date(2023, 5, 20)),
    ("Miu", "Miura Anindya", date(2004, 12, 1), "Tangerang", 154, "A", 9, "Passion", "aktif", date(2021, 3, 14)),
    ("Lulu", "Lucia Wulandari", date(2008, 4, 8), "Yogyakarta", 155, "AB", 12, None, "trainee", date(2025, 6, 1)),
    ("Ciko", "Citra Komala", date(2008, 10, 19), "Solo", 158, "O", 12, None, "trainee", date(2025, 6, 1)),
    ("Lala", "Lalita Maharani", date(2001, 7, 17), "Bogor", 163, "A", 6, "Love", "eks", date(2018, 4, 1)),
]

# 10 member tambahan supaya leaderboard lebih dari 12 orang (untuk mencoba tombol "lihat semua")
_KOTA = ["Medan", "Makassar", "Palembang", "Denpasar", "Bandung", "Jakarta", "Bekasi", "Malang", "Bogor", "Depok"]
_TEAM = ["Love", "Dream", "Passion"]
for i, nama in enumerate(["Bunga", "Dara", "Embun", "Kirei", "Mawar",
                          "Nami", "Pelangi", "Sakura", "Tara", "Wulan"]):
    gen = 9 + (i % 4)
    MEMBER.append((nama, f"{nama} Contoh", date(2003 + i % 5, 1 + i, 3 + i * 2), _KOTA[i],
                   152 + i, ["A", "B", "O", "AB"][i % 4], gen, _TEAM[i % 3], "aktif",
                   date(2019 + gen - 9, 3, 14)))


def isi():
    print("Menghapus isi database lama...")
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    with SessionLocal() as db:
        for kode, nama, poin, ket in ATURAN_POIN:
            db.add(models.JenisPoin(kode=kode, nama=nama, poin=poin, keterangan=ket))
        db.add(models.InfoGrup(
            nama="JKT48", tanggal_dibentuk=date(2011, 9, 11),
            deskripsi=("Idol group asal Jakarta dan sister group AKB48, dengan konsep "
                       "idol yang bisa ditemui langsung lewat pertunjukan rutin di teater. "
                       "[Deskripsi contoh, ubah dari web admin]")))

        members = []
        for (pg, nl, lahir, kota, tinggi, darah, gen, team, status, gabung) in MEMBER:
            m = models.Member(nama_panggilan=pg, nama_lengkap=nl, stage_name=pg, tanggal_lahir=lahir,
                              tempat_lahir=kota, hometown=kota, tinggi_cm=tinggi, golongan_darah=darah,
                              generasi=gen, team=team, status=status, tanggal_bergabung=gabung,
                              tanggal_lulus=date(2024, 12, 20) if status == "eks" else None)
            db.add(m)
            members.append(m)
        db.flush()
        aktif = [m for m in members if m.status != "eks"]
        reguler = [m for m in members if m.status == "aktif"]

        for m in reguler:  # saldo awal karier
            db.add(models.MemberBaseline(member_id=m.id, tanggal_cutoff=senin_ini - timedelta(weeks=9),
                                         total_show_awal=acak.randint(80, 320),
                                         total_lagu_awal=acak.randint(8, 30),
                                         total_center_awal=acak.randint(0, 3)))

        # Show: 3 show per minggu selama 9 minggu terakhir
        for minggu in range(9, -1, -1):
            for hari in (1, 3, 5):
                tgl = senin_ini - timedelta(weeks=minggu) + timedelta(days=hari)
                if tgl > hari_ini:
                    continue
                tampil = acak.sample(aktif, k=acak.randint(5, 8))
                show = models.Show(nama=f"Setlist Contoh {hari}", tanggal=tgl, lokasi="Teater")
                db.add(show)
                db.flush()
                for m in tampil:
                    show.peserta.append(models.ShowMember(member_id=m.id))
                    catat(db, member_id=m.id, kode="show", tanggal=tgl, sumber_tabel="show",
                          sumber_id=show.id, keterangan=show.nama)

        def projek(judul, kategori, minggu_lalu, peserta, center=()):
            tgl = senin_ini - timedelta(weeks=minggu_lalu) + timedelta(days=2)
            p = models.Projek(judul=judul, kategori=kategori, tanggal_rilis=min(tgl, hari_ini),
                              deskripsi=f"{judul} (data contoh)")
            db.add(p)
            db.flush()
            kode = KATEGORI_KE_KODE[kategori]
            for m in peserta:
                is_center = m in center
                p.peserta.append(models.MemberProjek(member_id=m.id, is_center=is_center))
                catat(db, member_id=m.id, kode=kode, tanggal=p.tanggal_rilis, sumber_tabel="projek",
                      sumber_id=p.id, keterangan=judul)
                if is_center and kode == "lagu_baru":
                    catat(db, member_id=m.id, kode="center", tanggal=p.tanggal_rilis,
                          sumber_tabel="projek", sumber_id=p.id, keterangan=f"Center: {judul}")
            return p

        h = {m.nama_panggilan: m for m in members}
        projek("Single Contoh Pertama", "single", 8, reguler[:7], center=[h["Mei"]])
        projek("Lagu Unit Contoh", "lagu", 5, [h["Yuki"], h["Sora"], h["Aya"]], center=[h["Sora"]])
        projek("Iklan Minuman Contoh", "iklan", 4, [h["Kiko"]])
        projek("Konser Tahunan Contoh", "projek_grup", 3, reguler)
        projek("Film Pendek Contoh", "film", 2, [h["Rin"], h["Nana"]])
        single = projek("Single Contoh Terbaru", "single", 0,
                        [h[n] for n in ("Hana", "Yuki", "Rin", "Mei", "Sora", "Kiko", "Aya")],
                        center=[h["Hana"]])

        # SSK minggu ini
        urutan = ["Yuki", "Hana", "Rin", "Mei", "Sora", "Aya", "Kiko", "Nana", "Miu", "Lulu", "Ciko"]
        tgl_ssk = min(senin_ini + timedelta(days=1), hari_ini)
        ssk = models.SskEvent(judul="SSK Lagu Contoh", tanggal_pengumuman=tgl_ssk, projek_id=single.id)
        db.add(ssk)
        db.flush()
        for i, nama in enumerate(urutan, start=1):
            ssk.hasil.append(models.SskHasil(member_id=h[nama].id, peringkat=i))
            catat(db, member_id=h[nama].id, kode="ssk", tanggal=tgl_ssk, sumber_tabel="ssk",
                  sumber_id=ssk.id, nilai=i, poin=poin_ssk(i), keterangan=f"SSK Lagu Contoh (peringkat {i})")

        # Kapten tiap team
        for nama, team, minggu in (("Mei", "Love", 30), ("Yuki", "Dream", 6), ("Miu", "Passion", 40)):
            l = models.Lencana(member_id=h[nama].id, jenis="kapten", keterangan=f"Team {team}",
                               tanggal_mulai=senin_ini - timedelta(weeks=minggu))
            db.add(l)
            db.flush()
            catat(db, member_id=l.member_id, kode="kapten_baru", tanggal=l.tanggal_mulai,
                  sumber_tabel="lencana", sumber_id=l.id, keterangan=f"Diangkat kapten Team {team}")

        # Akun sosmed + follower mingguan (setiap hari Minggu)
        for m in aktif:
            for platform, dasar in (("instagram", acak.randint(80, 900) * 1000),
                                    ("tiktok", acak.randint(50, 1500) * 1000)):
                akun = models.AkunSosmed(member_id=m.id, platform=platform, sumber="manual",
                                         username=f"{m.nama_panggilan.lower()}.contoh")
                db.add(akun)
                db.flush()
                jumlah = dasar
                for minggu in range(10, -1, -1):
                    tgl = senin_ini - timedelta(weeks=minggu) - timedelta(days=1)  # hari Minggu
                    db.add(models.SnapshotSosmed(akun_id=akun.id, tanggal=tgl, followers=jumlah))
                    jumlah = int(jumlah * (1 + acak.uniform(0.002, 0.05)))
                if hari_ini.weekday() >= 3:  # data minggu berjalan
                    db.add(models.SnapshotSosmed(akun_id=akun.id, tanggal=hari_ini, followers=jumlah))
        db.commit()

        # Simpan riwayat leaderboard 8 minggu terakhir (untuk grafik & streak)
        for minggu in range(8, 0, -1):
            mulai, selesai, baris = hitung(db, "minggu", senin_ini - timedelta(weeks=minggu))
            for r in baris:
                db.add(models.SkorLeaderboard(member_id=r["member"].id, periode_jenis="minggu",
                                              periode_mulai=mulai, periode_selesai=selesai,
                                              skor=r["skor"], peringkat=r["peringkat"]))
        db.commit()
    print(f"Selesai! {len(MEMBER)} member contoh, show 10 minggu, 6 projek, 1 SSK, 3 kapten, data follower.")


if __name__ == "__main__":
    jawab = input("Ini akan MENGHAPUS semua data di database. Ketik YA untuk lanjut: ")
    if jawab.strip().upper() == "YA":
        isi()
    else:
        print("Dibatalkan.")
