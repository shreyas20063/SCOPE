"""
Main Window for Furuta Pendulum Simulation (PyQt5)

This module provides the main application window with 3D visualization,
real-time plots, and interactive controls using PyQt5.

Course: Signals and Systems (EE204T)
Instructor: Prof. Ameer Mulla
Authors: Duggimpudi Shreyas Reddy, Prathamesh Nerpagar
"""

import numpy as np
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QPushButton, QLabel, QSlider, QGroupBox,
                              QGridLayout, QTextEdit, QSplitter, QFrame)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D


class FurutaPendulumWindow(QMainWindow):
    """
    Main window for the Furuta Pendulum simulation.

    Provides:
    - 3D visualization of the pendulum system
    - Real-time plots of angle and control torque
    - Interactive parameter adjustment sliders
    - Control buttons for start/pause, reset, and disturbance
    """

    def __init__(self, physics_model, controller):
        """
        Initialize the main window.

        Args:
            physics_model: Instance of FurutaPendulumPhysics
            controller: Instance of PIDController
        """
        super().__init__()

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

        # 3D artist references
        self.pend_sphere = None
        self.joint_sphere = None
        self.base_cylinder = None
        self.upright_ref = None
        self.shadow_arm = None
        self.shadow_pend = None
        self.direction_arrow = None
        self.torque_arrow = None

        # Setup UI
        self.init_ui()

        # Setup timer for animation
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_simulation)
        self.timer.setInterval(int(self.dt * 1000))

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle('Furuta Pendulum Simulator - PyQt5')
        self.setGeometry(100, 100, 1800, 1000)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QHBoxLayout(central_widget)

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)

        # Left panel - Visualization
        left_panel = self.create_visualization_panel()
        splitter.addWidget(left_panel)

        # Right panel - Controls
        right_panel = self.create_control_panel()
        splitter.addWidget(right_panel)

        # Set initial sizes
        splitter.setSizes([1400, 400])

        main_layout.addWidget(splitter)

    def create_visualization_panel(self):
        """Create the visualization panel with 3D view and plots."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # 3D View
        self.canvas_3d = FigureCanvas(Figure(figsize=(12, 8)))
        self.fig_3d = self.canvas_3d.figure
        self.ax_3d = self.fig_3d.add_subplot(111, projection='3d')
        self.setup_3d_view()
        layout.addWidget(self.canvas_3d, stretch=2)

        # Plots container
        plots_widget = QWidget()
        plots_layout = QHBoxLayout(plots_widget)

        # Angle plot
        self.canvas_angle = FigureCanvas(Figure(figsize=(6, 3)))
        self.fig_angle = self.canvas_angle.figure
        self.ax_angle = self.fig_angle.add_subplot(111)
        self.setup_angle_plot()
        plots_layout.addWidget(self.canvas_angle)

        # Control plot
        self.canvas_control = FigureCanvas(Figure(figsize=(6, 3)))
        self.fig_control = self.canvas_control.figure
        self.ax_control = self.fig_control.add_subplot(111)
        self.setup_control_plot()
        plots_layout.addWidget(self.canvas_control)

        layout.addWidget(plots_widget, stretch=1)

        return panel

    def create_control_panel(self):
        """Create the control panel with sliders and buttons."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)

        # Status display
        status_group = QGroupBox("System Status")
        status_layout = QVBoxLayout()
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(200)
        font = QFont("Courier", 9)
        self.status_text.setFont(font)
        status_layout.addWidget(self.status_text)
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # Physical parameters
        phys_group = QGroupBox("Physical Parameters")
        phys_layout = QGridLayout()

        self.mass_slider = self.create_slider_with_label(
            "Mass (kg)", 0.01, 0.2, self.physics.m, 100, phys_layout, 0)
        self.pend_len_slider = self.create_slider_with_label(
            "Pend Length (m)", 0.1, 0.4, self.physics.l, 100, phys_layout, 1)
        self.arm_len_slider = self.create_slider_with_label(
            "Arm Length (m)", 0.1, 0.3, self.physics.r, 100, phys_layout, 2)

        phys_group.setLayout(phys_layout)
        layout.addWidget(phys_group)

        # PID parameters
        pid_group = QGroupBox("PID Control Gains")
        pid_layout = QGridLayout()

        self.kp_slider = self.create_slider_with_label(
            "Kp", 0, 300, self.controller.Kp, 1, pid_layout, 0)
        self.kd_slider = self.create_slider_with_label(
            "Kd", 0, 50, self.controller.Kd, 1, pid_layout, 1)
        self.ki_slider = self.create_slider_with_label(
            "Ki", 0, 20, self.controller.Ki, 1, pid_layout, 2)

        pid_group.setLayout(pid_layout)
        layout.addWidget(pid_group)

        # Speed control
        speed_group = QGroupBox("Simulation Speed")
        speed_layout = QGridLayout()

        self.speed_slider = self.create_slider_with_label(
            "Speed", 0.1, 3.0, self.speed_multiplier, 10, speed_layout, 0)

        speed_group.setLayout(speed_layout)
        layout.addWidget(speed_group)

        # Control buttons
        buttons_group = QGroupBox("Controls")
        buttons_layout = QVBoxLayout()

        self.start_button = QPushButton("Start/Pause")
        self.start_button.setStyleSheet("background-color: #10b981; color: white; font-weight: bold; padding: 10px;")
        self.start_button.clicked.connect(self.toggle_simulation)
        buttons_layout.addWidget(self.start_button)

        self.reset_button = QPushButton("Reset")
        self.reset_button.setStyleSheet("background-color: #d1d5db; color: black; font-weight: bold; padding: 10px;")
        self.reset_button.clicked.connect(self.reset_simulation)
        buttons_layout.addWidget(self.reset_button)

        self.disturb_button = QPushButton("Disturb")
        self.disturb_button.setStyleSheet("background-color: #ef4444; color: white; font-weight: bold; padding: 10px;")
        self.disturb_button.clicked.connect(self.apply_disturbance)
        buttons_layout.addWidget(self.disturb_button)

        buttons_group.setLayout(buttons_layout)
        layout.addWidget(buttons_group)

        # Info text
        info_group = QGroupBox("Information")
        info_layout = QVBoxLayout()
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setHtml("""
            <p style='font-size: 9px; font-family: monospace;'>
            <b>Furuta Pendulum Control</b><br><br>
            <b>COMMON QUESTION:</b><br>
            "Why does the arm only spin one direction?"<br><br>
            <b>ANSWER: It DOESN'T!</b><br>
            The arm changes direction 50-100 times per second!<br><br>
            <b>HOW IT WORKS:</b><br>
            Uses ACCELERATION to create inertial forces that push pendulum up.<br><br>
            <b>TO SEE DIRECTION CHANGES:</b><br>
            1. Watch Control Plot (bottom right graph)<br>
            2. Line crosses zero = direction reversal!<br>
            3. Count the crossings<br>
            4. Set Speed to 0.3x (makes it visible)<br>
            5. Press Disturb - see LARGE reversals<br>
            6. Watch ω_φ in status: sign keeps flipping!<br><br>
            Arrows: Blue↔Red<br>
            τ: Positive↔Negative
            </p>
        """)
        info_layout.addWidget(info_text)
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        layout.addStretch()

        return panel

    def create_slider_with_label(self, name, min_val, max_val, init_val, scale, layout, row):
        """Create a slider with label and value display."""
        label = QLabel(name)
        layout.addWidget(label, row, 0)

        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(int(min_val * scale))
        slider.setMaximum(int(max_val * scale))
        slider.setValue(int(init_val * scale))
        slider.setTickPosition(QSlider.TicksBelow)
        slider.setTickInterval(int((max_val - min_val) * scale / 10))
        layout.addWidget(slider, row, 1)

        value_label = QLabel(f"{init_val:.2f}")
        layout.addWidget(value_label, row, 2)

        # Connect slider to update function
        slider.valueChanged.connect(lambda: self.update_slider_value(slider, value_label, scale))
        slider.valueChanged.connect(self.update_parameters)

        # Store the scale and value label for later use
        slider.scale = scale
        slider.value_label = value_label

        return slider

    def update_slider_value(self, slider, label, scale):
        """Update the slider value label."""
        value = slider.value() / scale
        label.setText(f"{value:.2f}")

    def update_parameters(self):
        """Update physics and controller parameters from sliders."""
        # Update physics parameters
        self.physics.update_parameters(
            mass=self.mass_slider.value() / self.mass_slider.scale,
            pendulum_length=self.pend_len_slider.value() / self.pend_len_slider.scale,
            arm_length=self.arm_len_slider.value() / self.arm_len_slider.scale
        )

        # Update controller gains
        self.controller.update_gains(
            kp=self.kp_slider.value() / self.kp_slider.scale,
            kd=self.kd_slider.value() / self.kd_slider.scale,
            ki=self.ki_slider.value() / self.ki_slider.scale
        )

        # Update speed
        self.speed_multiplier = max(0.1, self.speed_slider.value() / self.speed_slider.scale)

    def setup_3d_view(self):
        """Setup the 3D visualization axes."""
        self.ax_3d.set_xlim(-0.4, 0.4)
        self.ax_3d.set_ylim(-0.4, 0.4)
        self.ax_3d.set_zlim(-0.05, 0.4)
        self.ax_3d.set_facecolor('white')

        # Set pane colors
        try:
            self.ax_3d.w_xaxis.set_pane_color((0.95, 0.95, 0.95, 1.0))
            self.ax_3d.w_yaxis.set_pane_color((0.95, 0.95, 0.95, 1.0))
            self.ax_3d.w_zaxis.set_pane_color((0.98, 0.98, 1.0, 1.0))
        except AttributeError:
            pass

        self.ax_3d.set_title('Furuta Pendulum - 3D View', fontsize=14,
                            fontweight='bold', color='#1a1a1a', pad=20)
        self.ax_3d.set_xlabel('X (meters)', color='#333', fontsize=10)
        self.ax_3d.set_ylabel('Y (meters)', color='#333', fontsize=10)
        self.ax_3d.set_zlabel('Height (meters)', color='#333', fontsize=10)
        self.ax_3d.view_init(elev=25, azim=45)
        self.ax_3d.grid(True, alpha=0.4, color='#999999', linestyle='-', linewidth=0.5)

        # Draw base platform
        self.draw_base_platform()

        # Initialize 3D lines
        self.arm_line, = self.ax_3d.plot([], [], [], color='#2563eb',
                                         linewidth=8, solid_capstyle='round')
        self.pend_line, = self.ax_3d.plot([], [], [], color='#10b981',
                                          linewidth=5, solid_capstyle='round')

        self.fig_3d.tight_layout()

    def draw_base_platform(self):
        """Draw the base platform and floor grid."""
        circle_theta = np.linspace(0, 2 * np.pi, 100)

        # Base circle
        base_radius = 0.06
        base_x = base_radius * np.cos(circle_theta)
        base_y = base_radius * np.sin(circle_theta)
        base_z = np.zeros_like(base_x)
        self.ax_3d.plot(base_x, base_y, base_z, '#555555', linewidth=3, alpha=0.9)

        # Floor circle
        floor_radius = 0.38
        floor_x = floor_radius * np.cos(circle_theta)
        floor_y = floor_radius * np.sin(circle_theta)
        floor_z = np.ones_like(floor_x) * (-0.04)
        self.ax_3d.plot(floor_x, floor_y, floor_z, '#dddddd', linewidth=1, alpha=0.3)

        # Floor radial lines
        for angle in np.linspace(0, 2 * np.pi, 8, endpoint=False):
            self.ax_3d.plot([0, floor_radius * np.cos(angle)],
                           [0, floor_radius * np.sin(angle)],
                           [-0.04, -0.04], '#e5e5e5', linewidth=0.5, alpha=0.3)

    def setup_angle_plot(self):
        """Setup the pendulum angle time-series plot."""
        self.ax_angle.set_facecolor('#fafafa')
        self.ax_angle.grid(True, alpha=0.4, color='#cccccc', linestyle='-', linewidth=0.5)
        self.ax_angle.set_xlabel('Time (s)', color='#333', fontsize=10)
        self.ax_angle.set_ylabel('Angle (deg)', color='#333', fontsize=10)
        self.ax_angle.set_title('Pendulum Angle', fontweight='bold',
                               color='#1a1a1a', fontsize=11)
        self.theta_line, = self.ax_angle.plot([], [], color='#10b981',
                                              linewidth=2.5, label='θ')
        self.ax_angle.axhline(y=0, color='#666', linestyle='--', alpha=0.6, linewidth=1)
        self.fig_angle.tight_layout()

    def setup_control_plot(self):
        """Setup the control input time-series plot."""
        self.ax_control.set_facecolor('#fafafa')
        self.ax_control.grid(True, alpha=0.4, color='#cccccc', linestyle='-', linewidth=0.5)
        self.ax_control.set_xlabel('Time (s)', color='#333', fontsize=10)
        self.ax_control.set_ylabel('Torque (Nm)', color='#333', fontsize=10)
        self.ax_control.set_title('Control Input', fontweight='bold',
                                 color='#1a1a1a', fontsize=11)
        self.control_line, = self.ax_control.plot([], [], color='#3b82f6',
                                                  linewidth=2.5, label='τ')
        self.ax_control.axhline(y=0, color='#666', linestyle='--', alpha=0.6, linewidth=1)
        self.fig_control.tight_layout()

    def toggle_simulation(self):
        """Toggle simulation running state."""
        self.running = not self.running
        if self.running:
            self.timer.start()
        else:
            self.timer.stop()

    def reset_simulation(self):
        """Reset simulation to initial state."""
        self.running = False
        self.timer.stop()

        self.state = self.initial_params['state'].copy()
        self.time = 0.0

        # Reset physics parameters
        self.physics.update_parameters(
            mass=self.initial_params['mass'],
            pendulum_length=self.initial_params['pendulum_length'],
            arm_length=self.initial_params['arm_length']
        )

        # Reset controller
        self.controller.update_gains(
            kp=self.initial_params['kp'],
            kd=self.initial_params['kd'],
            ki=self.initial_params['ki']
        )
        self.controller.reset()

        # Reset speed
        self.speed_multiplier = self.initial_params['speed']

        # Reset sliders
        self.mass_slider.setValue(int(self.initial_params['mass'] * self.mass_slider.scale))
        self.pend_len_slider.setValue(int(self.initial_params['pendulum_length'] * self.pend_len_slider.scale))
        self.arm_len_slider.setValue(int(self.initial_params['arm_length'] * self.arm_len_slider.scale))
        self.kp_slider.setValue(int(self.initial_params['kp'] * self.kp_slider.scale))
        self.kd_slider.setValue(int(self.initial_params['kd'] * self.kd_slider.scale))
        self.ki_slider.setValue(int(self.initial_params['ki'] * self.ki_slider.scale))
        self.speed_slider.setValue(int(self.initial_params['speed'] * self.speed_slider.scale))

        # Clear history
        self.time_history = []
        self.theta_history = []
        self.control_history = []

        # Clear plots
        self.theta_line.set_data([], [])
        self.control_line.set_data([], [])
        self.ax_angle.set_xlim(0, 10)
        self.ax_angle.set_ylim(-50, 50)
        self.ax_control.set_xlim(0, 10)
        self.ax_control.set_ylim(-5, 5)

        # Remove arrows
        self.remove_arrows()

        self.update_display()
        self.canvas_3d.draw()
        self.canvas_angle.draw()
        self.canvas_control.draw()

    def apply_disturbance(self):
        """Apply random disturbance to the system."""
        # Apply disturbance to pendulum angle and angular velocity
        self.state[0] += np.random.uniform(-0.3, 0.3)
        self.state[1] += np.random.uniform(-2, 2)

        # Update display to show the disturbance effect
        self.update_display()

    def remove_arrows(self):
        """Remove direction and torque arrows from 3D plot."""
        for arrow_attr in ('direction_arrow', 'torque_arrow'):
            arrow = getattr(self, arrow_attr, None)
            if arrow is not None:
                try:
                    arrow.remove()
                except Exception:
                    pass
                setattr(self, arrow_attr, None)

    def update_simulation(self):
        """Update simulation state (called by timer)."""
        if not self.running:
            return

        try:
            steps = max(1, int(self.speed_multiplier))
            for _ in range(steps):
                if self.running:
                    self.step_simulation()

            self.update_display()

        except Exception as exc:
            print(f"Error in simulation update: {exc}")
            self.running = False
            self.timer.stop()

    def step_simulation(self):
        """Advance simulation by one timestep."""
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

            # Update 3D view
            self.update_3d_view(arm_end, pend_end)

            # Update plots
            self.update_plots()

            # Update status text
            self.update_status_text(positions['pendulum_height'])

            # Redraw canvases
            self.canvas_3d.draw()
            self.canvas_angle.draw()
            self.canvas_control.draw()

        except Exception as exc:
            print(f"Error updating display: {exc}")

    def update_3d_view(self, arm_end, pend_end):
        """Update the 3D visualization."""
        # Update lines
        self.arm_line.set_data([0, arm_end[0]], [0, arm_end[1]])
        self.arm_line.set_3d_properties([0, arm_end[2]])

        self.pend_line.set_data([arm_end[0], pend_end[0]],
                               [arm_end[1], pend_end[1]])
        self.pend_line.set_3d_properties([arm_end[2], pend_end[2]])

        # Update color based on stability
        is_stable = self.physics.is_stable(self.state)
        pend_color = '#10b981' if is_stable else '#ef4444'
        self.pend_line.set_color(pend_color)

        # Update 3D objects
        self.update_3d_objects(arm_end, pend_end, pend_color)

        # Update arrows
        self.update_arrows()

    def update_3d_objects(self, arm_end, pend_end, pend_color):
        """Update 3D spheres, cylinders, shadows."""
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
        self.pend_sphere = self.ax_3d.plot_surface(sx, sy, sz, color=pend_color,
                                                   alpha=0.95, shade=True, antialiased=True)

        # Joint sphere
        jx = arm_end[0] + 0.02 * np.outer(np.cos(u), np.sin(v))
        jy = arm_end[1] + 0.02 * np.outer(np.sin(u), np.sin(v))
        jz = arm_end[2] + 0.02 * np.outer(np.ones_like(u), np.cos(v))
        self.joint_sphere = self.ax_3d.plot_surface(jx, jy, jz, color='#2563eb',
                                                    alpha=0.9, shade=True, antialiased=True)

        # Base cylinder
        theta_c = np.linspace(0, 2 * np.pi, 30)
        z_c = np.linspace(-0.02, 0.01, 10)
        Theta, Z = np.meshgrid(theta_c, z_c)
        X = 0.055 * np.cos(Theta)
        Y = 0.055 * np.sin(Theta)
        self.base_cylinder = self.ax_3d.plot_surface(X, Y, Z, color="#6b7280",
                                                     alpha=0.8, shade=True, antialiased=True)

        # Upright reference line
        if self.upright_ref is None:
            self.upright_ref, = self.ax_3d.plot([arm_end[0], arm_end[0]],
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
            self.shadow_arm, = self.ax_3d.plot([0, arm_end[0]], [0, arm_end[1]],
                                              [-0.04, -0.04], color='#d1d5db',
                                              alpha=0.3, linewidth=4)
            self.shadow_pend, = self.ax_3d.plot([arm_end[0], pend_end[0]],
                                               [arm_end[1], pend_end[1]],
                                               [-0.04, -0.04], color='#d1d5db',
                                               alpha=0.3, linewidth=2)
        else:
            self.shadow_arm.set_data([0, arm_end[0]], [0, arm_end[1]])
            self.shadow_arm.set_3d_properties([-0.04, -0.04])
            self.shadow_pend.set_data([arm_end[0], pend_end[0]],
                                     [arm_end[1], pend_end[1]])
            self.shadow_pend.set_3d_properties([-0.04, -0.04])

    def update_arrows(self):
        """Update direction and torque arrows."""
        self.remove_arrows()

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
            self.direction_arrow = self.ax_3d.quiver(
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
            self.torque_arrow = self.ax_3d.quiver(
                0, 0, -0.01, torque_dx, torque_dy, 0,
                color=torque_color, alpha=0.9, arrow_length_ratio=0.5, linewidth=4
            )

    def update_plots(self):
        """Update time-series plots."""
        if len(self.time_history) > 1:
            # Update data
            self.theta_line.set_data(self.time_history, self.theta_history)
            self.control_line.set_data(self.time_history, self.control_history)

            # Calculate axis limits
            time_min = min(self.time_history)
            time_max = max(self.time_history)
            time_range = time_max - time_min
            time_margin = max(0.5, time_range * 0.05)

            # Update theta plot limits
            theta_min = min(self.theta_history)
            theta_max = max(self.theta_history)
            theta_range = theta_max - theta_min
            theta_margin = max(5, theta_range * 0.1)

            self.ax_angle.set_xlim(time_min - time_margin, time_max + time_margin)
            self.ax_angle.set_ylim(theta_min - theta_margin, theta_max + theta_margin)

            # Update control plot limits
            control_min = min(self.control_history)
            control_max = max(self.control_history)
            control_range = control_max - control_min
            control_margin = max(0.5, control_range * 0.1)

            self.ax_control.set_xlim(time_min - time_margin, time_max + time_margin)
            self.ax_control.set_ylim(control_min - control_margin, control_max + control_margin)

    def update_status_text(self, pend_height):
        """Update the status text display."""
        theta, theta_dot, phi, phi_dot = self.state
        current_tau = self.controller.compute_control(self.state) if self.running else 0
        is_stable = self.physics.is_stable(self.state)

        # Determine rotation direction
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
        status += f"φ = {np.degrees(phi):6.2f}° (arm angle)\n\n"
        status += f"ARM MOTION:\n"
        status += f"ω_φ = {np.degrees(phi_dot):7.1f}°/s ({rotation})\n"
        status += f"τ   = {current_tau:6.2f} Nm ({torque_dir})\n\n"
        status += f"PEND MOTION:\n"
        status += f"ω_θ = {np.degrees(theta_dot):7.1f}°/s\n"
        status += f"Height: {pend_height:.3f} m\n"
        status += f"Status: {'STABLE' if is_stable else 'UNSTABLE'}"

        self.status_text.setText(status)
