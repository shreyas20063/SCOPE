"""
Interactive PyQt5-based GUI for the RC Lowpass Filter simulator.

Developed for Signals and Systems (EE204T) under Prof. Ameer Mulla by
Duggimpudi Shreyas Reddy and Prathamesh Nerpagar.
"""

from __future__ import annotations

from typing import List

import numpy as np
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSlider,
    QPushButton,
    QGroupBox,
    QTextEdit,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

import matplotlib
matplotlib.use('Qt5Agg')

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.lines import Line2D

from core import signals
from utils import constants


class RCFilterSimulator(QMainWindow):
    """Interactive RC low-pass filter visualizer with PyQt5 interface."""

    def __init__(self) -> None:
        super().__init__()

        # Initialize parameters
        self.RC = constants.DEFAULT_RC_SECONDS
        self.freq = constants.DEFAULT_FREQUENCY_HZ
        self.amplitude = constants.DEFAULT_AMPLITUDE_V

        self.time_offset = 0.0
        self.running = False
        self.updating = False

        self.stem_lines: List[Line2D] = []
        self.stem_markers: List[Line2D] = []

        # Setup UI
        self.setWindowTitle("RC Lowpass Filter Simulator")
        self.setGeometry(100, 100, 1600, 900)

        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # Create matplotlib figure
        self._setup_figure()

        # Create canvas
        self.canvas = FigureCanvas(self.fig)
        main_layout.addWidget(self.canvas, stretch=7)

        # Create control panel
        control_panel = self._create_control_panel()
        main_layout.addWidget(control_panel, stretch=3)

        # Setup timer for animation
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate)
        self.timer.setInterval(50)  # 50ms interval

        # Initial update
        self.update_simulation()

    def _setup_figure(self) -> None:
        """Create the matplotlib figure with plots."""
        self.fig = Figure(figsize=(12, 9), facecolor='#f5f5f5')

        # Create subplots
        self.ax_time = self.fig.add_subplot(2, 1, 1)
        self.ax_freq = self.fig.add_subplot(2, 1, 2)

        # Style time domain plot
        self.ax_time.set_facecolor("#ffffff")
        self.ax_time.grid(True, alpha=0.2, color="#cccccc", linestyle="-", linewidth=0.5)
        self.ax_time.set_xlabel("Time (s)", fontsize=10, color="#333")
        self.ax_time.set_ylabel("Voltage (V)", fontsize=10, color="#333")
        self.ax_time.set_title("Time Domain", fontweight="bold", fontsize=11, color="#1a1a1a", pad=10)
        self.ax_time.tick_params(colors="#333", labelsize=9)
        self.ax_time.set_ylim(-11, 11)

        # Style frequency domain plot
        self.ax_freq.set_facecolor("#ffffff")
        self.ax_freq.grid(
            True,
            alpha=0.2,
            color="#cccccc",
            linestyle="-",
            linewidth=0.5,
            which="both",
        )
        self.ax_freq.set_xlabel("Frequency (Hz)", fontsize=10, color="#333")
        self.ax_freq.set_ylabel("Magnitude (dB)", fontsize=10, color="#333")
        self.ax_freq.set_title(
            "Frequency Domain (Bode Plot)", fontweight="bold", fontsize=11, color="#1a1a1a", pad=10
        )
        self.ax_freq.set_xscale("log")
        self.ax_freq.set_xlim(0.1, 100000)
        self.ax_freq.set_ylim(-80, 30)
        self.ax_freq.tick_params(colors="#333", labelsize=9)

        # Initialize plot lines
        (self.line_input,) = self.ax_time.plot([], [], "b-", linewidth=2.5, label="Input (Blue)", alpha=0.8)
        (self.line_output,) = self.ax_time.plot([], [], "r-", linewidth=2.8, label="Output (Red)")
        self.ax_time.legend(loc="upper right", fontsize=9, framealpha=0.95, edgecolor="#ccc")

        (self.line_bode,) = self.ax_freq.plot([], [], "b-", linewidth=2.5, alpha=0.9)
        self.cutoff_line = self.ax_freq.axvline(0, color="#10b981", linestyle="--", linewidth=2.5, alpha=0.7)

        legend_elements = [
            Line2D([0], [0], color="b", linewidth=2.5, label="Blue: Filter Response"),
            Line2D([0], [0], color="r", marker="o", linewidth=2, markersize=6, label="Red: Square Wave Harmonics"),
            Line2D([0], [0], color="#10b981", linestyle="--", linewidth=2.5, label="Green: Cutoff fc"),
        ]
        self.ax_freq.legend(handles=legend_elements, loc="upper right", fontsize=8.5, framealpha=0.95, edgecolor="#ccc")

        self.fig.tight_layout(pad=2.0)

    def _create_control_panel(self) -> QWidget:
        """Create the control panel with sliders and buttons."""
        panel = QWidget()
        panel.setStyleSheet("background-color: #f5f5f5;")
        layout = QVBoxLayout(panel)

        # Title
        title = QLabel("Controls")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setStyleSheet("color: #1a1a1a; background-color: transparent;")
        layout.addWidget(title)

        # Buttons
        button_layout = QHBoxLayout()

        self.btn_play = QPushButton("Play")
        self.btn_play.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                padding: 8px 16px;
                font-size: 11px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #60a5fa;
            }
        """)
        self.btn_play.clicked.connect(self.toggle_animation)
        button_layout.addWidget(self.btn_play)

        self.btn_reset = QPushButton("Reset")
        self.btn_reset.setStyleSheet("""
            QPushButton {
                background-color: #6b7280;
                color: white;
                border: none;
                padding: 8px 16px;
                font-size: 11px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #9ca3af;
            }
        """)
        self.btn_reset.clicked.connect(self.reset_simulation)
        button_layout.addWidget(self.btn_reset)

        layout.addLayout(button_layout)
        layout.addSpacing(10)

        # Frequency slider
        freq_group = QGroupBox()
        freq_group.setStyleSheet("QGroupBox { border: none; background-color: transparent; }")
        freq_layout = QVBoxLayout(freq_group)

        self.freq_label = QLabel(f"Frequency: {self.freq:.0f} Hz")
        self.freq_label.setStyleSheet("color: #333; font-size: 10px; background-color: transparent;")
        freq_layout.addWidget(self.freq_label)

        self.slider_freq = QSlider(Qt.Horizontal)
        self.slider_freq.setMinimum(int(constants.FREQUENCY_RANGE_HZ[0]))
        self.slider_freq.setMaximum(int(constants.FREQUENCY_RANGE_HZ[1]))
        self.slider_freq.setValue(int(self.freq))
        self.slider_freq.setTickPosition(QSlider.TicksBelow)
        self.slider_freq.setTickInterval(50)
        self.slider_freq.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #bbb;
                background: #e0e7ff;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #3b82f6;
                border: 1px solid #3b82f6;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
        """)
        self.slider_freq.valueChanged.connect(self.on_freq_change)
        freq_layout.addWidget(self.slider_freq)

        layout.addWidget(freq_group)

        # RC slider
        rc_group = QGroupBox()
        rc_group.setStyleSheet("QGroupBox { border: none; background-color: transparent; }")
        rc_layout = QVBoxLayout(rc_group)

        self.rc_label = QLabel(f"RC Time Constant: {self.RC * 1000:.2f} ms")
        self.rc_label.setStyleSheet("color: #333; font-size: 10px; background-color: transparent;")
        rc_layout.addWidget(self.rc_label)

        self.slider_rc = QSlider(Qt.Horizontal)
        self.slider_rc.setMinimum(int(constants.RC_RANGE_MS[0] * 100))
        self.slider_rc.setMaximum(int(constants.RC_RANGE_MS[1] * 100))
        self.slider_rc.setValue(int(self.RC * 1000 * 100))
        self.slider_rc.setTickPosition(QSlider.TicksBelow)
        self.slider_rc.setTickInterval(100)
        self.slider_rc.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #bbb;
                background: #e0e7ff;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #10b981;
                border: 1px solid #10b981;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
        """)
        self.slider_rc.valueChanged.connect(self.on_rc_change)
        rc_layout.addWidget(self.slider_rc)

        layout.addWidget(rc_group)

        # Amplitude slider
        amp_group = QGroupBox()
        amp_group.setStyleSheet("QGroupBox { border: none; background-color: transparent; }")
        amp_layout = QVBoxLayout(amp_group)

        self.amp_label = QLabel(f"Amplitude: {self.amplitude:.1f} V")
        self.amp_label.setStyleSheet("color: #333; font-size: 10px; background-color: transparent;")
        amp_layout.addWidget(self.amp_label)

        self.slider_amp = QSlider(Qt.Horizontal)
        self.slider_amp.setMinimum(int(constants.AMPLITUDE_RANGE_V[0] * 10))
        self.slider_amp.setMaximum(int(constants.AMPLITUDE_RANGE_V[1] * 10))
        self.slider_amp.setValue(int(self.amplitude * 10))
        self.slider_amp.setTickPosition(QSlider.TicksBelow)
        self.slider_amp.setTickInterval(10)
        self.slider_amp.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #bbb;
                background: #e0e7ff;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #f59e0b;
                border: 1px solid #f59e0b;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
        """)
        self.slider_amp.valueChanged.connect(self.on_amp_change)
        amp_layout.addWidget(self.slider_amp)

        layout.addWidget(amp_group)
        layout.addSpacing(10)

        # Status display
        status_group = QGroupBox("Status")
        status_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 11px;
                color: #1a1a1a;
                border: 2px solid #10b981;
                border-radius: 6px;
                margin-top: 6px;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        status_layout = QVBoxLayout(status_group)

        self.status_text = QLabel()
        self.status_text.setStyleSheet("color: #1a1a1a; font-family: monospace; font-size: 9px; background-color: transparent;")
        self.status_text.setWordWrap(True)
        status_layout.addWidget(self.status_text)

        layout.addWidget(status_group)

        # About section
        about_group = QGroupBox("About")
        about_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 11px;
                color: #1a1a1a;
                border: 2px solid #3b82f6;
                border-radius: 6px;
                margin-top: 6px;
                padding-top: 10px;
                background-color: #dbeafe;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        about_layout = QVBoxLayout(about_group)

        about_text = QTextEdit()
        about_text.setReadOnly(True)
        about_text.setStyleSheet("background-color: transparent; border: none; font-size: 8px; color: #1a1a1a;")
        about_text.setHtml(
            "<p><b>Square waves contain odd harmonics</b> (1f, 3f, 5f...)</p>"
            "<p><b>RC filter attenuates high frequencies</b></p>"
            "<p><b>Red stems</b> show harmonic amplitudes</p>"
            "<p><b>Blue curve</b> shows filter response</p>"
            "<p><b>At low f:</b> output ≈ input</p>"
            "<p><b>At high f:</b> output smoothed</p>"
            f"<p style='margin-top: 10px;'><i>{constants.COURSE_INFO}</i></p>"
        )
        about_layout.addWidget(about_text)

        layout.addWidget(about_group)
        layout.addStretch()

        return panel

    def on_freq_change(self, value: int) -> None:
        """Handle frequency slider change."""
        if not self.updating:
            self.freq = float(value)
            self.update_simulation()

    def on_rc_change(self, value: int) -> None:
        """Handle RC slider change."""
        if not self.updating:
            self.RC = value / 100000.0  # Convert from slider value to seconds
            self.update_simulation()

    def on_amp_change(self, value: int) -> None:
        """Handle amplitude slider change."""
        if not self.updating:
            self.amplitude = value / 10.0
            self.update_simulation()

    def toggle_animation(self) -> None:
        """Toggle animation play/pause."""
        self.running = not self.running
        if self.running:
            self.btn_play.setText("Pause")
            self.btn_play.setStyleSheet("""
                QPushButton {
                    background-color: #10b981;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    font-size: 11px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #34d399;
                }
            """)
            self.timer.start()
        else:
            self.btn_play.setText("Play")
            self.btn_play.setStyleSheet("""
                QPushButton {
                    background-color: #3b82f6;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    font-size: 11px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #60a5fa;
                }
            """)
            self.timer.stop()

    def reset_simulation(self) -> None:
        """Reset simulation to default values."""
        self.time_offset = 0.0
        self.running = False
        self.timer.stop()

        self.btn_play.setText("Play")
        self.btn_play.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                padding: 8px 16px;
                font-size: 11px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #60a5fa;
            }
        """)

        self.updating = True

        self.slider_freq.setValue(int(constants.DEFAULT_FREQUENCY_HZ))
        self.slider_rc.setValue(int(constants.DEFAULT_RC_SECONDS * 100000))
        self.slider_amp.setValue(int(constants.DEFAULT_AMPLITUDE_V * 10))

        self.freq = constants.DEFAULT_FREQUENCY_HZ
        self.RC = constants.DEFAULT_RC_SECONDS
        self.amplitude = constants.DEFAULT_AMPLITUDE_V

        self.updating = False
        self.update_simulation()

    def _clear_stems(self) -> None:
        """Clear stem plot lines."""
        for line in self.stem_lines:
            try:
                line.remove()
            except Exception:
                pass
        for marker in self.stem_markers:
            try:
                marker.remove()
            except Exception:
                pass
        self.stem_lines.clear()
        self.stem_markers.clear()

    def update_simulation(self) -> None:
        """Update the simulation plots based on current parameters."""
        if self.updating:
            return

        self.updating = True

        # Update labels
        self.freq_label.setText(f"Frequency: {self.freq:.0f} Hz")
        self.rc_label.setText(f"RC Time Constant: {self.RC * 1000:.2f} ms")
        self.amp_label.setText(f"Amplitude: {self.amplitude:.1f} V")

        fc = signals.cutoff_frequency(self.RC)
        ratio = self.freq / fc if fc else 0.0

        # Time domain calculations
        time_axis = signals.time_vector(self.time_offset, constants.TIME_WINDOW_SECONDS, constants.TIME_SAMPLES)
        time_relative = time_axis - time_axis[0]

        input_signal = signals.square_wave(self.amplitude, self.freq, time_axis)
        output_signal = signals.simulate_rc_output(time_relative, input_signal, self.RC)

        self.line_input.set_data(time_relative, input_signal)
        self.line_output.set_data(time_relative, output_signal)
        self.ax_time.set_xlim(0, constants.TIME_WINDOW_SECONDS)

        # Frequency domain calculations
        bode_freq, bode_mag_db = signals.bode_response(self.RC)
        self.line_bode.set_data(bode_freq, bode_mag_db)

        harmonic_freqs, harmonic_mag_db = signals.square_wave_harmonics(self.freq, self.amplitude)
        valid = harmonic_freqs <= self.ax_freq.get_xlim()[1]
        harmonic_freqs = harmonic_freqs[valid]
        harmonic_mag_db = harmonic_mag_db[valid]

        # Clear and redraw stems
        self._clear_stems()
        for fx, mag_db in zip(harmonic_freqs, harmonic_mag_db):
            stem_line = self.ax_freq.plot([fx, fx], [-80, mag_db], "r-", linewidth=2, alpha=0.8)[0]
            stem_marker = self.ax_freq.plot(fx, mag_db, "ro", markersize=6, alpha=0.9)[0]
            self.stem_lines.append(stem_line)
            self.stem_markers.append(stem_marker)

        self.cutoff_line.set_xdata([fc, fc])

        # Update status
        self._update_status(fc, ratio)

        self.canvas.draw()
        self.updating = False

    def _update_status(self, cutoff_frequency_hz: float, ratio: float) -> None:
        """Update the status display."""
        if ratio < constants.STATUS_THRESHOLDS["passing"]:
            status = "PASSING"
            status_color = "#10b981"
            desc = "Input < Cutoff"
        elif ratio < constants.STATUS_THRESHOLDS["transitioning"]:
            status = "TRANSITIONING"
            status_color = "#f59e0b"
            desc = "Input ≈ Cutoff"
        else:
            status = "FILTERING"
            status_color = "#ef4444"
            desc = "Input > Cutoff"

        status_str = (
            f"Cutoff fc: {cutoff_frequency_hz:.2f} Hz\n"
            f"Input f:   {self.freq:.0f} Hz\n"
            f"Ratio f/fc: {ratio:.2f}\n"
            f"RC const:  {self.RC * 1000:.2f} ms\n\n"
            f"<b>{status}</b>\n"
            f"{desc}"
        )

        self.status_text.setText(status_str)

        # Update status group box border color
        status_group = self.status_text.parent()
        status_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                font-size: 11px;
                color: #1a1a1a;
                border: 2px solid {status_color};
                border-radius: 6px;
                margin-top: 6px;
                padding-top: 10px;
                background-color: white;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }}
        """)

    def animate(self) -> None:
        """Animation update callback."""
        if self.running:
            self.time_offset += 0.005
            self.update_simulation()

    def run(self) -> None:
        """Show the window."""
        self.show()
