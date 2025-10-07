"""
Motor Feedback Simulator Module
Handles the main simulation class and core functionality
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, RadioButtons, Button
from scipy import signal
import matplotlib.image as mpimg
import os
from matplotlib.gridspec import GridSpec

from system_calculator import SystemCalculator
from plotter import PlotManager


class MotorFeedbackSimulator:
    """Main simulator class that coordinates UI and system calculations"""
    
    def __init__(self):
        # Default parameters
        self.alpha = 10.0  # Amplifier gain
        self.beta = 0.5    # Feedback gain (0 to 1)
        self.gamma = 1.0   # Motor constant
        self.p = 10.0      # Inertia pole location
        self.model_type = 'First-Order'

        # Initialize calculator and plotter
        self.calculator = SystemCalculator()
        
        # Load block diagram images
        script_dir = os.path.dirname(os.path.abspath(__file__))
        first_order_img_path = os.path.join(script_dir, 'image_389368.png')
        second_order_img_path = os.path.join(script_dir, 'image_389387.png')

        try:
            self.first_order_img = mpimg.imread(first_order_img_path)
            self.second_order_img = mpimg.imread(second_order_img_path)
            self.images_loaded = True
        except FileNotFoundError as e:
            self.images_loaded = False
            print(f"Error loading image: {e}. Please ensure image files are in the same folder as the script.")
        
        # Setup the figure
        self.setup_figure()
        
    def setup_figure(self):
        """Create the interactive figure with two-column layout"""
        self.fig = plt.figure("DC Motor Simulator", figsize=(18, 10))
        self.fig.suptitle('DC Motor Feedback Control Simulation', 
                         fontsize=15, fontweight='bold', y=0.98)
        
        # Create main grid: left column (controls) + right column (plots)
        gs_main = GridSpec(1, 2, figure=self.fig, width_ratios=[1.1, 3.5],
                          left=0.07, right=0.98, top=0.95, bottom=0.05,
                          wspace=0.15)
        
        # Left column for controls
        gs_left = gs_main[0].subgridspec(15, 1, hspace=1.8)
        
        # Right column for plots and info
        gs_right = gs_main[1].subgridspec(5, 2, hspace=0.45, wspace=0.30,
                                         height_ratios=[1.2, 1.5, 1.5, 0.8, 0.1])
        
        # Setup left column controls
        self._setup_controls(gs_left)
        
        # Setup right column plots
        self._setup_plots(gs_right)
        
        # Initialize plotter
        self.plotter = PlotManager(
            self.ax_block, self.ax_poles, self.ax_step, 
            self.ax_info, self.ax_param_display
        )
        
        # Initial plot
        self.update_plot()
        
    def _setup_controls(self, gs_left):
        """Setup control widgets in left column"""
        # Model selection
        ax_radio = self.fig.add_subplot(gs_left[0:2, 0])
        ax_radio.set_title('Model Selection', fontweight='bold', fontsize=11, pad=10)
        self.radio = RadioButtons(ax_radio, ('First-Order', 'Second-Order'), 
                                 active=0, activecolor='steelblue')
        self.radio.on_clicked(self.update_model)
        
        # Alpha Slider
        ax_alpha_label = self.fig.add_subplot(gs_left[3, 0])
        ax_alpha_label.text(0.5, 0.2, 'α (Amplifier gain)', ha='center', va='bottom', fontsize=10)
        ax_alpha_label.axis('off')
        ax_alpha_slider = self.fig.add_subplot(gs_left[4, 0])
        self.slider_alpha = Slider(
            ax_alpha_slider, '', 0.1, 50.0, 
            valinit=self.alpha, valstep=0.1, color='steelblue'
        )
        self.slider_alpha.label.set_visible(False)

        # Beta Slider
        ax_beta_label = self.fig.add_subplot(gs_left[5, 0])
        ax_beta_label.text(0.5, 0.2, 'β (Feedback gain)', ha='center', va='bottom', fontsize=10)
        ax_beta_label.axis('off')
        ax_beta_slider = self.fig.add_subplot(gs_left[6, 0])
        self.slider_beta = Slider(
            ax_beta_slider, '', 0.01, 1.0, 
            valinit=self.beta, valstep=0.01, color='steelblue'
        )
        self.slider_beta.label.set_visible(False)
        
        # Gamma Slider
        ax_gamma_label = self.fig.add_subplot(gs_left[7, 0])
        ax_gamma_label.text(0.5, 0.2, 'γ (Motor constant)', ha='center', va='bottom', fontsize=10)
        ax_gamma_label.axis('off')
        ax_gamma_slider = self.fig.add_subplot(gs_left[8, 0])
        self.slider_gamma = Slider(
            ax_gamma_slider, '', 0.1, 5.0, 
            valinit=self.gamma, valstep=0.1, color='steelblue'
        )
        self.slider_gamma.label.set_visible(False)

        # P Slider
        self.p_label_ax = self.fig.add_subplot(gs_left[9, 0])
        self.p_label_ax.text(0.5, 0.2, 'p (Lag pole)', ha='center', va='bottom', fontsize=10)
        self.p_label_ax.axis('off')
        self.p_slider_ax = self.fig.add_subplot(gs_left[10, 0])
        self.slider_p = Slider(
            self.p_slider_ax, '', 0.5, 30.0, 
            valinit=self.p, valstep=0.5, color='steelblue'
        )
        self.slider_p.label.set_visible(False)
        
        # Parameter value display
        self.ax_param_display = self.fig.add_subplot(gs_left[11:13, 0])
        self.ax_param_display.axis('off')
        
        # Reset button
        ax_reset = self.fig.add_subplot(gs_left[14, 0])
        self.btn_reset = Button(ax_reset, 'Reset Parameters', 
                               color='lightgray', hovercolor='darkgray')
        self.btn_reset.on_clicked(self.reset_params)
        
        # Connect sliders
        self.slider_alpha.on_changed(self.update_params)
        self.slider_beta.on_changed(self.update_params)
        self.slider_gamma.on_changed(self.update_params)
        self.slider_p.on_changed(self.update_params)
        
    def _setup_plots(self, gs_right):
        """Setup plot axes in right column"""
        # Block diagram
        self.ax_block = self.fig.add_subplot(gs_right[0, :])
        self.ax_block.axis('off')
        
        # Pole-zero plot
        self.ax_poles = self.fig.add_subplot(gs_right[1:3, 0])
        self.ax_poles.set_title('Pole-Zero Map (s-plane)', fontweight='bold', fontsize=11, pad=8)
        self.ax_poles.set_xlabel('Real (σ)', fontsize=10)
        self.ax_poles.set_ylabel('Imaginary (ω)', fontsize=10)
        self.ax_poles.grid(True, alpha=0.3, linestyle='--')
        self.ax_poles.axhline(y=0, color='k', linewidth=0.8)
        self.ax_poles.axvline(x=0, color='k', linewidth=0.8)
        
        # Step response plot
        self.ax_step = self.fig.add_subplot(gs_right[1:3, 1])
        self.ax_step.set_title('Step Response', fontweight='bold', fontsize=11, pad=8)
        self.ax_step.set_xlabel('Time (seconds)', fontsize=10)
        self.ax_step.set_ylabel('θ(t)', fontsize=10)
        self.ax_step.grid(True, alpha=0.3, linestyle='--')
        
        # System info display
        self.ax_info = self.fig.add_subplot(gs_right[3, :])
        self.ax_info.axis('off')
        
    def update_model(self, label):
        """Handle model type change"""
        self.model_type = label
        is_second_order = (self.model_type == 'Second-Order')
        self.p_label_ax.set_visible(is_second_order)
        self.p_slider_ax.set_visible(is_second_order)
        self.update_plot()
        
    def update_params(self, val):
        """Handle slider changes"""
        self.alpha = self.slider_alpha.val
        self.beta = self.slider_beta.val
        self.gamma = self.slider_gamma.val
        self.p = self.slider_p.val
        self.update_plot()
        
    def reset_params(self, event):
        """Reset all parameters to default values"""
        self.slider_alpha.reset()
        self.slider_beta.reset()
        self.slider_gamma.reset()
        self.slider_p.reset()
        self.radio.set_active(0)
        
    def update_plot(self):
        """Update all plots"""
        # Get system
        sys, poles, zeros = self.calculator.get_system(
            self.model_type, self.alpha, self.beta, self.gamma, self.p
        )
        
        # Update all plots through plotter
        self.plotter.draw_block_diagram(
            self.model_type, self.images_loaded, 
            self.first_order_img if self.model_type == 'First-Order' else self.second_order_img
        )
        self.plotter.update_param_display(
            self.alpha, self.beta, self.gamma, self.p, self.model_type
        )
        self.plotter.display_system_info(
            self.model_type, self.alpha, self.beta, self.gamma, self.p, poles
        )
        self.plotter.plot_poles_zeros(poles, zeros)
        self.plotter.plot_step_response(
            sys, poles, self.model_type, self.beta
        )
        
        self.fig.canvas.draw_idle()
