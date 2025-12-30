"""
Main window for the Feedback System Analysis Simulator
PyQt5-based GUI with tabbed layout
"""

import numpy as np
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QLabel, QSlider, QGroupBox, QFrame, QTabWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from utils.config import (DEFAULT_K0, DEFAULT_ALPHA, DEFAULT_BETA, DEFAULT_INPUT_AMP,
                          OMEGA_MIN, OMEGA_MAX, OMEGA_POINTS, TIME_MAX, TIME_POINTS,
                          BETA_RANGE, K0_RANGE, ALPHA_RANGE, INPUT_RANGE, setup_plot_style)
from core.calculations import (calculate_metrics, calculate_step_response,
                               calculate_bode_magnitude, calculate_bode_phase)
from gui.plot_widgets import (StepResponseCanvas, BodeMagnitudeCanvas, BodePhaseCanvas,
                               SPlaneCanvas, InfoPanelCanvas, MetricsPanelCanvas,
                               BlockDiagramCanvas)


class FeedbackAmplifierWindow(QMainWindow):
    """Main window for the interactive feedback system analysis simulator"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Feedback System Analysis')
        self.setGeometry(100, 100, 1100, 700)

        # Set default parameters
        self.K0 = DEFAULT_K0
        self.alpha = DEFAULT_ALPHA
        self.beta = DEFAULT_BETA
        self.input_amp = DEFAULT_INPUT_AMP

        # Create frequency and time arrays
        self.omega = np.logspace(OMEGA_MIN, OMEGA_MAX, OMEGA_POINTS)
        self.t = np.linspace(0, TIME_MAX, TIME_POINTS)

        setup_plot_style()
        self.init_ui()
        self.update_plots()

    def init_ui(self):
        """Initialize the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # Left: Control panel
        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel, stretch=0)

        # Right: Tabbed content
        tabs = self.create_tabs()
        main_layout.addWidget(tabs, stretch=1)

    def create_control_panel(self):
        """Create compact sidebar control panel"""
        panel = QFrame()
        panel.setFixedWidth(200)
        panel.setStyleSheet("""
            QFrame {
                background-color: #f5f6fa;
                border: 1px solid #dcdde1;
                border-radius: 6px;
            }
        """)

        layout = QVBoxLayout(panel)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)

        # Title
        title = QLabel("Parameters")
        title.setFont(QFont('Arial', 11, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #0077b6;")
        layout.addWidget(title)

        # Sliders
        layout.addWidget(self.create_slider("β (Feedback)", BETA_RANGE, self.beta, 4, self.on_beta_changed, "beta"))
        layout.addWidget(self.create_slider("K₀ (Gain)", K0_RANGE, self.K0, 0, self.on_k0_changed, "k0"))
        layout.addWidget(self.create_slider("α (rad/s)", ALPHA_RANGE, self.alpha, 1, self.on_alpha_changed, "alpha"))
        layout.addWidget(self.create_slider("Input (V)", INPUT_RANGE, self.input_amp, 2, self.on_input_changed, "input"))

        # Status display
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: white;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 8px;
                font-size: 9pt;
            }
        """)
        layout.addWidget(self.status_label)

        layout.addStretch()
        return panel

    def create_slider(self, label_text, range_config, initial_value, decimals, callback, name):
        """Create a slider group"""
        group = QGroupBox(label_text)
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 9pt;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                margin-top: 6px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 6px;
                padding: 0 3px;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(2)

        # Value label
        if decimals == 0:
            value_text = f"{initial_value:.0f}"
        elif decimals == 4:
            value_text = f"{initial_value:.4f}"
        else:
            value_text = f"{initial_value:.{decimals}f}"

        value_label = QLabel(value_text)
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setFont(QFont('Arial', 12, QFont.Bold))
        value_label.setStyleSheet("color: #0077b6;")
        setattr(self, f"{name}_value_label", value_label)
        layout.addWidget(value_label)

        # Slider
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(int(range_config[0] / range_config[2]))
        slider.setMaximum(int(range_config[1] / range_config[2]))
        slider.setValue(int(initial_value / range_config[2]))
        slider.valueChanged.connect(callback)
        slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 6px;
                background: #e0e0e0;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #0077b6;
                width: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
        """)
        setattr(self, f"{name}_slider", slider)
        layout.addWidget(slider)

        group.setLayout(layout)
        return group

    def create_tabs(self):
        """Create tabbed content area"""
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background: white;
            }
            QTabBar::tab {
                background: #ecf0f1;
                border: 1px solid #bdc3c7;
                padding: 6px 14px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom-color: white;
            }
        """)

        # Tab 1: Response plots
        tabs.addTab(self.create_response_tab(), "Response")

        # Tab 2: Analysis (S-plane + Metrics)
        tabs.addTab(self.create_analysis_tab(), "Analysis")

        # Tab 3: Info (Equations + Diagram)
        tabs.addTab(self.create_info_tab(), "Info")

        return tabs

    def create_response_tab(self):
        """Create response plots tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(4)
        layout.setContentsMargins(4, 4, 4, 4)

        self.step_canvas = StepResponseCanvas(self)
        self.bode_mag_canvas = BodeMagnitudeCanvas(self)
        self.bode_phase_canvas = BodePhaseCanvas(self)

        layout.addWidget(self.step_canvas, stretch=1)
        layout.addWidget(self.bode_mag_canvas, stretch=1)
        layout.addWidget(self.bode_phase_canvas, stretch=1)

        return widget

    def create_analysis_tab(self):
        """Create analysis tab with S-plane and metrics"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setSpacing(8)
        layout.setContentsMargins(4, 4, 4, 4)

        self.s_plane_canvas = SPlaneCanvas(self)
        self.metrics_canvas = MetricsPanelCanvas(self)

        layout.addWidget(self.s_plane_canvas, stretch=1)
        layout.addWidget(self.metrics_canvas, stretch=1)

        return widget

    def create_info_tab(self):
        """Create info tab with equations and diagram"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setSpacing(8)
        layout.setContentsMargins(4, 4, 4, 4)

        self.info_canvas = InfoPanelCanvas(self)
        self.diagram_canvas = BlockDiagramCanvas(self)

        layout.addWidget(self.info_canvas, stretch=1)
        layout.addWidget(self.diagram_canvas, stretch=1)

        return widget

    def on_beta_changed(self, value):
        """Handle beta slider change"""
        self.beta = value * BETA_RANGE[2]
        self.beta_value_label.setText(f'{self.beta:.4f}')
        self.update_plots()

    def on_k0_changed(self, value):
        """Handle K0 slider change"""
        self.K0 = value * K0_RANGE[2]
        self.k0_value_label.setText(f'{self.K0:.0f}')
        self.update_plots()

    def on_alpha_changed(self, value):
        """Handle alpha slider change"""
        self.alpha = value * ALPHA_RANGE[2]
        self.alpha_value_label.setText(f'{self.alpha:.1f}')
        self.update_plots()

    def on_input_changed(self, value):
        """Handle input amplitude slider change"""
        self.input_amp = value * INPUT_RANGE[2]
        self.input_value_label.setText(f'{self.input_amp:.2f}')
        self.update_plots()

    def update_plots(self):
        """Update all plots with current parameter values"""
        # Calculate metrics
        metrics = calculate_metrics(self.K0, self.alpha, self.beta)

        # Calculate responses
        ol_step, cl_step = calculate_step_response(self.K0, self.alpha, self.beta,
                                                    self.input_amp, self.t)
        mag_ol, mag_cl = calculate_bode_magnitude(self.K0, self.alpha, self.beta, self.omega)
        phase_ol, phase_cl = calculate_bode_phase(self.K0, self.alpha, self.beta, self.omega)

        # Update all plots
        self.step_canvas.update_plot(self.t, ol_step, cl_step, metrics)
        self.bode_mag_canvas.update_plot(self.omega, mag_ol, mag_cl, metrics)
        self.bode_phase_canvas.update_plot(self.omega, phase_ol, phase_cl)
        self.s_plane_canvas.update_plot(metrics)
        self.info_canvas.update_panel(self.K0, self.alpha, self.beta, self.input_amp)
        self.metrics_canvas.update_panel(metrics)

        # Update status
        self.status_label.setText(
            f"<b>Loop Gain:</b> {self.beta * self.K0:.1f}<br>"
            f"<b>Speedup:</b> {metrics['speedup']:.1f}x<br>"
            f"<b>CL BW:</b> {metrics['cl_bw']:.1f} rad/s"
        )
