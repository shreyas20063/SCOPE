"""
Initial & Final Value Theorem Visualizer

Interactive exploration of the IVT and FVT for Laplace transforms.
Demonstrates how s*e^{-st} acts as a scanning kernel:
  - As s -> inf, se^{-st} -> delta(t), capturing x(0+) via IVT
  - As s -> 0,  se^{-st} flattens, capturing x(inf) via FVT

Includes failure modes where FVT breaks down (unstable / oscillatory signals).

Based on MIT 6.003 Lecture 06, slides 35-36: Initial and Final Value Theorems.
"""

import time
from typing import Any, Dict, List, Optional

import numpy as np

from .base_simulator import BaseSimulator

# NumPy 2.0 renamed trapz -> trapezoid
_trapz = np.trapezoid if hasattr(np, 'trapezoid') else np.trapz


class IVTFVTSimulator(BaseSimulator):
    """Simulator for Initial and Final Value Theorem visualization."""

    NUM_SAMPLES_PER_SEGMENT = 500
    MAX_DISPLAY_VALUE = 100.0

    PARAMETER_SCHEMA = {
        "signal_type": {
            "type": "select",
            "options": [
                {"value": "decaying_exp", "label": "Decaying Exp: e^{-t}u(t)"},
                {"value": "step_response", "label": "Step Response: (1-e^{-2t})u(t)"},
                {"value": "oscillatory_decay", "label": "Damped Oscillation: e^{-0.5t}cos(3t)u(t)"},
            ],
            "default": "decaying_exp",
        },
        "failure_mode": {
            "type": "checkbox",
            "default": False,
        },
        "log_s": {
            "type": "slider",
            "min": -2.0,
            "max": 2.0,
            "step": 0.01,
            "default": 0.0,
        },
    }

    DEFAULT_PARAMS = {
        "signal_type": "decaying_exp",
        "failure_mode": False,
        "log_s": 0.0,
    }

    # Maps each normal signal to its failure counterpart
    FAILURE_MAP = {
        "decaying_exp": "unstable_exp",
        "step_response": "pure_oscillation",
        "oscillatory_decay": "pure_oscillation",
    }

    def __init__(self, simulation_id: str):
        super().__init__(simulation_id)
        self._revision: int = 0

    def initialize(self, params: Optional[Dict[str, Any]] = None) -> None:
        self.parameters = {**self.DEFAULT_PARAMS, **(params or {})}
        for name, value in self.parameters.items():
            if name in self.PARAMETER_SCHEMA:
                self.parameters[name] = self._validate_param(name, value)
        self._revision += 1
        self._initialized = True

    def reset(self) -> Dict[str, Any]:
        self.parameters = self.DEFAULT_PARAMS.copy()
        self._revision += 1
        self._initialized = True
        return self.get_state()

    def update_parameter(self, name: str, value: Any) -> Dict[str, Any]:
        if name in self.parameters:
            self.parameters[name] = self._validate_param(name, value)
        if name in ("signal_type", "failure_mode"):
            self._revision += 1
        return self.get_state()

    def get_plots(self) -> List[Dict[str, Any]]:
        data = self._compute()
        return [
            self._create_signal_plot(data),
            self._create_kernel_plot(data),
            self._create_product_plot(data),
        ]

    def get_state(self) -> Dict[str, Any]:
        data = self._compute()
        config = data["config"]
        s = data["s"]

        plots = [
            self._create_signal_plot(data),
            self._create_kernel_plot(data),
            self._create_product_plot(data),
        ]

        # Compute IVT limit: sX(s) at large s
        ivt_limit = None
        if config["ivt_valid"]:
            try:
                ivt_limit = round(float(config["sXs_func"](100.0)), 4)
            except (ValueError, ZeroDivisionError):
                ivt_limit = None

        # Compute FVT limit: sX(s) at small s
        fvt_limit = None
        if config["fvt_valid"]:
            try:
                fvt_limit = round(float(config["sXs_func"](0.01)), 4)
            except (ValueError, ZeroDivisionError):
                fvt_limit = None

        sXs_analytical = data["sXs_analytical"]

        return {
            "parameters": self.parameters.copy(),
            "plots": plots,
            "metadata": {
                "simulation_type": "ivt_fvt_visualizer",
                "sticky_controls": True,

                # Current signal info
                "active_signal_id": data["active_id"],
                "active_signal_label": config["label"],
                "is_failure_mode": bool(self.parameters["failure_mode"]),

                # Current s value
                "s_value": round(s, 6),
                "log_s": float(self.parameters["log_s"]),

                # Computed values
                "sXs_numerical": round(data["sXs_numerical"], 6),
                "sXs_analytical": round(sXs_analytical, 6) if not np.isnan(sXs_analytical) else None,
                "sXs_formula": config["sXs_formula"],
                "Xs_formula": config["Xs_formula"],

                # Analytical reference values
                "x_0_plus": config["x_0_plus"],
                "x_inf": config["x_inf"],
                "x_inf_display": str(config["x_inf"]) if config["x_inf"] is not None else "DNE",

                # Theorem validity
                "ivt_valid": config["ivt_valid"],
                "fvt_valid": config["fvt_valid"],
                "fvt_reason": config["fvt_reason"],

                # Limiting values
                "ivt_limit": ivt_limit,
                "fvt_limit": fvt_limit,

                "revision": self._revision,
            },
        }

    # -- Signal configurations -------------------------------------------

    @staticmethod
    def _get_signal_config(signal_id: str) -> Dict[str, Any]:
        """Return signal configuration by ID."""
        configs = {
            "decaying_exp": {
                "label": "e\u207b\u00b9\u1d57 u(t)",
                "x_0_plus": 1.0,
                "x_inf": 0.0,
                "sXs_formula": "s / (s + 1)",
                "Xs_formula": "1 / (s + 1)",
                "ivt_valid": True,
                "fvt_valid": True,
                "fvt_reason": None,
            },
            "step_response": {
                "label": "(1 \u2212 e\u207b\u00b2\u1d57) u(t)",
                "x_0_plus": 0.0,
                "x_inf": 1.0,
                "sXs_formula": "2 / (s + 2)",
                "Xs_formula": "2 / [s(s + 2)]",
                "ivt_valid": True,
                "fvt_valid": True,
                "fvt_reason": None,
            },
            "oscillatory_decay": {
                "label": "e\u207b\u2070\u00b7\u2075\u1d57 cos(3t) u(t)",
                "x_0_plus": 1.0,
                "x_inf": 0.0,
                "sXs_formula": "s(s+0.5) / [(s+0.5)\u00b2+9]",
                "Xs_formula": "(s+0.5) / [(s+0.5)\u00b2+9]",
                "ivt_valid": True,
                "fvt_valid": True,
                "fvt_reason": None,
            },
            "unstable_exp": {
                "label": "e\u1d57 u(t)  [UNSTABLE]",
                "x_0_plus": 1.0,
                "x_inf": None,
                "sXs_formula": "s / (s \u2212 1)  [Re(s)>1]",
                "Xs_formula": "1 / (s \u2212 1)",
                "ivt_valid": True,
                "fvt_valid": False,
                "fvt_reason": "Pole at s=1 (RHP) \u2014 x(t) diverges to \u221e, no finite limit exists",
            },
            "pure_oscillation": {
                "label": "cos(3t) u(t)  [OSCILLATES]",
                "x_0_plus": 1.0,
                "x_inf": None,
                "sXs_formula": "s\u00b2 / (s\u00b2 + 9)",
                "Xs_formula": "s / (s\u00b2 + 9)",
                "ivt_valid": True,
                "fvt_valid": False,
                "fvt_reason": "Poles on j\u03c9 axis (s=\u00b13j) \u2014 x(t) oscillates forever, no limit",
            },
        }

        config = configs[signal_id]

        # Attach callables (can't store lambdas in a dict returned from staticmethod cleanly,
        # so we add them here)
        x_funcs = {
            "decaying_exp": lambda t: np.exp(-t),
            "step_response": lambda t: 1.0 - np.exp(-2.0 * t),
            "oscillatory_decay": lambda t: np.exp(-0.5 * t) * np.cos(3.0 * t),
            "unstable_exp": lambda t: np.exp(t),
            "pure_oscillation": lambda t: np.cos(3.0 * t),
        }
        sXs_funcs = {
            "decaying_exp": lambda s: s / (s + 1.0),
            "step_response": lambda s: 2.0 / (s + 2.0),
            "oscillatory_decay": lambda s: s * (s + 0.5) / ((s + 0.5) ** 2 + 9.0),
            "unstable_exp": lambda s: s / (s - 1.0) if s != 1.0 else float("nan"),
            "pure_oscillation": lambda s: s ** 2 / (s ** 2 + 9.0),
        }

        config["x_func"] = x_funcs[signal_id]
        config["sXs_func"] = sXs_funcs[signal_id]
        return config

    # -- Core computation ------------------------------------------------

    def _compute(self) -> Dict[str, Any]:
        """Core computation: generate x(t), kernel, product, and integral."""
        signal_type = str(self.parameters["signal_type"])
        failure = bool(self.parameters["failure_mode"])
        log_s = float(self.parameters["log_s"])
        s = 10.0 ** log_s

        # Determine active signal
        if failure:
            active_id = self.FAILURE_MAP.get(signal_type, signal_type)
        else:
            active_id = signal_type

        config = self._get_signal_config(active_id)

        # Adaptive time ranges:
        # - Display range: capped for readable plots
        # - Integration range: extends further to capture kernel tail for accuracy
        # For large s, kernel is narrow -> fine resolution near t=0
        # For small s, kernel is broad -> need long integration range
        t_fine_end = min(10.0 / max(s, 0.1), 5.0)
        t_display_max = max(10.0, min(20.0 / max(s, 0.01), 50.0))

        # Integration range covers ~7 kernel time constants (e^{-7} < 0.001)
        t_int_max = max(t_display_max, min(7.0 / max(s, 0.001), 2000.0))

        t_fine = np.linspace(0, t_fine_end, self.NUM_SAMPLES_PER_SEGMENT)
        if t_fine_end < t_int_max:
            t_coarse = np.linspace(t_fine_end, t_int_max, self.NUM_SAMPLES_PER_SEGMENT)
            t = np.concatenate([t_fine, t_coarse[1:]])  # avoid duplicate
        else:
            t = t_fine

        # Signal x(t)
        x = config["x_func"](t)
        x_clipped = np.clip(x, -self.MAX_DISPLAY_VALUE, self.MAX_DISPLAY_VALUE)

        # Kernel: s * e^{-st}
        kernel = s * np.exp(-s * t)

        # Product: x(t) * s * e^{-st}
        product = x * kernel
        product_clipped = np.clip(product, -self.MAX_DISPLAY_VALUE, self.MAX_DISPLAY_VALUE)

        # Numerical integral: sX(s) = integral_0^inf x(t) * s * e^{-st} dt
        # Use the unclipped product for accuracy
        sXs_numerical = float(_trapz(product, t))

        # Tail correction: if x(inf) is finite and known, add residual
        # integral_T^inf x(inf)*s*e^{-st}dt = x(inf)*e^{-sT}
        x_inf = config["x_inf"]
        if x_inf is not None and x_inf != 0.0:
            tail_correction = x_inf * np.exp(-s * t[-1])
            sXs_numerical += float(tail_correction)

        # Analytical sX(s)
        try:
            sXs_analytical = float(config["sXs_func"](s))
        except (ValueError, ZeroDivisionError):
            sXs_analytical = float("nan")

        return {
            "t": t,
            "x": x_clipped,
            "kernel": kernel,
            "product": product_clipped,
            "s": s,
            "log_s": log_s,
            "sXs_numerical": sXs_numerical,
            "sXs_analytical": sXs_analytical,
            "active_id": active_id,
            "config": config,
            "t_display_max": t_display_max,
        }

    # -- Plot construction -----------------------------------------------

    def _get_base_layout(
        self, xtitle: str, ytitle: str, plot_id: str
    ) -> Dict[str, Any]:
        """Standard Plotly layout."""
        signal_type = str(self.parameters["signal_type"])
        failure = bool(self.parameters["failure_mode"])
        log_s = float(self.parameters["log_s"])
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
                "autorange": True,
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
            "datarevision": f"{plot_id}-{log_s}-{signal_type}-{failure}-{time.time()}",
            "uirevision": f"{plot_id}-{signal_type}-{failure}-{self._revision}",
        }

    def _create_signal_plot(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Plot 1: x(t) with reference lines for x(0+) and x(inf)."""
        t = data["t"]
        x = data["x"]
        config = data["config"]
        active_id = data["active_id"]
        t_list = t.tolist()

        is_failure = active_id in ("unstable_exp", "pure_oscillation")
        traces = []

        # Main signal trace
        traces.append({
            "x": t_list,
            "y": x.tolist(),
            "type": "scatter",
            "mode": "lines",
            "name": config["label"],
            "line": {
                "color": "#3b82f6",
                "width": 2.5,
                "dash": "dash" if is_failure else "solid",
            },
            "hovertemplate": "t=%{x:.3f}<br>x(t)=%{y:.4f}<extra></extra>",
        })

        # x(0+) reference line
        x0 = config["x_0_plus"]
        if x0 is not None:
            traces.append({
                "x": [t_list[0], t_list[-1]],
                "y": [x0, x0],
                "type": "scatter",
                "mode": "lines",
                "name": f"x(0\u207a) = {x0}",
                "line": {"color": "#10b981", "width": 1.5, "dash": "dot"},
                "showlegend": True,
                "hoverinfo": "name",
            })

        # x(inf) reference line (only if finite)
        xinf = config["x_inf"]
        if xinf is not None:
            traces.append({
                "x": [t_list[0], t_list[-1]],
                "y": [xinf, xinf],
                "type": "scatter",
                "mode": "lines",
                "name": f"x(\u221e) = {xinf}",
                "line": {"color": "#14b8a6", "width": 1.5, "dash": "dashdot"},
                "showlegend": True,
                "hoverinfo": "name",
            })

        layout = self._get_base_layout("t (seconds)", "x(t)", "signal_xt")
        # Limit x-axis for readability on the signal plot
        layout["xaxis"]["range"] = [0, min(data["t_display_max"], 15.0)]

        return {
            "id": "signal_xt",
            "title": f"Signal: {config['label']}",
            "data": traces,
            "layout": layout,
        }

    def _create_kernel_plot(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Plot 2: se^{-st} with filled area."""
        t = data["t"]
        kernel = data["kernel"]
        s = data["s"]
        t_list = t.tolist()

        traces = [{
            "x": t_list,
            "y": kernel.tolist(),
            "type": "scatter",
            "mode": "lines",
            "fill": "tozeroy",
            "fillcolor": "rgba(239, 68, 68, 0.12)",
            "name": f"s\u00b7e\u207b\u02e2\u1d57, s={s:.3g}",
            "line": {"color": "#ef4444", "width": 2.5},
            "hovertemplate": "t=%{x:.3f}<br>kernel=%{y:.4f}<extra></extra>",
        }]

        layout = self._get_base_layout("t (seconds)", "s e\u207b\u02e2\u1d57", "kernel_set")
        layout["xaxis"]["range"] = [0, min(data["t_display_max"], 15.0)]

        # Annotation: area is always 1 for t >= 0
        layout["annotations"] = [{
            "text": "Area = 1 (always)",
            "xref": "paper",
            "yref": "paper",
            "x": 0.98,
            "y": 0.95,
            "xanchor": "right",
            "yanchor": "top",
            "showarrow": False,
            "font": {"size": 12, "color": "#ef4444", "family": "Fira Code, monospace"},
            "bgcolor": "rgba(0,0,0,0.5)",
            "bordercolor": "rgba(239,68,68,0.3)",
            "borderwidth": 1,
            "borderpad": 5,
        }]

        return {
            "id": "kernel_set",
            "title": f"Laplace Kernel: s\u00b7exp(\u2212st),  s = {s:.3g}",
            "data": traces,
            "layout": layout,
        }

    def _create_product_plot(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Plot 3: x(t)*se^{-st} with filled area = sX(s)."""
        t = data["t"]
        product = data["product"]
        sXs_num = data["sXs_numerical"]
        s = data["s"]
        t_list = t.tolist()

        traces = [{
            "x": t_list,
            "y": product.tolist(),
            "type": "scatter",
            "mode": "lines",
            "fill": "tozeroy",
            "fillcolor": "rgba(16, 185, 129, 0.15)",
            "name": "x(t) \u00b7 s\u00b7e\u207b\u02e2\u1d57",
            "line": {"color": "#10b981", "width": 2},
            "hovertemplate": "t=%{x:.3f}<br>product=%{y:.4f}<extra></extra>",
        }]

        layout = self._get_base_layout(
            "t (seconds)", "x(t) \u00b7 s e\u207b\u02e2\u1d57", "product_integral"
        )
        layout["xaxis"]["range"] = [0, min(data["t_display_max"], 15.0)]

        # Annotation showing integral value
        layout["annotations"] = [{
            "text": f"Area = sX(s) = {sXs_num:.4f}",
            "xref": "paper",
            "yref": "paper",
            "x": 0.98,
            "y": 0.95,
            "xanchor": "right",
            "yanchor": "top",
            "showarrow": False,
            "font": {"size": 13, "color": "#10b981", "family": "Fira Code, monospace"},
            "bgcolor": "rgba(0,0,0,0.5)",
            "bordercolor": "rgba(16,185,129,0.3)",
            "borderwidth": 1,
            "borderpad": 6,
        }]

        return {
            "id": "product_integral",
            "title": f"Product & Integral:  sX(s) = {sXs_num:.4f}",
            "data": traces,
            "layout": layout,
        }
