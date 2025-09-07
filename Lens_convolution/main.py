"""
Lens Imaging and Blurring Simulation
Main application entry point
"""

import sys
import numpy as np
from PyQt5.QtWidgets import QApplication
from gui.main_window import MainWindow

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Start event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()