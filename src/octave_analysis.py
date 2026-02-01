"""
Modular utilities for Cosmic Octaves analysis.

Provides core functions reused by permutation tests and extensions.
"""

from typing import List, Sequence, Tuple, Optional
import numpy as np

# Default 15 log10(L) values (same as existing scripts)
DEFAULT_LOGS = np.array([
    -15.08, -10.28, -7.96, -6.00, -3.30, -0.046, 3.00,
    6.80, 8.84, 12.65, 16.67, 18.665, 20.70, 23.84, 26.64
])

# Default canonical pairs (small_index, large_index)
DEFAULT_PAIRS: List[Tuple[int, int]] = [
    (0, 8), (1, 9), (2, 10), (3, 11), (4, 12), (5, 13), (6, 14)
]


def get_deviations(logs: Sequence[float], delta: float = 24.0,
                   pairs: Optional[Sequence[Tuple[int, int]]] = None) -> np.ndarray:
    """Return deviations |(L_j - L_i) - delta| for each pair.

    Parameters
    - logs: sequence of log10(length) values
    - delta: target log10 ratio (default 24)
    - pairs: iterable of (i, j) index pairs; falls back to DEFAULT_PAIRS
    """
    if pairs is None:
        pairs = DEFAULT_PAIRS
    logs_arr = np.asarray(logs)
    return np.array([abs((logs_arr[j] - logs_arr[i]) - delta) for i, j in pairs])


def count_strong_matches(logs: Sequence[float], delta: float = 24.0,
                         threshold: float = 0.2,
                         pairs: Optional[Sequence[Tuple[int, int]]] = None) -> int:
    """Count pairs with deviation <= threshold.
    """
    devs = get_deviations(logs, delta=delta, pairs=pairs)
    return int(np.sum(devs <= threshold))


def max_strong_matches_in_scan(logs: Sequence[float],
                               delta_min: float = 22.0,
                               delta_max: float = 26.0,
                               step: float = 0.05,
                               threshold: float = 0.2,
                               pairs: Optional[Sequence[Tuple[int, int]]] = None) -> Tuple[int, float]:
    """Scan delta over [delta_min, delta_max] and return (max_strong, best_delta).
    """
    deltas = np.arange(delta_min, delta_max + step/2, step)
    max_strong = -1
    best_delta = float('nan')
    for delta in deltas:
        strong = count_strong_matches(logs, delta=delta, threshold=threshold, pairs=pairs)
        if strong > max_strong:
            max_strong = strong
            best_delta = float(delta)
    return max_strong, best_delta


__all__ = [
    'DEFAULT_LOGS', 'DEFAULT_PAIRS', 'get_deviations', 'count_strong_matches',
    'max_strong_matches_in_scan'
]
