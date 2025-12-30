"""
Plotting manager for the Convolution Simulator.

This module handles all plotting operations including mathematical
visualization and block-step diagram generation.
"""

import numpy as np
import matplotlib.pyplot as plt
from core.utils import PlotUtils

class PlotManager:
    """Manages all plotting operations for the simulator."""
    
    def __init__(self, main_app):
        self.app = main_app
        self.plot_utils = PlotUtils()
    
    def update_plots(self, time_val=None):
        """Update all plots for given time value."""
        if time_val is None:
            time_val = self.app.control_panel.get_time_value()
        
        self.app.current_time_val = time_val
        
        # Clear all axes
        for ax in self.app.get_current_axes():
            ax.clear()
            ax.grid(True, alpha=0.3)
        
        # Plot based on signal type
        if self.app.is_continuous:
            self.plot_continuous_signals(time_val)
        else:
            self.plot_discrete_signals(time_val)
        
        self.app.fig.tight_layout(pad=3.0)
        self.app.canvas.draw()
        
        # Update block plot if in block-step mode
        if self.app.visualization_style == "Block-Step":
            self.update_block_plot(time_val)
    
    def plot_continuous_signals(self, t0):
        """Plot continuous signals for mathematical view."""
        ax_x, ax_h, ax_prod, ax_y = self.app.get_current_axes()
        signals = self.app.get_current_signals()
        
        # Format expressions for LaTeX
        x_latex = self.app.signal_parser.latex_formatter(self.app.custom_x_str)
        h_latex = self.app.signal_parser.latex_formatter(self.app.custom_h_str)
        
        # Create time axis for plotting
        tau = np.linspace(-15, 15, 3000)
        
        # Compute signals
        x_tau = signals['x_func'](tau)
        h_flipped_shifted = signals['h_func'](t0 - tau)
        product = x_tau * h_flipped_shifted
        
        # Plot x(τ)
        self.plot_utils.plot_continuous_signal(
            ax_x, tau, x_tau, f'$x(\\tau)$', 'blue'
        )
        self.plot_utils.setup_axes_style(
            ax_x, f"$x(\\tau) = {x_latex}$", "", "", True, True
        )
        ax_x.set_xlim(-15, 15)
        
        # Plot h(t₀-τ)
        self.plot_utils.plot_continuous_signal(
            ax_h, tau, h_flipped_shifted, f'$h({t0:.2f}-\\tau)$', 'red'
        )
        self.plot_utils.setup_axes_style(
            ax_h, f"Flipped & Shifted h (where $h(\\tau) = {h_latex}$)", "", "", True, True
        )
        ax_h.set_xlim(-15, 15)
        
        # Plot product
        self.plot_utils.plot_continuous_signal(
            ax_prod, tau, product, '$x(\\tau)h(t-\\tau)$', 'green'
        )
        self.plot_utils.plot_product_fill(ax_prod, tau, product, 'green', 0.3)
        self.plot_utils.setup_axes_style(
            ax_prod, f"Product: $x(\\tau)h({t0:.2f}-\\tau)$", "", "", True, True
        )
        ax_prod.set_xlim(-15, 15)
        
        # Plot convolution result
        if len(signals['t_y']) > 0 and len(signals['y_result']) > 0:
            plot_mask = (signals['t_y'] >= -25) & (signals['t_y'] <= 25)
            t_plot = signals['t_y'][plot_mask]
            y_plot = signals['y_result'][plot_mask]
            
            highlight_point = None
            if t0 >= t_plot[0] and t0 <= t_plot[-1]:
                idx = np.argmin(np.abs(t_plot - t0))
                highlight_point = (t0, y_plot[idx])
            
            self.plot_utils.plot_continuous_signal(
                ax_y, t_plot, y_plot, '$y(t)$', 'black', 
                highlight_point=highlight_point
            )
            ax_y.set_xlim(-20, 20)
        
        self.plot_utils.setup_axes_style(
            ax_y, "Convolution Output: $y(t) = (x*h)(t)$", "Time t", "", True, True
        )
        
        # Update math label
        integral_val = np.trapz(product, tau)
        self.app.math_label.setText(
            f"$y({t0:.2f}) = \\int x(\\tau)h({t0:.2f}-\\tau)d\\tau \\approx {integral_val:.3f}$"
        )
    
    def plot_discrete_signals(self, n0):
        """Plot discrete signals for mathematical view."""
        ax_x, ax_h, ax_prod, ax_y = self.app.get_current_axes()
        signals = self.app.get_current_signals()
        
        # Format expressions for LaTeX
        x_latex = self.app.signal_parser.latex_formatter(self.app.custom_x_str)
        h_latex = self.app.signal_parser.latex_formatter(self.app.custom_h_str)
        
        n0 = int(round(n0))
        k = signals['n']
        x_k = signals['x_sequence']
        h_k = signals['h_sequence']
        
        # Compute h[n₀-k]
        h_flipped_shifted = np.zeros_like(k, dtype=float)
        for i, k_val in enumerate(k):
            target_h_idx = n0 - k_val
            if k[0] <= target_h_idx <= k[-1]:
                array_idx = target_h_idx - k[0]
                h_flipped_shifted[i] = h_k[array_idx]
        
        product = x_k * h_flipped_shifted
        
        # Plot x[k]
        self.plot_utils.plot_discrete_signal(
            ax_x, k, x_k, '$x[k]$', 'blue'
        )
        self.plot_utils.setup_axes_style(
            ax_x, f"$x[k] = {x_latex}$", "", "", True, True
        )
        
        # Plot h[n₀-k]
        self.plot_utils.plot_discrete_signal(
            ax_h, k, h_flipped_shifted, f'$h[{n0}-k]$', 'red'
        )
        self.plot_utils.setup_axes_style(
            ax_h, f"Flipped & Shifted h (where $h[k] = {h_latex}$)", "", "", True, True
        )
        
        # Plot product
        self.plot_utils.plot_discrete_signal(
            ax_prod, k, product, '$x[k]h[n-k]$', 'green'
        )
        self.plot_utils.setup_axes_style(
            ax_prod, f"Product: $x[k]h[{n0}-k]$", "", "", True, True
        )
        
        # Plot convolution result
        if len(signals['n_y']) > 0 and len(signals['y_result']) > 0:
            highlight_index = None
            if signals['n_y'][0] <= n0 <= signals['n_y'][-1]:
                highlight_index = n0
            
            self.plot_utils.plot_discrete_signal(
                ax_y, signals['n_y'], signals['y_result'], '$y[n]$', 'black',
                highlight_index=highlight_index
            )
        
        self.plot_utils.setup_axes_style(
            ax_y, "Convolution Output: $y[n] = (x*h)[n]$", "Index n", "", True, True
        )
        
        # Update math label
        sum_val = np.sum(product)
        self.app.math_label.setText(
            f"$y[{n0}] = \\sum x[k]h[{n0}-k] = {sum_val:.3f}$"
        )
    
    def update_block_plot(self, time_val):
        """Update block diagram visualization."""
        block_axes = self.app.get_block_axes()
        signals = self.app.get_current_signals()
        
        # Clear block axes
        for ax in block_axes:
            ax.clear()
            ax.grid(True, alpha=0.3)
        
        if self.app.is_continuous:
            self._plot_continuous_block_steps(time_val, block_axes, signals)
        else:
            self._plot_discrete_block_steps(time_val, block_axes, signals)
        
        self.app.block_fig.tight_layout()
        self.app.block_canvas.draw()
    
    def _plot_continuous_block_steps(self, t0, axes, signals):
        """Plot continuous block diagram steps."""
        ax_flip, ax_shift, ax_multiply, ax_sum = axes
        
        tau = np.linspace(-15, 15, 1500)
        h_tau = signals['h_func'](tau)
        h_flipped = signals['h_func'](-tau)
        h_flipped_shifted = signals['h_func'](t0 - tau)
        x_tau = signals['x_func'](tau)
        product = x_tau * h_flipped_shifted
        
        # Step 1: Flip
        self.plot_utils.plot_continuous_signal(
            ax_flip, tau, h_flipped, "Step 1: Flip", 'purple'
        )
        self.plot_utils.setup_axes_style(
            ax_flip, "1. Flip: $h(-\\tau)$", "", "", True, False
        )
        ax_flip.set_xlim(-15, 15)
        
        # Step 2: Shift
        self.plot_utils.plot_continuous_signal(
            ax_shift, tau, h_flipped_shifted, "Step 2: Shift", 'orange'
        )
        self.plot_utils.setup_axes_style(
            ax_shift, f"2. Shift: $h({t0:.1f}-\\tau)$", "", "", True, False
        )
        ax_shift.set_xlim(-15, 15)
        
        # Step 3: Multiply
        self.plot_utils.plot_continuous_signal(
            ax_multiply, tau, product, "Step 3: Multiply", 'green'
        )
        self.plot_utils.plot_product_fill(ax_multiply, tau, product, 'green', 0.3)
        self.plot_utils.setup_axes_style(
            ax_multiply, "3. Multiply", "", "", True, False
        )
        ax_multiply.set_xlim(-15, 15)
        
        # Step 4: Integrate
        integral_val = np.trapz(product, tau)
        ax_sum.text(0.5, 0.5, f"4. Integrate\n$\\int \\approx {integral_val:.3f}$",
                   ha='center', va='center', fontsize=12, 
                   transform=ax_sum.transAxes)
        self.plot_utils.setup_axes_style(
            ax_sum, "4. Result", "", "", False, False
        )
    
    def _plot_discrete_block_steps(self, n0, axes, signals):
        """Plot discrete block diagram steps."""
        ax_flip, ax_shift, ax_multiply, ax_sum = axes
        
        n0 = int(round(n0))
        k = signals['n']
        x_k = signals['x_sequence']
        h_k = signals['h_sequence']
        
        # Approximate flip and shift for visualization
        h_flipped = np.roll(np.flip(h_k), 1)
        h_flipped_shifted = np.roll(h_flipped, n0) if n0 > 0 else np.roll(h_flipped, n0-1)
        product = x_k * h_flipped_shifted
        
        # Step 1: Flip
        self.plot_utils.plot_discrete_signal(
            ax_flip, k, h_flipped, "Step 1: Flip", 'purple'
        )
        self.plot_utils.setup_axes_style(
            ax_flip, "1. Flip: $h[-k]$", "", "", True, False
        )
        
        # Step 2: Shift
        self.plot_utils.plot_discrete_signal(
            ax_shift, k, h_flipped_shifted, "Step 2: Shift", 'orange'
        )
        self.plot_utils.setup_axes_style(
            ax_shift, f"2. Shift: $h[{n0}-k]$", "", "", True, False
        )
        
        # Step 3: Multiply
        self.plot_utils.plot_discrete_signal(
            ax_multiply, k, product, "Step 3: Multiply", 'green'
        )
        self.plot_utils.setup_axes_style(
            ax_multiply, "3. Multiply", "", "", True, False
        )
        
        # Step 4: Sum
        sum_val = np.sum(product)
        ax_sum.text(0.5, 0.5, f"4. Sum\n$\\Sigma = {sum_val:.3f}$",
                   ha='center', va='center', fontsize=12,
                   transform=ax_sum.transAxes)
        self.plot_utils.setup_axes_style(
            ax_sum, "4. Result", "", "", False, False
        )
