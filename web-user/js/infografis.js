// infografis.js
// Mengisi halaman infografis dari satu alamat API:
//   GET /api/infografis -> satu baris per member aktif & trainee
//
// Semua perhitungan (peringkat, peringkat lengkap, diagram lingkaran)
// dilakukan di sini. Jadi saat tombol "Per generasi" / "Tertua" diklik,
// halaman cukup digambar ulang tanpa meminta data lagi ke API.

// ----------------------------------------------------------------------
// Keadaan halaman (berubah saat tombol diklik)
// ----------------------------------------------------------------------
const keadaan = {
  cakupan: "semua",  // "semua" atau "gen"
  gen: null,         // generasi yang dipilih (angka)
  urutUmur: "tua",   // "tua" atau "muda"
  allTime: false,    // true = ikut sertakan member eks (centang "Member all time")
};

let MEMBER_AKTIF = []; // aktif & trainee (dari /api/infografis)

let MEMBER = [];     // data dari API
let DAFTAR_GEN = []; // [3, 6, 7, ...]
let JUMLAH_PER_GEN = {};

// 14 warna untuk diagram lingkaran (generasi dengan member terbanyak = 14 orang). Terang-gelapnya juga dibedakan,
// supaya tetap bisa dibedakan oleh orang yang sulit membedakan warna.
const WARNA = ["#8E0C22", "#E8879F", "#4E2A8E", "#B9A3E6", "#B4561C",
               "#F4B98A", "#1E6B55", "#8FD0BC", "#1F4E66", "#9CC3D9",
               "#6B5A00", "#E3CB6B", "#5A3D52", "#C9A9BF"];

const IKON = {
  show: "M4 20h16M6 20V9l6-5 6 5v11M10 20v-5h4v5",
  senbatsu: "M12 3l2.6 5.3 5.9.9-4.3 4.1 1 5.8L12 16.4 6.8 19.1l1-5.8L3.5 9.2l5.9-.9z",
  lagu: "M9 18V5l11-2v13M9 18a3 3 0 1 1-6 0 3 3 0 0 1 6 0zM20 16a3 3 0 1 1-6 0 3 3 0 0 1 6 0z",
  tinggi: "M12 3v18M8 7l4-4 4 4M8 17l4 4 4-4",
  umur: "M12 7v5l3 2M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z",
  projek: "M4 7h16v12H4zM8 7V5h8v2M4 12h16",
};

// Enam kartu juara. "kolom" = nama field dari API.
const KATEGORI = [
  { kolom: "total_show", judul: "Paling banyak show", sub: "jumlah tampil di teater", satuan: "show",
    ikon: "show", warnaIkon: ["#FCE4EE", "#A3245A"],
    catatan: "Dari sheet show + saldo awal total show." },
  { kolom: "total_senbatsu", judul: "Paling banyak senbatsu", sub: "masuk lineup single utama", satuan: "kali",
    ikon: "senbatsu", warnaIkon: ["#F6E7B8", "#5C4300"],
    catatan: "Dari lineup lagu utama (A-side) setiap single." },
  { kolom: "total_lagu", judul: "Paling banyak bawa lagu", sub: "lagu yang pernah dibawakan", satuan: "lagu",
    ikon: "lagu", warnaIkon: ["#ECE6FA", "#5B3FA8"],
    catatan: "Dari total lagu awal + lagu baru yang tercatat di web." },
  { kolom: "tinggi_cm", judul: "Paling tinggi", sub: "tinggi badan", satuan: "cm",
    ikon: "tinggi", warnaIkon: ["#E3F4EA", "#1F6B43"],
    catatan: "Member yang tinggi badannya belum diisi tidak ikut dibandingkan." },
  { kolom: "umur", judul: "Urutan umur", sub: "dari tanggal lahir, per hari ini", satuan: "tahun",
    ikon: "umur", warnaIkon: ["#E6F1F6", "#1F4E66"], umur: true,
    catatan: "Kalau umurnya sama, yang lahir lebih dulu dianggap lebih tua." },
  { kolom: "total_projek", judul: "Paling banyak projek", sub: "film, iklan, dan projek luar", satuan: "projek",
    ikon: "projek", warnaIkon: ["#FFE7D6", "#A4461A"],
    catatan: "Dari projek kategori film, iklan, dan lainnya." },
];

