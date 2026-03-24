"""Hub data validator and enrichment module.

Stateless math module that validates and enriches data pushed to the
shared system hub. Handles transfer function and state-space representations,
derives cross-representations, and computes system properties (poles, zeros,
stability, controllability, observability).
"""

from typing import Any, Dict, List, Optional, Union

import numpy as np
from scipy.signal import ss2tf, tf2ss


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

    # Block diagram pass-through: no math to do.
    if source == "block_diagram":
        return {"success": True, "data": {**data, "domain": domain}}

    try:
        if source == "tf":
            return _enrich_from_tf(data, domain)
        else:
            return _enrich_from_ss(data, domain)
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def _enrich_from_tf(data: Dict[str, Any], domain: str) -> Dict[str, Any]:
    """Enrich a hub slot from transfer function data.

    Args:
        data: Dict with 'num' and 'den' coefficient lists (high-power first).
        domain: 'ct' or 'dt'.

    Returns:
        Enrichment result dict with 'success' and 'data'/'error'.
    """
    raw_num = data.get("num")
    raw_den = data.get("den")

    if raw_num is None or raw_den is None:
        return {"success": False, "error": "TF source requires 'num' and 'den' keys"}

    num = np.asarray(raw_num, dtype=float).ravel()
    den = np.asarray(raw_den, dtype=float).ravel()

    if len(den) == 0:
        return {"success": False, "error": "Denominator must not be empty"}
    if len(num) == 0:
        return {"success": False, "error": "Numerator must not be empty"}

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

    return {"success": True, "data": enriched}


def _enrich_from_ss(data: Dict[str, Any], domain: str) -> Dict[str, Any]:
    """Enrich a hub slot from state-space data.

    Args:
        data: Dict with 'A', 'B', 'C', 'D' matrix keys.
        domain: 'ct' or 'dt'.

    Returns:
        Enrichment result dict with 'success' and 'data'/'error'.
    """
    for key in ("A", "B", "C", "D"):
        if key not in data:
            return {"success": False, "error": f"SS source requires '{key}' matrix"}

    A = np.atleast_2d(np.asarray(data["A"], dtype=float))
    B = np.atleast_2d(np.asarray(data["B"], dtype=float))
    C = np.atleast_2d(np.asarray(data["C"], dtype=float))
    D = np.atleast_2d(np.asarray(data["D"], dtype=float))

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

    # Derive TF for SISO systems only.
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

        variable = "z" if domain == "dt" else "s"
        zeros = np.roots(num_trimmed) if len(num_trimmed) > 1 else np.array([])
        enriched["tf"] = {
            "num": _to_float_list(num_trimmed),
            "den": _to_float_list(den_trimmed),
            "variable": variable,
        }
        enriched["zeros"] = [_complex_to_dict(z) for z in zeros]

    return {"success": True, "data": enriched}


# ---------------------------------------------------------------------------
# Signal slot validator
# ---------------------------------------------------------------------------

def validate_signal_slot(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate a signal hub slot.

    Expected schema: {signals: {name: {x, y, type, label}}, sample_rate, duration}.
    Lightweight validation — just checks top-level types.

    Args:
        data: Signal slot data dict.

    Returns:
        Dict with 'success', 'data', and optionally 'error'.
    """
    if not isinstance(data, dict):
        return {"success": False, "error": "Data must be a dict"}

    signals = data.get("signals", {})
    if not isinstance(signals, dict):
        return {"success": False, "error": "'signals' must be a dict"}

    return {"success": True, "data": data}


# ---------------------------------------------------------------------------
# Circuit slot validator
# ---------------------------------------------------------------------------

def validate_circuit_slot(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate a circuit hub slot.

    Expected schema: {components: {R: 1000, C: 1e-6}, topology: "rc_lowpass", tf: {...}}.
    Lightweight validation — just checks top-level types.

    Args:
        data: Circuit slot data dict.

    Returns:
        Dict with 'success', 'data', and optionally 'error'.
    """
    if not isinstance(data, dict):
        return {"success": False, "error": "Data must be a dict"}

    components = data.get("components", {})
    if not isinstance(components, dict):
        return {"success": False, "error": "'components' must be a dict"}

    return {"success": True, "data": data}


# ---------------------------------------------------------------------------
# Optics slot validator
# ---------------------------------------------------------------------------

def validate_optics_slot(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate an optics hub slot.

    Expected schema: {elements: [{type, f, position}, ...], wavelength: 550}.
    Lightweight validation — just checks top-level types.

    Args:
        data: Optics slot data dict.

    Returns:
        Dict with 'success', 'data', and optionally 'error'.
    """
    if not isinstance(data, dict):
        return {"success": False, "error": "Data must be a dict"}

    elements = data.get("elements", [])
    if not isinstance(elements, list):
        return {"success": False, "error": "'elements' must be a list"}

    return {"success": True, "data": data}
