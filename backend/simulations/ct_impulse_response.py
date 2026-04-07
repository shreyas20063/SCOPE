"""
CT Impulse Response Builder Simulator

Interactive exploration of how the CT impulse response e^(pt)u(t) is constructed
term-by-term from the operator series expansion:
    A(1 + pA + p^2 A^2 + ...) delta(t) = (1 + pt + p^2 t^2/2! + ...) u(t) = e^(pt) u(t)
"""

import time
from typing import Any, Dict, List, Optional

import numpy as np

from .base_simulator import BaseSimulator


class CTImpulseResponseSimulator(BaseSimulator):
    """Simulator for CT impulse response Taylor series buildup."""

    MAX_DISPLAY_VALUE = 100.0
    NUM_SAMPLES = 500
    MAX_TERMS = 20
    MARGINAL_EPSILON = 0.05

    TERM_COLORS = [
        "#14b8a6", "#3b82f6", "#8b5cf6", "#ec4899",
        "#f59e0b", "#10b981", "#ef4444", "#06b6d4",
    ]

    PARAMETER_SCHEMA = {
        "pole_p": {
            "type": "slider",
            "min": -5.0,
            "max": 5.0,
            "step": 0.1,
            "default": -2.0,
        },
        "num_terms": {
            "type": "slider",
            "min": 1,
            "max": 20,
            "step": 1,
            "default": 10,
        },
        "show_all_partials": {
            "type": "checkbox",
            "default": True,
        },
        "show_individual_terms": {
            "type": "checkbox",
            "default": False,
        },
    }

    DEFAULT_PARAMS = {
        "pole_p": -2.0,
        "num_terms": 10,
        "show_all_partials": True,
        "show_individual_terms": False,
    }


    def __init__(self, simulation_id: str):
        super().__init__(simulation_id)
        self._current_terms: int = 0
        self._revision: int = 0

    def initialize(self, params: Optional[Dict[str, Any]] = None) -> None:
        self.parameters = {**self.DEFAULT_PARAMS, **(params or {})}
        for name, value in self.parameters.items():
            if name in self.PARAMETER_SCHEMA:
                self.parameters[name] = self._validate_param(name, value)
        self._current_terms = 0
        self._revision += 1
        self._initialized = True

    def reset(self) -> Dict[str, Any]:
        """Reset all state: parameters and term counter."""
        self._current_terms = 0
        self._revision += 1
        self.parameters = self.DEFAULT_PARAMS.copy()
        self._initialized = True
        return self.get_state()

    def update_parameter(self, name: str, value: Any) -> Dict[str, Any]:
        if name in self.parameters:
            old_val = self.parameters.get(name)
            self.parameters[name] = self._validate_param(name, value)
            # Reset term counter when pole changes so the user rebuilds
            if name == "pole_p" and old_val != self.parameters[name]:
                self._current_terms = 0
                self._revision += 1
        return self.get_state()

    def handle_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle custom button actions for progressive term addition."""
        max_terms = int(self.parameters["num_terms"])

        if action == "add_term":
            if self._current_terms < max_terms:
                self._current_terms += 1
        elif action == "remove_term":
            if self._current_terms > 0:
                self._current_terms -= 1
        elif action in ("reset_terms", "reset"):
            self._current_terms = 0
            self._revision += 1
            if action == "reset":
                self.parameters = self.DEFAULT_PARAMS.copy()

        return self.get_state()

    def get_plots(self) -> List[Dict[str, Any]]:
        data = self._compute()
        plots = [self._create_buildup_plot(data)]
        if bool(self.parameters["show_individual_terms"]) and self._current_terms > 0:
            plots.append(self._create_terms_plot(data))
        return plots

    def get_state(self) -> Dict[str, Any]:
        p = float(self.parameters["pole_p"])
        max_terms = int(self.parameters["num_terms"])

        # Convergence classification
        if p < -self.MARGINAL_EPSILON:
            convergence = "converging"
        elif p > self.MARGINAL_EPSILON:
            convergence = "diverging"
        else:
            convergence = "marginal"

        # Pole half-plane
        if p < 0:
            pole_half_plane = "left"
        elif p > 0:
            pole_half_plane = "right"
        else:
            pole_half_plane = "origin"

        # Latest term label
        k = max(self._current_terms - 1, 0)
        if self._current_terms == 0:
            latest_term_label = "No terms yet"
        elif k == 0:
            latest_term_label = "u(t)"
        elif k == 1:
            latest_term_label = "pt"
        else:
            latest_term_label = f"(pt)^{k}/{k}!"

        # Compute once — used for both plots and error
        data = self._compute()

        # Max approximation error at current term count
        max_error = 0.0
        if self._current_terms > 0:
            exact = data["exact"]
            partial = data["partial_sums"][self._current_terms - 1]
            errors = np.abs(exact - partial)
            mask = (np.abs(exact) < self.MAX_DISPLAY_VALUE) & (
                np.abs(partial) < self.MAX_DISPLAY_VALUE
            )
            if np.any(mask):
                max_error = float(np.max(errors[mask]))

        # Build plots from the same data
        plots = [self._create_buildup_plot(data)]
        if bool(self.parameters["show_individual_terms"]) and self._current_terms > 0:
            plots.append(self._create_terms_plot(data))

        return {
            "parameters": self.parameters.copy(),
            "plots": plots,
            "metadata": {
                "simulation_type": "ct_impulse_response",
            "hub_slots": self.HUB_SLOTS,
            "hub_domain": self.HUB_DOMAIN,
            "hub_dimensions": self.HUB_DIMENSIONS,
                "pole_p": p,
                "convergence": convergence,
                "pole_half_plane": pole_half_plane,
                "current_terms": self._current_terms,
                "max_terms": max_terms,
                "latest_term_label": latest_term_label,
                "max_error": round(max_error, 6),
                "revision": self._revision,
            },
        }

    # -- Computation -------------------------------------------------------

    def _adaptive_time_range(self, p: float) -> float:
        """Compute sensible t_max based on pole value."""
        abs_p = abs(p)
        if abs_p < 0.1:
            return 5.0
        return min(5.0, 8.0 / abs_p)

    def _compute(self) -> Dict[str, Any]:
        """Core computation: Taylor series terms, partial sums, and exact solution."""
        p = float(self.parameters["pole_p"])
        num_terms = self._current_terms

        t_max = self._adaptive_time_range(p)
        t = np.linspace(0, t_max, self.NUM_SAMPLES)

        # Exact solution: e^(pt) for t >= 0
        exact = np.exp(p * t)
        exact_clipped = np.clip(exact, -self.MAX_DISPLAY_VALUE, self.MAX_DISPLAY_VALUE)

        if num_terms == 0:
            return {
                "t": t,
                "exact": exact_clipped,
                "terms": np.empty((0, len(t))),
                "partial_sums": np.empty((0, len(t))),
                "p": p,
                "t_max": t_max,
            }

        # Compute terms using numerically stable recurrence:
        # T_0(t) = 1, T_k(t) = T_{k-1}(t) * (p*t) / k
        terms = np.zeros((num_terms, len(t)))
        terms[0] = np.ones_like(t)
        pt = p * t
        for k in range(1, num_terms):
            terms[k] = terms[k - 1] * pt / k

        # Partial sums: S_N = cumulative sum over terms axis
        partial_sums = np.cumsum(terms, axis=0)

        # Clip for display
        partial_sums_clipped = np.clip(
            partial_sums, -self.MAX_DISPLAY_VALUE, self.MAX_DISPLAY_VALUE
        )
        terms_clipped = np.clip(
            terms, -self.MAX_DISPLAY_VALUE, self.MAX_DISPLAY_VALUE
        )

        return {
            "t": t,
            "exact": exact_clipped,
            "terms": terms_clipped,
            "partial_sums": partial_sums_clipped,
            "p": p,
            "t_max": t_max,
        }

    # -- Plot construction -------------------------------------------------

    def _get_base_layout(
        self, xtitle: str, ytitle: str, plot_id: str
    ) -> Dict[str, Any]:
        """Standard Plotly layout with datarevision/uirevision."""
        p = float(self.parameters["pole_p"])
        return {
            "xaxis": {
                "title": {"text": xtitle, "font": {"color": "#f1f5f9", "size": 13}},
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
            "font": {
                "family": "Inter, sans-serif",
                "size": 12,
                "color": "#f1f5f9",
            },
            "margin": {"t": 45, "r": 25, "b": 55, "l": 60},
            "showlegend": True,
            "legend": {
                "font": {"color": "#94a3b8", "size": 11},
                "bgcolor": "rgba(0,0,0,0)",
                "x": 0.98,
                "y": 0.98,
                "xanchor": "right",
                "yanchor": "top",
            },
            # datarevision: always unique so Plotly re-renders on every update
            "datarevision": f"{plot_id}-{p}-{self._current_terms}-{time.time()}",
            # uirevision: changes on reset/pole change to clear zoom state;
            # stays same during add/remove term so zoom is preserved
            "uirevision": f"{plot_id}-{self._revision}",
        }

    def _create_buildup_plot(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Build the main Taylor series buildup plot."""
        t = data["t"]
        exact = data["exact"]
        partial_sums = data["partial_sums"]
        p = data["p"]
        num_terms = self._current_terms
        show_all = bool(self.parameters["show_all_partials"])

        t_list = t.tolist()
        traces = []

        # Zero reference line
        traces.append(
            {
                "x": [t_list[0], t_list[-1]],
                "y": [0, 0],
                "type": "scatter",
                "mode": "lines",
                "name": "Zero",
                "line": {"color": "rgba(148,163,184,0.3)", "width": 1, "dash": "dash"},
                "showlegend": False,
                "hoverinfo": "skip",
            }
        )

        # Partial sums
        if num_terms > 0:
            for k in range(num_terms):
                y_k = partial_sums[k].tolist()
                is_latest = k == num_terms - 1

                if show_all or is_latest:
                    opacity = (
                        1.0
                        if is_latest
                        else 0.15 + 0.85 * k / max(num_terms - 1, 1)
                    )
                    width = 2.5 if is_latest else 1.5

                    label_k = k + 1
                    name = (
                        f"S_{label_k} ({label_k} term{'s' if label_k > 1 else ''})"
                    )

                    traces.append(
                        {
                            "x": t_list,
                            "y": y_k,
                            "type": "scatter",
                            "mode": "lines",
                            "name": name,
                            "line": {
                                "color": "#14b8a6",
                                "width": width,
                                "dash": "dot" if is_latest else "dash",
                            },
                            "opacity": opacity,
                            "showlegend": is_latest,
                            "hovertemplate": f"{name}<br>t=%{{x:.3f}}<br>S=%{{y:.4f}}<extra></extra>",
                        }
                    )

        # Exact solution (on top)
        p_display = f"{p:g}"
        traces.append(
            {
                "x": t_list,
                "y": exact.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": f"e^({p_display}t) exact",
                "line": {"color": "#3b82f6", "width": 3},
                "hovertemplate": "Exact<br>t=%{x:.3f}<br>y=%{y:.4f}<extra></extra>",
            }
        )

        layout = self._get_base_layout("t (seconds)", "Amplitude", "taylor_buildup")
        layout["xaxis"]["range"] = [0, data["t_max"]]
        # Let Plotly auto-range the y-axis so data never goes out of bounds
        layout["yaxis"]["autorange"] = True

        title = "Taylor Series Buildup"
        if num_terms > 0:
            title += f"  \u2014  {num_terms} term{'s' if num_terms > 1 else ''}"

        return {
            "id": "taylor_buildup",
            "title": title,
            "data": traces,
            "layout": layout,
        }

    def _create_terms_plot(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Build the individual Taylor terms plot."""
        t = data["t"]
        terms = data["terms"]
        p = data["p"]
        num_terms = self._current_terms

        t_list = t.tolist()
        traces = []

        for k in range(num_terms):
            y_k = terms[k].tolist()
            color = self.TERM_COLORS[k % len(self.TERM_COLORS)]

            if k == 0:
                name = "T\u2080 = 1"
            elif k == 1:
                name = "T\u2081 = pt"
            else:
                name = f"T\u2096 = (pt)^{k}/{k}!"

            traces.append(
                {
                    "x": t_list,
                    "y": y_k,
                    "type": "scatter",
                    "mode": "lines",
                    "name": name,
                    "line": {"color": color, "width": 2},
                    "hovertemplate": f"{name}<br>t=%{{x:.3f}}<br>T=%{{y:.4f}}<extra></extra>",
                }
            )

        layout = self._get_base_layout(
            "t (seconds)", "Term Value", "individual_terms"
        )
        layout["xaxis"]["range"] = [0, data["t_max"]]
        layout["yaxis"]["autorange"] = True

        return {
            "id": "individual_terms",
            "title": "Individual Taylor Terms T_k(t) = (pt)^k / k!",
            "data": traces,
            "layout": layout,
        }
