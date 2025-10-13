"""
Fourier Transform Analysis Model
Handles computation of 2D Fourier transforms and magnitude/phase manipulation
"""

import numpy as np
from scipy.fft import fft2, ifft2, fftshift, ifftshift


class FourierModel:
    """
    Models Fourier transform behavior and magnitude/phase manipulation
    """

    def __init__(self):
        """Initialize Fourier model"""
        pass

    def compute_fourier_transform(self, image):
        """
        Compute 2D Fourier transform of an image

        Args:
            image (numpy.ndarray): Input image (2D grayscale)

        Returns:
            tuple: (fft_shifted, magnitude, phase) where:
                - fft_shifted: Shifted FFT for visualization
                - magnitude: Magnitude spectrum
                - phase: Phase spectrum
        """
        # Compute 2D FFT and shift zero frequency to center
        fft_result = fft2(image)
        fft_shifted = fftshift(fft_result)

        # Extract magnitude and phase
        magnitude = np.abs(fft_shifted)
        phase = np.angle(fft_shifted)

        return fft_shifted, magnitude, phase

    def reconstruct_from_components(self, magnitude, phase):
        """
        Reconstruct image from magnitude and phase components

        Args:
            magnitude (numpy.ndarray): Magnitude spectrum
            phase (numpy.ndarray): Phase spectrum

        Returns:
            numpy.ndarray: Reconstructed image (real part)
        """
        # Reconstruct complex FFT from magnitude and phase
        fft_reconstructed = magnitude * np.exp(1j * phase)

        # Inverse FFT
        image_reconstructed = ifft2(ifftshift(fft_reconstructed))

        # Return real part (imaginary part should be negligible)
        return np.real(image_reconstructed)

    def create_hybrid_image(self, magnitude1, phase1, magnitude2, phase2,
                           hybrid_type='mag1_phase2'):
        """
        Create hybrid images by combining magnitude and phase from different images

        Args:
            magnitude1: Magnitude spectrum of image 1
            phase1: Phase spectrum of image 1
            magnitude2: Magnitude spectrum of image 2
            phase2: Phase spectrum of image 2
            hybrid_type (str): Type of hybrid ('mag1_phase2' or 'mag2_phase1')

        Returns:
            numpy.ndarray: Hybrid image
        """
        if hybrid_type == 'mag1_phase2':
            return self.reconstruct_from_components(magnitude1, phase2)
        elif hybrid_type == 'mag2_phase1':
            return self.reconstruct_from_components(magnitude2, phase1)
        else:
            raise ValueError(f"Unknown hybrid type: {hybrid_type}")

    def apply_uniform_magnitude(self, magnitude, phase, uniform_value=10.0):
        """
        Replace magnitude spectrum with uniform value

        Args:
            magnitude: Original magnitude spectrum (for shape reference)
            phase: Phase spectrum to keep
            uniform_value (float): Uniform magnitude value

        Returns:
            numpy.ndarray: Reconstructed image with uniform magnitude
        """
        uniform_magnitude = np.ones_like(magnitude) * uniform_value
        return self.reconstruct_from_components(uniform_magnitude, phase)

    def apply_uniform_phase(self, magnitude, phase, uniform_value=0.0):
        """
        Replace phase spectrum with uniform value

        Args:
            magnitude: Magnitude spectrum to keep
            phase: Original phase spectrum (for shape reference)
            uniform_value (float): Uniform phase value (in radians)

        Returns:
            numpy.ndarray: Reconstructed image with uniform phase
        """
        uniform_phase = np.ones_like(phase) * uniform_value
        return self.reconstruct_from_components(magnitude, uniform_phase)

    def calculate_reconstruction_quality(self, original, reconstructed):
        """
        Calculate quality metrics between original and reconstructed images

        Args:
            original: Original image
            reconstructed: Reconstructed image

        Returns:
            dict: Quality metrics (MSE, correlation, SSIM-like measure)
        """
        # Ensure same shape
        if original.shape != reconstructed.shape:
            return {'error': 'Shape mismatch'}

        # Mean Squared Error
        mse = np.mean((original - reconstructed)**2)

        # Correlation coefficient
        correlation = np.corrcoef(original.flatten(), reconstructed.flatten())[0, 1]

        # Normalized error
        original_range = np.max(original) - np.min(original)
        if original_range > 0:
            normalized_error = np.sqrt(mse) / original_range
        else:
            normalized_error = 0.0

        # Structural similarity (simplified)
        mean_orig = np.mean(original)
        mean_recon = np.mean(reconstructed)
        std_orig = np.std(original)
        std_recon = np.std(reconstructed)

        c1 = 0.01**2
        c2 = 0.03**2

        if std_orig > 0 and std_recon > 0:
            ssim = ((2*mean_orig*mean_recon + c1) * (2*std_orig*std_recon + c2)) / \
                   ((mean_orig**2 + mean_recon**2 + c1) * (std_orig**2 + std_recon**2 + c2))
        else:
            ssim = 1.0 if mse < 1e-10 else 0.0

        return {
            'mse': mse,
            'correlation': correlation,
            'normalized_error': normalized_error,
            'ssim': ssim
        }

    def create_frequency_mask(self, shape, mask_type='lowpass', cutoff=0.3):
        """
        Create frequency domain masks for filtering

        Args:
            shape: Shape of the frequency domain (height, width)
            mask_type (str): 'lowpass', 'highpass', or 'bandpass'
            cutoff (float): Cutoff frequency (0-1, relative to Nyquist)

        Returns:
            numpy.ndarray: Binary mask
        """
        h, w = shape
        cy, cx = h // 2, w // 2

        # Create distance map from center
        y, x = np.ogrid[:h, :w]
        distances = np.sqrt((x - cx)**2 + (y - cy)**2)
        max_distance = np.sqrt(cx**2 + cy**2)
        normalized_distances = distances / max_distance

        if mask_type == 'lowpass':
            mask = (normalized_distances <= cutoff).astype(float)
        elif mask_type == 'highpass':
            mask = (normalized_distances > cutoff).astype(float)
        elif mask_type == 'bandpass':
            cutoff_low = cutoff
            cutoff_high = cutoff + 0.2
            mask = ((normalized_distances > cutoff_low) &
                   (normalized_distances <= cutoff_high)).astype(float)
        else:
            raise ValueError(f"Unknown mask type: {mask_type}")

        return mask

    def apply_frequency_filter(self, magnitude, phase, mask):
        """
        Apply frequency domain filter

        Args:
            magnitude: Magnitude spectrum
            phase: Phase spectrum
            mask: Frequency mask

        Returns:
            numpy.ndarray: Filtered image
        """
        filtered_magnitude = magnitude * mask
        return self.reconstruct_from_components(filtered_magnitude, phase)
