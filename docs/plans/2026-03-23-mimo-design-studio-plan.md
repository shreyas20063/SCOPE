# MIMO State-Space Design Studio Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a standalone MIMO state-space design studio simulation with analysis, pole placement, LQR, and LQG for arbitrary N×M×P systems.

**Architecture:** New simulation `mimo_design_studio` with a reusable `core/mimo_utils.py` math module, a `simulations/mimo_design_studio.py` simulator class, a custom `MIMODesignStudioViewer.jsx` frontend with tabbed layout, and a dedicated CSS file.

**Tech Stack:** Python (NumPy, SciPy — solve_ivp, place_poles, solve_continuous_are), React 18 (Plotly.js, KaTeX), CSS variables from design system.

---

### Task 1: Create `backend/core/mimo_utils.py` — Pure MIMO Math Utilities

**Files:**
- Create: `backend/core/mimo_utils.py`

**Step 1: Write the module with all MIMO math functions**

```python
"""MIMO state-space math utilities.

Pure NumPy/SciPy functions for controllability, observability,
MIMO simulation, pole placement, LQR, and LQG.
Reusable by any simulator — no BaseSimulator dependency.
"""

import numpy as np
from scipy.integrate import solve_ivp
from scipy.linalg import solve_continuous_are
from scipy.signal import place_poles
from typing import Any, Dict, List, Optional, Tuple


def controllability_matrix(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    """Compute controllability matrix [B, AB, A²B, ..., A^{n-1}B].

    Args:
        A: n×n state matrix.
        B: n×m input matrix.

    Returns:
        n × (n*m) controllability matrix.
    """
    n = A.shape[0]
    cols = [np.linalg.matrix_power(A, i) @ B for i in range(n)]
    return np.hstack(cols)


def observability_matrix(A: np.ndarray, C: np.ndarray) -> np.ndarray:
    """Compute observability matrix [C; CA; CA²; ...; CA^{n-1}].

    Args:
        A: n×n state matrix.
        C: p×n output matrix.

    Returns:
        (n*p) × n observability matrix.
    """
    n = A.shape[0]
    rows = [C @ np.linalg.matrix_power(A, i) for i in range(n)]
    return np.vstack(rows)


def mimo_step_response(
    A: np.ndarray,
    B: np.ndarray,
    C: np.ndarray,
    D: np.ndarray,
    t_eval: np.ndarray,
    input_channel: Optional[int] = None,
) -> Dict[str, Any]:
    """Compute MIMO step response via solve_ivp (RK45).

    For each input channel j, applies u_j(t) = 1 (unit step) with all
    other inputs zero, and computes all output responses.

    Args:
        A: n×n state matrix.
        B: n×m input matrix.
        C: p×n output matrix.
        D: p×m feedthrough matrix.
        t_eval: 1D time array for evaluation points.
        input_channel: If given, only simulate this input channel (0-indexed).
                       If None, simulate all input channels.

    Returns:
        Dict with:
          "t": time array (same as t_eval)
          "responses": dict mapping (input_idx, output_idx) → 1D array of y values
          "n_inputs": m
          "n_outputs": p
    """
    n_states = A.shape[0]
    n_inputs = B.shape[1]
    n_outputs = C.shape[0]
    t_span = (float(t_eval[0]), float(t_eval[-1]))

    channels = [input_channel] if input_channel is not None else range(n_inputs)
    responses = {}

    for j in channels:
        u = np.zeros(n_inputs)
        u[j] = 1.0

        def dynamics(t: float, x: np.ndarray, _u: np.ndarray = u) -> np.ndarray:
            return A @ x + B @ _u

        sol = solve_ivp(
            dynamics, t_span, np.zeros(n_states),
            t_eval=t_eval, method="RK45", rtol=1e-8, atol=1e-10,
        )
        # Y: p × len(t)
        Y = C @ sol.y + (D @ u).reshape(-1, 1)
        for i in range(n_outputs):
            responses[(j, i)] = Y[i]

    return {
        "t": t_eval,
        "responses": responses,
        "n_inputs": n_inputs,
        "n_outputs": n_outputs,
    }


def mimo_impulse_response(
    A: np.ndarray,
    B: np.ndarray,
    C: np.ndarray,
    D: np.ndarray,
    t_eval: np.ndarray,
    input_channel: Optional[int] = None,
) -> Dict[str, Any]:
    """Compute MIMO impulse response.

    Impulse response = C @ expm(A*t) @ B column j.
    Uses solve_ivp with x(0) = B[:,j] (state-space impulse trick).

    Args:
        A, B, C, D: State-space matrices.
        t_eval: Time array.
        input_channel: If given, only simulate this channel.

    Returns:
        Same structure as mimo_step_response.
    """
    n_states = A.shape[0]
    n_inputs = B.shape[1]
    n_outputs = C.shape[0]
    t_span = (float(t_eval[0]), float(t_eval[-1]))

    channels = [input_channel] if input_channel is not None else range(n_inputs)
    responses = {}

    for j in channels:
        x0 = B[:, j].copy()

        def dynamics(t: float, x: np.ndarray) -> np.ndarray:
            return A @ x

        sol = solve_ivp(
            dynamics, t_span, x0,
            t_eval=t_eval, method="RK45", rtol=1e-8, atol=1e-10,
        )
        Y = C @ sol.y
        # Add D*delta(0) contribution at t=0
        for i in range(n_outputs):
            responses[(j, i)] = Y[i]

    return {
        "t": t_eval,
        "responses": responses,
        "n_inputs": n_inputs,
        "n_outputs": n_outputs,
    }


def mimo_lqr(
    A: np.ndarray,
    B: np.ndarray,
    Q: np.ndarray,
    R: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute MIMO LQR gain via continuous algebraic Riccati equation.

    Solves: A'P + PA - PBR⁻¹B'P + Q = 0
    Returns: K = R⁻¹B'P

    Args:
        A: n×n state matrix.
        B: n×m input matrix.
        Q: n×n state cost (positive semi-definite).
        R: m×m input cost (positive definite).

    Returns:
        (K, P, cl_eigs) where:
          K: m×n gain matrix
          P: n×n Riccati solution
          cl_eigs: closed-loop eigenvalues of (A - BK)
    """
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
) -> Dict[str, np.ndarray]:
    """Compute full MIMO LQG controller (LQR + Kalman filter).

    Separation principle: LQR gain K from performance Riccati,
    Kalman gain L from estimator Riccati (dual problem).

    Augmented closed-loop system (2n states):
      x_aug = [x; x̂]
      A_cl = [[A, -BK], [LC, A-BK-LC]]

    Args:
        A: n×n, B: n×m, C: p×n — plant matrices.
        Q: n×n state cost, R: m×m input cost (for LQR).
        Qw: n×n process noise covariance.
        Rv: p×p measurement noise covariance.

    Returns:
        Dict with: K, L, P_lqr, P_kal, cl_eigs, A_cl, K_eigs, L_eigs
    """
    # LQR Riccati
    P_lqr = solve_continuous_are(A, B, Q, R)
    K = np.linalg.solve(R, B.T @ P_lqr)

    # Kalman (dual) Riccati: A'P + PA' - PC'Rv⁻¹CP + Qw = 0
    P_kal = solve_continuous_are(A.T, C.T, Qw, Rv)
    L = P_kal @ C.T @ np.linalg.inv(Rv)

    # Augmented closed-loop
    n = A.shape[0]
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
    """Compute MIMO state-feedback gain for pole placement.

    Args:
        A: n×n state matrix.
        B: n×m input matrix.
        desired_poles: length-n array of desired closed-loop poles.
                       Complex poles must come in conjugate pairs.

    Returns:
        (K, cl_eigs) where K is m×n gain matrix and cl_eigs are
        the actual achieved closed-loop eigenvalues.
    """
    result = place_poles(A, B, desired_poles)
    K = result.gain_matrix
    cl_eigs = np.linalg.eigvals(A - B @ K)
    return K, cl_eigs


def validate_dimensions(
    A: np.ndarray,
    B: np.ndarray,
    C: np.ndarray,
    D: np.ndarray,
) -> Optional[str]:
    """Validate A, B, C, D dimension compatibility.

    Returns None if valid, or an error message string.
    """
    n = A.shape[0]
    if A.shape != (n, n):
        return f"A must be square, got {A.shape}"
    if B.shape[0] != n:
        return f"B must have {n} rows to match A ({n}×{n}), got {B.shape[0]}"
    m = B.shape[1]
    p = C.shape[0]
    if C.shape[1] != n:
        return f"C must have {n} columns to match A ({n}×{n}), got {C.shape[1]}"
    if D.shape != (p, m):
        return f"D must be {p}×{m} to match C ({p} rows) and B ({m} cols), got {D.shape}"
    return None


def validate_conjugate_pairs(poles: np.ndarray) -> Optional[str]:
    """Check that complex poles come in conjugate pairs.

    Returns None if valid, or an error message string.
    """
    complex_poles = [p for p in poles if abs(p.imag) > 1e-10]
    for p in complex_poles:
        conj = p.conjugate()
        found = False
        for q in complex_poles:
            if abs(p - q) > 1e-10 and abs(conj - q) < 1e-8:
                found = True
                break
        if not found:
            return (
                f"Complex pole {p:.4g} must have a conjugate pair. "
                f"Add {conj:.4g} to the desired poles."
            )
    return None
```

