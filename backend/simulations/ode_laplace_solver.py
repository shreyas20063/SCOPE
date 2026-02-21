"""
ODE Solver via Laplace Transform — Step-by-Step

Given a linear constant-coefficient ODE and an input signal, walks through
the complete Laplace transform solution pipeline:
  (a) take L{} of each term, showing derivative→sⁿ mapping
  (b) solve the resulting algebraic equation for Y(s)
  (c) partial fraction decomposition
  (d) inverse Laplace via table lookup
  (e) plot the time-domain solution y(t)

Key insight: no homogeneous/particular solution splitting needed.

Based on MIT 6.003 Lecture 6, Slides 25–33.
"""

from math import factorial
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy.signal import residue

from .base_simulator import BaseSimulator


class ODELaplaceSolverSimulator(BaseSimulator):
    """Simulator for step-by-step ODE solving via Laplace transform."""

    MAX_STEP = 5
    CLAMP_VALUE = 200.0
    NUM_POINTS = 500

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
        "show_compare": False,
        "t_max": 8.0,
    }

    # ── Init ──────────────────────────────────────────────────────

    def __init__(self, simulation_id: str) -> None:
        super().__init__(simulation_id)

        self._current_step: int = 0

        # Polynomial coefficients (descending powers of s)
        self._output_poly: List[float] = []  # A(s) = aₙsⁿ + ... + a₀
        self._input_poly: List[float] = []   # B(s) = bₘsᵐ + ... + b₀

        # Input signal transform X(s) = X_num / X_den
        self._X_s_num: List[float] = []
        self._X_s_den: List[float] = []
        self._input_signal_name: str = "δ(t)"

        # Combined Y(s) = Y_num / Y_den
        self._Y_num: np.ndarray = np.array([1.0])
        self._Y_den: np.ndarray = np.array([1.0, 1.0])

        # Partial fraction results
        self._residues: np.ndarray = np.array([])
        self._poles: np.ndarray = np.array([])
        self._zeros: np.ndarray = np.array([])
        self._direct_terms: np.ndarray = np.array([])

        # Time domain
        self._t: Optional[np.ndarray] = None
        self._y_t: Optional[np.ndarray] = None
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
            # Reset steps when system changes
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
        """Parse comma-separated coefficient string into list of floats."""
        try:
            parts = [s.strip() for s in expr.split(",") if s.strip()]
            coeffs = [float(p) for p in parts]
            return coeffs if coeffs else [1.0]
        except (ValueError, TypeError):
            return [1.0]

    def _load_coefficients(self) -> None:
        """Load output/input polynomials from preset or custom input."""
        preset = self.parameters.get("preset", "first_order_impulse")

        if preset != "custom" and preset in self.PRESETS:
            p = self.PRESETS[preset]
            self._output_poly = list(p["output_coeffs"])
            self._input_poly = list(p["input_coeffs"])
            # Presets override input signal
            self.parameters["input_signal"] = p.get("input_signal", "delta")
            if "alpha" in p:
                self.parameters["alpha"] = p["alpha"]
            if "omega" in p:
                self.parameters["omega"] = p["omega"]
        else:
            self._output_poly = self._parse_coeffs(
                str(self.parameters.get("output_coeffs", "1, 1"))
            )
            self._input_poly = self._parse_coeffs(
                str(self.parameters.get("input_coeffs", "1"))
            )

        # Validate: need at least first-order ODE
        if len(self._output_poly) < 2:
            self._output_poly = [1, 1]
        # Ensure leading coefficient is nonzero
        if abs(self._output_poly[0]) < 1e-15:
            self._output_poly[0] = 1.0

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
            self._input_signal_name = f"e^(−{alpha:.4g}t)u(t)"
        elif sig == "cosine":
            self._X_s_num = [1.0, 0.0]  # s
            self._X_s_den = [1.0, 0.0, omega**2]  # s² + ω²
            self._input_signal_name = f"cos({omega:.4g}t)u(t)"
        else:
            self._X_s_num = [1.0]
            self._X_s_den = [1.0]
            self._input_signal_name = "δ(t)"

    # ── Core computation ──────────────────────────────────────────

    def _compute(self) -> None:
        """Full computation pipeline."""
        self._load_coefficients()
        self._compute_input_transform()
        self._form_Y_s()
        self._partial_fraction_decomposition()
        self._assemble_time_domain()
        self._build_ode_text()
        self._build_solution_steps()

    def _form_Y_s(self) -> None:
        """Form Y(s) = B(s)·X_num(s) / (A(s)·X_den(s))."""
        A = np.array(self._output_poly, dtype=float)
        B = np.array(self._input_poly, dtype=float)
        X_num = np.array(self._X_s_num, dtype=float)
        X_den = np.array(self._X_s_den, dtype=float)

        self._Y_num = np.polymul(B, X_num)
        self._Y_den = np.polymul(A, X_den)

        # Normalize by leading coefficient
        if abs(self._Y_den[0]) > 1e-15:
            self._Y_num = self._Y_num / self._Y_den[0]
            self._Y_den = self._Y_den / self._Y_den[0]

        # Find zeros
        if len(self._Y_num) > 1:
            self._zeros = np.roots(self._Y_num)
        else:
            self._zeros = np.array([])

    def _partial_fraction_decomposition(self) -> None:
        """Compute partial fraction decomposition of Y(s)."""
        try:
            r, p, k = residue(self._Y_num, self._Y_den)
            self._residues = r
            self._poles = p
            self._direct_terms = k
        except Exception:
            self._poles = np.roots(self._Y_den) if len(self._Y_den) > 1 else np.array([])
            self._residues = np.array([])
            self._direct_terms = np.array([])

        self._is_stable = (
            all(p.real < 1e-10 for p in self._poles)
            if len(self._poles) > 0
            else True
        )

    def _assemble_time_domain(self) -> None:
        """Build y(t) from partial fraction terms."""
        t_max = float(self.parameters.get("t_max", 8.0))
        t = np.linspace(0, t_max, self.NUM_POINTS)
        self._t = t

        if len(self._residues) == 0 or len(self._poles) == 0:
            self._y_t = np.zeros_like(t)
            self._x_t = self._compute_input_signal(t)
            return

        y = np.zeros(len(t), dtype=complex)

        # Group poles by proximity to handle repeated poles
        # scipy.signal.residue returns repeated poles consecutively
        # with residues for (s-p)^{-1}, (s-p)^{-2}, ... (highest first)
        pole_groups = self._group_poles()

        for group in pole_groups:
            pole = group["pole"]
            resids = group["residues"]
            for k, r in enumerate(resids):
                # L⁻¹{ R / (s-p)^(k+1) } = R · t^k / k! · e^{pt} · u(t)
                term = r * (t ** k / factorial(k)) * np.exp(pole * t)
                y += term

        # Add direct terms (impulse components at t=0, rare for proper systems)
        # k[0]*δ(t) + k[1]*δ'(t) + ... — we skip display of these

        self._y_t = np.clip(np.real(y), -self.CLAMP_VALUE, self.CLAMP_VALUE)
        self._x_t = self._compute_input_signal(t)

    def _group_poles(self) -> List[Dict[str, Any]]:
        """Group residues by pole value for repeated pole handling.

        scipy.signal.residue returns repeated poles listed consecutively.
        For a pole of multiplicity m, residues are ordered:
          r[0]/(s-p) + r[1]/(s-p)^2 + ... + r[m-1]/(s-p)^m
        Index k corresponds to (s-p)^{-(k+1)} — already the right order
        for inverse Laplace: L^{-1}{R/(s-p)^{k+1}} = R*t^k/k!*e^{pt}.
        """
        groups: List[Dict[str, Any]] = []
        used = set()

        for i in range(len(self._poles)):
            if i in used:
                continue
            p = self._poles[i]
            # Find all indices with the same pole
            indices = [
                j for j in range(len(self._poles))
                if j not in used and abs(self._poles[j] - p) < 1e-8
            ]
            used.update(indices)
            # Residues are already in the right order: index k → (s-p)^{-(k+1)}
            resids = [self._residues[j] for j in indices]
            groups.append({
                "pole": p,
                "residues": resids,
                "multiplicity": len(indices),
            })

        return groups

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

    def _build_ode_text(self) -> None:
        """Build human-readable ODE string."""
        order = len(self._output_poly) - 1
        terms = []
        for i, coeff in enumerate(self._output_poly):
            power = order - i
            if abs(coeff) < 1e-15:
                continue
            sym = self.DERIVATIVE_SYMBOLS[power] if power < len(self.DERIVATIVE_SYMBOLS) else f"y⁽{power}⁾(t)"
            coeff_str = self._fmt_coeff(coeff, is_first=(len(terms) == 0))
            terms.append(f"{coeff_str}{sym}")

        lhs = " ".join(terms) if terms else "0"

        # RHS: input coefficients × x(t) and derivatives
        input_order = len(self._input_poly) - 1
        rhs_terms = []
        x_derivs = ["x(t)", "ẋ(t)", "ẍ(t)", "x‴(t)", "x⁽⁴⁾(t)"]
        for i, coeff in enumerate(self._input_poly):
            power = input_order - i
            if abs(coeff) < 1e-15:
                continue
            sym = x_derivs[power] if power < len(x_derivs) else f"x⁽{power}⁾(t)"
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
        """Step 0: Display the original ODE."""
        order = len(self._output_poly) - 1
        sig = self._input_signal_name

        # Build the full ODE with actual input signal substituted
        # Replace x(t) placeholder with the actual input signal
        ode_with_input = self._ode_text
        if sig != "x(t)":
            # For presets, RHS is typically just a coefficient times x(t)
            # Show the actual input signal
            pass

        return {
            "step": 0,
            "title": "Original Differential Equation",
            "equation": self._ode_text,
            "description": (
                f"A {self._ordinal(order)}-order linear constant-coefficient ODE "
                f"with input x(t) = {sig}. "
                f"All initial conditions are zero (system at rest)."
            ),
            "details": {
                "order": order,
                "input_signal": sig,
            },
        }

    def _step_1_take_laplace(self) -> Dict[str, Any]:
        """Step 1: Take the Laplace transform of each term."""
        order = len(self._output_poly) - 1
        s_powers = ["", "s", "s²", "s³", "s⁴"]

        # Build LHS term-by-term transforms
        term_transforms = []
        lhs_terms = []
        for i, coeff in enumerate(self._output_poly):
            power = order - i
            if abs(coeff) < 1e-15:
                continue
            deriv_sym = self.DERIVATIVE_SYMBOLS[power] if power < len(self.DERIVATIVE_SYMBOLS) else f"y⁽{power}⁾(t)"
            s_sym = s_powers[power] if power < len(s_powers) else f"s^{power}"
            s_Y = f"{s_sym}Y(s)" if power > 0 else "Y(s)"

            coeff_display = self._fmt_coeff_simple(coeff)
            term_transforms.append({
                "original": f"{coeff_display}{deriv_sym}",
                "transform": f"{coeff_display}{s_Y}",
                "property": f"ℒ{{y⁽{power}⁾}} = {s_sym}Y(s)" if power > 0 else "ℒ{y} = Y(s)",
            })
            lhs_terms.append(f"{coeff_display}{s_Y}")

        # Input signal transform
        x_transform = self._describe_input_transform()

        # Algebraic equation after factoring
        A_poly_str = self._format_poly(self._output_poly, "s")
        lhs_factored = f"({A_poly_str})Y(s)"

        return {
            "step": 1,
            "title": "Take Laplace Transform",
            "equation": f"{' + '.join(lhs_terms)} = {x_transform['X_s_display']}",
            "description": (
                f"Using the derivative property: ℒ{{y⁽ⁿ⁾(t)}} = sⁿ·Y(s) (bilateral). "
                f"Input: ℒ{{{self._input_signal_name}}} = {x_transform['X_s_display']}."
            ),
            "details": {
                "term_transforms": term_transforms,
                "input_transform": x_transform,
                "factored_form": f"{lhs_factored} = {x_transform['B_X_display']}",
            },
        }

    def _step_2_solve_for_Y(self) -> Dict[str, Any]:
        """Step 2: Solve the algebraic equation for Y(s)."""
        num_str = self._format_poly(self._Y_num, "s")
        den_str = self._format_poly(self._Y_den, "s")

        # Factor denominator to show poles
        factored_den = self._factored_form(self._Y_den)
        poles_desc = self._describe_poles()

        return {
            "step": 2,
            "title": "Solve for Y(s)",
            "equation": f"Y(s) = ({num_str}) / ({den_str})",
            "description": f"Factored: Y(s) = ({num_str}) / {factored_den}. {poles_desc}",
            "details": {
                "numerator": num_str,
                "denominator": den_str,
                "factored_denominator": factored_den,
                "poles": [
                    {"real": float(p.real), "imag": float(p.imag)}
                    for p in self._poles
                ],
                "key_insight": (
                    "The Laplace transform converted the differential equation "
                    "into a simple algebraic equation — no need for homogeneous "
                    "and particular solutions!"
                ),
            },
        }

    def _step_3_partial_fractions(self) -> Dict[str, Any]:
        """Step 3: Partial fraction decomposition."""
        if len(self._residues) == 0:
            return {
                "step": 3,
                "title": "Partial Fraction Decomposition",
                "equation": "Y(s) has no poles (trivial case)",
                "description": "No decomposition needed.",
                "details": {},
            }

        terms = []
        algebra_steps = []
        pole_groups = self._group_poles()

        for group in pole_groups:
            p = group["pole"]
            mult = group["multiplicity"]
            resids = group["residues"]

            for k_idx, r in enumerate(resids):
                power = k_idx + 1  # scipy: index 0 → (s-p)^1, index 1 → (s-p)^2
                r_str = self._fmt_complex(r)
                p_factor = self._fmt_pole_factor(p)

                # Skip zero residues in display
                if abs(r) < 1e-10:
                    continue

                if power == 1:
                    term_str = f"{r_str} / {p_factor}"
                else:
                    term_str = f"{r_str} / {p_factor}{self._superscript(power)}"
                terms.append(term_str)

                algebra_steps.append({
                    "residue": r_str,
                    "pole": self._fmt_complex(p),
                    "power": power,
                    "explanation": (
                        f"R = {r_str} at pole s = {self._fmt_complex(p)}"
                        + (f" (order {power})" if power > 1 else "")
                    ),
                })

        # Direct terms
        direct_str = ""
        if len(self._direct_terms) > 0:
            direct_parts = []
            for k, d in enumerate(self._direct_terms):
                if abs(d) > 1e-10:
                    d_val = float(np.real(d))
                    if k == 0:
                        direct_parts.append(f"{d_val:.4g}")
                    else:
                        direct_parts.append(f"{d_val:.4g}·s^{k}")
            if direct_parts:
                direct_str = " + " + " + ".join(direct_parts)

        pfe_str = " + ".join(terms) + direct_str

        return {
            "step": 3,
            "title": "Partial Fraction Decomposition",
            "equation": f"Y(s) = {pfe_str}",
            "description": f"Decomposed into {len(terms)} partial fraction term(s).",
            "details": {
                "algebra_steps": algebra_steps,
                "pfe_terms": terms,
            },
        }

    def _step_4_inverse_laplace(self) -> Dict[str, Any]:
        """Step 4: Inverse Laplace transform via table lookup."""
        if len(self._residues) == 0:
            return {
                "step": 4,
                "title": "Inverse Laplace Transform",
                "equation": "y(t) = 0",
                "description": "",
                "details": {"pairs": []},
            }

        pairs = []
        time_terms = []
        pole_groups = self._group_poles()

        for group in pole_groups:
            p = group["pole"]
            resids = group["residues"]

            for k, r in enumerate(resids):
                # Skip zero residues
                if abs(r) < 1e-10:
                    continue

                r_str = self._fmt_complex(r)
                p_factor = self._fmt_pole_factor(p)
                p_val = float(np.real(p))
                exp_str = self._fmt_exp(p_val) if abs(p.imag) < 1e-10 else f"e^({self._fmt_complex(p)}t)"

                power = k + 1  # scipy order: index k → (s-p)^{-(k+1)}

                if power == 1 and abs(p.imag) < 1e-10:
                    s_form = f"{r_str} / {p_factor}"
                    t_form = f"{r_str}·{exp_str}·u(t)" if exp_str else f"{r_str}·u(t)"
                    table_entry = "ℒ⁻¹{R/(s+a)} = R·e⁻ᵃᵗ·u(t)"
                elif power == 1 and abs(p.imag) >= 1e-10:
                    s_form = f"{r_str} / {p_factor}"
                    t_form = f"{r_str}·{exp_str}·u(t)"
                    table_entry = "ℒ⁻¹{R/(s−p)} = R·eᵖᵗ·u(t) (combine conjugates → real)"
                else:
                    sup = self._superscript(power)
                    s_form = f"{r_str} / {p_factor}{sup}"
                    if k == 1:
                        t_form = f"{r_str}·t·{exp_str}·u(t)" if exp_str else f"{r_str}·t·u(t)"
                    elif k > 1:
                        t_form = f"{r_str}·t{self._superscript(k)}/{k}!·{exp_str}·u(t)"
                    else:
                        t_form = f"{r_str}·{exp_str}·u(t)" if exp_str else f"{r_str}·u(t)"
                    table_entry = f"ℒ⁻¹{{R/(s+a){sup}}} = R·tᵏ/k!·e⁻ᵃᵗ·u(t)"

                pairs.append({
                    "s_domain": s_form,
                    "time_domain": t_form,
                    "table_entry": table_entry,
                })
                time_terms.append(t_form)

        return {
            "step": 4,
            "title": "Inverse Laplace Transform (Table Lookup)",
            "equation": "y(t) = " + " + ".join(time_terms),
            "description": "Each partial fraction term maps to a known Laplace transform pair.",
            "details": {
                "pairs": pairs,
                "table_reference": [
                    {"s_form": "R/(s+a)", "t_form": "R·e⁻ᵃᵗ·u(t)", "condition": "Re(s) > −a"},
                    {"s_form": "R/(s+a)²", "t_form": "R·t·e⁻ᵃᵗ·u(t)", "condition": "Repeated pole"},
                    {"s_form": "ω/((s+σ)²+ω²)", "t_form": "e⁻σᵗsin(ωt)·u(t)", "condition": "Complex poles"},
                ],
            },
        }

    def _step_5_final_solution(self) -> Dict[str, Any]:
        """Step 5: Final combined solution with observations."""
        # Build simplified real-form expression
        expression = self._build_real_form_expression()

        # Stability note
        if self._is_stable:
            stability = "All poles have Re(s) < 0 → stable, decaying response."
        else:
            unstable_poles = [p for p in self._poles if p.real >= 0]
            stability = (
                f"UNSTABLE: {len(unstable_poles)} pole(s) with Re(s) ≥ 0 → "
                f"response grows without bound."
            )

        return {
            "step": 5,
            "title": "Final Solution y(t)",
            "equation": f"y(t) = {expression}",
            "description": stability,
            "details": {
                "expression": expression,
                "is_stable": self._is_stable,
                "key_insight": (
                    "The complete solution was obtained entirely through "
                    "algebraic manipulation in the s-domain — no need to "
                    "split into homogeneous and particular solutions!"
                ),
            },
        }

    def _build_real_form_expression(self) -> str:
        """Build a human-readable real-form expression for y(t)."""
        if len(self._residues) == 0:
            return "0"

        terms = []
        used_conjugates = set()
        pole_groups = self._group_poles()

        for group in pole_groups:
            p = group["pole"]
            resids = group["residues"]

            for k, r in enumerate(resids):
                # Skip if this is the conjugate of an already-processed complex pole
                conj_key = (round(p.real, 8), round(-p.imag, 8), k)
                if conj_key in used_conjugates:
                    continue

                if abs(p.imag) > 1e-10:
                    # Complex pole: combine with conjugate
                    used_conjugates.add((round(p.real, 8), round(p.imag, 8), k))
                    sigma = p.real
                    omega_d = abs(p.imag)
                    # 2*Re(R*e^{pt}) = e^{σt}*(A*cos(ωt) + B*sin(ωt))
                    A = 2 * r.real
                    B = -2 * r.imag
                    exp_part = f"e^({sigma:.4g}t)" if abs(sigma) > 1e-10 else ""
                    cos_part = f"{A:.4g}cos({omega_d:.4g}t)" if abs(A) > 1e-10 else ""
                    sin_part = f"{B:.4g}sin({omega_d:.4g}t)" if abs(B) > 1e-10 else ""
                    inner = " + ".join(filter(None, [cos_part, sin_part]))
                    if exp_part and inner:
                        term = f"{exp_part}·({inner})"
                    elif exp_part:
                        term = exp_part
                    elif inner:
                        term = inner
                    else:
                        term = "0"
                    if k > 0:
                        term = f"t^{k}/{k}!·{term}"
                    terms.append(term)
                else:
                    # Real pole
                    r_val = float(np.real(r))
                    p_val = float(np.real(p))
                    r_str = f"{r_val:.4g}" if abs(r_val - round(r_val)) > 1e-10 else str(int(round(r_val)))
                    exp_str = self._fmt_exp(p_val)
                    t_power = f"t/{k}!·" if k == 1 else (f"t^{k}/{k}!·" if k > 1 else "")

                    # Skip zero residues
                    if abs(r_val) < 1e-10:
                        continue

                    if exp_str and t_power:
                        term = f"{r_str}·{t_power}{exp_str}"
                    elif exp_str:
                        term = f"{r_str}·{exp_str}"
                    elif t_power:
                        term = f"{r_str}·{t_power.rstrip('·')}"
                    else:
                        term = r_str
                    terms.append(term)

        if not terms:
            return "0"

        result = terms[0]
        for t in terms[1:]:
            if t.startswith("−") or t.startswith("-"):
                result += f" {t}"
            else:
                result += f" + {t}"

        return f"({result})·u(t)"

    # ── Classical method comparison ───────────────────────────────

    def _compute_classical_solution(self) -> Optional[Dict[str, Any]]:
        """Build classical method description for comparison."""
        if not bool(self.parameters.get("show_compare", False)):
            return None

        A = np.array(self._output_poly, dtype=float)
        char_poles = np.roots(A)
        order = len(A) - 1

        # Characteristic equation
        char_eq = self._format_poly(self._output_poly, "s") + " = 0"

        # Roots description
        roots_desc = []
        for i, p in enumerate(char_poles):
            if abs(p.imag) < 1e-10:
                roots_desc.append(f"s{i+1} = {float(p.real):.4g}")
            else:
                roots_desc.append(f"s{i+1} = {self._fmt_complex(p)}")

        # Homogeneous solution form
        homo_terms = []
        processed = set()
        for i, p in enumerate(char_poles):
            key = (round(p.real, 6), round(abs(p.imag), 6))
            if key in processed:
                continue
            processed.add(key)

            # Count multiplicity
            mult = sum(1 for q in char_poles if abs(q - p) < 1e-6)

            if abs(p.imag) < 1e-10:
                for m in range(mult):
                    t_power = f"t^{m}·" if m > 0 else ""
                    homo_terms.append(f"C·{t_power}e^({p.real:.4g}t)")
            else:
                sigma = p.real
                omega_d = abs(p.imag)
                homo_terms.append(
                    f"e^({sigma:.4g}t)(C₁cos({omega_d:.4g}t) + C₂sin({omega_d:.4g}t))"
                )

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

        return {
            "characteristic_eq": char_eq,
            "roots": roots_desc,
            "homogeneous_form": " + ".join(homo_terms) if homo_terms else "0",
            "particular_form": particular,
            "summary": (
                f"Classical method requires {order + 2} steps: "
                f"(1) characteristic equation, (2) find {order} root(s), "
                f"(3) form y_h with {order} unknown constant(s), "
                f"(4) guess particular solution form, "
                f"(5) substitute & solve for unknowns, "
                f"(6) apply initial conditions. "
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
        """Plot the s-plane pole-zero map."""
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

        # Zeros (○ markers)
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
        """Plot the time-domain response y(t)."""
        if self._t is None or self._y_t is None:
            return {"id": "time_response", "title": "y(t)", "data": [], "layout": {}}

        traces: List[Dict[str, Any]] = [
            {
                "x": self._t.tolist(),
                "y": self._y_t.tolist(),
                "type": "scatter",
                "mode": "lines",
                "line": {"color": "#3b82f6", "width": 2.5},
                "name": "y(t)",
            },
        ]

        # At step 5, also show individual component terms
        if self._current_step >= 5:
            component_colors = ["#14b8a6", "#ef4444", "#f59e0b", "#a855f7", "#ec4899"]
            pole_groups = self._group_poles()
            ci = 0
            used_conjugates = set()

            for group in pole_groups:
                p = group["pole"]
                resids = group["residues"]

                for k, r in enumerate(resids):
                    conj_key = (round(p.real, 8), round(-p.imag, 8), k)
                    if conj_key in used_conjugates:
                        continue

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

                    term_clipped = np.clip(term, -self.CLAMP_VALUE, self.CLAMP_VALUE)
                    p_str = self._fmt_complex(p)
                    traces.append({
                        "x": self._t.tolist(),
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

    def get_state(self) -> Dict[str, Any]:
        if self._t is None:
            self._compute()

        state = super().get_state()

        # Reveal steps up to current
        visible_steps = self._solution_steps[: self._current_step + 1]

        state["metadata"] = {
            "simulation_type": "ode_laplace_solver",
            "sticky_controls": True,
            "current_step": self._current_step,
            "max_step": self.MAX_STEP,
            "solution_steps": visible_steps,
            "all_step_titles": [s["title"] for s in self._solution_steps],
            "ode_text": self._ode_text,
            "input_signal_text": self._input_signal_name,
            "system_info": {
                "order": len(self._output_poly) - 1,
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
                "preset_name": self.parameters.get("preset", "first_order_impulse"),
            },
            "classical_solution": self._compute_classical_solution(),
        }

        return state

    # ── Formatting helpers ────────────────────────────────────────

    @staticmethod
    def _fmt_complex(z: complex) -> str:
        """Format a complex number for display."""
        r, i = float(np.real(z)), float(np.imag(z))
        if abs(i) < 1e-10:
            if abs(r - round(r)) < 1e-10 and abs(r) < 1e6:
                return str(int(round(r)))
            return f"{r:.4g}"
        sign = "+" if i >= 0 else "−"
        ai = abs(i)
        if abs(r) < 1e-10:
            if abs(ai - round(ai)) < 1e-10:
                return f"{sign}{int(round(ai))}j" if sign == "−" else f"{int(round(ai))}j"
            return f"{sign}{ai:.4g}j" if sign == "−" else f"{ai:.4g}j"
        r_str = str(int(round(r))) if abs(r - round(r)) < 1e-10 else f"{r:.4g}"
        i_str = str(int(round(ai))) if abs(ai - round(ai)) < 1e-10 else f"{ai:.4g}"
        return f"{r_str}{sign}{i_str}j"

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
        """Get factored polynomial form from roots."""
        if isinstance(coeffs, list):
            coeffs = np.array(coeffs, dtype=float)
        if len(coeffs) <= 1:
            return f"{coeffs[0]:.4g}" if len(coeffs) == 1 else "1"

        roots = np.roots(coeffs)
        factors = []
        processed = set()

        for i, r in enumerate(roots):
            if i in processed:
                continue
            r_str = self._fmt_complex(r)
            # Check for conjugate pair
            conj_idx = None
            for j in range(i + 1, len(roots)):
                if j not in processed and abs(roots[j] - np.conj(r)) < 1e-8 and abs(r.imag) > 1e-10:
                    conj_idx = j
                    break

            if conj_idx is not None:
                processed.add(conj_idx)
                # Show as quadratic factor
                sigma = r.real
                omega_sq = r.real**2 + r.imag**2
                b = -2 * sigma
                c = omega_sq
                quad = self._format_poly([1.0, b, c], "s")
                factors.append(f"({quad})")
            else:
                factors.append(f"(s − ({r_str}))")

        leading = float(coeffs[0])
        if abs(leading - 1.0) > 1e-10:
            return f"{leading:.4g}·{''.join(factors)}"
        return "".join(factors)

    def _describe_poles(self) -> str:
        """Get a human-readable description of the poles."""
        if len(self._poles) == 0:
            return "No poles."

        parts = []
        for i, p in enumerate(self._poles):
            p_str = self._fmt_complex(p)
            if p.real < -1e-10:
                parts.append(f"p{i+1} = {p_str} (stable)")
            elif p.real > 1e-10:
                parts.append(f"p{i+1} = {p_str} (unstable)")
            else:
                parts.append(f"p{i+1} = {p_str} (marginal)")

        return "Poles: " + ", ".join(parts) + "."

    def _describe_input_transform(self) -> Dict[str, str]:
        """Describe the Laplace transform of the input signal."""
        sig = self.parameters.get("input_signal", "delta")
        alpha = float(self.parameters.get("alpha", 1.0))
        omega = float(self.parameters.get("omega", 2.0))

        X_s_str = self._format_poly(self._X_s_num, "s")
        X_den_str = self._format_poly(self._X_s_den, "s")

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

        # B(s) * X(s) for the full RHS
        B_str = self._format_poly(self._input_poly, "s")
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
                return "(s)"
            elif r < 0:
                val = abs(r)
                v_str = str(int(round(val))) if abs(val - round(val)) < 1e-10 else f"{val:.4g}"
                return f"(s + {v_str})"
            else:
                v_str = str(int(round(r))) if abs(r - round(r)) < 1e-10 else f"{r:.4g}"
                return f"(s − {v_str})"
        else:
            p_str = ODELaplaceSolverSimulator._fmt_complex(p)
            return f"(s − ({p_str}))"

    @staticmethod
    def _superscript(n: int) -> str:
        """Return unicode superscript for small integers."""
        sup_map = {2: "²", 3: "³", 4: "⁴", 5: "⁵"}
        return sup_map.get(n, f"^{n}")

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
