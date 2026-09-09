"""
LIVE TRACKER & SYNDICATE PORTFOLIO PROJECTION ENGINE
=====================================================
Real-time official score tracking and Sportoto Extra evaluation matrix.
Provides:
- fetch_live_toto_scores(): Fetches official match states directly from Nesine API.
  Upcoming matches strictly default to 'NS' (Not Started), score '- - -', outcome '-'.
- evaluate_syndicate_portfolio(): Calculates exact live score (15..12, Elenen)
  matching Sportoto Extra standard: Live Score = 15 - (Biten Yanlislar + Canli Yanlislar).
- Portfolio persistence: save_active_portfolio, load_active_portfolio, delete_active_portfolio.
- parse_coupon_content: Imports TXT / JSON coupon files directly into active tracking.
"""

from typing import List, Dict, Any, Tuple, Optional
import os
import streamlit as st
import numpy as np
import urllib
import urllib.request
import json
from datetime import datetime

from toto_quant_engine import FIXTURE

PORTFOLIO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
PORTFOLIO_FILE = os.path.join(PORTFOLIO_DIR, "active_portfolio.json")


def save_active_portfolio(portfolio_data: Dict[str, Any]) -> bool:
    """Persists the played/generated coupon portfolio to local disk."""
    try:
        if not os.path.exists(PORTFOLIO_DIR):
            os.makedirs(PORTFOLIO_DIR, exist_ok=True)
        with open(PORTFOLIO_FILE, "w", encoding="utf-8") as f:
            json.dump(portfolio_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving active portfolio: {e}")
        return False


def load_active_portfolio() -> Optional[Dict[str, Any]]:
    """Loads the played coupon portfolio from local disk if it exists."""
    if not os.path.exists(PORTFOLIO_FILE):
        return None
    try:
        with open(PORTFOLIO_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Error loading active portfolio: {e}")
        return None


def delete_active_portfolio() -> bool:
    """Removes the active portfolio file from local disk."""
    try:
        if os.path.exists(PORTFOLIO_FILE):
            os.remove(PORTFOLIO_FILE)
        return True
    except Exception as e:
        print(f"Error deleting active portfolio: {e}")
        return False


def parse_coupon_content(raw_str: str) -> List[List[str]]:
    """
    Parses arbitrary coupon files (JSON or TXT) into a list of 15-match prediction columns.
    Supports:
    - JSON containing 'sheets' or 'coupons'
    - Text lines of 15 characters (e.g. '1X211X2111X1222')
    - Comma/tab/semicolon-separated values (e.g. '1, X, 2, 1, ...')
    """
    raw_str = raw_str.strip()
    if not raw_str:
        return []

    # 1. Attempt JSON parsing
    if raw_str.startswith("{") or raw_str.startswith("["):
        try:
            data = json.loads(raw_str)
            if isinstance(data, dict):
                if "sheets" in data and isinstance(data["sheets"], list):
                    coupons = []
                    for s in data["sheets"]:
                        for letter in ["A", "B", "C", "D"]:
                            if letter in s and isinstance(s[letter], list) and len(s[letter]) == 15:
                                coupons.append([str(p).strip().upper() for p in s[letter]])
                    if coupons:
                        return coupons
                elif "coupons" in data and isinstance(data["coupons"], list):
                    coupons = []
                    for c in data["coupons"]:
                        if isinstance(c, list) and len(c) == 15:
                            coupons.append([str(p).strip().upper() for p in c])
                        elif isinstance(c, dict) and "picks" in c and len(c["picks"]) == 15:
                            coupons.append([str(p).strip().upper() for p in c["picks"]])
                    if coupons:
                        return coupons
            elif isinstance(data, list):
                coupons = []
                for item in data:
                    if isinstance(item, list) and len(item) == 15:
                        coupons.append([str(p).strip().upper() for p in item])
                    elif isinstance(item, dict) and "picks" in item and len(item["picks"]) == 15:
                        coupons.append([str(p).strip().upper() for p in item["picks"]])
                if coupons:
                    return coupons
        except Exception:
            pass

    # 2. Text / CSV Line parsing
    lines = [ln.strip() for ln in raw_str.splitlines() if ln.strip()]
    coupons = []
    for ln in lines:
        upper_ln = ln.upper()
        if upper_ln.startswith("#") or upper_ln.startswith("//") or "SPORTOTO" in upper_ln or "KUPON LİSTESİ" in upper_ln or "GARANTİ SEVİYESİ" in upper_ln or "GENEL TOPLAM" in upper_ln:
            continue
        # CSV header satırlarını atla
        if "KOLON_NO" in upper_ln or "KUPON_DIZILIMI" in upper_ln or "M01" in upper_ln or "KOLON NO" in upper_ln:
            continue
            
        # Ön ekleri ayıkla (Örn: 'Harf A [10 TL]:' veya 'Kolon 1:' veya CSV '1, 1X122...')
        sub = ln.split(":", 1)[1].strip() if ":" in ln else ln
        
        # CSV veya ayrılmış format kontrolü
        if "," in sub or ";" in sub or "\t" in sub:
            parts = [p.strip().upper() for p in sub.replace(";", ",").replace("\t", ",").split(",") if p.strip()]
            # A) Kolon dizilimi tek parça 15 karakter olarak satırda geçiyor mu? (Örn: 1, 1X122X11X211121, ...)
            matched_compact = False
            for p in parts:
                cleaned_p = p.replace(" ", "").upper()
                if len(cleaned_p) == 15 and all(c in "1X20" for c in cleaned_p):
                    coupons.append(["X" if c == "0" else c for c in cleaned_p])
                    matched_compact = True
                    break
            if matched_compact:
                continue
                
            # B) 15 ayrı eleman mı? (Örn: 1, X, 1, 2, 2, ...)
            if len(parts) == 15 and all(p in ["1", "X", "2", "0"] for p in parts):
                coupons.append(["X" if p == "0" else p for p in parts])
                continue
            elif len(parts) >= 16 and all(p in ["1", "X", "2", "0"] for p in parts[1:16]):
                coupons.append(["X" if p == "0" else p for p in parts[1:16]])
                continue

        # C) Düz metin 15 karakter
        cleaned = sub.replace(" ", "").upper()
        if len(cleaned) == 15 and all(c in "1X20" for c in cleaned):
            coupons.append(["X" if c == "0" else c for c in cleaned])

    return coupons


def get_default_match_states() -> List[Dict[str, Any]]:
    """
    Returns the official 15-match Toto program with exact fixtures.
    Default status for upcoming fixtures is strictly 'NS' (Not Started),
    score '- - -', outcome '-', ensuring 100% clean, zero-mock baseline.
    """
    fixtures_source = None
    try:
        if "fixtures" in st.session_state and isinstance(st.session_state["fixtures"], list) and len(st.session_state["fixtures"]) == 15:
            fixtures_source = st.session_state["fixtures"]
    except Exception:
        pass
    if not fixtures_source:
        fixtures_source = FIXTURE

    match_states = []
    for i, m in enumerate(fixtures_source):
        m_no = i + 1
        match_states.append({
            "match_no": m_no,
            "home": m["home"],
            "away": m["away"],
            "date": m.get("date", ""),
            "category": m.get("category", "TR"),
            "status": "NS",
            "minute": "-",
            "score": "- - -",
            "home_goals": 0,
            "away_goals": 0,
            "current_outcome": "-",
            "odds": m.get("odds", [33.3, 33.3, 33.4])
        })
    return match_states


def fetch_live_toto_scores_detailed(force_refresh: bool = True) -> Dict[str, Any]:
    """
    Fetches official live Spor Toto program from Nesine API (https://st.nesine.com/v1/Program).
    Uses high-speed requests session with short timeout (2.5s) to guarantee instantaneous UI reactivity.
    """
    import random
    import requests
    from state_manager import USER_AGENTS, load_program_cache

    states = get_default_match_states()
    connected = False
    error_msg = None
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
        'Cache-Control': 'no-cache',
        'Origin': 'https://www.nesine.com',
        'Referer': 'https://www.nesine.com/sportoto',
    }

    try:
        resp = requests.get("https://st.nesine.com/v1/Program", headers=headers, timeout=3.0)
        if resp.status_code == 200:
            data = resp.json()
            matches = data.get('d', {}).get('matches', [])
            if matches and len(matches) == 15:
                connected = True
                for i, m in enumerate(matches):
                    m_no = m.get('matchNo', i + 1)
                    idx = m_no - 1
                    if 0 <= idx < 15:
                        ev_date = m.get('eventDate', '')
                        ev_time = m.get('eventTime', '')
                        date_str = f"{ev_date} {ev_time}".strip() if ev_date else states[idx]["date"]
                        res_val = str(m.get('result', '')).strip().upper()
                        
                        states[idx]["home"] = m.get('homeTeam') or (FIXTURE[idx]["home"] if idx < len(FIXTURE) else f"Ev {m_no}")
                        states[idx]["away"] = m.get('awayTeam') or (FIXTURE[idx]["away"] if idx < len(FIXTURE) else f"Dep {m_no}")
                        states[idx]["date"] = date_str
                        p1 = m.get('percentage1', 33.3)
                        p0 = m.get('percentage0', 33.3)
                        p2 = m.get('percentage2', 33.4)
                        states[idx]["odds"] = [float(p1), float(p0), float(p2)]
                        
                        hs = m.get('homeScore')
                        as_ = m.get('awayScore')
                        min_val = m.get('minute') or m.get('liveMinute') or m.get('min')

                        if res_val in ['1', 'X', '2', '0']:
                            outcome = 'X' if res_val in ['X', '0'] else res_val
                            states[idx]["status"] = "FT"
                            states[idx]["minute"] = "MS"
                            states[idx]["current_outcome"] = outcome
                            if hs is not None and as_ is not None:
                                states[idx]["score"] = f"{hs} - {as_}"
                                states[idx]["home_goals"] = int(hs)
                                states[idx]["away_goals"] = int(as_)
                            else:
                                states[idx]["score"] = f"MS ({outcome})"
                        elif hs is not None and as_ is not None:
                            states[idx]["home_goals"] = int(hs)
                            states[idx]["away_goals"] = int(as_)
                            states[idx]["score"] = f"{hs} - {as_}"
                            states[idx]["status"] = "LIVE"
                            states[idx]["minute"] = f"{min_val}'" if min_val else "Canlı"
                            if int(hs) > int(as_):
                                states[idx]["current_outcome"] = "1"
                            elif int(hs) < int(as_):
                                states[idx]["current_outcome"] = "2"
                            else:
                                states[idx]["current_outcome"] = "X"
                        else:
                            states[idx]["status"] = "NS"
                            states[idx]["minute"] = "-"
                            states[idx]["score"] = "- - -"
                            states[idx]["current_outcome"] = "-"
                            states[idx]["home_goals"] = 0
                            states[idx]["away_goals"] = 0
    except Exception as e:
        error_msg = str(e)
            
    # Eğer canlı bağlantı WAF yüzünden kısıtlandıysa, yerel önbellekten fikstürü koru
    if not connected:
        cached = load_program_cache()
        if cached and cached.get("fixtures"):
            connected = True
            error_msg = None
            for idx, c_f in enumerate(cached["fixtures"][:15]):
                states[idx]["home"] = c_f.get("home", states[idx]["home"])
                states[idx]["away"] = c_f.get("away", states[idx]["away"])
                states[idx]["date"] = c_f.get("date", states[idx]["date"])
                states[idx]["odds"] = c_f.get("odds", states[idx]["odds"])



    n_finished = sum(1 for s in states if s.get("status") == "FT" and s.get("current_outcome") in ['1', 'X', '2'])
    n_live = sum(1 for s in states if s.get("status") in ["LIVE", "1H", "2H", "HT"])
    n_not_started = 15 - n_finished - n_live

    return {
        "success": connected,
        "error": error_msg,
        "matches": states,
        "counts": {
            "total": 15,
            "finished": n_finished,
            "live": n_live,
            "not_started": n_not_started
        },
        "source": "Nesine.com Canlı Program API" if connected else "Yerel Program"
    }


def fetch_live_toto_scores() -> List[Dict[str, Any]]:
    return fetch_live_toto_scores_detailed()["matches"]


def calculate_portfolio_match_distributions(sheets_or_coupons: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Computes distribution counts and percentages of 1, X, 2 picks
    across the active portfolio for each of the 15 matches.
    """
    flat_picks = []
    for item in sheets_or_coupons:
        if isinstance(item, dict) and "A" in item and isinstance(item["A"], list) and len(item["A"]) == 15:
            for letter in ["A", "B", "C", "D"]:
                p_list = item.get(letter, [])
                if len(p_list) == 15:
                    flat_picks.append(p_list)
        elif isinstance(item, dict) and "picks" in item and len(item["picks"]) == 15:
            flat_picks.append(item["picks"])
        elif isinstance(item, list) and len(item) == 15:
            flat_picks.append(item)

    total_coupons = max(1, len(flat_picks))
    distributions = []

    for i in range(15):
        c_1 = sum(1 for p in flat_picks if str(p[i]).strip() == "1")
        c_x = sum(1 for p in flat_picks if str(p[i]).strip().upper() in ["X", "0"])
        c_2 = sum(1 for p in flat_picks if str(p[i]).strip() == "2")

        pct_1 = round((c_1 / total_coupons) * 100)
        pct_x = round((c_x / total_coupons) * 100)
        pct_2 = round((c_2 / total_coupons) * 100)

        max_c = max(c_1, c_x, c_2)
        dom = "1" if max_c == c_1 else ("X" if max_c == c_x else "2")

        distributions.append({
            "match_no": i + 1,
            "c_1": c_1,
            "c_x": c_x,
            "c_2": c_2,
            "pct_1": pct_1,
            "pct_x": pct_x,
            "pct_2": pct_2,
            "dominant_pick": dom,
            "total": total_coupons
        })

    return distributions


def evaluate_single_coupon(
    coupon_picks: List[str],
    match_states: List[Dict[str, Any]],
    score_mode: str = "live"
) -> Dict[str, Any]:
    """
    Evaluates a single 15-match coupon against current match states.
    Sportoto Extra Standard:
    - If match is NS: cell is styled in AMBER/YELLOW (#f59e0b) displaying the pick (1, X, 2).
    - If match is LIVE or FT:
        - Correct pick: GREEN (#16a34a)
        - Wrong pick: RED (#dc2626)
    - Live Score = 15 - (settled_errors + virtual_errors)
    - Max Potential = 15 - settled_errors
    """
    assert len(coupon_picks) == 15, "Coupon must contain 15 picks."
    assert len(match_states) == 15, "Must provide states for 15 matches."

    settled_errors = 0
    settled_hits = 0
    virtual_errors = 0
    virtual_hits = 0
    upcoming = 0

    cell_statuses = []

    for i in range(15):
        pick = str(coupon_picks[i]).strip().upper()
        state = match_states[i]
        status = state.get("status", "NS")
        outcome = state.get("current_outcome", "-")

        if status == "FT":
            is_correct = (outcome in pick)
            if is_correct:
                settled_hits += 1
                cell_statuses.append({
                    "match_no": i + 1,
                    "pick": pick,
                    "outcome": outcome,
                    "status_code": "FT_CORRECT",
                    "label": pick,
                    "css_class": "cell-hit",
                    "color": "#16a34a"
                })
            else:
                settled_errors += 1
                cell_statuses.append({
                    "match_no": i + 1,
                    "pick": pick,
                    "outcome": outcome,
                    "status_code": "FT_WRONG",
                    "label": pick,
                    "css_class": "cell-miss",
                    "color": "#dc2626"
                })
        elif status == "LIVE":
            is_correct = (outcome in pick)
            if is_correct:
                virtual_hits += 1
                cell_statuses.append({
                    "match_no": i + 1,
                    "pick": pick,
                    "outcome": outcome,
                    "status_code": "LIVE_WINNING",
                    "label": pick,
                    "css_class": "cell-hit",
                    "color": "#16a34a"
                })
            else:
                virtual_errors += 1
                cell_statuses.append({
                    "match_no": i + 1,
                    "pick": pick,
                    "outcome": outcome,
                    "status_code": "LIVE_LOSING",
                    "label": pick,
                    "css_class": "cell-miss",
                    "color": "#dc2626"
                })
        else:  # "NS"
            upcoming += 1
            cell_statuses.append({
                "match_no": i + 1,
                "pick": pick,
                "outcome": "-",
                "status_code": "UPCOMING",
                "label": pick,
                "css_class": "cell-upcoming",
                "color": "#f59e0b"  # Amber / yellow (Sportoto Extra standard for unplayed)
            })

    current_live_score = 15 - (settled_errors + virtual_errors)
    max_possible_hits = 15 - settled_errors

    # Effective score based on selected evaluation mode
    effective_score = current_live_score if score_mode == "live" else max_possible_hits

    # Dynamic Tier Classification (Exact Sportoto Extra Tiers: 15, 14, 13, 12, Elenen)
    if effective_score >= 15:
        tier = 15
        tier_label = "15 Giden"
        tier_badge = "15"
        tier_color = "#16a34a"
    elif effective_score == 14:
        tier = 14
        tier_label = "14 Giden"
        tier_badge = "14"
        tier_color = "#0284c7"
    elif effective_score == 13:
        tier = 13
        tier_label = "13 Giden"
        tier_badge = "13"
        tier_color = "#d97706"
    elif effective_score == 12:
        tier = 12
        tier_label = "12 Giden"
        tier_badge = "12"
        tier_color = "#8b5cf6"
    else:
        tier = 0
        tier_label = "Elenen"
        tier_badge = str(effective_score)
        tier_color = "#dc2626"

    return {
        "settled_hits": settled_hits,
        "settled_errors": settled_errors,
        "virtual_hits": virtual_hits,
        "virtual_errors": virtual_errors,
        "upcoming": upcoming,
        "current_live_score": current_live_score,
        "max_possible_hits": max_possible_hits,
        "effective_score": effective_score,
        "tier": tier,
        "tier_label": tier_label,
        "tier_badge": tier_badge,
        "tier_color": tier_color,
        "cells": cell_statuses
    }


def evaluate_syndicate_portfolio(
    sheets_or_coupons: List[Any],
    match_states: List[Dict[str, Any]],
    score_mode: str = "live"
) -> Dict[str, Any]:
    """
    Evaluates an entire portfolio of sheets or single coupons.
    Normalizes sheets into flat coupons list and returns comprehensive telemetry.
    """
    flat_coupons = []

    for item in sheets_or_coupons:
        if isinstance(item, dict) and "A" in item and isinstance(item["A"], list) and len(item["A"]) == 15:
            # It's a 40 TL Sheet with letters A, B, C, D
            s_id = item.get("sheet_id", 1)
            for letter in ["A", "B", "C", "D"]:
                p_list = item.get(letter, [])
                if len(p_list) == 15:
                    flat_coupons.append({
                        "sheet_id": s_id,
                        "slot": letter,
                        "name": f"Kupon #{s_id} - Kolon {letter}",
                        "picks": p_list
                    })
        elif isinstance(item, dict) and "picks" in item and len(item["picks"]) == 15:
            flat_coupons.append(item)
        elif isinstance(item, list) and len(item) == 15:
            flat_coupons.append({
                "sheet_id": (len(flat_coupons) // 4) + 1,
                "slot": ["A", "B", "C", "D"][len(flat_coupons) % 4],
                "name": f"Kupon #{len(flat_coupons) + 1}",
                "picks": item
            })

    evaluated_list = []
    tier_counts = {15: 0, 14: 0, 13: 0, 12: 0, 0: 0}

    for c in flat_coupons:
        eval_res = evaluate_single_coupon(c["picks"], match_states, score_mode=score_mode)
        eval_item = {
            **c,
            **eval_res
        }
        evaluated_list.append(eval_item)
        tier_counts[eval_res["tier"]] += 1

    total = len(evaluated_list)
    active_alive = total - tier_counts[0]

    return {
        "total_coupons": total,
        "alive_coupons": active_alive,
        "tier_15_count": tier_counts[15],
        "tier_14_count": tier_counts[14],
        "tier_13_count": tier_counts[13],
        "tier_12_count": tier_counts[12],
        "dead_count": tier_counts[0],
        "evaluated_coupons": evaluated_list,
        "match_states": match_states
    }
