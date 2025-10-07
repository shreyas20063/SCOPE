"""
GUI Module for Amplifier Simulator
Contains all UI components and plotting functionality
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import customtkinter as ctk
from tkinter import filedialog, messagebox

import config
from utils.helpers import GainCalculator


class AmplifierGUI:
    """Manages the graphical user interface"""
    
    def __init__(self, root, audio_processor, audio_player, circuit_images):
        self.root = root
        self.audio_processor = audio_processor
        self.audio_player = audio_player
        self.circuit_images = circuit_images
        
        # Setup window
        self.root.title(config.WINDOW_TITLE)
        self.root.geometry(config.WINDOW_SIZE)
        ctk.set_appearance_mode(config.APPEARANCE_MODE)
        ctk.set_default_color_theme(config.COLOR_THEME)
        
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        # System parameters as StringVars for sliders
        self.K = ctk.DoubleVar(value=config.K_DEFAULT)
        self.F0 = ctk.DoubleVar(value=config.F0_DEFAULT)
        self.beta = ctk.DoubleVar(value=config.BETA_DEFAULT)
        self.VT = config.VT_DEFAULT
        
        self.current_mode = ctk.StringVar(value='simple')
        self.output_plot_limit = config.INITIAL_OUTPUT_LIMIT
        
        # Callbacks (to be set by main app)
        self.on_parameter_change = None
        self.on_load_audio = None
        self.on_play_audio = None
        self.on_reset = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the complete user interface"""
        # Create main frames
        left_frame = ctk.CTkFrame(self.root, width=400)
        left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        plot_frame = ctk.CTkFrame(self.root)
        plot_frame.grid(row=0, column=1, padx=(0, 10), pady=10, sticky="nsew")
        
        # Setup left panel
        self._setup_left_panel(left_frame)
        
        # Setup plotting area
        self._setup_plots(plot_frame)
    
    def _setup_left_panel(self, parent):
        """Setup the left control panel"""
        # Title
        ctk.CTkLabel(
            parent, 
            text="Amplifier Controls", 
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=(10, 15))
        
        # Mode selection
        config_frame = ctk.CTkFrame(parent)
        config_frame.pack(pady=5, padx=10, fill="x")
        ctk.CTkLabel(
            config_frame, 
            text="Amplifier Configuration", 
            font=ctk.CTkFont(weight="bold")
        ).pack(pady=(5, 5))
        
        for text, value in config.AMPLIFIER_CONFIGS:
            ctk.CTkRadioButton(
                config_frame, 
                text=text, 
                variable=self.current_mode, 
                value=value, 
                command=self._on_mode_change
            ).pack(anchor="w", padx=10, pady=3)
        
        # Image display
        self.image_label = ctk.CTkLabel(parent, text="")
        self.image_label.pack(pady=10, padx=10, fill="x")
        
        # Parameter sliders
        self._create_slider(parent, "F₀ - Power Amp Gain", self.F0, config.F0_MIN, config.F0_MAX)
        self._create_slider(parent, "K - Forward Gain", self.K, config.K_MIN, config.K_MAX)
        self._create_slider(parent, "β - Feedback Factor", self.beta, config.BETA_MIN, config.BETA_MAX)
        
        # Audio controls
        self._setup_audio_controls(parent)
    
    def _setup_audio_controls(self, parent):
        """Setup audio control buttons"""
        audio_frame = ctk.CTkFrame(parent)
        audio_frame.pack(pady=(15, 10), padx=10, fill="x", side="bottom")
        
        self.file_label = ctk.CTkLabel(audio_frame, text="Input: Pure Sine Wave")
        self.file_label.pack(pady=5)
        
        ctk.CTkButton(
            audio_frame, 
            text="Load Audio File...", 
            command=self._handle_load_audio
        ).pack(pady=5, fill="x")
        
        self.play_button = ctk.CTkButton(
            audio_frame, 
            text="▶ Play Output", 
            command=self._handle_play_audio
        )
        self.play_button.pack(pady=5, fill="x")
        
        ctk.CTkButton(
            audio_frame, 
            text="■ Stop Audio", 
            command=self._handle_stop_audio
        ).pack(pady=5, fill="x")
        
        ctk.CTkButton(
            audio_frame, 
            text="⟲ Reset Parameters", 
            command=self._handle_reset,
            fg_color=config.COLOR_RESET_BUTTON, 
            text_color="black"
        ).pack(pady=(10, 5), fill="x")
    
    def _create_slider(self, parent, text, variable, min_val, max_val):
        """Create a parameter slider with label"""
        frame = ctk.CTkFrame(parent)
        frame.pack(pady=4, padx=10, fill="x")
        
        label = ctk.CTkLabel(
            frame, 
            text=f"{text}: {variable.get():.2f}", 
            font=ctk.CTkFont(weight="bold")
        )
        label.pack(pady=(5, 0))
        
        slider = ctk.CTkSlider(
            frame, 
            from_=min_val, 
            to=max_val, 
            variable=variable,
            command=lambda v: self._slider_update(v, label, text)
        )
        slider.pack(fill="x", padx=10, pady=(0, 5))
    
    def _slider_update(self, value, label, text):
        """Handle slider updates"""
        label.configure(text=f"{text}: {value:.2f}")
        if self.on_parameter_change:
            self.on_parameter_change()
    
    def _on_mode_change(self):
        """Handle mode change"""
        if self.on_parameter_change:
            self.on_parameter_change()
    
    def _handle_load_audio(self):
        """Handle audio file loading"""
        file_path = filedialog.askopenfilename(
            filetypes=[("Audio Files", "*.wav *.mp3")]
        )
        if self.on_load_audio:
            self.on_load_audio(file_path)
    
    def _handle_play_audio(self):
        """Handle play audio button"""
        if self.on_play_audio:
            self.on_play_audio()
    
    def _handle_stop_audio(self):
        """Handle stop audio button"""
        self.audio_player.stop()
    
    def _handle_reset(self):
        """Handle reset button"""
        if self.on_reset:
            self.on_reset()
    
    def _setup_plots(self, parent):
        """Setup matplotlib plots"""
        plt.style.use(config.PLOT_STYLE)
        
        self.fig = Figure(figsize=(10, 8), dpi=100)
        gs = self.fig.add_gridspec(2, 2, hspace=0.45, wspace=0.3)
        
        self.ax_input = self.fig.add_subplot(gs[0, 0])
        self.ax_output = self.fig.add_subplot(gs[0, 1])
        self.ax_gain_curve = self.fig.add_subplot(gs[1, 0])
        self.ax_xy_plot = self.fig.add_subplot(gs[1, 1])
        
        self.fig.tight_layout(pad=2.0)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
    
    def update_circuit_image(self):
        """Update circuit diagram based on current mode"""
        current_mode = self.current_mode.get()
        image_to_display = self.circuit_images.get(current_mode)
        
        if image_to_display:
            self.image_label.configure(image=image_to_display, text="")
        else:
            self.image_label.configure(
                image=None, 
                text=f"Image for '{current_mode}' not found."
            )
    
    def update_plots(self):
        """Update all visualization plots"""
        # Clear all axes
        for ax in self.fig.axes:
            ax.clear()
        
        plot_data = self.audio_processor.get_plot_data()
        if plot_data is None:
            return
        
        time = plot_data['time']
        input_slice = plot_data['input_slice']
        output_slice = plot_data['output_slice']
        
        K_val = self.K.get()
        F0_val = self.F0.get()
        beta_val = self.beta.get()
        
        # Input plot
        self._plot_input(time, input_slice)
        
        # Output plot
        self._plot_output(time, output_slice)
        
        # Gain curve
        self._plot_gain_curve(K_val, F0_val, beta_val)
        
        # XY plot (linearity)
        self._plot_xy(input_slice, output_slice)
        
        self.fig.canvas.draw_idle()
    
    def _plot_input(self, time, input_slice):
        """Plot input signal"""
        self.ax_input.plot(time, input_slice, config.COLOR_INPUT, lw=2, label='Input')
        self.ax_input.set_title('Input Signal (Time Domain)')
        self.ax_input.set_xlabel('Time (s)')
        self.ax_input.set_ylabel('Amplitude')
        self.ax_input.legend(fontsize='small')
        self.ax_input.grid(True, linestyle=':', alpha=0.6)
        self.ax_input.set_ylim(config.INPUT_YLIM)
    
    def _plot_output(self, time, output_slice):
        """Plot output signal with dynamic scaling"""
        self.ax_output.plot(time, output_slice, config.COLOR_OUTPUT, lw=2, label='Output')
        self.ax_output.set_title('Output Signal (Time Domain)')
        self.ax_output.set_xlabel('Time (s)')
        self.ax_output.set_ylabel('Amplitude')
        self.ax_output.legend(fontsize='small')
        self.ax_output.grid(True, linestyle=':', alpha=0.6)
        
        if len(output_slice) > 0:
            max_output_amp = np.max(np.abs(output_slice))
            
            # Threshold-based scaling for "amplifying vibe"
            if max_output_amp > self.output_plot_limit * 0.95:
                self.output_plot_limit = max(max_output_amp * 1.2, 0.1)
            elif max_output_amp < self.output_plot_limit * 0.4 and self.output_plot_limit > 0.15:
                self.output_plot_limit = max(max_output_amp * 1.5, 0.1)
            
            if max_output_amp > self.output_plot_limit:
                self.output_plot_limit = max_output_amp * 1.2
            
            self.ax_output.set_ylim(-self.output_plot_limit, self.output_plot_limit)
    
    def _plot_gain_curve(self, K_val, F0_val, beta_val):
        """Plot gain vs F0 curves"""
        F0_range = np.linspace(config.F0_MIN, config.F0_MAX, 100)
        gain_simple, gain_feedback, ideal_gain = GainCalculator.calculate_gains(
            K_val, beta_val, F0_range
        )
        
        self.ax_gain_curve.plot(
            F0_range, gain_simple, 
            config.COLOR_SIMPLE_GAIN, ls='--', lw=2, label='Simple Gain'
        )
        self.ax_gain_curve.plot(
            F0_range, gain_feedback, 
            config.COLOR_FEEDBACK_GAIN, lw=2.5, label='Feedback Gain'
        )
        self.ax_gain_curve.axhline(
            ideal_gain, 
            color=config.COLOR_IDEAL_GAIN, ls=':', lw=2, label=r'Ideal (1/$\beta$)'
        )
        self.ax_gain_curve.axvline(
            F0_val, 
            color=config.COLOR_CURRENT_F0, ls='-.', lw=1.5, label=r'Current $F_0$'
        )
        
        self.ax_gain_curve.set_title(r'Gain vs. $F_0$ Variation')
        self.ax_gain_curve.set_xlabel(r'$F_0$')
        self.ax_gain_curve.set_ylabel('Gain')
        self.ax_gain_curve.legend(fontsize='small')
        self.ax_gain_curve.grid(True, linestyle=':', alpha=0.6)
        self.ax_gain_curve.set_ylim(min(gain_feedback)*0.9, max(gain_simple)*1.1)
    
    def _plot_xy(self, input_slice, output_slice):
        """Plot output vs input (linearity check)"""
        self.ax_xy_plot.plot(input_slice, output_slice, color=config.COLOR_XY_PLOT, lw=2)
        self.ax_xy_plot.set_title('Output vs. Input (Linearity)')
        self.ax_xy_plot.set_xlabel('Input Amplitude')
        self.ax_xy_plot.set_ylabel('Output Amplitude')
        self.ax_xy_plot.grid(True, linestyle=':', alpha=0.6)
        self.ax_xy_plot.axline((0, 0), slope=1, color='gray', ls='--', lw=1, alpha=0.7)
        
        if len(input_slice) > 0 and len(output_slice) > 0:
            max_abs_val = max(np.max(np.abs(input_slice)), np.max(np.abs(output_slice)))
            plot_limit = max(max_abs_val * 1.1, 0.011)
            self.ax_xy_plot.set_xlim(-plot_limit, plot_limit)
            self.ax_xy_plot.set_ylim(-plot_limit, plot_limit)
            self.ax_xy_plot.set_aspect('equal', 'box')
    
    def update_file_label(self, text):
        """Update the file label text"""
        self.file_label.configure(text=text)
    
    def reset_output_limit(self):
        """Reset output plot limit to default"""
        self.output_plot_limit = config.INITIAL_OUTPUT_LIMIT
    
    def get_parameters(self):
        """Get current parameter values"""
        return {
            'K': self.K.get(),
            'F0': self.F0.get(),
            'beta': self.beta.get(),
            'mode': self.current_mode.get(),
            'VT': self.VT
        }
    
    def set_parameters(self, K, F0, beta, mode):
        """Set parameter values"""
        self.K.set(K)
        self.F0.set(F0)
        self.beta.set(beta)
        self.current_mode.set(mode)