// detail.js
// Halaman detail satu member. Id member diambil dari alamat, contoh: detail.html?id=5
//
// Data yang dipanggil dari API (semua sekaligus, supaya cepat):
//   GET /api/members/{id}                 -> identitas
//   GET /api/members/{id}/statistik       -> total show, lagu, center, projek luar
//   GET /api/leaderboard                  -> peringkat, skor, rincian, streak minggu ini
//   GET /api/aktivitas?member_id=...      -> catatan poin minggu ini (untuk keterangan)
//   GET /api/leaderboard/riwayat/{id}     -> grafik skor
//   GET /api/sosmed/ratecard/{id}         -> rate card
//   GET /api/lencana?member_id=...        -> lencana kapten, dll
//   GET /api/projek?member_id=...         -> projek terbaru

const LABEL_POIN = {
  lagu_baru: "Lagu/projek baru",
  center: "Posisi center",
  show: "Show",
  film: "Projek luar: film",
  iklan: "Projek luar: iklan",
  kapten_baru: "Diangkat jadi kapten",
  kapten_aktif: "Kapten aktif",
  ssk: "Hasil SSK",
  follower: "Pertumbuhan follower",
};

const LABEL_KATEGORI = {
  single: ["Single", "team-love"],
  lagu: ["Lagu", "team-love"],
  projek_grup: ["Projek grup", "team-dream"],
  film: ["Film", "status-aktif"],
  iklan: ["Iklan", "team-passion"],
};

const LABEL_PLATFORM = { instagram: "Instagram", tiktok: "TikTok", x: "X", youtube: "YouTube" };

const IKON_MAHKOTA =
  `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" aria-hidden="true"><path d="M3 18h18l-2-11-5 5-2-7-2 7-5-5z"/></svg>`;
const IKON_BINTANG =
  `<svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 0C12.8 7 17 11.2 24 12C17 12.8 12.8 17 12 24C11.2 17 7 12.8 0 12C7 11.2 11.2 7 12 0Z" fill="currentColor"/></svg>`;

// 847629 -> "847,6 rb", 1250000 -> "1,3 jt"
function ringkas(n) {
  if (n === null || n === undefined) return "–";
  return Number(n).toLocaleString("id-ID", { notation: "compact", maximumFractionDigits: 1 });
}

// Ambil data, tapi kalau gagal kembalikan nilai cadangan (supaya satu bagian
// yang error tidak membuat seluruh halaman gagal)
async function ambilAman(path, cadangan) {
  try {
    return await ambil(path);
  } catch (e) {
    console.warn("Gagal memuat", path, e);
    return cadangan;
  }
}

async function muatDetail() {
  const id = Number(new URLSearchParams(location.search).get("id"));
  if (!id) return tampilkanTidakAda();

  let member;
  try {
    member = await ambil(`/api/members/${id}`);
  } catch (e) {
    return tampilkanTidakAda();
  }
  document.title = `${member.nama_panggilan} · JKT48 Fan Board`;

  const lb = await ambilAman("/api/leaderboard?periode=minggu", null);
  const minggu = lb ? `&dari=${lb.mulai}&sampai=${lb.selesai}` : "";

  // Panggil sisanya bersamaan
  const [statistik, aktivitas, riwayat, ratecard, lencana, projek] = await Promise.all([
    ambilAman(`/api/members/${id}/statistik`, null),
    ambilAman(`/api/aktivitas?member_id=${id}${minggu}`, []),
    ambilAman(`/api/leaderboard/riwayat/${id}?batas=8`, []),
    ambilAman(`/api/sosmed/ratecard/${id}`, []),
    ambilAman(`/api/lencana?member_id=${id}`, []),
    ambilAman(`/api/projek?member_id=${id}&batas=6`, []),
  ]);
  const baris = lb ? lb.data.find((d) => d.member_id === id) : null;

  isiHero(member, baris, statistik, lencana);
  isiRincianPoin(baris, aktivitas, lb);
  isiRatecard(ratecard);
  isiGrafik(riwayat, baris, lb);
  isiProjek(projek);
}

