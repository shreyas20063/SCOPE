"""Entry point for the Fourier series visualizer.

Prepared for the Signals and Systems course (EE204T) under
Prof. Ameer Mulla by Duggimpudi Shreyas Reddy and Prathamesh Nerpagar.
"""

import sys
from PyQt5.QtWidgets import QApplication
from gui.visualizer import FourierSeriesVisualizer


def main() -> None:
    """Launch the interactive visualizer."""
    app = QApplication(sys.argv)
    visualizer = FourierSeriesVisualizer()
    visualizer.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
