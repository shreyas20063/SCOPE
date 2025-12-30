"""PyQt5-based GUI for exploring Fourier series approximations."""

from __future__ import annotations

import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.gridspec as gridspec

from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSlider,
    QPushButton,
    QLabel,
    QApplication,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from core.series import describe_series, fourier_series
from core.waveforms import (
    square_wave,
    triangle_wave,
    square_wave_harmonic,
    triangle_wave_harmonic,
)
from utils.colors import ColorScheme


class MplCanvas(FigureCanvas):
    """Matplotlib canvas for embedding in PyQt5."""

    def __init__(self, parent=None, width=14, height=8, dpi=100):
        self.colors = ColorScheme()

        # Configure matplotlib fonts
        plt.rcParams["font.family"] = "STIXGeneral"
        plt.rcParams["mathtext.fontset"] = "stix"

        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor=self.colors.fig_bg)

        # Create layout
        layout = gridspec.GridSpec(
            2,
            2,
            figure=self.fig,
            left=0.10,
            right=0.95,
            top=0.93,
            bottom=0.10,
            width_ratios=[3, 1],
            height_ratios=[1.3, 1],
            hspace=0.30,
            wspace=0.15,
        )

        self.ax_main = self.fig.add_subplot(layout[0, 0])
        self.ax_harmonics = self.fig.add_subplot(layout[1, 0], sharex=self.ax_main)
        self.ax_controls = self.fig.add_subplot(layout[:, 1])

        self.fig.suptitle(
            "Interactive Fourier Series Visualization",
            fontsize=20,
            color=self.colors.text,
            y=0.97,
            weight="bold",
        )

        # Configure axes
        for ax in [self.ax_main, self.ax_harmonics]:
            ax.set_facecolor(self.colors.fig_bg)

        self.ax_controls.set_facecolor(self.colors.panel)
        self.ax_controls.tick_params(axis="both", which="both", length=0)
        self.ax_controls.set_xticklabels([])
        self.ax_controls.set_yticklabels([])
        for spine in self.ax_controls.spines.values():
            spine.set_edgecolor(self.colors.panel_border)
            spine.set_linewidth(2)

        super(MplCanvas, self).__init__(self.fig)


