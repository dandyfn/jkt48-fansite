// ml.js (admin)
// Halaman Model AI:
//   GET  /api/ml/status -> kapan dilatih, hasil uji, apakah data sudah berubah sejak dilatih
//   POST /api/ml/latih  -> latih ulang ketiga model (butuh login admin)

function angka1(n) {
  return n === null || n === undefined ? "–" : Number(n).toLocaleString("id-ID", { maximumFractionDigits: 2 });
}

function gambarBobot(id, daftar) {
  const el = document.getElementById(id);
  if (!daftar || !daftar.length) { el.innerHTML = `<li class="redup">Belum ada.</li>`; return; }
  const maks = Math.max(...daftar.map((b) => Math.abs(b.bobot))) || 1;
  el.innerHTML = daftar.map((b) => `
    <li>
      <span class="ml-bobot-label">${esc(b.label)}</span>
      <span class="ml-bobot-jalur"><span class="${b.bobot >= 0 ? "naik" : "turun"}" style="width:${(Math.abs(b.bobot) / maks * 100).toFixed(0)}%"></span></span>
      <span class="ml-bobot-angka">${b.bobot >= 0 ? "+" : "−"}${angka1(Math.abs(b.bobot))}</span>
    </li>`).join("");
}

function gambarStatus(s) {
  const waktu = new Date(s.dilatih_pada).toLocaleString("id-ID", { dateStyle: "long", timeStyle: "short" });
  document.getElementById("waktu-latih").textContent = `Terakhir dilatih ${waktu} · ${angka1(s.durasi_detik)} detik`;

  const status = document.getElementById("ml-status");
  status.hidden = false;
  status.className = "ml-status " + (s.perlu_latih_ulang ? "perlu" : "aman");
  status.innerHTML = s.perlu_latih_ulang
    ? `<strong>Data sudah berubah sejak model dilatih.</strong> Tekan "Latih ulang model" supaya prediksi memakai data terbaru.`
    : `<strong>Model sudah memakai data terbaru.</strong> Belum perlu dilatih ulang.`;

  const j = s.jumlah_data;
  document.getElementById("ml-ringkas").innerHTML = [
    ["Member", j.member], ["Show", j.show], ["Projek", j.projek], ["SSK", j.ssk],
  ].map(([label, n]) => `<div class="kotak-ringkas"><span class="angka">${angka(n)}</span><span class="label">${label} dipakai belajar</span></div>`).join("");

  // Model 1
  const m1 = s.senbatsu;
  document.getElementById("ml-senbatsu").innerHTML = !m1.siap ? esc(m1.pesan) : `
    <p class="ml-angka-besar">${angka1(m1.akurasi)}%<small>kursi tertebak saat diuji</small></p>
    <p class="redup kecil">Belajar dari ${m1.jumlah_soal} single (${angka(m1.jumlah_baris)} baris "soal"). Uji jujur pada 5 single terakhir:</p>
    <ul class="ml-uji">${m1.uji.map((u) => `<li>${esc(tanggal(u.tanggal))}: <strong>${u.benar}/${u.kursi}</strong></li>`).join("")}</ul>`;

  // Model 2
  const m2 = s.ssk;
  document.getElementById("ml-ssk").innerHTML = !m2.siap ? esc(m2.pesan) : `
    <p class="ml-angka-besar">${m2.uji.benar}/${m2.uji.kursi}<small>senbatsu SSK ${esc(tanggal(m2.uji.tanggal))} tertebak</small></p>
    <p class="redup kecil">Belajar dari ${m2.jumlah_soal} SSK (${angka(m2.jumlah_baris)} baris). Kemiripan urutan (Spearman):
      <strong>${angka1(m2.uji.korelasi)}</strong>. Skala 0–1, makin dekat 1 makin mirip urutan asli.</p>`;

  // Model 3
  const m3 = s.kelompok;
  document.getElementById("ml-kelompok").innerHTML = `
    <p class="ml-angka-besar">${m3.jumlah_kelompok}<small>kelompok member</small></p>
    <p class="redup kecil">Kerapian kelompok (silhouette): <strong>${angka1(m3.silhouette)}</strong>.
      Skala −1 sampai 1; di atas 0,25 berarti kelompoknya cukup jelas terpisah.</p>`;

  gambarBobot("bobot-senbatsu", m1.bobot);
  gambarBobot("bobot-ssk", m2.bobot);
}

async function muatStatus() {
  try {
    gambarStatus(await panggil("/api/ml/status"));
  } catch (e) {
    beriTahu(e.message, "gagal");
  }
}

document.getElementById("tombol-latih").addEventListener("click", async (e) => {
  const tombol = e.currentTarget;
  tombol.disabled = true;
  tombol.textContent = "Sedang melatih…";
  try {
    gambarStatus(await panggil("/api/ml/latih", { method: "POST" }));
    beriTahu("Model selesai dilatih ulang dengan data terbaru.");
  } catch (err) {
    beriTahu(err.message, "gagal");
  } finally {
    tombol.disabled = false;
    tombol.textContent = "Latih ulang model";
  }
});

muatStatus();
