"""
Control panel components for the Convolution Simulator.

This module handles all user controls including sliders, buttons,
input fields, and parameter adjustments.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QSlider, QGroupBox,
                             QRadioButton, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt
import csv

class ControlPanel:
    """Manages the left control panel with all user controls."""

    def __init__(self, main_app):
        self.app = main_app
        self.panel = main_app.left_panel

        self.setup_controls()

    def setup_controls(self):
        """Create all control widgets."""
        # Create main layout for left panel
        main_layout = QVBoxLayout(self.panel)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.create_custom_input_frame(main_layout)
        self.create_parameters_frame(main_layout)
        self.create_buttons_frame(main_layout)
        self.create_visualization_frame(main_layout)
        self.create_export_frame(main_layout)

        main_layout.addStretch()

    def create_custom_input_frame(self, parent_layout):
        """Create custom signal input controls."""
        custom_frame = QGroupBox("Custom Input")
        custom_layout = QVBoxLayout(custom_frame)

        # X signal input
        x_label = QLabel("x(t) or x[n]:")
        custom_layout.addWidget(x_label)

        self.x_entry = QLineEdit(self.app.custom_x_str)
        self.x_entry.returnPressed.connect(self._on_expression_changed)
        custom_layout.addWidget(self.x_entry)

        # H signal input
        h_label = QLabel("h(t) or h[n]:")
        custom_layout.addWidget(h_label)

        self.h_entry = QLineEdit(self.app.custom_h_str)
        self.h_entry.returnPressed.connect(self._on_expression_changed)
        custom_layout.addWidget(self.h_entry)

        parent_layout.addWidget(custom_frame)

    def create_parameters_frame(self, parent_layout):
        """Create parameter control sliders."""
        params_frame = QGroupBox("Parameters")
        params_layout = QVBoxLayout(params_frame)

        # Time/Index slider
        self.time_slider = self._create_slider(
            params_layout, "Time/Index (t or n)", -5, 5, 0, self._on_time_slider_change
        )

        # Playback speed slider
        self.playback_speed_slider = self._create_slider(
            params_layout, "Playback Speed (x)", 0.1, 4, 1, self._on_playback_speed_change
        )

        # Sampling rate slider
        self.sampling_rate_slider = self._create_slider(
            params_layout, "Sampling Rate (Hz)", 50, 2000, 500
        )

        parent_layout.addWidget(params_frame)

    def create_buttons_frame(self, parent_layout):
        """Create control buttons."""
        buttons_frame = QGroupBox("Controls")
        buttons_layout = QVBoxLayout(buttons_frame)

        # Playback controls
        playback_layout = QHBoxLayout()

        self.play_pause_button = QPushButton("Play")
        self.play_pause_button.clicked.connect(self.app.toggle_animation)
        playback_layout.addWidget(self.play_pause_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_and_reset)
        playback_layout.addWidget(self.stop_button)

        self.step_forward_button = QPushButton("Step →")
        self.step_forward_button.clicked.connect(self.step_time_forward)
        playback_layout.addWidget(self.step_forward_button)

        reset_button = QPushButton("Reset")
        reset_button.clicked.connect(self.reset_simulation)
        playback_layout.addWidget(reset_button)

        buttons_layout.addLayout(playback_layout)

        # Compute button
        compute_button = QPushButton("Compute Convolution")
        compute_button.setStyleSheet("font-weight: bold; padding: 5px;")
        compute_button.clicked.connect(self.app.compute_convolution)
        buttons_layout.addWidget(compute_button)

        parent_layout.addWidget(buttons_frame)

    def create_visualization_frame(self, parent_layout):
        """Create visualization style controls."""
        vis_frame = QGroupBox("Visualization Style")
        vis_layout = QVBoxLayout(vis_frame)

        self.math_radio = QRadioButton("Mathematical")
        self.math_radio.setChecked(True)
        self.math_radio.toggled.connect(self._toggle_visualization_style)
        vis_layout.addWidget(self.math_radio)

        self.block_radio = QRadioButton("Block-Step")
        self.block_radio.toggled.connect(self._toggle_visualization_style)
        vis_layout.addWidget(self.block_radio)

        parent_layout.addWidget(vis_frame)

    def create_export_frame(self, parent_layout):
        """Create export controls."""
        export_frame = QGroupBox("Export")
        export_layout = QVBoxLayout(export_frame)

        save_snapshot_button = QPushButton("Save Snapshot (PNG)")
        save_snapshot_button.clicked.connect(self.save_snapshot)
        export_layout.addWidget(save_snapshot_button)

        export_data_button = QPushButton("Export Data (CSV)")
        export_data_button.clicked.connect(self.export_data)
        export_layout.addWidget(export_data_button)

        save_animation_button = QPushButton("Save Animation (GIF)")
        save_animation_button.clicked.connect(self.save_animation)
        export_layout.addWidget(save_animation_button)

        parent_layout.addWidget(export_frame)

    def _create_slider(self, parent_layout, label, from_, to, default, callback=None):
        """Helper to create labeled slider."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        label_widget = QLabel(label)
        layout.addWidget(label_widget)

        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(int(from_ * 100))
        slider.setMaximum(int(to * 100))
        slider.setValue(int(default * 100))

        if callback:
            slider.valueChanged.connect(lambda val: callback(val / 100.0))

        layout.addWidget(slider)

        parent_layout.addWidget(container)

        # Store slider reference with value access
        slider._value = default
        slider._min = from_
        slider._max = to

        return slider

    def _on_time_slider_change(self, val):
        """Handle time slider changes."""
        time_val = float(val)
        self.time_slider._value = time_val
        self.app.current_time_val = time_val
        if hasattr(self.app, 'plot_manager'):
            self.app.plot_manager.update_plots(time_val)

    def _on_playback_speed_change(self, val):
        """Handle playback speed changes during animation."""
        self.playback_speed_slider._value = val
        if self.app.anim is not None and self.app.is_playing:
            self._restart_animation_with_new_speed()

    def _restart_animation_with_new_speed(self):
        """Restart animation with updated speed."""
        current_time = self.app.current_time_val
        self.app.stop_animation()

        # Restart from current position
        start_val, end_val = self.get_time_range()
        speed_multiplier = self.get_playback_speed()

        frames = self.app.animation_utils.create_frame_sequence(
            current_time, end_val, self.app.is_continuous
        )

        if len(frames) > 0:
            interval = self.app.animation_utils.calculate_animation_interval(speed_multiplier)
            import matplotlib.animation as animation
            self.app.anim = animation.FuncAnimation(
                self.app.fig, self.app.animate_step, frames=frames,
                interval=interval, repeat=False
            )
            self.app.is_playing = True
            self.app.canvas.draw()

    def _on_expression_changed(self):
        """Handle expression input changes."""
        self.app.custom_x_str = self.x_entry.text()
        self.app.custom_h_str = self.h_entry.text()
        self.app.compute_convolution()

    def _toggle_visualization_style(self):
        """Toggle between mathematical and block-step visualization."""
        if self.block_radio.isChecked():
            self.app.visualization_style = "Block-Step"
            self.app.right_panel.show()
        else:
            self.app.visualization_style = "Mathematical"
            self.app.right_panel.hide()

        if hasattr(self.app, 'plot_manager'):
            self.app.plot_manager.update_plots()

    # Public interface methods
    def update_time_slider_range(self, min_val, max_val):
        """Update the time slider range."""
        self.time_slider.setMinimum(int(min_val * 100))
        self.time_slider.setMaximum(int(max_val * 100))
        self.time_slider.setValue(int(min_val * 100))
        self.time_slider._min = min_val
        self.time_slider._max = max_val
        self.time_slider._value = min_val

    def get_time_range(self):
        """Get current time slider range."""
        return (self.time_slider._min, self.time_slider._max)

    def get_time_value(self):
        """Get current time slider value."""
        return self.time_slider._value

    def set_time_value(self, value):
        """Set time slider value."""
        self.time_slider._value = value
        self.time_slider.setValue(int(value * 100))

    def get_playback_speed(self):
        """Get current playback speed."""
        return self.playback_speed_slider._value

    def get_sampling_rate(self):
        """Get current sampling rate."""
        return self.sampling_rate_slider._value

    def step_time_forward(self):
        """Step time forward."""
        current_val = self.get_time_value()
        if self.app.is_continuous:
            start_val, end_val = self.get_time_range()
            step = (end_val - start_val) / 100
        else:
            step = 1

        new_val = min(current_val + step, self.get_time_range()[1])
        self.set_time_value(new_val)
        if hasattr(self.app, 'plot_manager'):
            self.app.plot_manager.update_plots(new_val)

    def step_time_backward(self):
        """Step time backward."""
        current_val = self.get_time_value()
        if self.app.is_continuous:
            start_val, end_val = self.get_time_range()
            step = (end_val - start_val) / 100
        else:
            step = 1

        new_val = max(current_val - step, self.get_time_range()[0])
        self.set_time_value(new_val)
        if hasattr(self.app, 'plot_manager'):
            self.app.plot_manager.update_plots(new_val)

    def stop_and_reset(self):
        """Stop animation only (keeps current position)."""
        self.app.stop_animation()
        self.play_pause_button.setText("Play")

    def reset_simulation(self):
        """Reset simulation to start."""
        start_val = self.get_time_range()[0]
        self.set_time_value(start_val)
        if hasattr(self.app, 'plot_manager'):
            self.app.plot_manager.update_plots(start_val)

    def enable_custom_inputs(self):
        """Enable custom input fields."""
        self.x_entry.setEnabled(True)
        self.h_entry.setEnabled(True)

    def disable_custom_inputs(self):
        """Disable custom input fields."""
        self.x_entry.setEnabled(False)
        self.h_entry.setEnabled(False)

    def update_play_button_text(self, is_playing):
        """Update play button text based on state."""
        text = "Pause" if is_playing else "Play"
        self.play_pause_button.setText(text)

    def update_input_fields(self):
        """Update input fields with current expressions."""
        self.x_entry.setText(self.app.custom_x_str)
        self.h_entry.setText(self.app.custom_h_str)

    # Export methods
    def save_snapshot(self):
        """Save current plot as PNG image."""
        filepath, _ = QFileDialog.getSaveFileName(
            self.app,
            "Save Snapshot",
            "",
            "PNG files (*.png);;All files (*.*)"
        )
        if filepath:
            try:
                self.app.fig.savefig(filepath, dpi=300, bbox_inches='tight')
                QMessageBox.information(self.app, "Success",
                                      f"Snapshot saved to {filepath}")
            except Exception as e:
                QMessageBox.critical(self.app, "Error",
                                   f"Failed to save snapshot: {e}")

    def export_data(self):
        """Export convolution data as CSV."""
        filepath, _ = QFileDialog.getSaveFileName(
            self.app,
            "Export Data",
            "",
            "CSV files (*.csv);;All files (*.*)"
        )
        if filepath:
            try:
                with open(filepath, 'w', newline='') as f:
                    writer = csv.writer(f)

                    if self.app.is_continuous and len(self.app.t_y) > 0:
                        writer.writerow(['t', 'y(t)'])
                        for i in range(len(self.app.t_y)):
                            writer.writerow([self.app.t_y[i], self.app.y_result[i]])
                    elif not self.app.is_continuous and len(self.app.n_y) > 0:
                        writer.writerow(['n', 'y[n]'])
                        for i in range(len(self.app.n_y)):
                            writer.writerow([self.app.n_y[i], self.app.y_result[i]])
                    else:
                        writer.writerow(['No data to export'])

                QMessageBox.information(self.app, "Success",
                                      f"Data exported to {filepath}")
            except Exception as e:
                QMessageBox.critical(self.app, "Error",
                                   f"Failed to export data: {e}")

    def save_animation(self):
        """Save animation as GIF."""
        filepath, _ = QFileDialog.getSaveFileName(
            self.app,
            "Save Animation",
            "",
            "GIF files (*.gif);;All files (*.*)"
        )
        if not filepath:
            return

        try:
            import imageio
            QMessageBox.information(self.app, "Saving Animation",
                                  "This may take a moment. The app will be unresponsive during saving.")

            start_val, end_val = self.get_time_range()
            if self.app.is_continuous:
                frames = self.app.animation_utils.create_frame_sequence(
                    start_val, end_val, True, 75
                )
            else:
                frames = self.app.animation_utils.create_frame_sequence(
                    start_val, end_val, False
                )

            with imageio.get_writer(filepath, mode='I', duration=0.1) as writer:
                for time_val in frames:
                    if hasattr(self.app, 'plot_manager'):
                        self.app.plot_manager.update_plots(time_val)
                    self.app.fig.canvas.draw()

                    # Get image data
                    image = self.app.fig.canvas.buffer_rgba()
                    width, height = self.app.fig.canvas.get_width_height()
                    image = image.reshape((height, width, 4))
                    # Convert RGBA to RGB
                    image_rgb = image[:, :, :3]
                    writer.append_data(image_rgb)

            QMessageBox.information(self.app, "Success",
                                  f"Animation saved to {filepath}")

        except ImportError:
            QMessageBox.critical(self.app, "Error",
                               "imageio library not found. Please install it with: pip install imageio")
        except Exception as e:
            QMessageBox.critical(self.app, "Error",
                               f"Failed to save animation: {e}")
