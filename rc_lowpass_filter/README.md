# Interactive RC Lowpass Filter Simulator

This repository contains an interactive Matplotlib-based simulator for visualising the behaviour of an RC low-pass filter in both the time and frequency domains. The project highlights how square-wave harmonics are attenuated and how the output waveform evolves as you adjust circuit parameters in real-time.

## Course Context

Created for **Signals and Systems (course code: EE204T)** under **Prof. Ameer Mulla** by **Duggimpudi Shreyas Reddy** and **Prathamesh Nerpagar**.

## Project Layout

- `main.py` – entry point that prints a banner and launches the simulator UI.
- `rc_lowpass/__init__.py` – exposes friendly imports for the package.
- `rc_lowpass/config/settings.py` – shared constants, slider ranges, and presentation text.
- `rc_lowpass/core/signals.py` – waveform generation, Runge–Kutta integration, and Bode calculations.
- `rc_lowpass/gui/simulator.py` – Matplotlib-based interactive interface wiring the UI to the core helpers.

## Running the Simulator

```bash
python main.py
```


The application starts paused. Use the on-screen controls to play, pause, reset, and tweak the square-wave frequency, RC time constant, and amplitude. The frequency-domain pane displays harmonic stems against the RC filter magnitude response to make attenuation patterns easy to interpret.
