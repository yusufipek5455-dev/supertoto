import streamlit as st
import numpy as np
import math
from live_tracker import (
    load_active_portfolio,
    save_active_portfolio,
    fetch_live_toto_scores_detailed,
    parse_coupon_content
)
from state_manager import (
    save_workspace_state,
    export_coupons_txt,
    export_coupons_csv
)
from core_engine import run_syndicate_solver

def estimate_prize_climate(fixtures, finished_results):
    finished_indices = [i for i, r in enumerate(finished_results) if r is not None and r in ['1', 'X', '2']]
    if not finished_indices:
        return None

    odds_multipliers = []
    for idx in finished_indices:
        res = finished_results[idx]
        odds = fixtures[idx].get("odds", [33.3, 33.3, 33.4]) if idx < len(fixtures) else [33.3, 33.3, 33.4]
        if not odds or sum(odds) == 0:
            odds = [33.3, 33.3, 33.4]
        tot = sum(odds)
        raw_val = odds[0] if res == '1' else (odds[1] if res == 'X' else odds[2])
        p = (raw_val / tot) if tot > 0 else (1.0 / 3.0)
        odds_multipliers.append(max(0.01, p))

    k = len(finished_indices)
    cum_prob = float(np.prod(odds_multipliers))
    neutral_prob = float((1.0 / 3.0) ** k)
    difficulty_ratio = neutral_prob / cum_prob if cum_prob > 0 else 1.0
    public_success_index = (cum_prob / neutral_prob) * 100.0 if neutral_prob > 0 else 100.0

    if difficulty_ratio > 4.0:
        climate = "Aşırı Sürpriz Karşılaşmalar (Devir Riski Yüksek)"
        color = "#ef4444"
        badge = "🔥 ÇOK YÜKSEK İKRAMİYE"
        base_12 = "800 TL - 3.000 TL"
        base_13 = "8.000 TL - 35.000 TL"
        base_14 = "80.000 TL - 450.000 TL"
        base_15 = "Devir / 5.000.000+ TL"
    elif difficulty_ratio > 1.2:
        climate = "Sürpriz Ağırlıklı (Yüksek İkramiye Potansiyeli)"
        color = "#f59e0b"
        badge = "⚡ YÜKSEK İKRAMİYE"
        base_12 = "300 TL - 1.200 TL"
        base_13 = "2.000 TL - 8.500 TL"
        base_14 = "20.000 TL - 75.000 TL"
        base_15 = "1.200.000 TL - 3.500.000 TL"
    elif difficulty_ratio > 0.4:
        climate = "Dengeli / Normal Dağılım (Piyasa Standartları)"
        color = "#38bdf8"
        badge = "⚖️ DENGELİ HAVUZ"
        base_12 = "150 TL - 500 TL"
        base_13 = "1.000 TL - 4.000 TL"
        base_14 = "10.000 TL - 35.000 TL"
        base_15 = "500.000 TL - 1.800.000 TL"
    else:
        climate = "Favori Yoğun (Düşük İkramiye Havuzu)"
        color = "#94a3b8"
        badge = "📉 DÜŞÜK İKRAMİYE"
        base_12 = "40 TL - 120 TL"
        base_13 = "150 TL - 500 TL"
        base_14 = "1.200 TL - 4.500 TL"
        base_15 = "80.000 TL - 250.000 TL"

    return {
        "k": k,
        "difficulty_ratio": difficulty_ratio,
        "public_success_index": public_success_index,
        "climate": climate,
        "badge": badge,
        "color": color,
        "est_12": base_12,
        "est_13": base_13,
        "est_14": base_14,
        "est_15": base_15
    }

def get_top_4_columns(columns, scores):
    if not columns:
        return []

    scored_cols = []
    for idx, col in enumerate(columns):
        hits = 0
        errors = 0
        pending = 0
        for m_idx in range(15):
            res = scores[m_idx] if m_idx < len(scores) else None
            if res in ['1', 'X', '2']:
                if col[m_idx] == res:
                    hits += 1
                else:
                    errors += 1
            else:
                pending += 1

        max_potential = 15 - errors
        scored_cols.append({
            "col_idx": idx,
            "col_num": idx + 1,
            "picks": col,
            "hits": hits,
            "errors": errors,
            "pending": pending,
            "max_potential": max_potential
        })

    scored_cols.sort(key=lambda x: (x["errors"], -x["hits"], x["col_idx"]))
    return scored_cols[:4]

