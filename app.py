import streamlit as st
from state_manager import init_global_state
from views import v_bulten, v_creator, v_vault, v_live

st.set_page_config(
    page_title="SüperToto Terminali",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Global Durumları Başlat
init_global_state()

# Terminal Standartlarında CSS Enjeksiyonu
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@500;700&family=Inter:wght@400;500;600;700;800&display=swap');
    * { font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    code, .mono { font-family: 'JetBrains Mono', monospace !important; }
    
    #MainMenu, header, footer, .stDeployButton {display: none !important;}
    div[data-testid="stToolbar"] {display: none !important;}
    div[data-testid="stDecoration"] {display: none !important;}
    div[data-testid="stStatusWidget"] {display: none !important;}
    
    .block-container {
        padding-top: 0.1rem !important;
        padding-bottom: 0.2rem !important;
        max-width: 99% !important;
    }

    /* Üst Bar Tasarımı */
    .top-navbar-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 6px;
        padding: 2px 12px;
        margin-bottom: 2px;
    }
    .brand-title {
        font-size: 16px;
        font-weight: 800;
        letter-spacing: 0.5px;
        color: #38bdf8;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .brand-status {
        background: #064e3b;
        color: #34d399;
        font-size: 11px;
        padding: 2px 8px;
        border-radius: 12px;
        font-weight: 700;
        border: 1px solid #059669;
    }

    /* 2. Maç Satır Kapsayıcısı */
    .match-row-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #1e293b;
        border: 1px solid #334155;
        border-bottom: none;
        border-radius: 6px 6px 0 0;
        padding: 3px 8px;
        font-size: 11px;
        font-weight: 600;
        color: #94a3b8;
        margin-top: 6px;
    }
    .match-row-header:first-of-type {
        margin-top: 0px;
    }
    .match-row-header .time-tag {
        color: #38bdf8;
        font-family: monospace;
    }

    /* 3. Butonları ve Boşlukları Sıkılaştır */
    div[data-testid="column"] {
        padding: 0px 1px !important;
    }
    
    /* Buton Tasarımları (Trading Terminal Standardı) */
    div.stButton > button {
        border-radius: 0 0 6px 6px !important;
        height: 34px !important;
        min-height: 34px !important;
        padding: 0px 4px !important;
        font-size: 12px !important;
        font-weight: 600 !important;
        transition: all 0.12s ease-in-out !important;
        border: 1px solid #334155 !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }
    
    /* Pasif Butonlar */
    div.stButton > button[kind="secondary"] {
        background-color: #0f172a !important;
        color: #cbd5e1 !important;
    }
    div.stButton > button[kind="secondary"]:hover {
        background-color: #1e293b !important;
        border-color: #64748b !important;
        color: #fff !important;
    }

    /* Aktif Yeşil Butonlar (Neon Kuant Teması) */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(180deg, #059669 0%, #047857 100%) !important;
        border-color: #10b981 !important;
        color: #ffffff !important;
        box-shadow: 0 0 10px rgba(16, 185, 129, 0.3) !important;
    }

    /* Numara Etiketi */
    .match-num-badge {
        background: #090d16;
        border: 1px solid #334155;
        border-radius: 0 0 0 6px;
        color: #38bdf8;
        font-family: monospace;
        font-weight: 700;
        height: 34px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
    }

    /* 40 TL Sheet Kupon Tablosu */
    .sheet-table-wrap {
        background: #0f172a;
        border: 1px solid #334155;
        border-radius: 8px;
        overflow: hidden;
        margin-top: 10px;
        margin-bottom: 12px;
    }
    .sheet-table {
        width: 100%;
        table-layout: fixed;
        border-collapse: collapse;
    }
    .sheet-table th {
        background: #1e293b;
        color: #94a3b8;
        font-size: 11px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding: 8px;
        border-bottom: 1px solid #334155;
        text-align: center;
    }
    .sheet-table td {
        padding: 5px 6px;
        border-bottom: 1px solid #1e293b;
        vertical-align: middle;
        text-align: center;
        font-size: 12px;
        color: #e2e8f0;
    }
    .sheet-table tr:last-child td {
        border-bottom: none;
    }
    .sheet-pill {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 32px;
        height: 28px;
        border-radius: 6px;
        font-weight: 800;
        font-size: 12px;
    }
    .sheet-pill-1 {
        background: rgba(2, 132, 199, 0.2);
        color: #38bdf8;
        border: 1px solid #0284c7;
    }
    .sheet-pill-x {
        background: rgba(217, 119, 6, 0.2);
        color: #fbbf24;
        border: 1px solid #d97706;
    }
    .sheet-pill-2 {
        background: rgba(16, 185, 129, 0.2);
        color: #34d399;
        border: 1px solid #10b981;
    }

    /* Top Radio Segment Styling */
    div[data-testid="stRadio"] > div {
        background: #0f172a;
        padding: 4px;
        border-radius: 8px;
        border: 1px solid #1e293b;
    }
</style>
""", unsafe_allow_html=True)

# Üst Navigasyon Şeridi
nav_col_brand, nav_col_menu = st.columns([2.6, 7.4])

with nav_col_brand:
    st.markdown("""
    <div style="padding-top: 5px;">
        <span style="font-size: 18px; font-weight: 800; color: #38bdf8;">⚡ SÜPERTOTO</span>
        <span style="background: #064e3b; color: #34d399; font-size: 11px; padding: 2px 8px; border-radius: 12px; margin-left: 6px; font-weight: bold; border: 1px solid #059669;">PRO TERMINAL</span>
    </div>
    """, unsafe_allow_html=True)

with nav_col_menu:
    menu_items = [
        "🎯 Kupon Oluşturucu",
        "📥 Canlı Bülten & Oran",
        "💼 Kuponlarım",
        "📊 Canlı Maç Sonuçları"
    ]
    if st.session_state.get("current_view") in ["📊 Canlı Takip Telemetrisi"]:
        st.session_state["current_view"] = "📊 Canlı Maç Sonuçları"
    if st.session_state.get("current_view") in ["💾 Kupon Kasası & Nesine", "💾 Kupon Kasası"]:
        st.session_state["current_view"] = "💼 Kuponlarım"
        
    current_idx = menu_items.index(st.session_state["current_view"]) if st.session_state["current_view"] in menu_items else 0
    selected_tab = st.radio(
        "Navigasyon",
        menu_items,
        index=current_idx,
        horizontal=True,
        label_visibility="collapsed"
    )
    if selected_tab != st.session_state["current_view"]:
        st.session_state["current_view"] = selected_tab
        st.rerun()

st.divider()

# Görünüm Yönlendiricisi (Router)
active_view = st.session_state["current_view"]

if active_view == "🎯 Kupon Oluşturucu":
    v_creator.render()
elif active_view == "📥 Canlı Bülten & Oran":
    v_bulten.render()
elif active_view in ["💼 Kuponlarım", "💾 Kupon Kasası & Nesine"]:
    v_vault.render()
elif active_view in ["📊 Canlı Maç Sonuçları", "📊 Canlı Takip Telemetrisi"]:
    v_live.render()
