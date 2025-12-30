# Modulation Techniques Simulator

Interactive PyQt5 application for visualizing amplitude modulation (AM), frequency modulation (FM), phase modulation (PM), and frequency division multiplexing (FDM). Built for engineering education with real-time parameter control and audio playback.

**Course:** Signals and Systems (EE204T)
**Instructor:** Prof. Ameer Mulla
**Authors:** Duggimpudi Shreyas Reddy, Prathamesh Nerpagar

---

## Also Available as Web Application

This simulation is also available in the **web platform** version with additional features:
- Browser-based interface (no installation required)
- Real-time WebSocket updates
- Mobile-responsive design

See [signals-web-platform](../signals-web-platform/) for the web version.

---

## Features

### Amplitude Modulation (AM)
- DSB-SC (Double Sideband Suppressed Carrier)
- AM with carrier
- Envelope detection visualization
- Recovered audio playback

### Frequency & Phase Modulation (FM/PM)
- Instantaneous frequency visualization
- Carson bandwidth calculation
- Modulation index control
- Signal recovery demonstration

### Frequency Division Multiplexing (FDM)
- Configurable channel count
- Adjustable channel spacing
- Individual channel demodulation
- Spectrum visualization

### User Interface
- Professional PyQt5 interface with card-based navigation
- Real-time parameter sliders
- Live spectrum and waveform plots
- Audio playback support

---

## Requirements

- Python 3.8+
- PyQt5
- NumPy
- Matplotlib
- SciPy
- sounddevice (for audio playback)

---

## Installation

```bash
pip install PyQt5 numpy matplotlib scipy sounddevice
```

---

## Running the Simulator

```bash
python main.py
```

---

## Usage

1. **Launch the application** - The main window displays three demo cards
2. **Select a demo** - Click on AM, FM/PM, or FDM card to open that module
3. **Adjust parameters** - Use sliders to modify carrier frequency, modulation index, etc.
4. **Observe results** - Watch real-time updates in time and frequency domain plots
5. **Play audio** - Use audio controls to hear modulated/demodulated signals

---

## Project Structure

```
modulation_techniques/
├── main.py                 # Entry point
├── gui/
│   ├── __init__.py
│   ├── mainwindow.py       # Main launcher window
│   ├── components.py       # Reusable UI components
│   ├── styles.py           # Color scheme and styling
│   └── demos/
│       ├── __init__.py
│       ├── base.py         # Base demo window class
│       ├── am.py           # Amplitude modulation demo
│       ├── fm.py           # Frequency/phase modulation demo
│       └── fdm.py          # Frequency division multiplexing demo
├── core/
│   └── __init__.py
├── utils/
│   ├── __init__.py
│   └── audio_utils.py      # Audio playback utilities
└── assets/
    └── __init__.py
```

---

## Theory

### Amplitude Modulation
AM encodes information in the amplitude of a carrier signal:
$$s(t) = [1 + m \cdot x(t)] \cdot \cos(2\pi f_c t)$$

where $m$ is the modulation index and $f_c$ is the carrier frequency.

### Frequency Modulation
FM encodes information in the instantaneous frequency:
$$s(t) = A_c \cos\left(2\pi f_c t + 2\pi k_f \int x(\tau) d\tau\right)$$

Carson's bandwidth rule: $B = 2(\Delta f + f_m)$

### Frequency Division Multiplexing
FDM allows multiple signals to share a single channel by assigning each signal a different carrier frequency.

---

## Suggested Experiments

1. **AM Overmodulation**: Increase modulation index > 1 to observe envelope distortion
2. **FM Bandwidth**: Vary modulation index to see Carson bandwidth in action
3. **FDM Channel Spacing**: Reduce channel spacing to observe inter-channel interference
4. **Demodulation Quality**: Compare original and recovered signals

---

*Educational simulation for modulation concepts in Signals and Systems.*
