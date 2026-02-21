"""
Laplace Properties Lab

Interactive demonstration of the seven key Laplace transform properties:
  1. Linearity:       ax₁(t) + bx₂(t)        ↔  aX₁(s) + bX₂(s)
  2. Time Delay:      x(t−T)                  ↔  e⁻ˢᵀ X(s)
  3. Multiply by t:   t·x(t)                  ↔  −dX(s)/ds
  4. Frequency Shift: e⁻ᵅᵗ x(t)              ↔  X(s+α)
  5. Differentiate:   dx/dt                   ↔  sX(s)
  6. Integrate:       ∫x(τ)dτ                 ↔  X(s)/s
  7. Convolution:     x₁(t)∗x₂(t)            ↔  X₁(s)·X₂(s)

Users pick one or two signals from a library, apply a property, and see the
operation in both time domain (continuous waveforms) and s-domain (pole-zero +
ROC) simultaneously.

Based on Lecture 6: slide 34 (full property table).
"""

from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .base_simulator import BaseSimulator

# ── Signal library ────────────────────────────────────────────────────

SIGNAL_LIBRARY = {
    "impulse": {
        "label": "δ(t)",
        "s_expr": "1",
        "roc_type": "all",
        "has_param": False,
    },
    "unit_step": {
        "label": "u(t)",
        "s_expr": "1/s",
        "roc_type": "right_half",
        "roc_boundary": 0.0,
        "has_param": False,
    },
    "exponential": {
        "label": "e⁻ᵅᵗ u(t)",
        "s_expr": "1/(s+α)",
        "roc_type": "right_half",
        "has_param": True,
        "param_name": "alpha",
    },
    "ramp_exp": {
        "label": "t·e⁻ᵅᵗ u(t)",
        "s_expr": "1/(s+α)²",
        "roc_type": "right_half",
        "has_param": True,
        "param_name": "alpha",
    },
    "cosine": {
        "label": "cos(ω₀t) u(t)",
        "s_expr": "s/(s²+ω₀²)",
        "roc_type": "right_half",
        "roc_boundary": 0.0,
        "has_param": True,
        "param_name": "omega0",
    },
    "damped_cosine": {
        "label": "e⁻ᵅᵗcos(ω₀t) u(t)",
        "s_expr": "(s+α)/((s+α)²+ω₀²)",
        "roc_type": "right_half",
        "has_param": True,
        "param_name": "both",
    },
}

PROPERTY_FORMULAS = {
    "linearity":     "ax₁(t) + bx₂(t)  ↔  aX₁(s) + bX₂(s),  ROC ⊇ R₁ ∩ R₂",
    "delay":         "x(t−T)  ↔  e⁻ˢᵀ·X(s),  ROC = R",
    "multiply_t":    "t·x(t)  ↔  −dX(s)/ds,  ROC = R",
    "freq_shift":    "e⁻ᵅᵗ·x(t)  ↔  X(s+α),  shift R by −α",
    "differentiate": "dx/dt  ↔  s·X(s),  ROC ⊇ R",
    "integrate":     "∫x(τ)dτ  ↔  X(s)/s,  ROC ⊇ R ∩ {Re(s)>0}",
    "convolution":   "x₁∗x₂  ↔  X₁(s)·X₂(s),  ROC ⊇ R₁ ∩ R₂",
}

# ── Constants ─────────────────────────────────────────────────────────

TIME_START = -1.0
TIME_END = 10.0
NUM_SAMPLES = 800
IMPULSE_SIGMA = 0.02
DISPLAY_CLIP = 1000.0


