"""
Matplotlib canvas widgets for the Feedback Amplifier Simulator
Contains all plotting functions integrated with PyQt5
"""

import os
import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.image as mpimg

from utils.config import COLORS, PANEL_COLORS, STEP_RESPONSE_Y_MAX, S_PLANE_X_MIN, S_PLANE_X_MAX
from core.calculations import format_value


class PlotCanvas(FigureCanvas):
    """Base canvas for matplotlib plots embedded in PyQt5"""

    def __init__(self, parent=None, width=8, height=6, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.fig.patch.set_facecolor(COLORS['background'])
        # Add margins to prevent labels from being cut off
        self.fig.subplots_adjust(left=0.12, right=0.95, top=0.88, bottom=0.15)
        super(PlotCanvas, self).__init__(self.fig)
        self.setParent(parent)


class StepResponseCanvas(PlotCanvas):
    """Canvas for step response plot"""

    def __init__(self, parent=None):
        super().__init__(parent, width=8, height=2.5, dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.fig.subplots_adjust(left=0.10, right=0.95, top=0.85, bottom=0.18)
        self.setup_axes()

    def setup_axes(self):
        """Setup initial axes configuration"""
        self.ax.set_facecolor(COLORS['axes'])
        self.ax.set_title('Step Response', fontsize=11, fontweight='bold', color=COLORS['title'])
        self.ax.set_xlabel('Time (s)', fontsize=9)
        self.ax.set_ylabel('Output (V)', fontsize=9)
        self.ax.grid(True, alpha=0.3, color=COLORS['grid'])
        self.ax.tick_params(labelsize=8)

    def update_plot(self, t, ol_response, cl_response, metrics):
        """Update the step response plot"""
        self.ax.clear()
        self.setup_axes()

        self.ax.plot(t, ol_response, color=COLORS['open_loop'], lw=2.5,
                     label='Open-Loop', linestyle='--', alpha=0.8)
        self.ax.plot(t, cl_response, color=COLORS['closed_loop'], lw=2.5,
                     label='Closed-Loop')

        self.ax.set_ylim(0, STEP_RESPONSE_Y_MAX)
        self.ax.set_xlim(0, t[-1])
        self.ax.legend(fontsize=8, loc='best')

        text = f"Speedup: {metrics['speedup']:.1f}x"
        self.ax.text(0.98, 0.05, text, transform=self.ax.transAxes, ha='right', va='bottom',
                     fontsize=8,
                     bbox=dict(boxstyle='round,pad=0.3', fc='#ffffff', ec=COLORS['edge'], alpha=0.9))

        self.draw()


class BodeMagnitudeCanvas(PlotCanvas):
    """Canvas for Bode magnitude plot"""

    def __init__(self, parent=None):
        super().__init__(parent, width=8, height=2.5, dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.fig.subplots_adjust(left=0.10, right=0.95, top=0.85, bottom=0.18)
        self.setup_axes()

    def setup_axes(self):
        """Setup initial axes configuration"""
        self.ax.set_facecolor(COLORS['axes'])
        self.ax.set_title('Bode Magnitude', fontsize=11, fontweight='bold', color=COLORS['title'])
        self.ax.set_xlabel('Frequency (rad/s)', fontsize=9)
        self.ax.set_ylabel('Magnitude (dB)', fontsize=9)
        self.ax.grid(True, alpha=0.3, which='both', color=COLORS['grid'])
        self.ax.tick_params(labelsize=8)

    def update_plot(self, omega, mag_ol, mag_cl, metrics):
        """Update the Bode magnitude plot"""
        self.ax.clear()
        self.setup_axes()

        self.ax.semilogx(omega, mag_ol, color=COLORS['open_loop'], lw=2.5,
                         label='Open-Loop', linestyle='--', alpha=0.8)
        self.ax.semilogx(omega, mag_cl, color=COLORS['closed_loop'], lw=2.5,
                         label='Closed-Loop')

        y_min = min(mag_ol.min(), mag_cl.min())
        y_max = max(mag_ol.max(), mag_cl.max())
        y_range = y_max - y_min
        self.ax.set_ylim(y_min - 0.1 * y_range, y_max + 0.1 * y_range)
        self.ax.set_xlim(omega[0], omega[-1])
        self.ax.legend(loc='lower left', fontsize=8)

        text = f"BW: {metrics['speedup']:.1f}x"
        self.ax.text(0.98, 0.05, text, transform=self.ax.transAxes, ha='right', va='bottom',
                     fontsize=8,
                     bbox=dict(boxstyle='round,pad=0.3', fc='#ffffff', ec=COLORS['edge'], alpha=0.9))

        self.draw()


class BodePhaseCanvas(PlotCanvas):
    """Canvas for Bode phase plot"""

    def __init__(self, parent=None):
        super().__init__(parent, width=8, height=2.5, dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.fig.subplots_adjust(left=0.10, right=0.95, top=0.85, bottom=0.18)
        self.setup_axes()

    def setup_axes(self):
        """Setup initial axes configuration"""
        self.ax.set_facecolor(COLORS['axes'])
        self.ax.set_title('Bode Phase', fontsize=11, fontweight='bold', color=COLORS['title'])
        self.ax.set_xlabel('Frequency (rad/s)', fontsize=9)
        self.ax.set_ylabel('Phase (deg)', fontsize=9)
        self.ax.set_yticks([-90, -45, 0])
        self.ax.set_ylim(-95, 5)
        self.ax.grid(True, alpha=0.3, which='both', color=COLORS['grid'])
        self.ax.tick_params(labelsize=8)

    def update_plot(self, omega, phase_ol, phase_cl):
        """Update the Bode phase plot"""
        self.ax.clear()
        self.setup_axes()

        self.ax.semilogx(omega, phase_ol, color=COLORS['open_loop'], lw=2.5,
                         label='Open-Loop', linestyle='--', alpha=0.8)
        self.ax.semilogx(omega, phase_cl, color=COLORS['closed_loop'], lw=2.5,
                         label='Closed-Loop')

        self.ax.set_xlim(omega[0], omega[-1])
        self.ax.legend(loc='lower left', fontsize=8)

        self.draw()


class SPlaneCanvas(PlotCanvas):
    """Canvas for s-plane pole location plot"""

    def __init__(self, parent=None):
        super().__init__(parent, width=5, height=4, dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.fig.subplots_adjust(left=0.15, right=0.95, top=0.88, bottom=0.12)
        self.setup_axes()

    def setup_axes(self):
        """Setup initial axes configuration"""
        self.ax.set_facecolor(COLORS['axes'])
        self.ax.set_title('Pole Location (s-plane)', fontsize=12, fontweight='bold', color=COLORS['title'])
        self.ax.set_xlabel('Real Axis (σ)', fontsize=10)
        self.ax.set_ylabel('Imag (jω)', fontsize=10)
        self.ax.grid(True, alpha=0.3, color=COLORS['grid'])

    def update_plot(self, metrics):
        """Update the s-plane plot"""
        self.ax.clear()
        self.setup_axes()

        ol_pole, cl_pole = metrics['ol_pole'], metrics['cl_pole']

        self.ax.plot(ol_pole, 0, 'x', markersize=12, markeredgewidth=3,
                     color=COLORS['open_loop'], label='Open-Loop Pole')
        self.ax.plot(cl_pole, 0, 'o', markersize=10, markerfacecolor='none',
                     markeredgewidth=2.5, color=COLORS['closed_loop'], label='Closed-Loop Pole')

        if not np.isclose(ol_pole, cl_pole, rtol=0.01):
            self.ax.add_patch(FancyArrowPatch((ol_pole, 0.15), (cl_pole, 0.15),
                                              arrowstyle='->', mutation_scale=20, lw=2, color='#333333'))

        self.ax.axhline(0, color='#888888', lw=1)
        self.ax.axvline(0, color='#888888', lw=1)
        self.ax.set_xlim(S_PLANE_X_MIN, S_PLANE_X_MAX)
        self.ax.set_ylim(-1, 1)
        self.ax.get_yaxis().set_ticks([])
        self.ax.legend(loc='upper left', fontsize=9)

        self.draw()


class InfoPanelCanvas(PlotCanvas):
    """Canvas for system information panel"""

    def __init__(self, parent=None):
        super().__init__(parent, width=4, height=3, dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.axis('off')

    def update_panel(self, K0, alpha, beta, input_amp):
        """Update the information panel"""
        self.ax.clear()
        self.ax.axis('off')

        bg_color, edge_color = PANEL_COLORS['info']
        self.ax.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0.02",
                                         transform=self.ax.transAxes,
                                         facecolor=bg_color, edgecolor=edge_color, linewidth=2))

        self.ax.text(0.5, 0.88, 'System Equations', ha='center', fontsize=13,
                     fontweight='bold', color=COLORS['title'])

        eq_ol = r'Open-Loop: $K(s) = \frac{\alpha K_0}{s + \alpha}$'
        eq_cl = r'Closed-Loop: $H(s) = \frac{\alpha K_0}{s + \alpha(1+\beta K_0)}$'
        self.ax.text(0.5, 0.58, f"{eq_ol}\n\n{eq_cl}", ha='center', va='center',
                     fontsize=10, linespacing=1.8)

        param_text = f"Current Parameters:\nβ={beta:.4f} | K₀={format_value(K0)}\nα={alpha:.1f} rad/s | Input={input_amp:.2f} V"
        self.ax.text(0.5, 0.18, param_text, ha='center', va='center',
                     fontsize=8.5, fontweight='bold', linespacing=1.6)

        self.draw()


class MetricsPanelCanvas(PlotCanvas):
    """Canvas for performance metrics panel"""

    def __init__(self, parent=None):
        super().__init__(parent, width=4, height=3, dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.axis('off')

    def update_panel(self, metrics):
        """Update the metrics panel"""
        self.ax.clear()
        self.ax.axis('off')

        bg_color, edge_color = PANEL_COLORS['metrics']
        self.ax.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0.02",
                                         transform=self.ax.transAxes,
                                         facecolor=bg_color, edgecolor=edge_color, linewidth=2))

        self.ax.text(0.5, 0.94, 'Performance Metrics', ha='center', fontsize=11,
                     fontweight='bold', color=COLORS['success'])

        # Open-Loop metrics
        self.ax.text(0.08, 0.82, 'Open-Loop', va='top', fontweight='bold',
                     color=COLORS['open_loop'], fontsize=9.5)
        self.ax.text(0.08, 0.73, "Gain:", va='top', fontsize=8, fontweight='bold')
        self.ax.text(0.35, 0.73, f"{format_value(metrics['ol_gain'])}", va='top', fontsize=8)
        self.ax.text(0.08, 0.65, "BW:", va='top', fontsize=8, fontweight='bold')
        self.ax.text(0.35, 0.65, f"{format_value(metrics['ol_bw'], 'rad/s')}", va='top', fontsize=8)
        self.ax.text(0.08, 0.57, "Rise Time:", va='top', fontsize=8, fontweight='bold')
        self.ax.text(0.35, 0.57, f"{format_value(metrics['ol_rise_time'], 's')}", va='top', fontsize=8)
        self.ax.text(0.08, 0.49, "Pole:", va='top', fontsize=8, fontweight='bold')
        self.ax.text(0.35, 0.49, f"{metrics['ol_pole']:.1f}", va='top', fontsize=8)

        # Closed-Loop metrics
        self.ax.text(0.08, 0.38, 'Closed-Loop', va='top', fontweight='bold',
                     color=COLORS['closed_loop'], fontsize=9.5)
        self.ax.text(0.08, 0.29, "Gain:", va='top', fontsize=8, fontweight='bold')
        self.ax.text(0.35, 0.29, f"{format_value(metrics['cl_gain'])}", va='top', fontsize=8)
        self.ax.text(0.08, 0.21, "BW:", va='top', fontsize=8, fontweight='bold')
        self.ax.text(0.35, 0.21, f"{format_value(metrics['cl_bw'], 'rad/s')}", va='top', fontsize=8)
        self.ax.text(0.08, 0.13, "Rise Time:", va='top', fontsize=8, fontweight='bold')
        self.ax.text(0.35, 0.13, f"{format_value(metrics['cl_rise_time'], 's')}", va='top', fontsize=8)
        self.ax.text(0.08, 0.05, "Pole:", va='top', fontsize=8, fontweight='bold')
        self.ax.text(0.35, 0.05, f"{metrics['cl_pole']:.1f}", va='top', fontsize=8)

        self.draw()


class BlockDiagramCanvas(PlotCanvas):
    """Canvas for block diagram display"""

    def __init__(self, parent=None):
        super().__init__(parent, width=3, height=3, dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.axis('off')
        self.image_path = None
        self.load_image()

    def load_image(self):
        """Load the block diagram image"""
        try:
            # Get the directory containing this file
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            image_filename = 'image_1dc166.png'
            self.image_path = os.path.join(current_dir, 'assets', image_filename)

            if os.path.exists(self.image_path):
                img = mpimg.imread(self.image_path)
                self.ax.imshow(img)
                self.draw()
            else:
                self.show_error()
        except Exception:
            self.show_error()

    def show_error(self):
        """Show error message if image not found"""
        error_text = f'Error: Image not found.\nAttempted path:\n{self.image_path}'
        self.ax.text(0.5, 0.5, error_text, ha='center', va='center', fontsize=8,
                     color='red', wrap=True,
                     bbox=dict(boxstyle='round,pad=0.5', fc='#ffebee', ec='#c62828'))
        self.draw()
