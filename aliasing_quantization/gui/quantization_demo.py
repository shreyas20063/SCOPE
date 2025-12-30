"""
Audio Quantization Demonstration Window
Compares three quantization techniques: Standard, Dither, and Robert's Method
"""

import numpy as np
import matplotlib.pyplot as plt
import scipy.signal as signal
import sounddevice as sd
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QSlider, QPushButton, QFrame, QButtonGroup, QRadioButton)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config import COLORS
from utils.utils import load_and_validate_audio


class DemoWindow_Quantization(QMainWindow):
    """Window for the Audio Quantization demonstration."""
    def __init__(self, parent=None, title="Audio Quantization Demo"):
        super().__init__()  # Don't pass parent to keep it as independent window
        self.setWindowTitle(title)
        self.resize(1160, 790)
        self.setMinimumSize(900, 600)

        # Set window background color
        self.setStyleSheet(f"background-color: {COLORS['bg']};")

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Create matplotlib figure and canvas
        self.fig = Figure(figsize=(10.5, 6.5), facecolor=COLORS['bg'])
        self.canvas = FigureCanvasQTAgg(self.fig)
        self.canvas.setStyleSheet(f"background-color: {COLORS['bg']};")

        # Add navigation toolbar
        self.toolbar = NavigationToolbar2QT(self.canvas, central_widget)

        # Add canvas and toolbar to layout
        main_layout.addWidget(self.canvas)
        main_layout.addWidget(self.toolbar)

        # Create control panel
        self.control_panel = self._create_control_panel()
        main_layout.addWidget(self.control_panel)

        # Instance Variables
        audio_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                  'assets', 'audio_sample.wav')
        self.original_sr, self.audio = load_and_validate_audio(audio_path)
        self.duration = min(3, len(self.audio) / self.original_sr if self.original_sr > 0 else 3)

        if self.original_sr > 0:
            self.audio = self.audio[:int(self.duration * self.original_sr)]
        else:
            self.audio = np.array([], dtype=np.float32)

        self.time = np.linspace(0, self.duration, len(self.audio), dtype=np.float32) if len(self.audio) > 0 else np.array([])
        self.bits = 4
        self.method = "Standard"
        self.current_quantized = self.audio.copy()

        self._setup_plot()
        self._update_plot()

    def _create_control_panel(self):
        """Creates the control panel with sliders and buttons."""
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['panel']};
                border-radius: 14px;
                padding: 10px;
            }}
        """)

        layout = QVBoxLayout(panel)
        layout.setSpacing(10)

        # First row: Slider controls and radio buttons
        row1 = QHBoxLayout()
        row1.setSpacing(10)

        # Bit Depth Label
        slider_label = QLabel("Bit Depth:")
        slider_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 14px;")
        row1.addWidget(slider_label)

        # Slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(1)
        self.slider.setMaximum(16)
        self.slider.setValue(4)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(1)
        self.slider.setMinimumWidth(240)
        self.slider.valueChanged.connect(self.slider_update)
        self.slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                border: 1px solid {COLORS['border']};
                height: 8px;
                background: {COLORS['bg']};
                margin: 2px 0;
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {COLORS['accent']};
                border: 1px solid {COLORS['accent_dark']};
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {COLORS['accent_dark']};
            }}
        """)
        row1.addWidget(self.slider)

        # Value Label
        self.slider_value_label = QLabel("4")
        self.slider_value_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 14px; font-weight: bold; min-width: 28px;")
        row1.addWidget(self.slider_value_label)

        row1.addSpacing(20)

        # Radio buttons for quantization method
        radio_frame = QFrame()
        radio_frame.setStyleSheet(f"""
            QRadioButton {{
                color: {COLORS['text_primary']};
                font-size: 13px;
                font-weight: bold;
                padding: 5px 10px;
                spacing: 5px;
            }}
            QRadioButton::indicator {{
                width: 15px;
                height: 15px;
            }}
            QRadioButton::indicator:checked {{
                background-color: {COLORS['accent']};
                border: 2px solid {COLORS['accent_dark']};
                border-radius: 8px;
            }}
            QRadioButton::indicator:unchecked {{
                background-color: {COLORS['bg']};
                border: 2px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """)
        radio_layout = QHBoxLayout(radio_frame)
        radio_layout.setSpacing(15)
        radio_layout.setContentsMargins(5, 5, 5, 5)

        self.radio_standard = QRadioButton("Standard")
        self.radio_dither = QRadioButton("Dither")
        self.radio_roberts = QRadioButton("Robert's")

        self.radio_standard.setChecked(True)
        self.radio_standard.toggled.connect(lambda: self.radio_update("Standard"))
        self.radio_dither.toggled.connect(lambda: self.radio_update("Dither"))
        self.radio_roberts.toggled.connect(lambda: self.radio_update("Robert's"))

        radio_layout.addWidget(self.radio_standard)
        radio_layout.addWidget(self.radio_dither)
        radio_layout.addWidget(self.radio_roberts)

        row1.addWidget(radio_frame)
        row1.addStretch()
        layout.addLayout(row1)

        # Second row: Play buttons
        row2 = QHBoxLayout()
        row2.setSpacing(10)
        row2.addStretch()

        # Play Original Button
        self.btn_play_orig = QPushButton("▶ Play Original")
        self.btn_play_orig.setMinimumWidth(180)
        self.btn_play_orig.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['success']};
                color: white;
                border: none;
                padding: 10px;
                font-weight: bold;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_dark']};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['accent_dark']};
            }}
        """)
        self.btn_play_orig.clicked.connect(self.play_original)
        row2.addWidget(self.btn_play_orig)

        # Play Quantized Button
        self.btn_play_quant = QPushButton("▶ Play Quantized")
        self.btn_play_quant.setMinimumWidth(180)
        self.btn_play_quant.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['warning']};
                color: white;
                border: none;
                padding: 10px;
                font-weight: bold;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_dark']};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['accent_dark']};
            }}
        """)
        self.btn_play_quant.clicked.connect(self.play_quantized)
        row2.addWidget(self.btn_play_quant)

        row2.addStretch()
        layout.addLayout(row2)

        return panel

    def slider_update(self, value):
        """Callback for the bit depth slider."""
        self.bits = int(value)
        self.slider_value_label.setText(str(self.bits))
        self._update_plot()

    def radio_update(self, value):
        """Callback for the quantization method selector."""
        self.method = value
        self._update_plot()

    # Quantization Functions
    def uniform_quantize(self, sig, bits):
        """Mid-rise quantizer for audio range [-1, 1]"""
        levels = 2 ** bits
        step = 2.0 / levels if levels > 0 else 2.0
        quantized = np.round(sig / step) * step
        return np.clip(quantized, -1.0, 1.0)

    def quantize_with_dither(self, sig, bits):
        """Mid-rise quantizer with dither"""
        levels = 2 ** bits
        step = 2.0 / levels if levels > 0 else 2.0
        dither = np.random.uniform(-step/2.0, step/2.0, size=sig.shape).astype(np.float32)
        quantized = np.round((sig + dither) / step) * step
        return np.clip(quantized, -1.0, 1.0)

    def roberts_technique(self, sig, bits):
        """Mid-rise quantizer with subtractive dither (Robert's)"""
        levels = 2 ** bits
        step = 2.0 / levels if levels > 0 else 2.0
        dither = np.random.uniform(-step/2.0, step/2.0, size=sig.shape).astype(np.float32)
        quantized = np.round((sig + dither) / step) * step - dither
        return np.clip(quantized, -1.0, 1.0)

    def _setup_plot(self):
        """Initial setup of the Matplotlib plot axes."""
        self.fig.clf()
        plt.style.use('seaborn-v0_8-whitegrid')

        gs = self.fig.add_gridspec(3, 2, hspace=0.4, wspace=0.3, bottom=0.1, top=0.95, left=0.08, right=0.95)
        self.ax_orig = self.fig.add_subplot(gs[0, :])
        self.ax_quant = self.fig.add_subplot(gs[1, :])
        self.ax_error = self.fig.add_subplot(gs[2, 0])
        self.ax_quant_func = self.fig.add_subplot(gs[2, 1])

        self.fig.patch.set_facecolor(COLORS['bg'])

        for ax in [self.ax_orig, self.ax_quant, self.ax_error, self.ax_quant_func]:
            ax.set_facecolor(COLORS['bg'])
            ax.grid(True, alpha=0.2, color=COLORS['grid'])
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.xaxis.label.set_color(COLORS['text_primary'])
            ax.yaxis.label.set_color(COLORS['text_primary'])
            ax.title.set_color(COLORS['text_primary'])
            ax.tick_params(axis='x', colors=COLORS['text_secondary'])
            ax.tick_params(axis='y', colors=COLORS['text_secondary'])

        # Find Best Segment
        chunk_size = 1000
        best_start = 0
        if len(self.audio) > chunk_size:
            max_rms = 0
            num_chunks = min(10, len(self.audio) // chunk_size)
            for i in range(num_chunks):
                start = i * chunk_size
                end = start + chunk_size
                if end <= len(self.audio):
                    try:
                        chunk_rms = np.sqrt(np.mean(self.audio[start:end]**2))
                        if chunk_rms > max_rms:
                            max_rms = chunk_rms
                            best_start = start
                    except FloatingPointError:
                        continue
        self.best_start_quant = best_start

        # Plot original signal
        n_samples_to_show = min(chunk_size, len(self.audio) - best_start)
        start_idx = self.best_start_quant
        end_idx = start_idx + n_samples_to_show

        if n_samples_to_show > 1 and len(self.time) >= end_idx:
            segment = self.audio[start_idx:end_idx]
            time_segment = self.time[start_idx:end_idx]
            self.ax_orig.plot(time_segment, segment, color=COLORS['accent'], linewidth=1.5, label='Original Signal')
        else:
            self.ax_orig.plot([],[], color=COLORS['accent'], linewidth=1.5, label='Original Signal (No Data)')

        self.ax_orig.set_title('Original Audio Signal', fontsize=13, fontweight='bold')
        self.ax_orig.set_xlabel('Time (seconds)', fontsize=11)
        self.ax_orig.set_ylabel('Amplitude', fontsize=11)
        self.ax_orig.legend(loc='upper right', framealpha=0.9)

        # Setup quantized signal line
        self.line_quant, = self.ax_quant.plot([], [], color=COLORS['warning'], linewidth=1.5, label='Quantized Signal')
        self.ax_quant.set_title('Quantized Signal', fontsize=13, fontweight='bold')
        self.ax_quant.set_xlabel('Time (seconds)', fontsize=11)
        self.ax_quant.set_ylabel('Amplitude', fontsize=11)
        self.ax_quant.legend(loc='upper right', framealpha=0.9)

        # Setup error spectrum axes
        self.ax_error.set_title('Quantization Error Spectrum', fontsize=12, fontweight='bold')
        self.ax_error.set_xlabel('Frequency (Hz)', fontsize=10)
        self.ax_error.set_ylabel('Magnitude (dB)', fontsize=10)

        # Setup quantization function axes
        self.ax_quant_func.set_title('Quantization Function', fontsize=12, fontweight='bold')
        self.ax_quant_func.set_xlabel('Input Amplitude', fontsize=10)
        self.ax_quant_func.set_ylabel('Output Amplitude', fontsize=10)

        try:
            self.fig.tight_layout(rect=[0, 0.03, 1, 0.95])
        except ValueError:
            print("Warning: Initial tight_layout failed.")

    def _update_plot(self):
        """Updates the quantization plots."""
        bits = self.bits
        method = self.method

        # Apply quantization
        if 'Standard' in method:
            quantized = self.uniform_quantize(self.audio, bits)
            method_label = 'Standard Q'
        elif 'Dither' in method:
            quantized = self.quantize_with_dither(self.audio, bits)
            method_label = 'With Dither'
        else:
            quantized = self.roberts_technique(self.audio, bits)
            method_label = "Robert's"

        self.current_quantized = quantized.astype(np.float32)

        # Update Quantized Plot
        n_samples_shown = 1000
        start_idx = self.best_start_quant
        end_idx = min(start_idx + n_samples_shown, len(self.audio))
        start_idx = max(0, end_idx - n_samples_shown)
        plot_len = end_idx - start_idx

        if plot_len > 1 and len(self.time) >= end_idx:
            quant_segment = quantized[start_idx:end_idx]
            time_segment = self.time[start_idx:end_idx]
            self.line_quant.set_data(time_segment, quant_segment)
            self.ax_quant.set_xlim(time_segment[0], time_segment[-1])

            orig_segment_abs = np.abs(self.audio[start_idx:end_idx])
            y_max_seg = np.max(orig_segment_abs) if len(orig_segment_abs) > 0 else 0.1
            y_max = max(0.1, y_max_seg) * 1.2
            self.ax_quant.set_ylim(-y_max, y_max)
        else:
            self.line_quant.set_data([], [])
            self.ax_quant.set_xlim(0,1)
            self.ax_quant.set_ylim(-0.1, 0.1)

        self.ax_quant.set_title(f'Quantized Signal ({bits} bits, {method_label})', fontsize=13, fontweight='bold')

        # Update Error Spectrum
        ax_err = self.ax_error
        ax_err.clear()
        ax_err.set_facecolor(COLORS['bg'])
        ax_err.grid(True, alpha=0.2, color=COLORS['grid'])
        ax_err.spines['top'].set_visible(False)
        ax_err.spines['right'].set_visible(False)
        ax_err.set_xlabel('Frequency (Hz)', fontsize=10, color=COLORS['text_primary'])
        ax_err.set_ylabel('Magnitude (dB)', fontsize=10, color=COLORS['text_primary'])
        ax_err.tick_params(axis='x', colors=COLORS['text_secondary'])
        ax_err.tick_params(axis='y', colors=COLORS['text_secondary'])

        error = self.audio - quantized
        snr = float('-inf')

        if len(error) > 1 and self.original_sr > 0:
            nperseg_err = min(2048, len(error))
            if nperseg_err > 0:
                try:
                    freqs_err, psd_err = signal.welch(error, self.original_sr, nperseg=nperseg_err, scaling='density')
                    psd_err_db = 10 * np.log10(psd_err + 1e-12)
                    ax_err.plot(freqs_err, psd_err_db, color=COLORS['danger'], linewidth=1.5, label='Quantization Error')

                    signal_power = np.mean(self.audio ** 2)
                    noise_power = np.mean(error ** 2)
                    if noise_power > 1e-15 and signal_power > 1e-15:
                        snr = 10 * np.log10(signal_power / noise_power)
                except (ValueError, FloatingPointError) as e:
                    print(f"Welch error: {e}")

        ax_err.set_xlim(0, self.original_sr / 2.0 if self.original_sr > 0 else 1)
        ax_err.legend(loc='upper right', framealpha=0.9, fontsize='small')
        ax_err.set_title(f'Error Spectrum (SNR={snr:.1f} dB)', fontsize=12, fontweight='bold', color=COLORS['text_primary'])

        ylim_err = ax_err.get_ylim()
        ax_err.set_ylim(max(ylim_err[0], -150), ylim_err[1] + 5)

        # Update Quantization Function
        ax_qfunc = self.ax_quant_func
        ax_qfunc.clear()
        ax_qfunc.set_facecolor(COLORS['bg'])
        ax_qfunc.grid(True, alpha=0.2, color=COLORS['grid'])
        ax_qfunc.spines['top'].set_visible(False)
        ax_qfunc.spines['right'].set_visible(False)
        ax_qfunc.set_xlabel('Input Amplitude', fontsize=10, color=COLORS['text_primary'])
        ax_qfunc.set_ylabel('Output Amplitude', fontsize=10, color=COLORS['text_primary'])
        ax_qfunc.tick_params(axis='x', colors=COLORS['text_secondary'])
        ax_qfunc.tick_params(axis='y', colors=COLORS['text_secondary'])
        ax_qfunc.set_title(f'{method_label} Function', fontsize=12, fontweight='bold', color=COLORS['text_primary'])

        x_test = np.linspace(-1, 1, 1000, dtype=np.float32)

        if 'Standard' in method:
            y_test = self.uniform_quantize(x_test, bits)
            ax_qfunc.plot(x_test, y_test, color=COLORS['warning'], linewidth=2.0, label='Quantizer')
            ax_qfunc.plot(x_test, x_test, '--', color=COLORS['accent'], alpha=0.6, linewidth=1.5, label='Ideal')
        else:
            for _ in range(30):
                if 'Dither' in method:
                    y_test = self.quantize_with_dither(x_test, bits)
                else:
                    y_test = self.roberts_technique(x_test, bits)
                ax_qfunc.plot(x_test, y_test, color=COLORS['warning'], alpha=0.08, linewidth=0.5)
            ax_qfunc.plot(x_test, x_test, '--', color=COLORS['accent'], alpha=0.7, linewidth=1.5, label='Ideal')

        ax_qfunc.set_xlim(-1, 1)
        ax_qfunc.set_ylim(-1.1, 1.1)
        ax_qfunc.legend(loc='upper left', framealpha=0.9, fontsize='small')

        try:
            self.fig.tight_layout(rect=[0, 0.03, 1, 0.95])
        except ValueError as e:
            print(f"Warning: tight_layout failed: {e}")

        self.canvas.draw_idle()

    def play_original(self):
        """Plays the original audio."""
        print("\n--- Playing Original (Quantization) ---")
        if self.audio is None or len(self.audio) == 0:
            print("Audio data is empty.")
            return
        if self.original_sr <= 0:
            print(f"Invalid sample rate: {self.original_sr}.")
            return

        try:
            sd.stop()
            audio_to_play = self.audio.astype(np.float32)
            sd.play(audio_to_play, int(round(self.original_sr)))
            print("Playback started.")
        except Exception as e:
            print(f"Error during playback: {e}")

    def play_quantized(self):
        """Plays the currently quantized audio."""
        print("\n--- Playing Quantized ---")
        if self.current_quantized is None or len(self.current_quantized) == 0:
            print("Quantized audio is empty.")
            return
        if self.original_sr <= 0:
            print(f"Invalid sample rate: {self.original_sr}.")
            return

        try:
            sd.stop()
            audio_to_play = self.current_quantized.astype(np.float32)
            sd.play(audio_to_play, int(round(self.original_sr)))
            print("Playback started.")
        except Exception as e:
            print(f"Error during playback: {e}")