**Step 2: Verify module imports cleanly**

Run: `cd /Users/shreyasreddy/Documents/GitHub/sims-dev && python -c "from backend.core.mimo_utils import *; print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add backend/core/mimo_utils.py
git commit -m "feat: add MIMO state-space math utilities module"
```

---

### Task 2: Create `backend/simulations/mimo_design_studio.py` — Simulator Class (Part 1: Core + Analysis)

**Files:**
- Create: `backend/simulations/mimo_design_studio.py`

This task covers: presets, parameter schema, matrix parsing, initialization, analysis computation (eigenvalues, controllability/observability), and all plot generation for analysis mode.

**Step 1: Write the simulator — presets, schema, parsing, analysis**

The simulator must implement:

1. **PARAMETER_SCHEMA / DEFAULT_PARAMS** with these controls:
   - `preset` (select): aircraft_lateral, coupled_spring_mass, dc_motor_flex, custom
   - `matrix_a/b/c/d` (expression): semicolon-delimited matrices
   - `design_mode` (select): analysis, pole_placement, lqr, lqg
   - `desired_poles` (expression): for pole placement mode
   - `q_diag` (expression): Q diagonal for LQR/LQG
   - `r_diag` (expression): R diagonal for LQR/LQG
   - `qw_diag` (expression): Qw diagonal for LQG (process noise)
   - `rv_diag` (expression): Rv diagonal for LQG (measurement noise)
   - `time_span` (slider): 1–50s, default 10
   - `step_input_channel` (slider): 0 to m-1, default 0
   - Buttons: `compute_controller` (for all design modes)
   - `visible_when` conditions to show/hide controls per design_mode

