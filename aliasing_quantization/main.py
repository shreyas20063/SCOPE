"""
Signal Processing Lab - Main Entry Point
Aliasing and Quantization Simulator
"""

import sys
from PyQt5.QtWidgets import QApplication
from gui.main_window import SignalProcessingLab

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SignalProcessingLab()
    window.show()
    sys.exit(app.exec_())