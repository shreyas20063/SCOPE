"""
Signal Operations Playground Simulator

Interactive exploration of signal transformations:
time-scaling f(at), time-shifting f(t-t0), time-reversal f(-t),
amplitude scaling A*f(t), and DC offset.

Includes quiz mode where students identify which operations
were applied to produce a mystery signal.
"""

import random
from typing import Any, Dict, List, Optional

import numpy as np

from .base_simulator import BaseSimulator


class SignalOperationsSimulator(BaseSimulator):
    """Simulator for signal transformation operations with quiz mode."""

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
        "mode": {
            "type": "select",
            "options": [
                {"value": "explore", "label": "Explore"},
                {"value": "quiz", "label": "Quiz"},
            ],
            "default": "explore",
        },
        "quiz_difficulty": {
            "type": "select",
            "options": [
                {"value": "easy", "label": "Easy (1 op)"},
                {"value": "medium", "label": "Medium (2 ops)"},
                {"value": "hard", "label": "Hard (3 ops)"},
            ],
            "default": "easy",
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
        "mode": "explore",
        "quiz_difficulty": "easy",
    }

    def __init__(self, simulation_id: str):
        super().__init__(simulation_id)
        self._t: Optional[np.ndarray] = None
        self._original: Optional[np.ndarray] = None
        self._transformed: Optional[np.ndarray] = None
        self._formula: str = "f(t)"

        # Quiz state
        self._quiz_signal: Optional[np.ndarray] = None
        self._quiz_operations: List = []
        self._quiz_options: List[str] = []
        self._quiz_answer: str = ""
        self._quiz_correct_index: int = 0
        self._quiz_generated: bool = False
        self._quiz_answered: bool = False
        self._quiz_correct: Optional[bool] = None

    def initialize(self, params: Optional[Dict[str, Any]] = None) -> None:
        self.parameters = {**self.DEFAULT_PARAMS, **(params or {})}
        for name, value in self.parameters.items():
            if name in self.PARAMETER_SCHEMA:
                self.parameters[name] = self._validate_param(name, value)
        self._initialized = True
        self._compute()

    def update_parameter(self, name: str, value: Any) -> Dict[str, Any]:
        if name in self.parameters:
            old_value = self.parameters.get(name)
            self.parameters[name] = self._validate_param(name, value)
            # Reset quiz when switching to quiz mode or changing difficulty
            if name == "mode" and value == "quiz":
                self._quiz_generated = False
                self._quiz_answered = False
                self._quiz_correct = None
            if name == "quiz_difficulty":
                self._quiz_generated = False
                self._quiz_answered = False
                self._quiz_correct = None
        self._compute()
        return self.get_state()

    def get_plots(self) -> List[Dict[str, Any]]:
        if self._t is None:
            self._compute()

        plots = []
        mode = self.parameters.get("mode", "explore")

        if mode == "explore":
            plots.append(self._create_original_plot())
            plots.append(self._create_transformed_plot())
        else:
            # Quiz mode: show original + quiz challenge
            plots.append(self._create_original_plot())
            plots.append(self._create_quiz_plot())

        return plots

    def get_state(self) -> Dict[str, Any]:
        state = super().get_state()
        state["metadata"] = {
            "simulation_type": "signal_operations",
            "mode": self.parameters["mode"],
            "formula_display": self._formula,
        }

        if self.parameters["mode"] == "quiz" and self._quiz_generated:
            state["metadata"]["quiz"] = {
                "options": self._quiz_options,
                "answered": self._quiz_answered,
                "correct": self._quiz_correct,
                "answer": self._quiz_answer if self._quiz_answered else None,
            }

        return state

    def handle_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle custom actions for quiz mode."""
        if action == "new_quiz":
            self._quiz_generated = False
            self._quiz_answered = False
            self._quiz_correct = None
            self._compute()
        elif action == "check_answer":
            answer_index = params.get("answer_index", -1)
            self._quiz_answered = True
            self._quiz_correct = (answer_index == self._quiz_correct_index)
        return self.get_state()

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

        # Quiz mode
        if self.parameters["mode"] == "quiz" and not self._quiz_generated:
            self._generate_quiz_question()

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
        return np.zeros_like(t)

    @staticmethod
    def _build_formula(A: float, a: float, t0: float, reverse: bool, dc: float) -> str:
        """Build human-readable formula string."""
        # Build inner argument
        t_var = "-t" if reverse else "t"

        # Time-scale + shift: a*(t - t0) or a*(-t - t0)
        if a == 0.0:
            inner = "0"
        else:
            # Build the (t - t0) part
            if t0 == 0.0:
                base = t_var
            elif t0 > 0:
                base = f"{t_var} - {t0:g}"
            else:
                base = f"{t_var} + {abs(t0):g}"

            # Apply scaling
            if a == 1.0:
                inner = base
            elif a == -1.0:
                if reverse and t0 == 0.0:
                    inner = "t"  # -(-t) = t
                else:
                    inner = f"-({base})" if t0 != 0.0 else f"-{t_var}"
            else:
                if t0 != 0.0:
                    inner = f"{a:g}({base})"
                else:
                    inner = f"{a:g}{t_var}"

        # Amplitude prefix
        if A == 0.0:
            # Just a constant: dc value
            return f"{dc:g}" if dc != 0.0 else "0"
        elif A == 1.0:
            result = f"f({inner})"
        elif A == -1.0:
            result = f"-f({inner})"
        else:
            result = f"{A:g} · f({inner})"

        # DC offset
        if dc > 0:
            result = f"{result} + {dc:g}"
        elif dc < 0:
            result = f"{result} - {abs(dc):g}"

        return result

    # ── Quiz Mode ────────────────────────────────────────────────

    def _generate_quiz_question(self) -> None:
        """Generate a random quiz question based on difficulty."""
        difficulty = self.parameters.get("quiz_difficulty", "easy")
        num_ops = {"easy": 1, "medium": 2, "hard": 3}.get(difficulty, 1)

        signal_type = self.parameters["signal_type"]
        frequency = self.parameters["frequency"]

        # Operation pool: (param_name, possible_values)
        op_pool = [
            ("amplitude", [-2.0, -1.0, -0.5, 0.5, 2.0, 3.0]),
            ("time_scale", [0.5, 2.0, -1.0, -2.0, 3.0]),
            ("time_shift", [-3.0, -2.0, -1.0, 1.0, 2.0, 3.0]),
            ("time_reverse", [True]),
            ("dc_offset", [-1.0, -0.5, 0.5, 1.0, 1.5]),
        ]

        selected = random.sample(op_pool, min(num_ops, len(op_pool)))

        # Build quiz parameters from identity
        quiz_params = {
            "amplitude": 1.0,
            "time_scale": 1.0,
            "time_shift": 0.0,
            "time_reverse": False,
            "dc_offset": 0.0,
        }

        self._quiz_operations = []
        for op_name, values in selected:
            value = random.choice(values)
            quiz_params[op_name] = value
            self._quiz_operations.append((op_name, value))

        # Compute quiz signal
        A = quiz_params["amplitude"]
        a = quiz_params["time_scale"]
        t0 = quiz_params["time_shift"]
        reverse = quiz_params["time_reverse"]
        dc = quiz_params["dc_offset"]

        t_arg = -self._t if reverse else self._t.copy()
        if a != 0:
            t_arg = a * (t_arg - t0)
        else:
            t_arg = np.zeros_like(self._t)

        self._quiz_signal = A * self._generate_signal(signal_type, frequency, t_arg) + dc
        self._quiz_answer = self._build_formula(A, a, t0, reverse, dc)

        # Generate multiple-choice options
        self._quiz_options = self._generate_options(quiz_params)
        self._quiz_generated = True
        self._quiz_answered = False
        self._quiz_correct = None

    def _generate_options(self, correct_params: Dict[str, Any]) -> List[str]:
        """Generate 4 options: 1 correct + 3 distractors."""
        correct_str = self._build_formula(
            correct_params["amplitude"],
            correct_params["time_scale"],
            correct_params["time_shift"],
            correct_params["time_reverse"],
            correct_params["dc_offset"],
        )
        options = [correct_str]

        attempts = 0
        while len(options) < 4 and attempts < 30:
            attempts += 1
            fake = dict(correct_params)

            # Mutate 1-2 operations randomly
            mutations = random.sample(list(correct_params.keys()), random.randint(1, 2))
            for key in mutations:
                if key == "amplitude":
                    fake[key] = random.choice([-2.0, -1.0, -0.5, 0.5, 1.0, 2.0, 3.0])
                elif key == "time_scale":
                    fake[key] = random.choice([-2.0, -1.0, 0.5, 1.0, 2.0, 3.0])
                elif key == "time_shift":
                    fake[key] = random.choice([-3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0])
                elif key == "time_reverse":
                    fake[key] = not correct_params[key]
                elif key == "dc_offset":
                    fake[key] = random.choice([-1.0, -0.5, 0.0, 0.5, 1.0, 1.5])

            fake_str = self._build_formula(
                fake["amplitude"], fake["time_scale"],
                fake["time_shift"], fake["time_reverse"], fake["dc_offset"],
            )
            if fake_str not in options:
                options.append(fake_str)

        # Pad with diverse fallbacks if we couldn't generate enough
        fallback_pool = ["2 · f(t)", "-f(t)", "f(2t)", "f(t - 1)", "f(-t)", "0.5 · f(t)"]
        for fb in fallback_pool:
            if len(options) >= 4:
                break
            if fb not in options:
                options.append(fb)

        random.shuffle(options)
        self._quiz_correct_index = options.index(correct_str)
        return options

    # ── Plot Construction ────────────────────────────────────────

    def _get_base_layout(self, xtitle: str, ytitle: str) -> Dict[str, Any]:
        """Standard Plotly layout for signal plots."""
        return {
            "xaxis": {
                "title": {"text": xtitle, "font": {"color": "#f1f5f9", "size": 13}},
                "range": list(self.TIME_RANGE),
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
                "color": "#94a3b8",
            },
            "yaxis": {
                "title": {"text": ytitle, "font": {"color": "#f1f5f9", "size": 13}},
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
                "color": "#94a3b8",
            },
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

    def _create_original_plot(self) -> Dict[str, Any]:
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
            "layout": self._get_base_layout("t (seconds)", "Amplitude"),
        }

    def _create_transformed_plot(self) -> Dict[str, Any]:
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
            "layout": self._get_base_layout("t (seconds)", "Amplitude"),
        }

    def _create_quiz_plot(self) -> Dict[str, Any]:
        """Plot: Quiz challenge signal."""
        if self._quiz_answered:
            if self._quiz_correct:
                title = f"✓ Correct! Answer: {self._quiz_answer}"
            else:
                title = f"✗ Incorrect. Answer: {self._quiz_answer}"
        else:
            title = "Quiz: What operations produced this signal?"

        data = [
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
                "y": self._quiz_signal.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": "g(t) = ???",
                "line": {"color": "#f59e0b", "width": 2.5},
            },
        ]

        return {
            "id": "quiz_challenge",
            "title": title,
            "data": data,
            "layout": self._get_base_layout("t (seconds)", "Amplitude"),
        }
