"""
Lens Optics Simulator - Web Version

Exactly matches PyQt5 version (lens_optics/optics/lens_model.py and lens_optics/gui)
Models optical systems using point spread functions (PSF).
Demonstrates diffraction-limited imaging and atmospheric seeing effects.
"""

import numpy as np
from scipy.special import j1  # Bessel function of first kind
from scipy.signal import fftconvolve
from typing import Any, Dict, List, Optional
from .base_simulator import BaseSimulator
import base64
import io


class LensOpticsSimulator(BaseSimulator):
    """
    Lens Optics simulation with PSF modeling.
    Matches PyQt5 version exactly.
    """

    # Configuration (matching PyQt5)
    IMAGE_SIZE = 256  # Larger for better quality
    PSF_GRID_SIZE = 256

    # Colors (matching PyQt5)
    COLOR_ORIGINAL = "#00A0FF"
    COLOR_BLURRED = "#FF5733"
    COLOR_PSF = "Hot"
    COLOR_MTF = "#3b82f6"
    COLOR_CROSS_SECTION = "#22c55e"

    # Parameter defaults (matching PyQt5 exactly)
    DEFAULT_PARAMS = {
        "diameter": 100.0,        # mm (PyQt5: 100mm default)
        "focal_length": 500.0,    # mm (PyQt5: 500mm default)
        "wavelength": 550.0,      # nm (PyQt5: 550nm green light)
        "pixel_size": 1.0,        # μm (PyQt5: 1μm default)
        "psf_size": 256,          # grid size
        "enable_atmosphere": False,
        "atmospheric_seeing": 1.5,  # arcsec (PyQt5: 1.5 default)
        "test_pattern": "edge_target",
    }

    def __init__(self, simulation_id: str):
        super().__init__(simulation_id)
        self._psf = None
        self._original_image = None
        self._blurred_image = None
        self._psf_metrics = {}
        self._quality_metrics = {}
        self._lens_metrics = {}
        self._psf_extent = None
        self._airy_radius = None

    def initialize(self, params: Optional[Dict[str, Any]] = None) -> None:
        """Initialize simulation with parameters."""
        self.parameters = self.DEFAULT_PARAMS.copy()
        if params:
            for name, value in params.items():
                if name in self.parameters:
                    self.parameters[name] = value
        self._initialized = True
        self._compute()

    def update_parameter(self, name: str, value: Any) -> Dict[str, Any]:
        """Update a single parameter and recompute."""
        if name in self.parameters:
            self.parameters[name] = value
            self._compute()
        return self.get_state()

    def reset(self) -> Dict[str, Any]:
        """Reset simulation to default parameters."""
        self.parameters = self.DEFAULT_PARAMS.copy()
        self._initialized = True
        self._compute()
        return self.get_state()

    def _compute(self) -> None:
        """Compute PSF, blur image, and calculate metrics."""
        # Extract parameters (convert units to SI)
        diameter_m = self.parameters["diameter"] * 1e-3  # mm to m
        focal_length_m = self.parameters["focal_length"] * 1e-3  # mm to m
        wavelength_m = self.parameters["wavelength"] * 1e-9  # nm to m
        pixel_size_m = self.parameters["pixel_size"] * 1e-6  # μm to m
        psf_size = self.parameters["psf_size"]
        enable_atmosphere = self.parameters["enable_atmosphere"]
        seeing_arcsec = self.parameters["atmospheric_seeing"]
        pattern = self.parameters["test_pattern"]

        # Generate test pattern
        self._original_image = self._generate_test_pattern(pattern, self.IMAGE_SIZE)

        # Compute PSF
        if enable_atmosphere and seeing_arcsec > 0:
            self._psf, self._psf_extent = self._combined_psf(
                diameter_m, focal_length_m, wavelength_m, pixel_size_m,
                seeing_arcsec, psf_size
            )
        else:
            self._psf, self._psf_extent, self._airy_radius = self._airy_disk_psf(
                diameter_m, focal_length_m, wavelength_m, pixel_size_m, psf_size
            )

        # Resize PSF for convolution
        psf_resized = self._match_psf_size(self._psf, self.IMAGE_SIZE)

        # Apply PSF (convolve)
        self._blurred_image = self._convolve_with_psf(
            self._original_image, psf_resized
        )

        # Calculate all metrics
        self._psf_metrics = self._calculate_psf_metrics(self._psf, pixel_size_m)
        self._quality_metrics = self._calculate_quality_metrics(
            self._original_image, self._blurred_image
        )
        self._lens_metrics = self._calculate_lens_metrics(
            diameter_m, focal_length_m, wavelength_m
        )

    def _airy_disk_psf(self, diameter: float, focal_length: float,
                       wavelength: float, pixel_size: float, grid_size: int):
        """
        Generate Airy disk point spread function for circular aperture.
        Matches PyQt5: lens_model.py:airy_disk_psf()
        """
        x = np.linspace(-grid_size//2, grid_size//2-1, grid_size) * pixel_size
        y = np.linspace(-grid_size//2, grid_size//2-1, grid_size) * pixel_size
        X, Y = np.meshgrid(x, y)
        R = np.sqrt(X**2 + Y**2)

        # First zero of Airy pattern: r = 1.22 * lambda * f / D
        airy_radius = 1.22 * wavelength * focal_length / diameter

        # Airy pattern: I = (2*J1(beta)/beta)^2
        with np.errstate(divide='ignore', invalid='ignore'):
            beta = np.pi * diameter * R / (wavelength * focal_length)
            airy = np.where(beta == 0, 1.0, (2 * j1(beta) / beta)**2)

        airy = airy / np.max(airy)  # Normalize to peak of 1

        # Create extent in micrometers
        extent = [
            -grid_size//2 * pixel_size * 1e6,
            grid_size//2 * pixel_size * 1e6,
            -grid_size//2 * pixel_size * 1e6,
            grid_size//2 * pixel_size * 1e6
        ]

        return airy.astype(np.float32), extent, airy_radius

    def _gaussian_psf(self, sigma_um: float, pixel_size: float, grid_size: int):
        """Generate Gaussian PSF (atmospheric seeing limited)."""
        # Create coordinate grid in micrometers
        pixel_size_um = pixel_size * 1e6
        x_um = np.linspace(-grid_size//2, grid_size//2-1, grid_size) * pixel_size_um
        y_um = np.linspace(-grid_size//2, grid_size//2-1, grid_size) * pixel_size_um
        X, Y = np.meshgrid(x_um, y_um)
        R_squared = X**2 + Y**2

        psf = np.exp(-R_squared / (2 * sigma_um**2))
        psf = psf / np.sum(psf)  # Normalize

        extent = [
            -grid_size//2 * pixel_size_um,
            grid_size//2 * pixel_size_um,
            -grid_size//2 * pixel_size_um,
            grid_size//2 * pixel_size_um
        ]

        return psf.astype(np.float32), extent

    def _combined_psf(self, diameter: float, focal_length: float, wavelength: float,
                      pixel_size: float, seeing_arcsec: float, grid_size: int):
        """
        Generate combined PSF including both diffraction and atmospheric seeing.
        Matches PyQt5: lens_model.py:combined_psf()
        """
        # Diffraction-limited Airy disk
        airy, extent, _ = self._airy_disk_psf(
            diameter, focal_length, wavelength, pixel_size, grid_size
        )

        # Convert seeing from arcseconds to physical size
        seeing_rad = seeing_arcsec * (np.pi / 180) / 3600
        seeing_physical = seeing_rad * focal_length  # meters
        seeing_um = seeing_physical * 1e6  # micrometers

        # Convert FWHM to sigma
        sigma_um = seeing_um / (2 * np.sqrt(2 * np.log(2)))

        # Generate atmospheric PSF
        atmo_psf, _ = self._gaussian_psf(sigma_um, pixel_size, grid_size)

        # Convolve diffraction PSF with atmospheric PSF
        combined = fftconvolve(airy, atmo_psf, mode='same')
        combined = combined / np.sum(combined)

        return combined.astype(np.float32), extent

    def _generate_test_pattern(self, pattern_type: str, size: int) -> np.ndarray:
        """
        Generate test images for simulation.
        Matches PyQt5: image_ops.py
        """
        if pattern_type == "resolution_chart":
            return self._generate_resolution_chart(size)
        elif pattern_type == "point_sources":
            return self._generate_point_sources(size)
        elif pattern_type == "edge_target":
            return self._generate_edge_target(size)
        elif pattern_type == "star_field":
            return self._generate_star_field(size)
        else:
            return self._generate_resolution_chart(size)

    def _generate_resolution_chart(self, size: int) -> np.ndarray:
        """Generate resolution test chart with varying spatial frequencies."""
        img = np.zeros((size, size))
        center = size // 2

        y, x = np.ogrid[:size, :size]
        r = np.sqrt((x - center)**2 + (y - center)**2)
        r_norm = r / (size // 2)

        # Radial frequency pattern
        freq = r_norm * 20
        radial_pattern = np.sin(2 * np.pi * freq)

        # Angular patterns (spokes)
        theta = np.arctan2(y - center, x - center)
        angular_pattern = np.sin(8 * theta)

        # Combine patterns
        img = 0.5 + 0.3 * radial_pattern + 0.2 * angular_pattern

        # Add high-frequency details
        fine_pattern = np.sin(2 * np.pi * r_norm * 50) * np.exp(-r_norm * 2)
        img += 0.1 * fine_pattern

        return np.clip(img, 0, 1).astype(np.float32)

    def _generate_point_sources(self, size: int) -> np.ndarray:
        """Generate point sources for PSF testing."""
        img = np.zeros((size, size))

        points = [
            (size//4, size//4),
            (size//4, 3*size//4),
            (3*size//4, size//4),
            (3*size//4, 3*size//4),
            (size//2, size//2),
            (size//8, size//2),
            (7*size//8, size//2),
            (size//2, size//8),
            (size//2, 7*size//8)
        ]

        for y, x in points:
            if 0 <= y < size and 0 <= x < size:
                img[y, x] = 1.0

        return img.astype(np.float32)

    def _generate_edge_target(self, size: int) -> np.ndarray:
        """Generate sharp edge target for MTF testing."""
        img = np.zeros((size, size))

        # Vertical edge
        img[:, :size//2] = 0.3
        img[:, size//2:] = 0.7

        # Horizontal edges
        img[:size//4, :] = 0.2
        img[3*size//4:, :] = 0.8

        # Diagonal edges
        for i in range(size):
            for j in range(size):
                if i + j > size:
                    img[i, j] = max(img[i, j], 0.6)
                if abs(i - j) < size // 10:
                    img[i, j] = 0.9

        return img.astype(np.float32)

    def _generate_star_field(self, size: int) -> np.ndarray:
        """Generate star field for astronomical simulation."""
        np.random.seed(42)
        img = np.zeros((size, size))

        n_stars = 50
        for _ in range(n_stars):
            x = np.random.randint(0, size)
            y = np.random.randint(0, size)
            brightness = np.random.uniform(0.3, 1.0)
            sigma = np.random.uniform(0.5, 2.0)

            for dy in range(-3, 4):
                for dx in range(-3, 4):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < size and 0 <= nx < size:
                        distance = np.sqrt(dx**2 + dy**2)
                        value = brightness * np.exp(-distance**2 / (2 * sigma**2))
                        img[ny, nx] = max(img[ny, nx], value)

        return img.astype(np.float32)

    def _match_psf_size(self, psf: np.ndarray, target_size: int) -> np.ndarray:
        """Resize PSF to match image size."""
        current_size = psf.shape[0]

        if current_size == target_size:
            return psf
        elif current_size > target_size:
            # Crop PSF
            start = (current_size - target_size) // 2
            return psf[start:start+target_size, start:start+target_size]
        else:
            # Pad PSF
            pad_size = (target_size - current_size) // 2
            padded = np.pad(psf, pad_size, mode='constant', constant_values=0)
            if padded.shape[0] < target_size:
                padded = np.pad(padded, ((0, 1), (0, 1)), mode='constant')
            elif padded.shape[0] > target_size:
                padded = padded[:target_size, :target_size]
            return padded

    def _convolve_with_psf(self, image: np.ndarray, psf: np.ndarray) -> np.ndarray:
        """Convolve image with PSF."""
        psf_normalized = psf / np.sum(psf)
        blurred = fftconvolve(image, psf_normalized, mode='same')
        return np.clip(blurred, 0, 1).astype(np.float32)

    def _calculate_psf_metrics(self, psf: np.ndarray, pixel_size_m: float) -> Dict:
        """
        Calculate PSF quality metrics.
        Matches PyQt5: lens_model.py:psf_metrics()
        """
        metrics = {}

        # Find PSF center
        center_y, center_x = np.unravel_index(np.argmax(psf), psf.shape)

        # Peak intensity
        metrics['peak_intensity'] = float(np.max(psf))

        # Calculate FWHM
        half_max = metrics['peak_intensity'] / 2
        h_profile = psf[center_y, :]
        v_profile = psf[:, center_x]

        h_indices = np.where(h_profile >= half_max)[0]
        v_indices = np.where(v_profile >= half_max)[0]

        h_fwhm = len(h_indices) if len(h_indices) > 0 else 1
        v_fwhm = len(v_indices) if len(v_indices) > 0 else 1

        fwhm_pixels = (h_fwhm + v_fwhm) / 2
        metrics['fwhm_pixels'] = float(fwhm_pixels)
        metrics['fwhm_um'] = float(fwhm_pixels * pixel_size_m * 1e6)

        # Calculate encircled energy
        total_energy = np.sum(psf)
        y, x = np.ogrid[:psf.shape[0], :psf.shape[1]]
        distances = np.sqrt((x - center_x)**2 + (y - center_y)**2)

        max_radius = min(center_x, center_y, psf.shape[1] - center_x, psf.shape[0] - center_y)
        max_radius = max(1, int(max_radius))
        radii = np.arange(1, max_radius + 1)

        encircled_energies = []
        for r in radii:
            mask = distances <= r
            energy = np.sum(psf[mask])
            encircled_energies.append(energy / total_energy)

        encircled_energies = np.array(encircled_energies)

        # EE50 and EE80
        ee50_idx = np.argmax(encircled_energies >= 0.5) if np.any(encircled_energies >= 0.5) else len(radii) - 1
        ee80_idx = np.argmax(encircled_energies >= 0.8) if np.any(encircled_energies >= 0.8) else len(radii) - 1

        metrics['ee50_radius_pixels'] = float(radii[ee50_idx]) if ee50_idx < len(radii) else float(max_radius)
        metrics['ee50_radius_um'] = float(metrics['ee50_radius_pixels'] * pixel_size_m * 1e6)
        metrics['ee80_radius_pixels'] = float(radii[ee80_idx]) if ee80_idx < len(radii) else float(max_radius)
        metrics['ee80_radius_um'] = float(metrics['ee80_radius_pixels'] * pixel_size_m * 1e6)

        # Strehl ratio
        metrics['strehl_ratio'] = float(metrics['peak_intensity'])

        # Store encircled energy curve data
        metrics['ee_radii'] = radii.tolist()[:50]  # Limit for JSON
        metrics['ee_values'] = encircled_energies.tolist()[:50]

        # Cross-section data
        center = psf.shape[0] // 2
        metrics['cross_section_h'] = psf[center, :].tolist()
        metrics['cross_section_v'] = psf[:, center].tolist()

        return metrics

    def _calculate_quality_metrics(self, original: np.ndarray,
                                    blurred: np.ndarray) -> Dict:
        """
        Calculate image quality metrics.
        Matches PyQt5: image_ops.py:calculate_image_quality_metrics()
        """
        # MSE
        mse = float(np.mean((original - blurred)**2))

        # PSNR
        if mse > 0:
            psnr = float(20 * np.log10(1.0 / np.sqrt(mse)))
        else:
            psnr = float('inf')

        # SSIM (simplified)
        mu1, mu2 = np.mean(original), np.mean(blurred)
        sigma1, sigma2 = np.var(original), np.var(blurred)
        sigma12 = np.mean((original - mu1) * (blurred - mu2))

        c1, c2 = 0.01**2, 0.03**2
        ssim = float(((2*mu1*mu2 + c1)*(2*sigma12 + c2)) /
                     ((mu1**2 + mu2**2 + c1)*(sigma1 + sigma2 + c2)))

        # Contrast reduction
        orig_contrast = float(np.std(original))
        blur_contrast = float(np.std(blurred))
        contrast_reduction = float(1 - (blur_contrast / orig_contrast)) if orig_contrast > 0 else 0.0

        # Edge preservation (using Sobel-like operator)
        def simple_edges(img):
            gx = np.diff(img, axis=1, prepend=img[:, :1])
            gy = np.diff(img, axis=0, prepend=img[:1, :])
            return np.sqrt(gx**2 + gy**2)

        orig_edges = simple_edges(original)
        blur_edges = simple_edges(blurred)
        edge_corr = np.corrcoef(orig_edges.flatten(), blur_edges.flatten())[0, 1]
        edge_preservation = float(edge_corr) if not np.isnan(edge_corr) else 0.0

        return {
            'mse': mse,
            'psnr': psnr,
            'ssim': ssim,
            'contrast_reduction': contrast_reduction,
            'edge_preservation': edge_preservation
        }

    def _calculate_lens_metrics(self, diameter: float, focal_length: float,
                                 wavelength: float) -> Dict:
        """Calculate lens optical metrics."""
        f_number = focal_length / diameter
        numerical_aperture = diameter / (2 * focal_length)
        airy_radius_m = 1.22 * wavelength * focal_length / diameter
        rayleigh_limit = 1.22 * wavelength / diameter

        return {
            'f_number': float(f_number),
            'numerical_aperture': float(numerical_aperture),
            'airy_radius_um': float(airy_radius_m * 1e6),
            'rayleigh_limit_rad': float(rayleigh_limit),
            'rayleigh_limit_arcsec': float(rayleigh_limit * 206265)
        }

    def _image_to_base64(self, image: np.ndarray, colormap: str = 'gray') -> str:
        """Convert image array to base64 data URL."""
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(4, 4), dpi=100)
        ax.imshow(image, cmap=colormap, vmin=0, vmax=1)
        ax.axis('off')
        fig.tight_layout(pad=0)

        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0,
                   facecolor='#1e293b', edgecolor='none')
        plt.close(fig)
        buf.seek(0)

        b64 = base64.b64encode(buf.read()).decode('utf-8')
        return f"data:image/png;base64,{b64}"

    def _psf_to_base64(self, psf: np.ndarray) -> str:
        """Convert PSF to base64 (log scale, hot colormap)."""
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        # Zoom to central region
        center = psf.shape[0] // 2
        zoom_size = psf.shape[0] // 4
        psf_zoomed = psf[center-zoom_size:center+zoom_size, center-zoom_size:center+zoom_size]

        fig, ax = plt.subplots(figsize=(4, 4), dpi=100)
        ax.imshow(np.log10(psf_zoomed + 1e-10), cmap='hot')
        ax.axis('off')
        fig.tight_layout(pad=0)

        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0,
                   facecolor='#1e293b', edgecolor='none')
        plt.close(fig)
        buf.seek(0)

        b64 = base64.b64encode(buf.read()).decode('utf-8')
        return f"data:image/png;base64,{b64}"

    # =========================================================================
    # Plot generation
    # =========================================================================

    def get_plots(self) -> List[Dict[str, Any]]:
        """Generate Plotly plot dictionaries."""
        if not self._initialized:
            self.initialize()

        plots = [
            self._create_original_image_plot(),
            self._create_blurred_image_plot(),
            self._create_psf_plot(),
            self._create_cross_section_plot(),
            self._create_encircled_energy_plot(),
            self._create_mtf_plot(),
        ]
        return plots

    def _create_original_image_plot(self) -> Dict[str, Any]:
        """Create original image plot."""
        return {
            "id": "original_image",
            "title": "Original Image",
            "data": [{
                "z": self._original_image.tolist(),
                "type": "heatmap",
                "colorscale": "Greys",
                "showscale": False,
            }],
            "layout": {
                "xaxis": {"showticklabels": False, "showgrid": False, "zeroline": False},
                "yaxis": {"showticklabels": False, "showgrid": False, "zeroline": False, "scaleanchor": "x"},
                "margin": {"l": 10, "r": 10, "t": 40, "b": 10},
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)",
                "uirevision": "constant",
            },
        }

    def _create_blurred_image_plot(self) -> Dict[str, Any]:
        """Create blurred image plot."""
        return {
            "id": "blurred_image",
            "title": f"Blurred Image | f/{self._lens_metrics.get('f_number', 0):.1f}",
            "data": [{
                "z": self._blurred_image.tolist(),
                "type": "heatmap",
                "colorscale": "Greys",
                "showscale": False,
            }],
            "layout": {
                "xaxis": {"showticklabels": False, "showgrid": False, "zeroline": False},
                "yaxis": {"showticklabels": False, "showgrid": False, "zeroline": False, "scaleanchor": "x"},
                "margin": {"l": 10, "r": 10, "t": 40, "b": 10},
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)",
                "uirevision": "constant",
            },
        }

    def _create_psf_plot(self) -> Dict[str, Any]:
        """Create PSF visualization (log scale)."""
        # Zoom to central region
        center = self._psf.shape[0] // 2
        zoom_size = self._psf.shape[0] // 4
        psf_zoomed = self._psf[center-zoom_size:center+zoom_size, center-zoom_size:center+zoom_size]

        airy_radius = self._lens_metrics.get('airy_radius_um', 0)

        return {
            "id": "psf",
            "title": f"Point Spread Function (Airy: {airy_radius:.2f} μm)",
            "data": [{
                "z": np.log10(psf_zoomed + 1e-10).tolist(),
                "type": "heatmap",
                "colorscale": "Hot",
                "showscale": True,
                "colorbar": {"title": "log(I)", "len": 0.8},
            }],
            "layout": {
                "xaxis": {"showticklabels": False, "showgrid": False, "zeroline": False},
                "yaxis": {"showticklabels": False, "showgrid": False, "zeroline": False, "scaleanchor": "x"},
                "margin": {"l": 10, "r": 60, "t": 40, "b": 10},
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)",
                "uirevision": "constant",
            },
        }

    def _create_cross_section_plot(self) -> Dict[str, Any]:
        """Create PSF cross-section plot."""
        center = self._psf.shape[0] // 2
        pixel_size_um = self.parameters["pixel_size"]

        # Create position axis in micrometers
        positions = (np.arange(self._psf.shape[0]) - center) * pixel_size_um

        h_profile = self._psf[center, :]
        v_profile = self._psf[:, center]

        return {
            "id": "cross_section",
            "title": "PSF Cross-Section",
            "data": [
                {
                    "x": positions.tolist(),
                    "y": h_profile.tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "name": "Horizontal",
                    "line": {"color": self.COLOR_ORIGINAL, "width": 2},
                },
                {
                    "x": positions.tolist(),
                    "y": v_profile.tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "name": "Vertical",
                    "line": {"color": self.COLOR_CROSS_SECTION, "width": 2},
                },
            ],
            "layout": {
                "xaxis": {
                    "title": "Position (μm)",
                    "showgrid": True,
                    "gridcolor": "rgba(148, 163, 184, 0.1)",
                },
                "yaxis": {
                    "title": "Intensity",
                    "showgrid": True,
                    "gridcolor": "rgba(148, 163, 184, 0.1)",
                },
                "legend": {"orientation": "h", "y": 1.1},
                "margin": {"l": 60, "r": 20, "t": 40, "b": 50},
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)",
                "uirevision": "constant",
            },
        }

    def _create_encircled_energy_plot(self) -> Dict[str, Any]:
        """Create encircled energy plot."""
        ee_radii = self._psf_metrics.get('ee_radii', [])
        ee_values = self._psf_metrics.get('ee_values', [])
        pixel_size_um = self.parameters["pixel_size"]

        # Convert to micrometers
        radii_um = [r * pixel_size_um for r in ee_radii]

        return {
            "id": "encircled_energy",
            "title": "Encircled Energy",
            "data": [
                {
                    "x": radii_um,
                    "y": ee_values,
                    "type": "scatter",
                    "mode": "lines",
                    "name": "EE",
                    "line": {"color": "#a855f7", "width": 2.5},
                    "fill": "tozeroy",
                    "fillcolor": "rgba(168, 85, 247, 0.2)",
                },
                # 50% line
                {
                    "x": [0, radii_um[-1] if radii_um else 1],
                    "y": [0.5, 0.5],
                    "type": "scatter",
                    "mode": "lines",
                    "name": "50%",
                    "line": {"color": "#fbbf24", "width": 1.5, "dash": "dash"},
                },
                # 80% line
                {
                    "x": [0, radii_um[-1] if radii_um else 1],
                    "y": [0.8, 0.8],
                    "type": "scatter",
                    "mode": "lines",
                    "name": "80%",
                    "line": {"color": "#22c55e", "width": 1.5, "dash": "dash"},
                },
            ],
            "layout": {
                "xaxis": {
                    "title": "Radius (μm)",
                    "showgrid": True,
                    "gridcolor": "rgba(148, 163, 184, 0.1)",
                },
                "yaxis": {
                    "title": "Encircled Energy",
                    "showgrid": True,
                    "gridcolor": "rgba(148, 163, 184, 0.1)",
                    "range": [0, 1.05],
                },
                "legend": {"orientation": "h", "y": 1.1},
                "margin": {"l": 60, "r": 20, "t": 40, "b": 50},
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)",
                "uirevision": "constant",
            },
        }

    def _create_mtf_plot(self) -> Dict[str, Any]:
        """Create MTF curve plot."""
        # Compute MTF from PSF
        otf = np.fft.fft2(self._psf)
        otf = np.fft.fftshift(otf)
        mtf = np.abs(otf)

        center = self._psf.shape[0] // 2
        mtf_profile = mtf[center, center:]
        mtf_profile = mtf_profile / mtf_profile[0]

        # Frequency axis in cycles/mm
        pixel_size_m = self.parameters["pixel_size"] * 1e-6
        freq_sampling = 1.0 / (pixel_size_m * self._psf.shape[0])
        freq = np.arange(len(mtf_profile)) * freq_sampling / 1000  # cycles/mm

        return {
            "id": "mtf",
            "title": "Modulation Transfer Function",
            "data": [
                {
                    "x": freq.tolist(),
                    "y": mtf_profile.tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "name": "MTF",
                    "line": {"color": self.COLOR_MTF, "width": 2.5},
                },
                {
                    "x": [0, freq[-1]],
                    "y": [0.5, 0.5],
                    "type": "scatter",
                    "mode": "lines",
                    "name": "50% MTF",
                    "line": {"color": "#ef4444", "width": 1.5, "dash": "dash"},
                },
            ],
            "layout": {
                "xaxis": {
                    "title": "Spatial Frequency (cycles/mm)",
                    "showgrid": True,
                    "gridcolor": "rgba(148, 163, 184, 0.1)",
                },
                "yaxis": {
                    "title": "MTF",
                    "showgrid": True,
                    "gridcolor": "rgba(148, 163, 184, 0.1)",
                    "range": [0, 1.1],
                },
                "legend": {"orientation": "h", "y": 1.1},
                "margin": {"l": 60, "r": 20, "t": 40, "b": 50},
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)",
                "uirevision": "constant",
            },
        }

    def get_state(self) -> Dict[str, Any]:
        """Get complete simulation state with enhanced metadata."""
        base_state = super().get_state()

        # Pattern labels
        pattern_labels = {
            'resolution_chart': 'Resolution Chart',
            'point_sources': 'Point Sources',
            'edge_target': 'Edge Target',
            'star_field': 'Star Field'
        }

        # Generate image data URLs for display
        original_image_url = self._image_to_base64(self._original_image)
        blurred_image_url = self._image_to_base64(self._blurred_image)
        psf_image_url = self._psf_to_base64(self._psf)

        base_state["metadata"] = {
            "simulation_type": "lens_optics",
            "sticky_controls": True,

            # Images for display
            "images": {
                "original": original_image_url,
                "blurred": blurred_image_url,
                "psf": psf_image_url,
            },

            # Current test pattern
            "test_pattern": pattern_labels.get(
                self.parameters["test_pattern"],
                self.parameters["test_pattern"]
            ),

            # Lens parameters (converted for display)
            "lens_info": {
                "diameter_mm": self.parameters["diameter"],
                "focal_length_mm": self.parameters["focal_length"],
                "wavelength_nm": self.parameters["wavelength"],
                "f_number": round(self._lens_metrics.get("f_number", 0), 1),
                "numerical_aperture": round(self._lens_metrics.get("numerical_aperture", 0), 4),
                "airy_radius_um": round(self._lens_metrics.get("airy_radius_um", 0), 2),
                "rayleigh_limit_arcsec": round(self._lens_metrics.get("rayleigh_limit_arcsec", 0), 3),
            },

            # PSF metrics
            "psf_metrics": {
                "fwhm_um": round(self._psf_metrics.get("fwhm_um", 0), 2),
                "ee50_um": round(self._psf_metrics.get("ee50_radius_um", 0), 2),
                "ee80_um": round(self._psf_metrics.get("ee80_radius_um", 0), 2),
                "peak_intensity": round(self._psf_metrics.get("peak_intensity", 0), 4),
                "strehl_ratio": round(self._psf_metrics.get("strehl_ratio", 0), 4),
            },

            # Image quality metrics
            "quality_metrics": {
                "mse": round(self._quality_metrics.get("mse", 0), 6),
                "psnr": round(self._quality_metrics.get("psnr", 0), 1) if self._quality_metrics.get("psnr", 0) < 100 else "∞",
                "ssim": round(self._quality_metrics.get("ssim", 0), 4),
                "contrast_reduction": round(self._quality_metrics.get("contrast_reduction", 0) * 100, 1),
                "edge_preservation": round(self._quality_metrics.get("edge_preservation", 0), 4),
            },

            # Atmosphere status
            "atmosphere_enabled": self.parameters["enable_atmosphere"],
            "seeing_arcsec": self.parameters["atmospheric_seeing"] if self.parameters["enable_atmosphere"] else None,

            # Quality assessment
            "quality_assessment": self._get_quality_assessment(),
        }

        return base_state

    def _get_quality_assessment(self) -> str:
        """Generate quality assessment text."""
        ssim = self._quality_metrics.get("ssim", 0)
        fwhm = self._psf_metrics.get("fwhm_um", 0)
        airy = self._lens_metrics.get("airy_radius_um", 0)

        # Quality grade
        if ssim > 0.95:
            quality = "Excellent"
        elif ssim > 0.85:
            quality = "Good"
        elif ssim > 0.7:
            quality = "Moderate"
        else:
            quality = "Degraded"

        # Diffraction status
        if fwhm <= airy * 2:
            diffraction = "Diffraction-limited"
        else:
            diffraction = "Seeing-limited"

        return f"{quality} | {diffraction}"
