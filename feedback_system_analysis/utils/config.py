"""
Configuration module for Feedback System Analysis
Contains all constants, default parameters, and styling configurations
"""

import numpy as np
import matplotlib.pyplot as plt

# Default System Parameters
DEFAULT_K0 = 200000.0          # Open-loop gain
DEFAULT_ALPHA = 40.0            # Pole location (rad/s)
DEFAULT_BETA = 0.0041           # Feedback factor
DEFAULT_INPUT_AMP = 1.0         # Input amplitude (V)

# Frequency Range for Bode Plots
OMEGA_MIN = -1                  # 10^-1 rad/s
OMEGA_MAX = 8                   # 10^8 rad/s
OMEGA_POINTS = 800

# Time Domain Settings
TIME_MAX = 2.0                  # Maximum time for step response (s)
TIME_POINTS = 1000

# Slider Ranges
BETA_RANGE = (0.0, 0.01, 0.0001)       # min, max, step
K0_RANGE = (1e4, 5e5, 1000)             # min, max, step
ALPHA_RANGE = (10, 200, 1)              # min, max, step
INPUT_RANGE = (0.1, 2.0, 0.01)          # min, max, step

# Plot Limits
STEP_RESPONSE_Y_MAX = 1.2e6
S_PLANE_X_MIN = -150000
S_PLANE_X_MAX = 1000

# Color Scheme
COLORS = {
    'open_loop': '#d62728',
    'closed_loop': '#1f77b4',
    'title': '#0077b6',
    'success': '#16a34a',
    'background': '#f4f4f5',
    'axes': '#ffffff',
    'edge': '#a1a1aa',
    'grid': '#d4d4d8',
    'text': '#18181b',
    'slider': '#0077b6',
}

# Panel Colors
PANEL_COLORS = {
    'info': ('#e0f2fe', '#0077b6'),      # bg, edge
    'metrics': ('#dcfce7', '#16a34a'),    # bg, edge
}

def setup_plot_style():
    """Configure matplotlib plot style for professional appearance"""
    plt.style.use('seaborn-v0_8-whitegrid')
    plt.rcParams['figure.facecolor'] = COLORS['background']
    plt.rcParams['axes.facecolor'] = COLORS['axes']
    plt.rcParams['axes.edgecolor'] = COLORS['edge']
    plt.rcParams['grid.color'] = COLORS['grid']
    plt.rcParams['text.color'] = COLORS['text']
    plt.rcParams['axes.labelcolor'] = COLORS['text']
    plt.rcParams['xtick.color'] = '#3f3f46'
    plt.rcParams['ytick.color'] = '#3f3f46'
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
    plt.rcParams['font.size'] = 10
