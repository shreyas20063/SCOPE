"""
Main GUI Window for Fourier Analysis
Provides interactive interface for exploring Fourier transform magnitude vs phase
"""

import sys
import os
import tempfile
import wave
import numpy as np
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QTabWidget, QGroupBox, QLabel, QSlider, QComboBox,
                            QPushButton, QSpinBox, QDoubleSpinBox, QCheckBox,
                            QFileDialog, QTextEdit, QSplitter, QGridLayout,
                            QProgressBar, QStatusBar, QStackedWidget)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QUrl
from PyQt5.QtMultimedia import QSoundEffect
from PyQt5.QtGui import QFont

from fourier.fourier_model import FourierModel
from fourier.audio_fourier_model import AudioFourierModel
from processing.image_ops import ImageProcessor
from processing.audio_ops import AudioProcessor
from visualization.plots import FourierPlotter
from gui.control_widgets import FourierControls, ImageControls, AudioControls
from gui.results_display import ResultsDisplay
from gui.audio_results_display import AudioResultsDisplay


class AnalysisWorker(QThread):
    """
    Worker thread for running Fourier analysis to keep GUI responsive
    """

    finished = pyqtSignal(dict)  # Emit results when done
    progress = pyqtSignal(int)   # Emit progress updates

    def __init__(self, fourier_model, img1, img2, params):
        super().__init__()
        self.fourier_model = fourier_model
        self.img1 = img1
        self.img2 = img2
        self.params = params

    def run(self):
        """Run Fourier analysis in background thread"""
        try:
            results = {}

            # Compute Fourier transforms
            self.progress.emit(20)
            fft1, mag1_orig, phase1_orig = self.fourier_model.compute_fourier_transform(self.img1)
            fft2, mag2_orig, phase2_orig = self.fourier_model.compute_fourier_transform(self.img2)

            results['mag1_orig'] = mag1_orig
            results['mag2_orig'] = mag2_orig
            results['phase1_orig'] = phase1_orig
            results['phase2_orig'] = phase2_orig

            # Apply modes for Image 1
            self.progress.emit(40)
            if self.params['img1_mode'] == 'original':
                mag1_display = mag1_orig.copy()
                phase1_display = phase1_orig.copy()
                img1_recon = self.img1.copy()
            elif self.params['img1_mode'] == 'uniform_mag':
                mag1_display = np.ones_like(mag1_orig) * self.params['uniform_magnitude']
                phase1_display = phase1_orig.copy()
                img1_recon = self.fourier_model.reconstruct_from_components(mag1_display, phase1_display)
            elif self.params['img1_mode'] == 'uniform_phase':
                mag1_display = mag1_orig.copy()
                phase1_display = np.ones_like(phase1_orig) * self.params['uniform_phase']
                img1_recon = self.fourier_model.reconstruct_from_components(mag1_display, phase1_display)

            results['mag1_display'] = mag1_display
            results['phase1_display'] = phase1_display
            results['img1_recon'] = img1_recon

            # Apply modes for Image 2
            self.progress.emit(60)
            if self.params['img2_mode'] == 'original':
                mag2_display = mag2_orig.copy()
                phase2_display = phase2_orig.copy()
                img2_recon = self.img2.copy()
            elif self.params['img2_mode'] == 'uniform_mag':
                mag2_display = np.ones_like(mag2_orig) * self.params['uniform_magnitude']
                phase2_display = phase2_orig.copy()
                img2_recon = self.fourier_model.reconstruct_from_components(mag2_display, phase2_display)
            elif self.params['img2_mode'] == 'uniform_phase':
                mag2_display = mag2_orig.copy()
                phase2_display = np.ones_like(phase2_orig) * self.params['uniform_phase']
                img2_recon = self.fourier_model.reconstruct_from_components(mag2_display, phase2_display)

            results['mag2_display'] = mag2_display
            results['phase2_display'] = phase2_display
            results['img2_recon'] = img2_recon

            # Create hybrid images
            self.progress.emit(75)
            hybrid_mag1_phase2 = self.fourier_model.create_hybrid_image(
                mag1_orig, phase1_orig, mag2_orig, phase2_orig, 'mag1_phase2'
            )
            hybrid_mag2_phase1 = self.fourier_model.create_hybrid_image(
                mag1_orig, phase1_orig, mag2_orig, phase2_orig, 'mag2_phase1'
            )

            results['hybrid_mag1_phase2'] = hybrid_mag1_phase2
            results['hybrid_mag2_phase1'] = hybrid_mag2_phase1

            # Calculate quality metrics
            self.progress.emit(90)
            quality1 = self.fourier_model.calculate_reconstruction_quality(self.img1, img1_recon)
            quality2 = self.fourier_model.calculate_reconstruction_quality(self.img2, img2_recon)

            results['quality1'] = quality1
            results['quality2'] = quality2

            self.progress.emit(100)
            self.finished.emit(results)

        except Exception as e:
            print(f"Analysis error: {e}")
            import traceback
            traceback.print_exc()
            self.finished.emit({'error': str(e)})


