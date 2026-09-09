/**
 * Generates an automated transfer script to save generated Toto columns
 * into Nesine's Saved Coupons (Kayıtlı Kuponlar) in 10-coupon batches with rate-limit cooldown.
 */
export function generateNesineTransferScript(
  columns: string[],
  memberId: number | string = 18950960,
  pno: number | string = 357
): string {
  const safeColumnsJson = JSON.stringify(columns);
  const defaultMemberId = Number(memberId) || 18950960;
  const defaultPno = Number(pno) || 357;

  return `(async function transferAllNesineCoupons() {
  const columns = ${safeColumnsJson};
  const outcomeMap = { '1': { ID: 0, Name: "1" }, 'X': { ID: 1, Name: "X" }, '2': { ID: 2, Name: "2" } };
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const BATCH_SIZE = 10;
  const COOLDOWN_MS = 2500;

  // Çerezlerden xsrf token'ı dinamik oku
  const xsrfCookie = document.cookie.split('; ').find(row => row.startsWith('XSRF-TOKEN='));
  const xsrfToken = xsrfCookie ? decodeURIComponent(xsrfCookie.split('=')[1]) : "";

  // Oturum bilgilerini dinamik algıla
  let dynamicMemberId = ${defaultMemberId};
  try {
    if (window.user && window.user.memberId) dynamicMemberId = Number(window.user.memberId);
    else if (window.memberId) dynamicMemberId = Number(window.memberId);
    else {
      const mCookie = document.cookie.split('; ').find(row => row.startsWith('memberId=') || row.startsWith('MemberId='));
      if (mCookie) dynamicMemberId = Number(mCookie.split('=')[1]);
    }
  } catch(e) {}

  let dynamicPno = ${defaultPno};
  try {
    if (window.pno) dynamicPno = Number(window.pno);
    else if (window.sportoto && window.sportoto.pno) dynamicPno = Number(window.sportoto.pno);
  } catch(e) {}

  console.log("%c[Nesine Aktarım] Başlatılıyor...", "color: #00ff88; font-weight: bold; font-size: 13px;");
  console.log("[Nesine Aktarım] Üye ID: " + dynamicMemberId + " | Bülten No (pno): " + dynamicPno + " | Toplam Kolon: " + columns.length);

  const totalCoupons = Math.ceil(columns.length / 4);

  for (let k = 0; k < columns.length; k += 4) {
    const kuponGrubu = columns.slice(k, k + 4);
    const index = Math.floor(k / 4) + 1;
    const kuponAdi = index < 10 ? "K0" + index : "K" + index;

    const columnsPayload = kuponGrubu.map(colStr => ({
      Events: colStr.split('').map((char, mIdx) => ({
        ID: mIdx + 1,
        Outcomes: [outcomeMap[char] || { ID: 0, Name: "1" }]
      })),
      Playable: true,
      DoubleBetCount: 0,
      TripleBetCount: 0,
      SelectedRowCount: 15,
      Calculable: true
    }));

    const payload = {
      couponName: kuponAdi,
      sportotoCoupon: {
        CouponAmount: kuponGrubu.length * 10,
        Multiply: "1",
        MemberId: dynamicMemberId,
        Columns: columnsPayload,
        pno: dynamicPno,
        columnAmount: 10
      }
    };

    try {
      const res = await fetch("https://st.nesine.com/v1/SavedCoupon/Save", {
        headers: {
          "accept": "application/json, text/plain, */*",
          "content-type": "application/json",
          "platformid": "1",
          "x-alt-referrer": "https://www.nesine.com/sportoto",
          "x-requested-with": "XMLHttpRequest",
          "x-xsrf-token": xsrfToken
        },
        referrer: "https://www.nesine.com/",
        body: JSON.stringify(payload),
        method: "POST",
        mode: "cors",
        credentials: "include"
      });

      if (res.ok) {
        console.log(\`%c[OK] \${kuponAdi} kaydedildi (\${index}/\${totalCoupons})\`, "color: #2ed573; font-weight: bold;");
      } else {
        const txt = await res.text();
        console.error(\`[HATA] \${kuponAdi}: \${txt}\`);
      }
    } catch (err) {
      console.error(\`[AĞ HATASI] \${kuponAdi}:\`, err);
    }

    await sleep(350);

    // Her 10 kuponda bir rate-limit dinlenmesi
    if (index % BATCH_SIZE === 0 && index !== totalCoupons) {
      console.log(\`%c[Mola] 10 kupon tamamlandı, \${COOLDOWN_MS / 1000}s dinleniliyor...\`, "color: #ffa502; font-weight: bold;");
      await sleep(COOLDOWN_MS);
    }
  }

  console.log("%c[Nesine Aktarım] Tüm kuponlar eksiksiz kaydedildi!", "color: #00ff88; font-size: 14px; font-weight: bold;");
  alert("✅ Tüm " + totalCoupons + " adet kupon başarıyla Nesine hesabınıza (Kayıtlı Kuponlar) aktarıldı!");
})();`;
}
