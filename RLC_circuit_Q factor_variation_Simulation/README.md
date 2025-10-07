# Interactive RLC Circuit Frequency Response Simulator

Signals and Systems (EE204T) course project carried out under Prof. Ameer Mulla  
by Duggimpudi Shreyas Reddy and Prathamesh Nerpagar.

This repository provides an interactive visualiser for a second-order series RLC circuit.  
Users can explore how the natural frequency (ω₀) and quality factor (Q) influence pole locations,  
the Bode magnitude/phase responses, and key system indicators such as resonant frequency and bandwidth.

## Project Layout

```
RLC_circuit_Q factor_variation/
├── README.md
├── main.py              # CLI entry point
├── gui/
│   ├── __init__.py
│   └── simulator.py     # Figure/slider wiring and UI logic
├── models/
│   ├── __init__.py
│   └── rlc_system.py    # System parameters and analytical routines
└── plotting/
    ├── __init__.py
    └── visuals.py       # Plot rendering helpers
```

Each module has a focused responsibility so that future debugging or extensions (e.g., new plots)  
can remain isolated and easier to maintain.

## Features

- Interactive sliders for ω₀ (natural frequency) and Q (quality factor)  
- Linked pole-zero diagram, Bode magnitude, and Bode phase plots with fixed axes for comparison  
- System information panel summarising damping classification, pole locations, and bandwidth metrics  
- Stable left-half plane shading and ω₀ reference circle for quick qualitative insights  

## Setup

Install the dependencies with pip if required:

```bash
pip install numpy matplotlib scipy
```

## Running the Simulator

From the repository root, launch the application with:

```bash
python3 main.py
```

An interactive Matplotlib window opens; adjust the sliders at the bottom to explore different configurations.

## Acknowledgement

This simulator was developed for the Signals and Systems (EE204T) course,  
guided by Prof. Ameer Mulla, with implementation by Duggimpudi Shreyas Reddy and Prathamesh Nerpagar.