// ----------------------------------------------------------------------
// Fungsi bantu
// ----------------------------------------------------------------------
const jumlah = (angka) => angka.reduce((a, b) => a + b, 0);
const memberGen = (g) => MEMBER.filter((m) => m.generasi === g);
const labelTeamPendek = (m) => (m.team ? `Team ${m.team}` : m.status === "eks" ? "Eks" : "Trainee");

// Member yang sedang dibandingkan (semua, atau satu generasi)
function kolam() {
  return keadaan.cakupan === "gen" ? memberGen(keadaan.gen) : MEMBER;
}

// Satu kategori dianggap "belum ada datanya" kalau semua nilainya kosong atau 0
function belumAdaData(kolom) {
  return MEMBER.every((m) => !m[kolom]);
}

// Urutkan lalu beri peringkat. Nilai sama = peringkat sama (1, 2, 2, 4, ...)
function beriPeringkat(daftar, ambilKunci) {
  let peringkat = 0, sebelum = null;
  return daftar.map((m, i) => {
    const kunci = ambilKunci(m);
    if (kunci !== sebelum) { peringkat = i + 1; sebelum = kunci; }
    return { ...m, peringkat };
  });
}

// ----------------------------------------------------------------------
// 1) Pilihan cakupan
// ----------------------------------------------------------------------
function gambarPilihanGen() {
  const wadah = document.getElementById("pilih-gen");
  wadah.hidden = keadaan.cakupan !== "gen";
  wadah.innerHTML = DAFTAR_GEN.map((g) => `
    <button type="button" class="tombol-gen${g === keadaan.gen ? " aktif" : ""}" data-gen="${g}"
            aria-pressed="${g === keadaan.gen}">
      <span>Gen ${g}</span><small>${JUMLAH_PER_GEN[g]} member</small>
    </button>`).join("");

  const jenis = keadaan.allTime ? "member all time (aktif, trainee, eks)" : "member aktif & trainee";
  document.getElementById("keterangan-cakupan").textContent = keadaan.cakupan === "gen"
    ? `Generasi ${keadaan.gen} · ${JUMLAH_PER_GEN[keadaan.gen]} ${keadaan.allTime ? "member all time" : "member"}`
    : `${MEMBER.length} ${jenis}`;
  document.getElementById("judul-cakupan").textContent =
    (keadaan.cakupan === "gen" ? `Gen ${keadaan.gen}` : "semua member") + (keadaan.allTime ? " · all time" : "");
  document.getElementById("kaki-cakupan").textContent = keadaan.allTime
    ? "Data dari semua member sepanjang masa (aktif, trainee, eks). Total lagu & center member eks hanya dari lagu yang tercatat."
    : 'Data dari member aktif & trainee. Centang "Member all time" untuk ikut menghitung member eks.';
  document.getElementById("petunjuk-gen").textContent = keadaan.cakupan === "gen"
    ? `Bagian setiap member Gen ${keadaan.gen}: sudah berapa kali ikut lagu, jadi center, dan masuk senbatsu.`
    : 'Pembagian per generasi. Pilih "Per generasi" di atas untuk melihat bagian setiap member.';
}

// ----------------------------------------------------------------------
// 2) Kartu juara kategori
// ----------------------------------------------------------------------
// Urutan lengkap satu kategori (semua member di cakupan)
function urutkan(kat) {
  const daftar = kolam();
  if (kat.umur) {
    // Urut dari tanggal lahir: tertua = lahir paling awal
    const tua = keadaan.urutUmur === "tua";
    const urut = daftar.filter((m) => m.tanggal_lahir)
      .sort((a, b) => (tua ? 1 : -1) * a.tanggal_lahir.localeCompare(b.tanggal_lahir));
    return beriPeringkat(urut, (m) => m.tanggal_lahir);
  }
  const urut = daftar.filter((m) => m[kat.kolom] > 0).sort((a, b) => b[kat.kolom] - a[kat.kolom]);
  return beriPeringkat(urut, (m) => m[kat.kolom]);
}
const top5 = (kat) => urutkan(kat).slice(0, 5);

