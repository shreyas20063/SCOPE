"""
Unit Impulse δ(t) Construction Lab Simulator

Builds intuition for the Dirac delta function by showing the limiting process:
rectangular pulses p_ε(t) of width 2ε and height 1/(2ε), always unit area,
as ε → 0.

Modes:
  - construction: Pulse + running integral converging to u(t)
  - system_response: Pulse through first-order CT system, output → e^(pt)u(t)
  - contrast: The "bad" building block w(t) = 1 at t=0 only (integral = 0)
"""

import time
from typing import Any, Dict, List, Optional

import numpy as np

from .base_simulator import BaseSimulator

# NumPy 2.0 renamed trapz -> trapezoid
_trapz = np.trapezoid if hasattr(np, 'trapezoid') else np.trapz

# --- Constants ---
NUM_SAMPLES = 2000
T_MIN = -3.0
T_MAX = 5.0


class ImpulseConstructionSimulator(BaseSimulator):
    """Simulator for the unit impulse construction lab."""

    PARAMETER_SCHEMA = {
        "epsilon": {
            "type": "slider",
            "min": 0.01,
            "max": 1.0,
            "step": 0.01,
            "default": 0.5,
        },
        "mode": {
            "type": "select",
            "options": [
                {"value": "construction", "label": "Delta Construction"},
                {"value": "system_response", "label": "System Response"},
                {"value": "contrast", "label": "Contrast"},
            ],
            "default": "construction",
        },
        "system_pole": {
            "type": "slider",
            "min": -5.0,
            "max": -0.1,
            "step": 0.1,
            "default": -1.0,
        },
        "show_limit": {
            "type": "checkbox",
            "default": True,
        },
    }

    DEFAULT_PARAMS = {
        "epsilon": 0.5,
        "mode": "construction",
        "system_pole": -1.0,
        "show_limit": True,
    }

    HUB_SLOTS = []

    def initialize(self, params: Optional[Dict[str, Any]] = None) -> None:
        self.parameters = {**self.DEFAULT_PARAMS, **(params or {})}
        for name, value in self.parameters.items():
            self.parameters[name] = self._validate_param(name, value)
        self._initialized = True
        self._compute()

    def update_parameter(self, name: str, value: Any) -> Dict[str, Any]:
        if name in self.parameters:
            self.parameters[name] = self._validate_param(name, value)
        self._compute()
        return self.get_state()

    # ------------------------------------------------------------------
    # Internal computation
    # ------------------------------------------------------------------

    def _compute(self) -> None:
        """Recompute all derived arrays from current parameters."""
        eps = float(self.parameters["epsilon"])
        mode = self.parameters["mode"]

        self._t = np.linspace(T_MIN, T_MAX, NUM_SAMPLES)
        self._dt = self._t[1] - self._t[0]

        # Rectangular pulse — always needed
        height = 1.0 / (2.0 * eps)
        self._pulse = np.where(np.abs(self._t) <= eps, height, 0.0)
        self._height = height
        self._area_numerical = float(_trapz(self._pulse, self._t))

        if mode == "construction":
            self._integral = np.cumsum(self._pulse) * self._dt
        elif mode == "system_response":
            p = float(self.parameters["system_pole"])
            self._system_output = self._analytical_convolution(eps, p)
        # contrast mode has no heavy precompute

    def _analytical_convolution(self, eps: float, p: float) -> np.ndarray:
        """Exact convolution of p_ε(t) with h(t) = e^(pt)u(t), p < 0.

        Piecewise closed-form:
          t < -ε         → 0
          -ε ≤ t < ε     → 1/(2ε·(-p)) · (1 − e^(p(t+ε)))
          t ≥ ε           → 1/(2ε·(-p)) · e^(pt) · (e^(−pε) − e^(pε))
        """
        t = self._t
        neg_p = -p  # positive since p < 0
        scale = 1.0 / (2.0 * eps * neg_p)

        y = np.zeros_like(t)

        # Region 2: -eps <= t < eps
        mask2 = (t >= -eps) & (t < eps)
        y[mask2] = scale * (1.0 - np.exp(p * (t[mask2] + eps)))

        # Region 3: t >= eps
        mask3 = t >= eps
        y[mask3] = scale * np.exp(p * t[mask3]) * (np.exp(-p * eps) - np.exp(p * eps))

        return y

    # ------------------------------------------------------------------
    # Plot builders
    # ------------------------------------------------------------------

    def get_plots(self) -> List[Dict[str, Any]]:
        mode = self.parameters["mode"]
        if mode == "construction":
            return [self._build_pulse_plot(), self._build_integral_plot()]
        elif mode == "system_response":
            return [self._build_pulse_plot(), self._build_system_output_plot()]
        else:  # contrast
            return [self._build_contrast_pulse_plot(), self._build_contrast_integral_plot()]

    # --- Pulse plot (construction & system_response) ---

    def _build_pulse_plot(self) -> Dict[str, Any]:
        eps = float(self.parameters["epsilon"])
        t_list = self._t.tolist()
        pulse_list = self._pulse.tolist()

        traces = [
            {
                "x": t_list,
                "y": pulse_list,
                "type": "scatter",
                "mode": "lines",
                "name": f"p_\u03b5(t)  \u03b5={eps:.2f}",
                "line": {"color": "#3b82f6", "width": 2.5},
                "fill": "tozeroy",
                "fillcolor": "rgba(59,130,246,0.15)",
            },
        ]

        layout = self._base_layout("pulse_plot")
        layout["xaxis"]["title"] = {"text": "t (seconds)", "font": {"size": 13}}
        layout["yaxis"]["title"] = {"text": "Amplitude", "font": {"size": 13}}

        # Dynamic y-axis: always show full pulse with 15% headroom
        y_top = self._height * 1.15
        layout["yaxis"]["range"] = [-y_top * 0.03, y_top]
        layout["yaxis"]["autorange"] = False

        # Annotation showing height value for readability
        if self._height > 5:
            layout["annotations"] = [
                {
                    "x": 0,
                    "y": self._height,
                    "text": f"  h = {self._height:.1f}",
                    "showarrow": False,
                    "xanchor": "left",
                    "yanchor": "bottom",
                    "font": {"color": "#3b82f6", "size": 11, "family": "Fira Code, monospace"},
                }
            ]

        return {
            "id": "pulse_plot",
            "title": f"Rectangular Pulse p_\u03b5(t) \u2014 \u03b5 = {eps:.3f}",
            "data": traces,
            "layout": layout,
        }

    # --- Integral plot (construction mode) ---

    def _build_integral_plot(self) -> Dict[str, Any]:
        t_list = self._t.tolist()
        integral_list = self._integral.tolist()
        show_limit = bool(self.parameters["show_limit"])

        traces = [
            {
                "x": t_list,
                "y": integral_list,
                "type": "scatter",
                "mode": "lines",
                "name": "\u222bp_\u03b5(\u03c4)d\u03c4",
                "line": {"color": "#ef4444", "width": 2.5},
            },
        ]

        if show_limit:
            unit_step = np.where(self._t >= 0, 1.0, 0.0).tolist()
            traces.append(
                {
                    "x": t_list,
                    "y": unit_step,
                    "type": "scatter",
                    "mode": "lines",
                    "name": "u(t) \u2014 ideal limit",
                    "line": {"color": "#10b981", "width": 2, "dash": "dash"},
                }
            )

        layout = self._base_layout("integral_plot")
        layout["xaxis"]["title"] = {"text": "t (seconds)", "font": {"size": 13}}
        layout["yaxis"]["title"] = {"text": "Amplitude", "font": {"size": 13}}
        layout["yaxis"]["range"] = [-0.15, 1.35]
        layout["yaxis"]["autorange"] = False

        return {
            "id": "integral_plot",
            "title": "Running Integral \u2192 converges to u(t)",
            "data": traces,
            "layout": layout,
        }

    # --- System output plot (system_response mode) ---

    def _build_system_output_plot(self) -> Dict[str, Any]:
        t_list = self._t.tolist()
        output_list = self._system_output.tolist()
        p = float(self.parameters["system_pole"])
        show_limit = bool(self.parameters["show_limit"])

        traces = [
            {
                "x": t_list,
                "y": output_list,
                "type": "scatter",
                "mode": "lines",
                "name": f"System output (p={p:.1f})",
                "line": {"color": "#ef4444", "width": 2.5},
            },
        ]

        if show_limit:
            ideal = np.where(self._t >= 0, np.exp(p * self._t), 0.0).tolist()
            traces.append(
                {
                    "x": t_list,
                    "y": ideal,
                    "type": "scatter",
                    "mode": "lines",
                    "name": f"e^({p:.1f}t)u(t) \u2014 ideal limit",
                    "line": {"color": "#10b981", "width": 2, "dash": "dash"},
                }
            )

        # Compute dynamic y range from actual data
        y_vals = self._system_output
        y_max = float(np.max(y_vals)) if len(y_vals) > 0 else 1.0
        y_min = float(np.min(y_vals)) if len(y_vals) > 0 else 0.0
        pad = max((y_max - y_min) * 0.15, 0.1)

        layout = self._base_layout("system_output")
        layout["xaxis"]["title"] = {"text": "t (seconds)", "font": {"size": 13}}
        layout["yaxis"]["title"] = {"text": "Amplitude", "font": {"size": 13}}
        layout["yaxis"]["range"] = [y_min - pad * 0.3, y_max + pad]
        layout["yaxis"]["autorange"] = False

        return {
            "id": "system_output",
            "title": f"First-Order System Output \u2014 pole p = {p:.1f}",
            "data": traces,
            "layout": layout,
        }

    # --- Contrast plots ---

    def _build_contrast_pulse_plot(self) -> Dict[str, Any]:
        """w(t) = 1 only at t=0, 0 elsewhere — shown as a single marker."""
        t_list = self._t.tolist()
        zero_line = np.zeros_like(self._t).tolist()

        traces = [
            # Horizontal zero line
            {
                "x": t_list,
                "y": zero_line,
                "type": "scatter",
                "mode": "lines",
                "name": "w(t) = 0 elsewhere",
                "line": {"color": "rgba(245,158,11,0.4)", "width": 1.5},
                "showlegend": False,
            },
            # Single marker at (0, 1)
            {
                "x": [0.0],
                "y": [1.0],
                "type": "scatter",
                "mode": "markers",
                "name": "w(0) = 1",
                "marker": {"color": "#f59e0b", "size": 12, "symbol": "circle"},
            },
        ]

        layout = self._base_layout("contrast_plot")
        layout["xaxis"]["title"] = {"text": "t (seconds)", "font": {"size": 13}}
        layout["yaxis"]["title"] = {"text": "Amplitude", "font": {"size": 13}}
        layout["yaxis"]["range"] = [-0.15, 1.5]
        layout["yaxis"]["autorange"] = False

        return {
            "id": "contrast_plot",
            "title": "\"Bad\" Building Block: w(t) = 1 at t=0 only",
            "data": traces,
            "layout": layout,
        }

    def _build_contrast_integral_plot(self) -> Dict[str, Any]:
        """Integral of w(t) is identically zero — contrasted with u(t)."""
        t_list = self._t.tolist()
        zero_line = np.zeros_like(self._t).tolist()
        show_limit = bool(self.parameters["show_limit"])

        traces = [
            {
                "x": t_list,
                "y": zero_line,
                "type": "scatter",
                "mode": "lines",
                "name": "\u222bw(\u03c4)d\u03c4 = 0",
                "line": {"color": "#ef4444", "width": 2.5},
            },
        ]

        if show_limit:
            unit_step = np.where(self._t >= 0, 1.0, 0.0).tolist()
            traces.append(
                {
                    "x": t_list,
                    "y": unit_step,
                    "type": "scatter",
                    "mode": "lines",
                    "name": "u(t) \u2014 what we need",
                    "line": {"color": "#10b981", "width": 2, "dash": "dash"},
                }
            )

        layout = self._base_layout("contrast_integral")
        layout["xaxis"]["title"] = {"text": "t (seconds)", "font": {"size": 13}}
        layout["yaxis"]["title"] = {"text": "Amplitude", "font": {"size": 13}}
        layout["yaxis"]["range"] = [-0.15, 1.35]
        layout["yaxis"]["autorange"] = False

        return {
            "id": "contrast_integral",
            "title": "Integral of w(t) \u2014 always zero (fails!)",
            "data": traces,
            "layout": layout,
        }

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    def get_state(self) -> Dict[str, Any]:
        state = super().get_state()
        eps = float(self.parameters["epsilon"])
        state["metadata"] = {
            "simulation_type": "impulse_construction",
            "hub_slots": self.HUB_SLOTS,
            "hub_domain": self.HUB_DOMAIN,
            "hub_dimensions": self.HUB_DIMENSIONS,
            "mode": self.parameters["mode"],
            "epsilon": eps,
            "pulse_height": self._height,
            "area": 1.0,
            "area_numerical": round(self._area_numerical, 6),
            "system_pole": float(self.parameters["system_pole"])
            if self.parameters["mode"] == "system_response"
            else None,
        }
        return state

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _base_layout(self, plot_id: str) -> Dict[str, Any]:
        mode = self.parameters["mode"]
        eps = self.parameters["epsilon"]
        pole = self.parameters["system_pole"]
        # datarevision: changes every call → forces Plotly to re-render data
        data_rev = f"{plot_id}-{mode}-{eps}-{pole}-{time.time()}"
        # uirevision: changes on mode switch → resets zoom/pan per mode
        # but stable within a mode so slider drags don't reset zoom
        ui_rev = f"{plot_id}-{mode}"

        return {
            "xaxis": {
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
                "color": "#94a3b8",
                "range": [T_MIN, T_MAX],
                "autorange": False,
            },
            "yaxis": {
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
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
            "datarevision": data_rev,
            "uirevision": ui_rev,
        }
