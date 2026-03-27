# Codebase Structure

**Analysis Date:** 2026-03-27

## Directory Layout

```
sims-dev/
├── backend/                    # Python FastAPI backend (port 8000)
│   ├── main.py                 # FastAPI app, all routes, middleware, simulator lifecycle
│   ├── config.py               # CORS origins, API_PREFIX="/api", server settings
│   ├── core/                   # Shared utilities (executor, data handler, math libs)
│   │   ├── __init__.py
│   │   ├── executor.py         # SimulationExecutor (timeout-protected execution)
│   │   ├── data_handler.py     # NumPy/SciPy -> JSON serialization, LTTB downsampling
│   │   ├── controllers.py      # LQR, pole placement, LQG controller design
│   │   ├── mimo_utils.py       # MIMO controllability, observability, simulation
│   │   ├── routh_hurwitz.py    # Routh array computation
│   │   └── hub_validator.py    # TF/SS validation and enrichment for Hub
│   ├── simulations/            # All simulator implementations (~60 files)
│   │   ├── __init__.py         # SIMULATOR_REGISTRY dict + get_simulator_class()
│   │   ├── base_simulator.py   # Abstract BaseSimulator class (254 lines)
│   │   ├── catalog.py          # SIMULATION_CATALOG, CATEGORIES, SECTIONS (~4083 lines)
│   │   ├── signal_parser.py    # Expression parsing utility
│   │   └── <sim_id>.py         # Individual simulator classes (56 files)
│   ├── routes/                 # Sub-routers
│   │   ├── __init__.py
│   │   └── hub.py              # POST /api/hub/validate endpoint
│   ├── utils/                  # Infrastructure (cache, rate limiter, WS, monitoring)
│   │   ├── __init__.py         # Re-exports all utils
│   │   ├── cache.py            # LRUCache with TTL
│   │   ├── rate_limiter.py     # Per-IP rate limiting
│   │   ├── websocket_manager.py # WebSocket connection management
│   │   └── monitoring.py       # PerformanceMonitor, request logging
│   ├── rl/                     # Reinforcement learning modules (experimental)
│   │   ├── __init__.py
│   │   ├── es_policy.py        # Evolution strategy policy
│   │   ├── mlp_policy.py       # MLP policy network
│   │   ├── plant_features.py   # Feature extraction for plants
│   │   ├── ppo_agent.py        # PPO agent
│   │   ├── ppo_env.py          # PPO environment
│   │   └── ppo_trainer.py      # PPO training loop
│   ├── assets/                 # Static assets
│   │   ├── models/             # Pre-trained RL model weights (JSON)
│   │   └── aliasing_quantization/ # Audio samples for aliasing sim
│   ├── tests/                  # Backend unit tests
│   │   ├── __init__.py
│   │   └── test_hub_validator.py
│   ├── logs/                   # Runtime log files (gitignored)
│   ├── test_e2e.py             # End-to-end test suite (~82K)
│   └── test_multiloop.py       # Multi-loop test suite (~57K)
├── frontend/                   # React/Vite frontend (port 3001)
│   ├── vite.config.js          # Vite config: proxy, code splitting, polyfills
│   ├── package.json            # Dependencies and scripts
│   ├── index.html              # SPA entry HTML
│   ├── public/                 # Static public assets
│   │   └── assets/             # Images for specific simulations
│   ├── src/
│   │   ├── main.jsx            # ReactDOM.createRoot entry
│   │   ├── App.jsx             # Root component: BrowserRouter, HubProvider, header/footer
│   │   ├── components/         # All React components (~75 files)
│   │   │   ├── SimulationViewer.jsx  # Main orchestrator (~92K, viewer chain dispatch)
│   │   │   ├── ControlPanel.jsx      # Dynamic control rendering (slider/select/checkbox/button/expression)
│   │   │   ├── PlotDisplay.jsx       # Generic Plotly renderer (fallback viewer)
│   │   │   ├── BlockDiagramViewer.jsx # Largest component (~137K)
│   │   │   ├── *Viewer.jsx           # ~50 custom simulation viewers
│   │   │   ├── *3D.jsx              # Three.js 3D visualization components
│   │   │   ├── HubButton.jsx        # Hub toggle button
│   │   │   ├── HubPanel.jsx         # Hub side panel UI
│   │   │   ├── ErrorBoundary.jsx     # React error boundary
│   │   │   ├── ThemeToggle.jsx       # Dark/light theme switcher
│   │   │   ├── Toast.jsx            # Toast notification component
│   │   │   └── ...
│   │   ├── pages/              # Route-level page components
│   │   │   ├── LandingPage.jsx       # Homepage with section-grouped simulation cards
│   │   │   └── SimulationPage.jsx    # Individual simulation page (loads useSimulation)
│   │   ├── hooks/              # Custom React hooks
│   │   │   ├── useSimulation.js      # Core simulation state management (~22K)
│   │   │   ├── useHub.js            # Hub context consumer hook
│   │   │   ├── useMemoizedPlots.js   # Plot memoization
│   │   │   ├── useIntersectionObserver.js # Scroll-based visibility
│   │   │   ├── useWebSocketSimulation.js  # WebSocket alternative to HTTP
│   │   │   └── index.js             # Hook re-exports
│   │   ├── services/           # API communication
│   │   │   └── api.js               # ApiClient class (axios singleton)
│   │   ├── contexts/           # React context providers
│   │   │   └── HubContext.jsx        # System Hub state + localStorage persistence
│   │   ├── styles/             # CSS files (~45 files)
│   │   │   ├── App.css               # Master stylesheet (~1530 lines), CSS variables in :root
│   │   │   ├── SimulationViewer.css  # Main viewer layout styles
│   │   │   ├── ControlPanel.css      # Control panel styles
│   │   │   ├── PlotDisplay.css       # Plot container styles
│   │   │   ├── Hub.css              # Hub panel styles
│   │   │   └── *Viewer.css          # Per-viewer custom styles
│   │   └── utils/              # Frontend utilities
│   │       └── urlParams.js          # URL parameter encoding/decoding
│   └── dist/                   # Production build output (gitignored content)
├── validation/                 # MATLAB comparison and benchmark scripts
│   ├── compare.py
│   ├── generate_paper_tables.py
│   ├── run_scope_benchmarks.py
│   ├── matlab/                 # MATLAB reference scripts
│   └── results/                # Benchmark results
├── Theory/                     # Processed lecture notes and images (not served)
├── Fonts/                      # Custom font files
├── .claude/                    # Claude tracking files (bugs.md, mistakes.md)
├── .planning/                  # GSD planning documents
│   └── codebase/               # Codebase analysis docs (this file)
├── CLAUDE.md                   # Project instructions and conventions
└── .gitignore
```

