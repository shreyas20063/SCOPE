"""
Audio Fourier Transform Analysis Model
Handles computation of 1D Fourier transforms and magnitude/phase manipulation for audio signals
"""

import numpy as np
from scipy.fft import fft, ifft, fftshift, ifftshift


class AudioFourierModel:
    """
    Models Fourier transform behavior for audio signals
    """

    def __init__(self):
        """Initialize audio Fourier model"""
        pass

    def compute_fourier_transform(self, signal):
        """
        Compute 1D Fourier transform of an audio signal

        Args:
            signal (numpy.ndarray): Input audio signal (1D)

        Returns:
            tuple: (fft_shifted, magnitude, phase)
        """
        fft_result = fft(signal)
        fft_shifted = fftshift(fft_result)

        magnitude = np.abs(fft_shifted)
        phase = np.angle(fft_shifted)

        return fft_shifted, magnitude, phase

    def reconstruct_from_components(self, magnitude, phase):
        """
        Reconstruct audio signal from magnitude and phase components

        Args:
            magnitude (numpy.ndarray): Magnitude spectrum
            phase (numpy.ndarray): Phase spectrum

        Returns:
            numpy.ndarray: Reconstructed audio signal (real part)
        """
        fft_reconstructed = magnitude * np.exp(1j * phase)
        signal_reconstructed = ifft(ifftshift(fft_reconstructed))
        return np.real(signal_reconstructed)

    def create_hybrid_signal(self, magnitude1, phase1, magnitude2, phase2,
                             hybrid_type='mag1_phase2'):
        """
        Create hybrid signals by combining magnitude and phase from different signals

        Args:
            magnitude1: Magnitude spectrum of signal 1
            phase1: Phase spectrum of signal 1
            magnitude2: Magnitude spectrum of signal 2
            phase2: Phase spectrum of signal 2
            hybrid_type (str): 'mag1_phase2' or 'mag2_phase1'

        Returns:
            numpy.ndarray: Hybrid audio signal
        """
        if hybrid_type == 'mag1_phase2':
            return self.reconstruct_from_components(magnitude1, phase2)
        if hybrid_type == 'mag2_phase1':
            return self.reconstruct_from_components(magnitude2, phase1)
        raise ValueError(f"Unknown hybrid type: {hybrid_type}")

    def apply_uniform_magnitude(self, magnitude, phase, uniform_value=1.0):
        """
        Replace magnitude spectrum with uniform value and reconstruct
        """
        uniform_magnitude = np.ones_like(magnitude) * uniform_value
        return self.reconstruct_from_components(uniform_magnitude, phase)

    def apply_uniform_phase(self, magnitude, phase, uniform_value=0.0):
        """
        Replace phase spectrum with uniform value and reconstruct
        """
        uniform_phase = np.ones_like(phase) * uniform_value
        return self.reconstruct_from_components(magnitude, uniform_phase)

    def calculate_reconstruction_quality(self, original, reconstructed):
        """
        Calculate quality metrics between original and reconstructed signals

        Args:
            original: Original audio signal
            reconstructed: Reconstructed audio signal

        Returns:
            dict: Quality metrics (MSE, correlation, SNR-like measure)
        """
        if original.shape != reconstructed.shape:
            min_len = min(len(original), len(reconstructed))
            original = original[:min_len]
            reconstructed = reconstructed[:min_len]

        mse = np.mean((original - reconstructed) ** 2)

        if np.std(original) > 0 and np.std(reconstructed) > 0:
            correlation = np.corrcoef(original, reconstructed)[0, 1]
        else:
            correlation = 1.0 if mse < 1e-10 else 0.0

        power_original = np.mean(original ** 2)
        power_error = np.mean((original - reconstructed) ** 2)
        if power_error > 0:
            snr = 10 * np.log10(power_original / power_error)
        else:
            snr = np.inf

        return {
            'mse': mse,
            'correlation': correlation,
            'snr_db': snr
        }
