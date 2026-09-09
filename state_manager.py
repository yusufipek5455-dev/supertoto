import streamlit as st
import re
import time
import os
import json
from datetime import datetime

DEFAULT_FIXTURES = [
    {"no": 1, "date": "11.09 20:00", "home": "Beşiktaş A.Ş.", "away": "Erzurumspor FK", "odds": [90.0, 7.0, 3.0]},
    {"no": 2, "date": "12.09 17:00", "home": "Eyüpspor", "away": "Çaykur Rizespor A.Ş.", "odds": [23.0, 27.0, 50.0]},
    {"no": 3, "date": "12.09 17:00", "home": "Samsunspor A.Ş.", "away": "Çorum FK", "odds": [58.0, 23.0, 19.0]},
    {"no": 4, "date": "12.09 20:00", "home": "Alanyaspor", "away": "Göztepe A.Ş.", "odds": [42.0, 31.0, 27.0]},
    {"no": 5, "date": "12.09 20:00", "home": "Konyaspor", "away": "Trabzonspor A.Ş.", "odds": [15.0, 18.0, 67.0]},
    {"no": 6, "date": "13.09 17:00", "home": "Gençlerbirliği", "away": "Kasımpaşa A.Ş.", "odds": [46.0, 28.0, 26.0]},
    {"no": 7, "date": "13.09 20:00", "home": "Amed Sportif", "away": "Başakşehir FK", "odds": [35.0, 27.0, 38.0]},
    {"no": 8, "date": "13.09 20:00", "home": "Galatasaray A.Ş.", "away": "Kocaelispor", "odds": [79.0, 15.0, 6.0]},
    {"no": 9, "date": "14.09 20:00", "home": "Gaziantep F.K. A.Ş.", "away": "Fenerbahçe A.Ş.", "odds": [11.0, 15.0, 74.0]},
    {"no": 10, "date": "12.09 16:30", "home": "Augsburg", "away": "B. Leverkusen", "odds": [24.0, 21.0, 55.0]},
    {"no": 11, "date": "11.09 21:45", "home": "Rennes", "away": "Marsilya", "odds": [32.0, 28.0, 40.0]},
    {"no": 12, "date": "12.09 17:00", "home": "Chelsea", "away": "Hull City", "odds": [83.0, 11.0, 6.0]},
    {"no": 13, "date": "13.09 18:30", "home": "Manchester United", "away": "Manchester City", "odds": [23.0, 26.0, 51.0]},
    {"no": 14, "date": "13.09 17:15", "home": "Levante", "away": "Barcelona", "odds": [6.0, 7.0, 87.0]},
    {"no": 15, "date": "12.09 19:00", "home": "Lazio", "away": "AC Milan", "odds": [25.0, 29.0, 46.0]},
]

