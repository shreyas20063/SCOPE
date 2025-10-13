"""
Results Display Components for Fourier Analysis
Handles display of analysis results, plots, and metrics
"""

import numpy as np
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel,
                            QGroupBox, QGridLayout)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class ResultsDisplay:
    """
    Manages display of Fourier analysis results across multiple tabs
    """

    def __init__(self, plotter):
        """
        Initialize results display

        Args:
            plotter: FourierPlotter instance for creating plots
        """
        self.plotter = plotter
        self.setup_tabs()

        # Store current data
        self.current_img1 = None
        self.current_img2 = None
        self.current_img1_display = None
        self.current_img2_display = None
        self.current_results = {}

    def setup_tabs(self):
        """Setup all display tabs"""
        self.setup_image1_tab()
        self.setup_image2_tab()
        self.setup_comparison_tab()

        # Store image names for dynamic labeling
        self.img1_name = "Image 1"
        self.img2_name = "Image 2"

    def setup_image1_tab(self):
        """Setup Image 1 analysis tab"""
        self.image1_tab = QWidget()
        layout = QVBoxLayout(self.image1_tab)

        # Create matplotlib figure and canvas
        self.img1_fig, self.img1_canvas = self.plotter.create_figure_canvas()
        layout.addWidget(self.img1_canvas)

        # Metrics display
        metrics_group = QGroupBox("Image 1 Quality Metrics")
        metrics_layout = QGridLayout(metrics_group)

        self.img1_mse_label = QLabel("MSE: -")
        self.img1_corr_label = QLabel("Correlation: -")
        self.img1_ssim_label = QLabel("SSIM: -")

        metrics_layout.addWidget(QLabel("Mean Squared Error:"), 0, 0)
        metrics_layout.addWidget(self.img1_mse_label, 0, 1)
        metrics_layout.addWidget(QLabel("Correlation:"), 1, 0)
        metrics_layout.addWidget(self.img1_corr_label, 1, 1)
        metrics_layout.addWidget(QLabel("SSIM:"), 2, 0)
        metrics_layout.addWidget(self.img1_ssim_label, 2, 1)

        layout.addWidget(metrics_group)

    def setup_image2_tab(self):
        """Setup Image 2 analysis tab"""
        self.image2_tab = QWidget()
        layout = QVBoxLayout(self.image2_tab)

        # Create matplotlib figure and canvas
        self.img2_fig, self.img2_canvas = self.plotter.create_figure_canvas()
        layout.addWidget(self.img2_canvas)

        # Metrics display
        metrics_group = QGroupBox("Image 2 Quality Metrics")
        metrics_layout = QGridLayout(metrics_group)

        self.img2_mse_label = QLabel("MSE: -")
        self.img2_corr_label = QLabel("Correlation: -")
        self.img2_ssim_label = QLabel("SSIM: -")

        metrics_layout.addWidget(QLabel("Mean Squared Error:"), 0, 0)
        metrics_layout.addWidget(self.img2_mse_label, 0, 1)
        metrics_layout.addWidget(QLabel("Correlation:"), 1, 0)
        metrics_layout.addWidget(self.img2_corr_label, 1, 1)
        metrics_layout.addWidget(QLabel("SSIM:"), 2, 0)
        metrics_layout.addWidget(self.img2_ssim_label, 2, 1)

        layout.addWidget(metrics_group)

    def setup_comparison_tab(self):
        """Setup comparison tab for hybrid images"""
        self.comparison_tab = QWidget()
        layout = QVBoxLayout(self.comparison_tab)

        # Create matplotlib figure and canvas
        self.comp_fig, self.comp_canvas = self.plotter.create_figure_canvas()
        layout.addWidget(self.comp_canvas)

        # Comparison metrics
        comp_group = QGroupBox("Hybrid Image Analysis")
        comp_layout = QGridLayout(comp_group)

        self.hybrid1_corr_label = QLabel("Hybrid 1 → Image 2: -")
        self.hybrid2_corr_label = QLabel("Hybrid 2 → Image 1: -")

        comp_layout.addWidget(QLabel("Correlations:"), 0, 0, 1, 2)
        comp_layout.addWidget(self.hybrid1_corr_label, 1, 0, 1, 2)
        comp_layout.addWidget(self.hybrid2_corr_label, 2, 0, 1, 2)

        # Explanation
        explanation = QLabel(
            "Hybrid images demonstrate phase importance:\n"
            "• Mag1 + Phase2 looks like Image 2\n"
            "• Mag2 + Phase1 looks like Image 1\n"
            "This proves phase carries structural information!"
        )
        explanation.setWordWrap(True)
        explanation.setStyleSheet(
            "QLabel { background-color: #e8f4f8; color: #000000; padding: 10px; border-radius: 5px; }"
        )
        comp_layout.addWidget(explanation, 3, 0, 1, 2)

        layout.addWidget(comp_group)

    def update_results(self, img1, img2, results,
                       img1_name="Image 1", img2_name="Image 2",
                       img1_display=None, img2_display=None):
        """
        Update all displays with new results

        Args:
            img1: Image 1
            img2: Image 2
            results: Dictionary containing all analysis results
            img1_name: Name for image 1 (for labels)
            img2_name: Name for image 2 (for labels)
            img1_display: Display image for image 1 (optional)
            img2_display: Display image for image 2 (optional)
        """
        self.current_img1 = img1
        self.current_img2 = img2
        self.current_results = results
        self.img1_name = img1_name
        self.img2_name = img2_name
        self.current_img1_display = self._ensure_display_image(
            img1_display if img1_display is not None else img1
        )
        self.current_img2_display = self._ensure_display_image(
            img2_display if img2_display is not None else img2
        )

        # Update Image 1 display
        self.update_image1_display(img1, results)

        # Update Image 2 display
        self.update_image2_display(img2, results)

        # Update comparison display
        self.update_comparison_display(img1, img2, results)

    def update_image1_display(self, img1, results):
        """Update Image 1 analysis display"""
        # Get data
        mag1 = results['mag1_display']
        phase1 = results['phase1_display']
        recon1 = results['img1_recon']
        original_display = self.current_img1_display if self.current_img1_display is not None else img1

        # Plot with original image
        self.plotter.plot_fourier_components(
            self.img1_fig, original_display, mag1, phase1, recon1, '',
            magnitude_ref=results['mag1_orig']
        )
        self.img1_canvas.draw()

        # Update metrics
        quality1 = results['quality1']
        self.img1_mse_label.setText(f"{quality1['mse']:.6f}")
        self.img1_corr_label.setText(f"{quality1['correlation']:.4f}")
        self.img1_ssim_label.setText(f"{quality1['ssim']:.4f}")

    def update_image2_display(self, img2, results):
        """Update Image 2 analysis display"""
        # Get data
        mag2 = results['mag2_display']
        phase2 = results['phase2_display']
        recon2 = results['img2_recon']
        original_display = self.current_img2_display if self.current_img2_display is not None else img2

        # Plot with original image
        self.plotter.plot_fourier_components(
            self.img2_fig, original_display, mag2, phase2, recon2, '',
            magnitude_ref=results['mag2_orig']
        )
        self.img2_canvas.draw()

        # Update metrics
        quality2 = results['quality2']
        self.img2_mse_label.setText(f"{quality2['mse']:.6f}")
        self.img2_corr_label.setText(f"{quality2['correlation']:.4f}")
        self.img2_ssim_label.setText(f"{quality2['ssim']:.4f}")

    def update_comparison_display(self, img1, img2, results):
        """Update comparison display"""
        # Get hybrid images
        hybrid1 = results['hybrid_mag1_phase2']
        hybrid2 = results['hybrid_mag2_phase1']
        display_img1 = self.current_img1_display if self.current_img1_display is not None else img1
        display_img2 = self.current_img2_display if self.current_img2_display is not None else img2

        # Plot comparison with dynamic names
        self.plotter.plot_hybrid_comparison(
            self.comp_fig, display_img1, display_img2, hybrid1, hybrid2,
            self.img1_name, self.img2_name
        )
        self.comp_canvas.draw()

        # Calculate correlations
        corr1 = abs(np.corrcoef(hybrid1.flatten(), img2.flatten())[0, 1])
        corr2 = abs(np.corrcoef(hybrid2.flatten(), img1.flatten())[0, 1])

        self.hybrid1_corr_label.setText(f"Hybrid 1 → {self.img2_name}: {corr1:.4f}")
        self.hybrid2_corr_label.setText(f"Hybrid 2 → {self.img1_name}: {corr2:.4f}")

    def _ensure_display_image(self, image):
        """Guarantee an image is in a display-friendly RGB format"""
        if image is None:
            return None
        if image.ndim == 2:
            return np.repeat(image[..., np.newaxis], 3, axis=2)
        return image
