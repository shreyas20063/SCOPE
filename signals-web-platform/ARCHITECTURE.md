# System Architecture

Technical architecture documentation for the Signals & Systems Web Platform.

## Overview

The platform is a full-stack web application providing interactive signal processing simulations for educational purposes. It's designed to handle 100+ concurrent users with real-time visualization capabilities.

```
                                    ┌─────────────────────┐
                                    │   Load Balancer     │
                                    │   (Cloud/nginx)     │
                                    └─────────┬───────────┘
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    │                         │                         │
         ┌──────────▼──────────┐   ┌──────────▼──────────┐   ┌──────────▼──────────┐
         │  Frontend (nginx)   │   │  Frontend (nginx)   │   │  Frontend (nginx)   │
         │    React + Vite     │   │    React + Vite     │   │    React + Vite     │
         └──────────┬──────────┘   └──────────┬──────────┘   └──────────┬──────────┘
                    │                         │                         │
                    └─────────────────────────┼─────────────────────────┘
                                              │
                                    ┌─────────▼───────────┐
                                    │   API Gateway       │
                                    │   (nginx proxy)     │
                                    └─────────┬───────────┘
                                              │
         ┌────────────────────────────────────┼────────────────────────────────────┐
         │                                    │                                    │
┌────────▼────────┐                ┌──────────▼──────────┐                ┌────────▼────────┐
│  Backend (1)    │                │  Backend (2)        │                │  Backend (N)    │
│  FastAPI        │                │  FastAPI            │                │  FastAPI        │
│  Gunicorn       │                │  Gunicorn           │                │  Gunicorn       │
│  4 workers      │                │  4 workers          │                │  4 workers      │
└────────┬────────┘                └──────────┬──────────┘                └────────┬────────┘
         │                                    │                                    │
         └────────────────────────────────────┼────────────────────────────────────┘
                                              │
                                    ┌─────────▼───────────┐
                                    │   In-Memory Cache   │
                                    │   (LRU, per-inst.)  │
                                    └─────────────────────┘
```

## Technology Stack

### Frontend

| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | React 18.2 | UI components and state management |
| Build Tool | Vite 5.0 | Fast bundling, HMR, code splitting |
| Visualization | Plotly.js 2.28 | Interactive 2D plots |
| 3D Graphics | Three.js 0.182 | 3D pendulum visualization |
| HTTP Client | Axios 1.6 | REST API calls |
| Routing | React Router 6 | SPA navigation |
| Styling | CSS Modules | Scoped component styles |

**Build Optimizations:**
- Code splitting by route
- Tree shaking for unused code
- Terser minification
- Asset fingerprinting for caching

### Backend

| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | FastAPI 0.109 | Async REST API + WebSocket |
| ASGI Server | Uvicorn 0.27 | Production server (dev) |
| WSGI Server | Gunicorn | Production server (workers) |
| Validation | Pydantic 2.5 | Request/response schemas |
| Numerics | NumPy 2.0+ | Array operations |
| Signal Processing | SciPy 1.10+ | Filters, FFT, ODE solvers |
| Image Processing | Pillow 10+ | Image manipulation |

**Production Configuration:**
- 4 Gunicorn workers per instance
- Uvicorn worker class for async
- 120s timeout for long computations
- Graceful shutdown handling

### Infrastructure

| Component | Technology | Purpose |
|-----------|------------|---------|
| Containerization | Docker | Reproducible builds |
| Orchestration | Docker Compose | Multi-container deployment |
| Reverse Proxy | nginx | Static serving, API proxy |
| CI/CD | GitHub Actions | Automated testing and deployment |
| Container Registry | GitHub Packages | Docker image storage |

## Simulations

The platform includes 13 interactive simulations:

| ID | Name | Category | Complexity |
|----|------|----------|------------|
| rc-lowpass | RC Lowpass Filter | Filters | Basic |
| aliasing-quantization | Aliasing & Quantization | Sampling | Basic |
| convolution | Convolution | Operations | Intermediate |
| ct-dt-poles | CT/DT Pole Mapping | Systems | Intermediate |
| dc-motor | DC Motor Control | Control | Advanced |
| feedback-system | Feedback Analysis | Control | Advanced |
| fourier-phase-magnitude | Fourier Phase/Magnitude | Transforms | Intermediate |
| fourier-series | Fourier Series | Transforms | Basic |
| furuta-pendulum | Furuta Pendulum | Control | Advanced |
| lens-optics | Lens Optics | Convolution | Intermediate |
| modulation | AM/FM Modulation | Communications | Intermediate |
| second-order-system | Second-Order Response | Systems | Basic |
| amplifier-topologies | Amplifier Topologies | Circuits | Intermediate |

## API Design

### REST Endpoints

```
GET  /health                           # Health check
GET  /health/ready                     # Readiness with metrics
GET  /api/v1/analytics                 # Performance metrics

GET  /api/v1/simulations               # List all simulations
GET  /api/v1/simulations/{id}          # Get simulation metadata
GET  /api/v1/simulations/{id}/state    # Get current state
POST /api/v1/simulations/{id}/execute  # Execute action
POST /api/v1/simulations/{id}/update   # Update parameters
GET  /api/v1/simulations/{id}/export/csv  # Export data

WS   /api/v1/simulations/{id}/ws       # Real-time updates
```

