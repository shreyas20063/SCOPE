"""
Furuta Pendulum (Rotary Inverted Pendulum) Simulator

An interactive 3D simulation demonstrating stabilization of an unstable system
using PID control. The Furuta Pendulum consists of a rotating arm with a
pendulum hanging from its end, and the goal is to keep the pendulum upright.

Course: Signals and Systems (EE204T)
Instructor: Prof. Ameer Mulla
Authors: Duggimpudi Shreyas Reddy, Prathamesh Nerpagar

Project Structure:
- src/physics/pendulum_dynamics.py - Physical model and equations of motion
- src/control/pid_controller.py - PID controller implementation
- src/gui/visualizer.py - 3D visualization and user interface
"""

import sys
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from physics.pendulum_dynamics import FurutaPendulumPhysics
from control.pid_controller import PIDController
from gui.visualizer import FurutaPendulumVisualizer


def main():
    """
    Main entry point for the Furuta Pendulum simulator.

    This function:
    1. Creates the physics model
    2. Initializes the PID controller
    3. Sets up the visualization
    4. Runs the interactive simulation
    """
    print("="*70)
    print("        Furuta Pendulum Simulator - Interactive 3D Version")
    print("="*70)
    print("\nCourse: Signals and Systems (EE204T)")
    print("Instructor: Prof. Ameer Mulla")
    print("Authors: Duggimpudi Shreyas Reddy, Prathamesh Nerpagar")
    print("="*70)
    print("\nStarting simulation...")
    print("✓ Direction arrows show arm rotation clearly!")
    print("✓ Torque direction indicators at base")
    print("✓ Watch the arm reverse when control changes")
    print("\nVisual Indicators:")
    print("  - Blue arrow = Counter-Clockwise rotation")
    print("  - Red arrow = Clockwise rotation")
    print("  - Green/Orange at base = Torque direction")
    print("  - Status shows ω_φ (arm angular velocity)")
    print("\nControls:")
    print("  - Use sliders to adjust parameters")
    print("  - Click 'Start/Pause' to begin simulation")
    print("  - Click 'Reset' to stop and clear everything")
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

    # Create and run visualizer
    visualizer = FurutaPendulumVisualizer(physics, controller)
    visualizer.run()


if __name__ == '__main__':
    main()
