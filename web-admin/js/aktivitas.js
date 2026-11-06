// aktivitas.js
// Halaman Input Aktivitas: 4 tab (Show, Projek, SSK, Lencana).
// Setiap data yang disimpan otomatis menghasilkan poin di backend (lihat poin.py).

let semuaMember = [];       // semua member (untuk lencana & nama)
let memberAktif = [];       // aktif + trainee (untuk show, projek, SSK)
let pemilihShow, pemilihProjek;
let showTerakhir = null;

const LABEL_KATEGORI = { single: "Single", lagu: "Lagu", projek_grup: "Projek grup", film: "Film", iklan: "Iklan" };
const KATEGORI_JKT = ["single", "lagu", "projek_grup"];

// =====================================================================
// TAB
// =====================================================================
const tabs = document.querySelectorAll('[role="tab"]');
function bukaTab(tab) {
  tabs.forEach((t) => {
    const pilih = t === tab;
    t.classList.toggle("aktif", pilih);
    t.setAttribute("aria-selected", pilih);
    t.tabIndex = pilih ? 0 : -1;
    document.getElementById(t.getAttribute("aria-controls")).hidden = !pilih;
  });
  history.replaceState(null, "", "#" + tab.id.slice(2));   // ingat tab di alamat (#show, #ssk, ...)
}
tabs.forEach((t, i) => {
  t.addEventListener("click", () => bukaTab(t));
  t.addEventListener("keydown", (e) => {                      // panah kiri/kanan pindah tab
    if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
    const n = tabs[(i + (e.key === "ArrowRight" ? 1 : tabs.length - 1)) % tabs.length];
    bukaTab(n);
    n.focus();
  });
});
function bukaTabDariAlamat() {
  const tab = document.getElementById("t-" + location.hash.slice(1));
  if (tab) bukaTab(tab);
}
bukaTabDariAlamat();
window.addEventListener("hashchange", bukaTabDariAlamat);

function namaMember(id) {
  const m = semuaMember.find((x) => x.id === id);
  return m ? m.nama_panggilan : `#${id}`;
}

async function jalankan(tombol, aksi) {
  // Matikan tombol selama menunggu API, supaya tidak tersimpan dua kali
  const teks = tombol.textContent;
  tombol.disabled = true;
  tombol.textContent = "Menyimpan…";
  try {
    await aksi();
  } catch (err) {
    beriTahu(err.message, "gagal");
  } finally {
    tombol.disabled = false;
    tombol.textContent = teks;
  }
}

// =====================================================================
// SHOW
// =====================================================================
async function muatShow() {
  const daftar = await panggil("/api/show").catch(() => []);
  showTerakhir = daftar[0] || null;
  document.getElementById("daftar-setlist").innerHTML =
    [...new Set(daftar.map((s) => s.nama))].map((n) => `<option value="${esc(n)}">`).join("");
  document.getElementById("tabel-show").innerHTML = daftar.slice(0, 20).map((s) => `
    <tr>
      <td>${tanggal(s.tanggal)}</td>
      <td><strong>${esc(s.nama)}</strong><br><small class="redup">${esc(s.lokasi || "")}</small></td>
      <td><span class="chip">${s.peserta.length} member</span>
        <small class="redup">${esc(s.peserta.map((p) => p.nama_panggilan).join(", "))}</small></td>
      <td class="kanan"><button type="button" class="tombol-kecil bahaya" data-hapus-show="${s.id}">Hapus</button></td>
    </tr>`).join("") || `<tr><td colspan="4" class="redup">Belum ada show.</td></tr>`;
}

document.getElementById("show-lineup-lalu").addEventListener("click", () => {
  if (!showTerakhir) return beriTahu("Belum ada show sebelumnya.", "gagal");
  pemilihShow.kosongkan();
  pemilihShow.pilih(showTerakhir.peserta.map((p) => p.member_id));
  if (!document.getElementById("show-nama").value) document.getElementById("show-nama").value = showTerakhir.nama;
  beriTahu(`Lineup "${showTerakhir.nama}" (${tanggal(showTerakhir.tanggal)}) dipilih`);
});