### WebSocket Protocol

```json
// Client → Server
{"action": "update", "params": {"frequency": 100}}
{"action": "reset", "params": {}}
{"action": "ping"}

// Server → Client
{"success": true, "type": "update", "plots": [...], "parameters": {...}}
{"success": true, "type": "reset", "plots": [...]}
{"success": true, "type": "pong"}
{"success": false, "type": "error", "error": "Rate limit exceeded"}
```

## Performance Optimizations

### Caching Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                        Request Flow                             │
├─────────────────────────────────────────────────────────────────┤
│  1. Request arrives                                             │
│  2. Generate cache key: hash(sim_id + params)                   │
│  3. Check LRU cache (O(1) lookup)                               │
│  4. If HIT: return cached result (< 1ms)                        │
│  5. If MISS: compute simulation (10-100ms)                      │
│  6. Cache result with TTL (5 minutes)                           │
│  7. Return response                                             │
└─────────────────────────────────────────────────────────────────┘
```

**Cache Configuration:**
- Max size: 10,000 entries (production)
- TTL: 5 minutes
- Expected hit rate: 80%+ for typical usage

### Response Compression

- GZip enabled for responses > 500 bytes
- Typical compression ratio: 60-80% for JSON plot data
- Reduces bandwidth significantly for large plots

### Plot Data Optimization

- Automatic subsampling for large datasets
- Max 2,000 points per trace by default
- Preserves visual quality while reducing payload

## Security

### Headers

All responses include:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`

### Rate Limiting

- HTTP: 100 requests/minute per IP (configurable)
- WebSocket: 10 messages/second per connection
- Prevents abuse while allowing educational use

### Container Security

- Non-root user in containers
- Minimal base images (slim/alpine)
- No secrets in images (runtime injection)

## Scaling

### Capacity Planning

| Users | Backend Instances | RAM per Instance | Expected Latency |
|-------|-------------------|------------------|------------------|
| 25 | 1 | 512MB | <50ms |
| 50 | 2 | 512MB | <50ms |
| 100 | 4 | 512MB | <100ms |
| 200 | 8 | 1GB | <100ms |

### Horizontal Scaling

```yaml
# docker-compose.prod.yml
services:
  backend:
    deploy:
      replicas: 4  # Adjust based on load
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

### Vertical Scaling

For computationally intensive simulations (Furuta pendulum, DC motor):
- Increase worker count per instance
- Add more CPU cores
- Consider GPU acceleration for future

## Monitoring

### Built-in Metrics

Available at `/api/v1/analytics`:

```json
{
  "performance": {
    "total_requests": 12345,
    "avg_response_time_ms": 45.2,
    "p95_response_time_ms": 120.5,
    "error_rate": 0.001
  },
  "cache": {
    "size": 1500,
    "max_size": 10000,
    "hit_rate": 0.85,
    "hits": 10500,
    "misses": 1845
  },
  "websocket": {
    "active_connections": 42,
    "total_messages": 50000
  }
}
```

### Recommended Tools

| Purpose | Tool | Notes |
|---------|------|-------|
| Uptime | Uptime Robot | Free, 5-min checks |
| Errors | Sentry | Detailed stack traces |
| Logs | Cloud provider | CloudWatch, Papertrail |
| APM | Datadog/New Relic | Full performance monitoring |

## Development Workflow

### Branching Strategy

```
main ──────────────────────────────────────────▶ Production
  │
  └── develop ─────────────────────────────────▶ Staging
        │
        ├── feature/new-simulation ────────────▶ Feature branches
        │
        └── bugfix/websocket-reconnect ────────▶ Bug fixes
```

### Deployment Flow

```
1. Developer pushes to feature branch
2. Opens PR to develop
3. CI runs tests, builds images
4. PR reviewed and merged
5. Auto-deploy to staging
6. Manual promotion to production (merge develop → main)
7. Auto-deploy to production
```

## File Structure

```
signals-web-platform/
├── backend/
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Configuration settings
│   ├── requirements.txt        # Python dependencies
│   ├── Dockerfile              # Production container
│   ├── core/
│   │   ├── executor.py         # Async task execution
│   │   └── data_handler.py     # Data serialization
│   ├── simulations/
│   │   ├── catalog.py          # Simulation registry
│   │   ├── base_simulator.py   # Base class
│   │   └── *.py                # Individual simulations
│   └── utils/
│       ├── cache.py            # LRU cache implementation
│       ├── websocket_manager.py # WebSocket handling
│       ├── rate_limiter.py     # Rate limiting
│       └── monitoring.py       # Metrics collection
│
├── frontend/
│   ├── package.json            # Node dependencies
│   ├── vite.config.js          # Build configuration
│   ├── Dockerfile              # Production container
│   ├── nginx.conf              # nginx configuration
│   ├── index.html              # Entry HTML
│   └── src/
│       ├── components/         # React components
│       ├── pages/              # Page components
│       ├── services/           # API client
│       ├── hooks/              # Custom React hooks
│       └── styles/             # CSS files
│
├── docker-compose.yml          # Development setup
├── docker-compose.prod.yml     # Production setup
├── .dockerignore               # Docker build exclusions
├── .env.example                # Environment template
├── DEPLOYMENT.md               # Deployment guide
└── ARCHITECTURE.md             # This file
```
