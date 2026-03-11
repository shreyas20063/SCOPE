"""Routh-Hurwitz stability criterion utilities.

Provides standalone functions for computing Routh arrays and stability
ranges that can be used by any simulator.
"""

from typing import Any, Dict, List

import numpy as np


def compute_routh_array(char_poly: np.ndarray) -> Dict[str, Any]:
    """Compute the Routh-Hurwitz stability array for a characteristic polynomial.

    Args:
        char_poly: 1D array of polynomial coefficients, highest power first.
                   e.g. [1, 6, 11, 6] for s^3 + 6s^2 + 11s + 6.

    Returns:
        Dict with keys: rows, powers, first_column, sign_changes, rhp_poles,
        flags, stable.
    """
    empty = {"rows": [], "powers": [], "first_column": [], "sign_changes": 0,
             "rhp_poles": 0, "flags": [], "stable": True}

    char_poly = np.asarray(char_poly, dtype=float)
    n = len(char_poly) - 1  # polynomial degree
    if n < 1:
        return empty

    # Build Routh table
    n_rows = n + 1
    n_cols = (n + 2) // 2
    routh = np.zeros((n_rows, n_cols))
    flags: List[Dict[str, Any]] = []

    # Fill first two rows from coefficients (alternating indices)
    for j in range(n_cols):
        idx_even = 2 * j
        if idx_even < len(char_poly):
            routh[0][j] = char_poly[idx_even]
        idx_odd = 2 * j + 1
        if idx_odd < len(char_poly):
            routh[1][j] = char_poly[idx_odd]

    # Compute remaining rows
    epsilon = 1e-6
    for i in range(2, n_rows):
        if abs(routh[i - 1][0]) < 1e-12:
            if np.all(np.abs(routh[i - 1]) < 1e-12):
                # All-zero row: use derivative of auxiliary polynomial
                aux_order = n - (i - 2)
                for j in range(n_cols):
                    power = aux_order - 2 * j
                    if power >= 0:
                        routh[i - 1][j] = power * routh[i - 2][j]
                flags.append({"row": i - 1, "type": "auxiliary", "aux_order": aux_order})
            else:
                # Zero in first column only: replace with epsilon
                routh[i - 1][0] = epsilon
                flags.append({"row": i - 1, "type": "epsilon"})

        pivot = routh[i - 1][0]
        for j in range(n_cols - 1):
            upper = routh[i - 2][j + 1] if (j + 1) < n_cols else 0.0
            lower = routh[i - 1][j + 1] if (j + 1) < n_cols else 0.0
            routh[i][j] = (pivot * upper - routh[i - 2][0] * lower) / pivot

    # Count sign changes in first column
    first_col = routh[:, 0]
    sign_changes = 0
    for i in range(1, len(first_col)):
        if first_col[i - 1] * first_col[i] < 0:
            sign_changes += 1

    # Power labels
    powers = [
        f"s^{n - i}" if (n - i) > 1 else ("s" if (n - i) == 1 else "1")
        for i in range(n_rows)
    ]

    # Serialize
    rows_list = [[float(routh[i][j]) for j in range(n_cols)] for i in range(n_rows)]

    # Marginal stability: no sign changes but auxiliary polynomial was used
    # (all-zero row indicates symmetric root pairs, typically on jω axis)
    has_auxiliary = any(f["type"] == "auxiliary" for f in flags)
    marginal = sign_changes == 0 and has_auxiliary

    return {
        "rows": rows_list,
        "powers": powers,
        "first_column": [float(first_col[i]) for i in range(n_rows)],
        "sign_changes": int(sign_changes),
        "rhp_poles": int(sign_changes),
        "flags": flags,
        "stable": sign_changes == 0,
        "marginal": marginal,
    }


def compute_stability_k_ranges(
    base_poly: np.ndarray,
    k_min: float = 0.0,
    k_max: float = 100.0,
    n_test: int = 500,
) -> Dict[str, Any]:
    """Sweep K and determine stability ranges using Routh criterion.

    The characteristic polynomial is formed as: base_poly + [0, ..., 0, K]
    i.e., K is added to the constant (last) coefficient.

    Args:
        base_poly: Base polynomial coefficients (high-power-first).
        k_min: Minimum K value for sweep.
        k_max: Maximum K value for sweep.
        n_test: Number of test points.

    Returns:
        Dict with ranges (list of {start, end, stable}) and critical_k_values.
    """
    k_values = np.linspace(k_min, k_max, n_test)
    stability = np.zeros(n_test, dtype=bool)
    rhp_counts = np.zeros(n_test, dtype=int)

    for i, k in enumerate(k_values):
        poly = base_poly.copy()
        poly[-1] = poly[-1] + k  # Add K to constant term
        result = compute_routh_array(poly)
        stability[i] = result["stable"]
        rhp_counts[i] = result["rhp_poles"]

    # Find transitions
    ranges = []
    critical_k_values = []
    start_idx = 0

    for i in range(1, n_test):
        if stability[i] != stability[start_idx]:
            # Transition detected — binary search for exact crossing
            k_lo, k_hi = float(k_values[i - 1]), float(k_values[i])
            for _ in range(50):  # bisection iterations
                k_mid = (k_lo + k_hi) / 2
                poly = base_poly.copy()
                poly[-1] = poly[-1] + k_mid
                mid_result = compute_routh_array(poly)
                if mid_result["stable"] == stability[start_idx]:
                    k_lo = k_mid
                else:
                    k_hi = k_mid
            critical_k = (k_lo + k_hi) / 2
            critical_k_values.append(round(critical_k, 4))

            ranges.append({
                "start": float(k_values[start_idx]),
                "end": round(critical_k, 4),
                "stable": bool(stability[start_idx]),
            })
            start_idx = i

    # Final range
    ranges.append({
        "start": float(k_values[start_idx]),
        "end": float(k_max),
        "stable": bool(stability[start_idx]),
    })

    return {
        "ranges": ranges,
        "critical_k_values": critical_k_values,
        "k_values": k_values.tolist(),
        "rhp_counts": rhp_counts.tolist(),
    }
