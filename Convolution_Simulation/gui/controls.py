"""
Control panel components for the Convolution Simulator.

This module handles all user controls including sliders, buttons,
input fields, and parameter adjustments.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv

class ControlPanel:
    """Manages the left control panel with all user controls."""
    
    def __init__(self, main_app):
        self.app = main_app
        self.panel = main_app.left_panel
        
        self.setup_controls()
    
    def setup_controls(self):
        """Create all control widgets."""
        self.create_custom_input_frame()
        self.create_parameters_frame()
        self.create_buttons_frame()
        self.create_visualization_frame()
        self.create_export_frame()
    
    def create_custom_input_frame(self):
        """Create custom signal input controls."""
        self.custom_frame = ttk.LabelFrame(self.panel, text="Custom Input", padding=10)
        self.custom_frame.pack(fill=tk.X, pady=10)
        
        # X signal input
        ttk.Label(self.custom_frame, text="x(t) or x[n]:").pack(anchor=tk.W)
        self.x_entry = ttk.Entry(self.custom_frame, textvariable=self.app.custom_x_str)
        self.x_entry.pack(fill=tk.X, pady=(0, 5))
        self.x_entry.bind('<Return>', self._on_expression_changed)
        
        # H signal input
        ttk.Label(self.custom_frame, text="h(t) or h[n]:").pack(anchor=tk.W)
        self.h_entry = ttk.Entry(self.custom_frame, textvariable=self.app.custom_h_str)
        self.h_entry.pack(fill=tk.X)
        self.h_entry.bind('<Return>', self._on_expression_changed)
    
    def create_parameters_frame(self):
        """Create parameter control sliders."""
        params_frame = ttk.LabelFrame(self.panel, text="Parameters", padding=10)
        params_frame.pack(fill=tk.X, pady=10)
        
        # Time/Index slider
        self.time_slider = self._create_slider(
            params_frame, "Time/Index (t or n)", -5, 5, 0, self._on_time_slider_change
        )
        
        # Playback speed slider
        self.playback_speed_slider = self._create_slider(
            params_frame, "Playback Speed (x)", 0.1, 4, 1, self._on_playback_speed_change
        )
        
        # Sampling rate slider
        self.sampling_rate_slider = self._create_slider(
            params_frame, "Sampling Rate (Hz)", 50, 2000, 500
        )
    
    def create_buttons_frame(self):
        """Create control buttons."""
        buttons_frame = ttk.LabelFrame(self.panel, text="Controls", padding=10)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        # Playback controls
        playback_frame = ttk.Frame(buttons_frame)
        playback_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.play_pause_button = ttk.Button(
            playback_frame, text="Play", command=self.app.toggle_animation
        )
        self.play_pause_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        
        self.step_forward_button = ttk.Button(
            playback_frame, text="Step →", command=self.step_time_forward
        )
        self.step_forward_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        
        ttk.Button(
            playback_frame, text="Reset", command=self.reset_simulation
        ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        
        # Compute button
        compute_button = ttk.Button(
            buttons_frame, text="Compute Convolution", 
            command=self.app.compute_convolution
        )
        compute_button.pack(fill=tk.X, pady=5, ipady=5)
        
        # Configure accent style for compute button
        style = ttk.Style()
        style.configure("Accent.TButton", font=("Helvetica", 10, "bold"))
        compute_button.configure(style="Accent.TButton")
    
    def create_visualization_frame(self):
        """Create visualization style controls."""
        vis_frame = ttk.LabelFrame(self.panel, text="Visualization Style", padding=10)
        vis_frame.pack(fill=tk.X, pady=10)
        
        ttk.Radiobutton(
            vis_frame, text="Mathematical", 
            variable=self.app.visualization_style, value="Mathematical",
            command=self._toggle_visualization_style
        ).pack(anchor=tk.W)
        
        ttk.Radiobutton(
            vis_frame, text="Block-Step", 
            variable=self.app.visualization_style, value="Block-Step",
            command=self._toggle_visualization_style
        ).pack(anchor=tk.W)
    
    def create_export_frame(self):
        """Create export controls."""
        export_frame = ttk.LabelFrame(self.panel, text="Export", padding=10)
        export_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(
            export_frame, text="Save Snapshot (PNG)", 
            command=self.save_snapshot
        ).pack(fill=tk.X, pady=2)
        
        ttk.Button(
            export_frame, text="Export Data (CSV)", 
            command=self.export_data
        ).pack(fill=tk.X, pady=2)
        
        ttk.Button(
            export_frame, text="Save Animation (GIF)", 
            command=self.save_animation
        ).pack(fill=tk.X, pady=2)
    
    def _create_slider(self, parent, label, from_, to, default, command=None):
        """Helper to create labeled slider."""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(frame, text=label).pack(side=tk.LEFT)
        
        var = tk.DoubleVar(value=default)
        slider = ttk.Scale(
            frame, from_=from_, to=to, variable=var, 
            orient=tk.HORIZONTAL, command=command
        )
        slider.pack(side=tk.RIGHT, expand=True, fill=tk.X)
        slider.variable = var
        
        return slider
    
    def _on_time_slider_change(self, val):
        """Handle time slider changes."""
        time_val = float(val)
        self.app.current_time_val = time_val
        if hasattr(self.app, 'plot_manager'):
            self.app.plot_manager.update_plots(time_val)
    
    def _on_playback_speed_change(self, val):
        """Handle playback speed changes during animation."""
        if self.app.anim is not None and self.app.is_playing:
            self._restart_animation_with_new_speed()
    
    def _restart_animation_with_new_speed(self):
        """Restart animation with updated speed."""
        current_time = self.app.current_time_val
        self.app.stop_animation()
        
        # Restart from current position
        start_val, end_val = self.get_time_range()
        speed_multiplier = self.get_playback_speed()
        
        frames = self.app.animation_utils.create_frame_sequence(
            current_time, end_val, self.app.is_continuous.get()
        )
        
        if len(frames) > 0:
            interval = self.app.animation_utils.calculate_animation_interval(speed_multiplier)
            self.app.anim = self.app.animation.FuncAnimation(
                self.app.fig, self.app.animate_step, frames=frames,
                interval=interval, repeat=False
            )
            self.app.is_playing = True
            self.app.canvas.draw()
    
    def _on_expression_changed(self, event=None):
        """Handle expression input changes."""
        self.app.compute_convolution()
    
    def _toggle_visualization_style(self):
        """Toggle between mathematical and block-step visualization."""
        if self.app.visualization_style.get() == "Block-Step":
            self.app.right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        else:
            self.app.right_panel.pack_forget()
        
        if hasattr(self.app, 'plot_manager'):
            self.app.plot_manager.update_plots()
    
    # Public interface methods
    def update_time_slider_range(self, min_val, max_val):
        """Update the time slider range."""
        self.time_slider.configure(from_=min_val, to=max_val)
        self.time_slider.variable.set(min_val)
    
    def get_time_range(self):
        """Get current time slider range."""
        return (self.time_slider.cget('from'), self.time_slider.cget('to'))
    
    def get_time_value(self):
        """Get current time slider value."""
        return self.time_slider.variable.get()
    
    def set_time_value(self, value):
        """Set time slider value."""
        self.time_slider.variable.set(value)
    
    def get_playback_speed(self):
        """Get current playback speed."""
        return self.playback_speed_slider.variable.get()
    
    def get_sampling_rate(self):
        """Get current sampling rate."""
        return self.sampling_rate_slider.variable.get()
    
    def step_time_forward(self):
        """Step time forward."""
        current_val = self.get_time_value()
        if self.app.is_continuous.get():
            start_val, end_val = self.get_time_range()
            step = (end_val - start_val) / 100
        else:
            step = 1
        
        new_val = min(current_val + step, self.get_time_range()[1])
        self.set_time_value(new_val)
        if hasattr(self.app, 'plot_manager'):
            self.app.plot_manager.update_plots(new_val)
    
    def step_time_backward(self):
        """Step time backward."""
        current_val = self.get_time_value()
        if self.app.is_continuous.get():
            start_val, end_val = self.get_time_range()
            step = (end_val - start_val) / 100
        else:
            step = 1
        
        new_val = max(current_val - step, self.get_time_range()[0])
        self.set_time_value(new_val)
        if hasattr(self.app, 'plot_manager'):
            self.app.plot_manager.update_plots(new_val)
    
    def reset_simulation(self):
        """Reset simulation to start."""
        start_val = self.get_time_range()[0]
        self.set_time_value(start_val)
        if hasattr(self.app, 'plot_manager'):
            self.app.plot_manager.update_plots(start_val)
    
    def enable_custom_inputs(self):
        """Enable custom input fields."""
        self.x_entry.config(state="normal")
        self.h_entry.config(state="normal")
    
    def disable_custom_inputs(self):
        """Disable custom input fields."""
        self.x_entry.config(state="disabled")
        self.h_entry.config(state="disabled")
    
    def update_play_button_text(self, is_playing):
        """Update play button text based on state."""
        text = "Pause" if is_playing else "Play"
        self.play_pause_button.config(text=text)
    
    # Export methods
    def save_snapshot(self):
        """Save current plot as PNG image."""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        if filepath:
            try:
                self.app.fig.savefig(filepath, dpi=300, bbox_inches='tight')
                messagebox.showinfo("Success", f"Snapshot saved to {filepath}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save snapshot: {e}")
    
    def export_data(self):
        """Export convolution data as CSV."""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filepath:
            try:
                with open(filepath, 'w', newline='') as f:
                    writer = csv.writer(f)
                    
                    if self.app.is_continuous.get() and len(self.app.t_y) > 0:
                        writer.writerow(['t', 'y(t)'])
                        for i in range(len(self.app.t_y)):
                            writer.writerow([self.app.t_y[i], self.app.y_result[i]])
                    elif not self.app.is_continuous.get() and len(self.app.n_y) > 0:
                        writer.writerow(['n', 'y[n]'])
                        for i in range(len(self.app.n_y)):
                            writer.writerow([self.app.n_y[i], self.app.y_result[i]])
                    else:
                        writer.writerow(['No data to export'])
                
                messagebox.showinfo("Success", f"Data exported to {filepath}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export data: {e}")
    
    def save_animation(self):
        """Save animation as GIF."""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".gif",
            filetypes=[("GIF files", "*.gif"), ("All files", "*.*")]
        )
        if not filepath:
            return
        
        try:
            import imageio
            messagebox.showinfo("Saving Animation", 
                              "This may take a moment. The app will be unresponsive during saving.")
            
            start_val, end_val = self.get_time_range()
            if self.app.is_continuous.get():
                frames = self.app.animation_utils.create_frame_sequence(
                    start_val, end_val, True, 75
                )
            else:
                frames = self.app.animation_utils.create_frame_sequence(
                    start_val, end_val, False
                )
            
            with imageio.get_writer(filepath, mode='I', duration=0.1) as writer:
                for time_val in frames:
                    if hasattr(self.app, 'plot_manager'):
                        self.app.plot_manager.update_plots(time_val)
                    self.app.fig.canvas.draw()
                    
                    # Get image data
                    image = self.app.fig.canvas.buffer_rgba()
                    image = image.reshape(self.app.fig.canvas.get_width_height()[::-1] + (4,))
                    # Convert RGBA to RGB
                    image_rgb = image[:, :, :3]
                    writer.append_data(image_rgb)
            
            messagebox.showinfo("Success", f"Animation saved to {filepath}")
            
        except ImportError:
            messagebox.showerror("Error", "imageio library not found. Please install it with: pip install imageio")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save animation: {e}")