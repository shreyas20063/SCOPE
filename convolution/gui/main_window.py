"""
Main window implementation for the Convolution Simulator.

This module contains the primary GUI class that orchestrates all
user interface components and handles the main application logic.
"""

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QRadioButton, QComboBox, QCheckBox,
                             QFrame, QMessageBox, QButtonGroup)
from PyQt5.QtCore import Qt, pyqtSignal
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
import matplotlib.animation as animation

# Import core modules
from core.convolution import ConvolutionEngine
from core.signals import SignalParser, DemoSignals
from core.utils import PlotUtils, AnimationUtils, ValidationUtils

# Import GUI components
from .controls import ControlPanel
from .plotting import PlotManager
from .themes import ThemeManager

class ConvolutionSimulator(QMainWindow):
    """Main application class for the Convolution Simulator."""

    def __init__(self):
        super().__init__()

        # Initialize core components
        self.convolution_engine = ConvolutionEngine()
        self.signal_parser = SignalParser()
        self.plot_utils = PlotUtils()
        self.animation_utils = AnimationUtils()

        # Initialize state variables
        self.setup_state_variables()

        # Initialize theme manager first (needed by setup_ui)
        self.theme_manager = ThemeManager(self)

        # Initialize GUI components
        self.setup_ui()
        self.plot_manager = PlotManager(self)
        self.control_panel = ControlPanel(self)

        # Bind events and initialize
        self.bind_events()
        self.theme_manager.apply_theme()
        self.update_mode_and_type()

    def setup_state_variables(self):
        """Initialize all state variables."""
        # Mode and type variables
        self.is_continuous = True
        self.is_demo_mode = True
        self.demo_choice = ""
        self.custom_x_str = "rect(t)"
        self.custom_h_str = "exp(-t) * u(t)"
        self.visualization_style = "Mathematical"
        self.dark_mode = False

        # Simulation variables
        self.t = np.linspace(-20, 20, 8000)
        self.n = np.arange(-10, 21)
        self.t_y = np.array([])
        self.n_y = np.array([])
        self.x_func = lambda t: np.zeros_like(t)
        self.h_func = lambda t: np.zeros_like(t)
        self.x_sequence = np.zeros_like(self.n)
        self.h_sequence = np.zeros_like(self.n)
        self.y_result = np.zeros_like(self.t)

        # Animation variables
        self.anim = None
        self.current_time_val = 0
        self.is_playing = False

    def setup_ui(self):
        """Create and layout all UI components."""
        self.setWindowTitle("Convolution Simulator")
        self.setGeometry(100, 100, 1400, 900)

        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Create header
        self.header_frame = self.create_header()
        main_layout.addWidget(self.header_frame)

        # Create body with panels
        body_layout = QHBoxLayout()

        # Left control panel
        self.left_panel = QWidget()
        self.left_panel.setMaximumWidth(250)
        body_layout.addWidget(self.left_panel)

        # Center plotting area
        self.center_panel = self.create_center_panel()
        body_layout.addWidget(self.center_panel, stretch=1)

        # Right panel (initially hidden)
        self.right_panel = self.create_right_panel()
        self.right_panel.hide()
        body_layout.addWidget(self.right_panel)

        main_layout.addLayout(body_layout, stretch=1)

        # Footer
        self.footer_frame = self.create_footer()
        main_layout.addWidget(self.footer_frame)

    def create_header(self):
        """Create the header with main controls."""
        header_frame = QWidget()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 10)

        # Title
        title_label = QLabel("Convolution Simulator")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        header_layout.addWidget(title_label)
        header_layout.addSpacing(20)

        # Signal type selection
        self.continuous_radio = QRadioButton("Continuous")
        self.continuous_radio.setChecked(True)
        self.continuous_radio.toggled.connect(self.on_signal_type_changed)
        header_layout.addWidget(self.continuous_radio)

        self.discrete_radio = QRadioButton("Discrete")
        self.discrete_radio.toggled.connect(self.on_signal_type_changed)
        header_layout.addWidget(self.discrete_radio)
        header_layout.addSpacing(20)

        # Mode selection
        self.demo_mode_radio = QRadioButton("Demo Mode")
        self.demo_mode_radio.setChecked(True)
        self.demo_mode_radio.toggled.connect(self.on_mode_changed)
        header_layout.addWidget(self.demo_mode_radio)

        self.demo_selector = QComboBox()
        self.demo_selector.setMinimumWidth(250)
        self.demo_selector.currentTextChanged.connect(self.on_demo_selected)
        header_layout.addWidget(self.demo_selector)

        self.custom_mode_radio = QRadioButton("Custom Mode")
        self.custom_mode_radio.toggled.connect(self.on_mode_changed)
        header_layout.addWidget(self.custom_mode_radio)

        header_layout.addStretch()

        # Theme toggle
        self.dark_mode_checkbox = QCheckBox("Dark Mode")
        self.dark_mode_checkbox.stateChanged.connect(self.theme_manager.toggle_theme)
        header_layout.addWidget(self.dark_mode_checkbox)

        return header_frame

    def create_center_panel(self):
        """Create the center plotting panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create matplotlib figure
        self.fig = Figure(figsize=(8, 8), dpi=100)
        self.canvas = FigureCanvasQTAgg(self.fig)
        layout.addWidget(self.canvas)

        # Create subplots
        self.ax_x = self.fig.add_subplot(4, 1, 1)
        self.ax_h = self.fig.add_subplot(4, 1, 2)
        self.ax_prod = self.fig.add_subplot(4, 1, 3)
        self.ax_y = self.fig.add_subplot(4, 1, 4)

        self.fig.tight_layout()
        return panel

    def create_right_panel(self):
        """Create the right panel for block-step visualization."""
        panel = QWidget()
        panel.setMaximumWidth(300)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 0, 0, 0)

        # Create figure for block diagram
        self.block_fig = Figure(figsize=(4, 8), dpi=100)
        self.block_canvas = FigureCanvasQTAgg(self.block_fig)
        layout.addWidget(self.block_canvas)

        # Create block diagram subplots
        self.ax_block_flip = self.block_fig.add_subplot(5, 1, 1)
        self.ax_block_shift = self.block_fig.add_subplot(5, 1, 2)
        self.ax_block_multiply = self.block_fig.add_subplot(5, 1, 3)
        self.ax_block_sum = self.block_fig.add_subplot(5, 1, 4)

        self.block_fig.tight_layout()
        return panel

    def create_footer(self):
        """Create the footer with math display."""
        footer_frame = QWidget()
        footer_layout = QHBoxLayout(footer_frame)
        footer_layout.setContentsMargins(0, 10, 0, 0)

        self.math_label = QLabel("y(t) = ∫ x(τ)h(t-τ)dτ")
        self.math_label.setStyleSheet("font-size: 12pt;")
        footer_layout.addWidget(self.math_label)

        footer_layout.addStretch()

        self.reference_label = QLabel("Signals and Systems - Convolution Simulator")
        self.reference_label.setStyleSheet("color: gray;")
        footer_layout.addWidget(self.reference_label)

        return footer_frame

    def bind_events(self):
        """Bind keyboard and other events."""
        # Keyboard shortcuts will be handled through keyPressEvent
        pass

    def keyPressEvent(self, event):
        """Handle keyboard events."""
        if event.key() == Qt.Key_Space:
            self.toggle_animation()
        elif event.key() == Qt.Key_Right:
            self.step_forward()
        elif event.key() == Qt.Key_Left:
            self.step_backward()
        else:
            super().keyPressEvent(event)

    def on_signal_type_changed(self):
        """Handle signal type change (continuous/discrete)."""
        self.is_continuous = self.continuous_radio.isChecked()
        self.update_mode_and_type()

    def on_mode_changed(self):
        """Handle mode change (demo/custom)."""
        self.is_demo_mode = self.demo_mode_radio.isChecked()
        self.update_mode_and_type()

    def update_mode_and_type(self):
        """Update UI and state when mode or signal type changes."""
        self.stop_animation()

        if self.is_demo_mode:
            self.demo_selector.setEnabled(True)
            # Update demo choices based on signal type
            choices = DemoSignals.get_demo_choices(self.is_continuous)
            self.demo_selector.clear()
            self.demo_selector.addItems(choices)
            if choices:
                self.demo_choice = choices[0]
                self.demo_selector.setCurrentText(self.demo_choice)
            self.on_demo_selected(self.demo_choice)
        else:
            self.demo_selector.setEnabled(False)
            # Set default custom expressions
            if self.is_continuous:
                self.custom_x_str = "exp(-t) * u(t)"
                self.custom_h_str = "rect(t-1)"
            else:
                self.custom_x_str = "0.5**n * u(n)"
                self.custom_h_str = "[1, 1, 1]"
            # Update input fields
            if hasattr(self.control_panel, 'update_input_fields'):
                self.control_panel.update_input_fields()

        self.compute_convolution()

    def on_demo_selected(self, choice):
        """Handle demo selection."""
        if not choice:
            return
        self.demo_choice = choice
        x_expr, h_expr = DemoSignals.get_demo_signals(choice, self.is_continuous)
        self.custom_x_str = x_expr
        self.custom_h_str = h_expr
        # Update input fields
        if hasattr(self.control_panel, 'update_input_fields'):
            self.control_panel.update_input_fields()
        self.compute_convolution()

    def compute_convolution(self):
        """Compute convolution for current signals."""
        self.stop_animation()

        try:
            if self.is_continuous:
                self._compute_continuous_convolution()
            else:
                self._compute_discrete_convolution()

            self._update_slider_range()
            self.plot_manager.update_plots()

        except Exception as e:
            QMessageBox.critical(self, "Computation Error",
                               f"Error computing convolution: {str(e)}")

    def _compute_continuous_convolution(self):
        """Compute continuous-time convolution."""
        x_expr = self.signal_parser.parse_expression(self.custom_x_str, 't')
        h_expr = self.signal_parser.parse_expression(self.custom_h_str, 't')

        self.x_func = self.signal_parser.create_function_from_expression(x_expr, 't')
        self.h_func = self.signal_parser.create_function_from_expression(h_expr, 't')

        # Get sampling rate from control panel
        sampling_rate = getattr(self.control_panel, 'get_sampling_rate', lambda: 500)()

        self.t_y, self.y_result = self.convolution_engine.compute_continuous_convolution(
            self.x_func, self.h_func, sampling_rate
        )

    def _compute_discrete_convolution(self):
        """Compute discrete-time convolution."""
        self.n = np.arange(-20, 21)

        x_expr = self.signal_parser.parse_expression(self.custom_x_str, 'n')
        h_expr = self.signal_parser.parse_expression(self.custom_h_str, 'n')

        # Parse sequences
        raw_x, start_x = self.signal_parser.parse_discrete_sequence(x_expr, self.n)
        raw_h, start_h = self.signal_parser.parse_discrete_sequence(h_expr, self.n)

        # Create full sequences on n grid
        self.x_sequence = np.zeros_like(self.n, dtype=float)
        self.h_sequence = np.zeros_like(self.n, dtype=float)

        # Place sequences at correct positions
        for i, val in enumerate(raw_x):
            idx = start_x + i
            if self.n[0] <= idx <= self.n[-1]:
                self.x_sequence[idx - self.n[0]] = val

        for i, val in enumerate(raw_h):
            idx = start_h + i
            if self.n[0] <= idx <= self.n[-1]:
                self.h_sequence[idx - self.n[0]] = val

        self.n_y, self.y_result = self.convolution_engine.compute_discrete_convolution(
            raw_x, raw_h, start_x, start_h
        )

    def _update_slider_range(self):
        """Update time slider range based on computed results."""
        if hasattr(self.control_panel, 'update_time_slider_range'):
            if self.is_continuous:
                slider_min, slider_max = -15, 15
            elif len(self.n_y) > 0:
                slider_min = min(self.n_y[0], self.n[0]) - 2
                slider_max = max(self.n_y[-1], self.n[-1]) + 2
            else:
                slider_min, slider_max = -10, 10

            self.control_panel.update_time_slider_range(slider_min, slider_max)

    def toggle_animation(self):
        """Toggle animation play/pause."""
        if self.anim and self.is_playing:
            self.stop_animation()
        else:
            self.start_animation()

    def start_animation(self):
        """Start convolution animation."""
        if hasattr(self.control_panel, 'get_time_range'):
            start_val, end_val = self.control_panel.get_time_range()
            speed_multiplier = getattr(self.control_panel, 'get_playback_speed', lambda: 1.0)()

            frames = self.animation_utils.create_frame_sequence(
                start_val, end_val, self.is_continuous
            )
            interval = self.animation_utils.calculate_animation_interval(speed_multiplier)

            self.anim = animation.FuncAnimation(
                self.fig, self.animate_step, frames=frames,
                interval=interval, repeat=False, blit=False
            )
            self.is_playing = True
            self.canvas.draw()

    def stop_animation(self):
        """Stop convolution animation."""
        self.is_playing = False
        if self.anim is not None:
            try:
                self.anim.event_source.stop()
            except:
                pass
            self.anim = None

    def animate_step(self, time_val):
        """Animation step function."""
        self.current_time_val = time_val
        if hasattr(self.control_panel, 'set_time_value'):
            self.control_panel.set_time_value(time_val)
        self.plot_manager.update_plots(time_val)

    def step_forward(self):
        """Step animation forward."""
        if hasattr(self.control_panel, 'step_time_forward'):
            self.control_panel.step_time_forward()

    def step_backward(self):
        """Step animation backward."""
        if hasattr(self.control_panel, 'step_time_backward'):
            self.control_panel.step_time_backward()

    # Getter methods for plot manager
    def get_current_axes(self):
        """Get current matplotlib axes."""
        return [self.ax_x, self.ax_h, self.ax_prod, self.ax_y]

    def get_block_axes(self):
        """Get block diagram axes."""
        return [self.ax_block_flip, self.ax_block_shift,
                self.ax_block_multiply, self.ax_block_sum]

    def get_current_signals(self):
        """Get current signal data."""
        return {
            'x_func': self.x_func,
            'h_func': self.h_func,
            'x_sequence': self.x_sequence,
            'h_sequence': self.h_sequence,
            't': self.t,
            'n': self.n,
            't_y': self.t_y,
            'n_y': self.n_y,
            'y_result': self.y_result
        }
