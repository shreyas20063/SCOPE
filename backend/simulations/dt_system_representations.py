"""
DT System Representation Navigator

Interactive concept map showing five equivalent representations of a
discrete-time LTI system:
  1. Block Diagram (Direct Form II)
  2. Difference Equation coefficients
  3. System Functional H(R) — delay-operator polynomial ratio
  4. System Function H(z) — z-transform transfer function
  5. Impulse Response h[n]

Users select a preset or enter custom coefficients. The backend computes
all five representations and returns conversion-step descriptions for the
animated concept map arrows.

Based on MIT 6.003 Lecture 5 (slides 2–12).
"""

import random
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .base_simulator import BaseSimulator


# ── Presets ─────────────────────────────────────────────────────────────────

PRESETS: Dict[str, Dict[str, Any]] = {
    "first_difference": {
        "name": "First Difference",
        "b": [1.0, -1.0],
        "a": [1.0],
        "desc": "FIR highpass: y[n] = x[n] − x[n−1]",
    },
    "accumulator": {
        "name": "Accumulator",
        "b": [1.0],
        "a": [1.0, -1.0],
        "desc": "IIR running sum: y[n] = x[n] + y[n−1]",
    },
    "moving_average_3": {
        "name": "3-Point Moving Average",
        "b": [1/3, 1/3, 1/3],
        "a": [1.0],
        "desc": "FIR smoother: y[n] = ⅓(x[n] + x[n−1] + x[n−2])",
    },
    "leaky_integrator": {
        "name": "Leaky Integrator",
        "b": [0.1],
        "a": [1.0, -0.9],
        "desc": "IIR lowpass: y[n] = 0.1x[n] + 0.9y[n−1]",
    },
    "second_order": {
        "name": "2nd-Order Resonator",
        "b": [1.0],
        "a": [1.0, -1.2, 0.64],
        "desc": "IIR with complex poles: r=0.8, θ≈41°",
    },
    "two_tap_fir": {
        "name": "Two-Tap Echo",
        "b": [1.0, 0.0, 0.5],
        "a": [1.0],
        "desc": "FIR echo: y[n] = x[n] + 0.5x[n−2]",
    },
}


# ── Formatting helpers ──────────────────────────────────────────────────────

def _fmt_coeff(c: float) -> str:
    """Format a coefficient value for display."""
    if c == int(c):
        return str(int(c))
    # Check common fractions
    for denom in (2, 3, 4, 5, 6, 8, 10):
        numer = c * denom
        if abs(numer - round(numer)) < 1e-9:
            n = int(round(numer))
            if abs(n) == 1 and denom == 1:
                return str(n)
            return f"{n}/{denom}"
    return f"{c:.4g}"


def _format_r_polynomial(coeffs: List[float]) -> str:
    """Format coefficient list as R-polynomial: c₀ + c₁R + c₂R² + ..."""
    if not coeffs or all(abs(c) < 1e-12 for c in coeffs):
        return "0"
    terms = []
    first = True
    for i, c in enumerate(coeffs):
        if abs(c) < 1e-12:
            continue
        if first:
            sign = "−" if c < 0 else ""
        else:
            sign = " − " if c < 0 else " + "
        ac = abs(c)
        ac_str = _fmt_coeff(ac)
        if i == 0:
            terms.append(f"{sign}{ac_str}")
        elif i == 1:
            if ac == 1.0:
                terms.append(f"{sign}R")
            else:
                terms.append(f"{sign}{ac_str}R")
        else:
            sup = _superscript(i)
            if ac == 1.0:
                terms.append(f"{sign}R{sup}")
            else:
                terms.append(f"{sign}{ac_str}R{sup}")
        first = False
    return "".join(terms) if terms else "0"


def _format_z_polynomial(coeffs: List[float]) -> str:
    """Format coefficient list as z-polynomial: c₀ + c₁z⁻¹ + c₂z⁻² + ..."""
    if not coeffs or all(abs(c) < 1e-12 for c in coeffs):
        return "0"
    terms = []
    first = True
    for i, c in enumerate(coeffs):
        if abs(c) < 1e-12:
            continue
        if first:
            sign = "−" if c < 0 else ""
        else:
            sign = " − " if c < 0 else " + "
        ac = abs(c)
        ac_str = _fmt_coeff(ac)
        if i == 0:
            terms.append(f"{sign}{ac_str}")
        elif i == 1:
            if ac == 1.0:
                terms.append(f"{sign}z⁻¹")
            else:
                terms.append(f"{sign}{ac_str}z⁻¹")
        else:
            sup = _superscript(-i)
            if ac == 1.0:
                terms.append(f"{sign}z{sup}")
            else:
                terms.append(f"{sign}{ac_str}z{sup}")
        first = False
    return "".join(terms) if terms else "0"


