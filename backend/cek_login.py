# cek_login.py
# Script diagnosa: mencari tahu kenapa login admin gagal.
#
# Cara jalan (dari folder backend):
#   .venv\Scripts\python.exe cek_login.py

from getpass import getpass
from pathlib import Path

print("=" * 60)
print("1. Folder terminal sekarang :", Path.cwd())
env = Path(".env")
print("   File .env ditemukan      :", "YA" if env.exists() else "TIDAK  <-- MASALAH")

if env.exists():
    isi = env.read_text(encoding="utf-8", errors="replace").splitlines()
    baris_hash = [b for b in isi if b.strip().startswith("ADMIN_PASSWORD_HASH")]
    print("   Baris ADMIN_PASSWORD_HASH:", len(baris_hash), "baris",
          "" if len(baris_hash) == 1 else " <-- MASALAH (harus tepat 1)")

from app.config import settings
from app.keamanan import _hasher

h = settings.admin_password_hash
print("\n2. Username yang terbaca    :", repr(settings.admin_username))
print("   Panjang hash             :", len(h), "(normalnya sekitar 97)")
print("   Awal hash                :", h[:20] if h else "(KOSONG)  <-- MASALAH")
print("   Hash diawali $argon2     :", "YA" if h.startswith("$argon2") else "TIDAK  <-- MASALAH")

if h:
    pw = getpass("\n3. Ketik password admin (tidak tampil di layar): ")
    try:
        cocok = _hasher.verify(pw, h)
    except Exception as e:
        cocok = False
        print("   Hash rusak / terpotong   :", e)
    print("   Hasil                    :", "PASSWORD COCOK" if cocok else "PASSWORD TIDAK COCOK  <-- MASALAH")
print("=" * 60)