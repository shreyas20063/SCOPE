from core.math_handler import SystemMath
from core.config import Config
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class PlotRenderer:
    """Handles all plot rendering and visualization with embedded matplotlib canvas"""

    def __init__(self, figure, axes, colors):
        self.fig = figure
        self.ax_s_plane = axes['s_plane']
        self.ax_z_plane = axes['z_plane']
        self.ax_step_response = axes['step_response']
        self.ax_stability_map = axes['stability_map']
        self.ax_pole_trajectory = axes['pole_trajectory']
        self.ax_learning_panel = axes['learning_panel']
        self.colors = colors

    def plot_s_plane_enhanced(self, tau, T, method):
        """Professional s-plane visualization for teaching"""
        self.ax_s_plane.clear()
        self.ax_s_plane.set_facecolor('#fdfdfd')

        # Calculate current system status
        s_pole = SystemMath.get_ct_pole(tau)
        z_pole = SystemMath.get_dt_pole(s_pole, T, method)
        is_stable = abs(z_pole) < 1
        status_color = self.colors['stable_discrete'] if is_stable else self.colors['unstable_discrete']

        self.ax_s_plane.set_title(f'S-Domain Analysis\nContinuous-Time Pole Location',
                                 fontsize=11, fontweight='bold', color=status_color, pad=12)

        # Draw stability region
        left_halfplane = patches.Rectangle((-4, -3), 4, 6, alpha=0.12, color=self.colors['stable_discrete'])
        self.ax_s_plane.add_patch(left_halfplane)

        # Coordinate system
        self.ax_s_plane.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
        self.ax_s_plane.axhline(y=0, color='black', linewidth=1.2, alpha=0.8)
        self.ax_s_plane.axvline(x=0, color='black', linewidth=1.2, alpha=0.8)

        # Plot the continuous-time pole
        self.ax_s_plane.plot(s_pole.real, s_pole.imag, 'D', color=self.colors['continuous'],
                           markersize=12, markeredgecolor='white', markeredgewidth=2, zorder=5,
                           label=f'CT Pole: s = {s_pole:.2f}')

        # Method-specific overlays
        if method == 'Forward Euler' and T > 0 and (1/T) < 5:
            center = (-1/T, 0)
            radius = 1/T
            circle = patches.Circle(center, radius, fill=False,
                                  color=self.colors['unstable_discrete'],
                                  linewidth=2, linestyle='--', alpha=0.7,
                                  label=f'FE Stability Boundary\n(radius = 1/T)')
            self.ax_s_plane.add_patch(circle)

        # Educational annotations
        self._add_s_plane_annotations()
        self._configure_s_plane_display()

    def plot_z_plane_enhanced(self, tau, T, method):
        """Professional z-plane visualization with clear stability indication"""
        self.ax_z_plane.clear()
        self.ax_z_plane.set_facecolor('#fdfdfd')

        s_pole = SystemMath.get_ct_pole(tau)
        z_pole = SystemMath.get_dt_pole(s_pole, T, method)
        is_stable = abs(z_pole) < 1

        # Status-aware title
        status = 'STABLE SYSTEM' if is_stable else 'UNSTABLE SYSTEM'
        title_color = self.colors['stable_discrete'] if is_stable else self.colors['unstable_discrete']
        self.ax_z_plane.set_title(f'Z-Domain Analysis\n{status}',
                                 fontsize=11, fontweight='bold', color=title_color, pad=12)

        # Unit circle with professional styling
        self._draw_unit_circle()

        # Plot discrete-time pole
        self._plot_dt_pole(z_pole, is_stable)

        # Add stability information
        self._add_z_plane_annotations(z_pole, is_stable)
        self._configure_z_plane_display()

    def plot_step_response_comparison(self, tau, T, method):
        """Comprehensive step response analysis"""
        self.ax_step_response.clear()
        self.ax_step_response.set_facecolor('#fdfdfd')

        s_pole = SystemMath.get_ct_pole(tau)
        z_pole = SystemMath.get_dt_pole(s_pole, T, method)
        is_stable = abs(z_pole) < 1

        self.ax_step_response.set_title('Step Response: Continuous vs Discrete Approximation\nHow Well Does Our Method Work?',
                                       fontsize=11, fontweight='bold', pad=12)

        # Generate time vectors and responses
        t_max = min(6*tau, 15) if is_stable else min(3*tau, 8)
        t_continuous = np.linspace(0, t_max, 1000)
        y_continuous = SystemMath.analytical_step_response(t_continuous, tau)

        # Plot continuous response
        self._plot_continuous_response(t_continuous, y_continuous)

        # Plot discrete response
        self._plot_discrete_response(t_max, T, tau, method, is_stable)

        self._configure_step_response_display(is_stable)

    def plot_stability_landscape(self, tau, T, method):
        """Show stability regions across parameter space"""
        self.ax_stability_map.clear()
        self.ax_stability_map.set_facecolor('#fdfdfd')
        self.ax_stability_map.set_title('Stability Analysis\nPole Magnitude vs Step Size',
                                       fontsize=11, fontweight='bold', pad=12)

        # Generate stability curve
        T_tau_range = np.linspace(0.1, 3.0, 150)
        pole_magnitudes = SystemMath.compute_stability_curve(T_tau_range, tau, method)

        # Create filled regions and plot curve
        self._create_stability_regions(T_tau_range, pole_magnitudes)
        self._plot_stability_curve(T_tau_range, pole_magnitudes)

        # Mark current operating point
        self._mark_current_point(tau, T, method)

        # Add method-specific annotations
        self._add_stability_annotations(method)
        self._configure_stability_display(pole_magnitudes)

    def plot_pole_movement_visualization(self, tau, T, method):
        """Show how poles move as parameters change"""
        self.ax_pole_trajectory.clear()
        self.ax_pole_trajectory.set_facecolor('#fdfdfd')
        self.ax_pole_trajectory.set_title('Pole Movement Visualization\nHow Poles Travel in Z-Plane',
                                        fontsize=11, fontweight='bold', pad=12)

        # Draw unit circle reference
        self._draw_trajectory_unit_circle()

        # Compute and plot trajectory
        T_tau_values = np.linspace(0.1, 3.0, 60)
        trajectory = SystemMath.compute_pole_trajectory(T_tau_values, tau, method)
        self._plot_pole_trajectory(trajectory)

        # Mark current position and annotate
        current_pole = SystemMath.get_dt_pole(SystemMath.get_ct_pole(tau), T, method)
        self._mark_current_pole(current_pole)
        self._annotate_trajectory_points(trajectory)

        self._configure_trajectory_display()

    def create_learning_panel(self, tau, T, method):
        """Dynamic educational content panel"""
        self.ax_learning_panel.clear()
        self.ax_learning_panel.set_xlim(0, 1)
        self.ax_learning_panel.set_ylim(0, 1)
        self.ax_learning_panel.axis('off')

        # Generate educational content
        explanation = self._generate_method_explanation(tau, T, method)

        # Display with appropriate styling
        s_pole = SystemMath.get_ct_pole(tau)
        z_pole = SystemMath.get_dt_pole(s_pole, T, method)
        is_stable = abs(z_pole) < 1

        bg_color = 'lightgreen' if is_stable else 'lightcoral'
        text_color = self.colors['stable_discrete'] if is_stable else self.colors['unstable_discrete']

        self.ax_learning_panel.text(-0.1, 1.0, explanation, transform=self.ax_learning_panel.transAxes,
                                  fontsize=9, verticalalignment='top', fontfamily='monospace',
                                  bbox=dict(boxstyle="round,pad=0.02", facecolor=bg_color, alpha=0.2,
                                          edgecolor=text_color, linewidth=1.5))

    def _add_s_plane_annotations(self):
        """Add educational annotations to s-plane"""
        self.ax_s_plane.text(-3.5, 3.2, 'STABLE\nREGION', fontsize=11, fontweight='bold',
                           color=self.colors['stable_discrete'], ha='center',
                           bbox=dict(boxstyle="round,pad=0.3", facecolor='lightgreen', alpha=0.6))

        self.ax_s_plane.text(1.5, 3.2, 'UNSTABLE\nREGION', fontsize=11, fontweight='bold',
                           color=self.colors['unstable_discrete'], ha='center',
                           bbox=dict(boxstyle="round,pad=0.3", facecolor='lightcoral', alpha=0.6))

    def _configure_s_plane_display(self):
        """Configure s-plane display settings"""
        self.ax_s_plane.set_xlim(-5.0, 3.0)
        self.ax_s_plane.set_ylim(-4.0, 4.0)
        self.ax_s_plane.set_xlabel('Real Part (σ)', fontsize=10, fontweight='bold', labelpad=12)
        self.ax_s_plane.set_ylabel('Imaginary Part (jω)', fontsize=10, fontweight='bold', labelpad=12)
        self.ax_s_plane.xaxis.set_major_locator(plt.MaxNLocator(5))
        self.ax_s_plane.yaxis.set_major_locator(plt.MaxNLocator(5))
        self.ax_s_plane.legend(loc='upper right', fontsize=9, framealpha=0.9,
                             bbox_to_anchor=(1.9, 0.75), borderaxespad=0)
        self.ax_s_plane.grid(True, linestyle='--', alpha=0.5)
        self.ax_s_plane.set_aspect('equal', adjustable='box')

    def _draw_unit_circle(self):
        """Draw unit circle in z-plane"""
        theta = np.linspace(0, 2*np.pi, 200)
        circle_x, circle_y = np.cos(theta), np.sin(theta)

        self.ax_z_plane.fill(circle_x, circle_y, alpha=0.1, color=self.colors['stable_discrete'])
        self.ax_z_plane.plot(circle_x, circle_y, color=self.colors['stable_discrete'],
                           linewidth=3, label='Unit Circle\n(Stability Boundary)', zorder=3)

        # Coordinate grid
        self.ax_z_plane.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
        self.ax_z_plane.axhline(y=0, color='black', linewidth=1.2, alpha=0.8)
        self.ax_z_plane.axvline(x=0, color='black', linewidth=1.2, alpha=0.8)

    def _plot_dt_pole(self, z_pole, is_stable):
        """Plot discrete-time pole with visual feedback"""
        pole_color = self.colors['stable_discrete'] if is_stable else self.colors['unstable_discrete']
        marker_style = 'o' if is_stable else 's'
        marker_size = 14 if is_stable else 16

        self.ax_z_plane.plot(z_pole.real, z_pole.imag, marker_style, color=pole_color,
                           markersize=marker_size, markeredgecolor='white', markeredgewidth=2, zorder=5,
                           label=f'DT Pole\nz = {z_pole:.3f}\n|z| = {abs(z_pole):.3f}')

        # Distance from origin
        if z_pole != 0:
            self.ax_z_plane.plot([0, z_pole.real], [0, z_pole.imag], '--',
                               color=pole_color, alpha=0.5, linewidth=2, zorder=2)

    def _add_z_plane_annotations(self, z_pole, is_stable):
        """Add stability information to z-plane"""
        distance_text = f'Distance from origin: {abs(z_pole):.3f}'
        stability_status = 'STABLE' if is_stable else 'UNSTABLE'
        pole_color = self.colors['stable_discrete'] if is_stable else self.colors['unstable_discrete']

        self.ax_z_plane.text(0.02, 0.98, f'{distance_text}\nStatus: {stability_status}',
                           transform=self.ax_z_plane.transAxes, fontsize=9, fontweight='bold',
                           verticalalignment='top', color=pole_color,
                           bbox=dict(boxstyle="round,pad=0.3", facecolor='white',
                                   edgecolor=pole_color, alpha=0.9))

    def _configure_z_plane_display(self):
        """Configure z-plane display settings"""
        self.ax_z_plane.set_xlim(-2.2, 2.2)
        self.ax_z_plane.set_ylim(-2.2, 2.2)
        self.ax_z_plane.set_xlabel('Real Part', fontsize=10, fontweight='bold', labelpad=10)
        self.ax_z_plane.set_ylabel('Imaginary Part', fontsize=10, fontweight='bold', labelpad=10)
        self.ax_z_plane.xaxis.set_major_locator(plt.MaxNLocator(5))
        self.ax_z_plane.yaxis.set_major_locator(plt.MaxNLocator(5))
        self.ax_z_plane.legend(loc='upper left', fontsize=9, framealpha=0.9,
                             bbox_to_anchor=(1.02, 1.0), borderaxespad=0)
        self.ax_z_plane.set_aspect('equal')

    def _plot_continuous_response(self, t_continuous, y_continuous):
        """Plot continuous-time response"""
        self.ax_step_response.fill_between(t_continuous, 0, y_continuous, alpha=0.15,
                                         color=self.colors['continuous'],
                                         label='Target Response Area')
        self.ax_step_response.plot(t_continuous, y_continuous, color=self.colors['continuous'],
                                 linewidth=3, label='Analytical Solution (CT)', zorder=5)

    def _plot_discrete_response(self, t_max, T, tau, method, is_stable):
        """Plot discrete-time response"""
        try:
            n_max = min(int(t_max / T), 300)
            t_discrete = np.arange(0, n_max) * T
            y_discrete = SystemMath.compute_discrete_step_response(n_max, T, tau, method)

            if is_stable:
                line_color, marker_style, alpha, linewidth, markersize = \
                    self.colors['stable_discrete'], 'o-', 0.8, 2, 5
                method_label = f'{method} Approximation'
            else:
                line_color, marker_style, alpha, linewidth, markersize = \
                    self.colors['unstable_discrete'], 's-', 0.9, 2.5, 6
                method_label = f'{method} (UNSTABLE)'

            if len(y_discrete) > 0 and np.max(np.abs(y_discrete)) < 20:
                self.ax_step_response.plot(t_discrete[:len(y_discrete)], y_discrete,
                                         marker_style, color=line_color, linewidth=linewidth,
                                         markersize=markersize, alpha=alpha,
                                         label=method_label, zorder=4)
                self._add_performance_indicator(t_discrete[:len(y_discrete)], y_discrete, tau, T)
            else:
                self._show_instability_warning()

        except Exception as e:
            self._show_computation_error(str(e))

    def _configure_step_response_display(self, is_stable):
        """Configure step response display"""
        self.ax_step_response.set_xlabel('Time (seconds)', fontsize=10, fontweight='bold')
        self.ax_step_response.set_ylabel('System Output', fontsize=10, fontweight='bold')
        self.ax_step_response.grid(True, alpha=0.3)
        self.ax_step_response.legend(loc='best', framealpha=0.9, fontsize=9)

        if is_stable:
            self.ax_step_response.set_ylim(-0.1, 1.3)
        else:
            self.ax_step_response.set_ylim(-2, 2)

    def _create_stability_regions(self, T_tau_range, pole_magnitudes):
        """Create filled stability regions"""
        stable_region = pole_magnitudes <= 1.0
        marginally_stable = (pole_magnitudes > 1.0) & (pole_magnitudes <= 1.2)

        self.ax_stability_map.fill_between(T_tau_range, 0, 1, alpha=0.2,
                                         color=self.colors['stable_discrete'],
                                         label='Stable Region (|z| < 1)')
        self.ax_stability_map.fill_between(T_tau_range[marginally_stable], 1, 1.2, alpha=0.15,
                                         color='orange', label='Marginal Stability')

    def _plot_stability_curve(self, T_tau_range, pole_magnitudes):
        """Plot the main stability curve"""
        self.ax_stability_map.plot(T_tau_range, pole_magnitudes, linewidth=2.5, color='navy', zorder=3)
        self.ax_stability_map.axhline(y=1, color=self.colors['unstable_discrete'],
                                    linestyle='--', linewidth=2, alpha=0.8,
                                    label='Stability Boundary')

    def _mark_current_point(self, tau, T, method):
        """Mark current operating point on stability map"""
        s_pole = SystemMath.get_ct_pole(tau)
        z_pole = SystemMath.get_dt_pole(s_pole, T, method)
        current_T_tau = T / tau
        current_magnitude = abs(z_pole)

        point_color = self.colors['stable_discrete'] if current_magnitude <= 1 else self.colors['unstable_discrete']

        self.ax_stability_map.plot(current_T_tau, current_magnitude, 'o', color=point_color,
                                 markersize=10, markeredgecolor='white', markeredgewidth=2, zorder=10,
                                 label=f'Current: T/τ = {current_T_tau:.2f}')

    def _add_stability_annotations(self, method):
        """Add method-specific annotations"""
        if method == 'Forward Euler':
            self.ax_stability_map.axvline(x=2.0, color='red', linestyle=':', linewidth=2, alpha=0.8,
                                        label='Critical Point (T/τ = 2)')
            self.ax_stability_map.plot(2.0, 1.0, 'v', color='red', markersize=8, zorder=6)

    def _configure_stability_display(self, pole_magnitudes):
        """Configure stability map display"""
        self.ax_stability_map.set_xlabel('T/τ Ratio (Step Size)', fontsize=10, fontweight='bold')
        self.ax_stability_map.set_ylabel('|z| (Pole Magnitude)', fontsize=10, fontweight='bold')
        self.ax_stability_map.grid(True, alpha=0.3)
        self.ax_stability_map.legend(loc='best', framealpha=0.9, fontsize=8)
        self.ax_stability_map.set_ylim(0, min(2.5, np.max(pole_magnitudes) * 1.1))

    def _draw_trajectory_unit_circle(self):
        """Draw unit circle for trajectory plot"""
        theta = np.linspace(0, 2*np.pi, 100)
        unit_x, unit_y = np.cos(theta), np.sin(theta)

        self.ax_pole_trajectory.plot(unit_x, unit_y, '--', color=self.colors['stable_discrete'],
                                   linewidth=2, alpha=0.6)
        self.ax_pole_trajectory.fill(unit_x, unit_y, alpha=0.08, color=self.colors['stable_discrete'])

        self.ax_pole_trajectory.grid(True, alpha=0.3)
        self.ax_pole_trajectory.axhline(y=0, color='black', linewidth=1.2, alpha=0.8)
        self.ax_pole_trajectory.axvline(x=0, color='black', linewidth=1.2, alpha=0.8)

    def _plot_pole_trajectory(self, trajectory):
        """Plot pole trajectory with color coding"""
        for i in range(len(trajectory) - 1):
            z_current = trajectory[i]
            z_next = trajectory[i + 1]

            # Color based on stability
            magnitude = abs(z_current)
            if magnitude <= 1.0:
                color, alpha, linewidth = self.colors['stable_discrete'], 0.7, 2
            elif magnitude <= 1.5:
                color, alpha, linewidth = 'orange', 0.8, 2.5
            else:
                color, alpha, linewidth = self.colors['unstable_discrete'], 0.9, 3

            self.ax_pole_trajectory.plot([z_current.real, z_next.real],
                                       [z_current.imag, z_next.imag],
                                       color=color, linewidth=linewidth, alpha=alpha, zorder=2)

    def _mark_current_pole(self, current_pole):
        """Mark current pole position"""
        current_color = self.colors['stable_discrete'] if abs(current_pole) <= 1 else self.colors['unstable_discrete']
        self.ax_pole_trajectory.plot(current_pole.real, current_pole.imag, 'o',
                                   color=current_color, markersize=12,
                                   markeredgecolor='white', markeredgewidth=2, zorder=10)

    def _annotate_trajectory_points(self, trajectory):
        """Annotate key points on trajectory"""
        if len(trajectory) > 0:
            start_point = trajectory[0]
            end_point = trajectory[-1]

            self.ax_pole_trajectory.annotate('START\n(small T/τ)', xy=(start_point.real, start_point.imag),
                                           xytext=(15, 15), textcoords='offset points', fontsize=8,
                                           bbox=dict(boxstyle="round,pad=0.2", facecolor='lightblue', alpha=0.8))

            if abs(end_point) > 1.5:
                self.ax_pole_trajectory.annotate('END\n(large T/τ)', xy=(end_point.real, end_point.imag),
                                               xytext=(-15, -15), textcoords='offset points', fontsize=8,
                                               bbox=dict(boxstyle="round,pad=0.2", facecolor='lightcoral', alpha=0.8))

    def _configure_trajectory_display(self):
        """Configure trajectory plot display"""
        self.ax_pole_trajectory.set_xlim(-2, 2)
        self.ax_pole_trajectory.set_ylim(-2, 2)
        self.ax_pole_trajectory.set_xlabel('Real Part', fontsize=10, fontweight='bold')
        self.ax_pole_trajectory.set_ylabel('Imaginary Part', fontsize=10, fontweight='bold')
        self.ax_pole_trajectory.grid(True, alpha=0.3)
        self.ax_pole_trajectory.set_aspect('equal')

    def _show_instability_warning(self):
        """Display instability warning message"""
        self.ax_step_response.text(0.5, 0.5, 'SYSTEM UNSTABLE\nNumerical explosion detected!',
                                 transform=self.ax_step_response.transAxes,
                                 ha='center', va='center', fontsize=14, fontweight='bold',
                                 color=self.colors['unstable_discrete'],
                                 bbox=dict(boxstyle="round,pad=0.5", facecolor='lightcoral', alpha=0.8))

    def _show_computation_error(self, error_msg):
        """Display computation error message"""
        self.ax_step_response.text(0.5, 0.5, f'Computation Error\n{error_msg[:50]}...',
                                 transform=self.ax_step_response.transAxes,
                                 ha='center', va='center', fontsize=12,
                                 bbox=dict(boxstyle="round,pad=0.5", facecolor='lightyellow', alpha=0.8))

    def _add_performance_indicator(self, t_discrete, y_discrete, tau, T):
        """Calculate and display approximation performance"""
        try:
            # Generate reference continuous response
            t_continuous = np.linspace(0, t_discrete[-1], 1000)
            y_continuous = SystemMath.analytical_step_response(t_continuous, tau)

            # Interpolate discrete response for comparison
            y_dt_interp = np.interp(t_continuous, t_discrete, y_discrete)

            # Calculate RMS error
            rms_error = np.sqrt(np.mean((y_continuous - y_dt_interp)**2))

            # Performance categories
            if rms_error < 0.05:
                performance, perf_color = "EXCELLENT", self.colors['stable_discrete']
            elif rms_error < 0.15:
                performance, perf_color = "GOOD", 'orange'
            elif rms_error < 0.3:
                performance, perf_color = "FAIR", 'orange'
            else:
                performance, perf_color = "POOR", self.colors['unstable_discrete']

            self.ax_step_response.text(0.02, 0.98, f'Approximation Quality: {performance}\nRMS Error: {rms_error:.4f}',
                                     transform=self.ax_step_response.transAxes, fontsize=9, fontweight='bold',
                                     verticalalignment='top', color=perf_color,
                                     bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.9))

        except Exception:
            pass  # Skip if calculation fails

    def _generate_method_explanation(self, tau, T, method):
        """Generate comprehensive method explanation text"""
        method_info = Config.METHOD_EXPLANATIONS[method]
        s_pole = SystemMath.get_ct_pole(tau)
        z_pole = SystemMath.get_dt_pole(s_pole, T, method)
        is_stable = abs(z_pole) < 1

        explanation = f"""CURRENT METHOD: {method}

MATHEMATICAL MAPPING:
{method_info['formula']}

CONCEPT:
{method_info['concept']}

STRENGTHS: {method_info['strength']}
LIMITATIONS: {method_info['weakness']}

STABILITY RULE:
{method_info['stability_limit']}

REAL-WORLD USE:
{method_info['real_world']}

CURRENT SYSTEM STATUS:
• T/τ ratio: {T/tau:.3f}
• Pole location: z = {z_pole:.3f}
• Pole magnitude: |z| = {abs(z_pole):.3f}
• System is: {"STABLE" if is_stable else "UNSTABLE"}"""

        return explanation
