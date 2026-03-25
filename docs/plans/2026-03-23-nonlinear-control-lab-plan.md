# Nonlinear Control Lab Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the Linearize → Design → Validate on Nonlinear Plant simulation — the CDC paper's flagship interactive tool.

**Architecture:** Backend simulator (~1400 lines) with SymPy-based Jacobian linearization, LQR/pole placement controller design, solve_ivp nonlinear validation, and ThreadPoolExecutor ROA computation. Frontend custom viewer (~700 lines) with HTML5 Canvas phase portrait, Plotly comparison plots, and KaTeX derivation chain. CSS (~400 lines).

**Tech Stack:** Python (NumPy, SciPy, SymPy), React 18, HTML5 Canvas, Plotly.js, KaTeX

**Design doc:** `docs/plans/2026-03-23-nonlinear-control-lab-design.md`

---

## Task 1: Backend — Plant Definitions & Expression Engine

**Files:**
- Create: `backend/simulations/nonlinear_control_lab.py`

**Context:** The existing `phase_portrait.py` (903 lines) has a safe expression evaluator for 2D systems. The new sim needs a more general engine: n-dimensional state, m inputs, SymPy symbolic representation for exact Jacobians.

**Step 1: Create the simulator skeleton with plant preset definitions**

```python
"""
Nonlinear Control Lab

Linearize nonlinear plants at equilibria, design controllers (LQR/pole placement)
on the linearization, validate on the true nonlinear dynamics via solve_ivp,
and visualize the region of attraction.

Core theory:
- Linearization: ẋ = f(x,u) → δẋ = A δx + B δu where A = ∂f/∂x|eq, B = ∂f/∂u|eq
- LQR: minimize ∫(x'Qx + u'Ru)dt → K = R⁻¹B'P (Riccati)
- Pole placement: place_poles(A, B, desired) → K
- Validation: simulate u = -K(x - x_eq) on the TRUE nonlinear plant
"""

import re
import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from scipy.integrate import solve_ivp
from scipy.optimize import fsolve
from scipy.linalg import solve_continuous_are, expm
from scipy import signal
from concurrent.futures import ThreadPoolExecutor
from .base_simulator import BaseSimulator

try:
    import sympy as sp
    HAS_SYMPY = True
except ImportError:
    HAS_SYMPY = False


# ------------------------------------------------------------------ #
#  Plant Definitions                                                  #
# ------------------------------------------------------------------ #

class NonlinearPlant:
    """Represents a nonlinear plant with symbolic dynamics for exact Jacobians."""

    def __init__(self, name: str, n_states: int, n_inputs: int,
                 state_names: List[str], input_names: List[str],
                 f_symbolic, equilibria: List[Dict],
                 param_defaults: Optional[Dict] = None):
        self.name = name
        self.n_states = n_states
        self.n_inputs = n_inputs
        self.state_names = state_names
        self.input_names = input_names
        self.f_symbolic = f_symbolic  # callable(symbols) -> sympy Matrix
        self.equilibria = equilibria
        self.param_defaults = param_defaults or {}


def _build_plants() -> Dict[str, NonlinearPlant]:
    """Build all preset plant definitions with SymPy symbolic dynamics."""
    if not HAS_SYMPY:
        return {}

    plants = {}

    # --- Inverted Pendulum on Cart ---
    # States: [x, x_dot, theta, theta_dot]
    # Input: [F] (force on cart)
    # Standard nonlinear model (Ogata, Khalil)
    x, xd, th, thd = sp.symbols('x x_dot theta theta_dot')
    F = sp.Symbol('F')
    M_val, m_val, l_val, g_val = 1.0, 0.1, 0.5, 9.81
    M_s, m_s, l_s, g_s = sp.Rational(1), sp.Rational(1, 10), sp.Rational(1, 2), sp.Float(9.81)

    sin_th = sp.sin(th)
    cos_th = sp.cos(th)
    denom = l_s * (M_s + m_s * sin_th**2)

    f_pend = sp.Matrix([
        xd,
        (F + m_s * sin_th * (l_s * thd**2 + g_s * cos_th)) / (M_s + m_s * sin_th**2),
        thd,
        (-F * cos_th - m_s * l_s * thd**2 * sin_th * cos_th - (M_s + m_s) * g_s * sin_th) / denom,
    ])

    plants["inverted_pendulum"] = NonlinearPlant(
        name="Inverted Pendulum on Cart",
        n_states=4, n_inputs=1,
        state_names=["x (position)", "ẋ (velocity)", "θ (angle)", "θ̇ (angular vel)"],
        input_names=["F (force)"],
        f_symbolic=lambda: (sp.Matrix([x, xd, th, thd]), sp.Matrix([F]), f_pend),
        equilibria=[
            {"name": "Upright (θ = π)", "x_eq": [0, 0, np.pi, 0], "u_eq": [0],
             "description": "Unstable upright — requires active control"},
            {"name": "Hanging (θ = 0)", "x_eq": [0, 0, 0, 0], "u_eq": [0],
             "description": "Stable hanging — gravity does the work"},
        ],
        param_defaults={"M": M_val, "m": m_val, "l": l_val, "g": g_val},
    )

    # --- Ball and Beam ---
    # States: [r, r_dot, alpha, alpha_dot]
    # Input: [tau] (torque on beam)
    r, rd, alpha, alphad = sp.symbols('r r_dot alpha alpha_dot')
    tau = sp.Symbol('tau')
    J_b = sp.Float(0.05)  # beam moment of inertia
    m_b = sp.Float(0.1)   # ball mass
    g_bb = sp.Float(9.81)
    R_b = sp.Float(0.01)  # ball radius
    J_ball = sp.Rational(2, 5) * m_b * R_b**2

    f_bb = sp.Matrix([
        rd,
        r * alphad**2 - g_bb * sp.sin(alpha),
        alphad,
        (tau - 2 * m_b * r * rd * alphad - m_b * g_bb * r * sp.cos(alpha)) / (J_b + m_b * r**2),
    ])

    plants["ball_and_beam"] = NonlinearPlant(
        name="Ball and Beam",
        n_states=4, n_inputs=1,
        state_names=["r (ball pos)", "ṙ (ball vel)", "α (beam angle)", "α̇ (beam ang vel)"],
        input_names=["τ (torque)"],
        f_symbolic=lambda: (sp.Matrix([r, rd, alpha, alphad]), sp.Matrix([tau]), f_bb),
        equilibria=[
            {"name": "Ball at center, beam level", "x_eq": [0, 0, 0, 0], "u_eq": [0],
             "description": "Unstable — ball rolls off without control"},
        ],
    )

    # --- Coupled Tanks (MIMO) ---
    # States: [h1, h2]
    # Inputs: [q1, q2]
    h1, h2 = sp.symbols('h1 h2')
    q1, q2 = sp.symbols('q1 q2')
    A1_t, A2_t = sp.Float(1.0), sp.Float(1.0)
    a1_t, a2_t = sp.Float(0.2), sp.Float(0.2)

    f_tanks = sp.Matrix([
        (q1 - a1_t * sp.sqrt(sp.Abs(h1))) / A1_t,
        (q2 + a1_t * sp.sqrt(sp.Abs(h1)) - a2_t * sp.sqrt(sp.Abs(h2))) / A2_t,
    ])

    # Equilibrium: h1_eq = (q1_eq/a1)^2, h2_eq = ((q1_eq+q2_eq)/a2)^2
    q1_eq, q2_eq = 1.0, 0.5
    h1_eq = (q1_eq / 0.2)**2  # 25.0
    h2_eq = ((q1_eq + q2_eq) / 0.2)**2  # 56.25

    plants["coupled_tanks"] = NonlinearPlant(
        name="Coupled Tanks (MIMO)",
        n_states=2, n_inputs=2,
        state_names=["h₁ (tank 1 level)", "h₂ (tank 2 level)"],
        input_names=["q₁ (inflow 1)", "q₂ (inflow 2)"],
        f_symbolic=lambda: (sp.Matrix([h1, h2]), sp.Matrix([q1, q2]), f_tanks),
        equilibria=[
            {"name": f"Equal flow (h₁={h1_eq:.1f}, h₂={h2_eq:.1f})",
             "x_eq": [h1_eq, h2_eq], "u_eq": [q1_eq, q2_eq],
             "description": "Nonlinear √h coupling — MIMO LQR showcase"},
        ],
    )

    # --- Van der Pol with Input ---
    # States: [x1, x2]
    # Input: [u]
    x1_vdp, x2_vdp = sp.symbols('x1 x2')
    u_vdp = sp.Symbol('u')
    mu_vdp = sp.Float(1.0)

    f_vdp = sp.Matrix([
        x2_vdp,
        mu_vdp * (1 - x1_vdp**2) * x2_vdp - x1_vdp + u_vdp,
    ])

    plants["van_der_pol"] = NonlinearPlant(
        name="Van der Pol Oscillator + Input",
        n_states=2, n_inputs=1,
        state_names=["x₁", "x₂"],
        input_names=["u"],
        f_symbolic=lambda: (sp.Matrix([x1_vdp, x2_vdp]), sp.Matrix([u_vdp]), f_vdp),
        equilibria=[
            {"name": "Origin", "x_eq": [0, 0], "u_eq": [0],
             "description": "Unstable focus with limit cycle — linearization fails far from origin"},
        ],
    )

    return plants


PRESET_PLANTS = _build_plants()
```

