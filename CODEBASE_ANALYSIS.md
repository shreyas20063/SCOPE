# Codebase Analysis: Signals & Systems Interactive Web Platform

## 3. Overall Architecture

### Backend — Python 3.11
- **Framework**: FastAPI 0.109 with Uvicorn/Gunicorn
- **Compute**: NumPy, SciPy (signal processing, ODE solvers, linear algebra), SymPy (symbolic math), Pillow (image processing)
- **Infrastructure**: GZip middleware, security headers, LRU cache with TTL, WebSocket manager, rate limiter (disabled), performance monitor, thread-based executor with 30s timeout
- **Pattern**: Abstract `BaseSimulator` → 44 concrete simulator classes → Registry → REST/WebSocket API

### Frontend — React 18.2 + Vite 5
- **Visualization**: Plotly.js 2.28 (2D plots), Three.js 0.182 (3D — Furuta Pendulum, Mass-Spring), KaTeX (math rendering)
- **Networking**: Axios (HTTP), native WebSocket
- **Routing**: react-router-dom 6 (2 routes: landing page, simulation page)
- **State**: Custom `useSimulation` hook with 150ms debounce, animation loop (play/pause/step)
- **Styling**: 1861-line CSS with 60+ CSS variables, dark/light theme toggle, responsive breakpoints at 768px/1024px

### Infrastructure
- Docker Compose (dev + prod), GitHub Actions CI/CD (test → build → deploy), Render.com blueprint, GHCR container registry

### Scale
- ~39,000 lines backend Python
- ~33,000 lines frontend JSX/JS
- 1,861 lines CSS

---

## 1. Fully Implemented Features

### 44 Interactive Simulations across 5 Categories

Each simulation includes:
- Backend simulator (parameter validation, NumPy-vectorized computation, Plotly-format output)
- Custom frontend viewer (39 dedicated viewers + fallback PlotDisplay)
- Dynamic controls (sliders, selects, checkboxes, buttons, expression inputs)
- Real-time parameter updates via debounced API calls

### Simulations by Category

| Category | Count | Simulations |
|---|---|---|
| **Signal Processing** | 12 | Aliasing & Quantization, Fourier Series, Fourier Phase vs Magnitude, Convolution, Signal Operations, Sampling & Reconstruction, Modulation Techniques, Impulse Construction, Audio Frequency Response, Polynomial Multiplication, Eigenfunction Tester, DT/CT Comparator |
| **Circuits** | 6 | RC Lowpass Filter, Feedback System Analysis, Amplifier Topologies, DC Motor, Cascade & Parallel Systems, Resonance Anatomy |
| **Control Systems** | 12 | Second Order System, CT/DT Poles, Block Diagram Builder, Cyclic Path Detector, Feedback Convergence, State Space Analyzer, Pole Behavior, Mass-Spring System, Delay Instability, Furuta Pendulum, UAV Perching, Perching Glider |
| **Transforms** | 13 | Laplace ROC, Laplace Properties, IVT/FVT Visualizer, ODE Laplace Solver, Z-Transform Properties, Z-Transform ROC, Inverse Z-Transform, DT System Representations, DT Difference Equation, CT Impulse Response, Complex Poles & Modes, Fundamental Modes, Vector Frequency Response, Operator Algebra |
| **Optics** | 1 | Lens Optics |

### Platform Features

| Feature | Details |
|---|---|
| **WebSocket real-time updates** | Bidirectional, per-connection rate limiting (10 msg/sec) |
| **In-memory LRU cache** | TTL-based, periodic cleanup every 5 min |
| **CSV data export** | Any simulation, auto-extracts from plot traces |
| **Performance analytics endpoint** | `/api/analytics` — cache hit rates, WebSocket stats, request monitoring |
| **Timeout-protected execution** | 30s max per simulation computation, thread-based |
| **Data serialization layer** | NumPy arrays, complex numbers, SciPy sparse matrices, datetime → JSON |
| **Dark/light theme toggle** | Full CSS variable system |
| **Keyboard shortcuts** | Dedicated panel |
| **URL parameter sharing** | Via `urlParams.js` utility + ShareButton component |
| **Responsive design** | Mobile tabs, breakpoints at 768px/1024px |
| **Accessibility** | Skip-to-content link, ARIA attributes, `focus-visible`, `prefers-reduced-motion` |
| **3D visualizations** | Three.js for Furuta Pendulum (1,173 lines) and Mass-Spring system (1,087 lines), lazy-loaded |
| **Launch animations** | Website launch (482 lines) + simulation launch (735 lines), once per session |
| **Hero canvas** | Interactive discrete-signal animation on landing page |
| **Simulation catalog** | Category filtering, search tags, emoji thumbnails |
| **GZip compression** | 60-80% reduction on plot JSON |
| **Security headers** | X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy |
| **Health checks** | Basic `/health` + detailed `/health/ready` (uptime, cache stats, WS connections) |
| **CI/CD pipeline** | 3-stage GitHub Actions (test → Docker build → deploy to Render.com) |
| **Docker** | Dev and prod compose files, separate backend/frontend Dockerfiles |

