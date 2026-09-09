# =============================================================================
# test_system_invariants.py
# 5 ALTIN KURAL (INVARIANTS) OTOMASYON TEST DOSYASI
# =============================================================================
# Kural 1: Sifir Sapma - Banko Korumasi (Singles == 100%)
# Kural 2: Havuz Disi Yasak - Out-of-Bounds Check
# Kural 3: Marjinal Frekans Korumasi - Anti-Gizli Tekli
# Kural 4: Sentetik Monte Carlo Stres Testi (10.000 senaryo, d_H <= R)
# Kural 5: Nesine Finansal Butunluk (mod 4, 40 TL yaprak)
# =============================================================================

import numpy as np
import time
from covering_engine import OptimizedSyndicateEngine, OUTCOME_MAP
from toto_quant_engine import FIXTURE


def extract_columns_from_pipeline(result):
    """Extract flat column list (list of list of str) from run_full_pipeline result."""
    columns = []
    for sheet in result["sheets"]:
        for letter in ["A", "B", "C", "D"]:
            col = sheet.get(letter, [])
            if col and len(col) == 15:
                columns.append(col)
    return columns


def test_full_syndicate_integrity():
    engine = OptimizedSyndicateEngine()

    # Test Senaryosu: 6 Tek, 3 Cifte, 6 Kapali
    user_picks = [
        ['1'],             # M01 - Tek
        ['X', '2'],        # M02 - Cifte (Gizli tekli bug'inin ciktigi mac)
        ['1'],             # M03 - Tek
        ['1', 'X', '2'],   # M04 - Kapali
        ['2'],             # M05 - Tek
        ['1', 'X', '2'],   # M06 - Kapali
        ['1', 'X', '2'],   # M07 - Kapali
        ['1'],             # M08 - Tek
        ['2'],             # M09 - Tek
        ['X', '2'],        # M10 - Cifte
        ['1', 'X', '2'],   # M11 - Kapali
        ['1', 'X', '2'],   # M12 - Kapali
        ['1', 'X', '2'],   # M13 - Kapali
        ['2'],             # M14 - Tek
        ['X', '2']         # M15 - Cifte
    ]

    target_budget_cols = 96
    mode = "13G"  # R = 2

    # 1. Cozucuyu Calistir
    t0 = time.perf_counter()
    result = engine.run_full_pipeline(user_picks, guarantee_mode=mode, custom_budget=target_budget_cols)
    t_solve = time.perf_counter() - t0

    columns = extract_columns_from_pipeline(result)
    num_cols = len(columns)
    total_cost = result["reduced_cost_tl"]
    total_sheets = result["total_sheets"]

    print(f"\n{'=' * 80}")
    print(f"  SYSTEM INVARIANT AUDIT: {num_cols} KOLON / {total_sheets} SAYFA / {total_cost:,.0f} TL")
    print(f"  Cozum Suresi: {t_solve*1000:.1f} ms | Mod: {mode}")
    print(f"{'=' * 80}")

    all_passed = True

    # =========================================================================
    # KURAL 5: NESINE FINANSAL BUTUNLUK
    # =========================================================================
    print("\n--- KURAL 5: Nesine Finansal Butunluk ---")
    k5_col_mod4 = (num_cols % 4 == 0)
    k5_cost_match = abs(num_cols * 10.0 - total_cost) < 0.01
    k5_sheet_match = (total_sheets == (num_cols + 3) // 4)

    if k5_col_mod4:
        print(f"  [PASSED] Kolon Sayisi {num_cols} mod 4 = {num_cols % 4} (4'un kati)")
    else:
        print(f"  [FAILED] Kolon Sayisi {num_cols} mod 4 = {num_cols % 4} (4'un kati degil!)")
        all_passed = False

    if k5_cost_match:
        print(f"  [PASSED] Toplam Ucret: {num_cols} x 10 TL = {num_cols * 10:,} TL == {total_cost:,.0f} TL")
    else:
        print(f"  [FAILED] Toplam Ucret Uyusmuyor: {num_cols} x 10 = {num_cols * 10} != {total_cost}")
        all_passed = False

    if k5_sheet_match:
        print(f"  [PASSED] Sayfa Sayisi: {total_sheets} == ceil({num_cols}/4)")
    else:
        print(f"  [FAILED] Sayfa Sayisi: {total_sheets} != ceil({num_cols}/4) = {(num_cols+3)//4}")
        all_passed = False

    # =========================================================================
    # KURAL 1: SIFIR SAPMA - BANKO KORUMASI
    # =========================================================================
    print("\n--- KURAL 1: Sifir Sapma - Banko (Tek) Korumasi ---")
    k1_passed = True
    for m_idx, picks in enumerate(user_picks):
        if len(picks) == 1:
            expected = picks[0]
            col_values = [c[m_idx] for c in columns]
            unique_vals = set(col_values)
            if unique_vals != {expected}:
                print(f"  [FAILED] M{m_idx+1}: Tek secim '{expected}' iken kolonda {unique_vals} bulundu!")
                k1_passed = False
                all_passed = False
    if k1_passed:
        print(f"  [PASSED] Tum tek secimler (bankolar) tum kolonlarda degismez korunuyor.")

    # =========================================================================
    # KURAL 2: HAVUZ DISI YASAK - OUT-OF-BOUNDS CHECK
    # =========================================================================
    print("\n--- KURAL 2: Havuz Disi Yasak (Out-of-Bounds) ---")
    k2_passed = True
    for m_idx, picks in enumerate(user_picks):
        col_values = [c[m_idx] for c in columns]
        for val in col_values:
            if val not in picks:
                print(f"  [FAILED] KRITIK GUVENLIK ACIGI: M{m_idx+1} macinda secilmeyen '{val}' basilmis! (Secimler: {picks})")
                k2_passed = False
                all_passed = False
    if k2_passed:
        print(f"  [PASSED] Hicbir kolonda havuz disi secim yok. Tum degerler kullanici secim kumesinde.")

    # =========================================================================
    # KURAL 3: MARJINAL FREKANS KORUMASI - ANTI-GIZLI TEKLI
    # =========================================================================
    print("\n--- KURAL 3: Marjinal Frekans Korumasi (Anti-Gizli Tekli) ---")
    k3_passed = True
    imbalance_warnings = []

    print(f"  {'Mac':<5} | {'Secim':<10} | {'Dagilim':<50} | {'Durum'}")
    print(f"  {'-'*75}")

    for m_idx, picks in enumerate(user_picks):
        col_values = [c[m_idx] for c in columns]
        total = len(col_values)
        counts = {p: col_values.count(p) for p in picks}
        ratios = {p: cnt / total for p, cnt in counts.items()}
        k = len(picks)

        dist_str = ", ".join(f"{p}={counts[p]} ({ratios[p]*100:.1f}%)" for p in picks)
        status = "OK"

        if k == 2:
            min_r = min(ratios.values())
            if min_r < 0.30 - 1e-4:
                status = f"FAIL (min={min_r*100:.1f}% < 30%)"
                k3_passed = False
                all_passed = False
            elif min_r < 0.35:
                status = f"WARN (min={min_r*100:.1f}%, esik yakin)"
        elif k == 3:
            min_r = min(ratios.values())
            if min_r < 0.20 - 1e-4:
                status = f"FAIL (min={min_r*100:.1f}% < 20%)"
                k3_passed = False
                all_passed = False
            elif min_r < 0.25:
                status = f"WARN (min={min_r*100:.1f}%, esik yakin)"

        print(f"  M{m_idx+1:02d}  | {'/'.join(picks):<10} | {dist_str:<50} | {status}")

    if k3_passed:
        print(f"  [PASSED] Tum cifte ve kapali secimler dengeli dagitildi.")
    else:
        print(f"  [FAILED] Marjinal frekans esikleri ihlal edildi!")

    # =========================================================================
    # KURAL 4: SENTETIK MONTE CARLO STRES TESTI (10.000 SENARYO)
    # =========================================================================
    print(f"\n--- KURAL 4: Monte Carlo Stres Testi (10.000 Senaryo, R=2) ---")
    print(f"  Ham havuzdan rastgele 10.000 adet gerceklesen skor cekilip d_H <= 2 kontrol ediliyor...")

    t_mc0 = time.perf_counter()

    # Kolonlari sayisal matrise cevir
    opt_map = {'1': 0, 'X': 1, '2': 2}
    cols_matrix = np.array([[opt_map[x] for x in col] for col in columns], dtype=np.uint8)

    R = 2  # 13G icin
    num_simulations = 10000
    failed_scenarios = 0
    cascading_hits = []

    rng = np.random.default_rng(42)

    for _ in range(num_simulations):
        # Ham havuzdan rastgele bir maç sonucu olustur
        sim = np.array([opt_map[rng.choice(picks)] for picks in user_picks], dtype=np.uint8)

        # Vektorel Hamming mesafesi
        distances = np.sum(cols_matrix != sim, axis=1)
        min_dist = int(np.min(distances))

        if min_dist > R:
            failed_scenarios += 1

        # Kademeli ikramiye analizi
        hits_within_3 = int(np.sum(distances <= 3))
        cascading_hits.append(hits_within_3)

    t_mc = time.perf_counter() - t_mc0

    if failed_scenarios == 0:
        print(f"  [PASSED] 10.000 senaryonun %100'unde en az 1 kolon d_H <= 2 mesafesinde!")
    else:
        print(f"  [FAILED] MATEMATIKSEL IFLAS: 10.000 senaryodan {failed_scenarios} tanesinde 13G GARANTISI DELINDI!")
        all_passed = False

    avg_12 = np.mean(cascading_hits)
    min_12 = np.min(cascading_hits)
    max_12 = np.max(cascading_hits)
    print(f"  Ortalama Yakalanan Alt Kademe Ikramiye (d_H <= 3): {avg_12:.1f} / senaryo")
    print(f"  Min: {min_12} | Max: {max_12} | Monte Carlo Suresi: {t_mc*1000:.1f} ms")

    # =========================================================================
    # SONUC TABLOSU
    # =========================================================================
    print(f"\n{'=' * 80}")
    print(f"  5 ALTIN KURAL SONUC TABLOSU")
    print(f"{'=' * 80}")
    rules = [
        ("Kural 1", "Sifir Sapma (Banko Korumasi)", k1_passed),
        ("Kural 2", "Havuz Disi Yasak (OoB Check)", k2_passed),
        ("Kural 3", "Marjinal Frekans (Anti-Gizli Tekli)", k3_passed),
        ("Kural 4", "Monte Carlo Stres (10K Senaryo)", failed_scenarios == 0),
        ("Kural 5", "Nesine Finansal Butunluk", k5_col_mod4 and k5_cost_match and k5_sheet_match),
    ]
    for rule_id, rule_name, passed in rules:
        icon = "[PASSED]" if passed else "[FAILED]"
        print(f"  {icon}  {rule_id}: {rule_name}")

    print(f"{'=' * 80}")
    if all_passed:
        print(f"  >>> TUM 5 ALTIN KURAL HATASIZ GECTI! SISTEM MATEMATIKSEL OLARAK SAGLAM. <<<")
    else:
        print(f"  >>> BAZI KURALLAR IHLAL EDILDI! YUKARIDAKI HATALARI INCELEYIN. <<<")
    print(f"{'=' * 80}\n")

    assert all_passed, "Bir veya daha fazla invariant ihlal edildi!"


def test_alternative_scenarios():
    """Farkli pick ve mod kombinasyonlarini test eder."""
    engine = OptimizedSyndicateEngine()

    scenarios = [
        {
            "name": "Varsayilan 1728 Havuz (13G)",
            "picks": [
                ['1'], ['1', 'X'], ['1', 'X', '2'], ['1', 'X'], ['X', '2'],
                ['1', 'X', '2'], ['1', 'X', '2'], ['1'], ['X', '2'], ['X', '2'],
                ['1', 'X'], ['1'], ['1'], ['2'], ['1']
            ],
            "mode": "13G",
            "budget": None,
            "R": 2,
        },
        {
            "name": "Yuksek Cifte Yogunlugu (14G)",
            "picks": [
                ['1', 'X'], ['X', '2'], ['1', '2'], ['1', 'X'], ['X', '2'],
                ['1', '2'], ['1', 'X'], ['X', '2'], ['1'], ['1'],
                ['1'], ['1'], ['1'], ['2'], ['1']
            ],
            "mode": "14G",
            "budget": None,
            "R": 1,
        },
        {
            "name": "12G Garanti (R=3)",
            "picks": [
                ['1'], ['X', '2'], ['1', 'X', '2'], ['1', 'X'], ['X', '2'],
                ['1', 'X', '2'], ['1', 'X', '2'], ['1'], ['X', '2'], ['X', '2'],
                ['1', 'X'], ['1'], ['1'], ['2'], ['1']
            ],
            "mode": "12G",
            "budget": None,
            "R": 3,
        },
    ]

    opt_map = {'1': 0, 'X': 1, '2': 2}
    rng = np.random.default_rng(123)

    for sc in scenarios:
        print(f"\n{'=' * 80}")
        print(f"  SENARYO: {sc['name']}")
        print(f"{'=' * 80}")

        result = engine.run_full_pipeline(sc["picks"], guarantee_mode=sc["mode"], custom_budget=sc["budget"])
        columns = extract_columns_from_pipeline(result)
        num_cols = len(columns)
        R = sc["R"]

        # Kural 5: Finansal
        assert num_cols % 4 == 0, f"Kolon {num_cols} mod 4 != 0"
        assert abs(num_cols * 10.0 - result["reduced_cost_tl"]) < 0.01

        # Kural 1 + 2: Banko + OoB
        for m_idx, picks in enumerate(sc["picks"]):
            col_values = [c[m_idx] for c in columns]
            for val in col_values:
                assert val in picks, f"OoB: M{m_idx+1} '{val}' not in {picks}"
            if len(picks) == 1:
                assert len(set(col_values)) == 1, f"Banko M{m_idx+1} variasyon!"

        # Kural 3: Marjinal frekans
        for m_idx, picks in enumerate(sc["picks"]):
            col_values = [c[m_idx] for c in columns]
            total = len(col_values)
            k = len(picks)
            if k >= 2:
                ratios = {p: col_values.count(p) / total for p in picks}
                min_r = min(ratios.values())
                if k == 2:
                    assert min_r >= 0.30 - 1e-4, f"M{m_idx+1} cifte min={min_r*100:.1f}% < 30%"
                elif k == 3:
                    assert min_r >= 0.20 - 1e-4, f"M{m_idx+1} kapali min={min_r*100:.1f}% < 20%"

        # Kural 4: Monte Carlo (1000 senaryo, hiz icin)
        cols_matrix = np.array([[opt_map[x] for x in col] for col in columns], dtype=np.uint8)
        fails = 0
        for _ in range(1000):
            sim = np.array([opt_map[rng.choice(p)] for p in sc["picks"]], dtype=np.uint8)
            dists = np.sum(cols_matrix != sim, axis=1)
            if np.min(dists) > R:
                fails += 1
        assert fails == 0, f"Monte Carlo {fails}/1000 senaryo basarisiz (R={R})"

        print(f"  [PASSED] {sc['name']}: {num_cols} Kolon, R={R}, 5 Kural OK")


if __name__ == "__main__":
    test_full_syndicate_integrity()
    test_alternative_scenarios()
    print("\n>>> BUTUN TESTLER VE SENARYOLAR BASARIYLA TAMAMLANDI! <<<\n")
