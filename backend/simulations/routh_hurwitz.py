"""
Routh-Hurwitz Stability Criterion Tool

Standalone educational tool for learning the Routh-Hurwitz stability criterion.
Users enter a characteristic polynomial, optionally with parametric gain K,
and the tool builds the Routh array step-by-step with visual sign-change
highlighting and stability range analysis.

Features:
- Step-by-step Routh array construction
- Sign change highlighting for RHP pole identification
- Special case handling (zero pivot → epsilon, all-zero row → auxiliary polynomial)
- Parametric K analysis with stability ranges
- Pole-zero map showing root locations
- Educational presets covering common cases

References: Nise Ch.6, Ogata Ch.5, Dorf & Bishop Ch.6
"""

import numpy as np
from typing import Any, Dict, List, Optional
from .base_simulator import BaseSimulator
from core.routh_hurwitz import compute_routh_array, compute_stability_k_ranges


# Preset polynomial definitions
PRESETS = {
    "custom": {
        "label": "Custom",
        "coeffs": "1, 6, 11, 6",
        "description": "Enter your own polynomial coefficients",
    },
    "stable_3rd": {
        "label": "Stable 3rd Order",
        "coeffs": "1, 6, 11, 6",
        "description": "s³ + 6s² + 11s + 6 — all poles in LHP",
    },
    "unstable_3rd": {
        "label": "Unstable 3rd Order",
        "coeffs": "1, 2, 3, 10",
        "description": "s³ + 2s² + 3s + 10 — sign changes in Routh array",
    },
    "marginal_3rd": {
        "label": "Marginal Stability",
        "coeffs": "1, 1, 2, 2",
        "description": "s³ + s² + 2s + 2 — poles on jω axis",
    },
    "stable_4th": {
        "label": "Stable 4th Order",
        "coeffs": "1, 10, 35, 50, 24",
        "description": "s⁴ + 10s³ + 35s² + 50s + 24 — all stable",
    },
    "parametric": {
        "label": "Parametric (K-dependent)",
        "coeffs": "1, 3, 3, 1",
        "description": "s³ + 3s² + 3s + (1+K) — stability depends on K",
    },
    "zero_row": {
        "label": "Special: All-Zero Row",
        "coeffs": "1, 2, 6, 4, 8",
        "description": "s⁴ + 2s³ + 6s² + 4s + 8 — triggers auxiliary polynomial derivative",
    },
    "zero_pivot": {
        "label": "Special: Zero in First Column",
        "coeffs": "1, 0, 2, 1",
        "description": "s³ + 0s² + 2s + 1 — triggers epsilon replacement",
    },
}

PRESET_OPTIONS = [{"value": k, "label": v["label"]} for k, v in PRESETS.items()]


