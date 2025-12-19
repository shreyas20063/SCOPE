#!/usr/bin/env python3
"""
Convolution Simulator - Main Entry Point

A comprehensive tool for visualizing convolution operations
for both continuous and discrete-time signals.

Usage:
    python main.py

"""

import sys

# Set matplotlib backend before importing PyQt5
import matplotlib
matplotlib.use('Qt5Agg')

from PyQt5.QtWidgets import QApplication
from gui.main_window import ConvolutionSimulator

def main():
    """Initialize and run the Convolution Simulator application."""
    app = QApplication(sys.argv)
    window = ConvolutionSimulator()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
