"""
Plot Canvas Module
PyQt5 widget containing matplotlib figure canvas
"""

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec
import matplotlib.image as mpimg
import os

from utils.plotting import PlotManager


class PlotCanvas(FigureCanvas):
    """Matplotlib canvas embedded in PyQt5"""

    def __init__(self, parent=None, width=16, height=10, dpi=100):
        # Create the figure
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)
        self.setParent(parent)

        # Load block diagram images
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        first_order_img_path = os.path.join(script_dir, 'assets', 'image_389368.png')
        second_order_img_path = os.path.join(script_dir, 'assets', 'image_389387.png')

        try:
            self.first_order_img = mpimg.imread(first_order_img_path)
            self.second_order_img = mpimg.imread(second_order_img_path)
            self.images_loaded = True
        except FileNotFoundError as e:
            self.images_loaded = False
            print(f"Error loading image: {e}. Please ensure image files are in assets folder.")

        # Setup the figure layout
        self.setup_figure()

    def setup_figure(self):
        """Create the figure layout with plots"""
        self.fig.suptitle('DC Motor Feedback Control Simulation',
                         fontsize=15, fontweight='bold', y=0.98)

        # Create main grid: plots area
        gs_main = GridSpec(5, 2, figure=self.fig,
                          left=0.08, right=0.95, top=0.95, bottom=0.08,
                          hspace=0.45, wspace=0.30,
                          height_ratios=[1.2, 1.5, 1.5, 0.8, 0.1])

        # Block diagram
        self.ax_block = self.fig.add_subplot(gs_main[0, :])
        self.ax_block.axis('off')

        # Pole-zero plot
        self.ax_poles = self.fig.add_subplot(gs_main[1:3, 0])
        self.ax_poles.set_title('Pole-Zero Map (s-plane)', fontweight='bold', fontsize=11, pad=8)
        self.ax_poles.set_xlabel('Real (σ)', fontsize=10)
        self.ax_poles.set_ylabel('Imaginary (ω)', fontsize=10)
        self.ax_poles.grid(True, alpha=0.3, linestyle='--')
        self.ax_poles.axhline(y=0, color='k', linewidth=0.8)
        self.ax_poles.axvline(x=0, color='k', linewidth=0.8)

        # Step response plot
        self.ax_step = self.fig.add_subplot(gs_main[1:3, 1])
        self.ax_step.set_title('Step Response', fontweight='bold', fontsize=11, pad=8)
        self.ax_step.set_xlabel('Time (seconds)', fontsize=10)
        self.ax_step.set_ylabel('θ(t)', fontsize=10)
        self.ax_step.grid(True, alpha=0.3, linestyle='--')

        # System info display
        self.ax_info = self.fig.add_subplot(gs_main[3, :])
        self.ax_info.axis('off')

        # Parameter display (dummy axis - will be updated by control panel)
        self.ax_param_display = self.fig.add_subplot(gs_main[4, :])
        self.ax_param_display.axis('off')

        # Initialize plotter
        self.plotter = PlotManager(
            self.ax_block, self.ax_poles, self.ax_step,
            self.ax_info, self.ax_param_display
        )

    def update_plots(self, sys, poles, zeros, model_type, alpha, beta, gamma, p):
        """Update all plots with new system data"""
        # Draw block diagram
        diagram_img = self.first_order_img if model_type == 'First-Order' else self.second_order_img
        self.plotter.draw_block_diagram(model_type, self.images_loaded, diagram_img)

        # Display system info
        self.plotter.display_system_info(model_type, alpha, beta, gamma, p, poles)

        # Plot poles and zeros
        self.plotter.plot_poles_zeros(poles, zeros)

        # Plot step response
        self.plotter.plot_step_response(sys, poles, model_type, beta)

        # Refresh canvas
        self.draw()

    def update_param_display(self, alpha, beta, gamma, p, model_type):
        """Update parameter display"""
        self.plotter.update_param_display(alpha, beta, gamma, p, model_type)
        self.draw()
