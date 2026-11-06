# buat_hash_password.py
# Mengubah password admin menjadi hash, untuk ditempel ke file .env.
#
# Cara jalan (dari folder backend):
#   .venv\Scripts\python.exe buat_hash_password.py
#
# Saat mengetik password, tulisannya memang TIDAK muncul di layar. Itu normal.

from getpass import getpass

from app.keamanan import buat_hash

password = getpass("Ketik password admin baru: ")
ulang = getpass("Ketik sekali lagi: ")

if not password:
    print("Password tidak boleh kosong.")
elif password != ulang:
    print("Password tidak sama. Jalankan ulang script ini.")
else:
    print("\nSalin SATU baris di bawah ini ke file .env (ganti baris ADMIN_PASSWORD yang lama):\n")
    print(f"ADMIN_PASSWORD_HASH='{buat_hash(password)}'")