// Lebar batang di daftar Top 5 (dalam %)
function lebarBatang(kat, nilai, daftar) {
  const nilaiSemua = daftar.map((m) => m[kat.kolom]);
  const maks = Math.max(...nilaiSemua), min = Math.min(...nilaiSemua);
  if (kat.kolom === "tinggi_cm") return 40 + ((nilai - min) / ((maks - min) || 1)) * 60;
  if (kat.umur) {
    const persen = (nilai - min) / ((maks - min) || 1) * 60;
    return keadaan.urutUmur === "tua" ? 40 + persen : 100 - persen;
  }
  return Math.max(6, (nilai / maks) * 100);
}

function kartuJuara(kat, indeks) {
  const menunggu = belumAdaData(kat.kolom);
  const mahkota = (keadaan.cakupan === "gen" ? `JUARA GEN ${keadaan.gen}` : "JUARA SEMUA MEMBER")
    + (keadaan.allTime ? " · ALL TIME" : "");
  const [bgIkon, fgIkon] = kat.warnaIkon;

  const tombolUmur = kat.umur ? `
    <div class="pil-grup pil-kecil" role="group" aria-label="Urutkan umur">
      <button type="button" class="pil${keadaan.urutUmur === "tua" ? " aktif" : ""}" data-umur="tua"
              aria-pressed="${keadaan.urutUmur === "tua"}">Tertua</button>
      <button type="button" class="pil${keadaan.urutUmur === "muda" ? " aktif" : ""}" data-umur="muda"
              aria-pressed="${keadaan.urutUmur === "muda"}">Termuda</button>
    </div>` : "";

  let juara, baris;
  if (menunggu) {
    // Belum ada data: tampilkan kerangka abu-abu, supaya kotaknya tetap ada
    juara = `
      <div class="juara-utama kosong">
        <div class="juara-foto"><div class="foto tint-0"><span class="inisial">?</span></div></div>
        <div class="juara-teks">
          <span class="juara-mahkota">${mahkota}</span>
          <span class="juara-nama">Belum ada data</span>
          <span class="juara-meta">Tampil otomatis setelah datanya diinput</span>
        </div>
      </div>`;
    baris = ["100%", "82%", "70%", "58%", "44%"].map((w, i) => `
      <li class="kosong"><span class="nomor">${i + 1}</span><span class="nama">—</span>
        <span class="trek"><span class="isi" style="width:${w}"></span></span><span class="nilai">–</span></li>`).join("");
  } else {
    const daftar = top5(kat);
    const satu = daftar.filter((m) => m.peringkat === 1);
    const m = daftar[0];
    let meta = `Gen ${m.generasi} · ${labelTeamPendek(m)}${m.status === "eks" ? " · Eks" : ""}`;
    if (kat.umur) meta = `Lahir ${tanggal(m.tanggal_lahir)} · Gen ${m.generasi}`;
    if (satu.length > 1) meta = `Seri dengan ${satu.slice(1).map((s) => s.nama_panggilan).join(", ")}`;
    juara = `
      <a class="juara-utama" href="detail.html?id=${m.id}">
        <div class="juara-foto">${htmlFoto(m, indeks)}<span class="medali-kecil">1</span></div>
        <div class="juara-teks">
          <span class="juara-mahkota">${mahkota}</span>
          <span class="juara-nama">${esc(m.nama_panggilan)}${satu.length > 1 ? ` +${satu.length - 1}` : ""}</span>
          <span class="juara-meta">${esc(meta)}</span>
        </div>
        <div class="juara-angka"><strong>${angka(m[kat.kolom])}</strong><span>${kat.satuan}</span></div>
      </a>`;
    baris = daftar.map((d) => `
      <li><span class="nomor">${d.peringkat}</span>
        <a class="nama" href="detail.html?id=${d.id}">${esc(d.nama_panggilan)}</a>
        <span class="trek"><span class="isi${d.peringkat === 1 ? " utama" : ""}" style="width:${lebarBatang(kat, d[kat.kolom], daftar)}%"></span></span>
        <span class="nilai">${angka(d[kat.kolom])}</span></li>`).join("");
  }

  return `
    <article class="kartu-juara">
      <div class="juara-kepala">
        <span class="juara-ikon" style="background:${bgIkon}" aria-hidden="true">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="${fgIkon}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="${IKON[kat.ikon]}"/></svg>
        </span>
        <div class="juara-judul"><h3>${kat.judul}</h3><p>${kat.sub}</p></div>
        ${menunggu ? `<span class="label-menunggu">Menunggu data</span>` : ""}
        ${tombolUmur}
      </div>
      ${juara}
      <ol class="daftar-top">${baris}</ol>
      <p class="kartu-catatan">${kat.catatan}</p>
      <button type="button" class="tombol-lengkap" data-lengkap="${indeks}" ${menunggu ? "disabled" : ""}>
        ${menunggu ? "Lihat semua (belum ada data)" : `Lihat semua (${urutkan(kat).length} member)`}
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 6l6 6-6 6"/></svg>
      </button>
    </article>`;
}

