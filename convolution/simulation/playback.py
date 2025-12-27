"""
Playback controller for convolution animations.

This module manages animation timing, frame generation,
and playback controls for the convolution simulator.
"""

import numpy as np
import matplotlib.animation as animation
from typing import Callable, List, Optional, Union

class PlaybackController:
    """Controls animation playback for convolution visualization."""
    
    def __init__(self, update_callback: Callable):
        self.update_callback = update_callback
        self.reset()
    
    def reset(self):
        """Reset playback state."""
        self.animation = None
        self.is_playing = False
        self.is_continuous = True
        self.current_value = 0
        self.start_value = 0
        self.end_value = 10
        self.speed_multiplier = 1.0
        self.base_fps = 30
        self.frames = np.array([])
    
    def configure(self, start_val: float, end_val: float, 
                 is_continuous: bool = True, speed: float = 1.0):
        """
        Configure playback parameters.
        
        Args:
            start_val: Starting time/index value
            end_val: Ending time/index value
            is_continuous: Whether signal is continuous
            speed: Speed multiplier for playback
        """
        self.start_value = start_val
        self.end_value = end_val
        self.is_continuous = is_continuous
        self.speed_multiplier = speed
        self.current_value = start_val
        
        # Generate frame sequence
        if is_continuous:
            self.frames = np.linspace(start_val, end_val, 100)
        else:
            self.frames = np.arange(int(start_val), int(end_val) + 1)
    
    def start_animation(self, figure) -> bool:
        """
        Start the animation.
        
        Args:
            figure: Matplotlib figure object
            
        Returns:
            True if animation started successfully
        """
        if len(self.frames) == 0:
            return False
        
        if self.animation is not None:
            self.stop_animation()
        
        interval = self._calculate_interval()
        
        try:
            self.animation = animation.FuncAnimation(
                figure, self._animate_step, frames=self.frames,
                interval=interval, repeat=False, blit=False
            )
            self.is_playing = True
            return True
        except Exception as e:
            print(f"Animation start failed: {e}")
            return False
    
    def stop_animation(self):
        """Stop the current animation."""
        if self.animation is not None:
            self.animation.event_source.stop()
            self.animation = None
        self.is_playing = False
    
    def pause_animation(self):
        """Pause the animation."""
        if self.animation is not None:
            self.animation.event_source.stop()
        self.is_playing = False
    
    def resume_animation(self, figure):
        """Resume animation from current position."""
        if not self.is_playing and len(self.frames) > 0:
            # Find current frame index
            current_idx = self._find_current_frame_index()
            remaining_frames = self.frames[current_idx:]
            
            if len(remaining_frames) > 0:
                interval = self._calculate_interval()
                self.animation = animation.FuncAnimation(
                    figure, self._animate_step, frames=remaining_frames,
                    interval=interval, repeat=False, blit=False
                )
                self.is_playing = True
    
    def step_forward(self) -> float:
        """
        Step forward one frame.
        
        Returns:
            New current value
        """
        if self.is_continuous:
            step = (self.end_value - self.start_value) / 100
        else:
            step = 1
        
        self.current_value = min(self.current_value + step, self.end_value)
        self.update_callback(self.current_value)
        return self.current_value
    
    def step_backward(self) -> float:
        """
        Step backward one frame.
        
        Returns:
            New current value
        """
        if self.is_continuous:
            step = (self.end_value - self.start_value) / 100
        else:
            step = 1
        
        self.current_value = max(self.current_value - step, self.start_value)
        self.update_callback(self.current_value)
        return self.current_value
    
    def jump_to_value(self, value: float) -> float:
        """
        Jump directly to a specific value.
        
        Args:
            value: Target value
            
        Returns:
            Actual set value (clamped to bounds)
        """
        self.current_value = np.clip(value, self.start_value, self.end_value)
        self.update_callback(self.current_value)
        return self.current_value
    
    def jump_to_start(self) -> float:
        """Jump to start of animation."""
        return self.jump_to_value(self.start_value)
    
    def jump_to_end(self) -> float:
        """Jump to end of animation."""
        return self.jump_to_value(self.end_value)
    
    def set_speed(self, speed_multiplier: float):
        """
        Set playback speed.
        
        Args:
            speed_multiplier: Speed factor (1.0 = normal speed)
        """
        self.speed_multiplier = max(0.1, min(speed_multiplier, 10.0))
        
        # If currently playing, restart with new speed
        if self.is_playing and self.animation is not None:
            figure = self.animation.event_source.canvas.figure
            self.stop_animation()
            self.resume_animation(figure)
    
    def get_progress(self) -> float:
        """
        Get current progress as percentage.
        
        Returns:
            Progress from 0.0 to 1.0
        """
        if self.end_value <= self.start_value:
            return 0.0
        
        return (self.current_value - self.start_value) / (self.end_value - self.start_value)
    
    def set_progress(self, progress: float) -> float:
        """
        Set progress as percentage.
        
        Args:
            progress: Progress from 0.0 to 1.0
            
        Returns:
            Actual set value
        """
        progress = np.clip(progress, 0.0, 1.0)
        value = self.start_value + progress * (self.end_value - self.start_value)
        return self.jump_to_value(value)
    
    def _animate_step(self, value: Union[float, int]):
        """Animation step callback."""
        self.current_value = value
        self.update_callback(value)
        
        # Check if animation should stop
        if abs(value - self.end_value) < 1e-6:
            self.is_playing = False
    
    def _calculate_interval(self) -> float:
        """Calculate animation interval based on speed."""
        return 1000 / (self.base_fps * self.speed_multiplier)
    
    def _find_current_frame_index(self) -> int:
        """Find the index of current frame in the frames array."""
        if len(self.frames) == 0:
            return 0
        return np.argmin(np.abs(self.frames - self.current_value))
    
    def get_frame_info(self) -> dict:
        """Get information about current frame sequence."""
        return {
            'total_frames': len(self.frames),
            'current_frame': self._find_current_frame_index(),
            'start_value': self.start_value,
            'end_value': self.end_value,
            'current_value': self.current_value,
            'is_continuous': self.is_continuous,
            'speed_multiplier': self.speed_multiplier
        }
    
    def export_frame_sequence(self) -> np.ndarray:
        """Export the current frame sequence for external use."""
        return self.frames.copy()

