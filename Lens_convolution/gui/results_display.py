"""
Results Display Components for Lens Simulation
Handles display of simulation results, plots, and analysis
"""

import numpy as np
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
                            QSplitter, QTabWidget, QScrollArea, QLabel,
                            QGroupBox, QGridLayout)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class ResultsDisplay:
    """
    Manages display of simulation results across multiple tabs
    """
    
    def __init__(self, plotter):
        """
        Initialize results display
        
        Args:
            plotter: SimulationPlotter instance for creating plots
        """
        self.plotter = plotter
        self.setup_tabs()
        
        # Store current data
        self.current_image = None
        self.current_blurred = None
        self.current_psf = None
        self.current_extent = None
        
    def setup_tabs(self):
        """Setup all display tabs"""
        self.setup_image_tab()
        self.setup_psf_tab()
        self.setup_analysis_tab()
        self.setup_lens_tab()
        
    def setup_image_tab(self):
        """Setup image comparison tab"""
        self.image_tab = QWidget()
        layout = QVBoxLayout(self.image_tab)
        
        # Create matplotlib figure and canvas
        self.image_fig, self.image_canvas = self.plotter.create_figure_canvas()
        layout.addWidget(self.image_canvas)
        
        # Image metrics display
        metrics_group = QGroupBox("Image Quality Metrics")
        metrics_layout = QGridLayout(metrics_group)
        
        self.mse_label = QLabel("MSE: -")
        self.psnr_label = QLabel("PSNR: -")
        self.ssim_label = QLabel("SSIM: -")
        self.contrast_label = QLabel("Contrast Reduction: -")
        
        metrics_layout.addWidget(QLabel("Mean Squared Error:"), 0, 0)
        metrics_layout.addWidget(self.mse_label, 0, 1)
        metrics_layout.addWidget(QLabel("Peak SNR (dB):"), 1, 0)
        metrics_layout.addWidget(self.psnr_label, 1, 1)
        metrics_layout.addWidget(QLabel("Structural Similarity:"), 2, 0)
        metrics_layout.addWidget(self.ssim_label, 2, 1)
        metrics_layout.addWidget(QLabel("Contrast Reduction:"), 3, 0)
        metrics_layout.addWidget(self.contrast_label, 3, 1)
        
        layout.addWidget(metrics_group)
        
    def setup_psf_tab(self):
        """Setup PSF analysis tab"""
        self.psf_tab = QWidget()
        layout = QVBoxLayout(self.psf_tab)
        
        # Create splitter for multiple PSF views
        splitter = QSplitter(Qt.Vertical)
        layout.addWidget(splitter)
        
        # 2D PSF view
        psf_widget = QWidget()
        psf_layout = QVBoxLayout(psf_widget)
        psf_layout.addWidget(QLabel("2D Point Spread Function"))
        self.psf_fig, self.psf_canvas = self.plotter.create_figure_canvas()
        psf_layout.addWidget(self.psf_canvas)
        splitter.addWidget(psf_widget)
        
        # Cross-section views
        cross_widget = QWidget()
        cross_layout = QVBoxLayout(cross_widget)
        cross_layout.addWidget(QLabel("PSF Cross-sections"))
        self.psf_cross_fig, self.psf_cross_canvas = self.plotter.create_figure_canvas()
        cross_layout.addWidget(self.psf_cross_canvas)
        splitter.addWidget(cross_widget)
        
        # Encircled energy plot
        ee_widget = QWidget()
        ee_layout = QVBoxLayout(ee_widget)
        ee_layout.addWidget(QLabel("Encircled Energy"))
        self.psf_ee_fig, self.psf_ee_canvas = self.plotter.create_figure_canvas()
        ee_layout.addWidget(self.psf_ee_canvas)
        splitter.addWidget(ee_widget)
        
        # PSF metrics display
        psf_metrics_group = QGroupBox("PSF Metrics")
        psf_metrics_layout = QGridLayout(psf_metrics_group)
        
        self.fwhm_label = QLabel("FWHM: -")
        self.ee50_label = QLabel("EE50: -")
        self.ee80_label = QLabel("EE80: -")
        self.peak_label = QLabel("Peak: -")
        
        psf_metrics_layout.addWidget(QLabel("FWHM (μm):"), 0, 0)
        psf_metrics_layout.addWidget(self.fwhm_label, 0, 1)
        psf_metrics_layout.addWidget(QLabel("50% EE Radius (μm):"), 1, 0)
        psf_metrics_layout.addWidget(self.ee50_label, 1, 1)
        psf_metrics_layout.addWidget(QLabel("80% EE Radius (μm):"), 2, 0)
        psf_metrics_layout.addWidget(self.ee80_label, 2, 1)
        psf_metrics_layout.addWidget(QLabel("Peak Intensity:"), 3, 0)
        psf_metrics_layout.addWidget(self.peak_label, 3, 1)
        
        layout.addWidget(psf_metrics_group)
        
    def setup_analysis_tab(self):
        """Setup detailed analysis tab"""
        self.analysis_tab = QWidget()
        layout = QVBoxLayout(self.analysis_tab)
        
        # Analysis plots
        self.analysis_fig, self.analysis_canvas = self.plotter.create_figure_canvas()
        layout.addWidget(self.analysis_canvas)
        
        # Analysis text output
        analysis_group = QGroupBox("Analysis Summary")
        analysis_layout = QVBoxLayout(analysis_group)
        
        self.analysis_text = QTextEdit()
        self.analysis_text.setMaximumHeight(150)
        self.analysis_text.setFont(QFont("Courier", 9))
        analysis_layout.addWidget(self.analysis_text)
        
        layout.addWidget(analysis_group)
        
    def setup_lens_tab(self):
        """Setup lens diagram tab"""
        self.lens_tab = QWidget()
        layout = QVBoxLayout(self.lens_tab)
        
        # Lens diagram
        self.lens_fig, self.lens_canvas = self.plotter.create_figure_canvas()
        layout.addWidget(self.lens_canvas)
        
        # Lens parameters display
        params_group = QGroupBox("Lens Parameters")
        params_layout = QGridLayout(params_group)
        
        self.diameter_label = QLabel("Diameter: -")
        self.focal_length_label = QLabel("Focal Length: -")
        self.f_number_label = QLabel("F-number: -")
        self.numerical_aperture_label = QLabel("NA: -")
        self.airy_disk_label = QLabel("Airy Disk: -")
        
        params_layout.addWidget(QLabel("Diameter:"), 0, 0)
        params_layout.addWidget(self.diameter_label, 0, 1)
        params_layout.addWidget(QLabel("Focal Length:"), 1, 0)
        params_layout.addWidget(self.focal_length_label, 1, 1)
        params_layout.addWidget(QLabel("F-number:"), 2, 0)
        params_layout.addWidget(self.f_number_label, 2, 1)
        params_layout.addWidget(QLabel("Numerical Aperture:"), 3, 0)
        params_layout.addWidget(self.numerical_aperture_label, 3, 1)
        params_layout.addWidget(QLabel("Airy Disk Radius:"), 4, 0)
        params_layout.addWidget(self.airy_disk_label, 4, 1)
        
        layout.addWidget(params_group)
        
    def update_original_image(self, image):
        """Update the original image display"""
        self.current_image = image
        if image is not None:
            # Show original image only
            self.plotter.plot_image_comparison(
                self.image_fig, image, image, 
                titles=['Original Image', 'Original Image']
            )
            self.image_canvas.draw()
    
    def update_results(self, original_image, blurred_image, psf, extent, 
                      psf_metrics, quality_metrics, parameters):
        """
        Update all displays with new results
        
        Args:
            original_image: Original input image
            blurred_image: Convolved (blurred) image
            psf: Point spread function
            extent: PSF coordinate extent
            psf_metrics: PSF quality metrics
            quality_metrics: Image quality metrics
            parameters: Simulation parameters
        """
        self.current_image = original_image
        self.current_blurred = blurred_image
        self.current_psf = psf
        self.current_extent = extent
        
        # Update image comparison
        self.update_image_display(original_image, blurred_image, quality_metrics)
        
        # Update PSF displays
        self.update_psf_display(psf, extent, psf_metrics, parameters)
        
        # Update analysis
        self.update_analysis_display(quality_metrics, psf_metrics, parameters)
        
        # Update lens diagram
        self.update_lens_display(parameters)
        
    def update_image_display(self, original, blurred, quality_metrics):
        """Update image comparison display"""
        # Plot image comparison
        self.plotter.plot_image_comparison(
            self.image_fig, original, blurred,
            titles=['Original Image', 'Blurred Image']
        )
        self.image_canvas.draw()
        
        # Update quality metrics
        if 'mse' in quality_metrics:
            self.mse_label.setText(f"{quality_metrics['mse']:.6f}")
        if 'psnr' in quality_metrics:
            psnr_val = quality_metrics['psnr']
            if np.isfinite(psnr_val):
                self.psnr_label.setText(f"{psnr_val:.2f} dB")
            else:
                self.psnr_label.setText("∞ dB")
        if 'ssim' in quality_metrics:
            self.ssim_label.setText(f"{quality_metrics['ssim']:.4f}")
        if 'contrast_reduction' in quality_metrics:
            contrast_val = quality_metrics['contrast_reduction'] * 100
            self.contrast_label.setText(f"{contrast_val:.1f}%")
    
    def update_psf_display(self, psf, extent, psf_metrics, parameters):
        """Update PSF visualization displays"""
        pixel_size_um = parameters['pixel_size'] * 1e6  # Convert to micrometers
        
        # 2D PSF view
        self.plotter.plot_psf_comparison(
            self.psf_fig, [psf], ['Point Spread Function'], extent
        )
        self.psf_canvas.draw()
        
        # Cross-sections
        self.plotter.plot_psf_cross_section(
            self.psf_cross_fig, psf, extent, pixel_size_um
        )
        self.psf_cross_canvas.draw()
        
        # Encircled energy
        self.plotter.plot_encircled_energy(
            self.psf_ee_fig, psf, pixel_size_um
        )
        self.psf_ee_canvas.draw()
        
        # Update PSF metrics display
        if 'fwhm_um' in psf_metrics:
            self.fwhm_label.setText(f"{psf_metrics['fwhm_um']:.2f}")
        if 'ee50_radius_um' in psf_metrics:
            self.ee50_label.setText(f"{psf_metrics['ee50_radius_um']:.2f}")
        if 'ee80_radius_um' in psf_metrics:
            self.ee80_label.setText(f"{psf_metrics['ee80_radius_um']:.2f}")
        if 'peak_intensity' in psf_metrics:
            self.peak_label.setText(f"{psf_metrics['peak_intensity']:.4f}")
    
    def update_analysis_display(self, quality_metrics, psf_metrics, parameters):
        """Update analysis display with comprehensive metrics"""
        # Create analysis plots
        self.plotter.plot_analysis_summary(
            self.analysis_fig, quality_metrics, psf_metrics, parameters
        )
        self.analysis_canvas.draw()
        
        # Generate analysis text
        analysis_text = self.generate_analysis_text(quality_metrics, psf_metrics, parameters)
        self.analysis_text.setText(analysis_text)
    
    def update_lens_display(self, parameters):
        """Update lens diagram and parameters"""
        # Create lens diagram
        self.plotter.plot_lens_diagram(self.lens_fig, parameters)
        self.lens_canvas.draw()
        
        # Update parameter displays
        diameter_mm = parameters['diameter'] * 1000
        focal_length_mm = parameters['focal_length'] * 1000
        
        self.diameter_label.setText(f"{diameter_mm:.1f} mm")
        self.focal_length_label.setText(f"{focal_length_mm:.1f} mm")
        
        # Calculate derived parameters
        f_number = parameters['focal_length'] / parameters['diameter']
        numerical_aperture = parameters['diameter'] / (2 * parameters['focal_length'])
        
        self.f_number_label.setText(f"f/{f_number:.1f}")
        self.numerical_aperture_label.setText(f"{numerical_aperture:.3f}")
        
        # Airy disk radius
        wavelength = parameters['wavelength']
        airy_radius_rad = 1.22 * wavelength / parameters['diameter']
        airy_radius_um = airy_radius_rad * parameters['focal_length'] * 1e6
        
        self.airy_disk_label.setText(f"{airy_radius_um:.2f} μm")
    
    def generate_analysis_text(self, quality_metrics, psf_metrics, parameters):
        """Generate comprehensive analysis text"""
        text = "SIMULATION ANALYSIS REPORT\n"
        text += "=" * 50 + "\n\n"
        
        # Lens configuration
        text += "LENS CONFIGURATION:\n"
        text += f"  Diameter: {parameters['diameter']*1000:.1f} mm\n"
        text += f"  Focal Length: {parameters['focal_length']*1000:.1f} mm\n"
        text += f"  F-number: f/{parameters['focal_length']/parameters['diameter']:.1f}\n"
        text += f"  Wavelength: {parameters['wavelength']*1e9:.0f} nm\n"
        
        if parameters.get('atmospheric_seeing'):
            text += f"  Atmospheric Seeing: {parameters['atmospheric_seeing']:.2f} arcsec\n"
        
        text += "\n"
        
        # PSF Analysis
        text += "POINT SPREAD FUNCTION:\n"
        if 'fwhm_um' in psf_metrics:
            text += f"  FWHM: {psf_metrics['fwhm_um']:.2f} μm\n"
        if 'ee50_radius_um' in psf_metrics:
            text += f"  50% Encircled Energy: {psf_metrics['ee50_radius_um']:.2f} μm radius\n"
        if 'ee80_radius_um' in psf_metrics:
            text += f"  80% Encircled Energy: {psf_metrics['ee80_radius_um']:.2f} μm radius\n"
        if 'strehl_ratio' in psf_metrics:
            text += f"  Strehl Ratio: {psf_metrics['strehl_ratio']:.3f}\n"
        
        text += "\n"
        
        # Image Quality
        text += "IMAGE QUALITY METRICS:\n"
        if 'mse' in quality_metrics:
            text += f"  Mean Squared Error: {quality_metrics['mse']:.6f}\n"
        if 'psnr' in quality_metrics:
            if np.isfinite(quality_metrics['psnr']):
                text += f"  Peak SNR: {quality_metrics['psnr']:.2f} dB\n"
            else:
                text += f"  Peak SNR: ∞ dB\n"
        if 'ssim' in quality_metrics:
            text += f"  Structural Similarity: {quality_metrics['ssim']:.4f}\n"
        if 'contrast_reduction' in quality_metrics:
            text += f"  Contrast Reduction: {quality_metrics['contrast_reduction']*100:.1f}%\n"
        
        text += "\n"
        
        # Performance assessment
        text += "PERFORMANCE ASSESSMENT:\n"
        
        # Diffraction limit check
        airy_radius_um = 1.22 * parameters['wavelength'] * parameters['focal_length'] / parameters['diameter'] * 1e6
        if 'fwhm_um' in psf_metrics:
            if psf_metrics['fwhm_um'] <= airy_radius_um * 2:
                text += "  • Diffraction-limited performance\n"
            else:
                text += "  • Seeing-limited performance\n"
        
        # Image quality assessment
        if 'ssim' in quality_metrics:
            if quality_metrics['ssim'] > 0.9:
                text += "  • Excellent image quality preservation\n"
            elif quality_metrics['ssim'] > 0.7:
                text += "  • Good image quality preservation\n"
            else:
                text += "  • Significant image degradation\n"
        
        return text