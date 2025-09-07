"""
Main window implementation for the Convolution Simulator.

This module contains the primary GUI class that orchestrates all
user interface components and handles the main application logic.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation

# Import core modules
from core.convolution import ConvolutionEngine
from core.signals import SignalParser, DemoSignals
from core.utils import PlotUtils, AnimationUtils, ValidationUtils

# Import GUI components
from .controls import ControlPanel
from .plotting import PlotManager
from .themes import ThemeManager

class ConvolutionSimulator:
    """Main application class for the Convolution Simulator."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Convolution Simulator")
        self.root.geometry("1400x900")
        
        # Initialize core components
        self.convolution_engine = ConvolutionEngine()
        self.signal_parser = SignalParser()
        self.plot_utils = PlotUtils()
        self.animation_utils = AnimationUtils()
        
        # Initialize state variables
        self.setup_state_variables()
        
        # Initialize GUI components
        self.theme_manager = ThemeManager(self)
        self.setup_ui()
        self.plot_manager = PlotManager(self)
        self.control_panel = ControlPanel(self)
        
        # Bind events and initialize
        self.bind_events()
        self.theme_manager.apply_theme()
        self.update_mode_and_type()
    
    def setup_state_variables(self):
        """Initialize all state variables."""
        # Mode and type variables
        self.is_continuous = tk.BooleanVar(value=True)
        self.is_demo_mode = tk.BooleanVar(value=True)
        self.demo_choice = tk.StringVar()
        self.custom_x_str = tk.StringVar(value="rect(t)")
        self.custom_h_str = tk.StringVar(value="exp(-t) * u(t)")
        self.visualization_style = tk.StringVar(value="Mathematical")
        self.dark_mode = tk.BooleanVar(value=False)
        
        # Simulation variables
        self.t = np.linspace(-20, 20, 8000)
        self.n = np.arange(-10, 21)
        self.t_y = np.array([])
        self.n_y = np.array([])
        self.x_func = lambda t: np.zeros_like(t)
        self.h_func = lambda t: np.zeros_like(t)
        self.x_sequence = np.zeros_like(self.n)
        self.h_sequence = np.zeros_like(self.n)
        self.y_result = np.zeros_like(self.t)
        
        # Animation variables
        self.anim = None
        self.current_time_val = 0
        self.is_playing = False
    
    def setup_ui(self):
        """Create and layout all UI components."""
        # Create main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create header
        self.header_frame = self.create_header(main_frame)
        self.header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Create body with panels
        body_frame = ttk.Frame(main_frame)
        body_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left control panel
        self.left_panel = self.create_left_panel(body_frame)
        self.left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # Center plotting area
        self.center_panel = self.create_center_panel(body_frame)
        self.center_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Right panel (initially hidden)
        self.right_panel = self.create_right_panel(body_frame)
        self.right_panel.pack_forget()
        
        # Footer
        self.footer_frame = self.create_footer(main_frame)
        self.footer_frame.pack(fill=tk.X, pady=(10, 0))
    
    def create_header(self, parent):
        """Create the header with main controls."""
        header_frame = ttk.Frame(parent)
        
        # Title
        title_label = ttk.Label(header_frame, text="Convolution Simulator", 
                               font=("Helvetica", 16, "bold"))
        title_label.pack(side=tk.LEFT, padx=(0, 20))
        
        # Signal type selection
        ttk.Radiobutton(header_frame, text="Continuous", 
                       variable=self.is_continuous, value=True,
                       command=self.update_mode_and_type).pack(side=tk.LEFT)
        ttk.Radiobutton(header_frame, text="Discrete", 
                       variable=self.is_continuous, value=False,
                       command=self.update_mode_and_type).pack(side=tk.LEFT, padx=(0, 20))
        
        # Mode selection
        ttk.Radiobutton(header_frame, text="Demo Mode", 
                       variable=self.is_demo_mode, value=True,
                       command=self.update_mode_and_type).pack(side=tk.LEFT)
        
        self.demo_selector = ttk.Combobox(header_frame, textvariable=self.demo_choice, 
                                         state="readonly", width=35)
        self.demo_selector.pack(side=tk.LEFT, padx=5)
        
        ttk.Radiobutton(header_frame, text="Custom Mode", 
                       variable=self.is_demo_mode, value=False,
                       command=self.update_mode_and_type).pack(side=tk.LEFT, padx=(10, 0))
        
        # Theme toggle
        ttk.Checkbutton(header_frame, text="Dark Mode", 
                       variable=self.dark_mode, 
                       command=self.theme_manager.toggle_theme).pack(side=tk.RIGHT)
        
        return header_frame
    
    def create_left_panel(self, parent):
        """Create the left control panel."""
        panel = ttk.Frame(parent, width=250)
        panel.pack_propagate(False)
        return panel
    
    def create_center_panel(self, parent):
        """Create the center plotting panel."""
        panel = ttk.Frame(parent)
        
        # Create matplotlib figure
        self.fig = Figure(figsize=(8, 8), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=panel)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Create subplots
        self.ax_x = self.fig.add_subplot(4, 1, 1)
        self.ax_h = self.fig.add_subplot(4, 1, 2)
        self.ax_prod = self.fig.add_subplot(4, 1, 3)
        self.ax_y = self.fig.add_subplot(4, 1, 4)
        
        self.fig.tight_layout()
        return panel
    
    def create_right_panel(self, parent):
        """Create the right panel for block-step visualization."""
        panel = ttk.Frame(parent, width=300)
        panel.pack_propagate(False)
        
        # Create figure for block diagram
        self.block_fig = Figure(figsize=(4, 8), dpi=100)
        self.block_canvas = FigureCanvasTkAgg(self.block_fig, master=panel)
        self.block_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Create block diagram subplots
        self.ax_block_flip = self.block_fig.add_subplot(5, 1, 1)
        self.ax_block_shift = self.block_fig.add_subplot(5, 1, 2)
        self.ax_block_multiply = self.block_fig.add_subplot(5, 1, 3)
        self.ax_block_sum = self.block_fig.add_subplot(5, 1, 4)
        
        self.block_fig.tight_layout()
        return panel
    
    def create_footer(self, parent):
        """Create the footer with math display."""
        footer_frame = ttk.Frame(parent)
        
        self.math_label = ttk.Label(footer_frame, 
                                   text="y(t) = ∫ x(τ)h(t-τ)dτ", 
                                   font=("Helvetica", 12))
        self.math_label.pack(side=tk.LEFT)
        
        self.reference_label = ttk.Label(footer_frame, 
                                        text="Ref: MIT 6.003F11 Lec 08", 
                                        foreground="blue", cursor="hand2")
        self.reference_label.pack(side=tk.RIGHT)
        
        return footer_frame
    
    def bind_events(self):
        """Bind keyboard and other events."""
        self.demo_selector.bind("<<ComboboxSelected>>", self.on_demo_selected)
        self.root.bind("<space>", lambda e: self.toggle_animation())
        self.root.bind("<Right>", lambda e: self.step_forward())
        self.root.bind("<Left>", lambda e: self.step_backward())
        self.root.focus_set()  # Allow keyboard events
    
    def update_mode_and_type(self, event=None):
        """Update UI and state when mode or signal type changes."""
        self.stop_animation()
        
        if self.is_demo_mode.get():
            self.demo_selector.config(state="readonly")
            # Update demo choices based on signal type
            choices = DemoSignals.get_demo_choices(self.is_continuous.get())
            self.demo_selector['values'] = choices
            if choices:
                self.demo_choice.set(choices[0])
            self.on_demo_selected()
        else:
            self.demo_selector.config(state="disabled")
            # Set default custom expressions
            if self.is_continuous.get():
                self.custom_x_str.set("exp(-t) * u(t)")
                self.custom_h_str.set("rect(t-1)")
            else:
                self.custom_x_str.set("0.5**n * u(n)")
                self.custom_h_str.set("[1, 1, 1]")
        
        self.compute_convolution()
    
    def on_demo_selected(self, event=None):
        """Handle demo selection."""
        choice = self.demo_choice.get()
        x_expr, h_expr = DemoSignals.get_demo_signals(choice, self.is_continuous.get())
        self.custom_x_str.set(x_expr)
        self.custom_h_str.set(h_expr)
        self.compute_convolution()
    
    def compute_convolution(self):
        """Compute convolution for current signals."""
        self.stop_animation()
        
        try:
            if self.is_continuous.get():
                self._compute_continuous_convolution()
            else:
                self._compute_discrete_convolution()
            
            self._update_slider_range()
            self.plot_manager.update_plots()
            
        except Exception as e:
            messagebox.showerror("Computation Error", 
                               f"Error computing convolution: {str(e)}")
    
    def _compute_continuous_convolution(self):
        """Compute continuous-time convolution."""
        x_expr = self.signal_parser.parse_expression(self.custom_x_str.get(), 't')
        h_expr = self.signal_parser.parse_expression(self.custom_h_str.get(), 't')
        
        self.x_func = self.signal_parser.create_function_from_expression(x_expr, 't')
        self.h_func = self.signal_parser.create_function_from_expression(h_expr, 't')
        
        # Get sampling rate from control panel
        sampling_rate = getattr(self.control_panel, 'get_sampling_rate', lambda: 500)()
        
        self.t_y, self.y_result = self.convolution_engine.compute_continuous_convolution(
            self.x_func, self.h_func, sampling_rate
        )
    
    def _compute_discrete_convolution(self):
        """Compute discrete-time convolution."""
        self.n = np.arange(-20, 21)
        
        x_expr = self.signal_parser.parse_expression(self.custom_x_str.get(), 'n')
        h_expr = self.signal_parser.parse_expression(self.custom_h_str.get(), 'n')
        
        # Parse sequences
        raw_x, start_x = self.signal_parser.parse_discrete_sequence(x_expr, self.n)
        raw_h, start_h = self.signal_parser.parse_discrete_sequence(h_expr, self.n)
        
        # Create full sequences on n grid
        self.x_sequence = np.zeros_like(self.n, dtype=float)
        self.h_sequence = np.zeros_like(self.n, dtype=float)
        
        # Place sequences at correct positions
        for i, val in enumerate(raw_x):
            idx = start_x + i
            if self.n[0] <= idx <= self.n[-1]:
                self.x_sequence[idx - self.n[0]] = val
        
        for i, val in enumerate(raw_h):
            idx = start_h + i
            if self.n[0] <= idx <= self.n[-1]:
                self.h_sequence[idx - self.n[0]] = val
        
        self.n_y, self.y_result = self.convolution_engine.compute_discrete_convolution(
            raw_x, raw_h, start_x, start_h
        )
    
    def _update_slider_range(self):
        """Update time slider range based on computed results."""
        if hasattr(self.control_panel, 'update_time_slider_range'):
            if self.is_continuous.get():
                slider_min, slider_max = -15, 15
            elif len(self.n_y) > 0:
                slider_min = min(self.n_y[0], self.n[0]) - 2
                slider_max = max(self.n_y[-1], self.n[-1]) + 2
            else:
                slider_min, slider_max = -10, 10
            
            self.control_panel.update_time_slider_range(slider_min, slider_max)
    
    def toggle_animation(self):
        """Toggle animation play/pause."""
        if self.anim and self.is_playing:
            self.stop_animation()
        else:
            self.start_animation()
    
    def start_animation(self):
        """Start convolution animation."""
        if hasattr(self.control_panel, 'get_time_range'):
            start_val, end_val = self.control_panel.get_time_range()
            speed_multiplier = getattr(self.control_panel, 'get_playback_speed', lambda: 1.0)()
            
            frames = self.animation_utils.create_frame_sequence(
                start_val, end_val, self.is_continuous.get()
            )
            interval = self.animation_utils.calculate_animation_interval(speed_multiplier)
            
            self.anim = animation.FuncAnimation(
                self.fig, self.animate_step, frames=frames,
                interval=interval, repeat=False, blit=False
            )
            self.is_playing = True
            self.canvas.draw()
    
    def stop_animation(self):
        """Stop convolution animation."""
        if self.anim:
            self.anim.event_source.stop()
            self.anim = None
        self.is_playing = False
    
    def animate_step(self, time_val):
        """Animation step function."""
        self.current_time_val = time_val
        if hasattr(self.control_panel, 'set_time_value'):
            self.control_panel.set_time_value(time_val)
        self.plot_manager.update_plots(time_val)
    
    def step_forward(self):
        """Step animation forward."""
        if hasattr(self.control_panel, 'step_time_forward'):
            self.control_panel.step_time_forward()
    
    def step_backward(self):
        """Step animation backward."""
        if hasattr(self.control_panel, 'step_time_backward'):
            self.control_panel.step_time_backward()
    
    # Getter methods for plot manager
    def get_current_axes(self):
        """Get current matplotlib axes."""
        return [self.ax_x, self.ax_h, self.ax_prod, self.ax_y]
    
    def get_block_axes(self):
        """Get block diagram axes."""
        return [self.ax_block_flip, self.ax_block_shift, 
                self.ax_block_multiply, self.ax_block_sum]
    
    def get_current_signals(self):
        """Get current signal data."""
        return {
            'x_func': self.x_func,
            'h_func': self.h_func,
            'x_sequence': self.x_sequence,
            'h_sequence': self.h_sequence,
            't': self.t,
            'n': self.n,
            't_y': self.t_y,
            'n_y': self.n_y,
            'y_result': self.y_result
        }