class AudioAnalysisWorker(QThread):
    """Worker thread for running Fourier analysis on audio signals"""

    finished = pyqtSignal(dict)
    progress = pyqtSignal(int)

    def __init__(self, audio_model, signal1, signal2, params):
        super().__init__()
        self.audio_model = audio_model
        self.signal1 = signal1
        self.signal2 = signal2
        self.params = params

    def run(self):
        try:
            results = {}

            min_len = min(len(self.signal1), len(self.signal2))
            signal1 = self.signal1[:min_len]
            signal2 = self.signal2[:min_len]

            self.progress.emit(20)
            fft1, mag1_orig, phase1_orig = self.audio_model.compute_fourier_transform(signal1)
            fft2, mag2_orig, phase2_orig = self.audio_model.compute_fourier_transform(signal2)

            results['mag1_orig'] = mag1_orig
            results['mag2_orig'] = mag2_orig
            results['phase1_orig'] = phase1_orig
            results['phase2_orig'] = phase2_orig

            self.progress.emit(40)
            if self.params['img1_mode'] == 'original':
                mag1_display = mag1_orig.copy()
                phase1_display = phase1_orig.copy()
                signal1_recon = signal1.copy()
            elif self.params['img1_mode'] == 'uniform_mag':
                mag1_display = np.ones_like(mag1_orig) * self.params['uniform_magnitude']
                phase1_display = phase1_orig.copy()
                signal1_recon = self.audio_model.reconstruct_from_components(mag1_display, phase1_display)
            elif self.params['img1_mode'] == 'uniform_phase':
                mag1_display = mag1_orig.copy()
                phase1_display = np.ones_like(phase1_orig) * self.params['uniform_phase']
                signal1_recon = self.audio_model.reconstruct_from_components(mag1_display, phase1_display)

            results['mag1_display'] = mag1_display
            results['phase1_display'] = phase1_display
            results['signal1_recon'] = signal1_recon

            self.progress.emit(60)
            if self.params['img2_mode'] == 'original':
                mag2_display = mag2_orig.copy()
                phase2_display = phase2_orig.copy()
                signal2_recon = signal2.copy()
            elif self.params['img2_mode'] == 'uniform_mag':
                mag2_display = np.ones_like(mag2_orig) * self.params['uniform_magnitude']
                phase2_display = phase2_orig.copy()
                signal2_recon = self.audio_model.reconstruct_from_components(mag2_display, phase2_display)
            elif self.params['img2_mode'] == 'uniform_phase':
                mag2_display = mag2_orig.copy()
                phase2_display = np.ones_like(phase2_orig) * self.params['uniform_phase']
                signal2_recon = self.audio_model.reconstruct_from_components(mag2_display, phase2_display)

            results['mag2_display'] = mag2_display
            results['phase2_display'] = phase2_display
            results['signal2_recon'] = signal2_recon

            self.progress.emit(75)
            hybrid_mag1_phase2 = self.audio_model.create_hybrid_signal(
                mag1_orig, phase1_orig, mag2_orig, phase2_orig, 'mag1_phase2'
            )
            hybrid_mag2_phase1 = self.audio_model.create_hybrid_signal(
                mag1_orig, phase1_orig, mag2_orig, phase2_orig, 'mag2_phase1'
            )

            results['hybrid_mag1_phase2'] = hybrid_mag1_phase2
            results['hybrid_mag2_phase1'] = hybrid_mag2_phase1

            self.progress.emit(90)
            quality1 = self.audio_model.calculate_reconstruction_quality(signal1, signal1_recon)
            quality2 = self.audio_model.calculate_reconstruction_quality(signal2, signal2_recon)

            results['quality1'] = quality1
            results['quality2'] = quality2

            self.progress.emit(100)
            self.finished.emit(results)

        except Exception as e:
            print(f"Audio analysis error: {e}")
            import traceback
            traceback.print_exc()
            self.finished.emit({'error': str(e)})

