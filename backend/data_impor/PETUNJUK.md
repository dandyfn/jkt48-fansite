# Petunjuk mengisi data asli

Buat **satu Google Sheets** dengan 5 tab (sheet): `member`, `akun`, `show`, `projek`, `follower`.
Salin baris judul kolom dari file `template_*.csv` ke baris pertama setiap tab.
Setelah terisi: **File → Download → Comma Separated Values (.csv)** per tab,
simpan ke folder `backend/data_impor/` dengan nama `member.csv`, `akun.csv`, dst.

Aturan umum:
- **Tanggal**: `2026-05-03` atau `03/05/2026`
- **Beberapa member dalam satu sel**: pisahkan dengan `|` → `Freya|Christy|Olla`
- **Member ditulis dengan nama panggilan** persis seperti di tab `member` (huruf besar/kecil bebas)
- Sel boleh dikosongkan kalau datanya belum ada (kecuali kolom wajib)

---

## 1. Tab `member` (paling pertama)

| Kolom | Wajib | Contoh | Keterangan |
|---|---|---|---|
| nama_lengkap | ✅ | Febriola Sinambela | dipakai untuk mengenali member saat import ulang |
| nama_panggilan | ✅ | Olla | harus unik |
| stage_name | | Olla | |
| nama_jepang | | オラ | nama dalam katakana/kanji, boleh kosong |
| jiko | | (salam perkenalan) | maks. 500 karakter; tulis persis seperti diucapkan |
| tempat_lahir | | Jakarta | |
| tanggal_lahir | | 2005-02-26 | umur & zodiak dihitung otomatis |
| hometown | | Jakarta | |
| tinggi_cm | | 154 | |
| golongan_darah | | B | A / B / AB / O |
| generasi | ✅ | 7 | angka saja |
| team | | Dream | Love / Dream / Passion, kosongkan untuk trainee |
| status | | aktif | aktif / trainee / eks (default aktif) |
| tanggal_bergabung | | 2018-12-08 | untuk "lama di JKT48" |
| tanggal_lulus | | | diisi untuk member eks |
| foto_url | | foto/olla.jpg | file di folder web-user/foto, lihat catatan di bawah |
| total_show_awal | | 400 | **saldo awal**: total show sebelum tanggal_cutoff |
| total_lagu_awal | | 35 | |
| total_center_awal | | 2 | |
| tanggal_cutoff | | 2026-04-01 | tanggal mulai mencatat (sama untuk semua member) |

## 2. Tab `akun`

| Kolom | Contoh | Keterangan |
|---|---|---|
| nama_panggilan | Olla | |
| platform | tiktok | instagram / tiktok / x / youtube |
| username | ollajkt48 | boleh dengan atau tanpa @ |
| sumber | manual | `api` hanya untuk akun Instagram Creator/Business |

## 3. Tab `show` (isi mundur ±6 bulan)

| Kolom | Contoh |
|---|---|
| tanggal | 2026-05-03 |
| nama | Passion 200% |
| lokasi | Teater fX Sudirman |
| member | Christy\|Erine\|Oniel\|Aralie |

Satu baris = satu pertunjukan. Dua show di hari yang sama (siang & malam) = dua baris.

## 4. Tab `projek`

| Kolom | Contoh | Keterangan |
|---|---|---|
| judul | Dekat Namun Jauh | |
| kategori | lagu | single / lagu / projek_grup / film / iklan |
| tanggal_rilis | 2026-04-11 | |
| peserta | Christy\|Erine\|Oniel | |
| center | Christy | harus juga ada di kolom peserta |
| deskripsi | Lagu Team Passion | opsional |

## 5. Tab `follower` (opsional, kalau punya catatan follower lama)

| Kolom | Contoh |
|---|---|
| tanggal | 2026-05-03 |
| nama_panggilan | Olla |
| platform | tiktok |
| followers | 1250000 |

---

## Sumber data yang disarankan

| Data | Sumber |
|---|---|
| Biodata, generasi, team, status | Halaman member di **jkt48.com** (sumber resmi, paling diutamakan) |
| Tanggal bergabung/lulus, riwayat | Halaman Wikipedia *List of JKT48 members*, lalu cocokkan dengan jkt48.com |
| Susunan team 2026 | Pengumuman resmi JKT48 dan berita (IDN Times, Popbela, JawaPos) |
| Jadwal & lineup show | Jadwal teater di jkt48.com dan akun media sosial resmi JKT48 |
| Lagu, single, center | Kanal YouTube & platform streaming resmi JKT48, berita rilis |
| Username sosmed | Profil resmi member (biasanya dicantumkan di jkt48.com) |

**Utamakan sumber resmi.** Kalau dua sumber berbeda, pakai jkt48.com.
Kumpulkan secara manual ke spreadsheet; jangan menjalankan program yang mengambil
halaman web secara massal (scraping), karena bisa melanggar ketentuan situsnya.

**Catatan foto:** foto member adalah milik JKT48/fotografernya. Untuk proyek belajar
di laptop sendiri tidak masalah, tapi sebelum web dipublikasikan pastikan ada izin
atau cantumkan kredit dengan jelas. Kolom `foto_url` boleh dikosongkan; web akan
menampilkan huruf awal nama.
