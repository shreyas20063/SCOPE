# SCOPE — Browser-Native Platform for Control Systems Analysis and Design

A free, browser-native platform for control systems analysis and design that requires no installation, no license, and no programming. Starting from a plant description, SCOPE supports the complete control design workflow: transfer function specification, block diagram construction, signal flow graph analysis, comprehensive stability analysis, controllability/observability assessment, steady-state error analysis, classical and modern controller design, reinforcement-learning auto-tuning, and 3D physical system visualization.

A cross-simulation data hub automatically propagates and enriches system representations across the platform, eliminating manual re-entry between tools.

**Paper**: *A Browser-Native Platform for Control Systems Analysis and Design*
**Authors**: Shreyas Reddy Duggimpudi and Ameer K. Mulla, IIT Dharwad

## Quick Start

```bash
# Backend
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install && npm run dev
# Open http://localhost:3001
```

## Platform Overview

**54 interactive simulations** organized into four sections:

### Design Pipeline (14 tools)

The complete control systems workflow, end to end:

| Step | Tool | What it does |
|------|------|-------------|
| 1 | **Block Diagram Builder** | Drag-and-drop block construction with auto TF computation via Mason's gain formula. SFG toggle for signal flow graph view. |
| 2 | **Signal Flow Scope** | Import diagrams, apply input signals, probe any node to visualize signal propagation. |
| 3 | **Root Locus Analyzer** | Evans root locus with breakaway points, asymptotes, jw crossings, K-sweep animation, step response sync. |
| 4 | **Routh-Hurwitz** | Step-by-step Routh array construction with sign-change highlighting and parametric K analysis. |
| 5 | **Nyquist Stability Criterion** | D-contour mapping, encirclement counting, N=Z-P relationship, gain variation effects. |
| 6 | **Nyquist-Bode Comparison** | Side-by-side Nyquist and Bode with synchronized frequency highlighting, GM/PM visualization. |
| 7 | **State Space Analyzer** | Full state-space workbench: TF or matrix input, eigenvalue map, step/impulse response, Bode, phase portrait. |
| 8 | **Steady-State Error Analyzer** | System type classification, error constants (Kp, Kv, Ka), gain-error-stability tradeoff visualization. |
| 9 | **Controller Tuning Lab** | PID + Lead-Lag + LQR/LQG/pole placement. Six auto-tuning methods. RL-based auto-tuning (ES + PPO). |
| 10 | **Lead-Lag Compensator Designer** | Frequency-domain design with Bode, Nichols, step analysis, phase contribution breakdown. |
| 11 | **Nonlinear Control Lab** | Linearize at equilibria (SymPy Jacobian), design LQR/pole-placement, validate linear vs nonlinear side-by-side. |
| 12 | **Phase Portrait Analyzer** | 2D nonlinear dynamical systems: vector fields, trajectories, equilibrium classification via Jacobian eigenvalues. |
| 13 | **MIMO Design Studio** | Arbitrary N x M x P state-space design: pole placement, LQR, LQG, response grids, SVG block diagrams. |
| 14 | **Furuta Pendulum** | 3D rotary inverted pendulum with PID control, real-time Three.js visualization. |

### Analytical Tools (11 tools)

Interactive solvers and exploration workbenches:

- **DT Difference Equation Solver** — Step-by-step evaluation with synchronized block diagram
- **Operator Algebra Visualizer** — R-operator polynomial expansion, factoring, block diagrams
- **Cyclic Path Detector** — FIR/IIR classification with quiz mode
- **Polynomial Multiplication** — Tabular anti-diagonal method visualization
- **Cascade & Parallel Decomposition** — Second-order factoring and partial fractions
- **DT System Representation Navigator** — Five equivalent representations simultaneously
- **Filter Design Tool** — S-plane pole/zero placement with frequency response
- **Vector Diagram Frequency Response** — Animated vectors tracing magnitude and phase
- **Eigenfunction Tester Lab** — Verify eigenfunctions of LTI systems
- **Inverse Z Transform Solver** — Step-by-step partial fractions and ROC matching
- **ODE Solver via Laplace** — Full Laplace pipeline: L{} -> Y(s) -> PFE -> L^-1 -> y(t)

