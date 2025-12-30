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
    MAX_HARMONICS = 50

    # Fixed axis ranges
    AMPLITUDE_RANGE = [-1.5, 1.5]
    HARMONIC_AMPLITUDE_RANGE = [-1.4, 1.4]

    # Colors matching original
    ORIGINAL_COLOR = "#3b82f6"  # Blue
    FOURIER_COLOR = "#ef4444"   # Red
    COMPONENT_COLORS = None  # Will use viridis colormap

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
            self.TIME_RANGE[1],  # Fixed time range
            self.TIME_POINTS
        )
        # Time scaled by frequency - waveform moves within fixed axis
        t_scaled = self._t * freq

        # Generate original waveform
        if waveform == "square":
            self._original = self._square_wave(t_scaled)
        else:
            self._original = self._triangle_wave(t_scaled)

        # Compute Fourier series approximation
        self._approximation = self._fourier_series(t_scaled, n, waveform)

        # Compute individual harmonics
        self._harmonics_data = []
        for k in range(1, n + 1):
            if waveform == "square":
                harmonic = self._square_wave_harmonic(t_scaled, k)
            else:
                harmonic = self._triangle_wave_harmonic(t_scaled, k)
            self._harmonics_data.append(harmonic)

        # Compute coefficients for spectrum
        self._coefficients = self._compute_coefficients(n, waveform)

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
    def _square_wave_harmonic(t: np.ndarray, k: int) -> np.ndarray:
        """k-th harmonic contribution for the square wave Fourier series."""
        basis = 2 * k - 1  # Only odd harmonics
        return (4 / np.pi) * np.sin(basis * 2 * np.pi * t) / basis

    @staticmethod
    def _triangle_wave_harmonic(t: np.ndarray, k: int) -> np.ndarray:
        """k-th harmonic contribution for the triangle wave Fourier series."""
        basis = 2 * k - 1  # Only odd harmonics
        return -(8 / np.pi**2) * np.cos(basis * 2 * np.pi * t) / (basis**2)

    def _fourier_series(self, t: np.ndarray, n: int, waveform: str) -> np.ndarray:
        """Return the truncated Fourier series approximation."""
        result = np.zeros_like(t)
        for k in range(1, n + 1):
            if waveform == "square":
                result += self._square_wave_harmonic(t, k)
            else:
                result += self._triangle_wave_harmonic(t, k)
        return result

    @staticmethod
    def _compute_coefficients(n: int, waveform: str) -> List[Dict]:
        """Compute Fourier coefficients for each harmonic."""
        coefficients = []
        for k in range(1, n + 1):
            basis = 2 * k - 1  # Harmonic number
            if waveform == "square":
                # Square wave: a_n = 4/(n*pi) for odd n
                amplitude = 4 / (np.pi * basis)
            else:
                # Triangle wave: a_n = 8/(n^2*pi^2) for odd n
                amplitude = 8 / (np.pi**2 * basis**2)
            coefficients.append({
                "harmonic": basis,
                "amplitude": amplitude,
                "amplitude_db": 20 * np.log10(amplitude) if amplitude > 0 else -100,
            })
        return coefficients

    # =========================================================================
    # Plot generation
    # =========================================================================

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
            "layout": {
                "xaxis": {
                    "title": "Time (s)",
                    "showgrid": True,
                    "gridcolor": "rgba(148, 163, 184, 0.1)",
                    "zeroline": True,
                    "zerolinecolor": "rgba(148, 163, 184, 0.3)",
                    "range": [self.TIME_RANGE[0], self.TIME_RANGE[1]],
                    "fixedrange": False,
                },
                "yaxis": {
                    "title": "Amplitude",
                    "showgrid": True,
                    "gridcolor": "rgba(148, 163, 184, 0.1)",
                    "zeroline": True,
                    "zerolinecolor": "rgba(148, 163, 184, 0.3)",
                    "range": self.AMPLITUDE_RANGE,
                    "fixedrange": False,
                },
                "legend": {
                    "orientation": "h",
                    "yanchor": "top",
                    "y": 0.99,
                    "xanchor": "right",
                    "x": 0.99,
                    "bgcolor": "rgba(30, 41, 59, 0.8)",
                    "bordercolor": "rgba(148, 163, 184, 0.2)",
                    "borderwidth": 1,
                },
                "margin": {"l": 60, "r": 30, "t": 40, "b": 50},
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)",
                "annotations": [
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
                ],
                "uirevision": "approximation",
            },
        }

    def _create_components_plot(self) -> Dict[str, Any]:
        """Create plot showing individual Fourier components."""
        n = int(self.parameters["harmonics"])

        # Generate colors using viridis-like palette
        colors = self._generate_colors(n)

        data = []
        # Always show individual components (limit display for performance)
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
            "layout": {
                "xaxis": {
                    "title": "Time (s)",
                    "showgrid": True,
                    "gridcolor": "rgba(148, 163, 184, 0.1)",
                    "zeroline": True,
                    "zerolinecolor": "rgba(148, 163, 184, 0.3)",
                    "range": [self.TIME_RANGE[0], self.TIME_RANGE[1]],
                    "fixedrange": False,
                },
                "yaxis": {
                    "title": "Amplitude",
                    "showgrid": True,
                    "gridcolor": "rgba(148, 163, 184, 0.1)",
                    "zeroline": True,
                    "zerolinecolor": "rgba(148, 163, 184, 0.3)",
                    "range": self.HARMONIC_AMPLITUDE_RANGE,
                    "fixedrange": False,
                },
                "legend": {
                    "orientation": "v",
                    "yanchor": "top",
                    "y": 0.98,
                    "xanchor": "right",
                    "x": 0.98,
                    "bgcolor": "rgba(30, 41, 59, 0.8)",
                    "bordercolor": "rgba(148, 163, 184, 0.2)",
                    "borderwidth": 1,
                },
                "margin": {"l": 60, "r": 30, "t": 40, "b": 50},
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)",
                "uirevision": "components",
            },
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
            "layout": {
                "xaxis": {
                    "title": "Harmonic Number (n)",
                    "showgrid": True,
                    "gridcolor": "rgba(148, 163, 184, 0.1)",
                    "zeroline": True,
                    "zerolinecolor": "rgba(148, 163, 184, 0.3)",
                    "range": [0, max_harmonic + 2],
                    "fixedrange": False,
                },
                "yaxis": {
                    "title": "Coefficient Magnitude |aₙ|",
                    "showgrid": True,
                    "gridcolor": "rgba(148, 163, 184, 0.1)",
                    "zeroline": True,
                    "zerolinecolor": "rgba(148, 163, 184, 0.3)",
                    "range": [0, 1.5],
                    "fixedrange": False,
                },
                "legend": {
                    "orientation": "h",
                    "yanchor": "top",
                    "y": 0.99,
                    "xanchor": "right",
                    "x": 0.99,
                    "bgcolor": "rgba(30, 41, 59, 0.8)",
                    "bordercolor": "rgba(148, 163, 184, 0.2)",
                    "borderwidth": 1,
                },
                "margin": {"l": 60, "r": 30, "t": 40, "b": 50},
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)",
                "uirevision": "spectrum",
            },
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
