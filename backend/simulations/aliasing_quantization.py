"""
Aliasing & Quantization Simulator
Matching PyQt5 version exactly with 3 demo modes:
- Audio Aliasing: Nyquist theorem, downsampling, anti-aliasing filter
- Audio Quantization: Standard, Dither, Robert's method comparison
- Image Quantization: Visual comparison of quantization methods on images

Uses real audio and image files from assets folder (matching PyQt5).
"""

import numpy as np
import os
from typing import Any, Dict, List, Optional
from scipy import signal
from scipy.fftpack import fft, fftfreq
from scipy.io import wavfile
from PIL import Image
from .base_simulator import BaseSimulator

# Path to assets
ASSETS_DIR = os.path.join(os.path.dirname(__file__), '..', 'assets', 'aliasing_quantization')


class AliasingQuantizationSimulator(BaseSimulator):
    """
    Aliasing & Quantization simulation matching PyQt5 exactly.

    Three demo modes:
    1. aliasing - Audio aliasing with downsampling
    2. quantization - Audio quantization with 3 methods
    3. image - Image quantization comparison
    """

    # Colors matching PyQt5
    COLOR_ORIGINAL = "#3b82f6"    # Blue
    COLOR_PROCESSED = "#ef4444"   # Red/Orange
    COLOR_DITHER = "#22c55e"      # Green
    COLOR_ROBERTS = "#a855f7"     # Purple
    COLOR_NYQUIST = "#10b981"     # Green
    COLOR_ERROR = "#f59e0b"       # Amber

    # Audio generation parameters
    AUDIO_DURATION = 3.0  # seconds
    ORIGINAL_SAMPLE_RATE = 44100  # Hz

    # Default parameters matching PyQt5
    DEFAULT_PARAMS = {
        "demo_mode": "aliasing",
        # Aliasing demo
        "downsample_factor": 4,
        "anti_aliasing": False,
        # Quantization demo (audio)
        "bit_depth": 4,
        "quant_method": "standard",
        # Image demo
        "image_bits": 3,
    }

    def __init__(self, simulation_id: str):
        super().__init__(simulation_id)
        self._audio = None
        self._original_sr = self.ORIGINAL_SAMPLE_RATE
        self._time = None
        # Aliasing results
        self._downsampled = None
        self._downsampled_time = None
        self._new_sr = None
        # Quantization results
        self._quantized = None
        self._quant_error = None
        # Image results
        self._original_image = None
        self._standard_image = None
        self._dither_image = None
        self._roberts_image = None
        # Metrics
        self._snr_db = 0.0
        self._mse_values = {}

    def initialize(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Initialize simulation with parameters."""
        self.parameters = self.DEFAULT_PARAMS.copy()
        if params:
            for name, value in params.items():
                if name in self.parameters:
                    self.parameters[name] = value

        # Load real audio file from assets (matching PyQt5)
        self._load_audio()
        # Load real test image from assets (matching PyQt5)
        self._load_test_image()

        self._initialized = True
        self._compute()
        return self.get_state()

    def update_parameter(self, name: str, value: Any) -> Dict[str, Any]:
        """Update parameter and recompute."""
        if name in self.parameters:
            self.parameters[name] = value
            self._compute()
        return self.get_state()

    def reset(self) -> Dict[str, Any]:
        """Reset to defaults."""
        self.parameters = self.DEFAULT_PARAMS.copy()
        self._initialized = True
        self._compute()
        return self.get_state()

    def _load_audio(self) -> None:
        """Load real audio file from assets (matching PyQt5)."""
        audio_path = os.path.join(ASSETS_DIR, 'audio_sample.wav')

        try:
            # Load audio file
            sample_rate, audio_data = wavfile.read(audio_path)
            self._original_sr = sample_rate

            # Convert to float32 normalized to [-1, 1]
            if audio_data.dtype == np.int16:
                audio_data = audio_data.astype(np.float32) / 32768.0
            elif audio_data.dtype == np.int32:
                audio_data = audio_data.astype(np.float32) / 2147483648.0
            elif audio_data.dtype == np.uint8:
                audio_data = (audio_data.astype(np.float32) - 128) / 128.0

            # If stereo, convert to mono
            if len(audio_data.shape) > 1:
                audio_data = np.mean(audio_data, axis=1)

            # Limit duration to 3 seconds for performance
            max_samples = int(self.AUDIO_DURATION * self._original_sr)
            if len(audio_data) > max_samples:
                audio_data = audio_data[:max_samples]

            self._audio = audio_data.astype(np.float32)
            self._time = np.linspace(0, len(self._audio) / self._original_sr,
                                     len(self._audio), dtype=np.float32)

            print(f"Loaded audio: {len(self._audio)} samples at {self._original_sr} Hz")

        except Exception as e:
            print(f"Failed to load audio file: {e}. Using synthetic audio.")
            self._generate_synthetic_audio()

    def _generate_synthetic_audio(self) -> None:
        """Fallback: Generate synthetic audio signal."""
        num_samples = int(self.AUDIO_DURATION * self.ORIGINAL_SAMPLE_RATE)
        self._original_sr = self.ORIGINAL_SAMPLE_RATE
        self._time = np.linspace(0, self.AUDIO_DURATION, num_samples, dtype=np.float32)

        frequencies = [220, 440, 880, 1760, 3520]
        amplitudes = [0.4, 0.3, 0.15, 0.1, 0.05]

        self._audio = np.zeros(num_samples, dtype=np.float32)
        for freq, amp in zip(frequencies, amplitudes):
            self._audio += amp * np.sin(2 * np.pi * freq * self._time)

        envelope = np.exp(-self._time * 0.3)
        self._audio *= envelope

        max_val = np.max(np.abs(self._audio))
        if max_val > 0:
            self._audio = self._audio / max_val * 0.9

    def _load_test_image(self) -> None:
        """Load real test image from assets (matching PyQt5)."""
        image_path = os.path.join(ASSETS_DIR, 'test_image.jpg')

        try:
            # Load and convert to grayscale
            img = Image.open(image_path).convert('L')
            # Resize if too large (for performance)
            if img.size[0] > 512 or img.size[1] > 512:
                img.thumbnail((512, 512), Image.Resampling.LANCZOS)

            # Convert to numpy array normalized to [0, 1]
            self._original_image = np.array(img).astype(np.float32) / 255.0
            print(f"Loaded image: {self._original_image.shape}")

        except Exception as e:
            print(f"Failed to load image file: {e}. Using synthetic image.")
            self._generate_synthetic_image()

    def _generate_synthetic_image(self) -> None:
        """Fallback: Generate synthetic test image."""
        size = 256
        x = np.linspace(0, 1, size, dtype=np.float32)
        y = np.linspace(0, 1, size, dtype=np.float32)
        X, Y = np.meshgrid(x, y)

        gradient = (X + Y) / 2.0
        circular = 0.3 * np.sin(10 * np.sqrt((X - 0.5)**2 + (Y - 0.5)**2) * 2 * np.pi)

        self._original_image = np.clip(gradient + circular, 0, 1)

    def _compute(self) -> None:
        """Compute based on current demo mode."""
        mode = self.parameters["demo_mode"]

        if mode == "aliasing":
            self._compute_aliasing()
        elif mode == "quantization":
            self._compute_quantization()
        elif mode == "image":
            self._compute_image_quantization()

    # =========================================================================
    # ALIASING DEMO (matching PyQt5 aliasing_demo.py)
    # =========================================================================

    def _compute_aliasing(self) -> None:
        """Compute aliasing demo - downsampling with optional anti-aliasing."""
        factor = max(1, int(self.parameters["downsample_factor"]))
        use_aa = self.parameters["anti_aliasing"]

        # Apply anti-aliasing filter if enabled
        if use_aa and factor > 1:
            # Low-pass filter before downsampling
            nyquist = self._original_sr / 2.0
            cutoff = (self._original_sr / factor) / 2.0 * 0.95

            if cutoff < nyquist and cutoff > 0:
                try:
                    normalized_cutoff = cutoff / nyquist
                    b, a = signal.butter(8, normalized_cutoff, btype='low')
                    filtered = signal.filtfilt(b, a, self._audio)
                except Exception:
                    filtered = self._audio
            else:
                filtered = self._audio
        else:
            filtered = self._audio

        # Downsample
        self._downsampled = filtered[::factor].astype(np.float32)
        self._new_sr = self._original_sr / factor

        # Create downsampled time axis
        self._downsampled_time = np.arange(len(self._downsampled), dtype=np.float32) / self._new_sr

    # =========================================================================
    # QUANTIZATION DEMO (matching PyQt5 quantization_demo.py)
    # =========================================================================

    def _compute_quantization(self) -> None:
        """Compute audio quantization with selected method."""
        bits = int(self.parameters["bit_depth"])
        method = self.parameters["quant_method"]

        if method == "standard":
            self._quantized = self._uniform_quantize(self._audio, bits)
        elif method == "dither":
            self._quantized = self._dither_quantize(self._audio, bits)
        elif method == "roberts":
            self._quantized = self._roberts_quantize(self._audio, bits)
        else:
            self._quantized = self._uniform_quantize(self._audio, bits)

        # Calculate error
        self._quant_error = self._audio - self._quantized

        # Calculate SNR
        signal_power = np.mean(self._audio ** 2)
        noise_power = np.mean(self._quant_error ** 2)
        if noise_power > 1e-15:
            self._snr_db = 10 * np.log10(signal_power / noise_power)
        else:
            self._snr_db = float('inf')

    @staticmethod
    def _uniform_quantize(sig: np.ndarray, bits: int) -> np.ndarray:
        """Mid-rise uniform quantizer for [-1, 1] range."""
        levels = 2 ** bits
        step = 2.0 / levels
        quantized = np.round(sig / step) * step
        return np.clip(quantized, -1.0, 1.0).astype(np.float32)

    @staticmethod
    def _dither_quantize(sig: np.ndarray, bits: int) -> np.ndarray:
        """Quantizer with additive dither."""
        levels = 2 ** bits
        step = 2.0 / levels
        dither = np.random.uniform(-step/2.0, step/2.0, size=sig.shape).astype(np.float32)
        quantized = np.round((sig + dither) / step) * step
        return np.clip(quantized, -1.0, 1.0).astype(np.float32)

    @staticmethod
    def _roberts_quantize(sig: np.ndarray, bits: int) -> np.ndarray:
        """Robert's subtractive dither method."""
        levels = 2 ** bits
        step = 2.0 / levels
        dither = np.random.uniform(-step/2.0, step/2.0, size=sig.shape).astype(np.float32)
        quantized = np.round((sig + dither) / step) * step - dither
        return np.clip(quantized, -1.0, 1.0).astype(np.float32)

    # =========================================================================
    # IMAGE QUANTIZATION DEMO (matching PyQt5 image_demo.py)
    # =========================================================================

    def _compute_image_quantization(self) -> None:
        """Compute image quantization with all 3 methods."""
        bits = int(self.parameters["image_bits"])
        img = self._original_image

        # Apply all 3 methods
        self._standard_image = self._uniform_quantize_image(img, bits)
        self._dither_image = self._dither_quantize_image(img, bits)
        self._roberts_image = self._roberts_quantize_image(img, bits)

        # Calculate MSE for each
        self._mse_values = {
            "standard": float(np.mean((img - self._standard_image) ** 2)),
            "dither": float(np.mean((img - self._dither_image) ** 2)),
            "roberts": float(np.mean((img - self._roberts_image) ** 2)),
        }

    @staticmethod
    def _uniform_quantize_image(img: np.ndarray, bits: int) -> np.ndarray:
        """Mid-tread quantizer for [0, 1] image range."""
        levels = 2 ** bits
        if levels <= 1:
            return np.clip(np.round(img), 0.0, 1.0)
        step = 1.0 / (levels - 1)
        quantized = np.round(img / step) * step
        return np.clip(quantized, 0.0, 1.0).astype(np.float32)

    @staticmethod
    def _dither_quantize_image(img: np.ndarray, bits: int) -> np.ndarray:
        """Image quantizer with dither."""
        levels = 2 ** bits
        if levels <= 1:
            dither = np.random.uniform(-0.5, 0.5, size=img.shape).astype(np.float32)
            return np.clip(np.round(img + dither), 0.0, 1.0)
        step = 1.0 / (levels - 1)
        dither = np.random.uniform(-step/2.0, step/2.0, size=img.shape).astype(np.float32)
        quantized = np.round((img + dither) / step) * step
        return np.clip(quantized, 0.0, 1.0).astype(np.float32)

    @staticmethod
    def _roberts_quantize_image(img: np.ndarray, bits: int) -> np.ndarray:
        """Robert's method for images."""
        levels = 2 ** bits
        if levels <= 1:
            dither = np.random.uniform(-0.5, 0.5, size=img.shape).astype(np.float32)
            quantized = np.clip(np.round(img + dither), 0.0, 1.0)
            return np.clip(quantized - dither, 0.0, 1.0)
        step = 1.0 / (levels - 1)
        dither = np.random.uniform(-step/2.0, step/2.0, size=img.shape).astype(np.float32)
        quantized = np.round((img + dither) / step) * step - dither
        return np.clip(quantized, 0.0, 1.0).astype(np.float32)

    # =========================================================================
    # PLOT GENERATION
    # =========================================================================

    def get_plots(self) -> List[Dict[str, Any]]:
        """Generate plots based on current demo mode."""
        if not self._initialized:
            self.initialize()

        mode = self.parameters["demo_mode"]

        if mode == "aliasing":
            return self._get_aliasing_plots()
        elif mode == "quantization":
            return self._get_quantization_plots()
        elif mode == "image":
            return self._get_image_plots()
        else:
            return []

    def _get_aliasing_plots(self) -> List[Dict[str, Any]]:
        """Generate aliasing demo plots (3 plots like PyQt5)."""
        factor = self.parameters["downsample_factor"]
        use_aa = self.parameters["anti_aliasing"]

        nyquist_orig = self._original_sr / 2.0
        nyquist_new = self._new_sr / 2.0

        # Show a segment of 1000 samples for clarity
        chunk_size = 1000
        start_idx = len(self._audio) // 4  # Start from quarter for interesting part
        end_idx = min(start_idx + chunk_size, len(self._audio))

        time_segment = self._time[start_idx:end_idx]
        audio_segment = self._audio[start_idx:end_idx]

        # Downsampled segment
        down_start = start_idx // factor
        down_end = min(down_start + chunk_size // factor, len(self._downsampled))
        time_down = self._downsampled_time[down_start:down_end]
        audio_down = self._downsampled[down_start:down_end]

        # Compute spectra using Welch's method
        nperseg_orig = min(2048, len(self._audio))
        nperseg_down = min(512, len(self._downsampled))

        try:
            freqs_orig, psd_orig = signal.welch(self._audio, self._original_sr, nperseg=nperseg_orig)
            psd_orig_db = 10 * np.log10(psd_orig + 1e-12)
        except Exception:
            freqs_orig = np.array([0])
            psd_orig_db = np.array([-100])

        try:
            freqs_down, psd_down = signal.welch(self._downsampled, self._new_sr, nperseg=nperseg_down)
            psd_down_db = 10 * np.log10(psd_down + 1e-12)
        except Exception:
            freqs_down = np.array([0])
            psd_down_db = np.array([-100])

        plots = [
            # Plot 1: Original Signal
            {
                "id": "original_signal",
                "title": "Original Audio Signal",
                "data": [{
                    "x": time_segment.tolist(),
                    "y": audio_segment.tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "name": "Original Signal",
                    "line": {"color": self.COLOR_ORIGINAL, "width": 1.5},
                }],
                "layout": self._get_time_layout("Time (s)", "Amplitude"),
            },
            # Plot 2: Downsampled Signal
            {
                "id": "downsampled_signal",
                "title": f"Downsampled Signal ({factor}x, {'AA ON' if use_aa else 'AA OFF'})",
                "data": [{
                    "x": time_down.tolist(),
                    "y": audio_down.tolist(),
                    "type": "scatter",
                    "mode": "lines+markers",
                    "name": "Downsampled",
                    "line": {"color": self.COLOR_PROCESSED, "width": 1.5},
                    "marker": {"color": self.COLOR_PROCESSED, "size": 4},
                }],
                "layout": self._get_time_layout("Time (s)", "Amplitude"),
            },
            # Plot 3: Frequency Spectrum
            {
                "id": "frequency_spectrum",
                "title": f"Frequency Spectrum (Factor={factor}x, Filter={'ON' if use_aa else 'OFF'})",
                "data": [
                    {
                        "x": freqs_orig.tolist(),
                        "y": psd_orig_db.tolist(),
                        "type": "scatter",
                        "mode": "lines",
                        "name": "Original",
                        "line": {"color": self.COLOR_ORIGINAL, "width": 2},
                    },
                    {
                        "x": freqs_down.tolist(),
                        "y": psd_down_db.tolist(),
                        "type": "scatter",
                        "mode": "lines",
                        "name": "Downsampled",
                        "line": {"color": self.COLOR_PROCESSED, "width": 2},
                    },
                ],
                "layout": {
                    **self._get_base_layout(),
                    "xaxis": {
                        "title": "Frequency (Hz)",
                        "showgrid": True,
                        "gridcolor": "rgba(148, 163, 184, 0.1)",
                        "range": [0, min(10000, nyquist_orig + 1000)],
                    },
                    "yaxis": {
                        "title": "Magnitude (dB)",
                        "showgrid": True,
                        "gridcolor": "rgba(148, 163, 184, 0.1)",
                    },
                    "shapes": [
                        {
                            "type": "line",
                            "x0": nyquist_orig, "x1": nyquist_orig,
                            "y0": -120, "y1": 20,
                            "line": {"color": self.COLOR_ORIGINAL, "width": 2, "dash": "dash"},
                        },
                        {
                            "type": "line",
                            "x0": nyquist_new, "x1": nyquist_new,
                            "y0": -120, "y1": 20,
                            "line": {"color": self.COLOR_PROCESSED, "width": 2, "dash": "dash"},
                        },
                    ],
                    "annotations": [
                        {
                            "x": nyquist_orig, "y": 10,
                            "text": f"Orig Nyquist<br>{nyquist_orig:.0f} Hz",
                            "showarrow": True, "arrowhead": 2,
                            "ax": 50, "ay": -20,
                            "font": {"color": self.COLOR_ORIGINAL, "size": 10},
                        },
                        {
                            "x": nyquist_new, "y": 0,
                            "text": f"New Nyquist<br>{nyquist_new:.0f} Hz",
                            "showarrow": True, "arrowhead": 2,
                            "ax": -50, "ay": -30,
                            "font": {"color": self.COLOR_PROCESSED, "size": 10},
                        },
                    ],
                    "legend": {"orientation": "h", "y": 1.12, "x": 0.5, "xanchor": "center"},
                },
            },
        ]

        return plots

    def _get_quantization_plots(self) -> List[Dict[str, Any]]:
        """Generate audio quantization plots (4 plots like PyQt5)."""
        bits = self.parameters["bit_depth"]
        method = self.parameters["quant_method"]
        method_label = {"standard": "Standard Q", "dither": "With Dither", "roberts": "Robert's"}[method]

        # Show a segment
        chunk_size = 1000
        start_idx = len(self._audio) // 4
        end_idx = min(start_idx + chunk_size, len(self._audio))

        time_segment = self._time[start_idx:end_idx]
        audio_segment = self._audio[start_idx:end_idx]
        quant_segment = self._quantized[start_idx:end_idx]

        # Compute error spectrum
        nperseg = min(2048, len(self._quant_error))
        try:
            freqs_err, psd_err = signal.welch(self._quant_error, self._original_sr, nperseg=nperseg)
            psd_err_db = 10 * np.log10(psd_err + 1e-12)
        except Exception:
            freqs_err = np.array([0])
            psd_err_db = np.array([-100])

        # Quantization function - for dither/roberts show multiple realizations like PyQt5
        x_test = np.linspace(-1, 1, 500)
        quant_func_traces = []

        if method == "standard":
            # Standard quantizer - single trace
            y_test = self._uniform_quantize(x_test, bits)
            quant_func_traces.append({
                "x": x_test.tolist(),
                "y": y_test.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": "Quantizer",
                "line": {"color": self.COLOR_ERROR, "width": 2},
            })
        else:
            # Dither/Roberts - show 30 realizations with low opacity like PyQt5
            for i in range(30):
                if method == "dither":
                    y_test = self._dither_quantize(x_test, bits)
                else:
                    y_test = self._roberts_quantize(x_test, bits)
                quant_func_traces.append({
                    "x": x_test.tolist(),
                    "y": y_test.tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "name": "Quantizer" if i == 0 else None,
                    "showlegend": i == 0,
                    "line": {"color": self.COLOR_ERROR, "width": 0.5},
                    "opacity": 0.15,
                })

        # Add ideal line
        quant_func_traces.append({
            "x": [-1, 1],
            "y": [-1, 1],
            "type": "scatter",
            "mode": "lines",
            "name": "Ideal",
            "line": {"color": self.COLOR_ORIGINAL, "width": 1.5, "dash": "dash"},
        })

        snr_text = f"{self._snr_db:.1f} dB" if self._snr_db != float('inf') else "∞ dB"

        plots = [
            # Plot 1: Original Signal
            {
                "id": "original_audio",
                "title": "Original Audio Signal",
                "data": [{
                    "x": time_segment.tolist(),
                    "y": audio_segment.tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "name": "Original Signal",
                    "line": {"color": self.COLOR_ORIGINAL, "width": 1.5},
                }],
                "layout": self._get_time_layout("Time (s)", "Amplitude"),
            },
            # Plot 2: Quantized Signal
            {
                "id": "quantized_audio",
                "title": f"Quantized Signal ({bits} bits, {method_label})",
                "data": [{
                    "x": time_segment.tolist(),
                    "y": quant_segment.tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "name": "Quantized Signal",
                    "line": {"color": self.COLOR_ERROR, "width": 1.5},
                }],
                "layout": self._get_time_layout("Time (s)", "Amplitude"),
            },
            # Plot 3: Error Spectrum
            {
                "id": "error_spectrum",
                "title": f"Quantization Error Spectrum (SNR = {snr_text})",
                "data": [{
                    "x": freqs_err.tolist(),
                    "y": psd_err_db.tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "name": "Error Spectrum",
                    "line": {"color": self.COLOR_PROCESSED, "width": 1.5},
                }],
                "layout": {
                    **self._get_base_layout(),
                    "xaxis": {
                        "title": "Frequency (Hz)",
                        "showgrid": True,
                        "gridcolor": "rgba(148, 163, 184, 0.1)",
                        "range": [0, self._original_sr / 2],
                    },
                    "yaxis": {
                        "title": "Magnitude (dB)",
                        "showgrid": True,
                        "gridcolor": "rgba(148, 163, 184, 0.1)",
                    },
                    "legend": {"orientation": "h", "y": 1.1, "x": 0.5, "xanchor": "center"},
                },
            },
            # Plot 4: Quantization Function (with multiple realizations for dither/roberts)
            {
                "id": "quant_function",
                "title": f"{method_label} Function ({bits} bits, {2**bits} levels)",
                "data": quant_func_traces,
                "layout": {
                    **self._get_base_layout(),
                    "xaxis": {
                        "title": "Input Amplitude",
                        "showgrid": True,
                        "gridcolor": "rgba(148, 163, 184, 0.1)",
                        "range": [-1.1, 1.1],
                    },
                    "yaxis": {
                        "title": "Output Amplitude",
                        "showgrid": True,
                        "gridcolor": "rgba(148, 163, 184, 0.1)",
                        "range": [-1.1, 1.1],
                    },
                    "legend": {"orientation": "h", "y": 1.1, "x": 0.5, "xanchor": "center"},
                },
            },
        ]

        return plots

    def _get_image_plots(self) -> List[Dict[str, Any]]:
        """Generate image quantization plots."""
        bits = self.parameters["image_bits"]

        # Create heatmap plots for images
        # Custom grayscale colorscale: 0=black, 1=white
        grayscale = [[0, "rgb(0,0,0)"], [1, "rgb(255,255,255)"]]

        plots = [
            # Original image
            {
                "id": "original_image",
                "title": "Original (8-bit)",
                "data": [{
                    "z": self._original_image.tolist(),
                    "type": "heatmap",
                    "colorscale": grayscale,
                    "showscale": False,
                    "zmin": 0, "zmax": 1,
                }],
                "layout": self._get_image_layout(),
            },
            # Standard quantization
            {
                "id": "standard_image",
                "title": f"Standard Q ({bits} bits)",
                "data": [{
                    "z": self._standard_image.tolist(),
                    "type": "heatmap",
                    "colorscale": grayscale,
                    "showscale": False,
                    "zmin": 0, "zmax": 1,
                }],
                "layout": self._get_image_layout(),
            },
            # Dither
            {
                "id": "dither_image",
                "title": f"Dither ({bits} bits)",
                "data": [{
                    "z": self._dither_image.tolist(),
                    "type": "heatmap",
                    "colorscale": grayscale,
                    "showscale": False,
                    "zmin": 0, "zmax": 1,
                }],
                "layout": self._get_image_layout(),
            },
            # Robert's
            {
                "id": "roberts_image",
                "title": f"Robert's ({bits} bits)",
                "data": [{
                    "z": self._roberts_image.tolist(),
                    "type": "heatmap",
                    "colorscale": grayscale,
                    "showscale": False,
                    "zmin": 0, "zmax": 1,
                }],
                "layout": self._get_image_layout(),
            },
            # MSE Comparison Bar Chart
            {
                "id": "mse_comparison",
                "title": f"Error Comparison ({bits} bits)",
                "data": [{
                    "x": ["Standard Q", "Dither", "Robert's"],
                    "y": [
                        self._mse_values.get("standard", 0),
                        self._mse_values.get("dither", 0),
                        self._mse_values.get("roberts", 0),
                    ],
                    "type": "bar",
                    "marker": {
                        "color": [self.COLOR_PROCESSED, self.COLOR_DITHER, self.COLOR_ROBERTS],
                    },
                    "text": [
                        f"{self._mse_values.get('standard', 0):.6f}",
                        f"{self._mse_values.get('dither', 0):.6f}",
                        f"{self._mse_values.get('roberts', 0):.6f}",
                    ],
                    "textposition": "outside",
                }],
                "layout": {
                    **self._get_base_layout(),
                    "xaxis": {
                        "title": "Quantization Method",
                        "showgrid": False,
                    },
                    "yaxis": {
                        "title": "Mean Squared Error (MSE)",
                        "showgrid": True,
                        "gridcolor": "rgba(148, 163, 184, 0.1)",
                    },
                    "showlegend": False,
                },
            },
            # Histograms
            {
                "id": "histograms",
                "title": "Intensity Histograms",
                "data": [
                    {
                        "x": self._standard_image.ravel().tolist(),
                        "type": "histogram",
                        "name": "Standard",
                        "opacity": 0.7,
                        "marker": {"color": self.COLOR_PROCESSED},
                        "nbinsx": min(2**(bits+1), 64),
                    },
                    {
                        "x": self._dither_image.ravel().tolist(),
                        "type": "histogram",
                        "name": "Dither",
                        "opacity": 0.7,
                        "marker": {"color": self.COLOR_DITHER},
                        "nbinsx": min(2**(bits+1), 64),
                    },
                    {
                        "x": self._roberts_image.ravel().tolist(),
                        "type": "histogram",
                        "name": "Robert's",
                        "opacity": 0.7,
                        "marker": {"color": self.COLOR_ROBERTS},
                        "nbinsx": min(2**(bits+1), 64),
                    },
                ],
                "layout": {
                    **self._get_base_layout(),
                    "xaxis": {
                        "title": "Intensity",
                        "showgrid": True,
                        "gridcolor": "rgba(148, 163, 184, 0.1)",
                        "range": [0, 1],
                    },
                    "yaxis": {
                        "title": "Count",
                        "showgrid": True,
                        "gridcolor": "rgba(148, 163, 184, 0.1)",
                    },
                    "barmode": "overlay",
                    "legend": {"orientation": "h", "y": 1.15, "x": 0.5, "xanchor": "center"},
                },
            },
        ]

        return plots

    def _get_base_layout(self) -> Dict[str, Any]:
        """Base layout for all plots."""
        return {
            "margin": {"l": 60, "r": 30, "t": 50, "b": 50},
            "plot_bgcolor": "rgba(0,0,0,0)",
            "paper_bgcolor": "rgba(0,0,0,0)",
            "font": {"color": "#e2e8f0"},
            "uirevision": "constant",
        }

    def _get_time_layout(self, xlabel: str, ylabel: str) -> Dict[str, Any]:
        """Layout for time-domain plots."""
        return {
            **self._get_base_layout(),
            "xaxis": {
                "title": xlabel,
                "showgrid": True,
                "gridcolor": "rgba(148, 163, 184, 0.1)",
            },
            "yaxis": {
                "title": ylabel,
                "showgrid": True,
                "gridcolor": "rgba(148, 163, 184, 0.1)",
                "range": [-1.2, 1.2],
            },
            "legend": {"orientation": "h", "y": 1.1, "x": 0.5, "xanchor": "center"},
        }

    def _get_image_layout(self) -> Dict[str, Any]:
        """Layout for image heatmaps."""
        return {
            **self._get_base_layout(),
            "xaxis": {"visible": False, "scaleanchor": "y"},
            "yaxis": {"visible": False, "autorange": "reversed"},
            "margin": {"l": 10, "r": 10, "t": 40, "b": 10},
        }

    # =========================================================================
    # METADATA
    # =========================================================================

    def get_metadata(self) -> Dict[str, Any]:
        """Return simulation metadata."""
        mode = self.parameters["demo_mode"]

        base_metadata = {
            "simulation_type": "aliasing_quantization",
            "demo_mode": mode,
            "has_custom_viewer": True,
            "sticky_controls": True,
        }

        if mode == "aliasing":
            factor = self.parameters["downsample_factor"]
            # Send full quality audio (limited to 2 seconds for web transfer)
            max_samples_orig = int(2.0 * self._original_sr)
            audio_orig_limited = self._audio[:max_samples_orig]

            return {
                **base_metadata,
                "original_sr": int(self._original_sr),
                "new_sr": int(self._new_sr),
                "nyquist_original": self._original_sr / 2.0,
                "nyquist_new": self._new_sr / 2.0,
                "downsample_factor": factor,
                "anti_aliasing": self.parameters["anti_aliasing"],
                "aliasing_risk": self._new_sr < 2 * 3520,  # Highest frequency in our audio
                # Full quality audio for playback
                "audio_original": {
                    "data": audio_orig_limited.tolist(),
                    "sample_rate": int(self._original_sr),
                },
                "audio_processed": {
                    "data": self._downsampled.tolist(),
                    "sample_rate": int(self._new_sr),
                },
            }

        elif mode == "quantization":
            bits = self.parameters["bit_depth"]
            # Send full quality audio (limited to 2 seconds for web transfer)
            max_samples = int(2.0 * self._original_sr)
            audio_orig_limited = self._audio[:max_samples]
            quant_limited = self._quantized[:max_samples]

            return {
                **base_metadata,
                "bit_depth": bits,
                "levels": 2 ** bits,
                "method": self.parameters["quant_method"],
                "snr_db": self._snr_db if self._snr_db != float('inf') else None,
                "snr_text": f"{self._snr_db:.1f} dB" if self._snr_db != float('inf') else "∞ dB",
                # Full quality audio for playback
                "audio_original": {
                    "data": audio_orig_limited.tolist(),
                    "sample_rate": int(self._original_sr),
                },
                "audio_processed": {
                    "data": quant_limited.tolist(),
                    "sample_rate": int(self._original_sr),
                },
            }

        elif mode == "image":
            bits = self.parameters["image_bits"]
            return {
                **base_metadata,
                "bit_depth": bits,
                "levels": 2 ** bits,
                "mse_standard": self._mse_values.get("standard", 0),
                "mse_dither": self._mse_values.get("dither", 0),
                "mse_roberts": self._mse_values.get("roberts", 0),
            }

        return base_metadata

    def get_state(self) -> Dict[str, Any]:
        """Return current simulation state with metadata."""
        state = super().get_state()
        state["metadata"] = self.get_metadata()
        return state
