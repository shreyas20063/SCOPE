# Signals and Systems - Interactive Python Simulations

A comprehensive collection of interactive simulations for understanding Signals and Systems concepts. Features both standalone PyQt5 desktop applications and a full-stack web platform with real-time visualization.

## Course Information

- **Course**: Signals and Systems (EE204T)
- **Instructor**: Prof. Ameer Mulla
- **Author**: Duggimpudi Shreyas Reddy

## Features

- **Web Platform** - Full-stack React + FastAPI application with real-time WebSocket updates
- **Desktop Applications** - Professional PyQt5 GUI with matplotlib visualization
- **29+ Interactive Simulations** - Comprehensive coverage of signals and systems topics across 5 categories
- **3D Visualization** - Three.js-based 3D rendering for complex systems
- **Quiz Modes** - Built-in quizzes to test your understanding
- **Modular Architecture** - Clean separation of GUI, core logic, and utilities

## Web Platform (Recommended)

The web platform provides a modern, browser-based interface for all simulations with real-time interactivity.

### Quick Start - Web Platform

```bash
# Clone the repository
git clone https://github.com/shreyas20063/Signals_and_Systems_Python_simulations.git
cd Signals_and_Systems_Python_simulations

# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --port 8000 --reload

# Frontend (new terminal)
cd frontend
npm install && npm run dev
# Access at http://localhost:3001
```

### Web Platform Simulations

#### Signal Processing

