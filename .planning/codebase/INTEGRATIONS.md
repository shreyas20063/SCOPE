# External Integrations

**Analysis Date:** 2026-03-27

## APIs & External Services

**None.** This is a fully self-contained application with zero external API dependencies. All computation runs locally on the backend. No third-party SaaS integrations (no Stripe, Supabase, AWS, Firebase, Auth0, Sentry, etc.).

## Data Storage

**Databases:**
- None. No database of any kind (no SQL, NoSQL, or embedded DB).
- All simulation state is held in-memory in `active_simulators` dict (`backend/main.py` line 172).
- Simulator instances are created on first request and persist in the Python process memory.

**Caching:**
- Custom in-memory LRU cache with TTL (`backend/utils/cache.py`)
- Cache stats exposed via `/api/analytics` endpoint
- Periodic cleanup every 5 minutes (`backend/main.py` line 85)
- No Redis, Memcached, or external cache

**File Storage:**
- Local filesystem only
- RL model weights: `backend/assets/models/es_pid_policy.json`, `backend/assets/models/a2c_pid_tuner.json`
- Audio sample: `backend/assets/audio_sample.wav` (used by audio frequency response simulation)
- Aliasing quantization assets: `backend/assets/aliasing_quantization/` directory
- No cloud storage (S3, GCS, Azure Blob)

**Client-Side Storage:**
- `localStorage` used as inter-simulation data bridge
  - Block Diagram Builder exports to `localStorage['blockDiagram_export']`
  - Signal Flow Scope imports from same key
- Hub context (`frontend/src/contexts/HubContext.jsx`) stores shared system data in React state (not persisted)

## Authentication & Identity

**Auth Provider:**
- None. No authentication or user identity system.
- No login, sessions, tokens, or user accounts.
- All API endpoints are publicly accessible.
- Rate limiting middleware exists (`backend/utils/rate_limiter.py`) but is disabled in `backend/main.py` (commented out at line 157).

## Monitoring & Observability

**Error Tracking:**
- None (no Sentry, Datadog, or external error tracking)
- Python `logging` module with basicConfig (`backend/main.py` line 51)

**Logs:**
- Python standard `logging` at INFO level
- Format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- Request logging via custom middleware (`backend/main.py` line 124) - logs endpoint, method, status code, duration, client IP
- Health check requests excluded from logging
- Performance monitor (`backend/utils/monitoring.py`) tracks uptime, cache hits, WS connections

**Analytics:**
- Custom analytics endpoint: `GET /api/analytics`
- Returns: performance stats, cache stats, rate limiter stats, WebSocket stats
- Purpose: Research paper metrics, not production monitoring

## CI/CD & Deployment

**Hosting:**
- No deployment configuration detected
- No Dockerfile, docker-compose, render.yaml, Procfile, vercel.json, or netlify.toml
- `.env.production` exists (contents not read) suggesting production deployment is configured elsewhere

**CI Pipeline:**
- None detected. No `.github/workflows/`, no `.gitlab-ci.yml`, no `Jenkinsfile`

**Linting/Formatting:**
- None configured. No ESLint, Prettier, Black, Ruff, or Biome config files detected.

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None

## WebSocket Communication

**Real-time Updates:**
- Endpoint: `WS /api/simulations/{sim_id}/ws`
- Custom WebSocket manager: `backend/utils/websocket_manager.py`
- Features: per-connection rate limiting (10 msg/sec), broadcast to all connections for a sim ID
- Used for: real-time parameter updates, RL training progress broadcasting
- Client reconnection handling: managed in `frontend/src/hooks/useSimulation.js`

## Inter-Simulation Communication

**System Hub:**
- Backend: `backend/routes/hub.py` (validation endpoint), `backend/core/hub_validator.py` (math enrichment)
- Frontend: `frontend/src/contexts/HubContext.jsx`, `frontend/src/hooks/useHub.js`, `frontend/src/components/HubPanel.jsx`
- Pattern: Simulations push transfer function / state-space data to shared hub slots via `to_hub_data` action
- Hub validates and enriches data (poles, zeros, stability, controllability) via `POST /api/hub/validate`
- Other simulations can pull from hub via `from_hub_data` action
- Slots: control, signal, circuit, optics
- 100KB payload size guard on validation endpoint
- NaN/Inf checks, TF order<100, SS dimension n<50 limits

**localStorage Bridge:**
- Block Diagram Builder -> Signal Flow Scope data transfer via `localStorage['blockDiagram_export']`
- JSON serialized block diagram topology

## Environment Configuration

**Required env vars:**
- None strictly required for development (all have defaults)
- `VITE_API_URL` - Optional; set in production to point frontend at backend URL
- `DEBUG_MODE` - Optional; enables debug logging when set to "true"

**Secrets location:**
- `.env.development`, `.env.production`, `.env.example` at project root
- No API keys, database credentials, or external service tokens detected in codebase
- No secrets management system (no Vault, AWS Secrets Manager, etc.)

---

*Integration audit: 2026-03-27*