**Step 2: Add the safe expression validator for custom ODEs**

Reuse the pattern from `phase_portrait.py` but extend to n-dimensional with input variables. Include `_SAFE_NAMESPACE`, `_DANGEROUS_PATTERNS`, `_validate_expr`, `_parse_expr` — same security patterns as `phase_portrait.py:28-80`.

**Step 3: Add PARAMETER_SCHEMA, DEFAULT_PARAMS, and the class skeleton**

```python
class NonlinearControlLabSimulator(BaseSimulator):
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
        "equilibrium_idx": {"type": "select", "default": "0", "options": []},
        "controller_method": {
            "type": "select", "default": "lqr",
            "options": [
                {"value": "lqr", "label": "LQR (Linear Quadratic Regulator)"},
                {"value": "pole_placement", "label": "Pole Placement"},
            ],
        },
        "projection_x": {"type": "select", "default": "0", "options": []},
        "projection_y": {"type": "select", "default": "2", "options": []},
        # LQR weights (log-scale, per-state Q diag)
        "lqr_q1": {"type": "slider", "min": 0.01, "max": 100, "step": 0.01, "default": 1.0},
        "lqr_q2": {"type": "slider", "min": 0.01, "max": 100, "step": 0.01, "default": 1.0},
        "lqr_q3": {"type": "slider", "min": 0.01, "max": 100, "step": 0.01, "default": 10.0},
        "lqr_q4": {"type": "slider", "min": 0.01, "max": 100, "step": 0.01, "default": 1.0},
        "lqr_r1": {"type": "slider", "min": 0.01, "max": 100, "step": 0.01, "default": 1.0},
        "lqr_r2": {"type": "slider", "min": 0.01, "max": 100, "step": 0.01, "default": 1.0},
        # Pole placement
        "pole_real_1": {"type": "slider", "min": -20, "max": 0, "step": 0.1, "default": -2.0},
        "pole_imag_1": {"type": "slider", "min": -10, "max": 10, "step": 0.1, "default": 0.0},
        "pole_real_2": {"type": "slider", "min": -20, "max": 0, "step": 0.1, "default": -2.0},
        "pole_imag_2": {"type": "slider", "min": -10, "max": 10, "step": 0.1, "default": 0.0},
        "pole_real_3": {"type": "slider", "min": -20, "max": 0, "step": 0.1, "default": -3.0},
        "pole_imag_3": {"type": "slider", "min": -10, "max": 10, "step": 0.1, "default": 0.0},
        "pole_real_4": {"type": "slider", "min": -20, "max": 0, "step": 0.1, "default": -3.0},
        "pole_imag_4": {"type": "slider", "min": -10, "max": 10, "step": 0.1, "default": 0.0},
        # Simulation
        "ic_offset_1": {"type": "slider", "min": -5, "max": 5, "step": 0.1, "default": 0.0},
        "ic_offset_2": {"type": "slider", "min": -5, "max": 5, "step": 0.1, "default": 0.1},
        "ic_offset_3": {"type": "slider", "min": -5, "max": 5, "step": 0.1, "default": 0.2},
        "ic_offset_4": {"type": "slider", "min": -5, "max": 5, "step": 0.1, "default": 0.0},
        "sim_time": {"type": "slider", "min": 1, "max": 30, "step": 0.5, "default": 10.0},
        # Display
        "show_linear": {"type": "checkbox", "default": True},
        "show_vector_field": {"type": "checkbox", "default": True},
        "show_streamlines": {"type": "checkbox", "default": True},
        # Custom ODE expressions (visible_when custom)
        "n_states_custom": {"type": "select", "default": "2", "options": [
            {"value": "2", "label": "2 states"},
            {"value": "3", "label": "3 states"},
            {"value": "4", "label": "4 states"},
        ]},
        "n_inputs_custom": {"type": "select", "default": "1", "options": [
            {"value": "1", "label": "1 input"},
            {"value": "2", "label": "2 inputs"},
        ]},
        "f1_expr": {"type": "expression", "default": "x2"},
        "f2_expr": {"type": "expression", "default": "-sin(x1) - 0.5*x2 + u1"},
        "f3_expr": {"type": "expression", "default": "x4"},
        "f4_expr": {"type": "expression", "default": "-x3 + u1"},
        "eq_x1": {"type": "slider", "min": -10, "max": 10, "step": 0.1, "default": 0.0},
        "eq_x2": {"type": "slider", "min": -10, "max": 10, "step": 0.1, "default": 0.0},
        "eq_x3": {"type": "slider", "min": -10, "max": 10, "step": 0.1, "default": 0.0},
        "eq_x4": {"type": "slider", "min": -10, "max": 10, "step": 0.1, "default": 0.0},
        "eq_u1": {"type": "slider", "min": -10, "max": 10, "step": 0.1, "default": 0.0},
        "eq_u2": {"type": "slider", "min": -10, "max": 10, "step": 0.1, "default": 0.0},
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
        "pole_real_2": -2.0, "pole_imag_2": 0.0,
        "pole_real_3": -3.0, "pole_imag_3": 0.0,
        "pole_real_4": -3.0, "pole_imag_4": 0.0,
        "ic_offset_1": 0.0, "ic_offset_2": 0.1,
        "ic_offset_3": 0.2, "ic_offset_4": 0.0,
        "sim_time": 10.0,
        "show_linear": True, "show_vector_field": True, "show_streamlines": True,
        "n_states_custom": "2", "n_inputs_custom": "1",
        "f1_expr": "x2", "f2_expr": "-sin(x1) - 0.5*x2 + u1",
        "f3_expr": "x4", "f4_expr": "-x3 + u1",
        "eq_x1": 0.0, "eq_x2": 0.0, "eq_x3": 0.0, "eq_x4": 0.0,
        "eq_u1": 0.0, "eq_u2": 0.0,
    }

    def initialize(self, params=None):
        self.parameters = {**self.DEFAULT_PARAMS, **(params or {})}
        for name, value in self.parameters.items():
            if name in self.PARAMETER_SCHEMA:
                self.parameters[name] = self._validate_param(name, value)
        self._initialized = True
        # Cache for expensive computations
        self._cached_plant_id = None
        self._cached_eq_idx = None
        self._A = None
        self._B = None
        self._K = None
        self._roa_result = None

    def update_parameter(self, name, value):
        if name in self.parameters:
            self.parameters[name] = self._validate_param(name, value)
        # Invalidate caches on plant/equilibrium change
        if name in ("plant_preset", "equilibrium_idx", "n_states_custom",
                     "n_inputs_custom") or name.startswith("f") and name.endswith("_expr"):
            self._cached_plant_id = None
            self._roa_result = None
        if name.startswith("lqr_") or name.startswith("pole_") or name == "controller_method":
            self._K = None
            self._roa_result = None
        return self.get_state()
```

