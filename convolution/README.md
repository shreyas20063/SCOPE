# Convolution Simulator

An interactive Python application for visualizing convolution operations for both continuous and discrete-time signals.Built for engineering education and signal processing understanding.


## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Demo Mode](#demo-mode)
- [Custom Mode](#custom-mode)
- [Signal Syntax Guide](#signal-syntax-guide)
- [Continuous vs Discrete Simulation](#continuous-vs-discrete-simulation)
- [Visualization Modes](#visualization-modes)
- [Export Options](#export-options)
- [Known Issues and Fixes](#known-issues-and-fixes)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [References](#references)

## Introduction

The Convolution Simulator is a comprehensive educational tool designed to help students and engineers understand convolution operations through interactive visualization. The application supports both continuous-time and discrete-time signals, offering mathematical and block-step visualization modes to illustrate the convolution process step by step.

Convolution is a fundamental operation in signal processing, defined mathematically as:

**Continuous-time:** $y(t) = \int_{-\infty}^{\infty} x(\tau)h(t-\tau)d\tau$

**Discrete-time:** $y[n] = \sum_{k=-\infty}^{\infty} x[k]h[n-k]$

## Features

### Core Functionality
- **Interactive Convolution Visualization**: Real-time animation showing the convolution process
- **Dual Signal Types**: Support for both continuous and discrete-time signals
- **Mathematical and Block-Step Views**: Two visualization modes for different learning approaches
- **Custom Signal Input**: Define your own signals using mathematical expressions
- **Demo Mode**: Pre-built signal combinations for quick exploration
- **Real-time Parameter Control**: Adjustable time/index position, playback speed, and sampling rate

### User Interface
- **Modern GUI**: Built with PyQt5 for cross-platform compatibility and professional appearance
- **Dark/Light Themes**: Toggle between visual themes for comfortable viewing
- **Responsive Controls**: Keyboard shortcuts and mouse interactions
- **Professional Layout**: Clean, organized interface suitable for educational presentations

### Export Capabilities
- **PNG Snapshots**: Save high-resolution images of current plots
- **CSV Data Export**: Export convolution results for further analysis
- **GIF Animations**: Create animated visualizations for presentations

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Step 1: Install Dependencies

Install all required packages using pip:

```bash
pip install -r requirements.txt
```

Or install packages individually:

```bash
pip install numpy>=1.21.0
pip install matplotlib>=3.5.0
pip install sympy>=1.9.0
pip install PyQt5>=5.15.0
pip install imageio>=2.19.0
```

### Step 2: Run the Application

Navigate to the project directory and run:

```bash
python main.py
```

## Usage

### Method 1: Windows Executable (Recommended for End Users)
Simply double-click `dist/convolution_simulator.exe` to launch the application. No Python installation or setup required.

### Method 2: Python Script (Recommended for Developers)
```bash
python main.py
```

### Building Your Own Executable
To create a Windows executable from source:

```bash
# Install PyInstaller
pip install pyinstaller

# Run the build script
python build_executable.py
```

The executable will be created in the `dist/` directory.

### Basic Operation
1. **Select Signal Type**: Choose between Continuous or Discrete signals
2. **Choose Mode**: Select Demo Mode for pre-built examples or Custom Mode for your own signals
3. **Configure Parameters**: Adjust time/index position, playback speed, and sampling rate
4. **Compute Convolution**: Click "Compute Convolution" to calculate results
5. **Animate**: Use Play/Pause controls or keyboard shortcuts to animate the process

### Keyboard Shortcuts
- `Space`: Play/Pause animation
- `Right Arrow`: Step forward
- `Left Arrow`: Step backward

### Mouse Controls
- **Time Slider**: Drag to manually control time/index position
- **Speed Slider**: Adjust animation playback speed
- **Sampling Rate**: Control numerical precision for continuous signals

## Demo Mode

Demo Mode provides carefully selected signal combinations that demonstrate key convolution concepts:

### Continuous-Time Demos
1. **Rect Pulse + Tri Pulse**: Rectangular pulse convolved with triangular pulse
   - x(t): `rect(t)` 
   - h(t): `tri(t)`
   - Demonstrates basic pulse shaping

2. **Unit Step + Exponential Decay**: Unit step response of first-order system
   - x(t): `u(t)`
   - h(t): `exp(-t) * u(t)`
   - Shows system response characteristics

### Discrete-Time Demos
1. **x=[1,2,1], h=[1,1]**: Simple finite sequences
   - x[n]: `[1, 2, 1]`
   - h[n]: `[1, 1]`
   - Basic discrete convolution example

2. **Decaying Exp + Differentiator**: Exponential decay through differentiator
   - x[n]: `0.9**n * u(n)`
   - h[n]: `[1, -0.5]`
   - Shows filtering effects

## Custom Mode

Custom Mode allows you to define your own signals using mathematical expressions. The simulator supports a wide range of mathematical functions and signal processing operations.

## Signal Syntax Guide

### Continuous-Time Signals (Variable: t)

For continuous signals, use standard mathematical expressions with `t` as the independent variable.

#### Basic Operators
| Operator | Description | Example |
|----------|-------------|---------|
| `*` | Multiplication | `2 * u(t)` |
| `+`, `-` | Addition, Subtraction | `rect(t+1) - rect(t-1)` |
| `**` or `^` | Exponentiation/Power | `t**2` or `t^2` |
| `/` | Division | `rect(t/2)` |

#### Special Functions

**u(...)** - Unit Step Function
- Represents the Heaviside step function (0 for negative inputs, 1 for positive inputs)
- Examples:
  - `u(t)` → Step that turns on at t=0
  - `u(t-2)` → Step that turns on at t=2
  - `u(t) - u(t-5)` → Rectangular pulse of width 5

**rect(...)** - Rectangular Pulse
- Rectangular pulse of height 1, centered at 0, with total width of 1 (from -0.5 to 0.5)
- Examples:
  - `rect(t)` → Standard rectangular pulse
  - `rect(t-3)` → Pulse centered at t=3
  - `rect(t/2)` → Pulse with width doubled to 2

**tri(...)** - Triangular Pulse
- Triangular pulse of height 1, centered at 0, with base width of 2 (from -1 to 1)
- Examples:
  - `tri(t)` → Standard triangular pulse
  - `5 * tri(t)` → Triangle with peak height of 5

#### Standard Functions
- `exp(...)` - Exponential function (e^x)
- `sin(...)` - Sine function
- `cos(...)` - Cosine function

#### Example Expressions
```
exp(-2*t) * u(t)
sin(2*3.14*t) * (u(t) - u(t-1))
rect(t) * cos(5*t)
```

### Discrete-Time Signals (Variable: n)

Discrete signals can be defined in two ways: as a function of the index n or as a direct list of values.

#### 1. As a Function of n
The syntax is nearly identical to the continuous-time case, but uses `n` as the variable.

**Keywords:**
- `u(n)`, `rect(n)`, `tri(n)` work as expected for discrete indices
- `delta[n]` or `δ[n]` - Unit impulse at n=0 (discrete signals only)

**Examples:**
```
0.9**n * u(n)
cos(0.5*n) * u(n)
5*delta[n] + 2*delta[n-1]
```

#### 2. As a Python List
Define sequences by directly typing values. The first element corresponds to n=0.

**Format:** `[value1, value2, value3, ...]`

**Examples:**
```
[1, 2, 3, 2, 1]        # Sequence with value 1 at n=0, 2 at n=1, etc.
[1, -1]                # Simple differentiator system
[1, 1, 1, 1]          # Four-point moving average filter
```

## Continuous vs Discrete Simulation

### Continuous-Time Mode
- Uses numerical integration for convolution computation
- Adjustable sampling rate (50-2000 Hz) for accuracy vs. performance
- Smooth animation with configurable time steps
- Mathematical visualization shows integral interpretation
- Supports arbitrary mathematical functions

### Discrete-Time Mode
- Uses exact discrete convolution algorithms
- Integer index stepping for precise discrete behavior
- Stem plots for proper discrete signal representation
- Mathematical visualization shows summation interpretation
- Supports both functional and list-based signal definitions

## Visualization Modes

### Mathematical View
The default view shows four synchronized plots:
1. **Input Signal x(τ) or x[k]**: The original input signal
2. **Flipped & Shifted Impulse Response**: h(t-τ) or h[n-k] showing the time-reversed and shifted version
3. **Product**: Point-wise multiplication x(τ)h(t-τ) or x[k]h[n-k]
4. **Convolution Result**: Final output y(t) or y[n] with current time/index highlighted

### Block-Step View
An additional right panel showing the step-by-step convolution process:
1. **Flip**: Time-reverse the impulse response h(-τ) or h[-k]
2. **Shift**: Translate to current time h(t-τ) or h[n-k]
3. **Multiply**: Point-wise multiplication with input signal
4. **Integrate/Sum**: Final integration or summation step

## Export Options

### PNG Snapshots
- High-resolution (300 DPI) image export
- Captures current state of all plots
- Suitable for reports and presentations

### CSV Data Export
- Exports time/index and convolution result values
- Compatible with Excel, MATLAB, and other analysis tools
- Includes proper headers for data identification

### GIF Animations
- Creates animated sequences showing the entire convolution process
- Configurable frame rate and duration
- Perfect for educational materials and presentations

## Known Issues and Fixes

### Performance Considerations
- **Large Time Ranges**: Computation time increases with range size. Recommended maximum: 1000 time units
- **High Sampling Rates**: Rates above 2000 Hz may cause UI lag on slower systems
- **Complex Expressions**: Highly oscillatory functions may require increased sampling rates

### Common Expression Errors
1. **Unbalanced Parentheses**: Check that all `(` have matching `)`
2. **Invalid Function Names**: Use `exp()` not `exponential()`, `sin()` not `sine()`
3. **Variable Confusion**: Use `t` for continuous, `n` for discrete
4. **List Format**: Discrete lists must use square brackets `[1,2,3]`

### Animation Issues
- **Stuttering**: Reduce playback speed or sampling rate
- **Memory Usage**: Long animations may consume significant memory
- **GIF Export**: Large GIFs may take several minutes to generate

## Project Structure

```
convolution-simulator/
│
├── main.py              # Application entry point
├── requirements.txt     # Python dependencies
├── README.md           # This documentation
├── .gitignore          # Git ignore rules
│
├── core/               # Core mathematical operations
│   ├── __init__.py
│   ├── convolution.py  # Convolution computation engine
│   ├── signals.py      # Signal generation and parsing
│   └── utils.py        # Mathematical and plotting utilities
│
├── gui/                # User interface components
│   ├── __init__.py
│   ├── main_window.py  # Main application window
│   ├── controls.py     # Control panel and widgets
│   ├── plotting.py     # Plot management and visualization
│   └── themes.py       # Theme management (light/dark)
│
├── simulation/         # High-level simulation control
│   ├── __init__.py
│   ├── continuous.py   # Continuous-time simulation
│   ├── discrete.py     # Discrete-time simulation
│   └── playback.py     # Animation and playback control
│
└── assets/             # Images and documentation assets
    └── demo_screenshot.png
```

## References

- **Oppenheim, A. V., & Willsky, A. S.**: "Signals and Systems" (2nd Edition)
- **NumPy Documentation**: [https://numpy.org/doc/](https://numpy.org/doc/)
- **Matplotlib Documentation**: [https://matplotlib.org/stable/](https://matplotlib.org/stable/)

---

**Convolution simulator** | Built with ❤️ for engineering education