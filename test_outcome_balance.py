# Marginal Outcome Balance and Hidden Single Test
import numpy as np
from covering_engine import OptimizedSyndicateEngine, OUTCOME_MAP
from toto_quant_engine import FIXTURE

def print_distribution_table(test_name: str, user_picks: list, reduced_columns: np.ndarray):
    N_cols = len(reduced_columns)
    print("\n" + "=" * 95)
    print(f"DISTRIBUTION TABLE: {test_name} (Total Columns: {N_cols}, Cost: {N_cols * 10:,} TL)")
    print("=" * 95)
    print(f"{'M#':<4} | {'Karsilasma':<30} | {'Secim':<10} | {'1 Sayi (%)':<16} | {'X Sayi (%)':<16} | {'2 Sayi (%)':<16} | Durum")
    print("-" * 95)

    all_passed = True
    for m in range(15):
        opts = user_picks[m]
        k = len(opts)
        home = FIXTURE[m]['home'][:14]
        away = FIXTURE[m]['away'][:14]
        match_info = f"{home} - {away}"
        counts = {o: int(np.count_nonzero(reduced_columns[:, m] == (0 if o == '1' else (1 if o == 'X' else 2)))) for o in ['1', 'X', '2']}
        ratios = {o: counts[o] / N_cols for o in ['1', 'X', '2']}

        str_1 = f"{counts['1']} ({ratios['1']*100:.1f}%)" if '1' in opts else "-"
        str_x = f"{counts['X']} ({ratios['X']*100:.1f}%)" if 'X' in opts else "-"
        str_2 = f"{counts['2']} ({ratios['2']*100:.1f}%)" if '2' in opts else "-"

        status = "[PASS] OK"
        if k == 1:
            if any(counts[o] != N_cols for o in opts):
                status = "[FAIL] (Single != 100%)"
                all_passed = False
        elif k == 2:
            min_r = min(ratios[o] for o in opts)
            if min_r < 0.30 - 1e-4:
                status = f"[FAIL] (Double min={min_r*100:.1f}% < 30%)"
                all_passed = False
        elif k == 3:
            min_r = min(ratios[o] for o in opts)
            if min_r < 0.20 - 1e-4:
                status = f"[FAIL] (Triple min={min_r*100:.1f}% < 20%)"
                all_passed = False

        picks_str = "/".join(opts)
        print(f"M{m+1:02d} | {match_info:<30} | {picks_str:<10} | {str_1:<16} | {str_x:<16} | {str_2:<16} | {status}")

    print("-" * 95)
    return all_passed

def run_balance_tests():
    engine = OptimizedSyndicateEngine()

    print("\n>>> RUNNING TEST CASE 1: Reported M02 Double ('X' and '2') with 13G Guarantee")
    test_picks_1 = [
        ['1'], ['X', '2'], ['1', 'X', '2'], ['1', 'X'], ['X', '2'],
        ['1', 'X', '2'], ['1', 'X', '2'], ['1'], ['X', '2'], ['X', '2'],
        ['1', 'X'], ['1'], ['1'], ['2'], ['1']
    ]

    res1 = engine.run_full_pipeline(test_picks_1, guarantee_mode="13G", custom_budget=96)
    cols1 = []
    for s in res1["sheets"]:
        for l in ["A", "B", "C", "D"]:
            if s.get(l):
                cols1.append([0 if o == '1' else (1 if o == 'X' else 2) for o in s[l]])
    cols_arr1 = np.array(cols1)

    t1_passed = print_distribution_table("Test 1: Reported M02 Case (13G / 96 Kolon)", test_picks_1, cols_arr1)
    assert res1["telemetry"]["guarantee_verified"] is True, "Test 1 Guarantee failed verification!"
    assert t1_passed is True, "Test 1 Outcome Balance failed!"
    print("TEST 1 PASSED: M02 double pick achieved marginal balance and guarantee is 100% verified.")

    print("\n>>> RUNNING TEST CASE 2: High Double Density (8 Doubles / 7 Singles) with 14G Guarantee")
    test_picks_2 = [
        ['1', 'X'], ['X', '2'], ['1', '2'], ['1', 'X'], ['X', '2'],
        ['1', '2'], ['1', 'X'], ['X', '2'], ['1'], ['1'],
        ['1'], ['1'], ['1'], ['2'], ['1']
    ]
    res2 = engine.run_full_pipeline(test_picks_2, guarantee_mode="14G")
    cols2 = []
    for s in res2["sheets"]:
        for l in ["A", "B", "C", "D"]:
            if s.get(l):
                cols2.append([0 if o == '1' else (1 if o == 'X' else 2) for o in s[l]])
    cols_arr2 = np.array(cols2)

    t2_passed = print_distribution_table("Test 2: High Double Density (14G)", test_picks_2, cols_arr2)
    assert res2["telemetry"]["guarantee_verified"] is True, "Test 2 Guarantee failed verification!"
    assert t2_passed is True, "Test 2 Outcome Balance failed!"
    print("TEST 2 PASSED: All 8 doubles maintained >= 30% and guarantee is 100% verified.")

    print("\n>>> RUNNING TEST CASE 3: Mixed Triples and Doubles with 13G Guarantee")
    test_picks_3 = [
        ['1', 'X', '2'], ['1', 'X', '2'], ['1', 'X', '2'],
        ['1', 'X'], ['X', '2'], ['1', '2'], ['1', 'X'],
        ['1'], ['1'], ['1'], ['1'], ['1'], ['2'], ['1'], ['1']
    ]
    res3 = engine.run_full_pipeline(test_picks_3, guarantee_mode="13G")
    cols3 = []
    for s in res3["sheets"]:
        for l in ["A", "B", "C", "D"]:
            if s.get(l):
                cols3.append([0 if o == '1' else (1 if o == 'X' else 2) for o in s[l]])
    cols_arr3 = np.array(cols3)

    t3_passed = print_distribution_table("Test 3: Mixed Triples and Doubles (13G)", test_picks_3, cols_arr3)
    assert res3["telemetry"]["guarantee_verified"] is True, "Test 3 Guarantee failed verification!"
    assert t3_passed is True, "Test 3 Outcome Balance failed!"
    print("TEST 3 PASSED: All triples >= 20%, all doubles >= 30%, singles == 100%.")

    print("\n" + "=" * 95)
    print("ALL MARGINAL OUTCOME BALANCE AND GUARANTEE TESTS PASSED WITHOUT DEFECTS!")
    print("=" * 95)

if __name__ == "__main__":
    run_balance_tests()
