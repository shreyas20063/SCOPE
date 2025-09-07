"""
Signal generation and parsing utilities.

This module provides tools for creating and parsing various signal types
including unit steps, impulses, rectangular pulses, and custom expressions.
"""

import numpy as np
import re
from typing import Callable, Tuple, Union, List

class SignalGenerator:
    """Generator for common signal processing functions."""
    
    @staticmethod
    def unit_step(t: np.ndarray) -> np.ndarray:
        """Unit step function u(t)."""
        return np.heaviside(t, 1)
    
    @staticmethod
    def rectangular_pulse(t: np.ndarray, width: float = 1.0) -> np.ndarray:
        """Rectangular pulse rect(t) with specified width."""
        return np.where(np.abs(t) <= width/2, 1, 0)
    
    @staticmethod
    def triangular_pulse(t: np.ndarray, width: float = 2.0) -> np.ndarray:
        """Triangular pulse tri(t) with specified base width."""
        return np.where(np.abs(t) <= width/2, 1 - np.abs(t)/(width/2), 0)
    
    @staticmethod
    def exponential_decay(t: np.ndarray, alpha: float = 1.0) -> np.ndarray:
        """Exponential decay function exp(-αt)."""
        return np.exp(-alpha * t)
    
    @staticmethod
    def sinc_function(t: np.ndarray, bandwidth: float = 1.0) -> np.ndarray:
        """Sinc function sinc(Bt)."""
        with np.errstate(divide='ignore', invalid='ignore'):
            result = np.sinc(bandwidth * t / np.pi)
        return np.nan_to_num(result, nan=1.0)
    
    @staticmethod
    def unit_impulse_discrete(n: np.ndarray, delay: int = 0) -> np.ndarray:
        """Unit impulse δ[n-delay] for discrete signals."""
        return np.where(n == delay, 1, 0)

class SignalParser:
    """Parser for converting user expressions to signal functions."""
    
    def __init__(self):
        self.safe_globals = {
            'np': np,
            'sin': np.sin,
            'cos': np.cos,
            'exp': np.exp,
            'heaviside': np.heaviside,
            'where': np.where,
            'abs': np.abs,
            'sqrt': np.sqrt,
            'log': np.log,
            'pi': np.pi,
            'e': np.e,
            "__builtins__": {}
        }
    
    def parse_expression(self, expr: str, var: str = 't') -> str:
        """
        Convert user-friendly math expressions to numpy-compatible strings.
        
        Args:
            expr: Mathematical expression string
            var: Variable name ('t' for continuous, 'n' for discrete)
            
        Returns:
            Parsed expression string
        """
        if expr.strip().startswith('[') and expr.strip().endswith(']'):
            return expr
        
        # Replace common mathematical notation
        parsed_expr = expr.replace('^', '**')
        
        # Handle special functions
        parsed_expr = re.sub(r'u\((.*?)\)', r'np.heaviside(\1, 1)', parsed_expr)
        parsed_expr = re.sub(r'rect\((.*?)\)', r'np.where(np.abs(\1)<=0.5, 1, 0)', parsed_expr)
        parsed_expr = re.sub(r'tri\((.*?)\)', r'np.where(np.abs(\1)<=1, 1-np.abs(\1), 0)', parsed_expr)
        
        # Handle discrete delta functions
        if var == 'n':
            parsed_expr = parsed_expr.replace('δ', 'delta')
            if parsed_expr.strip() == 'delta[n]':
                return '[1]'
            
            # Handle shifted delta functions
            match = re.match(r'delta\[n\s*-\s*(\d+)\]', parsed_expr.strip())
            if match:
                shift = int(match.group(1))
                seq = [0.0] * shift + [1.0]
                return str(seq)
        
        return parsed_expr
    
    def create_function_from_expression(self, expr: str, var: str = 't') -> Callable[[np.ndarray], np.ndarray]:
        """
        Create a callable function from a mathematical expression.
        
        Args:
            expr: Mathematical expression string
            var: Variable name
            
        Returns:
            Callable function
        """
        parsed_expr = self.parse_expression(expr, var)
        
        try:
            func = eval(f"lambda {var}: {parsed_expr}", self.safe_globals)
            return func
        except Exception as e:
            raise ValueError(f"Could not create function from expression '{expr}': {e}")
    
    def parse_discrete_sequence(self, expr: str, n_range: np.ndarray) -> Tuple[np.ndarray, int]:
        """
        Parse discrete sequence from expression or list.
        
        Args:
            expr: Expression string or list
            n_range: Range of indices to consider
            
        Returns:
            Tuple of (sequence_values, start_index)
        """
        parsed_expr = self.parse_expression(expr, var='n')
        
        if parsed_expr.strip().startswith('[') and parsed_expr.strip().endswith(']'):
            # Direct list input
            try:
                raw_seq = np.array(eval(parsed_expr))
                return raw_seq, 0
            except Exception as e:
                raise ValueError(f"Invalid list format: {e}")
        else:
            # Function-based input
            try:
                raw_seq = eval(parsed_expr, self.safe_globals, {'n': n_range})
                if isinstance(raw_seq, (int, float)):
                    raw_seq = np.full_like(n_range, raw_seq, dtype=float)
                
                # Find non-zero region
                non_zero_indices = np.where(np.abs(raw_seq) > 1e-12)[0]
                if len(non_zero_indices) == 0:
                    return np.array([]), 0
                
                first, last = non_zero_indices[0], non_zero_indices[-1]
                trimmed_seq = raw_seq[first:last+1]
                start_idx = n_range[first]
                
                return trimmed_seq, start_idx
            except Exception as e:
                raise ValueError(f"Could not evaluate expression '{expr}': {e}")
    
    def latex_formatter(self, expr: str) -> str:
        """
        Format expression string for LaTeX rendering.
        
        Args:
            expr: Mathematical expression
            
        Returns:
            LaTeX-formatted expression
        """
        latex_expr = expr.replace('*', r'\cdot ')
        latex_expr = latex_expr.replace('delta', r'\delta ')
        latex_expr = latex_expr.replace('δ', r'\delta ')
        latex_expr = latex_expr.replace('**', '^')
        latex_expr = latex_expr.replace('np.', '')
        latex_expr = latex_expr.replace('heaviside', 'u')
        return latex_expr