2. **Three presets** with real-world A, B, C, D matrices:

   **Aircraft Lateral Dynamics** (Etkin & Reid textbook model):
   ```
   States: [β, p, r, φ] (sideslip, roll rate, yaw rate, roll angle)
   Inputs: [δa, δr] (aileron, rudder)
   Outputs: [β, φ] (sideslip, roll angle)

   A = [[-0.322,  0.064,  0.0364, -0.9917],
        [ 0.0,   -0.465,  0.0121,  0.0],
        [-0.0150, -0.624, -0.275,   0.0],
        [ 0.0,    0.018,  0.318,   0.0]]
   B = [[ 0.0,    0.0064],
        [-0.161,  0.0028],
        [ 0.0,   -0.264],
        [ 0.0,    0.0]]
   C = [[1, 0, 0, 0],
        [0, 0, 0, 1]]
   D = [[0, 0],
        [0, 0]]
   ```

   **Coupled Mass-Spring-Damper** (two masses connected by springs):
   ```
   States: [x1, v1, x2, v2]
   Inputs: [F1, F2]
   Outputs: [x1, x2]

   m1=1, m2=1, k1=2, k2=1, kc=0.5, b1=0.3, b2=0.3
   A = [[ 0,    1,     0,    0],
        [-(k1+kc)/m1, -b1/m1, kc/m1,  0],
        [ 0,    0,     0,    1],
        [ kc/m2,  0,    -(k2+kc)/m2, -b2/m2]]
   B = [[0,   0],
        [1/m1, 0],
        [0,   0],
        [0,   1/m2]]
   C = [[1, 0, 0, 0],
        [0, 0, 1, 0]]
   D = [[0, 0],
        [0, 0]]
   ```

   **DC Motor + Flexible Load** (MISO: 4 states, 1 input, 2 outputs):
   ```
   States: [θm, ωm, θL, ωL] (motor angle, motor speed, load angle, load speed)
   Input: [V] (voltage)
   Outputs: [θm, θL]

   Parameters: J_m=0.01, J_L=0.05, b=0.1, k_s=1.0, K_t=0.1, K_e=0.1, R=1.0, L≈0
   A = [[ 0,      1,       0,     0],
        [-k_s/J_m, -(b+K_t*K_e/R)/J_m, k_s/J_m,  0],
        [ 0,      0,       0,     1],
        [ k_s/J_L,  0,      -k_s/J_L, -b/J_L]]
   B = [[0],
        [K_t/(J_m*R)],
        [0],
        [0]]
   C = [[1, 0, 0, 0],
        [0, 0, 1, 0]]
   D = [[0],
        [0]]
   ```

3. **`_compute()` method** that:
   - Parses matrices from expression strings (reuse pattern from state_space_analyzer `_parse_matrix`)
   - Validates dimensions via `mimo_utils.validate_dimensions()`
   - Computes eigenvalues of A
   - Computes controllability and observability matrices + ranks
   - Computes step/impulse responses via `mimo_utils.mimo_step_response/impulse`
   - If design_mode != "analysis", dispatches to controller computation (Task 3)
   - Returns data dict with all results

4. **Plot builders** (called from `_build_plots(data)`):
   - `_response_grid_plot(data, response_type)`: Builds the p×m subplot grid for step/impulse. Uses Plotly `make_subplots` style — actually returns a single Plotly figure with subplots configured via subplot row/col axes. Each trace is `{x: t, y: response[(j,i)], name: "y_{i+1} from u_{j+1}"}`. When controller is active, show both OL (dashed) and CL (solid).
   - `_eigenvalue_plot(data)`: Open-loop eigenvalues as × markers. When controller active, add CL eigenvalues as ● markers with different color. jω axis line, unit circle for reference.
   - All plots follow the project's Plotly conventions (paper_bgcolor, plot_bgcolor, gridcolor, font, margins, datarevision, uirevision).