document.getElementById("form-show").addEventListener("submit", (e) => {
  e.preventDefault();
  const data = {
    nama: document.getElementById("show-nama").value.trim(),
    tanggal: document.getElementById("show-tanggal").value,
    lokasi: document.getElementById("show-lokasi").value.trim() || null,
    member_ids: pemilihShow.ambilTerpilih().map((p) => p.member_id),
  };
  if (!data.nama || !data.tanggal) return beriTahu("Nama setlist dan tanggal wajib diisi.", "gagal");
  if (data.member_ids.length === 0) return beriTahu("Pilih minimal satu member yang tampil.", "gagal");

  jalankan(e.submitter, async () => {
    await panggil("/api/show", { method: "POST", body: data });
    beriTahu(`Show disimpan · ${data.member_ids.length} member mendapat poin show`);
    pemilihShow.kosongkan();   // nama & tanggal dibiarkan, memudahkan input show berikutnya
    await muatShow();
  });
});

document.getElementById("tabel-show").addEventListener("click", async (e) => {
  const t = e.target.closest("[data-hapus-show]");
  if (!t || !confirm("Hapus show ini? Poin show semua member yang tampil ikut terhapus.")) return;
  try {
    await panggil(`/api/show/${t.dataset.hapusShow}`, { method: "DELETE" });
    beriTahu("Show dihapus");
    await muatShow();
  } catch (err) { beriTahu(err.message, "gagal"); }
});

// =====================================================================
// PROJEK
// =====================================================================
const pilihKategori = document.getElementById("projek-kategori");
function aturKategori() {
  const jkt = KATEGORI_JKT.includes(pilihKategori.value);
  pemilihProjek.aturModeCenter(jkt);
  document.getElementById("info-poin-projek").textContent = jkt
    ? "Peserta +10 poin, center +15 poin tambahan"
    : `Peserta +${pilihKategori.value === "film" ? 20 : 12} poin (projek luar)`;
}
pilihKategori.addEventListener("change", aturKategori);

async function muatProjek() {
  const daftar = await panggil("/api/projek").catch(() => []);
  document.getElementById("ssk-projek").innerHTML = `<option value="">–</option>` +
    daftar.filter((p) => KATEGORI_JKT.includes(p.kategori))
      .map((p) => `<option value="${p.id}">${esc(p.judul)} (${tanggal(p.tanggal_rilis)})</option>`).join("");
  document.getElementById("tabel-projek").innerHTML = daftar.slice(0, 20).map((p) => {
    const center = p.peserta.filter((x) => x.is_center).map((x) => x.nama_panggilan);
    return `
      <tr>
        <td>${tanggal(p.tanggal_rilis)}</td>
        <td><strong>${esc(p.judul)}</strong></td>
        <td><span class="chip">${esc(LABEL_KATEGORI[p.kategori] || p.kategori)}</span></td>
        <td>${p.peserta.length} member${center.length ? `<br><small class="redup">Center: ${esc(center.join(", "))}</small>` : ""}</td>
        <td class="kanan"><button type="button" class="tombol-kecil bahaya" data-hapus-projek="${p.id}">Hapus</button></td>
      </tr>`;
  }).join("") || `<tr><td colspan="5" class="redup">Belum ada projek.</td></tr>`;
}

document.getElementById("form-projek").addEventListener("submit", (e) => {
  e.preventDefault();
  const data = {
    judul: document.getElementById("projek-judul").value.trim(),
    kategori: pilihKategori.value,
    tanggal_rilis: document.getElementById("projek-tanggal").value,
    deskripsi: document.getElementById("projek-deskripsi").value.trim() || null,
    cover_url: document.getElementById("projek-cover").value.trim() || null,
    peserta: pemilihProjek.ambilTerpilih(),
  };
  if (!data.judul || !data.tanggal_rilis) return beriTahu("Judul dan tanggal rilis wajib diisi.", "gagal");
  if (data.peserta.length === 0 && !confirm("Belum ada member yang dipilih. Tetap simpan projek tanpa peserta?")) return;

  jalankan(e.submitter, async () => {
    await panggil("/api/projek", { method: "POST", body: data });
    beriTahu(`Projek "${data.judul}" disimpan`);
    e.target.reset();
    document.getElementById("projek-tanggal").value = hariIni();
    pemilihProjek.kosongkan();
    aturKategori();
    await muatProjek();
  });
});

