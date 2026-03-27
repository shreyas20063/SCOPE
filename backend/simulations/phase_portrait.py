"""
Nonlinear Phase Portrait Analyzer

Interactive exploration of 2D autonomous nonlinear dynamical systems.
Users enter ẋ₁ = f(x₁,x₂) and ẋ₂ = g(x₁,x₂), then explore the phase
portrait through vector fields, trajectories (click-to-place ICs), and
equilibrium analysis with Jacobian classification.

Core theory (Khalil Ch 2-4, Strogatz Ch 5-8):
- Phase portrait = union of all trajectories in state space
- Equilibria: f(x*)=0, g(x*)=0  →  classification via Jacobian eigenvalues
- Hartman-Grobman theorem: near hyperbolic eq., nonlinear ≈ linearized
- Classification: node, spiral, saddle, center (from 2×2 eigenvalue structure)
"""

import math
import re
import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from scipy.integrate import solve_ivp
from scipy.optimize import fsolve
from .base_simulator import BaseSimulator


# ------------------------------------------------------------------ #
#  Safe expression evaluator for 2D state-space dynamics              #
# ------------------------------------------------------------------ #

_SAFE_NAMESPACE = {
    "np": np,
    "sin": np.sin,
    "cos": np.cos,
    "tan": np.tan,
    "exp": np.exp,
    "log": np.log,
    "log10": np.log10,
    "sqrt": np.sqrt,
    "abs": np.abs,
    "sign": np.sign,
    "pi": np.pi,
    "e": np.e,
    "tanh": np.tanh,
    "sinh": np.sinh,
    "cosh": np.cosh,
    "arctan": np.arctan,
    "arctan2": np.arctan2,
    "power": np.power,
    "maximum": np.maximum,
    "minimum": np.minimum,
    "__builtins__": {},
}

_DANGEROUS_PATTERNS = [
    "import", "exec", "eval", "__", "open", "file",
    "os.", "sys.", "subprocess", "compile", "globals",
    "locals", "getattr", "setattr", "delattr", "lambda",
    "class", "def ", "yield", "async", "await",
]


def _validate_expr(expr: str) -> Tuple[bool, str]:
    """Validate expression for security."""
    if not expr or not expr.strip():
        return False, "Expression cannot be empty"
    expr_lower = expr.lower()
    for pat in _DANGEROUS_PATTERNS:
        if pat in expr_lower:
            return False, f"Unsafe pattern: '{pat}'"
    if expr.count("(") != expr.count(")"):
        return False, "Unbalanced parentheses"
    return True, ""


def _parse_expr(expr: str) -> str:
    """Convert user-friendly math to numpy-compatible string."""
    parsed = expr.strip()
    parsed = parsed.replace("^", "**")
    # numpy function prefixing
    for fn in ("sin", "cos", "tan", "exp", "log", "log10", "sqrt",
               "abs", "sign", "tanh", "sinh", "cosh", "arctan"):
        parsed = re.sub(rf"(?<!np\.)\b{fn}\s*\(", f"np.{fn}(", parsed)
    parsed = re.sub(r"(?<!np\.)\bpi\b", "np.pi", parsed)
    # Don't replace standalone 'e' if it's part of variable names
    parsed = re.sub(r"(?<!np\.)\be\b(?![xp0-9\w])", "np.e", parsed)
    return parsed


def _make_func(expr_str: str):
    """
    Create a callable f(x1, x2) from expression string.
    Uses restricted namespace with __builtins__={} — same security
    model as signal_parser.py (already in codebase).
    Returns (func, error_string). func is None on failure.
    """
    ok, err = _validate_expr(expr_str)
    if not ok:
        return None, err
    parsed = _parse_expr(expr_str)
    try:
        code = f"lambda x1, x2: {parsed}"
        fn = eval(code, _SAFE_NAMESPACE.copy())  # noqa: S307 — sandboxed, no builtins
        # Quick test
        test_val = fn(np.array([0.0, 1.0]), np.array([0.0, 1.0]))
        if test_val is None:
            return None, "Expression returned None"
        return fn, ""
    except SyntaxError as exc:
        return None, f"Syntax error: {exc}"
    except NameError as exc:
        return None, f"Unknown name: {exc}"
    except Exception as exc:
        return None, f"Error: {exc}"


# ------------------------------------------------------------------ #
#  Equilibrium classification                                         #
# ------------------------------------------------------------------ #

