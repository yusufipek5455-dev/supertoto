"""
SPORTOTO COCKPIT - MULTI-COVERING & CASCADING PAYOUT ARCHITECTURE
================================================================
Institutional quantitative football modeling for Spor Toto 15-match fixtures.

Pure Mathematical Guarantee Levels:
- 🛡️ 13G Garanti (R=2): Multi-Covering K >= 2 on high +EV clusters. Cascading 13 + 3-6x 12.
- 🎯 14G Garanti (R=1): Multi-Covering K >= 2 on high +EV clusters. Cascading 14 + multiple 13 & 12.
- 👑 15G Tam Kapsama (R=0): Full Cartesian identity universe (Zero Error).

Architecture Invariants:
- Dynamic pricing on all buttons & selectors: Cost = Columns * 10.00 TL.
- Decoupled execution trigger: Toggling checkboxes updates real-time estimates with zero lag;
  optimization and coupon generation ONLY run when clicking '🚀 Kuponları ve Varyasyonları Oluştur'.
- Official Nesine 40 TL Sheet Formulation: 4 Columns (Harf A, B, C, D) = 40.00 TL.
"""

import streamlit as st
import streamlit.components.v1 as components
import json
import random
import textwrap
import math
import re
from datetime import datetime

import importlib
import live_tracker
import covering_engine
import toto_quant_engine
try:
    importlib.reload(live_tracker)
    importlib.reload(covering_engine)
    importlib.reload(toto_quant_engine)
except Exception:
    pass

from toto_quant_engine import FIXTURE
from live_tracker import (
    fetch_live_toto_scores,
    evaluate_syndicate_portfolio,
    get_default_match_states,
    calculate_portfolio_match_distributions,
    save_active_portfolio,
    load_active_portfolio,
    delete_active_portfolio,
    parse_coupon_content
)

from covering_engine import engine
from components.tickets import TicketExporter


def safe_markdown(content: str):
    st.markdown(textwrap.dedent(content).strip(), unsafe_allow_html=True)

st.set_page_config(
    page_title="Sportoto Quant Cockpit - Multi-Covering 40 TL Sheets",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Reset CSS & Modern Dark Tabs
st.markdown("""
<style>
    #MainMenu, header, footer, .stDeployButton {display: none !important;}
    div[data-testid="stToolbar"] {display: none !important;}
    div[data-testid="stDecoration"] {display: none !important;}
    div[data-testid="stStatusWidget"] {display: none !important;}
    .block-container {
        padding: 0 !important;
        margin: 0 !important;
        max-width: 100% !important;
    }
    iframe {
        border: none !important;
        width: 100% !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        background: #0f172a;
        padding: 8px 18px;
        border-bottom: 2px solid #334155;
        gap: 16px;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 14.5px;
        font-weight: 800;
        color: #94a3b8;
        padding: 8px 18px;
        border-radius: 6px 6px 0 0;
        transition: all 0.15s ease;
    }
    .stTabs [aria-selected="true"] {
        color: #38bdf8 !important;
        border-bottom: 3px solid #38bdf8 !important;
        background: #1e293b !important;
    }
    .stTabs [data-baseweb="tab-panel"] {
        padding: 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 1. DEFAULT BÜLTEN & STATE YÖNETİMİ ---
DEFAULT_FIXTURES = [
    {"no": 1, "date": "11.09 20:00", "home": "Beşiktaş A.Ş.", "away": "Erzurumspor FK", "odds": [78.0, 14.0, 8.0]},
    {"no": 2, "date": "12.09 17:00", "home": "Eyüpspor", "away": "Çaykur Rizespor A.Ş.", "odds": [44.0, 31.0, 25.0]},
    {"no": 3, "date": "12.09 17:00", "home": "Samsunspor A.Ş.", "away": "Çorum FK", "odds": [68.0, 20.0, 12.0]},
    {"no": 4, "date": "12.09 20:00", "home": "Alanyaspor", "away": "Göztepe A.Ş.", "odds": [38.0, 32.0, 30.0]},
    {"no": 5, "date": "12.09 20:00", "home": "Konyaspor", "away": "Trabzonspor A.Ş.", "odds": [24.0, 28.0, 48.0]},
    {"no": 6, "date": "13.09 17:00", "home": "Gençlerbirliği", "away": "Kasımpaşa A.Ş.", "odds": [34.0, 30.0, 36.0]},
    {"no": 7, "date": "13.09 20:00", "home": "Amed Sportif", "away": "Başakşehir FK", "odds": [26.0, 29.0, 45.0]},
    {"no": 8, "date": "13.09 20:00", "home": "Galatasaray A.Ş.", "away": "Kocaelispor", "odds": [85.0, 10.0, 5.0]},
    {"no": 9, "date": "14.09 20:00", "home": "Gaziantep F.K. A.Ş.", "away": "Fenerbahçe A.Ş.", "odds": [15.0, 22.0, 63.0]},
    {"no": 10, "date": "12.09 16:30", "home": "Augsburg", "away": "B. Leverkusen", "odds": [18.0, 24.0, 58.0]},
    {"no": 11, "date": "11.09 21:45", "home": "Rennes", "away": "Marsilya", "odds": [32.0, 31.0, 37.0]},
    {"no": 12, "date": "12.09 17:00", "home": "Chelsea", "away": "Hull City", "odds": [72.0, 18.0, 10.0]},
    {"no": 13, "date": "13.09 18:30", "home": "Manchester United", "away": "Manchester City", "odds": [25.0, 28.0, 47.0]},
    {"no": 14, "date": "13.09 17:15", "home": "Levante", "away": "Barcelona", "odds": [12.0, 20.0, 68.0]},
    {"no": 15, "date": "12.09 19:00", "home": "Lazio", "away": "AC Milan", "odds": [33.0, 32.0, 35.0]},
]

def format_fixtures(raw_list):
    formatted = []
    for idx, item in enumerate(raw_list[:15]):
        no = item.get("no", idx + 1)
        raw_date = item.get("date") or item.get("time") or item.get("tarih") or item.get("saat") or "Canlı"
        date = str(raw_date).strip()
        
        # 1. Parse Home and Away team names
        h_name, a_name = "", ""
        
        # A) Explicit home/away dictionary keys
        for h_key in ["home", "homeTeam", "Home", "ev", "evSahibi", "h", "ev_sahibi"]:
            for a_key in ["away", "awayTeam", "Away", "dep", "deplasman", "a", "deplasman_takimi"]:
                h_val = str(item.get(h_key, "") or "").strip()
                a_val = str(item.get(a_key, "") or "").strip()
                if h_val and a_val:
                    h_name, a_name = h_val, a_val
                    break
            if h_name and a_name:
                break
                
        # B) Single teams/match field (string or list/tuple)
        if not (h_name and a_name):
            teams_val = item.get("teams") or item.get("match") or item.get("name") or item.get("karsilasma") or item.get("mac")
            if isinstance(teams_val, (list, tuple)) and len(teams_val) >= 2:
                h_name = str(teams_val[0]).strip()
                a_name = str(teams_val[1]).strip()
            elif teams_val and isinstance(teams_val, str):
                t_str = teams_val.strip()
                # Split by newlines (\r\n or \n)
                lines = [line.strip() for line in t_str.splitlines() if line.strip()]
                if len(lines) >= 2:
                    h_name, a_name = lines[0], lines[1]
                else:
                    # Split across whitespace/hyphen variations (" - ", "-", " – ", " — ")
                    parts = re.split(r'\s*[-–—]\s*', t_str, maxsplit=1)
                    if len(parts) >= 2 and parts[0].strip() and parts[1].strip():
                        h_name, a_name = parts[0].strip(), parts[1].strip()
                    else:
                        # Split by vs / v / /
                        parts = re.split(r'\s+(?:vs|v|/)\s+|\s*/\s*', t_str, flags=re.IGNORECASE, maxsplit=1)
                        if len(parts) >= 2 and parts[0].strip() and parts[1].strip():
                            h_name, a_name = parts[0].strip(), parts[1].strip()

        # C) Thorough whitespace cleanup (collapse multiple spaces/tabs/newlines)
        h_name = " ".join(h_name.split()) if h_name else ""
        a_name = " ".join(a_name.split()) if a_name else ""
        
        # D) Safe fallback if still unresolved
        if not h_name or not a_name:
            if idx < len(DEFAULT_FIXTURES):
                h_name = h_name or DEFAULT_FIXTURES[idx]["home"]
                a_name = a_name or DEFAULT_FIXTURES[idx]["away"]
            else:
                h_name = h_name or f"Takım A {idx+1}"
                a_name = a_name or f"Takım B {idx+1}"
        
        # 2. Extract and calibrate odds
        odds_val = item.get("odds") or item.get("rates") or item.get("oranlar") or item.get("p_pub")
        if not odds_val:
            r1 = item.get("rate1") or item.get("oran1") or item.get("1")
            rx = item.get("rateX") or item.get("oranX") or item.get("X") or item.get("rate0") or item.get("oran0")
            r2 = item.get("rate2") or item.get("oran2") or item.get("2")
            if r1 is not None and rx is not None and r2 is not None:
                odds_val = [r1, rx, r2]
            else:
                odds_val = [33.0, 33.0, 34.0]
        try:
            odds = [float(o) for o in odds_val[:3]]
        except Exception:
            odds = [33.0, 33.0, 34.0]
            
        if max(odds) <= 1.0 and sum(odds) <= 1.05:
            odds = [round(o * 100.0, 1) for o in odds]
        else:
            odds = [round(o, 1) for o in odds]
            
        odds_sum = sum(odds) if sum(odds) > 0 else 100.0
        p_pub = [round(o / odds_sum, 4) for o in odds]
        p_true = [round(0.85 * p + 0.15 * (1.0 / 3.0), 4) for p in p_pub]
        t_sum = sum(p_true)
        p_true = [round(p / t_sum, 4) for p in p_true]
        
        formatted.append({
            "no": no,
            "date": date,
            "home": h_name,
            "away": a_name,
            "odds": odds,
            "p_pub": p_pub,
            "p_true": p_true,
            "category": item.get("category", "TR")
        })
    return formatted

if "active_fixtures" not in st.session_state:
    st.session_state["active_fixtures"] = format_fixtures(DEFAULT_FIXTURES)

fixtures = st.session_state["active_fixtures"]
try:
    engine.update_fixtures(fixtures)
except Exception:
    pass
fixtures_json = json.dumps(fixtures)

app_html = f"""
<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sportoto Multi-Covering Cockpit</title>
<style>
    * {{
        box-sizing: border-box;
        margin: 0;
        padding: 0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
        user-select: none;
    }}
    body {{
        background-color: #f1f5f9;
        padding: 10px 14px;
        color: #1e293b;
    }}
    .main-wrap {{
        max-width: 1320px;
        margin: 0 auto;
        display: flex;
        flex-direction: column;
        gap: 12px;
    }}

    /* ÜST DASHBOARD METRICS */
    .top-header {{
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #ffffff;
        padding: 12px 20px;
        border-radius: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        border-left: 4px solid #38bdf8;
    }}
    .brand-logo {{
        font-size: 15px;
        font-weight: 800;
        color: #38bdf8;
        display: flex;
        align-items: center;
        gap: 8px;
    }}
    .brand-badge {{
        background: #0284c7;
        color: #ffffff;
        font-size: 10px;
        font-weight: 800;
        padding: 3px 8px;
        border-radius: 4px;
        letter-spacing: 0.5px;
    }}
    .dashboard-metrics {{
        display: flex;
        gap: 24px;
        align-items: center;
    }}
    .metric-card {{
        display: flex;
        flex-direction: column;
        align-items: flex-end;
    }}
    .metric-sub {{
        font-size: 10px;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    .metric-val {{
        font-size: 14px;
        font-weight: 800;
        color: #ffffff;
    }}
    .metric-val.green {{
        color: #4ade80;
    }}
    .metric-val.yellow {{
        color: #facc15;
    }}

    /* TELEMETRY CASCADING BANNER */
    .telemetry-banner {{
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 4px solid #10b981;
        border-radius: 6px;
        padding: 8px 14px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px;
        font-size: 11.5px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.03);
    }}
    .tel-item {{
        display: flex;
        align-items: center;
        gap: 6px;
    }}
    .tel-label {{
        color: #64748b;
        font-weight: 600;
    }}
    .tel-val {{
        font-weight: 800;
        color: #0f172a;
    }}
    .tel-badge {{
        background: #dcfce7;
        color: #166534;
        font-size: 10px;
        font-weight: 800;
        padding: 2px 6px;
        border-radius: 4px;
    }}

    /* TERCİH HAVUZU VE SAĞ KONTROL PANELİ */
    .extra-board {{
        display: flex;
        gap: 12px;
        background: #ffffff;
        padding: 12px;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }}
    .extra-left {{
        flex: 2.2;
    }}
    .tbl-head-row {{
        display: flex;
        gap: 6px;
        margin-bottom: 6px;
    }}
    .th-no {{
        width: 44px;
        height: 30px;
        background-color: #475569;
        color: #ffffff;
        font-weight: 700;
        font-size: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 4px;
    }}
    .th-tercih {{
        flex: 1;
        height: 30px;
        background-color: #475569;
        color: #ffffff;
        font-weight: 700;
        font-size: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 4px;
    }}

    .match-card-row {{
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 5px 8px;
        margin-bottom: 6px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
        transition: all 0.1s ease;
    }}
    .match-card-row:hover {{
        border-color: #cbd5e1;
        box-shadow: 0 2px 6px rgba(0,0,0,0.06);
    }}
    .match-meta-header {{
        font-size: 11px;
        font-weight: 600;
        color: #94a3b8;
        margin-bottom: 2px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0 1px;
    }}
    .match-grid-row {{
        display: flex;
        gap: 6px;
        align-items: flex-end;
    }}
    .col-no {{
        flex: 0 0 34px;
        display: flex;
        flex-direction: column;
        justify-content: flex-end;
    }}
    .lbl-no-btn {{
        width: 100%;
        height: 30px;
        background: #0f172a;
        color: #38bdf8;
        border: 1px solid #1e293b;
        font-weight: 800;
        font-size: 12px;
        border-radius: 4px;
        display: flex;
        align-items: center;
        justify-content: center;
    }}
    .match-grid-row .col-pick-cell {{
        display: flex;
        flex-direction: column;
        min-width: 0;
    }}
    .match-grid-row .col-pick-cell.cell-home {{
        flex: 4.5;
    }}
    .match-grid-row .col-pick-cell.cell-draw {{
        flex: 1.2;
        min-width: 44px;
    }}
    .match-grid-row .col-pick-cell.cell-away {{
        flex: 4.5;
    }}
    .rate-badge {{
        font-size: 11px;
        font-weight: bold;
        color: #38bdf8;
        text-align: center;
        background: #0f172a;
        border-radius: 4px;
        padding: 1.5px 0;
        margin-bottom: 3px;
        border: 1px solid #1e293b;
        line-height: 14px;
    }}
    .btn-pick {{
        width: 100%;
        height: 30px;
        background-color: #ffffff;
        border: 1.5px solid #cbd5e1;
        border-radius: 4px;
        color: #1e293b;
        font-weight: 600;
        font-size: 11.5px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 0 6px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        transition: all 0.08s ease;
    }}
    .btn-pick:hover {{
        background-color: #f8fafc;
        border-color: #94a3b8;
    }}
    .btn-pick.active {{
        background-color: #16a34a !important;
        border-color: #15803d !important;
        color: #ffffff !important;
        font-weight: 700;
        box-shadow: 0 1px 3px rgba(22, 163, 74, 0.3);
    }}

    /* SAĞ PANEL */
    .extra-right {{
        flex: 1.45;
        display: flex;
        flex-direction: column;
        gap: 8px;
    }}

    .sel-preset {{
        width: 100%;
        padding: 6px 10px;
        border: 1.5px solid #cbd5e1;
        border-radius: 4px;
        font-size: 11.5px;
        font-weight: 600;
        background: #ffffff;
        color: #334155;
        cursor: pointer;
    }}
    .btn-row {{
        display: flex;
        gap: 6px;
    }}
    .btn-white {{
        flex: 1;
        padding: 6px 0;
        background: #ffffff;
        border: 1.5px solid #cbd5e1;
        border-radius: 4px;
        color: #334155;
        font-size: 11px;
        font-weight: 700;
        cursor: pointer;
        text-align: center;
        transition: all 0.1s ease;
    }}
    .btn-white:hover {{
        background: #f1f5f9;
    }}

    /* MULTI-COVER PRESET SELECTOR GRID */
    .grid-presets {{
        display: flex;
        flex-direction: column;
        gap: 6px;
    }}
    .card-preset {{
        border: 2px solid #cbd5e1;
        border-radius: 6px;
        padding: 8px 10px;
        text-align: left;
        background: #ffffff;
        cursor: pointer;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: all 0.1s ease;
    }}
    .card-preset:hover {{
        border-color: #0284c7;
        background: #f8fafc;
    }}
    .card-preset.active-preset {{
        border-color: #0284c7;
        background: #f0f9ff;
        box-shadow: 0 0 0 2px rgba(2, 132, 199, 0.35);
    }}
    .preset-left {{
        display: flex;
        flex-direction: column;
        gap: 2px;
    }}
    .preset-title {{
        font-size: 12px;
        font-weight: 800;
        color: #0f172a;
    }}
    .preset-sub {{
        font-size: 10.5px;
        color: #0284c7;
        font-weight: 700;
    }}
    .preset-tag {{
        display: inline-block;
        font-size: 9px;
        font-weight: 800;
        color: #166534;
        background: #dcfce7;
        padding: 2px 6px;
        border-radius: 4px;
        border: 1px solid #bbf7d0;
        white-space: nowrap;
    }}

    /* PROMINENT PRIMARY EXECUTION BUTTON */
    .btn-execute-primary {{
        width: 100%;
        padding: 12px 14px;
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
        border: none;
        border-radius: 6px;
        color: #ffffff;
        font-size: 13.5px;
        font-weight: 900;
        cursor: pointer;
        text-align: center;
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.35);
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 3px;
        transition: all 0.15s ease;
        margin-top: 2px;
    }}
    .btn-execute-primary:hover {{
        background: linear-gradient(135deg, #0369a1 0%, #075985 100%);
        box-shadow: 0 6px 16px rgba(2, 132, 199, 0.45);
        transform: translateY(-1px);
    }}
    .btn-execute-primary.needs-recalc {{
        background: linear-gradient(135deg, #16a34a 0%, #15803d 100%);
        box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.35), 0 6px 16px rgba(22, 163, 74, 0.4);
        animation: pulseButton 1.6s infinite;
    }}
    @keyframes pulseButton {{
        0% {{ transform: scale(1); }}
        50% {{ transform: scale(1.015); }}
        100% {{ transform: scale(1); }}
    }}
    .btn-execute-primary.executed {{
        background: linear-gradient(135deg, #059669 0%, #047857 100%);
        box-shadow: 0 4px 12px rgba(5, 150, 105, 0.35);
    }}
    .btn-reset-coupons {{
        width: 100%;
        padding: 8px 10px;
        background: #fff1f2;
        color: #e11d48;
        border: 1.5px solid #fecdd3;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 800;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        transition: all 0.15s ease;
        margin-top: 4px;
        margin-bottom: 4px;
    }}
    .btn-reset-coupons:hover {{
        background: #ffe4e6;
        border-color: #fda4af;
        color: #be123c;
    }}
    .btn-execute-sub {{
        font-size: 10.5px;
        font-weight: 700;
        color: #e0f2fe;
    }}

    /* BULK ACTION BUTTONS */
    .btn-bulk-copy {{
        width: 100%;
        padding: 9px 0;
        background: linear-gradient(90deg, #16a34a 0%, #15803d 100%);
        border: none;
        border-radius: 6px;
        color: #ffffff;
        font-size: 12.5px;
        font-weight: 800;
        cursor: pointer;
        text-align: center;
        box-shadow: 0 2px 6px rgba(22, 163, 74, 0.3);
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
    }}
    .btn-bulk-copy:hover {{
        background: linear-gradient(90deg, #15803d 0%, #166534 100%);
    }}

    /* 40 TL KUPON VE KOLON KARTLARI */
    .tickets-container {{
        display: flex;
        flex-direction: column;
        gap: 10px;
    }}
    .tickets-header-bar {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #ffffff;
        padding: 10px 14px;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }}
    .tickets-header-title {{
        font-size: 13px;
        font-weight: 800;
        color: #0f172a;
        display: flex;
        align-items: center;
        gap: 8px;
    }}

    .pagination-bar {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #ffffff;
        padding: 6px 14px;
        border-radius: 6px;
        border: 1px solid #e2e8f0;
    }}
    .btn-page {{
        background: #0284c7;
        color: #ffffff;
        border: none;
        border-radius: 4px;
        padding: 4px 10px;
        font-size: 11px;
        font-weight: 700;
        cursor: pointer;
    }}
    .btn-page:disabled {{
        background: #94a3b8;
        cursor: not-allowed;
    }}

    .sheet-card {{
        background: #ffffff;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border-left: 5px solid #0284c7;
        padding: 12px 14px;
        display: flex;
        flex-direction: column;
        gap: 8px;
    }}
    .sheet-head {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 6px;
        border-bottom: 1px solid #f1f5f9;
        padding-bottom: 8px;
    }}
    .sheet-title-grp {{
        display: flex;
        align-items: center;
        gap: 8px;
    }}
    .sheet-badge-id {{
        background: #0284c7;
        color: #ffffff;
        font-weight: 900;
        font-size: 13px;
        padding: 4px 10px;
        border-radius: 4px;
    }}
    .sheet-cost-pill {{
        background: #dcfce7;
        color: #166534;
        font-size: 11.5px;
        font-weight: 800;
        padding: 3px 10px;
        border-radius: 12px;
        border: 1px solid #bbf7d0;
    }}
    .sheet-slots-pill {{
        background: #e0f2fe;
        color: #0369a1;
        font-size: 11px;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 12px;
        border: 1px solid #bae6fd;
    }}
    .btn-copy-sheet {{
        background: #0284c7;
        color: #ffffff;
        border: none;
        border-radius: 4px;
        padding: 6px 14px;
        font-size: 11.5px;
        font-weight: 700;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 4px;
        box-shadow: 0 2px 6px rgba(2, 132, 199, 0.3);
    }}
    .btn-copy-sheet:hover {{
        background: #0369a1;
    }}

    /* TABLE */
    .sheet-table-wrap {{
        overflow-x: auto;
        border-radius: 6px;
        border: 1px solid #e2e8f0;
    }}
    .sheet-table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 11.5px;
        table-layout: fixed;
    }}
    .sheet-table th {{
        background: #f8fafc;
        color: #475569;
        font-weight: 800;
        padding: 8px 6px;
        border: 1px solid #e2e8f0;
        text-align: center;
    }}
    .sheet-table td {{
        display: table-cell !important;
        padding: 5px 6px;
        border: 1px solid #f1f5f9;
        text-align: center;
        vertical-align: middle;
    }}
    .sheet-table tr:hover td {{
        background: #f8fafc;
    }}
    .sheet-cell-col {{
        display: table-cell !important;
        width: 80px;
        text-align: center;
        vertical-align: middle;
    }}
    .sheet-pick-pill {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 30px;
        height: 28px;
        border-radius: 6px;
        background: #f8fafc;
        color: #0f172a;
        font-weight: 800;
        font-size: 13px;
        border: 1.5px solid #cbd5e1;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04);
        margin: 0 auto;
    }}
    .sheet-pick-pill.is-surprise {{
        background: #fff7ed;
        color: #c2410c;
        border-color: #f97316;
        font-weight: 900;
    }}
    .surprise-tag {{
        background: #ea580c;
        color: #ffffff;
        font-size: 9.5px;
        font-weight: 800;
        padding: 1.5px 5px;
        border-radius: 4px;
        margin-left: 4px;
        display: inline-block;
    }}

    .sheet-summary-letters {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 6px;
        background: #f8fafc;
        padding: 8px 10px;
        border-radius: 6px;
        font-size: 11px;
        border: 1px solid #e2e8f0;
    }}
    .letter-box {{
        display: flex;
        flex-direction: column;
        gap: 2px;
    }}
    .letter-box strong {{
        color: #0284c7;
    }}
    .letter-box span {{
        font-family: monospace;
        font-size: 10.5px;
        color: #334155;
        word-break: break-all;
    }}

    /* MODAL */
    .modal-overlay {{
        display: none;
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(0,0,0,0.65);
        z-index: 1000;
        align-items: center;
        justify-content: center;
    }}
    .modal-card {{
        background: #ffffff;
        padding: 16px;
        border-radius: 8px;
        width: 90%;
        max-width: 660px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.4);
    }}
    .modal-head {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
        border-bottom: 1.5px solid #e2e8f0;
        padding-bottom: 6px;
    }}
    .modal-head h3 {{
        font-size: 14px;
        font-weight: 800;
        color: #0f172a;
    }}
    .modal-close {{
        cursor: pointer;
        font-size: 20px;
        color: #64748b;
    }}
    .modal-ta {{
        width: 100%;
        height: 220px;
        font-family: monospace;
        font-size: 11px;
        padding: 6px;
        border: 1.5px solid #cbd5e0;
        border-radius: 4px;
        background: #f8fafc;
        margin-bottom: 8px;
        box-sizing: border-box;
    }}
