"""
State Space Analyzer Simulator

Converts transfer functions and differential equations to state-space form (A, B, C, D matrices).
For nonlinear systems, finds equilibrium points via symbolic solving and linearizes using
the Jacobian method. Returns step-by-step LaTeX derivations for educational display.
"""

import sympy as sp
from sympy.parsing.sympy_parser import (
    standard_transformations,
    convert_xor,
)
import numpy as np
from scipy import signal
from scipy.integrate import odeint
from typing import Any, Dict, List, Optional, Tuple
import threading
from .base_simulator import BaseSimulator

# Safe parse transformations: no auto_symbol, no implicit multiplication
_SAFE_TRANSFORMATIONS = standard_transformations + (convert_xor,)

# Module-level sympy symbols (shared, immutable)
_x1_sym, _x2_sym, _x3_sym, _u_sym = sp.symbols("x1 x2 x3 u", real=True)

# Allowed symbols for safe expression parsing
_ALLOWED_SYMBOLS: Dict[str, Any] = {
    "x1": _x1_sym,
    "x2": _x2_sym,
    "x3": _x3_sym,
    "u": _u_sym,
    "sin": sp.sin,
    "cos": sp.cos,
    "tan": sp.tan,
    "exp": sp.exp,
    "sqrt": sp.sqrt,
    "log": sp.log,
    "pi": sp.pi,
    "E": sp.E,
    "Abs": sp.Abs,
}


