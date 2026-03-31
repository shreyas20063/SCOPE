"""Hub data validator and enrichment module.

Stateless math module that validates and enriches data pushed to the
shared system hub. Handles transfer function and state-space representations,
derives cross-representations, and computes system properties (poles, zeros,
stability, controllability, observability).
"""

from typing import Any, Dict, List, Optional, Union

import numpy as np
from scipy.signal import ss2tf, tf2ss

from core.ss_utils import (
    transmission_zeros as compute_transmission_zeros,
    ss2tf_mimo,
    controllability_gramian,
    observability_gramian,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_float_list(arr: Any) -> List[float]:
    """Convert array-like to a plain Python list of floats.

    Args:
        arr: NumPy array or nested list.

    Returns:
        List of Python floats (or nested list for 2-D).
    """
    arr = np.asarray(arr, dtype=float)
    if arr.ndim == 1:
        return [float(v) for v in arr]
    return [[float(v) for v in row] for row in arr]


def _complex_to_dict(c: complex) -> Dict[str, float]:
    """Convert a complex number to {real, imag} dict.

    Args:
        c: Complex number.

    Returns:
        Dict with 'real' and 'imag' keys.
    """
    return {"real": float(c.real), "imag": float(c.imag)}


def _count_origin_poles_ct(poles: np.ndarray) -> int:
    """Count poles at the origin for a continuous-time system.

    A pole is considered at the origin if |pole| < 1e-6.

    Args:
        poles: 1-D array of pole locations (complex).

    Returns:
        Number of poles at s = 0.
    """
    return int(np.sum(np.abs(poles) < 1e-6))


def _count_unity_poles_dt(poles: np.ndarray) -> int:
    """Count poles at z = 1 for a discrete-time system.

    A pole is considered at z = 1 if |pole - 1| < 1e-6.

    Args:
        poles: 1-D array of pole locations (complex).

    Returns:
        Number of poles at z = 1.
    """
    return int(np.sum(np.abs(poles - 1.0) < 1e-6))


def _check_stability(poles: np.ndarray, domain: str) -> bool:
    """Check if a system is stable given its poles and domain.

    Args:
        poles: 1-D array of pole locations (complex).
        domain: 'ct' for continuous-time or 'dt' for discrete-time.

    Returns:
        True if the system is stable.
    """
    if len(poles) == 0:
        return True
    if domain == "dt":
        return bool(np.all(np.abs(poles) < 1.0 - 1e-10))
    # CT: all poles must have strictly negative real part.
    return bool(np.all(np.real(poles) < -1e-10))


def _controllability_rank(A: np.ndarray, B: np.ndarray) -> int:
    """Compute the rank of the controllability matrix [B, AB, ..., A^{n-1}B].

    Args:
        A: n x n state matrix.
        B: n x m input matrix.

    Returns:
        Rank of the controllability matrix.
    """
    A = np.atleast_2d(np.asarray(A, dtype=float))
    B = np.atleast_2d(np.asarray(B, dtype=float))
    n = A.shape[0]
    cols = [B]
    Ab = B.copy()
    for _ in range(n - 1):
        Ab = A @ Ab
        cols.append(Ab)
    ctrb = np.hstack(cols)
    return int(np.linalg.matrix_rank(ctrb))


def _observability_rank(A: np.ndarray, C: np.ndarray) -> int:
    """Compute the rank of the observability matrix [C; CA; ...; CA^{n-1}].

    Args:
        A: n x n state matrix.
        C: p x n output matrix.

    Returns:
        Rank of the observability matrix.
    """
    A = np.atleast_2d(np.asarray(A, dtype=float))
    C = np.atleast_2d(np.asarray(C, dtype=float))
    n = A.shape[0]
    rows = [C]
    Ca = C.copy()
    for _ in range(n - 1):
        Ca = Ca @ A
        rows.append(Ca)
    obsv = np.vstack(rows)
    return int(np.linalg.matrix_rank(obsv))


# ---------------------------------------------------------------------------
# Control slot validator
# ---------------------------------------------------------------------------

def validate_and_enrich_control(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and enrich a control system hub slot.

    Accepts a raw data dict with either transfer function or state-space
    representation (or a block_diagram pass-through) and derives all
    missing representations plus system properties.

    Args:
        data: Dict with at least a 'source' key ('tf', 'ss', or
              'block_diagram'). For 'tf': must include 'num' and 'den'
              lists. For 'ss': must include 'A', 'B', 'C', 'D' matrices.
              Optional 'domain' key ('ct' or 'dt'), defaults to 'ct'.

    Returns:
        Dict with 'success' (bool), 'data' (enriched dict if success),
        and 'error' (str if not success).
    """
    if not isinstance(data, dict):
        return {"success": False, "error": "Data must be a dict"}

    source = data.get("source")
    if source not in ("tf", "ss", "block_diagram"):
        return {"success": False, "error": f"Invalid source: {source!r}. Must be 'tf', 'ss', or 'block_diagram'"}

    domain = data.get("domain", "ct")
    if domain not in ("ct", "dt"):
        return {"success": False, "error": f"Invalid domain: {domain!r}. Must be 'ct' or 'dt'"}

    # Block diagram: enrich based on available TF data.
    if source == "block_diagram":
        try:
            tm = data.get("transfer_matrix")
            if tm and isinstance(tm.get("entries"), list) and len(tm["entries"]) > 0:
                return _enrich_from_transfer_matrix(data, domain)
            # SISO block diagram with flat tf — enrich as TF, preserve source.
            if data.get("tf") or data.get("num"):
                result = _enrich_from_tf(data, domain)
                if result.get("success") and result.get("data"):
                    result["data"]["source"] = "block_diagram"
                    if data.get("block_diagram"):
                        result["data"]["block_diagram"] = data["block_diagram"]
                return result
        except Exception as exc:
            return {"success": False, "error": str(exc)}
        # No TF computed yet — pass-through.
        return {"success": True, "data": {**data, "domain": domain}}

    try:
        if source == "tf":
            return _enrich_from_tf(data, domain)
        else:
            return _enrich_from_ss(data, domain)
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def _enrich_from_transfer_matrix(data: Dict[str, Any], domain: str) -> Dict[str, Any]:
    """Enrich a hub slot from a MIMO transfer function matrix.

    Computes poles, zeros, stability, and order for each G_ij entry.
    Aggregates system-level properties across the full matrix.
    For 1x1, also spreads flat tf/poles/zeros for backward compatibility.

    Args:
        data: Dict with 'transfer_matrix' containing 'entries' (p x m list
              of dicts with 'numerator'/'denominator' coefficient lists),
              'input_labels', 'output_labels', 'variable'.
        domain: 'ct' or 'dt'.

    Returns:
        Enrichment result dict with 'success' and 'data'/'error'.
    """
    tm = data["transfer_matrix"]
    raw_entries = tm["entries"]
    variable = tm.get("variable", "s")
    input_labels = tm.get("input_labels", [])
    output_labels = tm.get("output_labels", [])

    p = len(raw_entries)
    if p == 0:
        return {"success": False, "error": "Transfer matrix has no rows"}
    m = len(raw_entries[0])
    if m == 0:
        return {"success": False, "error": "Transfer matrix has no columns"}

    enriched_entries: List[List[Dict[str, Any]]] = []
    all_poles: List[complex] = []
    all_stable = True
    max_order = 0

    for i in range(p):
        row: List[Dict[str, Any]] = []
        for j in range(m):
            entry = raw_entries[i][j]
            raw_num = entry.get("numerator", [0.0])
            raw_den = entry.get("denominator", [1.0])

            num = np.asarray(raw_num, dtype=float).ravel()
            den = np.asarray(raw_den, dtype=float).ravel()

            # Sanitize
            if np.any(np.isnan(num)) or np.any(np.isinf(num)):
                num = np.array([0.0])
            if np.any(np.isnan(den)) or np.any(np.isinf(den)):
                den = np.array([1.0])

            den_t = np.trim_zeros(den, "f")
            if len(den_t) == 0:
                den_t = np.array([1.0])
            num_t = np.trim_zeros(num, "f")
            if len(num_t) == 0:
                num_t = np.array([0.0])

            poles = np.roots(den_t) if len(den_t) > 1 else np.array([])
            zeros = np.roots(num_t) if len(num_t) > 1 else np.array([])

            entry_stable = _check_stability(poles, domain)
            entry_order = len(poles)

            all_poles.extend(poles.tolist())
            if not entry_stable:
                all_stable = False
            max_order = max(max_order, entry_order)

            row.append({
                "num": _to_float_list(num_t),
                "den": _to_float_list(den_t),
                "poles": [_complex_to_dict(pp) for pp in poles],
                "zeros": [_complex_to_dict(zz) for zz in zeros],
                "stable": entry_stable,
                "order": entry_order,
            })
        enriched_entries.append(row)

    # System type from combined poles.
    combined = np.array(all_poles) if all_poles else np.array([])
    if domain == "dt":
        sys_type = _count_unity_poles_dt(combined)
    else:
        sys_type = _count_origin_poles_ct(combined)

    all_poles_display = [_complex_to_dict(complex(pp)) for pp in all_poles]

    enriched: Dict[str, Any] = {
        "source": "block_diagram",
        "domain": domain,
        "dimensions": {"n": max_order, "m": m, "p": p},
        "transfer_matrix": {
            "entries": enriched_entries,
            "input_labels": input_labels,
            "output_labels": output_labels,
            "variable": variable,
        },
        "poles": all_poles_display,
        "zeros": [],
        "stable": all_stable,
        "system_type": sys_type,
        "order": max_order,
    }

    if data.get("block_diagram"):
        enriched["block_diagram"] = data["block_diagram"]

    # 1x1 backward compat: spread flat tf/poles/zeros.
    if m == 1 and p == 1:
        e = enriched_entries[0][0]
        enriched["tf"] = {
            "num": e["num"],
            "den": e["den"],
            "variable": variable,
        }
        enriched["zeros"] = e["zeros"]

    return {"success": True, "data": enriched}


def _enrich_from_tf(data: Dict[str, Any], domain: str) -> Dict[str, Any]:
    """Enrich a hub slot from transfer function data.

    Args:
        data: Dict with 'num' and 'den' coefficient lists (high-power first).
        domain: 'ct' or 'dt'.

    Returns:
        Enrichment result dict with 'success' and 'data'/'error'.
    """
    # Accept both flat (num/den at top level) and nested (tf.num/tf.den) formats.
    # base_simulator.to_hub_data() produces the nested format.
    tf_block = data.get("tf", {})
    raw_num = data.get("num") if data.get("num") is not None else tf_block.get("num")
    raw_den = data.get("den") if data.get("den") is not None else tf_block.get("den")

    if raw_num is None or raw_den is None:
        return {"success": False, "error": "TF source requires 'num' and 'den' keys"}

    num = np.asarray(raw_num, dtype=float).ravel()
    den = np.asarray(raw_den, dtype=float).ravel()

    if len(den) == 0:
        return {"success": False, "error": "Denominator must not be empty"}
    if len(num) == 0:
        return {"success": False, "error": "Numerator must not be empty"}
    if len(den) > 100 or len(num) > 100:
        return {"success": False, "error": "Polynomial order too high (>100)"}
    if np.any(np.isnan(num)) or np.any(np.isinf(num)):
        return {"success": False, "error": "Numerator contains NaN or Inf"}
    if np.any(np.isnan(den)) or np.any(np.isinf(den)):
        return {"success": False, "error": "Denominator contains NaN or Inf"}

    # Strip leading zeros (BUG-002 prevention).
    den_trimmed = np.trim_zeros(den, "f")
    if len(den_trimmed) == 0:
        return {"success": False, "error": "Denominator is all zeros"}
    num_trimmed = np.trim_zeros(num, "f")
    if len(num_trimmed) == 0:
        num_trimmed = np.array([0.0])

    # Poles and zeros.
    poles = np.roots(den_trimmed) if len(den_trimmed) > 1 else np.array([])
    zeros = np.roots(num_trimmed) if len(num_trimmed) > 1 else np.array([])

    order = len(poles)

    # System type.
    if domain == "dt":
        system_type = _count_unity_poles_dt(poles)
    else:
        system_type = _count_origin_poles_ct(poles)

    stable = _check_stability(poles, domain)
    variable = "z" if domain == "dt" else "s"

    # Derive state-space (SISO only).
    ss_data: Optional[Dict[str, Any]] = None
    controllable: Optional[bool] = None
    observable: Optional[bool] = None

    if order > 0:
        A, B, C, D = tf2ss(num_trimmed, den_trimmed)
        ss_data = {
            "A": _to_float_list(A),
            "B": _to_float_list(B),
            "C": _to_float_list(C),
            "D": _to_float_list(D),
        }
        n = A.shape[0]
        controllable = _controllability_rank(A, B) == n
        observable = _observability_rank(A, C) == n

    enriched = {
        "source": "tf",
        "domain": domain,
        "dimensions": {"n": order, "m": 1, "p": 1},
        "tf": {
            "num": _to_float_list(num_trimmed),
            "den": _to_float_list(den_trimmed),
            "variable": variable,
        },
        "poles": [_complex_to_dict(p) for p in poles],
        "zeros": [_complex_to_dict(z) for z in zeros],
        "system_type": system_type,
        "order": order,
        "stable": stable,
    }

    if ss_data is not None:
        enriched["ss"] = ss_data
    if controllable is not None:
        enriched["controllable"] = controllable
    if observable is not None:
        enriched["observable"] = observable

    # Transmission zeros and Gramians (when SS is available)
    if order > 0 and ss_data is not None:
        try:
            t_zeros = compute_transmission_zeros(A, B, C, D)
            if len(t_zeros) > 0:
                enriched["transmission_zeros"] = [_complex_to_dict(z) for z in t_zeros]
        except Exception:
            pass

        # Gramians for stable systems
        if stable:
            try:
                Wc = controllability_gramian(A, B)
                Wo = observability_gramian(A, C)
                WcWo = Wc @ Wo
                eigs = np.linalg.eigvals(WcWo)
                hsv = np.sqrt(np.maximum(eigs.real, 0.0))
                enriched["hankel_singular_values"] = sorted(
                    [float(v) for v in hsv], reverse=True
                )
            except Exception:
                pass

    return {"success": True, "data": enriched}


def _enrich_from_ss(data: Dict[str, Any], domain: str) -> Dict[str, Any]:
    """Enrich a hub slot from state-space data.

    Args:
        data: Dict with 'A', 'B', 'C', 'D' matrix keys.
        domain: 'ct' or 'dt'.

    Returns:
        Enrichment result dict with 'success' and 'data'/'error'.
    """
    # Accept both flat (A/B/C/D at top level) and nested (ss.A/ss.B/ss.C/ss.D) formats.
    ss_block = data.get("ss", {})
    mat_src = {}
    for key in ("A", "B", "C", "D"):
        mat_src[key] = data.get(key) if data.get(key) is not None else ss_block.get(key)
        if mat_src[key] is None:
            return {"success": False, "error": f"SS source requires '{key}' matrix"}

    A = np.atleast_2d(np.asarray(mat_src["A"], dtype=float))
    B = np.atleast_2d(np.asarray(mat_src["B"], dtype=float))
    C = np.atleast_2d(np.asarray(mat_src["C"], dtype=float))
    D = np.atleast_2d(np.asarray(mat_src["D"], dtype=float))

    # Guard against NaN/Inf and excessively large matrices.
    for mat, name in [(A, "A"), (B, "B"), (C, "C"), (D, "D")]:
        if np.any(np.isnan(mat)) or np.any(np.isinf(mat)):
            return {"success": False, "error": f"Matrix {name} contains NaN or Inf"}
    if A.shape[0] > 100:
        return {"success": False, "error": f"System order {A.shape[0]} too large (max 100)"}

    # Validate dimensions.
    if A.ndim != 2 or A.shape[0] != A.shape[1]:
        return {"success": False, "error": f"A must be square, got shape {A.shape}"}

    n = A.shape[0]

    if B.ndim != 2 or B.shape[0] != n:
        return {"success": False, "error": f"B must have {n} rows, got shape {B.shape}"}
    m = B.shape[1]

    if C.ndim != 2 or C.shape[1] != n:
        return {"success": False, "error": f"C must have {n} columns, got shape {C.shape}"}
    p = C.shape[0]

    if D.ndim != 2 or D.shape[0] != p or D.shape[1] != m:
        return {"success": False, "error": f"D must be {p}x{m}, got shape {D.shape}"}

    is_siso = m == 1 and p == 1

    # Poles from eigenvalues of A.
    poles = np.linalg.eigvals(A)

    order = n

    if domain == "dt":
        system_type = _count_unity_poles_dt(poles)
    else:
        system_type = _count_origin_poles_ct(poles)

    stable = _check_stability(poles, domain)

    controllable = _controllability_rank(A, B) == n
    observable = _observability_rank(A, C) == n

    enriched: Dict[str, Any] = {
        "source": "ss",
        "domain": domain,
        "dimensions": {"n": n, "m": m, "p": p},
        "ss": {
            "A": _to_float_list(A),
            "B": _to_float_list(B),
            "C": _to_float_list(C),
            "D": _to_float_list(D),
        },
        "poles": [_complex_to_dict(p) for p in poles],
        "zeros": [],
        "system_type": system_type,
        "order": order,
        "stable": stable,
        "controllable": controllable,
        "observable": observable,
    }

    # Derive TF
    variable = "z" if domain == "dt" else "s"
    if is_siso:
        num, den = ss2tf(A, B, C, D)
        num = num.ravel()
        den = den.ravel()
        num_trimmed = np.trim_zeros(num, "f")
        if len(num_trimmed) == 0:
            num_trimmed = np.array([0.0])
        den_trimmed = np.trim_zeros(den, "f")
        if len(den_trimmed) == 0:
            den_trimmed = np.array([1.0])

        zeros = np.roots(num_trimmed) if len(num_trimmed) > 1 else np.array([])
        enriched["tf"] = {
            "num": _to_float_list(num_trimmed),
            "den": _to_float_list(den_trimmed),
            "variable": variable,
        }
        enriched["zeros"] = [_complex_to_dict(z) for z in zeros]
    else:
        # MIMO: derive per-channel TF matrix
        try:
            num_matrix, den_matrix = ss2tf_mimo(A, B, C, D)
            tf_entries = []
            for i in range(p):
                row = []
                for j in range(m):
                    row.append({
                        "num": _to_float_list(num_matrix[i][j]),
                        "den": _to_float_list(den_matrix[i][j]),
                    })
                tf_entries.append(row)
            enriched["tf_matrix"] = {"entries": tf_entries, "variable": variable}
        except Exception:
            pass

    # Transmission zeros
    if n > 0:
        try:
            t_zeros = compute_transmission_zeros(A, B, C, D)
            if len(t_zeros) > 0:
                enriched["transmission_zeros"] = [_complex_to_dict(z) for z in t_zeros]
        except Exception:
            pass

    # Gramians for stable systems
    if stable and n > 0:
        try:
            Wc = controllability_gramian(A, B)
            Wo = observability_gramian(A, C)
            WcWo = Wc @ Wo
            eigs = np.linalg.eigvals(WcWo)
            hsv = np.sqrt(np.maximum(eigs.real, 0.0))
            enriched["hankel_singular_values"] = sorted(
                [float(v) for v in hsv], reverse=True
            )
        except Exception:
            pass

    return {"success": True, "data": enriched}
