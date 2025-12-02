"""
Audio Aliasing Demonstration Window
Demonstrates the Nyquist theorem and aliasing effects
"""

import numpy as np
import matplotlib.pyplot as plt
import scipy.signal as signal
import sounddevice as sd
import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from config import COLORS
from utils import load_and_validate_audio


class DemoWindow_Aliasing(ctk.CTkToplevel):
    """Toplevel window for the Audio Aliasing demonstration."""
    def __init__(self, parent, title):
        super().__init__(parent)
        self.title(title)
        self.geometry("1160x790")
        self.configure(bg=COLORS['bg'])

        # Frame to hold the Matplotlib canvas and toolbar
        self.plot_frame = ctk.CTkFrame(self, fg_color=COLORS['bg'])
        self.plot_frame.pack(side='top', fill='both', expand=True, padx=10, pady=10)

        # Matplotlib Figure and Canvas
        fig = plt.figure(figsize=(10.5, 6.5), facecolor=COLORS['bg'])
        self.canvas = FigureCanvasTkAgg(fig, self.plot_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill='both', expand=True, padx=8, pady=8)

        # Matplotlib Navigation Toolbar
        toolbar = NavigationToolbar2Tk(self.canvas, self.plot_frame)
        toolbar.update()
        toolbar.pack(side='bottom', fill='x')

        # Control Panel Frame at the bottom
        self.control_panel = ctk.CTkFrame(self, fg_color=COLORS['panel'], corner_radius=14)
        self.control_panel.pack(fill='x', padx=35, pady=(0, 22))
        self.control_panel.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Downsampling Factor Slider
        self.slider_label = ctk.CTkLabel(
            self.control_panel, 
            text="Downsampling Factor:", 
            font=ctk.CTkFont(size=14)
        )
        self.slider_label.grid(row=0, column=0, padx=(20,10), pady=12, sticky='e')
        
        self.slider = ctk.CTkSlider(
            self.control_panel, 
            from_=1, 
            to=20, 
            number_of_steps=19, 
            width=240, 
            command=self.slider_update
        )
        self.slider.set(4)
        self.slider.grid(row=0, column=1, padx=(0,16), pady=16, sticky='w')
        
        self.slider_value_label = ctk.CTkLabel(
            self.control_panel, 
            text="4", 
            width=28, 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.slider_value_label.grid(row=0, column=2, padx=(0,24), pady=10)

        # Anti-Aliasing Checkbox
        self.check_aa = ctk.CTkCheckBox(
            self.control_panel, 
            text="Anti-Aliasing Filter", 
            font=ctk.CTkFont(size=14), 
            command=self.checkbox_update
        )
        self.check_aa.grid(row=0, column=3, padx=(0,32), pady=10)
        self.check_aa.deselect()

        # Play Buttons
        self.btn_play_orig = ctk.CTkButton(
            self.control_panel, 
            text="▶ Play Original", 
            fg_color=COLORS['success'], 
            hover_color=COLORS['accent_dark'], 
            font=ctk.CTkFont(weight="bold"), 
            width=180, 
            command=self.play_original
        )
        self.btn_play_down = ctk.CTkButton(
            self.control_panel, 
            text="▶ Play Downsampled", 
            fg_color=COLORS['warning'], 
            hover_color=COLORS['accent_dark'], 
            font=ctk.CTkFont(weight="bold"), 
            width=180, 
            command=self.play_downsampled
        )
        self.btn_play_orig.grid(row=1, column=1, padx=16, pady=(0,18), sticky='e')
        self.btn_play_down.grid(row=1, column=2, padx=8, pady=(0,18), sticky='w')

        # --- Instance Variables ---
        self.fig = fig
        self.original_sr, self.audio = load_and_validate_audio('audio_sample.wav')
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

    def slider_update(self, value):
        """Callback for the downsampling slider."""
        self.downsample_factor = int(round(value))
        self.slider_value_label.configure(text=str(self.downsample_factor))
        self._update_plot()

    def checkbox_update(self):
        """Callback for the anti-aliasing checkbox."""
        self.aa_status = bool(self.check_aa.get())
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