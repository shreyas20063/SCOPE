# 🎵 Aliasing and Quantization Simulator

A comprehensive interactive application for visualizing and understanding aliasing and quantization effects on both audio signals and images.

## 📚 Course Information

**Course:** Signals and Systems (EE204T)  
**Instructor:** Prof. Ameer Mulla  
**Students:** Prathamesh Nerpagar, Shreyas Duggimpudi

## 🌟 Features

### 📊 Audio Aliasing Demo
- Interactive downsampling with adjustable factors (1x to 20x)
- Real-time frequency spectrum analysis
- Anti-aliasing filter toggle
- Audio playback of original and downsampled signals
- Visual representation of Nyquist theorem

### 🎚️ Audio Quantization Demo
- Three quantization techniques:
  - Standard uniform quantization
  - Dithered quantization
  - Robert's subtractive dither method
- Adjustable bit depth (1-16 bits)
- SNR (Signal-to-Noise Ratio) calculation
- Quantization error spectrum visualization
- Interactive quantization function plots
- Audio playback comparison

### 🖼️ Image Quantization Demo
- Three quantization methods applied to images
- Adjustable bit depth (1-8 bits)
- Side-by-side comparison of techniques
- Histogram analysis for each method
- MSE (Mean Squared Error) comparison chart
- Support for grayscale images

## 📋 Requirements

- Python 3.8 or higher
- NumPy
- Matplotlib
- SciPy
- sounddevice
- Pillow
- customtkinter

## 🚀 Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/aliasing-quantization-simulator.git
cd aliasing-quantization-simulator
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python main.py
```

**Note:** Sample files (`audio_sample.wav` and `test_image.jpg`) are included in the repository.

## 💻 Usage

Run the main application:
```bash
python main.py
```

The main window will display three demo options. Click on any "Launch Demo" button to open the corresponding demonstration window.

## 📁 Project Structure

```
aliasing-quantization-simulator/
├── main.py                  # Entry point
├── config.py                # Configuration and colors
├── utils.py                 # Utility functions
├── main_window.py           # Main application window
├── aliasing_demo.py         # Aliasing demonstration
├── quantization_demo.py     # Audio quantization demo
├── image_demo.py            # Image quantization demo
├── requirements.txt         # Python dependencies
├── .gitignore              # Git ignore patterns
├── README.md               # This file
├── audio_sample.wav        # Sample audio file
└── test_image.jpg          # Sample image file
```

## 🎓 Educational Value

This application is designed for:
- **Students** learning digital signal processing
- **Engineers** visualizing sampling and quantization effects
- **Educators** demonstrating key DSP concepts
- **Researchers** prototyping signal processing techniques

## 🔧 Technical Details

### Aliasing Demo
- Implements downsampling with optional low-pass anti-aliasing filter
- Uses Butterworth filter design (8th order)
- Welch's method for power spectral density estimation
- Real-time audio playback using sounddevice

### Quantization Demos
- **Standard**: Mid-rise/mid-tread uniform quantization
- **Dither**: Additive uniform dither for noise shaping
- **Robert's Method**: Subtractive dither for improved SNR

### UI Framework
- Built with CustomTkinter for modern aesthetics
- Matplotlib integration for scientific plotting
- Responsive layout with grid-based card design

## 🎨 Color Scheme

The application uses a carefully designed color palette:
- Background: Light gray (#F9FAFB)
- Accent: Vibrant blue (#2563EB)
- Success: Bright green (#22C55E)
- Warning: Amber (#F59E0B)
- Danger: Red (#EF4444)


## 🙏 Acknowledgments

- Prof. Ameer Mulla for guidance and instruction in Signals and Systems (EE204T)
- Scipy and NumPy communities for signal processing tools
- CustomTkinter for the modern UI framework
- Matplotlib for visualization capabilities

---

**Developed as part of EE204T - Signals and Systems Course**

*Educational project demonstrating signal processing concepts including aliasing and quantization.*