class RouthHurwitzSimulator(BaseSimulator):
    """Routh-Hurwitz Stability Criterion interactive tool."""

    PARAMETER_SCHEMA = {
        "preset": {
            "type": "select",
            "options": PRESET_OPTIONS,
            "default": "stable_3rd",
        },
        "poly_coeffs": {
            "type": "expression",
            "default": "1, 6, 11, 6",
        },
        "use_parametric_k": {
            "type": "checkbox",
            "default": False,
        },
        "gain_k": {
            "type": "slider",
            "min": 0,
            "max": 200,
            "step": 0.1,
            "default": 1.0,
            "unit": "",
        },
        "k_max": {
            "type": "slider",
            "min": 10,
            "max": 1000,
            "step": 10,
            "default": 100,
        },
    }

    DEFAULT_PARAMS = {
        "preset": "stable_3rd",
        "poly_coeffs": "1, 6, 11, 6",
        "use_parametric_k": False,
        "gain_k": 1.0,
        "k_max": 100,
    }

    def __init__(self, simulation_id: str):
        super().__init__(simulation_id)
        self._routh_result: Dict[str, Any] = {}
        self._roots: List[complex] = []
        self._char_poly: np.ndarray = np.array([1, 6, 11, 6], dtype=float)
        self._stability_ranges: Dict[str, Any] = {}

    def initialize(self, params: Optional[Dict[str, Any]] = None) -> None:
        """Initialize simulation with parameters."""
        self.parameters = self.DEFAULT_PARAMS.copy()
        if params:
            for name, value in params.items():
                if name in self.parameters:
                    self.parameters[name] = self._validate_param(name, value)
        self._initialized = True
        self._compute()

    def update_parameter(self, name: str, value: Any) -> Dict[str, Any]:
        """Update a single parameter and recompute."""
        if name in self.parameters:
            self.parameters[name] = self._validate_param(name, value)
            # When preset changes, update poly_coeffs and auto-enable K for parametric
            if name == "preset" and value != "custom":
                preset = PRESETS.get(str(value), {})
                if "coeffs" in preset:
                    self.parameters["poly_coeffs"] = preset["coeffs"]
                if value == "parametric":
                    self.parameters["use_parametric_k"] = True
                elif self.parameters["use_parametric_k"]:
                    self.parameters["use_parametric_k"] = False
            # When poly_coeffs changes manually, switch to custom
            if name == "poly_coeffs":
                self.parameters["preset"] = "custom"
            self._compute()
        return self.get_state()

    def reset(self) -> Dict[str, Any]:
        """Reset to default parameters."""
        self.parameters = self.DEFAULT_PARAMS.copy()
        self._initialized = True
        self._compute()
        return self.get_state()

    def _parse_coeffs(self, coeffs_str: str) -> np.ndarray:
        """Parse comma-separated coefficient string to numpy array."""
        try:
            parts = [s.strip() for s in str(coeffs_str).split(",") if s.strip()]
            coeffs = [float(p) for p in parts]
            # Strip leading zeros (e.g. "0, 1, 2" → [1, 2])
            while len(coeffs) > 2 and abs(coeffs[0]) < 1e-12:
                coeffs.pop(0)
            if len(coeffs) < 2:
                return np.array([1, 1], dtype=float)
            return np.array(coeffs, dtype=float)
        except (ValueError, TypeError):
            return np.array([1, 1], dtype=float)

    def _format_polynomial(self, coeffs: np.ndarray, latex: bool = False) -> str:
        """Format polynomial coefficients as a display or LaTeX string."""
        n = len(coeffs) - 1
        terms = []
        for i, c in enumerate(coeffs):
            power = n - i
            if abs(c) < 1e-12:
                continue
            if power == 0:
                term = f"{c:g}"
            elif abs(c) == 1:
                sign = "" if c > 0 else "-"
                if power == 1:
                    term = f"{sign}s"
                else:
                    term = f"{sign}s^{{{power}}}" if latex else f"{sign}s^{power}"
            else:
                if power == 1:
                    term = f"{c:g}s"
                else:
                    term = f"{c:g}s^{{{power}}}" if latex else f"{c:g}s^{power}"
            terms.append(term)

        if not terms:
            return "0"

        result = terms[0]
        for t in terms[1:]:
            if t.startswith("-"):
                result += f" - {t[1:]}"
            else:
                result += f" + {t}"
        return result

    def _compute(self) -> None:
        """Compute Routh array, roots, and stability ranges."""
        base_poly = self._parse_coeffs(self.parameters["poly_coeffs"])
        use_k = bool(self.parameters["use_parametric_k"])
        K = float(self.parameters["gain_k"])

        # Build characteristic polynomial
        if use_k:
            self._char_poly = base_poly.copy()
            self._char_poly[-1] = self._char_poly[-1] + K
        else:
            self._char_poly = base_poly.copy()

        # Compute Routh array
        self._routh_result = compute_routh_array(self._char_poly)

        # Compute roots
        try:
            self._roots = np.roots(self._char_poly).tolist()
        except Exception:
            self._roots = []

        # Compute K stability ranges if parametric K enabled
        if use_k:
            k_max = float(self.parameters["k_max"])
            self._stability_ranges = compute_stability_k_ranges(
                base_poly, k_min=0.0, k_max=k_max, n_test=500
            )
        else:
            self._stability_ranges = {"ranges": [], "critical_k_values": []}

    def get_plots(self) -> List[Dict[str, Any]]:
        """Generate Plotly plot data."""
        if not self._initialized:
            self.initialize()

        plots = []

        # Plot 1: Pole-Zero Map
        plots.append(self._build_pole_zero_plot())

        # Plot 2: K Stability Map (only when parametric K enabled)
        if bool(self.parameters["use_parametric_k"]):
            plots.append(self._build_k_stability_plot())

        return plots

    def _build_pole_zero_plot(self) -> Dict[str, Any]:
        """Build s-plane pole map showing root locations."""
        stable_re, stable_im = [], []
        unstable_re, unstable_im = [], []
        jw_re, jw_im = [], []

        for root in self._roots:
            r = complex(root)
            re, im = r.real, r.imag
            if abs(re) < 1e-8:
                jw_re.append(re)
                jw_im.append(im)
            elif re < 0:
                stable_re.append(re)
                stable_im.append(im)
            else:
                unstable_re.append(re)
                unstable_im.append(im)

        data = []

        # Stable poles (LHP)
        if stable_re:
            data.append({
                "x": stable_re, "y": stable_im,
                "type": "scatter", "mode": "markers",
                "name": "Stable (LHP)",
                "marker": {"symbol": "x", "size": 14, "color": "#10b981",
                           "line": {"width": 2, "color": "#10b981"}},
            })

        # Unstable poles (RHP)
        if unstable_re:
            data.append({
                "x": unstable_re, "y": unstable_im,
                "type": "scatter", "mode": "markers",
                "name": "Unstable (RHP)",
                "marker": {"symbol": "x", "size": 14, "color": "#ef4444",
                           "line": {"width": 2, "color": "#ef4444"}},
            })

        # jω-axis poles
        if jw_re:
            data.append({
                "x": jw_re, "y": jw_im,
                "type": "scatter", "mode": "markers",
                "name": "Marginal (jω)",
                "marker": {"symbol": "x", "size": 14, "color": "#f59e0b",
                           "line": {"width": 2, "color": "#f59e0b"}},
            })

        # Imaginary axis reference
        all_im = stable_im + unstable_im + jw_im
        im_range = max(abs(v) for v in all_im) if all_im else 2
        im_range = max(im_range, 2) * 1.3
        data.append({
            "x": [0, 0], "y": [-im_range, im_range],
            "type": "scatter", "mode": "lines",
            "name": "jω axis",
            "line": {"color": "rgba(148,163,184,0.4)", "width": 1, "dash": "dash"},
            "showlegend": False,
        })

        all_re = stable_re + unstable_re + jw_re
        re_range = max(abs(v) for v in all_re) if all_re else 2
        re_range = max(re_range, 2) * 1.3

        return {
            "id": "pole_zero_map",
            "title": "Pole Locations (s-plane)",
            "data": data,
            "layout": {
                "xaxis": {
                    "title": "Real (σ)",
                    "range": [-re_range, re_range],
                    "gridcolor": "rgba(148,163,184,0.1)",
                    "zerolinecolor": "rgba(148,163,184,0.3)",
                    "scaleanchor": "y",
                },
                "yaxis": {
                    "title": "Imaginary (jω)",
                    "range": [-im_range, im_range],
                    "gridcolor": "rgba(148,163,184,0.1)",
                    "zerolinecolor": "rgba(148,163,184,0.3)",
                },
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)",
                "margin": {"l": 60, "r": 30, "t": 50, "b": 55},
                "uirevision": "pole_zero_map",
                "legend": {"x": 0.02, "y": 0.98, "bgcolor": "rgba(0,0,0,0)"},
                "font": {"family": "Inter, sans-serif", "size": 12},
            },
        }

    def _build_k_stability_plot(self) -> Dict[str, Any]:
        """Build K vs RHP-poles step plot for parametric analysis."""
        k_max = float(self.parameters["k_max"])
        current_k = float(self.parameters["gain_k"])

        # Reuse precomputed K-sweep data from _compute()
        k_vals = self._stability_ranges.get("k_values", [])
        rhp_counts = self._stability_ranges.get("rhp_counts", [])

        data = [
            # RHP pole count trace
            {
                "x": k_vals, "y": rhp_counts,
                "type": "scatter", "mode": "lines",
                "name": "RHP Poles",
                "line": {"color": "#3b82f6", "width": 2, "shape": "hv"},
                "fill": "tozeroy",
                "fillcolor": "rgba(239,68,68,0.1)",
            },
            # Stable region shading (y=0)
            {
                "x": [k for k, c in zip(k_vals, rhp_counts) if c == 0],
                "y": [0 for c in rhp_counts if c == 0],
                "type": "scatter", "mode": "markers",
                "name": "Stable region",
                "marker": {"color": "#10b981", "size": 3, "symbol": "line-ns"},
                "showlegend": False,
            },
            # Current K marker
            {
                "x": [current_k], "y": [self._routh_result.get("rhp_poles", 0)],
                "type": "scatter", "mode": "markers",
                "name": f"K = {current_k:.1f}",
                "marker": {"symbol": "diamond", "size": 14, "color": "#14b8a6",
                           "line": {"width": 2, "color": "#0d9488"}},
            },
        ]

        return {
            "id": "k_stability_map",
            "title": "RHP Poles vs Gain K",
            "data": data,
            "layout": {
                "xaxis": {
                    "title": "Gain K",
                    "range": [0, k_max],
                    "gridcolor": "rgba(148,163,184,0.1)",
                    "zerolinecolor": "rgba(148,163,184,0.3)",
                },
                "yaxis": {
                    "title": "Number of RHP Poles",
                    "gridcolor": "rgba(148,163,184,0.1)",
                    "zerolinecolor": "rgba(148,163,184,0.3)",
                    "dtick": 1,
                },
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)",
                "margin": {"l": 60, "r": 30, "t": 50, "b": 55},
                "uirevision": "k_stability_map",
                "font": {"family": "Inter, sans-serif", "size": 12},
            },
        }

    def get_state(self) -> Dict[str, Any]:
        """Return full simulation state."""
        if not self._initialized:
            self.initialize()

        base_state = super().get_state()

        # Build roots info for frontend
        roots_info = []
        for root in self._roots:
            r = complex(root)
            roots_info.append({
                "re": round(r.real, 6),
                "im": round(r.imag, 6),
                "stable": r.real < -1e-8,
                "marginal": abs(r.real) < 1e-8,
            })

        # Polynomial display strings
        poly_display = self._format_polynomial(self._char_poly)
        poly_latex = self._format_polynomial(self._char_poly, latex=True)
        degree = len(self._char_poly) - 1

        # Preset info
        preset_key = str(self.parameters["preset"])
        preset_info = PRESETS.get(preset_key, {})

        base_state["metadata"] = {
            "simulation_type": "routh_hurwitz",
            "polynomial_display": poly_display,
            "polynomial_latex": poly_latex,
            "degree": degree,
            "routh_table": self._routh_result,
            "roots": roots_info,
            "stability_ranges": self._stability_ranges,
            "preset_description": preset_info.get("description", ""),
            "use_parametric_k": bool(self.parameters["use_parametric_k"]),
            "current_k": float(self.parameters["gain_k"]) if self.parameters["use_parametric_k"] else None,
        }

        return base_state
