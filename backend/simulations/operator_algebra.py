"""
Operator Algebra Visualizer Simulator

Converts between three equivalent representations of discrete-time systems
using the R-operator (right-shift/delay operator):
  - Operator polynomial: P(R) = 1 - 2R + R^2
  - Difference equation: y[n] = x[n] - 2x[n-1] + x[n-2]
  - Impulse response: h[n] = {1, -2, 1, 0, 0, ...}

Based on MIT 6.003 Lecture 2 (Discrete-Time Systems).
"""

import ast
import re
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from numpy.polynomial import polynomial as P

from .base_simulator import BaseSimulator


# ── Safe expression evaluator ──────────────────────────────────────────────

class _PolyWrapper:
    """Thin wrapper around coefficient arrays supporting +, -, *, **."""

    __slots__ = ("c",)

    def __init__(self, coeffs):
        if isinstance(coeffs, (int, float)):
            self.c = np.array([float(coeffs)])
        elif isinstance(coeffs, np.ndarray):
            self.c = coeffs.astype(float)
        else:
            self.c = np.array(coeffs, dtype=float)

    # Trim trailing zeros for cleanliness
    def _trim(self):
        c = np.trim_zeros(self.c, "b")
        if len(c) == 0:
            self.c = np.array([0.0])
        else:
            self.c = c
        return self

    def __add__(self, other):
        other = _ensure_poly(other)
        return _PolyWrapper(P.polyadd(self.c, other.c))._trim()

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        other = _ensure_poly(other)
        return _PolyWrapper(P.polysub(self.c, other.c))._trim()

    def __rsub__(self, other):
        other = _ensure_poly(other)
        return _PolyWrapper(P.polysub(other.c, self.c))._trim()

    def __mul__(self, other):
        other = _ensure_poly(other)
        return _PolyWrapper(P.polymul(self.c, other.c))._trim()

    def __rmul__(self, other):
        return self.__mul__(other)

    def __pow__(self, exp):
        if not isinstance(exp, int) or exp < 0:
            raise ValueError("Exponent must be a non-negative integer")
        if exp > 20:
            raise ValueError("Exponent too large (max 20)")
        result = _PolyWrapper([1.0])
        for _ in range(exp):
            result = result * self
        return result._trim()

    def __neg__(self):
        return _PolyWrapper(-self.c)

    def __pos__(self):
        return _PolyWrapper(self.c.copy())


def _ensure_poly(x) -> _PolyWrapper:
    if isinstance(x, _PolyWrapper):
        return x
    return _PolyWrapper(x)


# Allowed AST node types for safe evaluation
_SAFE_NODES = (
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant, ast.Name,
    ast.Add, ast.Sub, ast.Mult, ast.Pow, ast.USub, ast.UAdd,
    ast.Load,  # context node on Name
)


def _validate_ast(node: ast.AST) -> None:
    """Recursively validate that the AST only contains safe nodes."""
    if not isinstance(node, _SAFE_NODES):
        raise ValueError(f"Unsupported expression element: {type(node).__name__}")
    for child in ast.iter_child_nodes(node):
        _validate_ast(child)


def _eval_ast(node: ast.AST, R: _PolyWrapper):
    """Recursively evaluate a validated AST with R as the polynomial variable."""
    if isinstance(node, ast.Expression):
        return _eval_ast(node.body, R)
    if isinstance(node, ast.Constant):
        if not isinstance(node.value, (int, float)):
            raise ValueError(f"Only numeric constants allowed, got {type(node.value).__name__}")
        return _PolyWrapper(node.value)
    if isinstance(node, ast.Name):
        if node.id != "R":
            raise ValueError(f"Unknown variable '{node.id}'. Only 'R' is allowed.")
        return R
    if isinstance(node, ast.UnaryOp):
        operand = _eval_ast(node.operand, R)
        if isinstance(node.op, ast.USub):
            return -operand
        if isinstance(node.op, ast.UAdd):
            return +operand
    if isinstance(node, ast.BinOp):
        left = _eval_ast(node.left, R)
        right = _eval_ast(node.right, R)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Pow):
            # Right side of ** must be a plain integer
            if isinstance(right, _PolyWrapper) and len(right.c) == 1:
                exp = int(right.c[0])
                return left ** exp
            raise ValueError("Exponent must be a constant integer")
    raise ValueError(f"Cannot evaluate node: {type(node).__name__}")


