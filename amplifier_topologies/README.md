# Amplifier Feedback Simulator

Python application for simulating and visualizing different amplifier configurations, including feedback systems and crossover distortion compensation.

## Course Information

**Course:** Signals and Systems (EE204T)
**Instructor:** Prof. Ameer Mulla
**Authors:** Duggimpudi Shreyas Reddy, Prathamesh Nerpagar

## Features

- **Four Amplifier Configurations:**
  - Simple Amplifier
  - Feedback System
  - Crossover Distortion
  - Compensated System

- **Real-time Visualization:**
  - Input/Output signal plots
  - Gain vs F0 variation curves
  - Linearity analysis (XY plots)
  - Circuit diagram display

- **Audio Processing:**
  - Load and process WAV/MP3 files
  - Generate test signals
  - Real-time audio playback

## Project Structure

```
amplifier_simulator/
├── core/
│   └── audio_processor.py  # Audio processing and signal generation
├── gui/
│   └── main_window.py      # PyQt5 GUI and plotting
├── utils/
│   └── helpers.py          # Helper functions
├── assets/                  # Circuit diagrams
├── config.py               # Configuration
├── main.py                 # Entry point
├── requirements.txt
└── README.md
```

## Installation

```bash
pip install -r requirements.txt
python main.py
```

## Controls

- **Amplifier Configuration:** Select between 4 modes
- **F0 Slider:** Adjust power amplifier gain (8-12)
- **K Slider:** Adjust forward gain (1-200)
- **Beta Slider:** Adjust feedback factor (0.01-1.0)
- **Load Audio:** Import WAV or MP3 files
- **Play Output:** Listen to processed signal

## Dependencies

- PyQt5
- numpy
- matplotlib
- scipy
- sounddevice
- Pillow

## Technical Details

### Amplifier Modes

1. **Simple Amplifier:** Direct gain multiplication
2. **Feedback System:** Negative feedback with gain = (K x F0)/(1 + Beta x K x F0)
3. **Crossover Distortion:** Dead-zone distortion near zero crossing
4. **Compensated System:** Feedback with distortion compensation

---

*Educational project demonstrating amplifier feedback systems and audio signal processing.*