def render():
    fixtures = st.session_state.get("fixtures", [])
    sol = st.session_state.get("solution")
    
    # 1. Kupon Portföyünü Otomatik Sağlama Al
    if not sol or not isinstance(sol, dict) or (not sol.get("columns") and not sol.get("sheets")):
        active_disk = load_active_portfolio()
        if active_disk and isinstance(active_disk, dict) and (active_disk.get("columns") or active_disk.get("sheets")):
            sol = active_disk
            st.session_state["solution"] = sol
        elif st.session_state.get("saved_portfolios"):
            first_name = list(st.session_state["saved_portfolios"].keys())[0]
            sol = st.session_state["saved_portfolios"][first_name]
            st.session_state["solution"] = sol
        else:
            user_picks = st.session_state.get("user_picks", {})
            sol = run_syndicate_solver(user_picks, fixtures=fixtures, mode="13G", target_cols=None)
            st.session_state["solution"] = sol
            save_active_portfolio(sol)
            save_workspace_state()



    scores = st.session_state.get("live_scores", [None] * 15)
    match_details = st.session_state.get("live_match_details", [
        {"status": "NS", "minute": "-", "score": "- - -", "outcome": "-", "is_official": False} for _ in range(15)
    ])

    columns = []
    if sol and isinstance(sol, dict):
        if sol.get("columns"):
            columns = sol["columns"]
        elif sol.get("sheets"):
            for s in sol["sheets"]:
                for l in ["A", "B", "C", "D"]:
                    if l in s and len(s[l]) == 15:
                        columns.append(s[l])

    tot_cols = len(columns)
    tot_cost = sol.get("total_cost", tot_cols * 10) if sol else tot_cols * 10

    user_picks = st.session_state.get("user_picks", {})
    coupon_picks_by_match = []
    for m_i in range(15):
        if columns:
            p_set = set(col[m_i] for col in columns if len(col) > m_i)
            coupon_picks_by_match.append(list(p_set) if p_set else ['1'])
        else:
            coupon_picks_by_match.append(user_picks.get(m_i, ['1']))

    finished_indices = [i for i, val in enumerate(scores) if val is not None and val in ['1', 'X', '2']]

    # Tercih Havuzu Delinme (Out-of-Bounds) Tespiti
    # Kullanıcının seçmediği bir sonuç bittiği/simüle edildiği an, kalkan garantisi matematiksel olarak çöker.
    breaches = []
    breach_indices = set()
    for m_i in range(15):
        res = scores[m_i]
        if res in ['1', 'X', '2']:
            allowed = set(coupon_picks_by_match[m_i])
            if user_picks and user_picks.get(m_i):
                allowed.update(user_picks[m_i])
            if allowed and (res not in allowed):
                f = fixtures[m_i] if m_i < len(fixtures) else {}
                m_no = f.get("no", m_i + 1)
                h = f.get("home", f"Ev {m_no}")
                is_off = match_details[m_i].get("is_official", False) if m_i < len(match_details) else False
                breaches.append({
                    "index": m_i,
                    "no": m_no,
                    "team": h,
                    "outcome": res,
                    "allowed": "/".join(sorted(list(allowed))),
                    "is_official": is_off
                })
                breach_indices.add(m_i)

    if columns:
        error_counts = []
        for col in columns:
            err = sum(1 for m_idx in finished_indices if col[m_idx] != scores[m_idx])
            error_counts.append(err)
        err_arr = np.array(error_counts)
        c15 = int(np.sum(err_arr == 0))
        c14 = int(np.sum(err_arr == 1))
        c13 = int(np.sum(err_arr == 2))
        c12 = int(np.sum(err_arr == 3))
    else:
        c15, c14, c13, c12 = 0, 0, 0, 0

    top_4_cols = get_top_4_columns(columns, scores)

    # Ultra-Kompakt CSS Enjeksiyonu (15 Maçın Tamamı Ekrana Sığacak Şekilde)
    st.html("""
    <style>
        .block-container {
            padding-top: 0.1rem !important;
            padding-bottom: 0.1rem !important;
            max-width: 99% !important;
        }
        [data-testid="stVerticalBlock"] {
            gap: 1px !important;
            row-gap: 1px !important;
        }
        [data-testid="stElementContainer"] {
            margin: 0 !important;
            padding: 0 !important;
        }
        [data-testid="stHorizontalBlock"] {
            gap: 2px !important;
            margin: 0 !important;
            align-items: center !important;
        }
        div[data-testid="column"] {
            min-width: 0 !important;
            padding: 0 !important;
        }

        /* Skor Tablosu */
        .live-scoreboard {
            width: 100%;
            border-collapse: collapse;
            border-radius: 5px;
            overflow: hidden;
            margin-bottom: 3px;
            text-align: center;
        }
        .live-scoreboard th {
            background: #1e293b;
            color: #94a3b8;
            font-size: 10px;
            font-weight: 700;
            padding: 2px 4px;
            border: 1px solid #334155;
            text-transform: uppercase;
            letter-spacing: 0.2px;
        }
        .live-scoreboard td {
            padding: 2px 4px;
            font-size: 14px;
            font-weight: 800;
            font-family: 'JetBrains Mono', monospace;
            border: 1px solid #334155;
            color: #f8fafc;
        }
        .live-scoreboard .val-15 { color: #10b981; }
        .live-scoreboard .val-14 { color: #38bdf8; }
        .live-scoreboard .val-13 { color: #f59e0b; }
        .live-scoreboard .val-12 { color: #a855f7; }
        .live-scoreboard .val-cost { color: #f8fafc; font-size: 13.5px; }

        /* Aksiyon Barı Butonları */
        div:has(> .is-live-actions) + div button {
            height: 26px !important;
            min-height: 26px !important;
            font-size: 11px !important;
            font-weight: 700 !important;
            padding: 0 4px !important;
            border-radius: 5px !important;
            margin: 0 !important;
        }

        /* Kompakt İkramiye İklimi Şeridi */
        .climate-strip {
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: nowrap;
            background: #0f172a;
            border: 1px solid #334155;
            border-radius: 5px;
            padding: 1px 8px;
            margin-bottom: 3px;
            font-size: 10.5px;
            gap: 4px;
            overflow-x: auto;
            height: 23px;
        }
        .climate-badge-pill {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            font-weight: 800;
            white-space: nowrap;
            padding: 0 5px;
            border-radius: 3px;
            font-size: 9.5px;
        }
        .tier-mini-pill {
            display: inline-flex;
            align-items: center;
            gap: 3px;
            color: #94a3b8;
            white-space: nowrap;
            background: #1e293b;
            padding: 0 4px;
            border-radius: 3px;
            border: 1px solid #334155;
            font-size: 9.5px;
        }
        .tier-mini-pill b {
            font-family: 'JetBrains Mono', monospace;
        }

        /* Maç Numarası */
        .badge-num {
            background: #0f172a;
            border: 1px solid #334155;
            color: #38bdf8;
            font-family: monospace;
            font-weight: 800;
            font-size: 9.5px;
            border-radius: 3px;
            width: 24px;
            height: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }

        /* Tercih Kutuları */
        .pick-box {
            flex: 1;
            height: 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 4px;
            border-radius: 3px;
            font-size: 9.5px;
            font-weight: 600;
            border: 1px solid #334155;
            background: #1e293b;
            color: #94a3b8;
            overflow: hidden;
            white-space: nowrap;
            text-overflow: ellipsis;
        }
        .pick-box.selected {
            background: rgba(16, 185, 129, 0.16) !important;
            border: 1px solid #10b981 !important;
            color: #34d399 !important;
            font-weight: 800 !important;
        }
        .pick-box-x {
            width: 25px;
            flex-shrink: 0;
            height: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 3px;
            font-size: 9px;
            font-weight: 700;
            border: 1px solid #334155;
            background: #1e293b;
            color: #94a3b8;
        }
        .pick-box-x.selected {
            background: rgba(16, 185, 129, 0.16) !important;
            border: 1px solid #10b981 !important;
            color: #34d399 !important;
            font-weight: 800 !important;
        }

        /* Canlı Durum Rozetleri */
        .live-pill {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 0 4px;
            border-radius: 3px;
            font-weight: 800;
            font-family: monospace;
            font-size: 9px;
            white-space: nowrap;
            height: 20px;
        }
        .live-pill.ft {
            background: rgba(16, 185, 129, 0.18);
            color: #34d399;
            border: 1px solid #10b981;
        }
        .live-pill.live {
            background: rgba(245, 158, 11, 0.18);
            color: #fbbf24;
            border: 1px solid #f59e0b;
        }
        .live-pill.sim {
            background: rgba(56, 189, 248, 0.18);
            color: #38bdf8;
            border: 1px solid #38bdf8;
        }
        .live-pill.ns {
            background: #1e293b;
            color: #94a3b8;
            border: 1px solid #334155;
        }

        /* 4 Kolon Başlık Rozetleri */
        .top-col-header-box {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            width: 25px;
            height: 20px;
            border-radius: 3px;
            font-weight: 800;
            font-family: 'JetBrains Mono', monospace;
            border: 1px solid #334155;
            background: #0f172a;
        }
        .top-col-header-box.tier-15 {
            color: #10b981;
            border-color: #10b981;
            background: rgba(16, 185, 129, 0.12);
        }
        .top-col-header-box.tier-14 {
            color: #38bdf8;
            border-color: #38bdf8;
            background: rgba(56, 189, 248, 0.12);
        }
        .top-col-header-box.tier-13 {
            color: #f59e0b;
            border-color: #f59e0b;
            background: rgba(245, 158, 11, 0.12);
        }
        .top-col-header-box.tier-12 {
            color: #a855f7;
            border-color: #a855f7;
            background: rgba(168, 85, 247, 0.12);
        }
        .top-col-header-box.tier-dead {
            color: #64748b;
            border-color: #334155;
            background: #1e293b;
        }

        /* 4 Kolon Hücre Rozetleri */
        .top-col-pill {
            width: 25px;
            height: 20px;
            border-radius: 3px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-family: 'JetBrains Mono', monospace;
            font-size: 10px;
            background: #f59e0b;
            color: #000000;
            border: 1px solid #d97706;
        }
        .top-col-pill.hit {
            background: #f59e0b;
            color: #000000;
            border: 1.5px solid #10b981 !important;
            box-shadow: 0 0 4px rgba(16, 185, 129, 0.6);
        }
        .top-col-pill.miss {
            opacity: 0.3;
            background: #475569;
            color: #cbd5e1;
            border: 1px solid #ef4444 !important;
            filter: grayscale(0.6);
        }

        /* Simülasyon Butonları - 3. Kolondaki (c_res) tüm butonlar */
        div[data-testid="column"]:nth-child(3) div.stButton > button {
            padding: 0 !important;
            height: 20px !important;
            min-height: 20px !important;
            max-height: 20px !important;
            font-size: 9.5px !important;
            font-weight: 700 !important;
            line-height: 18px !important;
            border-radius: 3px !important;
            margin: 0 !important;
        }
    </style>
    """)

    # 0.5 Havuz Delinme Uyarısı (Kullanıcı Kendi Havuzunu Deldiğinde Kör Kalmaması İçin)
    if breaches:
        breach_items = [
            f"<b>M{b['no']:02d} ({b['team']}):</b> Tercih '<code>{b['allowed']}</code>' iken '<code>{b['outcome']}</code>' geldi ({'Resmi' if b['is_official'] else 'Sim'})"
            for b in breaches
        ]
        breach_text = " &nbsp;|&nbsp; ".join(breach_items)
        mode_str = sol.get("mode", "13G") if sol else "13G"
        st.html(f"""
        <div style="background: rgba(239, 68, 68, 0.2); border: 1.5px solid #ef4444; border-radius: 5px; padding: 4px 10px; margin-bottom: 3px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 4px;">
            <div style="display: flex; align-items: center; gap: 6px;">
                <span style="font-size: 13px;">🚨</span>
                <span style="font-weight: 800; color: #ef4444; font-size: 11px;">
                    DİKKAT: TERCİH HAVUZU DELİNDİ — {mode_str} KALKAN GARANTİSİ RESMİ OLARAK BOZULDU!
                </span>
            </div>
            <div style="color: #fca5a5; font-size: 10.5px;">
                {breach_text} <span style="color:#f87171;">— (Kalan ikramiyeler artık kalkan garantisine değil, alt kolon şansına bağlıdır)</span>
            </div>
        </div>
        """)

    # 1. Üst Skor Tablosu
    val_15_style = "color:#ef4444 !important;" if breaches else ""
    val_14_style = "color:#ef4444 !important;" if (len(breaches) >= 2) else ""
    val_15_sub = "<small style='font-size:8.5px;color:#fca5a5;font-weight:700;'>(Şans)</small>" if breaches else ""
    val_14_sub = "<small style='font-size:8.5px;color:#fca5a5;font-weight:700;'>(Şans)</small>" if (len(breaches) >= 2) else ""
    tag_15 = "<span style='color:#ef4444;font-size:8px;padding:0 3px;background:rgba(239,68,68,0.2);border-radius:2px;border:1px solid #ef4444;'>DELİNDİ</span>" if breaches else ""

    st.html(f"""
    <table class="live-scoreboard">
        <thead>
            <tr>
                <th>Kupon Bedeli</th>
                <th>15 Giden {tag_15}</th>
                <th>14 Giden</th>
                <th>13 Giden</th>
                <th>12 Giden</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td class="val-cost">₺{tot_cost:,}</td>
                <td class="val-15" style="{val_15_style}">{c15} {val_15_sub}</td>
                <td class="val-14" style="{val_14_style}">{c14} {val_14_sub}</td>
                <td class="val-13">{c13}</td>
                <td class="val-12">{c12}</td>
            </tr>
        </tbody>
    </table>
    """)

    # İşlem Barı
    st.html('<span class="is-live-actions"></span>')
    c_btn_live, c_btn_reset, c_btn_creator, c_btn_dl = st.columns([3.5, 2.5, 2.0, 2.0])
    with c_btn_live:
        if st.button("🌐 Nesine'den Canlı Skorları Çek", key="btn_fetch_nesine_live", type="primary", use_container_width=True, help="Nesine resmi bülteninden biten ve canlı maç skorlarını anlık çeker ve kilitler"):
            with st.spinner("Nesine canlı verisi alınıyor..."):
                detailed = fetch_live_toto_scores_detailed(force_refresh=True)
                if detailed.get("success"):
                    updated_cnt = 0
                    for m in detailed["matches"]:
                        m_idx = m.get("match_no", 1) - 1
                        if 0 <= m_idx < 15:
                            st_val = m.get("status", "NS")
                            out = m.get("current_outcome")
                            
                            if st_val in ["FT", "LIVE"] and out in ['1', 'X', '2']:
                                scores[m_idx] = out
                                match_details[m_idx] = {
                                    "status": st_val,
                                    "minute": m.get("minute", "-"),
                                    "score": m.get("score", "- - -"),
                                    "outcome": out,
                                    "is_official": True
                                }
                                updated_cnt += 1
                            else:
                                if not match_details[m_idx].get("is_simulated", False):
                                    scores[m_idx] = None
                                    match_details[m_idx] = {
                                        "status": "NS",
                                        "minute": "-",
                                        "score": "- - -",
                                        "outcome": "-",
                                        "is_official": False
                                    }

                    # Canlı oranları ve takım adlarını da fixtures ile senkronize et
                    cur_fixtures = st.session_state.get("fixtures", [])
                    if cur_fixtures and len(cur_fixtures) == 15:
                        for m in detailed["matches"]:
                            m_idx = m.get("match_no", 1) - 1
                            if 0 <= m_idx < 15 and "odds" in m:
                                cur_fixtures[m_idx]["odds"] = m["odds"]
                                cur_fixtures[m_idx]["home"] = m["home"]
                                cur_fixtures[m_idx]["away"] = m["away"]
                                cur_fixtures[m_idx]["date"] = m["date"]
                        st.session_state["fixtures"] = cur_fixtures

                    st.session_state["live_scores"] = scores
                    st.session_state["live_match_details"] = match_details
                    save_workspace_state()
                    cnt = detailed.get("counts", {})
                    if updated_cnt > 0:
                        st.toast(f"✅ {updated_cnt} maç güncellendi ({cnt.get('finished', 0)} Bitti, {cnt.get('live', 0)} Canlı)", icon="🎯")
                    else:
                        st.toast("✅ Nesine bağlantısı sağlandı. 15 karşılaşmanın tamamı henüz başlamadı.", icon="ℹ️")
                    st.rerun()
                else:
                    st.toast(f"⚠️ Nesine servisine bağlanılamadı: {detailed.get('error', 'Zaman aşımı')}", icon="❌")

    with c_btn_reset:
        if st.button("🗑️ Simülasyonları Sıfırla", use_container_width=True, help="Yalnızca kullanıcı tarafından simüle edilen sonuçları temizler, resmi maçları korur"):
            for i in range(15):
                if not match_details[i].get("is_official", False):
                    scores[i] = None
                    match_details[i] = {
                        "status": "NS",
                        "minute": "-",
                        "score": "- - -",
                        "outcome": "-",
                        "is_official": False
                    }
            st.session_state["live_scores"] = scores
            st.session_state["live_match_details"] = match_details
            save_workspace_state()
            st.rerun()

    with c_btn_creator:
        if st.button("🎯 Kuponu Düzenle", use_container_width=True):
            st.session_state["current_view"] = "🎯 Kupon Oluşturucu"
            st.rerun()

    with c_btn_dl:
        with st.popover("📥 Yedekle", use_container_width=True):
            st.caption("Kupon Düz Metin / Tablo İndir")
            txt_content = export_coupons_txt(columns, mode=sol.get("mode", "13G") if sol else "13G", total_cost=tot_cost)
            st.download_button(
                label="📥 .TXT İndir (15 Karakter)",
                data=txt_content,
                file_name=f"sportoto_kuponlar_{tot_cols}kolon.txt",
                mime="text/plain",
                use_container_width=True
            )
            csv_content = export_coupons_csv(columns)
            st.download_button(
                label="📥 .CSV İndir (Tablo)",
                data=csv_content,
                file_name=f"sportoto_kuponlar_{tot_cols}kolon.csv",
                mime="text/csv",
                use_container_width=True
            )

    # 2. İkramiye Olasılığı Şeridi (Tek Yatay Bar)
    climate_info = estimate_prize_climate(fixtures, scores)
    if not climate_info:
        climate_info = {
            "k": 0,
            "climate": "Dengeli Dağılım",
            "badge": "⚖️ DENGELİ HAVUZ",
            "color": "#38bdf8",
            "difficulty_ratio": 1.0,
            "public_success_index": 100.0,
            "est_12": "150-500 TL",
            "est_13": "1.000-4.000 TL",
            "est_14": "10.000-35.000 TL",
            "est_15": "500.000-1.800.000 TL"
        }

    st.html(f"""
    <div class="climate-strip">
        <div class="climate-badge-pill" style="background:{climate_info['color']}22; color:{climate_info['color']}; border:1px solid {climate_info['color']};">
            {climate_info['badge']} <span style="color:#94a3b8; font-weight:600;">({climate_info['k']}/15 Maç)</span>
        </div>
        <div class="tier-mini-pill">
            <span>15 Bilen:</span> <b style="color:#10b981;">{climate_info['est_15']}</b> <small>({c15} Kolon)</small>
        </div>
        <div class="tier-mini-pill">
            <span>14 Bilen:</span> <b style="color:#38bdf8;">{climate_info['est_14']}</b> <small>({c14} Kolon)</small>
        </div>
        <div class="tier-mini-pill">
            <span>13 Bilen:</span> <b style="color:#f59e0b;">{climate_info['est_13']}</b> <small>({c13} Kolon)</small>
        </div>
        <div class="tier-mini-pill">
            <span>12 Bilen:</span> <b style="color:#a855f7;">{climate_info['est_12']}</b> <small>({c12} Kolon)</small>
        </div>
    </div>
    """)

    # 3. 15 Maç ve Sportoto Extra Tarzı En Çok Tutan İlk 4 Kolon Tablosu
    h_no, h_match, h_res, h_top4 = st.columns([0.35, 4.4, 2.7, 2.55], gap="small")
    with h_no:
        st.html("<div style='font-size:9.5px; font-weight:800; color:#94a3b8; text-align:center;'>#</div>")
    with h_match:
        st.html("<div style='font-size:9.5px; font-weight:800; color:#94a3b8; padding-left:2px;'>Tercihleriniz (Ev Sahibi - Beraberlik - Deplasman)</div>")
    with h_res:
        st.html("<div style='font-size:9.5px; font-weight:800; color:#38bdf8; text-align:center;'>Canlı Skor & Simülasyon</div>")
    with h_top4:
        top4_headers_html = []
        for rank_i in range(4):
            if rank_i < len(top_4_cols):
                c_item = top_4_cols[rank_i]
                pot = c_item["max_potential"]
                k_num = c_item["col_num"]
                cls = "tier-15" if pot >= 15 else ("tier-14" if pot == 14 else ("tier-13" if pot == 13 else ("tier-12" if pot == 12 else "tier-dead")))
                top4_headers_html.append(f'<div class="top-col-header-box {cls}" title="Kolon #{k_num}: {c_item["hits"]} D, {c_item["errors"]} Y"><span style="font-size:10px;line-height:1;">{pot}</span><span style="font-size:7px;opacity:0.8;line-height:1;">K#{k_num}</span></div>')
            else:
                top4_headers_html.append('<div class="top-col-header-box tier-dead"><span style="font-size:10px;">-</span></div>')

        st.html(f'<div style="display:flex; gap:3px; justify-content:center; align-items:center;">{"".join(top4_headers_html)}</div>')

    # 15 Karşılaşma Satır Döngüsü
    for i in range(15):
        fix = fixtures[i] if i < len(fixtures) else {"no": i+1, "home": "Takım 1", "away": "Takım 2", "odds": [33.3, 33.3, 33.4]}
        no = fix.get("no", i + 1)
        home = fix.get("home", "")
        away = fix.get("away", "")
        odds = fix.get("odds", [33.3, 33.3, 33.4])

        my_picks = coupon_picks_by_match[i]
        sel_1 = '1' in my_picks
        sel_x = 'X' in my_picks
        sel_2 = '2' in my_picks

        cur_outcome = scores[i]
        det = match_details[i] if i < len(match_details) else {"status": "NS", "minute": "-", "score": "- - -", "is_official": False}
        status = det.get("status", "NS")
        minute = det.get("minute", "-")
        score_str = det.get("score", "- - -")
        is_official = det.get("is_official", False)
        is_breached = (i in breach_indices)

        if is_breached:
            if is_official and (status == "FT" or minute == "MS"):
                res_badge_html = f'<span class="live-pill" style="background:rgba(239,68,68,0.25); color:#f87171; border:1px solid #ef4444;">🚨 Delindi: MS {score_str} ({cur_outcome})</span>'
            elif is_official:
                res_badge_html = f'<span class="live-pill" style="background:rgba(239,68,68,0.25); color:#f87171; border:1px solid #ef4444;">🚨 Delindi: {minute} ({cur_outcome})</span>'
            else:
                res_badge_html = f'<span class="live-pill" style="background:rgba(239,68,68,0.25); color:#f87171; border:1px solid #ef4444;">🚨 Sim Dışı: {cur_outcome}</span>'
        elif is_official and cur_outcome in ['1', 'X', '2']:
            if status == "FT" or minute == "MS":
                res_badge_html = f'<span class="live-pill ft">🔒 MS {score_str} ({cur_outcome})</span>'
            else:
                res_badge_html = f'<span class="live-pill live">🔒 🔴 {score_str} {minute} ({cur_outcome})</span>'
        elif cur_outcome in ['1', 'X', '2']:
            res_badge_html = f'<span class="live-pill sim">⚡ Sim: {cur_outcome}</span>'
        else:
            time_str = fix.get("date", "").split()[-1] if fix.get("date") else "Bekliyor"
            res_badge_html = f'<span class="live-pill ns">📅 {time_str}</span>'

        c_no, c_match, c_res, c_top4 = st.columns([0.35, 4.4, 2.7, 2.55], gap="small")

        with c_no:
            st.html(f'<div class="badge-num" style="{"border-color:#ef4444;color:#ef4444;" if is_breached else ""}">{no:02d}</div>')

        with c_match:
            breach_tag = '<span style="color:#ef4444; font-size:8px; font-weight:800; background:rgba(239,68,68,0.2); border:1px solid #ef4444; border-radius:2px; padding:0 3px; margin-left:3px;">🚨 DELİNDİ</span>' if is_breached else ''
            st.html(f"""
            <div style="display:flex; gap:3px; align-items:center; width:100%;">
                <div class="pick-box {'selected' if sel_1 else ''}">
                    <span style="overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">{home}</span>
                    <span style="font-family:monospace; font-size:9px; margin-left:2px; opacity:0.85;">%{odds[0]:.0f}</span>
                </div>
                <div class="pick-box-x {'selected' if sel_x else ''}">
                    <span>X</span>
                </div>
                <div class="pick-box {'selected' if sel_2 else ''}">
                    <span style="overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">{away}</span>
                    <span style="font-family:monospace; font-size:9px; margin-left:2px; opacity:0.85;">%{odds[2]:.0f}</span>
                </div>
                {breach_tag}
            </div>
            """)

        with c_res:
            if is_official:
                st.html(f"""
                <div style="height:20px; display:flex; align-items:center; justify-content:space-between; padding:0 2px;">
                    {res_badge_html}
                    <span style="font-size:9px; color:#64748b; font-weight:700;">🔒 Resmi</span>
                </div>
                """)
            else:
                c_pill, c_1, c_x, c_2, c_clr = st.columns([1.8, 0.8, 0.8, 0.8, 0.7], gap="small")
                with c_pill:
                    st.html(f'<div style="height:20px; display:flex; align-items:center;">{res_badge_html}</div>')
                with c_1:
                    if st.button("1", key=f"sim_{no}_1", type="primary" if cur_outcome == '1' else "secondary", use_container_width=True):
                        scores[i] = '1'
                        match_details[i]["outcome"] = '1'
                        match_details[i]["status"] = "SIM"
                        match_details[i]["is_simulated"] = True
                        match_details[i]["is_official"] = False
                        st.session_state["live_scores"] = scores
                        st.session_state["live_match_details"] = match_details
                        save_workspace_state()
                        st.rerun()
                with c_x:
                    if st.button("X", key=f"sim_{no}_X", type="primary" if cur_outcome == 'X' else "secondary", use_container_width=True):
                        scores[i] = 'X'
                        match_details[i]["outcome"] = 'X'
                        match_details[i]["status"] = "SIM"
                        match_details[i]["is_simulated"] = True
                        match_details[i]["is_official"] = False
                        st.session_state["live_scores"] = scores
                        st.session_state["live_match_details"] = match_details
                        save_workspace_state()
                        st.rerun()
                with c_2:
                    if st.button("2", key=f"sim_{no}_2", type="primary" if cur_outcome == '2' else "secondary", use_container_width=True):
                        scores[i] = '2'
                        match_details[i]["outcome"] = '2'
                        match_details[i]["status"] = "SIM"
                        match_details[i]["is_simulated"] = True
                        match_details[i]["is_official"] = False
                        st.session_state["live_scores"] = scores
                        st.session_state["live_match_details"] = match_details
                        save_workspace_state()
                        st.rerun()
                with c_clr:
                    if st.button("⟲", key=f"sim_{no}_clr", use_container_width=True, help="Simülasyonu Temizle"):
                        scores[i] = None
                        match_details[i]["outcome"] = "-"
                        match_details[i]["status"] = "NS"
                        match_details[i]["is_simulated"] = False
                        match_details[i]["is_official"] = False
                        st.session_state["live_scores"] = scores
                        st.session_state["live_match_details"] = match_details
                        save_workspace_state()
                        st.rerun()

        with c_top4:
            pills_html = []
            for rank_i in range(4):
                if rank_i < len(top_4_cols):
                    c_item = top_4_cols[rank_i]
                    p_val = c_item["picks"][i] if i < len(c_item["picks"]) else "-"
                    
                    if cur_outcome in ['1', 'X', '2']:
                        pill_state = "hit" if p_val == cur_outcome else "miss"
                    else:
                        pill_state = "pending"

                    pills_html.append(f'<div class="top-col-pill {pill_state}">{p_val}</div>')
                else:
                    pills_html.append('<div class="top-col-pill" style="opacity:0.2;">-</div>')

            st.html(f'<div style="display:flex; gap:3px; justify-content:center; align-items:center; height:20px;">{"".join(pills_html)}</div>')


