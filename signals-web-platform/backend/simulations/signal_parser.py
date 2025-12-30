"""
Signal Parser for Convolution Simulator

Provides secure parsing and evaluation of mathematical expressions for signals.
Supports both continuous-time and discrete-time signal expressions.

Based on: convolution/core/signals.py from the PyQt5 implementation
"""

import numpy as np
import re
from typing import Callable, Tuple, Any, Optional, Union, List


class SignalParser:
    """
    Parser for converting user expressions to signal functions.

    Provides:
    - Expression validation for security
    - Parsing of user-friendly math notation to numpy-compatible code
    - Creation of callable functions from expressions
    - Discrete sequence parsing from list notation

    Security:
    - Uses restricted namespace (no builtins)
    - Blocks dangerous patterns (import, exec, eval, etc.)
    - Validates balanced parentheses/brackets
    """

    # Whitelisted functions for safe evaluation
    SAFE_GLOBALS = {
        'np': np,
        'sin': np.sin,
        'cos': np.cos,
        'tan': np.tan,
        'exp': np.exp,
        'log': np.log,
        'log10': np.log10,
        'sqrt': np.sqrt,
        'abs': np.abs,
        'sign': np.sign,
        'heaviside': np.heaviside,
        'where': np.where,
        'sinc': np.sinc,
        'pi': np.pi,
        'e': np.e,
        'inf': np.inf,
        "__builtins__": {}  # Block all builtins for security
    }

    # Dangerous patterns to block
    DANGEROUS_PATTERNS = [
        'import', 'exec', 'eval', '__', 'open', 'file',
        'os.', 'sys.', 'subprocess', 'compile', 'globals',
        'locals', 'getattr', 'setattr', 'delattr', 'lambda',
        'class', 'def ', 'yield', 'async', 'await'
    ]

    def validate_expression(self, expr: str) -> Tuple[bool, str]:
        """
        Validate expression for security and syntax.

        Args:
            expr: The expression string to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not expr or not expr.strip():
            return False, "Expression cannot be empty"

        expr_stripped = expr.strip()

        # Allow list notation for discrete sequences
        if expr_stripped.startswith('[') and expr_stripped.endswith(']'):
            try:
                # Validate it's a valid list of numbers
                inner = expr_stripped[1:-1].strip()
                if inner:
                    parts = [p.strip() for p in inner.split(',')]
                    for part in parts:
                        float(part)  # Will raise if not a number
                return True, ""
            except ValueError:
                return False, "Invalid list format. Use comma-separated numbers: [1, 2, 3]"

        # Check for dangerous patterns
        expr_lower = expr.lower()
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern in expr_lower:
                return False, f"Unsafe pattern detected: '{pattern}'"

        # Check balanced parentheses
        if expr.count('(') != expr.count(')'):
            return False, "Unbalanced parentheses"

        # Check balanced brackets
        if expr.count('[') != expr.count(']'):
            return False, "Unbalanced brackets"

        return True, ""

    def parse_expression(self, expr: str, var: str = 't') -> str:
        """
        Convert user-friendly math expressions to numpy-compatible strings.

        Transformations:
        - u(t) -> np.heaviside(t, 1)
        - rect(t) -> np.where(np.abs(t)<=0.5, 1, 0)
        - tri(t) -> np.where(np.abs(t)<=1, 1-np.abs(t), 0)
        - sinc(t) -> np.sinc(t/np.pi)  (normalized sinc)
        - ^ -> ** (exponentiation)
        - delta[n] -> [1] (discrete impulse)
        - delta[n-k] -> [0, 0, ..., 1] (shifted impulse)

        Args:
            expr: Mathematical expression string
            var: Variable name ('t' for continuous, 'n' for discrete)

        Returns:
            Parsed expression string ready for eval
        """
        expr_stripped = expr.strip()

        # Handle list notation directly (pass through)
        if expr_stripped.startswith('[') and expr_stripped.endswith(']'):
            return expr_stripped

        parsed = expr

        # Replace exponentiation operator
        parsed = parsed.replace('^', '**')

        # Replace u(x) with np.heaviside(x, 1)
        parsed = re.sub(r'\bu\s*\(\s*([^)]+)\s*\)', r'np.heaviside(\1, 1)', parsed)

        # Replace rect(x) with np.where(np.abs(x)<=0.5, 1, 0)
        parsed = re.sub(
            r'\brect\s*\(\s*([^)]+)\s*\)',
            r'np.where(np.abs(\1)<=0.5, 1.0, 0.0)',
            parsed
        )

        # Replace tri(x) with triangular pulse
        parsed = re.sub(
            r'\btri\s*\(\s*([^)]+)\s*\)',
            r'np.where(np.abs(\1)<=1, 1.0-np.abs(\1), 0.0)',
            parsed
        )

        # Replace sinc(x) with np.sinc(x/pi) for normalized sinc
        parsed = re.sub(
            r'\bsinc\s*\(\s*([^)]+)\s*\)',
            r'np.sinc(\1/np.pi)',
            parsed
        )

        # Handle discrete delta functions
        if var == 'n':
            # Replace δ or delta with standard notation
            parsed = parsed.replace('δ', 'delta')

            # delta[n] -> [1]
            if re.match(r'^\s*delta\s*\[\s*n\s*\]\s*$', parsed):
                return '[1.0]'

            # delta[n-k] -> list with impulse at position k
            match = re.match(r'^\s*delta\s*\[\s*n\s*-\s*(\d+)\s*\]\s*$', parsed)
            if match:
                shift = int(match.group(1))
                # Create list: [0, 0, ..., 0, 1] with 'shift' zeros then 1
                seq = [0.0] * shift + [1.0]
                return str(seq)

            # delta[n+k] -> negative shift (impulse at position -k)
            match = re.match(r'^\s*delta\s*\[\s*n\s*\+\s*(\d+)\s*\]\s*$', parsed)
            if match:
                # This represents impulse at n = -k, return as marker
                return f'__delta_shift_neg_{match.group(1)}__'

        # Replace standalone math functions with numpy versions
        # Use negative lookbehind to avoid double-prefixing np.np.xxx
        parsed = re.sub(r'(?<!np\.)\bsin\s*\(', 'np.sin(', parsed)
        parsed = re.sub(r'(?<!np\.)\bcos\s*\(', 'np.cos(', parsed)
        parsed = re.sub(r'(?<!np\.)\btan\s*\(', 'np.tan(', parsed)
        parsed = re.sub(r'(?<!np\.)\bexp\s*\(', 'np.exp(', parsed)
        parsed = re.sub(r'(?<!np\.)\blog\s*\(', 'np.log(', parsed)
        parsed = re.sub(r'(?<!np\.)\bsqrt\s*\(', 'np.sqrt(', parsed)
        parsed = re.sub(r'(?<!np\.)\babs\s*\(', 'np.abs(', parsed)

        # Replace pi and e if standalone (avoid double-prefixing)
        parsed = re.sub(r'(?<!np\.)\bpi\b', 'np.pi', parsed)
        parsed = re.sub(r'(?<!np\.)\be\b(?!\w)', 'np.e', parsed)

        return parsed

    def create_function(self, expr: str, var: str = 't') -> Callable[[np.ndarray], np.ndarray]:
        """
        Create a callable function from a mathematical expression.

        Args:
            expr: Mathematical expression string
            var: Variable name ('t' or 'n')

        Returns:
            Callable function that takes numpy array and returns numpy array

        Raises:
            ValueError: If expression cannot be parsed or compiled
        """
        # Validate first
        is_valid, error_msg = self.validate_expression(expr)
        if not is_valid:
            raise ValueError(error_msg)

        parsed = self.parse_expression(expr, var)

        # Handle list notation - return constant function
        if parsed.strip().startswith('[') and parsed.strip().endswith(']'):
            try:
                values = eval(parsed)
                arr = np.array(values, dtype=float)
                # Return function that broadcasts this array appropriately
                def list_func(x):
                    result = np.zeros_like(x, dtype=float)
                    for i, val in enumerate(arr):
                        if i < len(x):
                            result[i] = val
                    return result
                return list_func
            except Exception as e:
                raise ValueError(f"Cannot parse list: {e}")

        try:
            # Create function string
            func_code = f"lambda {var}: {parsed}"

            # Compile with safe globals
            func = eval(func_code, self.SAFE_GLOBALS.copy())

            # Test the function with sample input
            test_input = np.linspace(-1, 1, 10)
            test_result = func(test_input)

            # Ensure result is array-like
            if isinstance(test_result, (int, float)):
                # Scalar result - wrap in function that broadcasts
                scalar_val = test_result
                return lambda x: np.full_like(x, scalar_val, dtype=float)

            return func

        except SyntaxError as e:
            raise ValueError(f"Syntax error in expression: {e}")
        except NameError as e:
            raise ValueError(f"Unknown function or variable: {e}")
        except Exception as e:
            raise ValueError(f"Cannot create function from '{expr}': {e}")

    def parse_discrete_sequence(
        self,
        expr: str,
        n_range: np.ndarray
    ) -> Tuple[np.ndarray, int]:
        """
        Parse discrete sequence from expression or list notation.

        Args:
            expr: Expression string or list like "[1, 2, 1]"
            n_range: Range of indices to consider

        Returns:
            Tuple of (sequence_values, start_index)
        """
        # Validate
        is_valid, error_msg = self.validate_expression(expr)
        if not is_valid:
            raise ValueError(error_msg)

        parsed = self.parse_expression(expr, 'n')

        # Handle direct list input: [1, 2, 1]
        if parsed.strip().startswith('[') and parsed.strip().endswith(']'):
            try:
                seq = np.array(eval(parsed), dtype=float)
                return seq, 0  # Start at index 0 by default
            except Exception as e:
                raise ValueError(f"Invalid list format: {e}")

        # Handle special delta markers
        if parsed.startswith('__delta_shift_neg_'):
            shift = int(parsed.split('_')[-2])
            # Impulse at n = -shift
            return np.array([1.0]), -shift

        # Handle function-based expression: 0.9**n * u(n)
        try:
            # Create safe namespace with n variable
            local_ns = {'n': n_range}
            result = eval(parsed, self.SAFE_GLOBALS.copy(), local_ns)

            if isinstance(result, (int, float)):
                result = np.full_like(n_range, result, dtype=float)
            else:
                result = np.asarray(result, dtype=float)

            # Trim to non-zero support for efficiency
            non_zero_indices = np.where(np.abs(result) > 1e-12)[0]

            if len(non_zero_indices) == 0:
                return np.array([0.0]), 0

            first_idx = non_zero_indices[0]
            last_idx = non_zero_indices[-1]

            trimmed_seq = result[first_idx:last_idx + 1]
            start_idx = int(n_range[first_idx])

            return trimmed_seq, start_idx

        except Exception as e:
            raise ValueError(f"Cannot evaluate expression '{expr}': {e}")

    def get_supported_functions(self, mode: str = 'continuous') -> dict:
        """
        Get dictionary of supported functions for help text.

        Args:
            mode: 'continuous' or 'discrete'

        Returns:
            Dictionary with function names and descriptions
        """
        common = {
            'sin(x)': 'Sine function',
            'cos(x)': 'Cosine function',
            'exp(x)': 'Exponential e^x',
            'log(x)': 'Natural logarithm',
            'sqrt(x)': 'Square root',
            'abs(x)': 'Absolute value',
            'pi': 'Pi constant (3.14159...)',
            'e': 'Euler\'s number (2.71828...)',
            '^': 'Exponentiation (e.g., t^2)',
        }

        if mode == 'continuous':
            return {
                **common,
                'u(t)': 'Unit step function',
                'rect(t)': 'Rectangular pulse (width 1)',
                'tri(t)': 'Triangular pulse (width 2)',
                'sinc(t)': 'Sinc function',
            }
        else:
            return {
                **common,
                'u(n)': 'Unit step (discrete)',
                'delta[n]': 'Unit impulse at n=0',
                'delta[n-k]': 'Shifted impulse at n=k',
                '[1, 2, 1]': 'Direct sequence input',
            }


# Convenience functions for direct use
def parse_and_validate(expr: str, var: str = 't') -> Tuple[bool, str, Optional[str]]:
    """
    Parse and validate an expression.

    Returns:
        Tuple of (is_valid, error_message, parsed_expression)
    """
    parser = SignalParser()
    is_valid, error = parser.validate_expression(expr)
    if not is_valid:
        return False, error, None

    try:
        parsed = parser.parse_expression(expr, var)
        return True, "", parsed
    except Exception as e:
        return False, str(e), None


def create_signal_function(expr: str, var: str = 't') -> Callable:
    """
    Create a signal function from expression.

    Convenience wrapper around SignalParser.create_function().
    """
    parser = SignalParser()
    return parser.create_function(expr, var)