## Directory Purposes

**`backend/simulations/`:**
- Purpose: All simulation engines (mathematical computation + Plotly plot generation)
- Contains: 56 simulator Python files, each a class extending `BaseSimulator`
- Key files:
  - `backend/simulations/__init__.py`: `SIMULATOR_REGISTRY` dict mapping sim IDs to classes
  - `backend/simulations/base_simulator.py`: Abstract base class (contract)
  - `backend/simulations/catalog.py`: 4083-line declarative catalog defining all sim metadata, controls, defaults
  - `backend/simulations/signal_parser.py`: Expression parsing utility used by some sims

**`backend/core/`:**
- Purpose: Shared backend utilities used across multiple simulators and routes
- Contains: Executor, data serialization, control theory math modules, hub validation
- Key files:
  - `backend/core/executor.py`: Timeout-protected execution wrapper
  - `backend/core/data_handler.py`: NumPy/SciPy -> JSON serialization
  - `backend/core/controllers.py`: LQR, pole placement, LQG (used by 3D sims, controller tuning lab, MIMO)
  - `backend/core/mimo_utils.py`: MIMO math (used by mimo_design_studio)
  - `backend/core/routh_hurwitz.py`: Routh array (used by root_locus, routh_hurwitz sims)
  - `backend/core/hub_validator.py`: TF/SS validation and math enrichment

**`backend/utils/`:**
- Purpose: Infrastructure services (caching, rate limiting, WebSocket, monitoring)
- Contains: Singleton instances exported from `__init__.py`
- Key files: `cache.py` (LRU), `websocket_manager.py`, `rate_limiter.py`, `monitoring.py`

