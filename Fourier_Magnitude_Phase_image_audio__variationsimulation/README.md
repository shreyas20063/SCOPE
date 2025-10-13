# Fourier Transform Analysis Application

An interactive PyQt5 application for exploring the importance of magnitude vs phase in signals and images.

## Academic Context

Developed as part of the **Signals and Systems (EE204T)** course under **Prof. Ameer Mulla**  
Authors: **Duggimpudi Shreyas Reddy** and **Prathamesh Nerpagar**

## Overview

This application demonstrates a fundamental principle in image processing: **phase information is more important than magnitude for preserving image structure**. Through interactive visualizations and hybrid image generation, users can explore how the Fourier transform decomposes images into frequency components.

## Features

- **Interactive Fourier Analysis**: Real-time computation of magnitude and phase spectra
- **Magnitude/Phase Manipulation**: Apply uniform magnitude or phase values to see their effects
- **Hybrid Images**: Swap magnitude and phase between two images to demonstrate phase importance
- **Dual Modalities**: Instantly toggle between image and audio signal exploration with the same controls
- **Integrated Audio Playback**: Hear originals, reconstructions, and hybrids without leaving the app
- **Multiple Visualization Tabs**:
  - Image 1 Analysis (magnitude, phase, reconstruction)
  - Image 2 Analysis (magnitude, phase, reconstruction)
  - Hybrid Comparison (demonstrates phase dominance)
- **Custom Images**: Load your own images or use built-in test patterns
- **Export Functionality**: Save results and plots for further analysis

## Installation

### Requirements

- Python 3.7 or higher
- PyQt5
- NumPy
- SciPy
- Matplotlib
- Pillow

### Install Dependencies

```bash
pip install PyQt5 numpy scipy matplotlib pillow
```

## Usage

### Running the Application

```bash
cd FourierApp
python main.py
```

### Basic Workflow

1. **Select Images**: Use the built-in test patterns (Building, Face, Geometric, Texture) or load your own images
2. **Choose Analysis Mode**:
   - **Original**: Shows standard Fourier transform
   - **Uniform Magnitude**: Replaces magnitude with constant value (proves phase importance!)
   - **Uniform Phase**: Replaces phase with constant value (structure is lost)
3. **Adjust Parameters**: Use sliders to control uniform magnitude/phase values
4. **Explore Tabs**: View different analysis results across multiple tabs
5. **Export**: Save results and plots for presentations or reports

### Key Experiments

#### Experiment 1: Phase Preserves Structure
1. Set Image 1 mode to "Uniform Magnitude"
2. Adjust the uniform magnitude slider
3. Notice: The reconstructed image still looks similar to the original!
4. **Conclusion**: Phase alone carries structural information

#### Experiment 2: Magnitude Alone Loses Structure
1. Set Image 1 mode to "Uniform Phase"
2. Notice: The reconstructed image loses all recognizable structure
3. **Conclusion**: Magnitude alone cannot preserve image structure

#### Experiment 3: Hybrid Images
1. Go to "Hybrid Comparison" tab
2. Observe:
   - Mag1 + Phase2 looks like Image 2
   - Mag2 + Phase1 looks like Image 1
3. **Conclusion**: Phase determines what you see!

## Application Structure

```
FourierApp/
├── main.py                 # Application entry point
├── fourier/               # Core Fourier analysis
│   ├── __init__.py
│   └── fourier_model.py   # Fourier transform computations
├── processing/            # Image processing
│   ├── __init__.py
│   └── image_ops.py       # Image loading and generation
├── visualization/         # Plotting and visualization
│   ├── __init__.py
│   └── plots.py          # All plotting functions
└── gui/                  # Graphical user interface
    ├── __init__.py
    ├── main_window.py    # Main application window
    ├── control_widgets.py # Control panel widgets
    └── results_display.py # Results visualization
```

## Theory

### 2D Fourier Transform

The 2D Fourier Transform decomposes an image into frequency components:

```
F(u,v) = ∫∫ f(x,y) e^(-i2π(ux+vy)) dx dy
```

Where:
- `F(u,v)` is the Fourier transform (complex-valued)
- `|F(u,v)|` is the magnitude spectrum
- `arg(F(u,v))` is the phase spectrum

### Key Insight

**Phase is more important than magnitude for image structure!**

This counterintuitive result is demonstrated through:
1. Uniform magnitude experiments
2. Uniform phase experiments
3. Hybrid image generation

### Applications

- Image compression (phase-preserving algorithms)
- Image enhancement and filtering
- Pattern recognition
- Computer vision
- Medical imaging
- Astronomy

## Technical Details

### Architecture

- **Modular Design**: Separate modules for Fourier analysis, processing, visualization, and GUI
- **Background Processing**: Uses QThread for non-blocking analysis
- **Responsive UI**: Auto-update with debouncing for smooth parameter changes
- **Professional GUI**: PyQt5-based interface with tabs and controls

### Performance

- Optimized FFT using SciPy
- Efficient numpy operations
- Background worker threads keep UI responsive
- Typical analysis time: < 1 second for 256x256 images

## Examples

### Built-in Test Patterns

1. **Building**: Geometric structure with edges and textures
2. **Face**: Synthetic face with circular features
3. **Geometric**: Patterns with lines, circles, and shapes
4. **Texture**: Complex sinusoidal and random textures

## Tips

- Enable "Auto-update on parameter change" for real-time exploration
- Try different test patterns to see varying effects
- Export plots for presentations or reports
- Review the Theory section below for background

## Troubleshooting

### Application won't start
- Ensure all dependencies are installed: `pip install PyQt5 numpy scipy matplotlib pillow`
- Check Python version: Python 3.7+ required

### Images not loading
- Ensure Pillow is installed: `pip install pillow`
- Supported formats: PNG, JPG, BMP, TIFF

### Slow performance
- Try smaller images (256x256 recommended)
- Disable auto-update for complex operations
- Close other resource-intensive applications

## Credits

Inspired by classical image processing research demonstrating the importance of phase in perception and reconstruction.

## License

MIT License - Feel free to use and modify for educational and research purposes.