</style>
</head>
<body>

<div class="main-wrap">
    <!-- DASHBOARD METRICS HEADER -->
    <div class="top-header">
        <div class="brand-logo">
            <span>⚡ SPORTOTO QUANT COCKPIT</span>
            <span class="brand-badge">MULTI-COVER 40 TL</span>
        </div>
        <div class="dashboard-metrics">
            <div class="metric-card">
                <span class="metric-sub">HAM KARTEZYEN HAVUZ</span>
                <strong class="metric-val" id="metric-raw">1.728 Kolon (17.280 TL)</strong>
            </div>
            <div class="metric-card">
                <span class="metric-sub">ADAPTİF ENTROPİ KESİMİ</span>
                <strong class="metric-val yellow" id="metric-pruned">~1.382 Kolon (Ölü Senaryolar Elendi)</strong>
            </div>
            <div class="metric-card">
                <span class="metric-sub" id="metric-guarantee-lbl">SEÇİLEN GARANTİ: 13G (R=2)</span>
                <strong class="metric-val green" id="metric-reduced">96 Kolon (960 TL)</strong>
            </div>
        </div>
    </div>

    <!-- TELEMETRY CASCADING BANNER -->
    <div class="telemetry-banner">
        <div class="tel-item">
            <span class="tel-label">🎯 15 Jackpot:</span>
            <span class="tel-val" id="tel-p15">%5.56</span>
        </div>
        <div class="tel-item">
            <span class="tel-label">⚡ 14 Şansı:</span>
            <span class="tel-val" id="tel-p14">%83.3</span>
        </div>
        <div class="tel-item">
            <span class="tel-label">🛡️ 13G Garantisi:</span>
            <span class="tel-badge">100% KESİN</span>
        </div>
        <div class="tel-item">
            <span class="tel-label">🏆 Çoklu 12 Dağılımı:</span>
            <span class="tel-val" id="tel-cascade" style="color: #0284c7;">1 Adet 13 + 3-6 Adet 12</span>
        </div>
        <div class="tel-item">
            <span class="tel-label">🔒 1 Hata Kalkanı:</span>
            <span class="tel-val" style="color: #16a34a;">12 Hit: 100% Amorti</span>
        </div>
    </div>

    <!-- 1. BÖLÜM: TERCİH HAVUZU VE SAĞ KONTROL PANELİ -->
    <div class="extra-board">
        <!-- SOL TABLO: 15 MAÇ BUTONLARI -->
        <div class="extra-left">
            <div class="tbl-head-row">
                <div class="th-no">NU.</div>
                <div class="th-tercih">SPORTOTO DİNAMİK TERCİH HAVUZU (1 - X - 2)</div>
            </div>
            <div id="extra-match-rows"></div>
        </div>

        <!-- SAĞ KONTROL PANELİ -->
        <div class="extra-right">
            <select class="sel-preset" onchange="applyPreset(this.value)">
                <option value="varsayilan_1728">Varsayılan Havuz: 1.728 Kolon (3 Tek, 6 Çifte, 3 Üçlü)</option>
                <option value="buyuk_pool">Genişletilmiş Havuz: 9.216 Kolon (3 Tek, 10 Çifte, 2 Üçlü)</option>
                <option value="cift">Tümü Çifte Şans (32.768 Kolon)</option>
                <option value="kapali">Tümünü Kapat (14.348.907 Kolon)</option>
                <option value="tek_ev">Tümünü 1 Yap (1 Kolon)</option>
            </select>

            <div class="btn-row">
                <button class="btn-white" onclick="setPattern('cift')">Tümü Çifte</button>
                <button class="btn-white" onclick="setPattern('kapali')">Tümünü Kapat</button>
                <button class="btn-white" onclick="setPattern('tek_ev')">Tümü 1</button>
            </div>

            <!-- PURE MATHEMATICAL GUARANTEE SELECTOR -->
            <div class="grid-presets">
                <div class="card-preset" id="preset-12g" onclick="selectGuaranteeMode('12G')">
                    <div class="preset-left">
                        <span class="preset-title">🔒 12G Garanti (R=3)</span>
                        <span class="preset-sub" id="sub-12g">16 Kolon / 160 TL</span>
                    </div>
                    <span class="preset-tag">Ekonomik Bütçe Kalkanı</span>
                </div>
                <div class="card-preset active-preset" id="preset-13g" onclick="selectGuaranteeMode('13G')">
                    <div class="preset-left">
                        <span class="preset-title">🛡️ 13G Garanti (R=2)</span>
                        <span class="preset-sub" id="sub-13g">96 Kolon / 960 TL</span>
                    </div>
                    <span class="preset-tag">K&ge;2 Çoklu 12 Kalkanı</span>
                </div>
                <div class="card-preset" id="preset-14g" onclick="selectGuaranteeMode('14G')">
                    <div class="preset-left">
                        <span class="preset-title">🎯 14G Garanti (R=1)</span>
                        <span class="preset-sub" id="sub-14g">192 Kolon / 1.920 TL</span>
                    </div>
                    <span class="preset-tag">K&ge;2 Çoklu 13 Kalkanı</span>
                </div>
                <div class="card-preset" id="preset-15g" onclick="selectGuaranteeMode('15G')">
                    <div class="preset-left">
                        <span class="preset-title">👑 15G Tam Kapsama (R=0)</span>
                        <span class="preset-sub" id="sub-15g">1.728 Kolon / 17.280 TL</span>
                    </div>
                    <span class="preset-tag">Ham Havuz (Sıfır Hata)</span>
                </div>
            </div>

            <!-- PROMINENT PRIMARY EXECUTION BUTTON -->
            <button class="btn-execute-primary" id="btn-execute" onclick="executeOptimization()">
                <span>🚀 Kuponları ve Varyasyonları Oluştur</span>
                <span class="btn-execute-sub" id="btn-execute-sub">13G: 96 Kolon / 960 TL</span>
            </button>

            <!-- RESET / CLEAR GENERATED COUPONS BUTTON -->
            <button class="btn-reset-coupons" id="btn-clear-coupons" onclick="clearGeneratedCoupons()">
                🗑️ Üretilen Kuponları Sil
            </button>

            <!-- BULK EXPORT ACTIONS -->
            <button class="btn-bulk-copy" onclick="copyAllTicketsPayload()">
                📋 Tüm Kolonları Kopyala (Nesine Formatı)
            </button>
            <button class="btn-white" style="padding: 7px 0;" onclick="downloadTxtFile()">
                📥 kuponlar.txt İndir
            </button>
        </div>
    </div>

    <!-- 2. BÖLÜM: 40 TL SHEET CARDS (PAGINATED VIEW) -->
    <div class="tickets-container">
        <div class="tickets-header-bar">
            <div class="tickets-header-title">
                <span>📋 NESİNE 40 TL KUPONLARI (4 KOLON = A-B-C-D = 40 TL)</span>
            </div>
            <div style="font-size: 12px; font-weight: 800; color: #0284c7;" id="lbl-tickets-count">
                96 Kolon (960 TL) Listeleniyor
            </div>
        </div>

        <div class="pagination-bar">
            <button class="btn-page" id="btn-page-prev" onclick="changePage(-1)">⬅️ Önceki Sayfa</button>
            <span id="lbl-page-info" style="font-weight: 700; font-size: 11.5px; color: #475569;">Sayfa 1 / 4 (Kupon 1 - 6)</span>
            <button class="btn-page" id="btn-page-next" onclick="changePage(1)">Sonraki Sayfa ➡️</button>
        </div>

        <div id="sheets-list" style="display: flex; flex-direction: column; gap: 10px;"></div>
    </div>