def _superscript(n: int) -> str:
    """Convert integer to Unicode superscript string."""
    sup_map = {
        "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴",
        "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹",
        "-": "⁻",
    }
    return "".join(sup_map.get(ch, ch) for ch in str(n))


def _format_diff_eq(b: List[float], a: List[float]) -> str:
    """Format difference equation: y[n] = Σ bₖ x[n−k] − Σ aₖ y[n−k]."""
    terms = []
    first = True

    # Feedforward terms: bₖ x[n−k]
    for k, bk in enumerate(b):
        if abs(bk) < 1e-12:
            continue
        if first:
            sign = "−" if bk < 0 else ""
        else:
            sign = " − " if bk < 0 else " + "
        ac = abs(bk)
        ac_str = _fmt_coeff(ac)
        x_term = "x[n]" if k == 0 else f"x[n−{k}]"
        if ac == 1.0:
            terms.append(f"{sign}{x_term}")
        else:
            terms.append(f"{sign}{ac_str}·{x_term}")
        first = False

    # Feedback terms: −aₖ y[n−k] for k ≥ 1
    for k in range(1, len(a)):
        ak = a[k]
        if abs(ak) < 1e-12:
            continue
        # The equation is y[n] + a₁y[n-1] + ... = b₀x[n] + ...
        # So y[n] = ... - a₁y[n-1] - ...
        neg_ak = -ak
        if first:
            sign = "−" if neg_ak < 0 else ""
        else:
            sign = " − " if neg_ak < 0 else " + "
        ac = abs(neg_ak)
        ac_str = _fmt_coeff(ac)
        y_term = f"y[n−{k}]"
        if ac == 1.0:
            terms.append(f"{sign}{y_term}")
        else:
            terms.append(f"{sign}{ac_str}·{y_term}")
        first = False

    rhs = "".join(terms) if terms else "0"
    return f"y[n] = {rhs}"


def _compute_impulse_response(b: List[float], a: List[float], n_samples: int) -> np.ndarray:
    """Compute impulse response h[n] by running the difference equation with x[n]=δ[n]."""
    h = np.zeros(n_samples)
    x = np.zeros(n_samples)
    x[0] = 1.0  # δ[n]

    for n in range(n_samples):
        # Feedforward: Σ bₖ x[n−k]
        val = 0.0
        for k, bk in enumerate(b):
            if n - k >= 0:
                val += bk * x[n - k]
        # Feedback: −Σ aₖ y[n−k] for k≥1
        for k in range(1, len(a)):
            if n - k >= 0:
                val -= a[k] * h[n - k]
        h[n] = val

    return h


def _compute_poles_zeros(b: List[float], a: List[float]) -> Tuple[List, List]:
    """Compute poles and zeros of H(z) = B(z)/A(z).

    Since H(z) = b₀ + b₁z⁻¹ + ... / (1 + a₁z⁻¹ + ...),
    multiply top and bottom by z^max(M,N) to get standard polynomial in z.
    """
    poles: List[complex] = []
    zeros: List[complex] = []

    # Zeros: roots of B(z) = b₀z^M + b₁z^(M-1) + ... + bₘ
    if len(b) > 1:
        # Coefficients of z^M, z^(M-1), ..., z^0
        b_poly = list(b)  # already in descending power order for np.roots if reversed
        # np.roots expects [highest power, ..., lowest power]
        # b = [b₀, b₁, ...] corresponds to b₀ + b₁z⁻¹ + ... = z⁻ᴹ(b₀zᴹ + b₁z^(M-1) + ...)
        try:
            z = np.roots(b_poly)
            zeros = [complex(round(r.real, 8), round(r.imag, 8)) for r in z]
        except Exception:
            pass

    # Poles: roots of A(z) = 1 + a₁z⁻¹ + ... = z⁻ᴺ(zᴺ + a₁z^(N-1) + ...)
    if len(a) > 1:
        try:
            p = np.roots(a)
            poles = [complex(round(r.real, 8), round(r.imag, 8)) for r in p]
        except Exception:
            pass

    return poles, zeros


