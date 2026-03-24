"""
Polynomial Multiplication Visualizer

Demonstrates the tabular/anti-diagonal method for multiplying two operator
power series:
  (1 + aR + a²R² + …) × (1 + bR + b²R² + …)

Collecting terms along anti-diagonals of the multiplication table produces
the combined unit-sample response of two cascaded first-order systems with
poles at a and b.

Graphical and tabular polynomial multiplication of operator series.
"""

from typing import Any, Dict, List, Optional

import numpy as np

from .base_simulator import BaseSimulator


# Unicode superscript digits for formatting exponents
_SUPERSCRIPTS = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")


def _sup(n: int) -> str:
    """Return superscript string for non-negative integer n."""
    if n == 0:
        return "⁰"
    return str(n).translate(_SUPERSCRIPTS)


def _power_label(base: str, exp: int) -> str:
    """Format 'base^exp' with special cases for 0 and 1."""
    if exp == 0:
        return "1"
    if exp == 1:
        return base
    return f"{base}{_sup(exp)}"


class PolynomialMultiplicationSimulator(BaseSimulator):
    """Simulator for polynomial (operator series) multiplication."""

    PARAMETER_SCHEMA = {
        "pole_a": {
            "type": "slider",
            "min": -0.95,
            "max": 0.95,
            "step": 0.05,
            "default": 0.5,
        },
        "pole_b": {
            "type": "slider",
            "min": -0.95,
            "max": 0.95,
            "step": 0.05,
            "default": 0.3,
        },
        "num_terms": {
            "type": "slider",
            "min": 3,
            "max": 10,
            "step": 1,
            "default": 6,
        },
        "view_mode": {
            "type": "select",
            "options": ["tabular", "graphical"],
            "default": "tabular",
        },
    }

    DEFAULT_PARAMS = {
        "pole_a": 0.5,
        "pole_b": 0.3,
        "num_terms": 6,
        "view_mode": "tabular",
    }

    HUB_SLOTS = ['control']

    def initialize(self, params: Optional[Dict[str, Any]] = None) -> None:
        self.parameters = {**self.DEFAULT_PARAMS, **(params or {})}
        for name, value in self.parameters.items():
            if name in self.PARAMETER_SCHEMA:
                self.parameters[name] = self._validate_param(name, value)
        self._initialized = True

    def update_parameter(self, name: str, value: Any) -> Dict[str, Any]:
        if name in self.parameters:
            self.parameters[name] = self._validate_param(name, value)
        return self.get_state()

    def get_plots(self) -> List[Dict[str, Any]]:
        data = self._compute()
        return self._build_plots(data)

    def get_state(self) -> Dict[str, Any]:
        data = self._compute()
        a = data["a"]
        b = data["b"]
        N = data["N"]

        # Build the closed-form description
        if abs(a - b) > 1e-10:
            closed_form = "(a^(n+1) − b^(n+1)) / (a − b)"
            closed_form_display = f"({a:g}ⁿ⁺¹ − {b:g}ⁿ⁺¹) / ({a - b:g})"
        else:
            closed_form = "(n+1) · aⁿ"
            closed_form_display = f"(n+1) · {a:g}ⁿ"

        return {
            "parameters": self.parameters.copy(),
            "plots": self._build_plots(data),
            "metadata": {
                "simulation_type": "polynomial_multiplication",
            "hub_slots": self.HUB_SLOTS,
            "hub_domain": self.HUB_DOMAIN,
            "hub_dimensions": self.HUB_DIMENSIONS,
                "pole_a": float(a),
                "pole_b": float(b),
                "num_terms": int(N),
                "table_data": data["table"].tolist(),
                "row_labels": [_power_label("a", i) for i in range(N)],
                "col_labels": [_power_label("b", j) for j in range(N)],
                "row_values": data["a_powers"].tolist(),
                "col_values": data["b_powers"].tolist(),
                "anti_diagonal_sums": data["anti_diag_sums"].tolist(),
                "num_anti_diagonals": int(len(data["anti_diag_sums"])),
                "closed_form": closed_form,
                "closed_form_display": closed_form_display,
                "view_mode": str(self.parameters["view_mode"]),
            },
        }

    # ── Computation ──────────────────────────────────────────────

    def _compute(self) -> Dict[str, Any]:
        """Compute the multiplication table and anti-diagonal sums."""
        a = float(self.parameters["pole_a"])
        b = float(self.parameters["pole_b"])
        N = int(self.parameters["num_terms"])

        # Powers of a and b
        indices = np.arange(N)
        a_powers = a ** indices  # [1, a, a², ..., a^(N-1)]
        b_powers = b ** indices  # [1, b, b², ..., b^(N-1)]

        # Multiplication table: table[i][j] = a^i * b^j
        table = np.outer(a_powers, b_powers)

        # Anti-diagonal sums: coefficient of R^n
        # For an N×N table, anti-diagonals go from 0 to 2(N-1)
        num_diags = 2 * N - 1
        anti_diag_sums = np.zeros(num_diags)
        for n in range(num_diags):
            for k in range(max(0, n - N + 1), min(n + 1, N)):
                anti_diag_sums[n] += a_powers[k] * b_powers[n - k]

        # Also compute exact coefficients for the full (infinite) series
        full_n = np.arange(num_diags)
        if abs(a - b) > 1e-10:
            exact_coeffs = (a ** (full_n + 1) - b ** (full_n + 1)) / (a - b)
        else:
            exact_coeffs = (full_n + 1) * (a ** full_n)

        return {
            "a": a,
            "b": b,
            "N": N,
            "a_powers": a_powers,
            "b_powers": b_powers,
            "table": table,
            "anti_diag_sums": anti_diag_sums,
            "exact_coeffs": exact_coeffs,
            "num_diags": num_diags,
        }

    # ── Plot Construction ────────────────────────────────────────

    def _build_plots(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build all plots from pre-computed data (single computation)."""
        return [
            self._create_h1_plot(data),
            self._create_h2_plot(data),
            self._create_combined_plot(data),
        ]

    def _get_base_layout(self, xtitle: str, ytitle: str) -> Dict[str, Any]:
        """Standard Plotly layout for stem plots."""
        return {
            "xaxis": {
                "title": {"text": xtitle, "font": {"color": "#f1f5f9", "size": 13}},
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
                "color": "#94a3b8",
                "dtick": 1,
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
            "font": {"family": "Inter, sans-serif", "size": 12, "color": "#f1f5f9"},
            "margin": {"t": 45, "r": 25, "b": 55, "l": 60},
            "showlegend": True,
            "legend": {
                "font": {"color": "#94a3b8", "size": 11},
                "bgcolor": "rgba(0,0,0,0)",
            },
        }

    @staticmethod
    def _auto_y_range(values: np.ndarray, padding: float = 0.2) -> List[float]:
        """Compute a y-axis range that fits all values with padding."""
        y_min = float(values.min())
        y_max = float(values.max())
        span = y_max - y_min
        if span < 1e-10:
            # All values identical — center around value with ±1
            return [y_min - 1.0, y_max + 1.0]
        pad = span * padding
        # Always include 0 on the axis for stem plots
        lo = min(y_min - pad, -pad * 0.5)
        hi = max(y_max + pad, pad * 0.5)
        return [lo, hi]

    @staticmethod
    def _make_stem_traces(
        n_vals: np.ndarray,
        y_vals: np.ndarray,
        name: str,
        color: str,
        marker_size: int = 10,
    ) -> List[Dict[str, Any]]:
        """Build stem plot traces (vertical lines + markers)."""
        n_list = n_vals.tolist()
        y_list = y_vals.tolist()

        # Vertical stem lines with None gaps
        stem_x: List = []
        stem_y: List = []
        for i in range(len(n_list)):
            stem_x.extend([n_list[i], n_list[i], None])
            stem_y.extend([0, y_list[i], None])

        return [
            {
                "x": stem_x,
                "y": stem_y,
                "type": "scatter",
                "mode": "lines",
                "name": "Stems",
                "line": {"color": color, "width": 2},
                "showlegend": False,
                "hoverinfo": "skip",
            },
            {
                "x": n_list,
                "y": y_list,
                "type": "scatter",
                "mode": "markers",
                "name": name,
                "marker": {
                    "color": color,
                    "size": marker_size,
                    "line": {"color": "#0a0e27", "width": 1.5},
                },
                "hovertemplate": "n=%{x}<br>value=%{y:.4f}<extra></extra>",
            },
        ]

    def _create_h1_plot(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Stem plot of h₁[n] = aⁿ."""
        a = data["a"]
        N = data["N"]
        n = np.arange(N)
        h1 = data["a_powers"]

        traces = self._make_stem_traces(n, h1, f"h₁[n] = ({a:g})ⁿ", "#3b82f6")

        layout = self._get_base_layout("n", "h₁[n]")
        layout["xaxis"]["range"] = [-0.5, N - 0.5]
        layout["yaxis"]["range"] = self._auto_y_range(h1)
        layout["yaxis"]["autorange"] = False

        return {
            "id": "h1_response",
            "title": f"h₁[n] = aⁿ = ({a:g})ⁿ",
            "data": traces,
            "layout": layout,
        }

    def _create_h2_plot(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Stem plot of h₂[n] = bⁿ."""
        b = data["b"]
        N = data["N"]
        n = np.arange(N)
        h2 = data["b_powers"]

        traces = self._make_stem_traces(n, h2, f"h₂[n] = ({b:g})ⁿ", "#ef4444")

        layout = self._get_base_layout("n", "h₂[n]")
        layout["xaxis"]["range"] = [-0.5, N - 0.5]
        layout["yaxis"]["range"] = self._auto_y_range(h2)
        layout["yaxis"]["autorange"] = False

        return {
            "id": "h2_response",
            "title": f"h₂[n] = bⁿ = ({b:g})ⁿ",
            "data": traces,
            "layout": layout,
        }

    def _create_combined_plot(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Stem plot of combined response cₙ."""
        a = data["a"]
        b = data["b"]
        num_diags = data["num_diags"]
        coeffs = data["anti_diag_sums"]
        n = np.arange(num_diags)

        # Combined response stems
        traces = self._make_stem_traces(
            n, coeffs, "cₙ (table sum)", "#14b8a6", marker_size=10
        )

        # Overlay exact closed-form at integer points (safe for negative poles)
        n_exact = np.arange(num_diags)
        if abs(a - b) > 1e-10:
            exact_vals = (a ** (n_exact + 1) - b ** (n_exact + 1)) / (a - b)
        else:
            exact_vals = (n_exact + 1) * (a ** n_exact)

        traces.append({
            "x": n_exact.tolist(),
            "y": exact_vals.tolist(),
            "type": "scatter",
            "mode": "lines",
            "name": "Exact (closed form)",
            "line": {"color": "#14b8a6", "width": 1.5, "dash": "dash"},
            "opacity": 0.5,
        })

        # Use both table sums and exact values for range computation
        all_vals = np.concatenate([coeffs, exact_vals])
        layout = self._get_base_layout("n", "cₙ")
        layout["xaxis"]["range"] = [-0.5, num_diags - 0.5]
        layout["yaxis"]["range"] = self._auto_y_range(all_vals)
        layout["yaxis"]["autorange"] = False

        return {
            "id": "combined_response",
            "title": "Combined: cₙ = Σ aᵏbⁿ⁻ᵏ",
            "data": traces,
            "layout": layout,
        }
