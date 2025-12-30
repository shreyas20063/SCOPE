"""
Image Processing and Convolution Operations Module
Handles image loading, convolution with PSFs, and image analysis
"""

import numpy as np
from scipy.signal import fftconvolve
from scipy.ndimage import zoom
import cv2
from PIL import Image

class ImageProcessor:
    """
    Handles image processing operations for lens simulation
    """
    
    def __init__(self):
        """Initialize image processor"""
        self.test_patterns = {
            'resolution_chart': self._generate_resolution_chart,
            'point_sources': self._generate_point_sources,
            'edge_target': self._generate_edge_target,
            'star_field': self._generate_star_field
        }
    
    def generate_test_image(self, size=512, pattern='resolution_chart'):
        """
        Generate test images for simulation
        
        Args:
            size (int): Image size (square)
            pattern (str): Pattern type
            
        Returns:
            numpy.ndarray: Generated test image
        """
        if pattern in self.test_patterns:
            return self.test_patterns[pattern](size)
        else:
            raise ValueError(f"Unknown pattern type: {pattern}")
    
    def load_image(self, file_path, target_size=512):
        """
        Load and preprocess image for simulation
        
        Args:
            file_path (str): Path to image file
            target_size (int): Target size for square image
            
        Returns:
            np.ndarray: Processed image array
        """
        try:
            # Load image using PIL
            img = Image.open(file_path)
            
            # Convert to grayscale
            if img.mode != 'L':
                img = img.convert('L')
            
            # Convert to numpy array
            img_array = np.array(img)
            
            # Resize to target size while maintaining aspect ratio
            h, w = img_array.shape
            
            # Calculate scaling factor to fit target size
            scale = target_size / max(h, w)
            new_h, new_w = int(h * scale), int(w * scale)
            
            img_resized = cv2.resize(img_array, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
            
            # Pad to exact target size
            img_padded = self._pad_to_size(img_resized, target_size)
            
            # Normalize to [0, 1]
            img_normalized = img_padded.astype(np.float32) / 255.0
            
            return img_normalized
            
        except Exception as e:
            print(f"Error loading image: {e}")
            return self.generate_test_image(target_size, 'resolution_chart')
    
    def _pad_to_size(self, img, target_size):
        """Pad image to exact target size"""
        h, w = img.shape
        pad_h = (target_size - h) // 2
        pad_w = (target_size - w) // 2
        
        padded = np.zeros((target_size, target_size), dtype=img.dtype)
        padded[pad_h:pad_h+h, pad_w:pad_w+w] = img
            
        return padded
    
    def _generate_resolution_chart(self, size):
        """Generate resolution test chart with varying spatial frequencies"""
        img = np.zeros((size, size))
        center = size // 2
        
        # Create concentric rings with increasing frequency
        y, x = np.ogrid[:size, :size]
        r = np.sqrt((x - center)**2 + (y - center)**2)
        
        # Normalize radius
        r_norm = r / (size // 2)
        
        # Create radial frequency pattern
        freq = r_norm * 20  # Max frequency
        radial_pattern = np.sin(2 * np.pi * freq)
        
        # Create angular patterns
        theta = np.arctan2(y - center, x - center)
        angular_pattern = np.sin(8 * theta)  # 8 spokes
        
        # Combine patterns
        img = 0.5 + 0.3 * radial_pattern + 0.2 * angular_pattern
        
        # Add some high-frequency details
        fine_pattern = np.sin(2 * np.pi * r_norm * 50) * np.exp(-r_norm * 2)
        img += 0.1 * fine_pattern
        
        # Ensure values are in [0, 1]
        img = np.clip(img, 0, 1)
        
        return img.astype(np.float32)
    
    def _generate_point_sources(self, size):
        """Generate point sources for PSF testing"""
        img = np.zeros((size, size))
        
        # Add several point sources
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
    
    def _generate_edge_target(self, size):
        """Generate sharp edge target for MTF testing"""
        img = np.zeros((size, size))
        
        # Vertical edge
        img[:, :size//2] = 0.3
        img[:, size//2:] = 0.7
        
        # Add horizontal edge in another region
        img[:size//4, :] = 0.2
        img[3*size//4:, :] = 0.8
        
        # Add diagonal edges
        for i in range(size):
            for j in range(size):
                if i + j > size:
                    img[i, j] = max(img[i, j], 0.6)
                if abs(i - j) < size // 10:
                    img[i, j] = 0.9
        
        return img.astype(np.float32)
    
    def _generate_star_field(self, size):
        """Generate star field for astronomical simulation"""
        np.random.seed(42)  # For reproducibility
        img = np.zeros((size, size))
        
        # Add random stars
        n_stars = 50
        for _ in range(n_stars):
            x = np.random.randint(0, size)
            y = np.random.randint(0, size)
            brightness = np.random.uniform(0.3, 1.0)
            
            # Create small Gaussian for each star
            sigma = np.random.uniform(0.5, 2.0)
            for dy in range(-3, 4):
                for dx in range(-3, 4):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < size and 0 <= nx < size:
                        distance = np.sqrt(dx**2 + dy**2)
                        value = brightness * np.exp(-distance**2 / (2 * sigma**2))
                        img[ny, nx] = max(img[ny, nx], value)
        
        return img.astype(np.float32)
    
    def convolve_with_psf(self, image, psf, noise_level=0.0):
        """
        Convolve image with point spread function
        
        Args:
            image (np.ndarray): Input image
            psf (np.ndarray): Point spread function
            noise_level (float): Noise level to add [0,1]
            
        Returns:
            np.ndarray: Convolved (blurred) image
        """
        # Normalize PSF
        psf_normalized = psf / np.sum(psf)
        
        # Perform convolution
        if image.ndim == 2:  # Grayscale
            blurred = fftconvolve(image, psf_normalized, mode='same')
        else:  # Color - convolve each channel
            blurred = np.zeros_like(image)
            for i in range(image.shape[2]):
                blurred[:, :, i] = fftconvolve(image[:, :, i], psf_normalized, mode='same')
        
        # Add noise if requested
        if noise_level > 0:
            noise = np.random.normal(0, noise_level, blurred.shape)
            blurred = blurred + noise
        
        # Ensure values stay in valid range
        blurred = np.clip(blurred, 0, 1)
        
        return blurred.astype(np.float32)
    
    def match_psf_size(self, psf, target_size):
        """
        Resize PSF to match image size
        
        Args:
            psf (np.ndarray): Point spread function
            target_size (int): Target size for PSF
            
        Returns:
            np.ndarray: Resized PSF
        """
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
            
            # Handle odd size differences
            if padded.shape[0] < target_size:
                padded = np.pad(padded, ((0, 1), (0, 1)), mode='constant', constant_values=0)
            elif padded.shape[0] > target_size:
                padded = padded[:target_size, :target_size]
                
            return padded
    
    def calculate_image_quality_metrics(self, original, blurred):
        """
        Calculate image quality metrics comparing original and blurred images
        
        Args:
            original (np.ndarray): Original image
            blurred (np.ndarray): Blurred image
            
        Returns:
            dict: Quality metrics
        """
        # Ensure images are same size
        if original.shape != blurred.shape:
            return {'error': 'Image shapes do not match'}
        
        # Convert to grayscale if needed for some metrics
        if original.ndim == 3:
            orig_gray = np.mean(original, axis=2)
            blur_gray = np.mean(blurred, axis=2)
        else:
            orig_gray = original
            blur_gray = blurred
        
        # Mean Squared Error
        mse = np.mean((orig_gray - blur_gray)**2)
        
        # Peak Signal-to-Noise Ratio
        if mse > 0:
            psnr = 20 * np.log10(1.0 / np.sqrt(mse))
        else:
            psnr = float('inf')
        
        # Structural Similarity Index (simplified version)
        mu1 = np.mean(orig_gray)
        mu2 = np.mean(blur_gray)
        sigma1 = np.var(orig_gray)
        sigma2 = np.var(blur_gray)
        sigma12 = np.mean((orig_gray - mu1) * (blur_gray - mu2))
        
        c1 = 0.01**2
        c2 = 0.03**2
        
        ssim = ((2*mu1*mu2 + c1)*(2*sigma12 + c2)) / ((mu1**2 + mu2**2 + c1)*(sigma1 + sigma2 + c2))
        
        # Edge preservation metric
        orig_edges = self._detect_edges(orig_gray)
        blur_edges = self._detect_edges(blur_gray)
        edge_preservation = np.corrcoef(orig_edges.flatten(), blur_edges.flatten())[0, 1]
        
        # Contrast reduction
        original_contrast = np.std(orig_gray)
        blurred_contrast = np.std(blur_gray)
        
        if original_contrast > 0:
            contrast_reduction = 1 - (blurred_contrast / original_contrast)
        else:
            contrast_reduction = 0.0
        
        return {
            'mse': mse,
            'psnr': psnr,
            'ssim': ssim,
            'edge_preservation': edge_preservation,
            'contrast_reduction': contrast_reduction
        }
    
    def _detect_edges(self, image):
        """Simple edge detection using Sobel operator"""
        # Ensure image is in the right format for OpenCV
        if image.dtype != np.uint8:
            image_uint8 = (image * 255).astype(np.uint8)
        else:
            image_uint8 = image
            
        sobel_x = cv2.Sobel(image_uint8, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(image_uint8, cv2.CV_64F, 0, 1, ksize=3)
        edges = np.sqrt(sobel_x**2 + sobel_y**2)
        return edges
    
    def create_comparison_image(self, original, blurred, psf=None):
        """
        Create side-by-side comparison image
        
        Args:
            original (np.ndarray): Original image
            blurred (np.ndarray): Blurred image  
            psf (np.ndarray): Optional PSF to include
            
        Returns:
            np.ndarray: Comparison image
        """
        if psf is not None:
            # Three-panel comparison
            h, w = original.shape[:2]
            
            # Resize PSF for display
            psf_display = zoom(psf, (h//4) / psf.shape[0], order=1)
            psf_padded = np.zeros((h, w))
            ph, pw = psf_display.shape
            psf_padded[:ph, :pw] = psf_display / np.max(psf_display)  # Normalize for display
            
            if original.ndim == 2:
                comparison = np.hstack([original, blurred, psf_padded])
            else:
                psf_rgb = np.stack([psf_padded, psf_padded, psf_padded], axis=2)
                comparison = np.hstack([original, blurred, psf_rgb])
        else:
            # Two-panel comparison
            comparison = np.hstack([original, blurred])
        
        return comparison