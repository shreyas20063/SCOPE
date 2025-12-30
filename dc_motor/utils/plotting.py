"""
Plotter Module
Handles all visualization and plotting functionality
"""

import numpy as np
from scipy import signal


class PlotManager:
    """Manages all plotting and visualization tasks"""

    def __init__(self, ax_block, ax_poles, ax_step, ax_info, ax_param_display):
        """
        Initialize plot manager with matplotlib axes

        Parameters:
        -----------
        ax_block : matplotlib axis
            Axis for block diagram
        ax_poles : matplotlib axis
            Axis for pole-zero map
        ax_step : matplotlib axis
            Axis for step response
        ax_info : matplotlib axis
            Axis for system information
        ax_param_display : matplotlib axis
            Axis for parameter display
        """
        self.ax_block = ax_block
        self.ax_poles = ax_poles
        self.ax_step = ax_step
        self.ax_info = ax_info
        self.ax_param_display = ax_param_display

    def draw_block_diagram(self, model_type, images_loaded, diagram_img):
        """Display the block diagram image"""
        self.ax_block.clear()
        self.ax_block.axis('off')

        if not images_loaded:
            self.ax_block.text(0.5, 0.5, 'Error: Block diagram images not found.',
                               ha='center', va='center', fontsize=12, color='red',
                               bbox=dict(boxstyle='round,pad=0.5', facecolor='white',
                                       edgecolor='red'))
            return

        self.ax_block.imshow(diagram_img)

    def update_param_display(self, alpha, beta, gamma, p, model_type):
        """Display current parameter values"""
        self.ax_param_display.clear()
        self.ax_param_display.axis('off')
        self.ax_param_display.set_xlim(0, 1)
        self.ax_param_display.set_ylim(0, 1)

        param_text = (
            f'Current Parameters:\n\n'
            f'α = {alpha:.2f}\n'
            f'β = {beta:.2f}\n'
            f'γ = {gamma:.2f}\n'
        )

        if model_type == 'Second-Order':
            param_text += f'p = {p:.2f}\n'

        self.ax_param_display.text(0.5, 0.5, param_text,
                                   ha='center', va='center', fontsize=10,
                                   bbox=dict(boxstyle='round', facecolor='lightblue',
                                           edgecolor='blue', linewidth=1.5, pad=0.5))

    def display_system_info(self, model_type, alpha, beta, gamma, p, poles):
        """Display system equations and pole information"""
        self.ax_info.clear()
        self.ax_info.axis('off')
        self.ax_info.set_xlim(0, 1)
        self.ax_info.set_ylim(0, 1)

        if model_type == 'First-Order':
            tf_num = f'{alpha * gamma:.1f}'
            tf_den = f's + {alpha * beta * gamma:.2f}'
            tf_text = rf'$\frac{{\Theta(s)}}{{V(s)}} = \frac{{\alpha\gamma}}{{s + \alpha\beta\gamma}} = \frac{{{tf_num}}}{{{tf_den}}}$'
            pole_text = f'Pole: s = {poles[0]:.2f}'
            pole_color = 'lightgreen'
        else:
            tf_num = f'{alpha * gamma * p:.1f}'
            tf_den = f's² + {p:.1f}s + {alpha * beta * gamma * p:.2f}'
            tf_text = rf'$\frac{{\Theta(s)}}{{V(s)}} = \frac{{\alpha\gamma p}}{{s^2 + ps + \alpha\beta\gamma p}} = \frac{{{tf_num}}}{{{tf_den}}}$'

            if np.iscomplex(poles[0]):
                pole_text = (f'Poles: s = {poles[0].real:.2f} ± {abs(poles[0].imag):.2f}j  '
                           f'(Complex conjugate → Oscillatory)')
                pole_color = 'lightyellow'
            else:
                pole_text = f'Poles: s₁ = {poles[0]:.2f}, s₂ = {poles[1]:.2f}  (Real → Overdamped)'
                pole_color = 'lightgreen'

        # Transfer function
        self.ax_info.text(0.2, 0.75, 'Transfer Function:',
                         ha='right', va='center', fontsize=10, fontweight='bold')
        self.ax_info.text(0.22, 0.75, tf_text,
                         ha='left', va='center', fontsize=11,
                         bbox=dict(boxstyle='round', facecolor='lightcyan',
                                 edgecolor='blue', linewidth=1.5, pad=0.3))

        # Pole information
        self.ax_info.text(0.2, 0.25, 'Poles:',
                         ha='right', va='center', fontsize=10, fontweight='bold')
        self.ax_info.text(0.22, 0.25, pole_text,
                         ha='left', va='center', fontsize=10,
                         bbox=dict(boxstyle='round', facecolor=pole_color,
                                 edgecolor='orange', linewidth=1.5, pad=0.3))

        # Final value
        if beta > 0:
            final_text = rf'Steady-State: 1/β = {1/beta:.2f}'
            self.ax_info.text(0.95, 0.5, final_text,
                             ha='right', va='center', fontsize=10,
                             bbox=dict(boxstyle='round', facecolor='lightgreen',
                                     edgecolor='green', linewidth=1.5, pad=0.3))

    def plot_poles_zeros(self, poles, zeros):
        """Plot pole-zero diagram with fixed axis limits"""
        self.ax_poles.clear()
        self.ax_poles.set_title('Pole-Zero Map (s-plane)', fontweight='bold', fontsize=11, pad=8)
        self.ax_poles.set_xlabel('Real (σ)', fontsize=10)
        self.ax_poles.set_ylabel('Imaginary (ω)', fontsize=10)
        self.ax_poles.grid(True, alpha=0.3, linestyle='--')
        self.ax_poles.axhline(y=0, color='k', linewidth=0.8)
        self.ax_poles.axvline(x=0, color='k', linewidth=0.8)

        # Fixed axis limits
        fixed_xlim = (-60, 10)
        fixed_ylim = (-35, 35)

        # Shade stable region (left half-plane)
        self.ax_poles.fill_betweenx([fixed_ylim[0], fixed_ylim[1]], fixed_xlim[0], 0,
                                    alpha=0.1, color='green', label='Stable region', zorder=1)

        # Plot poles
        pole_plotted = False
        for pole in poles:
            if np.iscomplex(pole):
                if not pole_plotted:
                    self.ax_poles.plot(pole.real, pole.imag, 'rx', markersize=13,
                                      markeredgewidth=3, label='Poles', zorder=5)
                    pole_plotted = True
                else:
                    self.ax_poles.plot(pole.real, pole.imag, 'rx', markersize=13,
                                      markeredgewidth=3, zorder=5)
            else:
                if not pole_plotted:
                    self.ax_poles.plot(pole, 0, 'rx', markersize=13,
                                      markeredgewidth=3, label='Poles', zorder=5)
                    pole_plotted = True
                else:
                    self.ax_poles.plot(pole, 0, 'rx', markersize=13,
                                      markeredgewidth=3, zorder=5)

        # Apply fixed limits
        self.ax_poles.set_xlim(fixed_xlim)
        self.ax_poles.set_ylim(fixed_ylim)

        self.ax_poles.legend(loc='upper right', fontsize=9, framealpha=0.9)

    def plot_step_response(self, sys, poles, model_type, beta):
        """Plot step response with fixed axis limits"""
        self.ax_step.clear()
        self.ax_step.set_title('Step Response', fontweight='bold', fontsize=11, pad=8)
        self.ax_step.set_xlabel('Time (seconds)', fontsize=10)
        self.ax_step.set_ylabel('θ(t)', fontsize=10)
        self.ax_step.grid(True, alpha=0.3, linestyle='--')

        # Fixed time span
        t_max = 5.0
        t = np.linspace(0, t_max, 2000)

        # Calculate step response
        t_step, y_step = signal.step(sys, T=t)
        self.ax_step.plot(t_step, y_step, 'b-', linewidth=2.5, label='Step Response', zorder=3)

        # Add reference line at final value
        if beta > 0:
            final_value = 1.0 / beta
            self.ax_step.axhline(y=final_value, color='red', linestyle='--', linewidth=2,
                                label=f'Final Value = 1/β = {final_value:.2f}', zorder=2)

        # Add envelope for second-order if complex poles
        if model_type == 'Second-Order' and np.iscomplex(poles[0]):
            real_part = poles[0].real
            envelope_decay = np.exp(real_part * t_step)

            if beta > 0:
                envelope_upper = (1/beta) * (1 + envelope_decay)
                envelope_lower = (1/beta) * (1 - envelope_decay)

                self.ax_step.plot(t_step, envelope_upper, 'r--', alpha=0.5, linewidth=1.5,
                                 label=f'Envelope: e^({real_part:.2f}t)', zorder=1)
                self.ax_step.plot(t_step, envelope_lower, 'r--', alpha=0.5, linewidth=1.5, zorder=1)
                self.ax_step.fill_between(t_step, envelope_lower, envelope_upper,
                                         alpha=0.12, color='red', zorder=1)

        self.ax_step.legend(loc='best', fontsize=9, framealpha=0.9)

        # Fixed axis limits
        self.ax_step.set_xlim(0, t_max)
        self.ax_step.set_ylim(-0.5, 3.5)
