"""
Z-Transform Properties Lab

Interactive demonstration of the four key Z-transform properties:
  1. Linearity:     α·x₁[n] + β·x₂[n]  ↔  α·X₁(z) + β·X₂(z)
  2. Time Delay:    x[n−k]              ↔  z⁻ᵏ·X(z)
  3. Multiply by n: n·x[n]              ↔  −z·dX(z)/dz
  4. Convolution:   x₁[n] ∗ x₂[n]      ↔  X₁(z)·X₂(z)

Users pick one or two signals from a library, apply a property, and see the
operation in both time domain (stem plots) and z-domain (pole-zero + ROC)
simultaneously.  Convolution includes step-by-step animation data.

Based on Lecture 5: slides 22–23 (linearity, delay), 45–50 (property table,
multiply-by-n examples).
"""

from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .base_simulator import BaseSimulator

# ── Signal library ────────────────────────────────────────────────────

SIGNAL_LIBRARY = {
    "impulse": {
        "label": "\u03b4[n]",
        "z_expr": "1",
        "roc_type": "all",
        "roc_radius": 0.0,
        "has_param": False,
    },
    "unit_step": {
        "label": "u[n]",
        "z_expr": "z / (z \u2212 1)",
        "roc_type": "outside",
        "roc_radius": 1.0,
        "has_param": False,
    },
    "geometric": {
        "label": "a\u207f u[n]",
        "z_expr": "z / (z \u2212 a)",
        "roc_type": "outside",
        "roc_radius": None,
        "has_param": True,
        "param_name": "a",
    },
    "ramp_geometric": {
        "label": "n\u00b7a\u207f u[n]",
        "z_expr": "az / (z \u2212 a)\u00b2",
        "roc_type": "outside",
        "roc_radius": None,
        "has_param": True,
        "param_name": "a",
    },
    "cosine": {
        "label": "cos(\u03c9\u2080n) u[n]",
        "z_expr": "z(z \u2212 cos\u03c9\u2080) / (z\u00b2 \u2212 2z cos\u03c9\u2080 + 1)",
        "roc_type": "outside",
        "roc_radius": 1.0,
        "has_param": True,
        "param_name": "omega0",
    },
    "finite_121": {
        "label": "[1, 2, 1]",
        "z_expr": "1 + 2z\u207b\u00b9 + z\u207b\u00b2",
        "roc_type": "nonzero",
        "roc_radius": 0.0,
        "has_param": False,
    },
}

PROPERTY_FORMULAS = {
    "linearity": "\u03b1\u00b7x\u2081[n] + \u03b2\u00b7x\u2082[n]  \u2194  \u03b1\u00b7X\u2081(z) + \u03b2\u00b7X\u2082(z),  ROC \u2287 ROC\u2081 \u2229 ROC\u2082",
    "delay": "x[n\u2212k]  \u2194  z\u207b\u1d4f\u00b7X(z),  ROC same (except z=0 or \u221e)",
    "multiply_n": "n\u00b7x[n]  \u2194  \u2212z\u00b7dX(z)/dz,  ROC same",
    "convolution": "x\u2081[n] \u2217 x\u2082[n]  \u2194  X\u2081(z)\u00b7X\u2082(z),  ROC \u2287 ROC\u2081 \u2229 ROC\u2082",
}