document.getElementById("tabel-projek").addEventListener("click", async (e) => {
  const t = e.target.closest("[data-hapus-projek]");
  if (!t || !confirm("Hapus projek ini? Poin semua pesertanya ikut terhapus.")) return;
  try {
    await panggil(`/api/projek/${t.dataset.hapusProjek}`, { method: "DELETE" });
    beriTahu("Projek dihapus");
    await muatProjek();
  } catch (err) { beriTahu(err.message, "gagal"); }
});

// =====================================================================
// SSK
// =====================================================================
function poinSsk(n) { return 33 - n + (n <= 16 ? 10 : 0); }

function buatBarisSsk() {
  const opsi = `<option value="">–</option>` +
    memberAktif.map((m) => `<option value="${m.id}">${esc(m.nama_panggilan)} (${esc(m.team || "Trainee")})</option>`).join("");
  let html = "";
  for (let n = 1; n <= 32; n++) {
    if (n === 1) html += `<p class="judul-blok-ssk">Single utama (1–16)</p>`;
    if (n === 17) html += `<p class="judul-blok-ssk">Coupling (17–32)</p>`;
    html += `
      <div class="baris-ssk${n <= 16 ? " utama" : ""}">
        <label for="ssk-${n}" class="no-ssk">${n}</label>
        <select id="ssk-${n}" data-peringkat="${n}">${opsi}</select>
        <span class="poin-ssk">+${poinSsk(n)}</span>
      </div>`;
  }
  document.getElementById("baris-ssk").innerHTML = html;
}

// Tandai merah kalau satu member dipilih di dua peringkat
document.getElementById("baris-ssk").addEventListener("change", () => {
  const semua = [...document.querySelectorAll("[data-peringkat]")];
  const hitung = {};
  semua.forEach((s) => s.value && (hitung[s.value] = (hitung[s.value] || 0) + 1));
  semua.forEach((s) => s.classList.toggle("dobel", !!s.value && hitung[s.value] > 1));
});

async function muatSsk() {
  const daftar = await panggil("/api/ssk").catch(() => []);
  document.getElementById("tabel-ssk").innerHTML = daftar.map((s) => `
    <tr>
      <td>${tanggal(s.tanggal_pengumuman)}</td>
      <td><strong>${esc(s.judul)}</strong></td>
      <td>${s.hasil.slice(0, 3).map((h) => `${h.peringkat}. ${esc(h.nama_panggilan)}`).join("<br>")}</td>
      <td>${s.hasil.length} member</td>
      <td class="kanan"><button type="button" class="tombol-kecil bahaya" data-hapus-ssk="${s.id}">Hapus</button></td>
    </tr>`).join("") || `<tr><td colspan="5" class="redup">Belum ada SSK.</td></tr>`;
}

document.getElementById("form-ssk").addEventListener("submit", (e) => {
  e.preventDefault();
  const hasil = [...document.querySelectorAll("[data-peringkat]")]
    .filter((s) => s.value)
    .map((s) => ({ member_id: Number(s.value), peringkat: Number(s.dataset.peringkat) }));
  const data = {
    judul: document.getElementById("ssk-judul").value.trim(),
    tanggal_pengumuman: document.getElementById("ssk-tanggal").value,
    projek_id: Number(document.getElementById("ssk-projek").value) || null,
    hasil,
  };
  if (!data.judul || !data.tanggal_pengumuman) return beriTahu("Judul dan tanggal pengumuman wajib diisi.", "gagal");
  if (hasil.length === 0) return beriTahu("Isi minimal satu peringkat.", "gagal");
  if (document.querySelector(".dobel")) return beriTahu("Ada member yang dipilih di lebih dari satu peringkat (ditandai merah).", "gagal");

  jalankan(e.submitter, async () => {
    await panggil("/api/ssk", { method: "POST", body: data });
    beriTahu(`Hasil SSK "${data.judul}" disimpan · ${hasil.length} member mendapat poin`);
    e.target.reset();
    document.getElementById("ssk-tanggal").value = hariIni();
    await muatSsk();
  });
});

document.getElementById("tabel-ssk").addEventListener("click", async (e) => {
  const t = e.target.closest("[data-hapus-ssk]");
  if (!t || !confirm("Hapus hasil SSK ini? Poin SSK semua member ikut terhapus.")) return;
  try {
    await panggil(`/api/ssk/${t.dataset.hapusSsk}`, { method: "DELETE" });
    beriTahu("Hasil SSK dihapus");
    await muatSsk();
  } catch (err) { beriTahu(err.message, "gagal"); }
});

