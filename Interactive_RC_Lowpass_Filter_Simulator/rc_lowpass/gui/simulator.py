"""
Interactive plotting utilities for the RC Lowpass Filter simulator.

Developed for Signals and Systems (EE204T) under Prof. Ameer Mulla by
Duggimpudi Shreyas Reddy and Prathamesh Nerpagar.
"""

from __future__ import annotations

from typing import List

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.gridspec import GridSpec
from matplotlib.lines import Line2D
from matplotlib.widgets import Button, Slider

from ..config import settings
from ..core import signals


class RCFilterSimulator:
    """Interactive RC low-pass filter visualizer."""

    def __init__(self) -> None:
        self.RC = settings.DEFAULT_RC_SECONDS
        self.freq = settings.DEFAULT_FREQUENCY_HZ
        self.amplitude = settings.DEFAULT_AMPLITUDE_V

        self.time_offset = 0.0
        self.running = False
        self.updating = False

        self.stem_lines: List[Line2D] = []
        self.stem_markers: List[Line2D] = []

        self._setup_figure()
        self.update_simulation()

    def _setup_figure(self) -> None:
        """Create the interactive figure layout."""
        self.fig = plt.figure("RC Lowpass Filter Simulator", figsize=(18, 9))
        self.fig.patch.set_facecolor("#f5f5f5")

        grid = GridSpec(
            2,
            1,
            figure=self.fig,
            left=0.06,
            right=0.65,
            top=0.95,
            bottom=0.08,
            hspace=0.25,
            height_ratios=[1, 1.3],
        )

        self.ax_time = self.fig.add_subplot(grid[0])
        self.ax_time.set_facecolor("#ffffff")
        self.ax_time.grid(True, alpha=0.2, color="#cccccc", linestyle="-", linewidth=0.5)
        self.ax_time.set_xlabel("Time (s)", fontsize=10, color="#333")
        self.ax_time.set_ylabel("Voltage (V)", fontsize=10, color="#333")
        self.ax_time.set_title("Time Domain", fontweight="bold", fontsize=11, color="#1a1a1a", pad=10)
        self.ax_time.tick_params(colors="#333", labelsize=9)
        self.ax_time.set_ylim(-11, 11)

        self.ax_freq = self.fig.add_subplot(grid[1])
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

        right_x = 0.68
        slider_width = 0.27

        self.fig.text(right_x, 0.96, "Controls", fontsize=13, fontweight="bold", color="#1a1a1a")

        btn_width = 0.12
        btn_height = 0.04
        gap = 0.01

        ax_start = plt.axes([right_x, 0.90, btn_width, btn_height])
        ax_reset = plt.axes([right_x + btn_width + gap, 0.90, btn_width, btn_height])

        self.btn_start = Button(ax_start, "▶ Play", color="#3b82f6", hovercolor="#60a5fa")
        self.btn_reset = Button(ax_reset, "↻ Reset", color="#6b7280", hovercolor="#9ca3af")

        self.btn_start.on_clicked(self.toggle_animation)
        self.btn_reset.on_clicked(self.reset_simulation)

        self.freq_label = self.fig.text(right_x, 0.84, "Frequency: 100 Hz", fontsize=9, color="#333")
        freq_slider_axes = plt.axes([right_x, 0.81, slider_width, 0.022], facecolor="#e0e7ff")

        self.rc_label = self.fig.text(right_x, 0.76, "RC Time Constant: 1.00 ms", fontsize=9, color="#333")
        rc_slider_axes = plt.axes([right_x, 0.73, slider_width, 0.022], facecolor="#e0e7ff")

        self.amp_label = self.fig.text(right_x, 0.68, "Amplitude: 5.0 V", fontsize=9, color="#333")
        amp_slider_axes = plt.axes([right_x, 0.65, slider_width, 0.022], facecolor="#e0e7ff")

        self.slider_freq = Slider(
            freq_slider_axes,
            "",
            settings.FREQUENCY_RANGE_HZ[0],
            settings.FREQUENCY_RANGE_HZ[1],
            valinit=self.freq,
            valstep=1,
            color="#3b82f6",
        )
        self.slider_rc = Slider(
            rc_slider_axes,
            "",
            settings.RC_RANGE_MS[0],
            settings.RC_RANGE_MS[1],
            valinit=self.RC * 1000,
            valstep=0.01,
            color="#10b981",
        )
        self.slider_amp = Slider(
            amp_slider_axes,
            "",
            settings.AMPLITUDE_RANGE_V[0],
            settings.AMPLITUDE_RANGE_V[1],
            valinit=self.amplitude,
            valstep=0.1,
            color="#f59e0b",
        )

        self.slider_freq.on_changed(self.on_freq_change)
        self.slider_rc.on_changed(self.on_rc_change)
        self.slider_amp.on_changed(self.on_amp_change)

        self.status_text = self.fig.text(
            right_x,
            0.58,
            "",
            fontsize=9,
            color="#1a1a1a",
            family="monospace",
            verticalalignment="top",
            bbox=dict(boxstyle="round,pad=0.6", facecolor="#ffffff", edgecolor="#d1d5db", linewidth=1.5),
        )

        about_text = (
            "About\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "• Square waves contain\n"
            "  odd harmonics\n"
            "  (1f, 3f, 5f...)\n\n"
            "• RC filter attenuates\n"
            "  high frequencies\n\n"
            "• Red stems show\n"
            "  harmonic amplitudes\n\n"
            "• Blue curve shows\n"
            "  filter response\n\n"
            "• At low f:\n"
            "  output ≈ input\n\n"
            "• At high f:\n"
            "  output smoothed\n\n"
            f"{settings.COURSE_INFO}"
        )

        self.fig.text(
            right_x,
            0.40,
            about_text,
            fontsize=8,
            color="#1a1a1a",
            family="sans-serif",
            verticalalignment="top",
            bbox=dict(boxstyle="round,pad=0.6", facecolor="#dbeafe", edgecolor="#3b82f6", linewidth=1.5),
        )

    def on_freq_change(self, value: float) -> None:
        if not self.updating:
            self.freq = value
            self.update_simulation()

    def on_rc_change(self, value_ms: float) -> None:
        if not self.updating:
            self.RC = value_ms / 1000.0
            self.update_simulation()

    def on_amp_change(self, value: float) -> None:
        if not self.updating:
            self.amplitude = value
            self.update_simulation()

    def toggle_animation(self, _event) -> None:
        self.running = not self.running
        if self.running:
            self.btn_start.label.set_text("|| Pause")
            self.btn_start.ax.set_facecolor("#10b981")
        else:
            self.btn_start.label.set_text("▶ Play")
            self.btn_start.ax.set_facecolor("#3b82f6")
        self.fig.canvas.draw_idle()

    def reset_simulation(self, _event) -> None:
        self.time_offset = 0.0
        self.running = False
        self.btn_start.label.set_text("▶ Play")
        self.btn_start.ax.set_facecolor("#3b82f6")

        self.updating = True
        self.slider_freq.eventson = False
        self.slider_rc.eventson = False
        self.slider_amp.eventson = False

        self.slider_freq.set_val(settings.DEFAULT_FREQUENCY_HZ)
        self.slider_rc.set_val(settings.DEFAULT_RC_SECONDS * 1000.0)
        self.slider_amp.set_val(settings.DEFAULT_AMPLITUDE_V)

        self.freq = settings.DEFAULT_FREQUENCY_HZ
        self.RC = settings.DEFAULT_RC_SECONDS
        self.amplitude = settings.DEFAULT_AMPLITUDE_V

        self.slider_freq.eventson = True
        self.slider_rc.eventson = True
        self.slider_amp.eventson = True
        self.updating = False

        self.update_simulation()

    def _clear_stems(self) -> None:
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
        if self.updating:
            return

        self.updating = True

        self.freq_label.set_text(f"Frequency: {self.freq:.0f} Hz")
        self.rc_label.set_text(f"RC Time Constant: {self.RC * 1000:.2f} ms")
        self.amp_label.set_text(f"Amplitude: {self.amplitude:.1f} V")

        fc = signals.cutoff_frequency(self.RC)
        ratio = self.freq / fc if fc else 0.0

        time_axis = signals.time_vector(self.time_offset, settings.TIME_WINDOW_SECONDS, settings.TIME_SAMPLES)
        time_relative = time_axis - time_axis[0]

        input_signal = signals.square_wave(self.amplitude, self.freq, time_axis)
        output_signal = signals.simulate_rc_output(time_relative, input_signal, self.RC)

        self.line_input.set_data(time_relative, input_signal)
        self.line_output.set_data(time_relative, output_signal)
        self.ax_time.set_xlim(0, settings.TIME_WINDOW_SECONDS)

        bode_freq, bode_mag_db = signals.bode_response(self.RC)
        self.line_bode.set_data(bode_freq, bode_mag_db)

        harmonic_freqs, harmonic_mag_db = signals.square_wave_harmonics(self.freq, self.amplitude)
        valid = harmonic_freqs <= self.ax_freq.get_xlim()[1]
        harmonic_freqs = harmonic_freqs[valid]
        harmonic_mag_db = harmonic_mag_db[valid]

        self._clear_stems()
        for fx, mag_db in zip(harmonic_freqs, harmonic_mag_db):
            stem_line = self.ax_freq.plot([fx, fx], [-80, mag_db], "r-", linewidth=2, alpha=0.8)[0]
            stem_marker = self.ax_freq.plot(fx, mag_db, "ro", markersize=6, alpha=0.9)[0]
            self.stem_lines.append(stem_line)
            self.stem_markers.append(stem_marker)

        self.cutoff_line.set_xdata([fc, fc])

        self._update_status(fc, ratio)

        self.fig.canvas.draw_idle()
        self.updating = False

    def _update_status(self, cutoff_frequency_hz: float, ratio: float) -> None:
        if ratio < settings.STATUS_THRESHOLDS["passing"]:
            status = "PASSING"
            status_color = "#10b981"
            desc = "Input < Cutoff"
        elif ratio < settings.STATUS_THRESHOLDS["transitioning"]:
            status = "TRANSITIONING"
            status_color = "#f59e0b"
            desc = "Input ≈ Cutoff"
        else:
            status = "FILTERING"
            status_color = "#ef4444"
            desc = "Input > Cutoff"

        status_str = (
            "Status\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"Cutoff fc: {cutoff_frequency_hz:.2f} Hz\n"
            f"Input f:   {self.freq:.0f} Hz\n"
            f"Ratio f/fc: {ratio:.2f}\n"
            f"RC const:  {self.RC * 1000:.2f} ms\n\n"
            f"{status}\n"
            f"{desc}"
        )

        self.status_text.set_text(status_str)
        bbox = self.status_text.get_bbox_patch()
        bbox.set_edgecolor(status_color)
        bbox.set_linewidth(2.5)

    def animate(self, _frame):
        if self.running:
            self.time_offset += 0.005
            self.update_simulation()
        return []

    def run(self) -> None:
        self.anim = FuncAnimation(self.fig, self.animate, interval=50, blit=False, cache_frame_data=False)
        plt.show()