class FourierSeriesVisualizer(QMainWindow):
    """Interactive Fourier series visualizer with PyQt5 and embedded matplotlib."""

    def __init__(self) -> None:
        super().__init__()

        self.colors = ColorScheme()
        self.t = np.linspace(0, 2, 3000)
        self.max_harmonics = 50
        self.current_harmonics = 1
        self.wave_type: str = "Square Wave"

        self.init_ui()
        self.update_display()

    def init_ui(self) -> None:
        """Initialize the user interface."""
        self.setWindowTitle("Fourier Series Visualization")
        self.setGeometry(100, 100, 1400, 900)

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Create matplotlib canvas
        self.canvas = MplCanvas(self, width=14, height=8, dpi=100)
        main_layout.addWidget(self.canvas)

        # Create control panel
        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel)

        # Set background color
        palette = self.palette()
        from PyQt5.QtGui import QColor
        palette.setColor(self.backgroundRole(), QColor(self.colors.bg))
        self.setPalette(palette)

    def create_control_panel(self) -> QWidget:
        """Create the control panel with slider and buttons."""
        control_widget = QWidget()
        control_layout = QVBoxLayout(control_widget)

        # Create slider section
        slider_layout = QHBoxLayout()

        # Slider label
        self.slider_label = QLabel(f"Harmonics (n): {self.current_harmonics}")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.slider_label.setFont(font)
        slider_layout.addWidget(self.slider_label)

        # Slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(1)
        self.slider.setMaximum(self.max_harmonics)
        self.slider.setValue(self.current_harmonics)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(5)
        self.slider.valueChanged.connect(self.on_slider_change)
        slider_layout.addWidget(self.slider)

        control_layout.addLayout(slider_layout)

        # Create button section
        button_layout = QHBoxLayout()

        # Square wave button
        self.square_button = QPushButton("Square Wave")
        self.square_button.setCheckable(True)
        self.square_button.setChecked(True)
        self.square_button.clicked.connect(lambda: self.change_wave_type("Square Wave"))
        button_layout.addWidget(self.square_button)

        # Triangle wave button
        self.triangle_button = QPushButton("Triangle Wave")
        self.triangle_button.setCheckable(True)
        self.triangle_button.clicked.connect(lambda: self.change_wave_type("Triangle Wave"))
        button_layout.addWidget(self.triangle_button)

        control_layout.addLayout(button_layout)

        # Apply styles to buttons
        self.update_button_styles()

        return control_widget

    def update_button_styles(self) -> None:
        """Update button styles to highlight the active waveform."""
        button_style_active = f"""
            QPushButton {{
                background-color: {self.colors.accent};
                color: white;
                font-weight: bold;
                padding: 10px;
                border: 2px solid {self.colors.panel_border};
                border-radius: 5px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: #1ea34a;
            }}
        """

        button_style_inactive = f"""
            QPushButton {{
                background-color: {self.colors.bg};
                color: {self.colors.text};
                font-weight: normal;
                padding: 10px;
                border: 2px solid {self.colors.grid};
                border-radius: 5px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {self.colors.panel};
                border-color: {self.colors.panel_border};
            }}
        """

        if self.wave_type == "Square Wave":
            self.square_button.setStyleSheet(button_style_active)
            self.triangle_button.setStyleSheet(button_style_inactive)
        else:
            self.triangle_button.setStyleSheet(button_style_active)
            self.square_button.setStyleSheet(button_style_inactive)

    def on_slider_change(self, value: int) -> None:
        """Handle slider value changes."""
        self.current_harmonics = value
        self.slider_label.setText(f"Harmonics (n): {value}")
        self.update_display()

    def change_wave_type(self, wave_type: str) -> None:
        """Switch the source waveform and refresh the plots."""
        self.wave_type = wave_type

        # Update button states
        if wave_type == "Square Wave":
            self.square_button.setChecked(True)
            self.triangle_button.setChecked(False)
        else:
            self.triangle_button.setChecked(True)
            self.square_button.setChecked(False)

        self.update_button_styles()
        self.update_display()

    def update_display(self) -> None:
        """Redraw the plots and informational panel."""
        n = self.current_harmonics

        # Clear axes
        self.canvas.ax_main.clear()
        self.canvas.ax_harmonics.clear()

        # Clear control panel texts
        for txt in self.canvas.ax_controls.texts[:]:
            txt.remove()

        # Configure axes appearance
        for ax in [self.canvas.ax_main, self.canvas.ax_harmonics]:
            ax.set_facecolor(self.colors.fig_bg)
            ax.grid(True, color=self.colors.grid, linestyle="--", linewidth=0.6, alpha=0.9)
            ax.tick_params(axis="both", colors=self.colors.text_muted, labelsize=11)
            for spine in ["left", "bottom"]:
                ax.spines[spine].set_color(self.colors.text_muted)
            for spine in ["right", "top"]:
                ax.spines[spine].set_visible(False)

        # Select waveform
        if self.wave_type == "Square Wave":
            original = square_wave(self.t)
            harmonic_fn = square_wave_harmonic
        else:
            original = triangle_wave(self.t)
            harmonic_fn = triangle_wave_harmonic

        approximation = fourier_series(self.t, n, self.wave_type)

        # Plot main comparison
        self.canvas.ax_main.set_xlim(0, 2)
        self.canvas.ax_main.set_ylim(-1.5, 1.5)
        self.canvas.ax_main.tick_params(axis="x", labelbottom=False)
        self.canvas.ax_main.set_ylabel("Amplitude", fontsize=13, color=self.colors.text)
        self.canvas.ax_main.plot(
            self.t, original, color=self.colors.original, lw=2.3, label="Original Wave"
        )
        self.canvas.ax_main.plot(
            self.t,
            approximation,
            color=self.colors.fourier,
            lw=2.5,
            label=f"Fourier Series (n={n})",
        )
        legend = self.canvas.ax_main.legend(loc="upper right", fontsize=11, fancybox=True, framealpha=0.7)
        legend.get_frame().set_facecolor(self.colors.panel)
        legend.get_frame().set_edgecolor(self.colors.panel_border)
        for text in legend.get_texts():
            text.set_color(self.colors.text)

        # Plot harmonics
        self.canvas.ax_harmonics.set_ylim(-1.4, 1.4)
        self.canvas.ax_harmonics.set_xlabel("Time (periods)", fontsize=13, color=self.colors.text)
        self.canvas.ax_harmonics.set_ylabel("Amplitude", fontsize=13, color=self.colors.text)

        colors = plt.cm.viridis(np.linspace(0, 1, n))
        for k in range(1, n + 1):
            harmonic = harmonic_fn(self.t, k)
            self.canvas.ax_harmonics.plot(self.t, harmonic, color=colors[k - 1], alpha=0.9, lw=1.3)

        # Update control panel
        self.canvas.ax_controls.text(
            0.5,
            0.95,
            "Control Panel",
            ha="center",
            va="top",
            fontsize=17,
            color=self.colors.text,
            weight="bold",
        )
        self.canvas.ax_controls.text(
            0.5,
            0.73,
            "Fourier Series Formula",
            ha="center",
            va="top",
            fontsize=13,
            color=self.colors.text_muted,
            weight="bold",
        )

        formula_main, expanded, properties = describe_series(n, self.wave_type)

        self.canvas.ax_controls.text(
            0.5,
            0.65,
            formula_main,
            ha="center",
            va="center",
            fontsize=11,
            color=self.colors.text,
        )
        self.canvas.ax_controls.text(
            0.5,
            0.55,
            expanded,
            ha="center",
            va="center",
            fontsize=8.5,
            color=self.colors.text,
        )
        self.canvas.ax_controls.text(
            0.5,
            0.45,
            properties,
            ha="center",
            va="center",
            fontsize=9,
            style="italic",
            color=self.colors.text_muted,
        )

        # Calculate and display error metrics
        mse = np.mean((original - approximation) ** 2)
        max_error = np.max(np.abs(original - approximation))
        info_text = (
            r"$\mathbf{{Analysis}}$"
            + "\n\n"
            + f"Wave Type: {self.wave_type}\n"
            + f"Harmonics: $n = {n}$\n\n"
            + r"$\mathbf{{Error~Metrics}}$"
            + "\n\n"
            + f"Mean Squared Error:\n${mse:.5f}$\n\n"
            + f"Max Absolute Error:\n${max_error:.4f}$"
        )

        self.canvas.ax_controls.text(
            0.5,
            0.23,
            info_text,
            ha="center",
            va="center",
            fontsize=11,
            color=self.colors.text,
            bbox=dict(
                boxstyle="round,pad=0.7",
                fc=self.colors.bg,
                ec=self.colors.panel_border,
                lw=2,
            ),
        )

        # Redraw canvas
        self.canvas.draw()

    def show(self) -> None:
        """Display the visualization window."""
        super().show()