5. **`get_state()` method** returning:
   ```python
   {
       "parameters": self.parameters.copy(),
       "plots": self._build_plots(data),
       "metadata": {
           "simulation_type": "mimo_design_studio",
           "n_states": n, "n_inputs": m, "n_outputs": p,
           "preset": preset_name,
           "matrices": {"A": A.tolist(), "B": B.tolist(), "C": C.tolist(), "D": D.tolist()},
           "eigenvalues": {"real": eigs.real.tolist(), "imag": eigs.imag.tolist()},
           "is_stable": bool,
           "controllability_rank": int,
           "observability_rank": int,
           "is_controllable": bool,
           "is_observable": bool,
           "design_mode": str,
           "controller": { ... },  # K, L, P, cl_eigs — populated by Task 3
           "error": None or str,
           "state_names": [...],   # from preset
           "input_names": [...],
           "output_names": [...],
       }
   }
   ```

**Key implementation notes:**
- Expression fields use the same `_parse_matrix()` pattern as state_space_analyzer (rows separated by `;`, values by `,`)
- Cap dimensions: N ≤ 8, M ≤ 4, P ≤ 4
- Use `_validate_expression()` with max 512 chars per matrix string
- Preset selection auto-fills all matrix expression fields
- `step_input_channel` slider max must dynamically cap at m-1 (handle via clamp in _compute)
- All numpy output must be `.tolist()`'d for JSON serialization

**Step 2: Verify backend loads without import errors**

Run: `cd /Users/shreyasreddy/Documents/GitHub/sims-dev && python -c "from backend.simulations.mimo_design_studio import MIMODesignStudioSimulator; s = MIMODesignStudioSimulator(); s.initialize(); state = s.get_state(); print('plots:', len(state['plots']), 'meta keys:', list(state['metadata'].keys()))"`
Expected: plots count > 0, metadata keys include simulation_type, n_states, etc.

**Step 3: Commit**

```bash
git add backend/simulations/mimo_design_studio.py
git commit -m "feat: MIMO design studio simulator — analysis mode with presets and plots"
```

---

### Task 3: Extend Simulator — Controller Design Modes (Pole Placement, LQR, LQG)

**Files:**
- Modify: `backend/simulations/mimo_design_studio.py`

**Step 1: Add controller computation methods**

Add these methods to MIMODesignStudioSimulator:

1. **`_compute_pole_placement(data, A, B)`**: Parses `desired_poles` expression into complex array, validates conjugate pairs via `mimo_utils.validate_conjugate_pairs()`, calls `mimo_utils.mimo_pole_placement()`, stores K and cl_eigs in data.

2. **`_compute_lqr(data, A, B)`**: Parses `q_diag` and `r_diag` expressions into diagonal matrices, validates dimensions (len(q_diag)==n, len(r_diag)==m), checks R positive-definite, calls `mimo_utils.mimo_lqr()`, stores K, P, cl_eigs.

3. **`_compute_lqg(data, A, B, C)`**: Parses all four diagonal expressions (q_diag, r_diag, qw_diag, rv_diag), validates, calls `mimo_utils.mimo_lqg()`, stores K, L, P_lqr, P_kal, A_cl, cl_eigs, K_eigs, L_eigs.

4. **`_compute_closed_loop_responses(data, A, B, C, D, K)`**: Given gain K, computes A_cl = A - B@K, then runs `mimo_step_response` and `mimo_impulse_response` on the closed-loop system (A_cl, B, C, D). Stores as `cl_step_responses` and `cl_impulse_responses` in data alongside the open-loop ones.

5. **For LQG closed-loop responses**: The augmented system has 2n states. Build augmented A_cl, B_aug, C_aug from the LQG result and simulate that. This shows the actual LQG performance including estimator transient.

6. **`handle_action()`**: When `compute_controller` button is pressed, trigger recomputation. The button action simply returns `get_state()` which triggers `_compute()` → controller dispatch.

**Key parsing detail for desired_poles:**
```python
def _parse_complex_list(self, expr: str) -> np.ndarray:
    """Parse '-1, -2, -3+1j, -3-1j' into complex array."""
    # Replace common notations: 'i' → 'j', spaces around +/- before j
    expr = expr.replace('i', 'j')
    parts = [p.strip() for p in expr.split(',')]
    return np.array([complex(p) for p in parts if p])
```

**Step 2: Test all three controller modes via Python**

Run:
```bash
cd /Users/shreyasreddy/Documents/GitHub/sims-dev && python -c "
from backend.simulations.mimo_design_studio import MIMODesignStudioSimulator

# Test pole placement
s = MIMODesignStudioSimulator()
s.initialize({'preset': 'aircraft_lateral', 'design_mode': 'pole_placement', 'desired_poles': '-1, -2, -3+1j, -3-1j'})
state = s.handle_action('compute_controller', {})
print('PP K shape:', state['metadata']['controller']['K'] and len(state['metadata']['controller']['K']))

# Test LQR
s2 = MIMODesignStudioSimulator()
s2.initialize({'preset': 'coupled_spring_mass', 'design_mode': 'lqr', 'q_diag': '1,1,1,1', 'r_diag': '1,1'})
state2 = s2.handle_action('compute_controller', {})
print('LQR K shape:', state2['metadata']['controller']['K'] and len(state2['metadata']['controller']['K']))

# Test LQG
s3 = MIMODesignStudioSimulator()
s3.initialize({'preset': 'aircraft_lateral', 'design_mode': 'lqg', 'q_diag': '1,1,1,1', 'r_diag': '1,1', 'qw_diag': '0.1,0.1,0.1,0.1', 'rv_diag': '1,1'})
state3 = s3.handle_action('compute_controller', {})
print('LQG L shape:', state3['metadata']['controller']['L'] and len(state3['metadata']['controller']['L']))
print('All modes OK')
"
```
Expected: All print statements show valid shapes, "All modes OK".

