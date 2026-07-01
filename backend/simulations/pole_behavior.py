"""Pole Behavior Explorer — first-order DT system y[n] = p0^n u[n].   Textbook: Oppenheim §2.3.

Drag a real pole and observe the unit-sample response stem plot, its |p0|^n
envelope, stability classification, and an optional quiz mode.
"""

import random
import time
from typing import Any, Dict, List, Optional

import numpy as np

from .base_simulator import BaseSimulator


class PoleBehaviorSimulator(BaseSimulator):
    """Simulator for first-order DT pole behavior exploration."""

    # ── 1. DEFINE ──────────────────────────────────────────────
    PARAMETER_SCHEMA = {
        "pole_position": {
            "type": "slider",
            "min": -2.0,
            "max": 2.0,
            "step": 0.01,
            "default": 0.5,
        },
        "num_samples": {
            "type": "slider",
            "min": 10,
            "max": 50,
            "step": 1,
            "default": 20,
        },
        "show_envelope": {
            "type": "checkbox",
            "default": False,
        },
        "mode": {
            "type": "select",
            "options": [
                {"value": "explore", "label": "Explore"},
                {"value": "quiz", "label": "Quiz"},
            ],
            "default": "explore",
        },
    }

    DEFAULT_PARAMS = {
        "pole_position": 0.5,
        "num_samples": 20,
        "show_envelope": False,
        "mode": "explore",
    }

    QUIZ_CANDIDATES = [
        -1.5, -1.2, -1.0, -0.9, -0.8, -0.7, -0.5, -0.3,
        0.0, 0.3, 0.5, 0.7, 0.8, 0.9, 1.0, 1.2, 1.5,
    ]

    def __init__(self, simulation_id: str) -> None:
        super().__init__(simulation_id)
        self._n: Optional[np.ndarray] = None
        self._y: Optional[np.ndarray] = None

        # Quiz state
        self._quiz_pole: Optional[float] = None
        self._quiz_y: Optional[np.ndarray] = None
        self._quiz_answered: bool = False
        self._quiz_correct: Optional[bool] = None
        self._quiz_user_answer: Optional[float] = None
        self._quiz_generated: bool = False

    # ── 2. LIFECYCLE ───────────────────────────────────────────
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
            if name == "mode":
                # Always reset quiz state on any mode change
                self._reset_quiz()
        self._compute()
        return self.get_state()

    def reset(self) -> Dict[str, Any]:
        """Reset all parameters and quiz state to defaults."""
        self.parameters = self.DEFAULT_PARAMS.copy()
        self._initialized = True
        self._reset_quiz()
        self._compute()
        return self.get_state()

    # ── 3. ACTIONS ─────────────────────────────────────────────
    def handle_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if action == "new_quiz":
            self._reset_quiz()
            self._compute()
        elif action == "check_answer":
            user_pole = float(params.get("answer", 0.0))
            self._quiz_user_answer = user_pole
            self._quiz_answered = True
            self._quiz_correct = abs(user_pole - self._quiz_pole) < 0.15
        return self.get_state()

    # ── 4. MATH ────────────────────────────────────────────────
    def _compute(self) -> None:
        p0 = float(self.parameters["pole_position"])
        N = int(self.parameters["num_samples"])

        # y[n] = p0^n u[n]; NumPy gives 0**0 == 1 and 0**n == 0 for n >= 1.
        self._n = np.arange(0, N)
        self._y = np.power(np.float64(p0), self._n)

        if self.parameters["mode"] == "quiz" and not self._quiz_generated:
            self._generate_quiz()

    def _generate_quiz(self) -> None:
        self._quiz_pole = random.choice(self.QUIZ_CANDIDATES)
        N = int(self.parameters["num_samples"])
        n = np.arange(0, N)
        self._quiz_y = np.power(np.float64(self._quiz_pole), n)

        self._quiz_generated = True
        self._quiz_answered = False
        self._quiz_correct = None
        self._quiz_user_answer = None

    def _reset_quiz(self) -> None:
        self._quiz_pole = None
        self._quiz_y = None
        self._quiz_generated = False
        self._quiz_answered = False
        self._quiz_correct = None
        self._quiz_user_answer = None

    # ── 5. PRESENT ─────────────────────────────────────────────
    def get_plots(self) -> List[Dict[str, Any]]:
        if self.parameters["mode"] == "quiz":
            return [self._create_quiz_stem_plot()]
        return [self._create_stem_plot()]

    @staticmethod
    def _stem_traces(
        n: np.ndarray,
        y: np.ndarray,
        name: str,
        stem_color: str,
        marker_line_color: str,
    ) -> List[Dict[str, Any]]:
        """Stem lines (with None separators) + marker dots for a discrete signal."""
        stem_x = np.empty(3 * len(n), dtype=object)
        stem_y = np.empty(3 * len(n), dtype=object)
        stem_x[0::3] = [int(v) for v in n]
        stem_x[1::3] = [int(v) for v in n]
        stem_x[2::3] = None
        stem_y[0::3] = 0
        stem_y[1::3] = [float(v) for v in y]
        stem_y[2::3] = None

        return [
            {
                "x": stem_x.tolist(),
                "y": stem_y.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": "Stems",
                "line": {"color": stem_color, "width": 2},
                "showlegend": False,
                "hoverinfo": "skip",
            },
            {
                "x": n.tolist(),
                "y": y.tolist(),
                "type": "scatter",
                "mode": "markers",
                "name": name,
                "marker": {
                    "color": stem_color,
                    "size": 8,
                    "line": {"color": marker_line_color, "width": 1.5},
                },
            },
        ]

    def _create_stem_plot(self) -> Dict[str, Any]:
        p0 = self.parameters["pole_position"]
        show_envelope = self.parameters["show_envelope"]

        traces = self._stem_traces(
            self._n, self._y, f"y[n] = ({p0})ⁿ", "#3b82f6", "#1e40af"
        )

        # Envelope |p0|^n == |p0^n| for integer n (conditional overlay)
        if show_envelope:
            envelope = np.abs(self._y)
            traces.append({
                "x": self._n.tolist(),
                "y": envelope.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": f"|{p0}|ⁿ (envelope)",
                "line": {"color": "#10b981", "width": 2, "dash": "dash"},
            })
            traces.append({
                "x": self._n.tolist(),
                "y": (-envelope).tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": f"−|{p0}|ⁿ",
                "line": {"color": "#10b981", "width": 2, "dash": "dash"},
                "showlegend": False,
            })

        return {
            "id": "stem_plot",
            "title": f"Unit-Sample Response: p₀ = {p0}",
            "data": traces,
            "layout": self._get_stem_layout(),
        }

    def _create_quiz_stem_plot(self) -> Dict[str, Any]:
        if not self._quiz_generated:
            self._generate_quiz()

        n_arr = np.arange(0, len(self._quiz_y))
        traces = self._stem_traces(
            n_arr, self._quiz_y, "y[n] = p₀ⁿ (mystery)", "#f59e0b", "#b45309"
        )

        if self._quiz_answered:
            if self._quiz_correct:
                title = f"Correct! p₀ = {self._quiz_pole}"
            else:
                title = f"Incorrect. Actual p₀ = {self._quiz_pole}"
        else:
            title = "Quiz: What pole produced this response?"

        return {
            "id": "stem_plot",
            "title": title,
            "data": traces,
            "layout": self._get_stem_layout(),
        }

    def _get_stem_layout(self) -> Dict[str, Any]:
        return {
            "xaxis": {
                "title": {"text": "n (samples)", "font": {"color": "#f1f5f9", "size": 13}},
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
                "color": "#94a3b8",
                "dtick": 1 if int(self.parameters["num_samples"]) <= 25 else 5,
            },
            "yaxis": {
                "title": {"text": "y[n]", "font": {"color": "#f1f5f9", "size": 13}},
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
                "zerolinewidth": 2,
                "color": "#94a3b8",
                "autorange": True,
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
            "datarevision": f"stem-{time.time()}",
            "uirevision": "stem_plot",
        }

    # ── 6. STATE ───────────────────────────────────────────────
    def get_state(self) -> Dict[str, Any]:
        state = super().get_state()
        p0 = float(self.parameters["pole_position"])
        abs_p0 = abs(p0)

        if abs_p0 < 1.0:
            behavior = "convergent"
            stability = "Stable"
        elif abs_p0 == 1.0:
            behavior = "marginally_stable"
            stability = "Marginally Stable"
        else:
            behavior = "divergent"
            stability = "Unstable"

        state["metadata"] = {
            "simulation_type": "pole_behavior",
            "hub_slots": self.HUB_SLOTS,
            "hub_domain": self.HUB_DOMAIN,
            "hub_dimensions": self.HUB_DIMENSIONS,
            "pole_position": round(p0, 4),
            "abs_pole": round(abs_p0, 4),
            "behavior": behavior,
            "stability": stability,
            "is_alternating": p0 < 0,
            "mode": self.parameters["mode"],
        }

        if self.parameters["mode"] == "quiz" and self._quiz_generated:
            state["metadata"]["quiz"] = {
                "answered": self._quiz_answered,
                "correct": self._quiz_correct,
                "actual_pole": self._quiz_pole if self._quiz_answered else None,
                "user_answer": self._quiz_user_answer if self._quiz_answered else None,
            }

        return state
