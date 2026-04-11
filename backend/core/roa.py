"""Region of Attraction (ROA) estimation utilities.

Grid-based ROA estimation via forward simulation of controlled nonlinear
systems. Classifies initial conditions as converged, diverged, or marginal.

Used by: nonlinear_control_lab.py
"""

import numpy as np
import concurrent.futures
from typing import Any, Callable, Dict, List, Optional, Tuple

from scipy.integrate import solve_ivp


def simulate_trajectory(f_numeric: Callable,
                        K: np.ndarray,
                        x_eq: np.ndarray,
                        u_eq: np.ndarray,
                        x0: np.ndarray,
                        t_span: Tuple[float, float],
                        n_states: int,
                        eps: float = 0.1
                        ) -> int:
    """Simulate a single initial condition and classify convergence.

    Uses state feedback u = -K(x - x_eq) + u_eq.

    Args:
        f_numeric: Callable f(x, u) -> dxdt (numpy arrays).
        K: Gain matrix (m x n).
        x_eq: Equilibrium state.
        u_eq: Equilibrium input.
        x0: Initial state.
        t_span: (t_start, t_end).
        n_states: Number of state variables.
        eps: Convergence threshold.

    Returns:
        0 = converged, 1 = diverged, 2 = marginal.
    """
    if K.ndim == 1:
        K = K.reshape(1, -1)

    def rhs(t: float, x: np.ndarray) -> np.ndarray:
        dx = x - x_eq
        u = (-K @ dx + u_eq.reshape(-1)).flatten()
        u = np.clip(u, -1000, 1000)
        try:
            dxdt = np.array(f_numeric(x, u)).flatten()
            if np.any(np.isnan(dxdt)) or np.any(np.isinf(dxdt)):
                return np.zeros(n_states)
            return dxdt
        except Exception:
            return np.zeros(n_states)

    def div_event(t: float, x: np.ndarray) -> float:
        return 1000.0 - np.linalg.norm(x)
    div_event.terminal = True
    div_event.direction = -1

    try:
        sol = solve_ivp(rhs, t_span, x0, method='RK45',
                        max_step=0.1, events=div_event,
                        rtol=1e-6, atol=1e-8)

        if sol.t_events and len(sol.t_events[0]) > 0:
            return 1  # diverged

        final_state = sol.y[:, -1]
        error = np.linalg.norm(final_state - x_eq)

        if error < eps:
            return 0  # converged
        elif error < eps * 10:
            return 2  # marginal
        else:
            return 1  # diverged

    except Exception:
        return 1  # diverged


def _simulate_single_ic(args: Tuple) -> int:
    """Wrapper for ThreadPoolExecutor — unpacks args tuple.

    Args:
        args: (f_numeric, K, x_eq, u_eq, x0, t_end, n_states, eps)

    Returns:
        Classification integer (0/1/2).
    """
    f_numeric, K, x_eq, u_eq, x0, t_end, n_states, eps = args
    return simulate_trajectory(
        f_numeric, K, x_eq, u_eq, x0,
        (0, t_end), n_states, eps
    )


def estimate_roa(f_numeric: Callable,
                 K: np.ndarray,
                 x_eq: np.ndarray,
                 u_eq: np.ndarray,
                 n_states: int,
                 proj_x: int,
                 proj_y: int,
                 grid_size: int = 25,
                 extent: float = 3.0,
                 t_end: float = 10.0,
                 eps: float = 0.1
                 ) -> Dict[str, Any]:
    """Compute region of attraction via grid-based simulation.

    Projects onto a 2D plane defined by proj_x and proj_y state indices.
    States not on axes are held at their equilibrium values.
    Uses ThreadPoolExecutor for parallelism.

    Args:
        f_numeric: Callable f(x, u) -> dxdt.
        K: Gain matrix (m x n).
        x_eq: Equilibrium state.
        u_eq: Equilibrium input.
        n_states: Number of states.
        proj_x: x-axis state index.
        proj_y: y-axis state index.
        grid_size: Grid resolution per axis.
        extent: Range around equilibrium.
        t_end: Simulation time for each IC.
        eps: Convergence threshold.

    Returns:
        Dict with 'x_vals', 'y_vals', 'result' (2D grid of 0/1/2).
    """
    cx = x_eq[proj_x]
    cy = x_eq[proj_y]
    x_vals = np.linspace(cx - extent, cx + extent, grid_size)
    y_vals = np.linspace(cy - extent, cy + extent, grid_size)

    # Build IC list
    tasks = []
    for i in range(grid_size):
        for j in range(grid_size):
            x0 = x_eq.copy()
            x0[proj_x] = x_vals[j]
            x0[proj_y] = y_vals[i]
            tasks.append((f_numeric, K, x_eq, u_eq, x0, t_end, n_states, eps))

    # Parallel execution
    results_flat = []
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            results_flat = list(executor.map(_simulate_single_ic, tasks))
    except Exception:
        results_flat = [1] * len(tasks)

    # Reshape to grid
    result_grid = np.array(results_flat).reshape(grid_size, grid_size)

    return {
        "x_vals": x_vals.tolist(),
        "y_vals": y_vals.tolist(),
        "result": result_grid.tolist(),
    }
