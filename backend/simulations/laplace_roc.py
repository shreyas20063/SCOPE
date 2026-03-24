"""
Laplace Transform & s-Plane ROC Explorer Simulator

Interactive s-plane visualization exploring Laplace transforms, regions of convergence,
and how ROC determines causality. Shows how the same H(s) can correspond to
different time-domain signals (causal, anti-causal, two-sided) depending on
which ROC region is selected. The continuous-time twin of the Z Transform ROC Explorer.
"""

import numpy as np
from scipy import signal as sp_signal
from typing import Any, Dict, List, Optional
from .base_simulator import BaseSimulator


class LaplaceROCSimulator(BaseSimulator):
    """
    Laplace Transform & s-Plane ROC Explorer simulation.

    Parameters:
    - signal_family: Type of signal/system to explore
    - pole1_real, pole1_imag: Primary pole location
    - pole2_real, pole2_imag: Secondary pole location
    - roc_selection: Which ROC region to use
    - time_range: Symmetric time window ±T
    - num_points: Number of plot points
    - show_convergence: Toggle convergence test
    - sigma_test: σ value for convergence test
    - custom_num_coeffs, custom_den_coeffs: Custom H(s) coefficients
    """

    # Colors (matching project palette)
    POLE_COLOR = "#ef4444"
    ZERO_COLOR = "#3b82f6"
    JW_AXIS_COLOR = "#a855f7"
    ROC_FILL = "rgba(16, 185, 129, 0.10)"
    ROC_BOUNDARY = "#10b981"
    ROC_EXCLUDED = "rgba(239, 68, 68, 0.06)"
    SIGNAL_RIGHT = "#3b82f6"
    SIGNAL_LEFT = "#ef4444"
    CONVERGENCE_COLOR = "#f59e0b"
    GRID_COLOR = "rgba(148, 163, 184, 0.2)"
    ZEROLINE_COLOR = "rgba(148, 163, 184, 0.3)"
    LEGEND_BG = "rgba(15, 23, 42, 0.8)"
    LEGEND_BORDER = "rgba(148, 163, 184, 0.2)"

    # Numerical constants
    MAX_SIGNAL_CLIP = 50.0
    MAX_AXIS_RANGE = 6.0
    MIN_AXIS_RANGE = 2.0
    AXIS_PADDING = 0.5

    PARAMETER_SCHEMA = {
        "signal_family": {
            "type": "select",
            "options": [
                {"value": "right_exponential", "label": "Right-sided: e\u1d43\u1d57u(t)"},
                {"value": "left_exponential", "label": "Left-sided: -e\u1d43\u1d57u(-t)"},
                {"value": "two_sided", "label": "Two-sided: e\u207b\u1d43|t|"},
                {"value": "sum_exponentials", "label": "Sum: e\u1d56\u00b9\u1d57u(t) + e\u1d56\u00b2\u1d57u(t)"},
                {"value": "second_order", "label": "Second-order (complex poles)"},
                {"value": "custom_rational", "label": "Custom Rational H(s)"},
            ],
            "default": "right_exponential",
        },
        "pole1_real": {"type": "slider", "min": -5.0, "max": 5.0, "step": 0.1, "default": -1.0},
        "pole1_imag": {"type": "slider", "min": -5.0, "max": 5.0, "step": 0.1, "default": 0.0},
        "pole2_real": {"type": "slider", "min": -5.0, "max": 5.0, "step": 0.1, "default": 2.0},
        "pole2_imag": {"type": "slider", "min": -5.0, "max": 5.0, "step": 0.1, "default": 0.0},
        "roc_selection": {
            "type": "select",
            "options": [
                {"value": "auto_causal", "label": "Causal (right of rightmost pole)"},
                {"value": "auto_anticausal", "label": "Anti-causal (left of leftmost pole)"},
                {"value": "strip", "label": "Strip (between poles)"},
            ],
            "default": "auto_causal",
        },
        "time_range": {"type": "slider", "min": 1.0, "max": 10.0, "step": 0.5, "default": 5.0},
        "num_points": {"type": "slider", "min": 200, "max": 2000, "step": 100, "default": 500},
        "show_convergence": {"type": "checkbox", "default": False},
        "sigma_test": {"type": "slider", "min": -5.0, "max": 5.0, "step": 0.1, "default": 0.0},
        "custom_num_coeffs": {"type": "expression", "default": "1"},
        "custom_den_coeffs": {"type": "expression", "default": "1, 1"},
    }

    DEFAULT_PARAMS = {
        "signal_family": "right_exponential",
        "pole1_real": -1.0,
        "pole1_imag": 0.0,
        "pole2_real": 2.0,
        "pole2_imag": 0.0,
        "roc_selection": "auto_causal",
        "time_range": 5.0,
        "num_points": 500,
        "show_convergence": False,
        "sigma_test": 0.0,
        "custom_num_coeffs": "1",
        "custom_den_coeffs": "1, 1",
    }

    HUB_SLOTS = ['control']

    def __init__(self, simulation_id: str):
        super().__init__(simulation_id)
        self._poles: np.ndarray = np.array([])
        self._zeros: np.ndarray = np.array([])
        self._num_coeffs: np.ndarray = np.array([1.0])
        self._den_coeffs: np.ndarray = np.array([1.0, 1.0])
        self._pole_reals: List[float] = []
        self._roc_left: float = -float("inf")
        self._roc_right: float = float("inf")
        self._is_causal: bool = True
        self._is_anticausal: bool = False
        self._is_two_sided: bool = False
        self._is_stable: bool = True
        self._t: np.ndarray = np.array([])
        self._x_t: np.ndarray = np.array([])
        self._convergence_data: Optional[Dict] = None
        self._residues: np.ndarray = np.array([])
        self._residue_poles: np.ndarray = np.array([])
        self._revision_counter: int = 0

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
        old_family = self.parameters.get("signal_family")

        if name in self.parameters:
            self.parameters[name] = self._validate_param(name, value)

        # When signal_family changes, reset ROC and pole params to sane defaults
        if name == "signal_family" and value != old_family:
            self.parameters["roc_selection"] = "auto_causal"
            if value == "right_exponential":
                self.parameters["pole1_real"] = -1.0
                self.parameters["pole1_imag"] = 0.0
            elif value == "left_exponential":
                self.parameters["pole1_real"] = -1.0
                self.parameters["pole1_imag"] = 0.0
            elif value == "two_sided":
                self.parameters["pole1_real"] = -1.0
                self.parameters["pole1_imag"] = 0.0
                self.parameters["pole2_real"] = 1.0
                self.parameters["pole2_imag"] = 0.0
                self.parameters["roc_selection"] = "strip"
            elif value == "sum_exponentials":
                self.parameters["pole1_real"] = -1.0
                self.parameters["pole1_imag"] = 0.0
                self.parameters["pole2_real"] = 2.0
                self.parameters["pole2_imag"] = 0.0
            elif value == "second_order":
                self.parameters["pole1_real"] = -0.5
                self.parameters["pole1_imag"] = 2.0
                self.parameters["pole2_real"] = 0.0
                self.parameters["pole2_imag"] = 0.0

        self._compute()
        return self.get_state()

    def handle_action(self, action: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle custom button actions."""
        if action == "select_roc_region":
            region = params.get("region", "auto_causal") if params else "auto_causal"
            self.parameters["roc_selection"] = region
            self._compute()
        return self.get_state()

    def reset(self) -> Dict[str, Any]:
        """Reset to default parameters."""
        self.parameters = self.DEFAULT_PARAMS.copy()
        self._convergence_data = None
        self._initialized = True
        self._compute()
        return self.get_state()

    # =========================================================================
    # Core computation
    # =========================================================================

    def _parse_coeffs(self, expr_str: str) -> np.ndarray:
        """Parse comma-separated coefficient string into numpy array."""
        try:
            parts = [s.strip() for s in str(expr_str).split(",")]
            coeffs = [float(p) for p in parts if p]
            if not coeffs:
                return np.array([1.0])
            return np.array(coeffs)
        except (ValueError, TypeError):
            return np.array([1.0])

    def _compute(self) -> None:
        """Compute poles, zeros, ROC, time-domain signal, and convergence."""
        self._determine_system()
        self._compute_roc()
        self._compute_residues()
        self._compute_time_domain()
        self._compute_convergence()
        self._revision_counter += 1

    def _determine_system(self) -> None:
        """Determine poles, zeros, and H(s) coefficients from signal family."""
        family = self.parameters["signal_family"]

        if family in ("right_exponential", "left_exponential"):
            # Single real pole: H(s) = 1/(s - a)
            a = float(self.parameters["pole1_real"])
            self._poles = np.array([a], dtype=complex)
            self._zeros = np.array([])
            # Polynomial form: H(s) = 1 / (s - a) => num=[1], den=[1, -a]
            self._num_coeffs = np.array([1.0])
            self._den_coeffs = np.array([1.0, -a])

        elif family == "two_sided":
            # Two real poles: e^{-a|t|} = e^{-at}u(t) + e^{at}u(-t)
            # Poles at s = -a and s = a (where a > 0 ideally)
            p1 = float(self.parameters["pole1_real"])
            p2 = float(self.parameters["pole2_real"])
            self._poles = np.array([p1, p2], dtype=complex)
            self._zeros = np.array([])
            # H(s) = 1/(s-p1) + 1/(s-p2) = (2s - p1 - p2) / ((s-p1)(s-p2))
            # But for two-sided e^{-|t|} with poles at ±a:
            #   = 1/(s-p1) [right-sided part] + 1/(s-p2) [left-sided part]
            # Keep as sum of partial fractions
            den = np.polymul([1.0, -p1], [1.0, -p2])
            # Numerator for sum: (s-p2) + (s-p1) = 2s - (p1+p2)
            num = np.array([2.0, -(p1 + p2)])
            self._num_coeffs = np.real(num)
            self._den_coeffs = np.real(den)

        elif family == "sum_exponentials":
            # Two poles, both right-sided: e^{p1·t}u(t) + e^{p2·t}u(t)
            p1 = float(self.parameters["pole1_real"])
            p2 = float(self.parameters["pole2_real"])
            self._poles = np.array([p1, p2], dtype=complex)
            self._zeros = np.array([])
            den = np.polymul([1.0, -p1], [1.0, -p2])
            num = np.array([2.0, -(p1 + p2)])
            self._num_coeffs = np.real(num)
            self._den_coeffs = np.real(den)

        elif family == "second_order":
            # Complex conjugate poles: s = σ ± jω
            sigma = float(self.parameters["pole1_real"])
            omega = float(self.parameters["pole1_imag"])
            if abs(omega) < 1e-6:
                # Degenerate: two real poles at same location
                p1 = sigma
                self._poles = np.array([p1], dtype=complex)
                self._num_coeffs = np.array([1.0])
                self._den_coeffs = np.array([1.0, -p1])
            else:
                p1 = complex(sigma, omega)
                p2 = complex(sigma, -omega)
                self._poles = np.array([p1, p2])
                # H(s) = 1/((s-p1)(s-p2)) = 1/(s² - 2σs + σ² + ω²)
                den = np.polymul([1.0, -p1], [1.0, -p2])
                self._num_coeffs = np.array([1.0])
                self._den_coeffs = np.real(den)
            self._zeros = np.array([])

        elif family == "custom_rational":
            self._num_coeffs = self._parse_coeffs(self.parameters["custom_num_coeffs"])
            self._den_coeffs = self._parse_coeffs(self.parameters["custom_den_coeffs"])
            if len(self._den_coeffs) > 1:
                self._poles = np.roots(self._den_coeffs)
            else:
                self._poles = np.array([])
            if len(self._num_coeffs) > 1:
                self._zeros = np.roots(self._num_coeffs)
            else:
                self._zeros = np.array([])

        else:
            # Fallback
            self._poles = np.array([-1.0], dtype=complex)
            self._zeros = np.array([])
            self._num_coeffs = np.array([1.0])
            self._den_coeffs = np.array([1.0, 1.0])

    def _compute_roc(self) -> None:
        """Compute ROC boundaries based on pole real parts and selection."""
        if len(self._poles) == 0:
            self._pole_reals = []
            self._roc_left = -float("inf")
            self._roc_right = float("inf")
            self._is_causal = True
            self._is_anticausal = False
            self._is_two_sided = False
            self._is_stable = True
            return

        # Sorted unique pole real parts (the ROC boundaries in the s-plane)
        reals = sorted(set(np.round(np.real(self._poles), 6).tolist()))
        self._pole_reals = reals

        roc_sel = self.parameters["roc_selection"]
        family = self.parameters["signal_family"]

        # Force ROC for explicitly causal/anticausal signal families
        if family == "right_exponential":
            roc_sel = "auto_causal"
        elif family == "left_exponential":
            roc_sel = "auto_anticausal"
        elif family == "two_sided":
            roc_sel = "strip"

        if roc_sel == "auto_causal":
            # ROC: Re(s) > rightmost pole real part
            self._roc_left = max(reals)
            self._roc_right = float("inf")
        elif roc_sel == "auto_anticausal":
            # ROC: Re(s) < leftmost pole real part
            self._roc_left = -float("inf")
            self._roc_right = min(reals)
        elif roc_sel == "strip":
            if len(reals) >= 2:
                # ROC: leftmost_real < Re(s) < rightmost_real
                self._roc_left = min(reals)
                self._roc_right = max(reals)
            else:
                # Can't form strip with single pole real part, fall back to causal
                self._roc_left = max(reals)
                self._roc_right = float("inf")

        self._is_causal = self._roc_right == float("inf")
        self._is_anticausal = self._roc_left == -float("inf") and self._roc_right != float("inf")
        self._is_two_sided = (
            not self._is_causal
            and not self._is_anticausal
            and self._roc_left > -float("inf")
        )

        # Stability: ROC includes jω axis (Re(s) = 0)
        self._is_stable = (
            (self._roc_left < 0 or self._roc_left == -float("inf"))
            and (self._roc_right > 0 or self._roc_right == float("inf"))
        )

    def _compute_residues(self) -> None:
        """Compute partial fraction residues using scipy."""
        if len(self._poles) == 0:
            self._residues = np.array([])
            self._residue_poles = np.array([])
            return

        try:
            # scipy.signal.residue: partial fraction of b(s)/a(s) for CT
            r, p, k = sp_signal.residue(self._num_coeffs, self._den_coeffs)
            self._residues = r
            self._residue_poles = p
        except Exception:
            # Fallback: equal residues
            self._residues = np.ones(len(self._poles), dtype=complex)
            self._residue_poles = self._poles.copy()

    def _compute_time_domain(self) -> None:
        """Compute x(t) based on partial fractions and ROC selection."""
        T = float(self.parameters["time_range"])
        N = int(self.parameters["num_points"])
        t = np.linspace(-T, T, N)
        self._t = t

        x_t = np.zeros(N)

        # Masks for step functions: u(t) and u(-t)
        u_pos = t >= 0      # u(t): right-sided
        u_neg = t < 0        # u(-t-epsilon): left-sided (strictly t<0)

        for residue, pole in zip(self._residues, self._residue_poles):
            pole_real = float(np.real(pole))

            # Determine if this pole contributes right-sided or left-sided
            # based on whether its real part is inside or outside the ROC
            if self._is_causal:
                # All poles contribute right-sided: R_i * e^{p_i * t} * u(t)
                contribution = residue * np.exp(pole * t)
                contribution = np.where(u_pos, contribution, 0.0)
                x_t += np.real(contribution)

            elif self._is_anticausal:
                # All poles contribute left-sided: -R_i * e^{p_i * t} * u(-t)
                contribution = -residue * np.exp(pole * t)
                contribution = np.where(u_neg, contribution, 0.0)
                x_t += np.real(contribution)

            elif self._is_two_sided:
                # Pole real part <= roc_left -> right-sided contribution
                # Pole real part >= roc_right -> left-sided contribution
                if pole_real <= self._roc_left + 1e-9:
                    # This pole is to the left of ROC strip -> right-sided
                    contribution = residue * np.exp(pole * t)
                    contribution = np.where(u_pos, contribution, 0.0)
                    x_t += np.real(contribution)
                elif pole_real >= self._roc_right - 1e-9:
                    # This pole is to the right of ROC strip -> left-sided
                    contribution = -residue * np.exp(pole * t)
                    contribution = np.where(u_neg, contribution, 0.0)
                    x_t += np.real(contribution)
                else:
                    # Pole is inside ROC strip (shouldn't happen), treat as right-sided
                    contribution = residue * np.exp(pole * t)
                    contribution = np.where(u_pos, contribution, 0.0)
                    x_t += np.real(contribution)
            else:
                # Default causal
                contribution = residue * np.exp(pole * t)
                contribution = np.where(u_pos, contribution, 0.0)
                x_t += np.real(contribution)

        # Clip extreme values for display
        max_abs = np.max(np.abs(x_t)) if len(x_t) > 0 else 0
        if max_abs > self.MAX_SIGNAL_CLIP:
            x_t = np.clip(x_t, -self.MAX_SIGNAL_CLIP, self.MAX_SIGNAL_CLIP)

        self._x_t = x_t

    def _compute_convergence(self) -> None:
        """Compute convergence test data: |x(t) * e^{-σt}|."""
        if not self.parameters["show_convergence"]:
            self._convergence_data = None
            return

        sigma = float(self.parameters["sigma_test"])
        t = self._t
        x_t = self._x_t

        if len(t) == 0 or len(x_t) == 0:
            self._convergence_data = None
            return

        # Compute the integrand: x(t) * e^{-σt}
        damped = x_t * np.exp(-sigma * t)
        abs_damped = np.abs(damped)
        abs_original = np.abs(x_t)

        # Clip for display
        abs_damped = np.clip(abs_damped, 0, self.MAX_SIGNAL_CLIP * 2)
        abs_original = np.clip(abs_original, 0, self.MAX_SIGNAL_CLIP * 2)

        # Check if σ is in the ROC
        in_roc = (
            (self._roc_left == -float("inf") or sigma > self._roc_left)
            and (self._roc_right == float("inf") or sigma < self._roc_right)
        )

        # Estimate if integral converges by checking if damped signal decays
        # Check tail values for convergence indication
        tail_fraction = max(1, len(abs_damped) // 10)
        left_tail_mean = float(np.mean(abs_damped[:tail_fraction]))
        right_tail_mean = float(np.mean(abs_damped[-tail_fraction:]))
        mid_mean = float(np.mean(abs_damped[len(abs_damped) // 3: 2 * len(abs_damped) // 3]))
        converges = (left_tail_mean + right_tail_mean) < mid_mean * 3 if mid_mean > 1e-10 else True

        self._convergence_data = {
            "t": t.tolist(),
            "abs_original": abs_original.tolist(),
            "abs_damped": abs_damped.tolist(),
            "sigma": sigma,
            "in_roc": bool(in_roc),
            "converges": bool(converges),
        }

    # =========================================================================
    # Formatting helpers
    # =========================================================================

    def _format_hs(self) -> str:
        """Format H(s) expression as a readable string."""
        family = self.parameters["signal_family"]

        if family in ("right_exponential", "left_exponential"):
            a = float(self.parameters["pole1_real"])
            if a >= 0:
                return f"1 / (s - {a:.3g})"
            else:
                return f"1 / (s + {-a:.3g})"

        elif family in ("two_sided", "sum_exponentials"):
            p1 = float(self.parameters["pole1_real"])
            p2 = float(self.parameters["pole2_real"])
            term1 = f"(s - {p1:.3g})" if p1 >= 0 else f"(s + {-p1:.3g})"
            term2 = f"(s - {p2:.3g})" if p2 >= 0 else f"(s + {-p2:.3g})"
            return f"1/{term1} + 1/{term2}"

        elif family == "second_order":
            sigma = float(self.parameters["pole1_real"])
            omega = float(self.parameters["pole1_imag"])
            if abs(omega) < 1e-6:
                if sigma >= 0:
                    return f"1 / (s - {sigma:.3g})"
                else:
                    return f"1 / (s + {-sigma:.3g})"
            else:
                # 1 / (s² - 2σs + σ² + ω²)
                a = -2 * sigma
                b = sigma**2 + omega**2
                a_str = f"+ {a:.3g}" if a >= 0 else f"- {-a:.3g}"
                return f"1 / (s\u00b2 {a_str}s + {b:.3g})"

        elif family == "custom_rational":
            num_str = self.parameters["custom_num_coeffs"]
            den_str = self.parameters["custom_den_coeffs"]
            return f"B(s)/A(s) = [{num_str}] / [{den_str}]"

        return "H(s)"

    def _format_roc(self) -> str:
        """Format ROC description as readable string."""
        if len(self._pole_reals) == 0:
            return "Entire s-plane"

        if self._roc_right == float("inf") and self._roc_left > -float("inf"):
            return f"Re(s) > {self._roc_left:.4g}"
        elif self._roc_left == -float("inf") and self._roc_right < float("inf"):
            return f"Re(s) < {self._roc_right:.4g}"
        elif self._roc_left > -float("inf") and self._roc_right < float("inf"):
            return f"{self._roc_left:.4g} < Re(s) < {self._roc_right:.4g}"
        else:
            return "Entire s-plane"

    def _get_signal_title(self) -> str:
        """Build title string for time-domain plot."""
        family = self.parameters["signal_family"]

        if family == "right_exponential":
            a = float(self.parameters["pole1_real"])
            if a >= 0:
                return f"x(t) = e^({a:.3g}t) u(t)  (causal)"
            else:
                return f"x(t) = e^({a:.3g}t) u(t)  (causal)"

        elif family == "left_exponential":
            a = float(self.parameters["pole1_real"])
            return f"x(t) = -e^({a:.3g}t) u(-t)  (anti-causal)"

        elif family == "two_sided":
            p1 = float(self.parameters["pole1_real"])
            p2 = float(self.parameters["pole2_real"])
            return f"x(t) = e^({p1:.2g}t)u(t) + (-e^({p2:.2g}t))u(-t)  (two-sided)"

        elif family == "sum_exponentials":
            p1 = float(self.parameters["pole1_real"])
            p2 = float(self.parameters["pole2_real"])
            causality = "causal" if self._is_causal else (
                "anti-causal" if self._is_anticausal else "two-sided"
            )
            return f"x(t): poles at s={p1:.2g}, {p2:.2g}  ({causality})"

        elif family == "second_order":
            sigma = float(self.parameters["pole1_real"])
            omega = float(self.parameters["pole1_imag"])
            if abs(omega) < 1e-6:
                return f"x(t) = e^({sigma:.2g}t) u(t)  (causal)"
            else:
                causality = "causal" if self._is_causal else "anti-causal"
                return f"x(t) = e^({sigma:.2g}t)cos({abs(omega):.2g}t) u(t)  ({causality})"

        causality = "causal" if self._is_causal else (
            "anti-causal" if self._is_anticausal else "two-sided"
        )
        return f"x(t)  ({causality})"

    def _format_complex(self, z: complex) -> str:
        """Format a complex number for display."""
        if abs(z.imag) < 1e-6:
            return f"{z.real:.4g}"
        elif abs(z.real) < 1e-6:
            return f"{z.imag:.4g}j"
        else:
            sign = "+" if z.imag >= 0 else "-"
            return f"{z.real:.3g} {sign} {abs(z.imag):.3g}j"

    # =========================================================================
    # Plot generation
    # =========================================================================

    def get_plots(self) -> List[Dict[str, Any]]:
        """Generate all Plotly plot dictionaries."""
        if not self._initialized:
            self.initialize()

        plots = [
            self._create_s_plane_plot(),
            self._create_time_domain_plot(),
        ]
        if self.parameters["show_convergence"] and self._convergence_data is not None:
            plots.append(self._create_convergence_plot())
        return plots

    def _compute_s_plane_range(self) -> float:
        """Compute dynamic axis range based on poles, zeros, and ROC."""
        max_r = self.MIN_AXIS_RANGE
        for p in self._poles:
            max_r = max(max_r, abs(p.real) + self.AXIS_PADDING)
            max_r = max(max_r, abs(p.imag) + self.AXIS_PADDING)
        for z in self._zeros:
            max_r = max(max_r, abs(z.real) + self.AXIS_PADDING)
            max_r = max(max_r, abs(z.imag) + self.AXIS_PADDING)
        if self._roc_left > -float("inf"):
            max_r = max(max_r, abs(self._roc_left) + self.AXIS_PADDING)
        if self._roc_right < float("inf"):
            max_r = max(max_r, abs(self._roc_right) + self.AXIS_PADDING)
        return min(max_r, self.MAX_AXIS_RANGE)

    def _create_s_plane_plot(self) -> Dict[str, Any]:
        """Create s-plane plot with poles, zeros, jω axis, and ROC."""
        traces = []
        axis_range = self._compute_s_plane_range()

        # jω axis (the CT stability boundary, like unit circle in z-plane)
        traces.append({
            "x": [0, 0],
            "y": [-axis_range, axis_range],
            "type": "scatter",
            "mode": "lines",
            "line": {"color": self.JW_AXIS_COLOR, "width": 2.5, "dash": "dash"},
            "name": "j\u03c9 axis (stability boundary)",
            "hoverinfo": "skip",
        })

        # σ axis (real axis)
        traces.append({
            "x": [-axis_range, axis_range],
            "y": [0, 0],
            "type": "scatter",
            "mode": "lines",
            "line": {"color": self.ZEROLINE_COLOR, "width": 1},
            "name": "\u03c3 axis (real)",
            "showlegend": False,
            "hoverinfo": "skip",
        })

        # ROC boundary vertical lines
        if self._roc_left > -float("inf"):
            traces.append({
                "x": [self._roc_left, self._roc_left],
                "y": [-axis_range, axis_range],
                "type": "scatter",
                "mode": "lines",
                "line": {"color": self.ROC_BOUNDARY, "width": 2},
                "name": f"ROC boundary Re(s) = {self._roc_left:.3g}",
                "hoverinfo": "skip",
            })

        if self._roc_right < float("inf"):
            traces.append({
                "x": [self._roc_right, self._roc_right],
                "y": [-axis_range, axis_range],
                "type": "scatter",
                "mode": "lines",
                "line": {"color": self.ROC_BOUNDARY, "width": 2},
                "name": f"ROC boundary Re(s) = {self._roc_right:.3g}",
                "hoverinfo": "skip",
            })

        # Pole markers
        for i, pole in enumerate(self._poles):
            pole_label = self._format_complex(pole)
            traces.append({
                "x": [float(pole.real)],
                "y": [float(pole.imag)],
                "type": "scatter",
                "mode": "markers+text",
                "marker": {
                    "symbol": "x",
                    "size": 16,
                    "color": self.POLE_COLOR,
                    "line": {"width": 3, "color": self.POLE_COLOR},
                },
                "text": [f"p{i + 1}"],
                "textposition": "top center",
                "textfont": {"color": self.POLE_COLOR, "size": 10},
                "name": f"Pole {i + 1}: s = {pole_label}",
                "showlegend": True,
                "hovertemplate": f"Pole {i + 1}<br>s = {pole_label}<br>Re(s) = {pole.real:.4f}<extra></extra>",
            })

        # Zero markers
        for i, zero in enumerate(self._zeros):
            if abs(zero) < 1e-10:
                continue
            zero_label = self._format_complex(zero)
            traces.append({
                "x": [float(zero.real)],
                "y": [float(zero.imag)],
                "type": "scatter",
                "mode": "markers",
                "marker": {
                    "symbol": "circle-open",
                    "size": 14,
                    "color": self.ZERO_COLOR,
                    "line": {"width": 3, "color": self.ZERO_COLOR},
                },
                "name": f"Zero {i + 1}: s = {zero_label}",
                "showlegend": True,
                "hovertemplate": f"Zero {i + 1}<br>s = {zero_label}<extra></extra>",
            })

        # Build ROC shapes
        shapes = self._get_roc_shapes(axis_range)

        # Fingerprint uirevision from system-defining parameters
        family = self.parameters["signal_family"]
        p1r = self.parameters["pole1_real"]
        p1i = self.parameters["pole1_imag"]
        p2r = self.parameters["pole2_real"]
        roc = self.parameters["roc_selection"]
        ui_fingerprint = f"s_plane-{family}-{p1r}-{p1i}-{p2r}-{roc}"

        return {
            "id": "s_plane",
            "title": "s-Plane: Poles, Zeros & ROC",
            "data": traces,
            "layout": {
                "xaxis": {
                    "title": "\u03c3 (Real)",
                    "range": [-axis_range, axis_range],
                    "scaleanchor": "y",
                    "scaleratio": 1,
                    "constrain": "domain",
                    "showgrid": True,
                    "gridcolor": self.GRID_COLOR,
                    "zeroline": False,
                    "fixedrange": False,
                    "color": "#f1f5f9",
                },
                "yaxis": {
                    "title": "j\u03c9 (Imaginary)",
                    "range": [-axis_range, axis_range],
                    "constrain": "domain",
                    "showgrid": True,
                    "gridcolor": self.GRID_COLOR,
                    "zeroline": False,
                    "fixedrange": False,
                    "color": "#f1f5f9",
                },
                "legend": {
                    "x": 0.02, "y": 0.98,
                    "xanchor": "left", "yanchor": "top",
                    "bgcolor": self.LEGEND_BG,
                    "bordercolor": self.LEGEND_BORDER,
                    "borderwidth": 1,
                    "font": {"size": 10, "color": "#94a3b8"},
                },
                "margin": {"l": 60, "r": 30, "t": 50, "b": 50},
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)",
                "font": {"family": "Inter, sans-serif", "size": 12, "color": "#f1f5f9"},
                "shapes": shapes,
                "uirevision": ui_fingerprint,
            },
        }

    def _get_roc_shapes(self, axis_range: float) -> List[Dict[str, Any]]:
        """Build Plotly shapes for ROC shading (vertical strips)."""
        shapes = []

        if len(self._pole_reals) == 0:
            return shapes

        ar = axis_range

        if self._roc_right == float("inf") and self._roc_left > -float("inf"):
            # Causal: ROC is Re(s) > roc_left
            # Valid region (right of boundary)
            shapes.append({
                "type": "rect",
                "x0": self._roc_left, "y0": -ar,
                "x1": ar, "y1": ar,
                "fillcolor": self.ROC_FILL,
                "line": {"width": 0},
                "layer": "below",
            })
            # Excluded region (left of boundary)
            shapes.append({
                "type": "rect",
                "x0": -ar, "y0": -ar,
                "x1": self._roc_left, "y1": ar,
                "fillcolor": self.ROC_EXCLUDED,
                "line": {"width": 0},
                "layer": "below",
            })

        elif self._roc_left == -float("inf") and self._roc_right < float("inf"):
            # Anti-causal: ROC is Re(s) < roc_right
            # Valid region (left of boundary)
            shapes.append({
                "type": "rect",
                "x0": -ar, "y0": -ar,
                "x1": self._roc_right, "y1": ar,
                "fillcolor": self.ROC_FILL,
                "line": {"width": 0},
                "layer": "below",
            })
            # Excluded region (right of boundary)
            shapes.append({
                "type": "rect",
                "x0": self._roc_right, "y0": -ar,
                "x1": ar, "y1": ar,
                "fillcolor": self.ROC_EXCLUDED,
                "line": {"width": 0},
                "layer": "below",
            })

        elif self._roc_left > -float("inf") and self._roc_right < float("inf"):
            # Strip ROC: roc_left < Re(s) < roc_right
            # Valid region (between boundaries)
            shapes.append({
                "type": "rect",
                "x0": self._roc_left, "y0": -ar,
                "x1": self._roc_right, "y1": ar,
                "fillcolor": self.ROC_FILL,
                "line": {"width": 0},
                "layer": "below",
            })
            # Excluded left
            shapes.append({
                "type": "rect",
                "x0": -ar, "y0": -ar,
                "x1": self._roc_left, "y1": ar,
                "fillcolor": self.ROC_EXCLUDED,
                "line": {"width": 0},
                "layer": "below",
            })
            # Excluded right
            shapes.append({
                "type": "rect",
                "x0": self._roc_right, "y0": -ar,
                "x1": ar, "y1": ar,
                "fillcolor": self.ROC_EXCLUDED,
                "line": {"width": 0},
                "layer": "below",
            })

        return shapes

    def _create_time_domain_plot(self) -> Dict[str, Any]:
        """Create continuous x(t) waveform plot."""
        traces = []

        if len(self._t) > 0 and len(self._x_t) > 0:
            t = self._t
            x = self._x_t

            # Split into negative and positive time for color coding
            neg_mask = t < 0
            pos_mask = t >= 0

            # Left-sided part (t < 0) in red
            if np.any(neg_mask) and np.any(np.abs(x[neg_mask]) > 1e-12):
                traces.append({
                    "x": t[neg_mask].tolist(),
                    "y": x[neg_mask].tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "line": {"color": self.SIGNAL_LEFT, "width": 2.5},
                    "name": "Left-sided (t < 0)",
                    "hovertemplate": "t = %{x:.3f}<br>x(t) = %{y:.4f}<extra></extra>",
                })

            # Right-sided part (t ≥ 0) in blue
            if np.any(pos_mask) and np.any(np.abs(x[pos_mask]) > 1e-12):
                traces.append({
                    "x": t[pos_mask].tolist(),
                    "y": x[pos_mask].tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "line": {"color": self.SIGNAL_RIGHT, "width": 2.5},
                    "name": "Right-sided (t \u2265 0)",
                    "hovertemplate": "t = %{x:.3f}<br>x(t) = %{y:.4f}<extra></extra>",
                })

        # Fingerprint
        family = self.parameters["signal_family"]
        p1r = self.parameters["pole1_real"]
        p1i = self.parameters["pole1_imag"]
        p2r = self.parameters["pole2_real"]
        roc = self.parameters["roc_selection"]
        ui_fingerprint = f"time_domain-{family}-{p1r}-{p1i}-{p2r}-{roc}"

        return {
            "id": "time_domain",
            "title": self._get_signal_title(),
            "data": traces,
            "layout": {
                "xaxis": {
                    "title": "Time t [s]",
                    "showgrid": True,
                    "gridcolor": self.GRID_COLOR,
                    "zeroline": True,
                    "zerolinecolor": self.ZEROLINE_COLOR,
                    "zerolinewidth": 1.5,
                    "autorange": True,
                    "fixedrange": False,
                    "color": "#f1f5f9",
                },
                "yaxis": {
                    "title": "x(t)",
                    "showgrid": True,
                    "gridcolor": self.GRID_COLOR,
                    "zeroline": True,
                    "zerolinecolor": self.ZEROLINE_COLOR,
                    "zerolinewidth": 1.5,
                    "autorange": True,
                    "fixedrange": False,
                    "color": "#f1f5f9",
                },
                "legend": {
                    "x": 0.98, "y": 0.98,
                    "xanchor": "right", "yanchor": "top",
                    "bgcolor": self.LEGEND_BG,
                    "bordercolor": self.LEGEND_BORDER,
                    "borderwidth": 1,
                    "font": {"size": 11, "color": "#94a3b8"},
                },
                "margin": {"l": 60, "r": 30, "t": 50, "b": 55},
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)",
                "font": {"family": "Inter, sans-serif", "size": 12, "color": "#f1f5f9"},
                "showlegend": True,
                "uirevision": ui_fingerprint,
            },
        }

    def _create_convergence_plot(self) -> Dict[str, Any]:
        """Create convergence test plot: |x(t)| vs |x(t)e^{-σt}|."""
        data = self._convergence_data
        if data is None:
            return {
                "id": "convergence",
                "title": "Convergence Test (enable toggle)",
                "data": [],
                "layout": {},
            }

        traces = []

        # Original |x(t)| in faded blue
        traces.append({
            "x": data["t"],
            "y": data["abs_original"],
            "type": "scatter",
            "mode": "lines",
            "line": {"color": "rgba(59, 130, 246, 0.3)", "width": 1.5},
            "name": "|x(t)|",
            "hovertemplate": "t = %{x:.3f}<br>|x(t)| = %{y:.4f}<extra></extra>",
        })

        # Damped |x(t)e^{-σt}| in amber
        sigma = data["sigma"]
        traces.append({
            "x": data["t"],
            "y": data["abs_damped"],
            "type": "scatter",
            "mode": "lines",
            "line": {"color": self.CONVERGENCE_COLOR, "width": 2.5},
            "name": f"|x(t)\u00b7e^(-{sigma:.2g}t)|",
            "hovertemplate": "t = %{x:.3f}<br>|x(t)e^{-\u03c3t}| = %{y:.4f}<extra></extra>",
        })

        # Convergence annotation
        converges = data["converges"]
        in_roc = data["in_roc"]
        status = "\u2713 Converges" if converges else "\u2717 Diverges"
        roc_text = "(\u03c3 in ROC)" if in_roc else "(\u03c3 NOT in ROC)"

        return {
            "id": "convergence",
            "title": f"Convergence Test at \u03c3 = {sigma:.2g}: {status} {roc_text}",
            "data": traces,
            "layout": {
                "xaxis": {
                    "title": "Time t [s]",
                    "showgrid": True,
                    "gridcolor": self.GRID_COLOR,
                    "zeroline": True,
                    "zerolinecolor": self.ZEROLINE_COLOR,
                    "autorange": True,
                    "fixedrange": False,
                    "color": "#f1f5f9",
                },
                "yaxis": {
                    "title": "Magnitude",
                    "showgrid": True,
                    "gridcolor": self.GRID_COLOR,
                    "zeroline": True,
                    "zerolinecolor": self.ZEROLINE_COLOR,
                    "autorange": True,
                    "fixedrange": False,
                    "color": "#f1f5f9",
                },
                "legend": {
                    "x": 0.98, "y": 0.98,
                    "xanchor": "right", "yanchor": "top",
                    "bgcolor": self.LEGEND_BG,
                    "bordercolor": self.LEGEND_BORDER,
                    "borderwidth": 1,
                    "font": {"size": 11, "color": "#94a3b8"},
                },
                "margin": {"l": 60, "r": 30, "t": 50, "b": 55},
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)",
                "font": {"family": "Inter, sans-serif", "size": 12, "color": "#f1f5f9"},
                "showlegend": True,
                "uirevision": f"convergence-{sigma}",
            },
        }

    # =========================================================================
    # Hub integration
    # =========================================================================

    def to_hub_data(self):
        """Export custom TF coefficients (custom_num_coeffs / custom_den_coeffs)."""
        num = self._parse_coeffs(str(self.parameters.get('custom_num_coeffs', '1')))
        den = self._parse_coeffs(str(self.parameters.get('custom_den_coeffs', '1, 1')))
        if len(num) > 0 and len(den) > 0:
            return {
                "source": "tf",
                "domain": self.HUB_DOMAIN,
                "dimensions": self.HUB_DIMENSIONS,
                "tf": {"num": list(num), "den": list(den), "variable": "s"},
            }
        return None

    # =========================================================================
    # State
    # =========================================================================

    def get_state(self) -> Dict[str, Any]:
        """Return current simulation state with metadata for custom viewer."""
        if not self._initialized:
            self.initialize()

        state = super().get_state()

        state["metadata"] = {
            "simulation_type": "laplace_roc",
            "hub_slots": self.HUB_SLOTS,
            "hub_domain": self.HUB_DOMAIN,
            "hub_dimensions": self.HUB_DIMENSIONS,
            "sticky_controls": True,
            "hs_expression": self._format_hs(),
            "roc_description": self._format_roc(),
            "causality": "Causal" if self._is_causal else (
                "Anti-causal" if self._is_anticausal else "Two-sided"
            ),
            "is_stable": self._is_stable,
            "stability_text": (
                "Stable (ROC includes j\u03c9 axis)" if self._is_stable
                else "Unstable (ROC excludes j\u03c9 axis)"
            ),
            "poles": [
                {
                    "real": float(p.real),
                    "imag": float(p.imag),
                    "magnitude": float(abs(p)),
                }
                for p in self._poles
            ],
            "zeros": [
                {
                    "real": float(z.real),
                    "imag": float(z.imag),
                }
                for z in self._zeros
            ],
            "pole_reals": [float(r) for r in self._pole_reals],
            "roc_left": float(self._roc_left) if self._roc_left != -float("inf") else None,
            "roc_right": float(self._roc_right) if self._roc_right != float("inf") else None,
        }

        return state
