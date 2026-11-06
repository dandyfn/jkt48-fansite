// dekorasi.js
// Menaburkan corak merah (bintang, titik, lingkaran, hati, plus, bintang garis)
// ke latar halaman. Posisi selalu sama setiap dimuat karena memakai "acak" berbenih.

(function () {
  const wadah = document.getElementById("dekorasi");
  if (!wadah) return;

  // Pembuat angka acak sederhana dengan benih (supaya hasil selalu sama)
  let benih = 11;
  function acak() {
    benih = (benih * 9301 + 49297) % 233280;
    return benih / 233280;
  }

  const MERAH = "#D7192F";
  const BENTUK = {
    bintang: { anim: "anim-kerlip", ukuran: [10, 22], opa: [0.55, 0.4],
      html: `<svg viewBox="0 0 24 24"><path d="M12 0C12.8 7 17 11.2 24 12C17 12.8 12.8 17 12 24C11.2 17 7 12.8 0 12C7 11.2 11.2 7 12 0Z" fill="${MERAH}"/></svg>` },
    titik: { anim: "anim-kedip", ukuran: [4, 6], opa: [0.3, 0.35],
      html: `<div style="border-radius:999px;background:${MERAH}"></div>` },
    cincin: { anim: "anim-melayang", ukuran: [22, 34], opa: [0.16, 0.16],
      html: `<div style="border-radius:999px;border:1.5px solid ${MERAH}"></div>` },
    hati: { anim: "anim-melayang", ukuran: [12, 14], opa: [0.4, 0.35],
      html: `<svg viewBox="0 0 24 24"><path d="M12 21s-7.5-4.6-9.6-9.3C.9 8.2 3 4.5 6.6 4.5c2.1 0 3.6 1.2 5.4 3.2 1.8-2 3.3-3.2 5.4-3.2 3.6 0 5.7 3.7 4.2 7.2C19.5 16.4 12 21 12 21z" fill="${MERAH}"/></svg>` },
    plus: { anim: "anim-kerlip", ukuran: [10, 12], opa: [0.35, 0.35],
      html: `<svg viewBox="0 0 24 24"><path d="M12 3v18M3 12h18" stroke="${MERAH}" stroke-width="3" stroke-linecap="round" fill="none"/></svg>` },
    garis: { anim: "anim-putar", ukuran: [14, 18], opa: [0.35, 0.35],
      html: `<svg viewBox="0 0 24 24"><path d="M12 2.5l2.9 6.1 6.6.8-4.9 4.5 1.3 6.6L12 17.2l-5.9 3.3 1.3-6.6-4.9-4.5 6.6-.8z" fill="none" stroke="${MERAH}" stroke-width="1.6" stroke-linejoin="round"/></svg>` },
  };

  function pilihBentuk(r) {
    if (r < 0.28) return "bintang";
    if (r < 0.48) return "titik";
    if (r < 0.58) return "cincin";
    if (r < 0.72) return "hati";
    if (r < 0.86) return "plus";
    return "garis";
  }

  let html = `
    <div class="polkadot atas"></div>
    <div class="polkadot tengah" style="top:33%"></div>
    <div class="polkadot tengah" style="top:64%"></div>
    <div class="hiasan anim-melayang" style="left:-4%;top:0.6%;width:260px;height:260px;opacity:.12;--durasi:5s;--jeda:0s">${BENTUK.cincin.html.replace("1.5px", "2px")}</div>
    <div class="hiasan anim-melayang" style="left:84%;top:2.4%;width:320px;height:320px;opacity:.1;--durasi:6s;--jeda:1s">${BENTUK.cincin.html.replace("1.5px", "2px")}</div>
    <div class="hiasan besar anim-kerlip" style="left:8%;top:3.2%;width:34px;height:34px;opacity:.9;--durasi:2.6s;--jeda:.2s">${BENTUK.bintang.html}</div>
    <div class="hiasan besar anim-kerlip" style="left:90%;top:1.8%;width:28px;height:28px;opacity:.85;--durasi:3s;--jeda:.8s">${BENTUK.bintang.html}</div>`;

  for (let i = 0; i < 150; i++) {
    const nama = pilihBentuk(acak());
    const b = BENTUK[nama];
    const sisi = acak();
    const kiri = sisi < 0.36 ? acak() * 12 : sisi < 0.72 ? 86 + acak() * 12 : 12 + acak() * 76;
    const ukuran = b.ukuran[0] + Math.round(acak() * b.ukuran[1]);
    const opa = (b.opa[0] + acak() * b.opa[1]).toFixed(2);
    const durasi = nama === "garis" ? 8 + (i % 4) * 2 : 2.2 + (i % 5) * 0.6;
    const jeda = ((i * 0.37) % 3).toFixed(2);
    html += `<div class="hiasan ${b.anim}" style="left:${kiri.toFixed(1)}%;top:${(acak() * 97).toFixed(1)}%;width:${ukuran}px;height:${ukuran}px;opacity:${opa};--durasi:${durasi}s;--jeda:${jeda}s">${b.html}</div>`;
  }
  wadah.innerHTML = html;
})();
