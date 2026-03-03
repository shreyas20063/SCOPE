"""
Sampling & Reconstruction Explorer

Demonstrates time-domain sampling, frequency-domain spectral copies, and
reconstruction fidelity. Students see the Nyquist criterion in action:
sample fast enough and sinc reconstruction recovers the signal perfectly;
too slow and spectral copies overlap, causing aliasing.
"""

from typing import Any, Dict, List, Optional
import numpy as np
from scipy.signal import chirp as scipy_chirp

from .base_simulator import BaseSimulator


class SamplingReconstructionSimulator(BaseSimulator):
    """
    Sampling & Reconstruction simulator.

    Three-panel visualization:
      1. Time domain — continuous signal with sample stems
      2. Frequency domain — original spectrum + spectral copies from sampling
      3. Reconstruction — ZOH / linear / sinc methods compared
    """

    NUM_CONTINUOUS = 2000  # High-resolution continuous signal points

    PARAMETER_SCHEMA = {
        "signal_type": {
            "type": "select",
            "options": [
                {"value": "sine", "label": "Pure Sine"},
                {"value": "sum_of_sines", "label": "Sum of Sines (f\u2080 + f\u2080+4 Hz)"},
                {"value": "square", "label": "Square Wave"},
                {"value": "triangle", "label": "Triangle Wave"},
                {"value": "chirp", "label": "Chirp (Frequency Sweep)"},
                {"value": "custom_multitone", "label": "Multi-tone (1 + 4 + 9 Hz)"},
            ],
            "default": "sum_of_sines",
        },
        "signal_frequency": {
            "type": "slider",
            "min": 0.5,
            "max": 20.0,
            "step": 0.1,
            "default": 3.0,
        },
        "sampling_frequency": {
            "type": "slider",
            "min": 1.0,
            "max": 100.0,
            "step": 0.5,
            "default": 20.0,
        },
        "time_window": {
            "type": "slider",
            "min": 0.5,
            "max": 5.0,
            "step": 0.1,
            "default": 2.0,
        },
        "show_zoh": {"type": "checkbox", "default": False},
        "show_linear": {"type": "checkbox", "default": False},
        "show_sinc": {"type": "checkbox", "default": True},
        "show_original": {"type": "checkbox", "default": True},
        "show_error": {"type": "checkbox", "default": False},
    }

    DEFAULT_PARAMS = {
        "signal_type": "sum_of_sines",
        "signal_frequency": 3.0,
        "sampling_frequency": 20.0,
        "time_window": 2.0,
        "show_zoh": False,
        "show_linear": False,
        "show_sinc": True,
        "show_original": True,
        "show_error": False,
    }

    def __init__(self, simulation_id: str):
        super().__init__(simulation_id)
        self._t_continuous: Optional[np.ndarray] = None
        self._x_continuous: Optional[np.ndarray] = None
        self._t_samples: Optional[np.ndarray] = None
        self._x_samples: Optional[np.ndarray] = None
        self._x_zoh: Optional[np.ndarray] = None
        self._x_linear: Optional[np.ndarray] = None
        self._x_sinc: Optional[np.ndarray] = None
        self._mse_zoh: float = 0.0
        self._mse_linear: float = 0.0
        self._mse_sinc: float = 0.0
        self._nyquist_freq: float = 0.0
        self._max_signal_freq: float = 0.0
        self._num_samples: int = 0
        self._is_above_nyquist: bool = False
        # Spectrum data
        self._freq_display: Optional[np.ndarray] = None
        self._mag_original: Optional[np.ndarray] = None
        self._mag_copies: Optional[np.ndarray] = None

    def initialize(self, params: Optional[Dict[str, Any]] = None) -> None:
        self.parameters = self.DEFAULT_PARAMS.copy()
        if params:
            for name, value in params.items():
                if name in self.PARAMETER_SCHEMA:
                    self.parameters[name] = self._validate_param(name, value)
        self._initialized = True
        self._compute()

    def update_parameter(self, name: str, value: Any) -> Dict[str, Any]:
        if name in self.parameters:
            self.parameters[name] = self._validate_param(name, value)
            self._compute()
        return self.get_state()

    def get_state(self) -> Dict[str, Any]:
        plots = self.get_plots()
        fs = float(self.parameters["sampling_frequency"])
        fmax = self._max_signal_freq
        nyquist = self._nyquist_freq
        ratio = nyquist / fmax if fmax > 0 else float("inf")

        return {
            "parameters": self.parameters.copy(),
            "plots": plots,
            "metadata": {
                "simulation_type": "sampling_reconstruction",
                "sampling_info": {
                    "sampling_frequency": round(fs, 2),
                    "sampling_interval": round(1.0 / fs, 4),
                    "nyquist_frequency": round(nyquist, 2),
                    "max_signal_frequency": round(fmax, 2),
                    "num_samples": self._num_samples,
                    "is_above_nyquist": self._is_above_nyquist,
                    "status": "FAITHFUL" if self._is_above_nyquist else "ALIASING",
                    "nyquist_ratio": round(ratio, 2),
                    "margin_hz": round(nyquist - fmax, 2),
                },
                "reconstruction_mse": {
                    "zoh": round(self._mse_zoh, 6),
                    "linear": round(self._mse_linear, 6),
                    "sinc": round(self._mse_sinc, 6),
                },
                "reconstruction_quality": {
                    "zoh": {
                        "mse": round(self._mse_zoh, 6),
                        "label": "Staircase Hold",
                        "quality": self._quality_label(self._mse_zoh),
                    },
                    "linear": {
                        "mse": round(self._mse_linear, 6),
                        "label": "Smooth Interpolation",
                        "quality": self._quality_label(self._mse_linear),
                    },
                    "sinc": {
                        "mse": round(self._mse_sinc, 6),
                        "label": "Perfect (Band-limited)",
                        "quality": self._quality_label(self._mse_sinc),
                    },
                },
            },
        }

    def get_plots(self) -> List[Dict[str, Any]]:
        if self._t_continuous is None:
            self._compute()

        plots = [
            self._create_sampling_plot(),
            self._create_spectrum_plot(),
            self._create_reconstruction_plot(),
        ]

        if self.parameters.get("show_error", False):
            plots.append(self._create_error_plot())

        return plots

    # -------------------------------------------------------------------------
    # Signal generation
    # -------------------------------------------------------------------------

    @staticmethod
    def _generate_signal(signal_type: str, f0: float, t: np.ndarray) -> np.ndarray:
        omega = 2.0 * np.pi * f0
        if signal_type == "sine":
            return np.sin(omega * t)
        elif signal_type == "sum_of_sines":
            return 0.7 * np.sin(omega * t) + 0.3 * np.sin(2.0 * np.pi * (f0 + 4.0) * t)
        elif signal_type == "square":
            return np.sign(np.sin(omega * t))
        elif signal_type == "triangle":
            return (2.0 / np.pi) * np.arcsin(np.sin(omega * t))
        elif signal_type == "chirp":
            t_end = t[-1] if len(t) > 0 else 1.0
            return scipy_chirp(t, f0, t_end, 4.0 * f0)
        elif signal_type == "custom_multitone":
            return (
                0.5 * np.sin(2.0 * np.pi * 1.0 * t)
                + 0.3 * np.sin(2.0 * np.pi * 4.0 * t)
                + 0.2 * np.sin(2.0 * np.pi * 9.0 * t)
            )
        return np.zeros_like(t)

    @staticmethod
    def _get_max_frequency(signal_type: str, f0: float) -> float:
        if signal_type == "sine":
            return f0
        elif signal_type == "sum_of_sines":
            return f0 + 4.0
        elif signal_type == "square":
            return f0 * 21  # Practical bandwidth (~21st harmonic)
        elif signal_type == "triangle":
            return f0 * 21
        elif signal_type == "chirp":
            return 4.0 * f0
        elif signal_type == "custom_multitone":
            return 9.0
        return f0

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _quality_label(mse: float) -> str:
        """Convert MSE to a human-readable quality label."""
        if mse < 0.001:
            return "Excellent"
        elif mse < 0.01:
            return "Good"
        elif mse < 0.05:
            return "Fair"
        return "Poor"

    def _get_component_frequencies(self) -> List[Dict[str, Any]]:
        """Return individual frequency components of the current signal."""
        signal_type = self.parameters["signal_type"]
        f0 = float(self.parameters["signal_frequency"])

        if signal_type == "sine":
            return [{"freq": f0, "label": f"f\u2080 = {f0} Hz", "amplitude": 1.0}]
        elif signal_type == "sum_of_sines":
            return [
                {"freq": f0, "label": f"f\u2081 = {f0} Hz", "amplitude": 0.7},
                {"freq": f0 + 4, "label": f"f\u2082 = {f0 + 4} Hz", "amplitude": 0.3},
            ]
        elif signal_type == "custom_multitone":
            return [
                {"freq": 1.0, "label": "1 Hz", "amplitude": 0.5},
                {"freq": 4.0, "label": "4 Hz", "amplitude": 0.3},
                {"freq": 9.0, "label": "9 Hz", "amplitude": 0.2},
            ]
        elif signal_type in ("square", "triangle"):
            harmonics = []
            for k in range(1, 22, 2):  # odd harmonics up to 21st
                amp = 1.0 / k if signal_type == "square" else 1.0 / (k * k)
                harmonics.append({
                    "freq": k * f0,
                    "label": f"{k}f\u2080 = {k * f0} Hz",
                    "amplitude": amp,
                })
            return harmonics
        elif signal_type == "chirp":
            return [{"freq": f0, "label": f"sweep {f0}\u2013{4 * f0} Hz", "amplitude": 1.0}]
        return []

    # -------------------------------------------------------------------------
    # Reconstruction methods
    # -------------------------------------------------------------------------

    @staticmethod
    def _reconstruct_zoh(
        t_samples: np.ndarray, x_samples: np.ndarray, t_continuous: np.ndarray
    ) -> np.ndarray:
        """Zero-order hold: hold each sample value until the next sample."""
        indices = np.searchsorted(t_samples, t_continuous, side="right") - 1
        indices = np.clip(indices, 0, len(x_samples) - 1)
        return x_samples[indices]

    @staticmethod
    def _reconstruct_linear(
        t_samples: np.ndarray, x_samples: np.ndarray, t_continuous: np.ndarray
    ) -> np.ndarray:
        """Piecewise linear interpolation between samples."""
        return np.interp(t_continuous, t_samples, x_samples)

    @staticmethod
    def _reconstruct_sinc(
        t_samples: np.ndarray,
        x_samples: np.ndarray,
        t_continuous: np.ndarray,
        T: float,
    ) -> np.ndarray:
        """Ideal band-limited reconstruction via sinc interpolation.

        x_r(t) = sum_n x[n] * sinc((t - nT) / T)
        """
        # Matrix: (num_continuous, num_samples)
        t_matrix = (t_continuous[:, np.newaxis] - t_samples[np.newaxis, :]) / T
        sinc_matrix = np.sinc(t_matrix)  # np.sinc(x) = sin(pi*x) / (pi*x)
        return sinc_matrix @ x_samples

    # -------------------------------------------------------------------------
    # Core computation
    # -------------------------------------------------------------------------

    def _compute(self) -> None:
        signal_type = self.parameters["signal_type"]
        f0 = float(self.parameters["signal_frequency"])
        fs = float(self.parameters["sampling_frequency"])
        t_window = float(self.parameters["time_window"])
        T = 1.0 / fs

        # 1. Continuous signal at high resolution
        self._t_continuous = np.linspace(0, t_window, self.NUM_CONTINUOUS)
        self._x_continuous = self._generate_signal(signal_type, f0, self._t_continuous)

        # 2. Discrete samples
        num_samples = int(np.floor(t_window * fs)) + 1
        self._t_samples = np.arange(num_samples) * T
        self._t_samples = self._t_samples[self._t_samples <= t_window]
        self._x_samples = self._generate_signal(signal_type, f0, self._t_samples)
        self._num_samples = len(self._t_samples)

        # 3. Reconstruct
        self._x_zoh = self._reconstruct_zoh(
            self._t_samples, self._x_samples, self._t_continuous
        )
        self._x_linear = self._reconstruct_linear(
            self._t_samples, self._x_samples, self._t_continuous
        )
        self._x_sinc = self._reconstruct_sinc(
            self._t_samples, self._x_samples, self._t_continuous, T
        )

        # 4. MSE
        self._mse_zoh = float(np.mean((self._x_continuous - self._x_zoh) ** 2))
        self._mse_linear = float(np.mean((self._x_continuous - self._x_linear) ** 2))
        self._mse_sinc = float(np.mean((self._x_continuous - self._x_sinc) ** 2))

        # 5. Nyquist metrics
        self._nyquist_freq = fs / 2.0
        self._max_signal_freq = self._get_max_frequency(signal_type, f0)
        self._is_above_nyquist = fs >= 2.0 * self._max_signal_freq

        # 6. Frequency spectrum
        self._compute_spectrum()

    def _compute_spectrum(self) -> None:
        """Compute baseband spectrum and tiled spectral copies for visualization."""
        fs = float(self.parameters["sampling_frequency"])
        t_window = float(self.parameters["time_window"])
        fmax = self._max_signal_freq

        # FFT of continuous signal (windowed for cleaner spectrum)
        N_fft = 4096
        fs_effective = self.NUM_CONTINUOUS / t_window
        window = np.hanning(self.NUM_CONTINUOUS)
        X = np.fft.rfft(self._x_continuous * window, n=N_fft)
        freqs_base = np.fft.rfftfreq(N_fft, d=1.0 / fs_effective)
        mag_base = 2.0 * np.abs(X) / self.NUM_CONTINUOUS

        # Display axis: 0 to enough to show first spectral copy
        display_max = max(2.0 * fs, 2.5 * fmax, 30.0)
        # Cap so we don't make the baseband invisible when fs is huge
        display_max = min(display_max, 5.0 * fs)
        num_display = 1500
        freq_display = np.linspace(0, display_max, num_display)

        # Original spectrum interpolated onto display grid
        mag_original = np.interp(freq_display, freqs_base, mag_base, right=0)

        # Spectral copies: sampling at fs tiles the spectrum at k*fs
        mag_copies = np.zeros_like(freq_display)
        num_copies = max(3, int(np.ceil(display_max / fs)) + 1)
        for k in range(-num_copies, num_copies + 1):
            shifted = np.abs(freq_display - k * fs)
            contrib = np.interp(shifted, freqs_base, mag_base, right=0)
            mag_copies += contrib

        self._freq_display = freq_display
        self._mag_original = mag_original
        self._mag_copies = mag_copies

    # -------------------------------------------------------------------------
    # Plot builders
    # -------------------------------------------------------------------------

    def _get_base_layout(self) -> Dict[str, Any]:
        return {
            "margin": {"l": 60, "r": 30, "t": 50, "b": 50},
            "plot_bgcolor": "rgba(0,0,0,0)",
            "paper_bgcolor": "rgba(0,0,0,0)",
            "font": {"color": "#e2e8f0", "family": "Inter, sans-serif", "size": 12},
        }

    def _create_sampling_plot(self) -> Dict[str, Any]:
        fs = self.parameters["sampling_frequency"]
        t_cont = self._t_continuous.tolist()
        x_cont = self._x_continuous.tolist()
        t_samp = self._t_samples.tolist()
        x_samp = self._x_samples.tolist()

        # Stem lines as a single trace with None separators
        stem_x: List = []
        stem_y: List = []
        for i in range(len(t_samp)):
            stem_x.extend([t_samp[i], t_samp[i], None])
            stem_y.extend([0, x_samp[i], None])

        data = [
            {
                "x": t_cont,
                "y": x_cont,
                "type": "scatter",
                "mode": "lines",
                "name": "x(t) continuous",
                "line": {"color": "#3b82f6", "width": 2},
            },
            {
                "x": stem_x,
                "y": stem_y,
                "type": "scatter",
                "mode": "lines",
                "name": "Sample stems",
                "line": {"color": "#ef4444", "width": 1.5},
                "showlegend": False,
                "hoverinfo": "skip",
            },
            {
                "x": t_samp,
                "y": x_samp,
                "type": "scatter",
                "mode": "markers",
                "name": f"x[n] (fs={fs:.1f} Hz, N={self._num_samples})",
                "marker": {"color": "#ef4444", "size": 8, "symbol": "circle"},
            },
        ]

        t_window = self.parameters["time_window"]
        layout = {
            **self._get_base_layout(),
            "xaxis": {
                "title": "Time (s)",
                "showgrid": True,
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
                "range": [0, t_window],
            },
            "yaxis": {
                "title": "Amplitude",
                "showgrid": True,
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
            },
            "legend": {"orientation": "h", "y": 1.12, "x": 0.5, "xanchor": "center"},
            "showlegend": True,
        }

        return {"id": "sampling", "title": "Sampling", "data": data, "layout": layout}

    def _create_spectrum_plot(self) -> Dict[str, Any]:
        """Frequency domain: original spectrum + spectral copies from sampling."""
        fs = float(self.parameters["sampling_frequency"])
        fmax = self._max_signal_freq
        nyquist = fs / 2.0
        is_safe = self._is_above_nyquist

        freq_list = self._freq_display.tolist()
        mag_orig_list = self._mag_original.tolist()
        mag_copies_list = self._mag_copies.tolist()

        data = [
            # Original spectrum (baseband)
            {
                "x": freq_list,
                "y": mag_orig_list,
                "type": "scatter",
                "mode": "lines",
                "fill": "tozeroy",
                "name": "Original X(f)",
                "line": {"color": "#3b82f6", "width": 2},
                "fillcolor": "rgba(59, 130, 246, 0.15)",
            },
            # Spectral copies from sampling
            {
                "x": freq_list,
                "y": mag_copies_list,
                "type": "scatter",
                "mode": "lines",
                "name": "Sampled copies",
                "line": {
                    "color": "#10b981" if is_safe else "#ef4444",
                    "width": 1.5,
                    "dash": "dot",
                },
                "fill": "tozeroy",
                "fillcolor": "rgba(16, 185, 129, 0.06)" if is_safe else "rgba(239, 68, 68, 0.06)",
            },
        ]

        # Vertical marker lines
        shapes = [
            # Nyquist frequency (fs/2)
            {
                "type": "line",
                "x0": nyquist, "x1": nyquist,
                "y0": 0, "y1": 1, "yref": "paper",
                "line": {
                    "color": "#10b981" if is_safe else "#ef4444",
                    "width": 2,
                    "dash": "dash",
                },
            },
            # Max signal frequency
            {
                "type": "line",
                "x0": fmax, "x1": fmax,
                "y0": 0, "y1": 1, "yref": "paper",
                "line": {"color": "#f59e0b", "width": 2, "dash": "dot"},
            },
            # Sampling frequency
            {
                "type": "line",
                "x0": fs, "x1": fs,
                "y0": 0, "y1": 1, "yref": "paper",
                "line": {"color": "#8b5cf6", "width": 1.5, "dash": "dashdot"},
            },
        ]

        # Aliasing zone shading
        if not is_safe:
            shapes.append({
                "type": "rect",
                "x0": 0, "x1": nyquist,
                "y0": 0, "y1": 1, "yref": "paper",
                "fillcolor": "rgba(239, 68, 68, 0.07)",
                "line": {"width": 0},
                "layer": "below",
            })

        annotations = [
            {
                "x": nyquist, "y": 1.05, "yref": "paper",
                "text": f"fs/2 = {nyquist:.1f}",
                "showarrow": False,
                "font": {"color": "#10b981" if is_safe else "#ef4444", "size": 10},
            },
            {
                "x": fmax, "y": 1.12, "yref": "paper",
                "text": f"fmax = {fmax:.1f}",
                "showarrow": False,
                "font": {"color": "#f59e0b", "size": 10},
            },
            {
                "x": fs, "y": 1.05, "yref": "paper",
                "text": f"fs = {fs:.1f}",
                "showarrow": False,
                "font": {"color": "#8b5cf6", "size": 10},
            },
        ]

        display_max = float(self._freq_display[-1])
        layout = {
            **self._get_base_layout(),
            "xaxis": {
                "title": "Frequency (Hz)",
                "showgrid": True,
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
                "range": [0, display_max],
            },
            "yaxis": {
                "title": "Magnitude",
                "showgrid": True,
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
            },
            "shapes": shapes,
            "annotations": annotations,
            "legend": {"orientation": "h", "y": 1.2, "x": 0.5, "xanchor": "center"},
            "showlegend": True,
        }

        return {"id": "spectrum", "title": "Frequency Spectrum", "data": data, "layout": layout}

    def _create_reconstruction_plot(self) -> Dict[str, Any]:
        t_cont = self._t_continuous.tolist()
        data: List[Dict[str, Any]] = []

        if self.parameters["show_original"]:
            data.append({
                "x": t_cont,
                "y": self._x_continuous.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": "Original x(t)",
                "line": {"color": "#3b82f6", "width": 1.5, "dash": "dot"},
                "opacity": 0.4,
            })

        if self.parameters["show_zoh"]:
            q = self._quality_label(self._mse_zoh)
            data.append({
                "x": t_cont,
                "y": self._x_zoh.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": f"ZOH \u2014 {q}",
                "line": {"color": "#f59e0b", "width": 2},
            })

        if self.parameters["show_linear"]:
            q = self._quality_label(self._mse_linear)
            data.append({
                "x": t_cont,
                "y": self._x_linear.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": f"Linear \u2014 {q}",
                "line": {"color": "#10b981", "width": 2},
            })

        if self.parameters["show_sinc"]:
            q = self._quality_label(self._mse_sinc)
            data.append({
                "x": t_cont,
                "y": self._x_sinc.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": f"Sinc \u2014 {q}",
                "line": {"color": "#8b5cf6", "width": 2},
            })

        t_window = self.parameters["time_window"]
        layout = {
            **self._get_base_layout(),
            "xaxis": {
                "title": "Time (s)",
                "showgrid": True,
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
                "range": [0, t_window],
            },
            "yaxis": {
                "title": "Amplitude",
                "showgrid": True,
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
            },
            "legend": {"orientation": "h", "y": 1.12, "x": 0.5, "xanchor": "center"},
            "showlegend": True,
        }

        return {
            "id": "reconstruction",
            "title": "Reconstruction",
            "data": data,
            "layout": layout,
        }

    def _create_error_plot(self) -> Dict[str, Any]:
        t_cont = self._t_continuous.tolist()
        data: List[Dict[str, Any]] = []

        if self.parameters["show_zoh"]:
            err = (self._x_continuous - self._x_zoh).tolist()
            data.append({
                "x": t_cont,
                "y": err,
                "type": "scatter",
                "mode": "lines",
                "name": "ZOH Error",
                "line": {"color": "#f59e0b", "width": 1.5},
            })

        if self.parameters["show_linear"]:
            err = (self._x_continuous - self._x_linear).tolist()
            data.append({
                "x": t_cont,
                "y": err,
                "type": "scatter",
                "mode": "lines",
                "name": "Linear Error",
                "line": {"color": "#10b981", "width": 1.5},
            })

        if self.parameters["show_sinc"]:
            err = (self._x_continuous - self._x_sinc).tolist()
            data.append({
                "x": t_cont,
                "y": err,
                "type": "scatter",
                "mode": "lines",
                "name": "Sinc Error",
                "line": {"color": "#8b5cf6", "width": 1.5},
            })

        t_window = self.parameters["time_window"]
        layout = {
            **self._get_base_layout(),
            "xaxis": {
                "title": "Time (s)",
                "showgrid": True,
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
                "range": [0, t_window],
            },
            "yaxis": {
                "title": "Error",
                "showgrid": True,
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
            },
            "legend": {"orientation": "h", "y": 1.12, "x": 0.5, "xanchor": "center"},
            "showlegend": True,
        }

        return {
            "id": "error",
            "title": "Reconstruction Error",
            "data": data,
            "layout": layout,
        }