**Step 4: Verify backend starts without errors**

Run: `cd /Users/shreyasreddy/Documents/GitHub/sims-dev/backend && python -c "from simulations.nonlinear_control_lab import NonlinearControlLabSimulator; s = NonlinearControlLabSimulator('test'); s.initialize(); print('OK:', s.parameters['plant_preset'])"`
Expected: `OK: inverted_pendulum`

**Step 5: Commit**

```
feat: add nonlinear control lab skeleton with plant presets
```

---

## Task 2: Backend — Jacobian Linearization Engine

**Files:**
- Modify: `backend/simulations/nonlinear_control_lab.py`

**Step 1: Implement `_get_plant()` and `_linearize()` methods**

`_get_plant()` returns the current plant (preset or custom). For presets, calls the plant's `f_symbolic()` to get SymPy state/input symbols and dynamics matrix. For custom, parses user expressions via `sympy.sympify`.

`_linearize()` computes A = ∂f/∂x and B = ∂f/∂u using `sympy.Matrix.jacobian()`, evaluates at the selected equilibrium numerically, returns (A, B, C, D) as NumPy arrays. C = I, D = 0.

Key implementation details:
- Cache linearization: only recompute when plant or equilibrium changes
- Controllability matrix: `ctrb = [B, AB, A²B, ..., A^(n-1)B]`, rank via `np.linalg.matrix_rank`
- For presets with parameters (M, m, l, g for pendulum): substitute numerical values before Jacobian evaluation
- `_build_numerical_dynamics()`: lambdify the SymPy expression to a fast NumPy callable for solve_ivp

**Step 2: Implement `_build_numerical_dynamics()` for solve_ivp**

Uses `sympy.lambdify` to convert the symbolic f(x,u) into a vectorized NumPy function. This is the function that `solve_ivp` will call. For presets, also provide a hand-coded NumPy version as fallback (faster than lambdify).

**Step 3: Verify linearization against known results**

Run verification for inverted pendulum at upright equilibrium (θ=π):
- A should have the classic [0,1,0,0; 0,0,-mg/M,0; 0,0,0,1; 0,0,(M+m)g/(Ml),0] structure
- System should be controllable (rank 4)

```bash
cd backend && python -c "
from simulations.nonlinear_control_lab import NonlinearControlLabSimulator
s = NonlinearControlLabSimulator('test')
s.initialize()
A, B = s._linearize_current()
print('A shape:', A.shape)
print('A ='); print(A)
print('B shape:', B.shape)
print('Controllable:', s._is_controllable)
"
```

