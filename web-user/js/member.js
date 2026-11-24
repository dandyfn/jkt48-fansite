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
// PERBANDINGAN ANTAR GEN
// ======================================================================
// Rata-rata umur & tinggi per generasi, digambar sebagai batang mendatar.
//   GET /api/infografis                   -> member aktif + trainee
//   GET /api/infografis?termasuk_eks=true -> semua member (centang "Member all time")
// Kedua daftar disimpan di DATA_GEN supaya tidak diambil ulang tiap centang diklik.
const DATA_GEN = { aktif: null, alltime: null };

function formatAngka(nilai) {
  return nilai.toLocaleString("id-ID", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
}

// [{gen, rata, jumlah}] untuk satu kolom (umur / tinggi_cm). Member tanpa data dilewati.
function rataPerGen(daftar, kolom) {
  const kelompok = {};
  daftar.forEach((m) => {
    if (m[kolom] === null || m[kolom] === undefined) return;
    (kelompok[m.generasi] = kelompok[m.generasi] || []).push(m[kolom]);
  });
  return Object.keys(kelompok).map(Number).sort((a, b) => a - b).map((gen) => {
    const nilai = kelompok[gen];
    return { gen, jumlah: nilai.length, rata: nilai.reduce((a, b) => a + b, 0) / nilai.length };
  });
}

function grafikGen({ judul, satuan, satuanPendek, kolom, daftar }) {
  const baris = rataPerGen(daftar, kolom);
  if (baris.length === 0) return `<p class="memuat">Belum ada data ${judul.toLowerCase()}.</p>`;

  // Rata-rata keseluruhan (semua member yang punya data, bukan rata-rata dari rata-rata)
  const semuaNilai = daftar.map((m) => m[kolom]).filter((v) => v !== null && v !== undefined);
  const rataSemua = semuaNilai.reduce((a, b) => a + b, 0) / semuaNilai.length;

  // Batang dimulai dari sedikit di bawah nilai terkecil, supaya beda 2-3 cm tetap terlihat.
  const terkecil = Math.min(...baris.map((b) => b.rata));
  const terbesar = Math.max(...baris.map((b) => b.rata));
  const dasar = Math.max(0, Math.floor(terkecil) - 3);
  const lebar = (v) => 8 + ((v - dasar) / ((terbesar - dasar) || 1)) * 92;   // 8%..100%

  const isi = baris.map((b) => {
    const kelas = b.rata === terbesar ? "tertinggi" : b.rata === terkecil ? "terendah" : "";
    return `
      <li class="gb-baris ${kelas}">
        <span class="gb-gen">Gen ${b.gen}</span>
        <span class="gb-jalur" aria-hidden="true"><span class="gb-isi" style="width:${lebar(b.rata).toFixed(1)}%"></span></span>
        <span class="gb-nilai">${formatAngka(b.rata)} <small>${satuanPendek}</small></span>
        <span class="gb-jumlah">${b.jumlah} org</span>
      </li>`;
  }).join("");

  const genTertinggi = baris.filter((b) => b.rata === terbesar).map((b) => "Gen " + b.gen).join(", ");
  const genTerendah = baris.filter((b) => b.rata === terkecil).map((b) => "Gen " + b.gen).join(", ");

  return `
    <div class="grafik-kepala">
      <div><h3>${judul}</h3><p>per generasi · dalam ${satuan}</p></div>
      <div class="grafik-angka"><strong>${formatAngka(rataSemua)}</strong><span>rata-rata semua</span></div>
    </div>
    <ol class="gb-daftar">${isi}</ol>
    <p class="kartu-catatan">
      Tertinggi: <strong>${genTertinggi}</strong> · Terendah: <strong>${genTerendah}</strong>.
      Batang dimulai dari ${dasar} ${satuanPendek} supaya selisih kecil tetap terlihat.
    </p>`;
}

function gambarGen() {
  const alltime = document.getElementById("gen-alltime").checked;
  const daftar = alltime ? DATA_GEN.alltime : DATA_GEN.aktif;
  if (!daftar) return;
  document.getElementById("gen-keterangan").textContent = alltime
    ? `Rata-rata dari ${daftar.length} member all time (aktif, trainee, dan eks). Umur = umur saat ini.`
    : `Rata-rata dari ${daftar.length} member aktif & trainee. Centang "Member all time" untuk ikut menghitung member eks.`;
  document.getElementById("grafik-umur").innerHTML =
    grafikGen({ judul: "Rata-rata umur", satuan: "tahun", satuanPendek: "th", kolom: "umur", daftar });
  document.getElementById("grafik-tinggi").innerHTML =
    grafikGen({ judul: "Rata-rata tinggi", satuan: "cm", satuanPendek: "cm", kolom: "tinggi_cm", daftar });
}

async function muatGen() {
  const alltime = document.getElementById("gen-alltime").checked;
  const kunci = alltime ? "alltime" : "aktif";
  if (!DATA_GEN[kunci]) {
    try {
      DATA_GEN[kunci] = await ambil(alltime ? "/api/infografis?termasuk_eks=true" : "/api/infografis");
    } catch (e) {
      document.getElementById("gen-keterangan").textContent = "Data perbandingan gen gagal dimuat.";
      return;
    }
  }
  gambarGen();
}

document.getElementById("gen-alltime").addEventListener("change", muatGen);

// ======================================================================
// MULAI
// ======================================================================
pasangPil("[data-status]", "status", muatMember);
muatMember("");
muatGen();