// ----------------------------------------------------------------------
function isiHero(m, baris, statistik, lencana) {
  document.getElementById("detail-foto").innerHTML = htmlFoto(m, m.id);
  document.getElementById("detail-nama").textContent = m.nama_panggilan;
  document.getElementById("detail-nama-lengkap").textContent =
    m.nama_lengkap + (m.stage_name && m.stage_name !== m.nama_panggilan ? ` · Stage name: ${m.stage_name}` : "");

  // Sorotan: peringkat & streak
  const sorotan = [];
  if (baris) {
    sorotan.push(`<span class="chip chip-gelap">${IKON_MAHKOTA.replace('width="22" height="22"', 'width="16" height="16"')} Peringkat ${baris.peringkat} minggu ini</span>`);
    if (baris.streak_minggu > 0) {
      sorotan.push(`<span class="chip team-love">${IKON_STREAK} Streak ${baris.streak_minggu} minggu di Top 5</span>`);
    }
  } else {
    sorotan.push(`<span class="chip status-${esc(m.status)}">Tidak ikut leaderboard (${esc(m.status)})</span>`);
  }
  document.getElementById("detail-sorotan").innerHTML = sorotan.join("");

  const chip = [`<span class="chip">Generasi ${esc(m.generasi)}</span>`,
                `<span class="chip ${kelasTeam(m.team)}">${esc(labelTeam(m.team))}</span>`];
  if (m.lama_di_jkt48) chip.push(`<span class="chip">Di JKT48 ${esc(m.lama_di_jkt48)}</span>`);
  if (m.umur !== null) chip.push(`<span class="chip">${m.umur} tahun · ${esc(m.zodiak || "")}</span>`);
  document.getElementById("detail-chip").innerHTML = chip.join("");

  // Lencana
  const elLencana = document.getElementById("detail-lencana");
  elLencana.innerHTML = lencana.map((l) => {
    const kapten = l.jenis === "kapten";
    const nama = { kapten: "Kapten", wakil_kapten: "Wakil Kapten", lainnya: "Lencana" }[l.jenis] || l.jenis;
    const periode = l.masih_menjabat
      ? `sejak ${tanggal(l.tanggal_mulai)}`
      : `${tanggal(l.tanggal_mulai, { year: "numeric" })}–${tanggal(l.tanggal_selesai, { year: "numeric" })}`;
    return `
      <div class="lencana${l.masih_menjabat ? "" : " lencana-lama"}">
        <span class="ikon-lencana ${kapten ? "ikon-emas" : "ikon-ungu"}">${kapten ? IKON_MAHKOTA : IKON_BINTANG}</span>
        <span><strong>${esc(nama)} ${esc(l.keterangan || "")}</strong><br><small>${periode}</small></span>
      </div>`;
  }).join("");
  elLencana.hidden = lencana.length === 0;

  // Ubin statistik
  const s = statistik || {};
  const ubin = [
    [baris ? angka(baris.skor) : "–", "Poin minggu ini", true],
    [angka(s.total_lagu), "Lagu / projek", false],
    [angka(s.total_show), "Total show", false],
    [s.total_center !== undefined ? angka(s.total_center) + "×" : "–", "Posisi center", false],
    [angka(s.projek_luar), "Projek luar", false],
  ];
  document.getElementById("detail-statistik").innerHTML = ubin.map(([nilai, label, merah]) => `
    <div class="ubin-detail">
      <div class="angka${merah ? " merah" : ""}">${nilai}</div>
      <div class="label">${label}</div>
    </div>`).join("");
}

// ----------------------------------------------------------------------
function isiRincianPoin(baris, aktivitas, lb) {
  if (lb) {
    document.getElementById("periode-poin").textContent =
      `${tanggal(lb.mulai, { day: "numeric", month: "short" })} – ${tanggal(lb.selesai)}`;
  }
  const daftar = document.getElementById("daftar-poin");
  if (!baris || Object.keys(baris.rincian).length === 0) {
    daftar.innerHTML = `<li class="memuat">Belum ada poin minggu ini.</li>`;
    document.getElementById("total-poin").textContent = baris ? "0" : "–";
    return;
  }

  // Kelompokkan catatan aktivitas per jenis, untuk keterangan di bawah label
  const perJenis = {};
  aktivitas.forEach((a) => (perJenis[a.jenis_kode] = perJenis[a.jenis_kode] || []).push(a));

  const urut = Object.entries(baris.rincian).sort((a, b) => b[1] - a[1]);
  daftar.innerHTML = urut.map(([kode, poin]) => {
    const catatan = perJenis[kode] || [];
    let ket = "";
    if (kode === "show") ket = `${catatan.length} show`;
    else if (kode === "follower") ket = `Naik ${angka(baris.pertumbuhan_follower_persen)}%, dibanding pertumbuhan tertinggi minggu ini`;
    else if (kode === "kapten_aktif") ket = "Masih menjabat kapten";
    else ket = catatan.map((c) => c.keterangan).filter(Boolean).join(", ");
    return `
      <li>
        <span><strong>${esc(LABEL_POIN[kode] || kode)}</strong><br><small>${esc(ket)}</small></span>
        <span class="poin-plus">+${angka(poin)}</span>
      </li>`;
  }).join("");
  document.getElementById("total-poin").textContent = angka(baris.skor);
}

