"""
Audio processing and signal generation module
Handles all audio signal processing, test signal generation, and amplifier simulation
"""

import numpy as np
from scipy.io import wavfile
import os

try:
    from pydub import AudioSegment
    MP3_SUPPORTED = True
except ImportError:
    MP3_SUPPORTED = False

import config


class AudioProcessor:
    """Handles audio processing and amplifier simulation"""
    
    def __init__(self):
        self.audio_data = None
        self.sample_rate = config.DEFAULT_SAMPLE_RATE
        self.output_audio = None
        self.is_custom_audio = False
        
    def generate_test_signal(self, sig_type='pure_sine'):
        """
        Generate demo test signals
        
        Args:
            sig_type: Type of signal ('pure_sine' or 'rich_sine')
        """
        self.sample_rate = config.DEFAULT_SAMPLE_RATE
        duration = config.DEFAULT_DURATION
        t = np.linspace(0, duration, int(self.sample_rate * duration), endpoint=False)
        amplitude = config.DEFAULT_AMPLITUDE
        frequency = config.DEFAULT_FREQUENCY
        
        if sig_type == 'pure_sine':
            self.audio_data = amplitude * np.sin(2 * np.pi * frequency * t)
        elif sig_type == 'rich_sine':
            self.audio_data = amplitude * (
                0.7 * np.sin(2 * np.pi * frequency * t) + 
                0.2 * np.sin(2 * np.pi * 2 * frequency * t) + 
                0.1 * np.sin(2 * np.pi * 3 * frequency * t)
            )
        
        self.is_custom_audio = False
        return f"Input: {sig_type.replace('_', ' ').title()}"
    
    def load_audio_file(self, file_path):
        """
        Load audio from WAV or MP3 file
        
        Args:
            file_path: Path to audio file
            
        Returns:
            tuple: (success: bool, message: str, filename: str)
        """
        if not file_path:
            return False, "No file selected", ""
        
        try:
            if file_path.lower().endswith('.mp3'):
                if not MP3_SUPPORTED:
                    return False, "MP3 Support Missing. Install 'pydub':\npip install pydub", ""
                
                audio = AudioSegment.from_mp3(file_path).set_channels(1)
                self.sample_rate = audio.frame_rate
                samples = np.array(audio.get_array_of_samples())
                self.audio_data = samples.astype(np.float32) / (2**15)
            else:
                self.sample_rate, data = wavfile.read(file_path)
                
                # Convert stereo to mono
                if len(data.shape) > 1:
                    data = data.mean(axis=1)
                
                # Normalize integer data
                if np.issubdtype(data.dtype, np.integer):
                    max_val = np.iinfo(data.dtype).max
                    self.audio_data = data.astype(np.float32) / max_val
                else:
                    self.audio_data = data.astype(np.float32)
            
            # Remove DC offset
            self.audio_data = self.audio_data - np.mean(self.audio_data)
            
            # Normalize amplitude
            max_abs = np.max(np.abs(self.audio_data))
            if max_abs > 0:
                self.audio_data = self.audio_data / max_abs * config.DEFAULT_AMPLITUDE
            
            # Trim if too long
            max_samples = self.sample_rate * config.MAX_AUDIO_DURATION
            trimmed = False
            if len(self.audio_data) > max_samples:
                self.audio_data = self.audio_data[:max_samples]
                trimmed = True
            
            self.is_custom_audio = True
            filename = os.path.basename(file_path)
            message = "Audio loaded successfully"
            if trimmed:
                message = f"Audio trimmed to {config.MAX_AUDIO_DURATION} seconds"
            
            return True, message, filename
            
        except Exception as e:
            return False, f"Error loading file: {str(e)}", ""
    
    def apply_crossover_distortion(self, signal, threshold):
        """
        Apply crossover distortion (dead zone near zero)
        
        Args:
            signal: Input signal array
            threshold: Dead zone threshold
            
        Returns:
            np.array: Signal with crossover distortion applied
        """
        output = signal.copy()
        dead_zone_mask = np.abs(signal) < threshold
        output[signal > threshold] -= threshold
        output[signal < -threshold] += threshold
        output[dead_zone_mask] = 0
        return output
    
    def process_audio(self, mode, K_val, F0_val, beta_val, VT):
        """
        Process audio through the selected amplifier configuration
        
        Args:
            mode: Amplifier mode ('simple', 'feedback', 'crossover', 'compensated')
            K_val: Forward gain
            F0_val: Power amp gain
            beta_val: Feedback factor
            VT: Threshold voltage for crossover distortion
        """
        if self.audio_data is None:
            return
        
        input_signal = self.audio_data.copy()

        if mode == 'simple':
            output = input_signal * F0_val
        elif mode == 'feedback':
            gain = (K_val * F0_val) / (1 + beta_val * K_val * F0_val)
            output = input_signal * gain
        elif mode == 'crossover':
            amplified_signal = input_signal * K_val
            output = self.apply_crossover_distortion(amplified_signal, VT)
        else:  # compensated
            gain = (K_val * F0_val) / (1 + beta_val * K_val * F0_val)
            amplified_signal = input_signal * gain
            effective_VT = VT / K_val
            output = self.apply_crossover_distortion(amplified_signal, effective_VT)
        
        self.output_audio = output
    
    def get_plot_data(self):
        """
        Get data for plotting
        
        Returns:
            dict: Dictionary containing time, input_slice, output_slice
        """
        if self.audio_data is None:
            return None
        
        plot_window_size = config.PLOT_WINDOW_SIZE
        
        if self.is_custom_audio and len(self.audio_data) > plot_window_size:
            peak_index = np.argmax(np.abs(self.audio_data))
            start_index = max(0, peak_index - plot_window_size // 2)
            end_index = min(len(self.audio_data), start_index + plot_window_size)
            start_index = max(0, end_index - plot_window_size)
        else:
            start_index = 0
            end_index = min(plot_window_size, len(self.audio_data))
        
        input_slice = self.audio_data[start_index:end_index]
        output_slice = self.output_audio[start_index:end_index] if self.output_audio is not None else np.zeros_like(input_slice)
        time = np.arange(len(input_slice)) / self.sample_rate
        
        return {
            'time': time,
            'input_slice': input_slice,
            'output_slice': output_slice
        }
    
    def prepare_audio_for_playback(self):
        """
        Prepare output audio for playback (normalize and clip)
        
        Returns:
            tuple: (success: bool, audio_data: np.array or None, message: str)
        """
        if self.output_audio is None:
            return False, None, "No audio to play"
        
        output_for_playback = self.output_audio.copy()
        max_abs = np.max(np.abs(output_for_playback))
        
        if max_abs > 1e-6:
            output_for_playback = output_for_playback / max_abs * 0.5
        else:
            return False, None, "Audio too quiet. Increase gain parameters."
        
        output_for_playback = np.clip(output_for_playback, -1.0, 1.0)
        
        return True, output_for_playback.astype(np.float32), "Ready to play"
