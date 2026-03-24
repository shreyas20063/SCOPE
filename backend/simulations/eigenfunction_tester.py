"""
Eigenfunction Tester Lab Simulator

Interactive exploration of eigenfunctions of LTI systems. Complex exponentials
e^{st} are eigenfunctions of ALL LTI systems with eigenvalue H(s). Students test
various signals against different systems to verify which are eigenfunctions.

"""

import random
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy import signal as sp_signal

from .base_simulator import BaseSimulator


class EigenfunctionTesterSimulator(BaseSimulator):
    """Simulator for the Eigenfunction Tester Lab."""

    NUM_SAMPLES = 1000
    MAX_DISPLAY_VALUE = 200.0
    POLE_THRESHOLD = 1e-10
    RATIO_THRESHOLD = 1e-8

    # System presets: {key: {label, num, den}}
    PRESETS = {
        "first_order": {
            "label": "First Order: H(s) = 1/(s+2)",
            "num": [1.0],
            "den": [1.0, 2.0],
        },
        "integrator": {
            "label": "Integrator: H(s) = 1/s",
            "num": [1.0],
            "den": [1.0, 0.0],
        },
        "second_order_real": {
            "label": "2nd Order: H(s) = 1/((s+1)(s+3))",
            "num": [1.0],
            "den": [1.0, 4.0, 3.0],
        },
        "second_order_complex": {
            "label": "Underdamped: H(s) = 1/(s\u00b2+2s+5)",
            "num": [1.0],
            "den": [1.0, 2.0, 5.0],
        },
        "unstable": {
            "label": "Unstable: H(s) = 1/(s\u22121)",
            "num": [1.0],
            "den": [1.0, -1.0],
        },
        "allpass": {
            "label": "Allpass: H(s) = (s\u22121)/(s+1)",
            "num": [1.0, -1.0],
            "den": [1.0, 1.0],
        },
    }

    # Signal palette descriptors
    SIGNAL_PALETTE = [
        {"key": "exp_neg", "label": "e\u207b\u1d57", "latex": "e^{-t}",
         "s_value": {"real": -1, "imag": 0}, "is_eigen": True, "category": "exponential"},
        {"key": "exp_pos", "label": "e\u1d57", "latex": "e^{t}",
         "s_value": {"real": 1, "imag": 0}, "is_eigen": True, "category": "exponential"},
        {"key": "exp_jt", "label": "e\u02b2\u1d57", "latex": "e^{jt}",
         "s_value": {"real": 0, "imag": 1}, "is_eigen": True, "category": "exponential"},
        {"key": "exp_neg_jt", "label": "e\u207b\u02b2\u1d57", "latex": "e^{-jt}",
         "s_value": {"real": 0, "imag": -1}, "is_eigen": True, "category": "exponential"},
        {"key": "cos_t", "label": "cos(t)", "latex": "\\cos(t)",
         "s_value": None, "is_eigen": False, "category": "trig"},
        {"key": "sin_t", "label": "sin(t)", "latex": "\\sin(t)",
         "s_value": None, "is_eigen": False, "category": "trig"},
        {"key": "unit_step", "label": "u(t)", "latex": "u(t)",
         "s_value": None, "is_eigen": False, "category": "other"},
        {"key": "t_squared", "label": "t\u00b2 u(t)", "latex": "t^2 u(t)",
         "s_value": None, "is_eigen": False, "category": "other"},
        {"key": "custom_exp", "label": "e\u02e2\u1d57 (custom)", "latex": "e^{st}",
         "s_value": "from_params", "is_eigen": True, "category": "custom"},
    ]

    EIGENFUNCTION_SIGNALS = {"exp_neg", "exp_pos", "exp_jt", "exp_neg_jt", "custom_exp"}

    PARAMETER_SCHEMA = {
        "system_preset": {
            "type": "select",
            "options": [
                {"value": "first_order", "label": "First Order: H(s) = 1/(s+2)"},
                {"value": "integrator", "label": "Integrator: H(s) = 1/s"},
                {"value": "second_order_real", "label": "2nd Order: 1/((s+1)(s+3))"},
                {"value": "second_order_complex", "label": "Underdamped: 1/(s\u00b2+2s+5)"},
                {"value": "unstable", "label": "Unstable: 1/(s\u22121)"},
                {"value": "allpass", "label": "Allpass: (s\u22121)/(s+1)"},
                {"value": "custom", "label": "Custom Coefficients"},
            ],
            "default": "first_order",
        },
        "num_coeffs": {"type": "expression", "default": "1"},
        "den_coeffs": {"type": "expression", "default": "1, 2"},
        "test_signal": {
            "type": "select",
            "options": [
                {"value": "exp_neg", "label": "e^{-t} (s = -1)"},
                {"value": "exp_pos", "label": "e^{t} (s = 1)"},
                {"value": "exp_jt", "label": "e^{jt} (s = j)"},
                {"value": "exp_neg_jt", "label": "e^{-jt} (s = -j)"},
                {"value": "cos_t", "label": "cos(t)"},
                {"value": "sin_t", "label": "sin(t)"},
                {"value": "unit_step", "label": "u(t)"},
                {"value": "t_squared", "label": "t\u00b2 u(t)"},
                {"value": "custom_exp", "label": "e^{st} (custom s)"},
            ],
            "default": "exp_neg",
        },
        "custom_s_real": {
            "type": "slider", "min": -5.0, "max": 5.0, "step": 0.1, "default": -1.0,
        },
        "custom_s_imag": {
            "type": "slider", "min": -5.0, "max": 5.0, "step": 0.1, "default": 0.0,
        },
        "time_range": {
            "type": "slider", "min": 1.0, "max": 10.0, "step": 0.5, "default": 5.0,
        },
        "show_ratio": {"type": "checkbox", "default": True},
        "show_splane": {"type": "checkbox", "default": True},
        "mode": {
            "type": "select",
            "options": [
                {"value": "explore", "label": "Explore"},
                {"value": "quiz", "label": "Quiz"},
            ],
            "default": "explore",
        },
    }

    DEFAULT_PARAMS = {
        "system_preset": "first_order",
        "num_coeffs": "1",
        "den_coeffs": "1, 2",
        "test_signal": "exp_neg",
        "custom_s_real": -1.0,
        "custom_s_imag": 0.0,
        "time_range": 5.0,
        "show_ratio": True,
        "show_splane": True,
        "mode": "explore",
    }

    HUB_SLOTS = ['control']

    def __init__(self, simulation_id: str):
        super().__init__(simulation_id)
        self._num = np.array([1.0])
        self._den = np.array([1.0, 2.0])
        self._poles = np.array([-2.0 + 0j])
        self._zeros = np.array([], dtype=complex)
        self._revision = 0
        # Quiz state
        self._quiz_system: Optional[str] = None
        self._quiz_signal: Optional[str] = None
        self._quiz_answer: bool = False
        self._quiz_generated: bool = False
        self._quiz_answered: bool = False
        self._quiz_correct: Optional[bool] = None
        self._quiz_user_answer: Optional[str] = None

    def initialize(self, params: Optional[Dict[str, Any]] = None) -> None:
        self.parameters = {**self.DEFAULT_PARAMS, **(params or {})}
        for name, value in self.parameters.items():
            if name in self.PARAMETER_SCHEMA:
                self.parameters[name] = self._validate_param(name, value)
        self._load_system()
        self._reset_quiz()
        self._revision += 1
        self._initialized = True

    def reset(self) -> Dict[str, Any]:
        self.parameters = self.DEFAULT_PARAMS.copy()
        self._load_system()
        self._reset_quiz()
        self._revision += 1
        self._initialized = True
        return self.get_state()

    def update_parameter(self, name: str, value: Any) -> Dict[str, Any]:
        if name in self.parameters:
            old_val = self.parameters.get(name)
            self.parameters[name] = self._validate_param(name, value)
            new_val = self.parameters[name]

            # Reload system when system params change
            if name in ("system_preset", "num_coeffs", "den_coeffs"):
                self._load_system()
                self._revision += 1

            # Auto-generate quiz when switching to quiz mode
            if name == "mode" and new_val == "quiz" and not self._quiz_generated:
                self._generate_quiz()

            # Reset quiz when switching back to explore
            if name == "mode" and new_val == "explore":
                self._reset_quiz()

        return self.get_state()

    def handle_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if action == "new_quiz":
            self._generate_quiz()
        elif action == "check_answer":
            user_answer = params.get("answer", "")
            self._quiz_user_answer = user_answer
            self._quiz_answered = True
            expected = "yes" if self._quiz_answer else "no"
            self._quiz_correct = (user_answer == expected)
        elif action == "reset":
            return self.reset()
        return self.get_state()

    def get_plots(self) -> List[Dict[str, Any]]:
        signal_data = self._compute_signal()
        plots = [self._create_time_domain_plot(signal_data)]

        if bool(self.parameters.get("show_ratio", True)):
            plots.append(self._create_ratio_plot(signal_data))

        if bool(self.parameters.get("show_splane", True)):
            plots.append(self._create_splane_plot(signal_data))

        return plots

    def get_state(self) -> Dict[str, Any]:
        signal_data = self._compute_signal()

        plots = [self._create_time_domain_plot(signal_data)]
        if bool(self.parameters.get("show_ratio", True)):
            plots.append(self._create_ratio_plot(signal_data))
        if bool(self.parameters.get("show_splane", True)):
            plots.append(self._create_splane_plot(signal_data))

        test_signal = str(self.parameters["test_signal"])
        is_eigen = test_signal in self.EIGENFUNCTION_SIGNALS
        s_val = signal_data.get("s_value")
        eigenvalue = signal_data.get("eigenvalue")
        at_pole = signal_data.get("at_pole", False)

        # Build eigenvalue metadata
        ev_meta = None
        if eigenvalue is not None and not at_pole:
            ev_meta = {
                "real": float(eigenvalue.real),
                "imag": float(eigenvalue.imag),
                "magnitude": float(abs(eigenvalue)),
                "angle_deg": float(np.degrees(np.angle(eigenvalue))),
            }

        s_meta = None
        if s_val is not None:
            s_meta = {"real": float(s_val.real), "imag": float(s_val.imag)}

        # Quiz metadata
        quiz_meta = None
        if self.parameters.get("mode") == "quiz" and self._quiz_generated:
            quiz_system_label = self.PRESETS.get(self._quiz_system, {}).get("label", "")
            quiz_signal_info = self._get_signal_info(self._quiz_signal)
            quiz_meta = {
                "answered": self._quiz_answered,
                "correct": self._quiz_correct,
                "user_answer": self._quiz_user_answer,
                "expected": "yes" if self._quiz_answer else "no",
                "quiz_system_label": quiz_system_label,
                "quiz_signal_label": quiz_signal_info.get("label", ""),
                "quiz_signal_latex": quiz_signal_info.get("latex", ""),
            }

        return {
            "parameters": self.parameters.copy(),
            "plots": plots,
            "metadata": {
                "simulation_type": "eigenfunction_tester",
            "hub_slots": self.HUB_SLOTS,
            "hub_domain": self.HUB_DOMAIN,
            "hub_dimensions": self.HUB_DIMENSIONS,
                "sticky_controls": True,
                "hs_expression": self._format_hs(),
                "system_label": self._get_system_label(),
                "poles": [
                    {"real": float(p.real), "imag": float(p.imag)}
                    for p in self._poles
                ],
                "zeros": [
                    {"real": float(z.real), "imag": float(z.imag)}
                    for z in self._zeros
                ],
                "test_signal_key": test_signal,
                "test_signal_label": self._get_signal_label(test_signal),
                "test_signal_latex": self._get_signal_info(test_signal).get("latex", ""),
                "is_eigenfunction": is_eigen and not at_pole,
                "at_pole": at_pole,
                "s_value": s_meta,
                "eigenvalue": ev_meta,
                "signal_palette": self.SIGNAL_PALETTE,
                "mode": self.parameters.get("mode", "explore"),
                "quiz": quiz_meta,
                "revision": self._revision,
            },
        }

    # ── System loading ────────────────────────────────────────────────

    def _load_system(self) -> None:
        preset = str(self.parameters.get("system_preset", "first_order"))
        if preset != "custom" and preset in self.PRESETS:
            p = self.PRESETS[preset]
            self._num = np.array(p["num"], dtype=float)
            self._den = np.array(p["den"], dtype=float)
        else:
            self._num = self._parse_coeffs(str(self.parameters.get("num_coeffs", "1")))
            self._den = self._parse_coeffs(str(self.parameters.get("den_coeffs", "1, 2")))

        self._poles = np.roots(self._den) if len(self._den) > 1 else np.array([], dtype=complex)
        self._zeros = np.roots(self._num) if len(self._num) > 1 else np.array([], dtype=complex)

    def _parse_coeffs(self, text: str) -> np.ndarray:
        try:
            parts = [float(x.strip()) for x in text.replace(";", ",").split(",") if x.strip()]
            if len(parts) == 0:
                return np.array([1.0])
            return np.array(parts, dtype=float)
        except (ValueError, TypeError):
            return np.array([1.0])

    # ── H(s) evaluation ──────────────────────────────────────────────

    def _evaluate_H(self, s: complex) -> Tuple[complex, bool]:
        """Evaluate H(s) = N(s)/D(s). Returns (value, at_pole)."""
        num_val = np.polyval(self._num, s)
        den_val = np.polyval(self._den, s)
        if abs(den_val) < self.POLE_THRESHOLD:
            return complex(float("inf"), 0), True
        return num_val / den_val, False

    # ── Signal computation ────────────────────────────────────────────

    def _get_s_for_signal(self, signal_key: str) -> Optional[complex]:
        s_map = {
            "exp_neg": complex(-1.0, 0.0),
            "exp_pos": complex(1.0, 0.0),
            "exp_jt": complex(0.0, 1.0),
            "exp_neg_jt": complex(0.0, -1.0),
        }
        if signal_key in s_map:
            return s_map[signal_key]
        if signal_key == "custom_exp":
            sr = float(self.parameters.get("custom_s_real", -1.0))
            si = float(self.parameters.get("custom_s_imag", 0.0))
            return complex(sr, si)
        return None

    def _compute_signal(self) -> Dict[str, Any]:
        test_signal = str(self.parameters.get("test_signal", "exp_neg"))
        T = float(self.parameters.get("time_range", 5.0))

        # For non-eigenfunction signals, start at t=0 (causal)
        if test_signal in self.EIGENFUNCTION_SIGNALS:
            t = np.linspace(-T / 4, T, self.NUM_SAMPLES)
        else:
            t = np.linspace(0, T, self.NUM_SAMPLES)

        if test_signal in self.EIGENFUNCTION_SIGNALS:
            return self._compute_eigenfunction_signal(test_signal, t)
        else:
            return self._compute_non_eigenfunction_signal(test_signal, t)

    def _compute_eigenfunction_signal(self, signal_key: str, t: np.ndarray) -> Dict[str, Any]:
        s = self._get_s_for_signal(signal_key)
        H_s, at_pole = self._evaluate_H(s)

        # x(t) = e^{st}  (complex)
        x_complex = np.exp(s * t)
        x_real = np.real(x_complex)

        if at_pole:
            # H(s) is infinite — signal hits a pole
            y_real = np.full_like(t, np.nan)
            ratio = np.full_like(t, np.nan)
            return {
                "t": t, "x_real": x_real, "y_real": y_real,
                "ratio": ratio, "eigenvalue": None, "at_pole": True,
                "is_eigenfunction": False, "s_value": s,
                "signal_key": signal_key, "is_complex_signal": abs(s.imag) > 1e-10,
            }

        # y(t) = H(s) * e^{st}
        y_complex = H_s * x_complex
        y_real = np.real(y_complex)

        # Clip for display
        x_real = np.clip(x_real, -self.MAX_DISPLAY_VALUE, self.MAX_DISPLAY_VALUE)
        y_real = np.clip(y_real, -self.MAX_DISPLAY_VALUE, self.MAX_DISPLAY_VALUE)

        # Ratio of real parts (for display)
        ratio = np.full_like(t, np.nan)
        safe = np.abs(x_real) > self.RATIO_THRESHOLD
        ratio[safe] = y_real[safe] / x_real[safe]
        ratio = np.clip(ratio, -self.MAX_DISPLAY_VALUE, self.MAX_DISPLAY_VALUE)

        return {
            "t": t, "x_real": x_real, "y_real": y_real,
            "ratio": ratio, "eigenvalue": H_s, "at_pole": False,
            "is_eigenfunction": True, "s_value": s,
            "signal_key": signal_key, "is_complex_signal": abs(s.imag) > 1e-10,
        }

    def _compute_non_eigenfunction_signal(self, signal_key: str, t: np.ndarray) -> Dict[str, Any]:
        # Build input signal
        if signal_key == "cos_t":
            x_t = np.cos(t)
        elif signal_key == "sin_t":
            x_t = np.sin(t)
        elif signal_key == "unit_step":
            x_t = np.ones_like(t)
        elif signal_key == "t_squared":
            x_t = t ** 2
        else:
            x_t = np.ones_like(t)

        # Compute output via scipy.signal.lsim
        try:
            sys = sp_signal.lti(self._num.tolist(), self._den.tolist())
            _, y_t, _ = sp_signal.lsim(sys, U=x_t, T=t)
        except Exception:
            y_t = np.zeros_like(t)

        # Clip for display
        x_t = np.clip(x_t, -self.MAX_DISPLAY_VALUE, self.MAX_DISPLAY_VALUE)
        y_t = np.clip(y_t, -self.MAX_DISPLAY_VALUE, self.MAX_DISPLAY_VALUE)

        # Ratio y(t)/x(t) where |x(t)| is safe
        ratio = np.full_like(t, np.nan)
        safe = np.abs(x_t) > self.RATIO_THRESHOLD
        ratio[safe] = y_t[safe] / x_t[safe]
        ratio = np.clip(ratio, -self.MAX_DISPLAY_VALUE, self.MAX_DISPLAY_VALUE)

        return {
            "t": t, "x_real": x_t, "y_real": y_t,
            "ratio": ratio, "eigenvalue": None, "at_pole": False,
            "is_eigenfunction": False, "s_value": None,
            "signal_key": signal_key, "is_complex_signal": False,
        }

    # ── Plot construction ─────────────────────────────────────────────

    def _get_base_layout(self, xtitle: str, ytitle: str, plot_id: str) -> Dict[str, Any]:
        preset = str(self.parameters.get("system_preset", ""))
        signal = str(self.parameters.get("test_signal", ""))
        sr = self.parameters.get("custom_s_real", 0)
        si = self.parameters.get("custom_s_imag", 0)
        return {
            "xaxis": {
                "title": {"text": xtitle, "font": {"color": "#f1f5f9", "size": 13}},
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
                "color": "#94a3b8",
            },
            "yaxis": {
                "title": {"text": ytitle, "font": {"color": "#f1f5f9", "size": 13}},
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
                "color": "#94a3b8",
                "autorange": True,
            },
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "font": {"family": "Inter, sans-serif", "size": 12, "color": "#f1f5f9"},
            "margin": {"t": 45, "r": 25, "b": 55, "l": 60},
            "showlegend": True,
            "legend": {
                "font": {"color": "#94a3b8", "size": 11},
                "bgcolor": "rgba(0,0,0,0)",
                "x": 0.98, "y": 0.98,
                "xanchor": "right", "yanchor": "top",
            },
            "datarevision": f"{plot_id}-{signal}-{sr}-{si}-{time.time()}",
            "uirevision": f"{plot_id}-{preset}-{self._revision}",
        }

    def _create_time_domain_plot(self, data: Dict[str, Any]) -> Dict[str, Any]:
        t = data["t"]
        x_real = data["x_real"]
        y_real = data["y_real"]
        signal_key = data["signal_key"]
        is_complex = data.get("is_complex_signal", False)

        t_list = t.tolist()
        traces = []

        # Input signal
        input_label = self._get_signal_label(signal_key)
        if is_complex:
            input_label = f"Re({input_label})"
        traces.append({
            "x": t_list,
            "y": x_real.tolist(),
            "type": "scatter",
            "mode": "lines",
            "name": f"Input: {input_label}",
            "line": {"color": "#3b82f6", "width": 2.5},
            "hovertemplate": "Input<br>t=%{x:.3f}<br>x=%{y:.4f}<extra></extra>",
        })

        # Output signal
        output_label = "y(t)"
        if is_complex:
            output_label = "Re(y(t))"
        traces.append({
            "x": t_list,
            "y": y_real.tolist(),
            "type": "scatter",
            "mode": "lines",
            "name": f"Output: {output_label}",
            "line": {"color": "#ef4444", "width": 2.5},
            "hovertemplate": "Output<br>t=%{x:.3f}<br>y=%{y:.4f}<extra></extra>",
        })

        # Zero reference line
        traces.append({
            "x": [t_list[0], t_list[-1]],
            "y": [0, 0],
            "type": "scatter",
            "mode": "lines",
            "name": "Zero",
            "line": {"color": "rgba(148,163,184,0.3)", "width": 1, "dash": "dash"},
            "showlegend": False,
            "hoverinfo": "skip",
        })

        layout = self._get_base_layout("t (seconds)", "Amplitude", "time_domain")

        title = "Input x(t) vs Output y(t)"
        if data["is_eigenfunction"]:
            ev = data["eigenvalue"]
            if ev is not None:
                title += f"  \u2014  y(t) = H(s)\u00b7x(t)"

        return {"id": "time_domain", "title": title, "data": traces, "layout": layout}

    def _create_ratio_plot(self, data: Dict[str, Any]) -> Dict[str, Any]:
        t = data["t"]
        ratio = data["ratio"]
        eigenvalue = data.get("eigenvalue")
        is_complex = data.get("is_complex_signal", False)

        t_list = t.tolist()
        traces = []

        # Ratio trace
        ratio_label = "Re(y)/Re(x)" if is_complex else "y(t)/x(t)"
        traces.append({
            "x": t_list,
            "y": ratio.tolist(),
            "type": "scatter",
            "mode": "lines",
            "name": ratio_label,
            "line": {"color": "#8b5cf6", "width": 2.5},
            "connectgaps": False,
            "hovertemplate": "Ratio<br>t=%{x:.3f}<br>r=%{y:.4f}<extra></extra>",
        })

        # Reference line at eigenvalue (if eigenfunction with real eigenvalue)
        if eigenvalue is not None and abs(eigenvalue.imag) < 1e-6:
            ev_real = float(eigenvalue.real)
            traces.append({
                "x": [t_list[0], t_list[-1]],
                "y": [ev_real, ev_real],
                "type": "scatter",
                "mode": "lines",
                "name": f"\u03bb = H(s) = {ev_real:.4f}",
                "line": {"color": "#10b981", "width": 2, "dash": "dash"},
                "hoverinfo": "name",
            })

        # Reference line at zero
        traces.append({
            "x": [t_list[0], t_list[-1]],
            "y": [0, 0],
            "type": "scatter",
            "mode": "lines",
            "name": "Zero",
            "line": {"color": "rgba(148,163,184,0.2)", "width": 1, "dash": "dot"},
            "showlegend": False,
            "hoverinfo": "skip",
        })

        layout = self._get_base_layout("t (seconds)", "Ratio y/x", "ratio_plot")

        title = "Ratio y(t)/x(t)"
        if data["is_eigenfunction"] and eigenvalue is not None:
            if is_complex:
                title += "  \u2014  Re(y)/Re(x) (complex eigenvalue, see info panel)"
            else:
                title += f"  \u2014  Constant = {float(eigenvalue.real):.4f}"
        elif not data["is_eigenfunction"]:
            title += "  \u2014  NOT constant (not an eigenfunction)"

        return {"id": "ratio_plot", "title": title, "data": traces, "layout": layout}

    def _create_splane_plot(self, data: Dict[str, Any]) -> Dict[str, Any]:
        s_val = data.get("s_value")
        traces = []

        # Axes
        axis_range = 6.0
        traces.append({
            "x": [-axis_range, axis_range], "y": [0, 0],
            "type": "scatter", "mode": "lines",
            "line": {"color": "rgba(148,163,184,0.4)", "width": 1},
            "showlegend": False, "hoverinfo": "skip",
        })
        traces.append({
            "x": [0, 0], "y": [-axis_range, axis_range],
            "type": "scatter", "mode": "lines",
            "line": {"color": "rgba(148,163,184,0.4)", "width": 1},
            "showlegend": False, "hoverinfo": "skip",
        })

        # Poles
        if len(self._poles) > 0:
            # Handle conjugate pairs — show unique poles
            pole_reals = [float(p.real) for p in self._poles]
            pole_imags = [float(p.imag) for p in self._poles]
            traces.append({
                "x": pole_reals, "y": pole_imags,
                "type": "scatter", "mode": "markers",
                "marker": {"symbol": "x", "size": 14, "color": "#ef4444",
                           "line": {"width": 2, "color": "#ef4444"}},
                "name": "Poles",
                "hovertemplate": "Pole<br>\u03c3=%{x:.3f}<br>j\u03c9=%{y:.3f}<extra></extra>",
            })

        # Zeros
        if len(self._zeros) > 0:
            zero_reals = [float(z.real) for z in self._zeros]
            zero_imags = [float(z.imag) for z in self._zeros]
            traces.append({
                "x": zero_reals, "y": zero_imags,
                "type": "scatter", "mode": "markers",
                "marker": {"symbol": "circle-open", "size": 14, "color": "#3b82f6",
                           "line": {"width": 2, "color": "#3b82f6"}},
                "name": "Zeros",
                "hovertemplate": "Zero<br>\u03c3=%{x:.3f}<br>j\u03c9=%{y:.3f}<extra></extra>",
            })

        # Evaluation point s0 and vectors (only for eigenfunction signals)
        if s_val is not None:
            sr, si = float(s_val.real), float(s_val.imag)
            s_label = self._format_complex(s_val)
            traces.append({
                "x": [sr], "y": [si],
                "type": "scatter", "mode": "markers+text",
                "marker": {"symbol": "star", "size": 16, "color": "#14b8a6",
                           "line": {"width": 1, "color": "#0d9488"}},
                "text": [f"  s = {s_label}"],
                "textposition": "top right",
                "textfont": {"color": "#14b8a6", "size": 12,
                             "family": "'Fira Code', monospace"},
                "name": f"s\u2080 = {s_label}",
                "hovertemplate": f"s\u2080 = {s_label}<extra></extra>",
            })

            # Vectors from poles to s0
            for i, pole in enumerate(self._poles):
                vec = s_val - pole
                traces.append({
                    "x": [float(pole.real), sr],
                    "y": [float(pole.imag), si],
                    "type": "scatter", "mode": "lines",
                    "line": {"color": "rgba(239,68,68,0.6)", "width": 1.5, "dash": "dot"},
                    "name": f"s\u2080\u2212p{i + 1} (|{abs(vec):.3f}|\u2220{np.degrees(np.angle(vec)):.1f}\u00b0)",
                    "showlegend": True,
                    "hoverinfo": "name",
                })

            # Vectors from zeros to s0
            for i, zero in enumerate(self._zeros):
                vec = s_val - zero
                traces.append({
                    "x": [float(zero.real), sr],
                    "y": [float(zero.imag), si],
                    "type": "scatter", "mode": "lines",
                    "line": {"color": "rgba(59,130,246,0.6)", "width": 1.5, "dash": "dot"},
                    "name": f"s\u2080\u2212z{i + 1} (|{abs(vec):.3f}|\u2220{np.degrees(np.angle(vec)):.1f}\u00b0)",
                    "showlegend": True,
                    "hoverinfo": "name",
                })

        preset = str(self.parameters.get("system_preset", ""))
        signal = str(self.parameters.get("test_signal", ""))
        sr_param = self.parameters.get("custom_s_real", 0)
        si_param = self.parameters.get("custom_s_imag", 0)

        layout = {
            "xaxis": {
                "title": {"text": "\u03c3 (Real)", "font": {"color": "#f1f5f9", "size": 13}},
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
                "color": "#94a3b8",
                "range": [-axis_range, axis_range],
                "constrain": "domain",
            },
            "yaxis": {
                "title": {"text": "j\u03c9 (Imaginary)", "font": {"color": "#f1f5f9", "size": 13}},
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
                "color": "#94a3b8",
                "scaleanchor": "x",
                "scaleratio": 1,
                "constrain": "domain",
            },
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "font": {"family": "Inter, sans-serif", "size": 12, "color": "#f1f5f9"},
            "margin": {"t": 45, "r": 25, "b": 55, "l": 60},
            "showlegend": True,
            "legend": {
                "font": {"color": "#94a3b8", "size": 10},
                "bgcolor": "rgba(0,0,0,0)",
                "x": 0.02, "y": 0.98,
                "xanchor": "left", "yanchor": "top",
            },
            "datarevision": f"s_plane-{signal}-{sr_param}-{si_param}-{time.time()}",
            "uirevision": f"s_plane-{preset}-{self._revision}",
        }

        title = "S-Plane: Poles, Zeros"
        if s_val is not None:
            title += " & Vectors to s\u2080"

        return {"id": "s_plane", "title": title, "data": traces, "layout": layout}

    # ── Quiz ──────────────────────────────────────────────────────────

    def _generate_quiz(self) -> None:
        # Pick a random system (not custom, not integrator for simplicity)
        quiz_systems = ["first_order", "second_order_real",
                        "second_order_complex", "unstable", "allpass"]
        self._quiz_system = random.choice(quiz_systems)

        # Pick a random signal
        quiz_signals = ["exp_neg", "exp_pos", "exp_jt", "cos_t",
                        "sin_t", "unit_step", "t_squared"]
        self._quiz_signal = random.choice(quiz_signals)

        self._quiz_answer = self._quiz_signal in self.EIGENFUNCTION_SIGNALS
        self._quiz_generated = True
        self._quiz_answered = False
        self._quiz_correct = None
        self._quiz_user_answer = None

        # Load the quiz system so plots reflect it
        p = self.PRESETS[self._quiz_system]
        self._num = np.array(p["num"], dtype=float)
        self._den = np.array(p["den"], dtype=float)
        self._poles = np.roots(self._den) if len(self._den) > 1 else np.array([], dtype=complex)
        self._zeros = np.roots(self._num) if len(self._num) > 1 else np.array([], dtype=complex)

        # Update params to show the quiz signal
        self.parameters["test_signal"] = self._quiz_signal
        self.parameters["system_preset"] = self._quiz_system

    def _reset_quiz(self) -> None:
        self._quiz_system = None
        self._quiz_signal = None
        self._quiz_answer = False
        self._quiz_generated = False
        self._quiz_answered = False
        self._quiz_correct = None
        self._quiz_user_answer = None

    # ── Formatting helpers ────────────────────────────────────────────

    def _format_complex(self, z: complex) -> str:
        r, i = z.real, z.imag
        if abs(i) < 1e-6:
            return f"{r:.3f}"
        if abs(r) < 1e-6:
            if abs(i - 1.0) < 1e-6:
                return "j"
            if abs(i + 1.0) < 1e-6:
                return "\u2212j"
            return f"{i:.3f}j"
        sign = "+" if i >= 0 else "\u2212"
        return f"{r:.3f} {sign} {abs(i):.3f}j"

    def _format_hs(self) -> str:
        num_str = self._poly_to_str(self._num, "s")
        den_str = self._poly_to_str(self._den, "s")
        return f"({num_str}) / ({den_str})"

    def _poly_to_str(self, coeffs: np.ndarray, var: str) -> str:
        n = len(coeffs) - 1
        terms = []
        for i, c in enumerate(coeffs):
            power = n - i
            if abs(c) < 1e-10:
                continue
            if power == 0:
                terms.append(f"{c:g}")
            elif power == 1:
                if abs(c - 1.0) < 1e-10:
                    terms.append(var)
                elif abs(c + 1.0) < 1e-10:
                    terms.append(f"-{var}")
                else:
                    terms.append(f"{c:g}{var}")
            else:
                if abs(c - 1.0) < 1e-10:
                    terms.append(f"{var}^{power}")
                elif abs(c + 1.0) < 1e-10:
                    terms.append(f"-{var}^{power}")
                else:
                    terms.append(f"{c:g}{var}^{power}")
        if not terms:
            return "0"
        result = terms[0]
        for t in terms[1:]:
            if t.startswith("-"):
                result += f" - {t[1:]}"
            else:
                result += f" + {t}"
        return result

    def _get_system_label(self) -> str:
        preset = str(self.parameters.get("system_preset", "first_order"))
        if preset in self.PRESETS:
            return self.PRESETS[preset]["label"]
        return "Custom System"

    def _get_signal_label(self, signal_key: str) -> str:
        info = self._get_signal_info(signal_key)
        return info.get("label", signal_key)

    def _get_signal_info(self, signal_key: str) -> Dict[str, Any]:
        for sig in self.SIGNAL_PALETTE:
            if sig["key"] == signal_key:
                return sig
        return {"key": signal_key, "label": signal_key, "latex": signal_key}
