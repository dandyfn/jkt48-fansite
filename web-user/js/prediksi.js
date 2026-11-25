// prediksi.js
// Halaman Prediksi AI. Semua angka berasal dari model machine learning di backend:
//   GET /api/ml/status            -> kapan model dilatih
//   GET /api/ml/senbatsu          -> model 1: peluang masuk senbatsu
//   GET /api/ml/ssk               -> model 2: tebakan urutan SSK
//   GET /api/ml/kelompok          -> model 3: kelompok member (clustering)
//   GET /api/ml/mirip/{member_id} -> model 3: member yang paling mirip

function fotoKecil(member, indeks) {
  return htmlFoto(member, indeks, "kecil");
}

function chipTeam(member) {
  if (member.status === "eks") return `<span class="chip">Eks · Gen ${member.generasi}</span>`;
  return `<span class="chip ${kelasTeam(member.team)}">${esc(labelTeam(member.team))}</span>`;
}

function htmlAlasan(alasan) {
  if (!alasan || !alasan.length) return "";
  return `<ul class="pr-alasan">${alasan.map((a) =>
    `<li><span>${esc(a.label)}</span> <strong>${esc(a.nilai)}</strong></li>`).join("")}</ul>`;
}

function angka1(n) {
  return Number(n).toLocaleString("id-ID", { maximumFractionDigits: 1 });
}

// ======================================================================
// STATUS MODEL
// ======================================================================
async function muatStatus() {
  const el = document.getElementById("pr-status");
  try {
    const s = await ambil("/api/ml/status");
    const waktu = new Date(s.dilatih_pada).toLocaleString("id-ID", { dateStyle: "medium", timeStyle: "short" });
    el.innerHTML = `Model dilatih <strong>${esc(waktu)}</strong> dari ${angka(s.jumlah_data.show)} show,
      ${angka(s.jumlah_data.projek)} projek, ${angka(s.jumlah_data.ssk)} SSK, dan ${angka(s.jumlah_data.member)} member.`;
  } catch (e) {
    el.textContent = "Status model gagal dimuat.";
  }
}

// ======================================================================
// MODEL 1: SENBATSU
// ======================================================================
async function muatSenbatsu() {
  const wadah = document.getElementById("senbatsu-masuk");
  let data;
  try {
    data = await ambil("/api/ml/senbatsu");
  } catch (e) {
    wadah.innerHTML = `<li class="memuat">Prediksi senbatsu belum tersedia.</li>`;
    return;
  }
  document.getElementById("senbatsu-keterangan").innerHTML =
    `Single biasanya berisi <strong>${data.kursi} kursi</strong> (dilihat dari 5 single terakhir).
     Persentase = seberapa yakin AI member itu masuk, dihitung dari keadaannya hari ini:
     show, lagu, senbatsu sebelumnya, center, dan hasil SSK.`;

  const masuk = data.prediksi.filter((p) => p.masuk);
  wadah.innerHTML = masuk.map((p, i) => `
    <li>
      <a class="pr-kartu" href="detail.html?id=${p.member.id}">
        <span class="pr-nomor">${i + 1}</span>
        ${fotoKecil(p.member, i)}
        <span class="pr-isi">
          <span class="pr-nama">${esc(p.member.nama_panggilan)}</span>
          ${chipTeam(p.member)}
          <span class="pr-bar" aria-hidden="true"><span style="width:${p.peluang}%"></span></span>
          ${htmlAlasan(p.alasan)}
        </span>
        <span class="pr-persen">${angka1(p.peluang)}<small>%</small></span>
      </a>
    </li>`).join("");

  const hampir = data.prediksi.filter((p) => !p.masuk).slice(0, 8);
  document.getElementById("senbatsu-hampir").innerHTML = hampir.map((p, i) => `
    <li><a href="detail.html?id=${p.member.id}">
      <span class="pr-nomor-kecil">${masuk.length + i + 1}</span>
      <span class="pr-nama-kecil">${esc(p.member.nama_panggilan)}</span>
      <span class="pr-persen-kecil">${angka1(p.peluang)}%</span>
    </a></li>`).join("");

  const benar = data.uji.reduce((a, u) => a + u.benar, 0);
  const kursi = data.uji.reduce((a, u) => a + u.kursi, 0);
  document.getElementById("senbatsu-akurasi").textContent = `· ${benar} dari ${kursi} kursi tertebak (${angka1(data.akurasi)}%)`;
  document.getElementById("senbatsu-uji").innerHTML = data.uji.map((u) =>
    `<li>Single ${esc(tanggal(u.tanggal))}: <strong>${u.benar} dari ${u.kursi}</strong> member tertebak</li>`).join("");
}

