import traceback
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

class DemoWindowFM(DemoWindowBase):
    def __init__(self, parent: QtWidgets.QWidget | None, title: str):
        super().__init__(parent, title)
        self.fc_hz = 10_000
        self._sensitivity_cache = {"FM": 1200.0, "PM": 1.2}
        self.sensitivity = self._sensitivity_cache["FM"]
        self.mode = "FM"
        self.current_modulated = np.zeros(1, dtype=np.float64)
        self.last_demod = np.zeros(1, dtype=np.float64)

        self._build_ui()
        self._load_audio()
        self.schedule_update()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        plot_frame = QtWidgets.QFrame()
        plot_layout = QtWidgets.QVBoxLayout(plot_frame)
        self.figure = Figure(figsize=(10.5, 7.5), dpi=90)
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
        controls.setColumnStretch(1, 1)

        controls.addWidget(make_label("Carrier (kHz)", bold=True), 0, 0)
        self.fc_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.fc_slider.setRange(5, 25)
        self.fc_slider.setValue(10)
        self.fc_slider.valueChanged.connect(self._on_fc_changed)
        style_slider(self.fc_slider)
        self.fc_label = QtWidgets.QLabel("10 kHz")
        self.fc_label.setStyleSheet(VALUE_LABEL_STYLE)
        controls.addWidget(self.fc_slider, 0, 1)
        controls.addWidget(self.fc_label, 0, 2, alignment=QtCore.Qt.AlignLeft)

        self.sensitivity_heading = make_label("Frequency Deviation (Hz)", bold=True)
        controls.addWidget(self.sensitivity_heading, 1, 0)
        self.beta_spin = QtWidgets.QDoubleSpinBox()
        self.beta_spin.setDecimals(1)
        self.beta_spin.setKeyboardTracking(False)
        self.beta_spin.valueChanged.connect(self._on_beta_changed)
        style_spinbox(self.beta_spin)
        self.beta_label = QtWidgets.QLabel("")
        self.beta_label.setStyleSheet(VALUE_LABEL_STYLE)
        controls.addWidget(self.beta_spin, 1, 1)
        controls.addWidget(self.beta_label, 1, 2, alignment=QtCore.Qt.AlignLeft)

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
        for label in ("FM", "PM"):
            btn = QtWidgets.QRadioButton(label)
            btn.setStyleSheet("color:#0F172A; font-weight:500;")
            if label == self.mode:
                btn.setChecked(True)
            self.mode_group.addButton(btn)
            mode_layout.addWidget(btn)
        self.mode_group.buttonClicked.connect(self._on_mode_changed)
        controls.addWidget(mode_box, 0, 3, 2, 1)

        btn_layout = QtWidgets.QHBoxLayout()
        self.btn_play_original = QtWidgets.QPushButton("Play Original")
        self.btn_play_original.clicked.connect(lambda: self._play_buffer(self.audio))
        self.btn_play_modulated = QtWidgets.QPushButton("Play Modulated")
        self.btn_play_modulated.clicked.connect(lambda: self._play_buffer(self.current_modulated, gain=0.25))
        self.btn_play_recovered = QtWidgets.QPushButton("Play Recovered")
        self.btn_play_recovered.clicked.connect(lambda: self._play_buffer(self.last_demod, gain=0.9))
        for btn, color in (
            (self.btn_play_original, COLORS["success"]),
            (self.btn_play_modulated, COLORS["warning"]),
            (self.btn_play_recovered, COLORS["accent"]),
        ):
            style_button(btn, color)
            btn_layout.addWidget(btn)
        if not SOUNDDEVICE_AVAILABLE:
            for btn in (self.btn_play_original, self.btn_play_modulated, self.btn_play_recovered):
                btn.setEnabled(False)
                btn.setToolTip("Install the 'sounddevice' package for playback.")
        controls.addLayout(btn_layout, 2, 0, 1, 4)

        layout.addWidget(control_frame)

    def _load_audio(self) -> None:
        self.original_sr, audio = load_and_validate_audio(AUDIO_SAMPLE_PATH)
        duration = min(2.5, len(audio) / self.original_sr if self.original_sr > 0 else 2.5)
        count = int(duration * self.original_sr) if self.original_sr > 0 else 0
        self.audio = audio[:count]
        self.time = (
            np.linspace(0, duration, len(self.audio), dtype=np.float64)
            if self.audio.size
            else np.zeros(1, dtype=np.float64)
        )
        self.current_modulated = np.zeros_like(self.audio)
        self.last_demod = np.zeros_like(self.audio)

    def _on_fc_changed(self, value: int) -> None:
        self.fc_hz = int(value) * 1000
        self.fc_label.setText(f"{value} kHz")
        self.schedule_update()

    def _on_beta_changed(self, value: float) -> None:
        value = float(value)
        self._sensitivity_cache[self.mode] = value
        self.sensitivity = value
        unit = "Hz" if self.mode == "FM" else "rad"
        self.beta_label.setText(f"{value:.1f} {unit}")
        self.schedule_update()

    def _on_mode_changed(self, button: QtWidgets.QAbstractButton) -> None:
        self.mode = button.text()
        self._apply_sensitivity_settings()

    def _apply_sensitivity_settings(self, initial: bool = False) -> None:
        unit = "Hz" if self.mode == "FM" else "rad"
        heading = "Frequency Deviation (Hz)" if self.mode == "FM" else "Phase Sensitivity (rad)"
        self.sensitivity_heading.setText(heading)
        with QtCore.QSignalBlocker(self.beta_spin):
            if self.mode == "FM":
                self.beta_spin.setRange(50.0, 5000.0)
                self.beta_spin.setSingleStep(50.0)
            else:
                self.beta_spin.setRange(0.2, 10.0)
                self.beta_spin.setSingleStep(0.1)
            value = self._sensitivity_cache[self.mode]
            self.beta_spin.setValue(value)
        self.sensitivity = value
        self.beta_label.setText(f"{value:.1f} {unit}")
        if not initial:
            self.schedule_update()
            
    def update_plot(self) -> None:
        if self._is_updating or self.audio.size < 2:
            return
        self._is_updating = True
        try:
            audio_norm = self.audio / (np.max(np.abs(self.audio)) + 1e-10)
            dt = (self.time[1] - self.time[0]) if self.time.size > 1 else (1.0 / max(self.original_sr, 1))
            kf = self.sensitivity
            if self.mode == "FM":
                integral = np.cumsum(audio_norm) * dt
                phase = 2 * np.pi * (self.fc_hz * self.time + kf * integral)
            else:
                phase = 2 * np.pi * self.fc_hz * self.time + kf * audio_norm
            modulated = np.cos(phase)
            self.current_modulated = modulated

            unwrapped = np.unwrap(phase)
            inst_freq = np.gradient(unwrapped, dt) / (2 * np.pi)

            try:
                analytic = signal.hilbert(modulated)
                carrier_mix = np.exp(-1j * 2 * np.pi * self.fc_hz * self.time)
                baseband = analytic * np.conj(carrier_mix)
                baseband_phase = np.unwrap(np.angle(baseband))

                if self.mode == "FM":
                    inst_freq_demod = np.gradient(baseband_phase, dt) / (2 * np.pi)
                    recovered = inst_freq_demod / (kf + 1e-12)
                else:
                    recovered = baseband_phase / (kf + 1e-12)

                nyq = self.original_sr / 2.0
                cutoff = min(5_000, nyq * 0.9) if nyq > 0 else 2_000
                cutoff = max(500.0, cutoff)
                if nyq > 0:
                    wn = min(0.99, cutoff / nyq)
                    b, a = signal.butter(5, wn, btype="low")
                    recovered = signal.filtfilt(b, a, recovered)

                recovered -= np.mean(recovered)
                self.last_demod = recovered / (np.max(np.abs(recovered)) + 1e-10)
            except Exception as exc:
                print(f"FM demodulation error: {exc}")
                self.last_demod = np.zeros_like(modulated)

            self.figure.clf()
            axes = self.figure.subplots(5, 1)
            configure_axes(axes)

            length = len(self.audio)
            seg = slice(length // 4, min(length // 4 + 2000, length))
            t_seg = self.time[seg]

            axes[0].plot(t_seg, audio_norm[seg], color=COLORS["accent"], linewidth=1.4)
            axes[0].set_title("Message Signal x(t)")
            axes[0].set_ylabel("Amplitude")

            axes[1].plot(t_seg, modulated[seg], color=COLORS["danger"], linewidth=0.8)
            axes[1].set_title(f"{self.mode} Signal (fc={self.fc_hz/1000:.0f} kHz, k={self.sensitivity:.1f})")
            axes[1].set_ylabel("Amplitude")

            axes[2].plot(t_seg, inst_freq[seg] / 1000, color=COLORS["success"], linewidth=1.2)
            axes[2].axhline(self.fc_hz / 1000, color=COLORS["danger"], linestyle="--", linewidth=1.2)
            if self.mode == "FM":
                delta_f = kf * np.max(np.abs(audio_norm))
                axes[2].axhline((self.fc_hz + delta_f) / 1000, color=COLORS["warning"], linestyle=":", linewidth=1.0)
                axes[2].axhline((self.fc_hz - delta_f) / 1000, color=COLORS["warning"], linestyle=":", linewidth=1.0)
            axes[2].set_title("Instantaneous Frequency")
            axes[2].set_ylabel("kHz")

            axes[3].plot(t_seg, self.last_demod[seg], color=COLORS["accent"], linewidth=1.2)
            axes[3].set_title("Recovered Baseband")
            axes[3].set_ylabel("Amplitude")

            if len(modulated) > 1 and self.original_sr > 0:
                nperseg = min(4096, len(modulated))
                freqs, psd = signal.welch(modulated, self.original_sr, nperseg=nperseg)
                psd_db = 10 * np.log10(psd + 1e-12)
                axes[4].plot(freqs / 1000, psd_db, color=COLORS["warning"], linewidth=1.5)
                axes[4].axvline(self.fc_hz / 1000, color=COLORS["danger"], linestyle="--", linewidth=1.1)
                if self.mode == "FM":
                    delta_f = kf * np.max(np.abs(audio_norm))
                    bw_carson_hz = 2 * (delta_f + 5_000)
                    left = (self.fc_hz - bw_carson_hz) / 1000
                    right = (self.fc_hz + bw_carson_hz) / 1000
                    axes[4].axvspan(left, right, alpha=0.1, color=COLORS["accent"])
                    axes[4].set_title(f"Spectrum (Carson BW ≈ {bw_carson_hz/1000:.1f} kHz)")
                else:
                    axes[4].set_title("Spectrum")
                axes[4].set_xlabel("Frequency (kHz)")
                axes[4].set_ylabel("Power (dB)")
                axes[4].set_xlim(0, min(40, freqs[-1] / 1000))
                axes[4].set_ylim(psd_db.max() - 80, psd_db.max() + 5)
            else:
                axes[4].set_title("Spectrum unavailable")
                axes[4].set_xlabel("Frequency (kHz)")

            self.figure.tight_layout(rect=[0, 0.02, 1, 0.98])
            self.canvas.draw_idle()
        except Exception as exc:
            print(f"FM update error: {exc}")
            traceback.print_exc()
        finally:
            self._is_updating = False