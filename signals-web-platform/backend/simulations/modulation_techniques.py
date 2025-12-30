"""
Modulation Techniques Simulator - Web Version

Matches the PyQt5 desktop version exactly with:
- Real audio file support
- Three demo tabs: AM, FM/PM, FDM
- Audio playback (base64 encoded WAV)
- Matching controls and visualization

Based on: modulation_techniques/gui/demos/am.py, fm.py, fdm.py
"""

import numpy as np
import scipy.signal as signal
from scipy.io import wavfile
from typing import Any, Dict, List, Optional
import io
import base64
import os
from .base_simulator import BaseSimulator


class ModulationTechniquesSimulator(BaseSimulator):
    """
    Modulation Techniques simulation matching PyQt5 version.

    Three demo modes:
    - AM: Amplitude Modulation (DSB-SC, AM+Carrier, Envelope)
    - FM/PM: Frequency and Phase Modulation
    - FDM: Frequency Division Multiplexing
    """

    # Configuration matching PyQt5
    SAMPLE_RATE = 44100
    AM_DURATION = 2.5  # seconds
    FM_DURATION = 2.5
    FDM_DURATION = 3.0
    DISPLAY_SAMPLES = 2000  # Samples to show in time domain plots

    # Colors matching PyQt5 COLORS dict
    COLORS = {
        "bg": "#F9FAFB",
        "panel": "#FFFFFF",
        "accent": "#2563EB",      # Blue
        "accent_dark": "#1D4ED8",
        "success": "#16A34A",      # Green
        "warning": "#CA8A04",      # Orange/Amber
        "danger": "#DC2626",       # Red
        "text_primary": "#0F172A",
        "text_secondary": "#475569",
        "grid": "#D1D5DB",
        "purple": "#8b5cf6",
    }

    # Parameter schema - defines all controls
    PARAMETER_SCHEMA = {
        "demo_mode": {
            "type": "select",
            "label": "Demo Mode",
            "options": [
                {"value": "am", "label": "Amplitude Modulation"},
                {"value": "fm_pm", "label": "Frequency & Phase Modulation"},
                {"value": "fdm", "label": "Frequency Division Multiplexing"},
            ],
            "default": "am",
            "group": "Mode",
        },
        # AM Controls
        "am_carrier_freq": {
            "type": "slider",
            "label": "Carrier Frequency",
            "min": 1,
            "max": 20,
            "step": 1,
            "default": 5,
            "unit": "kHz",
            "group": "AM Controls",
        },
        "am_carrier_dc": {
            "type": "slider",
            "label": "Carrier DC Offset",
            "min": 0.0,
            "max": 2.0,
            "step": 0.1,
            "default": 1.2,
            "unit": "",
            "group": "AM Controls",
        },
        "am_mode": {
            "type": "select",
            "label": "AM Mode",
            "options": [
                {"value": "dsb_sc", "label": "DSB-SC"},
                {"value": "am_carrier", "label": "AM+Carrier"},
                {"value": "envelope", "label": "Envelope"},
            ],
            "default": "dsb_sc",
            "group": "AM Controls",
        },
        # FM/PM Controls
        "fm_carrier_freq": {
            "type": "slider",
            "label": "Carrier Frequency",
            "min": 5,
            "max": 25,
            "step": 1,
            "default": 10,
            "unit": "kHz",
            "group": "FM/PM Controls",
        },
        "fm_deviation": {
            "type": "slider",
            "label": "Frequency Deviation (FM)",
            "min": 50,
            "max": 5000,
            "step": 50,
            "default": 1200,
            "unit": "Hz",
            "group": "FM/PM Controls",
        },
        "pm_sensitivity": {
            "type": "slider",
            "label": "Phase Sensitivity (PM)",
            "min": 0.2,
            "max": 10.0,
            "step": 0.1,
            "default": 1.2,
            "unit": "rad",
            "group": "FM/PM Controls",
        },
        "fm_pm_mode": {
            "type": "select",
            "label": "Modulation Type",
            "options": [
                {"value": "fm", "label": "FM (Frequency)"},
                {"value": "pm", "label": "PM (Phase)"},
            ],
            "default": "fm",
            "group": "FM/PM Controls",
        },
        # FDM Controls
        "fdm_channels": {
            "type": "slider",
            "label": "Number of Channels",
            "min": 1,
            "max": 5,
            "step": 1,
            "default": 3,
            "unit": "",
            "group": "FDM Controls",
        },
        "fdm_demod_channel": {
            "type": "slider",
            "label": "Demodulate Channel",
            "min": 1,
            "max": 5,
            "step": 1,
            "default": 1,
            "unit": "",
            "group": "FDM Controls",
        },
        "fdm_spacing": {
            "type": "slider",
            "label": "Channel Spacing",
            "min": 5,
            "max": 30,
            "step": 1,
            "default": 10,
            "unit": "kHz",
            "group": "FDM Controls",
        },
    }

    DEFAULT_PARAMS = {
        "demo_mode": "am",
        # AM
        "am_carrier_freq": 5,
        "am_carrier_dc": 1.2,
        "am_mode": "dsb_sc",
        # FM/PM
        "fm_carrier_freq": 10,
        "fm_deviation": 1200,
        "pm_sensitivity": 1.2,
        "fm_pm_mode": "fm",
        # FDM
        "fdm_channels": 3,
        "fdm_demod_channel": 1,
        "fdm_spacing": 10,
    }

    def __init__(self, simulation_id: str):
        super().__init__(simulation_id)
        self._audio = None
        self._time = None
        self._original_sr = self.SAMPLE_RATE

        # AM state
        self._am_modulated = None
        self._am_recovered = None

        # FM/PM state
        self._fm_modulated = None
        self._fm_recovered = None
        self._fm_inst_freq = None

        # FDM state
        self._fdm_multiplexed = None
        self._fdm_demodulated = None
        self._fdm_carrier_freqs = []

    def initialize(self, params: Optional[Dict[str, Any]] = None) -> None:
        """Initialize simulation with parameters."""
        self.parameters = self.DEFAULT_PARAMS.copy()
        if params:
            for name, value in params.items():
                if name in self.parameters:
                    self.parameters[name] = self._validate_param(name, value)

        self._load_audio()
        self._initialized = True
        self._compute()

    def _load_audio(self) -> None:
        """Load audio file from assets."""
        audio_path = os.path.join(
            os.path.dirname(__file__),
            "..", "assets", "audio_sample.wav"
        )

        try:
            if os.path.exists(audio_path):
                sr, audio = wavfile.read(audio_path)
                self._original_sr = sr

                # Convert to float64 normalized to [-1, 1]
                if audio.dtype == np.int16:
                    audio = audio.astype(np.float64) / 32768.0
                elif audio.dtype == np.int32:
                    audio = audio.astype(np.float64) / 2147483648.0
                elif audio.dtype == np.uint8:
                    audio = (audio.astype(np.float64) - 128) / 128.0
                else:
                    audio = audio.astype(np.float64)

                # Convert stereo to mono
                if len(audio.shape) > 1:
                    audio = np.mean(audio, axis=1)

                self._audio = audio
            else:
                # Generate synthetic audio if file not found
                self._generate_synthetic_audio()
        except Exception as e:
            print(f"Error loading audio: {e}")
            self._generate_synthetic_audio()

    def _generate_synthetic_audio(self) -> None:
        """Generate synthetic audio signal."""
        duration = 3.0
        t = np.linspace(0, duration, int(self._original_sr * duration))
        # Composite tone: A4 + A5
        self._audio = 0.3 * np.sin(2 * np.pi * 440 * t) + 0.2 * np.sin(2 * np.pi * 880 * t)

    def update_parameter(self, name: str, value: Any) -> Dict[str, Any]:
        """Update a single parameter and recompute."""
        if name in self.parameters:
            self.parameters[name] = self._validate_param(name, value)
            self._compute()
        return self.get_state()

    def reset(self) -> Dict[str, Any]:
        """Reset simulation to default parameters."""
        self.parameters = self.DEFAULT_PARAMS.copy()
        self._initialized = True
        self._compute()
        return self.get_state()

    def _compute(self) -> None:
        """Compute based on current demo mode."""
        demo_mode = self.parameters["demo_mode"]

        if demo_mode == "am":
            self._compute_am()
        elif demo_mode == "fm_pm":
            self._compute_fm_pm()
        elif demo_mode == "fdm":
            self._compute_fdm()

    # =========================================================================
    # AM Computation (matching am.py)
    # =========================================================================

    def _compute_am(self) -> None:
        """Compute AM modulation and demodulation."""
        duration = min(self.AM_DURATION, len(self._audio) / self._original_sr)
        sample_count = int(duration * self._original_sr)
        audio = self._audio[:sample_count].copy()
        self._time = np.linspace(0, duration, len(audio))

        # Normalize audio
        audio_norm = audio / (np.max(np.abs(audio)) + 1e-10)

        fc_hz = self.parameters["am_carrier_freq"] * 1000
        carrier_dc = self.parameters["am_carrier_dc"]
        am_mode = self.parameters["am_mode"]

        # Generate carrier
        carrier = np.cos(2 * np.pi * fc_hz * self._time)

        # Modulation
        if am_mode == "dsb_sc":
            self._am_modulated = audio_norm * carrier
        else:
            self._am_modulated = (audio_norm + carrier_dc) * carrier

        # Demodulation
        if am_mode == "envelope":
            # Envelope detection using Hilbert transform
            analytic = signal.hilbert(self._am_modulated)
            envelope = np.abs(analytic) - carrier_dc
            self._am_recovered = envelope
        else:
            # Synchronous demodulation
            demod_sync = self._am_modulated * carrier
            nyq = self._original_sr / 2.0
            cutoff = min(5000, nyq * 0.9)
            wn = min(0.99, cutoff / nyq)
            b, a = signal.butter(6, wn, btype="low")
            self._am_recovered = signal.filtfilt(b, a, demod_sync) * 2

        # Normalize recovered
        self._am_recovered = self._am_recovered / (np.max(np.abs(self._am_recovered)) + 1e-10)

        # Store normalized audio for comparison
        self._audio_norm = audio_norm

    # =========================================================================
    # FM/PM Computation (matching fm.py)
    # =========================================================================

    def _compute_fm_pm(self) -> None:
        """Compute FM or PM modulation and demodulation."""
        duration = min(self.FM_DURATION, len(self._audio) / self._original_sr)
        sample_count = int(duration * self._original_sr)
        audio = self._audio[:sample_count].copy()
        self._time = np.linspace(0, duration, len(audio))

        # Normalize audio
        audio_norm = audio / (np.max(np.abs(audio)) + 1e-10)
        self._audio_norm = audio_norm

        fc_hz = self.parameters["fm_carrier_freq"] * 1000
        fm_pm_mode = self.parameters["fm_pm_mode"]
        dt = 1.0 / self._original_sr

        if fm_pm_mode == "fm":
            # FM: phase is integral of message
            kf = self.parameters["fm_deviation"]
            integral = np.cumsum(audio_norm) * dt
            phase = 2 * np.pi * (fc_hz * self._time + kf * integral)
            self._fm_modulated = np.cos(phase)

            # FM demodulation via phase differentiation
            analytic = signal.hilbert(self._fm_modulated)
            inst_phase = np.unwrap(np.angle(analytic))
            inst_freq = np.gradient(inst_phase, dt) / (2 * np.pi)
            self._fm_inst_freq = inst_freq

            # Remove carrier and normalize
            self._fm_recovered = (inst_freq - fc_hz) / kf
        else:
            # PM: phase is proportional to message
            kp = self.parameters["pm_sensitivity"]
            phase = 2 * np.pi * fc_hz * self._time + kp * audio_norm
            self._fm_modulated = np.cos(phase)

            # PM demodulation
            analytic = signal.hilbert(self._fm_modulated)
            inst_phase = np.unwrap(np.angle(analytic))
            carrier_phase = 2 * np.pi * fc_hz * self._time
            self._fm_recovered = (inst_phase - carrier_phase) / kp

            # Calculate instantaneous frequency for display
            inst_freq = np.gradient(inst_phase, dt) / (2 * np.pi)
            self._fm_inst_freq = inst_freq

        # Lowpass filter recovered signal
        nyq = self._original_sr / 2.0
        cutoff = min(5000, nyq * 0.9)
        wn = min(0.99, cutoff / nyq)
        b, a = signal.butter(5, wn, btype="low")
        self._fm_recovered = signal.filtfilt(b, a, self._fm_recovered)

        # Normalize recovered
        self._fm_recovered = self._fm_recovered / (np.max(np.abs(self._fm_recovered)) + 1e-10)

    # =========================================================================
    # FDM Computation (matching fdm.py)
    # =========================================================================

    def _compute_fdm(self) -> None:
        """Compute Frequency Division Multiplexing."""
        duration = min(self.FDM_DURATION, len(self._audio) / self._original_sr)
        sample_count = int(duration * self._original_sr)
        audio = self._audio[:sample_count].copy()
        self._time = np.linspace(0, duration, len(audio))

        # Normalize audio
        audio_norm = audio / (np.max(np.abs(audio)) + 1e-10)
        self._audio_norm = audio_norm

        n_channels = int(self.parameters["fdm_channels"])
        spacing_hz = self.parameters["fdm_spacing"] * 1000
        base_freq = 5000  # 5 kHz base

        # Calculate carrier frequencies
        self._fdm_carrier_freqs = [base_freq + i * spacing_hz for i in range(n_channels)]

        # Create multiplexed signal (matching PyQt5 fdm.py logic)
        channels = []
        for i in range(n_channels):
            # Shift calculation matching PyQt5: idx * len / (num_channels * 2)
            shift_samples = int(i * len(audio_norm) / max(n_channels * 2, 1))
            shifted = np.roll(audio_norm, shift_samples)
            # Normalize each shifted channel (matching PyQt5)
            shifted = shifted / (np.max(np.abs(shifted)) + 1e-10)
            fc = self._fdm_carrier_freqs[i]
            carrier = np.cos(2 * np.pi * fc * self._time)
            modulated = shifted * carrier
            channels.append(modulated)

        # Sum and normalize (matching PyQt5)
        if channels:
            self._fdm_multiplexed = np.sum(channels, axis=0) / max(n_channels, 1)
        else:
            self._fdm_multiplexed = np.zeros_like(audio_norm)

        # Demodulate selected channel
        demod_channel = int(min(self.parameters["fdm_demod_channel"], n_channels)) - 1
        demod_fc = self._fdm_carrier_freqs[demod_channel]

        # Synchronous demodulation
        carrier = np.cos(2 * np.pi * demod_fc * self._time)
        product = self._fdm_multiplexed * carrier

        # Lowpass filter (matching PyQt5: fixed 5kHz cutoff)
        nyq = self._original_sr / 2.0
        cutoff = min(5000, nyq * 0.9) if nyq > 0 else 2000
        cutoff = max(500.0, cutoff)
        wn = min(0.99, cutoff / nyq)
        b, a = signal.butter(6, wn, btype="low")
        demod = signal.filtfilt(b, a, product) * 2
        self._fdm_demodulated = demod

        # Normalize
        self._fdm_demodulated = self._fdm_demodulated / (np.max(np.abs(self._fdm_demodulated)) + 1e-10)

    # =========================================================================
    # Audio encoding for web playback
    # =========================================================================

    def _encode_audio_base64(self, audio: np.ndarray, gain: float = 1.0) -> str:
        """Convert audio array to base64 WAV string."""
        audio_gained = audio * gain
        audio_norm = audio_gained / (np.max(np.abs(audio_gained)) + 1e-10)
        audio_int16 = (audio_norm * 32767).astype(np.int16)

        buffer = io.BytesIO()
        wavfile.write(buffer, self._original_sr, audio_int16)
        buffer.seek(0)
        return f"data:audio/wav;base64,{base64.b64encode(buffer.read()).decode()}"

    # =========================================================================
    # Plot generation
    # =========================================================================

    def get_plots(self) -> List[Dict[str, Any]]:
        """Generate plots based on current demo mode."""
        if not self._initialized:
            self.initialize()

        demo_mode = self.parameters["demo_mode"]

        if demo_mode == "am":
            return self._get_am_plots()
        elif demo_mode == "fm_pm":
            return self._get_fm_pm_plots()
        elif demo_mode == "fdm":
            return self._get_fdm_plots()

        return []

    def _get_am_plots(self) -> List[Dict[str, Any]]:
        """Generate AM demo plots (4 subplots like PyQt5)."""
        plots = []

        # Calculate display segment
        length = len(self._audio_norm)
        seg_start = length // 4
        seg_end = min(seg_start + self.DISPLAY_SAMPLES, length)
        seg = slice(seg_start, seg_end)
        t_seg = self._time[seg] * 1000  # Convert to ms

        fc_hz = self.parameters["am_carrier_freq"] * 1000
        am_mode = self.parameters["am_mode"]
        carrier_dc = self.parameters["am_carrier_dc"]

        # Plot 1: Message Signal
        plots.append({
            "id": "am_message",
            "title": "Message Signal x(t)",
            "data": [{
                "x": t_seg.tolist(),
                "y": self._audio_norm[seg].tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": "Message",
                "line": {"color": self.COLORS["accent"], "width": 1.5},
            }],
            "layout": self._get_plot_layout("Time (ms)", "Amplitude"),
        })

        # Plot 2: Modulated Signal
        mode_label = {"dsb_sc": "DSB-SC", "am_carrier": "AM+Carrier", "envelope": "Envelope"}
        mod_data = [{
            "x": t_seg.tolist(),
            "y": self._am_modulated[seg].tolist(),
            "type": "scatter",
            "mode": "lines",
            "name": "Modulated",
            "line": {"color": self.COLORS["danger"], "width": 1},
        }]

        # Add envelope for non-DSB-SC modes
        if am_mode != "dsb_sc":
            env = (self._audio_norm + carrier_dc)[seg]
            mod_data.extend([
                {
                    "x": t_seg.tolist(),
                    "y": env.tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "name": "Envelope",
                    "line": {"color": self.COLORS["success"], "width": 1.2},
                },
                {
                    "x": t_seg.tolist(),
                    "y": (-env).tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "name": "-Envelope",
                    "line": {"color": self.COLORS["success"], "width": 1.2},
                    "showlegend": False,
                },
            ])

        plots.append({
            "id": "am_modulated",
            "title": f"{mode_label.get(am_mode, am_mode)} Modulated (fc={fc_hz/1000:.0f} kHz)",
            "data": mod_data,
            "layout": self._get_plot_layout("Time (ms)", "Amplitude"),
        })

        # Plot 3: Recovered Signal
        method = "Envelope" if am_mode == "envelope" else "Synchronous"
        plots.append({
            "id": "am_recovered",
            "title": f"Recovered Signal ({method} demod)",
            "data": [{
                "x": t_seg.tolist(),
                "y": self._am_recovered[seg].tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": "Recovered",
                "line": {"color": self.COLORS["success"], "width": 1.5},
            }],
            "layout": self._get_plot_layout("Time (ms)", "Amplitude"),
        })

        # Plot 4: Spectrum
        freqs, psd = signal.welch(self._am_modulated, self._original_sr, nperseg=min(4096, len(self._am_modulated)))
        psd_db = 10 * np.log10(psd + 1e-12)

        plots.append({
            "id": "am_spectrum",
            "title": "Spectrum",
            "data": [{
                "x": (freqs / 1000).tolist(),
                "y": psd_db.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": "PSD",
                "line": {"color": self.COLORS["warning"], "width": 1.5},
            }],
            "layout": {
                **self._get_plot_layout("Frequency (kHz)", "Power (dB)"),
                "xaxis": {
                    "title": "Frequency (kHz)",
                    "range": [0, 25],
                    "showgrid": True,
                    "gridcolor": "rgba(148, 163, 184, 0.15)",
                },
                "shapes": [{
                    "type": "line",
                    "x0": fc_hz / 1000, "x1": fc_hz / 1000,
                    "y0": float(psd_db.min() - 10), "y1": float(psd_db.max() + 5),
                    "line": {"color": self.COLORS["danger"], "width": 2, "dash": "dash"},
                }],
            },
        })

        return plots

    def _get_fm_pm_plots(self) -> List[Dict[str, Any]]:
        """Generate FM/PM demo plots (5 subplots like PyQt5)."""
        plots = []

        length = len(self._audio_norm)
        seg_start = length // 4
        seg_end = min(seg_start + self.DISPLAY_SAMPLES, length)
        seg = slice(seg_start, seg_end)
        t_seg = self._time[seg] * 1000

        fc_hz = self.parameters["fm_carrier_freq"] * 1000
        fm_pm_mode = self.parameters["fm_pm_mode"]

        # Plot 1: Message Signal
        plots.append({
            "id": "fm_message",
            "title": "Message Signal x(t)",
            "data": [{
                "x": t_seg.tolist(),
                "y": self._audio_norm[seg].tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": "Message",
                "line": {"color": self.COLORS["accent"], "width": 1.5},
            }],
            "layout": self._get_plot_layout("Time (ms)", "Amplitude"),
        })

        # Plot 2: Modulated Signal
        if fm_pm_mode == "fm":
            title = f"FM Signal (fc={fc_hz/1000:.0f} kHz, Δf={self.parameters['fm_deviation']} Hz)"
        else:
            title = f"PM Signal (fc={fc_hz/1000:.0f} kHz, kp={self.parameters['pm_sensitivity']:.1f} rad)"

        plots.append({
            "id": "fm_modulated",
            "title": title,
            "data": [{
                "x": t_seg.tolist(),
                "y": self._fm_modulated[seg].tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": "Modulated",
                "line": {"color": self.COLORS["danger"], "width": 1},
            }],
            "layout": self._get_plot_layout("Time (ms)", "Amplitude"),
        })

        # Plot 3: Instantaneous Frequency
        inst_freq_khz = self._fm_inst_freq[seg] / 1000
        plots.append({
            "id": "fm_inst_freq",
            "title": "Instantaneous Frequency",
            "data": [
                {
                    "x": t_seg.tolist(),
                    "y": inst_freq_khz.tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "name": "Inst. Freq",
                    "line": {"color": self.COLORS["purple"], "width": 1.5},
                },
                {
                    "x": [t_seg[0], t_seg[-1]],
                    "y": [fc_hz / 1000, fc_hz / 1000],
                    "type": "scatter",
                    "mode": "lines",
                    "name": "Carrier",
                    "line": {"color": self.COLORS["danger"], "width": 1, "dash": "dash"},
                },
            ],
            "layout": self._get_plot_layout("Time (ms)", "Frequency (kHz)"),
        })

        # Plot 4: Recovered Signal
        plots.append({
            "id": "fm_recovered",
            "title": "Recovered Baseband",
            "data": [{
                "x": t_seg.tolist(),
                "y": self._fm_recovered[seg].tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": "Recovered",
                "line": {"color": self.COLORS["success"], "width": 1.5},
            }],
            "layout": self._get_plot_layout("Time (ms)", "Amplitude"),
        })

        # Plot 5: Spectrum
        freqs, psd = signal.welch(self._fm_modulated, self._original_sr, nperseg=min(4096, len(self._fm_modulated)))
        psd_db = 10 * np.log10(psd + 1e-12)

        # Carson's rule bandwidth
        if fm_pm_mode == "fm":
            bw_hz = 2 * (self.parameters["fm_deviation"] + 5000)
            bw_text = f"Carson BW ≈ {bw_hz/1000:.1f} kHz"
        else:
            bw_hz = 2 * 5000 * (1 + self.parameters["pm_sensitivity"])
            bw_text = f"BW ≈ {bw_hz/1000:.1f} kHz"

        plots.append({
            "id": "fm_spectrum",
            "title": f"Spectrum | {bw_text}",
            "data": [{
                "x": (freqs / 1000).tolist(),
                "y": psd_db.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": "PSD",
                "line": {"color": self.COLORS["warning"], "width": 1.5},
            }],
            "layout": {
                **self._get_plot_layout("Frequency (kHz)", "Power (dB)"),
                "xaxis": {
                    "title": "Frequency (kHz)",
                    "range": [0, 30],
                    "showgrid": True,
                    "gridcolor": "rgba(148, 163, 184, 0.15)",
                },
            },
        })

        return plots

    def _get_fdm_plots(self) -> List[Dict[str, Any]]:
        """Generate FDM demo plots (3 subplots like PyQt5)."""
        plots = []

        length = len(self._audio_norm)
        seg_start = length // 4
        seg_end = min(seg_start + self.DISPLAY_SAMPLES, length)
        seg = slice(seg_start, seg_end)
        t_seg = self._time[seg] * 1000

        n_channels = int(self.parameters["fdm_channels"])
        demod_channel = int(min(self.parameters["fdm_demod_channel"], n_channels))

        # Plot 1: Multiplexed Signal
        plots.append({
            "id": "fdm_multiplexed",
            "title": f"Multiplexed Signal ({n_channels} channels)",
            "data": [{
                "x": t_seg.tolist(),
                "y": self._fdm_multiplexed[seg].tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": "Multiplexed",
                "line": {"color": self.COLORS["warning"], "width": 1},
            }],
            "layout": self._get_plot_layout("Time (ms)", "Amplitude"),
        })

        # Plot 2: Spectrum with channel markers
        freqs, psd = signal.welch(self._fdm_multiplexed, self._original_sr, nperseg=min(4096, len(self._fdm_multiplexed)))
        psd_db = 10 * np.log10(psd + 1e-12)

        spectrum_data = [{
            "x": (freqs / 1000).tolist(),
            "y": psd_db.tolist(),
            "type": "scatter",
            "mode": "lines",
            "name": "PSD",
            "line": {"color": self.COLORS["warning"], "width": 1.5},
        }]

        # Add channel markers
        shapes = []
        for i, fc in enumerate(self._fdm_carrier_freqs):
            color = self.COLORS["accent"] if i == demod_channel - 1 else self.COLORS["text_secondary"]
            shapes.append({
                "type": "line",
                "x0": fc / 1000, "x1": fc / 1000,
                "y0": float(psd_db.min() - 10), "y1": float(psd_db.max() + 5),
                "line": {"color": color, "width": 2 if i == demod_channel - 1 else 1, "dash": "dash"},
            })

        plots.append({
            "id": "fdm_spectrum",
            "title": f"Spectrum (Channel {demod_channel} selected)",
            "data": spectrum_data,
            "layout": {
                **self._get_plot_layout("Frequency (kHz)", "Power (dB)"),
                "xaxis": {
                    "title": "Frequency (kHz)",
                    "range": [0, max(fc / 1000 for fc in self._fdm_carrier_freqs) + 10],
                    "showgrid": True,
                    "gridcolor": "rgba(148, 163, 184, 0.15)",
                },
                "shapes": shapes,
            },
        })

        # Plot 3: Demodulated Channel
        plots.append({
            "id": "fdm_demodulated",
            "title": f"Demodulated Channel {demod_channel}",
            "data": [{
                "x": t_seg.tolist(),
                "y": self._fdm_demodulated[seg].tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": "Demodulated",
                "line": {"color": self.COLORS["success"], "width": 1.5},
            }],
            "layout": self._get_plot_layout("Time (ms)", "Amplitude"),
        })

        return plots

    def _get_plot_layout(self, x_title: str, y_title: str) -> Dict[str, Any]:
        """Get standard plot layout."""
        return {
            "xaxis": {
                "title": x_title,
                "showgrid": True,
                "gridcolor": "rgba(148, 163, 184, 0.15)",
                "zeroline": True,
                "zerolinecolor": "rgba(148, 163, 184, 0.3)",
            },
            "yaxis": {
                "title": y_title,
                "showgrid": True,
                "gridcolor": "rgba(148, 163, 184, 0.15)",
            },
            "margin": {"l": 50, "r": 20, "t": 40, "b": 40},
            "height": 180,
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(15, 23, 42, 0.5)",
            "font": {"color": "#e2e8f0", "size": 11},
        }

    # =========================================================================
    # State and metadata
    # =========================================================================

    def get_state(self) -> Dict[str, Any]:
        """Return current simulation state with visualization data."""
        state = super().get_state()

        demo_mode = self.parameters["demo_mode"]

        # Build audio playback data
        audio_data = self._build_audio_data()

        # Build system info for info panel
        system_info = self._build_system_info()

        state["metadata"] = {
            "simulation_type": "modulation_techniques",
            "has_custom_viewer": True,
            "sticky_controls": True,
            "demo_mode": demo_mode,
            "audio_data": audio_data,
            "system_info": system_info,
        }

        return state

    def _build_audio_data(self) -> Dict[str, Any]:
        """Build audio playback data based on demo mode."""
        demo_mode = self.parameters["demo_mode"]

        if demo_mode == "am":
            return {
                "original": self._encode_audio_base64(self._audio_norm, gain=1.0),
                "modulated": self._encode_audio_base64(self._am_modulated, gain=0.35),
                "recovered": self._encode_audio_base64(self._am_recovered, gain=0.9),
            }
        elif demo_mode == "fm_pm":
            return {
                "original": self._encode_audio_base64(self._audio_norm, gain=1.0),
                "modulated": self._encode_audio_base64(self._fm_modulated, gain=0.25),
                "recovered": self._encode_audio_base64(self._fm_recovered, gain=0.9),
            }
        elif demo_mode == "fdm":
            return {
                "multiplexed": self._encode_audio_base64(self._fdm_multiplexed, gain=0.35),
                "demodulated": self._encode_audio_base64(self._fdm_demodulated, gain=1.0),
            }

        return {}

    def _build_system_info(self) -> Dict[str, Any]:
        """Build system info for display."""
        demo_mode = self.parameters["demo_mode"]

        if demo_mode == "am":
            am_mode = self.parameters["am_mode"]
            mode_label = {"dsb_sc": "DSB-SC", "am_carrier": "AM+Carrier", "envelope": "Envelope"}
            return {
                "mode": "Amplitude Modulation",
                "am_type": mode_label.get(am_mode, am_mode),
                "carrier_freq": f"{self.parameters['am_carrier_freq']} kHz",
                "carrier_dc": f"{self.parameters['am_carrier_dc']:.2f}",
                "sample_rate": f"{self._original_sr} Hz",
                "duration": f"{self.AM_DURATION:.1f}s",
            }
        elif demo_mode == "fm_pm":
            fm_pm_mode = self.parameters["fm_pm_mode"]
            if fm_pm_mode == "fm":
                return {
                    "mode": "Frequency Modulation",
                    "carrier_freq": f"{self.parameters['fm_carrier_freq']} kHz",
                    "freq_deviation": f"{self.parameters['fm_deviation']} Hz",
                    "carson_bw": f"{2 * (self.parameters['fm_deviation'] + 5000) / 1000:.1f} kHz",
                    "sample_rate": f"{self._original_sr} Hz",
                }
            else:
                return {
                    "mode": "Phase Modulation",
                    "carrier_freq": f"{self.parameters['fm_carrier_freq']} kHz",
                    "phase_sensitivity": f"{self.parameters['pm_sensitivity']:.1f} rad",
                    "sample_rate": f"{self._original_sr} Hz",
                }
        elif demo_mode == "fdm":
            return {
                "mode": "Frequency Division Multiplexing",
                "channels": self.parameters["fdm_channels"],
                "spacing": f"{self.parameters['fdm_spacing']} kHz",
                "demod_channel": self.parameters["fdm_demod_channel"],
                "carrier_freqs": ", ".join([f"{fc/1000:.0f}" for fc in self._fdm_carrier_freqs]) + " kHz",
                "sample_rate": f"{self._original_sr} Hz",
            }

        return {}
