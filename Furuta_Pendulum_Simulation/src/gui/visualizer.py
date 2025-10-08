"""
Interactive 3D Visualization and GUI Module

This module provides the interactive graphical interface for the Furuta Pendulum
simulator, including 3D visualization, real-time plots, and control widgets.

Course: Signals and Systems (EE204T)
Instructor: Prof. Ameer Mulla
Authors: Duggimpudi Shreyas Reddy, Prathamesh Nerpagar
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
from matplotlib.widgets import Slider, Button
from matplotlib.animation import FuncAnimation
from matplotlib.gridspec import GridSpec


class FurutaPendulumVisualizer:
    """
    Handles all visualization, GUI elements, and user interactions
    for the Furuta Pendulum simulation.
    """

    def __init__(self, physics_model, controller):
        """
        Initialize the visualizer with physics and control components.

        Args:
            physics_model: Instance of FurutaPendulumPhysics
            controller: Instance of PIDController
        """
        self.physics = physics_model
        self.controller = controller

        # Store initial parameter values for reset
        self.initial_params = {
            'state': np.array([0.1, 0.0, 0.0, 0.0]),
            'mass': self.physics.m,
            'pendulum_length': self.physics.l,
            'arm_length': self.physics.r,
            'kp': self.controller.Kp,
            'kd': self.controller.Kd,
            'ki': self.controller.Ki,
            'speed': 1.0
        }

        # Simulation state
        self.state = self.initial_params['state'].copy()
        self.time = 0.0
        self.dt = 0.01
        self.running = False
        self.speed_multiplier = self.initial_params['speed']

        # History for plotting
        self.max_history = 500
        self.time_history = []
        self.theta_history = []
        self.control_history = []

        # 3D artist references (will be created during rendering)
        self.pend_sphere = None
        self.joint_sphere = None
        self.base_cylinder = None
        self.upright_ref = None
        self.shadow_arm = None
        self.shadow_pend = None
        self.direction_arrow = None
        self.torque_arrow = None

        # Setup the figure and GUI
        self.setup_figure()

    def setup_figure(self):
        """Create the interactive figure with 3D view, plots, and controls."""
        self.fig = plt.figure("Furuta Pendulum Simulator", figsize=(18, 10))
        self.fig.patch.set_facecolor('white')

        gs = GridSpec(3, 4, figure=self.fig,
                      left=0.05, right=0.75, top=0.94, bottom=0.12,
                      hspace=0.35, wspace=0.35)

        # Create subplots
        self._setup_3d_view(gs)
        self._setup_angle_plot(gs)
        self._setup_control_plot(gs)
        self._setup_sliders()
        self._setup_buttons()
        self._add_info_text()

        self.update_display()

    def _setup_3d_view(self, gs):
        """Setup the main 3D visualization."""
        self.ax_main = self.fig.add_subplot(gs[0:2, 0:3], projection='3d')
        self.ax_main.set_xlim(-0.4, 0.4)
        self.ax_main.set_ylim(-0.4, 0.4)
        self.ax_main.set_zlim(-0.05, 0.4)
        self.ax_main.set_facecolor('white')

        # Set pane colors
        try:
            self.ax_main.w_xaxis.set_pane_color((0.95, 0.95, 0.95, 1.0))
            self.ax_main.w_yaxis.set_pane_color((0.95, 0.95, 0.95, 1.0))
            self.ax_main.w_zaxis.set_pane_color((0.98, 0.98, 1.0, 1.0))
        except AttributeError:
            try:
                self.ax_main.xaxis.set_pane_color((0.95, 0.95, 0.95, 1.0))
                self.ax_main.yaxis.set_pane_color((0.95, 0.95, 0.95, 1.0))
                self.ax_main.zaxis.set_pane_color((0.98, 0.98, 1.0, 1.0))
            except Exception:
                pass

        self.ax_main.set_title('Furuta Pendulum - 3D View', fontsize=14,
                               fontweight='bold', color='#1a1a1a', pad=20)
        self.ax_main.set_xlabel('X (meters)', color='#333', fontsize=10, labelpad=8)
        self.ax_main.set_ylabel('Y (meters)', color='#333', fontsize=10, labelpad=8)
        self.ax_main.set_zlabel('Height (meters)', color='#333', fontsize=10, labelpad=8)
        self.ax_main.view_init(elev=25, azim=45)
        self.ax_main.grid(True, alpha=0.4, color='#999999', linestyle='-', linewidth=0.5)
        self.ax_main.tick_params(colors='#333', labelsize=8)

        # Draw base platform and floor
        self._draw_base_platform()

        # Initialize 3D lines
        self.arm_line, = self.ax_main.plot([], [], [], color='#2563eb',
                                            linewidth=8, solid_capstyle='round')
        self.pend_line, = self.ax_main.plot([], [], [], color='#10b981',
                                             linewidth=5, solid_capstyle='round')

        # Status text
        self.status_text = self.fig.text(
            0.06, 0.88, '', verticalalignment='top', fontsize=9,
            color='#1a1a1a', family='monospace',
            bbox=dict(boxstyle='round', facecolor='#f0f0f0',
                     edgecolor='#999', linewidth=1.5, alpha=0.95)
        )

    def _draw_base_platform(self):
        """Draw the base platform and floor grid."""
        circle_theta = np.linspace(0, 2 * np.pi, 100)

        # Base circle
        base_radius = 0.06
        base_x = base_radius * np.cos(circle_theta)
        base_y = base_radius * np.sin(circle_theta)
        base_z = np.zeros_like(base_x)
        self.ax_main.plot(base_x, base_y, base_z, '#555555', linewidth=3, alpha=0.9)

        # Floor circle
        floor_radius = 0.38
        floor_x = floor_radius * np.cos(circle_theta)
        floor_y = floor_radius * np.sin(circle_theta)
        floor_z = np.ones_like(floor_x) * (-0.04)
        self.ax_main.plot(floor_x, floor_y, floor_z, '#dddddd', linewidth=1, alpha=0.3)

        # Floor radial lines
        for angle in np.linspace(0, 2 * np.pi, 8, endpoint=False):
            self.ax_main.plot([0, floor_radius * np.cos(angle)],
                             [0, floor_radius * np.sin(angle)],
                             [-0.04, -0.04], '#e5e5e5', linewidth=0.5, alpha=0.3)

    def _setup_angle_plot(self, gs):
        """Setup the pendulum angle time-series plot."""
        self.ax_theta = self.fig.add_subplot(gs[2, 0:2])
        self.ax_theta.set_facecolor('#fafafa')
        self.ax_theta.grid(True, alpha=0.4, color='#cccccc', linestyle='-', linewidth=0.5)
        self.ax_theta.set_xlabel('Time (s)', color='#333', fontsize=10)
        self.ax_theta.set_ylabel('Angle (deg)', color='#333', fontsize=10)
        self.ax_theta.set_title('Pendulum Angle', fontweight='bold',
                                color='#1a1a1a', fontsize=11)
        self.theta_line, = self.ax_theta.plot([], [], color='#10b981',
                                               linewidth=2.5, label='θ')
        self.ax_theta.axhline(y=0, color='#666', linestyle='--', alpha=0.6, linewidth=1)
        self.ax_theta.tick_params(colors='#333', labelsize=8)
        for spine in self.ax_theta.spines.values():
            spine.set_color('#cccccc')

    def _setup_control_plot(self, gs):
        """Setup the control input time-series plot."""
        self.ax_control = self.fig.add_subplot(gs[2, 2:4])
        self.ax_control.set_facecolor('#fafafa')
        self.ax_control.grid(True, alpha=0.4, color='#cccccc', linestyle='-', linewidth=0.5)
        self.ax_control.set_xlabel('Time (s)', color='#333', fontsize=10)
        self.ax_control.set_ylabel('Torque (Nm)', color='#333', fontsize=10)
        self.ax_control.set_title('Control Input', fontweight='bold',
                                  color='#1a1a1a', fontsize=11)
        self.control_line, = self.ax_control.plot([], [], color='#3b82f6',
                                                   linewidth=2.5, label='τ')
        self.ax_control.axhline(y=0, color='#666', linestyle='--', alpha=0.6, linewidth=1)
        self.ax_control.tick_params(colors='#333', labelsize=8)
        for spine in self.ax_control.spines.values():
            spine.set_color('#cccccc')

    def _setup_sliders(self):
        """Create interactive sliders for parameters."""
        slider_color = '#e8f0fe'
        right_x = 0.78
        slider_width = 0.16

        # Physical parameter sliders
        ax_l = plt.axes([right_x, 0.75, slider_width, 0.02], facecolor=slider_color)
        ax_r = plt.axes([right_x, 0.70, slider_width, 0.02], facecolor=slider_color)
        ax_m = plt.axes([right_x, 0.65, slider_width, 0.02], facecolor=slider_color)

        self.slider_l = Slider(ax_l, 'Pend Len', 0.1, 0.4,
                               valinit=self.physics.l, valstep=0.01, color='#f97316')
        self.slider_r = Slider(ax_r, 'Arm Len', 0.1, 0.3,
                               valinit=self.physics.r, valstep=0.01, color='#f97316')
        self.slider_m = Slider(ax_m, 'Mass', 0.01, 0.2,
                               valinit=self.physics.m, valstep=0.01, color='#f97316')

        # PID gain sliders
        ax_kp = plt.axes([right_x, 0.52, slider_width, 0.02], facecolor=slider_color)
        ax_kd = plt.axes([right_x, 0.47, slider_width, 0.02], facecolor=slider_color)
        ax_ki = plt.axes([right_x, 0.42, slider_width, 0.02], facecolor=slider_color)

        self.slider_kp = Slider(ax_kp, 'Kp', 0, 300,
                                valinit=self.controller.Kp, valstep=5, color='#10b981')
        self.slider_kd = Slider(ax_kd, 'Kd', 0, 50,
                                valinit=self.controller.Kd, valstep=1, color='#10b981')
        self.slider_ki = Slider(ax_ki, 'Ki', 0, 20,
                                valinit=self.controller.Ki, valstep=1, color='#10b981')

        # Speed slider
        ax_speed = plt.axes([right_x, 0.36, slider_width, 0.02], facecolor=slider_color)
        self.slider_speed = Slider(ax_speed, 'Speed', 0.1, 3.0,
                                   valinit=self.speed_multiplier, valstep=0.1, color='#8b5cf6')

        # Connect slider callbacks and store connection IDs
        self.cid_l = self.slider_l.on_changed(self._on_params_changed)
        self.cid_r = self.slider_r.on_changed(self._on_params_changed)
        self.cid_m = self.slider_m.on_changed(self._on_params_changed)
        self.cid_kp = self.slider_kp.on_changed(self._on_params_changed)
        self.cid_kd = self.slider_kd.on_changed(self._on_params_changed)
        self.cid_ki = self.slider_ki.on_changed(self._on_params_changed)
        self.cid_speed = self.slider_speed.on_changed(self._on_speed_changed)

        # Labels
        self.fig.text(right_x, 0.82, 'Physical Parameters:',
                     fontsize=11, fontweight='bold', color='#f97316')
        self.fig.text(right_x, 0.59, 'PID Control Gains:',
                     fontsize=11, fontweight='bold', color='#10b981')

    def _setup_buttons(self):
        """Create control buttons."""
        right_x = 0.78
        btn_width = 0.15
        btn_height = 0.04

        ax_start = plt.axes([right_x, 0.28, btn_width, btn_height])
        ax_reset = plt.axes([right_x, 0.22, btn_width, btn_height])
        ax_disturb = plt.axes([right_x, 0.16, btn_width, btn_height])

        self.btn_start = Button(ax_start, 'Start/Pause',
                                color='#10b981', hovercolor='#86efac')
        self.btn_reset = Button(ax_reset, 'Reset',
                                color='#d1d5db', hovercolor='#e5e7eb')
        self.btn_disturb = Button(ax_disturb, 'Disturb',
                                  color='#ef4444', hovercolor='#fca5a5')

        self.btn_start.on_clicked(self._on_start_clicked)
        self.btn_reset.on_clicked(self._on_reset_clicked)
        self.btn_disturb.on_clicked(self._on_disturb_clicked)

    def _add_info_text(self):
        """Add informational text panel."""
        info_text = (
            "Furuta Pendulum Control\n\n"
            "COMMON QUESTION:\n"
            "\"Why does the arm only\n"
            "spin one direction?\"\n\n"
            "ANSWER: It DOESN'T!\n"
            "The arm changes direction\n"
            "50-100 times per second!\n\n"
            "HOW IT WORKS:\n"
            "Uses ACCELERATION to\n"
            "create inertial forces\n"
            "that push pendulum up.\n\n"
            "TO SEE DIRECTION CHANGES:\n"
            "1. Watch Control Plot\n"
            "   (bottom right graph)\n"
            "2. Line crosses zero =\n"
            "   direction reversal!\n"
            "3. Count the crossings\n"
            "4. Set Speed to 0.3x\n"
            "   (makes it visible)\n"
            "5. Press Disturb - see\n"
            "   LARGE reversals\n"
            "6. Watch ω_φ in status:\n"
            "   +273 → -182 → +95\n"
            "   (sign keeps flipping!)\n\n"
            "Arrows: Blue↔Red\n"
            "τ: Positive↔Negative\n\n"
            "Read HOW_IT_WORKS.md\n"
            "for full explanation!"
        )

        self.fig.text(
            0.78, 0.11, info_text, fontsize=7.5, color='#1a1a1a',
            family='monospace', verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='#f0f9ff',
                     edgecolor='#3b82f6', linewidth=1.5, alpha=0.95)
        )

    def _on_params_changed(self, _val):
        """Callback when sliders change."""
        # Update physics parameters
        self.physics.update_parameters(
            mass=self.slider_m.val,
            pendulum_length=self.slider_l.val,
            arm_length=self.slider_r.val
        )

        # Update controller gains
        self.controller.update_gains(
            kp=self.slider_kp.val,
            kd=self.slider_kd.val,
            ki=self.slider_ki.val
        )

    def _on_speed_changed(self, _val):
        """Callback when speed slider changes."""
        self.speed_multiplier = max(0.1, self.slider_speed.val)
        if hasattr(self, 'anim') and self.anim is not None:
            try:
                new_interval = (self.dt / self.speed_multiplier) * 1000
                self.anim.event_source.interval = new_interval
            except Exception:
                pass

    def _on_start_clicked(self, _event):
        """Callback for Start/Pause button."""
        self.running = not self.running

    def _on_reset_clicked(self, _event):
        """Callback for Reset button - resets all parameters and sliders to initial values."""
        self.running = False
        self.state = self.initial_params['state'].copy()
        self.time = 0.0

        # Reset physics parameters directly
        self.physics.update_parameters(
            mass=self.initial_params['mass'],
            pendulum_length=self.initial_params['pendulum_length'],
            arm_length=self.initial_params['arm_length']
        )

        # Reset controller gains directly
        self.controller.update_gains(
            kp=self.initial_params['kp'],
            kd=self.initial_params['kd'],
            ki=self.initial_params['ki']
        )
        self.controller.reset()

        # Reset speed
        self.speed_multiplier = self.initial_params['speed']

        # Temporarily disconnect slider callbacks to prevent cascade
        self.slider_m.disconnect(self.cid_m)
        self.slider_l.disconnect(self.cid_l)
        self.slider_r.disconnect(self.cid_r)
        self.slider_kp.disconnect(self.cid_kp)
        self.slider_kd.disconnect(self.cid_kd)
        self.slider_ki.disconnect(self.cid_ki)
        self.slider_speed.disconnect(self.cid_speed)

        # Reset slider positions
        self.slider_m.set_val(self.initial_params['mass'])
        self.slider_l.set_val(self.initial_params['pendulum_length'])
        self.slider_r.set_val(self.initial_params['arm_length'])
        self.slider_kp.set_val(self.initial_params['kp'])
        self.slider_kd.set_val(self.initial_params['kd'])
        self.slider_ki.set_val(self.initial_params['ki'])
        self.slider_speed.set_val(self.initial_params['speed'])

        # Reconnect slider callbacks
        self.cid_l = self.slider_l.on_changed(self._on_params_changed)
        self.cid_r = self.slider_r.on_changed(self._on_params_changed)
        self.cid_m = self.slider_m.on_changed(self._on_params_changed)
        self.cid_kp = self.slider_kp.on_changed(self._on_params_changed)
        self.cid_kd = self.slider_kd.on_changed(self._on_params_changed)
        self.cid_ki = self.slider_ki.on_changed(self._on_params_changed)
        self.cid_speed = self.slider_speed.on_changed(self._on_speed_changed)

        # Clear history
        self.time_history = []
        self.theta_history = []
        self.control_history = []

        # Clear plots
        self.theta_line.set_data([], [])
        self.control_line.set_data([], [])
        self.ax_theta.set_xlim(0, 10)
        self.ax_theta.set_ylim(-50, 50)
        self.ax_control.set_xlim(0, 10)
        self.ax_control.set_ylim(-5, 5)

        # Remove arrows
        self._remove_arrows()

        self.update_display()
        try:
            self.fig.canvas.draw_idle()
        except Exception:
            pass

    def _on_disturb_clicked(self, _event):
        """Callback for Disturb button."""
        self.state[0] += np.random.uniform(-0.3, 0.3)
        self.state[1] += np.random.uniform(-2, 2)

    def _remove_arrows(self):
        """Remove direction and torque arrows."""
        for arrow_attr in ('direction_arrow', 'torque_arrow'):
            arrow = getattr(self, arrow_attr, None)
            if arrow is not None:
                try:
                    arrow.remove()
                except Exception:
                    pass
                setattr(self, arrow_attr, None)

    def step_simulation(self):
        """Advance simulation by one timestep."""
        if not self.running:
            return

        try:
            # Compute control
            tau = self.controller.compute_control(self.state)

            # Integrate dynamics
            self.state = self.physics.integrate_rk4(self.state, tau, self.dt)

            # Update time and history
            self.time += self.dt
            self.time_history.append(self.time)
            self.theta_history.append(np.degrees(self.state[0]))
            self.control_history.append(tau)

            # Limit history size
            if len(self.time_history) > self.max_history:
                self.time_history.pop(0)
                self.theta_history.pop(0)
                self.control_history.pop(0)

        except Exception as exc:
            print(f"Error in simulation step: {exc}")
            self.running = False

    def update_display(self):
        """Update all visual elements."""
        try:
            # Get positions
            positions = self.physics.compute_positions_3d(self.state)
            arm_end = positions['arm_end']
            pend_end = positions['pendulum_end']

            # Update lines
            self.arm_line.set_data([0, arm_end[0]], [0, arm_end[1]])
            self.arm_line.set_3d_properties([0, arm_end[2]])

            self.pend_line.set_data([arm_end[0], pend_end[0]],
                                    [arm_end[1], pend_end[1]])
            self.pend_line.set_3d_properties([arm_end[2], pend_end[2]])

            # Update colors
            is_stable = self.physics.is_stable(self.state)
            pend_color = '#10b981' if is_stable else '#ef4444'
            self.pend_line.set_color(pend_color)

            # Update 3D objects
            self._update_3d_objects(arm_end, pend_end, pend_color)

            # Update arrows
            self._update_arrows()

            # Update status text
            self._update_status_text(pend_end[2], is_stable)

            # Update plots
            self._update_plots()

        except Exception as exc:
            print(f"Error updating display: {exc}")

    def _update_3d_objects(self, arm_end, pend_end, pend_color):
        """Update 3D spheres, cylinders, shadows, etc."""
        # Remove old objects
        for attr in ('pend_sphere', 'joint_sphere', 'base_cylinder'):
            obj = getattr(self, attr, None)
            if obj is not None:
                try:
                    obj.remove()
                except Exception:
                    pass
                setattr(self, attr, None)

        # Pendulum sphere
        u = np.linspace(0, 2 * np.pi, 30)
        v = np.linspace(0, np.pi, 30)
        radius = 0.03
        sx = pend_end[0] + radius * np.outer(np.cos(u), np.sin(v))
        sy = pend_end[1] + radius * np.outer(np.sin(u), np.sin(v))
        sz = pend_end[2] + radius * np.outer(np.ones_like(u), np.cos(v))
        self.pend_sphere = self.ax_main.plot_surface(sx, sy, sz, color=pend_color,
                                                     alpha=0.95, shade=True, antialiased=True)

        # Joint sphere
        jx = arm_end[0] + 0.02 * np.outer(np.cos(u), np.sin(v))
        jy = arm_end[1] + 0.02 * np.outer(np.sin(u), np.sin(v))
        jz = arm_end[2] + 0.02 * np.outer(np.ones_like(u), np.cos(v))
        self.joint_sphere = self.ax_main.plot_surface(jx, jy, jz, color='#2563eb',
                                                      alpha=0.9, shade=True, antialiased=True)

        # Base cylinder
        theta_c = np.linspace(0, 2 * np.pi, 30)
        z_c = np.linspace(-0.02, 0.01, 10)
        Theta, Z = np.meshgrid(theta_c, z_c)
        X = 0.055 * np.cos(Theta)
        Y = 0.055 * np.sin(Theta)
        self.base_cylinder = self.ax_main.plot_surface(X, Y, Z, color="#6b7280",
                                                       alpha=0.8, shade=True, antialiased=True)

        # Upright reference line
        if self.upright_ref is None:
            self.upright_ref, = self.ax_main.plot([arm_end[0], arm_end[0]],
                                                  [arm_end[1], arm_end[1]],
                                                  [0, self.physics.l],
                                                  color='#9ca3af', linestyle='--',
                                                  alpha=0.5, linewidth=2)
        else:
            self.upright_ref.set_data([arm_end[0], arm_end[0]],
                                      [arm_end[1], arm_end[1]])
            self.upright_ref.set_3d_properties([0, self.physics.l])

        # Shadows
        if self.shadow_arm is None:
            self.shadow_arm, = self.ax_main.plot([0, arm_end[0]], [0, arm_end[1]],
                                                 [-0.04, -0.04], color='#d1d5db',
                                                 alpha=0.3, linewidth=4)
            self.shadow_pend, = self.ax_main.plot([arm_end[0], pend_end[0]],
                                                  [arm_end[1], pend_end[1]],
                                                  [-0.04, -0.04], color='#d1d5db',
                                                  alpha=0.3, linewidth=2)
        else:
            self.shadow_arm.set_data([0, arm_end[0]], [0, arm_end[1]])
            self.shadow_arm.set_3d_properties([-0.04, -0.04])
            self.shadow_pend.set_data([arm_end[0], pend_end[0]],
                                      [arm_end[1], pend_end[1]])
            self.shadow_pend.set_3d_properties([-0.04, -0.04])

    def _update_arrows(self):
        """Update direction and torque arrows."""
        self._remove_arrows()

        phi = self.state[2]
        phi_dot = self.state[3]

        # Direction arrow
        if abs(phi_dot) > 0.01:
            arrow_radius = 0.7 * self.physics.r
            arrow_base_x = arrow_radius * np.cos(phi)
            arrow_base_y = arrow_radius * np.sin(phi)
            arrow_scale = 0.08
            arrow_dx = -arrow_scale * np.sin(phi) * np.sign(phi_dot)
            arrow_dy = arrow_scale * np.cos(phi) * np.sign(phi_dot)
            arrow_color = '#3b82f6' if phi_dot > 0 else '#ef4444'
            self.direction_arrow = self.ax_main.quiver(
                arrow_base_x, arrow_base_y, 0.02, arrow_dx, arrow_dy, 0,
                color=arrow_color, alpha=0.8, arrow_length_ratio=0.4, linewidth=3
            )

        # Torque arrow
        current_tau = self.controller.compute_control(self.state) if self.running else 0
        if abs(current_tau) > 0.1:
            torque_scale = 0.05 * min(abs(current_tau) / 5.0, 1.0)
            torque_angle = phi + (np.pi / 2 if current_tau > 0 else -np.pi / 2)
            torque_dx = torque_scale * np.cos(torque_angle)
            torque_dy = torque_scale * np.sin(torque_angle)
            torque_color = '#10b981' if current_tau > 0 else '#f59e0b'
            self.torque_arrow = self.ax_main.quiver(
                0, 0, -0.01, torque_dx, torque_dy, 0,
                color=torque_color, alpha=0.9, arrow_length_ratio=0.5, linewidth=4
            )

    def _update_status_text(self, pend_height, is_stable):
        """Update the status text display."""
        theta, theta_dot, phi, phi_dot = self.state
        current_tau = self.controller.compute_control(self.state) if self.running else 0

        # Determine rotation direction with visual indicators
        if phi_dot > 0.5:
            rotation = "↻ CCW"
        elif phi_dot < -0.5:
            rotation = "↺ CW"
        else:
            rotation = "⊗ STOPPED"

        # Determine torque direction
        if current_tau > 0.1:
            torque_dir = "CCW +"
        elif current_tau < -0.1:
            torque_dir = "CW -"
        else:
            torque_dir = "ZERO"

        status = f"θ = {np.degrees(theta):6.2f}° "
        status += f"({'UP ✓' if is_stable else 'FALLING ✗'})\n"
        status += f"φ = {np.degrees(phi):6.2f}° (arm angle)\n"
        status += f"\nARM MOTION:\n"
        status += f"ω_φ = {np.degrees(phi_dot):7.1f}°/s ({rotation})\n"
        status += f"τ   = {current_tau:6.2f} Nm ({torque_dir})\n"
        status += f"\nPEND MOTION:\n"
        status += f"ω_θ = {np.degrees(theta_dot):7.1f}°/s\n"
        status += f"Height: {pend_height:.3f} m\n"
        status += f"Status: {'STABLE' if is_stable else 'UNSTABLE'}"

        self.status_text.set_text(status)

    def _update_plots(self):
        """Update time-series plots."""
        if len(self.time_history) > 1:
            # Update data
            self.theta_line.set_data(self.time_history, self.theta_history)
            self.control_line.set_data(self.time_history, self.control_history)

            # Calculate axis limits based on actual data range
            time_min = min(self.time_history)
            time_max = max(self.time_history)
            time_range = time_max - time_min
            time_margin = max(0.5, time_range * 0.05)  # 5% margin or 0.5s minimum

            # Update theta plot limits
            theta_min = min(self.theta_history)
            theta_max = max(self.theta_history)
            theta_range = theta_max - theta_min
            theta_margin = max(5, theta_range * 0.1)  # 10% margin or 5° minimum

            self.ax_theta.set_xlim(time_min - time_margin, time_max + time_margin)
            self.ax_theta.set_ylim(theta_min - theta_margin, theta_max + theta_margin)

            # Update control plot limits
            control_min = min(self.control_history)
            control_max = max(self.control_history)
            control_range = control_max - control_min
            control_margin = max(0.5, control_range * 0.1)  # 10% margin or 0.5 Nm minimum

            self.ax_control.set_xlim(time_min - time_margin, time_max + time_margin)
            self.ax_control.set_ylim(control_min - control_margin, control_max + control_margin)

        elif len(self.time_history) == 0:
            self.theta_line.set_data([], [])
            self.control_line.set_data([], [])

    def animate(self, _frame):
        """Animation callback function."""
        try:
            steps = max(1, int(self.speed_multiplier))
            for _ in range(steps):
                if self.running:
                    self.step_simulation()
            self.update_display()

            # Return list of artists
            artists = [self.arm_line, self.pend_line, self.status_text,
                      self.theta_line, self.control_line]
            if self.upright_ref is not None:
                artists.append(self.upright_ref)
            if self.shadow_arm is not None:
                artists.extend([self.shadow_arm, self.shadow_pend])
            if self.direction_arrow is not None:
                artists.append(self.direction_arrow)
            if self.torque_arrow is not None:
                artists.append(self.torque_arrow)
            return artists
        except Exception as exc:
            print(f"Error in animation: {exc}")
            return []

    def run(self):
        """Start the animation and show the figure."""
        try:
            interval = (self.dt / self.speed_multiplier) * 1000
            self.anim = FuncAnimation(self.fig, self.animate,
                                     interval=interval, blit=False,
                                     cache_frame_data=False)
            plt.show()
        except Exception as exc:
            print(f"Error starting animation: {exc}")
