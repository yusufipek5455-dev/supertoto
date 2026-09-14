/**
 * Nesine 10'lu Paket Yükleme Betik Motoru (generateNesineScript)
 *
 * Üretilen Spor Toto kolonlarını 4'erli kupon gruplarına (K01, K02...) ayırıp
 * Nesine'nin https://st.nesine.com/v1/SavedCoupon/Save API endpoint'ine doğrudan POST isteği atar.
 *
 * Düzeltmeler & Güçlendirmeler:
 * - window.SGAuthKey zorunlu yetkilendirme başlığı eklendi.
 * - Nesine'nin HTTP 200 dönüp sc: 401 vermesi durumunu yakalamak için res.json() ile data.sc === 200 kontrolü eklendi.
 * - MemberId dinamik olarak window.Nesine.Instances.Membership.settings.Id ve DOM'dan okunur; üye no uyumsuzlukları önlenir.
 * - Aktif bülten program numarası (pno) https://st.nesine.com/v2/Program veya window.SporTotoData üzerinden dinamik doğrulanır.
 * - Her kupon için tam 4 kolonluk (A, B, C, D) payload oluşturulur; eksik kolonlar Calculable: false ile beslenir.
 * - Oturum kapalıysa kullanıcıyı uyarır ve Nesine giriş penceresini tetikler.
 * - Konsolda detaylı başarı/hata takibi ve işlem sonunda gerçekçi özet rapor verir.
 */

