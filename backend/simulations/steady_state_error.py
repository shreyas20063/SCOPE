"""
Steady-State Error Analyzer

Full-featured steady-state error analysis tool for feedback control systems.
Supports unity and non-unity feedback H(s), disturbance rejection, sensitivity
functions, open-loop Bode analysis with gain/phase margins, and all-input
comparison mode.

Core theory (Ogata Ch.5-7, Nise Ch.7, Franklin Ch.6):
- System Type n = number of poles at s=0 in open-loop G(s)H(s)
- Error constants: Kp = lim(s->0) G(s)H(s), Kv = lim(s->0) sG(s)H(s),
  Ka = lim(s->0) s²G(s)H(s)
- Steady-state error: ess = lim(s->0) sE(s) via Final Value Theorem
- Sensitivity: S(s) = 1/(1+GH), T(s) = GH/(1+GH)
- Disturbance rejection: Y_d(s)/D(s) depends on injection point
"""

import time
import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from scipy import signal

from .base_simulator import BaseSimulator


class SteadyStateErrorSimulator(BaseSimulator):
    """Steady-state error analyzer for feedback control systems."""

    # ------------------------------------------------------------------ #
    #  Presets                                                            #
    # ------------------------------------------------------------------ #
    _PRESETS: Dict[str, Dict[str, Any]] = {
        "type0_first":    {"num": [1],       "den": [1, 2],
                           "desc": "Type 0: First-order — K/(s+2)"},
        "type0_second":   {"num": [1],       "den": [1, 4, 3],
                           "desc": "Type 0: Second-order — K/((s+1)(s+3))"},
        "type1_standard": {"num": [1],       "den": [1, 5, 0],
                           "desc": "Type 1: One integrator — K/(s(s+5))"},
        "type1_two_pole": {"num": [1],       "den": [1, 5, 4, 0],
                           "desc": "Type 1: Two poles + integrator — K/(s(s+1)(s+4))"},
        "type2_standard": {"num": [1],       "den": [1, 10, 0, 0],
                           "desc": "Type 2: Two integrators — K/(s²(s+10))"},
        "type2_complex":  {"num": [1],       "den": [1, 7, 10, 0, 0],
                           "desc": "Type 2: Two integrators, two poles — K/(s²(s+2)(s+5))"},
        "type3":          {"num": [1],       "den": [1, 4, 0, 0, 0],
                           "desc": "Type 3: Three integrators — K/(s³(s+4))"},
        "dc_motor_pos":   {"num": [10],      "den": [1, 12, 20, 0],
                           "desc": "DC Motor Position: 10K/(s(s²+12s+20))"},
        "antenna_track":  {"num": [1, 2],    "den": [1, 6, 8, 0],
                           "desc": "Antenna Tracking: K(s+2)/(s(s+2)(s+4))"},
        "thermal":        {"num": [1],       "den": [1, 3, 2],
                           "desc": "Thermal System: K/((s+1)(s+2))"},
        "cruise_control": {"num": [1],       "den": [1, 1, 0],
                           "desc": "Cruise Control: K/(s(s+1))"},
    }

    # ------------------------------------------------------------------ #
    #  Schema & Defaults                                                  #
    # ------------------------------------------------------------------ #
    PARAMETER_SCHEMA = {
        "plant_preset": {
            "type": "select",
            "options": [
                {"value": "type0_first",    "label": "Type 0 — K/(s+2)"},
                {"value": "type0_second",   "label": "Type 0 — K/((s+1)(s+3))"},
                {"value": "type1_standard", "label": "Type 1 — K/(s(s+5))"},
                {"value": "type1_two_pole", "label": "Type 1 — K/(s(s+1)(s+4))"},
                {"value": "type2_standard", "label": "Type 2 — K/(s²(s+10))"},
                {"value": "type2_complex",  "label": "Type 2 — K/(s²(s+2)(s+5))"},
                {"value": "type3",          "label": "Type 3 — K/(s³(s+4))"},
                {"value": "dc_motor_pos",   "label": "DC Motor Position"},
                {"value": "antenna_track",  "label": "Antenna Tracking"},
                {"value": "thermal",        "label": "Thermal System"},
                {"value": "cruise_control", "label": "Cruise Control"},
                {"value": "custom",         "label": "Custom G(s)"},
            ],
            "default": "type1_standard",
        },
        "plant_num": {"type": "expression", "default": "1"},
        "plant_den": {"type": "expression", "default": "1, 5, 0"},
        "gain_K": {
            "type": "slider", "min": 0.1, "max": 200,
            "step": 0.1, "default": 10.0,
        },
        "input_type": {
            "type": "select",
            "options": [
                {"value": "step",      "label": "Step — r(t) = Au(t)"},
                {"value": "ramp",      "label": "Ramp — r(t) = Atu(t)"},
                {"value": "parabolic", "label": "Parabolic — r(t) = ½At²u(t)"},
                {"value": "all",       "label": "All Inputs (Comparison)"},
            ],
            "default": "step",
        },
        "input_magnitude": {
            "type": "slider", "min": 0.1, "max": 10,
            "step": 0.1, "default": 1.0,
        },
        "feedback_type": {
            "type": "select",
            "options": [
                {"value": "unity",  "label": "Unity Feedback: H(s) = 1"},
                {"value": "custom", "label": "Custom H(s)"},
            ],
            "default": "unity",
        },
        "feedback_num": {"type": "expression", "default": "1"},
        "feedback_den": {"type": "expression", "default": "1, 0.1"},
        "disturbance_mode": {
            "type": "select",
            "options": [
                {"value": "none",   "label": "No Disturbance"},
                {"value": "input",  "label": "Input Disturbance (before plant)"},
                {"value": "output", "label": "Output Disturbance (after plant)"},
            ],
            "default": "none",
        },
        "disturbance_magnitude": {
            "type": "slider", "min": 0.0, "max": 5.0,
            "step": 0.1, "default": 1.0,
        },
    }

    DEFAULT_PARAMS: Dict[str, Any] = {
        "plant_preset": "type1_standard",
        "plant_num": "1",
        "plant_den": "1, 5, 0",
        "gain_K": 10.0,
        "input_type": "step",
        "input_magnitude": 1.0,
        "feedback_type": "unity",
        "feedback_num": "1",
        "feedback_den": "1, 0.1",
        "disturbance_mode": "none",
        "disturbance_magnitude": 1.0,
    }

    HUB_SLOTS = ["control"]

    # ------------------------------------------------------------------ #
    #  Lifecycle                                                          #
    # ------------------------------------------------------------------ #
    def initialize(self, params: Optional[Dict[str, Any]] = None) -> None:
        self.parameters = {**self.DEFAULT_PARAMS, **(params or {})}
        for name, value in self.parameters.items():
            self.parameters[name] = self._validate_param(name, value)
        self._initialized = True

    def update_parameter(self, name: str, value: Any) -> Dict[str, Any]:
        if name in self.parameters:
            self.parameters[name] = self._validate_param(name, value)
            if name == "plant_preset" and value != "custom":
                preset = self._PRESETS.get(str(value))
                if preset:
                    self.parameters["plant_num"] = ", ".join(
                        str(c) for c in preset["num"]
                    )
                    self.parameters["plant_den"] = ", ".join(
                        str(c) for c in preset["den"]
                    )
            if name in ("plant_num", "plant_den"):
                self.parameters["plant_preset"] = "custom"
        return self.get_state()

    def reset(self) -> Dict[str, Any]:
        self.parameters = self.DEFAULT_PARAMS.copy()
        self._initialized = True
        return self.get_state()

    # ------------------------------------------------------------------ #
    #  Polynomial helpers                                                 #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _parse_poly(s: str) -> np.ndarray:
        """Parse comma-separated coefficient string to ndarray."""
        try:
            parts = [p.strip() for p in str(s).split(",") if p.strip()]
            coeffs = [float(p) for p in parts]
            if not coeffs:
                return np.array([1.0])
            return np.array(coeffs, dtype=float)
        except (ValueError, TypeError):
            return np.array([1.0])

    @staticmethod
    def _poly_latex(coeffs: np.ndarray) -> str:
        """Convert coefficient array to LaTeX polynomial string."""
        n = len(coeffs) - 1
        terms: List[str] = []
        for i, c in enumerate(coeffs):
            power = n - i
            if abs(c) < 1e-12:
                continue
            abs_c = abs(c)
            if power == 0:
                term = f"{abs_c:g}"
            elif power == 1:
                term = "s" if abs_c == 1.0 else f"{abs_c:g}s"
            else:
                term = f"s^{{{power}}}" if abs_c == 1.0 else f"{abs_c:g}s^{{{power}}}"
            if not terms:
                if c < 0:
                    term = "-" + term
            else:
                term = (" + " + term) if c > 0 else (" - " + term)
            terms.append(term)
        return "".join(terms) if terms else "0"

    def _plant_latex(self, num: np.ndarray, den: np.ndarray,
                     gain_K: float) -> str:
        """Build KaTeX string for G(s) = K * num(s) / den(s)."""
        num_str = self._poly_latex(num)
        den_str = self._poly_latex(den)
        if num_str == "1":
            return f"G(s) = \\frac{{{gain_K:g}}}{{{den_str}}}"
        return f"G(s) = \\frac{{{gain_K:g}({num_str})}}{{{den_str}}}"

    # ------------------------------------------------------------------ #
    #  Transfer function extraction                                       #
    # ------------------------------------------------------------------ #
    def _get_plant_tf(self) -> Tuple[np.ndarray, np.ndarray]:
        """Return (num, den) with gain K applied to numerator."""
        preset = str(self.parameters["plant_preset"])
        K = float(self.parameters["gain_K"])

        if preset != "custom" and preset in self._PRESETS:
            p = self._PRESETS[preset]
            num_base = np.array(p["num"], dtype=float)
            den = np.array(p["den"], dtype=float)
        else:
            num_base = self._parse_poly(self.parameters["plant_num"])
            den = self._parse_poly(self.parameters["plant_den"])

        num = K * num_base

        # Validate properness
        if len(np.trim_zeros(num, "f")) > len(np.trim_zeros(den, "f")):
            num = np.array([1.0])
            den = np.array([1.0, 1.0])

        return num, den

    def _get_feedback_tf(self) -> Tuple[np.ndarray, np.ndarray]:
        """Return feedback path H(s) = h_num/h_den."""
        if str(self.parameters["feedback_type"]) == "unity":
            return np.array([1.0]), np.array([1.0])
        h_num = self._parse_poly(self.parameters["feedback_num"])
        h_den = self._parse_poly(self.parameters["feedback_den"])
        return h_num, h_den

    def _get_num_base(self) -> np.ndarray:
        """Return unscaled numerator (before K)."""
        preset = str(self.parameters["plant_preset"])
        if preset != "custom" and preset in self._PRESETS:
            return np.array(self._PRESETS[preset]["num"], dtype=float)
        return self._parse_poly(self.parameters["plant_num"])

    # ------------------------------------------------------------------ #
    #  System type & error constants                                      #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _count_origin_poles(den: np.ndarray) -> int:
        """Count trailing near-zero coefficients (poles at s=0)."""
        count = 0
        for c in reversed(den):
            if abs(c) < 1e-10:
                count += 1
            else:
                break
        return count

    @staticmethod
    def _cancel_common_s(num: np.ndarray,
                         den: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Cancel common s=0 factors between numerator and denominator."""
        n_num = 0
        for c in reversed(num):
            if abs(c) < 1e-10:
                n_num += 1
            else:
                break
        n_den = 0
        for c in reversed(den):
            if abs(c) < 1e-10:
                n_den += 1
            else:
                break
        common = min(n_num, n_den)
        if common == 0:
            return num.copy(), den.copy()
        num_r = num[:len(num) - common]
        den_r = den[:len(den) - common]
        if len(num_r) == 0:
            num_r = np.array([1.0])
        if len(den_r) == 0:
            den_r = np.array([1.0])
        return num_r, den_r

    @staticmethod
    def _error_constants(num: np.ndarray, den: np.ndarray,
                         sys_type: int) -> Dict[str, Any]:
        """Compute Kp, Kv, Ka error constants."""
        if sys_type > 0:
            den_r = den[:len(den) - sys_type]
        else:
            den_r = den

        num_at_0 = np.polyval(num, 0.0)
        den_at_0 = np.polyval(den_r, 0.0)
        K_static = num_at_0 / den_at_0 if abs(den_at_0) > 1e-15 else 0.0

        if sys_type == 0:
            return {"Kp": K_static, "Kv": 0.0, "Ka": 0.0, "K_static": K_static}
        elif sys_type == 1:
            return {"Kp": float("inf"), "Kv": K_static, "Ka": 0.0, "K_static": K_static}
        elif sys_type == 2:
            return {"Kp": float("inf"), "Kv": float("inf"), "Ka": K_static, "K_static": K_static}
        else:
            return {"Kp": float("inf"), "Kv": float("inf"), "Ka": float("inf"), "K_static": K_static}

    @staticmethod
    def _ess_values(ec: Dict[str, Any], sys_type: int,
                    A: float) -> Dict[str, float]:
        """Compute ess for step, ramp, parabolic."""
        Kp, Kv, Ka = ec["Kp"], ec["Kv"], ec["Ka"]

        step = A / (1.0 + Kp) if sys_type == 0 and Kp != float("inf") else (
            0.0 if sys_type > 0 else A / (1.0 + Kp))

        if sys_type == 0:
            ramp = float("inf")
        elif sys_type == 1:
            ramp = 0.0 if Kv == float("inf") else (
                float("inf") if abs(Kv) < 1e-15 else A / Kv)
        else:
            ramp = 0.0

        if sys_type <= 1:
            para = float("inf")
        elif sys_type == 2:
            para = 0.0 if Ka == float("inf") else (
                float("inf") if abs(Ka) < 1e-15 else A / Ka)
        else:
            para = 0.0

        return {"step": step, "ramp": ramp, "parabolic": para}

    # ------------------------------------------------------------------ #
    #  Closed-loop & loop transfer functions                              #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _loop_tf(g_num: np.ndarray, g_den: np.ndarray,
                 h_num: np.ndarray, h_den: np.ndarray
                 ) -> Tuple[np.ndarray, np.ndarray]:
        """Compute L(s) = G(s)H(s) as num_L/den_L."""
        num_L = np.polymul(g_num, h_num)
        den_L = np.polymul(g_den, h_den)
        return num_L, den_L

    @staticmethod
    def _cl_poles(g_num: np.ndarray, g_den: np.ndarray,
                  h_num: np.ndarray, h_den: np.ndarray
                  ) -> Tuple[np.ndarray, bool, np.ndarray]:
        """Compute CL poles: char poly = den_G·den_H + num_G·num_H.

        Returns (poles, is_stable, cl_char_poly).
        """
        char_poly = np.polyadd(
            np.polymul(g_den, h_den),
            np.polymul(g_num, h_num),
        )
        char_poly = np.trim_zeros(char_poly, "f")
        if len(char_poly) == 0:
            char_poly = np.array([1.0])

        poles = np.roots(char_poly)
        stable = bool(np.all(np.real(poles) < -1e-6)) if len(poles) > 0 else True
        return poles, stable, char_poly

    @staticmethod
    def _cl_tf(g_num: np.ndarray, g_den: np.ndarray,
               h_num: np.ndarray, h_den: np.ndarray
               ) -> Tuple[np.ndarray, np.ndarray]:
        """Closed-loop TF: T(s) = G/(1+GH), num_cl/den_cl."""
        num_cl = np.polymul(g_num, h_den)
        den_cl = np.polyadd(
            np.polymul(g_den, h_den),
            np.polymul(g_num, h_num),
        )
        den_cl = np.trim_zeros(den_cl, "f")
        if len(den_cl) == 0:
            den_cl = np.array([1.0])
        return num_cl, den_cl

    # ------------------------------------------------------------------ #
    #  Gain & phase margins                                               #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _compute_margins(num_L: np.ndarray,
                         den_L: np.ndarray) -> Dict[str, Any]:
        """Compute gain margin, phase margin, and crossover frequencies."""
        try:
            sys_L = signal.TransferFunction(num_L, den_L)
            w = np.logspace(-3, 4, 2000)
            w, H_resp = signal.freqresp(sys_L, w)

            mag = np.abs(H_resp)
            phase_deg = np.degrees(np.unwrap(np.angle(H_resp)))

            # Gain crossover: |L(jw)| = 1 (0 dB)
            gc_idx = None
            for i in range(len(mag) - 1):
                if (mag[i] >= 1.0 and mag[i + 1] < 1.0) or \
                   (mag[i] <= 1.0 and mag[i + 1] > 1.0):
                    # Linear interpolation
                    frac = (1.0 - mag[i]) / (mag[i + 1] - mag[i])
                    gc_idx = i
                    w_gc = w[i] + frac * (w[i + 1] - w[i])
                    phase_gc = phase_deg[i] + frac * (phase_deg[i + 1] - phase_deg[i])
                    break

            # Phase crossover: angle(L(jw)) = -180°
            pc_idx = None
            for i in range(len(phase_deg) - 1):
                if (phase_deg[i] >= -180 and phase_deg[i + 1] < -180) or \
                   (phase_deg[i] <= -180 and phase_deg[i + 1] > -180):
                    frac = (-180 - phase_deg[i]) / (phase_deg[i + 1] - phase_deg[i])
                    pc_idx = i
                    w_pc = w[i] + frac * (w[i + 1] - w[i])
                    mag_pc = mag[i] + frac * (mag[i + 1] - mag[i])
                    break

            result: Dict[str, Any] = {
                "w": w.tolist(),
                "mag_db": (20 * np.log10(np.maximum(mag, 1e-20))).tolist(),
                "phase_deg": phase_deg.tolist(),
            }

            if gc_idx is not None:
                pm = 180.0 + phase_gc
                result["PM"] = float(pm)
                result["w_gc"] = float(w_gc)
            else:
                result["PM"] = float("inf")
                result["w_gc"] = None

            if pc_idx is not None:
                gm = -20 * np.log10(max(mag_pc, 1e-20))
                result["GM"] = float(gm)
                result["w_pc"] = float(w_pc)
            else:
                result["GM"] = float("inf")
                result["w_pc"] = None

            return result
        except Exception:
            return {"w": [], "mag_db": [], "phase_deg": [],
                    "PM": None, "GM": None, "w_gc": None, "w_pc": None}

    # ------------------------------------------------------------------ #
    #  Sensitivity functions                                              #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _sensitivity_bode(num_L: np.ndarray,
                          den_L: np.ndarray) -> Dict[str, Any]:
        """Compute S(jw) and T(jw) frequency responses.

        S(s) = 1/(1+L), T(s) = L/(1+L) where L = GH.
        """
        try:
            sys_L = signal.TransferFunction(num_L, den_L)
            w = np.logspace(-3, 4, 1000)
            w, L_resp = signal.freqresp(sys_L, w)

            S = 1.0 / (1.0 + L_resp)
            T = L_resp / (1.0 + L_resp)

            S_mag_db = 20 * np.log10(np.maximum(np.abs(S), 1e-20))
            T_mag_db = 20 * np.log10(np.maximum(np.abs(T), 1e-20))

            # Peak sensitivity (robustness indicator)
            Ms = float(np.max(np.abs(S)))
            Mt = float(np.max(np.abs(T)))

            return {
                "w": w.tolist(),
                "S_db": S_mag_db.tolist(),
                "T_db": T_mag_db.tolist(),
                "Ms": Ms,
                "Mt": Mt,
                "Ms_db": float(20 * np.log10(max(Ms, 1e-20))),
                "Mt_db": float(20 * np.log10(max(Mt, 1e-20))),
            }
        except Exception:
            return {"w": [], "S_db": [], "T_db": [],
                    "Ms": None, "Mt": None, "Ms_db": None, "Mt_db": None}

    # ------------------------------------------------------------------ #
    #  Time-domain simulation                                             #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _simulate(num_cl: np.ndarray, den_cl: np.ndarray,
                  input_type: str, A: float, t_end: float,
                  is_stable: bool) -> Dict[str, Any]:
        """Simulate closed-loop time response."""
        n_pts = 500
        t = np.linspace(0, t_end, n_pts)
        diverged = False

        try:
            sys_cl = signal.TransferFunction(num_cl, den_cl)
            if input_type == "step":
                _, y = signal.step(sys_cl, T=t)
                y = A * y
                r = np.full_like(t, A)
            elif input_type == "ramp":
                U = A * t
                _, y, _ = signal.lsim(sys_cl, U=U, T=t)
                r = U
            else:  # parabolic
                U = A * t ** 2 / 2.0
                _, y, _ = signal.lsim(sys_cl, U=U, T=t)
                r = U

            if np.any(np.abs(y) > 1e4):
                diverged = True
                y = np.clip(y, -1e4, 1e4)
            e = r - y
        except Exception:
            y = np.zeros_like(t)
            r = np.full_like(t, A) if input_type == "step" else (
                A * t if input_type == "ramp" else A * t ** 2 / 2.0)
            e = r - y
            diverged = True

        return {"t": t, "y": y, "r": r, "e": e, "diverged": diverged}

    @staticmethod
    def _simulate_disturbance(g_num: np.ndarray, g_den: np.ndarray,
                              h_num: np.ndarray, h_den: np.ndarray,
                              mode: str, d_mag: float,
                              t_end: float) -> Optional[Dict[str, Any]]:
        """Simulate disturbance rejection response.

        Input disturbance: Y_d/D = G/(1+GH)
        Output disturbance: Y_d/D = 1/(1+GH)
        """
        if mode == "none" or d_mag == 0:
            return None

        n_pts = 500
        t = np.linspace(0, t_end, n_pts)

        try:
            if mode == "input":
                # D enters before plant: Y_d/D = G/(1+GH)
                num_d = np.polymul(g_num, h_den)
            else:
                # D enters after plant: Y_d/D = 1/(1+GH) = den_G·den_H / char
                num_d = np.polymul(g_den, h_den)

            den_d = np.polyadd(
                np.polymul(g_den, h_den),
                np.polymul(g_num, h_num),
            )
            den_d = np.trim_zeros(den_d, "f")
            if len(den_d) == 0:
                den_d = np.array([1.0])

            sys_d = signal.TransferFunction(num_d, den_d)
            _, y_d = signal.step(sys_d, T=t)
            y_d = d_mag * y_d

            if np.any(np.abs(y_d) > 1e4):
                y_d = np.clip(y_d, -1e4, 1e4)

            return {"t": t, "y_d": y_d, "mode": mode, "d_mag": d_mag}
        except Exception:
            return None

    # ------------------------------------------------------------------ #
    #  Performance metrics                                                #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _step_metrics(t: np.ndarray, y: np.ndarray,
                      A: float, is_stable: bool) -> Dict[str, Any]:
        """Compute step response performance metrics."""
        metrics: Dict[str, Any] = {}
        if not is_stable or A == 0:
            return metrics

        y_final = A  # target for unity-DC-gain CL
        y_norm = y / A if abs(A) > 1e-12 else y

        # Rise time (10% to 90%)
        try:
            t_10 = t[np.argmax(y_norm >= 0.1)] if np.any(y_norm >= 0.1) else None
            t_90 = t[np.argmax(y_norm >= 0.9)] if np.any(y_norm >= 0.9) else None
            if t_10 is not None and t_90 is not None and t_90 > t_10:
                metrics["rise_time"] = float(t_90 - t_10)
        except (ValueError, IndexError):
            pass

        # Overshoot
        y_max = float(np.max(y))
        if y_max > y_final * 1.001:
            metrics["overshoot"] = float((y_max - y_final) / y_final * 100)
            metrics["peak_time"] = float(t[np.argmax(y)])
        else:
            metrics["overshoot"] = 0.0

        # Settling time (2% band)
        try:
            in_band = np.abs(y - y_final) <= 0.02 * abs(y_final)
            if np.any(in_band):
                # Find last time outside band
                outside = np.where(~in_band)[0]
                if len(outside) > 0:
                    metrics["settling_time"] = float(t[outside[-1]])
                else:
                    metrics["settling_time"] = 0.0
        except (ValueError, IndexError):
            pass

        return metrics

    @staticmethod
    def _estimate_t_end(cl_poles: np.ndarray, is_stable: bool) -> float:
        """Estimate simulation time from CL poles."""
        if not is_stable or len(cl_poles) == 0:
            return 10.0
        reals = np.real(cl_poles)
        stable_r = reals[reals < -1e-10]
        if len(stable_r) == 0:
            return 10.0
        slowest = np.min(np.abs(stable_r))
        return float(np.clip(5.0 / slowest, 2.0, 50.0))

    # ------------------------------------------------------------------ #
    #  ess vs K sweep                                                     #
    # ------------------------------------------------------------------ #
    def _ess_vs_K(self, num_base: np.ndarray, den: np.ndarray,
                  h_num: np.ndarray, h_den: np.ndarray,
                  A: float) -> Dict[str, Any]:
        """Sweep K and compute ess + stability for each input type."""
        K_vals = np.logspace(-1, np.log10(200), 100).tolist()
        step_list: List[Optional[float]] = []
        ramp_list: List[Optional[float]] = []
        para_list: List[Optional[float]] = []
        stable_list: List[bool] = []

        for K in K_vals:
            num_k = K * num_base
            # For error constants, use the loop TF = GH
            L_num, L_den = self._loop_tf(num_k, den, h_num, h_den)
            L_num_eff, L_den_eff = self._cancel_common_s(L_num, L_den)
            sys_t = self._count_origin_poles(L_den_eff)
            ec = self._error_constants(L_num_eff, L_den_eff, sys_t)
            errors = self._ess_values(ec, sys_t, A)
            _, is_s, _ = self._cl_poles(num_k, den, h_num, h_den)

            stable_list.append(is_s)
            for key, lst in [("step", step_list), ("ramp", ramp_list),
                             ("parabolic", para_list)]:
                v = errors[key]
                lst.append(None if v == float("inf") else min(v, 1000.0))

        return {"K_values": K_vals, "step_ess": step_list,
                "ramp_ess": ramp_list, "parabolic_ess": para_list,
                "stable": stable_list}

    # ------------------------------------------------------------------ #
    #  FVT LaTeX                                                          #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _fvt_latex(input_type: str, sys_type: int,
                   ec: Dict[str, Any], A: float,
                   ess: float, is_stable: bool,
                   is_unity: bool) -> str:
        """Build FVT derivation LaTeX."""
        lines: List[str] = []
        if not is_stable:
            lines.append(r"e_{ss} = \lim_{s \to 0} s \cdot E(s)")
            lines.append(r"\text{FVT invalid — closed-loop system is unstable}")
            return " \\\\ ".join(lines)

        fb = "" if is_unity else "H(s)"
        lines.append(r"e_{ss} = \lim_{t \to \infty} e(t) = \lim_{s \to 0} s\,E(s)")
        if is_unity:
            lines.append(r"E(s) = \frac{R(s)}{1 + G(s)}")
            lines.append(r"\therefore\; e_{ss} = \lim_{s \to 0} \frac{s \cdot R(s)}{1 + G(s)}")
        else:
            lines.append(r"E(s) = R(s) - H(s)Y(s) = \frac{R(s)}{1 + G(s)H(s)}")
            lines.append(r"\therefore\; e_{ss} = \lim_{s \to 0} \frac{s \cdot R(s)}{1 + G(s)H(s)}")

        if input_type == "step":
            Kp = ec["Kp"]
            lines.append(
                r"= \lim_{s \to 0} \frac{s \cdot \frac{" + f"{A:g}"
                + r"}{s}}{1 + G" + (r"H" if not is_unity else "")
                + r"} = \frac{" + f"{A:g}" + r"}{1 + K_p}"
            )
            if sys_type == 0 and Kp != float("inf"):
                lines.append(f"= \\frac{{{A:g}}}{{1 + {Kp:.4g}}} = {ess:.4g}")
            else:
                lines.append("= 0")
        elif input_type == "ramp":
            Kv = ec["Kv"]
            lines.append(
                r"= \lim_{s \to 0} \frac{s \cdot \frac{" + f"{A:g}"
                + r"}{s^2}}{1 + G" + (r"H" if not is_unity else "")
                + r"} = \frac{" + f"{A:g}" + r"}{K_v}"
            )
            if sys_type == 0:
                lines.append(r"= \infty \quad (K_v = 0 \text{ for Type 0})")
            elif sys_type == 1 and Kv != float("inf") and Kv != 0:
                lines.append(f"= \\frac{{{A:g}}}{{{Kv:.4g}}} = {ess:.4g}")
            else:
                lines.append("= 0")
        else:  # parabolic
            Ka = ec["Ka"]
            lines.append(
                r"= \lim_{s \to 0} \frac{s \cdot \frac{" + f"{A:g}"
                + r"}{s^3}}{1 + G" + (r"H" if not is_unity else "")
                + r"} = \frac{" + f"{A:g}" + r"}{K_a}"
            )
            if sys_type <= 1:
                lines.append(r"= \infty \quad (K_a = 0 \text{ for Type }" + f"{sys_type})")
            elif sys_type == 2 and Ka != float("inf") and Ka != 0:
                lines.append(f"= \\frac{{{A:g}}}{{{Ka:.4g}}} = {ess:.4g}")
            else:
                lines.append("= 0")

        return " \\\\ ".join(lines)

    # ------------------------------------------------------------------ #
    #  Display helpers                                                    #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _dv(v: float) -> str:
        """Format value for display (inf → ∞)."""
        if v == float("inf"):
            return "\u221e"
        if v == 0.0:
            return "0"
        return f"{v:.4g}"

    # ------------------------------------------------------------------ #
    #  Plot builders                                                      #
    # ------------------------------------------------------------------ #
    def _layout(self, pid: str, title: str,
                xt: str = "", yt: str = "", **kw: Any) -> Dict[str, Any]:
        """Base Plotly layout."""
        lay: Dict[str, Any] = {
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "font": {"family": "Inter, sans-serif", "size": 12,
                      "color": "#f1f5f9"},
            "margin": {"t": 40, "r": 25, "b": 55, "l": 60},
            "xaxis": {"title": xt, "gridcolor": "rgba(148,163,184,0.1)",
                      "zerolinecolor": "rgba(148,163,184,0.3)"},
            "yaxis": {"title": yt, "gridcolor": "rgba(148,163,184,0.1)",
                      "zerolinecolor": "rgba(148,163,184,0.3)"},
            "legend": {"x": 0.98, "y": 0.98, "xanchor": "right",
                       "yanchor": "top", "bgcolor": "rgba(0,0,0,0)"},
            "uirevision": pid,
            "datarevision": f"{pid}-{time.time()}",
        }
        lay.update(kw)
        return lay

    def _plot_time_response(self, sims: Dict[str, Dict],
                            input_type: str, ss_errors: Dict,
                            is_stable: bool) -> Dict[str, Any]:
        """Plot 1: Time response (single or all-inputs comparison)."""
        data: List[Dict] = []
        annotations: List[Dict] = []

        if input_type == "all":
            colors = {"step": "#3b82f6", "ramp": "#ef4444", "parabolic": "#10b981"}
            labels = {"step": "Step", "ramp": "Ramp", "parabolic": "Parabolic"}
            for itype in ["step", "ramp", "parabolic"]:
                sim = sims.get(itype)
                if not sim:
                    continue
                t = sim["t"].tolist()
                data.append({"x": t, "y": sim["r"].tolist(), "type": "scatter",
                             "mode": "lines", "name": f"r(t) {labels[itype]}",
                             "line": {"color": colors[itype], "width": 1.5, "dash": "dash"},
                             "legendgroup": itype})
                data.append({"x": t, "y": sim["y"].tolist(), "type": "scatter",
                             "mode": "lines", "name": f"y(t) {labels[itype]}",
                             "line": {"color": colors[itype], "width": 2},
                             "legendgroup": itype})
            title = "All Inputs — Response Comparison"
        else:
            sim = sims[input_type]
            t = sim["t"].tolist()
            label = {"step": "Step", "ramp": "Ramp", "parabolic": "Parabolic"}[input_type]
            data = [
                {"x": t, "y": sim["r"].tolist(), "type": "scatter", "mode": "lines",
                 "name": "Reference r(t)", "line": {"color": "#3b82f6", "width": 2, "dash": "dash"}},
                {"x": t, "y": sim["y"].tolist(), "type": "scatter", "mode": "lines",
                 "name": "Output y(t)", "line": {"color": "#ef4444", "width": 2}},
            ]
            title = f"System Response ({label} Input)"

            ess = ss_errors.get(input_type, 0)
            if not is_stable or sim["diverged"]:
                annotations.append({
                    "x": 0.5, "y": 0.95, "xref": "paper", "yref": "paper",
                    "text": "UNSTABLE — FVT invalid", "showarrow": False,
                    "font": {"size": 14, "color": "#ef4444"},
                    "bgcolor": "rgba(239,68,68,0.15)",
                    "bordercolor": "#ef4444", "borderwidth": 1})
            elif 0 < ess < float("inf"):
                annotations.append({
                    "x": t[-1], "y": (sim["y"][-1] + sim["r"][-1]) / 2,
                    "text": f"e_ss = {ess:.3g}", "showarrow": True,
                    "arrowhead": 0, "arrowwidth": 2, "arrowcolor": "#10b981",
                    "font": {"color": "#10b981", "size": 11}})

        lay = self._layout("time_response", title, xt="Time (s)", yt="Amplitude")
        lay["annotations"] = annotations
        return {"id": "time_response", "title": title, "data": data, "layout": lay}

    def _plot_error(self, sims: Dict[str, Dict], input_type: str,
                    ss_errors: Dict, is_stable: bool) -> Dict[str, Any]:
        """Plot 2: Error signal(s)."""
        data: List[Dict] = []
        annotations: List[Dict] = []

        if input_type == "all":
            colors = {"step": "#3b82f6", "ramp": "#ef4444", "parabolic": "#10b981"}
            labels = {"step": "Step", "ramp": "Ramp", "parabolic": "Parabolic"}
            for itype in ["step", "ramp", "parabolic"]:
                sim = sims.get(itype)
                if not sim:
                    continue
                t = sim["t"].tolist()
                data.append({"x": t, "y": sim["e"].tolist(), "type": "scatter",
                             "mode": "lines", "name": f"e(t) {labels[itype]}",
                             "line": {"color": colors[itype], "width": 2}})
        else:
            sim = sims[input_type]
            t = sim["t"].tolist()
            data.append({"x": t, "y": sim["e"].tolist(), "type": "scatter",
                         "mode": "lines", "name": "Error e(t)",
                         "line": {"color": "#f59e0b", "width": 2}})
            ess = ss_errors.get(input_type, 0)
            if 0 < ess < float("inf") and is_stable:
                data.append({"x": [t[0], t[-1]], "y": [ess, ess], "type": "scatter",
                             "mode": "lines", "name": f"e_ss = {ess:.3g}",
                             "line": {"color": "#10b981", "width": 1.5, "dash": "dash"}})
            elif ess == float("inf"):
                annotations.append({"x": 0.5, "y": 0.92, "xref": "paper", "yref": "paper",
                                    "text": "e(t) → ∞", "showarrow": False,
                                    "font": {"size": 13, "color": "#f59e0b"}})
            elif ess == 0.0 and is_stable:
                annotations.append({"x": 0.5, "y": 0.92, "xref": "paper", "yref": "paper",
                                    "text": "e(t) → 0", "showarrow": False,
                                    "font": {"size": 13, "color": "#10b981"}})

        lay = self._layout("error_signal", "Error Signal e(t)", xt="Time (s)", yt="Error")
        lay["annotations"] = annotations
        return {"id": "error_signal", "title": "Error Signal e(t)", "data": data, "layout": lay}

    def _plot_ess_vs_K(self, ess_data: Dict, K: float) -> Dict[str, Any]:
        """Plot 3: ess vs K (log-log) with stability shading."""
        data: List[Dict] = []
        K_vals = ess_data["K_values"]

        for key, name, color in [("step_ess", "Step e_ss", "#3b82f6"),
                                  ("ramp_ess", "Ramp e_ss", "#ef4444"),
                                  ("parabolic_ess", "Parabolic e_ss", "#10b981")]:
            vals = ess_data[key]
            if any(v is not None and v > 0 for v in vals):
                data.append({"x": K_vals, "y": vals, "type": "scatter",
                             "mode": "lines", "name": name,
                             "line": {"color": color, "width": 2},
                             "connectgaps": False})

        # Current K line
        data.append({"x": [K, K], "y": [0.001, 1000], "type": "scatter",
                     "mode": "lines", "name": f"K = {K:g}",
                     "line": {"color": "#14b8a6", "width": 1.5, "dash": "dash"}})

        # Unstable region shading
        shapes: List[Dict] = []
        flags = ess_data["stable"]
        us = None
        for i, (k, s) in enumerate(zip(K_vals, flags)):
            if not s and us is None:
                us = k
            elif s and us is not None:
                shapes.append({"type": "rect", "xref": "x", "yref": "paper",
                               "x0": us, "x1": k, "y0": 0, "y1": 1,
                               "fillcolor": "rgba(239,68,68,0.08)", "line": {"width": 0},
                               "layer": "below"})
                us = None
        if us is not None:
            shapes.append({"type": "rect", "xref": "x", "yref": "paper",
                           "x0": us, "x1": K_vals[-1], "y0": 0, "y1": 1,
                           "fillcolor": "rgba(239,68,68,0.08)", "line": {"width": 0},
                           "layer": "below"})

        lay = self._layout("ess_vs_gain", "Steady-State Error vs Gain K",
                           xt="Gain K", yt="e_ss")
        lay["xaxis"]["type"] = "log"
        lay["yaxis"]["type"] = "log"
        lay["shapes"] = shapes
        return {"id": "ess_vs_gain", "title": "Steady-State Error vs Gain K",
                "data": data, "layout": lay}

    def _plot_poles(self, g_num: np.ndarray, g_den: np.ndarray,
                    cl_poles: np.ndarray, sys_type: int,
                    is_stable: bool) -> Dict[str, Any]:
        """Plot 4: OL + CL pole-zero map."""
        data: List[Dict] = []
        num_t = np.trim_zeros(g_num, "f")
        ol_z = np.roots(num_t) if len(num_t) > 1 else np.array([])
        den_t = np.trim_zeros(g_den, "f")
        ol_p = np.roots(den_t) if len(den_t) > 1 else np.array([])

        if len(ol_z) > 0:
            data.append({"x": np.real(ol_z).tolist(), "y": np.imag(ol_z).tolist(),
                         "type": "scatter", "mode": "markers", "name": "OL Zeros",
                         "marker": {"symbol": "circle-open", "size": 12, "color": "#10b981",
                                    "line": {"width": 2, "color": "#10b981"}}})
        # OL poles: separate origin
        non_orig = ol_p[np.abs(ol_p) > 1e-8]
        orig = ol_p[np.abs(ol_p) <= 1e-8]
        if len(non_orig) > 0:
            data.append({"x": np.real(non_orig).tolist(), "y": np.imag(non_orig).tolist(),
                         "type": "scatter", "mode": "markers", "name": "OL Poles",
                         "marker": {"symbol": "x", "size": 12, "color": "#ef4444",
                                    "line": {"width": 2, "color": "#ef4444"}}})
        n_orig = len(orig)
        if n_orig > 0:
            data.append({"x": [0.0], "y": [0.0], "type": "scatter",
                         "mode": "markers+text",
                         "name": f"OL Poles at origin (×{n_orig})",
                         "marker": {"symbol": "x", "size": 16, "color": "#ef4444",
                                    "line": {"width": 3, "color": "#ef4444"}},
                         "text": [f"×{n_orig}"], "textposition": "top right",
                         "textfont": {"color": "#ef4444", "size": 11}})
        if len(cl_poles) > 0:
            cl_re = np.real(cl_poles)
            cl_im = np.imag(cl_poles)
            cl_colors = ["#10b981" if r < -1e-6 else "#ef4444" for r in cl_re]
            data.append({"x": cl_re.tolist(), "y": cl_im.tolist(),
                         "type": "scatter", "mode": "markers", "name": "CL Poles",
                         "marker": {"symbol": "circle", "size": 10, "color": cl_colors,
                                    "line": {"width": 1, "color": cl_colors}}})

        all_re = np.concatenate([np.real(x) for x in [ol_p, ol_z, cl_poles] if len(x)])
        all_im = np.concatenate([np.imag(x) for x in [ol_p, ol_z, cl_poles] if len(x)])
        rr = max(float(np.max(np.abs(all_re))) if len(all_re) else 2.0, 1.0) * 1.3
        ir = max(float(np.max(np.abs(all_im))) if len(all_im) else 2.0, 1.0) * 1.3

        data.append({"x": [0, 0], "y": [-ir, ir], "type": "scatter", "mode": "lines",
                     "name": "jω axis", "line": {"color": "rgba(148,163,184,0.4)",
                     "width": 1, "dash": "dash"}, "showlegend": False})

        lay = self._layout("pole_zero_map", f"Pole-Zero Map (Type {sys_type})",
                           xt="Real", yt="Imaginary")
        lay["xaxis"]["range"] = [-rr, rr]
        lay["yaxis"]["range"] = [-ir, ir]
        lay["xaxis"]["scaleanchor"] = "y"
        return {"id": "pole_zero_map", "title": f"Pole-Zero Map (Type {sys_type})",
                "data": data, "layout": lay}

    def _plot_bode(self, margins: Dict) -> Dict[str, Any]:
        """Plot 5: Open-loop Bode (magnitude + phase) with GM/PM markers."""
        w = margins.get("w", [])
        mag_db = margins.get("mag_db", [])
        phase = margins.get("phase_deg", [])

        data: List[Dict] = []
        annotations: List[Dict] = []
        shapes: List[Dict] = []

        if w:
            # Magnitude
            data.append({"x": w, "y": mag_db, "type": "scatter", "mode": "lines",
                         "name": "|L(jω)| dB", "line": {"color": "#3b82f6", "width": 2},
                         "yaxis": "y"})
            # Phase
            data.append({"x": w, "y": phase, "type": "scatter", "mode": "lines",
                         "name": "∠L(jω) deg", "line": {"color": "#ef4444", "width": 2},
                         "yaxis": "y2"})

            # 0 dB reference
            shapes.append({"type": "line", "xref": "x", "yref": "y",
                           "x0": w[0], "x1": w[-1], "y0": 0, "y1": 0,
                           "line": {"color": "rgba(148,163,184,0.4)", "width": 1, "dash": "dash"},
                           "layer": "below"})
            # -180° reference
            shapes.append({"type": "line", "xref": "x", "yref": "y2",
                           "x0": w[0], "x1": w[-1], "y0": -180, "y1": -180,
                           "line": {"color": "rgba(148,163,184,0.4)", "width": 1, "dash": "dash"},
                           "layer": "below"})

            # GM marker
            w_pc = margins.get("w_pc")
            gm = margins.get("GM")
            if w_pc and gm and gm != float("inf"):
                data.append({"x": [w_pc, w_pc], "y": [0, -abs(gm) if gm > 0 else abs(gm)],
                             "type": "scatter", "mode": "lines+markers",
                             "name": f"GM = {gm:.1f} dB",
                             "line": {"color": "#10b981", "width": 2},
                             "marker": {"size": 8, "color": "#10b981"}})

            # PM marker
            w_gc = margins.get("w_gc")
            pm = margins.get("PM")
            if w_gc and pm and pm != float("inf"):
                data.append({"x": [w_gc, w_gc], "y": [-180, -180 + pm],
                             "type": "scatter", "mode": "lines+markers",
                             "name": f"PM = {pm:.1f}°",
                             "line": {"color": "#f59e0b", "width": 2},
                             "marker": {"size": 8, "color": "#f59e0b"},
                             "yaxis": "y2"})

        lay = self._layout("bode_ol", "Open-Loop Bode — L(s) = G(s)H(s)",
                           xt="Frequency (rad/s)", yt="Magnitude (dB)")
        lay["xaxis"]["type"] = "log"
        lay["yaxis"]["side"] = "left"
        lay["yaxis2"] = {
            "title": "Phase (deg)", "side": "right", "overlaying": "y",
            "gridcolor": "rgba(148,163,184,0.05)",
            "zerolinecolor": "rgba(148,163,184,0.2)",
            "titlefont": {"color": "#ef4444"},
            "tickfont": {"color": "#ef4444"},
        }
        lay["shapes"] = shapes
        lay["annotations"] = annotations
        return {"id": "bode_ol", "title": "Open-Loop Bode — L(s) = G(s)H(s)",
                "data": data, "layout": lay}

    def _plot_sensitivity(self, sens: Dict) -> Dict[str, Any]:
        """Plot 6: Sensitivity S(jw) and complementary sensitivity T(jw)."""
        w = sens.get("w", [])
        S_db = sens.get("S_db", [])
        T_db = sens.get("T_db", [])

        data: List[Dict] = []
        shapes: List[Dict] = []

        if w:
            data.append({"x": w, "y": S_db, "type": "scatter", "mode": "lines",
                         "name": "|S(jω)| dB", "line": {"color": "#3b82f6", "width": 2}})
            data.append({"x": w, "y": T_db, "type": "scatter", "mode": "lines",
                         "name": "|T(jω)| dB", "line": {"color": "#ef4444", "width": 2}})
            # 0 dB line
            shapes.append({"type": "line", "xref": "x", "yref": "y",
                           "x0": w[0], "x1": w[-1], "y0": 0, "y1": 0,
                           "line": {"color": "rgba(148,163,184,0.4)", "width": 1, "dash": "dash"},
                           "layer": "below"})

            Ms_db = sens.get("Ms_db")
            Mt_db = sens.get("Mt_db")
            if Ms_db is not None:
                shapes.append({"type": "line", "xref": "paper", "yref": "y",
                               "x0": 0, "x1": 1, "y0": Ms_db, "y1": Ms_db,
                               "line": {"color": "rgba(59,130,246,0.3)", "width": 1, "dash": "dot"},
                               "layer": "below"})

        lay = self._layout("sensitivity", "Sensitivity & Complementary Sensitivity",
                           xt="Frequency (rad/s)", yt="Magnitude (dB)")
        lay["xaxis"]["type"] = "log"
        lay["shapes"] = shapes
        return {"id": "sensitivity", "title": "Sensitivity & Complementary Sensitivity",
                "data": data, "layout": lay}

    # ------------------------------------------------------------------ #
    #  Public interface                                                   #
    # ------------------------------------------------------------------ #
    def get_plots(self) -> List[Dict[str, Any]]:
        if not self._initialized:
            self.initialize()
        _, plots, _ = self._compute_all()
        return plots

    def get_state(self) -> Dict[str, Any]:
        if not self._initialized:
            self.initialize()
        metadata, plots, _ = self._compute_all()
        return {"parameters": self.parameters.copy(),
                "plots": plots, "metadata": metadata}

    def _compute_all(self) -> Tuple[Dict, List[Dict], Dict]:
        """Central computation engine."""
        # Extract parameters
        g_num, g_den = self._get_plant_tf()
        h_num, h_den = self._get_feedback_tf()
        K = float(self.parameters["gain_K"])
        input_type = str(self.parameters["input_type"])
        A = float(self.parameters["input_magnitude"])
        preset = str(self.parameters["plant_preset"])
        is_unity = str(self.parameters["feedback_type"]) == "unity"
        dist_mode = str(self.parameters["disturbance_mode"])
        dist_mag = float(self.parameters["disturbance_magnitude"])

        # Loop TF: L(s) = G(s)H(s)
        L_num, L_den = self._loop_tf(g_num, g_den, h_num, h_den)

        # Effective (cancelled) loop TF for type/constant analysis
        L_eff_num, L_eff_den = self._cancel_common_s(L_num, L_den)
        sys_type = self._count_origin_poles(L_eff_den)

        # Error constants and ess
        ec = self._error_constants(L_eff_num, L_eff_den, sys_type)
        ss_errors = self._ess_values(ec, sys_type, A)
        current_ess = ss_errors.get(input_type, 0) if input_type != "all" else None

        # CL poles
        cl_poles, is_stable, _ = self._cl_poles(g_num, g_den, h_num, h_den)

        # CL TF for time simulation
        cl_num, cl_den = self._cl_tf(g_num, g_den, h_num, h_den)

        # Time simulation
        t_end = self._estimate_t_end(cl_poles, is_stable)

        if input_type == "all":
            sims = {}
            for it in ["step", "ramp", "parabolic"]:
                sims[it] = self._simulate(cl_num, cl_den, it, A, t_end, is_stable)
        else:
            sim = self._simulate(cl_num, cl_den, input_type, A, t_end, is_stable)
            sims = {input_type: sim}

        # Performance metrics (from step response)
        step_sim = sims.get("step")
        if step_sim is None and input_type != "all":
            step_sim = self._simulate(cl_num, cl_den, "step", A, t_end, is_stable)
        perf = self._step_metrics(step_sim["t"], step_sim["y"], A, is_stable) if step_sim else {}

        # ess vs K sweep
        num_base = self._get_num_base()
        ess_data = self._ess_vs_K(num_base, g_den, h_num, h_den, A)

        # Margins (on loop TF)
        margins = self._compute_margins(L_num, L_den)

        # Sensitivity functions
        sens = self._sensitivity_bode(L_num, L_den)

        # Disturbance simulation
        dist_sim = self._simulate_disturbance(g_num, g_den, h_num, h_den,
                                              dist_mode, dist_mag, t_end)

        # LaTeX
        num_base_display = self._get_num_base()
        plant_latex = self._plant_latex(num_base_display, g_den, K)
        fvt_input = input_type if input_type != "all" else "step"
        fvt_ess = ss_errors.get(fvt_input, 0)
        fvt_latex = self._fvt_latex(fvt_input, sys_type, ec, A,
                                    fvt_ess, is_stable, is_unity)

        # Feedback latex
        feedback_latex = None
        if not is_unity:
            h_num_raw = self._parse_poly(self.parameters["feedback_num"])
            h_den_raw = self._parse_poly(self.parameters["feedback_den"])
            h_n = self._poly_latex(h_num_raw)
            h_d = self._poly_latex(h_den_raw)
            feedback_latex = f"H(s) = \\frac{{{h_n}}}{{{h_d}}}"

        # Display strings
        ec_display = {k: self._dv(v) for k, v in ec.items()}
        ess_display = {k: self._dv(v) for k, v in ss_errors.items()}

        # ---- Build plots ---- #
        plots = [
            self._plot_time_response(sims, input_type, ss_errors, is_stable),
            self._plot_error(sims, input_type, ss_errors, is_stable),
            self._plot_bode(margins),
            self._plot_ess_vs_K(ess_data, K),
            self._plot_sensitivity(sens),
            self._plot_poles(g_num, g_den, cl_poles, sys_type, is_stable),
        ]

        # ---- Build metadata ---- #
        metadata: Dict[str, Any] = {
            "simulation_type": "steady_state_error",
            "hub_slots": self.HUB_SLOTS,
            "hub_domain": self.HUB_DOMAIN,
            "hub_dimensions": self.HUB_DIMENSIONS,
            "system_type": sys_type,
            "error_constants": {
                "Kp": ec["Kp"], "Kv": ec["Kv"], "Ka": ec["Ka"],
                "K_static": ec["K_static"],
            },
            "error_constants_display": ec_display,
            "steady_state_errors": {
                "step": ss_errors["step"], "ramp": ss_errors["ramp"],
                "parabolic": ss_errors["parabolic"],
            },
            "steady_state_errors_display": ess_display,
            "cl_stable": is_stable,
            "cl_poles": [{"real": float(np.real(p)), "imag": float(np.imag(p))}
                         for p in cl_poles],
            "plant_latex": plant_latex,
            "feedback_latex": feedback_latex,
            "is_unity_feedback": is_unity,
            "fvt_latex": fvt_latex,
            "fvt_valid": is_stable,
            "gain_K": K,
            "input_type": input_type,
            "input_magnitude": A,
            "preset_description": self._PRESETS.get(preset, {}).get("desc", ""),
            # Margins
            "gain_margin": margins.get("GM"),
            "phase_margin": margins.get("PM"),
            "w_gc": margins.get("w_gc"),
            "w_pc": margins.get("w_pc"),
            # Sensitivity peaks
            "Ms": sens.get("Ms"),
            "Mt": sens.get("Mt"),
            # Performance metrics
            "performance": perf,
            # Disturbance
            "disturbance": dist_sim,
            "disturbance_mode": dist_mode,
        }

        return metadata, plots, {}
