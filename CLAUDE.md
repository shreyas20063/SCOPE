# Signals & Systems Interactive Web Textbook

Interactive web platform for learning signals and systems through simulations. 13 simulations across 5 categories: Signal Processing, Circuits, Control Systems, Transforms, Optics.

## Stack

- **Backend**: Python 3.11, FastAPI 0.109, NumPy <2.0, SciPy <2.0, Pillow. Port 8000.
- **Frontend**: React 18.2, Vite 5, Plotly.js 2.28, Three.js 0.182, axios, react-router-dom 6. Port 3001.
- **Dev proxy**: Vite proxies `/api` to `http://127.0.0.1:8000`
- **API prefix**: `/api` (NOT `/api/v1`)

## Run Commands

```bash
# Backend
cd backend && python -m uvicorn main:app --reload --port 8000

# Frontend
cd frontend && npm run dev

# Build
cd frontend && npm run build
```

## Key Files

### Backend
| File | Role |
|------|------|
| `backend/main.py` | FastAPI app — CORS, GZip, WebSocket, caching, security headers, all routes |
| `backend/config.py` | CORS origins, API_PREFIX="/api", server config |
| `backend/simulations/catalog.py` | SIMULATION_CATALOG list + CATEGORIES dict — single source of truth for all sim definitions |
| `backend/simulations/base_simulator.py` | Abstract BaseSimulator class (175 lines) — the contract every simulator implements |
| `backend/simulations/__init__.py` | SIMULATOR_REGISTRY dict mapping sim IDs to classes, imports, __all__ |
| `backend/simulations/<sim_id>.py` | Individual simulator implementations (13 total) |
| `backend/core/executor.py` | SimulationExecutor — timeout-protected execution (30s max), thread-based |
| `backend/core/data_handler.py` | DataHandler — serializes NumPy/SciPy types to JSON, LTTB subsampling |

### Frontend
| File | Role |
|------|------|
| `frontend/src/App.jsx` | Root component, BrowserRouter, routes: `/` and `/simulation/:id` |
| `frontend/src/pages/SimulationPage.jsx` | Loads simulation via `useSimulation(id)` hook |
| `frontend/src/components/SimulationViewer.jsx` | Main orchestrator (~1575 lines) — viewer chain, info panels, mobile tabs |
| `frontend/src/components/ControlPanel.jsx` | Dynamic controls (slider/select/checkbox/button/expression) |
| `frontend/src/components/PlotDisplay.jsx` | Generic Plotly renderer (fallback when no custom viewer) |
| `frontend/src/components/RCLowpassViewer.jsx` | Custom viewer example — pattern for all custom viewers |
| `frontend/src/hooks/useSimulation.js` | State management, debounced updates (150ms), animation loop |
| `frontend/src/services/api.js` | ApiClient (axios), all API methods |
| `frontend/src/styles/App.css` | Master stylesheet (1530 lines) — all CSS variables defined in `:root` |

## Design System

All colors, spacing, and effects are defined as CSS variables in `frontend/src/styles/App.css` `:root`. Never hardcode values — always use `var(--variable-name)`.

### Colors
```
--primary-color: #14b8a6        (teal — main brand)
--primary-hover: #0d9488
--primary-light: rgba(20, 184, 166, 0.1)
--secondary-color: #3b82f6      (blue)
--accent-color: #00d9ff         (bright cyan)
--accent-purple: #7c3aed        (purple accent)
--accent-pink: #ff006e          (pink accent)

--background-color: #0a0e27     (deep dark)
--background-secondary: #111827
--surface-color: #131b2e        (card background)
--surface-hover: #1e293b

--text-primary: #f1f5f9
--text-secondary: #94a3b8
--text-muted: #64748b

--border-color: #1e293b
--border-hover: #334155

--success-color: #10b981
--warning-color: #f59e0b
--error-color: #ef4444
```

### Category Colors
```python
"Signal Processing": "#06b6d4"  # cyan
"Circuits":          "#8b5cf6"  # purple
"Control Systems":   "#f59e0b"  # amber
"Transforms":        "#10b981"  # emerald
"Optics":            "#ec4899"  # pink
```