---

## 2. Partially Implemented / In Progress

| Feature | Status |
|---|---|
| **Theory sections** (per-simulation educational text with equations) | Planned in CLAUDE.md page flow but no components built |
| **Analysis sections** (observations, "try this" suggestions, related concepts) | Planned in CLAUDE.md page flow but no components built |
| **Rate limiting middleware** | Code exists but is commented out / disabled |
| **Test suite** | 1 test file (`test_ode_laplace.py`) at project root; no `backend/tests/` directory; no frontend tests; CI skips with "No tests found" |
| **`.claude/bugs.md`** | Referenced in CLAUDE.md as the bug registry, but the file doesn't exist |
| **InfoPanel component** | Exists (94 lines) but appears minimal — likely a stub for the theory/analysis sections |
| **Staging deployment** | CI/CD has a `deploy-staging` job for `develop` branch that builds images but doesn't actually deploy |
| **KaTeX integration** | Dependency installed (`katex@0.16.33`) but not actively used in current implementation |

---

## 4. Most Technically Impressive / Novel Parts

### 4.1 Block Diagram Builder (6,186 lines total)
**Backend**: 2,893 lines | **Frontend**: 3,293 lines

The largest and most complex simulation. The backend implements:
- **Mason's Gain Formula** with determinant (delta) computation
- **Cyclic path/loop detection** algorithms with deduplication
- **Transfer function extraction** from arbitrary block diagrams
- **A\* wire routing** for visual connections
- Security-hardened: block limits, TF length validation, gain validation, mode validation

The frontend is a full **visual block diagram editor** with drag-and-drop blocks (Gain, Adder, Delay, Integrator), wiring, and real-time transfer function computation. At 3,293 lines it's essentially an embedded application.

### 4.2 ODE Laplace Solver (1,451 lines)
Symbolic ODE solving using Laplace transforms — takes differential equations, applies Laplace transform, solves algebraically, inverse transforms back. Uses SymPy for symbolic computation combined with NumPy for numerical evaluation. Effectively a **mini CAS (computer algebra system)** specialized for control theory.

### 4.3 State Space Analyzer (1,288 lines)
Full state-space analysis: controllability, observability, eigenvalue decomposition, modal analysis. Computes canonical forms and stability metrics. Supports both linear TF and nonlinear systems with linearization at equilibrium points.

### 4.4 3D Physics Simulations
- **Furuta Pendulum** (624 lines backend + 1,173 lines Three.js) — rotary inverted pendulum, a classic nonlinear control problem, with real-time 3D visualization featuring PBR materials, motion trails (20 ghost spheres), glow effects, and 60fps frame interpolation
- **Perching Glider** (748 lines) + **UAV Perching** (526 lines backend + 820-line viewer) — aerospace trajectory optimization simulations, unusual for a web platform
- **Mass-Spring System** (483 lines + 1,087 lines Three.js) — 3D spring-mass-damper visualization with energy-reactive glow

