# Furuta Pendulum Simulator

Interactive 3D demo of the rotary inverted pendulum (Furuta pendulum) controlled by a tunable PID loop.

**Course:** Signals and Systems (EE204T)  
**Instructor:** Prof. Ameer Mulla  
**Authors:** Duggimpudi Shreyas Reddy, Prathamesh Nerpagar

---

## Quick Start

```bash
pip install numpy matplotlib        # install dependencies
python main.py                      # launch the simulator
```

Once the window opens, use the sliders to tweak physical parameters and PID gains, and the buttons to start, reset, or disturb the system.

---

## How the Stabilisation Works (Why the Arm Seems to “Spin” One Way)

- The controller uses **angular acceleration** to create inertial forces that push the pendulum upright; absolute arm position is irrelevant.
- The arm actually **reverses direction many times per second**. To spot it:
  - Watch the **Torque plot** – the line crosses zero whenever the arm reverses.
  - Check the status text – `ω_φ` flips sign and the ↻/↺ symbol changes.
  - Slow the **Speed** slider (e.g. 0.3×) or press **Disturb** to make reversals obvious.

---

## Project Layout

```
Furuta_Pendulum_Simulation/
├── main.py                      # Entrypoint using the modular design
└── src/
    ├── control/pid_controller.py      # PID logic (anti-windup, saturation)
    ├── physics/pendulum_dynamics.py   # System model + RK4 integrator
    └── gui/visualizer.py              # 3D scene, plots, sliders, buttons
```

The modular version keeps physics, control, and GUI separate for easier maintenance and experimentation.

---

## Recent Highlights

- Reset button now restores **state, parameters, PID gains, slider positions, and plots**.
- Legacy single-file script removed; `main.py` is now the single entry point.
- Default PID gains set to `Kp=150`, `Kd=25`, `Ki=5` to match the current controller defaults.
- GUI overlays explain how to tell the arm is changing direction.
- Added in-code docstrings and comments for easier study.

---

## Try These Experiments

1. **PID tuning practice** – move Kp/Kd/Ki and watch the effect on the angle plot.  
2. **Physical parameter sweeps** – change pendulum length or mass and see how the controller copes.  
3. **Disturbance rejection** – spam the **Disturb** button and track torque reversals in the control plot.

---

## Troubleshooting

- **No window?** Ensure you are running Python with a GUI-capable matplotlib backend.
- **Arm seems one-sided?** Slow the speed slider and check the torque plot; the reversals are simply fast.
- **Pendulum drops immediately?** Reset to restore tuned defaults, or raise Kp and Kd.

---

Questions or suggestions? Reach out to the authors listed above. Enjoy experimenting! 🎡
