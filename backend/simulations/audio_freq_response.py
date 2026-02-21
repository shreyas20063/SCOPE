"""
Audio Frequency Response Playground Simulator

Interactive pole/zero placement on the s-plane to explore how H(jw) shapes
frequency response. Users click to place poles and zeros, see magnitude/phase
response, and observe filtered signal effects. Includes preset filters and
a challenge mode.

Based on MIT 6.003 Lecture 9: Frequency Response.
"""

import random
from typing import Any, Dict, List, Optional

import numpy as np
from scipy.signal import chirp as scipy_chirp, lsim, lti, zpk2tf

from .base_simulator import BaseSimulator


class AudioFreqResponseSimulator(BaseSimulator):
    """
    Audio Frequency Response Playground.

    Users place poles/zeros on the s-plane to define H(s), then observe:
    - |H(jw)| magnitude and phase response
    - Filtered signal in time and frequency domains
    - Preset filter configurations and challenge mode
    """

    # Constants
    SAMPLE_RATE = 16000
    NUM_FREQ_POINTS = 1000
    FREQ_MIN_HZ = 1.0
    FREQ_MAX_HZ = 10000.0
    MAX_POLES = 8
    MAX_ZEROS = 8
    IMAG_THRESHOLD = 1e-6  # Below this, treat as real (no conjugate)
    BASE_FREQ_HZ = 500.0   # Default center frequency for presets

    COLORS = {
        "magnitude": "#14b8a6",      # teal
        "phase": "#8b5cf6",          # purple
        "input": "#3b82f6",          # blue
        "output": "#ef4444",         # red
        "target": "#f59e0b",         # amber
        "reference": "#10b981",      # green
        "pole": "#ef4444",           # red
        "zero": "#3b82f6",           # blue
        "stable_fill": "rgba(52, 211, 153, 0.08)",
        "jw_axis": "#a855f7",        # purple
        "grid": "rgba(148, 163, 184, 0.15)",
        "text": "#f1f5f9",
        "text_secondary": "#94a3b8",
    }

    PARAMETER_SCHEMA = {
        "mode": {
            "type": "select",
            "label": "Mode",
            "options": [
                {"value": "explore", "label": "Explore"},
                {"value": "challenge", "label": "Challenge"},
            ],
            "default": "explore",
        },
        "signal_type": {
            "type": "select",
            "label": "Test Signal",
            "options": [
                {"value": "multi_tone", "label": "Multi-Tone (3 freq)"},
                {"value": "sine", "label": "Sine Wave"},
                {"value": "chirp", "label": "Chirp (Sweep)"},
                {"value": "square", "label": "Square Wave"},
                {"value": "white_noise", "label": "White Noise"},
            ],
            "default": "multi_tone",
        },
        "signal_freq": {
            "type": "slider",
            "label": "Signal Frequency",
            "min": 20,
            "max": 2000,
            "step": 10,
            "default": 440,
            "unit": "Hz",
            "visible_when": {"signal_type": ["sine", "square"]},
        },
        "show_db_scale": {
            "type": "checkbox",
            "label": "Magnitude in dB",
            "default": True,
        },
        "show_phase": {
            "type": "checkbox",
            "label": "Show Phase Response",
            "default": True,
        },
        "gain_K": {
            "type": "slider",
            "label": "System Gain (K)",
            "min": 0.1,
            "max": 10.0,
            "step": 0.1,
            "default": 1.0,
            "unit": "",
        },
    }

    DEFAULT_PARAMS = {
        "mode": "explore",
        "signal_type": "multi_tone",
        "signal_freq": 440,
        "show_db_scale": True,
        "show_phase": True,
        "gain_K": 1.0,
    }

    # Challenge configurations by difficulty
    CHALLENGE_CONFIGS = {
        "easy": [
            {
                "name": "Simple Lowpass",
                "poles": [(-2000 + 0j)],
                "zeros": [],
                "K": 2000.0,
                "hint": "Single real pole in the LHP. Where should it go?",
            },
            {
                "name": "Simple Highpass",
                "poles": [(-2000 + 0j)],
                "zeros": [(0 + 0j)],
                "K": 1.0,
                "hint": "One zero at the origin, one real pole.",
            },
            {
                "name": "Two Real Poles",
                "poles": [(-500 + 0j), (-3000 + 0j)],
                "zeros": [],
                "K": 1500000.0,
                "hint": "Two real poles, no zeros. Low frequencies pass through.",
            },
        ],
        "medium": [
            {
                "name": "2nd Order Lowpass",
                "preset": "lowpass",
                "hint": "Complex conjugate poles, no zeros. Classic Butterworth shape.",
            },
            {
                "name": "Bandpass Filter",
                "preset": "bandpass",
                "hint": "Complex poles with one zero at the origin. Passes a band of frequencies.",
            },
            {
                "name": "2nd Order Highpass",
                "preset": "highpass",
                "hint": "Complex conjugate poles, two zeros at origin.",
            },
        ],
        "hard": [
            {
                "name": "Notch Filter",
                "preset": "notch",
                "hint": "Zeros on the imaginary axis cancel a specific frequency. Poles nearby for sharpness.",
            },
            {
                "name": "Resonant Peak",
                "preset": "resonant",
                "hint": "Very lightly damped complex poles. Huge gain at one frequency.",
            },
            {
                "name": "Allpass Filter",
                "preset": "allpass",
                "hint": "Flat magnitude response! Zeros mirror poles across the jw axis.",
            },
        ],
    }

    def __init__(self, simulation_id: str):
        super().__init__(simulation_id)
        # Pole/zero state
        self._poles: List[complex] = []
        self._zeros: List[complex] = []
        self._placement_mode: str = "pole"

        # Precomputed data
        self._freq_axis: Optional[np.ndarray] = None
        self._magnitude: Optional[np.ndarray] = None
        self._phase: Optional[np.ndarray] = None
        self._time_axis: Optional[np.ndarray] = None
        self._input_signal: Optional[np.ndarray] = None
        self._output_signal: Optional[np.ndarray] = None
        self._freq_spectrum_axis: Optional[np.ndarray] = None
        self._input_spectrum: Optional[np.ndarray] = None
        self._output_spectrum: Optional[np.ndarray] = None

        # System analysis
        self._is_stable: bool = True
        self._has_marginal_poles: bool = False
        self._system_order: int = 0

        # Challenge state
        self._challenge_active: bool = False
        self._challenge_answered: bool = False
        self._challenge_score: Optional[float] = None
        self._challenge_target_poles: List[complex] = []
        self._challenge_target_zeros: List[complex] = []
        self._challenge_target_gain: float = 1.0
        self._challenge_target_magnitude: Optional[np.ndarray] = None
        self._challenge_hint: Optional[str] = None
        self._challenge_filter_name: Optional[str] = None
        self._challenge_difficulty: str = "easy"

        self._error: Optional[str] = None
        self._filter_failed: bool = False

    def initialize(self, params: Optional[Dict[str, Any]] = None) -> None:
        """Initialize simulation with parameters."""
        self.parameters = {**self.DEFAULT_PARAMS, **(params or {})}
        for name, value in self.parameters.items():
            self.parameters[name] = self._validate_param(name, value)
        self._initialized = True
        self._compute()

    def update_parameter(self, name: str, value: Any) -> Dict[str, Any]:
        """Update a single parameter and recompute."""
        if name in self.parameters:
            old_value = self.parameters[name]
            self.parameters[name] = self._validate_param(name, value)

            # Mode switch: auto-trigger challenge generation or cleanup
            if name == "mode":
                if value == "challenge" and not self._challenge_active:
                    self._action_new_challenge({"difficulty": "easy"})
                elif value == "explore":
                    self._challenge_active = False
                    self._challenge_answered = False
                    self._challenge_score = None

        self._compute()
        return self.get_state()

    def reset(self) -> Dict[str, Any]:
        """Reset all state to defaults."""
        self.parameters = self.DEFAULT_PARAMS.copy()
        self._poles = []
        self._zeros = []
        self._placement_mode = "pole"
        self._challenge_active = False
        self._challenge_answered = False
        self._challenge_score = None
        self._challenge_target_poles = []
        self._challenge_target_zeros = []
        self._challenge_target_magnitude = None
        self._challenge_hint = None
        self._challenge_filter_name = None
        self._error = None
        self._filter_failed = False
        self._initialized = True
        self._compute()
        return self.get_state()

    def handle_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle custom interactive actions."""
        action_map = {
            "add_pole": self._action_add_pole,
            "add_zero": self._action_add_zero,
            "remove_pole": self._action_remove_pole,
            "remove_zero": self._action_remove_zero,
            "clear_all": self._action_clear_all,
            "load_preset": self._action_load_preset,
            "set_placement_mode": self._action_set_placement_mode,
            "add_at_click": self._action_add_at_click,
            "new_challenge": self._action_new_challenge,
            "check_answer": self._action_check_answer,
        }

        handler = action_map.get(action)
        if handler is None:
            self._error = f"Unknown action: {action}"
            return self.get_state()

        try:
            self._error = None
            handler(params or {})
        except Exception as e:
            self._error = str(e)

        return self.get_state()

    # =========================================================================
    # Action handlers
    # =========================================================================

    def _action_add_pole(self, params: Dict[str, Any]) -> None:
        """Add a pole (with conjugate pair if complex)."""
        real = float(params.get("real", -1000))
        imag = float(params.get("imag", 0))

        if len(self._poles) >= self.MAX_POLES:
            self._error = f"Maximum {self.MAX_POLES} poles reached"
            return

        if abs(imag) > self.IMAG_THRESHOLD:
            # Complex: add conjugate pair
            if len(self._poles) + 2 > self.MAX_POLES:
                self._error = f"Need 2 slots for conjugate pair, only {self.MAX_POLES - len(self._poles)} left"
                return
            self._poles.append(complex(real, imag))
            self._poles.append(complex(real, -imag))
        else:
            self._poles.append(complex(real, 0))

        self._compute()

    def _action_add_zero(self, params: Dict[str, Any]) -> None:
        """Add a zero (with conjugate pair if complex)."""
        real = float(params.get("real", 0))
        imag = float(params.get("imag", 0))

        if len(self._zeros) >= self.MAX_ZEROS:
            self._error = f"Maximum {self.MAX_ZEROS} zeros reached"
            return

        if abs(imag) > self.IMAG_THRESHOLD:
            if len(self._zeros) + 2 > self.MAX_ZEROS:
                self._error = f"Need 2 slots for conjugate pair, only {self.MAX_ZEROS - len(self._zeros)} left"
                return
            self._zeros.append(complex(real, imag))
            self._zeros.append(complex(real, -imag))
        else:
            self._zeros.append(complex(real, 0))

        self._compute()

    def _action_remove_pole(self, params: Dict[str, Any]) -> None:
        """Remove a pole and its conjugate pair."""
        index = int(params.get("index", -1))
        if index < 0 or index >= len(self._poles):
            self._error = "Invalid pole index"
            return

        pole = self._poles[index]
        self._poles.pop(index)

        # Remove conjugate if it was complex
        if abs(pole.imag) > self.IMAG_THRESHOLD:
            conjugate = complex(pole.real, -pole.imag)
            for i, p in enumerate(self._poles):
                if abs(p - conjugate) < 1e-4:
                    self._poles.pop(i)
                    break

        self._compute()

    def _action_remove_zero(self, params: Dict[str, Any]) -> None:
        """Remove a zero and its conjugate pair."""
        index = int(params.get("index", -1))
        if index < 0 or index >= len(self._zeros):
            self._error = "Invalid zero index"
            return

        zero = self._zeros[index]
        self._zeros.pop(index)

        if abs(zero.imag) > self.IMAG_THRESHOLD:
            conjugate = complex(zero.real, -zero.imag)
            for i, z in enumerate(self._zeros):
                if abs(z - conjugate) < 1e-4:
                    self._zeros.pop(i)
                    break

        self._compute()

    def _action_clear_all(self, params: Dict[str, Any]) -> None:
        """Clear all poles and zeros."""
        self._poles = []
        self._zeros = []
        self._compute()

    def _action_load_preset(self, params: Dict[str, Any]) -> None:
        """Load a preset filter configuration."""
        preset = params.get("preset", "lowpass")
        poles, zeros, K = self._get_preset_config(preset)
        self._poles = list(poles)
        self._zeros = list(zeros)
        self.parameters["gain_K"] = round(K, 4)
        self._compute()

    def _action_set_placement_mode(self, params: Dict[str, Any]) -> None:
        """Switch between pole and zero placement."""
        mode = params.get("mode", "pole")
        if mode in ("pole", "zero"):
            self._placement_mode = mode

    def _action_add_at_click(self, params: Dict[str, Any]) -> None:
        """Add pole or zero based on current placement mode."""
        if self._placement_mode == "pole":
            self._action_add_pole(params)
        else:
            self._action_add_zero(params)

    def _action_new_challenge(self, params: Dict[str, Any]) -> None:
        """Generate a new challenge target filter."""
        difficulty = params.get("difficulty", "easy")
        configs = self.CHALLENGE_CONFIGS.get(difficulty, self.CHALLENGE_CONFIGS["easy"])
        config = random.choice(configs)

        if "preset" in config:
            poles, zeros, K = self._get_preset_config(config["preset"])
        else:
            poles = list(config["poles"])
            zeros = list(config["zeros"])
            K = config["K"]

        # Add random variation (+/- 30%) to prevent memorization
        variation = 0.7 + 0.6 * random.random()
        poles = [p * variation for p in poles]
        zeros = [z * variation for z in zeros if abs(z) > self.IMAG_THRESHOLD]
        # Keep origin zeros exactly at origin
        origin_zeros = [z for z in (config.get("zeros") or zeros) if abs(z) < self.IMAG_THRESHOLD]
        zeros = origin_zeros + zeros

        self._challenge_target_poles = poles
        self._challenge_target_zeros = zeros
        self._challenge_target_gain = K * (variation ** len(poles))
        self._challenge_target_magnitude = self._compute_magnitude_for(
            poles, zeros, self._challenge_target_gain
        )
        self._challenge_active = True
        self._challenge_answered = False
        self._challenge_score = None
        self._challenge_difficulty = difficulty
        self._challenge_hint = config.get("hint")
        self._challenge_filter_name = config["name"]

        # Clear user state
        self._poles = []
        self._zeros = []
        self._compute()

    def _action_check_answer(self, params: Dict[str, Any]) -> None:
        """Compare user's frequency response to target."""
        if not self._challenge_active or self._challenge_answered:
            return

        if self._magnitude is None or self._challenge_target_magnitude is None:
            self._challenge_score = 0
            self._challenge_answered = True
            return

        # Compare in dB domain
        user_db = 20 * np.log10(np.clip(self._magnitude, 1e-10, None))
        target_db = 20 * np.log10(np.clip(self._challenge_target_magnitude, 1e-10, None))

        mse = float(np.mean((user_db - target_db) ** 2))
        score = max(0, min(100, int(100 * np.exp(-mse / 100))))

        self._challenge_score = score
        self._challenge_answered = True
        self._compute()

    # =========================================================================
    # Preset configurations
    # =========================================================================

    def _get_preset_config(self, preset: str):
        """Return (poles, zeros, K) for a named preset."""
        omega_c = 2 * np.pi * self.BASE_FREQ_HZ

        if preset == "lowpass":
            # 2nd order Butterworth lowpass
            p1 = omega_c * np.exp(1j * 3 * np.pi / 4)
            p2 = np.conj(p1)
            K = float(omega_c ** 2)
            return [p1, p2], [], K

        elif preset == "highpass":
            # 2nd order Butterworth highpass
            p1 = omega_c * np.exp(1j * 3 * np.pi / 4)
            p2 = np.conj(p1)
            return [p1, p2], [0 + 0j, 0 + 0j], 1.0

        elif preset == "bandpass":
            # 2nd order bandpass, Q=5
            Q = 5.0
            sigma = omega_c / (2 * Q)
            omega_d = omega_c * np.sqrt(max(0, 1 - 1 / (4 * Q ** 2)))
            p1 = complex(-sigma, omega_d)
            p2 = np.conj(p1)
            K = float(omega_c / Q)
            return [p1, p2], [0 + 0j], K

        elif preset == "notch":
            # 2nd order notch at omega_c, Q=10
            Q = 10.0
            sigma = omega_c / (2 * Q)
            omega_d = omega_c * np.sqrt(max(0, 1 - 1 / (4 * Q ** 2)))
            p1 = complex(-sigma, omega_d)
            p2 = np.conj(p1)
            z1 = complex(0, omega_c)
            z2 = complex(0, -omega_c)
            return [p1, p2], [z1, z2], 1.0

        elif preset == "resonant":
            # Highly resonant, Q=50
            Q = 50.0
            sigma = omega_c / (2 * Q)
            omega_d = omega_c * np.sqrt(max(0, 1 - 1 / (4 * Q ** 2)))
            p1 = complex(-sigma, omega_d)
            p2 = np.conj(p1)
            K = float(omega_c ** 2)
            return [p1, p2], [], K

        elif preset == "allpass":
            # 2nd order allpass
            Q = 5.0
            sigma = omega_c / (2 * Q)
            omega_d = omega_c * np.sqrt(max(0, 1 - 1 / (4 * Q ** 2)))
            p1 = complex(-sigma, omega_d)
            p2 = np.conj(p1)
            z1 = complex(sigma, omega_d)
            z2 = np.conj(z1)
            return [p1, p2], [z1, z2], 1.0

        else:
            return [], [], 1.0

    # =========================================================================
    # Computation pipeline
    # =========================================================================

    def _compute(self) -> None:
        """Recompute everything from current state."""
        self._analyze_stability()
        self._compute_frequency_response()
        self._generate_signal()
        self._filter_signal()
        self._compute_spectra()

    def _analyze_stability(self) -> None:
        """Check system stability."""
        if not self._poles:
            self._is_stable = True
            self._has_marginal_poles = False
            self._system_order = 0
            return

        self._system_order = len(self._poles)
        self._is_stable = all(p.real < 0 for p in self._poles)
        self._has_marginal_poles = any(
            abs(p.real) < 1e-4 and abs(p.imag) > self.IMAG_THRESHOLD
            for p in self._poles
        )

    def _compute_frequency_response(self) -> None:
        """Compute H(jw) = K * prod(jw - z_i) / prod(jw - p_i)."""
        freq_hz = np.logspace(
            np.log10(self.FREQ_MIN_HZ),
            np.log10(self.FREQ_MAX_HZ),
            self.NUM_FREQ_POINTS,
        )
        self._freq_axis = freq_hz
        omega = 2 * np.pi * freq_hz
        K = float(self.parameters.get("gain_K", 1.0))

        if not self._poles and not self._zeros:
            self._magnitude = np.full_like(omega, abs(K))
            self._phase = np.zeros_like(omega)
            return

        s = 1j * omega

        numerator = np.ones_like(s, dtype=complex)
        for z in self._zeros:
            numerator *= (s - z)

        denominator = np.ones_like(s, dtype=complex)
        for p in self._poles:
            denominator *= (s - p)

        # Clamp denominator to avoid division by zero
        denom_mag = np.abs(denominator)
        denominator = np.where(denom_mag < 1e-12, 1e-12, denominator)

        H = K * numerator / denominator
        self._magnitude = np.abs(H)
        # Unwrap phase for cleaner display
        self._phase = np.rad2deg(np.unwrap(np.angle(H)))

    def _compute_magnitude_for(
        self, poles: List[complex], zeros: List[complex], K: float
    ) -> np.ndarray:
        """Compute magnitude response for arbitrary poles/zeros (for challenge targets)."""
        freq_hz = np.logspace(
            np.log10(self.FREQ_MIN_HZ),
            np.log10(self.FREQ_MAX_HZ),
            self.NUM_FREQ_POINTS,
        )
        omega = 2 * np.pi * freq_hz
        s = 1j * omega

        numerator = np.ones_like(s, dtype=complex)
        for z in zeros:
            numerator *= (s - z)

        denominator = np.ones_like(s, dtype=complex)
        for p in poles:
            denominator *= (s - p)

        denom_mag = np.abs(denominator)
        denominator = np.where(denom_mag < 1e-12, 1e-12, denominator)

        H = K * numerator / denominator
        return np.abs(H)

    def _generate_signal(self) -> None:
        """Generate test input signal."""
        duration = 0.2  # Fixed 200ms for display clarity
        sr = self.SAMPLE_RATE
        N = int(duration * sr)
        self._time_axis = np.linspace(0, duration, N, endpoint=False)
        t = self._time_axis
        sig_type = self.parameters.get("signal_type", "multi_tone")

        if sig_type == "sine":
            freq = float(self.parameters.get("signal_freq", 440))
            self._input_signal = np.sin(2 * np.pi * freq * t)

        elif sig_type == "multi_tone":
            self._input_signal = (
                np.sin(2 * np.pi * 200 * t)
                + 0.7 * np.sin(2 * np.pi * 800 * t)
                + 0.5 * np.sin(2 * np.pi * 2000 * t)
            ) / 2.2

        elif sig_type == "chirp":
            self._input_signal = scipy_chirp(
                t, f0=20, f1=4000, t1=duration, method="logarithmic"
            )

        elif sig_type == "square":
            freq = float(self.parameters.get("signal_freq", 440))
            self._input_signal = np.sign(np.sin(2 * np.pi * freq * t))

        elif sig_type == "white_noise":
            rng = np.random.default_rng(42)
            self._input_signal = rng.standard_normal(N) * 0.5

        else:
            self._input_signal = np.sin(2 * np.pi * 440 * t)

    def _filter_signal(self) -> None:
        """Apply H(s) to the input signal via scipy.signal.lsim."""
        self._filter_failed = False

        if self._input_signal is None:
            return

        K = float(self.parameters.get("gain_K", 1.0))

        if not self._poles and not self._zeros:
            self._output_signal = K * self._input_signal
            return

        try:
            z_array = np.array(self._zeros) if self._zeros else np.array([])
            p_array = np.array(self._poles) if self._poles else np.array([])

            num, den = zpk2tf(z_array, p_array, K)

            # Ensure real coefficients
            num = np.real(num)
            den = np.real(den)

            # Check for extremely large coefficients
            if np.any(np.abs(num) > 1e18) or np.any(np.abs(den) > 1e18):
                self._output_signal = self._input_signal.copy()
                self._filter_failed = True
                self._error = "System coefficients too large for time-domain simulation"
                return

            system = lti(num, den)
            _, y_out, _ = lsim(system, U=self._input_signal, T=self._time_axis)
            self._output_signal = np.real(y_out)

            # Clamp for unstable systems
            max_val = float(np.max(np.abs(self._input_signal))) * 100
            if max_val > 0:
                self._output_signal = np.clip(self._output_signal, -max_val, max_val)

        except Exception:
            self._output_signal = self._input_signal.copy()
            self._filter_failed = True

    def _compute_spectra(self) -> None:
        """Compute FFT of input and output signals."""
        if self._input_signal is None:
            return

        N = len(self._input_signal)
        sr = self.SAMPLE_RATE
        window = np.hanning(N)

        X = np.fft.rfft(self._input_signal * window)
        self._input_spectrum = 2.0 / N * np.abs(X)

        if self._output_signal is not None:
            Y = np.fft.rfft(self._output_signal * window)
            self._output_spectrum = 2.0 / N * np.abs(Y)
        else:
            self._output_spectrum = self._input_spectrum.copy()

        self._freq_spectrum_axis = np.fft.rfftfreq(N, 1.0 / sr)

    # =========================================================================
    # Transfer function formatting
    # =========================================================================

    def _format_transfer_function(self) -> str:
        """Build a human-readable H(s) expression."""
        K = self.parameters.get("gain_K", 1.0)

        if not self._poles and not self._zeros:
            return f"H(s) = {K:.2g}"

        def format_factor(root: complex) -> str:
            if abs(root.imag) < self.IMAG_THRESHOLD:
                if abs(root.real) < 1e-4:
                    return "s"
                elif root.real > 0:
                    return f"(s - {root.real:.0f})"
                else:
                    return f"(s + {abs(root.real):.0f})"
            else:
                # Quadratic factor for conjugate pair
                sigma = -root.real
                omega_sq = root.real ** 2 + root.imag ** 2
                if abs(sigma) < 1:
                    return f"(s\u00b2 + {omega_sq:.0f})"
                return f"(s\u00b2 + {2*sigma:.0f}s + {omega_sq:.0f})"

        # Build numerator from unique zeros (skip conjugates)
        num_parts = []
        seen_zeros = set()
        for z in self._zeros:
            key = (round(z.real, 2), round(abs(z.imag), 2))
            if key not in seen_zeros:
                seen_zeros.add(key)
                num_parts.append(format_factor(z))

        # Build denominator from unique poles
        den_parts = []
        seen_poles = set()
        for p in self._poles:
            key = (round(p.real, 2), round(abs(p.imag), 2))
            if key not in seen_poles:
                seen_poles.add(key)
                den_parts.append(format_factor(p))

        num_str = " ".join(num_parts) if num_parts else "1"
        den_str = " ".join(den_parts) if den_parts else "1"

        k_str = f"{K:.2g} " if abs(K - 1.0) > 0.01 else ""

        if den_str == "1":
            return f"H(s) = {k_str}{num_str}"
        if num_str == "1":
            return f"H(s) = {k_str}/ {den_str}"
        return f"H(s) = {k_str}{num_str} / {den_str}"

    def _classify_filter(self) -> str:
        """Classify the filter type from the magnitude response shape."""
        if self._magnitude is None or len(self._magnitude) < 10:
            return "custom"

        mag = self._magnitude
        low_avg = float(np.mean(mag[:50]))       # ~1-4 Hz
        mid_avg = float(np.mean(mag[400:600]))    # ~100-1000 Hz
        high_avg = float(np.mean(mag[-50:]))      # ~6000-10000 Hz
        peak_mag = float(np.max(mag))
        min_mag = float(np.min(mag))

        if not self._poles and not self._zeros:
            return "flat"

        # Avoid division by zero
        safe_low = max(low_avg, 1e-12)
        safe_high = max(high_avg, 1e-12)
        safe_mid = max(mid_avg, 1e-12)
        edge_max = max(safe_low, safe_high)

        # 1. Notch: deep dip while edges stay high (check BEFORE allpass)
        if edge_max > 1e-6 and min_mag < 0.1 * edge_max and low_avg > 0.3 * edge_max and high_avg > 0.3 * edge_max:
            return "notch"

        # 2. Allpass: flat magnitude across all frequencies, no deep dips
        if safe_low > 1e-6 and abs(safe_high / safe_low - 1) < 0.15 and abs(safe_mid / safe_low - 1) < 0.15 and min_mag > 0.5 * safe_low:
            return "allpass"

        # 3. Bandpass: peak in the middle, both edges lower
        if mid_avg > 3 * safe_low and mid_avg > 3 * safe_high:
            return "bandpass"

        # 4. Resonant: very sharp peak relative to both edges
        if peak_mag > 5 * safe_low and peak_mag > 5 * safe_high and peak_mag > 3 * safe_mid:
            return "resonant"

        # 5. Lowpass: high at DC, low at high frequencies
        if low_avg > 3 * safe_high:
            return "lowpass"

        # 6. Highpass: low at DC, high at high frequencies
        if high_avg > 3 * safe_low:
            return "highpass"

        return "custom"

    # =========================================================================
    # Plot generation
    # =========================================================================

    def get_plots(self) -> List[Dict[str, Any]]:
        """Generate all plots."""
        if not self._initialized:
            self.initialize()

        plots = [
            self._create_s_plane_plot(),
            self._create_magnitude_plot(),
        ]

        if self.parameters.get("show_phase", True):
            plots.append(self._create_phase_plot())

        plots.append(self._create_time_domain_plot())
        plots.append(self._create_spectrum_plot())

        return plots

    def _build_layout(self, **overrides) -> Dict[str, Any]:
        """Base layout for all Plotly plots."""
        layout = {
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "font": {"family": "Inter, sans-serif", "size": 12, "color": self.COLORS["text"]},
            "margin": {"t": 45, "r": 25, "b": 55, "l": 65},
            "showlegend": True,
            "legend": {
                "font": {"color": self.COLORS["text_secondary"], "size": 11},
                "bgcolor": "rgba(15, 23, 42, 0.8)",
                "bordercolor": "rgba(148, 163, 184, 0.2)",
                "borderwidth": 1,
            },
        }
        layout.update(overrides)
        return layout

    def _create_s_plane_plot(self) -> Dict[str, Any]:
        """S-plane pole-zero map."""
        # Determine range from current poles/zeros
        all_pz = self._poles + self._zeros
        if all_pz:
            max_val = max(max(abs(c.real), abs(c.imag)) for c in all_pz)
            plot_range = max(max_val * 1.5, 1000)
        else:
            plot_range = 5000

        traces = []

        # Stable region fill
        traces.append({
            "x": [-plot_range, 0, 0, -plot_range, -plot_range],
            "y": [-plot_range, -plot_range, plot_range, plot_range, -plot_range],
            "type": "scatter",
            "mode": "lines",
            "fill": "toself",
            "fillcolor": self.COLORS["stable_fill"],
            "line": {"color": "rgba(52, 211, 153, 0.3)", "width": 1},
            "name": "Stable Region (Re < 0)",
            "hoverinfo": "skip",
            "showlegend": True,
        })

        # jw axis
        traces.append({
            "x": [0, 0],
            "y": [-plot_range, plot_range],
            "type": "scatter",
            "mode": "lines",
            "line": {"color": self.COLORS["jw_axis"], "width": 2, "dash": "dash"},
            "name": "j\u03c9 axis",
            "hoverinfo": "name",
        })

        # Poles
        if self._poles:
            pole_x = [float(p.real) for p in self._poles]
            pole_y = [float(p.imag) for p in self._poles]
            hover = [
                f"Pole {i+1}<br>\u03c3 = {p.real:.1f}<br>\u03c9 = {p.imag:.1f}"
                for i, p in enumerate(self._poles)
            ]
            traces.append({
                "x": pole_x,
                "y": pole_y,
                "type": "scatter",
                "mode": "markers",
                "name": f"Poles ({len(self._poles)})",
                "marker": {
                    "symbol": "x",
                    "size": 14,
                    "color": self.COLORS["pole"],
                    "line": {"width": 3, "color": self.COLORS["pole"]},
                },
                "hovertext": hover,
                "hoverinfo": "text",
            })

        # Zeros
        if self._zeros:
            zero_x = [float(z.real) for z in self._zeros]
            zero_y = [float(z.imag) for z in self._zeros]
            hover = [
                f"Zero {i+1}<br>\u03c3 = {z.real:.1f}<br>\u03c9 = {z.imag:.1f}"
                for i, z in enumerate(self._zeros)
            ]
            traces.append({
                "x": zero_x,
                "y": zero_y,
                "type": "scatter",
                "mode": "markers",
                "name": f"Zeros ({len(self._zeros)})",
                "marker": {
                    "symbol": "circle-open",
                    "size": 14,
                    "color": self.COLORS["zero"],
                    "line": {"width": 3, "color": self.COLORS["zero"]},
                },
                "hovertext": hover,
                "hoverinfo": "text",
            })

        # Challenge target (only after answered)
        if self._challenge_active and self._challenge_answered:
            if self._challenge_target_poles:
                traces.append({
                    "x": [float(p.real) for p in self._challenge_target_poles],
                    "y": [float(p.imag) for p in self._challenge_target_poles],
                    "type": "scatter",
                    "mode": "markers",
                    "name": "Target Poles",
                    "marker": {
                        "symbol": "x",
                        "size": 12,
                        "color": self.COLORS["target"],
                        "line": {"width": 2, "color": self.COLORS["target"]},
                    },
                    "opacity": 0.7,
                })
            if self._challenge_target_zeros:
                traces.append({
                    "x": [float(z.real) for z in self._challenge_target_zeros],
                    "y": [float(z.imag) for z in self._challenge_target_zeros],
                    "type": "scatter",
                    "mode": "markers",
                    "name": "Target Zeros",
                    "marker": {
                        "symbol": "circle-open",
                        "size": 12,
                        "color": self.COLORS["target"],
                        "line": {"width": 2, "color": self.COLORS["target"]},
                    },
                    "opacity": 0.7,
                })

        # Fingerprint for uirevision
        pz_fingerprint = (
            f"s_plane-{len(self._poles)}-{len(self._zeros)}"
            f"-{sum(hash(p) for p in self._poles)}"
        )

        return {
            "id": "s_plane",
            "title": f"S-Plane | Order: {self._system_order}",
            "data": traces,
            "layout": self._build_layout(
                xaxis={
                    "title": "Real (\u03c3)",
                    "showgrid": True,
                    "gridcolor": self.COLORS["grid"],
                    "zeroline": True,
                    "zerolinecolor": "rgba(148,163,184,0.3)",
                    "range": [-plot_range, plot_range * 0.5],
                    "fixedrange": False,
                },
                yaxis={
                    "title": "Imaginary (\u03c9)",
                    "showgrid": True,
                    "gridcolor": self.COLORS["grid"],
                    "zeroline": True,
                    "zerolinecolor": "rgba(148,163,184,0.3)",
                    "range": [-plot_range, plot_range],
                    "scaleanchor": "x",
                    "scaleratio": 1,
                    "constrain": "domain",
                    "fixedrange": False,
                },
                uirevision=pz_fingerprint,
            ),
        }

    def _create_magnitude_plot(self) -> Dict[str, Any]:
        """Magnitude response |H(jw)|."""
        show_db = self.parameters.get("show_db_scale", True)

        traces = []

        if self._magnitude is not None and self._freq_axis is not None:
            if show_db:
                y_data = 20 * np.log10(np.clip(self._magnitude, 1e-10, None))
                y_label = "|H(j\u03c9)| (dB)"
            else:
                y_data = self._magnitude
                y_label = "|H(j\u03c9)|"

            traces.append({
                "x": self._freq_axis.tolist(),
                "y": np.nan_to_num(y_data, nan=0, posinf=60, neginf=-60).tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": "|H(j\u03c9)|",
                "line": {"color": self.COLORS["magnitude"], "width": 3},
            })

        # Challenge target overlay
        if (
            self._challenge_active
            and self._challenge_target_magnitude is not None
            and self._freq_axis is not None
        ):
            if show_db:
                target_y = 20 * np.log10(
                    np.clip(self._challenge_target_magnitude, 1e-10, None)
                )
            else:
                target_y = self._challenge_target_magnitude

            traces.append({
                "x": self._freq_axis.tolist(),
                "y": np.nan_to_num(target_y, nan=0, posinf=60, neginf=-60).tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": "Target",
                "line": {"color": self.COLORS["target"], "width": 2, "dash": "dot"},
            })

        # Reference lines (dB mode)
        if show_db:
            traces.append({
                "x": [self.FREQ_MIN_HZ, self.FREQ_MAX_HZ],
                "y": [0, 0],
                "type": "scatter",
                "mode": "lines",
                "name": "0 dB",
                "line": {"color": "rgba(148,163,184,0.3)", "width": 1, "dash": "dash"},
                "showlegend": False,
            })
            traces.append({
                "x": [self.FREQ_MIN_HZ, self.FREQ_MAX_HZ],
                "y": [-3, -3],
                "type": "scatter",
                "mode": "lines",
                "name": "-3 dB",
                "line": {"color": self.COLORS["reference"], "width": 1, "dash": "dash"},
            })

        y_axis_config = {
            "title": "|H(j\u03c9)| (dB)" if show_db else "|H(j\u03c9)|",
            "showgrid": True,
            "gridcolor": self.COLORS["grid"],
            "zeroline": True,
            "zerolinecolor": "rgba(148,163,184,0.3)",
        }
        if show_db:
            y_axis_config["range"] = [-60, 40]

        pz_fp = f"mag-{len(self._poles)}-{len(self._zeros)}-{hash(tuple(self._poles + self._zeros)) if (self._poles or self._zeros) else 0}"

        return {
            "id": "magnitude_response",
            "title": "Magnitude Response",
            "data": traces,
            "layout": self._build_layout(
                xaxis={
                    "title": "Frequency (Hz)",
                    "type": "log",
                    "showgrid": True,
                    "gridcolor": self.COLORS["grid"],
                    "range": [np.log10(self.FREQ_MIN_HZ), np.log10(self.FREQ_MAX_HZ)],
                    "fixedrange": False,
                },
                yaxis=y_axis_config,
                uirevision=pz_fp,
            ),
        }

    def _create_phase_plot(self) -> Dict[str, Any]:
        """Phase response angle(H(jw))."""
        traces = []

        if self._phase is not None and self._freq_axis is not None:
            traces.append({
                "x": self._freq_axis.tolist(),
                "y": np.nan_to_num(self._phase, nan=0).tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": "\u2220H(j\u03c9)",
                "line": {"color": self.COLORS["phase"], "width": 2.5},
            })

        # Challenge target phase
        if (
            self._challenge_active
            and self._challenge_target_magnitude is not None
            and self._freq_axis is not None
        ):
            # Recompute target phase
            omega = 2 * np.pi * self._freq_axis
            s = 1j * omega
            K = self._challenge_target_gain
            num = np.ones_like(s, dtype=complex)
            for z in self._challenge_target_zeros:
                num *= (s - z)
            den = np.ones_like(s, dtype=complex)
            for p in self._challenge_target_poles:
                den *= (s - p)
            den_mag = np.abs(den)
            den = np.where(den_mag < 1e-12, 1e-12, den)
            H_target = K * num / den
            target_phase = np.rad2deg(np.unwrap(np.angle(H_target)))

            traces.append({
                "x": self._freq_axis.tolist(),
                "y": np.nan_to_num(target_phase, nan=0).tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": "Target Phase",
                "line": {"color": self.COLORS["target"], "width": 2, "dash": "dot"},
            })

        # 0-degree reference
        traces.append({
            "x": [self.FREQ_MIN_HZ, self.FREQ_MAX_HZ],
            "y": [0, 0],
            "type": "scatter",
            "mode": "lines",
            "line": {"color": "rgba(148,163,184,0.3)", "width": 1, "dash": "dash"},
            "showlegend": False,
        })

        return {
            "id": "phase_response",
            "title": "Phase Response",
            "data": traces,
            "layout": self._build_layout(
                xaxis={
                    "title": "Frequency (Hz)",
                    "type": "log",
                    "showgrid": True,
                    "gridcolor": self.COLORS["grid"],
                    "range": [np.log10(self.FREQ_MIN_HZ), np.log10(self.FREQ_MAX_HZ)],
                    "fixedrange": False,
                },
                yaxis={
                    "title": "Phase (degrees)",
                    "showgrid": True,
                    "gridcolor": self.COLORS["grid"],
                    "zeroline": True,
                    "zerolinecolor": "rgba(148,163,184,0.3)",
                    "autorange": True,
                    "fixedrange": False,
                },
                uirevision="phase",
            ),
        }

    def _create_time_domain_plot(self) -> Dict[str, Any]:
        """Input vs output in time domain."""
        traces = []

        if self._time_axis is not None and self._input_signal is not None:
            # Show time in milliseconds
            t_ms = (self._time_axis * 1000).tolist()

            # Subsample for performance (max 2000 points)
            step = max(1, len(t_ms) // 2000)
            t_sub = t_ms[::step]
            input_sub = self._input_signal[::step].tolist()

            traces.append({
                "x": t_sub,
                "y": input_sub,
                "type": "scatter",
                "mode": "lines",
                "name": "Input x(t)",
                "line": {"color": self.COLORS["input"], "width": 2},
            })

            if self._output_signal is not None:
                output_sub = np.nan_to_num(self._output_signal[::step], nan=0).tolist()
                traces.append({
                    "x": t_sub,
                    "y": output_sub,
                    "type": "scatter",
                    "mode": "lines",
                    "name": "Output y(t)",
                    "line": {"color": self.COLORS["output"], "width": 2},
                })

        annotations = []
        if self._filter_failed:
            annotations.append({
                "x": 0.5, "y": 0.95,
                "xref": "paper", "yref": "paper",
                "text": "<b>Filter computation failed</b>",
                "showarrow": False,
                "font": {"color": self.COLORS["output"], "size": 11},
                "bgcolor": "rgba(15,23,42,0.9)",
                "bordercolor": self.COLORS["output"],
                "borderwidth": 1,
                "borderpad": 4,
            })
        elif not self._is_stable and self._poles:
            annotations.append({
                "x": 0.5, "y": 0.95,
                "xref": "paper", "yref": "paper",
                "text": "<b>UNSTABLE: Output may diverge</b>",
                "showarrow": False,
                "font": {"color": self.COLORS["output"], "size": 11},
                "bgcolor": "rgba(15,23,42,0.9)",
                "bordercolor": self.COLORS["output"],
                "borderwidth": 1,
                "borderpad": 4,
            })

        return {
            "id": "time_domain",
            "title": "Time Domain",
            "data": traces,
            "layout": self._build_layout(
                xaxis={
                    "title": "Time (ms)",
                    "showgrid": True,
                    "gridcolor": self.COLORS["grid"],
                    "fixedrange": False,
                },
                yaxis={
                    "title": "Amplitude",
                    "showgrid": True,
                    "gridcolor": self.COLORS["grid"],
                    "zeroline": True,
                    "zerolinecolor": "rgba(148,163,184,0.3)",
                    "autorange": True,
                    "fixedrange": False,
                },
                annotations=annotations,
                uirevision="time_domain",
            ),
        }

    def _create_spectrum_plot(self) -> Dict[str, Any]:
        """Frequency spectra of input and output."""
        traces = []

        if self._freq_spectrum_axis is not None and self._input_spectrum is not None:
            # Only show positive frequencies up to Nyquist/2 for clarity
            max_freq_idx = np.searchsorted(self._freq_spectrum_axis, 8000)
            min_freq_idx = np.searchsorted(self._freq_spectrum_axis, 20)
            freq_slice = slice(min_freq_idx, max_freq_idx)

            freq_hz = self._freq_spectrum_axis[freq_slice].tolist()
            input_mag = self._input_spectrum[freq_slice].tolist()

            traces.append({
                "x": freq_hz,
                "y": input_mag,
                "type": "scatter",
                "mode": "lines",
                "name": "|X(f)| Input",
                "line": {"color": self.COLORS["input"], "width": 2},
            })

            if self._output_spectrum is not None:
                output_mag = np.nan_to_num(
                    self._output_spectrum[freq_slice], nan=0
                ).tolist()
                traces.append({
                    "x": freq_hz,
                    "y": output_mag,
                    "type": "scatter",
                    "mode": "lines",
                    "name": "|Y(f)| Output",
                    "line": {"color": self.COLORS["output"], "width": 2},
                })

        return {
            "id": "spectrum",
            "title": "Frequency Spectrum",
            "data": traces,
            "layout": self._build_layout(
                xaxis={
                    "title": "Frequency (Hz)",
                    "type": "log",
                    "showgrid": True,
                    "gridcolor": self.COLORS["grid"],
                    "range": [np.log10(20), np.log10(8000)],
                    "fixedrange": False,
                },
                yaxis={
                    "title": "Magnitude",
                    "showgrid": True,
                    "gridcolor": self.COLORS["grid"],
                    "autorange": True,
                    "fixedrange": False,
                },
                uirevision="spectrum",
            ),
        }

    # =========================================================================
    # State
    # =========================================================================

    def get_state(self) -> Dict[str, Any]:
        """Return complete simulation state."""
        if not self._initialized:
            self.initialize()

        state = {
            "parameters": self.parameters.copy(),
            "plots": self.get_plots(),
            "metadata": {
                "simulation_type": "audio_freq_response",
                "sticky_controls": True,

                # Pole/zero data
                "poles": [
                    {"real": round(p.real, 2), "imag": round(p.imag, 2), "index": i}
                    for i, p in enumerate(self._poles)
                ],
                "zeros": [
                    {"real": round(z.real, 2), "imag": round(z.imag, 2), "index": i}
                    for i, z in enumerate(self._zeros)
                ],
                "gain_K": round(float(self.parameters.get("gain_K", 1.0)), 4),

                # System info
                "system_order": self._system_order,
                "is_stable": self._is_stable,
                "has_marginal_poles": self._has_marginal_poles,
                "num_poles": len(self._poles),
                "num_zeros": len(self._zeros),
                "filter_type": self._classify_filter(),
                "tf_expression": self._format_transfer_function(),

                # Interaction state
                "placement_mode": self._placement_mode,
                "error": self._error,
                "filter_failed": self._filter_failed,

                # Presets
                "presets": ["lowpass", "highpass", "bandpass", "notch", "resonant", "allpass"],

                # Challenge
                "challenge": {
                    "active": self._challenge_active,
                    "answered": self._challenge_answered,
                    "score": self._challenge_score,
                    "difficulty": self._challenge_difficulty,
                    "hint": self._challenge_hint,
                    "filter_name": self._challenge_filter_name,
                    "target_poles": (
                        [{"real": round(p.real, 2), "imag": round(p.imag, 2)}
                         for p in self._challenge_target_poles]
                        if self._challenge_answered else None
                    ),
                    "target_zeros": (
                        [{"real": round(z.real, 2), "imag": round(z.imag, 2)}
                         for z in self._challenge_target_zeros]
                        if self._challenge_answered else None
                    ),
                } if self._challenge_active else None,
            },
        }

        return state
