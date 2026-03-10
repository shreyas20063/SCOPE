"""
Root Locus Analyzer

Textbook-faithful root locus tool for control systems analysis.
Computes and visualizes how closed-loop poles migrate in the s-plane
as loop gain K varies from 0 to infinity (and optionally K < 0).

Features:
- Adaptive K sweep with branch tracking
- All Evans root locus construction rules: breakaway/break-in, asymptotes,
  jω-axis crossings, departure/arrival angles, real-axis segments
- Step response and performance metrics at selected K
- Gain and phase margins
- Draggable open-loop poles/zeros
- Import TF from Block Diagram Builder
- Preset classic systems

References: Nise Ch.8, Ogata Ch.6, Franklin/Powell/Emami-Naeini Ch.5
"""

import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from scipy import signal
from .base_simulator import BaseSimulator


class RootLocusSimulator(BaseSimulator):
    """Root Locus Analyzer with full textbook construction rules."""

    # Branch colors (rotate for multi-branch systems)
    BRANCH_COLORS = [
        "#3b82f6",  # blue
        "#ef4444",  # red
        "#10b981",  # green
        "#f59e0b",  # amber
        "#8b5cf6",  # purple
        "#ec4899",  # pink
        "#06b6d4",  # cyan
        "#f97316",  # orange
        "#14b8a6",  # teal
        "#a855f7",  # violet
    ]

    # Marker colors
    OL_POLE_COLOR = "#ef4444"     # red
    OL_ZERO_COLOR = "#3b82f6"     # blue
    CL_POLE_COLOR = "#f59e0b"     # amber (current K)
    STABLE_FILL = "rgba(16, 185, 129, 0.05)"  # subtle green LHP
    UNSTABLE_FILL = "rgba(239, 68, 68, 0.05)"  # subtle red RHP

    # Plot styling
    GRID_COLOR = "rgba(148, 163, 184, 0.15)"
    ZERO_LINE_COLOR = "rgba(148, 163, 184, 0.3)"
    TEXT_COLOR = "#e2e8f0"
    PAPER_BG = "#0a0e27"
    PLOT_BG = "#131b2e"

    # Damping line zeta values
    ZETA_VALUES = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    WN_VALUES = [1, 2, 5, 10, 20, 50]

    # Preset systems: {id: (num_coeffs_str, den_coeffs_str, description)}
    PRESET_SYSTEMS = {
        "two_real_poles": ("1", "1, 4, 3", "1/((s+1)(s+3))"),
        "integrator_pole": ("1", "1, 2, 0", "1/(s(s+2))"),
        "with_zero": ("1, 2", "1, 5, 4, 0", "(s+2)/(s(s+1)(s+4))"),
        "double_integrator": ("1", "1, 3, 0, 0", "1/(s²(s+3))"),
        "complex_poles": ("1", "1, 3, 7, 5", "1/((s²+2s+5)(s+1))"),
        "third_order": ("1", "1, 5, 4, 0", "1/(s(s+1)(s+4))"),
        "lead_compensated": ("1, 3", "1, 6, 5, 0", "(s+3)/(s(s+1)(s+5))"),
        "non_minimum_phase": ("1, -1", "1, 5, 6, 0", "(s-1)/(s(s+2)(s+3))"),
        "conditionally_stable": ("1", "1, 9, 26, 24, 0", "1/(s(s+1)(s+2)(s+6)(s+0))"),
        "fourth_order": ("1", "1, 10, 35, 50, 24", "1/((s+1)(s+2)(s+3)(s+4))"),
    }

    PARAMETER_SCHEMA = {
        "num_coeffs": {
            "type": "expression",
            "default": "1",
            "label": "Numerator N(s)",
            "group": "Transfer Function",
        },
        "den_coeffs": {
            "type": "expression",
            "default": "1, 5, 4, 0",
            "label": "Denominator D(s)",
            "group": "Transfer Function",
        },
        "preset": {
            "type": "select",
            "options": [
                {"value": "custom", "label": "Custom"},
                {"value": "two_real_poles", "label": "Two Real Poles"},
                {"value": "integrator_pole", "label": "Integrator + Pole"},
                {"value": "with_zero", "label": "With Zero (Break-in)"},
                {"value": "double_integrator", "label": "Double Integrator"},
                {"value": "complex_poles", "label": "Complex Poles"},
                {"value": "third_order", "label": "Third Order (Asymptotes)"},
                {"value": "lead_compensated", "label": "Lead Compensated"},
                {"value": "non_minimum_phase", "label": "Non-minimum Phase"},
                {"value": "conditionally_stable", "label": "Conditionally Stable"},
                {"value": "fourth_order", "label": "Fourth Order"},
            ],
            "default": "third_order",
            "label": "Preset System",
            "group": "Transfer Function",
        },
        "gain_K": {
            "type": "slider",
            "min": 0,
            "max": 200,
            "step": 0.01,
            "default": 1.0,
            "label": "Gain K",
            "group": "Gain",
        },
        "k_max": {
            "type": "slider",
            "min": 1,
            "max": 1000,
            "step": 1,
            "default": 100,
            "label": "K Maximum",
            "group": "Gain",
        },
        "negative_k": {
            "type": "checkbox",
            "default": False,
            "label": "Complementary (K < 0)",
            "group": "Gain",
        },
        "show_damping_lines": {
            "type": "checkbox",
            "default": True,
            "label": "Damping Ratio Lines",
            "group": "Overlays",
        },
        "show_wn_circles": {
            "type": "checkbox",
            "default": False,
            "label": "Natural Freq Circles",
            "group": "Overlays",
        },
        "show_asymptotes": {
            "type": "checkbox",
            "default": True,
            "label": "Asymptotes",
            "group": "Overlays",
        },
        "show_annotations": {
            "type": "checkbox",
            "default": True,
            "label": "Special Points",
            "group": "Overlays",
        },
    }

    DEFAULT_PARAMS = {
        "num_coeffs": "1",
        "den_coeffs": "1, 5, 4, 0",
        "preset": "third_order",
        "gain_K": 1.0,
        "k_max": 100,
        "negative_k": False,
        "show_damping_lines": True,
        "show_wn_circles": False,
        "show_asymptotes": True,
        "show_annotations": True,
    }

    def __init__(self, simulation_id: str):
        super().__init__(simulation_id)
        self._num = np.array([1.0])
        self._den = np.array([1.0, 5.0, 4.0, 0.0])
        self._error: Optional[str] = None

        # Cached locus data
        self._cache_key: Optional[tuple] = None
        self._cached_k_values: Optional[np.ndarray] = None
        self._cached_branches: Optional[List[np.ndarray]] = None
        self._cached_special: Optional[Dict] = None

    def initialize(self, params: Optional[Dict[str, Any]] = None) -> None:
        self.parameters = {**self.DEFAULT_PARAMS, **(params or {})}
        for name, value in self.parameters.items():
            self.parameters[name] = self._validate_param(name, value)

        # Load preset if set
        preset = self.parameters.get("preset", "custom")
        if preset != "custom" and preset in self.PRESET_SYSTEMS:
            num_str, den_str, _ = self.PRESET_SYSTEMS[preset]
            self.parameters["num_coeffs"] = num_str
            self.parameters["den_coeffs"] = den_str

        self._parse_coefficients()
        self._invalidate_cache()
        self._initialized = True

    def update_parameter(self, name: str, value: Any) -> Dict[str, Any]:
        if name in self.parameters:
            self.parameters[name] = self._validate_param(name, value)

        # Preset selection overrides coefficients
        if name == "preset" and value != "custom" and value in self.PRESET_SYSTEMS:
            num_str, den_str, _ = self.PRESET_SYSTEMS[value]
            self.parameters["num_coeffs"] = num_str
            self.parameters["den_coeffs"] = den_str
            self._parse_coefficients()
            self._invalidate_cache()

        # Coefficient changes require reparse and cache invalidation
        if name in ("num_coeffs", "den_coeffs"):
            self.parameters["preset"] = "custom"
            self._parse_coefficients()
            self._invalidate_cache()

        # k_max or negative_k change invalidates cache
        if name in ("k_max", "negative_k"):
            self._invalidate_cache()

        # gain_K change uses cached branches (fast path)
        return self.get_state()

    def handle_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        action_map = {
            "click_select_k": self._action_click_select_k,
            "load_preset": self._action_load_preset,
            "move_pole": self._action_move_pole,
            "move_zero": self._action_move_zero,
            "import_tf": self._action_import_tf,
        }
        handler = action_map.get(action)
        if handler:
            return handler(params)
        return self.get_state()

    def get_plots(self) -> List[Dict[str, Any]]:
        self._ensure_cache()
        plots = []
        plots.append(self._build_root_locus_plot())
        plots.append(self._build_step_response_plot())
        plots.append(self._build_performance_plot())
        return plots

    def get_state(self) -> Dict[str, Any]:
        self._ensure_cache()
        base = super().get_state()

        # Compute current CL poles and metrics
        K = float(self.parameters["gain_K"])
        if self.parameters["negative_k"]:
            K = -K
        cl_poles = self._cl_poles_at_k(K)
        metrics = self._compute_metrics(K, cl_poles)
        special = self._cached_special or {}

        # Open-loop poles/zeros
        ol_poles = np.roots(self._den) if len(self._den) > 1 else np.array([])
        ol_zeros = np.roots(self._num) if len(self._num) > 1 else np.array([])

        # Stability
        if len(cl_poles) == 0:
            stability = "stable"
        elif np.any(np.real(cl_poles) > 1e-8):
            stability = "unstable"
        elif np.any(np.abs(np.real(cl_poles)) <= 1e-8):
            stability = "marginally_stable"
        else:
            stability = "stable"

        # Dominant poles (closest to jw axis in LHP)
        dominant = self._get_dominant_poles(cl_poles)

        # Transfer function display strings
        num_display = self._poly_to_str(self._num)
        den_display = self._poly_to_str(self._den)
        system_type = self._count_origin_poles(self._den)

        base["metadata"] = {
            "simulation_type": "root_locus",
            "has_custom_viewer": True,
            "ol_poles": [{"real": float(np.real(p)), "imag": float(np.imag(p))} for p in ol_poles],
            "ol_zeros": [{"real": float(np.real(z)), "imag": float(np.imag(z))} for z in ol_zeros],
            "cl_poles": [{"real": float(np.real(p)), "imag": float(np.imag(p))} for p in cl_poles],
            "current_K": float(self.parameters["gain_K"]),
            "stability": stability,
            "dominant_poles": dominant,
            "metrics": metrics,
            "special_points": self._serialize_special_points(special),
            "transfer_function": {
                "num_display": num_display,
                "den_display": den_display,
                "system_type": system_type,
                "order": len(self._den) - 1,
            },
            "error": self._error,
        }
        return base

    # =========================================================================
    # Parsing
    # =========================================================================

    def _parse_coefficients(self) -> None:
        """Parse numerator and denominator from comma-separated strings."""
        self._error = None
        try:
            num_str = str(self.parameters.get("num_coeffs", "1")).strip()
            den_str = str(self.parameters.get("den_coeffs", "1, 0")).strip()

            num = self._parse_poly_string(num_str)
            den = self._parse_poly_string(den_str)

            if len(num) == 0 or len(den) == 0:
                self._error = "Coefficients cannot be empty"
                return
            if len(den) < 2:
                self._error = "Denominator must be at least order 1"
                return
            if len(num) > len(den):
                self._error = "Improper TF: numerator order must be ≤ denominator order"
                return
            if len(den) > 21:
                self._error = "System order too high (max 20)"
                return
            if abs(den[0]) < 1e-15:
                self._error = "Leading denominator coefficient cannot be zero"
                return

            # Normalize so leading den coeff = 1
            den = den / den[0]
            num = num / den[0] if abs(den[0]) > 1e-15 else num

            self._num = num
            self._den = den

        except Exception as e:
            self._error = f"Parse error: {str(e)}"

    def _parse_poly_string(self, s: str) -> np.ndarray:
        """Parse comma-separated coefficients (highest power first)."""
        s = s.strip()
        if not s:
            return np.array([0.0])
        parts = [p.strip() for p in s.split(",")]
        coeffs = [float(p) for p in parts if p]
        return np.array(coeffs) if coeffs else np.array([0.0])

    # =========================================================================
    # Root Locus Computation
    # =========================================================================

    def _invalidate_cache(self) -> None:
        self._cache_key = None
        self._cached_k_values = None
        self._cached_branches = None
        self._cached_special = None

    def _ensure_cache(self) -> None:
        """Compute locus if cache is stale."""
        if self._error:
            return
        key = (
            tuple(self._num.tolist()),
            tuple(self._den.tolist()),
            float(self.parameters["k_max"]),
            bool(self.parameters["negative_k"]),
        )
        if self._cache_key == key and self._cached_branches is not None:
            return
        self._cache_key = key
        self._compute_full_locus()
        self._compute_special_points()

    def _compute_full_locus(self) -> None:
        """Sweep K, compute CL poles, track branches."""
        k_max = float(self.parameters["k_max"])
        negative = bool(self.parameters["negative_k"])
        n = len(self._den) - 1  # number of branches

        if n == 0:
            self._cached_k_values = np.array([0.0])
            self._cached_branches = []
            return

        # First pass: log-spaced K values
        k_values = np.concatenate([
            [0.0],
            np.logspace(-4, np.log10(max(k_max, 1.0)), 500),
        ])
        k_values = np.unique(k_values)

        if negative:
            k_values = -k_values[::-1]  # sweep from -k_max to 0

        # Compute poles at each K
        all_poles = []
        for k in k_values:
            poles = self._cl_poles_at_k(k)
            all_poles.append(poles)

        # Adaptive refinement: insert points where poles move fast
        if len(all_poles) > 2:
            k_values, all_poles = self._adaptive_refine(k_values, all_poles, negative)

        # Branch tracking via greedy nearest-neighbor
        branches = self._track_branches(k_values, all_poles, n)

        self._cached_k_values = k_values
        self._cached_branches = branches

    def _cl_poles_at_k(self, k: float) -> np.ndarray:
        """Compute closed-loop poles for given K. CL char eq: D(s) + K*N(s) = 0."""
        num_padded = np.zeros_like(self._den)
        offset = len(self._den) - len(self._num)
        num_padded[offset:] = self._num
        char_poly = self._den + k * num_padded
        try:
            return np.roots(char_poly)
        except Exception:
            return np.array([])

    def _adaptive_refine(
        self,
        k_values: np.ndarray,
        all_poles: List[np.ndarray],
        negative: bool,
    ) -> Tuple[np.ndarray, List[np.ndarray]]:
        """Insert extra K points where pole movement is large."""
        # Compute max pole displacement between consecutive K values
        displacements = []
        for i in range(1, len(all_poles)):
            if len(all_poles[i]) == len(all_poles[i - 1]) and len(all_poles[i]) > 0:
                # Use sorted-by-imag matching for displacement estimate
                p1 = np.sort_complex(all_poles[i - 1])
                p2 = np.sort_complex(all_poles[i])
                disp = np.max(np.abs(p2 - p1))
            else:
                disp = 0.0
            displacements.append(disp)

        if not displacements:
            return k_values, all_poles

        displacements = np.array(displacements)
        median_disp = np.median(displacements[displacements > 0]) if np.any(displacements > 0) else 1.0
        threshold = 2.0 * median_disp

        # Find regions needing refinement
        extra_k = []
        for i, d in enumerate(displacements):
            if d > threshold and i < len(k_values) - 1:
                n_insert = min(20, max(5, int(d / median_disp)))
                extra_k.extend(np.linspace(k_values[i], k_values[i + 1], n_insert + 2)[1:-1])

        if not extra_k:
            return k_values, all_poles

        # Merge and recompute
        extra_k = np.array(extra_k)
        all_k = np.unique(np.concatenate([k_values, extra_k]))
        if negative:
            all_k = np.sort(all_k)
        else:
            all_k = np.sort(all_k)

        new_poles = []
        for k in all_k:
            new_poles.append(self._cl_poles_at_k(k))

        return all_k, new_poles

    def _track_branches(
        self,
        k_values: np.ndarray,
        all_poles: List[np.ndarray],
        n_branches: int,
    ) -> List[np.ndarray]:
        """Track pole branches across K values using nearest-neighbor matching."""
        if len(all_poles) == 0 or n_branches == 0:
            return []

        # Initialize branches
        branches = [[] for _ in range(n_branches)]

        # Sort first set of poles
        first_poles = all_poles[0]
        if len(first_poles) < n_branches:
            return []

        order = np.argsort(np.imag(first_poles) + 1j * np.real(first_poles))
        prev_poles = first_poles[order[:n_branches]]
        for b in range(n_branches):
            branches[b].append(prev_poles[b])

        # Track through remaining K values
        for i in range(1, len(all_poles)):
            poles = all_poles[i]
            if len(poles) < n_branches:
                # Pad with NaN if roots computation failed
                for b in range(n_branches):
                    branches[b].append(complex(np.nan, np.nan))
                continue

            # Greedy nearest-neighbor assignment
            available = list(range(len(poles)))
            assignment = [None] * n_branches

            for _ in range(n_branches):
                best_dist = np.inf
                best_b = -1
                best_p = -1
                for b in range(n_branches):
                    if assignment[b] is not None:
                        continue
                    for p_idx in available:
                        d = abs(poles[p_idx] - prev_poles[b])
                        if d < best_dist:
                            best_dist = d
                            best_b = b
                            best_p = p_idx
                if best_b >= 0 and best_p >= 0:
                    assignment[best_b] = best_p
                    available.remove(best_p)

            for b in range(n_branches):
                if assignment[b] is not None:
                    branches[b].append(poles[assignment[b]])
                else:
                    branches[b].append(complex(np.nan, np.nan))

            prev_poles = np.array([branches[b][-1] for b in range(n_branches)])

        return [np.array(branch) for branch in branches]

    # =========================================================================
    # Special Points
    # =========================================================================

    def _compute_special_points(self) -> None:
        """Compute all root locus construction rule points."""
        special: Dict[str, Any] = {}
        negative = bool(self.parameters["negative_k"])

        try:
            special["breakaway"] = self._find_breakaway_points(negative)
        except Exception:
            special["breakaway"] = []

        try:
            special["asymptotes"] = self._compute_asymptotes(negative)
        except Exception:
            special["asymptotes"] = {"centroid": 0, "angles": [], "n": 0}

        try:
            special["jw_crossings"] = self._find_jw_crossings()
        except Exception:
            special["jw_crossings"] = []

        try:
            special["departure_angles"] = self._compute_departure_angles()
        except Exception:
            special["departure_angles"] = []

        try:
            special["arrival_angles"] = self._compute_arrival_angles()
        except Exception:
            special["arrival_angles"] = []

        try:
            special["real_axis_segments"] = self._find_real_axis_segments(negative)
        except Exception:
            special["real_axis_segments"] = []

        self._cached_special = special

    def _find_breakaway_points(self, negative: bool) -> List[Dict]:
        """Find breakaway/break-in points: roots of N(s)D'(s) - N'(s)D(s) = 0."""
        N = self._num
        D = self._den
        Np = np.polyder(N)
        Dp = np.polyder(D)

        # N*D' - N'*D
        poly = np.polysub(np.polymul(N, Dp), np.polymul(Np, D))

        if len(poly) < 2:
            return []

        roots = np.roots(poly)
        breakaway = []

        for s in roots:
            # Only keep real roots (or nearly real)
            if abs(np.imag(s)) > 0.01:
                continue
            s_real = float(np.real(s))

            # Compute K at this point: K = -D(s)/N(s)
            n_val = np.polyval(N, s_real)
            if abs(n_val) < 1e-12:
                continue
            k_val = -np.polyval(D, s_real) / n_val

            # Check if K is valid for the locus type
            if negative and k_val > 0:
                continue
            if not negative and k_val < 0:
                continue

            # Check it's on a real-axis segment of the locus
            breakaway.append({
                "s": {"real": s_real, "imag": 0.0},
                "K": float(abs(k_val)),
            })

        return breakaway

    def _compute_asymptotes(self, negative: bool) -> Dict:
        """Compute asymptote centroid and angles."""
        poles = np.roots(self._den) if len(self._den) > 1 else np.array([])
        zeros = np.roots(self._num) if len(self._num) > 1 else np.array([])
        n_p = len(poles)
        n_z = len(zeros)
        n_a = n_p - n_z

        if n_a <= 0:
            return {"centroid": 0.0, "angles": [], "n": 0}

        centroid = float(np.real(np.sum(poles) - np.sum(zeros)) / n_a)

        if negative:
            angles = [float(360.0 * q / n_a) for q in range(n_a)]
        else:
            angles = [float((2 * q + 1) * 180.0 / n_a) for q in range(n_a)]

        return {"centroid": centroid, "angles": angles, "n": n_a}

    def _find_jw_crossings(self) -> List[Dict]:
        """Find where branches cross the imaginary axis."""
        crossings = []
        if self._cached_branches is None:
            return crossings

        k_values = self._cached_k_values
        for branch in self._cached_branches:
            for i in range(1, len(branch)):
                if np.isnan(branch[i]) or np.isnan(branch[i - 1]):
                    continue
                re_prev = np.real(branch[i - 1])
                re_curr = np.real(branch[i])
                # Sign change in real part
                if re_prev * re_curr < 0:
                    # Linear interpolation
                    t = abs(re_prev) / (abs(re_prev) + abs(re_curr))
                    k_cross = float(k_values[i - 1] + t * (k_values[i] - k_values[i - 1]))
                    omega = float(np.imag(branch[i - 1] + t * (branch[i] - branch[i - 1])))
                    crossings.append({
                        "omega": abs(omega),
                        "K": abs(k_cross),
                    })

        # Deduplicate close crossings
        unique = []
        for c in crossings:
            is_dup = False
            for u in unique:
                if abs(c["omega"] - u["omega"]) < 0.01 and abs(c["K"] - u["K"]) < 0.1:
                    is_dup = True
                    break
            if not is_dup:
                unique.append(c)

        return unique

    def _compute_departure_angles(self) -> List[Dict]:
        """Departure angles at complex open-loop poles."""
        poles = np.roots(self._den) if len(self._den) > 1 else np.array([])
        zeros = np.roots(self._num) if len(self._num) > 1 else np.array([])

        departures = []
        for i, p in enumerate(poles):
            if abs(np.imag(p)) < 1e-6:
                continue  # Skip real poles

            # Sum of angles from other poles
            angle_sum_poles = 0.0
            for j, other_p in enumerate(poles):
                if j != i:
                    angle_sum_poles += np.angle(p - other_p, deg=True)

            # Sum of angles from zeros
            angle_sum_zeros = 0.0
            for z in zeros:
                angle_sum_zeros += np.angle(p - z, deg=True)

            departure = 180.0 - angle_sum_poles + angle_sum_zeros
            # Normalize to [-180, 180]
            departure = ((departure + 180) % 360) - 180

            departures.append({
                "pole": {"real": float(np.real(p)), "imag": float(np.imag(p))},
                "angle_deg": float(departure),
            })

        return departures

    def _compute_arrival_angles(self) -> List[Dict]:
        """Arrival angles at complex open-loop zeros."""
        poles = np.roots(self._den) if len(self._den) > 1 else np.array([])
        zeros = np.roots(self._num) if len(self._num) > 1 else np.array([])

        arrivals = []
        for i, z in enumerate(zeros):
            if abs(np.imag(z)) < 1e-6:
                continue

            angle_sum_poles = 0.0
            for p in poles:
                angle_sum_poles += np.angle(z - p, deg=True)

            angle_sum_zeros = 0.0
            for j, other_z in enumerate(zeros):
                if j != i:
                    angle_sum_zeros += np.angle(z - other_z, deg=True)

            arrival = 180.0 + angle_sum_poles - angle_sum_zeros
            arrival = ((arrival + 180) % 360) - 180

            arrivals.append({
                "zero": {"real": float(np.real(z)), "imag": float(np.imag(z))},
                "angle_deg": float(arrival),
            })

        return arrivals

    def _find_real_axis_segments(self, negative: bool) -> List[Dict]:
        """Find segments of real axis that are part of the root locus."""
        poles = np.roots(self._den) if len(self._den) > 1 else np.array([])
        zeros = np.roots(self._num) if len(self._num) > 1 else np.array([])

        # Get all real poles and zeros
        real_pz = []
        for p in poles:
            if abs(np.imag(p)) < 1e-6:
                real_pz.append(float(np.real(p)))
        for z in zeros:
            if abs(np.imag(z)) < 1e-6:
                real_pz.append(float(np.real(z)))

        if not real_pz:
            return []

        real_pz.sort()

        # Test points between and beyond real poles/zeros
        segments = []
        test_points = []
        if real_pz:
            test_points.append(real_pz[0] - 1.0)
            for i in range(len(real_pz) - 1):
                test_points.append((real_pz[i] + real_pz[i + 1]) / 2.0)
            test_points.append(real_pz[-1] + 1.0)

        for tp in test_points:
            # Count poles and zeros to the right
            count_right = sum(1 for x in real_pz if x > tp)
            # For positive K: odd count → on locus. For negative K: even count.
            on_locus = (count_right % 2 == 1) if not negative else (count_right % 2 == 0)
            if on_locus:
                # Find the bounds of this segment
                left = -1e6
                right = 1e6
                for x in real_pz:
                    if x < tp and x > left:
                        left = x
                    if x > tp and x < right:
                        right = x
                segments.append({"left": left, "right": right})

        # Deduplicate
        unique = []
        for s in segments:
            is_dup = False
            for u in unique:
                if abs(s["left"] - u["left"]) < 1e-6 and abs(s["right"] - u["right"]) < 1e-6:
                    is_dup = True
                    break
            if not is_dup:
                unique.append(s)

        return unique

    # =========================================================================
    # Metrics
    # =========================================================================

    def _compute_metrics(self, K: float, cl_poles: np.ndarray) -> Dict:
        """Compute step response metrics and margins at given K."""
        metrics: Dict[str, Any] = {
            "damping_ratio": None,
            "natural_freq": None,
            "percent_overshoot": None,
            "settling_time": None,
            "rise_time": None,
            "steady_state_error": None,
            "gain_margin_db": None,
            "gain_margin_freq": None,
            "phase_margin_deg": None,
            "phase_margin_freq": None,
        }

        if len(cl_poles) == 0 or self._error:
            return metrics

        # Dominant poles (closest to jw axis with negative real part)
        dom = self._get_dominant_poles(cl_poles)
        if dom:
            metrics["damping_ratio"] = dom[0].get("zeta")
            metrics["natural_freq"] = dom[0].get("wn")

            zeta = dom[0].get("zeta", 1.0)
            wn = dom[0].get("wn", 1.0)
            if zeta is not None and 0 < zeta < 1 and wn > 0:
                metrics["percent_overshoot"] = float(
                    100 * np.exp(-np.pi * zeta / np.sqrt(1 - zeta ** 2))
                )
                metrics["settling_time"] = float(4.0 / (zeta * wn))
                metrics["rise_time"] = float((1.8 if zeta < 0.1 else 1.0 + 1.1 * zeta + 1.4 * zeta ** 2) / wn)

        # Steady-state error for unit step (type number dependent)
        try:
            system_type = self._count_origin_poles(self._den)
            # DC gain of closed-loop
            num_cl = K * self._num
            den_cl_padded = np.zeros_like(self._den)
            offset = len(self._den) - len(self._num)
            den_cl_padded[offset:] = self._num
            den_cl = self._den + K * den_cl_padded

            if system_type == 0:
                # Type 0: e_ss = 1/(1+Kp) where Kp = lim_{s→0} K*G(s)
                kp = K * np.polyval(self._num, 0) / np.polyval(self._den, 0) if abs(np.polyval(self._den, 0)) > 1e-12 else np.inf
                if np.isfinite(kp):
                    metrics["steady_state_error"] = float(1.0 / (1.0 + kp))
                else:
                    metrics["steady_state_error"] = 0.0
            else:
                metrics["steady_state_error"] = 0.0
        except Exception:
            pass

        # Gain and phase margins
        try:
            margins = self._compute_margins(K)
            metrics.update(margins)
        except Exception:
            pass

        return metrics

    def _compute_margins(self, K: float) -> Dict:
        """Compute gain and phase margins from open-loop frequency response."""
        result = {
            "gain_margin_db": None,
            "gain_margin_freq": None,
            "phase_margin_deg": None,
            "phase_margin_freq": None,
        }

        if abs(K) < 1e-12:
            return result

        w = np.logspace(-3, 3, 2000)
        s = 1j * w

        # Evaluate K*G(s)
        num_val = np.polyval(self._num, s)
        den_val = np.polyval(self._den, s)
        mask = np.abs(den_val) > 1e-15
        if not np.any(mask):
            return result

        KG = np.zeros_like(s)
        KG[mask] = K * num_val[mask] / den_val[mask]

        mag = np.abs(KG)
        phase = np.angle(KG, deg=True)

        # Gain crossover: |KG| = 1
        mag_db = 20 * np.log10(mag + 1e-30)
        for i in range(1, len(mag_db)):
            if mag_db[i - 1] * mag_db[i] < 0 or (mag_db[i - 1] > 0 and mag_db[i] <= 0):
                # Interpolate
                t = abs(mag_db[i - 1]) / (abs(mag_db[i - 1]) + abs(mag_db[i]))
                wc = w[i - 1] + t * (w[i] - w[i - 1])
                pc = phase[i - 1] + t * (phase[i] - phase[i - 1])
                result["phase_margin_deg"] = float(180.0 + pc)
                result["phase_margin_freq"] = float(wc)
                break

        # Phase crossover: angle(KG) = -180
        for i in range(1, len(phase)):
            phase_shifted = phase + 180
            if phase_shifted[i - 1] * phase_shifted[i] < 0:
                t = abs(phase_shifted[i - 1]) / (abs(phase_shifted[i - 1]) + abs(phase_shifted[i]))
                wp = w[i - 1] + t * (w[i] - w[i - 1])
                mc = mag[i - 1] + t * (mag[i] - mag[i - 1])
                if mc > 1e-15:
                    result["gain_margin_db"] = float(-20 * np.log10(mc))
                    result["gain_margin_freq"] = float(wp)
                break

        return result

    def _get_dominant_poles(self, cl_poles: np.ndarray) -> List[Dict]:
        """Get dominant closed-loop poles with their zeta and wn."""
        if len(cl_poles) == 0:
            return []

        dominant = []
        for p in cl_poles:
            sigma = float(np.real(p))
            omega = float(np.imag(p))
            wn = float(np.abs(p))
            zeta = float(-sigma / wn) if wn > 1e-10 else 1.0
            dominant.append({
                "real": sigma,
                "imag": omega,
                "zeta": max(0.0, min(zeta, 10.0)),  # Clamp
                "wn": wn,
            })

        # Sort by distance to jw axis (smallest |Re| first = most dominant)
        dominant.sort(key=lambda d: abs(d["real"]))
        return dominant

    def _count_origin_poles(self, den: np.ndarray) -> int:
        """Count number of poles at the origin (system type number)."""
        count = 0
        for c in reversed(den):
            if abs(c) < 1e-12:
                count += 1
            else:
                break
        return count

    # =========================================================================
    # Plot Builders
    # =========================================================================

    def _build_root_locus_plot(self) -> Dict:
        """Build the s-plane root locus plot."""
        traces = []
        shapes = []
        annotations_list = []

        negative = bool(self.parameters["negative_k"])
        K = float(self.parameters["gain_K"])
        if negative:
            K = -K

        # Root locus branches
        if self._cached_branches:
            for b_idx, branch in enumerate(self._cached_branches):
                color = self.BRANCH_COLORS[b_idx % len(self.BRANCH_COLORS)]
                x = [float(np.real(p)) for p in branch if not np.isnan(p)]
                y = [float(np.imag(p)) for p in branch if not np.isnan(p)]
                traces.append({
                    "x": x,
                    "y": y,
                    "type": "scatter",
                    "mode": "lines",
                    "line": {"color": color, "width": 2},
                    "name": f"Branch {b_idx + 1}",
                    "hovertemplate": "σ = %{x:.3f}<br>jω = %{y:.3f}<extra>Branch " + str(b_idx + 1) + "</extra>",
                    "showlegend": False,
                })

        # Open-loop poles (×)
        ol_poles = np.roots(self._den) if len(self._den) > 1 else np.array([])
        if len(ol_poles) > 0:
            traces.append({
                "x": [float(np.real(p)) for p in ol_poles],
                "y": [float(np.imag(p)) for p in ol_poles],
                "type": "scatter",
                "mode": "markers",
                "marker": {
                    "symbol": "x",
                    "size": 12,
                    "color": self.OL_POLE_COLOR,
                    "line": {"width": 2, "color": self.OL_POLE_COLOR},
                },
                "name": "OL Poles",
                "hovertemplate": "Pole: %{x:.3f} + %{y:.3f}j<extra>Open-Loop Pole</extra>",
            })

        # Open-loop zeros (○)
        ol_zeros = np.roots(self._num) if len(self._num) > 1 else np.array([])
        if len(ol_zeros) > 0:
            traces.append({
                "x": [float(np.real(z)) for z in ol_zeros],
                "y": [float(np.imag(z)) for z in ol_zeros],
                "type": "scatter",
                "mode": "markers",
                "marker": {
                    "symbol": "circle-open",
                    "size": 12,
                    "color": self.OL_ZERO_COLOR,
                    "line": {"width": 2, "color": self.OL_ZERO_COLOR},
                },
                "name": "OL Zeros",
                "hovertemplate": "Zero: %{x:.3f} + %{y:.3f}j<extra>Open-Loop Zero</extra>",
            })

        # Current CL poles (highlighted)
        cl_poles = self._cl_poles_at_k(K)
        if len(cl_poles) > 0:
            stable_mask = np.real(cl_poles) <= 0
            # Stable CL poles
            stable_p = cl_poles[stable_mask]
            if len(stable_p) > 0:
                traces.append({
                    "x": [float(np.real(p)) for p in stable_p],
                    "y": [float(np.imag(p)) for p in stable_p],
                    "type": "scatter",
                    "mode": "markers",
                    "marker": {
                        "symbol": "diamond",
                        "size": 14,
                        "color": self.CL_POLE_COLOR,
                        "line": {"width": 2, "color": "#ffffff"},
                    },
                    "name": f"CL Poles (K={abs(float(self.parameters['gain_K'])):.2f})",
                    "hovertemplate": "CL Pole: %{x:.3f} + %{y:.3f}j<extra>K=" + f"{abs(float(self.parameters['gain_K'])):.2f}" + "</extra>",
                })
            # Unstable CL poles
            unstable_p = cl_poles[~stable_mask]
            if len(unstable_p) > 0:
                traces.append({
                    "x": [float(np.real(p)) for p in unstable_p],
                    "y": [float(np.imag(p)) for p in unstable_p],
                    "type": "scatter",
                    "mode": "markers",
                    "marker": {
                        "symbol": "diamond",
                        "size": 14,
                        "color": "#ef4444",
                        "line": {"width": 2, "color": "#ffffff"},
                    },
                    "name": "CL Poles (Unstable)",
                    "hovertemplate": "UNSTABLE: %{x:.3f} + %{y:.3f}j<extra>Unstable CL Pole</extra>",
                })

        # Determine plot bounds
        all_re = [0.0]
        all_im = [0.0]
        for p in ol_poles:
            all_re.append(float(np.real(p)))
            all_im.append(float(np.imag(p)))
        for z in ol_zeros:
            all_re.append(float(np.real(z)))
            all_im.append(float(np.imag(z)))
        for p in cl_poles:
            all_re.append(float(np.real(p)))
            all_im.append(float(np.imag(p)))
        if self._cached_branches:
            for branch in self._cached_branches:
                for p in branch:
                    if not np.isnan(p):
                        all_re.append(float(np.real(p)))
                        all_im.append(float(np.imag(p)))

        re_min = min(all_re) - 1
        re_max = max(all_re) + 1
        im_min = min(all_im) - 1
        im_max = max(all_im) + 1
        # Ensure symmetric about real axis
        im_abs = max(abs(im_min), abs(im_max), 1.0)
        im_min = -im_abs
        im_max = im_abs

        # Clamp to reasonable bounds
        re_min = max(re_min, -50)
        re_max = min(re_max, 50)
        im_min = max(im_min, -50)
        im_max = min(im_max, 50)

        # RHP shading
        shapes.append({
            "type": "rect",
            "x0": 0, "x1": re_max + 10,
            "y0": im_min - 10, "y1": im_max + 10,
            "fillcolor": self.UNSTABLE_FILL,
            "line": {"width": 0},
            "layer": "below",
        })

        # Overlays
        show_damping = self.parameters.get("show_damping_lines", True)
        show_wn = self.parameters.get("show_wn_circles", False)
        show_asymp = self.parameters.get("show_asymptotes", True)
        show_annot = self.parameters.get("show_annotations", True)

        # Damping ratio lines
        if show_damping:
            for zeta in self.ZETA_VALUES:
                if zeta <= 0 or zeta >= 1:
                    continue
                angle = np.arccos(zeta)
                r = max(abs(im_max), abs(re_min))
                x_end = -r * np.cos(angle)
                # Upper line
                shapes.append({
                    "type": "line",
                    "x0": 0, "y0": 0,
                    "x1": float(x_end),
                    "y1": float(r * np.sin(angle)),
                    "line": {"color": "rgba(148, 163, 184, 0.2)", "width": 1, "dash": "dot"},
                    "layer": "below",
                })
                # Lower line
                shapes.append({
                    "type": "line",
                    "x0": 0, "y0": 0,
                    "x1": float(x_end),
                    "y1": float(-r * np.sin(angle)),
                    "line": {"color": "rgba(148, 163, 184, 0.2)", "width": 1, "dash": "dot"},
                    "layer": "below",
                })
                # Label
                annotations_list.append({
                    "x": float(x_end * 0.35),
                    "y": float(r * np.sin(angle) * 0.35),
                    "text": f"ζ={zeta}",
                    "showarrow": False,
                    "font": {"size": 9, "color": "rgba(148, 163, 184, 0.5)"},
                })

        # Natural frequency circles
        if show_wn:
            for wn in self.WN_VALUES:
                if wn > max(abs(re_min), im_abs) * 1.5:
                    continue
                theta = np.linspace(np.pi / 2, 3 * np.pi / 2, 50)
                traces.append({
                    "x": [float(wn * np.cos(t)) for t in theta],
                    "y": [float(wn * np.sin(t)) for t in theta],
                    "type": "scatter",
                    "mode": "lines",
                    "line": {"color": "rgba(148, 163, 184, 0.2)", "width": 1, "dash": "dot"},
                    "showlegend": False,
                    "hoverinfo": "skip",
                })

        # Asymptotes
        if show_asymp and self._cached_special:
            asym = self._cached_special.get("asymptotes", {})
            centroid = asym.get("centroid", 0)
            angles = asym.get("angles", [])
            if angles:
                r_asym = max(abs(re_max - centroid), abs(re_min - centroid), im_abs) * 1.5
                for angle_deg in angles:
                    angle_rad = np.radians(angle_deg)
                    x_end = centroid + r_asym * np.cos(angle_rad)
                    y_end = r_asym * np.sin(angle_rad)
                    shapes.append({
                        "type": "line",
                        "x0": float(centroid), "y0": 0,
                        "x1": float(x_end), "y1": float(y_end),
                        "line": {"color": "rgba(20, 184, 166, 0.4)", "width": 1.5, "dash": "dashdot"},
                        "layer": "below",
                    })
                # Centroid marker
                traces.append({
                    "x": [float(centroid)],
                    "y": [0.0],
                    "type": "scatter",
                    "mode": "markers",
                    "marker": {"symbol": "cross", "size": 8, "color": "#14b8a6"},
                    "name": "Centroid",
                    "showlegend": False,
                    "hovertemplate": f"Centroid: σ = {centroid:.3f}<extra></extra>",
                })

        # Annotations for special points
        if show_annot and self._cached_special:
            # Breakaway points
            for bp in self._cached_special.get("breakaway", []):
                s_val = bp["s"]
                annotations_list.append({
                    "x": s_val["real"],
                    "y": s_val["imag"],
                    "text": f"B/A (K={bp['K']:.2f})",
                    "showarrow": True,
                    "arrowhead": 2,
                    "arrowsize": 0.8,
                    "font": {"size": 10, "color": "#10b981"},
                    "bgcolor": "rgba(10, 14, 39, 0.8)",
                    "bordercolor": "#10b981",
                    "borderwidth": 1,
                })

            # jω crossings
            for jw in self._cached_special.get("jw_crossings", []):
                annotations_list.append({
                    "x": 0,
                    "y": jw["omega"],
                    "text": f"jω (K={jw['K']:.2f})",
                    "showarrow": True,
                    "arrowhead": 2,
                    "arrowsize": 0.8,
                    "font": {"size": 10, "color": "#f59e0b"},
                    "bgcolor": "rgba(10, 14, 39, 0.8)",
                    "bordercolor": "#f59e0b",
                    "borderwidth": 1,
                })
                # Also annotate at -omega
                if jw["omega"] > 0.1:
                    annotations_list.append({
                        "x": 0,
                        "y": -jw["omega"],
                        "text": f"jω (K={jw['K']:.2f})",
                        "showarrow": True,
                        "arrowhead": 2,
                        "arrowsize": 0.8,
                        "font": {"size": 10, "color": "#f59e0b"},
                        "bgcolor": "rgba(10, 14, 39, 0.8)",
                        "bordercolor": "#f59e0b",
                        "borderwidth": 1,
                    })

        import time
        layout = {
            "title": {"text": "Root Locus", "font": {"size": 16, "color": self.TEXT_COLOR}},
            "paper_bgcolor": self.PAPER_BG,
            "plot_bgcolor": self.PLOT_BG,
            "font": {"family": "Inter, sans-serif", "size": 12, "color": self.TEXT_COLOR},
            "xaxis": {
                "title": "Real (σ)",
                "gridcolor": self.GRID_COLOR,
                "zerolinecolor": self.ZERO_LINE_COLOR,
                "zerolinewidth": 2,
                "range": [re_min, re_max],
                "showline": True,
                "linecolor": "rgba(148, 163, 184, 0.3)",
            },
            "yaxis": {
                "title": "Imaginary (jω)",
                "gridcolor": self.GRID_COLOR,
                "zerolinecolor": self.ZERO_LINE_COLOR,
                "zerolinewidth": 2,
                "range": [im_min, im_max],
                "scaleanchor": "x",
                "scaleratio": 1,
                "showline": True,
                "linecolor": "rgba(148, 163, 184, 0.3)",
            },
            "shapes": shapes,
            "annotations": annotations_list,
            "showlegend": True,
            "legend": {
                "x": 0.01, "y": 0.99,
                "bgcolor": "rgba(19, 27, 46, 0.8)",
                "bordercolor": "rgba(148, 163, 184, 0.3)",
                "font": {"size": 10},
            },
            "margin": {"t": 50, "r": 30, "b": 60, "l": 65},
            "datarevision": f"rl-{time.time()}",
            "uirevision": "root_locus_splane",
        }

        return {"id": "root_locus", "title": "Root Locus", "data": traces, "layout": layout}

    def _build_step_response_plot(self) -> Dict:
        """Build step response plot at current K."""
        import time

        K = float(self.parameters["gain_K"])
        negative = bool(self.parameters["negative_k"])
        if negative:
            K = -K

        traces = []
        t_max = 10.0

        try:
            num_cl = K * self._num
            num_padded = np.zeros_like(self._den)
            offset = len(self._den) - len(self._num)
            num_padded[offset:] = self._num
            den_cl = self._den + K * num_padded

            # Check if system is proper
            if len(num_cl) > len(den_cl):
                raise ValueError("Improper system")

            tf = signal.TransferFunction(num_cl, den_cl)

            # Estimate appropriate time range
            cl_poles = np.roots(den_cl)
            real_parts = np.real(cl_poles)
            stable_poles = real_parts[real_parts < 0]
            if len(stable_poles) > 0:
                slowest = np.max(stable_poles)  # least negative
                t_max = min(max(5.0 / abs(slowest), 2.0), 50.0)

            t = np.linspace(0, t_max, 1000)
            t_out, y_out = signal.step(tf, T=t)

            # Clamp for unstable systems
            y_clamped = np.clip(y_out, -100, 100)

            traces.append({
                "x": t_out.tolist(),
                "y": y_clamped.tolist(),
                "type": "scatter",
                "mode": "lines",
                "line": {"color": "#3b82f6", "width": 2},
                "name": "Step Response",
            })

            # Steady-state reference line
            if np.all(np.real(cl_poles) < -1e-6):
                ss_val = float(np.polyval(num_cl, 0) / np.polyval(den_cl, 0)) if abs(np.polyval(den_cl, 0)) > 1e-12 else None
                if ss_val is not None and np.isfinite(ss_val):
                    traces.append({
                        "x": [0, float(t_max)],
                        "y": [ss_val, ss_val],
                        "type": "scatter",
                        "mode": "lines",
                        "line": {"color": "#10b981", "width": 1.5, "dash": "dash"},
                        "name": f"Steady State ({ss_val:.3f})",
                    })

                    # Unit step reference
                    traces.append({
                        "x": [0, float(t_max)],
                        "y": [1.0, 1.0],
                        "type": "scatter",
                        "mode": "lines",
                        "line": {"color": "rgba(148, 163, 184, 0.3)", "width": 1, "dash": "dot"},
                        "name": "Reference",
                        "showlegend": False,
                    })

        except Exception as e:
            # Show error trace
            traces.append({
                "x": [0, 1],
                "y": [0, 0],
                "type": "scatter",
                "mode": "lines",
                "line": {"color": "#ef4444", "width": 1},
                "name": f"Error: {str(e)[:50]}",
            })

        layout = {
            "title": {"text": f"Step Response (K = {abs(float(self.parameters['gain_K'])):.2f})", "font": {"size": 14, "color": self.TEXT_COLOR}},
            "paper_bgcolor": self.PAPER_BG,
            "plot_bgcolor": self.PLOT_BG,
            "font": {"family": "Inter, sans-serif", "size": 12, "color": self.TEXT_COLOR},
            "xaxis": {
                "title": "Time (s)",
                "gridcolor": self.GRID_COLOR,
                "zerolinecolor": self.ZERO_LINE_COLOR,
            },
            "yaxis": {
                "title": "Amplitude",
                "gridcolor": self.GRID_COLOR,
                "zerolinecolor": self.ZERO_LINE_COLOR,
            },
            "showlegend": True,
            "legend": {"x": 0.6, "y": 0.98, "font": {"size": 10}},
            "margin": {"t": 45, "r": 25, "b": 50, "l": 55},
            "height": 280,
            "datarevision": f"step-{time.time()}",
            "uirevision": "root_locus_step",
        }

        return {"id": "step_response", "title": "Step Response", "data": traces, "layout": layout}

    def _build_performance_plot(self) -> Dict:
        """Build ζ and ωn vs K sweep plot."""
        import time

        traces = []
        K_current = float(self.parameters["gain_K"])
        k_max = float(self.parameters["k_max"])
        negative = bool(self.parameters["negative_k"])

        # Sweep K and compute dominant pole metrics
        k_sweep = np.linspace(0.01, k_max, 200)
        zeta_vals = []
        wn_vals = []

        for k in k_sweep:
            k_actual = -k if negative else k
            cl_p = self._cl_poles_at_k(k_actual)
            dom = self._get_dominant_poles(cl_p)
            if dom:
                zeta_vals.append(dom[0]["zeta"])
                wn_vals.append(dom[0]["wn"])
            else:
                zeta_vals.append(None)
                wn_vals.append(None)

        # ζ vs K
        traces.append({
            "x": k_sweep.tolist(),
            "y": zeta_vals,
            "type": "scatter",
            "mode": "lines",
            "line": {"color": "#3b82f6", "width": 2},
            "name": "Damping Ratio ζ",
            "yaxis": "y",
        })

        # ωn vs K (right axis)
        traces.append({
            "x": k_sweep.tolist(),
            "y": wn_vals,
            "type": "scatter",
            "mode": "lines",
            "line": {"color": "#10b981", "width": 2},
            "name": "Natural Freq ωₙ",
            "yaxis": "y2",
        })

        # Current K line
        traces.append({
            "x": [K_current, K_current],
            "y": [0, max(z for z in zeta_vals if z is not None) * 1.2 if any(z for z in zeta_vals if z is not None) else 1],
            "type": "scatter",
            "mode": "lines",
            "line": {"color": "#f59e0b", "width": 2, "dash": "dash"},
            "name": f"K = {K_current:.2f}",
            "yaxis": "y",
        })

        # Mark unstable region
        jw_crossings = (self._cached_special or {}).get("jw_crossings", [])
        shapes = []
        for jw in jw_crossings:
            shapes.append({
                "type": "rect",
                "x0": jw["K"], "x1": k_max,
                "y0": 0, "y1": 100,
                "fillcolor": "rgba(239, 68, 68, 0.08)",
                "line": {"width": 0},
                "layer": "below",
            })

        layout = {
            "title": {"text": "Performance vs Gain", "font": {"size": 14, "color": self.TEXT_COLOR}},
            "paper_bgcolor": self.PAPER_BG,
            "plot_bgcolor": self.PLOT_BG,
            "font": {"family": "Inter, sans-serif", "size": 12, "color": self.TEXT_COLOR},
            "xaxis": {
                "title": "Gain K",
                "gridcolor": self.GRID_COLOR,
                "zerolinecolor": self.ZERO_LINE_COLOR,
            },
            "yaxis": {
                "title": "Damping Ratio ζ",
                "gridcolor": self.GRID_COLOR,
                "zerolinecolor": self.ZERO_LINE_COLOR,
                "titlefont": {"color": "#3b82f6"},
                "tickfont": {"color": "#3b82f6"},
                "range": [0, 2],
            },
            "yaxis2": {
                "title": "Natural Freq ωₙ (rad/s)",
                "overlaying": "y",
                "side": "right",
                "titlefont": {"color": "#10b981"},
                "tickfont": {"color": "#10b981"},
                "gridcolor": "rgba(148, 163, 184, 0.05)",
            },
            "shapes": shapes,
            "showlegend": True,
            "legend": {"x": 0.01, "y": 0.99, "font": {"size": 10}},
            "margin": {"t": 45, "r": 65, "b": 50, "l": 55},
            "height": 250,
            "datarevision": f"perf-{time.time()}",
            "uirevision": "root_locus_perf",
        }

        return {"id": "performance_vs_k", "title": "Performance vs Gain", "data": traces, "layout": layout}

    # =========================================================================
    # Actions
    # =========================================================================

    def _action_click_select_k(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Find K corresponding to clicked point on s-plane."""
        sigma = float(params.get("sigma", 0))
        omega = float(params.get("omega", 0))
        clicked = complex(sigma, omega)

        if self._cached_branches is None or self._cached_k_values is None:
            return self.get_state()

        # Find nearest branch point
        best_k = float(self.parameters["gain_K"])
        best_dist = np.inf

        k_values = self._cached_k_values
        for branch in self._cached_branches:
            for i, p in enumerate(branch):
                if np.isnan(p):
                    continue
                d = abs(p - clicked)
                if d < best_dist:
                    best_dist = d
                    best_k = abs(float(k_values[i]))

        self.parameters["gain_K"] = min(best_k, float(self.parameters["k_max"]))
        return self.get_state()

    def _action_load_preset(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Load a preset system."""
        preset_id = params.get("preset_id", "")
        if preset_id in self.PRESET_SYSTEMS:
            num_str, den_str, _ = self.PRESET_SYSTEMS[preset_id]
            self.parameters["num_coeffs"] = num_str
            self.parameters["den_coeffs"] = den_str
            self.parameters["preset"] = preset_id
            self._parse_coefficients()
            self._invalidate_cache()
        return self.get_state()

    def _action_move_pole(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Move an open-loop pole to a new location."""
        index = int(params.get("index", 0))
        new_real = float(params.get("real", 0))
        new_imag = float(params.get("imag", 0))

        poles = np.roots(self._den) if len(self._den) > 1 else np.array([])
        if index < 0 or index >= len(poles):
            return self.get_state()

        # Convert to complex array so we can assign complex values
        poles = poles.astype(complex)
        old_pole = poles[index]
        new_pole = complex(new_real, new_imag)
        poles[index] = new_pole

        # If the old pole was complex, also move its conjugate
        if abs(np.imag(old_pole)) > 1e-6:
            conj = np.conj(old_pole)
            for j, p in enumerate(poles):
                if j != index and abs(p - conj) < 1e-6:
                    poles[j] = np.conj(new_pole)
                    break

        # Reconstruct denominator from poles
        new_den = np.real(np.poly(poles))
        self._den = new_den
        self.parameters["den_coeffs"] = ", ".join(f"{c:.6g}" for c in new_den)
        self.parameters["preset"] = "custom"
        self._invalidate_cache()
        return self.get_state()

    def _action_move_zero(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Move an open-loop zero to a new location."""
        index = int(params.get("index", 0))
        new_real = float(params.get("real", 0))
        new_imag = float(params.get("imag", 0))

        zeros = np.roots(self._num) if len(self._num) > 1 else np.array([])
        if index < 0 or index >= len(zeros):
            return self.get_state()

        # Convert to complex array so we can assign complex values
        zeros = zeros.astype(complex)
        old_zero = zeros[index]
        new_zero = complex(new_real, new_imag)
        zeros[index] = new_zero

        if abs(np.imag(old_zero)) > 1e-6:
            conj = np.conj(old_zero)
            for j, z in enumerate(zeros):
                if j != index and abs(z - conj) < 1e-6:
                    zeros[j] = np.conj(new_zero)
                    break

        new_num = np.real(np.poly(zeros))
        self._num = new_num
        self.parameters["num_coeffs"] = ", ".join(f"{c:.6g}" for c in new_num)
        self.parameters["preset"] = "custom"
        self._invalidate_cache()
        return self.get_state()

    def _action_import_tf(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Import transfer function from Block Diagram Builder."""
        numerator = params.get("numerator", [])
        denominator = params.get("denominator", [])

        if isinstance(numerator, str):
            numerator = [float(x.strip()) for x in numerator.split(",") if x.strip()]
        if isinstance(denominator, str):
            denominator = [float(x.strip()) for x in denominator.split(",") if x.strip()]

        if not numerator or not denominator:
            self._error = "Import failed: empty numerator or denominator"
            return self.get_state()

        self.parameters["num_coeffs"] = ", ".join(str(c) for c in numerator)
        self.parameters["den_coeffs"] = ", ".join(str(c) for c in denominator)
        self.parameters["preset"] = "custom"
        self._parse_coefficients()
        self._invalidate_cache()
        return self.get_state()

    # =========================================================================
    # Helpers
    # =========================================================================

    def _poly_to_str(self, coeffs: np.ndarray) -> str:
        """Convert polynomial coefficients to display string like 's² + 3s + 2'."""
        n = len(coeffs) - 1
        if n < 0:
            return "0"

        terms = []
        superscripts = {"0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴",
                        "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹"}

        for i, c in enumerate(coeffs):
            power = n - i
            if abs(c) < 1e-10:
                continue

            # Coefficient display
            if power == 0:
                coeff_str = f"{c:.4g}"
            elif abs(c) == 1:
                coeff_str = "" if c == 1 else "-"
            else:
                coeff_str = f"{c:.4g}"

            # Variable part
            if power == 0:
                var_str = ""
            elif power == 1:
                var_str = "s"
            else:
                sup = "".join(superscripts.get(d, d) for d in str(power))
                var_str = f"s{sup}"

            term = f"{coeff_str}{var_str}"
            terms.append(term)

        if not terms:
            return "0"

        result = terms[0]
        for term in terms[1:]:
            if term.startswith("-"):
                result += f" - {term[1:]}"
            else:
                result += f" + {term}"

        return result

    def _serialize_special_points(self, special: Dict) -> Dict:
        """Ensure all special points are JSON-serializable."""
        serialized = {}
        for key, value in special.items():
            if isinstance(value, list):
                serialized[key] = []
                for item in value:
                    if isinstance(item, dict):
                        s_item = {}
                        for k, v in item.items():
                            if isinstance(v, dict):
                                s_item[k] = {sk: float(sv) if isinstance(sv, (int, float, np.floating)) else sv for sk, sv in v.items()}
                            elif isinstance(v, (np.floating, np.integer)):
                                s_item[k] = float(v)
                            else:
                                s_item[k] = v
                        serialized[key].append(s_item)
                    else:
                        serialized[key].append(value)
            elif isinstance(value, dict):
                s_dict = {}
                for k, v in value.items():
                    if isinstance(v, (np.floating, np.integer)):
                        s_dict[k] = float(v)
                    elif isinstance(v, list):
                        s_dict[k] = [float(x) if isinstance(x, (np.floating, np.integer)) else x for x in v]
                    else:
                        s_dict[k] = v
                serialized[key] = s_dict
            else:
                serialized[key] = value
        return serialized
