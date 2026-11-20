// pemilih.js
// Komponen "pemilih member": deretan tombol nama member yang bisa diklik
// untuk memilih / batal memilih. Dilengkapi pencarian, filter team,
// tombol pilih semua, dan (opsional) tanda center.
//
// Cara pakai:
//   const p = buatPemilih(document.getElementById("wadah"), daftarMember, { denganCenter: true });
//   p.ambilTerpilih()     -> [{ member_id: 3, is_center: false }, ...]
//   p.pilih([1, 2, 3])    -> pilih member tertentu
//   p.kosongkan()
//   p.aturModeCenter(true/false)

function buatPemilih(wadah, members, { denganCenter = false } = {}) {
  const terpilih = new Map();          // member_id -> is_center
  let modeCenter = denganCenter;
  let filterTeam = "";
  const idUnik = "p" + Math.random().toString(36).slice(2, 7);

  const team = [...new Set(members.map((m) => m.team || "Trainee"))].sort();

  wadah.classList.add("pemilih");
  wadah.innerHTML = `
    <div class="pemilih-alat">
      <label class="sr-only" for="${idUnik}-cari">Cari member</label>
      <input type="search" id="${idUnik}-cari" class="pemilih-cari" placeholder="Cari nama…" autocomplete="off">
      <div class="pemilih-team" role="group" aria-label="Filter team">
        <button type="button" class="chip-filter aktif" data-team="">Semua</button>
        ${team.map((t) => `<button type="button" class="chip-filter" data-team="${esc(t)}">${esc(t)}</button>`).join("")}
      </div>
      <div class="pemilih-aksi">
        <button type="button" class="tombol-kecil" data-aksi="semua">Pilih semua yang tampil</button>
        <button type="button" class="tombol-kecil" data-aksi="kosong">Kosongkan</button>
        <span class="pemilih-jumlah" aria-live="polite"></span>
      </div>
    </div>
    <p class="redup kecil pemilih-petunjuk"></p>
    <div class="pemilih-grid"></div>`;

  const grid = wadah.querySelector(".pemilih-grid");
  const cari = wadah.querySelector(".pemilih-cari");

  function yangTampil() {
    const kata = cari.value.trim().toLowerCase();
    return members.filter((m) =>
      (!filterTeam || (m.team || "Trainee") === filterTeam) &&
      (!kata || m.nama_panggilan.toLowerCase().includes(kata) || m.nama_lengkap.toLowerCase().includes(kata)));
  }

  function gambar() {
    wadah.querySelector(".pemilih-petunjuk").textContent = modeCenter
      ? "Klik nama untuk memilih. Klik ★ pada member terpilih untuk menandai posisi center."
      : "Klik nama untuk memilih atau membatalkan.";
    grid.innerHTML = yangTampil().map((m) => {
      const pilih = terpilih.has(m.id);
      const center = terpilih.get(m.id) === true;
      return `
        <div class="item-pilih${pilih ? " dipilih" : ""}${center ? " center" : ""}">
          <button type="button" class="tombol-nama" data-id="${m.id}" aria-pressed="${pilih}">
            <span class="centang" aria-hidden="true">${pilih ? "✓" : ""}</span>
            <span>${esc(m.nama_panggilan)}<small>${esc(m.team || "Trainee")} · Gen ${m.generasi}</small></span>
          </button>
          ${modeCenter && pilih
            ? `<button type="button" class="tombol-center" data-center="${m.id}" aria-pressed="${center}" title="Tandai center" aria-label="Center: ${esc(m.nama_panggilan)}">★</button>`
            : ""}
        </div>`;
    }).join("") || `<p class="redup">Tidak ada member yang cocok.</p>`;
    const nCenter = [...terpilih.values()].filter(Boolean).length;
    wadah.querySelector(".pemilih-jumlah").textContent =
      `${terpilih.size} dipilih` + (modeCenter && nCenter ? ` · ${nCenter} center` : "");
  }

  grid.addEventListener("click", (e) => {
    const nama = e.target.closest("[data-id]");
    const center = e.target.closest("[data-center]");
    if (nama) {
      const id = Number(nama.dataset.id);
      terpilih.has(id) ? terpilih.delete(id) : terpilih.set(id, false);
    }
    if (center) {
      const id = Number(center.dataset.center);
      terpilih.set(id, !terpilih.get(id));
    }
    gambar();
  });
  cari.addEventListener("input", gambar);
  wadah.querySelector(".pemilih-team").addEventListener("click", (e) => {
    const t = e.target.closest("[data-team]");
    if (!t) return;
    filterTeam = t.dataset.team;
    wadah.querySelectorAll(".chip-filter").forEach((c) => c.classList.toggle("aktif", c === t));
    gambar();
  });
  wadah.querySelector(".pemilih-aksi").addEventListener("click", (e) => {
    const aksi = e.target.closest("[data-aksi]");
    if (!aksi) return;
    if (aksi.dataset.aksi === "semua") yangTampil().forEach((m) => terpilih.has(m.id) || terpilih.set(m.id, false));
    if (aksi.dataset.aksi === "kosong") terpilih.clear();
    gambar();
  });

  gambar();
  return {
    ambilTerpilih: () => [...terpilih.entries()].map(([member_id, is_center]) => ({ member_id, is_center })),
    pilih(ids) { ids.forEach((id) => members.some((m) => m.id === id) && terpilih.set(id, false)); gambar(); },
    kosongkan() { terpilih.clear(); cari.value = ""; gambar(); },
    aturModeCenter(nyala) {
      modeCenter = nyala;
      if (!nyala) terpilih.forEach((_, id) => terpilih.set(id, false));
      gambar();
    },
  };
}
