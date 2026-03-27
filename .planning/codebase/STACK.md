# Technology Stack

**Analysis Date:** 2026-03-27

## Languages

**Primary:**
- Python 3.11+ (runtime detected: 3.13.5) - Backend API, simulation engines, RL training
- JavaScript (ES2020+ / ESM) - Frontend UI, 3D visualizations, plotting

**Secondary:**
- CSS3 - Styling with CSS custom properties (design system in `:root`)
- HTML5 - Canvas-based visualizations (phase portraits, vector fields)

## Runtime

**Environment:**
- Python: 3.11+ required (constraints: NumPy <2.0, SciPy <2.0); local detected 3.13.5
- Node.js: v22.20.0 (detected locally)
- No `.nvmrc` or `.python-version` files present

**Package Manager:**
- pip (Python) - `backend/requirements.txt`
- npm 10.9.3 (Node.js) - `frontend/package.json`
- Lockfile: `frontend/package-lock.json` present (lockfileVersion 3)
- No Python lockfile (no `requirements.lock`, `poetry.lock`, or `Pipfile.lock`)

## Frameworks

**Core:**
- FastAPI 0.109.0 - Python async web framework (`backend/main.py`)
- React 18.2.0 - Frontend UI library (`frontend/package.json`)
- Vite 5.0.12 - Frontend dev server and build tool (`frontend/vite.config.js`)

**Visualization:**
- Plotly.js 2.28.0 + react-plotly.js 2.6.0 - 2D charting (all simulation plots)
- Three.js 0.182.0 - 3D visualizations (pendulum, tanks, ball-beam)
- KaTeX 0.16.33 - LaTeX math rendering in UI
- HTML5 Canvas API - Phase portraits, vector fields (used directly, no library)

**Networking:**
- axios 1.6.5 - HTTP client for API calls (`frontend/src/services/api.js`)
- FastAPI WebSocket - Real-time simulation updates (`backend/main.py` line 578)

**Routing:**
- react-router-dom 6.21.2 - Client-side routing (`frontend/src/App.jsx`)
- FastAPI APIRouter - Server-side route modules (`backend/routes/hub.py`)

**Build/Dev:**
- @vitejs/plugin-react 4.2.1 - React JSX/Fast Refresh support
- terser 5.27.0 - Production JS minification
- uvicorn[standard] 0.27.0 - ASGI server for FastAPI
- gunicorn 21.2.0 - Production WSGI/ASGI server (available but not primary dev server)

## Key Dependencies

**Critical (Backend):**
- numpy >=1.24.0,<2.0.0 - All numerical computation, array operations
- scipy >=1.10.0,<2.0.0 - Control theory (signal, linalg, integrate, optimize)
- sympy >=1.12 - Symbolic Jacobian computation for nonlinear control lab
- pydantic >=2.5.0 - Request/response validation models
- Pillow >=10.0.0 - Image processing (lens optics simulation)
- python-multipart 0.0.6 - File upload support

**Critical (Frontend):**
- plotly.js 2.28.0 - Primary plotting library (every simulation uses it)
- three 0.182.0 - 3D physics visualizations (lazy-loaded, excluded from optimizeDeps)
- katex 0.16.33 - Math equation rendering throughout UI
- buffer 6.0.3 - Node.js polyfill required by Plotly.js dependencies

**Infrastructure (Backend):**
- Custom in-memory LRU cache with TTL (`backend/utils/cache.py`)
- Custom WebSocket connection manager (`backend/utils/websocket_manager.py`)
- Custom rate limiter (`backend/utils/rate_limiter.py`) - currently disabled
- Custom performance monitor (`backend/utils/monitoring.py`)

**RL Training Module:**
- Pure NumPy/SciPy implementation (no PyTorch, TensorFlow, or gymnasium)
- Evolution Strategies optimizer (`backend/rl/es_policy.py`)
- Actor-Critic (A2C) trainer (`backend/rl/mlp_policy.py`, `backend/rl/ppo_trainer.py`)
- Plant feature extraction (`backend/rl/plant_features.py`)
- PPO environment (`backend/rl/ppo_env.py`, `backend/rl/ppo_agent.py`)
- Trained model weights stored as JSON: `backend/assets/models/es_pid_policy.json`, `backend/assets/models/a2c_pid_tuner.json`

## Configuration

**Environment:**
- `.env.development` and `.env.production` present at project root (existence noted only)
- `.env.example` present for reference
- `VITE_API_URL` - Frontend env var; when set, points to production backend URL; when unset, uses Vite proxy (`/api`)
- `DEBUG_MODE` - Backend env var, read from `os.getenv()` in `backend/config.py`
- No other env vars detected in backend config (no database, no external API keys)

**Backend Config:**
- `backend/config.py` - CORS origins, API_PREFIX="/api", server host/port
- CORS in production overridden to `allow_origins=["*"]` in `backend/main.py` line 109
- GZip compression enabled for responses >500 bytes
- Security headers: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy

**Frontend Config:**
- `frontend/vite.config.js` - Dev server (port 3001), proxy `/api` to backend, build config
- Dev proxy: `/api` -> `http://127.0.0.1:8000`
- Build target: ES2020
- Manual chunk splitting: vendor-react, vendor-plotly, vendor-three, vendor-axios
- Three.js excluded from Vite pre-bundling (loaded on demand)
- `global: 'globalThis'` polyfill for Plotly.js Node.js globals

**Build:**
- Backend: No build step (Python interpreted)
- Frontend: `vite build` with terser minification, console.log stripping, no sourcemaps
- Chunk size warning limit: 1000KB

## Platform Requirements

**Development:**
- Python 3.11+ with pip
- Node.js (v18+ recommended, v22 detected locally)
- No Docker configuration detected
- No CI/CD pipeline detected (no `.github/workflows/`, no Dockerfile, no render.yaml)
- No linting/formatting tools configured (no ESLint, Prettier, Black, Ruff configs)

**Production:**
- Backend: uvicorn (dev) or gunicorn (production ASGI)
- Frontend: Static files from `vite build` output
- No deployment configuration files detected (no Dockerfile, render.yaml, Procfile, vercel.json, netlify.toml)
- Deployment target is undetermined from codebase alone

## NumPy/SciPy Compatibility

**Critical constraint:** NumPy pinned to <2.0.0 and SciPy pinned to <2.0.0.

**Known deprecation handling:**
- `np.trapz` deprecated in NumPy 2.0 - compatibility shim used across codebase: `_trapz = np.trapezoid if hasattr(np, 'trapezoid') else np.trapz`
- `scipy.signal.pade` removed in SciPy 1.17 - custom `_pade()` implementation in `backend/rl/es_policy.py`
- Applied in: `backend/simulations/signal_operations.py`, `backend/simulations/convolution_simulator.py`, `backend/simulations/impulse_construction.py`, `backend/simulations/ivt_fvt_visualizer.py`, `backend/core/controllers.py`, `backend/rl/es_policy.py`, `backend/rl/mlp_policy.py`

---

*Stack analysis: 2026-03-27*