class ZTransformPropertiesSimulator(BaseSimulator):
    """Simulator for the Z-Transform Properties Lab."""

    PARAMETER_SCHEMA = {
        "signal_1": {
            "type": "select",
            "options": list(SIGNAL_LIBRARY.keys()),
            "default": "unit_step",
        },
        "signal_2": {
            "type": "select",
            "options": list(SIGNAL_LIBRARY.keys()),
            "default": "geometric",
        },
        "property": {
            "type": "select",
            "options": ["linearity", "delay", "multiply_n", "convolution"],
            "default": "linearity",
        },
        "alpha": {"type": "slider", "min": -3.0, "max": 3.0, "step": 0.1, "default": 1.0},
        "beta": {"type": "slider", "min": -3.0, "max": 3.0, "step": 0.1, "default": 1.0},
        "delay_k": {"type": "slider", "min": 0, "max": 10, "step": 1, "default": 2},
        "signal_1_a": {"type": "slider", "min": -0.95, "max": 0.95, "step": 0.05, "default": 0.5},
        "signal_1_omega0": {"type": "slider", "min": 0.1, "max": 3.0, "step": 0.1, "default": 1.0},
        "signal_2_a": {"type": "slider", "min": -0.95, "max": 0.95, "step": 0.05, "default": 0.3},
        "signal_2_omega0": {"type": "slider", "min": 0.1, "max": 3.0, "step": 0.1, "default": 1.0},
        "num_samples": {"type": "slider", "min": 10, "max": 40, "step": 1, "default": 20},
    }

    DEFAULT_PARAMS = {
        "signal_1": "unit_step",
        "signal_2": "geometric",
        "property": "linearity",
        "alpha": 1.0,
        "beta": 1.0,
        "delay_k": 2,
        "signal_1_a": 0.5,
        "signal_1_omega0": 1.0,
        "signal_2_a": 0.3,
        "signal_2_omega0": 1.0,
        "num_samples": 20,
    }

    def __init__(self, simulation_id: str) -> None:
        super().__init__(simulation_id)
        self._cached: Optional[Dict[str, Any]] = None
        self._revision: int = 0

    # ── BaseSimulator interface ───────────────────────────────────────

    def initialize(self, params: Optional[Dict[str, Any]] = None) -> None:
        self.parameters = {**self.DEFAULT_PARAMS, **(params or {})}
        for name in list(self.parameters):
            if name in self.PARAMETER_SCHEMA:
                self.parameters[name] = self._validate_param(name, self.parameters[name])
        self._cached = None
        self._revision += 1
        self._initialized = True

    def reset(self) -> Dict[str, Any]:
        self.parameters = self.DEFAULT_PARAMS.copy()
        self._cached = None
        self._revision += 1
        self._initialized = True
        return self.get_state()

    def update_parameter(self, name: str, value: Any) -> Dict[str, Any]:
        if name in self.parameters:
            self.parameters[name] = self._validate_param(name, value)
        self._cached = None
        self._revision += 1
        return self.get_state()

    def get_plots(self) -> List[Dict[str, Any]]:
        return self._compute()["plots"]

    def get_state(self) -> Dict[str, Any]:
        data = self._compute()
        prop = self.parameters["property"]
        needs_second = prop in ("linearity", "convolution")

        return {
            "parameters": self.parameters.copy(),
            "plots": data["plots"],
            "metadata": {
                "simulation_type": "z_transform_properties",
                "property": prop,
                "property_formula": PROPERTY_FORMULAS.get(prop, ""),
                "signal_1_info": data["signal_1_info"],
                "signal_2_info": data.get("signal_2_info"),
                "result_info": data["result_info"],
                "roc_1": data["roc_1"],
                "roc_2": data.get("roc_2"),
                "roc_result": data["roc_result"],
                "conv_steps": data.get("conv_steps"),
                "conv_num_steps": data.get("conv_num_steps", 0),
                "needs_second_signal": needs_second,
                "revision": self._revision,
            },
        }

    # ── Master computation ────────────────────────────────────────────

    def _compute(self) -> Dict[str, Any]:
        if self._cached is not None:
            return self._cached

        prop = self.parameters["property"]
        N = int(self.parameters["num_samples"])
        n = np.arange(N, dtype=float)
        needs_second = prop in ("linearity", "convolution")

        x1, sig1_info = self._generate_signal(self.parameters["signal_1"], 1, n)
        roc_1 = self._get_roc(self.parameters["signal_1"], 1)
        pz_1 = self._get_poles_zeros(self.parameters["signal_1"], 1)

        x2, sig2_info, roc_2, pz_2 = None, None, None, None
        if needs_second:
            x2, sig2_info = self._generate_signal(self.parameters["signal_2"], 2, n)
            roc_2 = self._get_roc(self.parameters["signal_2"], 2)
            pz_2 = self._get_poles_zeros(self.parameters["signal_2"], 2)

        conv_steps = None
        conv_num_steps = 0

        if prop == "linearity":
            result, result_info, result_pz = self._apply_linearity(x1, x2, sig1_info, sig2_info, pz_1, pz_2)
        elif prop == "delay":
            result, result_info, result_pz = self._apply_delay(x1, sig1_info, n, pz_1)
        elif prop == "multiply_n":
            result, result_info, result_pz = self._apply_multiply_n(x1, sig1_info, n, pz_1)
        else:
            result, result_info, result_pz, conv_steps = self._apply_convolution(
                x1, x2, sig1_info, sig2_info, n, pz_1, pz_2
            )
            conv_num_steps = len(conv_steps)

        roc_result = self._compute_result_roc(prop, roc_1, roc_2)

        plots = self._build_plots(
            n, x1, sig1_info, x2, sig2_info, result, result_info,
            needs_second, pz_1, pz_2, result_pz, roc_1, roc_2, roc_result,
        )

        self._cached = {
            "plots": plots,
            "signal_1_info": sig1_info,
            "signal_2_info": sig2_info,
            "result_info": result_info,
            "roc_1": roc_1,
            "roc_2": roc_2,
            "roc_result": roc_result,
            "conv_steps": conv_steps,
            "conv_num_steps": conv_num_steps,
        }
        return self._cached

    # ── Signal generation ─────────────────────────────────────────────

    def _generate_signal(
        self, sig_key: str, sig_num: int, n: np.ndarray
    ) -> Tuple[np.ndarray, Dict[str, str]]:
        N = len(n)
        if sig_key == "impulse":
            x = np.zeros(N)
            x[0] = 1.0
            info = {"label": "\u03b4[n]", "z_expr": "1", "signal_key": sig_key}
        elif sig_key == "unit_step":
            x = np.ones(N)
            info = {"label": "u[n]", "z_expr": "z/(z\u22121)", "signal_key": sig_key}
        elif sig_key == "geometric":
            a = float(self.parameters[f"signal_{sig_num}_a"])
            x = a ** n
            info = {
                "label": f"({a:g})\u207f u[n]",
                "z_expr": f"z/(z\u2212{a:g})",
                "signal_key": sig_key,
            }
        elif sig_key == "ramp_geometric":
            a = float(self.parameters[f"signal_{sig_num}_a"])
            x = n * (a ** n)
            info = {
                "label": f"n\u00b7({a:g})\u207f u[n]",
                "z_expr": f"{a:g}z/(z\u2212{a:g})\u00b2",
                "signal_key": sig_key,
            }
        elif sig_key == "cosine":
            w0 = float(self.parameters[f"signal_{sig_num}_omega0"])
            x = np.cos(w0 * n)
            info = {
                "label": f"cos({w0:.1f}n) u[n]",
                "z_expr": f"z(z\u2212cos{w0:.1f})/(z\u00b2\u22122z\u00b7cos{w0:.1f}+1)",
                "signal_key": sig_key,
            }
        elif sig_key == "finite_121":
            x = np.zeros(N)
            x[0], x[1], x[2] = 1.0, 2.0, 1.0
            info = {"label": "[1, 2, 1]", "z_expr": "1+2z\u207b\u00b9+z\u207b\u00b2", "signal_key": sig_key}
        else:
            x = np.zeros(N)
            info = {"label": "?", "z_expr": "?", "signal_key": sig_key}
        return x, info

    # ── Property operations ───────────────────────────────────────────

    def _apply_linearity(
        self,
        x1: np.ndarray, x2: np.ndarray,
        info1: Dict, info2: Dict,
        pz_1: Dict, pz_2: Dict,
    ) -> Tuple[np.ndarray, Dict, Dict]:
        alpha = float(self.parameters["alpha"])
        beta = float(self.parameters["beta"])
        result = alpha * x1 + beta * x2

        result_info = {
            "label": f"{alpha:g}\u00b7{info1['label']} + {beta:g}\u00b7{info2['label']}",
            "z_expr": f"{alpha:g}\u00b7({info1['z_expr']}) + {beta:g}\u00b7({info2['z_expr']})",
        }
        result_pz = {
            "poles": pz_1["poles"] + pz_2["poles"],
            "zeros": [],
        }
        return result, result_info, result_pz

    def _apply_delay(
        self,
        x1: np.ndarray, info1: Dict, n: np.ndarray,
        pz_1: Dict,
    ) -> Tuple[np.ndarray, Dict, Dict]:
        k = int(self.parameters["delay_k"])
        N = len(n)
        result = np.zeros(N)
        if k < N:
            result[k:] = x1[: N - k]

        result_info = {
            "label": f"{info1['label']} delayed by {k}",
            "z_expr": f"z\u207b{k}\u00b7({info1['z_expr']})",
        }
        result_pz = {
            "poles": pz_1["poles"] + [(0.0, 0.0)] * k,
            "zeros": pz_1["zeros"] + [(0.0, 0.0)] * k,
        }
        return result, result_info, result_pz

    def _apply_multiply_n(
        self,
        x1: np.ndarray, info1: Dict, n: np.ndarray,
        pz_1: Dict,
    ) -> Tuple[np.ndarray, Dict, Dict]:
        result = n * x1
        result_info = {
            "label": f"n\u00b7{info1['label']}",
            "z_expr": f"\u2212z\u00b7d/dz[{info1['z_expr']}]",
        }
        result_pz = {
            "poles": pz_1["poles"],
            "zeros": pz_1["zeros"],
        }
        return result, result_info, result_pz

    def _apply_convolution(
        self,
        x1: np.ndarray, x2: np.ndarray,
        info1: Dict, info2: Dict, n: np.ndarray,
        pz_1: Dict, pz_2: Dict,
    ) -> Tuple[np.ndarray, Dict, Dict, List[Dict]]:
        full_conv = np.convolve(x1, x2)
        N = len(n)
        L = len(full_conv)

        conv_steps: List[Dict[str, Any]] = []
        for shift in range(L):
            products = []
            for k in range(N):
                idx = shift - k
                if 0 <= idx < N:
                    products.append({
                        "k": int(k),
                        "val": float(x1[k] * x2[idx]),
                    })
            conv_steps.append({
                "shift": int(shift),
                "result_value": float(full_conv[shift]),
                "products": products,
            })

        result_info = {
            "label": f"{info1['label']} \u2217 {info2['label']}",
            "z_expr": f"({info1['z_expr']})\u00b7({info2['z_expr']})",
        }
        result_pz = {
            "poles": pz_1["poles"] + pz_2["poles"],
            "zeros": pz_1["zeros"] + pz_2["zeros"],
        }
        return full_conv, result_info, result_pz, conv_steps

    # ── ROC helpers ───────────────────────────────────────────────────

    def _get_roc(self, sig_key: str, sig_num: int) -> Dict[str, Any]:
        sig = SIGNAL_LIBRARY[sig_key]
        roc_type = sig["roc_type"]
        if sig["has_param"]:
            pname = sig["param_name"]
            pkey = f"signal_{sig_num}_{pname}"
            pval = float(self.parameters.get(pkey, 0.5))
            radius = abs(pval) if pname == "a" else sig.get("roc_radius", 1.0)
        else:
            radius = sig.get("roc_radius", 0.0) or 0.0
        return {"type": roc_type, "radius": float(radius)}

    def _compute_result_roc(
        self, prop: str, roc_1: Dict, roc_2: Optional[Dict]
    ) -> Dict[str, Any]:
        if prop == "linearity":
            r = max(roc_1["radius"], roc_2["radius"]) if roc_2 else roc_1["radius"]
            return {"type": "outside", "radius": r, "note": "ROC \u2287 ROC\u2081 \u2229 ROC\u2082"}
        if prop == "delay":
            return {"type": roc_1["type"], "radius": roc_1["radius"], "note": "Same ROC (except z=0 or \u221e)"}
        if prop == "multiply_n":
            return {"type": roc_1["type"], "radius": roc_1["radius"], "note": "Same ROC"}
        # convolution
        r = max(roc_1["radius"], roc_2["radius"]) if roc_2 else roc_1["radius"]
        return {"type": "outside", "radius": r, "note": "ROC \u2287 ROC\u2081 \u2229 ROC\u2082"}

    # ── Pole / zero helpers ───────────────────────────────────────────

    def _get_poles_zeros(self, sig_key: str, sig_num: int) -> Dict[str, List[Tuple[float, float]]]:
        poles: List[Tuple[float, float]] = []
        zeros: List[Tuple[float, float]] = []

        if sig_key == "impulse":
            pass  # X(z) = 1
        elif sig_key == "unit_step":
            poles.append((1.0, 0.0))
            zeros.append((0.0, 0.0))
        elif sig_key == "geometric":
            a = float(self.parameters[f"signal_{sig_num}_a"])
            poles.append((a, 0.0))
            zeros.append((0.0, 0.0))
        elif sig_key == "ramp_geometric":
            a = float(self.parameters[f"signal_{sig_num}_a"])
            poles.append((a, 0.0))
            poles.append((a, 0.0))  # double pole
            zeros.append((0.0, 0.0))
        elif sig_key == "cosine":
            w0 = float(self.parameters[f"signal_{sig_num}_omega0"])
            poles.append((np.cos(w0), np.sin(w0)))
            poles.append((np.cos(w0), -np.sin(w0)))
            zeros.append((np.cos(w0), 0.0))
            zeros.append((0.0, 0.0))
        elif sig_key == "finite_121":
            zeros.append((-1.0, 0.0))
            zeros.append((-1.0, 0.0))  # double zero at -1

        return {"poles": poles, "zeros": zeros}

    # ── Plot construction ─────────────────────────────────────────────

    def _build_plots(
        self,
        n: np.ndarray,
        x1: np.ndarray, sig1_info: Dict,
        x2: Optional[np.ndarray], sig2_info: Optional[Dict],
        result: np.ndarray, result_info: Dict,
        needs_second: bool,
        pz_1: Dict, pz_2: Optional[Dict], result_pz: Dict,
        roc_1: Dict, roc_2: Optional[Dict], roc_result: Dict,
    ) -> List[Dict[str, Any]]:
        plots = [
            self._stem_plot(n, x1, sig1_info["label"], "signal_1", f"x\u2081[n] = {sig1_info['label']}", "#3b82f6"),
        ]
        if needs_second and x2 is not None:
            plots.append(
                self._stem_plot(n, x2, sig2_info["label"], "signal_2", f"x\u2082[n] = {sig2_info['label']}", "#ef4444")
            )
        result_n = np.arange(len(result), dtype=float)
        plots.append(
            self._stem_plot(result_n, result, result_info["label"], "result", f"Result: {result_info['label']}", "#14b8a6")
        )
        plots.append(self._z_plane_plot(pz_1, pz_2, result_pz, roc_1, roc_2, roc_result, needs_second))
        return plots

    @staticmethod
    def _make_stem_traces(
        n_vals: np.ndarray, y_vals: np.ndarray, name: str, color: str, marker_size: int = 10
    ) -> List[Dict[str, Any]]:
        n_list = n_vals.tolist()
        y_list = y_vals.tolist()
        stem_x: List = []
        stem_y: List = []
        for i in range(len(n_list)):
            stem_x.extend([n_list[i], n_list[i], None])
            stem_y.extend([0, y_list[i], None])
        return [
            {
                "x": stem_x, "y": stem_y,
                "type": "scatter", "mode": "lines",
                "name": "Stems", "line": {"color": color, "width": 2},
                "showlegend": False, "hoverinfo": "skip",
            },
            {
                "x": n_list, "y": y_list,
                "type": "scatter", "mode": "markers",
                "name": name,
                "marker": {"color": color, "size": marker_size, "line": {"color": "#0a0e27", "width": 1.5}},
                "hovertemplate": "n=%{x}<br>value=%{y:.4f}<extra></extra>",
            },
        ]

    def _stem_plot(
        self, n: np.ndarray, x: np.ndarray, trace_name: str,
        plot_id: str, title: str, color: str,
    ) -> Dict[str, Any]:
        traces = self._make_stem_traces(n, x, trace_name, color)
        rev = self._revision
        return {
            "id": plot_id,
            "title": title,
            "data": traces,
            "layout": {
                "xaxis": {
                    "title": {"text": "n", "font": {"color": "#f1f5f9", "size": 13}},
                    "gridcolor": "rgba(148,163,184,0.1)",
                    "zerolinecolor": "rgba(148,163,184,0.3)",
                    "color": "#94a3b8",
                    "dtick": 1 if len(n) <= 25 else 5,
                    "range": [-0.5, float(n[-1]) + 0.5],
                },
                "yaxis": {
                    "title": {"text": "Amplitude", "font": {"color": "#f1f5f9", "size": 13}},
                    "gridcolor": "rgba(148,163,184,0.1)",
                    "zerolinecolor": "rgba(148,163,184,0.3)",
                    "color": "#94a3b8",
                    "autorange": True,
                },
                "paper_bgcolor": "rgba(0,0,0,0)",
                "plot_bgcolor": "rgba(0,0,0,0)",
                "font": {"family": "Inter, sans-serif", "size": 12, "color": "#f1f5f9"},
                "margin": {"t": 45, "r": 25, "b": 55, "l": 60},
                "showlegend": False,
                "datarevision": f"{plot_id}-{rev}",
            },
        }

    def _z_plane_plot(
        self,
        pz_1: Dict, pz_2: Optional[Dict], result_pz: Dict,
        roc_1: Dict, roc_2: Optional[Dict], roc_result: Dict,
        needs_second: bool,
    ) -> Dict[str, Any]:
        traces: List[Dict[str, Any]] = []
        theta = np.linspace(0, 2 * np.pi, 200)

        # Collect all points to compute dynamic axis range
        all_radii = [1.0]  # unit circle always visible

        # ROC shading for signal 1
        if roc_1["type"] == "outside" and roc_1["radius"] > 0:
            r = roc_1["radius"]
            all_radii.append(r)
            traces.append({
                "x": (r * np.cos(theta)).tolist(),
                "y": (r * np.sin(theta)).tolist(),
                "type": "scatter", "mode": "lines",
                "fill": "toself",
                "fillcolor": "rgba(59,130,246,0.08)",
                "line": {"color": "rgba(59,130,246,0.4)", "width": 1.5, "dash": "dash"},
                "name": f"ROC\u2081: |z|>{r:.2g}",
                "hoverinfo": "name",
            })

        # ROC shading for signal 2
        if needs_second and roc_2 and roc_2["type"] == "outside" and roc_2["radius"] > 0:
            r = roc_2["radius"]
            all_radii.append(r)
            traces.append({
                "x": (r * np.cos(theta)).tolist(),
                "y": (r * np.sin(theta)).tolist(),
                "type": "scatter", "mode": "lines",
                "fill": "toself",
                "fillcolor": "rgba(239,68,68,0.08)",
                "line": {"color": "rgba(239,68,68,0.4)", "width": 1.5, "dash": "dash"},
                "name": f"ROC\u2082: |z|>{r:.2g}",
                "hoverinfo": "name",
            })

        # Result ROC
        if roc_result["type"] == "outside" and roc_result["radius"] > 0:
            r = roc_result["radius"]
            all_radii.append(r)
            traces.append({
                "x": (r * np.cos(theta)).tolist(),
                "y": (r * np.sin(theta)).tolist(),
                "type": "scatter", "mode": "lines",
                "fill": "toself",
                "fillcolor": "rgba(20,184,166,0.1)",
                "line": {"color": "rgba(20,184,166,0.6)", "width": 2},
                "name": f"ROC result: |z|>{r:.2g}",
                "hoverinfo": "name",
            })

        # Unit circle
        traces.append({
            "x": np.cos(theta).tolist(),
            "y": np.sin(theta).tolist(),
            "type": "scatter", "mode": "lines",
            "line": {"color": "#94a3b8", "width": 2},
            "name": "|z| = 1",
            "hoverinfo": "name",
        })

        # Poles and zeros for signal 1
        self._add_pz_traces(traces, pz_1, "#3b82f6", "x\u2081")
        for p in pz_1.get("poles", []) + pz_1.get("zeros", []):
            all_radii.append(abs(complex(p[0], p[1])))
        if needs_second and pz_2:
            self._add_pz_traces(traces, pz_2, "#ef4444", "x\u2082")
            for p in pz_2.get("poles", []) + pz_2.get("zeros", []):
                all_radii.append(abs(complex(p[0], p[1])))

        # Dynamic range: fit all poles/zeros/ROC with padding
        max_r = max(all_radii) if all_radii else 1.0
        axis_lim = max(max_r * 1.4, 1.5)

        # Axes
        traces.append({
            "x": [-axis_lim, axis_lim], "y": [0, 0],
            "type": "scatter", "mode": "lines",
            "line": {"color": "rgba(148,163,184,0.3)", "width": 1},
            "showlegend": False, "hoverinfo": "skip",
        })
        traces.append({
            "x": [0, 0], "y": [-axis_lim, axis_lim],
            "type": "scatter", "mode": "lines",
            "line": {"color": "rgba(148,163,184,0.3)", "width": 1},
            "showlegend": False, "hoverinfo": "skip",
        })

        rev = self._revision
        return {
            "id": "z_plane",
            "title": "Z-Plane: Poles, Zeros & ROC",
            "data": traces,
            "layout": {
                "xaxis": {
                    "title": "Real",
                    "showgrid": True,
                    "gridcolor": "rgba(148,163,184,0.1)",
                    "zeroline": False,
                    "range": [-axis_lim, axis_lim],
                    "fixedrange": False,
                    "color": "#94a3b8",
                },
                "yaxis": {
                    "title": "Imaginary",
                    "showgrid": True,
                    "gridcolor": "rgba(148,163,184,0.1)",
                    "zeroline": False,
                    "range": [-axis_lim, axis_lim],
                    "scaleanchor": "x",
                    "scaleratio": 1,
                    "fixedrange": False,
                    "color": "#94a3b8",
                },
                "legend": {
                    "x": 0.02, "y": 0.98,
                    "xanchor": "left", "yanchor": "top",
                    "bgcolor": "rgba(10,14,39,0.7)",
                    "bordercolor": "rgba(148,163,184,0.2)",
                    "borderwidth": 1,
                    "font": {"size": 11, "color": "#f1f5f9"},
                },
                "margin": {"l": 60, "r": 30, "t": 50, "b": 50},
                "paper_bgcolor": "rgba(0,0,0,0)",
                "plot_bgcolor": "rgba(0,0,0,0)",
                "font": {"family": "Inter, sans-serif", "size": 12, "color": "#f1f5f9"},
                "datarevision": f"z_plane-{rev}",
                "uirevision": f"z_plane-{rev}",
            },
        }

    @staticmethod
    def _add_pz_traces(
        traces: List[Dict], pz: Dict, color: str, label: str
    ) -> None:
        poles = pz.get("poles", [])
        zeros = pz.get("zeros", [])

        if poles:
            px = [p[0] for p in poles]
            py = [p[1] for p in poles]
            traces.append({
                "x": px, "y": py,
                "type": "scatter", "mode": "markers",
                "name": f"{label} poles",
                "marker": {
                    "symbol": "x",
                    "size": 14,
                    "color": color,
                    "line": {"width": 2.5, "color": color},
                },
                "hovertemplate": f"{label} pole<br>%{{x:.3f}} + %{{y:.3f}}j<extra></extra>",
            })

        if zeros:
            zx = [z[0] for z in zeros]
            zy = [z[1] for z in zeros]
            traces.append({
                "x": zx, "y": zy,
                "type": "scatter", "mode": "markers",
                "name": f"{label} zeros",
                "marker": {
                    "symbol": "circle-open",
                    "size": 14,
                    "color": color,
                    "line": {"width": 2.5, "color": color},
                },
                "hovertemplate": f"{label} zero<br>%{{x:.3f}} + %{{y:.3f}}j<extra></extra>",
            })
