"""
Visualization and Plotting Module
Handles all plotting and visualization for the lens simulation
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.patches as patches
from mpl_toolkits.axes_grid1 import make_axes_locatable

class SimulationPlotter:
    """
    Handles plotting and visualization for lens simulation
    """

    def __init__(self, figsize=(10, 4), dpi=100):
        """
        Initialize plotter

        Args:
            figsize (tuple): Figure size in inches
            dpi (int): Figure DPI
        """
        self.figsize = figsize
        self.dpi = dpi
        plt.style.use('default')

    def create_figure_canvas(self):
        """Create matplotlib figure and canvas for embedding in Qt"""
        fig = Figure(figsize=self.figsize, dpi=self.dpi)
        fig.subplots_adjust(left=0.1, right=0.95, top=0.9, bottom=0.15)
        canvas = FigureCanvas(fig)
        return fig, canvas
    
    def plot_image_comparison(self, fig, original, blurred, titles=['Original', 'Blurred']):
        """
        Plot side-by-side image comparison
        
        Args:
            fig: Matplotlib figure object
            original: Original image array
            blurred: Blurred image array
            titles: List of titles for images
        """
        fig.clear()
        
        # Create subplots
        ax1 = fig.add_subplot(1, 2, 1)
        ax2 = fig.add_subplot(1, 2, 2)
        
        # Plot original image
        im1 = ax1.imshow(original, cmap='gray', vmin=0, vmax=1)
        ax1.set_title(titles[0], fontsize=10)
        ax1.set_xlabel('Pixels', fontsize=9)
        ax1.set_ylabel('Pixels', fontsize=9)
        ax1.tick_params(labelsize=8)

        # Add colorbar
        divider1 = make_axes_locatable(ax1)
        cax1 = divider1.append_axes("right", size="5%", pad=0.05)
        cbar1 = fig.colorbar(im1, cax=cax1)
        cbar1.ax.tick_params(labelsize=7)

        # Plot blurred image
        im2 = ax2.imshow(blurred, cmap='gray', vmin=0, vmax=1)
        ax2.set_title(titles[1], fontsize=10)
        ax2.set_xlabel('Pixels', fontsize=9)
        ax2.set_ylabel('Pixels', fontsize=9)
        ax2.tick_params(labelsize=8)

        # Add colorbar
        divider2 = make_axes_locatable(ax2)
        cax2 = divider2.append_axes("right", size="5%", pad=0.05)
        cbar2 = fig.colorbar(im2, cax=cax2)
        cbar2.ax.tick_params(labelsize=7)

        fig.tight_layout(pad=1.5)
    
    def plot_psf_comparison(self, fig, psf_data_list, titles, extent=None):
        """
        Plot comparison of multiple PSFs
        
        Args:
            fig: Matplotlib figure object
            psf_data_list: List of PSF arrays
            titles: List of titles for each PSF
            extent: Coordinate extent for plotting
        """
        fig.clear()
        n_psfs = len(psf_data_list)
        
        if n_psfs == 1:
            rows, cols = 1, 1
        elif n_psfs == 2:
            rows, cols = 1, 2
        elif n_psfs <= 4:
            rows, cols = 2, 2
        else:
            rows, cols = 2, 3
        
        for i, (psf, title) in enumerate(zip(psf_data_list, titles)):
            ax = fig.add_subplot(rows, cols, i + 1)

            if extent is not None:
                im = ax.imshow(psf, cmap='hot', extent=extent, origin='lower')
                ax.set_xlabel('X (μm)', fontsize=9)
                ax.set_ylabel('Y (μm)', fontsize=9)
            else:
                im = ax.imshow(psf, cmap='hot', origin='lower')
                ax.set_xlabel('Pixels', fontsize=9)
                ax.set_ylabel('Pixels', fontsize=9)

            ax.set_title(title, fontsize=10)
            ax.tick_params(labelsize=8)

            # Add colorbar
            divider = make_axes_locatable(ax)
            cax = divider.append_axes("right", size="5%", pad=0.05)
            cbar = fig.colorbar(im, cax=cax)
            cbar.ax.tick_params(labelsize=7)

        fig.tight_layout(pad=1.5)
    
    def plot_psf_cross_section(self, fig, psf, extent, pixel_size_um):
        """
        Plot PSF cross-sections through center
        
        Args:
            fig: Matplotlib figure object
            psf: PSF array
            extent: Coordinate extent
            pixel_size_um: Pixel size in micrometers
        """
        fig.clear()
        
        # Find PSF center
        center_y, center_x = np.unravel_index(np.argmax(psf), psf.shape)
        
        # Get profiles
        h_profile = psf[center_y, :]
        v_profile = psf[:, center_x]
        
        # Create position arrays
        if extent is not None:
            x_pos = np.linspace(extent[0], extent[1], psf.shape[1])
            y_pos = np.linspace(extent[2], extent[3], psf.shape[0])
        else:
            x_pos = np.arange(psf.shape[1]) * pixel_size_um
            y_pos = np.arange(psf.shape[0]) * pixel_size_um
            x_pos = x_pos - x_pos[center_x]
            y_pos = y_pos - y_pos[center_y]
        
        # Plot horizontal and vertical profiles side by side
        ax1 = fig.add_subplot(1, 2, 1)
        ax1.plot(x_pos, h_profile, 'b-', linewidth=2, label='H')
        ax1.axhline(y=np.max(h_profile)/2, color='r', linestyle='--', alpha=0.7, label='FWHM')
        ax1.set_xlabel('Position (μm)', fontsize=9)
        ax1.set_ylabel('Intensity', fontsize=9)
        ax1.set_title('Horizontal', fontsize=10)
        ax1.grid(True, alpha=0.3)
        ax1.legend(fontsize=8)
        ax1.tick_params(labelsize=8)

        ax2 = fig.add_subplot(1, 2, 2)
        ax2.plot(y_pos, v_profile, 'g-', linewidth=2, label='V')
        ax2.axhline(y=np.max(v_profile)/2, color='r', linestyle='--', alpha=0.7, label='FWHM')
        ax2.set_xlabel('Position (μm)', fontsize=9)
        ax2.set_ylabel('Intensity', fontsize=9)
        ax2.set_title('Vertical', fontsize=10)
        ax2.grid(True, alpha=0.3)
        ax2.legend(fontsize=8)
        ax2.tick_params(labelsize=8)

        fig.tight_layout(pad=1.5)
    
    def plot_encircled_energy(self, fig, psf, pixel_size_um):
        """
        Plot encircled energy curve
        
        Args:
            fig: Matplotlib figure object
            psf: PSF array
            pixel_size_um: Pixel size in micrometers
        """
        fig.clear()
        
        # Calculate encircled energy
        center_y, center_x = np.unravel_index(np.argmax(psf), psf.shape)
        total_energy = np.sum(psf)
        
        # Create distance array from center
        y, x = np.ogrid[:psf.shape[0], :psf.shape[1]]
        distances = np.sqrt((x - center_x)**2 + (y - center_y)**2)
        
        # Calculate cumulative energy
        max_radius = min(center_x, center_y, psf.shape[1] - center_x, psf.shape[0] - center_y)
        radii = np.arange(1, max_radius + 1)
        
        encircled_energies = []
        for r in radii:
            mask = distances <= r
            energy = np.sum(psf[mask])
            encircled_energies.append(energy / total_energy)
        
        # Convert radii to micrometers
        radii_um = radii * pixel_size_um
        
        # Plot encircled energy
        ax = fig.add_subplot(1, 1, 1)
        ax.plot(radii_um, encircled_energies, 'b-', linewidth=2)
        ax.axhline(y=0.5, color='r', linestyle='--', alpha=0.7, label='50% EE')
        ax.axhline(y=0.8, color='orange', linestyle='--', alpha=0.7, label='80% EE')
        ax.set_xlabel('Radius (μm)', fontsize=9)
        ax.set_ylabel('Encircled Energy', fontsize=9)
        ax.set_title('Encircled Energy', fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)
        ax.set_ylim(0, 1)
        ax.tick_params(labelsize=8)

        fig.tight_layout(pad=1.5)
    
    def plot_analysis_summary(self, fig, quality_metrics, psf_metrics, parameters):
        """
        Plot comprehensive analysis summary
        
        Args:
            fig: Matplotlib figure object
            quality_metrics: Image quality metrics
            psf_metrics: PSF metrics
            parameters: Simulation parameters
        """
        fig.clear()
        
        # Create subplots for different analyses
        ax1 = fig.add_subplot(2, 2, 1)
        ax2 = fig.add_subplot(2, 2, 2)
        ax3 = fig.add_subplot(2, 2, 3)
        ax4 = fig.add_subplot(2, 2, 4)
        
        # Plot 1: Quality metrics comparison
        metrics_names = []
        metrics_values = []
        
        if 'ssim' in quality_metrics:
            metrics_names.append('SSIM')
            metrics_values.append(quality_metrics['ssim'])
        
        if 'contrast_reduction' in quality_metrics:
            metrics_names.append('Contrast\nPreservation')
            metrics_values.append(1 - quality_metrics['contrast_reduction'])
        
        if 'strehl_ratio' in psf_metrics:
            metrics_names.append('Strehl\nRatio')
            metrics_values.append(psf_metrics['strehl_ratio'])
        
        if metrics_names:
            bars = ax1.bar(metrics_names, metrics_values, color=['blue', 'green', 'orange'])
            ax1.set_ylabel('Quality Score')
            ax1.set_title('Quality Metrics')
            ax1.set_ylim(0, 1)
            ax1.grid(True, alpha=0.3)
            
            # Add value labels on bars
            for bar, value in zip(bars, metrics_values):
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                        f'{value:.3f}', ha='center', va='bottom')
        
        # Plot 2: PSF size comparison
        if 'fwhm_um' in psf_metrics:
            # Calculate theoretical diffraction limit
            airy_radius_um = 1.22 * parameters['wavelength'] * parameters['focal_length'] / parameters['diameter'] * 1e6
            diffraction_fwhm = airy_radius_um * 2  # Approximate FWHM
            
            actual_fwhm = psf_metrics['fwhm_um']
            
            ax2.bar(['Diffraction\nLimit', 'Actual\nFWHM'], 
                   [diffraction_fwhm, actual_fwhm],
                   color=['red', 'blue'])
            ax2.set_ylabel('FWHM (μm)')
            ax2.set_title('PSF Size Comparison')
            ax2.grid(True, alpha=0.3)
        
        # Plot 3: Encircled energy radii
        if 'ee50_radius_um' in psf_metrics and 'ee80_radius_um' in psf_metrics:
            ee_radii = [psf_metrics['ee50_radius_um'], psf_metrics['ee80_radius_um']]
            ee_labels = ['50% EE', '80% EE']
            
            bars = ax3.bar(ee_labels, ee_radii, color=['cyan', 'magenta'])
            ax3.set_ylabel('Radius (μm)')
            ax3.set_title('Encircled Energy Radii')
            ax3.grid(True, alpha=0.3)
            
            # Add value labels
            for bar, value in zip(bars, ee_radii):
                height = bar.get_height()
                ax3.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                        f'{value:.2f}', ha='center', va='bottom')
        
        # Plot 4: System parameters
        diameter_mm = parameters['diameter'] * 1000
        focal_length_mm = parameters['focal_length'] * 1000
        f_number = parameters['focal_length'] / parameters['diameter']
        
        param_names = ['Diameter\n(mm)', 'Focal Length\n(mm)', 'F-number']
        param_values = [diameter_mm, focal_length_mm, f_number]
        
        bars = ax4.bar(param_names, param_values, color=['brown', 'purple', 'olive'])
        ax4.set_ylabel('Value')
        ax4.set_title('System Parameters')
        ax4.grid(True, alpha=0.3)
        
        # Add value labels
        for bar, value in zip(bars, param_values):
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                    f'{value:.1f}', ha='center', va='bottom', fontsize=8)

        # Reduce font sizes
        for ax in [ax1, ax2, ax3, ax4]:
            ax.tick_params(labelsize=8)
            ax.title.set_fontsize(10)
            ax.xaxis.label.set_fontsize(8)
            ax.yaxis.label.set_fontsize(8)

        fig.tight_layout(pad=1.5)
    
    def plot_lens_diagram(self, fig, parameters):
        """
        Plot lens diagram with ray tracing
        
        Args:
            fig: Matplotlib figure object
            parameters: Simulation parameters
        """
        fig.clear()
        ax = fig.add_subplot(1, 1, 1)
        
        # Lens parameters
        diameter = parameters['diameter'] * 1000  # Convert to mm
        focal_length = parameters['focal_length'] * 1000  # Convert to mm
        
        # Draw lens
        lens_x = 0
        lens_top = diameter / 2
        lens_bottom = -diameter / 2
        
        # Lens shape (simple biconvex)
        lens_curve = 0.1 * diameter  # Curvature
        
        # Left surface
        theta_left = np.linspace(-np.pi/2, np.pi/2, 100)
        x_left = lens_x - lens_curve + lens_curve * np.cos(theta_left)
        y_left = lens_curve * np.sin(theta_left) * (diameter / (2 * lens_curve))
        
        # Right surface
        theta_right = np.linspace(np.pi/2, 3*np.pi/2, 100)
        x_right = lens_x + lens_curve + lens_curve * np.cos(theta_right)
        y_right = lens_curve * np.sin(theta_right) * (diameter / (2 * lens_curve))
        
        # Plot lens
        ax.fill_between(x_left, y_left, alpha=0.3, color='lightblue', label='Lens')
        ax.fill_between(x_right, y_right, alpha=0.3, color='lightblue')
        ax.plot(x_left, y_left, 'b-', linewidth=2)
        ax.plot(x_right, y_right, 'b-', linewidth=2)
        
        # Draw optical axis
        ax.axhline(y=0, color='black', linestyle='-', alpha=0.5, linewidth=1)
        
        # Draw focal points
        ax.plot(focal_length, 0, 'ro', markersize=8, label='Focal Point')
        ax.plot(-focal_length, 0, 'ro', markersize=8)
        
        # Draw parallel rays
        ray_heights = np.linspace(-diameter/3, diameter/3, 5)
        for height in ray_heights:
            if height != 0:
                # Incoming parallel ray
                ax.plot([-focal_length*1.5, lens_x-lens_curve], [height, height], 'r-', alpha=0.7)
                
                # Outgoing ray to focal point
                ax.plot([lens_x+lens_curve, focal_length], [height, 0], 'r-', alpha=0.7)
        
        # Principal ray (through center)
        ax.plot([-focal_length*1.5, focal_length*1.5], [0, 0], 'g-', linewidth=2, alpha=0.7, label='Principal Ray')
        
        # Labels and formatting
        ax.set_xlabel('Distance (mm)')
        ax.set_ylabel('Height (mm)')
        ax.set_title(f'Lens Diagram (f={focal_length:.0f}mm, D={diameter:.1f}mm)')
        ax.grid(True, alpha=0.3)
        ax.legend()
        ax.set_aspect('equal')
        
        # Set limits
        margin = max(diameter, focal_length) * 0.2
        ax.set_xlim(-focal_length*1.5 - margin, focal_length*1.5 + margin)
        ax.set_ylim(-diameter/2 - margin, diameter/2 + margin)

        ax.tick_params(labelsize=8)
        ax.xaxis.label.set_fontsize(9)
        ax.yaxis.label.set_fontsize(9)
        ax.title.set_fontsize(10)

        fig.tight_layout(pad=1.5)
    
    def save_figure(self, fig, filename, dpi=300):
        """
        Save figure to file
        
        Args:
            fig: Matplotlib figure object
            filename: Output filename
            dpi: Resolution for saved figure
        """
        fig.savefig(filename, dpi=dpi, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')