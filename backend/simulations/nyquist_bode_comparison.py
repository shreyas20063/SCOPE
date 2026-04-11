"""
Nyquist-Bode Comparison Simulator

Side-by-side comparison of Nyquist and Bode plots for the same transfer function.
Computes frequency response, stability margins (gain/phase margin), and pole-zero map.
Supports preset transfer functions and custom numerator/denominator entry.
"""

import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from .base_simulator import BaseSimulator


class NyquistBodeComparisonSimulator(BaseSimulator):
    """
    Nyquist-Bode comparison simulation.

    Generates Bode magnitude, Bode phase, Nyquist, and pole-zero plots
    for user-selected transfer functions with stability margin analysis.
    """

    FREQ_POINTS = 2000
    NYQUIST_MAG_CLIP = 500  # Clip Nyquist plot when |H| exceeds this

    # Colors matching codebase conventions
    RESPONSE_COLOR = "#22d3ee"       # Cyan - main response curve
    RESPONSE_COLOR_DIM = "rgba(34, 211, 238, 0.4)"  # Dimmed for negative freq
    POLE_COLOR = "#f87171"           # Red - poles
    ZERO_COLOR = "#3b82f6"           # Blue - zeros
    REFERENCE_COLOR = "#f472b6"      # Pink - reference lines
    STABLE_COLOR = "#34d399"         # Emerald green
    CRITICAL_POINT_COLOR = "#ef4444" # Red - (-1, 0) point
    UNIT_CIRCLE_COLOR = "#10b981"    # Green - unit circle
    CROSSOVER_COLOR = "#fbbf24"      # Amber - crossover markers
    IMAGINARY_AXIS_COLOR = "#a855f7" # Purple - jω axis

    PARAMETER_SCHEMA = {
        "preset": {
            "type": "select",
            "options": [
                {"value": "first_order", "label": "1st Order: K/(s+a)"},
                {"value": "second_order", "label": "2nd Order: Kω₀²/(s²+2ζω₀s+ω₀²)"},
                {"value": "lead_lag", "label": "Lead/Lag: K(s+z)/(s+p)"},
                {"value": "two_real_poles", "label": "Two Poles: K/((s+a)(s+b))"},
                {"value": "integrator_pole", "label": "Integrator: K/(s(s+a))"},
                {"value": "marginally_stable", "label": "Marginally Stable: K/(s(s+1)(s+2))"},
                {"value": "high_gm_low_pm", "label": "High GM, Low PM: K(s+0.5)/((s+1)(s+5)(s+10))"},
                {"value": "custom", "label": "Custom Coefficients"},
            ],
            "default": "second_order",
        },
        "gain_K": {
            "type": "slider", "min": 0.1, "max": 50.0,
            "step": 0.1, "default": 1.0,
        },
        "omega_0": {
            "type": "slider", "min": 0.5, "max": 50.0,
            "step": 0.5, "default": 5.0,
        },
        "zeta": {
            "type": "slider", "min": 0.05, "max": 2.0,
            "step": 0.01, "default": 0.5,
        },
        "pole_a": {
            "type": "slider", "min": 0.1, "max": 20.0,
            "step": 0.1, "default": 2.0,
        },
        "pole_b": {
            "type": "slider", "min": 0.1, "max": 20.0,
            "step": 0.1, "default": 5.0,
        },
        "zero_z": {
            "type": "slider", "min": 0.1, "max": 20.0,
            "step": 0.1, "default": 1.0,
        },
        "pole_p": {
            "type": "slider", "min": 0.1, "max": 20.0,
            "step": 0.1, "default": 10.0,
        },
        "custom_num": {
            "type": "expression", "default": "1",
        },
        "custom_den": {
            "type": "expression", "default": "1, 1",
        },
        "freq_min_exp": {
            "type": "slider", "min": -3, "max": 0,
            "step": 0.1, "default": -2,
        },
        "freq_max_exp": {
            "type": "slider", "min": 1, "max": 4,
            "step": 0.1, "default": 3,
        },
    }

    DEFAULT_PARAMS = {
        "preset": "second_order",
        "gain_K": 1.0,
        "omega_0": 5.0,
        "zeta": 0.5,
        "pole_a": 2.0,
        "pole_b": 5.0,
        "zero_z": 1.0,
        "pole_p": 10.0,
        "custom_num": "1",
        "custom_den": "1, 1",
        "freq_min_exp": -2,
        "freq_max_exp": 3,
    }

    HUB_SLOTS = ['control']

    def __init__(self, simulation_id: str):
        super().__init__(simulation_id)
        self._omega: Optional[np.ndarray] = None
        self._H: Optional[np.ndarray] = None
        self._magnitude_db: Optional[np.ndarray] = None
        self._phase_deg: Optional[np.ndarray] = None
        self._num_coeffs: Optional[np.ndarray] = None
        self._den_coeffs: Optional[np.ndarray] = None
        self._poles: Optional[np.ndarray] = None
        self._zeros: Optional[np.ndarray] = None
        self._stability_info: Dict[str, Any] = {}
        self._tf_expression: str = ""

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
            # Manual edit of custom_num/custom_den switches preset to custom
            if name in ("custom_num", "custom_den"):
                self.parameters["preset"] = "custom"
            self._compute()
        return self.get_state()

    def reset(self) -> Dict[str, Any]:
        """Reset simulation to default parameters."""
        self.parameters = self.DEFAULT_PARAMS.copy()
        self._initialized = True
        self._compute()
        return self.get_state()

    def _compute(self) -> None:
        """Compute Bode magnitude/phase, Nyquist plot, poles/zeros, and stability margins.

        Evaluates H(jw) = num(jw)/den(jw) over the frequency range, then extracts:
            Gain margin:  GM = -20*log10(|H(jw_pc)|) at phase crossover w_pc
            Phase margin: PM = 180 + angle(H(jw_gc)) at gain crossover w_gc

        Reference: Ogata, Modern Control Engineering, Sec. 7.1-7.2 (Bode diagrams and margins).
        """
        self._num_coeffs, self._den_coeffs = self._build_transfer_function()
        self._tf_expression = self._format_tf_expression()
        self._compute_poles_zeros()
        self._compute_frequency_response()
        self._compute_stability_margins()

    # =========================================================================
    # Transfer function construction
    # =========================================================================

    def _build_transfer_function(self) -> Tuple[np.ndarray, np.ndarray]:
        """Build numerator and denominator polynomial coefficients from preset."""
        preset = self.parameters["preset"]
        K = float(self.parameters["gain_K"])

        if preset == "first_order":
            a = float(self.parameters["pole_a"])
            return np.array([K]), np.array([1.0, a])

        elif preset == "second_order":
            w0 = float(self.parameters["omega_0"])
            z = float(self.parameters["zeta"])
            return np.array([K * w0**2]), np.array([1.0, 2 * z * w0, w0**2])

        elif preset == "lead_lag":
            zz = float(self.parameters["zero_z"])
            p = float(self.parameters["pole_p"])
            return np.array([K, K * zz]), np.array([1.0, p])

        elif preset == "two_real_poles":
            a = float(self.parameters["pole_a"])
            b = float(self.parameters["pole_b"])
            return np.array([K]), np.convolve([1.0, a], [1.0, b])

        elif preset == "integrator_pole":
            a = float(self.parameters["pole_a"])
            return np.array([K]), np.array([1.0, a, 0.0])

        elif preset == "marginally_stable":
            # K / (s(s+1)(s+2)) — marginally stable at K=6
            a = float(self.parameters["pole_a"])
            b = float(self.parameters["pole_b"])
            den = np.convolve([1.0, 0.0], np.convolve([1.0, a], [1.0, b]))
            return np.array([K]), den

        elif preset == "high_gm_low_pm":
            # K(s+0.5) / ((s+1)(s+5)(s+10)) — large gain margin, tight phase margin
            zz = float(self.parameters["zero_z"])
            num = np.array([K, K * zz])
            den = np.convolve([1.0, 1.0], np.convolve([1.0, 5.0], [1.0, 10.0]))
            return num, den

        elif preset == "custom":
            num = self._parse_coefficients(
                str(self.parameters.get("custom_num", "1")), fallback=[1.0]
            )
            den = self._parse_coefficients(
                str(self.parameters.get("custom_den", "1, 1")), fallback=[1.0, 1.0]
            )
            return np.array(num) * K, np.array(den)

        # Fallback
        return np.array([K]), np.array([1.0, 1.0])

    @staticmethod
    def _parse_coefficients(s: str, fallback: List[float]) -> List[float]:
        """Parse comma-separated coefficient string, e.g. '1, 2.5, 3'."""
        try:
            coeffs = [float(x.strip()) for x in s.split(",") if x.strip()]
            if not coeffs:
                return fallback
            return coeffs
        except (ValueError, TypeError):
            return fallback

    def _format_tf_expression(self) -> str:
        """Format a human-readable transfer function string."""
        preset = self.parameters["preset"]
        K = float(self.parameters["gain_K"])

        if preset == "first_order":
            a = float(self.parameters["pole_a"])
            return f"H(s) = {K:.2g} / (s + {a:.2g})"
        elif preset == "second_order":
            w0 = float(self.parameters["omega_0"])
            z = float(self.parameters["zeta"])
            return f"H(s) = {K * w0**2:.2g} / (s² + {2*z*w0:.2g}s + {w0**2:.2g})"
        elif preset == "lead_lag":
            zz = float(self.parameters["zero_z"])
            p = float(self.parameters["pole_p"])
            return f"H(s) = {K:.2g}(s + {zz:.2g}) / (s + {p:.2g})"
        elif preset == "two_real_poles":
            a = float(self.parameters["pole_a"])
            b = float(self.parameters["pole_b"])
            return f"H(s) = {K:.2g} / ((s + {a:.2g})(s + {b:.2g}))"
        elif preset == "integrator_pole":
            a = float(self.parameters["pole_a"])
            return f"H(s) = {K:.2g} / (s(s + {a:.2g}))"
        elif preset == "marginally_stable":
            a = float(self.parameters["pole_a"])
            b = float(self.parameters["pole_b"])
            return f"H(s) = {K:.2g} / (s(s + {a:.2g})(s + {b:.2g}))"
        elif preset == "high_gm_low_pm":
            zz = float(self.parameters["zero_z"])
            return f"H(s) = {K:.2g}(s + {zz:.2g}) / ((s + 1)(s + 5)(s + 10))"
        elif preset == "custom":
            num_str = self._poly_to_str(self._num_coeffs)
            den_str = self._poly_to_str(self._den_coeffs)
            return f"H(s) = ({num_str}) / ({den_str})"
        return "H(s) = ?"

    @staticmethod
    def _poly_to_str(coeffs: np.ndarray) -> str:
        """Convert polynomial coefficients [a_n, ..., a_1, a_0] to string."""
        n = len(coeffs) - 1
        terms = []
        for i, c in enumerate(coeffs):
            power = n - i
            if abs(c) < 1e-12:
                continue
            coeff_str = f"{c:.3g}" if (abs(c) != 1.0 or power == 0) else ("" if c > 0 else "-")
            if power == 0:
                coeff_str = f"{c:.3g}"
            var_str = f"s^{power}" if power > 1 else ("s" if power == 1 else "")
            term = f"{coeff_str}{var_str}"
            terms.append(term)
        return " + ".join(terms) if terms else "0"

    # =========================================================================
    # Frequency response computation
    # =========================================================================

    def _compute_poles_zeros(self) -> None:
        """Compute poles and zeros from polynomial coefficients."""
        self._zeros = np.roots(self._num_coeffs) if len(self._num_coeffs) > 1 else np.array([])
        self._poles = np.roots(self._den_coeffs) if len(self._den_coeffs) > 1 else np.array([])

    def _compute_frequency_response(self) -> None:
        """Evaluate H(jω) across the frequency range."""
        freq_min = float(self.parameters["freq_min_exp"])
        freq_max = float(self.parameters["freq_max_exp"])
        self._omega = np.logspace(freq_min, freq_max, self.FREQ_POINTS)

        s = 1j * self._omega
        num_val = np.polyval(self._num_coeffs, s)
        den_val = np.polyval(self._den_coeffs, s)

        # Avoid division by zero
        den_val = np.where(np.abs(den_val) < 1e-30, 1e-30, den_val)
        self._H = num_val / den_val

        magnitude = np.abs(self._H)
        magnitude = np.clip(magnitude, 1e-30, None)  # Avoid log(0)
        self._magnitude_db = 20.0 * np.log10(magnitude)
        self._phase_deg = np.unwrap(np.angle(self._H)) * 180.0 / np.pi

    def _compute_stability_margins(self) -> None:
        """Compute gain margin, phase margin, and stability status."""
        mag_db = self._magnitude_db
        phase = self._phase_deg
        omega = self._omega

        # Find gain crossover frequency (where |H| crosses 0 dB)
        gain_crossover_freq = None
        phase_at_gc = None
        gc_indices = np.where(np.diff(np.sign(mag_db)))[0]
        if len(gc_indices) > 0:
            idx = gc_indices[0]
            # Linear interpolation
            frac = -mag_db[idx] / (mag_db[idx + 1] - mag_db[idx]) if mag_db[idx + 1] != mag_db[idx] else 0
            gain_crossover_freq = omega[idx] * (omega[idx + 1] / omega[idx]) ** frac
            phase_at_gc = phase[idx] + frac * (phase[idx + 1] - phase[idx])

        # Find phase crossover frequency (where phase crosses -180°)
        phase_crossover_freq = None
        mag_at_pc = None
        phase_shifted = phase + 180.0
        pc_indices = np.where(np.diff(np.sign(phase_shifted)))[0]
        if len(pc_indices) > 0:
            idx = pc_indices[0]
            frac = -phase_shifted[idx] / (phase_shifted[idx + 1] - phase_shifted[idx]) if phase_shifted[idx + 1] != phase_shifted[idx] else 0
            phase_crossover_freq = omega[idx] * (omega[idx + 1] / omega[idx]) ** frac
            mag_at_pc = mag_db[idx] + frac * (mag_db[idx + 1] - mag_db[idx])

        # Compute margins
        gain_margin_db = None
        phase_margin_deg = None

        if mag_at_pc is not None:
            gain_margin_db = float(-mag_at_pc)

        if phase_at_gc is not None:
            phase_margin_deg = float(180.0 + phase_at_gc)

        # Determine stability
        if gain_margin_db is not None and phase_margin_deg is not None:
            if gain_margin_db > 1.0 and phase_margin_deg > 1.0:
                status = "Stable"
                is_stable = True
            elif abs(gain_margin_db) < 1.0 or abs(phase_margin_deg) < 1.0:
                status = "Marginally Stable"
                is_stable = False
            else:
                status = "Unstable"
                is_stable = False
        elif gain_margin_db is None and phase_margin_deg is None:
            # No crossovers — check if all poles are in LHP
            if len(self._poles) > 0 and np.all(np.real(self._poles) < 0):
                status = "Stable"
                is_stable = True
            else:
                status = "Unstable"
                is_stable = False
        else:
            # One margin exists, one doesn't — partial info
            if gain_margin_db is not None:
                is_stable = gain_margin_db > 0
            elif phase_margin_deg is not None:
                is_stable = phase_margin_deg > 0
            else:
                is_stable = False
            status = "Stable" if is_stable else "Unstable"

        self._stability_info = {
            "gain_margin_db": round(gain_margin_db, 2) if gain_margin_db is not None else None,
            "phase_margin_deg": round(phase_margin_deg, 2) if phase_margin_deg is not None else None,
            "gain_crossover_freq": round(float(gain_crossover_freq), 4) if gain_crossover_freq is not None else None,
            "phase_crossover_freq": round(float(phase_crossover_freq), 4) if phase_crossover_freq is not None else None,
            "is_stable": is_stable,
            "stability_status": status,
        }

    # =========================================================================
    # Plot generation
    # =========================================================================

    def get_plots(self) -> List[Dict[str, Any]]:
        """Generate all Plotly plot dicts."""
        if not self._initialized:
            self.initialize()
        return [
            self._create_bode_magnitude_plot(),
            self._create_bode_phase_plot(),
            self._create_nyquist_plot(),
            self._create_pole_zero_plot(),
        ]

    def get_state(self) -> Dict[str, Any]:
        """Return state with metadata for frontend sync highlighting."""
        if not self._initialized:
            self.initialize()

        base_state = super().get_state()

        # Subsample arrays for metadata to keep payload manageable
        step = max(1, len(self._omega) // 500)
        omega_sub = self._omega[::step]
        mag_sub = self._magnitude_db[::step]
        phase_sub = self._phase_deg[::step]
        real_sub = np.real(self._H[::step])
        imag_sub = np.imag(self._H[::step])

        # Clip nyquist values for frontend display
        nyq_mag = np.abs(self._H[::step])
        clip_mask = nyq_mag < self.NYQUIST_MAG_CLIP
        real_clipped = np.where(clip_mask, real_sub, np.nan)
        imag_clipped = np.where(clip_mask, imag_sub, np.nan)

        # Format poles/zeros for JSON
        poles_list = []
        for p in self._poles:
            poles_list.append([float(np.real(p)), float(np.imag(p))])
        zeros_list = []
        for z in self._zeros:
            zeros_list.append([float(np.real(z)), float(np.imag(z))])

        base_state["metadata"] = {
            "simulation_type": "nyquist_bode_comparison",
            "hub_slots": self.HUB_SLOTS,
            "hub_domain": self.HUB_DOMAIN,
            "hub_dimensions": self.HUB_DIMENSIONS,
            "has_custom_viewer": True,
            "sticky_controls": True,
            # Raw arrays for frontend synchronized highlighting
            "omega": omega_sub.tolist(),
            "magnitude_db": mag_sub.tolist(),
            "phase_deg": phase_sub.tolist(),
            "nyquist_real": real_clipped.tolist(),
            "nyquist_imag": imag_clipped.tolist(),
            # Stability analysis
            "stability_info": self._stability_info,
            # Display info
            "tf_expression": self._tf_expression,
            "poles": poles_list,
            "zeros": zeros_list,
            "preset_name": self.parameters["preset"],
        }
        return base_state

    def _create_bode_magnitude_plot(self) -> Dict[str, Any]:
        """Bode magnitude plot: |H(jω)| in dB vs log frequency."""
        omega = self._omega
        mag_db = self._magnitude_db
        si = self._stability_info

        # Auto-adjust y-axis
        mag_max = float(np.nanmax(mag_db))
        mag_min = float(np.nanmin(mag_db))
        ylim = [max(-80, mag_min - 5), min(60, mag_max + 10)]

        traces = [
            # Main magnitude response
            {
                "x": omega.tolist(),
                "y": mag_db.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": "|H(jω)|",
                "line": {"color": self.RESPONSE_COLOR, "width": 2.5},
                "hovertemplate": "ω = %{x:.3g} rad/s<br>|H| = %{y:.2f} dB<extra></extra>",
            },
            # 0 dB reference
            {
                "x": [omega[0], omega[-1]],
                "y": [0, 0],
                "type": "scatter",
                "mode": "lines",
                "name": "0 dB",
                "line": {"color": "rgba(148, 163, 184, 0.4)", "width": 1.5, "dash": "dot"},
                "showlegend": False,
            },
        ]

        # Gain crossover marker
        if si.get("gain_crossover_freq") is not None:
            gc_freq = si["gain_crossover_freq"]
            traces.append({
                "x": [gc_freq],
                "y": [0],
                "type": "scatter",
                "mode": "markers",
                "name": f"Gain Crossover (ω={gc_freq:.2g})",
                "marker": {"color": self.CROSSOVER_COLOR, "size": 10, "symbol": "diamond"},
            })

        # Phase crossover: show |H| at phase crossover freq
        if si.get("phase_crossover_freq") is not None and si.get("gain_margin_db") is not None:
            pc_freq = si["phase_crossover_freq"]
            mag_at_pc = -si["gain_margin_db"]  # GM = -mag_at_pc in dB
            traces.append({
                "x": [pc_freq, pc_freq],
                "y": [mag_at_pc, 0],
                "type": "scatter",
                "mode": "lines+markers",
                "name": f"GM = {si['gain_margin_db']:.1f} dB",
                "line": {"color": self.STABLE_COLOR, "width": 2, "dash": "dash"},
                "marker": {"color": self.STABLE_COLOR, "size": 8},
            })

        return {
            "id": "bode_magnitude",
            "title": "Bode Magnitude",
            "data": traces,
            "layout": self._bode_layout("Magnitude (dB)", ylim, "bode_mag"),
        }

    def _create_bode_phase_plot(self) -> Dict[str, Any]:
        """Bode phase plot: ∠H(jω) in degrees vs log frequency."""
        omega = self._omega
        phase = self._phase_deg
        si = self._stability_info

        # Auto-adjust y-axis
        phase_min = float(np.nanmin(phase))
        phase_max = float(np.nanmax(phase))
        ylim = [min(-200, phase_min - 10), max(10, phase_max + 10)]

        traces = [
            # Phase response
            {
                "x": omega.tolist(),
                "y": phase.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": "∠H(jω)",
                "line": {"color": self.RESPONSE_COLOR, "width": 2.5},
                "hovertemplate": "ω = %{x:.3g} rad/s<br>∠H = %{y:.1f}°<extra></extra>",
            },
            # -180° reference
            {
                "x": [omega[0], omega[-1]],
                "y": [-180, -180],
                "type": "scatter",
                "mode": "lines",
                "name": "-180°",
                "line": {"color": "rgba(148, 163, 184, 0.4)", "width": 1.5, "dash": "dot"},
                "showlegend": False,
            },
        ]

        # Phase crossover marker
        if si.get("phase_crossover_freq") is not None:
            pc_freq = si["phase_crossover_freq"]
            traces.append({
                "x": [pc_freq],
                "y": [-180],
                "type": "scatter",
                "mode": "markers",
                "name": f"Phase Crossover (ω={pc_freq:.2g})",
                "marker": {"color": self.CROSSOVER_COLOR, "size": 10, "symbol": "diamond"},
            })

        # Gain crossover: show phase margin
        if si.get("gain_crossover_freq") is not None and si.get("phase_margin_deg") is not None:
            gc_freq = si["gain_crossover_freq"]
            phase_at_gc = -180 + si["phase_margin_deg"]
            traces.append({
                "x": [gc_freq, gc_freq],
                "y": [-180, phase_at_gc],
                "type": "scatter",
                "mode": "lines+markers",
                "name": f"PM = {si['phase_margin_deg']:.1f}°",
                "line": {"color": self.STABLE_COLOR, "width": 2, "dash": "dash"},
                "marker": {"color": self.STABLE_COLOR, "size": 8},
            })

        return {
            "id": "bode_phase",
            "title": "Bode Phase",
            "data": traces,
            "layout": self._bode_layout("Phase (degrees)", ylim, "bode_phase"),
        }

    def _bode_layout(self, ytitle: str, yrange: List[float], uirev: str) -> Dict[str, Any]:
        """Common Bode plot layout."""
        omega = self._omega
        return {
            "xaxis": {
                "title": "Frequency (rad/s)",
                "type": "log",
                "showgrid": True,
                "gridcolor": "rgba(148, 163, 184, 0.15)",
                "range": [np.log10(omega[0]), np.log10(omega[-1])],
                "fixedrange": False,
            },
            "yaxis": {
                "title": ytitle,
                "showgrid": True,
                "gridcolor": "rgba(148, 163, 184, 0.15)",
                "zeroline": True,
                "zerolinecolor": "rgba(148, 163, 184, 0.3)",
                "range": yrange,
                "fixedrange": False,
            },
            "legend": {
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "left",
                "x": 0,
                "font": {"size": 11},
            },
            "margin": {"l": 60, "r": 25, "t": 45, "b": 55},
            "plot_bgcolor": "rgba(0,0,0,0)",
            "paper_bgcolor": "rgba(0,0,0,0)",
            "uirevision": uirev,
        }

    def _create_nyquist_plot(self) -> Dict[str, Any]:
        """Nyquist plot: Im(H(jω)) vs Re(H(jω)) with both freq branches."""
        H = self._H
        real_part = np.real(H)
        imag_part = np.imag(H)
        mag = np.abs(H)

        # Clip extreme values for display
        clip_mask = mag < self.NYQUIST_MAG_CLIP
        real_clipped = np.where(clip_mask, real_part, np.nan).tolist()
        imag_clipped = np.where(clip_mask, imag_part, np.nan).tolist()
        imag_neg = np.where(clip_mask, -imag_part, np.nan).tolist()  # Negative freq branch

        traces = [
            # Positive frequency branch (solid)
            {
                "x": real_clipped,
                "y": imag_clipped,
                "type": "scatter",
                "mode": "lines",
                "name": "H(jω), ω > 0",
                "line": {"color": self.RESPONSE_COLOR, "width": 2.5},
                "hovertemplate": "Re = %{x:.3g}<br>Im = %{y:.3g}<extra>ω > 0</extra>",
            },
            # Negative frequency branch (dashed)
            {
                "x": real_clipped,
                "y": imag_neg,
                "type": "scatter",
                "mode": "lines",
                "name": "H(jω), ω < 0",
                "line": {"color": self.RESPONSE_COLOR_DIM, "width": 2, "dash": "dash"},
                "hovertemplate": "Re = %{x:.3g}<br>Im = %{y:.3g}<extra>ω < 0</extra>",
            },
            # Critical point (-1, 0)
            {
                "x": [-1],
                "y": [0],
                "type": "scatter",
                "mode": "markers+text",
                "name": "Critical Point (-1, 0)",
                "marker": {"color": self.CRITICAL_POINT_COLOR, "size": 12, "symbol": "x",
                           "line": {"width": 3, "color": self.CRITICAL_POINT_COLOR}},
                "text": ["(-1, 0)"],
                "textposition": "top right",
                "textfont": {"color": self.CRITICAL_POINT_COLOR, "size": 11},
            },
        ]

        # Unit circle for reference
        theta = np.linspace(0, 2 * np.pi, 100)
        traces.append({
            "x": np.cos(theta).tolist(),
            "y": np.sin(theta).tolist(),
            "type": "scatter",
            "mode": "lines",
            "name": "Unit Circle",
            "line": {"color": self.UNIT_CIRCLE_COLOR, "width": 1, "dash": "dot"},
            "opacity": 0.5,
            "hoverinfo": "skip",
        })

        # Direction arrows along positive branch
        valid_indices = np.where(clip_mask)[0]
        if len(valid_indices) > 10:
            arrow_indices = valid_indices[np.linspace(0, len(valid_indices) - 1, 6, dtype=int)[1:-1]]
            traces.append({
                "x": [real_part[i] for i in arrow_indices],
                "y": [imag_part[i] for i in arrow_indices],
                "type": "scatter",
                "mode": "markers",
                "name": "ω direction",
                "marker": {
                    "symbol": "triangle-right",
                    "size": 8,
                    "color": self.RESPONSE_COLOR,
                    "angle": [
                        float(np.degrees(np.arctan2(
                            imag_part[min(i + 5, len(imag_part) - 1)] - imag_part[max(i - 5, 0)],
                            real_part[min(i + 5, len(real_part) - 1)] - real_part[max(i - 5, 0)]
                        ))) for i in arrow_indices
                    ],
                },
                "showlegend": False,
                "hoverinfo": "skip",
            })

        # Auto-scale axes
        valid_real = real_part[clip_mask]
        valid_imag = imag_part[clip_mask]
        if len(valid_real) > 0:
            pad = 0.15
            rx = max(abs(valid_real.min()), abs(valid_real.max()), 1.5)
            ry = max(abs(valid_imag.min()), abs(valid_imag.max()), 1.5)
            r = max(rx, ry) * (1 + pad)
            x_range = [min(-1.5, -r), max(1.5, r)]
            y_range = [-r, r]
        else:
            x_range = [-3, 3]
            y_range = [-3, 3]

        return {
            "id": "nyquist",
            "title": "Nyquist Plot",
            "data": traces,
            "layout": {
                "xaxis": {
                    "title": "Re{H(jω)}",
                    "showgrid": True,
                    "gridcolor": "rgba(148, 163, 184, 0.15)",
                    "zeroline": True,
                    "zerolinecolor": "rgba(148, 163, 184, 0.3)",
                    "range": x_range,
                    "fixedrange": False,
                    "scaleanchor": "y",
                    "scaleratio": 1,
                },
                "yaxis": {
                    "title": "Im{H(jω)}",
                    "showgrid": True,
                    "gridcolor": "rgba(148, 163, 184, 0.15)",
                    "zeroline": True,
                    "zerolinecolor": "rgba(148, 163, 184, 0.3)",
                    "range": y_range,
                    "fixedrange": False,
                },
                "legend": {
                    "orientation": "h",
                    "yanchor": "bottom",
                    "y": 1.02,
                    "xanchor": "left",
                    "x": 0,
                    "font": {"size": 11},
                },
                "margin": {"l": 60, "r": 25, "t": 45, "b": 55},
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)",
                "uirevision": "nyquist",
            },
        }

    def _create_pole_zero_plot(self) -> Dict[str, Any]:
        """S-plane pole-zero map."""
        traces = []

        # Determine axis range from poles and zeros
        all_points = np.concatenate([self._poles, self._zeros]) if len(self._zeros) > 0 else self._poles
        if len(all_points) > 0:
            max_extent = max(np.max(np.abs(np.real(all_points))),
                            np.max(np.abs(np.imag(all_points))), 1.0)
            r = max_extent * 1.4
        else:
            r = 2.0
        xlim = [-r, r * 0.3]
        ylim = [-r, r]

        # Stable region shading
        traces.append({
            "x": [xlim[0], 0, 0, xlim[0], xlim[0]],
            "y": [ylim[0], ylim[0], ylim[1], ylim[1], ylim[0]],
            "type": "scatter",
            "mode": "lines",
            "fill": "toself",
            "fillcolor": "rgba(52, 211, 153, 0.08)",
            "line": {"color": "rgba(52, 211, 153, 0.4)", "width": 1},
            "name": "Stable Region",
            "showlegend": True,
            "hoverinfo": "skip",
        })

        # jω axis
        traces.append({
            "x": [0, 0],
            "y": [ylim[0], ylim[1]],
            "type": "scatter",
            "mode": "lines",
            "line": {"color": self.IMAGINARY_AXIS_COLOR, "width": 2, "dash": "solid"},
            "name": "jω axis",
            "showlegend": True,
            "hoverinfo": "name",
        })

        # Plot zeros
        if len(self._zeros) > 0:
            traces.append({
                "x": [float(np.real(z)) for z in self._zeros],
                "y": [float(np.imag(z)) for z in self._zeros],
                "type": "scatter",
                "mode": "markers",
                "name": "Zeros",
                "marker": {
                    "symbol": "circle-open",
                    "size": 14,
                    "color": self.ZERO_COLOR,
                    "line": {"width": 3, "color": self.ZERO_COLOR},
                },
                "hovertemplate": "Zero<br>σ = %{x:.3f}<br>ω = %{y:.3f}j<extra></extra>",
            })

        # Plot poles
        if len(self._poles) > 0:
            traces.append({
                "x": [float(np.real(p)) for p in self._poles],
                "y": [float(np.imag(p)) for p in self._poles],
                "type": "scatter",
                "mode": "markers",
                "name": "Poles",
                "marker": {
                    "symbol": "x",
                    "size": 14,
                    "color": self.POLE_COLOR,
                    "line": {"width": 3, "color": self.POLE_COLOR},
                },
                "hovertemplate": "Pole<br>σ = %{x:.3f}<br>ω = %{y:.3f}j<extra></extra>",
            })

        return {
            "id": "pole_zero",
            "title": "Pole-Zero Map (S-Plane)",
            "data": traces,
            "layout": {
                "xaxis": {
                    "title": "Real (σ)",
                    "showgrid": True,
                    "gridcolor": "rgba(148, 163, 184, 0.15)",
                    "zeroline": True,
                    "zerolinecolor": "rgba(148, 163, 184, 0.3)",
                    "range": xlim,
                    "fixedrange": False,
                },
                "yaxis": {
                    "title": "Imaginary (jω)",
                    "showgrid": True,
                    "gridcolor": "rgba(148, 163, 184, 0.15)",
                    "zeroline": True,
                    "zerolinecolor": "rgba(148, 163, 184, 0.3)",
                    "range": ylim,
                    "scaleanchor": "x",
                    "scaleratio": 1,
                    "fixedrange": False,
                },
                "legend": {
                    "orientation": "h",
                    "yanchor": "bottom",
                    "y": 1.02,
                    "xanchor": "left",
                    "x": 0,
                    "font": {"size": 11},
                },
                "margin": {"l": 60, "r": 25, "t": 45, "b": 55},
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)",
                "uirevision": "pole_zero",
            },
        }
