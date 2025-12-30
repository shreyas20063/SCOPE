# DC Motor Feedback Control Simulation

An interactive Python simulation for visualizing and analyzing DC motor feedback control systems.

## 📚 Course Information

**Course:** Signals and Systems (EE204T)
**Professor:** Ameer Mulla
**Authors:** Duggimpudi Shreyas Reddy, Prathamesh Nerpagar

---

## Also Available as Web Application

This simulation is also available in the **web platform** version with additional features:
- Browser-based interface (no installation required)
- Real-time parameter updates
- Mobile-responsive design

See [signals-web-platform](../signals-web-platform/) for the web version.

---

## 🎯 About This Simulation

This interactive simulation demonstrates fundamental feedback control principles for DC motors. It provides real-time visualization of how different system parameters affect motor behavior, stability, and transient response characteristics.

### What This Simulation Does

The simulator allows users to:
- **Explore parameter effects** on system behavior through interactive sliders
- **Visualize pole-zero maps** in the s-plane to understand system stability
- **Analyze step responses** showing transient and steady-state behavior
- **Toggle between system models** (First-Order and Second-Order dynamics)
- **Observe real-time changes** in system characteristics as parameters vary

### Key Parameters

- **α (Amplifier gain):** Controls the input signal amplification (0.1 to 50.0)
- **β (Feedback gain):** Determines the feedback strength (0.01 to 1.0)
- **γ (Motor constant):** Represents motor torque-to-current ratio (0.1 to 5.0)
- **p (Lag pole):** Adds second-order dynamics to the system (0.5 to 30.0)

## 🔬 Learning Objectives

This simulation helps students understand:
- Feedback control system fundamentals
- System stability analysis through pole location
- Transient response characteristics
- Steady-state behavior and final value theorem
- The relationship between pole positions and time-domain response
- Effects of damping on system behavior (overdamped vs. underdamped)

## 🚀 Getting Started

### Prerequisites

Python 3.7 or higher is required.

### Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd dc-motor-feedback-simulation
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

### Required Files

Ensure these files are in the same directory:
- `main.py` - Entry point
- `simulator.py` - Main simulation class
- `system_calculator.py` - Transfer function calculations
- `plotter.py` - Visualization functions
- `image_389368.png` - First-Order system block diagram
- `image_389387.png` - Second-Order system block diagram
- `requirements.txt` - Python dependencies

### Running the Simulation

```bash
python main.py
```

## 📁 Project Structure

