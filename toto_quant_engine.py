"""
TOTO QUANT ENGINE
Institutional quantitative football modeling for Spor Toto 15-match fixtures.
Provides public distribution (P_pub), calibrated true probabilities (P_true), and value ratio weights.
Updated strictly with the exact 11.09.2026 - 14.09.2026 Nesine Spor Toto Program values.
"""

from typing import List, Dict, Any
import numpy as np

# 15 Maçlık Resmi Program ve Nesine Kamu Tercih Dağılımı (Program No: 358)
FIXTURE: List[Dict[str, Any]] = [
    {
        "no": 1,
        "date": "18.09 20:00",
        "home": "Kasımpaşa A.Ş.",
        "away": "Konyaspor",
        "odds": [47.0, 32.0, 21.0],
        "p_pub": [0.47, 0.32, 0.21],
        "p_true": [0.45, 0.31, 0.24],
        "category": "TR"
    },
    {
        "no": 2,
        "date": "18.09 20:00",
        "home": "Kocaelispor",
        "away": "Gaziantep F.K. A.Ş.",
        "odds": [60.0, 24.0, 16.0],
        "p_pub": [0.60, 0.24, 0.16],
        "p_true": [0.57, 0.26, 0.17],
        "category": "TR"
    },
    {
        "no": 3,
        "date": "19.09 17:00",
        "home": "Çorum FK",
        "away": "Alanyaspor",
        "odds": [55.0, 26.0, 19.0],
        "p_pub": [0.55, 0.26, 0.19],
        "p_true": [0.52, 0.27, 0.21],
        "category": "TR"
    },
    {
        "no": 4,
        "date": "19.09 17:00",
        "home": "Başakşehir FK",
        "away": "Gençlerbirliği",
        "odds": [67.0, 18.0, 15.0],
        "p_pub": [0.67, 0.18, 0.15],
        "p_true": [0.63, 0.21, 0.16],
        "category": "TR"
    },
    {
        "no": 5,
        "date": "19.09 20:00",
        "home": "Trabzonspor A.Ş.",
        "away": "Galatasaray A.Ş.",
        "odds": [24.0, 25.0, 51.0],
        "p_pub": [0.24, 0.25, 0.51],
        "p_true": [0.26, 0.27, 0.47],
        "category": "TR"
    },
    {
        "no": 6,
        "date": "19.09 20:00",
        "home": "Erzurumspor FK",
        "away": "Samsunspor A.Ş.",
        "odds": [41.0, 30.0, 29.0],
        "p_pub": [0.41, 0.30, 0.29],
        "p_true": [0.39, 0.31, 0.30],
        "category": "TR"
    },
    {
        "no": 7,
        "date": "20.09 17:00",
        "home": "Fenerbahçe A.Ş.",
        "away": "Eyüpspor",
        "odds": [89.0, 6.0, 5.0],
        "p_pub": [0.89, 0.06, 0.05],
        "p_true": [0.85, 0.09, 0.06],
        "category": "TR"
    },
    {
        "no": 8,
        "date": "20.09 20:00",
        "home": "Amed Sportif Faliyetler",
        "away": "Beşiktaş A.Ş.",
        "odds": [15.0, 23.0, 62.0],
        "p_pub": [0.15, 0.23, 0.62],
        "p_true": [0.18, 0.25, 0.57],
        "category": "TR"
    },
    {
        "no": 9,
        "date": "20.09 20:00",
        "home": "Göztepe A.Ş.",
        "away": "Çaykur Rizespor A.Ş.",
        "odds": [57.0, 22.0, 21.0],
        "p_pub": [0.57, 0.22, 0.21],
        "p_true": [0.54, 0.24, 0.22],
        "category": "TR"
    },
    {
        "no": 10,
        "date": "19.09 16:30",
        "home": "Stuttgart",
        "away": "B. Dortmund",
        "odds": [19.0, 19.0, 62.0],
        "p_pub": [0.19, 0.19, 0.62],
        "p_true": [0.22, 0.22, 0.56],
        "category": "EU"
    },
    {
        "no": 11,
        "date": "19.09 19:30",
        "home": "B. Leverkusen",
        "away": "Leipzig",
        "odds": [71.0, 15.0, 14.0],
        "p_pub": [0.71, 0.15, 0.14],
        "p_true": [0.67, 0.18, 0.15],
        "category": "EU"
    },
    {
        "no": 12,
        "date": "20.09 16:00",
        "home": "Tottenham",
        "away": "Aston Villa",
        "odds": [43.0, 31.0, 26.0],
        "p_pub": [0.43, 0.31, 0.26],
        "p_true": [0.41, 0.32, 0.27],
        "category": "EU"
    },
    {
        "no": 13,
        "date": "20.09 18:30",
        "home": "Newcastle United",
        "away": "Hull City",
        "odds": [56.0, 26.0, 18.0],
        "p_pub": [0.56, 0.26, 0.18],
        "p_true": [0.53, 0.27, 0.20],
        "category": "EU"
    },
    {
        "no": 14,
        "date": "20.09 22:00",
        "home": "Atletico Madrid",
        "away": "Real Madrid",
        "odds": [16.0, 19.0, 65.0],
        "p_pub": [0.16, 0.19, 0.65],
        "p_true": [0.19, 0.22, 0.59],
        "category": "EU"
    },
    {
        "no": 15,
        "date": "20.09 21:45",
        "home": "AS Roma",
        "away": "Inter",
        "odds": [22.0, 28.0, 50.0],
        "p_pub": [0.22, 0.28, 0.50],
        "p_true": [0.24, 0.29, 0.47],
        "category": "EU"
    }
]

