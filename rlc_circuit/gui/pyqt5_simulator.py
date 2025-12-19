"""
PyQt5-based interactive GUI controller for the RLC frequency response simulator.

Developed for the Signals and Systems (EE204T) course project under
Prof. Ameer Mulla by Duggimpudi Shreyas Reddy and Prathamesh Nerpagar.
"""

from __future__ import annotations

import sys
import numpy as np
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSlider,
    QGridLayout,
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec

from core.rlc_system import (
    RLCSystemParameters,
    analyze_system,
    frequency_response,
)
from plotting.visuals import display_system_info, plot_bode, plot_pole_zero


class RLCFrequencyResponseSimulator(QMainWindow):
    """PyQt5-based facade that wires together the model computations and plotting helpers."""

    def __init__(self) -> None:
        super().__init__()
        self.params = RLCSystemParameters()
        self._init_ui()
        self.update_plot()

    def _init_ui(self) -> None:
        """Initialize the PyQt5 user interface."""
        self.setWindowTitle("RLC Frequency Response Simulator")
        self.setGeometry(100, 100, 1600, 1000)

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Create matplotlib figure
        self.fig = Figure(figsize=(16, 10), dpi=100)
        self.fig.suptitle(
            "Second-Order System: Effect of Q on Frequency Response",
            fontsize=14,
            fontweight="bold",
        )

        # Create canvas
        self.canvas = FigureCanvas(self.fig)
        main_layout.addWidget(self.canvas)

        # Create grid for subplots
        grid = GridSpec(
            3,
            2,
            figure=self.fig,
            left=0.08,
            right=0.96,
            top=0.92,
            bottom=0.05,
            hspace=0.40,
            wspace=0.35,
        )

        self.ax_poles = self.fig.add_subplot(grid[0, 0])
        self.ax_info = self.fig.add_subplot(grid[0, 1])
        self.ax_mag = self.fig.add_subplot(grid[1, :])
        self.ax_phase = self.fig.add_subplot(grid[2, :])

        # Create control panel
        control_panel = self._create_control_panel()
        main_layout.addWidget(control_panel)

    def _create_control_panel(self) -> QWidget:
        """Create the control panel with sliders."""
        control_widget = QWidget()
        control_layout = QGridLayout(control_widget)
        control_layout.setSpacing(20)

        # Natural frequency slider
        omega_label = QLabel("ω₀ (Natural Freq):")
        omega_label.setStyleSheet("font-size: 12pt; font-weight: bold;")
        self.omega_value_label = QLabel(f"{self.params.omega_0:.1f} rad/s")
        self.omega_value_label.setStyleSheet("font-size: 12pt; color: blue;")
        self.omega_value_label.setMinimumWidth(100)

        self.omega_slider = QSlider(Qt.Horizontal)
        self.omega_slider.setMinimum(10)  # 1.0 * 10
        self.omega_slider.setMaximum(1000)  # 100.0 * 10
        self.omega_slider.setValue(int(self.params.omega_0 * 10))
        self.omega_slider.setTickPosition(QSlider.TicksBelow)
        self.omega_slider.setTickInterval(50)
        self.omega_slider.valueChanged.connect(self._update_omega)
        self.omega_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 8px;
                background: lightblue;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: steelblue;
                border: 1px solid #5c5c5c;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
        """)

        control_layout.addWidget(omega_label, 0, 0)
        control_layout.addWidget(self.omega_slider, 0, 1)
        control_layout.addWidget(self.omega_value_label, 0, 2)

        # Quality factor slider
        q_label = QLabel("Q (Quality Factor):")
        q_label.setStyleSheet("font-size: 12pt; font-weight: bold;")
        self.q_value_label = QLabel(f"{self.params.Q:.1f}")
        self.q_value_label.setStyleSheet("font-size: 12pt; color: blue;")
        self.q_value_label.setMinimumWidth(100)

        self.q_slider = QSlider(Qt.Horizontal)
        self.q_slider.setMinimum(1)  # 0.1 * 10
        self.q_slider.setMaximum(200)  # 20.0 * 10
        self.q_slider.setValue(int(self.params.Q * 10))
        self.q_slider.setTickPosition(QSlider.TicksBelow)
        self.q_slider.setTickInterval(10)
        self.q_slider.valueChanged.connect(self._update_q)
        self.q_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 8px;
                background: lightblue;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: steelblue;
                border: 1px solid #5c5c5c;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
        """)

        control_layout.addWidget(q_label, 1, 0)
        control_layout.addWidget(self.q_slider, 1, 1)
        control_layout.addWidget(self.q_value_label, 1, 2)

        # Set column stretch
        control_layout.setColumnStretch(1, 1)

        return control_widget

    def _update_omega(self, value: int) -> None:
        """Update natural frequency from slider."""
        omega = value / 10.0
        self.params.omega_0 = omega
        self.omega_value_label.setText(f"{omega:.1f} rad/s")
        self.update_plot()

    def _update_q(self, value: int) -> None:
        """Update quality factor from slider."""
        q = value / 10.0
        self.params.Q = q
        self.q_value_label.setText(f"{q:.1f}")
        self.update_plot()

    def update_plot(self) -> None:
        """Refresh every panel based on the current parameters."""
        characteristics = analyze_system(self.params)
        omega, response = frequency_response(characteristics.transfer_function)

        plot_pole_zero(self.ax_poles, characteristics.poles, self.params.omega_0)
        display_system_info(self.ax_info, self.params, characteristics)
        plot_bode(self.ax_mag, self.ax_phase, omega, response, self.params)

        self.canvas.draw()


def launch_simulator() -> None:
    """Entry point used by the CLI runner."""
    app = QApplication(sys.argv)
    simulator = RLCFrequencyResponseSimulator()
    simulator.show()
    sys.exit(app.exec_())
