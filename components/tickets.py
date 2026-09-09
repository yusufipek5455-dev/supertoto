"""
COMPONENTS / TICKETS
====================
Exact Nesine Injector Bridge and Multi-Covering Exporter for Official 40 TL Sheets.
Formats JSON payload strictly matching the specification:
{
  "total_sheets": 24,
  "total_cost_tl": 960.0,
  "guarantee_mode": "13G",
  "telemetry": {
    "p15_jackpot_pct": "%5.56",
    "p14_chance_pct": "%83.3",
    "p13_hit": "100% KESİN GARANTİ",
    "p12_cascade": "1 Adet 13 + 3-6 Adet 12 (Kademeli Çoklu İkramiye)"
  },
  "sheets": [
    {
      "sheet_id": 1,
      "cost_tl": 40.0,
      "A": ["1", "X", "1", "2", "1", "X", "2", "1", "1", "1", "X", "1", "2", "2", "2"],
      "B": ["1", "1", "1", "2", "X", "X", "2", "1", "X", "1", "X", "1", "2", "2", "2"],
      "C": ["1", "X", "2", "2", "1", "1", "2", "1", "1", "1", "X", "1", "1", "2", "2"],
      "D": ["1", "X", "1", "X", "1", "X", "2", "1", "1", "1", "2", "1", "2", "2", "2"]
    }
  ]
}
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from toto_quant_engine import FIXTURE


class TicketExporter:
    @staticmethod
    def generate_sheets_payload(
        sheets_data: List[Dict[str, Any]],
        total_cost_tl: Optional[float] = None,
        guarantee_mode: str = "13G",
        preset_mode: Optional[str] = None,
        telemetry: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Formats JSON payload for Nesine Injector using the Multi-Covering 40 TL Sheet architecture.
        Root keys: total_sheets, total_cost_tl, guarantee_mode, telemetry, sheets.
        """
        clean_sheets = []
        total_cost = 0.0

        for s in sheets_data:
            s_cost = float(s.get("cost_tl", 40.0))
            total_cost += s_cost
            clean_sheets.append({
                "sheet_id": s.get("sheet_id", 1),
                "name": s.get("name", f"Kupon #{s.get('sheet_id', 1)} (4 Kolon)"),
                "cost_tl": s_cost,
                "A": s.get("A", []),
                "B": s.get("B", []),
                "C": s.get("C", []),
                "D": s.get("D", [])
            })

        cost = total_cost_tl if total_cost_tl is not None else total_cost
        mode_val = guarantee_mode or preset_mode or "13G"

        return {
            "version": "5.0",
            "generator": "OptimizedSyndicateEngine (Multi-Covering)",
            "timestamp": datetime.now().isoformat(),
            "guarantee_mode": mode_val,
            "total_sheets": len(clean_sheets),
            "total_cost_tl": cost,
            "telemetry": telemetry or {},
            "sheets": clean_sheets
        }

    @staticmethod
    def generate_single_sheet_payload(sheet_obj: Dict[str, Any]) -> Dict[str, Any]:
        """
        Formats a single 40 TL sheet payload for direct injection.
        """
        return {
            "sheet_id": sheet_obj.get("sheet_id", 1),
            "name": sheet_obj.get("name", f"Kupon #{sheet_obj.get('sheet_id', 1)} (4 Kolon)"),
            "cost_tl": float(sheet_obj.get("cost_tl", 40.0)),
            "A": sheet_obj.get("A", []),
            "B": sheet_obj.get("B", []),
            "C": sheet_obj.get("C", []),
            "D": sheet_obj.get("D", [])
        }

    @staticmethod
    def generate_sheets_txt(sheets_data: List[Dict[str, Any]], meta: Optional[Dict[str, Any]] = None) -> str:
        """
        Generates standard tabulated plain TXT output for 40 TL Sheets with cascading telemetry.
        """
        lines = []
        total_sheets = len(sheets_data)
        total_cols = meta.get("reduced_columns", total_sheets * 4) if meta else total_sheets * 4
        total_cost = meta.get("reduced_cost_tl", total_sheets * 40.0) if meta else total_sheets * 40.0
        mode = meta.get("guarantee_mode", meta.get("preset_mode", "13G")) if meta else "13G"

        lines.append("================================================================================")
        lines.append("SPORTOTO QUANT COCKPIT - MULTI-COVERING KOLON LİSTESİ")
        lines.append(f"Garanti Seviyesi: {mode} | Toplam Kolon: {total_cols} Adet | Tutar: {total_cost:,.0f} TL")
        if meta:
            lines.append(f"Ham Havuz: {meta.get('raw_columns', 0):,} Kolon ({meta.get('raw_cost_tl', 0):,} TL) | Tasarruf: %{meta.get('savings_percent', 0.0)}")
            tel = meta.get("telemetry", {})
            if tel:
                lines.append(f"15 Büyük İkramiye: {tel.get('p15_jackpot_pct', 0.0)} | 14 Yakalama: {tel.get('p14_chance_pct', 0.0)} | 13G: {tel.get('p13_hit', '100%')}")
                lines.append(f"12 Kademeli Dağılım: {tel.get('p12_cascade', '-')}")
                lines.append(f"1 Hata Koruması: {tel.get('one_mistake_protection', '-')}")
        lines.append("================================================================================\n")

        for s in sheets_data:
            s_id = s.get("sheet_id", 1)
            s_cost = s.get("cost_tl", 40.0)
            a_picks = s.get("A", [])
            b_picks = s.get("B", [])
            c_picks = s.get("C", [])
            d_picks = s.get("D", [])

            lines.append("--------------------------------------------------------------------------------")
            lines.append(f"📋 Kupon #{s_id} (4 Kolon) -> [Harf A: 10 TL] [Harf B: 10 TL] [Harf C: 10 TL] [Harf D: 10 TL]")
            lines.append("--------------------------------------------------------------------------------")
            lines.append(f"{'Maç':<4} | {'Karşılaşma':<30} | {'Harf A':<6} | {'Harf B':<6} | {'Harf C':<6} | {'Harf D':<6} |")
            lines.append("--------------------------------------------------------------------------------")

            for m_i in range(15):
                m_info = FIXTURE[m_i] if m_i < len(FIXTURE) else {"home": f"Ev {m_i+1}", "away": f"Dep {m_i+1}"}
                match_str = f"{m_info['home']} - {m_info['away']}"[:30]
                a_val = a_picks[m_i] if m_i < len(a_picks) else "-"
                b_val = b_picks[m_i] if m_i < len(b_picks) else "-"
                c_val = c_picks[m_i] if m_i < len(c_picks) else "-"
                d_val = d_picks[m_i] if m_i < len(d_picks) else "-"
                lines.append(f"M{m_i+1:02d} | {match_str:<30} | {a_val:^6} | {b_val:^6} | {c_val:^6} | {d_val:^6} |")

            lines.append("--------------------------------------------------------------------------------")
            if a_picks:
                lines.append(f"Harf A [10 TL]: {', '.join(a_picks)}")
            if b_picks:
                lines.append(f"Harf B [10 TL]: {', '.join(b_picks)}")
            if c_picks:
                lines.append(f"Harf C [10 TL]: {', '.join(c_picks)}")
            if d_picks:
                lines.append(f"Harf D [10 TL]: {', '.join(d_picks)}")
            lines.append("")

        lines.append("================================================================================")
        lines.append(f"GENEL TOPLAM: {total_cols} Kolon = {total_cost:,.0f} TL")
        lines.append("Nesine.com'da her 4 kolon tek ekranda A, B, C, D harfleri sırayla doldurularak oynanır.")
        lines.append("================================================================================")

        return "\n".join(lines)

    # Legacy support
    @staticmethod
    def generate_injector_payload(
        tickets: List[Dict[str, Any]],
        guarantee_mode: str = "13G",
        total_cost_tl: Optional[float] = None
    ) -> Dict[str, Any]:
        raw_tickets = [t.get("picks", t) if isinstance(t, dict) else t for t in tickets]
        cost = total_cost_tl if total_cost_tl is not None else float(len(tickets) * 10)
        return {
            "version": "3.0",
            "generator": "OptimizedSyndicateEngine",
            "timestamp": datetime.now().isoformat(),
            "guarantee_mode": guarantee_mode,
            "total_tickets": len(tickets),
            "total_cost_tl": cost,
            "tickets": raw_tickets
        }

    @staticmethod
    def generate_plain_txt(tickets: List[Dict[str, Any]], meta: Optional[Dict[str, Any]] = None) -> str:
        return TicketExporter.generate_sheets_txt(tickets, meta)
