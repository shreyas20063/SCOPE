"""
GUI Control Widgets for Lens Simulation
Contains parameter controls and image selection widgets
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                            QLabel, QSlider, QComboBox, QPushButton, QSpinBox, 
                            QDoubleSpinBox, QCheckBox, QGridLayout)
from PyQt5.QtCore import Qt, pyqtSignal

class ParameterControls(QWidget):
    """
    Widget for controlling lens and simulation parameters
    """
    
    parameter_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """Setup the parameter control interface"""
        layout = QVBoxLayout(self)
        
        # Lens Parameters
        lens_group = QGroupBox("Lens Parameters")
        lens_layout = QGridLayout(lens_group)
        
        # Lens Diameter
        lens_layout.addWidget(QLabel("Diameter (mm):"), 0, 0)
        self.diameter_spin = QDoubleSpinBox()
        self.diameter_spin.setRange(1.0, 10000.0)
        self.diameter_spin.setValue(100.0)
        self.diameter_spin.setSuffix(" mm")
        self.diameter_spin.setDecimals(1)
        lens_layout.addWidget(self.diameter_spin, 0, 1)
        
        # Focal Length
        lens_layout.addWidget(QLabel("Focal Length (mm):"), 1, 0)
        self.focal_length_spin = QDoubleSpinBox()
        self.focal_length_spin.setRange(10.0, 10000.0)
        self.focal_length_spin.setValue(500.0)
        self.focal_length_spin.setSuffix(" mm")
        self.focal_length_spin.setDecimals(1)
        lens_layout.addWidget(self.focal_length_spin, 1, 1)
        
        # Wavelength
        lens_layout.addWidget(QLabel("Wavelength (nm):"), 2, 0)
        self.wavelength_spin = QDoubleSpinBox()
        self.wavelength_spin.setRange(400.0, 700.0)
        self.wavelength_spin.setValue(550.0)
        self.wavelength_spin.setSuffix(" nm")
        self.wavelength_spin.setDecimals(1)
        lens_layout.addWidget(self.wavelength_spin, 2, 1)
        
        layout.addWidget(lens_group)
        
        # Atmospheric Parameters
        atmo_group = QGroupBox("Atmospheric Effects")
        atmo_layout = QGridLayout(atmo_group)
        
        # Enable atmospheric effects
        self.enable_atmosphere = QCheckBox("Enable Atmospheric Seeing")
        atmo_layout.addWidget(self.enable_atmosphere, 0, 0, 1, 2)
        
        # Seeing
        atmo_layout.addWidget(QLabel("Seeing FWHM (arcsec):"), 1, 0)
        self.seeing_spin = QDoubleSpinBox()
        self.seeing_spin.setRange(0.1, 10.0)
        self.seeing_spin.setValue(1.5)
        self.seeing_spin.setSuffix(" arcsec")
        self.seeing_spin.setDecimals(2)
        self.seeing_spin.setEnabled(False)
        atmo_layout.addWidget(self.seeing_spin, 1, 1)
        
        layout.addWidget(atmo_group)
        
        # Simulation Parameters
        sim_group = QGroupBox("Simulation Parameters")
        sim_layout = QGridLayout(sim_group)
        
        # PSF Size
        sim_layout.addWidget(QLabel("PSF Grid Size:"), 0, 0)
        self.psf_size_spin = QSpinBox()
        self.psf_size_spin.setRange(64, 1024)
        self.psf_size_spin.setValue(256)
        self.psf_size_spin.setSingleStep(64)
        sim_layout.addWidget(self.psf_size_spin, 0, 1)
        
        # Pixel Size
        sim_layout.addWidget(QLabel("Pixel Size (μm):"), 1, 0)
        self.pixel_size_spin = QDoubleSpinBox()
        self.pixel_size_spin.setRange(0.1, 100.0)
        self.pixel_size_spin.setValue(1.0)
        self.pixel_size_spin.setSuffix(" μm")
        self.pixel_size_spin.setDecimals(2)
        sim_layout.addWidget(self.pixel_size_spin, 1, 1)
        
        # Noise Level
        sim_layout.addWidget(QLabel("Noise Level:"), 2, 0)
        self.noise_spin = QDoubleSpinBox()
        self.noise_spin.setRange(0.0, 0.1)
        self.noise_spin.setValue(0.01)
        self.noise_spin.setDecimals(4)
        sim_layout.addWidget(self.noise_spin, 2, 1)
        
        layout.addWidget(sim_group)
        
    def setup_connections(self):
        """Setup signal connections"""
        # Connect all controls to parameter_changed signal
        self.diameter_spin.valueChanged.connect(self.parameter_changed.emit)
        self.focal_length_spin.valueChanged.connect(self.parameter_changed.emit)
        self.wavelength_spin.valueChanged.connect(self.parameter_changed.emit)
        self.enable_atmosphere.toggled.connect(self.on_atmosphere_toggled)
        self.seeing_spin.valueChanged.connect(self.parameter_changed.emit)
        self.psf_size_spin.valueChanged.connect(self.parameter_changed.emit)
        self.pixel_size_spin.valueChanged.connect(self.parameter_changed.emit)
        self.noise_spin.valueChanged.connect(self.parameter_changed.emit)
        
    def on_atmosphere_toggled(self, checked):
        """Handle atmosphere checkbox toggle"""
        self.seeing_spin.setEnabled(checked)
        self.parameter_changed.emit()
        
    def get_parameters(self):
        """Get current parameter values"""
        params = {
            'diameter': self.diameter_spin.value() * 1e-3,  # Convert mm to m
            'focal_length': self.focal_length_spin.value() * 1e-3,  # Convert mm to m
            'wavelength': self.wavelength_spin.value() * 1e-9,  # Convert nm to m
            'psf_size': self.psf_size_spin.value(),
            'pixel_size': self.pixel_size_spin.value() * 1e-6,  # Convert μm to m
            'noise_level': self.noise_spin.value()
        }
        
        if self.enable_atmosphere.isChecked():
            params['atmospheric_seeing'] = self.seeing_spin.value()
        else:
            params['atmospheric_seeing'] = None
            
        return params

class ImageControls(QWidget):
    """
    Widget for controlling image selection and loading
    """
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the image control interface"""
        layout = QVBoxLayout(self)
        
        # Image Source
        source_group = QGroupBox("Image Source")
        source_layout = QVBoxLayout(source_group)
        
        # Test pattern selection
        source_layout.addWidget(QLabel("Test Pattern:"))
        self.pattern_combo = QComboBox()
        self.pattern_combo.addItems([
            "Resolution Chart",
            "Point Sources", 
            "Edge Target",
            "Star Field"
        ])
        source_layout.addWidget(self.pattern_combo)
        
        # Load custom image
        self.load_image_button = QPushButton("Load Custom Image...")
        source_layout.addWidget(self.load_image_button)
        
        layout.addWidget(source_group)
        
        # Image Properties
        props_group = QGroupBox("Image Properties") 
        props_layout = QGridLayout(props_group)
        
        # Image size
        props_layout.addWidget(QLabel("Size:"), 0, 0)
        self.size_label = QLabel("512 × 512")
        props_layout.addWidget(self.size_label, 0, 1)
        
        # Image type
        props_layout.addWidget(QLabel("Type:"), 1, 0)
        self.type_label = QLabel("Grayscale")
        props_layout.addWidget(self.type_label, 1, 1)
        
        # Dynamic range
        props_layout.addWidget(QLabel("Range:"), 2, 0)
        self.range_label = QLabel("0.0 - 1.0")
        props_layout.addWidget(self.range_label, 2, 1)
        
        layout.addWidget(props_group)
        
    def update_image_info(self, image):
        """Update image information display"""
        if image is not None:
            if image.ndim == 2:
                h, w = image.shape
                type_str = "Grayscale"
            else:
                h, w, c = image.shape
                type_str = f"Color ({c} channels)"
                
            self.size_label.setText(f"{w} × {h}")
            self.type_label.setText(type_str)
            self.range_label.setText(f"{image.min():.3f} - {image.max():.3f}")
        else:
            self.size_label.setText("No image")
            self.type_label.setText("-")
            self.range_label.setText("-")

