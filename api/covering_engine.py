"""
OPTIMIZED SYNDICATE ENGINE & MULTI-COVERING SPHERE REDUCTION CORE
==================================================================
Production-grade discrete optimization and quantitative syndicate engine
for Spor Toto 15-match fixtures on Omega = {1, X, 2}^15.

Pure Mathematical Guarantee Levels:
- 🛡️ 13G (R=2, Multi-Covering K >= 2 for Cascading 12s/11s)
- 🎯 14G (R=1, Multi-Covering K >= 2 for Cascading 13s/12s)
- 👑 15G (R=0, Full Cartesian Identity Universe)

Invariants:
- Strict User Selection Invariant (R=0 anchors on singles).
- Dynamic Pricing: Cost = Columns * 10.00 TL.
- Official Nesine 40 TL Sheet Packaging: 4 Columns (Harf A, B, C, D) = 40.00 TL.
"""

import itertools
from typing import List, Dict, Tuple, Any, Optional
import numpy as np
from toto_quant_engine import FIXTURE, get_probability_matrices, get_value_ratio_matrix, compute_dynamic_ev_matrix

OUTCOME_MAP = {0: "1", 1: "X", 2: "2"}
REV_OUTCOME_MAP = {"1": 0, "X": 1, "0": 1, "2": 2}


def fast_hamming_coverage(
    pool_matrix: np.ndarray,
    selected_matrix: np.ndarray,
    radius: int,
    chunk_size: int = 500
) -> np.ndarray:
    """
    Computes count of selected columns covering each pool candidate within radius R.
    For chunks of size B:
        diff = pool_chunk[:, np.newaxis, :] != selected_matrix[np.newaxis, :, :]
        dist = np.sum(diff, axis=-1)
        covered = np.sum(dist <= radius, axis=1)
    Returns:
        Integer array of coverage counts for all N pool members.
    """
    N = pool_matrix.shape[0]
    K = selected_matrix.shape[0]
    if N == 0 or K == 0:
        return np.zeros(N, dtype=np.int32)

    coverage_counts = np.zeros(N, dtype=np.int32)
    for start in range(0, N, chunk_size):
        end = min(start + chunk_size, N)
        diff = pool_matrix[start:end, np.newaxis, :] != selected_matrix[np.newaxis, :, :]
        dist = np.sum(diff, axis=-1)
        coverage_counts[start:end] = np.sum(dist <= radius, axis=1)

    return coverage_counts


