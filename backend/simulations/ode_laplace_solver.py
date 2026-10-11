"""
ODE Solver via Laplace Transform — Step-by-Step, with initial conditions

Solves the linear constant-coefficient ODE

    a_n y^(n)(t) + ... + a_1 y'(t) + a_0 y(t) = b_m x^(m)(t) + ... + b_0 x(t)

for a causal input x(t) and initial conditions y(0⁻), y'(0⁻), ...,
y^(n-1)(0⁻), using the UNILATERAL Laplace transform with lower limit 0⁻
(Oppenheim & Willsky, Signals and Systems 2e, §9.9; Lathi, Linear Systems
and Signals, §4.3):

  (a) transform each term. Differentiation property with 0⁻ conditions:
        L{y^(k)} = s^k Y(s) - sum_{j=0}^{k-1} s^(k-1-j) y^(j)(0⁻).
      The input is causal (x(t) = 0 for t < 0), so x^(j)(0⁻) = 0 and
      L{x^(k)} = s^k X(s): the right-hand side has no initial-condition terms.
  (b) A(s)Y(s) - I(s) = B(s)X(s), with the initial-condition polynomial
        I(s) = sum_{k=1}^{n} a_k sum_{j=0}^{k-1} s^(k-1-j) y^(j)(0⁻),
      so  Y(s) = B(s)X(s)/A(s)  +  I(s)/A(s)
                 (zero-state)       (zero-input)
  (c) partial fractions of each part (and of their sum)
  (d) inverse Laplace by table lookup
  (e) y(t) = y_zs(t) + y_zi(t) for t > 0. The value drawn at t = 0 is
      y(0⁺), which differs from y(0⁻) when the input (or an input derivative
      on the right-hand side) contains an impulse.

With every initial condition zero (initial rest) I(s) = 0 and the tool is the
original zero-state solver.

Pole multiplicities come from an exact factorisation of the denominator over
the rationals (user decimals are converted exactly), so repeated poles and
input poles that coincide with system poles are detected without a numerical
tolerance.
"""

import math
from fractions import Fraction
from math import comb, factorial
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import sympy as sp

from .base_simulator import BaseSimulator

_S = sp.Symbol("s")

# Superscript digits for derivative orders / powers.
_SUP_DIGITS = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")
_SUB_DIGITS = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")


def _sup(n: int) -> str:
    """Unicode superscript for an integer (e.g. 4 -> '⁴')."""
    return str(n).translate(_SUP_DIGITS)


