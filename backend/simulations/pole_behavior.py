"""
Pole Behavior Explorer

Interactive visualization of first-order DT system y[n] = p0^n * u[n].
Users drag a pole on the real number line and observe:
- Stem plot of the unit-sample response
- Color-coded stability regions (convergent / divergent)
- Optional envelope |p0|^n overlay
- Quiz mode: identify the pole from a mystery stem plot
"""

import random
import time
from typing import Any, Dict, List, Optional

import numpy as np

from .base_simulator import BaseSimulator


class PoleBehaviorSimulator(BaseSimulator):
    """Simulator for first-order DT pole behavior exploration."""

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

    def __init__(self, simulation_id: str) -> None:
        super().__init__(simulation_id)
        self._n: Optional[np.ndarray] = None
        self._y: Optional[np.ndarray] = None
        self._envelope: Optional[np.ndarray] = None

        # Quiz state
        self._quiz_pole: Optional[float] = None
        self._quiz_y: Optional[np.ndarray] = None
        self._quiz_answered: bool = False
        self._quiz_correct: Optional[bool] = None
        self._quiz_user_answer: Optional[float] = None
        self._quiz_generated: bool = False

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
                self._quiz_generated = False
                self._quiz_answered = False
                self._quiz_correct = None
                self._quiz_user_answer = None
        self._compute()
        return self.get_state()

    def reset(self) -> Dict[str, Any]:
        """Reset all parameters and quiz state to defaults."""
        self.parameters = self.DEFAULT_PARAMS.copy()
        self._initialized = True
        # Reset quiz state
        self._quiz_pole = None
        self._quiz_y = None
        self._quiz_generated = False
        self._quiz_answered = False
        self._quiz_correct = None
        self._quiz_user_answer = None
        # Recompute with default params
        self._compute()
        return self.get_state()

    def _compute(self) -> None:
        p0 = float(self.parameters["pole_position"])
        N = int(self.parameters["num_samples"])

        self._n = np.arange(0, N)

        # Handle p0 = 0: 0^0 = 1, 0^n = 0 for n >= 1
        if p0 == 0.0:
            self._y = np.zeros(N)
            self._y[0] = 1.0
        else:
            self._y = np.float64(p0) ** self._n

        # Envelope: |p0|^n
        abs_p0 = abs(p0)
        if abs_p0 == 0.0:
            self._envelope = np.zeros(N)
            self._envelope[0] = 1.0
        else:
            self._envelope = np.float64(abs_p0) ** self._n

        # Quiz generation
        if self.parameters["mode"] == "quiz" and not self._quiz_generated:
            self._generate_quiz()

    def _generate_quiz(self) -> None:
        candidates = [
            -1.5, -1.2, -1.0, -0.9, -0.8, -0.7, -0.5, -0.3,
            0.0, 0.3, 0.5, 0.7, 0.8, 0.9, 1.0, 1.2, 1.5,
        ]
        self._quiz_pole = random.choice(candidates)
        N = int(self.parameters["num_samples"])
        n = np.arange(0, N)

        if self._quiz_pole == 0.0:
            self._quiz_y = np.zeros(N)
            self._quiz_y[0] = 1.0
        else:
            self._quiz_y = np.float64(self._quiz_pole) ** n

        self._quiz_generated = True
        self._quiz_answered = False
        self._quiz_correct = None
        self._quiz_user_answer = None

    def handle_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if action == "new_quiz":
            self._quiz_generated = False
            self._quiz_answered = False
            self._quiz_correct = None
            self._quiz_user_answer = None
            self._compute()
        elif action == "check_answer":
            user_pole = float(params.get("answer", 0.0))
            self._quiz_user_answer = user_pole
            self._quiz_answered = True
            self._quiz_correct = abs(user_pole - self._quiz_pole) < 0.15
        return self.get_state()

    def get_plots(self) -> List[Dict[str, Any]]:
        # Always recompute to ensure plots match current parameters
        self._compute()

        if self.parameters["mode"] == "quiz":
            return [self._create_quiz_stem_plot()]
        return [self._create_stem_plot()]

    def _create_stem_plot(self) -> Dict[str, Any]:
        p0 = self.parameters["pole_position"]
        show_envelope = self.parameters["show_envelope"]
        traces = []

        # Stem lines: single trace with None separators for vertical lines
        stem_x: List = []
        stem_y: List = []
        for i in range(len(self._n)):
            stem_x.extend([int(self._n[i]), int(self._n[i]), None])
            stem_y.extend([0, float(self._y[i]), None])

        traces.append({
            "x": stem_x,
            "y": stem_y,
            "type": "scatter",
            "mode": "lines",
            "name": "Stems",
            "line": {"color": "#3b82f6", "width": 2},
            "showlegend": False,
            "hoverinfo": "skip",
        })

        # Marker dots at tips
        traces.append({
            "x": self._n.tolist(),
            "y": self._y.tolist(),
            "type": "scatter",
            "mode": "markers",
            "name": f"y[n] = ({p0})\u207f",
            "marker": {
                "color": "#3b82f6",
                "size": 8,
                "line": {"color": "#1e40af", "width": 1.5},
            },
        })

        # Envelope overlay (conditional)
        if show_envelope:
            traces.append({
                "x": self._n.tolist(),
                "y": self._envelope.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": f"|{p0}|\u207f (envelope)",
                "line": {"color": "#10b981", "width": 2, "dash": "dash"},
            })
            traces.append({
                "x": self._n.tolist(),
                "y": (-self._envelope).tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": f"\u2212|{p0}|\u207f",
                "line": {"color": "#10b981", "width": 2, "dash": "dash"},
                "showlegend": False,
            })

        return {
            "id": "stem_plot",
            "title": f"Unit-Sample Response: p\u2080 = {p0}",
            "data": traces,
            "layout": self._get_stem_layout(),
        }

    def _create_quiz_stem_plot(self) -> Dict[str, Any]:
        if not self._quiz_generated:
            self._generate_quiz()

        traces = []
        n_arr = np.arange(0, len(self._quiz_y))

        # Stems
        stem_x: List = []
        stem_y: List = []
        for i in range(len(n_arr)):
            stem_x.extend([int(n_arr[i]), int(n_arr[i]), None])
            stem_y.extend([0, float(self._quiz_y[i]), None])

        traces.append({
            "x": stem_x,
            "y": stem_y,
            "type": "scatter",
            "mode": "lines",
            "name": "Stems",
            "line": {"color": "#f59e0b", "width": 2},
            "showlegend": False,
            "hoverinfo": "skip",
        })

        traces.append({
            "x": n_arr.tolist(),
            "y": self._quiz_y.tolist(),
            "type": "scatter",
            "mode": "markers",
            "name": "y[n] = p\u2080\u207f (mystery)",
            "marker": {
                "color": "#f59e0b",
                "size": 8,
                "line": {"color": "#b45309", "width": 1.5},
            },
        })

        if self._quiz_answered:
            if self._quiz_correct:
                title = f"Correct! p\u2080 = {self._quiz_pole}"
            else:
                title = f"Incorrect. Actual p\u2080 = {self._quiz_pole}"
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
