"""
Control Panel Module
PyQt5 widget containing all control elements (sliders, radio buttons, etc.)
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QSlider, QRadioButton, QPushButton, QGroupBox,
                             QButtonGroup, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


class ControlPanel(QWidget):
    """Control panel widget with all interactive controls"""

    # Signals to communicate with main window
    parameters_changed = pyqtSignal(float, float, float, float)  # alpha, beta, gamma, p
    model_changed = pyqtSignal(str)  # model_type
    reset_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # Default parameters
        self.alpha = 10.0
        self.beta = 0.5
        self.gamma = 1.0
        self.p = 10.0
        self.model_type = 'First-Order'

        # Setup UI
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)

        # Title
        title = QLabel("Control Panel")
        title.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        # Add separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        # Model selection
        layout.addWidget(self.create_model_selection())

        # Add separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        # Parameter sliders
        layout.addWidget(QLabel("<b>Parameters:</b>"))
        layout.addWidget(self.create_alpha_slider())
        layout.addWidget(self.create_beta_slider())
        layout.addWidget(self.create_gamma_slider())
        self.p_widget = self.create_p_slider()
        layout.addWidget(self.p_widget)
        self.p_widget.setVisible(False)  # Hidden for first-order by default

        # Add separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        # Current parameter values display
        layout.addWidget(self.create_param_display())

        # Add stretch to push reset button to bottom
        layout.addStretch()

        # Reset button
        reset_btn = QPushButton("Reset Parameters")
        reset_btn.setMinimumHeight(40)
        reset_btn.clicked.connect(self.reset_parameters)
        layout.addWidget(reset_btn)

        self.setLayout(layout)
        self.setMinimumWidth(280)
        self.setMaximumWidth(350)

    def create_model_selection(self):
        """Create model selection radio buttons"""
        group_box = QGroupBox("Model Selection")
        layout = QVBoxLayout()

        self.radio_first = QRadioButton("First-Order")
        self.radio_second = QRadioButton("Second-Order")
        self.radio_first.setChecked(True)

        self.button_group = QButtonGroup()
        self.button_group.addButton(self.radio_first)
        self.button_group.addButton(self.radio_second)

        self.radio_first.toggled.connect(self.on_model_changed)

        layout.addWidget(self.radio_first)
        layout.addWidget(self.radio_second)
        group_box.setLayout(layout)

        return group_box

    def create_alpha_slider(self):
        """Create alpha (amplifier gain) slider"""
        return self._create_slider_group(
            "α (Amplifier gain)", 1, 500, 100,
            self.alpha, self.on_alpha_changed
        )

    def create_beta_slider(self):
        """Create beta (feedback gain) slider"""
        return self._create_slider_group(
            "β (Feedback gain)", 1, 100, 50,
            self.beta, self.on_beta_changed
        )

    def create_gamma_slider(self):
        """Create gamma (motor constant) slider"""
        return self._create_slider_group(
            "γ (Motor constant)", 1, 50, 10,
            self.gamma, self.on_gamma_changed
        )

    def create_p_slider(self):
        """Create p (lag pole) slider"""
        return self._create_slider_group(
            "p (Lag pole)", 5, 300, 100,
            self.p, self.on_p_changed
        )

    def _create_slider_group(self, label_text, min_val, max_val, scale, default_val, callback):
        """Helper to create a labeled slider with value display"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)

        # Label and value in one line
        header_layout = QHBoxLayout()
        label = QLabel(label_text)
        value_label = QLabel(f"{default_val:.2f}")
        value_label.setAlignment(Qt.AlignRight)
        header_layout.addWidget(label)
        header_layout.addWidget(value_label)
        layout.addLayout(header_layout)

        # Slider
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(min_val)
        slider.setMaximum(max_val)
        slider.setValue(int(default_val * scale))
        slider.setTickPosition(QSlider.TicksBelow)
        slider.setTickInterval((max_val - min_val) // 10)

        # Store references
        slider.value_label = value_label
        slider.scale = scale

        slider.valueChanged.connect(lambda: callback(slider, value_label, scale))
        layout.addWidget(slider)

        widget.setLayout(layout)
        widget.slider = slider  # Store reference for reset
        widget.value_label = value_label
        return widget

    def on_alpha_changed(self, slider, label, scale):
        """Handle alpha slider change"""
        self.alpha = slider.value() / scale
        label.setText(f"{self.alpha:.2f}")
        self.update_param_display()
        self.parameters_changed.emit(self.alpha, self.beta, self.gamma, self.p)

    def on_beta_changed(self, slider, label, scale):
        """Handle beta slider change"""
        self.beta = slider.value() / scale
        label.setText(f"{self.beta:.2f}")
        self.update_param_display()
        self.parameters_changed.emit(self.alpha, self.beta, self.gamma, self.p)

    def on_gamma_changed(self, slider, label, scale):
        """Handle gamma slider change"""
        self.gamma = slider.value() / scale
        label.setText(f"{self.gamma:.2f}")
        self.update_param_display()
        self.parameters_changed.emit(self.alpha, self.beta, self.gamma, self.p)

    def on_p_changed(self, slider, label, scale):
        """Handle p slider change"""
        self.p = slider.value() / scale
        label.setText(f"{self.p:.2f}")
        self.update_param_display()
        self.parameters_changed.emit(self.alpha, self.beta, self.gamma, self.p)

    def on_model_changed(self, checked):
        """Handle model type change"""
        if checked:  # First-Order selected
            self.model_type = 'First-Order'
            self.p_widget.setVisible(False)
        else:  # Second-Order selected
            self.model_type = 'Second-Order'
            self.p_widget.setVisible(True)

        self.update_param_display()
        self.model_changed.emit(self.model_type)

    def create_param_display(self):
        """Create parameter value display"""
        self.param_display = QLabel()
        self.param_display.setAlignment(Qt.AlignCenter)
        self.param_display.setStyleSheet("""
            QLabel {
                background-color: lightblue;
                border: 2px solid blue;
                border-radius: 5px;
                padding: 10px;
                font-size: 11pt;
            }
        """)
        self.update_param_display()
        return self.param_display

    def update_param_display(self):
        """Update parameter display text"""
        text = f"<b>Current Parameters:</b><br><br>"
        text += f"α = {self.alpha:.2f}<br>"
        text += f"β = {self.beta:.2f}<br>"
        text += f"γ = {self.gamma:.2f}<br>"
        if self.model_type == 'Second-Order':
            text += f"p = {self.p:.2f}<br>"
        self.param_display.setText(text)

    def reset_parameters(self):
        """Reset all parameters to default values"""
        # Reset values
        self.alpha = 10.0
        self.beta = 0.5
        self.gamma = 1.0
        self.p = 10.0

        # Reset sliders (find them in layout)
        for i in range(self.layout().count()):
            widget = self.layout().itemAt(i).widget()
            if hasattr(widget, 'slider'):
                slider = widget.slider
                value_label = widget.value_label
                scale = slider.scale

                # Determine default value based on position
                if 'Amplifier' in widget.layout().itemAt(0).layout().itemAt(0).widget().text():
                    slider.setValue(int(10.0 * scale))
                    value_label.setText("10.00")
                elif 'Feedback' in widget.layout().itemAt(0).layout().itemAt(0).widget().text():
                    slider.setValue(int(0.5 * scale))
                    value_label.setText("0.50")
                elif 'Motor' in widget.layout().itemAt(0).layout().itemAt(0).widget().text():
                    slider.setValue(int(1.0 * scale))
                    value_label.setText("1.00")
                elif 'Lag' in widget.layout().itemAt(0).layout().itemAt(0).widget().text():
                    slider.setValue(int(10.0 * scale))
                    value_label.setText("10.00")

        # Reset model selection
        self.radio_first.setChecked(True)
        self.model_type = 'First-Order'
        self.p_widget.setVisible(False)

        self.update_param_display()
        self.reset_requested.emit()

    def get_parameters(self):
        """Get current parameter values"""
        return {
            'alpha': self.alpha,
            'beta': self.beta,
            'gamma': self.gamma,
            'p': self.p,
            'model_type': self.model_type
        }
