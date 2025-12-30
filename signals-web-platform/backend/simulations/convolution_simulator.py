"""
Convolution Simulator

Implements an interactive convolution visualization with:
- Signal x(t) or x[n]
- Impulse response h(t-τ) or h[n-k] (flipped and shifted)
- Product x(τ)h(t-τ) visualization
- Convolution result y(t) with current value marker
- Animation support for sliding convolution
- Custom expression input with SignalParser
- Demo presets for common signal pairs
- Block-step visualization mode
- Step navigation controls

Math extracted from: convolution/core/convolution.py, convolution/core/signals.py
"""

import numpy as np
from typing import Any, Dict, List, Optional, Callable, Tuple
from .base_simulator import BaseSimulator
from .signal_parser import SignalParser


class ConvolutionSimulator(BaseSimulator):
    """
    Convolution simulation with full feature parity to PyQt5 version.

    Parameters:
    - input_mode: "preset" or "custom" expression mode
    - signal1/signal2: Type of signals (preset mode)
    - custom_x/custom_h: Custom expressions (custom mode)
    - demo_preset: Selected demo pair (preset mode)
    - time_shift: Current time shift t for visualization
    - mode: Continuous or discrete
    - viz_style: "mathematical" or "block_step" visualization
    - animation_speed: Playback speed multiplier
    - running: Animation state
    """

    # Configuration constants
    CONTINUOUS_SAMPLES = 1000
    CONTINUOUS_RANGE = (-10, 15)  # Extended range for better visualization
    DISCRETE_RANGE = (-15, 25)

    # Colors
    SIGNAL_X_COLOR = "#3b82f6"   # Blue
    SIGNAL_H_COLOR = "#10b981"   # Green
    PRODUCT_COLOR = "#f59e0b"    # Amber
    RESULT_COLOR = "#ef4444"     # Red
    MARKER_COLOR = "#8b5cf6"     # Purple
    FLIP_COLOR = "#a855f7"       # Purple for flip step
    SHIFT_COLOR = "#f97316"      # Orange for shift step

    # Demo presets
    DEMO_PRESETS = {
        "continuous": {
            "rect_tri": {
                "label": "Rect + Triangle",
                "x": "rect(t)",
                "h": "tri(t)",
                "description": "Rectangular pulse convolved with triangular pulse"
            },
            "step_exp": {
                "label": "Step + Exponential",
                "x": "u(t)",
                "h": "exp(-t) * u(t)",
                "description": "Unit step convolved with exponential decay"
            },
            "rect_rect": {
                "label": "Rect + Rect → Triangle",
                "x": "rect(t)",
                "h": "rect(t)",
                "description": "Two rectangular pulses produce a triangle"
            },
            "exp_exp": {
                "label": "Exp + Exp",
                "x": "exp(-t) * u(t)",
                "h": "exp(-t) * u(t)",
                "description": "Two exponential decays"
            },
            "sinc_rect": {
                "label": "Sinc + Rect",
                "x": "sinc(t)",
                "h": "rect(t/2)",
                "description": "Sinc function with rectangular window"
            },
        },
        "discrete": {
            "simple_seq": {
                "label": "[1,2,1] * [1,1]",
                "x": "[1, 2, 1]",
                "h": "[1, 1]",
                "description": "Simple finite sequences"
            },
            "exp_diff": {
                "label": "Exp + Differentiator",
                "x": "0.9**n * u(n)",
                "h": "[1, -0.5]",
                "description": "Exponential with differentiator"
            },
            "moving_avg": {
                "label": "Moving Average",
                "x": "[1, 0, 1, 0, 1]",
                "h": "[0.25, 0.25, 0.25, 0.25]",
                "description": "Signal through 4-point moving average"
            },
            "impulse_response": {
                "label": "Impulse Response",
                "x": "[1]",
                "h": "[1, 0.5, 0.25, 0.125]",
                "description": "Impulse through decaying system"
            },
            "echo": {
                "label": "Echo Effect",
                "x": "[1, 2, 3, 2, 1]",
                "h": "[1, 0, 0, 0.5]",
                "description": "Signal with delayed echo"
            },
        },
    }

    # Parameter schema
    PARAMETER_SCHEMA = {
        # Input mode selector
        "input_mode": {
            "type": "select",
            "options": [
                {"value": "preset", "label": "Preset Signals"},
                {"value": "custom", "label": "Custom Expression"},
            ],
            "default": "preset",
            "group": "Input Mode",
        },
        # Signal type selector (continuous/discrete)
        "mode": {
            "type": "select",
            "options": [
                {"value": "continuous", "label": "Continuous"},
                {"value": "discrete", "label": "Discrete"},
            ],
            "default": "continuous",
            "group": "Signal Type",
        },
        # Demo preset selectors (one for each mode)
        "demo_preset_ct": {
            "type": "select",
            "options": [],  # Populated dynamically
            "default": "rect_tri",
            "group": "Demo Presets",
        },
        "demo_preset_dt": {
            "type": "select",
            "options": [],  # Populated dynamically
            "default": "simple_seq",
            "group": "Demo Presets",
        },
        # Preset signal selectors (for backward compatibility)
        "signal1": {
            "type": "select",
            "options": [
                {"value": "rect", "label": "Rectangular"},
                {"value": "triangle", "label": "Triangular"},
                {"value": "exp", "label": "Exponential"},
                {"value": "step", "label": "Step"},
            ],
            "default": "rect",
            "group": "Preset Signals",
        },
        "signal2": {
            "type": "select",
            "options": [
                {"value": "rect", "label": "Rectangular"},
                {"value": "triangle", "label": "Triangular"},
                {"value": "exp", "label": "Exponential"},
                {"value": "step", "label": "Step"},
            ],
            "default": "exp",
            "group": "Preset Signals",
        },
        "signal1_width": {
            "type": "slider",
            "min": 0.1,
            "max": 5.0,
            "step": 0.1,
            "default": 1.0,
            "label": "x(t) Width",
            "group": "Preset Signals",
        },
        "signal2_width": {
            "type": "slider",
            "min": 0.1,
            "max": 5.0,
            "step": 0.1,
            "default": 1.0,
            "label": "h(t) Width",
            "group": "Preset Signals",
        },
        # Custom expression inputs
        "custom_x": {
            "type": "expression",
            "default": "rect(t)",
            "placeholder": "e.g., exp(-t) * u(t), rect(t-1)",
            "label": "x(t) Expression",
            "group": "Custom Signals",
        },
        "custom_h": {
            "type": "expression",
            "default": "exp(-t) * u(t)",
            "placeholder": "e.g., u(t), tri(t/2)",
            "label": "h(t) Expression",
            "group": "Custom Signals",
        },
        # Time/index control
        "time_shift": {
            "type": "slider",
            "min": -8,
            "max": 12,
            "step": 0.1,
            "default": 0,
            "unit": "s",
            "label": "Time Shift (t₀)",
            "group": "Time Control",
        },
        # Visualization style
        "viz_style": {
            "type": "select",
            "options": [
                {"value": "mathematical", "label": "Mathematical (4 plots)"},
                {"value": "block_step", "label": "Block-Step (decomposition)"},
            ],
            "default": "mathematical",
            "group": "Visualization",
        },
        # Animation controls
        "animation_speed": {
            "type": "slider",
            "min": 0.1,
            "max": 4.0,
            "step": 0.1,
            "default": 1.0,
            "unit": "x",
            "label": "Animation Speed",
            "group": "Animation",
        },
        "running": {
            "type": "checkbox",
            "default": False,
            "label": "Play Animation",
            "group": "Animation",
        },
    }

    DEFAULT_PARAMS = {
        "input_mode": "preset",
        "mode": "continuous",
        "demo_preset_ct": "rect_tri",
        "demo_preset_dt": "simple_seq",
        "signal1": "rect",
        "signal2": "exp",
        "signal1_width": 1.0,
        "signal2_width": 1.0,
        "custom_x": "rect(t)",
        "custom_h": "exp(-t) * u(t)",
        "time_shift": 0,
        "viz_style": "mathematical",
        "animation_speed": 0.5,
        "running": False,
    }

    def __init__(self, simulation_id: str):
        super().__init__(simulation_id)
        self._parser = SignalParser()
        self._t = None
        self._tau = None
        self._x_t = None
        self._h_original = None  # Original h(τ) before flip/shift
        self._h_flipped = None   # h(-τ)
        self._h_shifted = None   # h(t₀ - τ)
        self._product = None
        self._y_result = None
        self._t_result = None
        self._current_y_value = 0.0
        self._x_expression = ""
        self._h_expression = ""
        self._error_message = None

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

            # When mode changes, load the appropriate preset for that mode
            if name == "mode":
                # Reset time to 0 when changing modes
                self.parameters["time_shift"] = 0
                # Load the preset for the new mode
                self._load_demo_preset()

            # When input_mode changes to preset, load the demo
            if name == "input_mode" and value == "preset":
                self._load_demo_preset()

            # When either preset selector changes, load it
            if name in ("demo_preset_ct", "demo_preset_dt"):
                self._load_demo_preset()

            self._compute()
        return self.get_state()

    def _load_demo_preset(self) -> None:
        """Load expressions from selected demo preset."""
        mode = self.parameters["mode"]

        # Get the correct preset ID based on mode
        if mode == "continuous":
            preset_id = self.parameters.get("demo_preset_ct", "rect_tri")
        else:
            preset_id = self.parameters.get("demo_preset_dt", "simple_seq")

        presets = self.DEMO_PRESETS.get(mode, {})

        if preset_id in presets:
            preset = presets[preset_id]
            self.parameters["custom_x"] = preset["x"]
            self.parameters["custom_h"] = preset["h"]

    def advance_frame(self) -> Dict[str, Any]:
        """Advance animation by one frame."""
        speed = self.parameters.get("animation_speed", 1.0)
        mode = self.parameters["mode"]

        # Determine step size based on mode and speed
        if mode == "discrete":
            step = 1 * speed
        else:
            step = 0.1 * speed

        current_t = self.parameters["time_shift"]
        new_t = current_t + step

        # Wrap around at boundaries
        max_t = self.PARAMETER_SCHEMA["time_shift"]["max"]
        min_t = self.PARAMETER_SCHEMA["time_shift"]["min"]

        if new_t > max_t:
            new_t = min_t

        self.parameters["time_shift"] = round(new_t, 2)
        self._compute()
        return self.get_state()

    def step_forward(self) -> Dict[str, Any]:
        """Move one step forward."""
        mode = self.parameters["mode"]
        step = 1 if mode == "discrete" else 0.2

        current_t = self.parameters["time_shift"]
        max_t = self.PARAMETER_SCHEMA["time_shift"]["max"]
        new_t = min(current_t + step, max_t)

        self.parameters["time_shift"] = round(new_t, 2)
        self._compute()
        return self.get_state()

    def step_backward(self) -> Dict[str, Any]:
        """Move one step backward."""
        mode = self.parameters["mode"]
        step = 1 if mode == "discrete" else 0.2

        current_t = self.parameters["time_shift"]
        min_t = self.PARAMETER_SCHEMA["time_shift"]["min"]
        new_t = max(current_t - step, min_t)

        self.parameters["time_shift"] = round(new_t, 2)
        self._compute()
        return self.get_state()

    def reset(self) -> Dict[str, Any]:
        """Reset animation to initial state while preserving current mode and signals."""
        # Preserve current mode and signal settings
        current_mode = self.parameters.get("mode", "continuous")
        current_input_mode = self.parameters.get("input_mode", "preset")
        current_preset_ct = self.parameters.get("demo_preset_ct", "rect_tri")
        current_preset_dt = self.parameters.get("demo_preset_dt", "simple_seq")
        current_custom_x = self.parameters.get("custom_x", "rect(t)")
        current_custom_h = self.parameters.get("custom_h", "exp(-t) * u(t)")

        # Reset to defaults
        self.parameters = self.DEFAULT_PARAMS.copy()

        # Restore preserved settings
        self.parameters["mode"] = current_mode
        self.parameters["input_mode"] = current_input_mode
        self.parameters["demo_preset_ct"] = current_preset_ct
        self.parameters["demo_preset_dt"] = current_preset_dt
        self.parameters["custom_x"] = current_custom_x
        self.parameters["custom_h"] = current_custom_h

        # Reset animation state
        self.parameters["time_shift"] = 0
        self.parameters["running"] = False

        self._initialized = True
        self._error_message = None
        self._compute()
        return self.get_state()

    def get_demo_presets(self) -> Dict[str, Any]:
        """Get available demo presets for current mode."""
        mode = self.parameters.get("mode", "continuous")
        presets = self.DEMO_PRESETS.get(mode, {})
        return {
            "mode": mode,
            "presets": [
                {"value": key, "label": val["label"], "description": val.get("description", "")}
                for key, val in presets.items()
            ]
        }

    def get_export_data(self) -> Dict[str, Any]:
        """Get data for CSV export."""
        mode = self.parameters["mode"]
        return {
            "mode": mode,
            "t": self._tau.tolist() if self._tau is not None else [],
            "x": self._x_t.tolist() if self._x_t is not None else [],
            "h": self._h_shifted.tolist() if self._h_shifted is not None else [],
            "y": self._y_result.tolist() if self._y_result is not None else [],
            "t_result": self._t_result.tolist() if self._t_result is not None else [],
            "current_t": self.parameters["time_shift"],
            "current_y": self._current_y_value,
            "x_expression": self._x_expression,
            "h_expression": self._h_expression,
        }

    def _compute(self) -> None:
        """Compute all signals based on current parameters."""
        self._error_message = None
        mode = self.parameters["mode"]
        input_mode = self.parameters["input_mode"]
        t0 = self.parameters["time_shift"]

        try:
            if input_mode == "custom":
                # Use custom expressions
                x_expr = self.parameters["custom_x"]
                h_expr = self.parameters["custom_h"]
            else:
                # Load from demo preset or use signal selectors
                if mode == "continuous":
                    preset_id = self.parameters.get("demo_preset_ct", "rect_tri")
                else:
                    preset_id = self.parameters.get("demo_preset_dt", "simple_seq")
                presets = self.DEMO_PRESETS.get(mode, {})

                if preset_id in presets:
                    x_expr = presets[preset_id]["x"]
                    h_expr = presets[preset_id]["h"]
                else:
                    # Fallback to signal selectors
                    signal1_type = self.parameters["signal1"]
                    signal2_type = self.parameters["signal2"]
                    width1 = self.parameters["signal1_width"]
                    width2 = self.parameters["signal2_width"]
                    x_expr = self._signal_type_to_expr(signal1_type, width1)
                    h_expr = self._signal_type_to_expr(signal2_type, width2)

            self._x_expression = x_expr
            self._h_expression = h_expr

            if mode == "continuous":
                self._compute_continuous_from_expr(x_expr, h_expr, t0)
            else:
                self._compute_discrete_from_expr(x_expr, h_expr, int(t0))

        except Exception as e:
            self._error_message = str(e)
            # Set defaults on error
            self._tau = np.linspace(-5, 10, 100)
            self._x_t = np.zeros(100)
            self._h_original = np.zeros(100)
            self._h_flipped = np.zeros(100)
            self._h_shifted = np.zeros(100)
            self._product = np.zeros(100)
            self._y_result = np.zeros(100)
            self._t_result = self._tau.copy()
            self._current_y_value = 0.0

    def _signal_type_to_expr(self, signal_type: str, width: float) -> str:
        """Convert signal type selector to expression."""
        if signal_type == "rect":
            return f"rect(t/{width})"
        elif signal_type == "triangle":
            return f"tri(t/{width})"
        elif signal_type == "exp":
            alpha = 1.0 / width
            return f"exp(-{alpha}*t) * u(t)"
        elif signal_type == "step":
            return "u(t)"
        else:
            return "0"

    def _compute_continuous_from_expr(self, x_expr: str, h_expr: str, t0: float) -> None:
        """Compute continuous-time convolution from expressions."""
        # Create time/tau axis
        self._tau = np.linspace(
            self.CONTINUOUS_RANGE[0],
            self.CONTINUOUS_RANGE[1],
            self.CONTINUOUS_SAMPLES
        )

        # Parse and create functions
        x_func = self._parser.create_function(x_expr, 't')
        h_func = self._parser.create_function(h_expr, 't')

        # Compute x(τ)
        self._x_t = np.asarray(x_func(self._tau), dtype=float)

        # Compute h(τ) - original
        self._h_original = np.asarray(h_func(self._tau), dtype=float)

        # Compute h(-τ) - flipped
        self._h_flipped = np.asarray(h_func(-self._tau), dtype=float)

        # Compute h(t₀ - τ) - flipped and shifted
        self._h_shifted = np.asarray(h_func(t0 - self._tau), dtype=float)

        # Compute product x(τ) * h(t₀ - τ)
        self._product = self._x_t * self._h_shifted

        # Compute convolution integral at t₀
        self._current_y_value = float(np.trapz(self._product, self._tau))

        # Compute full convolution for result plot
        self._compute_full_convolution_continuous(x_func, h_func)

    def _compute_discrete_from_expr(self, x_expr: str, h_expr: str, n0: int) -> None:
        """Compute discrete-time convolution from expressions."""
        # Create index axis
        n = np.arange(self.DISCRETE_RANGE[0], self.DISCRETE_RANGE[1] + 1)
        self._tau = n.astype(float)

        # Parse sequences
        x_seq, x_start = self._parser.parse_discrete_sequence(x_expr, n)
        h_seq, h_start = self._parser.parse_discrete_sequence(h_expr, n)

        # Create full arrays on the grid
        self._x_t = np.zeros(len(n), dtype=float)
        self._h_original = np.zeros(len(n), dtype=float)

        # Place x sequence
        for i, val in enumerate(x_seq):
            idx = x_start + i - int(n[0])
            if 0 <= idx < len(n):
                self._x_t[idx] = val

        # Place h sequence (original)
        for i, val in enumerate(h_seq):
            idx = h_start + i - int(n[0])
            if 0 <= idx < len(n):
                self._h_original[idx] = val

        # Compute h[-k] - flipped
        self._h_flipped = np.zeros(len(n), dtype=float)
        for i, val in enumerate(h_seq):
            idx = -(h_start + i) - int(n[0])
            if 0 <= idx < len(n):
                self._h_flipped[idx] = val

        # Compute h[n₀ - k] - flipped and shifted
        self._h_shifted = np.zeros(len(n), dtype=float)
        for i, val in enumerate(h_seq):
            idx = n0 - (h_start + i) - int(n[0])
            if 0 <= idx < len(n):
                self._h_shifted[idx] = val

        # Compute product x[k] * h[n₀ - k]
        self._product = self._x_t * self._h_shifted

        # Compute convolution sum at n₀
        self._current_y_value = float(np.sum(self._product))

        # Compute full convolution
        self._compute_full_convolution_discrete(x_seq, h_seq, x_start, h_start, n)

    def _compute_full_convolution_continuous(self, x_func: Callable, h_func: Callable) -> None:
        """Compute full convolution result for continuous signals."""
        t_range = np.linspace(
            self.CONTINUOUS_RANGE[0],
            self.CONTINUOUS_RANGE[1],
            300
        )
        self._t_result = t_range
        self._y_result = np.zeros_like(t_range)

        for i, t_val in enumerate(t_range):
            h_shifted = h_func(t_val - self._tau)
            product = self._x_t * h_shifted
            self._y_result[i] = np.trapz(product, self._tau)

    def _compute_full_convolution_discrete(
        self,
        x_seq: np.ndarray,
        h_seq: np.ndarray,
        x_start: int,
        h_start: int,
        n: np.ndarray
    ) -> None:
        """Compute full discrete convolution."""
        # Use numpy convolve
        y_conv = np.convolve(x_seq, h_seq, mode='full')
        y_start = x_start + h_start

        # Create result on grid
        self._t_result = n.astype(float)
        self._y_result = np.zeros(len(n), dtype=float)

        for i, val in enumerate(y_conv):
            idx = y_start + i - int(n[0])
            if 0 <= idx < len(n):
                self._y_result[idx] = val

    # =========================================================================
    # Plot generation
    # =========================================================================

    def get_plots(self) -> List[Dict[str, Any]]:
        """Generate Plotly plot dictionaries."""
        if not self._initialized:
            self.initialize()

        viz_style = self.parameters.get("viz_style", "mathematical")

        if viz_style == "block_step":
            return self._get_block_step_plots()
        else:
            return self._get_mathematical_plots()

    def _get_mathematical_plots(self) -> List[Dict[str, Any]]:
        """Generate standard 4-plot mathematical view."""
        plots = [
            self._create_signal_x_plot(),
            self._create_signal_h_plot(),
            self._create_product_plot(),
            self._create_result_plot(),
        ]
        return plots

    def _get_block_step_plots(self) -> List[Dict[str, Any]]:
        """Generate block-step decomposition visualization."""
        mode = self.parameters["mode"]
        t0 = self.parameters["time_shift"]
        is_discrete = mode == "discrete"

        plots = [
            self._create_original_signals_plot(),
            self._create_flip_plot(),
            self._create_shift_plot(),
            self._create_multiply_plot(),
            self._create_integrate_plot(),
        ]
        return plots

    def _create_signal_x_plot(self) -> Dict[str, Any]:
        """Create plot for input signal x(τ)."""
        mode = self.parameters["mode"]
        is_discrete = mode == "discrete"

        title = f"x({'n' if is_discrete else 'τ'})"
        if self._x_expression:
            title = f"x = {self._x_expression}"

        data_traces = []

        if is_discrete:
            # Create stem plot for discrete
            x_vals = self._tau.tolist()
            y_vals = self._x_t.tolist()
            stem_x, stem_y = [], []
            for xi, yi in zip(x_vals, y_vals):
                stem_x.extend([xi, xi, None])
                stem_y.extend([0, yi, None])
            data_traces.append({
                "x": stem_x, "y": stem_y,
                "type": "scatter", "mode": "lines",
                "line": {"color": self.SIGNAL_X_COLOR, "width": 1.5},
                "showlegend": False,
            })
            data_traces.append({
                "x": x_vals, "y": y_vals,
                "type": "scatter", "mode": "markers",
                "name": "x[k]",
                "marker": {"size": 8, "color": self.SIGNAL_X_COLOR},
            })
        else:
            data_traces.append({
                "x": self._tau.tolist(),
                "y": self._x_t.tolist(),
                "type": "scatter", "mode": "lines",
                "name": "x(τ)",
                "line": {"color": self.SIGNAL_X_COLOR, "width": 2.5},
            })

        return {
            "id": "signal_x",
            "title": title,
            "data": data_traces,
            "layout": self._get_standard_layout(
                "τ" if not is_discrete else "k",
                [-0.5, 1.5]
            ),
        }

    def _create_signal_h_plot(self) -> Dict[str, Any]:
        """Create plot for h(t₀ - τ) (flipped and shifted)."""
        mode = self.parameters["mode"]
        t0 = self.parameters["time_shift"]
        is_discrete = mode == "discrete"

        if is_discrete:
            title = f"h[{int(round(t0))} - k]"
        else:
            title = f"h({t0:.1f} - τ)"

        if self._h_expression:
            title = f"h = {self._h_expression}, shifted"

        data_traces = []

        if is_discrete:
            # Create stem plot for discrete
            x_vals = self._tau.tolist()
            y_vals = self._h_shifted.tolist()
            stem_x, stem_y = [], []
            for xi, yi in zip(x_vals, y_vals):
                stem_x.extend([xi, xi, None])
                stem_y.extend([0, yi, None])
            data_traces.append({
                "x": stem_x, "y": stem_y,
                "type": "scatter", "mode": "lines",
                "line": {"color": self.SIGNAL_H_COLOR, "width": 1.5},
                "showlegend": False,
            })
            data_traces.append({
                "x": x_vals, "y": y_vals,
                "type": "scatter", "mode": "markers",
                "name": "h[n₀-k]",
                "marker": {"size": 8, "color": self.SIGNAL_H_COLOR},
            })
        else:
            data_traces.append({
                "x": self._tau.tolist(),
                "y": self._h_shifted.tolist(),
                "type": "scatter", "mode": "lines",
                "name": "h(t₀-τ)",
                "line": {"color": self.SIGNAL_H_COLOR, "width": 2.5},
            })

        return {
            "id": "signal_h",
            "title": title,
            "data": data_traces,
            "layout": self._get_standard_layout(
                "τ" if not is_discrete else "k",
                [-0.5, 1.5]
            ),
        }

    def _create_product_plot(self) -> Dict[str, Any]:
        """Create plot for product x(τ)h(t₀ - τ)."""
        mode = self.parameters["mode"]
        is_discrete = mode == "discrete"

        op_symbol = "Σ" if is_discrete else "∫"
        title = f"Product ({op_symbol} = {self._current_y_value:.4f})"

        data_traces = []

        if is_discrete:
            # Create stem plot for discrete
            x_vals = self._tau.tolist()
            y_vals = self._product.tolist()
            stem_x, stem_y = [], []
            for xi, yi in zip(x_vals, y_vals):
                stem_x.extend([xi, xi, None])
                stem_y.extend([0, yi, None])
            data_traces.append({
                "x": stem_x, "y": stem_y,
                "type": "scatter", "mode": "lines",
                "line": {"color": self.PRODUCT_COLOR, "width": 1.5},
                "showlegend": False,
            })
            data_traces.append({
                "x": x_vals, "y": y_vals,
                "type": "scatter", "mode": "markers",
                "name": "x·h",
                "marker": {"size": 8, "color": self.PRODUCT_COLOR},
            })
        else:
            data_traces.append({
                "x": self._tau.tolist(),
                "y": self._product.tolist(),
                "type": "scatter", "mode": "lines",
                "name": "x·h",
                "line": {"color": self.PRODUCT_COLOR, "width": 2.5},
                "fill": "tozeroy",
                "fillcolor": "rgba(245, 158, 11, 0.3)",
            })

        return {
            "id": "product",
            "title": title,
            "data": data_traces,
            "layout": self._get_standard_layout(
                "τ" if not is_discrete else "k",
                None
            ),
        }

    def _create_result_plot(self) -> Dict[str, Any]:
        """Create convolution result plot with current value marker."""
        mode = self.parameters["mode"]
        t0 = self.parameters["time_shift"]
        is_discrete = mode == "discrete"

        data_traces = []

        if is_discrete:
            # Create stem plot for discrete: vertical lines + markers
            x_vals = self._t_result.tolist() if self._t_result is not None else []
            y_vals = self._y_result.tolist() if self._y_result is not None else []

            # Create stem lines (vertical lines from 0 to each point)
            stem_x = []
            stem_y = []
            for xi, yi in zip(x_vals, y_vals):
                stem_x.extend([xi, xi, None])
                stem_y.extend([0, yi, None])

            # Stem lines
            data_traces.append({
                "x": stem_x,
                "y": stem_y,
                "type": "scatter",
                "mode": "lines",
                "name": "",
                "line": {"color": self.RESULT_COLOR, "width": 1.5},
                "showlegend": False,
            })
            # Stem markers (points at top)
            data_traces.append({
                "x": x_vals,
                "y": y_vals,
                "type": "scatter",
                "mode": "markers",
                "name": "y[n]",
                "marker": {"size": 8, "color": self.RESULT_COLOR},
            })
        else:
            # Continuous: regular line plot
            data_traces.append({
                "x": self._t_result.tolist() if self._t_result is not None else [],
                "y": self._y_result.tolist() if self._y_result is not None else [],
                "type": "scatter",
                "mode": "lines",
                "name": "y(t)",
                "line": {"color": self.RESULT_COLOR, "width": 2.5},
            })

        # Current value marker
        n0_label = int(round(t0)) if is_discrete else t0
        data_traces.append({
            "x": [float(t0)],
            "y": [self._current_y_value],
            "type": "scatter",
            "mode": "markers",
            "name": f"y[{n0_label}] = {self._current_y_value:.4f}" if is_discrete else f"y({t0:.1f}) = {self._current_y_value:.4f}",
            "marker": {"size": 14, "color": self.MARKER_COLOR, "symbol": "circle"},
        })

        return {
            "id": "result",
            "title": "Convolution Result y = x * h",
            "data": data_traces,
            "layout": {
                **self._get_standard_layout("t" if not is_discrete else "n", None),
                "legend": {
                    "orientation": "h",
                    "yanchor": "bottom",
                    "y": 1.02,
                    "xanchor": "right",
                    "x": 1,
                },
            },
        }

    # Block-step visualization plots
    def _create_original_signals_plot(self) -> Dict[str, Any]:
        """Create plot showing original x(τ) and h(τ)."""
        mode = self.parameters["mode"]
        is_discrete = mode == "discrete"
        trace_mode = "markers" if is_discrete else "lines"

        return {
            "id": "originals",
            "title": "Step 1: Original Signals",
            "data": [
                {
                    "x": self._tau.tolist(),
                    "y": self._x_t.tolist(),
                    "type": "scatter",
                    "mode": trace_mode,
                    "name": "x(τ)",
                    "line": {"color": self.SIGNAL_X_COLOR, "width": 2.5},
                    "marker": {"size": 6, "color": self.SIGNAL_X_COLOR},
                },
                {
                    "x": self._tau.tolist(),
                    "y": self._h_original.tolist(),
                    "type": "scatter",
                    "mode": trace_mode,
                    "name": "h(τ)",
                    "line": {"color": self.SIGNAL_H_COLOR, "width": 2.5},
                    "marker": {"size": 6, "color": self.SIGNAL_H_COLOR},
                },
            ],
            "layout": {
                **self._get_standard_layout("τ", [-0.5, 1.5]),
                "legend": {"orientation": "h", "y": 1.1},
            },
        }

    def _create_flip_plot(self) -> Dict[str, Any]:
        """Create plot showing h(-τ) - the flip operation."""
        mode = self.parameters["mode"]
        is_discrete = mode == "discrete"
        trace_mode = "markers" if is_discrete else "lines"

        return {
            "id": "flip",
            "title": "Step 2: Flip h(τ) → h(-τ)",
            "data": [
                {
                    "x": self._tau.tolist(),
                    "y": self._h_flipped.tolist(),
                    "type": "scatter",
                    "mode": trace_mode,
                    "name": "h(-τ)",
                    "line": {"color": self.FLIP_COLOR, "width": 2.5},
                    "marker": {"size": 6, "color": self.FLIP_COLOR},
                },
            ],
            "layout": self._get_standard_layout("τ", [-0.5, 1.5]),
        }

    def _create_shift_plot(self) -> Dict[str, Any]:
        """Create plot showing h(t₀-τ) - the shift operation."""
        mode = self.parameters["mode"]
        t0 = self.parameters["time_shift"]
        is_discrete = mode == "discrete"
        trace_mode = "markers" if is_discrete else "lines"

        if is_discrete:
            title = f"Step 3: Shift h(-τ) → h({int(t0)}-τ)"
        else:
            title = f"Step 3: Shift h(-τ) → h({t0:.1f}-τ)"

        return {
            "id": "shift",
            "title": title,
            "data": [
                {
                    "x": self._tau.tolist(),
                    "y": self._h_shifted.tolist(),
                    "type": "scatter",
                    "mode": trace_mode,
                    "name": f"h(t₀-τ)",
                    "line": {"color": self.SHIFT_COLOR, "width": 2.5},
                    "marker": {"size": 6, "color": self.SHIFT_COLOR},
                },
            ],
            "layout": self._get_standard_layout("τ", [-0.5, 1.5]),
        }

    def _create_multiply_plot(self) -> Dict[str, Any]:
        """Create plot showing x(τ)·h(t₀-τ) - the multiply operation."""
        mode = self.parameters["mode"]
        is_discrete = mode == "discrete"
        trace_mode = "markers" if is_discrete else "lines"

        fill_opts = {"fill": "tozeroy", "fillcolor": "rgba(245, 158, 11, 0.3)"} if not is_discrete else {}

        return {
            "id": "multiply",
            "title": "Step 4: Multiply x(τ)·h(t₀-τ)",
            "data": [
                {
                    "x": self._tau.tolist(),
                    "y": self._product.tolist(),
                    "type": "scatter",
                    "mode": trace_mode,
                    "name": "Product",
                    "line": {"color": self.PRODUCT_COLOR, "width": 2.5},
                    "marker": {"size": 6, "color": self.PRODUCT_COLOR},
                    **fill_opts,
                },
            ],
            "layout": self._get_standard_layout("τ", None),
        }

    def _create_integrate_plot(self) -> Dict[str, Any]:
        """Create plot showing integration/summation result."""
        mode = self.parameters["mode"]
        t0 = self.parameters["time_shift"]
        is_discrete = mode == "discrete"

        if is_discrete:
            op_text = f"y[{int(t0)}] = Σ x[k]·h[{int(t0)}-k] = {self._current_y_value:.4f}"
        else:
            op_text = f"y({t0:.2f}) = ∫ x(τ)·h({t0:.2f}-τ)dτ = {self._current_y_value:.4f}"

        trace_mode = "markers+lines" if is_discrete else "lines"
        marker_opts = {"size": 4, "color": self.RESULT_COLOR} if is_discrete else {}

        return {
            "id": "integrate",
            "title": f"Step 5: {'Sum' if is_discrete else 'Integrate'} → {op_text}",
            "data": [
                {
                    "x": self._t_result.tolist() if self._t_result is not None else [],
                    "y": self._y_result.tolist() if self._y_result is not None else [],
                    "type": "scatter",
                    "mode": trace_mode,
                    "name": "y(t)" if not is_discrete else "y[n]",
                    "line": {"color": self.RESULT_COLOR, "width": 2.5},
                    "marker": marker_opts,
                },
                {
                    "x": [float(t0)],
                    "y": [self._current_y_value],
                    "type": "scatter",
                    "mode": "markers",
                    "name": f"Current: {self._current_y_value:.4f}",
                    "marker": {"size": 14, "color": self.MARKER_COLOR, "symbol": "circle"},
                },
            ],
            "layout": {
                **self._get_standard_layout("t" if not is_discrete else "n", None),
                "legend": {"orientation": "h", "y": 1.1},
            },
        }

    def _get_standard_layout(self, x_label: str, y_range: Optional[List[float]] = None, auto_y: bool = True) -> Dict[str, Any]:
        """Get standard plot layout with autorange support."""
        mode = self.parameters["mode"]
        is_discrete = mode == "discrete"

        layout = {
            "xaxis": {
                "title": x_label,
                "showgrid": True,
                "gridcolor": "rgba(148, 163, 184, 0.1)",
                "zeroline": True,
                "zerolinecolor": "rgba(148, 163, 184, 0.3)",
                "autorange": True,  # Auto-adjust x-axis based on data
                "fixedrange": False,
            },
            "yaxis": {
                "title": "Amplitude",
                "showgrid": True,
                "gridcolor": "rgba(148, 163, 184, 0.1)",
                "zeroline": True,
                "zerolinecolor": "rgba(148, 163, 184, 0.3)",
                "autorange": True,  # Auto-adjust y-axis based on data
                "fixedrange": False,
            },
            "margin": {"l": 50, "r": 20, "t": 40, "b": 40},
            "plot_bgcolor": "rgba(0,0,0,0)",
            "paper_bgcolor": "rgba(0,0,0,0)",
            "uirevision": "constant",
        }

        # Only use fixed y_range if explicitly provided and not using auto
        if y_range and not auto_y:
            layout["yaxis"]["range"] = y_range
            layout["yaxis"]["autorange"] = False

        return layout

    def get_state(self) -> Dict[str, Any]:
        """Get current state including metadata."""
        state = super().get_state()

        # Add metadata for formula display and custom viewer
        mode = self.parameters["mode"]
        t0 = self.parameters["time_shift"]

        if mode == "discrete":
            formula = f"y[{int(t0)}] = Σ x[k]·h[{int(t0)}-k]"
            time_range = [-15, 25]
        else:
            formula = f"y({t0:.2f}) = ∫ x(τ)·h({t0:.2f}-τ)dτ"
            time_range = [-8, 12]

        state["metadata"] = {
            "simulation_type": "convolution_simulator",
            "has_custom_viewer": True,
            "sticky_controls": True,
            "mode": mode,
            "current_value": self._current_y_value,
            "formula": formula,
            "x_expr": self._x_expression,
            "h_expr": self._h_expression,
            "time_range": time_range,
            "presets": self.DEMO_PRESETS,
            "error": self._error_message,
            "demo_presets": self.get_demo_presets(),
        }

        return state
