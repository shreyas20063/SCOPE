"""
Signal Operations Explorer Simulator

Interactive exploration of signal transformations:
time-scaling f(at), time-shifting f(t-t0), time-reversal f(-t),
amplitude scaling A*f(t), and DC offset.

Supports even/odd decomposition and preset transformations.
"""

import numpy as np
from typing import Any, Dict, List, Optional

from .base_simulator import BaseSimulator


class SignalOperationsSimulator(BaseSimulator):
    """Simulator for signal transformation operations."""

    TIME_RANGE = (-5.0, 5.0)
    NUM_SAMPLES = 1000
    IMPULSE_SIGMA = 0.05

    PARAMETER_SCHEMA = {
        "signal_type": {
            "type": "select",
            "options": [
                {"value": "sine", "label": "Sine Wave"},
                {"value": "square", "label": "Square Wave"},
                {"value": "triangle", "label": "Triangle Wave"},
                {"value": "sawtooth", "label": "Sawtooth Wave"},
                {"value": "unit_step", "label": "Unit Step u(t)"},
                {"value": "impulse", "label": "Impulse δ(t)"},
                {"value": "exponential_decay", "label": "Exponential Decay"},
                {"value": "gaussian", "label": "Gaussian Pulse"},
                {"value": "sinc", "label": "Sinc Function"},
                {"value": "ramp", "label": "Ramp r(t)"},
            ],
            "default": "sine",
        },
        "frequency": {
            "type": "slider",
            "min": 0.5,
            "max": 10.0,
            "step": 0.1,
            "default": 1.0,
        },
        "amplitude": {
            "type": "slider",
            "min": -3.0,
            "max": 3.0,
            "step": 0.1,
            "default": 1.0,
        },
        "time_scale": {
            "type": "slider",
            "min": -3.0,
            "max": 3.0,
            "step": 0.1,
            "default": 1.0,
        },
        "time_shift": {
            "type": "slider",
            "min": -5.0,
            "max": 5.0,
            "step": 0.1,
            "default": 0.0,
        },
        "time_reverse": {
            "type": "checkbox",
            "default": False,
        },
        "dc_offset": {
            "type": "slider",
            "min": -2.0,
            "max": 2.0,
            "step": 0.1,
            "default": 0.0,
        },
        "show_decomposition": {
            "type": "checkbox",
            "default": False,
        },
    }

    DEFAULT_PARAMS = {
        "signal_type": "sine",
        "frequency": 1.0,
        "amplitude": 1.0,
        "time_scale": 1.0,
        "time_shift": 0.0,
        "time_reverse": False,
        "dc_offset": 0.0,
        "show_decomposition": False,
    }

    PRESETS = [
        {"label": "Identity", "params": {"amplitude": 1, "time_scale": 1, "time_shift": 0, "time_reverse": False, "dc_offset": 0}},
        {"label": "Time Reversal", "params": {"amplitude": 1, "time_scale": 1, "time_shift": 0, "time_reverse": True, "dc_offset": 0}},
        {"label": "Double Speed", "params": {"amplitude": 1, "time_scale": 2, "time_shift": 0, "time_reverse": False, "dc_offset": 0}},
        {"label": "Half Speed", "params": {"amplitude": 1, "time_scale": 0.5, "time_shift": 0, "time_reverse": False, "dc_offset": 0}},
        {"label": "Shift Right 2", "params": {"amplitude": 1, "time_scale": 1, "time_shift": 2, "time_reverse": False, "dc_offset": 0}},
        {"label": "Invert + Shift", "params": {"amplitude": -1, "time_scale": 1, "time_shift": 1, "time_reverse": False, "dc_offset": 0}},
        {"label": "Compress + Reverse", "params": {"amplitude": 1, "time_scale": 2, "time_shift": 0, "time_reverse": True, "dc_offset": 0}},
    ]

    def __init__(self, simulation_id: str):
        super().__init__(simulation_id)
        self._t: Optional[np.ndarray] = None
        self._original: Optional[np.ndarray] = None
        self._transformed: Optional[np.ndarray] = None
        self._even: Optional[np.ndarray] = None
        self._odd: Optional[np.ndarray] = None
        self._formula: str = "f(t)"

    def initialize(self, params: Optional[Dict[str, Any]] = None) -> None:
        self.parameters = {**self.DEFAULT_PARAMS, **(params or {})}
        for name, value in self.parameters.items():
            if name in self.PARAMETER_SCHEMA:
                self.parameters[name] = self._validate_param(name, value)
        self._initialized = True
        self._compute()

    def update_parameter(self, name: str, value: Any) -> Dict[str, Any]:
        if name in self.parameters:
            self.parameters[name] = self._validate_param(name, value)
        self._compute()
        return self.get_state()

    def get_plots(self) -> List[Dict[str, Any]]:
        if self._t is None:
            self._compute()

        y_arrays = [self._original, self._transformed]
        plots = [
            self._create_original_plot(y_arrays),
            self._create_transformed_plot(y_arrays),
        ]

        if self.parameters.get("show_decomposition", False) and self._even is not None:
            plots.append(self._create_decomposition_plot())

        return plots

    def get_state(self) -> Dict[str, Any]:
        state = super().get_state()
        state["metadata"] = {
            "simulation_type": "signal_operations",
            "formula_display": self._formula,
            "active_operations": self._get_active_operations(),
            "signal_metrics": self._compute_metrics() if self._t is not None else None,
            "presets": self.PRESETS,
        }
        return state

    # ── Computation ──────────────────────────────────────────────

    def _compute(self) -> None:
        """Compute original and transformed signals."""
        signal_type = self.parameters["signal_type"]
        frequency = self.parameters["frequency"]
        A = self.parameters["amplitude"]
        a = self.parameters["time_scale"]
        t0 = self.parameters["time_shift"]
        reverse = self.parameters["time_reverse"]
        dc = self.parameters["dc_offset"]

        self._t = np.linspace(self.TIME_RANGE[0], self.TIME_RANGE[1], self.NUM_SAMPLES)
        self._original = self._generate_signal(signal_type, frequency, self._t)

        # Transform chain: g(t) = A * f(a * (r(t) - t0)) + dc
        t_arg = -self._t if reverse else self._t.copy()
        if a != 0:
            t_arg = a * (t_arg - t0)
        else:
            t_arg = np.zeros_like(self._t)

        self._transformed = A * self._generate_signal(signal_type, frequency, t_arg) + dc
        self._formula = self._build_formula(A, a, t0, reverse, dc)

        # Even/odd decomposition of original signal
        if self.parameters.get("show_decomposition", False):
            f_neg = self._generate_signal(signal_type, frequency, -self._t)
            self._even = (self._original + f_neg) / 2.0
            self._odd = (self._original - f_neg) / 2.0
        else:
            self._even = None
            self._odd = None

    @staticmethod
    def _generate_signal(signal_type: str, frequency: float, t: np.ndarray) -> np.ndarray:
        """Generate a base signal evaluated at time values t."""
        omega = 2.0 * np.pi * frequency

        if signal_type == "sine":
            return np.sin(omega * t)
        elif signal_type == "square":
            return np.where(np.sin(omega * t) >= 0, 1.0, -1.0)
        elif signal_type == "triangle":
            return (2.0 / np.pi) * np.arcsin(np.sin(omega * t))
        elif signal_type == "sawtooth":
            phase = frequency * t
            return 2.0 * (phase - np.floor(phase + 0.5))
        elif signal_type == "unit_step":
            return np.where(t >= 0, 1.0, 0.0)
        elif signal_type == "impulse":
            sigma = SignalOperationsSimulator.IMPULSE_SIGMA
            return np.exp(-0.5 * (t / sigma) ** 2) / (sigma * np.sqrt(2.0 * np.pi))
        elif signal_type == "exponential_decay":
            alpha = frequency
            return np.exp(-alpha * np.abs(t)) * np.where(t >= 0, 1.0, 0.0)
        elif signal_type == "gaussian":
            sigma = 1.0 / (2.0 * np.pi * max(frequency, 0.1))
            return np.exp(-0.5 * (t / sigma) ** 2)
        elif signal_type == "sinc":
            return np.sinc(frequency * t)
        elif signal_type == "ramp":
            return t * np.where(t >= 0, 1.0, 0.0)
        return np.zeros_like(t)

    @staticmethod
    def _build_formula(A: float, a: float, t0: float, reverse: bool, dc: float) -> str:
        """Build human-readable formula string."""
        t_var = "-t" if reverse else "t"

        if a == 0.0:
            inner = "0"
        else:
            if t0 == 0.0:
                base = t_var
            elif t0 > 0:
                base = f"{t_var} - {t0:g}"
            else:
                base = f"{t_var} + {abs(t0):g}"

            if a == 1.0:
                inner = base
            elif a == -1.0:
                if reverse and t0 == 0.0:
                    inner = "t"
                else:
                    inner = f"-({base})" if t0 != 0.0 else f"-{t_var}"
            else:
                if t0 != 0.0:
                    inner = f"{a:g}({base})"
                else:
                    inner = f"{a:g}{t_var}"

        if A == 0.0:
            return f"{dc:g}" if dc != 0.0 else "0"
        elif A == 1.0:
            result = f"f({inner})"
        elif A == -1.0:
            result = f"-f({inner})"
        else:
            result = f"{A:g} \u00b7 f({inner})"

        if dc > 0:
            result = f"{result} + {dc:g}"
        elif dc < 0:
            result = f"{result} - {abs(dc):g}"

        return result

    # ── Metadata Helpers ──────────────────────────────────────────

    def _get_active_operations(self) -> List[Dict[str, Any]]:
        """Return list of active (non-identity) operations for badge display."""
        ops = []
        A = self.parameters["amplitude"]
        a = self.parameters["time_scale"]
        t0 = self.parameters["time_shift"]
        reverse = self.parameters["time_reverse"]
        dc = self.parameters["dc_offset"]

        if A != 1.0:
            ops.append({"name": "Amplitude", "symbol": f"A = {A:g}", "color": "#ef4444"})
        if a != 1.0:
            ops.append({"name": "Time Scale", "symbol": f"a = {a:g}", "color": "#f59e0b"})
        if t0 != 0.0:
            ops.append({"name": "Time Shift", "symbol": f"t\u2080 = {t0:g}", "color": "#3b82f6"})
        if reverse:
            ops.append({"name": "Time Reverse", "symbol": "f(\u2212t)", "color": "#8b5cf6"})
        if dc != 0.0:
            ops.append({"name": "DC Offset", "symbol": f"DC = {dc:g}", "color": "#10b981"})

        return ops

    def _compute_metrics(self) -> Dict[str, Any]:
        """Compute signal properties for display."""
        original_energy = float(np.trapz(np.abs(self._original) ** 2, self._t))
        transformed_energy = float(np.trapz(np.abs(self._transformed) ** 2, self._t))

        original_peak = float(np.max(np.abs(self._original)))
        transformed_peak = float(np.max(np.abs(self._transformed)))

        original_dc = float(np.mean(self._original))
        transformed_dc = float(np.mean(self._transformed))

        return {
            "original": {
                "energy": round(original_energy, 4),
                "peak_amplitude": round(original_peak, 4),
                "dc_component": round(original_dc, 4),
            },
            "transformed": {
                "energy": round(transformed_energy, 4),
                "peak_amplitude": round(transformed_peak, 4),
                "dc_component": round(transformed_dc, 4),
            },
            "energy_ratio": round(transformed_energy / max(original_energy, 1e-10), 4),
        }

    # ── Plot Construction ────────────────────────────────────────

    def _get_base_layout(self, xtitle: str, ytitle: str, y_data: Optional[List[np.ndarray]] = None) -> Dict[str, Any]:
        """Standard Plotly layout for signal plots with smart y-axis ranging."""
        yaxis_config: Dict[str, Any] = {
            "title": {"text": ytitle, "font": {"color": "#f1f5f9", "size": 13}},
            "gridcolor": "rgba(148,163,184,0.1)",
            "zerolinecolor": "rgba(148,163,184,0.3)",
            "color": "#94a3b8",
        }

        if y_data:
            all_y = np.concatenate([np.asarray(y) for y in y_data])
            y_min, y_max = float(np.nanmin(all_y)), float(np.nanmax(all_y))
            span = y_max - y_min
            padding = max(0.15 * span, 0.3)
            yaxis_config["range"] = [y_min - padding, y_max + padding]
            yaxis_config["autorange"] = False
        else:
            yaxis_config["autorange"] = True

        return {
            "xaxis": {
                "title": {"text": xtitle, "font": {"color": "#f1f5f9", "size": 13}},
                "range": list(self.TIME_RANGE),
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
                "color": "#94a3b8",
            },
            "yaxis": yaxis_config,
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "font": {"family": "Inter, sans-serif", "size": 12, "color": "#f1f5f9"},
            "margin": {"t": 45, "r": 25, "b": 55, "l": 60},
            "showlegend": True,
            "legend": {
                "font": {"color": "#94a3b8", "size": 11},
                "bgcolor": "rgba(0,0,0,0)",
            },
        }

    def _create_original_plot(self, y_arrays: List[np.ndarray]) -> Dict[str, Any]:
        """Plot: Original signal f(t)."""
        signal_name = self.parameters["signal_type"].replace("_", " ").title()
        return {
            "id": "original",
            "title": f"Original Signal: {signal_name}",
            "data": [
                {
                    "x": self._t.tolist(),
                    "y": self._original.tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "name": "f(t)",
                    "line": {"color": "#3b82f6", "width": 2.5},
                }
            ],
            "layout": self._get_base_layout("t (seconds)", "Amplitude", y_arrays),
        }

    def _create_transformed_plot(self, y_arrays: List[np.ndarray]) -> Dict[str, Any]:
        """Plot: Transformed signal with ghost original overlay."""
        return {
            "id": "transformed",
            "title": f"Transformed: {self._formula}",
            "data": [
                {
                    "x": self._t.tolist(),
                    "y": self._original.tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "name": "f(t) [original]",
                    "line": {"color": "#3b82f6", "width": 1.5, "dash": "dot"},
                    "opacity": 0.35,
                },
                {
                    "x": self._t.tolist(),
                    "y": self._transformed.tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "name": self._formula,
                    "line": {"color": "#ef4444", "width": 2.5},
                },
            ],
            "layout": self._get_base_layout("t (seconds)", "Amplitude", y_arrays),
        }

    def _create_decomposition_plot(self) -> Dict[str, Any]:
        """Plot: Even and odd decomposition of the original signal."""
        y_arrays = [self._even, self._odd]
        return {
            "id": "decomposition",
            "title": "Even / Odd Decomposition of f(t)",
            "data": [
                {
                    "x": self._t.tolist(),
                    "y": self._original.tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "name": "f(t) [original]",
                    "line": {"color": "#3b82f6", "width": 1.5, "dash": "dot"},
                    "opacity": 0.3,
                },
                {
                    "x": self._t.tolist(),
                    "y": self._even.tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "name": "Even: \u00bd[f(t) + f(\u2212t)]",
                    "line": {"color": "#10b981", "width": 2.5},
                },
                {
                    "x": self._t.tolist(),
                    "y": self._odd.tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "name": "Odd: \u00bd[f(t) \u2212 f(\u2212t)]",
                    "line": {"color": "#f59e0b", "width": 2.5},
                },
            ],
            "layout": self._get_base_layout("t (seconds)", "Amplitude", y_arrays),
        }
