import streamlit as st
import json
from state_manager import export_coupons_txt, export_coupons_csv, save_workspace_state

def render():
    st.markdown("### 💼 Kuponlarım & Nesine Aktarım İstasyonu")
    st.caption("Oynanan ve üretilen kuponları inceleyin, 40 TL'lik sayfaları arşivleyin, tek tıkla .TXT/.CSV/.JSON olarak yedekleyin.")
    
    sol = st.session_state.get("solution")
    fixtures = st.session_state.get("fixtures", [])
    
    if not sol or not isinstance(sol, dict) or (not sol.get("columns") and not sol.get("sheets")):
        st.warning("⚠️ Henüz üretilmiş geçerli bir kupon bulunmuyor. Lütfen önce Kupon Oluşturucu'dan üretim yapın.")
        if st.button("🎯 Kupon Oluşturucuya Git"):
            st.session_state["current_view"] = "🎯 Kupon Oluşturucu"
            st.rerun()
        return
        
    columns = sol.get("columns", [])
    if not columns and sol.get("sheets"):
        for s in sol["sheets"]:
            for l in ["A", "B", "C", "D"]:
                if l in s and len(s[l]) == 15:
                    columns.append(s[l])

    tot_cols = int(sol.get("total_columns") or len(columns) or (len(sol.get("sheets", [])) * 4))
    tot_cost = int(sol.get("total_cost") or (tot_cols * 10))
    tot_sheets = int(sol.get("total_sheets") or len(sol.get("sheets", [])) or ((tot_cols + 3) // 4))
    mode = sol.get("mode", "13G")

    c1, c2, c3 = st.columns(3)
    c1.metric("Paket Tutarı", f"{tot_cost:,} TL")
    c2.metric("Üretilen Kolon", f"{tot_cols:,} Adet")
    c3.metric("Nesine Kupon Sayısı", f"{tot_sheets} Sayfa (40 TL)")
    
    st.divider()
    
    col_left, col_right = st.columns([6, 4], gap="medium")
    
    with col_left:
        st.subheader("📤 Dışa Aktarım & Nesine Köprüsü")
        
        compact_cols = sol.get("compact_columns") or ["".join(c) for c in columns]
        compact_payload = json.dumps({
            "compact": True,
            "cols": compact_cols,
            "total_columns": tot_cols,
            "total_sheets": tot_sheets,
            "total_cost_tl": tot_cost
        }, separators=(',', ':'))

        std_payload = json.dumps({
            "sheets": sol.get("sheets", []),
            "total_columns": tot_cols,
            "total_sheets": tot_sheets,
            "total_cost_tl": tot_cost
        }, indent=2)

        txt_payload = export_coupons_txt(columns, mode, tot_cost)
        csv_payload = export_coupons_csv(columns, mode, tot_cost)

        tab_txt, tab_comp, tab_std = st.tabs([
            "📝 Düz Metin (15 Karakter .TXT)",
            "⚡ Nesine Köprüsü (~2 KB JSON)",
            "📄 Genişletilmiş JSON"
        ])
        with tab_txt:
            st.caption("Pano yedeklemesi ve geriye dönük analiz için her satırda 15 karakterlik dizilim:")
            st.text_area("Düz Metin (.TXT):", value=txt_payload, height=115, key="txt_plain_vault")
        with tab_comp:
            st.caption("Tampermonkey tarayıcı eklentisi için ultra hafif kompakt JSON formatı:")
            st.text_area("Kompakt Kod:", value=compact_payload, height=115, key="txt_compact_vault")
        with tab_std:
            st.caption("Klasik 40 TL A-B-C-D sayfa yapısı:")
            st.text_area("Geniş JSON:", value=std_payload, height=115, key="txt_std_vault")
        
        # 🚀 Tek Tıkla Nesine'ye Gönder Butonu (Tampermonkey Otomatik Enjeksiyon Köprüsü)
        if st.button("🚀 Tek Tıkla Nesine'ye Gönder", type="primary", use_container_width=True, help="Kuponu tarayıcı hafızasına / panoya yazar ve Nesine Spor Toto sayfasını yeni sekmede açarak Tampermonkey ile otomatik aktarır."):
            json_str = json.dumps(sol, ensure_ascii=False)
            import streamlit.components.v1 as components
            components.html(f"""
            <script>
            try {{
                localStorage.setItem("TOTO_AUTO_INJECT", {json.dumps(json_str)});
                if (window.parent && window.parent.localStorage) {{
                    window.parent.localStorage.setItem("TOTO_AUTO_INJECT", {json.dumps(json_str)});
                }}
            }} catch (e) {{}}
            try {{
                navigator.clipboard.writeText({json.dumps(json_str)});
            }} catch (e) {{}}
            window.open("https://www.nesine.com/sportoto#auto_inject=1", "_blank");
            </script>
            """, height=0)
            st.toast("⚡ Kupon tarayıcı hafızasına yazıldı ve Nesine sekmesi açıldı!", icon="🚀")

        # Tek Tıkla Fail-Safe İndirme Butonları
        c_act1, c_act2, c_act3, c_act4 = st.columns([1.3, 1.3, 1.3, 1.1])
        with c_act1:
            st.download_button(
                "📥 .TXT İndir",
                data=txt_payload,
                file_name=f"toto_{mode}_{tot_cols}kolon.txt",
                mime="text/plain",
                use_container_width=True,
                help="Her satırda 15 karakter (1X122X...)"
            )
        with c_act2:
            st.download_button(
                "📥 .CSV İndir",
                data=csv_payload,
                file_name=f"toto_{mode}_{tot_cols}kolon.csv",
                mime="text/csv",
                use_container_width=True,
                help="Excel ve veri analizi tablosu"
            )
        with c_act3:
            st.download_button(
                "📥 .JSON İndir",
                data=compact_payload,
                file_name=f"toto_{mode}_{tot_cost}TL_kompakt.json",
                mime="application/json",
                use_container_width=True,
                help="Nesine Tampermonkey için JSON"
            )
        with c_act4:
            if st.button("🗑️ Temizle", use_container_width=True, help="Kuponları sıfırlar"):
                st.session_state["solution"] = None
                save_workspace_state()
                st.rerun()

        st.caption("🛡️ **Fail-Safe Güvencesi:** Tarayıcı çerezleri silinse veya tarayıcı kapansa bile indirdiğiniz .TXT / .CSV dosyalarını haftalar sonra Canlı Takip ekranından geriye dönük başarı analizinde kullanabilirsiniz.")

    with col_right:
        st.subheader("📁 Arşive Kaydet")
        p_name = st.text_input("Kupon Paketi İsmi:", value=f"Kupon_{tot_cost}TL")
        if st.button("Kasaya Kilitle", use_container_width=True, type="primary"):
            if "saved_portfolios" not in st.session_state:
                st.session_state["saved_portfolios"] = {}
            st.session_state["saved_portfolios"][p_name] = sol
            st.success(f"'{p_name}' başarıyla arşive eklendi!")
            
        if st.session_state.get("saved_portfolios"):
            st.markdown("---")
            st.markdown("**📚 Arşivdeki Geçmiş Kuponlar:**")
            for name, item in list(st.session_state["saved_portfolios"].items()):
                c_p1, c_p2 = st.columns([8, 2])
                with c_p1:
                    i_cols = item.get('total_columns', 0)
                    i_cost = item.get('total_cost', i_cols * 10)
                    st.write(f"• **{name}** — {i_cols} Kolon ({i_cost} TL)")
                with c_p2:
                    if st.button("Sil", key=f"del_arch_{name}", use_container_width=True):
                        del st.session_state["saved_portfolios"][name]
                        st.rerun()

        import urllib.parse
        raw_bookmarklet = """(async function(){
    const sleep = ms => new Promise(r => setTimeout(r, ms));
    const dispatch = el => {
        if(!el) return;
        ['mouseover','mousedown','click','mouseup','change'].forEach(e => el.dispatchEvent(new MouseEvent(e, {bubbles:true, cancelable:true})));
    };
    function findAddBtn() {
        const els = Array.from(document.querySelectorAll('button, a, div[role="button"]'));
        const match = els.find(el => {
            const t = (el.innerText || '').toLocaleLowerCase('tr-TR').trim();
            return t.includes('sepete ekle') || t.includes('hemen oyna');
        });
        return match || document.querySelector('.btn-add-basket, #btnSaveCoupon, button[data-action="add-basket"]');
    }
    let raw = '';
    try {
        raw = await navigator.clipboard.readText();
    } catch(err) {
        raw = prompt('Panoya erisilemedi. Lutfen kupon JSON kodunu buraya yapistiriniz:');
    }
    if (!raw) return alert('Kupon verisi bulunamadi!');
    let payload;
    try {
        payload = JSON.parse(raw);
    } catch(e) {
        return alert('Panodaki veri gecerli bir kupon JSONi degil!');
    }
    let sheets = [];
    if (payload.sheets && Array.isArray(payload.sheets)) {
        sheets = payload.sheets;
    } else if (payload.compact && Array.isArray(payload.cols)) {
        const tot = Math.ceil(payload.cols.length / 4);
        for (let s = 0; s < tot; s++) {
            sheets.push({
                A: payload.cols[s*4] || [],
                B: payload.cols[s*4+1] || [],
                C: payload.cols[s*4+2] || [],
                D: payload.cols[s*4+3] || []
            });
        }
    } else if (Array.isArray(payload)) {
        const tot = Math.ceil(payload.length / 4);
        for (let s = 0; s < tot; s++) {
            sheets.push({
                A: payload[s*4] || [],
                B: payload[s*4+1] || [],
                C: payload[s*4+2] || [],
                D: payload[s*4+3] || []
            });
        }
    }
    if (sheets.length === 0) return alert('Kupon yapragi bulunamadi!');
    if (!confirm(sheets.length * 40 + ' TL tutarindaki (' + (sheets.length*4) + ' kolon) kupon Nesine sepetine yuklensin mi?')) return;
    const letters = ['A','B','C','D'];
    for (let s = 0; s < sheets.length; s++) {
        const sheet = sheets[s];
        for (let l = 0; l < letters.length; l++) {
            const char = letters[l];
            const picks = sheet[char];
            if (!picks) continue;
            for (let m = 0; m < 15; m++) {
                const pick = picks[m];
                if (!pick) continue;
                const btn = document.querySelector('[data-mno="' + (m+1) + '"][data-col="' + char + '"][data-val="' + pick + '"]') ||
                            document.querySelector('input[data-m="' + (m+1) + '"][data-c="' + char + '"][data-v="' + pick + '"]') ||
                            document.querySelector('[data-match-index="' + m + '"][data-column="' + char + '"][data-choice="' + pick + '"]');
                if (btn) {
                    if (m === 10) btn.scrollIntoView({ behavior: 'instant', block: 'center' });
                    dispatch(btn);
                    await sleep(20);
                }
            }
        }
        await sleep(350);
        if (s < sheets.length - 1) {
            const addBtn = findAddBtn();
            if (!addBtn) return alert('HATA: Sepete Ekle butonu bulunamadi! ' + (s+1) + '. yaprakta durduruldu.');
            dispatch(addBtn);
            await sleep(650);
        }
    }
    alert('✅ ' + (sheets.length * 40) + ' TL kupon basariyla sepete yuklendi!');
}})();"""

        bm_iframe_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
        background: #0f172a;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        color: #94a3b8;
        border: 1.5px dashed #0284c7;
        border-radius: 8px;
        padding: 9px 12px;
        text-align: center;
    }}
    .title {{
        font-weight: 800;
        font-size: 11.5px;
        color: #38bdf8;
        margin-bottom: 2px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 5px;
    }}
    .desc {{
        font-size: 10px;
        color: #94a3b8;
        margin-bottom: 6px;
    }}
    .lag-shield {{
        background: #090e17;
        border: 1px solid #1e293b;
        border-radius: 6px;
        padding: 5px 8px;
        margin-bottom: 6px;
        text-align: left;
    }}
    .lag-shield-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 10.5px;
        font-weight: 700;
        color: #cbd5e1;
        margin-bottom: 3px;
    }}
    .lag-badge {{
        font-family: monospace;
        font-size: 10.5px;
        color: #fbbf24;
        background: rgba(245, 158, 11, 0.15);
        border: 1px solid rgba(245, 158, 11, 0.4);
        padding: 1px 6px;
        border-radius: 4px;
        font-weight: 800;
    }}
    .slider-input {{
        width: 100%;
        height: 4px;
        background: #334155;
        border-radius: 2px;
        accent-color: #f59e0b;
        cursor: pointer;
        outline: none;
    }}
    .lag-hint {{
        font-size: 9px;
        color: #64748b;
        margin-top: 3px;
        line-height: 1.25;
    }}
    .btn-row {{
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        margin-bottom: 5px;
    }}
    .btn-drag {{
        display: inline-block;
        background: #0284c7;
        color: #ffffff !important;
        text-decoration: none !important;
        font-weight: 700;
        font-size: 11px;
        padding: 5px 12px;
        border-radius: 5px;
        border: 1px solid #38bdf8;
        box-shadow: 0 2px 6px rgba(2, 132, 199, 0.35);
        cursor: grab;
        user-select: none;
    }}
    .btn-drag:hover {{
        background: #0369a1;
    }}
    .btn-copy {{
        background: #1e293b;
        color: #e2e8f0;
        border: 1px solid #475569;
        font-size: 10.5px;
        font-weight: 600;
        padding: 5px 9px;
        border-radius: 5px;
        cursor: pointer;
    }}
    .btn-copy:hover {{
        background: #334155;
    }}
    .hint {{
        font-size: 9px;
        color: #64748b;
        line-height: 1.25;
    }}