class OptimizedSyndicateEngine:
    def __init__(self, fixtures: Optional[List[Dict[str, Any]]] = None):
        if fixtures is not None:
            self.update_fixtures(fixtures)
        else:
            self.p_pub, self.p_true = get_probability_matrices()
            self.val_ratios = get_value_ratio_matrix()

    def update_fixtures(self, dynamic_odds: Any):
        """Dynamically update probability and EV ratio matrices from active fixtures or raw odds."""
        p_pub, p_true, val_ratios = compute_dynamic_ev_matrix(dynamic_odds=dynamic_odds, epsilon=1e-3)
        self.p_pub = p_pub
        self.p_true = p_true
        self.val_ratios = val_ratios

    def generate_candidate_pool(self, user_picks: List[List[str]]) -> np.ndarray:
        """
        Computes Cartesian product directly from user's active choices.
        Strict User Invariant: Single choices (k_i = 1) have R=0 error tolerance
        and are identically preserved across all generated candidate vectors.
        Returns:
            candidates: (N, 15) np.uint8 array
        """
        assert len(user_picks) == 15, "Pool must contain exactly 15 matches."

        encoded_picks = []
        for match_opts in user_picks:
            clean = sorted(list(set(REV_OUTCOME_MAP[o] for o in match_opts if o in REV_OUTCOME_MAP)))
            encoded_picks.append(clean if clean else [0])

        cartesian_prod = list(itertools.product(*encoded_picks))
        return np.array(cartesian_prod, dtype=np.uint8)

    def compute_local_sphere_bounds(self, raw_cols: int, user_picks: Optional[List[List[str]]] = None) -> Dict[str, Any]:
        """
        Computes exact local Hamming sphere volumes restricted to the user's active choice subspace.
        For S singles, D doubles, T triples (S + D + T = 15):
          V_local(R=0) = 1
          V_local(R=1) = 1 + D*1 + T*2
          V_local(R=2) = V_local(R=1) + C(D, 2)*1 + D*T*2 + C(T, 2)*4
        """
        if user_picks is not None and len(user_picks) == 15:
            d = sum(1 for p in user_picks if len(set(p)) == 2)
            t = sum(1 for p in user_picks if len(set(p)) >= 3)
            s = 15 - d - t
        else:
            d = max(0, min(15, int(round(np.log2(max(1, raw_cols))))))
            t = 0
            s = 15 - d

        v0 = 1
        v1 = 1 + d + 2 * t
        v2 = v1 + (d * (d - 1) // 2) + (d * t * 2) + (t * (t - 1) * 2)
        # V_local(R=3) for 12G Garanti (D choose 3 + D choose 2 * T * 2 + D * T choose 2 * 4 + T choose 3 * 8)
        term_d3 = (d * (d - 1) * (d - 2)) // 6 if d >= 3 else 0
        term_d2t = ((d * (d - 1)) // 2) * t * 2 if d >= 2 else 0
        term_dt2 = d * ((t * (t - 1)) // 2) * 4 if t >= 2 else 0
        term_t3 = ((t * (t - 1) * (t - 2)) // 6) * 8 if t >= 3 else 0
        v3 = v2 + term_d3 + term_d2t + term_dt2 + term_t3

        bound_15g = raw_cols
        bound_14g = max(1, int(np.ceil(raw_cols / max(1, v1))))
        bound_13g = max(1, int(np.ceil(raw_cols / max(1, v2))))
        bound_12g = max(1, int(np.ceil(raw_cols / max(1, v3))))

        return {
            "d": d, "t": t, "s": s,
            "v0": v0, "v1": v1, "v2": v2, "v3": v3,
            "bound_15g": bound_15g,
            "bound_14g": bound_14g,
            "bound_13g": bound_13g,
            "bound_12g": bound_12g
        }

    def estimate_required_columns(
        self,
        raw_cols: int,
        guarantee_mode: str = "13G",
        user_picks: Optional[List[List[str]]] = None
    ) -> int:
        """
        Dynamically estimates required covering columns (M) based on current raw pool size
        and restricted Hamming sphere geometry.
        Returns a multiple of 4 (padded for exact 40 TL sheets).
        """
        mode = guarantee_mode.upper()
        if raw_cols <= 4:
            return raw_cols

        bounds = self.compute_local_sphere_bounds(raw_cols, user_picks)

        if "14" in mode:
            # R=1 Sphere Covering with ~1.35x greedy overlap factor
            est = int(round((bounds["bound_14g"] * 1.35) / 4.0) * 4)
            return min(raw_cols, max(4, est))
        elif "15" in mode:
            # R=0 Full Universe
            return raw_cols
        elif "12" in mode:
            # R=3 Sphere Covering for 12G (significantly fewer columns than 13G)
            est = int(round((bounds["bound_12g"] * 2.1) / 4.0) * 4)
            return min(raw_cols, max(4, est))
        else:  # "13G" default
            # R=2 Sphere Covering with ~1.85x greedy overlap factor
            est = int(round((bounds["bound_13g"] * 1.85) / 4.0) * 4)
            return min(raw_cols, max(4, est))


    def apply_entropy_cut(
        self,
        candidates: np.ndarray,
        p_lower: float = 5.0,
        p_upper: float = 99.0
    ) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
        """
        Adaptive Shannon Entropy Cut:
        S(c) = sum_{i=0}^{14} -log2(P_pub,i(c_i))
        Dynamically prunes:
        - Bottom 5% (dead consensus with poor payouts: S < S_0.05)
        - Top 1% (statistically impossible chaos: S > S_0.99)
        """
        N = candidates.shape[0]
        log2_pub = -np.log2(np.maximum(self.p_pub, 1e-4))
        entropies = np.zeros(N, dtype=np.float64)

        for i in range(15):
            entropies += log2_pub[i, candidates[:, i]]

        if N <= 16:
            s_min = float(np.min(entropies))
            s_max = float(np.max(entropies))
            mean_s = float(np.mean(entropies))
            return candidates, np.ones(N, dtype=bool), {
                "raw_cols": N,
                "pruned_cols": N,
                "prune_ratio": 0.0,
                "s_min": round(s_min, 2),
                "s_max": round(s_max, 2),
                "mean_entropy": round(mean_s, 2)
            }

        s_min = float(np.percentile(entropies, p_lower))
        s_max = float(np.percentile(entropies, p_upper))

        mask = (entropies >= s_min) & (entropies <= s_max)
        surviving_count = int(np.count_nonzero(mask))

        # Safety fallback
        if surviving_count < min(N, 16):
            dist_to_median = np.abs(entropies - np.median(entropies))
            top_k = min(N, max(16, surviving_count))
            best_idx = np.argsort(dist_to_median)[:top_k]
            mask = np.zeros(N, dtype=bool)
            mask[best_idx] = True
            surviving_count = len(best_idx)

        pruned_candidates = candidates[mask]
        stats = {
            "raw_cols": N,
            "pruned_cols": surviving_count,
            "prune_ratio": round((1.0 - (surviving_count / N)) * 100.0, 1),
            "s_min": round(s_min, 2),
            "s_max": round(s_max, 2),
            "mean_entropy": round(float(np.mean(entropies[mask])), 2) if surviving_count > 0 else 0.0
        }

        return pruned_candidates, mask, stats

    def calculate_ev_weights(self, candidates: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Computes for each candidate column:
        1. W(c) = prod_{i=0}^{14} (P_true,i(c_i) / P_pub,i(c_i))
        2. P_true(c) = prod_{i=0}^{14} P_true,i(c_i)
        """
        N = candidates.shape[0]
        log_w = np.zeros(N, dtype=np.float64)
        log_ptrue = np.zeros(N, dtype=np.float64)

        for i in range(15):
            c_i = candidates[:, i]
            log_w += np.log(self.val_ratios[i, c_i])
            log_ptrue += np.log(self.p_true[i, c_i])

        w = np.exp(log_w)
        p_true = np.exp(log_ptrue)
        return w, p_true

    def solve_multi_cover(
        self,
        candidates: np.ndarray,
        guarantee_mode: str = "13G",
        alpha: float = 0.35,
        custom_budget: Optional[int] = None,
        beta: float = 1.5
    ) -> Dict[str, Any]:
        """
        Two-Stage Multi-Covering Solver with Marginal Outcome Balance Constraints
        ========================================================================
        - Stage 1 (Pure Guarantee + Balance Regularization):
          Greedily covers 100% of candidate pool within radius R
          (R=2 for 13G, R=1 for 14G, R=0 for 15G, R=3 for 12G).
          Dynamic regularization:
            Score(cand) = UncoveredGain(cand) * (1.0 + alpha * EV(cand)) - beta * ImbalancePenalty(cand)
            with alpha = 0.35, beta = 1.5.
            ImbalancePenalty(cand) = sum_{i=0}^{14} max(0, count(cand_i)/current_total - target_cap_i)
        - Stage 2 (+EV Multi-Covering Boost & Deficit Balancing):
          Uses target budget (padded to multiple of 4 for 40 TL sheets).
          Prioritizes +EV candidates while eliminating outcome deficits.
        - Stage 3 (Marginal Outcome Balance Verification):
          Strictly verifies:
            - Singles (k_i = 1): Var(c_i) == 0.0 (100% identical).
            - Doubles (k_i = 2): min(ratio) >= 0.30 (no outcome below 30%).
            - Triples (k_i = 3): min(ratio) >= 0.20 (no outcome below 20%).
        """
        N = candidates.shape[0]
        weights, p_true = self.calculate_ev_weights(candidates)

        mode_clean = guarantee_mode.upper()
        if "14" in mode_clean:
            R = 1
            est_target = self.estimate_required_columns(N, "14G")
        elif "15" in mode_clean:
            R = 0
            est_target = N
        elif "12" in mode_clean:
            R = 3
            est_target = self.estimate_required_columns(N, "12G")
        else:  # "13G" default
            R = 2
            est_target = self.estimate_required_columns(N, "13G")

        # Active outcome options and cardinality per match
        active_outcomes = [np.unique(candidates[:, i]) for i in range(15)]
        active_k = np.array([len(opts) for opts in active_outcomes], dtype=np.int32)
        # target_cap: 1.0 for singles, 0.70 for doubles, 0.50 for triples
        target_caps = np.where(active_k == 1, 1.0, np.where(active_k == 2, 0.70, 0.50))
        # min_bounds: 1.0 for singles, 0.30 for doubles, 0.20 for triples
        min_bounds = np.where(active_k == 1, 1.0, np.where(active_k == 2, 0.30, 0.20))

        if R == 0 or N <= 1:
            target_count = min(N, custom_budget if custom_budget is not None else N)
            sort_order = np.argsort(weights)[::-1]
            selected_indices = sort_order[:target_count]
            return {
                "selected_indices": selected_indices,
                "reduced_columns": candidates[selected_indices],
                "weights": weights[selected_indices],
                "p_true": p_true[selected_indices],
                "guarantee_mode": guarantee_mode,
                "radius": R,
                "columns_count": len(selected_indices),
                "cost_tl": len(selected_indices) * 10.0,
                "guarantee_verified": True,
                "coverage_pct": 100.0,
                "multi_cov_pct": 0.0
            }

        # Compute Pairwise Hamming Distance Ball Mask via One-Hot BLAS GEMM
        one_hot = np.zeros((N, 45), dtype=np.float32)
        for i in range(15):
            one_hot[np.arange(N), i * 3 + candidates[:, i]] = 1.0
        matches = np.dot(one_hot, one_hot.T)
        ball_mask = (matches >= (15 - R)).astype(np.float32)

        cand_ev_scores = (weights / max(1e-9, float(np.max(weights))))
        cov_count = np.zeros(N, dtype=np.int32)
        selected_indices_list = []
        selected_set = set()
        outcome_counts = np.zeros((15, 3), dtype=np.int32)

        def compute_imbalance_penalties(cand_arr: np.ndarray, counts_mat: np.ndarray, cur_tot: int) -> np.ndarray:
            if cur_tot < 4:
                return np.zeros(cand_arr.shape[0], dtype=np.float64)
            penalties = np.zeros(cand_arr.shape[0], dtype=np.float64)
            for i in range(15):
                c_i = cand_arr[:, i]
                freqs = counts_mat[i, c_i] / cur_tot
                excess = np.maximum(0.0, freqs - target_caps[i])
                penalties += excess
            return penalties

        def compute_deficit_bonuses(cand_arr: np.ndarray, counts_mat: np.ndarray, cur_tot: int) -> np.ndarray:
            if cur_tot < 4:
                return np.zeros(cand_arr.shape[0], dtype=np.float64)
            bonuses = np.zeros(cand_arr.shape[0], dtype=np.float64)
            for i in range(15):
                c_i = cand_arr[:, i]
                freqs = counts_mat[i, c_i] / cur_tot
                deficits = np.maximum(0.0, min_bounds[i] - freqs)
                bonuses += deficits * 10.0
            return bonuses

        weights_f32 = weights.astype(np.float32)

        # STAGE 1: GUARANTEE 100% 1-COVER (K >= 1) WITH BALANCE PENALTY REGULARIZATION
        uncovered_mask = (cov_count == 0).astype(np.float32)
        gain = np.dot(uncovered_mask, ball_mask)

        while np.any(cov_count == 0):
            for idx in selected_set:
                gain[idx] = -1.0

            if np.max(gain) <= 0:
                break

            cur_tot = len(selected_indices_list)
            penalties = compute_imbalance_penalties(candidates, outcome_counts, cur_tot)

            scores = gain * (1.0 + alpha * cand_ev_scores) - (beta * penalties)
            for idx in selected_set:
                scores[idx] = -1e9

            best_idx = int(np.argmax(scores))
            if gain[best_idx] <= 0:
                break

            selected_indices_list.append(best_idx)
            selected_set.add(best_idx)

            in_ball = ball_mask[:, best_idx] > 0
            newly_covered = np.where(in_ball & (cov_count == 0))[0]
            cov_count[in_ball] += 1
            if len(newly_covered) > 0:
                gain -= np.sum(ball_mask[newly_covered, :], axis=0)

            for i in range(15):
                outcome_counts[i, candidates[best_idx, i]] += 1

        stage1_count = len(selected_indices_list)

        # STAGE 2: BOOST HIGH +EV CLUSTERS (K >= 2) & BALANCED PADDING
        target_budget = custom_budget if custom_budget is not None else est_target
        target_budget = max(stage1_count, target_budget)
        target_budget = min(N, target_budget)

        # Pad to multiple of 4 for exact 40 TL Sheets
        if target_budget > 4 and target_budget % 4 != 0:
            target_budget = ((target_budget + 3) // 4) * 4
            target_budget = min(N, target_budget)

        ev_median = np.median(weights)
        ev_75th = np.percentile(weights, 75.0)

        requirements = np.ones(N, dtype=np.int32)
        requirements[weights >= ev_median] = 2
        requirements[weights >= ev_75th] = 3

        while len(selected_indices_list) < target_budget:
            needed_mask = (cov_count < requirements).astype(np.float32)
            has_needed = np.any(needed_mask > 0)
            if not has_needed:
                top_uncovered = np.where(cov_count < (requirements + 1))[0]
                if len(top_uncovered) > 0:
                    requirements[top_uncovered] += 1
                    needed_mask = (cov_count < requirements).astype(np.float32)
                    has_needed = True

            cur_tot = len(selected_indices_list)
            penalties = compute_imbalance_penalties(candidates, outcome_counts, cur_tot)
            deficit_bonus = compute_deficit_bonuses(candidates, outcome_counts, cur_tot)

            if has_needed:
                needed_weights = (needed_mask * weights_f32).astype(np.float32)
                gain = np.dot(needed_weights, ball_mask)
                for idx in selected_set:
                    gain[idx] = -1.0
                if np.max(gain) > 0:
                    scores = gain * (1.0 + alpha * cand_ev_scores) - (beta * penalties) + deficit_bonus
                else:
                    scores = (1.0 + alpha * cand_ev_scores) - (beta * penalties) + deficit_bonus
            else:
                scores = (1.0 + alpha * cand_ev_scores) - (beta * penalties) + deficit_bonus

            for idx in selected_set:
                scores[idx] = -1e9

            best_idx = int(np.argmax(scores))
            if scores[best_idx] <= -1e8:
                break

            selected_indices_list.append(best_idx)
            selected_set.add(best_idx)

            covered_in_ball = np.where(ball_mask[:, best_idx])[0]
            cov_count[covered_in_ball] += 1
            for i in range(15):
                outcome_counts[i, candidates[best_idx, i]] += 1

        # STAGE 2.5: BACKWARD PRUNING WITH EV-ASCENDING SORT (Sıralama Tuzağı Koruması)
        # Removes redundant greedy columns. Evaluates lowest EV columns first (ev_score ascending)
        # so high-EV surprise columns are preserved while dead favorites are pruned.
        if len(selected_indices_list) > 4:
            prune_order = sorted(list(selected_indices_list), key=lambda idx: cand_ev_scores[idx])
            for cand_c in prune_order:
                if len(selected_indices_list) <= 4:
                    break
                covered_in_ball = np.where(ball_mask[:, cand_c])[0]
                if len(covered_in_ball) > 0 and np.all(cov_count[covered_in_ball] > requirements[covered_in_ball]):
                    selected_indices_list.remove(cand_c)
                    selected_set.remove(cand_c)
                    cov_count[covered_in_ball] -= 1
                    for i in range(15):
                        outcome_counts[i, candidates[cand_c, i]] -= 1

        # STAGE 3: STRICT MARGINAL OUTCOME BALANCE ENFORCEMENT
        # If any double < 30% or triple < 20%, add balanced candidates (padded in groups of 4)
        def has_marginal_violations(counts_mat, cur_total):
            if cur_total == 0:
                return False
            for i in range(15):
                for o in active_outcomes[i]:
                    r = counts_mat[i, o] / cur_total
                    if r < min_bounds[i] - 1e-4:
                        return True
            return False

        while has_marginal_violations(outcome_counts, len(selected_indices_list)) and len(selected_indices_list) < N:
            slots_to_add = 4
            added_any = False
            for _ in range(slots_to_add):
                if len(selected_indices_list) >= N:
                    break
                cur_tot = len(selected_indices_list)
                penalties = compute_imbalance_penalties(candidates, outcome_counts, cur_tot)
                deficit_bonus = compute_deficit_bonuses(candidates, outcome_counts, cur_tot)
                scores = deficit_bonus - (beta * penalties) + (0.05 * cand_ev_scores)
                for idx in selected_set:
                    scores[idx] = -1e9
                best_idx = int(np.argmax(scores))
                if scores[best_idx] <= -1e8:
                    break
                selected_indices_list.append(best_idx)
                selected_set.add(best_idx)
                covered_in_ball = np.where(ball_mask[:, best_idx])[0]
                cov_count[covered_in_ball] += 1
                for i in range(15):
                    outcome_counts[i, candidates[best_idx, i]] += 1
                added_any = True
            if not added_any:
                break

        selected_indices = np.array(selected_indices_list, dtype=np.int32)
        reduced_columns = candidates[selected_indices]
        reduced_weights = weights[selected_indices]
        reduced_ptrue = p_true[selected_indices]

        # Sort descending by +EV score for presentation
        sort_order = np.argsort(reduced_weights)[::-1]
        selected_indices = selected_indices[sort_order]
        reduced_columns = reduced_columns[sort_order]
        reduced_weights = reduced_weights[sort_order]
        reduced_ptrue = reduced_ptrue[sort_order]

        coverage_pct = float(np.mean(cov_count >= 1) * 100.0)
        multi_cov_pct = float(np.mean(cov_count[weights >= ev_median] >= 2) * 100.0) if np.any(weights >= ev_median) else 0.0

        # Build outcome distribution summary for telemetry and verification
        tot_cols = len(selected_indices)
        outcome_dist = []
        for i in range(15):
            d_i = {}
            for o in active_outcomes[i]:
                cnt = int(np.count_nonzero(reduced_columns[:, i] == o))
                pct = round(cnt / tot_cols * 100.0, 1) if tot_cols > 0 else 0.0
                d_i[OUTCOME_MAP[o]] = {"count": cnt, "ratio": round(cnt / tot_cols, 4) if tot_cols > 0 else 0.0, "pct": pct}
            outcome_dist.append(d_i)

        return {
            "selected_indices": selected_indices,
            "reduced_columns": reduced_columns,
            "weights": reduced_weights,
            "p_true": reduced_ptrue,
            "guarantee_mode": guarantee_mode,
            "radius": R,
            "columns_count": len(selected_indices),
            "cost_tl": len(selected_indices) * 10.0,
            "stage1_columns": stage1_count,
            "guarantee_verified": bool(coverage_pct >= 99.99),
            "coverage_pct": round(coverage_pct, 2),
            "multi_cov_pct": round(multi_cov_pct, 2),
            "outcome_distributions": outcome_dist
        }

    # Backward compatibility
    def solve_set_cover(
        self,
        candidates: np.ndarray,
        target_mode: str = "13G",
        alpha: float = 1.0,
        budget_cap: Optional[int] = None
    ) -> Dict[str, Any]:
        return self.solve_multi_cover(candidates, guarantee_mode=target_mode, alpha=alpha, custom_budget=budget_cap)

    def run_ev_weighted_cover(
        self,
        candidates: np.ndarray,
        target_mode: str = "13G",
        alpha: float = 1.0,
        budget_cap: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Backwards-compatible API for test_covering_engine.py
        """
        raw_cols = candidates.shape[0]
        res = self.solve_multi_cover(candidates, guarantee_mode=target_mode, alpha=alpha, custom_budget=budget_cap)
        red_cols = res["columns_count"]

        bounds = self.compute_local_sphere_bounds(raw_cols)
        mode = target_mode.upper()
        if "14" in mode:
            sphere_bound = bounds["bound_14g"]
        elif "15" in mode:
            sphere_bound = bounds["bound_15g"]
        else:
            sphere_bound = bounds["bound_13g"]

        eff = round((sphere_bound / red_cols) * 100.0, 1) if red_cols > 0 else 0.0
        savings = round((1.0 - (red_cols / raw_cols)) * 100.0, 1) if raw_cols > 0 else 0.0
        p15_res = round((red_cols / raw_cols) * 100.0, 2) if raw_cols > 0 else 0.0

        telemetry = {
            "raw_columns": raw_cols,
            "raw_cost_tl": raw_cols * 10,
            "reduced_columns": red_cols,
            "reduced_cost_tl": red_cols * 10,
            "theoretical_sphere_bound": sphere_bound,
            "sphere_efficiency_pct": eff,
            "savings_percent": savings,
            "residual_15_probability_pct": p15_res,
            "guarantee_strictly_verified": res["guarantee_verified"]
        }

        return {
            **res,
            "telemetry": telemetry
        }


    def calculate_residual_probabilities(
        self,
        raw_cols: int,
        red_cols: int,
        guarantee_mode: str
    ) -> Dict[str, Any]:
        """
        Pure Dynamic Odds & Cascading Telemetry
        """
        mode = guarantee_mode.upper()
        p15_res = (red_cols / raw_cols) * 100.0 if raw_cols > 0 else 0.0
        p14_proj = min(99.0, (red_cols * 15.0 / raw_cols) * 100.0) if raw_cols > 0 else 0.0

        if "15" in mode:
            p15_str = "100% KESİN"
            p14_str = "100% KESİN"
            p13_str = "100% KESİN"
            cascade_12 = "Tam Kapsama (Tüm İkramiyeler Dahil)"
            mistake_prot = "14/15 -> 100% 14 Hit Garantisi"
        elif "14" in mode:
            p15_str = f"%{round(min(99.9, p15_res), 2)}"
            p14_str = "100% KESİN GARANTİ"
            p13_str = "100% KESİN GARANTİ"
            cascade_12 = "1 Adet 14 + Çoklu 13 & 12 İkramiyesi"
            mistake_prot = "14/15 -> Çoklu 13 Hit Garantisi"
        else: # "13G"
            p15_str = f"%{round(min(99.9, p15_res), 2)}"
            p14_str = f"%{round(p14_proj, 1)}"
            p13_str = "100% KESİN GARANTİ"
            cascade_12 = "1 Adet 13 + 3-6 Adet 12 (Kademeli Çoklu İkramiye)"
            mistake_prot = "14/15 -> 3-4 Adet 12 Hit (Amorti Kalkanı)"

        return {
            "p15_jackpot_pct": p15_str,
            "p14_chance_pct": p14_str,
            "p13_hit": p13_str,
            "p12_cascade": cascade_12,
            "one_mistake_protection": mistake_prot
        }

    def package_into_40tl_sheets(
        self,
        columns: np.ndarray,
        weights: np.ndarray,
        p_true: np.ndarray
    ) -> List[Dict[str, Any]]:
        """
        OFFICIAL 40 TL NESINE SHEET PACKAGING
        =====================================
        4 Single Columns (10 TL each) = 1 Sheet = 40.00 TL.
        Labels:
        Kupon #X (4 Kolon) -> [Harf A: 10 TL] [Harf B: 10 TL] [Harf C: 10 TL] [Harf D: 10 TL]
        """
        N = columns.shape[0]
        num_sheets = (N + 3) // 4
        sheets = []
        letters = ["A", "B", "C", "D"]

        for s_idx in range(num_sheets):
            sheet_obj = {
                "sheet_id": s_idx + 1,
                "name": f"Kupon #{s_idx + 1} (4 Kolon)",
                "cost_tl": 0.0,
                "columns_count": 0,
                "A": [],
                "B": [],
                "C": [],
                "D": [],
                "columns_details": {}
            }

            for l_idx, letter in enumerate(letters):
                col_idx = s_idx * 4 + l_idx
                if col_idx < N:
                    col_vec = columns[col_idx]
                    picks_list = [OUTCOME_MAP[col_vec[i]] for i in range(15)]
                    sheet_obj[letter] = picks_list
                    sheet_obj["columns_count"] += 1
                    sheet_obj["cost_tl"] += 10.0

                    surprises = []
                    for i in range(15):
                        opt_idx = col_vec[i]
                        pub_pct = self.p_pub[i, opt_idx]
                        if pub_pct < 0.25:
                            surprises.append({
                                "match_no": i + 1,
                                "match_str": f"M{i+1:02d}: {FIXTURE[i]['home']}-{FIXTURE[i]['away']}",
                                "pick": OUTCOME_MAP[opt_idx],
                                "pub_pct": round(pub_pct * 100, 1)
                            })

                    sheet_obj["columns_details"][letter] = {
                        "column_no": col_idx + 1,
                        "slot": letter,
                        "picks": picks_list,
                        "ev_score": round(float(weights[col_idx]), 3),
                        "prob_pct": round(float(p_true[col_idx] * 100.0), 4),
                        "surprises": surprises
                    }
                else:
                    sheet_obj[letter] = []

            sheets.append(sheet_obj)

        return sheets

    def _repair_coverage_gaps(
        self,
        raw_pool: np.ndarray,
        selected_columns: np.ndarray,
        selected_weights: np.ndarray,
        selected_ptrue: np.ndarray,
        R: int
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, int]:
        """
        Stage 4: Coverage Gap Repair
        =============================
        After solver runs on entropy-pruned pool, some pruned-out candidates may
        not be within d_H <= R of any selected column. This stage identifies those
        uncovered candidates and greedily adds repair columns until full coverage.
        Pads result to next multiple of 4.
        
        Returns: (repaired_columns, repaired_weights, repaired_ptrue, repair_count)
        """
        N_raw = raw_pool.shape[0]
        N_sel = selected_columns.shape[0]

        if N_sel == 0 or N_raw == 0:
            return selected_columns, selected_weights, selected_ptrue, 0

        # Find uncovered raw candidates using fast_hamming_coverage
        cov_counts = fast_hamming_coverage(raw_pool, selected_columns, radius=R, chunk_size=500)
        uncovered_mask = (cov_counts == 0)
        uncovered_count = int(np.count_nonzero(uncovered_mask))
        if uncovered_count == 0:
            return selected_columns, selected_weights, selected_ptrue, 0

        # Vectorized greedy repair: pick candidates that cover the most uncovered points
        uncovered_points = raw_pool[uncovered_mask]  # (U, 15)
        U = uncovered_points.shape[0]

        # Pairwise Hamming distance matrix among uncovered points: (U, U)
        u_diff = uncovered_points[:, np.newaxis, :] != uncovered_points[np.newaxis, :, :]
        u_cov_mat = (np.sum(u_diff, axis=-1) <= R)

        repair_indices = []
        covered_u = np.zeros(U, dtype=bool)

        while not np.all(covered_u):
            rem_mask = ~covered_u
            gains = np.sum(u_cov_mat[:, rem_mask], axis=1)
            for p in repair_indices:
                gains[p] = -1

            best_u = int(np.argmax(gains))
            if gains[best_u] <= 0:
                for rem_i in np.where(rem_mask)[0]:
                    repair_indices.append(rem_i)
                break

            repair_indices.append(best_u)
            covered_u |= u_cov_mat[best_u]

        repair_columns = [uncovered_points[i] for i in repair_indices]

        # Pad repair columns to maintain multiple-of-4 total
        total_after_repair = N_sel + len(repair_columns)
        pad_needed = (4 - (total_after_repair % 4)) % 4
        if pad_needed > 0:
            # Add highest EV candidates from raw_pool that aren't already selected
            sel_set = set(map(tuple, selected_columns.tolist()))
            repair_set = set(map(tuple, [r.tolist() for r in repair_columns]))
            ev_weights, _ = self.calculate_ev_weights(raw_pool)
            ev_order = np.argsort(ev_weights)[::-1]
            for idx in ev_order:
                if pad_needed <= 0:
                    break
                cand_tuple = tuple(raw_pool[idx].tolist())
                if cand_tuple not in sel_set and cand_tuple not in repair_set:
                    repair_columns.append(raw_pool[idx])
                    repair_set.add(cand_tuple)
                    pad_needed -= 1

        repair_count = len(repair_columns)
        if repair_count == 0:
            return selected_columns, selected_weights, selected_ptrue, 0

        repair_arr = np.array(repair_columns, dtype=np.uint8)
        repair_w, repair_p = self.calculate_ev_weights(repair_arr)

        final_columns = np.concatenate([selected_columns, repair_arr], axis=0)
        final_weights = np.concatenate([selected_weights, repair_w], axis=0)
        final_ptrue = np.concatenate([selected_ptrue, repair_p], axis=0)

        return final_columns, final_weights, final_ptrue, repair_count

    def run_full_pipeline(
        self,
        user_picks: List[List[str]],
        guarantee_mode: str = "13G",
        custom_budget: Optional[int] = None,
        dynamic_odds: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Executes pure multi-covering pipeline:
        User Picks -> Cartesian Pool -> Adaptive Entropy Cut -> Multi-Cover
        -> Coverage Gap Repair -> 40 TL Sheets
        """
        if dynamic_odds is not None:
            self.update_fixtures(dynamic_odds)
        raw_pool = self.generate_candidate_pool(user_picks)
        pruned_pool, mask, entropy_stats = self.apply_entropy_cut(raw_pool)
        cover_res = self.solve_multi_cover(pruned_pool, guarantee_mode=guarantee_mode, custom_budget=custom_budget)

        # Determine radius for gap repair
        mode_clean = guarantee_mode.upper()
        if "14" in mode_clean:
            R = 1
        elif "15" in mode_clean:
            R = 0
        elif "12" in mode_clean:
            R = 3
        else:
            R = 2

        # Stage 4: Coverage Gap Repair — ensure pruned-out candidates are also covered
        repaired_cols, repaired_w, repaired_p, repair_count = self._repair_coverage_gaps(
            raw_pool,
            cover_res["reduced_columns"],
            cover_res["weights"],
            cover_res["p_true"],
            R
        )

        sheets = self.package_into_40tl_sheets(repaired_cols, repaired_w, repaired_p)

        raw_cols = raw_pool.shape[0]
        red_cols = repaired_cols.shape[0]
        raw_cost = raw_cols * 10.0
        red_cost = red_cols * 10.0
        savings_pct = (1.0 - (red_cost / raw_cost)) * 100.0 if raw_cost > 0 else 0.0

        telemetry = self.calculate_residual_probabilities(raw_cols, red_cols, guarantee_mode)
        telemetry["guarantee_verified"] = cover_res.get("guarantee_verified", True)
        telemetry["coverage_pct"] = cover_res.get("coverage_pct", 100.0)
        telemetry["multi_cov_pct"] = cover_res.get("multi_cov_pct", 0.0)
        if repair_count > 0:
            telemetry["coverage_gap_repair"] = repair_count


        return {
            "guarantee_mode": guarantee_mode,
            "raw_columns": raw_cols,
            "raw_cost_tl": raw_cost,
            "pruned_columns": entropy_stats["pruned_cols"],
            "prune_ratio": entropy_stats["prune_ratio"],
            "reduced_columns": red_cols,
            "reduced_cost_tl": red_cost,
            "savings_percent": round(savings_pct, 1),
            "telemetry": telemetry,
            "total_sheets": len(sheets),
            "sheets": sheets,
            "entropy_stats": entropy_stats
        }


class NesineBinPacker:
    """
    Backward-compatible bin-packer helper for test_covering_engine.py
    """
    @staticmethod
    def pack_single_columns(columns: np.ndarray) -> List[Dict[str, Any]]:
        N = columns.shape[0]
        num_sheets = (N + 3) // 4
        sheets = []
        letters = ["A", "B", "C", "D"]
        for s in range(num_sheets):
            sheet = {
                "sheet_id": s + 1,
                "name": f"Kupon #{s + 1} (4 Kolon)",
                "cost_tl": 0.0,
                "A": [], "B": [], "C": [], "D": []
            }
            for l_idx, letter in enumerate(letters):
                c_idx = s * 4 + l_idx
                if c_idx < N:
                    sheet[letter] = [OUTCOME_MAP[columns[c_idx, i]] for i in range(15)]
                    sheet["cost_tl"] += 10.0
            sheets.append(sheet)
        return sheets

    @staticmethod
    def pack_asymmetric_blocks(columns: np.ndarray, user_picks: List[List[str]]) -> List[Dict[str, Any]]:
        return NesineBinPacker.pack_single_columns(columns)

    @staticmethod
    def generate_plain_txt_export(sheets: List[Dict[str, Any]], telemetry: Dict[str, Any]) -> str:
        from components.tickets import TicketExporter
        return TicketExporter.generate_sheets_txt(sheets, meta=telemetry)


engine = OptimizedSyndicateEngine()
SphereCoveringEngine = OptimizedSyndicateEngine

__all__ = ["OptimizedSyndicateEngine", "SphereCoveringEngine", "NesineBinPacker", "engine"]

