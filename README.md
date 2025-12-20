# Signals and Systems - Interactive Python Simulations

A comprehensive collection of 13 interactive simulations for understanding Signals and Systems concepts. All simulations feature professional PyQt5 interfaces with real-time visualization.

## Course Information

- **Course**: Signals and Systems (EE204T)
- **Instructor**: Prof. Ameer Mulla
- **Authors**: Duggimpudi Shreyas Reddy, Prathamesh Nerpagar

## Features

- **Professional PyQt5 GUI** - Modern, responsive interfaces
- **Real-time Visualization** - Interactive matplotlib plots
- **Modular Architecture** - Clean separation of GUI, core logic, and utilities

## Repository Structure

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

## Simulations

| # | Simulation | Description | Run Command |
|---|------------|-------------|-------------|
| 1 | [Aliasing & Quantization](aliasing_quantization/) | Nyquist theorem, aliasing, quantization methods | `python aliasing_quantization/main.py` |
| 2 | [Amplifier Simulator](amplifier_simulator/) | Simple, feedback, crossover, compensated amplifiers | `python amplifier_simulator/main.py` |
| 3 | [Convolution Simulator](convolution/) | Step-by-step convolution visualization | `python convolution/main.py` |
| 4 | [CT/DT Poles Conversion](ct_dt_poles/) | S-plane to Z-plane pole transformations | `python ct_dt_poles/main.py` |
| 5 | [DC Motor Control](dc_motor/) | First/second-order motor control systems | `python dc_motor/main.py` |
| 6 | [Feedback Amplifier](feedback_amplifier/) | Bode plots and pole trajectories | `python feedback_amplifier/main.py` |
| 7 | [Fourier Analysis](fourier_analysis/) | Image and audio Fourier transforms | `python fourier_analysis/main.py` |
| 8 | [Fourier Series](fourier_series/) | Fourier series approximations | `python fourier_series/main.py` |
| 9 | [Furuta Pendulum](furuta_pendulum/) | 3D inverted pendulum with PID control | `python furuta_pendulum/main.py` |
| 10 | [Lens Optics](lens_optics/) | PSF-based optical resolution simulation | `python lens_optics/main.py` |
| 11 | [Modulation Techniques](modulation_techniques/) | AM, FM, and FDM modulation | `python modulation_techniques/main.py` |
| 12 | [RC Lowpass Filter](rc_lowpass_filter/) | Interactive filter frequency response | `python rc_lowpass_filter/main.py` |
| 13 | [RLC Circuit](rlc_circuit/) | Q factor variation and pole-zero analysis | `python rlc_circuit/main.py` |

## Installation

### Requirements
- Python 3.8+
- PyQt5, numpy, matplotlib, scipy

### Quick Start

```bash
# Clone the repository
git clone https://github.com/shreyas20063/Signals_and_Systems_Python_simulations.git
cd Signals_and_Systems_Python_simulations

# Install all dependencies
pip install PyQt5 numpy matplotlib scipy opencv-python Pillow sounddevice

# Run any simulation
python simulation_name/main.py
```

### Per-Simulation Installation

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

## Contributing

Contributions are welcome! Submit pull requests or open issues for bug fixes, new features, or documentation improvements.

## Contact

- **Duggimpudi Shreyas Reddy** - [GitHub](https://github.com/shreyas20063)
- **Prathamesh Nerpagar** - [GitHub](https://github.com/aspirantee24bt017)

## Acknowledgments

- Prof. Ameer Mulla for course guidance
- PyQt5, matplotlib, numpy, and scipy communities

---

*Educational simulations for Signals and Systems concepts.*