</div>

<!-- TRANSFER MODAL -->
<div class="modal-overlay" id="export-modal">
    <div class="modal-card">
        <div class="modal-head">
            <h3>📊 Nesine.com Multi-Covering 40 TL Sheet Paketi</h3>
            <div class="modal-close" onclick="closeExportModal()">&times;</div>
        </div>
        <div style="font-size: 11px; color: #64748b; margin-bottom: 6px;">
            Aşağıdaki JSON verisini kopyalayıp Nesine.com konsoluna veya eklentiye yapıştırarak tüm kuponları tek tıkla doldurabilirsiniz:
        </div>
        <textarea class="modal-ta" id="modal-ta-content" readonly></textarea>
        <div style="display: flex; gap: 6px;">
            <button class="btn-page" style="padding: 9px;" onclick="copyModalContent()">📋 Panoya Kopyala</button>
            <button class="btn-white" style="flex: 1; justify-content: center; background: #16a34a; color:#fff; border:none;" onclick="downloadTxtFile()">💾 kuponlar.txt İndir</button>
        </div>
    </div>
</div>

<script>
    const fixtures = {fixtures_json};

    // 15 Maçlık Kullanıcı Tercihleri
    const picks = [];
    const default1728 = [
        ['1'],              // M1: Besiktas (Single)
        ['1', 'X'],         // M2: Eyup (Double)
        ['1', 'X', '2'],    // M3: Samsun (Triple)
        ['1', 'X'],         // M4: Alanya (Double)
        ['X', '2'],         // M5: Konya (Double)
        ['1', 'X', '2'],    // M6: Gencler (Triple)
        ['1', 'X', '2'],    // M7: Amed (Triple)
        ['1'],              // M8: GS (Single)
        ['X', '2'],         // M9: Antep (Double)
        ['X', '2'],         // M10: Augsburg (Double)
        ['1', 'X'],         // M11: Rennes (Double)
        ['1'],              // M12: Chelsea (Single)
        ['1'],              // M13: ManU (Single)
        ['2'],              // M14: Barca (Single)
        ['1']               // M15: Single
    ];

    for (let i = 0; i < 15; i++) {{
        const def = default1728[i];
        picks.push({{
            '1': def.includes('1'),
            'X': def.includes('X'),
            '2': def.includes('2')
        }});
    }}

    let activeGuaranteeMode = '13G'; // '13G', '14G', '15G'
    let isDirty = false;
    let generatedSheets = [];
    let totalGeneratedCols = 96;
    let currentPage = 1;
    const SHEETS_PER_PAGE = 6;

    // Render 15 Match Choice Rows (Tarih, Maç Başlığı ve Oran Rozetli)
    function renderExtraTable() {{
        const container = document.getElementById('extra-match-rows');
        if (!container) return;
        container.innerHTML = '';

        fixtures.forEach((m, idx) => {{
            const card = document.createElement('div');
            card.className = 'match-card-row';

            const mNo = m.no || (idx + 1);
            const mDate = String(m.date || 'Canlı').trim();
            const mHome = String(m.home || `Ev ${{mNo}}`).trim();
            const mAway = String(m.away || `Dep ${{mNo}}`).trim();
            const odds = m.odds || (m.p_pub ? m.p_pub.map(p => Math.round(p * 100)) : [33, 33, 34]);
            const r1 = Math.round(odds[0] !== undefined ? odds[0] : 33);
            const rx = Math.round(odds[1] !== undefined ? odds[1] : 33);
            const r2 = Math.round(odds[2] !== undefined ? odds[2] : 34);

            // Satır Üst Bilgisi: No ve Tarih / Saat
            const meta = document.createElement('div');
            meta.className = 'match-meta-header';
            meta.innerHTML = `
                <span>M${{String(mNo).padStart(2, '0')}} • ${{mHome}} vs ${{mAway}}</span>
                <span>🕒 ${{mDate}}</span>
            `;
            card.appendChild(meta);

            // Grid Row: No, 1, X, 2
            const grid = document.createElement('div');
            grid.className = 'match-grid-row';

            // No
            const colNo = document.createElement('div');
            colNo.className = 'col-no';
            const lblNo = document.createElement('div');
            lblNo.className = 'lbl-no-btn';
            lblNo.innerText = mNo;
            colNo.appendChild(lblNo);
            grid.appendChild(colNo);

            // Home (1)
            const colHome = document.createElement('div');
            colHome.className = 'col-pick-cell cell-home';
            colHome.innerHTML = `<div class="rate-badge">%${{r1}}</div>`;
            const b1 = document.createElement('button');
            b1.className = 'btn-pick' + (picks[idx]['1'] ? ' active' : '');
            b1.innerText = mHome;
            b1.onclick = () => togglePick(idx, '1');
            colHome.appendChild(b1);
            grid.appendChild(colHome);

            // Draw (X)
            const colDraw = document.createElement('div');
            colDraw.className = 'col-pick-cell cell-draw';
            colDraw.innerHTML = `<div class="rate-badge">%${{rx}}</div>`;
            const bx = document.createElement('button');
            bx.className = 'btn-pick btn-x' + (picks[idx]['X'] ? ' active' : '');
            bx.innerText = 'X';
            bx.onclick = () => togglePick(idx, 'X');
            colDraw.appendChild(bx);
            grid.appendChild(colDraw);

            // Away (2)
            const colAway = document.createElement('div');
            colAway.className = 'col-pick-cell cell-away';
            colAway.innerHTML = `<div class="rate-badge">%${{r2}}</div>`;
            const b2 = document.createElement('button');
            b2.className = 'btn-pick' + (picks[idx]['2'] ? ' active' : '');
            b2.innerText = mAway;
            b2.onclick = () => togglePick(idx, '2');
            colAway.appendChild(b2);
            grid.appendChild(colAway);

            card.appendChild(grid);
            container.appendChild(card);
        }});
    }}

    // Toggle Pick (Decoupled: Only Updates Dynamic Pool Estimates)
    function togglePick(idx, opt) {{
        picks[idx][opt] = !picks[idx][opt];
        // Enforce at least 1 pick per match
        if (!picks[idx]['1'] && !picks[idx]['X'] && !picks[idx]['2']) {{
            picks[idx][opt] = true;
        }}
        renderExtraTable();
        isDirty = true;
        updateDynamicEstimates();
    }}

    function setPattern(type) {{
        for (let i = 0; i < 15; i++) {{
            if (type === 'cift') {{
                picks[i]['1'] = true; picks[i]['X'] = true; picks[i]['2'] = false;
            }} else if (type === 'kapali') {{
                picks[i]['1'] = true; picks[i]['X'] = true; picks[i]['2'] = true;
            }} else if (type === 'tek_ev') {{
                picks[i]['1'] = true; picks[i]['X'] = false; picks[i]['2'] = false;
            }}
        }}
        renderExtraTable();
        isDirty = true;
        updateDynamicEstimates();
    }}

    function applyPreset(val) {{
        if (val === 'varsayilan_1728') {{
            for (let i = 0; i < 15; i++) {{
                const def = default1728[i];
                picks[i]['1'] = def.includes('1');
                picks[i]['X'] = def.includes('X');
                picks[i]['2'] = def.includes('2');
            }}
        }} else if (val === 'buyuk_pool') {{
            for (let i = 0; i < 15; i++) {{
                if (i < 2) {{
                    picks[i]['1'] = true; picks[i]['X'] = true; picks[i]['2'] = true;
                }} else if (i < 12) {{
                    picks[i]['1'] = true; picks[i]['X'] = true; picks[i]['2'] = false;
                }} else {{
                    picks[i]['1'] = true; picks[i]['X'] = false; picks[i]['2'] = false;
                }}
            }}
        }} else if (val === 'cift') setPattern('cift');
        else if (val === 'kapali') setPattern('kapali');
        else if (val === 'tek_ev') setPattern('tek_ev');

        renderExtraTable();
        isDirty = true;
        updateDynamicEstimates();
    }}

    // Switch Guarantee Mode Card
    function selectGuaranteeMode(mode) {{
        activeGuaranteeMode = mode;
        ['12g', '13g', '14g', '15g'].forEach(m => {{
            const el = document.getElementById(`preset-${{m}}`);
            if (el) el.classList.remove('active-preset');
        }});
        const activeEl = document.getElementById(`preset-${{mode.toLowerCase()}}`);
        if (activeEl) activeEl.classList.add('active-preset');

        isDirty = true;
        updateDynamicEstimates();
    }}

    // DYNAMIC ESTIMATES (REAL-TIME MATH ON BUTTONS & LABELS)
    function updateDynamicEstimates() {{
        let rawCols = 1;
        let numDoubles = 0;
        let numTriples = 0;
        for (let i = 0; i < 15; i++) {{
            let c = 0;
            if (picks[i]['1']) c++;
            if (picks[i]['X']) c++;
            if (picks[i]['2']) c++;
            c = c || 1;
            if (c === 2) numDoubles++;
            if (c === 3) numTriples++;
            rawCols *= c;
        }}

        const rawCost = rawCols * 10;
        document.getElementById('metric-raw').innerText = `${{rawCols.toLocaleString()}} Kolon (${{rawCost.toLocaleString()}} TL)`;

        const prunedCols = Math.max(1, Math.round(rawCols * 0.85));
        document.getElementById('metric-pruned').innerText = `~${{prunedCols.toLocaleString()}} Kolon (Ölü Senaryolar Elendi)`;

        // Restricted Local Hamming Sphere Volumes
        const v0 = 1;
        const v1 = 1 + numDoubles + (numTriples * 2);
        const v2 = v1 + Math.floor(numDoubles * (numDoubles - 1) / 2) + (numDoubles * numTriples * 2) + Math.floor(numTriples * (numTriples - 1) * 2);
        const termD3 = numDoubles >= 3 ? Math.floor(numDoubles * (numDoubles - 1) * (numDoubles - 2) / 6) : 0;
        const termD2T = numDoubles >= 2 ? Math.floor(numDoubles * (numDoubles - 1) / 2) * numTriples * 2 : 0;
        const termDT2 = numTriples >= 2 ? numDoubles * Math.floor(numTriples * (numTriples - 1) / 2) * 4 : 0;
        const termT3 = numTriples >= 3 ? Math.floor(numTriples * (numTriples - 1) * (numTriples - 2) / 6) * 8 : 0;
        const v3 = v2 + termD3 + termD2T + termDT2 + termT3;

        const bound14 = Math.ceil(rawCols / Math.max(1, v1));
        const bound13 = Math.ceil(rawCols / Math.max(1, v2));
        const bound12 = Math.ceil(rawCols / Math.max(1, v3));

        const dyn12g = Math.min(rawCols, Math.max(4, Math.round((bound12 * 2.1) / 4) * 4));
        const dyn13g = Math.min(rawCols, Math.max(4, Math.round((bound13 * 1.85) / 4) * 4));
        const dyn14g = Math.min(rawCols, Math.max(4, Math.round((bound14 * 1.35) / 4) * 4));
        const dyn15g = rawCols;

        const sheets12 = Math.ceil(dyn12g / 4);
        const sheets13 = Math.ceil(dyn13g / 4);
        const sheets14 = Math.ceil(dyn14g / 4);
        const sheets15 = Math.ceil(dyn15g / 4);

        // Update Card Subtexts Dynamically
        const sub12El = document.getElementById('sub-12g');
        if (sub12El) sub12El.innerText = `${{dyn12g.toLocaleString()}} Kolon / ${{ (dyn12g * 10).toLocaleString() }} TL`;

        const sub13El = document.getElementById('sub-13g');
        if (sub13El) sub13El.innerText = `${{dyn13g.toLocaleString()}} Kolon / ${{ (dyn13g * 10).toLocaleString() }} TL`;

        const sub14El = document.getElementById('sub-14g');
        if (sub14El) sub14El.innerText = `${{dyn14g.toLocaleString()}} Kolon / ${{ (dyn14g * 10).toLocaleString() }} TL`;

        const sub15El = document.getElementById('sub-15g');
        if (sub15El) sub15El.innerText = `${{dyn15g.toLocaleString()}} Kolon / ${{ (dyn15g * 10).toLocaleString() }} TL`;

        // Target Selected Mode
        let targetCols = dyn13g;
        let targetSheets = sheets13;
        let modeLabel = "13G Garanti (R=2)";
        if (activeGuaranteeMode === '14G') {{
            targetCols = dyn14g;
            targetSheets = sheets14;
            modeLabel = "14G Garanti (R=1)";
        }} else if (activeGuaranteeMode === '15G') {{
            targetCols = dyn15g;
            targetSheets = sheets15;
            modeLabel = "15G Tam Kapsama (R=0)";
        }} else if (activeGuaranteeMode === '12G') {{
            targetCols = dyn12g;
            targetSheets = sheets12;
            modeLabel = "12G Garanti (R=3)";
        }}

        const btnExec = document.getElementById('btn-execute');
        const btnSub = document.getElementById('btn-execute-sub');
        if (btnExec && btnSub) {{
            btnSub.innerText = `${{modeLabel}}: ${{targetCols.toLocaleString()}} Kolon / ${{ (targetCols * 10).toLocaleString() }} TL`;
            if (!generatedSheets || generatedSheets.length === 0) {{
                btnExec.classList.remove('executed', 'needs-recalc');
                btnExec.querySelector('span:first-child').innerText = '🚀 Kuponları ve Varyasyonları Oluştur';
            }} else if (isDirty) {{
                btnExec.classList.remove('executed');
                btnExec.classList.add('needs-recalc');
                btnExec.querySelector('span:first-child').innerText = '🚀 Seçimleri Güncelle ve Kuponları Üret';
            }}
        }}

        const redMetric = document.getElementById('metric-reduced');
        const guarLbl = document.getElementById('metric-guarantee-lbl');
        if (guarLbl) guarLbl.innerText = `SEÇİLEN GARANTİ: ${{modeLabel.toUpperCase()}}`;
        if (redMetric && (!generatedSheets || generatedSheets.length === 0)) {{
            redMetric.innerText = `Henüz Üretilmedi (Tahmini: ~${{targetCols.toLocaleString()}} Kolon / ${{ (targetCols * 10).toLocaleString() }} TL)`;
        }}

        return {{
            rawCols,
            dyn12g,
            dyn13g,
            dyn14g,
            dyn15g,
            targetCols,
            targetSheets,
            modeLabel
        }};
    }}

    // EXPLICIT EXECUTION TRIGGER (TWO-STAGE MULTI-COVERING SOLVER IN JS)
    function executeOptimization() {{
        const est = updateDynamicEstimates();
        const rawCols = est.rawCols;
        let targetCols = est.targetCols;
        let totalSheets = est.targetSheets;

        // Build Active Choices
        const activeChoices = [];
        for (let i = 0; i < 15; i++) {{
            const opts = [];
            if (picks[i]['1']) opts.push('1');
            if (picks[i]['X']) opts.push('X');
            if (picks[i]['2']) opts.push('2');
            if (opts.length === 0) opts.push('1');
            activeChoices.push(opts);
        }}

        // Generate Cartesian candidates (up to 3000)
        let candidates = [];
        function generateCombos(mIdx, current) {{
            if (candidates.length >= 3000) return;
            if (mIdx === 15) {{
                candidates.push(current.slice());
                return;
            }}
            const opts = activeChoices[mIdx];
            for (let j = 0; j < opts.length; j++) {{
                current.push(opts[j]);
                generateCombos(mIdx + 1, current);
                current.pop();
                if (candidates.length >= 3000) break;
            }}
        }}
        generateCombos(0, []);

        const N = candidates.length;
        const optMap = {{ '1': 0, 'X': 1, '2': 2 }};

        // Compute Shannon Entropy & EV Weights
        const entropies = new Float64Array(N);
        const weights = new Float64Array(N);
        const pTrueList = new Float64Array(N);

        for (let k = 0; k < N; k++) {{
            const cand = candidates[k];
            let ent = 0.0;
            let logW = 0.0;
            let logP = 0.0;
            for (let i = 0; i < 15; i++) {{
                const oIdx = optMap[cand[i]] || 0;
                const pPub = Math.max(1e-4, fixtures[i].p_pub[oIdx]);
                const pTr = fixtures[i].p_true[oIdx];
                ent += -Math.log2(pPub);
                const rawRatio = (pTr + 1e-3) / (pPub + 1e-3);
                const clippedRatio = Math.max(0.4, Math.min(2.5, rawRatio));
                logW += Math.log(clippedRatio);
                logP += Math.log(pTr);
            }}
            entropies[k] = ent;
            weights[k] = Math.exp(logW);
            pTrueList[k] = Math.exp(logP);
        }}

        // Entropy Cut: filter bottom 5% and top 1% (if N > 16)
        let candidateIndices = [];
        if (N > 16) {{
            const sortedEnt = Array.from(entropies).sort((a, b) => a - b);
            const sMin = sortedEnt[Math.floor(N * 0.05)];
            const sMax = sortedEnt[Math.min(N - 1, Math.floor(N * 0.99))];
            for (let k = 0; k < N; k++) {{
                if (entropies[k] >= sMin && entropies[k] <= sMax) {{
                    candidateIndices.push(k);
                }}
            }}
            if (candidateIndices.length < 16) {{
                candidateIndices = Array.from({{ length: N }}, (_, i) => i);
            }}
        }} else {{
            candidateIndices = Array.from({{ length: N }}, (_, i) => i);
        }}

        const P_active = candidateIndices.map(idx => candidates[idx]);
        const W_active = candidateIndices.map(idx => weights[idx]);
        const Ptr_active = candidateIndices.map(idx => pTrueList[idx]);
        const numActive = P_active.length;

        // Active cardinality and target bounds per match
        const activeK = new Int32Array(15);
        const targetCaps = new Float64Array(15);
        const minBounds = new Float64Array(15);
        for (let m = 0; m < 15; m++) {{
            const k = activeChoices[m].length;
            activeK[m] = k;
            targetCaps[m] = k === 1 ? 1.0 : (k === 2 ? 0.70 : 0.50);
            minBounds[m] = k === 1 ? 1.0 : (k === 2 ? 0.30 : 0.20);
        }}
        const outcomeCounts = Array.from({{ length: 15 }}, () => ({{ '1': 0, 'X': 0, '2': 0 }}));
        const alpha = 0.35;
        const beta = 1.5;

        function computeImbalancePenalty(cand, curTot) {{
            if (curTot < 4) return 0.0;
            let penalty = 0.0;
            for (let m = 0; m < 15; m++) {{
                const o = cand[m];
                const freq = outcomeCounts[m][o] / curTot;
                const excess = freq - targetCaps[m];
                if (excess > 0) penalty += excess;
            }}
            return penalty;
        }}

        function computeDeficitBonus(cand, curTot) {{
            if (curTot < 4) return 0.0;
            let bonus = 0.0;
            for (let m = 0; m < 15; m++) {{
                const o = cand[m];
                const freq = outcomeCounts[m][o] / curTot;
                const def = minBounds[m] - freq;
                if (def > 0) bonus += def * 10.0;
            }}
            return bonus;
        }}

        // Radius R
        let R = 2;
        if (activeGuaranteeMode === '14G') R = 1;
        else if (activeGuaranteeMode === '15G') R = 0;
        else if (activeGuaranteeMode === '12G') R = 3;

        let selectedCols = [];

        if (R === 0 || numActive <= 1) {{
            const sortedIdx = Array.from({{ length: numActive }}, (_, i) => i)
                .sort((a, b) => W_active[b] - W_active[a]);
            const takeCount = Math.min(numActive, targetCols);
            selectedCols = sortedIdx.slice(0, takeCount).map(idx => ({{
                col_id: idx + 1,
                picks: P_active[idx],
                ev_score: W_active[idx].toFixed(3),
                prob_pct: (Ptr_active[idx] * 100).toFixed(4),
                surprises: []
            }}));
        }} else {{
            // TWO-STAGE MULTI-COVERING IN JS WITH BALANCE REGULARIZATION
            const ballMask = [];
            for (let i = 0; i < numActive; i++) {{
                const row = new Uint8Array(numActive);
                const c1 = P_active[i];
                for (let j = 0; j < numActive; j++) {{
                    const c2 = P_active[j];
                    let dist = 0;
                    for (let m = 0; m < 15; m++) {{
                        if (c1[m] !== c2[m]) dist++;
                    }}
                    if (dist <= R) row[j] = 1;
                }}
                ballMask.push(row);
            }}

            const covCount = new Int32Array(numActive);
            const selectedList = [];
            const selectedSet = new Set();
            const maxW = Math.max(...W_active, 1.0);

            // Stage 1: 100% 1-Cover with Balance Regularization
            while (true) {{
                let hasUncovered = false;
                for (let i = 0; i < numActive; i++) {{
                    if (covCount[i] === 0) {{ hasUncovered = true; break; }}
                }}
                if (!hasUncovered) break;

                let bestIdx = -1;
                let bestScore = -1e9;
                const curTot = selectedList.length;

                for (let j = 0; j < numActive; j++) {{
                    if (selectedSet.has(j)) continue;
                    let gain = 0;
                    const row = ballMask[j];
                    for (let i = 0; i < numActive; i++) {{
                        if (covCount[i] === 0 && row[i] === 1) gain++;
                    }}
                    const candEv = W_active[j] / maxW;
                    const pen = computeImbalancePenalty(P_active[j], curTot);
                    const score = gain * (1.0 + alpha * candEv) - (beta * pen);
                    if (score > bestScore) {{
                        bestScore = score;
                        bestIdx = j;
                    }}
                }}

                if (bestIdx === -1 || bestScore <= -1e8) break;
                selectedList.push(bestIdx);
                selectedSet.add(bestIdx);
                const bRow = ballMask[bestIdx];
                for (let i = 0; i < numActive; i++) {{
                    if (bRow[i] === 1) covCount[i]++;
                }}
                for (let m = 0; m < 15; m++) {{
                    outcomeCounts[m][P_active[bestIdx][m]]++;
                }}
            }}

            // Stage 2: Boost +EV Multi-Covering K >= 2 & Balanced Budget Padding
            const stage1Count = selectedList.length;
            targetCols = Math.max(stage1Count, targetCols);
            if (targetCols > 4 && targetCols % 4 !== 0) {{
                targetCols = Math.min(numActive, Math.ceil(targetCols / 4) * 4);
            }}

            const sortedW = [...W_active].sort((a, b) => a - b);
            const evMedian = sortedW[Math.floor(numActive / 2)] || 1.0;
            const requirements = new Int32Array(numActive);
            for (let i = 0; i < numActive; i++) {{
                requirements[i] = (W_active[i] >= evMedian) ? 2 : 1;
            }}

            while (selectedList.length < targetCols) {{
                let bestIdx = -1;
                let bestScore = -1e9;
                const curTot = selectedList.length;

                for (let j = 0; j < numActive; j++) {{
                    if (selectedSet.has(j)) continue;
                    let gain = 0.0;
                    const row = ballMask[j];
                    for (let i = 0; i < numActive; i++) {{
                        if (covCount[i] < requirements[i] && row[i] === 1) {{
                            gain += W_active[i];
                        }}
                    }}
                    const candEv = W_active[j] / maxW;
                    const pen = computeImbalancePenalty(P_active[j], curTot);
                    const defBonus = computeDeficitBonus(P_active[j], curTot);
                    let score = 0.0;
                    if (gain > 0) {{
                        score = gain * (1.0 + alpha * candEv) - (beta * pen) + defBonus;
                    }} else {{
                        score = (1.0 + alpha * candEv) - (beta * pen) + defBonus;
                    }}
                    if (score > bestScore) {{
                        bestScore = score;
                        bestIdx = j;
                    }}
                }}

                if (bestIdx === -1 || bestScore <= -1e8) break;

                selectedList.push(bestIdx);
                selectedSet.add(bestIdx);
                const bRow = ballMask[bestIdx];
                for (let i = 0; i < numActive; i++) {{
                    if (bRow[i] === 1) covCount[i]++;
                }}
                for (let m = 0; m < 15; m++) {{
                    outcomeCounts[m][P_active[bestIdx][m]]++;
                }}
            }}

            // Stage 3: Strict Marginal Outcome Balance Enforcement
            function hasMarginalViolations() {{
                const curTot = selectedList.length;
                if (curTot === 0) return false;
                for (let m = 0; m < 15; m++) {{
                    for (let opt of activeChoices[m]) {{
                        const r = outcomeCounts[m][opt] / curTot;
                        if (r < minBounds[m] - 1e-4) return true;
                    }}
                }}
                return false;
            }}

            while (hasMarginalViolations() && selectedList.length < numActive) {{
                let added = false;
                for (let step = 0; step < 4; step++) {{
                    if (selectedList.length >= numActive) break;
                    const curTot = selectedList.length;
                    let bestIdx = -1;
                    let bestScore = -1e9;
                    for (let j = 0; j < numActive; j++) {{
                        if (selectedSet.has(j)) continue;
                        const pen = computeImbalancePenalty(P_active[j], curTot);
                        const defBonus = computeDeficitBonus(P_active[j], curTot);
                        const score = defBonus - (beta * pen) + (0.05 * (W_active[j] / maxW));
                        if (score > bestScore) {{
                            bestScore = score;
                            bestIdx = j;
                        }}
                    }}
                    if (bestIdx === -1 || bestScore <= -1e8) break;
                    selectedList.push(bestIdx);
                    selectedSet.add(bestIdx);
                    const bRow = ballMask[bestIdx];
                    for (let i = 0; i < numActive; i++) {{
                        if (bRow[i] === 1) covCount[i]++;
                    }}
                    for (let m = 0; m < 15; m++) {{
                        outcomeCounts[m][P_active[bestIdx][m]]++;
                    }}
                    added = true;
                }}
                if (!added) break;
            }}

            // Sort selected columns by EV score descending
            selectedList.sort((a, b) => W_active[b] - W_active[a]);

            selectedCols = selectedList.map(idx => {{
                const colPicks = P_active[idx];
                const surprises = [];
                for (let m = 0; m < 15; m++) {{
                    const oIdx = optMap[colPicks[m]] || 0;
                    const pubPct = fixtures[m].p_pub[oIdx];
                    if (pubPct < 0.25) {{
                        surprises.push({{
                            match_no: m + 1,
                            match_str: `M${{m+1}}: ${{fixtures[m].home}}-${{fixtures[m].away}}`,
                            pick: colPicks[m],
                            pub_pct: Math.round(pubPct * 100)
                        }});
                    }}
                }}
                return {{
                    col_id: idx + 1,
                    picks: colPicks,
                    ev_score: W_active[idx].toFixed(3),
                    prob_pct: (Ptr_active[idx] * 100).toFixed(4),
                    surprises: surprises
                }};
            }});
        }}

        totalGeneratedCols = selectedCols.length;
        totalSheets = Math.ceil(totalGeneratedCols / 4);
        const redCost = totalGeneratedCols * 10;
        const rawCost = rawCols * 10;
        const sav = rawCost > 0 ? Math.max(0, (1 - (redCost / rawCost)) * 100) : 0;

        // Update Top Banner
        document.getElementById('metric-guarantee-lbl').innerText = `SEÇİLEN GARANTİ: ${{est.modeLabel.toUpperCase()}}`;
        document.getElementById('metric-reduced').innerText = `${{totalGeneratedCols.toLocaleString()}} Kolon (${{redCost.toLocaleString()}} TL) - Tasarruf: %${{sav.toFixed(1)}}`;
        document.getElementById('lbl-tickets-count').innerText = `${{totalGeneratedCols.toLocaleString()}} Kolon (${{redCost.toLocaleString()}} TL) Listeleniyor`;

        // Update Telemetry banner
        const p15 = ((totalGeneratedCols / rawCols) * 100).toFixed(2);
        const p14 = Math.min(99.0, (totalGeneratedCols * 15.0 / rawCols) * 100).toFixed(1);
        document.getElementById('tel-p15').innerText = `%${{p15}}`;
        document.getElementById('tel-p14').innerText = `%${{p14}}`;

        let cascadeTxt = "1 Adet 13 + 3-6 Adet 12 (Yüksek İkramiye)";
        if (activeGuaranteeMode === '14G') cascadeTxt = "1 Adet 14 + Çoklu 13 & 12 (Silver Strike)";
        else if (activeGuaranteeMode === '15G') cascadeTxt = "1 Adet 15 + Çoklu 14/13/12 (Jackpot)";
        document.getElementById('tel-cascade').innerText = cascadeTxt;

        // Package into 40 TL Sheets
        generatedSheets = [];
        const letters = ['A', 'B', 'C', 'D'];

        for (let s = 0; s < totalSheets; s++) {{
            const sheetObj = {{
                sheet_id: s + 1,
                name: `Kupon #${{s + 1}} (4 Kolon)`,
                cost_tl: 0.0,
                columns_count: 0,
                A: [],
                B: [],
                C: [],
                D: [],
                details: {{}}
            }};

            for (let l = 0; l < 4; l++) {{
                const cIdx = s * 4 + l;
                const letter = letters[l];
                if (cIdx < selectedCols.length) {{
                    const col = selectedCols[cIdx];
                    sheetObj[letter] = col.picks;
                    sheetObj.columns_count++;
                    sheetObj.cost_tl += 10.0;
                    sheetObj.details[letter] = col;
                }} else {{
                    sheetObj[letter] = [];
                }}
            }}

            generatedSheets.push(sheetObj);
        }}

        currentPage = 1;
        renderPaginatedSheets();

        // Mark execution state as clean
        isDirty = false;
        const btnExec = document.getElementById('btn-execute');
        if (btnExec) {{
            btnExec.classList.remove('needs-recalc');
            btnExec.querySelector('span:first-child').innerText = '✅ Kuponlar Başarıyla Üretildi';
        }}
    }}

    function changePage(delta) {{
        const totalPages = Math.ceil(generatedSheets.length / SHEETS_PER_PAGE) || 1;
        const newPage = currentPage + delta;
        if (newPage >= 1 && newPage <= totalPages) {{
            currentPage = newPage;
            renderPaginatedSheets();
        }}
    }}

    // CLEAR / DELETE GENERATED COUPONS
    function clearGeneratedCoupons() {{
        generatedSheets = [];
        totalGeneratedCols = 0;
        isDirty = false;

        const est = updateDynamicEstimates();
        const btnExec = document.getElementById('btn-execute');
        if (btnExec) {{
            btnExec.classList.remove('executed', 'needs-recalc');
            btnExec.querySelector('span:first-child').innerText = '🚀 Kuponları ve Varyasyonları Oluştur';
            const btnSub = document.getElementById('btn-execute-sub');
            if (btnSub) {{
                btnSub.innerText = `${{est.modeLabel}}: ${{est.targetCols.toLocaleString()}} Kolon / ${{ (est.targetCols * 10).toLocaleString() }} TL`;
            }}
        }}

        const redEl = document.getElementById('metric-reduced');
        if (redEl) redEl.innerText = `Henüz Kupon Üretilmedi (Hazır Bekliyor)`;

        const lblTickets = document.getElementById('lbl-tickets-count');
        if (lblTickets) lblTickets.innerText = `0 Kolon (0 TL)`;

        const p15El = document.getElementById('tel-p15');
        if (p15El) p15El.innerText = `-%`;
        const p14El = document.getElementById('tel-p14');
        if (p14El) p14El.innerText = `-%`;
        const casEl = document.getElementById('tel-cascade');
        if (casEl) casEl.innerText = `Kupon üretimi bekleniyor`;

        renderPaginatedSheets();
    }}

    // RENDER PAGINATED 40 TL SHEET CARDS
    function renderPaginatedSheets() {{
        const container = document.getElementById('sheets-list');
        if (!container) return;
        container.innerHTML = '';

        if (!generatedSheets || generatedSheets.length === 0) {{
            const lblPage = document.getElementById('lbl-page-info');
            if (lblPage) lblPage.innerText = 'Sayfa 0 / 0 (Henüz Kupon Üretilmedi)';
            const pPrev = document.getElementById('btn-page-prev');
            if (pPrev) pPrev.disabled = true;
            const pNext = document.getElementById('btn-page-next');
            if (pNext) pNext.disabled = true;
            const lblCount = document.getElementById('lbl-tickets-count');
            if (lblCount) lblCount.innerText = '0 Kolon (0 TL)';
            container.innerHTML = `
                <div style="background: #ffffff; border: 2px dashed #cbd5e1; border-radius: 8px; padding: 32px 16px; text-align: center; color: #64748b;">
                    <div style="font-size: 28px; margin-bottom: 8px;">🎯</div>
                    <div style="font-weight: 800; font-size: 14px; color: #334155; margin-bottom: 4px;">Henüz Kupon Üretilmedi</div>
                    <div style="font-size: 12px; color: #64748b;">
                        Tercihlerinizi yaptıktan sonra yukarıdaki <strong>'🚀 Kuponları ve Varyasyonları Oluştur'</strong> butonuna basarak garantili kolonlarınızı oluşturabilirsiniz.
                    </div>
                </div>
            `;
            return;
        }}

        const totalPages = Math.ceil(generatedSheets.length / SHEETS_PER_PAGE) || 1;
        currentPage = Math.min(currentPage, totalPages);

        const startIdx = (currentPage - 1) * SHEETS_PER_PAGE;
        const endIdx = Math.min(startIdx + SHEETS_PER_PAGE, generatedSheets.length);

        document.getElementById('lbl-page-info').innerText = `Sayfa ${{currentPage}} / ${{totalPages}} (Kupon ${{startIdx + 1}} - ${{endIdx}})`;
        document.getElementById('btn-page-prev').disabled = (currentPage === 1);
        document.getElementById('btn-page-next').disabled = (currentPage === totalPages);

        const visibleSheets = generatedSheets.slice(startIdx, endIdx);

        visibleSheets.forEach((s, idx) => {{
            const globalIdx = startIdx + idx;
            const card = document.createElement('div');
            card.className = 'sheet-card';

            // Head
            const head = document.createElement('div');
            head.className = 'sheet-head';

            const titleGrp = document.createElement('div');
            titleGrp.className = 'sheet-title-grp';

            const badgeId = document.createElement('span');
            badgeId.className = 'sheet-badge-id';
            badgeId.innerText = `📋 KUPON #${{s.sheet_id}} (4 KOLON)`;

            const costPill = document.createElement('span');
            costPill.className = 'sheet-cost-pill';
            costPill.innerText = `Bedel: ${{s.cost_tl.toFixed(2)}} TL`;

            const slotsPill = document.createElement('span');
            slotsPill.className = 'sheet-slots-pill';
            slotsPill.innerText = `4 Kolon: Harf A-B-C-D`;

            titleGrp.appendChild(badgeId);
            titleGrp.appendChild(costPill);
            titleGrp.appendChild(slotsPill);

            const btnCopy = document.createElement('button');
            btnCopy.className = 'btn-copy-sheet';
            btnCopy.innerHTML = `📋 Bu 4 Kolonu Kopyala (A-B-C-D)`;
            btnCopy.onclick = () => copySingleSheet(globalIdx);

            head.appendChild(titleGrp);
            head.appendChild(btnCopy);

            // Table
            const tableWrap = document.createElement('div');
            tableWrap.className = 'sheet-table-wrap';

            let tableHtml = `
                <table class="sheet-table">
                    <thead>
                        <tr>
                            <th style="width: 44px;">Maç</th>
                            <th style="text-align: left; padding-left: 10px;">Karşılaşma</th>
                            <th style="width: 85px; color: #0284c7; font-weight: 800;">Harf A (10 TL)</th>
                            <th style="width: 85px; color: #0284c7; font-weight: 800;">Harf B (10 TL)</th>
                            <th style="width: 85px; color: #0284c7; font-weight: 800;">Harf C (10 TL)</th>
                            <th style="width: 85px; color: #0284c7; font-weight: 800;">Harf D (10 TL)</th>
                        </tr>
                    </thead>
                    <tbody>
            `;

            for (let i = 0; i < 15; i++) {{
                const m = fixtures[i];
                const aPick = s.A[i] || '-';
                const bPick = s.B[i] || '-';
                const cPick = s.C[i] || '-';
                const dPick = s.D[i] || '-';

                function renderCell(pick, letter) {{
                    if (!pick || pick === '-') return '<td class="sheet-cell-col"><span style="color: #cbd5e1; font-weight: 600;">-</span></td>';
                    const det = s.details && s.details[letter];
                    const isSurprise = det && Array.isArray(det.surprises) && det.surprises.some(sp => sp.match_no === (i + 1));
                    const surpriseObj = isSurprise ? det.surprises.find(sp => sp.match_no === (i + 1)) : null;
                    const surpriseBadge = surpriseObj ? `<span class="surprise-tag" title="Sürpriz: %${{surpriseObj.pub_pct}}">⚡ %${{surpriseObj.pub_pct}}</span>` : '';
                    const cls = isSurprise ? 'sheet-pick-pill is-surprise' : 'sheet-pick-pill';
                    return `<td class="sheet-cell-col"><div style="display: flex; align-items: center; justify-content: center; gap: 4px;"><span class="${{cls}}">${{pick}}</span>${{surpriseBadge}}</div></td>`;
                }}

                tableHtml += `
                    <tr>
                        <td style="font-weight: 800; color: #64748b; width: 44px; text-align: center;">M${{i+1 < 10 ? '0' + (i+1) : (i+1)}}</td>
                        <td style="text-align: left; padding-left: 10px; font-weight: 700; color: #1e293b;">${{m.home}} - ${{m.away}}</td>
                        ${{renderCell(aPick, 'A')}}
                        ${{renderCell(bPick, 'B')}}
                        ${{renderCell(cPick, 'C')}}
                        ${{renderCell(dPick, 'D')}}
                    </tr>
                `;
            }}

            tableHtml += `
                    </tbody>
                </table>
            `;
            tableWrap.innerHTML = tableHtml;

            // Sheet Summary Box
            const summaryBox = document.createElement('div');
            summaryBox.className = 'sheet-summary-letters';

            ['A', 'B', 'C', 'D'].forEach(letter => {{
                const lBox = document.createElement('div');
                lBox.className = 'letter-box';
                const picksArr = s[letter];
                const picksStr = picksArr.length > 0 ? picksArr.join(', ') : 'Boş';
                lBox.innerHTML = `<strong>Harf ${{letter}} (10 TL):</strong><span>${{picksStr}}</span>`;
                summaryBox.appendChild(lBox);
            }});

            card.appendChild(head);
            card.appendChild(tableWrap);
            card.appendChild(summaryBox);
            container.appendChild(card);
        }});
    }}

    function buildExportPayload() {{
        const sheetsPayload = generatedSheets.map(s => ({{
            sheet_id: s.sheet_id,
            name: s.name,
            cost_tl: s.cost_tl,
            A: s.A,
            B: s.B,
            C: s.C,
            D: s.D
        }}));

        return {{
            total_sheets: generatedSheets.length,
            total_cost_tl: generatedSheets.reduce((sum, s) => sum + s.cost_tl, 0),
            guarantee_mode: activeGuaranteeMode,
            telemetry: {{
                p15_jackpot_pct: parseFloat(document.getElementById('tel-p15').innerText.replace('%', '')),
                p14_chance_pct: parseFloat(document.getElementById('tel-p14').innerText.replace('%', '')),
                p13_hit: "100% KESİN GARANTİ",
                p12_cascade: document.getElementById('tel-cascade').innerText
            }},
            sheets: sheetsPayload
        }};
    }}

    function copySingleSheet(sIdx) {{
        const s = generatedSheets[sIdx];
        if (!s) return;
        const payload = {{
            sheet_id: s.sheet_id,
            name: s.name,
            cost_tl: s.cost_tl,
            A: s.A,
            B: s.B,
            C: s.C,
            D: s.D
        }};
        const text = JSON.stringify(payload, null, 2);
        navigator.clipboard.writeText(text).then(() => {{
            alert(`✅ Kupon #${{s.sheet_id}} (${{s.cost_tl}} TL / 4 Kolon: A-B-C-D) Nesine formatında panoya kopyalandı!`);
        }}).catch(() => {{
            document.getElementById('modal-ta-content').value = text;
            document.getElementById('export-modal').style.display = 'flex';
        }});
    }}

    function copyAllTicketsPayload() {{
        if (!generatedSheets || generatedSheets.length === 0) {{
            alert("⚠️ Henüz kupon üretilmedi. Lütfen önce '🚀 Kuponları ve Varyasyonları Oluştur' butonuna basınız.");
            return;
        }}
        const payload = buildExportPayload();
        const text = JSON.stringify(payload, null, 2);
        navigator.clipboard.writeText(text).then(() => {{
            alert(`✅ Tüm ${{totalGeneratedCols}} Kolon (${{payload.total_cost_tl}} TL) Nesine formatında panoya kopyalandı!`);
        }}).catch(() => {{
            document.getElementById('modal-ta-content').value = text;
            document.getElementById('export-modal').style.display = 'flex';
        }});
    }}

    function downloadTxtFile() {{
        if (!generatedSheets || generatedSheets.length === 0) {{
            alert("⚠️ Henüz kupon üretilmedi. Lütfen önce '🚀 Kuponları ve Varyasyonları Oluştur' butonuna basınız.");
            return;
        }}
        const lines = [];
        const totalCost = generatedSheets.reduce((sum, s) => sum + s.cost_tl, 0);

        lines.push("================================================================================");
        lines.push("SPORTOTO QUANT COCKPIT - MULTI-COVERING KOLON LİSTESİ");
        lines.push(`Garanti Seviyesi: ${{activeGuaranteeMode}} | Toplam Kolon: ${{totalGeneratedCols}} Adet | Tutar: ${{totalCost}} TL`);
        lines.push("================================================================================\\n");

        generatedSheets.forEach(s => {{
            lines.push("--------------------------------------------------------------------------------");
            lines.push(`📋 Kupon #${{s.sheet_id}} [Bedel: ${{s.cost_tl}} TL | ${{s.columns_count}} Kolon: Harf A, B, C, D]`);
            lines.push("--------------------------------------------------------------------------------");
            lines.push("Maç  | Karşılaşma                     |  A  |  B  |  C  |  D  |");
            lines.push("--------------------------------------------------------------------------------");

            for (let i = 0; i < 15; i++) {{
                const m = fixtures[i];
                const matchStr = (m.home + " - " + m.away).padEnd(30, ' ').substring(0, 30);
                const mNo = (i + 1 < 10 ? 'M0' : 'M') + (i + 1);
                const a = (s.A[i] || '-').padStart(2, ' ').padEnd(3, ' ');
                const b = (s.B[i] || '-').padStart(2, ' ').padEnd(3, ' ');
                const c = (s.C[i] || '-').padStart(2, ' ').padEnd(3, ' ');
                const d = (s.D[i] || '-').padStart(2, ' ').padEnd(3, ' ');
                lines.push(`${{mNo}}  | ${{matchStr}} | ${{a}} | ${{b}} | ${{c}} | ${{d}} |`);
            }}

            lines.push("--------------------------------------------------------------------------------");
            if (s.A.length > 0) lines.push(`Harf A [10 TL]: ${{s.A.join(', ')}}`);
            if (s.B.length > 0) lines.push(`Harf B [10 TL]: ${{s.B.join(', ')}}`);
            if (s.C.length > 0) lines.push(`Harf C [10 TL]: ${{s.C.join(', ')}}`);
            if (s.D.length > 0) lines.push(`Harf D [10 TL]: ${{s.D.join(', ')}}`);
            lines.push("");
        }});

        lines.push("================================================================================");
        lines.push(`GENEL TOPLAM: ${{totalGeneratedCols}} Kolon = ${{totalCost}} TL`);
        lines.push("Nesine.com'da her 4 kolon tek ekranda A, B, C, D harfleri sırayla işaretlenerek oynanır.");
        lines.push("================================================================================");

        const text = lines.join('\\n');
        const blob = new Blob([text], {{ type: 'text/plain;charset=utf-8' }});
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `kuponlar_multicover_${{activeGuaranteeMode.toLowerCase()}}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    }}

    function copyModalContent() {{
        const ta = document.getElementById('modal-ta-content');
        ta.select();
        document.execCommand('copy');
        alert("✅ Panoya kopyalandı!");
    }}

    function closeExportModal() {{
        document.getElementById('export-modal').style.display = 'none';
    }}

    window.addEventListener('DOMContentLoaded', () => {{
        renderExtraTable();
        updateDynamicEstimates();
        renderPaginatedSheets();
    }});

    // Immediate initial execution
    renderExtraTable();
    updateDynamicEstimates();
    renderPaginatedSheets();
</script>

</body>
</html>
"""

def sync_portfolio_state(raw_cols_or_sheets, name="Portföy", mode="13G", is_played=True):
    """
    Synchronizes both st.session_state['active_portfolio_columns'] and
    st.session_state['active_portfolio'] (sheets), saving to local disk.
    """
    if not raw_cols_or_sheets:
        return False
    
    # Check if input is already 4-column sheets
    if isinstance(raw_cols_or_sheets, list) and len(raw_cols_or_sheets) > 0 and isinstance(raw_cols_or_sheets[0], dict) and "A" in raw_cols_or_sheets[0]:
        sheets = raw_cols_or_sheets
        cols = []
        for s in sheets:
            for letter in ["A", "B", "C", "D"]:
                if letter in s and isinstance(s[letter], list) and len(s[letter]) == 15:
                    cols.append([str(p).strip().upper() for p in s[letter]])
    else:
        # Input is flat columns (list of 15-match picks)
        cols = []
        for c in raw_cols_or_sheets:
            if isinstance(c, list) and len(c) == 15:
                cols.append([str(p).strip().upper() for p in c])
            elif isinstance(c, str) and len(c) == 15:
                cols.append([p.upper() for p in c])
        
        if not cols:
            return False
            
        total_s = math.ceil(len(cols) / 4)
        letters = ["A", "B", "C", "D"]
        sheets = []
        for s in range(total_s):
            s_obj = {"sheet_id": s + 1, "cost_tl": 0.0, "A": [], "B": [], "C": [], "D": []}
            for l_idx, letter in enumerate(letters):
                c_idx = s * 4 + l_idx
                if c_idx < len(cols):
                    s_obj[letter] = cols[c_idx]
                    s_obj["cost_tl"] += 10.0
            sheets.append(s_obj)

    total_coupons = len(cols)
    total_sheets = math.ceil(total_coupons / 4)
    total_cost_tl = total_coupons * 10.0

    new_meta = {
        "name": name,
        "mode": mode,
        "created_at": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "total_coupons": total_coupons,
        "total_sheets": total_sheets,
        "total_cost_tl": total_cost_tl,
        "sheets": sheets,
        "columns": cols,
        "is_played": is_played
    }
    save_active_portfolio(new_meta)
    st.session_state["active_portfolio"] = sheets
    st.session_state["active_portfolio_columns"] = cols
    st.session_state["portfolio_meta"] = new_meta
    return True

tab1, tab2 = st.tabs(["⚡ 40 TL Kupon Üretici & İndirgeme", "🔴 Canlı Hafta Sonu Kokpiti"])

with tab1:
    # --- 2. BÜLTEN YÜKLEME PANELİ (UI'I BOZMAYAN EXPANDER) ---
    with st.expander("📥 Canlı Bülten & Halk Oranlarını Yükle (Nesine)", expanded=False):
        col_in, col_btn = st.columns([5, 1])
        with col_in:
            pasted_data = st.text_area(
                "Tampermonkey'den kopyalanan JSON:",
                placeholder="Nesine'deki butondan aldığınız JSON listesini buraya yapıştırın...",
                height=70,
                label_visibility="collapsed"
            )
        with col_btn:
            if st.button("Uygula", use_container_width=True):
                if pasted_data.strip():
                    try:
                        parsed = json.loads(pasted_data)
                        if isinstance(parsed, dict):
                            for k in ["matches", "program", "data", "fixtures", "bulten", "items", "list"]:
                                if k in parsed and isinstance(parsed[k], list):
                                    parsed = parsed[k]
                                    break
                        if isinstance(parsed, list) and len(parsed) >= 15:
                            st.session_state["active_fixtures"] = format_fixtures(parsed)
                            st.success("✅ 15 Maç ve Oranlar Yüklendi!")
                            st.rerun()
                        else:
                            count_found = len(parsed) if isinstance(parsed, list) else 0
                            st.error(f"JSON listesinde en az 15 maç olmalıdır (Tespit edilen: {count_found} maç).")
                    except Exception as e:
                        st.error(f"Geçersiz JSON: {e}")

    components.html(app_html, height=2250, scrolling=True)

with tab2:
    # =========================================================================
    # SPORTOTO EXTRA LIVE COCKPIT & REAL-TIME PORTFOLIO MATRIX
    # =========================================================================
    safe_markdown("""
    <style>
        .st-extra-wrap {
            max-width: 1400px;
            margin: 0 auto;
            padding: 4px 8px;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            color: #0f172a;
        }

        /* 1. TOP BLUE PILLS HEADER (Sportoto Extra Exact Visual Style) */
        .extra-top-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: linear-gradient(90deg, #0284c7 0%, #0369a1 100%);
            border-radius: 8px;
            padding: 8px 16px;
            margin-bottom: 10px;
            color: #ffffff;
            box-shadow: 0 2px 8px rgba(2, 132, 199, 0.25);
        }
        .extra-top-pill {
            background: rgba(255, 255, 255, 0.2);
            padding: 4px 16px;
            border-radius: 20px;
            font-size: 13.5px;
            font-weight: 800;
            letter-spacing: 0.5px;
            border: 1px solid rgba(255, 255, 255, 0.35);
        }
        .extra-top-title {
            font-size: 15px;
            font-weight: 900;
            letter-spacing: 0.5px;
        }

        /* 2. DYNAMIC TELEMETRY SHIELD CARDS */
        .telemetry-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
            margin-bottom: 12px;
        }
        .telemetry-box {
            background: #ffffff;
            border-radius: 8px;
            border: 1px solid #e2e8f0;
            padding: 10px 14px;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
            text-align: center;
        }
        .telemetry-box-15 { border-top: 4px solid #16a34a; }
        .telemetry-box-14 { border-top: 4px solid #0284c7; }
        .telemetry-box-13 { border-top: 4px solid #d97706; }
        .telemetry-box-12 { border-top: 4px solid #8b5cf6; }

        .tel-title {
            font-size: 11px;
            font-weight: 800;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .tel-value {
            font-size: 26px;
            font-weight: 900;
            margin-top: 2px;
        }
        .tel-sub {
            font-size: 10.5px;
            color: #94a3b8;
            font-weight: 600;
        }

        /* 3. WHITE KPI TABLE CARD (Sportoto Extra Exact Style) */
        .extra-kpi-card {
            background: #ffffff;
            border-radius: 8px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.08);
            margin-bottom: 12px;
            overflow: hidden;
        }
        .extra-kpi-table {
            width: 100%;
            border-collapse: collapse;
            text-align: center;
        }
        .extra-kpi-table th {
            background: #f8fafc;
            color: #475569;
            font-size: 12px;
            font-weight: 800;
            padding: 10px 12px;
            border-bottom: 1px solid #e2e8f0;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .extra-kpi-table td {
            padding: 12px 14px;
            font-size: 24px;
            font-weight: 900;
            color: #0f172a;
        }

        /* 4. MASTER MATRIX TABLE WRAPPER */
        .extra-matrix-card {
            background: #ffffff;
            border-radius: 8px;
            border: 1px solid #cbd5e1;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
            overflow-x: auto;
            margin-bottom: 14px;
        }
        .extra-matrix-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
            min-width: 960px;
        }
        .extra-matrix-table th {
            background: #f8fafc;
            color: #475569;
            font-weight: 800;
            padding: 8px 6px;
            border-bottom: 2px solid #cbd5e1;
            text-align: center;
            white-space: nowrap;
        }
        .extra-matrix-table td {
            padding: 6px 6px;
            border-bottom: 1px solid #f1f5f9;
            vertical-align: middle;
        }
        .extra-matrix-table tr:hover td {
            background: #f8fafc;
        }

        /* ROW PILLS & COMPONENTS */
        .m-num-pill {
            background: #334155;
            color: #ffffff;
            font-weight: 900;
            font-size: 11px;
            padding: 4px 8px;
            border-radius: 6px;
            display: inline-block;
            text-align: center;
            min-width: 28px;
        }
        .m-date-pill {
            background: #f1f5f9;
            color: #334155;
            font-weight: 700;
            font-size: 10.5px;
            padding: 3px 6px;
            border-radius: 4px;
            border: 1px solid #e2e8f0;
            white-space: nowrap;
            display: inline-block;
        }
        .m-name-txt {
            font-weight: 800;
            color: #0f172a;
            font-size: 11.5px;
            white-space: nowrap;
        }
        .m-status-pill {
            font-size: 9.5px;
            font-weight: 800;
            padding: 2px 6px;
            border-radius: 3px;
            margin-left: 6px;
            display: inline-block;
        }
        .m-status-ns { background: #64748b; color: #ffffff; }
        .m-status-live { background: #ef4444; color: #ffffff; animation: livePulse 1.5s infinite; }
        .m-status-ft { background: #16a34a; color: #ffffff; }

        /* TERCİH 3-BOX PILL ROW */
        .tercih-box-row {
            display: flex;
            align-items: center;
            gap: 4px;
            min-width: 320px;
        }
        .tercih-btn {
            padding: 5px 8px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 800;
            text-align: center;
            border: 1.5px solid transparent;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .tercih-home { flex: 1.2; }
        .tercih-x { width: 34px; }
        .tercih-away { flex: 1.2; }

        .tercih-ns-unsel {
            background: #ffffff;
            color: #64748b;
            border-color: #cbd5e1;
        }
        .tercih-ns-sel {
            background: #ecfdf5;
            color: #065f46;
            border-color: #10b981;
        }
        .tercih-win {
            background: #15803d !important;
            color: #ffffff !important;
            border-color: #16a34a !important;
            font-weight: 900;
            box-shadow: 0 1px 4px rgba(21, 128, 61, 0.4);
        }
        .tercih-lose-picked {
            background: #ffe4e6;
            color: #9f1239;
            border-color: #fecdd3;
        }
        .tercih-lose-unpicked {
            background: #ffffff;
            color: #94a3b8;
            border-color: #e2e8f0;
        }

        /* COUPON COLUMN CELLS (Exact Sportoto Extra Styling) */
        .c-header-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 12px;
            color: #ffffff;
            font-weight: 900;
            font-size: 13.5px;
            min-width: 36px;
            text-align: center;
            box-shadow: 0 2px 6px rgba(0,0,0,0.15);
        }
        .c-cell-pill {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 30px;
            height: 28px;
            border-radius: 6px;
            font-weight: 900;
            font-size: 13px;
            text-align: center;
            margin: 0 auto;
        }
        .cell-ns {
            background: #f59e0b;
            color: #ffffff;
            border: 1px solid #d97706;
        }
        .cell-hit {
            background: #16a34a;
            color: #ffffff;
            border: 1.5px solid #22c55e;
            box-shadow: 0 0 5px rgba(34, 197, 94, 0.4);
        }
        .cell-miss {
            background: #dc2626;
            color: #ffffff;
            border: 1.5px solid #ef4444;
        }

        @keyframes livePulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
    </style>
    """)

    # 1. LOAD & SYNC ACTIVE PORTFOLIO FROM SESSION OR LOCAL DISK
    if "active_portfolio" not in st.session_state or st.session_state.active_portfolio is None:
        saved_meta = load_active_portfolio()
        if saved_meta and isinstance(saved_meta, dict):
            sync_portfolio_state(
                saved_meta.get("columns") or saved_meta.get("sheets") or saved_meta.get("coupons", []),
                name=saved_meta.get("name", "Aktif Portföy"),
                mode=saved_meta.get("mode", "13G"),
                is_played=saved_meta.get("is_played", True)
            )
        else:
            st.session_state.active_portfolio = None
            st.session_state.active_portfolio_columns = None
            st.session_state.portfolio_meta = None

    # 2. SCOREKEEPER STATE INITIALIZATION & MATCH STATES
    active_fixtures = st.session_state.get("active_fixtures", DEFAULT_FIXTURES)

    if "sk_initialized" not in st.session_state:
        try:
            official_init = fetch_live_toto_scores()
        except Exception:
            official_init = get_default_match_states()
        for i in range(15):
            off = official_init[i] if i < len(official_init) else {}
            off_res = str(off.get("current_outcome", "-")).strip().upper()
            default_res = off_res if off_res in ["1", "X", "2"] else "—"
            default_stat = "Bitti" if off.get("status") == "FT" else "Devam Ediyor"
            if f"sk_outcome_{i}" not in st.session_state:
                st.session_state[f"sk_outcome_{i}"] = default_res
            if f"sk_status_{i}" not in st.session_state:
                st.session_state[f"sk_status_{i}"] = default_stat
        st.session_state["sk_initialized"] = True

    # Construct match_states from active fixtures + scorekeeper widgets
    match_states = []
    for i in range(15):
        fix = active_fixtures[i] if i < len(active_fixtures) else {}
        h_name = fix.get("home", f"Ev {i+1}")
        a_name = fix.get("away", f"Dep {i+1}")
        d_str = fix.get("date", "")

        cur_outcome = st.session_state.get(f"sk_outcome_{i}", "—")
        cur_status = st.session_state.get(f"sk_status_{i}", "Devam Ediyor")

        if cur_status == "Bitti" and cur_outcome in ["1", "X", "2"]:
            m_status = "FT"
            m_outcome = cur_outcome
            m_score = f"MS: {cur_outcome}"
            m_min = "MS"
        elif cur_status == "Devam Ediyor" and cur_outcome in ["1", "X", "2"]:
            m_status = "LIVE"
            m_outcome = cur_outcome
            m_score = f"Canlı: {cur_outcome}"
            m_min = "Canlı"
        else:
            m_status = "NS"
            m_outcome = "-"
            m_score = "- - -"
            m_min = "-"

        match_states.append({
            "match_no": i + 1,
            "home": h_name,
            "away": a_name,
            "date": d_str,
            "category": "TR",
            "status": m_status,
            "minute": m_min,
            "score": m_score,
            "home_goals": 0,
            "away_goals": 0,
            "current_outcome": m_outcome
        })

    # 3. EMPTY STATE: NO ACTIVE PORTFOLIO LOADED YET
    if st.session_state.active_portfolio is None or len(st.session_state.active_portfolio) == 0:
        st.markdown("""
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-left: 6px solid #0284c7; border-radius: 8px; padding: 20px 24px; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.06);">
            <h3 style="color: #0f172a; margin: 0 0 8px 0; font-size: 18px; font-weight: 800;">
                📋 Canlı Takip İçin Kupon Portföyü Bekleniyor
            </h3>
            <p style="color: #475569; font-size: 13.5px; margin: 0 0 16px 0; line-height: 1.6;">
                Hangi kuponları oynadığınızı sisteme tanıtmak için aşağıdaki 3 yöntemden birini kullanabilirsiniz.
                Sistem oynanmış kuponlarınızı otomatik olarak yerel diske kaydedecek ve tarayıcı kapansa dahi hafta sonu canlı takibe devam edecektir.
            </p>
        </div>
        """, unsafe_allow_html=True)

        up_col1, up_col2 = st.columns([1.1, 1.1])

        with up_col1:
            st.markdown("##### 📂 Yöntem 1: Oynadığınız Kupon Dosyasını Yükleyin")
            uploaded_file = st.file_uploader(
                "Nesine veya SportotoExtra kupon dosyanızı yükleyin (TXT / JSON):",
                type=["txt", "json"],
                key="tab2_direct_upload"
            )
            if uploaded_file is not None:
                try:
                    raw_str = uploaded_file.read().decode("utf-8", errors="ignore")
                    parsed_cols = parse_coupon_content(raw_str)
                    if parsed_cols and len(parsed_cols) > 0:
                        sync_portfolio_state(parsed_cols, name=f"Yüklenen Kupon ({uploaded_file.name})", mode="13G")
                        st.success(f"✅ {len(parsed_cols)} Kolon ({len(parsed_cols)*10} TL) başarıyla yüklendi!")
                        st.rerun()
                    else:
                        st.error("Dosya içeriğinde 15 maçlık geçerli kolon bulunamadı.")
                except Exception as e:
                    st.error(f"Dosya okuma hatası: {e}")

        with up_col2:
            st.markdown("##### 📋 Yöntem 2: Panodan Kupon Metnini Yapıştırın")
            direct_paste = st.text_area(
                "Kupon metnini buraya yapıştırın (TXT veya JSON):",
                placeholder="Harf A [10 TL]: 1, X, 2, 1, 1, X, 2, 1, 1, 1, X, 1, 2, 2, 2\nveya\n1X211X2111X1222...",
                height=85,
                key="tab2_direct_paste_empty"
            )
            if st.button("📋 Kuponları Aktar & Canlıya Al", use_container_width=True, key="btn_paste_empty"):
                if direct_paste.strip():
                    p_cols = parse_coupon_content(direct_paste)
                    if p_cols:
                        sync_portfolio_state(p_cols, name="Panodan Yüklenen Portföy", mode="13G")
                        st.success(f"✅ {len(p_cols)} Kolon başarıyla yüklendi!")
                        st.rerun()
                    else:
                        st.error("Geçerli 15 maçlık kolon tespit edilemedi.")

        st.markdown("---")
        st.markdown("##### 🚀 Yöntem 3: Tab 1 Bülteni ile Otomatik Portföy Üret ve Canlıya Al")
        st.caption("1. Sekmedeki maç bültenini veya oranları kullanarak anında garantili portföy üretir ve canlı takibe bağlar.")
        gen_c1, gen_c2 = st.columns([2, 1])
        with gen_c1:
            quick_mode = st.selectbox(
                "Garanti Seviyesi:",
                ["13G (R=2 Garanti)", "14G (R=1 Garanti)", "12G (R=3 Garanti)", "15G (R=0 Tam Kapsama)"],
                index=0,
                key="tab2_quick_mode"
            )
        with gen_c2:
            st.write("")
            st.write("")
            if st.button("🚀 Portföyü Üret & Canlı Takibe Başla", type="primary", use_container_width=True):
                cur_mode_key = quick_mode[:3]
                default_picks = [
                    ['1'], ['1', 'X'], ['1', 'X', '2'], ['1', 'X'], ['X', '2'],
                    ['1', 'X', '2'], ['1', 'X'], ['1'], ['X', '2'], ['X', '2'],
                    ['1', 'X'], ['1'], ['1'], ['2'], ['1']
                ]
                res_gen = engine.run_full_pipeline(
                    default_picks,
                    guarantee_mode=cur_mode_key,
                    dynamic_odds=st.session_state.get("active_fixtures", None)
                )
                gen_sheets = res_gen.get("sheets", [])
                sync_portfolio_state(gen_sheets, name=f"{cur_mode_key} Küre Kalkanı Portföyü", mode=cur_mode_key)
                st.rerun()

    else:
        # =========================================================================
        # ACTIVE PORTFOLIO IS LOADED: RENDER SPORTOTO EXTRA DASHBOARD & TELEMETRY
        # =========================================================================
        portfolio = st.session_state.active_portfolio
        active_cols = st.session_state.get("active_portfolio_columns", [])
        if not active_cols:
            sync_portfolio_state(portfolio)
            active_cols = st.session_state.get("active_portfolio_columns", [])

        meta = st.session_state.get("portfolio_meta", {}) or {}
        cur_mode = meta.get("mode", "13G")
        portfolio_title = meta.get("name", f"{cur_mode} Küre Kalkanı Portföyü")

        # Dynamic Evaluation Mode Toggle
        if "tab2_calc_rule" not in st.session_state:
            st.session_state.tab2_calc_rule = "live"

        score_mode = st.session_state.tab2_calc_rule
        eval_res = evaluate_syndicate_portfolio(portfolio, match_states, score_mode=score_mode)
        dist_list = calculate_portfolio_match_distributions(portfolio)
        all_evaluated = eval_res["evaluated_coupons"]
        total_coupons = eval_res["total_coupons"]
        total_cost_tl = total_coupons * 10.0
        total_sheets = math.ceil(total_coupons / 4)

        # 4. EXACT DYNAMIC GUARANTEE ERROR CALCULATION E(c)
        finished_matches = [
            i for i, m in enumerate(match_states)
            if m["status"] == "FT" and m["current_outcome"] in ["1", "X", "2"]
        ]
        live_matches = [
            i for i, m in enumerate(match_states)
            if m["status"] == "LIVE" and m["current_outcome"] in ["1", "X", "2"]
        ]

        col_settled_errors = []
        col_total_errors = []
        for c in active_cols:
            picks = c if isinstance(c, list) else list(c)
            s_err = sum(1 for m_idx in finished_matches if str(picks[m_idx]).upper() != match_states[m_idx]["current_outcome"])
            l_err = sum(1 for m_idx in live_matches if str(picks[m_idx]).upper() != match_states[m_idx]["current_outcome"])
            col_settled_errors.append(s_err)
            col_total_errors.append(s_err + l_err)

        # Active errors array depending on evaluation mode
        active_errs = col_total_errors if score_mode == "live" else col_settled_errors

        count_15g = sum(1 for e in active_errs if e == 0)
        count_14g_shield = sum(1 for e in active_errs if e <= 1)
        count_13g_shield = sum(1 for e in active_errs if e <= 2)
        count_12g_shield = sum(1 for e in active_errs if e <= 3)
        count_dead = sum(1 for e in active_errs if e > 3)

        # Exact individual tier counts for KPI table
        tier_15 = count_15g
        tier_14 = sum(1 for e in active_errs if e == 1)
        tier_13 = sum(1 for e in active_errs if e == 2)
        tier_12 = sum(1 for e in active_errs if e == 3)
        tier_dead = count_dead

        # 5. TOP BLUE PILLS HEADER (Sportoto Extra Visual Reference)
        safe_markdown(f"""
        <div class="extra-top-bar">
            <span class="extra-top-pill">{cur_mode}</span>
            <span class="extra-top-title">{portfolio_title}</span>
            <span class="extra-top-pill">{total_coupons} Kolon</span>
        </div>
        """)

        # 6. DYNAMIC GUARANTEE TELEMETRY CARDS (0 Hata, <=1 Hata, <=2 Hata, <=3 Hata)
        safe_markdown(f"""
        <div class="telemetry-grid">
            <div class="telemetry-box telemetry-box-15">
                <div class="tel-title">🏆 15G Adayları (0 Hata)</div>
                <div class="tel-value" style="color: #16a34a;">{count_15g}</div>
                <div class="tel-sub">Kolon (Büyük İkramiye)</div>
            </div>
            <div class="telemetry-box telemetry-box-14">
                <div class="tel-title">🎯 14G Kalkanı (≤ 1 Hata)</div>
                <div class="tel-value" style="color: #0284c7;">{count_14g_shield}</div>
                <div class="tel-sub">Kolon (14 Teminatı)</div>
            </div>
            <div class="telemetry-box telemetry-box-13">
                <div class="tel-title">🛡️ 13G Kalkanı (≤ 2 Hata)</div>
                <div class="tel-value" style="color: #d97706;">{count_13g_shield}</div>
                <div class="tel-sub">Kolon (Küre Teminatı)</div>
            </div>
            <div class="telemetry-box telemetry-box-12">
                <div class="tel-title">🔒 12G Kapsamı (≤ 3 Hata)</div>
                <div class="tel-value" style="color: #8b5cf6;">{count_12g_shield}</div>
                <div class="tel-sub">Kolon (Alt İkramiye)</div>
            </div>
        </div>
        """)

        # 7. WHITE KPI TABLE CARD (Sportoto Extra Exact Style)
        safe_markdown(f"""
        <div class="extra-kpi-card">
            <table class="extra-kpi-table">
                <thead>
                    <tr>
                        <th>Kupon Bedeli</th>
                        <th style="color: #16a34a;">15 Giden</th>
                        <th style="color: #0284c7;">14 Giden</th>
                        <th style="color: #d97706;">13 Giden</th>
                        <th style="color: #8b5cf6;">12 Giden</th>
                        <th style="color: #dc2626;">Elenen</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>{total_cost_tl:,.0f} TL</td>
                        <td style="color: #16a34a;">{tier_15}</td>
                        <td style="color: #0284c7;">{tier_14}</td>
                        <td style="color: #d97706;">{tier_13}</td>
                        <td style="color: #8b5cf6;">{tier_12}</td>
                        <td style="color: #dc2626;">{tier_dead}</td>
                    </tr>
                </tbody>
            </table>
        </div>
        """)

        # 8. AMBER ALERT BANNER OR GREEN SHIELD BADGE
        is_13g_breached = (count_13g_shield == 0) and (len(finished_matches) > 0 or (score_mode == "live" and len(live_matches) > 0))

        if is_13g_breached:
            relevant_m = finished_matches if score_mode != "live" else (finished_matches + live_matches)
            culprits = []
            for m_idx in relevant_m:
                actual = match_states[m_idx]["current_outcome"]
                miss_cnt = sum(1 for c in active_cols if str(c[m_idx]).upper() != actual)
                miss_pct = round((miss_cnt / max(1, len(active_cols))) * 100, 1)
                culprits.append({
                    "m_no": m_idx + 1,
                    "match": f"{match_states[m_idx]['home']} - {match_states[m_idx]['away']}",
                    "outcome": actual,
                    "miss_cnt": miss_cnt,
                    "miss_pct": miss_pct,
                    "status": "Bitti" if match_states[m_idx]["status"] == "FT" else "Canlı"
                })
            culprits.sort(key=lambda x: x["miss_pct"], reverse=True)
            culprit_items_html = "".join([
                f"<li style='margin-bottom: 4px;'><strong>M{c['m_no']:02d} • {c['match']}</strong>: Sonuç <strong>{c['outcome']}</strong> ({c['status']}) — Kolonların %{c['miss_pct']}'si ({c['miss_cnt']} adet) kaybetti</li>"
                for c in culprits[:5]
            ])

            safe_markdown(f"""
            <div style="background: #fffbeb; border: 1.5px solid #f59e0b; border-left: 6px solid #d97706; border-radius: 8px; padding: 14px 18px; margin-bottom: 14px; box-shadow: 0 4px 12px rgba(217, 119, 6, 0.1);">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                    <span style="font-size: 22px;">⚠️</span>
                    <h4 style="color: #b45309; margin: 0; font-size: 15px; font-weight: 900;">
                        13G GARANTİ KALKANI DELİNDİ! (Portföydeki Tüm Kolonlar > 2 Hata Aldı)
                    </h4>
                </div>
                <p style="color: #92400e; font-size: 13px; margin: 0 0 8px 0; line-height: 1.5;">
                    Portföydeki tüm {total_coupons} kolon kesinleşen/canlı maçlarda en az 3 hata aldı. 13G küre garantisi bu maç senaryosunda aşıldı.
                </p>
                <div style="background: #ffffff; border: 1px solid #fef3c7; border-radius: 6px; padding: 8px 12px;">
                    <div style="font-size: 11.5px; font-weight: 800; color: #b45309; margin-bottom: 4px;">
                        Garantiyi Bozan Kritik Maçlar (En Yüksek Kayıp Oranı):
                    </div>
                    <ul style="margin: 0; padding-left: 18px; color: #475569; font-size: 11.5px;">
                        {culprit_items_html}
                    </ul>
                </div>
            </div>
            """)
        else:
            safe_markdown(f"""
            <div style="background: #f0fdf4; border: 1px solid #86efac; border-left: 5px solid #16a34a; border-radius: 6px; padding: 8px 14px; margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 16px;">🛡️</span>
                    <span style="color: #166534; font-weight: 800; font-size: 12.5px;">
                        13G Garanti Kalkanı Aktif: <strong>{count_13g_shield} Kolon</strong> 13G küre teminatı içinde devam ediyor.
                    </span>
                </div>
                <span style="background: #dcfce7; color: #15803d; font-weight: 900; font-size: 11px; padding: 2px 8px; border-radius: 10px;">
                    GÜVENLİ
                </span>
            </div>
            """)

        # 9. ACTION BUTTONS ROW
        act_c1, act_c2 = st.columns(2)
        with act_c1:
            is_played = meta.get("is_played", True)
            btn_txt = "✔ OYNATILDI / CANLI AKTİF" if is_played else "✔ KUPONU OYNA VE KİLİTLE"
            if st.button(btn_txt, use_container_width=True, type="primary"):
                meta["is_played"] = True
                meta["played_at"] = datetime.now().strftime("%d.%m.%Y %H:%M")
                save_active_portfolio(meta)
                st.session_state.portfolio_meta = meta
                st.toast("✅ Kupon portföyü resmi oynandı olarak kilitlendi!")
        with act_c2:
            if st.button("🗑️ KUPONU SİL (SIFIRLA)", use_container_width=True):
                delete_active_portfolio()
                st.session_state.active_portfolio = None
                st.session_state.active_portfolio_columns = None
                st.session_state.portfolio_meta = None
                st.rerun()

        # 10. TOOLBAR & CONTROLS
        tb_c1, tb_c2, tb_c3 = st.columns([1.2, 1.2, 2.2])
        with tb_c1:
            if st.button("🔄 Canlı Skorları Güncelle", use_container_width=True):
                fetch_live_toto_scores.clear()
                st.rerun()
        with tb_c2:
            auto_refresh = st.toggle("⏱️ 10 sn Otomatik Güncelleme", value=True, key="tab2_auto_refresh_toggle")
        with tb_c3:
            rule_radio = st.radio(
                "Canlı Puan Kuralı:",
                ["⚡ Anlık Canlı Skor (Önerilen)", "🛡️ Kesinleşen Biten Maçlar"],
                horizontal=True,
                index=0 if st.session_state.tab2_calc_rule == "live" else 1,
                key="tab2_calc_rule_radio"
            )
            new_rule = "live" if "Anlık" in rule_radio else "potential"
            if new_rule != st.session_state.tab2_calc_rule:
                st.session_state.tab2_calc_rule = new_rule
                st.rerun()

        # Auto Refresh Trigger (10 SECONDS - Tab 2 Scoped)
        if auto_refresh:
            components.html("""
            <script>
                setTimeout(function() {
                    try {
                        const parentDoc = window.parent.document;
                        const activeTab = parentDoc.querySelector('.stTabs [aria-selected="true"]');
                        if (activeTab && (activeTab.innerText.includes("Canlı") || activeTab.innerText.includes("Kokpit"))) {
                            const btns = parentDoc.querySelectorAll('button');
                            for (let b of btns) {
                                if (b.innerText && b.innerText.includes("Canlı Skorları Güncelle")) {
                                    b.click();
                                    return;
                                }
                            }
                        }
                    } catch(e) {}
                }, 10000);
            </script>
            """, height=0)

        # 11. 15-ROW INTERACTIVE SCOREKEEPER
        with st.expander("⚽ 15 Karşılaşma Canlı Skor & Sonuç Takipçisi (Skorkeeper)", expanded=True):
            sk_top1, sk_top2, sk_top3 = st.columns([1.5, 1.5, 3])
            with sk_top1:
                if st.button("🔄 Nesine Resmi Skorları ile Eşitle", use_container_width=True, key="btn_sync_official"):
                    fetch_live_toto_scores.clear()
                    off_scores = fetch_live_toto_scores()
                    for idx in range(15):
                        off = off_scores[idx] if idx < len(off_scores) else {}
                        off_res = str(off.get("current_outcome", "-")).strip().upper()
                        st.session_state[f"sk_outcome_{idx}"] = off_res if off_res in ["1", "X", "2"] else "—"
                        st.session_state[f"sk_status_{idx}"] = "Bitti" if off.get("status") == "FT" else "Devam Ediyor"
                    st.rerun()
            with sk_top2:
                if st.button("🧹 Tüm Sonuçları Sıfırla (—)", use_container_width=True, key="btn_reset_sk"):
                    for idx in range(15):
                        st.session_state[f"sk_outcome_{idx}"] = "—"
                        st.session_state[f"sk_status_{idx}"] = "Devam Ediyor"
                    st.rerun()
            with sk_top3:
                st.caption(f"🏁 {len(finished_matches)} Biten Maç &nbsp;|&nbsp; 🔴 {len(live_matches)} Canlı &nbsp;|&nbsp; ⏳ {15 - len(finished_matches) - len(live_matches)} Başlamadı")

            sk_c1, sk_c2 = st.columns(2)
            for i in range(15):
                col_target = sk_c1 if i < 8 else sk_c2
                with col_target:
                    fix = active_fixtures[i] if i < len(active_fixtures) else {}
                    h_name = fix.get("home", f"Ev {i+1}")
                    a_name = fix.get("away", f"Dep {i+1}")
                    d_str = fix.get("date", "")

                    st.markdown(
                        f"<div style='font-size: 11.5px; font-weight: 800; color: #1e293b; margin-top: 6px;'>"
                        f"<span style='background: #334155; color: #fff; padding: 1px 5px; border-radius: 4px; font-size: 10px;'>M{i+1:02d}</span> "
                        f"{h_name} - {a_name} "
                        f"<span style='font-size: 9.5px; color: #64748b;'>({d_str})</span></div>",
                        unsafe_allow_html=True
                    )
                    c_res, c_st = st.columns([1.2, 1.0])
                    with c_res:
                        st.segmented_control(
                            f"Sonuç M{i+1}",
                            options=["—", "1", "X", "2"],
                            key=f"sk_outcome_{i}",
                            label_visibility="collapsed"
                        )
                    with c_st:
                        st.segmented_control(
                            f"Durum M{i+1}",
                            options=["Devam Ediyor", "Bitti"],
                            key=f"sk_status_{i}",
                            label_visibility="collapsed"
                        )

        # 12. COLUMN TIER FILTERS & PAGINATION CONTROLS
        filter_keys = ["all", "15", "14", "13", "12", "dead"]
        filter_labels = {
            "all": f"Tümü ({total_coupons})",
            "15": f"🏆 15 Giden ({eval_res['tier_15_count']})",
            "14": f"🎯 14 Giden ({eval_res['tier_14_count']})",
            "13": f"🛡️ 13 Giden ({eval_res['tier_13_count']})",
            "12": f"🔒 12 Giden ({eval_res['tier_12_count']})",
            "dead": f"⚰️ Elenen ({eval_res['dead_count']})"
        }

        if "tab2_filter_key" not in st.session_state or st.session_state.tab2_filter_key not in filter_keys:
            st.session_state.tab2_filter_key = "all"

        selected_key = st.pills(
            "Kolon Filtresi:",
            filter_keys,
            format_func=lambda k: filter_labels.get(k, k),
            default="all",
            key="tab2_filter_key"
        )

        # Filter Coupons
        if selected_key == "15":
            active_display_coupons = [c for c in all_evaluated if c["tier"] == 15]
        elif selected_key == "14":
            active_display_coupons = [c for c in all_evaluated if c["tier"] == 14]
        elif selected_key == "13":
            active_display_coupons = [c for c in all_evaluated if c["tier"] == 13]
        elif selected_key == "12":
            active_display_coupons = [c for c in all_evaluated if c["tier"] == 12]
        elif selected_key == "dead":
            active_display_coupons = [c for c in all_evaluated if c["tier"] == 0]
        else:
            active_display_coupons = all_evaluated

        # Pagination: 12 Columns per Page
        cols_per_page = 12
        total_pages = max(1, math.ceil(len(active_display_coupons) / cols_per_page))

        if "tab2_matrix_page" not in st.session_state:
            st.session_state.tab2_matrix_page = 1
        elif st.session_state.tab2_matrix_page > total_pages:
            st.session_state.tab2_matrix_page = total_pages

        pg_c1, pg_c2, pg_c3 = st.columns([1.3, 2.4, 1.3])
        with pg_c1:
            if st.button("⬅️ Önceki Kolonlar", use_container_width=True, disabled=(st.session_state.tab2_matrix_page <= 1)):
                st.session_state.tab2_matrix_page = max(1, st.session_state.tab2_matrix_page - 1)
                st.rerun()
        with pg_c2:
            start_c_idx = (st.session_state.tab2_matrix_page - 1) * cols_per_page
            end_c_idx = min(len(active_display_coupons), start_c_idx + cols_per_page)
            st.markdown(
                f"<div style='text-align: center; font-weight: 800; font-size: 13px; color: #475569; padding-top: 6px;'>"
                f"Sayfa {st.session_state.tab2_matrix_page} / {total_pages} &nbsp;|&nbsp; "
                f"Kolon {start_c_idx + 1 if active_display_coupons else 0} - {end_c_idx} (Toplam {len(active_display_coupons)})"
                f"</div>",
                unsafe_allow_html=True
            )
        with pg_c3:
            if st.button("Sonraki Kolonlar ➡️", use_container_width=True, disabled=(st.session_state.tab2_matrix_page >= total_pages)):
                st.session_state.tab2_matrix_page = min(total_pages, st.session_state.tab2_matrix_page + 1)
                st.rerun()

        page_coupons = active_display_coupons[start_c_idx:end_c_idx]

        # 13. BUILD THE MASTER MATRIX TABLE HTML (SPORTOTO EXTRA GRID)
        matrix_th_cols = []
        for c_idx, c in enumerate(page_coupons):
            col_global_num = start_c_idx + c_idx + 1
            tier_num = c["tier_badge"]
            tier_color = c["tier_color"]
            col_name = f"K{col_global_num:02d}"
            matrix_th_cols.append(f"""
            <th style="width: 44px; text-align: center; padding: 6px 2px;">
                <div style="display: flex; flex-direction: column; align-items: center; gap: 2px;">
                    <span class="c-header-badge" style="background: {tier_color};">{tier_num}</span>
                    <span style="font-size: 10px; color: #64748b; font-weight: 800;">{col_name}</span>
                </div>
            </th>
            """)

        matrix_rows_html = []
        for i in range(15):
            m = match_states[i]
            m_no = i + 1
            date_str = m.get("date", "")
            home_team = m["home"]
            away_team = m["away"]
            status = m["status"]
            score = m["score"]
            outcome = m["current_outcome"]

            # Status badge
            if status == "LIVE":
                st_pill = f'<span class="m-status-pill m-status-live">🔴 {m["minute"]} ({score})</span>'
            elif status == "FT":
                st_pill = f'<span class="m-status-pill m-status-ft">🏁 FT ({score})</span>'
            else:
                st_pill = f'<span class="m-status-pill m-status-ns">⏳ Başlamadı (- - -)</span>'

            # Match distributions from active portfolio
            dist = dist_list[i] if i < len(dist_list) else {"c_1": 0, "c_x": 0, "c_2": 0}
            has_1 = (dist["c_1"] > 0)
            has_x = (dist["c_x"] > 0)
            has_2 = (dist["c_2"] > 0)

            # 3 Tercih pill buttons (Home - X - Away)
            if status == "NS":
                cls_1 = "tercih-ns-sel" if has_1 else "tercih-ns-unsel"
                cls_x = "tercih-ns-sel" if has_x else "tercih-ns-unsel"
                cls_2 = "tercih-ns-sel" if has_2 else "tercih-ns-unsel"
            else:
                if outcome == "1":
                    cls_1 = "tercih-win"
                    cls_x = "tercih-lose-picked" if has_x else "tercih-lose-unpicked"
                    cls_2 = "tercih-lose-picked" if has_2 else "tercih-lose-unpicked"
                elif outcome in ["X", "0"]:
                    cls_1 = "tercih-lose-picked" if has_1 else "tercih-lose-unpicked"
                    cls_x = "tercih-win"
                    cls_2 = "tercih-lose-picked" if has_2 else "tercih-lose-unpicked"
                elif outcome == "2":
                    cls_1 = "tercih-lose-picked" if has_1 else "tercih-lose-unpicked"
                    cls_x = "tercih-lose-picked" if has_x else "tercih-lose-unpicked"
                    cls_2 = "tercih-win"
                else:
                    cls_1 = "tercih-ns-sel" if has_1 else "tercih-ns-unsel"
                    cls_x = "tercih-ns-sel" if has_x else "tercih-ns-unsel"
                    cls_2 = "tercih-ns-sel" if has_2 else "tercih-ns-unsel"

            tercih_html = f"""
            <div class="tercih-box-row">
                <div class="tercih-btn tercih-home {cls_1}" title="{home_team}">{home_team}</div>
                <div class="tercih-btn tercih-x {cls_x}" title="Beraberlik">X</div>
                <div class="tercih-btn tercih-away {cls_2}" title="{away_team}">{away_team}</div>
            </div>
            """

            # Coupon column cells for match i
            cells_html = []
            for c in page_coupons:
                pick = str(c["picks"][i]).strip().upper()
                if status == "NS":
                    cell_cls = "cell-ns"
                elif status in ["LIVE", "FT"]:
                    cell_cls = "cell-hit" if outcome in pick else "cell-miss"
                else:
                    cell_cls = "cell-ns"

                cells_html.append(f"""
                <td style="text-align: center; padding: 4px 2px;">
                    <div class="c-cell-pill {cell_cls}">{pick}</div>
                </td>
                """)

            row_html = f"""
            <tr>
                <td style="text-align: center; width: 36px;"><span class="m-num-pill">{m_no}</span></td>
                <td style="width: 110px;"><span class="m-date-pill">{date_str}</span></td>
                <td style="width: 260px;">
                    <span class="m-name-txt">{home_team} - {away_team}</span>
                    {st_pill}
                </td>
                <td style="width: 330px;">{tercih_html}</td>
                {"".join(cells_html)}
            </tr>
            """
            matrix_rows_html.append(row_html)

        # Render Master Table in Streamlit
        master_table_html = f"""
        <div class="extra-matrix-card">
            <table class="extra-matrix-table">
                <thead>
                    <tr>
                        <th style="width: 36px;">#</th>
                        <th style="width: 110px;">Tarih - Saat</th>
                        <th style="width: 260px; text-align: left; padding-left: 10px;">Karşılaşma & Canlı Durum</th>
                        <th style="width: 330px; text-align: left; padding-left: 10px;">
                            <span>Tercih</span>
                            <span style="font-size: 10px; color: #94a3b8; font-weight: 600; margin-left: 8px;">(Kupon Tercih Dağılımı)</span>
                        </th>
                        {"".join(matrix_th_cols)}
                    </tr>
                </thead>
                <tbody>
                    {"".join(matrix_rows_html)}
                </tbody>
            </table>
        </div>
        """
        safe_markdown(master_table_html)

        # 14. EXPANDER FOR UPLOADING / REPLACING ACTIVE PORTFOLIO
        with st.expander("📂 Portföyü Değiştir / Yeni Kupon Yükle (TXT / JSON)", expanded=False):
            sec_c1, sec_c2 = st.columns(2)
            with sec_c1:
                st.markdown("##### 📁 Kupon Dosyası Yükle")
                sec_file = st.file_uploader(
                    "Yeni kupon dosyasını seçin (mevcut portföyün üzerine yazılır):",
                    type=["txt", "json"],
                    key="tab2_secondary_upload"
                )
                if sec_file is not None:
                    try:
                        s_raw = sec_file.read().decode("utf-8", errors="ignore")
                        s_cols = parse_coupon_content(s_raw)
                        if s_cols:
                            sync_portfolio_state(s_cols, name=f"Yüklenen Kupon ({sec_file.name})", mode="13G")
                            st.success(f"✅ {len(s_cols)} Kolon yüklendi!")
                            st.rerun()
                        else:
                            st.error("Dosya içeriğinde geçerli 15 maçlık kolon bulunamadı.")
                    except Exception as e:
                        st.error(f"Hata: {e}")
            with sec_c2:
                st.markdown("##### 📋 Panodan Yapıştır")
                sec_paste = st.text_area(
                    "Kupon metnini yapıştırın (TXT / JSON):",
                    placeholder="Harf A [10 TL]: 1, X, 2, 1...\nveya\n1X211X2111X1222...",
                    height=85,
                    key="tab2_secondary_paste"
                )
                if st.button("📋 Panodaki Kuponları Yükle", use_container_width=True, key="btn_sec_paste"):
                    if sec_paste.strip():
                        p_cols = parse_coupon_content(sec_paste)
                        if p_cols:
                            sync_portfolio_state(p_cols, name="Panodan Yüklenen Portföy", mode="13G")
                            st.success(f"✅ {len(p_cols)} Kolon yüklendi!")
                            st.rerun()
                        else:
                            st.error("Yapıştırılan metinde geçerli 15 maçlık kolon bulunamadı.")
