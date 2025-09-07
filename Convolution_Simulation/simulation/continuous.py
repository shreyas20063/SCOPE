"""
Continuous-time convolution simulation controller.

This module provides high-level control for continuous-time
convolution simulations with proper numerical handling.
"""

import numpy as np
from typing import Callable, Tuple, Optional
from core.convolution import ConvolutionEngine

class ContinuousSimulation:
    """Controller for continuous-time convolution simulations."""
    
    def __init__(self):
        self.engine = ConvolutionEngine()
        self.reset()
    
    def reset(self):
        """Reset simulation state."""
        self.x_func = None
        self.h_func = None
        self.t_range = (-30, 30)
        self.sampling_rate = 500
        self.current_time = 0
        self.convolution_result = None
        self.time_axis = None
    
    def set_signals(self, x_func: Callable, h_func: Callable):
        """Set the input and impulse response functions."""
        self.x_func = x_func
        self.h_func = h_func
    
    def set_parameters(self, t_range: Tuple[float, float], sampling_rate: float):
        """Set simulation parameters."""
        self.t_range = t_range
        self.sampling_rate = sampling_rate
    
    def compute_convolution(self) -> bool:
        """
        Compute the convolution result.
        
        Returns:
            True if successful, False otherwise
        """
        if self.x_func is None or self.h_func is None:
            return False
        
        try:
            self.time_axis, self.convolution_result = self.engine.compute_continuous_convolution(
                self.x_func, self.h_func, self.sampling_rate, self.t_range
            )
            return True
        except Exception as e:
            print(f"Convolution computation failed: {e}")
            return False
    
    def get_signals_at_time(self, t0: float) -> dict:
        """
        Get all signal values at specified time.
        
        Args:
            t0: Time point for evaluation
            
        Returns:
            Dictionary containing signal data
        """
        if self.x_func is None or self.h_func is None:
            return {}
        
        tau_range = (-15, 15)
        tau, product, integral = self.engine.compute_product_at_time(
            self.x_func, self.h_func, t0, tau_range
        )
        
        return {
            'tau': tau,
            'x_tau': self.x_func(tau),
            'h_flipped_shifted': self.h_func(t0 - tau),
            'product': product,
            'integral_value': integral,
            'current_time': t0
        }
    
    def get_convolution_value_at_time(self, t0: float) -> float:
        """Get convolution output value at specified time."""
        if self.time_axis is None or self.convolution_result is None:
            return 0.0
        
        if t0 < self.time_axis[0] or t0 > self.time_axis[-1]:
            return 0.0
        
        return np.interp(t0, self.time_axis, self.convolution_result)
    
    def get_time_bounds(self) -> Tuple[float, float]:
        """Get valid time bounds for simulation."""
        if self.time_axis is not None:
            return self.time_axis[0], self.time_axis[-1]
        return -15, 15
    
    def is_ready(self) -> bool:
        """Check if simulation is ready for visualization."""
        return (self.x_func is not None and 
                self.h_func is not None and 
                self.convolution_result is not None)
