"""
Lens Optics and Point Spread Function Module
Handles calculation of optical point spread functions and lens physics
"""

import numpy as np
from scipy.special import j1  # Bessel function of first kind
from scipy import ndimage

class LensModel:
    """
    Models optical lens behavior and point spread function generation
    """
    
    def __init__(self, wavelength=550e-9, pixel_size=1e-6):
        """
        Initialize lens model
        
        Args:
            wavelength (float): Light wavelength in meters (default: 550nm green light)
            pixel_size (float): Pixel size in meters for discretization
        """
        self.wavelength = wavelength
        self.pixel_size = pixel_size
        
    def airy_disk_psf(self, diameter, focal_length, grid_size=256):
        """
        Generate Airy disk point spread function for circular aperture
        
        Args:
            diameter (float): Lens diameter in meters
            focal_length (float): Lens focal length in meters  
            grid_size (int): Size of output grid (grid_size x grid_size)
            
        Returns:
            tuple: (psf, extent, airy_radius) where psf is 2D array, extent is coordinate range, airy_radius is first zero
        """
        # Create coordinate grid
        x = np.linspace(-grid_size//2, grid_size//2-1, grid_size) * self.pixel_size
        y = np.linspace(-grid_size//2, grid_size//2-1, grid_size) * self.pixel_size
        X, Y = np.meshgrid(x, y)
        R = np.sqrt(X**2 + Y**2)
        
        # Calculate angular radius
        # First zero of Airy pattern occurs at: sin(theta) = 1.22 * lambda / D
        # For small angles: theta ≈ sin(theta) = r / f
        # Therefore: r = 1.22 * lambda * f / D
        airy_radius = 1.22 * self.wavelength * focal_length / diameter
        
        # Normalized radius for Airy function
        # The argument of the Bessel function: beta = (pi * D * r) / (lambda * f)
        with np.errstate(divide='ignore', invalid='ignore'):
            beta = np.pi * diameter * R / (self.wavelength * focal_length)
            
            # Calculate Airy pattern: I = I0 * (2*J1(beta)/beta)^2
            # Handle the singularity at beta = 0
            airy = np.where(beta == 0, 1.0, (2 * j1(beta) / beta)**2)
        
        # Normalize and create extent
        airy = airy / np.max(airy)
        extent = [-grid_size//2 * self.pixel_size * 1e6, 
                  grid_size//2 * self.pixel_size * 1e6,
                  -grid_size//2 * self.pixel_size * 1e6, 
                  grid_size//2 * self.pixel_size * 1e6]  # Convert to micrometers
        
        return airy.astype(np.float32), extent, airy_radius
    
    def gaussian_psf(self, sigma_um, grid_size=256):
        """
        Generate Gaussian PSF (atmospheric seeing limited)
        
        Args:
            sigma_um (float): Gaussian sigma in micrometers
            grid_size (int): Size of output grid
            
        Returns:
            tuple: (psf, extent)
        """
        # Create coordinate grid in micrometers
        x_um = np.linspace(-grid_size//2, grid_size//2-1, grid_size) * self.pixel_size * 1e6
        y_um = np.linspace(-grid_size//2, grid_size//2-1, grid_size) * self.pixel_size * 1e6
        X, Y = np.meshgrid(x_um, y_um)
        R_squared = X**2 + Y**2
        
        # Generate Gaussian
        psf = np.exp(-R_squared / (2 * sigma_um**2))
        psf = psf / np.sum(psf)  # Normalize
        
        extent = [-grid_size//2 * self.pixel_size * 1e6, 
                  grid_size//2 * self.pixel_size * 1e6,
                  -grid_size//2 * self.pixel_size * 1e6, 
                  grid_size//2 * self.pixel_size * 1e6]
        
        return psf.astype(np.float32), extent
    
    def combined_psf(self, diameter, focal_length, seeing_arcsec, grid_size=256):
        """
        Generate combined PSF including both diffraction and atmospheric seeing
        
        Args:
            diameter (float): Lens diameter in meters
            focal_length (float): Lens focal length in meters
            seeing_arcsec (float): Atmospheric seeing FWHM in arcseconds
            grid_size (int): Size of output grid
            
        Returns:
            tuple: (psf, extent)
        """
        # Generate diffraction-limited Airy disk
        airy, extent, _ = self.airy_disk_psf(diameter, focal_length, grid_size)
        
        # Convert seeing from arcseconds to radians, then to physical size
        seeing_rad = seeing_arcsec * (np.pi / 180) / 3600  # arcsec to radians
        seeing_physical = seeing_rad * focal_length  # radians to meters
        seeing_um = seeing_physical * 1e6  # meters to micrometers
        
        # Generate atmospheric PSF (Gaussian with FWHM = seeing)
        # Convert FWHM to sigma: sigma = FWHM / (2 * sqrt(2 * ln(2)))
        sigma_um = seeing_um / (2 * np.sqrt(2 * np.log(2)))
        atmo_psf, _ = self.gaussian_psf(sigma_um, grid_size)
        
        # Convolve diffraction PSF with atmospheric PSF
        combined = ndimage.convolve(airy, atmo_psf, mode='constant')
        combined = combined / np.sum(combined)  # Renormalize
        
        return combined.astype(np.float32), extent
    
    def psf_metrics(self, psf, pixel_size_m):
        """
        Calculate PSF quality metrics
        
        Args:
            psf (numpy.ndarray): Point spread function
            pixel_size_m (float): Pixel size in meters
            
        Returns:
            dict: Dictionary of PSF metrics
        """
        metrics = {}
        
        # Find PSF center
        center_y, center_x = np.unravel_index(np.argmax(psf), psf.shape)
        
        # Peak intensity
        metrics['peak_intensity'] = np.max(psf)
        
        # Calculate FWHM (Full Width at Half Maximum)
        half_max = metrics['peak_intensity'] / 2
        
        # Get horizontal and vertical profiles through center
        h_profile = psf[center_y, :]
        v_profile = psf[:, center_x]
        
        # Find FWHM for horizontal profile
        h_indices = np.where(h_profile >= half_max)[0]
        if len(h_indices) > 0:
            h_fwhm_pixels = h_indices[-1] - h_indices[0] + 1
        else:
            h_fwhm_pixels = 1
        
        # Find FWHM for vertical profile
        v_indices = np.where(v_profile >= half_max)[0]
        if len(v_indices) > 0:
            v_fwhm_pixels = v_indices[-1] - v_indices[0] + 1
        else:
            v_fwhm_pixels = 1
        
        # Average FWHM and convert to micrometers
        fwhm_pixels = (h_fwhm_pixels + v_fwhm_pixels) / 2
        metrics['fwhm_pixels'] = fwhm_pixels
        metrics['fwhm_um'] = fwhm_pixels * pixel_size_m * 1e6
        
        # Calculate encircled energy
        metrics.update(self._calculate_encircled_energy(psf, pixel_size_m))
        
        # Calculate Strehl ratio (peak of actual PSF / peak of perfect PSF)
        # For a perfect Airy disk, the central intensity is 1
        metrics['strehl_ratio'] = metrics['peak_intensity']
        
        return metrics
    
    def _calculate_encircled_energy(self, psf, pixel_size_m):
        """
        Calculate encircled energy for different radii
        
        Args:
            psf (numpy.ndarray): Point spread function
            pixel_size_m (float): Pixel size in meters
            
        Returns:
            dict: Encircled energy metrics
        """
        center_y, center_x = np.unravel_index(np.argmax(psf), psf.shape)
        total_energy = np.sum(psf)
        
        # Create distance array from center
        y, x = np.ogrid[:psf.shape[0], :psf.shape[1]]
        distances = np.sqrt((x - center_x)**2 + (y - center_y)**2)
        
        # Calculate cumulative energy for different radii
        max_radius = min(center_x, center_y, psf.shape[1] - center_x, psf.shape[0] - center_y)
        radii = np.arange(1, max_radius + 1)
        
        encircled_energies = []
        for r in radii:
            mask = distances <= r
            energy = np.sum(psf[mask])
            encircled_energies.append(energy / total_energy)
        
        encircled_energies = np.array(encircled_energies)
        
        # Find radii for 50% and 80% encircled energy
        ee50_idx = np.argmax(encircled_energies >= 0.5)
        ee80_idx = np.argmax(encircled_energies >= 0.8)
        
        metrics = {}
        if ee50_idx > 0:
            metrics['ee50_radius_pixels'] = radii[ee50_idx]
            metrics['ee50_radius_um'] = radii[ee50_idx] * pixel_size_m * 1e6
        else:
            metrics['ee50_radius_pixels'] = max_radius
            metrics['ee50_radius_um'] = max_radius * pixel_size_m * 1e6
        
        if ee80_idx > 0:
            metrics['ee80_radius_pixels'] = radii[ee80_idx]
            metrics['ee80_radius_um'] = radii[ee80_idx] * pixel_size_m * 1e6
        else:
            metrics['ee80_radius_pixels'] = max_radius
            metrics['ee80_radius_um'] = max_radius * pixel_size_m * 1e6
        
        return metrics
    
    def calculate_f_number(self, diameter, focal_length):
        """
        Calculate f-number (f/#) of the lens
        
        Args:
            diameter (float): Lens diameter in meters
            focal_length (float): Lens focal length in meters
            
        Returns:
            float: F-number
        """
        return focal_length / diameter
    
    def calculate_numerical_aperture(self, diameter, focal_length):
        """
        Calculate numerical aperture
        
        Args:
            diameter (float): Lens diameter in meters
            focal_length (float): Lens focal length in meters
            
        Returns:
            float: Numerical aperture
        """
        # For a lens in air: NA = D / (2*f)
        return diameter / (2 * focal_length)
    
    def rayleigh_criterion(self, diameter):
        """
        Calculate Rayleigh resolution limit
        
        Args:
            diameter (float): Lens diameter in meters
            
        Returns:
            float: Angular resolution in radians
        """
        return 1.22 * self.wavelength / diameter
    
    def depth_of_field(self, diameter, focal_length, object_distance, circle_of_confusion=None):
        """
        Calculate depth of field
        
        Args:
            diameter (float): Lens diameter in meters
            focal_length (float): Lens focal length in meters
            object_distance (float): Distance to object in meters
            circle_of_confusion (float): Acceptable circle of confusion in meters
            
        Returns:
            dict: Near focus, far focus, and total DOF
        """
        if circle_of_confusion is None:
            # Use Airy disk radius as COC
            circle_of_confusion = 1.22 * self.wavelength * focal_length / diameter
        
        f_number = self.calculate_f_number(diameter, focal_length)
        
        # Hyperfocal distance
        H = focal_length**2 / (f_number * circle_of_confusion)
        
        # Near and far focus distances
        if object_distance > H:
            near_focus = (H * object_distance) / (H + object_distance)
            far_focus = np.inf
        else:
            near_focus = (H * object_distance) / (H + object_distance)
            far_focus = (H * object_distance) / (H - object_distance)
        
        total_dof = far_focus - near_focus if np.isfinite(far_focus) else np.inf
        
        return {
            'near_focus': near_focus,
            'far_focus': far_focus,
            'total_dof': total_dof,
            'hyperfocal_distance': H
        }