function gambarJuara() {
  document.getElementById("grid-juara").innerHTML = KATEGORI.map(kartuJuara).join("");
}

// ----------------------------------------------------------------------
// 3) Diagram lingkaran: lagu, center, senbatsu
// ----------------------------------------------------------------------
function grafikLingkaran({ judul, kolom, catatan }) {
  const menunggu = belumAdaData(kolom);
  const perMember = keadaan.cakupan === "gen";

  // Potongan lingkaran: per generasi (Semua member) atau per member (satu generasi)
  const potong = perMember
    ? memberGen(keadaan.gen).map((m) => ({ label: m.nama_panggilan, nilai: m[kolom] || 0 }))
        .sort((a, b) => b.nilai - a.nilai || a.label.localeCompare(b.label))
    : DAFTAR_GEN.map((g) => ({ label: `Gen ${g}`, nilai: jumlah(memberGen(g).map((m) => m[kolom] || 0)) }));
  if (menunggu) potong.forEach((p) => (p.nilai = 1));     // kerangka abu-abu sama besar

  const total = jumlah(potong.map((p) => p.nilai));
  const persen = (v) => `${Math.round((v / (total || 1)) * 100)}%`;
  // Lebih dari 14 potongan (mis. Gen 3 all time = 31 member): 13 terbesar berwarna, sisanya abu-abu
  const banyak = potong.length > WARNA.length;
  const warna = (i) => (menunggu ? (i % 2 ? "#EFE7EB" : "#E2D6DC")
    : banyak && i >= WARNA.length - 1 ? "#CFC3C9" : WARNA[i % WARNA.length]);

  // conic-gradient: setiap potongan mulai dari jam 12, searah jarum jam
  let sudut = 0;
  const bagian = [];
  potong.forEach((p, i) => {
    if (p.nilai <= 0) return;
    const akhir = sudut + (p.nilai / total) * 360;
    bagian.push(`${warna(i)} ${sudut.toFixed(2)}deg ${akhir.toFixed(2)}deg`);
    sudut = akhir;
  });
  const kosong = !menunggu && total === 0;                // misal: Gen 6 belum pernah center
  const latar = kosong || bagian.length === 0 ? "#F3E9EE" : `conic-gradient(${bagian.join(", ")})`;

  const tengahAngka = menunggu ? "–" : total;
  const tengahLabel = menunggu ? "menunggu data" : perMember ? `total Gen ${keadaan.gen}` : "total semua gen";

  const legenda = potong.map((p, i) => `
    <li>
      <span class="warna" style="background:${warna(i)}" aria-hidden="true"></span>
      <span class="gen">${esc(p.label)}</span>
      <span class="nilai">${menunggu ? "–" : p.nilai}</span>
      <span class="persen">${menunggu || kosong ? "" : persen(p.nilai)}</span>
    </li>`).join("");
  const ringkasan = menunggu ? `${judul}: data belum tersedia`
    : `${judul} ${perMember ? `per member Gen ${keadaan.gen}` : "per generasi"}: `
      + potong.map((p) => `${p.label} ${p.nilai} (${persen(p.nilai)})`).join(", ");

  return `
    <article class="kartu-grafik">
      <div class="grafik-kepala">
        <div><h3>${judul}</h3><p>${perMember ? `per member Gen ${keadaan.gen}` : "per generasi"}</p></div>
        ${menunggu ? `<span class="label-menunggu">Menunggu data</span>` : ""}
      </div>
      <div class="donat" role="img" aria-label="${esc(ringkasan)}" style="background: ${latar}">
        <div class="donat-tengah${perMember && !menunggu ? " sorot" : ""}"><strong>${tengahAngka}</strong><span>${tengahLabel}</span></div>
      </div>
      ${kosong ? `<p class="info-keterangan" style="text-align:center">Belum ada di generasi ini.</p>` : ""}
      ${banyak && !menunggu ? `<p class="info-keterangan" style="text-align:center">13 terbesar berwarna, ${potong.length - 13} lainnya abu-abu.</p>` : ""}
      <ul class="legenda${perMember ? " legenda-member" : ""}">${legenda}</ul>
      <p class="kartu-catatan">${perMember ? catatan.member : catatan.gen}</p>
    </article>`;
}

