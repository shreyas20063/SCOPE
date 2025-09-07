#!/usr/bin/env python3
"""
Convolution Simulator - Main Entry Point

A comprehensive tool for visualizing convolution operations
for both continuous and discrete-time signals.

Usage:
    python main.py

"""

import tkinter as tk
from gui.main_window import ConvolutionSimulator

def main():
    """Initialize and run the Convolution Simulator application."""
    root = tk.Tk()
    app = ConvolutionSimulator(root)
    root.mainloop()

if __name__ == "__main__":
    main()
