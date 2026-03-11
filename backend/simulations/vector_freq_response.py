"""
Vector Diagram Frequency Response Builder Simulator

Recreates the animated vector-diagram-to-frequency-response construction from
MIT 6.003 Lecture 9 (slides 26–56). Users configure poles, zeros, and gain
via a LaTeX-style transfer function expression or presets.
The backend computes the full frequency response and per-factor contributions.
The frontend custom viewer animates the ω sweep with synchronized vectors.

Based on MIT 6.003 Lecture 09: Frequency Response.
"""

import re
import numpy as np
from typing import Any, Dict, List, Optional, Tuple

from .base_simulator import BaseSimulator


class VectorFreqResponseSimulator(BaseSimulator):
    """
    Vector Diagram Frequency Response simulation.

    For H(s) = K × N(s)/D(s), computes:
    - Poles/zeros from polynomial coefficients via np.roots
    - Full |H(jω)| and ∠H(jω) over a frequency sweep
    - Per-factor magnitudes and phases for individual contribution views
    - Static s-plane plot with poles and zeros

    Accepts transfer functions as:
    - Inline expressions: (s+1)/(s^2+2s+1)
    - Comma-separated coefficients: num_coeffs / den_coeffs
    - Presets with pedagogical defaults
    """

    # Colors
    POLE_COLOR = "#ef4444"
    ZERO_COLOR = "#3b82f6"
    JW_AXIS_COLOR = "#a855f7"
    PHASE_COLOR = "#ef4444"
    MAG_COLOR = "#3b82f6"
    TEAL_COLOR = "#14b8a6"
    GREEN_COLOR = "#10b981"
    GRID_COLOR = "rgba(148, 163, 184, 0.15)"
    ZEROLINE_COLOR = "rgba(148, 163, 184, 0.3)"
    LEGEND_BG = "rgba(15, 23, 42, 0.8)"
    LEGEND_BORDER = "rgba(148, 163, 184, 0.2)"

    # Numerical constants
    NUM_POINTS = 500
    MAX_MAG_CLIP = 50.0
    MIN_AXIS_RANGE = 2.0
    AXIS_PADDING = 1.5

    # Preset TF expressions: {num_coeffs, den_coeffs, gain, name, description}
    PRESETS = {
        "single_pole": {
            "num_coeffs": "1",
            "den_coeffs": "1, 3",
            "gain": 3.0,
            "name": "Single Real Pole",
            "description": "H(s) = 3/(s + 3) — first-order low-pass",
        },
        "single_zero": {
            "num_coeffs": "1, 2",
            "den_coeffs": "1",
            "gain": 1.0,
            "name": "Single Real Zero",
            "description": "H(s) = (s + 2) — first-order high-pass factor",
        },
        "pole_zero_pair": {
            "num_coeffs": "1, 2",
            "den_coeffs": "1, 4",
            "gain": 3.0,
            "name": "Pole-Zero Pair",
            "description": "H(s) = 3(s + 2)/(s + 4) — lead network",
        },
        "conjugate_poles": {
            "num_coeffs": "1",
            "den_coeffs": "1, 2, 10",
            "gain": 10.0,
            "name": "Conjugate Pole Pair",
            "description": "H(s) = 10/(s² + 2s + 10) — resonant second-order",
        },
        "complex_system": {
            "num_coeffs": "1, 1",
            "den_coeffs": "1, 2, 10",
            "gain": 10.0,
            "name": "Complex System",
            "description": "H(s) = 10(s + 1)/(s² + 2s + 10) — zero near resonance",
        },
        "custom": {
            "num_coeffs": "1",
            "den_coeffs": "1, 3",
            "gain": 1.0,
            "name": "Custom",
            "description": "Enter your own transfer function",
        },
    }

    PARAMETER_SCHEMA = {
        "preset": {
            "type": "select",
            "options": [
                {"value": "single_pole", "label": "Single Real Pole: 3/(s + 3)"},
                {"value": "single_zero", "label": "Single Real Zero: (s + 2)"},
                {"value": "pole_zero_pair", "label": "Pole-Zero Pair: 3(s+2)/(s+4)"},
                {"value": "conjugate_poles", "label": "Conjugate Poles: 10/(s²+2s+10)"},
                {"value": "complex_system", "label": "Complex: 10(s+1)/(s²+2s+10)"},
                {"value": "custom", "label": "Custom Expression"},
            ],
            "default": "single_pole",
        },
        "num_coeffs": {"type": "expression", "default": "1"},
        "den_coeffs": {"type": "expression", "default": "1, 3"},
        "gain": {"type": "slider", "min": 0.1, "max": 50.0, "step": 0.1, "default": 3.0},
        "omega_max": {"type": "slider", "min": 1.0, "max": 30.0, "step": 0.5, "default": 8.0},
        "show_individual": {"type": "checkbox", "default": False},
    }

    DEFAULT_PARAMS = {
        "preset": "single_pole",
        "num_coeffs": "1",
        "den_coeffs": "1, 3",
        "gain": 3.0,
        "omega_max": 8.0,
        "show_individual": False,
    }

    def __init__(self, simulation_id: str):
        super().__init__(simulation_id)
        self._num: np.ndarray = np.array([1.0])
        self._den: np.ndarray = np.array([1.0, 3.0])
        self._poles: List[complex] = []
        self._zeros: List[complex] = []
        self._gain: float = 3.0
        self._omega: np.ndarray = np.array([])
        self._h_jw: np.ndarray = np.array([])
        self._magnitude: np.ndarray = np.array([])
        self._phase: np.ndarray = np.array([])
        self._individual_zero_mags: List[np.ndarray] = []
        self._individual_zero_phases: List[np.ndarray] = []
        self._individual_pole_mags: List[np.ndarray] = []
        self._individual_pole_phases: List[np.ndarray] = []
        self._error: Optional[str] = None

    def initialize(self, params: Optional[Dict[str, Any]] = None) -> None:
        """Initialize simulation with parameters."""
        self.parameters = self.DEFAULT_PARAMS.copy()
        if params:
            for name, value in params.items():
                if name in self.parameters:
                    self.parameters[name] = self._validate_param(name, value)
        self._initialized = True
        self._apply_preset_defaults()
        self._parse_coefficients()
        self._compute()

    def update_parameter(self, name: str, value: Any) -> Dict[str, Any]:
        """Update a single parameter and recompute."""
        old_preset = self.parameters.get("preset")

        if name in self.parameters:
            self.parameters[name] = self._validate_param(name, value)

        # When preset changes, load its defaults
        if name == "preset" and value != old_preset:
            self._apply_preset_defaults()

        self._parse_coefficients()
        self._compute()
        return self.get_state()

    def reset(self) -> Dict[str, Any]:
        """Reset to default parameters."""
        self.parameters = self.DEFAULT_PARAMS.copy()
        self._error = None
        self._initialized = True
        self._apply_preset_defaults()
        self._parse_coefficients()
        self._compute()
        return self.get_state()

    def execute(self, action: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle custom actions."""
        params = params or {}
        if action == "parse_expression":
            return self._action_parse_expression(params)
        elif action == "reset":
            return self.reset()
        elif action in ("init", "run", "update"):
            if params:
                for k, v in params.items():
                    if k in self.parameters:
                        self.parameters[k] = self._validate_param(k, v)
                self._parse_coefficients()
                self._compute()
            return self.get_state()
        return self.get_state()

    # =========================================================================
    # Preset management
    # =========================================================================

    def _apply_preset_defaults(self) -> None:
        """Apply preset-specific defaults."""
        preset = self.parameters["preset"]
        if preset not in self.PRESETS or preset == "custom":
            return

        config = self.PRESETS[preset]
        self.parameters["num_coeffs"] = config["num_coeffs"]
        self.parameters["den_coeffs"] = config["den_coeffs"]
        self.parameters["gain"] = config["gain"]

    # =========================================================================
    # TF Expression Parser (adapted from root locus)
    # =========================================================================

    def _action_parse_expression(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Parse a TF expression like '(s+1)/(s^2+2s+1)' and update."""
        expr = str(params.get("expression", "")).strip()
        if not expr:
            self._error = "Empty expression"
            return self.get_state()

        try:
            num_str, den_str = self._parse_tf_expression(expr)
            self.parameters["num_coeffs"] = num_str
            self.parameters["den_coeffs"] = den_str
            self.parameters["preset"] = "custom"
            self._error = None
            self._parse_coefficients()
            self._compute()
        except Exception as e:
            self._error = f"Parse error: {str(e)}"

        return self.get_state()

    def _parse_tf_expression(self, expr: str) -> Tuple[str, str]:
        """Parse a TF expression into coefficient strings.

        Returns (num_coeffs_str, den_coeffs_str) as comma-separated strings
        in descending power order.
        """
        expr = expr.strip()
        # Remove H(s) = or G(s) = prefix
        expr = re.sub(r'[GH]\s*\(\s*s\s*\)\s*=\s*', '', expr).strip()

        # Find the division point — '/' not inside parentheses
        split_idx = -1
        depth = 0
        for i, ch in enumerate(expr):
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
            elif ch == '/' and depth == 0:
                split_idx = i
                break

        if split_idx >= 0:
            num_str = self._strip_outer_parens(expr[:split_idx])
            den_str = self._strip_outer_parens(expr[split_idx + 1:])
        else:
            num_str = self._strip_outer_parens(expr)
            den_str = "1"

        num_coeffs = self._parse_polynomial_expr(num_str)
        den_coeffs = self._parse_polynomial_expr(den_str)

        return (
            ", ".join(f"{c:.6g}" for c in num_coeffs),
            ", ".join(f"{c:.6g}" for c in den_coeffs),
        )

    @staticmethod
    def _strip_outer_parens(s: str) -> str:
        """Strip matched outer parentheses: '((s+1))' -> 's+1'."""
        s = s.strip()
        while len(s) >= 2 and s[0] == '(' and s[-1] == ')':
            depth = 0
            matched = True
            for i, ch in enumerate(s):
                if ch == '(':
                    depth += 1
                elif ch == ')':
                    depth -= 1
                if depth == 0 and i < len(s) - 1:
                    matched = False
                    break
            if matched:
                s = s[1:-1].strip()
            else:
                break
        return s

    def _parse_polynomial_expr(self, poly_str: str) -> List[float]:
        """Parse polynomial expression like 's^2 + 3s + 1' or '(s+1)(s+3)'.

        Returns coefficients in descending power order.
        """
        poly_str = poly_str.strip()
        if not poly_str or poly_str == "0":
            return [0.0]

        # Pure number
        try:
            val = float(poly_str)
            return [val]
        except ValueError:
            pass

        # Check for factored form
        factored = self._try_parse_factored(poly_str)
        if factored is not None:
            return factored

        # Polynomial form: s^2 + 3s + 1
        return self._parse_expanded_poly(poly_str)

    def _try_parse_factored(self, expr: str) -> Optional[List[float]]:
        """Try to parse as product of factors like (s+1)(s-2) or s(s+1).

        Returns coefficients (high-power-first) or None if not factored form.
        """
        expr = expr.strip()
        factors: List[List[float]] = []
        leading_coeff = 1.0
        i = 0

        # Try to extract leading coefficient
        coeff_match = re.match(r'^(-?\d*\.?\d+)\s*\*?\s*(?=[\(s])', expr)
        if coeff_match:
            leading_coeff = float(coeff_match.group(1))
            i = coeff_match.end()

        while i < len(expr):
            ch = expr[i]
            if ch in (' ', '*'):
                i += 1
                continue

            if ch == '(':
                depth = 1
                j = i + 1
                while j < len(expr) and depth > 0:
                    if expr[j] == '(':
                        depth += 1
                    elif expr[j] == ')':
                        depth -= 1
                    j += 1
                factor_str = expr[i + 1:j - 1].strip()
                factor_coeffs = self._parse_expanded_poly(factor_str)
                factors.append(factor_coeffs)
                i = j
            elif expr[i:i + 1].lower() == 's':
                power_match = re.match(r's\s*\^\s*(\d+)', expr[i:])
                if power_match:
                    power = int(power_match.group(1))
                    factor = [1.0] + [0.0] * power
                    factors.append(factor)
                    i += power_match.end()
                else:
                    factors.append([1.0, 0.0])
                    i += 1
            else:
                return None

        if not factors:
            return None

        result = np.array([leading_coeff])
        for f in factors:
            result = np.polymul(result, np.array(f))
        return [float(c) for c in result]

    def _parse_expanded_poly(self, poly_str: str) -> List[float]:
        """Parse expanded polynomial like 's^2 + 3s + 1'."""
        poly_str = poly_str.strip()
        if not poly_str or poly_str == "0":
            return [0.0]

        try:
            val = float(poly_str)
            return [val]
        except ValueError:
            pass

        terms = self._tokenize_poly_terms(poly_str)
        coeffs: Dict[int, float] = {}

        for term in terms:
            term = term.strip()
            if not term:
                continue

            has_s = bool(re.search(r's', term, re.IGNORECASE))

            if not has_s:
                try:
                    coeffs[0] = coeffs.get(0, 0) + float(term.replace(" ", ""))
                except ValueError:
                    pass
                continue

            power_match = re.search(r's\s*\^\s*(-?\d+)', term, re.IGNORECASE)
            if power_match:
                power = int(power_match.group(1))
            else:
                power = 1

            coeff_str = re.sub(r'\s*\*?\s*s(\s*\^\s*-?\d+)?', '', term, flags=re.IGNORECASE).strip()
            coeff_str = coeff_str.rstrip("*").strip().replace(" ", "")

            if coeff_str in ("", "+"):
                coeff = 1.0
            elif coeff_str == "-":
                coeff = -1.0
            else:
                try:
                    coeff = float(coeff_str)
                except ValueError:
                    coeff = 1.0

            coeffs[power] = coeffs.get(power, 0) + coeff

        if not coeffs:
            return [1.0]

        max_power = max(coeffs.keys())
        return [coeffs.get(i, 0.0) for i in range(max_power, -1, -1)]

    @staticmethod
    def _tokenize_poly_terms(poly_str: str) -> List[str]:
        """Split polynomial string into signed terms."""
        terms: List[str] = []
        current = ""
        s = poly_str.strip()
        i = 0

        while i < len(s):
            ch = s[i]
            if ch in ('+', '-') and i > 0:
                j = i - 1
                while j >= 0 and s[j] == ' ':
                    j -= 1
                if j >= 0 and s[j] == '^':
                    current += ch
                    i += 1
                    continue
                if current.strip():
                    terms.append(current.strip())
                current = ch if ch == '-' else ""
                i += 1
                continue
            current += ch
            i += 1

        if current.strip():
            terms.append(current.strip())

        return terms

    # =========================================================================
    # Coefficient parsing and pole/zero extraction
    # =========================================================================

    def _parse_coefficients(self) -> None:
        """Parse num_coeffs/den_coeffs strings into arrays and extract poles/zeros."""
        self._error = None

        try:
            num_str = str(self.parameters.get("num_coeffs", "1")).strip()
            den_str = str(self.parameters.get("den_coeffs", "1")).strip()

            num_list = [float(x.strip()) for x in num_str.split(",") if x.strip()]
            den_list = [float(x.strip()) for x in den_str.split(",") if x.strip()]

            if not num_list:
                num_list = [1.0]
            if not den_list:
                den_list = [1.0]

            self._num = np.array(num_list, dtype=float)
            self._den = np.array(den_list, dtype=float)

            # Extract poles and zeros via np.roots
            if len(self._num) > 1:
                self._zeros = list(np.roots(self._num))
            else:
                self._zeros = []

            if len(self._den) > 1:
                self._poles = list(np.roots(self._den))
            else:
                self._poles = []

            self._gain = float(self.parameters.get("gain", 1.0))

        except Exception as e:
            self._error = f"Coefficient error: {str(e)}"
            self._num = np.array([1.0])
            self._den = np.array([1.0, 1.0])
            self._poles = [complex(-1, 0)]
            self._zeros = []
            self._gain = 1.0

    # =========================================================================
    # Core computation
    # =========================================================================

    def _compute(self) -> None:
        """Compute the full frequency response and per-factor data."""
        omega_max = float(self.parameters["omega_max"])
        self._omega = np.linspace(-omega_max, omega_max, self.NUM_POINTS)
        s = 1j * self._omega

        # Compute H(jω) = K × N(jω) / D(jω) using factor form
        numerator = np.ones(self.NUM_POINTS, dtype=complex) * self._gain
        denominator = np.ones(self.NUM_POINTS, dtype=complex)

        # Per-zero contributions
        self._individual_zero_mags = []
        self._individual_zero_phases = []
        for z in self._zeros:
            factor = s - z
            numerator *= factor
            self._individual_zero_mags.append(np.abs(factor))
            self._individual_zero_phases.append(np.angle(factor))

        # Per-pole contributions
        self._individual_pole_mags = []
        self._individual_pole_phases = []
        for p in self._poles:
            factor = s - p
            denominator *= factor
            self._individual_pole_mags.append(np.abs(factor))
            self._individual_pole_phases.append(np.angle(factor))

        # Compute H(jω) with safeguard
        with np.errstate(divide='ignore', invalid='ignore'):
            self._h_jw = np.where(
                np.abs(denominator) < 1e-12,
                self.MAX_MAG_CLIP * np.exp(1j * np.angle(numerator)),
                numerator / denominator
            )

        self._magnitude = np.clip(np.abs(self._h_jw), 0, self.MAX_MAG_CLIP)
        self._phase = np.unwrap(np.angle(self._h_jw))

    # =========================================================================
    # Expression formatting
    # =========================================================================

    def _format_num_display(self) -> str:
        """Format numerator polynomial for LaTeX display."""
        return self._poly_to_latex(self._num)

    def _format_den_display(self) -> str:
        """Format denominator polynomial for LaTeX display."""
        return self._poly_to_latex(self._den)

    @staticmethod
    def _poly_to_latex(coeffs: np.ndarray) -> str:
        """Convert coefficient array to LaTeX polynomial string."""
        n = len(coeffs) - 1
        if n < 0:
            return "0"
        if n == 0:
            return f"{coeffs[0]:.4g}"

        terms = []
        for i, c in enumerate(coeffs):
            power = n - i
            if abs(c) < 1e-10:
                continue

            # Coefficient display
            if power == 0:
                coeff_str = f"{abs(c):.4g}"
            elif abs(abs(c) - 1.0) < 1e-10:
                coeff_str = ""
            else:
                coeff_str = f"{abs(c):.4g}"

            # Variable display
            if power == 0:
                var_str = ""
            elif power == 1:
                var_str = "s"
            else:
                var_str = f"s^{{{power}}}"

            # Sign
            if len(terms) == 0:
                sign = "-" if c < 0 else ""
            else:
                sign = " - " if c < 0 else " + "

            terms.append(f"{sign}{coeff_str}{var_str}")

        return "".join(terms) if terms else "0"

    def _format_hs_expression(self) -> str:
        """Format H(s) as a readable text string."""
        num_str = self._poly_to_text(self._num)
        den_str = self._poly_to_text(self._den)
        K = self._gain

        if den_str == "1":
            if abs(K - 1.0) < 1e-6:
                return num_str
            return f"{K:.4g} \u00b7 ({num_str})"

        if abs(K - 1.0) < 1e-6:
            return f"({num_str}) / ({den_str})"
        return f"{K:.4g} \u00b7 ({num_str}) / ({den_str})"

    @staticmethod
    def _poly_to_text(coeffs: np.ndarray) -> str:
        """Convert coefficient array to readable text polynomial."""
        n = len(coeffs) - 1
        if n < 0:
            return "0"
        if n == 0:
            return f"{coeffs[0]:.4g}"

        terms = []
        for i, c in enumerate(coeffs):
            power = n - i
            if abs(c) < 1e-10:
                continue

            if power == 0:
                coeff_str = f"{abs(c):.4g}"
            elif abs(abs(c) - 1.0) < 1e-10:
                coeff_str = ""
            else:
                coeff_str = f"{abs(c):.4g}"

            if power == 0:
                var_str = ""
            elif power == 1:
                var_str = "s"
            else:
                var_str = f"s\u00b2" if power == 2 else f"s^{power}"

            if len(terms) == 0:
                sign = "\u2212" if c < 0 else ""
            else:
                sign = " \u2212 " if c < 0 else " + "

            terms.append(f"{sign}{coeff_str}{var_str}")

        return "".join(terms) if terms else "0"

    @staticmethod
    def _format_complex(z: complex) -> str:
        """Format a complex number for display."""
        if abs(z.imag) < 1e-6:
            return f"{z.real:.3g}"
        elif abs(z.real) < 1e-6:
            return f"{z.imag:.3g}j"
        sign = "+" if z.imag >= 0 else "\u2212"
        return f"{z.real:.3g} {sign} {abs(z.imag):.3g}j"

    # =========================================================================
    # s-Plane axis range
    # =========================================================================

    def _compute_axis_range(self) -> float:
        """Compute dynamic axis range based on poles, zeros, and omega_max."""
        max_r = self.MIN_AXIS_RANGE
        for p in self._poles:
            max_r = max(max_r, abs(p.real) + self.AXIS_PADDING)
            max_r = max(max_r, abs(p.imag) + self.AXIS_PADDING)
        for z in self._zeros:
            max_r = max(max_r, abs(z.real) + self.AXIS_PADDING)
            max_r = max(max_r, abs(z.imag) + self.AXIS_PADDING)
        # Also ensure omega_max fits on the imaginary axis
        omega_max = float(self.parameters.get("omega_max", 8.0))
        max_r = max(max_r, omega_max + 0.5)
        return max_r

    # =========================================================================
    # Plot generation
    # =========================================================================

    def get_plots(self) -> List[Dict[str, Any]]:
        """Generate all Plotly plot dictionaries."""
        if not self._initialized:
            self.initialize()
        return [
            self._create_s_plane_plot(),
            self._create_magnitude_plot(),
            self._create_phase_plot(),
        ]

    def _create_s_plane_plot(self) -> Dict[str, Any]:
        """Create s-plane plot with poles and zeros."""
        traces = []
        axis_range = self._compute_axis_range()

        # jω axis (prominent)
        traces.append({
            "x": [0, 0],
            "y": [-axis_range, axis_range],
            "type": "scatter",
            "mode": "lines",
            "line": {"color": self.JW_AXIS_COLOR, "width": 2.5, "dash": "dash"},
            "name": "j\u03c9 axis",
            "hoverinfo": "skip",
        })

        # σ axis
        traces.append({
            "x": [-axis_range, axis_range],
            "y": [0, 0],
            "type": "scatter",
            "mode": "lines",
            "line": {"color": self.ZEROLINE_COLOR, "width": 1},
            "name": "\u03c3 axis",
            "showlegend": False,
            "hoverinfo": "skip",
        })

        # Zero markers (larger, with text labels)
        for i, z in enumerate(self._zeros):
            label = self._format_complex(z)
            traces.append({
                "x": [float(z.real)],
                "y": [float(z.imag)],
                "type": "scatter",
                "mode": "markers+text",
                "marker": {
                    "symbol": "circle-open",
                    "size": 18,
                    "color": self.ZERO_COLOR,
                    "line": {"width": 3, "color": self.ZERO_COLOR},
                },
                "text": [f"z{i + 1}"],
                "textposition": "top right",
                "textfont": {"color": self.ZERO_COLOR, "size": 11, "family": "Inter, sans-serif"},
                "name": f"Zero: {label}",
                "showlegend": True,
                "hovertemplate": f"Zero {i + 1}<br>s = {label}<extra></extra>",
            })

        # Pole markers (larger, with text labels)
        for i, p in enumerate(self._poles):
            label = self._format_complex(p)
            traces.append({
                "x": [float(p.real)],
                "y": [float(p.imag)],
                "type": "scatter",
                "mode": "markers+text",
                "marker": {
                    "symbol": "x",
                    "size": 18,
                    "color": self.POLE_COLOR,
                    "line": {"width": 3, "color": self.POLE_COLOR},
                },
                "text": [f"p{i + 1}"],
                "textposition": "top right",
                "textfont": {"color": self.POLE_COLOR, "size": 11, "family": "Inter, sans-serif"},
                "name": f"Pole: {label}",
                "showlegend": True,
                "hovertemplate": f"Pole {i + 1}<br>s = {label}<extra></extra>",
            })

        # UI revision fingerprint
        preset = self.parameters["preset"]
        gain = self._gain
        poles_str = ",".join(f"{p.real:.2f}{p.imag:.2f}" for p in self._poles)
        zeros_str = ",".join(f"{z.real:.2f}{z.imag:.2f}" for z in self._zeros)
        ui_fp = f"splane-{preset}-{gain}-{poles_str}-{zeros_str}"

        return {
            "id": "s_plane",
            "title": "s-Plane: Poles & Zeros",
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
                    "font": {"size": 11, "color": "#94a3b8"},
                },
                "margin": {"l": 55, "r": 25, "t": 40, "b": 50},
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)",
                "font": {"family": "Inter, sans-serif", "size": 12, "color": "#f1f5f9"},
                "uirevision": ui_fp,
            },
        }

    def _create_magnitude_plot(self) -> Dict[str, Any]:
        """Create magnitude response |H(jω)| plot."""
        traces = []

        traces.append({
            "x": self._omega.tolist(),
            "y": self._magnitude.tolist(),
            "type": "scatter",
            "mode": "lines",
            "line": {"color": self.MAG_COLOR, "width": 2.5},
            "name": "|H(j\u03c9)|",
            "hovertemplate": "\u03c9 = %{x:.2f}<br>|H| = %{y:.3f}<extra></extra>",
        })

        if self.parameters["show_individual"]:
            for i, mag in enumerate(self._individual_zero_mags):
                traces.append({
                    "x": self._omega.tolist(),
                    "y": mag.tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "line": {"color": self.TEAL_COLOR, "width": 1.5, "dash": "dot"},
                    "name": f"|j\u03c9 \u2212 z{i + 1}|",
                    "opacity": 0.6,
                })
            for i, mag in enumerate(self._individual_pole_mags):
                traces.append({
                    "x": self._omega.tolist(),
                    "y": mag.tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "line": {"color": self.POLE_COLOR, "width": 1.5, "dash": "dot"},
                    "name": f"|j\u03c9 \u2212 p{i + 1}|",
                    "opacity": 0.6,
                })

        preset = self.parameters["preset"]
        gain = self._gain
        poles_str = ",".join(f"{p.real:.2f}" for p in self._poles)
        zeros_str = ",".join(f"{z.real:.2f}" for z in self._zeros)
        ui_fp = f"mag-{preset}-{gain}-{poles_str}-{zeros_str}"

        return {
            "id": "magnitude_response",
            "title": "|H(j\u03c9)| Magnitude Response",
            "data": traces,
            "layout": {
                "xaxis": {
                    "title": "\u03c9 (rad/s)",
                    "showgrid": True,
                    "gridcolor": self.GRID_COLOR,
                    "zeroline": True,
                    "zerolinecolor": self.ZEROLINE_COLOR,
                    "zerolinewidth": 1,
                    "autorange": True,
                    "fixedrange": False,
                    "color": "#f1f5f9",
                },
                "yaxis": {
                    "title": "|H(j\u03c9)|",
                    "showgrid": True,
                    "gridcolor": self.GRID_COLOR,
                    "zeroline": True,
                    "zerolinecolor": self.ZEROLINE_COLOR,
                    "zerolinewidth": 1,
                    "autorange": True,
                    "fixedrange": False,
                    "rangemode": "tozero",
                    "color": "#f1f5f9",
                },
                "legend": {
                    "x": 0.98, "y": 0.98,
                    "xanchor": "right", "yanchor": "top",
                    "bgcolor": self.LEGEND_BG,
                    "bordercolor": self.LEGEND_BORDER,
                    "borderwidth": 1,
                    "font": {"size": 10, "color": "#94a3b8"},
                },
                "margin": {"l": 55, "r": 25, "t": 40, "b": 50},
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)",
                "font": {"family": "Inter, sans-serif", "size": 12, "color": "#f1f5f9"},
                "showlegend": bool(self.parameters["show_individual"]),
                "uirevision": ui_fp,
            },
        }

    def _create_phase_plot(self) -> Dict[str, Any]:
        """Create phase response ∠H(jω) plot."""
        traces = []

        traces.append({
            "x": self._omega.tolist(),
            "y": self._phase.tolist(),
            "type": "scatter",
            "mode": "lines",
            "line": {"color": self.PHASE_COLOR, "width": 2.5},
            "name": "\u2220H(j\u03c9)",
            "hovertemplate": "\u03c9 = %{x:.2f}<br>\u2220H = %{y:.3f} rad<extra></extra>",
        })

        if self.parameters["show_individual"]:
            for i, ph in enumerate(self._individual_zero_phases):
                traces.append({
                    "x": self._omega.tolist(),
                    "y": ph.tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "line": {"color": self.TEAL_COLOR, "width": 1.5, "dash": "dot"},
                    "name": f"\u2220(j\u03c9 \u2212 z{i + 1})",
                    "opacity": 0.6,
                })
            for i, ph in enumerate(self._individual_pole_phases):
                traces.append({
                    "x": self._omega.tolist(),
                    "y": (-ph).tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "line": {"color": self.POLE_COLOR, "width": 1.5, "dash": "dot"},
                    "name": f"\u2212\u2220(j\u03c9 \u2212 p{i + 1})",
                    "opacity": 0.6,
                })

        preset = self.parameters["preset"]
        gain = self._gain
        poles_str = ",".join(f"{p.real:.2f}" for p in self._poles)
        zeros_str = ",".join(f"{z.real:.2f}" for z in self._zeros)
        ui_fp = f"phase-{preset}-{gain}-{poles_str}-{zeros_str}"

        return {
            "id": "phase_response",
            "title": "\u2220H(j\u03c9) Phase Response",
            "data": traces,
            "layout": {
                "xaxis": {
                    "title": "\u03c9 (rad/s)",
                    "showgrid": True,
                    "gridcolor": self.GRID_COLOR,
                    "zeroline": True,
                    "zerolinecolor": self.ZEROLINE_COLOR,
                    "zerolinewidth": 1,
                    "autorange": True,
                    "fixedrange": False,
                    "color": "#f1f5f9",
                },
                "yaxis": {
                    "title": "\u2220H(j\u03c9) [rad]",
                    "showgrid": True,
                    "gridcolor": self.GRID_COLOR,
                    "zeroline": True,
                    "zerolinecolor": self.ZEROLINE_COLOR,
                    "zerolinewidth": 1,
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
                    "font": {"size": 10, "color": "#94a3b8"},
                },
                "margin": {"l": 55, "r": 25, "t": 40, "b": 50},
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)",
                "font": {"family": "Inter, sans-serif", "size": 12, "color": "#f1f5f9"},
                "showlegend": bool(self.parameters["show_individual"]),
                "uirevision": ui_fp,
            },
        }

    # =========================================================================
    # State
    # =========================================================================

    def get_state(self) -> Dict[str, Any]:
        """Return current simulation state with metadata for custom viewer."""
        if not self._initialized:
            self.initialize()

        state = super().get_state()

        state["metadata"] = {
            "simulation_type": "vector_freq_response",
            "sticky_controls": True,
            "hs_expression": self._format_hs_expression(),
            "num_display": self._format_num_display(),
            "den_display": self._format_den_display(),
            "num_coeffs_str": str(self.parameters.get("num_coeffs", "1")),
            "den_coeffs_str": str(self.parameters.get("den_coeffs", "1")),
            "preset_name": self.PRESETS.get(
                self.parameters.get("preset", "custom"), {}
            ).get("name", "Custom"),
            "preset_description": self.PRESETS.get(
                self.parameters.get("preset", "custom"), {}
            ).get("description", ""),
            "poles": [
                {"real": float(p.real), "imag": float(p.imag)}
                for p in self._poles
            ],
            "zeros": [
                {"real": float(z.real), "imag": float(z.imag)}
                for z in self._zeros
            ],
            "gain": float(self._gain),
            "omega": self._omega.tolist(),
            "magnitude": self._magnitude.tolist(),
            "phase": self._phase.tolist(),
            "individual_zero_mags": [m.tolist() for m in self._individual_zero_mags],
            "individual_zero_phases": [p.tolist() for p in self._individual_zero_phases],
            "individual_pole_mags": [m.tolist() for m in self._individual_pole_mags],
            "individual_pole_phases": [p.tolist() for p in self._individual_pole_phases],
            "axis_range": float(self._compute_axis_range()),
            "system_order": len(self._den) - 1,
            "error": self._error,
        }

        return state
