"""
Resonance Anatomy Explorer Simulator

Dissects the three characteristic frequencies of a second-order system
H(s) = K / (Ms² + Bs + K): the undamped natural frequency ω₀,
the damped oscillation frequency ω_d, and the magnitude peak frequency ω_peak.
"""
from typing import Any, Dict, List, Optional
import numpy as np
from .base_simulator import BaseSimulator


class ResonanceAnatomySimulator(BaseSimulator):
    """Interactive exploration of second-order system resonance anatomy.

    Visualizes three distinct frequencies and their relationship to damping,
    with s-plane pole geometry, magnitude response, and impulse response.
    """

    # --- Constants ---
    NUM_SAMPLES = 1000
    NUM_FREQ_SAMPLES = 2000
    EPS = 1e-6
    PEAK_THRESHOLD = 1.0 / np.sqrt(2.0)  # ζ < 0.7071 for ω_peak to exist
    MAG_CAP = 1e4  # cap magnitude for undamped case

    # Plot colors
    TEAL = "#14b8a6"
    BLUE = "#3b82f6"
    RED = "#ef4444"
    GREEN = "#10b981"
    AMBER = "#f59e0b"
    PURPLE = "#a855f7"
    CYAN = "#06b6d4"
    WHITE = "#f1f5f9"
    GRID_COLOR = "rgba(148,163,184,0.15)"
    ZEROLINE_COLOR = "rgba(148,163,184,0.3)"
    STABLE_FILL = "rgba(52,211,153,0.08)"
    LEGEND_BG = "rgba(15,23,42,0.8)"

    PARAMETER_SCHEMA: Dict[str, Dict] = {
        "preset": {
            "type": "select", "label": "Preset",
            "options": [
                {"value": "custom", "label": "Custom Parameters"},
                {"value": "sharp_resonance", "label": "Sharp Resonance (high Q, low damping)"},
                {"value": "broad_resonance", "label": "Broad Resonance (low Q, high damping)"},
                {"value": "critical_damping", "label": "Critical Damping (ζ = 1)"},
                {"value": "no_resonance", "label": "No Resonance Peak (overdamped)"},
            ],
            "default": "custom",
        },
        "K": {
            "type": "slider", "label": "Spring Constant (K)",
            "min": 1.0, "max": 100.0, "step": 0.5, "default": 25.0,
            "unit": "N/m",
        },
        "M": {
            "type": "slider", "label": "Mass (M)",
            "min": 0.1, "max": 5.0, "step": 0.1, "default": 1.0,
            "unit": "kg",
        },
        "B": {
            "type": "slider", "label": "Damping (B)",
            "min": 0.0, "max": 20.0, "step": 0.1, "default": 2.0,
            "unit": "Ns/m",
        },
        "time_window": {
            "type": "slider", "label": "Time Window",
            "min": 1.0, "max": 20.0, "step": 0.5, "default": 8.0,
            "unit": "s",
        },
    }

    DEFAULT_PARAMS: Dict[str, Any] = {
        "preset": "custom",
        "K": 25.0,
        "M": 1.0,
        "B": 2.0,
        "time_window": 8.0,
    }


    def __init__(self, simulation_id: str) -> None:
        super().__init__(simulation_id)
        self._omega_0: float = 0.0
        self._sigma: float = 0.0
        self._zeta: float = 0.0
        self._omega_d: Optional[float] = None
        self._omega_peak: Optional[float] = None
        self._damping_type: str = "underdamped"
        self._pole_s1: complex = 0j
        self._pole_s2: complex = 0j
        self._t: np.ndarray = np.array([])
        self._omega: np.ndarray = np.array([])
        self._magnitude: np.ndarray = np.array([])
        self._h_t: np.ndarray = np.array([])
        self._h_scale: float = 0.0
        self._revision: int = 0

    def initialize(self, params: Optional[Dict[str, Any]] = None) -> None:
        self.parameters = {**self.DEFAULT_PARAMS, **(params or {})}
        for name, value in self.parameters.items():
            self.parameters[name] = self._validate_param(name, value)
        self._initialized = True
        self._compute_system()

    def update_parameter(self, name: str, value: Any) -> Dict[str, Any]:
        if name in self.parameters:
            self.parameters[name] = self._validate_param(name, value)
        if name == "preset" and value != "custom":
            self._apply_preset(value)
        self._compute_system()
        return self.get_state()

    def _apply_preset(self, preset: str) -> None:
        """Set K, M, B for textbook resonance cases.

        All presets use K=25, M=1 (omega_0=5 rad/s).
        Critical damping: B = 2*sqrt(M*K) = 10.
        """
        if preset == "sharp_resonance":
            # Q ~ 12.5, zeta ~ 0.04
            self.parameters["K"] = 25.0
            self.parameters["M"] = 1.0
            self.parameters["B"] = 0.4
        elif preset == "broad_resonance":
            # Q ~ 0.83, zeta ~ 0.6 — peak barely visible
            self.parameters["K"] = 25.0
            self.parameters["M"] = 1.0
            self.parameters["B"] = 6.0
        elif preset == "critical_damping":
            # zeta = 1.0 exactly
            self.parameters["K"] = 25.0
            self.parameters["M"] = 1.0
            self.parameters["B"] = 10.0
        elif preset == "no_resonance":
            # zeta ~ 1.5, overdamped
            self.parameters["K"] = 25.0
            self.parameters["M"] = 1.0
            self.parameters["B"] = 15.0

    def reset(self) -> Dict[str, Any]:
        self.parameters = {**self.DEFAULT_PARAMS}
        self._revision = 0
        self._initialized = True
        self._compute_system()
        return self.get_state()

    def get_plots(self) -> List[Dict[str, Any]]:
        if not self._initialized:
            self.initialize()
        return [
            self._create_magnitude_plot(),
            self._create_s_plane_plot(),
            self._create_impulse_plot(),
        ]

    def _axis(self, title: str, **overrides: Any) -> Dict[str, Any]:
        """Shared axis styling (grid, zeroline, dark-theme color) + per-axis extras."""
        axis = {
            "title": title,
            "showgrid": True,
            "gridcolor": self.GRID_COLOR,
            "zeroline": True,
            "zerolinecolor": self.ZEROLINE_COLOR,
            "color": self.WHITE,
        }
        axis.update(overrides)
        return axis

    def _base_layout(
        self,
        xaxis: Dict[str, Any],
        yaxis: Dict[str, Any],
        datarevision: str,
        uirevision: str,
        margin_r: int = 25,
        legend_x: float = 1.0,
        legend_anchor: str = "right",
        legend_size: int = 11,
    ) -> Dict[str, Any]:
        """Common Plotly layout tail shared by all three plots.

        Only axis titles/ranges, legend anchor/size, right margin, and the
        revision strings differ between plots; everything else is identical.
        """
        return {
            "xaxis": xaxis,
            "yaxis": yaxis,
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "font": {"family": "Inter, sans-serif", "size": 12, "color": self.WHITE},
            "margin": {"t": 50, "r": margin_r, "b": 55, "l": 60},
            "showlegend": True,
            "legend": {
                "font": {"color": "#94a3b8", "size": legend_size},
                "bgcolor": self.LEGEND_BG,
                "bordercolor": "rgba(148,163,184,0.2)",
                "borderwidth": 1,
                "x": legend_x, "xanchor": legend_anchor,
                "y": 1.0, "yanchor": "top",
            },
            "datarevision": datarevision,
            "uirevision": uirevision,
        }

    # ------------------------------------------------------------------
    # Core computation
    # ------------------------------------------------------------------

    def _compute_system(self) -> None:
        """Compute three characteristic frequencies and impulse response.

        Implements H(s) = K / (Ms^2 + Bs + K) for a mass-spring-damper:
            omega_0    = sqrt(K/M)                 (undamped natural frequency)
            omega_d    = sqrt(omega_0^2 - sigma^2)  (damped oscillation frequency, exists when zeta < 1)
            omega_peak = sqrt(omega_0^2 - 2*sigma^2) (magnitude peak frequency, exists when zeta < 1/sqrt(2))
        where sigma = B/(2M) and zeta = B/(2*sqrt(MK)).

        Reference: Ogata, Modern Control Engineering, Sec. 3.6 (resonance characteristics).
        """
        K = float(self.parameters["K"])
        M = float(self.parameters["M"])
        B = float(self.parameters["B"])
        T = float(self.parameters["time_window"])

        # Fundamental derived quantities
        self._omega_0 = np.sqrt(K / M)
        self._sigma = B / (2.0 * M)
        self._zeta = B / (2.0 * np.sqrt(M * K))

        # Damping classification
        if self._zeta < self.EPS:
            self._damping_type = "undamped"
        elif self._zeta < 1.0 - self.EPS:
            self._damping_type = "underdamped"
        elif self._zeta <= 1.0 + self.EPS:
            self._damping_type = "critically_damped"
        else:
            self._damping_type = "overdamped"

        # ω_d: damped oscillation frequency (exists when ζ < 1)
        if self._damping_type in ("undamped", "underdamped"):
            disc_d = self._omega_0 ** 2 - self._sigma ** 2
            self._omega_d = np.sqrt(max(0.0, disc_d))
        else:
            self._omega_d = None

        # ω_peak: magnitude peak frequency (exists when ζ < 1/√2)
        if self._zeta < self.PEAK_THRESHOLD - self.EPS:
            disc_p = self._omega_0 ** 2 - 2.0 * self._sigma ** 2
            self._omega_peak = np.sqrt(max(0.0, disc_p))
        else:
            self._omega_peak = None

        # Poles
        if self._damping_type in ("undamped", "underdamped"):
            self._pole_s1 = complex(-self._sigma, self._omega_d)
            self._pole_s2 = complex(-self._sigma, -self._omega_d)
        elif self._damping_type == "critically_damped":
            self._pole_s1 = complex(-self._sigma, 0)
            self._pole_s2 = complex(-self._sigma, 0)
        else:
            sqrt_term = np.sqrt(self._sigma ** 2 - self._omega_0 ** 2)
            self._pole_s1 = complex(-self._sigma + sqrt_term, 0)
            self._pole_s2 = complex(-self._sigma - sqrt_term, 0)

        # Time and frequency arrays
        self._t = np.linspace(0, T, self.NUM_SAMPLES)
        omega_max = max(3.0 * self._omega_0, 10.0)
        self._omega = np.linspace(0.01, omega_max, self.NUM_FREQ_SAMPLES)

        # Response arrays
        self._magnitude = self._compute_magnitude(K, M)
        self._h_t, self._h_scale = self._compute_impulse_response(M)

        self._revision += 1

    def _compute_magnitude(self, K: float, M: float) -> np.ndarray:
        """|H(jω)| for H(s) = K / (Ms² + Bs + K), capped for the undamped case."""
        omega = self._omega
        numerator = K / M
        denom_sq = (self._omega_0 ** 2 - omega ** 2) ** 2 + (2.0 * self._sigma * omega) ** 2
        denom_sq = np.maximum(denom_sq, 1e-20)
        magnitude = numerator / np.sqrt(denom_sq)
        return np.minimum(magnitude, self.MAG_CAP)

    def _compute_impulse_response(self, M: float) -> tuple:
        """h(t) for each damping regime.

        Returns (h_t, scale). `scale` is the underdamped envelope amplitude
        1/(M·ω_d) (0.0 for the other regimes, where no envelope is drawn).
        """
        t = self._t
        sigma = self._sigma
        scale = 0.0

        if self._damping_type in ("undamped", "underdamped"):
            omega_d = self._omega_d
            if omega_d > 1e-10:
                scale = 1.0 / (M * omega_d)
                h_t = scale * np.exp(-sigma * t) * np.sin(omega_d * t)
            else:
                h_t = np.zeros_like(t)
        elif self._damping_type == "critically_damped":
            h_t = (1.0 / M) * t * np.exp(-sigma * t)
        else:  # overdamped
            s1 = self._pole_s1.real
            s2 = self._pole_s2.real
            diff = s1 - s2
            if abs(diff) > 1e-10:
                scale_od = 1.0 / (M * diff)
                h_t = scale_od * (np.exp(s1 * t) - np.exp(s2 * t))
            else:
                h_t = (1.0 / M) * t * np.exp(s1 * t)
        return h_t, scale

    # ------------------------------------------------------------------
    # Magnitude response plot
    # ------------------------------------------------------------------

    def _create_magnitude_plot(self) -> Dict[str, Any]:
        """Build the magnitude response |H(jω)| with frequency markers."""
        omega = self._omega
        omega_0 = self._omega_0
        magnitude = self._magnitude

        mag_max = float(np.max(magnitude))
        y_top = mag_max * 1.15

        traces = []

        # Main magnitude curve
        traces.append({
            "x": omega.tolist(),
            "y": magnitude.tolist(),
            "type": "scatter",
            "mode": "lines",
            "name": "|H(j\u03c9)|",
            "line": {"color": self.TEAL, "width": 2.5},
            "hovertemplate": "\u03c9 = %{x:.3f} rad/s<br>|H| = %{y:.4f}<extra></extra>",
        })

        # ω₀ vertical marker (always shown)
        traces.append({
            "x": [omega_0, omega_0],
            "y": [0, y_top],
            "type": "scatter",
            "mode": "lines",
            "name": f"\u03c9\u2080 = {omega_0:.3f} rad/s",
            "line": {"color": self.AMBER, "width": 2, "dash": "dash"},
            "hoverinfo": "name",
        })

        # ω_d vertical marker
        if self._omega_d is not None:
            traces.append({
                "x": [self._omega_d, self._omega_d],
                "y": [0, y_top],
                "type": "scatter",
                "mode": "lines",
                "name": f"\u03c9_d = {self._omega_d:.3f} rad/s",
                "line": {"color": self.BLUE, "width": 2, "dash": "dot"},
                "hoverinfo": "name",
            })

        # ω_peak vertical marker
        if self._omega_peak is not None:
            traces.append({
                "x": [self._omega_peak, self._omega_peak],
                "y": [0, y_top],
                "type": "scatter",
                "mode": "lines",
                "name": f"\u03c9_peak = {self._omega_peak:.3f} rad/s",
                "line": {"color": self.RED, "width": 2, "dash": "dashdot"},
                "hoverinfo": "name",
            })

            # Horizontal peak magnitude marker
            peak_idx = np.argmin(np.abs(omega - self._omega_peak))
            peak_val = float(magnitude[peak_idx])
            traces.append({
                "x": [0, self._omega_peak],
                "y": [peak_val, peak_val],
                "type": "scatter",
                "mode": "lines",
                "name": f"Peak = {peak_val:.3f}",
                "line": {"color": self.RED, "width": 1, "dash": "dot"},
                "opacity": 0.5,
                "showlegend": False,
            })

        # Annotations for frequency labels at top
        annotations = []
        annotations.append({
            "x": omega_0, "y": 1.03, "xref": "x", "yref": "paper",
            "text": "\u03c9\u2080", "showarrow": False,
            "font": {"color": self.AMBER, "size": 13, "family": "Fira Code, monospace"},
        })
        if self._omega_d is not None:
            annotations.append({
                "x": self._omega_d, "y": 1.03, "xref": "x", "yref": "paper",
                "text": "\u03c9_d", "showarrow": False,
                "font": {"color": self.BLUE, "size": 13, "family": "Fira Code, monospace"},
            })
        if self._omega_peak is not None:
            annotations.append({
                "x": self._omega_peak, "y": 1.03, "xref": "x", "yref": "paper",
                "text": "\u03c9_pk", "showarrow": False,
                "font": {"color": self.RED, "size": 13, "family": "Fira Code, monospace"},
            })

        omega_max = float(self._omega[-1])
        fingerprint = f"mag-{self._omega_0:.4f}-{self._sigma:.4f}-{self._zeta:.4f}"

        layout = self._base_layout(
            xaxis=self._axis("Frequency \u03c9 (rad/s)", range=[0, omega_max]),
            yaxis=self._axis("|H(j\u03c9)|", rangemode="tozero", autorange=True),
            datarevision=f"magnitude_response-{self._revision}-{fingerprint}",
            uirevision=fingerprint,
        )
        layout["annotations"] = annotations

        return {
            "id": "magnitude_response",
            "title": "Magnitude Response |H(j\u03c9)|",
            "data": traces,
            "layout": layout,
        }

    # ------------------------------------------------------------------
    # S-plane plot
    # ------------------------------------------------------------------

    def _create_s_plane_plot(self) -> Dict[str, Any]:
        """Build the s-plane pole plot with geometric decomposition."""
        omega_0 = self._omega_0
        sigma = self._sigma

        # Determine axis range
        max_extent = max(abs(self._pole_s1.real), abs(self._pole_s1.imag),
                         abs(self._pole_s2.real), abs(self._pole_s2.imag),
                         omega_0) * 1.4 + 0.5
        axis_range = [-max_extent, max_extent * 0.3]
        y_range = [-max_extent, max_extent]

        traces = []

        # Stable region fill (left half-plane)
        traces.append({
            "x": [axis_range[0], 0, 0, axis_range[0]],
            "y": [y_range[0], y_range[0], y_range[1], y_range[1]],
            "type": "scatter",
            "mode": "none",
            "fill": "toself",
            "fillcolor": self.STABLE_FILL,
            "name": "Stable Region",
            "showlegend": True,
            "hoverinfo": "skip",
        })

        # jω axis (stability boundary)
        traces.append({
            "x": [0, 0],
            "y": [y_range[0], y_range[1]],
            "type": "scatter",
            "mode": "lines",
            "name": "j\u03c9 axis",
            "line": {"color": self.PURPLE, "width": 1.5, "dash": "dash"},
            "showlegend": False,
            "hoverinfo": "skip",
        })

        # ω₀ circle
        theta = np.linspace(0, 2 * np.pi, 200)
        circle_x = omega_0 * np.cos(theta)
        circle_y = omega_0 * np.sin(theta)
        traces.append({
            "x": circle_x.tolist(),
            "y": circle_y.tolist(),
            "type": "scatter",
            "mode": "lines",
            "name": f"|s| = \u03c9\u2080 = {omega_0:.2f}",
            "line": {"color": self.AMBER, "width": 1.5, "dash": "dot"},
            "hoverinfo": "skip",
        })

        # Poles
        pole_x = [self._pole_s1.real, self._pole_s2.real]
        pole_y = [self._pole_s1.imag, self._pole_s2.imag]
        traces.append({
            "x": pole_x,
            "y": pole_y,
            "type": "scatter",
            "mode": "markers+text",
            "name": "Poles",
            "marker": {
                "symbol": "x",
                "size": 14,
                "color": self.RED,
                "line": {"width": 3, "color": self.RED},
            },
            "text": ["s\u2081", "s\u2082"],
            "textposition": "top right",
            "textfont": {"color": self.RED, "size": 12, "family": "Fira Code, monospace"},
        })

        # Geometric decomposition (only for complex poles)
        if self._damping_type in ("undamped", "underdamped") and self._omega_d is not None:
            p_re = self._pole_s1.real  # -σ
            p_im = self._pole_s1.imag  # ω_d

            # Horizontal line: pole → jω axis (shows σ)
            traces.append({
                "x": [p_re, 0],
                "y": [p_im, p_im],
                "type": "scatter",
                "mode": "lines",
                "name": f"\u03c3 = {sigma:.3f}",
                "line": {"color": "#94a3b8", "width": 1.5, "dash": "dot"},
                "hoverinfo": "name",
            })

            # Vertical line: pole → real axis (shows ω_d)
            traces.append({
                "x": [p_re, p_re],
                "y": [0, p_im],
                "type": "scatter",
                "mode": "lines",
                "name": f"\u03c9_d = {self._omega_d:.3f}",
                "line": {"color": "#94a3b8", "width": 1.5, "dash": "dot"},
                "showlegend": False,
                "hoverinfo": "name",
            })

            # Line from origin to pole (shows |s| = ω₀)
            traces.append({
                "x": [0, p_re],
                "y": [0, p_im],
                "type": "scatter",
                "mode": "lines",
                "name": f"\u03c9\u2080 = {omega_0:.3f}",
                "line": {"color": self.AMBER, "width": 1.2},
                "showlegend": False,
                "hoverinfo": "name",
            })

        fingerprint = f"splane-{self._omega_0:.4f}-{self._sigma:.4f}"

        # Annotations for σ and ω_d
        plot_annotations = []
        if self._damping_type in ("undamped", "underdamped") and self._omega_d is not None:
            p_re = self._pole_s1.real
            p_im = self._pole_s1.imag
            plot_annotations.append({
                "x": p_re / 2.0, "y": p_im + max_extent * 0.06,
                "xref": "x", "yref": "y",
                "text": "\u03c3", "showarrow": False,
                "font": {"color": "#94a3b8", "size": 13, "family": "Fira Code, monospace"},
            })
            plot_annotations.append({
                "x": p_re - max_extent * 0.06, "y": p_im / 2.0,
                "xref": "x", "yref": "y",
                "text": "\u03c9_d", "showarrow": False,
                "font": {"color": "#94a3b8", "size": 13, "family": "Fira Code, monospace"},
            })

        layout = self._base_layout(
            xaxis=self._axis("Re(s)", range=axis_range, constrain="domain"),
            yaxis=self._axis(
                "Im(s)", range=y_range, scaleanchor="x", scaleratio=1,
                constrain="domain",
            ),
            datarevision=f"s_plane-{self._revision}-{fingerprint}",
            uirevision=fingerprint,
            margin_r=30,
            legend_x=0.0,
            legend_anchor="left",
            legend_size=10,
        )
        layout["annotations"] = plot_annotations

        return {
            "id": "s_plane",
            "title": "S-Plane: Pole Geometry",
            "data": traces,
            "layout": layout,
        }

    # ------------------------------------------------------------------
    # Impulse response plot
    # ------------------------------------------------------------------

    def _create_impulse_plot(self) -> Dict[str, Any]:
        """Build the impulse response h(t) with envelope and period markers."""
        t = self._t
        sigma = self._sigma
        h_t = self._h_t

        traces = []

        if self._damping_type in ("undamped", "underdamped"):
            omega_d = self._omega_d
            if omega_d > 1e-10:
                traces.append({
                    "x": t.tolist(),
                    "y": h_t.tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "name": "h(t)",
                    "line": {"color": self.WHITE, "width": 2.5},
                })

                # Envelope (only if there's damping)
                if sigma > 1e-10:
                    env_pos = self._h_scale * np.exp(-sigma * t)
                    env_neg = -env_pos
                    traces.append({
                        "x": t.tolist(),
                        "y": env_pos.tolist(),
                        "type": "scatter",
                        "mode": "lines",
                        "name": "Envelope \u00b1e^(-\u03c3t)/(M\u03c9_d)",
                        "line": {"color": self.GREEN, "width": 1.5, "dash": "dash"},
                    })
                    traces.append({
                        "x": t.tolist(),
                        "y": env_neg.tolist(),
                        "type": "scatter",
                        "mode": "lines",
                        "name": "Envelope",
                        "line": {"color": self.GREEN, "width": 1.5, "dash": "dash"},
                        "showlegend": False,
                    })

                # Period markers
                if omega_d > 1e-10:
                    period = 2.0 * np.pi / omega_d
                    T_max = float(t[-1])
                    h_max = float(np.max(np.abs(h_t))) * 1.1
                    marker_times = np.arange(period, T_max, period)
                    for i, mt in enumerate(marker_times[:6]):  # max 6 markers
                        traces.append({
                            "x": [float(mt), float(mt)],
                            "y": [-h_max, h_max],
                            "type": "scatter",
                            "mode": "lines",
                            "name": f"T_d = {period:.3f} s" if i == 0 else "T_d",
                            "line": {"color": self.CYAN, "width": 1, "dash": "dot"},
                            "opacity": 0.35,
                            "showlegend": i == 0,
                            "hoverinfo": "skip",
                        })
            else:
                # ω_d effectively zero
                traces.append({
                    "x": t.tolist(),
                    "y": h_t.tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "name": "h(t)",
                    "line": {"color": self.WHITE, "width": 2.5},
                })

        elif self._damping_type == "critically_damped":
            traces.append({
                "x": t.tolist(),
                "y": h_t.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": "h(t) = (t/M)e^(-\u03c3t)",
                "line": {"color": self.WHITE, "width": 2.5},
            })

        else:  # overdamped
            traces.append({
                "x": t.tolist(),
                "y": h_t.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": "h(t)",
                "line": {"color": self.WHITE, "width": 2.5},
            })

        fingerprint = f"impulse-{self._omega_0:.4f}-{self._sigma:.4f}"

        layout = self._base_layout(
            xaxis=self._axis(
                "Time t (s)", range=[0, float(self.parameters["time_window"])],
            ),
            yaxis=self._axis("h(t)", autorange=True),
            datarevision=f"impulse_response-{self._revision}-{fingerprint}",
            uirevision=fingerprint,
        )

        return {
            "id": "impulse_response",
            "title": "Impulse Response h(t)",
            "data": traces,
            "layout": layout,
        }

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    def get_state(self) -> Dict[str, Any]:
        if not self._initialized:
            self.initialize()

        K = float(self.parameters["K"])
        M = float(self.parameters["M"])
        B = float(self.parameters["B"])

        # Format pole string
        if self._damping_type in ("undamped", "underdamped"):
            s1_r = round(self._pole_s1.real, 3)
            s1_i = round(abs(self._pole_s1.imag), 3)
            poles_str = f"s = {s1_r} ± j{s1_i}"
        elif self._damping_type == "critically_damped":
            poles_str = f"s = {round(self._pole_s1.real, 3)} (repeated)"
        else:
            poles_str = f"s₁ = {round(self._pole_s1.real, 3)}, s₂ = {round(self._pole_s2.real, 3)}"

        tf_str = f"{K:.1f} / ({M:.1f}s² + {B:.1f}s + {K:.1f})"

        return {
            "parameters": self.parameters.copy(),
            "plots": self.get_plots(),
            "metadata": {
                "simulation_type": "resonance_anatomy",
                "hub_slots": self.HUB_SLOTS,
                "hub_domain": self.HUB_DOMAIN,
                "hub_dimensions": self.HUB_DIMENSIONS,
                "sticky_controls": True,
                "system_info": {
                    "omega_0": round(self._omega_0, 4),
                    "omega_d": round(self._omega_d, 4) if self._omega_d is not None else None,
                    "omega_peak": round(self._omega_peak, 4) if self._omega_peak is not None else None,
                    "sigma": round(self._sigma, 4) if abs(self._sigma) > 1e-10 else 0.0,
                    "zeta": round(self._zeta, 4),
                    "damping_type": self._damping_type,
                    "peak_threshold": round(self.PEAK_THRESHOLD, 4),
                    "omega_peak_exists": self._omega_peak is not None,
                    "omega_d_exists": self._omega_d is not None,
                    "pole_s1": {
                        "real": round(self._pole_s1.real, 4),
                        "imag": round(self._pole_s1.imag, 4),
                    },
                    "pole_s2": {
                        "real": round(self._pole_s2.real, 4),
                        "imag": round(self._pole_s2.imag, 4),
                    },
                    "K": K, "M": M, "B": B,
                },
                "equations": {
                    "transfer_function": tf_str,
                    "poles_str": poles_str,
                },
            },
        }
