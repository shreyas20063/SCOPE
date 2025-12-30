"""
Configuration file for Amplifier Topologies
Contains all constants and default parameters
"""

import os

# System Default Parameters
K_DEFAULT = 100.0
F0_DEFAULT = 10.0
BETA_DEFAULT = 0.1
VT_DEFAULT = 0.7

# Parameter Ranges
K_MIN, K_MAX = 1, 200
F0_MIN, F0_MAX = 8, 12
BETA_MIN, BETA_MAX = 0.01, 1.0

# Audio Settings
DEFAULT_SAMPLE_RATE = 44100
DEFAULT_DURATION = 1.0
DEFAULT_AMPLITUDE = 0.1
DEFAULT_FREQUENCY = 120
MAX_AUDIO_DURATION = 10  # seconds

# UI Settings
WINDOW_TITLE = "Amplifier Topologies"
WINDOW_WIDTH = 1600
WINDOW_HEIGHT = 850

# Plot Settings
PLOT_WINDOW_SIZE = 3000
INPUT_YLIM = (-0.15, 0.15)
INITIAL_OUTPUT_LIMIT = 0.1

# Image Settings
IMAGE_BOUNDING_BOX = (300, 175)
# Get the directory where this config file is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
IMAGE_MAP = {
    'simple': os.path.join(ASSETS_DIR, 'simple.png'),
    'feedback': os.path.join(ASSETS_DIR, 'feedback.png'),
    'crossover': os.path.join(ASSETS_DIR, 'crossover.png'),
    'compensated': os.path.join(ASSETS_DIR, 'compensated.png')
}

# Amplifier Configurations
AMPLIFIER_CONFIGS = [
    ("1. Simple Amplifier", 'simple'), 
    ("2. Feedback System", 'feedback'), 
    ("3. Crossover Distortion", 'crossover'), 
    ("4. Compensated System", 'compensated')
]

# Plot Colors
COLOR_INPUT = '#00A0FF'
COLOR_OUTPUT = '#FF5733'
COLOR_SIMPLE_GAIN = '#00A0FF'
COLOR_FEEDBACK_GAIN = 'green'
COLOR_IDEAL_GAIN = 'purple'
COLOR_CURRENT_F0 = 'red'
COLOR_XY_PLOT = '#FFC300'
COLOR_RESET_BUTTON = 'goldenrod'

# Plot Style
PLOT_STYLE = 'seaborn-v0_8-whitegrid'