class ODELaplaceSolverSimulator(BaseSimulator):
    """Simulator for step-by-step ODE solving via the unilateral Laplace transform."""

    MAX_STEP = 5
    CLAMP_VALUE = 200.0
    NUM_POINTS = 500

    # Initial-condition sliders: y(0⁻), y'(0⁻), y''(0⁻). Exactly the first n
    # (n = ODE order) are used; higher ones are taken as 0 for n > 3.
    IC_PARAMS: Tuple[str, ...] = ("ic_y0", "ic_y1", "ic_y2")

    # ── Presets ───────────────────────────────────────────────────

    PRESETS: Dict[str, Dict[str, Any]] = {
        "first_order_impulse": {
            "label": "Lec 6 Ex 1: ẏ + y = δ(t)",
            "output_coeffs": [1, 1],
            "input_coeffs": [1],
            "input_signal": "delta",
            "description": "First-order system. Solution: e⁻ᵗu(t).",
        },
        "second_order_impulse": {
            "label": "Lec 6 Ex 2: ÿ + 3ẏ + 2y = δ(t)",
            "output_coeffs": [1, 3, 2],
            "input_coeffs": [1],
            "input_signal": "delta",
            "description": "Second-order with real distinct poles at s = −1, −2.",
        },
        "second_order_step": {
            "label": "Step response: ÿ + 3ẏ + 2y = u(t)",
            "output_coeffs": [1, 3, 2],
            "input_coeffs": [1],
            "input_signal": "step",
            "description": "Step response — same system, different input.",
        },
        "underdamped": {
            "label": "Underdamped: ÿ + 2ẏ + 5y = δ(t)",
            "output_coeffs": [1, 2, 5],
            "input_coeffs": [1],
            "input_signal": "delta",
            "description": "Complex conjugate poles at s = −1 ± 2j.",
        },
        "repeated_poles": {
            "label": "Repeated: ÿ + 2ẏ + y = δ(t)",
            "output_coeffs": [1, 2, 1],
            "input_coeffs": [1],
            "input_signal": "delta",
            "description": "Repeated pole at s = −1. Solution involves te⁻ᵗu(t).",
        },
        "third_order": {
            "label": "3rd order: y‴ + 6y″ + 11y′ + 6y = δ(t)",
            "output_coeffs": [1, 6, 11, 6],
            "input_coeffs": [1],
            "input_signal": "delta",
            "description": "Poles at s = −1, −2, −3.",
        },
        "exponential_input": {
            "label": "Exp input: ẏ + 2y = e⁻ᵗu(t)",
            "output_coeffs": [1, 2],
            "input_coeffs": [1],
            "input_signal": "exp",
            "alpha": 1.0,
            "description": "Non-impulse input demonstrates input transform step.",
        },
    }

    PARAMETER_SCHEMA = {
        "preset": {
            "type": "select",
            "options": [
                {"value": "first_order_impulse", "label": "Lec 6 Ex 1: ẏ + y = δ(t)"},
                {"value": "second_order_impulse", "label": "Lec 6 Ex 2: ÿ + 3ẏ + 2y = δ(t)"},
                {"value": "second_order_step", "label": "Step: ÿ + 3ẏ + 2y = u(t)"},
                {"value": "underdamped", "label": "Underdamped: ÿ + 2ẏ + 5y = δ(t)"},
                {"value": "repeated_poles", "label": "Repeated: ÿ + 2ẏ + y = δ(t)"},
                {"value": "third_order", "label": "3rd: y‴ + 6y″ + 11y′ + 6y = δ(t)"},
                {"value": "exponential_input", "label": "Exp: ẏ + 2y = e⁻ᵗu(t)"},
                {"value": "custom", "label": "Custom Coefficients"},
            ],
            "default": "first_order_impulse",
        },
        "output_coeffs": {"type": "expression", "default": "1, 3, 2"},
        "input_coeffs": {"type": "expression", "default": "1"},
        "input_signal": {
            "type": "select",
            "options": [
                {"value": "delta", "label": "δ(t) — Impulse"},
                {"value": "step", "label": "u(t) — Unit Step"},
                {"value": "exp", "label": "e^(−αt)u(t) — Exponential"},
                {"value": "cosine", "label": "cos(ωt)u(t) — Cosine"},
            ],
            "default": "delta",
        },
        "alpha": {"type": "slider", "min": 0.1, "max": 10.0, "step": 0.1, "default": 1.0},
        "omega": {"type": "slider", "min": 0.1, "max": 20.0, "step": 0.1, "default": 2.0},
        "ic_y0": {"type": "slider", "min": -5.0, "max": 5.0, "step": 0.1, "default": 0.0},
        "ic_y1": {"type": "slider", "min": -5.0, "max": 5.0, "step": 0.1, "default": 0.0},
        "ic_y2": {"type": "slider", "min": -5.0, "max": 5.0, "step": 0.1, "default": 0.0},
        "response_view": {
            "type": "select",
            "options": [
                {"value": "total", "label": "Total y(t)"},
                {"value": "decomposition", "label": "Zero-input + zero-state + total"},
            ],
            "default": "total",
        },
        "show_compare": {"type": "checkbox", "default": False},
        "t_max": {"type": "slider", "min": 2.0, "max": 20.0, "step": 0.5, "default": 8.0},
    }

    DEFAULT_PARAMS = {
        "preset": "first_order_impulse",
        "output_coeffs": "1, 3, 2",
        "input_coeffs": "1",
        "input_signal": "delta",
        "alpha": 1.0,
        "omega": 2.0,
        "ic_y0": 0.0,
        "ic_y1": 0.0,
        "ic_y2": 0.0,
        "response_view": "total",
        "show_compare": False,
        "t_max": 8.0,
    }

    HUB_SLOTS = ['control']

    # ── Hub integration ───────────────────────────────────────────

    def to_hub_data(self) -> Optional[Dict[str, Any]]:
        """Export the ODE as a transfer function H(s) = input_coeffs / output_coeffs.

        ``output_coeffs`` are the coefficients of the LHS polynomial
        (acting on y) — these become the TF denominator. ``input_coeffs``
        are the RHS polynomial (acting on u) — the TF numerator. Both
        are stored high-power-first, matching the hub convention.
        Initial conditions do not enter H(s).
        """
        try:
            num = self._parse_coeffs(str(self.parameters.get("input_coeffs", "1")))
            den = self._parse_coeffs(str(self.parameters.get("output_coeffs", "1, 1")))
        except Exception:
            return None
        if not num or not den:
            return None
        return {
            "source": "tf",
            "domain": self.HUB_DOMAIN,
            "dimensions": self.HUB_DIMENSIONS,
            "tf": {
                "num": list(num),
                "den": list(den),
                "variable": "s",
            },
        }

    def from_hub_data(self, hub_data: Dict[str, Any]) -> bool:
        """Inject a hub TF as input_coeffs (numerator) and output_coeffs (denominator)."""
        if not isinstance(hub_data, dict):
            return False
        if hub_data.get("domain", "ct") != self.HUB_DOMAIN:
            return False
        dims = hub_data.get("dimensions") or {}
        if (dims.get("m") or 1) > 1 or (dims.get("p") or 1) > 1:
            return False
        tf = hub_data.get("tf")
        if not tf or not tf.get("num") or not tf.get("den"):
            return False
        self.parameters["input_coeffs"] = ", ".join(str(c) for c in tf["num"])
        self.parameters["output_coeffs"] = ", ".join(str(c) for c in tf["den"])
        return True

    # ── Init ──────────────────────────────────────────────────────

    def __init__(self, simulation_id: str) -> None:
        super().__init__(simulation_id)

        self._current_step: int = 0

        # Polynomial coefficients (descending powers of s)
        self._output_poly: List[float] = []  # A(s) = aₙsⁿ + ... + a₀
        self._input_poly: List[float] = []   # B(s) = bₘsᵐ + ... + b₀
        self._order: int = 1
        self._warnings: List[str] = []

        # Initial conditions at t = 0⁻
        self._ics_all: List[float] = [0.0, 0.0, 0.0]
        self._ics_used: List[float] = []
        self._ics_zero: bool = True
        self._I_poly: List[float] = []       # I(s), descending, length n

        # Input signal transform X(s) = X_num / X_den
        self._X_s_num: List[float] = []
        self._X_s_den: List[float] = []
        self._input_signal_name: str = "δ(t)"

        # Exact (rational) polynomials used for the pole structure
        self._exact: Dict[str, sp.Poly] = {}

        # Combined Y(s) = Y_num / Y_den (normalised to a monic denominator)
        self._Y_num: np.ndarray = np.array([1.0])
        self._Y_den: np.ndarray = np.array([1.0, 1.0])

        # Pole structure and partial fractions
        self._pole_entries: List[Dict[str, Any]] = []
        self._groups_total: List[Dict[str, Any]] = []
        self._groups_zs: List[Dict[str, Any]] = []
        self._groups_zi: List[Dict[str, Any]] = []
        self._residues: np.ndarray = np.array([])
        self._poles: np.ndarray = np.array([])
        self._zeros: np.ndarray = np.array([])
        self._direct_terms: List[float] = []  # polynomial part of Y(s), ASCENDING (impulses)
        self._stability: str = "stable"

        # Values just after t = 0
        self._y0plus: List[float] = [0.0]
        self._y0plus_zs: List[float] = [0.0]

        # Time domain (raw = unclipped; _y_t is the clipped total for plotting)
        self._t: Optional[np.ndarray] = None
        self._y_t: Optional[np.ndarray] = None
        self._y_raw: Optional[np.ndarray] = None
        self._y_zs_raw: Optional[np.ndarray] = None
        self._y_zi_raw: Optional[np.ndarray] = None
        self._y_total_pf_raw: Optional[np.ndarray] = None
        self._x_t: Optional[np.ndarray] = None

        # Solution steps
        self._solution_steps: List[Dict[str, Any]] = []
        self._is_stable: bool = True
        self._ode_text: str = ""

    # ── Lifecycle ─────────────────────────────────────────────────

    def initialize(self, params: Optional[Dict[str, Any]] = None) -> None:
        self.parameters = {**self.DEFAULT_PARAMS, **(params or {})}
        for name, value in self.parameters.items():
            if name in self.PARAMETER_SCHEMA:
                self.parameters[name] = self._validate_param(name, value)
        self._initialized = True
        self._current_step = 0
        self._compute()

    def update_parameter(self, name: str, value: Any) -> Dict[str, Any]:
        if name in self.parameters:
            self.parameters[name] = self._validate_param(name, value)
            # Reset steps when the ODE or its input changes. Initial
            # conditions and the plot view do NOT reset the walkthrough, so a
            # student can drag y(0⁻) while watching the response.
            if name in ("preset", "output_coeffs", "input_coeffs", "input_signal", "alpha", "omega"):
                self._current_step = 0
            self._compute()
        return self.get_state()

    def reset(self) -> Dict[str, Any]:
        self._current_step = 0
        return super().reset()

    def handle_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if action == "next_step":
            self._current_step = min(self._current_step + 1, self.MAX_STEP)
        elif action == "prev_step":
            self._current_step = max(self._current_step - 1, 0)
        elif action == "show_all":
            self._current_step = self.MAX_STEP
        elif action == "reset_steps":
            self._current_step = 0
        return self.get_state()

    # ── Coefficient parsing ───────────────────────────────────────

    def _parse_coeffs(self, expr: str) -> List[float]:
        """Parse comma-separated coefficient string into list of floats (hub export)."""
        try:
            parts = [s.strip() for s in expr.split(",") if s.strip()]
            coeffs = [float(p) for p in parts]
            return coeffs if coeffs else [1.0]
        except (ValueError, TypeError):
            return [1.0]

    @staticmethod
    def _parse_coeff_list(expr: str) -> Optional[List[float]]:
        """Strictly parse "a, b, c" into finite floats; None if unreadable."""
        text = str(expr).replace("−", "-")
        parts = [p.strip() for p in text.split(",") if p.strip()]
        if not parts:
            return None
        try:
            vals = [float(p) for p in parts]
        except (ValueError, TypeError):
            return None
        if not all(math.isfinite(v) for v in vals):
            return None
        return vals

    @staticmethod
    def _strip_leading_zeros(vals: List[float]) -> List[float]:
        """Drop leading zero coefficients ("0, 1, 2" is the first-order s + 2)."""
        out = list(vals)
        while len(out) > 1 and out[0] == 0:
            out.pop(0)
        return out

    def _load_coefficients(self) -> None:
        """Load output/input polynomials from preset or custom input.

        Preset-owned scalar fields (`input_signal`, `alpha`, `omega`) are
        applied only on preset TRANSITION — not on every compute. Without
        this guard, any later user update to one of those fields is silently
        reverted on the next _compute() call: user picks preset=underdamped,
        then tries input_signal=cosine, which would otherwise be overwritten
        back to the preset's default on the very next state fetch. Tracked
        via _last_loaded_preset.

        Custom coefficients: leading zeros are stripped (so the order is the
        true degree of A(s)); an order-0 (algebraic) equation is allowed.
        Unreadable or all-zero output coefficients fall back to ẏ + y with a
        warning, unreadable input coefficients to B(s) = 1.
        """
        preset = self.parameters.get("preset", "first_order_impulse")
        preset_changed = (preset != getattr(self, "_last_loaded_preset", None))

        if preset != "custom" and preset in self.PRESETS:
            p = self.PRESETS[preset]
            # ODE coefficients ARE reloaded every compute — they're derived
            # from the preset, not user-editable while a preset is active.
            self._output_poly = list(p["output_coeffs"])
            self._input_poly = list(p["input_coeffs"])
            # Scalar fields only apply on transition so user overrides stick.
            if preset_changed:
                self.parameters["input_signal"] = p.get("input_signal", "delta")
                if "alpha" in p:
                    self.parameters["alpha"] = p["alpha"]
                if "omega" in p:
                    self.parameters["omega"] = p["omega"]
        else:
            a = self._parse_coeff_list(str(self.parameters.get("output_coeffs", "1, 1")))
            if a is not None:
                a = self._strip_leading_zeros(a)
            if a is None or all(v == 0 for v in a):
                self._warnings.append(
                    "Could not use the output coefficients (need finite numbers, not all zero); "
                    "solving ẏ + y = … instead."
                )
                a = [1.0, 1.0]
            b = self._parse_coeff_list(str(self.parameters.get("input_coeffs", "1")))
            if b is None:
                self._warnings.append(
                    "Could not read the input coefficients; using B(s) = 1."
                )
                b = [1.0]
            b = self._strip_leading_zeros(b)
            self._output_poly = a
            self._input_poly = b

        # Record what preset we just loaded, so the next _load_coefficients
        # call can detect a transition vs. a re-compute of the same preset.
        self._last_loaded_preset = preset
        self._order = len(self._output_poly) - 1

    def _load_initial_conditions(self) -> None:
        """Read y(0⁻), y'(0⁻), y''(0⁻); keep exactly the first n (zeros beyond 3)."""
        vals = []
        for name in self.IC_PARAMS:
            try:
                v = float(self.parameters.get(name, 0.0) or 0.0)
            except (TypeError, ValueError):
                v = 0.0
            vals.append(v if math.isfinite(v) else 0.0)
        n = self._order
        self._ics_all = vals
        self._ics_used = (vals + [0.0] * max(0, n - len(vals)))[:n]
        self._ics_zero = all(v == 0.0 for v in self._ics_used)

        # I(s) = sum_{i=0}^{n-1} c_i s^i,  c_i = sum_{j=0}^{n-1-i} a_{i+j+1} y^(j)(0⁻)
        a_asc = [float(c) for c in self._output_poly[::-1]]
        c_asc = [
            sum(a_asc[i + j + 1] * self._ics_used[j] for j in range(n - i))
            for i in range(n)
        ]
        self._I_poly = c_asc[::-1]

    # ── Input signal transform ────────────────────────────────────

    def _compute_input_transform(self) -> None:
        """Compute X(s) = X_num(s) / X_den(s) for chosen input signal."""
        sig = self.parameters.get("input_signal", "delta")
        alpha = float(self.parameters.get("alpha", 1.0))
        omega = float(self.parameters.get("omega", 2.0))

        if sig == "delta":
            self._X_s_num = [1.0]
            self._X_s_den = [1.0]
            self._input_signal_name = "δ(t)"
        elif sig == "step":
            self._X_s_num = [1.0]
            self._X_s_den = [1.0, 0.0]  # s
            self._input_signal_name = "u(t)"
        elif sig == "exp":
            self._X_s_num = [1.0]
            self._X_s_den = [1.0, alpha]  # s + α
            self._input_signal_name = f"{self._fmt_exp(-alpha)}u(t)"
        elif sig == "cosine":
            self._X_s_num = [1.0, 0.0]  # s
            self._X_s_den = [1.0, 0.0, omega**2]  # s² + ω²
            self._input_signal_name = f"cos({self._omega_t(omega)})u(t)"
        else:
            self._X_s_num = [1.0]
            self._X_s_den = [1.0]
            self._input_signal_name = "δ(t)"

    def _exact_input_transform(self) -> Tuple[sp.Poly, sp.Poly]:
        """X(s) as exact rational polynomials (ω² computed exactly)."""
        sig = self.parameters.get("input_signal", "delta")
        alpha = self._q(float(self.parameters.get("alpha", 1.0)))
        omega = self._q(float(self.parameters.get("omega", 2.0)))
        if sig == "step":
            return sp.Poly([1], _S), sp.Poly([1, 0], _S)
        if sig == "exp":
            return sp.Poly([1], _S), sp.Poly([1, alpha], _S)
        if sig == "cosine":
            return sp.Poly([1, 0], _S), sp.Poly([1, 0, omega**2], _S)
        return sp.Poly([1], _S), sp.Poly([1], _S)

    # ── Core computation ──────────────────────────────────────────

    def _compute(self) -> None:
        """Full computation pipeline."""
        self._warnings = []
        self._load_coefficients()
        self._load_initial_conditions()
        self._compute_input_transform()
        self._form_Y_s()
        self._partial_fraction_decomposition()
        self._compute_initial_values()
        self._assemble_time_domain()
        self._build_ode_text()
        self._build_solution_steps()

    @staticmethod
    def _q(x: Any) -> sp.Rational:
        """Exact rational value of a number (decimals stay exact: 0.1 -> 1/10)."""
        if isinstance(x, (int, np.integer)):
            return sp.Integer(int(x))
        fr = Fraction(repr(float(x)))
        return sp.Rational(fr.numerator, fr.denominator)

    def _poly_q(self, coeffs: Sequence[Any]) -> sp.Poly:
        return sp.Poly([self._q(c) for c in coeffs], _S)

    def _form_Y_s(self) -> None:
        """Form Y(s) = [B(s)X(s) + I(s)] / A(s) and its two parts.

        Over the common denominator D(s) = A(s)·X_den(s):
            Y(s) = [B(s)X_num(s) + I(s)X_den(s)] / D(s).
        """
        A = np.array(self._output_poly, dtype=float)
        B = np.array(self._input_poly, dtype=float)
        X_num = np.array(self._X_s_num, dtype=float)
        X_den = np.array(self._X_s_den, dtype=float)
        I = np.array(self._I_poly, dtype=float) if self._I_poly else np.array([0.0])

        N_zs = np.polymul(B, X_num)
        D = np.polymul(A, X_den)
        N_tot = np.trim_zeros(np.polyadd(N_zs, np.polymul(I, X_den)), "f")
        if len(N_tot) == 0:
            N_tot = np.array([0.0])

        # Normalize by leading coefficient
        self._Y_num = N_tot
        self._Y_den = D
        if abs(D[0]) > 1e-15:
            self._Y_num = N_tot / D[0]
            self._Y_den = D / D[0]

        # Zeros of Y(s) (they move with the initial conditions; poles do not)
        num_trim = np.trim_zeros(np.asarray(self._Y_num, dtype=float), "f")
        self._zeros = np.roots(num_trim) if len(num_trim) > 1 else np.array([])

        # Exact versions
        A_q = self._poly_q(self._output_poly)
        B_q = self._poly_q(self._input_poly)
        I_q = self._poly_q(self._I_poly) if self._I_poly else sp.Poly([0], _S)
        Xn_q, Xd_q = self._exact_input_transform()
        Nzs_q = B_q * Xn_q
        D_q = A_q * Xd_q
        self._exact = {
            "A": A_q, "B": B_q, "I": I_q, "Xn": Xn_q, "Xd": Xd_q,
            "Nzs": Nzs_q, "D": D_q, "Ntot": Nzs_q + I_q * Xd_q,
        }

    # ── Pole structure and partial fractions ──────────────────────

    @staticmethod
    def _multiplicity(f: sp.Poly, P: sp.Poly) -> int:
        """Number of times the irreducible factor f divides P exactly."""
        k = 0
        Q = P
        while not Q.is_zero and Q.degree() >= f.degree():
            quo, rem = Q.div(f)
            if not rem.is_zero:
                break
            Q = quo
            k += 1
        return k

    def _build_pole_entries(self) -> List[Dict[str, Any]]:
        """Distinct poles of D(s) = A(s)X_den(s) with exact multiplicities.

        Each entry: value (complex), mult_D (in A·X_den), mult_A (in A), cancel
        (how many times the factor also divides the total numerator). Order
        matches scipy.signal.residue (first occurrence in np.roots, then by
        magnitude) so step text lists the poles exactly as before.
        """
        D_q = self._exact["D"]
        A_q = self._exact["A"]
        N_q = self._exact["Ntot"]
        I_q = self._exact["I"]
        if D_q.is_zero or D_q.degree() <= 0:
            return []

        entries: List[Dict[str, Any]] = []
        _, factors = D_q.factor_list()
        for f, e in factors:
            if f.degree() <= 0:
                continue
            e_A = self._multiplicity(f, A_q)
            e_N = 0 if N_q.is_zero else min(self._multiplicity(f, N_q), int(e))
            e_I = 0 if (I_q.is_zero or e_A == 0) else min(self._multiplicity(f, I_q), e_A)
            roots = np.atleast_1d(np.roots([float(c) for c in f.all_coeffs()])).astype(complex)
            for r in roots:
                entries.append({
                    "value": complex(r),
                    "mult_D": int(e),
                    "mult_A": int(e_A),
                    "cancel": int(e_N),
                    "cancel_zi": int(e_I),
                })

        # Ordering compatible with scipy.signal.residue
        ref = np.atleast_1d(np.roots(np.asarray(self._Y_den, dtype=float))).astype(complex)
        cap = [en["mult_D"] for en in entries]
        members: List[List[int]] = [[] for _ in entries]
        pairs = sorted(
            (abs(r - en["value"]), i, j)
            for i, r in enumerate(ref)
            for j, en in enumerate(entries)
        )
        taken = set()
        for _, i, j in pairs:
            if i in taken or cap[j] == 0:
                continue
            taken.add(i)
            cap[j] -= 1
            members[j].append(i)
        first = [min(m) if m else len(ref) + j for j, m in enumerate(members)]
        mag = [
            abs(np.mean(ref[sorted(m)])) if m else abs(entries[j]["value"])
            for j, m in enumerate(members)
        ]
        order = sorted(range(len(entries)), key=lambda j: first[j])
        order = sorted(order, key=lambda j: mag[j])
        entries = [entries[j] for j in order]

        # Conjugate partners (for exact conjugate symmetry of residues)
        for i, en in enumerate(entries):
            en["conj"] = None
            v = en["value"]
            if v.imag < 0:
                for j, other in enumerate(entries):
                    w = other["value"]
                    if w.imag > 0 and abs(w - v.conjugate()) <= 1e-9 * max(1.0, abs(v)):
                        en["conj"] = j
                        break
        return entries

    @staticmethod
    def _taylor_poly(coeffs_desc: Sequence[complex], p: complex, m: int) -> List[complex]:
        """First m Taylor coefficients of a polynomial about s = p (repeated synthetic division)."""
        c = list(coeffs_desc)
        out: List[complex] = []
        for _ in range(m):
            if not c:
                out.append(0j)
                continue
            acc = [c[0]]
            for x in c[1:]:
                acc.append(x + acc[-1] * p)
            out.append(acc[-1])
            c = acc[:-1]
        return out

    @staticmethod
    def _series_mul(u: Sequence[complex], v: Sequence[complex], m: int) -> List[complex]:
        w = [0j] * m
        for i in range(min(m, len(u))):
            for j in range(min(m - i, len(v))):
                w[i + j] += u[i] * v[j]
        return w

    def _pfe(self, num_q: sp.Poly, den_q: sp.Poly, mult_key: str) -> Tuple[List[Dict[str, Any]], List[float]]:
        """Partial fractions num/den = Q(s) + sum_p sum_k r_{p,k}/(s-p)^k.

        Residues by the cover-up rule with derivatives: for a pole p of
        multiplicity m, r_{p,k} = [1/(m-k)!] d^{m-k}/ds^{m-k} [(s-p)^m num/den]
        at s = p, computed from Taylor series.

        Returns:
            (groups, direct) — groups [{pole, residues (index k-1 ↔ 1/(s-p)^k),
            multiplicity}] in pole-entry order; direct = polynomial part Q(s)
            coefficients in ASCENDING powers (Q(s) ↔ sum q_k δ^(k)(t)).
        """
        entries = self._pole_entries
        idx = [i for i, en in enumerate(entries) if en[mult_key] > 0]
        if num_q.is_zero:
            return ([{"pole": entries[i]["value"], "residues": [0j] * entries[i][mult_key],
                      "multiplicity": entries[i][mult_key]} for i in idx], [])

        quo, rem = num_q.div(den_q)
        direct = [] if quo.is_zero else [float(c) for c in reversed(quo.all_coeffs())]
        r_desc = [complex(float(c)) for c in rem.all_coeffs()] if not rem.is_zero else [0j]
        lc = float(den_q.LC())

        res_by_entry: Dict[int, List[complex]] = {}
        for i in idx:
            p = entries[i]["value"]
            m = entries[i][mult_key]
            g = self._taylor_poly(r_desc, p, m)
            for j in idx:
                if j == i:
                    continue
                q = entries[j]["value"]
                mq = entries[j][mult_key]
                d = p - q
                ser = [((-1) ** l) * comb(mq + l - 1, l) * d ** (-(mq + l)) for l in range(m)]
                g = self._series_mul(g, ser, m)
            g = [v / lc for v in g]
            res = [g[m - k] for k in range(1, m + 1)]
            if p.imag == 0:
                res = [complex(r.real, 0.0) for r in res]
            res_by_entry[i] = res
        for i in idx:
            c = entries[i].get("conj")
            if c is not None and c in res_by_entry:
                res_by_entry[i] = [r.conjugate() for r in res_by_entry[c]]

        groups = [{"pole": entries[i]["value"], "residues": res_by_entry[i],
                   "multiplicity": entries[i][mult_key]} for i in idx]
        return groups, direct

    def _partial_fraction_decomposition(self) -> None:
        """Partial fractions of Y_zs = BX/A, Y_zi = I/A and the total Y."""
        self._pole_entries = self._build_pole_entries()
        ex = self._exact

        self._groups_zs, _ = self._pfe(ex["Nzs"], ex["D"], "mult_D")
        if ex["I"].is_zero:
            self._groups_zi = []
        else:
            self._groups_zi, _ = self._pfe(ex["I"], ex["A"], "mult_A")
        self._groups_total, self._direct_terms = self._pfe(ex["Ntot"], ex["D"], "mult_D")

        poles: List[complex] = []
        residues: List[complex] = []
        for g in self._groups_total:
            poles.extend([g["pole"]] * g["multiplicity"])
            residues.extend(g["residues"])
        self._poles = np.array(poles, dtype=complex)
        self._residues = np.array(residues, dtype=complex)

        # System stability from the characteristic roots (roots of A(s)),
        # not from the input's poles: stable iff all Re < 0; marginally
        # stable iff the jω-axis roots are simple (Ogata/Nise).
        tol = 1e-10
        char = [en for en in self._pole_entries if en["mult_A"] > 0]
        if any(en["value"].real > tol * max(1.0, abs(en["value"])) for en in char):
            self._stability = "unstable"
        elif any(abs(en["value"].real) <= tol * max(1.0, abs(en["value"])) and en["mult_A"] > 1 for en in char):
            self._stability = "unstable"
        elif any(abs(en["value"].real) <= tol * max(1.0, abs(en["value"])) for en in char):
            self._stability = "marginally_stable"
        else:
            self._stability = "stable"
        self._is_stable = self._stability == "stable"

    # ── Values at t = 0⁺ (generalised initial value theorem) ──────

    @staticmethod
    def _markov_0plus(num_q: sp.Poly, den_q: sp.Poly, count: int) -> List[float]:
        """y^(j)(0⁺), j < count, from the 1/s expansion of the strictly proper part.

        R(s)/D(s) = sum_j h_j / s^(j+1) with h_j = y^(j)(0⁺) (O&W §9.5.10 for
        j = 0): h_j = (r_j - sum_{i=1}^{j} d_i h_{j-i}) / d_0, exact rationals.
        """
        if num_q.is_zero or den_q.degree() <= 0:
            return [0.0] * count
        rem = num_q.rem(den_q)
        d = den_q.all_coeffs()
        N = len(d) - 1
        rc = rem.all_coeffs() if not rem.is_zero else [sp.Integer(0)]
        rc = [sp.Integer(0)] * (N - len(rc)) + list(rc)
        h: List[Any] = []
        for j in range(count):
            rj = rc[j] if j < N else sp.Integer(0)
            acc = rj - sum(d[i] * h[j - i] for i in range(1, min(j, N) + 1))
            h.append(acc / d[0])
        return [float(v) for v in h]

    def _compute_initial_values(self) -> None:
        count = max(self._order, 1)
        ex = self._exact
        self._y0plus = self._markov_0plus(ex["Ntot"], ex["D"], count)
        self._y0plus_zs = self._markov_0plus(ex["Nzs"], ex["D"], count)

    # ── Time domain ───────────────────────────────────────────────

    @staticmethod
    def _eval_groups(groups: Sequence[Dict[str, Any]], t: np.ndarray) -> np.ndarray:
        """Sum of r·t^k/k!·e^{pt} over all partial-fraction terms (t > 0)."""
        y = np.zeros(len(t), dtype=complex)
        for group in groups:
            pole = group["pole"]
            for k, r in enumerate(group["residues"]):
                # L⁻¹{ R / (s-p)^(k+1) } = R · t^k / k! · e^{pt} · u(t)
                y += r * (t ** k / factorial(k)) * np.exp(pole * t)
        return np.real(y)

    def _assemble_time_domain(self) -> None:
        """Build y_zs(t), y_zi(t) and y(t) = y_zs + y_zi on t ∈ [0, t_max]."""
        t_max = float(self.parameters.get("t_max", 8.0))
        t = np.linspace(0, t_max, self.NUM_POINTS)
        self._t = t

        with np.errstate(over="ignore", invalid="ignore"):
            self._y_zs_raw = self._eval_groups(self._groups_zs, t)
            self._y_zi_raw = self._eval_groups(self._groups_zi, t)
            self._y_raw = self._y_zs_raw + self._y_zi_raw
            self._y_total_pf_raw = self._eval_groups(self._groups_total, t)

        self._y_t = self._clip(self._y_raw)
        self._x_t = self._compute_input_signal(t)

    def _clip(self, y: np.ndarray) -> np.ndarray:
        return np.clip(np.nan_to_num(y, nan=0.0, posinf=self.CLAMP_VALUE, neginf=-self.CLAMP_VALUE),
                       -self.CLAMP_VALUE, self.CLAMP_VALUE)

    def _compute_input_signal(self, t: np.ndarray) -> np.ndarray:
        """Compute x(t) for reference plot."""
        sig = self.parameters.get("input_signal", "delta")
        alpha = float(self.parameters.get("alpha", 1.0))
        omega = float(self.parameters.get("omega", 2.0))

        if sig == "delta":
            x = np.zeros_like(t)
            if len(t) > 1:
                dt = t[1] - t[0]
                x[0] = 1.0 / dt  # Visual impulse (area=1)
            return x
        elif sig == "step":
            return np.ones_like(t)
        elif sig == "exp":
            return np.exp(-alpha * t)
        elif sig == "cosine":
            return np.cos(omega * t)
        return np.zeros_like(t)

    # ── ODE text generation ───────────────────────────────────────

    DERIVATIVE_SYMBOLS = ["y(t)", "ẏ(t)", "ÿ(t)", "y‴(t)", "y⁽⁴⁾(t)"]
    X_DERIVATIVE_SYMBOLS = ["x(t)", "ẋ(t)", "ẍ(t)", "x‴(t)", "x⁽⁴⁾(t)"]

    def _deriv_sym(self, power: int) -> str:
        return self.DERIVATIVE_SYMBOLS[power] if power < len(self.DERIVATIVE_SYMBOLS) else f"y⁽{_sup(power)}⁾(t)"

    def _x_deriv_sym(self, power: int) -> str:
        return self.X_DERIVATIVE_SYMBOLS[power] if power < len(self.X_DERIVATIVE_SYMBOLS) else f"x⁽{_sup(power)}⁾(t)"

    def _build_ode_text(self) -> None:
        """Build human-readable ODE string."""
        order = len(self._output_poly) - 1
        terms = []
        for i, coeff in enumerate(self._output_poly):
            power = order - i
            if abs(coeff) < 1e-15:
                continue
            sym = self._deriv_sym(power)
            coeff_str = self._fmt_coeff(coeff, is_first=(len(terms) == 0))
            terms.append(f"{coeff_str}{sym}")

        lhs = " ".join(terms) if terms else "0"

        # RHS: input coefficients × x(t) and derivatives
        input_order = len(self._input_poly) - 1
        rhs_terms = []
        for i, coeff in enumerate(self._input_poly):
            power = input_order - i
            if abs(coeff) < 1e-15:
                continue
            sym = self._x_deriv_sym(power)
            coeff_str = self._fmt_coeff(coeff, is_first=(len(rhs_terms) == 0))
            rhs_terms.append(f"{coeff_str}{sym}")

        rhs = " ".join(rhs_terms) if rhs_terms else "0"
        self._ode_text = f"{lhs} = {rhs}"

    @staticmethod
    def _fmt_coeff(coeff: float, is_first: bool = False) -> str:
        """Format a coefficient for display."""
        if abs(coeff - 1.0) < 1e-10:
            return "" if is_first else "+ "
        if abs(coeff + 1.0) < 1e-10:
            return "−" if is_first else "− "
        if coeff < 0:
            prefix = "−" if is_first else "− "
            val = abs(coeff)
            if abs(val - round(val)) < 1e-10:
                return f"{prefix}{int(round(val))}"
            return f"{prefix}{val:.4g}"
        else:
            prefix = "" if is_first else "+ "
            if abs(coeff - round(coeff)) < 1e-10:
                return f"{prefix}{int(round(coeff))}"
            return f"{prefix}{coeff:.4g}"

    # ── Initial-condition text helpers ────────────────────────────

    @staticmethod
    def _ic_label(j: int, side: str = "-") -> str:
        """y(0⁻), y′(0⁻), y″(0⁻), y‴(0⁻), y⁽⁴⁾(0⁻) … (side '+' gives 0⁺)."""
        base = ["y", "y′", "y″", "y‴"]
        name = base[j] if j < len(base) else f"y⁽{_sup(j)}⁾"
        return f"{name}(0{'⁻' if side == '-' else '⁺'})"

    @staticmethod
    def _ic_tex(j: int, side: str = "-") -> str:
        base = ["y", "y'", "y''", "y'''"]
        name = base[j] if j < len(base) else f"y^{{({j})}}"
        return f"{name}(0^{{{'-' if side == '-' else '+'}}})"

    @staticmethod
    def _fmt_num(x: float) -> str:
        """Plain number with a typographic minus: 3, −1, 0.5, 2.333."""
        x = float(x)
        if abs(x - round(x)) < 1e-9 and abs(x) < 1e9:
            s = str(int(round(x)))
        else:
            s = f"{x:.4g}"
        return s.replace("-", "−")

    def _fmt_signed(self, x: float) -> str:
        s = self._fmt_num(x)
        return s if s.startswith("−") else f"+{s}"

    @staticmethod
    def _s_pow(k: int) -> str:
        if k == 0:
            return ""
        if k == 1:
            return "s"
        return f"s{_sup(k)}"

    @staticmethod
    def _tex_num(x: float) -> str:
        x = float(x)
        if abs(x - round(x)) < 1e-9 and abs(x) < 1e9:
            return str(int(round(x)))
        return f"{x:.4g}"

    def _tex_poly(self, coeffs: Sequence[float], var: str = "s") -> str:
        """LaTeX polynomial from descending coefficients."""
        coeffs = [float(c) for c in coeffs]
        degree = len(coeffs) - 1
        out = ""
        for i, c in enumerate(coeffs):
            power = degree - i
            if abs(c) < 1e-12:
                continue
            mag = abs(c)
            if abs(mag - 1.0) < 1e-10 and power > 0:
                c_str = ""
            else:
                c_str = self._tex_num(mag)
            if power == 0:
                body = c_str if c_str else "1"
            elif power == 1:
                body = f"{c_str}{var}"
            else:
                body = f"{c_str}{var}^{{{power}}}"
            if not out:
                out = ("-" if c < 0 else "") + body
            else:
                out += (" - " if c < 0 else " + ") + body
        return out or "0"

    def _tex_frac(self, num: Sequence[float], den: Sequence[float]) -> str:
        den_t = np.trim_zeros(np.asarray(den, dtype=float), "f")
        num_s = self._tex_poly(num)
        if len(den_t) == 1:
            if abs(den_t[0] - 1.0) < 1e-12:
                return num_s
            return f"\\dfrac{{{num_s}}}{{{self._tex_num(den_t[0])}}}"
        return f"\\dfrac{{{num_s}}}{{{self._tex_poly(den)}}}"

    @staticmethod
    def _paren(expr: str) -> str:
        """Wrap a multi-term expression in parentheses."""
        if " + " in expr or " − " in expr:
            return f"({expr})"
        return expr

    def _ic_pieces(self, i: int) -> List[Tuple[float, int]]:
        """(a_k, j) pairs of the coefficient of s^i in I(s), highest derivative first."""
        n = self._order
        a_asc = [float(c) for c in self._output_poly[::-1]]
        pieces = [(a_asc[i + j + 1], j) for j in range(n - i) if a_asc[i + j + 1] != 0]
        return sorted(pieces, key=lambda pj: -pj[1])

    def _ic_poly_symbolic(self, tex: bool = False) -> str:
        """I(s) in terms of the symbols y(0⁻), y′(0⁻), … with the numeric a_k."""
        n = self._order
        parts: List[str] = []
        for i in range(n - 1, -1, -1):
            pieces = self._ic_pieces(i)
            if not pieces:
                continue
            inner = ""
            for a, j in pieces:
                label = self._ic_tex(j) if tex else self._ic_label(j)
                mag = abs(a)
                coef = "" if abs(mag - 1.0) < 1e-12 else (self._tex_num(mag) if tex else self._fmt_num(mag))
                if not inner:
                    inner = ("-" if tex else "−") * (a < 0) + coef + label
                else:
                    inner += (" - " if tex else " − ") if a < 0 else " + "
                    inner += coef + label
            if len(pieces) > 1:
                group = f"\\left[{inner}\\right]" if tex else f"[{inner}]"
            else:
                group = inner
            if i == 0:
                term = group
            elif tex:
                term = f"{group}\\,s" if i == 1 else f"{group}\\,s^{{{i}}}"
            else:
                term = f"{group}·{self._s_pow(i)}"
            parts.append(term)
        if not parts:
            return "0"
        out = parts[0]
        for p in parts[1:]:
            if p.startswith("−") or p.startswith("-"):
                out += (" - " if tex else " − ") + p[1:]
            else:
                out += " + " + p
        return out

    def _ic_poly_numeric(self) -> str:
        if not self._I_poly or all(abs(c) < 1e-15 for c in self._I_poly):
            return "0"
        return self._format_poly(self._I_poly, "s")

    def _ic_poly_numeric_tex(self) -> str:
        if not self._I_poly or all(abs(c) < 1e-15 for c in self._I_poly):
            return "0"
        return self._tex_poly(self._I_poly)

    def _deriv_bracket(self, k: int, tex: bool = False) -> str:
        """s^k Y(s) − s^(k−1) y(0⁻) − … − y^(k−1)(0⁻) (without the brackets)."""
        if tex:
            head = "Y(s)" if k == 0 else ("sY(s)" if k == 1 else f"s^{{{k}}}Y(s)")
        else:
            head = f"{self._s_pow(k)}Y(s)"
        parts = [head]
        for j in range(k):
            power = k - 1 - j
            if tex:
                lab = self._ic_tex(j)
                parts.append(lab if power == 0 else (f"s\\,{lab}" if power == 1 else f"s^{{{power}}}\\,{lab}"))
            else:
                lab = self._ic_label(j)
                parts.append(lab if power == 0 else f"{self._s_pow(power)}·{lab}")
        return (" - " if tex else " − ").join(parts)

    def _transformed_lhs(self, tex: bool = False) -> str:
        """Σ a_k [s^k Y − …] with the IC terms written out (unicode or LaTeX)."""
        n = self._order
        out = ""
        for i, a in enumerate(self._output_poly):
            k = n - i
            a = float(a)
            if abs(a) < 1e-15:
                continue
            mag = abs(a)
            coef = "" if abs(mag - 1.0) < 1e-10 else (self._tex_num(mag) if tex else self._fmt_num(mag))
            if k == 0:
                body = f"{coef}Y(s)"
            elif tex:
                body = f"{coef}\\left[{self._deriv_bracket(k, tex=True)}\\right]"
            else:
                body = f"{coef}[{self._deriv_bracket(k)}]"
            if not out:
                out = ("-" if tex else "−") * (a < 0) + body
            else:
                out += ((" - " if tex else " − ") if a < 0 else " + ") + body
        return out or "0"

    def _rhs_display(self) -> str:
        """B(s)X(s) as one fraction, e.g. 1, 1/s, (s + 1)/(s + 4)."""
        num = np.polymul(np.array(self._input_poly, float), np.array(self._X_s_num, float))
        den = np.array(self._X_s_den, float)
        num_s = self._format_poly(num, "s")
        if len(den) == 1 or num_s == "0":
            return num_s
        return f"{self._paren(num_s)}/{self._paren(self._format_poly(den, 's'))}"

    def _impulse_terms(self, coeffs_asc: Sequence[float]) -> List[str]:
        """['1·δ(t)', '−2·δ′(t)'] for the polynomial part Q(s) = Σ q_k s^k."""
        names = ["δ(t)", "δ′(t)", "δ″(t)", "δ‴(t)"]
        out = []
        for k, q in enumerate(coeffs_asc):
            if abs(q) < 1e-12:
                continue
            nm = names[k] if k < len(names) else f"δ⁽{_sup(k)}⁾(t)"
            out.append(self._coef_times(q, nm))
        return out

    def _impulse_text(self) -> Optional[str]:
        terms = self._impulse_terms(self._direct_terms)
        if not terms:
            return None
        joined = self._signed_join(terms)
        return (f"Y(s) is improper, so y(t) also contains {joined} at t = 0 "
                f"(not drawn on the plot).")

    def _ic_usage_note(self) -> Optional[str]:
        n = self._order
        custom = self.parameters.get("preset") == "custom" or self.parameters.get("preset") not in self.PRESETS
        if n == 0:
            return "Order 0 (algebraic equation): no initial conditions are used."
        if not custom:
            return None
        if n == 1:
            return "Order 1: only y(0⁻) is used; the y′(0⁻) and y″(0⁻) sliders are ignored."
        if n == 2:
            return "Order 2: y(0⁻) and y′(0⁻) are used; the y″(0⁻) slider is ignored."
        if n == 3:
            return "Order 3: y(0⁻), y′(0⁻) and y″(0⁻) are all used."
        extra = " = ".join(self._ic_label(j) for j in range(3, n))
        return f"Order {n}: only three sliders, so {extra} = 0 is assumed."

    def _ic_sentence(self) -> str:
        n = self._order
        if n == 0:
            return "No derivatives of y appear, so there are no initial conditions."
        if self._ics_zero:
            return "All initial conditions are zero (system at rest)."
        vals = ", ".join(f"{self._ic_label(j)} = {self._fmt_num(v)}" for j, v in enumerate(self._ics_used))
        return f"Initial conditions at t = 0⁻: {vals}."

    def _initial_values(self) -> List[Dict[str, Any]]:
        out = []
        for j in range(self._order):
            minus = float(self._ics_used[j])
            plus = float(self._y0plus[j]) if j < len(self._y0plus) else minus
            jump = plus - minus
            if abs(jump) < 1e-10 * max(1.0, abs(plus)):
                jump = 0.0
            out.append({
                "j": j,
                "minus_label": self._ic_label(j, "-"),
                "plus_label": self._ic_label(j, "+"),
                "minus_tex": self._ic_tex(j, "-"),
                "plus_tex": self._ic_tex(j, "+"),
                "minus": minus,
                "plus": plus,
                "jump": jump,
            })
        return out

    def _jump_text(self, values: List[Dict[str, Any]]) -> str:
        n = self._order
        if n == 0:
            return "Order 0: y(t) follows the input instantly; there are no initial conditions to carry."
        jumps = [v for v in values if v["jump"] != 0.0]
        if not jumps:
            if n == 1:
                return "No jump: y is continuous at t = 0, so y(0⁺) = y(0⁻)."
            if n <= 4:
                names = [self._ic_label(j).replace("(0⁻)", "") for j in range(n)]
                listed = ", ".join(names[:-1]) + " and " + names[-1]
                return (f"No jump: {listed} are continuous at t = 0 (no impulse acts on them), "
                        f"so their 0⁺ values equal the given 0⁻ values.")
            return (f"No jump: y and its first {n - 1} derivatives are continuous at t = 0, "
                    f"so y⁽ʲ⁾(0⁺) = y⁽ʲ⁾(0⁻) for j < {n}.")
        sig = self.parameters.get("input_signal", "delta")
        has_deriv = len(self._input_poly) > 1
        if sig == "delta" and not has_deriv:
            cause = "the impulse δ(t) in the input"
        elif sig == "delta":
            cause = "δ(t) and its derivatives on the right-hand side"
        else:
            cause = ("the input derivatives on the right-hand side (the derivative of the "
                     "jump of x(t) at t = 0 is an impulse)")
        items = "; ".join(
            f"{v['minus_label']} = {self._fmt_num(v['minus'])} → {v['plus_label']} = "
            f"{self._fmt_num(v['plus'])} (jump {self._fmt_signed(v['jump'])})"
            for v in jumps
        )
        return f"Jump at t = 0 caused by {cause}: {items}."

    def _ivt_texts(self) -> Tuple[str, str]:
        y0 = self._fmt_num(self._y0plus[0])
        y0_tex = self._tex_num(self._y0plus[0])
        if self._direct_terms:
            q_desc = list(reversed(self._direct_terms))
            q = self._format_poly(q_desc, "s")
            text = (f"Y(s) is improper: Y(s) = Q(s) + Y_sp(s) with Q(s) = {q} (impulses at t = 0). "
                    f"The initial value theorem applies to the strictly proper part: "
                    f"y(0⁺) = lim(s→∞) s·Y_sp(s) = {y0}.")
            tex = f"y(0^{{+}}) = \\lim_{{s\\to\\infty}} s\\,Y_{{sp}}(s) = {y0_tex}"
        else:
            text = f"Initial value theorem: y(0⁺) = lim(s→∞) s·Y(s) = {y0} (this is y(0⁺), not y(0⁻))."
            tex = f"y(0^{{+}}) = \\lim_{{s\\to\\infty}} s\\,Y(s) = {y0_tex}"
        return text, tex

    EXPLANATION = (
        "The initial conditions are values at t = 0⁻, just before the input acts. "
        "An impulse in the input (or in the input derivatives on the right-hand side) "
        "can make y or its derivatives jump at t = 0, so y(0⁺) can differ from y(0⁻). "
        "The plot shows y(t) for t > 0; the initial value theorem, lim(s→∞) sY(s), "
        "gives y(0⁺), not y(0⁻)."
    )

    CAUSAL_NOTE = (
        "The input is causal (x(t) = 0 for t < 0), so x(0⁻) = x′(0⁻) = … = 0: "
        "the right-hand side has no initial-condition terms (ℒ{x⁽ᵏ⁾} = sᵏX(s))."
    )

    def _cancellations(self, key: str = "cancel") -> List[Dict[str, Any]]:
        """Poles cancelled exactly by zeros: of the total Y(s) (key 'cancel') or
        of the zero-input part I(s)/A(s) (key 'cancel_zi').

        A pole of multiplicity m contributes t⁰…t^(m−1) times its mode; if a zero
        cancels c of its m factors, only the t^(m−c)…t^(m−1) terms disappear
        (all of them when c = m).
        """
        mult_key = "mult_D" if key == "cancel" else "mult_A"
        out = []
        seen = set()
        for en in self._pole_entries:
            c = en[key]
            if c <= 0:
                continue
            p = en["value"]
            pair = (round(p.real, 8), round(abs(p.imag), 8))
            if pair in seen:
                continue
            seen.add(pair)
            if abs(p.imag) < 1e-10:
                body = self._fmt_exp(float(p.real))  # '' for s = 0 (constant mode)
                mode = f"the mode {body}" if body else "the constant mode"
                where = self._fmt_complex(p)
            else:
                sigma, wd = p.real, abs(p.imag)
                env = self._fmt_exp(float(sigma))
                trig = f"cos/sin({self._omega_t(wd)})"
                body = f"{env}·{trig}" if env else trig
                mode = f"the mode {body}"
                where = f"{self._fmt_complex(complex(sigma, wd))} and its conjugate"
            m = en[mult_key]
            if c >= m:
                if key == "cancel":
                    text = f"s = {where}: a zero of Y(s) cancels this pole, so {mode} is absent from y(t)."
                else:
                    text = (f"s = {where}: I(s) shares this root with A(s), so these initial conditions "
                            f"do not excite {mode} — it is absent from y_zi(t).")
            else:
                gone = []
                for k in range(m - c, m):
                    tk = "t" if k == 1 else f"t{_sup(k)}"
                    gone.append(f"{tk}·{body}" if body else tk)
                gone_txt = " and ".join(gone) + (" terms" if len(gone) > 1 else " term")
                left = m - c
                kept = f"{mode} remains" if left == 1 else f"{mode} remains up to the t{_sup(left - 1) if left > 2 else ''} term"
                if key == "cancel":
                    text = (f"s = {where}: a zero of Y(s) cancels {c} of the {m} repeated factors of this pole, "
                            f"so y(t) has no {gone_txt} ({kept}).")
                else:
                    text = (f"s = {where}: I(s) shares {c} of the {m} repeated factors of this root with A(s), "
                            f"so y_zi(t) has no {gone_txt} ({kept}).")
            out.append({"pole": {"real": float(p.real), "imag": float(p.imag)}, "text": text})
        return out

    # ── Solution step builders ────────────────────────────────────

    def _build_solution_steps(self) -> None:
        """Build the 6-step solution walkthrough."""
        self._solution_steps = [
            self._step_0_ode(),
            self._step_1_take_laplace(),
            self._step_2_solve_for_Y(),
            self._step_3_partial_fractions(),
            self._step_4_inverse_laplace(),
            self._step_5_final_solution(),
        ]

    def _step_0_ode(self) -> Dict[str, Any]:
        """Step 0: Display the original ODE and its initial conditions."""
        order = self._order
        sig = self._input_signal_name
        if order == 0:
            head = f"An algebraic (order-0) equation with input x(t) = {sig}. "
        else:
            head = (f"A {self._ordinal(order)}-order linear constant-coefficient ODE "
                    f"with input x(t) = {sig}. ")
        note = self._ic_usage_note()
        return {
            "step": 0,
            "title": "Original Differential Equation",
            "equation": self._ode_text,
            "description": head + self._ic_sentence() + (f" {note}" if note and order != 0 else ""),
            "details": {
                "order": order,
                "input_signal": sig,
                "ics": [{"label": self._ic_label(j), "value": v} for j, v in enumerate(self._ics_used)],
                "ic_note": note,
            },
        }

    def _step_1_take_laplace(self) -> Dict[str, Any]:
        """Step 1: Unilateral Laplace transform of each term (0⁻ initial conditions)."""
        order = self._order
        term_transforms = []
        for i, coeff in enumerate(self._output_poly):
            power = order - i
            if abs(coeff) < 1e-15:
                continue
            deriv_sym = self._deriv_sym(power)
            coeff_display = self._fmt_coeff_simple(coeff)
            bracket = self._deriv_bracket(power)
            transform = f"{coeff_display}[{bracket}]" if power > 0 else f"{coeff_display}Y(s)"
            term_transforms.append({
                "original": f"{coeff_display}{deriv_sym}",
                "transform": transform,
                "property": f"ℒ{{{deriv_sym}}} = {bracket}",
            })
        input_order = len(self._input_poly) - 1
        rhs_properties = []
        for i, coeff in enumerate(self._input_poly):
            power = input_order - i
            if abs(coeff) < 1e-15 or power == 0:
                continue
            rhs_properties.append(
                f"ℒ{{{self._x_deriv_sym(power)}}} = {self._s_pow(power)}X(s)  (causal input: no initial terms)"
            )

        x_transform = self._describe_input_transform()
        rhs = self._rhs_display()
        lhs = self._transformed_lhs()

        if order == 0:
            prop = "No derivatives of y, so there are no initial-condition terms."
        else:
            prop = ("Unilateral Laplace transform (lower limit 0⁻). Differentiation property: "
                    "ℒ{y⁽ᵏ⁾(t)} = sᵏY(s) − Σⱼ s^(k−1−j)·y⁽ʲ⁾(0⁻), j = 0 … k−1.")
        tex = []
        if order > 0:
            tex.append({"label": "Differentiation property (0⁻ initial conditions)",
                        "tex": r"\mathcal{L}\{y^{(k)}(t)\} = s^{k}Y(s) - \sum_{j=0}^{k-1} s^{k-1-j}\,y^{(j)}(0^{-})"})
        tex.append({"label": "This ODE, transformed",
                    "tex": f"{self._transformed_lhs(tex=True)} = "
                           f"{self._tex_frac(np.polymul(self._input_poly, self._X_s_num), self._X_s_den)}"})
        lines = [{"label": "Input", "text": f"X(s) = ℒ{{{self._input_signal_name}}} = {x_transform['X_s_display']}"}]
        if len(self._input_poly) > 1 or abs(float(self._input_poly[0]) - 1.0) > 1e-12:
            lines.append({"label": "Right side", "text": f"B(s)X(s) = {x_transform['B_X_display']} = {rhs}"})
        lines.append({"label": "Causal input", "text": self.CAUSAL_NOTE})

        return {
            "step": 1,
            "title": "Take Laplace Transform",
            "equation": f"{lhs} = {rhs}",
            "description": f"{prop} {self.CAUSAL_NOTE} Input: ℒ{{{self._input_signal_name}}} = {x_transform['X_s_display']}.",
            "details": {
                "term_transforms": term_transforms,
                "rhs_properties": rhs_properties,
                "input_transform": x_transform,
                "factored_form": f"({self._format_poly(self._output_poly, 's')})Y(s) − I(s) = {x_transform['B_X_display']}",
                "causal_note": self.CAUSAL_NOTE,
                "tex": tex,
                "lines": lines,
            },
        }

    def _step_2_solve_for_Y(self) -> Dict[str, Any]:
        """Step 2: A(s)Y(s) − I(s) = B(s)X(s); solve for Y(s) = Y_zs + Y_zi."""
        num_str = self._format_poly(self._Y_num, "s")
        den_str = self._format_poly(self._Y_den, "s")
        factored_den = self._factored_form(self._Y_den)
        # A product of several factors is bracketed so '/' clearly divides by all of them
        n_factors = len(self._factor_list(self._Y_den)) if len(self._Y_den) > 1 else 1
        factored_disp = f"[{factored_den}]" if n_factors > 1 or "·" in factored_den else factored_den
        poles_desc = self._describe_poles()

        A_str = self._format_poly(self._output_poly, "s")
        B_str = self._format_poly(self._input_poly, "s")
        X_str = self._describe_input_transform()["X_s_display"]
        I_sym = self._ic_poly_symbolic()
        I_num = self._ic_poly_numeric()
        Nzs = np.polymul(np.array(self._input_poly, float), np.array(self._X_s_num, float))
        Dzs = np.polymul(np.array(self._output_poly, float), np.array(self._X_s_den, float))
        Yzs_str = f"{self._paren(self._format_poly(Nzs, 's'))} / {self._paren(self._format_poly(Dzs, 's'))}"
        Yzi_str = "0" if I_num == "0" else f"{self._paren(I_num)} / {self._paren(A_str)}"

        lines = [
            {"label": "Polynomials", "text": f"A(s) = {A_str},  B(s) = {B_str},  X(s) = {X_str}"},
            {"label": "Initial-condition polynomial",
             "text": f"I(s) = {I_sym} = {I_num}" if I_sym != I_num else f"I(s) = {I_num}"},
            {"label": "Zero-state part", "text": f"Y_zs(s) = B(s)X(s)/A(s) = {Yzs_str}"},
            {"label": "Zero-input part", "text": f"Y_zi(s) = I(s)/A(s) = {Yzi_str}"},
        ]
        for c in self._cancellations("cancel_zi"):
            lines.append({"label": "Zero-input modes", "text": c["text"]})
        for c in self._cancellations():
            lines.append({"label": "Pole-zero cancellation", "text": c["text"]})
        tex = [
            {"label": "Collect terms", "tex": r"A(s)Y(s) - I(s) = B(s)X(s)"},
            {"label": "Initial-condition polynomial",
             "tex": f"I(s) = {self._ic_poly_symbolic(tex=True)} = {self._ic_poly_numeric_tex()}"
             if self._order > 0 else r"I(s) = 0"},
            {"label": "Zero-state + zero-input",
             "tex": r"Y(s) = \underbrace{\frac{B(s)X(s)}{A(s)}}_{\text{zero-state}} + "
                    r"\underbrace{\frac{I(s)}{A(s)}}_{\text{zero-input}} = "
                    f"{self._tex_frac(Nzs, Dzs)} + "
                    f"{self._tex_frac(self._I_poly if self._I_poly else [0.0], self._output_poly) if I_num != '0' else '0'}"},
        ]
        if self._ics_zero:
            split = "I(s) = 0 (initial rest), so Y(s) = B(s)X(s)/A(s) is the zero-state response."
        else:
            split = "Y(s) = Y_zs(s) + Y_zi(s): zero-state B(s)X(s)/A(s) plus zero-input I(s)/A(s)."
        return {
            "step": 2,
            "title": "Solve for Y(s)",
            "equation": f"Y(s) = {self._paren(num_str)} / {self._paren(den_str)}",
            "description": (f"A(s)Y(s) − I(s) = B(s)X(s) ⇒ Y(s) = [B(s)X(s) + I(s)] / A(s). {split} "
                            f"Factored: Y(s) = {self._paren(num_str)} / {factored_disp}. {poles_desc}"),
            "details": {
                "numerator": num_str,
                "denominator": den_str,
                "factored_denominator": factored_den,
                "poles": [
                    {"real": float(p.real), "imag": float(p.imag)}
                    for p in self._poles
                ],
                "I_symbolic": I_sym,
                "I_numeric": I_num,
                "Y_zs": Yzs_str,
                "Y_zi": Yzi_str,
                "lines": lines,
                "tex": tex,
                "key_insight": (
                    "The Laplace transform converted the differential equation "
                    "into a simple algebraic equation — no need for homogeneous "
                    "and particular solutions!"
                ),
            },
        }

    def _pfe_terms(self, groups: Sequence[Dict[str, Any]]) -> Tuple[List[str], List[Dict[str, Any]]]:
        """Partial-fraction term strings, e.g. '4 / (s + 1)', '−2 / (s + 2)²',
        '(−0.1−0.2j) / (s − 2j)' (signed; join with _signed_join)."""
        terms = []
        algebra_steps = []
        for group in groups:
            p = group["pole"]
            for k_idx, r in enumerate(group["residues"]):
                power = k_idx + 1  # index 0 → (s-p)^1, index 1 → (s-p)^2
                if abs(r) < 1e-10:
                    continue
                r_str = self._res_str(r)
                p_factor = self._fmt_pole_factor(p)
                if power == 1:
                    term_str = f"{r_str} / {p_factor}"
                else:
                    term_str = f"{r_str} / {p_factor}{_sup(power)}"
                terms.append(term_str)
                algebra_steps.append({
                    "residue": self._fmt_complex(r),
                    "pole": self._fmt_complex(p),
                    "power": power,
                    "explanation": (
                        f"R = {self._fmt_complex(r)} at pole s = {self._fmt_complex(p)}"
                        + (f" (order {power})" if power > 1 else "")
                    ),
                })
        return terms, algebra_steps

    def _pfe_string(self, groups: Sequence[Dict[str, Any]], direct_asc: Sequence[float]) -> str:
        terms, _ = self._pfe_terms(groups)
        if direct_asc and any(abs(q) > 1e-12 for q in direct_asc):
            q_str = self._format_poly(list(reversed(list(direct_asc))), "s")
            terms = terms + [self._paren(q_str)]
        return self._signed_join(terms) or "0"

    def _step_3_partial_fractions(self) -> Dict[str, Any]:
        """Step 3: Partial fraction decomposition (each part and the total)."""
        terms, algebra_steps = self._pfe_terms(self._groups_total)
        pfe_str = self._pfe_string(self._groups_total, self._direct_terms)
        lines = [
            {"label": "Zero-state", "text": f"Y_zs(s) = {self._pfe_string(self._groups_zs, self._direct_terms)}"},
            {"label": "Zero-input", "text": f"Y_zi(s) = {self._pfe_string(self._groups_zi, [])}"},
        ]
        q_terms = self._impulse_terms(self._direct_terms)
        if q_terms:
            q_desc = self._format_poly(list(reversed(self._direct_terms)), "s")
            lines.append({"label": "Polynomial part",
                          "text": f"Q(s) = {q_desc} ↔ {self._signed_join(q_terms)} (impulses at t = 0)"})
        if not self._pole_entries:
            desc = "Y(s) has no poles: it is a polynomial (impulses only)."
        else:
            desc = f"Decomposed into {len(terms)} partial fraction term(s)."
            if not self._ics_zero:
                desc += (" Each part is expanded on its own; adding the two expansions "
                         "gives the expansion of Y(s).")
        return {
            "step": 3,
            "title": "Partial Fraction Decomposition",
            "equation": f"Y(s) = {pfe_str}",
            "description": desc,
            "details": {
                "algebra_steps": algebra_steps,
                "pfe_terms": terms,
                "lines": lines,
            },
        }

    def _exp_string(self, p: complex) -> str:
        """e^{pt} for a table entry; complex exponents are parenthesised: e^((−1+2j)t)."""
        if abs(p.imag) < 1e-10:
            return self._fmt_exp(float(np.real(p)))
        if abs(p.real) < 1e-10:
            return f"e^({self._fmt_complex(p)}t)"
        return f"e^(({self._fmt_complex(p)})t)"

    def _time_terms(self, groups: Sequence[Dict[str, Any]]) -> Tuple[List[str], List[Dict[str, Any]]]:
        pairs = []
        time_terms = []
        for group in groups:
            p = group["pole"]
            for k, r in enumerate(group["residues"]):
                if abs(r) < 1e-10:
                    continue
                r_str = self._res_str(r)
                p_factor = self._fmt_pole_factor(p)
                exp_str = self._exp_string(p)
                power = k + 1  # index k → (s-p)^{-(k+1)}
                # R/(s−p)^(k+1) ↔ R·tᵏ/k!·eᵖᵗ·u(t)
                body = "·".join(x for x in (self._t_power(k), exp_str, "u(t)") if x)
                t_form = self._res_times(r, body)

                if power == 1 and abs(p.imag) < 1e-10:
                    s_form = f"{r_str} / {p_factor}"
                    table_entry = "ℒ⁻¹{R/(s+a)} = R·e⁻ᵃᵗ·u(t)"
                elif power == 1:
                    s_form = f"{r_str} / {p_factor}"
                    table_entry = "ℒ⁻¹{R/(s−p)} = R·eᵖᵗ·u(t) (combine conjugates → real)"
                else:
                    sup = _sup(power)
                    s_form = f"{r_str} / {p_factor}{sup}"
                    table_entry = f"ℒ⁻¹{{R/(s+a){sup}}} = R·tᵏ/k!·e⁻ᵃᵗ·u(t)"

                pairs.append({"s_domain": s_form, "time_domain": t_form, "table_entry": table_entry})
                time_terms.append(t_form)
        return time_terms, pairs

    def _step_4_inverse_laplace(self) -> Dict[str, Any]:
        """Step 4: Inverse Laplace transform via table lookup."""
        time_terms, pairs = self._time_terms(self._groups_total)
        impulse_terms = self._impulse_terms(self._direct_terms)
        all_terms = impulse_terms + time_terms
        lines = [
            {"label": "Zero-state", "text": f"y_zs(t) = {self._real_form_inner(self._groups_zs, self._direct_terms)}"},
            {"label": "Zero-input", "text": f"y_zi(t) = {self._real_form_inner(self._groups_zi, [])}"},
        ]
        return {
            "step": 4,
            "title": "Inverse Laplace Transform (Table Lookup)",
            "equation": "y(t) = " + (self._signed_join(all_terms) or "0"),
            "description": ("Each partial fraction term maps to a known Laplace transform pair. "
                            "The unilateral inverse determines y(t) for t > 0."),
            "details": {
                "pairs": pairs,
                "lines": lines,
                "table_reference": [
                    {"s_form": "R/(s+a)", "t_form": "R·e⁻ᵃᵗ·u(t)", "condition": "Re(s) > −a"},
                    {"s_form": "R/(s+a)²", "t_form": "R·t·e⁻ᵃᵗ·u(t)", "condition": "Repeated pole"},
                    {"s_form": "ω/((s+σ)²+ω²)", "t_form": "e^(−σt)·sin(ωt)·u(t)", "condition": "Complex poles"},
                ],
            },
        }

    def _stability_text(self) -> str:
        """System stability (from the roots of A(s)) plus what this particular y(t) does.

        The behaviour of y(t) is read from the poles that survive in the reduced
        Y(s): a pole of multiplicity mult_D in A(s)X_den(s) of which ``cancel``
        factors are cancelled by zeros of the numerator is left with
        multiplicity mult_D − cancel (0 = mode absent; on the jω axis, 1 =
        bounded term, ≥ 2 = t·e^{pt} growth).
        """
        if self._order == 0:
            return "Order 0: A(s) is a constant, so there are no characteristic roots (no natural modes)."
        tol = 1e-10
        entries = self._pole_entries
        y_zero = self._exact["Ntot"].is_zero  # Y(s) ≡ 0: every pole is gone

        def on_axis(en: Dict[str, Any]) -> bool:
            return abs(en["value"].real) <= tol * max(1.0, abs(en["value"]))

        def in_rhp(en: Dict[str, Any]) -> bool:
            return en["value"].real > tol * max(1.0, abs(en["value"]))

        def left(en: Dict[str, Any]) -> int:
            return 0 if y_zero else en["mult_D"] - en["cancel"]

        # The input's own poles on the jω axis (step: s = 0; cosine: ±jω)
        axis_input = [en for en in entries if on_axis(en) and en["mult_D"] > en["mult_A"]]
        input_only = [en for en in axis_input if en["mult_A"] == 0]
        coincident = [en for en in axis_input if en["mult_A"] > 0]
        grows = [en for en in entries
                 if (in_rhp(en) and left(en) >= 1) or (on_axis(en) and left(en) >= 2)]
        axis_left = [en for en in entries if on_axis(en) and left(en) >= 1]

        if self._stability == "stable":
            text = ("All characteristic roots (roots of A(s)) have Re(s) < 0 → stable system: "
                    "the natural modes, including the whole zero-input response, decay.")
            if any(left(en) >= 1 for en in input_only):
                text += (" The input's pole(s) on the jω axis leave a steady-state term "
                         "that does not decay.")
            elif input_only:
                text += (" The input's pole(s) on the jω axis are cancelled by zero(s) of "
                         "H(s) = B(s)/A(s), so they leave no steady-state term: y(t) → 0.")
            elif entries:
                text += " Every pole of Y(s) has Re(s) < 0, so y(t) → 0."
            return text

        if self._stability == "marginally_stable":
            text = ("Simple characteristic root(s) on the jω axis → marginally stable: "
                    "those modes neither grow nor decay.")
            if grows:
                text += (" The input has a pole on that same root, so y(t) grows "
                         "(resonance: t·e^{pt} terms).")
            elif coincident:
                text += (" The input has a pole on that same root, but a zero of Y(s) cancels "
                         "one factor of the repeated pole: there is no t·e^{pt} term, so "
                         "y(t) stays bounded (no resonance).")
            if any(left(en) >= 1 for en in input_only):
                text += " The input's own pole(s) on the jω axis add a term that does not decay."
            if y_zero:
                text += " Here Y(s) = 0 exactly, so y(t) = 0 for t > 0."
            elif not axis_left:
                text += (" Here zeros of Y(s) cancel every pole on the jω axis, so these modes "
                         "are absent and y(t) → 0.")
            return text

        n_bad = sum(
            en["mult_A"] for en in entries
            if en["mult_A"] > 0 and (in_rhp(en) or (on_axis(en) and en["mult_A"] > 1))
        )
        text = (f"UNSTABLE: {n_bad} characteristic root(s) of A(s) with Re(s) > 0 or repeated on "
                f"the jω axis → those modes grow without bound.")
        if not grows:
            if y_zero:
                text += (" Here Y(s) = 0 exactly, so this y(t) is 0 for t > 0 and does not grow; "
                         "a slightly different input or initial condition would excite the "
                         "growing mode(s).")
            else:
                text += (" Here zeros of Y(s) cancel every growing mode, so this y(t) does not "
                         "grow; a slightly different input or initial condition would excite them.")
        return text

    def _step_5_final_solution(self) -> Dict[str, Any]:
        """Step 5: Final combined solution, 0⁻ → 0⁺ values, stability."""
        terms = self._real_form_terms(self._groups_total, [])
        inner = self._signed_join(terms) or "0"
        impulse_terms = self._impulse_terms(self._direct_terms)
        impulse_prefix = self._signed_join(impulse_terms)

        if self._ics_zero:
            if not terms:
                wrapped = ""
            elif len(terms) == 1:
                wrapped = f"{inner}·u(t)"
            else:
                wrapped = f"({inner})·u(t)"
            expression = self._signed_join(impulse_terms + [wrapped]) or "0"
            equation = f"y(t) = {expression}"
        else:
            expression = f"{inner},  t > 0"
            equation = f"y(t) = {expression}"
            if impulse_prefix:
                equation += f"  (plus {impulse_prefix} at t = 0)"

        values = self._initial_values()
        ivt_text, ivt_tex = self._ivt_texts()
        lines = [
            {"label": "Zero-input", "text": f"y_zi(t) = {self._real_form_inner(self._groups_zi, [])}"},
            {"label": "Zero-state", "text": f"y_zs(t) = {self._real_form_inner(self._groups_zs, self._direct_terms)}"},
        ]
        for v in values:
            jump = "" if v["jump"] == 0.0 else f"  (jump {self._fmt_signed(v['jump'])})"
            lines.append({
                "label": "Initial value" if v["j"] == 0 else None,
                "text": f"{v['minus_label']} = {self._fmt_num(v['minus'])} → "
                        f"{v['plus_label']} = {self._fmt_num(v['plus'])}{jump}",
            })
        lines.append({"label": "Initial value theorem", "text": ivt_text})
        imp = self._impulse_text()
        if imp:
            lines.append({"label": "Impulses", "text": imp})

        description = self._stability_text()
        if not self._ics_zero:
            description += (" Initial conditions entered through I(s) using their 0⁻ values "
                            "directly — y(0⁺) never had to be found first.")
        return {
            "step": 5,
            "title": "Final Solution y(t)",
            "equation": equation,
            "description": description,
            "details": {
                "expression": expression,
                "expression_zs": self._real_form_inner(self._groups_zs, self._direct_terms),
                "expression_zi": self._real_form_inner(self._groups_zi, []),
                "is_stable": self._is_stable,
                "stability": self._stability,
                "initial_values": values,
                "lines": lines,
                "tex": [{"label": "Initial value theorem", "tex": ivt_tex}],
                "key_insight": (
                    "The complete solution was obtained entirely through "
                    "algebraic manipulation in the s-domain — no need to "
                    "split into homogeneous and particular solutions!"
                ),
            },
        }

    def _real_form_inner(self, groups: Sequence[Dict[str, Any]], direct_asc: Sequence[float]) -> str:
        """Readable real-form sum for t > 0 (conjugate pairs combined), e.g.
        'e⁻ᵗ − e^(−2t)', '0.5·e⁻ᵗ·sin(2t)', '0.25·t·sin(2t)'.

        Impulse terms (polynomial part) are prefixed when ``direct_asc`` is given.
        """
        return self._signed_join(self._real_form_terms(groups, direct_asc)) or "0"

    def _real_form_terms(self, groups: Sequence[Dict[str, Any]], direct_asc: Sequence[float]) -> List[str]:
        """Signed terms of _real_form_inner (join with _signed_join).

        R/(s−p)^(k+1) ↔ R·tᵏ/k!·eᵖᵗ; a conjugate pair σ ± jω_d with residues
        R, R̄ gives 2Re(R·tᵏ/k!·e^{(σ+jω_d)t}) = tᵏ/k!·e^{σt}(A cos ω_d t + B sin ω_d t)
        with A = 2Re R, B = −2Im R (R taken at the upper-half-plane pole).
        """
        terms: List[str] = []
        used_conjugates = set()

        for group in groups:
            p = group["pole"]
            for k, r in enumerate(group["residues"]):
                # Skip if this is the conjugate of an already-processed complex pole
                conj_key = (round(p.real, 8), round(-p.imag, 8), k)
                if conj_key in used_conjugates:
                    continue
                t_pow = self._t_power(k)

                if abs(p.imag) > 1e-10:
                    used_conjugates.add((round(p.real, 8), round(p.imag, 8), k))
                    pu, ru = (p, r) if p.imag > 0 else (p.conjugate(), r.conjugate())
                    A = 2 * ru.real
                    B = -2 * ru.imag
                    wt = self._omega_t(pu.imag)
                    parts = [(c, trig) for c, trig in ((A, f"cos({wt})"), (B, f"sin({wt})")) if abs(c) > 1e-10]
                    if not parts:
                        continue
                    prefix = "·".join(x for x in (t_pow, self._fmt_exp(float(pu.real))) if x)
                    if len(parts) == 1:
                        c, trig = parts[0]
                        terms.append(self._coef_times(c, f"{prefix}·{trig}" if prefix else trig))
                    elif prefix:
                        inner = self._signed_join([self._coef_times(c, trig) for c, trig in parts])
                        terms.append(f"{prefix}·({inner})")
                    else:
                        terms.extend(self._coef_times(c, trig) for c, trig in parts)
                else:
                    r_val = float(np.real(r))
                    if abs(r_val) < 1e-10:
                        continue
                    body = "·".join(x for x in (t_pow, self._fmt_exp(float(np.real(p)))) if x)
                    terms.append(self._coef_times(r_val, body))

        impulses = self._impulse_terms(direct_asc) if direct_asc else []
        return impulses + terms

    # ── Classical method comparison ───────────────────────────────

    def _compute_classical_solution(self) -> Optional[Dict[str, Any]]:
        """Build classical method description for comparison."""
        if not bool(self.parameters.get("show_compare", False)):
            return None

        order = self._order
        char = [en for en in self._pole_entries if en["mult_A"] > 0]

        # Characteristic equation
        char_eq = self._format_poly(self._output_poly, "s") + " = 0"

        def sub(n: int) -> str:
            return str(n).translate(_SUB_DIGITS)

        roots_desc = []
        i = 0
        for en in char:
            p = en["value"]
            for _ in range(en["mult_A"]):
                roots_desc.append(f"s{sub(i + 1)} = {self._fmt_complex(p)}")
                i += 1

        # Homogeneous solution form: a root of multiplicity m gives t⁰ … t^(m−1)
        # terms, each with its own constant C₁, C₂, … (n constants in all)
        homo_terms = []
        n_const = 0
        for en in char:
            p = en["value"]
            mult = en["mult_A"]
            env = self._fmt_exp(float(p.real))
            if abs(p.imag) < 1e-10:
                for m in range(mult):
                    n_const += 1
                    t_pow = "" if m == 0 else ("t" if m == 1 else f"t{_sup(m)}")
                    body = "·".join(x for x in (t_pow, env) if x)
                    homo_terms.append(f"C{sub(n_const)}·{body}" if body else f"C{sub(n_const)}")
            elif p.imag > 0:
                wt = self._omega_t(p.imag)
                for m in range(mult):
                    c1, c2 = n_const + 1, n_const + 2
                    n_const += 2
                    t_pow = "" if m == 0 else ("t" if m == 1 else f"t{_sup(m)}")
                    prefix = "·".join(x for x in (t_pow, env) if x)
                    trig = f"C{sub(c1)}·cos({wt}) + C{sub(c2)}·sin({wt})"
                    homo_terms.append(f"{prefix}·({trig})" if prefix else trig)

        # Particular solution description
        sig = self.parameters.get("input_signal", "delta")
        if sig == "delta":
            particular = "For δ(t) input: particular solution is 0 for t > 0"
        elif sig == "step":
            particular = "For u(t) input: guess yₚ = constant, substitute to find value"
        elif sig == "exp":
            particular = "For exponential input: guess yₚ = Ae^(−αt), solve for A"
        else:
            particular = "For sinusoidal input: guess yₚ = Acos(ωt) + Bsin(ωt)"
        # Modification rule: a guess that duplicates a homogeneous mode must be
        # multiplied by t^m, m = multiplicity of that characteristic root.
        if sig != "delta":
            dup = [en for en in char if en["mult_D"] > en["mult_A"]]
            if dup:
                m = max(en["mult_A"] for en in dup)
                where = self._fmt_complex(dup[0]["value"])
                if abs(dup[0]["value"].imag) > 1e-10:
                    where = f"±{self._fmt_complex(complex(0.0, abs(dup[0]['value'].imag)))}"
                t_m = "t" if m == 1 else f"t{_sup(m)}"
                particular += (f". Here s = {where} is also a characteristic root (multiplicity {m}): "
                               f"that guess duplicates a homogeneous mode, so multiply it by {t_m}")

        values = self._initial_values()
        if order == 0:
            ic_note = "Order 0: no constants to fit."
        else:
            plus = ", ".join(f"{v['plus_label']} = {self._fmt_num(v['plus'])}" for v in values)
            minus = ", ".join(f"{v['minus_label']} = {self._fmt_num(v['minus'])}" for v in values)
            ic_note = (f"Fit the {order} constant(s) of yₕ + yₚ to the values just after the input acts: "
                       f"{plus}. The Laplace method used the 0⁻ values ({minus}) directly.")
            if any(v["jump"] != 0.0 for v in values):
                ic_note += " They differ here because of the jump at t = 0."

        return {
            "characteristic_eq": char_eq,
            "roots": roots_desc,
            "homogeneous_form": " + ".join(homo_terms) if homo_terms else "0",
            "particular_form": particular,
            "initial_conditions_note": ic_note,
            "summary": (
                "Order 0: there is no characteristic equation; y(t) follows directly from the input."
                if order == 0 else
                f"Classical method, 6 steps: "
                f"(1) characteristic equation, (2) find its {order} root(s), "
                f"(3) form y_h with {order} unknown constant(s), "
                f"(4) guess the particular-solution form, "
                f"(5) substitute yₚ into the ODE to find its coefficients, "
                f"(6) fit the {order} constant(s) to the initial conditions at t = 0⁺. "
                f"Laplace method: 4 algebraic steps, no guessing!"
            ),
        }

    # ── Plot generation ───────────────────────────────────────────

    def get_plots(self) -> List[Dict[str, Any]]:
        if self._t is None:
            self._compute()

        plots = [self._make_input_plot()]

        if self._current_step >= 2:
            plots.append(self._make_pole_zero_plot())
        if self._current_step >= 4:
            plots.append(self._make_time_response_plot())

        return plots

    def _base_layout(self) -> Dict[str, Any]:
        return {
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "font": {"family": "Inter, sans-serif", "size": 12, "color": "#f1f5f9"},
            "margin": {"t": 45, "r": 25, "b": 55, "l": 60},
            "showlegend": True,
            "legend": {"font": {"color": "#94a3b8", "size": 11}},
        }

    def _make_input_plot(self) -> Dict[str, Any]:
        """Plot the input signal x(t)."""
        if self._t is None or self._x_t is None:
            return {"id": "input_signal", "title": "Input Signal x(t)", "data": [], "layout": {}}

        sig = self.parameters.get("input_signal", "delta")
        layout = {
            **self._base_layout(),
            "xaxis": {
                "title": "t (seconds)",
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
                "color": "#f1f5f9",
            },
            "yaxis": {
                "title": "x(t)",
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
                "color": "#f1f5f9",
                "autorange": True,
            },
        }

        fingerprint = f"input-{sig}-{self.parameters.get('alpha',1)}-{self.parameters.get('omega',2)}"
        layout["uirevision"] = fingerprint

        if sig == "delta":
            # Impulse as vertical arrow at t=0
            data = [
                {
                    "x": [0, 0],
                    "y": [0, 1],
                    "type": "scatter",
                    "mode": "lines+markers",
                    "line": {"color": "#10b981", "width": 3},
                    "marker": {"symbol": "triangle-up", "size": 12, "color": "#10b981"},
                    "name": "δ(t)",
                    "hovertemplate": "δ(t) at t=0<extra></extra>",
                },
            ]
            layout["yaxis"]["range"] = [-0.1, 1.5]
            layout["annotations"] = [{
                "x": 0, "y": 1.2, "text": "δ(t)",
                "showarrow": False, "font": {"color": "#10b981", "size": 14},
            }]
        else:
            data = [
                {
                    "x": self._t.tolist(),
                    "y": self._x_t.tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "line": {"color": "#10b981", "width": 2},
                    "name": f"x(t) = {self._input_signal_name}",
                },
            ]

        return {
            "id": "input_signal",
            "title": f"Input Signal: x(t) = {self._input_signal_name}",
            "data": data,
            "layout": layout,
        }

    def _make_pole_zero_plot(self) -> Dict[str, Any]:
        """Plot the s-plane pole-zero map of Y(s)."""
        traces: List[Dict[str, Any]] = []

        # jω axis (imaginary axis)
        all_pts = list(self._poles) + list(self._zeros)
        max_r = max((max(abs(p.real), abs(p.imag)) for p in all_pts), default=1.0) * 1.5
        max_r = max(max_r, 2.0)

        traces.append({
            "x": [0, 0],
            "y": [-max_r, max_r],
            "type": "scatter",
            "mode": "lines",
            "line": {"color": "rgba(168,85,247,0.4)", "width": 1.5, "dash": "dash"},
            "name": "jω axis",
            "hoverinfo": "skip",
        })

        # Real axis
        traces.append({
            "x": [-max_r, max_r],
            "y": [0, 0],
            "type": "scatter",
            "mode": "lines",
            "line": {"color": "rgba(148,163,184,0.3)", "width": 1, "dash": "dash"},
            "name": "Real axis",
            "hoverinfo": "skip",
            "showlegend": False,
        })

        # Stability region shading (left half-plane)
        traces.append({
            "x": [-max_r, 0, 0, -max_r],
            "y": [-max_r, -max_r, max_r, max_r],
            "type": "scatter",
            "fill": "toself",
            "fillcolor": "rgba(16,185,129,0.05)",
            "line": {"width": 0},
            "name": "Stable region (Re < 0)",
            "hoverinfo": "skip",
            "showlegend": False,
        })

        # Poles (× markers)
        if len(self._poles) > 0:
            traces.append({
                "x": [float(p.real) for p in self._poles],
                "y": [float(p.imag) for p in self._poles],
                "type": "scatter",
                "mode": "markers+text",
                "marker": {
                    "symbol": "x",
                    "size": 14,
                    "color": "#ef4444",
                    "line": {"width": 3, "color": "#ef4444"},
                },
                "text": [f"p{i+1}" for i in range(len(self._poles))],
                "textposition": "top right",
                "textfont": {"size": 10, "color": "#ef4444"},
                "name": "Poles",
                "hovertemplate": "Pole: %{x:.4f} + %{y:.4f}j<extra></extra>",
            })

        # Zeros (○ markers) — roots of B(s)X_num(s) + I(s)X_den(s): they move
        # with the initial conditions.
        if len(self._zeros) > 0:
            traces.append({
                "x": [float(z.real) for z in self._zeros],
                "y": [float(z.imag) for z in self._zeros],
                "type": "scatter",
                "mode": "markers",
                "marker": {
                    "symbol": "circle-open",
                    "size": 14,
                    "color": "#3b82f6",
                    "line": {"width": 3},
                },
                "name": "Zeros",
                "hovertemplate": "Zero: %{x:.4f} + %{y:.4f}j<extra></extra>",
            })

        # Exact pole-zero cancellations (e.g. an IC vector that excites one mode)
        cancelled_en = [en for en in self._pole_entries if en["cancel"] > 0]
        cancelled = [en["value"] for en in cancelled_en]
        if cancelled:
            hover = []
            for en in cancelled_en:
                z = f"{en['value'].real:.4f} + {en['value'].imag:.4f}j"
                if en["cancel"] >= en["mult_D"]:
                    hover.append(f"Cancelled pole {z}: mode absent from y(t)")
                else:
                    hover.append(f"Pole {z}: {en['cancel']} of its {en['mult_D']} factors cancelled "
                                 f"(multiplicity {en['mult_D'] - en['cancel']} left in Y(s))")
            traces.append({
                "x": [float(p.real) for p in cancelled],
                "y": [float(p.imag) for p in cancelled],
                "text": hover,
                "type": "scatter",
                "mode": "markers",
                "marker": {
                    "symbol": "circle-open",
                    "size": 26,
                    "color": "#f59e0b",
                    "line": {"width": 2, "color": "#f59e0b"},
                },
                "name": "Pole-zero cancellation",
                "hovertemplate": "%{text}<extra></extra>",
            })

        fingerprint = f"pz-{'-'.join(f'{p.real:.4f}{p.imag:.4f}' for p in self._poles)}"
        layout = {
            **self._base_layout(),
            "xaxis": {
                "title": "Re{s}",
                "range": [-max_r, max_r],
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
                "color": "#f1f5f9",
                "scaleanchor": "y",
                "scaleratio": 1,
                "constrain": "domain",
            },
            "yaxis": {
                "title": "Im{s}",
                "range": [-max_r, max_r],
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
                "color": "#f1f5f9",
                "constrain": "domain",
            },
            "uirevision": fingerprint,
        }

        return {
            "id": "pole_zero_splane",
            "title": "Pole-Zero Map (s-plane)",
            "data": traces,
            "layout": layout,
        }

    def _make_time_response_plot(self) -> Dict[str, Any]:
        """Plot y(t) for t > 0 (total, or zero-input + zero-state + total)."""
        if self._t is None or self._y_t is None:
            return {"id": "time_response", "title": "y(t)", "data": [], "layout": {}}

        t_list = self._t.tolist()
        view = self.parameters.get("response_view", "total")
        traces: List[Dict[str, Any]] = []

        if view == "decomposition":
            traces.append({
                "x": t_list,
                "y": self._clip(self._y_zi_raw).tolist(),
                "type": "scatter",
                "mode": "lines",
                "line": {"color": "#f59e0b", "width": 2, "dash": "dash"},
                "name": "y<sub>zi</sub>(t) zero-input",
            })
            traces.append({
                "x": t_list,
                "y": self._clip(self._y_zs_raw).tolist(),
                "type": "scatter",
                "mode": "lines",
                "line": {"color": "#14b8a6", "width": 2, "dash": "dash"},
                "name": "y<sub>zs</sub>(t) zero-state",
            })
            traces.append({
                "x": t_list,
                "y": self._y_t.tolist(),
                "type": "scatter",
                "mode": "lines",
                "line": {"color": "#3b82f6", "width": 2.5},
                "name": "y(t) = y<sub>zi</sub> + y<sub>zs</sub>",
            })
        else:
            traces.append({
                "x": t_list,
                "y": self._y_t.tolist(),
                "type": "scatter",
                "mode": "lines",
                "line": {"color": "#3b82f6", "width": 2.5},
                "name": "y(t)",
            })

            # At step 5, also show individual component terms
            if self._current_step >= 5:
                component_colors = ["#14b8a6", "#ef4444", "#f59e0b", "#a855f7", "#ec4899"]
                ci = 0
                used_conjugates = set()

                for group in self._groups_total:
                    p = group["pole"]
                    resids = group["residues"]

                    for k, r in enumerate(resids):
                        conj_key = (round(p.real, 8), round(-p.imag, 8), k)
                        if conj_key in used_conjugates:
                            continue
                        if abs(r) < 1e-10:
                            continue

                        with np.errstate(over="ignore", invalid="ignore"):
                            if abs(p.imag) > 1e-10:
                                used_conjugates.add((round(p.real, 8), round(p.imag, 8), k))
                                # Real part of complex conjugate pair
                                term = 2 * np.real(
                                    r * (self._t ** k / factorial(k)) * np.exp(p * self._t)
                                )
                            else:
                                term = np.real(
                                    r * (self._t ** k / factorial(k)) * np.exp(p * self._t)
                                )

                        term_clipped = self._clip(term)
                        p_str = self._fmt_complex(p)
                        traces.append({
                            "x": t_list,
                            "y": term_clipped.tolist(),
                            "type": "scatter",
                            "mode": "lines",
                            "line": {
                                "color": component_colors[ci % len(component_colors)],
                                "width": 1.5,
                                "dash": "dash",
                            },
                            "name": f"p = {p_str}",
                        })
                        ci += 1

        # Zero line reference
        traces.append({
            "x": [float(self._t[0]), float(self._t[-1])],
            "y": [0, 0],
            "type": "scatter",
            "mode": "lines",
            "line": {"color": "rgba(148,163,184,0.3)", "width": 1, "dash": "dot"},
            "showlegend": False,
            "hoverinfo": "skip",
        })

        # y(0⁻) vs y(0⁺): the curve starts at y(0⁺); mark y(0⁻) when they differ.
        if self._order >= 1:
            y_minus = float(self._ics_used[0])
            y_plus = float(self._y0plus[0])
            if abs(y_plus - y_minus) > 1e-9 * max(1.0, abs(y_plus)):
                ym = float(np.clip(y_minus, -self.CLAMP_VALUE, self.CLAMP_VALUE))
                yp = float(np.clip(y_plus, -self.CLAMP_VALUE, self.CLAMP_VALUE))
                traces.append({
                    "x": [0, 0],
                    "y": [ym, yp],
                    "type": "scatter",
                    "mode": "lines",
                    "line": {"color": "rgba(148,163,184,0.7)", "width": 1.5, "dash": "dot"},
                    "name": "jump at t = 0",
                    "showlegend": False,
                    "hoverinfo": "skip",
                })
                traces.append({
                    "x": [0],
                    "y": [ym],
                    "type": "scatter",
                    "mode": "markers",
                    "marker": {"symbol": "circle-open", "size": 11, "color": "#3b82f6",
                               "line": {"width": 2, "color": "#3b82f6"}},
                    "name": f"y(0⁻) = {self._fmt_num(y_minus)}",
                    "hovertemplate": "y(0⁻) = %{y:.4g} (before the input acts)<extra></extra>",
                })
                traces.append({
                    "x": [0],
                    "y": [yp],
                    "type": "scatter",
                    "mode": "markers",
                    "marker": {"symbol": "circle", "size": 8, "color": "#3b82f6"},
                    "name": f"y(0⁺) = {self._fmt_num(y_plus)}",
                    "hovertemplate": "y(0⁺) = %{y:.4g} (just after t = 0)<extra></extra>",
                })

        coeffs_str = ",".join(f"{c:.4g}" for c in self._output_poly)
        fingerprint = f"time-{coeffs_str}-{self.parameters.get('input_signal','delta')}"
        layout = {
            **self._base_layout(),
            "xaxis": {
                "title": "t (seconds)",
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
                "color": "#f1f5f9",
            },
            "yaxis": {
                "title": "y(t)",
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
                "color": "#f1f5f9",
                "autorange": True,
            },
            "uirevision": fingerprint,
        }

        return {
            "id": "time_response",
            "title": "Time-Domain Response y(t)",
            "data": traces,
            "layout": layout,
        }

    # ── get_state ─────────────────────────────────────────────────

    def _initial_conditions_metadata(self) -> Dict[str, Any]:
        values = self._initial_values()
        ivt_text, ivt_tex = self._ivt_texts()
        n = self._order
        return {
            "order": n,
            "ics_all": list(self._ics_all),
            "ics_used": list(self._ics_used),
            "labels_used": [self._ic_label(j) for j in range(n)],
            "all_zero": self._ics_zero,
            "note": self._ic_usage_note(),
            "summary": self._ic_sentence(),
            "I_coeffs": list(self._I_poly),
            "I_symbolic": self._ic_poly_symbolic(),
            "I_numeric": self._ic_poly_numeric(),
            "I_symbolic_tex": self._ic_poly_symbolic(tex=True),
            "I_numeric_tex": self._ic_poly_numeric_tex(),
            "initial_values": values,
            "y0plus": list(self._y0plus),
            "has_jump": any(v["jump"] != 0.0 for v in values),
            "jump_text": self._jump_text(values),
            "impulses": list(self._direct_terms),
            "impulse_text": self._impulse_text(),
            "ivt_text": ivt_text,
            "ivt_tex": ivt_tex,
            "explanation": self.EXPLANATION,
            "causal_note": self.CAUSAL_NOTE,
            "expression_zs": self._real_form_inner(self._groups_zs, self._direct_terms),
            "expression_zi": self._real_form_inner(self._groups_zi, []),
            "cancellations": self._cancellations(),
            "zi_cancellations": self._cancellations("cancel_zi"),
        }

    def get_state(self) -> Dict[str, Any]:
        if self._t is None:
            self._compute()

        state = super().get_state()

        # Reveal steps up to current
        visible_steps = self._solution_steps[: self._current_step + 1]

        state["metadata"] = {
            "simulation_type": "ode_laplace_solver",
            "hub_slots": self.HUB_SLOTS,
            "hub_domain": self.HUB_DOMAIN,
            "hub_dimensions": self.HUB_DIMENSIONS,
            "sticky_controls": True,
            "current_step": self._current_step,
            "max_step": self.MAX_STEP,
            "solution_steps": visible_steps,
            "all_step_titles": [s["title"] for s in self._solution_steps],
            "ode_text": self._ode_text,
            "input_signal_text": self._input_signal_name,
            "response_view": self.parameters.get("response_view", "total"),
            "warnings": list(self._warnings),
            "initial_conditions": self._initial_conditions_metadata(),
            "system_info": {
                "order": self._order,
                "output_coeffs": self._output_poly,
                "input_coeffs": self._input_poly,
                "poles": [
                    {"real": float(p.real), "imag": float(p.imag)}
                    for p in self._poles
                ],
                "zeros": [
                    {"real": float(z.real), "imag": float(z.imag)}
                    for z in self._zeros
                ],
                "residues": [
                    {"real": float(r.real), "imag": float(r.imag)}
                    for r in self._residues
                ],
                "is_stable": self._is_stable,
                "stability": self._stability,
                "preset_name": self.parameters.get("preset", "first_order_impulse"),
            },
            "classical_solution": self._compute_classical_solution(),
        }

        return state

    # ── Formatting helpers ────────────────────────────────────────

    @staticmethod
    def _fmt_complex(z: complex) -> str:
        """Format a complex number for display (typographic minus): −1, 2j, −1+2j."""
        r, i = float(np.real(z)), float(np.imag(z))
        if abs(i) < 1e-10:
            if abs(r - round(r)) < 1e-10 and abs(r) < 1e6:
                return str(int(round(r))).replace("-", "−")
            return f"{r:.4g}".replace("-", "−")
        sign = "+" if i >= 0 else "−"
        ai = abs(i)
        i_str = str(int(round(ai))) if abs(ai - round(ai)) < 1e-10 else f"{ai:.4g}"
        if i_str == "1":
            i_str = ""  # j, not 1j
        if abs(r) < 1e-10:
            return (f"−{i_str}j" if sign == "−" else f"{i_str}j").replace("-", "−")
        r_str = str(int(round(r))) if abs(r - round(r)) < 1e-10 else f"{r:.4g}"
        return f"{r_str}{sign}{i_str}j".replace("-", "−")

    @staticmethod
    def _signed_join(terms: Sequence[str]) -> str:
        """Join signed terms: ['a', '−b', 'c'] → 'a − b + c' (a leading minus becomes the operator)."""
        out = ""
        for term in terms:
            if not term:
                continue
            if not out:
                out = term
            elif term[0] in "−-":
                out += f" − {term[1:]}"
            else:
                out += f" + {term}"
        return out

    def _coef_times(self, c: float, body: str) -> str:
        """c·body with unit coefficients dropped: 1·e⁻ᵗ → e⁻ᵗ, −1·δ(t) → −δ(t)."""
        c_str = self._fmt_num(c)
        if not body:
            return c_str
        if c_str == "1":
            return body
        if c_str == "−1":
            return f"−{body}"
        return f"{c_str}·{body}"

    @staticmethod
    def _omega_t(w: float) -> str:
        """ωt for a trig argument: 2t, 0.7t, and t (not 1t) for ω = 1."""
        s = f"{abs(w):.4g}"
        return "t" if s == "1" else f"{s}t"

    @staticmethod
    def _t_power(k: int) -> str:
        """tᵏ/k! of the table pair R/(s−p)^(k+1) ↔ R·tᵏ/k!·eᵖᵗ: '', 't', 't²/2!', …"""
        if k == 0:
            return ""
        if k == 1:
            return "t"
        return f"t{_sup(k)}/{k}!"

    def _res_str(self, z: complex) -> str:
        """Residue for display; a complex value with both parts is parenthesised: (−0.1+0.2j)."""
        s = self._fmt_complex(z)
        if abs(float(np.imag(z))) >= 1e-10 and abs(float(np.real(z))) >= 1e-10:
            return f"({s})"
        return s

    def _res_times(self, r: complex, body: str) -> str:
        """Residue times a table entry: real residues drop a unit coefficient."""
        if abs(float(np.imag(r))) < 1e-10:
            return self._coef_times(float(np.real(r)), body)
        return f"{self._res_str(r)}·{body}"

    @staticmethod
    def _fmt_coeff_simple(coeff: float) -> str:
        """Format coefficient without sign handling (for transform terms)."""
        if abs(coeff - 1.0) < 1e-10:
            return ""
        if abs(coeff + 1.0) < 1e-10:
            return "−"
        if abs(coeff - round(coeff)) < 1e-10:
            return str(int(round(coeff)))
        return f"{coeff:.4g}"

    @staticmethod
    def _format_poly(coeffs, var: str = "s") -> str:
        """Format polynomial coefficients as a readable string.

        coeffs in descending powers: [aₙ, aₙ₋₁, ..., a₁, a₀]
        """
        if isinstance(coeffs, np.ndarray):
            coeffs = coeffs.tolist()
        degree = len(coeffs) - 1
        terms = []
        superscripts = {"0": "⁰", "1": "", "2": "²", "3": "³", "4": "⁴", "5": "⁵"}

        for i, c in enumerate(coeffs):
            power = degree - i
            if abs(c) < 1e-10:
                continue
            # Format coefficient
            abs_c = abs(c)
            if abs(abs_c - 1.0) < 1e-10 and power > 0:
                c_str = ""
            elif abs(abs_c - round(abs_c)) < 1e-10:
                c_str = str(int(round(abs_c)))
            else:
                c_str = f"{abs_c:.4g}"

            # Format variable^power
            if power == 0:
                var_str = c_str if c_str else "1"
            elif power == 1:
                var_str = f"{c_str}{var}"
            else:
                sup = superscripts.get(str(power), f"^{power}")
                var_str = f"{c_str}{var}{sup}"

            # Sign
            if len(terms) == 0:
                prefix = "−" if c < 0 else ""
            else:
                prefix = " − " if c < 0 else " + "

            terms.append(f"{prefix}{var_str}")

        return "".join(terms) if terms else "0"

    def _factored_form(self, coeffs) -> str:
        """Factored denominator from the exact pole structure, e.g. s(s + 1)(s + 2)²(s² + 2s + 5).

        A repeated root is written once with its multiplicity as a power, a
        conjugate pair as a real quadratic; factors appear in np.roots order.
        """
        if isinstance(coeffs, list):
            coeffs = np.array(coeffs, dtype=float)
        if len(coeffs) <= 1:
            return self._fmt_num(coeffs[0]) if len(coeffs) == 1 else "1"
        factors = self._factor_list(coeffs)
        leading = float(coeffs[0])
        if abs(leading - 1.0) > 1e-10:
            return f"{self._fmt_num(leading)}·{''.join(factors)}"
        return "".join(factors) or "1"

    def _factor_list(self, coeffs) -> List[str]:
        """Factors of the monic part of the denominator (see _factored_form)."""
        coeffs = np.asarray(coeffs, dtype=float)
        entries = self._pole_entries
        if not entries:
            return []
        ref = np.atleast_1d(np.roots(coeffs)).astype(complex)
        # first np.roots occurrence of each distinct pole (for the old ordering)
        first = []
        for en in entries:
            d = np.abs(ref - en["value"]) if len(ref) else np.array([0.0])
            first.append(int(np.argmin(d)) if len(ref) else 0)
        order = sorted(range(len(entries)), key=lambda j: first[j])

        factors = []
        done = set()
        for j in order:
            if j in done:
                continue
            en = entries[j]
            r = en["value"]
            done.add(j)
            m = en["mult_D"]
            power = _sup(m) if m > 1 else ""
            if abs(r.imag) > 1e-10:
                # pair with its conjugate
                for k in order:
                    if k not in done and abs(entries[k]["value"] - r.conjugate()) < 1e-8 * max(1.0, abs(r)):
                        done.add(k)
                        break
                quad = self._format_poly([1.0, -2 * r.real, r.real**2 + r.imag**2], "s")
                factors.append(f"({quad}){power}")
            elif abs(r.real) < 1e-10:
                factors.insert(0, f"s{power}")
            else:
                factors.append(f"{self._fmt_pole_factor(r)}{power}")
        return factors

    def _describe_poles(self) -> str:
        """Poles of Y(s) with their location (a pole is not itself 'stable';
        system stability is judged from the roots of A(s) in step 5)."""
        if len(self._poles) == 0:
            return "No poles."

        parts = []
        for i, p in enumerate(self._poles):
            p_str = self._fmt_complex(p)
            if p.real < -1e-10:
                parts.append(f"p{i+1} = {p_str} (Re < 0)")
            elif p.real > 1e-10:
                parts.append(f"p{i+1} = {p_str} (Re > 0)")
            else:
                parts.append(f"p{i+1} = {p_str} (on the jω axis)")

        return "Poles of Y(s): " + ", ".join(parts) + "."

    def _describe_input_transform(self) -> Dict[str, str]:
        """Describe the Laplace transform of the input signal."""
        sig = self.parameters.get("input_signal", "delta")
        alpha = float(self.parameters.get("alpha", 1.0))
        omega = float(self.parameters.get("omega", 2.0))

        if sig == "delta":
            display = "1"
        elif sig == "step":
            display = "1/s"
        elif sig == "exp":
            display = f"1/(s + {alpha:.4g})"
        elif sig == "cosine":
            display = f"s/(s² + {omega**2:.4g})"
        else:
            display = "1"

        # B(s) * X(s) for the full RHS (multi-term B(s) parenthesised)
        B_str = self._paren(self._format_poly(self._input_poly, "s"))
        if display == "1":
            B_X = B_str if B_str != "1" else "1"
        else:
            B_X = f"{B_str}·{display}" if B_str != "1" else display

        return {
            "signal_name": self._input_signal_name,
            "X_s_display": display,
            "B_X_display": B_X,
        }

    @staticmethod
    def _fmt_pole_factor(p: complex) -> str:
        """Format (s - p) as a clean factor, e.g. (s + 1) instead of (s − (-1))."""
        r = float(np.real(p))
        i = float(np.imag(p))
        if abs(i) < 1e-10:
            if abs(r) < 1e-10:
                return "s"
            elif r < 0:
                val = abs(r)
                v_str = str(int(round(val))) if abs(val - round(val)) < 1e-10 else f"{val:.4g}"
                return f"(s + {v_str})"
            else:
                v_str = str(int(round(r))) if abs(r - round(r)) < 1e-10 else f"{r:.4g}"
                return f"(s − {v_str})"
        p_str = ODELaplaceSolverSimulator._fmt_complex(p)
        if abs(r) < 1e-10:
            # purely imaginary: (s − 2j), (s + 2j)
            return f"(s + {p_str[1:]})" if p_str.startswith("−") else f"(s − {p_str})"
        return f"(s − ({p_str}))"

    @staticmethod
    def _fmt_exp(p_val: float) -> str:
        """Format e^{pt} cleanly, e.g. e^(−t) instead of e^(-1t)."""
        if abs(p_val) < 1e-10:
            return ""  # e^0 = 1
        elif abs(p_val - 1.0) < 1e-10:
            return "eᵗ"
        elif abs(p_val + 1.0) < 1e-10:
            return "e⁻ᵗ"
        elif p_val < 0:
            val = abs(p_val)
            v_str = str(int(round(val))) if abs(val - round(val)) < 1e-10 else f"{val:.4g}"
            return f"e^(−{v_str}t)"
        else:
            v_str = str(int(round(p_val))) if abs(p_val - round(p_val)) < 1e-10 else f"{p_val:.4g}"
            return f"e^({v_str}t)"

    @staticmethod
    def _ordinal(n: int) -> str:
        """Return ordinal string for a number."""
        suffixes = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th"}
        return suffixes.get(n, f"{n}th")
