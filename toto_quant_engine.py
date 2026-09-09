"""
TOTO QUANT ENGINE
Institutional quantitative football modeling for Spor Toto 15-match fixtures.
Provides public distribution (P_pub), calibrated true probabilities (P_true), and value ratio weights.
Updated strictly with the exact 11.09.2026 - 14.09.2026 Nesine Spor Toto Program values.
"""

from typing import List, Dict, Any
import numpy as np

# 15 Maçlık Resmi Program ve Nesine Kamu Tercih Dağılımı (Program No: 357)
FIXTURE: List[Dict[str, Any]] = [
    {
        "no": 1,
        "date": "11.09 20:00",
        "home": "Beşiktaş A.Ş.",
        "away": "Erzurumspor FK",
        "odds": [90.0, 7.0, 3.0],
        "p_pub": [0.90, 0.07, 0.03],
        "p_true": [0.86, 0.09, 0.05],
        "category": "TR"
    },
    {
        "no": 2,
        "date": "12.09 17:00",
        "home": "Eyüpspor",
        "away": "Çaykur Rizespor A.Ş.",
        "odds": [23.0, 27.0, 50.0],
        "p_pub": [0.23, 0.27, 0.50],
        "p_true": [0.26, 0.28, 0.46],
        "category": "TR"
    },
    {
        "no": 3,
        "date": "12.09 17:00",
        "home": "Samsunspor A.Ş.",
        "away": "Çorum FK",
        "odds": [58.0, 23.0, 19.0],
        "p_pub": [0.58, 0.23, 0.19],
        "p_true": [0.55, 0.25, 0.20],
        "category": "TR"
    },
    {
        "no": 4,
        "date": "12.09 20:00",
        "home": "Alanyaspor",
        "away": "Göztepe A.Ş.",
        "odds": [42.0, 31.0, 27.0],
        "p_pub": [0.42, 0.31, 0.27],
        "p_true": [0.40, 0.32, 0.28],
        "category": "TR"
    },
    {
        "no": 5,
        "date": "12.09 20:00",
        "home": "Konyaspor",
        "away": "Trabzonspor A.Ş.",
        "odds": [15.0, 18.0, 67.0],
        "p_pub": [0.15, 0.18, 0.67],
        "p_true": [0.19, 0.22, 0.59],
        "category": "TR"
    },
    {
        "no": 6,
        "date": "13.09 17:00",
        "home": "Gençlerbirliği",
        "away": "Kasımpaşa A.Ş.",
        "odds": [46.0, 28.0, 26.0],
        "p_pub": [0.46, 0.28, 0.26],
        "p_true": [0.43, 0.29, 0.28],
        "category": "TR"
    },
    {
        "no": 7,
        "date": "13.09 20:00",
        "home": "Amed Sportif",
        "away": "Başakşehir FK",
        "odds": [35.0, 27.0, 38.0],
        "p_pub": [0.35, 0.27, 0.38],
        "p_true": [0.35, 0.28, 0.37],
        "category": "TR"
    },
    {
        "no": 8,
        "date": "13.09 20:00",
        "home": "Galatasaray A.Ş.",
        "away": "Kocaelispor",
        "odds": [79.0, 15.0, 6.0],
        "p_pub": [0.79, 0.15, 0.06],
        "p_true": [0.76, 0.16, 0.08],
        "category": "TR"
    },
    {
        "no": 9,
        "date": "14.09 20:00",
        "home": "Gaziantep F.K. A.Ş.",
        "away": "Fenerbahçe A.Ş.",
        "odds": [11.0, 15.0, 74.0],
        "p_pub": [0.11, 0.15, 0.74],
        "p_true": [0.16, 0.19, 0.65],
        "category": "TR"
    },
    {
        "no": 10,
        "date": "12.09 16:30",
        "home": "Augsburg",
        "away": "B. Leverkusen",
        "odds": [24.0, 21.0, 55.0],
        "p_pub": [0.24, 0.21, 0.55],
        "p_true": [0.26, 0.24, 0.50],
        "category": "EU"
    },
    {
        "no": 11,
        "date": "11.09 21:45",
        "home": "Rennes",
        "away": "Marsilya",
        "odds": [32.0, 28.0, 40.0],
        "p_pub": [0.32, 0.28, 0.40],
        "p_true": [0.32, 0.29, 0.39],
        "category": "EU"
    },
    {
        "no": 12,
        "date": "12.09 17:00",
        "home": "Chelsea",
        "away": "Hull City",
        "odds": [83.0, 11.0, 6.0],
        "p_pub": [0.83, 0.11, 0.06],
        "p_true": [0.79, 0.13, 0.08],
        "category": "EU"
    },
    {
        "no": 13,
        "date": "13.09 18:30",
        "home": "Manchester United",
        "away": "Manchester City",
        "odds": [23.0, 26.0, 51.0],
        "p_pub": [0.23, 0.26, 0.51],
        "p_true": [0.26, 0.28, 0.46],
        "category": "EU"
    },
    {
        "no": 14,
        "date": "13.09 17:15",
        "home": "Levante",
        "away": "Barcelona",
        "odds": [6.0, 7.0, 87.0],
        "p_pub": [0.06, 0.07, 0.87],
        "p_true": [0.12, 0.13, 0.75],
        "category": "EU"
    },
    {
        "no": 15,
        "date": "12.09 19:00",
        "home": "Lazio",
        "away": "AC Milan",
        "odds": [25.0, 29.0, 46.0],
        "p_pub": [0.25, 0.29, 0.46],
        "p_true": [0.27, 0.30, 0.43],
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

