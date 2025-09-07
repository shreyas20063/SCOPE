"""
Discrete-time convolution simulation controller.

This module provides high-level control for discrete-time
convolution simulations with proper sequence handling.
"""

import numpy as np
from typing import Tuple, Optional
from core.convolution import ConvolutionEngine
from core.signals import SignalParser

class DiscreteSimulation:
    """Controller for discrete-time convolution simulations."""
    
    def __init__(self):
        self.engine = ConvolutionEngine()
        self.parser = SignalParser()
        self.reset()
    
    def reset(self):
        """Reset simulation state."""
        self.x_sequence = np.array([])
        self.h_sequence = np.array([])
        self.x_start_idx = 0
        self.h_start_idx = 0
        self.n_range = np.arange(-20, 21)
        self.current_index = 0
        self.convolution_result = None
        self.result_indices = None
    
    def set_sequences_from_expressions(self, x_expr: str, h_expr: str) -> bool:
        """
        Set sequences from string expressions.
        
        Args:
            x_expr: Expression for x[n]
            h_expr: Expression for h[n]
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Parse x sequence
            self.x_sequence, self.x_start_idx = self.parser.parse_discrete_sequence(
                x_expr, self.n_range
            )
            
            # Parse h sequence
            self.h_sequence, self.h_start_idx = self.parser.parse_discrete_sequence(
                h_expr, self.n_range
            )
            
            return True
        except Exception as e:
            print(f"Failed to parse sequences: {e}")
            return False
    
    def set_sequences_direct(self, x_seq: np.ndarray, h_seq: np.ndarray,
                           x_start: int = 0, h_start: int = 0):
        """Set sequences directly from arrays."""
        self.x_sequence = x_seq.copy()
        self.h_sequence = h_seq.copy()
        self.x_start_idx = x_start
        self.h_start_idx = h_start
    
    def compute_convolution(self) -> bool:
        """
        Compute the discrete convolution.
        
        Returns:
            True if successful, False otherwise
        """
        if len(self.x_sequence) == 0 or len(self.h_sequence) == 0:
            return False
        
        try:
            self.result_indices, self.convolution_result = self.engine.compute_discrete_convolution(
                self.x_sequence, self.h_sequence, self.x_start_idx, self.h_start_idx
            )
            return True
        except Exception as e:
            print(f"Discrete convolution computation failed: {e}")
            return False
    
    def get_sequences_on_grid(self) -> dict:
        """
        Get sequences mapped onto the standard grid.
        
        Returns:
            Dictionary containing gridded sequences
        """
        x_grid = np.zeros_like(self.n_range, dtype=float)
        h_grid = np.zeros_like(self.n_range, dtype=float)
        
        # Map x sequence onto grid
        for i, val in enumerate(self.x_sequence):
            idx = self.x_start_idx + i
            if self.n_range[0] <= idx <= self.n_range[-1]:
                x_grid[idx - self.n_range[0]] = val
        
        # Map h sequence onto grid
        for i, val in enumerate(self.h_sequence):
            idx = self.h_start_idx + i
            if self.n_range[0] <= idx <= self.n_range[-1]:
                h_grid[idx - self.n_range[0]] = val
        
        return {
            'n': self.n_range,
            'x_grid': x_grid,
            'h_grid': h_grid
        }
    
    def get_signals_at_index(self, n0: int) -> dict:
        """
        Get all signal values at specified index.
        
        Args:
            n0: Index for evaluation
            
        Returns:
            Dictionary containing signal data
        """
        grid_data = self.get_sequences_on_grid()
        
        product, sum_value = self.engine.compute_discrete_product_at_index(
            grid_data['x_grid'], grid_data['h_grid'], grid_data['n'], n0
        )
        
        return {
            'n': grid_data['n'],
            'x_n': grid_data['x_grid'],
            'h_flipped_shifted': self._compute_h_flipped_shifted(n0),
            'product': product,
            'sum_value': sum_value,
            'current_index': n0
        }
    
    def _compute_h_flipped_shifted(self, n0: int) -> np.ndarray:
        """Compute h[n0-k] for visualization."""
        grid_data = self.get_sequences_on_grid()
        h_flipped_shifted = np.zeros_like(grid_data['n'], dtype=float)
        
        for i, k_val in enumerate(grid_data['n']):
            target_h_idx = n0 - k_val
            if grid_data['n'][0] <= target_h_idx <= grid_data['n'][-1]:
                array_idx = target_h_idx - grid_data['n'][0]
                h_flipped_shifted[i] = grid_data['h_grid'][array_idx]
        
        return h_flipped_shifted
    
    def get_convolution_value_at_index(self, n0: int) -> float:
        """Get convolution output value at specified index."""
        if self.result_indices is None or self.convolution_result is None:
            return 0.0
        
        if n0 < self.result_indices[0] or n0 > self.result_indices[-1]:
            return 0.0
        
        idx = n0 - self.result_indices[0]
        if 0 <= idx < len(self.convolution_result):
            return self.convolution_result[idx]
        
        return 0.0
    
    def get_index_bounds(self) -> Tuple[int, int]:
        """Get valid index bounds for simulation."""
        if self.result_indices is not None:
            return int(self.result_indices[0]), int(self.result_indices[-1])
        return int(self.n_range[0]), int(self.n_range[-1])
    
    def is_ready(self) -> bool:
        """Check if simulation is ready for visualization."""
        return (len(self.x_sequence) > 0 and 
                len(self.h_sequence) > 0 and 
                self.convolution_result is not None)
    
    def get_sequence_info(self) -> dict:
        """Get information about the current sequences."""
        return {
            'x_length': len(self.x_sequence),
            'h_length': len(self.h_sequence),
            'x_start': self.x_start_idx,
            'h_start': self.h_start_idx,
            'result_length': len(self.convolution_result) if self.convolution_result is not None else 0,
            'result_start': self.result_indices[0] if self.result_indices is not None else 0
        }
