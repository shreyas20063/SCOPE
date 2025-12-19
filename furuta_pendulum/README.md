# Furuta Pendulum Simulator - PyQt5 Professional Version

Interactive 3D simulator of the rotary inverted (Furuta) pendulum, controlled by a tunable PID loop. Built with PyQt5 for a professional, responsive user interface.

**Course:** Signals and Systems (EE204T)
**Instructor:** Prof. Ameer Mulla
**Authors:** Duggimpudi Shreyas Reddy, Prathamesh Nerpagar

---

## Features

- **Professional PyQt5 Interface**: Modern, responsive GUI with embedded matplotlib visualizations
- **Real-time 3D View**: Interactive 3D visualization with torque and angle plots for quick feedback
- **Parameter Control**: Sliders for mass, arm length, pendulum length, and simulation speed
- **PID Tuning**: Live adjustment of Kp, Ki, and Kd gains with anti-windup and saturation handling
- **System Monitoring**: Real-time status panel showing all system states and control signals
- **Interactive Controls**: Start/Pause, Reset, and Disturbance buttons for experiments

---

## Requirements

- Python 3.9 or newer
- Python packages: `numpy`, `matplotlib`, `PyQt5`

---

## Quick Start

```bash
python3 -m venv .venv                # optional: keep dependencies isolated
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install numpy matplotlib PyQt5   # install dependencies
python main.py                       # launch the PyQt5 simulator
```

Once the PyQt5 window opens you will see:

- **Left Panel**:
  - 3D rendering of the arm and pendulum (top)
  - Time-series plots for pendulum angle and control torque (bottom)
- **Right Panel**:
  - System status display showing real-time state
  - Sliders for physical parameters (mass, lengths)
  - Sliders for PID gains (Kp, Ki, Kd)
  - Simulation speed control
  - Control buttons: Start/Pause, Reset, Disturb
  - Information panel with usage tips

Use the mouse to rotate the 3D view; the status panel continuously reports arm direction (ω_φ), torque, and system state.

---

## Controls at a Glance

- **Start/Pause** toggles integration.
- **Reset** restores the tuned defaults (state, parameters, gains, slider positions, history).
- **Disturb** adds a quick impulse to test disturbance rejection.
- **Speed** slider changes simulation playback speed (handy to observe fast reversals).
- PID sliders (`Kp`, `Ki`, `Kd`) adjust controller aggressiveness in real time.

---

## Project Structure

```
furuta_pendulum/
├── main.py                  # Entry point
├── requirements.txt         # Dependencies
├── core/
│   ├── pendulum_dynamics.py # System model + RK4 integrator
│   └── pid_controller.py    # PID control with anti-windup
├── gui/
│   └── main_window.py       # PyQt5 GUI with 3D visualization
├── utils/
└── assets/
```

---

## How It Works

- The **physics model** (`core/pendulum_dynamics.py`) integrates the nonlinear Furuta pendulum equations with a fourth-order Runge-Kutta step (`dt = 0.01 s`).
- The **PID controller** (`core/pid_controller.py`) drives the pendulum angle (`θ`) to zero, limiting torque output and clamping the integral term to avoid wind-up.
- The **PyQt5 GUI** (`gui/main_window.py`) provides:
  - Embedded matplotlib canvases for 3D visualization and real-time plots
  - QTimer-based animation loop that advances physics and updates displays
  - Interactive widgets (sliders, buttons) connected to simulation parameters
  - Real-time status monitoring and control feedback
- Direction arrows and torque color cues make it easy to spot the frequent arm reversals that keep the pendulum upright.

---

## Suggested Experiments

1. Dial `Kp`, `Ki`, and `Kd` to practice PID tuning—watch the angle plot for overshoot and settling time.
2. Vary mass, arm length, or pendulum length to explore how inertia changes controller performance.
3. Use `Disturb` repeatedly to study disturbance rejection and the resulting torque spikes.
4. Slow the simulation to ≈0.3× speed to clearly observe the arm reversing direction multiple times per second.

---

## Troubleshooting

- **Window doesn't appear:** Ensure PyQt5 is properly installed (`pip install PyQt5`). On some systems, you may need to install additional Qt dependencies.
- **Import errors:** Make sure you're running from the correct directory and all dependencies are installed.
- **Simulation feels one-sided:** Check the torque plot (bottom right)—the arm reverses whenever the trace crosses zero.
- **Pendulum falls immediately:** Press `Reset` to restore defaults, or increase `Kp`/`Kd` using the sliders for a tighter controller.
- **3D view is laggy:** Try reducing the simulation speed or closing other applications to free up system resources.

---

*Educational simulation demonstrating inverted pendulum control with PID.*
