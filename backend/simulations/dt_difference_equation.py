"""
DT Difference Equation Step-by-Step Solver

Interactive step-by-step evaluation of discrete-time difference equations
with synchronized block diagram visualization, equation substitution display,
and incrementally growing stem plots.

Initial conditions (Oppenheim & Willsky Sec. 2.4.2, Oppenheim & Schafer
Sec. 2.5, Lathi Ch. 3)
--------------------------------------------------------------------------
Every preset is a first-order LCCDE

    y[n] = sum_k b_k x[n-k] + sum_{k>=1} c_k y[n-k]

(``feedforward_coeffs`` = b_k, ``feedback_coeffs`` = c_k = -a_k in the
O&S / ``scipy.signal.lfilter`` convention).  The applied input is causal:
x[n] = 0 for n < 0.

* Recursive presets (accumulator, leaky integrator; N = 1): y[0] needs the
  auxiliary condition y[-1].  It is exactly what the feedback delay of the
  block diagram holds at n = 0, and ``ic_y_minus_1`` sets it.
* Non-recursive presets (difference machine, moving average; N = 0): y[n]
  is an explicit function of the present and past inputs only, so no
  auxiliary conditions are needed (O&W Sec. 2.4.2).  x[-1] is an input
  sample (0 for a causal input), not an initial condition, so these presets
  take no IC and always start from initial rest.  Their zero-input response
  is identically 0.

y[-1] = 0 is initial rest, which reproduces the original (pre-IC) behaviour
exactly, including the steps through n = -2 and n = -1.  With a nonzero
y[-1] only n >= 0 is determined by the problem, so the recursion starts at
n = 0 and the IC is drawn at n = -1.  The output is then the zero-input
response (IC only, x = 0) plus the zero-state response (x only, IC = 0,
= h * x); the system is incrementally linear but not LTI (O&W Sec. 1.6.6,
Example 1.20).
"""

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy.signal import lfilter, lfiltic

from .base_simulator import BaseSimulator


