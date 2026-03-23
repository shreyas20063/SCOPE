"""Pure MIMO math utilities for state-space control systems.

Provides standalone functions for controllability, observability, step/impulse
responses, LQR, LQG, and pole placement. No dependency on the simulations
package — uses only NumPy and SciPy.
"""

from typing import Dict, List, Optional, Tuple, Union

import numpy as np
from scipy.integrate import solve_ivp
from scipy.linalg import solve_continuous_are
from scipy.signal import place_poles


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def validate_dimensions(
    A: np.ndarray,
    B: np.ndarray,
    C: np.ndarray,
    D: np.ndarray,
) -> Optional[str]:
    """Validate state-space matrix dimensions (A, B, C, D).

    Checks that A is n x n, B is n x m, C is p x n, D is p x m.

    Args:
        A: State matrix.
        B: Input matrix.
        C: Output matrix.
        D: Feedthrough matrix.

    Returns:
        None if all dimensions are consistent, otherwise an error string
        describing the first mismatch found.
    """
    A = np.atleast_2d(A)
    B = np.atleast_2d(B)
    C = np.atleast_2d(C)
    D = np.atleast_2d(D)

    if A.ndim != 2 or A.shape[0] != A.shape[1]:
        return f"A must be square, got shape {A.shape}"

    n = A.shape[0]

    if B.ndim != 2 or B.shape[0] != n:
        return f"B must have {n} rows (matching A), got shape {B.shape}"

    m = B.shape[1]

    if C.ndim != 2 or C.shape[1] != n:
        return f"C must have {n} columns (matching A), got shape {C.shape}"

    p = C.shape[0]

    if D.ndim != 2 or D.shape[0] != p or D.shape[1] != m:
        return (
            f"D must be {p} x {m} (matching C rows, B cols), got shape {D.shape}"
        )

    return None


def validate_conjugate_pairs(poles: np.ndarray) -> Optional[str]:
    """Validate that complex poles come in conjugate pairs.

    Args:
        poles: 1-D array of desired pole locations (real or complex).

    Returns:
        None if valid (all complex poles have their conjugate present),
        otherwise an error string listing the unpaired poles.
    """
    poles = np.asarray(poles, dtype=complex).ravel()
    tol = 1e-8
    unpaired: List[complex] = []
    used = np.zeros(len(poles), dtype=bool)

    for i, p in enumerate(poles):
        if used[i]:
            continue
        if abs(p.imag) < tol:
            # Real pole — no conjugate needed.
            used[i] = True
            continue
        # Look for a conjugate partner.
        conj = p.conjugate()
        found = False
        for j in range(i + 1, len(poles)):
            if used[j]:
                continue
            if abs(poles[j] - conj) < tol:
                used[i] = True
                used[j] = True
                found = True
                break
        if not found:
            unpaired.append(p)

    if unpaired:
        pairs_str = ", ".join(f"{z}" for z in unpaired)
        return f"Complex poles missing conjugate pairs: {pairs_str}"
    return None


# ---------------------------------------------------------------------------
# Controllability & Observability
# ---------------------------------------------------------------------------

