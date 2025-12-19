#!/usr/bin/env python3
"""
CT & DT Poles Conversion - Interactive Learning Tool

An educational tool for understanding continuous-time to discrete-time
system transformations using different numerical integration methods.
"""

import sys
from PyQt5.QtWidgets import QApplication
from gui.main_window import MainWindow


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("CT & DT Poles Conversion")
    app.setStyle('Fusion')

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
