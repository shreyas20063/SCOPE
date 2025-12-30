"""
GUI Module for Amplifier Topologies
Contains all UI components and plotting functionality
Converted to PyQt5
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QSlider, QRadioButton, QButtonGroup,
                              QFileDialog, QMessageBox, QFrame, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont

import config
from utils.helpers import GainCalculator


class AmplifierGUI(QWidget):
    """Manages the graphical user interface"""

    # Define signals for callbacks
    parameter_changed = pyqtSignal()
    load_audio_requested = pyqtSignal(str)
    play_audio_requested = pyqtSignal()
    reset_requested = pyqtSignal()

    def __init__(self, parent, audio_processor, audio_player, circuit_images):
        super().__init__(parent)
        self.audio_processor = audio_processor
        self.audio_player = audio_player
        self.circuit_images = circuit_images

        # System parameters
        self.K = config.K_DEFAULT
        self.F0 = config.F0_DEFAULT
        self.beta = config.BETA_DEFAULT
        self.VT = config.VT_DEFAULT

        self.current_mode = 'simple'
        self.output_plot_limit = config.INITIAL_OUTPUT_LIMIT

        # Callbacks (to be connected by main app)
        self.on_parameter_change = None
        self.on_load_audio = None
        self.on_play_audio = None
        self.on_reset = None

        self.setup_ui()
        
    def setup_ui(self):
        """Setup the complete user interface"""
        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Left panel
        left_frame = QFrame()
        left_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        left_frame.setMaximumWidth(400)
        left_frame.setMinimumWidth(400)
        left_layout = QVBoxLayout(left_frame)
        self._setup_left_panel(left_layout)

        # Right panel (plots)
        plot_frame = QFrame()
        plot_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        plot_layout = QVBoxLayout(plot_frame)
        self._setup_plots(plot_layout)

        main_layout.addWidget(left_frame)
        main_layout.addWidget(plot_frame, stretch=1)
    
    def _setup_left_panel(self, layout):
        """Setup the left control panel"""
        # Title
        title = QLabel("Amplifier Controls")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        layout.addSpacing(10)

        # Mode selection
        config_frame = QFrame()
        config_frame.setFrameStyle(QFrame.Box)
        config_layout = QVBoxLayout(config_frame)

        mode_label = QLabel("Amplifier Configuration")
        mode_label.setFont(QFont("Arial", 12, QFont.Bold))
        config_layout.addWidget(mode_label)

        self.mode_group = QButtonGroup(self)
        for text, value in config.AMPLIFIER_CONFIGS:
            radio = QRadioButton(text)
            radio.setProperty('mode_value', value)
            if value == 'simple':
                radio.setChecked(True)
            radio.toggled.connect(self._on_mode_change)
            self.mode_group.addButton(radio)
            config_layout.addWidget(radio)

        layout.addWidget(config_frame)
        layout.addSpacing(10)

        # Image display
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumHeight(175)
        self.image_label.setScaledContents(False)
        layout.addWidget(self.image_label)
        layout.addSpacing(10)

        # Parameter sliders
        self._create_slider(layout, "F₀ - Power Amp Gain", 'F0', config.F0_MIN, config.F0_MAX, config.F0_DEFAULT)
        self._create_slider(layout, "K - Forward Gain", 'K', config.K_MIN, config.K_MAX, config.K_DEFAULT)
        self._create_slider(layout, "β - Feedback Factor", 'beta', config.BETA_MIN, config.BETA_MAX, config.BETA_DEFAULT)

        # Audio controls
        layout.addStretch()
        self._setup_audio_controls(layout)
    
    def _setup_audio_controls(self, layout):
        """Setup audio control buttons"""
        audio_frame = QFrame()
        audio_frame.setFrameStyle(QFrame.Box)
        audio_layout = QVBoxLayout(audio_frame)

        self.file_label = QLabel("Input: Pure Sine Wave")
        self.file_label.setAlignment(Qt.AlignCenter)
        self.file_label.setWordWrap(True)
        audio_layout.addWidget(self.file_label)

        load_btn = QPushButton("Load Audio File...")
        load_btn.clicked.connect(self._handle_load_audio)
        audio_layout.addWidget(load_btn)

        self.play_button = QPushButton("▶ Play Output")
        self.play_button.clicked.connect(self._handle_play_audio)
        audio_layout.addWidget(self.play_button)

        stop_btn = QPushButton("■ Stop Audio")
        stop_btn.clicked.connect(self._handle_stop_audio)
        audio_layout.addWidget(stop_btn)

        reset_btn = QPushButton("⟲ Reset Parameters")
        reset_btn.clicked.connect(self._handle_reset)
        reset_btn.setStyleSheet("background-color: goldenrod; color: black; font-weight: bold;")
        audio_layout.addWidget(reset_btn)

        layout.addWidget(audio_frame)
    
    def _create_slider(self, layout, text, param_name, min_val, max_val, default_val):
        """Create a parameter slider with label"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Box)
        slider_layout = QVBoxLayout(frame)
        slider_layout.setContentsMargins(5, 5, 5, 5)

        label = QLabel(f"{text}: {default_val:.2f}")
        label.setFont(QFont("Arial", 10, QFont.Bold))
        label.setAlignment(Qt.AlignCenter)
        slider_layout.addWidget(label)

        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(int(min_val * 100))
        slider.setMaximum(int(max_val * 100))
        slider.setValue(int(default_val * 100))
        slider.setProperty('param_name', param_name)
        slider.setProperty('label', label)
        slider.setProperty('text', text)
        slider.valueChanged.connect(self._slider_update)

        # Store slider reference
        setattr(self, f'{param_name}_slider', slider)
        setattr(self, f'{param_name}_label', label)

        slider_layout.addWidget(slider)
        layout.addWidget(frame)

    def _slider_update(self):
        """Handle slider updates"""
        slider = self.sender()
        param_name = slider.property('param_name')
        label = slider.property('label')
        text = slider.property('text')
        value = slider.value() / 100.0

        # Update parameter
        setattr(self, param_name, value)

        # Update label
        label.setText(f"{text}: {value:.2f}")

        # Trigger callback
        if self.on_parameter_change:
            self.on_parameter_change()

    def _on_mode_change(self):
        """Handle mode change"""
        checked_button = self.mode_group.checkedButton()
        if checked_button:
            self.current_mode = checked_button.property('mode_value')
            if self.on_parameter_change:
                self.on_parameter_change()

    def _handle_load_audio(self):
        """Handle audio file loading"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Audio File",
            "",
            "Audio Files (*.wav *.mp3)"
        )
        if file_path and self.on_load_audio:
            self.on_load_audio(file_path)

    def _handle_play_audio(self):
        """Handle play audio button"""
        if self.on_play_audio:
            self.on_play_audio()

    def _handle_stop_audio(self):
        """Handle stop audio button"""
        self.audio_player.stop()

    def _handle_reset(self):
        """Handle reset button"""
        if self.on_reset:
            self.on_reset()
    
    def _setup_plots(self, layout):
        """Setup matplotlib plots"""
        plt.style.use(config.PLOT_STYLE)

        self.fig = Figure(figsize=(10, 8), dpi=100)
        gs = self.fig.add_gridspec(2, 2, hspace=0.45, wspace=0.3)

        self.ax_input = self.fig.add_subplot(gs[0, 0])
        self.ax_output = self.fig.add_subplot(gs[0, 1])
        self.ax_gain_curve = self.fig.add_subplot(gs[1, 0])
        self.ax_xy_plot = self.fig.add_subplot(gs[1, 1])

        self.fig.tight_layout(pad=2.0)

        self.canvas = FigureCanvasQTAgg(self.fig)
        layout.addWidget(self.canvas)

    def update_circuit_image(self):
        """Update circuit diagram based on current mode"""
        pixmap = self.circuit_images.get(self.current_mode)

        if pixmap:
            # Scale pixmap to fit while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(
                config.IMAGE_BOUNDING_BOX[0],
                config.IMAGE_BOUNDING_BOX[1],
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
        else:
            self.image_label.setText(f"Image for '{self.current_mode}' not found.")
    
    def update_plots(self):
        """Update all visualization plots"""
        # Clear all axes
        for ax in self.fig.axes:
            ax.clear()

        plot_data = self.audio_processor.get_plot_data()
        if plot_data is None:
            return

        time = plot_data['time']
        input_slice = plot_data['input_slice']
        output_slice = plot_data['output_slice']

        K_val = self.K
        F0_val = self.F0
        beta_val = self.beta

        # Input plot
        self._plot_input(time, input_slice)

        # Output plot
        self._plot_output(time, output_slice)

        # Gain curve
        self._plot_gain_curve(K_val, F0_val, beta_val)

        # XY plot (linearity)
        self._plot_xy(input_slice, output_slice)

        self.canvas.draw_idle()
    
    def _plot_input(self, time, input_slice):
        """Plot input signal"""
        self.ax_input.plot(time, input_slice, config.COLOR_INPUT, lw=2, label='Input')
        self.ax_input.set_title('Input Signal (Time Domain)')
        self.ax_input.set_xlabel('Time (s)')
        self.ax_input.set_ylabel('Amplitude')
        self.ax_input.legend(fontsize='small')
        self.ax_input.grid(True, linestyle=':', alpha=0.6)
        self.ax_input.set_ylim(config.INPUT_YLIM)
    
    def _plot_output(self, time, output_slice):
        """Plot output signal with dynamic scaling"""
        self.ax_output.plot(time, output_slice, config.COLOR_OUTPUT, lw=2, label='Output')
        self.ax_output.set_title('Output Signal (Time Domain)')
        self.ax_output.set_xlabel('Time (s)')
        self.ax_output.set_ylabel('Amplitude')
        self.ax_output.legend(fontsize='small')
        self.ax_output.grid(True, linestyle=':', alpha=0.6)
        
        if len(output_slice) > 0:
            max_output_amp = np.max(np.abs(output_slice))
            
            # Threshold-based scaling for "amplifying vibe"
            if max_output_amp > self.output_plot_limit * 0.95:
                self.output_plot_limit = max(max_output_amp * 1.2, 0.1)
            elif max_output_amp < self.output_plot_limit * 0.4 and self.output_plot_limit > 0.15:
                self.output_plot_limit = max(max_output_amp * 1.5, 0.1)
            
            if max_output_amp > self.output_plot_limit:
                self.output_plot_limit = max_output_amp * 1.2
            
            self.ax_output.set_ylim(-self.output_plot_limit, self.output_plot_limit)
    
    def _plot_gain_curve(self, K_val, F0_val, beta_val):
        """Plot gain vs F0 curves"""
        F0_range = np.linspace(config.F0_MIN, config.F0_MAX, 100)
        gain_simple, gain_feedback, ideal_gain = GainCalculator.calculate_gains(
            K_val, beta_val, F0_range
        )
        
        self.ax_gain_curve.plot(
            F0_range, gain_simple, 
            config.COLOR_SIMPLE_GAIN, ls='--', lw=2, label='Simple Gain'
        )
        self.ax_gain_curve.plot(
            F0_range, gain_feedback, 
            config.COLOR_FEEDBACK_GAIN, lw=2.5, label='Feedback Gain'
        )
        self.ax_gain_curve.axhline(
            ideal_gain, 
            color=config.COLOR_IDEAL_GAIN, ls=':', lw=2, label=r'Ideal (1/$\beta$)'
        )
        self.ax_gain_curve.axvline(
            F0_val, 
            color=config.COLOR_CURRENT_F0, ls='-.', lw=1.5, label=r'Current $F_0$'
        )
        
        self.ax_gain_curve.set_title(r'Gain vs. $F_0$ Variation')
        self.ax_gain_curve.set_xlabel(r'$F_0$')
        self.ax_gain_curve.set_ylabel('Gain')
        self.ax_gain_curve.legend(fontsize='small')
        self.ax_gain_curve.grid(True, linestyle=':', alpha=0.6)
        self.ax_gain_curve.set_ylim(min(gain_feedback)*0.9, max(gain_simple)*1.1)
    
    def _plot_xy(self, input_slice, output_slice):
        """Plot output vs input (linearity check)"""
        self.ax_xy_plot.plot(input_slice, output_slice, color=config.COLOR_XY_PLOT, lw=2)
        self.ax_xy_plot.set_title('Output vs. Input (Linearity)')
        self.ax_xy_plot.set_xlabel('Input Amplitude')
        self.ax_xy_plot.set_ylabel('Output Amplitude')
        self.ax_xy_plot.grid(True, linestyle=':', alpha=0.6)
        self.ax_xy_plot.axline((0, 0), slope=1, color='gray', ls='--', lw=1, alpha=0.7)
        
        if len(input_slice) > 0 and len(output_slice) > 0:
            max_abs_val = max(np.max(np.abs(input_slice)), np.max(np.abs(output_slice)))
            plot_limit = max(max_abs_val * 1.1, 0.011)
            self.ax_xy_plot.set_xlim(-plot_limit, plot_limit)
            self.ax_xy_plot.set_ylim(-plot_limit, plot_limit)
            self.ax_xy_plot.set_aspect('equal', 'box')
    
    def update_file_label(self, text):
        """Update the file label text"""
        self.file_label.setText(text)

    def reset_output_limit(self):
        """Reset output plot limit to default"""
        self.output_plot_limit = config.INITIAL_OUTPUT_LIMIT

    def get_parameters(self):
        """Get current parameter values"""
        return {
            'K': self.K,
            'F0': self.F0,
            'beta': self.beta,
            'mode': self.current_mode,
            'VT': self.VT
        }

    def set_parameters(self, K, F0, beta, mode):
        """Set parameter values"""
        self.K = K
        self.F0 = F0
        self.beta = beta
        self.current_mode = mode

        # Update sliders
        self.K_slider.setValue(int(K * 100))
        self.F0_slider.setValue(int(F0 * 100))
        self.beta_slider.setValue(int(beta * 100))

        # Update labels
        self.K_label.setText(f"K - Forward Gain: {K:.2f}")
        self.F0_label.setText(f"F₀ - Power Amp Gain: {F0:.2f}")
        self.beta_label.setText(f"β - Feedback Factor: {beta:.2f}")

        # Update radio button
        for button in self.mode_group.buttons():
            if button.property('mode_value') == mode:
                button.setChecked(True)
                break