**Step 4: Commit**

```
feat: add SymPy Jacobian linearization engine
```

---

## Task 3: Backend — Controller Design (LQR + Pole Placement)

**Files:**
- Modify: `backend/simulations/nonlinear_control_lab.py`

**Step 1: Implement `_design_controller()` method**

Dispatches based on `controller_method` parameter:

**LQR branch:**
```python
n = self._A.shape[0]
m = self._B.shape[1]
Q = np.diag([float(self.parameters.get(f"lqr_q{i+1}", 1.0)) for i in range(n)])
R = np.diag([float(self.parameters.get(f"lqr_r{j+1}", 1.0)) for j in range(m)])
P = solve_continuous_are(self._A, self._B, Q, R)
K = np.linalg.solve(R, self._B.T @ P)
```

**Pole placement branch:**
```python
n = self._A.shape[0]
desired = []
for i in range(n):
    re_part = float(self.parameters.get(f"pole_real_{i+1}", -2.0))
    im_part = float(self.parameters.get(f"pole_imag_{i+1}", 0.0))
    desired.append(complex(re_part, im_part))
# Enforce conjugate pairs for real K
desired = _enforce_conjugate_pairs(desired)
result = signal.place_poles(self._A, self._B, np.array(desired))
K = result.gain_matrix
```

Both branches: compute CL eigenvalues `eig(A - BK)`, store `self._K`, `self._cl_eigs`, `self._K_latex` (KaTeX string).

**Step 2: Implement `_enforce_conjugate_pairs()`**

Ensures every complex pole has its conjugate present. If user enters p = -2+3j, automatically include -2-3j. Skip if pure real.

**Step 3: Verify controller design**

```bash
cd backend && python -c "
from simulations.nonlinear_control_lab import NonlinearControlLabSimulator
s = NonlinearControlLabSimulator('test')
s.initialize()
K, cl_eigs = s._design_controller_current()
print('K:', K)
print('CL eigenvalues:', cl_eigs)
print('All stable:', all(e.real < 0 for e in cl_eigs))
"
```

**Step 4: Commit**

```
feat: add LQR and pole placement controller design
```

---

## Task 4: Backend — Nonlinear/Linear Simulation & Comparison

**Files:**
- Modify: `backend/simulations/nonlinear_control_lab.py`

**Step 1: Implement `_simulate()` method**

Two simulations from the same IC:

**Linear prediction:**
```python
A_cl = A - B @ K
# x_lin(t) = expm(A_cl * t) @ delta_x0 + x_eq
t_span = np.linspace(0, T, 500)
x_lin = np.array([expm(A_cl * t) @ dx0 for t in t_span])  # each row is state
x_lin += x_eq  # shift back to absolute coordinates
u_lin = -K @ (x_lin - x_eq).T  # control effort
```

**Nonlinear validation:**
```python
def dynamics(t, x):
    u = -K @ (x - x_eq) + u_eq
    return f_numerical(x, u)

sol = solve_ivp(dynamics, [0, T], x0, method='RK45',
                t_eval=t_span, max_step=0.01,
                events=[divergence_event])
```

`divergence_event`: terminates if `||x|| > 1000` to prevent runaway.

**Step 2: Implement `_compute_vector_field()` method**

Computes the CONTROLLED vector field for the phase portrait: at each grid point, apply u = -K(x - x_eq) + u_eq, compute f(x, u), project onto the selected 2D axes. Returns grid of (dx_i, dx_j) vectors.

Grid: 20×20 over a range centered on the equilibrium. States not on the projection axes are held at equilibrium values.

**Step 3: Implement `_compute_streamlines()` method**

Integrate forward/backward from seed points using solve_ivp, project onto 2D axes. 8-12 seed streamlines from a circle around the equilibrium.

**Step 4: Verify simulation output**

```bash
cd backend && python -c "
from simulations.nonlinear_control_lab import NonlinearControlLabSimulator
s = NonlinearControlLabSimulator('test')
s.initialize({'plant_preset': 'van_der_pol'})
state = s.get_state()
print('Plots:', [p['id'] for p in state['plots']])
print('Metadata keys:', list(state.get('metadata', {}).keys()))
"
```

**Step 5: Commit**

```
feat: add linear/nonlinear simulation comparison engine
```

---

## Task 5: Backend — Region of Attraction Computation

**Files:**
- Modify: `backend/simulations/nonlinear_control_lab.py`

**Step 1: Implement `_compute_roa()` method**

```python
def _compute_roa(self) -> Dict:
    """Compute region of attraction via IC grid simulation."""
    n = self._n_states
    proj_x = int(self.parameters["projection_x"])
    proj_y = int(self.parameters["projection_y"])
    x_eq = self._current_eq["x_eq"]
    u_eq = self._current_eq["u_eq"]

    # Grid centered on equilibrium, in the projection plane
    range_x = 5.0  # adjustable
    range_y = 5.0
    nx, ny = 25, 25
    xs = np.linspace(x_eq[proj_x] - range_x, x_eq[proj_x] + range_x, nx)
    ys = np.linspace(x_eq[proj_y] - range_y, x_eq[proj_y] + range_y, ny)

    results = np.zeros((ny, nx))  # 0=diverged, 0.5=marginal, 1=converged

    def simulate_ic(args):
        ix, iy, x0 = args
        # ... solve_ivp with u = -K(x - x_eq), classify convergence
        return (ix, iy, classification)

    # Build IC grid
    tasks = []
    for iy, y_val in enumerate(ys):
        for ix, x_val in enumerate(xs):
            ic = np.array(x_eq, dtype=float)
            ic[proj_x] = x_val
            ic[proj_y] = y_val
            tasks.append((ix, iy, ic))

    with ThreadPoolExecutor(max_workers=8) as pool:
        for ix, iy, cls in pool.map(simulate_ic, tasks):
            results[iy, ix] = cls

    return {"x_grid": xs.tolist(), "y_grid": ys.tolist(), "convergence": results.tolist()}
```

**Step 2: Wire ROA to the `handle_action()` / button mechanism**

