"""
Amplifier Topologies Simulator

Simulates various amplifier configurations including simple, feedback,
crossover (push-pull), and compensated modes.

Converted from PyQt5: amplifier_topologies/core/audio_processor.py
Matches PyQt5 parameters and behavior exactly.
"""

import numpy as np
from typing import Any, Dict, List, Optional
from .base_simulator import BaseSimulator


class AmplifierSimulator(BaseSimulator):
    """
    Amplifier simulation with different configurations.

    Parameters (matching PyQt5 exactly):
    - K: Forward gain (1-200, default 100)
    - F0: Power amp gain (8-12, default 10)
    - beta: Feedback factor (0.01-1.0, default 0.1)
    - VT: Threshold voltage for crossover distortion (fixed 0.7V)
    - amplifier_type: simple, feedback, crossover, compensated
    """

    # Configuration (matching PyQt5)
    SAMPLE_RATE = 44100
    DEFAULT_DURATION = 1.0
    DEFAULT_AMPLITUDE = 0.1
    DEFAULT_FREQUENCY = 40  # Hz - lower frequency to show ~2-3 clear cycles
    PLOT_WINDOW_SIZE = 4410  # ~100ms window to show clear waveforms
    INPUT_YLIM = (-0.15, 0.15)
    INITIAL_OUTPUT_LIMIT = 0.1

    # Colors (matching PyQt5)
    COLOR_INPUT = "#00A0FF"
    COLOR_OUTPUT = "#FF5733"
    COLOR_SIMPLE_GAIN = "#00A0FF"
    COLOR_FEEDBACK_GAIN = "#22c55e"  # green
    COLOR_IDEAL_GAIN = "#a855f7"  # purple
    COLOR_CURRENT_F0 = "#ef4444"  # red
    COLOR_XY_PLOT = "#FFC300"  # amber

    # Parameter schema (matching PyQt5 ranges exactly)
    PARAMETER_SCHEMA = {
        "K": {
            "type": "slider",
            "min": 1,
            "max": 200,
            "step": 1,
            "default": 100,
            "unit": "",
            "label": "K - Forward Gain",
            "group": "Amplifier",
        },
        "F0": {
            "type": "slider",
            "min": 8,
            "max": 12,
            "step": 0.01,
            "default": 10.0,
            "unit": "",
            "label": "F₀ - Power Amp Gain",
            "group": "Amplifier",
        },
        "beta": {
            "type": "slider",
            "min": 0.01,
            "max": 1.0,
            "step": 0.01,
            "default": 0.1,
            "unit": "",
            "label": "β - Feedback Factor",
            "group": "Feedback",
        },
        "amplifier_type": {
            "type": "select",
            "options": [
                {"value": "simple", "label": "1. Simple Amplifier"},
                {"value": "feedback", "label": "2. Feedback System"},
                {"value": "crossover", "label": "3. Crossover Distortion"},
                {"value": "compensated", "label": "4. Compensated System"},
            ],
            "default": "simple",
            "label": "Amplifier Configuration",
            "group": "Mode",
        },
        "input_source": {
            "type": "select",
            "options": [
                {"value": "pure_sine", "label": "Pure Sine Wave"},
                {"value": "rich_sine", "label": "Rich Sine (Harmonics)"},
            ],
            "default": "pure_sine",
            "label": "Input Source",
            "group": "Input",
        },
    }

    DEFAULT_PARAMS = {
        "K": 100,
        "F0": 10.0,
        "beta": 0.1,
        "amplifier_type": "simple",
        "input_source": "pure_sine",
    }

    # Fixed threshold voltage (matching PyQt5)
    VT = 0.7

    def __init__(self, simulation_id: str):
        super().__init__(simulation_id)
        self._time = None
        self._input_signal = None
        self._output_signal = None
        self._audio_data = None
        self._output_audio = None
        # Dynamic axis limits - only update when out of bounds
        self._output_y_limit = self.INITIAL_OUTPUT_LIMIT
        self._xy_plot_limit = 0.15
        self._gain_y_min = 0
        self._gain_y_max = 15

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
        # Reset all dynamic axis limits
        self._output_y_limit = self.INITIAL_OUTPUT_LIMIT
        self._xy_plot_limit = 0.15
        self._gain_y_min = 0
        self._gain_y_max = 15
        self._initialized = True
        self._compute()
        return self.get_state()

    def _generate_test_signal(self, sig_type: str = 'pure_sine') -> np.ndarray:
        """Generate demo test signals (matching PyQt5)."""
        t = np.linspace(0, self.DEFAULT_DURATION,
                       int(self.SAMPLE_RATE * self.DEFAULT_DURATION), endpoint=False)
        amplitude = self.DEFAULT_AMPLITUDE
        frequency = self.DEFAULT_FREQUENCY

        if sig_type == 'pure_sine':
            return amplitude * np.sin(2 * np.pi * frequency * t)
        elif sig_type == 'rich_sine':
            return amplitude * (
                0.7 * np.sin(2 * np.pi * frequency * t) +
                0.2 * np.sin(2 * np.pi * 2 * frequency * t) +
                0.1 * np.sin(2 * np.pi * 3 * frequency * t)
            )
        return amplitude * np.sin(2 * np.pi * frequency * t)

    def _apply_crossover_distortion(self, signal: np.ndarray, threshold: float) -> np.ndarray:
        """Apply crossover distortion (dead zone near zero) - matching PyQt5."""
        output = signal.copy()
        dead_zone_mask = np.abs(signal) < threshold
        output[signal > threshold] -= threshold
        output[signal < -threshold] += threshold
        output[dead_zone_mask] = 0
        return output

    def _compute(self) -> None:
        """Compute amplifier output based on mode (matching PyQt5 logic)."""
        K_val = self.parameters["K"]
        F0_val = self.parameters["F0"]
        beta_val = self.parameters["beta"]
        amp_type = self.parameters["amplifier_type"]
        input_source = self.parameters["input_source"]

        # Generate input signal
        self._audio_data = self._generate_test_signal(input_source)
        input_signal = self._audio_data.copy()

        # Process based on amplifier type (matching PyQt5 exactly)
        if amp_type == 'simple':
            output = input_signal * F0_val
        elif amp_type == 'feedback':
            gain = (K_val * F0_val) / (1 + beta_val * K_val * F0_val)
            output = input_signal * gain
        elif amp_type == 'crossover':
            amplified_signal = input_signal * K_val
            output = self._apply_crossover_distortion(amplified_signal, self.VT)
        else:  # compensated
            gain = (K_val * F0_val) / (1 + beta_val * K_val * F0_val)
            amplified_signal = input_signal * gain
            effective_VT = self.VT / K_val
            output = self._apply_crossover_distortion(amplified_signal, effective_VT)

        self._output_audio = output

        # Get plot data slice (matching PyQt5 behavior)
        plot_window_size = self.PLOT_WINDOW_SIZE
        start_index = 0
        end_index = min(plot_window_size, len(self._audio_data))

        self._input_signal = self._audio_data[start_index:end_index]
        self._output_signal = output[start_index:end_index]
        self._time = np.arange(len(self._input_signal)) / self.SAMPLE_RATE

        # Smart axis scaling - only update when data goes OUT OF BOUNDS
        if len(self._output_signal) > 0:
            max_output_amp = np.max(np.abs(self._output_signal))
            # Only expand if data exceeds current limit
            if max_output_amp > self._output_y_limit * 0.95:
                self._output_y_limit = max_output_amp * 1.2
            # Only shrink if data is much smaller AND we have headroom
            elif max_output_amp < self._output_y_limit * 0.3 and self._output_y_limit > 0.2:
                self._output_y_limit = max(max_output_amp * 2.0, 0.1)

        # Update XY plot limits - only when out of bounds
        if len(self._input_signal) > 0 and len(self._output_signal) > 0:
            max_xy = max(np.max(np.abs(self._input_signal)), np.max(np.abs(self._output_signal)))
            if max_xy > self._xy_plot_limit * 0.95:
                self._xy_plot_limit = max_xy * 1.2
            elif max_xy < self._xy_plot_limit * 0.3 and self._xy_plot_limit > 0.02:
                self._xy_plot_limit = max(max_xy * 2.0, 0.015)

    def _calculate_gains(self, K_val: float, beta_val: float, F0_range: np.ndarray):
        """Calculate gain curves (matching PyQt5 GainCalculator)."""
        gain_simple = F0_range
        gain_feedback = (K_val * F0_range) / (1 + beta_val * K_val * F0_range)
        ideal_gain = 1 / beta_val if beta_val > 0 else float('inf')
        return gain_simple, gain_feedback, ideal_gain

    # =========================================================================
    # Plot generation (4 plots matching PyQt5)
    # =========================================================================

    def get_plots(self) -> List[Dict[str, Any]]:
        """Generate Plotly plot dictionaries matching PyQt5 layout."""
        if not self._initialized:
            self.initialize()

        plots = [
            self._create_input_plot(),
            self._create_output_plot(),
            self._create_gain_curve_plot(),
            self._create_xy_plot(),
        ]
        return plots

    def _create_input_plot(self) -> Dict[str, Any]:
        """Create input signal time domain plot."""
        time_ms = self._time * 1000  # Convert to ms
        # Calculate x-axis range to show full window
        x_max = (self.PLOT_WINDOW_SIZE / self.SAMPLE_RATE) * 1000  # ms

        return {
            "id": "input_signal",
            "title": "Input Signal (Time Domain)",
            "data": [
                {
                    "x": time_ms.tolist(),
                    "y": self._input_signal.tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "name": "Input",
                    "line": {"color": self.COLOR_INPUT, "width": 2},
                },
            ],
            "layout": {
                "xaxis": {
                    "title": "Time (ms)",
                    "range": [0, x_max],
                    "showgrid": True,
                    "gridcolor": "rgba(148, 163, 184, 0.2)",
                    "zeroline": True,
                    "zerolinecolor": "rgba(148, 163, 184, 0.3)",
                    "fixedrange": False,
                },
                "yaxis": {
                    "title": "Amplitude",
                    "range": list(self.INPUT_YLIM),
                    "showgrid": True,
                    "gridcolor": "rgba(148, 163, 184, 0.2)",
                    "zeroline": True,
                    "zerolinecolor": "rgba(148, 163, 184, 0.3)",
                    "fixedrange": False,
                },
                "legend": {
                    "orientation": "h",
                    "yanchor": "bottom",
                    "y": 1.02,
                    "xanchor": "right",
                    "x": 1,
                },
                "margin": {"l": 60, "r": 30, "t": 50, "b": 50},
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)",
                "uirevision": "constant",
            },
        }

    def _create_output_plot(self) -> Dict[str, Any]:
        """Create output signal time domain plot with smart auto-scaling."""
        time_ms = self._time * 1000
        # Calculate x-axis range to show full window
        x_max = (self.PLOT_WINDOW_SIZE / self.SAMPLE_RATE) * 1000  # ms

        return {
            "id": "output_signal",
            "title": "Output Signal (Time Domain)",
            "data": [
                {
                    "x": time_ms.tolist(),
                    "y": self._output_signal.tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "name": "Output",
                    "line": {"color": self.COLOR_OUTPUT, "width": 2},
                },
            ],
            "layout": {
                "xaxis": {
                    "title": "Time (ms)",
                    "range": [0, x_max],
                    "showgrid": True,
                    "gridcolor": "rgba(148, 163, 184, 0.2)",
                    "zeroline": True,
                    "zerolinecolor": "rgba(148, 163, 184, 0.3)",
                    "fixedrange": False,
                },
                "yaxis": {
                    "title": "Amplitude",
                    "range": [-self._output_y_limit, self._output_y_limit],
                    "showgrid": True,
                    "gridcolor": "rgba(148, 163, 184, 0.2)",
                    "zeroline": True,
                    "zerolinecolor": "rgba(148, 163, 184, 0.3)",
                    "fixedrange": False,
                },
                "legend": {
                    "orientation": "h",
                    "yanchor": "bottom",
                    "y": 1.02,
                    "xanchor": "right",
                    "x": 1,
                },
                "margin": {"l": 60, "r": 30, "t": 50, "b": 50},
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)",
                "uirevision": "constant",
            },
        }

    def _create_gain_curve_plot(self) -> Dict[str, Any]:
        """Create gain vs F0 curves plot with smart auto-scaling."""
        K_val = self.parameters["K"]
        F0_val = self.parameters["F0"]
        beta_val = self.parameters["beta"]

        # F0 range matching PyQt5
        F0_min, F0_max = 8, 12
        F0_range = np.linspace(F0_min, F0_max, 100)

        gain_simple, gain_feedback, ideal_gain = self._calculate_gains(
            K_val, beta_val, F0_range
        )

        # Smart Y-axis scaling - only update when out of bounds
        data_y_min = min(min(gain_feedback), min(gain_simple)) * 0.9
        data_y_max = max(max(gain_simple), ideal_gain) * 1.1

        # Expand limits if data goes out of bounds
        if data_y_min < self._gain_y_min:
            self._gain_y_min = data_y_min
        if data_y_max > self._gain_y_max:
            self._gain_y_max = data_y_max
        # Shrink only if data is much smaller
        if data_y_max < self._gain_y_max * 0.4:
            self._gain_y_max = data_y_max * 1.5
        if data_y_min > self._gain_y_min * 2 and self._gain_y_min > 0:
            self._gain_y_min = data_y_min * 0.5

        traces = [
            # Simple gain curve
            {
                "x": F0_range.tolist(),
                "y": gain_simple.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": "Simple Gain",
                "line": {"color": self.COLOR_SIMPLE_GAIN, "width": 2, "dash": "dash"},
            },
            # Feedback gain curve
            {
                "x": F0_range.tolist(),
                "y": gain_feedback.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": "Feedback Gain",
                "line": {"color": self.COLOR_FEEDBACK_GAIN, "width": 2.5},
            },
            # Ideal gain (1/β) horizontal line
            {
                "x": [F0_min, F0_max],
                "y": [ideal_gain, ideal_gain],
                "type": "scatter",
                "mode": "lines",
                "name": f"Ideal (1/β = {ideal_gain:.1f})",
                "line": {"color": self.COLOR_IDEAL_GAIN, "width": 2, "dash": "dot"},
            },
            # Current F0 vertical line
            {
                "x": [F0_val, F0_val],
                "y": [self._gain_y_min, self._gain_y_max],
                "type": "scatter",
                "mode": "lines",
                "name": f"Current F₀ = {F0_val:.1f}",
                "line": {"color": self.COLOR_CURRENT_F0, "width": 1.5, "dash": "dashdot"},
            },
        ]

        return {
            "id": "gain_curve",
            "title": "Gain vs. F₀ Variation",
            "data": traces,
            "layout": {
                "xaxis": {
                    "title": "F₀",
                    "range": [F0_min, F0_max],
                    "showgrid": True,
                    "gridcolor": "rgba(148, 163, 184, 0.2)",
                    "zeroline": True,
                    "zerolinecolor": "rgba(148, 163, 184, 0.3)",
                    "fixedrange": False,
                },
                "yaxis": {
                    "title": "Gain",
                    "range": [self._gain_y_min, self._gain_y_max],
                    "showgrid": True,
                    "gridcolor": "rgba(148, 163, 184, 0.2)",
                    "zeroline": True,
                    "zerolinecolor": "rgba(148, 163, 184, 0.3)",
                    "fixedrange": False,
                },
                "legend": {
                    "orientation": "v",
                    "yanchor": "top",
                    "y": 0.98,
                    "xanchor": "left",
                    "x": 0.02,
                    "bgcolor": "rgba(15, 23, 42, 0.8)",
                    "bordercolor": "rgba(148, 163, 184, 0.2)",
                    "borderwidth": 1,
                    "font": {"size": 10},
                },
                "margin": {"l": 60, "r": 30, "t": 50, "b": 50},
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)",
                "uirevision": "constant",
            },
        }

    def _create_xy_plot(self) -> Dict[str, Any]:
        """Create output vs input (linearity check) plot with smart auto-scaling."""
        # Use stored limit (already computed in _compute with smart scaling)
        plot_limit = self._xy_plot_limit

        return {
            "id": "xy_linearity",
            "title": "Output vs. Input (Linearity)",
            "data": [
                # Ideal unity slope line
                {
                    "x": [-plot_limit, plot_limit],
                    "y": [-plot_limit, plot_limit],
                    "type": "scatter",
                    "mode": "lines",
                    "name": "Ideal (unity)",
                    "line": {"color": "rgba(128, 128, 128, 0.7)", "width": 1, "dash": "dash"},
                },
                # Actual output vs input
                {
                    "x": self._input_signal.tolist(),
                    "y": self._output_signal.tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "name": "Actual",
                    "line": {"color": self.COLOR_XY_PLOT, "width": 2},
                },
            ],
            "layout": {
                "xaxis": {
                    "title": "Input Amplitude",
                    "range": [-plot_limit, plot_limit],
                    "showgrid": True,
                    "gridcolor": "rgba(148, 163, 184, 0.2)",
                    "zeroline": True,
                    "zerolinecolor": "rgba(148, 163, 184, 0.3)",
                    "fixedrange": False,
                    "scaleanchor": "y",
                    "scaleratio": 1,
                },
                "yaxis": {
                    "title": "Output Amplitude",
                    "range": [-plot_limit, plot_limit],
                    "showgrid": True,
                    "gridcolor": "rgba(148, 163, 184, 0.2)",
                    "zeroline": True,
                    "zerolinecolor": "rgba(148, 163, 184, 0.3)",
                    "fixedrange": False,
                },
                "legend": {
                    "orientation": "h",
                    "yanchor": "bottom",
                    "y": 1.02,
                    "xanchor": "right",
                    "x": 1,
                },
                "margin": {"l": 60, "r": 30, "t": 50, "b": 50},
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)",
                "uirevision": "constant",
            },
        }

    def get_state(self) -> Dict[str, Any]:
        """Return current simulation state with extra info for info panel."""
        base_state = super().get_state()

        K_val = self.parameters["K"]
        F0_val = self.parameters["F0"]
        beta_val = self.parameters["beta"]
        amp_type = self.parameters["amplifier_type"]
        input_source = self.parameters["input_source"]

        # Calculate effective gain based on mode
        if amp_type == 'simple':
            effective_gain = F0_val
            gain_formula = f"G = F₀ = {F0_val:.1f}"
        elif amp_type == 'feedback':
            effective_gain = (K_val * F0_val) / (1 + beta_val * K_val * F0_val)
            gain_formula = f"G = KF₀/(1+βKF₀) = {effective_gain:.2f}"
        elif amp_type == 'crossover':
            effective_gain = K_val
            gain_formula = f"G = K = {K_val} (with crossover distortion)"
        else:  # compensated
            effective_gain = (K_val * F0_val) / (1 + beta_val * K_val * F0_val)
            gain_formula = f"G = KF₀/(1+βKF₀) = {effective_gain:.2f} (compensated)"

        # Ideal gain
        ideal_gain = 1 / beta_val if beta_val > 0 else float('inf')

        # Input source label
        input_labels = {
            'pure_sine': 'Pure Sine Wave',
            'rich_sine': 'Rich Sine (Harmonics)'
        }

        # Amplifier mode labels with descriptions
        mode_labels = {
            'simple': 'Simple Amplifier',
            'feedback': 'Feedback System',
            'crossover': 'Crossover Distortion',
            'compensated': 'Compensated System'
        }

        mode_descriptions = {
            'simple': 'Open-loop amplifier with gain = F₀',
            'feedback': 'Negative feedback reduces gain but improves linearity',
            'crossover': 'Push-pull output stage with dead zone (VT = 0.7V)',
            'compensated': 'Feedback + compensation reduces effective dead zone'
        }

        # Circuit diagram image path
        circuit_images = {
            'simple': '/assets/amplifier_topologies/simple.png',
            'feedback': '/assets/amplifier_topologies/feedback.png',
            'crossover': '/assets/amplifier_topologies/crossover.png',
            'compensated': '/assets/amplifier_topologies/compensated.png'
        }

        # Prepare audio data for playback (normalized to [-1, 1])
        # Input audio (original signal)
        audio_input = None
        if self._audio_data is not None:
            max_val_in = np.max(np.abs(self._audio_data))
            if max_val_in > 0:
                normalized_input = (self._audio_data / max_val_in * 0.8).tolist()
            else:
                normalized_input = self._audio_data.tolist()
            audio_input = {
                "data": normalized_input,
                "sample_rate": self.SAMPLE_RATE,
                "duration": len(self._audio_data) / self.SAMPLE_RATE
            }

        # Output audio (processed signal)
        audio_output = None
        if self._output_audio is not None:
            max_val = np.max(np.abs(self._output_audio))
            if max_val > 0:
                normalized_audio = (self._output_audio / max_val * 0.8).tolist()
            else:
                normalized_audio = self._output_audio.tolist()
            audio_output = {
                "data": normalized_audio,
                "sample_rate": self.SAMPLE_RATE,
                "duration": len(self._output_audio) / self.SAMPLE_RATE
            }

        base_state["metadata"] = {
            "simulation_type": "amplifier_topologies",
            "sticky_controls": True,
            "circuit_image": circuit_images.get(amp_type, ''),
            "has_audio": True,
            "audio_input": audio_input,
            "audio_output": audio_output,
            "system_info": {
                "mode": mode_labels.get(amp_type, amp_type),
                "mode_description": mode_descriptions.get(amp_type, ''),
                "effective_gain": round(effective_gain, 2),
                "gain_formula": gain_formula,
                "ideal_gain": round(ideal_gain, 2) if ideal_gain != float('inf') else "∞",
                "K": K_val,
                "F0": F0_val,
                "beta": beta_val,
                "VT": self.VT,
                "input_source": input_labels.get(input_source, input_source),
            },
            "current_params": {
                "K": K_val,
                "F0": F0_val,
                "beta": beta_val,
                "mode": amp_type,
            },
        }

        return base_state