def _normalize_expression(expr: str) -> str:
    """Normalize user input into valid Python expression syntax."""
    s = expr.strip()
    if not s:
        raise ValueError("Expression is empty")

    # Replace ^ with **
    s = s.replace("^", "**")

    # Replace unicode superscripts
    superscript_map = {"²": "**2", "³": "**3", "⁴": "**4", "⁵": "**5"}
    for sup, repl in superscript_map.items():
        s = s.replace(sup, repl)

    # Insert implicit multiplication:
    # digit before R:  2R  → 2*R
    s = re.sub(r"(\d)\s*([R])", r"\1*\2", s)
    # R before digit that's NOT after **: R2 → error? No, treat as R*2 (unlikely but safe)
    # Actually R2 is ambiguous. Skip this — users should write R^2 or R**2.
    # ) before ( or R or digit:  )(  → )*(,   )R → )*R,   )2 → )*2
    s = re.sub(r"\)\s*\(", r")*(", s)
    s = re.sub(r"\)\s*([R\d])", r")*\1", s)
    # R before (:  R(  → R*(
    s = re.sub(r"([R])\s*\(", r"\1*(", s)
    # digit before (:  2(  → 2*(
    s = re.sub(r"(\d)\s*\(", r"\1*(", s)
    # ) before R:  already handled above

    return s


def parse_expression(expr: str) -> np.ndarray:
    """
    Parse an R-operator expression and return coefficient array.

    Args:
        expr: Expression string like '(1-R)^2' or '1 - 2R + R^2'

    Returns:
        NumPy array of coefficients [c0, c1, c2, ...] where ck is
        the coefficient of R^k. This is also the impulse response.

    Raises:
        ValueError: If expression is invalid or unsafe.
    """
    normalized = _normalize_expression(expr)

    try:
        tree = ast.parse(normalized, mode="eval")
    except SyntaxError as e:
        raise ValueError(f"Invalid expression syntax: {e.msg}") from e

    _validate_ast(tree)

    R = _PolyWrapper([0.0, 1.0])  # R = 0 + 1*R (ascending power order)
    result = _eval_ast(tree, R)

    if isinstance(result, (int, float)):
        return np.array([float(result)])

    coeffs = result.c
    # Round near-integer coefficients
    rounded = np.round(coeffs)
    mask = np.abs(coeffs - rounded) < 1e-10
    coeffs[mask] = rounded[mask]

    return coeffs


# ── Formatting helpers ──────────────────────────────────────────────────────

def _format_coeff(c: float, power: int, is_first: bool) -> str:
    """Format a single term c*R^power for display."""
    if abs(c) < 1e-12:
        return ""

    # Determine sign prefix
    if is_first:
        sign = "-" if c < 0 else ""
    else:
        sign = " - " if c < 0 else " + "

    ac = abs(c)
    # Format the coefficient value
    if ac == int(ac):
        ac_str = str(int(ac))
    else:
        ac_str = f"{ac:.4g}"

    if power == 0:
        return f"{sign}{ac_str}"
    elif power == 1:
        if ac == 1.0:
            return f"{sign}R"
        return f"{sign}{ac_str}R"
    else:
        if ac == 1.0:
            return f"{sign}R^{power}"
        return f"{sign}{ac_str}R^{power}"


def format_expanded(coeffs: np.ndarray) -> str:
    """Format coefficients as expanded polynomial string."""
    if len(coeffs) == 0 or np.all(np.abs(coeffs) < 1e-12):
        return "0"

    terms = []
    first = True
    for i, c in enumerate(coeffs):
        term = _format_coeff(c, i, first)
        if term:
            terms.append(term)
            first = False

    return "".join(terms) if terms else "0"


def format_difference_equation(coeffs: np.ndarray) -> str:
    """Format coefficients as a difference equation y[n] = ..."""
    if len(coeffs) == 0 or np.all(np.abs(coeffs) < 1e-12):
        return "y[n] = 0"

    terms = []
    first = True
    for i, c in enumerate(coeffs):
        if abs(c) < 1e-12:
            continue

        # Sign
        if first:
            sign = "-" if c < 0 else ""
        else:
            sign = " - " if c < 0 else " + "

        ac = abs(c)
        if ac == int(ac):
            ac_str = str(int(ac))
        else:
            ac_str = f"{ac:.4g}"

        # x[n-i] term
        if i == 0:
            x_term = "x[n]"
        else:
            x_term = f"x[n-{i}]"

        if ac == 1.0:
            terms.append(f"{sign}{x_term}")
        else:
            terms.append(f"{sign}{ac_str}{x_term}")

        first = False

    rhs = "".join(terms) if terms else "0"
    return f"y[n] = {rhs}"


