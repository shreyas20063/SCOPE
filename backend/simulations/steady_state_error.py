"""
Steady-State Error Analyzer

Interactive exploration of steady-state tracking error in unity-feedback
control systems. Demonstrates the relationship between system type (number
of integrators), error constants (Kp, Kv, Ka), input type (step/ramp/
parabolic), and gain K.

Core theory (Ogata Ch.5, Nise Ch.7):
- System Type n = number of poles at s=0 in open-loop G(s)
- Error constants: Kp = lim(s->0) G(s), Kv = lim(s->0) sG(s), Ka = lim(s->0) s^2 G(s)
- Steady-state error: ess = lim(s->0) sE(s) via Final Value Theorem
"""

import time
import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from scipy import signal
from .base_simulator import BaseSimulator


class SteadyStateErrorSimulator(BaseSimulator):
    """Steady-state error analyzer for unity-feedback control systems."""

    # ------------------------------------------------------------------ #
    #  Presets                                                            #
    # ------------------------------------------------------------------ #
    _PRESETS: Dict[str, Dict[str, list]] = {
        "type0_first":    {"num": [1],       "den": [1, 2]},
        "type0_second":   {"num": [1],       "den": [1, 4, 3]},
        "type1_standard": {"num": [1],       "den": [1, 5, 0]},
        "type1_two_pole": {"num": [1],       "den": [1, 5, 4, 0]},
        "type2_standard": {"num": [1],       "den": [1, 10, 0, 0]},
        "type2_complex":  {"num": [1],       "den": [1, 7, 10, 0, 0]},
        "type3":          {"num": [1],       "den": [1, 4, 0, 0, 0]},
    }

    _PRESET_DESCRIPTIONS: Dict[str, str] = {
        "type0_first":    "Type 0: First-order plant with one real pole",
        "type0_second":   "Type 0: Second-order plant with two real poles",
        "type1_standard": "Type 1: One integrator, one real pole",
        "type1_two_pole": "Type 1: One integrator, two real poles",
        "type2_standard": "Type 2: Two integrators, one real pole",
        "type2_complex":  "Type 2: Two integrators, two real poles",
        "type3":          "Type 3: Three integrators, one real pole",
    }

    # ------------------------------------------------------------------ #
    #  Schema & Defaults                                                  #
    # ------------------------------------------------------------------ #
    PARAMETER_SCHEMA = {
        "plant_preset": {
            "type": "select",
            "options": [
                {"value": "type0_first",    "label": "Type 0 \u2014 K/(s+2)"},
                {"value": "type0_second",   "label": "Type 0 \u2014 K/((s+1)(s+3))"},
                {"value": "type1_standard", "label": "Type 1 \u2014 K/(s(s+5))"},
                {"value": "type1_two_pole", "label": "Type 1 \u2014 K/(s(s+1)(s+4))"},
                {"value": "type2_standard", "label": "Type 2 \u2014 K/(s\u00b2(s+10))"},
                {"value": "type2_complex",  "label": "Type 2 \u2014 K/(s\u00b2(s+2)(s+5))"},
                {"value": "type3",          "label": "Type 3 \u2014 K/(s\u00b3(s+4))"},
                {"value": "custom",         "label": "Custom G(s)"},
            ],
            "default": "type1_standard",
        },
        "plant_num": {"type": "expression", "default": "1"},
        "plant_den": {"type": "expression", "default": "1, 5, 0"},
        "gain_K": {
            "type": "slider", "min": 0.1, "max": 100,
            "step": 0.1, "default": 10.0,
        },
        "input_type": {
            "type": "select",
            "options": [
                {"value": "step",      "label": "Step \u2014 r(t) = Au(t)"},
                {"value": "ramp",      "label": "Ramp \u2014 r(t) = Atu(t)"},
                {"value": "parabolic", "label": "Parabolic \u2014 r(t) = \u00bdAt\u00b2u(t)"},
            ],
            "default": "step",
        },
        "input_magnitude": {
            "type": "slider", "min": 0.1, "max": 10,
            "step": 0.1, "default": 1.0,
        },
    }

    DEFAULT_PARAMS: Dict[str, Any] = {
        "plant_preset": "type1_standard",
        "plant_num": "1",
        "plant_den": "1, 5, 0",
        "gain_K": 10.0,
        "input_type": "step",
        "input_magnitude": 1.0,
    }

    # ------------------------------------------------------------------ #
    #  Lifecycle                                                          #
    # ------------------------------------------------------------------ #
    def initialize(self, params: Optional[Dict[str, Any]] = None) -> None:
        """Initialize simulation with parameters."""
        self.parameters = {**self.DEFAULT_PARAMS, **(params or {})}
        for name, value in self.parameters.items():
            self.parameters[name] = self._validate_param(name, value)
        self._initialized = True

    def update_parameter(self, name: str, value: Any) -> Dict[str, Any]:
        """Update a single parameter and return new state."""
        if name in self.parameters:
            self.parameters[name] = self._validate_param(name, value)
            # Selecting a preset updates the expression fields
            if name == "plant_preset" and value != "custom":
                preset = self._PRESETS.get(str(value))
                if preset:
                    self.parameters["plant_num"] = ", ".join(
                        str(c) for c in preset["num"]
                    )
                    self.parameters["plant_den"] = ", ".join(
                        str(c) for c in preset["den"]
                    )
            # Manual edit of num/den switches preset to custom
            if name in ("plant_num", "plant_den"):
                self.parameters["plant_preset"] = "custom"
        return self.get_state()

    def reset(self) -> Dict[str, Any]:
        """Reset to default parameters."""
        self.parameters = self.DEFAULT_PARAMS.copy()
        self._initialized = True
        return self.get_state()

    # ------------------------------------------------------------------ #
    #  Polynomial helpers                                                 #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _parse_poly_string(s: str) -> np.ndarray:
        """Parse comma-separated coefficient string to ndarray.

        Args:
            s: e.g. "1, 5, 0"

        Returns:
            np.ndarray of float coefficients, fallback [1] on error.
        """
        try:
            parts = [p.strip() for p in str(s).split(",") if p.strip()]
            coeffs = [float(p) for p in parts]
            if not coeffs:
                return np.array([1.0])
            return np.array(coeffs, dtype=float)
        except (ValueError, TypeError):
            return np.array([1.0])

    @staticmethod
    def _format_polynomial_latex(coeffs: np.ndarray) -> str:
        """Convert coefficient array to LaTeX polynomial string.

        [1, 5, 0] -> "s^2 + 5s"
        [1, 4, 3] -> "s^2 + 4s + 3"
        """
        n = len(coeffs) - 1
        terms: List[str] = []
        for i, c in enumerate(coeffs):
            power = n - i
            if abs(c) < 1e-12:
                continue
            abs_c = abs(c)
            # Build the term without sign
            if power == 0:
                term = f"{abs_c:g}"
            elif power == 1:
                term = "s" if abs_c == 1.0 else f"{abs_c:g}s"
            else:
                term = f"s^{{{power}}}" if abs_c == 1.0 else f"{abs_c:g}s^{{{power}}}"
            # Attach sign
            if not terms:
                # First term: only show minus if negative
                if c < 0:
                    term = "-" + term
            else:
                term = (" + " + term) if c > 0 else (" - " + term)
            terms.append(term)

        return "".join(terms) if terms else "0"

    def _format_plant_latex(self, num: np.ndarray, den: np.ndarray,
                            gain_K: float) -> str:
        """Build KaTeX string for G(s) = K * num(s) / den(s)."""
        num_str = self._format_polynomial_latex(num)
        den_str = self._format_polynomial_latex(den)
        # Don't show "K · (1)" when numerator is just a constant
        if num_str == "1":
            return f"G(s) = \\frac{{{gain_K:g}}}{{{den_str}}}"
        return f"G(s) = \\frac{{{gain_K:g}({num_str})}}{{{den_str}}}"

    # ------------------------------------------------------------------ #
    #  Plant transfer function                                            #
    # ------------------------------------------------------------------ #
    def _get_plant_tf(self) -> Tuple[np.ndarray, np.ndarray]:
        """Return (num, den) with gain K applied to numerator.

        Uses presets for known plants, parses expression strings for custom.
        Validates properness: deg(den) >= deg(num). Falls back to 1/(s+1)
        if improper.
        """
        preset = str(self.parameters["plant_preset"])
        K = float(self.parameters["gain_K"])

        if preset != "custom" and preset in self._PRESETS:
            p = self._PRESETS[preset]
            num_base = np.array(p["num"], dtype=float)
            den = np.array(p["den"], dtype=float)
        else:
            num_base = self._parse_poly_string(self.parameters["plant_num"])
            den = self._parse_poly_string(self.parameters["plant_den"])

        num = K * num_base

        # Validate properness
        if len(np.trim_zeros(num, "f")) > len(np.trim_zeros(den, "f")):
            num = np.array([1.0])
            den = np.array([1.0, 1.0])

        return num, den

    # ------------------------------------------------------------------ #
    #  System type & error constants                                      #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _count_origin_poles(den: np.ndarray) -> int:
        """Count trailing near-zero coefficients (poles at s=0)."""
        count = 0
        for c in reversed(den):
            if abs(c) < 1e-10:
                count += 1
            else:
                break
        return count

    @staticmethod
    def _cancel_common_s_factors(
        num: np.ndarray, den: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Cancel common s=0 factors between numerator and denominator.

        For G(s) = num_body·s^m / (den_body·s^n), cancels min(m,n)
        common s-factors, returning reduced polynomials.
        """
        n_num = 0
        for c in reversed(num):
            if abs(c) < 1e-10:
                n_num += 1
            else:
                break
        n_den = 0
        for c in reversed(den):
            if abs(c) < 1e-10:
                n_den += 1
            else:
                break
        common = min(n_num, n_den)
        if common == 0:
            return num.copy(), den.copy()
        num_red = num[: len(num) - common]
        den_red = den[: len(den) - common]
        if len(num_red) == 0:
            num_red = np.array([1.0])
        if len(den_red) == 0:
            den_red = np.array([1.0])
        return num_red, den_red

    @staticmethod
    def _compute_error_constants(num: np.ndarray, den: np.ndarray,
                                 system_type: int) -> Dict[str, Any]:
        """Compute position, velocity, and acceleration error constants.

        Factors out s^n from den before evaluating the static gain.
        """
        # Remove the trailing zeros (the s^n factor)
        if system_type > 0:
            den_reduced = den[: len(den) - system_type]
        else:
            den_reduced = den

        # Static gain: polyval at s=0 gives the constant term
        num_at_0 = np.polyval(num, 0.0)
        den_at_0 = np.polyval(den_reduced, 0.0)
        if abs(den_at_0) < 1e-15:
            K_static = 0.0
        else:
            K_static = num_at_0 / den_at_0

        # Error constants based on system type
        if system_type == 0:
            Kp = K_static
            Kv = 0.0
            Ka = 0.0
        elif system_type == 1:
            Kp = float("inf")
            Kv = K_static
            Ka = 0.0
        elif system_type == 2:
            Kp = float("inf")
            Kv = float("inf")
            Ka = K_static
        else:  # type >= 3
            Kp = float("inf")
            Kv = float("inf")
            Ka = float("inf")

        return {"Kp": Kp, "Kv": Kv, "Ka": Ka, "K_static": K_static}

    @staticmethod
    def _compute_steady_state_errors(error_constants: Dict[str, Any],
                                     system_type: int,
                                     A: float) -> Dict[str, Any]:
        """Compute ess for step, ramp, parabolic inputs.

        Returns dict with float values (may be float('inf') or 0.0).
        """
        Kp = error_constants["Kp"]
        Kv = error_constants["Kv"]
        Ka = error_constants["Ka"]

        # Step error
        if system_type == 0:
            step_ess = A / (1.0 + Kp) if Kp != float("inf") else 0.0
        else:
            step_ess = 0.0

        # Ramp error: ess = A / Kv
        if system_type == 0:
            ramp_ess = float("inf")
        elif system_type == 1:
            if Kv == float("inf"):
                ramp_ess = 0.0
            elif abs(Kv) < 1e-15:
                ramp_ess = float("inf")  # degenerate: zero-pole cancellation
            else:
                ramp_ess = A / Kv
        else:
            ramp_ess = 0.0

        # Parabolic error: ess = A / Ka
        if system_type <= 1:
            parabolic_ess = float("inf")
        elif system_type == 2:
            if Ka == float("inf"):
                parabolic_ess = 0.0
            elif abs(Ka) < 1e-15:
                parabolic_ess = float("inf")  # degenerate: zero-pole cancellation
            else:
                parabolic_ess = A / Ka
        else:
            parabolic_ess = 0.0

        return {"step": step_ess, "ramp": ramp_ess, "parabolic": parabolic_ess}

    # ------------------------------------------------------------------ #
    #  Closed-loop poles & stability                                      #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _compute_cl_poles(num: np.ndarray,
                          den: np.ndarray) -> Tuple[np.ndarray, bool]:
        """Compute closed-loop poles for unity feedback: 1 + G(s) = 0.

        CL characteristic polynomial = den + num.
        Returns (poles_array, is_stable).
        """
        den_cl = np.polyadd(den, num)
        # Strip leading zeros (BUG-002 prevention)
        den_cl = np.trim_zeros(den_cl, "f")
        if len(den_cl) == 0:
            den_cl = np.array([1.0])

        poles = np.roots(den_cl)
        # Strictly stable: all poles must have Re < 0 (not just < epsilon).
        # Marginally stable poles (Re ≈ 0, Im ≠ 0) make FVT invalid.
        if len(poles) == 0:
            is_stable = True
        else:
            is_stable = bool(np.all(np.real(poles) < -1e-6))
        return poles, is_stable

    @staticmethod
    def _estimate_time_range(cl_poles: np.ndarray, is_stable: bool) -> float:
        """Estimate a good simulation time range from CL poles."""
        if not is_stable or len(cl_poles) == 0:
            return 10.0

        real_parts = np.real(cl_poles)
        stable_reals = real_parts[real_parts < -1e-10]
        if len(stable_reals) == 0:
            return 10.0

        slowest = np.min(np.abs(stable_reals))
        t_settle = 5.0 / slowest
        return float(np.clip(t_settle, 2.0, 50.0))

    # ------------------------------------------------------------------ #
    #  Time-domain simulation                                             #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _simulate_response(num_cl: np.ndarray, den_cl: np.ndarray,
                           input_type: str, A: float, t_end: float,
                           is_stable: bool) -> Dict[str, Any]:
        """Simulate closed-loop time response.

        Args:
            num_cl: Closed-loop numerator (= OL num for unity feedback)
            den_cl: Closed-loop denominator (= OL den + OL num)
            input_type: "step", "ramp", or "parabolic"
            A: Input magnitude
            t_end: Simulation end time
            is_stable: Whether CL system is stable

        Returns:
            dict with keys t, y, r, e, diverged
        """
        n_pts = 500
        t_arr = np.linspace(0, t_end, n_pts)
        diverged = False

        try:
            sys_cl = signal.TransferFunction(num_cl, den_cl)

            if input_type == "step":
                t_out, y = signal.step(sys_cl, T=t_arr)
                y = A * y
                r = np.full_like(t_arr, A)
            elif input_type == "ramp":
                U = A * t_arr
                t_out, y, _ = signal.lsim(sys_cl, U=U, T=t_arr)
                r = U
            else:  # parabolic
                U = A * t_arr**2 / 2.0
                t_out, y, _ = signal.lsim(sys_cl, U=U, T=t_arr)
                r = U

            # Check for divergence
            if np.any(np.abs(y) > 1e4):
                diverged = True
                y = np.clip(y, -1e4, 1e4)

            e = r - y

        except Exception:
            y = np.zeros_like(t_arr)
            r = np.full_like(t_arr, A) if input_type == "step" else (
                A * t_arr if input_type == "ramp" else A * t_arr**2 / 2.0
            )
            e = r - y
            diverged = True

        return {
            "t": t_arr,
            "y": y,
            "r": r,
            "e": e,
            "diverged": diverged,
        }

    # ------------------------------------------------------------------ #
    #  ess vs K sweep                                                     #
    # ------------------------------------------------------------------ #
    def _compute_ess_vs_K(self, num_base: np.ndarray,
                          den: np.ndarray,
                          A: float) -> Dict[str, Any]:
        """Sweep gain K and compute ess for each input type.

        Args:
            num_base: Unscaled numerator (before K multiplication)
            den: Denominator polynomial
            A: Input magnitude

        Returns:
            dict with K_values, step_ess, ramp_ess, parabolic_ess, stable
        """
        K_values = np.logspace(-1, 2, 80).tolist()
        step_ess_list: List[Optional[float]] = []
        ramp_ess_list: List[Optional[float]] = []
        parabolic_ess_list: List[Optional[float]] = []
        stable_list: List[bool] = []

        # Cancel common origin factors (constant across K since K > 0)
        num_base_eff, den_eff = self._cancel_common_s_factors(num_base, den)
        system_type = self._count_origin_poles(den_eff)

        for K in K_values:
            num_k = K * num_base_eff
            ec = self._compute_error_constants(num_k, den_eff, system_type)
            errors = self._compute_steady_state_errors(ec, system_type, A)
            _, is_stable = self._compute_cl_poles(num_k, den_eff)

            stable_list.append(is_stable)

            for key, out_list in [("step", step_ess_list),
                                  ("ramp", ramp_ess_list),
                                  ("parabolic", parabolic_ess_list)]:
                val = errors[key]
                if val == float("inf"):
                    out_list.append(None)  # JSON null
                else:
                    out_list.append(min(val, 1000.0))

        return {
            "K_values": K_values,
            "step_ess": step_ess_list,
            "ramp_ess": ramp_ess_list,
            "parabolic_ess": parabolic_ess_list,
            "stable": stable_list,
        }

    # ------------------------------------------------------------------ #
    #  FVT LaTeX derivation                                               #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _build_fvt_latex(input_type: str, system_type: int,
                         error_constants: Dict[str, Any], A: float,
                         ess: float, is_stable: bool) -> str:
        """Build LaTeX showing the Final Value Theorem derivation."""
        lines: List[str] = []

        if not is_stable:
            lines.append(
                r"e_{ss} = \lim_{s \to 0} s \cdot E(s)"
            )
            lines.append(
                r"\text{FVT invalid --- closed-loop system is unstable}"
            )
            return " \\\\ ".join(lines)

        # Foundational FVT derivation (Ogata Ch.5, Nise Ch.7)
        lines.append(
            r"e_{ss} = \lim_{t \to \infty} e(t) = \lim_{s \to 0} s\,E(s)"
        )
        lines.append(
            r"E(s) = \frac{R(s)}{1 + G(s)}"
        )
        lines.append(
            r"\therefore\; e_{ss} = \lim_{s \to 0} \frac{s \cdot R(s)}{1 + G(s)}"
        )

        if input_type == "step":
            Kp = error_constants["Kp"]
            lines.append(
                r"= \lim_{s \to 0} \frac{s \cdot \frac{"
                + f"{A:g}"
                + r"}{s}}{1 + G(s)} = \frac{"
                + f"{A:g}"
                + r"}{1 + K_p}"
            )
            if system_type == 0 and Kp != float("inf"):
                lines.append(
                    f"= \\frac{{{A:g}}}{{1 + {Kp:.4g}}} = {ess:.4g}"
                )
            else:
                lines.append("= 0")
        elif input_type == "ramp":
            Kv = error_constants["Kv"]
            lines.append(
                r"= \lim_{s \to 0} \frac{s \cdot \frac{"
                + f"{A:g}"
                + r"}{s^2}}{1 + G(s)} = \frac{"
                + f"{A:g}"
                + r"}{K_v}"
            )
            if system_type == 0:
                lines.append(r"= \infty \quad (K_v = 0 \text{ for Type 0})")
            elif system_type == 1 and Kv != float("inf") and Kv != 0.0:
                lines.append(
                    f"= \\frac{{{A:g}}}{{{Kv:.4g}}} = {ess:.4g}"
                )
            else:
                lines.append("= 0")
        else:  # parabolic
            Ka = error_constants["Ka"]
            lines.append(
                r"= \lim_{s \to 0} \frac{s \cdot \frac{"
                + f"{A:g}"
                + r"}{s^3}}{1 + G(s)} = \frac{"
                + f"{A:g}"
                + r"}{K_a}"
            )
            if system_type <= 1:
                lines.append(
                    r"= \infty \quad (K_a = 0 \text{ for Type }"
                    + f"{system_type}"
                    + ")"
                )
            elif system_type == 2 and Ka != float("inf") and Ka != 0.0:
                lines.append(
                    f"= \\frac{{{A:g}}}{{{Ka:.4g}}} = {ess:.4g}"
                )
            else:
                lines.append("= 0")

        return " \\\\ ".join(lines)

    # ------------------------------------------------------------------ #
    #  Display formatters                                                 #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _display_value(v: float) -> str:
        """Format a numeric value for display, converting inf to symbol."""
        if v == float("inf"):
            return "\u221e"
        if v == 0.0:
            return "0"
        return f"{v:.4g}"

    # ------------------------------------------------------------------ #
    #  Plot builders                                                      #
    # ------------------------------------------------------------------ #
    def _base_layout(self, plot_id: str, title: str,
                     xaxis_title: str = "", yaxis_title: str = "",
                     **extra: Any) -> Dict[str, Any]:
        """Shared layout template for all plots."""
        layout: Dict[str, Any] = {
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "font": {"family": "Inter, sans-serif", "size": 12,
                      "color": "#f1f5f9"},
            "margin": {"t": 40, "r": 25, "b": 55, "l": 60},
            "xaxis": {
                "title": xaxis_title,
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
            },
            "yaxis": {
                "title": yaxis_title,
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
            },
            "legend": {
                "x": 0.98, "y": 0.98,
                "xanchor": "right", "yanchor": "top",
                "bgcolor": "rgba(0,0,0,0)",
            },
            "uirevision": plot_id,
            "datarevision": f"{plot_id}-{time.time()}",
        }
        layout.update(extra)
        return layout

    def _build_time_response_plot(self, sim: Dict[str, Any],
                                  input_type: str, ess: float,
                                  is_stable: bool) -> Dict[str, Any]:
        """Plot 1: Reference vs output time response."""
        t = sim["t"].tolist()
        r = sim["r"].tolist()
        y = sim["y"].tolist()

        input_label = {"step": "Step", "ramp": "Ramp",
                       "parabolic": "Parabolic"}[input_type]

        data: List[Dict[str, Any]] = [
            {
                "x": t, "y": r,
                "type": "scatter", "mode": "lines",
                "name": f"Reference r(t)",
                "line": {"color": "#3b82f6", "width": 2, "dash": "dash"},
            },
            {
                "x": t, "y": y,
                "type": "scatter", "mode": "lines",
                "name": "Output y(t)",
                "line": {"color": "#ef4444", "width": 2},
            },
        ]

        annotations: List[Dict[str, Any]] = []

        if not is_stable or sim["diverged"]:
            annotations.append({
                "x": 0.5, "y": 0.95, "xref": "paper", "yref": "paper",
                "text": "UNSTABLE \u2014 FVT invalid",
                "showarrow": False,
                "font": {"size": 14, "color": "#ef4444"},
                "bgcolor": "rgba(239,68,68,0.15)",
                "bordercolor": "#ef4444",
                "borderwidth": 1,
            })
        elif 0 < ess < float("inf"):
            # Show gap annotation at the right end
            t_end = t[-1]
            y_end = y[-1]
            r_end = r[-1]
            annotations.append({
                "x": t_end, "y": (y_end + r_end) / 2,
                "ax": t_end - (t_end * 0.05), "ay": (y_end + r_end) / 2,
                "xref": "x", "yref": "y",
                "axref": "x", "ayref": "y",
                "text": f"e_ss = {ess:.3g}",
                "showarrow": True,
                "arrowhead": 0, "arrowwidth": 2,
                "arrowcolor": "#10b981",
                "font": {"color": "#10b981", "size": 11},
            })

        layout = self._base_layout(
            "time_response",
            f"System Response ({input_label} Input)",
            xaxis_title="Time (s)",
            yaxis_title="Amplitude",
        )
        layout["annotations"] = annotations

        return {"id": "time_response", "title": f"System Response ({input_label} Input)",
                "data": data, "layout": layout}

    def _build_error_signal_plot(self, sim: Dict[str, Any],
                                 ess: float,
                                 is_stable: bool) -> Dict[str, Any]:
        """Plot 2: Error signal e(t)."""
        t = sim["t"].tolist()
        e = sim["e"].tolist()

        data: List[Dict[str, Any]] = [
            {
                "x": t, "y": e,
                "type": "scatter", "mode": "lines",
                "name": "Error e(t)",
                "line": {"color": "#f59e0b", "width": 2},
            },
        ]

        annotations: List[Dict[str, Any]] = []

        if 0 < ess < float("inf") and is_stable:
            # Horizontal reference at ess
            data.append({
                "x": [t[0], t[-1]], "y": [ess, ess],
                "type": "scatter", "mode": "lines",
                "name": f"e_ss = {ess:.3g}",
                "line": {"color": "#10b981", "width": 1.5, "dash": "dash"},
            })
            annotations.append({
                "x": t[-1] * 0.8, "y": ess,
                "text": f"e_ss = {ess:.3g}",
                "showarrow": False,
                "yshift": 12,
                "font": {"color": "#10b981", "size": 11},
            })
        elif ess == float("inf"):
            annotations.append({
                "x": 0.5, "y": 0.92, "xref": "paper", "yref": "paper",
                "text": "e(t) \u2192 \u221e",
                "showarrow": False,
                "font": {"size": 13, "color": "#f59e0b"},
            })
        elif ess == 0.0 and is_stable:
            annotations.append({
                "x": 0.5, "y": 0.92, "xref": "paper", "yref": "paper",
                "text": "e(t) \u2192 0",
                "showarrow": False,
                "font": {"size": 13, "color": "#10b981"},
            })

        layout = self._base_layout(
            "error_signal", "Error Signal e(t) = r(t) - y(t)",
            xaxis_title="Time (s)", yaxis_title="Error",
        )
        layout["annotations"] = annotations

        return {"id": "error_signal", "title": "Error Signal e(t) = r(t) - y(t)",
                "data": data, "layout": layout}

    def _build_ess_vs_gain_plot(self, ess_data: Dict[str, Any],
                                current_K: float) -> Dict[str, Any]:
        """Plot 3: Steady-state error vs gain K (log-log)."""
        K_vals = ess_data["K_values"]
        data: List[Dict[str, Any]] = []

        curves = [
            ("step_ess",      "Step e_ss",      "#3b82f6"),
            ("ramp_ess",      "Ramp e_ss",      "#ef4444"),
            ("parabolic_ess", "Parabolic e_ss", "#10b981"),
        ]

        for key, name, color in curves:
            vals = ess_data[key]
            # Only plot if there are finite non-zero values
            finite_vals = [v for v in vals if v is not None and v > 0]
            if not finite_vals:
                continue
            data.append({
                "x": K_vals, "y": vals,
                "type": "scatter", "mode": "lines",
                "name": name,
                "line": {"color": color, "width": 2},
                "connectgaps": False,
            })

        # Vertical line at current K
        data.append({
            "x": [current_K, current_K], "y": [0.001, 1000],
            "type": "scatter", "mode": "lines",
            "name": f"K = {current_K:g}",
            "line": {"color": "#14b8a6", "width": 1.5, "dash": "dash"},
        })

        # Shade unstable region
        shapes: List[Dict[str, Any]] = []
        stable_flags = ess_data["stable"]
        unstable_start = None
        for i, (k, s) in enumerate(zip(K_vals, stable_flags)):
            if not s and unstable_start is None:
                unstable_start = k
            elif s and unstable_start is not None:
                shapes.append({
                    "type": "rect",
                    "xref": "x", "yref": "paper",
                    "x0": unstable_start, "x1": k,
                    "y0": 0, "y1": 1,
                    "fillcolor": "rgba(239,68,68,0.08)",
                    "line": {"width": 0},
                    "layer": "below",
                })
                unstable_start = None
        if unstable_start is not None:
            shapes.append({
                "type": "rect",
                "xref": "x", "yref": "paper",
                "x0": unstable_start, "x1": K_vals[-1],
                "y0": 0, "y1": 1,
                "fillcolor": "rgba(239,68,68,0.08)",
                "line": {"width": 0},
                "layer": "below",
            })

        layout = self._base_layout(
            "ess_vs_gain", "Steady-State Error vs Gain K",
            xaxis_title="Gain K", yaxis_title="e_ss",
        )
        layout["xaxis"]["type"] = "log"
        layout["yaxis"]["type"] = "log"
        layout["shapes"] = shapes

        return {"id": "ess_vs_gain", "title": "Steady-State Error vs Gain K",
                "data": data, "layout": layout}

    def _build_pole_zero_map(self, num: np.ndarray, den: np.ndarray,
                             cl_poles: np.ndarray, system_type: int,
                             is_stable: bool) -> Dict[str, Any]:
        """Plot 4: Open-loop and closed-loop pole-zero map."""
        data: List[Dict[str, Any]] = []

        # Open-loop zeros (roots of numerator)
        num_trimmed = np.trim_zeros(num, "f")
        ol_zeros = np.roots(num_trimmed) if len(num_trimmed) > 1 else np.array([])

        # Open-loop poles (roots of denominator)
        den_trimmed = np.trim_zeros(den, "f")
        ol_poles = np.roots(den_trimmed) if len(den_trimmed) > 1 else np.array([])

        # OL zeros
        if len(ol_zeros) > 0:
            data.append({
                "x": np.real(ol_zeros).tolist(),
                "y": np.imag(ol_zeros).tolist(),
                "type": "scatter", "mode": "markers",
                "name": "OL Zeros",
                "marker": {"symbol": "circle-open", "size": 12,
                           "color": "#10b981",
                           "line": {"width": 2, "color": "#10b981"}},
            })

        # OL poles — separate origin poles for annotation
        non_origin_ol = ol_poles[np.abs(ol_poles) > 1e-8]
        origin_ol = ol_poles[np.abs(ol_poles) <= 1e-8]

        if len(non_origin_ol) > 0:
            data.append({
                "x": np.real(non_origin_ol).tolist(),
                "y": np.imag(non_origin_ol).tolist(),
                "type": "scatter", "mode": "markers",
                "name": "OL Poles",
                "marker": {"symbol": "x", "size": 12,
                           "color": "#ef4444",
                           "line": {"width": 2, "color": "#ef4444"}},
            })

        n_origin_poles = int(len(origin_ol))
        if n_origin_poles > 0:
            data.append({
                "x": [0.0], "y": [0.0],
                "type": "scatter", "mode": "markers+text",
                "name": f"OL Poles at origin (\u00d7{n_origin_poles})",
                "marker": {"symbol": "x", "size": 16,
                           "color": "#ef4444",
                           "line": {"width": 3, "color": "#ef4444"}},
                "text": [f"\u00d7{n_origin_poles}"],
                "textposition": "top right",
                "textfont": {"color": "#ef4444", "size": 11},
            })

        # Closed-loop poles
        if len(cl_poles) > 0:
            cl_re = np.real(cl_poles)
            cl_im = np.imag(cl_poles)
            cl_colors = ["#10b981" if r < -1e-6 else "#ef4444"
                         for r in cl_re]
            data.append({
                "x": cl_re.tolist(),
                "y": cl_im.tolist(),
                "type": "scatter", "mode": "markers",
                "name": "CL Poles",
                "marker": {"symbol": "circle", "size": 10,
                           "color": cl_colors,
                           "line": {"width": 1, "color": cl_colors}},
            })

        # Collect all points for axis range
        all_re = np.concatenate([
            np.real(ol_poles) if len(ol_poles) else np.array([]),
            np.real(ol_zeros) if len(ol_zeros) else np.array([]),
            np.real(cl_poles) if len(cl_poles) else np.array([]),
        ])
        all_im = np.concatenate([
            np.imag(ol_poles) if len(ol_poles) else np.array([]),
            np.imag(ol_zeros) if len(ol_zeros) else np.array([]),
            np.imag(cl_poles) if len(cl_poles) else np.array([]),
        ])

        re_range = float(np.max(np.abs(all_re))) if len(all_re) else 2.0
        im_range = float(np.max(np.abs(all_im))) if len(all_im) else 2.0
        re_range = max(re_range, 1.0) * 1.3
        im_range = max(im_range, 1.0) * 1.3

        # jw-axis reference
        data.append({
            "x": [0, 0], "y": [-im_range, im_range],
            "type": "scatter", "mode": "lines",
            "name": "j\u03c9 axis",
            "line": {"color": "rgba(148,163,184,0.4)", "width": 1,
                     "dash": "dash"},
            "showlegend": False,
        })

        layout = self._base_layout(
            "pole_zero_map",
            f"Pole-Zero Map (Type {system_type})",
            xaxis_title="Real",
            yaxis_title="Imaginary",
        )
        layout["xaxis"]["range"] = [-re_range, re_range]
        layout["yaxis"]["range"] = [-im_range, im_range]
        layout["xaxis"]["scaleanchor"] = "y"

        return {"id": "pole_zero_map",
                "title": f"Pole-Zero Map (Type {system_type})",
                "data": data, "layout": layout}

    # ------------------------------------------------------------------ #
    #  Public interface                                                   #
    # ------------------------------------------------------------------ #
    def get_plots(self) -> List[Dict[str, Any]]:
        """Generate all 4 analysis plots."""
        if not self._initialized:
            self.initialize()
        _, plots, _ = self._compute_all()
        return plots

    def get_state(self) -> Dict[str, Any]:
        """Return full simulation state with plots and metadata."""
        if not self._initialized:
            self.initialize()

        metadata, plots, _ = self._compute_all()

        return {
            "parameters": self.parameters.copy(),
            "plots": plots,
            "metadata": metadata,
        }

    def _compute_all(self) -> Tuple[Dict[str, Any],
                                     List[Dict[str, Any]],
                                     Dict[str, Any]]:
        """Central computation — returns (metadata, plots, internals)."""
        # Plant TF (with K)
        num, den = self._get_plant_tf()
        K = float(self.parameters["gain_K"])
        input_type = str(self.parameters["input_type"])
        A = float(self.parameters["input_magnitude"])
        preset = str(self.parameters["plant_preset"])

        # Cancel common s=0 factors for accurate type/constant computation.
        # Originals (num, den) kept for display; effective versions for theory.
        num_eff, den_eff = self._cancel_common_s_factors(num, den)

        # System type (on effective, cancellation-reduced plant)
        system_type = self._count_origin_poles(den_eff)

        # Error constants (on effective plant)
        error_constants = self._compute_error_constants(
            num_eff, den_eff, system_type
        )

        # Steady-state errors
        ss_errors = self._compute_steady_state_errors(
            error_constants, system_type, A
        )

        # Current ess for the selected input type
        current_ess = ss_errors[input_type]

        # CL poles & stability (on effective plant — avoids spurious
        # s=0 modes from cancelled pole-zero pairs)
        cl_poles, is_stable = self._compute_cl_poles(num_eff, den_eff)

        # OL poles/zeros for display (use ORIGINALS to show full plant)
        den_trimmed = np.trim_zeros(den, "f")
        ol_poles = np.roots(den_trimmed) if len(den_trimmed) > 1 else np.array([])
        num_trimmed = np.trim_zeros(num, "f")
        ol_zeros = np.roots(num_trimmed) if len(num_trimmed) > 1 else np.array([])

        # Time simulation (use effective — avoids unobservable s=0 modes)
        t_end = self._estimate_time_range(cl_poles, is_stable)
        num_cl = num_eff.copy()
        den_cl = np.polyadd(den_eff, num_eff)
        den_cl = np.trim_zeros(den_cl, "f")
        if len(den_cl) == 0:
            den_cl = np.array([1.0])
        sim = self._simulate_response(num_cl, den_cl, input_type, A,
                                      t_end, is_stable)

        # ess vs K sweep (base num without K applied)
        if preset != "custom" and preset in self._PRESETS:
            num_base = np.array(self._PRESETS[preset]["num"], dtype=float)
        else:
            num_base = self._parse_poly_string(self.parameters["plant_num"])
        ess_data = self._compute_ess_vs_K(num_base, den, A)

        # LaTeX strings
        plant_latex = self._format_plant_latex(
            num_base, den, K
        )
        fvt_latex = self._build_fvt_latex(
            input_type, system_type, error_constants, A,
            current_ess, is_stable,
        )

        # Display strings for error constants and ess
        ec_display = {k: self._display_value(v)
                      for k, v in error_constants.items()}
        ess_display = {k: self._display_value(v)
                       for k, v in ss_errors.items()}

        # ---- Build plots ---- #
        plots = [
            self._build_time_response_plot(sim, input_type, current_ess,
                                           is_stable),
            self._build_error_signal_plot(sim, current_ess, is_stable),
            self._build_ess_vs_gain_plot(ess_data, K),
            self._build_pole_zero_map(num, den, cl_poles, system_type,
                                      is_stable),
        ]

        # ---- Build metadata ---- #
        metadata: Dict[str, Any] = {
            "simulation_type": "steady_state_error",
            "system_type": system_type,
            "error_constants": {
                "Kp": error_constants["Kp"],
                "Kv": error_constants["Kv"],
                "Ka": error_constants["Ka"],
                "K_static": error_constants["K_static"],
            },
            "error_constants_display": ec_display,
            "steady_state_errors": {
                "step": ss_errors["step"],
                "ramp": ss_errors["ramp"],
                "parabolic": ss_errors["parabolic"],
            },
            "steady_state_errors_display": ess_display,
            "cl_stable": is_stable,
            "cl_poles": [{"real": float(np.real(p)),
                          "imag": float(np.imag(p))} for p in cl_poles],
            "ol_poles": [{"real": float(np.real(p)),
                          "imag": float(np.imag(p))} for p in ol_poles],
            "ol_zeros": [{"real": float(np.real(p)),
                          "imag": float(np.imag(p))} for p in ol_zeros],
            "plant_latex": plant_latex,
            "fvt_latex": fvt_latex,
            "fvt_valid": is_stable,
            "gain_K": K,
            "input_type": input_type,
            "input_magnitude": A,
            "preset_description": self._PRESET_DESCRIPTIONS.get(preset, ""),
        }

        return metadata, plots, {}
