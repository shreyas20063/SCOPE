"""
Audio Aliasing Demonstration Window
Demonstrates the Nyquist theorem and aliasing effects
"""

import numpy as np
import matplotlib.pyplot as plt
import scipy.signal as signal
import sounddevice as sd
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QSlider, QPushButton, QCheckBox, QFrame)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config import COLORS
from utils.utils import load_and_validate_audio


class DemoWindow_Aliasing(QMainWindow):
    """Window for the Audio Aliasing demonstration."""
    def __init__(self, parent=None, title="Audio Aliasing Demo"):
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

        # --- Instance Variables ---
        audio_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                  'assets', 'audio_sample.wav')
        self.original_sr, self.audio = load_and_validate_audio(audio_path)
        self.duration = min(3, len(self.audio) / self.original_sr if self.original_sr > 0 else 3)

        if self.original_sr > 0:
            self.audio = self.audio[:int(self.duration * self.original_sr)]
        else:
            self.audio = np.array([], dtype=np.float32)

        self.time = np.linspace(0, self.duration, len(self.audio), dtype=np.float32) if len(self.audio) > 0 else np.array([])
        self.aa_status = False
        self.downsample_factor = 4
        self.current_downsampled = np.array([0.0], dtype=np.float32)
        self.current_sr = 1.0

        # Setup and initial plot update
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

        # First row: Slider controls and checkbox
        row1 = QHBoxLayout()
        row1.setSpacing(10)

        # Downsampling Factor Label
        slider_label = QLabel("Downsampling Factor:")
        slider_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 14px;")
        row1.addWidget(slider_label)

        # Slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(1)
        self.slider.setMaximum(20)
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

        # Anti-Aliasing Checkbox
        self.check_aa = QCheckBox("Anti-Aliasing Filter")
        self.check_aa.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 14px;")
        self.check_aa.stateChanged.connect(self.checkbox_update)
        row1.addWidget(self.check_aa)

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

        # Play Downsampled Button
        self.btn_play_down = QPushButton("▶ Play Downsampled")
        self.btn_play_down.setMinimumWidth(180)
        self.btn_play_down.setStyleSheet(f"""
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
        self.btn_play_down.clicked.connect(self.play_downsampled)
        row2.addWidget(self.btn_play_down)

        row2.addStretch()
        layout.addLayout(row2)

        return panel

    def slider_update(self, value):
        """Callback for the downsampling slider."""
        self.downsample_factor = int(value)
        self.slider_value_label.setText(str(self.downsample_factor))
        self._update_plot()

    def checkbox_update(self):
        """Callback for the anti-aliasing checkbox."""
        self.aa_status = self.check_aa.isChecked()
        self._update_plot()

    def _setup_plot(self):
        """Initial setup of the Matplotlib plot axes."""
        self.fig.clf()
        self.axes = self.fig.subplots(3, 1)
        self.fig.patch.set_facecolor(COLORS['bg'])

        for ax in self.axes:
            ax.set_facecolor(COLORS['bg'])
            ax.grid(True, alpha=0.2, color=COLORS['grid'])
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.xaxis.label.set_color(COLORS['text_primary'])
            ax.yaxis.label.set_color(COLORS['text_primary'])
            ax.title.set_color(COLORS['text_primary'])
            ax.tick_params(axis='x', colors=COLORS['text_secondary'])
            ax.tick_params(axis='y', colors=COLORS['text_secondary'])

        self.fig.subplots_adjust(bottom=0.1, top=0.95, left=0.08, right=0.97, hspace=0.4)

        # Find Best Segment Logic
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
                        print(f"Warning: Floating point error calculating RMS for chunk {i}")
                        continue
        self.best_start = best_start

        # Calculate indices for the segment to display
        n_samples_to_show = min(chunk_size, len(self.audio) - best_start)
        start_idx = self.best_start
        end_idx = start_idx + n_samples_to_show

        # Plot original signal segment
        if n_samples_to_show > 1 and len(self.time) >= end_idx:
            segment = self.audio[start_idx:end_idx]
            time_segment = self.time[start_idx:end_idx]
            self.axes[0].plot(time_segment, segment, color=COLORS['accent'], linewidth=1.5, label='Original Signal')
        else:
            self.axes[0].plot([], [], color=COLORS['accent'], linewidth=1.5, label='Original Signal (No Data)')

        self.axes[0].set_title('Original Audio Signal', fontsize=13, fontweight='bold')
        self.axes[0].set_xlabel('Time (seconds)', fontsize=11)
        self.axes[0].set_ylabel('Amplitude', fontsize=11)
        self.axes[0].legend(loc='upper right', framealpha=0.9)

        # Setup downsampled signal line
        self.line_down, = self.axes[1].plot([], [], 'o-', color=COLORS['danger'], markersize=4, linewidth=1.5, label='Downsampled Signal')
        self.axes[1].set_title('Downsampled Signal', fontsize=13, fontweight='bold')
        self.axes[1].set_xlabel('Time (seconds)', fontsize=11)
        self.axes[1].set_ylabel('Amplitude', fontsize=11)
        self.axes[1].legend(loc='upper right', framealpha=0.9)

        # Setup frequency spectrum axes
        self.axes[2].set_title('Frequency Spectrum Comparison', fontsize=13, fontweight='bold')
        self.axes[2].set_xlabel('Frequency (Hz)', fontsize=11)
        self.axes[2].set_ylabel('Magnitude (dB)', fontsize=11)

        try:
            self.fig.tight_layout(rect=[0, 0.03, 1, 0.97])
        except ValueError:
            print("Warning: Initial tight_layout failed.")

    def _update_plot(self):
        """Updates the plots based on current settings."""
        downsample_factor = self.downsample_factor
        use_filter = self.aa_status

        # Apply Anti-Aliasing Filter
        filtered_audio = self.audio
        if use_filter and self.original_sr > 0:
            nyquist = self.original_sr / 2.0
            cutoff = max(0.01, (self.original_sr / max(1, downsample_factor)) / 2.0 * 0.95)

            if cutoff < nyquist and cutoff > 0:
                try:
                    b, a = signal.butter(8, cutoff / nyquist, btype='low')
                    filtered_audio = signal.filtfilt(b, a, self.audio)
                except ValueError as e:
                    print(f"Filter design error: {e}. Using unfiltered audio.")
                    filtered_audio = self.audio
            else:
                print(f"Warning: Invalid cutoff frequency. Skipping filter.")
                if downsample_factor > self.original_sr / 4:
                    print("Downsampling factor is very high, using zeros.")
                    filtered_audio = np.zeros_like(self.audio)
                else:
                    filtered_audio = self.audio

        # Downsampling
        downsampled = filtered_audio[::max(1, downsample_factor)]
        new_sr = self.original_sr / max(1.0, float(downsample_factor))

        if len(downsampled) < 2:
            downsampled = np.array([0.0] * max(1, len(downsampled)), dtype=np.float32)
            new_sr = 1.0 if new_sr <= 0 else new_sr

        self.current_downsampled = downsampled.astype(np.float32)
        self.current_sr = new_sr

        # Update Downsampled Time Series Plot
        time_down = np.arange(len(downsampled), dtype=np.float32) / new_sr if new_sr > 0 else np.zeros(len(downsampled))

        display_start_idx_down = self.best_start // max(1, downsample_factor)
        n_show_max_down = len(downsampled) - display_start_idx_down
        n_show_down = min(1000 // max(1, downsample_factor), n_show_max_down)
        n_show_down = max(0, n_show_down)

        if n_show_down > 1:
            display_end_idx_down = display_start_idx_down + n_show_down
            display_start_idx_down = max(0, display_start_idx_down)
            display_end_idx_down = min(len(downsampled), display_end_idx_down)
            n_show_down = display_end_idx_down - display_start_idx_down

            if n_show_down > 1:
                display_segment_down = downsampled[display_start_idx_down:display_end_idx_down]
                time_segment_down = time_down[display_start_idx_down:display_end_idx_down]
                self.line_down.set_data(time_segment_down, display_segment_down)

                if len(time_segment_down) > 0:
                    self.axes[1].set_xlim(time_segment_down[0], time_segment_down[-1])
                else:
                    self.axes[1].set_xlim(0,1)

                y_max_abs_down = np.max(np.abs(display_segment_down)) if len(display_segment_down) > 0 else 0.1
                y_max_down = max(0.1, y_max_abs_down) * 1.2
                self.axes[1].set_ylim(-y_max_down, y_max_down)
            else:
                self.line_down.set_data([], [])
                self.axes[1].set_xlim(0, 1)
                self.axes[1].set_ylim(-0.1, 0.1)
        else:
            self.line_down.set_data([], [])
            self.axes[1].set_xlim(0, 1)
            self.axes[1].set_ylim(-0.1, 0.1)

        # Update Frequency Spectrum Plot
        ax_spec = self.axes[2]
        ax_spec.clear()
        ax_spec.set_facecolor(COLORS['bg'])
        ax_spec.grid(True, alpha=0.2, color=COLORS['grid'])
        ax_spec.spines['top'].set_visible(False)
        ax_spec.spines['right'].set_visible(False)
        ax_spec.set_title(f'Frequency Spectrum (Factor={downsample_factor}x, Filter={"ON" if use_filter else "OFF"})',
                          fontsize=13, fontweight='bold', color=COLORS['text_primary'])
        ax_spec.set_xlabel('Frequency (Hz)', fontsize=11, color=COLORS['text_primary'])
        ax_spec.set_ylabel('Magnitude (dB)', fontsize=11, color=COLORS['text_primary'])
        ax_spec.tick_params(axis='x', colors=COLORS['text_secondary'])
        ax_spec.tick_params(axis='y', colors=COLORS['text_secondary'])

        # Calculate spectra
        psd_orig_db = np.array([-100.0])
        freqs_orig = np.array([0.0])
        if len(self.audio) > 1 and self.original_sr > 0:
            nperseg_orig = min(2048, len(self.audio))
            if nperseg_orig > 0:
                try:
                    freqs_orig, psd_orig = signal.welch(self.audio, self.original_sr, nperseg=nperseg_orig, scaling='density')
                    psd_orig_db = 10 * np.log10(psd_orig + 1e-12)
                except (ValueError, FloatingPointError) as e:
                    print(f"Welch error (original): {e}")

        psd_down_db = np.array([-100.0])
        freqs_down = np.array([0.0])
        if len(downsampled) > 1 and new_sr > 0:
            nperseg_down = min(512, len(downsampled))
            if nperseg_down > 0:
                try:
                    freqs_down, psd_down = signal.welch(downsampled, new_sr, nperseg=nperseg_down, scaling='density')
                    psd_down_db = 10 * np.log10(psd_down + 1e-12)
                except (ValueError, FloatingPointError) as e:
                    print(f"Welch error (downsampled): {e}")

        # Plot spectra
        ax_spec.plot(freqs_orig, psd_orig_db, color=COLORS['accent'], alpha=0.8, label='Original', linewidth=2)
        ax_spec.plot(freqs_down, psd_down_db, color=COLORS['danger'], alpha=0.8, label='Downsampled', linewidth=2)

        # Plot Nyquist lines
        nyquist_orig_val = self.original_sr / 2.0
        nyquist_new_val = new_sr / 2.0
        if nyquist_orig_val > 0:
            ax_spec.axvline(nyquist_orig_val, color=COLORS['accent'], linestyle='--', alpha=0.6, linewidth=1.5, label=f'Orig Nyquist ({nyquist_orig_val:.0f} Hz)')
        if nyquist_new_val > 0:
            ax_spec.axvline(nyquist_new_val, color=COLORS['danger'], linestyle='--', alpha=0.6, linewidth=1.5, label=f'New Nyquist ({nyquist_new_val:.0f} Hz)')

        xlim_spec_upper = min(10000, nyquist_orig_val + 1000) if nyquist_orig_val > 0 else 10000
        ax_spec.set_xlim(0, xlim_spec_upper)

        max_psd_orig = np.max(psd_orig_db[np.isfinite(psd_orig_db)]) if np.any(np.isfinite(psd_orig_db)) else -100
        max_psd_down = np.max(psd_down_db[np.isfinite(psd_down_db)]) if np.any(np.isfinite(psd_down_db)) else -100
        ylim_spec_upper = max(max_psd_orig, max_psd_down) + 10
        ylim_spec_lower = max(ylim_spec_upper - 90, -120)
        ax_spec.set_ylim(ylim_spec_lower, ylim_spec_upper)

        ax_spec.legend(loc='upper right', framealpha=0.9, fontsize='small')

        try:
            self.fig.tight_layout(rect=[0, 0.03, 1, 0.97])
        except ValueError as e:
            print(f"Warning: tight_layout failed: {e}")

        self.canvas.draw_idle()

    def play_original(self):
        """Plays the original audio."""
        print("\n--- Playing Original ---")
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

    def play_downsampled(self):
        """Plays the currently downsampled audio."""
        print("\n--- Playing Downsampled ---")
        if self.current_downsampled is None or len(self.current_downsampled) == 0:
            print("Downsampled audio is empty.")
            return
        if len(self.current_downsampled) <= 1 and np.all(self.current_downsampled == 0):
            print("Downsampled audio is silent or too short.")
            return
        if self.current_sr <= 0:
            print(f"Invalid sample rate: {self.current_sr}.")
            return

        try:
            sd.stop()
            sr_int = int(round(self.current_sr))
            if sr_int <= 0:
                print(f"Rounded sample rate {sr_int} is invalid.")
                return

            audio_to_play = self.current_downsampled.astype(np.float32)
            sd.play(audio_to_play, sr_int)
            print("Playback started.")
        except Exception as e:
            print(f"Error during playback: {e}")
