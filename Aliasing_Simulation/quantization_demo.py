"""
Audio Quantization Demonstration Window
Compares three quantization techniques: Standard, Dither, and Robert's Method
"""

import numpy as np
import matplotlib.pyplot as plt
import scipy.signal as signal
import sounddevice as sd
import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from config import COLORS
from utils import load_and_validate_audio


class DemoWindow_Quantization(ctk.CTkToplevel):
    """Toplevel window for the Audio Quantization demonstration."""
    def __init__(self, parent, title):
        super().__init__(parent)
        self.title(title)
        self.geometry("1160x790")
        self.configure(bg=COLORS['bg'])

        # Plot Frame
        self.plot_frame = ctk.CTkFrame(self, fg_color=COLORS['bg'])
        self.plot_frame.pack(side='top', fill='both', expand=True, padx=10, pady=10)

        fig = plt.figure(figsize=(10.5, 6.5), facecolor=COLORS['bg'])
        self.canvas = FigureCanvasTkAgg(fig, self.plot_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill='both', expand=True, padx=8, pady=8)

        toolbar = NavigationToolbar2Tk(self.canvas, self.plot_frame)
        toolbar.update()
        toolbar.pack(side='bottom', fill='x')

        # Control Panel
        self.control_panel = ctk.CTkFrame(self, fg_color=COLORS['panel'], corner_radius=14)
        self.control_panel.pack(fill='x', padx=35, pady=(0, 22))
        self.control_panel.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Bit Depth Slider
        self.slider_label = ctk.CTkLabel(
            self.control_panel, 
            text="Bit Depth:", 
            font=ctk.CTkFont(size=14)
        )
        self.slider_label.grid(row=0, column=0, padx=(20,10), pady=12, sticky='e')
        
        self.slider = ctk.CTkSlider(
            self.control_panel, 
            from_=1, 
            to=16, 
            number_of_steps=15, 
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
        self.slider_value_label.grid(row=0, column=2, padx=(0,24), pady=10, sticky='w')

        # Quantization Method Selector
        self.radio_var = ctk.StringVar(value="Standard")
        self.radio_group = ctk.CTkSegmentedButton(
            self.control_panel,
            values=["Standard", "Dither", "Robert's"],
            variable=self.radio_var,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.radio_update
        )
        self.radio_group.grid(row=0, column=3, padx=20, pady=10)

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
        self.btn_play_quant = ctk.CTkButton(
            self.control_panel, 
            text="▶ Play Quantized", 
            fg_color=COLORS['warning'], 
            hover_color=COLORS['accent_dark'], 
            font=ctk.CTkFont(weight="bold"), 
            width=180, 
            command=self.play_quantized
        )
        self.btn_play_orig.grid(row=1, column=1, padx=10, pady=(0,18))
        self.btn_play_quant.grid(row=1, column=2, padx=10, pady=(0,18), sticky='w')

        # Instance Variables
        self.fig = fig
        self.original_sr, self.audio = load_and_validate_audio('audio_sample.wav')
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

    def slider_update(self, value):
        """Callback for the bit depth slider."""
        self.bits = int(round(value))
        self.slider_value_label.configure(text=str(self.bits))
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