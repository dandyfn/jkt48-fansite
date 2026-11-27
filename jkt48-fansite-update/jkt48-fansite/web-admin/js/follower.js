// follower.js
// Halaman Input Follower:
//   Tab "Input cepat" -> tabel akun + kotak angka, simpan sekaligus (POST /api/sosmed/follower/massal)
//   Tab "Kelola akun" -> daftar/ubah/hapus akun sosmed
//   Tombol tarik IG   -> POST /api/sosmed/instagram/tarik

const LABEL_PLATFORM = { instagram: "Instagram", tiktok: "TikTok", x: "X", youtube: "YouTube" };
const BATAS_WASPADA = 30;   // sama dengan batas di backend (sosmed.py)

let semuaAkun = [];

// =====================================================================
// TAB
// =====================================================================
document.querySelectorAll('[role="tab"]').forEach((tab, i, semua) => {
  tab.addEventListener("click", () => {
    semua.forEach((t) => {
      const pilih = t === tab;
      t.classList.toggle("aktif", pilih);
      t.setAttribute("aria-selected", pilih);
      t.tabIndex = pilih ? 0 : -1;
      document.getElementById(t.getAttribute("aria-controls")).hidden = !pilih;
    });
  });
});

// =====================================================================
// MEMBACA ANGKA: "1.234.567", "850rb", "1,2jt", "1.2m", "15k"
// =====================================================================
function bacaAngka(teks) {
  let t = teks.trim().toLowerCase().replace(/\s/g, "");
  if (!t) return null;
  let kali = 1;
  if (/(jt|juta|m)$/.test(t)) { kali = 1e6; t = t.replace(/(jt|juta|m)$/, ""); }
  else if (/(rb|ribu|k)$/.test(t)) { kali = 1e3; t = t.replace(/(rb|ribu|k)$/, ""); }
  if (kali > 1) {
    t = t.replace(",", ".");                          // 1,2 -> 1.2 (desimal)
  } else {
    t = t.replace(/[.,]/g, "");                       // 1.234.567 -> 1234567
  }
  const n = Number(t);
  return Number.isFinite(n) && n >= 0 ? Math.round(n * kali) : NaN;
}

// =====================================================================
// INPUT CEPAT
// =====================================================================
function akunUntukInput() {
  const platform = document.getElementById("filter-platform").value;
  const sumber = document.getElementById("filter-sumber").value;
  return semuaAkun.filter((a) => a.aktif && (!platform || a.platform === platform) && (!sumber || a.sumber === sumber));
}

function gambarTabelInput() {
  const daftar = akunUntukInput();
  const perlu = daftar.filter((a) => a.perlu_update).length;
  document.getElementById("info-input").textContent = `${daftar.length} akun · ${perlu} perlu diupdate`;
  document.getElementById("tabel-input").innerHTML = daftar.map((a) => `
    <tr data-baris="${a.id}" class="${a.perlu_update ? "perlu-update" : ""}">
      <td><strong>${esc(a.nama_panggilan)}</strong></td>
      <td>
        <span class="chip">${esc(LABEL_PLATFORM[a.platform] || a.platform)}</span>
        <a href="${esc(a.link_profil)}" target="_blank" rel="noopener" class="tautan-buka">@${esc(a.username)} · Buka ↗</a>
      </td>
      <td class="kanan">
        <strong>${a.follower_terakhir !== null ? angka(a.follower_terakhir) : "–"}</strong><br>
        <small class="redup">${a.tanggal_terakhir ? tanggal(a.tanggal_terakhir) : "belum pernah"}</small>
      </td>
      <td>
        <label class="sr-only" for="isi-${a.id}">Follower baru ${esc(a.nama_panggilan)} ${esc(a.platform)}</label>
        <input class="isi-angka" id="isi-${a.id}" data-akun="${a.id}" inputmode="numeric" autocomplete="off" placeholder="contoh 850rb">
      </td>
      <td class="kanan"><span class="perubahan" id="ubah-${a.id}"></span></td>
    </tr>`).join("") || `<tr><td colspan="5" class="redup">Tidak ada akun untuk filter ini. Daftarkan di tab "Kelola akun".</td></tr>`;
  hitungTerisi();
}