def _classify_equilibrium(jacobian: np.ndarray) -> Dict[str, Any]:
    """
    Classify a 2D equilibrium from its Jacobian matrix.

    Returns dict with:
        type: str  (stable_node, unstable_node, saddle, stable_spiral,
                    unstable_spiral, center, degenerate)
        eigenvalues: list of complex
        eigenvectors: list of arrays
        trace: float
        determinant: float
    """
    eigvals, eigvecs = np.linalg.eig(jacobian)
    tr = np.trace(jacobian)
    det = np.linalg.det(jacobian)

    re_parts = np.real(eigvals)
    im_parts = np.imag(eigvals)
    is_complex = np.any(np.abs(im_parts) > 1e-8)

    if abs(det) < 1e-10:
        eq_type = "degenerate"
    elif is_complex:
        avg_re = np.mean(re_parts)
        if avg_re < -1e-8:
            eq_type = "stable_spiral"
        elif avg_re > 1e-8:
            eq_type = "unstable_spiral"
        else:
            eq_type = "center"
    else:
        if re_parts[0] * re_parts[1] < 0:
            eq_type = "saddle"
        elif re_parts[0] < -1e-8 and re_parts[1] < -1e-8:
            eq_type = "stable_node"
        elif re_parts[0] > 1e-8 and re_parts[1] > 1e-8:
            eq_type = "unstable_node"
        else:
            eq_type = "degenerate"

    return {
        "type": eq_type,
        "eigenvalues": [complex(e) for e in eigvals],
        "eigenvectors": [np.real(eigvecs[:, i]).tolist() for i in range(2)],
        "trace": float(tr),
        "determinant": float(det),
    }


# ------------------------------------------------------------------ #
#  Preset definitions                                                 #
# ------------------------------------------------------------------ #

_PRESETS = {
    "simple_pendulum": {
        "label": "Simple Pendulum (damped)",
        "f_expr": "x2",
        "g_expr": "-sin(x1) - 0.5*x2",
        "x_range": [-8, 8],
        "y_range": [-4, 4],
    },
    "van_der_pol": {
        "label": "Van der Pol Oscillator",
        "f_expr": "x2",
        "g_expr": "mu*(1 - x1**2)*x2 - x1",
        "x_range": [-5, 5],
        "y_range": [-5, 5],
    },
    "lotka_volterra": {
        "label": "Lotka-Volterra (Predator-Prey)",
        "f_expr": "alpha*x1 - beta*x1*x2",
        "g_expr": "delta*x1*x2 - gamma*x2",
        "x_range": [0, 6],
        "y_range": [0, 6],
    },
    "duffing": {
        "label": "Duffing Oscillator (unforced)",
        "f_expr": "x2",
        "g_expr": "x1 - x1**3 - delta*x2",
        "x_range": [-3, 3],
        "y_range": [-3, 3],
    },
    "limit_cycle": {
        "label": "Limit Cycle",
        "f_expr": "x2 + x1*(1 - x1**2 - x2**2)",
        "g_expr": "-x1 + x2*(1 - x1**2 - x2**2)",
        "x_range": [-3, 3],
        "y_range": [-3, 3],
    },
}


# ------------------------------------------------------------------ #
#  Simulator                                                          #
# ------------------------------------------------------------------ #