### Spacing, Radii, Transitions
```
--radius-sm: 6px    --radius-md: 8px    --radius-lg: 12px    --radius-xl: 16px    --radius-full: 9999px
--transition-fast: 150ms    --transition-normal: 250ms    --transition-slow: 400ms
--shadow-glow: 0 0 20px rgba(0, 217, 255, 0.25)
--shadow-glow-lg: 0 0 40px rgba(0, 217, 255, 0.15), 0 0 80px rgba(0, 217, 255, 0.05)
```

### Fonts
```
Primary: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif
Mono: 'Fira Code', 'Cascadia Code', 'JetBrains Mono', monospace
```

### Theme Toggle
Dark/light mode via `document.documentElement.setAttribute('data-theme', 'dark'|'light')`. Light mode overrides in `[data-theme="light"]` blocks.

## Plot Conventions

All plots use Plotly.js format. Backend returns `{id, title, data, layout}` dicts.

### Colors
- Blue `#3b82f6` — input signal, primary trace
- Red `#ef4444` — output signal, secondary trace
- Green `#10b981` — reference lines, cutoff markers
- Teal `#14b8a6` — accent traces

### Layout Pattern
```javascript
{
  paper_bgcolor: isDark ? '#0a0e27' : 'rgba(255,255,255,0.98)',
  plot_bgcolor: isDark ? '#131b2e' : '#f8fafc',
  font: { family: 'Inter, sans-serif', size: 12 },
  xaxis: { gridcolor: 'rgba(148,163,184,0.1)', zerolinecolor: 'rgba(148,163,184,0.3)' },
  margin: { t: 45, r: 25, b: 55, l: 60 },
  datarevision: `${id}-${title}-${Date.now()}`,  // forces update
  uirevision: id,                                 // preserves zoom/pan
}
```

## Adding a New Simulation

### Step 1: Backend Simulator
Create `backend/simulations/<sim_id>.py`:
```python
from .base_simulator import BaseSimulator
import numpy as np

class MySimulator(BaseSimulator):
    PARAMETER_SCHEMA = {
        "param_name": {"type": "slider", "min": 0, "max": 100, "default": 50}
    }
    DEFAULT_PARAMS = {"param_name": 50}

    def initialize(self, params=None):
        self.parameters = {**self.DEFAULT_PARAMS, **(params or {})}
        for name, value in self.parameters.items():
            self.parameters[name] = self._validate_param(name, value)
        self._initialized = True

    def update_parameter(self, name, value):
        if name in self.parameters:
            self.parameters[name] = self._validate_param(name, value)
        return self.get_state()

    def get_plots(self):
        # Call private _compute() then build Plotly dicts
        data = self._compute()
        return [{"id": "plot_id", "title": "Plot Title", "data": [...], "layout": {...}}]

    def get_state(self):
        return {
            "parameters": self.parameters.copy(),
            "plots": self.get_plots(),
            "metadata": {"simulation_type": "<sim_id>"}  # Required for custom viewer matching
        }

    def _compute(self):
        # NumPy vectorized math here
        pass
```

### Step 2: Register
In `backend/simulations/__init__.py`:
1. Add import: `from .<sim_id> import MySimulator`
2. Add to SIMULATOR_REGISTRY: `"<sim_id>": MySimulator,`
3. Add to __all__: `"MySimulator",`

### Step 3: Catalog Entry
In `backend/simulations/catalog.py`, add to SIMULATION_CATALOG:
```python
{
    "id": "<sim_id>",
    "name": "Display Name",
    "description": "What this simulation teaches",
    "category": "Signal Processing",  # must be a key in CATEGORIES
    "thumbnail": "emoji",
    "tags": ["tag1", "tag2"],
    "has_simulator": True,
    "controls": [
        {"type": "slider", "name": "param", "label": "Label", "min": 0, "max": 100, "step": 1, "default": 50, "unit": "Hz", "group": "Group Name"}
    ],
    "default_params": {"param": 50},
    "plots": [{"id": "plot_id", "title": "Plot Title", "description": "What this plot shows"}],
}
```

Control types: `slider`, `select` (with `options` list), `checkbox`, `button`, `expression`. Use `visible_when` for conditional visibility.

