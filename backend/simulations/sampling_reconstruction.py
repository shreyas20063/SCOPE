"""
Sampling & Reconstruction Explorer

Demonstrates time-domain sampling and reconstruction fidelity.
Students compare zero-order hold, linear interpolation, and ideal sinc
reconstruction to see how sampling rate affects signal recovery.
"""

from typing import Any, Dict, List, Optional
import numpy as np
from scipy.signal import chirp as scipy_chirp

from .base_simulator import BaseSimulator


class SamplingReconstructionSimulator(BaseSimulator):
    """
    Sampling & Reconstruction simulator.

    Two-panel visualization:
      Left: continuous signal with sample stems
      Right: three reconstruction methods overlaid with optional original
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
            "default": 10.0,
        },
        "time_window": {
            "type": "slider",
            "min": 0.5,
            "max": 5.0,
            "step": 0.1,
            "default": 2.0,
        },
        "show_zoh": {"type": "checkbox", "default": True},
        "show_linear": {"type": "checkbox", "default": True},
        "show_sinc": {"type": "checkbox", "default": True},
        "show_original": {"type": "checkbox", "default": True},
        "show_error": {"type": "checkbox", "default": False},
    }

    DEFAULT_PARAMS = {
        "signal_type": "sum_of_sines",
        "signal_frequency": 3.0,
        "sampling_frequency": 10.0,
        "time_window": 2.0,
        "show_zoh": True,
        "show_linear": True,
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
        fs = self.parameters["sampling_frequency"]
        return {
            "parameters": self.parameters.copy(),
            "plots": plots,
            "metadata": {
                "simulation_type": "sampling_reconstruction",
                "sampling_info": {
                    "sampling_frequency": round(fs, 2),
                    "sampling_interval": round(1.0 / fs, 4),
                    "nyquist_frequency": round(self._nyquist_freq, 2),
                    "max_signal_frequency": round(self._max_signal_freq, 2),
                    "num_samples": self._num_samples,
                    "is_above_nyquist": self._is_above_nyquist,
                    "status": "FAITHFUL" if self._is_above_nyquist else "ALIASING",
                },
                "reconstruction_mse": {
                    "zoh": round(self._mse_zoh, 6),
                    "linear": round(self._mse_linear, 6),
                    "sinc": round(self._mse_sinc, 6),
                },
            },
        }

    def get_plots(self) -> List[Dict[str, Any]]:
        if self._t_continuous is None:
            self._compute()

        plots = [
            self._create_sampling_plot(),
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
            data.append({
                "x": t_cont,
                "y": self._x_zoh.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": f"ZOH (MSE={self._mse_zoh:.4f})",
                "line": {"color": "#f59e0b", "width": 2},
            })

        if self.parameters["show_linear"]:
            data.append({
                "x": t_cont,
                "y": self._x_linear.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": f"Linear (MSE={self._mse_linear:.4f})",
                "line": {"color": "#10b981", "width": 2},
            })

        if self.parameters["show_sinc"]:
            data.append({
                "x": t_cont,
                "y": self._x_sinc.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": f"Sinc (MSE={self._mse_sinc:.4f})",
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
