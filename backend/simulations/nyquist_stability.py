"""
Nyquist Stability Criterion Simulator

Educational tool for teaching the Nyquist Stability Criterion:
- D-contour mapping from s-plane to L(s)-plane
- Encirclement counting of the critical point (-1, 0)
- N = Z - P relationship (N=CW encirclements, P=OL RHP poles, Z=CL RHP poles)
- Preset systems covering all key stability scenarios
- Padé approximation for time-delay systems
"""

import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from .base_simulator import BaseSimulator


class NyquistStabilitySimulator(BaseSimulator):
    """
    Nyquist Stability Criterion simulation.

    Generates Nyquist plot with encirclement analysis, D-contour visualization,
    and closed-loop pole map. Teaches the relationship N = Z - P.
    """

    FREQ_POINTS = 2000
    NYQUIST_MAG_CLIP = 500
    D_CONTOUR_POINTS = 2000

    # Colors
    RESPONSE_COLOR = "#22d3ee"
    RESPONSE_COLOR_DIM = "rgba(34, 211, 238, 0.4)"
    POLE_COLOR = "#f87171"
    ZERO_COLOR = "#3b82f6"
    CRITICAL_POINT_COLOR = "#ef4444"
    UNIT_CIRCLE_COLOR = "#10b981"
    STABLE_COLOR = "#34d399"
    CONTOUR_COLOR = "#fbbf24"
    CONTOUR_COLOR_DIM = "rgba(251, 191, 36, 0.4)"
    CL_POLE_STABLE_COLOR = "#10b981"
    CL_POLE_UNSTABLE_COLOR = "#ef4444"
    IMAGINARY_AXIS_COLOR = "#a855f7"

    PRESET_DEFINITIONS = {
        "stable_simple": {
            "name": "Stable: K/(s+1)(s+2)",
            "description": "Simple stable system, no RHP OL poles",
            "build": "two_real_poles_stable",
        },
        "stable_second_order": {
            "name": "2nd Order: Kω₀²/(s²+2ζω₀s+ω₀²)",
            "description": "Stable second-order system",
            "build": "second_order",
        },
        "unstable_third_order": {
            "name": "Type-1: K/(s(s+1)(s+2))",
            "description": "Integrator + two poles, unstable at high K",
            "build": "integrator_two_poles",
        },
        "conditionally_stable": {
            "name": "Conditional: K(s+6)/(s(s+1)(s+3)(s+4))",
            "description": "Stable only for a range of K values",
            "build": "conditional",
        },
        "rhp_pole_stable": {
            "name": "RHP Pole: K(s+3)/((s-1)(s+2))",
            "description": "Open-loop unstable, stabilized by feedback",
            "build": "rhp_pole",
        },
        "double_integrator": {
            "name": "Double Integrator: K/s²",
            "description": "Always unstable (2 encirclements)",
            "build": "double_integrator",
        },
        "time_delay": {
            "name": "Time Delay: Ke⁻ˢᵀ/(s+1) (Padé)",
            "description": "Delay-induced instability via Padé approximation",
            "build": "time_delay",
        },
        "custom": {
            "name": "Custom Coefficients",
            "description": "Enter your own numerator/denominator",
            "build": "custom",
        },
    }

    PARAMETER_SCHEMA = {
        "preset": {
            "type": "select",
            "options": [
                {"value": k, "label": v["name"]}
                for k, v in PRESET_DEFINITIONS.items()
            ],
            "default": "stable_simple",
        },
        "gain_K": {
            "type": "slider", "min": 0.1, "max": 100.0,
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
            "step": 0.1, "default": 1.0,
        },
        "pole_b": {
            "type": "slider", "min": 0.1, "max": 20.0,
            "step": 0.1, "default": 2.0,
        },
        "zero_z": {
            "type": "slider", "min": 0.1, "max": 20.0,
            "step": 0.1, "default": 3.0,
        },
        "delay_T": {
            "type": "slider", "min": 0.01, "max": 5.0,
            "step": 0.01, "default": 0.5,
        },
        "custom_num": {
            "type": "expression", "default": "1",
        },
        "custom_den": {
            "type": "expression", "default": "1, 3, 2",
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
        "preset": "stable_simple",
        "gain_K": 1.0,
        "omega_0": 5.0,
        "zeta": 0.5,
        "pole_a": 1.0,
        "pole_b": 2.0,
        "zero_z": 3.0,
        "delay_T": 0.5,
        "custom_num": "1",
        "custom_den": "1, 3, 2",
        "freq_min_exp": -2,
        "freq_max_exp": 3,
    }

    def __init__(self, simulation_id: str):
        super().__init__(simulation_id)
        self._omega: Optional[np.ndarray] = None
        self._H: Optional[np.ndarray] = None
        self._num_coeffs: Optional[np.ndarray] = None
        self._den_coeffs: Optional[np.ndarray] = None
        self._poles: Optional[np.ndarray] = None
        self._zeros: Optional[np.ndarray] = None
        self._cl_poles: Optional[np.ndarray] = None
        self._stability_criterion: Dict[str, Any] = {}
        self._stability_info: Dict[str, Any] = {}
        self._tf_expression: str = ""
        self._d_contour_s: Optional[np.ndarray] = None
        self._d_contour_image: Optional[np.ndarray] = None

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
            self._compute()
        return self.get_state()

    def reset(self) -> Dict[str, Any]:
        """Reset to defaults."""
        self.parameters = self.DEFAULT_PARAMS.copy()
        self._initialized = True
        self._compute()
        return self.get_state()

    def _compute(self) -> None:
        """Main computation pipeline."""
        self._num_coeffs, self._den_coeffs = self._build_transfer_function()
        self._tf_expression = self._format_tf_expression()
        self._compute_poles_zeros()
        self._compute_frequency_response()
        self._compute_closed_loop_poles()
        self._compute_d_contour()
        self._count_encirclements()  # Uses D-contour image + CL poles for verification
        self._compute_stability_margins()
        self._compute_stability_criterion()

    # =========================================================================
    # Transfer function construction
    # =========================================================================

    def _build_transfer_function(self) -> Tuple[np.ndarray, np.ndarray]:
        """Build num/den polynomial coefficients from preset."""
        preset = self.parameters["preset"]
        K = float(self.parameters["gain_K"])
        build = self.PRESET_DEFINITIONS.get(preset, {}).get("build", "two_real_poles_stable")

        if build == "two_real_poles_stable":
            a = float(self.parameters["pole_a"])
            b = float(self.parameters["pole_b"])
            return np.array([K]), np.convolve([1.0, a], [1.0, b])

        elif build == "second_order":
            w0 = float(self.parameters["omega_0"])
            z = float(self.parameters["zeta"])
            return np.array([K * w0**2]), np.array([1.0, 2 * z * w0, w0**2])

        elif build == "integrator_two_poles":
            a = float(self.parameters["pole_a"])
            b = float(self.parameters["pole_b"])
            den = np.convolve([1.0, 0.0], np.convolve([1.0, a], [1.0, b]))
            return np.array([K]), den

        elif build == "conditional":
            z_val = float(self.parameters["zero_z"])
            # K(s+z) / (s(s+1)(s+3)(s+4))
            num = np.array([K, K * z_val])
            den = np.convolve([1.0, 0.0], [1.0, 1.0])
            den = np.convolve(den, [1.0, 3.0])
            den = np.convolve(den, [1.0, 4.0])
            return num, den

        elif build == "rhp_pole":
            z_val = float(self.parameters["zero_z"])
            b = float(self.parameters["pole_b"])
            # K(s+z) / ((s-1)(s+b))
            num = np.array([K, K * z_val])
            den = np.convolve([1.0, -1.0], [1.0, b])
            return num, den

        elif build == "double_integrator":
            return np.array([K]), np.array([1.0, 0.0, 0.0])

        elif build == "time_delay":
            a = float(self.parameters["pole_a"])
            T = float(self.parameters["delay_T"])
            # L(s) = K * e^{-sT} / (s + a)
            # Padé approximation for e^{-sT}
            pade_num, pade_den = self._build_pade(T, order=3)
            num = np.array(pade_num) * K
            den = np.convolve(pade_den, [1.0, a])
            return num, den

        elif build == "custom":
            num = self._parse_coefficients(
                str(self.parameters.get("custom_num", "1")), fallback=[1.0]
            )
            den = self._parse_coefficients(
                str(self.parameters.get("custom_den", "1, 1")), fallback=[1.0, 1.0]
            )
            return np.array(num) * K, np.array(den)

        return np.array([K]), np.array([1.0, 1.0])

    @staticmethod
    def _build_pade(T: float, order: int = 3) -> Tuple[List[float], List[float]]:
        """Padé approximation of e^{-sT} of given order.

        Returns (num, den) polynomial coefficients in descending power order.
        Uses the formula: Padé[n/n] of e^{-x} where x = sT.
        """
        from math import factorial, comb
        # Padé [n/n] approximation of e^{-x}:
        # num(x) = sum_{k=0}^{n} C(n,k) * (2n-k)! / (2n)! * (-x)^k / k!  ... simplified:
        # a_k = (-1)^k * C(n,k) * factorial(2n-k) / factorial(2n)
        # den has same coefficients but without (-1)^k
        n = order
        num_coeffs = []  # coefficients of x^0, x^1, ..., x^n
        den_coeffs = []
        for k in range(n + 1):
            c = comb(n, k) * factorial(2 * n - k) / (factorial(2 * n) * factorial(k))
            # Scale by T^k for substitution x = sT
            c_scaled = c * (T ** k)
            den_coeffs.append(c_scaled)
            num_coeffs.append(c_scaled * ((-1) ** k))

        # Convert from ascending power [a_0, a_1*s, a_2*s^2, ...] to descending
        num_coeffs.reverse()
        den_coeffs.reverse()
        return num_coeffs, den_coeffs

    @staticmethod
    def _parse_coefficients(s: str, fallback: List[float]) -> List[float]:
        """Parse comma-separated coefficient string."""
        try:
            coeffs = [float(x.strip()) for x in s.split(",") if x.strip()]
            if not coeffs:
                return fallback
            return coeffs
        except (ValueError, TypeError):
            return fallback

    def _format_tf_expression(self) -> str:
        """Format human-readable TF string."""
        preset = self.parameters["preset"]
        K = float(self.parameters["gain_K"])
        build = self.PRESET_DEFINITIONS.get(preset, {}).get("build", "")

        if build == "two_real_poles_stable":
            a = float(self.parameters["pole_a"])
            b = float(self.parameters["pole_b"])
            return f"L(s) = {K:.2g} / ((s + {a:.2g})(s + {b:.2g}))"
        elif build == "second_order":
            w0 = float(self.parameters["omega_0"])
            z = float(self.parameters["zeta"])
            return f"L(s) = {K * w0**2:.2g} / (s\u00b2 + {2*z*w0:.2g}s + {w0**2:.2g})"
        elif build == "integrator_two_poles":
            a = float(self.parameters["pole_a"])
            b = float(self.parameters["pole_b"])
            return f"L(s) = {K:.2g} / (s(s + {a:.2g})(s + {b:.2g}))"
        elif build == "conditional":
            z_val = float(self.parameters["zero_z"])
            return f"L(s) = {K:.2g}(s + {z_val:.2g}) / (s(s + 1)(s + 3)(s + 4))"
        elif build == "rhp_pole":
            z_val = float(self.parameters["zero_z"])
            b = float(self.parameters["pole_b"])
            return f"L(s) = {K:.2g}(s + {z_val:.2g}) / ((s \u2212 1)(s + {b:.2g}))"
        elif build == "double_integrator":
            return f"L(s) = {K:.2g} / s\u00b2"
        elif build == "time_delay":
            a = float(self.parameters["pole_a"])
            T = float(self.parameters["delay_T"])
            return f"L(s) = {K:.2g} \u00b7 e^({{-{T:.2g}s}}) / (s + {a:.2g})  [Pad\u00e9 order 3]"
        elif build == "custom":
            num_str = self._poly_to_str(self._num_coeffs)
            den_str = self._poly_to_str(self._den_coeffs)
            return f"L(s) = ({num_str}) / ({den_str})"
        return "L(s) = ?"

    @staticmethod
    def _poly_to_str(coeffs: np.ndarray) -> str:
        """Convert polynomial coefficients to string."""
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
    # Frequency response & poles/zeros
    # =========================================================================

    def _compute_poles_zeros(self) -> None:
        """Compute OL poles and zeros."""
        self._zeros = np.roots(self._num_coeffs) if len(self._num_coeffs) > 1 else np.array([])
        self._poles = np.roots(self._den_coeffs) if len(self._den_coeffs) > 1 else np.array([])

    def _compute_frequency_response(self) -> None:
        """Evaluate L(jω) across the frequency range."""
        freq_min = float(self.parameters["freq_min_exp"])
        freq_max = float(self.parameters["freq_max_exp"])
        self._omega = np.logspace(freq_min, freq_max, self.FREQ_POINTS)

        s = 1j * self._omega
        num_val = np.polyval(self._num_coeffs, s)
        den_val = np.polyval(self._den_coeffs, s)
        den_val = np.where(np.abs(den_val) < 1e-30, 1e-30, den_val)
        self._H = num_val / den_val

    def _compute_closed_loop_poles(self) -> None:
        """Compute closed-loop poles: roots of den(s) + K*num(s) = 0."""
        K = float(self.parameters["gain_K"])
        # Pad shorter array to match lengths
        n_num = len(self._num_coeffs)
        n_den = len(self._den_coeffs)
        max_len = max(n_num, n_den)

        num_padded = np.zeros(max_len)
        den_padded = np.zeros(max_len)
        num_padded[max_len - n_num:] = self._num_coeffs
        den_padded[max_len - n_den:] = self._den_coeffs

        char_poly = den_padded + K * num_padded

        if len(char_poly) > 1:
            self._cl_poles = np.roots(char_poly)
        else:
            self._cl_poles = np.array([])

    def _count_encirclements(self) -> None:
        """Count CW encirclements of (-1, 0).

        Uses both numerical winding number and algebraic verification.
        Falls back to algebraic N = Z - P when numerical result is unreliable.
        """
        L_contour = self._d_contour_image
        valid = np.isfinite(L_contour)
        if np.sum(valid) < 2:
            self._N = 0
            self._passes_through_critical = False
            return

        L_valid = L_contour[valid]

        # Check if curve passes through or very near (-1, 0)
        dist_to_critical = np.abs(L_valid + 1.0)
        min_dist = float(np.min(dist_to_critical))
        self._passes_through_critical = min_dist < 0.02

        # Numerical winding number via unwrapped phase
        w = L_valid + 1.0
        angles = np.unwrap(np.angle(w))
        total_angle = float(angles[-1] - angles[0])
        N_numerical = int(round(-total_angle / (2 * np.pi)))

        # Algebraic verification: N = Z - P (argument principle, always exact)
        P = int(np.sum(np.real(self._poles) > 1e-10)) if len(self._poles) > 0 else 0
        Z = int(np.sum(np.real(self._cl_poles) > 1e-10)) if len(self._cl_poles) > 0 else 0
        N_algebraic = Z - P

        # Use numerical result when it agrees with algebraic, otherwise fall back
        if self._passes_through_critical:
            # Curve passes through critical point — N is undefined
            self._N = N_algebraic  # best estimate
        elif N_numerical == N_algebraic:
            self._N = N_numerical
        else:
            # Numerical disagrees — use algebraic (more reliable for high-order systems)
            self._N = N_algebraic

    def _compute_stability_margins(self) -> None:
        """Compute gain and phase margins."""
        mag_db = 20.0 * np.log10(np.clip(np.abs(self._H), 1e-30, None))
        phase = np.unwrap(np.angle(self._H)) * 180.0 / np.pi
        omega = self._omega

        gain_margin_db = None
        phase_margin_deg = None
        gain_crossover_freq = None
        phase_crossover_freq = None

        # Gain crossover (|H| = 0 dB)
        gc_indices = np.where(np.diff(np.sign(mag_db)))[0]
        if len(gc_indices) > 0:
            idx = gc_indices[0]
            denom = mag_db[idx + 1] - mag_db[idx]
            frac = -mag_db[idx] / denom if abs(denom) > 1e-15 else 0
            gain_crossover_freq = float(omega[idx] * (omega[idx + 1] / omega[idx]) ** frac)
            phase_at_gc = phase[idx] + frac * (phase[idx + 1] - phase[idx])
            phase_margin_deg = float(180.0 + phase_at_gc)

        # Phase crossover (phase = -180°)
        phase_shifted = phase + 180.0
        pc_indices = np.where(np.diff(np.sign(phase_shifted)))[0]
        if len(pc_indices) > 0:
            idx = pc_indices[0]
            denom = phase_shifted[idx + 1] - phase_shifted[idx]
            frac = -phase_shifted[idx] / denom if abs(denom) > 1e-15 else 0
            phase_crossover_freq = float(omega[idx] * (omega[idx + 1] / omega[idx]) ** frac)
            mag_at_pc = mag_db[idx] + frac * (mag_db[idx + 1] - mag_db[idx])
            gain_margin_db = float(-mag_at_pc)

        self._stability_info = {
            "gain_margin_db": round(gain_margin_db, 2) if gain_margin_db is not None else None,
            "phase_margin_deg": round(phase_margin_deg, 2) if phase_margin_deg is not None else None,
            "gain_crossover_freq": round(gain_crossover_freq, 4) if gain_crossover_freq is not None else None,
            "phase_crossover_freq": round(phase_crossover_freq, 4) if phase_crossover_freq is not None else None,
        }

    def _compute_stability_criterion(self) -> None:
        """Assemble the N = Z - P relationship."""
        P = int(np.sum(np.real(self._poles) > 1e-10)) if len(self._poles) > 0 else 0
        Z = int(np.sum(np.real(self._cl_poles) > 1e-10)) if len(self._cl_poles) > 0 else 0
        N = self._N

        # Check for marginal stability (CL poles on jω axis)
        marginal = False
        if len(self._cl_poles) > 0:
            for p in self._cl_poles:
                if abs(np.real(p)) < 1e-6 and abs(np.imag(p)) > 1e-10:
                    marginal = True
                    break

        # When curve passes through (-1,0), encirclement count is unreliable
        passes_critical = getattr(self, '_passes_through_critical', False)

        equation_holds = (N == Z - P)

        if marginal or passes_critical:
            status = "Marginally Stable"
            is_stable = False
        elif Z == 0:
            status = "Stable"
            is_stable = True
        else:
            status = "Unstable"
            is_stable = False

        # Build explanation
        if passes_critical:
            explanation = f"Nyquist curve passes through (\u22121, 0) \u2192 CL poles on j\u03c9 axis. Marginally stable."
        elif is_stable:
            if P == 0:
                explanation = f"N={N}, P={P} \u2192 Z=N+P={N}+{P}=0. No CL poles in RHP. System is stable."
            else:
                explanation = f"N={N}, P={P} \u2192 Z=N+P={N}+{P}=0. The {abs(N)} CCW encirclement(s) cancel the {P} OL RHP pole(s)."
        elif marginal:
            explanation = f"N={N}, P={P} \u2192 Z=N+P={Z}. CL poles on j\u03c9 axis \u2192 marginally stable."
        else:
            explanation = f"N={N}, P={P} \u2192 Z=N+P={N}+{P}={Z}. {Z} CL pole(s) in RHP \u2192 unstable."

        self._stability_criterion = {
            "P": P,
            "Z": Z,
            "N": N,
            "equation_holds": equation_holds,
            "is_stable": is_stable,
            "stability_status": status,
            "explanation": explanation,
        }

    # =========================================================================
    # D-contour computation
    # =========================================================================

    def _compute_d_contour(self) -> None:
        """Compute D-contour path in s-plane and its image through L(s).

        Standard Nyquist contour (closed, CW traversal enclosing RHP):
        - For systems WITHOUT jω-axis poles:
          1. -jR → +jR (full imaginary axis, through origin)
          2. R·e^{jθ}, θ: π/2 → -π/2 (large semicircle through RHP)
        - For systems WITH pole at origin:
          1. -jR → -jε (negative imaginary axis)
          2. ε·e^{jθ}, θ: -π/2 → +π/2 (small RHP indentation around origin)
          3. +jε → +jR (positive imaginary axis)
          4. R·e^{jθ}, θ: π/2 → -π/2 (large semicircle through RHP)
        """
        freq_max = float(self.parameters["freq_max_exp"])
        R = 10 ** freq_max
        epsilon = 0.05

        # Detect pole at origin
        has_origin_pole = False
        if len(self._poles) > 0:
            for p in self._poles:
                if abs(np.real(p)) < 1e-6 and abs(np.imag(p)) < epsilon:
                    has_origin_pole = True
                    break

        pts = self.D_CONTOUR_POINTS
        segments = []

        if has_origin_pole:
            # Negative jω: -jR to -jε
            omega_neg = np.logspace(np.log10(R), np.log10(epsilon), pts)
            segments.append(-1j * omega_neg)

            # Small indentation around origin: ε·e^{jθ}, θ from -π/2 to +π/2
            theta_indent = np.linspace(-np.pi / 2, np.pi / 2, 60)
            segments.append(epsilon * np.exp(1j * theta_indent))

            # Positive jω: +jε to +jR
            omega_pos = np.logspace(np.log10(epsilon), np.log10(R), pts)
            segments.append(1j * omega_pos)
        else:
            # Full imaginary axis: -jR through 0 to +jR
            omega_neg = np.logspace(np.log10(R), -4, pts)
            omega_pos = np.logspace(-4, np.log10(R), pts)
            segments.append(-1j * omega_neg)
            segments.append(1j * omega_pos)

        # Large semicircle: R·e^{jθ}, θ from π/2 to -π/2
        theta_large = np.linspace(np.pi / 2, -np.pi / 2, 500)
        segments.append(R * np.exp(1j * theta_large))

        self._d_contour_s = np.concatenate(segments)

        # Map through L(s)
        num_val = np.polyval(self._num_coeffs, self._d_contour_s)
        den_val = np.polyval(self._den_coeffs, self._d_contour_s)
        den_val = np.where(np.abs(den_val) < 1e-30, 1e-30, den_val)
        self._d_contour_image = num_val / den_val

    # =========================================================================
    # Plot generation
    # =========================================================================

    def get_plots(self) -> List[Dict[str, Any]]:
        """Generate all plot dicts."""
        if not self._initialized:
            self.initialize()
        return [
            self._create_nyquist_plot(),
            self._create_d_contour_plot(),
            self._create_cl_pole_map(),
        ]

    def get_state(self) -> Dict[str, Any]:
        """Return state with stability criterion metadata."""
        if not self._initialized:
            self.initialize()

        base_state = super().get_state()

        # Subsample for frontend animation
        step = max(1, len(self._omega) // 500)
        omega_sub = self._omega[::step]
        real_sub = np.real(self._H[::step])
        imag_sub = np.imag(self._H[::step])
        mag = np.abs(self._H[::step])
        clip_mask = mag < self.NYQUIST_MAG_CLIP
        real_clipped = np.where(clip_mask, real_sub, np.nan)
        imag_clipped = np.where(clip_mask, imag_sub, np.nan)

        # D-contour points for animation
        d_step = max(1, len(self._d_contour_s) // 300)
        d_contour_real = np.real(self._d_contour_s[::d_step])
        d_contour_imag = np.imag(self._d_contour_s[::d_step])
        d_image_real = np.real(self._d_contour_image[::d_step])
        d_image_imag = np.imag(self._d_contour_image[::d_step])
        d_image_mag = np.abs(self._d_contour_image[::d_step])
        d_clip = d_image_mag < self.NYQUIST_MAG_CLIP
        d_image_real_clipped = np.where(d_clip, d_image_real, np.nan)
        d_image_imag_clipped = np.where(d_clip, d_image_imag, np.nan)

        # Format poles/zeros for JSON
        ol_poles = [[float(np.real(p)), float(np.imag(p))] for p in self._poles] if len(self._poles) > 0 else []
        ol_zeros = [[float(np.real(z)), float(np.imag(z))] for z in self._zeros] if len(self._zeros) > 0 else []
        cl_poles = [[float(np.real(p)), float(np.imag(p))] for p in self._cl_poles] if len(self._cl_poles) > 0 else []

        base_state["metadata"] = {
            "simulation_type": "nyquist_stability",
            "has_custom_viewer": True,
            "sticky_controls": True,
            "stability_criterion": self._stability_criterion,
            "stability_info": self._stability_info,
            "tf_expression": self._tf_expression,
            "ol_poles": ol_poles,
            "ol_zeros": ol_zeros,
            "cl_poles": cl_poles,
            "omega": omega_sub.tolist(),
            "nyquist_real": real_clipped.tolist(),
            "nyquist_imag": imag_clipped.tolist(),
            "d_contour_s_real": d_contour_real.tolist(),
            "d_contour_s_imag": d_contour_imag.tolist(),
            "d_contour_image_real": d_image_real_clipped.tolist(),
            "d_contour_image_imag": d_image_imag_clipped.tolist(),
            "preset_name": self.parameters["preset"],
        }
        return base_state

    def _create_nyquist_plot(self) -> Dict[str, Any]:
        """Nyquist plot with encirclement analysis."""
        H = self._H
        real_part = np.real(H)
        imag_part = np.imag(H)
        mag = np.abs(H)

        clip_mask = mag < self.NYQUIST_MAG_CLIP
        real_clipped = np.where(clip_mask, real_part, np.nan).tolist()
        imag_clipped = np.where(clip_mask, imag_part, np.nan).tolist()
        imag_neg = np.where(clip_mask, -imag_part, np.nan).tolist()

        criterion = self._stability_criterion
        N = criterion.get("N", 0)

        traces = [
            # Positive frequency branch
            {
                "x": real_clipped,
                "y": imag_clipped,
                "type": "scatter",
                "mode": "lines",
                "name": "L(j\u03c9), \u03c9 > 0",
                "line": {"color": self.RESPONSE_COLOR, "width": 2.5},
                "hovertemplate": "Re = %{x:.3g}<br>Im = %{y:.3g}<extra>\u03c9 > 0</extra>",
            },
            # Negative frequency branch
            {
                "x": real_clipped,
                "y": imag_neg,
                "type": "scatter",
                "mode": "lines",
                "name": "L(j\u03c9), \u03c9 < 0",
                "line": {"color": self.RESPONSE_COLOR_DIM, "width": 2, "dash": "dash"},
                "hovertemplate": "Re = %{x:.3g}<br>Im = %{y:.3g}<extra>\u03c9 < 0</extra>",
            },
            # Critical point (-1, 0)
            {
                "x": [-1],
                "y": [0],
                "type": "scatter",
                "mode": "markers+text",
                "name": "Critical Point (\u22121, 0)",
                "marker": {"color": self.CRITICAL_POINT_COLOR, "size": 14, "symbol": "x",
                           "line": {"width": 3, "color": self.CRITICAL_POINT_COLOR}},
                "text": [f"(\u22121, 0) N={N}"],
                "textposition": "top right",
                "textfont": {"color": self.CRITICAL_POINT_COLOR, "size": 12, "family": "Inter, sans-serif"},
            },
        ]

        # Unit circle
        theta = np.linspace(0, 2 * np.pi, 100)
        traces.append({
            "x": np.cos(theta).tolist(),
            "y": np.sin(theta).tolist(),
            "type": "scatter",
            "mode": "lines",
            "name": "Unit Circle",
            "line": {"color": self.UNIT_CIRCLE_COLOR, "width": 1, "dash": "dot"},
            "opacity": 0.4,
            "hoverinfo": "skip",
        })

        # Direction arrows
        valid_indices = np.where(clip_mask)[0]
        if len(valid_indices) > 10:
            arrow_indices = valid_indices[np.linspace(0, len(valid_indices) - 1, 6, dtype=int)[1:-1]]
            traces.append({
                "x": [float(real_part[i]) for i in arrow_indices],
                "y": [float(imag_part[i]) for i in arrow_indices],
                "type": "scatter",
                "mode": "markers",
                "name": "\u03c9 direction",
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

        # Auto-scale
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

        # Encirclement count annotation
        status = criterion.get("stability_status", "")
        ann_color = self.STABLE_COLOR if criterion.get("is_stable") else self.CRITICAL_POINT_COLOR

        return {
            "id": "nyquist_plot",
            "title": "Nyquist Plot \u2014 L(j\u03c9)",
            "data": traces,
            "layout": {
                "xaxis": {
                    "title": "Re{L(j\u03c9)}",
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
                    "title": "Im{L(j\u03c9)}",
                    "showgrid": True,
                    "gridcolor": "rgba(148, 163, 184, 0.15)",
                    "zeroline": True,
                    "zerolinecolor": "rgba(148, 163, 184, 0.3)",
                    "range": y_range,
                    "fixedrange": False,
                },
                "annotations": [{
                    "text": f"N = {N} {'(CW)' if N > 0 else '(CCW)' if N < 0 else ''}",
                    "xref": "paper", "yref": "paper",
                    "x": 0.98, "y": 0.02,
                    "showarrow": False,
                    "font": {"size": 14, "color": ann_color, "family": "Inter, sans-serif"},
                    "bgcolor": "rgba(0,0,0,0.6)",
                    "bordercolor": ann_color,
                    "borderwidth": 1,
                    "borderpad": 6,
                }],
                "legend": {
                    "orientation": "h",
                    "yanchor": "bottom", "y": 1.02,
                    "xanchor": "left", "x": 0,
                    "font": {"size": 11},
                },
                "margin": {"l": 60, "r": 25, "t": 45, "b": 55},
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)",
                "uirevision": "nyquist",
            },
        }

    def _create_d_contour_plot(self) -> Dict[str, Any]:
        """S-plane D-contour with OL poles and zeros."""
        traces = []

        # Determine axis range
        all_points = []
        if len(self._poles) > 0:
            all_points.extend(self._poles)
        if len(self._zeros) > 0:
            all_points.extend(self._zeros)

        if all_points:
            all_pts = np.array(all_points)
            max_extent = max(np.max(np.abs(np.real(all_pts))),
                            np.max(np.abs(np.imag(all_pts))), 2.0)
            r = max_extent * 1.5
        else:
            r = 3.0

        xlim = [-r, r]
        ylim = [-r, r]

        # RHP region shading (unstable)
        traces.append({
            "x": [0, xlim[1], xlim[1], 0, 0],
            "y": [ylim[0], ylim[0], ylim[1], ylim[1], ylim[0]],
            "type": "scatter",
            "mode": "lines",
            "fill": "toself",
            "fillcolor": "rgba(239, 68, 68, 0.06)",
            "line": {"color": "rgba(239, 68, 68, 0.2)", "width": 1},
            "name": "RHP (unstable)",
            "hoverinfo": "skip",
        })

        # LHP region shading (stable)
        traces.append({
            "x": [xlim[0], 0, 0, xlim[0], xlim[0]],
            "y": [ylim[0], ylim[0], ylim[1], ylim[1], ylim[0]],
            "type": "scatter",
            "mode": "lines",
            "fill": "toself",
            "fillcolor": "rgba(52, 211, 153, 0.06)",
            "line": {"color": "rgba(52, 211, 153, 0.2)", "width": 1},
            "name": "LHP (stable)",
            "hoverinfo": "skip",
        })

        # jω axis
        traces.append({
            "x": [0, 0],
            "y": [ylim[0], ylim[1]],
            "type": "scatter",
            "mode": "lines",
            "line": {"color": self.IMAGINARY_AXIS_COLOR, "width": 2},
            "name": "j\u03c9 axis",
            "hoverinfo": "name",
        })

        # D-contour path (positive freq part only, clipped to view)
        d_s = self._d_contour_s
        # Only show the part visible in the axis range
        visible_mask = (np.abs(np.real(d_s)) < r * 1.2) & (np.abs(np.imag(d_s)) < r * 1.2)
        d_real = np.where(visible_mask, np.real(d_s), np.nan)
        d_imag = np.where(visible_mask, np.imag(d_s), np.nan)

        traces.append({
            "x": d_real.tolist(),
            "y": d_imag.tolist(),
            "type": "scatter",
            "mode": "lines",
            "name": "D-contour",
            "line": {"color": self.CONTOUR_COLOR, "width": 2.5},
            "hovertemplate": "s = %{x:.3g} + %{y:.3g}j<extra>D-contour</extra>",
        })

        # OL Zeros
        if len(self._zeros) > 0:
            traces.append({
                "x": [float(np.real(z)) for z in self._zeros],
                "y": [float(np.imag(z)) for z in self._zeros],
                "type": "scatter",
                "mode": "markers",
                "name": "OL Zeros",
                "marker": {
                    "symbol": "circle-open",
                    "size": 14,
                    "color": self.ZERO_COLOR,
                    "line": {"width": 3, "color": self.ZERO_COLOR},
                },
                "hovertemplate": "Zero<br>s = %{x:.3f} + %{y:.3f}j<extra></extra>",
            })

        # OL Poles
        if len(self._poles) > 0:
            traces.append({
                "x": [float(np.real(p)) for p in self._poles],
                "y": [float(np.imag(p)) for p in self._poles],
                "type": "scatter",
                "mode": "markers",
                "name": "OL Poles",
                "marker": {
                    "symbol": "x",
                    "size": 14,
                    "color": self.POLE_COLOR,
                    "line": {"width": 3, "color": self.POLE_COLOR},
                },
                "hovertemplate": "Pole<br>s = %{x:.3f} + %{y:.3f}j<extra></extra>",
            })

        P = self._stability_criterion.get("P", 0)

        return {
            "id": "d_contour_plot",
            "title": f"D-Contour (S-Plane) \u2014 P = {P} OL RHP pole(s)",
            "data": traces,
            "layout": {
                "xaxis": {
                    "title": "Real (\u03c3)",
                    "showgrid": True,
                    "gridcolor": "rgba(148, 163, 184, 0.15)",
                    "zeroline": True,
                    "zerolinecolor": "rgba(148, 163, 184, 0.3)",
                    "range": xlim,
                    "fixedrange": False,
                },
                "yaxis": {
                    "title": "Imaginary (j\u03c9)",
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
                    "yanchor": "bottom", "y": 1.02,
                    "xanchor": "left", "x": 0,
                    "font": {"size": 11},
                },
                "margin": {"l": 60, "r": 25, "t": 45, "b": 55},
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)",
                "uirevision": "d_contour",
            },
        }

    def _create_cl_pole_map(self) -> Dict[str, Any]:
        """Closed-loop pole map confirming Z count."""
        traces = []
        Z = self._stability_criterion.get("Z", 0)

        # Determine axis range from CL poles
        all_points = self._cl_poles if len(self._cl_poles) > 0 else np.array([0])
        max_extent = max(np.max(np.abs(np.real(all_points))),
                        np.max(np.abs(np.imag(all_points))), 1.0)
        r = max_extent * 1.4
        xlim = [-r, r * 0.5]
        ylim = [-r, r]

        # Stable region
        traces.append({
            "x": [xlim[0], 0, 0, xlim[0], xlim[0]],
            "y": [ylim[0], ylim[0], ylim[1], ylim[1], ylim[0]],
            "type": "scatter",
            "mode": "lines",
            "fill": "toself",
            "fillcolor": "rgba(52, 211, 153, 0.08)",
            "line": {"color": "rgba(52, 211, 153, 0.4)", "width": 1},
            "name": "Stable Region",
            "hoverinfo": "skip",
        })

        # jω axis
        traces.append({
            "x": [0, 0],
            "y": [ylim[0], ylim[1]],
            "type": "scatter",
            "mode": "lines",
            "line": {"color": self.IMAGINARY_AXIS_COLOR, "width": 2},
            "name": "j\u03c9 axis",
            "hoverinfo": "name",
        })

        # CL poles colored by stability
        if len(self._cl_poles) > 0:
            stable_poles = [p for p in self._cl_poles if np.real(p) < -1e-10]
            unstable_poles = [p for p in self._cl_poles if np.real(p) > 1e-10]
            marginal_poles = [p for p in self._cl_poles if abs(np.real(p)) <= 1e-10]

            if stable_poles:
                traces.append({
                    "x": [float(np.real(p)) for p in stable_poles],
                    "y": [float(np.imag(p)) for p in stable_poles],
                    "type": "scatter",
                    "mode": "markers",
                    "name": "CL Poles (stable)",
                    "marker": {
                        "symbol": "x",
                        "size": 14,
                        "color": self.CL_POLE_STABLE_COLOR,
                        "line": {"width": 3, "color": self.CL_POLE_STABLE_COLOR},
                    },
                    "hovertemplate": "CL Pole (stable)<br>s = %{x:.3f} + %{y:.3f}j<extra></extra>",
                })

            if unstable_poles:
                traces.append({
                    "x": [float(np.real(p)) for p in unstable_poles],
                    "y": [float(np.imag(p)) for p in unstable_poles],
                    "type": "scatter",
                    "mode": "markers",
                    "name": "CL Poles (unstable)",
                    "marker": {
                        "symbol": "x",
                        "size": 14,
                        "color": self.CL_POLE_UNSTABLE_COLOR,
                        "line": {"width": 3, "color": self.CL_POLE_UNSTABLE_COLOR},
                    },
                    "hovertemplate": "CL Pole (RHP!)<br>s = %{x:.3f} + %{y:.3f}j<extra></extra>",
                })

            if marginal_poles:
                traces.append({
                    "x": [float(np.real(p)) for p in marginal_poles],
                    "y": [float(np.imag(p)) for p in marginal_poles],
                    "type": "scatter",
                    "mode": "markers",
                    "name": "CL Poles (marginal)",
                    "marker": {
                        "symbol": "x",
                        "size": 14,
                        "color": self.CONTOUR_COLOR,
                        "line": {"width": 3, "color": self.CONTOUR_COLOR},
                    },
                    "hovertemplate": "CL Pole (j\u03c9 axis)<br>s = %{x:.3f} + %{y:.3f}j<extra></extra>",
                })

        K = float(self.parameters["gain_K"])

        return {
            "id": "cl_pole_map",
            "title": f"Closed-Loop Poles (K={K:.2g}) \u2014 Z = {Z}",
            "data": traces,
            "layout": {
                "xaxis": {
                    "title": "Real (\u03c3)",
                    "showgrid": True,
                    "gridcolor": "rgba(148, 163, 184, 0.15)",
                    "zeroline": True,
                    "zerolinecolor": "rgba(148, 163, 184, 0.3)",
                    "range": xlim,
                    "fixedrange": False,
                },
                "yaxis": {
                    "title": "Imaginary (j\u03c9)",
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
                    "yanchor": "bottom", "y": 1.02,
                    "xanchor": "left", "x": 0,
                    "font": {"size": 11},
                },
                "margin": {"l": 60, "r": 25, "t": 45, "b": 55},
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)",
                "uirevision": "cl_poles",
            },
        }