</style>
</head>
<body>
    <div class="title">📌 Eklentisiz Çözüm: Yer İmi Butonu (Bookmarklet)</div>
    <div class="desc">Tampermonkey kullanmıyorsanız butonu <b>Yer İmleri Çubuğuna</b> sürükleyin:</div>

    <div class="lag-shield">
        <div class="lag-shield-header">
            <span>⚡ Ağ Gecikmesi (Lag Shield):</span>
            <span class="lag-badge" id="delay-val">750 ms</span>
        </div>
        <input type="range" class="slider-input" id="delay-slider" min="650" max="1200" step="25" value="750" oninput="updateDelay(this.value)">
        <div class="lag-hint">💡 <i>Yavaş internet veya yoğun saatlerde sepetin kaçırılmaması için gecikmeyi artırabilirsiniz.</i></div>
    </div>

    <div class="btn-row">
        <a class="btn-drag" id="btn-drag" href="#" draggable="true" onclick="alert('Bu butona doğrudan tıklamayın!\\n\\nFareyle tutup tarayıcınızın üstündeki Yer İmleri (Favoriler) çubuğuna sürükleyip bırakın.'); return false;">
            📌 Nesine'ye Aktar
        </a>
        <button class="btn-copy" onclick="copyCode()">📋 Kodu Kopyala</button>
    </div>
    <div class="hint">
        <b>3 Adımda:</b> 1. Butonu Yer İmlerine sürükle &nbsp;•&nbsp; 2. Kuponu panoya kopyala &nbsp;•&nbsp; 3. Nesine sekmesinde yer imine tıkla!
    </div>
    <script>
    function buildScript(delay) {{
        return `javascript:(async function(){{const NETWORK_DELAY=${{delay}};const sleep=ms=>new Promise(r=>setTimeout(r,ms));const dispatch=el=>{{if(!el)return;['mouseover','mousedown','click','mouseup','change'].forEach(e=>el.dispatchEvent(new MouseEvent(e,{{bubbles:true,cancelable:true}})));}};function findAddBtn(){{const els=Array.from(document.querySelectorAll('button,a,div[role="button"]'));const match=els.find(el=>{{const t=(el.innerText||'').toLocaleLowerCase('tr-TR').trim();return t.includes('sepete ekle')||t.includes('hemen oyna');}});return match||document.querySelector('.btn-add-basket,#btnSaveCoupon,button[data-action="add-basket"]');}}let raw='';try{{raw=await navigator.clipboard.readText();}}catch(err){{raw=prompt('Panoya erisilemedi. Lutfen kupon JSON kodunu buraya yapistiriniz:');}}if(!raw)return alert('Kupon verisi bulunamadi!');let payload;try{{payload=JSON.parse(raw);}}catch(e){{return alert('Panodaki veri gecerli bir kupon JSONi degil!');}}let sheets=[];if(payload.sheets&&Array.isArray(payload.sheets)){{sheets=payload.sheets;}}else if(payload.compact&&Array.isArray(payload.cols)){{const tot=Math.ceil(payload.cols.length/4);for(let s=0;s<tot;s++){{sheets.push({{A:payload.cols[s*4]||[],B:payload.cols[s*4+1]||[],C:payload.cols[s*4+2]||[],D:payload.cols[s*4+3]||[]}});}}}}else if(Array.isArray(payload)){{const tot=Math.ceil(payload.length/4);for(let s=0;s<tot;s++){{sheets.push({{A:payload[s*4]||[],B:payload[s*4+1]||[],C:payload[s*4+2]||[],D:payload[s*4+3]||[]}});}}}}if(sheets.length===0)return alert('Kupon yapragi bulunamadi!');if(!confirm(sheets.length*40+' TL ('+(sheets.length*4)+' kolon) Nesine sepetine yuklensin mi?'))return;const letters=['A','B','C','D'];for(let s=0;s<sheets.length;s++){{const sheet=sheets[s];for(let l=0;l<letters.length;l++){{const char=letters[l];const picks=sheet[char];if(!picks)continue;for(let m=0;m<15;m++){{const pick=picks[m];if(!pick)continue;const btn=document.querySelector('[data-mno="'+(m+1)+'"][data-col="'+char+'"][data-val="'+pick+'"]')||document.querySelector('input[data-m="'+(m+1)+'"][data-c="'+char+'"][data-v="'+pick+'"]')||document.querySelector('[data-match-index="'+m+'"][data-column="'+char+'"][data-choice="'+pick+'"]');if(btn){{if(m===10)btn.scrollIntoView({{behavior:'instant',block:'center'}});dispatch(btn);await sleep(20);}}}}}}await sleep(Math.floor(NETWORK_DELAY/2));if(s<sheets.length-1){{const addBtn=findAddBtn();if(!addBtn)return alert('HATA: Sepete Ekle butonu bulunamadi! '+(s+1)+'. yaprakta durduruldu.');dispatch(addBtn);await sleep(NETWORK_DELAY);}}}}alert('✅ '+(sheets.length*40)+' TL kupon basariyla sepete yuklendi!');}})();`;
    }}

    let currentDelay = 750;
    function updateDelay(val) {{
        currentDelay = val;
        document.getElementById('delay-val').innerText = val + ' ms';
        const code = buildScript(val);
        document.getElementById('btn-drag').setAttribute('href', encodeURI(code));
    }}

    updateDelay(750);

    function copyCode() {{
        const code = buildScript(currentDelay);
        if (navigator.clipboard && navigator.clipboard.writeText) {{
            navigator.clipboard.writeText(code).then(() => {{
                alert('✅ Yer imi kodu (' + currentDelay + ' ms gecikmeli) panoya kopyalandı!\\n\\nTarayıcınızın Yer İmleri çubuğuna sağ tıklayıp Yeni Yer İmi ekleyin ve Adres (URL) kısmına yapıştırın.');
            }}).catch(() => {{
                prompt('Kodu kopyalamak için Ctrl+C yapın:', code);
            }});
        }} else {{
            prompt('Kodu kopyalamak için Ctrl+C yapın:', code);
        }}
    }}
    </script>
