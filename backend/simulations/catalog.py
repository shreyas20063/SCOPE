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

    # =========================================================================
    # 14. BLOCK DIAGRAM BUILDER
    # =========================================================================
    {
        "id": "block_diagram_builder",
        "name": "Block Diagram Builder",
        "description": "Build block diagrams by dragging and connecting Gain, Adder, Delay, and Integrator blocks. Switch between building diagrams to get transfer functions, or entering transfer functions to see their block diagram realization.",
        "category": "Control Systems",
        "thumbnail": "🔲",
        "tags": ["block diagram", "transfer function", "feedback", "operator", "simulink", "DT", "CT"],
        "has_simulator": True,
        "controls": [
            {"type": "select", "name": "system_type", "label": "System Type", "options": [
                {"label": "Discrete-Time (DT)", "value": "dt"},
                {"label": "Continuous-Time (CT)", "value": "ct"}
            ], "default": "dt", "group": "System"},
            {"type": "select", "name": "mode", "label": "Mode", "options": [
                {"label": "Build Diagram → TF", "value": "build"},
                {"label": "Enter TF → Diagram", "value": "parse"}
            ], "default": "build", "group": "System"},
        ],
        "default_params": {"system_type": "dt", "mode": "build"},
        "plots": [
            {"id": "response", "title": "System Response", "description": "Step/impulse response of the computed transfer function"},
        ],
    },

    # =========================================================================
    # 15. SIGNAL OPERATIONS PLAYGROUND
    # =========================================================================
    {
        "id": "signal_operations",
        "name": "Signal Operations Playground",
        "description": "Interactive canvas for exploring signal transformations: time-scaling, time-shifting, time-reversal, amplitude scaling, and DC offset. Apply chains of operations and see the original vs. transformed signal. Includes a quiz mode to test your understanding.",
        "category": "Signal Processing",
        "thumbnail": "🎛️",
        "tags": ["signal operations", "time scaling", "time shifting", "time reversal", "amplitude", "transformations", "quiz"],
        "has_simulator": True,
        "controls": [
            # Signal Selection
            {"type": "select", "name": "signal_type", "label": "Base Signal", "options": [
                {"value": "sine", "label": "Sine Wave"},
                {"value": "square", "label": "Square Wave"},
                {"value": "triangle", "label": "Triangle Wave"},
                {"value": "sawtooth", "label": "Sawtooth Wave"},
                {"value": "unit_step", "label": "Unit Step u(t)"},
                {"value": "impulse", "label": "Impulse δ(t)"},
            ], "default": "sine", "group": "Signal"},
            {"type": "slider", "name": "frequency", "label": "Frequency", "min": 0.5, "max": 10.0, "step": 0.1, "default": 1.0, "unit": "Hz", "group": "Signal", "visible_when": {"signal_type": ["sine", "square", "triangle", "sawtooth"]}},

            # Mode
            {"type": "select", "name": "mode", "label": "Mode", "options": [
                {"value": "explore", "label": "Explore"},
                {"value": "quiz", "label": "Quiz"},
            ], "default": "explore", "group": "Mode"},

            # Transformations (hidden in quiz mode)
            {"type": "slider", "name": "amplitude", "label": "Amplitude A", "min": -3.0, "max": 3.0, "step": 0.1, "default": 1.0, "group": "Transformations", "description": "A in A·f(t)", "visible_when": {"mode": "explore"}},
            {"type": "slider", "name": "time_scale", "label": "Time Scale a", "min": -3.0, "max": 3.0, "step": 0.1, "default": 1.0, "group": "Transformations", "description": "a in f(a·t)", "visible_when": {"mode": "explore"}},
            {"type": "slider", "name": "time_shift", "label": "Time Shift t₀", "min": -5.0, "max": 5.0, "step": 0.1, "default": 0.0, "unit": "s", "group": "Transformations", "description": "t₀ in f(t - t₀)", "visible_when": {"mode": "explore"}},
            {"type": "checkbox", "name": "time_reverse", "label": "Time Reverse f(−t)", "default": False, "group": "Transformations", "visible_when": {"mode": "explore"}},
            {"type": "slider", "name": "dc_offset", "label": "DC Offset", "min": -2.0, "max": 2.0, "step": 0.1, "default": 0.0, "group": "Transformations", "visible_when": {"mode": "explore"}},

            # Quiz Controls (visible only in quiz mode)
            {"type": "select", "name": "quiz_difficulty", "label": "Difficulty", "options": [
                {"value": "easy", "label": "Easy (1 op)"},
                {"value": "medium", "label": "Medium (2 ops)"},
                {"value": "hard", "label": "Hard (3 ops)"},
            ], "default": "easy", "group": "Quiz", "visible_when": {"mode": "quiz"}},
            {"type": "button", "name": "new_quiz", "label": "New Question", "group": "Quiz", "visible_when": {"mode": "quiz"}},
        ],
        "default_params": {
            "signal_type": "sine",
            "frequency": 1.0,
            "amplitude": 1.0,
            "time_scale": 1.0,
            "time_shift": 0.0,
            "time_reverse": False,
            "dc_offset": 0.0,
            "mode": "explore",
            "quiz_difficulty": "easy",
        },
        "plots": [
            {"id": "original", "title": "Original Signal f(t)", "description": "Base signal before any transformations"},
            {"id": "transformed", "title": "Transformed Signal", "description": "Signal after applying all operations, with original ghost overlay"},
            {"id": "quiz_challenge", "title": "Quiz Challenge", "description": "Mystery transformed signal — identify the operations applied"},
        ],
    },
    # =========================================================================
    # 18. FEEDBACK & CONVERGENCE EXPLORER
    # =========================================================================
    {
        "id": "feedback_convergence",
        "name": "Feedback & Convergence Explorer",
        "description": "Explore how a single feedback loop with gain p\u2080 creates geometric sequences. Watch the impulse response y[n] = p\u2080\u207f converge or diverge as you adjust the pole, and trace the signal path cycle by cycle through the feedback loop.",
        "category": "Signal Processing",
        "thumbnail": "\U0001f501",
        "tags": ["feedback", "convergence", "divergence", "geometric", "impulse response", "poles", "modes", "discrete-time"],
        "has_simulator": True,
        "controls": [
            {"type": "slider", "name": "p0", "label": "Feedback Gain p\u2080", "min": -2.0, "max": 2.0, "step": 0.01, "default": 0.5, "unit": "", "group": "Feedback Loop"},
            {"type": "slider", "name": "num_samples", "label": "Number of Samples", "min": 5, "max": 30, "step": 1, "default": 15, "unit": "", "group": "Display"},
            {"type": "checkbox", "name": "show_envelope", "label": "Show Envelope \u00b1|p\u2080|\u207f", "default": True, "group": "Display"},
            {"type": "checkbox", "name": "show_unit_circle", "label": "Show |p\u2080|=1 Boundary", "default": False, "group": "Display"},
            {"type": "button", "name": "animate_cycles", "label": "Animate Cycle", "group": "Animation"},
            {"type": "button", "name": "reset_animation", "label": "Reset Animation", "group": "Animation"},
        ],
        "default_params": {
            "p0": 0.5,
            "num_samples": 15,
            "show_envelope": True,
            "show_unit_circle": False,
        },
        "plots": [
            {"id": "impulse_response", "title": "Impulse Response", "description": "Stem plot of y[n] = p\u2080\u207f \u2014 green for converging, red for diverging"},
            {"id": "geometric_sum", "title": "Partial Sum", "description": "Cumulative sum S[n] = \u03a3 p\u2080\u1d4f showing geometric series convergence"},
        ],
    },

    # =========================================================================
    # 16. SAMPLING & RECONSTRUCTION EXPLORER
    # =========================================================================
    {
        "id": "sampling_reconstruction",
        "name": "Sampling & Reconstruction",
        "description": "Explore how sampling interval affects signal reconstruction fidelity. Compare zero-order hold, linear interpolation, and ideal sinc reconstruction methods side by side. Visualize the Nyquist criterion in action.",
        "category": "Signal Processing",
        "thumbnail": "\U0001f4f6",
        "tags": ["sampling", "reconstruction", "nyquist", "interpolation", "sinc", "zero-order hold", "DAC"],
        "has_simulator": True,
        "controls": [
            {"type": "select", "name": "signal_type", "label": "Signal Preset", "options": [
                {"value": "sine", "label": "Pure Sine"},
                {"value": "sum_of_sines", "label": "Sum of Sines (f\u2080 + f\u2080+4 Hz)"},
                {"value": "square", "label": "Square Wave"},
                {"value": "triangle", "label": "Triangle Wave"},
                {"value": "chirp", "label": "Chirp (Frequency Sweep)"},
                {"value": "custom_multitone", "label": "Multi-tone (1 + 4 + 9 Hz)"},
            ], "default": "sum_of_sines", "group": "Signal"},
            {"type": "slider", "name": "signal_frequency", "label": "Primary Frequency", "min": 0.5, "max": 20.0, "step": 0.1, "default": 3.0, "unit": "Hz", "group": "Signal"},
            {"type": "slider", "name": "sampling_frequency", "label": "Sampling Frequency (fs)", "min": 1.0, "max": 100.0, "step": 0.5, "default": 10.0, "unit": "Hz", "group": "Sampling"},
            {"type": "slider", "name": "time_window", "label": "Time Window", "min": 0.5, "max": 5.0, "step": 0.1, "default": 2.0, "unit": "s", "group": "Display"},
            {"type": "checkbox", "name": "show_zoh", "label": "Zero-Order Hold", "default": True, "group": "Reconstruction Methods"},
            {"type": "checkbox", "name": "show_linear", "label": "Linear Interpolation", "default": True, "group": "Reconstruction Methods"},
            {"type": "checkbox", "name": "show_sinc", "label": "Ideal Sinc", "default": True, "group": "Reconstruction Methods"},
            {"type": "checkbox", "name": "show_original", "label": "Show Original Signal", "default": True, "group": "Display"},
            {"type": "checkbox", "name": "show_error", "label": "Show Error Plot", "default": False, "group": "Display"},
        ],
        "default_params": {
            "signal_type": "sum_of_sines",
            "signal_frequency": 3.0,
            "sampling_frequency": 10.0,
            "time_window": 2.0,
            "show_zoh": True,
            "show_linear": True,
            "show_sinc": True,
            "show_original": True,
            "show_error": False,
        },
        "plots": [
            {"id": "sampling", "title": "Sampling", "description": "Continuous signal with discrete sample points (stem plot)"},
            {"id": "reconstruction", "title": "Reconstruction", "description": "Comparison of ZOH, linear, and sinc reconstruction methods"},
            {"id": "error", "title": "Reconstruction Error", "description": "Error between original and each reconstruction method"},
        ],
    },
    # =========================================================================
    # 17. MASS-SPRING SYSTEM VISUALIZER
    # =========================================================================
    {
        "id": "mass_spring_system",
        "name": "Mass-Spring System",
        "description": "Animated mass-spring-damper system showing how physical systems transform input signals. Watch the spring stretch and compress as base excitation x(t) becomes mass displacement y(t).",
        "category": "Control Systems",
        "thumbnail": "\U0001f529",
        "tags": ["mass-spring", "damper", "oscillation", "second-order", "resonance", "natural frequency", "damping ratio", "ODE"],
        "has_simulator": True,
        "controls": [
            {"type": "slider", "name": "mass", "label": "Mass (m)", "min": 0.1, "max": 5.0, "step": 0.1, "default": 1.0, "unit": "kg", "group": "System"},
            {"type": "slider", "name": "spring_constant", "label": "Spring Constant (k)", "min": 1, "max": 100, "step": 1, "default": 10, "unit": "N/m", "group": "System"},
            {"type": "slider", "name": "damping", "label": "Damping (b)", "min": 0, "max": 10, "step": 0.1, "default": 0.5, "unit": "Ns/m", "group": "System"},
            {"type": "select", "name": "input_type", "label": "Input Waveform", "options": [
                {"value": "step", "label": "Step Input"},
                {"value": "sinusoid", "label": "Sinusoidal"},
                {"value": "impulse", "label": "Impulse"},
                {"value": "none", "label": "Free Response"},
            ], "default": "step", "group": "Input"},
            {"type": "slider", "name": "input_frequency", "label": "Input Frequency", "min": 0.1, "max": 10.0, "step": 0.1, "default": 1.0, "unit": "Hz", "group": "Input", "visible_when": {"input_type": "sinusoid"}},
            {"type": "slider", "name": "input_amplitude", "label": "Amplitude", "min": 0.1, "max": 2.0, "step": 0.1, "default": 1.0, "unit": "m", "group": "Input"},
            {"type": "slider", "name": "simulation_time", "label": "Duration", "min": 2, "max": 20, "step": 1, "default": 10, "unit": "s", "group": "Simulation"},
        ],
        "default_params": {
            "mass": 1.0,
            "spring_constant": 10.0,
            "damping": 0.5,
            "input_type": "step",
            "input_frequency": 1.0,
            "input_amplitude": 1.0,
            "simulation_time": 10.0,
        },
        "plots": [
            {"id": "response", "title": "System Response", "description": "Input x(t) and output y(t) overlaid — the system as signal transformer"},
            {"id": "phase_portrait", "title": "Phase Portrait", "description": "y vs y\u2032 trajectory in phase plane"},
        ],
    },
    # =========================================================================
    # 18. DT DIFFERENCE EQUATION STEP-BY-STEP SOLVER
    # =========================================================================
    {
        "id": "dt_difference_equation",
        "name": "DT Difference Equation Solver",
        "description": "Step-by-step evaluation of discrete-time difference equations with synchronized block diagram visualization. Watch signal values propagate through gain, delay, and adder blocks one sample at a time.",
        "category": "Signal Processing",
        "thumbnail": "\U0001f522",
        "tags": ["difference equation", "discrete-time", "block diagram", "step-by-step", "impulse response", "accumulator"],
        "has_simulator": True,
        "controls": [
            {"type": "select", "name": "equation_preset", "label": "Difference Equation", "options": [
                {"value": "difference_machine", "label": "Difference Machine: y[n] = x[n] \u2212 x[n\u22121]"},
                {"value": "accumulator", "label": "Accumulator: y[n] = x[n] + y[n\u22121]"},
                {"value": "moving_average", "label": "Moving Average: y[n] = (x[n]+x[n\u22121])/2"},
                {"value": "leaky_integrator", "label": "Leaky Integrator: y[n] = 0.9y[n\u22121]+0.1x[n]"},
            ], "default": "difference_machine", "group": "Equation"},
            {"type": "select", "name": "input_signal", "label": "Input Signal", "options": [
                {"value": "impulse", "label": "Unit Impulse \u03b4[n]"},
                {"value": "step", "label": "Unit Step u[n]"},
                {"value": "ramp", "label": "Ramp n\u00b7u[n]"},
            ], "default": "impulse", "group": "Input Signal"},
            {"type": "slider", "name": "animation_speed", "label": "Animation Speed", "min": 0.5, "max": 3.0, "step": 0.5, "default": 1.0, "unit": "x", "group": "Playback"},
            {"type": "button", "name": "step_forward", "label": "Step Forward", "group": "Playback"},
            {"type": "button", "name": "step_backward", "label": "Step Back", "group": "Playback"},
            {"type": "button", "name": "reset", "label": "Reset", "group": "Playback"},
            {"type": "button", "name": "play_pause", "label": "Play", "group": "Playback"},
        ],
        "default_params": {
            "equation_preset": "difference_machine",
            "input_signal": "impulse",
            "animation_speed": 1.0,
        },
        "plots": [
            {"id": "input_signal", "title": "Input Signal x[n]", "description": "Discrete input signal stem plot, growing incrementally"},
            {"id": "output_signal", "title": "Output Signal y[n]", "description": "Computed output signal stem plot, growing incrementally"},
        ],
    },
    # =========================================================================
    # 19. POLYNOMIAL MULTIPLICATION VISUALIZER
    # =========================================================================
    {
        "id": "polynomial_multiplication",
        "name": "Polynomial Multiplication",
        "description": "Visualize the tabular/anti-diagonal method for multiplying two operator series (1 + aR + a²R² + …) × (1 + bR + b²R² + …). Watch how collecting terms along anti-diagonals produces the combined unit-sample response of cascaded first-order systems.",
        "category": "Signal Processing",
        "thumbnail": "\u2716",
        "tags": ["polynomial", "multiplication", "operator series", "cascade", "convolution", "anti-diagonal", "impulse response", "first-order"],
        "has_simulator": True,
        "controls": [
            {"type": "slider", "name": "pole_a", "label": "Pole a", "min": -0.95, "max": 0.95, "step": 0.05, "default": 0.5, "group": "System Poles"},
            {"type": "slider", "name": "pole_b", "label": "Pole b", "min": -0.95, "max": 0.95, "step": 0.05, "default": 0.3, "group": "System Poles"},
            {"type": "slider", "name": "num_terms", "label": "Number of Terms", "min": 3, "max": 10, "step": 1, "default": 6, "group": "Display"},
            {"type": "select", "name": "view_mode", "label": "View Mode", "options": [
                {"value": "tabular", "label": "Tabular (Anti-Diagonal)"},
                {"value": "graphical", "label": "Graphical (Cascade)"},
            ], "default": "tabular", "group": "Display"},
        ],
        "default_params": {
            "pole_a": 0.5,
            "pole_b": 0.3,
            "num_terms": 6,
            "view_mode": "tabular",
        },
        "plots": [
            {"id": "h1_response", "title": "h₁[n] = aⁿ", "description": "Impulse response of first system (pole at a)"},
            {"id": "h2_response", "title": "h₂[n] = bⁿ", "description": "Impulse response of second system (pole at b)"},
            {"id": "combined_response", "title": "Combined cₙ", "description": "Combined unit-sample response from anti-diagonal sums"},
        ],
    },
    # =========================================================================
    # 20. OPERATOR ALGEBRA VISUALIZER
    # =========================================================================
    {
        "id": "operator_algebra",
        "name": "Operator Algebra Visualizer",
        "description": "Explore the R-operator (delay operator) algebra for discrete-time systems. Type an operator polynomial like (1-R)^2 and instantly see the expanded form, factored form, difference equation, block diagram, and impulse response.",
        "category": "Signal Processing",
        "thumbnail": "\U0001f522",
        "tags": ["R-operator", "delay", "difference equation", "polynomial", "discrete-time", "impulse response", "block diagram"],
        "has_simulator": True,
        "controls": [
            {"type": "expression", "name": "expression", "label": "Operator Polynomial P(R)", "default": "(1-R)^2", "placeholder": "e.g. (1-R)^2, 1+2R+R^2", "group": "Expression"},
            {"type": "slider", "name": "num_samples", "label": "Impulse Response Length", "min": 5, "max": 40, "step": 1, "default": 15, "unit": "samples", "group": "Display"},
        ],
        "default_params": {
            "expression": "(1-R)^2",
            "num_samples": 15,
        },
        "plots": [
            {"id": "impulse_response", "title": "Impulse Response h[n]", "description": "Stem plot of the system impulse response (coefficients of the operator polynomial)"},
        ],
    },
    # =========================================================================
    # 21. POLE BEHAVIOR EXPLORER
    # =========================================================================
    {
        "id": "pole_behavior",
        "name": "Pole Behavior Explorer",
        "description": "Drag a pole along the real number line and watch the first-order DT system response y[n] = p\u2080\u207f u[n] update in real time. See how pole location determines convergence, divergence, and alternating-sign behavior. Quiz mode tests your intuition.",
        "category": "Signal Processing",
        "thumbnail": "\U0001f3af",
        "tags": ["poles", "discrete-time", "stability", "convergence", "first-order", "z-transform", "unit sample response"],
        "has_simulator": True,
        "controls": [
            {"type": "slider", "name": "pole_position", "label": "Pole Position (p\u2080)", "min": -2.0, "max": 2.0, "step": 0.01, "default": 0.5, "group": "Pole", "visible_when": {"mode": "explore"}},
            {"type": "slider", "name": "num_samples", "label": "Number of Samples", "min": 10, "max": 50, "step": 1, "default": 20, "group": "Display"},
            {"type": "checkbox", "name": "show_envelope", "label": "Show Envelope |\u2009p\u2080\u2009|\u207f", "default": False, "group": "Display", "visible_when": {"mode": "explore"}},
            {"type": "select", "name": "mode", "label": "Mode", "options": [
                {"value": "explore", "label": "Explore"},
                {"value": "quiz", "label": "Quiz"},
            ], "default": "explore", "group": "Mode"},
            {"type": "button", "name": "new_quiz", "label": "New Question", "group": "Quiz", "visible_when": {"mode": "quiz"}},
        ],
        "default_params": {
            "pole_position": 0.5,
            "num_samples": 20,
            "show_envelope": False,
            "mode": "explore",
        },
        "plots": [
            {"id": "stem_plot", "title": "Unit-Sample Response", "description": "Stem plot of y[n] = p\u2080\u207f u[n] showing the system's impulse response as the pole moves"},
        ],
    },
    # =========================================================================
    # 22. CYCLIC PATH DETECTOR
    # =========================================================================
    {
        "id": "cyclic_path_detector",
        "name": "Cyclic Path Detector",
        "description": "Detect cyclic signal paths in block diagrams. Identify feedback loops, classify systems as FIR or IIR, and test your understanding in quiz mode. Based on MIT 6.003 Lecture 2, slides 43-49.",
        "category": "Signal Processing",
        "thumbnail": "\U0001f517",
        "tags": ["cyclic paths", "feedback", "FIR", "IIR", "block diagram", "acyclic", "discrete-time", "operator"],
        "has_simulator": True,
        "controls": [
            {"type": "select", "name": "preset", "label": "Diagram Preset", "options": [
                {"value": "difference", "label": "Difference Machine"},
                {"value": "accumulator", "label": "Accumulator"},
                {"value": "cascaded_diff", "label": "Cascaded Difference"},
                {"value": "slide48_a", "label": "Slide 48 \u2014 System A"},
                {"value": "slide48_b", "label": "Slide 48 \u2014 System B"},
                {"value": "slide48_c", "label": "Slide 48 \u2014 System C"},
                {"value": "slide48_d", "label": "Slide 48 \u2014 System D"},
            ], "default": "difference", "group": "Diagram"},
            {"type": "select", "name": "mode", "label": "Mode", "options": [
                {"value": "explore", "label": "Explore"},
                {"value": "quiz", "label": "Quiz"},
            ], "default": "explore", "group": "Mode"},
            {"type": "checkbox", "name": "show_cycles", "label": "Highlight Cycles", "default": True, "group": "Display", "visible_when": {"mode": "explore"}},
            {"type": "slider", "name": "impulse_steps", "label": "Impulse Response Steps", "min": 5, "max": 30, "step": 1, "default": 15, "unit": "steps", "group": "Analysis"},
            {"type": "button", "name": "new_quiz", "label": "New Question", "group": "Quiz", "visible_when": {"mode": "quiz"}},
        ],
        "default_params": {
            "preset": "difference",
            "mode": "explore",
            "show_cycles": True,
            "impulse_steps": 15,
        },
        "plots": [
            {"id": "impulse_response", "title": "Impulse Response h[n]", "description": "Stem plot showing FIR (finite) vs IIR (infinite) impulse response"},
        ],
    },
    # =========================================================================
    # CASCADE & PARALLEL DECOMPOSITION
    # =========================================================================
    {
        "id": "cascade_parallel",
        "name": "Cascade & Parallel Decomposition",
        "description": "Decompose a second-order DT system into cascade (series) and parallel (partial fraction) forms. Watch step-by-step factoring of the operator polynomial and see that all three representations produce the same impulse response.",
        "category": "Signal Processing",
        "thumbnail": "\U0001f500",
        "tags": [
            "decomposition", "cascade", "parallel", "partial fractions",
            "poles", "transfer function", "DT", "impulse response", "modes",
            "second order", "factoring",
        ],
        "has_simulator": True,
        "controls": [
            {
                "type": "slider", "name": "a1", "label": "a\u2081 (Feedback Coeff 1)",
                "min": -2.0, "max": 2.0, "step": 0.01, "default": 1.6,
                "unit": "", "group": "System Coefficients",
                "description": "First feedback coefficient in y[n] = a\u2081 y[n-1] + a\u2082 y[n-2] + x[n]",
            },
            {
                "type": "slider", "name": "a2", "label": "a\u2082 (Feedback Coeff 2)",
                "min": -1.0, "max": 1.0, "step": 0.01, "default": -0.63,
                "unit": "", "group": "System Coefficients",
                "description": "Second feedback coefficient",
            },
            {
                "type": "button", "name": "decompose",
                "label": "Decompose \u2192", "group": "Animation",
            },
            {
                "type": "button", "name": "reset_decomposition",
                "label": "Reset Steps", "group": "Animation",
            },
        ],
        "default_params": {"a1": 1.6, "a2": -0.63},
        "plots": [
            {"id": "original_response", "title": "Original Form: h[n]", "description": "Impulse response computed directly from the difference equation"},
            {"id": "cascade_response", "title": "Cascade Form: h\u2081[n] * h\u2082[n]", "description": "Impulse response from convolving two first-order responses"},
            {"id": "parallel_response", "title": "Parallel Form: A\u2081p\u2081\u207f + A\u2082p\u2082\u207f", "description": "Impulse response from partial fraction sum"},
            {"id": "individual_modes", "title": "Individual Modes", "description": "Geometric modes shown separately with sum overlay"},
        ],
    },
    # =========================================================================
    # FUNDAMENTAL MODES SUPERPOSITION
    # =========================================================================
    {
        "id": "fundamental_modes",
        "name": "Fundamental Modes Superposition",
        "description": "Visualize how any Nth-order DT system's unit-sample response is a weighted sum of N fundamental modes (geometric sequences). Adjust poles and weights to see how individual modes A\u2096\u00b7p\u2096\u207f combine into the total response y[n] = \u03a3A\u2096\u00b7p\u2096\u207f.",
        "category": "Signal Processing",
        "thumbnail": "\U0001f4ca",
        "tags": [
            "poles", "modes", "superposition", "discrete-time",
            "partial fractions", "geometric sequences", "impulse response",
            "DT systems", "parallel form",
        ],
        "has_simulator": True,
        "controls": [
            {
                "type": "select", "name": "system_order", "label": "System Order",
                "options": [
                    {"value": "2", "label": "2 Poles"},
                    {"value": "3", "label": "3 Poles"},
                    {"value": "4", "label": "4 Poles"},
                ],
                "default": "2", "group": "System",
                "description": "Number of poles (fundamental modes)",
            },
            {
                "type": "select", "name": "mode", "label": "Mode",
                "options": [
                    {"value": "explore", "label": "Explore"},
                    {"value": "reconstruct", "label": "Reconstruct Challenge"},
                ],
                "default": "explore", "group": "System",
                "description": "Explore modes freely or match a mystery signal",
            },
            {
                "type": "slider", "name": "num_samples", "label": "Samples",
                "min": 5, "max": 50, "step": 1, "default": 25,
                "unit": "", "group": "Display",
                "description": "Number of discrete-time samples to display",
            },
            {
                "type": "slider", "name": "p1", "label": "Pole p\u2081",
                "min": -1.5, "max": 1.5, "step": 0.01, "default": 0.9,
                "unit": "", "group": "Poles",
                "description": "Location of pole 1 on the real line",
            },
            {
                "type": "slider", "name": "p2", "label": "Pole p\u2082",
                "min": -1.5, "max": 1.5, "step": 0.01, "default": 0.7,
                "unit": "", "group": "Poles",
                "description": "Location of pole 2 on the real line",
            },
            {
                "type": "slider", "name": "p3", "label": "Pole p\u2083",
                "min": -1.5, "max": 1.5, "step": 0.01, "default": -0.5,
                "unit": "", "group": "Poles",
                "description": "Location of pole 3 on the real line",
                "visible_when": {"system_order": ["3", "4"]},
            },
            {
                "type": "slider", "name": "p4", "label": "Pole p\u2084",
                "min": -1.5, "max": 1.5, "step": 0.01, "default": 0.3,
                "unit": "", "group": "Poles",
                "description": "Location of pole 4 on the real line",
                "visible_when": {"system_order": ["4"]},
            },
            {
                "type": "slider", "name": "A1", "label": "Weight A\u2081",
                "min": -5.0, "max": 5.0, "step": 0.1, "default": 4.5,
                "unit": "", "group": "Weights",
                "description": "Partial-fraction coefficient for mode 1",
            },
            {
                "type": "slider", "name": "A2", "label": "Weight A\u2082",
                "min": -5.0, "max": 5.0, "step": 0.1, "default": -3.5,
                "unit": "", "group": "Weights",
                "description": "Partial-fraction coefficient for mode 2",
            },
            {
                "type": "slider", "name": "A3", "label": "Weight A\u2083",
                "min": -5.0, "max": 5.0, "step": 0.1, "default": 1.0,
                "unit": "", "group": "Weights",
                "description": "Partial-fraction coefficient for mode 3",
                "visible_when": {"system_order": ["3", "4"]},
            },
            {
                "type": "slider", "name": "A4", "label": "Weight A\u2084",
                "min": -5.0, "max": 5.0, "step": 0.1, "default": 1.0,
                "unit": "", "group": "Weights",
                "description": "Partial-fraction coefficient for mode 4",
                "visible_when": {"system_order": ["4"]},
            },
            {
                "type": "select", "name": "difficulty", "label": "Difficulty",
                "options": [
                    {"value": "easy", "label": "Easy (2 poles)"},
                    {"value": "medium", "label": "Medium (3 poles)"},
                    {"value": "hard", "label": "Hard (4 poles)"},
                ],
                "default": "easy", "group": "Challenge",
                "description": "Challenge difficulty level",
                "visible_when": {"mode": "reconstruct"},
            },
            {
                "type": "button", "name": "new_challenge",
                "label": "New Challenge", "group": "Challenge",
                "visible_when": {"mode": "reconstruct"},
            },
            {
                "type": "button", "name": "show_answer",
                "label": "Reveal Answer", "group": "Challenge",
                "visible_when": {"mode": "reconstruct"},
            },
        ],
        "default_params": {
            "system_order": "2",
            "mode": "explore",
            "num_samples": 25,
            "p1": 0.9,
            "p2": 0.7,
            "p3": -0.5,
            "p4": 0.3,
            "A1": 4.5,
            "A2": -3.5,
            "A3": 1.0,
            "A4": 1.0,
            "difficulty": "easy",
        },
        "plots": [
            {"id": "modes_overlay", "title": "Fundamental Modes & Total Response", "description": "Stem plot showing each mode A\u2096\u00b7p\u2096\u207f as colored stems, with the total y[n] in white"},
            {"id": "pole_map", "title": "Pole Locations (Z-Plane)", "description": "Poles on the z-plane with unit circle stability boundary"},
            {"id": "mode_envelopes", "title": "Mode Competition (Amplitude Envelopes)", "description": "Envelope |A\u2096\u00b7p\u2096\u207f| showing which mode dominates at each time step"},
        ],
        "sticky_controls": True,
    },
    # =========================================================================
    # DT ↔ CT SIDE-BY-SIDE COMPARATOR
    # =========================================================================
    {
        "id": "dt_ct_comparator",
        "name": "DT \u2194 CT Comparator",
        "description": "Side-by-side comparison of first-order DT and CT systems sharing the same pole value p. See how p\u207f u[n] in DT and e\u1d56\u1d57 u(t) in CT produce fundamentally different stability behavior \u2014 the same number, two different worlds.",
        "category": "Signal Processing",
        "thumbnail": "\u2696\ufe0f",
        "tags": ["DT", "CT", "poles", "stability", "unit circle", "s-plane", "impulse response", "exponential", "comparison"],
        "has_simulator": True,
        "controls": [
            {"type": "slider", "name": "p", "label": "Pole Value (p)", "min": -2.0, "max": 2.0, "step": 0.01, "default": 0.5, "unit": "", "group": "Pole", "description": "Controls both systems simultaneously"},
            {"type": "slider", "name": "num_samples", "label": "DT Samples", "min": 5, "max": 30, "step": 1, "default": 20, "unit": "", "group": "Display"},
            {"type": "slider", "name": "ct_duration", "label": "CT Duration", "min": 1.0, "max": 8.0, "step": 0.5, "default": 4.0, "unit": "s", "group": "Display"},
            {"type": "checkbox", "name": "show_envelope", "label": "Show Envelope", "default": True, "group": "Display"},
            {"type": "select", "name": "mode", "label": "Mode", "options": [
                {"value": "explore", "label": "Explore"},
                {"value": "quiz", "label": "Quiz"},
            ], "default": "explore", "group": "Mode"},
            {"type": "button", "name": "new_quiz", "label": "New Question", "group": "Quiz", "visible_when": {"mode": "quiz"}},
        ],
        "default_params": {
            "p": 0.5,
            "num_samples": 20,
            "ct_duration": 4.0,
            "show_envelope": True,
            "mode": "explore",
        },
        "plots": [
            {"id": "dt_response", "title": "DT: y[n] = p\u207f u[n]", "description": "Stem plot of the discrete-time impulse response"},
            {"id": "ct_response", "title": "CT: y(t) = e\u1d56\u1d57 u(t)", "description": "Continuous-time impulse response curve"},
        ],
    },
    # =========================================================================
    # UNIT IMPULSE CONSTRUCTION LAB
    # =========================================================================
    {
        "id": "impulse_construction",
        "name": "Unit Impulse Construction",
        "description": "Build intuition for the Dirac delta function by watching rectangular pulses p\u03b5(t) of width 2\u03b5 and height 1/(2\u03b5) \u2014 always unit area \u2014 converge to \u03b4(t) as \u03b5\u21920. See the integral converge to u(t), pass the pulse through a first-order CT system, and contrast with the 'bad' building block w(t).",
        "category": "Signal Processing",
        "thumbnail": "\u26a1",
        "tags": ["impulse", "delta function", "Dirac delta", "unit step", "limiting process", "continuous-time", "rectangular pulse", "system response"],
        "has_simulator": True,
        "controls": [
            {"type": "slider", "name": "epsilon", "label": "Pulse Half-Width (\u03b5)", "min": 0.01, "max": 1.0, "step": 0.01, "default": 0.5, "unit": "s", "group": "Pulse Shape"},
            {"type": "select", "name": "mode", "label": "View Mode", "options": [
                {"value": "construction", "label": "Delta Construction"},
                {"value": "system_response", "label": "System Response"},
                {"value": "contrast", "label": "Contrast: Bad Building Block"},
            ], "default": "construction", "group": "Mode"},
            {"type": "slider", "name": "system_pole", "label": "System Pole (p)", "min": -5.0, "max": -0.1, "step": 0.1, "default": -1.0, "group": "System", "visible_when": {"mode": "system_response"}},
            {"type": "checkbox", "name": "show_limit", "label": "Show Ideal Limit", "default": True, "group": "Display"},
        ],
        "default_params": {
            "epsilon": 0.5,
            "mode": "construction",
            "system_pole": -1.0,
            "show_limit": True,
        },
        "plots": [
            {"id": "pulse_plot", "title": "Rectangular Pulse p\u03b5(t)", "description": "Unit-area rectangular pulse of width 2\u03b5 and height 1/(2\u03b5)"},
            {"id": "integral_plot", "title": "Running Integral", "description": "Cumulative integral converging to the unit step u(t)"},
            {"id": "system_output", "title": "System Output", "description": "Output when p\u03b5(t) is passed through a first-order CT system"},
            {"id": "contrast_plot", "title": "Contrast: w(t)", "description": "The 'bad' building block w(t) = 1 at t=0 only, whose integral is zero"},
        ],
    },
    # =========================================================================
    # CT IMPULSE RESPONSE BUILDER
    # =========================================================================
    {
        "id": "ct_impulse_response",
        "name": "CT Impulse Response Builder",
        "description": "Build the continuous-time impulse response e^(pt)u(t) term-by-term from the Taylor/operator series expansion A(1 + pA + p\u00b2A\u00b2 + \u2026)\u03b4(t). Watch partial sums converge to the exact exponential for stable poles (p < 0) and diverge for unstable poles (p > 0).",
        "category": "Signal Processing",
        "thumbnail": "\u2211",
        "tags": [
            "impulse response", "continuous-time", "operator", "Taylor series",
            "exponential", "convergence", "feedback", "CT", "s-plane", "poles",
        ],
        "has_simulator": True,
        "controls": [
            {
                "type": "slider", "name": "pole_p", "label": "Pole Value p",
                "min": -5.0, "max": 5.0, "step": 0.1, "default": -2.0,
                "unit": "", "group": "System",
                "description": "CT pole location on the real axis",
            },
            {
                "type": "slider", "name": "num_terms", "label": "Max Terms",
                "min": 1, "max": 20, "step": 1, "default": 10,
                "unit": "", "group": "Display",
                "description": "Maximum number of Taylor series terms to add",
            },
            {
                "type": "checkbox", "name": "show_all_partials",
                "label": "Show All Partial Sums", "default": True,
                "group": "Display",
            },
            {
                "type": "checkbox", "name": "show_individual_terms",
                "label": "Show Individual Terms", "default": False,
                "group": "Display",
            },
            {
                "type": "button", "name": "add_term",
                "label": "\u25b6 Add Term", "group": "Animation",
            },
            {
                "type": "button", "name": "remove_term",
                "label": "\u25c0 Remove Term", "group": "Animation",
            },
            {
                "type": "button", "name": "reset_terms",
                "label": "\u21ba Reset Terms", "group": "Animation",
            },
        ],
        "default_params": {
            "pole_p": -2.0,
            "num_terms": 10,
            "show_all_partials": True,
            "show_individual_terms": False,
        },
        "plots": [
            {
                "id": "taylor_buildup",
                "title": "Taylor Series Buildup",
                "description": "Partial sums S_N(t) approaching e^(pt)u(t)",
            },
            {
                "id": "individual_terms",
                "title": "Individual Terms",
                "description": "Each Taylor term T_k(t) = (pt)^k / k!",
            },
        ],
    },
    # =========================================================================
    # COMPLEX POLES & SINUSOIDAL MODES
    # =========================================================================
    {
        "id": "complex_poles_modes",
        "name": "Complex Poles & Sinusoidal Modes",
        "description": "Visualize how complex conjugate poles of a CT second-order system (mass-spring-damper) produce sinusoidal oscillation from the superposition of two complex exponential modes. Explore s-plane pole locations, mode decomposition, Taylor series convergence, and the 3D helix of e^(j\u03c9t).",
        "category": "Control Systems",
        "thumbnail": "\U0001f30a",
        "tags": [
            "complex poles", "sinusoidal modes", "mass-spring", "damping",
            "s-plane", "complex exponential", "Taylor series", "helix",
            "conjugate poles", "second order", "continuous time", "impulse response",
        ],
        "has_simulator": True,
        "sticky_controls": True,
        "controls": [
            {"type": "slider", "name": "K", "label": "Spring Constant (K)", "min": 1, "max": 100, "step": 1, "default": 10, "unit": "N/m", "group": "Physical System"},
            {"type": "slider", "name": "M", "label": "Mass (M)", "min": 0.1, "max": 5.0, "step": 0.1, "default": 1.0, "unit": "kg", "group": "Physical System"},
            {"type": "slider", "name": "b", "label": "Damping (b)", "min": 0.0, "max": 10.0, "step": 0.1, "default": 0.0, "unit": "Ns/m", "group": "Physical System"},
            {"type": "slider", "name": "num_taylor_terms", "label": "Taylor Terms", "min": 1, "max": 15, "step": 1, "default": 5, "unit": "", "group": "Taylor Series"},
            {"type": "slider", "name": "time_window", "label": "Time Window", "min": 1, "max": 20, "step": 0.5, "default": 5, "unit": "s", "group": "Display"},
        ],
        "default_params": {"K": 10.0, "M": 1.0, "b": 0.0, "num_taylor_terms": 5, "time_window": 5.0},
        "plots": [
            {"id": "s_plane", "title": "S-Plane Poles", "description": "Complex conjugate pole locations with stability regions"},
            {"id": "mode_decomposition", "title": "Mode Decomposition", "description": "Two complex exponential modes and their real sum h(t)"},
            {"id": "taylor_convergence", "title": "Taylor Series Convergence", "description": "Partial sums of sin(\u03c9\u2080t) Taylor series"},
            {"id": "helix_3d", "title": "3D Complex Exponential Helix", "description": "e^(j\u03c9\u2080t) as a helix in (t, Re, Im) space with real projection"},
        ],
    },
    # =========================================================================
    # Z-TRANSFORM PROPERTIES LAB
    # =========================================================================
    {
        "id": "z_transform_properties",
        "name": "Z-Transform Properties Lab",
        "description": "Interactive demonstration of the four key Z-transform properties: linearity, time delay, multiply-by-n, and convolution. Pick signals from a library, apply a property, and see the operation in both time domain and z-domain simultaneously with animated convolution and ROC visualization.",
        "category": "Transforms",
        "thumbnail": "\u2124",
        "tags": [
            "z-transform", "linearity", "delay", "convolution",
            "ROC", "poles", "zeros", "discrete-time", "properties",
        ],
        "has_simulator": True,
        "controls": [
            {"type": "select", "name": "signal_1", "label": "Signal x\u2081[n]", "options": [
                {"value": "impulse", "label": "\u03b4[n] (Impulse)"},
                {"value": "unit_step", "label": "u[n] (Unit Step)"},
                {"value": "geometric", "label": "a\u207f u[n] (Geometric)"},
                {"value": "ramp_geometric", "label": "n\u00b7a\u207f u[n] (Ramp)"},
                {"value": "cosine", "label": "cos(\u03c9\u2080n) u[n]"},
                {"value": "finite_121", "label": "[1, 2, 1] (Finite)"},
            ], "default": "unit_step", "group": "Signals"},
            {"type": "slider", "name": "signal_1_a", "label": "a (Signal 1)", "min": -0.95, "max": 0.95, "step": 0.05, "default": 0.5, "group": "Signals", "visible_when": {"signal_1": ["geometric", "ramp_geometric"]}},
            {"type": "slider", "name": "signal_1_omega0", "label": "\u03c9\u2080 (Signal 1)", "min": 0.1, "max": 3.0, "step": 0.1, "default": 1.0, "unit": "rad", "group": "Signals", "visible_when": {"signal_1": "cosine"}},

            {"type": "select", "name": "signal_2", "label": "Signal x\u2082[n]", "options": [
                {"value": "impulse", "label": "\u03b4[n] (Impulse)"},
                {"value": "unit_step", "label": "u[n] (Unit Step)"},
                {"value": "geometric", "label": "a\u207f u[n] (Geometric)"},
                {"value": "ramp_geometric", "label": "n\u00b7a\u207f u[n] (Ramp)"},
                {"value": "cosine", "label": "cos(\u03c9\u2080n) u[n]"},
                {"value": "finite_121", "label": "[1, 2, 1] (Finite)"},
            ], "default": "geometric", "group": "Signals", "visible_when": {"property": ["linearity", "convolution"]}},
            {"type": "slider", "name": "signal_2_a", "label": "a (Signal 2)", "min": -0.95, "max": 0.95, "step": 0.05, "default": 0.3, "group": "Signals", "visible_when": {"signal_2": ["geometric", "ramp_geometric"], "property": ["linearity", "convolution"]}},
            {"type": "slider", "name": "signal_2_omega0", "label": "\u03c9\u2080 (Signal 2)", "min": 0.1, "max": 3.0, "step": 0.1, "default": 1.0, "unit": "rad", "group": "Signals", "visible_when": {"signal_2": "cosine", "property": ["linearity", "convolution"]}},

            {"type": "select", "name": "property", "label": "Property", "options": [
                {"value": "linearity", "label": "Linearity"},
                {"value": "delay", "label": "Time Delay"},
                {"value": "multiply_n", "label": "Multiply by n"},
                {"value": "convolution", "label": "Convolution"},
            ], "default": "linearity", "group": "Property"},

            {"type": "slider", "name": "alpha", "label": "\u03b1 (alpha)", "min": -3.0, "max": 3.0, "step": 0.1, "default": 1.0, "group": "Property", "visible_when": {"property": "linearity"}},
            {"type": "slider", "name": "beta", "label": "\u03b2 (beta)", "min": -3.0, "max": 3.0, "step": 0.1, "default": 1.0, "group": "Property", "visible_when": {"property": "linearity"}},
            {"type": "slider", "name": "delay_k", "label": "Delay k", "min": 0, "max": 10, "step": 1, "default": 2, "group": "Property", "visible_when": {"property": "delay"}},

            {"type": "slider", "name": "num_samples", "label": "Samples", "min": 10, "max": 40, "step": 1, "default": 20, "group": "Display"},
        ],
        "default_params": {
            "signal_1": "unit_step",
            "signal_2": "geometric",
            "property": "linearity",
            "alpha": 1.0,
            "beta": 1.0,
            "delay_k": 2,
            "signal_1_a": 0.5,
            "signal_1_omega0": 1.0,
            "signal_2_a": 0.3,
            "signal_2_omega0": 1.0,
            "num_samples": 20,
        },
        "plots": [
            {"id": "signal_1", "title": "x\u2081[n]", "description": "Time-domain samples of signal 1"},
            {"id": "signal_2", "title": "x\u2082[n]", "description": "Time-domain samples of signal 2"},
            {"id": "result", "title": "Result", "description": "Result of applying the selected property"},
            {"id": "z_plane", "title": "Z-Plane", "description": "Pole-zero plot with ROC regions"},
        ],
    },
    # =========================================================================
    # Z TRANSFORM & ROC EXPLORER
    # =========================================================================
    {
        "id": "z_transform_roc",
        "name": "Z Transform & ROC Explorer",
        "description": "Interactive z-plane visualization exploring Z transforms, regions of convergence, and how ROC determines causality. See how the same H(z) maps to different time-domain signals depending on the ROC selection.",
        "category": "Transforms",
        "thumbnail": "Z",
        "tags": ["z-transform", "ROC", "poles", "zeros", "causality", "inverse z-transform", "stability", "convergence"],
        "has_simulator": True,
        "sticky_controls": True,
        "controls": [
            {"type": "select", "name": "signal_family", "label": "Signal Family", "options": [
                {"value": "right_exponential", "label": "Right-sided: a\u207fu[n]"},
                {"value": "left_exponential", "label": "Left-sided: -a\u207fu[-n-1]"},
                {"value": "two_sided", "label": "Two-sided Exponential"},
                {"value": "second_order", "label": "Second-order (2 poles)"},
                {"value": "damped_sinusoid", "label": "Damped Sinusoid: r\u207fcos(\u03c9\u2080n)u[n]"},
                {"value": "custom_rational", "label": "Custom Rational H(z)"},
            ], "default": "right_exponential", "group": "Signal"},

            {"type": "slider", "name": "pole_real", "label": "Pole 1 Real", "min": -1.5, "max": 1.5, "step": 0.01, "default": 0.7, "group": "Poles",
             "visible_when": {"signal_family": ["right_exponential", "left_exponential", "two_sided", "second_order"]}},
            {"type": "slider", "name": "pole_imag", "label": "Pole 1 Imaginary", "min": -1.5, "max": 1.5, "step": 0.01, "default": 0.0, "group": "Poles",
             "visible_when": {"signal_family": ["right_exponential", "left_exponential", "two_sided", "second_order"]}},
            {"type": "slider", "name": "pole2_real", "label": "Pole 2 Real", "min": -1.5, "max": 1.5, "step": 0.01, "default": -0.5, "group": "Poles",
             "visible_when": {"signal_family": ["two_sided", "second_order"]}},
            {"type": "slider", "name": "pole2_imag", "label": "Pole 2 Imaginary", "min": -1.5, "max": 1.5, "step": 0.01, "default": 0.0, "group": "Poles",
             "visible_when": {"signal_family": ["two_sided", "second_order"]}},

            {"type": "slider", "name": "r_magnitude", "label": "Radius r", "min": 0.1, "max": 1.5, "step": 0.01, "default": 0.8, "group": "Damped Sinusoid",
             "visible_when": {"signal_family": "damped_sinusoid"}},
            {"type": "slider", "name": "omega_0", "label": "Frequency \u03c9\u2080", "min": 0.1, "max": 3.14, "step": 0.01, "default": 0.785, "unit": "rad", "group": "Damped Sinusoid",
             "visible_when": {"signal_family": "damped_sinusoid"}},

            {"type": "expression", "name": "custom_num_coeffs", "label": "Numerator coeffs (comma-separated)", "default": "1", "group": "Custom H(z)",
             "visible_when": {"signal_family": "custom_rational"}},
            {"type": "expression", "name": "custom_den_coeffs", "label": "Denominator coeffs (comma-separated)", "default": "1, -0.7", "group": "Custom H(z)",
             "visible_when": {"signal_family": "custom_rational"}},

            {"type": "select", "name": "roc_selection", "label": "ROC Region", "options": [
                {"value": "auto_causal", "label": "Causal (outside all poles)"},
                {"value": "auto_anticausal", "label": "Anti-causal (inside all poles)"},
                {"value": "annular", "label": "Annular Ring (two-sided)"},
            ], "default": "auto_causal", "group": "Region of Convergence"},

            {"type": "slider", "name": "num_samples", "label": "Samples", "min": 10, "max": 60, "step": 1, "default": 30, "group": "Display"},
            {"type": "checkbox", "name": "show_convergence", "label": "Show Convergence", "default": False, "group": "Display"},
            {"type": "slider", "name": "convergence_terms", "label": "Partial Sum Terms", "min": 1, "max": 50, "step": 1, "default": 10, "group": "Display",
             "visible_when": {"show_convergence": True}},
        ],
        "default_params": {
            "signal_family": "right_exponential",
            "pole_real": 0.7, "pole_imag": 0.0,
            "pole2_real": -0.5, "pole2_imag": 0.0,
            "r_magnitude": 0.8, "omega_0": 0.785,
            "roc_selection": "auto_causal",
            "num_samples": 30,
            "show_convergence": False,
            "convergence_terms": 10,
            "custom_num_coeffs": "1",
            "custom_den_coeffs": "1, -0.7",
        },
        "plots": [
            {"id": "z_plane", "title": "Z-Plane", "description": "Poles, zeros, unit circle, and ROC region"},
            {"id": "time_domain", "title": "Time-Domain Signal x[n]", "description": "Inverse Z-transform stem plot determined by ROC selection"},
            {"id": "convergence", "title": "Convergence of Partial Sums", "description": "Watch partial sums approach the closed-form H(z)"},
        ],
    },
    # =========================================================================
    # INVERSE Z TRANSFORM STEP-BY-STEP SOLVER
    # =========================================================================
    {
        "id": "inverse_z_transform",
        "name": "Inverse Z Transform Solver",
        "description": "Step-by-step inverse Z transform solver. Factor the denominator, perform partial fraction decomposition, match Z-transform pairs based on ROC, and assemble the time-domain signal h[n]. Includes quiz mode and multiple solution methods.",
        "category": "Transforms",
        "thumbnail": "\u2124\u207b\u00b9",
        "tags": ["z-transform", "inverse", "partial fractions", "ROC", "poles", "residues", "step-by-step", "quiz"],
        "has_simulator": True,
        "controls": [
            {"type": "select", "name": "preset", "label": "Example H(z)", "options": [
                {"value": "example_1", "label": "Slide 35: z/((z\u22120.5)(z\u22120.8))"},
                {"value": "example_2", "label": "Slide 38: Standard PFE"},
                {"value": "example_3", "label": "Repeated Pole"},
                {"value": "example_4", "label": "Complex Poles"},
                {"value": "example_5", "label": "Mixed Causal/Anticausal"},
                {"value": "custom", "label": "Custom Coefficients"},
            ], "default": "example_1", "group": "Transfer Function"},
            {"type": "expression", "name": "num_coeffs", "label": "Numerator b[] (descending z)", "default": "1, 0", "group": "Transfer Function", "visible_when": {"preset": "custom"}},
            {"type": "expression", "name": "den_coeffs", "label": "Denominator a[] (descending z)", "default": "1, -1.3, 0.4", "group": "Transfer Function", "visible_when": {"preset": "custom"}},
            {"type": "select", "name": "roc_type", "label": "ROC Specification", "options": [
                {"value": "causal", "label": "Causal (|z| > max|pole|)"},
                {"value": "anticausal", "label": "Anti-causal (|z| < min|pole|)"},
                {"value": "custom", "label": "Custom (per-pole in viewer)"},
            ], "default": "causal", "group": "ROC"},
            {"type": "select", "name": "active_method", "label": "Solution Method", "options": [
                {"value": "partial_fractions", "label": "A: Partial Fractions"},
                {"value": "long_division", "label": "B: Long Division"},
                {"value": "power_series", "label": "C: Power Series"},
            ], "default": "partial_fractions", "group": "Method"},
            {"type": "select", "name": "mode", "label": "Mode", "options": [
                {"value": "solve", "label": "Solve"},
                {"value": "quiz", "label": "Quiz"},
            ], "default": "solve", "group": "Mode"},
            {"type": "slider", "name": "num_samples", "label": "Samples", "min": 10, "max": 60, "step": 1, "default": 30, "unit": "", "group": "Display"},
            {"type": "button", "name": "prev_step", "label": "\u2190 Prev Step", "group": "Navigation"},
            {"type": "button", "name": "next_step", "label": "Next Step \u2192", "group": "Navigation"},
            {"type": "button", "name": "show_all", "label": "Show All Steps", "group": "Navigation"},
            {"type": "button", "name": "reset_steps", "label": "Reset Steps", "group": "Navigation"},
            {"type": "button", "name": "new_quiz", "label": "New Quiz", "group": "Quiz", "visible_when": {"mode": "quiz"}},
        ],
        "default_params": {
            "preset": "example_1",
            "num_coeffs": "1, 0",
            "den_coeffs": "1, -1.3, 0.4",
            "roc_type": "causal",
            "active_method": "partial_fractions",
            "mode": "solve",
            "num_samples": 30,
        },
        "plots": [
            {"id": "pole_zero_map", "title": "Pole-Zero Map & ROC", "description": "Z-plane with poles, zeros, unit circle, and ROC shading"},
            {"id": "impulse_response", "title": "Impulse Response h[n]", "description": "Stem plot of the inverse Z transform result"},
            {"id": "magnitude_response", "title": "|H(e\u02b2\u03c9)|", "description": "Magnitude response on the unit circle"},
        ],
    },
    # =========================================================================
    # DT SYSTEM REPRESENTATION NAVIGATOR
    # =========================================================================
    {
        "id": "dt_system_representations",
        "name": "DT System Representation Navigator",
        "description": "Interactive concept map showing five equivalent representations of a discrete-time LTI system: block diagram, difference equation, system functional H(R), system function H(z), and impulse response h[n]. Enter a system in any form and see all five simultaneously with animated conversion paths.",
        "category": "Signal Processing",
        "thumbnail": "\U0001f5fa",
        "tags": [
            "representations", "difference equation", "transfer function",
            "impulse response", "block diagram", "H(z)", "H(R)",
            "delay operator", "z-transform", "concept map", "DT",
        ],
        "has_simulator": True,
        "controls": [
            {
                "type": "select", "name": "preset", "label": "System Preset",
                "options": [
                    {"value": "first_difference", "label": "First Difference (FIR)"},
                    {"value": "accumulator", "label": "Accumulator (IIR)"},
                    {"value": "moving_average_3", "label": "3-Point Moving Avg (FIR)"},
                    {"value": "leaky_integrator", "label": "Leaky Integrator (IIR)"},
                    {"value": "second_order", "label": "2nd-Order Resonator (IIR)"},
                    {"value": "two_tap_fir", "label": "Two-Tap Echo (FIR)"},
                    {"value": "custom", "label": "Custom Coefficients"},
                ],
                "default": "first_difference", "group": "System",
            },
            {
                "type": "expression", "name": "b_coefficients",
                "label": "b coefficients (feedforward)",
                "default": "1, -1",
                "placeholder": "e.g. 1, -0.5, 0.25",
                "group": "Custom Input",
                "visible_when": {"preset": "custom"},
            },
            {
                "type": "expression", "name": "a_coefficients",
                "label": "a coefficients (feedback)",
                "default": "1",
                "placeholder": "e.g. 1, -0.9 (a\u2080 = 1 always)",
                "group": "Custom Input",
                "visible_when": {"preset": "custom"},
            },
            {
                "type": "slider", "name": "num_samples",
                "label": "Impulse Response Samples",
                "min": 8, "max": 30, "step": 1, "default": 15,
                "group": "Display",
            },
            {
                "type": "select", "name": "mode", "label": "Mode",
                "options": [
                    {"value": "explore", "label": "Explore"},
                    {"value": "challenge", "label": "Challenge"},
                ],
                "default": "explore", "group": "Mode",
            },
            {
                "type": "button", "name": "new_challenge",
                "label": "New Challenge",
                "group": "Challenge",
                "visible_when": {"mode": "challenge"},
            },
            {
                "type": "button", "name": "reveal_all",
                "label": "Reveal Answer",
                "group": "Challenge",
                "visible_when": {"mode": "challenge"},
            },
        ],
        "default_params": {
            "preset": "first_difference",
            "b_coefficients": "1, -1",
            "a_coefficients": "1",
            "num_samples": 15,
            "mode": "explore",
        },
        "plots": [
            {"id": "impulse_response", "title": "Impulse Response h[n]", "description": "Stem plot of the system impulse response"},
            {"id": "pole_zero", "title": "Pole-Zero Map", "description": "Poles and zeros on the z-plane with unit circle"},
        ],
    },
    # =========================================================================
    # Lecture 06 — Laplace Transform
    # =========================================================================
    {
        "id": "laplace_roc",
        "name": "Laplace Transform & s-Plane ROC Explorer",
        "description": "Explore how the Laplace transform maps continuous-time signals to the s-plane. Select different signal types, move poles, and click ROC regions to see how the same H(s) produces different time-domain signals depending on the region of convergence.",
        "category": "Transforms",
        "thumbnail": "\U0001f504",
        "tags": ["laplace", "s-plane", "roc", "convergence", "causality", "transforms"],
        "has_simulator": True,
        "sticky_controls": True,
        "controls": [
            {
                "type": "select", "name": "signal_family",
                "label": "Signal Type",
                "options": [
                    {"value": "right_exponential", "label": "Right-sided: e\u1d43\u1d57u(t)"},
                    {"value": "left_exponential", "label": "Left-sided: -e\u1d43\u1d57u(-t)"},
                    {"value": "two_sided", "label": "Two-sided: e\u207b\u1d43|t|"},
                    {"value": "sum_exponentials", "label": "Sum: e\u1d56\u00b9\u1d57u(t) + e\u1d56\u00b2\u1d57u(t)"},
                    {"value": "second_order", "label": "Second-order (complex poles)"},
                    {"value": "custom_rational", "label": "Custom Rational H(s)"},
                ],
                "default": "right_exponential", "group": "Signal",
            },
            {
                "type": "slider", "name": "pole1_real",
                "label": "Pole 1 (Re)", "min": -5.0, "max": 5.0, "step": 0.1,
                "default": -1.0, "unit": "", "group": "Poles",
            },
            {
                "type": "slider", "name": "pole1_imag",
                "label": "Pole 1 (Im)", "min": -5.0, "max": 5.0, "step": 0.1,
                "default": 0.0, "unit": "", "group": "Poles",
                "visible_when": {"signal_family": ["second_order", "custom_rational"]},
            },
            {
                "type": "slider", "name": "pole2_real",
                "label": "Pole 2 (Re)", "min": -5.0, "max": 5.0, "step": 0.1,
                "default": 2.0, "unit": "", "group": "Poles",
                "visible_when": {"signal_family": ["two_sided", "sum_exponentials", "second_order"]},
            },
            {
                "type": "slider", "name": "pole2_imag",
                "label": "Pole 2 (Im)", "min": -5.0, "max": 5.0, "step": 0.1,
                "default": 0.0, "unit": "", "group": "Poles",
                "visible_when": {"signal_family": ["second_order", "custom_rational"]},
            },
            {
                "type": "select", "name": "roc_selection",
                "label": "ROC Region",
                "options": [
                    {"value": "auto_causal", "label": "Causal (right of rightmost pole)"},
                    {"value": "auto_anticausal", "label": "Anti-causal (left of leftmost pole)"},
                    {"value": "strip", "label": "Strip (between poles)"},
                ],
                "default": "auto_causal", "group": "ROC",
            },
            {
                "type": "slider", "name": "time_range",
                "label": "Time Range (\u00b1T)", "min": 1.0, "max": 10.0, "step": 0.5,
                "default": 5.0, "unit": "s", "group": "Display",
            },
            {
                "type": "slider", "name": "num_points",
                "label": "Plot Points", "min": 200, "max": 2000, "step": 100,
                "default": 500, "unit": "", "group": "Display",
            },
            {
                "type": "checkbox", "name": "show_convergence",
                "label": "Show Convergence Test",
                "default": False, "group": "Convergence",
            },
            {
                "type": "slider", "name": "sigma_test",
                "label": "Test \u03c3", "min": -5.0, "max": 5.0, "step": 0.1,
                "default": 0.0, "unit": "", "group": "Convergence",
                "visible_when": {"show_convergence": True},
            },
            {
                "type": "expression", "name": "custom_num_coeffs",
                "label": "Numerator coeffs", "default": "1", "group": "Custom",
                "visible_when": {"signal_family": "custom_rational"},
            },
            {
                "type": "expression", "name": "custom_den_coeffs",
                "label": "Denominator coeffs", "default": "1, 1", "group": "Custom",
                "visible_when": {"signal_family": "custom_rational"},
            },
        ],
        "default_params": {
            "signal_family": "right_exponential",
            "pole1_real": -1.0,
            "pole1_imag": 0.0,
            "pole2_real": 2.0,
            "pole2_imag": 0.0,
            "roc_selection": "auto_causal",
            "time_range": 5.0,
            "num_points": 500,
            "show_convergence": False,
            "sigma_test": 0.0,
            "custom_num_coeffs": "1",
            "custom_den_coeffs": "1, 1",
        },
        "plots": [
            {"id": "s_plane", "title": "s-Plane: Poles, Zeros & ROC", "description": "Complex s-plane showing pole/zero locations and the Region of Convergence as a shaded vertical strip"},
            {"id": "time_domain", "title": "Time-Domain Signal x(t)", "description": "Continuous-time waveform determined by H(s) and the chosen ROC"},
            {"id": "convergence", "title": "Convergence Test", "description": "Shows |x(t)e^{-\u03c3t}| to visualize where the Laplace integral converges"},
        ],
    },
    # =========================================================================
    # INITIAL & FINAL VALUE THEOREM VISUALIZER
    # =========================================================================
    {
        "id": "ivt_fvt_visualizer",
        "name": "Initial & Final Value Theorem",
        "description": "Interactive visualization of the Initial and Final Value Theorems for Laplace transforms. Explore how the kernel s\u00b7e^{-st} scans a signal: as s\u2192\u221e it concentrates near t=0 (IVT), as s\u21920 it flattens to capture the steady-state (FVT). Includes failure mode demonstrations where FVT breaks down.",
        "category": "Transforms",
        "thumbnail": "\u221e",
        "tags": [
            "laplace", "initial value theorem", "final value theorem",
            "IVT", "FVT", "s-domain", "kernel", "convergence",
            "steady-state", "stability", "failure modes",
        ],
        "has_simulator": True,
        "sticky_controls": True,
        "controls": [
            {
                "type": "select", "name": "signal_type",
                "label": "Signal",
                "options": [
                    {"value": "decaying_exp", "label": "Decaying Exp: e^{-t}u(t)"},
                    {"value": "step_response", "label": "Step Response: (1-e^{-2t})u(t)"},
                    {"value": "oscillatory_decay", "label": "Damped Oscillation: e^{-0.5t}cos(3t)u(t)"},
                ],
                "default": "decaying_exp", "group": "Signal",
            },
            {
                "type": "checkbox", "name": "failure_mode",
                "label": "Enable Failure Mode",
                "default": False, "group": "Signal",
            },
            {
                "type": "slider", "name": "log_s",
                "label": "log\u2081\u2080(s)",
                "min": -2.0, "max": 2.0, "step": 0.01,
                "default": 0.0, "unit": "", "group": "Laplace Variable",
            },
        ],
        "default_params": {
            "signal_type": "decaying_exp",
            "failure_mode": False,
            "log_s": 0.0,
        },
        "plots": [
            {"id": "signal_xt", "title": "Signal x(t)", "description": "The signal being analyzed with initial and final value reference lines"},
            {"id": "kernel_set", "title": "Laplace Kernel s\u00b7e^{-st}", "description": "The scanning kernel that concentrates near t=0 for large s and flattens for small s"},
            {"id": "product_integral", "title": "Product & Integral", "description": "x(t) multiplied by the kernel; the shaded area equals sX(s)"},
        ],
    },
    # =========================================================================
    # LAPLACE PROPERTIES LAB
    # =========================================================================
    {
        "id": "laplace_properties",
        "name": "Laplace Properties Lab",
        "description": "Interactive demonstration of the seven key Laplace transform properties: linearity, time delay, multiply-by-t, frequency shift, differentiation, integration, and convolution. Pick signals from a library, apply a property, and see the operation in both time domain and s-domain simultaneously with ROC visualization.",
        "category": "Transforms",
        "thumbnail": "\u2112",
        "tags": [
            "laplace", "linearity", "delay", "convolution",
            "ROC", "poles", "zeros", "continuous-time", "properties",
            "differentiation", "integration", "frequency-shift",
        ],
        "has_simulator": True,
        "controls": [
            {"type": "select", "name": "signal_1", "label": "Signal x\u2081(t)", "options": [
                {"value": "impulse", "label": "\u03b4(t) (Impulse)"},
                {"value": "unit_step", "label": "u(t) (Unit Step)"},
                {"value": "exponential", "label": "e^(\u2212\u03b1t) u(t)"},
                {"value": "ramp_exp", "label": "t\u00b7e^(\u2212\u03b1t) u(t)"},
                {"value": "cosine", "label": "cos(\u03c9\u2080t) u(t)"},
                {"value": "damped_cosine", "label": "e^(\u2212\u03b1t)cos(\u03c9\u2080t) u(t)"},
            ], "default": "unit_step", "group": "Signals"},
            {"type": "slider", "name": "signal_1_alpha", "label": "\u03b1 (Signal 1)", "min": 0.1, "max": 5.0, "step": 0.1, "default": 1.0, "group": "Signals",
             "visible_when": {"signal_1": ["exponential", "ramp_exp", "damped_cosine"]}},
            {"type": "slider", "name": "signal_1_omega0", "label": "\u03c9\u2080 (Signal 1)", "min": 0.1, "max": 10.0, "step": 0.1, "default": 2.0, "unit": "rad/s", "group": "Signals",
             "visible_when": {"signal_1": ["cosine", "damped_cosine"]}},

            {"type": "select", "name": "signal_2", "label": "Signal x\u2082(t)", "options": [
                {"value": "impulse", "label": "\u03b4(t) (Impulse)"},
                {"value": "unit_step", "label": "u(t) (Unit Step)"},
                {"value": "exponential", "label": "e^(\u2212\u03b1t) u(t)"},
                {"value": "ramp_exp", "label": "t\u00b7e^(\u2212\u03b1t) u(t)"},
                {"value": "cosine", "label": "cos(\u03c9\u2080t) u(t)"},
                {"value": "damped_cosine", "label": "e^(\u2212\u03b1t)cos(\u03c9\u2080t) u(t)"},
            ], "default": "exponential", "group": "Signals",
             "visible_when": {"property": ["linearity", "convolution"]}},
            {"type": "slider", "name": "signal_2_alpha", "label": "\u03b1 (Signal 2)", "min": 0.1, "max": 5.0, "step": 0.1, "default": 1.0, "group": "Signals",
             "visible_when": {"signal_2": ["exponential", "ramp_exp", "damped_cosine"]}},
            {"type": "slider", "name": "signal_2_omega0", "label": "\u03c9\u2080 (Signal 2)", "min": 0.1, "max": 10.0, "step": 0.1, "default": 2.0, "unit": "rad/s", "group": "Signals",
             "visible_when": {"signal_2": ["cosine", "damped_cosine"]}},

            {"type": "select", "name": "property", "label": "Property", "options": [
                {"value": "linearity", "label": "Linearity"},
                {"value": "delay", "label": "Time Delay"},
                {"value": "multiply_t", "label": "Multiply by t"},
                {"value": "freq_shift", "label": "Frequency Shift"},
                {"value": "differentiate", "label": "Differentiation"},
                {"value": "integrate", "label": "Integration"},
                {"value": "convolution", "label": "Convolution"},
            ], "default": "linearity", "group": "Property"},

            {"type": "slider", "name": "alpha", "label": "a (scale \u2081)", "min": -3.0, "max": 3.0, "step": 0.1, "default": 1.0, "group": "Property",
             "visible_when": {"property": "linearity"}},
            {"type": "slider", "name": "beta", "label": "b (scale \u2082)", "min": -3.0, "max": 3.0, "step": 0.1, "default": 1.0, "group": "Property",
             "visible_when": {"property": "linearity"}},
            {"type": "slider", "name": "delay_T", "label": "Delay T", "min": 0.0, "max": 5.0, "step": 0.1, "default": 1.0, "unit": "s", "group": "Property",
             "visible_when": {"property": "delay"}},
            {"type": "slider", "name": "freq_shift_alpha", "label": "Shift \u03b1", "min": -3.0, "max": 3.0, "step": 0.1, "default": 1.0, "group": "Property",
             "visible_when": {"property": "freq_shift"}},
        ],
        "default_params": {
            "signal_1": "unit_step",
            "signal_2": "exponential",
            "property": "linearity",
            "alpha": 1.0,
            "beta": 1.0,
            "delay_T": 1.0,
            "freq_shift_alpha": 1.0,
            "signal_1_alpha": 1.0,
            "signal_1_omega0": 2.0,
            "signal_2_alpha": 1.0,
            "signal_2_omega0": 2.0,
        },
        "plots": [
            {"id": "signal_1", "title": "x\u2081(t)", "description": "Time-domain plot of signal 1"},
            {"id": "signal_2", "title": "x\u2082(t)", "description": "Time-domain plot of signal 2"},
            {"id": "result", "title": "Result", "description": "Result of applying the selected property"},
            {"id": "s_plane", "title": "S-Plane", "description": "Pole-zero plot with ROC regions in the s-plane"},
        ],
    },

    # =========================================================================
    # ODE SOLVER VIA LAPLACE TRANSFORM
    # =========================================================================
    {
        "id": "ode_laplace_solver",
        "name": "ODE Solver via Laplace Transform",
        "description": "Step-by-step solution of linear constant-coefficient ODEs using the Laplace transform pipeline: take L{}, solve algebraically for Y(s), partial fractions, inverse Laplace, and plot y(t). No homogeneous/particular solution splitting needed!",
        "category": "Transforms",
        "thumbnail": "\u2112",
        "tags": ["ODE", "Laplace transform", "differential equation", "partial fractions", "inverse Laplace", "s-domain"],
        "has_simulator": True,
        "controls": [
            {"type": "select", "name": "preset", "label": "ODE Preset", "options": [
                {"value": "first_order_impulse", "label": "Lec 6 Ex 1: \u1e8f + y = \u03b4(t)"},
                {"value": "second_order_impulse", "label": "Lec 6 Ex 2: \u00ff + 3\u1e8f + 2y = \u03b4(t)"},
                {"value": "second_order_step", "label": "Step: \u00ff + 3\u1e8f + 2y = u(t)"},
                {"value": "underdamped", "label": "Underdamped: \u00ff + 2\u1e8f + 5y = \u03b4(t)"},
                {"value": "repeated_poles", "label": "Repeated: \u00ff + 2\u1e8f + y = \u03b4(t)"},
                {"value": "third_order", "label": "3rd: y\u2034 + 6y\u2033 + 11\u1e8f + 6y = \u03b4(t)"},
                {"value": "exponential_input", "label": "Exp: \u1e8f + 2y = e\u207b\u1d57u(t)"},
                {"value": "custom", "label": "Custom Coefficients"},
            ], "default": "first_order_impulse", "group": "ODE"},
            {"type": "expression", "name": "output_coeffs", "label": "Output coeffs a\u2099,...,a\u2080 (descending)", "default": "1, 3, 2", "group": "ODE", "visible_when": {"preset": "custom"}},
            {"type": "expression", "name": "input_coeffs", "label": "Input coeffs b\u2098,...,b\u2080 (descending)", "default": "1", "group": "ODE", "visible_when": {"preset": "custom"}},
            {"type": "select", "name": "input_signal", "label": "Input Signal x(t)", "options": [
                {"value": "delta", "label": "\u03b4(t) \u2014 Impulse"},
                {"value": "step", "label": "u(t) \u2014 Unit Step"},
                {"value": "exp", "label": "e^(\u2212\u03b1t)u(t) \u2014 Exponential"},
                {"value": "cosine", "label": "cos(\u03c9t)u(t) \u2014 Cosine"},
            ], "default": "delta", "group": "Input"},
            {"type": "slider", "name": "alpha", "label": "\u03b1 (decay rate)", "min": 0.1, "max": 10.0, "step": 0.1, "default": 1.0, "unit": "", "group": "Input", "visible_when": {"input_signal": "exp"}},
            {"type": "slider", "name": "omega", "label": "\u03c9 (frequency)", "min": 0.1, "max": 20.0, "step": 0.1, "default": 2.0, "unit": "rad/s", "group": "Input", "visible_when": {"input_signal": "cosine"}},
            {"type": "checkbox", "name": "show_compare", "label": "Compare: Classical Method", "default": False, "group": "Display"},
            {"type": "slider", "name": "t_max", "label": "Time Range", "min": 2.0, "max": 20.0, "step": 0.5, "default": 8.0, "unit": "s", "group": "Display"},
        ],
        "default_params": {
            "preset": "first_order_impulse",
            "output_coeffs": "1, 3, 2",
            "input_coeffs": "1",
            "input_signal": "delta",
            "alpha": 1.0,
            "omega": 2.0,
            "show_compare": False,
            "t_max": 8.0,
        },
        "plots": [
            {"id": "input_signal", "title": "Input Signal x(t)", "description": "The input driving signal"},
            {"id": "pole_zero_splane", "title": "Pole-Zero Map (s-plane)", "description": "Poles and zeros of Y(s) in the complex s-plane"},
            {"id": "time_response", "title": "Time-Domain Response y(t)", "description": "The solution of the ODE"},
        ],
    },
    # =========================================================================
    # RESONANCE ANATOMY EXPLORER
    # =========================================================================
    {
        "id": "resonance_anatomy",
        "name": "Resonance Anatomy Explorer",
        "description": "Dissect the three characteristic frequencies of a second-order system H(s) = K/(Ms\u00b2 + Bs + K): the undamped natural frequency \u03c9\u2080, the damped oscillation frequency \u03c9_d, and the magnitude peak frequency \u03c9_peak. Watch them converge and disappear as damping increases.",
        "category": "Control Systems",
        "thumbnail": "\U0001f50d",
        "tags": [
            "resonance", "second order", "natural frequency", "damped frequency",
            "peak frequency", "damping ratio", "mass-spring-damper", "s-plane",
            "frequency response", "impulse response",
        ],
        "has_simulator": True,
        "sticky_controls": True,
        "controls": [
            {"type": "slider", "name": "K", "label": "Spring Constant (K)", "min": 1, "max": 100, "step": 0.5, "default": 25, "unit": "N/m", "group": "Physical System"},
            {"type": "slider", "name": "M", "label": "Mass (M)", "min": 0.1, "max": 5.0, "step": 0.1, "default": 1.0, "unit": "kg", "group": "Physical System"},
            {"type": "slider", "name": "B", "label": "Damping (B)", "min": 0.0, "max": 20.0, "step": 0.1, "default": 2.0, "unit": "Ns/m", "group": "Physical System"},
            {"type": "slider", "name": "time_window", "label": "Time Window", "min": 1, "max": 20, "step": 0.5, "default": 8, "unit": "s", "group": "Display"},
        ],
        "default_params": {"K": 25.0, "M": 1.0, "B": 2.0, "time_window": 8.0},
        "plots": [
            {"id": "magnitude_response", "title": "Magnitude Response |H(j\u03c9)|", "description": "Frequency response with \u03c9\u2080, \u03c9_d, and \u03c9_peak markers"},
            {"id": "s_plane", "title": "S-Plane Poles", "description": "Complex conjugate poles with geometric \u03c3/\u03c9_d decomposition"},
            {"id": "impulse_response", "title": "Impulse Response h(t)", "description": "Time-domain oscillation at \u03c9_d with exponential envelope"},
        ],
    },

    # =========================================================================
    # EIGENFUNCTION TESTER LAB
    # =========================================================================
    {
        "id": "eigenfunction_tester",
        "name": "Eigenfunction Tester Lab",
        "description": "Test which signals are eigenfunctions of LTI systems. Complex exponentials e^{st} are eigenfunctions of ALL LTI systems with eigenvalue H(s). Verify this for multiple systems and signal types, with vector diagrams in the s-plane.",
        "category": "Transforms",
        "thumbnail": "\u03bb",
        "tags": [
            "eigenfunction", "eigenvalue", "LTI", "frequency response",
            "transfer function", "complex exponential", "Laplace", "H(s)",
        ],
        "has_simulator": True,
        "sticky_controls": True,
        "controls": [
            # System selection
            {"type": "select", "name": "system_preset", "label": "LTI System", "options": [
                {"value": "lecture_example", "label": "Lecture 9: H(s) = 1/(s+2)"},
                {"value": "integrator", "label": "Integrator: H(s) = 1/s"},
                {"value": "second_order_real", "label": "2nd Order: 1/((s+1)(s+3))"},
                {"value": "second_order_complex", "label": "Underdamped: 1/(s\u00b2+2s+5)"},
                {"value": "unstable", "label": "Unstable: 1/(s\u22121)"},
                {"value": "allpass", "label": "Allpass: (s\u22121)/(s+1)"},
                {"value": "custom", "label": "Custom Coefficients"},
            ], "default": "lecture_example", "group": "System"},
            # Custom coefficients
            {"type": "expression", "name": "num_coeffs", "label": "Numerator N(s) coeffs", "default": "1", "placeholder": "e.g. 1 or 2, 7, 8", "group": "System", "visible_when": {"system_preset": "custom"}},
            {"type": "expression", "name": "den_coeffs", "label": "Denominator D(s) coeffs", "default": "1, 2", "placeholder": "e.g. 1, 2 or 1, 3, 4", "group": "System", "visible_when": {"system_preset": "custom"}},
            # Signal selection
            {"type": "select", "name": "test_signal", "label": "Test Signal", "options": [
                {"value": "exp_neg", "label": "e^{\u22121t} (s = \u22121)"},
                {"value": "exp_pos", "label": "e^{t} (s = 1)"},
                {"value": "exp_jt", "label": "e^{jt} (s = j)"},
                {"value": "exp_neg_jt", "label": "e^{\u2212jt} (s = \u2212j)"},
                {"value": "cos_t", "label": "cos(t)"},
                {"value": "sin_t", "label": "sin(t)"},
                {"value": "unit_step", "label": "u(t)"},
                {"value": "t_squared", "label": "t\u00b2 u(t)"},
                {"value": "custom_exp", "label": "e^{st} (custom s)"},
            ], "default": "exp_neg", "group": "Signal"},
            # Custom s parameters
            {"type": "slider", "name": "custom_s_real", "label": "\u03c3 (Real part of s)", "min": -5.0, "max": 5.0, "step": 0.1, "default": -1.0, "group": "Signal", "visible_when": {"test_signal": "custom_exp"}},
            {"type": "slider", "name": "custom_s_imag", "label": "\u03c9 (Imag part of s)", "min": -5.0, "max": 5.0, "step": 0.1, "default": 0.0, "group": "Signal", "visible_when": {"test_signal": "custom_exp"}},
            # Display options
            {"type": "slider", "name": "time_range", "label": "Time Range", "min": 1.0, "max": 10.0, "step": 0.5, "default": 5.0, "unit": "s", "group": "Display"},
            {"type": "checkbox", "name": "show_ratio", "label": "Show Ratio Plot", "default": True, "group": "Display"},
            {"type": "checkbox", "name": "show_splane", "label": "Show S-Plane", "default": True, "group": "Display"},
            # Mode
            {"type": "select", "name": "mode", "label": "Mode", "options": [
                {"value": "explore", "label": "Explore"},
                {"value": "quiz", "label": "Quiz"},
            ], "default": "explore", "group": "Mode"},
            {"type": "button", "name": "new_quiz", "label": "New Question", "group": "Mode", "visible_when": {"mode": "quiz"}},
        ],
        "default_params": {
            "system_preset": "lecture_example",
            "num_coeffs": "1",
            "den_coeffs": "1, 2",
            "test_signal": "exp_neg",
            "custom_s_real": -1.0,
            "custom_s_imag": 0.0,
            "time_range": 5.0,
            "show_ratio": True,
            "show_splane": True,
            "mode": "explore",
        },
        "plots": [
            {"id": "time_domain", "title": "Input x(t) vs Output y(t)", "description": "Input and output signals overlaid. For eigenfunctions, output is a scaled version of input."},
            {"id": "ratio_plot", "title": "Ratio y(t)/x(t)", "description": "Constant for eigenfunctions (= eigenvalue), varies for non-eigenfunctions."},
            {"id": "s_plane", "title": "S-Plane: Poles, Zeros & Vectors", "description": "Pole-zero map with vectors to evaluation point s."},
        ],
    },

    # =========================================================================
    # VECTOR DIAGRAM FREQUENCY RESPONSE BUILDER
    # =========================================================================
    {
        "id": "vector_freq_response",
        "name": "Vector Diagram Frequency Response",
        "description": "Build frequency response curves from vector diagrams. Watch vectors from poles and zeros to the jω axis trace out magnitude and phase as frequency sweeps. Recreates the animated construction from MIT 6.003 Lecture 9.",
        "category": "Transforms",
        "thumbnail": "📐",
        "tags": [
            "frequency response", "vector diagram", "poles", "zeros",
            "magnitude", "phase", "s-plane", "eigenfunction",
            "transfer function", "Bode",
        ],
        "has_simulator": True,
        "sticky_controls": True,
        "controls": [
            # System Configuration
            {"type": "select", "name": "preset", "label": "System Preset", "options": [
                {"value": "single_zero", "label": "Single Zero: H(s) = s \u2212 z\u2081"},
                {"value": "single_pole", "label": "Single Pole: H(s) = K/(s \u2212 p\u2081)"},
                {"value": "pole_zero_pair", "label": "Pole-Zero: H(s) = K(s \u2212 z\u2081)/(s \u2212 p\u2081)"},
                {"value": "conjugate_poles", "label": "Conjugate Poles: H(s) = K/((s \u2212 p\u2081)(s \u2212 p\u2081*))"},
                {"value": "custom", "label": "Custom Configuration"},
            ], "default": "single_zero", "group": "System"},
            {"type": "slider", "name": "gain", "label": "Gain K", "min": 0.1, "max": 20.0, "step": 0.1, "default": 1.0, "group": "System",
             "visible_when": {"preset": ["single_pole", "pole_zero_pair", "conjugate_poles", "custom"]}},

            # Zero positions
            {"type": "slider", "name": "zero1_real", "label": "Zero \u03c3 (real)", "min": -5.0, "max": 5.0, "step": 0.1, "default": -3.0, "group": "Zeros",
             "visible_when": {"preset": ["single_zero", "pole_zero_pair", "custom"]}},
            {"type": "slider", "name": "zero1_imag", "label": "Zero j\u03c9 (imag)", "min": -5.0, "max": 5.0, "step": 0.1, "default": 0.0, "group": "Zeros",
             "visible_when": {"preset": ["custom"]}},

            # Pole positions
            {"type": "slider", "name": "pole1_real", "label": "Pole 1 \u03c3 (real)", "min": -5.0, "max": 1.0, "step": 0.1, "default": -3.0, "group": "Poles",
             "visible_when": {"preset": ["single_pole", "pole_zero_pair", "conjugate_poles", "custom"]}},
            {"type": "slider", "name": "pole1_imag", "label": "Pole 1 j\u03c9 (imag)", "min": 0.0, "max": 5.0, "step": 0.1, "default": 3.0, "group": "Poles",
             "visible_when": {"preset": ["conjugate_poles", "custom"]}},
            {"type": "slider", "name": "pole2_real", "label": "Pole 2 \u03c3 (real)", "min": -5.0, "max": 1.0, "step": 0.1, "default": -1.0, "group": "Poles",
             "visible_when": {"preset": ["custom"]}},
            {"type": "slider", "name": "pole2_imag", "label": "Pole 2 j\u03c9 (imag)", "min": -5.0, "max": 5.0, "step": 0.1, "default": 0.0, "group": "Poles",
             "visible_when": {"preset": ["custom"]}},

            # Display
            {"type": "slider", "name": "omega_max", "label": "Frequency Range \u00b1\u03c9", "min": 2.0, "max": 15.0, "step": 0.5, "default": 5.0, "unit": "rad/s", "group": "Display"},
            {"type": "checkbox", "name": "show_individual", "label": "Show Individual Contributions", "default": False, "group": "Display"},
        ],
        "default_params": {
            "preset": "single_zero",
            "gain": 1.0,
            "zero1_real": -3.0,
            "zero1_imag": 0.0,
            "pole1_real": -3.0,
            "pole1_imag": 3.0,
            "pole2_real": -1.0,
            "pole2_imag": 0.0,
            "omega_max": 5.0,
            "show_individual": False,
        },
        "plots": [
            {"id": "s_plane", "title": "s-Plane: Poles & Zeros", "description": "Interactive s-plane showing pole/zero locations and animated vectors to j\u03c9"},
            {"id": "magnitude_response", "title": "|H(j\u03c9)| Magnitude", "description": "Magnitude of frequency response, traced out as \u03c9 sweeps"},
            {"id": "phase_response", "title": "\u2220H(j\u03c9) Phase", "description": "Phase of frequency response, traced out as \u03c9 sweeps"},
        ],
    },

    # =========================================================================
    # AUDIO FREQUENCY RESPONSE PLAYGROUND
    # =========================================================================
    {
        "id": "audio_freq_response",
        "name": "Audio Frequency Response Playground",
        "description": "Place poles and zeros on the s-plane to define a transfer function H(s) and instantly see how it shapes the frequency response. Apply the filter to test signals (sine, multi-tone, chirp, square wave) and compare input vs output in time and frequency domains. Includes preset filters (lowpass, highpass, bandpass, notch, resonant) and a challenge mode.",
        "category": "Signal Processing",
        "thumbnail": "\U0001f39b\ufe0f",
        "tags": [
            "frequency response", "poles", "zeros", "filter", "audio",
            "bode", "magnitude", "phase", "transfer function",
            "lowpass", "highpass", "bandpass", "notch", "resonant",
        ],
        "has_simulator": True,
        "sticky_controls": True,
        "controls": [
            {"type": "select", "name": "mode", "label": "Mode", "options": [
                {"value": "explore", "label": "Explore"},
                {"value": "challenge", "label": "Challenge"},
            ], "default": "explore", "group": "Mode"},
            {"type": "select", "name": "signal_type", "label": "Test Signal", "options": [
                {"value": "multi_tone", "label": "Multi-Tone (3 freq)"},
                {"value": "sine", "label": "Sine Wave"},
                {"value": "chirp", "label": "Chirp (Sweep)"},
                {"value": "square", "label": "Square Wave"},
                {"value": "white_noise", "label": "White Noise"},
            ], "default": "multi_tone", "group": "Signal"},
            {"type": "slider", "name": "signal_freq", "label": "Signal Frequency", "min": 20, "max": 2000, "step": 10, "default": 440, "unit": "Hz", "group": "Signal",
             "visible_when": {"signal_type": ["sine", "square"]}},
            {"type": "checkbox", "name": "show_db_scale", "label": "Magnitude in dB", "default": True, "group": "Display"},
            {"type": "checkbox", "name": "show_phase", "label": "Show Phase Response", "default": True, "group": "Display"},
            {"type": "slider", "name": "gain_K", "label": "System Gain (K)", "min": 0.1, "max": 10.0, "step": 0.1, "default": 1.0, "unit": "", "group": "Gain"},
        ],
        "default_params": {
            "mode": "explore",
            "signal_type": "multi_tone",
            "signal_freq": 440,
            "show_db_scale": True,
            "show_phase": True,
            "gain_K": 1.0,
        },
        "plots": [
            {"id": "s_plane", "title": "S-Plane Pole-Zero Map", "description": "Interactive s-plane showing poles (\u00d7) and zeros (\u25cb). Click to place, right-click to remove. Left half-plane is the stable region."},
            {"id": "magnitude_response", "title": "Magnitude Response |H(j\u03c9)|", "description": "Bode magnitude plot showing how the filter attenuates or amplifies each frequency."},
            {"id": "phase_response", "title": "Phase Response \u2220H(j\u03c9)", "description": "Phase shift introduced by the filter at each frequency."},
            {"id": "time_domain", "title": "Time Domain: Input vs Output", "description": "Test signal before and after filtering."},
            {"id": "spectrum", "title": "Frequency Spectrum", "description": "FFT magnitude of input and output signals showing spectral content changes."},
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