def controllability_matrix(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    """Compute the controllability matrix [B, AB, A^2 B, ..., A^{n-1} B].

    Args:
        A: n x n state matrix.
        B: n x m input matrix.

    Returns:
        n x (n * m) controllability matrix.
    """
    A = np.atleast_2d(np.asarray(A, dtype=float))
    B = np.atleast_2d(np.asarray(B, dtype=float))
    n = A.shape[0]
    cols = [B]
    Ab = B.copy()
    for _ in range(n - 1):
        Ab = A @ Ab
        cols.append(Ab)
    return np.hstack(cols)


def observability_matrix(A: np.ndarray, C: np.ndarray) -> np.ndarray:
    """Compute the observability matrix [C; CA; CA^2; ...; CA^{n-1}].

    Args:
        A: n x n state matrix.
        C: p x n output matrix.

    Returns:
        (n * p) x n observability matrix.
    """
    A = np.atleast_2d(np.asarray(A, dtype=float))
    C = np.atleast_2d(np.asarray(C, dtype=float))
    n = A.shape[0]
    rows = [C]
    Ca = C.copy()
    for _ in range(n - 1):
        Ca = Ca @ A
        rows.append(Ca)
    return np.vstack(rows)


# ---------------------------------------------------------------------------
# Time-domain responses
# ---------------------------------------------------------------------------

def mimo_step_response(
    A: np.ndarray,
    B: np.ndarray,
    C: np.ndarray,
    D: np.ndarray,
    t_eval: np.ndarray,
    input_channel: Optional[int] = None,
) -> Dict:
    """Compute the unit step response for a MIMO state-space system.

    Uses solve_ivp (RK45) with zero initial state and unit step input on
    each (or a single) input channel.

    Args:
        A: n x n state matrix.
        B: n x m input matrix.
        C: p x n output matrix.
        D: p x m feedthrough matrix.
        t_eval: 1-D array of time evaluation points (must be sorted).
        input_channel: If given, only simulate this input channel (0-indexed).
                       If None, simulate all m channels.

    Returns:
        Dict with keys:
            "t": 1-D time array,
            "responses": dict mapping (input_idx, output_idx) to 1-D y array,
            "n_inputs": number of inputs simulated,
            "n_outputs": number of outputs.
    """
    A = np.atleast_2d(np.asarray(A, dtype=float))
    B = np.atleast_2d(np.asarray(B, dtype=float))
    C = np.atleast_2d(np.asarray(C, dtype=float))
    D = np.atleast_2d(np.asarray(D, dtype=float))
    t_eval = np.asarray(t_eval, dtype=float).ravel()

    n = A.shape[0]
    m = B.shape[1]
    p = C.shape[0]

    channels = [input_channel] if input_channel is not None else list(range(m))
    responses: Dict[Tuple[int, int], np.ndarray] = {}

    for j in channels:
        bj = B[:, j]  # n-vector: column j of B
        dj = D[:, j]  # p-vector: column j of D

        def rhs(_t: float, x: np.ndarray, _bj: np.ndarray = bj) -> np.ndarray:
            return A @ x + _bj  # unit step: u(t) = 1

        sol = solve_ivp(
            rhs,
            t_span=(t_eval[0], t_eval[-1]),
            y0=np.zeros(n),
            t_eval=t_eval,
            method="RK45",
            rtol=1e-8,
            atol=1e-10,
        )

        # y(t) = C x(t) + D u(t);  u(t) = 1 for step
        y_all = C @ sol.y + dj[:, np.newaxis]  # p x len(t)

        for i in range(p):
            responses[(j, i)] = y_all[i]

    return {
        "t": t_eval,
        "responses": responses,
        "n_inputs": len(channels),
        "n_outputs": p,
    }


def mimo_impulse_response(
    A: np.ndarray,
    B: np.ndarray,
    C: np.ndarray,
    D: np.ndarray,
    t_eval: np.ndarray,
    input_channel: Optional[int] = None,
) -> Dict:
    """Compute the impulse response for a MIMO state-space system.

    Models the impulse as an initial condition x(0) = B[:, j] for each
    input channel j, with u(t) = 0 thereafter.

    Note: The D-matrix contribution to an ideal impulse (a Dirac delta at t=0)
    is infinite and not included in the continuous-time output. The returned
    response reflects only the state evolution y(t) = C * exp(At) * B[:, j].

    Args:
        A: n x n state matrix.
        B: n x m input matrix.
        C: p x n output matrix.
        D: p x m feedthrough matrix.
        t_eval: 1-D array of time evaluation points (must be sorted).
        input_channel: If given, only simulate this input channel (0-indexed).
                       If None, simulate all m channels.

    Returns:
        Dict with keys:
            "t": 1-D time array,
            "responses": dict mapping (input_idx, output_idx) to 1-D y array,
            "n_inputs": number of inputs simulated,
            "n_outputs": number of outputs.
    """
    A = np.atleast_2d(np.asarray(A, dtype=float))
    B = np.atleast_2d(np.asarray(B, dtype=float))
    C = np.atleast_2d(np.asarray(C, dtype=float))
    D = np.atleast_2d(np.asarray(D, dtype=float))
    t_eval = np.asarray(t_eval, dtype=float).ravel()

    n = A.shape[0]
    m = B.shape[1]
    p = C.shape[0]

    channels = [input_channel] if input_channel is not None else list(range(m))
    responses: Dict[Tuple[int, int], np.ndarray] = {}

    def rhs(_t: float, x: np.ndarray) -> np.ndarray:
        return A @ x  # zero input after impulse

    for j in channels:
        x0 = B[:, j].copy()

        sol = solve_ivp(
            rhs,
            t_span=(t_eval[0], t_eval[-1]),
            y0=x0,
            t_eval=t_eval,
            method="RK45",
            rtol=1e-8,
            atol=1e-10,
        )

        # y(t) = C x(t);  no D term for continuous impulse (u=0 for t > 0)
        y_all = C @ sol.y  # p x len(t)

        for i in range(p):
            responses[(j, i)] = y_all[i]

    return {
        "t": t_eval,
        "responses": responses,
        "n_inputs": len(channels),
        "n_outputs": p,
    }


# ---------------------------------------------------------------------------
# Controller design
# ---------------------------------------------------------------------------

def mimo_lqr(
    A: np.ndarray,
    B: np.ndarray,
    Q: np.ndarray,
    R: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute the continuous-time LQR optimal gain.

    Solves the continuous algebraic Riccati equation (CARE):
        A'P + PA - PBR^{-1}B'P + Q = 0
    and returns K = R^{-1} B' P.

    Args:
        A: n x n state matrix.
        B: n x m input matrix.
        Q: n x n state weighting matrix (positive semi-definite).
        R: m x m input weighting matrix (positive definite).

    Returns:
        Tuple of (K, P, cl_eigs) where
            K: m x n optimal gain matrix,
            P: n x n solution to the CARE,
            cl_eigs: 1-D array of closed-loop eigenvalues of (A - BK).
    """
    A = np.atleast_2d(np.asarray(A, dtype=float))
    B = np.atleast_2d(np.asarray(B, dtype=float))
    Q = np.atleast_2d(np.asarray(Q, dtype=float))
    R = np.atleast_2d(np.asarray(R, dtype=float))

    P = solve_continuous_are(A, B, Q, R)
    K = np.linalg.solve(R, B.T @ P)
    cl_eigs = np.linalg.eigvals(A - B @ K)

    return K, P, cl_eigs


def mimo_lqg(
    A: np.ndarray,
    B: np.ndarray,
    C: np.ndarray,
    Q: np.ndarray,
    R: np.ndarray,
    Qw: np.ndarray,
    Rv: np.ndarray,
) -> Dict:
    """Compute the continuous-time LQG controller (LQR + Kalman filter).

    Solves the dual Riccati equations:
        - CARE for regulator:  A'P + PA - PBR^{-1}B'P + Q = 0  =>  K = R^{-1}B'P
        - CARE for estimator:  AP_k + P_k A' - P_k C' Rv^{-1} C P_k + Qw = 0  =>  L = P_k C' Rv^{-1}

    The augmented closed-loop system is:
        A_cl = [[A, -BK], [LC, A - BK - LC]]

    Args:
        A: n x n state matrix.
        B: n x m input matrix.
        C: p x n output matrix.
        Q: n x n state weighting (LQR cost).
        R: m x m input weighting (LQR cost).
        Qw: n x n process noise covariance.
        Rv: p x p measurement noise covariance.

    Returns:
        Dict with keys:
            "K": m x n regulator gain,
            "L": n x p Kalman (observer) gain,
            "P_lqr": n x n CARE solution for regulator,
            "P_kal": n x n CARE solution for estimator,
            "cl_eigs": 1-D array of augmented CL eigenvalues (2n),
            "K_eigs": 1-D array of regulator CL eigenvalues (A - BK),
            "L_eigs": 1-D array of estimator eigenvalues (A - LC),
            "A_cl": 2n x 2n augmented CL state matrix.
    """
    A = np.atleast_2d(np.asarray(A, dtype=float))
    B = np.atleast_2d(np.asarray(B, dtype=float))
    C = np.atleast_2d(np.asarray(C, dtype=float))
    Q = np.atleast_2d(np.asarray(Q, dtype=float))
    R = np.atleast_2d(np.asarray(R, dtype=float))
    Qw = np.atleast_2d(np.asarray(Qw, dtype=float))
    Rv = np.atleast_2d(np.asarray(Rv, dtype=float))

    n = A.shape[0]

    # --- Regulator (LQR) ---
    P_lqr = solve_continuous_are(A, B, Q, R)
    K = np.linalg.solve(R, B.T @ P_lqr)

    # --- Estimator (Kalman filter) ---
    # Dual CARE:  A P_k + P_k A' - P_k C' Rv^{-1} C P_k + Qw = 0
    # This is equivalent to solve_continuous_are(A', C', Qw, Rv)
    P_kal = solve_continuous_are(A.T, C.T, Qw, Rv)
    L = np.linalg.solve(Rv, C @ P_kal).T  # n x p

    # --- Augmented closed-loop ---
    # State: [x; x_hat], dynamics:
    #   dx     = A x  - B K x_hat
    #   dx_hat = L C x + (A - B K - L C) x_hat
    A_cl = np.block([
        [A, -B @ K],
        [L @ C, A - B @ K - L @ C],
    ])

    cl_eigs = np.linalg.eigvals(A_cl)
    K_eigs = np.linalg.eigvals(A - B @ K)
    L_eigs = np.linalg.eigvals(A - L @ C)

    return {
        "K": K,
        "L": L,
        "P_lqr": P_lqr,
        "P_kal": P_kal,
        "cl_eigs": cl_eigs,
        "K_eigs": K_eigs,
        "L_eigs": L_eigs,
        "A_cl": A_cl,
    }


def mimo_pole_placement(
    A: np.ndarray,
    B: np.ndarray,
    desired_poles: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    """Compute a state feedback gain K that places closed-loop poles.

    Uses scipy.signal.place_poles (which handles MIMO via the Kautsky-Nichols-
    van Dooren algorithm).

    Args:
        A: n x n state matrix.
        B: n x m input matrix.
        desired_poles: 1-D array of n desired closed-loop pole locations.

    Returns:
        Tuple of (K, cl_eigs) where
            K: m x n gain matrix such that eig(A - BK) ≈ desired_poles,
            cl_eigs: 1-D array of achieved closed-loop eigenvalues.
    """
    A = np.atleast_2d(np.asarray(A, dtype=float))
    B = np.atleast_2d(np.asarray(B, dtype=float))
    desired_poles = np.asarray(desired_poles, dtype=complex).ravel()

    result = place_poles(A, B, desired_poles)
    K = result.gain_matrix
    cl_eigs = np.linalg.eigvals(A - B @ K)

    return K, cl_eigs