class DifferenceEquationSimulator(BaseSimulator):
    """Step-by-step DT difference equation solver with block diagram visualization."""

    # Display range for stem plots
    N_MIN = -2
    N_MAX = 15
    N_START = -3  # current_n starts here ("before at rest" — no steps computed yet)
    # With a nonzero initial condition the recursion starts at n = 0: the
    # state at the end of n = -1 is the IC itself, nothing earlier is defined.
    N_START_IC = -1

    # Colors (project palette)
    INPUT_COLOR = "#3b82f6"       # Blue
    OUTPUT_COLOR = "#ef4444"      # Red
    HIGHLIGHT_COLOR = "#8b5cf6"   # Purple
    TEAL_COLOR = "#14b8a6"        # Teal
    IC_COLOR = "#f59e0b"          # Amber — initial condition and zero-input response
    ZSR_COLOR = "#14b8a6"         # Teal — zero-state response

    # Horizontal offset of the zero-input / zero-state stems in the
    # decomposition plot, so both stems at the same n stay visible.
    DECOMP_OFFSET = 0.15

    # Which parameter supplies which auxiliary condition: (signal, k) ->
    # param name, where (signal, k) means signal[-k].  Only past outputs are
    # initial conditions; past inputs belong to the (causal) input.
    IC_PARAMS: Dict[Tuple[str, int], str] = {
        ("y", 1): "ic_y_minus_1",
    }

    # Equation preset definitions
    PRESETS = {
        "difference_machine": {
            "label": "Difference Machine",
            "equation_text": "y[n] = x[n] − x[n−1]",
            "description": "Computes successive differences (non-recursive)",
            "feedforward_coeffs": [1.0, -1.0],   # b0*x[n] + b1*x[n-1]
            "feedback_coeffs": [],                 # no feedback
            "diagram_type": "difference_machine",
            # Non-recursive: no register / initial condition entry.
            "h_latex": r"h[n] = \delta[n] - \delta[n-1]",
        },
        "accumulator": {
            "label": "Accumulator",
            "equation_text": "y[n] = x[n] + y[n−1]",
            "description": "Running sum (recursive)",
            "feedforward_coeffs": [1.0],           # b0*x[n]
            "feedback_coeffs": [1.0],              # a1*y[n-1]
            "diagram_type": "accumulator",
            "register": {"signal": "y", "scale": 1.0,
                         "symbol": "y[n−1]", "ic_symbol": "y[−1]"},
            "zir_latex": r"y_{zi}[n] = y[-1]\,u[n]",
            "h_latex": r"h[n] = u[n]",
        },
        "moving_average": {
            "label": "Moving Average",
            "equation_text": "y[n] = (x[n] + x[n−1]) / 2",
            "description": "Two-point moving average (non-recursive)",
            "feedforward_coeffs": [0.5, 0.5],      # 0.5*x[n] + 0.5*x[n-1]
            "feedback_coeffs": [],
            "diagram_type": "moving_average",
            # Non-recursive: no register / initial condition entry.
            "h_latex": r"h[n] = \tfrac{1}{2}\,\delta[n] + \tfrac{1}{2}\,\delta[n-1]",
        },
        "leaky_integrator": {
            "label": "Leaky Integrator",
            "equation_text": "y[n] = 0.9·y[n−1] + 0.1·x[n]",
            "description": "Exponential smoother (recursive)",
            "feedforward_coeffs": [0.1],            # 0.1*x[n]
            "feedback_coeffs": [0.9],               # 0.9*y[n-1]
            "diagram_type": "leaky_integrator",
            "register": {"signal": "y", "scale": 1.0,
                         "symbol": "y[n−1]", "ic_symbol": "y[−1]"},
            "zir_latex": r"y_{zi}[n] = y[-1]\,(0.9)^{n+1}\,u[n]",
            "h_latex": r"h[n] = 0.1\,(0.9)^{n}\,u[n]",
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
        "ic_y_minus_1": {
            "type": "slider",
            "min": -5.0,
            "max": 5.0,
            "step": 0.1,
            "default": 0.0,
        },
        "show_decomposition": {
            "type": "checkbox",
            "default": False,
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
        "ic_y_minus_1": 0.0,
        "show_decomposition": False,
        "animation_speed": 1.0,
    }

    HUB_DOMAIN = "dt"

    def __init__(self, simulation_id: str):
        super().__init__(simulation_id)
        self._current_n: int = self.N_START
        self._x_history: Dict[int, float] = {}
        self._y_history: Dict[int, float] = {}
        self._delay_states: List[float] = []
        self._delay_states_history: List[List[float]] = []
        self._substitution_history: List[Dict[str, Any]] = []
        self._wire_values: Dict[str, Optional[float]] = {}

    def initialize(self, params: Optional[Dict[str, Any]] = None) -> None:
        """Initialize simulation with parameters."""
        self.parameters = {**self.DEFAULT_PARAMS, **(params or {})}
        for name, value in self.parameters.items():
            self.parameters[name] = self._validate_param(name, value)
        self._initialized = True
        self._reset_state()

    # =========================================================================
    # Initial conditions
    # =========================================================================

    def _preset(self) -> Dict[str, Any]:
        """Return the definition of the selected preset."""
        return self.PRESETS[self.parameters["equation_preset"]]

    def _is_recursive(self) -> bool:
        """True when the preset feeds back past outputs (N >= 1)."""
        return bool(self._preset()["feedback_coeffs"])

    def _required_ics(self) -> List[Tuple[str, int]]:
        """Auxiliary conditions the recursion needs at n = 0, as (signal, k).

        Only past outputs y[-1], ..., y[-N] are initial conditions.  A
        non-recursive preset (N = 0) needs none (O&W Sec. 2.4.2): the past
        inputs x[n-k] with n-k < 0 are samples of the causal input, i.e. 0.

        Returns:
            [("y", 1), ..., ("y", N)]; empty for a non-recursive preset.
        """
        preset = self._preset()
        return [("y", k) for k in range(1, len(preset["feedback_coeffs"]) + 1)]

    def _ic_values(self) -> Dict[Tuple[str, int], float]:
        """Values of the initial conditions the selected preset uses.

        An IC control the preset does not use (hidden while a non-recursive
        preset is selected) is ignored, so it can never change the numbers.
        """
        values = {}
        for key in self._required_ics():
            name = self.IC_PARAMS.get(key)
            values[key] = float(self.parameters.get(name, 0.0)) if name else 0.0
        return values

    def _has_initial_conditions(self) -> bool:
        """True when any initial condition the preset uses is nonzero."""
        return any(v != 0.0 for v in self._ic_values().values())

    def _start_n(self) -> int:
        """current_n before the first step (initial rest: -3, else -1)."""
        return self.N_START_IC if self._has_initial_conditions() else self.N_START

    def _at_start(self) -> bool:
        """True before the first step has been computed."""
        return self._current_n <= self._start_n()

    def _num_delays(self) -> int:
        """Number of delay elements in the preset's block diagram."""
        preset = self._preset()
        num_delays = max(
            len(preset["feedforward_coeffs"]) - 1,
            len(preset["feedback_coeffs"]),
            0,
        )
        # At least 1 delay for all our presets
        return max(num_delays, 1)

    def _initial_delay_states(self) -> List[float]:
        """Delay register contents at the start of step n = 0.

        Initial rest: all zero.  Otherwise the feedback delay holds y[-1].
        """
        num_delays = self._num_delays()
        if not self._has_initial_conditions():
            return [0.0] * num_delays
        register = self._preset()["register"]
        ic = self._ic_values().get((register["signal"], 1), 0.0)
        # "+ 0.0" turns a -0.0 into 0.0
        return [register["scale"] * ic + 0.0] + [0.0] * (num_delays - 1)

    def _past_x(self, m: int) -> float:
        """x[m] as the recursion sees it (causal input: 0 for m < 0)."""
        return self._x_history.get(m, 0.0)

    def _past_y(self, m: int) -> float:
        """y[m] as the recursion sees it (the IC for m < 0 when ICs are set)."""
        if m in self._y_history:
            return self._y_history[m]
        if m < 0 and self._has_initial_conditions():
            return self._ic_values().get(("y", -m), 0.0)
        return 0.0

    # =========================================================================
    # State management
    # =========================================================================

    def _reset_state(self) -> None:
        """Rewind to the start: 'at rest', or holding the initial conditions."""
        self._current_n = self._start_n()
        self._x_history = {}
        self._y_history = {}
        self._substitution_history = []
        self._delay_states_history = []
        self._delay_states = self._initial_delay_states()
        self._wire_values = self._get_start_wire_values()

    def _replay_to(self, target_n: int) -> None:
        """Rewind and recompute every step up to target_n (clamped to the range)."""
        self._reset_state()
        while self._current_n < min(target_n, self.N_MAX):
            self._current_n += 1
            self._compute_step(self._current_n)

    def update_parameter(self, name: str, value: Any) -> Dict[str, Any]:
        """Update a single parameter.

        Changing the equation or the input rewinds to the start.  Changing an
        initial condition recomputes every step up to the current n, so the
        effect of the IC can be watched without stepping again; before the
        first step it stays at the start (current_n = -1 means "nothing
        computed" with an IC but "n = -2, -1 computed" at initial rest, so
        replaying to it would invent two steps).
        """
        if name in self.parameters:
            was_at_start = self._at_start()
            self.parameters[name] = self._validate_param(name, value)
            # Changing equation or input signal resets the simulation
            if name in ("equation_preset", "input_signal"):
                self._reset_state()
            elif name in self.IC_PARAMS.values():
                if was_at_start:
                    self._reset_state()
                else:
                    self._replay_to(self._current_n)
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

    def _input_array(self, n: np.ndarray) -> np.ndarray:
        """Vectorized x[n] for the selected (causal) input signal."""
        sig = self.parameters["input_signal"]
        n = np.asarray(n)
        if sig == "impulse":
            return (n == 0).astype(float)
        if sig == "step":
            return (n >= 0).astype(float)
        if sig == "ramp":
            return np.where(n >= 0, n, 0).astype(float)
        return np.zeros(n.shape, dtype=float)

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
            x_prev = self._past_x(n - k)
            ff_sum += ff[k] * x_prev

        # Compute feedback sum: a1*y[n-1] + a2*y[n-2] + ...
        fb_sum = 0.0
        for k in range(len(fb)):
            y_prev = self._past_y(n - 1 - k)
            fb_sum += fb[k] * y_prev

        # y[n] = feedforward + feedback
        y_n = ff_sum + fb_sum
        self._y_history[n] = y_n

        # Build substitution text
        sub_text = self._build_substitution(n, preset, x_n, y_n)
        entry: Dict[str, Any] = {
            "n": n,
            "text": sub_text,
            "result": round(y_n, 6),
        }
        if self._has_initial_conditions():
            # Initial conditions this step reads (only n = 0 for first order)
            entry["ic_terms"] = [
                {"symbol": f"{sig}[{n - k}]", "value": round(val, 6)}
                for (sig, k), val in self._ic_values().items()
                if n - k < 0
            ]
        self._substitution_history.append(entry)

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
        """Build the equation substitution string for display.

        Past values come from _past_x/_past_y, so at n = 0 the initial
        conditions appear in the substitution (e.g. y[0] = x[0] + y[-1] =
        1 + 0.5 = 1.5).  Negative operands are shown in parentheses.
        """
        eq_type = preset["diagram_type"]

        def fmt(v: float) -> str:
            if v == int(v):
                return str(int(v))
            return f"{v:.4g}"

        def opnd(v: float) -> str:
            return f"({fmt(v)})" if v < 0 else fmt(v)

        if eq_type == "difference_machine":
            x_prev = self._past_x(n - 1)
            return (
                f"y[{n}] = x[{n}] − x[{n-1}]"
                f" = {opnd(x_n)} − {opnd(x_prev)}"
                f" = {fmt(y_n)}"
            )
        elif eq_type == "accumulator":
            y_prev = self._past_y(n - 1)
            return (
                f"y[{n}] = x[{n}] + y[{n-1}]"
                f" = {opnd(x_n)} + {opnd(y_prev)}"
                f" = {fmt(y_n)}"
            )
        elif eq_type == "moving_average":
            x_prev = self._past_x(n - 1)
            return (
                f"y[{n}] = (x[{n}] + x[{n-1}]) / 2"
                f" = ({opnd(x_n)} + {opnd(x_prev)}) / 2"
                f" = {fmt(y_n)}"
            )
        elif eq_type == "leaky_integrator":
            y_prev = self._past_y(n - 1)
            return (
                f"y[{n}] = 0.9·y[{n-1}] + 0.1·x[{n}]"
                f" = 0.9·{opnd(y_prev)} + 0.1·{opnd(x_n)}"
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

    def _get_start_wire_values(self) -> Dict[str, Optional[float]]:
        """Wire values before the first step.

        Initial rest: all zeros (original behaviour).  With an initial
        condition only the wires fed by the delay register are known before
        x[0] arrives: the delay output (the stored IC) and the gain right
        after it.  Wires that depend on x[0] are None (not yet computed).
        """
        if not self._has_initial_conditions():
            return self._get_at_rest_wire_values()
        preset = self._preset()
        diagram_type = preset["diagram_type"]
        q = self._delay_states[0] if self._delay_states else 0.0
        values: Dict[str, Optional[float]] = {
            k: None for k in self._get_at_rest_wire_values()
        }
        values["delay_out"] = q
        if diagram_type == "leaky_integrator":
            values["gain_fb_out"] = preset["feedback_coeffs"][0] * q
        return values

    # =========================================================================
    # Action handlers (step_forward, step_backward, reset, advance, restart)
    # =========================================================================

    def step_forward(self) -> Dict[str, Any]:
        """Compute next sample and return updated state."""
        if self._current_n >= self.N_MAX:
            return self.get_state()
        self._current_n += 1
        self._compute_step(self._current_n)
        return self.get_state()

    def step_backward(self) -> Dict[str, Any]:
        """Go back one step (recomputes all earlier steps from the start)."""
        if self._at_start():
            return self.get_state()
        self._replay_to(self._current_n - 1)
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

    def restart(self) -> Dict[str, Any]:
        """Rewind to the first step, keeping every parameter (incl. ICs)."""
        self._reset_state()
        return self.get_state()

    def handle_action(self, action: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Custom actions routed from /execute.

        Args:
            action: "restart" rewinds to the start and keeps the parameters.
            params: unused.

        Returns:
            Full simulation state.

        Raises:
            ValueError: for an unknown action.
        """
        if not self._initialized:
            self.initialize()
        if action == "restart":
            return self.restart()
        raise ValueError(f"Unknown action for dt_difference_equation: {action}")

    # =========================================================================
    # Zero-input / zero-state decomposition
    # =========================================================================

    def _lfilter_coeffs(self) -> Tuple[List[float], List[float]]:
        """(b, a) of the preset in the O&S / lfilter convention, a[0] = 1."""
        preset = self._preset()
        b = list(preset["feedforward_coeffs"])
        a = [1.0] + [-c for c in preset["feedback_coeffs"]]
        return b, a

    def _decomposition(self) -> Dict[str, List[float]]:
        """Total, zero-input and zero-state responses for n = 0..current_n.

        Zero-input: same initial conditions, x = 0.  Zero-state: same input,
        all initial conditions 0 (initial rest), which equals h * x.  The
        total is the step-by-step recursion.  Computed with lfilter; the
        initial state comes from lfiltic(b, a, y=[y[-1], ...]) with the
        causal input's x[-k] = 0.  A non-recursive preset has no initial
        conditions, so its zero-input response is identically 0.
        """
        if self._current_n < 0:
            return {"n": [], "x": [], "total": [], "zir": [], "zsr": []}
        n = np.arange(0, self._current_n + 1)
        x = self._input_array(n)
        b, a = self._lfilter_coeffs()
        ics = self._ic_values()
        zsr = lfilter(b, a, x)
        if self._has_initial_conditions():
            y_past = [ics.get(("y", k), 0.0) for k in range(1, len(a))]
            zi = lfiltic(b, a, y=y_past)
            zir, _ = lfilter(b, a, np.zeros_like(x), zi=zi)
        else:
            zir = np.zeros_like(x)
        total = np.array([self._y_history[int(k)] for k in n])
        return {
            "n": n.tolist(),
            "x": x.tolist(),
            "total": total.tolist(),
            "zir": np.asarray(zir, dtype=float).tolist(),
            "zsr": np.asarray(zsr, dtype=float).tolist(),
        }

    # =========================================================================
    # Plot generation
    # =========================================================================

    def _decomposition_shown(self) -> bool:
        """The split is offered for recursive presets only (else y_zi = 0)."""
        return bool(self.parameters.get("show_decomposition")) and self._is_recursive()

    def get_plots(self) -> List[Dict[str, Any]]:
        """Generate stem plots for x[n] and y[n] (+ decomposition when enabled)."""
        if not self._initialized:
            self.initialize()
        plots = [self._create_input_plot(), self._create_output_plot()]
        if self._decomposition_shown():
            plots.append(self._create_decomposition_plot())
        return plots

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

    def _ic_sample(self) -> Optional[Dict[str, Any]]:
        """The initial condition y[-1] to draw at n = -1, or None.

        Only drawn when a recursive preset has a nonzero y[-1].
        """
        if not self._has_initial_conditions():
            return None
        ics = self._ic_values()
        if ("y", 1) not in ics:
            return None
        return {"n": -1, "value": ics[("y", 1)], "label": "initial condition"}

    def _ic_marker_traces(self) -> List[Dict[str, Any]]:
        """Dotted stem + open diamond for the initial condition y[-1] at n = -1."""
        sample = self._ic_sample()
        if sample is None:
            return []
        v = sample["value"]
        hover = (
            "y[−1] = %{y:.4g}<br>initial condition<br>"
            "(held in the feedback delay at n = 0)<extra></extra>"
        )
        return [
            {
                "x": [-1, -1], "y": [0, v],
                "type": "scatter", "mode": "lines",
                "line": {"color": self.IC_COLOR, "width": 2, "dash": "dot"},
                "showlegend": False, "hoverinfo": "skip",
            },
            {
                "x": [-1], "y": [v],
                "type": "scatter", "mode": "markers",
                "name": "initial condition",
                "marker": {
                    "size": 12,
                    "color": self.IC_COLOR,
                    "symbol": "diamond-open",
                    "line": {"color": self.IC_COLOR, "width": 2.5},
                },
                "hovertemplate": hover,
            },
        ]

    def _compute_y_range(
        self, history: Dict[int, float], extra: Optional[List[float]] = None
    ) -> List[float]:
        """Compute explicit y-axis range from data with padding.

        PlotDisplay forces autorange:false, so we must provide an explicit range.

        Args:
            history: plotted samples {n: value}.
            extra: further values that must be visible (IC samples, ...).
        """
        vals = list(history.values()) + list(extra or [])
        if not vals:
            return [-0.5, 1.5]
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
        if self._at_start():
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
        """Create stem plot for y[n] (+ y[-1] when it is an IC)."""
        traces = self._create_stem_traces(
            self._y_history, self._current_n, self.OUTPUT_COLOR, "y[n]"
        )
        traces += self._ic_marker_traces()
        ic = self._ic_sample()
        return {
            "id": "output_signal",
            "title": "Output Signal y[n]",
            "data": traces,
            "layout": self._get_stem_layout(
                "n", "y[n]",
                self._compute_y_range(self._y_history, [ic["value"]] if ic else None),
            ),
        }

    def _offset_stems(
        self, n: List[int], values: List[float], offset: float, color: str,
        name: str, symbol: str, label: str,
    ) -> List[Dict[str, Any]]:
        """Stem traces drawn at n + offset (hover reports the true n)."""
        stem_x: List[Optional[float]] = []
        stem_y: List[Optional[float]] = []
        for ni, vi in zip(n, values):
            stem_x.extend([ni + offset, ni + offset, None])
            stem_y.extend([0, vi, None])
        return [
            {
                "x": stem_x, "y": stem_y,
                "type": "scatter", "mode": "lines",
                "line": {"color": color, "width": 1.8},
                "showlegend": False, "hoverinfo": "skip",
            },
            {
                "x": [ni + offset for ni in n], "y": list(values),
                "customdata": list(n),
                "type": "scatter", "mode": "markers",
                "name": name,
                "marker": {"size": 8, "color": color, "symbol": symbol},
                "hovertemplate": f"n = %{{customdata}}<br>{label} = %{{y:.4g}}<extra></extra>",
            },
        ]

    def _create_decomposition_plot(self) -> Dict[str, Any]:
        """Zero-input and zero-state responses with their sum (the total)."""
        dec = self._decomposition()
        n, zir, zsr, total = dec["n"], dec["zir"], dec["zsr"], dec["total"]
        off = self.DECOMP_OFFSET
        traces: List[Dict[str, Any]] = []
        traces += self._offset_stems(
            n, zir, -off, self.IC_COLOR,
            "y<sub>zi</sub>[n] zero-input", "diamond", "y<sub>zi</sub>",
        )
        traces += self._offset_stems(
            n, zsr, +off, self.ZSR_COLOR,
            "y<sub>zs</sub>[n] zero-state", "square", "y<sub>zs</sub>",
        )
        traces.append({
            "x": list(n), "y": list(total),
            "type": "scatter", "mode": "markers",
            "name": "y[n] = y<sub>zi</sub> + y<sub>zs</sub>",
            "marker": {
                "size": 11, "color": self.OUTPUT_COLOR, "symbol": "circle-open",
                "line": {"color": self.OUTPUT_COLOR, "width": 2},
            },
            "hovertemplate": "n = %{x}<br>y = %{y:.4g}<extra></extra>",
        })
        # The y[-1] initial condition belongs to the zero-input response
        traces += self._ic_marker_traces()
        ic = self._ic_sample()
        extra = list(zir) + list(zsr) + ([ic["value"]] if ic else [])
        layout = self._get_stem_layout(
            "n", "response", self._compute_y_range(self._y_history, extra)
        )
        layout["legend"] = {
            "font": {"color": "#94a3b8"}, "orientation": "h",
            "x": 0, "xanchor": "left", "y": -0.36, "yanchor": "top",
        }
        layout["margin"] = {"t": 40, "r": 20, "b": 105, "l": 55}
        return {
            "id": "decomposition",
            "title": "Zero-Input + Zero-State Decomposition",
            "data": traces,
            "layout": layout,
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

    def _initial_conditions_metadata(self) -> Dict[str, Any]:
        """Describe the initial conditions for the viewer.

        ``recursive`` False (difference machine, moving average) means the
        equation needs no auxiliary conditions: ``items`` is empty and
        ``register`` / ``zir_latex`` are None.
        """
        preset = self._preset()
        register = preset.get("register")
        ics = self._ic_values()
        items = []
        for (sig, k), val in ics.items():
            items.append({
                "param": self.IC_PARAMS.get((sig, k)),
                "signal": sig,
                "k": k,
                "symbol": f"{sig}[−{k}]",
                "latex": f"{sig}[-{k}]",
                "value": round(val, 6),
                "role": "feedback",
            })
        register_meta = None
        if register is not None:
            register_meta = {
                "symbol": register["symbol"],
                "ic_symbol": register["ic_symbol"],
                "scale": register["scale"],
                "initial_value": round(self._initial_delay_states()[0], 6),
            }
        return {
            "mode": "ic" if self._has_initial_conditions() else "initial_rest",
            "recursive": self._is_recursive(),
            "start_n": self._start_n(),
            "items": items,
            "register": register_meta,
            "zir_latex": preset.get("zir_latex"),
            "h_latex": preset["h_latex"],
        }

    def _at_defaults(self) -> bool:
        """True when every parameter has its default value."""
        return all(self.parameters.get(k) == v for k, v in self.DEFAULT_PARAMS.items())

    def get_state(self) -> Dict[str, Any]:
        """Return full state including metadata for custom viewer."""
        if not self._initialized:
            self.initialize()

        preset = self.PRESETS[self.parameters["equation_preset"]]

        # Build x/y value arrays for frontend
        sorted_x = sorted(self._x_history.items())
        sorted_y = sorted(self._y_history.items())

        at_start = self._at_start()
        initial_rest = not self._has_initial_conditions()
        decomposition = self._decomposition()

        state = {
            "parameters": self.parameters.copy(),
            "plots": self.get_plots(),
            "metadata": {
                "simulation_type": "dt_difference_equation",
            "hub_slots": self.HUB_SLOTS,
            "hub_domain": self.HUB_DOMAIN,
            "hub_dimensions": self.HUB_DIMENSIONS,
                "has_custom_viewer": True,
                "current_n": self._current_n,
                "is_at_rest": at_start and initial_rest,
                "at_start": at_start,
                "can_step_back": not at_start,
                "can_step_forward": self._current_n < self.N_MAX,
                "equation_text": preset["equation_text"],
                "equation_preset": self.parameters["equation_preset"],
                "equation_description": preset["description"],
                "diagram_type": preset["diagram_type"],
                "wire_values": {
                    k: (round(v, 6) if v is not None else None)
                    for k, v in self._wire_values.items()
                },
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
                # Reset restores every default; nothing to do only when the
                # parameters are the defaults and no step has been taken.
                "can_reset": not (at_start and self._at_defaults()),
                "initial_conditions": self._initial_conditions_metadata(),
                "ic_samples": {"y": self._ic_sample()},
                "show_decomposition": self._decomposition_shown(),
                "decomposition": {
                    key: [round(v, 6) for v in vals] if key not in ("n",) else vals
                    for key, vals in decomposition.items()
                },
            },
        }
        return state
