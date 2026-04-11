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
from core.ss_utils import (
    tf_proper_decomposition,
    tf2ss_canonical,
    mimo_tf2ss,
    minreal,
    controllability_gramian,
    observability_gramian,
    transmission_zeros,
    ss2tf_mimo,
    convert_canonical,
)

# Safe parse transformations: no auto_symbol, no implicit multiplication
_SAFE_TRANSFORMATIONS = standard_transformations + (convert_xor,)

# Module-level sympy symbols (shared, immutable)
_x1_sym, _x2_sym, _x3_sym, _u_sym = sp.symbols("x1 x2 x3 u", real=True)
# Extended symbols for N×M×P nonlinear mode
_x_syms = sp.symbols("x1:7", real=True)   # x1, x2, x3, x4, x5, x6
_u_syms = sp.symbols("u1:5", real=True)   # u1, u2, u3, u4

# Allowed symbols for safe expression parsing
_ALLOWED_SYMBOLS: Dict[str, Any] = {
    "x1": _x_syms[0],
    "x2": _x_syms[1],
    "x3": _x_syms[2],
    "x4": _x_syms[3],
    "x5": _x_syms[4],
    "x6": _x_syms[5],
    "u": _u_sym,        # Keep legacy single u for backward compat
    "u1": _u_syms[0],
    "u2": _u_syms[1],
    "u3": _u_syms[2],
    "u4": _u_syms[3],
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

    # Nonlinear presets: generalized N×M×P format
    NONLINEAR_PRESETS_V2: Dict[str, Dict[str, Any]] = {
        # Existing (n=2, m=1, p=1)
        "pendulum": {
            "n": 2, "m": 1, "p": 1,
            "f": ["x2", "-sin(x1) - 0.5*x2 + u1"],
            "h": ["x1"],
            "name": "Simple Pendulum with Damping",
        },
        "van_der_pol": {
            "n": 2, "m": 1, "p": 1,
            "f": ["x2", "2*(1 - x1**2)*x2 - x1 + u1"],
            "h": ["x1"],
            "name": "Van der Pol Oscillator",
        },
        "duffing": {
            "n": 2, "m": 1, "p": 1,
            "f": ["x2", "-x1 - x1**3 - 0.5*x2 + u1"],
            "h": ["x1"],
            "name": "Duffing Oscillator (hard spring)",
        },
        # New (n=4, m=1, p=2) — inverted pendulum on cart
        "inverted_pendulum": {
            "n": 4, "m": 1, "p": 2,
            "f": [
                "x2",
                "(u1 + 0.2*sin(x3)*(0.5*x4**2 - 9.81*cos(x3))) / (1 + 0.2*sin(x3)**2)",
                "x4",
                "(-u1*cos(x3) - 0.2*0.5*x4**2*sin(x3)*cos(x3) - 1.2*9.81*sin(x3)) / (0.5*(1 + 0.2*sin(x3)**2))",
            ],
            "h": ["x1", "x3"],
            "name": "Inverted Pendulum on Cart",
            "eq_hint": [0, 0, 3.14159, 0],
        },
        # New (n=2, m=2, p=2) — MIMO nonlinear
        "coupled_tanks": {
            "n": 2, "m": 2, "p": 2,
            "f": [
                "u1 - 0.6*sqrt(x1 + 0.01)",
                "u2 + 0.6*sqrt(x1 + 0.01) - 0.6*sqrt(x2 + 0.01)",
            ],
            "h": ["x1", "x2"],
            "name": "Coupled Tanks (MIMO)",
            "eq_hint": [-0.01, -0.01],
            "op_hint": [1.0, 1.0],
        },
        # New (n=2, m=0, p=2) — autonomous
        "lotka_volterra": {
            "n": 2, "m": 0, "p": 2,
            "f": ["1.0*x1 - 0.5*x1*x2", "0.2*x1*x2 - 0.5*x2"],
            "h": ["x1", "x2"],
            "name": "Lotka-Volterra Predator-Prey",
        },
    }

    # Legacy compatibility alias
    NONLINEAR_PRESETS: Dict[str, Tuple] = {
        k: (v["f"][0], v["f"][1], v["h"][0], v["name"])
        for k, v in NONLINEAR_PRESETS_V2.items()
        if v["n"] == 2 and v["m"] <= 1 and v["p"] == 1
    }

    # MIMO TF presets: (num_matrix, den_matrix, display_name)
    # Each entry in num/den matrix is a list of polynomial coefficients (highest power first)
    MIMO_TF_PRESETS: Dict[str, Dict[str, Any]] = {
        "mimo_coupled_spring": {
            "name": "Coupled Mass-Spring-Damper (2×2)",
            "p": 2, "m": 2,
            "num": [
                [[1.0], [0.5]],         # G11 = 1/(s²+0.3s+2.5), G12 = 0.5/(s²+0.3s+2.5)
                [[0.5], [1.0]],         # G21 = 0.5/(s²+0.3s+1.5), G22 = 1/(s²+0.3s+1.5)
            ],
            "den": [
                [[1.0, 0.3, 2.5], [1.0, 0.3, 2.5]],
                [[1.0, 0.3, 1.5], [1.0, 0.3, 1.5]],
            ],
        },
        "mimo_dc_motor": {
            "name": "DC Motor + Flexible Load (1×2 MISO)",
            "p": 2, "m": 1,
            "num": [
                [[10.0]],               # G11 = 10/(s²+11s+100)
                [[200.0]],              # G21 = 200/(s⁴+13s³+122s²+220s+2000)
            ],
            "den": [
                [[1.0, 11.0, 100.0]],
                [[1.0, 13.0, 122.0, 220.0, 2000.0]],
            ],
        },
    }

    PARAMETER_SCHEMA: Dict[str, Dict] = {
        "system_type": {
            "type": "select",
            "options": [
                {"value": "linear_tf", "label": "SISO Transfer Function"},
                {"value": "mimo_tf", "label": "MIMO Transfer Function"},
                {"value": "state_space", "label": "State-Space Matrices (A,B,C,D)"},
                {"value": "nonlinear", "label": "Nonlinear System"},
            ],
            "default": "linear_tf",
        },
        "preset": {
            "type": "select",
            "options": [
                # SISO TF presets
                {"value": "rc_lowpass", "label": "RC Low-Pass [1/(s+1)]"},
                {"value": "mass_spring", "label": "Mass-Spring [1/(s²+2s+1)]"},
                {"value": "dc_motor", "label": "DC Motor Position [1/(s²+s)]"},
                {"value": "unstable", "label": "Unstable [1/(s²-1)]"},
                # Nonlinear presets
                {"value": "pendulum", "label": "Simple Pendulum (n=2)"},
                {"value": "van_der_pol", "label": "Van der Pol (n=2)"},
                {"value": "duffing", "label": "Duffing (n=2)"},
                {"value": "inverted_pendulum", "label": "Inverted Pendulum on Cart (n=4)"},
                {"value": "coupled_tanks", "label": "Coupled Tanks MIMO (n=2, m=2)"},
                {"value": "lotka_volterra", "label": "Lotka-Volterra (autonomous, n=2)"},
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
                {"value": "modal", "label": "Modal (Diagonal)"},
                {"value": "jordan", "label": "Jordan (Schur)"},
            ],
            "default": "controllable",
        },
        "apply_minreal": {
            "type": "checkbox",
            "default": False,
        },
        # MIMO TF controls
        "mimo_outputs": {
            "type": "select",
            "options": [
                {"value": 1, "label": "1"},
                {"value": 2, "label": "2"},
                {"value": 3, "label": "3"},
                {"value": 4, "label": "4"},
            ],
            "default": 2,
        },
        "mimo_inputs": {
            "type": "select",
            "options": [
                {"value": 1, "label": "1"},
                {"value": 2, "label": "2"},
                {"value": 3, "label": "3"},
                {"value": 4, "label": "4"},
            ],
            "default": 2,
        },
        "mimo_preset": {
            "type": "select",
            "options": [
                {"value": "mimo_coupled_spring", "label": "Coupled Mass-Spring-Damper (2×2)"},
                {"value": "mimo_dc_motor", "label": "DC Motor + Flex Load (1×2 MISO)"},
                {"value": "mimo_custom", "label": "Custom MIMO TF"},
            ],
            "default": "mimo_coupled_spring",
        },
        # MIMO TF entry fields: G_ij num/den for i=1..4, j=1..4
        # Stored as comma-separated coefficients, highest power first
        **{
            f"mimo_tf_{i}{j}_num": {"type": "expression", "default": "0"}
            for i in range(1, 5) for j in range(1, 5)
        },
        **{
            f"mimo_tf_{i}{j}_den": {"type": "expression", "default": "1"}
            for i in range(1, 5) for j in range(1, 5)
        },
        # Nonlinear dimension controls
        "nl_states": {
            "type": "select",
            "options": [{"value": i, "label": str(i)} for i in range(1, 7)],
            "default": 2,
        },
        "nl_inputs": {
            "type": "select",
            "options": [{"value": i, "label": str(i)} for i in range(0, 5)],
            "default": 1,
        },
        "nl_outputs": {
            "type": "select",
            "options": [{"value": i, "label": str(i)} for i in range(1, 5)],
            "default": 1,
        },
        # State equations ẋ₁..ẋ₆
        "nl_f1": {"type": "expression", "default": "x2"},
        "nl_f2": {"type": "expression", "default": "-sin(x1) - 0.5*x2 + u1"},
        "nl_f3": {"type": "expression", "default": "0"},
        "nl_f4": {"type": "expression", "default": "0"},
        "nl_f5": {"type": "expression", "default": "0"},
        "nl_f6": {"type": "expression", "default": "0"},
        # Output equations y₁..y₄
        "nl_h1": {"type": "expression", "default": "x1"},
        "nl_h2": {"type": "expression", "default": "x2"},
        "nl_h3": {"type": "expression", "default": "x3"},
        "nl_h4": {"type": "expression", "default": "x4"},
        # Legacy compat (still used by old presets)
        "nl_output": {"type": "expression", "default": "x1"},
        "eq_mode": {
            "type": "select",
            "options": [
                {"value": "zero_input", "label": "Zero-Input Equilibria (u = 0)"},
                {"value": "operating_point", "label": "Operating Point (specify x*, solve for u*)"},
            ],
            "default": "zero_input",
        },
        "eq_point_idx": {
            "type": "slider",
            "min": 0,
            "max": 4,
            "step": 1,
            "default": 0,
        },
        # Operating point sliders (x* values)
        "op_x1": {"type": "slider", "min": -10, "max": 10, "step": 0.1, "default": 0.0},
        "op_x2": {"type": "slider", "min": -10, "max": 10, "step": 0.1, "default": 0.0},
        "op_x3": {"type": "slider", "min": -10, "max": 10, "step": 0.1, "default": 0.0},
        "op_x4": {"type": "slider", "min": -10, "max": 10, "step": 0.1, "default": 0.0},
        "op_x5": {"type": "slider", "min": -10, "max": 10, "step": 0.1, "default": 0.0},
        "op_x6": {"type": "slider", "min": -10, "max": 10, "step": 0.1, "default": 0.0},
        "matrix_a": {
            "type": "expression",
            "default": "0, 1; -2, -3",
        },
        "matrix_b": {
            "type": "expression",
            "default": "0; 1",
        },
        "matrix_c": {
            "type": "expression",
            "default": "1, 0",
        },
        "matrix_d": {
            "type": "expression",
            "default": "0",
        },
    }

    DEFAULT_PARAMS: Dict[str, Any] = {
        "system_type": "linear_tf",
        "preset": "rc_lowpass",
        "tf_numerator": "1",
        "tf_denominator": "1, 1",
        "canonical_form": "controllable",
        "apply_minreal": False,
        "mimo_outputs": 2,
        "mimo_inputs": 2,
        "mimo_preset": "mimo_coupled_spring",
        **{f"mimo_tf_{i}{j}_num": "0" for i in range(1, 5) for j in range(1, 5)},
        **{f"mimo_tf_{i}{j}_den": "1" for i in range(1, 5) for j in range(1, 5)},
        "nl_states": 2,
        "nl_inputs": 1,
        "nl_outputs": 1,
        "nl_f1": "x2",
        "nl_f2": "-sin(x1) - 0.5*x2 + u1",
        "nl_f3": "0",
        "nl_f4": "0",
        "nl_f5": "0",
        "nl_f6": "0",
        "nl_h1": "x1",
        "nl_h2": "x2",
        "nl_h3": "x3",
        "nl_h4": "x4",
        "nl_output": "x1",
        "eq_mode": "zero_input",
        "eq_point_idx": 0,
        "op_x1": 0.0, "op_x2": 0.0, "op_x3": 0.0,
        "op_x4": 0.0, "op_x5": 0.0, "op_x6": 0.0,
        "matrix_a": "0, 1; -2, -3",
        "matrix_b": "0; 1",
        "matrix_c": "1, 0",
        "matrix_d": "0",
    }

    HUB_SLOTS = ["control"]
    HUB_DIMENSIONS = {"n": None, "m": None, "p": None}

    def to_hub_data(self) -> Optional[Dict[str, Any]]:
        """Export linearized SS matrices (or TF) to the hub.

        For SISO TF mode: exports TF coefficients (standard path).
        For MIMO TF, Direct SS, and Nonlinear modes: exports A,B,C,D matrices
        so downstream sims (e.g., MIMO Design Studio) can use them.
        """
        data = self._compute()
        if data.get("A") is None:
            return None

        A = data["A"]
        B = data["B"]
        C = data["C"]
        D = data["D"]
        n = data.get("system_order", len(A))
        m = len(B[0]) if B and B[0] else 1
        p = len(C) if C else 1

        hub = {
            "source": "ss",
            "domain": self.HUB_DOMAIN,
            "dimensions": {"n": n, "m": m, "p": p},
            "ss": {"A": A, "B": B, "C": C, "D": D},
        }

        # Also include TF for SISO systems
        if m == 1 and p == 1:
            num_n = data.get("num_n")
            den_n = data.get("den_n")
            if num_n and den_n:
                hub["tf"] = {"num": num_n, "den": den_n, "variable": "s"}
                hub["source"] = "tf"

        return hub

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
        # Apply preset defaults for expression fields (skip for direct matrix mode)
        sys_type = self.parameters.get("system_type", "linear_tf")
        if sys_type == "mimo_tf":
            mimo_preset = self.parameters.get("mimo_preset", "mimo_coupled_spring")
            if mimo_preset != "mimo_custom":
                self._apply_preset_expressions(mimo_preset)
        elif sys_type != "state_space":
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
        if name == "mimo_preset" and str(value) != "mimo_custom":
            self._apply_preset_expressions(str(value))

        # Manual edit of TF fields switches preset to custom
        if name in ("tf_numerator", "tf_denominator"):
            self.parameters["preset"] = "custom"
        if name.startswith("mimo_tf_") and name.endswith(("_num", "_den")):
            self.parameters["mimo_preset"] = "mimo_custom"

        return self.get_state()

    def _apply_preset_expressions(self, preset: str) -> None:
        """Fill expression fields from preset definitions."""
        if preset in self.LINEAR_PRESETS:
            num, den, _ = self.LINEAR_PRESETS[preset]
            self.parameters["tf_numerator"] = ", ".join(str(v) for v in num)
            self.parameters["tf_denominator"] = ", ".join(str(v) for v in den)
            self.parameters["system_type"] = "linear_tf"
        elif preset in self.MIMO_TF_PRESETS:
            pdata = self.MIMO_TF_PRESETS[preset]
            self.parameters["mimo_outputs"] = pdata["p"]
            self.parameters["mimo_inputs"] = pdata["m"]
            self.parameters["mimo_preset"] = preset
            # Fill MIMO TF expression fields
            for i in range(pdata["p"]):
                for j in range(pdata["m"]):
                    key_num = f"mimo_tf_{i+1}{j+1}_num"
                    key_den = f"mimo_tf_{i+1}{j+1}_den"
                    self.parameters[key_num] = ", ".join(
                        str(v) for v in pdata["num"][i][j]
                    )
                    self.parameters[key_den] = ", ".join(
                        str(v) for v in pdata["den"][i][j]
                    )
            self.parameters["system_type"] = "mimo_tf"
        elif preset in self.NONLINEAR_PRESETS_V2:
            pdata = self.NONLINEAR_PRESETS_V2[preset]
            self.parameters["nl_states"] = pdata["n"]
            self.parameters["nl_inputs"] = pdata["m"]
            self.parameters["nl_outputs"] = pdata["p"]
            # Fill state equations
            for i in range(pdata["n"]):
                self.parameters[f"nl_f{i+1}"] = pdata["f"][i]
            # Fill output equations
            for i in range(pdata["p"]):
                self.parameters[f"nl_h{i+1}"] = pdata["h"][i]
            # Legacy compat
            self.parameters["nl_output"] = pdata["h"][0]
            if pdata["n"] >= 2 and pdata["m"] <= 1:
                self.parameters["nl_f1"] = pdata["f"][0]
                self.parameters["nl_f2"] = pdata["f"][1]
            self.parameters["system_type"] = "nonlinear"
            # Set operating point defaults from preset hint
            op_hint = pdata.get("op_hint")
            if op_hint:
                for i, v in enumerate(op_hint):
                    self.parameters[f"op_x{i+1}"] = v
                # Default to operating point mode for presets that have one
                self.parameters["eq_mode"] = "operating_point"

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
        # Compute system properties (controllability, observability, etc.)
        properties: Dict[str, Any] = {}
        if data.get("A") is not None:
            try:
                properties = self._compute_properties(data)
            except Exception:
                pass
        return {
            "parameters": self.parameters.copy(),
            "plots": self._build_plots(data),
            "metadata": {
                "simulation_type": "state_space_analyzer",
                "hub_slots": self.HUB_SLOTS,
                "hub_domain": self.HUB_DOMAIN,
                "hub_dimensions": self.HUB_DIMENSIONS,
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
                "properties": properties,
                # Dimension info
                "n_inputs": data.get("n_inputs", 1),
                "n_outputs": data.get("n_outputs", 1),
                "is_siso": data.get("is_siso", True),
                # Canonical form and minreal
                "canonical_form": data.get("canonical_form", "controllable"),
                "minreal_info": data.get("minreal_info"),
                "transmission_zeros": data.get("transmission_zeros"),
                # TF representation (for display)
                "tf_matrix": data.get("tf_matrix"),
            },
        }

    def _build_plots(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Assemble plot list from computed data.

        Plot IDs produced (frontend uses these to assign plots to tabs):
          eigenvalue_map   — always
          step_response    — SISO modes when A exists
          impulse_response — SISO modes when A exists
          bode_magnitude   — SISO modes when A exists
          bode_phase       — SISO modes when A exists
          phase_portrait   — nonlinear only
          mimo_step_grid   — MIMO modes (p×m step response grid)
          sv_plot          — MIMO modes (singular value plot)
        """
        if data.get("A") is None:
            plots = [self._eigenvalue_plot(data)]
            # Still show phase portrait for nonlinear even without A
            sys_type = self.parameters.get("system_type", "linear_tf")
            if sys_type == "nonlinear" and data.get("f1_str"):
                plots.append(self._phase_portrait_plot(data))
            return plots

        plots = [self._eigenvalue_plot(data)]
        sys_type = self.parameters.get("system_type", "linear_tf")
        is_mimo = not data.get("is_siso", True)

        # Phase portrait (nonlinear only)
        if sys_type == "nonlinear":
            plots.append(self._phase_portrait_plot(data))

        if is_mimo:
            # MIMO: p×m step response grid + singular value plot
            plots.append(self._mimo_step_grid_plot(data))
            plots.append(self._singular_value_plot(data))
        else:
            # SISO: standard time-domain and frequency-domain plots
            plots.append(self._step_response_plot(data))
            plots.append(self._impulse_response_plot(data))
            plots.extend(self._bode_plots(data))

        return plots

    # -------------------------------------------------------------------------
    # Main computation dispatcher
    # -------------------------------------------------------------------------

    def _compute(self) -> Dict[str, Any]:
        """Dispatch to linear, direct, or nonlinear computation; wrap errors."""
        try:
            sys_type = self.parameters.get("system_type", "linear_tf")
            if sys_type == "nonlinear":
                return self._compute_nonlinear()
            elif sys_type == "state_space":
                return self._compute_direct()
            elif sys_type == "mimo_tf":
                return self._compute_mimo_tf()
            else:
                return self._compute_linear()
        except Exception as exc:
            err_msg = str(exc)[:200]
            return {
                "error": err_msg,
                "latex_steps": [
                    {
                        "title": "Computation Error",
                        "latex": "\\text{Error: see message below}",
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
        from core.tf_parser import parse_coeff_string
        return parse_coeff_string(expr_str)

    def _parse_matrix(self, expr_str: str, name: str) -> List[List[float]]:
        """Parse matrix string.  Rows separated by ';', values by ','.

        Examples:
            '0, 1; -2, -3'  →  [[0, 1], [-2, -3]]
            '1, 0'          →  [[1, 0]]
            '0; 1'          →  [[0], [1]]
            '0'             →  [[0]]
        """
        expr_str = str(expr_str).strip()
        if not expr_str:
            raise ValueError(f"Empty matrix {name}")
        rows = [r.strip() for r in expr_str.split(";")]
        result: List[List[float]] = []
        for row_str in rows:
            if not row_str:
                continue
            vals = [v.strip() for v in row_str.split(",") if v.strip()]
            if not vals:
                continue
            try:
                result.append([float(v) for v in vals])
            except ValueError as exc:
                raise ValueError(
                    f"Invalid value in matrix {name}: {exc}"
                ) from exc
        if not result:
            raise ValueError(f"Empty matrix {name}")
        # Validate uniform column count
        ncols = len(result[0])
        for i, row in enumerate(result):
            if len(row) != ncols:
                raise ValueError(
                    f"Matrix {name} row {i+1} has {len(row)} values, "
                    f"expected {ncols}"
                )
        return result

    def _compute_linear(self) -> Dict[str, Any]:
        """Convert TF to state-space via ss_utils; build LaTeX derivation steps.

        Supports all 4 canonical forms (controllable, observable, modal, jordan),
        improper TFs via polynomial long division, and optional minimal realization.
        """
        preset = self.parameters.get("preset", "rc_lowpass")
        canonical = self.parameters.get("canonical_form", "controllable")
        do_minreal = bool(self.parameters.get("apply_minreal", False))

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

        # Convert to SS using selected canonical form (handles improper TFs)
        A, B, C, D = tf2ss_canonical(num_n, den_n, form=canonical)

        # Optional minimal realization
        minreal_info = None
        if do_minreal and A.shape[0] > 0:
            A, B, C, D, minreal_info = minreal(A, B, C, D)

        n = A.shape[0]
        eigenvalues = np.linalg.eigvals(A) if n > 0 else np.array([])
        is_stable = bool(np.all(eigenvalues.real < -1e-10)) if n > 0 else True
        is_marginal = bool(
            np.all(eigenvalues.real <= 1e-10) and not is_stable
        ) if n > 0 else False

        # Transmission zeros
        t_zeros = transmission_zeros(A, B, C, D) if n > 0 else np.array([])

        latex_steps = self._build_linear_latex(
            num_n, den_n, A, B, C, D, eigenvalues, canonical, n, is_marginal
        )

        result = {
            "A": A.tolist(),
            "B": B.tolist(),
            "C": C.tolist(),
            "D": D.tolist() if isinstance(D, np.ndarray) else [[float(D)]],
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
                "D": D.tolist() if isinstance(D, np.ndarray) else [[float(D)]],
            },
            "equilibrium_points": [],
            "selected_eq_idx": 0,
            "system_order": n,
            "preset_name": preset_name,
            "num_n": num_n,
            "den_n": den_n,
            "canonical_form": canonical,
        }
        # Add transmission zeros
        if len(t_zeros) > 0:
            result["transmission_zeros"] = [
                {"real": float(z.real), "imag": float(z.imag)} for z in t_zeros
            ]
        # Add minreal info
        if minreal_info is not None:
            result["minreal_info"] = minreal_info
        return result

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
        form_names = {
            "controllable": "Controllable Canonical",
            "observable": "Observable Canonical",
            "modal": "Modal (Diagonal)",
            "jordan": "Jordan (Schur)",
        }
        form_name = form_names.get(canonical, canonical.title())

        if canonical == "controllable":
            form_explain = (
                "\\begin{aligned}"
                "&\\text{Controllable canonical (phase-variable) form:} \\\\"
                "&\\text{denominator coefficients populate the last row of } A, "
                "\\text{ column vector } B = [0,\\ldots,0,1]^T"
                "\\end{aligned}"
            )
            form_explain_text = (
                "Controllable form ensures every state is reachable from the input. "
                "The companion matrix structure directly encodes the characteristic polynomial."
            )
        elif canonical == "observable":
            form_explain = (
                "\\begin{aligned}"
                "&\\text{Observable canonical form:} \\\\"
                "&\\text{denominator coefficients populate the last column of } A; \\\\"
                "&\\text{input vector } B = [0,\\ldots,0,1]^T; "
                "\\text{ output row } C = [1, 0, \\ldots, 0]"
                "\\end{aligned}"
            )
            form_explain_text = (
                "Observable form ensures every state affects the output. "
                "It is the transpose dual of controllable form."
            )
        elif canonical == "modal":
            form_explain = (
                "\\begin{aligned}"
                "&\\text{Modal (diagonal) form:} \\\\"
                "&A = T^{-1} A_{cc} T \\text{ where } T \\text{ is the eigenvector matrix} \\\\"
                "&\\text{Real eigenvalues } \\to 1{\\times}1 \\text{ diagonal entries} \\\\"
                "&\\text{Complex pairs } \\sigma \\pm j\\omega \\to "
                "\\begin{bmatrix} \\sigma & \\omega \\\\ -\\omega & \\sigma \\end{bmatrix}"
                "\\end{aligned}"
            )
            form_explain_text = (
                "Modal form decouples each natural mode. Each diagonal entry (or 2×2 block) "
                "corresponds to one eigenvalue, making mode contributions transparent."
            )
        else:  # jordan
            form_explain = (
                "\\begin{aligned}"
                "&\\text{Jordan (Schur) form:} \\\\"
                "&A = Z^T A_{cc} Z \\text{ (real Schur decomposition)} \\\\"
                "&\\text{Quasi-upper-triangular: } 1{\\times}1 \\text{ and } 2{\\times}2 \\text{ blocks on diagonal}"
                "\\end{aligned}"
            )
            form_explain_text = (
                "The real Schur decomposition is a numerically stable alternative to the "
                "Jordan normal form. It reveals the eigenvalue structure without the "
                "conditioning issues of true Jordan decomposition."
            )

        steps.append({
            "title": f"③ {form_name} Form",
            "latex": form_explain,
            "explanation": form_explain_text,
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
                dc_gain = float((C @ np.linalg.solve(-A, B) + D).flat[0])
                if not np.isfinite(dc_gain):
                    raise ValueError("overflow")
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
    # MIMO TF path
    # -------------------------------------------------------------------------

    def _compute_mimo_tf(self) -> Dict[str, Any]:
        """Convert MIMO transfer function matrix to minimal state-space."""
        mimo_preset = self.parameters.get("mimo_preset", "mimo_coupled_spring")
        do_minreal = bool(self.parameters.get("apply_minreal", False))

        if mimo_preset in self.MIMO_TF_PRESETS:
            pdata = self.MIMO_TF_PRESETS[mimo_preset]
            p_out = pdata["p"]
            m_in = pdata["m"]
            num_matrix = pdata["num"]
            den_matrix = pdata["den"]
            preset_name = pdata["name"]
        else:
            p_out = int(self.parameters.get("mimo_outputs", 2))
            m_in = int(self.parameters.get("mimo_inputs", 2))
            preset_name = "Custom MIMO Transfer Function"
            num_matrix = []
            den_matrix = []
            for i in range(p_out):
                num_row = []
                den_row = []
                for j in range(m_in):
                    key_n = f"mimo_tf_{i+1}{j+1}_num"
                    key_d = f"mimo_tf_{i+1}{j+1}_den"
                    num_str = self.parameters.get(key_n, "0")
                    den_str = self.parameters.get(key_d, "1")
                    num_row.append(self._parse_tf_coefficients(num_str))
                    den_row.append(self._parse_tf_coefficients(den_str))
                num_matrix.append(num_row)
                den_matrix.append(den_row)

        # Convert to SS via mimo_tf2ss (includes internal minreal)
        A, B, C, D = mimo_tf2ss(num_matrix, den_matrix)

        n = A.shape[0]
        eigenvalues = np.linalg.eigvals(A) if n > 0 else np.array([])
        is_stable = bool(np.all(eigenvalues.real < -1e-10)) if n > 0 else True
        is_marginal = bool(
            np.all(eigenvalues.real <= 1e-10) and not is_stable
        ) if n > 0 else False

        # Transmission zeros
        t_zeros = transmission_zeros(A, B, C, D) if n > 0 else np.array([])

        # Build TF matrix info for display
        tf_matrix_info = {"entries": []}
        for i in range(p_out):
            row_entries = []
            for j in range(m_in):
                num_ij = num_matrix[i][j]
                den_ij = den_matrix[i][j]
                row_entries.append({
                    "num": [float(c) for c in num_ij],
                    "den": [float(c) for c in den_ij],
                    "order": max(len(den_ij) - 1, 0),
                })
            tf_matrix_info["entries"].append(row_entries)

        # LaTeX steps
        latex_steps = self._build_mimo_tf_latex(
            num_matrix, den_matrix, A, B, C, D, eigenvalues,
            p_out, m_in, n, is_stable, is_marginal
        )

        result = {
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
            "n_inputs": m_in,
            "n_outputs": p_out,
            "is_siso": (m_in == 1 and p_out == 1),
            "preset_name": preset_name,
            "tf_matrix": tf_matrix_info,
        }
        if len(t_zeros) > 0:
            result["transmission_zeros"] = [
                {"real": float(z.real), "imag": float(z.imag)} for z in t_zeros
            ]
        return result

    def _build_mimo_tf_latex(
        self,
        num_matrix: List,
        den_matrix: List,
        A: np.ndarray,
        B: np.ndarray,
        C: np.ndarray,
        D: np.ndarray,
        eigenvalues: np.ndarray,
        p: int,
        m: int,
        n: int,
        is_stable: bool,
        is_marginal: bool,
    ) -> List[Dict[str, str]]:
        """Generate LaTeX derivation steps for MIMO TF → state-space."""
        steps = []

        # Step 1: Transfer matrix
        tf_rows = []
        for i in range(p):
            row_cells = []
            for j in range(m):
                num_lat = self._poly_to_latex(num_matrix[i][j], "s")
                den_lat = self._poly_to_latex(den_matrix[i][j], "s")
                row_cells.append(f"\\frac{{{num_lat}}}{{{den_lat}}}")
            tf_rows.append(" & ".join(row_cells))
        tf_matrix_lat = (
            "\\begin{bmatrix} " + " \\\\ ".join(tf_rows) + " \\end{bmatrix}"
        )
        steps.append({
            "title": "① MIMO Transfer Function Matrix",
            "latex": f"G(s) = {tf_matrix_lat}",
            "explanation": (
                f"A {p}×{m} MIMO transfer function matrix. Each entry G_ij(s) "
                f"maps input j to output i independently."
            ),
        })

        # Step 2: Per-channel SISO conversion
        steps.append({
            "title": "② Per-Channel SISO Conversion",
            "latex": (
                "\\text{Each } G_{ij}(s) \\to (A_{ij}, B_{ij}, C_{ij}, D_{ij})"
                " \\text{ via controllable canonical form}"
            ),
            "explanation": (
                "Each scalar transfer function is independently converted to "
                "state-space form, then assembled into a block-diagonal structure."
            ),
        })

        # Step 3: Block-diagonal assembly
        steps.append({
            "title": "③ Block-Diagonal Assembly",
            "latex": (
                f"A_{{big}} = \\text{{blkdiag}}(A_{{11}}, \\ldots, A_{{{p}{m}}})"
                f" \\quad (n = {n})"
            ),
            "explanation": (
                f"The assembled system has {n} states. "
                f"Input routing matrix B selects columns, "
                f"output routing matrix C selects rows."
            ),
        })

        # Step 4: Minimal realization
        steps.append({
            "title": "④ Minimal Realization",
            "latex": (
                f"n_{{min}} = {n} \\text{{ (after removing uncontrollable/unobservable modes)}}"
            ),
            "explanation": (
                "Balanced truncation removes redundant states that appear "
                "when multiple channels share the same dynamics."
            ),
        })

        # Step 5: State-space matrices
        if n <= 8:
            A_lat = self._matrix_to_latex(A)
            B_lat = self._matrix_to_latex(B)
            C_lat = self._matrix_to_latex(C)
            D_lat = self._matrix_to_latex(D)
            steps.append({
                "title": "⑤ State-Space Matrices",
                "latex": (
                    f"\\begin{{aligned}}"
                    f"A &= {A_lat} \\\\"
                    f"B &= {B_lat} \\\\"
                    f"C &= {C_lat} \\\\"
                    f"D &= {D_lat}"
                    f"\\end{{aligned}}"
                ),
                "explanation": (
                    f"A: {n}×{n}, B: {n}×{m}, C: {p}×{n}, D: {p}×{m}"
                ),
            })
        else:
            steps.append({
                "title": "⑤ State-Space Dimensions",
                "latex": (
                    f"A \\in \\mathbb{{R}}^{{{n}\\times{n}}}, \\quad "
                    f"B \\in \\mathbb{{R}}^{{{n}\\times{m}}}, \\quad "
                    f"C \\in \\mathbb{{R}}^{{{p}\\times{n}}}, \\quad "
                    f"D \\in \\mathbb{{R}}^{{{p}\\times{m}}}"
                ),
                "explanation": (
                    f"Matrices too large for display ({n}×{n}). "
                    f"See the Properties tab for numerical values."
                ),
            })

        # Step 6: Eigenvalues
        eig_parts = []
        for eig in eigenvalues[:10]:  # Cap display at 10
            r, im = eig.real, eig.imag
            if abs(im) < 1e-10:
                eig_parts.append(f"\\lambda = {r:.4f}")
            elif im > 0:
                eig_parts.append(f"\\lambda = {r:.4f} \\pm {abs(im):.4f}j")

        stability_note = (
            "\\text{Asymptotically stable}" if is_stable
            else "\\text{Marginally stable}" if is_marginal
            else "\\text{Unstable}"
        )
        eig_latex = (
            "\\begin{aligned}"
            + " \\\\ ".join(f"&{e}" for e in eig_parts)
            + (" \\\\ &\\vdots" if len(eigenvalues) > 10 else "")
            + " \\\\ &" + stability_note
            + "\\end{aligned}"
        )
        steps.append({
            "title": "⑥ Eigenvalues & Stability",
            "latex": eig_latex,
            "explanation": (
                f"The system has {len(eigenvalues)} poles. "
                "All must be in the open LHP for asymptotic stability."
            ),
        })

        return steps

    def _mimo_step_grid_plot(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate p×m step response grid for MIMO systems."""
        from core.mimo_utils import mimo_step_response

        A = np.array(data["A"], dtype=float)
        B = np.atleast_2d(np.array(data["B"], dtype=float))
        C = np.atleast_2d(np.array(data["C"], dtype=float))
        D = np.atleast_2d(np.array(data["D"], dtype=float))

        n = A.shape[0]
        m_in = B.shape[1]
        p_out = C.shape[0]

        t_eval = np.linspace(0, 10, 500)
        if n == 0:
            # Static gain — flat response at D values
            traces = []
            for j in range(m_in):
                for i in range(p_out):
                    traces.append({
                        "x": t_eval.tolist(),
                        "y": [float(D[i, j])] * len(t_eval),
                        "type": "scatter",
                        "mode": "lines",
                        "name": f"y{i+1} ← u{j+1}",
                    })
            return {
                "id": "mimo_step_grid",
                "title": "Step Response Grid (Static Gain)",
                "data": traces,
                "layout": self._default_time_layout("mimo_step_grid"),
            }

        resp = mimo_step_response(A, B, C, D, t_eval)

        colors = [
            "#3b82f6", "#ef4444", "#10b981", "#f59e0b",
            "#8b5cf6", "#ec4899", "#06b6d4", "#14b8a6",
        ]

        traces = []
        for j in range(m_in):
            for i in range(p_out):
                y_data = resp["responses"].get((j, i), np.zeros_like(t_eval))
                traces.append({
                    "x": t_eval.tolist(),
                    "y": y_data.tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "name": f"y{i+1} ← u{j+1}",
                    "line": {"color": colors[(j * p_out + i) % len(colors)], "width": 2},
                })

        return {
            "id": "mimo_step_grid",
            "title": f"Step Response Grid ({p_out}×{m_in})",
            "data": traces,
            "layout": {
                "xaxis": {
                    "title": "Time (s)",
                    "gridcolor": "rgba(148,163,184,0.1)",
                    "zerolinecolor": "rgba(148,163,184,0.3)",
                    "color": "#f1f5f9",
                },
                "yaxis": {
                    "title": "Output",
                    "gridcolor": "rgba(148,163,184,0.1)",
                    "zerolinecolor": "rgba(148,163,184,0.3)",
                    "color": "#f1f5f9",
                },
                "paper_bgcolor": "rgba(0,0,0,0)",
                "plot_bgcolor": "rgba(0,0,0,0)",
                "font": {"family": "Inter, sans-serif", "size": 12, "color": "#f1f5f9"},
                "margin": {"t": 45, "r": 25, "b": 55, "l": 60},
                "showlegend": True,
                "legend": {"font": {"color": "#94a3b8"}, "bgcolor": "rgba(0,0,0,0.3)"},
                "uirevision": "mimo_step_grid",
            },
        }

    def _singular_value_plot(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Singular value plot: σ(G(jω)) vs frequency for MIMO systems."""
        A = np.array(data["A"], dtype=float)
        B = np.atleast_2d(np.array(data["B"], dtype=float))
        C = np.atleast_2d(np.array(data["C"], dtype=float))
        D = np.atleast_2d(np.array(data["D"], dtype=float))

        n = A.shape[0]
        freqs = np.logspace(-2, 3, 200)

        sv_data = []  # list of arrays, one per singular value
        for w in freqs:
            s = 1j * w
            if n > 0:
                G = C @ np.linalg.solve(s * np.eye(n) - A, B) + D
            else:
                G = D.astype(complex)
            svs = np.linalg.svd(G, compute_uv=False)
            sv_data.append(svs)

        sv_array = np.array(sv_data)  # (n_freqs, min(p,m))
        n_sv = sv_array.shape[1]

        colors = ["#3b82f6", "#ef4444", "#10b981", "#f59e0b"]
        traces = []
        for k in range(n_sv):
            sv_db = 20 * np.log10(np.maximum(sv_array[:, k], 1e-15))
            traces.append({
                "x": freqs.tolist(),
                "y": sv_db.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": f"σ{k+1}",
                "line": {"color": colors[k % len(colors)], "width": 2},
            })

        return {
            "id": "sv_plot",
            "title": "Singular Value Plot σ(G(jω))",
            "data": traces,
            "layout": {
                "xaxis": {
                    "title": "Frequency (rad/s)",
                    "type": "log",
                    "gridcolor": "rgba(148,163,184,0.1)",
                    "zerolinecolor": "rgba(148,163,184,0.3)",
                    "color": "#f1f5f9",
                },
                "yaxis": {
                    "title": "Singular Value (dB)",
                    "gridcolor": "rgba(148,163,184,0.1)",
                    "zerolinecolor": "rgba(148,163,184,0.3)",
                    "color": "#f1f5f9",
                },
                "paper_bgcolor": "rgba(0,0,0,0)",
                "plot_bgcolor": "rgba(0,0,0,0)",
                "font": {"family": "Inter, sans-serif", "size": 12, "color": "#f1f5f9"},
                "margin": {"t": 45, "r": 25, "b": 55, "l": 60},
                "showlegend": True,
                "legend": {"font": {"color": "#94a3b8"}, "bgcolor": "rgba(0,0,0,0.3)"},
                "uirevision": "sv_plot",
            },
        }

    # -------------------------------------------------------------------------
    # Direct state-space matrix path
    # -------------------------------------------------------------------------

    def _compute_direct(self) -> Dict[str, Any]:
        """Compute analysis from directly entered A, B, C, D matrices."""
        A_raw = self._parse_matrix(self.parameters.get("matrix_a", "0"), "A")
        B_raw = self._parse_matrix(self.parameters.get("matrix_b", "0"), "B")
        C_raw = self._parse_matrix(self.parameters.get("matrix_c", "0"), "C")
        D_raw = self._parse_matrix(self.parameters.get("matrix_d", "0"), "D")

        A = np.array(A_raw, dtype=float)
        B = np.atleast_2d(np.array(B_raw, dtype=float))
        C = np.atleast_2d(np.array(C_raw, dtype=float))
        D = np.atleast_2d(np.array(D_raw, dtype=float))

        n = A.shape[0]
        if A.shape != (n, n):
            raise ValueError(f"A must be square, got shape {A.shape}")
        if B.shape[0] != n:
            raise ValueError(f"B must have {n} rows to match A, got {B.shape[0]}")
        if C.shape[1] != n:
            raise ValueError(f"C must have {n} columns to match A, got {C.shape[1]}")

        eigenvalues = np.linalg.eigvals(A)
        is_stable = bool(np.all(eigenvalues.real < -1e-10))
        is_marginal = bool(np.all(eigenvalues.real <= 1e-10) and not is_stable)

        latex_steps = self._build_direct_latex(A, B, C, D, eigenvalues, n, is_marginal)

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
            "n_inputs": B.shape[1],
            "n_outputs": C.shape[0],
            "is_siso": (B.shape[1] == 1 and C.shape[0] == 1),
            "preset_name": "Direct State-Space Entry",
        }

    def _build_direct_latex(
        self,
        A: np.ndarray,
        B: np.ndarray,
        C: np.ndarray,
        D: np.ndarray,
        eigenvalues: np.ndarray,
        n: int,
        is_marginal: bool = False,
    ) -> List[Dict[str, str]]:
        """Generate LaTeX derivation steps for direct matrix entry."""
        steps: List[Dict[str, str]] = []

        A_lat = self._matrix_to_latex(A)
        B_lat = self._matrix_to_latex(B)
        C_lat = self._matrix_to_latex(C)
        D_val = float(D.flat[0]) if D.size > 0 else 0.0

        # Step 1: Matrices
        steps.append({
            "title": "\u2460 State-Space Matrices",
            "latex": (
                f"\\begin{{aligned}}"
                f"A &= {A_lat}, & B &= {B_lat} \\\\"
                f"C &= {C_lat}, & D &= {self._fmt(D_val)}"
                f"\\end{{aligned}}"
            ),
            "explanation": (
                f"User-supplied {n}\u00d7{n} state-space realization.  "
                "A: system dynamics, B: input coupling, C: output, D: feedthrough."
            ),
        })

        # Step 2: State + output equations
        steps.append({
            "title": "\u2461 State & Output Equations",
            "latex": (
                "\\begin{aligned}"
                "\\dot{\\mathbf{x}}(t) &= A\\,\\mathbf{x}(t) + B\\,u(t) \\\\"
                "y(t) &= C\\,\\mathbf{x}(t) + D\\,u(t)"
                "\\end{aligned}"
            ),
            "explanation": (
                "The standard state-space form: a first-order vector ODE (state equation) "
                "plus a linear output map."
            ),
        })

        # Step 3: Expanded form (small systems)
        if n <= 4:
            expanded = self._expanded_state_eq_latex(A, B, n)
            steps.append({
                "title": "\u2462 Expanded Matrix Form",
                "latex": expanded,
                "explanation": "Full matrix multiplication written out explicitly.",
            })

        # Step 4: Characteristic polynomial
        char_coeffs = np.real(np.poly(A))
        poly_lat = self._poly_to_latex(char_coeffs.tolist(), "\\lambda")
        steps.append({
            "title": "\u2463 Characteristic Polynomial",
            "latex": f"\\det(\\lambda I - A) = {poly_lat}",
            "explanation": (
                "The eigenvalues are the roots of this polynomial.  "
                "They determine the system\u2019s natural modes and stability."
            ),
        })

        # Step 5: Eigenvalues & stability
        eig_parts = []
        for i, (r, im) in enumerate(
            zip(eigenvalues.real, eigenvalues.imag)
        ):
            if abs(im) < 1e-10:
                eig_parts.append(f"\\lambda_{{{i+1}}} = {r:.4f}")
            elif im > 0:
                eig_parts.append(
                    f"\\lambda_{{{i+1}}} = {r:.4f} + {im:.4f}j"
                )
            else:
                eig_parts.append(
                    f"\\lambda_{{{i+1}}} = {r:.4f} - {abs(im):.4f}j"
                )

        all_neg = np.all(eigenvalues.real < -1e-10)
        if all_neg:
            stab_note = (
                "\\text{Asymptotically stable \u2014 all eigenvalues in open LHP}"
            )
        elif is_marginal:
            stab_note = (
                "\\text{Marginally stable \u2014 eigenvalue(s) on } j\\omega"
                "\\text{ axis}"
            )
        else:
            stab_note = (
                "\\text{Unstable \u2014 eigenvalue(s) in right half-plane}"
            )

        dc_str = ""
        if all_neg:
            try:
                dc = float((C @ np.linalg.solve(-A, B) + D).flat[0])
                if not np.isfinite(dc):
                    raise ValueError("overflow")
                dc_str = (
                    f" \\\\ &\\text{{DC gain: }} K_{{dc}} = C(-A)^{{-1}}B + D"
                    f" = {dc:.4g}"
                )
            except Exception:
                pass

        eig_latex = (
            "\\begin{aligned}"
            + " \\\\ ".join(f"&{e}" for e in eig_parts)
            + " \\\\ &" + stab_note
            + dc_str
            + "\\end{aligned}"
        )
        steps.append({
            "title": "\u2464 Eigenvalues & Stability",
            "latex": eig_latex,
            "explanation": (
                "Eigenvalues of A = natural modes of the system.  "
                "Stable iff all real parts < 0."
            ),
        })

        return steps

    # -------------------------------------------------------------------------
    # System properties (controllability, observability, damping, etc.)
    # -------------------------------------------------------------------------

    def _compute_properties(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Compute system properties for the Properties tab.

        Returns dict with controllability, observability, pole analysis,
        DC gain, and transfer function coefficients (for display).
        """
        A = np.array(data["A"], dtype=float)
        B = np.atleast_2d(np.array(data["B"], dtype=float))
        C = np.atleast_2d(np.array(data["C"], dtype=float))
        D = np.atleast_2d(np.array(data["D"], dtype=float))
        n = A.shape[0]

        # -- Controllability: rank of [B, AB, A^2 B, ..., A^{n-1} B] --
        ctrb_cols = [np.linalg.matrix_power(A, i) @ B for i in range(n)]
        ctrb_matrix = np.hstack(ctrb_cols)
        ctrb_rank = int(np.linalg.matrix_rank(ctrb_matrix))

        # -- Observability: rank of [C; CA; CA^2; ...; CA^{n-1}] --
        obsv_rows = [C @ np.linalg.matrix_power(A, i) for i in range(n)]
        obsv_matrix = np.vstack(obsv_rows)
        obsv_rank = int(np.linalg.matrix_rank(obsv_matrix))

        # -- Per-pole analysis: natural frequency & damping ratio --
        eigenvalues = np.linalg.eigvals(A)
        pole_info: List[Dict[str, Any]] = []
        for eig in eigenvalues:
            sigma = float(eig.real)
            omega = float(eig.imag)
            omega_n = float(abs(eig))
            if omega_n > 1e-10:
                zeta = float(-sigma / omega_n)
            else:
                zeta = 1.0 if sigma < 0 else -1.0
            pole_info.append({
                "real": round(sigma, 6),
                "imag": round(omega, 6),
                "omega_n": round(omega_n, 6),
                "zeta": round(zeta, 6),
            })

        # -- DC gain: C (-A)^{-1} B + D (stable systems only) --
        dc_gain = None
        if np.all(eigenvalues.real < -1e-10):
            try:
                dc_val = float((C @ np.linalg.solve(-A, B) + D).flat[0])
                dc_gain = round(dc_val, 6) if np.isfinite(dc_val) else None
            except Exception:
                pass

        # -- Transfer function from state-space (for display) --
        tf_num = None
        tf_den = None
        try:
            ss_sys = signal.StateSpace(A, B, C, D)
            tf_sys = ss_sys.to_tf()
            tf_num = [round(float(c), 6) for c in tf_sys.num.flatten()]
            tf_den = [round(float(c), 6) for c in tf_sys.den.flatten()]
        except Exception:
            pass

        # -- Gramians and Hankel singular values (stable systems only) --
        hsv_list = None
        if np.all(eigenvalues.real < -1e-10):
            try:
                Wc = controllability_gramian(A, B)
                Wo = observability_gramian(A, C)
                WcWo = Wc @ Wo
                eigs_wc_wo = np.linalg.eigvals(WcWo)
                hsv = np.sqrt(np.maximum(eigs_wc_wo.real, 0.0))
                hsv_list = sorted(hsv.tolist(), reverse=True)
            except Exception:
                pass

        # -- Transmission zeros --
        t_zeros_list = None
        try:
            t_zeros = transmission_zeros(A, B, C, D)
            if len(t_zeros) > 0:
                t_zeros_list = [
                    {"real": round(float(z.real), 6), "imag": round(float(z.imag), 6)}
                    for z in t_zeros
                ]
        except Exception:
            pass

        props = {
            "controllability_rank": ctrb_rank,
            "is_controllable": ctrb_rank == n,
            "observability_rank": obsv_rank,
            "is_observable": obsv_rank == n,
            "system_order": n,
            "pole_info": pole_info,
            "dc_gain": dc_gain,
            "tf_num": tf_num,
            "tf_den": tf_den,
        }
        if hsv_list is not None:
            props["hankel_singular_values"] = hsv_list
        if t_zeros_list is not None:
            props["transmission_zeros"] = t_zeros_list
        return props

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
        """Linearize N×M×P nonlinear system around equilibrium via Jacobian.

        Supports arbitrary number of states (1-6), inputs (0-4), outputs (1-4).
        """
        preset = self.parameters.get("preset", "pendulum")
        eq_idx = int(self.parameters.get("eq_point_idx", 0))

        if preset in self.NONLINEAR_PRESETS_V2:
            pdata = self.NONLINEAR_PRESETS_V2[preset]
            n_states = pdata["n"]
            m_inputs = pdata["m"]
            p_outputs = pdata["p"]
            f_strs = pdata["f"]
            h_strs = pdata["h"]
            preset_name = pdata["name"]
            eq_hint = pdata.get("eq_hint")
        else:
            n_states = int(self.parameters.get("nl_states", 2))
            m_inputs = int(self.parameters.get("nl_inputs", 1))
            p_outputs = int(self.parameters.get("nl_outputs", 1))
            f_strs = [self.parameters.get(f"nl_f{i+1}", "0") for i in range(n_states)]
            h_strs = [self.parameters.get(f"nl_h{i+1}", f"x{i+1}") for i in range(p_outputs)]
            preset_name = "Custom Nonlinear System"
            eq_hint = None

        # Build symbol lists
        x_syms_used = list(_x_syms[:n_states])
        u_syms_used = list(_u_syms[:m_inputs]) if m_inputs > 0 else []
        all_syms = x_syms_used + u_syms_used

        # Parse expressions
        f_exprs = [self._safe_parse_expr(s) for s in f_strs]
        h_exprs = [self._safe_parse_expr(s) for s in h_strs]

        # Lambdify for numerical evaluation
        f_funcs = [sp.lambdify(all_syms if all_syms else [sp.Symbol('_dummy')],
                               expr, modules="numpy") for expr in f_exprs]

        latex_steps: List[Dict[str, str]] = []

        # Step 1: Show original system
        f_lines = " \\\\ ".join(
            f"\\dot{{x}}_{{{i+1}}} &= {sp.latex(f_exprs[i])}" for i in range(n_states)
        )
        h_lines = " \\\\ ".join(
            f"y_{{{i+1}}} &= {sp.latex(h_exprs[i])}" for i in range(p_outputs)
        )
        latex_steps.append({
            "title": f"① Nonlinear State Equations (n={n_states}, m={m_inputs}, p={p_outputs})",
            "latex": f"\\begin{{aligned}} {f_lines} \\\\ {h_lines} \\end{{aligned}}",
            "explanation": (
                f"A {n_states}-state, {m_inputs}-input, {p_outputs}-output nonlinear system. "
                "Linearization will produce a local linear approximation."
            ),
        })

        # Step 2: Find linearization point
        eq_mode = str(self.parameters.get("eq_mode", "zero_input"))
        u_zero_subs = {u_s: 0 for u_s in u_syms_used}
        u_zero_subs[_u_sym] = 0  # legacy 'u' symbol

        # u_eq_vals: the input values at the linearization point
        u_eq_vals: List[float] = [0.0] * m_inputs
        is_operating_point = False

        if eq_mode == "operating_point" and m_inputs > 0:
            # User specifies x*, we solve for u* such that f(x*, u*) = 0
            x_eq = [float(self.parameters.get(f"op_x{i+1}", 0.0))
                    for i in range(n_states)]

            # Build numeric f(u) with x fixed at x_eq
            x_subs = {x_syms_used[i]: x_eq[i] for i in range(n_states)}
            f_fixed_x = [expr.subs(x_subs) for expr in f_exprs]
            # These are now functions of u only
            safe_mods = [{"sqrt": lambda x: np.sqrt(np.maximum(x, 0.0))}, "numpy"]
            u_funcs = [sp.lambdify(
                u_syms_used if u_syms_used else [sp.Symbol('_dummy')],
                fexpr, modules=safe_mods
            ) for fexpr in f_fixed_x]

            def residual(u_vec):
                return np.array([float(uf(*u_vec)) for uf in u_funcs])

            from scipy.optimize import least_squares
            u_guess = np.zeros(m_inputs)
            try:
                result_ls = least_squares(residual, u_guess, method='lm')
                u_sol = result_ls.x
                if result_ls.cost < 1e-10:  # ||residual||² < threshold
                    u_eq_vals = list(u_sol)
                    is_operating_point = True
                else:
                    # fsolve didn't converge — report error
                    x_str = ", ".join(f"{v:.4f}" for v in x_eq)
                    return {
                        "latex_steps": latex_steps,
                        "error": (
                            f"Cannot find u* such that f(x*, u*) = 0 at x* = ({x_str}). "
                            "Try a different operating point."
                        ),
                        "system_order": n_states,
                        "n_inputs": max(m_inputs, 1),
                        "n_outputs": p_outputs,
                        "is_siso": (m_inputs <= 1 and p_outputs == 1),
                        "preset_name": preset_name,
                    }
            except Exception as exc:
                return {
                    "latex_steps": latex_steps,
                    "error": f"Operating point solver failed: {exc}",
                    "system_order": n_states,
                    "n_inputs": max(m_inputs, 1),
                    "n_outputs": p_outputs,
                    "is_siso": (m_inputs <= 1 and p_outputs == 1),
                    "preset_name": preset_name,
                }

            # Display operating point
            x_vals_str = ", ".join(
                f"x_{{{i+1}}}^* = {x_eq[i]:.4f}" for i in range(n_states)
            )
            u_vals_str = ", ".join(
                f"u_{{{i+1}}}^* = {u_eq_vals[i]:.4f}" for i in range(m_inputs)
            )
            latex_steps.append({
                "title": "② Operating Point",
                "latex": (
                    f"\\begin{{aligned}} &{x_vals_str} \\\\ &{u_vals_str} \\end{{aligned}}"
                ),
                "explanation": (
                    "Operating point where ẋ = 0 with nonzero steady-state input u*. "
                    "The system is solved for the input required to maintain x* = const."
                ),
            })

            real_solutions = [tuple(x_eq)]
            sel_idx = 0

        else:
            # Zero-input mode: find equilibria with u = 0
            f_at_u0 = [expr.subs(u_zero_subs) for expr in f_exprs]
            real_solutions = self._find_equilibria_nd(f_at_u0, x_syms_used, eq_hint)

            if real_solutions:
                eq_display_parts = []
                for i, sol in enumerate(real_solutions):
                    vals = ", ".join(f"{v:.4f}" for v in sol)
                    eq_display_parts.append(
                        f"\\bar{{\\mathbf{{x}}}}_{{{i+1}}} &= ({vals})"
                    )
                eq_display = (
                    "\\begin{aligned}"
                    + " \\\\ ".join(eq_display_parts)
                    + "\\end{aligned}"
                )
            else:
                eq_display = "\\text{No real equilibria found — using origin}"
                real_solutions = [tuple(0.0 for _ in range(n_states))]

            latex_steps.append({
                "title": f"② Equilibrium Points ({len(real_solutions)} found)",
                "latex": eq_display,
                "explanation": (
                    "Zero-input equilibria where ẋ = 0 with u = 0. "
                    "Switch to Operating Point mode for systems requiring "
                    "nonzero steady-state input."
                ),
            })

            sel_idx = min(eq_idx, len(real_solutions) - 1)
            x_eq = list(real_solutions[sel_idx])

        # Step 3: Show selected linearization point
        eq_vals = ", ".join(
            f"\\bar{{x}}_{{{i+1}}} = {x_eq[i]:.4f}" for i in range(n_states)
        )
        point_label = "Operating Point" if is_operating_point else f"Equilibrium #{sel_idx + 1}"
        latex_steps.append({
            "title": f"③ Selected {point_label}",
            "latex": eq_vals,
            "explanation": "Linearization point.",
        })

        # Step 4: Jacobian (symbolic)
        f_vec = sp.Matrix(f_exprs)
        x_vec_sym = sp.Matrix(x_syms_used)

        A_sym = f_vec.jacobian(x_vec_sym)

        if m_inputs > 0:
            u_vec_sym = sp.Matrix(u_syms_used)
            B_sym = f_vec.jacobian(u_vec_sym)
        else:
            B_sym = sp.zeros(n_states, 1)

        # Show A Jacobian (cap at n<=4 for display)
        if n_states <= 4:
            latex_steps.append({
                "title": "④ Jacobian A (Symbolic)",
                "latex": (
                    "A = \\frac{\\partial \\mathbf{f}}{\\partial \\mathbf{x}} = "
                    f"{sp.latex(A_sym)}"
                ),
                "explanation": f"The {n_states}×{n_states} state Jacobian matrix.",
            })

        # Evaluate at equilibrium/operating point
        subs_dict = {x_syms_used[i]: x_eq[i] for i in range(n_states)}
        for i, u_s in enumerate(u_syms_used):
            subs_dict[u_s] = u_eq_vals[i] if i < len(u_eq_vals) else 0.0
        subs_dict[_u_sym] = u_eq_vals[0] if u_eq_vals else 0.0  # legacy u

        A_num_sym = A_sym.subs(subs_dict).evalf()
        B_num_sym = B_sym.subs(subs_dict).evalf()

        # Output Jacobians
        h_vec = sp.Matrix(h_exprs)
        C_sym = h_vec.jacobian(x_vec_sym)
        if m_inputs > 0:
            D_sym = h_vec.jacobian(sp.Matrix(u_syms_used))
        else:
            D_sym = sp.zeros(p_outputs, 1)
        C_num_sym = C_sym.subs(subs_dict).evalf()
        D_num_sym = D_sym.subs(subs_dict).evalf()

        def _to_np(m: sp.Matrix) -> np.ndarray:
            return np.array([[complex(v).real for v in row] for row in m.tolist()], dtype=float)

        A_np = _to_np(A_num_sym)
        B_np = _to_np(B_num_sym)
        C_np = _to_np(C_num_sym)
        D_np = _to_np(D_num_sym)

        # Ensure B has correct shape for autonomous systems
        if m_inputs == 0:
            B_np = np.zeros((n_states, 1))
            D_np = np.zeros((p_outputs, 1))

        # Guard: Jacobian may contain inf/NaN at singular equilibria
        # (e.g., √(x+ε) at x = -ε has d/dx = 1/(2√0) = ∞)
        if not np.all(np.isfinite(A_np)) or not np.all(np.isfinite(B_np)):
            eq_str = ", ".join(f"{v:.4f}" for v in x_eq)
            latex_steps.append({
                "title": "⑤ Jacobian Singularity",
                "latex": "A \\text{ or } B \\text{ contains } \\pm\\infty",
                "explanation": (
                    f"The Jacobian is singular at ({eq_str}). "
                    "This equilibrium is at a non-differentiable point — "
                    "linearization is not valid here. "
                    "Select a different equilibrium or operating point."
                ),
            })
            singular_result = {
                "latex_steps": latex_steps,
                "equilibrium_points": [list(sol) for sol in real_solutions],
                "selected_eq_idx": sel_idx,
                "system_order": n_states,
                "n_inputs": max(m_inputs, 1),
                "n_outputs": p_outputs,
                "is_siso": (m_inputs <= 1 and p_outputs == 1),
                "preset_name": preset_name,
                "x1_eq": float(x_eq[0]),
                "x2_eq": float(x_eq[1]) if n_states >= 2 else 0.0,
                "error": (
                    f"Jacobian contains ∞ at equilibrium ({eq_str}) — "
                    "linearization not possible at a non-differentiable point"
                ),
            }
            # Include phase portrait functions so the plot still renders
            if n_states >= 2:
                singular_result["f1_str"] = f_strs[0]
                singular_result["f2_str"] = f_strs[1]
                partial_subs = {}
                for i in range(2, n_states):
                    partial_subs[x_syms_used[i]] = x_eq[i]
                for i, u_s in enumerate(u_syms_used):
                    partial_subs[u_s] = u_eq_vals[i] if i < len(u_eq_vals) else 0.0
                partial_subs[_u_sym] = u_eq_vals[0] if u_eq_vals else 0.0
                f1_2d = f_exprs[0].subs(partial_subs)
                f2_2d = f_exprs[1].subs(partial_subs)
                singular_result["_f1_func"] = sp.lambdify(
                    [x_syms_used[0], x_syms_used[1], _u_sym], f1_2d, modules="numpy"
                )
                singular_result["_f2_func"] = sp.lambdify(
                    [x_syms_used[0], x_syms_used[1], _u_sym], f2_2d, modules="numpy"
                )
            return singular_result

        if n_states <= 6:
            A_eval_lat = self._matrix_to_latex(A_np)
            B_eval_lat = self._matrix_to_latex(B_np)
            latex_steps.append({
                "title": "⑤ Evaluated Matrices at Equilibrium",
                "latex": f"A = {A_eval_lat}, \\quad B = {B_eval_lat}",
                "explanation": "Numerical Jacobian values at the selected equilibrium.",
            })

        # Linearized system
        latex_steps.append({
            "title": "⑥ Linearized State-Space System",
            "latex": (
                "\\begin{aligned}"
                "\\delta\\dot{\\mathbf{x}} &= A\\,\\delta\\mathbf{x} + B\\,\\delta\\mathbf{u} \\\\"
                "\\delta\\mathbf{y} &= C\\,\\delta\\mathbf{x} + D\\,\\delta\\mathbf{u}"
                "\\end{aligned}"
            ),
            "explanation": "Local linear approximation around the equilibrium.",
        })

        # Eigenvalues & stability
        eigenvalues = np.linalg.eigvals(A_np)
        is_stable = bool(np.all(eigenvalues.real < -1e-10))
        is_marginal_nl = bool(np.all(eigenvalues.real <= 1e-10) and not is_stable)

        eig_parts = []
        for r, im in zip(eigenvalues.real, eigenvalues.imag):
            idx = len(eig_parts) + 1
            if abs(im) < 1e-10:
                eig_parts.append(f"\\lambda_{{{idx}}} = {r:.4f}")
            elif im > 0:
                eig_parts.append(f"\\lambda_{{{idx}}} = {r:.4f} + {im:.4f}j")
            else:
                eig_parts.append(f"\\lambda_{{{idx}}} = {r:.4f} - {abs(im):.4f}j")

        stability_note = (
            "\\text{Asymptotically stable}" if is_stable
            else "\\text{Marginally stable}" if is_marginal_nl
            else "\\text{Unstable}"
        )
        eig_latex_nl = (
            "\\begin{aligned}"
            + " \\\\ ".join(f"&{e}" for e in eig_parts)
            + " \\\\ &" + stability_note
            + "\\end{aligned}"
        )
        latex_steps.append({
            "title": "⑦ Eigenvalues & Local Stability",
            "latex": eig_latex_nl,
            "explanation": "Hartman–Grobman theorem: stability of linearization predicts local nonlinear behavior.",
        })

        is_siso = (m_inputs <= 1 and p_outputs == 1)

        result = {
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
            "equilibrium_points": [list(sol) for sol in real_solutions],
            "selected_eq_idx": sel_idx,
            "system_order": n_states,
            "n_inputs": max(m_inputs, 1),
            "n_outputs": p_outputs,
            "is_siso": is_siso,
            "preset_name": preset_name,
            # Phase portrait data (for n>=2)
            "x1_eq": float(x_eq[0]),
            "x2_eq": float(x_eq[1]) if n_states >= 2 else 0.0,
        }

        # Pass lambdified f1/f2 for phase portrait (always 2D projection)
        if n_states >= 2:
            result["f1_str"] = f_strs[0]
            result["f2_str"] = f_strs[1]
            # Build 2-arg lambdified functions for phase portrait
            # These only use x1, x2 (other states = eq values, u = u_eq)
            partial_subs = {}
            for i in range(2, n_states):
                partial_subs[x_syms_used[i]] = x_eq[i]
            for i, u_s in enumerate(u_syms_used):
                partial_subs[u_s] = u_eq_vals[i] if i < len(u_eq_vals) else 0.0
            partial_subs[_u_sym] = u_eq_vals[0] if u_eq_vals else 0.0

            f1_2d = f_exprs[0].subs(partial_subs)
            f2_2d = f_exprs[1].subs(partial_subs)
            result["_f1_func"] = sp.lambdify(
                [x_syms_used[0], x_syms_used[1], _u_sym], f1_2d, modules="numpy"
            )
            result["_f2_func"] = sp.lambdify(
                [x_syms_used[0], x_syms_used[1], _u_sym], f2_2d, modules="numpy"
            )

        return result

    def _find_equilibria_nd(
        self,
        f_exprs: List[sp.Expr],
        x_syms: List[sp.Symbol],
        eq_hint: Optional[List[float]] = None,
    ) -> List[Tuple[float, ...]]:
        """Find equilibria for N-dimensional system.

        Uses symbolic solve with timeout, then numerical fsolve fallback.
        """
        n = len(x_syms)

        # Add hint as first candidate if it actually satisfies f(hint) ≈ 0
        hint_solutions: List[Tuple[float, ...]] = []
        if eq_hint is not None and len(eq_hint) == n:
            try:
                f_funcs_check = [
                    sp.lambdify(x_syms, expr, modules=[
                        {"sqrt": lambda x: np.sqrt(np.maximum(x, 0.0))}, "numpy"
                    ]) for expr in f_exprs
                ]
                residuals = [float(f(*eq_hint)) for f in f_funcs_check]
                if all(abs(r) < 0.01 for r in residuals):
                    hint_solutions.append(tuple(eq_hint))
            except Exception:
                pass  # Skip invalid hint

        # Try symbolic solve (with timeout for complex systems)
        symbolic_result: List[Dict] = []
        solved = threading.Event()
        timeout = 3 if n > 2 else 6  # Shorter timeout for higher dimensions

        def _sympy_solve():
            try:
                symbolic_result.extend(sp.solve(f_exprs, x_syms, dict=True))
            except Exception:
                pass
            solved.set()

        t = threading.Thread(target=_sympy_solve, daemon=True)
        t.start()
        symbolic_ok = solved.wait(timeout=timeout)

        real_sols: List[Tuple[float, ...]] = list(hint_solutions)
        if symbolic_ok and symbolic_result:
            for sol in symbolic_result:
                vals = []
                all_real = True
                for x_s in x_syms:
                    v = complex(sol.get(x_s, 0))
                    if abs(v.imag) > 1e-6:
                        all_real = False
                        break
                    vals.append(float(v.real))
                if all_real:
                    tup = tuple(vals)
                    # Deduplicate
                    if all(sum(abs(a - b) for a, b in zip(tup, existing)) > 0.01
                           for existing in real_sols):
                        real_sols.append(tup)

        if real_sols:
            return real_sols[:5]

        # Numerical fallback
        try:
            from scipy.optimize import fsolve
            f_funcs = [sp.lambdify(x_syms, expr, modules="numpy") for expr in f_exprs]

            def system(z):
                return [float(f_funcs[i](*z)) for i in range(n)]

            # Adaptive grid: sparser for higher dimensions
            grid_size = max(3, 7 - n)
            grid_vals = np.linspace(-np.pi, np.pi, grid_size)

            found: List[Tuple[float, ...]] = []
            # Generate grid points (limit total evaluations)
            from itertools import product as iter_product
            grid_points = list(iter_product(grid_vals, repeat=n))[:200]

            for guess in grid_points:
                try:
                    sol_num, _, ier, _ = fsolve(system, list(guess), full_output=True)
                    if ier == 1:
                        tup = tuple(float(v) for v in sol_num)
                        if all(sum(abs(a - b) for a, b in zip(tup, existing)) > 0.01
                               for existing in found):
                            res = system(list(tup))
                            if all(abs(r) < 1e-6 for r in res):
                                found.append(tup)
                except Exception:
                    pass
            return found[:5] if found else [tuple(0.0 for _ in range(n))]
        except Exception:
            return [tuple(0.0 for _ in range(n))]

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
                    ss = float((C_ss @ np.linalg.solve(-A_ss, B_ss) + D_ss).item())
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

    def _impulse_response_plot(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Impulse response h(t) using scipy.signal.impulse."""
        try:
            A = np.array(data["A"], dtype=float)
            B = np.array(data["B"], dtype=float)
            C = np.array(data["C"], dtype=float)
            D = np.array(data["D"], dtype=float)

            sys_ss = signal.StateSpace(A, B, C, D)
            t = np.linspace(0, 15, 1000)
            t_out, y_out = signal.impulse(sys_ss, T=t)
            y_flat = y_out.flatten()

            clip_mag = 200.0
            y_clipped = np.clip(y_flat, -clip_mag, clip_mag)

            traces = [{
                "x": t_out.tolist(),
                "y": y_clipped.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": "h(t)",
                "line": {"color": "#8b5cf6", "width": 2.5},
                "hovertemplate": "t = %{x:.3f} s<br>h(t) = %{y:.4f}<extra></extra>",
            }]

            uirev = (
                f"impulse-{self.parameters.get('system_type')}"
                f"-{self.parameters.get('preset')}"
            )

            return {
                "id": "impulse_response",
                "title": "Impulse Response",
                "data": traces,
                "layout": {
                    "xaxis": {
                        "title": "Time [s]",
                        "gridcolor": "rgba(148,163,184,0.1)",
                        "zerolinecolor": "rgba(148,163,184,0.3)",
                        "color": "#f1f5f9",
                    },
                    "yaxis": {
                        "title": "h(t)",
                        "gridcolor": "rgba(148,163,184,0.1)",
                        "zerolinecolor": "rgba(148,163,184,0.3)",
                        "color": "#f1f5f9",
                        "autorange": True,
                    },
                    "paper_bgcolor": "rgba(0,0,0,0)",
                    "plot_bgcolor": "rgba(0,0,0,0)",
                    "font": {
                        "family": "Inter, sans-serif",
                        "size": 12,
                        "color": "#f1f5f9",
                    },
                    "margin": {"t": 45, "r": 25, "b": 55, "l": 60},
                    "showlegend": True,
                    "legend": {
                        "font": {"color": "#94a3b8"},
                        "bgcolor": "rgba(0,0,0,0.3)",
                    },
                    "uirevision": uirev,
                },
            }
        except Exception as exc:
            return {
                "id": "impulse_response",
                "title": "Impulse Response (N/A)",
                "data": [],
                "layout": {
                    "paper_bgcolor": "rgba(0,0,0,0)",
                    "plot_bgcolor": "rgba(0,0,0,0)",
                    "annotations": [{
                        "text": f"Cannot compute: {str(exc)[:100]}",
                        "xref": "paper", "yref": "paper",
                        "x": 0.5, "y": 0.5,
                        "showarrow": False,
                        "font": {"color": "#94a3b8", "size": 13},
                    }],
                },
            }

    def _bode_plots(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Bode magnitude and phase plots using scipy.signal.bode.

        Returns a list of two plot dicts: [bode_magnitude, bode_phase].
        """
        try:
            A = np.array(data["A"], dtype=float)
            B = np.array(data["B"], dtype=float)
            C = np.array(data["C"], dtype=float)
            D = np.array(data["D"], dtype=float)

            sys_ss = signal.StateSpace(A, B, C, D)
            w, mag, phase = signal.bode(sys_ss, n=500)

            uirev_base = (
                f"bode-{self.parameters.get('system_type')}"
                f"-{self.parameters.get('preset')}"
            )

            # -3 dB line for reference
            mag_traces = [
                {
                    "x": w.tolist(),
                    "y": mag.tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "name": "|H(j\u03c9)| [dB]",
                    "line": {"color": "#3b82f6", "width": 2.5},
                    "hovertemplate": (
                        "\u03c9 = %{x:.4g} rad/s<br>"
                        "|H| = %{y:.2f} dB<extra></extra>"
                    ),
                },
            ]
            # Add 0 dB reference
            mag_traces.append({
                "x": [float(w[0]), float(w[-1])],
                "y": [0.0, 0.0],
                "type": "scatter",
                "mode": "lines",
                "name": "0 dB",
                "line": {"color": "rgba(148,163,184,0.4)", "width": 1, "dash": "dash"},
                "hoverinfo": "skip",
                "showlegend": False,
            })

            magnitude_plot = {
                "id": "bode_magnitude",
                "title": "Bode \u2014 Magnitude",
                "data": mag_traces,
                "layout": {
                    "xaxis": {
                        "title": "Frequency [rad/s]",
                        "type": "log",
                        "gridcolor": "rgba(148,163,184,0.1)",
                        "zerolinecolor": "rgba(148,163,184,0.3)",
                        "color": "#f1f5f9",
                    },
                    "yaxis": {
                        "title": "Magnitude [dB]",
                        "gridcolor": "rgba(148,163,184,0.1)",
                        "zerolinecolor": "rgba(148,163,184,0.3)",
                        "color": "#f1f5f9",
                    },
                    "paper_bgcolor": "rgba(0,0,0,0)",
                    "plot_bgcolor": "rgba(0,0,0,0)",
                    "font": {
                        "family": "Inter, sans-serif",
                        "size": 12,
                        "color": "#f1f5f9",
                    },
                    "margin": {"t": 45, "r": 25, "b": 55, "l": 60},
                    "showlegend": True,
                    "legend": {
                        "font": {"color": "#94a3b8"},
                        "bgcolor": "rgba(0,0,0,0.3)",
                    },
                    "uirevision": f"{uirev_base}-mag",
                },
            }

            # Phase plot
            phase_traces = [
                {
                    "x": w.tolist(),
                    "y": phase.tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "name": "\u2220H(j\u03c9) [\u00b0]",
                    "line": {"color": "#ef4444", "width": 2.5},
                    "hovertemplate": (
                        "\u03c9 = %{x:.4g} rad/s<br>"
                        "\u2220H = %{y:.1f}\u00b0<extra></extra>"
                    ),
                },
            ]
            # -180 deg reference
            phase_traces.append({
                "x": [float(w[0]), float(w[-1])],
                "y": [-180.0, -180.0],
                "type": "scatter",
                "mode": "lines",
                "name": "-180\u00b0",
                "line": {"color": "rgba(239,68,68,0.3)", "width": 1, "dash": "dash"},
                "hoverinfo": "skip",
                "showlegend": False,
            })

            phase_plot = {
                "id": "bode_phase",
                "title": "Bode \u2014 Phase",
                "data": phase_traces,
                "layout": {
                    "xaxis": {
                        "title": "Frequency [rad/s]",
                        "type": "log",
                        "gridcolor": "rgba(148,163,184,0.1)",
                        "zerolinecolor": "rgba(148,163,184,0.3)",
                        "color": "#f1f5f9",
                    },
                    "yaxis": {
                        "title": "Phase [\u00b0]",
                        "gridcolor": "rgba(148,163,184,0.1)",
                        "zerolinecolor": "rgba(148,163,184,0.3)",
                        "color": "#f1f5f9",
                    },
                    "paper_bgcolor": "rgba(0,0,0,0)",
                    "plot_bgcolor": "rgba(0,0,0,0)",
                    "font": {
                        "family": "Inter, sans-serif",
                        "size": 12,
                        "color": "#f1f5f9",
                    },
                    "margin": {"t": 45, "r": 25, "b": 55, "l": 60},
                    "showlegend": True,
                    "legend": {
                        "font": {"color": "#94a3b8"},
                        "bgcolor": "rgba(0,0,0,0.3)",
                    },
                    "uirevision": f"{uirev_base}-phase",
                },
            }

            return [magnitude_plot, phase_plot]

        except Exception:
            return []

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

        # Mark all equilibrium points (project to first 2 states)
        eq_pts = data.get("equilibrium_points", [[x1_eq, x2_eq]])
        sel_idx = data.get("selected_eq_idx", 0)
        for i, eq_pt in enumerate(eq_pts):
            ex1 = float(eq_pt[0]) if len(eq_pt) > 0 else 0.0
            ex2 = float(eq_pt[1]) if len(eq_pt) > 1 else 0.0
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
