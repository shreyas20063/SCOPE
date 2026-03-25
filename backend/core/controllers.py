"""Shared controller math for 3D Physics Lab simulations.

Pure functions for PID, LQR, Pole Placement, and LQG controller design
and closed-loop simulation. All simulation uses solve_ivp with RK45 on
the full nonlinear ODE — linearization is only used to compute gains.

Used by: inverted_pendulum_3d, ball_beam_3d, coupled_tanks_3d,
         furuta_pendulum (retrofit), mass_spring_system (retrofit).
"""

from typing import Callable, Dict, List, Optional, Tuple, Union

import numpy as np
from scipy.integrate import solve_ivp
from scipy.linalg import expm, solve_continuous_are
from scipy.signal import place_poles as scipy_place_poles


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

    Args:
        A: State matrix (n×n).
        B: Input matrix (n×m).
        C: Output matrix (p×n).
        Q_lqr: LQR state cost (n×n).
        R_lqr: LQR input cost (m×m).
        Q_kalman: Process noise covariance (n×n).
        R_kalman: Measurement noise covariance (p×p).

    Returns:
        (K, L, P_ctrl, P_est) — controller gain, observer gain,
        control Riccati solution, estimator Riccati solution.
    """
    K, P_ctrl, _ = compute_lqr(A, B, Q_lqr, R_lqr)

    # Dual problem: estimator Riccati
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

        # PID output
        u_pid = Kp * e + Ki * int_err + Kd * d_filt
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
        u_pid = Kp * e + Ki * int_err_traj[i] + Kd * d_filt_traj[i]
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