// Setiap kali angka diketik: tampilkan perubahan % dan beri warna kalau mencurigakan
document.getElementById("tabel-input").addEventListener("input", (e) => {
  const input = e.target.closest(".isi-angka");
  if (!input) return;
  const akun = semuaAkun.find((a) => a.id === Number(input.dataset.akun));
  const nilai = bacaAngka(input.value);
  const el = document.getElementById("ubah-" + akun.id);
  const baris = input.closest("tr");
  baris.classList.remove("waspada", "salah");
  if (input.value.trim() === "") { el.textContent = ""; }
  else if (Number.isNaN(nilai)) { el.textContent = "angka tidak dikenali"; baris.classList.add("salah"); }
  else if (akun.follower_terakhir) {
    const persen = ((nilai - akun.follower_terakhir) / akun.follower_terakhir) * 100;
    el.textContent = `${angka(nilai)} · ${persen >= 0 ? "+" : ""}${persen.toFixed(1)}%`;
    if (Math.abs(persen) > BATAS_WASPADA) baris.classList.add("waspada");
  } else {
    el.textContent = angka(nilai);
  }
  hitungTerisi();
});

// Enter -> pindah ke kotak berikutnya (lebih cepat dari klik)
document.getElementById("tabel-input").addEventListener("keydown", (e) => {
  if (e.key !== "Enter" || !e.target.matches(".isi-angka")) return;
  e.preventDefault();
  const semua = [...document.querySelectorAll(".isi-angka")];
  const berikut = semua[semua.indexOf(e.target) + 1];
  if (berikut) berikut.focus();
  else document.getElementById("tombol-simpan-semua").focus();
});

function hitungTerisi() {
  const n = [...document.querySelectorAll(".isi-angka")].filter((i) => i.value.trim() !== "").length;
  document.getElementById("info-terisi").textContent = `${n} baris terisi`;
}

document.getElementById("filter-platform").addEventListener("change", gambarTabelInput);
document.getElementById("filter-sumber").addEventListener("change", gambarTabelInput);

document.getElementById("tombol-simpan-semua").addEventListener("click", async (e) => {
  const isian = [...document.querySelectorAll(".isi-angka")].filter((i) => i.value.trim() !== "");
  if (isian.length === 0) return beriTahu("Belum ada angka yang diisi.", "gagal");
  const salah = isian.filter((i) => Number.isNaN(bacaAngka(i.value)));
  if (salah.length) { salah[0].focus(); return beriTahu("Ada angka yang tidak dikenali (baris merah).", "gagal"); }
  const waspada = document.querySelectorAll("tr.waspada").length;
  if (waspada && !confirm(`${waspada} angka berubah lebih dari ${BATAS_WASPADA}% (baris oranye). Yakin sudah benar?`)) return;

  const data = {
    tanggal: document.getElementById("tanggal-input").value,
    data: isian.map((i) => ({ akun_id: Number(i.dataset.akun), followers: bacaAngka(i.value) })),
  };
  const tombol = e.currentTarget;
  tombol.disabled = true;
  tombol.textContent = "Menyimpan…";
  try {
    const hasil = await panggil("/api/sosmed/follower/massal", { method: "POST", body: data });
    beriTahu(`Tersimpan: ${hasil.baru} baru, ${hasil.diperbarui} diperbarui`);
    if (hasil.peringatan.length) {
      beriTahu(`${hasil.peringatan.length} angka mencurigakan: ` +
        hasil.peringatan.map((p) => `${p.nama_panggilan} (${p.perubahan_persen > 0 ? "+" : ""}${p.perubahan_persen}%)`).join(", "), "gagal");
    }
    await muatAkun();
  } catch (err) {
    beriTahu(err.message, "gagal");
  } finally {
    tombol.disabled = false;
    tombol.textContent = "Simpan semua";
  }
});

// =====================================================================
// TARIK INSTAGRAM
// =====================================================================
document.getElementById("tombol-tarik-ig").addEventListener("click", async (e) => {
  const tombol = e.currentTarget;
  const wadah = document.getElementById("hasil-tarik");
  tombol.disabled = true;
  tombol.textContent = "Menarik…";
  try {
    const hasil = await panggil("/api/sosmed/instagram/tarik", { method: "POST" });
    wadah.innerHTML = `
      <p class="kotak-info"><strong>${esc(hasil.pesan)}</strong></p>
      ${hasil.gagal.length ? `<ul class="daftar-gagal">${hasil.gagal.map((g) =>
        `<li><strong>@${esc(g.username)}</strong>: ${esc(g.alasan)}</li>`).join("")}</ul>` : ""}`;
    if (hasil.berhasil.length) await muatAkun();
  } catch (err) {
    beriTahu(err.message, "gagal");
  } finally {
    tombol.disabled = false;
    tombol.textContent = "Tarik sekarang";
  }
});

