from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QSlider, QPushButton, QRadioButton, QButtonGroup,
                             QLabel, QGroupBox, QSizePolicy, QShortcut, QTabWidget,
                             QFrame)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QKeySequence
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np

from core.config import Config
from core.math_handler import SystemMath
from gui.plot_renderer import PlotRenderer
from utils.educational_content import EducationalContent
from utils.problem_generator import AssessmentTools


class MainWindow(QMainWindow):
    """Main PyQt5 window for CT-DT Poles Conversion application"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('CT & DT Poles Conversion')
        self.setGeometry(100, 100, 1200, 700)

        # Initialize system parameters
        self.tau = 1.0
        self.T = 0.5
        self.method = 'Forward Euler'
        self.learning_mode = 'explore'
        self.current_scenario = 0
        self.animation_running = False
        self.demo_timer = None

        # Setup UI
        self._setup_ui()
        self._setup_shortcuts()

        # Initial update
        self.update_all_visualizations()

    def _setup_ui(self):
        """Setup clean layout: controls on left, tabs on right"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # Left: Compact control panel
        control_panel = self._create_control_panel()
        main_layout.addWidget(control_panel, stretch=0)

        # Right: Tabbed plot area
        plot_area = self._create_plot_area()
        main_layout.addWidget(plot_area, stretch=1)

        self.statusBar().showMessage('Ready')

    def _create_control_panel(self):
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
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Title
        title = QLabel("Controls")
        title.setFont(QFont('Arial', 11, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title)

        # T/τ Slider
        layout.addWidget(self._create_slider_group())

        # Method Selection
        layout.addWidget(self._create_method_group())

        # Buttons
        layout.addWidget(self._create_button_group())

        # Status display
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: white;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 6px;
                font-size: 9pt;
            }
        """)
        layout.addWidget(self.status_label)

        layout.addStretch()
        return panel

    def _create_slider_group(self):
        """Create T/τ slider"""
        group = QGroupBox("T/τ Ratio")
        group.setStyleSheet(self._group_style())
        layout = QVBoxLayout()
        layout.setSpacing(4)

        self.slider_label = QLabel("0.50")
        self.slider_label.setAlignment(Qt.AlignCenter)
        self.slider_label.setFont(QFont('Arial', 16, QFont.Bold))
        self.slider_label.setStyleSheet("color: #2980b9;")
        layout.addWidget(self.slider_label)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(1)
        self.slider.setMaximum(300)
        self.slider.setValue(50)
        self.slider.valueChanged.connect(self._on_slider_changed)
        layout.addWidget(self.slider)

        minmax = QHBoxLayout()
        minmax.addWidget(QLabel("0.01"))
        minmax.addStretch()
        minmax.addWidget(QLabel("3.0"))
        layout.addLayout(minmax)

        group.setLayout(layout)
        return group

    def _create_method_group(self):
        """Create method selection"""
        group = QGroupBox("Method")
        group.setStyleSheet(self._group_style())
        layout = QVBoxLayout()
        layout.setSpacing(2)

        self.method_group = QButtonGroup()
        methods = ['Forward Euler', 'Backward Euler', 'Trapezoidal']

        for i, method in enumerate(methods):
            radio = QRadioButton(method)
            radio.setStyleSheet("font-size: 9pt;")
            if i == 0:
                radio.setChecked(True)
            radio.toggled.connect(lambda checked, m=method: self._on_method_changed(m, checked))
            self.method_group.addButton(radio, i)
            layout.addWidget(radio)

        group.setLayout(layout)
        return group

    def _create_button_group(self):
        """Create action buttons"""
        group = QGroupBox("Actions")
        group.setStyleSheet(self._group_style())
        layout = QVBoxLayout()
        layout.setSpacing(4)

        # Reset
        self.btn_reset = QPushButton('Reset')
        self.btn_reset.setStyleSheet(self._btn_style("#27ae60"))
        self.btn_reset.clicked.connect(self._on_reset)
        layout.addWidget(self.btn_reset)

        # Demo
        self.btn_demo = QPushButton('Run Demo')
        self.btn_demo.setStyleSheet(self._btn_style("#3498db"))
        self.btn_demo.clicked.connect(self._on_demo)
        layout.addWidget(self.btn_demo)

        # Guided
        self.btn_guided = QPushButton('Guided Mode')
        self.btn_guided.setStyleSheet(self._btn_style("#f39c12"))
        self.btn_guided.clicked.connect(self._on_guided_mode)
        layout.addWidget(self.btn_guided)

        # Next Scenario (hidden)
        self.btn_next_scenario = QPushButton('Next')
        self.btn_next_scenario.setStyleSheet(self._btn_style("#16a085"))
        self.btn_next_scenario.clicked.connect(self._on_next_scenario)
        self.btn_next_scenario.setVisible(False)
        layout.addWidget(self.btn_next_scenario)

        group.setLayout(layout)
        return group

    def _group_style(self):
        return """
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
        """

    def _btn_style(self, color):
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                font-weight: bold;
                padding: 6px;
                border-radius: 4px;
                font-size: 9pt;
            }}
            QPushButton:hover {{
                opacity: 0.9;
            }}
        """

    def _create_plot_area(self):
        """Create tabbed plot area"""
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background: white;
            }
            QTabBar::tab {
                background: #ecf0f1;
                border: 1px solid #bdc3c7;
                padding: 6px 12px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom-color: white;
            }
        """)

        # Tab 1: Main (S-plane, Z-plane, Step Response)
        self.tabs.addTab(self._create_main_tab(), "Main")

        # Tab 2: Stability
        self.tabs.addTab(self._create_stability_tab(), "Stability")

        # Tab 3: Theory
        self.tabs.addTab(self._create_theory_tab(), "Theory")

        return self.tabs

    def _create_main_tab(self):
        """Main analysis tab: S-plane, Z-plane, Step Response"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)

        plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')

        self.main_fig = Figure(figsize=(10, 6), facecolor='white')
        self.main_canvas = FigureCanvas(self.main_fig)
        self.main_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 2 rows: top row has S-plane and Z-plane, bottom row has step response
        gs = self.main_fig.add_gridspec(2, 2, height_ratios=[1, 1], hspace=0.35, wspace=0.3)

        self.axes = {
            's_plane': self.main_fig.add_subplot(gs[0, 0]),
            'z_plane': self.main_fig.add_subplot(gs[0, 1]),
            'step_response': self.main_fig.add_subplot(gs[1, :])
        }

        toolbar = NavigationToolbar(self.main_canvas, widget)
        layout.addWidget(toolbar)
        layout.addWidget(self.main_canvas)

        return widget

    def _create_stability_tab(self):
        """Stability analysis tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)

        self.stability_fig = Figure(figsize=(10, 5), facecolor='white')
        self.stability_canvas = FigureCanvas(self.stability_fig)
        self.stability_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        gs = self.stability_fig.add_gridspec(1, 2, wspace=0.3)
        self.stability_axes = {
            'stability_map': self.stability_fig.add_subplot(gs[0, 0]),
            'pole_trajectory': self.stability_fig.add_subplot(gs[0, 1])
        }

        toolbar = NavigationToolbar(self.stability_canvas, widget)
        layout.addWidget(toolbar)
        layout.addWidget(self.stability_canvas)

        return widget

    def _create_theory_tab(self):
        """Theory/learning panel tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)

        self.learning_fig = Figure(figsize=(10, 6), facecolor='white')
        self.learning_canvas = FigureCanvas(self.learning_fig)
        self.learning_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.learning_axes = {
            'learning_panel': self.learning_fig.add_subplot(111)
        }

        layout.addWidget(self.learning_canvas)

        return widget

    def _setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        QShortcut(QKeySequence("Ctrl+R"), self).activated.connect(self._on_reset)
        QShortcut(QKeySequence("Ctrl+D"), self).activated.connect(self._on_demo)
        QShortcut(QKeySequence("Ctrl+G"), self).activated.connect(self._on_guided_mode)
        QShortcut(QKeySequence(Qt.Key_Space), self).activated.connect(self._on_next_scenario)
        QShortcut(QKeySequence(Qt.Key_Right), self).activated.connect(self._on_next_scenario)
        QShortcut(QKeySequence(Qt.Key_Left), self).activated.connect(self._on_previous_scenario)

    def _on_slider_changed(self, value):
        """Handle slider change"""
        T_tau = 0.01 + (value - 1) * (3.0 - 0.01) / 299
        self.T = T_tau * self.tau
        self.slider_label.setText(f"{T_tau:.2f}")
        self.update_all_visualizations()

    def _on_method_changed(self, method, checked):
        """Handle method change"""
        if checked:
            self.method = method
            self.update_all_visualizations()

    def _on_reset(self):
        """Reset to defaults"""
        if self.demo_timer:
            self.demo_timer.stop()
        self.animation_running = False
        self.slider.setValue(50)
        self.method_group.button(0).setChecked(True)
        self.method = 'Forward Euler'
        self.learning_mode = 'explore'
        self.btn_next_scenario.setVisible(False)
        self.update_all_visualizations()
        self.statusBar().showMessage('Reset')

    def _on_demo(self):
        """Run demo"""
        if self.demo_timer and self.demo_timer.isActive():
            self.demo_timer.stop()
            self.animation_running = False
            self.btn_demo.setText('Run Demo')
            self.statusBar().showMessage('Demo stopped')
            return

        self.btn_demo.setText('Stop')
        self.animation_running = True
        self.demo_values = list(range(50, 220, 3)) + list(range(220, 50, -3))
        self.demo_index = 0

        self.demo_timer = QTimer(self)
        self.demo_timer.timeout.connect(self._run_demo_step)
        self.demo_timer.start(80)
        self.statusBar().showMessage('Running demo...')

    def _run_demo_step(self):
        """Demo step"""
        if self.demo_index < len(self.demo_values):
            self.slider.setValue(self.demo_values[self.demo_index])
            self.demo_index += 1
        else:
            self.demo_timer.stop()
            self.animation_running = False
            self.btn_demo.setText('Run Demo')
            self.statusBar().showMessage('Demo complete')

    def _on_guided_mode(self):
        """Start guided mode"""
        self.learning_mode = 'guided'
        self.current_scenario = 0
        self.btn_next_scenario.setVisible(True)
        self._load_scenario(Config.GUIDED_SCENARIOS[0])
        self.statusBar().showMessage(f'Scenario 1/{len(Config.GUIDED_SCENARIOS)}')

    def _on_next_scenario(self):
        """Next scenario"""
        if self.learning_mode != 'guided':
            return
        self.current_scenario = (self.current_scenario + 1) % len(Config.GUIDED_SCENARIOS)
        self._load_scenario(Config.GUIDED_SCENARIOS[self.current_scenario])
        self.statusBar().showMessage(f'Scenario {self.current_scenario + 1}/{len(Config.GUIDED_SCENARIOS)}')

    def _on_previous_scenario(self):
        """Previous scenario"""
        if self.learning_mode != 'guided':
            return
        self.current_scenario = (self.current_scenario - 1) % len(Config.GUIDED_SCENARIOS)
        self._load_scenario(Config.GUIDED_SCENARIOS[self.current_scenario])
        self.statusBar().showMessage(f'Scenario {self.current_scenario + 1}/{len(Config.GUIDED_SCENARIOS)}')

    def _load_scenario(self, scenario):
        """Load scenario"""
        T_tau = scenario['T_tau']
        slider_value = int(1 + (T_tau - 0.01) * 299 / (3.0 - 0.01))
        self.slider.setValue(slider_value)

        method_index = ['Forward Euler', 'Backward Euler', 'Trapezoidal'].index(scenario['method'])
        self.method_group.button(method_index).setChecked(True)
        self.method = scenario['method']
        self.statusBar().showMessage(scenario['message'])

    def update_all_visualizations(self):
        """Update all plots"""
        s_pole = SystemMath.get_ct_pole(self.tau)
        z_pole = SystemMath.get_dt_pole(s_pole, self.T, self.method)
        is_stable = abs(z_pole) < 1

        # Create renderer with all axes
        all_axes = {**self.axes, **self.stability_axes, **self.learning_axes}
        renderer = PlotRenderer(self.main_fig, all_axes, Config.COLORS)

        # Main tab
        renderer.plot_s_plane_enhanced(self.tau, self.T, self.method)
        renderer.plot_z_plane_enhanced(self.tau, self.T, self.method)
        renderer.plot_step_response_comparison(self.tau, self.T, self.method)

        # Stability tab
        renderer.ax_stability_map = self.stability_axes['stability_map']
        renderer.ax_pole_trajectory = self.stability_axes['pole_trajectory']
        renderer.plot_stability_landscape(self.tau, self.T, self.method)
        renderer.plot_pole_movement_visualization(self.tau, self.T, self.method)

        # Theory tab
        renderer.ax_learning_panel = self.learning_axes['learning_panel']
        renderer.create_learning_panel(self.tau, self.T, self.method)

        # Update status
        status_color = "#27ae60" if is_stable else "#e74c3c"
        status = "STABLE" if is_stable else "UNSTABLE"
        self.status_label.setText(
            f"<b style='color:{status_color}'>{status}</b><br>"
            f"T/τ: {self.T/self.tau:.2f}<br>"
            f"|z|: {abs(z_pole):.3f}"
        )

        # Refresh canvases
        self.main_canvas.draw()
        self.stability_canvas.draw()
        self.learning_canvas.draw()