// ======================================================================
// MODEL 2: SSK
// ======================================================================
async function muatSsk() {
  const wadah = document.getElementById("ssk-daftar");
  let data;
  try {
    data = await ambil("/api/ml/ssk");
  } catch (e) {
    wadah.innerHTML = `<li class="memuat">Prediksi SSK belum tersedia.</li>`;
    return;
  }
  document.getElementById("ssk-keterangan").innerHTML =
    `Mengikuti format SSK terakhir: <strong>${data.jumlah_peringkat} peringkat</strong>, dengan
     <strong>${data.kursi} teratas</strong> masuk senbatsu. Skor 0–100 adalah tebakan AI (100 = peringkat 1).`;

  wadah.innerHTML = data.prediksi.map((p, i) => `
    ${i === data.kursi ? `<li class="pr-garis-senbatsu"><span>Batas senbatsu</span></li>` : ""}
    <li class="${p.senbatsu ? "pr-ssk-senbatsu" : ""}">
      <a href="detail.html?id=${p.member.id}">
        <span class="pr-nomor-kecil">${p.peringkat}</span>
        ${fotoKecil(p.member, i)}
        <span class="pr-nama-kecil">${esc(p.member.nama_panggilan)}</span>
        <span class="pr-bar pr-bar-ssk" aria-hidden="true"><span style="width:${Math.max(0, Math.min(100, p.skor))}%"></span></span>
        <span class="pr-persen-kecil">${angka1(p.skor)}</span>
      </a>
    </li>`).join("");

  const u = data.uji;
  document.getElementById("ssk-akurasi").textContent = `· ${u.benar} dari ${u.kursi} senbatsu tertebak`;
  document.getElementById("ssk-uji").innerHTML =
    `Model diuji pada SSK ${esc(tanggal(u.tanggal))}: AI hanya belajar dari SSK sebelumnya, lalu menebak.
     Hasilnya <strong>${u.benar} dari ${u.kursi}</strong> member senbatsu tertebak, dan kemiripan urutannya
     <strong>${u.korelasi === null ? "–" : angka1(u.korelasi)}</strong> (skala 0 sampai 1; makin dekat 1, makin mirip urutan aslinya).`;
}

// ======================================================================
// MODEL 3: KELOMPOK + MEMBER MIRIP
// ======================================================================
let DATA_KELOMPOK = null;

function gambarKelompok() {
  const tampilEks = document.getElementById("kelompok-eks").checked;
  document.getElementById("kelompok-daftar").innerHTML = DATA_KELOMPOK.kelompok.map((k) => {
    const anggota = k.anggota.filter((m) => tampilEks || m.status !== "eks");
    const ciri = k.menonjol.length
      ? k.menonjol.map((c) => `<span class="chip">${esc(c.label)}</span>`).join(" ")
      : `<span class="chip">angka masih kecil</span>`;
    return `
      <article class="pr-kelompok-kartu">
        <div class="pr-kelompok-kepala">
          <h3>${esc(k.nama)}</h3>
          <span class="pr-jumlah">${anggota.length} member${tampilEks ? "" : " aktif & trainee"}</span>
        </div>
        <div class="chip-baris">Paling menonjol: ${ciri}</div>
        <dl class="pr-rata">
          <div><dt>Show / bulan</dt><dd>${angka1(k.rata.show_per_bulan)}</dd></div>
          <div><dt>Lagu / tahun</dt><dd>${angka1(k.rata.lagu_per_tahun)}</dd></div>
          <div><dt>Senbatsu</dt><dd>${Math.round(k.rata.rasio_senbatsu * 100)}%</dd></div>
          <div><dt>Center</dt><dd>${angka1(k.rata.center_total)}</dd></div>
        </dl>
        <ul class="pr-anggota">
          ${anggota.length ? anggota.map((m) => `
            <li><a href="detail.html?id=${m.id}" class="${m.status === "eks" ? "eks" : ""}">${esc(m.nama_panggilan)}</a></li>`).join("")
            : `<li class="redup">Tidak ada member aktif di kelompok ini.</li>`}
        </ul>
      </article>`;
  }).join("");
}

