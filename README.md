# SCOPE

> **📄 Part of an IEEE CDC submission — currently under review.**
> This work is submitted to the IEEE Conference on Decision and Control (CDC)
> and is undergoing peer review. Citations and academic discussion welcome.

A browser-native platform for control systems analysis and design. No installation, no programming, no license key — open a browser and go.

SCOPE covers the complete control workflow — plant specification, system analysis, controller design, and closed-loop validation — for SISO and MIMO, linear and nonlinear systems. It includes 54 interactive tools and simulations, a drag-and-drop block diagram editor, real-time 3D animations of five canonical plants, and a shared data hub that propagates plant data between tools automatically so you never re-enter it.

## Quick Start

```bash
# Backend
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install && npm run dev
```

Open **http://localhost:3001**. That's it — no API keys, no accounts, no configuration.

## Features

### Plant modeling
- Transfer functions (SISO and MIMO transfer matrices)
- Drag-and-drop block diagram builder with auto-reduction via Mason's gain formula
- State-space matrices `(A, B, C, D)`
- Symbolic nonlinear ODE entry

### System analysis
- State-space analyzer — poles, zeros, eigenvalues, controllability/observability, canonical forms, minimal realizations
- Routh–Hurwitz with step-by-step array construction and parametric K analysis
- Bode, Nyquist, and side-by-side Nyquist–Bode comparison
- Root locus with breakaway points, asymptotes, jω crossings, and K-sweep animation
- Steady-state error analyzer (system type, Kp/Kv/Ka)
- Signal flow graph with node-level probing
- Phase portrait analyzer for 2D nonlinear systems with automatic equilibrium classification

### Controller design
- PID with six auto-tuning methods: Ziegler–Nichols (open/closed), Cohen–Coon, Lambda, IMC, ITAE-optimal
- Lead-lag compensator designer with Bode and Nichols views
- Pole placement (SISO and MIMO)
- LQR and LQG (LQR + Kalman filter observer)
- MIMO Design Studio for arbitrary N×M×P systems
- Controller comparison view — overlay up to five designs with a side-by-side metrics table

### Validation
- Linear vs. nonlinear side-by-side response comparison
- Region-of-attraction heatmap across a grid of initial conditions

### Real-time 3D plants
Five canonical plants rendered with Three.js where you can swap controllers and watch the physical response:
- Inverted pendulum
- Furuta pendulum
- Ball-and-beam
- Coupled two-tank system
- Mass-spring-damper

### Signal processing and transforms
Convolution, sampling and reconstruction, modulation (AM / FM / PM / FDM), Fourier series, Z-transform and ROC explorer, Laplace transform and ROC explorer, initial/final value theorems, aliasing and quantization, and more — 30+ additional simulations alongside the control systems tools.

## Architecture

A single-page React app talking to a FastAPI/Python backend over REST and WebSocket.

**Tool engine.** Each tool is a Python `BaseSimulator` subclass that declares a parameter schema (types, ranges, defaults, conditional visibility) and implements `initialize`, `update_parameter`, and `get_plots`. Numerical computation uses SciPy and SymPy. Inputs are schema-validated and every request is wrapped in a 30-second timeout.

**System Hub.** A shared data layer persisted in browser `localStorage` and synced across tabs. When you push a plant from any tool, the backend derives the remaining representations (TF ↔ SS, poles/zeros, controllability/observability, stability) and every other tool reads from the hub automatically. Successive pushes are deep-merged, so pushing a controller doesn't overwrite the plant.

**Frontend.** Reads each tool's parameter schema and auto-generates its controls, giving every tool a consistent interaction model. Plots are Plotly, 3D scenes are Three.js, equations are rendered with KaTeX. Parameter updates debounce to a single batched request within 150 ms and preserve zoom/pan state across updates.

## Tech Stack

| Layer | Technologies |
|---|---|
| Backend | Python 3.11, FastAPI, NumPy, SciPy, SymPy, Pillow |
| Frontend | React 18, Vite 5, Plotly.js, Three.js, KaTeX, axios |
| Compute | SciPy (`solve_ivp`, `place_poles`, `solve_continuous_are`, `tf2ss`), SymPy (symbolic Jacobians) |
| Transport | REST + WebSocket |

## API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/simulations` | List all tools |
| `GET` | `/api/simulations/{id}/state` | Current state (parameters, plots, metadata) |
| `POST` | `/api/simulations/{id}/execute` | Run action (`init`, `update`, `run`, `reset`, `to_hub_data`, `from_hub_data`) |
| `POST` | `/api/simulations/{id}/update` | Update parameters |
| `POST` | `/api/hub/validate` | Validate and enrich hub data |
| `WS` | `/api/simulations/{id}/ws` | Real-time updates |

## Project Layout

```
backend/
  simulations/      # One file per tool — each is a BaseSimulator subclass
  core/             # Executor, data handler, MIMO utils, Routh-Hurwitz
  routes/           # Hub + simulation endpoints
  main.py           # FastAPI entry point
frontend/
  src/
    components/     # Per-tool viewers (Plotly, Three.js, custom SVG)
    pages/          # Landing page + simulation page
    hooks/          # useSimulation, useHub
    contexts/       # HubContext
    services/       # API client
```

## Adding a New Simulation

1. Create `backend/simulations/<sim_id>.py` subclassing `BaseSimulator` — declare `PARAMETER_SCHEMA`, `DEFAULT_PARAMS`, and implement `initialize`, `update_parameter`, `get_plots`, `get_state`.
2. Register it in `backend/simulations/__init__.py` (add import, entry in `SIMULATOR_REGISTRY`, and `__all__`).
3. Add a catalog entry in `backend/simulations/catalog.py` — name, description, category, controls, default params, plots.
4. Optionally add a custom viewer in `frontend/src/components/<Name>Viewer.jsx` and wire it into the viewer chain in `SimulationViewer.jsx`.

## Status & License

**Submission status.** This repository accompanies a manuscript submitted to
the IEEE Conference on Decision and Control (CDC) and is currently under
peer review. If you use the code or ideas in published work, please cite
the paper once it is out.

**License.** Released under the [MIT License](LICENSE).