def format_fixtures(raw_list):
    """
    Ham Nesine / Tampermonkey JSON listesini standart 15 maçlık yapıya dönüştürür.
    Takım isimlerini ve oranları sağlam regex mantığıyla ayrıştırır.
    Nesine API'sinin percentage1/0/2 ve eventDate/eventTime alanlarını öncelikli destekler.
    """
    formatted = []
    for idx, item in enumerate(raw_list[:15]):
        no = item.get("matchNo") or item.get("no") or (idx + 1)
        
        # Tarih ve Saat Ayrıştırma
        ed = item.get("eventDate")
        et = item.get("eventTime")
        if ed and et:
            date_parts = str(ed).strip().split(".")
            if len(date_parts) >= 2:
                day_month = f"{date_parts[0]}.{date_parts[1]}"
                raw_date = f"{day_month} {str(et).strip()}"
            else:
                raw_date = f"{ed} {et}".strip()
        elif ed:
            raw_date = str(ed).strip()
        else:
            raw_date = item.get("date") or item.get("time") or item.get("tarih") or item.get("saat") or "Canlı"
        date = str(raw_date).strip()
        
        # 1. Takım İsimlerini Ayrıştır
        h_name, a_name = "", ""
        
        # A) Açık home/away anahtarları
        for h_key in ["homeTeam", "home", "Home", "ev", "evSahibi", "h", "ev_sahibi"]:
            for a_key in ["awayTeam", "away", "Away", "dep", "deplasman", "a", "deplasman_takimi"]:
                h_val = str(item.get(h_key, "") or "").strip()
                a_val = str(item.get(a_key, "") or "").strip()
                if h_val and a_val:
                    h_name, a_name = h_val, a_val
                    break
            if h_name and a_name:
                break
                
        # B) Tek bir string / liste formatı
        if not (h_name and a_name):
            teams_val = item.get("teams") or item.get("match") or item.get("name") or item.get("karsilasma") or item.get("mac")
            if isinstance(teams_val, (list, tuple)) and len(teams_val) >= 2:
                h_name = str(teams_val[0]).strip()
                a_name = str(teams_val[1]).strip()
            elif teams_val and isinstance(teams_val, str):
                t_str = teams_val.strip()
                lines = [line.strip() for line in t_str.splitlines() if line.strip()]
                if len(lines) >= 2:
                    h_name, a_name = lines[0], lines[1]
                else:
                    parts = re.split(r'\s*[-–—]\s*', t_str, maxsplit=1)
                    if len(parts) >= 2 and parts[0].strip() and parts[1].strip():
                        h_name, a_name = parts[0].strip(), parts[1].strip()
                    else:
                        parts = re.split(r'\s+(?:vs|v|/)\s+|\s*/\s*', t_str, flags=re.IGNORECASE, maxsplit=1)
                        if len(parts) >= 2 and parts[0].strip() and parts[1].strip():
                            h_name, a_name = parts[0].strip(), parts[1].strip()

        # C) Gürültü filtreleme ve boşluk temizliği (Canlı, İY, MS, skor vb.)
        NOISE_REGEX = r'\b(canlı|canli|ilk yarı|ikinci yarı|iy|ms|uzatma|ert|ipt|kırmızı kart|\d+[\'’]|\d+\s*[-–:]\s*\d+)\b'
        if h_name:
            h_name = re.sub(NOISE_REGEX, '', h_name, flags=re.IGNORECASE)
            h_name = " ".join(h_name.split())
        if a_name:
            a_name = re.sub(NOISE_REGEX, '', a_name, flags=re.IGNORECASE)
            a_name = " ".join(a_name.split())
        
        # D) Güvenli yedekleme
        if not h_name or not a_name:
            if idx < len(DEFAULT_FIXTURES):
                h_name = h_name or DEFAULT_FIXTURES[idx]["home"]
                a_name = a_name or DEFAULT_FIXTURES[idx]["away"]
            else:
                h_name = h_name or f"Takım A {idx+1}"
                a_name = a_name or f"Takım B {idx+1}"
        
        # 2. Oranları Çıkar (Nesine API percentage1/percentage0/percentage2 öncelikli)
        p1 = item.get("percentage1")
        p0 = item.get("percentage0")
        p2 = item.get("percentage2")
        
        if p1 is not None and p0 is not None and p2 is not None:
            try:
                odds_val = [float(p1), float(p0), float(p2)]
            except Exception:
                odds_val = None
        else:
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
            
        if sum(odds) <= 0.0 or all(float(x) == 0.0 for x in odds):
            odds = [33.3, 33.3, 33.4]
        elif max(odds) <= 1.0 and sum(odds) <= 1.05:
            odds = [round(o * 100.0, 1) for o in odds]
        else:
            odds = [round(o, 1) for o in odds]
            
        formatted.append({
            "no": int(no),
            "date": date,
            "home": h_name,
            "away": a_name,
            "odds": odds
        })
    return formatted

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
PROGRAM_CACHE_FILE = os.path.join(CACHE_DIR, "nesine_program_cache.json")

