// main.js
// Mengisi halaman utama dengan data dari API:
//   Section 1 -> GET /api/leaderboard
//   Section 2 -> GET /api/grup  dan  GET /api/projek?kategori=...
//   (Biodata member pindah ke member.html -> js/member.js)

// ======================================================================
// SECTION 1: LEADERBOARD
// ======================================================================

async function muatLeaderboard(periode) {
  const podium = document.getElementById("podium");
  const lainnya = document.getElementById("peringkat-lain");
  const status = document.getElementById("status-leaderboard");
  podium.innerHTML = `<p class="memuat">Memuat leaderboard…</p>`;
  lainnya.innerHTML = "";

  let hasil;
  try {
    hasil = await ambil(`/api/leaderboard?periode=${periode}`);
  } catch (e) {
    podium.innerHTML = `<p class="memuat">Leaderboard gagal dimuat.</p>`;
    return;
  }

  const KATA = { minggu: "minggu ini", bulan: "bulan ini", karier: "sepanjang karier" };
  document.getElementById("kata-periode").textContent = KATA[periode];
  document.getElementById("label-periode").textContent =
    periode === "minggu" ? `${tanggal(hasil.mulai, { day: "numeric", month: "short" })} – ${tanggal(hasil.selesai)}`
    : periode === "bulan" ? tanggal(hasil.mulai, { month: "long", year: "numeric" })
    : `sepanjang karier, termasuk total lagu & center sebelum April 2026`;

  const data = hasil.data;
  if (data.length === 0 || data.every((d) => d.skor === 0)) {
    podium.innerHTML = `
      <div class="memuat">
        <p>Belum ada poin di periode ini, karena data show &amp; projek baru belum diinput.</p>
        ${periode !== "karier" ? `<button type="button" class="tombol-semua" id="ke-karier">Lihat peringkat sepanjang karier</button>` : ""}
      </div>`;
    const ke = document.getElementById("ke-karier");
    if (ke) ke.addEventListener("click", () => document.querySelector('[data-periode="karier"]').click());
    status.textContent = "";
    aturTombolSemua(0, 0);
    return false;
  }

  // Podium: urutan tampil 2 - 1 - 3 (juara 1 di tengah)
  const top3 = data.slice(0, 3);
  const urutanTampil = [top3[1], top3[0], top3[2]].filter(Boolean);
  podium.innerHTML = urutanTampil.map((m) => kartuPodium(m, data.indexOf(m), periode)).join("");

  // Peringkat 4-12 selalu tampil; 13 ke bawah disembunyikan di balik tombol
  lainnya.innerHTML = data.slice(3, JUMLAH_DEFAULT).map((m, i) => kartuPeringkat(m, i + 3, periode)).join("");
  const sisa = data.slice(JUMLAH_DEFAULT);
  document.getElementById("peringkat-tambahan").innerHTML =
    sisa.map((m, i) => kartuPeringkat(m, i + JUMLAH_DEFAULT, periode)).join("");
  aturTombolSemua(sisa.length, data.length);

  status.textContent = `${data.length} member aktif & trainee ikut dihitung.`;
  return true;
}

// Berapa peringkat yang tampil tanpa menekan tombol
const JUMLAH_DEFAULT = 12;

const IKON_PANAH =
  `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg>`;

function aturTombolSemua(jumlahSisa, total) {
  const tombol = document.getElementById("tombol-semua");
  const tambahan = document.getElementById("peringkat-tambahan");
  // Setiap kali leaderboard dimuat ulang, kembali ke keadaan tertutup
  tambahan.hidden = true;
  tombol.setAttribute("aria-expanded", "false");
  tombol.hidden = jumlahSisa === 0;  // member 12 atau kurang -> tombol tidak perlu
  tombol.dataset.teksBuka = `Lihat peringkat ${JUMLAH_DEFAULT + 1}–${total}`;
  tombol.innerHTML = `${tombol.dataset.teksBuka} ${IKON_PANAH}`;
}

document.getElementById("tombol-semua").addEventListener("click", (e) => {
  const tombol = e.currentTarget;
  const tambahan = document.getElementById("peringkat-tambahan");
  const buka = tambahan.hidden;           // kalau sedang tersembunyi -> buka
  tambahan.hidden = !buka;
  tombol.setAttribute("aria-expanded", String(buka));
  tombol.innerHTML = `${buka ? "Sembunyikan" : tombol.dataset.teksBuka} ${IKON_PANAH}`;
  if (!buka) document.getElementById("peringkat-lain").scrollIntoView({ behavior: "smooth", block: "end" });
});

function kartuPodium(m, indeks, periode) {
  const posisi = indeks + 1;
  const mahkota = posisi === 1
    ? `<span class="bintang-periode">
         <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#F6E7B8" stroke-width="2" stroke-linejoin="round" aria-hidden="true"><path d="M3 18h18l-2-11-5 5-2-7-2 7-5-5z"/></svg>
         ${periode === "karier" ? "Bintang sepanjang karier" : `Bintang ${periode} ini`}
       </span>`
    : "";
  return `
    <a class="kartu-podium posisi-${posisi}" href="detail.html?id=${m.member_id}">
      <div style="position:relative">
        ${htmlFoto(m, indeks)}
        <span class="medali medali-${posisi}" aria-label="Peringkat ${m.peringkat}">${m.peringkat}</span>
        ${mahkota}
      </div>
      <div class="podium-info">
        <div>
          <div class="nama-besar">${esc(m.nama_panggilan)}</div>
          <div class="chip-baris">
            <span class="chip">Gen ${esc(m.generasi)}</span>
            <span class="chip ${kelasTeam(m.team)}">${esc(labelTeam(m.team))}</span>
          </div>
        </div>
        <div>
          <div class="skor-besar">${angka(m.skor)}</div>
          <div class="label-poin">poin</div>
        </div>
      </div>
      ${periode === "karier" ? "" : `
      <div class="podium-bawah">
        <span class="streak">${IKON_STREAK} Streak ${m.streak_minggu} minggu</span>
        ${htmlPerubahan(m.perubahan_peringkat)}
      </div>`}
    </a>`;
}

