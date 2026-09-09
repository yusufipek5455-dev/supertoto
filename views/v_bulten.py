import streamlit as st
import json
import numpy as np
from state_manager import (
    format_fixtures,
    DEFAULT_FIXTURES,
    fetch_live_bulletin_from_nesine,
    save_workspace_state,
    load_program_cache
)

def render():
    st.markdown("### 📥 Canlı Bülten & Nesine Oranları İstasyonu")
    
    prog = st.session_state.get("program_info")
    if not isinstance(prog, dict):
        prog = {}
    p_no = prog.get("pNo", "357")
    week = prog.get("week", "141236")
    start_date = (prog.get("startDate") or "11.09.2026 19:55").replace("T", " ")[:16]
    end_date = (prog.get("endDate") or "14.09.2026 21:45").replace("T", " ")[:16]
    is_fb = st.session_state.get("bulletin_is_fallback", False)
    fb_src = st.session_state.get("bulletin_fallback_source", "Yerel Disk Snapshot'ı")

    # Canlı Durum ve Bilgi Rozeti
    status_dot_color = "#f59e0b" if is_fb else "#10b981"
    status_title = f"🛡️ WAF Koruması Devrede ({fb_src})" if is_fb else "Nesine.com Canlı API Köprüsü (Doğrudan)"
    title_color = "#f59e0b" if is_fb else "#38bdf8"
    
    st.html(f"""
    <div style="background:#0f172a; border:1px solid #1e293b; border-radius:6px; padding:6px 12px; margin-bottom:10px; display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; font-size:12px;">
        <div style="display:flex; align-items:center; gap:8px;">
            <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:{status_dot_color}; box-shadow:0 0 6px {status_dot_color};"></span>
            <span style="font-weight:700; color:{title_color};">{status_title}</span>
            <span style="color:#64748b;">|</span>
            <span style="color:#cbd5e1;">Program No: <strong style="color:#f8fafc;">{p_no}</strong></span>
            <span style="color:#64748b;">|</span>
            <span style="color:#cbd5e1;">Hafta: <strong style="color:#f8fafc;">{week}</strong></span>
        </div>
        <div style="color:#94a3b8; font-size:11px;">
            📅 Başlangıç: {start_date} &nbsp;—&nbsp; Bitiş: {end_date}
        </div>
    </div>
    """)

    # Ana Aksiyon Butonları
    c_btn1, c_btn2, c_btn3 = st.columns([3.5, 2.5, 2.0])
    with c_btn1:
        if st.button("🌐 Nesine'den Canlı Bülteni & Oranları Çek", type="primary", use_container_width=True):
            with st.spinner("Nesine resmi bülteni ve oranları çekiliyor (UA Rotasyonu devrede)..."):
                res = fetch_live_bulletin_from_nesine(timeout=6.0)
                if res["success"]:
                    st.session_state["fixtures"] = res["fixtures"]
                    if res.get("program_info"):
                        st.session_state["program_info"] = res["program_info"]
                    st.session_state["bulletin_is_fallback"] = res.get("is_fallback", False)
                    st.session_state["bulletin_fallback_source"] = res.get("fallback_source", "")
                    save_workspace_state()
                    if res.get("is_fallback"):
                        st.warning(f"🛡️ WAF / Rate-Limit Koruması: {res.get('fallback_source')} otomatik yüklendi.")
                    else:
                        st.toast("⚡ Nesine canlı bülteni ve güncel kamu oranları doğrudan API üzerinden yüklendi!")
                        st.success("✅ 15 Karşılaşma ve Nesine kamu oranları başarıyla güncellendi.")
                    st.rerun()
                else:
                    st.error(f"❌ Nesine bülteni çekilemedi: {res.get('error', 'Bilinmeyen hata')}")

    with c_btn2:
        disk_cache = load_program_cache()
        if disk_cache and disk_cache.get("fixtures"):
            cache_label = f"💾 Disk Yedeğini Yükle ({disk_cache.get('date_str', '')[:10]})"
            if st.button(cache_label, use_container_width=True, help="WAF kısıtında diskteki son başarılı snapshot'ı anında geri yükler"):
                st.session_state["fixtures"] = disk_cache["fixtures"]
                if disk_cache.get("program_info"):
                    st.session_state["program_info"] = disk_cache["program_info"]
                st.session_state["bulletin_is_fallback"] = True
                st.session_state["bulletin_fallback_source"] = f"Yerel Disk Yedeği ({disk_cache.get('date_str', '')})"
                save_workspace_state()
                st.toast("💾 Yerel disk yedeği bültene aktarıldı!")
                st.rerun()
        else:
            if st.button("🔄 Varsayılan Bülteni Yükle", use_container_width=True):
                st.session_state["fixtures"] = DEFAULT_FIXTURES
                st.session_state["bulletin_is_fallback"] = True
                st.session_state["bulletin_fallback_source"] = "Sistem Varsayılan Fikstürü"
                save_workspace_state()
                st.success("Varsayılan bülten yüklendi.")
                st.rerun()

    with c_btn3:
        if st.button("➡️ Kupon Oluşturucuya Geç", type="secondary", use_container_width=True):
            st.session_state["current_view"] = "🎯 Kupon Oluşturucu"
            st.rerun()



    # 15 Maçın Kompakt Kartları
    fixtures = st.session_state.get("fixtures", DEFAULT_FIXTURES)
    if fixtures:
        st.divider()
        st.markdown("<div style='font-size:13px; font-weight:700; color:#f8fafc; margin-bottom:8px;'>📋 Sistemde Aktif Olan 15 Karşılaşma & Nesine Kamu Dağılımı</div>", unsafe_allow_html=True)
        
        fix_cols = st.columns(3)
        for idx, f in enumerate(fixtures):
            c_target = fix_cols[idx % 3]
            odds = f.get("odds", [33.3, 33.3, 33.4])
            
            # Favori vurgusu
            max_idx = int(np.argmax(odds)) if len(odds) == 3 else 0
            
            with c_target:
                st.html(f"""
                <div style="background: #1e293b; border: 1px solid #334155; border-radius: 6px; padding: 6px 10px; margin-bottom: 6px; font-size: 11.5px;">
                    <div style="display: flex; justify-content: space-between; color: #94a3b8; font-weight: 700; font-size: 11px;">
                        <span style="color:#38bdf8;">M{f.get('no', idx+1):02d}</span>
                        <span style="color: #94a3b8;">🕒 {f.get('date', '-')}</span>
                    </div>
                    <div style="color: #f8fafc; font-weight: 700; margin: 3px 0; font-size: 12px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">
                        {f.get('home', '')} <span style="color:#64748b; font-weight:400;">vs</span> {f.get('away', '')}
                    </div>
                    <div style="display:flex; justify-content:space-between; background:#0f172a; border-radius:4px; padding:2px 6px; font-family:monospace; font-size:11px; font-weight:700;">
                        <span style="color:{'#34d399' if max_idx == 0 else '#94a3b8'};">1: %{odds[0]:.0f}</span>
                        <span style="color:{'#34d399' if max_idx == 1 else '#94a3b8'};">X: %{odds[1]:.0f}</span>
                        <span style="color:{'#34d399' if max_idx == 2 else '#94a3b8'};">2: %{odds[2]:.0f}</span>
                    </div>
                </div>
                """)

