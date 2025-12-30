# Interactive Second-Order System Response Simulator

Signals and Systems (EE204T) course project carried out under Prof. Ameer Mulla
by Duggimpudi Shreyas Reddy and Prathamesh Nerpagar.

---

## Also Available as Web Application

This simulation is also available in the **web platform** version with additional features:
- Browser-based interface (no installation required)
- Real-time parameter updates
- Mobile-responsive design

See [signals-web-platform](../signals-web-platform/) for the web version.

---

This repository provides an interactive visualiser for a second-order system.
Users can explore how the natural frequency (ω₀) and quality factor (Q) influence pole locations,
the Bode magnitude/phase responses, and key system indicators such as resonant frequency and bandwidth.

## Project Layout

```
second_order_system/
├── README.md
├── main.py              # CLI entry point with PyQt5/Matplotlib fallback
├── gui/
│   ├── __init__.py
│   ├── pyqt5_simulator.py  # PyQt5-based UI (primary interface)
│   └── simulator.py        # Matplotlib widgets UI (fallback)
├── core/
│   ├── __init__.py
│   └── system.py        # System parameters and analytical routines
├── plotting/
│   ├── __init__.py
│   └── visuals.py       # Plot rendering helpers
├── utils/               # Utility functions (reserved for future use)
└── assets/              # Static assets (reserved for future use)
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
pip install -r requirements.txt
```

Or install individually:

```bash
pip install numpy matplotlib scipy PyQt5
```

Note: PyQt5 is now the primary interface. If PyQt5 is not installed, the application will automatically fall back to the Matplotlib widgets interface.

## Running the Simulator

From the repository root, launch the application with:

```bash
python3 main.py
```

A PyQt5 window with embedded Matplotlib plots will open. Adjust the sliders at the bottom to explore different configurations interactively.

## Acknowledgement

This simulator was developed for the Signals and Systems (EE204T) course,
guided by Prof. Ameer Mulla, with implementation by Duggimpudi Shreyas Reddy and Prathamesh Nerpagar.
