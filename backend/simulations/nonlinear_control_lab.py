"""
Nonlinear Control Lab — Linearize, Design, Validate pipeline.

Full nonlinear plant analysis: SymPy-based Jacobian linearization at user-selected
equilibria, LQR / Pole Placement controller design on the linearized model, then
side-by-side linear vs nonlinear simulation to validate the linearization regime.

Core theory (Khalil Ch 3-4, Slotine & Li Ch 3-4):
- Jacobian linearization: δẋ = A δx + B δu  where A=∂f/∂x, B=∂f/∂u at (x*,u*)
- LQR: minimize ∫(x'Qx + u'Ru)dt  →  Riccati equation  →  K = R⁻¹B'P
- Pole placement: choose CL eigenvalues, compute K via Ackermann / scipy
- Validity: linearization accurate near equilibrium; nonlinear sim shows actual ROA
"""

import re
import time
import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from scipy.integrate import solve_ivp
from scipy.linalg import expm, solve_continuous_are
from scipy.signal import place_poles
import concurrent.futures

from .base_simulator import BaseSimulator

# Try sympy — needed for symbolic Jacobian
try:
    import sympy as sp
    from sympy import Matrix, symbols, sympify, cos, sin, sqrt, pi
    from sympy import lambdify as sp_lambdify
    _HAS_SYMPY = True
except ImportError:
    _HAS_SYMPY = False


# ------------------------------------------------------------------ #
#  Safe expression validation (reused from phase_portrait.py)         #
# ------------------------------------------------------------------ #

_DANGEROUS_PATTERNS = [
    "import", "exec", "eval", "__", "open", "file",
    "os.", "sys.", "subprocess", "compile", "globals",
    "locals", "getattr", "setattr", "delattr", "lambda",
    "class", "def ", "yield", "async", "await",
]


def _validate_expr(expr: str) -> Tuple[bool, str]:
    """Validate expression string for security.

    Args:
        expr: Raw user expression string.

    Returns:
        (is_valid, error_message) tuple.
    """
    if not expr or not expr.strip():
        return False, "Expression cannot be empty"
    expr_lower = expr.lower()
    for pat in _DANGEROUS_PATTERNS:
        if pat in expr_lower:
            return False, f"Unsafe pattern: '{pat}'"
    if expr.count("(") != expr.count(")"):
        return False, "Unbalanced parentheses"
    if len(expr) > 500:
        return False, "Expression too long (max 500 chars)"
    return True, ""


# ------------------------------------------------------------------ #
#  Preset plant definitions                                           #
# ------------------------------------------------------------------ #

def _get_preset_plants() -> Dict[str, Dict[str, Any]]:
    """Return preset nonlinear plant definitions.

    Each preset defines:
        n_states, n_inputs: dimensions
        state_names, input_names: display labels
        f_exprs: list of SymPy expression strings for ẋᵢ
        equilibria: list of (x_eq, u_eq) tuples
        params: dict of physical parameter symbols and values
        description: short text
    """
    return {
        "inverted_pendulum": {
            "n_states": 4,
            "n_inputs": 1,
            "state_names": ["x (cart pos)", "ẋ (cart vel)",
                            "θ (angle)", "θ̇ (ang vel)"],
            "input_names": ["F (force)"],
            "params": {"M": 1.0, "m": 0.1, "l": 0.5, "g": 9.81},
            "description": "Inverted pendulum on cart (4 states, 1 input)",
            "equilibria": [
                {
                    "label": "Upright (θ=π)",
                    "x_eq": [0.0, 0.0, np.pi, 0.0],
                    "u_eq": [0.0],
                },
                {
                    "label": "Hanging (θ=0)",
                    "x_eq": [0.0, 0.0, 0.0, 0.0],
                    "u_eq": [0.0],
                },
            ],
        },
        "ball_and_beam": {
            "n_states": 4,
            "n_inputs": 1,
            "state_names": ["r (ball pos)", "ṙ (ball vel)",
                            "α (beam angle)", "α̇ (beam ang vel)"],
            "input_names": ["τ (torque)"],
            "params": {"J_b": 0.05, "m": 0.1, "g": 9.81, "R": 0.015},
            "description": "Ball and beam system (4 states, 1 input)",
            "equilibria": [
                {
                    "label": "Ball at center",
                    "x_eq": [0.0, 0.0, 0.0, 0.0],
                    "u_eq": [0.0],
                },
            ],
        },
        "coupled_tanks": {
            "n_states": 2,
            "n_inputs": 2,
            "state_names": ["h₁ (tank 1 level)", "h₂ (tank 2 level)"],
            "input_names": ["q₁ (inflow 1)", "q₂ (inflow 2)"],
            "params": {"A1": 1.0, "A2": 1.0, "a1": 0.2, "a2": 0.2, "g": 9.81},
            "description": "Coupled tanks MIMO (2 states, 2 inputs) — √h nonlinearity",
            "equilibria": [
                {
                    "label": "Nominal levels (h₁=1, h₂=0.5)",
                    "x_eq": [1.0, 0.5],
                    "u_eq": [0.885889, -0.259471],
                },
            ],
        },
        "van_der_pol": {
            "n_states": 2,
            "n_inputs": 1,
            "state_names": ["x₁", "x₂"],
            "input_names": ["u"],
            "params": {"mu": 1.0},
            "description": "Van der Pol oscillator + input (2 states, 1 input)",
            "equilibria": [
                {
                    "label": "Origin",
                    "x_eq": [0.0, 0.0],
                    "u_eq": [0.0],
                },
            ],
        },
    }


def _build_symbolic_dynamics(preset_name: str,
                             params: Dict[str, float]
                             ) -> Tuple[List, List, List, sp.Matrix]:
    """Build SymPy symbolic state equations for a preset plant.

    Args:
        preset_name: Key into preset definitions.
        params: Physical parameter values.

    Returns:
        (x_syms, u_syms, param_syms, f_vector) where f_vector is a SymPy Matrix
        of expressions for ẋ = f(x, u).
    """
    if preset_name == "inverted_pendulum":
        x1, x2, x3, x4 = symbols('x1 x2 x3 x4')
        u1 = symbols('u1')
        M_val = params["M"]
        m_val = params["m"]
        l_val = params["l"]
        g_val = params["g"]

        # Standard inverted pendulum: θ measured from downward vertical
        # θ=π is upright.  Dynamics from Lagrangian:
        # (M+m)ẍ + ml(θ̈ cosθ − θ̇² sinθ) = F
        # l θ̈ + ẍ cosθ − g sinθ = 0
        # Solved for ẍ, θ̈:
        denom = M_val + m_val * sp.sin(x3)**2

        f1 = x2
        f2 = (u1 + m_val * sp.sin(x3) * (l_val * x4**2 + g_val * sp.cos(x3))) / denom
        f3 = x4
        f4 = (-u1 * sp.cos(x3) - m_val * l_val * x4**2 * sp.sin(x3) * sp.cos(x3)
               - (M_val + m_val) * g_val * sp.sin(x3)) / (l_val * denom)

        return ([x1, x2, x3, x4], [u1], [],
                sp.Matrix([f1, f2, f3, f4]))

    elif preset_name == "ball_and_beam":
        x1, x2, x3, x4 = symbols('x1 x2 x3 x4')
        u1 = symbols('u1')
        m_val = params["m"]
        g_val = params["g"]
        J_b = params["J_b"]

        # Ball: m(r̈ − r α̇²) = −mg sinα  (rolling on beam)
        # Beam: (J_beam + mr²) α̈ + 2mr ṙ α̇ + mgr cosα = τ
        # Simplified (small ball, J_ball neglected):
        f1 = x2
        f2 = x1 * x4**2 - g_val * sp.sin(x3)
        f3 = x4
        # Simplified beam torque equation
        f4 = (u1 - 2 * m_val * x1 * x2 * x4
               - m_val * g_val * x1 * sp.cos(x3)) / (J_b + m_val * x1**2)

        return ([x1, x2, x3, x4], [u1], [],
                sp.Matrix([f1, f2, f3, f4]))

    elif preset_name == "coupled_tanks":
        x1, x2 = symbols('x1 x2')
        u1, u2 = symbols('u1 u2')
        A1_v = params["A1"]
        A2_v = params["A2"]
        a1_v = params["a1"]
        a2_v = params["a2"]
        g_val = params["g"]

        # ḣ₁ = (q₁ − a₁√(2g h₁)) / A₁
        # ḣ₂ = (q₂ + a₁√(2g h₁) − a₂√(2g h₂)) / A₂
        # Note: using sqrt(x) directly — states assumed positive (water level).
        # Abs() breaks SymPy Jacobian; for linearization near positive eq. this is fine.
        c = sp.sqrt(2 * g_val)
        f1 = (u1 - a1_v * c * sp.sqrt(x1)) / A1_v
        f2 = (u2 + a1_v * c * sp.sqrt(x1)
               - a2_v * c * sp.sqrt(x2)) / A2_v

        return ([x1, x2], [u1, u2], [],
                sp.Matrix([f1, f2]))

    elif preset_name == "van_der_pol":
        x1, x2 = symbols('x1 x2')
        u1 = symbols('u1')
        mu_val = params["mu"]

        f1 = x2
        f2 = mu_val * (1 - x1**2) * x2 - x1 + u1

        return ([x1, x2], [u1], [],
                sp.Matrix([f1, f2]))

    else:
        raise ValueError(f"Unknown preset: {preset_name}")