class AnimationExporter:
    """Helper class for exporting animations to various formats."""
    
    @staticmethod
    def export_gif(figure, frames: np.ndarray, update_func: Callable,
                  filename: str, duration: float = 0.1) -> bool:
        """
        Export animation as GIF file.
        
        Args:
            figure: Matplotlib figure
            frames: Frame sequence array
            update_func: Function to update plots for each frame
            filename: Output filename
            duration: Frame duration in seconds
            
        Returns:
            True if export successful
        """
        try:
            import imageio
            
            with imageio.get_writer(filename, mode='I', duration=duration) as writer:
                for frame_val in frames:
                    update_func(frame_val)
                    figure.canvas.draw()
                    
                    # Convert figure to image array
                    figure.canvas.draw()
                    image = np.frombuffer(figure.canvas.tostring_rgb(), dtype='uint8')
                    image = image.reshape(figure.canvas.get_width_height()[::-1] + (3,))
                    writer.append_data(image)
            
            return True
        except Exception as e:
            print(f"GIF export failed: {e}")
            return False
    
    @staticmethod
    def export_frames_as_images(figure, frames: np.ndarray, update_func: Callable,
                               output_dir: str, prefix: str = "frame") -> bool:
        """
        Export individual frames as PNG images.
        
        Args:
            figure: Matplotlib figure
            frames: Frame sequence array
            update_func: Function to update plots for each frame
            output_dir: Output directory
            prefix: Filename prefix
            
        Returns:
            True if export successful
        """
        try:
            import os
            os.makedirs(output_dir, exist_ok=True)
            
            for i, frame_val in enumerate(frames):
                update_func(frame_val)
                figure.canvas.draw()
                
                filename = os.path.join(output_dir, f"{prefix}_{i:04d}.png")
                figure.savefig(filename, dpi=150, bbox_inches='tight')
            
            return True
        except Exception as e:
            print(f"Frame export failed: {e}")
            return False