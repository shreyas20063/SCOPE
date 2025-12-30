import traceback
import numpy as np
import scipy.signal as signal
from typing import List, Optional
from PyQt5 import QtCore, QtWidgets
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from .base import DemoWindowBase, SOUNDDEVICE_AVAILABLE
from gui.styles import (COLORS, make_label, style_spinbox, style_button)
from utils import load_and_validate_audio, configure_axes
from assets import AUDIO_SAMPLE_PATH

class DemoWindowFDM(DemoWindowBase):
    def __init__(self, parent: Optional[QtWidgets.QWidget], title: str):
        super().__init__(parent, title)
        self.num_channels = 3
        self.selected_channel = 1
        self.channel_spacing_hz = 10_000
        self.current_multiplexed = np.zeros(1, dtype=np.float64)
        self.current_demodulated = np.zeros(1, dtype=np.float64)
        self.channel_freqs: List[int] = []

        self._build_ui()
        self._load_audio()
        self.schedule_update()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        plot_frame = QtWidgets.QFrame()
        plot_layout = QtWidgets.QVBoxLayout(plot_frame)
        self.figure = Figure(figsize=(10.5, 6.5), dpi=90)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        plot_layout.addWidget(self.canvas)
        plot_layout.addWidget(self.toolbar)
        layout.addWidget(plot_frame, 1)

        layout.addSpacing(8)

        control_frame = QtWidgets.QFrame()
        control_frame.setStyleSheet(
            "background-color:#EEF2FF; border:1px solid #CBD5F5; border-radius:16px;"
        )
        controls = QtWidgets.QGridLayout(control_frame)
        controls.setContentsMargins(18, 16, 18, 16)
        controls.setHorizontalSpacing(20)
        controls.setVerticalSpacing(12)
        controls.setColumnStretch(3, 1)

        controls.addWidget(make_label("Channels", bold=True), 0, 0)
        self.channel_spin = QtWidgets.QSpinBox()
        self.channel_spin.setRange(1, 5)
        self.channel_spin.setValue(self.num_channels)
        self.channel_spin.valueChanged.connect(self._on_channel_count_changed)
        style_spinbox(self.channel_spin)
        controls.addWidget(self.channel_spin, 0, 1)

        controls.addWidget(make_label("Demodulate Channel", bold=True), 0, 2)
        self.selection_spin = QtWidgets.QSpinBox()
        self.selection_spin.setRange(1, self.num_channels)
        self.selection_spin.setValue(self.selected_channel)
        self.selection_spin.valueChanged.connect(self._on_selected_channel_changed)
        style_spinbox(self.selection_spin)
        controls.addWidget(self.selection_spin, 0, 3)

        controls.addWidget(make_label("Spacing (kHz)", bold=True), 1, 0)
        self.spacing_spin = QtWidgets.QSpinBox()
        self.spacing_spin.setRange(5, 30)
        self.spacing_spin.setValue(self.channel_spacing_hz // 1000)
        self.spacing_spin.valueChanged.connect(self._on_spacing_changed)
        style_spinbox(self.spacing_spin)
        controls.addWidget(self.spacing_spin, 1, 1)

        btn_layout = QtWidgets.QHBoxLayout()
        self.btn_play_mux = QtWidgets.QPushButton("Play Multiplexed")
        self.btn_play_mux.clicked.connect(lambda: self._play_buffer(self.current_multiplexed, gain=0.35))
        self.btn_play_demod = QtWidgets.QPushButton("Play Demodulated")
        self.btn_play_demod.clicked.connect(lambda: self._play_buffer(self.current_demodulated, gain=1.0))
        for btn, color in (
            (self.btn_play_mux, COLORS["warning"]),
            (self.btn_play_demod, COLORS["accent"]),
        ):
            style_button(btn, color)
            if not SOUNDDEVICE_AVAILABLE:
                btn.setEnabled(False)
                btn.setToolTip("Install the 'sounddevice' package for playback.")
            btn_layout.addWidget(btn)
        controls.addLayout(btn_layout, 1, 2, 1, 2)

        layout.addWidget(control_frame)

    def _load_audio(self) -> None:
        self.original_sr, audio = load_and_validate_audio(AUDIO_SAMPLE_PATH)
        duration = min(3.0, len(audio) / self.original_sr if self.original_sr > 0 else 3.0)
        count = int(duration * self.original_sr) if self.original_sr > 0 else 0
        self.audio = audio[:count]
        self.time = (
            np.linspace(0, duration, len(self.audio), dtype=np.float64)
            if self.audio.size
            else np.zeros(1, dtype=np.float64)
        )
        self.current_multiplexed = np.zeros_like(self.audio)
        self.current_demodulated = np.zeros_like(self.audio)

    def _on_channel_count_changed(self, value: int) -> None:
        self.num_channels = value
        self.selection_spin.setMaximum(self.num_channels)
        if self.selected_channel > self.num_channels:
            self.selected_channel = self.num_channels
            self.selection_spin.setValue(self.selected_channel)
        self.schedule_update()

    def _on_selected_channel_changed(self, value: int) -> None:
        self.selected_channel = value
        self.schedule_update()

    def _on_spacing_changed(self, value: int) -> None:
        self.channel_spacing_hz = int(value) * 1000
        self.schedule_update()

    def update_plot(self) -> None:
        if self._is_updating or self.audio.size < 2:
            return
        self._is_updating = True
        try:
            base_freq = 5_000
            channels = []
            self.channel_freqs = []
            for idx in range(self.num_channels):
                shift_samples = int(idx * len(self.audio) / max(self.num_channels * 2, 1))
                shifted = np.roll(self.audio, shift_samples)
                shifted = shifted / (np.max(np.abs(shifted)) + 1e-10)
                fc = base_freq + idx * self.channel_spacing_hz
                carrier = np.cos(2 * np.pi * fc * self.time)
                modulated = shifted * carrier
                channels.append(modulated)
                self.channel_freqs.append(fc)
            if not channels:
                self.current_multiplexed = np.zeros_like(self.audio)
            else:
                mux = np.sum(channels, axis=0) / max(self.num_channels, 1)
                self.current_multiplexed = mux

            fc_sel = self.channel_freqs[self.selected_channel - 1]
            carrier_sel = np.cos(2 * np.pi * fc_sel * self.time)
            product = self.current_multiplexed * carrier_sel
            nyq = self.original_sr / 2.0
            cutoff = min(5_000, nyq * 0.9) if nyq > 0 else 2_000
            cutoff = max(500.0, cutoff)
            if nyq > 0:
                wn = min(0.99, cutoff / nyq)
                b, a = signal.butter(6, wn, btype="low")
                demod = signal.filtfilt(b, a, product) * 2
            else:
                demod = product
            self.current_demodulated = demod / (np.max(np.abs(demod)) + 1e-10)

            self.figure.clf()
            axes = self.figure.subplots(3, 1)
            configure_axes(axes)
            length = len(self.audio)
            seg = slice(length // 5, min(length // 5 + 2000, length))
            t_seg = self.time[seg]

            axes[0].plot(t_seg, self.current_multiplexed[seg], color=COLORS["danger"], linewidth=1.0)
            axes[0].set_title(f"Multiplexed Signal ({self.num_channels} channels)")
            axes[0].set_ylabel("Amplitude")

            if len(self.current_multiplexed) > 1 and self.original_sr > 0:
                freqs, psd = signal.welch(
                    self.current_multiplexed, self.original_sr, nperseg=min(4096, len(self.current_multiplexed))
                )
                psd_db = 10 * np.log10(psd + 1e-12)
                axes[1].plot(freqs / 1000, psd_db, color=COLORS["warning"], linewidth=1.3)
                for idx, fc in enumerate(self.channel_freqs):
                    color = COLORS["accent"] if (idx + 1) == self.selected_channel else COLORS["accent_dark"]
                    axes[1].axvline(fc / 1000, color=color, linestyle="--", linewidth=1.1, alpha=0.75)
                    bw = 5_000
                    axes[1].axvspan(
                        (fc - bw) / 1000,
                        (fc + bw) / 1000,
                        alpha=0.08 if (idx + 1) != self.selected_channel else 0.18,
                        color=color,
                    )
                max_freq = max(self.channel_freqs) + self.channel_spacing_hz if self.channel_freqs else 0
                axes[1].set_xlim(0, min(freqs[-1] / 1000, max_freq / 1000 * 1.2 if max_freq else 40))
                axes[1].set_title(f"Spectrum (spacing {self.channel_spacing_hz/1000:.0f} kHz)")
                axes[1].set_ylabel("Power (dB)")
                axes[1].set_xlabel("Frequency (kHz)")
            else:
                axes[1].set_title("Spectrum unavailable")
                axes[1].set_xlabel("Frequency (kHz)")

            axes[2].plot(t_seg, self.current_demodulated[seg], color=COLORS["success"], linewidth=1.2)
            axes[2].set_title(f"Demodulated Channel {self.selected_channel} (fc={fc_sel/1000:.1f} kHz)")
            axes[2].set_ylabel("Amplitude")
            axes[2].set_xlabel("Time (s)")

            self.figure.tight_layout(rect=[0, 0.02, 1, 0.98])
            self.canvas.draw_idle()
        except Exception as exc:
            print(f"FDM update error: {exc}")
            traceback.print_exc()
        finally:
            self._is_updating = False