def save_program_cache(fixtures: list, program_info: dict):
    """Nesine'den çekilen son geçerli bülteni disk yedeği olarak saklar."""
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        payload = {
            "timestamp": time.time(),
            "date_str": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "program_info": program_info,
            "fixtures": fixtures
        }
        with open(PROGRAM_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def load_program_cache():
    """Disk yedeğindeki son geçerli bülteni yükler."""
    if os.path.exists(PROGRAM_CACHE_FILE):
        try:
            with open(PROGRAM_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None

def fetch_live_bulletin_from_nesine(timeout: float = 4.0, max_retries: int = 3):
    """
    Nesine resmi Spor Toto API'sinden (https://st.nesine.com/v1/Program)
    canlı 15 maçlık bülteni ve kamu dağılım oranlarını çeker.
    Cloudflare / WAF / 403 / 429 kısıtlarına karşı:
    1. User-Agent rotasyonu uygular.
    2. Gecikmeli tekrar denemeler (retry loop) yapar.
    3. Tüm denemeler başarısız olursa son geçerli yerel disk yedeğine (fail-safe snapshot) düşer.
    """
    import urllib.request
    import urllib.error
    import random
    
    last_error = None
    ua_list = list(USER_AGENTS)
    random.shuffle(ua_list)
    
    for attempt in range(min(max_retries, len(ua_list))):
        ua = ua_list[attempt]
        try:
            headers = {
                'User-Agent': ua,
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Origin': 'https://www.nesine.com',
                'Referer': 'https://www.nesine.com/sportoto',
                'Sec-Ch-Ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-site'
            }
            req = urllib.request.Request("https://st.nesine.com/v1/Program", headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as res:
                raw = res.read()
                try:
                    data = json.loads(raw.decode('utf-8'))
                except Exception:
                    data = json.loads(raw.decode('windows-1254', 'ignore'))
                
                d = data.get('d', {})
                matches = d.get('matches', [])
                if matches and len(matches) >= 15:
                    clean_fixtures = format_fixtures(matches[:15])
                    program_info = {
                        "pNo": d.get("pNo"),
                        "week": d.get("week"),
                        "status": d.get("status"),
                        "startDate": d.get("programStartDate"),
                        "endDate": d.get("programEndDate")
                    }
                    # Başarılı bülteni yerel disk yedeği olarak sakla
                    save_program_cache(clean_fixtures, program_info)
                    return {
                        "success": True,
                        "fixtures": clean_fixtures,
                        "program_info": program_info,
                        "is_fallback": False,
                        "fallback_source": None,
                        "error": None
                    }
                else:
                    last_error = f"Beklenen 15 maç bulunamadı (Alınan: {len(matches)} maç)"
        except urllib.error.HTTPError as e:
            last_error = f"HTTP {e.code}: {e.reason}"
            if e.code in [403, 429]:
                time.sleep(0.3)
        except Exception as e:
            last_error = str(e)
            time.sleep(0.2)
            
    # Canlı bağlantı başarısız ise Yerel Disk Yedeği (Fail-Safe Cache) devreye girer
    cached = load_program_cache()
    if cached and cached.get("fixtures") and len(cached["fixtures"]) == 15:
        return {
            "success": True,
            "fixtures": cached["fixtures"],
            "program_info": cached.get("program_info", {}),
            "is_fallback": True,
            "fallback_source": f"Yerel Disk Yedeği ({cached.get('date_str', 'Bilinmeyen Tarih')})",
            "error": f"Canlı API kısıtı ({last_error}), yerel disk snapshot'ı devreye alındı."
        }
        
    # Yerel disk yedeği yoksa DEFAULT_FIXTURES
    return {
        "success": True,
        "fixtures": DEFAULT_FIXTURES,
        "program_info": {
            "pNo": 357,
            "week": 141236,
            "status": True,
            "startDate": "2026-09-11T19:55:00+03:00",
            "endDate": "2026-09-14T21:45:00+03:00"
        },
        "is_fallback": True,
        "fallback_source": "Sistem Varsayılan Fikstürü",
        "error": f"Canlı API kısıtı ({last_error}), varsayılan fikstür devrede."
    }

def export_coupons_txt(columns: list, mode: str = "13G", total_cost: int = None) -> str:
    """
    Her satırda 15 karakterlik (örn. 1X122X11X211121) düz metin çıktısı üretir.
    Kullanıcı çerezleri silinse dahi tek tıkla indirip saklayabilir.
    """
    if not columns:
        return ""
    cost = total_cost if total_cost is not None else len(columns) * 10
    lines = [
        f"# SPOR TOTO {mode.upper()} KUPON PORTFOYU",
        f"# Toplam Kolon: {len(columns)} Adet | Toplam Tutar: {cost:,} TL",
        f"# Format: 15 Karakter Duz Metin (1-X-2)",
        ""
    ]
    for col in columns:
        if isinstance(col, list):
            lines.append("".join(col))
        elif isinstance(col, str):
            lines.append(col)
    return "\n".join(lines)

def export_coupons_csv(columns: list, mode: str = "13G", total_cost: int = None) -> str:
    """
    Excel ve geriye dönük veri analizi için tam CSV formatı üretir.
    """
    if not columns:
        return ""
    header = "Kolon_No,Kupon_Dizilimi,M01,M02,M03,M04,M05,M06,M07,M08,M09,M10,M11,M12,M13,M14,M15"
    csv_lines = [header]
    for idx, col in enumerate(columns):
        col_list = list(col) if isinstance(col, (list, str)) else []
        col_str = "".join(col_list)
        matches_str = ",".join(col_list)
        csv_lines.append(f"{idx + 1},{col_str},{matches_str}")
    return "\n".join(csv_lines)



import json
import os

WORKSPACE_STATE_FILE = "workspace_state.json"

DEFAULT_PICKS = {
    i: ['1', 'X', '2'] if i in [3, 5, 6, 10, 11, 12] 
    else (['X', '2'] if i in [1, 9, 14] 
    else (['1'] if i in [0, 2, 7] else ['2'])) 
    for i in range(15)
}

def sanitize_user_picks(raw_picks):
    """0-14 arası tüm 15 maçın eksiksiz ve integer anahtarlı olmasını garanti eder."""
    normalized = {}
    if not isinstance(raw_picks, dict):
        return {i: list(DEFAULT_PICKS[i]) for i in range(15)}
    
    for i in range(15):
        val = raw_picks.get(i)
        if val is None:
            val = raw_picks.get(str(i))
        if isinstance(val, (list, tuple)):
            clean_list = [str(x).upper() for x in val if str(x).upper() in ['1', 'X', '2', '0']]
            clean_list = ['X' if x == '0' else x for x in clean_list]
            dedup = []
            for c in clean_list:
                if c not in dedup:
                    dedup.append(c)
            normalized[i] = dedup
        else:
            normalized[i] = list(DEFAULT_PICKS[i])
    return normalized

def sanitize_solution(sol):
    """Çözüm objesinin bütünlüğünü garanti eder; eksik anahtarları tamamlar veya geçersizse None döner."""
    if not sol or not isinstance(sol, dict):
        return None
    columns = sol.get("columns", [])
    sheets = sol.get("sheets", [])
    if not columns and not sheets:
        return None
    
    tot_cols = sol.get("total_columns") or len(columns) or (len(sheets) * 4)
    tot_sheets = sol.get("total_sheets") or len(sheets) or ((tot_cols + 3) // 4)
    tot_cost = sol.get("total_cost") or (tot_cols * 10)
    
    sol["total_columns"] = int(tot_cols)
    sol["total_sheets"] = int(tot_sheets)
    sol["total_cost"] = int(tot_cost)
    return sol

def save_workspace_state():
    """Oturum durumunu yerel JSON dosyasına yazarak sekmeler arası ve sert yenileme (Ctrl+F5) kaybını önler."""
    try:
        data = {
            "current_view": st.session_state.get("current_view", "🎯 Kupon Oluşturucu"),
            "fixtures": st.session_state.get("fixtures", DEFAULT_FIXTURES),
            "program_info": st.session_state.get("program_info"),
            "user_picks": {str(k): v for k, v in sanitize_user_picks(st.session_state.get("user_picks")).items()},
            "solution": sanitize_solution(st.session_state.get("solution")),
            "saved_portfolios": st.session_state.get("saved_portfolios", {}),
            "live_scores": st.session_state.get("live_scores", [None] * 15),
            "live_match_details": st.session_state.get("live_match_details", [{"status": "NS", "minute": "-", "score": "- - -", "outcome": "-"} for _ in range(15)]),
            "selected_sheet_idx": st.session_state.get("selected_sheet_idx", 0)
        }
        with open(WORKSPACE_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def load_workspace_state():
    """Yerel JSON dosyasından durumu yükler, dosya yoksa None döner."""
    if os.path.exists(WORKSPACE_STATE_FILE):
        try:
            with open(WORKSPACE_STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    return None
                if "user_picks" in data:
                    data["user_picks"] = sanitize_user_picks(data["user_picks"])
                if "solution" in data:
                    data["solution"] = sanitize_solution(data["solution"])
                if "live_scores" in data and isinstance(data["live_scores"], list):
                    scores = data["live_scores"]
                    data["live_scores"] = [scores[i] if i < len(scores) and scores[i] in ['1', 'X', '2'] else None for i in range(15)]
                if "live_match_details" not in data or not isinstance(data["live_match_details"], list):
                    data["live_match_details"] = [{"status": "NS", "minute": "-", "score": "- - -", "outcome": "-"} for _ in range(15)]
                return data
        except Exception:
            return None
    return None

def init_global_state():
    """Tüm oturum durumlarını tek noktada garantiye alır ve diskten geri yükler."""
    disk_data = load_workspace_state() or {}

    if "current_view" not in st.session_state:
        st.session_state["current_view"] = disk_data.get("current_view", "🎯 Kupon Oluşturucu")
    if "fixtures" not in st.session_state or not st.session_state["fixtures"]:
        loaded_fix = disk_data.get("fixtures", DEFAULT_FIXTURES)
        # Eski bayat oranlar kaydedilmişse (ör. Beşiktaş %78), güncel DEFAULT_FIXTURES ile güncelle
        if loaded_fix and len(loaded_fix) == 15 and loaded_fix[0].get("odds", [0])[0] == 78.0:
            loaded_fix = DEFAULT_FIXTURES
        st.session_state["fixtures"] = loaded_fix
    if "program_info" not in st.session_state:
        st.session_state["program_info"] = disk_data.get("program_info", {
            "pNo": 357,
            "week": 141236,
            "status": True,
            "startDate": "2026-09-11T19:55:00+03:00",
            "endDate": "2026-09-14T21:45:00+03:00"
        })
    if "user_picks" not in st.session_state:
        raw_picks = disk_data.get("user_picks")
        st.session_state["user_picks"] = sanitize_user_picks(raw_picks)
    else:
        st.session_state["user_picks"] = sanitize_user_picks(st.session_state["user_picks"])
        
    if "solution" not in st.session_state:
        st.session_state["solution"] = sanitize_solution(disk_data.get("solution"))
    elif st.session_state["solution"]:
        st.session_state["solution"] = sanitize_solution(st.session_state["solution"])

    if "saved_portfolios" not in st.session_state:
        st.session_state["saved_portfolios"] = disk_data.get("saved_portfolios", {})
    if "live_scores" not in st.session_state:
        st.session_state["live_scores"] = disk_data.get("live_scores", [None] * 15)
    if "live_match_details" not in st.session_state:
        st.session_state["live_match_details"] = disk_data.get("live_match_details", [{"status": "NS", "minute": "-", "score": "- - -", "outcome": "-"} for _ in range(15)])
    if "selected_sheet_idx" not in st.session_state:
        st.session_state["selected_sheet_idx"] = disk_data.get("selected_sheet_idx", 0)