def _snap_root(r: float) -> float:
    """Snap a root to a clean value if it's close to one.

    Uses generous tolerance because polyroots can be imprecise
    for repeated roots (e.g., triple root gives ~1e-5 error).
    """
    tol = 1e-4
    # Try integers first
    ri = round(r)
    if abs(r - ri) < tol:
        return float(ri)
    # Try halves: ±0.5, ±1.5, ...
    rh = round(r * 2) / 2.0
    if abs(r - rh) < tol:
        return rh
    # Try thirds
    rt = round(r * 3) / 3.0
    if abs(r - rt) < tol:
        return rt
    # Try quarters
    rq = round(r * 4) / 4.0
    if abs(r - rq) < tol:
        return rq
    return r


def format_factored(coeffs: np.ndarray) -> str:
    """
    Attempt to factor the polynomial into a readable product form.

    Returns the factored string, or the expanded form if factoring
    doesn't simplify nicely.
    """
    degree = len(coeffs) - 1
    if degree <= 0:
        c = coeffs[0] if len(coeffs) > 0 else 0
        return str(int(c)) if c == int(c) else f"{c:.4g}"

    if degree == 1:
        return format_expanded(coeffs)

    try:
        roots = P.polyroots(coeffs)
    except Exception:
        return format_expanded(coeffs)

    if len(roots) == 0:
        return format_expanded(coeffs)

    # Leading coefficient (coefficient of R^degree)
    leading = coeffs[-1]

    # Snap roots to clean values and separate real/complex
    # Use generous tolerance since polyroots can introduce small imaginary parts
    # for repeated real roots (e.g., triple root at 1 gives imag ~1e-5)
    snapped = []
    for r in roots:
        if abs(r.imag) > 1e-3:
            # Genuinely complex root — fall back to expanded form
            return format_expanded(coeffs)
        snapped.append(_snap_root(r.real))

    # Group by value (tolerance 1e-6) to find multiplicities
    snapped_sorted = sorted(snapped)
    root_groups: List[Tuple[float, int]] = []
    i = 0
    while i < len(snapped_sorted):
        r = snapped_sorted[i]
        mult = 1
        while i + mult < len(snapped_sorted) and abs(snapped_sorted[i + mult] - r) < 1e-6:
            mult += 1
        root_groups.append((r, mult))
        i += mult

    # Build factor strings
    # P(R) = leading * ∏(R - rᵢ)^mᵢ
    # We rewrite each (R - rᵢ) in user-friendly form, tracking sign/coeff changes.
    factors = []
    coeff_adjustment = 1.0  # multiplicative adjustment from rewriting factors

    for root_val, mult in root_groups:
        if root_val == 0.0:
            # (R - 0) = R
            factor_str = "R"
        elif root_val == 1.0:
            # (R - 1) = -(1 - R), sign flip per occurrence
            factor_str = "(1 - R)"
            coeff_adjustment *= (-1) ** mult
        elif root_val == -1.0:
            # (R + 1) = (1 + R)
            factor_str = "(1 + R)"
        else:
            # Try to write as (aR + b) with integer a, b
            # (R - r) = (1/a)(aR - ar) where a*r should be integer
            # We want aR + b where b = -a*r
            found_int_form = False
            for a in range(1, 7):
                b = -a * root_val
                if abs(b - round(b)) < 1e-8:
                    b = int(round(b))
                    if a == 1:
                        if b > 0:
                            factor_str = f"(R + {b})"
                        else:
                            factor_str = f"(R - {abs(b)})"
                    else:
                        if b > 0:
                            factor_str = f"({a}R + {b})"
                        elif b < 0:
                            factor_str = f"({a}R - {abs(b)})"
                        else:
                            factor_str = f"{a}R"
                        # Each (R - r) = (1/a)(aR + b), contributes 1/a
                        coeff_adjustment *= (1.0 / a) ** mult
                    found_int_form = True
                    break

            if not found_int_form:
                # Fall back to decimal representation
                if root_val > 0:
                    factor_str = f"(R - {root_val:.4g})"
                else:
                    factor_str = f"(R + {abs(root_val):.4g})"

        if mult > 1:
            factor_str = f"{factor_str}^{mult}"

        factors.append(factor_str)

    # Effective leading coefficient after all rewriting
    effective_leading = leading * coeff_adjustment

    # Round if close to integer
    if abs(effective_leading - round(effective_leading)) < 1e-8:
        effective_leading = round(effective_leading)

    # Build prefix
    if abs(effective_leading - 1.0) < 1e-10:
        prefix = ""
    elif abs(effective_leading - (-1.0)) < 1e-10:
        prefix = "-"
    elif effective_leading == int(effective_leading):
        prefix = f"{int(effective_leading)}"
    else:
        prefix = f"{effective_leading:.4g}"

    result = prefix + "".join(factors)

    # Verify by re-parsing and comparing coefficients
    try:
        verify_coeffs = parse_expression(result)
        if len(verify_coeffs) == len(coeffs) and np.allclose(verify_coeffs, coeffs, atol=1e-8):
            return result
    except Exception:
        pass

    # Verification failed — return expanded form
    return format_expanded(coeffs)


