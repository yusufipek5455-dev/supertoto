// ==UserScript==
// @name         Spor Toto Nesine Enjektör & Veri Köprüsü
// @namespace    http://tampermonkey.net/
// @version      3.6
// @description  Nesine Spor Toto bülteni ve halk oranlarını kusursuz kopyalar; kuponları 15 ms mikro hızla sepete basar.
// @author       Syndicate Quant Engine
// @match        https://www.nesine.com/sportoto*
// @match        https://www.nesine.com/spor-toto*
// @match        https://*.nesine.com/sportoto*
// @match        https://*.nesine.com/spor-toto*
// @match        http://localhost:8501/*
// @match        http://127.0.0.1:8501/*
// @grant        GM_setValue
// @grant        GM_getValue
// ==/UserScript==

(function () {
    'use strict';

    // Streamlit Localhost Köprüsü: LocalStorage -> Tampermonkey GM Storage
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        const syncStorage = () => {
            try {
                const val = localStorage.getItem("TOTO_AUTO_INJECT");
                if (val && typeof GM_setValue === 'function') {
                    GM_setValue("TOTO_AUTO_INJECT", val);
                }
            } catch (e) {}
        };
        window.addEventListener('storage', syncStorage);
        setInterval(syncStorage, 800);
        return; // Localhost'ta Nesine terminal arayüzünü açma
    }

    const sleep = (ms) => new Promise(r => setTimeout(r, ms));

    function trigger(el, isCheck = true) {
        if (!el) return;
        ['mouseover', 'mousedown'].forEach(evt => {
            el.dispatchEvent(new MouseEvent(evt, { bubbles: true, cancelable: true }));
        });
        
        if (el.click) el.click();
        
        try {
            if (el instanceof HTMLInputElement) {
                const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'checked');
                if (nativeSetter && nativeSetter.set) {
                    nativeSetter.set.call(el, isCheck);
                } else {
                    el.checked = isCheck;
                }
            } else if ('checked' in el) {
                el.checked = isCheck;
            }
        } catch (e) {
            if ('checked' in el) el.checked = isCheck;
        }

        ['mouseup', 'input', 'change'].forEach(evt => {
            el.dispatchEvent(new Event(evt, { bubbles: true, cancelable: true }));
        });
    }

    function getMatchRows() {
        const allTrs = Array.from(document.querySelectorAll('table tbody tr, table tr, .st-match-row, .spor-toto-row, [data-match-id], tr[data-m]'));
        return allTrs.filter(tr => tr.querySelectorAll('input[type="checkbox"], .checkbox, [data-choice]').length >= 3).slice(0, 15);
    }

    let isRunning = false;
    let isCanceled = false;
    let fileLoadedPayload = null;

    function initTerminalUI() {
        if (document.getElementById('toto-terminal-box')) return;

        const box = document.createElement('div');
        box.id = 'toto-terminal-box';
        box.style.cssText = `
            position: fixed;
            top: 70px;
            right: 20px;
            z-index: 9999999;
            background: #0f172a;
            color: #f8fafc;
            padding: 12px;
            border-radius: 8px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.7);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            width: 320px;
            border: 1px solid #334155;
        `;

        box.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <span style="font-weight:700; font-size:12px; color:#38bdf8;">⚡ TOTO KOKPİT KÖPRÜSÜ</span>
                <span id="toto-status-tag" style="font-size:10px; color:#10b981; font-weight:600;">HAZIR</span>
            </div>
            
            <button id="btn-export-bulten" style="width:100%; background:#0284c7; color:#fff; border:none; padding:7px; border-radius:5px; font-weight:600; font-size:12px; cursor:pointer; margin-bottom:8px;">
                📤 Güncel Bülten & Oranları Kopyala
            </button>

            <!-- Sürükle Bırak / Dosya Seçme Alanı (Pano Boyutu Sınırı Koruması) -->
            <div id="drop-zone" style="border: 2px dashed #475569; border-radius: 6px; padding: 7px 6px; text-align: center; margin-bottom: 6px; cursor: pointer; background: #1e293b; transition: all 0.2s;">
                <span id="drop-zone-text" style="font-size: 11px; color: #94a3b8; display: block;">
                    📁 .JSON Dosyası Sürükle veya Seç
                </span>
                <input type="file" id="file-sheets-json" accept=".json,application/json" style="display: none;" />
            </div>

            <textarea id="txt-sheets-json" placeholder="Veya JSON kodunu buraya yapıştır..." 
                style="width:100%; height:50px; background:#0f172a; color:#fff; border:1px solid #334155; border-radius:4px; padding:6px; font-size:11px; box-sizing:border-box; resize:none;"></textarea>
            
            <div style="margin-top:8px; display:flex; gap:5px;">
                <button id="btn-fill-coupons" style="flex:2; background:#059669; color:#fff; border:none; padding:7px; border-radius:5px; font-weight:700; font-size:12px; cursor:pointer;">
                    🚀 Kuponları Doldur
                </button>
                <button id="btn-stop-coupons" style="flex:2; background:#dc2626; color:#fff; border:none; padding:7px; border-radius:5px; font-weight:700; font-size:12px; cursor:pointer; display:none;">
                    ⏹️ Durdur
                </button>
                <button id="btn-paste-clip" style="flex:1; background:#0284c7; color:#fff; border:none; padding:7px; border-radius:5px; font-size:11px; cursor:pointer;" title="Panodaki kupon JSON kodunu yapıştır">
                    📋 Yapıştır
                </button>
                <button id="btn-clear-coupons" style="flex:1; background:#475569; color:#fff; border:none; padding:7px; border-radius:5px; font-size:11px; cursor:pointer;">
                    Temizle
                </button>
            </div>
            <div id="toto-log" style="margin-top:6px; font-size:10px; color:#94a3b8; text-align:center; min-height:16px;">
                Bekleniyor...
            </div>
        `;

        document.body.appendChild(box);

        document.getElementById('btn-export-bulten').onclick = scrapeFixtures;
        document.getElementById('btn-fill-coupons').onclick = startInjection;
        document.getElementById('btn-stop-coupons').onclick = stopInjection;
        document.getElementById('btn-clear-coupons').onclick = clearAllSelections;

        document.getElementById('btn-paste-clip').onclick = async () => {
            try {
                const text = await navigator.clipboard.readText();
                if (text) {
                    const parsed = JSON.parse(text);
                    applyAutoPayload(parsed);
                }
            } catch (err) {
                const log = document.getElementById('toto-log');
                if (log) log.innerHTML = `<span style="color:#ef4444;">Panodan okunamadı. Lütfen metin kutusuna Ctrl+V ile yapıştırın.</span>`;
            }
        };

        // Dosya Yükleme & Drag-Drop Yönetimi
        const dropZone = document.getElementById('drop-zone');
        const fileInput = document.getElementById('file-sheets-json');
        const dropText = document.getElementById('drop-zone-text');

        dropZone.onclick = () => fileInput.click();

        fileInput.onchange = (e) => {
            const file = e.target.files[0];
            if (file) handleJsonFile(file);
        };

        dropZone.ondragover = (e) => {
            e.preventDefault();
            dropZone.style.borderColor = '#38bdf8';
            dropZone.style.background = '#0f172a';
        };

        dropZone.ondragleave = () => {
            dropZone.style.borderColor = '#475569';
            dropZone.style.background = '#1e293b';
        };

        dropZone.ondrop = (e) => {
            e.preventDefault();
            dropZone.style.borderColor = '#475569';
            dropZone.style.background = '#1e293b';
            const file = e.dataTransfer.files[0];
            if (file) handleJsonFile(file);
        };

        function applyAutoPayload(parsed) {
            fileLoadedPayload = parsed;
            const txtArea = document.getElementById('txt-sheets-json');
            if (txtArea) {
                txtArea.value = typeof parsed === 'string' ? parsed : JSON.stringify(parsed, null, 2);
            }
            const sCount = parsed.total_sheets || (parsed.sheets ? parsed.sheets.length : (Array.isArray(parsed) ? Math.ceil(parsed.length / 4) : (parsed.cols ? Math.ceil(parsed.cols.length / 4) : 0)));
            const cCount = parsed.total_columns || (parsed.cols ? parsed.cols.length : (sCount * 4));
            if (dropText) {
                dropText.innerHTML = `<span style="color:#38bdf8; font-weight:700;">🚀 Otomatik Kupon Aktarıldı!</span><br><span style="color:#10b981; font-size:10px;">${sCount} Sayfa (${cCount} Kolon - ${cCount * 10} TL)</span>`;
            }
            const log = document.getElementById('toto-log');
            if (log) {
                log.innerHTML = `<span style="color:#10b981; font-weight:700;">⚡ Kupon hazır! "Kuponları Doldur"a basarak sepete ekleyebilirsiniz.</span>`;
            }
            const statusTag = document.getElementById('toto-status-tag');
            if (statusTag) {
                statusTag.innerText = 'KUPON YÜKLENDİ';
                statusTag.style.color = '#38bdf8';
            }
        }

        async function checkForAutoInject() {
            let autoPayload = null;
            // 1. GM_getValue denetimi (Cross-Domain Köprü)
            try {
                if (typeof GM_getValue === 'function') {
                    const gmVal = GM_getValue("TOTO_AUTO_INJECT");
                    if (gmVal) {
                        autoPayload = typeof gmVal === 'string' ? JSON.parse(gmVal) : gmVal;
                        GM_setValue("TOTO_AUTO_INJECT", null); // Tek kullanımlık tüketim
                    }
                }
            } catch (e) {}

            // 2. localStorage denetimi
            if (!autoPayload) {
                try {
                    const lsVal = localStorage.getItem("TOTO_AUTO_INJECT");
                    if (lsVal) {
                        autoPayload = JSON.parse(lsVal);
                    }
                } catch (e) {}
            }

            // 3. URL hash auto_inject işareti varsa panodan otomatik okuma
            if (!autoPayload && (window.location.hash.includes("auto_inject") || window.location.search.includes("auto_inject"))) {
                try {
                    if (navigator.clipboard && navigator.clipboard.readText) {
                        const clipText = await navigator.clipboard.readText();
                        if (clipText) {
                            try {
                                const parsed = JSON.parse(clipText);
                                if (parsed && (parsed.sheets || parsed.cols || parsed.columns || Array.isArray(parsed))) {
                                    autoPayload = parsed;
                                }
                            } catch (e) {}
                        }
                    }
                } catch (e) {}
            }

            if (autoPayload) {
                applyAutoPayload(autoPayload);
            }
        }

        setTimeout(checkForAutoInject, 400);

        function handleJsonFile(file) {
            const reader = new FileReader();
            reader.onload = (evt) => {
                try {
                    const parsed = JSON.parse(evt.target.result);
                    applyAutoPayload(parsed);
                } catch (err) {
                    fileLoadedPayload = null;
                    document.getElementById('toto-log').innerHTML = `<span style="color:#ef4444;">Dosya okunamadı: Geçersiz JSON formatı!</span>`;
                }
            };
            reader.readAsText(file);
        }
    }

    function stopInjection() {
        if (isRunning) {
            isCanceled = true;
            document.getElementById('toto-log').innerHTML = `<span style="color:#f59e0b;">🛑 Durduruluyor, lütfen bekleyin...</span>`;
        }
    }

    // Nesine Tablosundan Maçları ve Oranları Hatasız Ayıklayıcı (Çift Snapshot ile Phantom Odds Korumalı)
    async function scrapeFixtures() {
        const log = document.getElementById('toto-log');
        log.innerHTML = `<span style="color:#38bdf8;">Tablo taranıyor ve oran kararlılığı doğrulanıyor...</span>`;

        function extractSnapshot() {
            const rows = document.querySelectorAll('table tbody tr, table tr');
            const list = [];
            const NOISE_REGEX = /^(canl[ıi]|ilk yar[ıi]|ikinci yar[ıi]|iy|ms|uzatma|ert|ipt|k[ıi]rm[ıi]z[ıi] kart|\d+['’]|\d+\s*[-–:]\s*\d+)$/i;
            const cleanStr = (s) => s ? s.replace(/\b\d+\s*[-–:]\s*\d+\b/g, '').replace(/\b(canl[ıi]|iy|ms|ert|ipt)\b/gi, '').trim() : "";
            const parsePercent = (valStr, fallback) => {
                if (!valStr) return fallback;
                const n = parseFloat(valStr.replace(',', '.'));
                return isNaN(n) ? fallback : n;
            };

            rows.forEach((tr) => {
                if (list.length >= 15) return;
                const tds = tr.querySelectorAll('td');
                if (tds.length < 4) return;

                const mNo = parseInt(tds[0]?.innerText?.trim(), 10);
                if (isNaN(mNo) || mNo < 1 || mNo > 15) return;

                const dateStr = tds[1]?.innerText?.replace(/\s+/g, ' ')?.trim() || "";
                const teamCell = tds[2];
                let home = "", away = "";

                // 1. Doğrudan kulüp adı etiketleri
                const explicitTeamEls = teamCell.querySelectorAll('.team, .team-name, .home-team, .away-team, .col-team, a[title], span[title], [data-team], [data-team-name]');
                if (explicitTeamEls.length >= 2) {
                    home = cleanStr(explicitTeamEls[0].getAttribute('title') || explicitTeamEls[0].innerText || "");
                    away = cleanStr(explicitTeamEls[1].getAttribute('title') || explicitTeamEls[1].innerText || "");
                }

                // 2. Yedek metin ayrıştırma
                if (!home || !away) {
                    let teamRaw = teamCell.innerText?.trim() || "";
                    let parts = teamRaw.split('\n').map(s => s.trim()).filter(s => s && !NOISE_REGEX.test(s));
                    if (parts.length < 2) {
                        parts = teamRaw.replace(/[–—]/g, '-').split('-').map(s => s.trim()).filter(s => s && !NOISE_REGEX.test(s));
                    }
                    home = cleanStr(parts[0]) || `Ev Sahibi ${mNo}`;
                    away = cleanStr(parts[1]) || `Deplasman ${mNo}`;
                }

                // Halk Oranları
                let p1 = 33.3, px = 33.3, p2 = 33.4;
                const ratesText = tds[3]?.innerText || "";
                const matches = ratesText.match(/(\d{1,2}(?:[\.,]\d+)?)/g);
                if (matches && matches.length >= 3) {
                    p1 = parsePercent(matches[0], 33.3);
                    px = parsePercent(matches[1], 33.3);
                    p2 = parsePercent(matches[2], 33.4);
                }

                list.push({
                    no: mNo,
                    date: dateStr,
                    home: home,
                    away: away,
                    odds: [p1, px, p2]
                });
            });
            return list;
        }

        // Phantom Odds Koruması: Arka arkaya 2 snapshot al ve WebSocket/XHR yarışını ele
        let list1 = extractSnapshot();
        await sleep(50);
        let list2 = extractSnapshot();

        let finalList = list1;
        if (JSON.stringify(list1) !== JSON.stringify(list2)) {
            // Oranlar o anda değişti, kararlı durum için 3. kez bekle ve al
            await sleep(60);
            finalList = extractSnapshot();
        }

        if (finalList.length === 15) {
            const jsonText = JSON.stringify(finalList, null, 2);
            try {
                localStorage.setItem('nesine_toto_bulletin_backup', jsonText);
                localStorage.setItem('nesine_toto_bulletin_backup_time', new Date().toISOString());
            } catch (e) {
                console.warn('localStorage backup failed:', e);
            }
            navigator.clipboard.writeText(jsonText).then(() => {
                log.innerHTML = `<span style="color:#10b981; font-weight:700;">✅ 15 Maç ve Oran Kopyalandı (ve Yerel Yedeklendi)!</span>`;
            }).catch(() => {
                log.innerHTML = `<span style="color:#f59e0b;">Panoya kopyalanamadı, konsola yazıldı.</span>`;
                console.log(jsonText);
            });
        } else {
            log.innerHTML = `<span style="color:#f59e0b;">⚠️ ${finalList.length} Maç Bulundu. Sayfayı yenileyip deneyin.</span>`;
        }
    }

    async function clearAllSelections() {
        const log = document.getElementById('toto-log');
        const rows = getMatchRows();
        let count = 0;
        for (const row of rows) {
            const cbs = Array.from(row.querySelectorAll('input[type="checkbox"], .checkbox, [data-choice]'));
            for (const cb of cbs) {
                if (cb.checked || cb.classList.contains('active') || cb.classList.contains('selected')) {
                    trigger(cb, false);
                    count++;
                }
            }
        }
        fileLoadedPayload = null;
        document.getElementById('txt-sheets-json').value = '';
        const dropText = document.getElementById('drop-zone-text');
        if (dropText) dropText.innerHTML = `📁 .JSON Dosyası Sürükle veya Seç`;
        log.innerText = `${count} işaret temizlendi.`;
    }

    // Kuponları 40 TL'lik Bloklar Halinde Sepete Atan Anti-Bot Korumalı Enjeksiyon Motoru
    async function startInjection() {
        const log = document.getElementById('toto-log');
        const btnFill = document.getElementById('btn-fill-coupons');
        const btnStop = document.getElementById('btn-stop-coupons');
        const statusTag = document.getElementById('toto-status-tag');

        let payload = fileLoadedPayload;
        if (!payload) {
            const raw = document.getElementById('txt-sheets-json').value.trim();
            if (!raw) {
                log.innerHTML = '<span style="color:#ef4444;">Lütfen JSON dosyasını yükleyin veya metni yapıştırın!</span>';
                return;
            }
            try {
                payload = JSON.parse(raw);
            } catch (e) {
                log.innerHTML = '<span style="color:#ef4444;">Geçersiz JSON formatı!</span>';
                return;
            }
        }

        let sheets = [];
        // Kompakt 15 Karakter Kupon Dizisi Desteği
        if (payload.compact && Array.isArray(payload.cols)) {
            const totalSheets = Math.ceil(payload.cols.length / 4);
            for (let s = 0; s < totalSheets; s++) {
                sheets.push({
                    sheet_id: s + 1,
                    A: typeof payload.cols[s * 4] === 'string' ? payload.cols[s * 4].split("") : (payload.cols[s * 4] || []),
                    B: typeof payload.cols[s * 4 + 1] === 'string' ? payload.cols[s * 4 + 1].split("") : (payload.cols[s * 4 + 1] || []),
                    C: typeof payload.cols[s * 4 + 2] === 'string' ? payload.cols[s * 4 + 2].split("") : (payload.cols[s * 4 + 2] || []),
                    D: typeof payload.cols[s * 4 + 3] === 'string' ? payload.cols[s * 4 + 3].split("") : (payload.cols[s * 4 + 3] || [])
                });
            }
        } else if (payload.sheets && Array.isArray(payload.sheets)) {
            sheets = payload.sheets;
        } else if (Array.isArray(payload)) {
            if (payload.length > 0 && typeof payload[0] === 'string' && payload[0].length === 15) {
                // Düz 15 karakterlik dizilim listesi
                const totalSheets = Math.ceil(payload.length / 4);
                for (let s = 0; s < totalSheets; s++) {
                    sheets.push({
                        sheet_id: s + 1,
                        A: (payload[s * 4] || "").split(""),
                        B: (payload[s * 4 + 1] || "").split(""),
                        C: (payload[s * 4 + 2] || "").split(""),
                        D: (payload[s * 4 + 3] || "").split("")
                    });
                }
            } else if (payload.length > 0 && payload[0].A) {
                sheets = payload;
            } else {
                const totalSheets = Math.ceil(payload.length / 4);
                for (let s = 0; s < totalSheets; s++) {
                    sheets.push({
                        sheet_id: s + 1,
                        A: payload[s * 4] || [],
                        B: payload[s * 4 + 1] || [],
                        C: payload[s * 4 + 2] || [],
                        D: payload[s * 4 + 3] || []
                    });
                }
            }
        }

        if (!sheets || sheets.length === 0) {
            log.innerHTML = '<span style="color:#ef4444;">Sayfada kupon yaprağı bulunamadı!</span>';
            return;
        }

        const matchRows = getMatchRows();
        const letterOffsets = { 'A': 0, 'B': 3, 'C': 6, 'D': 9 };
        const optToIndex = { '1': 0, 'X': 1, '0': 1, '2': 2 };

        // Çalışma durumu UI güncellemesi
        isRunning = true;
        isCanceled = false;
        btnFill.style.display = 'none';
        btnStop.style.display = 'block';
        statusTag.innerText = 'DOLDURULUYOR...';
        statusTag.style.color = '#38bdf8';

        log.innerHTML = `<span style="color:#38bdf8;">0 / ${sheets.length} Sayfa Dolduruluyor...</span>`;

        try {
            for (let s = 0; s < sheets.length; s++) {
                if (isCanceled) {
                    log.innerHTML = `<span style="color:#f59e0b; font-weight:700;">🛑 İşlem Durduruldu (${s} / ${sheets.length} sayfa tamamlandı).</span>`;
                    break;
                }

                const sheet = sheets[s];
                const letters = ['A', 'B', 'C', 'D'];

                // Sayfa Bütünlük Denetimi (Incomplete Sheet Koruması - Nesine Eksik Kolon Hatası Önleyici)
                const isComplete = letters.every(l => {
                    const p = sheet[l];
                    return (Array.isArray(p) ? p.length : (typeof p === 'string' ? p.length : 0)) >= 15;
                });
                if (!isComplete) {
                    log.innerHTML = `<span style="color:#ef4444; font-weight:700;">HATA: Sayfa #${s+1} eksik kolon içeriyor (A, B, C, D 15 maç tam dolu olmalıdır)!</span>`;
                    break;
                }

                // Sayfa Öncesi Temizlik (Pre-Sheet Clearance - Phantom Checkbox Koruması)
                if (matchRows.length >= 15) {
                    for (let m = 0; m < 15; m++) {
                        const cbs = Array.from(matchRows[m].querySelectorAll('input[type="checkbox"], .checkbox, [data-choice]'));
                        for (const cb of cbs) {
                            if (cb.checked || cb.classList.contains('active') || cb.classList.contains('selected')) {
                                trigger(cb, false);
                            }
                        }
                    }
                    await sleep(30);
                }

                for (let l = 0; l < letters.length; l++) {
                    if (isCanceled) break;

                    const char = letters[l];
                    const rawPicks = sheet[char];
                    const picks = Array.isArray(rawPicks) ? rawPicks : (typeof rawPicks === 'string' ? rawPicks.split("") : []);
                    if (!picks || picks.length < 15) continue;

                    for (let m = 0; m < 15; m++) {
                        if (isCanceled) break;

                        const pick = picks[m];
                        
                        // Öncelik 1: Veri Özniteliği Seçicileri
                        let btn = document.querySelector(`[data-mno="${m+1}"][data-col="${char}"][data-val="${pick}"]`) ||
                                  document.querySelector(`input[data-m="${m+1}"][data-c="${char}"][data-v="${pick}"]`);
                        
                        // Öncelik 2: Nesine Standart Satır/Hücre İndeksi
                        if (!btn && matchRows.length >= 15) {
                            const baseOffset = letterOffsets[char] || 0;
                            const cbs = Array.from(matchRows[m].querySelectorAll('input[type="checkbox"], .checkbox, [data-choice]'));
                            if (cbs.length >= 12) {
                                btn = cbs[baseOffset + optToIndex[pick]];
                            }
                        }

                        if (btn) {
                            // 1. Lazy-rendered alt maçlar için ekrana kaydır
                            btn.scrollIntoView({ behavior: 'instant', block: 'center' });
                            
                            trigger(btn, true);

                            // 2. Doğrulama (Confirmation) Döngüsü - DOM repaint teyidi
                            for (let retry = 0; retry < 2; retry++) {
                                const isChecked = btn.checked || btn.classList.contains('active') || btn.classList.contains('selected');
                                if (isChecked) break;
                                await sleep(15);
                                trigger(btn, true);
                            }

                            // 3. Güvenli İnsan Benzeri Tıklama Titremesi (35-55 ms)
                            const clickJitter = 35 + Math.floor(Math.random() * 20);
                            await sleep(clickJitter);
                        }
                    }
                }

                if (isCanceled) {
                    log.innerHTML = `<span style="color:#f59e0b; font-weight:700;">🛑 İşlem Durduruldu (${s} / ${sheets.length} sayfa tamamlandı).</span>`;
                    break;
                }

                log.innerHTML = `<span style="color:#38bdf8;">${s + 1} / ${sheets.length} Sayfa Sepete Ekleniyor...</span>`;
                
                // Sayfa Tamamlama & Fiyat Hesaplama Beklemesi (500-750 ms)
                const sheetJitter = 500 + Math.floor(Math.random() * 250);
                await sleep(sheetJitter);

                // Sepete Ekle / Oyna Butonunu Tetikle
                const addBtn = document.querySelector('.btn-add-basket, #btnSaveCoupon, button[data-action="add-basket"], #btnHemenOyna, .btn-play');
                if (addBtn && s < sheets.length - 1) {
                    trigger(addBtn, true);
                    // Sepete Ekleme Sonrası API / DOM Yerleşme Beklemesi (700-1100 ms)
                    const basketJitter = 700 + Math.floor(Math.random() * 400);
                    await sleep(basketJitter);
                }
            }

            if (!isCanceled) {
                log.innerHTML = `<span style="color:#10b981; font-weight:700;">✅ ${sheets.length * 40} TL Kupon Hazır! Onaylayabilirsiniz.</span>`;
            }
        } finally {
            isRunning = false;
            isCanceled = false;
            btnFill.style.display = 'block';
            btnStop.style.display = 'none';
            statusTag.innerText = 'HAZIR';
            statusTag.style.color = '#10b981';
        }
    }

    if (document.readyState === 'loading') {
        window.addEventListener('DOMContentLoaded', () => setTimeout(initTerminalUI, 1200));
    } else {
        setTimeout(initTerminalUI, 1200);
    }
})();
