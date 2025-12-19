"""
Convolution computation engine for both continuous and discrete signals.

This module handles the numerical computation of convolution operations
using NumPy's efficient convolution algorithms.
"""

import numpy as np
from typing import Tuple, Callable, Optional

class ConvolutionEngine:
    """Engine for computing convolution operations."""
    
    def __init__(self):
        self.t_extended = np.array([])
        self.n_extended = np.array([])
        
    def compute_continuous_convolution(self, 
                                     x_func: Callable[[np.ndarray], np.ndarray],
                                     h_func: Callable[[np.ndarray], np.ndarray],
                                     sampling_rate: float = 500,
                                     time_range: Tuple[float, float] = (-30, 30)) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute convolution for continuous-time signals.
        
        Args:
            x_func: Input signal function
            h_func: Impulse response function
            sampling_rate: Sampling rate for numerical computation
            time_range: Time range for computation
            
        Returns:
            Tuple of (time_axis, convolution_result)
        """
        t_start, t_end = time_range
        self.t_extended = np.linspace(t_start, t_end, int(sampling_rate * (t_end - t_start)))
        dt = self.t_extended[1] - self.t_extended[0]
        
        # Evaluate functions
        x_t = x_func(self.t_extended)
        h_t = h_func(self.t_extended)
        
        # Compute convolution
        y_conv_full = np.convolve(x_t, h_t, 'full') * dt
        
        # Create time axis for result
        conv_length = len(y_conv_full)
        t_start_conv = 2 * t_start
        t_end_conv = 2 * t_end
        t_y = np.linspace(t_start_conv, t_end_conv, conv_length)
        
        return t_y, y_conv_full
    
    def compute_discrete_convolution(self,
                                   x_sequence: np.ndarray,
                                   h_sequence: np.ndarray,
                                   x_start_idx: int = 0,
                                   h_start_idx: int = 0) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute convolution for discrete-time signals.
        
        Args:
            x_sequence: Input sequence values
            h_sequence: Impulse response sequence values
            x_start_idx: Starting index for x sequence
            h_start_idx: Starting index for h sequence
            
        Returns:
            Tuple of (index_axis, convolution_result)
        """
        # Compute convolution
        y_result = np.convolve(x_sequence, h_sequence, 'full')
        
        # Create index axis
        start_y = x_start_idx + h_start_idx
        n_y = np.arange(start_y, start_y + len(y_result))
        
        return n_y, y_result
    
    def compute_product_at_time(self,
                               x_func: Callable[[np.ndarray], np.ndarray],
                               h_func: Callable[[np.ndarray], np.ndarray],
                               t0: float,
                               tau_range: Tuple[float, float] = (-15, 15),
                               num_points: int = 3000) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        Compute the product x(τ)h(t₀-τ) for visualization.
        
        Args:
            x_func: Input signal function
            h_func: Impulse response function
            t0: Time point for evaluation
            tau_range: Range for τ variable
            num_points: Number of evaluation points
            
        Returns:
            Tuple of (tau_axis, product_values, integral_value)
        """
        tau_start, tau_end = tau_range
        tau = np.linspace(tau_start, tau_end, num_points)
        
        x_tau = x_func(tau)
        h_flipped_shifted = h_func(t0 - tau)
        product = x_tau * h_flipped_shifted
        
        # Compute integral using trapezoidal rule
        integral_val = np.trapz(product, tau)
        
        return tau, product, integral_val
    
    def compute_discrete_product_at_index(self,
                                        x_sequence: np.ndarray,
                                        h_sequence: np.ndarray,
                                        n_indices: np.ndarray,
                                        n0: int) -> Tuple[np.ndarray, float]:
        """
        Compute the product x[k]h[n₀-k] for discrete signals.
        
        Args:
            x_sequence: Input sequence
            h_sequence: Impulse response sequence
            n_indices: Index array
            n0: Current index for evaluation
            
        Returns:
            Tuple of (product_values, sum_value)
        """
        # Create flipped and shifted h sequence
        h_flipped_shifted = np.zeros_like(n_indices, dtype=float)
        
        for i, k_val in enumerate(n_indices):
            target_h_idx = n0 - k_val
            if n_indices[0] <= target_h_idx <= n_indices[-1]:
                array_idx = target_h_idx - n_indices[0]
                h_flipped_shifted[i] = h_sequence[array_idx]
        
        product = x_sequence * h_flipped_shifted
        sum_val = np.sum(product)
        
        return product, sum_val