def _build_conversion_steps(b: List[float], a: List[float],
                            diff_eq_text: str,
                            hr_num: str, hr_den: str,
                            hz_num: str, hz_den: str) -> Dict[str, Dict]:
    """Build detailed conversion step descriptions for the concept map arrows."""
    is_fir = len(a) == 1 and abs(a[0] - 1.0) < 1e-12

    # DE → H(R)
    de_to_hr_steps = [
        "Start with the difference equation",
        f"  {_format_diff_eq(b, a)}",
        "Replace each delay: x[n−k] → Rᵏ·X,  y[n−k] → Rᵏ·Y",
        f"  Y = ({hr_num})·X" if is_fir else f"  ({hr_den})·Y = ({hr_num})·X",
        f"  H(R) = Y/X = ({hr_num}) / ({hr_den})",
    ]

    # H(R) → H(z)
    hr_to_hz_steps = [
        f"Start with H(R) = ({hr_num}) / ({hr_den})",
        "The delay operator R is equivalent to z⁻¹",
        "Substitute R → z⁻¹ everywhere:",
        f"  H(z) = ({hz_num}) / ({hz_den})",
    ]

    # H(z) → h[n]
    if is_fir:
        hz_to_hn_steps = [
            f"H(z) = {hz_num}",
            "For FIR systems, h[n] is read directly from the coefficients:",
            f"  h[n] = {{ {', '.join(_fmt_coeff(c) for c in b)} }} (zero for n ≥ {len(b)})",
        ]
    else:
        hz_to_hn_steps = [
            f"H(z) = ({hz_num}) / ({hz_den})",
            "Method 1: Partial fraction expansion + inverse Z-transform",
            "Method 2: Long division of polynomials",
            "Method 3: Recursive computation with x[n] = δ[n]",
        ]

    # DE → h[n]
    de_to_hn_steps = [
        f"Start with: {_format_diff_eq(b, a)}",
        "Set input x[n] = δ[n] (unit impulse)",
        "Compute output y[n] = h[n] step by step:",
        "  n=0: substitute x[0]=1, x[k<0]=0, y[k<0]=0",
        "  n=1: substitute x[1]=0, use computed y[0]",
        "  Continue for each n...",
    ]

    # DE → Block Diagram
    de_to_bd_steps = [
        f"Start with: {_format_diff_eq(b, a)}",
        "Direct Form II realization:",
        f"  Feedforward taps (b): {[_fmt_coeff(c) for c in b]}",
        f"  Feedback taps (a): {[_fmt_coeff(c) for c in a[1:]]}",
        "  Shared delay line with max(M, N−1) delay elements",
        "  Feedback enters before delay, feedforward taps after",
    ]

    return {
        "de_to_hr": {"title": "Diff Eq → H(R)", "subtitle": "R-operator substitution", "steps": de_to_hr_steps},
        "hr_to_hz": {"title": "H(R) → H(z)", "subtitle": "R = z⁻¹", "steps": hr_to_hz_steps},
        "hz_to_hn": {"title": "H(z) → h[n]", "subtitle": "Inverse Z-transform", "steps": hz_to_hn_steps},
        "de_to_hn": {"title": "Diff Eq → h[n]", "subtitle": "Compute with δ[n]", "steps": de_to_hn_steps},
        "de_to_bd": {"title": "Diff Eq → Block Diagram", "subtitle": "Direct Form II", "steps": de_to_bd_steps},
        "bd_to_de": {"title": "Block Diagram → Diff Eq", "subtitle": "Read coefficients",
                     "steps": ["Read feedforward gains → b coefficients",
                               "Read feedback gains → a coefficients",
                               "Write the difference equation from the gains"]},
        "hn_to_hz": {"title": "h[n] → H(z)", "subtitle": "Z-transform",
                     "steps": ["H(z) = Σ h[n] z⁻ⁿ  (sum over all n ≥ 0)",
                               "Substitute each h[n] value and simplify",
                               "Factor if possible to identify poles and zeros"]},
        "hz_to_hr": {"title": "H(z) → H(R)", "subtitle": "z⁻¹ = R",
                     "steps": [f"Start with H(z) = ({hz_num}) / ({hz_den})",
                               "Substitute z⁻¹ → R everywhere:",
                               f"H(R) = ({hr_num}) / ({hr_den})"]},
    }


