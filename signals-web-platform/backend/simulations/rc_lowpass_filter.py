"""
RC Lowpass Filter Simulator

Implements an interactive RC lowpass filter simulation with:
- Time domain view: Square wave input vs filtered output
- Frequency domain: Bode plot with harmonic markers

Math extracted from: rc_lowpass_filter/rc_lowpass/core/signals.py
"""

import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from .base_simulator import BaseSimulator


class RCLowpassSimulator(BaseSimulator):
    """
    RC Lowpass Filter simulation.

    Parameters:
    - frequency: Input square wave frequency (Hz)
    - rc_ms: RC time constant (milliseconds)
    - amplitude: Input signal amplitude (V)
    """

    # Configuration constants (from original settings.py)
    TIME_WINDOW_SECONDS = 0.05
    TIME_SAMPLES = 1000
    BODE_FREQUENCY_DECADES = (-1, 5)  # 0.1 Hz to 100 kHz
    MAX_HARMONIC_ORDER = 39

    # Fixed axis ranges (matching PyQt5 version)
    TIME_Y_RANGE = [-11, 11]  # Voltage range
    BODE_X_RANGE = [-1, 5]    # Log scale: 0.1 Hz to 100 kHz
    BODE_Y_RANGE = [-80, 30]  # dB range

    # Parameter schema matching catalog.py
    PARAMETER_SCHEMA = {
        "frequency": {
            "type": "slider",
            "min": 1,
            "max": 300,
            "step": 1,
            "default": 100,
            "unit": "Hz",
        },
        "rc_ms": {
            "type": "slider",
            "min": 0.1,
            "max": 10.0,
            "step": 0.01,
            "default": 1.0,
            "unit": "ms",
        },
        "amplitude": {
            "type": "slider",
            "min": 1.0,
            "max": 10.0,
            "step": 0.1,
            "default": 5.0,
            "unit": "V",
        },
    }

    DEFAULT_PARAMS = {
        "frequency": 100,
        "rc_ms": 1.0,
        "amplitude": 5.0,
    }

    def __init__(self, simulation_id: str):
        super().__init__(simulation_id)
        self._time = None
        self._input_signal = None
        self._output_signal = None
        self._bode_freqs = None
        self._bode_magnitude = None
        self._harmonic_freqs = None
        self._harmonic_db = None
        self._cutoff_freq = None

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
        frequency = self.parameters["frequency"]
        rc_seconds = self.parameters["rc_ms"] / 1000.0  # Convert ms to seconds
        amplitude = self.parameters["amplitude"]

        # Time domain computation
        self._time = np.linspace(0, self.TIME_WINDOW_SECONDS, self.TIME_SAMPLES)
        self._input_signal = self._square_wave(amplitude, frequency, self._time)
        self._output_signal = self._simulate_rc_output(self._time, self._input_signal, rc_seconds)

        # Frequency domain computation
        self._bode_freqs, self._bode_magnitude = self._bode_response(rc_seconds)
        self._harmonic_freqs, self._harmonic_db = self._square_wave_harmonics(frequency, amplitude)
        self._cutoff_freq = self._cutoff_frequency(rc_seconds)

    # =========================================================================
    # Math functions (extracted from rc_lowpass_filter/rc_lowpass/core/signals.py)
    # =========================================================================

    @staticmethod
    def _square_wave(amplitude: float, frequency: float, t: np.ndarray) -> np.ndarray:
        """Generate square wave signal."""
        return amplitude * np.sign(np.sin(2 * np.pi * frequency * t))

    @staticmethod
    def _simulate_rc_output(t: np.ndarray, input_signal: np.ndarray, rc_seconds: float) -> np.ndarray:
        """
        Simulate RC filter output using 4th-order Runge-Kutta integration.

        The RC lowpass filter differential equation:
        dV_out/dt = (V_in - V_out) / RC
        """
        output = np.zeros_like(input_signal)
        dt = t[1] - t[0]

        # Initial condition
        output[0] = 0.0

        # RK4 integration
        for i in range(len(t) - 1):
            v_out = output[i]
            v_in = input_signal[i]
            v_in_next = input_signal[i + 1]
            v_in_mid = (v_in + v_in_next) / 2

            # RK4 coefficients
            k1 = (v_in - v_out) / rc_seconds
            k2 = (v_in_mid - (v_out + k1 * dt / 2)) / rc_seconds
            k3 = (v_in_mid - (v_out + k2 * dt / 2)) / rc_seconds
            k4 = (v_in_next - (v_out + k3 * dt)) / rc_seconds

            output[i + 1] = v_out + (dt / 6) * (k1 + 2*k2 + 2*k3 + k4)

        return output

    def _bode_response(self, rc_seconds: float, num_points: int = 500) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate Bode magnitude response.

        Transfer function: H(jw) = 1 / (1 + jwRC)
        |H(jw)| = 1 / sqrt(1 + (wRC)^2)
        """
        f_min = 10 ** self.BODE_FREQUENCY_DECADES[0]
        f_max = 10 ** self.BODE_FREQUENCY_DECADES[1]
        frequencies = np.logspace(
            self.BODE_FREQUENCY_DECADES[0],
            self.BODE_FREQUENCY_DECADES[1],
            num_points
        )

        omega = 2 * np.pi * frequencies
        magnitude = 1.0 / np.sqrt(1 + (omega * rc_seconds) ** 2)
        magnitude_db = 20 * np.log10(magnitude)

        return frequencies, magnitude_db

    def _square_wave_harmonics(self, fundamental_hz: float, amplitude_v: float) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate harmonic content of a square wave.

        Square wave Fourier series has only odd harmonics:
        a_n = 4A/(n*pi) for odd n, 0 for even n
        """
        harmonics = np.arange(1, self.MAX_HARMONIC_ORDER + 1, 2)  # Odd harmonics only
        frequencies = harmonics * fundamental_hz

        # Amplitude of each harmonic
        amplitudes = (4 * amplitude_v) / (harmonics * np.pi)
        amplitude_db = 20 * np.log10(amplitudes)

        return frequencies, amplitude_db

    @staticmethod
    def _cutoff_frequency(rc_seconds: float) -> float:
        """Calculate -3dB cutoff frequency: f_c = 1/(2*pi*RC)"""
        return 1.0 / (2 * np.pi * rc_seconds)

    # =========================================================================
    # Plot generation
    # =========================================================================

    def get_plots(self) -> List[Dict[str, Any]]:
        """Generate Plotly plot dictionaries."""
        if not self._initialized:
            self.initialize()

        plots = [
            self._create_time_domain_plot(),
            self._create_bode_plot(),
        ]
        return plots

    def get_state(self) -> Dict[str, Any]:
        """Return current simulation state with metadata for sticky controls."""
        base_state = super().get_state()

        status_info = self._get_status()

        # Add metadata with sticky_controls flag
        base_state["metadata"] = {
            "simulation_type": "rc_lowpass_filter",
            "sticky_controls": True,  # Keep control panel fixed when scrolling
            "filter_info": {
                "frequency": self.parameters["frequency"],
                "rc_ms": self.parameters["rc_ms"],
                "amplitude": self.parameters["amplitude"],
                "cutoff_freq": round(self._cutoff_freq, 1),
                "status": status_info["status"],
                "ratio": round(status_info["ratio"], 2),
            },
        }

        return base_state

    def _get_status(self) -> Dict[str, Any]:
        """Calculate filter status like PyQt5 version."""
        frequency = self.parameters["frequency"]
        ratio = frequency / self._cutoff_freq if self._cutoff_freq > 0 else 0

        # Thresholds from original: passing=0.3, transitioning=1.5
        if ratio < 0.3:
            status = "PASSING"
            status_color = "#10b981"  # Green
            desc = "Input < Cutoff"
        elif ratio < 1.5:
            status = "TRANSITIONING"
            status_color = "#f59e0b"  # Amber
            desc = "Input ≈ Cutoff"
        else:
            status = "FILTERING"
            status_color = "#ef4444"  # Red
            desc = "Input > Cutoff"

        return {
            "status": status,
            "color": status_color,
            "description": desc,
            "ratio": ratio,
            "cutoff_freq": self._cutoff_freq,
        }

    def _create_time_domain_plot(self) -> Dict[str, Any]:
        """Create time domain plot showing input and output signals."""
        # Convert time to milliseconds for display
        time_ms = self._time * 1000

        return {
            "id": "time_domain",
            "title": "Time Domain Response",
            "data": [
                {
                    "x": time_ms.tolist(),
                    "y": self._input_signal.tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "name": "Input (Square Wave)",
                    "line": {"color": "#3b82f6", "width": 2.5},
                },
                {
                    "x": time_ms.tolist(),
                    "y": self._output_signal.tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "name": "Output (Filtered)",
                    "line": {"color": "#ef4444", "width": 2.5},
                },
            ],
            "layout": {
                "xaxis": {
                    "title": "Time (ms)",
                    "showgrid": True,
                    "gridcolor": "rgba(148, 163, 184, 0.1)",
                    "zeroline": True,
                    "zerolinecolor": "rgba(148, 163, 184, 0.3)",
                    "range": [0, self.TIME_WINDOW_SECONDS * 1000],  # Fixed: 0 to 50 ms
                    "fixedrange": False,
                },
                "yaxis": {
                    "title": "Voltage (V)",
                    "showgrid": True,
                    "gridcolor": "rgba(148, 163, 184, 0.1)",
                    "zeroline": True,
                    "zerolinecolor": "rgba(148, 163, 184, 0.3)",
                    "range": self.TIME_Y_RANGE,  # Fixed: -11 to 11 V
                    "fixedrange": False,
                },
                "legend": {
                    "orientation": "h",
                    "yanchor": "top",
                    "y": 0.99,
                    "xanchor": "right",
                    "x": 0.99,
                    "bgcolor": "rgba(30, 41, 59, 0.8)",
                },
                "margin": {"l": 60, "r": 30, "t": 50, "b": 50},
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)",
                "uirevision": "time_domain_axes",  # Preserves zoom/pan but allows title updates
            },
        }

    def _create_bode_plot(self) -> Dict[str, Any]:
        """Create Bode magnitude plot with harmonic markers (stem plot style like PyQt5)."""
        # Filter harmonics to only show those in plot range
        f_min = 10 ** self.BODE_FREQUENCY_DECADES[0]
        f_max = 10 ** self.BODE_FREQUENCY_DECADES[1]

        visible_mask = (self._harmonic_freqs >= f_min) & (self._harmonic_freqs <= f_max)
        visible_harmonic_freqs = self._harmonic_freqs[visible_mask]
        visible_harmonic_db = self._harmonic_db[visible_mask]

        # Build stem plot data (vertical lines for each harmonic like PyQt5)
        stem_data = []
        for freq, mag_db in zip(visible_harmonic_freqs, visible_harmonic_db):
            # Vertical line from bottom to harmonic magnitude
            stem_data.append({
                "x": [freq, freq],
                "y": [self.BODE_Y_RANGE[0], mag_db],
                "type": "scatter",
                "mode": "lines",
                "line": {"color": "#ef4444", "width": 2},
                "showlegend": False,
                "hoverinfo": "skip",
            })

        return {
            "id": "bode",
            "title": "Frequency Response (Bode Plot)",
            "data": [
                # Filter transfer function (blue line like PyQt5)
                {
                    "x": self._bode_freqs.tolist(),
                    "y": self._bode_magnitude.tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "name": "Filter Response",
                    "line": {"color": "#3b82f6", "width": 2.5},
                },
                # Cutoff frequency vertical line (as trace so it updates properly)
                {
                    "x": [self._cutoff_freq, self._cutoff_freq],
                    "y": [self.BODE_Y_RANGE[0], self.BODE_Y_RANGE[1]],
                    "type": "scatter",
                    "mode": "lines",
                    "name": f"Cutoff fc={self._cutoff_freq:.0f}Hz",
                    "line": {"color": "#10b981", "width": 2.5, "dash": "dash"},
                },
                # Stem lines for harmonics
                *stem_data,
                # Harmonic markers (red dots at top of stems)
                {
                    "x": visible_harmonic_freqs.tolist(),
                    "y": visible_harmonic_db.tolist(),
                    "type": "scatter",
                    "mode": "markers",
                    "name": "Square Wave Harmonics",
                    "marker": {"color": "#ef4444", "size": 8},
                },
            ],
            "layout": {
                "xaxis": {
                    "title": "Frequency (Hz)",
                    "type": "log",
                    "showgrid": True,
                    "gridcolor": "rgba(148, 163, 184, 0.1)",
                    "range": self.BODE_X_RANGE,  # Fixed: 0.1 Hz to 100 kHz
                    "fixedrange": False,
                },
                "yaxis": {
                    "title": "Magnitude (dB)",
                    "showgrid": True,
                    "gridcolor": "rgba(148, 163, 184, 0.1)",
                    "zeroline": True,
                    "zerolinecolor": "rgba(148, 163, 184, 0.3)",
                    "range": self.BODE_Y_RANGE,  # Fixed: -80 to 30 dB
                    "fixedrange": False,
                },
                "legend": {
                    "orientation": "h",
                    "yanchor": "top",
                    "y": 0.99,
                    "xanchor": "right",
                    "x": 0.99,
                    "bgcolor": "rgba(30, 41, 59, 0.8)",
                },
                "margin": {"l": 60, "r": 30, "t": 50, "b": 50},
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)",
                "uirevision": "bode_axes",
            },
        }
