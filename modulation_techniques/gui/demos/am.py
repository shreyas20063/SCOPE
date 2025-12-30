from typing import Optional
import numpy as np
import scipy.signal as signal
from PyQt5 import QtCore, QtWidgets
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from .base import DemoWindowBase, SOUNDDEVICE_AVAILABLE
from gui.styles import (COLORS, VALUE_LABEL_STYLE, make_label, style_slider, style_spinbox, style_button)
from utils import load_and_validate_audio, configure_axes
from assets import AUDIO_SAMPLE_PATH

class DemoWindowAM(DemoWindowBase):
    def __init__(self, parent: Optional[QtWidgets.QWidget], title: str):
        super().__init__(parent, title)
        self.fc_hz = 5_000
        self.carrier_dc = 1.2
        self.mode = "DSB-SC"
        self.current_modulated = np.zeros(1, dtype=np.float64)
        self.last_demod = np.zeros(1, dtype=np.float64)

        self._build_ui()
        self._load_audio()
        self.schedule_update()

    def _build_ui(self) -> None:
        main_layout = QtWidgets.QVBoxLayout(self)
        plot_frame = QtWidgets.QFrame()
        plot_layout = QtWidgets.QVBoxLayout(plot_frame)
        self.figure = Figure(figsize=(10.5, 6.5), dpi=90)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        plot_layout.addWidget(self.canvas)
        plot_layout.addWidget(self.toolbar)
        main_layout.addWidget(plot_frame, 1)

        main_layout.addSpacing(8)

        control_frame = QtWidgets.QFrame()
        control_frame.setStyleSheet(
            "background-color:#EEF2FF; border:1px solid #CBD5F5; border-radius:16px;"
        )
        controls = QtWidgets.QGridLayout(control_frame)
        controls.setContentsMargins(18, 16, 18, 16)
        controls.setHorizontalSpacing(20)
        controls.setVerticalSpacing(12)
        controls.setColumnStretch(1, 1)

        controls.addWidget(make_label("Carrier Frequency (kHz)", bold=True), 0, 0)
        self.fc_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.fc_slider.setRange(1, 20)
        self.fc_slider.setValue(5)
        self.fc_slider.valueChanged.connect(self._on_fc_changed)
        style_slider(self.fc_slider)
        self.fc_value_lbl = QtWidgets.QLabel("5 kHz")
        self.fc_value_lbl.setStyleSheet(VALUE_LABEL_STYLE)
        controls.addWidget(self.fc_slider, 0, 1)
        controls.addWidget(self.fc_value_lbl, 0, 2, alignment=QtCore.Qt.AlignLeft)

        controls.addWidget(make_label("Carrier DC Offset", bold=True), 1, 0)
        self.dc_spin = QtWidgets.QDoubleSpinBox()
        self.dc_spin.setRange(0.0, 2.0)
        self.dc_spin.setSingleStep(0.1)
        self.dc_spin.setDecimals(2)
        self.dc_spin.setValue(1.2)
        self.dc_spin.valueChanged.connect(self._on_dc_changed)
        style_spinbox(self.dc_spin)
        self.dc_value_lbl = QtWidgets.QLabel("1.20")
        self.dc_value_lbl.setStyleSheet(VALUE_LABEL_STYLE)
        controls.addWidget(self.dc_spin, 1, 1)
        controls.addWidget(self.dc_value_lbl, 1, 2, alignment=QtCore.Qt.AlignLeft)

        mode_box = QtWidgets.QGroupBox("Mode")
        mode_box.setStyleSheet(
            "QGroupBox {border:1px solid #CBD5F5; border-radius:10px; margin-top:6px;"
            "font-weight:600; color:#0F172A; padding-top:12px;}"
            "QGroupBox::title {subcontrol-origin: margin; left:14px; padding:0 4px;}"
        )
        mode_layout = QtWidgets.QHBoxLayout(mode_box)
        mode_layout.setContentsMargins(10, 4, 10, 6)
        mode_layout.setSpacing(12)
        self.mode_group = QtWidgets.QButtonGroup(self)
        for label in ("DSB-SC", "AM+Carrier", "Envelope"):
            button = QtWidgets.QRadioButton(label)
            if label == self.mode:
                button.setChecked(True)
            self.mode_group.addButton(button)
            mode_layout.addWidget(button)
            button.setStyleSheet("color:#0F172A; font-weight:500;")
        self.mode_group.buttonClicked.connect(self._on_mode_changed)
        controls.addWidget(mode_box, 0, 3, 2, 1)

        btn_layout = QtWidgets.QHBoxLayout()
        self.btn_play_original = QtWidgets.QPushButton("Play Original")
        self.btn_play_original.clicked.connect(self.play_original)
        self.btn_play_modulated = QtWidgets.QPushButton("Play Modulated")
        self.btn_play_modulated.clicked.connect(self.play_modulated)
        self.btn_play_recovered = QtWidgets.QPushButton("Play Recovered")
        self.btn_play_recovered.clicked.connect(self.play_recovered)
        for btn, color in (
            (self.btn_play_original, COLORS["success"]),
            (self.btn_play_modulated, COLORS["warning"]),
            (self.btn_play_recovered, COLORS["accent"]),
        ):
            style_button(btn, color)
            if not SOUNDDEVICE_AVAILABLE:
                btn.setEnabled(False)
                btn.setToolTip("Install the 'sounddevice' package for playback.")
            btn_layout.addWidget(btn)
        controls.addLayout(btn_layout, 2, 0, 1, 4)

        main_layout.addWidget(control_frame)

    def _load_audio(self) -> None:
        self.original_sr, audio = load_and_validate_audio(AUDIO_SAMPLE_PATH)
        duration = min(2.5, len(audio) / self.original_sr if self.original_sr > 0 else 2.5)
        sample_count = int(duration * self.original_sr) if self.original_sr > 0 else 0
        self.audio = audio[:sample_count]
        self.time = (
            np.linspace(0, duration, len(self.audio), dtype=np.float64)
            if self.audio.size
            else np.zeros(1, dtype=np.float64)
        )
        self.current_modulated = np.zeros_like(self.audio)
        self.last_demod = np.zeros_like(self.audio)

    # --- control handlers -------------------------------------------------
    def _on_fc_changed(self, value: int) -> None:
        self.fc_hz = int(value) * 1000
        self.fc_value_lbl.setText(f"{value} kHz")
        self.schedule_update()

    def _on_dc_changed(self, value: float) -> None:
        self.carrier_dc = float(value)
        self.dc_value_lbl.setText(f"{value:.2f}")
        self.schedule_update()

    def _on_mode_changed(self, button: QtWidgets.QAbstractButton) -> None:
        self.mode = button.text()
        self.schedule_update()

    # --- playback ---------------------------------------------------------
    def play_original(self) -> None:
        self._play_buffer(self.audio, gain=1.0)

    def play_modulated(self) -> None:
        self._play_buffer(self.current_modulated, gain=0.35)

    def play_recovered(self) -> None:
        self._play_buffer(self.last_demod, gain=0.9)

    # --- plotting ---------------------------------------------------------
    def update_plot(self) -> None:
        if self._is_updating or self.audio.size < 2:
            return
        self._is_updating = True
        try:
            audio_norm = self.audio / (np.max(np.abs(self.audio)) + 1e-10)
            carrier = np.cos(2 * np.pi * self.fc_hz * self.time)
            if self.mode == "DSB-SC":
                modulated = audio_norm * carrier
            else:
                modulated = (audio_norm + self.carrier_dc) * carrier
            self.current_modulated = np.ascontiguousarray(modulated)

            demod_sync = modulated * carrier
            nyq = self.original_sr / 2.0
            cutoff = min(5_000, nyq * 0.9) if nyq > 0 else 2_000
            cutoff = max(500.0, cutoff)
            if nyq > 0:
                wn = min(0.99, cutoff / nyq)
                b, a = signal.butter(6, wn, btype="low")
                demod_filtered = signal.filtfilt(b, a, demod_sync) * 2
            else:
                demod_filtered = demod_sync

            if self.mode == "Envelope":
                analytic = signal.hilbert(modulated)
                envelope = np.abs(analytic) - self.carrier_dc
                demod_display = envelope
            else:
                demod_display = demod_filtered

            demod_display = demod_display / (np.max(np.abs(demod_display)) + 1e-10)
            self.last_demod = demod_display

            self.figure.clf()
            axes = self.figure.subplots(4, 1)
            configure_axes(axes)

            length = len(self.audio)
            seg = slice(length // 4, min(length // 4 + 2000, length))
            t_seg = self.time[seg]

            axes[0].plot(t_seg, audio_norm[seg], color=COLORS["accent"], linewidth=1.4)
            axes[0].set_title("Message Signal x(t)")
            axes[0].set_ylabel("Amplitude")

            axes[1].plot(t_seg, modulated[seg], color=COLORS["danger"], linewidth=0.9)
            if self.mode != "DSB-SC":
                env = (audio_norm + self.carrier_dc)[seg]
                axes[1].plot(t_seg, env, color=COLORS["success"], linewidth=1.2, alpha=0.8)
                axes[1].plot(t_seg, -env, color=COLORS["success"], linewidth=1.2, alpha=0.8)
            axes[1].set_title(f"{self.mode} Modulated Signal (fc={self.fc_hz/1000:.0f} kHz)")
            axes[1].set_ylabel("Amplitude")

            axes[2].plot(t_seg, demod_display[seg], color=COLORS["success"], linewidth=1.2)
            method = "Envelope" if self.mode == "Envelope" else "Synchronous"
            axes[2].set_title(f"Recovered Signal ({method} demod)")
            axes[2].set_ylabel("Amplitude")

            if len(modulated) > 1 and self.original_sr > 0:
                freqs, psd = signal.welch(modulated, self.original_sr, nperseg=min(4096, len(modulated)))
                psd_db = 10 * np.log10(psd + 1e-12)
                axes[3].plot(freqs / 1000, psd_db, color=COLORS["warning"], linewidth=1.6)
                axes[3].axvline(self.fc_hz / 1000, color=COLORS["danger"], linestyle="--", linewidth=1.2)
                band = 5  # kHz assumed message band
                axes[3].axvspan((self.fc_hz - band * 1000) / 1000, (self.fc_hz + band * 1000) / 1000, alpha=0.12, color=COLORS["accent"])
                axes[3].set_xlim(0, min(25, freqs[-1] / 1000))
                axes[3].set_ylim(psd_db.max() - 80, psd_db.max() + 5)
                axes[3].set_title("Spectrum")
                axes[3].set_xlabel("Frequency (kHz)")
                axes[3].set_ylabel("Power (dB)")
            else:
                axes[3].set_title("Spectrum unavailable (audio too short)")
                axes[3].set_xlabel("Frequency (kHz)")

            self.figure.tight_layout(rect=[0, 0.02, 1, 0.98])
            self.canvas.draw_idle()
        except Exception as exc:
            print(f"AM update error: {exc}")
        finally:
            self._is_updating = False