The "compute_roa" button triggers this computation via the execute endpoint's "compute_roa" action. Store result in `self._roa_result`, include in metadata when present.

**Step 3: Verify ROA computation**

```bash
cd backend && python -c "
from simulations.nonlinear_control_lab import NonlinearControlLabSimulator
s = NonlinearControlLabSimulator('test')
s.initialize({'plant_preset': 'van_der_pol'})
roa = s._compute_roa()
import numpy as np
arr = np.array(roa['convergence'])
print('ROA grid:', arr.shape)
print('Converged:', np.sum(arr > 0.8), '/', arr.size)
"
```

**Step 4: Commit**

```
feat: add threaded region of attraction computation
```

---

## Task 6: Backend — get_plots(), get_state(), and Metadata Assembly

**Files:**
- Modify: `backend/simulations/nonlinear_control_lab.py`

**Step 1: Implement `get_plots()` with all Plotly plots**

4 plots:
1. **time_response**: Multi-trace for each state. Solid = nonlinear, dashed = linear. X-axis = time, Y-axis = state value. Legend per state.
2. **control_effort**: u(t) for nonlinear (solid) and linear (dashed). For MIMO, multiple traces.
3. **eigenvalue_map**: CL eigenvalues on complex plane. OL eigenvalues as reference. Imaginary axis as stability boundary.
4. **roa_heatmap**: Plotly heatmap/contour of convergence grid. Only included when `self._roa_result` is not None.

All plots follow existing conventions: `paper_bgcolor`, `plot_bgcolor`, `gridcolor`, `datarevision`, `uirevision`.

**Step 2: Implement `get_state()` with rich metadata**

```python
def get_state(self):
    state = self._compute_all()
    return {
        "parameters": self.parameters.copy(),
        "plots": state["plots"],
        "metadata": {
            "simulation_type": "nonlinear_control_lab",
            "has_custom_viewer": True,
            "plant_name": self._plant_name,
            "n_states": self._n_states,
            "n_inputs": self._n_inputs,
            "state_names": self._state_names,
            "input_names": self._input_names,
            "equilibria": self._equilibria_list,
            "selected_eq": self._current_eq,
            "A_matrix": self._A.tolist() if self._A is not None else None,
            "B_matrix": self._B.tolist() if self._B is not None else None,
            "K_matrix": self._K.tolist() if self._K is not None else None,
            "K_latex": self._K_latex,
            "cl_eigenvalues": [{"re": e.real, "im": e.imag} for e in self._cl_eigs],
            "ol_eigenvalues": [{"re": e.real, "im": e.imag} for e in self._ol_eigs],
            "is_controllable": self._is_controllable,
            "controllability_rank": self._ctrb_rank,
            "is_stable": all(e.real < 0 for e in self._cl_eigs),
            "ode_latex": self._ode_latex,
            "linearized_latex": self._linearized_latex,
            "performance": self._performance_metrics,
            # Phase portrait data (computed backend, rendered frontend Canvas)
            "vector_field": self._vector_field_data,
            "streamlines": self._streamline_data,
            "trajectory_nonlinear": self._traj_nl,
            "trajectory_linear": self._traj_lin,
            "roa": self._roa_result,
        },
    }
```

**Step 3: Implement `handle_action()` for execute endpoint**

Handle actions: `init`, `update`, `run`, `reset`, `compute_roa`. The `compute_roa` action triggers `_compute_roa()` and stores result.

**Step 4: Verify full state output**

```bash
cd backend && python -c "
from simulations.nonlinear_control_lab import NonlinearControlLabSimulator
s = NonlinearControlLabSimulator('test')
s.initialize()
state = s.get_state()
m = state['metadata']
print('Type:', m['simulation_type'])
print('Plant:', m['plant_name'])
print('States:', m['n_states'])
print('Controllable:', m['is_controllable'])
print('CL stable:', m['is_stable'])
print('Plots:', len(state['plots']))
print('Vector field pts:', len(m.get('vector_field', {}).get('dx', [])) if m.get('vector_field') else 0)
"
```

**Step 5: Commit**

```
feat: add plots, metadata, and state assembly for nonlinear control lab
```

---

## Task 7: Backend — Registration (Catalog + Registry)

**Files:**
- Modify: `backend/simulations/__init__.py:62-63` (add import + registry entry)
- Modify: `backend/simulations/catalog.py:3127` (add catalog entry before closing `]`)

**Step 1: Add import and registry entry**

In `__init__.py`, after line 63 (`from .phase_portrait import PhasePortraitSimulator`):
```python
from .nonlinear_control_lab import NonlinearControlLabSimulator
```

In `SIMULATOR_REGISTRY`, after `"phase_portrait": PhasePortraitSimulator,`:
```python
"nonlinear_control_lab": NonlinearControlLabSimulator,
```

In `__all__`, add `"NonlinearControlLabSimulator",`

**Step 2: Add catalog entry**

After the `phase_portrait` entry (line 3127), before the closing `]`:

