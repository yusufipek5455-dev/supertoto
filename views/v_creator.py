import streamlit as st
import numpy as np
import math
from core_engine import run_syndicate_solver, compute_theoretical_baseline_estimates
from state_manager import save_workspace_state, export_coupons_txt, export_coupons_csv

def render():
    fixtures = st.session_state["fixtures"]
    picks = st.session_state.get("user_picks")
    if not isinstance(picks, dict):
        picks = {}
    for i in range(15):
        if i not in picks:
            picks[i] = ['1']
    st.session_state["user_picks"] = picks
    
    if "selected_mode" not in st.session_state:
        st.session_state["selected_mode"] = "13G"
    selected_mode = st.session_state["selected_mode"]
    
    # Scoped Pixel-Perfect Responsive CSS
    st.html("""
    <style>
        .block-container {
            padding-top: 0.35rem !important;
            padding-bottom: 0.5rem !important;
            max-width: 99% !important;
        }
        div[data-testid="stElementContainer"] {
            margin: 0 !important;
            padding: 0 !important;
        }
        div[data-testid="stVerticalBlock"] {
            gap: 2px !important;
        }
        div[data-testid="stHorizontalBlock"] {
            gap: 3px !important;
            margin-bottom: 2px !important;
            align-items: center !important;
        }
        div[data-testid="column"] {
            min-width: 0 !important;
            padding: 0 1px !important;
        }
        
        /* 15 Maç Tercih Matrisi Satırları */
        .compact-match-row {
            display: flex;
            align-items: center;
            justify-content: flex-start;
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 4px;
            padding: 0 8px;
            height: 26px;
            font-size: 11.5px;
            color: #f1f5f9;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .compact-match-row .m-title {
            font-weight: 600;
            color: #f8fafc;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .compact-match-num {
            background: #0f172a;
            border: 1px solid #334155;
            color: #38bdf8;
            font-family: monospace;
            font-weight: 800;
            font-size: 11px;
            text-align: center;
            border-radius: 4px;
            height: 26px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        /* Sol Kolondaki Matris Butonları (%78, %14 X, %8) */
        div[data-testid="column"]:first-child div.stButton > button {
            padding: 0 2px !important;
            min-height: 26px !important;
            height: 26px !important;
            max-height: 26px !important;
            font-size: 11px !important;
            font-weight: 700 !important;
            line-height: 24px !important;
            border-radius: 4px !important;
            margin: 0 !important;
            white-space: nowrap !important;
        }

        /* İstatistik Sayaç Kutuları: Tek / Çift / Kapalı */
        .stat-box {
            background: #0f172a;
            border: 1px solid #334155;
            border-radius: 5px;
            height: 26px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 11px;
            font-weight: 700;
            color: #cbd5e1;
        }

        /* Sağ Kolon: Hızlı Eylem Butonları */
        div:has(> .is-quick-row) + div button {
            background: #2563eb !important;
            color: #ffffff !important;
            font-weight: 700 !important;
            font-size: 11px !important;
            height: 26px !important;
            min-height: 26px !important;
            max-height: 26px !important;
            border-radius: 5px !important;
            border: none !important;
            padding: 0 4px !important;
            margin: 0 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            transition: all 0.15s ease !important;
        }
        div:has(> .is-quick-row) + div button:hover {
            background: #1d4ed8 !important;
            box-shadow: 0 0 8px rgba(37, 99, 235, 0.4) !important;
        }

        /* 2x2 Garanti Kartları */
        div[class*="st-key-btn_mode_"] button {
            height: 48px !important;
            min-height: 48px !important;
            max-height: 48px !important;
            border-radius: 6px !important;
            padding: 2px 6px !important;
            border: 1.5px solid #334155 !important;
            background: #1e293b !important;
            transition: all 0.15s ease !important;
            margin: 0 !important;
        }
        div[class*="st-key-btn_mode_"] button:hover {
            border-color: #38bdf8 !important;
            background: #24344d !important;
        }
        div:has(> .is-guarantee-active) + div button {
            background: #09141f !important;
            border: 2px solid #10b981 !important;
            box-shadow: 0 0 8px rgba(16, 185, 129, 0.35) !important;
        }
        div[class*="st-key-btn_mode_"] button p {
            margin: 0 !important;
            padding: 0 !important;
            line-height: 1.25 !important;
            text-align: left !important;
            white-space: nowrap !important;
            font-size: 10px !important;
            letter-spacing: -0.2px !important;
            color: #f8fafc !important;
        }
        div:has(> .is-guarantee-active) + div button p {
            color: #34d399 !important;
        }

        /* 3'lü İstatistik Kartları */
        .stat-card-refactor {
            background: #0f172a;
            border: 1px solid #1e293b;
            border-radius: 6px;
            padding: 4px 6px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            height: 48px;
            font-family: monospace;
            box-sizing: border-box;
        }
        .stat-card-refactor .sc-title {
            font-size: 8px;
            color: #94a3b8;
            line-height: 1.15;
            white-space: normal;
            height: 18px;
            overflow: hidden;
        }
        .stat-card-refactor .sc-val {
            font-size: 11.5px;
            font-weight: 800;
            color: #f8fafc;
            line-height: 1.2;
        }
        .stat-card-refactor .sc-sub {
            font-size: 8px;
            color: #64748b;
            line-height: 1;
        }

        /* İki Büyük Eylem Butonu */
        div[class*="st-key-btn_exec_"] button {
            border-radius: 8px !important;
            padding: 5px 10px !important;
            min-height: 48px !important;
            height: auto !important;
            text-align: left !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: center !important;
            transition: all 0.15s ease !important;
            margin: 0 !important;
            white-space: normal !important;
        }
        div[class*="st-key-btn_exec_"] button div[data-testid="stMarkdownContainer"] {
            width: 100% !important;
            white-space: normal !important;
        }
        div[class*="st-key-btn_exec_"] button div[data-testid="stMarkdownContainer"] p {
            white-space: normal !important;
            overflow: visible !important;
            text-overflow: unset !important;
        }
        div[class*="st-key-btn_exec_ekonomik"] button {
            background: #0b1b15 !important;
            border: 1.5px solid rgba(16, 185, 129, 0.7) !important;
        }
        div[class*="st-key-btn_exec_ekonomik"] button:hover {
            background: #0f2820 !important;
            border-color: #10b981 !important;
            box-shadow: 0 0 10px rgba(16, 185, 129, 0.3) !important;
        }
        div[class*="st-key-btn_exec_akilli"] button {
            background: #0d1829 !important;
            border: 1.5px solid rgba(56, 189, 248, 0.7) !important;
        }
        div[class*="st-key-btn_exec_akilli"] button:hover {
            background: #13233c !important;
            border-color: #38bdf8 !important;
            box-shadow: 0 0 10px rgba(56, 189, 248, 0.3) !important;
        }
        div[class*="st-key-btn_exec_"] button p {
            margin: 0 !important;
            padding: 0 !important;
            text-align: left !important;
            line-height: 1.25 !important;
        }
        div[class*="st-key-btn_exec_ekonomik"] button p:first-child {
            font-size: 11.5px !important;
            font-weight: 800 !important;
            color: #34d399 !important;
        }
        div[class*="st-key-btn_exec_akilli"] button p:first-child {
            font-size: 11.5px !important;
            font-weight: 800 !important;
            color: #38bdf8 !important;
        }
        div[class*="st-key-btn_exec_"] button p:last-child {
            font-size: 9px !important;
            color: #94a3b8 !important;
            margin-top: 1px !important;
        }

        /* Kupon Kasasına Git Butonu */
        div:has(> .is-goto-btn) + div button {
            height: 30px !important;
            min-height: 30px !important;
            font-size: 11.5px !important;
            font-weight: 700 !important;
            margin-top: 2px !important;
        }
    </style>
    """)
    
    # Dinamik Teorik Kalkan Tahminleri ve Kısıtlı Hamming Küre Hacimleri
    est = compute_theoretical_baseline_estimates(picks)
    raw_combinations = est["raw_combinations"]
    m_15 = est["modes"]["15G"]
    m_14 = est["modes"]["14G"]
    m_13 = est["modes"]["13G"]
    m_12 = est["modes"]["12G"]

    cnt_15, cost_15 = m_15["columns"], m_15["cost_tl"]
    cnt_14, cost_14 = m_14["columns"], m_14["cost_tl"]
    cnt_13, cost_13 = m_13["columns"], m_13["cost_tl"]
    cnt_12, cost_12 = m_12["columns"], m_12["cost_tl"]

    chance_15_str = "%100"
    chance_14_str = f"%{m_14.get('chance_pct', 0.0):.1f} 15 Şansı"
    chance_13_str = f"%{m_13.get('chance_pct', 0.0):.1f} 14-15 Şansı"
    chance_12_str = f"%{m_12.get('chance_pct', 0.0):.1f} 13-15 Şansı"
    sol = st.session_state.get("solution")

    col_matrix, col_controls = st.columns([5.2, 4.8], gap="medium")
    
    with col_matrix:
        c_th1, c_th2 = st.columns([6, 4])
        with c_th1:
            st.html("<div style='font-size:12.5px; font-weight:800; color:#38bdf8; padding:1px 0;'>📋 15 MAÇ TERCİH MATRİSİ</div>")
        with c_th2:
            st.html(f"<div style='text-align:right; font-size:11px; font-weight:700; color:#94a3b8; padding:1px 0;'>Ham Havuz: <b style='color:#f8fafc;'>{raw_combinations:,} Kolon</b> ({raw_combinations*10:,} TL)</div>")

        for i in range(15):
            fix = fixtures[i]
            no = fix["no"]
            odds = fix.get("odds", [33.3, 33.3, 33.4])
            r1, rx, r2 = odds[0], odds[1], odds[2]
            curr_picks = list(picks.get(i, []))

            r_cols = st.columns([0.45, 3.75, 1.3, 1.3, 1.3], gap="small")
            c_no, c_name, c_1, c_x, c_2 = r_cols[0], r_cols[1], r_cols[2], r_cols[3], r_cols[4]

            with c_no:
                st.html(f'<div class="compact-match-num">{no:02d}</div>')

            with c_name:
                m_title = f"{fix['home']} - {fix['away']}"
                st.html(f'<div class="compact-match-row"><span class="m-title" title="{m_title}">{m_title}</span></div>')

            with c_1:
                is_1 = '1' in curr_picks
                dot_1 = "• " if r1 >= 60.0 else ""
                lbl_1 = f"{dot_1}%{r1:.0f}"
                if st.button(lbl_1, key=f"p1_{no}", type="primary" if is_1 else "secondary", use_container_width=True):
                    if is_1:
                        if len(curr_picks) > 1:
                            picks[i] = [p for p in curr_picks if p != '1']
                        else:
                            st.toast("⚠️ En az bir tercih seçili kalmalıdır!", icon="🛡️")
                    else:
                        picks[i] = curr_picks + ['1']
                    save_workspace_state()
                    st.rerun()
                    
            with c_x:
                is_x = 'X' in curr_picks
                dot_x = "• " if rx >= 60.0 else ""
                lbl_x = f"{dot_x}%{rx:.0f} X"
                if st.button(lbl_x, key=f"px_{no}", type="primary" if is_x else "secondary", use_container_width=True):
                    if is_x:
                        if len(curr_picks) > 1:
                            picks[i] = [p for p in curr_picks if p != 'X']
                        else:
                            st.toast("⚠️ En az bir tercih seçili kalmalıdır!", icon="🛡️")
                    else:
                        picks[i] = curr_picks + ['X']
                    save_workspace_state()
                    st.rerun()
                    
            with c_2:
                is_2 = '2' in curr_picks
                dot_2 = "• " if r2 >= 60.0 else ""
                lbl_2 = f"{dot_2}%{r2:.0f}"
                if st.button(lbl_2, key=f"p2_{no}", type="primary" if is_2 else "secondary", use_container_width=True):
                    if is_2:
                        if len(curr_picks) > 1:
                            picks[i] = [p for p in curr_picks if p != '2']
                        else:
                            st.toast("⚠️ En az bir tercih seçili kalmalıdır!", icon="🛡️")
                    else:
                        picks[i] = curr_picks + ['2']
                    save_workspace_state()
                    st.rerun()

    with col_controls:
        # 1. Kayıtlı Tercihlerim Dropdown
        st.selectbox(
            "Kayıtlı Tercihlerim",
            options=["Kayıtlı Tercihlerim", "Varsayılan Tercihler (Canlı)", "Favori Ağırlıklı Kurgu"],
            index=0,
            label_visibility="collapsed"
        )
        
        # 2. İstatistik Sayaç Kutuları
        n_tek = sum(1 for p in picks.values() if len(p) == 1)
        n_cift = sum(1 for p in picks.values() if len(p) == 2)
        n_kapali = sum(1 for p in picks.values() if len(p) == 3)

        c_st1, c_st2, c_st3 = st.columns(3)
        with c_st1:
            st.html(f'<div class="stat-box">{n_tek} Tek</div>')
        with c_st2:
            st.html(f'<div class="stat-box">{n_cift} Çift</div>')
        with c_st3:
            st.html(f'<div class="stat-box">{n_kapali} Kapalı</div>')

        # 3. 2x2 Hızlı Kurgu Filtre Butonları
        st.html('<span class="is-quick-row"></span>')
        b_q1, b_q2 = st.columns(2)
        with b_q1:
            if st.button("Tümü Çifte", key="btn_q_cifte", use_container_width=True, help="Tüm maçları en yüksek 2 ihtimale (çifte) ayarlar"):
                new_picks = {}
                for idx_m in range(15):
                    odds = fixtures[idx_m].get("odds", [33.3, 33.3, 33.4])
                    if odds[0] >= odds[2]:
                        new_picks[idx_m] = ['1', 'X']
                    else:
                        new_picks[idx_m] = ['X', '2']
                st.session_state["user_picks"] = new_picks
                save_workspace_state()
                st.toast("Tüm maçlar çifte tercihlere ayarlandı", icon="⚡")
                st.rerun()
        with b_q2:
            if st.button("Tümü Kapalı", key="btn_q_kapali", use_container_width=True, help="Tüm 15 maçı 1-X-2 kapatır"):
                st.session_state["user_picks"] = {i: ['1', 'X', '2'] for i in range(15)}
                save_workspace_state()
                st.toast("Tüm maçlar 1-X-2 kapatıldı", icon="🛡️")
                st.rerun()

        st.html('<span class="is-quick-row"></span>')
        b_q3, b_q4 = st.columns(2)
        with b_q3:
            if st.button("Bankoları Koru", key="btn_q_banko", use_container_width=True, help="Mevcut tekleri (banko) korur, diğer maçları çifte/kapalı yapar"):
                new_picks = {}
                for idx_m in range(15):
                    curr = picks.get(idx_m, ['1'])
                    if len(curr) == 1:
                        new_picks[idx_m] = list(curr)
                    else:
                        new_picks[idx_m] = ['1', 'X', '2']
                st.session_state["user_picks"] = new_picks
                save_workspace_state()
                st.toast("Bankolar korundu, diğer maçlar kapatıldı", icon="👑")
                st.rerun()
        with b_q4:
            if st.button("🔄 Sıfırla", key="btn_q_reset", use_container_width=True, help="Tüm 15 maçı varsayılan [1] tercihine sıfırlar"):
                st.session_state["user_picks"] = {i: ['1'] for i in range(15)}
                save_workspace_state()
                st.toast("Tüm maçlar varsayılana sıfırlandı", icon="🔄")
                st.rerun()

        # 4. 2x2 Garanti Seviyesi Kartları (Kolon Sayısı + TL Fiyatı + Yüzde)
        cost_15 = cnt_15 * 10
        cost_14 = cnt_14 * 10
        cost_13 = cnt_13 * 10
        cost_12 = cnt_12 * 10

        lbl_15 = f"**15G**  **{cnt_15:,} Kolon** ({cost_15:,} TL)  {chance_15_str}"
        lbl_14 = f"**14G**  **{cnt_14:,} Kolon** ({cost_14:,} TL)  {chance_14_str}"
        lbl_13 = f"**13G**  **{cnt_13:,} Kolon** ({cost_13:,} TL)  {chance_13_str}"
        lbl_12 = f"**12G**  **{cnt_12:,} Kolon** ({cost_12:,} TL)  {chance_12_str}"

        help_15 = "15 Garanti: 0 hata toleransı. %100 tam kapsama."
        help_14 = f"14 Garanti: 1 hata toleransı. 15 Gelme Şansı: %{m_14.get('chance_pct', 0.0):.1f}"
        help_13 = f"13 Garanti: 2 hata toleransı. 14 ve 15 Gelme Şansı: %{m_13.get('chance_pct', 0.0):.1f} (15 Şansı: %{m_13.get('hit_15_pct', 0.0):.1f})"
        help_12 = f"12 Garanti: 3 hata toleransı. 13, 14 ve 15 Gelme Şansı: %{m_12.get('chance_pct', 0.0):.1f} (15 Şansı: %{m_12.get('hit_15_pct', 0.0):.1f})"

        g_row1_c1, g_row1_c2 = st.columns(2)
        with g_row1_c1:
            is_15 = (selected_mode == "15G")
            st.html(f'<span class="is-guarantee-row {"is-guarantee-active" if is_15 else ""}"></span>')
            if st.button(lbl_15, key="btn_mode_15G", help=help_15, use_container_width=True):
                st.session_state["selected_mode"] = "15G"
                save_workspace_state()
                st.rerun()

        with g_row1_c2:
            is_14 = (selected_mode == "14G")
            st.html(f'<span class="is-guarantee-row {"is-guarantee-active" if is_14 else ""}"></span>')
            if st.button(lbl_14, key="btn_mode_14G", help=help_14, use_container_width=True):
                st.session_state["selected_mode"] = "14G"
                save_workspace_state()
                st.rerun()

        g_row2_c1, g_row2_c2 = st.columns(2)
        with g_row2_c1:
            is_13 = (selected_mode == "13G")
            st.html(f'<span class="is-guarantee-row {"is-guarantee-active" if is_13 else ""}"></span>')
            if st.button(lbl_13, key="btn_mode_13G", help=help_13, use_container_width=True):
                st.session_state["selected_mode"] = "13G"
                save_workspace_state()
                st.rerun()

        with g_row2_c2:
            is_12 = (selected_mode == "12G")
            st.html(f'<span class="is-guarantee-row {"is-guarantee-active" if is_12 else ""}"></span>')
            if st.button(lbl_12, key="btn_mode_12G", help=help_12, use_container_width=True):
                st.session_state["selected_mode"] = "12G"
                save_workspace_state()
                st.rerun()

        # Aktif Seçim İçin Kolon ve Tutar Bilgisi
        active_cnt = cnt_13 if selected_mode == "13G" else (cnt_14 if selected_mode == "14G" else (cnt_15 if selected_mode == "15G" else cnt_12))
        active_cost = active_cnt * 10
        active_sheets = (active_cnt + 3) // 4

        # 5. 3'lü İstatistik Kartları (Normal Kupon Bedeli, Sistem Bedeli, Nesine Kupon Sayısı)
        sol_existing = st.session_state.get("solution")
        if sol_existing and isinstance(sol_existing, dict) and sol_existing.get("total_columns"):
            display_cols = sol_existing.get("total_columns", active_cnt)
            display_cost = sol_existing.get("total_cost", active_cost)
            display_sheets = sol_existing.get("total_sheets", (display_cols + 3) // 4)
        else:
            display_cols = active_cnt
            display_cost = active_cost
            display_sheets = active_sheets

        c_stat1, c_stat2, c_stat3 = st.columns(3)
        with c_stat1:
            st.html(f"""
            <div class="stat-card-refactor">
                <div class="sc-title">Normal Kupon Bedeli (15 Garantili)</div>
                <div class="sc-val">{(raw_combinations * 10):,} TL</div>
                <div class="sc-sub">({raw_combinations:,} Kolon)</div>
            </div>
            """)
        with c_stat2:
            st.html(f"""
            <div class="stat-card-refactor">
                <div class="sc-title">Sistem Bedeli</div>
                <div class="sc-val" style="color:#34d399;">{display_cost:,} TL</div>
                <div class="sc-sub">({display_cols:,} Kolon)</div>
            </div>
            """)
        with c_stat3:
            st.html(f"""
            <div class="stat-card-refactor">
                <div class="sc-title">Nesine Kupon Sayısı</div>
                <div class="sc-val" style="color:#38bdf8;">{display_sheets} Kupon</div>
                <div class="sc-sub">(4'er Kolon)</div>
            </div>
            """)

        # 6. İki Büyük Eylem Butonu (Ekonomik vs Akıllı Sürpriz Avcısı)
        is_13 = (selected_mode == "13G")
        btn1_title = "🛡️ Ekonomik 13 Garantili" if is_13 else f"🛡️ Ekonomik {selected_mode} Garantili"
        btn1_desc = "Sadece 13 garantisini sağlayan en ucuz ve en düşük kolonlu sistem. Fazladan kolon atmaz." if is_13 else f"Sadece {selected_mode} garantisini sağlayan en ucuz ve en düşük kolonlu sistem. Fazladan kolon atmaz."

        btn2_title = "🚀 Akıllı 13G + Sürpriz Avcısı" if is_13 else f"🚀 Akıllı {selected_mode} + Sürpriz Avcısı"
        btn2_desc = "13 garantisinin üzerine, yapay zekanın bulduğu en mantıklı ve en çok ikramiye verecek sürpriz kolonları otonom (otomatik) olarak ekler." if is_13 else f"{selected_mode} garantisinin üzerine, yapay zekanın bulduğu en mantıklı ve en çok ikramiye verecek sürpriz kolonları otonom (otomatik) olarak ekler."

        # Button 1: Ekonomik
        btn1_lbl = f"**{btn1_title}**  ({active_cnt:,} Kolon / {active_cost:,} TL)\n\n{btn1_desc}"
        if st.button(btn1_lbl, key="btn_exec_ekonomik", use_container_width=True):
            empty_matches = [i + 1 for i in range(15) if not picks.get(i)]
            if empty_matches:
                st.error(f"⚠️ Eksik maçlar için en az bir tercih yapın: M{', M'.join(map(str, empty_matches))}")
            else:
                with st.spinner(f"{selected_mode} Ekonomik Kupon Hesaplanıyor..."):
                    sol = run_syndicate_solver(
                        user_picks=picks,
                        fixtures=fixtures,
                        mode=selected_mode,
                        solver_mode="base_only",
                        booster_cols=0,
                        target_cols=active_cnt
                    )
                    st.session_state["solution"] = sol
                    st.session_state["selected_sheet_idx"] = 0
                    from live_tracker import save_active_portfolio
                    save_active_portfolio(sol)
                    save_workspace_state()
                    st.toast("Ekonomik sistem kuponu oluşturuldu (Minimum maliyet).", icon="🛡️")
                    st.rerun()

        # Button 2: Akıllı + Sürpriz Avcısı
        btn2_lbl = f"**{btn2_title}**\n\n{btn2_desc}"
        if st.button(btn2_lbl, key="btn_exec_akilli", use_container_width=True):
            empty_matches = [i + 1 for i in range(15) if not picks.get(i)]
            if empty_matches:
                st.error(f"⚠️ Eksik maçlar için en az bir tercih yapın: M{', M'.join(map(str, empty_matches))}")
            else:
                with st.spinner(f"{selected_mode} Akıllı Sürpriz Kuponu Hesaplanıyor..."):
                    sol = run_syndicate_solver(
                        user_picks=picks,
                        fixtures=fixtures,
                        mode=selected_mode,
                        solver_mode="auto_boost",
                        booster_cols=None,
                        target_cols=None
                    )
                    st.session_state["solution"] = sol
                    st.session_state["selected_sheet_idx"] = 0
                    from live_tracker import save_active_portfolio
                    save_active_portfolio(sol)
                    save_workspace_state()
                    st.toast("Yapay zeka bülteni analiz edip en kârlı ekstra kolonları kupona ekledi.", icon="🚀")
                    st.rerun()

        # Üretilen Kupon Özeti Kartı
        sol = st.session_state.get("solution")
        if sol and isinstance(sol, dict) and (sol.get("columns") or sol.get("sheets")):
            tot_cost = sol.get("total_cost", sol.get("total_columns", 0) * 10)
            tot_sheets = sol.get("total_sheets", len(sol.get("sheets", [])))
            tot_cols = sol.get("total_columns", len(sol.get("columns", [])))
            cov_pct = sol.get("coverage_pct", 100.0)
            is_full = sol.get("is_full_coverage", True)
            min_req = sol.get("min_cols_for_100_pct", tot_cols)
            
            columns = sol.get("columns", [])
            if not columns and sol.get("sheets"):
                for s in sol["sheets"]:
                    for l in ["A", "B", "C", "D"]:
                        if l in s and len(s[l]) == 15:
                            columns.append(s[l])

            if not is_full or cov_pct < 99.9:
                coverage_badge_html = f"""
                <div style="background: rgba(245, 158, 11, 0.14); border: 1.5px solid #f59e0b; border-radius: 5px; padding: 4px 8px; margin-top: 4px; font-size: 11px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="color:#fbbf24; font-weight:800;">
                            ⚠️ {selected_mode} Kapsama Oranı: %{cov_pct:.1f}
                        </span>
                        <span style="color:#cbd5e1; font-weight:700;">
                            (%100 Kalkan İçin Minimum <b style="color:#38bdf8;">{min_req} Kolon</b> Gerekli)
                        </span>
                    </div>
                    <div style="color:#94a3b8; font-size:10px; margin-top:2px;">
                        Belirlenen bütçe ({tot_cols} Kolon) havuzun tamamını örtmeye yetmedi. Havuzun %{cov_pct:.1f}'lik kısmı {selected_mode} kalkanı altındadır.
                    </div>
                </div>
                """
            else:
                coverage_badge_html = f"""
                <div style="background: rgba(16, 185, 129, 0.12); border: 1px solid #10b981; border-radius: 5px; padding: 3px 8px; margin-top: 4px; display:flex; justify-content:space-between; align-items:center; font-size: 11px;">
                    <span style="color:#34d399; font-weight:800;">
                        🛡️ %100 {selected_mode} Matematiksel Kalkan Aktif
                    </span>
                    <span style="color:#94a3b8; font-size:10px;">
                        Tüm {raw_combinations:,} senaryo kalkan güvencesinde
                    </span>
                </div>
                """

            sol_strat = sol.get("solver_mode", "auto_boost")
            base_cnt = sol.get("baseline_columns", tot_cols)
            boost_cnt = sol.get("booster_columns", 0)
            strat_label = "Ekonomik" if sol_strat in ("pure", "base_only") else f"Akıllı + Sürpriz (+{boost_cnt} Kolon)"

            st.html(f"""
            <div style="background: #0f172a; border: 1px solid #0284c7; border-radius: 5px; padding: 4px 10px; margin-top: 4px; display: flex; justify-content: space-between; align-items: center;">
                <div style="font-size: 11.5px; font-weight: 800; color: #38bdf8;">
                    🎯 Üretilen Kupon: {tot_cols} Kolon <span style="font-size:10px; color:#34d399; font-weight:700;">({strat_label})</span>
                </div>
                <div style="font-size: 11px; color: #94a3b8;">
                    Sistem Bedeli: <b style="color:#f8fafc;">{tot_cost:,} TL</b> ({tot_sheets} Kupon)
                </div>
            </div>
            {coverage_badge_html}
            """)
            
            st.html('<span class="is-goto-btn"></span>')
            c_d1, c_d2, c_d3, c_d4 = st.columns([0.9, 0.9, 1.5, 1.1])
            with c_d1:
                txt_data = export_coupons_txt(columns, selected_mode, tot_cost)
                st.download_button(
                    "📥 .TXT İndir",
                    data=txt_data,
                    file_name=f"toto_{selected_mode}_{tot_cols}kolon.txt",
                    mime="text/plain",
                    use_container_width=True,
                    help="Tek tıkla 15 karakterlik düz metin dökümü (1X122X...)"
                )
            with c_d2:
                csv_data = export_coupons_csv(columns, selected_mode, tot_cost)
                st.download_button(
                    "📥 .CSV İndir",
                    data=csv_data,
                    file_name=f"toto_{selected_mode}_{tot_cols}kolon.csv",
                    mime="text/csv",
                    use_container_width=True,
                    help="Excel ve geriye dönük başarı analizi için tam döküm"
                )
            with c_d3:
                import json
                if st.button("🚀 Nesine'ye Gönder", type="primary", use_container_width=True, help="Kuponu tarayıcı hafızasına / panoya yazar ve Nesine Spor Toto sayfasını yeni sekmede açarak Tampermonkey ile otomatik aktarır."):
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
            with c_d4:
                if st.button(f"💼 Kuponlarım ➡️", use_container_width=True, help=f"{tot_sheets} Sayfalık kuponlarıma git"):
                    st.session_state["current_view"] = "💼 Kuponlarım"
                    st.rerun()
