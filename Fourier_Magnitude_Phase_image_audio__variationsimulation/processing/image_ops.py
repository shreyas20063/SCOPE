"""
Image Processing Operations Module
Handles image loading, test pattern generation, and preprocessing
"""

import numpy as np
from scipy import ndimage
from PIL import Image


class ImageProcessor:
    """
    Handles image processing operations for Fourier analysis
    """

    def __init__(self):
        """Initialize image processor"""
        self.test_patterns = {
            'building': self._generate_building,
            'face': self._generate_face,
            'geometric': self._generate_geometric,
            'texture': self._generate_texture
        }

    def generate_test_image(self, size=256, pattern='building'):
        """
        Generate test images for Fourier analysis

        Args:
            size (int): Image size (square)
            pattern (str): Pattern type

        Returns:
            numpy.ndarray: Generated test image (normalized to [0, 1])
        """
        if pattern in self.test_patterns:
            return self.test_patterns[pattern](size)
        else:
            raise ValueError(f"Unknown pattern type: {pattern}")

    def load_image(self, file_path, target_size=256):
        """
        Load and preprocess image for Fourier analysis

        Args:
            file_path (str): Path to image file
            target_size (int): Target size for square image

        Returns:
            tuple:
                - np.ndarray: Grayscale image array (normalized to [0, 1])
                - np.ndarray: Display image array in RGB (normalized to [0, 1])
        """
        try:
            # Load image using PIL
            img = Image.open(file_path)

            # Prepare color and grayscale versions
            img_rgb = img.convert('RGB')
            img_gray = img_rgb.convert('L')

            # Resize to target size
            img_rgb = img_rgb.resize((target_size, target_size), Image.Resampling.LANCZOS)
            img_gray = img_gray.resize((target_size, target_size), Image.Resampling.LANCZOS)

            # Convert to numpy array and normalize
            gray_array = np.array(img_gray, dtype=np.float64) / 255.0
            color_array = np.array(img_rgb, dtype=np.float64) / 255.0

            return gray_array, color_array

        except Exception as e:
            print(f"Error loading image: {e}")
            # Return default test image on error
            fallback = self.generate_test_image(target_size, 'building')
            fallback_color = np.repeat(fallback[..., np.newaxis], 3, axis=2)
            return fallback, fallback_color

    def _generate_building(self, size=256):
        """Generate synthetic building image"""
        img = np.zeros((size, size))

        # Building body (two sections)
        img[80:200, 70:110] = 0.8   # Left section
        img[80:200, 150:190] = 0.8  # Right section

        # Roof
        img[50:80, 70:190] = 0.9

        # Windows in left section
        for i in range(100, 190, 20):
            for j in range(80, 100, 10):
                img[i:i+8, j:j+6] = 0.3

        # Windows in right section
        for i in range(100, 190, 20):
            for j in range(160, 180, 10):
                img[i:i+8, j:j+6] = 0.3

        # Door
        img[160:200, 125:135] = 0.4

        # Ground
        img[200:, :] = 0.6

        # Add slight noise for realism
        noise = np.random.normal(0, 0.02, (size, size))
        img = np.clip(img + noise, 0, 1)

        return img.astype(np.float64)

    def _generate_face(self, size=256):
        """Generate synthetic face image"""
        img = np.zeros((size, size))
        center = size // 2

        # Face contour (circle)
        y, x = np.ogrid[-center:size-center, -center:size-center]
        face_mask = x*x + y*y <= 80*80
        img[face_mask] = 0.85

        # Left eye
        left_eye_y, left_eye_x = np.ogrid[-110:size-110, -90:size-90]
        left_eye_mask = left_eye_x*left_eye_x + left_eye_y*left_eye_y <= 15*15
        img[left_eye_mask] = 0.2

        # Right eye
        right_eye_y, right_eye_x = np.ogrid[-110:size-110, -165:size-165]
        right_eye_mask = right_eye_x*right_eye_x + right_eye_y*right_eye_y <= 15*15
        img[right_eye_mask] = 0.2

        # Nose
        for i in range(128, 160):
            width = (i - 128) // 4
            img[i, center-width:center+width] = 0.6

        # Mouth (smile)
        for i in range(-30, 31):
            mouth_y = int(180 + (i*i) / 40)
            mouth_x = center + i
            if 0 <= mouth_y < size and 0 <= mouth_x < size:
                img[mouth_y-2:mouth_y+2, mouth_x-1:mouth_x+1] = 0.3

        # Smooth for realistic appearance
        img = ndimage.gaussian_filter(img, sigma=1.5)

        return img.astype(np.float64)

    def _generate_geometric(self, size=256):
        """Generate geometric patterns for testing"""
        img = np.zeros((size, size))

        # Circles
        center = size // 2
        for radius in [30, 60, 90]:
            y, x = np.ogrid[:size, :size]
            circle_mask = np.sqrt((x - center)**2 + (y - center)**2)
            img[(circle_mask >= radius-2) & (circle_mask <= radius+2)] = 0.8

        # Vertical lines
        for x in range(20, size, 40):
            img[:, x:x+3] = 0.7

        # Horizontal lines
        for y in range(20, size, 40):
            img[y:y+3, :] = 0.7

        # Diagonal line
        for i in range(size):
            if 0 <= i < size:
                img[i, i] = 0.9
                if i < size - 1:
                    img[i, i+1] = 0.9

        # Add corner squares
        img[10:40, 10:40] = 0.6
        img[10:40, size-40:size-10] = 0.6
        img[size-40:size-10, 10:40] = 0.6
        img[size-40:size-10, size-40:size-10] = 0.6

        return img.astype(np.float64)

    def _generate_texture(self, size=256):
        """Generate textured pattern"""
        img = np.zeros((size, size))

        # Base gradient
        y, x = np.ogrid[:size, :size]
        img = x / size * 0.5 + y / size * 0.3

        # Add sinusoidal patterns
        freq1 = 2 * np.pi * 8 / size
        freq2 = 2 * np.pi * 16 / size
        img += 0.2 * np.sin(freq1 * x) * np.cos(freq1 * y)
        img += 0.1 * np.sin(freq2 * x) * np.sin(freq2 * y)

        # Add random texture
        np.random.seed(42)
        texture = np.random.rand(size, size) * 0.2
        img += texture

        # Normalize to [0, 1]
        img = (img - img.min()) / (img.max() - img.min())

        return img.astype(np.float64)

    def normalize_image(self, image):
        """
        Normalize image to [0, 1] range

        Args:
            image: Input image

        Returns:
            numpy.ndarray: Normalized image
        """
        img_min = np.min(image)
        img_max = np.max(image)

        if img_max - img_min > 0:
            normalized = (image - img_min) / (img_max - img_min)
        else:
            normalized = np.zeros_like(image)

        return normalized

    def resize_image(self, image, target_size):
        """
        Resize image to target size

        Args:
            image: Input image
            target_size (int): Target size (square)

        Returns:
            numpy.ndarray: Resized image
        """
        # Convert to PIL Image
        img_uint8 = (image * 255).astype(np.uint8)
        pil_img = Image.fromarray(img_uint8, mode='L')

        # Resize
        pil_img = pil_img.resize((target_size, target_size), Image.Resampling.LANCZOS)

        # Convert back to numpy
        resized = np.array(pil_img, dtype=np.float64) / 255.0

        return resized

    def add_noise(self, image, noise_level=0.01):
        """
        Add Gaussian noise to image

        Args:
            image: Input image
            noise_level (float): Standard deviation of noise

        Returns:
            numpy.ndarray: Noisy image
        """
        noise = np.random.normal(0, noise_level, image.shape)
        noisy = image + noise
        return np.clip(noisy, 0, 1)

    def calculate_image_statistics(self, image):
        """
        Calculate image statistics

        Args:
            image: Input image

        Returns:
            dict: Statistics
        """
        return {
            'mean': np.mean(image),
            'std': np.std(image),
            'min': np.min(image),
            'max': np.max(image),
            'median': np.median(image),
            'shape': image.shape
        }