export function generateNesineScript(
  columns: string[],
  memberId?: number | string,
  pno?: number | string
): string {
  const safeColumnsJson = JSON.stringify(columns);
  const fallbackMemberId = memberId ? Number(memberId) : 0;
  const fallbackPno = pno ? Number(pno) : 358;

  return `(async function transferAllNesineCoupons() {
  console.clear();
  console.log("%c⚡ [Spor Toto Akıllı Aktarım Motoru v5.0] Başlatılıyor...", "color: #00e676; font-size: 14px; font-weight: bold;");

  const columns = ${safeColumnsJson};
  if (!columns || columns.length === 0) {
    alert("❌ Aktarılacak kolon verisi bulunamadı!");
    return;
  }

  // 1. Nesine Domain & Oturum Kontrolü
  if (!window.location.hostname.includes("nesine.com")) {
    alert("❌ Bu kod yalnızca www.nesine.com üzerinde çalışır!\\nLütfen https://www.nesine.com/sportoto sayfasına gidip kodu orada çalıştırın.");
    return;
  }

  const isLoginFn = window.Nesine?.Instances?.Membership?.IsLogin;
  if (typeof isLoginFn === "function" && !isLoginFn()) {
    alert("❌ Nesine hesabınıza giriş yapmamış görünüyorsunuz!\\nLütfen önce üye girişi yapın, ardından kodu tekrar çalıştırın.");
    if (window.Nesine?.Instances?.LoginWrapper?.DisplayLoginDialog) {
      window.Nesine.Instances.LoginWrapper.DisplayLoginDialog();
    }
    return;
  }

  // 2. Member ID Dinamik Algılama
  let dynamicMemberId = 0;
  try {
    if (window.Nesine?.Instances?.Membership?.settings?.Id) {
      dynamicMemberId = Number(window.Nesine.Instances.Membership.settings.Id);
    } else if (window.SporTotoData?.MemberId) {
      dynamicMemberId = Number(window.SporTotoData.MemberId);
    } else if (window.user?.memberId) {
      dynamicMemberId = Number(window.user.memberId);
    } else {
      const el = document.querySelector("#lblUyeNo, .user-no, [data-memberid], .member-id, .uye-no");
      if (el) dynamicMemberId = Number(el.innerText.replace(/\\D/g, ""));
    }
  } catch (e) {}

  if (!dynamicMemberId && ${fallbackMemberId}) {
    dynamicMemberId = ${fallbackMemberId};
  }

  if (!dynamicMemberId) {
    const inputId = prompt("Nesine Üye Numaranız otomatik tespit edilemedi.\\nLütfen 8 haneli Nesine Üye Numaranızı girin:");
    if (inputId) dynamicMemberId = Number(inputId.replace(/\\D/g, ""));
  }

  if (!dynamicMemberId) {
    alert("❌ Üye numarası olmadan kuponlar kaydedilemez. İşlem durduruldu.");
    return;
  }

  // 3. API Yetkilendirme Anahtarı (SGAuthKey)
  const defaultAuthKey = "Basic RDQ3MDc4RDMtNjcwQi00OUJBLTgxNUYtM0IyMjI2MTM1MTZCOkI4MzJCQjZGLTQwMjgtNDIwNS05NjFELTg1N0QxRTZEOTk0OA==";
  const authKey = window.SGAuthKey || defaultAuthKey;

  // 4. Bülten Program Numarası (pno) Doğrulama
  let dynamicPno = ${fallbackPno};
  try {
    if (window.SporTotoData?.Program?.pno) {
      dynamicPno = Number(window.SporTotoData.Program.pno);
    } else if (window.SporTotoData?.pno) {
      dynamicPno = Number(window.SporTotoData.pno);
    } else {
      const pRes = await fetch("https://st.nesine.com/v2/Program", {
        headers: { "Authorization": authKey, "Referer": "https://www.nesine.com/" }
      });
      const pData = await pRes.json();
      if (pData.sc === 200 && pData.d?.pNo) {
        dynamicPno = Number(pData.d.pNo);
      }
    }
  } catch (e) {}

  // 5. XSRF Token Okuma
  let xsrfToken = "";
  try {
    const xsrfCookie = document.cookie.split("; ").find(row => row.startsWith("XSRF-TOKEN="));
    if (xsrfCookie) xsrfToken = decodeURIComponent(xsrfCookie.split("=")[1]);
  } catch (e) {}

  const outcomeMap = {
    '1': { ID: 0, Name: "1" },
    'X': { ID: 1, Name: "X" },
    '0': { ID: 1, Name: "X" },
    '2': { ID: 2, Name: "2" }
  };
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const BATCH_SIZE = 10;
  const COOLDOWN_MS = 2500;

  const totalCoupons = Math.ceil(columns.length / 4);
  console.log("%c[Bilgi] Üye No: " + dynamicMemberId + " | Program (pno): " + dynamicPno + " | Kolon Sayısı: " + columns.length + " (" + totalCoupons + " kupon)", "color: #38bdf8; font-weight: bold;");

  let successCount = 0;
  let failCount = 0;
  const errors = [];

  for (let k = 0; k < columns.length; k += 4) {
    const kuponGrubu = columns.slice(k, k + 4);
    const index = Math.floor(k / 4) + 1;
    const kuponAdi = index < 10 ? "K0" + index : "K" + index;

    // Nesine 4 Kolon (A, B, C, D) standardına göre Columns dizisini 4 elemanlı oluştur
    const columnsPayload = [];
    for (let slot = 0; slot < 4; slot++) {
      if (slot < kuponGrubu.length) {
        const colStr = kuponGrubu[slot];
        columnsPayload.push({
          Events: colStr.split("").map((char, mIdx) => ({
            ID: mIdx + 1,
            Outcomes: [outcomeMap[char] || { ID: 0, Name: "1" }]
          })),
          Playable: true,
          DoubleBetCount: 0,
          TripleBetCount: 0,
          SelectedRowCount: 15,
          Calculable: true
        });
      } else {
        // Boş slotları Calculable: false olarak ekle
        columnsPayload.push({
          Events: [],
          Playable: false,
          DoubleBetCount: 0,
          TripleBetCount: 0,
          SelectedRowCount: 0,
          Calculable: false
        });
      }
    }

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

    const reqHeaders = {
      "accept": "application/json, text/plain, */*",
      "content-type": "application/json",
      "authorization": authKey,
      "x-alt-referrer": window.location.href,
      "x-requested-with": "XMLHttpRequest"
    };
    if (xsrfToken) reqHeaders["x-xsrf-token"] = xsrfToken;

    try {
      const res = await fetch("https://st.nesine.com/v1/SavedCoupon/Save", {
        headers: reqHeaders,
        referrer: window.location.href,
        body: JSON.stringify(payload),
        method: "POST",
        mode: "cors",
        credentials: "include"
      });

      const data = await res.json();

      // Nesine Başarı Protokolü: HTTP 200 AND sc === 200
      if (data && data.sc === 200 && data.d) {
        successCount++;
        const barcode = data.d.barcode || "KAYDEDILDI";
        console.log(\`%c[✓ \${index}/\${totalCoupons}] \${kuponAdi} kaydedildi (Barkod: \${barcode})\`, "color: #00e676; font-weight: bold;");
      } else {
        failCount++;
        const errMsg = data?.ml?.[0]?.m || data?.el?.[0]?.m || ("Hata Kodu (sc): " + (data?.sc || "Bilinmiyor"));
        errors.push(\`\${kuponAdi}: \${errMsg}\`);
        console.error(\`%c[✗ \${index}/\${totalCoupons}] \${kuponAdi} KAYDEDILEMEDI: \${errMsg}\`, "color: #ff5252; font-weight: bold;");
      }
    } catch (err) {
      failCount++;
      errors.push(\`\${kuponAdi}: Ağ Hatası (\${err.message})\`);
      console.error(\`[AĞ HATASI] \${kuponAdi}:\`, err);
    }

    await sleep(350);

    // Her 10 kuponda bir rate-limit molası
    if (index % BATCH_SIZE === 0 && index !== totalCoupons) {
      console.log(\`%c[Mola] 10 kupon tamamlandı, \${COOLDOWN_MS / 1000}s bekleniyor...\`, "color: #ffb300; font-weight: bold;");
      await sleep(COOLDOWN_MS);
    }
  }

  console.log("%c===============================================", "color: #38bdf8;");
  console.log(\`%c[Aktarım Özeti] Başarılı: \${successCount} / \${totalCoupons} | Başarısız: \${failCount}\`, "font-size: 13px; font-weight: bold; color: " + (failCount === 0 ? "#00e676" : "#ff5252"));

  if (failCount === 0) {
    alert(\`🎉 TEBRİKLER!\\n\\nToplam \${successCount} adet kupon (\${columns.length} kolon) Nesine hesabınıza (Kayıtlı Kuponlar) eksiksiz olarak kaydedildi!\\n\\nNesine menüsünden "Kayıtlı Kuponlarım" sayfasına giderek kontrol edebilirsiniz.\`);
  } else {
    alert(\`⚠️ AKTARIM TAMAMLANDI (KISMİ HATA)\\n\\n- Başarılı: \${successCount} adet kupon\\n- Hatalı: \${failCount} adet kupon\\n\\nHata Detayları için klavyeden F12 tuşuna basıp Konsol sekmesine bakınız:\\n\${errors.slice(0, 3).join("\\n")}\`);
  }
})();`;
}

// Backward compatibility alias
export const generateNesineTransferScript = generateNesineScript;