```
DC Motor Simulation/
│
├── main.py                 # Entry point and course information
├── simulator.py            # Main simulator class and UI setup
├── system_calculator.py    # Transfer function and pole-zero calculations
├── plotter.py             # All plotting and visualization functions
├── image_389368.png       # First-Order system block diagram
├── image_389387.png       # Second-Order system block diagram
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

## 🎮 Using the Simulation

### Interface Layout

The simulation window is divided into two main sections:

#### Left Panel - Controls
- **Model Selection:** Toggle between First-Order and Second-Order systems
- **Parameter Sliders:** Adjust α, β, γ, and p (p only visible for Second-Order)
- **Current Values Display:** Shows active parameter values
- **Reset Button:** Returns all parameters to default values

#### Right Panel - Visualizations
1. **Block Diagram:** Shows the system's feedback control structure
2. **Pole-Zero Map:** Displays pole locations in the complex s-plane
   - Green shaded region indicates the stable half-plane
   - Red 'X' marks show pole positions
3. **Step Response:** Time-domain response to unit step input
   - Blue curve shows system response
   - Red dashed line indicates final steady-state value
   - For underdamped systems, envelope curves show oscillation decay
4. **System Information:** Displays transfer function, pole locations, and steady-state value

### Tips for Exploration

1. **Start with First-Order System:**
   - Observe how increasing α affects response speed
   - See how β changes the steady-state value (Final value = 1/β)

2. **Switch to Second-Order System:**
   - Adjust parameters to see overdamped vs. underdamped behavior
   - Watch poles move between real and complex conjugate pairs
   - Observe oscillatory behavior when poles are complex

3. **Stability Analysis:**
   - All poles must be in the left half-plane (negative real part) for stability
   - Complex poles closer to the imaginary axis produce more oscillation
   - Real poles further left produce faster settling

## 📊 System Models

### First-Order Model

**Transfer Function:**
```
Θ(s)/V(s) = αγ/(s + αβγ)
```

**Characteristics:**
- Single pole at s = -αβγ
- Exponential response (no oscillation)
- Faster response with larger αβγ

### Second-Order Model

**Transfer Function:**
```
Θ(s)/V(s) = αγp/(s² + ps + αβγp)
```

**Characteristics:**
- Two poles: s = -p/2 ± √((p/2)² - αβγp)
- Real poles → Overdamped (slow, no overshoot)
- Complex poles → Underdamped (fast, with oscillation)

## 🔧 Technical Details

### Dependencies
- **NumPy (≥1.21.0):** Numerical computations
- **Matplotlib (≥3.4.0):** Interactive visualization and plotting
- **SciPy (≥1.7.0):** Control systems analysis (signal processing)

### Module Descriptions

#### `main.py`
- Application entry point
- Contains course and simulation information
- Initializes and runs the simulator

#### `simulator.py`
- `MotorFeedbackSimulator` class manages the entire application
- Handles UI setup and widget creation
- Coordinates between calculator and plotter modules
- Manages parameter updates and event handling

#### `system_calculator.py`
- `SystemCalculator` class performs all mathematical computations
- Calculates transfer functions for both system models
- Computes pole and zero locations
- Handles discriminant calculations for second-order systems

#### `plotter.py`
- `PlotManager` class handles all visualization tasks
- Draws block diagrams, pole-zero maps, and step responses
- Displays system information and parameter values
- Manages plot formatting and updates

## 📈 Educational Features

### Visual Feedback
- **Real-time updates:** All plots update instantly as parameters change
- **Color coding:** Green (stable), Yellow (underdamped), Red (reference lines)
- **Fixed scales:** Consistent axis limits for better comparison

### System Analysis Tools
- **Pole-Zero Map:** Understand stability from pole locations
- **Step Response:** See actual time-domain behavior
- **Transfer Function Display:** Mathematical representation with current values
- **Steady-State Calculation:** Final value theorem application

## 🎓 Learning Exercises

### Exercise 1: Stability Analysis
1. Start with default parameters
2. Gradually increase α while observing pole movement
3. Note when poles approach the imaginary axis
4. Observe corresponding changes in step response

### Exercise 2: Damping Effects
1. Switch to Second-Order model
2. Adjust parameters to achieve complex conjugate poles
3. Vary parameters to see transitions between:
   - Overdamped (two real poles)
   - Critically damped (repeated real pole)
   - Underdamped (complex conjugate poles)

### Exercise 3: Steady-State Analysis
1. Fix α and γ
2. Vary β from 0.1 to 1.0
3. Observe how steady-state value changes
4. Verify Final Value Theorem: lim[t→∞] θ(t) = 1/β

## 🐛 Troubleshooting

### Images Not Loading
**Error:** "Block diagram images not found"
- Ensure `image_389368.png` and `image_389387.png` are in the same directory as the Python files
- Check file names match exactly (case-sensitive)

### Import Errors
**Error:** "No module named 'scipy'" (or numpy, matplotlib)
```bash
pip install -r requirements.txt
```

### Display Issues
- If plots don't update, try clicking the reset button
- For high-DPI displays, plots may appear small - adjust figsize in `simulator.py` if needed

## 🤝 Contributing

This is an educational project. For suggestions or improvements, feel free to open an issue or submit a pull request.

---

**Note:** This simulation is designed as a learning tool for understanding feedback control systems. It demonstrates core concepts in signals and systems theory through interactive visualization.