"""
Simulation Catalog - Contains metadata for all 13 simulations.

Each simulation entry includes:
- id: Unique identifier
- name: Display name
- description: Brief description
- category: Category for grouping
- thumbnail: Emoji icon
- tags: Search tags
- has_simulator: Whether a simulator class exists
- controls: List of parameter definitions
- default_params: Default parameter values
- plots: List of plot definitions
"""

# Category definitions with colors
CATEGORIES = {
    "Signal Processing": {"color": "#06b6d4", "icon": "wave"},
    "Circuits": {"color": "#8b5cf6", "icon": "circuit"},
    "Control Systems": {"color": "#f59e0b", "icon": "gear"},
    "Transforms": {"color": "#10b981", "icon": "transform"},
    "Optics": {"color": "#ec4899", "icon": "lens"},
}

# Complete simulation catalog with parameter definitions from 4A analysis
SIMULATION_CATALOG = [
    # =========================================================================
    # 1. RC LOWPASS FILTER
    # =========================================================================
    {
        "id": "rc_lowpass_filter",
        "name": "RC Lowpass Filter",
        "description": "Interactive RC filter simulation showing frequency response and filtering of square wave input signals. Adjust frequency and RC time constant in real-time.",
        "category": "Circuits",
        "thumbnail": "📉",
        "tags": ["filter", "frequency response", "bode plot", "cutoff"],
        "has_simulator": True,
        "controls": [
            {"type": "slider", "name": "frequency", "label": "Input Frequency", "min": 1, "max": 300, "step": 1, "default": 100, "unit": "Hz", "group": "Input Signal"},
            {"type": "slider", "name": "rc_ms", "label": "RC Time Constant", "min": 0.1, "max": 10.0, "step": 0.01, "default": 1.0, "unit": "ms", "group": "Filter"},
            {"type": "slider", "name": "amplitude", "label": "Input Amplitude", "min": 1.0, "max": 10.0, "step": 0.1, "default": 5.0, "unit": "V", "group": "Input Signal"},
        ],
        "default_params": {"frequency": 100, "rc_ms": 1.0, "amplitude": 5.0},
        "plots": [
            {"id": "time_domain", "title": "Time Domain", "description": "Input and output signals over time"},
            {"id": "bode", "title": "Frequency Domain (Bode Plot)", "description": "Filter magnitude response with harmonics"},
        ],
    },

    # =========================================================================
    # 2. ALIASING & QUANTIZATION (Matching PyQt5 with 3 demo modes)
    # =========================================================================
    {
        "id": "aliasing_quantization",
        "name": "Aliasing & Quantization",
        "description": "Explore the Nyquist theorem, aliasing effects, and compare quantization methods (Standard, Dither, Robert's). Features audio aliasing, audio quantization, and image quantization demos.",
        "category": "Signal Processing",
        "thumbnail": "📊",
        "tags": ["nyquist", "sampling", "ADC", "digital", "dither", "quantization", "aliasing"],
        "has_simulator": True,
        "controls": [
            # Note: demo_mode is controlled by tabs in AliasingQuantizationViewer (not in control panel)
            # Aliasing Demo Controls
            {"type": "slider", "name": "downsample_factor", "label": "Downsampling Factor", "min": 1, "max": 20, "step": 1, "default": 4, "unit": "x", "group": "Aliasing", "visible_when": {"demo_mode": "aliasing"}},
            {"type": "checkbox", "name": "anti_aliasing", "label": "Anti-Aliasing Filter", "default": False, "group": "Aliasing", "visible_when": {"demo_mode": "aliasing"}},
            # Audio Quantization Demo Controls - method selector at top
            {"type": "select", "name": "quant_method", "label": "Method", "options": [
                {"value": "standard", "label": "Standard"},
                {"value": "dither", "label": "Dither"},
                {"value": "roberts", "label": "Robert's"}
            ], "default": "standard", "group": "Quantization", "visible_when": {"demo_mode": "quantization"}},
            {"type": "slider", "name": "bit_depth", "label": "Bit Depth", "min": 1, "max": 16, "step": 1, "default": 4, "unit": "bits", "group": "Quantization", "visible_when": {"demo_mode": "quantization"}},
            # Image Demo Controls
            {"type": "slider", "name": "image_bits", "label": "Image Bit Depth", "min": 1, "max": 8, "step": 1, "default": 3, "unit": "bits", "group": "Image", "visible_when": {"demo_mode": "image"}},
        ],
        "default_params": {
            "demo_mode": "aliasing",
            "downsample_factor": 4,
            "anti_aliasing": False,
            "bit_depth": 4,
            "quant_method": "standard",
            "image_bits": 3
        },
        "plots": [
            {"id": "original_signal", "title": "Original Signal", "description": "Original audio signal"},
            {"id": "downsampled_signal", "title": "Downsampled", "description": "Downsampled signal"},
            {"id": "frequency_spectrum", "title": "Spectrum", "description": "Frequency spectrum with Nyquist markers"},
        ],
    },

    # =========================================================================
    # 3. AMPLIFIER TOPOLOGIES (Matching PyQt5 exactly)
    # =========================================================================
    {
        "id": "amplifier_topologies",
        "name": "Amplifier Topologies",
        "description": "Explore various amplifier configurations including simple, feedback, push-pull (crossover distortion), and compensated designs. Visualize gain curves, transfer characteristics, and input/output signals in real-time.",
        "category": "Circuits",
        "thumbnail": "🔊",
        "tags": ["amplifier", "gain", "feedback", "crossover distortion", "push-pull"],
        "has_simulator": True,
        "controls": [
            # Amplifier Configuration (matching PyQt5 radio buttons)
            {"type": "select", "name": "amplifier_type", "label": "Amplifier Configuration", "options": [
                {"value": "simple", "label": "1. Simple Amplifier"},
                {"value": "feedback", "label": "2. Feedback System"},
                {"value": "crossover", "label": "3. Crossover Distortion"},
                {"value": "compensated", "label": "4. Compensated System"}
            ], "default": "simple", "group": "Mode"},
            # Parameters (matching PyQt5 sliders exactly)
            {"type": "slider", "name": "F0", "label": "F₀ - Power Amp Gain", "min": 8, "max": 12, "step": 0.01, "default": 10.0, "unit": "", "group": "Amplifier"},
            {"type": "slider", "name": "K", "label": "K - Forward Gain", "min": 1, "max": 200, "step": 1, "default": 100, "unit": "", "group": "Amplifier"},
            {"type": "slider", "name": "beta", "label": "β - Feedback Factor", "min": 0.01, "max": 1.0, "step": 0.01, "default": 0.1, "unit": "", "group": "Feedback"},
            # Input source selection
            {"type": "select", "name": "input_source", "label": "Input Source", "options": [
                {"value": "pure_sine", "label": "Pure Sine Wave"},
                {"value": "rich_sine", "label": "Rich Sine (Harmonics)"}
            ], "default": "pure_sine", "group": "Input"},
        ],
        "default_params": {"K": 100, "F0": 10.0, "beta": 0.1, "amplifier_type": "simple", "input_source": "pure_sine"},
        "plots": [
            {"id": "input_signal", "title": "Input Signal (Time Domain)", "description": "Input waveform"},
            {"id": "output_signal", "title": "Output Signal (Time Domain)", "description": "Amplified output with dynamic scaling"},
            {"id": "gain_curve", "title": "Gain vs. F₀ Variation", "description": "Simple vs feedback gain curves with ideal (1/β)"},
            {"id": "xy_linearity", "title": "Output vs. Input (Linearity)", "description": "Transfer characteristic showing linearity/distortion"},
        ],
        # Circuit diagram display
        "displays": [
            {"id": "circuit_diagram", "type": "image", "description": "Circuit diagram for current mode"},
            {"id": "gain_info", "type": "info", "description": "Effective gain and formula"},
        ],
    },

    # =========================================================================
    # 4. CONVOLUTION SIMULATOR (Custom Viewer - matching PyQt5)
    # =========================================================================
    {
        "id": "convolution_simulator",
        "name": "Convolution Simulator",
        "description": "Visualize continuous and discrete convolution operations step-by-step. Understand how signals combine through convolution with interactive animations.",
        "category": "Signal Processing",
        "thumbnail": "🔄",
        "tags": ["convolution", "LTI", "impulse response", "signals"],
        "has_simulator": True,
        "sticky_controls": True,
        "controls": [
            # Signal type (Continuous/Discrete)
            {"type": "select", "name": "mode", "label": "Signal Type", "options": [
                {"value": "continuous", "label": "Continuous"},
                {"value": "discrete", "label": "Discrete"}
            ], "default": "continuous", "group": "Mode"},
            # Input source (Preset/Custom)
            {"type": "select", "name": "input_mode", "label": "Input Source", "options": [
                {"value": "preset", "label": "Demo Presets"},
                {"value": "custom", "label": "Custom Expressions"}
            ], "default": "preset", "group": "Mode"},
            # Continuous demo preset selector
            {"type": "select", "name": "demo_preset_ct", "label": "Demo Preset", "options": [
                {"value": "rect_tri", "label": "Rect + Triangle"},
                {"value": "step_exp", "label": "Step + Exponential"},
                {"value": "rect_rect", "label": "Rect + Rect"},
                {"value": "exp_exp", "label": "Exp + Exp"},
                {"value": "sinc_rect", "label": "Sinc + Rect"}
            ], "default": "rect_tri", "group": "Signals", "visible_when": {"input_mode": "preset", "mode": "continuous"}},
            # Discrete demo preset selector
            {"type": "select", "name": "demo_preset_dt", "label": "Demo Preset", "options": [
                {"value": "simple_seq", "label": "[1,2,1] * [1,1]"},
                {"value": "exp_diff", "label": "Exp + Differentiator"},
                {"value": "moving_avg", "label": "Moving Average"},
                {"value": "impulse_response", "label": "Impulse Response"},
                {"value": "echo", "label": "Echo Effect"}
            ], "default": "simple_seq", "group": "Signals", "visible_when": {"input_mode": "preset", "mode": "discrete"}},
            # Custom expressions - continuous mode
            {"type": "expression", "name": "custom_x", "label": "x(t)", "default": "rect(t)", "group": "Signals", "visible_when": {"input_mode": "custom", "mode": "continuous"}},
            {"type": "expression", "name": "custom_h", "label": "h(t)", "default": "exp(-t) * u(t)", "group": "Signals", "visible_when": {"input_mode": "custom", "mode": "continuous"}},
            # Custom expressions - discrete mode
            {"type": "expression", "name": "custom_x", "label": "x[n]", "default": "[1, 2, 1]", "group": "Signals", "visible_when": {"input_mode": "custom", "mode": "discrete"}},
            {"type": "expression", "name": "custom_h", "label": "h[n]", "default": "[1, 1]", "group": "Signals", "visible_when": {"input_mode": "custom", "mode": "discrete"}},
            # Playback controls
            {"type": "button", "name": "play_pause", "label": "Play", "group": "Playback"},
            {"type": "button", "name": "step_backward", "label": "Step Back", "group": "Playback"},
            {"type": "button", "name": "step_forward", "label": "Step Forward", "group": "Playback"},
            {"type": "button", "name": "reset", "label": "Reset", "group": "Playback"},
            {"type": "slider", "name": "time_shift", "label": "Time Position (t₀)", "min": -8, "max": 12, "step": 0.1, "default": 0, "unit": "", "group": "Playback"},
            {"type": "slider", "name": "animation_speed", "label": "Animation Speed", "min": 0.1, "max": 4.0, "step": 0.1, "default": 0.5, "unit": "x", "group": "Playback"},
        ],
        "default_params": {
            "time_shift": 0,
            "mode": "continuous",
            "running": False,
            "input_mode": "preset",
            "demo_preset_ct": "rect_tri",
            "demo_preset_dt": "simple_seq",
            "custom_x": "rect(t)",
            "custom_h": "exp(-t) * u(t)",
            "animation_speed": 0.5
        },
        "plots": [
            {"id": "signal_x", "title": "Signal x(τ)", "description": "First input signal"},
            {"id": "signal_h", "title": "Signal h(t₀-τ)", "description": "Flipped and shifted impulse response"},
            {"id": "product", "title": "Product x(τ)h(t₀-τ)", "description": "Overlapping product (area = y(t₀))"},
            {"id": "result", "title": "Convolution Result y(t)", "description": "(x * h)(t)"},
        ],
    },

    # =========================================================================
    # 5. CT/DT POLES CONVERSION (Matching PyQt5 exactly)
    # =========================================================================
    {
        "id": "ct_dt_poles",
        "name": "CT/DT Poles Conversion",
        "description": "Interactive learning tool for understanding CT to DT system transformations using Forward Euler, Backward Euler, and Trapezoidal methods. Features S-plane and Z-plane visualization, step response comparison, stability analysis, and educational theory panels.",
        "category": "Transforms",
        "thumbnail": "🎯",
        "tags": ["poles", "zeros", "s-plane", "z-plane", "stability", "numerical integration", "euler", "bilinear", "sampling"],
        "has_simulator": True,
        "controls": [
            # T/τ Ratio slider (matching PyQt5: 0.01 to 3.0, default 0.50)
            {"type": "slider", "name": "t_tau_ratio", "label": "T/τ Ratio", "min": 0.01, "max": 3.0, "step": 0.01, "default": 0.50, "unit": "", "group": "System", "description": "Sampling period relative to time constant"},
            # Method selection (matching PyQt5: Forward Euler default)
            {"type": "select", "name": "method", "label": "Transformation Method", "options": [
                {"value": "forward_euler", "label": "Forward Euler"},
                {"value": "backward_euler", "label": "Backward Euler"},
                {"value": "trapezoidal", "label": "Trapezoidal (Bilinear)"}
            ], "default": "forward_euler", "group": "Method", "description": "Numerical integration method for CT to DT conversion"},
            # Guided scenarios (matching PyQt5 guided mode)
            {"type": "select", "name": "guided_scenario", "label": "Guided Scenario", "options": [
                {"value": "none", "label": "Free Exploration"},
                {"value": "0", "label": "1: Small Step (Stable)"},
                {"value": "1", "label": "2: Moderate Step"},
                {"value": "2", "label": "3: Near Limit"},
                {"value": "3", "label": "4: FE Unstable"},
                {"value": "4", "label": "5: BE Stable"},
                {"value": "5", "label": "6: Trapezoidal"}
            ], "default": "none", "group": "Learning", "description": "Select a guided learning scenario"},
        ],
        "default_params": {"t_tau_ratio": 0.50, "method": "forward_euler", "guided_scenario": "none"},
        "plots": [
            # Main Tab plots
            {"id": "s_plane", "title": "S-Domain Analysis", "description": "Continuous-time pole location with stability regions"},
            {"id": "z_plane", "title": "Z-Domain Analysis", "description": "Discrete-time pole with unit circle and stability status"},
            {"id": "step_response", "title": "Step Response", "description": "CT vs DT step response with RMS error quality indicator"},
            # Stability Tab plots
            {"id": "stability_map", "title": "Stability Analysis", "description": "Pole magnitude vs T/τ ratio with stability regions"},
            {"id": "pole_trajectory", "title": "Pole Movement", "description": "How poles travel in Z-plane as parameters change"},
            # Theory Tab
            {"id": "theory_panel", "title": "Theory & Learning", "description": "Method explanations and educational content"},
        ],
    },

    # =========================================================================
    # 6. DC MOTOR FEEDBACK CONTROL (Matching PyQt5 exactly)
    # =========================================================================
    {
        "id": "dc_motor",
        "name": "DC Motor Feedback Control",
        "description": "Interactive simulation demonstrating feedback control principles for DC motors. Explore how amplifier gain, feedback, and motor parameters affect system behavior through pole-zero maps and step response analysis.",
        "category": "Control Systems",
        "thumbnail": "⚙️",
        "tags": ["motor", "feedback", "control", "poles", "transfer function", "stability"],
        "has_simulator": True,
        "controls": [
            # Model selection (matching PyQt5 radio buttons)
            {"type": "select", "name": "model_type", "label": "Model Selection", "options": [
                {"value": "first_order", "label": "First-Order"},
                {"value": "second_order", "label": "Second-Order"}
            ], "default": "first_order", "group": "Model"},
            # Parameters (ranges fixed to include PyQt5 defaults)
            {"type": "slider", "name": "alpha", "label": "α (Amplifier gain)", "min": 0.1, "max": 50.0, "step": 0.1, "default": 10.0, "unit": "", "group": "Parameters"},
            {"type": "slider", "name": "beta", "label": "β (Feedback gain)", "min": 0.01, "max": 1.0, "step": 0.01, "default": 0.5, "unit": "", "group": "Parameters"},
            {"type": "slider", "name": "gamma", "label": "γ (Motor constant)", "min": 0.1, "max": 5.0, "step": 0.1, "default": 1.0, "unit": "", "group": "Parameters"},
            {"type": "slider", "name": "p", "label": "p (Lag pole)", "min": 1.0, "max": 30.0, "step": 0.1, "default": 10.0, "unit": "", "group": "Parameters", "visible_when": {"model_type": "second_order"}},
        ],
        "default_params": {"model_type": "first_order", "alpha": 10.0, "beta": 0.5, "gamma": 1.0, "p": 10.0},
        "plots": [
            {"id": "pole_zero_map", "title": "Pole-Zero Map (s-plane)", "description": "System poles with stability region"},
            {"id": "step_response", "title": "Step Response", "description": "System transient response with final value"},
        ],
        # Additional display elements
        "displays": [
            {"id": "block_diagram", "type": "image", "description": "Feedback control block diagram"},
            {"id": "transfer_function", "type": "equation", "description": "System transfer function"},
            {"id": "poles_info", "type": "info", "description": "Pole locations and stability info"},
            {"id": "steady_state", "type": "value", "description": "Steady-state value (1/β)"},
        ],
    },

    # =========================================================================
    # 7. FEEDBACK SYSTEM ANALYSIS (Matching PyQt5 exactly)
    # =========================================================================
    {
        "id": "feedback_system_analysis",
        "name": "Feedback System Analysis",
        "description": "Interactive visualization of negative feedback effects on amplifier performance. Compare open-loop vs closed-loop behavior including gain, bandwidth, rise time, and pole locations. Features step response, Bode plots, and S-plane pole visualization.",
        "category": "Circuits",
        "thumbnail": "🔁",
        "tags": ["feedback", "stability", "gain", "bandwidth", "bode", "amplifier", "poles"],
        "has_simulator": True,
        "controls": [
            # β (Feedback Factor) - PyQt5: 0 to 0.01, step 0.0001, default 0.0041
            {"type": "slider", "name": "beta", "label": "β (Feedback Factor)", "min": 0.0, "max": 0.01, "step": 0.0001, "default": 0.0041, "unit": "", "group": "Feedback", "description": "Feedback strength - affects gain reduction and bandwidth expansion"},
            # K₀ (Open-Loop Gain) - PyQt5: 10,000 to 500,000, step 1000, default 200,000
            {"type": "slider", "name": "K0", "label": "K₀ (Open-Loop Gain)", "min": 10000, "max": 500000, "step": 1000, "default": 200000, "unit": "V/V", "group": "Amplifier", "description": "Amplifier open-loop gain"},
            # α (Pole Location) - PyQt5: 10 to 200, step 1, default 40
            {"type": "slider", "name": "alpha", "label": "α (Pole Location)", "min": 10, "max": 200, "step": 1, "default": 40, "unit": "rad/s", "group": "Amplifier", "description": "Open-loop pole location - affects bandwidth"},
            # Input Amplitude - PyQt5: 0.1 to 2.0, step 0.01, default 1.0
            {"type": "slider", "name": "input_amp", "label": "Input Amplitude", "min": 0.1, "max": 2.0, "step": 0.01, "default": 1.0, "unit": "V", "group": "Input", "description": "Input signal amplitude for step response"},
        ],
        "default_params": {"beta": 0.0041, "K0": 200000, "alpha": 40, "input_amp": 1.0},
        "plots": [
            {"id": "step_response", "title": "Step Response", "description": "Open-loop vs closed-loop step response with speedup indicator"},
            {"id": "bode_magnitude", "title": "Bode Magnitude", "description": "Frequency response magnitude with bandwidth markers"},
            {"id": "bode_phase", "title": "Bode Phase", "description": "Frequency response phase comparison"},
            {"id": "s_plane", "title": "S-Plane Poles", "description": "Pole locations showing feedback effect on stability"},
        ],
    },

    # =========================================================================
    # 8. FOURIER ANALYSIS: PHASE VS MAGNITUDE (Matching PyQt5 exactly)
    # =========================================================================
    {
        "id": "fourier_phase_vs_magnitude",
        "name": "Fourier Analysis: Phase Vs Magnitude",
        "description": "Interactive demonstration that phase carries more structural information than magnitude. Compare images/audio signals and their hybrids to see how phase dominates perception. Supports both 2D image analysis and 1D audio analysis.",
        "category": "Transforms",
        "thumbnail": "📈",
        "tags": ["FFT", "spectrum", "frequency", "magnitude", "phase", "image", "audio", "hybrid", "SSIM"],
        "has_simulator": True,
        "controls": [
            # Analysis Mode (Image vs Audio)
            {"type": "select", "name": "analysis_mode", "label": "Analysis Mode", "options": [
                {"value": "image", "label": "Image Analysis"},
                {"value": "audio", "label": "Audio Analysis"}
            ], "default": "image", "group": "Mode", "description": "Switch between 2D image and 1D audio Fourier analysis"},
            # Image Source Selection
            {"type": "select", "name": "image1_pattern", "label": "Image 1 Pattern", "options": [
                {"value": "building", "label": "Building"},
                {"value": "face", "label": "Face"},
                {"value": "geometric", "label": "Geometric"},
                {"value": "texture", "label": "Texture"}
            ], "default": "building", "group": "Image Source", "visible_when": {"analysis_mode": "image"}},
            {"type": "select", "name": "image2_pattern", "label": "Image 2 Pattern", "options": [
                {"value": "building", "label": "Building"},
                {"value": "face", "label": "Face"},
                {"value": "geometric", "label": "Geometric"},
                {"value": "texture", "label": "Texture"}
            ], "default": "face", "group": "Image Source", "visible_when": {"analysis_mode": "image"}},
            # Image Mode Selection
            {"type": "select", "name": "image1_mode", "label": "Image 1 Mode", "options": [
                {"value": "original", "label": "Original"},
                {"value": "uniform_magnitude", "label": "Uniform Magnitude"},
                {"value": "uniform_phase", "label": "Uniform Phase"}
            ], "default": "original", "group": "Fourier Mode", "visible_when": {"analysis_mode": "image"}},
            {"type": "select", "name": "image2_mode", "label": "Image 2 Mode", "options": [
                {"value": "original", "label": "Original"},
                {"value": "uniform_magnitude", "label": "Uniform Magnitude"},
                {"value": "uniform_phase", "label": "Uniform Phase"}
            ], "default": "original", "group": "Fourier Mode", "visible_when": {"analysis_mode": "image"}},
            # Audio Source Selection
            {"type": "select", "name": "audio1_type", "label": "Audio 1 Signal", "options": [
                {"value": "sine", "label": "Sine (440 Hz)"},
                {"value": "square", "label": "Square (220 Hz)"},
                {"value": "sawtooth", "label": "Sawtooth (180 Hz)"},
                {"value": "beat", "label": "Beat (AM)"}
            ], "default": "sine", "group": "Audio Source", "visible_when": {"analysis_mode": "audio"}},
            {"type": "select", "name": "audio2_type", "label": "Audio 2 Signal", "options": [
                {"value": "sine", "label": "Sine (440 Hz)"},
                {"value": "square", "label": "Square (220 Hz)"},
                {"value": "sawtooth", "label": "Sawtooth (180 Hz)"},
                {"value": "beat", "label": "Beat (AM)"}
            ], "default": "square", "group": "Audio Source", "visible_when": {"analysis_mode": "audio"}},
            # Uniform Value Sliders (matching PyQt5 exactly)
            {"type": "slider", "name": "uniform_magnitude", "label": "Uniform Magnitude", "min": 0.1, "max": 100.0, "step": 0.1, "default": 10.0, "unit": "", "group": "Uniform Values", "description": "Value for uniform magnitude replacement"},
            {"type": "slider", "name": "uniform_phase", "label": "Uniform Phase", "min": -3.14, "max": 3.14, "step": 0.01, "default": 0.0, "unit": "rad", "group": "Uniform Values", "description": "Value for uniform phase replacement (-π to π)"},
        ],
        "default_params": {
            "analysis_mode": "image",
            "image1_pattern": "building",
            "image2_pattern": "face",
            "image1_mode": "original",
            "image2_mode": "original",
            "audio1_type": "sine",
            "audio2_type": "square",
            "uniform_magnitude": 10.0,
            "uniform_phase": 0.0
        },
        "plots": [
            # Image mode plots
            {"id": "image1_original", "title": "Image 1 Original", "description": "Original test image 1"},
            {"id": "image1_magnitude", "title": "Image 1 Magnitude", "description": "Log magnitude spectrum"},
            {"id": "image1_phase", "title": "Image 1 Phase", "description": "Phase spectrum (-π to π)"},
            {"id": "image1_reconstructed", "title": "Image 1 Reconstructed", "description": "IFFT reconstruction"},
            {"id": "image2_original", "title": "Image 2 Original", "description": "Original test image 2"},
            {"id": "image2_magnitude", "title": "Image 2 Magnitude", "description": "Log magnitude spectrum"},
            {"id": "image2_phase", "title": "Image 2 Phase", "description": "Phase spectrum (-π to π)"},
            {"id": "image2_reconstructed", "title": "Image 2 Reconstructed", "description": "IFFT reconstruction"},
            {"id": "hybrid_mag1_phase2", "title": "Hybrid: Mag1 + Phase2", "description": "Looks like Image 2 (phase dominates!)"},
            {"id": "hybrid_mag2_phase1", "title": "Hybrid: Mag2 + Phase1", "description": "Looks like Image 1 (phase dominates!)"},
            # Audio mode plots
            {"id": "audio1_waveform", "title": "Audio 1 Waveform", "description": "Time domain signal 1"},
            {"id": "audio1_magnitude", "title": "Audio 1 Magnitude", "description": "Magnitude spectrum (dB)"},
            {"id": "audio1_phase", "title": "Audio 1 Phase", "description": "Phase spectrum"},
            {"id": "audio2_waveform", "title": "Audio 2 Waveform", "description": "Time domain signal 2"},
            {"id": "audio2_magnitude", "title": "Audio 2 Magnitude", "description": "Magnitude spectrum (dB)"},
            {"id": "audio2_phase", "title": "Audio 2 Phase", "description": "Phase spectrum"},
            {"id": "hybrid1_waveform", "title": "Hybrid: Mag1 + Phase2", "description": "Phase from signal 2"},
            {"id": "hybrid2_waveform", "title": "Hybrid: Mag2 + Phase1", "description": "Phase from signal 1"},
        ],
    },

    # =========================================================================
    # 9. FOURIER SERIES
    # =========================================================================
    {
        "id": "fourier_series",
        "name": "Fourier Series",
        "description": "Decompose periodic waveforms into harmonic components. Build signals from sine and cosine terms and visualize convergence with increasing harmonics.",
        "category": "Transforms",
        "thumbnail": "〰️",
        "tags": ["harmonics", "periodic", "synthesis", "waveforms"],
        "has_simulator": True,
        "controls": [
            {"type": "select", "name": "waveform", "label": "Waveform Type", "options": [{"value": "square", "label": "Square Wave"}, {"value": "triangle", "label": "Triangle Wave"}], "default": "square", "group": "Waveform"},
            {"type": "slider", "name": "harmonics", "label": "Number of Harmonics", "min": 1, "max": 50, "step": 1, "default": 10, "unit": "", "group": "Waveform"},
            {"type": "slider", "name": "frequency", "label": "Fundamental Frequency", "min": 0.5, "max": 5, "step": 0.5, "default": 1.0, "unit": "Hz", "group": "Waveform"},
        ],
        "default_params": {"waveform": "square", "harmonics": 10, "frequency": 1.0},
        "plots": [
            {"id": "approximation", "title": "Fourier Approximation", "description": "Original waveform vs Fourier series approximation"},
            {"id": "components", "title": "Harmonic Components", "description": "Individual harmonic terms"},
            {"id": "spectrum", "title": "Coefficient Spectrum", "description": "Magnitude of Fourier coefficients"},
        ],
    },

    # =========================================================================
    # 10. FURUTA PENDULUM (Matching PyQt5 exactly)
    # =========================================================================
    {
        "id": "furuta_pendulum",
        "name": "Furuta Pendulum",
        "description": "Interactive simulation of a rotary inverted pendulum (Furuta Pendulum) with PID control. Features real-time 3D visualization, angle tracking, control torque plots, and stability analysis. Control the pendulum to stay upright using a motor at the arm pivot.",
        "category": "Control Systems",
        "thumbnail": "🎢",
        "tags": ["inverted pendulum", "balance", "nonlinear", "control", "PID", "3D visualization", "stability"],
        "has_simulator": True,
        "controls": [
            # Physical Parameters (tuned for stable control)
            {"type": "slider", "name": "mass", "label": "Pendulum Mass", "min": 0.05, "max": 0.3, "step": 0.01, "default": 0.1, "unit": "kg", "group": "Physical", "description": "Mass at end of pendulum"},
            {"type": "slider", "name": "pendulum_length", "label": "Pendulum Length", "min": 0.1, "max": 0.5, "step": 0.01, "default": 0.3, "unit": "m", "group": "Physical", "description": "Length of pendulum rod"},
            {"type": "slider", "name": "arm_length", "label": "Arm Length", "min": 0.1, "max": 0.4, "step": 0.01, "default": 0.2, "unit": "m", "group": "Physical", "description": "Length of rotating horizontal arm"},
            # PID Controller
            {"type": "slider", "name": "Kp", "label": "Kp (Proportional)", "min": 0, "max": 150, "step": 1, "default": 1, "unit": "", "group": "PID Controller", "description": "Proportional gain - main restoring force"},
            {"type": "slider", "name": "Kd", "label": "Kd (Derivative)", "min": 0, "max": 30, "step": 0.5, "default": 0, "unit": "", "group": "PID Controller", "description": "Derivative gain - damping"},
            {"type": "slider", "name": "Ki", "label": "Ki (Integral)", "min": 0, "max": 10, "step": 0.5, "default": 0.5, "unit": "", "group": "PID Controller", "description": "Integral gain - eliminates steady-state error"},
            # Initial Conditions
            {"type": "slider", "name": "initial_angle", "label": "Initial Angle", "min": -30, "max": 30, "step": 1, "default": 15, "unit": "deg", "group": "Initial Conditions", "description": "Starting pendulum angle from vertical"},
        ],
        "default_params": {"mass": 0.1, "pendulum_length": 0.3, "arm_length": 0.2, "Kp": 1, "Kd": 0, "Ki": 0.5, "initial_angle": 15},
        "plots": [
            {"id": "pendulum_angle", "title": "Pendulum Angle", "description": "θ vs time with stability bands"},
            {"id": "control_torque", "title": "Control Torque", "description": "τ vs time (motor command)"},
            {"id": "arm_position", "title": "Arm Rotation", "description": "φ vs time (arm angle)"},
        ],
        # 3D visualization metadata
        "has_3d_visualization": True,
        "visualization_type": "furuta_pendulum_3d",
    },

    # =========================================================================
    # 11. LENS OPTICS (Matching PyQt5 exactly)
    # =========================================================================
    {
        "id": "lens_optics",
        "name": "Lens Optics",
        "description": "Model optical systems using convolution. Simulate lens blur with diffraction-limited Airy disk PSF, aperture effects, atmospheric seeing, and analyze image quality. Features PSF cross-sections, encircled energy plots, and MTF curves.",
        "category": "Optics",
        "thumbnail": "🔍",
        "tags": ["PSF", "blur", "aperture", "imaging", "Airy disk", "diffraction", "MTF", "seeing"],
        "has_simulator": True,
        "controls": [
            # Test Pattern (first - most important selection)
            {"type": "select", "name": "test_pattern", "label": "Test Pattern", "options": [
                {"value": "edge_target", "label": "Edge Target"},
                {"value": "resolution_chart", "label": "Resolution Chart"},
                {"value": "point_sources", "label": "Point Sources"},
                {"value": "star_field", "label": "Star Field"}
            ], "default": "edge_target", "group": "Input", "description": "Test image for PSF evaluation"},
            # Lens Parameters (matching PyQt5 exactly)
            {"type": "slider", "name": "diameter", "label": "Aperture Diameter", "min": 50, "max": 200, "step": 1, "default": 100, "unit": "mm", "group": "Lens", "description": "Lens aperture diameter"},
            {"type": "slider", "name": "focal_length", "label": "Focal Length", "min": 200, "max": 1000, "step": 10, "default": 500, "unit": "mm", "group": "Lens", "description": "Lens focal length"},
            {"type": "slider", "name": "wavelength", "label": "Wavelength", "min": 400, "max": 700, "step": 10, "default": 550, "unit": "nm", "group": "Lens", "description": "Light wavelength (550nm = green)"},
            {"type": "slider", "name": "pixel_size", "label": "Pixel Size", "min": 0.5, "max": 10.0, "step": 0.1, "default": 1.0, "unit": "μm", "group": "Sensor", "description": "Sensor pixel size"},
            # Atmosphere
            {"type": "checkbox", "name": "enable_atmosphere", "label": "Enable Atmospheric Seeing", "default": False, "group": "Atmosphere"},
            {"type": "slider", "name": "atmospheric_seeing", "label": "Seeing (FWHM)", "min": 0.5, "max": 5.0, "step": 0.1, "default": 1.5, "unit": "arcsec", "group": "Atmosphere", "description": "Atmospheric seeing FWHM", "visible_when": {"enable_atmosphere": True}},
        ],
        "default_params": {
            "diameter": 100,
            "focal_length": 500,
            "wavelength": 550,
            "pixel_size": 1.0,
            "enable_atmosphere": False,
            "atmospheric_seeing": 1.5,
            "test_pattern": "edge_target"
        },
        "plots": [
            {"id": "original_image", "title": "Original Image", "description": "Test pattern input"},
            {"id": "blurred_image", "title": "Blurred Image", "description": "PSF-convolved output"},
            {"id": "psf", "title": "Point Spread Function", "description": "Airy disk PSF (log scale)"},
            {"id": "cross_section", "title": "PSF Cross-Section", "description": "Horizontal and vertical profiles"},
            {"id": "encircled_energy", "title": "Encircled Energy", "description": "Energy vs radius with EE50/EE80"},
            {"id": "mtf", "title": "Modulation Transfer Function", "description": "MTF curve with 50% cutoff"},
        ],
        # Display metadata for custom viewer
        "displays": [
            {"id": "lens_info", "type": "info", "description": "Lens parameters and f-number"},
            {"id": "psf_metrics", "type": "metrics", "description": "PSF quality metrics"},
            {"id": "quality_metrics", "type": "metrics", "description": "Image quality metrics"},
        ],
    },

    # =========================================================================
    # 12. MODULATION TECHNIQUES (Matches PyQt5 version with tabs)
    # =========================================================================
    {
        "id": "modulation_techniques",
        "name": "Modulation Techniques",
        "description": "Explore AM, FM/PM, and FDM modulation with real audio. Switch between Amplitude Modulation, Frequency/Phase Modulation, and Frequency Division Multiplexing demos.",
        "category": "Signal Processing",
        "thumbnail": "📡",
        "tags": ["AM", "FM", "PM", "FDM", "modulation", "carrier", "radio", "audio"],
        "has_simulator": True,
        "controls": [
            # Demo mode is controlled by tabs in ModulationViewer, hidden from controls panel
            {"type": "select", "name": "demo_mode", "label": "Demo Mode", "options": [
                {"value": "am", "label": "Amplitude Modulation"},
                {"value": "fm_pm", "label": "Frequency & Phase Modulation"},
                {"value": "fdm", "label": "Frequency Division Multiplexing"}
            ], "default": "am", "hidden": True},
            # AM Controls - mode selector first, then other params
            {"type": "select", "name": "am_mode", "label": "Mode", "options": [
                {"value": "dsb_sc", "label": "DSB-SC"},
                {"value": "am_carrier", "label": "AM+Carrier"},
                {"value": "envelope", "label": "Envelope Detection"}
            ], "default": "dsb_sc", "group": "AM Controls", "visible_when": {"demo_mode": "am"}},
            {"type": "slider", "name": "am_carrier_freq", "label": "Carrier Frequency", "min": 1, "max": 20, "step": 1, "default": 5, "unit": "kHz", "group": "AM Controls", "visible_when": {"demo_mode": "am"}},
            {"type": "slider", "name": "am_carrier_dc", "label": "Carrier DC Offset", "min": 0.0, "max": 2.0, "step": 0.1, "default": 1.2, "unit": "", "group": "AM Controls", "visible_when": {"demo_mode": "am"}},
            # FM/PM Controls - mode selector first, then other params
            {"type": "select", "name": "fm_pm_mode", "label": "Mode", "options": [
                {"value": "fm", "label": "FM (Frequency)"},
                {"value": "pm", "label": "PM (Phase)"}
            ], "default": "fm", "group": "FM/PM Controls", "visible_when": {"demo_mode": "fm_pm"}},
            {"type": "slider", "name": "fm_carrier_freq", "label": "Carrier Frequency", "min": 5, "max": 25, "step": 1, "default": 10, "unit": "kHz", "group": "FM/PM Controls", "visible_when": {"demo_mode": "fm_pm"}},
            {"type": "slider", "name": "fm_deviation", "label": "Frequency Deviation (FM)", "min": 50, "max": 5000, "step": 50, "default": 1200, "unit": "Hz", "group": "FM/PM Controls", "visible_when": {"demo_mode": "fm_pm"}},
            {"type": "slider", "name": "pm_sensitivity", "label": "Phase Sensitivity (PM)", "min": 0.2, "max": 10.0, "step": 0.1, "default": 1.2, "unit": "rad", "group": "FM/PM Controls", "visible_when": {"demo_mode": "fm_pm"}},
            # FDM Controls
            {"type": "slider", "name": "fdm_channels", "label": "Number of Channels", "min": 1, "max": 5, "step": 1, "default": 3, "unit": "", "group": "FDM Controls", "visible_when": {"demo_mode": "fdm"}},
            {"type": "slider", "name": "fdm_demod_channel", "label": "Demodulate Channel", "min": 1, "max": 5, "step": 1, "default": 1, "unit": "", "group": "FDM Controls", "visible_when": {"demo_mode": "fdm"}},
            {"type": "slider", "name": "fdm_spacing", "label": "Channel Spacing", "min": 5, "max": 30, "step": 1, "default": 10, "unit": "kHz", "group": "FDM Controls", "visible_when": {"demo_mode": "fdm"}},
        ],
        "default_params": {
            "demo_mode": "am",
            "am_carrier_freq": 5, "am_carrier_dc": 1.2, "am_mode": "dsb_sc",
            "fm_carrier_freq": 10, "fm_deviation": 1200, "pm_sensitivity": 1.2, "fm_pm_mode": "fm",
            "fdm_channels": 3, "fdm_demod_channel": 1, "fdm_spacing": 10
        },
        "plots": [
            {"id": "waveforms", "title": "Waveforms", "description": "Time-domain signal visualization"},
            {"id": "spectrum", "title": "Spectrum", "description": "Power spectral density"},
        ],
    },

    # =========================================================================
    # 13. SECOND-ORDER SYSTEM RESPONSE
    # =========================================================================
    {
        "id": "second_order_system",
        "name": "Second-Order System Response",
        "description": "Explore second-order system dynamics including pole locations, frequency response, and damping behavior. Visualize how Q-factor affects resonance, bandwidth, and transient response.",
        "category": "Control Systems",
        "thumbnail": "📉",
        "tags": ["second-order", "Q-factor", "damping", "resonance", "poles", "bode plot", "frequency response"],
        "has_simulator": True,
        "controls": [
            {"type": "slider", "name": "omega_0", "label": "Natural Frequency ω₀", "min": 1.0, "max": 100.0, "step": 0.5, "default": 10.0, "unit": "rad/s", "group": "System"},
            {"type": "slider", "name": "Q_slider", "label": "Quality Factor Q", "min": 0, "max": 100, "step": 1, "default": 50, "unit": "", "group": "System", "display_transform": "q_log"},
        ],
        "default_params": {"omega_0": 10.0, "Q_slider": 50},
        "plots": [
            {"id": "pole_zero", "title": "Pole-Zero Plot", "description": "S-plane with system poles"},
            {"id": "bode_magnitude", "title": "Bode Magnitude", "description": "|H(jω)| in dB"},
            {"id": "bode_phase", "title": "Bode Phase", "description": "∠H(jω) in degrees"},
        ],
    },
]


