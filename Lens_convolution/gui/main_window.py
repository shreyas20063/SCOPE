"""
Main GUI Window for Lens Simulation
Provides interactive interface for exploring lens imaging and blurring effects
"""

import sys
import numpy as np
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QTabWidget, QGroupBox, QLabel, QSlider, QComboBox,
                            QPushButton, QSpinBox, QDoubleSpinBox, QCheckBox,
                            QFileDialog, QTextEdit, QSplitter, QGridLayout,
                            QProgressBar, QStatusBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont

from optics.lens_model import LensModel
from processing.image_ops import ImageProcessor  
from visualization.plots import SimulationPlotter
from gui.control_widgets import ParameterControls, ImageControls
from gui.results_display import ResultsDisplay

class SimulationWorker(QThread):
    """
    Worker thread for running simulations to keep GUI responsive
    """
    
    finished = pyqtSignal(dict)  # Emit results when done
    progress = pyqtSignal(int)   # Emit progress updates
    
    def __init__(self, lens_model, image_processor, image, params):
        super().__init__()
        self.lens_model = lens_model
        self.image_processor = image_processor
        self.image = image
        self.params = params
        
    def run(self):
        """Run simulation in background thread"""
        try:
            results = {}
            
            # Generate PSF
            self.progress.emit(25)
            if self.params.get('atmospheric_seeing'):
                psf, extent = self.lens_model.combined_psf(
                    self.params['diameter'],
                    self.params['focal_length'], 
                    self.params['atmospheric_seeing'],
                    self.params['psf_size']
                )
            else:
                psf, extent, airy_radius = self.lens_model.airy_disk_psf(
                    self.params['diameter'],
                    self.params['focal_length'],
                    self.params['psf_size']
                )
                results['airy_radius'] = airy_radius
            
            results['psf'] = psf
            results['extent'] = extent
            
            # Calculate PSF metrics
            self.progress.emit(50)
            psf_metrics = self.lens_model.psf_metrics(psf, self.params['pixel_size'])
            results['psf_metrics'] = psf_metrics
            
            # Convolve image with PSF
            self.progress.emit(75)
            psf_resized = self.image_processor.match_psf_size(psf, self.image.shape[0])
            blurred_image = self.image_processor.convolve_with_psf(
                self.image, psf_resized, self.params['noise_level']
            )
            results['blurred_image'] = blurred_image
            
            # Calculate image quality metrics
            self.progress.emit(90)
            quality_metrics = self.image_processor.calculate_image_quality_metrics(
                self.image, blurred_image
            )
            results['quality_metrics'] = quality_metrics
            
            self.progress.emit(100)
            self.finished.emit(results)
            
        except Exception as e:
            print(f"Simulation error: {e}")
            self.finished.emit({'error': str(e)})