| # | Simulation | Description |
|---|-----------|-------------|
| 1 | **Aliasing & Quantization** | Explore the Nyquist theorem, aliasing effects, and compare quantization methods (Standard, Dither, Robert's). Features audio aliasing, audio quantization, and image quantization demos. |
| 2 | **Convolution Simulator** | Visualize continuous and discrete convolution operations step-by-step. Understand how signals combine through convolution with interactive animations. |
| 3 | **Modulation Techniques** | Explore AM, FM/PM, and FDM modulation with real audio. Switch between Amplitude Modulation, Frequency/Phase Modulation, and Frequency Division Multiplexing demos. |
| 4 | **Signal Operations Playground** | Interactive canvas for exploring signal transformations: time-scaling, time-shifting, time-reversal, amplitude scaling, and DC offset. Includes a quiz mode to test your understanding. |
| 5 | **Sampling & Reconstruction** | Explore how sampling interval affects signal reconstruction fidelity. Compare zero-order hold, linear interpolation, and ideal sinc reconstruction methods. Visualize the Nyquist criterion in action. |
| 6 | **Feedback & Convergence Explorer** | Explore how a single feedback loop with gain p₀ creates geometric sequences. Watch the impulse response y[n] = p₀ⁿ converge or diverge as you adjust the pole. |
| 7 | **DT Difference Equation Solver** | Step-by-step evaluation of discrete-time difference equations with synchronized block diagram visualization. Watch signal values propagate through gain, delay, and adder blocks one sample at a time. |
| 8 | **Polynomial Multiplication** | Visualize the tabular/anti-diagonal method for multiplying two operator series. Watch how collecting terms along anti-diagonals produces the combined unit-sample response of cascaded first-order systems. |
| 9 | **Operator Algebra Visualizer** | Explore the R-operator (delay operator) algebra for discrete-time systems. Type an operator polynomial and instantly see the expanded form, factored form, difference equation, block diagram, and impulse response. |
| 10 | **Pole Behavior Explorer** | Drag a pole along the real number line and watch the first-order DT system response update in real time. See how pole location determines convergence, divergence, and alternating-sign behavior. Includes quiz mode. |
| 11 | **Cyclic Path Detector** | Detect cyclic signal paths in block diagrams. Identify feedback loops, classify systems as FIR or IIR, and test your understanding in quiz mode. |
| 12 | **Cascade & Parallel Decomposition** | Decompose a second-order DT system into cascade (series) and parallel (partial fraction) forms. Watch step-by-step factoring and verify that all three representations produce the same impulse response. |
| 13 | **Fundamental Modes Superposition** | Visualize how any Nth-order DT system's unit-sample response is a weighted sum of N fundamental modes (geometric sequences). Adjust poles and weights to see how individual modes combine. |
| 14 | **DT ↔ CT Comparator** | Side-by-side comparison of first-order DT and CT systems sharing the same pole value p. See how pⁿu[n] in DT and eᵖᵗu(t) in CT produce fundamentally different stability behavior. |
| 15 | **Unit Impulse Construction** | Build intuition for the Dirac delta function by watching rectangular pulses of width 2ε and height 1/(2ε) converge to δ(t) as ε→0. See the integral converge to u(t) and pass the pulse through a first-order CT system. |
| 16 | **CT Impulse Response Builder** | Build the continuous-time impulse response e^(pt)u(t) term-by-term from the Taylor/operator series expansion. Watch partial sums converge to the exact exponential for stable poles and diverge for unstable poles. |
| 17 | **DT System Representation Navigator** | Interactive concept map showing five equivalent representations of a DT LTI system: block diagram, difference equation, system functional H(R), system function H(z), and impulse response h[n]. |

#### Circuits

| # | Simulation | Description |
|---|-----------|-------------|
| 18 | **RC Lowpass Filter** | Interactive RC filter simulation showing frequency response and filtering of square wave input signals. Adjust frequency and RC time constant in real-time. |
| 19 | **Amplifier Topologies** | Explore various amplifier configurations including simple, feedback, push-pull (crossover distortion), and compensated designs. Visualize gain curves, transfer characteristics, and I/O signals. |
| 20 | **Feedback System Analysis** | Interactive visualization of negative feedback effects on amplifier performance. Compare open-loop vs closed-loop behavior including gain, bandwidth, rise time, and pole locations. |

#### Control Systems

| # | Simulation | Description |
|---|-----------|-------------|
| 21 | **DC Motor Feedback Control** | Interactive simulation demonstrating feedback control principles for DC motors. Explore how amplifier gain, feedback, and motor parameters affect system behavior through pole-zero maps and step response. |
| 22 | **Second-Order System Response** | Explore second-order system dynamics including pole locations, frequency response, and damping behavior. Visualize how Q-factor affects resonance, bandwidth, and transient response. |
| 23 | **Block Diagram Builder** | Build block diagrams by dragging and connecting Gain, Adder, Delay, and Integrator blocks. Switch between building diagrams to get transfer functions, or entering transfer functions to see their block diagram realization. |
| 24 | **Mass-Spring System** | Animated mass-spring-damper system showing how physical systems transform input signals. Watch the spring stretch and compress as base excitation x(t) becomes mass displacement y(t). |
| 25 | **Furuta Pendulum** | Interactive simulation of a rotary inverted pendulum with PID control. Features real-time 3D visualization, angle tracking, control torque plots, and stability analysis. |
| 26 | **Complex Poles & Sinusoidal Modes** | Visualize how complex conjugate poles of a CT second-order system produce sinusoidal oscillation from complex exponential modes. Explore s-plane pole locations, mode decomposition, Taylor series convergence, and the 3D helix of e^(jωt). |

#### Transforms

| # | Simulation | Description |
|---|-----------|-------------|
| 27 | **CT/DT Poles Conversion** | Interactive learning tool for understanding CT to DT system transformations using Forward Euler, Backward Euler, and Trapezoidal methods. Features S-plane and Z-plane visualization and stability analysis. |
| 28 | **Fourier Analysis: Phase vs Magnitude** | Interactive demonstration that phase carries more structural information than magnitude. Compare images/audio signals and their hybrids to see how phase dominates perception. |
| 29 | **Fourier Series** | Decompose periodic waveforms into harmonic components. Build signals from sine and cosine terms and visualize convergence with increasing harmonics. |
| 30 | **Z-Transform Properties Lab** | Interactive demonstration of the four key Z-transform properties: linearity, time delay, multiply-by-n, and convolution. See operations in both time domain and z-domain simultaneously. |
| 31 | **Z Transform & ROC Explorer** | Interactive z-plane visualization exploring Z transforms, regions of convergence, and how ROC determines causality. See how the same H(z) maps to different time-domain signals depending on the ROC. |
| 32 | **Inverse Z Transform Solver** | Step-by-step inverse Z transform solver. Factor the denominator, perform partial fraction decomposition, match Z-transform pairs based on ROC, and assemble the time-domain signal h[n]. |

#### Optics

| # | Simulation | Description |
|---|-----------|-------------|
| 33 | **Lens Optics** | Model optical systems using convolution. Simulate lens blur with diffraction-limited Airy disk PSF, aperture effects, atmospheric seeing, and analyze image quality with PSF cross-sections, encircled energy plots, and MTF curves. |

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

### Desktop Simulations

| # | Simulation | Description | Run Command |
|---|------------|-------------|-------------|
| 1 | Aliasing & Quantization | Nyquist theorem, aliasing, quantization methods | `python aliasing_quantization/main.py` |
| 2 | Amplifier Topologies | Simple, feedback, crossover, compensated amplifiers | `python amplifier_topologies/main.py` |
| 3 | Convolution Simulator | Step-by-step convolution visualization | `python convolution/main.py` |
| 4 | CT/DT Poles Conversion | S-plane to Z-plane pole transformations | `python ct_dt_poles/main.py` |
| 5 | DC Motor Control | First/second-order motor control systems | `python dc_motor/main.py` |
| 6 | Feedback System Analysis | Bode plots and pole trajectories | `python feedback_system_analysis/main.py` |
| 7 | Fourier Phase vs Magnitude | Image and audio Fourier transforms | `python fourier_phase_vs_magnitude/main.py` |
| 8 | Fourier Series | Fourier series approximations | `python fourier_series/main.py` |
| 9 | Furuta Pendulum | 3D inverted pendulum with PID control | `python furuta_pendulum/main.py` |
| 10 | Lens Optics | PSF-based optical resolution simulation | `python lens_optics/main.py` |
| 11 | Modulation Techniques | AM, FM, and FDM modulation | `python modulation_techniques/main.py` |
| 12 | RC Lowpass Filter | Interactive filter frequency response | `python rc_lowpass_filter/main.py` |
| 13 | Second-Order System | Q factor variation and pole-zero analysis | `python second_order_system/main.py` |

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

## Learning Objectives

These simulations cover:

- **Signal Processing**: Sampling, aliasing, quantization, convolution, difference equations, operator algebra
- **Fourier Analysis**: Series, transforms, spectral analysis, phase vs magnitude
- **Filter Design**: Lowpass, highpass, bandpass filters
- **Modulation**: AM, FM, PM, multiplexing techniques
- **Control Systems**: PID control, stability analysis, mass-spring systems, feedback convergence
- **System Analysis**: Poles/zeros, Bode plots, step response, block diagrams
- **Z-Transforms**: Properties, ROC, inverse transforms, partial fractions
- **Optics**: PSF convolution, MTF, diffraction-limited imaging

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

## Acknowledgments

- Prof. Ameer Mulla for course guidance
- PyQt5, matplotlib, numpy, scipy, FastAPI, and React communities

---

*Educational simulations for Signals and Systems concepts.*