**`backend/rl/`:**
- Purpose: Reinforcement learning experiment for auto-PID tuning
- Contains: MLP policy, ES policy, PPO agent, plant feature extraction
- Key files: `backend/rl/es_policy.py`, `backend/rl/mlp_policy.py`
- Note: Experimental, used by `controller_tuning_lab` simulation

**`backend/routes/`:**
- Purpose: FastAPI sub-routers (only hub validation currently separated)
- Contains: `hub.py` with `POST /api/hub/validate`
- Note: Most routes are inline in `backend/main.py`

**`frontend/src/components/`:**
- Purpose: All React components (~75 JSX files)
- Contains: Custom viewers (one per simulation type), shared UI components, 3D visualizations
- Key files:
  - `SimulationViewer.jsx` (~92K): Main orchestrator, viewer dispatch chain
  - `ControlPanel.jsx` (~19K): Dynamic control rendering from catalog definitions
  - `PlotDisplay.jsx` (~13K): Generic Plotly renderer
  - `BlockDiagramViewer.jsx` (~137K): Largest component, block diagram builder with A* routing
  - `FurutaPendulum3D.jsx`, `InvertedPendulum3D.jsx`, `BallBeam3D.jsx`, `CoupledTanks3D.jsx`, `MassSpring3D.jsx`: Three.js 3D visualizations

**`frontend/src/hooks/`:**
- Purpose: Custom React hooks for state management
- Contains: Simulation state, hub interaction, plot memoization, scroll observers
- Key file: `useSimulation.js` (~22K) - the core hook managing all simulation state and API calls

**`frontend/src/services/`:**
- Purpose: API communication layer
- Contains: `api.js` - singleton `ApiClient` class wrapping axios

**`frontend/src/contexts/`:**
- Purpose: React context providers
- Contains: `HubContext.jsx` - cross-simulation data sharing via localStorage

**`frontend/src/styles/`:**
- Purpose: All CSS (no CSS-in-JS, no Tailwind)
- Contains: ~45 CSS files, one per major component plus master `App.css`
- Key file: `App.css` (~1530 lines) - all CSS variables in `:root`, global styles

**`frontend/src/pages/`:**
- Purpose: Route-level page components
- Contains: `LandingPage.jsx` (homepage grid), `SimulationPage.jsx` (individual sim page)

**`validation/`:**
- Purpose: MATLAB comparison scripts and benchmarks for research paper
- Contains: Python scripts to run SCOPE simulations and compare with MATLAB ground truth

## Key File Locations

**Entry Points:**
- `backend/main.py`: FastAPI app creation, all HTTP/WS routes, simulator lifecycle management
- `frontend/src/main.jsx`: React root render
- `frontend/src/App.jsx`: Root component with routing, HubProvider, theme, header/footer
- `frontend/vite.config.js`: Dev server config, proxy, build optimization

**Configuration:**
- `backend/config.py`: CORS origins, API_PREFIX, server host/port
- `frontend/vite.config.js`: Dev proxy `/api` -> `localhost:8000`, code splitting, polyfills
- `frontend/src/styles/App.css` `:root`: All CSS variables (colors, spacing, fonts, shadows)

**Core Logic:**
- `backend/simulations/catalog.py`: Single source of truth for all simulation definitions
- `backend/simulations/__init__.py`: Registry mapping sim IDs to Python classes
- `backend/simulations/base_simulator.py`: Abstract base class every simulator implements
- `frontend/src/hooks/useSimulation.js`: All frontend simulation state management
- `frontend/src/components/SimulationViewer.jsx`: Viewer dispatch chain (~line 1739-2196)

**Testing:**
- `backend/test_e2e.py`: End-to-end backend tests (~82K)
- `backend/test_multiloop.py`: Multi-loop tests (~57K)
- `backend/tests/test_hub_validator.py`: Hub validator unit tests
- `validation/`: MATLAB comparison benchmarks

## Naming Conventions

