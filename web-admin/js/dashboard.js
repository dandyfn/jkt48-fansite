// dashboard.js
// Ringkasan untuk admin: jumlah member, akun yang follower-nya perlu diupdate,
// Top 5 minggu ini, dan poin yang terakhir tercatat.

const LABEL_JENIS = {
  lagu_baru: "Lagu baru", center: "Center", show: "Show", film: "Film", iklan: "Iklan",
  kapten_baru: "Kapten baru", kapten_aktif: "Kapten aktif", ssk: "SSK", follower: "Follower",
};

async function muatDashboard() {
  const [grup, akun, lb, aktivitas] = await Promise.all([
    panggil("/api/grup").catch(() => null),
    panggil("/api/sosmed/akun").catch(() => []),
    panggil("/api/leaderboard?periode=minggu").catch(() => null),
    panggil("/api/aktivitas?batas=10").catch(() => []),
  ]);

  // Kotak ringkasan
  const perluUpdate = akun.filter((a) => a.perlu_update).length;
  const s = grup ? grup.statistik : {};
  const kotak = [
    [s.member_aktif, "Member aktif", "member.html"],
    [s.member_trainee, "Trainee", "member.html"],
    [s.member_eks, "Member eks", "member.html"],
    [perluUpdate, "Akun follower perlu diupdate", null, perluUpdate > 0],
  ];
  document.getElementById("ringkasan").innerHTML = kotak.map(([n, label, href, waspada]) => {
    const isi = `<span class="angka">${angka(n)}</span><span class="label">${label}</span>`;
    const kelas = `kotak-ringkas${waspada ? " waspada" : ""}`;
    return href ? `<a href="${href}" class="${kelas}">${isi}</a>` : `<div class="${kelas}">${isi}</div>`;
  }).join("");
  document.getElementById("info-follower").textContent =
    `${akun.length} akun sosmed terdaftar, ${perluUpdate} belum diupdate lebih dari 7 hari.`;

  // Top 5
  const top = document.getElementById("top5");
  if (lb && lb.data.some((d) => d.skor > 0)) {
    document.getElementById("periode-top").textContent =
      `${tanggal(lb.mulai, { day: "numeric", month: "short" })} – ${tanggal(lb.selesai)}`;
    top.innerHTML = lb.data.slice(0, 5).map((d) => `
      <li>
        <span class="no-top">${d.peringkat}</span>
        <span class="nama-top">${esc(d.nama_panggilan)}${d.kapten ? ' <span class="chip chip-emas">Kapten</span>' : ""}</span>
        <span class="skor-top">${angka(d.skor)}</span>
      </li>`).join("");
  } else {
    top.innerHTML = `<li class="redup">Belum ada poin minggu ini.</li>`;
  }

  // Aktivitas terbaru
  const tbody = document.getElementById("aktivitas-terbaru");
  tbody.innerHTML = aktivitas.length
    ? aktivitas.map((a) => `
        <tr>
          <td>${tanggal(a.tanggal)}</td>
          <td><strong>${esc(a.nama_panggilan)}</strong></td>
          <td><span class="chip">${esc(LABEL_JENIS[a.jenis_kode] || a.jenis_kode)}</span></td>
          <td>${esc(a.keterangan || "")}</td>
          <td class="kanan"><strong>+${angka(a.poin)}</strong></td>
        </tr>`).join("")
    : `<tr><td colspan="5" class="redup">Belum ada poin yang tercatat.</td></tr>`;
}

muatDashboard();
