// login.js
// Kirim username & password ke POST /api/auth/login.
// Kalau benar, API membalas token -> disimpan di browser -> masuk ke dashboard.

const pesan = document.getElementById("pesan-login");

function tampilkanPesan(teks, jenis = "gagal") {
  pesan.textContent = teks;
  pesan.className = `pesan-login pesan-${jenis}`;
  pesan.hidden = false;
}

// Pesan dari halaman lain (misal: sesi habis / baru keluar)
const asal = new URLSearchParams(location.search).get("pesan");
if (asal === "sesi") tampilkanPesan("Sesi login sudah berakhir. Silakan masuk lagi.", "info");
if (asal === "keluar") tampilkanPesan("Kamu sudah keluar.", "info");

// Kalau masih punya token, langsung ke dashboard
if (ambilToken() && !asal) location.href = "index.html";

// Tombol lihat/sembunyikan password
document.getElementById("tombol-lihat").addEventListener("click", (e) => {
  const input = document.getElementById("password");
  const lihat = input.type === "password";
  input.type = lihat ? "text" : "password";
  e.currentTarget.textContent = lihat ? "Sembunyikan" : "Lihat";
  e.currentTarget.setAttribute("aria-pressed", String(lihat));
});

document.getElementById("form-login").addEventListener("submit", async (e) => {
  e.preventDefault();
  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value;
  if (!username || !password) {
    tampilkanPesan("Username dan password wajib diisi.");
    return;
  }

  const tombol = document.getElementById("tombol-masuk");
  tombol.disabled = true;
  tombol.textContent = "Memeriksa…";

  try {
    // Endpoint login memakai format formulir (bukan JSON), sesuai standar OAuth2
    const jawaban = await fetch(API_URL + "/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ username, password }),
    });
    const data = await jawaban.json();
    if (!jawaban.ok) {
      tampilkanPesan(data.detail || "Login gagal.");
      return;
    }
    simpanToken(data.access_token);
    location.href = "index.html";
  } catch (err) {
    tampilkanPesan("Tidak bisa terhubung ke API. Pastikan uvicorn sudah menyala.");
  } finally {
    tombol.disabled = false;
    tombol.textContent = "Masuk";
  }
});
