"""
Feedback System Analysis Simulator - PyQt5 Version

Course: Signals and Systems (EE204T)
Professor: Ameer Mulla
Students: Prathamesh Nerpagar, Duggimpudi Shreyas Reddy

This simulation demonstrates the effects of feedback on system performance,
including changes in bandwidth, gain, rise time, and pole locations. Users can
interactively adjust system parameters (K₀, α, β, input amplitude) using sliders
and observe real-time updates to:
- Step response comparisons
- Bode magnitude and phase plots
- S-plane pole locations
- Performance metrics

The simulation visualizes both open-loop and closed-loop system behaviors,
helping students understand fundamental feedback control concepts.

This version uses PyQt5 for a modern, professional GUI with embedded matplotlib canvases.
"""

import sys
import warnings
from PyQt5.QtWidgets import QApplication

from gui.main_window import FeedbackAmplifierWindow

warnings.filterwarnings('ignore')


def main():
    """Main function to run the PyQt5 simulator"""
    try:
        app = QApplication(sys.argv)
        app.setStyle('Fusion')  # Use Fusion style for a modern look

        window = FeedbackAmplifierWindow()
        window.show()

        sys.exit(app.exec_())

    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
