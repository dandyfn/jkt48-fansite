// member.js
// Halaman Kelola Member:
//   - tabel semua member (cari + filter status)
//   - form tambah / edit (POST atau PUT /api/members)
//   - saldo awal karier (PUT /api/members/{id}/baseline)
//   - hapus (DELETE /api/members/{id})

const KOLOM_MEMBER = [
  "nama_lengkap", "nama_panggilan", "stage_name", "foto_url", "tempat_lahir", "tanggal_lahir",
  "hometown", "tinggi_cm", "golongan_darah", "generasi", "team", "status",
  "tanggal_bergabung", "tanggal_lulus",
];
const KOLOM_ANGKA = ["tinggi_cm", "generasi"];
const KOLOM_BASELINE = ["total_show_awal", "total_lagu_awal", "total_center_awal"];

let semuaMember = [];
let idSedangDiedit = null;     // null = sedang menambah, angka = sedang mengedit

const dialog = document.getElementById("dialog-member");
const form = document.getElementById("form-member");

// =====================================================================
// TABEL
// =====================================================================
async function muatMember() {
  try {
    semuaMember = await panggil("/api/members");
  } catch (e) {
    document.getElementById("tabel-member").innerHTML =
      `<tr><td colspan="7" class="redup">${esc(e.message)}</td></tr>`;
    return;
  }
  tampilkanTabel();
}