**Step 3: Commit**

```bash
git add backend/simulations/mimo_design_studio.py
git commit -m "feat: MIMO controller design — pole placement, LQR, LQG modes"
```

---

### Task 4: Register Simulator + Add Catalog Entry

**Files:**
- Modify: `backend/simulations/__init__.py`
- Modify: `backend/simulations/catalog.py`

**Step 1: Register in `__init__.py`**

Add import (after the `phase_portrait` import, line 63):
```python
from .mimo_design_studio import MIMODesignStudioSimulator
```

Add to SIMULATOR_REGISTRY (after `"phase_portrait"` entry):
```python
"mimo_design_studio": MIMODesignStudioSimulator,
```

Add to `__all__`:
```python
"MIMODesignStudioSimulator",
```

**Step 2: Add catalog entry in `catalog.py`**

Insert before the closing `]` of SIMULATION_CATALOG (line 3128). The catalog entry must include all controls with proper `visible_when` conditions, groups, and descriptions.

Key controls in catalog:
```python
{
    "id": "mimo_design_studio",
    "name": "MIMO State-Space Design Studio",
    "description": (
        "Design and analyze multi-input multi-output (MIMO) state-space systems. "
        "Enter arbitrary A, B, C, D matrices or select from real-world presets "
        "(aircraft dynamics, coupled oscillators, flexible motor). Compute "
        "controllability/observability, design MIMO controllers via pole placement, "
        "LQR, or LQG, and visualize the full response matrix."
    ),
    "category": "Control Systems",
    "thumbnail": "🎛️",
    "tags": [
        "MIMO", "state space", "multivariable", "pole placement", "LQR",
        "LQG", "Kalman filter", "controllability", "observability",
        "Riccati", "eigenvalues", "modern control", "optimal control",
    ],
    "has_simulator": True,
    "controls": [
        # System group
        {"type": "select", "name": "preset", "label": "System Preset",
         "options": [
             {"value": "aircraft_lateral", "label": "Aircraft Lateral Dynamics (4×2×2)"},
             {"value": "coupled_spring_mass", "label": "Coupled Mass-Spring-Damper (4×2×2)"},
             {"value": "dc_motor_flex", "label": "DC Motor + Flexible Load (4×1×2)"},
             {"value": "custom", "label": "Custom Matrices"},
         ],
         "default": "aircraft_lateral", "group": "System"},

        # Matrix expressions
        {"type": "expression", "name": "matrix_a", "label": "A Matrix (rows ; separated)",
         "default": "-0.322, 0.064, 0.0364, -0.9917; 0, -0.465, 0.0121, 0; -0.015, -0.624, -0.275, 0; 0, 0.018, 0.318, 0",
         "group": "Matrices", "description": "n×n state matrix. Rows separated by semicolons, values by commas."},
        {"type": "expression", "name": "matrix_b", "label": "B Matrix",
         "default": "0, 0.0064; -0.161, 0.0028; 0, -0.264; 0, 0",
         "group": "Matrices", "description": "n×m input matrix."},
        {"type": "expression", "name": "matrix_c", "label": "C Matrix",
         "default": "1, 0, 0, 0; 0, 0, 0, 1",
         "group": "Matrices", "description": "p×n output matrix."},
        {"type": "expression", "name": "matrix_d", "label": "D Matrix",
         "default": "0, 0; 0, 0",
         "group": "Matrices", "description": "p×m feedthrough matrix (usually zeros)."},

        # Design mode
        {"type": "select", "name": "design_mode", "label": "Design Mode",
         "options": [
             {"value": "analysis", "label": "Analysis Only"},
             {"value": "pole_placement", "label": "Pole Placement"},
             {"value": "lqr", "label": "LQR (Optimal)"},
             {"value": "lqg", "label": "LQG (LQR + Kalman Filter)"},
         ],
         "default": "analysis", "group": "Controller Design"},

        # Pole placement controls
        {"type": "expression", "name": "desired_poles", "label": "Desired Poles",
         "default": "-1, -2, -3+1j, -3-1j",
         "group": "Controller Design",
         "description": "Comma-separated desired CL poles. Complex poles need conjugate pairs (e.g. -3+1j, -3-1j).",
         "visible_when": {"design_mode": "pole_placement"}},

        # LQR/LQG cost weights
        {"type": "expression", "name": "q_diag", "label": "Q Diagonal (state cost)",
         "default": "1, 1, 1, 1",
         "group": "Controller Design",
         "description": "Diagonal entries of Q matrix (one per state). Higher = penalize that state more.",
         "visible_when": {"design_mode": ["lqr", "lqg"]}},
        {"type": "expression", "name": "r_diag", "label": "R Diagonal (input cost)",
         "default": "1, 1",
         "group": "Controller Design",
         "description": "Diagonal entries of R matrix (one per input). Higher = cheaper control effort.",
         "visible_when": {"design_mode": ["lqr", "lqg"]}},

        # LQG noise weights
        {"type": "expression", "name": "qw_diag", "label": "Qw Diagonal (process noise)",
         "default": "0.1, 0.1, 0.1, 0.1",
         "group": "Estimator (LQG)",
         "description": "Process noise covariance diagonal. Higher = less trust in model.",
         "visible_when": {"design_mode": "lqg"}},
        {"type": "expression", "name": "rv_diag", "label": "Rv Diagonal (sensor noise)",
         "default": "1, 1",
         "group": "Estimator (LQG)",
         "description": "Measurement noise covariance diagonal. Higher = less trust in sensors.",
         "visible_when": {"design_mode": "lqg"}},

        # Compute button
        {"type": "button", "name": "compute_controller", "label": "Compute Controller",
         "group": "Controller Design",
         "visible_when": {"design_mode": ["pole_placement", "lqr", "lqg"]}},

        # Simulation settings
        {"type": "slider", "name": "time_span", "label": "Time Span", "min": 1, "max": 50,
         "step": 1, "default": 10, "unit": "s", "group": "Simulation"},
        {"type": "slider", "name": "step_input_channel", "label": "Step Input Channel",
         "min": 0, "max": 3, "step": 1, "default": 0, "group": "Simulation",
         "description": "Which input channel receives the unit step (0-indexed)."},
    ],
    "default_params": {
        "preset": "aircraft_lateral",
        "matrix_a": "-0.322, 0.064, 0.0364, -0.9917; 0, -0.465, 0.0121, 0; -0.015, -0.624, -0.275, 0; 0, 0.018, 0.318, 0",
        "matrix_b": "0, 0.0064; -0.161, 0.0028; 0, -0.264; 0, 0",
        "matrix_c": "1, 0, 0, 0; 0, 0, 0, 1",
        "matrix_d": "0, 0; 0, 0",
        "design_mode": "analysis",
        "desired_poles": "-1, -2, -3+1j, -3-1j",
        "q_diag": "1, 1, 1, 1",
        "r_diag": "1, 1",
        "qw_diag": "0.1, 0.1, 0.1, 0.1",
        "rv_diag": "1, 1",
        "time_span": 10,
        "step_input_channel": 0,
    },
    "plots": [
        {"id": "step_response_grid", "title": "MIMO Step Response", "description": "Step response matrix — each subplot shows one output's response to one input's unit step"},
        {"id": "impulse_response_grid", "title": "MIMO Impulse Response", "description": "Impulse response matrix — same grid layout as step response"},
        {"id": "eigenvalue_map", "title": "Eigenvalue Map", "description": "Open-loop (×) and closed-loop (●) eigenvalues in the s-plane"},
    ],
},
```

