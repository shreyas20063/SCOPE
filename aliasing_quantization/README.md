# Aliasing and Quantization Simulator

Interactive application for visualizing aliasing and quantization effects on audio signals and images.

## Course Information

**Course:** Signals and Systems (EE204T)
**Instructor:** Prof. Ameer Mulla
**Authors:** Duggimpudi Shreyas Reddy, Prathamesh Nerpagar

---

## Also Available as Web Application

This simulation is also available in the **web platform** version with additional features:
- Browser-based interface (no installation required)
- Real-time parameter updates
- Mobile-responsive design

See [signals-web-platform](../signals-web-platform/) for the web version.

---

## Features

### Audio Aliasing Demo
- Interactive downsampling (1x to 20x)
- Real-time frequency spectrum analysis
- Anti-aliasing filter toggle
- Audio playback comparison
- Nyquist theorem visualization

### Audio Quantization Demo
- Three quantization techniques:
  - Standard uniform quantization
  - Dithered quantization
  - Robert's subtractive dither
- Adjustable bit depth (1-16 bits)
- SNR calculation
- Error spectrum visualization

### Image Quantization Demo
- Three quantization methods
- Adjustable bit depth (1-8 bits)
- Side-by-side comparison
- Histogram analysis
- MSE comparison chart

## Requirements

- Python 3.8+
- PyQt5
- NumPy
- Matplotlib
- SciPy
- sounddevice
- Pillow

## Installation

```bash
pip install -r requirements.txt
python main.py
```

Sample files (`audio_sample.wav` and `test_image.jpg`) are included in the `assets/` folder.

## Project Structure

```
aliasing_quantization/
├── gui/
│   ├── main_window.py       # Main launcher window
│   ├── aliasing_demo.py     # Aliasing demonstration
│   ├── quantization_demo.py # Audio quantization demo
│   └── image_demo.py        # Image quantization demo
├── utils/
│   ├── config.py            # Colors and configuration
│   └── utils.py             # Utility functions
├── assets/
│   ├── audio_sample.wav     # Sample audio
│   └── test_image.jpg       # Sample image
├── main.py                  # Entry point
├── requirements.txt
└── README.md
```

## Technical Details

### Aliasing Demo
- Butterworth filter design (8th order)
- Welch's method for power spectral density
- Real-time audio playback

### Quantization Methods
- **Standard**: Mid-rise/mid-tread uniform quantization
- **Dither**: Additive uniform dither for noise shaping
- **Robert's Method**: Subtractive dither for improved SNR

## Acknowledgments

- Prof. Ameer Mulla for course guidance
- SciPy and NumPy communities

---

*Educational project demonstrating aliasing and quantization concepts.*