```python
# =========================================================================
# NONLINEAR CONTROL LAB — Linearize → Design → Validate
# =========================================================================
{
    "id": "nonlinear_control_lab",
    "name": "Nonlinear Control Lab",
    "description": "Linearize nonlinear plants at equilibria, design LQR/pole-placement controllers on the linearization, then validate on the true nonlinear dynamics. Visualize region of attraction and compare linear vs. nonlinear responses.",
    "category": "Control Systems",
    "thumbnail": "🔬",
    "tags": ["nonlinear", "linearization", "Jacobian", "LQR", "pole placement",
             "region of attraction", "inverted pendulum", "MIMO", "state feedback",
             "Lyapunov", "phase portrait", "solve_ivp"],
    "has_simulator": True,
    "controls": [
        # Plant group
        {"type": "select", "name": "plant_preset", "label": "Plant", "options": [
            {"value": "inverted_pendulum", "label": "Inverted Pendulum on Cart (4×1)"},
            {"value": "ball_and_beam", "label": "Ball and Beam (4×1)"},
            {"value": "coupled_tanks", "label": "Coupled Tanks MIMO (2×2)"},
            {"value": "van_der_pol", "label": "Van der Pol + Input (2×1)"},
            {"value": "custom", "label": "Custom ODE"},
        ], "default": "inverted_pendulum", "group": "Plant"},
        # Custom ODE controls (visible_when custom)
        {"type": "select", "name": "n_states_custom", "label": "Number of States", "options": [
            {"value": "2", "label": "2"}, {"value": "3", "label": "3"}, {"value": "4", "label": "4"},
        ], "default": "2", "group": "Plant", "visible_when": {"plant_preset": "custom"}},
        {"type": "select", "name": "n_inputs_custom", "label": "Number of Inputs", "options": [
            {"value": "1", "label": "1"}, {"value": "2", "label": "2"},
        ], "default": "1", "group": "Plant", "visible_when": {"plant_preset": "custom"}},
        {"type": "expression", "name": "f1_expr", "label": "ẋ₁ = f₁(x,u)", "default": "x2", "group": "Plant", "visible_when": {"plant_preset": "custom"}},
        {"type": "expression", "name": "f2_expr", "label": "ẋ₂ = f₂(x,u)", "default": "-sin(x1) - 0.5*x2 + u1", "group": "Plant", "visible_when": {"plant_preset": "custom"}},
        {"type": "expression", "name": "f3_expr", "label": "ẋ₃ = f₃(x,u)", "default": "x4", "group": "Plant", "visible_when": {"plant_preset": "custom"}},
        {"type": "expression", "name": "f4_expr", "label": "ẋ₄ = f₄(x,u)", "default": "-x3 + u1", "group": "Plant", "visible_when": {"plant_preset": "custom"}},
        # Equilibrium group
        {"type": "select", "name": "equilibrium_idx", "label": "Equilibrium", "options": [
            {"value": "0", "label": "Default"},
        ], "default": "0", "group": "Equilibrium"},
        # Custom equilibrium (visible_when custom)
        {"type": "slider", "name": "eq_x1", "label": "x₁ eq", "min": -10, "max": 10, "step": 0.1, "default": 0, "group": "Equilibrium", "visible_when": {"plant_preset": "custom"}},
        {"type": "slider", "name": "eq_x2", "label": "x₂ eq", "min": -10, "max": 10, "step": 0.1, "default": 0, "group": "Equilibrium", "visible_when": {"plant_preset": "custom"}},
        {"type": "slider", "name": "eq_x3", "label": "x₃ eq", "min": -10, "max": 10, "step": 0.1, "default": 0, "group": "Equilibrium", "visible_when": {"plant_preset": "custom"}},
        {"type": "slider", "name": "eq_x4", "label": "x₄ eq", "min": -10, "max": 10, "step": 0.1, "default": 0, "group": "Equilibrium", "visible_when": {"plant_preset": "custom"}},
        {"type": "slider", "name": "eq_u1", "label": "u₁ eq", "min": -10, "max": 10, "step": 0.1, "default": 0, "group": "Equilibrium", "visible_when": {"plant_preset": "custom"}},
        {"type": "slider", "name": "eq_u2", "label": "u₂ eq", "min": -10, "max": 10, "step": 0.1, "default": 0, "group": "Equilibrium", "visible_when": {"plant_preset": "custom"}},
        {"type": "select", "name": "projection_x", "label": "Phase X-axis", "options": [
            {"value": "0", "label": "State 1"}, {"value": "1", "label": "State 2"},
            {"value": "2", "label": "State 3"}, {"value": "3", "label": "State 4"},
        ], "default": "0", "group": "Equilibrium"},
        {"type": "select", "name": "projection_y", "label": "Phase Y-axis", "options": [
            {"value": "0", "label": "State 1"}, {"value": "1", "label": "State 2"},
            {"value": "2", "label": "State 3"}, {"value": "3", "label": "State 4"},
        ], "default": "2", "group": "Equilibrium"},
        # Controller group
        {"type": "select", "name": "controller_method", "label": "Design Method", "options": [
            {"value": "lqr", "label": "LQR (Riccati)"},
            {"value": "pole_placement", "label": "Pole Placement"},
        ], "default": "lqr", "group": "Controller"},
        {"type": "slider", "name": "lqr_q1", "label": "Q₁₁ (state 1)", "min": 0.01, "max": 100, "step": 0.01, "default": 1.0, "group": "Controller", "visible_when": {"controller_method": "lqr"}},
        {"type": "slider", "name": "lqr_q2", "label": "Q₂₂ (state 2)", "min": 0.01, "max": 100, "step": 0.01, "default": 1.0, "group": "Controller", "visible_when": {"controller_method": "lqr"}},
        {"type": "slider", "name": "lqr_q3", "label": "Q₃₃ (state 3)", "min": 0.01, "max": 100, "step": 0.01, "default": 10.0, "group": "Controller", "visible_when": {"controller_method": "lqr"}},
        {"type": "slider", "name": "lqr_q4", "label": "Q₄₄ (state 4)", "min": 0.01, "max": 100, "step": 0.01, "default": 1.0, "group": "Controller", "visible_when": {"controller_method": "lqr"}},
        {"type": "slider", "name": "lqr_r1", "label": "R₁₁ (input 1)", "min": 0.01, "max": 100, "step": 0.01, "default": 1.0, "group": "Controller", "visible_when": {"controller_method": "lqr"}},
        {"type": "slider", "name": "lqr_r2", "label": "R₂₂ (input 2)", "min": 0.01, "max": 100, "step": 0.01, "default": 1.0, "group": "Controller", "visible_when": {"controller_method": "lqr"}},
        {"type": "slider", "name": "pole_real_1", "label": "p₁ real", "min": -20, "max": 0, "step": 0.1, "default": -2.0, "group": "Controller", "visible_when": {"controller_method": "pole_placement"}},
        {"type": "slider", "name": "pole_imag_1", "label": "p₁ imag", "min": -10, "max": 10, "step": 0.1, "default": 0.0, "group": "Controller", "visible_when": {"controller_method": "pole_placement"}},
        {"type": "slider", "name": "pole_real_2", "label": "p₂ real", "min": -20, "max": 0, "step": 0.1, "default": -2.0, "group": "Controller", "visible_when": {"controller_method": "pole_placement"}},
        {"type": "slider", "name": "pole_imag_2", "label": "p₂ imag", "min": -10, "max": 10, "step": 0.1, "default": 0.0, "group": "Controller", "visible_when": {"controller_method": "pole_placement"}},
        {"type": "slider", "name": "pole_real_3", "label": "p₃ real", "min": -20, "max": 0, "step": 0.1, "default": -3.0, "group": "Controller", "visible_when": {"controller_method": "pole_placement"}},
        {"type": "slider", "name": "pole_imag_3", "label": "p₃ imag", "min": -10, "max": 10, "step": 0.1, "default": 0.0, "group": "Controller", "visible_when": {"controller_method": "pole_placement"}},
        {"type": "slider", "name": "pole_real_4", "label": "p₄ real", "min": -20, "max": 0, "step": 0.1, "default": -3.0, "group": "Controller", "visible_when": {"controller_method": "pole_placement"}},
        {"type": "slider", "name": "pole_imag_4", "label": "p₄ imag", "min": -10, "max": 10, "step": 0.1, "default": 0.0, "group": "Controller", "visible_when": {"controller_method": "pole_placement"}},
        # Simulation group
        {"type": "slider", "name": "ic_offset_1", "label": "Δx₁ (IC offset)", "min": -5, "max": 5, "step": 0.1, "default": 0.0, "group": "Simulation"},
        {"type": "slider", "name": "ic_offset_2", "label": "Δx₂", "min": -5, "max": 5, "step": 0.1, "default": 0.1, "group": "Simulation"},
        {"type": "slider", "name": "ic_offset_3", "label": "Δx₃", "min": -5, "max": 5, "step": 0.1, "default": 0.2, "group": "Simulation"},
        {"type": "slider", "name": "ic_offset_4", "label": "Δx₄", "min": -5, "max": 5, "step": 0.1, "default": 0.0, "group": "Simulation"},
        {"type": "slider", "name": "sim_time", "label": "Duration", "min": 1, "max": 30, "step": 0.5, "default": 10.0, "unit": "s", "group": "Simulation"},
        {"type": "button", "name": "compute_roa", "label": "Compute Region of Attraction", "group": "Simulation"},
        # Display group
        {"type": "checkbox", "name": "show_linear", "label": "Show Linear Prediction", "default": True, "group": "Display"},
        {"type": "checkbox", "name": "show_vector_field", "label": "Show Vector Field", "default": True, "group": "Display"},
        {"type": "checkbox", "name": "show_streamlines", "label": "Show Streamlines", "default": True, "group": "Display"},
    ],
    "default_params": {
        "plant_preset": "inverted_pendulum",
        "equilibrium_idx": "0",
        "controller_method": "lqr",
        "projection_x": "0", "projection_y": "2",
        "lqr_q1": 1.0, "lqr_q2": 1.0, "lqr_q3": 10.0, "lqr_q4": 1.0,
        "lqr_r1": 1.0, "lqr_r2": 1.0,
        "pole_real_1": -2.0, "pole_imag_1": 0.0,
        "pole_real_2": -2.0, "pole_imag_2": 0.0,
        "pole_real_3": -3.0, "pole_imag_3": 0.0,
        "pole_real_4": -3.0, "pole_imag_4": 0.0,
        "ic_offset_1": 0.0, "ic_offset_2": 0.1,
        "ic_offset_3": 0.2, "ic_offset_4": 0.0,
        "sim_time": 10.0,
        "show_linear": True, "show_vector_field": True, "show_streamlines": True,
        "n_states_custom": "2", "n_inputs_custom": "1",
        "f1_expr": "x2", "f2_expr": "-sin(x1) - 0.5*x2 + u1",
        "f3_expr": "x4", "f4_expr": "-x3 + u1",
        "eq_x1": 0, "eq_x2": 0, "eq_x3": 0, "eq_x4": 0,
        "eq_u1": 0, "eq_u2": 0,
    },
    "plots": [
        {"id": "time_response", "title": "State Trajectories", "description": "Linear (dashed) vs nonlinear (solid) state responses"},
        {"id": "control_effort", "title": "Control Effort", "description": "Control input u(t) applied to the plant"},
        {"id": "eigenvalue_map", "title": "Eigenvalue Map", "description": "Open-loop and closed-loop eigenvalues on complex plane"},
        {"id": "roa_heatmap", "title": "Region of Attraction", "description": "IC grid colored by convergence to equilibrium"},
    ],
},
```

