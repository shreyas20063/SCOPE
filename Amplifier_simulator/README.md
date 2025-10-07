# Amplifier Feedback Simulator

A comprehensive Python application for simulating and visualizing different amplifier configurations, including feedback systems and crossover distortion compensation.

## Academic Information

**Course:** Signals and Systems (EE204T)  
**Professor:** Ameer Mulla  
**Students:** Prathamesh Nerpagar, Duggimpudi Shreyas Reddy

## Project Overview

This simulation demonstrates the behavior of different amplifier configurations and helps understand key concepts in signals and systems:

- How negative feedback improves amplifier stability
- Reduction of distortion through feedback compensation
- Maintaining consistent gain despite component variations
- Real-time analysis of signal processing through different amplifier stages

The tool provides interactive visualization of input/output waveforms, gain stability analysis, and linearity characteristics with audio processing capabilities.

## Features

- **Four Amplifier Configurations:**
  - Simple Amplifier
  - Feedback System
  - Crossover Distortion
  - Compensated System

- **Real-time Visualization:**
  - Input/Output signal plots
  - Gain vs F₀ variation curves
  - Linearity analysis (XY plots)
  - Circuit diagram display

- **Audio Processing:**
  - Load and process WAV/MP3 files
  - Generate test signals
  - Real-time audio playback
  - Support for custom audio files

## Project Structure

```
Audio-amplifier-simulator/
├── core/                   # Audio processing module
│   ├── __init__.py
│   └── audio_processor.py # Audio processing and signal generation
├── ui/                     # GUI module
│   ├── __init__.py
│   └── gui.py             # GUI components and plotting
├── utils/                  # Helper utilities
│   ├── __init__.py
│   └── helpers.py         # Helper functions
├── compensated.png        # Circuit diagram for compensated system
├── crossover.png          # Circuit diagram for crossover distortion
├── feedback.png           # Circuit diagram for feedback system
├── simple.png             # Circuit diagram for simple amplifier
├── config.py              # Configuration and constants
├── main.py                # Entry point
├── requirements.txt       # Python dependencies
├── music.wav              # Sample audio file (optional)
└── README.md              # This file
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Audio-amplifier-simulator.git
cd Audio-amplifier-simulator
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Add circuit diagram images to the project directory:
   - `simple.png`
   - `feedback.png`
   - `crossover.png`
   - `compensated.png`

## Usage

Run the application:
```bash
python main.py
```

### Controls

- **Amplifier Configuration:** Select between 4 different amplifier modes
- **F₀ Slider:** Adjust power amplifier gain (8-12)
- **K Slider:** Adjust forward gain (1-200)
- **β Slider:** Adjust feedback factor (0.01-1.0)
- **Load Audio File:** Import WAV or MP3 files
- **Play Output:** Listen to the processed signal
- **Reset Parameters:** Return to default values

## Module Descriptions

### `config.py`
Contains all application constants, default values, and configuration parameters.

### `core/audio_processor.py`
Handles:
- Audio signal generation (sine waves)
- Audio file loading (WAV/MP3)
- Amplifier simulation algorithms
- Crossover distortion modeling

### `ui/gui.py`
Manages:
- User interface layout
- Interactive controls
- Real-time plotting with matplotlib
- Circuit diagram display

### `utils/helpers.py`
Provides:
- Image loading and resizing
- Audio playback threading
- Gain calculation utilities

## Dependencies

- `numpy` - Numerical computations
- `matplotlib` - Plotting and visualization
- `scipy` - Audio file I/O
- `customtkinter` - Modern UI framework
- `sounddevice` - Audio playback
- `Pillow` - Image processing
- `pydub` (optional) - MP3 support

## Technical Details

### Amplifier Modes

1. **Simple Amplifier:** Direct gain multiplication
2. **Feedback System:** Implements negative feedback with gain = (K×F₀)/(1+β×K×F₀)
3. **Crossover Distortion:** Models dead-zone distortion near zero crossing
4. **Compensated System:** Combines feedback with distortion compensation

### Signal Processing

The application processes audio through the selected amplifier configuration and displays:
- Time-domain input/output waveforms
- Frequency-dependent gain characteristics
- Linearity analysis showing deviation from ideal response

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Author

**Course:** Signals and Systems (EE204T)  
**Professor:** Ameer Mulla  
**Students:** Prathamesh Nerpagar, Duggimpudi Shreyas Reddy

Created for educational purposes to demonstrate amplifier feedback systems and audio signal processing.