def _build_custom_symbolic(f_exprs: List[str],
                           n_states: int,
                           n_inputs: int
                           ) -> Tuple[List, List, sp.Matrix, Optional[str]]:
    """Build SymPy symbolic dynamics from user-entered expressions.

    Args:
        f_exprs: List of expression strings for each ẋᵢ.
        n_states: Number of state variables.
        n_inputs: Number of inputs.

    Returns:
        (x_syms, u_syms, f_vector, error_string). error_string is None on success.
    """
    x_syms = symbols(' '.join(f'x{i+1}' for i in range(n_states)))
    if isinstance(x_syms, sp.Symbol):
        x_syms = [x_syms]
    else:
        x_syms = list(x_syms)

    u_syms = symbols(' '.join(f'u{i+1}' for i in range(n_inputs)))
    if isinstance(u_syms, sp.Symbol):
        u_syms = [u_syms]
    else:
        u_syms = list(u_syms)

    # Build namespace for sympify
    local_dict = {}
    for s in x_syms:
        local_dict[str(s)] = s
    for s in u_syms:
        local_dict[str(s)] = s

    f_vec = []
    for i, expr_str in enumerate(f_exprs):
        ok, err = _validate_expr(expr_str)
        if not ok:
            return x_syms, u_syms, sp.Matrix([]), f"f{i+1}: {err}"
        try:
            parsed = expr_str.strip().replace("^", "**")
            sym_expr = sympify(parsed, locals=local_dict)
            f_vec.append(sym_expr)
        except Exception as exc:
            return x_syms, u_syms, sp.Matrix([]), f"f{i+1}: {exc}"

    return x_syms, u_syms, sp.Matrix(f_vec), None


# ------------------------------------------------------------------ #
#  Jacobian linearization                                             #
# ------------------------------------------------------------------ #

def _compute_jacobians(f_vector: sp.Matrix,
                       x_syms: List,
                       u_syms: List,
                       x_eq: List[float],
                       u_eq: List[float]
                       ) -> Tuple[np.ndarray, np.ndarray]:
    """Compute A = ∂f/∂x and B = ∂f/∂u evaluated at equilibrium.

    Args:
        f_vector: SymPy Matrix of state equations.
        x_syms: SymPy state symbols.
        u_syms: SymPy input symbols.
        x_eq: Equilibrium state values.
        u_eq: Equilibrium input values.

    Returns:
        (A, B) as numpy arrays.
    """
    n = len(x_syms)
    m = len(u_syms)

    # Symbolic Jacobians
    A_sym = f_vector.jacobian(sp.Matrix(x_syms))
    B_sym = f_vector.jacobian(sp.Matrix(u_syms))

    # Substitution dict
    subs = {}
    for i, s in enumerate(x_syms):
        subs[s] = x_eq[i]
    for i, s in enumerate(u_syms):
        subs[s] = u_eq[i]

    # Evaluate numerically
    A_num = np.array(A_sym.subs(subs).tolist(), dtype=float)
    B_num = np.array(B_sym.subs(subs).tolist(), dtype=float)

    return A_num, B_num


def _check_controllability(A: np.ndarray, B: np.ndarray) -> Tuple[bool, int]:
    """Check controllability via rank of [B, AB, A²B, ..., A^(n-1)B].

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


# ------------------------------------------------------------------ #
#  Controller design                                                  #
# ------------------------------------------------------------------ #

def _design_lqr(A: np.ndarray,
                B: np.ndarray,
                Q: np.ndarray,
                R: np.ndarray
                ) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], str]:
    """Design LQR controller via continuous Riccati equation.

    Args:
        A: System matrix (n x n).
        B: Input matrix (n x m).
        Q: State weight matrix (n x n, positive semi-definite).
        R: Input weight matrix (m x m, positive definite).

    Returns:
        (K, P, error_message). K is m x n gain matrix, P is Riccati solution.
        On failure, K and P are None and error_message describes the issue.
    """
    if B.ndim == 1:
        B = B.reshape(-1, 1)
    try:
        P = solve_continuous_are(A, B, Q, R)
        K = np.linalg.solve(R, B.T @ P)
        return K, P, ""
    except np.linalg.LinAlgError as exc:
        return None, None, f"Riccati solve failed: {exc}"
    except Exception as exc:
        return None, None, f"LQR error: {exc}"


def _design_pole_placement(A: np.ndarray,
                           B: np.ndarray,
                           desired_poles: np.ndarray
                           ) -> Tuple[Optional[np.ndarray], str]:
    """Design controller via pole placement.

    Ensures conjugate pairs for real K matrix.

    Args:
        A: System matrix (n x n).
        B: Input matrix (n x m).
        desired_poles: Array of desired CL eigenvalues.

    Returns:
        (K, error_message). K is m x n gain matrix.
    """
    if B.ndim == 1:
        B = B.reshape(-1, 1)
    try:
        result = place_poles(A, B, desired_poles)
        K = result.gain_matrix
        return K, ""
    except Exception as exc:
        return None, f"Pole placement error: {exc}"


def _ensure_conjugate_pairs(poles: List[complex], n: int) -> np.ndarray:
    """Ensure complex poles come in conjugate pairs for real K.

    If the user specifies a complex pole without its conjugate, add it.
    If both a pole and its conjugate are already present, keep both.

    Args:
        poles: List of desired poles.
        n: Required number of poles.

    Returns:
        Array of n poles with conjugate pairs enforced.
    """
    result = []
    used = set()

    for i, p in enumerate(poles):
        if i in used or len(result) >= n:
            continue

        if abs(p.imag) < 1e-10:
            # Real pole — no conjugate needed
            result.append(complex(p.real, 0))
            used.add(i)
        else:
            # Complex pole — look for its conjugate in the remaining list
            conj = p.conjugate()
            found_conj = False
            for j in range(i + 1, len(poles)):
                if j not in used and abs(poles[j] - conj) < 1e-10:
                    # Conjugate already provided by user
                    result.append(p)
                    result.append(conj)
                    used.add(i)
                    used.add(j)
                    found_conj = True
                    break
            if not found_conj:
                # Add conjugate automatically
                result.append(p)
                used.add(i)
                if len(result) < n:
                    result.append(conj)

    return np.array(result[:n])


# ------------------------------------------------------------------ #
#  Simulation engine                                                  #
# ------------------------------------------------------------------ #

def _simulate_nonlinear(f_numeric: callable,
                        K: np.ndarray,
                        x_eq: np.ndarray,
                        u_eq: np.ndarray,
                        x0: np.ndarray,
                        t_span: Tuple[float, float],
                        n_points: int = 500
                        ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, bool]:
    """Simulate nonlinear system with state feedback u = -K(x - x_eq) + u_eq.

    Args:
        f_numeric: Callable f(x, u) -> dx/dt (numpy arrays).
        K: Gain matrix (m x n).
        x_eq: Equilibrium state.
        u_eq: Equilibrium input.
        x0: Initial state.
        t_span: (t_start, t_end).
        n_points: Number of output time points.

    Returns:
        (t, x_traj, u_traj, diverged) where x_traj is (n_points, n),
        u_traj is (n_points, m), diverged is bool.
    """
    n = len(x_eq)
    m = len(u_eq)
    if K.ndim == 1:
        K = K.reshape(1, -1)

    diverged = False

    def rhs(t: float, x: np.ndarray) -> np.ndarray:
        dx = x - x_eq
        u = -K @ dx + u_eq.reshape(-1)
        # Clamp control effort to avoid numerical blowup
        u = np.clip(u, -1000, 1000)
        try:
            dxdt = f_numeric(x, u)
            if np.any(np.isnan(dxdt)) or np.any(np.isinf(dxdt)):
                return np.zeros(n)
            return np.array(dxdt).flatten()
        except Exception:
            return np.zeros(n)

    def divergence_event(t: float, x: np.ndarray) -> float:
        return 1000.0 - np.linalg.norm(x)
    divergence_event.terminal = True
    divergence_event.direction = -1

    t_eval = np.linspace(t_span[0], t_span[1], n_points)

    try:
        sol = solve_ivp(rhs, t_span, x0, method='RK45',
                        t_eval=t_eval, events=divergence_event,
                        max_step=0.05, rtol=1e-8, atol=1e-10)
        if sol.t_events and len(sol.t_events[0]) > 0:
            diverged = True
    except Exception:
        # Fallback: return equilibrium
        sol_t = t_eval
        sol_y = np.tile(x_eq.reshape(-1, 1), (1, n_points))
        t_out = sol_t
        x_out = sol_y.T
        u_out = np.tile(u_eq, (n_points, 1))
        return t_out, x_out, u_out, True

    # Pad if solve_ivp terminated early
    actual_pts = len(sol.t)
    t_out = np.zeros(n_points)
    x_out = np.zeros((n_points, n))
    u_out = np.zeros((n_points, m))

    t_out[:actual_pts] = sol.t
    x_out[:actual_pts] = sol.y.T

    if actual_pts < n_points:
        diverged = True
        t_out[actual_pts:] = np.linspace(sol.t[-1], t_span[1],
                                         n_points - actual_pts)
        x_out[actual_pts:] = sol.y[:, -1]

    # Compute control at each point
    for i in range(n_points):
        dx = x_out[i] - x_eq
        u_out[i] = (-K @ dx + u_eq.reshape(-1)).flatten()

    u_out = np.clip(u_out, -1000, 1000)

    return t_out, x_out, u_out, diverged


def _simulate_linear(A: np.ndarray,
                     B: np.ndarray,
                     K: np.ndarray,
                     x_eq: np.ndarray,
                     u_eq: np.ndarray,
                     x0: np.ndarray,
                     t_span: Tuple[float, float],
                     n_points: int = 500
                     ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Simulate linearized system via matrix exponential.

    δẋ = (A - BK)δx, δx(0) = x0 - x_eq
    x(t) = expm((A-BK)*t) @ δx0 + x_eq

    Args:
        A: System matrix.
        B: Input matrix.
        K: Gain matrix.
        x_eq: Equilibrium state.
        u_eq: Equilibrium input.
        x0: Initial state.
        t_span: (t_start, t_end).
        n_points: Number of output points.

    Returns:
        (t, x_traj, u_traj) arrays.
    """
    if B.ndim == 1:
        B = B.reshape(-1, 1)
    if K.ndim == 1:
        K = K.reshape(1, -1)

    n = A.shape[0]
    m = K.shape[0]
    A_cl = A - B @ K
    dx0 = x0 - x_eq

    t_arr = np.linspace(t_span[0], t_span[1], n_points)
    x_out = np.zeros((n_points, n))
    u_out = np.zeros((n_points, m))

    for i, t in enumerate(t_arr):
        dx = expm(A_cl * t) @ dx0
        x_out[i] = dx + x_eq
        u_out[i] = (-K @ dx + u_eq.reshape(-1)).flatten()

    return t_arr, x_out, u_out


