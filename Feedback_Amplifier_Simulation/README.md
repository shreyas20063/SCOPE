# Interactive Feedback Amplifier Simulator

An interactive Python-based simulator for visualizing and understanding feedback control systems in amplifiers, developed as part of the **Signals and Systems (EE204T)** course.

## 📚 Course Information

- **Course**: Signals and Systems (EE204T)
- **Professor**: Ameer Mulla
- **Students**: 
  - Prathamesh Nerpagar
  - Duggimpudi Shreyas Reddy

## 🎯 What This Simulation Does

This interactive tool demonstrates how feedback affects amplifier performance in real-time. Users can adjust system parameters using sliders and immediately observe the effects on:

- **Step Response**: Compare how open-loop and closed-loop systems respond to step inputs
- **Bode Plots**: Visualize frequency response in both magnitude and phase
- **S-Plane Analysis**: Track pole locations as feedback parameters change
- **Performance Metrics**: Monitor gain, bandwidth, rise time, and speedup factors

### Key Learning Objectives

- Understand the trade-off between gain and bandwidth in feedback systems
- Observe how negative feedback improves system speed and stability
- Visualize the relationship between pole locations and system behavior
- Explore the impact of feedback factor (β) on overall system performance

## 🔧 System Model

The simulator implements the following transfer functions:

**Open-Loop System:**
```
K(s) = αK₀/(s + α)
```

**Closed-Loop System:**
```
H(s) = αK₀/(s + α(1 + βK₀))
```

Where:
- `K₀` = Open-loop gain
- `α` = Pole location (rad/s)
- `β` = Feedback factor

## 📦 Installation

### Prerequisites

- Python 3.7 or higher
- pip package manager

### Required Libraries

Install all dependencies using:

```bash
pip install -r requirements.txt
```

Or install individually:

```bash
pip install numpy matplotlib
```

## 🚀 Usage

### Running the Simulator

Simply run the main script:

```bash
python main.py
```

### Interactive Controls

The simulator provides four sliders to adjust system parameters:

1. **β (Feedback)**: Range 0.0 to 0.01 - Controls the feedback strength
2. **K₀ (Gain)**: Range 10,000 to 500,000 - Sets the open-loop gain
3. **α (Pole rad/s)**: Range 10 to 200 - Determines the open-loop pole location
4. **Input (V)**: Range 0.1 to 2.0 - Sets the input signal amplitude

### Understanding the Displays

**Left Column (Main Plots):**
- Top: Step response comparison
- Middle: Bode magnitude plot
- Bottom: Bode phase plot

**Right Column (Analysis Panels):**
- Top: System equations and current parameters
- Middle: S-plane pole locations with movement arrows
- Bottom Left: Detailed performance metrics
- Bottom Right: Block diagram (requires `image_1dc166.png`)

## 📁 Project Structure

```
Feedback Amplifier Simulation/
│
├── main.py              # Main application and GUI
├── config.py            # Configuration and constants
├── calculations.py      # Core mathematical computations
├── plotting.py          # Visualization functions
├── image_1dc166.png     # Block diagram image
├── requirements.txt     # Python dependencies
├── README.md           # This file
└── .gitignore          # Git ignore rules
```

## 🔬 Module Descriptions

### `config.py`
Contains all configuration constants, default parameters, color schemes, and plot styling settings. Centralizes all configurable values for easy modification.

### `calculations.py`
Implements core signal processing and mathematical computations:
- System metrics calculations
- Step response generation
- Bode plot calculations (magnitude and phase)
- Value formatting utilities

### `plotting.py`
Handles all visualization tasks:
- Plot rendering for step response, Bode plots, and s-plane
- Information panel displays
- Metrics panel formatting
- Block diagram display

### `main.py`
The main application that ties everything together:
- Initializes the simulator
- Creates the GUI layout
- Manages slider interactions
- Coordinates updates across all displays

## 🎓 Educational Use

This simulator is designed to help students:

1. **Visualize Feedback Effects**: See how feedback reduces gain but increases bandwidth
2. **Understand System Dynamics**: Observe the relationship between pole locations and time-domain behavior
3. **Experiment Freely**: Safe environment to test extreme parameter values
4. **Build Intuition**: Develop understanding of control system trade-offs

## 📊 Example Experiments

### Experiment 1: Impact of Feedback
1. Set β = 0 (no feedback)
2. Observe open-loop behavior
3. Gradually increase β
4. Notice bandwidth increase and gain reduction

### Experiment 2: Gain-Bandwidth Trade-off
1. Start with default parameters
2. Increase K₀ to maximum
3. Adjust β to see compensation effects
4. Compare speedup factors

### Experiment 3: Pole Movement
1. Focus on the s-plane plot
2. Vary β and observe pole migration
3. Relate pole position to rise time changes

## 🐛 Troubleshooting

**Issue**: Block diagram not displaying
- **Solution**: Ensure `image_1dc166.png` is in the same directory as `main.py`

**Issue**: Plots not updating smoothly
- **Solution**: Close other applications to free up system resources

**Issue**: Import errors
- **Solution**: Verify all four Python files are in the same directory

---

**Note**: This simulator is a teaching tool designed to complement theoretical learning with interactive visualization. Experiment freely to build your intuition about feedback control systems!