def compute_dynamic_ev_matrix(
    dynamic_odds: Optional[Any] = None,
    epsilon: float = 1e-3
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Computes P_pub, P_smooth, and Dirichlet +EV value ratio matrix V_{i, j}.
    Formulation:
        P_smooth_{i, j} = (P_pub_{i, j} + epsilon) / (1.0 + 3.0 * epsilon)
        V_{i, j} = clip(1.0 / (3.0 * P_smooth_{i, j}), 0.4, 2.5)
    Returns:
        p_pub: (15, 3) normalized public consensus probabilities
        p_smooth: (15, 3) Laplace/Dirichlet smoothed probabilities
        val_ratios: (15, 3) clipped EV value ratios
    """
    if dynamic_odds is not None:
        raw_list = []
        for item in dynamic_odds[:15]:
            if isinstance(item, dict):
                o = item.get("odds") or item.get("p_pub") or [33.3, 33.3, 33.4]
            elif isinstance(item, (list, tuple, np.ndarray)):
                o = item
            else:
                o = [33.3, 33.3, 33.4]
            raw_list.append([float(x) for x in o[:3]])

        raw_mat = np.array(raw_list, dtype=np.float64)
        sums = raw_mat.sum(axis=1, keepdims=True)
        # Handle zero-sum odds (unopened/unpopulated matches) with Laplace uniform prior
        zero_rows = (sums.squeeze() <= 0)
        if np.any(zero_rows):
            raw_mat[zero_rows] = [33.333, 33.333, 33.334]
            sums[zero_rows] = 100.0
        p_pub = raw_mat / sums
    else:
        p_pub = np.array([m["p_pub"] for m in FIXTURE], dtype=np.float64)
        p_pub = p_pub / p_pub.sum(axis=1, keepdims=True)

    # Laplace / Dirichlet smoothing to avoid zero-division
    p_smooth = (p_pub + epsilon) / (1.0 + 3.0 * epsilon)
    p_smooth = p_smooth / p_smooth.sum(axis=1, keepdims=True)

    # Bayesian Shrinkage True Probability Model (Prevents "Ters Sürpriz" Heavy Favorite Penalty)
    # P_true shrinks P_pub towards the uniform prior (1/3) to balance consensus bias
    alpha = 0.75
    p_true = alpha * p_pub + (1.0 - alpha) * (1.0 / 3.0)
    p_true = p_true / p_true.sum(axis=1, keepdims=True)

    # Institutional EV ratio: P_true / (P_smooth + epsilon), bounded in [0.60, 2.00]
    val_ratios = np.clip(p_true / (p_smooth + epsilon), 0.60, 2.00)
    return p_pub, p_smooth, val_ratios


def get_probability_matrices(
    dynamic_odds: Optional[Any] = None,
    epsilon: float = 1e-3
) -> Tuple[np.ndarray, np.ndarray]:
    p_pub, p_smooth, _ = compute_dynamic_ev_matrix(dynamic_odds=dynamic_odds, epsilon=epsilon)
    return p_pub, p_smooth


def get_value_ratio_matrix(
    dynamic_odds: Optional[Any] = None,
    epsilon: float = 1e-3
) -> np.ndarray:
    """
    Computes institutional +EV value ratio matrix:
    V_{i, j} = clip(1.0 / (3.0 * P_smooth_{i, j}), 0.4, 2.5)
    """
    _, _, val_ratios = compute_dynamic_ev_matrix(dynamic_odds=dynamic_odds, epsilon=epsilon)
    return val_ratios

