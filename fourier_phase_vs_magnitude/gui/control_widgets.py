"""
GUI Control Widgets for Fourier Analysis
Contains parameter controls and image selection widgets
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                            QLabel, QSlider, QComboBox, QPushButton, QSpinBox,
                            QDoubleSpinBox, QCheckBox, QGridLayout, QRadioButton,
                            QButtonGroup)
from PyQt5.QtCore import Qt, pyqtSignal
import numpy as np


class FourierControls(QWidget):
    """
    Widget for controlling Fourier analysis parameters
    """

    parameter_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._mag_slider_default = 100  # corresponds to 10.0
        self._phase_slider_default = 0  # corresponds to 0.0
        self._mag_slider_value = self._mag_slider_default
        self._phase_slider_value = self._phase_slider_default
        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        """Setup the parameter control interface"""
        layout = QVBoxLayout(self)

        # Image Selection
        image_select_group = QGroupBox("Image Selection")
        self.selection_group = image_select_group
        image_layout = QGridLayout(image_select_group)

        # Image 1 mode
        self.img1_mode_label = QLabel("Image 1 Mode:")
        image_layout.addWidget(self.img1_mode_label, 0, 0)
        self.img1_mode_combo = QComboBox()
        self.img1_mode_combo.addItems(['Original', 'Uniform Magnitude', 'Uniform Phase'])
        image_layout.addWidget(self.img1_mode_combo, 0, 1)

        # Image 2 mode
        self.img2_mode_label = QLabel("Image 2 Mode:")
        image_layout.addWidget(self.img2_mode_label, 1, 0)
        self.img2_mode_combo = QComboBox()
        self.img2_mode_combo.addItems(['Original', 'Uniform Magnitude', 'Uniform Phase'])
        image_layout.addWidget(self.img2_mode_combo, 1, 1)

        layout.addWidget(image_select_group)

        # Uniform Value Controls
        uniform_group = QGroupBox("Uniform Value Controls")
        uniform_layout = QGridLayout(uniform_group)

        # Uniform Magnitude slider
        uniform_layout.addWidget(QLabel("Uniform Magnitude:"), 0, 0)
        self.mag_slider = QSlider(Qt.Horizontal)
        self.mag_slider.setRange(1, 1000)  # 0.1 to 100.0 (x10)
        self.mag_slider.setValue(self._mag_slider_default)  # 10.0
        self.mag_slider.setTickPosition(QSlider.TicksBelow)
        self.mag_slider.setTickInterval(100)
        uniform_layout.addWidget(self.mag_slider, 0, 1)

        self.mag_value_label = QLabel("10.0")
        uniform_layout.addWidget(self.mag_value_label, 0, 2)
        self._mag_slider_value = self.mag_slider.value()

        # Uniform Phase slider
        uniform_layout.addWidget(QLabel("Uniform Phase (rad):"), 1, 0)
        self.phase_slider = QSlider(Qt.Horizontal)
        self.phase_slider.setRange(-314, 314)  # -pi to pi (x100)
        self.phase_slider.setValue(self._phase_slider_default)
        self.phase_slider.setTickPosition(QSlider.TicksBelow)
        self.phase_slider.setTickInterval(157)  # pi/2
        uniform_layout.addWidget(self.phase_slider, 1, 1)

        self.phase_value_label = QLabel("0.00")
        uniform_layout.addWidget(self.phase_value_label, 1, 2)
        self._phase_slider_value = self.phase_slider.value()

        layout.addWidget(uniform_group)

    def setup_connections(self):
        """Setup signal connections"""
        # Connect all controls to parameter_changed signal
        self.img1_mode_combo.currentTextChanged.connect(self.on_mode_changed)
        self.img2_mode_combo.currentTextChanged.connect(self.on_mode_changed)
        self.mag_slider.valueChanged.connect(self.on_mag_slider_changed)
        self.phase_slider.valueChanged.connect(self.on_phase_slider_changed)
        self.update_slider_states()

    def on_mag_slider_changed(self, value):
        """Handle magnitude slider change"""
        if not self.mag_slider.isEnabled():
            return

        self._mag_slider_value = value
        self.mag_value_label.setText(f"{value / 10.0:.1f}")
        self.parameter_changed.emit()

    def on_phase_slider_changed(self, value):
        """Handle phase slider change"""
        if not self.phase_slider.isEnabled():
            return

        self._phase_slider_value = value
        self.phase_value_label.setText(f"{value / 100.0:.2f}")
        self.parameter_changed.emit()

    def get_parameters(self):
        """Get current parameter values"""
        # Convert mode names to internal codes
        mode_map = {
            'Original': 'original',
            'Uniform Magnitude': 'uniform_mag',
            'Uniform Phase': 'uniform_phase'
        }

        params = {
            'img1_mode': mode_map[self.img1_mode_combo.currentText()],
            'img2_mode': mode_map[self.img2_mode_combo.currentText()],
            'uniform_magnitude': self._mag_slider_value / 10.0,
            'uniform_phase': self._phase_slider_value / 100.0
        }

        return params

    def set_mode(self, mode):
        """Update labels to reflect current analysis mode"""
        if mode == 'audio':
            self.selection_group.setTitle("Audio Selection")
            self.img1_mode_label.setText("Audio 1 Mode:")
            self.img2_mode_label.setText("Audio 2 Mode:")
        else:
            self.selection_group.setTitle("Image Selection")
            self.img1_mode_label.setText("Image 1 Mode:")
            self.img2_mode_label.setText("Image 2 Mode:")

    def set_channel_mode(self, channel, mode_key):
        """Programmatically set mode for a channel (1 or 2)"""
        mode_indices = {
            'original': 0,
            'uniform_mag': 1,
            'uniform_phase': 2
        }
        if mode_key not in mode_indices:
            return
        combo = self.img1_mode_combo if channel == 1 else self.img2_mode_combo
        combo.setCurrentIndex(mode_indices[mode_key])

    def on_mode_changed(self, _value=None):
        """Handle mode changes and refresh slider availability"""
        sender = self.sender()
        selected_text = sender.currentText() if sender else None
        if selected_text == 'Uniform Magnitude':
            self.reset_phase_slider()
        elif selected_text == 'Uniform Phase':
            self.reset_mag_slider()
        elif selected_text == 'Original':
            self.reset_mag_slider()
            self.reset_phase_slider()

        self.update_slider_states()
        self.parameter_changed.emit()

    def update_slider_states(self):
        """Enable or disable sliders based on selected modes"""
        active_modes = {
            self.img1_mode_combo.currentText(),
            self.img2_mode_combo.currentText()
        }

        enable_mag = 'Uniform Magnitude' in active_modes
        enable_phase = 'Uniform Phase' in active_modes

        mag_was_enabled = self.mag_slider.isEnabled()
        phase_was_enabled = self.phase_slider.isEnabled()

        self.mag_slider.setEnabled(enable_mag)
        self.mag_value_label.setEnabled(enable_mag)
        self.phase_slider.setEnabled(enable_phase)
        self.phase_value_label.setEnabled(enable_phase)

        if enable_mag:
            if not mag_was_enabled or self.mag_slider.value() != self._mag_slider_value:
                self._apply_mag_slider_value(self._mag_slider_value)
            self.mag_value_label.setText(f"{self._mag_slider_value / 10.0:.1f}")
            self.mag_slider.setToolTip("Adjust uniform magnitude value")
        else:
            self.mag_value_label.setText("—")
            self.mag_slider.setToolTip("Enable a Uniform Magnitude mode to adjust this slider")

        if enable_phase:
            if not phase_was_enabled or self.phase_slider.value() != self._phase_slider_value:
                self._apply_phase_slider_value(self._phase_slider_value)
            self.phase_value_label.setText(f"{self._phase_slider_value / 100.0:.2f}")
            self.phase_slider.setToolTip("Adjust uniform phase value")
        else:
            self.phase_value_label.setText("—")
            self.phase_slider.setToolTip("Enable a Uniform Phase mode to adjust this slider")

    def reset_mag_slider(self):
        """Reset magnitude slider to default value without emitting signals"""
        self._apply_mag_slider_value(self._mag_slider_default, update_label=True)

    def reset_phase_slider(self):
        """Reset phase slider to default value without emitting signals"""
        self._apply_phase_slider_value(self._phase_slider_default, update_label=True)
        self.update_slider_states()

    def _apply_mag_slider_value(self, value, update_label=False):
        """Apply a magnitude slider value while keeping internal state consistent"""
        self._mag_slider_value = value
        if self.mag_slider.value() != value:
            self.mag_slider.blockSignals(True)
            self.mag_slider.setValue(value)
            self.mag_slider.blockSignals(False)
        if update_label or self.mag_slider.isEnabled():
            self.mag_value_label.setText(f"{value / 10.0:.1f}")

    def _apply_phase_slider_value(self, value, update_label=False):
        """Apply a phase slider value while keeping internal state consistent"""
        self._phase_slider_value = value
        if self.phase_slider.value() != value:
            self.phase_slider.blockSignals(True)
            self.phase_slider.setValue(value)
            self.phase_slider.blockSignals(False)
        if update_label or self.phase_slider.isEnabled():
            self.phase_value_label.setText(f"{value / 100.0:.2f}")

    def reset_all(self, emit_signal=False):
        """Reset both sliders to defaults and optionally emit change"""
        self.reset_mag_slider()
        self.reset_phase_slider()
        self.update_slider_states()
        if emit_signal:
            self.parameter_changed.emit()


class ImageControls(QWidget):
    """
    Widget for controlling image selection and loading
    """

    def __init__(self):
        super().__init__()
        self._base_patterns = ["Building", "Face", "Geometric", "Texture"]
        self._custom_item_index = {1: None, 2: None}
        self.setup_ui()

    def setup_ui(self):
        """Setup the image control interface"""
        layout = QVBoxLayout(self)

        # Image Source for Image 1
        source1_group = QGroupBox("Image 1 Source")
        source1_layout = QVBoxLayout(source1_group)

        # Test pattern selection
        source1_layout.addWidget(QLabel("Test Pattern:"))
        self.pattern1_combo = QComboBox()
        self.pattern1_combo.addItems(self._base_patterns)
        source1_layout.addWidget(self.pattern1_combo)

        # Load custom image
        self.load_image1_button = QPushButton("Load Custom Image 1...")
        source1_layout.addWidget(self.load_image1_button)

        layout.addWidget(source1_group)

        # Image Source for Image 2
        source2_group = QGroupBox("Image 2 Source")
        source2_layout = QVBoxLayout(source2_group)

        # Test pattern selection
        source2_layout.addWidget(QLabel("Test Pattern:"))
        self.pattern2_combo = QComboBox()
        self.pattern2_combo.addItems(self._base_patterns)
        self.pattern2_combo.setCurrentIndex(1)  # Default to Face
        source2_layout.addWidget(self.pattern2_combo)

        # Load custom image
        self.load_image2_button = QPushButton("Load Custom Image 2...")
        source2_layout.addWidget(self.load_image2_button)

        layout.addWidget(source2_group)

        # Image Properties
        props_group = QGroupBox("Image Properties")
        props_layout = QGridLayout(props_group)

        props_layout.addWidget(QLabel("Image 1 Size:"), 0, 0)
        self.size1_label = QLabel("256 × 256")
        props_layout.addWidget(self.size1_label, 0, 1)

        props_layout.addWidget(QLabel("Image 2 Size:"), 1, 0)
        self.size2_label = QLabel("256 × 256")
        props_layout.addWidget(self.size2_label, 1, 1)

        props_layout.addWidget(QLabel("Type:"), 2, 0)
        self.type_label = QLabel("Grayscale")
        props_layout.addWidget(self.type_label, 2, 1)

        props_layout.addWidget(QLabel("Range:"), 3, 0)
        self.range_label = QLabel("0.0 - 1.0")
        props_layout.addWidget(self.range_label, 3, 1)

        layout.addWidget(props_group)
        props_group.setVisible(False)

    def update_image_info(self, image_num, image):
        """Update image information display"""
        # Properties hidden; only ensure labels exist
        if image is not None:
            if image.ndim == 2:
                h, w = image.shape
            else:
                h, w = image.shape[1], image.shape[0]
            size_str = f"{w} × {h}"
        else:
            size_str = "No image"

        if image_num == 1:
            self.size1_label.setText(size_str)
        else:
            self.size2_label.setText(size_str)

    def set_custom_image_label(self, image_num, label):
        """Update combo box to reflect custom image selection"""
        combo = self.pattern1_combo if image_num == 1 else self.pattern2_combo
        display_text = f"Custom: {label}"
        custom_index = self._custom_item_index[image_num]

        combo.blockSignals(True)
        if custom_index is None:
            combo.addItem(display_text)
            custom_index = combo.count() - 1
            self._custom_item_index[image_num] = custom_index
        else:
            combo.setItemText(custom_index, display_text)
        combo.setCurrentIndex(custom_index)
        combo.blockSignals(False)

    def set_pattern_selection(self, image_num, pattern_name):
        """Ensure combo points to a built-in pattern"""
        combo = self.pattern1_combo if image_num == 1 else self.pattern2_combo
        index = combo.findText(pattern_name)
        if index >= 0:
            combo.blockSignals(True)
            combo.setCurrentIndex(index)
            combo.blockSignals(False)


class AudioControls(QWidget):
    """
    Widget for controlling audio selection and loading
    """

    def __init__(self):
        super().__init__()
        self._base_patterns = ["Sine", "Square", "Sawtooth", "Beat"]
        self._custom_item_index = {1: None, 2: None}
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        source1_group = QGroupBox("Audio 1 Source")
        source1_layout = QVBoxLayout(source1_group)

        source1_layout.addWidget(QLabel("Test Signal:"))
        self.pattern1_combo = QComboBox()
        self.pattern1_combo.addItems(self._base_patterns)
        source1_layout.addWidget(self.pattern1_combo)

        self.load_audio1_button = QPushButton("Load Custom Audio 1...")
        source1_layout.addWidget(self.load_audio1_button)

        layout.addWidget(source1_group)

        source2_group = QGroupBox("Audio 2 Source")
        source2_layout = QVBoxLayout(source2_group)

        source2_layout.addWidget(QLabel("Test Signal:"))
        self.pattern2_combo = QComboBox()
        self.pattern2_combo.addItems(self._base_patterns)
        self.pattern2_combo.setCurrentIndex(1)  # Default to Square
        source2_layout.addWidget(self.pattern2_combo)

        self.load_audio2_button = QPushButton("Load Custom Audio 2...")
        source2_layout.addWidget(self.load_audio2_button)

        layout.addWidget(source2_group)

        info_group = QGroupBox("Audio Properties")
        info_layout = QGridLayout(info_group)

        info_layout.addWidget(QLabel("Audio 1 Duration:"), 0, 0)
        self.duration1_label = QLabel("0.00 s")
        info_layout.addWidget(self.duration1_label, 0, 1)

        info_layout.addWidget(QLabel("Audio 2 Duration:"), 1, 0)
        self.duration2_label = QLabel("0.00 s")
        info_layout.addWidget(self.duration2_label, 1, 1)

        info_layout.addWidget(QLabel("Sample Rate:"), 2, 0)
        self.sample_rate_label = QLabel("44100 Hz")
        info_layout.addWidget(self.sample_rate_label, 2, 1)

        info_layout.addWidget(QLabel("Amplitude Range:"), 3, 0)
        self.range_label = QLabel("-1.00 to 1.00")
        info_layout.addWidget(self.range_label, 3, 1)

        layout.addWidget(info_group)
        info_group.setVisible(False)

    def update_audio_info(self, audio_num, signal, sample_rate):
        """Update audio metadata display"""
        duration = len(signal) / sample_rate if sample_rate else 0.0
        range_min = signal.min() if len(signal) > 0 else 0.0
        range_max = signal.max() if len(signal) > 0 else 0.0

        if audio_num == 1:
            self.duration1_label.setText(f"{duration:.2f} s")
        else:
            self.duration2_label.setText(f"{duration:.2f} s")

        self.sample_rate_label.setText(f"{sample_rate} Hz")
        self.range_label.setText(f"{range_min:.2f} to {range_max:.2f}")

    def set_custom_audio_label(self, audio_num, label):
        """Update combo box with custom audio description"""
        combo = self.pattern1_combo if audio_num == 1 else self.pattern2_combo
        display_text = f"Custom: {label}"
        custom_index = self._custom_item_index[audio_num]

        combo.blockSignals(True)
        if custom_index is None:
            combo.addItem(display_text)
            custom_index = combo.count() - 1
            self._custom_item_index[audio_num] = custom_index
        else:
            combo.setItemText(custom_index, display_text)
        combo.setCurrentIndex(custom_index)
        combo.blockSignals(False)

    def set_pattern_selection(self, audio_num, pattern_name):
        combo = self.pattern1_combo if audio_num == 1 else self.pattern2_combo
        index = combo.findText(pattern_name)
        if index >= 0:
            combo.blockSignals(True)
            combo.setCurrentIndex(index)
            combo.blockSignals(False)
    def set_custom_image_label(self, image_num, label):
        """Update combo box to reflect custom image selection"""
        combo = self.pattern1_combo if image_num == 1 else self.pattern2_combo
        display_text = f"Custom: {label}"
        custom_index = self._custom_item_index[image_num]

        combo.blockSignals(True)
        if custom_index is None:
            combo.addItem(display_text)
            custom_index = combo.count() - 1
            self._custom_item_index[image_num] = custom_index
        else:
            combo.setItemText(custom_index, display_text)

        combo.setCurrentIndex(custom_index)
        combo.blockSignals(False)

    def set_pattern_selection(self, image_num, pattern_name):
        """Ensure combo points to a built-in pattern"""
        combo = self.pattern1_combo if image_num == 1 else self.pattern2_combo
        index = combo.findText(pattern_name)
        if index >= 0:
            combo.blockSignals(True)
            combo.setCurrentIndex(index)
            combo.blockSignals(False)
