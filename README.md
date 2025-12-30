# Signals and Systems - Interactive Python Simulations

A comprehensive collection of interactive simulations for understanding Signals and Systems concepts. Features both standalone PyQt5 desktop applications and a full-stack web platform with real-time visualization.

## Course Information

- **Course**: Signals and Systems (EE204T)
- **Instructor**: Prof. Ameer Mulla
- **Authors**: Duggimpudi Shreyas Reddy, Prathamesh Nerpagar

## Features

- **Web Platform** - Full-stack React + FastAPI application with real-time WebSocket updates
- **Desktop Applications** - Professional PyQt5 GUI with matplotlib visualization
- **13 Interactive Simulations** - Comprehensive coverage of signals and systems topics
- **3D Visualization** - Three.js-based 3D rendering for complex systems
- **Modular Architecture** - Clean separation of GUI, core logic, and utilities

## Web Platform (Recommended)

The web platform provides a modern, browser-based interface for all simulations with real-time interactivity.

### Quick Start - Web Platform

```bash
# Clone the repository
git clone https://github.com/shreyas20063/Signals_and_Systems_Python_simulations.git
cd Signals_and_Systems_Python_simulations/signals-web-platform

# Option 1: Docker (Recommended)
docker-compose up --build
# Access at http://localhost:3000

# Option 2: Manual Setup
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --port 8000 --reload

# Frontend (new terminal)
cd frontend
npm install && npm run dev
# Access at http://localhost:5173
```

See [signals-web-platform/README.md](signals-web-platform/README.md) for detailed documentation.

## Desktop Applications (PyQt5)

Standalone desktop applications with professional interfaces.

### Repository Structure

```
simulation_name/
├── gui/              # PyQt5 GUI components
├── core/             # Core simulation logic
├── utils/            # Utility functions
├── assets/           # Resources (audio, images)
├── main.py           # Entry point
├── requirements.txt  # Dependencies
└── README.md         # Documentation
```

### Simulations

| # | Simulation | Description | Run Command |
|---|------------|-------------|-------------|
| 1 | [Aliasing & Quantization](aliasing_quantization/) | Nyquist theorem, aliasing, quantization methods | `python aliasing_quantization/main.py` |
| 2 | [Amplifier Topologies](amplifier_topologies/) | Simple, feedback, crossover, compensated amplifiers | `python amplifier_topologies/main.py` |
| 3 | [Convolution Simulator](convolution/) | Step-by-step convolution visualization | `python convolution/main.py` |
| 4 | [CT/DT Poles Conversion](ct_dt_poles/) | S-plane to Z-plane pole transformations | `python ct_dt_poles/main.py` |
| 5 | [DC Motor Control](dc_motor/) | First/second-order motor control systems | `python dc_motor/main.py` |
| 6 | [Feedback System Analysis](feedback_system_analysis/) | Bode plots and pole trajectories | `python feedback_system_analysis/main.py` |
| 7 | [Fourier Phase vs Magnitude](fourier_phase_vs_magnitude/) | Image and audio Fourier transforms | `python fourier_phase_vs_magnitude/main.py` |
| 8 | [Fourier Series](fourier_series/) | Fourier series approximations | `python fourier_series/main.py` |
| 9 | [Furuta Pendulum](furuta_pendulum/) | 3D inverted pendulum with PID control | `python furuta_pendulum/main.py` |
| 10 | [Lens Optics](lens_optics/) | PSF-based optical resolution simulation | `python lens_optics/main.py` |
| 11 | [Modulation Techniques](modulation_techniques/) | AM, FM, and FDM modulation | `python modulation_techniques/main.py` |
| 12 | [RC Lowpass Filter](rc_lowpass_filter/) | Interactive filter frequency response | `python rc_lowpass_filter/main.py` |
| 13 | [Second-Order System](second_order_system/) | Q factor variation and pole-zero analysis | `python second_order_system/main.py` |

### Installation - Desktop Apps

#### Requirements
- Python 3.8+
- PyQt5, numpy, matplotlib, scipy

#### Quick Start

```bash
# Clone the repository
git clone https://github.com/shreyas20063/Signals_and_Systems_Python_simulations.git
cd Signals_and_Systems_Python_simulations

# Install all dependencies
pip install PyQt5 numpy matplotlib scipy opencv-python Pillow sounddevice

# Run any simulation
python simulation_name/main.py
```

#### Per-Simulation Installation

```bash
cd simulation_name
pip install -r requirements.txt
python main.py
```

## Learning Objectives

These simulations cover:

- **Signal Processing**: Sampling, aliasing, quantization, convolution
- **Fourier Analysis**: Series, transforms, spectral analysis
- **Filter Design**: Lowpass, highpass, bandpass filters
- **Modulation**: AM, FM, PM, multiplexing techniques
- **Control Systems**: PID control, stability analysis
- **System Analysis**: Poles/zeros, Bode plots, step response

## Tech Stack

### Web Platform
- **Backend**: FastAPI, Python 3.11, NumPy, SciPy, WebSocket
- **Frontend**: React 18, Vite, Plotly.js, Three.js
- **Deployment**: Docker, Docker Compose
- **Performance**: GZip compression, lazy loading, code splitting, LRU caching

### Desktop Applications
- **GUI**: PyQt5
- **Visualization**: Matplotlib
- **Computation**: NumPy, SciPy

## Performance Optimizations

The web platform includes several performance enhancements:

| Feature | Benefit |
|---------|---------|
| GZip Compression | 60-80% smaller API responses |
| Lazy Loading | Faster initial page load |
| Code Splitting | Vendor chunks cached separately |
| Request Debouncing | 80% fewer API calls during slider interaction |
| LRU Caching | Instant response for repeated parameters |
| Plot Subsampling | Reduced bandwidth for large datasets |

## Contributing

Contributions are welcome! Submit pull requests or open issues for bug fixes, new features, or documentation improvements.

## Contact

- **Duggimpudi Shreyas Reddy** - [GitHub](https://github.com/shreyas20063)
- **Prathamesh Nerpagar** - [GitHub](https://github.com/aspirantee24bt017)

## Acknowledgments

- Prof. Ameer Mulla for course guidance
- PyQt5, matplotlib, numpy, scipy, FastAPI, and React communities

---

*Educational simulations for Signals and Systems concepts.*