function gambarLingkaran() {
  document.getElementById("grafik-lingkaran").innerHTML = [
    grafikLingkaran({ judul: "Jumlah lagu", kolom: "total_lagu", catatan: {
      gen: "Satu lagu yang dibawakan 5 member dihitung 5 (jumlah keikutsertaan, bukan judul lagu).",
      member: "Persentase = lagu member itu dibagi total keikutsertaan lagu satu generasi." } }),
    grafikLingkaran({ judul: "Jumlah center", kolom: "total_center", catatan: {
      gen: "Generasi yang belum pernah dapat posisi center tidak muncul di lingkaran, hanya di legenda.",
      member: "Member yang belum pernah jadi center tidak muncul di lingkaran, hanya di legenda." } }),
    grafikLingkaran({ judul: "Jumlah senbatsu", kolom: "total_senbatsu", catatan: {
      gen: "Senbatsu = ikut lineup lagu utama single.",
      member: "Persentase = senbatsu member itu dibagi total senbatsu satu generasi." } }),
  ].join("");
}

// ----------------------------------------------------------------------
// 4) Jendela "Lihat semua": peringkat lengkap satu kategori
// ----------------------------------------------------------------------
const dialog = document.getElementById("dialog-peringkat");

function bukaPeringkatLengkap(kat) {
  const daftar = urutkan(kat);
  const nilaiSemua = daftar.map((m) => m[kat.kolom]);
  document.getElementById("dialog-cakupan").textContent =
    (keadaan.cakupan === "gen" ? `GEN ${keadaan.gen}` : "SEMUA MEMBER") + (keadaan.allTime ? " · ALL TIME" : "");
  document.getElementById("dialog-judul").textContent =
    kat.umur ? `Urutan umur (${keadaan.urutUmur === "tua" ? "tertua" : "termuda"} dulu)` : kat.judul;
  document.getElementById("dialog-sub").textContent =
    `${daftar.length} member · ${kat.catatan}`;
  document.getElementById("dialog-daftar").innerHTML = daftar.map((d) => `
    <li><span class="nomor">${d.peringkat}</span>
      <a class="nama" href="detail.html?id=${d.id}">${esc(d.nama_panggilan)}
        <small>Gen ${d.generasi} · ${esc(labelTeamPendek(d))}</small></a>
      <span class="trek"><span class="isi${d.peringkat === 1 ? " utama" : ""}" style="width:${lebarBatang(kat, d[kat.kolom], daftar)}%"></span></span>
      <span class="nilai">${angka(d[kat.kolom])} <small>${kat.satuan}</small></span></li>`).join("");
  dialog.showModal();
}

document.getElementById("dialog-tutup").addEventListener("click", () => dialog.close());
// Klik di luar kotak (di latar gelap) juga menutup jendela
dialog.addEventListener("click", (e) => { if (e.target === dialog) dialog.close(); });

// ----------------------------------------------------------------------
// Gambar semua + pasang tombol
// ----------------------------------------------------------------------
function gambarSemua() {
  gambarPilihanGen();
  gambarJuara();
  gambarLingkaran();
}

// Tombol "Semua member" / "Per generasi"
document.querySelectorAll("[data-cakupan]").forEach((tombol) => {
  tombol.addEventListener("click", () => {
    keadaan.cakupan = tombol.dataset.cakupan;
    document.querySelectorAll("[data-cakupan]").forEach((t) => {
      const aktif = t === tombol;
      t.classList.toggle("aktif", aktif);
      t.setAttribute("aria-pressed", String(aktif));
    });
    gambarSemua();
  });
});