### System Simulations (10 simulations)

Physical systems — circuits, motors, pendulums, optics:

- **RC Lowpass Filter** — Frequency response and square wave filtering
- **Amplifier Topologies** — Simple, feedback, push-pull, compensated designs
- **DC Motor Feedback Control** — Pole-zero maps and step response analysis
- **Feedback System Analysis** — Open-loop vs closed-loop comparison
- **Second-Order System Response** — Q-factor, resonance, damping behavior
- **Spring Mass Damper System** — Animated physical system with base excitation
- **Complex Poles & Sinusoidal Modes** — Complex exponential mode superposition, 3D helix
- **Resonance Anatomy Explorer** — Three characteristic frequencies of H(s)
- **Delay Effect: Domino of Instability** — Sensor delay destroying dead-beat control
- **Lens Optics** — Convolution-based optical modeling with Airy disk PSF

### Signal Explorations (19 simulations)

Signals, sampling, Fourier, Z-transforms, Laplace:

- **Aliasing & Quantization** — Nyquist theorem, dither, Robert's method, image quantization
- **Convolution Simulator** — Continuous and discrete convolution step-by-step
- **Modulation Techniques** — AM, FM/PM, FDM with real audio
- **Signal Operations Explorer** — Time-scaling, shifting, reversal, even/odd decomposition
- **Sampling & Reconstruction** — ZOH, linear interpolation, sinc reconstruction
- **Feedback & Convergence Explorer** — Geometric sequences from feedback loops
- **Pole Behavior Explorer** — Drag poles to see convergence/divergence in real time
- **Fundamental Modes Superposition** — Nth-order response as weighted mode sum
- **DT <-> CT Comparator** — Same pole value, two different stability worlds
- **Unit Impulse Construction** — Rectangular pulses converging to delta(t)
- **CT Impulse Response Builder** — Taylor series buildup of e^(pt)u(t)
- **Fourier Series** — Harmonic decomposition and convergence
- **Fourier Phase vs Magnitude** — Phase dominance in structural perception
- **Z-Transform Properties Lab** — Linearity, delay, convolution in z-domain
- **Z Transform & ROC Explorer** — Interactive z-plane with ROC selection
- **Laplace Transform & ROC Explorer** — S-plane pole manipulation and ROC regions
- **Laplace Properties Lab** — Seven Laplace transform properties
- **Initial & Final Value Theorem** — Kernel visualization, failure mode demos
- **CT/DT Poles Conversion** — Forward Euler, Backward Euler, Trapezoidal methods

## System Hub

The cross-simulation data hub connects all tools in the design pipeline. When a user pushes a plant from any simulation, the hub:

1. **Validates and enriches** — derives TF <-> SS cross-representation, computes poles, zeros, stability, controllability, observability
2. **Persists in localStorage** — works across tabs, no backend state needed
3. **Auto-loads on mount** — the next simulation opened reads from the hub and pre-populates its parameters
4. **Detects stale controllers** — if the plant changes, existing controller data is flagged stale

Four typed slots: `control`, `signal`, `circuit`, `optics`. The control slot is the most developed, supporting full TF/SS/poles/zeros/properties enrichment.

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Backend** | Python 3.11, FastAPI, NumPy, SciPy, SymPy, Pillow |
| **Frontend** | React 18, Vite 5, Plotly.js, Three.js, KaTeX, axios |
| **Compute** | SciPy (solve_ivp, place_poles, solve_continuous_are, tf2ss), SymPy (symbolic Jacobians) |

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/simulations` | List all simulations with section info |
| GET | `/api/simulations/{id}/state` | Current state (parameters, plots, metadata) |
| POST | `/api/simulations/{id}/execute` | Execute action (init, update, run, reset, to_hub_data, from_hub_data) |
| POST | `/api/simulations/{id}/update` | Update parameters |
| POST | `/api/hub/validate` | Validate and enrich hub data |
| WS | `/api/simulations/{id}/ws` | Real-time WebSocket updates |

## License

MIT
