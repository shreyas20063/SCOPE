"""
CLI launcher for the Second-Order System frequency response simulator.

Developed for the Signals and Systems (EE204T) course project under
Prof. Ameer Mulla by Duggimpudi Shreyas Reddy and Prathamesh Nerpagar.
"""

from __future__ import annotations

import sys


def main() -> None:
    """Launch the simulator with PyQt5 interface."""
    try:
        # Try to import PyQt5 and use the new interface
        from gui.pyqt5_simulator import launch_simulator
        print("Launching PyQt5-based simulator...")
        launch_simulator()
    except ImportError as e:
        # Fallback to matplotlib widgets if PyQt5 is not available
        print(f"PyQt5 not available ({e}). Falling back to Matplotlib widgets...")
        from gui.simulator import launch_simulator
        launch_simulator()


if __name__ == "__main__":
    main()