class MainWindow(QMainWindow):
    """
    Main application window for lens simulation
    """
    
    def __init__(self):
        super().__init__()
        
        # Initialize components
        self.lens_model = LensModel()
        self.image_processor = ImageProcessor()
        self.plotter = SimulationPlotter()
        
        # Current state
        self.current_image = None
        self.current_results = {}
        self.worker = None
        
        # Setup UI
        self.setup_ui()
        self.setup_connections()
        
        # Load default image
        self.load_default_image()
        
        # Set window properties
        self.setWindowTitle("Lens Imaging and Blurring Simulation")
        self.setGeometry(100, 100, 1400, 900)
        
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
        splitter.setSizes([350, 1050])
        
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
        title_label = QLabel("Simulation Controls")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title_label)
        
        # Parameter controls
        self.param_controls = ParameterControls()
        layout.addWidget(self.param_controls)
        
        # Image controls
        self.image_controls = ImageControls()
        layout.addWidget(self.image_controls)
        
        # Simulation controls
        sim_group = QGroupBox("Simulation")
        sim_layout = QVBoxLayout(sim_group)
        
        self.run_button = QPushButton("Run Simulation")
        self.run_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")
        sim_layout.addWidget(self.run_button)
        
        self.auto_update_check = QCheckBox("Auto-update on parameter change")
        self.auto_update_check.setChecked(True)
        sim_layout.addWidget(self.auto_update_check)
        
        layout.addWidget(sim_group)
        
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
        
        # Create tabbed interface for different views
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Results display
        self.results_display = ResultsDisplay(self.plotter)
        
        # Add tabs
        self.tab_widget.addTab(self.results_display.image_tab, "Images")
        self.tab_widget.addTab(self.results_display.psf_tab, "Point Spread Function")
        self.tab_widget.addTab(self.results_display.analysis_tab, "Analysis")
        self.tab_widget.addTab(self.results_display.lens_tab, "Lens Diagram")
        
        return results_widget
    
    def setup_connections(self):
        """Setup signal-slot connections"""
        # Simulation controls
        self.run_button.clicked.connect(self.run_simulation)
        
        # Parameter change connections
        self.param_controls.parameter_changed.connect(self.on_parameter_changed)
        
        # Image controls
        self.image_controls.load_image_button.clicked.connect(self.load_image_file)
        self.image_controls.pattern_combo.currentTextChanged.connect(self.load_test_pattern)
        
        # Export controls
        self.save_results_button.clicked.connect(self.save_results)
        self.save_plots_button.clicked.connect(self.save_plots)
        
        # Auto-update timer
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.run_simulation)
        
    def on_parameter_changed(self):
        """Handle parameter changes"""
        if self.auto_update_check.isChecked() and self.current_image is not None:
            # Debounce updates - wait 500ms after last change
            self.update_timer.start(500)
    
    def load_default_image(self):
        """Load a default test image"""
        self.current_image = self.image_processor.generate_test_image(
            size=512, pattern='resolution_chart'
        )
        self.results_display.update_original_image(self.current_image)
        self.image_controls.update_image_info(self.current_image)
        
    def load_image_file(self):
        """Load image from file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Image", "", 
            "Image Files (*.png *.jpg *.jpeg *.bmp *.tiff);;All Files (*)"
        )
        
        if file_path:
            try:
                self.current_image = self.image_processor.load_image(file_path, target_size=512)
                self.results_display.update_original_image(self.current_image)
                self.image_controls.update_image_info(self.current_image)
                self.statusBar.showMessage(f"Loaded image: {file_path}")
                
                if self.auto_update_check.isChecked():
                    self.run_simulation()
                    
            except Exception as e:
                self.statusBar.showMessage(f"Error loading image: {e}")
    
    def load_test_pattern(self, pattern_name):
        """Load test pattern"""
        pattern_map = {
            'Resolution Chart': 'resolution_chart',
            'Point Sources': 'point_sources', 
            'Edge Target': 'edge_target',
            'Star Field': 'star_field'
        }
        
        if pattern_name in pattern_map:
            self.current_image = self.image_processor.generate_test_image(
                size=512, pattern=pattern_map[pattern_name]
            )
            self.results_display.update_original_image(self.current_image)
            self.image_controls.update_image_info(self.current_image)
            
            if self.auto_update_check.isChecked():
                self.run_simulation()
    
    def run_simulation(self):
        """Run lens simulation"""
        if self.current_image is None:
            self.statusBar.showMessage("No image loaded")
            return
        
        if self.worker and self.worker.isRunning():
            return  # Simulation already running
        
        # Get parameters from controls
        params = self.param_controls.get_parameters()
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.run_button.setEnabled(False)
        self.statusBar.showMessage("Running simulation...")
        
        # Start worker thread
        self.worker = SimulationWorker(
            self.lens_model, self.image_processor, 
            self.current_image, params
        )
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.finished.connect(self.on_simulation_finished)
        self.worker.start()
    
    def on_simulation_finished(self, results):
        """Handle simulation completion"""
        self.progress_bar.setVisible(False)
        self.run_button.setEnabled(True)
        
        if 'error' in results:
            self.statusBar.showMessage(f"Simulation error: {results['error']}")
            return
        
        # Store results
        self.current_results = results
        
        # Update displays
        self.results_display.update_results(
            self.current_image,
            results['blurred_image'],
            results['psf'],
            results['extent'],
            results['psf_metrics'],
            results['quality_metrics'],
            self.param_controls.get_parameters()
        )
        
        self.statusBar.showMessage("Simulation completed")
    
    def save_results(self):
        """Save simulation results to file"""
        if not self.current_results:
            self.statusBar.showMessage("No results to save")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Results", "simulation_results.npz",
            "NumPy Archive (*.npz);;All Files (*)"
        )
        
        if file_path:
            try:
                # Prepare data for saving
                save_data = {
                    'original_image': self.current_image,
                    'blurred_image': self.current_results['blurred_image'],
                    'psf': self.current_results['psf'],
                    'extent': self.current_results['extent'],
                    'parameters': self.param_controls.get_parameters()
                }
                
                np.savez(file_path, **save_data)
                self.statusBar.showMessage(f"Results saved to: {file_path}")
                
            except Exception as e:
                self.statusBar.showMessage(f"Error saving results: {e}")
    
    def save_plots(self):
        """Save current plots to image files"""
        if not self.current_results:
            self.statusBar.showMessage("No plots to save")
            return
        
        directory = QFileDialog.getExistingDirectory(self, "Select Directory for Plots")
        
        if directory:
            try:
                # Save each tab's plot
                tabs = [
                    ('images', self.results_display.image_fig),
                    ('psf', self.results_display.psf_fig),
                    ('analysis', self.results_display.analysis_fig),
                    ('lens', self.results_display.lens_fig)
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
        event.accept()