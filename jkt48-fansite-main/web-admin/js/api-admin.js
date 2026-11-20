// api-admin.js
// Fungsi bantu untuk SEMUA halaman web admin:
//   - menyimpan token login
//   - memanggil API dengan token (panggil)
//   - menerjemahkan pesan error API ke bahasa Indonesia
//   - notifikasi kecil (beriTahu) dan fungsi format

const API_URL = "http://127.0.0.1:8000";
const KUNCI_TOKEN = "jkt48_admin_token";

// ---------------------------------------------------------------------
// Token
// ---------------------------------------------------------------------
function ambilToken() {
  return localStorage.getItem(KUNCI_TOKEN);
}
function simpanToken(token) {
  localStorage.setItem(KUNCI_TOKEN, token);
}
function hapusToken() {
  localStorage.removeItem(KUNCI_TOKEN);
}

// ---------------------------------------------------------------------
// Memanggil API
// ---------------------------------------------------------------------
class GalatApi extends Error {
  constructor(pesan, status, data) {
    super(pesan);
    this.status = status;
    this.data = data;
  }
}

// Contoh:
//   await panggil("/api/members")                                   -> GET
//   await panggil("/api/members", { method: "POST", body: {...} })  -> POST JSON
async function panggil(path, { method = "GET", body } = {}) {
  const headers = {};
  const token = ambilToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  let isi;
  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    isi = JSON.stringify(body);
  }

  let jawaban;
  try {
    jawaban = await fetch(API_URL + path, { method, headers, body: isi });
  } catch (e) {
    throw new GalatApi("Tidak bisa terhubung ke API. Pastikan uvicorn sudah menyala.", 0);
  }

  // Token hilang / kedaluwarsa -> kembali ke halaman login
  if (jawaban.status === 401) {
    hapusToken();
    location.href = "login.html?pesan=sesi";
    throw new GalatApi("Sesi login berakhir", 401);
  }
  if (jawaban.status === 204) return null;

  const data = await jawaban.json().catch(() => null);
  if (!jawaban.ok) throw new GalatApi(terjemahkanError(data, jawaban.status), jawaban.status, data);
  return data;
}

// Ubah pesan error API menjadi kalimat yang mudah dibaca
const NAMA_KOLOM = {
  nama_lengkap: "Nama lengkap", nama_panggilan: "Nama panggilan", generasi: "Generasi",
  tinggi_cm: "Tinggi", golongan_darah: "Golongan darah", status: "Status",
  tanggal_lahir: "Tanggal lahir", tanggal_bergabung: "Tanggal bergabung",
  tanggal_lulus: "Tanggal lulus", tanggal_cutoff: "Tanggal saldo awal",
};
function terjemahkanError(data, status) {
  if (!data) return `Terjadi kesalahan (kode ${status})`;
  if (typeof data.detail === "string") return data.detail;
  if (Array.isArray(data.detail)) {
    return data.detail.map((e) => {
      const kolom = e.loc[e.loc.length - 1];
      const nama = NAMA_KOLOM[kolom] || kolom;
      const ctx = e.ctx || {};
      const arti = {
        missing: "wajib diisi",
        greater_than_equal: `minimal ${ctx.ge}`,
        less_than_equal: `maksimal ${ctx.le}`,
        string_too_short: "tidak boleh kosong",
        literal_error: "pilihannya tidak valid",
        date_from_datetime_parsing: "format tanggal salah",
        date_parsing: "format tanggal salah",
        int_parsing: "harus berupa angka",
      }[e.type] || e.msg;
      return `${nama}: ${arti}`;
    }).join(" · ");
  }
  return `Terjadi kesalahan (kode ${status})`;
}

// ---------------------------------------------------------------------
// Notifikasi kecil di pojok kanan bawah
// ---------------------------------------------------------------------
function beriTahu(pesan, jenis = "sukses") {
  let wadah = document.getElementById("wadah-notifikasi");
  if (!wadah) {
    wadah = document.createElement("div");
    wadah.id = "wadah-notifikasi";
    wadah.setAttribute("aria-live", "polite");
    document.body.appendChild(wadah);
  }
  const el = document.createElement("div");
  el.className = `notifikasi notifikasi-${jenis}`;
  el.textContent = pesan;
  wadah.appendChild(el);
  setTimeout(() => el.remove(), jenis === "gagal" ? 7000 : 3500);
}

// ---------------------------------------------------------------------
// Format & keamanan teks
// ---------------------------------------------------------------------
function esc(teks) {
  if (teks === null || teks === undefined) return "";
  return String(teks)
    .replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;").replaceAll("'", "&#39;");
}
function angka(n) {
  return n === null || n === undefined ? "–" : Number(n).toLocaleString("id-ID", { maximumFractionDigits: 1 });
}
function tanggal(str, pilihan = { day: "numeric", month: "short", year: "numeric" }) {
  if (!str) return "–";
  return new Date(str + "T00:00:00").toLocaleDateString("id-ID", pilihan);
}
function hariIni() {
  // "YYYY-MM-DD" sesuai zona waktu laptop
  const d = new Date();
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
}
