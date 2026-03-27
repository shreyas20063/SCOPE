"""Shared controller math for 3D Physics Lab simulations.

Pure functions for PID, LQR, Pole Placement, and LQG controller design
and closed-loop simulation. All simulation uses solve_ivp with RK45 on
the full nonlinear ODE — linearization is only used to compute gains.

Used by: inverted_pendulum_3d, ball_beam_3d, coupled_tanks_3d,
         furuta_pendulum (retrofit), mass_spring_system (retrofit).
"""

from typing import Callable, Dict, List, Optional, Tuple, Union

import numpy as np
from scipy import optimize, signal
from scipy.integrate import solve_ivp
from scipy.linalg import expm, solve_continuous_are
from scipy.signal import place_poles as scipy_place_poles

_trapz = np.trapezoid if hasattr(np, 'trapezoid') else np.trapz


# ------------------------------------------------------------------ #
#  Linearization helpers                                              #
# ------------------------------------------------------------------ #

def numerical_jacobian(
    f: Callable[[np.ndarray, np.ndarray], np.ndarray],
    x_eq: np.ndarray,
    u_eq: np.ndarray,
    eps: float = 1e-6,
) -> Tuple[np.ndarray, np.ndarray]:
    """Compute A = ∂f/∂x and B = ∂f/∂u via central finite differences.

    Args:
        f: Dynamics function f(x, u) -> dx/dt.
        x_eq: Equilibrium state vector.
        u_eq: Equilibrium input vector.
        eps: Perturbation size.

    Returns:
        (A, B) matrices at the equilibrium.
    """
    n = len(x_eq)
    m = len(u_eq)
    x0 = np.array(x_eq, dtype=float)
    u0 = np.array(u_eq, dtype=float)

    A = np.zeros((n, n))
    for j in range(n):
        xp = x0.copy(); xp[j] += eps
        xm = x0.copy(); xm[j] -= eps
        A[:, j] = (f(xp, u0) - f(xm, u0)) / (2 * eps)

    B = np.zeros((n, m))
    for j in range(m):
        up = u0.copy(); up[j] += eps
        um = u0.copy(); um[j] -= eps
        B[:, j] = (f(x0, up) - f(x0, um)) / (2 * eps)

    return A, B


