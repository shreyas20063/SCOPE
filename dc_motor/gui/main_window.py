"""
Main Window Module
PyQt5 main application window
"""

from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStatusBar
from PyQt5.QtCore import Qt

from gui.control_panel import ControlPanel
from gui.plot_canvas import PlotCanvas
from core.motor_system import SystemCalculator


class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()

        # Initialize system calculator
        self.calculator = SystemCalculator()

        # Default parameters
        self.alpha = 10.0
        self.beta = 0.5
        self.gamma = 1.0
        self.p = 10.0
        self.model_type = 'First-Order'

        # Setup UI
        self.init_ui()

        # Initial plot
        self.update_plots()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("DC Motor Feedback Control Simulation")
        self.setGeometry(100, 100, 1600, 900)

        # Create central widget and main layout
        central_widget = QWidget()
        main_layout = QHBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # Create control panel
        self.control_panel = ControlPanel()
        self.control_panel.parameters_changed.connect(self.on_parameters_changed)
        self.control_panel.model_changed.connect(self.on_model_changed)
        self.control_panel.reset_requested.connect(self.on_reset_requested)

        # Create plot canvas
        self.plot_canvas = PlotCanvas(width=16, height=10, dpi=100)

        # Add widgets to layout
        main_layout.addWidget(self.control_panel)
        main_layout.addWidget(self.plot_canvas, stretch=1)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Adjust parameters to see system response")

    def on_parameters_changed(self, alpha, beta, gamma, p):
        """Handle parameter changes from control panel"""
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.p = p
        self.update_plots()
        self.status_bar.showMessage(
            f"Parameters updated: α={alpha:.2f}, β={beta:.2f}, γ={gamma:.2f}" +
            (f", p={p:.2f}" if self.model_type == 'Second-Order' else "")
        )

    def on_model_changed(self, model_type):
        """Handle model type change from control panel"""
        self.model_type = model_type
        self.update_plots()
        self.status_bar.showMessage(f"Model changed to: {model_type}")

    def on_reset_requested(self):
        """Handle reset button click"""
        params = self.control_panel.get_parameters()
        self.alpha = params['alpha']
        self.beta = params['beta']
        self.gamma = params['gamma']
        self.p = params['p']
        self.model_type = params['model_type']
        self.update_plots()
        self.status_bar.showMessage("Parameters reset to default values")

    def update_plots(self):
        """Update all plots with current parameters"""
        # Calculate system
        sys, poles, zeros = self.calculator.get_system(
            self.model_type, self.alpha, self.beta, self.gamma, self.p
        )

        # Update plots
        self.plot_canvas.update_plots(
            sys, poles, zeros, self.model_type,
            self.alpha, self.beta, self.gamma, self.p
        )

        # Update parameter display in control panel
        self.control_panel.update_param_display()
