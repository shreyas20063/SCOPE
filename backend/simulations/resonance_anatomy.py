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
        self._compute_system()
        return self.get_state()

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
            poles_str = f"s = {s1_r} \u00b1 j{s1_i}"
        elif self._damping_type == "critically_damped":
            poles_str = f"s = {round(self._pole_s1.real, 3)} (repeated)"
        else:
            poles_str = f"s\u2081 = {round(self._pole_s1.real, 3)}, s\u2082 = {round(self._pole_s2.real, 3)}"

        tf_str = f"{K:.1f} / ({M:.1f}s\u00b2 + {B:.1f}s + {K:.1f})"

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

    # ------------------------------------------------------------------
    # Core computation
    # ------------------------------------------------------------------

    def _compute_system(self) -> None:
        """Compute all derived quantities from current parameters."""
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

        self._revision += 1

    # ------------------------------------------------------------------
    # Magnitude response plot
    # ------------------------------------------------------------------

    def _create_magnitude_plot(self) -> Dict[str, Any]:
        """Build the magnitude response |H(jω)| with frequency markers."""
        K = float(self.parameters["K"])
        M = float(self.parameters["M"])
        omega = self._omega
        omega_0 = self._omega_0
        sigma = self._sigma

        # Compute |H(jω)|
        numerator = K / M
        denom_sq = (omega_0 ** 2 - omega ** 2) ** 2 + (2.0 * sigma * omega) ** 2
        denom_sq = np.maximum(denom_sq, 1e-20)
        magnitude = numerator / np.sqrt(denom_sq)
        magnitude = np.minimum(magnitude, self.MAG_CAP)

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

        return {
            "id": "magnitude_response",
            "title": "Magnitude Response |H(j\u03c9)|",
            "data": traces,
            "layout": {
                "xaxis": {
                    "title": "Frequency \u03c9 (rad/s)",
                    "showgrid": True,
                    "gridcolor": self.GRID_COLOR,
                    "zeroline": True,
                    "zerolinecolor": self.ZEROLINE_COLOR,
                    "range": [0, omega_max],
                    "color": self.WHITE,
                },
                "yaxis": {
                    "title": "|H(j\u03c9)|",
                    "showgrid": True,
                    "gridcolor": self.GRID_COLOR,
                    "zeroline": True,
                    "zerolinecolor": self.ZEROLINE_COLOR,
                    "rangemode": "tozero",
                    "autorange": True,
                    "color": self.WHITE,
                },
                "annotations": annotations,
                "paper_bgcolor": "rgba(0,0,0,0)",
                "plot_bgcolor": "rgba(0,0,0,0)",
                "font": {"family": "Inter, sans-serif", "size": 12, "color": self.WHITE},
                "margin": {"t": 50, "r": 25, "b": 55, "l": 60},
                "showlegend": True,
                "legend": {
                    "font": {"color": "#94a3b8", "size": 11},
                    "bgcolor": self.LEGEND_BG,
                    "bordercolor": "rgba(148,163,184,0.2)",
                    "borderwidth": 1,
                    "x": 1.0, "xanchor": "right",
                    "y": 1.0, "yanchor": "top",
                },
                "datarevision": f"magnitude_response-{self._revision}-{fingerprint}",
                "uirevision": fingerprint,
            },
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
            # σ label at midpoint
            mid_x = p_re / 2.0

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

        return {
            "id": "s_plane",
            "title": "S-Plane: Pole Geometry",
            "data": traces,
            "layout": {
                "xaxis": {
                    "title": "Re(s)",
                    "showgrid": True,
                    "gridcolor": self.GRID_COLOR,
                    "zeroline": True,
                    "zerolinecolor": self.ZEROLINE_COLOR,
                    "range": axis_range,
                    "color": self.WHITE,
                    "constrain": "domain",
                },
                "yaxis": {
                    "title": "Im(s)",
                    "showgrid": True,
                    "gridcolor": self.GRID_COLOR,
                    "zeroline": True,
                    "zerolinecolor": self.ZEROLINE_COLOR,
                    "range": y_range,
                    "scaleanchor": "x",
                    "scaleratio": 1,
                    "color": self.WHITE,
                    "constrain": "domain",
                },
                "annotations": plot_annotations,
                "paper_bgcolor": "rgba(0,0,0,0)",
                "plot_bgcolor": "rgba(0,0,0,0)",
                "font": {"family": "Inter, sans-serif", "size": 12, "color": self.WHITE},
                "margin": {"t": 50, "r": 30, "b": 55, "l": 60},
                "showlegend": True,
                "legend": {
                    "font": {"color": "#94a3b8", "size": 10},
                    "bgcolor": self.LEGEND_BG,
                    "bordercolor": "rgba(148,163,184,0.2)",
                    "borderwidth": 1,
                    "x": 0.0, "xanchor": "left",
                    "y": 1.0, "yanchor": "top",
                },
                "datarevision": f"s_plane-{self._revision}-{fingerprint}",
                "uirevision": fingerprint,
            },
        }

    # ------------------------------------------------------------------
    # Impulse response plot
    # ------------------------------------------------------------------

    def _create_impulse_plot(self) -> Dict[str, Any]:
        """Build the impulse response h(t) with envelope and period markers."""
        t = self._t
        M = float(self.parameters["M"])
        sigma = self._sigma

        traces = []

        if self._damping_type in ("undamped", "underdamped"):
            omega_d = self._omega_d
            if omega_d > 1e-10:
                scale = 1.0 / (M * omega_d)
                h_t = scale * np.exp(-sigma * t) * np.sin(omega_d * t)

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
                    env_pos = scale * np.exp(-sigma * t)
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
                h_t = np.zeros_like(t)
                traces.append({
                    "x": t.tolist(),
                    "y": h_t.tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "name": "h(t)",
                    "line": {"color": self.WHITE, "width": 2.5},
                })

        elif self._damping_type == "critically_damped":
            h_t = (1.0 / M) * t * np.exp(-sigma * t)
            traces.append({
                "x": t.tolist(),
                "y": h_t.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": "h(t) = (t/M)e^(-\u03c3t)",
                "line": {"color": self.WHITE, "width": 2.5},
            })

        else:  # overdamped
            s1 = self._pole_s1.real
            s2 = self._pole_s2.real
            diff = s1 - s2
            if abs(diff) > 1e-10:
                scale_od = 1.0 / (M * diff)
                h_t = scale_od * (np.exp(s1 * t) - np.exp(s2 * t))
            else:
                h_t = (1.0 / M) * t * np.exp(s1 * t)
            traces.append({
                "x": t.tolist(),
                "y": h_t.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": "h(t)",
                "line": {"color": self.WHITE, "width": 2.5},
            })

        fingerprint = f"impulse-{self._omega_0:.4f}-{self._sigma:.4f}"

        return {
            "id": "impulse_response",
            "title": "Impulse Response h(t)",
            "data": traces,
            "layout": {
                "xaxis": {
                    "title": "Time t (s)",
                    "showgrid": True,
                    "gridcolor": self.GRID_COLOR,
                    "zeroline": True,
                    "zerolinecolor": self.ZEROLINE_COLOR,
                    "range": [0, float(self.parameters["time_window"])],
                    "color": self.WHITE,
                },
                "yaxis": {
                    "title": "h(t)",
                    "showgrid": True,
                    "gridcolor": self.GRID_COLOR,
                    "zeroline": True,
                    "zerolinecolor": self.ZEROLINE_COLOR,
                    "autorange": True,
                    "color": self.WHITE,
                },
                "paper_bgcolor": "rgba(0,0,0,0)",
                "plot_bgcolor": "rgba(0,0,0,0)",
                "font": {"family": "Inter, sans-serif", "size": 12, "color": self.WHITE},
                "margin": {"t": 50, "r": 25, "b": 55, "l": 60},
                "showlegend": True,
                "legend": {
                    "font": {"color": "#94a3b8", "size": 11},
                    "bgcolor": self.LEGEND_BG,
                    "bordercolor": "rgba(148,163,184,0.2)",
                    "borderwidth": 1,
                    "x": 1.0, "xanchor": "right",
                    "y": 1.0, "yanchor": "top",
                },
                "datarevision": f"impulse_response-{self._revision}-{fingerprint}",
                "uirevision": fingerprint,
            },
        }
