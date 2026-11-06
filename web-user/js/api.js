// api.js
// Alamat API dan fungsi bantu yang dipakai semua halaman web user.

// Alamat backend. Saat nanti di-deploy, cukup ganti baris ini.
const API_URL = "http://127.0.0.1:8000";

// Ambil data JSON dari API. Contoh: await ambil("/api/members")
async function ambil(path) {
  let jawaban;
  try {
    jawaban = await fetch(API_URL + path);
  } catch (e) {
    // Gagal terhubung sama sekali -> kemungkinan besar API belum menyala
    tampilkanBannerError();
    throw e;
  }
  if (!jawaban.ok) {
    throw new Error(`API membalas ${jawaban.status} untuk ${path}`);
  }
  return jawaban.json();
}

function tampilkanBannerError() {
  const banner = document.getElementById("banner-error");
  if (banner) banner.hidden = false;
}

// "Amankan" teks sebelum dimasukkan ke HTML, supaya tanda < > dari data
// tidak dianggap sebagai kode HTML (mencegah serangan XSS).
function esc(teks) {
  if (teks === null || teks === undefined) return "";
  return String(teks)
    .replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;").replaceAll("'", "&#39;");
}

// 1234567 -> "1.234.567",  91.92 -> "91,9"
function angka(n) {
  return n === null || n === undefined ? "–" : Number(n).toLocaleString("id-ID", { maximumFractionDigits: 1 });
}

// "2026-11-02" -> "2 Nov 2026"
function tanggal(str, pilihan = { day: "numeric", month: "short", year: "numeric" }) {
  if (!str) return "–";
  return new Date(str + "T00:00:00").toLocaleDateString("id-ID", pilihan);
}

// Kelas warna chip team
function kelasTeam(team) {
  if (!team) return "team-trainee";
  return "team-" + team.toLowerCase();
}

function labelTeam(team) {
  return team ? "Team " + team : "Trainee";
}

const IKON_MAHKOTA_KECIL =
  `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linejoin="round" aria-hidden="true"><path d="M3 18h18l-2-11-5 5-2-7-2 7-5-5z"/></svg>`;

// Foto member; kalau belum ada, tampilkan huruf pertama nama.
// Kalau member sedang menjabat kapten, foto diberi bingkai emas + pita "Kapten".
//   ukuran: "besar" (podium, detail, biodata) atau "kecil" (daftar peringkat -> hanya ikon mahkota)
function htmlFoto(member, indeks, ukuran = "besar") {
  const tint = "tint-" + (indeks % 4);
  const isi = member.foto_url
    ? `<img src="${esc(member.foto_url)}" alt="Foto ${esc(member.nama_panggilan)}" loading="lazy">`
    : `<span class="inisial" aria-hidden="true">${esc((member.nama_panggilan || "?")[0])}</span>`;
  const foto = `<div class="foto ${tint}">${isi}</div>`;
  if (!member.kapten) return foto;

  const pita = ukuran === "kecil"
    ? `<span class="mahkota-kapten" title="Kapten ${esc(member.kapten)}">${IKON_MAHKOTA_KECIL}<span class="sr-only">Kapten ${esc(member.kapten)}</span></span>`
    : `<span class="pita-kapten">${IKON_MAHKOTA_KECIL} Kapten</span>`;
  return `<div class="bingkai-kapten bingkai-${ukuran}">${foto}${pita}</div>`;
}

// Tanda naik/turun peringkat
function htmlPerubahan(nilai) {
  if (nilai === null || nilai === undefined) return `<span class="tetap">baru</span>`;
  if (nilai > 0) return `<span class="naik">▲ naik ${nilai}</span>`;
  if (nilai < 0) return `<span class="turun">▼ turun ${Math.abs(nilai)}</span>`;
  return `<span class="tetap">— tetap</span>`;
}

const IKON_STREAK =
  `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#E0457F" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 22c4 0 7-3 7-7 0-4-3-6-4-9-1 2-2 3-4 3 0-2 0-4-2-7-1 4-6 7-6 13 0 4 3 7 9 7z"/></svg>`;
