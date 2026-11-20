// pengaturan.js
//   Simpan leaderboard -> POST /api/leaderboard/simpan
//   Aturan poin        -> GET / PUT /api/aturan-poin
//   Profil grup        -> GET / PUT /api/grup

// Tanggal "YYYY-MM-DD" digeser sekian hari
function geserHari(str, hari) {
  const d = new Date(str + "T00:00:00");
  d.setDate(d.getDate() + hari);
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
}

// =====================================================================
// SIMPAN LEADERBOARD
// =====================================================================
async function simpanLeaderboard(periode, dari, sampai, tombol) {
  const teks = tombol.textContent;
  tombol.disabled = true;
  tombol.textContent = "Menyimpan…";
  try {
    const hasil = await panggil(`/api/leaderboard/simpan?periode=${periode}&dari=${dari}&sampai=${sampai}`, { method: "POST" });
    const el = document.getElementById("hasil-simpan");
    el.hidden = false;
    el.textContent = `${hasil.pesan}: ${hasil.jumlah_periode} periode ${periode === "minggu" ? "mingguan" : "bulanan"}, ` +
      `${hasil.jumlah_baris} baris skor ` +
      (dari === sampai ? `(periode yang mencakup ${tanggal(dari)}).` : `(${tanggal(dari)} – ${tanggal(sampai)}).`);
    beriTahu("Leaderboard tersimpan");
  } catch (err) {
    beriTahu(err.message, "gagal");
  } finally {
    tombol.disabled = false;
    tombol.textContent = teks;
  }
}

document.getElementById("simpan-minggu-lalu").addEventListener("click", (e) => {
  const tgl = geserHari(hariIni(), -7);                 // tanggal mana saja di minggu lalu
  simpanLeaderboard("minggu", tgl, tgl, e.currentTarget);
});
document.getElementById("simpan-bulan-lalu").addEventListener("click", (e) => {
  const awalBulanIni = hariIni().slice(0, 8) + "01";
  const tgl = geserHari(awalBulanIni, -1);              // hari terakhir bulan lalu
  simpanLeaderboard("bulan", tgl, tgl, e.currentTarget);
});
document.getElementById("form-rentang").addEventListener("submit", (e) => {
  e.preventDefault();
  const dari = document.getElementById("rentang-dari").value;
  const sampai = document.getElementById("rentang-sampai").value;
  if (!dari || !sampai) return beriTahu("Isi tanggal dari dan sampai.", "gagal");
  if (sampai < dari) return beriTahu("Tanggal 'sampai' tidak boleh sebelum 'dari'.", "gagal");
  simpanLeaderboard(document.getElementById("rentang-periode").value, dari, sampai, e.submitter);
});

// =====================================================================
// ATURAN POIN
// =====================================================================
async function muatAturan() {
  const aturan = await panggil("/api/aturan-poin").catch(() => []);
  document.getElementById("tabel-aturan").innerHTML = aturan.map((a) => {
    const rumus = a.kode === "ssk";
    return `
      <tr>
        <td><strong>${esc(a.nama)}</strong><br><small class="redup">${esc(a.keterangan || "")}</small></td>
        <td class="kanan">
          ${rumus ? '<span class="redup kecil">pakai rumus</span>' : `
          <label class="sr-only" for="poin-${esc(a.kode)}">Poin ${esc(a.nama)}</label>
          <input type="number" min="0" step="0.5" class="isi-poin" id="poin-${esc(a.kode)}" value="${a.poin}" data-awal="${a.poin}">`}
        </td>
        <td class="kanan">${rumus ? "" : `<button type="button" class="tombol-kecil" data-simpan-aturan="${esc(a.kode)}">Simpan</button>`}</td>
      </tr>`;
  }).join("");
}

document.getElementById("tabel-aturan").addEventListener("click", async (e) => {
  const t = e.target.closest("[data-simpan-aturan]");
  if (!t) return;
  const kode = t.dataset.simpanAturan;
  const input = document.getElementById("poin-" + kode);
  const poin = Number(input.value);
  if (input.value === "" || poin < 0) return beriTahu("Poin harus angka 0 atau lebih.", "gagal");
  if (poin === Number(input.dataset.awal)) return beriTahu("Nilainya belum diubah.");
  if (!confirm(`Ubah poin menjadi ${poin}? Semua poin lama jenis ini ikut dihitung ulang.`)) return;
  try {
    await panggil(`/api/aturan-poin/${kode}`, { method: "PUT", body: { poin } });
    beriTahu("Aturan poin diperbarui");
    await muatAturan();
  } catch (err) { beriTahu(err.message, "gagal"); }
});

// =====================================================================
// PROFIL GRUP
// =====================================================================
async function muatGrup() {
  const grup = await panggil("/api/grup").catch(() => null);
  if (!grup) return;
  document.getElementById("grup-nama").value = grup.info.nama || "";
  document.getElementById("grup-tanggal").value = grup.info.tanggal_dibentuk || "";
  document.getElementById("grup-logo").value = grup.info.logo_url || "";
  document.getElementById("grup-deskripsi").value = grup.info.deskripsi || "";
}

document.getElementById("form-grup").addEventListener("submit", async (e) => {
  e.preventDefault();
  const data = {
    nama: document.getElementById("grup-nama").value.trim() || "JKT48",
    tanggal_dibentuk: document.getElementById("grup-tanggal").value || null,
    logo_url: document.getElementById("grup-logo").value.trim() || null,
    deskripsi: document.getElementById("grup-deskripsi").value.trim() || null,
  };
  try {
    await panggil("/api/grup", { method: "PUT", body: data });
    beriTahu("Profil grup disimpan");
  } catch (err) { beriTahu(err.message, "gagal"); }
});

// =====================================================================
// MULAI
// =====================================================================
document.getElementById("rentang-dari").value = geserHari(hariIni(), -182);   // ±6 bulan lalu
document.getElementById("rentang-sampai").value = geserHari(hariIni(), -7);
muatAturan();
muatGrup();
