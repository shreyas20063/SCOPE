# Fourier Transform Analysis Application

An interactive PyQt5 application for exploring the importance of magnitude vs phase in signals and images.

## Academic Context

Developed as part of the **Signals and Systems (EE204T)** course under **Prof. Ameer Mulla**  
Authors: **Duggimpudi Shreyas Reddy** and **Prathamesh Nerpagar**

## Overview

This application demonstrates a fundamental principle in signal processing: **phase information is more important than magnitude for preserving signal structure**. Through interactive visualizations and hybrid generation, users can explore how the Fourier transform decomposes both images and audio signals into frequency components. The application supports dual modalities—seamlessly switch between image and audio analysis to observe the same phase-dominance principle across different signal types.

## Features

- **Dual Modalities**: Seamlessly toggle between image and audio signal exploration with the same controls
- **Interactive Fourier Analysis**: Real-time computation of magnitude and phase spectra for both images and audio
- **Magnitude/Phase Manipulation**: Apply uniform magnitude or phase values to see their effects on both signal types
- **Hybrid Generation**: Swap magnitude and phase between two signals (images or audio) to demonstrate phase importance
- **Integrated Audio Playback**: Hear original signals, reconstructions, and hybrids directly within the application
- **Multiple Visualization Tabs**:
  - Signal 1 analysis (magnitude, phase, reconstruction)
  - Signal 2 analysis (magnitude, phase, reconstruction)
  - Hybrid comparison (demonstrates phase dominance)
- **Custom Inputs**: Load your own images or audio files, or use built-in test patterns and waveforms
- **Export Functionality**: Save results and plots for further analysis

## Installation

### Requirements

- Python 3.7 or higher
- PyQt5
- NumPy
- SciPy
- Matplotlib
- Pillow (for image processing)
- sounddevice (for audio playback)
- soundfile (for audio file I/O)

### Install Dependencies

```bash
pip install PyQt5 numpy scipy matplotlib pillow sounddevice soundfile
```

## Usage

### Running the Application

```bash
cd FourierApp
python main.py
```

### Basic Workflow

1. **Select Mode**: Choose between Image or Audio mode
2. **Select Signals**: 
   - **Images**: Use built-in test patterns (Building, Face, Geometric, Texture) or load your own images
   - **Audio**: Use built-in test waveforms (Sine, Square, Sawtooth, Chirp) or load your own audio files
3. **Choose Analysis Mode**:
   - **Original**: Shows standard Fourier transform
   - **Uniform Magnitude**: Replaces magnitude with constant value (proves phase importance)
   - **Uniform Phase**: Replaces phase with constant value (structure is lost)
4. **Adjust Parameters**: Use sliders to control uniform magnitude/phase values
5. **Explore Tabs**: View different analysis results across multiple tabs
6. **For Audio**: Play original, reconstructed, and hybrid audio using integrated playback controls
7. **Export**: Save results and plots for presentations or reports

### Key Experiments

#### Experiment 1: Phase Preserves Structure (Images)

1. Select Image mode
2. Set Signal 1 mode to "Uniform Magnitude"
3. Adjust the uniform magnitude slider
4. Notice: The reconstructed image still looks similar to the original
5. **Conclusion**: Phase alone carries structural information

#### Experiment 2: Phase Preserves Timbre (Audio)

1. Select Audio mode
2. Set Signal 1 mode to "Uniform Magnitude"
3. Adjust the uniform magnitude slider
4. Play the reconstructed audio
5. Notice: The audio sounds remarkably similar to the original
6. **Conclusion**: Phase alone preserves the perceived characteristics of sound

#### Experiment 3: Magnitude Alone Loses Structure (Images)

1. Select Image mode
2. Set Signal 1 mode to "Uniform Phase"
3. Notice: The reconstructed image loses all recognizable structure
4. **Conclusion**: Magnitude alone cannot preserve image structure

#### Experiment 4: Magnitude Alone Loses Timbre (Audio)

1. Select Audio mode
2. Set Signal 1 mode to "Uniform Phase"
3. Play the reconstructed audio
4. Notice: The audio sounds completely different (often like noise)
5. **Conclusion**: Magnitude alone cannot preserve audio characteristics

#### Experiment 5: Hybrid Signals

1. Go to "Hybrid Comparison" tab
2. For Images:
   - Mag1 + Phase2 looks like Image 2
   - Mag2 + Phase1 looks like Image 1
3. For Audio:
   - Mag1 + Phase2 sounds like Audio 2
   - Mag2 + Phase1 sounds like Audio 1
4. **Conclusion**: Phase determines what you perceive, regardless of signal type

## Application Structure