# ------------------------------------------------------------------ #
#  Vector field and streamlines                                       #
# ------------------------------------------------------------------ #

def _compute_vector_field(f_numeric: callable,
                          K: np.ndarray,
                          x_eq: np.ndarray,
                          u_eq: np.ndarray,
                          n_states: int,
                          proj_x: int,
                          proj_y: int,
                          grid_size: int = 20,
                          extent: float = 3.0
                          ) -> Dict[str, Any]:
    """Compute 2D projected vector field of controlled dynamics.

    Projects the full n-dimensional dynamics onto a 2D plane defined by
    proj_x and proj_y state indices.  States not on axes are held at equilibrium.

    Args:
        f_numeric: Callable f(x, u) -> dxdt.
        K: Gain matrix (m x n).
        x_eq: Equilibrium state.
        u_eq: Equilibrium input.
        n_states: Total number of states.
        proj_x: State index for x-axis.
        proj_y: State index for y-axis.
        grid_size: Number of grid points per axis.
        extent: Range around equilibrium for the grid.

    Returns:
        Dict with x_grid, y_grid, dx, dy arrays (as lists).
    """
    if K.ndim == 1:
        K = K.reshape(1, -1)

    cx = x_eq[proj_x]
    cy = x_eq[proj_y]
    x_vals = np.linspace(cx - extent, cx + extent, grid_size)
    y_vals = np.linspace(cy - extent, cy + extent, grid_size)
    X, Y = np.meshgrid(x_vals, y_vals)

    DX = np.zeros_like(X)
    DY = np.zeros_like(Y)

    for i in range(grid_size):
        for j in range(grid_size):
            state = x_eq.copy()
            state[proj_x] = X[i, j]
            state[proj_y] = Y[i, j]

            dx = state - x_eq
            u = (-K @ dx + u_eq.reshape(-1)).flatten()
            u = np.clip(u, -1000, 1000)

            try:
                dxdt = np.array(f_numeric(state, u)).flatten()
                if np.any(np.isnan(dxdt)) or np.any(np.isinf(dxdt)):
                    dxdt = np.zeros(n_states)
            except Exception:
                dxdt = np.zeros(n_states)

            DX[i, j] = dxdt[proj_x]
            DY[i, j] = dxdt[proj_y]

    # Normalize for display
    mag = np.sqrt(DX**2 + DY**2)
    max_mag = np.max(mag)
    if max_mag > 1e-10:
        DX_norm = DX / max_mag
        DY_norm = DY / max_mag
    else:
        DX_norm = DX
        DY_norm = DY

    return {
        "x_grid": X.tolist(),
        "y_grid": Y.tolist(),
        "dx": DX_norm.tolist(),
        "dy": DY_norm.tolist(),
        "mag": mag.tolist(),
    }


def _compute_streamlines(f_numeric: callable,
                         K: np.ndarray,
                         x_eq: np.ndarray,
                         u_eq: np.ndarray,
                         n_states: int,
                         proj_x: int,
                         proj_y: int,
                         n_seeds: int = 10,
                         extent: float = 3.0,
                         t_stream: float = 5.0
                         ) -> List[Dict[str, List]]:
    """Compute streamlines via forward integration from seed points.

    Args:
        f_numeric: Callable f(x, u) -> dxdt.
        K: Gain matrix.
        x_eq: Equilibrium state.
        u_eq: Equilibrium input.
        n_states: Number of states.
        proj_x: x-axis state index.
        proj_y: y-axis state index.
        n_seeds: Number of seed points.
        extent: Spatial extent around equilibrium.
        t_stream: Integration time.

    Returns:
        List of dicts with 'x' and 'y' keys (list of floats for each streamline).
    """
    if K.ndim == 1:
        K = K.reshape(1, -1)

    # Generate seed points in a ring around equilibrium
    angles = np.linspace(0, 2 * np.pi, n_seeds, endpoint=False)
    radius = extent * 0.7
    streamlines = []

    for angle in angles:
        x0 = x_eq.copy()
        x0[proj_x] += radius * np.cos(angle)
        x0[proj_y] += radius * np.sin(angle)

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
            return 500.0 - np.linalg.norm(x)
        div_event.terminal = True
        div_event.direction = -1

        try:
            sol = solve_ivp(rhs, (0, t_stream), x0, method='RK45',
                            max_step=0.1, events=div_event,
                            rtol=1e-6, atol=1e-8)
            if len(sol.t) > 2:
                streamlines.append({
                    "x": sol.y[proj_x].tolist(),
                    "y": sol.y[proj_y].tolist(),
                })
        except Exception:
            continue

    return streamlines


# ------------------------------------------------------------------ #
#  Region of Attraction                                               #
# ------------------------------------------------------------------ #

