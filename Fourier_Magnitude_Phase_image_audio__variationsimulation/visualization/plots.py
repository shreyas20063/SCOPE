"""
Plotting and Visualization Module
Handles creation of all plots for Fourier analysis
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class FourierPlotter:
    """
    Creates visualizations for Fourier analysis
    """

    def __init__(self):
        """Initialize plotter"""
        # Set default matplotlib style
        plt.style.use('default')
        self.default_figsize = (12, 8)
        self.default_dpi = 100

    def create_figure_canvas(self, figsize=None, dpi=None):
        """
        Create matplotlib figure and Qt canvas

        Args:
            figsize: Figure size (width, height) in inches
            dpi: Dots per inch

        Returns:
            tuple: (figure, canvas)
        """
        if figsize is None:
            figsize = self.default_figsize
        if dpi is None:
            dpi = self.default_dpi

        fig = Figure(figsize=figsize, dpi=dpi)
        canvas = FigureCanvas(fig)

        return fig, canvas

    def plot_image_comparison(self, fig, images, titles):
        """
        Plot multiple images side by side

        Args:
            fig: Matplotlib figure
            images: List of images to display
            titles: List of titles for each image
        """
        fig.clear()
        n_images = len(images)

        for i, (img, title) in enumerate(zip(images, titles)):
            ax = fig.add_subplot(1, n_images, i+1)
            ax.imshow(img, cmap='gray', vmin=0, vmax=1)
            ax.set_title(title, fontsize=10, fontweight='bold')
            ax.axis('off')

        fig.tight_layout()

    def plot_fourier_components(self, fig, original_img, magnitude, phase, image_recon,
                                 title_prefix='', magnitude_ref=None):
        """
        Plot original image, magnitude, phase, and reconstructed image

        Args:
            fig: Matplotlib figure
            original_img: Original input image
            magnitude: Magnitude spectrum
            phase: Phase spectrum
            image_recon: Reconstructed image
            title_prefix: Prefix for titles
        """
        fig.clear()

        # Original Image
        ax0 = fig.add_subplot(2, 2, 1)
        if original_img.ndim == 2:
            ax0.imshow(original_img, cmap='gray', vmin=0, vmax=1)
        else:
            ax0.imshow(np.clip(original_img, 0.0, 1.0))
        ax0.set_title(f'{title_prefix}Original', fontsize=10, fontweight='bold')
        ax0.axis('off')

        # Magnitude (log scale for better visualization)
        ax1 = fig.add_subplot(2, 2, 2)
        mag_log = np.log10(np.maximum(magnitude, 1e-8))
        ref_log = mag_log if magnitude_ref is None else np.log10(np.maximum(magnitude_ref, 1e-8))
        vmin = ref_log.min()
        vmax = ref_log.max()
        if np.isclose(vmin, vmax):
            vmin -= 1.0
            vmax += 1.0
        im1 = ax1.imshow(mag_log, cmap='hot', vmin=vmin, vmax=vmax)
        ax1.set_title(f'{title_prefix}Magnitude (Log)', fontsize=10, fontweight='bold')
        ax1.axis('off')
        fig.colorbar(im1, ax=ax1, fraction=0.046, pad=0.04)

        # Phase
        ax2 = fig.add_subplot(2, 2, 3)
        im2 = ax2.imshow(phase, cmap='twilight', vmin=-np.pi, vmax=np.pi)
        ax2.set_title(f'{title_prefix}Phase', fontsize=10, fontweight='bold')
        ax2.axis('off')
        fig.colorbar(im2, ax=ax2, fraction=0.046, pad=0.04)

        # Reconstructed image
        ax3 = fig.add_subplot(2, 2, 4)
        if original_img.ndim == 2:
            recon_display = np.clip(image_recon, 0.0, 1.0)
            ax3.imshow(recon_display, cmap='gray', vmin=0, vmax=1)
        else:
            ax3.imshow(np.clip(image_recon, 0.0, 1.0))
        ax3.set_title(f'{title_prefix}Reconstructed', fontsize=10, fontweight='bold')
        ax3.axis('off')

        fig.tight_layout()

    def plot_hybrid_comparison(self, fig, img1, img2, hybrid1, hybrid2, img1_name='Image 1', img2_name='Image 2'):
        """
        Plot hybrid image comparison

        Args:
            fig: Matplotlib figure
            img1: Original image 1
            img2: Original image 2
            hybrid1: Hybrid with mag1 + phase2
            hybrid2: Hybrid with mag2 + phase1
            img1_name: Name of image 1 (default: 'Image 1')
            img2_name: Name of image 2 (default: 'Image 2')
        """
        fig.clear()

        # Original images
        ax1 = fig.add_subplot(2, 2, 1)
        if img1.ndim == 2:
            ax1.imshow(img1, cmap='gray', vmin=0, vmax=1)
        else:
            ax1.imshow(np.clip(img1, 0.0, 1.0))
        ax1.set_title(img1_name, fontsize=10, fontweight='bold')
        ax1.axis('off')

        ax2 = fig.add_subplot(2, 2, 2)
        if img2.ndim == 2:
            ax2.imshow(img2, cmap='gray', vmin=0, vmax=1)
        else:
            ax2.imshow(np.clip(img2, 0.0, 1.0))
        ax2.set_title(img2_name, fontsize=10, fontweight='bold')
        ax2.axis('off')

        # Hybrid images
        ax3 = fig.add_subplot(2, 2, 3)
        ax3.imshow(hybrid1, cmap='gray')
        ax3.set_title(f'Mag({img1_name}) + Phase({img2_name})\n→ Looks like {img2_name}!', fontsize=9, fontweight='bold')
        ax3.axis('off')

        ax4 = fig.add_subplot(2, 2, 4)
        ax4.imshow(hybrid2, cmap='gray')
        ax4.set_title(f'Mag({img2_name}) + Phase({img1_name})\n→ Looks like {img1_name}!', fontsize=9, fontweight='bold')
        ax4.axis('off')

        fig.tight_layout()

    def plot_audio_components(self, fig, signal, magnitude, phase, reconstructed,
                              sample_rate, title_prefix='', magnitude_ref=None):
        """
        Plot audio waveform, magnitude spectrum, phase spectrum, and reconstruction
        """
        fig.clear()

        n_samples = len(signal)
        freq_axis = np.linspace(-sample_rate / 2, sample_rate / 2, n_samples, endpoint=False)

        display_samples = min(n_samples, max(int(sample_rate * 0.2), 2000))
        display_duration = display_samples / sample_rate
        time_axis = np.linspace(0, display_duration, display_samples, endpoint=False)
        recon_display = reconstructed[:display_samples]
        signal_display = signal[:display_samples]

        signal_amp = np.max(np.abs(signal))
        if signal_amp <= 0:
            signal_amp = 1.0

        mag_ref = magnitude if magnitude_ref is None else magnitude_ref
        mag_ref_db = 20 * np.log10(np.maximum(mag_ref, 1e-8))
        mag_min = np.min(mag_ref_db)
        mag_max = np.max(mag_ref_db)
        if mag_min == mag_max:
            mag_min -= 1.0
            mag_max += 1.0

        ax0 = fig.add_subplot(2, 2, 1)
        ax0.plot(time_axis, signal_display, color='tab:blue', linewidth=1.0)
        ax0.set_title(f'{title_prefix}Original Waveform', fontsize=10, fontweight='bold')
        ax0.set_xlabel('Time (s)')
        ax0.set_ylabel('Amplitude')
        ax0.grid(True, alpha=0.3)
        ax0.set_ylim(-signal_amp, signal_amp)

        ax1 = fig.add_subplot(2, 2, 2)
        magnitude_db = 20 * np.log10(np.maximum(magnitude, 1e-8))
        ax1.plot(freq_axis, magnitude_db, color='darkred')
        ax1.set_title(f'{title_prefix}Magnitude Spectrum (dB)', fontsize=10, fontweight='bold')
        ax1.set_xlabel('Frequency (Hz)')
        ax1.set_ylabel('Magnitude (dB)')
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim(mag_min, mag_max)

        ax2 = fig.add_subplot(2, 2, 3)
        ax2.plot(freq_axis, phase, color='purple')
        ax2.set_title(f'{title_prefix}Phase Spectrum', fontsize=10, fontweight='bold')
        ax2.set_xlabel('Frequency (Hz)')
        ax2.set_ylabel('Phase (rad)')
        ax2.grid(True, alpha=0.3)
        ax2.set_ylim(-np.pi, np.pi)

        ax3 = fig.add_subplot(2, 2, 4)
        ax3.plot(time_axis, recon_display, color='seagreen', linewidth=1.0)
        ax3.set_title(f'{title_prefix}Reconstructed Waveform', fontsize=10, fontweight='bold')
        ax3.set_xlabel('Time (s)')
        ax3.set_ylabel('Amplitude')
        ax3.grid(True, alpha=0.3)
        ax3.set_ylim(-signal_amp, signal_amp)

        fig.tight_layout()

    def plot_audio_hybrid_comparison(self, fig, signal1, signal2, hybrid1, hybrid2,
                                     sample_rate, name1='Signal 1', name2='Signal 2'):
        """
        Plot hybrid comparison for audio signals
        """
        fig.clear()

        n_samples = len(signal1)
        display_samples = min(n_samples, max(int(sample_rate * 0.2), 2000))
        time_axis = np.linspace(0, display_samples / sample_rate, display_samples, endpoint=False)
        sig1 = signal1[:display_samples]
        sig2 = signal2[:display_samples]
        hyb1 = hybrid1[:display_samples]
        hyb2 = hybrid2[:display_samples]
        amp_ref = max(
            np.max(np.abs(sig1)),
            np.max(np.abs(sig2)),
            np.max(np.abs(hyb1)),
            np.max(np.abs(hyb2))
        )
        if amp_ref <= 0:
            amp_ref = 1.0

        ax1 = fig.add_subplot(2, 2, 1)
        ax1.plot(time_axis, sig1, color='tab:blue', linewidth=1.0)
        ax1.set_title(name1, fontsize=10, fontweight='bold')
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Amplitude')
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim(-amp_ref, amp_ref)

        ax2 = fig.add_subplot(2, 2, 2)
        ax2.plot(time_axis, sig2, color='darkorange', linewidth=1.0)
        ax2.set_title(name2, fontsize=10, fontweight='bold')
        ax2.set_xlabel('Time (s)')
        ax2.set_ylabel('Amplitude')
        ax2.grid(True, alpha=0.3)
        ax2.set_ylim(-amp_ref, amp_ref)

        ax3 = fig.add_subplot(2, 2, 3)
        ax3.plot(time_axis, hyb1, color='seagreen', linewidth=1.0)
        ax3.set_title(f'Mag({name1}) + Phase({name2})', fontsize=9, fontweight='bold')
        ax3.set_xlabel('Time (s)')
        ax3.set_ylabel('Amplitude')
        ax3.grid(True, alpha=0.3)
        ax3.set_ylim(-amp_ref, amp_ref)

        ax4 = fig.add_subplot(2, 2, 4)
        ax4.plot(time_axis, hyb2, color='slateblue', linewidth=1.0)
        ax4.set_title(f'Mag({name2}) + Phase({name1})', fontsize=9, fontweight='bold')
        ax4.set_xlabel('Time (s)')
        ax4.set_ylabel('Amplitude')
        ax4.grid(True, alpha=0.3)
        ax4.set_ylim(-amp_ref, amp_ref)

        fig.tight_layout()

    def save_figure(self, fig, filepath, dpi=300):
        """
        Save figure to file

        Args:
            fig: Matplotlib figure
            filepath: Output file path
            dpi: Resolution in dots per inch
        """
        fig.savefig(filepath, dpi=dpi, bbox_inches='tight', facecolor='white')
