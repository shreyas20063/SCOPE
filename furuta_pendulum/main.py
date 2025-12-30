"""
Furuta Pendulum (Rotary Inverted Pendulum) Simulator - PyQt5 Version

An interactive 3D simulation demonstrating stabilization of an unstable system
using PID control. The Furuta Pendulum consists of a rotating arm with a
pendulum hanging from its end, and the goal is to keep the pendulum upright.

Course: Signals and Systems (EE204T)
Instructor: Prof. Ameer Mulla
Authors: Duggimpudi Shreyas Reddy, Prathamesh Nerpagar

Project Structure:
- core/pendulum_dynamics.py - Physical model and equations of motion
- core/pid_controller.py - PID controller implementation
- gui/main_window.py - PyQt5-based 3D visualization and user interface
"""

import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication

# Add parent directory to path
parent_path = Path(__file__).parent
sys.path.insert(0, str(parent_path))

from core.pendulum_dynamics import FurutaPendulumPhysics
from core.pid_controller import PIDController
from gui.main_window import FurutaPendulumWindow


def main():
    """
    Main entry point for the Furuta Pendulum simulator.

    This function:
    1. Creates the physics model
    2. Initializes the PID controller
    3. Sets up the PyQt5 visualization window
    4. Runs the interactive simulation
    """
    print("="*70)
    print("    Furuta Pendulum Simulator - PyQt5 Professional Version")
    print("="*70)
    print("\nCourse: Signals and Systems (EE204T)")
    print("Instructor: Prof. Ameer Mulla")
    print("Authors: Duggimpudi Shreyas Reddy, Prathamesh Nerpagar")
    print("="*70)
    print("\nStarting PyQt5 application...")
    print("✓ Professional PyQt5 interface with embedded matplotlib")
    print("✓ 3D visualization with direction arrows")
    print("✓ Real-time plots for angle and control torque")
    print("✓ Interactive sliders for all parameters")
    print("\nVisual Indicators:")
    print("  - Blue arrow = Counter-Clockwise rotation")
    print("  - Red arrow = Clockwise rotation")
    print("  - Green/Orange at base = Torque direction")
    print("  - Status panel shows real-time system state")
    print("\nControls:")
    print("  - Use sliders in right panel to adjust parameters")
    print("  - Click 'Start/Pause' to begin/pause simulation")
    print("  - Click 'Reset' to restore initial conditions")
    print("  - Click 'Disturb' to test controller response")
    print("  - Drag with mouse to rotate 3D view")
    print("="*70)
    print()

    # Initialize components
    physics = FurutaPendulumPhysics(
        mass=0.05,           # 50 grams
        pendulum_length=0.2, # 20 cm
        arm_length=0.15      # 15 cm
    )

    controller = PIDController(
        kp=150.0,  # Proportional gain (tested and stable)
        kd=25.0,   # Derivative gain (good damping)
        ki=5.0,    # Integral gain (eliminates steady-state error)
        dt=0.01    # 10ms timestep
    )

    # Create PyQt5 application
    app = QApplication(sys.argv)
    app.setApplicationName("Furuta Pendulum Simulator")

    # Create and show main window
    window = FurutaPendulumWindow(physics, controller)
    window.show()

    # Run application event loop
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