**Step 3: Verify backend loads and API returns the new simulation**

```bash
cd backend && python -c "
from simulations.catalog import get_simulation_by_id
sim = get_simulation_by_id('nonlinear_control_lab')
print('Found:', sim['name'])
print('Controls:', len(sim['controls']))
from simulations import SIMULATOR_REGISTRY
print('Registry:', 'nonlinear_control_lab' in SIMULATOR_REGISTRY)
"
```

**Step 4: Start the backend and verify API**

```bash
cd backend && timeout 5 python -m uvicorn main:app --port 8000 2>&1 | head -5
# Then in another test:
curl -s http://127.0.0.1:8000/api/simulations/nonlinear_control_lab | python -m json.tool | head -20
```

**Step 5: Commit**

```
feat: register nonlinear control lab in catalog and simulator registry
```

---

## Task 8: Frontend — NonlinearControlLabViewer.jsx (Canvas Phase Portrait)

**Files:**
- Create: `frontend/src/components/NonlinearControlLabViewer.jsx`

**Step 1: Create the viewer component with Canvas phase portrait**

The Canvas phase portrait is the centerpiece. It renders:
- Vector field arrows from `metadata.vector_field`
- Streamlines from `metadata.streamlines`
- Nonlinear trajectory from `metadata.trajectory_nonlinear`
- Linear trajectory overlay (dashed) from `metadata.trajectory_linear`
- Equilibrium marker
- ROA heatmap overlay from `metadata.roa`
- Click-to-set IC interaction

Key Canvas rendering functions:
- `drawVectorField(ctx, data, transform)`: arrows with magnitude-scaled length and color
- `drawStreamlines(ctx, data, transform)`: smooth curves with arrowheads
- `drawTrajectory(ctx, points, transform, style)`: animated trajectory with trail
- `drawEquilibrium(ctx, point, transform, type)`: filled/open circle based on stability
- `drawROAOverlay(ctx, data, transform)`: semi-transparent colored rectangles

