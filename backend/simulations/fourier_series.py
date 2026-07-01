"""
Fourier Series Simulator

Implements an interactive Fourier series visualization with:
- Comparison of original waveform vs Fourier approximation
- Individual Fourier components visualization
- Coefficient spectrum showing amplitude decay
- Support for Square and Triangle waves

Math extracted from: fourier_series/core/series.py, fourier_series/core/waveforms.py
"""

import numpy as np
from typing import Any, Dict, List, Optional
from .base_simulator import BaseSimulator


class FourierSeriesSimulator(BaseSimulator):
    """
    Fourier Series simulation.

    Parameters:
    - waveform: Type of wave (square, triangle)
    - harmonics: Number of harmonics (n)
    - frequency: Fundamental frequency (Hz)
    """

    # Configuration constants (from original visualizer.py)
    TIME_POINTS = 3000
    TIME_RANGE = (0, 4)  # Fixed time window in seconds

    # Fixed axis ranges
    AMPLITUDE_RANGE = [-1.5, 1.5]
    HARMONIC_AMPLITUDE_RANGE = [-1.4, 1.4]

    # Colors matching original
    ORIGINAL_COLOR = "#3b82f6"
    FOURIER_COLOR = "#ef4444"

    # Parameter schema
    PARAMETER_SCHEMA = {
        "waveform": {
            "type": "select",
            "options": [
                {"value": "square", "label": "Square Wave"},
                {"value": "triangle", "label": "Triangle Wave"},
            ],
            "default": "square",
        },
        "harmonics": {
            "type": "slider",
            "min": 1,
            "max": 50,
            "step": 1,
            "default": 10,
        },
        "frequency": {
            "type": "slider",
            "min": 0.5,
            "max": 5.0,
            "step": 0.5,
            "default": 1.0,
            "unit": "Hz",
        },
    }

    DEFAULT_PARAMS = {
        "waveform": "square",
        "harmonics": 10,
        "frequency": 1.0,
    }


    def __init__(self, simulation_id: str):
        super().__init__(simulation_id)
        self._t = None
        self._original = None
        self._approximation = None
        self._harmonics_data = None
        self._coefficients = None
        self._mse = 0.0
        self._max_error = 0.0

    def initialize(self, params: Optional[Dict[str, Any]] = None) -> None:
        """Initialize simulation with parameters."""
        self.parameters = self.DEFAULT_PARAMS.copy()
        if params:
            for name, value in params.items():
                if name in self.parameters:
                    self.parameters[name] = self._validate_param(name, value)
        self._initialized = True
        self._compute()

    def update_parameter(self, name: str, value: Any) -> Dict[str, Any]:
        """Update a single parameter and recompute."""
        if name in self.parameters:
            self.parameters[name] = self._validate_param(name, value)
            self._compute()
        return self.get_state()

    def reset(self) -> Dict[str, Any]:
        """Reset simulation to default parameters."""
        self.parameters = self.DEFAULT_PARAMS.copy()
        self._initialized = True
        self._compute()
        return self.get_state()

    def _compute(self) -> None:
        """Compute all signals based on current parameters."""
        waveform = self.parameters["waveform"]
        n = int(self.parameters["harmonics"])
        freq = self.parameters["frequency"]

        # Generate fixed time vector (axis stays constant)
        self._t = np.linspace(
            self.TIME_RANGE[0],
            self.TIME_RANGE[1],
            self.TIME_POINTS
        )
        t_scaled = self._t * freq

        # Generate original waveform
        if waveform == "square":
            self._original = self._square_wave(t_scaled)
        else:
            self._original = self._triangle_wave(t_scaled)

        # Odd-harmonic index array: basis = 1, 3, 5, ... for k = 1..n
        basis = 2 * np.arange(1, n + 1) - 1

        # Individual harmonic contributions, one row per odd harmonic
        harmonics = self._harmonics(t_scaled, basis, waveform)
        self._harmonics_data = list(harmonics)

        # Fourier series approximation is the sum of all harmonics
        self._approximation = harmonics.sum(axis=0)

        # Coefficients for spectrum (magnitudes shared with the harmonics)
        self._coefficients = self._compute_coefficients(basis, waveform)

        # Compute error metrics
        self._mse = np.mean((self._original - self._approximation) ** 2)
        self._max_error = np.max(np.abs(self._original - self._approximation))

    # =========================================================================
    # Math functions (extracted from fourier_series/core/waveforms.py)
    # =========================================================================

    @staticmethod
    def _square_wave(t: np.ndarray) -> np.ndarray:
        """Return a unit-amplitude square wave with period 1."""
        t_mod = np.mod(t, 1.0)
        return np.where(t_mod < 0.5, 1.0, -1.0)

    @staticmethod
    def _triangle_wave(t: np.ndarray) -> np.ndarray:
        """Return a unit-amplitude triangle wave with period 1."""
        t_mod = np.mod(t, 1.0)
        return np.where(t_mod < 0.5, -1 + 4 * t_mod, 3 - 4 * t_mod)

    @staticmethod
    def _amplitude(basis: np.ndarray, waveform: str) -> np.ndarray:
        """Coefficient magnitude |a_n| for each odd harmonic number `basis`.

        Square wave: |a_n| = 4/(n*pi); triangle wave: |a_n| = 8/(n^2*pi^2).
        Single source of truth shared by the harmonics and the spectrum.
        """
        if waveform == "square":
            return 4 / (np.pi * basis)
        return 8 / (np.pi**2 * basis**2)

    @classmethod
    def _harmonics(cls, t: np.ndarray, basis: np.ndarray, waveform: str) -> np.ndarray:
        """Return one harmonic contribution per odd harmonic, as rows.

        Square wave uses sine harmonics; triangle wave uses (negated) cosine
        harmonics. Amplitudes come from `_amplitude` so they stay consistent
        with the spectrum coefficients.
        """
        amp = cls._amplitude(basis, waveform)[:, None]
        angle = basis[:, None] * 2 * np.pi * t[None, :]
        if waveform == "square":
            return amp * np.sin(angle)
        return -amp * np.cos(angle)

    @classmethod
    def _compute_coefficients(cls, basis: np.ndarray, waveform: str) -> List[Dict]:
        """Compute Fourier coefficient magnitudes for each odd harmonic."""
        amplitudes = cls._amplitude(basis, waveform)
        coefficients = []
        for harmonic, amplitude in zip(basis, amplitudes):
            coefficients.append({
                "harmonic": int(harmonic),
                "amplitude": amplitude,
                "amplitude_db": 20 * np.log10(amplitude) if amplitude > 0 else -100,
            })
        return coefficients

    # =========================================================================
    # Plot generation
    # =========================================================================

    # Axis styling shared by every plot (grid + zeroline + interactive range).
    _AXIS_STYLE = {
        "showgrid": True,
        "gridcolor": "rgba(148, 163, 184, 0.1)",
        "zeroline": True,
        "zerolinecolor": "rgba(148, 163, 184, 0.3)",
        "fixedrange": False,
    }
    _LEGEND_STYLE = {
        "bgcolor": "rgba(30, 41, 59, 0.8)",
        "bordercolor": "rgba(148, 163, 184, 0.2)",
        "borderwidth": 1,
    }

    @classmethod
    def _base_layout(
        cls,
        x_title: str,
        x_range: List,
        y_title: str,
        y_range: List,
        legend: Dict[str, Any],
        uirevision: str,
    ) -> Dict[str, Any]:
        """Assemble the Plotly layout shared by all three plots."""
        return {
            "xaxis": {"title": x_title, **cls._AXIS_STYLE, "range": x_range},
            "yaxis": {"title": y_title, **cls._AXIS_STYLE, "range": y_range},
            "legend": {**legend, **cls._LEGEND_STYLE},
            "margin": {"l": 60, "r": 30, "t": 40, "b": 50},
            "plot_bgcolor": "rgba(0,0,0,0)",
            "paper_bgcolor": "rgba(0,0,0,0)",
            "uirevision": uirevision,
        }

    def get_plots(self) -> List[Dict[str, Any]]:
        """Generate Plotly plot dictionaries."""
        if not self._initialized:
            self.initialize()

        plots = [
            self._create_approximation_plot(),
            self._create_components_plot(),
            self._create_spectrum_plot(),
        ]
        return plots

    def get_state(self) -> Dict[str, Any]:
        """Return current simulation state with metadata for sticky controls."""
        base_state = super().get_state()

        # Add metadata with sticky_controls flag
        base_state["metadata"] = {
            "simulation_type": "fourier_series",
            "hub_slots": self.HUB_SLOTS,
            "hub_domain": self.HUB_DOMAIN,
            "hub_dimensions": self.HUB_DIMENSIONS,
            "sticky_controls": True,  # Keep control panel fixed when scrolling
            "series_info": {
                "waveform": self.parameters["waveform"],
                "harmonics": int(self.parameters["harmonics"]),
                "frequency": self.parameters["frequency"],
                "mse": round(self._mse, 6),
                "max_error": round(self._max_error, 4),
            },
        }

        return base_state

    def _create_approximation_plot(self) -> Dict[str, Any]:
        """Create comparison plot of original vs Fourier approximation."""
        n = int(self.parameters["harmonics"])
        waveform = self.parameters["waveform"].capitalize()

        layout = self._base_layout(
            x_title="Time (s)",
            x_range=[self.TIME_RANGE[0], self.TIME_RANGE[1]],
            y_title="Amplitude",
            y_range=self.AMPLITUDE_RANGE,
            legend={"orientation": "h", "yanchor": "top", "y": 0.99,
                    "xanchor": "right", "x": 0.99},
            uirevision="approximation",
        )
        layout["annotations"] = [
            {
                "x": 0.02,
                "y": 0.98,
                "xref": "paper",
                "yref": "paper",
                "text": f"MSE: {self._mse:.5f}<br>Max Error: {self._max_error:.4f}",
                "showarrow": False,
                "font": {"size": 10, "color": "#94a3b8"},
                "bgcolor": "rgba(30, 41, 59, 0.8)",
                "bordercolor": "rgba(148, 163, 184, 0.2)",
                "borderwidth": 1,
                "borderpad": 4,
            }
        ]

        return {
            "id": "approximation",
            "title": f"Fourier Approximation (n={n})",
            "data": [
                {
                    "x": self._t.tolist(),
                    "y": self._original.tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "name": f"Original {waveform}",
                    "line": {"color": self.ORIGINAL_COLOR, "width": 2.5},
                },
                {
                    "x": self._t.tolist(),
                    "y": self._approximation.tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "name": f"Fourier Series (n={n})",
                    "line": {"color": self.FOURIER_COLOR, "width": 2.5},
                },
            ],
            "layout": layout,
        }

    def _create_components_plot(self) -> Dict[str, Any]:
        """Create plot showing individual Fourier components."""
        n = int(self.parameters["harmonics"])
        colors = self._generate_colors(n)

        data = []
        display_n = min(n, 20)
        for k in range(display_n):
            harmonic = self._harmonics_data[k]
            data.append({
                "x": self._t.tolist(),
                "y": harmonic.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": f"n={2*k+1}",
                "line": {"color": colors[k], "width": 1.5},
                "opacity": 0.8,
            })

        return {
            "id": "components",
            "title": f"Individual Fourier Components (showing {display_n} of {n})",
            "data": data,
            "layout": self._base_layout(
                x_title="Time (s)",
                x_range=[self.TIME_RANGE[0], self.TIME_RANGE[1]],
                y_title="Amplitude",
                y_range=self.HARMONIC_AMPLITUDE_RANGE,
                legend={"orientation": "v", "yanchor": "top", "y": 0.98,
                        "xanchor": "right", "x": 0.98},
                uirevision="components",
            ),
        }

    def _create_spectrum_plot(self) -> Dict[str, Any]:
        """Create stem plot of Fourier coefficient magnitudes."""
        waveform = self.parameters["waveform"]
        harmonics = [c["harmonic"] for c in self._coefficients]
        amplitudes = [c["amplitude"] for c in self._coefficients]

        # Get max harmonic for x-axis range
        max_harmonic = harmonics[-1] if harmonics else 1

        # Build stem plot data (vertical lines + markers)
        stem_data = []
        for h, a in zip(harmonics, amplitudes):
            stem_data.append({
                "x": [h, h],
                "y": [0, a],
                "type": "scatter",
                "mode": "lines",
                "line": {"color": self.ORIGINAL_COLOR, "width": 2},
                "showlegend": False,
                "hoverinfo": "skip",
            })

        return {
            "id": "spectrum",
            "title": f"Fourier Coefficient Spectrum ({waveform.capitalize()} Wave)",
            "data": [
                *stem_data,
                {
                    "x": harmonics,
                    "y": amplitudes,
                    "type": "scatter",
                    "mode": "markers",
                    "name": "Coefficients",
                    "marker": {"color": self.ORIGINAL_COLOR, "size": 8},
                    "hovertemplate": "n=%{x}<br>|a<sub>n</sub>|=%{y:.4f}<extra></extra>",
                },
            ],
            "layout": self._base_layout(
                x_title="Harmonic Number (n)",
                x_range=[0, max_harmonic + 2],
                y_title="Coefficient Magnitude |aₙ|",
                y_range=[0, 1.5],
                legend={"orientation": "h", "yanchor": "top", "y": 0.99,
                        "xanchor": "right", "x": 0.99},
                uirevision="spectrum",
            ),
        }

    @staticmethod
    def _generate_colors(n: int) -> List[str]:
        """Generate dark-mode friendly colors for n items."""
        # Gradient from cyan to yellow (both visible on dark backgrounds)
        colors = []
        for i in range(n):
            t = i / max(n - 1, 1)
            # Interpolate from cyan (0, 200, 220) to yellow (253, 231, 37)
            r = int(0 + t * (253 - 0))
            g = int(200 + t * (231 - 200))
            b = int(220 + t * (37 - 220))
            colors.append(f"rgb({r},{g},{b})")
        return colors
