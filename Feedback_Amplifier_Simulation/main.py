"""
Interactive Feedback Amplifier Simulator

Course: Signals and Systems (EE204T)
Professor: Ameer Mulla
Students: Prathamesh Nerpagar, Duggimpudi Shreyas Reddy

This simulation demonstrates the effects of feedback on amplifier performance,
including changes in bandwidth, gain, rise time, and pole locations. Users can
interactively adjust system parameters (K₀, α, β, input amplitude) using sliders
and observe real-time updates to:
- Step response comparisons
- Bode magnitude and phase plots
- S-plane pole locations
- Performance metrics

The simulation visualizes both open-loop and closed-loop system behaviors,
helping students understand fundamental feedback control concepts.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import warnings

# Import custom modules
from config import (setup_plot_style, DEFAULT_K0, DEFAULT_ALPHA, DEFAULT_BETA,
                    DEFAULT_INPUT_AMP, OMEGA_MIN, OMEGA_MAX, OMEGA_POINTS,
                    TIME_MAX, TIME_POINTS, BETA_RANGE, K0_RANGE, ALPHA_RANGE,
                    INPUT_RANGE, COLORS)
from calculations import (calculate_metrics, calculate_step_response,
                          calculate_bode_magnitude, calculate_bode_phase)
from plotting import (plot_step_response, plot_bode_magnitude, plot_bode_phase,
                      plot_s_plane, plot_info_panel, plot_metrics_panel,
                      plot_block_diagram)

warnings.filterwarnings('ignore')

class FeedbackAmplifierSimulator:
    """Main class to create and manage the interactive feedback amplifier simulation"""
    
    def __init__(self):
        """Initialize the simulator, UI components, and default parameters"""
        # Set default parameters
        self.K0 = DEFAULT_K0
        self.alpha = DEFAULT_ALPHA
        self.beta = DEFAULT_BETA
        self.input_amp = DEFAULT_INPUT_AMP
        
        # Create frequency and time arrays
        self.omega = np.logspace(OMEGA_MIN, OMEGA_MAX, OMEGA_POINTS)
        self.t = np.linspace(0, TIME_MAX, TIME_POINTS)
        
        # Setup plot style
        setup_plot_style()
        
        # Create figure and layout
        self.fig = plt.figure(figsize=(16, 10))
        self.fig.canvas.manager.set_window_title('Interactive Feedback Control Simulator')
        
        self.setup_layout()
        self.setup_sliders()
        self.initial_plot()
    
    def setup_layout(self):
        """Create the grid layout for all plots and panels"""
        gs = self.fig.add_gridspec(3, 2, hspace=0.5, wspace=0.35,
                                   left=0.07, right=0.97, top=0.90, bottom=0.18,
                                   width_ratios=[1.6, 1], height_ratios=[1, 1, 1])
        
        # Left column: main plots
        gs_plots = gs[:, 0].subgridspec(3, 1, hspace=0.4)
        self.ax_step = self.fig.add_subplot(gs_plots[0, 0])
        self.ax_bode_mag = self.fig.add_subplot(gs_plots[1, 0])
        self.ax_bode_phase = self.fig.add_subplot(gs_plots[2, 0])
        
        # Right column: info panels
        gs_panels = gs[:, 1].subgridspec(3, 1, hspace=0.4)
        self.ax_info = self.fig.add_subplot(gs_panels[0, 0])
        self.ax_s_plane = self.fig.add_subplot(gs_panels[1, 0])
        
        # Bottom right: metrics and diagram
        gs_bottom_panels = gs_panels[2, 0].subgridspec(1, 2, wspace=0.15, width_ratios=[1.3, 1])
        self.ax_metrics = self.fig.add_subplot(gs_bottom_panels[0, 0])
        self.ax_diagram = self.fig.add_subplot(gs_bottom_panels[0, 1])
        
        # Turn off axes for info panels
        for ax in [self.ax_info, self.ax_metrics, self.ax_diagram]:
            ax.axis('off')
        
        # Set title
        self.fig.suptitle('Feedback Control Simulation', 
                         fontsize=22, fontweight='bold', color=COLORS['title'], y=0.96)
    
    def setup_sliders(self):
        """Create and configure the interactive sliders"""
        slider_color = {'color': COLORS['slider'], 'alpha': 0.8}
        
        # Create slider axes
        ax_beta = self.fig.add_axes([0.1, 0.10, 0.35, 0.02])
        ax_K0 = self.fig.add_axes([0.55, 0.10, 0.35, 0.02])
        ax_alpha = self.fig.add_axes([0.1, 0.05, 0.35, 0.02])
        ax_input = self.fig.add_axes([0.55, 0.05, 0.35, 0.02])
        
        # Create sliders
        self.slider_beta = Slider(ax_beta, 'β (Feedback)', 
                                  BETA_RANGE[0], BETA_RANGE[1], 
                                  valinit=self.beta, valstep=BETA_RANGE[2], **slider_color)
        self.slider_K0 = Slider(ax_K0, 'K₀ (Gain)', 
                                K0_RANGE[0], K0_RANGE[1], 
                                valinit=self.K0, valstep=K0_RANGE[2], **slider_color)
        self.slider_alpha = Slider(ax_alpha, 'α (Pole rad/s)', 
                                   ALPHA_RANGE[0], ALPHA_RANGE[1], 
                                   valinit=self.alpha, valstep=ALPHA_RANGE[2], **slider_color)
        self.slider_input = Slider(ax_input, 'Input (V)', 
                                   INPUT_RANGE[0], INPUT_RANGE[1], 
                                   valinit=self.input_amp, valstep=INPUT_RANGE[2], **slider_color)
        
        # Configure slider appearance and callbacks
        for slider in [self.slider_beta, self.slider_K0, self.slider_alpha, self.slider_input]:
            slider.on_changed(self.update)
            slider.label.set_fontweight('bold')
            slider.label.set_fontsize(10)
    
    def update(self, val):
        """Main update function called when any slider is changed"""
        # Get current slider values
        self.beta = self.slider_beta.val
        self.K0 = self.slider_K0.val
        self.alpha = self.slider_alpha.val
        self.input_amp = self.slider_input.val
        
        # Calculate metrics
        metrics = calculate_metrics(self.K0, self.alpha, self.beta)
        
        # Calculate responses
        ol_step, cl_step = calculate_step_response(self.K0, self.alpha, self.beta, 
                                                    self.input_amp, self.t)
        mag_ol, mag_cl = calculate_bode_magnitude(self.K0, self.alpha, self.beta, self.omega)
        phase_ol, phase_cl = calculate_bode_phase(self.K0, self.alpha, self.beta, self.omega)
        
        # Update all plots
        plot_step_response(self.ax_step, self.t, ol_step, cl_step, metrics)
        plot_bode_magnitude(self.ax_bode_mag, self.omega, mag_ol, mag_cl, metrics)
        plot_bode_phase(self.ax_bode_phase, self.omega, phase_ol, phase_cl)
        plot_s_plane(self.ax_s_plane, metrics)
        plot_info_panel(self.ax_info, self.K0, self.alpha, self.beta, self.input_amp)
        plot_metrics_panel(self.ax_metrics, metrics)
        plot_block_diagram(self.ax_diagram)
        
        # Redraw canvas
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
    
    def initial_plot(self):
        """Draw the initial state of the simulation"""
        self.update(None)

def main():
    """Main function to run the simulator"""
    try:
        simulator = FeedbackAmplifierSimulator()
        plt.show()
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    main()