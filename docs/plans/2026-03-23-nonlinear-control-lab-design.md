# Nonlinear Control Lab Design

**Simulation ID**: `nonlinear_control_lab`
**Category**: Control Systems
**Date**: 2026-03-23

## Purpose

Linearize a nonlinear plant at an equilibrium, design a controller (LQR/pole placement) on the linearization, validate on the true nonlinear dynamics, visualize the region of attraction. All in-browser, zero installation. Bridges linear and nonlinear control in one interactive workflow.

## Files

| File | Lines | Role |
|------|-------|------|
| `backend/simulations/nonlinear_control_lab.py` | ~1400 | Simulator: plants, Jacobian, controller design, solve_ivp, ROA |
| `frontend/src/components/NonlinearControlLabViewer.jsx` | ~700 | Custom viewer: Canvas phase portrait, Plotly plots, KaTeX panels |
| `frontend/src/styles/NonlinearControlLab.css` | ~400 | Styling |

## Plant Presets

| Preset | States | Inputs | Equilibria |
|--------|--------|--------|------------|
| Inverted pendulum on cart | 4 (x, ẋ, θ, θ̇) | 1 (F) | Upright (θ=π), Hanging (θ=0) |
| Ball and beam | 4 (r, ṙ, α, α̇) | 1 (τ) | Ball at center (r=0) |
| Coupled tanks (MIMO) | 2 (h₁, h₂) | 2 (q₁, q₂) | Equal heights |
| Van der Pol + input | 2 (x, ẋ) | 1 (u) | Origin |

Custom ODE: user expressions parsed via `sympy.sympify`, 2-4 states, 1-2 inputs.

## Linearization

SymPy symbolic Jacobian (exact, not finite-difference). Produces A = ∂f/∂x, B = ∂f/∂u at selected equilibrium. C = I (full state feedback), D = 0. Controllability rank check.

## Controller Design

- **Pole Placement**: `scipy.signal.place_poles`, user specifies desired CL poles, conjugate pairs enforced
- **LQR**: `scipy.linalg.solve_continuous_are`, Q diagonal (log-scale sliders per state), R diagonal (per input)
- K matrix displayed via KaTeX, CL eigenvalues computed

## Simulation

- **Linear**: Matrix exponential `scipy.linalg.expm` for clean analytical curves
- **Nonlinear**: `solve_ivp` RK45 adaptive step, u = -K(x - x_eq) + u_eq
- **ROA**: 25×25 grid of ICs, each run via solve_ivp, classified converged/diverged/marginal. ThreadPoolExecutor(8) for parallelism. Triggered by explicit button (not live).

## Frontend Layout

- **Phase portrait (Canvas, 60% width)**: Vector field arrows, streamlines (RK4 JS-side), equilibria markers, animated trajectory, linear overlay (dashed), ROA heatmap overlay. Click-to-set IC. User-selectable 2D projection axes.
- **Plotly plots (40% width, stacked)**: Time responses (linear dashed vs nonlinear solid), control effort, eigenvalue map
- **Below**: Metrics strip, KaTeX derivation chain (ODE → A,B → K → CL eigenvalues)
- **ROA heatmap**: Full-width Plotly contour, shown after button press

## Control Groups

| Group | Controls |
|-------|----------|
| Plant | preset, custom ODE expressions |
| Equilibrium | equilibrium selector, projection axes |
| Controller | method (PP/LQR), desired poles, Q/R weights |
| Simulation | IC offsets, sim time, perturbation magnitude |
| Display | show_linear_overlay, show_vector_field, show_streamlines |

## Key Decisions

- SymPy for exact Jacobians (CDC credibility)
- Canvas for phase portrait (performance with 400+ arrows + streamlines)
- ROA as explicit button (625 solve_ivp calls ~2-5s)
- Backend sends vector field grid data; Canvas renders frontend-side
- MIMO uniform: K always a matrix, same code path for SISO/MIMO
- Thread pool for ROA parallelism