class StateSpaceAnalyzerSimulator(BaseSimulator):
    """
    State Space Analyzer: converts TF/ODE to state-space matrices (A, B, C, D)
    and linearizes nonlinear systems around equilibrium points via Jacobian.
    Returns step-by-step LaTeX derivations for educational display.
    """

    # Linear TF presets: (num_coeffs, den_coeffs, display_name)
    LINEAR_PRESETS: Dict[str, Tuple] = {
        "rc_lowpass": ([1.0], [1.0, 1.0], "RC Low-Pass Filter"),
        "mass_spring": ([1.0], [1.0, 2.0, 1.0], "Critically Damped Mass-Spring"),
        "dc_motor": ([1.0], [1.0, 1.0, 0.0], "DC Motor"),
        "unstable": ([1.0], [1.0, 0.0, -1.0], "Unstable Second-Order System"),
    }

    # Nonlinear presets: (f1_str, f2_str, output_str, display_name)
    NONLINEAR_PRESETS: Dict[str, Tuple] = {
        "pendulum": (
            "x2",
            "-sin(x1) - 0.5*x2 + u",
            "x1",
            "Simple Pendulum with Damping",
        ),
        "van_der_pol": (
            "x2",
            "2*(1 - x1**2)*x2 - x1 + u",
            "x1",
            "Van der Pol Oscillator",
        ),
        "duffing": (
            "x2",
            "-x1 - x1**3 - 0.5*x2 + u",
            "x1",
            "Duffing Oscillator (hard spring)",
        ),
    }

    PARAMETER_SCHEMA: Dict[str, Dict] = {
        "system_type": {
            "type": "select",
            "options": [
                {"value": "linear_tf", "label": "Linear Transfer Function"},
                {"value": "nonlinear", "label": "Nonlinear System"},
            ],
            "default": "linear_tf",
        },
        "preset": {
            "type": "select",
            "options": [
                {"value": "rc_lowpass", "label": "RC Low-Pass  [1/(s+1)]"},
                {"value": "mass_spring", "label": "Mass-Spring  [1/(s²+2s+1)]"},
                {"value": "dc_motor", "label": "DC Motor Position  [1/(s²+s)]"},
                {"value": "unstable", "label": "Unstable  [1/(s²-1)]"},
                {"value": "pendulum", "label": "Simple Pendulum"},
                {"value": "van_der_pol", "label": "Van der Pol Oscillator"},
                {"value": "duffing", "label": "Duffing Oscillator (hard spring)"},
                {"value": "custom", "label": "Custom Expression"},
            ],
            "default": "rc_lowpass",
        },
        "tf_numerator": {
            "type": "expression",
            "default": "1",
        },
        "tf_denominator": {
            "type": "expression",
            "default": "1, 1",
        },
        "canonical_form": {
            "type": "select",
            "options": [
                {"value": "controllable", "label": "Controllable Canonical"},
                {"value": "observable", "label": "Observable Canonical"},
            ],
            "default": "controllable",
        },
        "nl_f1": {
            "type": "expression",
            "default": "x2",
        },
        "nl_f2": {
            "type": "expression",
            "default": "-sin(x1) - 0.5*x2 + u",
        },
        "nl_output": {
            "type": "expression",
            "default": "x1",
        },
        "eq_point_idx": {
            "type": "slider",
            "min": 0,
            "max": 4,
            "step": 1,
            "default": 0,
        },
    }

    DEFAULT_PARAMS: Dict[str, Any] = {
        "system_type": "linear_tf",
        "preset": "rc_lowpass",
        "tf_numerator": "1",
        "tf_denominator": "1, 1",
        "canonical_form": "controllable",
        "nl_f1": "x2",
        "nl_f2": "-sin(x1) - 0.5*x2 + u",
        "nl_output": "x1",
        "eq_point_idx": 0,
    }

    _MAX_EXPR_LEN = 256  # character limit for user-supplied expression strings

    def _validate_expression(self, name: str, value: str) -> str:
        """Clamp expression strings to _MAX_EXPR_LEN and strip whitespace."""
        value = str(value).strip()
        if len(value) > self._MAX_EXPR_LEN:
            raise ValueError(
                f"Expression '{name}' is too long "
                f"(max {self._MAX_EXPR_LEN} characters)."
            )
        return value

    def initialize(self, params: Optional[Dict[str, Any]] = None) -> None:
        """Initialize with merged parameters; validate non-expression params."""
        self.parameters = {**self.DEFAULT_PARAMS, **(params or {})}
        for name, value in list(self.parameters.items()):
            schema = self.PARAMETER_SCHEMA.get(name, {})
            if schema.get("type") == "expression":
                self.parameters[name] = self._validate_expression(name, value)
            else:
                self.parameters[name] = self._validate_param(name, value)
        # Apply preset defaults for expression fields
        preset = self.parameters.get("preset", "rc_lowpass")
        if preset != "custom":
            self._apply_preset_expressions(preset)
        self._initialized = True

    def update_parameter(self, name: str, value: Any) -> Dict[str, Any]:
        """Update a single parameter; expression params stored as strings."""
        if name not in self.parameters:
            return self.get_state()

        schema = self.PARAMETER_SCHEMA.get(name, {})
        if schema.get("type") == "expression":
            self.parameters[name] = self._validate_expression(name, value)
        else:
            self.parameters[name] = self._validate_param(name, value)

        # When preset changes to a non-custom preset, auto-fill expression fields
        if name == "preset" and str(value) != "custom":
            self._apply_preset_expressions(str(value))

        return self.get_state()

    def _apply_preset_expressions(self, preset: str) -> None:
        """Fill expression fields from preset definitions."""
        if preset in self.LINEAR_PRESETS:
            num, den, _ = self.LINEAR_PRESETS[preset]
            self.parameters["tf_numerator"] = ", ".join(str(v) for v in num)
            self.parameters["tf_denominator"] = ", ".join(str(v) for v in den)
            self.parameters["system_type"] = "linear_tf"
        elif preset in self.NONLINEAR_PRESETS:
            f1, f2, out, _ = self.NONLINEAR_PRESETS[preset]
            self.parameters["nl_f1"] = f1
            self.parameters["nl_f2"] = f2
            self.parameters["nl_output"] = out
            self.parameters["system_type"] = "nonlinear"

    def handle_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle custom button actions (e.g., 'compute')."""
        if params:
            for name, value in params.items():
                if name in self.parameters:
                    schema = self.PARAMETER_SCHEMA.get(name, {})
                    if schema.get("type") == "expression":
                        self.parameters[name] = self._validate_expression(name, value)
                    else:
                        self.parameters[name] = self._validate_param(name, value)
        return self.get_state()

    # -------------------------------------------------------------------------
    # Core get_state / get_plots
    # -------------------------------------------------------------------------

    def get_plots(self) -> List[Dict[str, Any]]:
        """Return plots (used by base class API; get_state overrides for efficiency)."""
        data = self._compute()
        return self._build_plots(data)

    def get_state(self) -> Dict[str, Any]:
        """Compute once, build metadata and plots from the same result."""
        data = self._compute()
        return {
            "parameters": self.parameters.copy(),
            "plots": self._build_plots(data),
            "metadata": {
                "simulation_type": "state_space_analyzer",
                "system_type": self.parameters.get("system_type", "linear_tf"),
                "preset": self.parameters.get("preset", "rc_lowpass"),
                "preset_name": data.get("preset_name", ""),
                "latex_steps": data.get("latex_steps", []),
                "matrices": data.get("matrices", {}),
                "eigenvalues": data.get("eigenvalues", {"real": [], "imag": []}),
                "is_stable": data.get("is_stable", None),
                "is_marginal": data.get("is_marginal", False),
                "equilibrium_points": data.get("equilibrium_points", []),
                "selected_eq_idx": data.get("selected_eq_idx", 0),
                "system_order": data.get("system_order", 0),
                "error": data.get("error", None),
            },
        }

    def _build_plots(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Assemble plot list from computed data."""
        plots = [self._eigenvalue_plot(data)]
        sys_type = self.parameters.get("system_type", "linear_tf")
        if sys_type == "linear_tf" and data.get("A") is not None:
            plots.append(self._step_response_plot(data))
        elif sys_type == "nonlinear" and data.get("A") is not None:
            plots.append(self._phase_portrait_plot(data))
        return plots

    # -------------------------------------------------------------------------
    # Main computation dispatcher
    # -------------------------------------------------------------------------

    def _compute(self) -> Dict[str, Any]:
        """Dispatch to linear or nonlinear computation; wrap errors gracefully."""
        try:
            if self.parameters.get("system_type") == "nonlinear":
                return self._compute_nonlinear()
            else:
                return self._compute_linear()
        except Exception as exc:
            err_msg = str(exc)[:200]
            return {
                "error": err_msg,
                "latex_steps": [
                    {
                        "title": "Computation Error",
                        "latex": "\\text{{Error: }} " + str(sp.latex(sp.Symbol(err_msg.replace(' ', '\\_')))),
                        "explanation": err_msg,
                    }
                ],
                "matrices": {},
                "eigenvalues": {"real": [], "imag": []},
                "is_stable": None,
                "equilibrium_points": [],
                "selected_eq_idx": 0,
                "system_order": 0,
                "preset_name": "",
                "A": None,
            }

    # -------------------------------------------------------------------------
    # Linear TF path
    # -------------------------------------------------------------------------

    def _parse_tf_coefficients(self, expr_str: str) -> List[float]:
        """Parse '1, 2, 3' or '1 2 3' into [1.0, 2.0, 3.0]."""
        expr_str = expr_str.replace(";", ",")
        parts = [p.strip() for p in expr_str.replace(",", " ").split()]
        if not parts:
            raise ValueError("Empty coefficient string")
        return [float(p) for p in parts if p]

    def _compute_linear(self) -> Dict[str, Any]:
        """Convert TF to state-space via scipy; build LaTeX derivation steps."""
        preset = self.parameters.get("preset", "rc_lowpass")
        canonical = self.parameters.get("canonical_form", "controllable")

        if preset in self.LINEAR_PRESETS:
            num, den, preset_name = self.LINEAR_PRESETS[preset]
            num = list(num)
            den = list(den)
        else:
            num = self._parse_tf_coefficients(self.parameters.get("tf_numerator", "1"))
            den = self._parse_tf_coefficients(
                self.parameters.get("tf_denominator", "1, 1")
            )
            preset_name = "Custom Transfer Function"

        if len(den) < 2:
            raise ValueError("Denominator must have at least 2 coefficients (order ≥ 1)")
        if abs(den[0]) < 1e-14:
            raise ValueError("Leading denominator coefficient cannot be zero")

        # Normalize so leading coefficient = 1
        a0 = float(den[0])
        num_n = [float(v) / a0 for v in num]
        den_n = [float(v) / a0 for v in den]

        # scipy tf2ss
        A, B, C, D = signal.tf2ss(num_n, den_n)

        # Observable canonical: transpose A, swap B↔Cᵀ
        if canonical == "observable":
            A_oc = A.T.copy()
            B_oc = C.T.copy()
            C_oc = B.T.copy()
            A, B, C = A_oc, B_oc, C_oc

        n = A.shape[0]
        eigenvalues = np.linalg.eigvals(A)
        is_stable = bool(np.all(eigenvalues.real < -1e-10))
        is_marginal = bool(
            np.all(eigenvalues.real <= 1e-10) and not is_stable
        )

        latex_steps = self._build_linear_latex(
            num_n, den_n, A, B, C, D, eigenvalues, canonical, n, is_marginal
        )

        return {
            "A": A.tolist(),
            "B": B.tolist(),
            "C": C.tolist(),
            "D": D.tolist(),
            "eigenvalues": {
                "real": eigenvalues.real.tolist(),
                "imag": eigenvalues.imag.tolist(),
            },
            "is_stable": is_stable,
            "is_marginal": is_marginal,
            "latex_steps": latex_steps,
            "matrices": {
                "A": A.tolist(),
                "B": B.tolist(),
                "C": C.tolist(),
                "D": D.tolist(),
            },
            "equilibrium_points": [],
            "selected_eq_idx": 0,
            "system_order": n,
            "preset_name": preset_name,
            "num_n": num_n,
            "den_n": den_n,
        }

    def _build_linear_latex(
        self,
        num: List[float],
        den: List[float],
        A: np.ndarray,
        B: np.ndarray,
        C: np.ndarray,
        D: np.ndarray,
        eigenvalues: np.ndarray,
        canonical: str,
        n: int,
        is_marginal: bool = False,
    ) -> List[Dict[str, str]]:
        """Generate LaTeX derivation steps for TF → state-space conversion."""
        steps = []

        # Step 1: Transfer function
        num_latex = self._poly_to_latex(num, "s")
        den_latex = self._poly_to_latex(den, "s")
        steps.append({
            "title": "① Transfer Function",
            "latex": f"H(s) = \\frac{{{num_latex}}}{{{den_latex}}}",
            "explanation": (
                "The transfer function H(s) = Y(s)/U(s) relates Laplace-domain "
                "input U(s) to output Y(s), assuming zero initial conditions."
            ),
        })

        # Step 2: State variables
        x_labels = ", ".join(f"x_{i+1}" for i in range(n))
        xdot_labels = ", ".join(f"\\dot{{x}}_{i+1}" for i in range(n))
        steps.append({
            "title": "② Define State Variables",
            "latex": (
                f"\\mathbf{{x}}(t) = \\begin{{bmatrix}} {x_labels.replace(',', ' &')} \\end{{bmatrix}}^{{\\!T}}"
            ),
            "explanation": (
                f"An order-{n} system requires {n} state variables. "
                "In the phase-variable (companion) form, x₁ is the output "
                "and each subsequent state is its derivative."
            ),
        })

        # Step 3: Canonical form explanation
        if canonical == "controllable":
            form_explain = (
                "\\begin{aligned}"
                "&\\text{Controllable canonical (phase-variable) form:} \\\\"
                "&\\text{denominator coefficients populate the last row of } A, "
                "\\text{ column vector } B = [0,\\ldots,0,1]^T"
                "\\end{aligned}"
            )
        else:
            form_explain = (
                "\\begin{aligned}"
                "&\\text{Observable canonical form:} \\\\"
                "&\\text{denominator coefficients populate the last column of } A; \\\\"
                "&\\text{input vector } B = [0,\\ldots,0,1]^T; "
                "\\text{ output row } C = [1, 0, \\ldots, 0]"
                "\\end{aligned}"
            )
        steps.append({
            "title": f"③ {('Controllable' if canonical == 'controllable' else 'Observable')} Canonical Form",
            "latex": form_explain,
            "explanation": (
                "Controllable form ensures every state is reachable from the input. "
                "Observable form ensures every state affects the output. "
                "Both are equivalent realizations of H(s)."
            ),
        })

        # Step 4: State-space matrices
        A_lat = self._matrix_to_latex(A)
        B_lat = self._matrix_to_latex(B)
        C_lat = self._matrix_to_latex(C)
        D_val = float(D.flat[0]) if D.size > 0 else 0.0
        D_lat = self._fmt(D_val)
        steps.append({
            "title": "④ State-Space Matrices",
            "latex": (
                f"\\begin{{aligned}}"
                f"A &= {A_lat}, & B &= {B_lat} \\\\"
                f"C &= {C_lat}, & D &= {D_lat}"
                f"\\end{{aligned}}"
            ),
            "explanation": (
                "A: system dynamics matrix (n×n), B: input matrix (n×1), "
                "C: output matrix (1×n), D: feedthrough scalar."
            ),
        })

        # Step 5: State equation
        steps.append({
            "title": "⑤ State Equation",
            "latex": "\\dot{\\mathbf{x}}(t) = A\\,\\mathbf{x}(t) + B\\,u(t)",
            "explanation": (
                "This first-order vector ODE replaces the original nth-order scalar ODE. "
                "It governs how the internal state evolves with time."
            ),
        })

        # Step 6: Output equation
        steps.append({
            "title": "⑥ Output Equation",
            "latex": "y(t) = C\\,\\mathbf{x}(t) + D\\,u(t)",
            "explanation": (
                "Maps the internal state vector to the observable output. "
                "D ≠ 0 indicates direct feedthrough from input to output."
            ),
        })

        # Step 7: Expanded matrix form (for small systems)
        if n <= 3:
            expanded = self._expanded_state_eq_latex(A, B, n)
            steps.append({
                "title": "⑦ Expanded Matrix Form",
                "latex": expanded,
                "explanation": "The full matrix multiplication written out explicitly.",
            })

        # Step 8: Eigenvalues / poles
        eig_parts = []
        for r, im in zip(eigenvalues.real, eigenvalues.imag):
            if abs(im) < 1e-10:
                eig_parts.append(f"\\lambda = {r:.4f}")
            elif im > 0:
                eig_parts.append(f"\\lambda = {r:.4f} + {im:.4f}j")
            else:
                eig_parts.append(f"\\lambda = {r:.4f} - {abs(im):.4f}j")

        all_negative = np.all(eigenvalues.real < -1e-10)
        if all_negative:
            stability_note = (
                "\\text{Asymptotically stable — all eigenvalues in open LHP}"
            )
        elif is_marginal:
            stability_note = (
                "\\text{Marginally stable — eigenvalue(s) on } j\\omega"
                "\\text{ axis (bounded but non-decaying response)}"
            )
        else:
            stability_note = (
                "\\text{Unstable — eigenvalue(s) in right half-plane}"
            )

        # DC gain (exact formula) for stable strictly-proper systems
        dc_gain_str = ""
        if all_negative:
            try:
                dc_gain = float(C @ np.linalg.solve(-A, B) + D)
                dc_gain_str = (
                    f" \\\\ &\\text{{DC gain: }} K_{{dc}} = C(-A)^{{-1}}B + D = {dc_gain:.4g}"
                )
            except Exception:
                pass

        eig_latex = (
            "\\begin{aligned}"
            + " \\\\ ".join(f"&{e}" for e in eig_parts)
            + " \\\\ &" + stability_note
            + dc_gain_str
            + "\\end{aligned}"
        )
        steps.append({
            "title": "⑧ Eigenvalues (Poles) & Stability",
            "latex": eig_latex,
            "explanation": (
                "Eigenvalues of A = poles of H(s). "
                "Asymptotically stable iff all real parts strictly negative. "
                "Marginally stable if purely imaginary poles exist. "
                "DC gain = C(−A)⁻¹B + D for stable systems."
            ),
        })

        return steps

    # -------------------------------------------------------------------------
    # Nonlinear path
    # -------------------------------------------------------------------------

    def _safe_parse_expr(self, expr_str: str) -> sp.Expr:
        """Parse a sympy expression with whitelisted symbols only.

        Uses a restricted transformation set (no auto_symbol) so unrecognised
        names raise NameError instead of silently becoming free symbols, which
        would bypass the whitelist.
        """
        expr_str = expr_str.replace("^", "**")
        try:
            return sp.parse_expr(
                expr_str,
                local_dict=_ALLOWED_SYMBOLS,
                transformations=_SAFE_TRANSFORMATIONS,
            )
        except Exception as exc:
            raise ValueError(f"Cannot parse '{expr_str}': {exc}") from exc

    def _compute_nonlinear(self) -> Dict[str, Any]:
        """Linearize nonlinear system around equilibrium via Jacobian."""
        preset = self.parameters.get("preset", "pendulum")
        eq_idx = int(self.parameters.get("eq_point_idx", 0))

        if preset in self.NONLINEAR_PRESETS:
            f1_str, f2_str, out_str, preset_name = self.NONLINEAR_PRESETS[preset]
        else:
            f1_str = self.parameters.get("nl_f1", "x2")
            f2_str = self.parameters.get("nl_f2", "-x1")
            out_str = self.parameters.get("nl_output", "x1")
            preset_name = "Custom Nonlinear System"

        x1, x2, u = _x1_sym, _x2_sym, _u_sym

        f1_expr = self._safe_parse_expr(f1_str)
        f2_expr = self._safe_parse_expr(f2_str)
        g_expr = self._safe_parse_expr(out_str)

        # Lambdify once here — reused by _phase_portrait_plot via the data dict
        f1_func = sp.lambdify([x1, x2, u], f1_expr, modules="numpy")
        f2_func = sp.lambdify([x1, x2, u], f2_expr, modules="numpy")

        latex_steps: List[Dict[str, str]] = []

        # Step 1: Show original system
        f1_lat = sp.latex(f1_expr)
        f2_lat = sp.latex(f2_expr)
        g_lat = sp.latex(g_expr)
        latex_steps.append({
            "title": "① Nonlinear State Equations",
            "latex": (
                f"\\begin{{aligned}}"
                f"\\dot{{x}}_1 &= {f1_lat} \\\\"
                f"\\dot{{x}}_2 &= {f2_lat} \\\\"
                f"y &= {g_lat}"
                f"\\end{{aligned}}"
            ),
            "explanation": (
                "The nonlinear state equations describe how each state variable evolves. "
                "Linearization will approximate this with a linear system near an operating point."
            ),
        })

        # Step 2: Equilibrium condition
        f1_u0 = f1_expr.subs(u, 0)
        f2_u0 = f2_expr.subs(u, 0)
        latex_steps.append({
            "title": "② Equilibrium Condition (ẋ = 0, u = 0)",
            "latex": (
                f"\\begin{{aligned}}"
                f"f_1(\\bar{{x}}_1, \\bar{{x}}_2, 0) &= {sp.latex(f1_u0)} = 0 \\\\"
                f"f_2(\\bar{{x}}_1, \\bar{{x}}_2, 0) &= {sp.latex(f2_u0)} = 0"
                f"\\end{{aligned}}"
            ),
            "explanation": (
                "Equilibria are steady-state points where ẋ = 0. "
                "We set u = 0 (unforced system) and solve simultaneously."
            ),
        })

        # Solve for equilibria
        real_solutions = self._find_equilibria(f1_u0, f2_u0, x1, x2)

        # Format equilibrium display
        if real_solutions:
            eq_display_parts = []
            for i, (ex1, ex2) in enumerate(real_solutions):
                eq_display_parts.append(
                    f"(\\bar{{x}}_1,\\, \\bar{{x}}_2)_{{{i+1}}} &= "
                    f"({ex1:.4f},\\; {ex2:.4f})"
                )
            eq_display = (
                "\\begin{aligned}"
                + " \\\\ ".join(eq_display_parts)
                + "\\end{aligned}"
            )
        else:
            eq_display = "\\text{No real equilibria found — using } (0, 0)"
            real_solutions = [(0.0, 0.0)]

        latex_steps.append({
            "title": f"③ Equilibrium Points ({len(real_solutions)} found)",
            "latex": eq_display,
            "explanation": (
                "Each equilibrium represents a constant operating condition. "
                "Use the slider to select which equilibrium to linearize around."
            ),
        })

        # Select equilibrium
        sel_idx = min(eq_idx, len(real_solutions) - 1)
        x1_eq, x2_eq = real_solutions[sel_idx]

        latex_steps.append({
            "title": f"④ Selected Equilibrium #{sel_idx + 1}",
            "latex": (
                f"\\bar{{x}}_1 = {x1_eq:.4f}, \\quad "
                f"\\bar{{x}}_2 = {x2_eq:.4f}, \\quad \\bar{{u}} = 0"
            ),
            "explanation": "Linearization will produce a local approximation valid near this point.",
        })

        # Step 5: Jacobian (symbolic)
        f_vec = sp.Matrix([f1_expr, f2_expr])
        x_vec_sym = sp.Matrix([x1, x2])
        u_vec_sym = sp.Matrix([u])

        A_sym = f_vec.jacobian(x_vec_sym)
        B_sym = f_vec.jacobian(u_vec_sym)

        latex_steps.append({
            "title": "⑤ Jacobian Matrix A (Symbolic)",
            "latex": (
                "A = \\left.\\frac{\\partial \\mathbf{f}}{\\partial \\mathbf{x}}"
                f"\\right|_{{\\bar{{\\mathbf{{x}}}}}} = {sp.latex(A_sym)}"
            ),
            "explanation": (
                "The Jacobian is the matrix of all first-order partial derivatives "
                "of f = [f₁, f₂]ᵀ with respect to x = [x₁, x₂]ᵀ."
            ),
        })

        latex_steps.append({
            "title": "⑥ Input Jacobian B (Symbolic)",
            "latex": (
                "B = \\left.\\frac{\\partial \\mathbf{f}}{\\partial u}"
                f"\\right|_{{\\bar{{\\mathbf{{x}}}}}} = {sp.latex(B_sym)}"
            ),
            "explanation": "B describes how the input u enters each state equation.",
        })

        # Evaluate at equilibrium
        subs_dict = {x1: x1_eq, x2: x2_eq, u: 0}
        A_num_sym = A_sym.subs(subs_dict).evalf()
        B_num_sym = B_sym.subs(subs_dict).evalf()

        g_vec = sp.Matrix([g_expr])
        C_sym = g_vec.jacobian(x_vec_sym)
        D_sym = g_vec.jacobian(u_vec_sym)
        C_num_sym = C_sym.subs(subs_dict).evalf()
        D_num_sym = D_sym.subs(subs_dict).evalf()

        # Convert to numpy arrays
        def _to_np(m: sp.Matrix) -> np.ndarray:
            return np.array([[complex(v).real for v in row] for row in m.tolist()], dtype=float)

        A_np = _to_np(A_num_sym)
        B_np = _to_np(B_num_sym)
        C_np = _to_np(C_num_sym)
        D_np = _to_np(D_num_sym)

        A_eval_lat = self._matrix_to_latex(A_np)
        B_eval_lat = self._matrix_to_latex(B_np)
        C_eval_lat = self._matrix_to_latex(C_np)

        latex_steps.append({
            "title": "⑦ Evaluated Matrices at Equilibrium",
            "latex": (
                f"A = {A_eval_lat}, \\quad B = {B_eval_lat}, \\quad C = {C_eval_lat}"
            ),
            "explanation": (
                "Substituting the equilibrium coordinates into the Jacobian gives "
                "the numeric A, B, C matrices of the linearized system."
            ),
        })

        # Linearized system equations
        latex_steps.append({
            "title": "⑧ Linearized State-Space System",
            "latex": (
                "\\begin{aligned}"
                "\\delta\\dot{\\mathbf{x}} &= A\\,\\delta\\mathbf{x} + B\\,\\delta u \\\\"
                "\\delta y &= C\\,\\delta\\mathbf{x} + D\\,\\delta u"
                "\\end{aligned}"
            ),
            "explanation": (
                "The deviation variables δx = x − x̄, δu = u − ū describe "
                "small perturbations around the equilibrium. This linear system "
                "approximates the nonlinear dynamics locally."
            ),
        })

        # Stability
        eigenvalues = np.linalg.eigvals(A_np)
        is_stable = bool(np.all(eigenvalues.real < -1e-10))
        is_marginal_nl = bool(
            np.all(eigenvalues.real <= 1e-10) and not is_stable
        )

        eig_parts = []
        for r, im in zip(eigenvalues.real, eigenvalues.imag):
            if abs(im) < 1e-10:
                eig_parts.append(f"\\lambda_{{{len(eig_parts)+1}}} = {r:.4f}")
            elif im > 0:
                eig_parts.append(f"\\lambda_{{{len(eig_parts)+1}}} = {r:.4f} + {im:.4f}j")
            else:
                eig_parts.append(f"\\lambda_{{{len(eig_parts)+1}}} = {r:.4f} - {abs(im):.4f}j")

        if is_stable:
            stability_note = (
                "\\text{Linearization is asymptotically } \\mathbf{stable}"
                "\\text{ at this equilibrium}"
            )
        elif is_marginal_nl:
            stability_note = (
                "\\text{Linearization is } \\mathbf{marginally stable}"
                "\\text{ — non-linear analysis needed}"
            )
        else:
            stability_note = (
                "\\text{Linearization is } \\mathbf{unstable}"
                "\\text{ at this equilibrium}"
            )
        eig_latex_nl = (
            "\\begin{aligned}"
            + " \\\\ ".join(f"&{e}" for e in eig_parts)
            + " \\\\ &" + stability_note
            + "\\end{aligned}"
        )
        latex_steps.append({
            "title": "⑨ Eigenvalues & Local Stability",
            "latex": eig_latex_nl,
            "explanation": (
                "Stability of the linearized system predicts local behavior of the "
                "nonlinear system near this equilibrium (Hartman–Grobman theorem)."
            ),
        })

        return {
            "A": A_np.tolist(),
            "B": B_np.tolist(),
            "C": C_np.tolist(),
            "D": D_np.tolist(),
            "eigenvalues": {
                "real": eigenvalues.real.tolist(),
                "imag": eigenvalues.imag.tolist(),
            },
            "is_stable": is_stable,
            "is_marginal": is_marginal_nl,
            "latex_steps": latex_steps,
            "matrices": {
                "A": A_np.tolist(),
                "B": B_np.tolist(),
                "C": C_np.tolist(),
                "D": D_np.tolist(),
            },
            "equilibrium_points": [(float(x), float(y)) for x, y in real_solutions],
            "selected_eq_idx": sel_idx,
            "system_order": 2,
            "preset_name": preset_name,
            "f1_str": f1_str,
            "f2_str": f2_str,
            "x1_eq": float(x1_eq),
            "x2_eq": float(x2_eq),
            # Pass lambdified callables so _phase_portrait_plot does not re-parse
            "_f1_func": f1_func,
            "_f2_func": f2_func,
        }

    def _find_equilibria(
        self,
        f1: sp.Expr,
        f2: sp.Expr,
        x1: sp.Symbol,
        x2: sp.Symbol,
    ) -> List[Tuple[float, float]]:
        """Solve f1=0, f2=0; return real numeric solutions.

        Strategy:
        1. Try symbolic sp.solve in a background thread with a 6-second timeout.
           Using a thread (not process) avoids macOS spawn overhead.  The thread
           runs as daemon so it does not block server shutdown if it outlives the
           timeout window.
        2. If symbolic solve times out, fall back to scipy.optimize.fsolve on a
           grid of initial guesses to recover approximate equilibria numerically.
        """
        symbolic_result: List[Dict] = []
        solved = threading.Event()

        def _sympy_solve():
            try:
                symbolic_result.extend(sp.solve([f1, f2], [x1, x2], dict=True))
            except Exception:
                pass
            solved.set()

        t = threading.Thread(target=_sympy_solve, daemon=True)
        t.start()
        symbolic_ok = solved.wait(timeout=6)

        if symbolic_ok and symbolic_result:
            real_sols: List[Tuple[float, float]] = []
            for sol in symbolic_result:
                v1 = complex(sol.get(x1, 0))
                v2 = complex(sol.get(x2, 0))
                if abs(v1.imag) < 1e-6 and abs(v2.imag) < 1e-6:
                    real_sols.append((float(v1.real), float(v2.real)))
            if real_sols:
                return real_sols[:5]

        # Numerical fallback via scipy.optimize.fsolve on a grid of ICs
        try:
            from scipy.optimize import fsolve
            f1_func = sp.lambdify([x1, x2], f1, modules="numpy")
            f2_func = sp.lambdify([x1, x2], f2, modules="numpy")

            def system(z):
                return [float(f1_func(z[0], z[1])), float(f2_func(z[0], z[1]))]

            grid = np.linspace(-np.pi, np.pi, 5)
            found: List[Tuple[float, float]] = []
            seen: List[Tuple[float, float]] = []
            for gx in grid:
                for gy in grid:
                    try:
                        sol_num, _, ier, _ = fsolve(system, [gx, gy], full_output=True)
                        if ier == 1:
                            vx, vy = float(sol_num[0]), float(sol_num[1])
                            # Deduplicate (within 0.01 tolerance)
                            if all(
                                abs(vx - sx) + abs(vy - sy) > 0.01
                                for sx, sy in seen
                            ):
                                res = system([vx, vy])
                                if abs(res[0]) < 1e-6 and abs(res[1]) < 1e-6:
                                    seen.append((vx, vy))
                                    found.append((vx, vy))
                    except Exception:
                        pass
            return found[:5] if found else [(0.0, 0.0)]
        except Exception:
            return [(0.0, 0.0)]

    # -------------------------------------------------------------------------
    # LaTeX helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _fmt(val: float, spec: str = ".4g") -> str:
        """Format a float with given spec; handle near-zero."""
        if abs(val) < 1e-12:
            return "0"
        return format(val, spec)

    def _matrix_to_latex(self, matrix, spec: str = ".4g") -> str:
        """Convert a 2D numpy array to a LaTeX bmatrix string."""
        if matrix is None:
            return "\\begin{bmatrix}\\end{bmatrix}"
        arr = np.atleast_2d(np.array(matrix, dtype=float))
        rows = []
        for row in arr:
            rows.append(" & ".join(self._fmt(v, spec) for v in row))
        body = " \\\\ ".join(rows)
        return f"\\begin{{bmatrix}} {body} \\end{{bmatrix}}"

    @staticmethod
    def _poly_to_latex(coeffs: List[float], var: str) -> str:
        """Convert polynomial coefficients [a_n, ..., a_0] to LaTeX string."""
        n = len(coeffs) - 1
        terms: List[str] = []
        for i, c in enumerate(coeffs):
            power = n - i
            if abs(c) < 1e-12:
                continue
            c_abs = abs(c)
            sign = "-" if c < 0 else ("+" if terms else "")
            sign_prefix = "-" if c < 0 else ""
            if power == 0:
                term = f"{c_abs:.4g}"
            elif power == 1:
                coef_str = "" if abs(c_abs - 1) < 1e-12 else f"{c_abs:.4g}"
                term = f"{coef_str}{var}"
            else:
                coef_str = "" if abs(c_abs - 1) < 1e-12 else f"{c_abs:.4g}"
                term = f"{coef_str}{var}^{{{power}}}"
            if terms:
                terms.append(("- " if c < 0 else "+ ") + term)
            else:
                terms.append(sign_prefix + term)
        return " ".join(terms) if terms else "0"

    def _expanded_state_eq_latex(self, A: np.ndarray, B: np.ndarray, n: int) -> str:
        """Build expanded ẋ = Ax + Bu matrix equation for small n."""
        xdot = "\\begin{bmatrix}" + " \\\\ ".join(f"\\dot{{x}}_{i+1}" for i in range(n)) + "\\end{bmatrix}"
        x_v = "\\begin{bmatrix}" + " \\\\ ".join(f"x_{i+1}" for i in range(n)) + "\\end{bmatrix}"
        A_lat = self._matrix_to_latex(A)
        B_lat = self._matrix_to_latex(B)
        return f"{xdot} = {A_lat} {x_v} + {B_lat} u"

    # -------------------------------------------------------------------------
    # Plots
    # -------------------------------------------------------------------------

    def _eigenvalue_plot(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Eigenvalue map in the complex plane."""
        eig_real = data.get("eigenvalues", {}).get("real", [])
        eig_imag = data.get("eigenvalues", {}).get("imag", [])
        is_stable = data.get("is_stable", None)

        marker_color = (
            "#10b981" if is_stable is True
            else "#ef4444" if is_stable is False
            else "#94a3b8"
        )

        # Stability boundary line: extend to cover the data range
        if eig_real:
            y_max = max(3.0, max(abs(v) for v in eig_imag) * 1.5 + 1)
        else:
            y_max = 3.0

        traces = [
            {
                "x": [0.0, 0.0],
                "y": [-y_max, y_max],
                "type": "scatter",
                "mode": "lines",
                "name": "jω axis (stability boundary)",
                "line": {"color": "rgba(148,163,184,0.5)", "width": 1.5, "dash": "dash"},
                "hoverinfo": "skip",
                "showlegend": True,
            }
        ]

        if eig_real:
            traces.append({
                "x": eig_real,
                "y": eig_imag,
                "type": "scatter",
                "mode": "markers",
                "name": "Eigenvalues (Poles)",
                "marker": {
                    "symbol": "x",
                    "size": 16,
                    "color": marker_color,
                    "line": {"width": 3, "color": marker_color},
                },
                "hovertemplate": "Re: %{x:.4f}<br>Im: %{y:.4f}<extra>Pole</extra>",
            })

        stability_str = (
            " — Stable" if is_stable is True
            else " — Unstable" if is_stable is False
            else ""
        )
        uirev = (
            f"eig-{self.parameters.get('system_type')}"
            f"-{self.parameters.get('preset')}"
            f"-{self.parameters.get('eq_point_idx', 0)}"
            f"-{self.parameters.get('tf_denominator', '')}"
        )

        return {
            "id": "eigenvalue_map",
            "title": f"Eigenvalue Map{stability_str}",
            "data": traces,
            "layout": {
                "xaxis": {
                    "title": "Real Part",
                    "gridcolor": "rgba(148,163,184,0.1)",
                    "zerolinecolor": "rgba(148,163,184,0.3)",
                    "color": "#f1f5f9",
                    "autorange": True,
                },
                "yaxis": {
                    "title": "Imaginary Part",
                    "gridcolor": "rgba(148,163,184,0.1)",
                    "zerolinecolor": "rgba(148,163,184,0.3)",
                    "color": "#f1f5f9",
                    "autorange": True,
                },
                "paper_bgcolor": "rgba(0,0,0,0)",
                "plot_bgcolor": "rgba(0,0,0,0)",
                "font": {"family": "Inter, sans-serif", "size": 12, "color": "#f1f5f9"},
                "margin": {"t": 45, "r": 25, "b": 55, "l": 60},
                "showlegend": True,
                "legend": {"font": {"color": "#94a3b8"}, "bgcolor": "rgba(0,0,0,0.3)"},
                "uirevision": uirev,
                "annotations": [
                    {
                        "x": 0.02, "y": 0.97,
                        "xref": "paper", "yref": "paper",
                        "text": "← Stable",
                        "showarrow": False,
                        "font": {"color": "#10b981", "size": 11},
                        "xanchor": "left",
                    },
                    {
                        "x": 0.98, "y": 0.97,
                        "xref": "paper", "yref": "paper",
                        "text": "Unstable →",
                        "showarrow": False,
                        "font": {"color": "#ef4444", "size": 11},
                        "xanchor": "right",
                    },
                ],
            },
        }

    def _step_response_plot(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Compute and plot step response using scipy.signal.step."""
        try:
            A = np.array(data["A"], dtype=float)
            B = np.array(data["B"], dtype=float)
            C = np.array(data["C"], dtype=float)
            D = np.array(data["D"], dtype=float)

            sys_ss = signal.StateSpace(A, B, C, D)
            t = np.linspace(0, 15, 1000)
            t_out, y_out = signal.step(sys_ss, T=t)
            y_flat = y_out.flatten()

            # Clip diverging responses for display
            clip_mag = 200.0
            y_clipped = np.clip(y_flat, -clip_mag, clip_mag)

            traces = [{
                "x": t_out.tolist(),
                "y": y_clipped.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": "Step Response y(t)",
                "line": {"color": "#3b82f6", "width": 2.5},
                "hovertemplate": "t = %{x:.3f} s<br>y = %{y:.4f}<extra></extra>",
            }]

            # Steady-state reference for stable systems — use exact DC gain formula
            is_stable = data.get("is_stable", False)
            if is_stable:
                try:
                    A_ss = np.array(data["A"], dtype=float)
                    B_ss = np.array(data["B"], dtype=float)
                    C_ss = np.array(data["C"], dtype=float)
                    D_ss = np.array(data["D"], dtype=float)
                    ss = float(C_ss @ np.linalg.solve(-A_ss, B_ss) + D_ss)
                except Exception:
                    ss = float(y_clipped[-20:].mean()) if len(y_clipped) > 0 else 0.0
                traces.append({
                    "x": [0, float(t_out[-1])],
                    "y": [ss, ss],
                    "type": "scatter",
                    "mode": "lines",
                    "name": f"Steady-state = {ss:.4g}",
                    "line": {"color": "#10b981", "width": 1.5, "dash": "dash"},
                    "hoverinfo": "skip",
                })

            uirev = f"step-{self.parameters.get('system_type')}-{self.parameters.get('preset')}-{self.parameters.get('canonical_form')}"

            return {
                "id": "step_response",
                "title": "Step Response",
                "data": traces,
                "layout": {
                    "xaxis": {
                        "title": "Time [s]",
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
                    "paper_bgcolor": "rgba(0,0,0,0)",
                    "plot_bgcolor": "rgba(0,0,0,0)",
                    "font": {"family": "Inter, sans-serif", "size": 12, "color": "#f1f5f9"},
                    "margin": {"t": 45, "r": 25, "b": 55, "l": 60},
                    "showlegend": True,
                    "legend": {"font": {"color": "#94a3b8"}, "bgcolor": "rgba(0,0,0,0.3)"},
                    "uirevision": uirev,
                },
            }

        except Exception as exc:
            return {
                "id": "step_response",
                "title": "Step Response (N/A)",
                "data": [],
                "layout": {
                    "paper_bgcolor": "rgba(0,0,0,0)",
                    "plot_bgcolor": "rgba(0,0,0,0)",
                    "annotations": [{
                        "text": f"Cannot compute step response: {str(exc)[:100]}",
                        "xref": "paper", "yref": "paper",
                        "x": 0.5, "y": 0.5,
                        "showarrow": False,
                        "font": {"color": "#94a3b8", "size": 13},
                    }],
                },
            }

    def _phase_portrait_plot(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Phase portrait with sample trajectories around the equilibrium."""
        f1_str = data.get("f1_str", self.parameters.get("nl_f1", "x2"))
        f2_str = data.get("f2_str", self.parameters.get("nl_f2", "-x1"))
        x1_eq = float(data.get("x1_eq", 0.0))
        x2_eq = float(data.get("x2_eq", 0.0))

        # Reuse lambdified callables computed in _compute_nonlinear if available
        f1_func = data.get("_f1_func")
        f2_func = data.get("_f2_func")
        if f1_func is None or f2_func is None:
            # Fallback: re-parse only if callables were not passed through
            x1_sym, x2_sym, u_sym = _x1_sym, _x2_sym, _u_sym
            try:
                f1_expr = self._safe_parse_expr(f1_str)
                f2_expr = self._safe_parse_expr(f2_str)
                f1_func = sp.lambdify([x1_sym, x2_sym, u_sym], f1_expr, modules="numpy")
                f2_func = sp.lambdify([x1_sym, x2_sym, u_sym], f2_expr, modules="numpy")
            except Exception:
                f1_func = lambda x1, x2, u: x2  # noqa: E731
                f2_func = lambda x1, x2, u: -x1  # noqa: E731

        def ode_system(state, _t):
            try:
                dx1 = float(f1_func(state[0], state[1], 0))
                dx2 = float(f2_func(state[0], state[1], 0))
                if not (np.isfinite(dx1) and np.isfinite(dx2)):
                    return [0.0, 0.0]
                return [dx1, dx2]
            except Exception:
                return [0.0, 0.0]

        t_span = np.linspace(0, 8, 400)
        r = 2.5
        angles = np.linspace(0, 2 * np.pi, 8, endpoint=False)
        ics = [[x1_eq + r * np.cos(a), x2_eq + r * np.sin(a)] for a in angles]

        traj_colors = [
            "#14b8a6", "#3b82f6", "#8b5cf6", "#f59e0b",
            "#ec4899", "#06b6d4", "#10b981", "#64748b",
        ]

        traces = []
        for i, ic in enumerate(ics):
            try:
                sol = odeint(ode_system, ic, t_span, rtol=1e-5, atol=1e-7)
                x1_t, x2_t = sol[:, 0], sol[:, 1]
                mask = np.isfinite(x1_t) & np.isfinite(x2_t) & (np.abs(x1_t) < 25) & (np.abs(x2_t) < 25)
                if mask.sum() > 20:
                    traces.append({
                        "x": x1_t[mask].tolist(),
                        "y": x2_t[mask].tolist(),
                        "type": "scatter",
                        "mode": "lines",
                        "line": {"color": traj_colors[i % len(traj_colors)], "width": 1.8},
                        "opacity": 0.8,
                        "hovertemplate": "x₁=%{x:.3f}<br>x₂=%{y:.3f}<extra></extra>",
                        "showlegend": False,
                    })
            except Exception:
                pass

        # Mark all equilibrium points
        eq_pts = data.get("equilibrium_points", [(x1_eq, x2_eq)])
        sel_idx = data.get("selected_eq_idx", 0)
        for i, (ex1, ex2) in enumerate(eq_pts):
            is_sel = i == sel_idx
            traces.append({
                "x": [ex1],
                "y": [ex2],
                "type": "scatter",
                "mode": "markers",
                "name": f"Eq. #{i+1}" + (" (selected)" if is_sel else ""),
                "marker": {
                    "symbol": "circle",
                    "size": 14 if is_sel else 10,
                    "color": "#ef4444" if is_sel else "#94a3b8",
                    "line": {"width": 2, "color": "white"},
                },
                "hovertemplate": f"Equilibrium #{i+1}<br>x₁={ex1:.4f}<br>x₂={ex2:.4f}<extra></extra>",
            })

        uirev = f"phase-{self.parameters.get('preset')}-{self.parameters.get('eq_point_idx', 0)}-{self.parameters.get('nl_f1', '')}"

        margin = r * 1.3
        return {
            "id": "phase_portrait",
            "title": f"Phase Portrait around Equilibrium #{sel_idx + 1}",
            "data": traces,
            "layout": {
                "xaxis": {
                    "title": "x₁",
                    "gridcolor": "rgba(148,163,184,0.1)",
                    "zerolinecolor": "rgba(148,163,184,0.3)",
                    "color": "#f1f5f9",
                    "range": [x1_eq - margin, x1_eq + margin],
                },
                "yaxis": {
                    "title": "x₂",
                    "gridcolor": "rgba(148,163,184,0.1)",
                    "zerolinecolor": "rgba(148,163,184,0.3)",
                    "color": "#f1f5f9",
                    "range": [x2_eq - margin, x2_eq + margin],
                },
                "paper_bgcolor": "rgba(0,0,0,0)",
                "plot_bgcolor": "rgba(0,0,0,0)",
                "font": {"family": "Inter, sans-serif", "size": 12, "color": "#f1f5f9"},
                "margin": {"t": 45, "r": 25, "b": 55, "l": 60},
                "showlegend": True,
                "legend": {"font": {"color": "#94a3b8"}, "bgcolor": "rgba(0,0,0,0.3)"},
                "uirevision": uirev,
            },
        }