// Tombol Gen & Tertua/Termuda dibuat ulang setiap kali digambar,
// jadi klik-nya ditangkap di wadah (event delegation)
document.getElementById("pilih-gen").addEventListener("click", (e) => {
  const tombol = e.target.closest("[data-gen]");
  if (!tombol) return;
  keadaan.gen = Number(tombol.dataset.gen);
  gambarSemua();
  document.querySelector(`[data-gen="${keadaan.gen}"]`).focus();
});
document.getElementById("grid-juara").addEventListener("click", (e) => {
  const lengkap = e.target.closest("[data-lengkap]");
  if (lengkap) { bukaPeringkatLengkap(KATEGORI[Number(lengkap.dataset.lengkap)]); return; }
  const tombol = e.target.closest("[data-umur]");
  if (!tombol) return;
  keadaan.urutUmur = tombol.dataset.umur;
  gambarJuara();
  document.querySelector(`[data-umur="${keadaan.urutUmur}"]`).focus();
});

// ----------------------------------------------------------------------
// 5) Cari member: semua member (aktif, trainee, eks)
//    Data: GET /api/infografis?termasuk_eks=true
//    Peringkat dihitung dibanding SEMUA member sepanjang sejarah.
// ----------------------------------------------------------------------
let SEMUA = [];                                  // semua member termasuk eks
const cari = { status: "semua", pilih: -1, saran: [] };
const LABEL_STATUS = { aktif: "Aktif", trainee: "Trainee", eks: "Eks" };

// Ubin di kartu hasil: strukturnya sama dengan 6 kartu juara + center + SSK
const UBIN = [
  { kolom: "total_show", judul: "Show", satuan: "show", ikon: "show", warna: KATEGORI[0].warnaIkon },
  { kolom: "total_senbatsu", judul: "Senbatsu", satuan: "kali", ikon: "senbatsu", warna: KATEGORI[1].warnaIkon },
  { kolom: "total_lagu", judul: "Lagu", satuan: "lagu", ikon: "lagu", warna: KATEGORI[2].warnaIkon },
  { kolom: "total_center", judul: "Center", satuan: "kali", ikon: "senbatsu", warna: ["#FDE3E3", "#8E0C22"] },
  { kolom: "tinggi_cm", judul: "Tinggi", satuan: "cm", ikon: "tinggi", warna: KATEGORI[3].warnaIkon },
  { kolom: "umur", judul: "Umur", satuan: "tahun", ikon: "umur", warna: KATEGORI[4].warnaIkon, umur: true },
  { kolom: "total_projek", judul: "Projek luar", satuan: "projek", ikon: "projek", warna: KATEGORI[5].warnaIkon },
  { kolom: "ssk_terbaik", judul: "SSK terbaik", satuan: "", ikon: "senbatsu", warna: ["#F6E7B8", "#5C4300"], ssk: true },
];

