"""
Audio Processing Operations Module
Handles audio signal generation, loading, and preprocessing
"""

import numpy as np
from scipy.io import wavfile
from scipy import signal
import pathlib


class AudioProcessor:
    """
    Handles audio processing operations for Fourier analysis
    """

    def __init__(self, sample_rate=44100, duration=2.0):
        self.sample_rate = sample_rate
        self.duration = duration
        self.test_patterns = {
            'sine': self._generate_sine,
            'square': self._generate_square,
            'sawtooth': self._generate_sawtooth,
            'beat': self._generate_beat
        }

    def generate_test_signal(self, pattern='sine'):
        """
        Generate test audio signals

        Args:
            pattern (str): Pattern type ('sine', 'square', 'sawtooth', 'beat')

        Returns:
            tuple: (signal, sample_rate)
        """
        pattern = pattern.lower()
        if pattern not in self.test_patterns:
            raise ValueError(f"Unknown audio pattern: {pattern}")

        signal = self.test_patterns[pattern]()
        return signal, self.sample_rate

    def load_audio(self, file_path):
        """
        Load audio file and resample/normalize for analysis

        Args:
            file_path (str): Path to audio file

        Returns:
            tuple: (signal, sample_rate)
        """
        file_path = pathlib.Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        sample_rate, data = wavfile.read(str(file_path))

        if data.ndim > 1:
            data = data.mean(axis=1)

        data = data.astype(np.float64)
        max_val = np.max(np.abs(data))
        if max_val > 0:
            data /= max_val

        if sample_rate != self.sample_rate:
            num_samples = int(len(data) * self.sample_rate / sample_rate)
            data = signal.resample(data, num_samples)
            sample_rate = self.sample_rate

        target_length = int(self.sample_rate * self.duration)
        data = self._match_length(data, target_length)

        return data, sample_rate

    def _match_length(self, data, target_length):
        """Trim or pad signal to target length"""
        if len(data) > target_length:
            return data[:target_length]
        if len(data) < target_length:
            pad_width = target_length - len(data)
            return np.pad(data, (0, pad_width), mode='constant')
        return data

    def _time_axis(self):
        """Generate time axis for default configuration"""
        return np.linspace(0, self.duration, int(self.sample_rate * self.duration), endpoint=False)

    def _generate_sine(self, frequency=440):
        t = self._time_axis()
        return np.sin(2 * np.pi * frequency * t)

    def _generate_square(self):
        t = self._time_axis()
        return signal.square(2 * np.pi * 220 * t, duty=0.5)

    def _generate_sawtooth(self):
        t = self._time_axis()
        return signal.sawtooth(2 * np.pi * 180 * t)

    def _generate_beat(self):
        t = self._time_axis()
        carrier = np.sin(2 * np.pi * 440 * t)
        modulator = np.sin(2 * np.pi * 2 * t)
        return carrier * (0.5 * (modulator + 1.0))
