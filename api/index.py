"""
SüperToto Vercel Serverless Python Entrypoint
============================================
FastAPI serverless solver running on Vercel:
- POST /api/solve (and /solve)
- GET  /api/health (and /health)
"""

import os
import sys

# Ensure repository root is on sys.path for serverless execution
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from core_engine import run_syndicate_solver, CHAR_TO_INT

app = FastAPI(
    title="SüperToto Solver Engine",
    description="Vercel Serverless Multi-Covering Spor Toto Solver",
    version="4.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MatchPick(BaseModel):
    id: Optional[int] = None
    home: Optional[str] = None
    away: Optional[str] = None
    picks: List[str] = Field(default_factory=lambda: ["1"])


class SolveRequest(BaseModel):
    matches: List[Union[MatchPick, List[str], Dict[str, Any]]]
    mode: str = Field(default="13G", description="Guarantee mode: 15G, 14G, 13G, 12G")
    target_columns: Optional[int] = Field(default=None, description="Target columns (must be multiple of 4)")
    solver_mode: Optional[str] = Field(default="auto_boost", description="Strategy: 'base_only' (ekonomik) or 'auto_boost' (akıllı sürpriz avcısı)")
    booster_columns: Optional[int] = Field(default=None, description="Extra booster columns")


class SolveResponse(BaseModel):
    status: str
    mode: str
    solver_mode: str = "auto_boost"
    total_columns: int
    baseline_columns: int
    booster_columns: int
    total_sheets: int
    total_cost: int
    columns: List[List[str]]
    compact_columns: List[str]
    column_types: List[str]
    sheets: List[Dict[str, Any]]
    coverage_pct: float
    is_full_coverage: bool


def _handle_health():
    return {
        "status": "healthy",
        "app": "SüperToto Terminali",
        "engine": "SüperToto Hybrid Solver Engine",
        "mod_4_aligned": True
    }


def _handle_solve(req: SolveRequest) -> SolveResponse:
    if len(req.matches) != 15:
        raise HTTPException(
            status_code=422,
            detail=f"Bülten tam olarak 15 karşılaşma içermelidir (Gönderilen: {len(req.matches)})."
        )

    clean_picks: List[List[str]] = []
    for idx, m in enumerate(req.matches):
        raw_opts: List[str] = []
        if isinstance(m, MatchPick):
            raw_opts = m.picks
        elif isinstance(m, dict):
            raw_opts = m.get("picks", m.get("selections", ["1"]))
        elif isinstance(m, (list, tuple)):
            raw_opts = list(m)
        else:
            raw_opts = ["1"]

        sanitized: List[str] = []
        for o in raw_opts:
            val = 'X' if str(o).strip().upper() == '0' else str(o).strip().upper()
            if val in CHAR_TO_INT and val not in sanitized:
                sanitized.append(val)

        if not sanitized:
            raise HTTPException(
                status_code=422,
                detail=f"Maç #{idx+1} için geçerli en az bir tercih ('1', 'X', '2') yapılmalıdır."
            )
        clean_picks.append(sanitized)

    effective_solver_mode = req.solver_mode or "auto_boost"

    try:
        sol = run_syndicate_solver(
            user_picks=clean_picks,
            mode=req.mode,
            target_cols=req.target_columns,
            booster_cols=req.booster_columns,
            solver_mode=effective_solver_mode
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Solver hatası: {str(e)}")

    tot_cols = sol["total_columns"]
    assert tot_cols % 4 == 0, f"Mod 4 kuralı ihlali: {tot_cols}"
    assert sol["total_cost"] == tot_cols * 10, "Maliyet tutarsızlığı"

    return SolveResponse(
        status="success",
        mode=sol["mode"],
        solver_mode=sol.get("solver_mode", effective_solver_mode),
        total_columns=tot_cols,
        baseline_columns=sol.get("baseline_columns", tot_cols),
        booster_columns=sol.get("booster_columns", 0),
        total_sheets=sol["total_sheets"],
        total_cost=sol["total_cost"],
        columns=sol["columns"],
        compact_columns=sol["compact_columns"],
        column_types=sol.get("column_types", ["base"] * tot_cols),
        sheets=sol["sheets"],
        coverage_pct=sol["coverage_pct"],
        is_full_coverage=sol["is_full_coverage"]
    )



def _handle_bulletin():
    try:
        from state_manager import fetch_live_bulletin_from_nesine
        res = fetch_live_bulletin_from_nesine(timeout=5.0)
        return res
    except Exception as e:
        from state_manager import DEFAULT_FIXTURES
        return {
            "success": True,
            "fixtures": DEFAULT_FIXTURES,
            "program_info": {"pNo": "357", "week": "141236"},
            "is_fallback": True,
            "fallback_source": f"Yerel Fikstür Yedeği ({str(e)})",
            "error": str(e)
        }


# Dual route registration for Vercel (/api/bulletin and /bulletin)
@app.get("/api/bulletin")
@app.get("/bulletin")
def get_bulletin():
    return _handle_bulletin()


# Dual route registration for Vercel (/api/health and /health)
@app.get("/api/health")
@app.get("/health")
def healthcheck():
    return _handle_health()


@app.post("/api/solve", response_model=SolveResponse)
@app.post("/solve", response_model=SolveResponse)
def solve_portfolio(req: SolveRequest):
    return _handle_solve(req)