class AdvancedControls(QWidget):
    """
    Widget for advanced simulation controls and settings
    """
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        """Setup advanced controls"""
        layout = QVBoxLayout(self)
        
        # Analysis Options
        analysis_group = QGroupBox("Analysis Options")
        analysis_layout = QVBoxLayout(analysis_group)
        
        self.show_psf_contours = QCheckBox("Show PSF Contours")
        self.show_psf_contours.setChecked(True)
        analysis_layout.addWidget(self.show_psf_contours)
        
        self.calc_encircled_energy = QCheckBox("Calculate Encircled Energy")
        self.calc_encircled_energy.setChecked(True)
        analysis_layout.addWidget(self.calc_encircled_energy)
        
        self.show_cross_sections = QCheckBox("Show PSF Cross-sections")
        self.show_cross_sections.setChecked(True)
        analysis_layout.addWidget(self.show_cross_sections)
        
        layout.addWidget(analysis_group)
        
        # Display Options
        display_group = QGroupBox("Display Options")
        display_layout = QGridLayout(display_group)
        
        # Colormap selection
        display_layout.addWidget(QLabel("Colormap:"), 0, 0)
        self.colormap_combo = QComboBox()
        self.colormap_combo.addItems([
            "gray", "hot", "jet", "viridis", "plasma", "inferno"
        ])
        self.colormap_combo.setCurrentText("hot")
        display_layout.addWidget(self.colormap_combo, 0, 1)
        
        # Log scale
        self.log_scale_check = QCheckBox("Log Scale for PSF")
        display_layout.addWidget(self.log_scale_check, 1, 0, 1, 2)
        
        layout.addWidget(display_group)
        
        # Export Options
        export_group = QGroupBox("Export Options")
        export_layout = QVBoxLayout(export_group)
        
        self.high_res_export = QCheckBox("High Resolution Export")
        self.high_res_export.setChecked(True)
        export_layout.addWidget(self.high_res_export)
        
        self.include_metadata = QCheckBox("Include Metadata")
        self.include_metadata.setChecked(True)
        export_layout.addWidget(self.include_metadata)
        
        layout.addWidget(export_group)