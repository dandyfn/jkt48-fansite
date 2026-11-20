// member.js
// Halaman member.html: kartu biodata semua member + pencarian.
//   GET /api/members?status=...
// (Dulu ini section 3 di halaman utama.)

// ======================================================================
// BIODATA MEMBER
// ======================================================================

// Data member yang sudah diambil dari API (sesuai filter status).
// Pencarian menyaring daftar ini langsung di browser, tanpa memanggil API lagi.
let semuaMember = [];

async function muatMember(status) {
  const grid = document.getElementById("daftar-member");
  grid.innerHTML = `<p class="memuat">Memuat member…</p>`;
  try {
    semuaMember = await ambil(status ? `/api/members?status=${status}` : "/api/members");
  } catch (e) {
    semuaMember = [];
    grid.innerHTML = `<p class="memuat">Data member gagal dimuat.</p>`;
    return;
  }
  tampilkanMember();
}

function tampilkanMember() {
  const grid = document.getElementById("daftar-member");
  const info = document.getElementById("info-cari");
  const kata = document.getElementById("cari-member").value.trim().toLowerCase();

  // Cocokkan kata kunci dengan nama panggilan, nama lengkap, stage name, kota, dan team
  const hasil = kata
    ? semuaMember.filter((m) =>
        [m.nama_panggilan, m.nama_lengkap, m.stage_name, m.hometown, m.tempat_lahir, m.team]
          .some((teks) => teks && teks.toLowerCase().includes(kata)))
    : semuaMember;

  info.textContent = kata
    ? `Menampilkan ${hasil.length} dari ${semuaMember.length} member untuk "${kata}"`
    : `${semuaMember.length} member`;

  if (hasil.length === 0) {
    grid.innerHTML = semuaMember.length === 0
      ? `<p class="memuat">Belum ada member dengan status ini.</p>`
      : `<p class="memuat">Tidak ada member yang cocok dengan "${esc(kata)}".</p>`;
    return;
  }
  grid.innerHTML = hasil.map(kartuMember).join("");
}

// Setiap kali isi kotak pencarian berubah, saring ulang
document.getElementById("cari-member").addEventListener("input", tampilkanMember);

function kartuMember(m, indeks) {
  const lahir = [m.tempat_lahir, m.tanggal_lahir ? tanggal(m.tanggal_lahir) : null].filter(Boolean).join(", ");
  const baris = [
    ["Lahir", lahir || "–"],
    ["Hometown", m.hometown || "–"],
    ["Umur", m.umur !== null ? m.umur + " tahun" : "–"],
    ["Zodiak", m.zodiak || "–"],
    ["Tinggi", m.tinggi_cm ? m.tinggi_cm + " cm" : "–"],
    ["Gol. darah", m.golongan_darah || "–"],
    ["Generasi", "Gen " + m.generasi],
    ["Team", m.team || "–"],
  ];
  return `
    <article class="kartu-member">
      <div class="atas">
        ${htmlFoto(m, indeks)}
        <div style="display:flex;flex-direction:column;gap:6px;min-width:0">
          <span class="chip status-${esc(m.status)}" style="align-self:flex-start">${esc(m.status[0].toUpperCase() + m.status.slice(1))}</span>
          <span class="nama">${esc(m.nama_panggilan)}</span>
          <span class="nama-lengkap">${esc(m.nama_lengkap)}</span>
          ${m.nama_jepang ? `<span class="nama-jepang" lang="ja">${esc(m.nama_jepang)}</span>` : ""}
          ${m.kapten ? `<span class="chip ikon-emas" style="align-self:flex-start">Kapten ${esc(m.kapten)}</span>` : ""}
          <span style="font-size:13px;color:var(--redup)">${m.lama_di_jkt48 ? "Di JKT48 " + esc(m.lama_di_jkt48) : ""}</span>
        </div>
      </div>
      ${m.jiko ? `<blockquote class="jiko"><span class="label-jiko">Jiko</span>${esc(m.jiko)}</blockquote>` : ""}
      <dl>
        ${baris.map(([dt, dd]) => `<div><dt>${dt}</dt><dd>${esc(dd)}</dd></div>`).join("")}
      </dl>
    </article>`;
}

// ======================================================================
// MULAI
// ======================================================================
pasangPil("[data-status]", "status", muatMember);
muatMember("");
