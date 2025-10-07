"""
Helper utilities for the Amplifier Simulator
Contains image loading and audio playback functionality
"""

import threading
import sounddevice as sd
from PIL import Image
import customtkinter as ctk
import config


class ImageLoader:
    """Handles loading and resizing of circuit diagram images"""
    
    @staticmethod
    def load_images():
        """
        Loads and resizes images to fit within a fixed bounding box
        
        Returns:
            dict: Dictionary mapping mode names to CTkImage objects
        """
        circuit_images = {}
        bounding_box = config.IMAGE_BOUNDING_BOX

        for mode, filename in config.IMAGE_MAP.items():
            try:
                img = Image.open(filename)
                original_width, original_height = img.size

                # Calculate scaling ratio to fit bounding box
                width_ratio = bounding_box[0] / original_width
                height_ratio = bounding_box[1] / original_height
                scale_ratio = min(width_ratio, height_ratio)
                
                new_width = int(original_width * scale_ratio)
                new_height = int(original_height * scale_ratio)

                ctk_image = ctk.CTkImage(light_image=img, size=(new_width, new_height))
                circuit_images[mode] = ctk_image
            
            except FileNotFoundError:
                print(f"Warning: Could not find '{filename}'. Make sure it's in the same folder.")
                circuit_images[mode] = None
            except Exception as e:
                print(f"Error loading image {filename}: {e}")
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
            play_button: Button to disable/enable
            on_error_callback: Function to call on error
        """
        if not self.is_playing:
            self.is_playing = True
            self.sample_rate = sample_rate
            play_button.configure(state="disabled")
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
                play_button.configure(state="normal")
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
