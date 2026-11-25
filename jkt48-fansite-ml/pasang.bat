@echo off
setlocal
title Pasang update JKT48 Fan Board (Edit + Model AI)
REM ==========================================================
REM  Klik dua kali file ini. Isinya:
REM   1. Menyalin semua file baru ke D:\FansiteJKT\jkt48-fansite
REM      (file lama DITIMPA; .env, .venv, dan database TIDAK disentuh)
REM   2. Memasang library ML (scikit-learn, pandas, joblib)
REM   3. Memasukkan data show (show yang sudah ada dilewati)
REM ==========================================================
set "TUJUAN=D:\FansiteJKT\jkt48-fansite"
set "ASAL=%~dp0jkt48-fansite"

if not exist "%TUJUAN%\backend" (
  echo [GAGAL] Folder %TUJUAN%\backend tidak ditemukan.
  echo Pastikan project-mu memang ada di %TUJUAN%
  pause
  exit /b 1
)
if not exist "%ASAL%\backend" (
  echo [GAGAL] File ini harus dijalankan dari folder hasil ekstrak zip,
  echo di samping folder "jkt48-fansite".
  pause
  exit /b 1
)

echo.
echo [1/3] Menyalin file baru ke %TUJUAN% ...
robocopy "%ASAL%" "%TUJUAN%" /E /IS /IT /NFL /NDL /NJH /NJS /NP /XD .venv data __pycache__ /XF .env
if %ERRORLEVEL% GEQ 8 (
  echo [GAGAL] Ada file yang tidak bisa disalin. Tutup VS Code dan uvicorn, lalu jalankan lagi.
  pause
  exit /b 1
)
echo       Selesai menyalin.

echo.
echo [2/3] Memasang library machine learning (butuh internet, bisa 1-3 menit) ...
"%TUJUAN%\backend\.venv\Scripts\python.exe" -m pip install -q -r "%TUJUAN%\backend\requirements.txt"
if errorlevel 1 (
  echo [PERINGATAN] Pemasangan library gagal. Cek koneksi internet, lalu jalankan file ini lagi.
  pause
  exit /b 1
)
echo       Selesai memasang library.

echo.
echo [3/3] Memasukkan data show (show yang sudah ada otomatis dilewati) ...
cd /d "%TUJUAN%\backend"
".venv\Scripts\python.exe" impor_csv.py show data_impor\data_jkt48.xlsx > "%TEMP%\impor_show_jkt48.txt" 2>&1
findstr /C:"Selesai:" "%TEMP%\impor_show_jkt48.txt"

echo.
echo ==========================================================
echo  SEMUA SELESAI. Sekarang nyalakan API seperti biasa:
echo    cd backend
echo    .venv\Scripts\python.exe -m uvicorn app.main:app --reload
echo ==========================================================
pause