Transform: maps state-space coordinates to canvas pixels. Supports zoom/pan via mouse.

**Step 2: Add Plotly comparison plots**

Time response and control effort plots from `plots` prop. Eigenvalue map plot. Use the same TuningPlot-style wrapper pattern from ControllerTuningLabViewer.

**Step 3: Add KaTeX derivation chain panel**

Shows the full workflow:
1. Nonlinear ODE: `ẋ = f(x,u)` (from `metadata.ode_latex`)
2. Arrow → Linearized: `δẋ = Aδx + Bδu` (from `metadata.linearized_latex`)
3. Arrow → Gain: `K = ...` (from `metadata.K_latex`)
4. Arrow → CL eigenvalues (from `metadata.cl_eigenvalues`)

Uses lazy-loaded KaTeX via the same `loadKatex()` pattern as ControllerTuningLabViewer.

**Step 4: Add metrics strip**

Badges for: controllability rank, CL stability, eigenvalue locations, convergence time, max state deviation.

**Step 5: Commit**

```
feat: add NonlinearControlLabViewer with Canvas phase portrait
```

---

## Task 9: Frontend — CSS Styling

**Files:**
- Create: `frontend/src/styles/NonlinearControlLab.css`

**Step 1: Write all CSS using design system variables**

Key classes:
- `.ncl-viewer`: main container, flex row layout (60/40 split)
- `.ncl-phase-canvas-container`: Canvas wrapper with border, background
- `.ncl-canvas`: the actual `<canvas>` element
- `.ncl-plots-column`: stacked Plotly plots
- `.ncl-derivation-chain`: KaTeX panel below plots
- `.ncl-metrics-strip`: badge strip
- `.ncl-roa-section`: full-width ROA heatmap section
- `.ncl-axis-selector`: projection axis dropdowns overlay on canvas
- Responsive: stack vertically below 768px

All colors via `var(--...)`, all radii via `var(--radius-...)`, transitions via `var(--transition-...)`.

**Step 2: Commit**

```
feat: add NonlinearControlLab CSS with design system variables
```

---

## Task 10: Frontend — Wire Viewer into SimulationViewer.jsx

**Files:**
- Modify: `frontend/src/components/SimulationViewer.jsx:62-63` (add lazy import)
- Modify: `frontend/src/components/SimulationViewer.jsx:2025-2026` (add viewer chain entry)

**Step 1: Add lazy import**

After line 62 (`const SteadyStateErrorViewer = lazy(...)`):
```javascript
const NonlinearControlLabViewer = lazy(() => import('./NonlinearControlLabViewer'));
```

**Step 2: Add viewer chain entry**

After the `steady_state_error` block (line 2025, before the `) : (` fallback):
```jsx
) : metadata?.simulation_type === 'nonlinear_control_lab' ? (
  <Suspense fallback={<LazyLoadFallback />}>
    <NonlinearControlLabViewer
      metadata={metadata}
      plots={plots}
      currentParams={currentParams}
      onParamChange={onParamChange}
      onButtonClick={onButtonClick}
    />
  </Suspense>
```

**Step 3: Verify the page loads**

Start frontend dev server, navigate to `/simulation/nonlinear_control_lab`. Verify:
- No console errors
- Controls render in grouped panels
- Plots appear
- Canvas renders (even if empty initially)

**Step 4: Commit**

```
feat: wire NonlinearControlLabViewer into SimulationViewer
```

---

## Task 11: Integration Testing & Polish

**Step 1: Test all 4 plant presets**

For each preset:
- Select it from dropdown
- Verify linearization produces correct A, B dimensions
- Verify LQR produces stable CL eigenvalues
- Verify nonlinear simulation doesn't crash or produce NaN
- Verify phase portrait renders with vector field
- Switch projection axes and verify redraw

**Step 2: Test pole placement**

- Switch to pole placement
- Adjust pole sliders
- Verify conjugate pair enforcement
- Verify CL eigenvalues match desired poles

**Step 3: Test ROA computation**

- Click "Compute Region of Attraction" button
- Verify heatmap appears after computation (~2-5s)
- Verify green region around equilibrium for stable designs
- Test with unstable design (positive real poles) — should show mostly red

**Step 4: Test MIMO (coupled tanks)**

- Select coupled tanks
- Verify 2×2 R matrix, 2×2 K matrix
- Verify both control inputs shown in control effort plot

**Step 5: Test custom ODE**

- Select custom, enter `x2` and `-x1 + u1` (harmonic oscillator)
- Set equilibrium at origin
- Verify linearization produces correct A = [[0,1],[-1,0]]
- Design LQR controller, verify stabilization

**Step 6: Commit**

```
feat: complete nonlinear control lab integration and testing
```

---

## Task 12: Update CLAUDE.md and Tracking Files

**Files:**
- Modify: `CLAUDE.md` (Recent Features Added section)
- Check: `.claude/bugs.md` and `.claude/mistakes.md` for any issues found during implementation

**Step 1: Add to Recent Features Added**

```markdown
### Nonlinear Control Lab (simulation: `nonlinear_control_lab`)
- **Backend**: `backend/simulations/nonlinear_control_lab.py` (~1400 lines)
- **Frontend**: `frontend/src/components/NonlinearControlLabViewer.jsx` (~700 lines)
- **CSS**: `frontend/src/styles/NonlinearControlLab.css` (~400 lines)
- **Purpose**: Linearize → Design → Validate workflow for nonlinear plants
- **Key features**:
  - 4 plant presets: inverted pendulum (4×1), ball & beam (4×1), coupled tanks MIMO (2×2), Van der Pol (2×1) + custom ODE
  - SymPy symbolic Jacobian for exact linearization at user-selected equilibria
  - LQR (Riccati) and pole placement controller design
  - Side-by-side linear prediction vs nonlinear validation via solve_ivp
  - HTML5 Canvas phase portrait with vector field, streamlines, animated trajectories
  - User-selectable 2D projection axes for higher-order systems
  - Threaded region of attraction computation (25×25 IC grid)
  - KaTeX derivation chain: ODE → A,B → K → CL eigenvalues
  - Full MIMO support (coupled tanks: 2-input 2-output LQR)
```

**Step 2: Commit**

```
docs: add nonlinear control lab to CLAUDE.md feature list
```