**Step 3: Verify backend serves the new simulation**

Run: `cd /Users/shreyasreddy/Documents/GitHub/sims-dev && python -c "from backend.simulations.catalog import get_simulation_by_id; s = get_simulation_by_id('mimo_design_studio'); print(s['name'], len(s['controls']), 'controls')"`
Expected: `MIMO State-Space Design Studio 14 controls` (or similar count)

Run: `cd /Users/shreyasreddy/Documents/GitHub/sims-dev && python -c "from backend.simulations import get_simulator_class; cls = get_simulator_class('mimo_design_studio'); s = cls(); s.initialize(); print(s.get_state()['metadata']['simulation_type'])"`
Expected: `mimo_design_studio`

**Step 4: Commit**

```bash
git add backend/simulations/__init__.py backend/simulations/catalog.py
git commit -m "feat: register MIMO design studio in simulator registry and catalog"
```

---

### Task 5: Create `frontend/src/styles/MIMODesignStudio.css`

**Files:**
- Create: `frontend/src/styles/MIMODesignStudio.css`

**Step 1: Write the stylesheet**

Follow existing patterns (reference SteadyStateError.css, ControllerTuningLab.css). Must include:

- `.mimo-studio` root container
- `.mimo-tabs` / `.mimo-tab` / `.mimo-tab.active` — tab navigation bar
- `.mimo-tab-content` — tab panel container
- `.mimo-metrics-strip` — horizontal metrics bar below tabs
- `.mimo-metric` / `.mimo-metric-label` / `.mimo-metric-value` — individual metric items
- `.mimo-response-grid` — container for the p×m subplot grid
- `.mimo-matrix-panel` — KaTeX matrix display area
- `.mimo-matrix-card` — individual matrix card (A, B, C, D, K, L, P)
- `.mimo-rank-badge` / `.mimo-rank-full` / `.mimo-rank-deficient` — controllability/observability rank badges
- `.mimo-diagram-container` — SVG block diagram area
- `.mimo-controller-info` — controller results panel (K, P, eigenvalues)
- `.mimo-warning` — warning messages (uncontrollable, Riccati failure)
- `.mimo-dimension-badge` — N×M×P dimension display
- Dark/light theme variants via `[data-theme="light"]` selectors
- All colors via CSS variables (--primary-color, --success-color, --warning-color, --error-color, etc.)
- Responsive: stack plots vertically below 768px

