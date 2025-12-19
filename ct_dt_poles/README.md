# CT & DT Poles Conversion - Interactive Learning Tool

An educational tool for understanding continuous-time to discrete-time system transformations using different numerical integration methods.

## Overview

This application helps students and instructors visualize and understand how continuous-time (CT) system poles transform to discrete-time (DT) poles through various numerical integration methods:
- Forward Euler
- Backward Euler
- Trapezoidal Rule

## Features

- **Interactive Visualization**: Real-time s-plane to z-plane pole mapping
- **Stability Analysis**: Visual feedback on system stability
- **Step Response Comparison**: Compare continuous vs discrete approximations
- **Educational Content**: Built-in explanations and learning resources
- **Guided Mode**: Step-by-step exploration scenarios
- **Assessment Tools**: Built-in quiz to test understanding
- **Professional PyQt5 Interface**: Modern, responsive GUI

## Project Structure

```
CT&DT_Poles_Conversion/
├── main.py                 # Application entry point
├── gui/                    # PyQt5 GUI components
│   ├── __init__.py
│   ├── main_window.py     # Main application window
│   └── plot_renderer.py   # Matplotlib plotting with Qt integration
├── core/                   # Core functionality
│   ├── __init__.py
│   ├── config.py          # Configuration and constants
│   └── math_handler.py    # Mathematical computations
├── utils/                  # Utility modules
│   ├── __init__.py
│   ├── educational_content.py  # Educational content and feedback
│   └── problem_generator.py    # Assessment and practice problems
├── assets/                 # Assets folder (for future use)
│   └── __init__.py
└── source_code/            # Original implementation (preserved)
    └── ...
```

## Installation

### Requirements

- Python 3.7+
- PyQt5
- NumPy
- Matplotlib

### Install Dependencies

```bash
pip install PyQt5 numpy matplotlib
```

## Usage

### Running the Application

```bash
python main.py
```

Or make it executable:

```bash
chmod +x main.py
./main.py
```

### Using the Interface

1. **Step Size Ratio Slider**: Adjust the T/τ ratio to see how it affects stability
2. **Method Selection**: Choose between Forward Euler, Backward Euler, or Trapezoidal
3. **Reset Button**: Reset to default parameters (Ctrl+R)
4. **Run Demo**: Automated demonstration of stability transitions (Ctrl+D)
   - Click again to stop the demo
5. **Guided Mode**: Follow predefined scenarios for learning (Ctrl+G)
   - Use "Next Scenario" button, Space, or Right Arrow to advance
   - Use Left Arrow to go back to previous scenario
6. **Assessment Quiz**: Test your understanding with interactive quiz

### Keyboard Shortcuts

- **Ctrl+R**: Reset to defaults
- **Ctrl+D**: Run/Stop demo animation
- **Ctrl+G**: Start guided mode
- **Space** or **Right Arrow**: Next scenario (in guided mode)
- **Left Arrow**: Previous scenario (in guided mode)

## Key Concepts

### S-Plane (Continuous Time)
- Left half-plane = stable region
- System pole at s = -1/τ

### Z-Plane (Discrete Time)
- Inside unit circle = stable region
- Pole location depends on method and step size T

### Stability Criteria

- **Forward Euler**: Stable when T/τ < 2
- **Backward Euler**: Always stable (for stable CT systems)
- **Trapezoidal**: Maps imaginary axis to unit circle exactly

## Educational Usage

### For Students
1. Start with small T/τ ratios (< 0.5) to see stable behavior
2. Gradually increase T/τ to observe stability transitions
3. Compare different methods at the same T/τ ratio
4. Use guided mode for structured learning
5. Take the assessment quiz to test understanding

### For Instructors
- Use guided mode to demonstrate key concepts
- Show critical points (e.g., T/τ = 2 for Forward Euler)
- Compare accuracy and stability trade-offs
- Generate practice problems for homework

## Changes from Original

### Major Updates
1. **Framework Migration**: Converted from Matplotlib widgets to PyQt5
2. **Project Structure**: Reorganized into modular structure (gui/, core/, utils/)
3. **Enhanced UI**: Modern PyQt5 interface with better controls
4. **Maintained Functionality**: All original features preserved and enhanced

### Benefits
- More responsive and professional interface
- Better separation of concerns
- Easier to maintain and extend
- Cross-platform compatibility
- Modern look and feel

## Technical Details

### Numerical Methods

**Forward Euler**: z = 1 + sT
- Simple but can become unstable
- Stability limit: T/τ < 2

**Backward Euler**: z = 1/(1 - sT)
- Inherently stable
- More conservative (damped)

**Trapezoidal (Tustin)**: z = (1 + sT/2)/(1 - sT/2)
- Best accuracy-stability balance
- Industry standard

## Contributing

This is an educational tool. Contributions for improvements are welcome:
- Enhanced visualizations
- Additional numerical methods
- More educational content
- Bug fixes

## License

Educational use only. Part of Signals and Systems course materials.

## Support

For questions or issues, please contact the course instructor or teaching assistants.

## Acknowledgments

Developed for 6.003 Signals and Systems course.
Based on fundamental concepts of discrete-time system approximation.