# ── Simulator ──────────────────────────────────────────────────────────────

class SystemRepresentationSimulator(BaseSimulator):
    """
    DT System Representation Navigator.

    Computes five equivalent representations of a discrete-time LTI system
    and provides conversion path descriptions for an interactive concept map.
    """

    PARAMETER_SCHEMA = {
        "preset": {
            "type": "select",
            "options": list(PRESETS.keys()) + ["custom"],
            "default": "first_difference",
        },
        "b_coefficients": {
            "type": "expression",
            "default": "1, -1",
        },
        "a_coefficients": {
            "type": "expression",
            "default": "1",
        },
        "num_samples": {
            "type": "slider",
            "min": 8,
            "max": 30,
            "default": 15,
            "step": 1,
        },
        "mode": {
            "type": "select",
            "options": ["explore", "challenge"],
            "default": "explore",
        },
    }

    DEFAULT_PARAMS = {
        "preset": "first_difference",
        "b_coefficients": "1, -1",
        "a_coefficients": "1",
        "num_samples": 15,
        "mode": "explore",
    }

    CHALLENGE_REPRESENTATIONS = ["diff_eq", "h_r", "h_z", "impulse_response", "block_diagram"]

    def initialize(self, params: Optional[Dict[str, Any]] = None) -> None:
        self.parameters = {**self.DEFAULT_PARAMS, **(params or {})}
        for name, value in self.parameters.items():
            self.parameters[name] = self._validate_param(name, value)
        self._cached_data: Optional[Dict[str, Any]] = None
        self._challenge_state: Dict[str, Any] = {
            "active": False,
            "source_rep": None,
            "target_rep": None,
            "revealed": False,
            "preset_id": None,
        }
        self._initialized = True

    def reset(self) -> Dict[str, Any]:
        self.parameters = self.DEFAULT_PARAMS.copy()
        self._cached_data = None
        self._challenge_state = {
            "active": False, "source_rep": None,
            "target_rep": None, "revealed": False, "preset_id": None,
        }
        self._initialized = True
        return self.get_state()

    def update_parameter(self, name: str, value: Any) -> Dict[str, Any]:
        old_mode = self.parameters.get("mode", "explore")

        if name in self.parameters:
            self.parameters[name] = self._validate_param(name, value)
        self._cached_data = None

        new_mode = self.parameters.get("mode", "explore")

        # Auto-generate challenge when switching to challenge mode
        if name == "mode" and new_mode == "challenge" and old_mode != "challenge":
            self._generate_challenge()
            self._cached_data = None

        # Clear challenge state when switching back to explore
        if name == "mode" and new_mode == "explore" and old_mode != "explore":
            self._challenge_state = {
                "active": False, "source_rep": None,
                "target_rep": None, "revealed": False, "preset_id": None,
            }

        return self.get_state()

    def handle_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if action == "new_challenge":
            self._generate_challenge()
            self._cached_data = None
        elif action == "reveal_all":
            self._challenge_state["revealed"] = True
        elif action == "init":
            if not self._initialized:
                self.initialize(params)
            else:
                self._cached_data = None
        elif action == "reset":
            return self.reset()
        return self.get_state()

    def _generate_challenge(self) -> None:
        """Generate a random challenge: show one representation, ask for another."""
        preset_ids = list(PRESETS.keys())
        preset_id = random.choice(preset_ids)
        preset = PRESETS[preset_id]

        self.parameters["preset"] = preset_id
        self.parameters["b_coefficients"] = ", ".join(str(c) for c in preset["b"])
        self.parameters["a_coefficients"] = ", ".join(str(c) for c in preset["a"])

        reps = self.CHALLENGE_REPRESENTATIONS.copy()
        source = random.choice(reps)
        reps.remove(source)
        target = random.choice(reps)

        self._challenge_state = {
            "active": True,
            "source_rep": source,
            "target_rep": target,
            "revealed": False,
            "preset_id": preset_id,
        }

    def _get_coefficients(self) -> Tuple[List[float], List[float]]:
        """Parse coefficients from current parameters."""
        preset = self.parameters.get("preset", "first_difference")

        if preset != "custom" and preset in PRESETS:
            p = PRESETS[preset]
            return list(p["b"]), list(p["a"])

        # Custom: parse comma-separated values
        b_str = str(self.parameters.get("b_coefficients", "1"))
        a_str = str(self.parameters.get("a_coefficients", "1"))

        try:
            b = [float(x.strip()) for x in b_str.split(",") if x.strip()]
        except ValueError:
            b = [1.0]
        try:
            a = [float(x.strip()) for x in a_str.split(",") if x.strip()]
        except ValueError:
            a = [1.0]

        if not b:
            b = [1.0]
        if not a:
            a = [1.0]

        # Normalize so a[0] = 1
        if abs(a[0]) > 1e-12 and abs(a[0] - 1.0) > 1e-12:
            a0 = a[0]
            a = [ai / a0 for ai in a]
            b = [bi / a0 for bi in b]
        elif abs(a[0]) < 1e-12:
            a[0] = 1.0

        return b, a

    def _compute(self) -> Dict[str, Any]:
        if self._cached_data is not None:
            return self._cached_data

        b, a = self._get_coefficients()
        num_samples = int(self.parameters.get("num_samples", 15))
        preset = self.parameters.get("preset", "first_difference")

        is_fir = len(a) == 1 and abs(a[0] - 1.0) < 1e-12
        system_order = max(len(b) - 1, len(a) - 1)

        # 1. Difference equation
        diff_eq_text = _format_diff_eq(b, a)

        # Build term lists for frontend
        b_terms = []
        for k, bk in enumerate(b):
            if abs(bk) > 1e-12:
                b_terms.append({"coeff": float(bk), "delay": k,
                                "label": f"{_fmt_coeff(bk)}·x[n−{k}]" if k > 0 else f"{_fmt_coeff(bk)}·x[n]"})
        a_terms = []
        for k in range(1, len(a)):
            if abs(a[k]) > 1e-12:
                a_terms.append({"coeff": float(a[k]), "delay": k,
                                "label": f"{_fmt_coeff(-a[k])}·y[n−{k}]"})

        # 2. H(R)
        hr_num = _format_r_polynomial(b)
        hr_den = _format_r_polynomial(a)
        hr_display = f"H(R) = ({hr_num}) / ({hr_den})" if not is_fir or len(b) > 1 else f"H(R) = {hr_num}"
        if is_fir and len(b) == 1:
            hr_display = f"H(R) = {hr_num}"
        elif hr_den == "1":
            hr_display = f"H(R) = {hr_num}"

        # 3. H(z)
        hz_num = _format_z_polynomial(b)
        hz_den = _format_z_polynomial(a)
        if hz_den == "1":
            hz_display = f"H(z) = {hz_num}"
        else:
            hz_display = f"H(z) = ({hz_num}) / ({hz_den})"

        # 4. Impulse response
        h = _compute_impulse_response(b, a, num_samples)
        n_vals = list(range(num_samples))

        # Simple closed-form description
        if is_fir:
            nonzero = [(k, bk) for k, bk in enumerate(b) if abs(bk) > 1e-12]
            parts = []
            for idx, (k, bk) in enumerate(nonzero):
                term = f"δ[n−{k}]" if k > 0 else "δ[n]"
                abk = abs(bk)
                coeff_str = _fmt_coeff(abk)
                if abk != 1.0:
                    term = f"{coeff_str}·{term}"
                if idx == 0:
                    if bk < 0:
                        term = f"−{term}"
                else:
                    term = f" − {term}" if bk < 0 else f" + {term}"
                parts.append(term)
            closed_form = "".join(parts) if parts else "0"
        elif len(a) == 2:
            pole = -a[1]
            closed_form = f"h[n] = {_fmt_coeff(b[0])}·({_fmt_coeff(pole)})ⁿ·u[n]"
        else:
            closed_form = "h[n] computed recursively"

        # 5. Block diagram info
        block_diagram = {
            "form": "direct_form_2",
            "b_gains": [float(x) for x in b],
            "a_gains": [float(x) for x in a[1:]] if len(a) > 1 else [],
            "delay_count": max(len(b) - 1, len(a) - 1),
        }

        # Poles and zeros
        poles, zeros = _compute_poles_zeros(b, a)
        pole_mags = [abs(p) for p in poles]
        is_stable = all(m < 1.0 - 1e-9 for m in pole_mags) if poles else True
        is_marginally_stable = any(abs(m - 1.0) < 1e-9 for m in pole_mags) and not any(m > 1.0 + 1e-9 for m in pole_mags)

        # Conversion steps
        conversions = _build_conversion_steps(b, a, diff_eq_text, hr_num, hr_den, hz_num, hz_den)

        # Preset name
        preset_name = PRESETS[preset]["name"] if preset in PRESETS else "Custom System"

        self._cached_data = {
            "b": b, "a": a,
            "system_order": system_order,
            "is_fir": is_fir,
            "is_stable": is_stable,
            "is_marginally_stable": is_marginally_stable,
            "poles": [{"real": p.real, "imag": p.imag, "magnitude": abs(p)} for p in poles],
            "zeros": [{"real": z.real, "imag": z.imag, "magnitude": abs(z)} for z in zeros],
            "preset_name": preset_name,

            "diff_eq": {"text": diff_eq_text, "b_terms": b_terms, "a_terms": a_terms},
            "h_r": {"numerator": hr_num, "denominator": hr_den, "display": hr_display},
            "h_z": {"numerator": hz_num, "denominator": hz_den, "display": hz_display},
            "impulse_response": {"n": n_vals, "h": h.tolist(), "closed_form": closed_form},
            "block_diagram": block_diagram,
            "conversions": conversions,

            "n_samples": num_samples,
            "h_array": h,
        }
        return self._cached_data

    def get_plots(self) -> List[Dict[str, Any]]:
        data = self._compute()
        return [
            self._create_impulse_plot(data),
            self._create_pole_zero_plot(data),
        ]

    def get_state(self) -> Dict[str, Any]:
        data = self._compute()
        mode = self.parameters.get("mode", "explore")

        # Build metadata (exclude internal numpy arrays)
        metadata = {
            "simulation_type": "dt_system_representations",
            "b_coeffs": data["b"],
            "a_coeffs": data["a"],
            "system_order": data["system_order"],
            "is_fir": data["is_fir"],
            "is_stable": data["is_stable"],
            "is_marginally_stable": data["is_marginally_stable"],
            "poles": data["poles"],
            "zeros": data["zeros"],
            "preset_name": data["preset_name"],

            "diff_eq": data["diff_eq"],
            "h_r": data["h_r"],
            "h_z": data["h_z"],
            "impulse_response": {"n": data["impulse_response"]["n"],
                                 "h": data["impulse_response"]["h"],
                                 "closed_form": data["impulse_response"]["closed_form"]},
            "block_diagram": data["block_diagram"],
            "conversions": data["conversions"],

            "mode": mode,
            "challenge": self._challenge_state.copy(),
        }

        return {
            "parameters": self.parameters.copy(),
            "plots": [
                self._create_impulse_plot(data),
                self._create_pole_zero_plot(data),
            ],
            "metadata": metadata,
        }

    def _create_impulse_plot(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Stem plot of the impulse response h[n]."""
        plot_id = "impulse_response"
        title = "Impulse Response h[n]"
        h = data["h_array"]
        n = np.arange(len(h))

        traces = []
        # Vertical stems
        for i in range(len(n)):
            traces.append({
                "x": [int(n[i]), int(n[i])],
                "y": [0, float(h[i])],
                "type": "scatter",
                "mode": "lines",
                "line": {"color": "#3b82f6", "width": 2},
                "showlegend": False,
                "hoverinfo": "skip",
            })
        # Markers
        traces.append({
            "x": n.tolist(),
            "y": h.tolist(),
            "type": "scatter",
            "mode": "markers",
            "marker": {"color": "#3b82f6", "size": 9,
                       "line": {"color": "#1e3a5f", "width": 1.5}},
            "name": "h[n]",
            "hovertemplate": "n=%{x}<br>h[n]=%{y:.4g}<extra></extra>",
        })

        # Dynamic y-axis: autorange with padding
        h_abs = np.abs(h)
        h_max = float(max(h_abs.max(), 0.5))
        y_pad = h_max * 0.2
        y_lo = float(min(h.min(), 0)) - y_pad
        y_hi = float(max(h.max(), 0)) + y_pad

        # Fingerprint for uirevision — resets zoom when system changes
        b_str = self.parameters.get("b_coefficients", "")
        a_str = self.parameters.get("a_coefficients", "")
        preset = self.parameters.get("preset", "")
        ui_fingerprint = f"{plot_id}-{preset}-{b_str}-{a_str}"

        layout = {
            "xaxis": {
                "title": "n",
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
                "color": "#f1f5f9",
                "range": [-0.5, len(h) - 0.5],
                "dtick": max(1, len(h) // 15),
            },
            "yaxis": {
                "title": "h[n]",
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
                "color": "#f1f5f9",
                "autorange": True,
                "range": [y_lo, y_hi],
            },
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "font": {"family": "Inter, sans-serif", "size": 12, "color": "#f1f5f9"},
            "margin": {"t": 40, "r": 25, "b": 50, "l": 55},
            "showlegend": False,
            "shapes": [{
                "type": "line",
                "x0": -0.5, "x1": len(h) - 0.5, "y0": 0, "y1": 0,
                "line": {"color": "rgba(148,163,184,0.4)", "width": 1, "dash": "dash"},
            }],
            "datarevision": f"{plot_id}-{time.time()}",
            "uirevision": ui_fingerprint,
        }

        return {"id": plot_id, "title": title, "data": traces, "layout": layout}

    def _create_pole_zero_plot(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Pole-zero plot with unit circle."""
        plot_id = "pole_zero"
        title = "Pole-Zero Map"

        traces = []

        # Unit circle
        theta = np.linspace(0, 2 * np.pi, 100)
        traces.append({
            "x": np.cos(theta).tolist(),
            "y": np.sin(theta).tolist(),
            "type": "scatter",
            "mode": "lines",
            "line": {"color": "rgba(148,163,184,0.3)", "width": 1.5, "dash": "dash"},
            "name": "Unit Circle",
            "hoverinfo": "skip",
        })

        # Zeros (circles)
        if data["zeros"]:
            zr = [z["real"] for z in data["zeros"]]
            zi = [z["imag"] for z in data["zeros"]]
            traces.append({
                "x": zr, "y": zi,
                "type": "scatter",
                "mode": "markers",
                "marker": {"symbol": "circle-open", "size": 12, "color": "#10b981",
                           "line": {"width": 2.5}},
                "name": "Zeros",
                "hovertemplate": "Zero: %{x:.3f} + %{y:.3f}j<extra></extra>",
            })

        # Poles (x marks)
        if data["poles"]:
            pr = [p["real"] for p in data["poles"]]
            pi = [p["imag"] for p in data["poles"]]
            traces.append({
                "x": pr, "y": pi,
                "type": "scatter",
                "mode": "markers",
                "marker": {"symbol": "x", "size": 12, "color": "#ef4444",
                           "line": {"width": 2.5}},
                "name": "Poles",
                "hovertemplate": "Pole: %{x:.3f} + %{y:.3f}j<extra></extra>",
            })

        # Dynamic axis range — always show unit circle + all poles/zeros with padding
        max_range = 1.5  # minimum shows unit circle
        all_reals = []
        all_imags = []
        if data["poles"]:
            all_reals += [p["real"] for p in data["poles"]]
            all_imags += [p["imag"] for p in data["poles"]]
        if data["zeros"]:
            all_reals += [z["real"] for z in data["zeros"]]
            all_imags += [z["imag"] for z in data["zeros"]]
        if all_reals or all_imags:
            extent = max(
                max(abs(v) for v in all_reals) if all_reals else 0,
                max(abs(v) for v in all_imags) if all_imags else 0,
                1.0,
            )
            max_range = extent * 1.4

        # Fingerprint for uirevision — resets zoom when system changes
        b_str = self.parameters.get("b_coefficients", "")
        a_str = self.parameters.get("a_coefficients", "")
        preset = self.parameters.get("preset", "")
        ui_fingerprint = f"{plot_id}-{preset}-{b_str}-{a_str}"

        layout = {
            "xaxis": {
                "title": "Real",
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
                "color": "#f1f5f9",
                "range": [-max_range, max_range],
                "scaleanchor": "y",
                "scaleratio": 1,
                "constrain": "domain",
            },
            "yaxis": {
                "title": "Imaginary",
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
                "color": "#f1f5f9",
                "range": [-max_range, max_range],
                "constrain": "domain",
            },
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "font": {"family": "Inter, sans-serif", "size": 12, "color": "#f1f5f9"},
            "margin": {"t": 40, "r": 25, "b": 50, "l": 55},
            "showlegend": True,
            "legend": {"font": {"color": "#94a3b8", "size": 10},
                       "bgcolor": "rgba(0,0,0,0)"},
            "datarevision": f"{plot_id}-{time.time()}",
            "uirevision": ui_fingerprint,
        }

        return {"id": plot_id, "title": title, "data": traces, "layout": layout}
