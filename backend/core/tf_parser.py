"""Transfer function expression parser.

Parses textbook-style TF expressions like '(s+1)/(s^2+2s+1)' into
coefficient arrays. Supports:
- Expanded polynomial form: s^2 + 3s + 1
- Factored form: (s+1)(s-2), s(s+1), 2(s+1)(s+3)
- Mixed: leading coefficient * factored product
- G(s) = ... or H(s) = ... prefix stripping
- Comma-separated coefficient strings: '1, 2, 3'

References: Used by root_locus, vector_freq_response, state_space_analyzer.
"""

import re
from typing import Dict, List, Optional, Tuple

import numpy as np


def parse_tf_expression(expr: str) -> Tuple[str, str]:
    """Parse a TF expression into numerator/denominator coefficient strings.

    Args:
        expr: TF expression like '(s+1)/(s^2+2s+1)' or 'G(s) = 10/(s(s+2))'

    Returns:
        (num_coeffs_str, den_coeffs_str) as comma-separated strings
        in descending power order (highest power first).

    Raises:
        ValueError: If the expression cannot be parsed.
    """
    expr = expr.strip()
    # Remove G(s) = or H(s) = prefix
    expr = re.sub(r'[GH]\s*\(\s*s\s*\)\s*=\s*', '', expr).strip()

    # Find the division point — '/' not inside parentheses
    split_idx = _find_top_level_slash(expr)

    if split_idx >= 0:
        num_str = _strip_outer_parens(expr[:split_idx])
        den_str = _strip_outer_parens(expr[split_idx + 1:])
    else:
        num_str = _strip_outer_parens(expr)
        den_str = "1"

    num_coeffs = parse_polynomial_expr(num_str)
    den_coeffs = parse_polynomial_expr(den_str)

    return (
        ", ".join(f"{c:.6g}" for c in num_coeffs),
        ", ".join(f"{c:.6g}" for c in den_coeffs),
    )


def parse_polynomial_expr(poly_str: str) -> List[float]:
    """Parse polynomial expression into coefficient list.

    Supports expanded form ('s^2 + 3s + 1'), factored form ('(s+1)(s+3)'),
    and pure numbers.

    Args:
        poly_str: Polynomial expression string.

    Returns:
        Coefficients in descending power order (highest power first).
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
    factored = _try_parse_factored(poly_str)
    if factored is not None:
        return factored

    # Polynomial form: s^2 + 3s + 1
    return _parse_expanded_poly(poly_str)


def parse_coeff_string(expr_str: str) -> List[float]:
    """Parse comma or space-separated coefficient string.

    Args:
        expr_str: String like '1, 2, 3' or '1 2 3'.

    Returns:
        List of float coefficients.

    Raises:
        ValueError: If string is empty or contains non-numeric values.
    """
    expr_str = expr_str.replace(";", ",")
    parts = [p.strip() for p in expr_str.replace(",", " ").split()]
    if not parts:
        raise ValueError("Empty coefficient string")
    return [float(p) for p in parts if p]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _find_top_level_slash(expr: str) -> int:
    """Find index of '/' not inside parentheses. Returns -1 if not found."""
    depth = 0
    for i, ch in enumerate(expr):
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
        elif ch == '/' and depth == 0:
            return i
    return -1


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


def _try_parse_factored(expr: str) -> Optional[List[float]]:
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

    # Collect factors
    while i < len(expr):
        ch = expr[i]
        if ch in (' ', '*'):
            i += 1
            continue

        if ch == '(':
            # Find matching close paren
            depth = 1
            j = i + 1
            while j < len(expr) and depth > 0:
                if expr[j] == '(':
                    depth += 1
                elif expr[j] == ')':
                    depth -= 1
                j += 1
            factor_str = expr[i + 1:j - 1].strip()
            factor_coeffs = _parse_expanded_poly(factor_str)
            factors.append(factor_coeffs)
            i = j
        elif expr[i:i + 1].lower() == 's':
            # Bare 's' factor (s alone = pole at origin)
            # Check if it's s^n
            power_match = re.match(r's\s*\^\s*(\d+)', expr[i:])
            if power_match:
                power = int(power_match.group(1))
                # s^n = [1, 0, 0, ..., 0] with n zeros
                factor = [1.0] + [0.0] * power
                factors.append(factor)
                i += power_match.end()
            else:
                factors.append([1.0, 0.0])  # s = [1, 0]
                i += 1
        else:
            # Not a factored form
            return None

    if not factors:
        return None

    # Multiply all factors together using np.polymul
    result = np.array([leading_coeff])
    for f in factors:
        result = np.polymul(result, np.array(f))

    return [float(c) for c in result]


def _parse_expanded_poly(poly_str: str) -> List[float]:
    """Parse expanded polynomial like 's^2 + 3s + 1'.

    Returns coefficients in descending power order.
    """
    poly_str = poly_str.strip()
    if not poly_str or poly_str == "0":
        return [0.0]

    try:
        val = float(poly_str)
        return [val]
    except ValueError:
        pass

    # Tokenize into signed terms
    terms = _tokenize_poly_terms(poly_str)
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

        # Find the power of s
        power_match = re.search(r's\s*\^\s*(-?\d+)', term, re.IGNORECASE)
        if power_match:
            power = int(power_match.group(1))
        else:
            power = 1

        # Extract coefficient
        coeff_str = re.sub(
            r'\s*\*?\s*s(\s*\^\s*-?\d+)?', '', term, flags=re.IGNORECASE
        ).strip()
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
    # Return in descending power order (high-power-first)
    return [coeffs.get(i, 0.0) for i in range(max_power, -1, -1)]


def _tokenize_poly_terms(poly_str: str) -> List[str]:
    """Split polynomial string into signed terms."""
    terms: List[str] = []
    current = ""
    s = poly_str.strip()
    i = 0

    while i < len(s):
        ch = s[i]
        if ch in ('+', '-') and i > 0:
            # Check if this sign is part of an exponent (e.g., s^-1)
            j = i - 1
            while j >= 0 and s[j] == ' ':
                j -= 1
            if j >= 0 and s[j] == '^':
                current += ch
                i += 1
                continue
            # Term separator
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