class MainWindow(QMainWindow):
    """
    Main application window for Fourier analysis
    """

    def __init__(self):
        super().__init__()

        # Initialize components
        self.fourier_model = FourierModel()
        self.audio_model = AudioFourierModel()
        self.image_processor = ImageProcessor()
        self.audio_processor = AudioProcessor()
        self.plotter = FourierPlotter()

        # Current state
        self.current_img1 = None
        self.current_img2 = None
        self.current_img1_display = None
        self.current_img2_display = None
        self.current_results = {}
        self.worker = None

        self.current_audio1 = None
        self.current_audio2 = None
        self.current_audio1_trimmed = None
        self.current_audio2_trimmed = None
        self.audio_results = {}
        self.audio_sample_rate = self.audio_processor.sample_rate
        self.audio1_name = "Sine"
        self.audio2_name = "Square"

        self.mode = 'image'
        self.temp_audio_files = []
        self.active_sound_effects = []
        self.sound_file_map = {}

        # Image names for dynamic labeling
        self.img1_name = "Building"
        self.img2_name = "Face"

        # Setup UI
        self.setup_ui()
        self.setup_connections()

        # Load default images
        self.load_default_images()
        self.load_default_audio()

        # Set window properties
        self.setWindowTitle("Fourier Transform: Magnitude vs Phase Analysis")
        self.setGeometry(100, 100, 1600, 1000)

    def setup_ui(self):
        """Setup the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QHBoxLayout(central_widget)

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # Left panel: Controls
        left_panel = self.create_control_panel()
        splitter.addWidget(left_panel)

        # Right panel: Results and visualization
        right_panel = self.create_results_panel()
        splitter.addWidget(right_panel)

        # Set splitter proportions
        splitter.setSizes([400, 1200])

        # Status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.statusBar.addPermanentWidget(self.progress_bar)

    def create_control_panel(self):
        """Create the control panel with parameter controls"""
        control_widget = QWidget()
        layout = QVBoxLayout(control_widget)

        # Title
        title_label = QLabel("Analysis Controls")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title_label)

        # Mode toggle
        self.mode_toggle_button = QPushButton("Switch to Audio Mode")
        self.mode_toggle_button.setStyleSheet(
            "QPushButton { background-color: #6C63FF; color: white; font-weight: bold; padding: 8px; }"
        )
        layout.addWidget(self.mode_toggle_button)

        # Fourier controls
        self.fourier_controls = FourierControls()
        layout.addWidget(self.fourier_controls)
        self.fourier_controls.set_mode('image')

        # Source controls stack
        self.image_controls = ImageControls()
        self.audio_controls = AudioControls()
        self.source_stack = QStackedWidget()
        self.source_stack.addWidget(self.image_controls)
        self.source_stack.addWidget(self.audio_controls)
        layout.addWidget(self.source_stack)
        self.source_stack.setCurrentIndex(0)

        # Audio playback controls (visible in audio mode)
        self.audio_playback_group = QGroupBox("Audio Playback")
        playback_layout = QGridLayout(self.audio_playback_group)
        self.play_audio1_original_button = QPushButton("Play Audio 1 - Original")
        self.play_audio1_recon_button = QPushButton("Play Audio 1 - Reconstructed")
        self.play_audio2_original_button = QPushButton("Play Audio 2 - Original")
        self.play_audio2_recon_button = QPushButton("Play Audio 2 - Reconstructed")
        self.play_hybrid1_button = QPushButton("Play Hybrid (Mag1 + Phase2)")
        self.play_hybrid2_button = QPushButton("Play Hybrid (Mag2 + Phase1)")

        buttons = [
            (self.play_audio1_original_button, 0, 0),
            (self.play_audio1_recon_button, 0, 1),
            (self.play_audio2_original_button, 1, 0),
            (self.play_audio2_recon_button, 1, 1),
            (self.play_hybrid1_button, 2, 0),
            (self.play_hybrid2_button, 2, 1)
        ]
        for button, row, col in buttons:
            playback_layout.addWidget(button, row, col)

        layout.addWidget(self.audio_playback_group)
        self.audio_playback_group.setVisible(False)

        # Analysis controls
        analysis_group = QGroupBox("Analysis")
        analysis_layout = QVBoxLayout(analysis_group)

        self.auto_update_check = QCheckBox("Auto-update on parameter change")
        self.auto_update_check.setChecked(True)
        analysis_layout.addWidget(self.auto_update_check)

        layout.addWidget(analysis_group)

        # Export controls
        export_group = QGroupBox("Export")
        export_layout = QVBoxLayout(export_group)

        self.save_results_button = QPushButton("Save Results")
        self.save_plots_button = QPushButton("Save Plots")

        export_layout.addWidget(self.save_results_button)
        export_layout.addWidget(self.save_plots_button)

        layout.addWidget(export_group)

        # Stretch to push everything to top
        layout.addStretch()

        return control_widget

    def create_results_panel(self):
        """Create the results and visualization panel"""
        results_widget = QWidget()
        layout = QVBoxLayout(results_widget)

        # Stack for image/audio results
        self.results_stack = QStackedWidget()
        layout.addWidget(self.results_stack)

        # Image analysis tabs
        self.image_tab_widget = QTabWidget()
        self.results_display = ResultsDisplay(self.plotter)
        self.image_tab_widget.addTab(self.results_display.image1_tab, "Image 1 Analysis")
        self.image_tab_widget.addTab(self.results_display.image2_tab, "Image 2 Analysis")
        self.image_tab_widget.addTab(self.results_display.comparison_tab, "Hybrid Comparison")
        self.results_stack.addWidget(self.image_tab_widget)

        # Audio analysis tabs
        self.audio_tab_widget = QTabWidget()
        self.audio_results_display = AudioResultsDisplay(self.plotter)
        self.audio_tab_widget.addTab(self.audio_results_display.audio1_tab, "Audio 1 Analysis")
        self.audio_tab_widget.addTab(self.audio_results_display.audio2_tab, "Audio 2 Analysis")
        self.audio_tab_widget.addTab(self.audio_results_display.hybrid_tab, "Audio Hybrid")
        self.results_stack.addWidget(self.audio_tab_widget)

        self.results_stack.setCurrentIndex(0)

        return results_widget

    def setup_connections(self):
        """Setup signal-slot connections"""
        self.mode_toggle_button.clicked.connect(self.toggle_mode)

        # Parameter change connections
        self.fourier_controls.parameter_changed.connect(self.on_parameter_changed)

        # Image controls
        self.image_controls.load_image1_button.clicked.connect(lambda: self.load_image_file(1))
        self.image_controls.load_image2_button.clicked.connect(lambda: self.load_image_file(2))
        self.image_controls.pattern1_combo.currentTextChanged.connect(lambda: self.load_test_pattern(1))
        self.image_controls.pattern2_combo.currentTextChanged.connect(lambda: self.load_test_pattern(2))

        # Audio controls
        self.audio_controls.load_audio1_button.clicked.connect(lambda: self.load_audio_file(1))
        self.audio_controls.load_audio2_button.clicked.connect(lambda: self.load_audio_file(2))
        self.audio_controls.pattern1_combo.currentTextChanged.connect(lambda: self.load_test_audio(1))
        self.audio_controls.pattern2_combo.currentTextChanged.connect(lambda: self.load_test_audio(2))

        # Audio playback controls
        self.play_audio1_original_button.clicked.connect(lambda: self.play_audio('audio1_original'))
        self.play_audio1_recon_button.clicked.connect(lambda: self.play_audio('audio1_recon'))
        self.play_audio2_original_button.clicked.connect(lambda: self.play_audio('audio2_original'))
        self.play_audio2_recon_button.clicked.connect(lambda: self.play_audio('audio2_recon'))
        self.play_hybrid1_button.clicked.connect(lambda: self.play_audio('hybrid1'))
        self.play_hybrid2_button.clicked.connect(lambda: self.play_audio('hybrid2'))

        # Export controls
        self.save_results_button.clicked.connect(self.save_results)
        self.save_plots_button.clicked.connect(self.save_plots)

        # Auto-update timer
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.run_analysis)

    def on_parameter_changed(self):
        """Handle parameter changes"""
        if not self.auto_update_check.isChecked():
            return

        if self.mode == 'image':
            ready = self.current_img1 is not None and self.current_img2 is not None
        else:
            ready = self.current_audio1 is not None and self.current_audio2 is not None

        if ready:
            self.update_timer.start(300)

    def load_default_images(self):
        """Load default test images"""
        self.current_img1 = self.image_processor.generate_test_image(
            size=256, pattern='building'
        )
        self.current_img2 = self.image_processor.generate_test_image(
            size=256, pattern='face'
        )
        self.current_img1_display = self._prepare_display_image(self.current_img1)
        self.current_img2_display = self._prepare_display_image(self.current_img2)
        self.image_controls.set_pattern_selection(1, "Building")
        self.image_controls.set_pattern_selection(2, "Face")
        self.image_controls.update_image_info(1, self.current_img1_display)
        self.image_controls.update_image_info(2, self.current_img2_display)
        self.fourier_controls.reset_all()

        # Run initial analysis
        self.run_analysis()

    def load_default_audio(self):
        """Load default test audio signals"""
        audio1, sr1 = self.audio_processor.generate_test_signal('sine')
        audio2, sr2 = self.audio_processor.generate_test_signal('square')

        self.current_audio1 = audio1
        self.current_audio2 = audio2
        self.current_audio1_trimmed = None
        self.current_audio2_trimmed = None
        self.audio_sample_rate = sr1
        self.audio1_name = "Sine"
        self.audio2_name = "Square"

        self.audio_controls.set_pattern_selection(1, "Sine")
        self.audio_controls.set_pattern_selection(2, "Square")
        self.audio_controls.update_audio_info(1, self.current_audio1, self.audio_sample_rate)
        self.audio_controls.update_audio_info(2, self.current_audio2, self.audio_sample_rate)
        self.fourier_controls.reset_all()

    def load_image_file(self, image_num):
        """Load image from file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, f"Load Image {image_num}", "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.tiff);;All Files (*)"
        )

        if file_path:
            try:
                gray_img, display_img = self.image_processor.load_image(file_path, target_size=256)

                # Extract filename without extension for label
                filename = os.path.splitext(os.path.basename(file_path))[0]

                if image_num == 1:
                    self.current_img1 = gray_img
                    self.current_img1_display = self._prepare_display_image(display_img)
                    self.img1_name = filename
                else:
                    self.current_img2 = gray_img
                    self.current_img2_display = self._prepare_display_image(display_img)
                    self.img2_name = filename

                display_reference = self.current_img1_display if image_num == 1 else self.current_img2_display
                self.image_controls.update_image_info(image_num, display_reference)
                self.image_controls.set_custom_image_label(image_num, filename)
                self.fourier_controls.reset_all()
                self.fourier_controls.set_channel_mode(image_num, 'original')
                self.statusBar.showMessage(f"Loaded image {image_num}: {file_path}")

                if self.auto_update_check.isChecked():
                    self.run_analysis()

            except Exception as e:
                self.statusBar.showMessage(f"Error loading image: {e}")

    def load_audio_file(self, audio_num):
        """Load audio from file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, f"Load Audio {audio_num}", "",
            "Audio Files (*.wav *.flac *.aiff *.aif);;All Files (*)"
        )

        if file_path:
            try:
                signal, sample_rate = self.audio_processor.load_audio(file_path)

                filename = os.path.splitext(os.path.basename(file_path))[0]

                if audio_num == 1:
                    self.current_audio1 = signal
                    self.audio1_name = filename
                    self.current_audio1_trimmed = None
                else:
                    self.current_audio2 = signal
                    self.audio2_name = filename
                    self.current_audio2_trimmed = None

                self.audio_sample_rate = sample_rate
                self.audio_controls.update_audio_info(audio_num, signal, sample_rate)
                self.audio_controls.set_custom_audio_label(audio_num, filename)
                self.fourier_controls.reset_all()
                self.fourier_controls.set_channel_mode(audio_num, 'original')
                self.statusBar.showMessage(f"Loaded audio {audio_num}: {file_path}")

                if self.mode == 'audio' and self.auto_update_check.isChecked():
                    self.run_analysis()

            except Exception as e:
                self.statusBar.showMessage(f"Error loading audio: {e}")

    def load_test_pattern(self, image_num):
        """Load test pattern"""
        pattern_map = {
            'Building': 'building',
            'Face': 'face',
            'Geometric': 'geometric',
            'Texture': 'texture'
        }

        if image_num == 1:
            pattern_name = self.image_controls.pattern1_combo.currentText()
        else:
            pattern_name = self.image_controls.pattern2_combo.currentText()

        if pattern_name in pattern_map:
            generated_img = self.image_processor.generate_test_image(
                size=256, pattern=pattern_map[pattern_name]
            )

            if image_num == 1:
                self.current_img1 = generated_img
                self.current_img1_display = self._prepare_display_image(generated_img)
                self.img1_name = pattern_name
            else:
                self.current_img2 = generated_img
                self.current_img2_display = self._prepare_display_image(generated_img)
                self.img2_name = pattern_name

            display_reference = self.current_img1_display if image_num == 1 else self.current_img2_display
            self.image_controls.update_image_info(image_num, display_reference)
            self.image_controls.set_pattern_selection(image_num, pattern_name)
            self.fourier_controls.reset_all()
            self.fourier_controls.set_channel_mode(image_num, 'original')

            if self.auto_update_check.isChecked():
                self.run_analysis()

    def load_test_audio(self, audio_num):
        """Load test audio signal"""
        pattern_map = {
            'Sine': 'sine',
            'Square': 'square',
            'Sawtooth': 'sawtooth',
            'Beat': 'beat'
        }

        combo = self.audio_controls.pattern1_combo if audio_num == 1 else self.audio_controls.pattern2_combo
        pattern_name = combo.currentText()

        if pattern_name in pattern_map:
            generated_signal, sample_rate = self.audio_processor.generate_test_signal(pattern_map[pattern_name])

            if audio_num == 1:
                self.current_audio1 = generated_signal
                self.audio1_name = pattern_name
                self.current_audio1_trimmed = None
            else:
                self.current_audio2 = generated_signal
                self.audio2_name = pattern_name
                self.current_audio2_trimmed = None

            self.audio_sample_rate = sample_rate
            self.audio_controls.update_audio_info(audio_num, generated_signal, sample_rate)
            self.fourier_controls.reset_all()
            self.fourier_controls.set_channel_mode(audio_num, 'original')

            if self.mode == 'audio' and self.auto_update_check.isChecked():
                self.run_analysis()

    def toggle_mode(self):
        """Switch between image and audio analysis modes"""
        if self.worker and self.worker.isRunning():
            return

        if self.mode == 'image':
            self.mode = 'audio'
            self.mode_toggle_button.setText("Switch to Image Mode")
            self.fourier_controls.set_mode('audio')
            self.fourier_controls.reset_all()
            self.fourier_controls.set_channel_mode(1, 'original')
            self.fourier_controls.set_channel_mode(2, 'original')
            self.source_stack.setCurrentIndex(1)
            self.results_stack.setCurrentIndex(1)
            self.audio_playback_group.setVisible(True)
            self.statusBar.showMessage("Audio mode enabled")
        else:
            self.mode = 'image'
            self.mode_toggle_button.setText("Switch to Audio Mode")
            self.fourier_controls.set_mode('image')
            self.fourier_controls.reset_all()
            self.fourier_controls.set_channel_mode(1, 'original')
            self.fourier_controls.set_channel_mode(2, 'original')
            self.source_stack.setCurrentIndex(0)
            self.results_stack.setCurrentIndex(0)
            self.audio_playback_group.setVisible(False)
            self.statusBar.showMessage("Image mode enabled")

        if self.auto_update_check.isChecked():
            self.run_analysis()

    def play_audio(self, key):
        """Play selected audio signal or reconstruction"""
        if self.mode != 'audio':
            self.statusBar.showMessage("Switch to Audio mode to play signals")
            return

        if key in ('audio1_recon', 'audio2_recon', 'hybrid1', 'hybrid2') and not self.audio_results:
            self.statusBar.showMessage("Run audio analysis to generate reconstructions")
            return

        signal = None
        if key == 'audio1_original':
            signal = self.current_audio1_trimmed if self.current_audio1_trimmed is not None else self.current_audio1
        elif key == 'audio2_original':
            signal = self.current_audio2_trimmed if self.current_audio2_trimmed is not None else self.current_audio2
        elif key == 'audio1_recon':
            signal = self.audio_results.get('signal1_recon')
        elif key == 'audio2_recon':
            signal = self.audio_results.get('signal2_recon')
        elif key == 'hybrid1':
            signal = self.audio_results.get('hybrid_mag1_phase2')
        elif key == 'hybrid2':
            signal = self.audio_results.get('hybrid_mag2_phase1')

        if signal is None or len(signal) == 0:
            self.statusBar.showMessage("Audio signal not available")
            return

        self._play_audio_signal(np.asarray(signal, dtype=np.float64))

    def _play_audio_signal(self, signal):
        """Play a numpy audio signal using QSoundEffect"""
        wav_path = self._create_temp_wav(signal)
        effect = QSoundEffect()
        effect.setSource(QUrl.fromLocalFile(wav_path))
        effect.setLoopCount(1)
        effect.setVolume(0.7)
        effect.play()

        self.active_sound_effects.append(effect)
        self.sound_file_map[effect] = wav_path
        effect.playingChanged.connect(lambda eff=effect: self._handle_sound_finished(eff))

    def _handle_sound_finished(self, effect):
        if effect in self.active_sound_effects and not effect.isPlaying():
            self.active_sound_effects.remove(effect)
            wav_path = self.sound_file_map.pop(effect, None)
            if wav_path:
                if wav_path in self.temp_audio_files:
                    self.temp_audio_files.remove(wav_path)
                try:
                    os.remove(wav_path)
                except OSError:
                    pass

    def _create_temp_wav(self, signal):
        """Create a temporary WAV file from a numpy array"""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        temp_path = temp_file.name
        temp_file.close()

        clipped = np.clip(signal, -1.0, 1.0)
        pcm_data = (clipped * 32767).astype(np.int16)

        with wave.open(temp_path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.audio_sample_rate)
            wf.writeframes(pcm_data.tobytes())

        self.temp_audio_files.append(temp_path)
        return temp_path

    def run_analysis(self):
        """Run Fourier analysis"""
        if self.worker and self.worker.isRunning():
            return  # Analysis already running

        # Get parameters from controls
        params = self.fourier_controls.get_parameters()

        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.statusBar.showMessage("Running analysis...")

        if self.mode == 'image':
            if self.current_img1 is None or self.current_img2 is None:
                self.statusBar.showMessage("No images loaded")
                self.progress_bar.setVisible(False)
                return

            self.worker = AnalysisWorker(
                self.fourier_model,
                self.current_img1,
                self.current_img2,
                params
            )
            self.worker.finished.connect(self.on_image_analysis_finished)
        else:
            if self.current_audio1 is None or self.current_audio2 is None:
                self.statusBar.showMessage("No audio signals loaded")
                self.progress_bar.setVisible(False)
                return

            self.worker = AudioAnalysisWorker(
                self.audio_model,
                self.current_audio1,
                self.current_audio2,
                params
            )
            self.worker.finished.connect(self.on_audio_analysis_finished)

        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.start()

    def on_image_analysis_finished(self, results):
        """Handle analysis completion"""
        self.progress_bar.setVisible(False)

        if 'error' in results:
            self.statusBar.showMessage(f"Analysis error: {results['error']}")
            return

        # Store results
        self.current_results = results

        # Update displays
        self.results_display.update_results(
            self.current_img1,
            self.current_img2,
            results,
            self.img1_name,
            self.img2_name,
            img1_display=self.current_img1_display,
            img2_display=self.current_img2_display
        )

        self.statusBar.showMessage("Analysis completed")
        self.worker = None

    def on_audio_analysis_finished(self, results):
        """Handle audio analysis completion"""
        self.progress_bar.setVisible(False)

        if 'error' in results:
            self.statusBar.showMessage(f"Analysis error: {results['error']}")
            return

        self.audio_results = results

        min_len = min(len(self.current_audio1), len(self.current_audio2),
                       len(results['signal1_recon']), len(results['signal2_recon']))
        signal1 = self.current_audio1[:min_len]
        signal2 = self.current_audio2[:min_len]

        self.current_audio1_trimmed = signal1
        self.current_audio2_trimmed = signal2

        self.audio_results_display.update_results(
            signal1,
            signal2,
            results,
            self.audio_sample_rate,
            name1=self.audio1_name,
            name2=self.audio2_name
        )

        self.audio_tab_widget.setTabText(0, f"{self.audio1_name} Analysis")
        self.audio_tab_widget.setTabText(1, f"{self.audio2_name} Analysis")
        self.audio_tab_widget.setTabText(2, f"Hybrid: {self.audio1_name} / {self.audio2_name}")

        self.statusBar.showMessage("Audio analysis completed")
        self.worker = None

    def save_results(self):
        """Save analysis results to file"""
        if self.mode == 'image':
            if not self.current_results:
                self.statusBar.showMessage("No results to save")
                return
            default_name = "fourier_image_results.npz"
        else:
            if not self.audio_results:
                self.statusBar.showMessage("No results to save")
                return
            default_name = "fourier_audio_results.npz"

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Results", default_name,
            "NumPy Archive (*.npz);;All Files (*)"
        )

        if file_path:
            try:
                if self.mode == 'image':
                    save_data = {
                        'image1': self.current_img1,
                        'image2': self.current_img2,
                        'magnitude1': self.current_results['mag1_orig'],
                        'magnitude2': self.current_results['mag2_orig'],
                        'phase1': self.current_results['phase1_orig'],
                        'phase2': self.current_results['phase2_orig'],
                        'hybrid1': self.current_results['hybrid_mag1_phase2'],
                        'hybrid2': self.current_results['hybrid_mag2_phase1'],
                        'parameters': self.fourier_controls.get_parameters()
                    }
                else:
                    save_data = {
                        'audio1': self.current_audio1,
                        'audio2': self.current_audio2,
                        'sample_rate': self.audio_sample_rate,
                        'magnitude1': self.audio_results['mag1_orig'],
                        'magnitude2': self.audio_results['mag2_orig'],
                        'phase1': self.audio_results['phase1_orig'],
                        'phase2': self.audio_results['phase2_orig'],
                        'hybrid1': self.audio_results['hybrid_mag1_phase2'],
                        'hybrid2': self.audio_results['hybrid_mag2_phase1'],
                        'parameters': self.fourier_controls.get_parameters()
                    }

                np.savez(file_path, **save_data)
                self.statusBar.showMessage(f"Results saved to: {file_path}")

            except Exception as e:
                self.statusBar.showMessage(f"Error saving results: {e}")

    def _prepare_display_image(self, image):
        """
        Ensure an image is suitable for display (convert grayscale to RGB)

        Args:
            image (np.ndarray): Input image

        Returns:
            np.ndarray: Display-ready image
        """
        if image is None:
            return None

        if image.ndim == 2:
            return np.repeat(image[..., np.newaxis], 3, axis=2)

        return image

    def save_plots(self):
        """Save current plots to image files"""
        if self.mode == 'image':
            if not self.current_results:
                self.statusBar.showMessage("No plots to save")
                return
        else:
            if not self.audio_results:
                self.statusBar.showMessage("No plots to save")
                return

        directory = QFileDialog.getExistingDirectory(self, "Select Directory for Plots")

        if directory:
            try:
                if self.mode == 'image':
                    tabs = [
                        ('image1', getattr(self.results_display, 'img1_fig', None)),
                        ('image2', getattr(self.results_display, 'img2_fig', None)),
                        ('comparison', getattr(self.results_display, 'comp_fig', None)),
                    ]
                else:
                    tabs = [
                        ('audio1', getattr(self.audio_results_display, 'audio1_fig', None)),
                        ('audio2', getattr(self.audio_results_display, 'audio2_fig', None)),
                        ('audio_hybrid', getattr(self.audio_results_display, 'hybrid_fig', None)),
                    ]

                for name, fig in tabs:
                    if fig:
                        file_path = f"{directory}/plot_{name}.png"
                        self.plotter.save_figure(fig, file_path)

                self.statusBar.showMessage(f"Plots saved to: {directory}")

            except Exception as e:
                self.statusBar.showMessage(f"Error saving plots: {e}")

    def closeEvent(self, event):
        """Handle application closing"""
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()

        for effect in list(self.active_sound_effects):
            effect.stop()
        self.active_sound_effects.clear()
        self.sound_file_map.clear()

        for path in self.temp_audio_files:
            try:
                os.remove(path)
            except OSError:
                pass
        self.temp_audio_files.clear()
        event.accept()