class DemoSignals:
    """Predefined demo signal combinations."""
    
    CONTINUOUS_DEMOS = {
        "Rect Pulse + Tri Pulse": {
            "x": "rect(t)",
            "h": "np.where(np.abs(t)<=1, 1-np.abs(t), 0)",
            "description": "Rectangular pulse convolved with triangular pulse"
        },
        "Unit Step + Exponential Decay": {
            "x": "u(t)",
            "h": "exp(-t) * u(t)",
            "description": "Unit step response of first-order system"
        },
        "Gaussian + Impulse": {
            "x": "exp(-t**2)",
            "h": "u(t) - u(t-1)",
            "description": "Gaussian pulse through rectangular window"
        }
    }
    
    DISCRETE_DEMOS = {
        "x=[1,2,1], h=[1,1]": {
            "x": "[1, 2, 1]",
            "h": "[1, 1]",
            "description": "Simple finite sequences"
        },
        "Decaying Exp + Differentiator": {
            "x": "0.9**n * u(n)",
            "h": "[1, -0.5]",
            "description": "Exponential decay through differentiator"
        },
        "Moving Average Filter": {
            "x": "[1, 0, 1, 0, 1]",
            "h": "[0.25, 0.25, 0.25, 0.25]",
            "description": "Impulse train through 4-point moving average"
        }
    }
    
    @classmethod
    def get_demo_choices(cls, is_continuous: bool) -> List[str]:
        """Get available demo choices for current mode."""
        if is_continuous:
            return list(cls.CONTINUOUS_DEMOS.keys())
        else:
            return list(cls.DISCRETE_DEMOS.keys())
    
    @classmethod
    def get_demo_signals(cls, choice: str, is_continuous: bool) -> Tuple[str, str]:
        """Get x and h expressions for selected demo."""
        demos = cls.CONTINUOUS_DEMOS if is_continuous else cls.DISCRETE_DEMOS
        if choice in demos:
            demo = demos[choice]
            return demo["x"], demo["h"]
        return "", ""
