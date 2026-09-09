// ==UserScript==
// @name         Antigravity Nesine Spor Toto Otomatik Kupon Doldurucu (Multi-Cover 40 TL Sheets)
// @namespace    https://antigravity.ai/
// @version      4.5
// @description  Streamlit Spor Toto Cockpit 40 TL Kolonlarını (A-B-C-D Harf Düzeni / 960 TL - 480 TL) Nesine.com bültenine tek tıkla otomatik doldurur.
// @author       Antigravity Quant Team
// @match        https://*.nesine.com/spor-toto*
// @match        https://www.nesine.com/spor-toto*
// @grant        none
// ==/UserScript==

(function() {
    'use strict';

    console.log('%c⚡ [Antigravity] Nesine Spor Toto Multi-Covering 40 TL Injector v4.5 Aktif.', 'color: #38bdf8; font-weight: bold;');

    let loadedPayload = null;
    let sheetsList = [];
    let currentSheetIdx = 0;
    let isInjecting = false;

    const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

    function createInjectorWidget() {
        if (document.getElementById('antigravity-nesine-widget')) return;

        const widget = document.createElement('div');
        widget.id = 'antigravity-nesine-widget';
        widget.style.cssText = `
            position: fixed;
            top: 60px;
            right: 20px;
            width: 390px;
            background: #0f172a;
            color: #f8fafc;
            border: 2px solid #0284c7;
            border-radius: 10px;
            padding: 14px;
            z-index: 9999999;
            box-shadow: 0 10px 30px rgba(0,0,0,0.7);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            font-size: 12px;
        `;

        widget.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; padding-bottom: 8px; margin-bottom: 10px;">
                <div style="font-weight: 800; font-size: 13px; color: #38bdf8; display: flex; align-items: center; gap: 6px;">
                    <span>⚡ ANTIGRAVITY</span>
                    <span style="background: #0284c7; color: #fff; font-size: 10px; padding: 2px 6px; border-radius: 3px;">MULTI-COVER 40 TL</span>
                </div>
                <div style="cursor: pointer; font-size: 16px; color: #94a3b8;" id="ag-toggle-btn">➖</div>
            </div>

            <div id="ag-body">
                <div style="margin-bottom: 8px; color: #94a3b8; font-size: 11px;">
                    Kokpitten kopyaladığınız 40 TL Sheet JSON aktarım verisini yapıştırın:
                </div>
                <textarea id="ag-payload-input" placeholder="📋 JSON verisini buraya yapıştırın..." style="
                    width: 100%;
                    height: 70px;
                    background: #1e293b;
                    border: 1px solid #475569;
                    border-radius: 6px;
                    color: #e2e8f0;
                    padding: 6px;
                    font-size: 11px;
                    font-family: monospace;
                    box-sizing: border-box;
                    margin-bottom: 8px;
                    resize: vertical;
                "></textarea>

                <div style="display: flex; gap: 6px; margin-bottom: 10px;">
                    <button id="ag-btn-parse" style="
                        flex: 1;
                        background: #0284c7;
                        color: #ffffff;
                        border: none;
                        border-radius: 4px;
                        padding: 7px;
                        font-weight: 700;
                        cursor: pointer;
                    ">📥 Kolonları Yükle</button>
                    <button id="ag-btn-clear" style="
                        background: #475569;
                        color: #ffffff;
                        border: none;
                        border-radius: 4px;
                        padding: 7px 10px;
                        cursor: pointer;
                    ">🧹 Temizle</button>
                </div>

                <div id="ag-status-box" style="
                    background: #1e293b;
                    border-left: 3px solid #38bdf8;
                    padding: 8px;
                    border-radius: 4px;
                    margin-bottom: 10px;
                    font-size: 11px;
                    color: #cbd5e1;
                    line-height: 1.4;
                ">
                    Durum: <strong>Kupon bekleniyor...</strong>
                </div>

                <div id="ag-controls" style="display: none; flex-direction: column; gap: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: 700; color: #38bdf8;">Aktif Kupon:</span>
                        <select id="ag-sheet-select" style="
                            background: #1e293b;
                            color: #fff;
                            border: 1px solid #475569;
                            border-radius: 4px;
                            padding: 4px 8px;
                            font-size: 11px;
                            max-width: 240px;
                        "></select>
                    </div>

                    <button id="ag-btn-inject-sheet" style="
                        background: #16a34a;
                        color: #ffffff;
                        border: none;
                        border-radius: 6px;
                        padding: 11px;
                        font-weight: 800;
                        font-size: 13px;
                        cursor: pointer;
                        box-shadow: 0 2px 8px rgba(22, 163, 74, 0.4);
                    ">🚀 Bu Kolonları Doldur (40 TL / A-B-C-D)</button>

                    <div style="display: flex; gap: 6px;">
                        <button id="ag-btn-prev" style="flex: 1; background: #334155; color: #fff; border: none; padding: 7px; border-radius: 4px; cursor: pointer; font-weight: 600;">⬅️ Önceki</button>
                        <button id="ag-btn-next" style="flex: 1; background: #334155; color: #fff; border: none; padding: 7px; border-radius: 4px; cursor: pointer; font-weight: 600;">Sonraki ➡️</button>
                    </div>

                    <div style="border-top: 1px solid #334155; padding-top: 8px; display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 10px; color: #94a3b8;">Tek Harf Doldur:</span>
                        <div style="display: flex; gap: 4px;">
                            <button class="ag-btn-letter" data-letter="A" style="background:#1e293b; border:1px solid #475569; color:#fff; padding:2px 8px; border-radius:3px; cursor:pointer;">A</button>
                            <button class="ag-btn-letter" data-letter="B" style="background:#1e293b; border:1px solid #475569; color:#fff; padding:2px 8px; border-radius:3px; cursor:pointer;">B</button>
                            <button class="ag-btn-letter" data-letter="C" style="background:#1e293b; border:1px solid #475569; color:#fff; padding:2px 8px; border-radius:3px; cursor:pointer;">C</button>
                            <button class="ag-btn-letter" data-letter="D" style="background:#1e293b; border:1px solid #475569; color:#fff; padding:2px 8px; border-radius:3px; cursor:pointer;">D</button>
                        </div>
                    </div>

                    <button id="ag-btn-auto-step" style="
                        background: #d97706;
                        color: #ffffff;
                        border: none;
                        border-radius: 4px;
                        padding: 7px;
                        font-weight: 700;
                        font-size: 11px;
                        cursor: pointer;
                    ">🛒 Doldur & Sepete Ekle ve İlerle ⏩</button>
                </div>
            </div>
        `;

        document.body.appendChild(widget);

        let isMinimized = false;
        document.getElementById('ag-toggle-btn').onclick = () => {
            isMinimized = !isMinimized;
            document.getElementById('ag-body').style.display = isMinimized ? 'none' : 'block';
            document.getElementById('ag-toggle-btn').innerText = isMinimized ? '➕' : '➖';
        };

        document.getElementById('ag-btn-parse').onclick = parsePayloadInput;
        document.getElementById('ag-btn-clear').onclick = clearNesineCheckboxes;
        document.getElementById('ag-btn-inject-sheet').onclick = injectSelectedSheet;

        document.getElementById('ag-sheet-select').onchange = (e) => {
            currentSheetIdx = parseInt(e.target.value);
            updateStatusBox();
        };

        document.getElementById('ag-btn-prev').onclick = () => {
            if (currentSheetIdx > 0) {
                currentSheetIdx--;
                document.getElementById('ag-sheet-select').value = currentSheetIdx;
                updateStatusBox();
            }
        };

        document.getElementById('ag-btn-next').onclick = () => {
            if (currentSheetIdx < sheetsList.length - 1) {
                currentSheetIdx++;
                document.getElementById('ag-sheet-select').value = currentSheetIdx;
                updateStatusBox();
            }
        };

        widget.querySelectorAll('.ag-btn-letter').forEach(btn => {
            btn.onclick = async (e) => {
                if (isInjecting || !sheetsList[currentSheetIdx]) return;
                const letter = e.target.getAttribute('data-letter');
                const s = sheetsList[currentSheetIdx];
                if (!s || !s[letter] || s[letter].length < 15) {
                    alert(`Harf ${letter} için kupon bulunamadı.`);
                    return;
                }
                isInjecting = true;
                await injectLetterPicks(s[letter], letter);
                isInjecting = false;
                alert(`✅ Harf ${letter} (10 TL) dolduruldu!`);
            };
        });

        document.getElementById('ag-btn-auto-step').onclick = async () => {
            if (isInjecting || !sheetsList[currentSheetIdx]) return;
            isInjecting = true;
            const s = sheetsList[currentSheetIdx];
            const ok = await injectFullSheet(s);
            if (!ok) {
                isInjecting = false;
                alert('Tablo bulunamadı.');
                return;
            }

            const playBtn = document.querySelector('#btnHemenOyna, .btn-play, .btnPlay, button[data-test="play-button"], [data-action="play"]');
            if (playBtn) {
                playBtn.click();
                await sleep(500);
            }

            if (currentSheetIdx < sheetsList.length - 1) {
                currentSheetIdx++;
                document.getElementById('ag-sheet-select').value = currentSheetIdx;
                updateStatusBox();
                alert(`✅ Kupon #${s.sheet_id} dolduruldu! Sıradaki Kupon #${currentSheetIdx + 1} hazır.`);
            } else {
                alert(`🎉 Tüm ${sheetsList.length * 4} Kolon tamamlandı!`);
            }
            isInjecting = false;
        };
    }

    function parsePayloadInput() {
        const raw = document.getElementById('ag-payload-input').value.trim();
        if (!raw) {
            alert('Lütfen önce veriyi yapıştırın.');
            return;
        }

        try {
            sheetsList = [];
            loadedPayload = JSON.parse(raw);

            if (loadedPayload.sheets && Array.isArray(loadedPayload.sheets)) {
                sheetsList = loadedPayload.sheets;
            } else if (loadedPayload.A && Array.isArray(loadedPayload.A)) {
                sheetsList = [loadedPayload];
            } else if (loadedPayload.tickets && Array.isArray(loadedPayload.tickets)) {
                const tks = loadedPayload.tickets;
                const totalSheets = Math.ceil(tks.length / 4);
                for (let s = 0; s < totalSheets; s++) {
                    sheetsList.push({
                        sheet_id: s + 1,
                        name: `Kupon #${s + 1} (4 Kolon)`,
                        cost_tl: Math.min(4, tks.length - s * 4) * 10,
                        A: tks[s * 4] || [],
                        B: tks[s * 4 + 1] || [],
                        C: tks[s * 4 + 2] || [],
                        D: tks[s * 4 + 3] || []
                    });
                }
            } else if (Array.isArray(loadedPayload)) {
                if (loadedPayload.length > 0 && loadedPayload[0].A) {
                    sheetsList = loadedPayload;
                } else {
                    const totalSheets = Math.ceil(loadedPayload.length / 4);
                    for (let s = 0; s < totalSheets; s++) {
                        sheetsList.push({
                            sheet_id: s + 1,
                            name: `Kupon #${s + 1} (4 Kolon)`,
                            cost_tl: Math.min(4, loadedPayload.length - s * 4) * 10,
                            A: loadedPayload[s * 4] || [],
                            B: loadedPayload[s * 4 + 1] || [],
                            C: loadedPayload[s * 4 + 2] || [],
                            D: loadedPayload[s * 4 + 3] || []
                        });
                    }
                }
            }

            if (!sheetsList || sheetsList.length === 0) throw new Error('Geçerli kolon listesi bulunamadı.');

            const sel = document.getElementById('ag-sheet-select');
            sel.innerHTML = '';
            sheetsList.forEach((s, idx) => {
                const opt = document.createElement('option');
                opt.value = idx;
                const sCost = s.cost_tl || 40.0;
                opt.innerText = `📋 Kupon #${s.sheet_id || idx + 1} (${sCost} TL)`;
                sel.appendChild(opt);
            });

            currentSheetIdx = 0;
            document.getElementById('ag-controls').style.display = 'flex';
            updateStatusBox();
            const totalCost = loadedPayload.total_cost_tl || sheetsList.reduce((acc, s) => acc + (s.cost_tl || 40), 0);
            alert(`✅ ${sheetsList.length * 4} Kolon (${totalCost} TL) başarıyla yüklendi!`);
        } catch (err) {
            console.error('[Antigravity] Parse hatası:', err);
            alert('Ayrıştırma hatası: JSON formatı geçersiz.');
        }
    }

    function updateStatusBox() {
        const s = sheetsList[currentSheetIdx];
        const mode = loadedPayload.guarantee_mode || loadedPayload.preset_mode || '13G Garanti (R=2 Multi-Cover)';
        const totalCost = loadedPayload.total_cost_tl || (sheetsList.length * 40);
        const curCost = s ? (s.cost_tl || 40) : 40;
        document.getElementById('ag-status-box').innerHTML = `
            <div>Seçili: <strong>Kupon #${currentSheetIdx + 1}</strong> (${currentSheetIdx + 1} / ${sheetsList.length}) [${curCost} TL]</div>
            <div>Mod: <span style="color: #38bdf8; font-weight: 700;">${mode}</span></div>
            <div>Genel Toplam: <strong>${sheetsList.length * 4} Kolon (${totalCost} TL)</strong></div>
        `;
    }

    async function clickNesineBox(el, targetChecked) {
        if (!el) return;
        const isChecked = Boolean(el.checked || el.classList.contains('active') || el.classList.contains('selected'));
        if (isChecked !== targetChecked) {
            el.dispatchEvent(new MouseEvent('mouseover', { bubbles: true, cancelable: true }));
            el.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true }));
            el.click();

            try {
                if (el instanceof HTMLInputElement) {
                    const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'checked');
                    if (nativeSetter && nativeSetter.set) {
                        nativeSetter.set.call(el, targetChecked);
                    } else {
                        el.checked = targetChecked;
                    }
                } else if ('checked' in el) {
                    el.checked = targetChecked;
                }
            } catch (err) {
                if ('checked' in el) el.checked = targetChecked;
            }

            el.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, cancelable: true }));
            el.dispatchEvent(new Event('input', { bubbles: true, cancelable: true }));
            el.dispatchEvent(new Event('change', { bubbles: true, cancelable: true }));
            await sleep(15);
        }
    }

    function getMatchRows() {
        const allTrs = Array.from(document.querySelectorAll('table tr, .st-match-row, .spor-toto-row, [data-match-id], tr[data-m]'));
        return allTrs.filter(tr => tr.querySelectorAll('input[type="checkbox"], .checkbox, [data-choice]').length >= 3).slice(0, 15);
    }

    async function clearNesineCheckboxes() {
        const rows = getMatchRows();
        let count = 0;
        for (const row of rows) {
            const cbs = Array.from(row.querySelectorAll('input[type="checkbox"], .checkbox'));
            for (const cb of cbs) {
                if (cb.checked || cb.classList.contains('active')) {
                    await clickNesineBox(cb, false);
                    count++;
                }
            }
        }
        alert(`🧹 ${count} adet işaret temizlendi.`);
    }

    async function clearLetterSlot(targetSlot) {
        const rows = getMatchRows();
        if (rows.length < 15) return;
        const letterOffsets = { 'A': 0, 'B': 3, 'C': 6, 'D': 9 };
        const baseOffset = letterOffsets[targetSlot] || 0;
        for (let mIdx = 0; mIdx < 15; mIdx++) {
            const row = rows[mIdx];
            const cbs = Array.from(row.querySelectorAll('input[type="checkbox"], .checkbox, [data-choice]'));
            if (cbs.length < 12) continue;
            for (let opt = 0; opt < 3; opt++) {
                const cbEl = cbs[baseOffset + opt];
                if (cbEl && (cbEl.checked || cbEl.classList.contains('active') || cbEl.classList.contains('selected'))) {
                    await clickNesineBox(cbEl, false);
                }
            }
        }
    }

    async function injectLetterPicks(picksArray, targetSlot) {
        if (!picksArray || picksArray.length < 15) return false;
        const rows = getMatchRows();
        if (rows.length < 15) return false;

        const letterOffsets = { 'A': 0, 'B': 3, 'C': 6, 'D': 9 };
        const optToIndex = { '1': 0, 'X': 1, '0': 1, '2': 2 };
        const baseOffset = letterOffsets[targetSlot] || 0;

        for (let mIdx = 0; mIdx < 15; mIdx++) {
            const row = rows[mIdx];
            const cbs = Array.from(row.querySelectorAll('input[type="checkbox"], .checkbox, [data-choice]'));
            if (cbs.length < 12) continue;

            const rawVal = picksArray[mIdx] || '1';
            const desiredPicks = rawVal.toString().replace(/[^1X02]/g, '').split('');

            for (const opt of ['1', 'X', '2']) {
                const cbEl = cbs[baseOffset + optToIndex[opt]];
                if (!cbEl) continue;
                const shouldBeChecked = desiredPicks.includes(opt) || (opt === 'X' && desiredPicks.includes('0'));
                await clickNesineBox(cbEl, shouldBeChecked);
            }
        }
        return true;
    }

    async function injectFullSheet(sheet) {
        if (!sheet) return false;
        const letters = ['A', 'B', 'C', 'D'];
        for (const l of letters) {
            if (sheet[l] && sheet[l].length === 15) {
                await injectLetterPicks(sheet[l], l);
            } else {
                await clearLetterSlot(l);
            }
        }
        return true;
    }

    async function injectSelectedSheet() {
        if (isInjecting || !sheetsList[currentSheetIdx]) return;
        isInjecting = true;
        const s = sheetsList[currentSheetIdx];
        const success = await injectFullSheet(s);
        isInjecting = false;
        if (success) {
            alert(`✅ Kupon #${s.sheet_id || currentSheetIdx + 1} (4 Kolon / A-B-C-D) başarıyla dolduruldu!`);
        } else {
            alert('Nesine tablosu bulunamadı. Lütfen Spor Toto bülten sayfasında olduğunuzdan emin olun.');
        }
    }

    if (document.readyState === 'loading') {
        window.addEventListener('DOMContentLoaded', createInjectorWidget);
    } else {
        createInjectorWidget();
    }
})();
