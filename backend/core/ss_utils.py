"""Shared state-space math utilities.

Pure functions for TF↔SS conversion, canonical forms, minimal realization,
Gramians, and transmission zeros. Used by both state_space_analyzer.py and
hub_validator.py.

References:
    - Ogata "Modern Control Engineering" 5th ed.
    - Kailath "Linear Systems"
    - Emami-Naeini & Van Dooren (1982) for transmission zeros
    - Moore (1981) for balanced truncation
"""

from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from scipy import signal
from scipy import linalg


# ---------------------------------------------------------------------------
# Improper TF handling
# ---------------------------------------------------------------------------

def tf_proper_decomposition(
    num: Union[List[float], np.ndarray],
    den: Union[List[float], np.ndarray],
) -> Tuple[np.ndarray, np.ndarray, float]:
    """Polynomial long division: G(s) = D_poly(s) + N_sp(s)/den(s).

    For proper TFs (deg(num) <= deg(den)): returns (num, den, D_scalar=0).
    For improper TFs (deg(num) > deg(den)): returns (remainder, den, D_value).

    The D_value returned is the constant term of the quotient polynomial.
    For SS conversion, only the constant (degree-0) term maps to D; higher-order
    terms in the quotient represent pure differentiators which are handled by
    the proper-part remainder.

    Uses np.polydiv for the division.

    Args:
        num: numerator coefficients, highest power first
        den: denominator coefficients, highest power first

    Returns:
        (num_proper, den, D_value) where:
        - num_proper: remainder after division (proper part numerator)
        - den: unchanged denominator
        - D_value: float scalar, the direct feedthrough

    Reference: Ogata §3-8
    """
    num = np.atleast_1d(np.asarray(num, dtype=float))
    den = np.atleast_1d(np.asarray(den, dtype=float))

    # Strip leading zeros
    while len(num) > 1 and abs(num[0]) < 1e-14:
        num = num[1:]
    while len(den) > 1 and abs(den[0]) < 1e-14:
        den = den[1:]

    if len(num) <= len(den):
        # Already proper — D is the scalar when degrees are equal
        if len(num) == len(den):
            d_val = float(num[0] / den[0])
            remainder = num - d_val * den
            # Strip leading near-zeros from remainder
            while len(remainder) > 1 and abs(remainder[0]) < 1e-12:
                remainder = remainder[1:]
            return remainder, den, d_val
        return num, den, 0.0

    # Improper: polynomial long division
    quotient, remainder = np.polydiv(num, den)

    # D is the constant (last) element of quotient
    d_val = float(quotient[-1]) if len(quotient) > 0 else 0.0

    # Strip leading near-zeros from remainder
    while len(remainder) > 1 and abs(remainder[0]) < 1e-12:
        remainder = remainder[1:]

    return remainder, den, d_val


# ---------------------------------------------------------------------------
# SISO TF → SS with canonical forms
# ---------------------------------------------------------------------------