// ----------------------------------------------------------------------
function isiRatecard(ratecard) {
  const el = document.getElementById("ratecard");
  if (ratecard.length === 0) {
    el.innerHTML = `<p style="color:#E2D1E7;margin:0">Akun media sosial belum didaftarkan.</p>`;
    return;
  }
  el.innerHTML = ratecard.map((r) => {
    const tumbuh = r.pertumbuhan_persen;
    const chipTumbuh = tumbuh === null ? "" :
      `<span class="chip-tumbuh ${tumbuh < 0 ? "minus" : ""}">${tumbuh >= 0 ? "▲" : "▼"} ${angka(Math.abs(tumbuh))}%</span>`;
    return `
      <div class="item-ratecard">
        <div class="baris-antara">
          <a href="${esc(r.link_profil)}" target="_blank" rel="noopener" class="nama-platform">${esc(LABEL_PLATFORM[r.platform] || r.platform)} ↗</a>
          <span class="chip-sumber">${r.sumber === "api" ? "Otomatis · API" : "Manual"}${r.tanggal ? " · " + tanggal(r.tanggal, { day: "numeric", month: "short" }) : ""}</span>
        </div>
        <div class="baris-antara" style="align-items:flex-end">
          <div>
            <div class="angka-follower">${ringkas(r.followers)}</div>
            <div class="sub-follower">follower · @${esc(r.username)}</div>
          </div>
          ${chipTumbuh}
        </div>
      </div>`;
  }).join("");
}

// ----------------------------------------------------------------------
function isiGrafik(riwayat, baris, lb) {
  const data = riwayat.map((r) => ({ skor: r.skor, label: tanggal(r.periode_mulai, { day: "numeric", month: "short" }), ini: false }));
  // Tambahkan minggu berjalan kalau belum tersimpan di riwayat
  if (baris && lb && !riwayat.some((r) => r.periode_mulai === lb.mulai)) {
    data.push({ skor: baris.skor, label: "Minggu ini", ini: true });
  }
  const tampil = data.slice(-8);
  const el = document.getElementById("grafik");
  if (tampil.length === 0) {
    el.innerHTML = `<p class="memuat">Riwayat skor belum tersedia.</p>`;
    el.setAttribute("aria-label", "Riwayat skor belum tersedia");
    return;
  }
  const maks = Math.max(...tampil.map((d) => d.skor), 1);
  el.innerHTML = tampil.map((d) => `
    <div class="batang-wadah">
      <span class="batang-nilai">${angka(d.skor)}</span>
      <div class="batang${d.ini ? " ini" : ""}" style="height:${Math.max((d.skor / maks) * 150, 4)}px"></div>
      <span class="batang-label">${esc(d.label)}</span>
    </div>`).join("");
  el.setAttribute("aria-label",
    "Grafik skor mingguan: " + tampil.map((d) => `${d.label} ${angka(d.skor)}`).join(", "));
}

// ----------------------------------------------------------------------
function isiProjek(projek) {
  const el = document.getElementById("daftar-projek");
  if (projek.length === 0) {
    el.innerHTML = `<li class="memuat">Belum ada projek yang tercatat.</li>`;
    return;
  }
  const id = Number(new URLSearchParams(location.search).get("id"));
  el.innerHTML = projek.map((p) => {
    const [label, kelas] = LABEL_KATEGORI[p.kategori] || [p.kategori, ""];
    const saya = p.peserta.find((x) => x.member_id === id);
    const peran = saya && saya.is_center ? "Posisi center · " : "";
    return `
      <li>
        <span class="chip ${kelas} chip-kategori">${esc(label)}</span>
        <span><strong>${esc(p.judul)}</strong><br><small>${peran}${tanggal(p.tanggal_rilis)}</small></span>
      </li>`;
  }).join("");
}

// ----------------------------------------------------------------------
function tampilkanTidakAda() {
  document.getElementById("isi-detail").innerHTML = `
    <div class="kotak" style="margin:64px 0;text-align:center;align-items:center">
      <h1 class="judul-section" style="margin:0">Member tidak ditemukan</h1>
      <p class="teks-redup">Mungkin alamatnya salah atau member sudah dihapus.</p>
      <a href="index.html" class="tombol-utama" style="text-decoration:none">Kembali ke halaman utama</a>
    </div>`;
}

muatDetail();