def get_all_simulations():
    """Return all simulations with category info."""
    result = []
    for sim in SIMULATION_CATALOG:
        sim_copy = sim.copy()
        sim_copy["category_info"] = CATEGORIES.get(sim["category"], {})
        result.append(sim_copy)
    return result


def get_simulation_by_id(sim_id: str):
    """Return a single simulation by ID."""
    for sim in SIMULATION_CATALOG:
        if sim["id"] == sim_id:
            sim_copy = sim.copy()
            sim_copy["category_info"] = CATEGORIES.get(sim["category"], {})
            return sim_copy
    return None


def get_categories():
    """Return all categories with their metadata."""
    return CATEGORIES


def get_simulations_by_category(category: str):
    """Return simulations filtered by category."""
    result = []
    for sim in SIMULATION_CATALOG:
        if sim["category"] == category:
            sim_copy = sim.copy()
            sim_copy["category_info"] = CATEGORIES.get(sim["category"], {})
            result.append(sim_copy)
    return result


def get_simulation_controls(sim_id: str):
    """Return controls for a specific simulation."""
    sim = get_simulation_by_id(sim_id)
    if sim:
        return sim.get("controls", [])
    return []


def get_simulation_defaults(sim_id: str):
    """Return default parameters for a specific simulation."""
    sim = get_simulation_by_id(sim_id)
    if sim:
        return sim.get("default_params", {})
    return {}
