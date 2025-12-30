# Signals & Systems Web Platform

A high-performance, interactive web platform for visualizing and exploring Signals and Systems concepts. Built with FastAPI and React, featuring real-time WebSocket updates, 3D visualizations, and 13 comprehensive simulations.

## Features

- **13 Interactive Simulations** - Comprehensive coverage of signals and systems topics
- **Real-time Updates** - WebSocket-powered instant parameter updates
- **3D Visualizations** - Three.js-based 3D rendering (Furuta Pendulum)
- **Responsive Design** - Works on desktop and mobile devices
- **Dark Theme** - Modern, eye-friendly interface
- **CSV Export** - Download simulation data for further analysis
- **Performance Optimized** - LRU caching, rate limiting, designed for 100+ concurrent users

## Tech Stack

### Backend
- **FastAPI** - High-performance Python web framework
- **Uvicorn** - ASGI server
- **NumPy/SciPy** - Scientific computing
- **Pillow** - Image processing
- **WebSocket** - Real-time bidirectional communication

### Frontend
- **React 18** - UI library
- **Vite** - Build tool and dev server
- **Plotly.js** - Interactive plotting
- **Three.js** - 3D graphics
- **React Router** - Client-side routing
- **Axios** - HTTP client

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- npm or yarn

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/shreyas20063/Signals_and_Systems_Python_simulations.git
cd Signals_and_Systems_Python_simulations/signals-web-platform
```

2. **Set up the backend**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Set up the frontend**
```bash
cd ../frontend
npm install
```

### Running Locally

**Start the backend** (Terminal 1):
```bash
cd backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Start the frontend** (Terminal 2):
```bash
cd frontend
npm run dev
```

Access the application at `http://localhost:5173`

## Docker Deployment

### Using Docker Compose (Recommended)
```bash
docker-compose up --build
```

This starts:
- Backend at `http://localhost:8000`
- Frontend at `http://localhost:3000`

### Individual Containers

**Backend:**
```bash
cd backend
docker build -t signals-backend .
docker run -p 8000:8000 signals-backend
```

**Frontend:**
```bash
cd frontend
docker build -t signals-frontend .
docker run -p 3000:3000 signals-frontend
```

## API Documentation

Once the backend is running, access the interactive API docs:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/simulations` | GET | List all simulations |
| `/api/v1/simulations/{id}` | GET | Get simulation details |
| `/api/v1/simulations/{id}/state` | GET | Get current simulation state |
| `/api/v1/simulations/{id}/execute` | POST | Execute simulation action |
| `/api/v1/simulations/{id}/update` | POST | Update parameters |
| `/api/v1/simulations/{id}/export/csv` | GET | Export data as CSV |
| `/api/v1/simulations/{id}/ws` | WS | WebSocket for real-time updates |
| `/health` | GET | Health check |
| `/health/ready` | GET | Readiness check with metrics |

## Project Structure

```
signals-web-platform/
├── backend/
│   ├── core/               # Core utilities (executor, data handler)
│   ├── simulations/        # Simulation implementations
│   │   ├── catalog.py      # Simulation metadata and controls
│   │   ├── base_simulator.py
│   │   ├── rc_lowpass_filter.py
│   │   ├── aliasing_quantization.py
│   │   ├── convolution_simulator.py
│   │   └── ... (13 total)
│   ├── utils/              # Caching, WebSocket manager, rate limiter
│   ├── assets/             # Static assets (images, audio)
│   ├── main.py             # FastAPI application
│   ├── config.py           # Configuration
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/     # React components
│   │   │   ├── SimulationViewer.jsx
│   │   │   ├── ControlPanel.jsx
│   │   │   ├── PlotDisplay.jsx
│   │   │   ├── FurutaPendulum3D.jsx
│   │   │   └── ...
│   │   ├── pages/          # Page components
│   │   ├── hooks/          # Custom React hooks
│   │   ├── services/       # API services
│   │   ├── styles/         # CSS styles
│   │   └── utils/          # Utility functions
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
└── docker-compose.yml
```

## Available Simulations

| # | Simulation | Category | Description |
|---|------------|----------|-------------|
| 1 | RC Lowpass Filter | Circuits | Frequency response and Bode plots |
| 2 | Aliasing & Quantization | Signal Processing | Nyquist theorem, sampling, ADC effects |
| 3 | Amplifier Topologies | Circuits | Simple, feedback, crossover, compensated |
| 4 | Convolution Simulator | Signal Processing | Step-by-step convolution visualization |
| 5 | CT/DT Poles Conversion | Transforms | S-plane to Z-plane transformations |
| 6 | DC Motor Control | Control Systems | Feedback control with pole analysis |
| 7 | Feedback System Analysis | Circuits | Bode plots and stability analysis |
| 8 | Fourier Phase vs Magnitude | Transforms | Phase dominance demonstration |
| 9 | Fourier Series | Transforms | Harmonic decomposition |
| 10 | Furuta Pendulum | Control Systems | 3D inverted pendulum with PID |
| 11 | Lens Optics | Optics | PSF, MTF, and image quality |
| 12 | Modulation Techniques | Signal Processing | AM, FM, PM, FDM |
| 13 | Second-Order System | Control Systems | Q-factor and resonance analysis |

## Configuration

### Backend Configuration (`backend/config.py`)
```python
CORS_SETTINGS = {
    "allow_origins": ["*"],
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}
API_PREFIX = "/api/v1"
```

### Frontend Configuration
Update the API base URL in `frontend/src/services/api.js` if deploying to a different host.

## Performance Features

- **LRU Cache**: In-memory caching with TTL for simulation results
- **Rate Limiting**: Configurable per-IP and global rate limits
- **WebSocket Manager**: Efficient connection pooling and message broadcasting
- **Security Headers**: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection
- **Performance Monitoring**: Built-in metrics endpoint at `/api/v1/analytics`

## Development

### Backend Development
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --log-level debug
```

### Frontend Development
```bash
cd frontend
npm run dev
```

### Building for Production
```bash
# Frontend build
cd frontend
npm run build  # Outputs to dist/

# Backend (no build step required)
# Use Gunicorn with Uvicorn workers for production:
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## Course Information

- **Course**: Signals and Systems (EE204T)
- **Instructor**: Prof. Ameer Mulla
- **Author**: [Duggimpudi Shreyas Reddy](https://github.com/shreyas20063)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-simulation`)
3. Commit your changes (`git commit -m 'Add new simulation'`)
4. Push to the branch (`git push origin feature/new-simulation`)
5. Open a Pull Request

## License

This project is for educational purposes. See the main repository for license details.

## Acknowledgments

- Prof. Ameer Mulla for course guidance
- FastAPI, React, Plotly.js, and Three.js communities