**Step 2: Commit**

```bash
git add frontend/src/styles/MIMODesignStudio.css
git commit -m "feat: add MIMO design studio stylesheet"
```

---

### Task 6: Create `frontend/src/components/MIMODesignStudioViewer.jsx` — Core Viewer

**Files:**
- Create: `frontend/src/components/MIMODesignStudioViewer.jsx`

**Step 1: Write the viewer component**

Structure (follow StateSpaceViewer.jsx and ControllerTuningLabViewer.jsx patterns):

```jsx
// Top-level: MIMODesignStudioViewer receives { metadata, plots, onParamChange }
// Internal components:
//   - useTheme() hook (same pattern as StateSpaceViewer)
//   - LaTeX helper component (same pattern)
//   - MatrixKaTeX component — renders a matrix with KaTeX bmatrix
//   - MetricsStrip — horizontal bar with dimension, rank, stability badges
//   - ResponseTab — renders step + impulse response Plotly subplots
//   - PoleZeroTab — eigenvalue map with OL/CL overlay
//   - PropertiesTab — matrices, controllability/observability display
//   - ControllerTab — K, P, L matrices, CL eigenvalues
//   - DiagramTab — SVG block diagrams (3 variants)
```

Key implementation details:

1. **Tab system**: 5 tabs (Response, Pole-Zero, Properties, Controller, Diagram). Use useState for active tab. Controller and Diagram tabs only enabled when design_mode !== "analysis".

2. **ResponseTab**: Receives step/impulse response data from metadata. Renders two Plotly plots (step grid, impulse grid). Each plot uses Plotly subplots — configure via layout with `xaxis`, `xaxis2`, ... `yaxis`, `yaxis2`, etc. and `data` array with `xaxis: "x1"`, `yaxis: "y1"` references.

   For p outputs × m inputs, generate subplot grid annotations:
   - Column headers: "Input 1", "Input 2", ...
   - Row headers: "Output 1", "Output 2", ...
   - Each cell: trace for OL (dashed, blue `#3b82f6`) + CL (solid, green `#10b981`) if controller active

3. **PoleZeroTab**: Single Plotly scatter plot. OL eigenvalues as `×` markers (red `#ef4444`), CL eigenvalues as `●` markers (green `#10b981`). Draw jω axis (vertical line at Re=0). Annotate stable/unstable half-planes.

4. **PropertiesTab**: KaTeX display of A, B, C, D matrices, controllability matrix (or just its rank if too large), observability matrix, state/input/output names from preset.

5. **ControllerTab**: KaTeX display of K, P, L matrices. CL eigenvalues list. For LQR: show Q, R diagonal visualized as `Q = diag(...)`. For LQG: show Qw, Rv too. Performance: dominant pole time constant, settling time estimate.

6. **DiagramTab**: Three SVG variants based on design_mode:
   - Analysis: `u → [B] → Σ → ∫ → x → [C] → y` with `[A]` feedback
   - State Feedback: `r → Σ → [B] → Plant(A) → x → [C] → y`, `x → [-K] → Σ`
   - LQG: Full observer structure with plant, Kalman filter `(Â = (A-LC)x̂ + Bu + Ly)`, and K gain

   SVGs use the same pattern as ControllerTuningLabViewer's SVG diagrams — KaTeX-rendered labels via foreignObject elements, arrows as `<line>` with `marker-end`, blocks as `<rect>` with rounded corners.

7. **MetricsStrip** (always visible):
   - `n×m×p` dimension badge
   - Controllability: `rank(C) = r/n` with green/red coloring
   - Observability: `rank(O) = r/n` with green/red coloring
   - OL Stability: stable/unstable/marginal badge
   - When controller active: CL Stability badge, dominant τ

**Step 2: Verify the component renders without errors**

Start the frontend dev server and navigate to `/simulation/mimo_design_studio`. Check browser console for React errors.

Run: `cd /Users/shreyasreddy/Documents/GitHub/sims-dev/frontend && npm run dev`
Then verify in browser.

**Step 3: Commit**

```bash
git add frontend/src/components/MIMODesignStudioViewer.jsx
git commit -m "feat: MIMO design studio viewer with tabbed layout and response grid"
```

---

### Task 7: Wire Viewer into SimulationViewer.jsx

**Files:**
- Modify: `frontend/src/components/SimulationViewer.jsx`

**Step 1: Add lazy import**

After the `PhasePortraitViewer` lazy import (line 63), add:
```javascript
const MIMODesignStudioViewer = lazy(() => import('./MIMODesignStudioViewer'));
```

