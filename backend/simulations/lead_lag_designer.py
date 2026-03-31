"""Lead-Lag Compensator Designer — Frequency-domain compensator design tool.

Interactive tool for designing lead and lag compensators using the standard
α/ωm (lead) and β/ωm (lag) parameterization. Shows Bode plots, step response,
pole-zero map, individual phase contributions, and Nichols chart.

Key differentiator from Controller Tuning Lab: focused on frequency-domain
design methodology with textbook parameterization and phase breakdown.
"""

from .base_simulator import BaseSimulator
import numpy as np
from scipy import signal

# NumPy 2.0 compat
_trapz = np.trapezoid if hasattr(np, 'trapezoid') else np.trapz


class LeadLagDesignerSimulator(BaseSimulator):
    """Interactive lead-lag compensator design with α/ωm parameterization,
    Bode/Nichols/step analysis, and phase contribution breakdown."""

    PARAMETER_SCHEMA = {
        # ===== PLANT =====
        "plant_preset": {
            "type": "select",
            "options": [
                {"value": "first_order", "label": "1st Order: K/(s+1)"},
                {"value": "type1", "label": "Type 1: K/[s(s+1)]"},
                {"value": "second_order", "label": "2nd Order: Kωn²/(s²+2ζωns+ωn²)"},
                {"value": "type1_two_poles", "label": "Type 1+2P: K/[s(s+1)(0.5s+1)]"},
                {"value": "dc_motor", "label": "DC Motor: K/[s(s+5)]"},
                {"value": "custom", "label": "Custom TF"},
            ],
            "default": "type1",
        },
        "plant_K": {"type": "slider", "min": 0.1, "max": 50, "default": 1.0, "step": 0.1},
        "plant_wn": {"type": "slider", "min": 0.5, "max": 20, "default": 4.0, "step": 0.1},
        "plant_zeta": {"type": "slider", "min": 0.05, "max": 2.0, "default": 0.5, "step": 0.01},
        "custom_num": {"type": "expression", "default": "1"},
        "custom_den": {"type": "expression", "default": "1, 1, 0"},
        # ===== LEAD SECTION =====
        "lead_enable": {"type": "checkbox", "default": True},
        "lead_alpha": {"type": "slider", "min": 0.02, "max": 0.98, "default": 0.1, "step": 0.01},
        "lead_wm": {"type": "slider", "min": 0.1, "max": 100, "default": 10.0, "step": 0.1},
        # ===== LAG SECTION =====
        "lag_enable": {"type": "checkbox", "default": False},
        "lag_beta": {"type": "slider", "min": 0.02, "max": 0.98, "default": 0.1, "step": 0.01},
        "lag_wm": {"type": "slider", "min": 0.001, "max": 10, "default": 0.1, "step": 0.001},
        # ===== DESIGN =====
        "gain_Kc": {"type": "slider", "min": 0.01, "max": 100, "default": 1.0, "step": 0.01},
        "pm_target": {"type": "slider", "min": 0, "max": 90, "default": 45, "step": 1},
        "show_components": {"type": "checkbox", "default": True},
    }

    DEFAULT_PARAMS = {
        "plant_preset": "type1",
        "plant_K": 1.0,
        "plant_wn": 4.0,
        "plant_zeta": 0.5,
        "custom_num": "1",
        "custom_den": "1, 1, 0",
        "lead_enable": True,
        "lead_alpha": 0.1,
        "lead_wm": 10.0,
        "lag_enable": False,
        "lag_beta": 0.1,
        "lag_wm": 0.1,
        "gain_Kc": 1.0,
        "pm_target": 45,
        "show_components": True,
    }

    HUB_SLOTS = ['control']

    def initialize(self, params=None):
        self.parameters = {**self.DEFAULT_PARAMS, **(params or {})}
        for name, value in self.parameters.items():
            self.parameters[name] = self._validate_param(name, value)
        self._initialized = True

    def update_parameter(self, name, value):
        if name in self.parameters:
            self.parameters[name] = self._validate_param(name, value)
            # Manual edit of custom_num/custom_den switches preset to custom
            if name in ("custom_num", "custom_den"):
                self.parameters["plant_preset"] = "custom"
        return self.get_state()

    def get_plots(self):
        plots, _ = self._compute_with_info()
        return plots

    def get_state(self):
        plots, design_info = self._compute_with_info()
        return {
            "parameters": self.parameters.copy(),
            "plots": plots,
            "metadata": {
                "simulation_type": "lead_lag_designer",
            "hub_slots": self.HUB_SLOTS,
            "hub_domain": self.HUB_DOMAIN,
            "hub_dimensions": self.HUB_DIMENSIONS,
                "design_info": design_info,
                "tf_labels": self._tf_labels(),
            },
        }

    # =========================================================================
    # Transfer function building
    # =========================================================================

    def _build_plant_tf(self) -> tuple:
        """Build plant G(s) as (num, den) coefficient arrays (high-power first)."""
        preset = self.parameters["plant_preset"]
        K = float(self.parameters["plant_K"])

        if preset == "first_order":
            return np.array([K]), np.array([1.0, 1.0])
        elif preset == "type1":
            # K / [s(s+1)] = K / (s² + s)
            return np.array([K]), np.array([1.0, 1.0, 0.0])
        elif preset == "second_order":
            wn = float(self.parameters["plant_wn"])
            zeta = float(self.parameters["plant_zeta"])
            return np.array([K * wn**2]), np.array([1.0, 2 * zeta * wn, wn**2])
        elif preset == "type1_two_poles":
            # K / [s(s+1)(0.5s+1)] = K / (0.5s³ + 1.5s² + s)
            return np.array([K]), np.array([0.5, 1.5, 1.0, 0.0])
        elif preset == "dc_motor":
            # K / [s(s+5)]
            return np.array([K]), np.array([1.0, 5.0, 0.0])
        elif preset == "custom":
            try:
                num = np.array([float(x.strip()) for x in
                                str(self.parameters["custom_num"]).split(",")])
                den = np.array([float(x.strip()) for x in
                                str(self.parameters["custom_den"]).split(",")])
                if len(num) == 0:
                    num = np.array([1.0])
                if len(den) == 0:
                    den = np.array([1.0])
                return num, den
            except (ValueError, TypeError):
                return np.array([1.0]), np.array([1.0, 1.0])
        # fallback
        return np.array([K]), np.array([1.0, 1.0])

    def _build_lead_tf(self) -> tuple:
        """Build lead section: C_lead(s) = (s/ωz + 1) / (s/ωp + 1).

        ωz = ωm·√α,  ωp = ωm/√α  (ωp > ωz since α < 1)
        """
        if not self.parameters.get("lead_enable", False):
            return np.array([1.0]), np.array([1.0])

        alpha = max(0.02, min(0.98, float(self.parameters["lead_alpha"])))
        wm = max(0.1, float(self.parameters["lead_wm"]))
        sqrt_a = np.sqrt(alpha)
        wz = wm * sqrt_a
        wp = wm / sqrt_a
        return np.array([1.0 / wz, 1.0]), np.array([1.0 / wp, 1.0])

    def _build_lag_tf(self) -> tuple:
        """Build lag section: C_lag(s) = (s/ωz + 1) / (s/ωp + 1).

        ωz = ωm/√β,  ωp = ωm·√β  (ωz > ωp since β < 1 → lag)
        """
        if not self.parameters.get("lag_enable", False):
            return np.array([1.0]), np.array([1.0])

        beta = max(0.02, min(0.98, float(self.parameters["lag_beta"])))
        wm = max(0.001, float(self.parameters["lag_wm"]))
        sqrt_b = np.sqrt(beta)
        wz = wm / sqrt_b
        wp = wm * sqrt_b
        return np.array([1.0 / wz, 1.0]), np.array([1.0 / wp, 1.0])

    @staticmethod
    def _convolve_tfs(tf_list: list) -> tuple:
        """Multiply transfer functions by convolving num/den arrays."""
        num = np.array([1.0])
        den = np.array([1.0])
        for n, d in tf_list:
            num = np.convolve(num, n)
            den = np.convolve(den, d)
        return num, den

    # =========================================================================
    # Frequency response & margins
    # =========================================================================

    @staticmethod
    def _freq_response(num: np.ndarray, den: np.ndarray,
                       w: np.ndarray) -> np.ndarray:
        """Evaluate H(jω) = num(jω)/den(jω)."""
        s = 1j * w
        num_val = np.polyval(num, s)
        den_val = np.polyval(den, s)
        den_val = np.where(np.abs(den_val) < 1e-30, 1e-30 + 0j, den_val)
        return num_val / den_val

    @staticmethod
    def _compute_margins(w: np.ndarray, H: np.ndarray) -> dict:
        """Compute PM, GM, gain crossover ωgc, phase crossover ωpc."""
        mag_db = 20 * np.log10(np.maximum(np.abs(H), 1e-30))
        phase_deg = np.degrees(np.unwrap(np.angle(H)))

        # Gain crossover: |H| crosses 0 dB from above
        wgc, pm = None, None
        for i in range(len(mag_db) - 1):
            if mag_db[i] > 0 and mag_db[i + 1] <= 0:
                frac = mag_db[i] / (mag_db[i] - mag_db[i + 1])
                wgc = w[i] * (w[i + 1] / w[i]) ** frac
                phase_at_gc = phase_deg[i] + frac * (phase_deg[i + 1] - phase_deg[i])
                pm = 180.0 + phase_at_gc
                break

        # Phase crossover: phase crosses -180° from above
        wpc, gm = None, None
        for i in range(len(phase_deg) - 1):
            if phase_deg[i] > -180 and phase_deg[i + 1] <= -180:
                frac = (phase_deg[i] + 180) / (phase_deg[i] - phase_deg[i + 1])
                wpc = w[i] * (w[i + 1] / w[i]) ** frac
                mag_at_pc = mag_db[i] + frac * (mag_db[i + 1] - mag_db[i])
                gm = -mag_at_pc
                break

        return {"pm": pm, "gm": gm, "wgc": wgc, "wpc": wpc}

    # =========================================================================
    # LaTeX label helpers
    # =========================================================================

    def _tf_labels(self) -> dict:
        """Generate LaTeX labels for block diagram."""
        preset = self.parameters["plant_preset"]
        K = float(self.parameters["plant_K"])

        plant_map = {
            "first_order": f"\\frac{{{K:.4g}}}{{s+1}}",
            "type1": f"\\frac{{{K:.4g}}}{{s(s+1)}}",
            "second_order": (
                f"\\frac{{{K * float(self.parameters['plant_wn'])**2:.4g}}}"
                f"{{s^2+{2*float(self.parameters['plant_zeta'])*float(self.parameters['plant_wn']):.4g}s"
                f"+{float(self.parameters['plant_wn'])**2:.4g}}}"
            ),
            "type1_two_poles": f"\\frac{{{K:.4g}}}{{s(s+1)(0.5s+1)}}",
            "dc_motor": f"\\frac{{{K:.4g}}}{{s(s+5)}}",
            "custom": "G(s)",
        }
        plant_latex = plant_map.get(preset, "G(s)")

        # Compensator label
        parts = []
        Kc = float(self.parameters["gain_Kc"])
        if abs(Kc - 1.0) > 0.001:
            parts.append(f"{Kc:.4g}")

        if self.parameters.get("lead_enable"):
            alpha = float(self.parameters["lead_alpha"])
            wm = float(self.parameters["lead_wm"])
            sqrt_a = np.sqrt(alpha)
            wz = wm * sqrt_a
            wp = wm / sqrt_a
            parts.append(f"\\frac{{{1/wz:.3g}s+1}}{{{1/wp:.3g}s+1}}")

        if self.parameters.get("lag_enable"):
            beta = float(self.parameters["lag_beta"])
            wm_lag = float(self.parameters["lag_wm"])
            sqrt_b = np.sqrt(beta)
            wz = wm_lag / sqrt_b
            wp = wm_lag * sqrt_b
            parts.append(f"\\frac{{{1/wz:.3g}s+1}}{{{1/wp:.3g}s+1}}")

        comp_latex = " \\cdot ".join(parts) if parts else "1"

        return {
            "plant_latex": plant_latex,
            "comp_latex": comp_latex,
        }

    # =========================================================================
    # Main computation pipeline
    # =========================================================================

    def _compute_with_info(self) -> tuple:
        """Core computation. Returns (plots_list, design_info_dict)."""
        p = self.parameters

        # Build transfer functions
        num_G, den_G = self._build_plant_tf()
        num_lead, den_lead = self._build_lead_tf()
        num_lag, den_lag = self._build_lag_tf()
        Kc = float(p["gain_Kc"])

        # Compensator C(s) = Kc · lead · lag
        num_C, den_C = self._convolve_tfs(
            [(num_lead, den_lead), (num_lag, den_lag)]
        )
        num_C = Kc * num_C

        # Open-loop L(s) = C(s) · G(s)
        num_L = np.convolve(num_C, num_G)
        den_L = np.convolve(den_C, den_G)

        # Closed-loop T(s) = L/(1+L) → num_T = num_L, den_T = den_L + num_L
        num_T = num_L.copy()
        den_T = np.polyadd(den_L, num_L)

        # Adaptive frequency range from system poles/zeros
        w = self._adaptive_freq_range(num_L, den_L)

        # Frequency responses
        H_G = self._freq_response(num_G, den_G, w)
        H_C = self._freq_response(num_C, den_C, w)
        H_L = self._freq_response(num_L, den_L, w)
        H_lead = self._freq_response(num_lead, den_lead, w)
        H_lag = self._freq_response(num_lag, den_lag, w)

        # Margins
        margins = self._compute_margins(w, H_L)

        # Design info
        design_info = self._build_design_info(margins, num_T, den_T)

        # Build plots
        show_comp = bool(p.get("show_components", True))
        pm_target = float(p.get("pm_target", 45))

        plots = [
            self._plot_bode_mag(w, H_G, H_C, H_L, margins, show_comp),
            self._plot_bode_phase(w, H_G, H_C, H_L, margins, pm_target, show_comp),
            self._plot_step_response(num_T, den_T),
            self._plot_pole_zero(num_L, den_L, num_T, den_T),
            self._plot_comp_phase(w, H_lead, H_lag, H_C),
            self._plot_nichols(w, H_L, margins),
        ]

        return plots, design_info

    @staticmethod
    def _adaptive_freq_range(num: np.ndarray, den: np.ndarray) -> np.ndarray:
        """Compute frequency range that captures all interesting features."""
        freqs = [1.0]
        for p in np.roots(den):
            if abs(p) > 1e-6:
                freqs.append(abs(p))
        if len(num) > 1:
            for z in np.roots(num):
                if abs(z) > 1e-6:
                    freqs.append(abs(z))
        w_min = max(1e-4, min(freqs) / 50)
        w_max = min(1e6, max(freqs) * 50)
        return np.logspace(np.log10(w_min), np.log10(w_max), 1000)

    def _build_design_info(self, margins: dict, num_T: np.ndarray,
                           den_T: np.ndarray) -> dict:
        """Compute design equations and derived quantities."""
        p = self.parameters
        info = {"Kc": float(p["gain_Kc"])}

        if p.get("lead_enable"):
            alpha = float(p["lead_alpha"])
            wm = float(p["lead_wm"])
            sqrt_a = np.sqrt(alpha)
            info["lead"] = {
                "alpha": round(alpha, 4),
                "wm": round(wm, 4),
                "phi_max": round(float(np.degrees(np.arcsin(
                    (1 - alpha) / (1 + alpha)))), 2),
                "wz": round(float(wm * sqrt_a), 4),
                "wp": round(float(wm / sqrt_a), 4),
                "hf_gain_db": round(float(-20 * np.log10(alpha)), 2),
            }

        if p.get("lag_enable"):
            beta = float(p["lag_beta"])
            wm_lag = float(p["lag_wm"])
            sqrt_b = np.sqrt(beta)
            info["lag"] = {
                "beta": round(beta, 4),
                "wm": round(wm_lag, 4),
                "phi_max_lag": round(float(-np.degrees(np.arcsin(
                    (1 - beta) / (1 + beta)))), 2),
                "wz": round(float(wm_lag / sqrt_b), 4),
                "wp": round(float(wm_lag * sqrt_b), 4),
                "lf_gain_boost_db": round(float(-20 * np.log10(beta)), 2),
            }

        # Margins
        info["pm"] = round(margins["pm"], 2) if margins["pm"] is not None else None
        info["gm"] = round(margins["gm"], 2) if margins["gm"] is not None else None
        info["wgc"] = round(margins["wgc"], 4) if margins["wgc"] is not None else None
        info["wpc"] = round(margins["wpc"], 4) if margins["wpc"] is not None else None

        # CL stability
        cl_poles = np.roots(den_T)
        stable_mask = np.real(cl_poles) < 0
        info["cl_stable"] = bool(np.all(stable_mask)) if len(cl_poles) > 0 else True
        info["cl_poles"] = [
            {"real": round(float(p.real), 6), "imag": round(float(p.imag), 6)}
            for p in cl_poles
        ]

        # Step metrics (computed here to avoid double step computation)
        if info["cl_stable"]:
            try:
                sys_cl = signal.TransferFunction(num_T, den_T)
                if len(cl_poles) > 0:
                    neg_real = np.real(cl_poles[stable_mask])
                    slowest = np.min(np.abs(neg_real)) if len(neg_real) > 0 else 1.0
                    t_end = min(50, max(5, 6.0 / max(slowest, 1e-6)))
                else:
                    t_end = 10
                t_arr = np.linspace(0, t_end, 500)
                _, y = signal.step(sys_cl, T=t_arr)
                ss_val = float(y[-1]) if len(y) > 0 else 0
                if abs(ss_val) > 1e-6:
                    info["step_metrics"] = self._step_metrics(t_arr, y, ss_val)
                    info["step_metrics"]["ss_error"] = round(abs(1.0 - ss_val), 4)
            except Exception:
                pass

        return info

    # =========================================================================
    # Step response metrics
    # =========================================================================

    @staticmethod
    def _step_metrics(t: np.ndarray, y: np.ndarray, ss_val: float) -> dict:
        """Compute rise time, overshoot, settling time."""
        metrics = {}
        if abs(ss_val) < 1e-6:
            return metrics

        # Rise time (10% → 90%)
        y10, y90 = 0.1 * ss_val, 0.9 * ss_val
        t10 = t90 = None
        for i in range(len(y) - 1):
            if t10 is None and y[i] <= y10 and y[i + 1] > y10:
                t10 = float(t[i])
            if t90 is None and y[i] <= y90 and y[i + 1] > y90:
                t90 = float(t[i])
                break
        if t10 is not None and t90 is not None:
            metrics["rise_time"] = round(t90 - t10, 4)

        # Overshoot
        if ss_val > 0:
            peak = float(np.max(y))
            os_pct = max(0, (peak - ss_val) / ss_val * 100)
            metrics["overshoot"] = round(os_pct, 2)

        # Settling time (2% band)
        tol = 0.02 * abs(ss_val)
        for i in range(len(y) - 1, -1, -1):
            if abs(y[i] - ss_val) > tol:
                metrics["settling_time"] = round(float(t[min(i + 1, len(t) - 1)]), 4)
                break

        return metrics

    # =========================================================================
    # Plot builders
    # =========================================================================

    def _plot_bode_mag(self, w, H_G, H_C, H_L, margins, show_comp):
        """Bode magnitude plot: plant, compensator, open-loop."""
        traces = []
        mag_L = 20 * np.log10(np.maximum(np.abs(H_L), 1e-30))

        if show_comp:
            mag_G = 20 * np.log10(np.maximum(np.abs(H_G), 1e-30))
            mag_C = 20 * np.log10(np.maximum(np.abs(H_C), 1e-30))
            traces.append({
                "x": w.tolist(), "y": mag_G.tolist(),
                "type": "scatter", "mode": "lines",
                "name": "Plant G(s)",
                "line": {"color": "#64748b", "width": 1.5, "dash": "dot"},
            })
            traces.append({
                "x": w.tolist(), "y": mag_C.tolist(),
                "type": "scatter", "mode": "lines",
                "name": "Comp C(s)",
                "line": {"color": "#f59e0b", "width": 1.5, "dash": "dash"},
            })

        traces.append({
            "x": w.tolist(), "y": mag_L.tolist(),
            "type": "scatter", "mode": "lines",
            "name": "Open-Loop L(s)",
            "line": {"color": "#3b82f6", "width": 2.5},
        })

        # 0 dB reference
        traces.append({
            "x": [float(w[0]), float(w[-1])], "y": [0, 0],
            "type": "scatter", "mode": "lines", "showlegend": False,
            "line": {"color": "rgba(148,163,184,0.3)", "width": 1, "dash": "dash"},
        })

        # Gain margin annotation
        if margins.get("wpc") is not None and margins.get("gm") is not None:
            wpc = margins["wpc"]
            gm = margins["gm"]
            traces.append({
                "x": [wpc, wpc], "y": [-gm, 0],
                "type": "scatter", "mode": "lines",
                "name": f"GM = {gm:.1f} dB",
                "line": {"color": "#ef4444", "width": 2},
            })

        # Gain crossover marker
        if margins.get("wgc") is not None:
            traces.append({
                "x": [margins["wgc"]], "y": [0],
                "type": "scatter", "mode": "markers",
                "name": f"\u03c9gc = {margins['wgc']:.2f}",
                "marker": {"color": "#10b981", "size": 10, "symbol": "diamond"},
            })

        return {
            "id": "bode_magnitude",
            "title": "Bode: Magnitude",
            "data": traces,
            "layout": {
                "xaxis": {"title": "Frequency (rad/s)", "type": "log",
                          "gridcolor": "rgba(148,163,184,0.1)"},
                "yaxis": {"title": "Magnitude (dB)",
                          "gridcolor": "rgba(148,163,184,0.1)"},
                "legend": {"x": 0.01, "y": 0.99, "bgcolor": "rgba(0,0,0,0)",
                           "font": {"size": 10}},
                "margin": {"t": 35, "r": 20, "b": 50, "l": 55},
            },
        }

    def _plot_bode_phase(self, w, H_G, H_C, H_L, margins, pm_target, show_comp):
        """Bode phase plot with PM annotation and target line."""
        traces = []
        phase_L = np.degrees(np.unwrap(np.angle(H_L)))

        if show_comp:
            phase_G = np.degrees(np.unwrap(np.angle(H_G)))
            phase_C = np.degrees(np.unwrap(np.angle(H_C)))
            traces.append({
                "x": w.tolist(), "y": phase_G.tolist(),
                "type": "scatter", "mode": "lines",
                "name": "Plant G(s)",
                "line": {"color": "#64748b", "width": 1.5, "dash": "dot"},
            })
            traces.append({
                "x": w.tolist(), "y": phase_C.tolist(),
                "type": "scatter", "mode": "lines",
                "name": "Comp C(s)",
                "line": {"color": "#f59e0b", "width": 1.5, "dash": "dash"},
            })

        traces.append({
            "x": w.tolist(), "y": phase_L.tolist(),
            "type": "scatter", "mode": "lines",
            "name": "Open-Loop L(s)",
            "line": {"color": "#3b82f6", "width": 2.5},
        })

        # -180° reference
        traces.append({
            "x": [float(w[0]), float(w[-1])], "y": [-180, -180],
            "type": "scatter", "mode": "lines", "showlegend": False,
            "line": {"color": "rgba(148,163,184,0.3)", "width": 1, "dash": "dash"},
        })

        # PM target line
        if pm_target > 0:
            target_phase = -180 + pm_target
            traces.append({
                "x": [float(w[0]), float(w[-1])],
                "y": [target_phase, target_phase],
                "type": "scatter", "mode": "lines",
                "name": f"PM target ({pm_target}\u00b0)",
                "line": {"color": "rgba(16,185,129,0.4)", "width": 1.5, "dash": "dashdot"},
            })

        # PM annotation
        if margins.get("wgc") is not None and margins.get("pm") is not None:
            wgc = margins["wgc"]
            pm = margins["pm"]
            traces.append({
                "x": [wgc, wgc], "y": [-180, -180 + pm],
                "type": "scatter", "mode": "lines",
                "name": f"PM = {pm:.1f}\u00b0",
                "line": {"color": "#10b981", "width": 2},
            })

        return {
            "id": "bode_phase",
            "title": "Bode: Phase",
            "data": traces,
            "layout": {
                "xaxis": {"title": "Frequency (rad/s)", "type": "log",
                          "gridcolor": "rgba(148,163,184,0.1)"},
                "yaxis": {"title": "Phase (deg)",
                          "gridcolor": "rgba(148,163,184,0.1)"},
                "legend": {"x": 0.01, "y": 0.01, "bgcolor": "rgba(0,0,0,0)",
                           "font": {"size": 10}},
                "margin": {"t": 35, "r": 20, "b": 50, "l": 55},
            },
        }

    def _plot_step_response(self, num_T, den_T):
        """Closed-loop step response with performance annotations."""
        traces = []
        cl_poles = np.roots(den_T)
        is_stable = len(cl_poles) == 0 or np.all(np.real(cl_poles) < 0)

        if is_stable and len(den_T) > 0:
            try:
                sys_cl = signal.TransferFunction(num_T, den_T)
                if len(cl_poles) > 0:
                    neg = np.real(cl_poles[np.real(cl_poles) < 0])
                    slowest = np.min(np.abs(neg)) if len(neg) > 0 else 1.0
                    t_end = min(50, max(5, 6.0 / max(slowest, 1e-6)))
                else:
                    t_end = 10
                t = np.linspace(0, t_end, 500)
                t_out, y = signal.step(sys_cl, T=t)

                ss_val = float(y[-1]) if len(y) > 0 else 0

                traces.append({
                    "x": t_out.tolist(), "y": y.tolist(),
                    "type": "scatter", "mode": "lines",
                    "name": "Step Response",
                    "line": {"color": "#3b82f6", "width": 2},
                })
                # Unit reference
                traces.append({
                    "x": [float(t_out[0]), float(t_out[-1])], "y": [1.0, 1.0],
                    "type": "scatter", "mode": "lines",
                    "name": "Reference",
                    "line": {"color": "rgba(16,185,129,0.4)", "width": 1, "dash": "dash"},
                })
                # SS value
                if abs(ss_val) > 1e-6 and abs(ss_val - 1.0) > 0.001:
                    traces.append({
                        "x": [float(t_out[0]), float(t_out[-1])],
                        "y": [ss_val, ss_val],
                        "type": "scatter", "mode": "lines",
                        "name": f"SS = {ss_val:.3f}",
                        "line": {"color": "rgba(148,163,184,0.3)", "width": 1, "dash": "dot"},
                    })
                title = "Closed-Loop Step Response"
            except Exception:
                traces.append({
                    "x": [0], "y": [0], "type": "scatter", "mode": "markers",
                    "name": "Error", "marker": {"color": "#ef4444"},
                })
                title = "Step Response \u2014 computation error"
        else:
            try:
                sys_cl = signal.TransferFunction(num_T, den_T)
                t = np.linspace(0, 5, 500)
                t_out, y = signal.step(sys_cl, T=t)
                y = np.clip(y, -100, 100)
                traces.append({
                    "x": t_out.tolist(), "y": y.tolist(),
                    "type": "scatter", "mode": "lines",
                    "name": "UNSTABLE",
                    "line": {"color": "#ef4444", "width": 2},
                })
            except Exception:
                traces.append({
                    "x": [0, 5], "y": [0, 0], "type": "scatter", "mode": "lines",
                    "name": "Unstable", "line": {"color": "#ef4444"},
                })
            title = "Step Response \u2014 UNSTABLE"

        return {
            "id": "step_response",
            "title": title,
            "data": traces,
            "layout": {
                "xaxis": {"title": "Time (s)",
                          "gridcolor": "rgba(148,163,184,0.1)"},
                "yaxis": {"title": "Output y(t)",
                          "gridcolor": "rgba(148,163,184,0.1)"},
                "margin": {"t": 35, "r": 20, "b": 50, "l": 55},
                "legend": {"x": 0.6, "y": 0.99, "bgcolor": "rgba(0,0,0,0)",
                           "font": {"size": 10}},
            },
        }

    def _plot_pole_zero(self, num_L, den_L, num_T, den_T):
        """Pole-zero map showing OL and CL poles/zeros."""
        traces = []
        ol_poles = np.roots(den_L)
        ol_zeros = np.roots(num_L) if len(num_L) > 1 else np.array([])
        cl_poles = np.roots(den_T)
        cl_zeros = np.roots(num_T) if len(num_T) > 1 else np.array([])

        if len(ol_poles) > 0:
            traces.append({
                "x": np.real(ol_poles).tolist(),
                "y": np.imag(ol_poles).tolist(),
                "type": "scatter", "mode": "markers",
                "name": "OL Poles",
                "marker": {"color": "rgba(100,116,139,0.5)", "size": 10,
                           "symbol": "x-thin", "line": {"width": 2}},
            })
        if len(ol_zeros) > 0:
            traces.append({
                "x": np.real(ol_zeros).tolist(),
                "y": np.imag(ol_zeros).tolist(),
                "type": "scatter", "mode": "markers",
                "name": "OL Zeros",
                "marker": {"color": "rgba(100,116,139,0.5)", "size": 10,
                           "symbol": "circle-open", "line": {"width": 2}},
            })
        if len(cl_poles) > 0:
            colors = [
                "#10b981" if p.real < -1e-10 else
                "#f59e0b" if abs(p.real) < 1e-10 else "#ef4444"
                for p in cl_poles
            ]
            traces.append({
                "x": np.real(cl_poles).tolist(),
                "y": np.imag(cl_poles).tolist(),
                "type": "scatter", "mode": "markers",
                "name": "CL Poles",
                "marker": {"color": colors, "size": 12, "symbol": "x",
                           "line": {"width": 3}},
            })
        if len(cl_zeros) > 0:
            traces.append({
                "x": np.real(cl_zeros).tolist(),
                "y": np.imag(cl_zeros).tolist(),
                "type": "scatter", "mode": "markers",
                "name": "CL Zeros",
                "marker": {"color": "#3b82f6", "size": 10,
                           "symbol": "circle-open",
                           "line": {"width": 2, "color": "#3b82f6"}},
            })

        # Axis range
        all_pts = np.concatenate(
            [a for a in [ol_poles, cl_poles, ol_zeros, cl_zeros] if len(a) > 0]
        ) if any(len(a) > 0 for a in [ol_poles, cl_poles, ol_zeros, cl_zeros]) else np.array([0])
        rng = max(
            np.max(np.abs(np.real(all_pts))),
            np.max(np.abs(np.imag(all_pts))),
            1
        ) * 1.3

        # jω axis
        traces.append({
            "x": [0, 0], "y": [-rng, rng],
            "type": "scatter", "mode": "lines", "showlegend": False,
            "line": {"color": "rgba(148,163,184,0.2)", "width": 1},
        })

        return {
            "id": "pole_zero_map",
            "title": "Pole-Zero Map",
            "data": traces,
            "layout": {
                "xaxis": {"title": "Real", "gridcolor": "rgba(148,163,184,0.1)",
                          "scaleanchor": "y"},
                "yaxis": {"title": "Imag", "gridcolor": "rgba(148,163,184,0.1)"},
                "margin": {"t": 35, "r": 20, "b": 50, "l": 55},
                "legend": {"x": 0.01, "y": 0.99, "bgcolor": "rgba(0,0,0,0)",
                           "font": {"size": 10}},
            },
        }

    def _plot_comp_phase(self, w, H_lead, H_lag, H_C):
        """Phase contribution breakdown of lead and lag sections."""
        traces = []
        p = self.parameters
        phase_lead = np.degrees(np.angle(H_lead))
        phase_lag = np.degrees(np.angle(H_lag))
        phase_total = np.degrees(np.angle(H_C))

        if p.get("lead_enable"):
            alpha = float(p["lead_alpha"])
            wm = float(p["lead_wm"])
            phi_max = float(np.degrees(np.arcsin((1 - alpha) / (1 + alpha))))
            traces.append({
                "x": w.tolist(), "y": phase_lead.tolist(),
                "type": "scatter", "mode": "lines",
                "name": "Lead Phase",
                "line": {"color": "#10b981", "width": 2},
            })
            traces.append({
                "x": [wm], "y": [phi_max],
                "type": "scatter", "mode": "markers+text",
                "name": f"\u03c6_max = {phi_max:.1f}\u00b0",
                "text": [f" {phi_max:.1f}\u00b0"],
                "textposition": "top right",
                "textfont": {"color": "#10b981", "size": 11},
                "marker": {"color": "#10b981", "size": 10, "symbol": "star"},
            })

        if p.get("lag_enable"):
            beta = float(p["lag_beta"])
            wm_lag = float(p["lag_wm"])
            phi_lag = float(-np.degrees(np.arcsin((1 - beta) / (1 + beta))))
            traces.append({
                "x": w.tolist(), "y": phase_lag.tolist(),
                "type": "scatter", "mode": "lines",
                "name": "Lag Phase",
                "line": {"color": "#ef4444", "width": 2},
            })
            traces.append({
                "x": [wm_lag], "y": [phi_lag],
                "type": "scatter", "mode": "markers+text",
                "name": f"\u03c6_lag = {phi_lag:.1f}\u00b0",
                "text": [f" {phi_lag:.1f}\u00b0"],
                "textposition": "bottom right",
                "textfont": {"color": "#ef4444", "size": 11},
                "marker": {"color": "#ef4444", "size": 10, "symbol": "star"},
            })

        if p.get("lead_enable") or p.get("lag_enable"):
            traces.append({
                "x": w.tolist(), "y": phase_total.tolist(),
                "type": "scatter", "mode": "lines",
                "name": "Total C(s)",
                "line": {"color": "#f59e0b", "width": 2, "dash": "dash"},
            })

        # 0° reference
        traces.append({
            "x": [float(w[0]), float(w[-1])], "y": [0, 0],
            "type": "scatter", "mode": "lines", "showlegend": False,
            "line": {"color": "rgba(148,163,184,0.2)", "width": 1, "dash": "dot"},
        })

        return {
            "id": "compensator_phase",
            "title": "Compensator Phase Breakdown",
            "data": traces,
            "layout": {
                "xaxis": {"title": "Frequency (rad/s)", "type": "log",
                          "gridcolor": "rgba(148,163,184,0.1)"},
                "yaxis": {"title": "Phase (deg)",
                          "gridcolor": "rgba(148,163,184,0.1)"},
                "margin": {"t": 35, "r": 20, "b": 50, "l": 55},
                "legend": {"x": 0.01, "y": 0.99, "bgcolor": "rgba(0,0,0,0)",
                           "font": {"size": 10}},
            },
        }

    def _plot_nichols(self, w, H_L, margins):
        """Nichols chart: OL gain (dB) vs OL phase (deg)."""
        mag_db = 20 * np.log10(np.maximum(np.abs(H_L), 1e-30))
        phase_deg = np.degrees(np.unwrap(np.angle(H_L)))

        traces = [{
            "x": phase_deg.tolist(), "y": mag_db.tolist(),
            "type": "scatter", "mode": "lines",
            "name": "L(j\u03c9)",
            "line": {"color": "#3b82f6", "width": 2},
        }]

        # Critical point (-180°, 0 dB)
        traces.append({
            "x": [-180], "y": [0],
            "type": "scatter", "mode": "markers",
            "name": "Critical Point",
            "marker": {"color": "#ef4444", "size": 12, "symbol": "x",
                       "line": {"width": 3}},
        })

        # Reference lines
        y_min, y_max = float(np.min(mag_db)), float(np.max(mag_db))
        x_min, x_max = float(np.min(phase_deg)), float(np.max(phase_deg))
        traces.append({
            "x": [-180, -180], "y": [y_min, y_max],
            "type": "scatter", "mode": "lines", "showlegend": False,
            "line": {"color": "rgba(239,68,68,0.2)", "width": 1, "dash": "dash"},
        })
        traces.append({
            "x": [x_min, x_max], "y": [0, 0],
            "type": "scatter", "mode": "lines", "showlegend": False,
            "line": {"color": "rgba(148,163,184,0.2)", "width": 1, "dash": "dash"},
        })

        # PM marker on Nichols
        if margins.get("pm") is not None and margins.get("wgc") is not None:
            pm = margins["pm"]
            traces.append({
                "x": [-180 + pm], "y": [0],
                "type": "scatter", "mode": "markers+text",
                "name": f"PM = {pm:.1f}\u00b0",
                "text": [f"PM={pm:.1f}\u00b0"],
                "textposition": "top center",
                "textfont": {"size": 10, "color": "#10b981"},
                "marker": {"color": "#10b981", "size": 8, "symbol": "diamond"},
            })

        return {
            "id": "nichols_chart",
            "title": "Nichols Chart",
            "data": traces,
            "layout": {
                "xaxis": {"title": "Open-Loop Phase (deg)",
                          "gridcolor": "rgba(148,163,184,0.1)"},
                "yaxis": {"title": "Open-Loop Gain (dB)",
                          "gridcolor": "rgba(148,163,184,0.1)"},
                "margin": {"t": 35, "r": 20, "b": 50, "l": 55},
                "legend": {"x": 0.01, "y": 0.99, "bgcolor": "rgba(0,0,0,0)",
                           "font": {"size": 10}},
            },
        }
