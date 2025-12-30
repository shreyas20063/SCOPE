"""
Fourier Analysis: Phase Vs Magnitude Application
Main application entry point

This application demonstrates the importance of phase vs magnitude
in Fourier transforms through interactive visualization.
"""

import sys
from PyQt5.QtWidgets import QApplication
from gui.main_window import MainWindow


def main():
    """Main application entry point"""
    print("=" * 70)
    print("FOURIER ANALYSIS: PHASE VS MAGNITUDE")
    print("=" * 70)
    print("\nStarting application...")
    print("\nFeatures:")
    print("  • Interactive Fourier transform analysis")
    print("  • Magnitude and phase manipulation")
    print("  • Hybrid image generation")
    print("  • Multiple visualization tabs")
    print("  • Real-time parameter updates")
    print("  • Export results and plots")
    print("\nControls:")
    print("  • Select different image modes (Original, Uniform Magnitude, Uniform Phase)")
    print("  • Adjust uniform values with sliders")
    print("  • Load custom images or use test patterns")
    print("  • View results across multiple analysis tabs")
    print("\n" + "=" * 70 + "\n")

    # Create Qt application
    app = QApplication(sys.argv)

    # Set application metadata
    app.setApplicationName("Fourier Analysis: Phase Vs Magnitude")
    app.setOrganizationName("Fourier Analysis: Phase Vs Magnitude")

    # Create and show main window
    window = MainWindow()
    window.show()

    print("Application window opened successfully!")
    print("\nTip: Experiment with 'Uniform Magnitude' mode to see that")
    print("     phase preserves image structure!\n")

    # Start event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
