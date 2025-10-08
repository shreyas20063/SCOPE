# Furuta Pendulum Simulator

Interactive 3D simulator of the rotary inverted (Furuta) pendulum, controlled by a tunable PID loop.

**Course:** Signals and Systems (EE204T)  
**Instructor:** Prof. Ameer Mulla  
**Authors:** Duggimpudi Shreyas Reddy, Prathamesh Nerpagar

---

## Features

- Real-time 3D view with torque and angle plots for quick feedback.
- Sliders for mass, arm length, pendulum length, and speed to explore different physical setups.
- PID controller with anti-windup and saturation handling; sliders expose `Kp`, `Ki`, and `Kd`.
- Reset and disturbance buttons for repeatable experiments and robustness checks.

---

## Requirements

- Python 3.9 or newer.
- Python packages: `numpy`, `matplotlib`.

`matplotlib` must be able to open an interactive window (Qt5, Tk, MacOSX backend, etc.).

---

## Quick Start

```bash
python3 -m venv .venv                # optional: keep dependencies isolated
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install numpy matplotlib         # install dependencies
python main.py                       # launch the interactive simulator
```

Once the window opens you will see:

- 3D rendering of the arm and pendulum.
- Time-series plots for pendulum angle and control torque.
- Sliders for PID gains, physical parameters, and playback speed.
- Buttons for `Start/Pause`, `Reset`, and `Disturb`.

Use the mouse to rotate the camera; the status panel in the window reports the arm direction (`ω_φ`) and applied torque.

---

## Controls at a Glance

- **Start/Pause** toggles integration.
- **Reset** restores the tuned defaults (state, parameters, gains, slider positions, history).
- **Disturb** adds a quick impulse to test disturbance rejection.
- **Speed** slider changes simulation playback speed (handy to observe fast reversals).
- PID sliders (`Kp`, `Ki`, `Kd`) adjust controller aggressiveness in real time.

---

## Project Layout

```
Furuta_Pendulum_Simulation/
├── main.py
└── src/
    ├── control/
    │   └── pid_controller.py        # PID law, anti-windup, component breakdown
    ├── physics/
    │   └── pendulum_dynamics.py     # System model + RK4 integrator
    └── gui/
        └── visualizer.py            # 3D scene, plots, widgets, event loop
```

`main.py` wires the three modules together and prints a short cheat-sheet when you run it from the terminal.

---

## How It Works

- The **physics model** integrates the nonlinear Furuta pendulum equations with a fourth-order Runge-Kutta step (`dt = 0.01 s`).
- The **PID controller** drives the pendulum angle (`θ`) to zero, limiting torque output and clamping the integral term to avoid wind-up.
- The **visualizer** advances the physics state, applies control, and updates the 3D scene plus plots each animation frame.
- Direction arrows and torque color cues make it easy to spot the frequent arm reversals that keep the pendulum upright.

---

## Suggested Experiments

1. Dial `Kp`, `Ki`, and `Kd` to practice PID tuning—watch the angle plot for overshoot and settling time.
2. Vary mass, arm length, or pendulum length to explore how inertia changes controller performance.
3. Use `Disturb` repeatedly to study disturbance rejection and the resulting torque spikes.
4. Slow the simulation to ≈0.3× speed to clearly observe the arm reversing direction multiple times per second.

---

## Troubleshooting

- **No figure window appears:** ensure you run Python with a GUI-capable `matplotlib` backend (Tk, Qt, MacOSX, etc.).
- **Simulation feels one-sided:** check the torque plot—the arm reverses whenever the trace crosses zero.
- **Pendulum falls immediately:** press `Reset` to restore defaults, or increase `Kp`/`Kd` for a tighter controller.

---

Questions or suggestions? Reach out to the authors listed above and enjoy exploring the Furuta pendulum! 🎡
