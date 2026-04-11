"""Expression validation for user-supplied math expressions.

Security-focused validator that rejects dangerous patterns (code injection)
while allowing safe mathematical expressions with numpy functions.

Used by phase_portrait and nonlinear_control_lab simulators.
"""

from typing import Tuple


DANGEROUS_PATTERNS = [
    "import", "exec", "eval", "__", "open", "file",
    "os.", "sys.", "subprocess", "compile", "globals",
    "locals", "getattr", "setattr", "delattr", "lambda",
    "class", "def ", "yield", "async", "await",
]


def validate_expr(expr: str, max_length: int = 500) -> Tuple[bool, str]:
    """Validate a user expression string for security.

    Checks for dangerous patterns (code injection), balanced parentheses,
    and optional length limits.

    Args:
        expr: Raw user expression string.
        max_length: Maximum allowed length (0 = no limit).

    Returns:
        (is_valid, error_message) tuple. error_message is empty if valid.
    """
    if not expr or not expr.strip():
        return False, "Expression cannot be empty"
    expr_lower = expr.lower()
    for pat in DANGEROUS_PATTERNS:
        if pat in expr_lower:
            return False, f"Unsafe pattern: '{pat}'"
    if expr.count("(") != expr.count(")"):
        return False, "Unbalanced parentheses"
    if max_length > 0 and len(expr) > max_length:
        return False, f"Expression too long (max {max_length} chars)"
    return True, ""