function tampilkanTabel() {
  const kata = document.getElementById("cari").value.trim().toLowerCase();
  const status = document.getElementById("filter-status").value;
  const hasil = semuaMember.filter((m) =>
    (!status || m.status === status) &&
    (!kata || [m.nama_panggilan, m.nama_lengkap, m.stage_name, m.hometown, m.team]
      .some((t) => t && t.toLowerCase().includes(kata))));

  document.getElementById("jumlah-member").textContent = `${hasil.length} dari ${semuaMember.length} member`;
  const tbody = document.getElementById("tabel-member");
  if (hasil.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="redup">Tidak ada member yang cocok.</td></tr>`;
    return;
  }
  tbody.innerHTML = hasil.map((m) => `
    <tr>
      <td>
        <div class="sel-member">
          <span class="avatar">${esc(m.nama_panggilan[0])}</span>
          <span><strong>${esc(m.nama_panggilan)}</strong>${m.kapten ? ' <span class="chip chip-emas">Kapten</span>' : ""}<br>
          <small class="redup">${esc(m.nama_lengkap)}</small></span>
        </div>
      </td>
      <td>${m.generasi}</td>
      <td>${esc(m.team || "–")}</td>
      <td><span class="chip status-${esc(m.status)}">${esc(m.status)}</span></td>
      <td>${m.umur ?? "–"}</td>
      <td>${esc(m.lama_di_jkt48 || "–")}</td>
      <td class="kanan">
        <div class="aksi">
          <a class="tombol-kecil" href="../web-user/detail.html?id=${m.id}" target="_blank" rel="noopener" aria-label="Lihat ${esc(m.nama_panggilan)} di web user">Lihat</a>
          <button type="button" class="tombol-kecil" data-edit="${m.id}">Edit</button>
          <button type="button" class="tombol-kecil bahaya" data-hapus="${m.id}">Hapus</button>
        </div>
      </td>
    </tr>`).join("");
}

document.getElementById("cari").addEventListener("input", tampilkanTabel);
document.getElementById("filter-status").addEventListener("change", tampilkanTabel);

// Tombol Edit / Hapus di dalam tabel (satu pendengar untuk semua baris)
document.getElementById("tabel-member").addEventListener("click", (e) => {
  const edit = e.target.closest("[data-edit]");
  const hapus = e.target.closest("[data-hapus]");
  if (edit) bukaForm(Number(edit.dataset.edit));
  if (hapus) hapusMember(Number(hapus.dataset.hapus));
});

// =====================================================================
// FORM TAMBAH / EDIT
// =====================================================================
document.getElementById("tombol-tambah").addEventListener("click", () => bukaForm(null));
dialog.querySelectorAll("[data-tutup]").forEach((t) => t.addEventListener("click", () => dialog.close()));

async function bukaForm(id) {
  idSedangDiedit = id;
  form.reset();
  sembunyikanPesan();
  document.getElementById("judul-dialog").textContent = id ? "Edit member" : "Tambah member";

  if (id) {
    const m = semuaMember.find((x) => x.id === id);
    KOLOM_MEMBER.forEach((k) => (form.elements[k].value = m[k] ?? ""));
    try {
      const b = await panggil(`/api/members/${id}/baseline`);
      document.getElementById("b-tanggal_cutoff").value = b.tanggal_cutoff || "";
      KOLOM_BASELINE.forEach((k) => (document.getElementById("b-" + k).value = b.tanggal_cutoff ? b[k] : ""));
    } catch (e) { /* biarkan kosong */ }
  } else {
    form.elements.status.value = "aktif";
  }
  dialog.showModal();
  document.getElementById("f-nama_lengkap").focus();
}

function ambilDataForm() {
  const data = {};
  KOLOM_MEMBER.forEach((k) => {
    const nilai = form.elements[k].value.trim();
    if (nilai === "") data[k] = null;                       // kosong -> null
    else data[k] = KOLOM_ANGKA.includes(k) ? Number(nilai) : nilai;
  });
  return data;
}

function ambilDataBaseline() {
  const angkaDiisi = KOLOM_BASELINE.some((k) => document.getElementById("b-" + k).value !== "");
  const tgl = document.getElementById("b-tanggal_cutoff").value;
  if (!angkaDiisi && !tgl) return null;                    // tidak diisi sama sekali
  const data = { tanggal_cutoff: tgl || hariIni() };
  KOLOM_BASELINE.forEach((k) => (data[k] = Number(document.getElementById("b-" + k).value || 0)));
  return data;
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  sembunyikanPesan();
  const data = ambilDataForm();

  // Cek sederhana sebelum dikirim
  if (!data.nama_lengkap || !data.nama_panggilan || !data.generasi) {
    tampilkanPesan("Nama lengkap, nama panggilan, dan generasi wajib diisi.");
    return;
  }

  const tombol = document.getElementById("tombol-simpan");
  tombol.disabled = true;
  tombol.textContent = "Menyimpan…";
  try {
    const member = idSedangDiedit
      ? await panggil(`/api/members/${idSedangDiedit}`, { method: "PUT", body: data })
      : await panggil("/api/members", { method: "POST", body: data });

    const baseline = ambilDataBaseline();
    if (baseline) await panggil(`/api/members/${member.id}/baseline`, { method: "PUT", body: baseline });

    dialog.close();
    beriTahu(idSedangDiedit ? `Data ${member.nama_panggilan} diperbarui` : `${member.nama_panggilan} ditambahkan`);
    await muatMember();
  } catch (err) {
    tampilkanPesan(err.message);
  } finally {
    tombol.disabled = false;
    tombol.textContent = "Simpan";
  }
});

function tampilkanPesan(teks) {
  const el = document.getElementById("pesan-form");
  el.textContent = teks;
  el.hidden = false;
  el.scrollIntoView({ block: "nearest" });
}
function sembunyikanPesan() {
  document.getElementById("pesan-form").hidden = true;
}

// =====================================================================
// HAPUS
// =====================================================================
async function hapusMember(id) {
  const m = semuaMember.find((x) => x.id === id);
  if (!confirm(`Hapus ${m.nama_panggilan} (${m.nama_lengkap})?\n\nData yang sudah dihapus tidak bisa dikembalikan.`)) return;
  try {
    await panggil(`/api/members/${id}`, { method: "DELETE" });
    beriTahu(`${m.nama_panggilan} dihapus`);
    await muatMember();
  } catch (err) {
    // 409 = masih punya data show/projek -> sarankan ubah status jadi eks
    beriTahu(err.message, "gagal");
  }
}

muatMember();
