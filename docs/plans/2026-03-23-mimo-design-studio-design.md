# MIMO State-Space Design Studio — Design Document

**Date:** 2026-03-23
**Simulation ID:** `mimo_design_studio`
**Category:** Control Systems

## Overview

Standalone MIMO state-space design tool. Users select or enter arbitrary N-state, M-input, P-output systems, then analyze and design controllers (pole placement, LQR, LQG) with full visualization of the MIMO response matrix.

## Architecture

```
backend/
  core/mimo_utils.py                    (~300 lines)  — pure MIMO math utilities
  simulations/mimo_design_studio.py     (~1000-1200 lines) — simulator class

frontend/
  src/components/MIMODesignStudioViewer.jsx  (~800-1000 lines) — tabbed viewer
  src/styles/MIMODesignStudio.css            (~400 lines)
```

### core/mimo_utils.py

Pure NumPy/SciPy module, no BaseSimulator dependency. Functions:

- `controllability_matrix(A, B)` → n × (n·m)
- `observability_matrix(A, C)` → (n·p) × n
- `mimo_step_response(A, B, C, D, t_eval)` → dict per input/output pair via solve_ivp RK45
- `mimo_impulse_response(A, B, C, D, t_eval)` → same structure
- `mimo_lqr(A, B, Q, R)` → K, P, CL eigenvalues
- `mimo_lqg(A, B, C, Q_lqr, R_lqr, Qw, Rv)` → K, L, P_lqr, P_kal, A_cl augmented
- `mimo_pole_placement(A, B, desired_poles)` → K matrix

## Presets

| Preset | N | M | P | Description |
|--------|---|---|---|-------------|
| Aircraft Lateral Dynamics | 4 | 2 | 2 | sideslip, roll rate, yaw rate, roll angle / aileron, rudder |
| Coupled Mass-Spring-Damper | 4 | 2 | 2 | x₁, v₁, x₂, v₂ / F₁, F₂ |
| DC Motor + Flexible Load | 4 | 1 | 2 | θ_m, ω_m, θ_L, ω_L / voltage (MISO) |
| Custom | var | var | var | User enters A, B, C, D as semicolon-delimited expressions |

## Controls

| Group | Control | Type |
|-------|---------|------|
| System | Preset | select |
| System | N×M×P display | (read-only in viewer) |
| Matrices | A, B, C, D | expression (semicolon-delimited) |
| Design | Mode | select: Analysis / Pole Placement / LQR / LQG |
| Pole Placement | Desired poles | expression (e.g. `-1, -2, -3+1j, -3-1j`) |
| Pole Placement | Compute K | button |
| LQR | Q diagonal | expression (e.g. `1, 1, 1, 1`) |
| LQR | R diagonal | expression (e.g. `1, 1`) |
| LQR | Compute K | button |
| LQG | Q diagonal (LQR) | expression |
| LQG | R diagonal (LQR) | expression |
| LQG | Qw diagonal (process noise) | expression |
| LQG | Rv diagonal (measurement noise) | expression |
| LQG | Compute LQG | button |
| Simulation | Time span | slider (1–50s) |
| Simulation | Step input channel | select (which input gets the unit step) |

Q/R/Qw/Rv are expression fields (not individual sliders) to handle arbitrary dimensions.

## Viewer Tabs

| Tab | Content |
|-----|---------|
| Response | MIMO step response grid (p×m subplots), impulse response grid. OL dashed + CL solid when controller active |
| Pole-Zero | Eigenvalue map — OL (×) + CL (●) overlaid. Unit circle, jω axis |
| Properties | Controllability matrix + rank, Observability matrix + rank, KaTeX-rendered A/B/C/D, stability info |
| Controller | K matrix (KaTeX), P matrix, L matrix (LQG), CL eigenvalues, performance metrics |
| Diagram | SVG block diagram — 3 variants: open-loop SS, state feedback (K), LQG (K + Kalman filter) |

### Response Grid Layout

For 2-input, 2-output:
```
         Input 1          Input 2
Output 1 [y₁ from u₁]    [y₁ from u₂]
Output 2 [y₂ from u₁]    [y₂ from u₂]
```

### SVG Diagrams

1. **Analysis**: u → [B] → ∫ → [A] → [C] → y
2. **State Feedback**: r → Σ → [B] → plant → x → [C] → y, x → [-K] → Σ
3. **LQG**: plant + Kalman estimator + K, separation principle layout

### Metrics Strip

Always visible below plots:
- Dimensions: n/m/p
- Controllability rank / n (color-coded)
- Observability rank / n (color-coded)
- OL stability (eigenvalue summary)
- CL stability + dominant pole τ (when controller active)

## Error Handling

- Dimension mismatch: clear error messages ("B must have N rows to match A")
- Uncontrollable: warning badge, still compute partial result
- Riccati non-convergence: catch, display "adjust Q/R weights"
- Complex poles: validate conjugate pairs for real K
- Dimension caps: N ≤ 8, M ≤ 4, P ≤ 4
- Singular R: check positive-definiteness before Riccati

## Data Flow

```
Param change → POST /update → _compute():
  1. Parse matrices from expressions
  2. Validate dimensions (A: n×n, B: n×m, C: p×n, D: p×m)
  3. Eigenvalues of A, controllability/observability ranks
  4. If design_mode != analysis: compute K (and L for LQG)
  5. Build A_cl = A - BK, simulate OL + CL responses
  6. Generate all Plotly plots
  7. Assemble metadata (matrices, gains, eigenvalues, ranks, LaTeX)
→ JSON {plots, metadata} → Viewer renders tabs
```
