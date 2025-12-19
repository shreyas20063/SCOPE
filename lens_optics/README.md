# Lens Imaging and Blurring Simulation

A comprehensive PyQt5-based simulation tool for exploring optical lens behavior, point spread functions (PSF), and image blurring effects.

## Features

- Interactive PyQt5 graphical user interface
- Real-time optical simulation with diffraction-limited PSF calculations
- Atmospheric seeing effects simulation
- Multiple test pattern generators (resolution charts, point sources, edge targets, star fields)
- Comprehensive image quality metrics (MSE, PSNR, SSIM)
- PSF analysis (FWHM, encircled energy, Strehl ratio)
- Ray tracing and lens diagram visualization
- Results export functionality

## Project Structure

```
Lens_convolution/
├── __init__.py                 # Package initialization
├── main.py                     # Application entry point
├── requirements.txt            # Python dependencies
├── assets/                     # Image and data assets
│   └── optical-resolution-chart.jpg
├── gui/                        # PyQt5 GUI components
│   ├── __init__.py
│   ├── main_window.py          # Main application window
│   ├── control_widgets.py     # Parameter and image controls
│   └── results_display.py     # Results visualization
├── optics/                     # Optical physics and lens modeling
│   ├── __init__.py
│   └── lens_model.py          # PSF generation and calculations
├── processing/                 # Image processing operations
│   ├── __init__.py
│   └── image_ops.py           # Image loading and convolution
└── visualization/              # Plotting and visualization
    ├── __init__.py
    └── plots.py               # Matplotlib-based plots
```

## Installation

1. Clone or download this repository
2. Install required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the application:

```bash
python main.py
```

### Controls

- **Lens Parameters**: Adjust diameter, focal length, and wavelength
- **Atmospheric Effects**: Enable seeing effects and adjust FWHM
- **Simulation Parameters**: Control PSF grid size, pixel size, and noise level
- **Image Source**: Choose test patterns or load custom images
- **Auto-update**: Automatically re-run simulation on parameter changes

### Tabs

1. **Images**: Original vs. blurred image comparison with quality metrics
2. **Point Spread Function**: 2D PSF, cross-sections, and encircled energy
3. **Analysis**: Comprehensive quality metrics and performance assessment
4. **Lens Diagram**: Ray tracing and lens parameter visualization

## Dependencies

- Python 3.7+
- NumPy: Numerical computations
- SciPy: Scientific functions (Bessel functions, convolution)
- PyQt5: GUI framework
- OpenCV (cv2): Image processing
- Pillow (PIL): Image loading
- Matplotlib: Plotting and visualization

## Physics Background

### Airy Disk PSF
The application simulates diffraction-limited imaging using the Airy disk pattern:
- Calculated from circular aperture diffraction
- First zero occurs at: r = 1.22 * λ * f / D
- Rayleigh criterion for resolution limit

### Atmospheric Seeing
Optional Gaussian PSF component representing atmospheric turbulence:
- Specified as FWHM in arcseconds
- Convolved with diffraction PSF for combined effect
- Simulates ground-based telescope observations

### Image Quality Metrics
- **MSE**: Mean Squared Error
- **PSNR**: Peak Signal-to-Noise Ratio
- **SSIM**: Structural Similarity Index
- **Contrast Reduction**: Loss of image contrast

### PSF Metrics
- **FWHM**: Full Width at Half Maximum
- **Encircled Energy**: Energy contained within radius
- **Strehl Ratio**: Peak intensity vs. perfect PSF

## License

Part of Signals and Systems Python Simulations collection.

## Version

1.0.0 - Initial structured release