### 4.5 Signal Processing Pipeline Depth
- Aliasing simulation with **three demo modes** (audio aliasing, audio quantization with dither/Robert's method, image quantization using Pillow)
- Audio frequency response simulator (1,398 lines) — FFT-based analysis and filter design
- Modulation techniques (939 lines) — AM/FM/PM/FDM modulation with spectrum analysis and demodulation

### 4.6 Comprehensive Z-Transform / Laplace Suite
The platform has unusually complete coverage of both continuous and discrete transform domains: ROC visualization, property demonstrations, inverse transforms, IVT/FVT theorems, and CT↔DT comparators. This breadth is rare even in commercial educational tools like MATLAB's interactive examples.

### 4.7 Eigenfunction Tester (844 lines)
Lets users input arbitrary signals and test whether they're eigenfunctions of LTI systems — a concept typically only explained theoretically. Making it interactive and explorable is novel for a web platform.

### 4.8 Fourier Phase vs Magnitude (1,197 lines backend + 610 lines frontend)
2D image Fourier analysis with hybrid reconstruction (swap phase/magnitude between images) and SSIM comparison metrics. Demonstrates Oppenheim & Lim's phase-dominance result interactively.

---

## 5. Gaps

| Gap | Detail |
|---|---|
| **No tests** | 1 test file total. No pytest suite, no frontend tests (no Vitest/Jest). CI gracefully skips. |
| **No educational content layer** | Theory sections, equations, and analysis panels are described in CLAUDE.md but not built. Simulations are interactive but lack textbook-style explanations. |
| **No user accounts or persistence** | All state is ephemeral (in-memory). No database, no user progress tracking, no saved configurations. |
| **No error boundaries** | `ErrorMessage.jsx` exists but no React error boundaries wrapping viewers — a Three.js crash could take down the whole page. |
| **Missing bugs.md** | Referenced as the known-bug registry but doesn't exist. |
| **NumPy version mismatch** | `requirements.txt` constrains `numpy<2.0` but implementation log says `numpy 2.4.2` is installed. Compat guards exist (`_trapz`) but this is fragile. |
| **Single-threaded executor lock** | `SimulationExecutor` uses a global `threading.Lock()`, meaning all simulations serialize through one lock — potential bottleneck at scale. |
| **No input sanitization on expression controls** | The `expression` control type and `signal_parser.py` (392 lines) exist. Frontend blocks `import/exec/eval` but no backend sandboxing. |
| **Optics category is thin** | Only 1 simulation (Lens Optics) vs 12 in Signal Processing and Control Systems. |
| **No offline/PWA support** | No service worker, no manifest — requires active server connection. |
| **Rate limiting disabled** | The middleware exists but is commented out. Under load, the server has no throttling. |
| **KaTeX unused** | Installed as a dependency but not integrated into any viewer or panel. |
| **TypeScript types installed but unused** | `@types/react` and `@types/react-dom` in devDependencies but project is plain JavaScript. |

---

## Appendix: File Size Summary

### Backend (Top 15 by lines)

| File | Lines | Role |
|---|---|---|
| `block_diagram_builder.py` | 2,893 | Block diagram builder with Mason's formula |
| `catalog.py` | 2,443 | All 44 simulation metadata definitions |
| `ode_laplace_solver.py` | 1,451 | Symbolic ODE solving via Laplace |
| `audio_freq_response.py` | 1,398 | Audio FFT analysis and filter design |
| `state_space_analyzer.py` | 1,288 | Controllability, observability, canonical forms |
| `fourier_phase_vs_magnitude.py` | 1,197 | 2D Fourier analysis, hybrid reconstruction |
| `inverse_z_transform.py` | 1,133 | Partial fractions, power series, contour methods |
| `convolution_simulator.py` | 1,133 | CT/DT convolution with step animation |
| `laplace_roc.py` | 1,063 | Region of convergence visualization |
| `ct_dt_poles.py` | 1,017 | S-plane ↔ Z-plane conversion methods |
| `z_transform_roc.py` | 1,012 | Z-transform ROC, causality, stability |
| `modulation_techniques.py` | 939 | AM/FM/PM/FDM modulation |
| `aliasing_quantization.py` | 936 | 3-mode aliasing/quantization demo |
| `laplace_properties.py` | 918 | Laplace property demonstrations |
| `lens_optics.py` | 871 | PSF, MTF, atmospheric seeing |

### Frontend (Top 15 by lines)

| File | Lines | Role |
|---|---|---|
| `BlockDiagramViewer.jsx` | 3,293 | Visual block diagram editor |
| `SimulationViewer.jsx` | 1,995 | Main orchestrator, viewer chain |
| `App.css` | 1,861 | Full CSS design system |
| `FurutaPendulum3D.jsx` | 1,173 | 3D pendulum with PBR materials |
| `InverseZTransformViewer.jsx` | 1,093 | Multi-method IZT visualization |
| `MassSpring3D.jsx` | 1,087 | 3D spring-mass animation |
| `UAVPerchingViewer.jsx` | 820 | Aerospace trajectory viewer |
| `MassSpringViewer.jsx` | 797 | Split canvas + Plotly layout |
| `SystemRepresentationViewer.jsx` | 764 | DT system forms viewer |
| `ODELaplaceViewer.jsx` | 763 | ODE solver visualization |
| `SimulationLaunchAnimation.jsx` | 735 | Transition animation |
| `PerchingGliderViewer.jsx` | 722 | Glider dynamics viewer |
| `CascadeParallelViewer.jsx` | 685 | System composition viewer |
| `ControlPanel.jsx` | 643 | Dynamic parameter controls |
| `useSimulation.js` | 630 | Core state management hook |
