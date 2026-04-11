"""Jacobian linearization utilities for nonlinear systems.

Provides symbolic Jacobian computation at equilibrium points, with
optional SymPy dependency (graceful degradation when unavailable).

Used by: nonlinear_control_lab.py, potentially other nonlinear sims.
"""

import numpy as np
from typing import Any, Dict, List, Optional, Tuple

# Optional SymPy — must work without it
try:
    import sympy as sp
    _HAS_SYMPY = True
except ImportError:
    _HAS_SYMPY = False


def has_sympy() -> bool:
    """Check whether SymPy is available."""
    return _HAS_SYMPY


def compute_jacobian(f_vector: 'sp.Matrix',
                     x_syms: List,
                     u_syms: List,
                     x_eq: List[float],
                     u_eq: List[float]
                     ) -> Tuple[np.ndarray, np.ndarray]:
    """Compute A = df/dx and B = df/du evaluated at equilibrium.

    Args:
        f_vector: SymPy Matrix of state equations f(x, u).
        x_syms: SymPy state variable symbols.
        u_syms: SymPy input variable symbols.
        x_eq: Equilibrium state values.
        u_eq: Equilibrium input values.

    Returns:
        (A, B) as numpy arrays, where A is n x n and B is n x m.

    Raises:
        RuntimeError: If SymPy is not installed.
        ValueError: If Jacobian contains inf/nan at the equilibrium.
    """
    if not _HAS_SYMPY:
        raise RuntimeError("SymPy is required for Jacobian computation")

    # Symbolic Jacobians
    A_sym = f_vector.jacobian(sp.Matrix(x_syms))
    B_sym = f_vector.jacobian(sp.Matrix(u_syms))

    # Substitution dict
    subs: Dict[Any, float] = {}
    for i, s in enumerate(x_syms):
        subs[s] = x_eq[i]
    for i, s in enumerate(u_syms):
        subs[s] = u_eq[i]

    # Evaluate numerically
    A_num = np.array(A_sym.subs(subs).tolist(), dtype=float)
    B_num = np.array(B_sym.subs(subs).tolist(), dtype=float)

    if not np.all(np.isfinite(A_num)) or not np.all(np.isfinite(B_num)):
        raise ValueError("Jacobian contains inf/nan — equilibrium may be at a singularity")

    return A_num, B_num


def check_controllability(A: np.ndarray, B: np.ndarray) -> Tuple[bool, int]:
    """Check controllability via rank of [B, AB, A^2 B, ..., A^(n-1) B].

    Args:
        A: n x n system matrix.
        B: n x m input matrix.

    Returns:
        (is_controllable, rank) tuple.
    """
    n = A.shape[0]
    if B.ndim == 1:
        B = B.reshape(-1, 1)
    ctrb_matrix = B.copy()
    AiB = B.copy()
    for i in range(1, n):
        AiB = A @ AiB
        ctrb_matrix = np.hstack([ctrb_matrix, AiB])

    rank = np.linalg.matrix_rank(ctrb_matrix)
    return bool(rank == n), int(rank)


def find_equilibria(f_vector: 'sp.Matrix',
                    x_syms: List,
                    u_syms: List,
                    u_eq: Optional[List[float]] = None
                    ) -> List[Dict[str, List[float]]]:
    """Find equilibrium points by solving f(x, u) = 0.

    Args:
        f_vector: SymPy Matrix of state equations.
        x_syms: SymPy state variable symbols.
        u_syms: SymPy input variable symbols.
        u_eq: Fixed input values. If None, inputs are treated as free.

    Returns:
        List of dicts with 'x_eq' and 'u_eq' keys (as float lists).
        May be empty if no real solutions are found.

    Raises:
        RuntimeError: If SymPy is not installed.
    """
    if not _HAS_SYMPY:
        raise RuntimeError("SymPy is required for equilibrium finding")

    # Substitute fixed inputs if provided
    f_sub = f_vector
    if u_eq is not None:
        subs = {u_syms[i]: u_eq[i] for i in range(len(u_syms))}
        f_sub = f_vector.subs(subs)
        solve_vars = list(x_syms)
    else:
        solve_vars = list(x_syms) + list(u_syms)

    try:
        solutions = sp.solve(f_sub, solve_vars, dict=True)
    except Exception:
        return []

    results = []
    for sol in solutions:
        # Check all values are real
        try:
            x_vals = [float(complex(sol.get(s, 0)).real) for s in x_syms]
            if u_eq is not None:
                u_vals = list(u_eq)
            else:
                u_vals = [float(complex(sol.get(s, 0)).real) for s in u_syms]
            # Skip solutions with large imaginary parts
            x_imag = [abs(complex(sol.get(s, 0)).imag) for s in x_syms]
            if max(x_imag) < 1e-10:
                results.append({"x_eq": x_vals, "u_eq": u_vals})
        except (TypeError, ValueError):
            continue

    return results
