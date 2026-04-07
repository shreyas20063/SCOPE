"""
DT ↔ CT Side-by-Side Comparator

Shows how the same pole value p produces pⁿu[n] in DT vs eᵖᵗu(t) in CT,
with fundamentally different stability regions: unit circle (DT) vs left
half-plane (CT).
"""

import random
import time
from typing import Any, Dict, List, Optional

import numpy as np

from .base_simulator import BaseSimulator


class DTCTComparatorSimulator(BaseSimulator):
    """Simulator comparing first-order DT and CT system responses."""

    # Constants
    CT_NUM_POINTS = 500
    Y_CLIP = 50.0  # Clip extreme values to prevent Plotly overflow

    PARAMETER_SCHEMA = {
        "p": {
            "type": "slider",
            "min": -2.0,
            "max": 2.0,
            "step": 0.01,
            "default": 0.5,
        },
        "num_samples": {
            "type": "slider",
            "min": 5,
            "max": 30,
            "step": 1,
            "default": 20,
        },
        "ct_duration": {
            "type": "slider",
            "min": 1.0,
            "max": 8.0,
            "step": 0.5,
            "default": 4.0,
        },
        "show_envelope": {
            "type": "checkbox",
            "default": True,
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
        "p": 0.5,
        "num_samples": 20,
        "ct_duration": 4.0,
        "show_envelope": True,
        "mode": "explore",
    }


    def __init__(self, simulation_id: str) -> None:
        super().__init__(simulation_id)
        # Monotonic revision counter — forces Plotly to reset axis state
        self._revision: int = 0
        # Quiz state
        self._quiz_p: Optional[float] = None
        self._quiz_answer: Optional[str] = None
        self._quiz_generated: bool = False
        self._quiz_user_answer: Optional[str] = None
        self._quiz_answered: bool = False
        self._quiz_correct: Optional[bool] = None

    def initialize(self, params: Optional[Dict[str, Any]] = None) -> None:
        self.parameters = {**self.DEFAULT_PARAMS, **(params or {})}
        for name, value in self.parameters.items():
            if name in self.PARAMETER_SCHEMA:
                self.parameters[name] = self._validate_param(name, value)
        self._revision = 0
        self._initialized = True

    def update_parameter(self, name: str, value: Any) -> Dict[str, Any]:
        if name in self.parameters:
            old_value = self.parameters.get(name)
            self.parameters[name] = self._validate_param(name, value)
            # Mode change → full reset of quiz state
            if name == "mode":
                self._reset_quiz_state()
                # Generate a fresh quiz immediately when entering quiz mode
                if value == "quiz":
                    self._generate_quiz()
        self._revision += 1
        return self.get_state()

    def reset(self) -> Dict[str, Any]:
        """Reset all params and quiz state to defaults."""
        self.parameters = self.DEFAULT_PARAMS.copy()
        self._initialized = True
        self._revision += 1
        self._reset_quiz_state()
        return self.get_state()

    def _reset_quiz_state(self) -> None:
        """Clear all quiz-related internal state."""
        self._quiz_generated = False
        self._quiz_answered = False
        self._quiz_correct = None
        self._quiz_user_answer = None
        self._quiz_p = None
        self._quiz_answer = None

    def handle_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if action == "new_quiz":
            self._reset_quiz_state()
            self._generate_quiz()
            self._revision += 1
        elif action == "check_quiz":
            user_answer = params.get("answer", "")
            self._quiz_user_answer = user_answer
            self._quiz_answered = True
            self._quiz_correct = (user_answer == self._quiz_answer)
            self._revision += 1
        return self.get_state()

    # ── Computation ──────────────────────────────────────────────────────

    def _compute_dt(self, p: float, N: int) -> Dict[str, np.ndarray]:
        """Compute DT response y[n] = pⁿ u[n]."""
        n = np.arange(0, N)
        if p == 0.0:
            y = np.zeros(N)
            y[0] = 1.0
        else:
            y = np.float64(p) ** n

        # Envelope |p|^n
        abs_p = abs(p)
        if abs_p == 0.0:
            envelope = np.zeros(N)
            envelope[0] = 1.0
        else:
            envelope = np.float64(abs_p) ** n

        # Clip extreme values
        y = np.clip(y, -self.Y_CLIP, self.Y_CLIP)
        envelope = np.clip(envelope, 0, self.Y_CLIP)

        return {"n": n, "y": y, "envelope": envelope}

    def _compute_ct(self, p: float, duration: float) -> Dict[str, np.ndarray]:
        """Compute CT response y(t) = eᵖᵗ u(t)."""
        t = np.linspace(0, duration, self.CT_NUM_POINTS)
        y = np.exp(p * t)

        # Clip extreme values
        y = np.clip(y, -self.Y_CLIP, self.Y_CLIP)

        # Envelope for CT
        envelope = np.abs(y)

        return {"t": t, "y": y, "envelope": envelope}

    @staticmethod
    def _smart_y_range(y_vals: np.ndarray, pad: float = 0.15) -> List[float]:
        """Compute y-axis range with padding, handling edge cases."""
        y_min = float(np.nanmin(y_vals))
        y_max = float(np.nanmax(y_vals))

        # Protect against flat signals
        if abs(y_max - y_min) < 1e-6:
            y_min -= 0.5
            y_max += 0.5

        span = y_max - y_min
        return [y_min - pad * span, y_max + pad * span]

    def _classify_stability(self, p: float) -> Dict[str, Any]:
        """Classify stability for both DT and CT."""
        abs_p = abs(p)

        # DT stability: |p| < 1
        if abs_p < 1.0 - 1e-9:
            dt_stable = True
            dt_status = "Stable"
            dt_behavior = "convergent"
        elif abs(abs_p - 1.0) < 1e-9:
            dt_stable = False
            dt_status = "Marginal"
            dt_behavior = "marginally_stable"
        else:
            dt_stable = False
            dt_status = "Unstable"
            dt_behavior = "divergent"

        # CT stability: p < 0
        if p < -1e-9:
            ct_stable = True
            ct_status = "Stable"
            ct_behavior = "convergent"
        elif abs(p) < 1e-9:
            ct_stable = False
            ct_status = "Marginal"
            ct_behavior = "marginally_stable"
        else:
            ct_stable = False
            ct_status = "Unstable"
            ct_behavior = "divergent"

        # Agreement classification
        if dt_stable and ct_stable:
            agreement = "both_stable"
        elif dt_stable and not ct_stable:
            agreement = "dt_only"
        elif not dt_stable and ct_stable:
            agreement = "ct_only"
        else:
            agreement = "neither_stable"

        return {
            "dt_stable": dt_stable,
            "dt_status": dt_status,
            "dt_behavior": dt_behavior,
            "dt_is_alternating": p < 0,
            "ct_stable": ct_stable,
            "ct_status": ct_status,
            "ct_behavior": ct_behavior,
            "agreement": agreement,
            "pole_value": round(p, 4),
            "abs_pole": round(abs_p, 4),
        }

    # ── Quiz ─────────────────────────────────────────────────────────────

    def _generate_quiz(self) -> None:
        """Generate a quiz question with a random pole value."""
        candidates = [
            (-1.5, "ct_only"),
            (-1.2, "ct_only"),
            (-1.0, "ct_only"),
            (-0.8, "both_stable"),
            (-0.5, "both_stable"),
            (-0.3, "both_stable"),
            (0.3, "dt_only"),
            (0.5, "dt_only"),
            (0.8, "dt_only"),
            (0.9, "dt_only"),
            (1.2, "neither_stable"),
            (1.5, "neither_stable"),
        ]

        self._quiz_p, self._quiz_answer = random.choice(candidates)
        self._quiz_generated = True
        self._quiz_answered = False
        self._quiz_correct = None
        self._quiz_user_answer = None

    # ── Plot Builders ────────────────────────────────────────────────────

    def _base_layout(self) -> Dict[str, Any]:
        """Shared layout fields for both plots."""
        return {
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "font": {"family": "Inter, sans-serif", "size": 12, "color": "#f1f5f9"},
            "margin": {"t": 45, "r": 20, "b": 55, "l": 55},
            "showlegend": True,
            "legend": {"font": {"color": "#94a3b8", "size": 10}, "bgcolor": "rgba(0,0,0,0)"},
        }

    def _build_dt_plot(self, dt_data: Dict, stability: Dict, show_envelope: bool) -> Dict[str, Any]:
        """Build Plotly dict for DT stem plot."""
        n = dt_data["n"]
        y = dt_data["y"]
        p = stability["pole_value"]
        color = "#3b82f6" if stability["dt_stable"] else "#ef4444"

        traces = []

        # Stem lines
        stem_x: List = []
        stem_y: List = []
        for i in range(len(n)):
            stem_x.extend([int(n[i]), int(n[i]), None])
            stem_y.extend([0, float(y[i]), None])

        traces.append({
            "x": stem_x,
            "y": stem_y,
            "type": "scatter",
            "mode": "lines",
            "name": "Stems",
            "line": {"color": color, "width": 2},
            "showlegend": False,
            "hoverinfo": "skip",
        })

        # Marker dots
        traces.append({
            "x": n.tolist(),
            "y": y.tolist(),
            "type": "scatter",
            "mode": "markers",
            "name": f"pⁿ u[n], p={p}",
            "marker": {
                "color": color,
                "size": 7,
                "line": {"color": "#1e293b", "width": 1},
            },
        })

        # Envelope
        if show_envelope and abs(p) > 1e-9:
            env = dt_data["envelope"]
            traces.append({
                "x": n.tolist(),
                "y": env.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": "|p|ⁿ",
                "line": {"color": "#10b981", "width": 1.5, "dash": "dash"},
            })
            traces.append({
                "x": n.tolist(),
                "y": (-env).tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": "−|p|ⁿ",
                "line": {"color": "#10b981", "width": 1.5, "dash": "dash"},
                "showlegend": False,
            })

        # Compute explicit y-axis range from all trace data
        all_y = list(y)
        if show_envelope and abs(p) > 1e-9:
            all_y.extend(dt_data["envelope"].tolist())
            all_y.extend((-dt_data["envelope"]).tolist())
        y_range = self._smart_y_range(np.array(all_y))

        rev = self._revision
        layout = {
            **self._base_layout(),
            "xaxis": {
                "title": {"text": "n (samples)", "font": {"color": "#f1f5f9", "size": 13}},
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
                "zerolinewidth": 2,
                "color": "#94a3b8",
                "dtick": 1 if len(n) <= 25 else 5,
            },
            "yaxis": {
                "title": {"text": "y[n]", "font": {"color": "#f1f5f9", "size": 13}},
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
                "zerolinewidth": 2,
                "color": "#94a3b8",
                "range": y_range,
            },
            "datarevision": f"dt-{rev}-{time.time()}",
            "uirevision": f"dt-{rev}",
        }

        return {
            "id": "dt_response",
            "title": f"DT: y[n] = pⁿ u[n]",
            "data": traces,
            "layout": layout,
        }

    def _build_ct_plot(self, ct_data: Dict, stability: Dict, show_envelope: bool) -> Dict[str, Any]:
        """Build Plotly dict for CT continuous plot."""
        t = ct_data["t"]
        y = ct_data["y"]
        p = stability["pole_value"]
        color = "#3b82f6" if stability["ct_stable"] else "#ef4444"

        traces = []

        # Main response curve
        traces.append({
            "x": t.tolist(),
            "y": y.tolist(),
            "type": "scatter",
            "mode": "lines",
            "name": f"eᵖᵗ u(t), p={p}",
            "line": {"color": color, "width": 2.5},
        })

        # Envelope
        if show_envelope and abs(p) > 1e-9:
            env = ct_data["envelope"]
            traces.append({
                "x": t.tolist(),
                "y": env.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": "eᴿᵉ⁽ᵖ⁾ᵗ",
                "line": {"color": "#10b981", "width": 1.5, "dash": "dash"},
            })

        # Compute explicit y-axis range
        all_y = list(y)
        if show_envelope and abs(p) > 1e-9:
            all_y.extend(ct_data["envelope"].tolist())
        y_range = self._smart_y_range(np.array(all_y))

        rev = self._revision
        layout = {
            **self._base_layout(),
            "xaxis": {
                "title": {"text": "t (seconds)", "font": {"color": "#f1f5f9", "size": 13}},
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
                "zerolinewidth": 2,
                "color": "#94a3b8",
            },
            "yaxis": {
                "title": {"text": "y(t)", "font": {"color": "#f1f5f9", "size": 13}},
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
                "zerolinewidth": 2,
                "color": "#94a3b8",
                "range": y_range,
            },
            "datarevision": f"ct-{rev}-{time.time()}",
            "uirevision": f"ct-{rev}",
        }

        return {
            "id": "ct_response",
            "title": f"CT: y(t) = eᵖᵗ u(t)",
            "data": traces,
            "layout": layout,
        }

    # ── Public Interface ─────────────────────────────────────────────────

    def _get_active_pole(self) -> float:
        """Return the pole value to use for plots — quiz pole in quiz mode, slider pole otherwise."""
        if self.parameters["mode"] == "quiz" and self._quiz_generated:
            return float(self._quiz_p)
        return float(self.parameters["p"])

    def get_plots(self) -> List[Dict[str, Any]]:
        p = self._get_active_pole()
        N = int(self.parameters["num_samples"])
        duration = float(self.parameters["ct_duration"])
        show_envelope = bool(self.parameters["show_envelope"])

        stability = self._classify_stability(p)
        dt_data = self._compute_dt(p, N)
        ct_data = self._compute_ct(p, duration)

        return [
            self._build_dt_plot(dt_data, stability, show_envelope),
            self._build_ct_plot(ct_data, stability, show_envelope),
        ]

    def get_state(self) -> Dict[str, Any]:
        p_explore = float(self.parameters["p"])
        p_active = self._get_active_pole()
        stability = self._classify_stability(p_active)

        # Auto-generate quiz on first access in quiz mode
        if self.parameters["mode"] == "quiz" and not self._quiz_generated:
            self._generate_quiz()
            # Recompute stability for the quiz pole
            p_active = float(self._quiz_p)
            stability = self._classify_stability(p_active)

        state = super().get_state()
        state["metadata"] = {
            "simulation_type": "dt_ct_comparator",
            "hub_slots": self.HUB_SLOTS,
            "hub_domain": self.HUB_DOMAIN,
            "hub_dimensions": self.HUB_DIMENSIONS,
            **stability,
            "mode": self.parameters["mode"],
            "revision": self._revision,
        }

        if self.parameters["mode"] == "quiz" and self._quiz_generated:
            state["metadata"]["quiz"] = {
                "quiz_p": self._quiz_p,
                "answered": self._quiz_answered,
                "correct": self._quiz_correct,
                "correct_answer": self._quiz_answer if self._quiz_answered else None,
                "user_answer": self._quiz_user_answer if self._quiz_answered else None,
            }

        return state
