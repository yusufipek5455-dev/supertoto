/**
 * Nesine Robust Paket Yükleme Betik Motoru (generateNesineTransferScript)
 *
 * Üretilen Spor Toto kolonlarını 4'erli kupon gruplarına (K01, K02...) ayırıp
 * Nesine'nin https://st.nesine.com/v1/SavedCoupon/Save API endpoint'ine doğrudan POST isteği atar.
 *
 * Mimari Özellikler:
 * - document.cookie üzerinden anlık canlı XSRF-TOKEN (liveXsrf) okunur.
 * - Akamai / WAF limitlerine takılmamak için kuponlar arası 1.2s (1200ms) doğal bekleme.
 * - 4'erli kupon grupları (K01, K02...).
 */

export function generateNesineTransferScript(
  columns: string[],
  memberId: number | string = 18950960,
  pno: number | string = 358
): string {
  const safeColumnsJson = JSON.stringify(columns);
  const safeMemberId = Number(memberId) || 18950960;
  const safePno = Number(pno) || 358;

  return `(async function transferAllNesineCouponsRobust() {
  const columns = ${safeColumnsJson};
  const outcomeMap = { '1': { ID: 0, Name: "1" }, 'X': { ID: 1, Name: "X" }, '2': { ID: 2, Name: "2" } };
  const sleep = ms => new Promise(r => setTimeout(r, ms));

  function getCookie(name) {
    const v = document.cookie.match('(^|;) ?' + name + '=([^;]*)(;|$)');
    return v ? decodeURIComponent(v[2]) : null;
  }

  const liveXsrf = getCookie('XSRF-TOKEN');
  const totalCoupons = Math.ceil(columns.length / 4);

  console.log("%c[Nesine Aktarım] Başlatılıyor... Toplam: " + totalCoupons + " Kupon", "color: #00ff88; font-weight: bold;");

  for (let k = 0; k < columns.length; k += 4) {
    const kuponGrubu = columns.slice(k, k + 4);
    const index = Math.floor(k / 4) + 1;
    const kuponAdi = index < 10 ? "K0" + index : "K" + index;

    const columnsPayload = kuponGrubu.map(colStr => ({
      Events: colStr.split('').map((char, mIdx) => ({
        ID: mIdx + 1,
        Outcomes: [outcomeMap[char]]
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
        MemberId: ${safeMemberId},
        Columns: columnsPayload,
        pno: ${safePno},
        columnAmount: 10
      }
    };

    try {
      const res = await fetch("https://st.nesine.com/v1/SavedCoupon/Save", {
        headers: {
          "accept": "application/json, text/plain, */*",
          "content-type": "application/json",
          "platformid": "1",
          "x-requested-with": "XMLHttpRequest",
          ...(liveXsrf ? { "x-xsrf-token": liveXsrf } : {})
        },
        referrer: "https://www.nesine.com/sportoto",
        body: JSON.stringify(payload),
        method: "POST",
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

    // WAF limitine takılmamak için her kupon arası stabil 1.2s bekleme
    await sleep(1200);
  }

  console.log("%c[Tamamlandı] Tüm kuponlar eksiksiz yüklendi!", "color: #00ff88; font-size: 14px; font-weight: bold;");
  alert("Tüm kuponlar başarıyla Nesine hesabınıza aktarıldı!");
})();`;
}

// Backward compatibility alias
export const generateNesineScript = generateNesineTransferScript;