class LaplacePropertiesSimulator(BaseSimulator):
    """Simulator for the Laplace Transform Properties Lab."""

    PARAMETER_SCHEMA = {
        "signal_1": {
            "type": "select",
            "options": list(SIGNAL_LIBRARY.keys()),
            "default": "unit_step",
        },
        "signal_2": {
            "type": "select",
            "options": list(SIGNAL_LIBRARY.keys()),
            "default": "exponential",
        },
        "property": {
            "type": "select",
            "options": [
                "linearity", "delay", "multiply_t", "freq_shift",
                "differentiate", "integrate", "convolution",
            ],
            "default": "linearity",
        },
        "alpha": {"type": "slider", "min": -3.0, "max": 3.0, "step": 0.1, "default": 1.0},
        "beta": {"type": "slider", "min": -3.0, "max": 3.0, "step": 0.1, "default": 1.0},
        "delay_T": {"type": "slider", "min": 0.0, "max": 5.0, "step": 0.1, "default": 1.0},
        "freq_shift_alpha": {"type": "slider", "min": -3.0, "max": 3.0, "step": 0.1, "default": 1.0},
        "signal_1_alpha": {"type": "slider", "min": 0.1, "max": 5.0, "step": 0.1, "default": 1.0},
        "signal_1_omega0": {"type": "slider", "min": 0.1, "max": 10.0, "step": 0.1, "default": 2.0},
        "signal_2_alpha": {"type": "slider", "min": 0.1, "max": 5.0, "step": 0.1, "default": 1.0},
        "signal_2_omega0": {"type": "slider", "min": 0.1, "max": 10.0, "step": 0.1, "default": 2.0},
    }

    DEFAULT_PARAMS = {
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
    }

    def __init__(self, simulation_id: str) -> None:
        super().__init__(simulation_id)
        self._cached: Optional[Dict[str, Any]] = None
        self._revision: int = 0

    # ── BaseSimulator interface ───────────────────────────────────────

    def initialize(self, params: Optional[Dict[str, Any]] = None) -> None:
        self.parameters = {**self.DEFAULT_PARAMS, **(params or {})}
        for name in list(self.parameters):
            if name in self.PARAMETER_SCHEMA:
                self.parameters[name] = self._validate_param(name, self.parameters[name])
        self._cached = None
        self._revision += 1
        self._initialized = True

    def reset(self) -> Dict[str, Any]:
        self.parameters = self.DEFAULT_PARAMS.copy()
        self._cached = None
        self._revision += 1
        self._initialized = True
        return self.get_state()

    def update_parameter(self, name: str, value: Any) -> Dict[str, Any]:
        if name in self.parameters:
            self.parameters[name] = self._validate_param(name, value)
        self._cached = None
        self._revision += 1
        return self.get_state()

    def get_plots(self) -> List[Dict[str, Any]]:
        return self._compute()["plots"]

    def get_state(self) -> Dict[str, Any]:
        data = self._compute()
        prop = self.parameters["property"]
        needs_second = prop in ("linearity", "convolution")

        return {
            "parameters": self.parameters.copy(),
            "plots": data["plots"],
            "metadata": {
                "simulation_type": "laplace_properties",
                "property": prop,
                "property_formula": PROPERTY_FORMULAS.get(prop, ""),
                "signal_1_info": data["signal_1_info"],
                "signal_2_info": data.get("signal_2_info"),
                "result_info": data["result_info"],
                "roc_1": data["roc_1"],
                "roc_2": data.get("roc_2"),
                "roc_result": data["roc_result"],
                "needs_second_signal": needs_second,
                "original_poles": data.get("original_poles"),
                "shifted_poles": data.get("shifted_poles"),
                "revision": self._revision,
            },
        }

    # ── Master computation ────────────────────────────────────────────

    def _compute(self) -> Dict[str, Any]:
        if self._cached is not None:
            return self._cached

        prop = self.parameters["property"]
        needs_second = prop in ("linearity", "convolution")

        t = np.linspace(TIME_START, TIME_END, NUM_SAMPLES)
        dt = t[1] - t[0]

        x1, sig1_info = self._generate_signal(self.parameters["signal_1"], 1, t)
        roc_1 = self._get_roc(self.parameters["signal_1"], 1)
        pz_1 = self._get_poles_zeros(self.parameters["signal_1"], 1)

        x2, sig2_info, roc_2, pz_2 = None, None, None, None
        if needs_second:
            x2, sig2_info = self._generate_signal(self.parameters["signal_2"], 2, t)
            roc_2 = self._get_roc(self.parameters["signal_2"], 2)
            pz_2 = self._get_poles_zeros(self.parameters["signal_2"], 2)

        original_poles = None
        shifted_poles = None

        if prop == "linearity":
            result, result_t, result_info, result_pz = self._apply_linearity(
                x1, x2, sig1_info, sig2_info, pz_1, pz_2, t
            )
        elif prop == "delay":
            result, result_t, result_info, result_pz = self._apply_delay(x1, sig1_info, t, pz_1)
        elif prop == "multiply_t":
            result, result_t, result_info, result_pz = self._apply_multiply_t(x1, sig1_info, t, pz_1)
        elif prop == "freq_shift":
            result, result_t, result_info, result_pz, original_poles, shifted_poles = (
                self._apply_freq_shift(x1, sig1_info, t, pz_1)
            )
        elif prop == "differentiate":
            result, result_t, result_info, result_pz = self._apply_differentiate(
                x1, sig1_info, t, pz_1
            )
        elif prop == "integrate":
            result, result_t, result_info, result_pz = self._apply_integrate(
                x1, sig1_info, t, pz_1
            )
        else:  # convolution
            result, result_t, result_info, result_pz = self._apply_convolution(
                x1, x2, sig1_info, sig2_info, t, dt, pz_1, pz_2
            )

        roc_result = self._compute_result_roc(prop, roc_1, roc_2)

        plots = self._build_plots(
            t, x1, sig1_info, x2, sig2_info,
            result, result_t, result_info, needs_second,
            pz_1, pz_2, result_pz,
            roc_1, roc_2, roc_result,
            original_poles, shifted_poles,
        )

        self._cached = {
            "plots": plots,
            "signal_1_info": sig1_info,
            "signal_2_info": sig2_info,
            "result_info": result_info,
            "roc_1": roc_1,
            "roc_2": roc_2,
            "roc_result": roc_result,
            "original_poles": original_poles,
            "shifted_poles": shifted_poles,
        }
        return self._cached

    # ── Signal generation ─────────────────────────────────────────────

    def _generate_signal(
        self, sig_key: str, sig_num: int, t: np.ndarray
    ) -> Tuple[np.ndarray, Dict[str, str]]:
        u = (t >= 0).astype(float)

        if sig_key == "impulse":
            # Narrow Gaussian approximation for display
            x = (1.0 / (IMPULSE_SIGMA * np.sqrt(2 * np.pi))) * np.exp(
                -t ** 2 / (2 * IMPULSE_SIGMA ** 2)
            )
            info = {"label": "δ(t)", "s_expr": "1", "signal_key": sig_key}

        elif sig_key == "unit_step":
            x = u.copy()
            info = {"label": "u(t)", "s_expr": "1/s", "signal_key": sig_key}

        elif sig_key == "exponential":
            a = float(self.parameters[f"signal_{sig_num}_alpha"])
            x = np.exp(-a * t) * u
            info = {
                "label": f"e^(−{a:g}t) u(t)",
                "s_expr": f"1/(s+{a:g})",
                "signal_key": sig_key,
            }

        elif sig_key == "ramp_exp":
            a = float(self.parameters[f"signal_{sig_num}_alpha"])
            x = t * np.exp(-a * t) * u
            info = {
                "label": f"t·e^(−{a:g}t) u(t)",
                "s_expr": f"1/(s+{a:g})²",
                "signal_key": sig_key,
            }

        elif sig_key == "cosine":
            w0 = float(self.parameters[f"signal_{sig_num}_omega0"])
            x = np.cos(w0 * t) * u
            info = {
                "label": f"cos({w0:g}t) u(t)",
                "s_expr": f"s/(s²+{w0:g}²)",
                "signal_key": sig_key,
            }

        elif sig_key == "damped_cosine":
            a = float(self.parameters[f"signal_{sig_num}_alpha"])
            w0 = float(self.parameters[f"signal_{sig_num}_omega0"])
            x = np.exp(-a * t) * np.cos(w0 * t) * u
            info = {
                "label": f"e^(−{a:g}t)cos({w0:g}t) u(t)",
                "s_expr": f"(s+{a:g})/((s+{a:g})²+{w0:g}²)",
                "signal_key": sig_key,
            }

        else:
            x = np.zeros_like(t)
            info = {"label": "?", "s_expr": "?", "signal_key": sig_key}

        return x, info

    # ── Property operations ───────────────────────────────────────────

    def _apply_linearity(
        self,
        x1: np.ndarray, x2: np.ndarray,
        info1: Dict, info2: Dict,
        pz_1: Dict, pz_2: Dict,
        t: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray, Dict, Dict]:
        a = float(self.parameters["alpha"])
        b = float(self.parameters["beta"])
        result = a * x1 + b * x2

        result_info = {
            "label": f"{a:g}·{info1['label']} + {b:g}·{info2['label']}",
            "s_expr": f"{a:g}·({info1['s_expr']}) + {b:g}·({info2['s_expr']})",
        }
        # Union of poles; zeros are indeterminate for sums of rationals
        result_pz = {
            "poles": pz_1["poles"] + pz_2["poles"],
            "zeros": [],
        }
        return result, t, result_info, result_pz

    def _apply_delay(
        self,
        x1: np.ndarray, info1: Dict, t: np.ndarray,
        pz_1: Dict,
    ) -> Tuple[np.ndarray, np.ndarray, Dict, Dict]:
        T = float(self.parameters["delay_T"])
        # Shift signal by T: x(t-T) via interpolation
        result = np.interp(t - T, t, x1, left=0.0, right=0.0)

        result_info = {
            "label": f"{info1['label']} delayed by {T:g}s",
            "s_expr": f"e^(−{T:g}s)·({info1['s_expr']})",
        }
        # e^(-sT) doesn't add finite poles/zeros
        result_pz = {
            "poles": list(pz_1["poles"]),
            "zeros": list(pz_1["zeros"]),
        }
        return result, t, result_info, result_pz

    def _apply_multiply_t(
        self,
        x1: np.ndarray, info1: Dict, t: np.ndarray,
        pz_1: Dict,
    ) -> Tuple[np.ndarray, np.ndarray, Dict, Dict]:
        result = t * x1

        result_info = {
            "label": f"t·{info1['label']}",
            "s_expr": f"−d/ds[{info1['s_expr']}]",
        }
        # Differentiation in s doubles pole multiplicity
        result_pz = {
            "poles": list(pz_1["poles"]) + list(pz_1["poles"]),
            "zeros": list(pz_1["zeros"]),
        }
        return result, t, result_info, result_pz

    def _apply_freq_shift(
        self,
        x1: np.ndarray, info1: Dict, t: np.ndarray,
        pz_1: Dict,
    ) -> Tuple[np.ndarray, np.ndarray, Dict, Dict, List, List]:
        a = float(self.parameters["freq_shift_alpha"])
        u = (t >= 0).astype(float)
        result = np.exp(-a * t) * x1 * u
        # Clip for numerical stability when a is negative
        result = np.clip(result, -DISPLAY_CLIP, DISPLAY_CLIP)

        result_info = {
            "label": f"e^(−{a:g}t)·{info1['label']}",
            "s_expr": f"{info1['s_expr']} with s → s+{a:g}",
        }

        # Shift all poles and zeros by -a along real axis
        original_poles = list(pz_1["poles"])
        original_zeros = list(pz_1["zeros"])
        shifted_poles = [(p[0] - a, p[1]) for p in original_poles]
        shifted_zeros = [(z[0] - a, z[1]) for z in original_zeros]

        result_pz = {
            "poles": shifted_poles,
            "zeros": shifted_zeros,
        }

        # Return original and shifted for arrow visualization
        return (
            result, t, result_info, result_pz,
            [list(p) for p in original_poles],
            [list(p) for p in shifted_poles],
        )

    def _apply_differentiate(
        self,
        x1: np.ndarray, info1: Dict, t: np.ndarray,
        pz_1: Dict,
    ) -> Tuple[np.ndarray, np.ndarray, Dict, Dict]:
        result = np.gradient(x1, t)
        # Clip spikes from discontinuities
        result = np.clip(result, -DISPLAY_CLIP, DISPLAY_CLIP)

        result_info = {
            "label": f"d/dt[{info1['label']}]",
            "s_expr": f"s·({info1['s_expr']})",
        }

        # s·X(s) adds a zero at s=0; check for pole-zero cancellation
        poles = list(pz_1["poles"])
        zeros = list(pz_1["zeros"])
        # Check if there's a pole at origin to cancel with the new zero
        origin_pole = (0.0, 0.0)
        if origin_pole in poles:
            poles = list(poles)
            poles.remove(origin_pole)
            # Zero from s factor cancels with pole — no new zero added
        else:
            zeros = list(zeros) + [(0.0, 0.0)]

        result_pz = {"poles": poles, "zeros": zeros}
        return result, t, result_info, result_pz

    def _apply_integrate(
        self,
        x1: np.ndarray, info1: Dict, t: np.ndarray,
        pz_1: Dict,
    ) -> Tuple[np.ndarray, np.ndarray, Dict, Dict]:
        dt = t[1] - t[0]
        result = np.cumsum(x1) * dt
        # For t < 0, zero out (right-sided integral)
        result[t < 0] = 0.0

        result_info = {
            "label": f"∫{info1['label']} dτ",
            "s_expr": f"({info1['s_expr']})/s",
        }

        # X(s)/s adds a pole at s=0; check for zero cancellation
        poles = list(pz_1["poles"])
        zeros = list(pz_1["zeros"])
        origin_zero = (0.0, 0.0)
        if origin_zero in zeros:
            zeros = list(zeros)
            zeros.remove(origin_zero)
        else:
            poles = list(poles) + [(0.0, 0.0)]

        result_pz = {"poles": poles, "zeros": zeros}
        return result, t, result_info, result_pz

    def _apply_convolution(
        self,
        x1: np.ndarray, x2: np.ndarray,
        info1: Dict, info2: Dict,
        t: np.ndarray, dt: float,
        pz_1: Dict, pz_2: Dict,
    ) -> Tuple[np.ndarray, np.ndarray, Dict, Dict]:
        full_conv = np.convolve(x1, x2) * dt
        # Build time axis for full convolution
        t_full = np.linspace(2 * t[0], 2 * t[-1], len(full_conv))
        # Truncate to original time range
        mask = (t_full >= t[0]) & (t_full <= t[-1])
        conv_truncated = full_conv[mask]
        t_truncated = t_full[mask]

        # Resample to match original time vector
        if len(t_truncated) > 0:
            result = np.interp(t, t_truncated, conv_truncated, left=0.0, right=0.0)
        else:
            result = np.zeros_like(t)

        result_info = {
            "label": f"{info1['label']} ∗ {info2['label']}",
            "s_expr": f"({info1['s_expr']})·({info2['s_expr']})",
        }
        result_pz = {
            "poles": pz_1["poles"] + pz_2["poles"],
            "zeros": pz_1["zeros"] + pz_2["zeros"],
        }
        return result, t, result_info, result_pz

    # ── ROC helpers ───────────────────────────────────────────────────

    def _get_roc(self, sig_key: str, sig_num: int) -> Dict[str, Any]:
        sig = SIGNAL_LIBRARY[sig_key]
        roc_type = sig["roc_type"]

        if roc_type == "all":
            return {"type": "all", "boundary": None}

        if sig_key in ("unit_step", "cosine"):
            boundary = 0.0
        elif sig_key in ("exponential", "ramp_exp"):
            a = float(self.parameters[f"signal_{sig_num}_alpha"])
            boundary = -a
        elif sig_key == "damped_cosine":
            a = float(self.parameters[f"signal_{sig_num}_alpha"])
            boundary = -a
        else:
            boundary = 0.0

        return {"type": "right_half", "boundary": float(boundary)}

    def _compute_result_roc(
        self, prop: str, roc_1: Dict, roc_2: Optional[Dict]
    ) -> Dict[str, Any]:
        def _boundary(roc: Optional[Dict]) -> float:
            if roc is None:
                return -1e9
            if roc["type"] == "all":
                return -1e9
            return float(roc.get("boundary", 0) or 0)

        b1 = _boundary(roc_1)

        if prop == "linearity":
            b2 = _boundary(roc_2)
            b = max(b1, b2)
            return {"type": "right_half", "boundary": b, "note": "ROC ⊇ R₁ ∩ R₂"}

        if prop == "delay":
            return {"type": roc_1["type"], "boundary": roc_1.get("boundary"), "note": "Same ROC"}

        if prop == "multiply_t":
            return {"type": roc_1["type"], "boundary": roc_1.get("boundary"), "note": "Same ROC"}

        if prop == "freq_shift":
            a = float(self.parameters["freq_shift_alpha"])
            if roc_1["type"] == "all":
                return {"type": "all", "boundary": None, "note": f"Shifted by −{a:g} (still all ℂ)"}
            new_b = b1 - a
            sign = "−" if a > 0 else "+"
            return {"type": "right_half", "boundary": new_b, "note": f"ROC shifted by {sign}{abs(a):g}"}

        if prop == "differentiate":
            return {"type": roc_1["type"], "boundary": roc_1.get("boundary"), "note": "ROC ⊇ R"}

        if prop == "integrate":
            new_b = max(b1, 0.0)
            return {"type": "right_half", "boundary": new_b, "note": "ROC ⊇ R ∩ {Re(s)>0}"}

        # convolution
        b2 = _boundary(roc_2)
        b = max(b1, b2)
        return {"type": "right_half", "boundary": b, "note": "ROC ⊇ R₁ ∩ R₂"}

    # ── Pole / zero helpers ───────────────────────────────────────────

    def _get_poles_zeros(
        self, sig_key: str, sig_num: int
    ) -> Dict[str, List[Tuple[float, float]]]:
        poles: List[Tuple[float, float]] = []
        zeros: List[Tuple[float, float]] = []

        if sig_key == "impulse":
            pass  # X(s) = 1
        elif sig_key == "unit_step":
            poles.append((0.0, 0.0))
        elif sig_key == "exponential":
            a = float(self.parameters[f"signal_{sig_num}_alpha"])
            poles.append((-a, 0.0))
        elif sig_key == "ramp_exp":
            a = float(self.parameters[f"signal_{sig_num}_alpha"])
            poles.append((-a, 0.0))
            poles.append((-a, 0.0))  # double pole
        elif sig_key == "cosine":
            w0 = float(self.parameters[f"signal_{sig_num}_omega0"])
            poles.append((0.0, w0))
            poles.append((0.0, -w0))
            zeros.append((0.0, 0.0))
        elif sig_key == "damped_cosine":
            a = float(self.parameters[f"signal_{sig_num}_alpha"])
            w0 = float(self.parameters[f"signal_{sig_num}_omega0"])
            poles.append((-a, w0))
            poles.append((-a, -w0))
            zeros.append((-a, 0.0))

        return {"poles": poles, "zeros": zeros}

    # ── Plot construction ─────────────────────────────────────────────

    def _build_plots(
        self,
        t: np.ndarray,
        x1: np.ndarray, sig1_info: Dict,
        x2: Optional[np.ndarray], sig2_info: Optional[Dict],
        result: np.ndarray, result_t: np.ndarray,
        result_info: Dict, needs_second: bool,
        pz_1: Dict, pz_2: Optional[Dict], result_pz: Dict,
        roc_1: Dict, roc_2: Optional[Dict], roc_result: Dict,
        original_poles: Optional[List], shifted_poles: Optional[List],
    ) -> List[Dict[str, Any]]:
        plots = [
            self._line_plot(
                t, x1, sig1_info["label"], "signal_1",
                f"x₁(t) = {sig1_info['label']}", "#3b82f6",
            ),
        ]
        if needs_second and x2 is not None:
            plots.append(
                self._line_plot(
                    t, x2, sig2_info["label"], "signal_2",
                    f"x₂(t) = {sig2_info['label']}", "#ef4444",
                )
            )
        plots.append(
            self._line_plot(
                result_t, result, result_info["label"], "result",
                f"Result: {result_info['label']}", "#14b8a6",
            )
        )
        plots.append(
            self._s_plane_plot(
                pz_1, pz_2, result_pz,
                roc_1, roc_2, roc_result,
                needs_second,
                original_poles, shifted_poles,
            )
        )
        return plots

    def _line_plot(
        self, t: np.ndarray, x: np.ndarray, trace_name: str,
        plot_id: str, title: str, color: str,
    ) -> Dict[str, Any]:
        rev = self._revision
        return {
            "id": plot_id,
            "title": title,
            "data": [{
                "x": t.tolist(),
                "y": x.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": trace_name,
                "line": {"color": color, "width": 2.5},
                "hovertemplate": "t=%{x:.3f}<br>value=%{y:.4f}<extra></extra>",
            }],
            "layout": {
                "xaxis": {
                    "title": {"text": "t (seconds)", "font": {"color": "#f1f5f9", "size": 13}},
                    "gridcolor": "rgba(148,163,184,0.1)",
                    "zerolinecolor": "rgba(148,163,184,0.3)",
                    "color": "#94a3b8",
                    "range": [float(t[0]), float(t[-1])],
                },
                "yaxis": {
                    "title": {"text": "Amplitude", "font": {"color": "#f1f5f9", "size": 13}},
                    "gridcolor": "rgba(148,163,184,0.1)",
                    "zerolinecolor": "rgba(148,163,184,0.3)",
                    "color": "#94a3b8",
                    "autorange": True,
                },
                "paper_bgcolor": "rgba(0,0,0,0)",
                "plot_bgcolor": "rgba(0,0,0,0)",
                "font": {"family": "Inter, sans-serif", "size": 12, "color": "#f1f5f9"},
                "margin": {"t": 45, "r": 25, "b": 55, "l": 60},
                "showlegend": False,
                "datarevision": f"{plot_id}-{rev}",
            },
        }

    def _s_plane_plot(
        self,
        pz_1: Dict, pz_2: Optional[Dict], result_pz: Dict,
        roc_1: Dict, roc_2: Optional[Dict], roc_result: Dict,
        needs_second: bool,
        original_poles: Optional[List], shifted_poles: Optional[List],
    ) -> Dict[str, Any]:
        traces: List[Dict[str, Any]] = []
        all_re = [0.0]
        all_im = [0.0]

        # Collect all points for axis range
        for pz in [pz_1, pz_2, result_pz]:
            if pz is None:
                continue
            for p in pz.get("poles", []) + pz.get("zeros", []):
                all_re.append(p[0])
                all_im.append(abs(p[1]))

        # Also include ROC boundaries in range computation
        for roc in [roc_1, roc_2, roc_result]:
            if roc and roc.get("boundary") is not None:
                all_re.append(roc["boundary"])

        if original_poles:
            for p in original_poles:
                all_re.append(p[0])
                all_im.append(abs(p[1]))

        max_re = max(abs(r) for r in all_re) if all_re else 1.0
        max_im = max(abs(i) for i in all_im) if all_im else 1.0
        axis_lim = max(max(max_re, max_im) * 1.5, 2.5)

        # ── ROC shading for signal 1 ──
        if roc_1["type"] == "right_half" and roc_1.get("boundary") is not None:
            sigma = roc_1["boundary"]
            traces.append({
                "x": [sigma, axis_lim, axis_lim, sigma, sigma],
                "y": [-axis_lim, -axis_lim, axis_lim, axis_lim, -axis_lim],
                "type": "scatter", "mode": "lines",
                "fill": "toself",
                "fillcolor": "rgba(59,130,246,0.06)",
                "line": {"color": "rgba(0,0,0,0)", "width": 0},
                "showlegend": False, "hoverinfo": "skip",
            })
            traces.append({
                "x": [sigma, sigma],
                "y": [-axis_lim, axis_lim],
                "type": "scatter", "mode": "lines",
                "line": {"color": "rgba(59,130,246,0.5)", "width": 1.5, "dash": "dash"},
                "name": f"ROC₁: Re(s)>{sigma:.2g}",
                "hoverinfo": "name",
            })

        # ── ROC shading for signal 2 ──
        if needs_second and roc_2 and roc_2["type"] == "right_half" and roc_2.get("boundary") is not None:
            sigma = roc_2["boundary"]
            traces.append({
                "x": [sigma, axis_lim, axis_lim, sigma, sigma],
                "y": [-axis_lim, -axis_lim, axis_lim, axis_lim, -axis_lim],
                "type": "scatter", "mode": "lines",
                "fill": "toself",
                "fillcolor": "rgba(239,68,68,0.06)",
                "line": {"color": "rgba(0,0,0,0)", "width": 0},
                "showlegend": False, "hoverinfo": "skip",
            })
            traces.append({
                "x": [sigma, sigma],
                "y": [-axis_lim, axis_lim],
                "type": "scatter", "mode": "lines",
                "line": {"color": "rgba(239,68,68,0.5)", "width": 1.5, "dash": "dash"},
                "name": f"ROC₂: Re(s)>{sigma:.2g}",
                "hoverinfo": "name",
            })

        # ── ROC for result ──
        if roc_result["type"] == "right_half" and roc_result.get("boundary") is not None:
            sigma = roc_result["boundary"]
            traces.append({
                "x": [sigma, axis_lim, axis_lim, sigma, sigma],
                "y": [-axis_lim, -axis_lim, axis_lim, axis_lim, -axis_lim],
                "type": "scatter", "mode": "lines",
                "fill": "toself",
                "fillcolor": "rgba(20,184,166,0.08)",
                "line": {"color": "rgba(0,0,0,0)", "width": 0},
                "showlegend": False, "hoverinfo": "skip",
            })
            traces.append({
                "x": [sigma, sigma],
                "y": [-axis_lim, axis_lim],
                "type": "scatter", "mode": "lines",
                "line": {"color": "rgba(20,184,166,0.7)", "width": 2.5},
                "name": f"ROC result: Re(s)>{sigma:.2g}",
                "hoverinfo": "name",
            })

        # ── jω axis (imaginary axis) ──
        traces.append({
            "x": [0, 0],
            "y": [-axis_lim, axis_lim],
            "type": "scatter", "mode": "lines",
            "line": {"color": "#94a3b8", "width": 2},
            "name": "jω axis",
            "hoverinfo": "name",
        })

        # ── Real axis ──
        traces.append({
            "x": [-axis_lim, axis_lim],
            "y": [0, 0],
            "type": "scatter", "mode": "lines",
            "line": {"color": "rgba(148,163,184,0.3)", "width": 1},
            "showlegend": False, "hoverinfo": "skip",
        })

        # ── Poles and zeros ──
        self._add_pz_traces(traces, pz_1, "#3b82f6", "x₁")
        if needs_second and pz_2:
            self._add_pz_traces(traces, pz_2, "#ef4444", "x₂")
        # Result poles/zeros in teal (only for properties that change them)
        if result_pz and (result_pz["poles"] or result_pz["zeros"]):
            prop = self.parameters["property"]
            if prop in ("freq_shift", "differentiate", "integrate"):
                self._add_pz_traces(traces, result_pz, "#14b8a6", "result")

        # ── Frequency shift arrows ──
        annotations = []
        if original_poles and shifted_poles:
            for orig, shifted in zip(original_poles, shifted_poles):
                annotations.append({
                    "x": shifted[0], "y": shifted[1],
                    "ax": orig[0], "ay": orig[1],
                    "xref": "x", "yref": "y",
                    "axref": "x", "ayref": "y",
                    "showarrow": True,
                    "arrowhead": 3,
                    "arrowsize": 1.5,
                    "arrowwidth": 2,
                    "arrowcolor": "#f59e0b",
                })

        rev = self._revision
        return {
            "id": "s_plane",
            "title": "S-Plane: Poles, Zeros & ROC",
            "data": traces,
            "layout": {
                "xaxis": {
                    "title": "Re(s) (σ)",
                    "showgrid": True,
                    "gridcolor": "rgba(148,163,184,0.1)",
                    "zeroline": False,
                    "range": [-axis_lim, axis_lim],
                    "fixedrange": False,
                    "color": "#94a3b8",
                },
                "yaxis": {
                    "title": "Im(s) (jω)",
                    "showgrid": True,
                    "gridcolor": "rgba(148,163,184,0.1)",
                    "zeroline": False,
                    "range": [-axis_lim, axis_lim],
                    "scaleanchor": "x",
                    "scaleratio": 1,
                    "fixedrange": False,
                    "color": "#94a3b8",
                    "constrain": "domain",
                },
                "annotations": annotations,
                "legend": {
                    "x": 0.02, "y": 0.98,
                    "xanchor": "left", "yanchor": "top",
                    "bgcolor": "rgba(10,14,39,0.7)",
                    "bordercolor": "rgba(148,163,184,0.2)",
                    "borderwidth": 1,
                    "font": {"size": 11, "color": "#f1f5f9"},
                },
                "margin": {"l": 60, "r": 30, "t": 50, "b": 50},
                "paper_bgcolor": "rgba(0,0,0,0)",
                "plot_bgcolor": "rgba(0,0,0,0)",
                "font": {"family": "Inter, sans-serif", "size": 12, "color": "#f1f5f9"},
                "datarevision": f"s_plane-{rev}",
                "uirevision": f"s_plane-{rev}",
            },
        }

    @staticmethod
    def _add_pz_traces(
        traces: List[Dict], pz: Dict, color: str, label: str
    ) -> None:
        poles = pz.get("poles", [])
        zeros = pz.get("zeros", [])

        if poles:
            px = [p[0] for p in poles]
            py = [p[1] for p in poles]
            traces.append({
                "x": px, "y": py,
                "type": "scatter", "mode": "markers",
                "name": f"{label} poles",
                "marker": {
                    "symbol": "x",
                    "size": 14,
                    "color": color,
                    "line": {"width": 2.5, "color": color},
                },
                "hovertemplate": f"{label} pole<br>%{{x:.3f}} + %{{y:.3f}}j<extra></extra>",
            })

        if zeros:
            zx = [z[0] for z in zeros]
            zy = [z[1] for z in zeros]
            traces.append({
                "x": zx, "y": zy,
                "type": "scatter", "mode": "markers",
                "name": f"{label} zeros",
                "marker": {
                    "symbol": "circle-open",
                    "size": 14,
                    "color": color,
                    "line": {"width": 2.5, "color": color},
                },
                "hovertemplate": f"{label} zero<br>%{{x:.3f}} + %{{y:.3f}}j<extra></extra>",
            })