```
FourierApp/
├── main.py                      # Application entry point
├── core/                        # Core functionality
│   ├── __init__.py
│   ├── fourier/                # Fourier analysis
│   │   ├── __init__.py
│   │   ├── fourier_model.py    # 2D Fourier transforms (images)
│   │   └── audio_fourier_model.py  # 1D Fourier transforms (audio)
│   └── processing/             # Signal processing
│       ├── __init__.py
│       ├── image_ops.py        # Image loading and generation
│       └── audio_ops.py        # Audio loading and generation
├── utils/                      # Utilities
│   ├── __init__.py
│   └── plots.py               # Plotting and visualization
├── gui/                       # Graphical user interface
│   ├── __init__.py
│   ├── main_window.py         # Main application window
│   ├── control_widgets.py     # Control panel widgets
│   ├── results_display.py     # Image results visualization
│   └── audio_results_display.py  # Audio results visualization
└── assets/                    # Static assets
    └── __init__.py            # Images and audio files (optional)
```

## Theory

### 1D Fourier Transform (Audio Signals)

The 1D Fourier Transform decomposes an audio signal into frequency components:

```
F(ω) = ∫ f(t) e^(-iωt) dt
```

Where:
- `F(ω)` is the Fourier transform (complex-valued)
- `|F(ω)|` is the magnitude spectrum (amplitude of each frequency)
- `arg(F(ω))` is the phase spectrum (timing/alignment of frequencies)

### 2D Fourier Transform (Images)

The 2D Fourier Transform decomposes an image into frequency components:

```
F(u,v) = ∫∫ f(x,y) e^(-i2π(ux+vy)) dx dy
```

Where:
- `F(u,v)` is the Fourier transform (complex-valued)
- `|F(u,v)|` is the magnitude spectrum (amplitude of spatial frequencies)
- `arg(F(u,v))` is the phase spectrum (spatial alignment of frequencies)

### Key Insight

**Phase is more important than magnitude for signal structure—in both images and audio.**

This counterintuitive result is demonstrated through:
1. Uniform magnitude experiments (phase-only reconstruction)
2. Uniform phase experiments (magnitude-only reconstruction)
3. Hybrid signal generation (magnitude-phase swapping)

### Why Phase Matters

- **Images**: Phase encodes edge locations, shapes, and spatial relationships
- **Audio**: Phase encodes temporal structure, transients, and waveform shape
- **Perception**: Human perception is highly sensitive to phase discontinuities
- **Reconstruction**: Phase alone can often reconstruct a recognizable signal; magnitude alone cannot

### Applications

**Image Processing:**
- Image compression (phase-preserving algorithms)
- Image enhancement and filtering
- Pattern recognition
- Computer vision
- Medical imaging
- Astronomy

**Audio Processing:**
- Audio codec design
- Speech recognition
- Music information retrieval
- Sound synthesis
- Audio watermarking
- Noise reduction

## Technical Details

### Architecture

- **Modular Design**: Separate modules for Fourier analysis, processing, visualization, and GUI
- **Background Processing**: Uses QThread for non-blocking analysis
- **Responsive UI**: Auto-update with debouncing for smooth parameter changes
- **Professional GUI**: PyQt5-based interface with tabs and controls

### Performance

- Optimized FFT using SciPy
- Efficient NumPy operations
- Background worker threads keep UI responsive
- Typical analysis time: <1 second for 256×256 images

## Examples

### Built-in Test Patterns (Images)

1. **Building**: Geometric structure with edges and textures
2. **Face**: Synthetic face with circular features
3. **Geometric**: Patterns with lines, circles, and shapes
4. **Texture**: Complex sinusoidal and random textures

### Built-in Test Waveforms (Audio)

1. **Sine Wave**: Pure tone with simple harmonic structure
2. **Square Wave**: Rich harmonic content with sharp transitions
3. **Sawtooth Wave**: Linear ramp with distinctive timbre
4. **Chirp**: Frequency sweep demonstrating time-frequency relationships

## Tips

- Enable "Auto-update on parameter change" for real-time exploration
- Try different test patterns/waveforms to see varying effects
- For audio: Use headphones for better perception of subtle phase effects
- For images: Start with high-contrast patterns to observe phase importance clearly
- Compare hybrid results across both modalities to see the universal principle
- Export plots for presentations or reports
- Experiment with different signal sizes for performance optimization

## Troubleshooting

### Application Won't Start

- Ensure all dependencies are installed: `pip install PyQt5 numpy scipy matplotlib pillow sounddevice soundfile`
- Check Python version: Python 3.7+ required

### Images Not Loading

- Ensure Pillow is installed: `pip install pillow`
- Supported formats: PNG, JPG, BMP, TIFF

### Audio Not Playing

- Ensure sounddevice is installed: `pip install sounddevice soundfile`
- Check system audio output settings
- Verify audio device permissions (macOS/Linux)
- Supported formats: WAV, MP3, FLAC, OGG

### Audio Files Not Loading

- Ensure soundfile is installed: `pip install soundfile`
- Try converting audio to WAV format if issues persist
- Check that sample rate is reasonable (8kHz - 48kHz recommended)

### Slow Performance

- Try smaller signals (256×256 for images, <5 seconds for audio)
- Disable auto-update for complex operations
- Close other resource-intensive applications
- For audio: Reduce sample rate or use shorter clips

## Credits

Inspired by classical signal processing research demonstrating the importance of phase in perception and reconstruction across both visual and auditory modalities.

## License

Feel free to use and modify for educational and research purposes.