def tf2ss_canonical(
    num: Union[List[float], np.ndarray],
    den: Union[List[float], np.ndarray],
    form: str = "controllable",
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Convert SISO TF to state-space in specified canonical form.

    Handles improper TFs by extracting D via long division first.

    Args:
        num: numerator polynomial coefficients [highest power first]
        den: denominator polynomial coefficients [highest power first]
        form: one of 'controllable', 'observable', 'modal', 'jordan'

    Returns:
        (A, B, C, D) as numpy arrays

    Forms:
        controllable: scipy.signal.tf2ss output (companion matrix in A)
        observable: transpose of controllable (A→A.T, B↔C.T)
        modal: eigendecomposition with real block diagonal for complex pairs
        jordan: real Schur decomposition (numerical Jordan)

    Reference:
        - Controllable/Observable: Ogata §3-8
        - Modal: Kailath "Linear Systems" §6.1
        - Jordan: Horn & Johnson "Matrix Analysis" §3.1
    """
    num = np.atleast_1d(np.asarray(num, dtype=float))
    den = np.atleast_1d(np.asarray(den, dtype=float))

    # Handle improper TFs
    num_proper, den, d_extra = tf_proper_decomposition(num, den)

    # Normalize denominator leading coefficient to 1
    a0 = den[0]
    if abs(a0) < 1e-14:
        raise ValueError("Leading denominator coefficient is zero")
    num_n = num_proper / a0
    den_n = den / a0

    # Base: controllable canonical form via scipy
    A_cc, B_cc, C_cc, D_cc = signal.tf2ss(num_n, den_n)

    # Add the extra D from improper decomposition
    D_cc = D_cc + d_extra

    n = A_cc.shape[0]
    if n == 0:
        # Static gain (no dynamics)
        return (
            np.zeros((0, 0)),
            np.zeros((0, 1)),
            np.zeros((1, 0)),
            np.atleast_2d(D_cc),
        )

    if form == "controllable":
        return A_cc, B_cc, C_cc, np.atleast_2d(D_cc)

    elif form == "observable":
        # Dual of controllable: A→A.T, B↔C.T
        return A_cc.T.copy(), C_cc.T.copy(), B_cc.T.copy(), np.atleast_2d(D_cc)

    elif form == "modal":
        return _to_modal_form(A_cc, B_cc, C_cc, D_cc)

    elif form == "jordan":
        return _to_jordan_form(A_cc, B_cc, C_cc, D_cc)

    else:
        raise ValueError(f"Unknown canonical form: {form!r}")


def _to_modal_form(
    A: np.ndarray, B: np.ndarray, C: np.ndarray, D: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Convert to modal (real block-diagonal) canonical form.

    For real eigenvalues: 1×1 diagonal entries.
    For complex conjugate pairs: 2×2 blocks [[σ, ω], [-ω, σ]].

    Uses eigendecomposition and constructs a real transformation.
    """
    n = A.shape[0]
    eigenvalues, V = np.linalg.eig(A)

    # Build real transformation matrix
    T = np.zeros((n, n))
    A_modal = np.zeros((n, n))
    i = 0
    processed = set()

    # Sort eigenvalues: real first, then complex pairs
    indices = list(range(n))
    real_indices = [j for j in indices if abs(eigenvalues[j].imag) < 1e-10]
    complex_indices = [j for j in indices if abs(eigenvalues[j].imag) >= 1e-10]

    col = 0
    for j in real_indices:
        T[:, col] = V[:, j].real
        A_modal[col, col] = eigenvalues[j].real
        col += 1

    j = 0
    while j < len(complex_indices):
        idx = complex_indices[j]
        sigma = eigenvalues[idx].real
        omega = abs(eigenvalues[idx].imag)
        T[:, col] = V[:, idx].real
        T[:, col + 1] = V[:, idx].imag
        A_modal[col, col] = sigma
        A_modal[col, col + 1] = omega
        A_modal[col + 1, col] = -omega
        A_modal[col + 1, col + 1] = sigma
        col += 2
        j += 2  # Skip conjugate pair

    # Apply similarity transformation
    try:
        T_inv = np.linalg.inv(T)
    except np.linalg.LinAlgError:
        # Fallback: use Schur decomposition for defective matrices
        return _to_jordan_form(A, B, C, D)

    B_modal = T_inv @ B
    C_modal = C @ T

    return A_modal, B_modal, C_modal, np.atleast_2d(D)


def _to_jordan_form(
    A: np.ndarray, B: np.ndarray, C: np.ndarray, D: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Convert to Jordan-like form via real Schur decomposition.

    Real Schur produces a quasi-upper-triangular matrix (1×1 and 2×2 blocks
    on the diagonal), which is the numerically stable version of Jordan form.
    """
    T_schur, Z = linalg.schur(A, output="real")
    B_j = Z.T @ B
    C_j = C @ Z

    return T_schur, B_j, C_j, np.atleast_2d(D)


# ---------------------------------------------------------------------------
# MIMO TF matrix → SS
# ---------------------------------------------------------------------------

def mimo_tf2ss(
    num_matrix: List[List[List[float]]],
    den_matrix: List[List[List[float]]],
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Convert p×m MIMO transfer function matrix to state-space.

    Pipeline:
    1. For each (i,j) entry: convert to SISO SS via tf2ss
    2. Block-diagonal assembly of all channel realizations
    3. Minimal realization to remove redundant states

    Args:
        num_matrix: p×m list of lists, each entry is a list of numerator coefficients
        den_matrix: p×m list of lists, each entry is a list of denominator coefficients

    Returns:
        (A, B, C, D) as numpy arrays (minimal realization)

    Reference: Kailath "Linear Systems" §6.4
    """
    p = len(num_matrix)
    m = len(num_matrix[0]) if p > 0 else 0

    if p == 0 or m == 0:
        raise ValueError("MIMO TF must have at least 1 input and 1 output")

    # Convert each channel to SISO SS
    channel_ss = []  # list of (A_ij, B_ij, C_ij, D_ij, order_ij)
    for i in range(p):
        row = []
        for j in range(m):
            num_ij = np.atleast_1d(np.asarray(num_matrix[i][j], dtype=float))
            den_ij = np.atleast_1d(np.asarray(den_matrix[i][j], dtype=float))

            # Skip zero-gain entries (no dynamics)
            if len(num_ij) == 1 and abs(num_ij[0]) < 1e-14 and len(den_ij) == 1:
                row.append(None)
                continue

            A_ij, B_ij, C_ij, D_ij = tf2ss_canonical(num_ij, den_ij, "controllable")
            n_ij = A_ij.shape[0]
            row.append((A_ij, B_ij, C_ij, float(D_ij.flat[0]) if D_ij.size else 0.0, n_ij))
        channel_ss.append(row)

    # Compute total state dimension
    total_n = sum(
        ch[4] for row in channel_ss for ch in row if ch is not None
    )

    if total_n == 0:
        # Pure static gain
        D_big = np.zeros((p, m))
        for i in range(p):
            for j in range(m):
                ch = channel_ss[i][j]
                if ch is not None:
                    D_big[i, j] = ch[3]
        return np.zeros((0, 0)), np.zeros((0, m)), np.zeros((p, 0)), D_big

    # Block-diagonal assembly
    A_big = np.zeros((total_n, total_n))
    B_big = np.zeros((total_n, m))
    C_big = np.zeros((p, total_n))
    D_big = np.zeros((p, m))

    state_offset = 0
    for i in range(p):
        for j in range(m):
            ch = channel_ss[i][j]
            if ch is None:
                continue
            A_ij, B_ij, C_ij, d_ij, n_ij = ch
            if n_ij == 0:
                D_big[i, j] = d_ij
                continue

            # Place A_ij on diagonal
            A_big[state_offset:state_offset + n_ij,
                  state_offset:state_offset + n_ij] = A_ij

            # B_big: route input j to this channel's states
            B_big[state_offset:state_offset + n_ij, j:j + 1] += B_ij

            # C_big: route this channel's states to output i
            C_big[i:i + 1, state_offset:state_offset + n_ij] += C_ij

            # D
            D_big[i, j] = d_ij

            state_offset += n_ij

    # Apply minimal realization to remove redundant states
    try:
        A_min, B_min, C_min, D_min, _ = minreal(A_big, B_big, C_big, D_big)
        return A_min, B_min, C_min, D_min
    except Exception:
        # If minreal fails, return the unreduced realization
        return A_big, B_big, C_big, D_big


# ---------------------------------------------------------------------------
# Minimal realization via balanced truncation
# ---------------------------------------------------------------------------

def minreal(
    A: np.ndarray,
    B: np.ndarray,
    C: np.ndarray,
    D: np.ndarray,
    tol: float = 1e-8,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, Dict[str, Any]]:
    """Compute minimal realization by removing uncontrollable/unobservable states.

    For stable systems: uses Gramian-based balanced truncation.
    For unstable systems: uses controllability/observability rank-based truncation.

    Args:
        A, B, C, D: state-space matrices
        tol: threshold for Hankel singular values or singular values

    Returns:
        (A_min, B_min, C_min, D_min, info) where info contains:
        - hsv: Hankel singular values (empty for unstable systems)
        - n_original: original state count
        - n_reduced: reduced state count
        - n_removed: number of removed states

    Reference:
        - Moore (1981) "Principal component analysis in linear systems"
        - Laub, Heath, Paige, Ward (1987)
    """
    A = np.atleast_2d(np.asarray(A, dtype=float))
    B = np.atleast_2d(np.asarray(B, dtype=float))
    C = np.atleast_2d(np.asarray(C, dtype=float))
    D = np.atleast_2d(np.asarray(D, dtype=float))

    n = A.shape[0]
    info: Dict[str, Any] = {
        "hsv": [],
        "n_original": n,
        "n_reduced": n,
        "n_removed": 0,
    }

    if n == 0:
        return A, B, C, D, info

    eigenvalues = np.linalg.eigvals(A)
    is_stable = bool(np.all(eigenvalues.real < -1e-10))

    if is_stable:
        # Gramian-based balanced truncation
        try:
            Wc = controllability_gramian(A, B)
            Wo = observability_gramian(A, C)

            # Hankel singular values
            WcWo = Wc @ Wo
            eigs_wc_wo = np.linalg.eigvals(WcWo)
            hsv = np.sqrt(np.maximum(eigs_wc_wo.real, 0.0))
            hsv = np.sort(hsv)[::-1]  # descending

            info["hsv"] = hsv.tolist()

            # Find states to keep
            keep_mask = hsv > tol
            n_keep = int(np.sum(keep_mask))
            if n_keep == 0:
                n_keep = 1  # Keep at least one state
            if n_keep == n:
                info["n_reduced"] = n
                return A, B, C, D, info

            # Balanced transformation via Cholesky + SVD
            L_c = np.linalg.cholesky(Wc + tol * np.eye(n))
            L_o = np.linalg.cholesky(Wo + tol * np.eye(n))

            U, S, Vt = np.linalg.svd(L_o.T @ L_c)
            S_sqrt_inv = np.diag(1.0 / np.sqrt(np.maximum(S, tol)))

            T_bal = L_c @ Vt.T @ S_sqrt_inv
            T_bal_inv = S_sqrt_inv @ U.T @ L_o.T

            A_bal = T_bal_inv @ A @ T_bal
            B_bal = T_bal_inv @ B
            C_bal = C @ T_bal

            # Truncate to n_keep states
            A_min = A_bal[:n_keep, :n_keep]
            B_min = B_bal[:n_keep, :]
            C_min = C_bal[:, :n_keep]

            info["n_reduced"] = n_keep
            info["n_removed"] = n - n_keep
            return A_min, B_min, C_min, D, info

        except Exception:
            # Fall through to rank-based method
            pass

    # Rank-based truncation for unstable or when Gramian method fails
    return _minreal_rank_based(A, B, C, D, tol, info)


def _minreal_rank_based(
    A: np.ndarray,
    B: np.ndarray,
    C: np.ndarray,
    D: np.ndarray,
    tol: float,
    info: Dict[str, Any],
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, Dict[str, Any]]:
    """Rank-based minimal realization using Kalman decomposition.

    Removes states that are not both controllable AND observable.
    Works for both stable and unstable systems.
    """
    n = A.shape[0]
    m = B.shape[1]

    # Controllability matrix rank
    ctrb_cols = [np.linalg.matrix_power(A, i) @ B for i in range(n)]
    ctrb = np.hstack(ctrb_cols) if ctrb_cols else np.zeros((n, 0))
    _, s_c, Vt_c = np.linalg.svd(ctrb, full_matrices=True)
    rank_c = int(np.sum(s_c > tol * s_c[0])) if len(s_c) > 0 else 0

    if rank_c == 0:
        info["n_reduced"] = 0
        info["n_removed"] = n
        return np.zeros((0, 0)), np.zeros((0, m)), np.zeros((C.shape[0], 0)), D, info

    # Observability matrix rank
    obsv_rows = [C @ np.linalg.matrix_power(A, i) for i in range(n)]
    obsv = np.vstack(obsv_rows)
    _, s_o, _ = np.linalg.svd(obsv, full_matrices=True)
    rank_o = int(np.sum(s_o > tol * s_o[0])) if len(s_o) > 0 else 0

    # If both fully controllable and observable, system is already minimal
    if rank_c >= n and rank_o >= n:
        return A, B, C, D, info

    # Use Schur-based approach to isolate controllable+observable subspace
    # Transform to separate controllable subspace
    U_c, _, _ = np.linalg.svd(ctrb, full_matrices=True)
    T_c = U_c[:, :rank_c]  # columns spanning controllable subspace

    # Project to controllable subspace
    T_c_pinv = np.linalg.pinv(T_c)
    A_c = T_c_pinv @ A @ T_c
    B_c = T_c_pinv @ B
    C_c = C @ T_c

    # Now check observability in the controllable subspace
    obsv_c_rows = [C_c @ np.linalg.matrix_power(A_c, i) for i in range(rank_c)]
    obsv_c = np.vstack(obsv_c_rows)
    _, s_oc, _ = np.linalg.svd(obsv_c, full_matrices=True)
    rank_co = int(np.sum(s_oc > tol * s_oc[0])) if len(s_oc) > 0 else rank_c

    if rank_co >= rank_c:
        # All controllable states are also observable
        info["n_reduced"] = rank_c
        info["n_removed"] = n - rank_c
        return A_c, B_c, C_c, D, info

    # Further reduce: isolate observable subspace within controllable
    U_oc, _, _ = np.linalg.svd(obsv_c.T, full_matrices=True)
    T_oc = U_oc[:, :rank_co]
    T_oc_pinv = np.linalg.pinv(T_oc)

    A_min = T_oc_pinv @ A_c @ T_oc
    B_min = T_oc_pinv @ B_c
    C_min = C_c @ T_oc

    info["n_reduced"] = rank_co
    info["n_removed"] = n - rank_co
    return A_min, B_min, C_min, D, info


# ---------------------------------------------------------------------------
# Gramian computation
# ---------------------------------------------------------------------------

def controllability_gramian(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    """Compute controllability Gramian: solve A·Wc + Wc·A' + B·B' = 0.

    Requires A to be stable (all eigenvalues in open LHP).
    Uses scipy.linalg.solve_continuous_lyapunov.

    Returns: Wc (n×n positive semidefinite matrix)
    Reference: Kailath §7.4
    """
    A = np.atleast_2d(np.asarray(A, dtype=float))
    B = np.atleast_2d(np.asarray(B, dtype=float))
    # solve_continuous_lyapunov solves A·X + X·A^H + Q = 0
    # We need A·Wc + Wc·A^T + B·B^T = 0 → Q = B·B^T
    Q = -B @ B.T
    return linalg.solve_continuous_lyapunov(A, Q)


def observability_gramian(A: np.ndarray, C: np.ndarray) -> np.ndarray:
    """Compute observability Gramian: solve A'·Wo + Wo·A + C'·C = 0.

    Requires A to be stable.
    Uses scipy.linalg.solve_continuous_lyapunov.

    Returns: Wo (n×n positive semidefinite matrix)
    Reference: Kailath §7.4
    """
    A = np.atleast_2d(np.asarray(A, dtype=float))
    C = np.atleast_2d(np.asarray(C, dtype=float))
    Q = -C.T @ C
    return linalg.solve_continuous_lyapunov(A.T, Q)


# ---------------------------------------------------------------------------
# Transmission zeros
# ---------------------------------------------------------------------------

def transmission_zeros(
    A: np.ndarray,
    B: np.ndarray,
    C: np.ndarray,
    D: np.ndarray,
) -> np.ndarray:
    """Compute transmission zeros via the Rosenbrock system matrix method.

    Transmission zeros are values of s where the system matrix
    P(s) = [[sI-A, -B], [C, D]] drops rank.

    Computed as finite generalized eigenvalues of:
        M1 = [[A, B], [C, D]]  vs  M2 = [[I, 0], [0, 0]]

    Args:
        A (n×n), B (n×m), C (p×n), D (p×m)

    Returns:
        1D complex array of transmission zeros

    Reference:
        - Emami-Naeini & Van Dooren (1982) Automatica 18(4)
        - Laub & Moore (1978)
    """
    A = np.atleast_2d(np.asarray(A, dtype=float))
    B = np.atleast_2d(np.asarray(B, dtype=float))
    C = np.atleast_2d(np.asarray(C, dtype=float))
    D = np.atleast_2d(np.asarray(D, dtype=float))

    n = A.shape[0]
    m = B.shape[1]
    p = C.shape[0]

    if n == 0:
        return np.array([], dtype=complex)

    # Build system matrix pencil: M1 - λ·M2
    M1 = np.block([
        [A, B],
        [C, D],
    ])
    M2 = np.block([
        [np.eye(n), np.zeros((n, m))],
        [np.zeros((p, n)), np.zeros((p, m))],
    ])

    try:
        # Generalized eigenvalue problem
        gen_eigs = linalg.eigvals(M1, M2)

        # Filter: keep only finite eigenvalues (|λ| < large threshold)
        finite_mask = np.isfinite(gen_eigs) & (np.abs(gen_eigs) < 1e12)
        zeros = gen_eigs[finite_mask]

        # Sort by magnitude
        zeros = zeros[np.argsort(np.abs(zeros))]
        return zeros

    except Exception:
        return np.array([], dtype=complex)


# ---------------------------------------------------------------------------
# SS → TF conversion (SISO and MIMO)
# ---------------------------------------------------------------------------

def ss2tf_mimo(
    A: np.ndarray,
    B: np.ndarray,
    C: np.ndarray,
    D: np.ndarray,
) -> Tuple[List[List[np.ndarray]], List[List[np.ndarray]]]:
    """Convert state-space to MIMO transfer function matrix.

    For SISO (m=1, p=1): uses scipy.signal.ss2tf directly.
    For MIMO: computes each G_ij(s) channel individually.

    Returns:
        (num_matrix, den_matrix) where each is a p×m nested list of 1D arrays

    Reference: Ogata §12-3
    """
    A = np.atleast_2d(np.asarray(A, dtype=float))
    B = np.atleast_2d(np.asarray(B, dtype=float))
    C = np.atleast_2d(np.asarray(C, dtype=float))
    D = np.atleast_2d(np.asarray(D, dtype=float))

    n = A.shape[0]
    m = B.shape[1]
    p = C.shape[0]

    num_matrix: List[List[np.ndarray]] = []
    den_matrix: List[List[np.ndarray]] = []

    for i in range(p):
        num_row: List[np.ndarray] = []
        den_row: List[np.ndarray] = []
        for j in range(m):
            if n == 0:
                # Static gain only
                num_row.append(np.array([float(D[i, j])]))
                den_row.append(np.array([1.0]))
            else:
                try:
                    num_ij, den_ij = signal.ss2tf(
                        A, B[:, j:j + 1], C[i:i + 1, :], D[i:i + 1, j:j + 1],
                    )
                    num_row.append(np.atleast_1d(num_ij.flatten()))
                    den_row.append(np.atleast_1d(den_ij.flatten()))
                except Exception:
                    num_row.append(np.array([float(D[i, j])]))
                    den_row.append(np.array([1.0]))
        num_matrix.append(num_row)
        den_matrix.append(den_row)

    return num_matrix, den_matrix


# ---------------------------------------------------------------------------
# Canonical form conversion
# ---------------------------------------------------------------------------

def convert_canonical(
    A: np.ndarray,
    B: np.ndarray,
    C: np.ndarray,
    D: np.ndarray,
    to_form: str,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Convert between canonical forms via similarity transformation.

    Computes T such that A_new = T⁻¹·A·T, B_new = T⁻¹·B, C_new = C·T.

    Args:
        A, B, C, D: current state-space matrices
        to_form: target form ('controllable', 'observable', 'modal', 'jordan')

    Returns:
        (A_new, B_new, C_new, D_new, T) where T is the transformation matrix
    """
    A = np.atleast_2d(np.asarray(A, dtype=float))
    B = np.atleast_2d(np.asarray(B, dtype=float))
    C = np.atleast_2d(np.asarray(C, dtype=float))
    D = np.atleast_2d(np.asarray(D, dtype=float))

    n = A.shape[0]
    if n == 0:
        return A, B, C, D, np.eye(0)

    if to_form == "modal":
        A_new, B_new, C_new, D_new = _to_modal_form(A, B, C, D)
        # Recover T from modal transformation
        try:
            # T is the eigenvector matrix (or the real version of it)
            eigenvalues, V = np.linalg.eig(A)
            # Build real T (same logic as _to_modal_form)
            T = np.zeros((n, n))
            real_idx = [j for j in range(n) if abs(eigenvalues[j].imag) < 1e-10]
            complex_idx = [j for j in range(n) if abs(eigenvalues[j].imag) >= 1e-10]
            col = 0
            for j in real_idx:
                T[:, col] = V[:, j].real
                col += 1
            k = 0
            while k < len(complex_idx):
                idx = complex_idx[k]
                T[:, col] = V[:, idx].real
                T[:, col + 1] = V[:, idx].imag
                col += 2
                k += 2
        except Exception:
            T = np.eye(n)
        return A_new, B_new, C_new, D_new, T

    elif to_form == "jordan":
        T_schur, Z = linalg.schur(A, output="real")
        B_new = Z.T @ B
        C_new = C @ Z
        return T_schur, B_new, C_new, D, Z

    elif to_form == "controllable":
        # Controllability matrix
        ctrb_cols = [np.linalg.matrix_power(A, i) @ B for i in range(n)]
        Mc = np.hstack(ctrb_cols)
        try:
            T = np.linalg.inv(Mc[:, :n]) if Mc.shape[1] >= n else np.eye(n)
        except np.linalg.LinAlgError:
            T = np.eye(n)
        T_inv = np.linalg.pinv(T)
        return T_inv @ A @ T, T_inv @ B, C @ T, D, T

    elif to_form == "observable":
        # Observability matrix
        obsv_rows = [C @ np.linalg.matrix_power(A, i) for i in range(n)]
        Mo = np.vstack(obsv_rows)
        try:
            T_inv = Mo[:n, :] if Mo.shape[0] >= n else np.eye(n)
            T = np.linalg.inv(T_inv)
        except np.linalg.LinAlgError:
            T = np.eye(n)
            T_inv = np.eye(n)
        return T_inv @ A @ T, T_inv @ B, C @ T, D, T

    else:
        raise ValueError(f"Unknown target form: {to_form!r}")
