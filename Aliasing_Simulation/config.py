"""
Configuration file for Signal Processing Lab
Contains color palette and appearance settings
"""

import customtkinter as ctk
import matplotlib
matplotlib.use('TkAgg')

# --- Color Palette ---
COLORS = {
    'bg': '#F9FAFB',        # Very light gray background
    'panel': '#FFFFFF',       # White panels
    'accent': '#2563EB',      # Vibrant blue accent
    'accent_dark': '#1D4ED8', # Darker blue for hover/press
    'success': '#22C55E',     # Bright green for success/play
    'warning': '#F59E0B',     # Amber/yellow for warning/play
    'danger': '#EF4444',      # Red for danger/errors
    'text_primary': '#0F172A',# Very dark blue/black for main text
    'text_secondary': '#475569',# Muted gray for secondary text
    'border': '#E2E8F0',      # Light gray for borders
    'grid': '#D1D5DB'         # Slightly darker gray for plot grids
}

# --- CustomTkinter Appearance Settings ---
def setup_appearance():
    """Initialize CustomTkinter appearance settings"""
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")