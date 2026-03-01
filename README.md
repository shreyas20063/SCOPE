# Signals & Systems — Interactive Web Simulations

A comprehensive collection of **44 interactive simulations** for learning Signals and Systems through hands-on exploration. Built as a full-stack web platform with real-time visualization, 3D rendering, and WebSocket-driven interactivity.

## Course Information

- **Course**: Signals and Systems
- **Author**: Shreyas Reddy

## Features

- **44 Interactive Simulations** across 5 categories
- **Real-Time Visualization** — Plotly.js charts with live parameter updates
- **3D Rendering** — Three.js for Furuta Pendulum and complex systems
- **Block Diagram Builder** — Drag-and-drop with automatic transfer function computation
- **Quiz Modes** — Test understanding in Signal Operations, Pole Behavior, and more
- **Dark/Light Theme** — Full theme support with CSS variables
- **Responsive Design** — Desktop and mobile layouts

## Quick Start

```bash
# Clone
git clone https://github.com/shreyas-reddy/signals-and-systems.git
cd signals-and-systems

# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --port 8000 --reload

# Frontend (new terminal)
cd frontend
npm install && npm run dev
# Open http://localhost:3001
```

## Simulation Catalog

### Signal Processing (18 simulations)

| # | Simulation | Description |
|---|-----------|-------------|
| 1 | **Aliasing & Quantization** | Explore the Nyquist theorem, aliasing effects, and compare quantization methods (Standard, Dither, Robert's). Features audio aliasing, audio quantization, and image quantization demos. |
| 2 | **Convolution Simulator** | Visualize continuous and discrete convolution operations step-by-step with interactive animations. |
| 3 | **Modulation Techniques** | Explore AM, FM/PM, and FDM modulation with real audio. Switch between Amplitude Modulation, Frequency/Phase Modulation, and Frequency Division Multiplexing demos. |
| 4 | **Signal Operations Explorer** | Interactive canvas for signal transformations: time-scaling, time-shifting, time-reversal, amplitude scaling, DC offset. Apply chains of operations, view overlays, analyze signal metrics, and explore even/odd decomposition. Includes quiz mode. |
| 5 | **Sampling & Reconstruction** | Explore how sampling interval affects signal reconstruction fidelity. Compare zero-order hold, linear interpolation, and ideal sinc reconstruction. Visualize the Nyquist criterion in action. |
| 6 | **Feedback & Convergence Explorer** | Explore how a single feedback loop with gain p₀ creates geometric sequences. Watch y[n] = p₀ⁿ converge or diverge as you adjust the pole and trace the signal path cycle by cycle. |
| 7 | **DT Difference Equation Solver** | Step-by-step evaluation of discrete-time difference equations with synchronized block diagram visualization. Watch signal values propagate through gain, delay, and adder blocks one sample at a time. |
| 8 | **Polynomial Multiplication** | Visualize the tabular/anti-diagonal method for multiplying operator series. Watch how collecting terms along anti-diagonals produces the combined unit-sample response of cascaded first-order systems. |
| 9 | **Operator Algebra Visualizer** | Explore R-operator (delay operator) algebra. Type an operator polynomial and instantly see the expanded form, factored form, difference equation, block diagram, and impulse response. |
| 10 | **Pole Behavior Explorer** | Drag a pole along the real number line and watch the first-order DT system response update in real time. See how pole location determines convergence, divergence, and alternating-sign behavior. Includes quiz mode. |
| 11 | **Cyclic Path Detector** | Detect cyclic signal paths in block diagrams. Identify feedback loops, classify systems as FIR or IIR, and test your understanding in quiz mode. |
| 12 | **Cascade & Parallel Decomposition** | Decompose a second-order DT system into cascade (series) and parallel (partial fraction) forms. Watch step-by-step factoring and verify all three representations produce the same impulse response. |
| 13 | **Fundamental Modes Superposition** | Visualize how any Nth-order DT system's unit-sample response is a weighted sum of N fundamental modes. Adjust poles and weights to see how individual modes Aₖ·pₖⁿ combine. |
| 14 | **DT ↔ CT Comparator** | Side-by-side comparison of first-order DT and CT systems sharing the same pole value p. See how pⁿu[n] in DT and eᵖᵗu(t) in CT produce fundamentally different stability behavior. |
| 15 | **Unit Impulse Construction** | Build intuition for the Dirac delta by watching rectangular pulses of width 2ε and height 1/(2ε) converge to δ(t) as ε→0. Pass the pulse through a first-order CT system. |
| 16 | **CT Impulse Response Builder** | Build e^(pt)u(t) term-by-term from the Taylor/operator series expansion. Watch partial sums converge for stable poles and diverge for unstable poles. |
| 17 | **DT System Representation Navigator** | Interactive concept map showing five equivalent representations of a DT LTI system: block diagram, difference equation, H(R), H(z), and h[n]. Enter a system in any form and see all five simultaneously. |
| 18 | **Audio Frequency Response Playground** | Place poles and zeros on the s-plane to define H(s) and see how it shapes the frequency response. Apply filters to test signals and compare input vs output. Includes preset filters and challenge mode. |

### Circuits (3 simulations)

| # | Simulation | Description |
|---|-----------|-------------|
| 19 | **RC Lowpass Filter** | Interactive RC filter showing frequency response and filtering of square wave input signals. Adjust frequency and RC time constant in real-time. |
| 20 | **Amplifier Topologies** | Explore amplifier configurations including simple, feedback, push-pull (crossover distortion), and compensated designs. Visualize gain curves, transfer characteristics, and I/O signals. |
| 21 | **Feedback System Analysis** | Interactive visualization of negative feedback effects on amplifier performance. Compare open-loop vs closed-loop behavior including gain, bandwidth, rise time, and pole locations. |

### Control Systems (10 simulations)

| # | Simulation | Description |
|---|-----------|-------------|
| 22 | **DC Motor Feedback Control** | Feedback control principles for DC motors. Explore how amplifier gain, feedback, and motor parameters affect system behavior through pole-zero maps and step response. |
| 23 | **Second-Order System Response** | Explore second-order system dynamics: pole locations, frequency response, and damping behavior. Visualize how Q-factor affects resonance, bandwidth, and transient response. |
| 24 | **Block Diagram Builder** | Drag-and-drop block diagram construction with Gain, Adder, Delay, and Integrator blocks. Automatic transfer function computation via Mason's gain formula. 5 preset systems with textbook-quality wire routing and collision avoidance. |
| 25 | **Spring Mass Damper System** | Animated mass-spring-damper showing how physical systems transform input signals. Watch the spring stretch and compress as base excitation x(t) becomes mass displacement y(t). |
| 26 | **Furuta Pendulum** | Rotary inverted pendulum with PID control. Real-time 3D visualization, angle tracking, control torque plots, and stability analysis. |
| 27 | **Complex Poles & Sinusoidal Modes** | Visualize how complex conjugate poles produce sinusoidal oscillation from complex exponential modes. Explore s-plane pole locations, mode decomposition, and the 3D helix of e^(jωt). |
| 28 | **Resonance Anatomy Explorer** | Dissect the three characteristic frequencies of a second-order system: undamped natural ω₀, damped oscillation ω_d, and magnitude peak ω_peak. Watch them converge and disappear as damping increases. |
| 29 | **Delay Effect: The Domino of Instability** | See how adding sensor delay destroys a perfect dead-beat controller. Three robots race toward a wall with different delay amounts. |
| 30 | **UAV Perching Trajectory** | Simulate a fixed-wing glider performing bird-like perching. Control elevator pitch-up rate to decelerate through high-alpha stall drag and land on a perch. Features animated streamlines. |
| 31 | **2D Perching Glider** | Fly a glider onto a perch using open-loop, proportional, or optimal control. Experience why feedback is essential for agile maneuvers. Features flat-plate aerodynamics and real-time pole visualization. |

### Transforms (12 simulations)

| # | Simulation | Description |
|---|-----------|-------------|
| 32 | **CT/DT Poles Conversion** | CT to DT system transformations using Forward Euler, Backward Euler, and Trapezoidal methods. S-plane and Z-plane visualization with stability analysis. |
| 33 | **Fourier Analysis: Phase vs Magnitude** | Demonstrates that phase carries more structural information than magnitude. Compare images/audio signals and their hybrids. |
| 34 | **Fourier Series** | Decompose periodic waveforms into harmonic components. Build signals from sine and cosine terms and visualize convergence. |
| 35 | **Z-Transform Properties Lab** | Interactive demonstration of linearity, time delay, multiply-by-n, and convolution properties. See operations in both time domain and z-domain simultaneously. |
| 36 | **Z Transform & ROC Explorer** | Interactive z-plane visualization of Z transforms and regions of convergence. See how the same H(z) maps to different time-domain signals depending on the ROC. |
| 37 | **Inverse Z Transform Solver** | Step-by-step inverse Z transform: factor, partial fractions, match Z-transform pairs based on ROC, assemble h[n]. Includes quiz mode. |
| 38 | **Laplace Transform & s-Plane ROC Explorer** | Explore how the Laplace transform maps CT signals to the s-plane. Move poles and click ROC regions to see how the same H(s) produces different time-domain signals. |
| 39 | **Initial & Final Value Theorem** | Visualization of IVT and FVT for Laplace transforms. Explore how the kernel s·e^{-st} scans a signal as s→∞ and s→0. Includes failure mode demonstrations. |
| 40 | **Laplace Properties Lab** | Seven key Laplace properties: linearity, time delay, multiply-by-t, frequency shift, differentiation, integration, and convolution. |
| 41 | **ODE Solver via Laplace Transform** | Step-by-step ODE solution via the Laplace pipeline: take L{}, solve for Y(s), partial fractions, inverse Laplace, plot y(t). |
| 42 | **Eigenfunction Tester Lab** | Test which signals are eigenfunctions of LTI systems. Verify that complex exponentials e^{st} are eigenfunctions with eigenvalue H(s). |
| 43 | **Vector Diagram Frequency Response** | Build frequency response curves from vector diagrams. Watch vectors from poles and zeros trace out magnitude and phase as frequency sweeps. |

### Optics (1 simulation)

| # | Simulation | Description |
|---|-----------|-------------|
| 44 | **Lens Optics** | Model optical systems using convolution. Simulate lens blur with diffraction-limited Airy disk PSF, aperture effects, atmospheric seeing. Features PSF cross-sections, encircled energy, and MTF curves. |

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Backend** | Python 3.11, FastAPI 0.109, NumPy, SciPy, Pillow, WebSocket |
| **Frontend** | React 18.2, Vite 5, Plotly.js 2.28, Three.js 0.182, axios, react-router-dom 6 |
| **Dev** | Vite proxies `/api` → `localhost:8000`, HMR, GZip compression |

## Architecture

```
backend/
├── main.py                    # FastAPI app, routes, CORS, WebSocket
├── config.py                  # CORS origins, API_PREFIX="/api"
├── simulations/
│   ├── catalog.py             # SIMULATION_CATALOG — single source of truth
│   ├── base_simulator.py      # Abstract BaseSimulator class
│   ├── __init__.py            # SIMULATOR_REGISTRY mapping
│   └── <sim_id>.py            # 13 individual simulator implementations
├── core/
│   ├── executor.py            # Thread-based execution with 30s timeout
│   └── data_handler.py        # NumPy/SciPy serialization, LTTB subsampling
└── requirements.txt

frontend/
├── src/
│   ├── App.jsx                # Router: / and /simulation/:id
│   ├── pages/SimulationPage.jsx
│   ├── components/
│   │   ├── SimulationViewer.jsx    # Main orchestrator (~1575 lines)
│   │   ├── ControlPanel.jsx        # Dynamic controls
│   │   ├── PlotDisplay.jsx         # Generic Plotly renderer
│   │   ├── BlockDiagramViewer.jsx  # SVG block diagram builder
│   │   └── <Name>Viewer.jsx       # Custom viewers per simulation
│   ├── hooks/useSimulation.js      # State management, debounced updates
│   ├── services/api.js             # ApiClient (axios)
│   └── styles/App.css              # Master stylesheet, CSS variables
└── vite.config.js
```

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/simulations` | List all simulations |
| GET | `/api/simulations/{id}` | Get simulation details |
| GET | `/api/simulations/{id}/state` | Get current state (parameters, plots, metadata) |
| POST | `/api/simulations/{id}/execute` | Execute action (init, update, run, reset, step) |
| POST | `/api/simulations/{id}/update` | Update parameters |
| GET | `/api/simulations/{id}/export/csv` | Export data as CSV |
| WS | `/api/simulations/{id}/ws` | Real-time WebSocket updates |

## Contact

- **Shreyas Reddy** — [GitHub](https://github.com/shreyas-reddy)
