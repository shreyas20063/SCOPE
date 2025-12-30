"""
Helper utilities for the Amplifier Simulator
Contains image loading and audio playback functionality
"""

import threading
import sounddevice as sd
from PyQt5.QtGui import QPixmap
import config


class ImageLoader:
    """Handles loading and resizing of circuit diagram images"""

    @staticmethod
    def load_images():
        """
        Loads circuit diagram images

        Returns:
            dict: Dictionary mapping mode names to QPixmap objects
        """
        circuit_images = {}

        for mode, filepath in config.IMAGE_MAP.items():
            try:
                pixmap = QPixmap(filepath)
                if pixmap.isNull():
                    print(f"Warning: Could not load '{filepath}'. Make sure it exists in the assets folder.")
                    circuit_images[mode] = None
                else:
                    circuit_images[mode] = pixmap

            except Exception as e:
                print(f"Error loading image {filepath}: {e}")
                circuit_images[mode] = None

        return circuit_images


class AudioPlayer:
    """Handles audio playback in a separate thread"""

    def __init__(self):
        self.is_playing = False
        self.sample_rate = config.DEFAULT_SAMPLE_RATE

    def play(self, audio_data, sample_rate, play_button, on_error_callback):
        """
        Play audio in a separate thread

        Args:
            audio_data: Numpy array of audio samples
            sample_rate: Sample rate of audio
            play_button: QPushButton to disable/enable
            on_error_callback: Function to call on error
        """
        if not self.is_playing:
            self.is_playing = True
            self.sample_rate = sample_rate
            play_button.setEnabled(False)
            threading.Thread(
                target=self._play_thread,
                args=(audio_data, play_button, on_error_callback),
                daemon=True
            ).start()

    def _play_thread(self, audio_data, play_button, on_error_callback):
        """Audio playback thread"""
        try:
            sd.play(audio_data, self.sample_rate)
            sd.wait()
        except Exception as e:
            on_error_callback(f"Playback Error: {e}")
        finally:
            self.is_playing = False
            try:
                play_button.setEnabled(True)
            except:
                pass  # Widget may have been destroyed

    def stop(self):
        """Stop audio playback"""
        sd.stop()
        self.is_playing = False


class GainCalculator:
    """Calculates gain curves for different amplifier configurations"""
    
    @staticmethod
    def calculate_gains(K_val, beta_val, F0_range):
        """
        Calculate gain curves
        
        Args:
            K_val: Forward gain value
            beta_val: Feedback factor
            F0_range: Array of F0 values
            
        Returns:
            tuple: (gain_simple, gain_feedback, ideal_gain)
        """
        gain_simple = F0_range
        gain_feedback = (K_val * F0_range) / (1 + beta_val * K_val * F0_range)
        ideal_gain = 1 / beta_val if beta_val > 0 else float('inf')
        
        return gain_simple, gain_feedback, ideal_gain