</body>
</html>"""
        import streamlit.components.v1 as components
        components.html(bm_iframe_html, height=160)

    # 40 TL Sheet Kupon Görsel Tablosu
    if sol.get("sheets") and fixtures:
        st.divider()
        st.subheader("📋 40 TL Kupon Sayfaları Önizlemesi")
        sheets = sol["sheets"]
        total_s = len(sheets)

        sel_idx = st.selectbox(
            "Görüntülenecek Sayfayı Seçin:",
            options=list(range(total_s)),
            format_func=lambda idx: f"Sayfa #{idx+1} / {total_s} (4 Kolon - 40 TL)"
        )

        cur_sheet = sheets[sel_idx]
        lines = []
        lines.append('<div class="sheet-table-wrap">')
        lines.append('<table class="sheet-table">')
        lines.append('<thead><tr>')
        lines.append('<th style="width: 48px;">No</th>')
        lines.append('<th style="text-align: left; padding-left: 14px;">Karşılaşma</th>')
        lines.append('<th style="width: 80px; color: #38bdf8;">Harf A</th>')
        lines.append('<th style="width: 80px; color: #38bdf8;">Harf B</th>')
        lines.append('<th style="width: 80px; color: #38bdf8;">Harf C</th>')
        lines.append('<th style="width: 80px; color: #38bdf8;">Harf D</th>')
        lines.append('</tr></thead><tbody>')

        for m in range(15):
            fix = fixtures[m] if m < len(fixtures) else {}
            h = fix.get("home", f"Ev {m+1}")
            a = fix.get("away", f"Dep {m+1}")
            pA = cur_sheet.get("A", ["-"] * 15)[m] if "A" in cur_sheet and len(cur_sheet["A"]) > m else "-"
            pB = cur_sheet.get("B", ["-"] * 15)[m] if "B" in cur_sheet and len(cur_sheet["B"]) > m else "-"
            pC = cur_sheet.get("C", ["-"] * 15)[m] if "C" in cur_sheet and len(cur_sheet["C"]) > m else "-"
            pD = cur_sheet.get("D", ["-"] * 15)[m] if "D" in cur_sheet and len(cur_sheet["D"]) > m else "-"

            def pill(val):
                cls = 'sheet-pill-1' if val == '1' else ('sheet-pill-x' if val in ['X', '0'] else ('sheet-pill-2' if val == '2' else ''))
                return f'<div class="sheet-pill {cls}">{val}</div>'

            lines.append('<tr>')
            lines.append(f'<td style="font-weight: 700; color: #94a3b8;">{m+1:02d}</td>')
            lines.append(f'<td style="text-align: left; padding-left: 14px; font-weight: 600; font-size: 11.5px; color: #f1f5f9;">{h} – {a}</td>')
            lines.append(f'<td>{pill(pA)}</td>')
            lines.append(f'<td>{pill(pB)}</td>')
            lines.append(f'<td>{pill(pC)}</td>')
            lines.append(f'<td>{pill(pD)}</td>')
            lines.append('</tr>')

        lines.append('</tbody></table></div>')
        st.markdown("\n".join(lines), unsafe_allow_html=True)