function kartuPeringkat(m, indeks, periode) {
  const karier = periode === "karier";
  return `
    <a class="kartu-peringkat" href="detail.html?id=${m.member_id}">
      <span class="nomor">${m.peringkat}</span>
      ${htmlFoto(m, indeks, "kecil")}
      <div class="tengah">
        <span class="nama">${esc(m.nama_panggilan)}</span>
        <span class="sub">Gen ${esc(m.generasi)} · ${esc(m.team || "Trainee")}</span>
        ${karier ? "" : `<span class="streak" style="font-size:13px;font-weight:700">${IKON_STREAK} ${m.streak_minggu} minggu</span>`}
      </div>
      <div>
        <div class="skor">${angka(m.skor)}</div>
        <div class="ubah">${karier ? "poin" : htmlPerubahan(m.perubahan_peringkat)}</div>
      </div>
    </a>`;
}

// ======================================================================
// SECTION 2: PROFIL GRUP
// ======================================================================

async function muatProfilGrup() {
  let grup;
  try {
    grup = await ambil("/api/grup");
  } catch (e) {
    document.getElementById("deskripsi-grup").textContent = "Profil grup gagal dimuat.";
    return;
  }

  document.getElementById("nama-grup").textContent = grup.info.nama;
  document.getElementById("deskripsi-grup").textContent =
    grup.info.deskripsi || "Deskripsi grup belum diisi dari web admin.";

  const s = grup.statistik;
  const tahun = grup.info.tanggal_dibentuk ? grup.info.tanggal_dibentuk.slice(0, 4) : "–";
  const ubin = [
    [tahun, "Tahun dibentuk", "#FFF2F7"],
    [angka(s.jumlah_single), "Jumlah single", "#F4F0FC"],
    [angka(s.jumlah_lagu), "Jumlah lagu", "#FFF4EC"],
    [angka(s.member_aktif), "Member aktif", "#EEF7F3"],
    [angka(s.member_trainee), "Member trainee", "#F4F0FC"],
    [angka(s.member_eks), "Member eks", "#F5F1F2"],
  ];
  document.getElementById("statistik-grup").innerHTML = ubin
    .map(([nilai, label, warna]) =>
      `<div class="ubin" style="background:${warna}"><span class="angka">${nilai}</span><span class="label">${label}</span></div>`)
    .join("");

  // Kartu rilis terbaru
  const r = grup.rilis_terbaru;
  const kartuRilis = document.getElementById("rilis-terbaru");
  if (r) {
    const center = r.peserta.filter((p) => p.is_center).map((p) => p.nama_panggilan).join(", ");
    kartuRilis.innerHTML = `
      <span class="label-kartu label-emas">Rilis terbaru</span>
      <div class="sampul">${r.cover_url ? `<img src="${esc(r.cover_url)}" alt="Cover ${esc(r.judul)}">` : "Cover belum ada"}</div>
      <span class="judul-kartu">${esc(r.judul)}</span>
      <span class="keterangan">Rilis ${tanggal(r.tanggal_rilis)}${center ? " · Center: " + esc(center) : ""}</span>`;
  } else {
    kartuRilis.innerHTML = `<span class="label-kartu label-emas">Rilis terbaru</span><span>Belum ada rilisan.</span>`;
  }

  // Kartu projek terbaru
  const p = grup.projek_terbaru;
  document.getElementById("projek-terbaru").innerHTML = `
    <span class="label-kartu label-putih">Projek terbaru</span>
    <span class="judul-kartu">${p ? esc(p.judul) : "Belum ada projek grup"}</span>
    <span style="color:var(--teks-2)">${p ? esc(p.deskripsi || "") + " · " + tanggal(p.tanggal_rilis) : ""}</span>`;
}

async function muatDaftarRilis(kategori) {
  const daftar = document.getElementById("daftar-rilis");
  daftar.innerHTML = `<li class="memuat">Memuat…</li>`;
  try {
    const projek = await ambil(`/api/projek?kategori=${kategori}`);
    daftar.innerHTML = projek.length
      ? projek.map((p, i) => `
          <li>
            <span class="no">${String(projek.length - i).padStart(2, "0")}</span>
            <span class="judul">${esc(p.judul)}</span>
            <span class="tahun">${tanggal(p.tanggal_rilis, { year: "numeric" })}</span>
          </li>`).join("")
      : `<li class="memuat">Belum ada ${kategori}.</li>`;
  } catch (e) {
    daftar.innerHTML = `<li class="memuat">Gagal memuat.</li>`;
  }
}

// ======================================================================
// MULAI
// ======================================================================

pasangPil("[data-periode]", "periode", muatLeaderboard);
pasangPil("[data-kategori]", "kategori", muatDaftarRilis);

// Buka mingguan dulu; kalau minggu ini belum ada poin sama sekali, pindah ke "Karier"
muatLeaderboard("minggu").then((ada) => {
  if (ada === false) document.querySelector('[data-periode="karier"]').click();
});
muatProfilGrup();
muatDaftarRilis("single");