const normal = (t) => (t || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");

// Peringkat satu member di satu ubin, dibanding semua member yang punya nilainya
function peringkatDiSemua(ubin, m) {
  let daftar;
  if (ubin.umur) {
    if (!m.tanggal_lahir) return null;
    daftar = SEMUA.filter((x) => x.tanggal_lahir).sort((a, b) => a.tanggal_lahir.localeCompare(b.tanggal_lahir));
    const urut = beriPeringkat(daftar, (x) => x.tanggal_lahir);
    return { posisi: urut.find((x) => x.id === m.id).peringkat, dari: urut.length, kata: "tertua" };
  }
  if (ubin.ssk) {
    if (!m.ssk_terbaik) return null;
    daftar = SEMUA.filter((x) => x.ssk_terbaik).sort((a, b) => a.ssk_terbaik - b.ssk_terbaik);
  } else {
    if (!(m[ubin.kolom] > 0)) return null;
    daftar = SEMUA.filter((x) => x[ubin.kolom] > 0).sort((a, b) => b[ubin.kolom] - a[ubin.kolom]);
  }
  const urut = beriPeringkat(daftar, (x) => x[ubin.kolom]);
  return { posisi: urut.find((x) => x.id === m.id).peringkat, dari: urut.length, kata: "" };
}

function teksPeriode(m) {
  const mulai = m.tanggal_bergabung ? tanggal(m.tanggal_bergabung, { month: "short", year: "numeric" }) : "?";
  if (m.status === "eks") {
    const akhir = m.tanggal_lulus ? tanggal(m.tanggal_lulus, { month: "short", year: "numeric" }) : "?";
    return `${mulai} – ${akhir}`;
  }
  return `${mulai} – sekarang`;
}

function kartuHasil(m) {
  const indeks = SEMUA.indexOf(m);
  const ubin = UBIN.map((u) => {
    const nilai = u.ssk ? (m.ssk_terbaik ? `#${m.ssk_terbaik}` : null) : m[u.kolom];
    const ada = nilai !== null && nilai !== undefined;
    const p = peringkatDiSemua(u, m);
    const [bg, fg] = u.warna;
    return `
      <div class="ubin">
        <span class="juara-ikon kecil" style="background:${bg}" aria-hidden="true">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="${fg}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="${IKON[u.ikon]}"/></svg>
        </span>
        <span class="ubin-judul">${u.judul}</span>
        <strong class="ubin-angka">${ada ? (u.ssk ? esc(nilai) : angka(nilai)) : "–"}${ada && u.satuan ? ` <small>${u.satuan}</small>` : ""}</strong>
        <span class="ubin-peringkat">${p ? `Peringkat ${p.kata ? p.kata + " " : ""}<b>#${p.posisi}</b> dari ${p.dari}` : (u.ssk ? "Belum pernah ikut SSK" : "Belum ada data")}</span>
      </div>`;
  }).join("");

  return `
    <article class="kartu-cari">
      <div class="cari-kepala">
        <div class="juara-foto">${htmlFoto(m, indeks)}</div>
        <div class="cari-identitas">
          <span class="lencana-status status-${m.status}">${LABEL_STATUS[m.status] || esc(m.status)}</span>
          <h3>${esc(m.nama_panggilan)}</h3>
          <p>${esc(m.nama_lengkap || "")}</p>
          <p class="redup-kecil">Gen ${m.generasi} · ${esc(m.team ? `Team ${m.team}` : m.status === "trainee" ? "Trainee" : "–")} · ${esc(teksPeriode(m))}</p>
        </div>
        <a class="tombol-lengkap cari-profil" href="detail.html?id=${m.id}">Lihat profil
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 6l6 6-6 6"/></svg></a>
      </div>
      <div class="grid-ubin">${ubin}</div>
      <p class="kartu-catatan">Peringkat dibanding ${SEMUA.length} member (aktif, trainee, eks). Nilai sama = peringkat sama.
        Total lagu & center member eks hanya dari lagu yang tercatat (single, album, digital, projek grup).</p>
    </article>`;
}

function gambarSaran() {
  const input = document.getElementById("cari-input");
  const kata = normal(input.value.trim());
  const daftar = SEMUA.filter((m) => cari.status === "semua" || m.status === cari.status);
  cari.saran = kata
    ? daftar.filter((m) => normal(m.nama_panggilan).includes(kata) || normal(m.nama_lengkap).includes(kata))
        .sort((a, b) => (normal(b.nama_panggilan).startsWith(kata) - normal(a.nama_panggilan).startsWith(kata))
          || a.generasi - b.generasi)
        .slice(0, 8)
    : [];
  const ul = document.getElementById("cari-saran");
  ul.innerHTML = cari.saran.map((m, i) => `
    <li role="option" id="saran-${i}" data-id="${m.id}" aria-selected="${i === cari.pilih}" class="${i === cari.pilih ? "dipilih" : ""}">
      <strong>${esc(m.nama_panggilan)}</strong>
      <span>${esc(m.nama_lengkap || "")}</span>
      <small>Gen ${m.generasi} · ${LABEL_STATUS[m.status] || esc(m.status)}</small>
    </li>`).join("");
  const buka = cari.saran.length > 0;
  ul.hidden = !buka;
  input.setAttribute("aria-expanded", String(buka));
  if (cari.pilih >= 0) input.setAttribute("aria-activedescendant", `saran-${cari.pilih}`);
  else input.removeAttribute("aria-activedescendant");
  document.getElementById("cari-info").textContent = kata && !buka
    ? "Tidak ada member yang cocok."
    : `${daftar.length} member bisa dicari${cari.status === "semua" ? " (aktif, trainee, eks)" : ""}.`;
}

function tampilkanMember(id) {
  const m = SEMUA.find((x) => x.id === Number(id));
  if (!m) return;
  document.getElementById("cari-input").value = m.nama_panggilan;
  cari.saran = []; cari.pilih = -1;
  document.getElementById("cari-saran").hidden = true;
  document.getElementById("cari-input").setAttribute("aria-expanded", "false");
  document.getElementById("cari-hasil").innerHTML = kartuHasil(m);
}

(function pasangCari() {
  const input = document.getElementById("cari-input");
  input.addEventListener("input", () => { cari.pilih = -1; gambarSaran(); });
  input.addEventListener("keydown", (e) => {
    if (!cari.saran.length) return;
    if (e.key === "ArrowDown") { cari.pilih = (cari.pilih + 1) % cari.saran.length; gambarSaran(); e.preventDefault(); }
    else if (e.key === "ArrowUp") { cari.pilih = (cari.pilih - 1 + cari.saran.length) % cari.saran.length; gambarSaran(); e.preventDefault(); }
    else if (e.key === "Enter") { tampilkanMember(cari.saran[Math.max(cari.pilih, 0)].id); e.preventDefault(); }
    else if (e.key === "Escape") { document.getElementById("cari-saran").hidden = true; }
  });
  document.getElementById("cari-saran").addEventListener("click", (e) => {
    const li = e.target.closest("[data-id]");
    if (li) tampilkanMember(li.dataset.id);
  });
  document.addEventListener("click", (e) => {
    if (!e.target.closest(".cari-kotak")) document.getElementById("cari-saran").hidden = true;
  });
  document.querySelectorAll("[data-status]").forEach((t) => t.addEventListener("click", () => {
    cari.status = t.dataset.status;
    document.querySelectorAll("[data-status]").forEach((x) => {
      x.classList.toggle("aktif", x === t);
      x.setAttribute("aria-pressed", String(x === t));
    });
    cari.pilih = -1;
    gambarSaran();
  }));
})();

// Ganti kumpulan member yang dibandingkan (aktif saja <-> all time), lalu gambar ulang
function pakaiKumpulan(daftar) {
  MEMBER = daftar;
  DAFTAR_GEN = [...new Set(MEMBER.map((m) => m.generasi))].sort((a, b) => a - b);
  JUMLAH_PER_GEN = {};
  DAFTAR_GEN.forEach((g) => (JUMLAH_PER_GEN[g] = memberGen(g).length));
  // Generasi yang sedang dipilih tetap dipakai kalau masih ada; kalau tidak, pilih yang membernya terbanyak
  if (!DAFTAR_GEN.includes(keadaan.gen)) {
    keadaan.gen = DAFTAR_GEN.reduce((a, b) => (JUMLAH_PER_GEN[b] > JUMLAH_PER_GEN[a] ? b : a));
  }
  gambarSemua();
}

document.getElementById("centang-alltime").addEventListener("change", (e) => {
  keadaan.allTime = e.target.checked;
  pakaiKumpulan(keadaan.allTime ? SEMUA : MEMBER_AKTIF);
});

async function muatSemuaMember() {
  try {
    SEMUA = await ambil("/api/infografis?termasuk_eks=true");
    document.getElementById("centang-alltime").disabled = false;
    gambarSaran();
  } catch (e) {
    document.getElementById("cari-info").textContent = "Daftar member gagal dimuat.";
  }
}

// ----------------------------------------------------------------------
// Mulai
// ----------------------------------------------------------------------
(async function mulai() {
  muatSemuaMember();               // kotak "Cari member" dimuat terpisah
  try {
    MEMBER_AKTIF = await ambil("/api/infografis");
  } catch (e) {
    document.getElementById("grid-juara").innerHTML = `<p class="memuat">Infografis gagal dimuat.</p>`;
    return;
  }
  if (MEMBER_AKTIF.length === 0) {
    document.getElementById("grid-juara").innerHTML = `<p class="memuat">Belum ada member aktif atau trainee.</p>`;
    return;
  }
  // Generasi default saat "Per generasi" dipilih: generasi dengan member terbanyak (diatur di pakaiKumpulan)
  pakaiKumpulan(MEMBER_AKTIF);
})();
