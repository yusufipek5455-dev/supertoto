"""
Verification tests for covering_engine.py
Tests:
- 11 doubles + 4 singles (2,048 columns)
- 14G (R=1), 13G (R=2), 12G (R=3)
- Strict mathematical verification: min_{c in C} d_H(p, c) <= R for all p in P
- Execution speed & telemetry metrics
- Nesine bin-packing and TXT export
"""

import time
import numpy as np
from covering_engine import SphereCoveringEngine, NesineBinPacker

def run_tests():
    engine = SphereCoveringEngine()
    print("=== TEST 1: POOL GENERATION (11 Doubles + 4 Singles) ===")
    user_picks = []
    for i in range(15):
        if i < 11:
            user_picks.append(['1', 'X'])
        else:
            user_picks.append(['1'])

    t0 = time.perf_counter()
    candidates = engine.generate_candidate_pool(user_picks)
    t_gen = time.perf_counter() - t0
    print(f"Generated {candidates.shape[0]} candidates in {t_gen*1000:.2f} ms.")
    assert candidates.shape == (2048, 15), f"Expected shape (2048, 15), got {candidates.shape}"

    for mode in ["14G", "13G", "12G"]:
        print(f"\n=== TEST COVERING FOR {mode} ===")
        t0 = time.perf_counter()
        res = engine.run_ev_weighted_cover(candidates, target_mode=mode, alpha=1.0)
        t_cover = time.perf_counter() - t0

        telemetry = res["telemetry"]
        red_cols = res["reduced_columns"]
        print(f"Mode {mode} completed in {t_cover:.3f} s:")
        print(f"  - Raw columns: {telemetry['raw_columns']:,} ({telemetry['raw_cost_tl']:,} TL)")
        print(f"  - Reduced columns: {telemetry['reduced_columns']:,} ({telemetry['reduced_cost_tl']:,} TL)")
        print(f"  - Theoretical Sphere Bound: {telemetry['theoretical_sphere_bound']:,}")
        print(f"  - Sphere Efficiency: %{telemetry['sphere_efficiency_pct']}")
        print(f"  - Savings: %{telemetry['savings_percent']}")
        print(f"  - Residual 15-Hit Probability: %{telemetry['residual_15_probability_pct']}")
        print(f"  - Guarantee Strictly Verified: {telemetry['guarantee_strictly_verified']}")

        assert telemetry["guarantee_strictly_verified"] is True, f"Covering for {mode} failed strict verification!"

    print("\n=== TEST NESINE BIN PACKING ===")
    res_14g = engine.run_ev_weighted_cover(candidates, target_mode="14G")
    sheets_single = NesineBinPacker.pack_single_columns(res_14g["reduced_columns"])
    print(f"Single column packing: {len(sheets_single)} sheets generated.")
    assert len(sheets_single) > 0, "No sheets generated"
    
    sheets_block = NesineBinPacker.pack_asymmetric_blocks(res_14g["reduced_columns"], user_picks)
    print(f"Block packing: {len(sheets_block)} sheets generated.")
    assert len(sheets_block) > 0, "No block sheets generated"

    txt_export = NesineBinPacker.generate_plain_txt_export(sheets_block, res_14g["telemetry"])
    print(f"Generated TXT export ({len(txt_export.splitlines())} lines). Sample header:")
    for line in txt_export.splitlines()[:10]:
        print("  ", line.encode("ascii", "replace").decode("ascii"))

    print("\n>>> ALL TESTS PASSED SUCCESSFULLY! <<<")

if __name__ == "__main__":
    run_tests()
