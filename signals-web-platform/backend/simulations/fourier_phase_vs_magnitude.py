"""
Fourier Analysis: Phase vs Magnitude Simulator

Complete web implementation matching PyQt5 app exactly.
Demonstrates that phase information is more critical than magnitude
for preserving signal structure in both images and audio.

Features:
- Image mode: Two test images with Building, Face, Geometric, Texture patterns
- Audio mode: Two test signals with Sine, Square, Sawtooth, Beat waveforms
- Mode selection: Original, Uniform Magnitude, Uniform Phase
- Hybrid comparison: Magnitude from one + Phase from other
- Quality metrics: MSE, Correlation, SSIM (images), SNR (audio)
- Base64 encoded images and audio for proper web display/playback

Math extracted from: fourier_phase_vs_magnitude/core/
"""

import numpy as np
from scipy.fft import fft2, ifft2, fft, ifft, fftshift, ifftshift
from scipy import signal as scipy_signal
from scipy import ndimage
from typing import Any, Dict, List, Optional
import base64
import io
from .base_simulator import BaseSimulator

# Try to import PIL for image encoding
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# Try to import scipy.io.wavfile for audio encoding
try:
    from scipy.io import wavfile
    HAS_WAVFILE = True
except ImportError:
    HAS_WAVFILE = False