// =====================================================================
// LENCANA
// =====================================================================
const LABEL_LENCANA = { kapten: "Kapten", wakil_kapten: "Wakil kapten", lainnya: "Lainnya" };

async function muatLencana() {
  const daftar = await panggil("/api/lencana").catch(() => []);
  document.getElementById("tabel-lencana").innerHTML = daftar.map((l) => `
    <tr>
      <td><strong>${esc(l.nama_panggilan)}</strong></td>
      <td>${esc(LABEL_LENCANA[l.jenis] || l.jenis)} ${esc(l.keterangan || "")}</td>
      <td>${tanggal(l.tanggal_mulai)} – ${l.tanggal_selesai ? tanggal(l.tanggal_selesai) : "sekarang"}</td>
      <td>${l.masih_menjabat ? '<span class="chip status-aktif">Menjabat</span>' : '<span class="chip status-eks">Selesai</span>'}</td>
      <td class="kanan"><div class="aksi">
        ${l.masih_menjabat ? `<button type="button" class="tombol-kecil" data-akhiri="${l.id}">Akhiri hari ini</button>` : ""}
        <button type="button" class="tombol-kecil bahaya" data-hapus-lencana="${l.id}">Hapus</button>
      </div></td>
    </tr>`).join("") || `<tr><td colspan="5" class="redup">Belum ada lencana.</td></tr>`;
}

document.getElementById("form-lencana").addEventListener("submit", (e) => {
  e.preventDefault();
  const data = {
    member_id: Number(document.getElementById("lencana-member").value),
    jenis: document.getElementById("lencana-jenis").value,
    keterangan: document.getElementById("lencana-keterangan").value.trim() || null,
    tanggal_mulai: document.getElementById("lencana-mulai").value,
    tanggal_selesai: document.getElementById("lencana-selesai").value || null,
  };
  if (!data.member_id || !data.tanggal_mulai) return beriTahu("Member dan tanggal mulai wajib diisi.", "gagal");

  jalankan(e.submitter, async () => {
    await panggil("/api/lencana", { method: "POST", body: data });
    beriTahu(`Lencana ${LABEL_LENCANA[data.jenis]} untuk ${namaMember(data.member_id)} disimpan`);
    e.target.reset();
    document.getElementById("lencana-mulai").value = hariIni();
    await muatLencana();
  });
});

document.getElementById("tabel-lencana").addEventListener("click", async (e) => {
  const akhiri = e.target.closest("[data-akhiri]");
  const hapus = e.target.closest("[data-hapus-lencana]");
  try {
    if (akhiri && confirm("Akhiri jabatan ini per hari ini? Bingkai kapten di web user akan hilang.")) {
      await panggil(`/api/lencana/${akhiri.dataset.akhiri}`, { method: "PUT", body: { tanggal_selesai: hariIni() } });
      beriTahu("Jabatan diakhiri");
      await muatLencana();
    }
    if (hapus && confirm("Hapus lencana ini? Poin 'diangkat kapten' ikut terhapus.")) {
      await panggil(`/api/lencana/${hapus.dataset.hapusLencana}`, { method: "DELETE" });
      beriTahu("Lencana dihapus");
      await muatLencana();
    }
  } catch (err) { beriTahu(err.message, "gagal"); }
});

// =====================================================================
// MULAI
// =====================================================================
(async function mulai() {
  try {
    semuaMember = await panggil("/api/members");
  } catch (err) {
    beriTahu(err.message, "gagal");
    return;
  }
  memberAktif = semuaMember.filter((m) => m.status !== "eks");

  pemilihShow = buatPemilih(document.getElementById("pemilih-show"), memberAktif);
  pemilihProjek = buatPemilih(document.getElementById("pemilih-projek"), memberAktif, { denganCenter: true });
  aturKategori();
  buatBarisSsk();
  document.getElementById("lencana-member").innerHTML = `<option value="">Pilih member…</option>` +
    semuaMember.map((m) => `<option value="${m.id}">${esc(m.nama_panggilan)} – ${esc(m.nama_lengkap)}</option>`).join("");

  ["show-tanggal", "projek-tanggal", "ssk-tanggal", "lencana-mulai"]
    .forEach((id) => (document.getElementById(id).value = hariIni()));

  await Promise.all([muatShow(), muatProjek(), muatSsk(), muatLencana()]);
})();