# ── Simulator ───────────────────────────────────────────────────────────────

class OperatorAlgebraSimulator(BaseSimulator):
    """
    Operator Algebra Visualizer for discrete-time systems.

    Converts R-operator polynomial expressions between representations:
    expanded polynomial, factored form, difference equation, block diagram,
    and impulse response.
    """

    MAX_DEGREE = 20

    PRESETS = {
        "first_diff": {"label": "(1 - R)", "expression": "(1-R)"},
        "second_diff": {"label": "(1 - R)^2", "expression": "(1-R)^2"},
        "smooth_sq": {"label": "(1 + R)^2", "expression": "(1+R)^2"},
        "diff_of_sq": {"label": "(1 - R)(1 + R)", "expression": "(1-R)(1+R)"},
        "moving_avg": {"label": "(1 + R + R^2)", "expression": "(1+R+R^2)"},
        "pure_delay": {"label": "R^3", "expression": "R^3"},
        "third_diff": {"label": "(1 - R)^3", "expression": "(1-R)^3"},
        "weighted": {"label": "(2R + 1)^2", "expression": "(2*R+1)^2"},
    }

    PARAMETER_SCHEMA = {
        "expression": {
            "type": "expression",
            "default": "(1-R)^2",
            "placeholder": "Enter R-operator expression, e.g. (1-R)^2",
        },
        "num_samples": {
            "type": "slider",
            "min": 5,
            "max": 40,
            "default": 15,
            "step": 1,
        },
    }

    DEFAULT_PARAMS = {
        "expression": "(1-R)^2",
        "num_samples": 15,
    }

    def initialize(self, params: Optional[Dict[str, Any]] = None) -> None:
        self.parameters = {**self.DEFAULT_PARAMS, **(params or {})}
        for name, value in self.parameters.items():
            self.parameters[name] = self._validate_param(name, value)
        self._cached_data: Optional[Dict[str, Any]] = None
        self._initialized = True

    def reset(self) -> Dict[str, Any]:
        """Reset all parameters to defaults and clear cached state."""
        self.parameters = self.DEFAULT_PARAMS.copy()
        self._cached_data = None
        self._initialized = True
        return self.get_state()

    def update_parameter(self, name: str, value: Any) -> Dict[str, Any]:
        if name in self.parameters:
            self.parameters[name] = self._validate_param(name, value)
        self._cached_data = None  # invalidate cache
        return self.get_state()

    def handle_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle custom actions (preset loading, reset)."""
        if action == "load_preset":
            preset_id = params.get("preset_id", "")
            if preset_id in self.PRESETS:
                self.parameters["expression"] = self.PRESETS[preset_id]["expression"]
                self._cached_data = None
        elif action == "init":
            if not self._initialized:
                self.initialize(params)
            else:
                self._cached_data = None
        elif action == "reset":
            return self.reset()
        return self.get_state()

    def _compute(self) -> Dict[str, Any]:
        """Parse expression and compute all representations.

        Results are cached until parameters change (via update_parameter,
        handle_action, or reset which all set _cached_data = None).
        """
        if self._cached_data is not None:
            return self._cached_data

        expr = self.parameters.get("expression", "(1-R)^2")
        num_samples = int(self.parameters.get("num_samples", 15))

        try:
            coeffs = parse_expression(expr)
        except ValueError as e:
            self._cached_data = {
                "error": str(e),
                "coefficients": np.array([0.0]),
                "expanded": "",
                "factored": "",
                "difference_eq": "",
                "degree": 0,
                "impulse_response": np.zeros(num_samples),
                "n_indices": np.arange(num_samples),
            }
            return self._cached_data

        if len(coeffs) - 1 > self.MAX_DEGREE:
            coeffs = coeffs[: self.MAX_DEGREE + 1]

        expanded = format_expanded(coeffs)
        factored = format_factored(coeffs)
        diff_eq = format_difference_equation(coeffs)

        # Impulse response: pad or truncate to num_samples
        h = np.zeros(num_samples)
        n_copy = min(len(coeffs), num_samples)
        h[:n_copy] = coeffs[:n_copy]

        self._cached_data = {
            "error": None,
            "coefficients": coeffs,
            "expanded": expanded,
            "factored": factored,
            "difference_eq": diff_eq,
            "degree": len(coeffs) - 1,
            "impulse_response": h,
            "n_indices": np.arange(num_samples),
        }
        return self._cached_data

    def get_plots(self) -> List[Dict[str, Any]]:
        data = self._compute()
        return [self._create_impulse_plot(data)]

    def get_state(self) -> Dict[str, Any]:
        """Return full state — computes once and reuses for plots + metadata."""
        data = self._compute()

        # Build state manually (avoiding super().get_state() which
        # calls get_plots() → _compute() again)
        return {
            "parameters": self.parameters.copy(),
            "plots": [self._create_impulse_plot(data)],
            "metadata": {
                "simulation_type": "operator_algebra",
                "expanded": data["expanded"],
                "factored": data["factored"],
                "difference_eq": data["difference_eq"],
                "coefficients": data["coefficients"].tolist(),
                "degree": data["degree"],
                "error": data.get("error"),
                "presets": {
                    pid: {"label": p["label"], "expression": p["expression"]}
                    for pid, p in self.PRESETS.items()
                },
            },
        }

    def _create_impulse_plot(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Build Plotly stem plot for impulse response."""
        plot_id = "impulse_response"
        title = "Impulse Response h[n]"

        if data.get("error"):
            layout = self._base_layout("n", "h[n]", plot_id, title)
            return {"id": plot_id, "title": title, "data": [], "layout": layout}

        n = data["n_indices"]
        h = data["impulse_response"]
        num_samples = len(n)

        # Stem plot: vertical lines from 0 to h[n] + markers at top
        traces = []

        # Vertical stems as individual lines
        for i in range(num_samples):
            traces.append({
                "x": [int(n[i]), int(n[i])],
                "y": [0, float(h[i])],
                "type": "scatter",
                "mode": "lines",
                "line": {"color": "#3b82f6", "width": 2},
                "showlegend": False,
                "hoverinfo": "skip",
            })

        # Markers at the top of each stem
        traces.append({
            "x": n.tolist(),
            "y": h.tolist(),
            "type": "scatter",
            "mode": "markers",
            "marker": {
                "color": "#3b82f6",
                "size": 10,
                "line": {"color": "#1e3a5f", "width": 1.5},
            },
            "name": "h[n]",
            "hovertemplate": "n=%{x}<br>h[n]=%{y:.4g}<extra></extra>",
        })

        layout = self._base_layout("n", "h[n]", plot_id, title)

        # Compute sensible y-axis range from the actual data
        h_abs_max = float(max(abs(h.max()), abs(h.min()), 0.5))
        y_pad = h_abs_max * 0.25
        layout["yaxis"]["range"] = [-(h_abs_max + y_pad), h_abs_max + y_pad]
        layout["yaxis"]["autorange"] = False

        layout["xaxis"]["range"] = [-0.5, num_samples - 0.5]
        layout["xaxis"]["dtick"] = max(1, num_samples // 20)
        layout["xaxis"]["autorange"] = False

        # Zero reference line
        layout["shapes"] = [{
            "type": "line",
            "x0": -0.5, "x1": num_samples - 0.5,
            "y0": 0, "y1": 0,
            "line": {"color": "rgba(148,163,184,0.4)", "width": 1, "dash": "dash"},
        }]

        return {"id": plot_id, "title": title, "data": traces, "layout": layout}

    def _base_layout(self, x_title: str, y_title: str,
                     plot_id: str = "", title: str = "") -> Dict[str, Any]:
        """Base Plotly layout with datarevision for forced re-renders."""
        return {
            "xaxis": {
                "title": x_title,
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
                "color": "#f1f5f9",
            },
            "yaxis": {
                "title": y_title,
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
                "color": "#f1f5f9",
            },
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "font": {"family": "Inter, sans-serif", "size": 12, "color": "#f1f5f9"},
            "margin": {"t": 45, "r": 25, "b": 55, "l": 60},
            "showlegend": False,
            # datarevision forces Plotly to re-render when data changes
            "datarevision": f"{plot_id}-{title}-{time.time()}",
            # uirevision preserves user zoom/pan across parameter updates
            "uirevision": plot_id,
        }