class FourierPhaseMagnitudeSimulator(BaseSimulator):
    """
    Fourier Phase vs Magnitude simulation matching PyQt5 app.

    Parameters matching PyQt5:
    - analysis_mode: 'image' or 'audio'
    - image1_pattern / audio1_type: Source for signal 1
    - image2_pattern / audio2_type: Source for signal 2
    - image1_mode / image2_mode: Original, Uniform Magnitude, Uniform Phase
    - uniform_magnitude: 0.1 to 100.0 (default 10.0)
    - uniform_phase: -π to π (default 0.0)
    """

    # Configuration matching PyQt5
    IMAGE_SIZE = 256  # Fixed size matching PyQt5
    AUDIO_SAMPLE_RATE = 44100
    AUDIO_DURATION = 2.0
    AUDIO_DISPLAY_SAMPLES = 2000  # First 2000 samples for waveform display

    # Unified color palette - matches other simulations
    COLORS = {
        # Signal colors
        "signal1": "#22d3ee",        # Cyan - signal 1
        "signal2": "#f87171",        # Coral red - signal 2
        "hybrid1": "#34d399",        # Emerald - hybrid (mag1 + phase2)
        "hybrid2": "#fbbf24",        # Amber - hybrid (mag2 + phase1)
        "reconstructed": "#a78bfa",  # Violet - reconstructed

        # Spectrum colors
        "magnitude": "#ef4444",      # Red for magnitude emphasis
        "phase": "#10b981",          # Green for phase emphasis

        # Reference
        "reference": "#f472b6",      # Pink
        "grid": "rgba(148, 163, 184, 0.2)",
        "text": "#e2e8f0",
    }

    # Image colormaps for Plotly
    IMAGE_COLORSCALE = "Greys"
    MAGNITUDE_COLORSCALE = "Hot"
    PHASE_COLORSCALE = "RdBu"

    # Parameter schema matching PyQt5 exactly
    PARAMETER_SCHEMA = {
        "analysis_mode": {
            "type": "select",
            "label": "Analysis Mode",
            "options": [
                {"value": "image", "label": "Image Analysis"},
                {"value": "audio", "label": "Audio Analysis"},
            ],
            "default": "image",
            "description": "Switch between image and audio Fourier analysis",
        },
        # Image parameters
        "image1_pattern": {
            "type": "select",
            "label": "Image 1 Pattern",
            "options": [
                {"value": "building", "label": "Building"},
                {"value": "face", "label": "Face"},
                {"value": "geometric", "label": "Geometric"},
                {"value": "texture", "label": "Texture"},
            ],
            "default": "building",
            "group": "Image Source",
        },
        "image2_pattern": {
            "type": "select",
            "label": "Image 2 Pattern",
            "options": [
                {"value": "building", "label": "Building"},
                {"value": "face", "label": "Face"},
                {"value": "geometric", "label": "Geometric"},
                {"value": "texture", "label": "Texture"},
            ],
            "default": "face",
            "group": "Image Source",
        },
        "image1_mode": {
            "type": "select",
            "label": "Image 1 Mode",
            "options": [
                {"value": "original", "label": "Original"},
                {"value": "uniform_magnitude", "label": "Uniform Magnitude"},
                {"value": "uniform_phase", "label": "Uniform Phase"},
            ],
            "default": "original",
            "group": "Fourier Mode",
        },
        "image2_mode": {
            "type": "select",
            "label": "Image 2 Mode",
            "options": [
                {"value": "original", "label": "Original"},
                {"value": "uniform_magnitude", "label": "Uniform Magnitude"},
                {"value": "uniform_phase", "label": "Uniform Phase"},
            ],
            "default": "original",
            "group": "Fourier Mode",
        },
        # Audio parameters
        "audio1_type": {
            "type": "select",
            "label": "Audio 1 Signal",
            "options": [
                {"value": "sine", "label": "Sine (440 Hz)"},
                {"value": "square", "label": "Square (220 Hz)"},
                {"value": "sawtooth", "label": "Sawtooth (180 Hz)"},
                {"value": "beat", "label": "Beat (AM)"},
            ],
            "default": "sine",
            "group": "Audio Source",
        },
        "audio2_type": {
            "type": "select",
            "label": "Audio 2 Signal",
            "options": [
                {"value": "sine", "label": "Sine (440 Hz)"},
                {"value": "square", "label": "Square (220 Hz)"},
                {"value": "sawtooth", "label": "Sawtooth (180 Hz)"},
                {"value": "beat", "label": "Beat (AM)"},
            ],
            "default": "square",
            "group": "Audio Source",
        },
        # Uniform value sliders (matching PyQt5 exactly)
        "uniform_magnitude": {
            "type": "slider",
            "label": "Uniform Magnitude",
            "min": 0.1,
            "max": 100.0,
            "step": 0.1,
            "default": 10.0,
            "unit": "",
            "description": "Value to use when replacing magnitude spectrum",
        },
        "uniform_phase": {
            "type": "slider",
            "label": "Uniform Phase",
            "min": -3.14,
            "max": 3.14,
            "step": 0.01,
            "default": 0.0,
            "unit": "rad",
            "description": "Value to use when replacing phase spectrum (-π to π)",
        },
    }

    DEFAULT_PARAMS = {
        "analysis_mode": "image",
        "image1_pattern": "building",
        "image2_pattern": "face",
        "image1_mode": "original",
        "image2_mode": "original",
        "audio1_type": "sine",
        "audio2_type": "square",
        "uniform_magnitude": 10.0,
        "uniform_phase": 0.0,
    }

    def __init__(self, simulation_id: str):
        super().__init__(simulation_id)
        # Image data
        self._image1 = None
        self._image2 = None
        self._mag1 = None
        self._phase1 = None
        self._mag2 = None
        self._phase2 = None
        self._recon1 = None
        self._recon2 = None
        self._hybrid_mag1_phase2 = None
        self._hybrid_mag2_phase1 = None
        self._image_metrics = {}

        # Audio data
        self._audio1 = None
        self._audio2 = None
        self._audio_mag1 = None
        self._audio_phase1 = None
        self._audio_mag2 = None
        self._audio_phase2 = None
        self._audio_recon1 = None
        self._audio_recon2 = None
        self._audio_hybrid1 = None
        self._audio_hybrid2 = None
        self._audio_metrics = {}

    def initialize(self, params: Optional[Dict[str, Any]] = None) -> None:
        """Initialize simulation with parameters."""
        self.parameters = self.DEFAULT_PARAMS.copy()
        if params:
            for name, value in params.items():
                if name in self.parameters:
                    self.parameters[name] = self._validate_param(name, value)
        self._initialized = True
        self._compute()

    def update_parameter(self, name: str, value: Any) -> Dict[str, Any]:
        """Update a single parameter and recompute."""
        if name in self.parameters:
            self.parameters[name] = self._validate_param(name, value)
            self._compute()
        return self.get_state()

    def reset(self) -> Dict[str, Any]:
        """Reset simulation to default parameters."""
        self.parameters = self.DEFAULT_PARAMS.copy()
        self._initialized = True
        self._compute()
        return self.get_state()

    def run(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run simulation with given parameters, ensuring recomputation."""
        if not self._initialized:
            self.initialize(params)
        elif params:
            for name, value in params.items():
                if name in self.parameters:
                    self.parameters[name] = self._validate_param(name, value)
            # Recompute after updating parameters
            self._compute()
        return self.get_state()

    def _compute(self) -> None:
        """Compute all Fourier analysis based on current mode."""
        if self.parameters["analysis_mode"] == "image":
            self._compute_image_analysis()
        else:
            self._compute_audio_analysis()

    # =========================================================================
    # Image Analysis (matching PyQt5)
    # =========================================================================

    def _rgb_to_gray(self, img: np.ndarray) -> np.ndarray:
        """Convert RGB image to grayscale using luminance formula."""
        if img.ndim == 3 and img.shape[2] == 3:
            return 0.299 * img[:, :, 0] + 0.587 * img[:, :, 1] + 0.114 * img[:, :, 2]
        return img

    def _compute_image_analysis(self) -> None:
        """Compute 2D Fourier analysis for images."""
        # Generate test images (may be RGB)
        self._image1 = self._generate_image(self.parameters["image1_pattern"])
        self._image2 = self._generate_image(self.parameters["image2_pattern"])

        # Convert to grayscale for FFT (but keep originals for display)
        gray1 = self._rgb_to_gray(self._image1)
        gray2 = self._rgb_to_gray(self._image2)

        # Compute FFT for both images (on grayscale)
        fft1 = fftshift(fft2(gray1))
        fft2_result = fftshift(fft2(gray2))

        # Extract magnitude and phase (original)
        self._mag1 = np.abs(fft1)
        self._phase1 = np.angle(fft1)
        self._mag2 = np.abs(fft2_result)
        self._phase2 = np.angle(fft2_result)

        # Apply modes for image 1 and store processed versions
        self._mag1_processed, self._phase1_processed = self._apply_mode(
            self._mag1, self._phase1, self.parameters["image1_mode"]
        )

        # Apply modes for image 2 and store processed versions
        self._mag2_processed, self._phase2_processed = self._apply_mode(
            self._mag2, self._phase2, self.parameters["image2_mode"]
        )

        # Reconstruct images (will be grayscale)
        self._recon1 = self._reconstruct_image(self._mag1_processed, self._phase1_processed)
        self._recon2 = self._reconstruct_image(self._mag2_processed, self._phase2_processed)

        # Create hybrid images (the key demonstration!)
        # Hybrid 1: Magnitude from Image 1 + Phase from Image 2
        self._hybrid_mag1_phase2 = self._reconstruct_image(self._mag1, self._phase2)
        # Hybrid 2: Magnitude from Image 2 + Phase from Image 1
        self._hybrid_mag2_phase1 = self._reconstruct_image(self._mag2, self._phase1)

        # Calculate quality metrics (using grayscale)
        self._image_metrics = {
            "image1": self._calculate_image_quality(gray1, self._recon1),
            "image2": self._calculate_image_quality(gray2, self._recon2),
            "hybrid1_to_image2": self._calculate_image_quality(gray2, self._hybrid_mag1_phase2),
            "hybrid2_to_image1": self._calculate_image_quality(gray1, self._hybrid_mag2_phase1),
        }

    def _apply_mode(self, magnitude: np.ndarray, phase: np.ndarray, mode: str):
        """Apply processing mode to magnitude/phase."""
        if mode == "uniform_magnitude":
            uniform_val = self.parameters["uniform_magnitude"]
            return np.full_like(magnitude, uniform_val), phase
        elif mode == "uniform_phase":
            uniform_val = self.parameters["uniform_phase"]
            return magnitude, np.full_like(phase, uniform_val)
        else:  # original
            return magnitude, phase

    def _reconstruct_image(self, magnitude: np.ndarray, phase: np.ndarray) -> np.ndarray:
        """Reconstruct image from magnitude and phase."""
        fft_reconstructed = magnitude * np.exp(1j * phase)
        reconstructed = np.real(ifft2(ifftshift(fft_reconstructed)))
        # Normalize to [0, 1]
        if reconstructed.max() != reconstructed.min():
            reconstructed = (reconstructed - reconstructed.min()) / (reconstructed.max() - reconstructed.min())
        return reconstructed

    def _generate_image(self, pattern: str) -> np.ndarray:
        """Generate test image matching PyQt5 patterns."""
        size = self.IMAGE_SIZE
        if pattern == "building":
            return self._generate_building(size)
        elif pattern == "face":
            return self._generate_face(size)
        elif pattern == "geometric":
            return self._generate_geometric(size)
        elif pattern == "texture":
            return self._generate_texture(size)
        else:
            return self._generate_building(size)

    def _generate_building(self, size: int) -> np.ndarray:
        """Generate a colorful sunset cityscape."""
        img = np.zeros((size, size, 3))

        # Vibrant sunset sky gradient (orange/pink/purple)
        y = np.arange(size).reshape(-1, 1) / size
        img[:, :, 0] = 0.95 - 0.4 * y.squeeze()   # R: orange to pink
        img[:, :, 1] = 0.4 + 0.2 * y.squeeze()    # G: warm tones
        img[:, :, 2] = 0.3 + 0.5 * y.squeeze()    # B: purple at top

        ground_y = int(size * 0.75)

        # Colorful ground
        img[ground_y:, :, 0] = 0.15
        img[ground_y:, :, 1] = 0.12
        img[ground_y:, :, 2] = 0.20

        def draw_building(x, w, h, color):
            """Draw a colorful building silhouette."""
            for c in range(3):
                img[ground_y - h:ground_y, x:x+w, c] = color[c]
            # Lit windows (yellow/warm)
            win_h, win_w = 8, 6
            for wy in range(ground_y - h + 10, ground_y - 10, win_h + 6):
                for wx in range(x + 5, x + w - 5, win_w + 5):
                    if np.random.rand() > 0.3:  # 70% windows lit
                        img[wy:wy+win_h, wx:wx+win_w, 0] = 1.0
                        img[wy:wy+win_h, wx:wx+win_w, 1] = 0.9
                        img[wy:wy+win_h, wx:wx+win_w, 2] = 0.4

        np.random.seed(42)
        # Colorful buildings with different heights
        colors = [(0.2, 0.15, 0.35), (0.25, 0.18, 0.4), (0.18, 0.12, 0.32),
                  (0.22, 0.16, 0.38), (0.2, 0.14, 0.34)]
        x = 10
        while x < size - 30:
            w = np.random.randint(25, 50)
            h = np.random.randint(int(size * 0.25), int(size * 0.6))
            color = colors[np.random.randint(len(colors))]
            draw_building(x, w, h, color)
            x += w + np.random.randint(5, 15)

        # Add sun/moon glow
        sun_y, sun_x = int(size * 0.25), int(size * 0.7)
        y_grid, x_grid = np.ogrid[:size, :size]
        sun_dist = np.sqrt((x_grid - sun_x)**2 + (y_grid - sun_y)**2)
        sun_glow = np.exp(-sun_dist / 40) * 0.5
        img[:, :, 0] = np.minimum(1.0, img[:, :, 0] + sun_glow)
        img[:, :, 1] = np.minimum(1.0, img[:, :, 1] + sun_glow * 0.6)

        for c in range(3):
            img[:, :, c] = ndimage.gaussian_filter(img[:, :, c], sigma=0.5)

        return np.clip(img, 0, 1).astype(np.float64)

    def _generate_face(self, size: int) -> np.ndarray:
        """Generate a cute colorful emoji-style face."""
        img = np.zeros((size, size, 3))
        center = size // 2
        y, x = np.ogrid[:size, :size]

        # Bright gradient background (cyan to pink)
        y_norm = y / size
        img[:, :, 0] = 0.4 + 0.5 * y_norm.squeeze()   # R
        img[:, :, 1] = 0.8 - 0.3 * y_norm.squeeze()   # G
        img[:, :, 2] = 0.9 - 0.2 * y_norm.squeeze()   # B

        # Yellow face circle
        face_radius = size * 0.38
        face_cy = center
        dist = np.sqrt((x - center)**2 + (y - face_cy)**2)
        face_mask = dist <= face_radius

        # Bright yellow face
        img[face_mask, 0] = 1.0
        img[face_mask, 1] = 0.85
        img[face_mask, 2] = 0.2

        # Add slight gradient to face
        face_grad = dist / face_radius
        img[face_mask, 0] -= face_grad[face_mask] * 0.15
        img[face_mask, 1] -= face_grad[face_mask] * 0.1

        # Big cute eyes
        eye_y = face_cy - int(size * 0.08)
        eye_spacing = int(size * 0.14)
        eye_radius = size // 10

        for eye_x in [center - eye_spacing, center + eye_spacing]:
            eye_dist = np.sqrt((x - eye_x)**2 + (y - eye_y)**2)
            # White of eye
            eye_white = eye_dist <= eye_radius
            img[eye_white, 0] = 1.0
            img[eye_white, 1] = 1.0
            img[eye_white, 2] = 1.0
            # Black pupil
            pupil_mask = eye_dist <= eye_radius * 0.5
            img[pupil_mask, 0] = 0.1
            img[pupil_mask, 1] = 0.1
            img[pupil_mask, 2] = 0.1
            # Eye shine
            shine_x = eye_x - eye_radius // 3
            shine_y = eye_y - eye_radius // 3
            shine_dist = np.sqrt((x - shine_x)**2 + (y - shine_y)**2)
            shine_mask = shine_dist <= eye_radius * 0.2
            img[shine_mask, 0] = 1.0
            img[shine_mask, 1] = 1.0
            img[shine_mask, 2] = 1.0

        # Pink cheeks
        cheek_radius = size // 12
        for cheek_x in [center - int(size * 0.25), center + int(size * 0.25)]:
            cheek_y = face_cy + int(size * 0.08)
            cheek_dist = np.sqrt((x - cheek_x)**2 + (y - cheek_y)**2)
            cheek_mask = cheek_dist <= cheek_radius
            img[cheek_mask, 0] = 1.0
            img[cheek_mask, 1] = 0.6
            img[cheek_mask, 2] = 0.6

        # Happy smile (U-shape curve)
        smile_y = face_cy + int(size * 0.10)
        smile_width = int(size * 0.15)
        smile_depth = int(size * 0.06)
        for sx in range(center - smile_width, center + smile_width + 1):
            dx = (sx - center) / smile_width
            # U-shape: lowest at center, higher at edges
            sy = smile_y + int(smile_depth * (1 - dx**2))
            for dy in range(-4, 5):
                if 0 <= sy + dy < size and 0 <= sx < size:
                    img[sy + dy, sx, 0] = 0.3
                    img[sy + dy, sx, 1] = 0.15
                    img[sy + dy, sx, 2] = 0.1

        for c in range(3):
            img[:, :, c] = ndimage.gaussian_filter(img[:, :, c], sigma=0.5)

        return np.clip(img, 0, 1).astype(np.float64)

    def _generate_geometric(self, size: int) -> np.ndarray:
        """Generate a vibrant colorful mandala pattern."""
        img = np.zeros((size, size, 3))
        center = size // 2
        y, x = np.ogrid[:size, :size]
        dist = np.sqrt((x - center)**2 + (y - center)**2)
        angle = np.arctan2(y - center, x - center)

        # Deep dark background for contrast
        img[:, :, 0] = 0.05
        img[:, :, 1] = 0.02
        img[:, :, 2] = 0.12

        # Vibrant neon colors
        colors = [
            (1.0, 0.1, 0.3),   # Hot pink
            (1.0, 0.5, 0.0),   # Bright orange
            (1.0, 1.0, 0.0),   # Pure yellow
            (0.0, 1.0, 0.3),   # Neon green
            (0.0, 0.8, 1.0),   # Electric cyan
            (0.6, 0.0, 1.0),   # Vivid purple
            (1.0, 0.2, 0.8),   # Magenta
        ]

        # Create bold mandala rings
        for i, radius in enumerate(range(18, int(size * 0.5), 15)):
            thickness = 12
            ring_mask = (dist >= radius - thickness) & (dist <= radius + thickness)
            color = colors[i % len(colors)]

            # Strong angular modulation for mandala petals
            n_petals = 8 + (i % 2) * 4
            petal_mod = 0.3 + 0.7 * np.cos(n_petals * angle)**2

            for c in range(3):
                img[ring_mask, c] = np.maximum(img[ring_mask, c], color[c] * petal_mod[ring_mask])

        # Bright glowing center
        center_mask = dist <= 30
        center_grad = 1 - (dist / 30)**0.5
        img[center_mask, 0] = 1.0 * center_grad[center_mask]
        img[center_mask, 1] = 0.9 * center_grad[center_mask]
        img[center_mask, 2] = 0.3 * center_grad[center_mask]

        # Bold radiating rays
        n_rays = 16
        for i in range(n_rays):
            ray_angle = 2 * np.pi * i / n_rays
            ray_mask = (np.abs(np.mod(angle - ray_angle + np.pi, 2*np.pi) - np.pi) < 0.06) & (dist > 35) & (dist < size * 0.48)
            color = colors[i % len(colors)]
            for c in range(3):
                img[ray_mask, c] = np.maximum(img[ray_mask, c], color[c] * 0.9)

        # Strong outer glow
        outer_glow = np.exp(-(dist - size * 0.42)**2 / (2 * 25**2)) * (dist > size * 0.3)
        img[:, :, 0] += outer_glow * 0.5
        img[:, :, 1] += outer_glow * 0.3
        img[:, :, 2] += outer_glow * 0.6

        # Boost overall vibrancy
        img = np.power(img, 0.8)

        for c in range(3):
            img[:, :, c] = ndimage.gaussian_filter(img[:, :, c], sigma=0.4)

        return np.clip(img, 0, 1).astype(np.float64)

    def _generate_texture(self, size: int) -> np.ndarray:
        """Generate a vibrant plasma/aurora texture pattern."""
        img = np.zeros((size, size, 3))
        y, x = np.meshgrid(np.arange(size), np.arange(size), indexing='ij')
        center = size // 2

        np.random.seed(42)

        # Red channel - bold diagonal waves
        r_base = 0.5 + 0.4 * np.sin(2 * np.pi * 3 * x / size)
        r_base += 0.3 * np.sin(2 * np.pi * 5 * (x + y) / size / np.sqrt(2))
        r_base += 0.2 * np.cos(2 * np.pi * 7 * y / size)

        # Green channel - strong circular ripples
        dist = np.sqrt((x - center)**2 + (y - center)**2)
        g_base = 0.4 + 0.4 * np.sin(2 * np.pi * 4 * dist / size)
        g_base += 0.3 * np.cos(2 * np.pi * 5 * x / size)
        g_base += 0.2 * np.sin(2 * np.pi * 8 * (x - y) / size / np.sqrt(2))

        # Blue channel - vivid patterns
        b_base = 0.6 + 0.35 * np.sin(2 * np.pi * 3 * y / size)
        b_base += 0.3 * np.cos(2 * np.pi * 6 * x / size)
        b_base += 0.25 * np.sin(2 * np.pi * 4 * dist / size)

        # Add smooth noise
        noise = np.random.rand(size, size)
        noise_smooth = ndimage.gaussian_filter(noise, sigma=10)

        img[:, :, 0] = r_base + 0.25 * noise_smooth
        img[:, :, 1] = g_base + 0.2 * noise_smooth
        img[:, :, 2] = b_base + 0.25 * noise_smooth

        # Normalize each channel
        for c in range(3):
            ch = img[:, :, c]
            img[:, :, c] = (ch - ch.min()) / (ch.max() - ch.min() + 1e-8)

        # Strong saturation boost
        img = np.power(img, 0.7)

        # Increase contrast
        img = (img - 0.5) * 1.3 + 0.5

        # Add more bright sparkles
        for _ in range(25):
            sy, sx = np.random.randint(10, size - 10, 2)
            spark_dist = np.sqrt((x - sx)**2 + (y - sy)**2)
            spark_mask = spark_dist < 10
            spark_val = np.exp(-spark_dist[spark_mask] / 4)
            for c in range(3):
                img[spark_mask, c] = np.minimum(1.0, img[spark_mask, c] + 0.5 * spark_val)

        for c in range(3):
            img[:, :, c] = ndimage.gaussian_filter(img[:, :, c], sigma=0.4)

        return np.clip(img, 0, 1).astype(np.float64)

    def _calculate_image_quality(self, original: np.ndarray, reconstructed: np.ndarray) -> Dict:
        """Calculate image quality metrics (MSE, Correlation, SSIM)."""
        mse = float(np.mean((original - reconstructed)**2))

        # Correlation coefficient
        corr = np.corrcoef(original.flatten(), reconstructed.flatten())[0, 1]
        correlation = float(corr) if not np.isnan(corr) else 0.0

        # Simplified SSIM (matching PyQt5)
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
            "mse": mse,
            "correlation": correlation,
            "ssim": float(ssim),
        }

    # =========================================================================
    # Audio Analysis (matching PyQt5)
    # =========================================================================

    def _compute_audio_analysis(self) -> None:
        """Compute 1D Fourier analysis for audio signals."""
        # Generate test signals
        self._audio1 = self._generate_audio(self.parameters["audio1_type"])
        self._audio2 = self._generate_audio(self.parameters["audio2_type"])

        # Compute FFT for both signals
        fft1 = fftshift(fft(self._audio1))
        fft2_result = fftshift(fft(self._audio2))

        self._audio_mag1 = np.abs(fft1)
        self._audio_phase1 = np.angle(fft1)
        self._audio_mag2 = np.abs(fft2_result)
        self._audio_phase2 = np.angle(fft2_result)

        # Reconstruct originals (perfect reconstruction)
        self._audio_recon1 = self._reconstruct_audio(self._audio_mag1, self._audio_phase1)
        self._audio_recon2 = self._reconstruct_audio(self._audio_mag2, self._audio_phase2)

        # Create hybrid signals (key demonstration)
        # Hybrid 1: Magnitude from Audio 1 + Phase from Audio 2
        self._audio_hybrid1 = self._reconstruct_audio(self._audio_mag1, self._audio_phase2)
        # Hybrid 2: Magnitude from Audio 2 + Phase from Audio 1
        self._audio_hybrid2 = self._reconstruct_audio(self._audio_mag2, self._audio_phase1)

        # Calculate quality metrics
        self._audio_metrics = {
            "audio1": self._calculate_audio_quality(self._audio1, self._audio_recon1),
            "audio2": self._calculate_audio_quality(self._audio2, self._audio_recon2),
            "hybrid1_to_audio2": self._calculate_audio_quality(self._audio2, self._audio_hybrid1),
            "hybrid2_to_audio1": self._calculate_audio_quality(self._audio1, self._audio_hybrid2),
        }

    def _reconstruct_audio(self, magnitude: np.ndarray, phase: np.ndarray) -> np.ndarray:
        """Reconstruct audio from magnitude and phase."""
        fft_reconstructed = magnitude * np.exp(1j * phase)
        return np.real(ifft(ifftshift(fft_reconstructed)))

    def _generate_audio(self, signal_type: str) -> np.ndarray:
        """Generate test audio signals with SAME base frequency for phase dominance demo.

        All signals use 220 Hz base frequency so their frequency content overlaps.
        This allows meaningful magnitude/phase swapping where phase truly dominates.
        """
        t = np.linspace(0, self.AUDIO_DURATION,
                        int(self.AUDIO_SAMPLE_RATE * self.AUDIO_DURATION),
                        endpoint=False)

        base_freq = 220  # Same base frequency for all signals

        if signal_type == "sine":
            # Multi-harmonic "sine-like" signal (fundamental + weak harmonics)
            # This gives it frequency content to swap with other signals
            signal = np.sin(2 * np.pi * base_freq * t)
            signal += 0.3 * np.sin(2 * np.pi * 2 * base_freq * t)  # 2nd harmonic
            signal += 0.15 * np.sin(2 * np.pi * 3 * base_freq * t)  # 3rd harmonic
            return signal / np.max(np.abs(signal))  # Normalize

        elif signal_type == "square":
            # Square wave at same base frequency
            return scipy_signal.square(2 * np.pi * base_freq * t, duty=0.5)

        elif signal_type == "sawtooth":
            # Sawtooth wave at same base frequency
            return scipy_signal.sawtooth(2 * np.pi * base_freq * t)

        elif signal_type == "beat":
            # Beat signal with same base frequency
            carrier = np.sin(2 * np.pi * base_freq * t)
            # Add harmonics to make it spectrally rich
            carrier += 0.5 * np.sin(2 * np.pi * 2 * base_freq * t)
            carrier += 0.25 * np.sin(2 * np.pi * 3 * base_freq * t)
            modulator = 0.5 * (1 + np.sin(2 * np.pi * 3 * t))  # 3 Hz modulation
            signal = carrier * modulator
            return signal / np.max(np.abs(signal))

        else:
            return scipy_signal.square(2 * np.pi * base_freq * t, duty=0.5)

    def _calculate_audio_quality(self, original: np.ndarray, reconstructed: np.ndarray) -> Dict:
        """Calculate audio quality metrics (MSE, Correlation, SNR)."""
        mse = float(np.mean((original - reconstructed)**2))

        # Correlation coefficient
        if np.std(original) > 0 and np.std(reconstructed) > 0:
            corr = np.corrcoef(original, reconstructed)[0, 1]
            correlation = float(corr) if not np.isnan(corr) else 0.0
        else:
            correlation = 1.0 if mse < 1e-10 else 0.0

        # Signal-to-Noise Ratio
        power_original = np.mean(original**2)
        power_error = np.mean((original - reconstructed)**2)
        if power_error > 1e-15:
            snr = 10 * np.log10(power_original / power_error)
        else:
            snr = 100.0  # Very high SNR for near-perfect reconstruction

        return {
            "mse": mse,
            "correlation": correlation,
            "snr_db": float(snr),
        }

    # =========================================================================
    # Image/Audio Encoding for Web Display
    # =========================================================================

    def _encode_image_base64(self, img_array: np.ndarray) -> str:
        """Convert numpy array to base64 PNG string. Handles both grayscale and RGB."""
        if not HAS_PIL:
            return ""

        # Normalize to 0-255
        img_norm = (np.clip(img_array, 0, 1) * 255).astype(np.uint8)

        # Check if RGB or grayscale
        if img_array.ndim == 3 and img_array.shape[2] == 3:
            img = Image.fromarray(img_norm, mode='RGB')
        else:
            img = Image.fromarray(img_norm, mode='L')

        # Encode to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return f"data:image/png;base64,{base64.b64encode(buffer.read()).decode()}"

    def _encode_magnitude_base64(self, mag_array: np.ndarray) -> str:
        """Convert magnitude spectrum to base64 PNG with vibrant 'inferno' colormap."""
        if not HAS_PIL:
            return ""

        # Log scale for better visualization
        mag_log = np.log10(mag_array + 1e-8)

        # Normalize to 0-1 with enhanced contrast
        mag_min, mag_max = mag_log.min(), mag_log.max()
        if mag_max - mag_min > 0:
            mag_norm = (mag_log - mag_min) / (mag_max - mag_min)
        else:
            mag_norm = np.zeros_like(mag_log)

        # Apply gamma correction for better mid-tone visibility
        mag_norm = np.power(mag_norm, 0.7)

        # Inferno-like colormap (black -> purple -> red -> orange -> yellow)
        # This is more visually striking than basic 'hot'
        img_rgb = np.zeros((mag_array.shape[0], mag_array.shape[1], 3), dtype=np.uint8)

        # Red channel: smooth ramp
        img_rgb[:, :, 0] = np.clip(
            np.where(mag_norm < 0.4,
                     mag_norm * 2.5 * 100,  # Dark to purple
                     100 + (mag_norm - 0.4) * 1.67 * 155),  # Purple to bright
            0, 255).astype(np.uint8)

        # Green channel: delayed ramp
        img_rgb[:, :, 1] = np.clip(
            np.where(mag_norm < 0.3,
                     0,
                     np.where(mag_norm < 0.7,
                              (mag_norm - 0.3) * 2.5 * 180,
                              180 + (mag_norm - 0.7) * 3.33 * 75)),
            0, 255).astype(np.uint8)

        # Blue channel: peaks early then fades
        img_rgb[:, :, 2] = np.clip(
            np.where(mag_norm < 0.25,
                     mag_norm * 4 * 200,
                     np.where(mag_norm < 0.5,
                              200 - (mag_norm - 0.25) * 4 * 200,
                              0)),
            0, 255).astype(np.uint8)

        img = Image.fromarray(img_rgb, mode='RGB')

        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return f"data:image/png;base64,{base64.b64encode(buffer.read()).decode()}"

    def _encode_phase_base64(self, phase_array: np.ndarray) -> str:
        """Convert phase spectrum to base64 PNG with 'twilight' cyclic colormap."""
        if not HAS_PIL:
            return ""

        # Normalize phase from [-π, π] to [0, 1]
        phase_norm = (phase_array + np.pi) / (2 * np.pi)

        # Twilight-like cyclic colormap (purple -> blue -> white -> red -> purple)
        # Better for showing cyclic phase data
        img_rgb = np.zeros((phase_array.shape[0], phase_array.shape[1], 3), dtype=np.uint8)

        # Create smooth cyclic transitions
        # Phase 0 (center): light/white
        # Phase -π/π (edges): dark purple

        # Distance from center (0.5)
        dist_from_center = np.abs(phase_norm - 0.5) * 2  # 0 at center, 1 at edges

        # Red: high in upper half, low in lower half
        img_rgb[:, :, 0] = np.clip(
            np.where(phase_norm > 0.5,
                     100 + 155 * (1 - dist_from_center),  # Bright red in upper-center
                     80 + 100 * (1 - dist_from_center)),   # Muted in lower half
            0, 255).astype(np.uint8)

        # Green: peaks at center (white), low at edges
        img_rgb[:, :, 1] = np.clip(
            200 * (1 - dist_from_center ** 0.8),
            0, 255).astype(np.uint8)

        # Blue: high in lower half, low in upper half
        img_rgb[:, :, 2] = np.clip(
            np.where(phase_norm < 0.5,
                     100 + 155 * (1 - dist_from_center),  # Bright blue in lower-center
                     80 + 100 * (1 - dist_from_center)),   # Muted in upper half
            0, 255).astype(np.uint8)

        # Darken the edges (where phase wraps around)
        edge_darkening = 1 - 0.4 * dist_from_center ** 2
        img_rgb[:, :, 0] = (img_rgb[:, :, 0] * edge_darkening).astype(np.uint8)
        img_rgb[:, :, 1] = (img_rgb[:, :, 1] * edge_darkening).astype(np.uint8)
        img_rgb[:, :, 2] = (img_rgb[:, :, 2] * edge_darkening).astype(np.uint8)

        img = Image.fromarray(img_rgb, mode='RGB')

        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return f"data:image/png;base64,{base64.b64encode(buffer.read()).decode()}"

    def _encode_audio_base64(self, audio_array: np.ndarray) -> str:
        """Convert audio signal to base64 WAV string."""
        if not HAS_WAVFILE:
            return ""

        # Normalize to int16 range
        audio_norm = audio_array / (np.max(np.abs(audio_array)) + 1e-8)
        audio_int16 = (audio_norm * 32767).astype(np.int16)

        # Encode to WAV
        buffer = io.BytesIO()
        wavfile.write(buffer, self.AUDIO_SAMPLE_RATE, audio_int16)
        buffer.seek(0)
        return f"data:audio/wav;base64,{base64.b64encode(buffer.read()).decode()}"

    # =========================================================================
    # Plot generation - Simplified for three-pane layout
    # =========================================================================

    def get_plots(self) -> List[Dict[str, Any]]:
        """Generate minimal plots - main content is in visualization_data."""
        if not self._initialized:
            self.initialize()

        # Just return waveform plots for audio mode
        if self.parameters["analysis_mode"] == "audio":
            return self._get_audio_plots()
        else:
            # For image mode, return empty - images are in visualization_data
            return []

    def _get_audio_plots(self) -> List[Dict[str, Any]]:
        """Generate waveform plots for audio mode."""
        t = np.linspace(0, self.AUDIO_DISPLAY_SAMPLES / self.AUDIO_SAMPLE_RATE,
                        self.AUDIO_DISPLAY_SAMPLES)

        plots = []

        # Audio 1 waveform
        plots.append({
            "id": "audio1_waveform",
            "title": f"Audio 1: {self.parameters['audio1_type'].title()}",
            "data": [{
                "x": t.tolist(),
                "y": self._audio1[:self.AUDIO_DISPLAY_SAMPLES].tolist(),
                "type": "scatter",
                "mode": "lines",
                "line": {"color": self.COLORS["signal1"], "width": 1.5},
                "name": "Audio 1",
            }],
            "layout": {
                "xaxis": {"title": "Time (s)", "range": [0, t[-1]]},
                "yaxis": {"title": "Amplitude", "range": [-1.2, 1.2]},
                "margin": {"l": 50, "r": 20, "t": 40, "b": 40},
                "height": 200,
            },
        })

        # Audio 2 waveform
        plots.append({
            "id": "audio2_waveform",
            "title": f"Audio 2: {self.parameters['audio2_type'].title()}",
            "data": [{
                "x": t.tolist(),
                "y": self._audio2[:self.AUDIO_DISPLAY_SAMPLES].tolist(),
                "type": "scatter",
                "mode": "lines",
                "line": {"color": self.COLORS["signal2"], "width": 1.5},
                "name": "Audio 2",
            }],
            "layout": {
                "xaxis": {"title": "Time (s)", "range": [0, t[-1]]},
                "yaxis": {"title": "Amplitude", "range": [-1.2, 1.2]},
                "margin": {"l": 50, "r": 20, "t": 40, "b": 40},
                "height": 200,
            },
        })

        # Hybrid 1: Magnitude from Audio 1 + Phase from Audio 2
        # Phase determines temporal structure (waveform shape)
        plots.append({
            "id": "hybrid1_waveform",
            "title": f"Hybrid: Mag({self.parameters['audio1_type'].title()}) + Phase({self.parameters['audio2_type'].title()})",
            "data": [{
                "x": t.tolist(),
                "y": self._audio_hybrid1[:self.AUDIO_DISPLAY_SAMPLES].tolist(),
                "type": "scatter",
                "mode": "lines",
                "line": {"color": self.COLORS["hybrid1"], "width": 1.5},
                "name": f"Temporal structure from {self.parameters['audio2_type'].title()}",
            }],
            "layout": {
                "xaxis": {"title": "Time (s)", "range": [0, t[-1]]},
                "yaxis": {"title": "Amplitude", "range": [-1.2, 1.2]},
                "margin": {"l": 50, "r": 20, "t": 40, "b": 40},
                "height": 200,
            },
        })

        # Hybrid 2: Magnitude from Audio 2 + Phase from Audio 1
        # Phase determines temporal structure (waveform shape)
        plots.append({
            "id": "hybrid2_waveform",
            "title": f"Hybrid: Mag({self.parameters['audio2_type'].title()}) + Phase({self.parameters['audio1_type'].title()})",
            "data": [{
                "x": t.tolist(),
                "y": self._audio_hybrid2[:self.AUDIO_DISPLAY_SAMPLES].tolist(),
                "type": "scatter",
                "mode": "lines",
                "line": {"color": self.COLORS["hybrid2"], "width": 1.5},
                "name": f"Temporal structure from {self.parameters['audio1_type'].title()}",
            }],
            "layout": {
                "xaxis": {"title": "Time (s)", "range": [0, t[-1]]},
                "yaxis": {"title": "Amplitude", "range": [-1.2, 1.2]},
                "margin": {"l": 50, "r": 20, "t": 40, "b": 40},
                "height": 200,
            },
        })

        return plots

    # =========================================================================
    # State and Metadata
    # =========================================================================

    def get_computed_values(self) -> Dict[str, Any]:
        """Return computed values."""
        if self.parameters["analysis_mode"] == "image":
            return {
                "image1_metrics": self._image_metrics.get("image1", {}),
                "image2_metrics": self._image_metrics.get("image2", {}),
                "hybrid1_metrics": self._image_metrics.get("hybrid1_to_image2", {}),
                "hybrid2_metrics": self._image_metrics.get("hybrid2_to_image1", {}),
            }
        else:
            return {
                "audio1_metrics": self._audio_metrics.get("audio1", {}),
                "audio2_metrics": self._audio_metrics.get("audio2", {}),
                "hybrid1_metrics": self._audio_metrics.get("hybrid1_to_audio2", {}),
                "hybrid2_metrics": self._audio_metrics.get("hybrid2_to_audio1", {}),
            }

    def get_state(self) -> Dict[str, Any]:
        """Return current simulation state with visualization data."""
        state = super().get_state()
        state["computed_values"] = self.get_computed_values()

        mode = self.parameters["analysis_mode"]

        # Build visualization data for the dedicated component
        if mode == "image":
            visualization_data = self._build_image_visualization_data()
        else:
            visualization_data = self._build_audio_visualization_data()

        state["metadata"] = {
            "simulation_type": "fourier_phase_vs_magnitude",
            "sticky_controls": True,
            "analysis_mode": mode,
            "has_custom_viewer": True,  # Signal to use custom component
            "system_info": self._build_system_info(mode),
            "visualization_data": visualization_data,
        }

        return state

    def _build_image_visualization_data(self) -> Dict:
        """Build image visualization data with base64 encoded images."""
        # Send processed magnitude/phase (which shows uniform values when mode is applied)
        return {
            "type": "image",
            "source1": {
                "name": self.parameters["image1_pattern"].title(),
                "mode": self.parameters["image1_mode"],
                "original": self._encode_image_base64(self._image1),
                "magnitude": self._encode_magnitude_base64(self._mag1_processed),
                "phase": self._encode_phase_base64(self._phase1_processed),
                "reconstructed": self._encode_image_base64(self._recon1),
                "metrics": self._image_metrics.get("image1", {}),
            },
            "source2": {
                "name": self.parameters["image2_pattern"].title(),
                "mode": self.parameters["image2_mode"],
                "original": self._encode_image_base64(self._image2),
                "magnitude": self._encode_magnitude_base64(self._mag2_processed),
                "phase": self._encode_phase_base64(self._phase2_processed),
                "reconstructed": self._encode_image_base64(self._recon2),
                "metrics": self._image_metrics.get("image2", {}),
            },
            "hybrids": {
                "mag1_phase2": {
                    "image": self._encode_image_base64(self._hybrid_mag1_phase2),
                    "label": "Mag₁ + Phase₂",
                    "insight": "Looks like Image 2!",
                    "correlation_to_source": self._image_metrics.get("hybrid1_to_image2", {}).get("correlation", 0),
                },
                "mag2_phase1": {
                    "image": self._encode_image_base64(self._hybrid_mag2_phase1),
                    "label": "Mag₂ + Phase₁",
                    "insight": "Looks like Image 1!",
                    "correlation_to_source": self._image_metrics.get("hybrid2_to_image1", {}).get("correlation", 0),
                },
            },
        }

    def _build_audio_visualization_data(self) -> Dict:
        """Build audio visualization data with base64 encoded audio."""
        return {
            "type": "audio",
            "source1": {
                "name": self.parameters["audio1_type"].title(),
                "audio": self._encode_audio_base64(self._audio1),
                "metrics": self._audio_metrics.get("audio1", {}),
            },
            "source2": {
                "name": self.parameters["audio2_type"].title(),
                "audio": self._encode_audio_base64(self._audio2),
                "metrics": self._audio_metrics.get("audio2", {}),
            },
            "hybrids": {
                "mag1_phase2": {
                    # Phase determines temporal structure (waveform shape)
                    # Both magnitude and phase contribute to perception
                    "audio": self._encode_audio_base64(self._audio_hybrid1),
                    "label": "Mag₁ + Phase₂",
                    "insight": "Waveform shape from Audio 2",
                    "correlation": self._audio_metrics.get("hybrid1_to_audio2", {}).get("correlation", 0),
                },
                "mag2_phase1": {
                    # Phase from Audio 1 shapes the temporal structure
                    "audio": self._encode_audio_base64(self._audio_hybrid2),
                    "label": "Mag₂ + Phase₁",
                    "insight": "Waveform shape from Audio 1",
                    "correlation": self._audio_metrics.get("hybrid2_to_audio1", {}).get("correlation", 0),
                },
            },
        }

    def _build_system_info(self, mode: str) -> Dict:
        """Build system info for info panel."""
        if mode == "image":
            m1 = self._image_metrics.get("image1", {})
            m2 = self._image_metrics.get("image2", {})
            h1 = self._image_metrics.get("hybrid1_to_image2", {})
            h2 = self._image_metrics.get("hybrid2_to_image1", {})

            return {
                "mode": "Image Analysis",
                "image1_pattern": self.parameters["image1_pattern"].title(),
                "image2_pattern": self.parameters["image2_pattern"].title(),
                "image1_mode": self.parameters["image1_mode"].replace("_", " ").title(),
                "image2_mode": self.parameters["image2_mode"].replace("_", " ").title(),
                "image_size": f"{self.IMAGE_SIZE}×{self.IMAGE_SIZE}",

                # Image 1 metrics
                "image1_mse": f"{m1.get('mse', 0):.6f}",
                "image1_correlation": f"{m1.get('correlation', 0):.4f}",
                "image1_ssim": f"{m1.get('ssim', 0):.4f}",

                # Image 2 metrics
                "image2_mse": f"{m2.get('mse', 0):.6f}",
                "image2_correlation": f"{m2.get('correlation', 0):.4f}",
                "image2_ssim": f"{m2.get('ssim', 0):.4f}",

                # Hybrid metrics (the key insight!)
                "hybrid1_correlation": f"{h1.get('correlation', 0):.4f}",
                "hybrid2_correlation": f"{h2.get('correlation', 0):.4f}",

                # Key insight message
                "insight": "Phase carries structural information! Hybrid images resemble the image whose PHASE they use.",
            }
        else:
            m1 = self._audio_metrics.get("audio1", {})
            m2 = self._audio_metrics.get("audio2", {})
            h1 = self._audio_metrics.get("hybrid1_to_audio2", {})
            h2 = self._audio_metrics.get("hybrid2_to_audio1", {})

            return {
                "mode": "Audio Analysis",
                "audio1_type": self.parameters["audio1_type"].title(),
                "audio2_type": self.parameters["audio2_type"].title(),
                "sample_rate": f"{self.AUDIO_SAMPLE_RATE} Hz",
                "duration": f"{self.AUDIO_DURATION} s",

                # Audio 1 metrics
                "audio1_mse": f"{m1.get('mse', 0):.6f}",
                "audio1_correlation": f"{m1.get('correlation', 0):.4f}",
                "audio1_snr": f"{m1.get('snr_db', 0):.1f} dB",

                # Audio 2 metrics
                "audio2_mse": f"{m2.get('mse', 0):.6f}",
                "audio2_correlation": f"{m2.get('correlation', 0):.4f}",
                "audio2_snr": f"{m2.get('snr_db', 0):.1f} dB",

                # Hybrid metrics
                "hybrid1_correlation": f"{h1.get('correlation', 0):.4f}",
                "hybrid2_correlation": f"{h2.get('correlation', 0):.4f}",

                # Key insight message
                "insight": "Phase carries temporal structure! Hybrid signals inherit timing from the phase source.",
            }