def controllability_matrix(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    """Compute controllability matrix [B, AB, A²B, ..., A^(n-1)B]."""
    n = A.shape[0]
    cols = [B]
    for i in range(1, n):
        cols.append(A @ cols[-1])
    return np.hstack(cols)


def observability_matrix(A: np.ndarray, C: np.ndarray) -> np.ndarray:
    """Compute observability matrix [C; CA; CA²; ...; CA^(n-1)]."""
    n = A.shape[0]
    rows = [C]
    for i in range(1, n):
        rows.append(rows[-1] @ A)
    return np.vstack(rows)


# ------------------------------------------------------------------ #
#  Controller gain computation                                        #
# ------------------------------------------------------------------ #

def compute_lqr(
    A: np.ndarray,
    B: np.ndarray,
    Q: np.ndarray,
    R: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute LQR optimal gain via continuous algebraic Riccati equation.

    Minimizes J = ∫(x'Qx + u'Ru)dt.

    Args:
        A: State matrix (n×n).
        B: Input matrix (n×m).
        Q: State cost matrix (n×n), positive semi-definite.
        R: Input cost matrix (m×m), positive definite.

    Returns:
        (K, P, cl_eigs) where K is the gain matrix, P is the Riccati solution,
        and cl_eigs are the closed-loop eigenvalues.
    """
    A = np.atleast_2d(A)
    B = np.atleast_2d(B)
    Q = np.atleast_2d(Q)
    R = np.atleast_2d(R)

    P = solve_continuous_are(A, B, Q, R)
    K = np.linalg.solve(R, B.T @ P)
    cl_eigs = np.linalg.eigvals(A - B @ K)
    return K, P, cl_eigs


def compute_pole_placement(
    A: np.ndarray,
    B: np.ndarray,
    desired_poles: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    """Compute state feedback gain K to place closed-loop poles.

    Args:
        A: State matrix (n×n).
        B: Input matrix (n×m).
        desired_poles: Array of n desired closed-loop eigenvalues.

    Returns:
        (K, cl_eigs) where K is the gain matrix and cl_eigs are the
        achieved closed-loop eigenvalues.
    """
    A = np.atleast_2d(A)
    B = np.atleast_2d(B)
    desired_poles = np.array(desired_poles)

    result = scipy_place_poles(A, B, desired_poles)
    K = result.gain_matrix
    cl_eigs = np.linalg.eigvals(A - B @ K)
    return K, cl_eigs


def compute_lqg(
    A: np.ndarray,
    B: np.ndarray,
    C: np.ndarray,
    Q_lqr: np.ndarray,
    R_lqr: np.ndarray,
    Q_kalman: np.ndarray,
    R_kalman: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Compute LQG controller (LQR gain + Kalman observer gain).

    Separation principle: design K from (A, B, Q, R) and L from (A, C, Qn, Rn)
    independently.

    Note: The estimator CARE formulation used here
    (solve_continuous_are(A.T, C.T, Q, R)) is only correct when C is symmetric
    (typically C = I, full-state output). For general non-symmetric C, the
    transpose structure in the CARE would need adjustment.

    Args:
        A: State matrix (n×n).
        B: Input matrix (n×m).
        C: Output matrix (p×n). Must be symmetric (e.g., identity matrix).
        Q_lqr: LQR state cost (n×n).
        R_lqr: LQR input cost (m×m).
        Q_kalman: Process noise covariance (n×n).
        R_kalman: Measurement noise covariance (p×p).

    Returns:
        (K, L, P_ctrl, P_est) — controller gain, observer gain,
        control Riccati solution, estimator Riccati solution.

    Raises:
        ValueError: If C is not symmetric (not supported by this formulation).
    """
    if not np.allclose(C, C.T):
        raise ValueError(
            "compute_lqg only supports symmetric C matrices (typically C=I). "
            "For general C, the estimator CARE formulation must be adjusted."
        )

    K, P_ctrl, _ = compute_lqr(A, B, Q_lqr, R_lqr)

    # Dual problem: estimator Riccati
    # solve_continuous_are(A', C', Q, R) solves: A·P + P·A' − P·C·R⁻¹·C'·P + Q = 0
    # This equals the standard estimator CARE only when C = C' (symmetric).
    P_est = solve_continuous_are(A.T, C.T, Q_kalman, R_kalman)
    L = P_est @ C.T @ np.linalg.inv(R_kalman)

    return K, L, P_ctrl, P_est


def compute_pid_gains(
    Kp: float,
    Ki: float,
    Kd: float,
    N: float = 100.0,
) -> Dict[str, float]:
    """Package PID gains with derivative filter coefficient.

    PID with filtered derivative:
        u(t) = Kp·e + Ki·∫e dt + Kd·(N·e − N·e_filtered)

    Args:
        Kp: Proportional gain.
        Ki: Integral gain.
        Kd: Derivative gain.
        N: Derivative filter coefficient (higher = less filtering).

    Returns:
        Dict with keys: Kp, Ki, Kd, N.
    """
    return {"Kp": Kp, "Ki": Ki, "Kd": Kd, "N": N}


# ------------------------------------------------------------------ #
#  Closed-loop simulation (all use full nonlinear ODE)                #
# ------------------------------------------------------------------ #

def simulate_uncontrolled(
    f: Callable[[np.ndarray, np.ndarray], np.ndarray],
    x0: np.ndarray,
    t_span: Tuple[float, float],
    n_inputs: int,
    dt: float = 0.01,
) -> Dict[str, np.ndarray]:
    """Simulate the uncontrolled plant (u = 0).

    Args:
        f: Dynamics function f(x, u) -> dx/dt.
        x0: Initial state.
        t_span: (t_start, t_end).
        n_inputs: Number of input channels.
        dt: Output sample period.

    Returns:
        Dict with keys: t, x, u.
    """
    t_eval = np.arange(t_span[0], t_span[1], dt)
    u_zero = np.zeros(n_inputs)

    def rhs(t, x):
        return f(np.array(x), u_zero)

    sol = solve_ivp(rhs, t_span, x0, method='RK45',
                    t_eval=t_eval, max_step=dt, rtol=1e-8, atol=1e-10)

    n_pts = len(sol.t)
    return {
        "t": sol.t,
        "x": sol.y.T,  # (n_pts, n_states)
        "u": np.zeros((n_pts, n_inputs)),
    }


def simulate_pid(
    f: Callable[[np.ndarray, np.ndarray], np.ndarray],
    x0: np.ndarray,
    t_span: Tuple[float, float],
    gains: Dict[str, float],
    output_index: int,
    x_ref: float,
    n_inputs: int,
    input_index: int = 0,
    u_max: float = 100.0,
    dt: float = 0.01,
) -> Dict[str, np.ndarray]:
    """Simulate PID control on the nonlinear plant.

    The PID acts on a single output state (output_index) tracking x_ref,
    producing a single control input (input_index).

    Args:
        f: Dynamics function f(x, u) -> dx/dt.
        x0: Initial state.
        t_span: (t_start, t_end).
        gains: Dict with Kp, Ki, Kd, N keys.
        output_index: State index to control.
        x_ref: Reference value for the controlled state.
        n_inputs: Total number of inputs.
        input_index: Which input the PID drives.
        u_max: Control effort saturation limit.
        dt: Output sample period.

    Returns:
        Dict with keys: t, x, u.
    """
    Kp = gains["Kp"]
    Ki = gains["Ki"]
    Kd = gains["Kd"]
    N = gains["N"]

    # Augment state with [integral_error, filtered_derivative]
    n_states = len(x0)
    x0_aug = np.zeros(n_states + 2)
    x0_aug[:n_states] = x0

    t_eval = np.arange(t_span[0], t_span[1], dt)
    u_log = []

    def rhs(t, x_aug):
        x = x_aug[:n_states]
        int_err = x_aug[n_states]
        d_filt = x_aug[n_states + 1]

        e = x_ref - x[output_index]

        # PID output: Kd term uses filtered derivative N*(e - d_filt) = ḋ_filt
        # d_filt tracks e via first-order filter, so N*(e - d_filt) ≈ de/dt
        u_pid = Kp * e + Ki * int_err + Kd * N * (e - d_filt)
        u_pid = np.clip(u_pid, -u_max, u_max)

        u = np.zeros(n_inputs)
        u[input_index] = u_pid

        dx = f(x, u)
        dx_aug = np.zeros(n_states + 2)
        dx_aug[:n_states] = dx
        dx_aug[n_states] = e  # d(int_err)/dt = e
        dx_aug[n_states + 1] = N * (e - d_filt)  # filtered derivative

        return dx_aug

    sol = solve_ivp(rhs, t_span, x0_aug, method='RK45',
                    t_eval=t_eval, max_step=dt, rtol=1e-8, atol=1e-10)

    # Reconstruct control signal
    x_traj = sol.y[:n_states, :].T
    int_err_traj = sol.y[n_states, :]
    d_filt_traj = sol.y[n_states + 1, :]

    u_traj = np.zeros((len(sol.t), n_inputs))
    for i in range(len(sol.t)):
        e = x_ref - x_traj[i, output_index]
        u_pid = Kp * e + Ki * int_err_traj[i] + Kd * N * (e - d_filt_traj[i])
        u_pid = np.clip(u_pid, -u_max, u_max)
        u_traj[i, input_index] = u_pid

    return {
        "t": sol.t,
        "x": x_traj,
        "u": u_traj,
    }


def simulate_state_feedback(
    f: Callable[[np.ndarray, np.ndarray], np.ndarray],
    x0: np.ndarray,
    t_span: Tuple[float, float],
    K: np.ndarray,
    x_eq: np.ndarray,
    u_eq: np.ndarray,
    u_max: float = 100.0,
    dt: float = 0.01,
) -> Dict[str, np.ndarray]:
    """Simulate full-state feedback u = u_eq − K(x − x_eq) on the nonlinear plant.

    Args:
        f: Dynamics function f(x, u) -> dx/dt.
        x0: Initial state.
        t_span: (t_start, t_end).
        K: State feedback gain matrix (m×n).
        x_eq: Equilibrium state.
        u_eq: Equilibrium input.
        u_max: Per-channel control saturation.
        dt: Output sample period.

    Returns:
        Dict with keys: t, x, u.
    """
    K = np.atleast_2d(K)
    x_eq = np.array(x_eq, dtype=float)
    u_eq = np.array(u_eq, dtype=float)
    t_eval = np.arange(t_span[0], t_span[1], dt)

    def rhs(t, x):
        dx = np.array(x) - x_eq
        u = u_eq - K @ dx
        u = np.clip(u.flatten(), -u_max, u_max)
        return f(np.array(x), u)

    sol = solve_ivp(rhs, t_span, x0, method='RK45',
                    t_eval=t_eval, max_step=dt, rtol=1e-8, atol=1e-10)

    # Reconstruct u
    x_traj = sol.y.T
    n_inputs = K.shape[0]
    u_traj = np.zeros((len(sol.t), n_inputs))
    for i in range(len(sol.t)):
        dx = x_traj[i] - x_eq
        u = u_eq - K @ dx
        u_traj[i] = np.clip(u.flatten(), -u_max, u_max)

    return {
        "t": sol.t,
        "x": x_traj,
        "u": u_traj,
    }


def simulate_lqg(
    f: Callable[[np.ndarray, np.ndarray], np.ndarray],
    x0: np.ndarray,
    t_span: Tuple[float, float],
    K: np.ndarray,
    L: np.ndarray,
    A: np.ndarray,
    B: np.ndarray,
    C: np.ndarray,
    x_eq: np.ndarray,
    u_eq: np.ndarray,
    u_max: float = 100.0,
    dt: float = 0.01,
) -> Dict[str, np.ndarray]:
    """Simulate LQG (state feedback + Kalman observer) on the nonlinear plant.

    The true plant evolves with nonlinear f(x,u). The observer runs the
    linearized model: x̂̇ = A(x̂−x_eq) + B(u−u_eq) + L(y − C(x̂−x_eq)).
    Control law: u = u_eq − K(x̂ − x_eq).

    Args:
        f: Nonlinear dynamics f(x, u) -> dx/dt.
        x0: Initial true state.
        t_span: (t_start, t_end).
        K: State feedback gain (m×n).
        L: Observer gain (n×p).
        A, B, C: Linearized state-space matrices.
        x_eq: Equilibrium state.
        u_eq: Equilibrium input.
        u_max: Per-channel saturation.
        dt: Output sample period.

    Returns:
        Dict with keys: t, x, x_hat, u.
    """
    K = np.atleast_2d(K)
    L = np.atleast_2d(L)
    A = np.atleast_2d(A)
    B = np.atleast_2d(B)
    C = np.atleast_2d(C)
    x_eq = np.array(x_eq, dtype=float)
    u_eq = np.array(u_eq, dtype=float)
    n = len(x_eq)
    t_eval = np.arange(t_span[0], t_span[1], dt)

    # Augmented state: [x_true (n), x_hat (n)]
    x0_aug = np.zeros(2 * n)
    x0_aug[:n] = x0
    x0_aug[n:] = x_eq  # observer starts at equilibrium

    def rhs(t, z):
        x_true = z[:n]
        x_hat = z[n:]

        dx_hat = x_hat - x_eq
        u = u_eq - K @ dx_hat
        u = np.clip(u.flatten(), -u_max, u_max)

        # True plant (nonlinear)
        dx_true = f(x_true, u)

        # Observer (linearized)
        y = C @ (x_true - x_eq)  # measurement
        y_hat = C @ dx_hat
        innovation = y.flatten() - y_hat.flatten()

        dx_hat_dot = A @ dx_hat + B @ (u - u_eq) + L @ innovation

        dz = np.zeros(2 * n)
        dz[:n] = dx_true
        dz[n:] = dx_hat_dot
        return dz

    sol = solve_ivp(rhs, t_span, x0_aug, method='RK45',
                    t_eval=t_eval, max_step=dt, rtol=1e-8, atol=1e-10)

    x_traj = sol.y[:n, :].T
    x_hat_traj = sol.y[n:, :].T

    # Reconstruct u
    n_inputs = K.shape[0]
    u_traj = np.zeros((len(sol.t), n_inputs))
    for i in range(len(sol.t)):
        dx_hat = x_hat_traj[i] - x_eq
        u = u_eq - K @ dx_hat
        u_traj[i] = np.clip(u.flatten(), -u_max, u_max)

    return {
        "t": sol.t,
        "x": x_traj,
        "x_hat": x_hat_traj,
        "u": u_traj,
    }


# ------------------------------------------------------------------ #
#  Analysis helpers                                                    #
# ------------------------------------------------------------------ #

def compute_performance_metrics(
    t: np.ndarray,
    x: np.ndarray,
    state_index: int,
    x_ref: float,
    settling_threshold: float = 0.02,
) -> Dict[str, float]:
    """Compute time-domain performance metrics for a single state.

    Args:
        t: Time array.
        x: State trajectory (n_pts, n_states).
        state_index: Which state to analyze.
        x_ref: Reference/target value.
        settling_threshold: Fraction of |x_ref| for settling criterion.

    Returns:
        Dict with rise_time, settling_time, overshoot, steady_state_error, ise.
    """
    y = x[:, state_index]
    e = x_ref - y
    y0 = y[0]
    dy = x_ref - y0  # total change expected

    metrics: Dict[str, float] = {}

    # Rise time (10% to 90% of final value)
    if abs(dy) > 1e-10:
        y10 = y0 + 0.1 * dy
        y90 = y0 + 0.9 * dy
        t10 = None
        t90 = None
        for i in range(len(t)):
            if t10 is None and ((dy > 0 and y[i] >= y10) or (dy < 0 and y[i] <= y10)):
                t10 = t[i]
            if t90 is None and ((dy > 0 and y[i] >= y90) or (dy < 0 and y[i] <= y90)):
                t90 = t[i]
        if t10 is not None and t90 is not None:
            metrics["rise_time"] = t90 - t10
        else:
            metrics["rise_time"] = float('inf')
    else:
        metrics["rise_time"] = 0.0

    # Overshoot
    if abs(dy) > 1e-10:
        if dy > 0:
            peak = np.max(y)
            metrics["overshoot"] = max(0, (peak - x_ref) / abs(dy) * 100)
        else:
            peak = np.min(y)
            metrics["overshoot"] = max(0, (x_ref - peak) / abs(dy) * 100)
    else:
        metrics["overshoot"] = 0.0

    # Settling time
    band = settling_threshold * max(abs(x_ref), abs(dy), 0.01)
    settled = np.abs(y - x_ref) <= band
    metrics["settling_time"] = float('inf')
    if np.any(settled):
        # Find last time it leaves the band
        for i in range(len(t) - 1, -1, -1):
            if not settled[i]:
                if i < len(t) - 1:
                    metrics["settling_time"] = t[i + 1]
                break
        else:
            metrics["settling_time"] = t[0]

    # Steady-state error (average of last 10%)
    tail = max(1, len(t) // 10)
    metrics["steady_state_error"] = float(np.mean(np.abs(e[-tail:])))

    # ISE
    dt_arr = np.diff(t)
    metrics["ise"] = float(np.sum(e[:-1]**2 * dt_arr))

    return metrics


def compute_energy(u: np.ndarray, t: np.ndarray) -> float:
    """Compute total control energy ∫|u|² dt."""
    dt_arr = np.diff(t)
    return float(np.sum(np.sum(u[:-1]**2, axis=1) * dt_arr))


# ------------------------------------------------------------------ #
#  State-space to Transfer Function conversion                        #
# ------------------------------------------------------------------ #

def ss2tf_siso(
    A: np.ndarray,
    B: np.ndarray,
    output_index: int = 0,
    input_index: int = 0,
) -> Tuple[np.ndarray, np.ndarray]:
    """Convert state-space (A, B) to SISO transfer function (num, den).

    Constructs C to select the output_index-th state, D = 0.

    Args:
        A: State matrix (n×n).
        B: Input matrix (n×m).
        output_index: Which state is the measured output.
        input_index: Which input channel to use.

    Returns:
        (num, den) polynomial coefficient arrays (highest power first).
    """
    A = np.atleast_2d(A)
    B = np.atleast_2d(B)
    n = A.shape[0]
    m = B.shape[1]
    C = np.zeros((1, n))
    C[0, output_index] = 1.0
    D = np.zeros((1, m))

    num, den = signal.ss2tf(A, B, C, D, input=input_index)
    # ss2tf returns num as 2D array for MIMO; squeeze for SISO
    num = np.squeeze(num)
    # Remove leading near-zero coefficients
    while len(num) > 1 and abs(num[0]) < 1e-12:
        num = num[1:]
    return num, den


# ------------------------------------------------------------------ #
#  Auto-tune helpers                                                   #
# ------------------------------------------------------------------ #

def _cl_max_real(
    plant_num: np.ndarray,
    plant_den: np.ndarray,
    K_test: float,
) -> float:
    """Return max real part of CL poles for proportional gain K_test."""
    padded = np.pad(plant_num, (len(plant_den) - len(plant_num), 0))
    cl_char = np.polyadd(plant_den, K_test * padded)
    poles = np.roots(cl_char)
    if len(poles) == 0:
        return 0.0
    return float(np.max(poles.real))


def _refine_boundary(
    plant_num: np.ndarray,
    plant_den: np.ndarray,
    K_lo: float,
    K_hi: float,
    iterations: int = 50,
) -> Tuple[float, Optional[float]]:
    """Binary-search to refine the gain where CL poles cross jω axis.

    Returns (K_boundary, Pu) where Pu is the ultimate period at that gain.
    """
    padded = np.pad(plant_num, (len(plant_den) - len(plant_num), 0))
    for _ in range(iterations):
        K_mid = (K_lo + K_hi) / 2
        cl_mid = np.polyadd(plant_den, K_mid * padded)
        poles_mid = np.roots(cl_mid)
        if len(poles_mid) == 0:
            break
        if np.max(poles_mid.real) >= 0:
            K_hi = K_mid
        else:
            K_lo = K_mid

    Ku = (K_lo + K_hi) / 2
    cl_u = np.polyadd(plant_den, Ku * padded)
    poles_u = np.roots(cl_u)
    thresh = 0.1 * max(abs(Ku), 1)
    near_imag = np.abs(poles_u.imag[np.abs(poles_u.real) < thresh])
    Pu = None
    if len(near_imag) > 0:
        omega_u = float(np.max(near_imag))
        if omega_u > 0:
            Pu = 2 * np.pi / omega_u
    return Ku, Pu


def _find_stability_boundaries(
    plant_num: np.ndarray,
    plant_den: np.ndarray,
) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """Find the proportional gain range [K_min, K_max] where CL is stable.

    For stable plants: K_min=0, K_max=Ku.
    For unstable plants: K_min>0 (minimum stabilizing gain), K_max=Ku.

    Returns (K_min, K_max, Pu) — any can be None if not found.
    Also tries negative gains for plants with negative DC gain.
    """
    # Sweep both positive and negative gains
    pos_gains = np.logspace(-2, 4, 800)
    neg_gains = -pos_gains[::-1]
    all_gains = np.concatenate([neg_gains, pos_gains])

    transitions = []  # (K_boundary_lo, K_boundary_hi, direction)
    prev_max_real = None
    prev_K = None

    for K_test in all_gains:
        max_real = _cl_max_real(plant_num, plant_den, K_test)
        if prev_max_real is not None:
            if prev_max_real >= 0 and max_real < 0:
                # unstable → stable transition
                transitions.append((prev_K, K_test, "stabilizing"))
            elif prev_max_real < 0 and max_real >= 0:
                # stable → unstable transition
                transitions.append((prev_K, K_test, "destabilizing"))
        prev_max_real = max_real
        prev_K = K_test

    if not transitions:
        return None, None, None

    K_min = None
    K_max = None
    Pu = None

    for K_lo_raw, K_hi_raw, direction in transitions:
        K_boundary, Pu_boundary = _refine_boundary(
            plant_num, plant_den, K_lo_raw, K_hi_raw)
        if direction == "stabilizing":
            K_min = K_boundary
        elif direction == "destabilizing":
            K_max = K_boundary
            Pu = Pu_boundary

    return K_min, K_max, Pu


# ------------------------------------------------------------------ #
#  Auto-tune methods (transfer function domain)                       #
# ------------------------------------------------------------------ #

def auto_tune_zn_closed(
    plant_num: np.ndarray,
    plant_den: np.ndarray,
    ctype: str = "PID",
) -> Optional[Dict[str, float]]:
    """Ziegler-Nichols closed-loop (ultimate gain) auto-tuning.

    Handles both stable and unstable open-loop plants by finding the
    stability boundaries. Uses the upper boundary (K_max) as Ku.

    Args:
        plant_num: Numerator polynomial coefficients (highest power first).
        plant_den: Denominator polynomial coefficients.
        ctype: Controller type — "P", "PI", or "PID".

    Returns:
        Dict with Kp, Ki, Kd keys, or None if Ku cannot be found.
    """
    plant_num = np.array(plant_num, dtype=float)
    plant_den = np.array(plant_den, dtype=float)

    K_min, Ku, Pu = _find_stability_boundaries(plant_num, plant_den)

    if Ku is None or Pu is None:
        return None

    if ctype == "P":
        return {"Kp": 0.5 * Ku, "Ki": 0.0, "Kd": 0.0}
    elif ctype == "PI":
        Kp = 0.45 * Ku
        Ti = Pu / 1.2
        return {"Kp": Kp, "Ki": Kp / Ti, "Kd": 0.0}
    else:  # PID
        Kp = 0.6 * Ku
        Ti = 0.5 * Pu
        Td = 0.125 * Pu
        Ki = Kp / Ti
        Kd = Kp * Td
        return {"Kp": Kp, "Ki": Ki, "Kd": Kd}


def auto_tune_itae(
    plant_num: np.ndarray,
    plant_den: np.ndarray,
    ctype: str = "PID",
    duration: float = 10.0,
    deriv_filter_N: float = 20.0,
) -> Optional[Dict[str, float]]:
    """ITAE-optimal PID tuning via Nelder-Mead numerical optimization.

    Minimizes ∫t·|e(t)|dt subject to closed-loop stability.
    Handles unstable plants by finding the minimum stabilizing gain
    and seeding the optimizer above it.

    Args:
        plant_num: Numerator polynomial coefficients (highest power first).
        plant_den: Denominator polynomial coefficients.
        ctype: Controller type — "P", "PI", or "PID".
        duration: Simulation duration for cost evaluation.
        deriv_filter_N: Derivative filter coefficient.

    Returns:
        Dict with Kp, Ki, Kd keys, or None if optimization fails.
    """
    plant_num = np.array(plant_num, dtype=float)
    plant_den = np.array(plant_den, dtype=float)
    N = deriv_filter_N
    T = np.linspace(0, duration, 500)

    def cost(gains: np.ndarray) -> float:
        kp = float(np.clip(gains[0], -200.0, 200.0))
        ki = float(np.clip(gains[1], -100.0, 100.0))
        kd = float(np.clip(gains[2], -50.0, 50.0))
        c_num = np.array([kp + kd * N, kp * N + ki, ki * N])
        c_den = np.array([1.0, N, 0.0])
        ol_n = np.convolve(c_num, plant_num)
        ol_d = np.convolve(c_den, plant_den)
        ml = max(len(ol_d), len(ol_n))
        cl_d = np.pad(ol_d, (ml - len(ol_d), 0)) + np.pad(ol_n, (ml - len(ol_n), 0))
        poles = np.roots(cl_d)
        if len(poles) > 0 and np.max(poles.real) > -1e-6:
            return 1e6
        try:
            sys_cl = signal.TransferFunction(ol_n, cl_d)
            t_sim, y_sim = signal.step(sys_cl, T=T)
            if not np.all(np.isfinite(y_sim)):
                return 1e6
            e_sim = 1.0 - y_sim
            return float(_trapz(t_sim * np.abs(e_sim), t_sim))
        except Exception:
            return 1e6

    # Find stability boundaries to seed the optimizer
    K_min, K_max, _ = _find_stability_boundaries(plant_num, plant_den)

    # Try ZN first for a good starting point
    zn_gains = auto_tune_zn_closed(plant_num, plant_den, ctype)
    if zn_gains and cost(np.array([zn_gains["Kp"], zn_gains["Ki"], zn_gains["Kd"]])) < 1e6:
        x0 = np.array([zn_gains["Kp"], zn_gains["Ki"], zn_gains["Kd"]])
    elif K_min is not None and K_max is not None:
        # Unstable plant: seed at midpoint of stable gain range
        kp_mid = (K_min + K_max) / 2
        x0 = np.array([kp_mid, abs(kp_mid) * 0.3, abs(kp_mid) * 0.1])
    elif K_min is not None:
        # Has lower boundary but no upper: seed above K_min
        kp_seed = K_min * 2.0
        x0 = np.array([kp_seed, abs(kp_seed) * 0.3, abs(kp_seed) * 0.1])
    else:
        x0 = np.array([1.0, 0.5, 0.1])

    # Try alternatives if initial point is infeasible
    if cost(x0) >= 1e6:
        kp_base = abs(x0[0]) if abs(x0[0]) > 0.1 else 5.0
        alternatives = [
            np.array([kp_base, kp_base * 0.3, kp_base * 0.5]),
            np.array([kp_base * 3, kp_base, kp_base]),
            np.array([-kp_base, -kp_base * 0.3, kp_base * 0.5]),
            np.array([5.0, 2.0, 10.0]),
            np.array([10.0, 5.0, 5.0]),
            np.array([50.0, 10.0, 20.0]),
            np.array([-50.0, -10.0, 20.0]),
        ]
        for alt in alternatives:
            if cost(alt) < 1e6:
                x0 = alt
                break
        else:
            return None  # All infeasible

    result = optimize.minimize(
        cost, x0, method="Nelder-Mead",
        options={"maxiter": 300, "xatol": 0.01, "fatol": 0.001},
    )
    kp = float(result.x[0])
    ki = float(result.x[1])
    kd = float(result.x[2])

    if ctype == "P":
        return {"Kp": kp, "Ki": 0.0, "Kd": 0.0}
    elif ctype == "PI":
        return {"Kp": kp, "Ki": ki, "Kd": 0.0}
    elif ctype == "PD":
        return {"Kp": kp, "Ki": 0.0, "Kd": kd}
    return {"Kp": kp, "Ki": ki, "Kd": kd}


def auto_tune_lqr_itae(
    f: Callable[[np.ndarray, np.ndarray], np.ndarray],
    x0: np.ndarray,
    A: np.ndarray,
    B: np.ndarray,
    x_eq: np.ndarray,
    u_eq: np.ndarray,
    output_index: int,
    x_ref: float,
    u_max: float = 100.0,
    duration: float = 5.0,
    dt: float = 0.01,
    n_states: int = 4,
) -> Optional[Tuple[np.ndarray, np.ndarray, np.ndarray]]:
    """ITAE-optimal LQR weight tuning via time-domain ODE simulation.

    Optimizes the diagonal Q weights and scalar R for LQR to minimize
    ITAE on the actual nonlinear trajectory. This works for all plants
    including open-loop unstable ones (inverted pendulums, ball & beam).

    Args:
        f: Dynamics function f(x, u) -> dx/dt.
        x0: Initial state vector.
        A: Linearized state matrix (n×n).
        B: Linearized input matrix (n×m).
        x_eq: Equilibrium state.
        u_eq: Equilibrium input.
        output_index: State index being tracked.
        x_ref: Reference value.
        u_max: Control saturation.
        duration: Simulation time.
        dt: Timestep.
        n_states: Number of states.

    Returns:
        (K, Q_diag, R_val) or None if optimization fails.
        K is the optimal gain matrix, Q_diag the optimal Q diagonal,
        R_val the optimal R scalar.
    """
    t_span = (0.0, duration)
    A = np.atleast_2d(A)
    B = np.atleast_2d(B)

    def cost(params: np.ndarray) -> float:
        # params = [log10(q1), log10(q2), ..., log10(r)]
        try:
            q_diag = np.power(10.0, np.clip(params[:n_states], -2, 4))
            r_val = 10.0 ** np.clip(params[n_states], -3, 3)
            Q = np.diag(q_diag)
            R = np.array([[r_val]])

            K, _, cl_eigs = compute_lqr(A, B, Q, R)

            # Check CL stability
            if np.max(cl_eigs.real) > -1e-6:
                return 1e6

            result = simulate_state_feedback(
                f, x0, t_span, K, x_eq, u_eq,
                u_max=u_max, dt=dt)
            t = result["t"]
            x = result["x"]
            y = x[:, output_index]

            if not np.all(np.isfinite(y)):
                return 1e6

            e = np.abs(x_ref - y)
            if np.max(e) > 10 * max(abs(x_ref - x0[output_index]), 1.0):
                return 1e6

            itae = float(_trapz(t * e, t))
            tail = max(1, len(t) // 5)
            tail_err = float(np.mean(e[-tail:]))
            return itae + 50.0 * tail_err
        except Exception:
            return 1e6

    # Starting points: vary Q diagonal weights in log space
    candidates = [
        np.array([1, 0, 1, 0, -1]),   # q=[10,1,10,1], r=0.1
        np.array([0, 0, 0, 0, 0]),     # q=[1,1,1,1], r=1
        np.array([2, 0, 0, 0, -1]),    # q=[100,1,1,1], r=0.1
        np.array([0, 0, 2, 0, -2]),    # q=[1,1,100,1], r=0.01
        np.array([1, 1, 1, 1, 0]),     # q=[10,10,10,10], r=1
    ]
    # Adjust: put weight on the controlled output
    for c in candidates:
        c[output_index] = max(c[output_index], 1.0)

    best_x0 = None
    best_cost = 1e6
    for cand in candidates:
        c = cost(cand[:n_states + 1])
        if c < best_cost:
            best_cost = c
            best_x0 = cand[:n_states + 1]

    if best_x0 is None or best_cost >= 1e6:
        return None

    result = optimize.minimize(
        cost, best_x0, method="Nelder-Mead",
        options={"maxiter": 80, "xatol": 0.2, "fatol": 0.05},
    )

    q_diag = np.power(10.0, np.clip(result.x[:n_states], -2, 4))
    r_val = 10.0 ** np.clip(result.x[n_states], -3, 3)
    Q = np.diag(q_diag)
    R = np.array([[r_val]])
    K, _, _ = compute_lqr(A, B, Q, R)
    return K, q_diag, r_val
