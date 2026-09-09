"""
TOTO QUANT REST API (FastAPI)
=============================
Provides discrete optimization and multi-covering syndicate endpoints:
- POST /api/solve : Solves 15-match fixture portfolio guaranteeing 5 Golden Rules
- GET  /api/health: Healthcheck and system telemetry
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
import math
from core_engine import run_syndicate_solver, CHAR_TO_INT

app = FastAPI(
    title="Toto Quant Institutional Solver API",
    description="Vectorized multi-covering sphere reduction API for Spor Toto 15-match fixtures",
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
    target_columns: Optional[int] = Field(default=None, description="Optional target columns (must be multiple of 4)")
    solver_mode: Optional[str] = Field(default="auto_boost", description="Strategy: 'base_only' (ekonomik) or 'auto_boost' (akıllı sürpriz avcısı)")
    booster_columns: Optional[int] = Field(default=None, description="Extra booster columns on top of baseline")


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


@app.get("/api/health")
def healthcheck():
    return {
        "status": "healthy",
        "engine": "Toto Quant Pro v4.2 Hybrid",
        "golden_rules": 5,
        "mod_4_aligned": True
    }


@app.post("/api/solve", response_model=SolveResponse)
def solve_portfolio(req: SolveRequest):
    if len(req.matches) != 15:
        raise HTTPException(
            status_code=422,
            detail=f"Bülten tam olarak 15 karşılaşma içermelidir (Gönderilen: {len(req.matches)})."
        )

    # Normalize user_picks into List[List[str]]
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

        # Validate and sanitize choices
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

    # Execute two-stage institutional solver
    try:
        sol = run_syndicate_solver(
            user_picks=clean_picks,
            mode=req.mode,
            target_cols=req.target_columns,
            booster_cols=req.booster_columns,
            solver_mode=req.solver_mode or "auto_boost"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Solver hatası: {str(e)}")

    # Enforce strict financial invariants
    tot_cols = sol["total_columns"]
    assert tot_cols % 4 == 0, f"Mod 4 delinmesi: {tot_cols}"
    assert sol["total_cost"] == tot_cols * 10, "Fiyatlama tutarsızlığı"
    assert len(sol["sheets"]) == tot_cols // 4, "Sayfa sayısı tutarsızlığı"

    return SolveResponse(
        status="success",
        mode=sol["mode"],
        solver_mode=sol.get("solver_mode", req.solver_mode or "auto_boost"),
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
