"""
Z Transform & ROC Explorer Simulator

Interactive z-plane visualization exploring Z transforms, regions of convergence,
and how ROC determines causality. Shows how the same H(z) can correspond to
different time-domain signals (causal, anti-causal, two-sided) depending on
which ROC region is selected.
"""

import numpy as np
from scipy import signal as sp_signal
from typing import Any, Dict, List, Optional
from .base_simulator import BaseSimulator


class ZTransformROCSimulator(BaseSimulator):
    """
    Z Transform & ROC Explorer simulation.

    Parameters:
    - signal_family: Type of signal/system to explore
    - pole_real, pole_imag: Primary pole location
    - pole2_real, pole2_imag: Secondary pole location (two-sided, second-order)
    - r_magnitude, omega_0: Damped sinusoid parameters
    - roc_selection: Which ROC region to use
    - num_samples: Number of discrete samples
    - show_convergence: Toggle convergence visualization
    - convergence_terms: Number of partial sum terms
    - custom_num_coeffs, custom_den_coeffs: Custom H(z) coefficients
    """

    # Colors
    POLE_COLOR = "#ef4444"
    ZERO_COLOR = "#3b82f6"
    UNIT_CIRCLE_COLOR = "#a855f7"
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
    FILL_STABLE = "rgba(52, 211, 153, 0.08)"

    PARAMETER_SCHEMA = {
        "signal_family": {
            "type": "select",
            "options": [
                {"value": "right_exponential", "label": "Right-sided: a\u207fu[n]"},
                {"value": "left_exponential", "label": "Left-sided: -a\u207fu[-n-1]"},
                {"value": "two_sided", "label": "Two-sided Exponential"},
                {"value": "second_order", "label": "Second-order (2 poles)"},
                {"value": "damped_sinusoid", "label": "Damped Sinusoid: r\u207fcos(\u03c9\u2080n)u[n]"},
                {"value": "custom_rational", "label": "Custom Rational H(z)"},
            ],
            "default": "right_exponential",
        },
        "pole_real": {"type": "slider", "min": -1.5, "max": 1.5, "step": 0.01, "default": 0.7},
        "pole_imag": {"type": "slider", "min": -1.5, "max": 1.5, "step": 0.01, "default": 0.0},
        "pole2_real": {"type": "slider", "min": -1.5, "max": 1.5, "step": 0.01, "default": -0.5},
        "pole2_imag": {"type": "slider", "min": -1.5, "max": 1.5, "step": 0.01, "default": 0.0},
        "r_magnitude": {"type": "slider", "min": 0.1, "max": 1.5, "step": 0.01, "default": 0.8},
        "omega_0": {"type": "slider", "min": 0.1, "max": 3.14, "step": 0.01, "default": 0.785},
        "roc_selection": {
            "type": "select",
            "options": [
                {"value": "auto_causal", "label": "Causal (outside all poles)"},
                {"value": "auto_anticausal", "label": "Anti-causal (inside all poles)"},
                {"value": "annular", "label": "Annular Ring (two-sided)"},
            ],
            "default": "auto_causal",
        },
        "num_samples": {"type": "slider", "min": 10, "max": 60, "step": 1, "default": 30},
        "show_convergence": {"type": "checkbox", "default": False},
        "convergence_terms": {"type": "slider", "min": 1, "max": 50, "step": 1, "default": 10},
        "custom_num_coeffs": {"type": "expression", "default": "1"},
        "custom_den_coeffs": {"type": "expression", "default": "1, -0.7"},
    }

    DEFAULT_PARAMS = {
        "signal_family": "right_exponential",
        "pole_real": 0.7,
        "pole_imag": 0.0,
        "pole2_real": -0.5,
        "pole2_imag": 0.0,
        "r_magnitude": 0.8,
        "omega_0": 0.785,
        "roc_selection": "auto_causal",
        "num_samples": 30,
        "show_convergence": False,
        "convergence_terms": 10,
        "custom_num_coeffs": "1",
        "custom_den_coeffs": "1, -0.7",
    }

    HUB_SLOTS = ['control']
    HUB_DOMAIN = "dt"

    def __init__(self, simulation_id: str):
        super().__init__(simulation_id)
        self._poles: np.ndarray = np.array([])
        self._zeros: np.ndarray = np.array([])
        self._num_coeffs: np.ndarray = np.array([1.0])
        self._den_coeffs: np.ndarray = np.array([1.0, -0.7])
        self._pole_radii: List[float] = []
        self._roc_inner: float = 0.0
        self._roc_outer: float = float("inf")
        self._is_causal: bool = True
        self._is_anticausal: bool = False
        self._is_two_sided: bool = False
        self._is_stable: bool = True
        self._n_full: np.ndarray = np.array([])
        self._x_full: np.ndarray = np.array([])
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
            # Reset pole sliders to defaults for clean start
            self.parameters["pole_real"] = self.DEFAULT_PARAMS["pole_real"]
            self.parameters["pole_imag"] = self.DEFAULT_PARAMS["pole_imag"]
            self.parameters["pole2_real"] = self.DEFAULT_PARAMS["pole2_real"]
            self.parameters["pole2_imag"] = self.DEFAULT_PARAMS["pole2_imag"]
            self.parameters["r_magnitude"] = self.DEFAULT_PARAMS["r_magnitude"]
            self.parameters["omega_0"] = self.DEFAULT_PARAMS["omega_0"]

        self._compute()
        return self.get_state()

    def handle_action(self, action: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle custom button actions."""
        if action == "select_roc_region":
            region_idx = params.get("region_index", 0) if params else 0
            self._apply_roc_region(region_idx)
            self._compute()
        return self.get_state()

    def reset(self) -> Dict[str, Any]:
        """Reset to default parameters."""
        self.parameters = self.DEFAULT_PARAMS.copy()
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
        """Determine poles, zeros, and H(z) coefficients from signal family."""
        family = self.parameters["signal_family"]

        if family in ("right_exponential", "left_exponential"):
            a = complex(self.parameters["pole_real"], self.parameters["pole_imag"])
            self._poles = np.array([a])
            if abs(a.imag) > 1e-6:
                self._poles = np.array([a, np.conj(a)])
            self._zeros = np.array([])
            # H(z) = 1 / (1 - a*z^{-1})  =>  num=[1], den=[1, -a]
            if len(self._poles) == 2:
                self._num_coeffs = np.array([1.0])
                self._den_coeffs = np.real(np.polymul([1.0], np.polymul(
                    [1.0, -self._poles[0]], [1.0, -self._poles[1]]
                )))
            else:
                self._num_coeffs = np.array([1.0])
                self._den_coeffs = np.array([1.0, -float(a.real)])

        elif family == "two_sided":
            a = complex(self.parameters["pole_real"], self.parameters["pole_imag"])
            b = complex(self.parameters["pole2_real"], self.parameters["pole2_imag"])
            poles = [a]
            if abs(a.imag) > 1e-6:
                poles.append(np.conj(a))
            poles.append(b)
            if abs(b.imag) > 1e-6:
                poles.append(np.conj(b))
            self._poles = np.array(poles)
            self._zeros = np.array([])
            den = np.array([1.0])
            for p in self._poles:
                den = np.polymul(den, [1.0, -p])
            self._den_coeffs = np.real(den)
            self._num_coeffs = np.array([1.0])

        elif family == "second_order":
            p1 = complex(self.parameters["pole_real"], self.parameters["pole_imag"])
            p2 = complex(self.parameters["pole2_real"], self.parameters["pole2_imag"])
            poles = [p1]
            if abs(p1.imag) > 1e-6:
                poles = [p1, np.conj(p1)]
            else:
                poles.append(p2)
                if abs(p2.imag) > 1e-6:
                    poles.append(np.conj(p2))
            self._poles = np.array(poles)
            self._zeros = np.array([])
            den = np.array([1.0])
            for p in self._poles:
                den = np.polymul(den, [1.0, -p])
            self._den_coeffs = np.real(den)
            self._num_coeffs = np.array([1.0])

        elif family == "damped_sinusoid":
            r = float(self.parameters["r_magnitude"])
            w0 = float(self.parameters["omega_0"])
            p1 = r * np.exp(1j * w0)
            p2 = r * np.exp(-1j * w0)
            self._poles = np.array([p1, p2])
            # H(z) = (1 - r*cos(w0)*z^{-1}) / (1 - 2*r*cos(w0)*z^{-1} + r^2*z^{-2})
            self._num_coeffs = np.array([1.0, -r * np.cos(w0)])
            self._den_coeffs = np.array([1.0, -2.0 * r * np.cos(w0), r ** 2])
            self._zeros = np.roots(self._num_coeffs)

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
            self._poles = np.array([0.7])
            self._zeros = np.array([])
            self._num_coeffs = np.array([1.0])
            self._den_coeffs = np.array([1.0, -0.7])

    def _compute_roc(self) -> None:
        """Compute ROC boundaries based on pole radii and selection."""
        if len(self._poles) == 0:
            self._pole_radii = []
            self._roc_inner = 0.0
            self._roc_outer = float("inf")
            self._is_causal = True
            self._is_anticausal = False
            self._is_two_sided = False
            self._is_stable = True
            return

        # Sorted unique pole radii
        radii = sorted(set(np.round(np.abs(self._poles), 6).tolist()))
        self._pole_radii = radii

        roc_sel = self.parameters["roc_selection"]
        family = self.parameters["signal_family"]

        # Force ROC for explicitly causal/anticausal signal families
        if family == "right_exponential":
            roc_sel = "auto_causal"
        elif family == "left_exponential":
            roc_sel = "auto_anticausal"

        if roc_sel == "auto_causal":
            self._roc_inner = max(radii)
            self._roc_outer = float("inf")
        elif roc_sel == "auto_anticausal":
            self._roc_inner = 0.0
            self._roc_outer = min(radii)
        elif roc_sel == "annular":
            if len(radii) >= 2:
                self._roc_inner = min(radii)
                self._roc_outer = max(radii)
            else:
                # Can't form annular with single radius, fall back to causal
                self._roc_inner = max(radii)
                self._roc_outer = float("inf")

        self._is_causal = self._roc_outer == float("inf")
        self._is_anticausal = self._roc_inner == 0.0 and self._roc_outer != float("inf")
        self._is_two_sided = (
            not self._is_causal
            and not self._is_anticausal
            and self._roc_inner > 0
        )

        # Stability: ROC includes unit circle
        self._is_stable = self._roc_inner < 1.0 and (
            self._roc_outer == float("inf") or self._roc_outer > 1.0
        )

    def _compute_residues(self) -> None:
        """Compute partial fraction residues using scipy."""
        if len(self._poles) == 0:
            self._residues = np.array([])
            self._residue_poles = np.array([])
            return

        try:
            # residuez: partial fraction of b(z)/a(z) in z^{-1} powers
            r, p, k = sp_signal.residuez(self._num_coeffs, self._den_coeffs)
            self._residues = r
            self._residue_poles = p
        except Exception:
            # Fallback: simple residues for first-order poles
            self._residues = np.ones(len(self._poles))
            self._residue_poles = self._poles.copy()

    def _compute_time_domain(self) -> None:
        """Compute inverse Z-transform based on ROC selection."""
        N = int(self.parameters["num_samples"])
        n_pos = np.arange(0, N)
        n_neg = np.arange(-N, 0)

        x_pos = np.zeros(N)
        x_neg = np.zeros(N)

        for i, (residue, pole) in enumerate(zip(self._residues, self._residue_poles)):
            r_pole = abs(pole)

            # Determine if this pole is inside or outside the ROC
            # Inside ROC boundary -> right-sided (causal) contribution
            # Outside ROC boundary -> left-sided (anti-causal) contribution
            if r_pole < self._roc_inner + 1e-9 or (
                self._roc_outer == float("inf") and r_pole <= self._roc_inner + 1e-9
            ):
                # Pole is inside ROC -> right-sided: residue * pole^n * u[n]
                contribution = residue * np.power(pole, n_pos)
                x_pos += np.real(contribution)
            elif self._roc_outer != float("inf") and r_pole > self._roc_outer - 1e-9:
                # Pole is outside ROC -> left-sided: -residue * pole^n * u[-n-1]
                contribution = -residue * np.power(pole, n_neg)
                x_neg += np.real(contribution)
            elif self._is_causal:
                # Default causal: right-sided
                contribution = residue * np.power(pole, n_pos)
                x_pos += np.real(contribution)
            else:
                # Default anti-causal: left-sided
                contribution = -residue * np.power(pole, n_neg)
                x_neg += np.real(contribution)

        # Combine
        has_left = np.any(np.abs(x_neg) > 1e-12)
        has_right = np.any(np.abs(x_pos) > 1e-12)

        if has_left and has_right:
            self._n_full = np.concatenate([n_neg, n_pos])
            self._x_full = np.concatenate([x_neg, x_pos])
        elif has_left:
            self._n_full = n_neg
            self._x_full = x_neg
        else:
            self._n_full = n_pos
            self._x_full = x_pos

        # Clip extreme values for display (keep readable)
        if len(self._x_full) > 0:
            max_val = np.max(np.abs(self._x_full))
            if max_val > 100:
                # For divergent signals, clip to keep plot readable
                clip_val = min(max_val, 100.0)
                self._x_full = np.clip(self._x_full, -clip_val, clip_val)

    def _compute_convergence(self) -> None:
        """Compute partial sum convergence data."""
        if not self.parameters["show_convergence"]:
            self._convergence_data = None
            return

        K = int(self.parameters["convergence_terms"])
        # Evaluate at z = e^{j*pi/4} on the unit circle
        z_eval = np.exp(1j * np.pi / 4)
        z_eval_r = abs(z_eval)  # = 1.0

        # Check if z_eval is in the ROC
        in_roc = self._roc_inner < z_eval_r and (
            self._roc_outer == float("inf") or z_eval_r < self._roc_outer
        )

        # Only compute right-sided partial sums for now
        N = min(K, len(self._x_full))
        # Use the right-sided portion of x[n] for n >= 0
        n_pos_mask = self._n_full >= 0
        x_right = self._x_full[n_pos_mask]

        partial_sums_real = []
        partial_sums_imag = []
        running_sum = 0.0 + 0.0j
        k_values = []

        for k in range(min(K, len(x_right))):
            running_sum += x_right[k] * z_eval ** (-k)
            partial_sums_real.append(float(running_sum.real))
            partial_sums_imag.append(float(running_sum.imag))
            k_values.append(k)

        # Closed form H(z_eval)
        try:
            hz_val = np.polyval(self._num_coeffs, z_eval) / np.polyval(self._den_coeffs, z_eval)
        except Exception:
            hz_val = 0.0 + 0.0j

        self._convergence_data = {
            "partial_sums_real": partial_sums_real,
            "partial_sums_imag": partial_sums_imag,
            "closed_form_real": float(np.real(hz_val)),
            "closed_form_imag": float(np.imag(hz_val)),
            "k_values": k_values,
            "in_roc": in_roc,
        }

    def _apply_roc_region(self, region_idx: int) -> None:
        """Apply a specific ROC region selection."""
        options = ["auto_causal", "auto_anticausal", "annular"]
        if 0 <= region_idx < len(options):
            self.parameters["roc_selection"] = options[region_idx]

    # =========================================================================
    # Formatting helpers
    # =========================================================================

    def _format_hz(self) -> str:
        """Format H(z) expression as a readable string."""
        family = self.parameters["signal_family"]

        if family in ("right_exponential", "left_exponential"):
            a = complex(self.parameters["pole_real"], self.parameters["pole_imag"])
            if abs(a.imag) < 1e-6:
                return f"1 / (1 - {a.real:.3g}z\u207b\u00b9)"
            else:
                return f"1 / (1 - ({a.real:.2g}+{a.imag:.2g}j)z\u207b\u00b9)(1 - ({a.real:.2g}-{a.imag:.2g}j)z\u207b\u00b9)"

        elif family == "two_sided":
            a = complex(self.parameters["pole_real"], self.parameters["pole_imag"])
            b = complex(self.parameters["pole2_real"], self.parameters["pole2_imag"])
            parts = []
            if abs(a.imag) < 1e-6:
                parts.append(f"(1 - {a.real:.3g}z\u207b\u00b9)")
            else:
                parts.append(f"(1 - {a:.2g}z\u207b\u00b9)")
            if abs(b.imag) < 1e-6:
                parts.append(f"(1 - {b.real:.3g}z\u207b\u00b9)")
            else:
                parts.append(f"(1 - {b:.2g}z\u207b\u00b9)")
            return "1 / " + "".join(parts)

        elif family == "second_order":
            p1 = complex(self.parameters["pole_real"], self.parameters["pole_imag"])
            p2 = complex(self.parameters["pole2_real"], self.parameters["pole2_imag"])
            if abs(p1.imag) > 1e-6:
                return f"1 / (1 - 2\u00b7{p1.real:.2g}\u00b7cos({abs(p1.imag):.2g})z\u207b\u00b9 + {abs(p1)**2:.3g}z\u207b\u00b2)"
            else:
                return f"1 / (1 - {p1.real:.3g}z\u207b\u00b9)(1 - {p2.real:.3g}z\u207b\u00b9)"

        elif family == "damped_sinusoid":
            r = float(self.parameters["r_magnitude"])
            w0 = float(self.parameters["omega_0"])
            return f"(1 - {r*np.cos(w0):.3g}z\u207b\u00b9) / (1 - {2*r*np.cos(w0):.3g}z\u207b\u00b9 + {r**2:.3g}z\u207b\u00b2)"

        elif family == "custom_rational":
            num_str = self.parameters["custom_num_coeffs"]
            den_str = self.parameters["custom_den_coeffs"]
            return f"B(z)/A(z) = [{num_str}] / [{den_str}]"

        return "H(z)"

    def _format_roc(self) -> str:
        """Format ROC description as readable string."""
        if len(self._pole_radii) == 0:
            return "Entire z-plane"

        if self._roc_outer == float("inf"):
            return f"|z| > {self._roc_inner:.4g}"
        elif self._roc_inner == 0:
            return f"|z| < {self._roc_outer:.4g}"
        else:
            return f"{self._roc_inner:.4g} < |z| < {self._roc_outer:.4g}"

    def _get_signal_title(self) -> str:
        """Build title string for time-domain plot."""
        family = self.parameters["signal_family"]
        if family == "right_exponential":
            a = complex(self.parameters["pole_real"], self.parameters["pole_imag"])
            if abs(a.imag) < 1e-6:
                return f"x[n] = ({a.real:.3g})\u207f u[n]  (causal)"
            return f"x[n] = ({a:.2g})\u207f u[n]  (causal)"
        elif family == "left_exponential":
            a = complex(self.parameters["pole_real"], self.parameters["pole_imag"])
            if abs(a.imag) < 1e-6:
                return f"x[n] = -({a.real:.3g})\u207f u[-n-1]  (anti-causal)"
            return f"x[n] = -({a:.2g})\u207f u[-n-1]  (anti-causal)"
        elif family == "damped_sinusoid":
            r = self.parameters["r_magnitude"]
            w0 = self.parameters["omega_0"]
            return f"x[n] = ({r:.2g})\u207f cos({w0:.2g}n) u[n]"

        causality = "causal" if self._is_causal else ("anti-causal" if self._is_anticausal else "two-sided")
        return f"x[n]  ({causality})"

    # =========================================================================
    # Plot generation
    # =========================================================================

    def get_plots(self) -> List[Dict[str, Any]]:
        """Generate all Plotly plot dictionaries."""
        if not self._initialized:
            self.initialize()

        plots = [
            self._create_z_plane_plot(),
            self._create_time_domain_plot(),
        ]
        if self.parameters["show_convergence"] and self._convergence_data is not None:
            plots.append(self._create_convergence_plot())
        return plots

    def _compute_z_plane_range(self) -> float:
        """Compute dynamic axis range based on poles, zeros, and ROC."""
        max_r = 1.2  # At minimum, show unit circle with padding
        for p in self._poles:
            max_r = max(max_r, abs(p) + 0.3)
        for z in self._zeros:
            max_r = max(max_r, abs(z) + 0.3)
        if self._roc_inner > 0:
            max_r = max(max_r, self._roc_inner + 0.3)
        if self._roc_outer != float("inf"):
            max_r = max(max_r, self._roc_outer + 0.3)
        return min(max_r, 3.0)  # Cap at 3.0

    def _create_z_plane_plot(self) -> Dict[str, Any]:
        """Create z-plane plot with poles, zeros, unit circle, and ROC."""
        traces = []
        axis_range = self._compute_z_plane_range()

        # Unit circle
        theta = np.linspace(0, 2 * np.pi, 200)
        traces.append({
            "x": np.cos(theta).tolist(),
            "y": np.sin(theta).tolist(),
            "type": "scatter",
            "mode": "lines",
            "line": {"color": self.UNIT_CIRCLE_COLOR, "width": 2.5, "dash": "dash"},
            "name": "Unit Circle |z|=1",
            "hoverinfo": "skip",
        })

        # ROC boundary circles
        if self._roc_inner > 1e-6:
            r_inner = self._roc_inner
            traces.append({
                "x": (r_inner * np.cos(theta)).tolist(),
                "y": (r_inner * np.sin(theta)).tolist(),
                "type": "scatter",
                "mode": "lines",
                "line": {"color": self.ROC_BOUNDARY, "width": 2},
                "name": f"ROC inner |z|={r_inner:.3g}",
                "hoverinfo": "skip",
            })

        if self._roc_outer != float("inf"):
            r_outer = self._roc_outer
            traces.append({
                "x": (r_outer * np.cos(theta)).tolist(),
                "y": (r_outer * np.sin(theta)).tolist(),
                "type": "scatter",
                "mode": "lines",
                "line": {"color": self.ROC_BOUNDARY, "width": 2},
                "name": f"ROC outer |z|={r_outer:.3g}",
                "hoverinfo": "skip",
            })

        # Axes
        traces.append({
            "x": [-axis_range, axis_range], "y": [0, 0],
            "type": "scatter", "mode": "lines",
            "line": {"color": self.ZEROLINE_COLOR, "width": 1},
            "showlegend": False, "hoverinfo": "skip",
        })
        traces.append({
            "x": [0, 0], "y": [-axis_range, axis_range],
            "type": "scatter", "mode": "lines",
            "line": {"color": self.ZEROLINE_COLOR, "width": 1},
            "showlegend": False, "hoverinfo": "skip",
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
                "text": [f"p{i+1}"],
                "textposition": "top center",
                "textfont": {"color": self.POLE_COLOR, "size": 10},
                "name": f"Pole {i+1}: {pole_label}",
                "showlegend": True,
                "hovertemplate": f"Pole {i+1}<br>z = {pole_label}<br>|z| = {abs(pole):.4f}<extra></extra>",
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
                "name": f"Zero {i+1}: {zero_label}",
                "showlegend": True,
                "hovertemplate": f"Zero {i+1}<br>z = {zero_label}<extra></extra>",
            })

        # Build ROC shapes for layout
        shapes = self._get_roc_shapes(axis_range)

        return {
            "id": "z_plane",
            "title": "Z-Plane: Poles, Zeros & ROC",
            "data": traces,
            "layout": {
                "xaxis": {
                    "title": "Real",
                    "range": [-axis_range, axis_range],
                    "scaleanchor": "y",
                    "scaleratio": 1,
                    "showgrid": True,
                    "gridcolor": self.GRID_COLOR,
                    "zeroline": False,
                    "fixedrange": False,
                },
                "yaxis": {
                    "title": "Imaginary",
                    "range": [-axis_range, axis_range],
                    "showgrid": True,
                    "gridcolor": self.GRID_COLOR,
                    "zeroline": False,
                    "fixedrange": False,
                },
                "legend": {
                    "x": 0.02, "y": 0.98,
                    "xanchor": "left", "yanchor": "top",
                    "bgcolor": self.LEGEND_BG,
                    "bordercolor": self.LEGEND_BORDER,
                    "borderwidth": 1,
                    "font": {"size": 10},
                },
                "margin": {"l": 60, "r": 30, "t": 50, "b": 50},
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)",
                "shapes": shapes,
                "uirevision": f"z_plane_{self._revision_counter}",
            },
        }

    def _get_roc_shapes(self, axis_range: float = 2.0) -> List[Dict[str, Any]]:
        """Build Plotly shapes for ROC shading."""
        shapes = []

        if len(self._pole_radii) == 0:
            return shapes

        # ROC fill: show the valid region
        # For causal (|z| > r): fill a large circle and cut out inner
        # For anti-causal (|z| < r): fill inner circle
        # For annular (r1 < |z| < r2): fill between two circles

        if self._roc_outer == float("inf"):
            # Causal: ROC is outside radius roc_inner
            # Draw large background circle as ROC
            shapes.append({
                "type": "circle",
                "x0": -axis_range, "y0": -axis_range,
                "x1": axis_range, "y1": axis_range,
                "fillcolor": self.ROC_FILL,
                "line": {"width": 0},
                "layer": "below",
            })
            # Cut out the excluded inner region
            if self._roc_inner > 1e-6:
                r = self._roc_inner
                shapes.append({
                    "type": "circle",
                    "x0": -r, "y0": -r, "x1": r, "y1": r,
                    "fillcolor": self.ROC_EXCLUDED,
                    "line": {"color": self.ROC_BOUNDARY, "width": 1.5},
                    "layer": "below",
                })
        elif self._roc_inner == 0:
            # Anti-causal: ROC is inside radius roc_outer
            r = self._roc_outer
            shapes.append({
                "type": "circle",
                "x0": -r, "y0": -r, "x1": r, "y1": r,
                "fillcolor": self.ROC_FILL,
                "line": {"color": self.ROC_BOUNDARY, "width": 1.5},
                "layer": "below",
            })
        else:
            # Annular: between roc_inner and roc_outer
            r_out = self._roc_outer
            r_in = self._roc_inner
            shapes.append({
                "type": "circle",
                "x0": -r_out, "y0": -r_out, "x1": r_out, "y1": r_out,
                "fillcolor": self.ROC_FILL,
                "line": {"color": self.ROC_BOUNDARY, "width": 1.5},
                "layer": "below",
            })
            shapes.append({
                "type": "circle",
                "x0": -r_in, "y0": -r_in, "x1": r_in, "y1": r_in,
                "fillcolor": self.ROC_EXCLUDED,
                "line": {"color": self.ROC_BOUNDARY, "width": 1.5},
                "layer": "below",
            })

        return shapes

    def _create_time_domain_plot(self) -> Dict[str, Any]:
        """Create stem plot of x[n]."""
        traces = []

        if len(self._n_full) > 0:
            # Split into negative and positive n for color coding
            neg_mask = self._n_full < 0
            pos_mask = self._n_full >= 0

            # Left-sided (negative n) in red
            if np.any(neg_mask):
                n_neg = self._n_full[neg_mask]
                x_neg = self._x_full[neg_mask]
                traces.extend(self._create_stem_traces(
                    n_neg, x_neg, self.SIGNAL_LEFT, "Left-sided", width=2.0
                ))

            # Right-sided (non-negative n) in blue
            if np.any(pos_mask):
                n_pos = self._n_full[pos_mask]
                x_pos = self._x_full[pos_mask]
                traces.extend(self._create_stem_traces(
                    n_pos, x_pos, self.SIGNAL_RIGHT, "Right-sided", width=2.0
                ))

        return {
            "id": "time_domain",
            "title": self._get_signal_title(),
            "data": traces,
            "layout": {
                "xaxis": {
                    "title": "Sample index n",
                    "showgrid": True,
                    "gridcolor": self.GRID_COLOR,
                    "zeroline": True,
                    "zerolinecolor": self.ZEROLINE_COLOR,
                    "zerolinewidth": 1.5,
                    "autorange": True,
                    "dtick": 5,
                    "fixedrange": False,
                },
                "yaxis": {
                    "title": "x[n]",
                    "showgrid": True,
                    "gridcolor": self.GRID_COLOR,
                    "zeroline": True,
                    "zerolinecolor": self.ZEROLINE_COLOR,
                    "zerolinewidth": 1.5,
                    "autorange": True,
                    "fixedrange": False,
                },
                "legend": {
                    "x": 0.98, "y": 0.98,
                    "xanchor": "right", "yanchor": "top",
                    "bgcolor": self.LEGEND_BG,
                    "bordercolor": self.LEGEND_BORDER,
                    "borderwidth": 1,
                    "font": {"size": 11},
                },
                "margin": {"l": 60, "r": 30, "t": 50, "b": 55},
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)",
                "uirevision": f"time_domain_{self._revision_counter}",
            },
        }

    def _create_stem_traces(
        self, n: np.ndarray, y: np.ndarray, color: str, name: str, width: float = 1.5
    ) -> List[Dict[str, Any]]:
        """Create Plotly traces for a stem plot."""
        traces = []

        # Vertical lines
        x_lines: List = []
        y_lines: List = []
        for i in range(len(n)):
            x_lines.extend([float(n[i]), float(n[i]), None])
            y_lines.extend([0.0, float(y[i]), None])

        traces.append({
            "x": x_lines,
            "y": y_lines,
            "type": "scatter",
            "mode": "lines",
            "line": {"color": color, "width": width},
            "showlegend": False,
            "hoverinfo": "skip",
        })

        # Markers
        traces.append({
            "x": n.tolist(),
            "y": y.tolist(),
            "type": "scatter",
            "mode": "markers",
            "marker": {"color": color, "size": 7, "line": {"color": color, "width": 1}},
            "name": name,
            "showlegend": True,
            "hovertemplate": f"{name}<br>n = %{{x}}<br>x[n] = %{{y:.4f}}<extra></extra>",
        })

        return traces

    def _create_convergence_plot(self) -> Dict[str, Any]:
        """Create convergence of partial sums plot."""
        data = self._convergence_data
        if data is None:
            return {
                "id": "convergence",
                "title": "Convergence (enable toggle)",
                "data": [],
                "layout": {},
            }

        traces = []

        # Partial sums trajectory
        if data["k_values"]:
            traces.append({
                "x": data["partial_sums_real"],
                "y": data["partial_sums_imag"],
                "type": "scatter",
                "mode": "lines+markers",
                "marker": {
                    "size": 6,
                    "color": data["k_values"],
                    "colorscale": "Viridis",
                    "colorbar": {"title": "K", "thickness": 15, "len": 0.6},
                },
                "line": {"color": "rgba(59,130,246,0.3)", "width": 1},
                "name": "Partial sums S\u2096(z)",
                "hovertemplate": "K=%{marker.color}<br>Re=%{x:.4f}<br>Im=%{y:.4f}<extra></extra>",
            })

        # Closed form target
        traces.append({
            "x": [data["closed_form_real"]],
            "y": [data["closed_form_imag"]],
            "type": "scatter",
            "mode": "markers",
            "marker": {"symbol": "star", "size": 16, "color": self.ROC_BOUNDARY,
                        "line": {"width": 2, "color": "#fff"}},
            "name": f"H(z\u2080) = {data['closed_form_real']:.3f} + {data['closed_form_imag']:.3f}j",
        })

        roc_status = "z\u2080 in ROC" if data["in_roc"] else "z\u2080 NOT in ROC"

        return {
            "id": "convergence",
            "title": f"Convergence of Partial Sums ({roc_status})",
            "data": traces,
            "layout": {
                "xaxis": {
                    "title": "Real",
                    "showgrid": True,
                    "gridcolor": self.GRID_COLOR,
                    "zeroline": True,
                    "zerolinecolor": self.ZEROLINE_COLOR,
                    "autorange": True,
                    "fixedrange": False,
                },
                "yaxis": {
                    "title": "Imaginary",
                    "showgrid": True,
                    "gridcolor": self.GRID_COLOR,
                    "zeroline": True,
                    "zerolinecolor": self.ZEROLINE_COLOR,
                    "autorange": True,
                    "fixedrange": False,
                },
                "legend": {
                    "x": 0.02, "y": 0.98,
                    "xanchor": "left", "yanchor": "top",
                    "bgcolor": self.LEGEND_BG,
                    "bordercolor": self.LEGEND_BORDER,
                    "borderwidth": 1,
                    "font": {"size": 11},
                },
                "margin": {"l": 60, "r": 30, "t": 50, "b": 55},
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)",
                "uirevision": f"convergence_{self._revision_counter}",
            },
        }

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
    # Hub integration
    # =========================================================================

    def to_hub_data(self):
        """Export custom TF coefficients (custom_num_coeffs / custom_den_coeffs)."""
        num = self._parse_coeffs(str(self.parameters.get('custom_num_coeffs', '1')))
        den = self._parse_coeffs(str(self.parameters.get('custom_den_coeffs', '1, -0.7')))
        if len(num) > 0 and len(den) > 0:
            return {
                "source": "tf",
                "domain": self.HUB_DOMAIN,
                "dimensions": self.HUB_DIMENSIONS,
                "tf": {"num": list(num), "den": list(den), "variable": "z"},
            }
        return None

    def from_hub_data(self, hub_data):
        """Producer-only: z_transform_roc is an interactive ROC visualizer.

        The user enters a DT TF and explores its region of convergence.
        Auto-pulling a TF from the hub would replace the user's current
        input mid-exploration. Users who want to load a TF from elsewhere
        should use the sim's own input controls.
        """
        return False

    # =========================================================================
    # State
    # =========================================================================

    def get_state(self) -> Dict[str, Any]:
        """Return current simulation state with metadata for custom viewer."""
        if not self._initialized:
            self.initialize()

        state = super().get_state()

        state["metadata"] = {
            "simulation_type": "z_transform_roc",
            "hub_slots": self.HUB_SLOTS,
            "hub_domain": self.HUB_DOMAIN,
            "hub_dimensions": self.HUB_DIMENSIONS,
            "sticky_controls": True,
            "hz_expression": self._format_hz(),
            "roc_description": self._format_roc(),
            "causality": "Causal" if self._is_causal else (
                "Anti-causal" if self._is_anticausal else "Two-sided"
            ),
            "is_stable": self._is_stable,
            "stability_text": (
                "Stable (ROC includes |z|=1)" if self._is_stable
                else "Unstable (ROC excludes |z|=1)"
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
            "pole_radii": [float(r) for r in self._pole_radii],
            "roc_inner": float(self._roc_inner),
            "roc_outer": float(self._roc_outer) if self._roc_outer != float("inf") else None,
        }

        return state
