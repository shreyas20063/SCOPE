"""
Cascade ↔ Parallel Decomposition Workbench

Decomposes a second-order DT system into three equivalent forms:
  - Original (direct form): y[n] = a₁·y[n-1] + a₂·y[n-2] + x[n]
  - Cascade (series): H(z) = H₁(z)·H₂(z)
  - Parallel (partial fractions): H(z) = A₁/(1-p₁z⁻¹) + A₂/(1-p₂z⁻¹)

Step-by-step factoring animation shows the algebra, and all three
impulse responses overlay to prove equivalence.

Based on MIT 6.003 Lecture 3, Slides 13–20.
"""

from typing import Any, Dict, List, Optional

import numpy as np

from .base_simulator import BaseSimulator


class CascadeParallelSimulator(BaseSimulator):
    """Simulator for cascade/parallel decomposition of second-order DT systems."""

    NUM_SAMPLES = 40
    NUM_SAMPLES_UNSTABLE = 25
    CLAMP_VALUE = 100.0

    PARAMETER_SCHEMA = {
        "a1": {
            "type": "slider",
            "min": -2.0,
            "max": 2.0,
            "step": 0.01,
            "default": 1.6,
        },
        "a2": {
            "type": "slider",
            "min": -1.0,
            "max": 1.0,
            "step": 0.01,
            "default": -0.63,
        },
    }

    DEFAULT_PARAMS = {
        "a1": 1.6,
        "a2": -0.63,
    }

    def __init__(self, simulation_id: str) -> None:
        super().__init__(simulation_id)
        self._decomposition_step: int = 0

        # Computed quantities
        self._p1: complex = 0.0
        self._p2: complex = 0.0
        self._poles_are_complex: bool = False
        self._poles_are_repeated: bool = False
        self._A1: complex = 0.0
        self._A2: complex = 0.0
        self._discriminant: float = 0.0
        self._is_stable: bool = True

        self._n: Optional[np.ndarray] = None
        self._h_original: Optional[np.ndarray] = None
        self._h_cascade: Optional[np.ndarray] = None
        self._h_parallel: Optional[np.ndarray] = None
        self._mode1: Optional[np.ndarray] = None
        self._mode2: Optional[np.ndarray] = None

        self._factoring_steps: List[Dict[str, Any]] = []

    # ── Lifecycle ────────────────────────────────────────────────

    def initialize(self, params: Optional[Dict[str, Any]] = None) -> None:
        """Initialize simulator with optional parameter overrides."""
        self.parameters = {**self.DEFAULT_PARAMS, **(params or {})}
        for name, value in self.parameters.items():
            if name in self.PARAMETER_SCHEMA:
                self.parameters[name] = self._validate_param(name, value)
        self._initialized = True
        self._decomposition_step = 0
        self._compute()

    def update_parameter(self, name: str, value: Any) -> Dict[str, Any]:
        """Update a single parameter, reset decomposition step, recompute."""
        if name in self.parameters:
            self.parameters[name] = self._validate_param(name, value)
            self._decomposition_step = 0
        self._compute()
        return self.get_state()

    def reset(self) -> Dict[str, Any]:
        """Reset all parameters and decomposition state to defaults."""
        self._decomposition_step = 0
        return super().reset()

    def handle_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle decompose/reset button actions."""
        if action == "decompose":
            self._decomposition_step = min(self._decomposition_step + 1, 4)
        elif action == "reset_decomposition":
            self._decomposition_step = 0
        return self.get_state()

    # ── Core math ────────────────────────────────────────────────

    def _compute(self) -> None:
        """Compute poles, partial-fraction coefficients, and all impulse responses."""
        a1 = float(self.parameters["a1"])
        a2 = float(self.parameters["a2"])

        # Characteristic polynomial: z² - a1·z - a2 = 0
        self._discriminant = a1 * a1 + 4.0 * a2
        disc = self._discriminant

        # Poles
        if abs(disc) < 1e-10:
            # Repeated poles
            self._poles_are_repeated = True
            self._poles_are_complex = False
            p = a1 / 2.0
            self._p1 = complex(p, 0.0)
            self._p2 = complex(p, 0.0)
        elif disc < 0:
            # Complex conjugate poles
            self._poles_are_complex = True
            self._poles_are_repeated = False
            real_part = a1 / 2.0
            imag_part = np.sqrt(-disc) / 2.0
            self._p1 = complex(real_part, imag_part)
            self._p2 = complex(real_part, -imag_part)
        else:
            # Real distinct poles
            self._poles_are_complex = False
            self._poles_are_repeated = False
            sqrt_disc = np.sqrt(disc)
            self._p1 = complex((a1 + sqrt_disc) / 2.0, 0.0)
            self._p2 = complex((a1 - sqrt_disc) / 2.0, 0.0)

        # Stability check
        self._is_stable = abs(self._p1) < 1.0 and abs(self._p2) < 1.0

        # Number of samples
        N = self.NUM_SAMPLES_UNSTABLE if not self._is_stable else self.NUM_SAMPLES
        self._n = np.arange(N)

        # Partial fraction coefficients
        if self._poles_are_repeated:
            p = self._p1
            self._A1 = complex(1.0, 0.0)
            self._A2 = complex(1.0, 0.0)
        else:
            self._A1 = self._p1 / (self._p1 - self._p2)
            self._A2 = self._p2 / (self._p2 - self._p1)

        # ── Impulse responses ──

        # 1) Direct form (iterative)
        h = np.zeros(N)
        h[0] = 1.0
        for i in range(1, N):
            h[i] = a1 * h[i - 1] + (a2 * h[i - 2] if i >= 2 else 0.0)
        self._h_original = self._clamp(h)

        # 2) Cascade form (convolve two first-order impulse responses)
        n = self._n
        if self._poles_are_complex:
            h1 = np.real(self._p1 ** n)
            h2 = np.real(self._p2 ** n)
            h_cascade_full = np.convolve(
                np.real(self._p1 ** np.arange(N)),
                np.real(self._p2 ** np.arange(N)),
            )[:N]
            # For complex poles, direct convolution of real parts doesn't work.
            # Use the full complex convolution and take the real part.
            h1c = self._p1 ** np.arange(N)
            h2c = self._p2 ** np.arange(N)
            h_cascade_full = np.real(np.convolve(h1c, h2c))[:N]
        else:
            h1 = np.real(self._p1 ** n)
            h2 = np.real(self._p2 ** n)
            h_cascade_full = np.convolve(h1, h2)[:N]
        self._h_cascade = self._clamp(h_cascade_full)

        # 3) Parallel form (analytical)
        if self._poles_are_repeated:
            p = self._p1
            h_par = np.real((n + 1) * p ** n)
        else:
            h_par = np.real(self._A1 * self._p1 ** n + self._A2 * self._p2 ** n)
        self._h_parallel = self._clamp(h_par)

        # 4) Individual modes
        if self._poles_are_repeated:
            self._mode1 = self._clamp(np.real(self._p1 ** n))
            self._mode2 = self._clamp(np.real(n * self._p1 ** n))
        else:
            self._mode1 = self._clamp(np.real(self._A1 * self._p1 ** n))
            self._mode2 = self._clamp(np.real(self._A2 * self._p2 ** n))

        # Build factoring steps
        self._build_factoring_steps(a1, a2)

    def _clamp(self, arr: np.ndarray) -> np.ndarray:
        """Clamp values to prevent display explosion for unstable systems."""
        return np.clip(arr, -self.CLAMP_VALUE, self.CLAMP_VALUE)

    def _build_factoring_steps(self, a1: float, a2: float) -> None:
        """Build the step-by-step factoring description list."""
        p1, p2 = self._p1, self._p2

        def fmt_complex(z: complex) -> str:
            if abs(z.imag) < 1e-10:
                return f"{z.real:.4f}"
            sign = "+" if z.imag >= 0 else "-"
            return f"{z.real:.4f} {sign} {abs(z.imag):.4f}j"

        def fmt_a2(val: float) -> str:
            return f"+ {val:.4f}" if val >= 0 else f"- {abs(val):.4f}"

        if self._poles_are_complex:
            r = abs(p1)
            theta = np.angle(p1)
            pole_desc = f"r = {r:.4f}, θ = {np.degrees(theta):.1f}°"
        elif self._poles_are_repeated:
            pole_desc = f"Repeated pole at p = {p1.real:.4f}"
        else:
            pole_desc = f"p₁ = {p1.real:.4f}, p₂ = {p2.real:.4f}"

        a2_sign = fmt_a2(a2)

        self._factoring_steps = [
            {
                "step": 0,
                "title": "Original System",
                "equation": f"y[n] = {a1:.2f} y[n-1] {a2_sign} y[n-2] + x[n]",
                "description": "Second-order difference equation with two feedback taps.",
            },
            {
                "step": 1,
                "title": "Factor the Characteristic Polynomial",
                "equation": f"z² - ({a1:.2f})z - ({a2:.2f}) = (z - {fmt_complex(p1)})(z - {fmt_complex(p2)})",
                "description": f"Discriminant = {self._discriminant:.4f}. {pole_desc}.",
            },
            {
                "step": 2,
                "title": "Cascade (Series) Form",
                "equation": f"H(z) = 1/(1 - {fmt_complex(p1)} z⁻¹) · 1/(1 - {fmt_complex(p2)} z⁻¹)",
                "description": "Two first-order sections in series — output of first feeds into second.",
            },
            {
                "step": 3,
                "title": "Partial Fraction → Parallel Form",
                "equation": (
                    f"H(z) = {fmt_complex(self._A1)}/(1 - {fmt_complex(p1)} z⁻¹) + {fmt_complex(self._A2)}/(1 - {fmt_complex(p2)} z⁻¹)"
                    if not self._poles_are_repeated
                    else f"H(z) = z/(z - {p1.real:.4f})²  →  h[n] = (n+1)·({p1.real:.4f})ⁿ"
                ),
                "description": (
                    f"A₁ = {fmt_complex(self._A1)}, A₂ = {fmt_complex(self._A2)}"
                    if not self._poles_are_repeated
                    else "Repeated pole: partial fractions yield a polynomial-times-geometric mode."
                ),
            },
            {
                "step": 4,
                "title": "Individual Geometric Modes",
                "equation": (
                    f"h[n] = {fmt_complex(self._A1)}·({fmt_complex(p1)})ⁿ + {fmt_complex(self._A2)}·({fmt_complex(p2)})ⁿ"
                    if not self._poles_are_repeated
                    else f"h[n] = ({p1.real:.4f})ⁿ + n·({p1.real:.4f})ⁿ = (n+1)·({p1.real:.4f})ⁿ"
                ),
                "description": "Separate colored curves show each mode; they sum to the total response.",
            },
        ]

    # ── Plot generation ──────────────────────────────────────────

    def get_plots(self) -> List[Dict[str, Any]]:
        """Return plots appropriate for the current decomposition step."""
        if self._n is None:
            self._compute()

        plots: List[Dict[str, Any]] = []
        step = self._decomposition_step

        # Always show original
        plots.append(self._make_stem_plot(
            "original_response",
            "Original Form — h[n]",
            self._h_original,
            "#3b82f6",
            "h[n] (direct)",
        ))

        # Cascade at step >= 2
        if step >= 2:
            plots.append(self._make_stem_plot(
                "cascade_response",
                "Cascade Form — h₁[n] * h₂[n]",
                self._h_cascade,
                "#14b8a6",
                "h[n] (cascade)",
                ghost=self._h_original,
                ghost_label="h[n] (original)",
            ))

        # Parallel at step >= 3
        if step >= 3:
            plots.append(self._make_stem_plot(
                "parallel_response",
                "Parallel Form — A₁p₁ⁿ + A₂p₂ⁿ",
                self._h_parallel,
                "#22d3ee",
                "h[n] (parallel)",
                ghost=self._h_original,
                ghost_label="h[n] (original)",
            ))

        # Individual modes at step 4
        if step >= 4:
            plots.append(self._make_modes_plot())

        return plots

    def _make_stem_plot(
        self,
        plot_id: str,
        title: str,
        h: np.ndarray,
        color: str,
        name: str,
        ghost: Optional[np.ndarray] = None,
        ghost_label: str = "original",
    ) -> Dict[str, Any]:
        """Build a stem plot with optional ghost overlay."""
        n = self._n
        N = len(n)
        traces: List[Dict[str, Any]] = []

        # Ghost trace (original as faded overlay)
        if ghost is not None:
            for i in range(N):
                traces.append({
                    "x": [int(n[i]), int(n[i])],
                    "y": [0, float(ghost[i])],
                    "type": "scatter",
                    "mode": "lines",
                    "line": {"color": "rgba(148,163,184,0.25)", "width": 1},
                    "showlegend": False,
                    "hoverinfo": "skip",
                })
            traces.append({
                "x": n.tolist(),
                "y": ghost.tolist(),
                "type": "scatter",
                "mode": "markers",
                "marker": {"color": "rgba(148,163,184,0.35)", "size": 6},
                "name": ghost_label,
                "hovertemplate": "n=%{x}<br>h[n]=%{y:.4g}<extra></extra>",
            })

        # Main stem lines
        for i in range(N):
            traces.append({
                "x": [int(n[i]), int(n[i])],
                "y": [0, float(h[i])],
                "type": "scatter",
                "mode": "lines",
                "line": {"color": color, "width": 2},
                "showlegend": False,
                "hoverinfo": "skip",
            })

        # Main markers
        traces.append({
            "x": n.tolist(),
            "y": h.tolist(),
            "type": "scatter",
            "mode": "markers",
            "marker": {
                "color": color,
                "size": 9,
                "line": {"color": "rgba(0,0,0,0.3)", "width": 1},
            },
            "name": name,
            "hovertemplate": "n=%{x}<br>h[n]=%{y:.4g}<extra></extra>",
        })

        # Fingerprint for uirevision: when params or step change, reset zoom
        a1 = self.parameters["a1"]
        a2 = self.parameters["a2"]
        revision_key = f"{plot_id}-a1={a1}-a2={a2}-step={self._decomposition_step}"

        layout = self._base_layout("n", "h[n]")
        layout["title"] = {"text": title, "font": {"size": 14, "color": "#f1f5f9"}}
        layout["yaxis"]["autorange"] = True
        layout["xaxis"]["range"] = [-0.5, N - 0.5]
        layout["xaxis"]["dtick"] = max(1, N // 20)
        layout["uirevision"] = revision_key

        # Zero line
        layout["shapes"] = [{
            "type": "line",
            "x0": -0.5, "x1": N - 0.5,
            "y0": 0, "y1": 0,
            "line": {"color": "rgba(148,163,184,0.4)", "width": 1, "dash": "dash"},
        }]

        return {"id": plot_id, "title": title, "data": traces, "layout": layout}

    def _make_modes_plot(self) -> Dict[str, Any]:
        """Build the individual-modes plot with separate colored curves."""
        n = self._n
        N = len(n)
        traces: List[Dict[str, Any]] = []

        mode_configs = [
            (self._mode1, "#fbbf24", "Mode 1: A₁p₁ⁿ" if not self._poles_are_repeated else "Mode 1: pⁿ"),
            (self._mode2, "#f472b6", "Mode 2: A₂p₂ⁿ" if not self._poles_are_repeated else "Mode 2: n·pⁿ"),
        ]

        for mode, color, mode_name in mode_configs:
            # Mode stem lines
            for i in range(N):
                traces.append({
                    "x": [int(n[i]), int(n[i])],
                    "y": [0, float(mode[i])],
                    "type": "scatter",
                    "mode": "lines",
                    "line": {"color": color, "width": 1.5, "dash": "dot"},
                    "showlegend": False,
                    "hoverinfo": "skip",
                })
            traces.append({
                "x": n.tolist(),
                "y": mode.tolist(),
                "type": "scatter",
                "mode": "markers",
                "marker": {"color": color, "size": 7},
                "name": mode_name,
                "hovertemplate": "n=%{x}<br>%{y:.4g}<extra></extra>",
            })

        # Sum (total response) as solid stems
        h_sum = self._h_parallel
        for i in range(N):
            traces.append({
                "x": [int(n[i]), int(n[i])],
                "y": [0, float(h_sum[i])],
                "type": "scatter",
                "mode": "lines",
                "line": {"color": "#22d3ee", "width": 2},
                "showlegend": False,
                "hoverinfo": "skip",
            })
        traces.append({
            "x": n.tolist(),
            "y": h_sum.tolist(),
            "type": "scatter",
            "mode": "markers",
            "marker": {
                "color": "#22d3ee",
                "size": 9,
                "line": {"color": "rgba(0,0,0,0.3)", "width": 1},
            },
            "name": "Sum (total h[n])",
            "hovertemplate": "n=%{x}<br>h[n]=%{y:.4g}<extra></extra>",
        })

        a1 = self.parameters["a1"]
        a2 = self.parameters["a2"]
        revision_key = f"modes-a1={a1}-a2={a2}-step={self._decomposition_step}"

        layout = self._base_layout("n", "h[n]")
        layout["title"] = {
            "text": "Individual Modes",
            "font": {"size": 14, "color": "#f1f5f9"},
        }
        layout["yaxis"]["autorange"] = True
        layout["xaxis"]["range"] = [-0.5, N - 0.5]
        layout["xaxis"]["dtick"] = max(1, N // 20)
        layout["uirevision"] = revision_key

        layout["shapes"] = [{
            "type": "line",
            "x0": -0.5, "x1": N - 0.5,
            "y0": 0, "y1": 0,
            "line": {"color": "rgba(148,163,184,0.4)", "width": 1, "dash": "dash"},
        }]

        return {
            "id": "individual_modes",
            "title": "Individual Modes",
            "data": traces,
            "layout": layout,
        }

    def _base_layout(self, xtitle: str, ytitle: str) -> Dict[str, Any]:
        """Standard Plotly layout template."""
        return {
            "xaxis": {
                "title": xtitle,
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
                "showgrid": True,
            },
            "yaxis": {
                "title": ytitle,
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
                "showgrid": True,
            },
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "font": {"family": "Inter, sans-serif", "size": 12},
            "margin": {"t": 45, "r": 25, "b": 55, "l": 60},
            "legend": {
                "x": 1, "xanchor": "right",
                "y": 1, "yanchor": "top",
                "bgcolor": "rgba(0,0,0,0.3)",
                "font": {"size": 11, "color": "#f1f5f9"},
            },
        }

    # ── State ────────────────────────────────────────────────────

    def get_state(self) -> Dict[str, Any]:
        """Return full state including metadata for the custom viewer."""
        if self._n is None:
            self._compute()

        state = super().get_state()
        state["metadata"] = {
            "simulation_type": "cascade_parallel",
            "sticky_controls": True,
            "decomposition_step": self._decomposition_step,
            "factoring_steps": self._factoring_steps,
            "system_info": {
                "a1": float(self.parameters["a1"]),
                "a2": float(self.parameters["a2"]),
                "p1_real": float(self._p1.real),
                "p1_imag": float(self._p1.imag),
                "p2_real": float(self._p2.real),
                "p2_imag": float(self._p2.imag),
                "poles_are_complex": self._poles_are_complex,
                "poles_are_repeated": self._poles_are_repeated,
                "A1_real": float(self._A1.real),
                "A1_imag": float(self._A1.imag),
                "A2_real": float(self._A2.real),
                "A2_imag": float(self._A2.imag),
                "discriminant": float(self._discriminant),
                "is_stable": self._is_stable,
                "pole_magnitudes": [float(abs(self._p1)), float(abs(self._p2))],
            },
        }
        return state