**Step 2: Add to viewer chain**

After the `phase_portrait` viewer chain entry (around line 2027-2035), add:
```jsx
) : metadata?.simulation_type === 'mimo_design_studio' ? (
  <Suspense fallback={<LazyLoadFallback />}>
    <MIMODesignStudioViewer
      metadata={metadata}
      plots={plots}
      onParamChange={onParamChange}
    />
  </Suspense>
```

**Step 3: Add to no-controls class list if needed**

Check if MIMO studio needs the no-controls class — it shouldn't, since it has a ControlPanel with sliders/selects. No change needed here.

**Step 4: Verify end-to-end**

Start backend and frontend:
```bash
cd /Users/shreyasreddy/Documents/GitHub/sims-dev/backend && python -m uvicorn main:app --reload --port 8000
cd /Users/shreyasreddy/Documents/GitHub/sims-dev/frontend && npm run dev
```

Navigate to `/simulation/mimo_design_studio`:
1. Default loads aircraft lateral preset — verify 2×2 response grid renders
2. Switch preset to coupled_spring_mass — verify matrices update
3. Switch preset to dc_motor_flex — verify 1×2 response grid (MISO)
4. Set design_mode to "lqr" — verify Q/R controls appear
5. Click "Compute Controller" — verify CL response overlaid on response grid
6. Switch to LQG — verify Qw/Rv controls appear, compute works

**Step 5: Commit**

```bash
git add frontend/src/components/SimulationViewer.jsx
git commit -m "feat: wire MIMO design studio viewer into SimulationViewer chain"
```

---

### Task 8: Polish & Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md` — add to "Recent Features Added" section

**Step 1: Add feature entry to CLAUDE.md**

```markdown
### MIMO State-Space Design Studio (simulation: `mimo_design_studio`)
- **Backend**: `backend/simulations/mimo_design_studio.py` (~1000-1200 lines), `backend/core/mimo_utils.py` (~300 lines)
- **Frontend**: `frontend/src/components/MIMODesignStudioViewer.jsx` (~800-1000 lines)
- **CSS**: `frontend/src/styles/MIMODesignStudio.css` (~400 lines)
- **Purpose**: Full MIMO state-space design and analysis for arbitrary N×M×P systems
- **Key features**:
  - 3 real-world presets: Aircraft Lateral (4×2×2), Coupled Mass-Spring-Damper (4×2×2), DC Motor + Flex Load (4×1×2 MISO)
  - Custom N×M×P matrices via semicolon-delimited expressions (max N=8, M=4, P=4)
  - Controllability/observability matrix computation and rank display
  - MIMO pole placement via scipy.signal.place_poles (m×n K matrix)
  - MIMO LQR via continuous Riccati equation (arbitrary Q, R diagonal)
  - MIMO LQG: dual Riccati (K + L gains), augmented 2n-order CL simulation
  - p×m response grid: step and impulse response for every input→output pair
  - Open-loop + closed-loop eigenvalue overlay on s-plane
  - SVG block diagrams: open-loop SS, state feedback, LQG observer structure
  - KaTeX-rendered matrices (A, B, C, D, K, L, P, Q, R) throughout
  - Metrics strip: dimensions, controllability/observability rank badges, stability
```

**Step 2: Commit all remaining changes**

```bash
git add CLAUDE.md
git commit -m "docs: add MIMO design studio to recent features"
```

---

### Task 9: End-to-End Verification

**No files to modify — verification only.**

**Step 1: Start backend**
```bash
cd /Users/shreyasreddy/Documents/GitHub/sims-dev/backend && python -m uvicorn main:app --reload --port 8000
```

**Step 2: Start frontend**
```bash
cd /Users/shreyasreddy/Documents/GitHub/sims-dev/frontend && npm run dev
```

**Step 3: Verify all presets and modes**

Manual checklist:
- [ ] Aircraft Lateral preset loads, 2×2 step response grid renders
- [ ] Coupled Mass-Spring-Damper preset loads, matrices update correctly
- [ ] DC Motor + Flex Load preset loads, shows 1×2 MISO response grid
- [ ] Custom mode: can type arbitrary matrices, computes after update
- [ ] Pole placement: enter 4 poles, compute → K displayed, CL response overlaid
- [ ] LQR: enter Q/R diagonals, compute → K/P displayed, CL eigenvalues shown
- [ ] LQG: enter Q/R/Qw/Rv, compute → K/L/P displayed, LQG response shown
- [ ] Eigenvalue map shows OL × and CL ● markers correctly
- [ ] Properties tab shows controllability/observability matrices and ranks
- [ ] Controller tab shows gain matrices with KaTeX rendering
- [ ] Diagram tab shows correct SVG for each design mode
- [ ] Metrics strip updates with all badges
- [ ] Uncontrollable system shows warning (modify A to make rank-deficient)
- [ ] Invalid dimensions show clear error message
- [ ] Dark/light theme toggle works
- [ ] Mobile responsive below 768px

**Step 4: Fix any issues found, commit fixes**