async function muatKelompok() {
  try {
    DATA_KELOMPOK = await ambil("/api/ml/kelompok");
  } catch (e) {
    document.getElementById("kelompok-daftar").innerHTML = `<p class="memuat">Kelompok member belum tersedia.</p>`;
    return;
  }
  gambarKelompok();

  // Isi saran nama untuk kotak "member mirip"
  const semua = DATA_KELOMPOK.kelompok.flatMap((k) => k.anggota)
    .sort((a, b) => a.nama_panggilan.localeCompare(b.nama_panggilan));
  document.getElementById("mirip-saran").innerHTML = semua.map((m) =>
    `<option value="${esc(m.nama_panggilan)}${m.status === "eks" ? " (eks)" : ""}"></option>`).join("");
  window.DAFTAR_MEMBER_ML = semua;
}

function htmlStat(f) {
  return `${angka1(f.show_per_bulan)} show/bln · ${angka1(f.lagu_per_tahun)} lagu/thn · ${Math.round(f.rasio_senbatsu * 100)}% senbatsu`;
}

async function cariMirip() {
  const hasil = document.getElementById("mirip-hasil");
  const teks = document.getElementById("mirip-input").value.replace(" (eks)", "").trim().toLowerCase();
  const daftar = window.DAFTAR_MEMBER_ML || [];
  const pilihan = daftar.find((m) => m.nama_panggilan.toLowerCase() === teks)
    || daftar.find((m) => m.nama_panggilan.toLowerCase().startsWith(teks));
  if (!teks || !pilihan) {
    hasil.innerHTML = `<p class="memuat">Member tidak ditemukan. Pilih nama dari daftar saran.</p>`;
    return;
  }
  hasil.innerHTML = `<p class="memuat">Mencari…</p>`;
  try {
    const data = await ambil(`/api/ml/mirip/${pilihan.id}`);
    const m = data.member;
    hasil.innerHTML = `
      <div class="pr-mirip-asal">
        ${fotoKecil(m, 0)}
        <div><strong>${esc(m.nama_panggilan)}</strong> ${chipTeam(m)}
          <p>Kelompok: <strong>${esc(m.kelompok)}</strong> · ${htmlStat(m.fitur)}</p></div>
      </div>
      <ol class="pr-mirip">
        ${data.mirip.map((x, i) => `
          <li><a href="detail.html?id=${x.member.id}">
            ${fotoKecil(x.member, i + 1)}
            <span class="pr-isi">
              <span class="pr-nama-kecil">${esc(x.member.nama_panggilan)} ${chipTeam(x.member)}</span>
              <span class="pr-sub">${esc(x.nama_kelompok)} · ${htmlStat(x.member.fitur)}</span>
            </span>
            <span class="pr-persen-kecil">${angka1(x.kemiripan)}%<small>mirip</small></span>
          </a></li>`).join("")}
      </ol>`;
  } catch (e) {
    hasil.innerHTML = `<p class="memuat">Gagal mencari member mirip.</p>`;
  }
}

// ======================================================================
// MULAI
// ======================================================================
document.getElementById("kelompok-eks").addEventListener("change", () => DATA_KELOMPOK && gambarKelompok());
document.getElementById("mirip-tombol").addEventListener("click", cariMirip);
document.getElementById("mirip-input").addEventListener("keydown", (e) => { if (e.key === "Enter") cariMirip(); });

muatStatus();
muatSenbatsu();
muatSsk();
muatKelompok();
