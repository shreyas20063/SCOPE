"""
Utility functions for mathematical operations and plotting.

This module provides helper functions for the convolution simulator,
including mathematical utilities and plotting configuration.
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Tuple, Optional, Any
import matplotlib.animation as animation

class MathUtils:
    """Mathematical utility functions."""
    
    @staticmethod
    def safe_eval(expr_str: str, var_dict: dict, safe_globals: dict) -> Optional[np.ndarray]:
        """
        Safely evaluate a numpy expression with error handling.
        
        Args:
            expr_str: Expression string to evaluate
            var_dict: Local variables dictionary
            safe_globals: Safe global functions dictionary
            
        Returns:
            Evaluated result or None if error occurs
        """
        try:
            if expr_str.strip().startswith('[') and expr_str.strip().endswith(']'):
                return np.array(eval(expr_str))
            
            safe_locals = var_dict
            return eval(expr_str, safe_globals, safe_locals)
        except Exception as e:
            print(f"Evaluation error for '{expr_str}': {e}")
            return None
    
    @staticmethod
    def interpolate_at_time(t_array: np.ndarray, y_array: np.ndarray, t_target: float) -> float:
        """
        Interpolate y value at target time.
        
        Args:
            t_array: Time array
            y_array: Value array
            t_target: Target time for interpolation
            
        Returns:
            Interpolated value
        """
        if len(t_array) == 0 or len(y_array) == 0:
            return 0.0
        
        if t_target <= t_array[0]:
            return y_array[0]
        elif t_target >= t_array[-1]:
            return y_array[-1]
        else:
            return np.interp(t_target, t_array, y_array)
    
    @staticmethod
    def find_signal_support(signal: np.ndarray, threshold: float = 1e-12) -> Tuple[int, int]:
        """
        Find the support (non-zero region) of a signal.
        
        Args:
            signal: Input signal array
            threshold: Threshold for considering values as zero
            
        Returns:
            Tuple of (start_index, end_index)
        """
        non_zero_indices = np.where(np.abs(signal) > threshold)[0]
        if len(non_zero_indices) == 0:
            return 0, 0
        return non_zero_indices[0], non_zero_indices[-1]
    
    @staticmethod
    def normalize_signal(signal: np.ndarray, method: str = 'max') -> np.ndarray:
        """
        Normalize a signal using specified method.
        
        Args:
            signal: Input signal
            method: Normalization method ('max', 'rms', 'energy')
            
        Returns:
            Normalized signal
        """
        if method == 'max':
            max_val = np.max(np.abs(signal))
            return signal / max_val if max_val > 0 else signal
        elif method == 'rms':
            rms_val = np.sqrt(np.mean(signal**2))
            return signal / rms_val if rms_val > 0 else signal
        elif method == 'energy':
            energy = np.sum(signal**2)
            return signal / np.sqrt(energy) if energy > 0 else signal
        else:
            return signal

class PlotUtils:
    """Plotting utility functions and configurations."""
    
    @staticmethod
    def setup_axes_style(ax: plt.Axes, title: str, xlabel: str = "", ylabel: str = "", 
                        grid: bool = True, legend: bool = True) -> None:
        """
        Configure matplotlib axes with consistent styling.
        
        Args:
            ax: Matplotlib axes object
            title: Axes title
            xlabel: X-axis label
            ylabel: Y-axis label
            grid: Whether to show grid
            legend: Whether to show legend
        """
        ax.set_title(title, fontsize=12, fontweight='bold')
        if xlabel:
            ax.set_xlabel(xlabel, fontsize=10)
        if ylabel:
            ax.set_ylabel(ylabel, fontsize=10)
        
        if grid:
            ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
        
        if legend:
            ax.legend(loc='upper right', fontsize=9)
        
        # Set consistent tick parameters
        ax.tick_params(axis='both', which='major', labelsize=9)
        ax.tick_params(axis='both', which='minor', labelsize=8)
    
    @staticmethod
    def plot_continuous_signal(ax: plt.Axes, t: np.ndarray, signal: np.ndarray, 
                             label: str, color: str = 'blue', linewidth: float = 2.0,
                             highlight_point: Optional[Tuple[float, float]] = None) -> None:
        """
        Plot continuous-time signal with optional highlight point.
        
        Args:
            ax: Matplotlib axes
            t: Time array
            signal: Signal values
            label: Plot label
            color: Line color
            linewidth: Line width
            highlight_point: Optional (time, value) to highlight
        """
        ax.plot(t, signal, color=color, linewidth=linewidth, label=label)
        
        if highlight_point:
            t_point, y_point = highlight_point
            ax.plot(t_point, y_point, 'ro', markersize=8, zorder=10)
            ax.axvline(t_point, color='red', linestyle='--', alpha=0.7, zorder=5)
    
    @staticmethod
    def plot_discrete_signal(ax: plt.Axes, n: np.ndarray, signal: np.ndarray,
                           label: str, color: str = 'blue', markersize: float = 6.0,
                           highlight_index: Optional[int] = None) -> None:
        """
        Plot discrete-time signal with stem plot.
        
        Args:
            ax: Matplotlib axes
            n: Index array
            signal: Signal values
            label: Plot label
            color: Marker color
            markersize: Marker size
            highlight_index: Optional index to highlight
        """
        markerline, stemlines, baseline = ax.stem(n, signal, label=label)
        markerline.set_color(color)
        markerline.set_markersize(markersize)
        stemlines.set_color(color)
        baseline.set_color('black')
        baseline.set_linewidth(0.5)
        
        if highlight_index is not None and highlight_index in n:
            idx = np.where(n == highlight_index)[0][0]
            ax.plot(highlight_index, signal[idx], 'ro', markersize=10, zorder=10)
            ax.axvline(highlight_index, color='red', linestyle='--', alpha=0.7, zorder=5)
    
    @staticmethod
    def plot_product_fill(ax: plt.Axes, t: np.ndarray, product: np.ndarray,
                         color: str = 'green', alpha: float = 0.3) -> None:
        """
        Plot product with filled area for visual emphasis.
        
        Args:
            ax: Matplotlib axes
            t: Time/index array
            product: Product values
            color: Fill color
            alpha: Fill transparency
        """
        ax.fill_between(t, product, alpha=alpha, color=color, zorder=1)
    
    @staticmethod
    def configure_dark_theme(fig: plt.Figure, axes_list: list) -> None:
        """
        Configure dark theme for matplotlib figures.
        
        Args:
            fig: Matplotlib figure
            axes_list: List of axes to configure
        """
        fig_bg_color = '#333333'
        text_color = 'white'
        
        fig.patch.set_facecolor(fig_bg_color)
        
        for ax in axes_list:
            if ax:
                ax.set_facecolor(fig_bg_color)
                ax.tick_params(colors=text_color, which='both')
                ax.xaxis.label.set_color(text_color)
                ax.yaxis.label.set_color(text_color)
                ax.title.set_color(text_color)
                
                # Update grid color
                ax.grid(True, alpha=0.3, color='gray')
    
    @staticmethod
    def configure_light_theme(fig: plt.Figure, axes_list: list) -> None:
        """
        Configure light theme for matplotlib figures.
        
        Args:
            fig: Matplotlib figure
            axes_list: List of axes to configure
        """
        fig_bg_color = 'white'
        text_color = 'black'
        
        fig.patch.set_facecolor(fig_bg_color)
        
        for ax in axes_list:
            if ax:
                ax.set_facecolor(fig_bg_color)
                ax.tick_params(colors=text_color, which='both')
                ax.xaxis.label.set_color(text_color)
                ax.yaxis.label.set_color(text_color)
                ax.title.set_color(text_color)
                
                # Update grid color
                ax.grid(True, alpha=0.3, color='gray')

class AnimationUtils:
    """Utilities for animation control and management."""
    
    @staticmethod
    def create_frame_sequence(start_val: float, end_val: float, 
                            is_continuous: bool = True, num_frames: int = 100) -> np.ndarray:
        """
        Create frame sequence for animation.
        
        Args:
            start_val: Starting value
            end_val: Ending value
            is_continuous: Whether signal is continuous
            num_frames: Number of frames for continuous signals
            
        Returns:
            Array of frame values
        """
        if is_continuous:
            return np.linspace(start_val, end_val, num_frames)
        else:
            return np.arange(int(start_val), int(end_val) + 1)
    
    @staticmethod
    def calculate_animation_interval(speed_multiplier: float, base_fps: float = 30) -> float:
        """
        Calculate animation interval based on speed multiplier.
        
        Args:
            speed_multiplier: Speed multiplication factor
            base_fps: Base frames per second
            
        Returns:
            Interval in milliseconds
        """
        return 1000 / (base_fps * speed_multiplier)
    
    @staticmethod
    def find_frame_index(frames: np.ndarray, target_value: float) -> int:
        """
        Find frame index closest to target value.
        
        Args:
            frames: Array of frame values
            target_value: Target value to find
            
        Returns:
            Index of closest frame
        """
        return np.argmin(np.abs(frames - target_value))

class ValidationUtils:
    """Input validation utilities."""
    
    @staticmethod
    def validate_expression(expr: str, var: str = 't') -> Tuple[bool, str]:
        """
        Validate mathematical expression syntax.
        
        Args:
            expr: Expression string
            var: Variable name
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not expr.strip():
            return False, "Expression cannot be empty"
        
        # Check for balanced parentheses
        if expr.count('(') != expr.count(')'):
            return False, "Unbalanced parentheses"
        
        if expr.count('[') != expr.count(']'):
            return False, "Unbalanced brackets"
        
        # Check for dangerous characters/functions
        dangerous_patterns = ['import', 'exec', 'eval', '__', 'open', 'file']
        for pattern in dangerous_patterns:
            if pattern in expr.lower():
                return False, f"Potentially unsafe operation: {pattern}"
        
        return True, ""
    
    @staticmethod
    def validate_time_range(start: float, end: float) -> Tuple[bool, str]:
        """
        Validate time range parameters.
        
        Args:
            start: Start time
            end: End time
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if start >= end:
            return False, "Start time must be less than end time"
        
        if end - start > 1000:
            return False, "Time range too large (max 1000 units)"
        
        return True, ""