def _simulate_single_ic(args: Tuple) -> int:
    """Simulate a single IC and classify convergence.

    Designed for use with ThreadPoolExecutor.

    Args:
        args: (f_numeric, K, x_eq, u_eq, x0, t_end, n_states, eps)

    Returns:
        0 = converged, 1 = diverged, 2 = marginal
    """
    f_numeric, K, x_eq, u_eq, x0, t_end, n_states, eps = args

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
        sol = solve_ivp(rhs, (0, t_end), x0, method='RK45',
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


def _compute_roa(f_numeric: callable,
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

    Uses ThreadPoolExecutor for parallelism.

    Args:
        f_numeric: Callable f(x, u) -> dxdt.
        K: Gain matrix.
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
        Dict with x_vals, y_vals, result (2D grid of 0/1/2).
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


# ------------------------------------------------------------------ #
#  LaTeX formatting                                                   #
# ------------------------------------------------------------------ #

def _matrix_to_latex(mat: np.ndarray, name: str, fmt: str = ".3g") -> str:
    """Format a numpy matrix as KaTeX LaTeX string.

    Args:
        mat: 2D numpy array.
        name: Matrix name (e.g., "A", "K").
        fmt: Number format string.

    Returns:
        LaTeX string.
    """
    if mat.ndim == 1:
        mat = mat.reshape(1, -1)
    rows = mat.shape[0]
    cols = mat.shape[1]

    inner = " \\\\ ".join(
        " & ".join(format(mat[i, j], fmt) for j in range(cols))
        for i in range(rows)
    )
    return f"{name} = \\begin{{bmatrix}} {inner} \\end{{bmatrix}}"


def _ode_to_latex(f_vector: 'sp.Matrix',
                  x_syms: List,
                  u_syms: List) -> str:
    """Convert SymPy ODE to LaTeX string for display.

    Args:
        f_vector: SymPy Matrix of expressions.
        x_syms: State symbols.
        u_syms: Input symbols.

    Returns:
        LaTeX string of the ODE system.
    """
    if not _HAS_SYMPY:
        return ""
    lines = []
    for i, (x, f) in enumerate(zip(x_syms, f_vector)):
        latex_f = sp.latex(f)
        lines.append(f"\\dot{{x}}_{{{i+1}}} = {latex_f}")
    return " \\\\ ".join(lines)


# ------------------------------------------------------------------ #
#  Main Simulator Class                                               #
# ------------------------------------------------------------------ #

class NonlinearControlLabSimulator(BaseSimulator):
    """Nonlinear Control Lab: Linearize → Design → Validate pipeline.

    Provides Jacobian linearization of nonlinear plants at user-selected
    equilibria, LQR and pole placement controller design, and side-by-side
    linear vs nonlinear simulation with vector fields and ROA analysis.
    """

    PARAMETER_SCHEMA = {
        "plant_preset": {
            "type": "select", "default": "inverted_pendulum",
            "options": [
                {"value": "inverted_pendulum", "label": "Inverted Pendulum on Cart"},
                {"value": "ball_and_beam", "label": "Ball and Beam"},
                {"value": "coupled_tanks", "label": "Coupled Tanks (MIMO)"},
                {"value": "van_der_pol", "label": "Van der Pol + Input"},
                {"value": "custom", "label": "Custom ODE"},
            ],
        },
        "equilibrium_idx": {
            "type": "select", "default": "0",
            "options": [
                {"value": "0", "label": "Equilibrium 1"},
                {"value": "1", "label": "Equilibrium 2"},
                {"value": "2", "label": "Equilibrium 3"},
            ],
        },
        "controller_method": {
            "type": "select", "default": "lqr",
            "options": [
                {"value": "lqr", "label": "LQR (Linear Quadratic Regulator)"},
                {"value": "pole_placement", "label": "Pole Placement"},
            ],
        },
        "projection_x": {
            "type": "select", "default": "0",
            "options": [
                {"value": "0", "label": "State 1"},
                {"value": "1", "label": "State 2"},
                {"value": "2", "label": "State 3"},
                {"value": "3", "label": "State 4"},
            ],
        },
        "projection_y": {
            "type": "select", "default": "2",
            "options": [
                {"value": "0", "label": "State 1"},
                {"value": "1", "label": "State 2"},
                {"value": "2", "label": "State 3"},
                {"value": "3", "label": "State 4"},
            ],
        },
        "lqr_q1": {"type": "slider", "min": 0.01, "max": 100,
                    "step": 0.01, "default": 1.0},
        "lqr_q2": {"type": "slider", "min": 0.01, "max": 100,
                    "step": 0.01, "default": 1.0},
        "lqr_q3": {"type": "slider", "min": 0.01, "max": 100,
                    "step": 0.01, "default": 10.0},
        "lqr_q4": {"type": "slider", "min": 0.01, "max": 100,
                    "step": 0.01, "default": 1.0},
        "lqr_r1": {"type": "slider", "min": 0.01, "max": 100,
                    "step": 0.01, "default": 1.0},
        "lqr_r2": {"type": "slider", "min": 0.01, "max": 100,
                    "step": 0.01, "default": 1.0},
        "pole_real_1": {"type": "slider", "min": -20, "max": 0,
                        "step": 0.1, "default": -2.0},
        "pole_imag_1": {"type": "slider", "min": -10, "max": 10,
                        "step": 0.1, "default": 0.0},
        "pole_real_2": {"type": "slider", "min": -20, "max": 0,
                        "step": 0.1, "default": -3.0},
        "pole_imag_2": {"type": "slider", "min": -10, "max": 10,
                        "step": 0.1, "default": 0.0},
        "pole_real_3": {"type": "slider", "min": -20, "max": 0,
                        "step": 0.1, "default": -4.0},
        "pole_imag_3": {"type": "slider", "min": -10, "max": 10,
                        "step": 0.1, "default": 0.0},
        "pole_real_4": {"type": "slider", "min": -20, "max": 0,
                        "step": 0.1, "default": -5.0},
        "pole_imag_4": {"type": "slider", "min": -10, "max": 10,
                        "step": 0.1, "default": 0.0},
        "ic_offset_1": {"type": "slider", "min": -5, "max": 5,
                        "step": 0.1, "default": 0.0},
        "ic_offset_2": {"type": "slider", "min": -5, "max": 5,
                        "step": 0.1, "default": 0.1},
        "ic_offset_3": {"type": "slider", "min": -5, "max": 5,
                        "step": 0.1, "default": 0.2},
        "ic_offset_4": {"type": "slider", "min": -5, "max": 5,
                        "step": 0.1, "default": 0.0},
        "sim_time": {"type": "slider", "min": 1, "max": 30,
                     "step": 0.5, "default": 10.0},
        "show_linear": {"type": "checkbox", "default": True},
        "show_vector_field": {"type": "checkbox", "default": True},
        "show_streamlines": {"type": "checkbox", "default": True},
        "n_states_custom": {
            "type": "select", "default": "2",
            "options": [
                {"value": "2", "label": "2 states"},
                {"value": "3", "label": "3 states"},
                {"value": "4", "label": "4 states"},
            ],
        },
        "n_inputs_custom": {
            "type": "select", "default": "1",
            "options": [
                {"value": "1", "label": "1 input"},
                {"value": "2", "label": "2 inputs"},
            ],
        },
        "f1_expr": {"type": "expression", "default": "x2"},
        "f2_expr": {"type": "expression",
                     "default": "-sin(x1) - 0.5*x2 + u1"},
        "f3_expr": {"type": "expression", "default": "x4"},
        "f4_expr": {"type": "expression", "default": "-x3 + u1"},
        "eq_x1": {"type": "slider", "min": -10, "max": 10,
                   "step": 0.1, "default": 0.0},
        "eq_x2": {"type": "slider", "min": -10, "max": 10,
                   "step": 0.1, "default": 0.0},
        "eq_x3": {"type": "slider", "min": -10, "max": 10,
                   "step": 0.1, "default": 0.0},
        "eq_x4": {"type": "slider", "min": -10, "max": 10,
                   "step": 0.1, "default": 0.0},
        "eq_u1": {"type": "slider", "min": -10, "max": 10,
                   "step": 0.1, "default": 0.0},
        "eq_u2": {"type": "slider", "min": -10, "max": 10,
                   "step": 0.1, "default": 0.0},
    }

    DEFAULT_PARAMS = {
        "plant_preset": "inverted_pendulum",
        "equilibrium_idx": "0",
        "controller_method": "lqr",
        "projection_x": "0",
        "projection_y": "2",
        "lqr_q1": 1.0, "lqr_q2": 1.0, "lqr_q3": 10.0, "lqr_q4": 1.0,
        "lqr_r1": 1.0, "lqr_r2": 1.0,
        "pole_real_1": -2.0, "pole_imag_1": 0.0,
        "pole_real_2": -3.0, "pole_imag_2": 0.0,
        "pole_real_3": -4.0, "pole_imag_3": 0.0,
        "pole_real_4": -5.0, "pole_imag_4": 0.0,
        "ic_offset_1": 0.0, "ic_offset_2": 0.1,
        "ic_offset_3": 0.2, "ic_offset_4": 0.0,
        "sim_time": 10.0,
        "show_linear": True,
        "show_vector_field": True,
        "show_streamlines": True,
        "n_states_custom": "2",
        "n_inputs_custom": "1",
        "f1_expr": "x2",
        "f2_expr": "-sin(x1) - 0.5*x2 + u1",
        "f3_expr": "x4",
        "f4_expr": "-x3 + u1",
        "eq_x1": 0.0, "eq_x2": 0.0, "eq_x3": 0.0, "eq_x4": 0.0,
        "eq_u1": 0.0, "eq_u2": 0.0,
    }

    HUB_SLOTS = ['control']
    HUB_DIMENSIONS = {'n': None, 'm': None, 'p': None}

    def __init__(self, simulation_id: str):
        """Initialize the Nonlinear Control Lab simulator.

        Args:
            simulation_id: Unique identifier for this simulation instance.
        """
        super().__init__(simulation_id)
        self._error: Optional[str] = None
        self._roa_result: Optional[Dict[str, Any]] = None
        # Cached computation results
        self._A: Optional[np.ndarray] = None
        self._B: Optional[np.ndarray] = None
        self._K: Optional[np.ndarray] = None
        self._x_eq: Optional[np.ndarray] = None
        self._u_eq: Optional[np.ndarray] = None
        self._f_numeric: Optional[callable] = None
        self._f_vector: Optional['sp.Matrix'] = None
        self._x_syms: List = []
        self._u_syms: List = []
        self._n_states: int = 4
        self._n_inputs: int = 1
        self._is_controllable: bool = False
        self._ctrl_rank: int = 0
        self._ol_eigenvalues: List[complex] = []
        self._cl_eigenvalues: List[complex] = []
        self._state_names: List[str] = []
        self._input_names: List[str] = []
        self._design_error: str = ""
        self._cached_plant_key: Optional[tuple] = None
        self._eq_warning: Optional[str] = None

    def initialize(self, params: Optional[Dict[str, Any]] = None) -> None:
        """Initialize with given or default parameters.

        Args:
            params: Optional parameter overrides.
        """
        self.parameters = {**self.DEFAULT_PARAMS, **(params or {})}
        for name, value in self.parameters.items():
            self.parameters[name] = self._validate_param(name, value)
        self._roa_result = None
        self._error = None
        self._cached_plant_key = None
        self._eq_warning = None
        self._initialized = True

    def update_parameter(self, name: str, value: Any) -> Dict[str, Any]:
        """Update a single parameter and return updated state.

        Args:
            name: Parameter name.
            value: New value.

        Returns:
            Updated state dict.
        """
        if name in self.parameters:
            self.parameters[name] = self._validate_param(name, value)
        # Clear ROA cache on parameter change (except when just
        # toggling visualization options)
        if name not in ("show_linear", "show_vector_field",
                        "show_streamlines", "projection_x", "projection_y"):
            self._roa_result = None
        return self.get_state()

    # ================================================================ #
    #  Core computation pipeline                                       #
    # ================================================================ #

    def _build_plant(self) -> Tuple[bool, str]:
        """Build the plant model from current parameters.

        Sets self._f_vector, self._f_numeric, self._x_syms, self._u_syms,
        self._n_states, self._n_inputs, self._x_eq, self._u_eq, self._state_names,
        self._input_names.

        Returns:
            (success, error_message).
        """
        if not _HAS_SYMPY:
            return False, "SymPy not available"

        preset = str(self.parameters["plant_preset"])
        presets = _get_preset_plants()

        if preset == "custom":
            return self._build_custom_plant()

        if preset not in presets:
            return False, f"Unknown preset: {preset}"

        pdef = presets[preset]
        self._n_states = pdef["n_states"]
        self._n_inputs = pdef["n_inputs"]
        self._state_names = pdef["state_names"]
        self._input_names = pdef["input_names"]

        # Build symbolic dynamics
        try:
            self._x_syms, self._u_syms, _, self._f_vector = \
                _build_symbolic_dynamics(preset, pdef["params"])
        except Exception as exc:
            return False, f"Symbolic dynamics error: {exc}"

        # Select equilibrium
        eq_idx = int(self.parameters.get("equilibrium_idx", "0"))
        eq_idx = min(eq_idx, len(pdef["equilibria"]) - 1)
        eq = pdef["equilibria"][eq_idx]
        self._x_eq = np.array(eq["x_eq"], dtype=float)
        self._u_eq = np.array(eq["u_eq"], dtype=float)

        # Build numeric callable via lambdify
        try:
            all_syms = list(self._x_syms) + list(self._u_syms)
            # Use numpy with safe sqrt for negative values
            numpy_mod = [{"sqrt": lambda x: np.sqrt(np.maximum(x, 0.0))},
                         "numpy"]
            f_lamb = sp_lambdify(all_syms, self._f_vector, modules=numpy_mod)

            def f_numeric(x: np.ndarray, u: np.ndarray) -> np.ndarray:
                args = list(x) + list(u.flatten())
                result = np.array(f_lamb(*args), dtype=float).flatten()
                return result

            self._f_numeric = f_numeric
        except Exception as exc:
            return False, f"Lambdify error: {exc}"

        return True, ""

    def _build_custom_plant(self) -> Tuple[bool, str]:
        """Build plant from user-entered custom ODE expressions.

        Returns:
            (success, error_message).
        """
        n_states = int(self.parameters.get("n_states_custom", "2"))
        n_inputs = int(self.parameters.get("n_inputs_custom", "1"))
        self._n_states = n_states
        self._n_inputs = n_inputs

        # Collect expressions
        f_exprs = []
        for i in range(n_states):
            expr = str(self.parameters.get(f"f{i+1}_expr", "0"))
            f_exprs.append(expr)

        # State/input names for custom
        self._state_names = [f"x{i+1}" for i in range(n_states)]
        self._input_names = [f"u{i+1}" for i in range(n_inputs)]

        # Build symbolic
        x_syms, u_syms, f_vector, err = _build_custom_symbolic(
            f_exprs, n_states, n_inputs
        )
        if err:
            return False, err

        self._x_syms = x_syms
        self._u_syms = u_syms
        self._f_vector = f_vector

        # Equilibrium from sliders
        self._x_eq = np.array(
            [float(self.parameters.get(f"eq_x{i+1}", 0.0))
             for i in range(n_states)],
            dtype=float
        )
        self._u_eq = np.array(
            [float(self.parameters.get(f"eq_u{i+1}", 0.0))
             for i in range(n_inputs)],
            dtype=float
        )

        # Build numeric callable
        try:
            all_syms = list(x_syms) + list(u_syms)
            f_lamb = sp_lambdify(all_syms, f_vector, modules="numpy")

            def f_numeric(x: np.ndarray, u: np.ndarray) -> np.ndarray:
                args = list(x) + list(u.flatten())
                result = np.array(f_lamb(*args), dtype=float).flatten()
                return result

            self._f_numeric = f_numeric
        except Exception as exc:
            return False, f"Lambdify error: {exc}"

        # Verify equilibrium: f(x_eq, u_eq) should be near zero
        try:
            f_at_eq = self._f_numeric(self._x_eq, self._u_eq)
            eq_residual = float(np.linalg.norm(f_at_eq))
            if eq_residual > 0.01:
                self._eq_warning = (
                    f"f(x*, u*) has norm {eq_residual:.4f} "
                    f"— may not be a true equilibrium"
                )
            else:
                self._eq_warning = None
        except Exception:
            self._eq_warning = None

        return True, ""

    def _linearize(self) -> Tuple[bool, str]:
        """Perform Jacobian linearization at current equilibrium.

        Sets self._A, self._B, self._is_controllable, self._ctrl_rank,
        self._ol_eigenvalues.

        Returns:
            (success, error_message).
        """
        try:
            self._A, self._B = _compute_jacobians(
                self._f_vector, self._x_syms, self._u_syms,
                self._x_eq.tolist(), self._u_eq.tolist()
            )
        except Exception as exc:
            return False, f"Jacobian computation failed: {exc}"

        # Ensure B is 2D
        if self._B.ndim == 1:
            self._B = self._B.reshape(-1, 1)

        # Check controllability
        self._is_controllable, self._ctrl_rank = _check_controllability(
            self._A, self._B
        )

        # Open-loop eigenvalues
        try:
            self._ol_eigenvalues = list(np.linalg.eigvals(self._A))
        except Exception:
            self._ol_eigenvalues = []

        return True, ""

    def _design_controller(self) -> Tuple[bool, str]:
        """Design controller based on current method selection.

        Sets self._K, self._cl_eigenvalues, self._design_error.

        Returns:
            (success, error_message).
        """
        method = str(self.parameters["controller_method"])
        n = self._n_states
        m = self._n_inputs

        if not self._is_controllable:
            self._design_error = "System not controllable — cannot design controller"
            # Still try — might work for stabilizable systems
            # but warn the user

        if method == "lqr":
            # Build Q and R from parameters
            q_vals = [float(self.parameters.get(f"lqr_q{i+1}", 1.0))
                      for i in range(n)]
            Q = np.diag(q_vals)

            r_vals = [float(self.parameters.get(f"lqr_r{i+1}", 1.0))
                      for i in range(m)]
            R = np.diag(r_vals)

            K, P, err = _design_lqr(self._A, self._B, Q, R)
            if K is None:
                self._K = np.zeros((m, n))
                self._design_error = err
                self._cl_eigenvalues = list(self._ol_eigenvalues)
                return False, err
            self._K = K
            self._design_error = ""

        elif method == "pole_placement":
            # Build desired poles from parameters
            desired = []
            for i in range(n):
                re_val = float(self.parameters.get(f"pole_real_{i+1}", -(i+2)))
                im_val = float(self.parameters.get(f"pole_imag_{i+1}", 0.0))
                if abs(im_val) > 1e-10:
                    desired.append(complex(re_val, im_val))
                else:
                    desired.append(complex(re_val, 0))

            desired_arr = _ensure_conjugate_pairs(desired, n)
            K, err = _design_pole_placement(self._A, self._B, desired_arr)
            if K is None:
                self._K = np.zeros((m, n))
                self._design_error = err
                self._cl_eigenvalues = list(self._ol_eigenvalues)
                return False, err
            self._K = K
            self._design_error = ""

        else:
            self._K = np.zeros((m, n))
            self._design_error = f"Unknown method: {method}"
            return False, self._design_error

        # Ensure K is 2D
        if self._K.ndim == 1:
            self._K = self._K.reshape(1, -1)

        # CL eigenvalues
        try:
            A_cl = self._A - self._B @ self._K
            self._cl_eigenvalues = list(np.linalg.eigvals(A_cl))
        except Exception:
            self._cl_eigenvalues = []

        return True, ""

    def _run_simulations(self) -> Dict[str, Any]:
        """Run both linear and nonlinear simulations.

        Returns:
            Dict with time series data for both simulations.
        """
        t_end = float(self.parameters.get("sim_time", 10.0))
        n = self._n_states

        # Initial condition: equilibrium + offsets
        ic_offsets = np.array(
            [float(self.parameters.get(f"ic_offset_{i+1}", 0.0))
             for i in range(n)],
            dtype=float
        )
        x0 = self._x_eq + ic_offsets

        result = {
            "t": [], "x_nonlinear": [], "u_nonlinear": [],
            "x_linear": [], "u_linear": [],
            "diverged": False,
        }

        # Nonlinear simulation
        try:
            t_nl, x_nl, u_nl, diverged = _simulate_nonlinear(
                self._f_numeric, self._K, self._x_eq, self._u_eq,
                x0, (0, t_end), n_points=500
            )
            result["t"] = t_nl.tolist()
            result["x_nonlinear"] = x_nl.tolist()
            result["u_nonlinear"] = u_nl.tolist()
            result["diverged"] = diverged
        except Exception as exc:
            t_arr = np.linspace(0, t_end, 500)
            result["t"] = t_arr.tolist()
            result["x_nonlinear"] = np.tile(
                self._x_eq, (500, 1)).tolist()
            result["u_nonlinear"] = np.tile(
                self._u_eq, (500, 1)).tolist()
            result["diverged"] = True

        # Linear simulation
        if self.parameters.get("show_linear", True):
            try:
                t_lin, x_lin, u_lin = _simulate_linear(
                    self._A, self._B, self._K, self._x_eq, self._u_eq,
                    x0, (0, t_end), n_points=500
                )
                result["x_linear"] = x_lin.tolist()
                result["u_linear"] = u_lin.tolist()
            except Exception:
                result["x_linear"] = np.tile(
                    self._x_eq, (500, 1)).tolist()
                result["u_linear"] = np.tile(
                    self._u_eq, (500, 1)).tolist()

        return result

    def _compute_performance_metrics(self,
                                     sim_data: Dict[str, Any]
                                     ) -> Dict[str, Any]:
        """Compute performance metrics from simulation results.

        Args:
            sim_data: Dict from _run_simulations().

        Returns:
            Dict with convergence_time, max_deviation, final_error, is_stable.
        """
        t = np.array(sim_data["t"])
        x_nl = np.array(sim_data["x_nonlinear"])

        if len(t) == 0 or len(x_nl) == 0:
            return {
                "convergence_time": -1,
                "max_deviation": 0.0,
                "final_error": 0.0,
                "is_stable": False,
            }

        # Error from equilibrium over time
        errors = np.linalg.norm(x_nl - self._x_eq, axis=1)

        # Max deviation
        max_dev = float(np.max(errors)) if len(errors) > 0 else 0.0

        # Final error
        final_err = float(errors[-1]) if len(errors) > 0 else 0.0

        # Convergence time (first time error stays below threshold)
        threshold = 0.05 * max_dev if max_dev > 1e-6 else 0.01
        conv_time = float("inf")
        for i in range(len(errors) - 1, -1, -1):
            if errors[i] > threshold:
                if i < len(t) - 1:
                    conv_time = float(t[i + 1])
                break
        else:
            conv_time = 0.0

        # Stability: CL eigenvalues all in LHP
        is_stable = all(
            e.real < 0 for e in self._cl_eigenvalues
        ) if self._cl_eigenvalues else False

        return {
            "convergence_time": conv_time if not np.isinf(conv_time) else -1,
            "max_deviation": max_dev,
            "final_error": final_err,
            "is_stable": is_stable,
        }

    def _compute_all(self) -> Tuple[Dict[str, Any],
                                     List[Dict[str, Any]]]:
        """Run the full pipeline: build → linearize → design → simulate.

        Returns:
            (metadata, plots) tuple.
        """
        self._error = None

        # Cache key for plant-affecting parameters — skip expensive SymPy
        # rebuild when only controller weights or sim settings changed
        plant_key = (
            self.parameters.get("plant_preset"),
            self.parameters.get("equilibrium_idx"),
            self.parameters.get("n_states_custom"),
            self.parameters.get("n_inputs_custom"),
            self.parameters.get("f1_expr"),
            self.parameters.get("f2_expr"),
            self.parameters.get("f3_expr"),
            self.parameters.get("f4_expr"),
            self.parameters.get("eq_x1"),
            self.parameters.get("eq_x2"),
            self.parameters.get("eq_x3"),
            self.parameters.get("eq_x4"),
            self.parameters.get("eq_u1"),
            self.parameters.get("eq_u2"),
        )

        if plant_key != self._cached_plant_key:
            # Step 1: Build plant
            ok, err = self._build_plant()
            if not ok:
                return self._error_state(err)

            # Step 2: Linearize
            ok, err = self._linearize()
            if not ok:
                return self._error_state(err)

            self._cached_plant_key = plant_key

        # Step 3: Design controller
        ok, err = self._design_controller()
        # Continue even on design failure — show OL system

        # Step 4: Simulate
        sim_data = self._run_simulations()

        # Step 5: Performance metrics
        perf = self._compute_performance_metrics(sim_data)

        # Step 6: Vector field and streamlines
        proj_x = int(self.parameters.get("projection_x", "0"))
        proj_y = int(self.parameters.get("projection_y", "2"))
        # Clamp projection indices to valid range
        proj_x = min(proj_x, self._n_states - 1)
        proj_y = min(proj_y, self._n_states - 1)
        if proj_x == proj_y:
            proj_y = (proj_x + 1) % self._n_states

        vf_data = None
        if self.parameters.get("show_vector_field", True):
            try:
                vf_data = _compute_vector_field(
                    self._f_numeric, self._K, self._x_eq, self._u_eq,
                    self._n_states, proj_x, proj_y
                )
            except Exception:
                pass

        sl_data = None
        if self.parameters.get("show_streamlines", True):
            try:
                sl_data = _compute_streamlines(
                    self._f_numeric, self._K, self._x_eq, self._u_eq,
                    self._n_states, proj_x, proj_y
                )
            except Exception:
                pass

        # Step 7: Build plots
        plots = self._build_plots(sim_data, proj_x, proj_y)

        # Step 8: Build metadata
        metadata = self._build_metadata(
            sim_data, perf, vf_data, sl_data, proj_x, proj_y
        )

        return metadata, plots

    def _error_state(self, error_msg: str) -> Tuple[Dict[str, Any],
                                                      List[Dict[str, Any]]]:
        """Return a minimal state when an error occurs.

        Args:
            error_msg: Description of the error.

        Returns:
            (metadata, plots) with error information.
        """
        self._error = error_msg
        metadata = {
            "simulation_type": "nonlinear_control_lab",
            "hub_slots": self.HUB_SLOTS,
            "hub_domain": self.HUB_DOMAIN,
            "hub_dimensions": self.HUB_DIMENSIONS,
            "has_custom_viewer": True,
            "error": error_msg,
            "n_states": self._n_states,
            "n_inputs": self._n_inputs,
            "is_controllable": False,
            "is_stable": False,
        }
        # Empty plots
        plots = [
            self._empty_plot("time_response", "Time Response (Error)"),
            self._empty_plot("control_effort", "Control Effort (Error)"),
            self._empty_plot("eigenvalue_map", "Eigenvalue Map (Error)"),
        ]
        return metadata, plots

    def _empty_plot(self, plot_id: str, title: str) -> Dict[str, Any]:
        """Generate an empty plot placeholder.

        Args:
            plot_id: Unique plot identifier.
            title: Plot title.

        Returns:
            Plotly plot dict.
        """
        return {
            "id": plot_id,
            "title": title,
            "data": [],
            "layout": self._base_layout(title),
        }

    # ================================================================ #
    #  Plot builders                                                   #
    # ================================================================ #

    def _base_layout(self, title: str, **kwargs: Any) -> Dict[str, Any]:
        """Standard Plotly layout.

        Args:
            title: Plot title.
            **kwargs: Additional layout overrides.

        Returns:
            Plotly layout dict.
        """
        layout = {
            "title": {"text": title, "font": {"size": 14}},
            "paper_bgcolor": "#0a0e27",
            "plot_bgcolor": "#131b2e",
            "font": {"family": "Inter, sans-serif", "size": 12,
                      "color": "#f1f5f9"},
            "xaxis": {
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
            },
            "yaxis": {
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
            },
            "margin": {"t": 45, "r": 25, "b": 55, "l": 60},
            "showlegend": True,
            "legend": {"font": {"size": 10}},
        }
        layout.update(kwargs)
        return layout

    def _build_plots(self,
                     sim_data: Dict[str, Any],
                     proj_x: int,
                     proj_y: int
                     ) -> List[Dict[str, Any]]:
        """Build all Plotly plots.

        Args:
            sim_data: Simulation results dict.
            proj_x: x-axis projection state index.
            proj_y: y-axis projection state index.

        Returns:
            List of Plotly plot dicts.
        """
        plots = [
            self._build_time_response_plot(sim_data),
            self._build_control_effort_plot(sim_data),
            self._build_eigenvalue_plot(),
        ]

        # ROA heatmap only when computed
        if self._roa_result is not None:
            plots.append(self._build_roa_plot(proj_x, proj_y))

        return plots

    def _build_time_response_plot(self,
                                   sim_data: Dict[str, Any]
                                   ) -> Dict[str, Any]:
        """Build time response plot with all state traces.

        Nonlinear = solid lines, Linear = dashed lines.

        Args:
            sim_data: Simulation data dict.

        Returns:
            Plotly plot dict.
        """
        t = sim_data.get("t", [])
        x_nl = sim_data.get("x_nonlinear", [])
        x_lin = sim_data.get("x_linear", [])

        colors = ["#3b82f6", "#ef4444", "#10b981", "#f59e0b",
                   "#8b5cf6", "#ec4899"]
        traces = []

        # State names for legend
        names = self._state_names if self._state_names else \
            [f"x{i+1}" for i in range(self._n_states)]

        # Nonlinear traces (solid)
        if len(x_nl) > 0:
            x_nl_arr = np.array(x_nl)
            for i in range(min(self._n_states, x_nl_arr.shape[1])):
                traces.append({
                    "x": t,
                    "y": x_nl_arr[:, i].tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "name": f"{names[i]} (NL)",
                    "line": {"color": colors[i % len(colors)], "width": 2},
                })

        # Linear traces (dashed)
        show_linear = self.parameters.get("show_linear", True)
        if show_linear and len(x_lin) > 0:
            x_lin_arr = np.array(x_lin)
            for i in range(min(self._n_states, x_lin_arr.shape[1])):
                traces.append({
                    "x": t,
                    "y": x_lin_arr[:, i].tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "name": f"{names[i]} (Lin)",
                    "line": {"color": colors[i % len(colors)], "width": 1.5,
                             "dash": "dash"},
                })

        # Equilibrium reference lines
        if self._x_eq is not None and len(t) > 0:
            for i in range(self._n_states):
                traces.append({
                    "x": [t[0], t[-1]],
                    "y": [float(self._x_eq[i]), float(self._x_eq[i])],
                    "type": "scatter",
                    "mode": "lines",
                    "name": f"x*{i+1}",
                    "line": {"color": colors[i % len(colors)], "width": 1,
                             "dash": "dot"},
                    "showlegend": False,
                })

        layout = self._base_layout("Time Response")
        layout["xaxis"]["title"] = "Time (s)"
        layout["yaxis"]["title"] = "State value"
        layout["datarevision"] = f"time_resp-{time.time()}"
        layout["uirevision"] = "time_response"

        return {
            "id": "time_response",
            "title": "Time Response",
            "data": traces,
            "layout": layout,
        }

    def _build_control_effort_plot(self,
                                    sim_data: Dict[str, Any]
                                    ) -> Dict[str, Any]:
        """Build control effort u(t) plot.

        Args:
            sim_data: Simulation data dict.

        Returns:
            Plotly plot dict.
        """
        t = sim_data.get("t", [])
        u_nl = sim_data.get("u_nonlinear", [])
        u_lin = sim_data.get("u_linear", [])

        colors = ["#14b8a6", "#f59e0b", "#8b5cf6"]
        traces = []
        u_names = self._input_names if self._input_names else \
            [f"u{i+1}" for i in range(self._n_inputs)]

        if len(u_nl) > 0:
            u_nl_arr = np.array(u_nl)
            if u_nl_arr.ndim == 1:
                u_nl_arr = u_nl_arr.reshape(-1, 1)
            for i in range(min(self._n_inputs, u_nl_arr.shape[1])):
                traces.append({
                    "x": t,
                    "y": u_nl_arr[:, i].tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "name": f"{u_names[i]} (NL)",
                    "line": {"color": colors[i % len(colors)], "width": 2},
                })

        show_linear = self.parameters.get("show_linear", True)
        if show_linear and len(u_lin) > 0:
            u_lin_arr = np.array(u_lin)
            if u_lin_arr.ndim == 1:
                u_lin_arr = u_lin_arr.reshape(-1, 1)
            for i in range(min(self._n_inputs, u_lin_arr.shape[1])):
                traces.append({
                    "x": t,
                    "y": u_lin_arr[:, i].tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "name": f"{u_names[i]} (Lin)",
                    "line": {"color": colors[i % len(colors)], "width": 1.5,
                             "dash": "dash"},
                })

        layout = self._base_layout("Control Effort")
        layout["xaxis"]["title"] = "Time (s)"
        layout["yaxis"]["title"] = "Control input"
        layout["datarevision"] = f"ctrl_effort-{time.time()}"
        layout["uirevision"] = "control_effort"

        return {
            "id": "control_effort",
            "title": "Control Effort",
            "data": traces,
            "layout": layout,
        }

    def _build_eigenvalue_plot(self) -> Dict[str, Any]:
        """Build eigenvalue map showing OL and CL poles on complex plane.

        Returns:
            Plotly plot dict.
        """
        traces = []

        # Open-loop eigenvalues
        if self._ol_eigenvalues:
            ol_re = [float(e.real) for e in self._ol_eigenvalues]
            ol_im = [float(e.imag) for e in self._ol_eigenvalues]
            traces.append({
                "x": ol_re,
                "y": ol_im,
                "type": "scatter",
                "mode": "markers",
                "name": "OL poles",
                "marker": {"color": "#ef4444", "size": 12,
                            "symbol": "x", "line": {"width": 2}},
            })

        # Closed-loop eigenvalues
        if self._cl_eigenvalues:
            cl_re = [float(e.real) for e in self._cl_eigenvalues]
            cl_im = [float(e.imag) for e in self._cl_eigenvalues]
            traces.append({
                "x": cl_re,
                "y": cl_im,
                "type": "scatter",
                "mode": "markers",
                "name": "CL poles",
                "marker": {"color": "#10b981", "size": 12,
                            "symbol": "circle", "line": {"width": 2,
                                                          "color": "#10b981"}},
            })

        # Imaginary axis (stability boundary)
        if self._ol_eigenvalues or self._cl_eigenvalues:
            all_im = ([float(abs(e.imag)) for e in self._ol_eigenvalues] +
                      [float(abs(e.imag)) for e in self._cl_eigenvalues])
            max_im = float(max(max(all_im) * 1.3, 1.0)) if all_im else 5.0
            traces.append({
                "x": [0, 0],
                "y": [-max_im, max_im],
                "type": "scatter",
                "mode": "lines",
                "name": "jω axis",
                "line": {"color": "rgba(148,163,184,0.5)", "width": 1,
                          "dash": "dash"},
                "showlegend": False,
            })

        # LHP shading
        if self._ol_eigenvalues or self._cl_eigenvalues:
            all_re = ([float(e.real) for e in self._ol_eigenvalues] +
                      [float(e.real) for e in self._cl_eigenvalues])
            min_re = float(min(min(all_re) * 1.3, -1.0)) if all_re else -10.0
            traces.append({
                "x": [min_re, 0, 0, min_re],
                "y": [-max_im, -max_im, max_im, max_im],
                "type": "scatter",
                "fill": "toself",
                "fillcolor": "rgba(16,185,129,0.05)",
                "line": {"color": "rgba(0,0,0,0)"},
                "name": "Stable region",
                "showlegend": False,
            })

        layout = self._base_layout("Eigenvalue Map")
        layout["xaxis"]["title"] = "Real"
        layout["yaxis"]["title"] = "Imaginary"

        # Compute equal-span ranges server-side instead of scaleanchor (BUG-007)
        if self._ol_eigenvalues or self._cl_eigenvalues:
            all_re = ([float(e.real) for e in self._ol_eigenvalues] +
                      [float(e.real) for e in self._cl_eigenvalues])
            all_im = ([float(e.imag) for e in self._ol_eigenvalues] +
                      [float(e.imag) for e in self._cl_eigenvalues])
            x_min, x_max = min(all_re), max(all_re)
            y_min, y_max = min(all_im), max(all_im)
            x_span = x_max - x_min
            y_span = y_max - y_min
            max_span = max(x_span, y_span, 1.0)
            x_center = (x_max + x_min) / 2
            y_center = (y_max + y_min) / 2
            layout["xaxis"]["range"] = [x_center - max_span / 2 - 0.5,
                                         x_center + max_span / 2 + 0.5]
            layout["yaxis"]["range"] = [y_center - max_span / 2 - 0.5,
                                         y_center + max_span / 2 + 0.5]

        layout["datarevision"] = f"eig-{time.time()}"
        layout["uirevision"] = "eigenvalue_map"

        return {
            "id": "eigenvalue_map",
            "title": "Eigenvalue Map",
            "data": traces,
            "layout": layout,
        }

    def _build_roa_plot(self, proj_x: int, proj_y: int) -> Dict[str, Any]:
        """Build Region of Attraction heatmap.

        Args:
            proj_x: x-axis state index.
            proj_y: y-axis state index.

        Returns:
            Plotly plot dict.
        """
        roa = self._roa_result
        if roa is None:
            return self._empty_plot("roa_heatmap",
                                    "Region of Attraction (not computed)")

        x_names = self._state_names if self._state_names else \
            [f"x{i+1}" for i in range(self._n_states)]

        # Color scale: 0=converged (green), 1=diverged (red), 2=marginal (yellow)
        result_arr = np.array(roa["result"], dtype=float)
        # Map: converged=1.0, marginal=0.5, diverged=0.0
        display = np.where(result_arr == 0, 1.0,
                           np.where(result_arr == 2, 0.5, 0.0))

        traces = [{
            "x": roa["x_vals"],
            "y": roa["y_vals"],
            "z": display.tolist(),
            "type": "heatmap",
            "colorscale": [
                [0.0, "#ef4444"],    # diverged
                [0.5, "#f59e0b"],    # marginal
                [1.0, "#10b981"],    # converged
            ],
            "showscale": True,
            "colorbar": {
                "title": "Convergence",
                "tickvals": [0, 0.5, 1],
                "ticktext": ["Diverged", "Marginal", "Converged"],
            },
        }]

        # Mark equilibrium
        traces.append({
            "x": [float(self._x_eq[proj_x])],
            "y": [float(self._x_eq[proj_y])],
            "type": "scatter",
            "mode": "markers",
            "name": "Equilibrium",
            "marker": {"color": "#ffffff", "size": 10,
                        "symbol": "star", "line": {"width": 1,
                                                    "color": "#000000"}},
        })

        layout = self._base_layout("Region of Attraction")
        layout["xaxis"]["title"] = x_names[proj_x] if proj_x < len(x_names) else f"x{proj_x+1}"
        layout["yaxis"]["title"] = x_names[proj_y] if proj_y < len(x_names) else f"x{proj_y+1}"
        layout["datarevision"] = f"roa-{time.time()}"
        layout["uirevision"] = "roa_heatmap"

        return {
            "id": "roa_heatmap",
            "title": "Region of Attraction",
            "data": traces,
            "layout": layout,
        }

    # ================================================================ #
    #  Metadata builder                                                #
    # ================================================================ #

    def _build_metadata(self,
                        sim_data: Dict[str, Any],
                        perf: Dict[str, Any],
                        vf_data: Optional[Dict[str, Any]],
                        sl_data: Optional[List[Dict[str, List]]],
                        proj_x: int,
                        proj_y: int
                        ) -> Dict[str, Any]:
        """Build rich metadata for the frontend viewer.

        Args:
            sim_data: Simulation results.
            perf: Performance metrics dict.
            vf_data: Vector field data (or None).
            sl_data: Streamline data (or None).
            proj_x: x-axis projection index.
            proj_y: y-axis projection index.

        Returns:
            Metadata dict for get_state().
        """
        n = self._n_states
        m = self._n_inputs
        preset = str(self.parameters["plant_preset"])

        # State and input names
        x_names = self._state_names if self._state_names else \
            [f"x{i+1}" for i in range(n)]
        u_names = self._input_names if self._input_names else \
            [f"u{i+1}" for i in range(m)]

        # LaTeX strings
        A_latex = _matrix_to_latex(self._A, "A") if self._A is not None else ""
        B_latex = _matrix_to_latex(self._B, "B") if self._B is not None else ""
        K_latex = _matrix_to_latex(self._K, "K") if self._K is not None else ""
        ode_latex = _ode_to_latex(self._f_vector, self._x_syms, self._u_syms) \
            if self._f_vector is not None else ""

        # Equilibrium options for the current preset
        presets = _get_preset_plants()
        eq_options = []
        if preset in presets:
            for i, eq in enumerate(presets[preset]["equilibria"]):
                eq_options.append({"value": str(i), "label": eq["label"]})
        elif preset == "custom":
            eq_options.append({"value": "0", "label": "Custom equilibrium"})

        # Eigenvalue formatting
        def fmt_eig(e: complex) -> str:
            if abs(e.imag) < 1e-10:
                return f"{e.real:.4g}"
            return f"{e.real:.4g} {'+' if e.imag >= 0 else '-'} {abs(e.imag):.4g}j"

        ol_eig_strs = [fmt_eig(e) for e in self._ol_eigenvalues]
        cl_eig_strs = [fmt_eig(e) for e in self._cl_eigenvalues]

        # Trajectory data for canvas rendering
        trajectory_data = {
            "t": sim_data.get("t", []),
            "x_nonlinear": sim_data.get("x_nonlinear", []),
            "x_linear": sim_data.get("x_linear", []),
        }

        # Plant description
        if preset in presets:
            plant_desc = presets[preset]["description"]
        elif preset == "custom":
            plant_desc = f"Custom ODE ({n} states, {m} inputs)"
        else:
            plant_desc = ""

        metadata = {
            "simulation_type": "nonlinear_control_lab",
            "hub_slots": self.HUB_SLOTS,
            "hub_domain": self.HUB_DOMAIN,
            "hub_dimensions": self.HUB_DIMENSIONS,
            "has_custom_viewer": True,
            "error": self._error or self._design_error or None,

            # Plant info
            "plant_preset": preset,
            "plant_description": plant_desc,
            "n_states": n,
            "n_inputs": m,
            "state_names": x_names,
            "input_names": u_names,

            # Equilibrium
            "x_eq": self._x_eq.tolist() if self._x_eq is not None else [],
            "u_eq": self._u_eq.tolist() if self._u_eq is not None else [],
            "equilibrium_options": eq_options,

            # Linearization
            "A_matrix": self._A.tolist() if self._A is not None else [],
            "B_matrix": self._B.tolist() if self._B is not None else [],
            "A_latex": A_latex,
            "B_latex": B_latex,
            "ode_latex": ode_latex,
            "is_controllable": self._is_controllable,
            "controllability_rank": self._ctrl_rank,

            # Controller
            "controller_method": str(self.parameters["controller_method"]),
            "K_matrix": self._K.tolist() if self._K is not None else [],
            "K_latex": K_latex,
            "design_error": self._design_error,

            # Eigenvalues
            "ol_eigenvalues": [
                {"real": float(e.real), "imag": float(e.imag)}
                for e in self._ol_eigenvalues
            ],
            "cl_eigenvalues": [
                {"real": float(e.real), "imag": float(e.imag)}
                for e in self._cl_eigenvalues
            ],
            "ol_eigenvalue_strings": ol_eig_strs,
            "cl_eigenvalue_strings": cl_eig_strs,
            "is_stable": perf.get("is_stable", False),

            # Performance
            "performance": perf,

            # Projections
            "projection_x": proj_x,
            "projection_y": proj_y,

            # Visualization data for canvas
            "vector_field": vf_data,
            "streamlines": sl_data,
            "trajectory_data": trajectory_data,

            # ROA
            "roa_result": self._roa_result,
            "has_roa": self._roa_result is not None,

            # Simulation status
            "diverged": sim_data.get("diverged", False),

            # Equilibrium validation warning (custom ODEs)
            "eq_warning": self._eq_warning,
        }

        return metadata

    # ================================================================ #
    #  Public interface                                                #
    # ================================================================ #

    def get_plots(self) -> List[Dict[str, Any]]:
        """Generate and return current plots.

        Returns:
            List of Plotly plot dicts.
        """
        if not self._initialized:
            self.initialize()
        _, plots = self._compute_all()
        return plots

    def get_state(self) -> Dict[str, Any]:
        """Return full simulation state with plots and metadata.

        Returns:
            Dict with parameters, plots, and metadata.
        """
        if not self._initialized:
            self.initialize()

        metadata, plots = self._compute_all()

        return {
            "parameters": self.parameters.copy(),
            "plots": plots,
            "metadata": metadata,
        }

    def handle_action(self, action: str,
                      params: Optional[Dict[str, Any]] = None
                      ) -> Dict[str, Any]:
        """Handle execute endpoint actions.

        Supported actions: init, update, run, reset, compute_roa.

        Args:
            action: Action name string.
            params: Optional parameters for the action.

        Returns:
            Updated state dict.
        """
        if action == "init":
            self.initialize(params)
        elif action == "update" and params:
            for name, value in params.items():
                if name in self.parameters:
                    self.parameters[name] = self._validate_param(name, value)
            self._roa_result = None
        elif action == "run":
            if params:
                for name, value in params.items():
                    if name in self.parameters:
                        self.parameters[name] = self._validate_param(
                            name, value)
        elif action == "reset":
            self.initialize()
        elif action == "compute_roa":
            # Explicit ROA computation — expensive, not on every update
            self._compute_roa_action()
        return self.get_state()

    def _compute_roa_action(self) -> None:
        """Execute the ROA computation.

        Builds plant and controller if needed, then runs the grid-based
        ROA analysis.
        """
        # Ensure plant and controller are built
        ok, err = self._build_plant()
        if not ok:
            self._error = err
            return

        ok, err = self._linearize()
        if not ok:
            self._error = err
            return

        ok, err = self._design_controller()
        if not ok:
            # Still try ROA with whatever K we have
            pass

        proj_x = int(self.parameters.get("projection_x", "0"))
        proj_y = int(self.parameters.get("projection_y", "2"))
        proj_x = min(proj_x, self._n_states - 1)
        proj_y = min(proj_y, self._n_states - 1)
        if proj_x == proj_y:
            proj_y = (proj_x + 1) % self._n_states

        t_end = float(self.parameters.get("sim_time", 10.0))

        try:
            self._roa_result = _compute_roa(
                self._f_numeric, self._K, self._x_eq, self._u_eq,
                self._n_states, proj_x, proj_y,
                grid_size=25, extent=3.0, t_end=t_end
            )
        except Exception as exc:
            self._error = f"ROA computation failed: {exc}"
            self._roa_result = None
