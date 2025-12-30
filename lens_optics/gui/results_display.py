"""
Results Display Components for Lens Simulation
Handles display of simulation results, plots, and analysis
"""

import numpy as np
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
                            QSplitter, QLabel, QGroupBox, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class ResultsDisplay:
    """Manages display of simulation results across multiple tabs"""

    def __init__(self, plotter):
        self.plotter = plotter
        self.setup_tabs()
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

    def _create_compact_metrics(self, title, labels_values):
        """Create a compact horizontal metrics bar"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 4px;
            }
        """)
        frame.setMaximumHeight(50)

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(20)

        # Title
        title_label = QLabel(f"<b>{title}:</b>")
        title_label.setStyleSheet("font-size: 9pt; color: #495057;")
        layout.addWidget(title_label)

        # Metrics
        for label, value_label in labels_values:
            metric = QLabel(f"{label}: ")
            metric.setStyleSheet("font-size: 8pt; color: #6c757d;")
            value_label.setStyleSheet("font-size: 8pt; font-weight: bold; color: #212529;")
            layout.addWidget(metric)
            layout.addWidget(value_label)

        layout.addStretch()
        return frame

    def setup_image_tab(self):
        """Setup image comparison tab"""
        self.image_tab = QWidget()
        layout = QVBoxLayout(self.image_tab)
        layout.setSpacing(4)

        # Canvas takes most space
        self.image_fig, self.image_canvas = self.plotter.create_figure_canvas()
        layout.addWidget(self.image_canvas, stretch=1)

        # Compact metrics bar
        self.mse_label = QLabel("-")
        self.psnr_label = QLabel("-")
        self.ssim_label = QLabel("-")
        self.contrast_label = QLabel("-")

        metrics = self._create_compact_metrics("Quality", [
            ("MSE", self.mse_label),
            ("PSNR", self.psnr_label),
            ("SSIM", self.ssim_label),
            ("Contrast", self.contrast_label)
        ])
        layout.addWidget(metrics)

    def setup_psf_tab(self):
        """Setup PSF analysis tab"""
        self.psf_tab = QWidget()
        layout = QVBoxLayout(self.psf_tab)
        layout.setSpacing(4)

        # Splitter for PSF views
        splitter = QSplitter(Qt.Vertical)
        layout.addWidget(splitter, stretch=1)

        # 2D PSF view
        self.psf_fig, self.psf_canvas = self.plotter.create_figure_canvas()
        splitter.addWidget(self.psf_canvas)

        # Cross-section views
        self.psf_cross_fig, self.psf_cross_canvas = self.plotter.create_figure_canvas()
        splitter.addWidget(self.psf_cross_canvas)

        # Encircled energy plot
        self.psf_ee_fig, self.psf_ee_canvas = self.plotter.create_figure_canvas()
        splitter.addWidget(self.psf_ee_canvas)

        # Compact metrics bar
        self.fwhm_label = QLabel("-")
        self.ee50_label = QLabel("-")
        self.ee80_label = QLabel("-")
        self.peak_label = QLabel("-")

        metrics = self._create_compact_metrics("PSF", [
            ("FWHM (μm)", self.fwhm_label),
            ("EE50 (μm)", self.ee50_label),
            ("EE80 (μm)", self.ee80_label),
            ("Peak", self.peak_label)
        ])
        layout.addWidget(metrics)

    def setup_analysis_tab(self):
        """Setup detailed analysis tab"""
        self.analysis_tab = QWidget()
        layout = QVBoxLayout(self.analysis_tab)
        layout.setSpacing(4)

        # Analysis plots
        self.analysis_fig, self.analysis_canvas = self.plotter.create_figure_canvas()
        layout.addWidget(self.analysis_canvas, stretch=1)

        # Compact text output
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        self.analysis_text.setMaximumHeight(80)
        self.analysis_text.setFont(QFont("Courier", 8))
        self.analysis_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.analysis_text)

    def setup_lens_tab(self):
        """Setup lens diagram tab"""
        self.lens_tab = QWidget()
        layout = QVBoxLayout(self.lens_tab)
        layout.setSpacing(4)

        # Lens diagram
        self.lens_fig, self.lens_canvas = self.plotter.create_figure_canvas()
        layout.addWidget(self.lens_canvas, stretch=1)

        # Compact parameters bar
        self.diameter_label = QLabel("-")
        self.focal_length_label = QLabel("-")
        self.f_number_label = QLabel("-")
        self.numerical_aperture_label = QLabel("-")
        self.airy_disk_label = QLabel("-")

        metrics = self._create_compact_metrics("Lens", [
            ("D", self.diameter_label),
            ("f", self.focal_length_label),
            ("F/#", self.f_number_label),
            ("NA", self.numerical_aperture_label),
            ("Airy", self.airy_disk_label)
        ])
        layout.addWidget(metrics)

    def update_original_image(self, image):
        """Update the original image display"""
        self.current_image = image
        if image is not None:
            self.plotter.plot_image_comparison(
                self.image_fig, image, image,
                titles=['Original Image', 'Original Image']
            )
            self.image_canvas.draw()

    def update_results(self, original_image, blurred_image, psf, extent,
                      psf_metrics, quality_metrics, parameters):
        """Update all displays with new results"""
        self.current_image = original_image
        self.current_blurred = blurred_image
        self.current_psf = psf
        self.current_extent = extent

        self.update_image_display(original_image, blurred_image, quality_metrics)
        self.update_psf_display(psf, extent, psf_metrics, parameters)
        self.update_analysis_display(quality_metrics, psf_metrics, parameters)
        self.update_lens_display(parameters)

    def update_image_display(self, original, blurred, quality_metrics):
        """Update image comparison display"""
        self.plotter.plot_image_comparison(
            self.image_fig, original, blurred,
            titles=['Original Image', 'Blurred Image']
        )
        self.image_canvas.draw()

        if 'mse' in quality_metrics:
            self.mse_label.setText(f"{quality_metrics['mse']:.4f}")
        if 'psnr' in quality_metrics:
            psnr_val = quality_metrics['psnr']
            self.psnr_label.setText(f"{psnr_val:.1f} dB" if np.isfinite(psnr_val) else "∞")
        if 'ssim' in quality_metrics:
            self.ssim_label.setText(f"{quality_metrics['ssim']:.3f}")
        if 'contrast_reduction' in quality_metrics:
            self.contrast_label.setText(f"{quality_metrics['contrast_reduction']*100:.1f}%")

    def update_psf_display(self, psf, extent, psf_metrics, parameters):
        """Update PSF visualization displays"""
        pixel_size_um = parameters['pixel_size'] * 1e6

        self.plotter.plot_psf_comparison(
            self.psf_fig, [psf], ['Point Spread Function'], extent
        )
        self.psf_canvas.draw()

        self.plotter.plot_psf_cross_section(
            self.psf_cross_fig, psf, extent, pixel_size_um
        )
        self.psf_cross_canvas.draw()

        self.plotter.plot_encircled_energy(
            self.psf_ee_fig, psf, pixel_size_um
        )
        self.psf_ee_canvas.draw()

        if 'fwhm_um' in psf_metrics:
            self.fwhm_label.setText(f"{psf_metrics['fwhm_um']:.2f}")
        if 'ee50_radius_um' in psf_metrics:
            self.ee50_label.setText(f"{psf_metrics['ee50_radius_um']:.2f}")
        if 'ee80_radius_um' in psf_metrics:
            self.ee80_label.setText(f"{psf_metrics['ee80_radius_um']:.2f}")
        if 'peak_intensity' in psf_metrics:
            self.peak_label.setText(f"{psf_metrics['peak_intensity']:.3f}")

    def update_analysis_display(self, quality_metrics, psf_metrics, parameters):
        """Update analysis display"""
        self.plotter.plot_analysis_summary(
            self.analysis_fig, quality_metrics, psf_metrics, parameters
        )
        self.analysis_canvas.draw()

        text = self.generate_analysis_text(quality_metrics, psf_metrics, parameters)
        self.analysis_text.setText(text)

    def update_lens_display(self, parameters):
        """Update lens diagram and parameters"""
        self.plotter.plot_lens_diagram(self.lens_fig, parameters)
        self.lens_canvas.draw()

        diameter_mm = parameters['diameter'] * 1000
        focal_length_mm = parameters['focal_length'] * 1000
        f_number = parameters['focal_length'] / parameters['diameter']
        numerical_aperture = parameters['diameter'] / (2 * parameters['focal_length'])
        airy_radius_um = 1.22 * parameters['wavelength'] * parameters['focal_length'] / parameters['diameter'] * 1e6

        self.diameter_label.setText(f"{diameter_mm:.1f}mm")
        self.focal_length_label.setText(f"{focal_length_mm:.0f}mm")
        self.f_number_label.setText(f"f/{f_number:.1f}")
        self.numerical_aperture_label.setText(f"{numerical_aperture:.3f}")
        self.airy_disk_label.setText(f"{airy_radius_um:.1f}μm")

    def generate_analysis_text(self, quality_metrics, psf_metrics, parameters):
        """Generate compact analysis text"""
        parts = []

        # Lens config
        parts.append(f"Lens: D={parameters['diameter']*1000:.1f}mm, f={parameters['focal_length']*1000:.0f}mm, F/{parameters['focal_length']/parameters['diameter']:.1f}")

        # PSF info
        if 'fwhm_um' in psf_metrics:
            parts.append(f"PSF FWHM: {psf_metrics['fwhm_um']:.2f}μm")

        # Quality
        if 'ssim' in quality_metrics:
            qual = "Excellent" if quality_metrics['ssim'] > 0.9 else "Good" if quality_metrics['ssim'] > 0.7 else "Degraded"
            parts.append(f"Quality: {qual} (SSIM={quality_metrics['ssim']:.3f})")

        # Diffraction check
        airy_radius_um = 1.22 * parameters['wavelength'] * parameters['focal_length'] / parameters['diameter'] * 1e6
        if 'fwhm_um' in psf_metrics:
            limited = "Diffraction-limited" if psf_metrics['fwhm_um'] <= airy_radius_um * 2 else "Seeing-limited"
            parts.append(limited)

        return " | ".join(parts)
