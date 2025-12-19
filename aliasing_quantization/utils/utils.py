"""
Utility functions for Signal Processing Lab
Audio loading and validation functions
"""

import numpy as np
from scipy.io import wavfile
import warnings
warnings.filterwarnings('ignore')

def load_and_validate_audio(audio_file):
    """Loads and validates a WAV audio file, providing a fallback."""
    try:
        sr, audio_data = wavfile.read(audio_file)
        # Convert to mono if stereo
        if len(audio_data.shape) > 1:
            audio_data = audio_data.mean(axis=1)

        # Normalize based on data type to float between -1.0 and 1.0
        if audio_data.dtype == np.int16:
            audio = audio_data.astype(np.float32) / 32768.0
        elif audio_data.dtype == np.int32:
            audio = audio_data.astype(np.float32) / 2147483648.0
        elif audio_data.dtype == np.uint8:  # 8-bit WAV is usually unsigned 0-255
            audio = (audio_data.astype(np.float32) - 128.0) / 128.0
        else:  # Assume it's already float but might be outside range
            audio = audio_data.astype(np.float32)
            max_val = np.max(np.abs(audio))
            if max_val > 1.0:
                audio = audio / max_val
            elif max_val == 0:  # Avoid division by zero if silent
                pass  # Keep as zeros

        # Check RMS (Root Mean Square) to see if audio is too quiet/silent
        rms = np.sqrt(np.mean(audio**2))
        if rms < 0.001:  # Threshold for considering audio silent
            print(f"Warning: Audio file '{audio_file}' is silent or near silent (RMS={rms:.4f}). Generating fallback tone.")
            # Generate a simple fallback tone (A4 + A5)
            sr = 44100  # Ensure SR is set for fallback
            t = np.linspace(0, 3, int(sr * 3), dtype=np.float32)
            audio = 0.3 * np.sin(2 * np.pi * 440 * t) + 0.2 * np.sin(2 * np.pi * 880 * t)
        return sr, audio

    except FileNotFoundError:
        print(f"Error: Audio file '{audio_file}' not found. Generating fallback tone.")
    except Exception as e:
        print(f"Error loading audio file '{audio_file}': {e}. Generating fallback tone.")

    # Fallback tone generation if loading fails
    sr = 44100
    t = np.linspace(0, 3, int(sr * 3), dtype=np.float32)
    audio = 0.3 * np.sin(2 * np.pi * 440 * t) + 0.2 * np.sin(2 * np.pi * 880 * t)
    return sr, audio