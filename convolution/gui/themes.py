"""
Theme management for the Convolution Simulator.

This module handles light/dark theme switching and visual styling
for both the GUI components and matplotlib plots.
"""

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt
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
        self.app.dark_mode = self.app.dark_mode_checkbox.isChecked()
        self.apply_theme()

    def apply_theme(self):
        """Apply the currently selected theme."""
        is_dark = self.app.dark_mode
        theme = self.dark_theme if is_dark else self.light_theme

        # Apply to main window
        self._apply_qt_theme(theme)

        # Apply to matplotlib figures
        self._apply_matplotlib_theme(theme)

        # Redraw canvases
        self.app.canvas.draw()
        if hasattr(self.app, 'block_canvas'):
            self.app.block_canvas.draw()

    def _apply_qt_theme(self, theme):
        """Apply theme to Qt widgets."""
        # Create a stylesheet for the application
        bg_color = theme['bg']
        fg_color = theme['fg']

        # Comprehensive stylesheet
        stylesheet = f"""
            QMainWindow {{
                background-color: {bg_color};
                color: {fg_color};
            }}
            QWidget {{
                background-color: {bg_color};
                color: {fg_color};
            }}
            QLabel {{
                background-color: transparent;
                color: {fg_color};
            }}
            QPushButton {{
                background-color: {bg_color};
                color: {fg_color};
                border: 1px solid {fg_color};
                padding: 5px;
                border-radius: 3px;
            }}
            QPushButton:hover {{
                background-color: {'#404040' if theme == self.dark_theme else '#e0e0e0'};
            }}
            QPushButton:pressed {{
                background-color: {'#505050' if theme == self.dark_theme else '#d0d0d0'};
            }}
            QLineEdit {{
                background-color: {'#404040' if theme == self.dark_theme else 'white'};
                color: {fg_color};
                border: 1px solid {fg_color};
                padding: 3px;
                border-radius: 3px;
            }}
            QComboBox {{
                background-color: {'#404040' if theme == self.dark_theme else 'white'};
                color: {fg_color};
                border: 1px solid {fg_color};
                padding: 3px;
                border-radius: 3px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background-color: {'#404040' if theme == self.dark_theme else 'white'};
                color: {fg_color};
                selection-background-color: {'#505050' if theme == self.dark_theme else '#e0e0e0'};
            }}
            QGroupBox {{
                background-color: transparent;
                color: {fg_color};
                border: 1px solid {fg_color};
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }}
            QRadioButton {{
                background-color: transparent;
                color: {fg_color};
            }}
            QCheckBox {{
                background-color: transparent;
                color: {fg_color};
            }}
            QSlider::groove:horizontal {{
                border: 1px solid {fg_color};
                height: 8px;
                background: {'#404040' if theme == self.dark_theme else '#d0d0d0'};
                margin: 2px 0;
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {fg_color};
                border: 1px solid {fg_color};
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }}
        """

        self.app.setStyleSheet(stylesheet)

    def _apply_matplotlib_theme(self, theme):
        """Apply theme to matplotlib figures."""
        # Main figure
        if hasattr(self.app, 'fig'):
            if theme == self.dark_theme:
                self.plot_utils.configure_dark_theme(
                    self.app.fig, self.app.get_current_axes()
                )
            else:
                self.plot_utils.configure_light_theme(
                    self.app.fig, self.app.get_current_axes()
                )

        # Block figure
        if hasattr(self.app, 'block_fig'):
            if theme == self.dark_theme:
                self.plot_utils.configure_dark_theme(
                    self.app.block_fig, self.app.get_block_axes()
                )
            else:
                self.plot_utils.configure_light_theme(
                    self.app.block_fig, self.app.get_block_axes()
                )

    def get_current_theme_colors(self):
        """Get current theme color scheme."""
        return self.dark_theme if self.app.dark_mode else self.light_theme
