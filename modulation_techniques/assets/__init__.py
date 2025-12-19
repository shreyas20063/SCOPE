"""Assets for modulation simulator (audio files, images, etc.)."""

import os

# Path to assets directory
ASSETS_DIR = os.path.dirname(os.path.abspath(__file__))

# Path to audio sample
AUDIO_SAMPLE_PATH = os.path.join(ASSETS_DIR, "audio_sample.wav")

__all__ = [
    "ASSETS_DIR",
    "AUDIO_SAMPLE_PATH",
]