### Step 4: Frontend Viewer (Optional)
If generic PlotDisplay isn't enough, create `frontend/src/components/<Name>Viewer.jsx`. Follow `RCLowpassViewer.jsx` pattern.

### Step 5: Wire Viewer Chain
In `SimulationViewer.jsx` (~line 1488), add to the `metadata?.simulation_type` if/else chain:
```jsx
) : metadata?.simulation_type === '<sim_id>' ? (
  <CustomViewer metadata={metadata} plots={plots} />
```

## Page Flow (Target Layout)

Each simulation page should follow this structure:
```
Header: Simulation name + category badge
    |
Theory Section (scrollable)
  - Clean typeset explanation of the concept
  - Key equations
  - "What you'll explore" summary
    |
Interactive Simulation
  [Plot Area (main canvas) | Controls (side panel)]
    |
Analysis Section (scrollable)
  - Key observations from the simulation
  - "Try this" interactive suggestions
  - Related concepts
```

Theory and Analysis sections are planned — the components need to be built as part of future work.

## API Contract

| Method | Endpoint | Body | Returns |
|--------|----------|------|---------|
| GET | `/api/simulations` | — | List of catalog entries |
| GET | `/api/simulations/{id}` | — | Single catalog entry |
| GET | `/api/simulations/{id}/state` | — | `{parameters, plots, metadata}` |
| POST | `/api/simulations/{id}/execute` | `{action, params}` | `{success, data}` |
| POST | `/api/simulations/{id}/update` | `{params: {k: v}}` | `{success, data}` |
| GET | `/api/simulations/{id}/export/csv` | — | CSV file |
| WS | `/api/simulations/{id}/ws` | — | Real-time updates |
| GET | `/health` | — | `{status: "healthy"}` |

Actions for execute: `init`, `update`, `run`, `reset`, `advance`, `step_forward`, `step_backward`

## Coding Conventions

### Python
- Type hints on all function signatures
- Google-style docstrings
- NumPy vectorized operations (no Python for-loops on arrays)
- Extend BaseSimulator for all simulators
- `DataHandler.serialize_result()` on all output before sending to frontend

### JavaScript
- Functional components only (no class components)
- Hooks for state: useState, useCallback, useMemo, useRef, useEffect
- Lazy loading for heavy components (Three.js, complex viewers)
- CSS variables only — never hardcode colors or spacing
- Responsive breakpoints: 768px (mobile), 1024px (tablet)

## Gotchas

- **Buffer polyfill**: Plotly.js needs `buffer` polyfill, configured in `vite.config.js` via `define: { global: 'globalThis' }`
- **API prefix**: Uses `/api` not `/api/v1`. Defined in `backend/config.py` as `API_PREFIX`
- **DataHandler**: All simulator output must pass through `DataHandler.serialize_result()` — NumPy types aren't JSON-serializable
- **uirevision**: Set `uirevision: plotId` in Plotly layouts to preserve zoom/pan across parameter updates
- **datarevision**: Use `${id}-${title}-${Date.now()}` to force Plotly to re-render
- **Debounce**: Parameter updates debounced 150ms in useSimulation hook
- **Three.js**: Excluded from Vite optimizeDeps, loaded lazily only for Furuta Pendulum
- **CORS**: Dev origins in config.py: localhost:3000, 3001, 5173, 127.0.0.1 variants
- **np.trapz**: Deprecated in NumPy 2.0+. Use `_trapz = np.trapezoid if hasattr(np, 'trapezoid') else np.trapz` compat helper instead. Already applied in signal_operations, convolution, impulse_construction, ivt_fvt_visualizer.
- **Simulator init errors**: `get_or_create_simulator()` in main.py has try/except + threading lock. Always returns `None` on failure (never crashes endpoint).

## Tracking Files & Auto-Logging Rules

All tracking files live in `.claude/`. **Read them before starting work. Update them as you go — don't wait to be asked.**

| File | Purpose | When to read |
|------|---------|--------------|
| `.claude/bugs.md` | Bug tracker with fixes and prevention rules | Before making any code changes |
| `.claude/mistakes.md` | Process failures and lessons learned | Before implementing or testing |