**Files:**
- Backend simulators: `backend/simulations/<snake_case_sim_id>.py` (e.g., `rc_lowpass_filter.py`, `controller_tuning_lab.py`)
- Backend core modules: `backend/core/<snake_case>.py` (e.g., `data_handler.py`, `hub_validator.py`)
- Frontend viewers: `frontend/src/components/<PascalCase>Viewer.jsx` (e.g., `RCLowpassViewer.jsx`, `ControllerTuningLabViewer.jsx`)
- Frontend 3D components: `frontend/src/components/<PascalCase>3D.jsx` (e.g., `FurutaPendulum3D.jsx`)
- Frontend styles: `frontend/src/styles/<PascalCase>.css` matching the component name
- Hooks: `frontend/src/hooks/use<PascalCase>.js` (e.g., `useSimulation.js`, `useHub.js`)

**Directories:**
- `snake_case` for Python packages: `simulations/`, `core/`, `utils/`, `routes/`
- `lowercase` for frontend: `components/`, `hooks/`, `services/`, `contexts/`, `styles/`, `pages/`

**Simulation IDs:**
- `snake_case` strings matching the Python module filename: `rc_lowpass_filter`, `controller_tuning_lab`, `mimo_design_studio`
- Used in: `SIMULATOR_REGISTRY` keys, `SIMULATION_CATALOG` `id` fields, API URLs, `metadata.simulation_type`

**Classes:**
- Backend: `PascalCaseSimulator` (e.g., `RCLowpassSimulator`, `ControllerTuningLabSimulator`)
- Frontend: Functional components named `PascalCase` (e.g., `SimulationViewer`, `ControlPanel`)

## Where to Add New Code

**New Simulation (full pipeline):**
1. Backend simulator: `backend/simulations/<sim_id>.py` - class extending `BaseSimulator`
2. Register in: `backend/simulations/__init__.py` - add import and `SIMULATOR_REGISTRY` entry
3. Catalog entry: `backend/simulations/catalog.py` - add dict to `SIMULATION_CATALOG` list
4. Section mapping: `backend/simulations/catalog.py` `SECTION_MAP` - assign to section
5. (Optional) Custom viewer: `frontend/src/components/<Name>Viewer.jsx`
6. (Optional) Custom styles: `frontend/src/styles/<Name>.css`
7. Wire viewer: `frontend/src/components/SimulationViewer.jsx` - add to viewer chain (~line 1739)

**New Shared Math Utility:**
- Place in: `backend/core/<module_name>.py`
- Import from simulators that need it

**New API Endpoint:**
- For simulation-specific: Add inline in `backend/main.py` under relevant section
- For new feature area: Create `backend/routes/<feature>.py` with `APIRouter`, include in `backend/main.py`

**New React Component:**
- Implementation: `frontend/src/components/<Name>.jsx`
- Styles: `frontend/src/styles/<Name>.css`
- Import CSS in the component file

**New Custom Hook:**
- Place in: `frontend/src/hooks/use<Name>.js`
- Re-export from: `frontend/src/hooks/index.js`

**New Frontend Utility:**
- Place in: `frontend/src/utils/<name>.js`

**New Page Route:**
- Page component: `frontend/src/pages/<Name>.jsx`
- Route: Add `<Route>` in `frontend/src/App.jsx`

## Special Directories

**`backend/assets/`:**
- Purpose: Pre-trained model weights and audio samples
- Generated: Partially (model weights from training scripts)
- Committed: Yes

**`frontend/dist/`:**
- Purpose: Vite production build output
- Generated: Yes (`npm run build`)
- Committed: No (gitignored)

**`backend/logs/`:**
- Purpose: Runtime performance logs
- Generated: Yes (at runtime)
- Committed: No (gitignored)

**`.claude/`:**
- Purpose: Bug tracker (`bugs.md`) and mistake log (`mistakes.md`)
- Generated: No (manually maintained)
- Committed: Yes

**`.planning/`:**
- Purpose: GSD planning and codebase analysis documents
- Generated: By analysis tools
- Committed: Yes

**`Theory/`:**
- Purpose: Processed lecture notes and images from course material
- Generated: No
- Committed: Yes (but gitignored in some configs)

**`validation/`:**
- Purpose: MATLAB comparison benchmarks for research paper
- Generated: Partially (results from benchmark runs)
- Committed: Yes

---

*Structure analysis: 2026-03-27*
