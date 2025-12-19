# Fourier Series Visualization

Interactive Fourier series exploration tool created for the Signals and Systems course (EE204T) under Prof. Ameer Mulla by Duggimpudi Shreyas Reddy and Prathamesh Nerpagar.

## Project Structure

- `core/` — waveform definitions and Fourier series helpers
- `gui/` — PyQt5-based UI with embedded matplotlib canvas for the visualization
- `utils/` — utility functions and color schemes
- `assets/` — directory for assets (images, data files, etc.)
- `main.py` — entry point used to launch the app

## Features

- Professional PyQt5 interface with embedded matplotlib plotting
- Interactive slider to adjust number of harmonics (1-50)
- Toggle between Square Wave and Triangle Wave visualization
- Real-time Fourier series approximation
- Individual harmonic visualization with color-coded components
- Error metrics (MSE and Max Absolute Error)
- Mathematical formulas and convergence properties display

## Requirements

```bash
pip install numpy matplotlib PyQt5
```

## Getting Started

```bash
python3 main.py
```

Move the slider to select the number of harmonics and switch between square and triangle waves to compare their Fourier series behaviour.

## Technical Details

The application uses:
- **PyQt5** for the main window and controls
- **Matplotlib** embedded in PyQt5 canvas for high-quality plots
- **NumPy** for fast numerical computations
- Custom color scheme for modern, professional appearance
