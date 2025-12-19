# Interactive RC Lowpass Filter Simulator

This repository contains an interactive PyQt5-based simulator for visualizing the behavior of an RC low-pass filter in both the time and frequency domains. The project highlights how square-wave harmonics are attenuated and how the output waveform evolves as you adjust circuit parameters in real-time.

## Course Context

Created for **Signals and Systems (course code: EE204T)** under **Prof. Ameer Mulla** by **Duggimpudi Shreyas Reddy** and **Prathamesh Nerpagar**.

## Features

- Professional PyQt5 interface with embedded Matplotlib canvas
- Real-time interactive sliders for frequency, RC time constant, and amplitude
- Time domain visualization with input/output waveforms
- Frequency domain Bode plot with harmonic stems
- Smooth animation with play/pause controls
- Live status display showing filter state (passing/transitioning/filtering)
- Clean, modern UI design with color-coded controls

## Project Structure

```
Interactive_RC_Lowpass_Filter_Simulator/
├── main.py                 # Entry point - launches PyQt5 application
├── gui/
│   ├── __init__.py
│   └── main_window.py      # PyQt5 main window with embedded matplotlib
├── core/
│   ├── __init__.py
│   └── signals.py          # Signal processing and RC filter calculations
├── utils/
│   ├── __init__.py
│   └── constants.py        # Configuration constants and settings
├── assets/                 # (Reserved for future assets)
└── rc_lowpass/            # (Legacy structure - deprecated)
```

## Requirements

- Python 3.7+
- PyQt5
- matplotlib
- numpy

## Installation

```bash
pip install PyQt5 matplotlib numpy
```

## Running the Simulator

```bash
python main.py
```

## Usage

The application starts in a paused state. Use the on-screen controls to:

- Click **Play** button to start animation
- Drag sliders to adjust parameters in real-time (works while paused or playing)
- Click **Pause** button to stop animation
- Click **Reset** button to return to default values and pause

### Parameters

- **Frequency**: 1-300 Hz (square wave input frequency)
- **RC Time Constant**: 0.1-10.0 ms (filter time constant)
- **Amplitude**: 1.0-10.0 V (input signal amplitude)

The frequency-domain pane displays harmonic stems against the RC filter magnitude response to make attenuation patterns easy to interpret. The status panel shows the cutoff frequency, input frequency, their ratio, and the current filter state.
