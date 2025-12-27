"""
Theme management for the Convolution Simulator.

This module handles light/dark theme switching and visual styling
for both the GUI components and matplotlib plots.
"""

import tkinter as tk
from tkinter import ttk
from core.utils import PlotUtils

class ThemeManager:
    """Manages application themes and visual styling."""
    
    def __init__(self, main_app):
        self.app = main_app
        self.plot_utils = PlotUtils()
        
        # Theme colors
        self.light_theme = {
            'bg': '#f0f0f0',
            'fg': 'black',
            'fig_bg': 'white',
            'grid_color': 'gray'
        }
        
        self.dark_theme = {
            'bg': '#2e2e2e',
            'fg': 'white',
            'fig_bg': '#333333',
            'grid_color': 'lightgray'
        }
    
    def toggle_theme(self):
        """Toggle between light and dark themes."""
        self.apply_theme()
    
    def apply_theme(self):
        """Apply the currently selected theme."""
        is_dark = self.app.dark_mode.get()
        theme = self.dark_theme if is_dark else self.light_theme
        
        # Apply to root window
        self.app.root.configure(bg=theme['bg'])
        
        # Configure ttk styles
        self._configure_ttk_styles(theme)
        
        # Apply to matplotlib figures
        self._apply_matplotlib_theme(theme)
        
        # Redraw canvases
        self.app.canvas.draw()
        if hasattr(self.app, 'block_canvas'):
            self.app.block_canvas.draw()
    
    def _configure_ttk_styles(self, theme):
        """Configure ttk widget styles."""
        style = ttk.Style()
        
        # Configure base styles
        style.configure('.', 
                       background=theme['bg'], 
                       foreground=theme['fg'])
        
        # Configure specific widget styles
        widgets = [
            'TLabel', 'TButton', 'TRadiobutton', 
            'TCheckbutton', 'TLabelframe', 'TEntry',
            'TCombobox', 'TScale', 'TFrame'
        ]
        
        for widget in widgets:
            style.configure(widget, 
                           background=theme['bg'], 
                           foreground=theme['fg'])
        
        # Special handling for labelframe labels
        style.configure('TLabelframe.Label', 
                       background=theme['bg'], 
                       foreground=theme['fg'])
        
        # Configure entry and combobox fieldbackground
        style.configure('TEntry', fieldbackground=theme['bg'])
        style.configure('TCombobox', fieldbackground=theme['bg'])
        
        # Configure scale (slider) colors
        style.configure('TScale', 
                       background=theme['bg'],
                       troughcolor=theme['bg'],
                       darkcolor=theme['fg'],
                       lightcolor=theme['fg'])
    
    def _apply_matplotlib_theme(self, theme):
        """Apply theme to matplotlib figures."""
        # Main figure
        if hasattr(self.app, 'fig'):
            self.plot_utils.configure_dark_theme(
                self.app.fig, self.app.get_current_axes()
            ) if theme == self.dark_theme else self.plot_utils.configure_light_theme(
                self.app.fig, self.app.get_current_axes()
            )
        
        # Block figure
        if hasattr(self.app, 'block_fig'):
            self.plot_utils.configure_dark_theme(
                self.app.block_fig, self.app.get_block_axes()
            ) if theme == self.dark_theme else self.plot_utils.configure_light_theme(
                self.app.block_fig, self.app.get_block_axes()
            )
    
    def get_current_theme_colors(self):
        """Get current theme color scheme."""
        return self.dark_theme if self.app.dark_mode.get() else self.light_theme
