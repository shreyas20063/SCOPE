import numpy as np
from scipy.io import wavfile
from typing import Sequence
from gui.styles import COLORS

def load_and_validate_audio(audio_file: str) -> tuple[int, np.ndarray]:
    """Return (sample_rate, mono_float64_audio); fall back to a tone when needed."""
    
    def fallback() -> tuple[int, np.ndarray]:
        sr = 44_100
        t = np.linspace(0, 3, int(sr * 3), dtype=np.float64)
        tone = 0.3 * np.sin(2 * np.pi * 440 * t) + 0.2 * np.sin(2 * np.pi * 880 * t)
        return sr, np.ascontiguousarray(tone, dtype=np.float64)

    try:
        sr, audio = wavfile.read(audio_file)
        audio = np.asarray(audio)
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        
        # Normalization logic
        if audio.dtype == np.int16:
            audio = audio.astype(np.float64) / 32768.0
        elif audio.dtype == np.int32:
            audio = audio.astype(np.float64) / 2147483648.0
        elif audio.dtype == np.uint8:
            audio = (audio.astype(np.float64) - 128.0) / 128.0
        else:
            audio = audio.astype(np.float64)
            peak = np.max(np.abs(audio))
            if peak > 1.0:
                audio /= peak

        rms = float(np.sqrt(np.mean(audio**2))) if audio.size else 0.0
        if rms < 1e-3:
            print(f"Audio file '{audio_file}' is effectively silent; using fallback tone.")
            return fallback()
        return int(sr), np.ascontiguousarray(audio, dtype=np.float64)
    except FileNotFoundError:
        print(f"Audio file '{audio_file}' not found; using fallback tone.")
    except Exception as exc:
        print(f"Error loading '{audio_file}': {exc}; using fallback tone.")
    return fallback()

def configure_axes(axes: Sequence) -> None:
    for ax in axes:
        ax.set_facecolor(COLORS["bg"])
        ax.grid(True, alpha=0.25, color=COLORS["grid"])
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.tick_params(axis="x", colors=COLORS["text_secondary"])
        ax.tick_params(axis="y", colors=COLORS["text_secondary"])
        ax.xaxis.label.set_color(COLORS["text_primary"])
        ax.yaxis.label.set_color(COLORS["text_primary"])
        ax.title.set_color(COLORS["text_primary"])