### Auto-Log: Bugs (`.claude/bugs.md`)

**Trigger:** Any time you fix a bug, find a bug, or introduce a regression.

**Action:** Immediately append a new `BUG-NNN` entry. Do this BEFORE moving on to the next task.

```markdown
## BUG-NNN: Short title

**Date:** YYYY-MM-DD
**Status:** Fixed / Open / Regression
**File:** file path(s) affected

**Bug:** What was broken, factually.

**Fix:** What was changed and why.

**Prevention:** Rule to avoid reintroduction.
```

### Auto-Log: Mistakes (`.claude/mistakes.md`)

**Trigger:** Any time you produce wrong output, make false claims ("all tests pass" when they don't), use bad assumptions, or the user catches an error.

**Action:** Log BEFORE fixing. The mistake entry matters more than the fix.

```markdown
## MISTAKE-NNN: Short title

**Date:** YYYY-MM-DD
**Severity:** Critical / High / Medium / Low
**Context:** Where it happened

**What happened:** What went wrong, factually.

**Root cause:** Why it happened — the actual misunderstanding or process failure.

**Rule:** Concrete, actionable rule(s) to prevent recurrence.
```

### Auto-Log: New Simulations (CLAUDE.md → "Recent Features Added")

**Trigger:** Any time you add a new simulation (backend simulator + catalog entry + optional viewer).

**Action:** Append to the "Recent Features Added" section below with:

```markdown
### Simulation Name (simulation: `sim_id`)
- **Backend**: `backend/simulations/<sim_id>.py` (~N lines)
- **Frontend**: `frontend/src/components/<Name>Viewer.jsx` (~N lines) [if custom viewer]
- **Purpose**: One-line description
- **Key features**: Bullet list of notable capabilities
```

### Auto-Log: Significant Changes to Existing Sims

**Trigger:** Any non-trivial change to an existing simulation (new controls, new modes, algorithm changes, UI overhaul).

**Action:** Add a bullet under the relevant simulation's section in "Recent Features Added", or create a new subsection if the change is large.

## Recent Features Added

### Signal Flow Scope (simulation: `signal_flow_scope`)
- **Backend**: `backend/simulations/signal_flow_scope.py` (~680 lines)
- **Frontend**: `frontend/src/components/SignalFlowScopeViewer.jsx` (~520 lines)
- **Purpose**: Import block diagrams from Block Diagram Builder via localStorage, apply input signals (impulse/step/sinusoid/ramp), and probe any node to visualize signal propagation
- **Key features**: Click-to-probe interaction, Mason's Gain Formula for per-node TF computation, SVG signal flow graph + Plotly scope plots split layout
- **Import mechanism**: localStorage bridge — Block Diagram Builder exports JSON to `localStorage['blockDiagram_export']`, Signal Flow Scope imports it

### SFG Toggle (in Block Diagram Builder)
- **File**: `frontend/src/components/BlockDiagramViewer.jsx`
- **Purpose**: Toggle between block diagram and textbook-correct Signal Flow Graph view
- **Key implementation**: `convertToSFG()` converts blocks to SFG following Mason/Oppenheim/Nise conventions
- **Rules**: Nodes = signals (circles), branches = transfer functions (directed edges with gain labels). ALL TF blocks become edge gains. Operator-domain labels: R (delay), A (integrator).
- **Known constraints**: See `.claude/bugs.md` BUG-001 through BUG-007 for fixed issues and prevention rules

### Root Locus Analyzer Major Overhaul
- **Backend**: Inline TF expression parser (expanded + factored forms), Routh-Hurwitz table computation, stability K-ranges from jω crossings, locus data export for animation
- **Frontend**: Full vertical layout (s-plane full-width 600px), inline KaTeX TF input, K-sweep animation with trail, Routh-Hurwitz table with sign-change highlighting, stability ranges bar visualization
- **Key features**: Play/pause K animation, speed control (0.5x–4x), throttled step response sync, collapsible construction rules, responsive mobile tabs

### Block Diagram Builder Enhancements
- Custom TF blocks with KaTeX expression rendering
- Wire routing with A* pathfinding and crossing bridges
- Auto-arrange after TF parsing
- JSON export for Signal Flow Scope import
- Block count limit (30), TF string length limit (500 chars)
- Generalized Mason's Delta computation

### Routh-Hurwitz Stability Criterion Tool (simulation: `routh_hurwitz`)
- **Backend**: `backend/simulations/routh_hurwitz.py` (~310 lines), shared utility `backend/core/routh_hurwitz.py` (~130 lines)
- **Frontend**: `frontend/src/components/RouthHurwitzViewer.jsx` (~280 lines), `frontend/src/styles/RouthHurwitzViewer.css` (~350 lines)
- **Purpose**: Standalone educational tool for building Routh arrays step-by-step with sign-change highlighting
- **Key features**: KaTeX polynomial display, 8 educational presets (including special cases), parametric K analysis with stability ranges bar, pole-zero map, shared Routh utility extracted from root_locus.py

### Controller Tuning Lab (simulation: `controller_tuning_lab`)
- **Backend**: `backend/simulations/controller_tuning_lab.py` (~1520 lines)
- **Frontend**: `frontend/src/components/ControllerTuningLabViewer.jsx` (~600 lines)
- **CSS**: `frontend/src/styles/ControllerTuningLab.css` (~320 lines)
- **Purpose**: Unified controller design and auto-tuning environment (classical + modern)
- **Key features**:
  - 7 plant presets (1st/2nd order, integrator, FOPDT, DC motor, unstable, custom TF)
  - PID with derivative filter + Lead-Lag compensator
  - 6 auto-tuning methods: ZN open/closed-loop, Cohen-Coon, Lambda, IMC, ITAE optimal
  - 7 analysis plots: step response, Bode mag/phase, pole-zero map, control effort, error signal, Nyquist
  - SVG feedback loop block diagram with KaTeX transfer function rendering
  - Performance metrics strip (rise time, settling time, overshoot, margins, ISE/IAE/ITAE)
  - Save up to 5 reference responses for comparison
  - Fullscreen comparison overlay with overlaid traces and metrics table
  - **Phase 2 — Modern controllers**: State Feedback (manual K), Pole Placement (`scipy.signal.place_poles`), LQR Optimal (`scipy.linalg.solve_continuous_are`)
  - **Phase 3 — LQG (LQR + Kalman Filter)**: Dual Riccati equation solution, augmented 2n-order CL state-space, reference feedforward N_bar for unit tracking, custom SVG observer block diagram
  - TF↔SS bridging: `tf2ss()` conversion, controllability matrix rank check, `StateSpace.to_tf()` for CL
  - KaTeX-rendered state-space matrices (A, B, C, D) with `\dot{x} = Ax + Bu` equations
  - State-feedback SVG block diagram variant (K on feedback path instead of C(s))
  - LQG SVG block diagram variant (Kalman Filter + K blocks in observer-feedback structure)
  - Controllability badge, plant order display, and Kalman gain L display in metrics strip

### Lead-Lag Compensator Designer (simulation: `lead_lag_designer`)
- **Backend**: `backend/simulations/lead_lag_designer.py` (~580 lines)
- **Frontend**: `frontend/src/components/LeadLagDesignerViewer.jsx` (~360 lines)
- **CSS**: `frontend/src/styles/LeadLagDesigner.css` (~280 lines)
- **Purpose**: Dedicated frequency-domain lead-lag compensator design tool with textbook α/ωm parameterization
- **Key features**:
  - Independent lead (α, ωm) and lag (β, ωm) section controls with enable/disable
  - 6 plant presets: 1st order, type 1, 2nd order, type 1+2P, DC motor, custom TF
  - 6 analysis plots: Bode mag/phase, step response, pole-zero map, compensator phase breakdown, Nichols chart
  - Phase contribution breakdown showing individual lead and lag phase curves with φ_max markers
  - PM/GM target lines on Bode plots, stability-colored metrics strip
  - Design info panel showing computed zero/pole locations, max phase, HF gain, LF boost
  - SVG feedback loop block diagram with KaTeX transfer function rendering
  - Nichols chart (unique to this tool — not available in Controller Tuning Lab)

### Steady-State Error Analyzer (simulation: `steady_state_error`)
- **Backend**: `backend/simulations/steady_state_error.py` (~1030 lines)
- **Frontend**: `frontend/src/components/SteadyStateErrorViewer.jsx` (~443 lines)
- **CSS**: `frontend/src/styles/SteadyStateError.css` (~370 lines)
- **Purpose**: Systematic analysis of steady-state tracking error in unity-feedback control systems
- **Key features**:
  - 7 plant presets: Type 0 (2 variants), Type 1 (2 variants), Type 2 (2 variants), Type 3, plus custom G(s)
  - System type detection (poles at origin), error constants (Kp, Kv, Ka) computation
  - Color-coded error table showing ess for step/ramp/parabolic inputs (green=0, amber=finite, red=∞)
  - Final Value Theorem step-by-step LaTeX derivation (collapsible)
  - SVG unity feedback block diagram with KaTeX-rendered G(s)
  - 4 plots: time response, error signal, ess-vs-K parametric curve (log-log), pole-zero map
  - Gain K slider showing the fundamental gain-error-stability tradeoff
  - ess-vs-K plot with stability boundary shading and all 3 input curves
  - Unstable CL detection with FVT invalidity warning

### Nonlinear Phase Portrait Analyzer (simulation: `phase_portrait`)
- **Backend**: `backend/simulations/phase_portrait.py` (~580 lines)
- **Frontend**: `frontend/src/components/PhasePortraitViewer.jsx` (~310 lines)
- **CSS**: `frontend/src/styles/PhasePortrait.css` (~340 lines)
- **Purpose**: Interactive exploration of 2D autonomous nonlinear dynamical systems with vector fields, trajectories, and equilibrium classification
- **Key features**:
  - 5 presets: Simple Pendulum, Van der Pol, Lotka-Volterra, Duffing, Limit Cycle + custom equations
  - Safe expression evaluator for f(x₁,x₂), g(x₁,x₂) with sandboxed numpy namespace
  - Click-to-add initial conditions → solve_ivp forward+backward trajectories
  - Grid-based fsolve equilibrium finding with deduplication
  - 2×2 Jacobian via central finite differences → eigenvalue classification (node/spiral/saddle/center)
  - Equilibrium detail panel: eigenvalues, eigenvectors, Jacobian matrix, tr/det
  - Time series plot for latest trajectory (x₁(t), x₂(t))
  - Preset-specific parameter sliders (μ for VdP, α/β/γ/δ for LV, δ for Duffing)

### Nonlinear Control Lab (simulation: `nonlinear_control_lab`)
- **Backend**: `backend/simulations/nonlinear_control_lab.py` (~2220 lines)
- **Frontend**: `frontend/src/components/NonlinearControlLabViewer.jsx` (~920 lines)
- **CSS**: `frontend/src/styles/NonlinearControlLab.css` (~400 lines)
- **Purpose**: Linearize → Design → Validate workflow for nonlinear plants — the CDC paper's flagship simulation
- **Key features**:
  - 4 plant presets: inverted pendulum on cart (4×1), ball & beam (4×1), coupled tanks MIMO (2×2), Van der Pol (2×1) + custom ODE
  - SymPy symbolic Jacobian for exact linearization (∂f/∂x, ∂f/∂u) at user-selected equilibria
  - LQR (Riccati via `solve_continuous_are`) and pole placement (`place_poles`) controller design
  - Side-by-side linear prediction (matrix exponential) vs nonlinear validation (`solve_ivp` RK45)
  - HTML5 Canvas phase portrait with vector field arrows (magnitude-colored), streamlines, animated trajectories
  - User-selectable 2D projection axes for higher-order systems (4-state → pick 2 axes)
  - Click-to-set initial condition on Canvas
  - Threaded region of attraction computation (25×25 IC grid, `ThreadPoolExecutor(8)`)
  - KaTeX derivation chain: ODE → A,B → K → CL eigenvalues (collapsible)
  - Metrics strip: stability, controllability rank, CL eigenvalues, convergence time, ‖K‖
  - Full MIMO support (coupled tanks: 2-input 2-output LQR with diagonal Q,R)
