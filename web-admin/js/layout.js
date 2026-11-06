// layout.js
// Dipasang di setiap halaman admin (kecuali login):
//   1. Kalau belum login -> lempar ke login.html
//   2. Cek token ke API (GET /api/auth/saya)
//   3. Isi menu samping, tandai halaman yang sedang dibuka
// Halaman memberi tahu dirinya lewat <body data-halaman="member">.

const MENU = [
  { kunci: "dashboard", label: "Dashboard", href: "index.html",
    ikon: '<path d="M3 13h8V3H3zM13 21h8V11h-8zM3 21h8v-6H3zM13 3v6h8V3z"/>' },
  { kunci: "member", label: "Member", href: "member.html",
    ikon: '<circle cx="9" cy="8" r="4"/><path d="M2 21c0-3.9 3.1-7 7-7s7 3.1 7 7M17 11a3 3 0 100-6M22 21c0-3-1.8-5.5-4.5-6.5"/>' },
  { kunci: "aktivitas", label: "Input Aktivitas", href: "aktivitas.html",
    ikon: '<path d="M12 5v14M5 12h14"/>' },
  { kunci: "follower", label: "Input Follower", href: "follower.html",
    ikon: '<path d="M3 3v18h18"/><path d="M7 15l4-4 3 3 5-6"/>' },
  { kunci: "pengaturan", label: "Pengaturan", href: "pengaturan.html",
    ikon: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 00.3 1.8l.1.1a2 2 0 11-2.8 2.8l-.1-.1a1.7 1.7 0 00-1.8-.3 1.7 1.7 0 00-1 1.5V21a2 2 0 11-4 0v-.1a1.7 1.7 0 00-1.1-1.5 1.7 1.7 0 00-1.8.3l-.1.1a2 2 0 11-2.8-2.8l.1-.1a1.7 1.7 0 00.3-1.8 1.7 1.7 0 00-1.5-1H3a2 2 0 110-4h.1a1.7 1.7 0 001.5-1.1 1.7 1.7 0 00-.3-1.8l-.1-.1a2 2 0 112.8-2.8l.1.1a1.7 1.7 0 001.8.3H9a1.7 1.7 0 001-1.5V3a2 2 0 114 0v.1a1.7 1.7 0 001 1.5 1.7 1.7 0 001.8-.3l.1-.1a2 2 0 112.8 2.8l-.1.1a1.7 1.7 0 00-.3 1.8V9a1.7 1.7 0 001.5 1H21a2 2 0 110 4h-.1a1.7 1.7 0 00-1.5 1z"/>' },
];

(async function siapkanLayout() {
  if (!ambilToken()) {
    location.href = "login.html";
    return;
  }

  const aktif = document.body.dataset.halaman;
  document.getElementById("sidebar").innerHTML = `
    <a href="index.html" class="logo-admin">
      <svg width="26" height="26" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 0C12.8 7 17 11.2 24 12C17 12.8 12.8 17 12 24C11.2 17 7 12.8 0 12C7 11.2 11.2 7 12 0Z" fill="currentColor"/></svg>
      <span>JKT48 Fan Board<small>Admin</small></span>
    </a>
    <nav class="menu-admin" aria-label="Menu admin">
      ${MENU.map((m) => m.segera
        ? `<span class="item-menu segera" aria-disabled="true">
             <svg viewBox="0 0 24 24" aria-hidden="true">${m.ikon}</svg>${m.label}<em>segera</em>
           </span>`
        : `<a href="${m.href}" class="item-menu${m.kunci === aktif ? " aktif" : ""}"${m.kunci === aktif ? ' aria-current="page"' : ""}>
             <svg viewBox="0 0 24 24" aria-hidden="true">${m.ikon}</svg>${m.label}
           </a>`).join("")}
    </nav>
    <div class="sidebar-bawah">
      <a href="../web-user/index.html" target="_blank" rel="noopener" class="item-menu">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14 3h7v7M10 14L21 3M21 14v7H3V3h7"/></svg>Lihat web user
      </a>
      <button type="button" class="item-menu tombol-keluar" id="tombol-keluar">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9"/></svg>Keluar
      </button>
    </div>`;

  document.getElementById("tombol-keluar").addEventListener("click", () => {
    hapusToken();
    location.href = "login.html?pesan=keluar";
  });

  // Pastikan token masih berlaku (kalau tidak, panggil() otomatis melempar ke login)
  try {
    const saya = await panggil("/api/auth/saya");
    const sapa = document.getElementById("sapaan");
    if (sapa) sapa.textContent = `Halo, ${saya.username}`;
  } catch (e) {
    if (e.status === 0) beriTahu(e.message, "gagal");
  }
})();