// =====================================================================
// KELOLA AKUN
// =====================================================================
function gambarTabelAkun() {
  const kata = document.getElementById("cari-akun").value.trim().toLowerCase().replace(/^@/, "");
  const daftar = semuaAkun.filter((a) => !kata ||
    a.nama_panggilan.toLowerCase().includes(kata) || a.username.toLowerCase().includes(kata));
  document.getElementById("info-akun").textContent = `${daftar.length} dari ${semuaAkun.length} akun`;
  document.getElementById("tabel-akun").innerHTML = daftar.map((a) => `
    <tr>
      <td><strong>${esc(a.nama_panggilan)}</strong></td>
      <td>${esc(LABEL_PLATFORM[a.platform] || a.platform)}</td>
      <td><a href="${esc(a.link_profil)}" target="_blank" rel="noopener">@${esc(a.username)}</a></td>
      <td>
        <label class="sr-only" for="sumber-${a.id}">Sumber ${esc(a.username)}</label>
        <select id="sumber-${a.id}" class="pilih-kecil" data-ubah-sumber="${a.id}">
          <option value="manual"${a.sumber === "manual" ? " selected" : ""}>Manual</option>
          <option value="api"${a.sumber === "api" ? " selected" : ""}>API</option>
        </select>
      </td>
      <td><label class="saklar"><input type="checkbox" data-ubah-aktif="${a.id}"${a.aktif ? " checked" : ""}><span class="sr-only">Aktif</span></label></td>
      <td class="kanan">${a.follower_terakhir !== null ? angka(a.follower_terakhir) : "–"}<br><small class="redup">${a.tanggal_terakhir ? tanggal(a.tanggal_terakhir) : ""}</small></td>
      <td class="kanan"><button type="button" class="tombol-kecil bahaya" data-hapus-akun="${a.id}">Hapus</button></td>
    </tr>`).join("") || `<tr><td colspan="7" class="redup">Belum ada akun.</td></tr>`;
}
document.getElementById("cari-akun").addEventListener("input", gambarTabelAkun);

document.getElementById("tabel-akun").addEventListener("change", async (e) => {
  const sumber = e.target.closest("[data-ubah-sumber]");
  const aktif = e.target.closest("[data-ubah-aktif]");
  try {
    if (sumber) {
      await panggil(`/api/sosmed/akun/${sumber.dataset.ubahSumber}`, { method: "PUT", body: { sumber: sumber.value } });
      beriTahu(`Sumber diubah menjadi ${sumber.value}`);
    }
    if (aktif) {
      await panggil(`/api/sosmed/akun/${aktif.dataset.ubahAktif}`, { method: "PUT", body: { aktif: aktif.checked } });
      beriTahu(aktif.checked ? "Akun diaktifkan" : "Akun dinonaktifkan (tidak dihitung di leaderboard)");
    }
    await muatAkun();
  } catch (err) { beriTahu(err.message, "gagal"); }
});

document.getElementById("tabel-akun").addEventListener("click", async (e) => {
  const t = e.target.closest("[data-hapus-akun]");
  if (!t || !confirm("Hapus akun ini beserta SELURUH riwayat follower-nya?")) return;
  try {
    await panggil(`/api/sosmed/akun/${t.dataset.hapusAkun}`, { method: "DELETE" });
    beriTahu("Akun dihapus");
    await muatAkun();
  } catch (err) { beriTahu(err.message, "gagal"); }
});

document.getElementById("form-akun").addEventListener("submit", async (e) => {
  e.preventDefault();
  const data = {
    member_id: Number(document.getElementById("akun-member").value),
    platform: document.getElementById("akun-platform").value,
    username: document.getElementById("akun-username").value.trim(),
    sumber: document.getElementById("akun-sumber").value,
  };
  if (!data.member_id || !data.username) return beriTahu("Member dan username wajib diisi.", "gagal");
  try {
    await panggil("/api/sosmed/akun", { method: "POST", body: data });
    beriTahu(`Akun @${data.username.replace(/^@/, "")} didaftarkan`);
    document.getElementById("akun-username").value = "";
    await muatAkun();
  } catch (err) { beriTahu(err.message, "gagal"); }
});

// =====================================================================
// MULAI
// =====================================================================
async function muatAkun() {
  semuaAkun = await panggil("/api/sosmed/akun?hanya_aktif=false").catch((err) => {
    beriTahu(err.message, "gagal");
    return [];
  });
  gambarTabelInput();
  gambarTabelAkun();
}

(async function mulai() {
  document.getElementById("tanggal-input").value = hariIni();
  const members = await panggil("/api/members").catch(() => []);
  document.getElementById("akun-member").innerHTML = `<option value="">Pilih member…</option>` +
    members.filter((m) => m.status !== "eks")
      .map((m) => `<option value="${m.id}">${esc(m.nama_panggilan)} – ${esc(m.nama_lengkap)}</option>`).join("");
  await muatAkun();
})();
