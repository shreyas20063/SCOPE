"""
DT Difference Equation Step-by-Step Solver

Interactive step-by-step evaluation of discrete-time difference equations
with synchronized block diagram visualization, equation substitution display,
and incrementally growing stem plots. Recreates MIT 6.003 Lecture 2 slides 5-17.
"""

from typing import Any, Dict, List, Optional

import numpy as np

from .base_simulator import BaseSimulator


class DifferenceEquationSimulator(BaseSimulator):
    """Step-by-step DT difference equation solver with block diagram visualization."""

    # Display range for stem plots
    N_MIN = -2
    N_MAX = 15
    N_START = -3  # current_n starts here ("before at rest" — no steps computed yet)

    # Colors (project palette)
    INPUT_COLOR = "#3b82f6"       # Blue
    OUTPUT_COLOR = "#ef4444"      # Red
    HIGHLIGHT_COLOR = "#8b5cf6"   # Purple
    TEAL_COLOR = "#14b8a6"        # Teal

    # Equation preset definitions
    PRESETS = {
        "difference_machine": {
            "label": "Difference Machine",
            "equation_text": "y[n] = x[n] − x[n−1]",
            "description": "Computes successive differences (non-recursive)",
            "feedforward_coeffs": [1.0, -1.0],   # b0*x[n] + b1*x[n-1]
            "feedback_coeffs": [],                 # no feedback
            "diagram_type": "difference_machine",
        },
        "accumulator": {
            "label": "Accumulator",
            "equation_text": "y[n] = x[n] + y[n−1]",
            "description": "Running sum (recursive)",
            "feedforward_coeffs": [1.0],           # b0*x[n]
            "feedback_coeffs": [1.0],              # a1*y[n-1]
            "diagram_type": "accumulator",
        },
        "moving_average": {
            "label": "Moving Average",
            "equation_text": "y[n] = (x[n] + x[n−1]) / 2",
            "description": "Two-point moving average (non-recursive)",
            "feedforward_coeffs": [0.5, 0.5],      # 0.5*x[n] + 0.5*x[n-1]
            "feedback_coeffs": [],
            "diagram_type": "moving_average",
        },
        "leaky_integrator": {
            "label": "Leaky Integrator",
            "equation_text": "y[n] = 0.9·y[n−1] + 0.1·x[n]",
            "description": "Exponential smoother (recursive)",
            "feedforward_coeffs": [0.1],            # 0.1*x[n]
            "feedback_coeffs": [0.9],               # 0.9*y[n-1]
            "diagram_type": "leaky_integrator",
        },
    }

    PARAMETER_SCHEMA = {
        "equation_preset": {
            "type": "select",
            "options": [
                {"value": "difference_machine", "label": "Difference Machine: y[n] = x[n] − x[n−1]"},
                {"value": "accumulator", "label": "Accumulator: y[n] = x[n] + y[n−1]"},
                {"value": "moving_average", "label": "Moving Average: y[n] = (x[n]+x[n−1])/2"},
                {"value": "leaky_integrator", "label": "Leaky Integrator: y[n] = 0.9y[n−1]+0.1x[n]"},
            ],
            "default": "difference_machine",
        },
        "input_signal": {
            "type": "select",
            "options": [
                {"value": "impulse", "label": "Unit Impulse δ[n]"},
                {"value": "step", "label": "Unit Step u[n]"},
                {"value": "ramp", "label": "Ramp n·u[n]"},
            ],
            "default": "impulse",
        },
        "animation_speed": {
            "type": "slider",
            "min": 0.5,
            "max": 3.0,
            "step": 0.5,
            "default": 1.0,
        },
    }

    DEFAULT_PARAMS = {
        "equation_preset": "difference_machine",
        "input_signal": "impulse",
        "animation_speed": 1.0,
    }

    def __init__(self, simulation_id: str):
        super().__init__(simulation_id)
        self._current_n: int = self.N_START
        self._x_history: Dict[int, float] = {}
        self._y_history: Dict[int, float] = {}
        self._delay_states: List[float] = []
        self._delay_states_history: List[List[float]] = []
        self._substitution_history: List[Dict[str, Any]] = []
        self._wire_values: Dict[str, float] = {}

    def initialize(self, params: Optional[Dict[str, Any]] = None) -> None:
        """Initialize simulation with parameters."""
        self.parameters = {**self.DEFAULT_PARAMS, **(params or {})}
        for name, value in self.parameters.items():
            self.parameters[name] = self._validate_param(name, value)
        self._initialized = True
        self._reset_state()

    def _reset_state(self) -> None:
        """Reset computation state to 'at rest'."""
        self._current_n = self.N_START
        self._x_history = {}
        self._y_history = {}
        self._substitution_history = []
        self._delay_states_history = []

        preset = self.PRESETS[self.parameters["equation_preset"]]
        num_delays = max(
            len(preset["feedforward_coeffs"]) - 1,
            len(preset["feedback_coeffs"]),
            0,
        )
        # At least 1 delay for all our presets
        num_delays = max(num_delays, 1)
        self._delay_states = [0.0] * num_delays
        self._wire_values = self._get_at_rest_wire_values()

    def update_parameter(self, name: str, value: Any) -> Dict[str, Any]:
        """Update a single parameter and reset computation state."""
        if name in self.parameters:
            self.parameters[name] = self._validate_param(name, value)
            # Changing equation or input signal resets the simulation
            if name in ("equation_preset", "input_signal"):
                self._reset_state()
        return self.get_state()

    # =========================================================================
    # Step computation
    # =========================================================================

    def _get_input_value(self, n: int) -> float:
        """Compute x[n] for the selected input signal."""
        sig = self.parameters["input_signal"]
        if sig == "impulse":
            return 1.0 if n == 0 else 0.0
        elif sig == "step":
            return 1.0 if n >= 0 else 0.0
        elif sig == "ramp":
            return float(n) if n >= 0 else 0.0
        return 0.0

    def _compute_step(self, n: int) -> None:
        """Compute one step of the difference equation at index n."""
        preset = self.PRESETS[self.parameters["equation_preset"]]
        ff = preset["feedforward_coeffs"]
        fb = preset["feedback_coeffs"]

        # Get input
        x_n = self._get_input_value(n)
        self._x_history[n] = x_n

        # Read delay outputs (values from previous step)
        delay_outputs = list(self._delay_states)

        # Compute feedforward sum: b0*x[n] + b1*x[n-1] + ...
        ff_sum = ff[0] * x_n
        for k in range(1, len(ff)):
            x_prev = self._x_history.get(n - k, 0.0)
            ff_sum += ff[k] * x_prev

        # Compute feedback sum: a1*y[n-1] + a2*y[n-2] + ...
        fb_sum = 0.0
        for k in range(len(fb)):
            y_prev = self._y_history.get(n - 1 - k, 0.0)
            fb_sum += fb[k] * y_prev

        # y[n] = feedforward + feedback
        y_n = ff_sum + fb_sum
        self._y_history[n] = y_n

        # Build substitution text
        sub_text = self._build_substitution(n, preset, x_n, y_n)
        self._substitution_history.append({
            "n": n,
            "text": sub_text,
            "result": round(y_n, 6),
        })

        # Compute wire values for block diagram
        self._wire_values = self._compute_wire_values(
            preset["diagram_type"], x_n, y_n, delay_outputs
        )

        # Update delay states for next step
        self._update_delay_states(preset["diagram_type"], x_n, y_n)

        # Save delay state snapshot for step_backward
        self._delay_states_history.append(list(self._delay_states))

    def _build_substitution(
        self, n: int, preset: Dict, x_n: float, y_n: float
    ) -> str:
        """Build the equation substitution string for display."""
        eq_type = preset["diagram_type"]

        def fmt(v: float) -> str:
            if v == int(v):
                return str(int(v))
            return f"{v:.4g}"

        if eq_type == "difference_machine":
            x_prev = self._x_history.get(n - 1, 0.0)
            return (
                f"y[{n}] = x[{n}] − x[{n-1}]"
                f" = {fmt(x_n)} − {fmt(x_prev)}"
                f" = {fmt(y_n)}"
            )
        elif eq_type == "accumulator":
            y_prev = self._y_history.get(n - 1, 0.0)
            return (
                f"y[{n}] = x[{n}] + y[{n-1}]"
                f" = {fmt(x_n)} + {fmt(y_prev)}"
                f" = {fmt(y_n)}"
            )
        elif eq_type == "moving_average":
            x_prev = self._x_history.get(n - 1, 0.0)
            return (
                f"y[{n}] = (x[{n}] + x[{n-1}]) / 2"
                f" = ({fmt(x_n)} + {fmt(x_prev)}) / 2"
                f" = {fmt(y_n)}"
            )
        elif eq_type == "leaky_integrator":
            y_prev = self._y_history.get(n - 1, 0.0)
            return (
                f"y[{n}] = 0.9·y[{n-1}] + 0.1·x[{n}]"
                f" = 0.9·{fmt(y_prev)} + 0.1·{fmt(x_n)}"
                f" = {fmt(y_n)}"
            )
        return f"y[{n}] = {fmt(y_n)}"

    def _compute_wire_values(
        self,
        diagram_type: str,
        x_n: float,
        y_n: float,
        delay_outputs: List[float],
    ) -> Dict[str, float]:
        """Compute wire values for the block diagram at the current step."""
        d_out = delay_outputs[0] if delay_outputs else 0.0

        if diagram_type == "difference_machine":
            # x[n] → direct to adder; x[n] → gain(-1) → delay → adder
            return {
                "x_in": x_n,
                "gain_out": -x_n,           # output of ×(-1) block
                "delay_in": -x_n,            # what goes into delay (stored for next)
                "delay_out": d_out,           # came out of delay this step
                "adder_out": y_n,             # = x_n + delay_out
            }
        elif diagram_type == "accumulator":
            # x[n] → adder → y[n]; y[n] → delay → adder
            return {
                "x_in": x_n,
                "delay_out": d_out,           # y[n-1] from delay
                "adder_out": y_n,             # = x_n + delay_out
                "delay_in": y_n,              # y[n] feeds back into delay
            }
        elif diagram_type == "moving_average":
            # x[n] → ×0.5 → adder; x[n] → delay → ×0.5 → adder
            return {
                "x_in": x_n,
                "gain1_out": 0.5 * x_n,      # top path gain
                "delay_out": d_out,           # x[n-1]
                "gain2_out": 0.5 * d_out,     # bottom path gain
                "adder_out": y_n,
                "delay_in": x_n,
            }
        elif diagram_type == "leaky_integrator":
            # x[n] → ×0.1 → adder → y[n]; y[n] → delay → ×0.9 → adder
            return {
                "x_in": x_n,
                "gain_x_out": 0.1 * x_n,     # input gain
                "delay_out": d_out,           # y[n-1]
                "gain_fb_out": 0.9 * d_out,   # feedback gain
                "adder_out": y_n,
                "delay_in": y_n,
            }
        return {"x_in": x_n, "adder_out": y_n}

    def _update_delay_states(
        self, diagram_type: str, x_n: float, y_n: float
    ) -> None:
        """Update delay element states after computing a step."""
        if diagram_type == "difference_machine":
            self._delay_states[0] = -x_n
        elif diagram_type == "accumulator":
            self._delay_states[0] = y_n
        elif diagram_type == "moving_average":
            self._delay_states[0] = x_n
        elif diagram_type == "leaky_integrator":
            self._delay_states[0] = y_n

    def _get_at_rest_wire_values(self) -> Dict[str, float]:
        """Wire values when system is at rest (all zeros)."""
        diagram_type = self.PRESETS[self.parameters["equation_preset"]]["diagram_type"]
        if diagram_type == "difference_machine":
            return {
                "x_in": 0, "gain_out": 0, "delay_in": 0, "delay_out": 0, "adder_out": 0
            }
        elif diagram_type == "accumulator":
            return {
                "x_in": 0, "delay_out": 0, "adder_out": 0, "delay_in": 0
            }
        elif diagram_type == "moving_average":
            return {
                "x_in": 0, "gain1_out": 0, "delay_out": 0, "gain2_out": 0,
                "adder_out": 0, "delay_in": 0
            }
        elif diagram_type == "leaky_integrator":
            return {
                "x_in": 0, "gain_x_out": 0, "delay_out": 0, "gain_fb_out": 0,
                "adder_out": 0, "delay_in": 0
            }
        return {}

    # =========================================================================
    # Action handlers (step_forward, step_backward, reset, advance)
    # =========================================================================

    def step_forward(self) -> Dict[str, Any]:
        """Compute next sample and return updated state."""
        if self._current_n >= self.N_MAX:
            return self.get_state()
        self._current_n += 1
        self._compute_step(self._current_n)
        return self.get_state()

    def step_backward(self) -> Dict[str, Any]:
        """Go back one step using stored history."""
        if self._current_n <= self.N_START:
            return self.get_state()

        # Remove last computed step
        if self._current_n in self._x_history:
            del self._x_history[self._current_n]
        if self._current_n in self._y_history:
            del self._y_history[self._current_n]
        if self._substitution_history:
            self._substitution_history.pop()
        if self._delay_states_history:
            self._delay_states_history.pop()

        self._current_n -= 1

        # Restore delay states from history
        if self._delay_states_history:
            self._delay_states = list(self._delay_states_history[-1])
        else:
            num_delays = len(self._delay_states)
            self._delay_states = [0.0] * num_delays

        # Recompute wire values for the now-current step
        if self._current_n > self.N_START and self._substitution_history:
            preset = self.PRESETS[self.parameters["equation_preset"]]
            n = self._current_n
            x_n = self._x_history.get(n, 0.0)
            y_n = self._y_history.get(n, 0.0)
            # For wire values, we need delay outputs from the step before current
            if len(self._delay_states_history) >= 2:
                prev_delays = self._delay_states_history[-2]
            elif len(self._delay_states_history) == 1:
                prev_delays = [0.0] * len(self._delay_states)
            else:
                prev_delays = [0.0] * len(self._delay_states)
            self._wire_values = self._compute_wire_values(
                preset["diagram_type"], x_n, y_n, prev_delays
            )
        else:
            self._wire_values = self._get_at_rest_wire_values()

        return self.get_state()

    def advance_frame(self) -> Dict[str, Any]:
        """Advance one frame for animation (same as step_forward)."""
        return self.step_forward()

    def reset(self) -> Dict[str, Any]:
        """Full reset — restore default parameters and clear all state."""
        self.parameters = {**self.DEFAULT_PARAMS}
        self._reset_state()
        self._initialized = True
        return self.get_state()

    # =========================================================================
    # Plot generation
    # =========================================================================

    def get_plots(self) -> List[Dict[str, Any]]:
        """Generate stem plots for x[n] and y[n]."""
        if not self._initialized:
            self.initialize()
        return [self._create_input_plot(), self._create_output_plot()]

    def _create_stem_traces(
        self,
        history: Dict[int, float],
        current_n: int,
        color: str,
        name: str,
    ) -> List[Dict[str, Any]]:
        """Create Plotly stem plot traces from a history dict."""
        if not history:
            return [{
                "x": [], "y": [],
                "type": "scatter", "mode": "markers",
                "name": name,
                "marker": {"size": 8, "color": color},
            }]

        # Sort by n and separate current from past
        sorted_items = sorted(history.items())
        past_n = [n for n, _ in sorted_items if n < current_n]
        past_v = [history[n] for n in past_n]
        curr_n_val = history.get(current_n)

        traces = []

        # Past samples — stem lines
        if past_n:
            stem_x, stem_y = [], []
            for ni, vi in zip(past_n, past_v):
                stem_x.extend([ni, ni, None])
                stem_y.extend([0, vi, None])
            traces.append({
                "x": stem_x, "y": stem_y,
                "type": "scatter", "mode": "lines",
                "line": {"color": color, "width": 1.5},
                "showlegend": False, "hoverinfo": "skip",
            })
            traces.append({
                "x": past_n, "y": past_v,
                "type": "scatter", "mode": "markers",
                "name": name,
                "marker": {"size": 7, "color": color},
            })

        # Current sample — highlighted
        if curr_n_val is not None:
            traces.append({
                "x": [current_n, current_n],
                "y": [0, curr_n_val],
                "type": "scatter", "mode": "lines",
                "line": {"color": self.HIGHLIGHT_COLOR, "width": 2.5},
                "showlegend": False, "hoverinfo": "skip",
            })
            traces.append({
                "x": [current_n],
                "y": [curr_n_val],
                "type": "scatter", "mode": "markers",
                "name": f"n={current_n}",
                "marker": {
                    "size": 12,
                    "color": self.HIGHLIGHT_COLOR,
                    "line": {"color": "white", "width": 2},
                },
            })

        return traces

    def _compute_y_range(self, history: Dict[int, float]) -> List[float]:
        """Compute explicit y-axis range from data with padding.

        PlotDisplay forces autorange:false, so we must provide an explicit range.
        """
        if not history:
            return [-0.5, 1.5]
        vals = list(history.values())
        y_min = min(vals)
        y_max = max(vals)
        # Include zero line in range
        y_min = min(y_min, 0.0)
        y_max = max(y_max, 0.0)
        # Add 20% padding (minimum 0.5 so flat lines don't collapse)
        span = y_max - y_min
        pad = max(span * 0.2, 0.5)
        return [y_min - pad, y_max + pad]

    def _compute_x_range(self) -> List[float]:
        """Compute dynamic x-axis range based on current step."""
        if self._current_n <= self.N_START:
            # At rest: show a small default window
            return [self.N_MIN - 0.5, 8.5]
        # Show from N_MIN to at least 3 steps ahead, up to N_MAX
        x_end = min(max(self._current_n + 3, 8), self.N_MAX) + 0.5
        return [self.N_MIN - 0.5, x_end]

    def _create_input_plot(self) -> Dict[str, Any]:
        """Create stem plot for x[n]."""
        traces = self._create_stem_traces(
            self._x_history, self._current_n, self.INPUT_COLOR, "x[n]"
        )
        return {
            "id": "input_signal",
            "title": "Input Signal x[n]",
            "data": traces,
            "layout": self._get_stem_layout(
                "n", "x[n]", self._compute_y_range(self._x_history)
            ),
        }

    def _create_output_plot(self) -> Dict[str, Any]:
        """Create stem plot for y[n]."""
        traces = self._create_stem_traces(
            self._y_history, self._current_n, self.OUTPUT_COLOR, "y[n]"
        )
        return {
            "id": "output_signal",
            "title": "Output Signal y[n]",
            "data": traces,
            "layout": self._get_stem_layout(
                "n", "y[n]", self._compute_y_range(self._y_history)
            ),
        }

    def _get_stem_layout(
        self, x_label: str, y_label: str, y_range: List[float]
    ) -> Dict[str, Any]:
        """Standard layout for stem plots with explicit ranges."""
        x_range = self._compute_x_range()
        # Unique revision forces Plotly re-render on every state change
        rev = f"diffeq-{self._current_n}-{len(self._x_history)}-{len(self._y_history)}"
        return {
            "xaxis": {
                "title": x_label,
                "range": x_range,
                "dtick": 1,
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
                "color": "#f1f5f9",
            },
            "yaxis": {
                "title": y_label,
                "range": y_range,
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
                "color": "#f1f5f9",
            },
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "font": {"family": "Inter, sans-serif", "size": 12, "color": "#f1f5f9"},
            "margin": {"t": 40, "r": 20, "b": 45, "l": 55},
            "showlegend": True,
            "legend": {"font": {"color": "#94a3b8"}, "orientation": "h", "y": 1.08},
            "datarevision": rev,
        }

    # =========================================================================
    # State
    # =========================================================================

    def get_state(self) -> Dict[str, Any]:
        """Return full state including metadata for custom viewer."""
        if not self._initialized:
            self.initialize()

        preset = self.PRESETS[self.parameters["equation_preset"]]

        # Build x/y value arrays for frontend
        sorted_x = sorted(self._x_history.items())
        sorted_y = sorted(self._y_history.items())

        state = {
            "parameters": self.parameters.copy(),
            "plots": self.get_plots(),
            "metadata": {
                "simulation_type": "dt_difference_equation",
                "has_custom_viewer": True,
                "current_n": self._current_n,
                "is_at_rest": self._current_n <= self.N_START,
                "can_step_back": self._current_n > self.N_START,
                "can_step_forward": self._current_n < self.N_MAX,
                "equation_text": preset["equation_text"],
                "equation_preset": self.parameters["equation_preset"],
                "equation_description": preset["description"],
                "diagram_type": preset["diagram_type"],
                "wire_values": {k: round(v, 6) for k, v in self._wire_values.items()},
                "delay_states": [round(d, 6) for d in self._delay_states],
                "substitution_history": self._substitution_history[-20:],  # last 20
                "x_values": {
                    "n": [item[0] for item in sorted_x],
                    "values": [round(item[1], 6) for item in sorted_x],
                },
                "y_values": {
                    "n": [item[0] for item in sorted_y],
                    "values": [round(item[1], 6) for item in sorted_y],
                },
                "input_signal_type": self.parameters["input_signal"],
            },
        }
        return state