class PhasePortraitSimulator(BaseSimulator):
    """Nonlinear Phase Portrait Analyzer."""

    PARAMETER_SCHEMA = {
        "preset": {
            "type": "select",
            "options": [
                {"value": "simple_pendulum", "label": "Simple Pendulum (damped)"},
                {"value": "van_der_pol", "label": "Van der Pol Oscillator"},
                {"value": "lotka_volterra", "label": "Lotka-Volterra"},
                {"value": "duffing", "label": "Duffing (unforced)"},
                {"value": "limit_cycle", "label": "Limit Cycle"},
                {"value": "custom", "label": "Custom Equations"},
            ],
            "default": "simple_pendulum",
        },
        "f_expr": {"type": "expression", "default": "x2"},
        "g_expr": {"type": "expression", "default": "-sin(x1) - 0.5*x2"},
        # Preset-specific sliders
        "mu": {
            "type": "slider", "min": 0.0, "max": 5.0,
            "step": 0.1, "default": 1.0,
            "visible_when": {"preset": "van_der_pol"},
        },
        "alpha": {
            "type": "slider", "min": 0.1, "max": 3.0,
            "step": 0.1, "default": 1.0,
            "visible_when": {"preset": "lotka_volterra"},
        },
        "beta": {
            "type": "slider", "min": 0.1, "max": 2.0,
            "step": 0.1, "default": 0.5,
            "visible_when": {"preset": "lotka_volterra"},
        },
        "gamma": {
            "type": "slider", "min": 0.1, "max": 2.0,
            "step": 0.1, "default": 0.5,
            "visible_when": {"preset": "lotka_volterra"},
        },
        "delta_lv": {
            "type": "slider", "min": 0.1, "max": 2.0,
            "step": 0.1, "default": 0.2,
            "visible_when": {"preset": "lotka_volterra"},
        },
        "delta_duffing": {
            "type": "slider", "min": 0.0, "max": 2.0,
            "step": 0.05, "default": 0.3,
            "visible_when": {"preset": "duffing"},
        },
        # View controls
        "x_min": {"type": "slider", "min": -20, "max": 0, "step": 0.5, "default": -8},
        "x_max": {"type": "slider", "min": 0, "max": 20, "step": 0.5, "default": 8},
        "y_min": {"type": "slider", "min": -20, "max": 0, "step": 0.5, "default": -4},
        "y_max": {"type": "slider", "min": 0, "max": 20, "step": 0.5, "default": 4},
        "grid_density": {
            "type": "slider", "min": 10, "max": 30,
            "step": 1, "default": 20,
        },
        "trajectory_time": {
            "type": "slider", "min": 5, "max": 60,
            "step": 1, "default": 20,
        },
    }

    DEFAULT_PARAMS: Dict[str, Any] = {
        "preset": "simple_pendulum",
        "f_expr": "x2",
        "g_expr": "-sin(x1) - 0.5*x2",
        "mu": 1.0,
        "alpha": 1.0, "beta": 0.5, "gamma": 0.5, "delta_lv": 0.2,
        "delta_duffing": 0.3,
        "x_min": -8, "x_max": 8,
        "y_min": -4, "y_max": 4,
        "grid_density": 20,
        "trajectory_time": 20,
    }

    HUB_SLOTS = ["control"]

    # ------------------------------------------------------------------ #
    #  Lifecycle                                                          #
    # ------------------------------------------------------------------ #
    def initialize(self, params: Optional[Dict[str, Any]] = None) -> None:
        self.parameters = {**self.DEFAULT_PARAMS, **(params or {})}
        for name, value in self.parameters.items():
            self.parameters[name] = self._validate_param(name, value)
        self._trajectories: List[Dict[str, Any]] = []
        self._equilibria: List[Dict[str, Any]] = []
        self._f_func = None
        self._g_func = None
        self._error: Optional[str] = None
        self._next_traj_id = 0
        self._apply_preset()
        self._compile_functions()
        self._find_equilibria()
        self._initialized = True

    def update_parameter(self, name: str, value: Any) -> Dict[str, Any]:
        if name in self.parameters:
            self.parameters[name] = self._validate_param(name, value)

            if name == "preset" and value != "custom":
                self._apply_preset()
                self._trajectories.clear()
                self._next_traj_id = 0

            needs_recompile = name in (
                "f_expr", "g_expr", "preset",
                "mu", "alpha", "beta", "gamma", "delta_lv", "delta_duffing",
            )
            if needs_recompile:
                self._compile_functions()
                self._find_equilibria()
                self._reintegrate_trajectories()
            else:
                needs_eq_update = name in ("x_min", "x_max", "y_min", "y_max", "grid_density")
                if needs_eq_update:
                    self._find_equilibria()
                    self._reintegrate_trajectories()

        return self.get_state()

    # ------------------------------------------------------------------ #
    #  Custom actions: add/remove trajectories                            #
    # ------------------------------------------------------------------ #
    def handle_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle custom actions for trajectory management."""
        if action == "add_trajectory":
            x0 = float(params.get("x1", 0.0))
            y0 = float(params.get("x2", 0.0))
            traj = self._integrate_trajectory(x0, y0)
            if traj is not None:
                self._trajectories.append(traj)
            return self.get_state()

        elif action == "remove_trajectory":
            traj_id = params.get("trajectory_id")
            if traj_id is not None:
                self._trajectories = [
                    t for t in self._trajectories if t["id"] != traj_id
                ]
            return self.get_state()

        elif action == "clear_trajectories":
            self._trajectories.clear()
            self._next_traj_id = 0
            return self.get_state()

        return self.get_state()

    # ------------------------------------------------------------------ #
    #  Preset application                                                 #
    # ------------------------------------------------------------------ #
    def _apply_preset(self) -> None:
        preset_key = self.parameters.get("preset", "simple_pendulum")
        if preset_key == "custom":
            return
        preset = _PRESETS.get(preset_key)
        if not preset:
            return
        self.parameters["f_expr"] = preset["f_expr"]
        self.parameters["g_expr"] = preset["g_expr"]
        self.parameters["x_min"] = preset["x_range"][0]
        self.parameters["x_max"] = preset["x_range"][1]
        self.parameters["y_min"] = preset["y_range"][0]
        self.parameters["y_max"] = preset["y_range"][1]

    # ------------------------------------------------------------------ #
    #  Expression compilation                                             #
    # ------------------------------------------------------------------ #
    def _compile_functions(self) -> None:
        """Build the dynamics callables, substituting preset parameters."""
        self._error = None
        f_raw = self.parameters["f_expr"]
        g_raw = self.parameters["g_expr"]

        f_sub = self._substitute_params(f_raw)
        g_sub = self._substitute_params(g_raw)

        f_fn, f_err = _make_func(f_sub)
        if f_fn is None:
            self._error = f"dx1/dt error: {f_err}"
            self._f_func = lambda x1, x2: np.zeros_like(x1)
            self._g_func = lambda x1, x2: np.zeros_like(x1)
            return
        g_fn, g_err = _make_func(g_sub)
        if g_fn is None:
            self._error = f"dx2/dt error: {g_err}"
            self._f_func = lambda x1, x2: np.zeros_like(x1)
            self._g_func = lambda x1, x2: np.zeros_like(x1)
            return
        self._f_func = f_fn
        self._g_func = g_fn

    def _substitute_params(self, expr: str) -> str:
        """Replace named parameters (mu, alpha, etc.) with numeric values."""
        if self.parameters.get("preset") == "custom":
            return expr
        result = expr
        param_map = {
            "mu": self.parameters.get("mu", 1.0),
            "alpha": self.parameters.get("alpha", 1.0),
            "beta": self.parameters.get("beta", 0.5),
            "gamma": self.parameters.get("gamma", 0.5),
            "delta": self._get_delta_value(),
        }
        for name, val in param_map.items():
            result = re.sub(rf"\b{name}\b", str(float(val)), result)
        return result

    def _get_delta_value(self) -> float:
        """Get the delta parameter for current preset."""
        preset = self.parameters.get("preset")
        if preset == "lotka_volterra":
            return self.parameters.get("delta_lv", 0.2)
        elif preset == "duffing":
            return self.parameters.get("delta_duffing", 0.3)
        return 0.0

    # ------------------------------------------------------------------ #
    #  Dynamics ODE                                                       #
    # ------------------------------------------------------------------ #
    def _dynamics(self, t: float, state: np.ndarray) -> np.ndarray:
        """ODE right-hand side: [dx1, dx2] = [f(x1,x2), g(x1,x2)]."""
        x1, x2 = state
        try:
            dx1 = float(self._f_func(x1, x2))
            dx2 = float(self._g_func(x1, x2))
        except Exception:
            dx1, dx2 = 0.0, 0.0
        if math.isnan(dx1) or math.isinf(dx1):
            dx1 = 0.0
        if math.isnan(dx2) or math.isinf(dx2):
            dx2 = 0.0
        clamp = 1e6
        dx1 = max(-clamp, min(clamp, dx1))
        dx2 = max(-clamp, min(clamp, dx2))
        return np.array([dx1, dx2])

    # ------------------------------------------------------------------ #
    #  Vector field computation                                           #
    # ------------------------------------------------------------------ #
    def _compute_vector_field(self) -> Dict[str, Any]:
        """Compute quiver data on a grid."""
        n = int(self.parameters["grid_density"])
        x_min, x_max = self.parameters["x_min"], self.parameters["x_max"]
        y_min, y_max = self.parameters["y_min"], self.parameters["y_max"]

        x = np.linspace(x_min, x_max, n)
        y = np.linspace(y_min, y_max, n)
        X, Y = np.meshgrid(x, y)

        try:
            U = self._f_func(X, Y)
            V = self._g_func(X, Y)
            if isinstance(U, (int, float)):
                U = np.full_like(X, U)
            if isinstance(V, (int, float)):
                V = np.full_like(X, V)
        except Exception:
            U = np.zeros_like(X)
            V = np.zeros_like(X)

        U = np.where(np.isfinite(U), U, 0.0)
        V = np.where(np.isfinite(V), V, 0.0)

        mag = np.sqrt(U**2 + V**2)
        max_mag = np.max(mag)
        if max_mag > 1e-12:
            safe_mag = np.where(mag > 1e-12, mag, 1.0)
            scale = np.log1p(mag) / np.log1p(max_mag)
            U_norm = np.where(mag > 1e-12, U / safe_mag * scale, 0.0)
            V_norm = np.where(mag > 1e-12, V / safe_mag * scale, 0.0)
        else:
            U_norm = U
            V_norm = V

        return {
            "x": X.flatten().tolist(),
            "y": Y.flatten().tolist(),
            "u": U_norm.flatten().tolist(),
            "v": V_norm.flatten().tolist(),
            "magnitude": mag.flatten().tolist(),
        }

    # ------------------------------------------------------------------ #
    #  Trajectory integration                                             #
    # ------------------------------------------------------------------ #
    def _integrate_trajectory(self, x0: float, y0: float) -> Optional[Dict[str, Any]]:
        """Integrate a trajectory from initial condition (x0, y0)."""
        t_max = float(self.parameters["trajectory_time"])

        # Forward integration
        try:
            sol_fwd = solve_ivp(
                self._dynamics, [0, t_max], [x0, y0],
                method="RK45", max_step=0.05,
                dense_output=False, rtol=1e-8, atol=1e-10,
            )
            if not sol_fwd.success:
                # Retry with stiff-capable solver
                sol_fwd = solve_ivp(
                    self._dynamics, [0, t_max], [x0, y0],
                    method="LSODA", max_step=0.05,
                    dense_output=False, rtol=1e-6, atol=1e-8,
                )
            if sol_fwd.success:
                x1_fwd = sol_fwd.y[0].tolist()
                x2_fwd = sol_fwd.y[1].tolist()
                t_fwd = sol_fwd.t.tolist()
            else:
                x1_fwd, x2_fwd, t_fwd = [x0], [y0], [0.0]
        except Exception:
            x1_fwd, x2_fwd, t_fwd = [x0], [y0], [0.0]

        # Backward integration (reverse time)
        try:
            sol_bwd = solve_ivp(
                self._dynamics, [0, -t_max], [x0, y0],
                method="RK45", max_step=0.05,
                dense_output=False, rtol=1e-8, atol=1e-10,
            )
            if not sol_bwd.success:
                # Retry with stiff-capable solver
                sol_bwd = solve_ivp(
                    self._dynamics, [0, -t_max], [x0, y0],
                    method="LSODA", max_step=0.05,
                    dense_output=False, rtol=1e-6, atol=1e-8,
                )
            if sol_bwd.success and len(sol_bwd.t) > 1:
                x1_bwd = sol_bwd.y[0][1:][::-1].tolist()
                x2_bwd = sol_bwd.y[1][1:][::-1].tolist()
                t_bwd = sol_bwd.t[1:][::-1].tolist()
            else:
                x1_bwd, x2_bwd, t_bwd = [], [], []
        except Exception:
            x1_bwd, x2_bwd, t_bwd = [], [], []

        x1_full = x1_bwd + x1_fwd
        x2_full = x2_bwd + x2_fwd
        t_full = t_bwd + t_fwd

        # Subsample if too many points
        max_pts = 800
        if len(x1_full) > max_pts:
            indices = np.linspace(0, len(x1_full) - 1, max_pts, dtype=int)
            x1_full = [x1_full[i] for i in indices]
            x2_full = [x2_full[i] for i in indices]
            t_full = [t_full[i] for i in indices]

        traj_id = self._next_traj_id
        self._next_traj_id += 1

        return {
            "id": traj_id,
            "x0": x0,
            "y0": y0,
            "x1": x1_full,
            "x2": x2_full,
            "t": t_full,
        }

    def _reintegrate_trajectories(self) -> None:
        """Re-integrate all trajectories with current dynamics."""
        old_trajs = self._trajectories[:]
        self._trajectories.clear()
        for t in old_trajs:
            new_traj = self._integrate_trajectory(t["x0"], t["y0"])
            if new_traj is not None:
                new_traj["id"] = t["id"]
                self._trajectories.append(new_traj)

    # ------------------------------------------------------------------ #
    #  Equilibrium finding                                                #
    # ------------------------------------------------------------------ #
    def _find_equilibria(self) -> None:
        """Find and classify equilibria via grid-based fsolve."""
        self._equilibria = []
        x_min, x_max = self.parameters["x_min"], self.parameters["x_max"]
        y_min, y_max = self.parameters["y_min"], self.parameters["y_max"]

        def system(state):
            x1, x2 = state
            try:
                return [
                    float(self._f_func(x1, x2)),
                    float(self._g_func(x1, x2)),
                ]
            except Exception:
                return [1e10, 1e10]

        x_range = x_max - x_min
        y_range = y_max - y_min
        n_guess = max(8, min(20, int(2 * max(x_range, y_range))))
        dedup_tol = 0.01 * max(x_range, y_range, 0.1)
        x_guesses = np.linspace(x_min, x_max, n_guess)
        y_guesses = np.linspace(y_min, y_max, n_guess)
        found_points: List[np.ndarray] = []

        for xg in x_guesses:
            for yg in y_guesses:
                try:
                    sol, info, ier, _ = fsolve(
                        system, [xg, yg], full_output=True
                    )
                    if ier == 1:
                        residual = np.linalg.norm(info["fvec"])
                        if residual < 1e-6:
                            margin = 0.5
                            if (x_min - margin <= sol[0] <= x_max + margin and
                                    y_min - margin <= sol[1] <= y_max + margin):
                                is_dup = any(
                                    np.linalg.norm(sol - fp) < dedup_tol
                                    for fp in found_points
                                )
                                if not is_dup:
                                    found_points.append(sol.copy())
                except Exception:
                    continue

        for pt in found_points:
            jac = self._compute_jacobian(pt[0], pt[1])
            classification = _classify_equilibrium(jac)
            self._equilibria.append({
                "x1": float(pt[0]),
                "x2": float(pt[1]),
                "jacobian": jac.tolist(),
                **classification,
            })

    def _compute_jacobian(self, x1: float, x2: float) -> np.ndarray:
        """Compute 2x2 Jacobian via central finite differences."""
        h = 1e-6
        try:
            df_dx1 = (float(self._f_func(x1 + h, x2)) - float(self._f_func(x1 - h, x2))) / (2 * h)
            df_dx2 = (float(self._f_func(x1, x2 + h)) - float(self._f_func(x1, x2 - h))) / (2 * h)
            dg_dx1 = (float(self._g_func(x1 + h, x2)) - float(self._g_func(x1 - h, x2))) / (2 * h)
            dg_dx2 = (float(self._g_func(x1, x2 + h)) - float(self._g_func(x1, x2 - h))) / (2 * h)
        except Exception:
            return np.zeros((2, 2))

        jac = np.array([[df_dx1, df_dx2], [dg_dx1, dg_dx2]])
        jac = np.where(np.isfinite(jac), jac, 0.0)
        return jac

    # ------------------------------------------------------------------ #
    #  Plot building                                                      #
    # ------------------------------------------------------------------ #
    def get_plots(self) -> List[Dict[str, Any]]:
        return [self._build_phase_portrait(), self._build_time_series()]

    def _build_phase_portrait(self) -> Dict[str, Any]:
        """Main phase plane: vector field + trajectories + equilibria."""
        vf = self._compute_vector_field()
        traces = []

        # --- Vector field as line-segment arrows ---
        n_pts = len(vf["x"])
        x_range = self.parameters["x_max"] - self.parameters["x_min"]
        y_range = self.parameters["y_max"] - self.parameters["y_min"]
        n_grid = int(self.parameters["grid_density"])
        arrow_scale_x = x_range / n_grid * 0.4
        arrow_scale_y = y_range / n_grid * 0.4

        arrow_x = []
        arrow_y = []
        for i in range(n_pts):
            x0 = vf["x"][i]
            y0 = vf["y"][i]
            dx = vf["u"][i] * arrow_scale_x
            dy = vf["v"][i] * arrow_scale_y
            arrow_x.extend([x0, x0 + dx, None])
            arrow_y.extend([y0, y0 + dy, None])

        traces.append({
            "x": arrow_x,
            "y": arrow_y,
            "mode": "lines",
            "line": {"color": "rgba(148, 163, 184, 0.35)", "width": 1},
            "hoverinfo": "skip",
            "showlegend": False,
        })

        # Arrow heads (dots at tips, colored by magnitude)
        head_x, head_y, head_mag = [], [], []
        for i in range(n_pts):
            if vf["magnitude"][i] < 1e-12:
                continue
            head_x.append(vf["x"][i] + vf["u"][i] * arrow_scale_x)
            head_y.append(vf["y"][i] + vf["v"][i] * arrow_scale_y)
            head_mag.append(vf["magnitude"][i])

        if head_x:
            traces.append({
                "x": head_x,
                "y": head_y,
                "mode": "markers",
                "marker": {
                    "size": 3,
                    "color": head_mag,
                    "colorscale": [
                        [0, "rgba(100, 116, 139, 0.4)"],
                        [0.5, "rgba(59, 130, 246, 0.6)"],
                        [1, "rgba(20, 184, 166, 0.9)"],
                    ],
                    "showscale": False,
                },
                "hoverinfo": "skip",
                "showlegend": False,
            })

        # --- Trajectories ---
        traj_colors = [
            "#3b82f6", "#ef4444", "#10b981", "#f59e0b",
            "#8b5cf6", "#ec4899", "#06b6d4", "#f97316",
            "#84cc16", "#6366f1",
        ]
        for i, traj in enumerate(self._trajectories):
            color = traj_colors[i % len(traj_colors)]
            traces.append({
                "x": traj["x1"],
                "y": traj["x2"],
                "mode": "lines",
                "line": {"color": color, "width": 2},
                "name": f"IC ({traj['x0']:.1f}, {traj['y0']:.1f})",
                "hovertemplate": "x\u2081=%{x:.3f}<br>x\u2082=%{y:.3f}<extra></extra>",
            })
            # IC marker
            traces.append({
                "x": [traj["x0"]],
                "y": [traj["y0"]],
                "mode": "markers",
                "marker": {"size": 8, "color": color, "symbol": "circle",
                           "line": {"color": "#fff", "width": 1.5}},
                "showlegend": False,
                "hovertemplate": f"IC: ({traj['x0']:.2f}, {traj['y0']:.2f})<extra></extra>",
            })
            # Direction arrow at trajectory midpoint
            n_traj = len(traj["x1"])
            if n_traj > 10:
                mid = n_traj // 2
                if mid > 0 and mid < len(traj["x1"]) - 1:
                    dx = traj["x1"][mid + 1] - traj["x1"][mid - 1]
                    dy = traj["x2"][mid + 1] - traj["x2"][mid - 1]
                    if abs(dx) >= abs(dy):
                        arrow_symbol = "triangle-right" if dx >= 0 else "triangle-left"
                    else:
                        arrow_symbol = "triangle-up" if dy >= 0 else "triangle-down"
                else:
                    arrow_symbol = "triangle-right"
                traces.append({
                    "x": [traj["x1"][mid]],
                    "y": [traj["x2"][mid]],
                    "mode": "markers",
                    "marker": {"size": 6, "color": color, "symbol": arrow_symbol},
                    "showlegend": False,
                    "hoverinfo": "skip",
                })

        # --- Equilibria ---
        eq_colors = {
            "stable_node": "#10b981", "unstable_node": "#ef4444",
            "saddle": "#f59e0b", "stable_spiral": "#06b6d4",
            "unstable_spiral": "#f97316", "center": "#8b5cf6",
            "degenerate": "#64748b",
        }
        eq_symbols = {
            "stable_node": "circle", "unstable_node": "circle-open",
            "saddle": "x", "stable_spiral": "circle",
            "unstable_spiral": "circle-open", "center": "diamond",
            "degenerate": "square",
        }
        eq_labels = {
            "stable_node": "Stable Node", "unstable_node": "Unstable Node",
            "saddle": "Saddle", "stable_spiral": "Stable Spiral",
            "unstable_spiral": "Unstable Spiral", "center": "Center",
            "degenerate": "Degenerate",
        }

        eq_by_type: Dict[str, list] = {}
        for eq in self._equilibria:
            et = eq["type"]
            if et not in eq_by_type:
                eq_by_type[et] = []
            eq_by_type[et].append(eq)

        for et, eqs in eq_by_type.items():
            xs = [eq["x1"] for eq in eqs]
            ys = [eq["x2"] for eq in eqs]
            hovers = []
            for eq in eqs:
                ev_strs = []
                shown = set()
                for idx, ev in enumerate(eq["eigenvalues"]):
                    if idx in shown:
                        continue
                    if abs(ev.imag) < 1e-8:
                        ev_strs.append(f"{ev.real:.4f}")
                    else:
                        ev_strs.append(f"{ev.real:.4f} + {abs(ev.imag):.4f}j")
                        ev_strs.append(f"{ev.real:.4f} \u2212 {abs(ev.imag):.4f}j")
                        # Skip the conjugate
                        for j in range(idx + 1, len(eq["eigenvalues"])):
                            if abs(eq["eigenvalues"][j].real - ev.real) < 1e-8 and abs(eq["eigenvalues"][j].imag + ev.imag) < 1e-8:
                                shown.add(j)
                                break
                hovers.append(
                    f"({eq['x1']:.3f}, {eq['x2']:.3f})<br>"
                    f"{eq_labels[et]}<br>"
                    f"\u03bb: {', '.join(ev_strs)}<br>"
                    f"tr={eq['trace']:.4f}, det={eq['determinant']:.4f}"
                )
            traces.append({
                "x": xs, "y": ys,
                "mode": "markers",
                "marker": {
                    "size": 12,
                    "color": eq_colors.get(et, "#64748b"),
                    "symbol": eq_symbols.get(et, "circle"),
                    "line": {"color": "#fff", "width": 2},
                },
                "name": eq_labels.get(et, et),
                "hovertemplate": "%{customdata}<extra></extra>",
                "customdata": hovers,
            })

        layout = {
            "xaxis": {
                "title": {"text": "x\u2081", "font": {"size": 14}},
                "range": [self.parameters["x_min"], self.parameters["x_max"]],
                "gridcolor": "rgba(148, 163, 184, 0.1)",
                "zerolinecolor": "rgba(148, 163, 184, 0.3)",
                "zerolinewidth": 1.5,
            },
            "yaxis": {
                "title": {"text": "x\u2082", "font": {"size": 14}},
                "range": [self.parameters["y_min"], self.parameters["y_max"]],
                "gridcolor": "rgba(148, 163, 184, 0.1)",
                "zerolinecolor": "rgba(148, 163, 184, 0.3)",
                "zerolinewidth": 1.5,
            },
            "margin": {"t": 45, "r": 25, "b": 55, "l": 60},
            "legend": {
                "x": 1.0, "y": 1.0, "xanchor": "right",
                "bgcolor": "rgba(0, 0, 0, 0)",
                "font": {"size": 11},
            },
            "hovermode": "closest",
        }

        return {
            "id": "phase_portrait",
            "title": "Phase Portrait",
            "data": traces,
            "layout": layout,
        }

    def _build_time_series(self) -> Dict[str, Any]:
        """Time-domain plot for the most recent trajectory."""
        traces = []
        if self._trajectories:
            traj = self._trajectories[-1]
            traces.append({
                "x": traj["t"], "y": traj["x1"],
                "mode": "lines",
                "line": {"color": "#3b82f6", "width": 2},
                "name": "x\u2081(t)",
            })
            traces.append({
                "x": traj["t"], "y": traj["x2"],
                "mode": "lines",
                "line": {"color": "#ef4444", "width": 2},
                "name": "x\u2082(t)",
            })

        layout = {
            "xaxis": {
                "title": {"text": "Time (s)", "font": {"size": 13}},
                "gridcolor": "rgba(148, 163, 184, 0.1)",
                "zerolinecolor": "rgba(148, 163, 184, 0.3)",
            },
            "yaxis": {
                "title": {"text": "State", "font": {"size": 13}},
                "gridcolor": "rgba(148, 163, 184, 0.1)",
                "zerolinecolor": "rgba(148, 163, 184, 0.3)",
            },
            "margin": {"t": 45, "r": 25, "b": 55, "l": 60},
            "legend": {
                "x": 1.0, "y": 1.0, "xanchor": "right",
                "bgcolor": "rgba(0, 0, 0, 0)",
                "font": {"size": 11},
            },
        }

        return {
            "id": "time_series",
            "title": "Time Response (Latest Trajectory)",
            "data": traces,
            "layout": layout,
        }

    # ------------------------------------------------------------------ #
    #  State                                                              #
    # ------------------------------------------------------------------ #
    def get_state(self) -> Dict[str, Any]:
        preset = self.parameters.get("preset", "simple_pendulum")
        preset_info = _PRESETS.get(preset, {})

        return {
            "parameters": self.parameters.copy(),
            "plots": self.get_plots(),
            "metadata": {
                "simulation_type": "phase_portrait",
                "hub_slots": self.HUB_SLOTS,
                "hub_domain": self.HUB_DOMAIN,
                "hub_dimensions": self.HUB_DIMENSIONS,
                "error": self._error,
                "equilibria": [
                    {
                        "x1": eq["x1"],
                        "x2": eq["x2"],
                        "type": eq["type"],
                        "eigenvalues": [
                            {"real": e.real, "imag": e.imag}
                            for e in eq["eigenvalues"]
                        ],
                        "eigenvectors": eq["eigenvectors"],
                        "trace": eq["trace"],
                        "determinant": eq["determinant"],
                        "jacobian": eq["jacobian"],
                    }
                    for eq in self._equilibria
                ],
                "trajectories": [
                    {"id": t["id"], "x0": t["x0"], "y0": t["y0"]}
                    for t in self._trajectories
                ],
                "preset_label": preset_info.get("label", "Custom"),
                "f_expr": self.parameters["f_expr"],
                "g_expr": self.parameters["g_expr"],
            },
        }
