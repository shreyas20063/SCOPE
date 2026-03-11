"""Controller Tuning Lab — PID/Lead-Lag controller design and auto-tuning."""

from .base_simulator import BaseSimulator
import numpy as np
from scipy import signal, optimize

# NumPy 2.0 compat
_trapz = np.trapezoid if hasattr(np, 'trapezoid') else np.trapz


class ControllerTuningLabSimulator(BaseSimulator):
    """Unified controller design environment with plant selection,
    PID/Lead-Lag tuning, 6 auto-tune methods, and 7 analysis plots."""

    PARAMETER_SCHEMA = {
        # ===== PLANT SELECTION =====
        "plant_preset": {
            "type": "select",
            "options": [
                {"value": "first_order", "label": "1st Order: K/(τs+1)"},
                {"value": "second_order", "label": "2nd Order: Kω²/(s²+2ζωs+ω²)"},
                {"value": "integrator", "label": "Integrator: K/s"},
                {"value": "double_integrator", "label": "Double Integrator: K/s²"},
                {"value": "fopdt", "label": "1st Order + Delay: Ke^(-Ls)/(τs+1)"},
                {"value": "dc_motor", "label": "DC Motor: K/(s(Js+b))"},
                {"value": "unstable", "label": "Unstable: K/(s-a)"},
                {"value": "custom", "label": "Custom TF (enter coefficients)"},
            ],
            "default": "first_order",
            "group": "Plant",
        },
        "plant_gain": {
            "type": "slider", "min": 0.1, "max": 20, "step": 0.1, "default": 1.0,
            "label": "Plant Gain K", "unit": "", "group": "Plant",
        },
        "plant_tau": {
            "type": "slider", "min": 0.1, "max": 10, "step": 0.1, "default": 1.0,
            "label": "Time Constant τ", "unit": "s", "group": "Plant",
            "visible_when": {"plant_preset": ["first_order", "fopdt"]},
        },
        "plant_zeta": {
            "type": "slider", "min": 0.05, "max": 2.0, "step": 0.01, "default": 0.5,
            "label": "Damping Ratio ζ", "unit": "", "group": "Plant",
            "visible_when": {"plant_preset": "second_order"},
        },
        "plant_omega": {
            "type": "slider", "min": 0.5, "max": 20, "step": 0.5, "default": 5.0,
            "label": "Natural Freq ωn", "unit": "rad/s", "group": "Plant",
            "visible_when": {"plant_preset": "second_order"},
        },
        "plant_delay": {
            "type": "slider", "min": 0.01, "max": 5.0, "step": 0.01, "default": 0.5,
            "label": "Time Delay L", "unit": "s", "group": "Plant",
            "visible_when": {"plant_preset": "fopdt"},
        },
        "plant_J": {
            "type": "slider", "min": 0.01, "max": 2.0, "step": 0.01, "default": 0.1,
            "label": "Inertia J", "unit": "kg·m²", "group": "Plant",
            "visible_when": {"plant_preset": "dc_motor"},
        },
        "plant_b": {
            "type": "slider", "min": 0.01, "max": 2.0, "step": 0.01, "default": 0.5,
            "label": "Friction b", "unit": "N·m·s", "group": "Plant",
            "visible_when": {"plant_preset": "dc_motor"},
        },
        "plant_a": {
            "type": "slider", "min": 0.1, "max": 10, "step": 0.1, "default": 1.0,
            "label": "Unstable Pole a", "unit": "", "group": "Plant",
            "visible_when": {"plant_preset": "unstable"},
        },
        "custom_num": {
            "type": "expression", "default": "1",
            "label": "Numerator Coefficients", "group": "Plant",
            "placeholder": "e.g. 1  or  1, 2  (descending powers of s)",
            "visible_when": {"plant_preset": "custom"},
        },
        "custom_den": {
            "type": "expression", "default": "1, 1",
            "label": "Denominator Coefficients", "group": "Plant",
            "placeholder": "e.g. 1, 3, 2  for s²+3s+2",
            "visible_when": {"plant_preset": "custom"},
        },
        # ===== CONTROLLER TYPE =====
        "controller_type": {
            "type": "select",
            "options": [
                {"value": "P", "label": "P (Proportional)"},
                {"value": "PI", "label": "PI (Proportional-Integral)"},
                {"value": "PD", "label": "PD (Proportional-Derivative)"},
                {"value": "PID", "label": "PID (Full)"},
                {"value": "lead_lag", "label": "Lead-Lag Compensator"},
                {"value": "state_feedback", "label": "State Feedback (manual K)"},
                {"value": "pole_placement", "label": "Pole Placement"},
                {"value": "lqr", "label": "LQR (Optimal)"},
            ],
            "default": "PID",
            "group": "Controller",
        },
        "Kp": {
            "type": "slider", "min": 0, "max": 100, "step": 0.01, "default": 1.0,
            "label": "Proportional Gain Kp", "group": "Controller",
            "visible_when": {"controller_type": ["P", "PI", "PD", "PID"]},
        },
        "Ki": {
            "type": "slider", "min": 0, "max": 100, "step": 0.01, "default": 0.0,
            "label": "Integral Gain Ki", "group": "Controller",
            "visible_when": {"controller_type": ["PI", "PID"]},
        },
        "Kd": {
            "type": "slider", "min": 0, "max": 100, "step": 0.01, "default": 0.0,
            "label": "Derivative Gain Kd", "group": "Controller",
            "visible_when": {"controller_type": ["PD", "PID"]},
        },
        "deriv_filter_N": {
            "type": "slider", "min": 1, "max": 200, "step": 1, "default": 20,
            "label": "Derivative Filter N", "group": "Controller",
            "visible_when": {"controller_type": ["PD", "PID"]},
        },
        "lead_lag_Kc": {
            "type": "slider", "min": 0.01, "max": 50, "step": 0.01, "default": 1.0,
            "label": "Compensator Gain Kc", "group": "Controller",
            "visible_when": {"controller_type": "lead_lag"},
        },
        "lead_lag_zero": {
            "type": "slider", "min": 0.1, "max": 50, "step": 0.1, "default": 2.0,
            "label": "Zero Location z", "group": "Controller",
            "visible_when": {"controller_type": "lead_lag"},
        },
        "lead_lag_pole": {
            "type": "slider", "min": 0.1, "max": 50, "step": 0.1, "default": 10.0,
            "label": "Pole Location p", "group": "Controller",
            "visible_when": {"controller_type": "lead_lag"},
        },
        # ===== STATE FEEDBACK GAINS =====
        "sf_k1": {
            "type": "slider", "min": -50, "max": 50, "step": 0.1, "default": 1.0,
            "label": "K\u2081 (state 1)", "group": "Controller",
            "visible_when": {"controller_type": ["state_feedback"]},
        },
        "sf_k2": {
            "type": "slider", "min": -50, "max": 50, "step": 0.1, "default": 0.0,
            "label": "K\u2082 (state 2)", "group": "Controller",
            "visible_when": {"controller_type": ["state_feedback"]},
        },
        "sf_k3": {
            "type": "slider", "min": -50, "max": 50, "step": 0.1, "default": 0.0,
            "label": "K\u2083 (state 3)", "group": "Controller",
            "visible_when": {"controller_type": ["state_feedback"]},
        },
        "sf_k4": {
            "type": "slider", "min": -50, "max": 50, "step": 0.1, "default": 0.0,
            "label": "K\u2084 (state 4)", "group": "Controller",
            "visible_when": {"controller_type": ["state_feedback"]},
        },
        # ===== POLE PLACEMENT =====
        "pp_pole1_real": {
            "type": "slider", "min": -20, "max": 0, "step": 0.1, "default": -2.0,
            "label": "Pole 1 Real", "group": "Controller",
            "visible_when": {"controller_type": "pole_placement"},
        },
        "pp_pole1_imag": {
            "type": "slider", "min": -20, "max": 20, "step": 0.1, "default": 0.0,
            "label": "Pole 1 Imag", "group": "Controller",
            "visible_when": {"controller_type": "pole_placement"},
        },
        "pp_pole2_real": {
            "type": "slider", "min": -20, "max": 0, "step": 0.1, "default": -3.0,
            "label": "Pole 2 Real", "group": "Controller",
            "visible_when": {"controller_type": "pole_placement"},
        },
        "pp_pole2_imag": {
            "type": "slider", "min": -20, "max": 20, "step": 0.1, "default": 0.0,
            "label": "Pole 2 Imag", "group": "Controller",
            "visible_when": {"controller_type": "pole_placement"},
        },
        "pp_pole3_real": {
            "type": "slider", "min": -20, "max": 0, "step": 0.1, "default": -5.0,
            "label": "Pole 3 Real", "group": "Controller",
            "visible_when": {"controller_type": "pole_placement"},
        },
        "pp_pole3_imag": {
            "type": "slider", "min": -20, "max": 20, "step": 0.1, "default": 0.0,
            "label": "Pole 3 Imag", "group": "Controller",
            "visible_when": {"controller_type": "pole_placement"},
        },
        "pp_pole4_real": {
            "type": "slider", "min": -20, "max": 0, "step": 0.1, "default": -7.0,
            "label": "Pole 4 Real", "group": "Controller",
            "visible_when": {"controller_type": "pole_placement"},
        },
        "pp_pole4_imag": {
            "type": "slider", "min": -20, "max": 20, "step": 0.1, "default": 0.0,
            "label": "Pole 4 Imag", "group": "Controller",
            "visible_when": {"controller_type": "pole_placement"},
        },
        "apply_pole_placement": {
            "type": "button", "label": "Compute K", "group": "Controller",
            "visible_when": {"controller_type": "pole_placement"},
        },
        # ===== LQR =====
        "lqr_q1": {
            "type": "slider", "min": 0.01, "max": 100, "step": 0.1, "default": 1.0,
            "label": "Q\u2081\u2081 (state 1 weight)", "group": "Controller",
            "visible_when": {"controller_type": "lqr"},
        },
        "lqr_q2": {
            "type": "slider", "min": 0.01, "max": 100, "step": 0.1, "default": 1.0,
            "label": "Q\u2082\u2082 (state 2 weight)", "group": "Controller",
            "visible_when": {"controller_type": "lqr"},
        },
        "lqr_q3": {
            "type": "slider", "min": 0.01, "max": 100, "step": 0.1, "default": 1.0,
            "label": "Q\u2083\u2083 (state 3 weight)", "group": "Controller",
            "visible_when": {"controller_type": "lqr"},
        },
        "lqr_q4": {
            "type": "slider", "min": 0.01, "max": 100, "step": 0.1, "default": 1.0,
            "label": "Q\u2084\u2084 (state 4 weight)", "group": "Controller",
            "visible_when": {"controller_type": "lqr"},
        },
        "lqr_r": {
            "type": "slider", "min": 0.001, "max": 100, "step": 0.01, "default": 1.0,
            "label": "R (control weight)", "group": "Controller",
            "visible_when": {"controller_type": "lqr"},
        },
        "apply_lqr": {
            "type": "button", "label": "Compute LQR K", "group": "Controller",
            "visible_when": {"controller_type": "lqr"},
        },
        # ===== TUNING METHOD =====
        "tuning_method": {
            "type": "select",
            "options": [
                {"value": "manual", "label": "Manual (use sliders)"},
                {"value": "zn_open", "label": "Ziegler-Nichols (Open-Loop)"},
                {"value": "zn_closed", "label": "Ziegler-Nichols (Closed-Loop)"},
                {"value": "cohen_coon", "label": "Cohen-Coon"},
                {"value": "lambda_tuning", "label": "Lambda Tuning"},
                {"value": "imc", "label": "IMC Tuning"},
                {"value": "itae_optimal", "label": "ITAE Optimal (Numerical)"},
            ],
            "default": "manual",
            "group": "Tuning",
            "visible_when": {"controller_type": ["P", "PI", "PD", "PID"]},
        },
        "lambda_cl_tau": {
            "type": "slider", "min": 0.1, "max": 10, "step": 0.1, "default": 1.0,
            "label": "Desired CL Time Constant λ", "unit": "s", "group": "Tuning",
            "visible_when": {"tuning_method": "lambda_tuning"},
        },
        "apply_tuning": {
            "type": "button", "label": "Apply Auto-Tune", "group": "Tuning",
            "visible_when": {"tuning_method": [
                "zn_open", "zn_closed", "cohen_coon",
                "lambda_tuning", "imc", "itae_optimal",
            ]},
        },
        # ===== DISPLAY / REFERENCE =====
        "sim_duration": {
            "type": "slider", "min": 1, "max": 30, "step": 0.5, "default": 10,
            "label": "Simulation Duration", "unit": "s", "group": "Display",
        },
        "save_reference": {
            "type": "button", "label": "Save as Reference", "group": "Display",
        },
        "clear_references": {
            "type": "button", "label": "Clear All References", "group": "Display",
        },
    }

    DEFAULT_PARAMS = {
        "plant_preset": "first_order",
        "plant_gain": 1.0,
        "plant_tau": 1.0,
        "plant_zeta": 0.5,
        "plant_omega": 5.0,
        "plant_delay": 0.5,
        "plant_J": 0.1,
        "plant_b": 0.5,
        "plant_a": 1.0,
        "custom_num": "1",
        "custom_den": "1, 1",
        "controller_type": "PID",
        "Kp": 1.0,
        "Ki": 0.0,
        "Kd": 0.0,
        "deriv_filter_N": 20,
        "lead_lag_Kc": 1.0,
        "lead_lag_zero": 2.0,
        "lead_lag_pole": 10.0,
        "tuning_method": "manual",
        "lambda_cl_tau": 1.0,
        "sim_duration": 10,
        "sf_k1": 1.0, "sf_k2": 0.0, "sf_k3": 0.0, "sf_k4": 0.0,
        "pp_pole1_real": -2.0, "pp_pole1_imag": 0.0,
        "pp_pole2_real": -3.0, "pp_pole2_imag": 0.0,
        "pp_pole3_real": -5.0, "pp_pole3_imag": 0.0,
        "pp_pole4_real": -7.0, "pp_pole4_imag": 0.0,
        "lqr_q1": 1.0, "lqr_q2": 1.0, "lqr_q3": 1.0, "lqr_q4": 1.0,
        "lqr_r": 1.0,
    }

    def initialize(self, params: dict | None = None) -> None:
        self.parameters = {**self.DEFAULT_PARAMS, **(params or {})}
        for name, value in self.parameters.items():
            if name in self.PARAMETER_SCHEMA:
                self.parameters[name] = self._validate_param(name, value)
        self._plant_num = np.array([1.0])
        self._plant_den = np.array([1.0, 1.0])
        self._ctrl_num = np.array([1.0])
        self._ctrl_den = np.array([1.0])
        self._ol_num = np.array([1.0])
        self._ol_den = np.array([1.0, 1.0])
        self._cl_num = np.array([1.0])
        self._cl_den = np.array([1.0, 1.0])
        self._reference_responses: list[dict] = []
        self._tuning_info: str | None = None
        # State-space cache for modern controllers
        self._A = np.array([[0.0]])
        self._B = np.array([[1.0]])
        self._C = np.array([[1.0]])
        self._D = np.array([[0.0]])
        self._plant_order = 1
        self._is_controllable = True
        self._state_feedback_mode = False
        self._state_feedback_K: np.ndarray | None = None
        self._initialized = True

    def update_parameter(self, name: str, value) -> dict:
        if name in self.PARAMETER_SCHEMA:
            self.parameters[name] = self._validate_param(name, value)
        elif name in self.parameters:
            self.parameters[name] = value
        return self.get_state()

    # =========================================================================
    # Plant construction
    # =========================================================================

    @staticmethod
    def _parse_poly_string(s: str) -> np.ndarray:
        """Parse comma-separated coefficient string to numpy array."""
        parts = [p.strip() for p in str(s).split(",")]
        coeffs = [float(p) for p in parts if p]
        return np.array(coeffs) if coeffs else np.array([1.0])

    def _build_plant_tf(self) -> None:
        """Build plant transfer function from current parameters."""
        p = self.parameters
        preset = p.get("plant_preset", "first_order")
        K = float(p.get("plant_gain", 1.0))

        if preset == "first_order":
            tau = float(p.get("plant_tau", 1.0))
            self._plant_num = np.array([K])
            self._plant_den = np.array([tau, 1.0])
        elif preset == "second_order":
            zeta = float(p.get("plant_zeta", 0.5))
            omega = float(p.get("plant_omega", 5.0))
            self._plant_num = np.array([K * omega**2])
            self._plant_den = np.array([1.0, 2 * zeta * omega, omega**2])
        elif preset == "integrator":
            self._plant_num = np.array([K])
            self._plant_den = np.array([1.0, 0.0])
        elif preset == "double_integrator":
            self._plant_num = np.array([K])
            self._plant_den = np.array([1.0, 0.0, 0.0])
        elif preset == "fopdt":
            tau = float(p.get("plant_tau", 1.0))
            delay = float(p.get("plant_delay", 0.5))
            delay = max(delay, 0.001)
            pade_num, pade_den = signal.pade(delay, 3)
            self._plant_num = np.convolve([K], pade_num)
            self._plant_den = np.convolve([tau, 1.0], pade_den)
        elif preset == "dc_motor":
            J = float(p.get("plant_J", 0.1))
            b = float(p.get("plant_b", 0.5))
            self._plant_num = np.array([K])
            self._plant_den = np.array([J, b, 0.0])
        elif preset == "unstable":
            a = float(p.get("plant_a", 1.0))
            self._plant_num = np.array([K])
            self._plant_den = np.array([1.0, -a])
        elif preset == "custom":
            try:
                self._plant_num = self._parse_poly_string(p.get("custom_num", "1"))
                self._plant_den = self._parse_poly_string(p.get("custom_den", "1, 1"))
                if len(self._plant_den) < 1 or self._plant_den[0] == 0:
                    self._plant_den = np.array([1.0, 1.0])
            except (ValueError, TypeError):
                self._plant_num = np.array([1.0])
                self._plant_den = np.array([1.0, 1.0])
        else:
            self._plant_num = np.array([K])
            self._plant_den = np.array([1.0, 1.0])

        # TF → state-space conversion for modern controllers
        try:
            A, B, C, D = signal.tf2ss(self._plant_num, self._plant_den)
            self._A = np.atleast_2d(A)
            self._B = B.reshape(-1, 1) if B.ndim == 1 else np.atleast_2d(B)
            self._C = C.reshape(1, -1) if C.ndim == 1 else np.atleast_2d(C)
            self._D = np.atleast_2d(D)
            self._plant_order = self._A.shape[0]
            n = self._plant_order
            ctrb_cols = [np.linalg.matrix_power(self._A, i) @ self._B for i in range(n)]
            ctrb = np.hstack(ctrb_cols)
            self._is_controllable = int(np.linalg.matrix_rank(ctrb)) >= n
        except Exception:
            self._plant_order = 1
            self._is_controllable = True

    # =========================================================================
    # Controller construction
    # =========================================================================

    def _build_controller_tf(self) -> None:
        """Build controller transfer function from current parameters."""
        p = self.parameters
        ctype = p.get("controller_type", "PID")
        Kp = float(p.get("Kp", 1.0))
        Ki = float(p.get("Ki", 0.0))
        Kd = float(p.get("Kd", 0.0))
        N = float(p.get("deriv_filter_N", 20))

        if ctype == "P":
            self._ctrl_num = np.array([Kp])
            self._ctrl_den = np.array([1.0])
        elif ctype == "PI":
            # C(s) = Kp + Ki/s = (Kp*s + Ki) / s
            self._ctrl_num = np.array([Kp, Ki])
            self._ctrl_den = np.array([1.0, 0.0])
        elif ctype == "PD":
            # C(s) = Kp + Kd*N*s/(s+N) = ((Kp+Kd*N)*s + Kp*N) / (s+N)
            self._ctrl_num = np.array([Kp + Kd * N, Kp * N])
            self._ctrl_den = np.array([1.0, N])
        elif ctype == "PID":
            # C(s) = Kp + Ki/s + Kd*N*s/(s+N)
            has_i = abs(Ki) > 1e-12
            has_d = abs(Kd) > 1e-12
            if has_i and has_d:
                # Full PID: common denom s*(s+N)
                # Num: (Kp + Kd*N)*s² + (Kp*N + Ki)*s + Ki*N
                self._ctrl_num = np.array([Kp + Kd * N, Kp * N + Ki, Ki * N])
                self._ctrl_den = np.array([1.0, N, 0.0])
            elif has_i:
                # PI: C(s) = (Kp*s + Ki) / s
                self._ctrl_num = np.array([Kp, Ki])
                self._ctrl_den = np.array([1.0, 0.0])
            elif has_d:
                # PD: C(s) = ((Kp+Kd*N)*s + Kp*N) / (s+N)
                self._ctrl_num = np.array([Kp + Kd * N, Kp * N])
                self._ctrl_den = np.array([1.0, N])
            else:
                # Just P
                self._ctrl_num = np.array([Kp])
                self._ctrl_den = np.array([1.0])
        elif ctype == "lead_lag":
            Kc = float(p.get("lead_lag_Kc", 1.0))
            zero = float(p.get("lead_lag_zero", 2.0))
            pole = float(p.get("lead_lag_pole", 10.0))
            self._ctrl_num = np.array([Kc, Kc * zero])
            self._ctrl_den = np.array([1.0, pole])
        elif ctype in ("state_feedback", "pole_placement", "lqr"):
            K_vec = self._get_state_feedback_K()
            if K_vec is not None and self._is_controllable:
                A_cl = self._A - self._B @ K_vec.reshape(1, -1)
                cl_ss = signal.StateSpace(A_cl, self._B, self._C, self._D)
                cl_tf = cl_ss.to_tf()
                self._cl_num = np.atleast_1d(cl_tf.num)
                self._cl_den = np.atleast_1d(cl_tf.den)
                self._ctrl_num = np.array([1.0])
                self._ctrl_den = np.array([1.0])
                self._state_feedback_mode = True
                self._state_feedback_K = K_vec
                return
            else:
                self._ctrl_num = np.array([1.0])
                self._ctrl_den = np.array([1.0])
                self._state_feedback_mode = True
                self._state_feedback_K = K_vec
                return
        else:
            self._ctrl_num = np.array([Kp])
            self._ctrl_den = np.array([1.0])
        self._state_feedback_mode = False
        self._state_feedback_K = None

    # =========================================================================
    # State-feedback helpers
    # =========================================================================

    def _get_state_feedback_K(self) -> np.ndarray | None:
        """Get state-feedback gain vector from current parameters."""
        p = self.parameters
        ctype = p.get("controller_type")
        n = self._plant_order

        if ctype == "state_feedback":
            return np.array([float(p.get(f"sf_k{i+1}", 0)) for i in range(n)])

        elif ctype == "pole_placement":
            desired = []
            for i in range(n):
                re = float(p.get(f"pp_pole{i+1}_real", -(i + 2)))
                im = float(p.get(f"pp_pole{i+1}_imag", 0))
                desired.append(complex(re, im) if abs(im) > 1e-10 else complex(re, 0))
            desired = self._ensure_conjugate_pairs(desired[:n])
            if len(desired) != n:
                return None
            try:
                result = signal.place_poles(self._A, self._B, np.array(desired))
                K = result.gain_matrix
                return K[0] if K.ndim > 1 else K
            except Exception:
                return None

        elif ctype == "lqr":
            Q = np.diag([float(p.get(f"lqr_q{i+1}", 1.0)) for i in range(n)])
            R = np.atleast_2d(float(p.get("lqr_r", 1.0)))
            try:
                from scipy.linalg import solve_continuous_are
                P = solve_continuous_are(self._A, self._B, Q, R)
                K = np.linalg.solve(R, self._B.T @ P)
                return K.flatten()
            except Exception:
                return None

        return None

    @staticmethod
    def _ensure_conjugate_pairs(poles: list) -> list:
        """Ensure complex poles come in conjugate pairs."""
        result = []
        used: set[int] = set()
        for i, p in enumerate(poles):
            if i in used:
                continue
            result.append(p)
            used.add(i)
            if abs(p.imag) > 1e-10:
                conj = p.conjugate()
                found = False
                for j, q in enumerate(poles):
                    if j not in used and abs(q - conj) < 1e-10:
                        result.append(q)
                        used.add(j)
                        found = True
                        break
                if not found:
                    result.append(conj)
        return result

    # =========================================================================
    # Closed-loop computation
    # =========================================================================

    def _compute_closed_loop(self) -> None:
        """Compute open-loop and closed-loop transfer functions."""
        if getattr(self, '_state_feedback_mode', False):
            # CL already computed in _build_controller_tf for state-feedback
            # Use plant TF as OL for Bode/Nyquist (approximate)
            self._ol_num = self._plant_num.copy()
            self._ol_den = self._plant_den.copy()
            return
        self._ol_num = np.convolve(self._ctrl_num, self._plant_num)
        self._ol_den = np.convolve(self._ctrl_den, self._plant_den)

        max_len = max(len(self._ol_den), len(self._ol_num))
        ol_den_padded = np.pad(self._ol_den, (max_len - len(self._ol_den), 0))
        ol_num_padded = np.pad(self._ol_num, (max_len - len(self._ol_num), 0))
        self._cl_den = ol_den_padded + ol_num_padded
        self._cl_num = self._ol_num.copy()

    # =========================================================================
    # Time-domain computation
    # =========================================================================

    def _compute_step_response(self) -> tuple[np.ndarray, np.ndarray]:
        """Compute closed-loop unit step response."""
        duration = float(self.parameters.get("sim_duration", 10))
        T = np.linspace(0, duration, 1000)
        try:
            sys = signal.TransferFunction(self._cl_num, self._cl_den)
            t, y = signal.step(sys, T=T)
            # Cap diverging output for unstable systems
            final_val = y[-1] if np.isfinite(y[-1]) else 1.0
            cap = max(abs(final_val) * 10, 10.0)
            y = np.clip(y, -cap, cap)
        except Exception:
            t, y = T, np.zeros_like(T)
        return t, y

    def _compute_control_effort(self, t: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Compute control signal u(t) = C(s) * e(t)."""
        try:
            e_t = 1.0 - y
            ctrl_sys = signal.TransferFunction(self._ctrl_num, self._ctrl_den)
            _, u, _ = signal.lsim(ctrl_sys, U=e_t, T=t)
            cap = max(np.abs(u[np.isfinite(u)]).max() * 1.5, 10.0) if np.any(np.isfinite(u)) else 100.0
            u = np.clip(u, -cap, cap)
        except Exception:
            u = np.zeros_like(t)
        return t, u

    @staticmethod
    def _compute_error_signal(y: np.ndarray) -> np.ndarray:
        """Compute error signal e(t) = 1 - y(t)."""
        return 1.0 - y

    # =========================================================================
    # Frequency-domain computation
    # =========================================================================

    def _compute_bode(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Compute open-loop Bode plot data."""
        try:
            sys = signal.TransferFunction(self._ol_num, self._ol_den)
            w, mag, phase = signal.bode(sys, n=500)
            return w, mag, phase
        except Exception:
            w = np.logspace(-2, 3, 500)
            return w, np.zeros_like(w), np.zeros_like(w)

    def _compute_nyquist(self) -> tuple[np.ndarray, np.ndarray]:
        """Compute open-loop Nyquist data."""
        try:
            sys = signal.TransferFunction(self._ol_num, self._ol_den)
            w = np.logspace(-3, 3, 1000)
            _, H = signal.freqresp(sys, w)
            return H.real, H.imag
        except Exception:
            return np.zeros(100), np.zeros(100)

    def _compute_pole_zero_map(self) -> dict:
        """Compute closed-loop and open-loop poles/zeros."""
        try:
            cl_poles = np.roots(self._cl_den)
            cl_zeros = np.roots(self._cl_num)
        except Exception:
            cl_poles = np.array([])
            cl_zeros = np.array([])
        return {
            "cl_poles_real": cl_poles.real.tolist(),
            "cl_poles_imag": cl_poles.imag.tolist(),
            "cl_zeros_real": cl_zeros.real.tolist(),
            "cl_zeros_imag": cl_zeros.imag.tolist(),
        }

    # =========================================================================
    # Performance metrics
    # =========================================================================

    def _compute_performance_metrics(
        self, t: np.ndarray, y: np.ndarray, e: np.ndarray,
        w: np.ndarray, mag_db: np.ndarray, phase_deg: np.ndarray,
    ) -> dict:
        """Compute all performance metrics."""
        metrics: dict = {}
        final = y[-1] if len(y) > 0 and np.isfinite(y[-1]) else 1.0
        if abs(final) < 1e-10:
            final = 1.0

        # Rise time (10% to 90% of final value)
        try:
            y10, y90 = 0.1 * final, 0.9 * final
            idx10 = np.where(y >= y10)[0]
            idx90 = np.where(y >= y90)[0]
            t_rise = (t[idx90[0]] - t[idx10[0]]) if len(idx10) > 0 and len(idx90) > 0 else None
            metrics["rise_time"] = float(t_rise) if t_rise is not None and t_rise > 0 else None
        except (IndexError, ValueError):
            metrics["rise_time"] = None

        # Peak and overshoot
        try:
            peak_idx = np.argmax(y)
            y_peak = float(y[peak_idx])
            t_peak = float(t[peak_idx])
            overshoot = max(0, (y_peak - final) / abs(final) * 100)
            metrics["overshoot_pct"] = float(overshoot)
            metrics["peak_time"] = t_peak
            metrics["peak_value"] = y_peak
        except (ValueError, IndexError):
            metrics["overshoot_pct"] = 0.0
            metrics["peak_time"] = None
            metrics["peak_value"] = None

        # Settling time (2% band)
        try:
            band = 0.02 * abs(final)
            within_band = np.abs(y - final) <= band
            if np.all(within_band):
                metrics["settling_time"] = 0.0
            else:
                last_outside = np.where(~within_band)[0]
                metrics["settling_time"] = float(t[last_outside[-1]]) if len(last_outside) > 0 else None
        except (IndexError, ValueError):
            metrics["settling_time"] = None

        # Steady-state error
        metrics["steady_state_error"] = float(abs(1.0 - final))

        # Stability margins from Bode data
        gm_db, pm_deg, w_gc, w_pc = self._compute_stability_margins(w, mag_db, phase_deg)
        metrics["gain_margin_db"] = gm_db
        metrics["phase_margin_deg"] = pm_deg
        metrics["gain_crossover_freq"] = w_gc
        metrics["phase_crossover_freq"] = w_pc

        # Bandwidth (-3dB of CL)
        try:
            cl_sys = signal.TransferFunction(self._cl_num, self._cl_den)
            w_cl = np.logspace(-2, 4, 2000)
            _, H_cl = signal.freqresp(cl_sys, w_cl)
            mag_cl_db = 20 * np.log10(np.abs(H_cl) + 1e-15)
            dc_gain_db = mag_cl_db[0]
            below_3db = np.where(mag_cl_db < dc_gain_db - 3)[0]
            metrics["bandwidth"] = float(w_cl[below_3db[0]]) if len(below_3db) > 0 else None
        except Exception:
            metrics["bandwidth"] = None

        # Integral criteria
        dt = np.diff(t)
        dt_ext = np.append(dt, dt[-1]) if len(dt) > 0 else np.array([0.01])
        e_abs = np.abs(e)
        metrics["ise"] = float(_trapz(e**2, t)) if len(t) > 1 else 0.0
        metrics["iae"] = float(_trapz(e_abs, t)) if len(t) > 1 else 0.0
        metrics["itae"] = float(_trapz(t * e_abs, t)) if len(t) > 1 else 0.0

        # Stability classification
        try:
            cl_poles = np.roots(self._cl_den)
            max_real = np.max(cl_poles.real) if len(cl_poles) > 0 else 0
            if max_real < -1e-6:
                metrics["is_stable"] = True
                metrics["stability_class"] = "Stable"
            elif max_real < 1e-6:
                metrics["is_stable"] = False
                metrics["stability_class"] = "Marginally Stable"
            else:
                metrics["is_stable"] = False
                metrics["stability_class"] = "Unstable"
        except Exception:
            metrics["is_stable"] = False
            metrics["stability_class"] = "Unknown"

        return metrics

    @staticmethod
    def _compute_stability_margins(
        w: np.ndarray, mag_db: np.ndarray, phase_deg: np.ndarray,
    ) -> tuple[float | None, float | None, float | None, float | None]:
        """Compute gain and phase margins from Bode data."""
        gm_db = None
        pm_deg = None
        w_gc = None
        w_pc = None

        if len(w) < 2:
            return gm_db, pm_deg, w_gc, w_pc

        # Gain crossover: |L(jw)| = 0 dB
        for i in range(len(mag_db) - 1):
            if (mag_db[i] >= 0 and mag_db[i + 1] < 0) or (mag_db[i] <= 0 and mag_db[i + 1] > 0):
                frac = (0 - mag_db[i]) / (mag_db[i + 1] - mag_db[i] + 1e-15)
                frac = np.clip(frac, 0, 1)
                w_gc = float(w[i] + frac * (w[i + 1] - w[i]))
                phase_at_gc = float(phase_deg[i] + frac * (phase_deg[i + 1] - phase_deg[i]))
                pm_deg = float(180.0 + phase_at_gc)
                break

        # Phase crossover: phase = -180°
        for i in range(len(phase_deg) - 1):
            if (phase_deg[i] >= -180 and phase_deg[i + 1] < -180) or \
               (phase_deg[i] <= -180 and phase_deg[i + 1] > -180):
                frac = (-180 - phase_deg[i]) / (phase_deg[i + 1] - phase_deg[i] + 1e-15)
                frac = np.clip(frac, 0, 1)
                w_pc = float(w[i] + frac * (w[i + 1] - w[i]))
                mag_at_pc = float(mag_db[i] + frac * (mag_db[i + 1] - mag_db[i]))
                gm_db = float(-mag_at_pc)
                break

        return gm_db, pm_deg, w_gc, w_pc

    # =========================================================================
    # Transfer function display strings
    # =========================================================================

    def _compute_tf_strings(self) -> dict:
        """Generate LaTeX and plain-text transfer function strings."""
        plant_latex = self._poly_to_latex_frac(self._plant_num, self._plant_den)
        cl_latex = self._poly_to_latex_frac(self._cl_num, self._cl_den)

        result = {
            "plant_tf_latex": plant_latex,
            "closed_loop_tf_latex": cl_latex,
            "plant_tf_str": f"G(s) = {self._poly_to_str(self._plant_num)}/({self._poly_to_str(self._plant_den)})",
            "closed_loop_tf_str": f"T(s) = {self._poly_to_str(self._cl_num)}/({self._poly_to_str(self._cl_den)})",
        }

        if getattr(self, '_state_feedback_mode', False):
            K = getattr(self, '_state_feedback_K', None)
            if K is not None:
                k_str = ', '.join(f'{k:.4g}' for k in K)
                result["controller_tf_latex"] = f"\\mathbf{{K}} = [{k_str}]"
                result["controller_tf_str"] = f"u = -Kx + r, K = [{k_str}]"
            else:
                result["controller_tf_latex"] = "\\mathbf{K} = \\text{(not computed)}"
                result["controller_tf_str"] = "K = (not computed)"
        else:
            ctrl_latex = self._poly_to_latex_frac(self._ctrl_num, self._ctrl_den)
            result["controller_tf_latex"] = ctrl_latex
            result["controller_tf_str"] = f"C(s) = {self._poly_to_str(self._ctrl_num)}/({self._poly_to_str(self._ctrl_den)})"

        return result

    @staticmethod
    def _poly_to_str(coeffs: np.ndarray) -> str:
        """Convert polynomial coefficients to human-readable string."""
        n = len(coeffs) - 1
        terms = []
        for i, c in enumerate(coeffs):
            power = n - i
            if abs(c) < 1e-10:
                continue
            c_str = f"{c:.4g}"
            if power == 0:
                terms.append(c_str)
            elif power == 1:
                terms.append(f"{c_str}s" if abs(c) != 1 else "s")
            else:
                terms.append(f"{c_str}s^{power}" if abs(c) != 1 else f"s^{power}")
        return " + ".join(terms) if terms else "0"

    @staticmethod
    def _poly_to_latex_frac(num: np.ndarray, den: np.ndarray) -> str:
        """Convert num/den polynomial pair to LaTeX fraction."""
        def _poly_latex(coeffs: np.ndarray) -> str:
            n = len(coeffs) - 1
            terms = []
            for i, c in enumerate(coeffs):
                power = n - i
                if abs(c) < 1e-10:
                    continue
                c_abs = abs(c)
                sign = "-" if c < 0 else ("+" if terms else "")
                if power == 0:
                    terms.append(f"{sign}{c_abs:.4g}")
                elif power == 1:
                    if abs(c_abs - 1.0) < 1e-10:
                        terms.append(f"{sign}s")
                    else:
                        terms.append(f"{sign}{c_abs:.4g}s")
                else:
                    if abs(c_abs - 1.0) < 1e-10:
                        terms.append(f"{sign}s^{{{power}}}")
                    else:
                        terms.append(f"{sign}{c_abs:.4g}s^{{{power}}}")
            return " ".join(terms) if terms else "0"

        num_str = _poly_latex(num)
        den_str = _poly_latex(den)
        # If denominator is just "1", skip fraction
        if den_str.strip() == "1":
            return num_str
        return f"\\frac{{{num_str}}}{{{den_str}}}"

    # =========================================================================
    # Auto-tuning
    # =========================================================================

    def _auto_tune(self) -> dict | None:
        """Run selected auto-tuning method, return gain dict or None."""
        method = self.parameters.get("tuning_method", "manual")
        ctype = self.parameters.get("controller_type", "PID")

        dispatch = {
            "zn_open": self._zn_open_loop,
            "zn_closed": self._zn_closed_loop,
            "cohen_coon": self._cohen_coon,
            "lambda_tuning": self._lambda_tuning,
            "imc": self._imc_tuning,
            "itae_optimal": self._itae_optimal,
        }
        func = dispatch.get(method)
        if func is None:
            return None
        try:
            result = func(ctype)
            if result:
                self._tuning_info = f"{method.replace('_', ' ').title()} → Kp={result.get('Kp', 0):.4g}, Ki={result.get('Ki', 0):.4g}, Kd={result.get('Kd', 0):.4g}"
            return result
        except Exception as ex:
            self._tuning_info = f"Auto-tune failed: {str(ex)[:100]}"
            return None

    def _fit_fopdt_model(self) -> tuple[float, float, float]:
        """Fit FOPDT model (K_p, tau_p, L) to plant step response."""
        try:
            plant_sys = signal.TransferFunction(self._plant_num, self._plant_den)
            T = np.linspace(0, 50, 2000)
            t, y = signal.step(plant_sys, T=T)
        except Exception:
            return 1.0, 1.0, 0.1

        # Check if system settles (not a pure integrator)
        if not np.isfinite(y[-1]) or abs(y[-1]) > 1e6:
            # Integrator-like: fit ramp
            mid = len(y) // 2
            if mid > 10:
                slope = np.mean(np.gradient(y[mid:], t[mid:]))
                return max(abs(slope), 0.001), 1.0, 0.01
            return 1.0, 1.0, 0.1

        K_p = float(y[-1])
        if abs(K_p) < 1e-10:
            K_p = 1.0

        dy = np.gradient(y, t)
        i_max = int(np.argmax(np.abs(dy)))
        max_slope = float(dy[i_max])
        if abs(max_slope) < 1e-10:
            return K_p, 1.0, 0.01

        # Dead time: x-intercept of tangent at max slope
        L = float(t[i_max] - y[i_max] / max_slope)
        L = max(L, 0.001)

        # Time constant: K_p / max_slope
        tau_p = float(abs(K_p / max_slope))
        tau_p = max(tau_p, 0.001)

        return K_p, tau_p, L

    def _zn_open_loop(self, ctype: str) -> dict:
        """Ziegler-Nichols open-loop (process reaction curve) tuning."""
        K_p, tau_p, L = self._fit_fopdt_model()
        ratio = tau_p / (K_p * L)

        if ctype in ("P",):
            Kp = ratio
            return {"Kp": Kp, "Ki": 0.0, "Kd": 0.0}
        elif ctype in ("PI",):
            Kp = 0.9 * ratio
            Ti = L / 0.3
            return {"Kp": Kp, "Ki": Kp / Ti, "Kd": 0.0}
        else:  # PID or PD
            Kp = 1.2 * ratio
            Ti = 2.0 * L
            Td = 0.5 * L
            Ki = Kp / Ti if ctype in ("PID", "PI") else 0.0
            Kd = Kp * Td if ctype in ("PID", "PD") else 0.0
            return {"Kp": Kp, "Ki": Ki, "Kd": Kd}

    def _zn_closed_loop(self, ctype: str) -> dict:
        """Ziegler-Nichols closed-loop (ultimate gain) tuning."""
        # Find ultimate gain Ku via binary search
        Ku = None
        Pu = None
        plant_num = self._plant_num
        plant_den = self._plant_den

        # Sweep gain to find where CL poles cross imaginary axis
        gains = np.logspace(-2, 3, 500)
        prev_max_real = None
        for K_test in gains:
            cl_char = np.polyadd(plant_den, K_test * np.pad(plant_num, (len(plant_den) - len(plant_num), 0)))
            poles = np.roots(cl_char)
            if len(poles) == 0:
                continue
            max_real = np.max(poles.real)
            if prev_max_real is not None and prev_max_real < 0 and max_real >= 0:
                # Refine with binary search
                K_lo, K_hi = float(gains[max(0, np.searchsorted(gains, K_test) - 1)]), float(K_test)
                for _ in range(50):
                    K_mid = (K_lo + K_hi) / 2
                    cl_char_mid = np.polyadd(plant_den, K_mid * np.pad(plant_num, (len(plant_den) - len(plant_num), 0)))
                    poles_mid = np.roots(cl_char_mid)
                    if len(poles_mid) == 0:
                        break
                    if np.max(poles_mid.real) >= 0:
                        K_hi = K_mid
                    else:
                        K_lo = K_mid
                Ku = (K_lo + K_hi) / 2
                # Find frequency of imaginary poles
                cl_char_u = np.polyadd(plant_den, Ku * np.pad(plant_num, (len(plant_den) - len(plant_num), 0)))
                poles_u = np.roots(cl_char_u)
                imag_parts = np.abs(poles_u.imag[np.abs(poles_u.real) < 0.1 * max(abs(Ku), 1)])
                if len(imag_parts) > 0:
                    omega_u = float(np.max(imag_parts))
                    Pu = 2 * np.pi / omega_u if omega_u > 0 else 1.0
                break
            prev_max_real = max_real

        if Ku is None or Pu is None:
            # Fallback to open-loop method
            return self._zn_open_loop(ctype)

        if ctype == "P":
            return {"Kp": 0.5 * Ku, "Ki": 0.0, "Kd": 0.0}
        elif ctype == "PI":
            Kp = 0.45 * Ku
            Ti = Pu / 1.2
            return {"Kp": Kp, "Ki": Kp / Ti, "Kd": 0.0}
        else:  # PID or PD
            Kp = 0.6 * Ku
            Ti = 0.5 * Pu
            Td = 0.125 * Pu
            Ki = Kp / Ti if ctype in ("PID", "PI") else 0.0
            Kd = Kp * Td if ctype in ("PID", "PD") else 0.0
            return {"Kp": Kp, "Ki": Ki, "Kd": Kd}

    def _cohen_coon(self, ctype: str) -> dict:
        """Cohen-Coon tuning rules."""
        K_p, tau_p, L = self._fit_fopdt_model()
        r = L / tau_p
        base = tau_p / (K_p * L)

        if ctype == "P":
            Kp = base * (1 + r / 3)
            return {"Kp": Kp, "Ki": 0.0, "Kd": 0.0}
        elif ctype == "PI":
            Kp = base * (0.9 + r / 12)
            Ti = L * (30 + 3 * r) / (9 + 20 * r)
            return {"Kp": Kp, "Ki": Kp / Ti, "Kd": 0.0}
        else:  # PID or PD
            Kp = base * (4 / 3 + r / 4)
            Ti = L * (32 + 6 * r) / (13 + 8 * r)
            Td = L * 4 / (11 + 2 * r)
            Ki = Kp / Ti if ctype in ("PID", "PI") else 0.0
            Kd = Kp * Td if ctype in ("PID", "PD") else 0.0
            return {"Kp": Kp, "Ki": Ki, "Kd": Kd}

    def _lambda_tuning(self, ctype: str) -> dict:
        """Lambda tuning (user-specified CL time constant)."""
        K_p, tau_p, L = self._fit_fopdt_model()
        lambda_cl = float(self.parameters.get("lambda_cl_tau", 1.0))
        Kp = tau_p / (K_p * (lambda_cl + L))
        Ti = tau_p
        Ki = Kp / Ti if ctype in ("PI", "PID") else 0.0
        return {"Kp": Kp, "Ki": Ki, "Kd": 0.0}

    def _imc_tuning(self, ctype: str) -> dict:
        """IMC (Internal Model Control) tuning."""
        K_p, tau_p, L = self._fit_fopdt_model()
        tau_c = max(0.25 * tau_p, 1.5 * L)
        Kp = (tau_p + 0.5 * L) / (K_p * (tau_c + 0.5 * L))
        Ti = tau_p + 0.5 * L
        Td = tau_p * L / (2 * tau_p + L) if (2 * tau_p + L) > 0 else 0
        Ki = Kp / Ti if ctype in ("PI", "PID") else 0.0
        Kd = Kp * Td if ctype in ("PID", "PD") else 0.0
        return {"Kp": Kp, "Ki": Ki, "Kd": Kd}

    def _itae_optimal(self, ctype: str) -> dict:
        """ITAE-optimal tuning via numerical optimization."""
        plant_num = self._plant_num.copy()
        plant_den = self._plant_den.copy()
        duration = float(self.parameters.get("sim_duration", 10))
        N = float(self.parameters.get("deriv_filter_N", 20))
        T = np.linspace(0, duration, 500)

        def cost(gains: np.ndarray) -> float:
            kp, ki, kd = float(gains[0]), float(gains[1]), float(gains[2])
            kp = max(kp, 0.001)
            ki = max(ki, 0)
            kd = max(kd, 0)
            # Build PID TF
            c_num = np.array([kp + kd * N, kp * N + ki, ki * N])
            c_den = np.array([1.0, N, 0.0])
            ol_n = np.convolve(c_num, plant_num)
            ol_d = np.convolve(c_den, plant_den)
            ml = max(len(ol_d), len(ol_n))
            cl_d = np.pad(ol_d, (ml - len(ol_d), 0)) + np.pad(ol_n, (ml - len(ol_n), 0))
            # Check stability
            poles = np.roots(cl_d)
            if len(poles) > 0 and np.max(poles.real) > 0:
                return 1e6
            try:
                sys_cl = signal.TransferFunction(ol_n, cl_d)
                t_sim, y_sim = signal.step(sys_cl, T=T)
                e_sim = 1.0 - y_sim
                return float(_trapz(t_sim * np.abs(e_sim), t_sim))
            except Exception:
                return 1e6

        x0 = np.array([
            float(self.parameters.get("Kp", 1.0)),
            float(self.parameters.get("Ki", 0.0)),
            float(self.parameters.get("Kd", 0.0)),
        ])
        # Ensure starting point is reasonable
        if x0[0] < 0.001:
            x0[0] = 1.0

        result = optimize.minimize(
            cost, x0, method="Nelder-Mead",
            options={"maxiter": 80, "xatol": 0.01, "fatol": 0.001},
        )
        kp, ki, kd = float(result.x[0]), float(result.x[1]), float(result.x[2])
        kp = max(kp, 0.001)
        ki = max(ki, 0)
        kd = max(kd, 0)

        if ctype == "P":
            return {"Kp": kp, "Ki": 0.0, "Kd": 0.0}
        elif ctype == "PI":
            return {"Kp": kp, "Ki": ki, "Kd": 0.0}
        elif ctype == "PD":
            return {"Kp": kp, "Ki": 0.0, "Kd": kd}
        return {"Kp": kp, "Ki": ki, "Kd": kd}

    # =========================================================================
    # Reference system
    # =========================================================================

    def _save_reference(self) -> None:
        """Save current step response as a reference snapshot."""
        t, y = self._compute_step_response()
        label = self._make_reference_label()
        snapshot = {
            "t": t.tolist(),
            "y": y.tolist(),
            "label": label,
            "params": {k: v for k, v in self.parameters.items()
                       if k in ("Kp", "Ki", "Kd", "controller_type", "tuning_method",
                                "lead_lag_Kc", "lead_lag_zero", "lead_lag_pole")},
        }
        if len(self._reference_responses) >= 5:
            self._reference_responses.pop(0)
        self._reference_responses.append(snapshot)

    def _make_reference_label(self) -> str:
        """Generate a label for the current controller configuration."""
        ctype = self.parameters.get("controller_type", "PID")
        if ctype == "lead_lag":
            Kc = self.parameters.get("lead_lag_Kc", 1)
            z = self.parameters.get("lead_lag_zero", 2)
            p = self.parameters.get("lead_lag_pole", 10)
            return f"Lead-Lag: Kc={Kc:.2g}, z={z:.2g}, p={p:.2g}"
        Kp = self.parameters.get("Kp", 1)
        Ki = self.parameters.get("Ki", 0)
        Kd = self.parameters.get("Kd", 0)
        method = self.parameters.get("tuning_method", "manual")
        prefix = method.replace("_", " ").title() if method != "manual" else "Manual"
        return f"{ctype} ({prefix}): Kp={Kp:.3g}, Ki={Ki:.3g}, Kd={Kd:.3g}"

    # =========================================================================
    # Plot builders
    # =========================================================================

    def _build_step_response_plot(self, t: np.ndarray, y: np.ndarray, metrics: dict) -> dict:
        """Build step response plot with annotations."""
        duration = float(self.parameters.get("sim_duration", 10))
        final = float(y[-1]) if len(y) > 0 and np.isfinite(y[-1]) else 1.0
        if abs(final) < 1e-10:
            final = 1.0

        data = [
            {
                "x": t.tolist(), "y": y.tolist(), "type": "scatter", "mode": "lines",
                "name": "Current", "line": {"color": "#3b82f6", "width": 2.5},
            },
        ]
        # Reference traces
        ref_colors = ["#6b7280", "#9ca3af", "#a78bfa", "#fb923c", "#f472b6"]
        for i, ref in enumerate(self._reference_responses):
            data.append({
                "x": ref["t"], "y": ref["y"], "type": "scatter", "mode": "lines",
                "name": ref.get("label", f"Ref {i + 1}"),
                "line": {"color": ref_colors[i % len(ref_colors)], "width": 1.5, "dash": "dash"},
            })
        # Setpoint line
        data.append({
            "x": [0, duration], "y": [1, 1], "type": "scatter", "mode": "lines",
            "name": "Setpoint", "line": {"color": "#10b981", "width": 1, "dash": "dot"},
        })
        # Settling band
        data.extend([
            {
                "x": [0, duration], "y": [final * 1.02, final * 1.02],
                "type": "scatter", "mode": "lines",
                "name": "\u00b12% Band", "line": {"color": "#94a3b8", "width": 0.5, "dash": "dot"},
                "showlegend": False,
            },
            {
                "x": [0, duration], "y": [final * 0.98, final * 0.98],
                "type": "scatter", "mode": "lines", "showlegend": False,
                "line": {"color": "#94a3b8", "width": 0.5, "dash": "dot"},
            },
        ])
        # Overshoot marker
        overshoot = metrics.get("overshoot_pct", 0)
        t_peak = metrics.get("peak_time")
        y_peak = metrics.get("peak_value")
        if t_peak is not None and y_peak is not None and overshoot > 0.1:
            data.append({
                "x": [t_peak], "y": [y_peak], "type": "scatter", "mode": "markers",
                "name": f"Overshoot {overshoot:.1f}%",
                "marker": {"color": "#ef4444", "size": 10, "symbol": "diamond"},
            })

        annotations = []
        rise_time = metrics.get("rise_time")
        if rise_time is not None:
            annotations.append({
                "x": rise_time, "y": 0.9 * final,
                "text": f"t\u1d63 = {rise_time:.3f}s",
                "showarrow": True, "arrowhead": 2, "ax": 40, "ay": -30,
                "font": {"size": 11, "color": "#f59e0b"},
            })
        settling = metrics.get("settling_time")
        if settling is not None and settling > 0:
            annotations.append({
                "x": settling, "y": final,
                "text": f"t\u209b = {settling:.3f}s",
                "showarrow": True, "arrowhead": 2, "ax": 40, "ay": 30,
                "font": {"size": 11, "color": "#10b981"},
            })

        return {
            "id": "step_response",
            "title": "Closed-Loop Step Response",
            "data": data,
            "layout": {
                "xaxis": {"title": "Time (s)"},
                "yaxis": {"title": "Amplitude"},
                "annotations": annotations,
            },
        }

    def _build_bode_magnitude_plot(self, w: np.ndarray, mag_db: np.ndarray, metrics: dict) -> dict:
        """Build Bode magnitude plot."""
        data = [
            {
                "x": w.tolist(), "y": mag_db.tolist(), "type": "scatter", "mode": "lines",
                "name": "|L(j\u03c9)|", "line": {"color": "#3b82f6", "width": 2},
            },
            {
                "x": [float(w[0]), float(w[-1])], "y": [0, 0],
                "type": "scatter", "mode": "lines",
                "name": "0 dB", "line": {"color": "#94a3b8", "width": 1, "dash": "dot"},
            },
        ]
        w_pc = metrics.get("phase_crossover_freq")
        gm = metrics.get("gain_margin_db")
        if w_pc is not None and gm is not None:
            data.append({
                "x": [w_pc, w_pc], "y": [0, -gm],
                "type": "scatter", "mode": "lines+markers",
                "name": f"GM = {gm:.1f} dB", "line": {"color": "#10b981", "width": 2},
            })
        return {
            "id": "bode_magnitude",
            "title": "Open-Loop Bode: Magnitude",
            "data": data,
            "layout": {
                "xaxis": {"title": "Frequency (rad/s)", "type": "log"},
                "yaxis": {"title": "Magnitude (dB)"},
            },
        }

    def _build_bode_phase_plot(self, w: np.ndarray, phase_deg: np.ndarray, metrics: dict) -> dict:
        """Build Bode phase plot."""
        data = [
            {
                "x": w.tolist(), "y": phase_deg.tolist(), "type": "scatter", "mode": "lines",
                "name": "\u2220L(j\u03c9)", "line": {"color": "#ef4444", "width": 2},
            },
            {
                "x": [float(w[0]), float(w[-1])], "y": [-180, -180],
                "type": "scatter", "mode": "lines",
                "name": "-180\u00b0", "line": {"color": "#94a3b8", "width": 1, "dash": "dot"},
            },
        ]
        w_gc = metrics.get("gain_crossover_freq")
        pm = metrics.get("phase_margin_deg")
        if w_gc is not None and pm is not None:
            phase_at_gc = pm - 180.0
            data.append({
                "x": [w_gc, w_gc], "y": [-180, phase_at_gc],
                "type": "scatter", "mode": "lines+markers",
                "name": f"PM = {pm:.1f}\u00b0", "line": {"color": "#f59e0b", "width": 2},
            })
        return {
            "id": "bode_phase",
            "title": "Open-Loop Bode: Phase",
            "data": data,
            "layout": {
                "xaxis": {"title": "Frequency (rad/s)", "type": "log"},
                "yaxis": {"title": "Phase (deg)"},
            },
        }

    def _build_pole_zero_plot(self, pz_data: dict) -> dict:
        """Build pole-zero map plot."""
        cl_pr = pz_data["cl_poles_real"]
        cl_pi = pz_data["cl_poles_imag"]
        cl_zr = pz_data["cl_zeros_real"]
        cl_zi = pz_data["cl_zeros_imag"]

        # Compute axis range
        all_pts = cl_pr + cl_pi + cl_zr + cl_zi + [0]
        max_range = max(abs(v) for v in all_pts if np.isfinite(v)) if all_pts else 5
        max_range = max(max_range * 1.3, 2)

        data = [
            {
                "x": [-max_range, 0, 0, -max_range],
                "y": [-max_range, -max_range, max_range, max_range],
                "fill": "toself", "fillcolor": "rgba(16, 185, 129, 0.05)",
                "line": {"width": 0}, "name": "Stable Region", "showlegend": False,
            },
            {
                "x": [0, 0], "y": [-max_range, max_range],
                "type": "scatter", "mode": "lines",
                "name": "j\u03c9 axis", "line": {"color": "#94a3b8", "width": 1, "dash": "dot"},
            },
            {
                "x": cl_pr, "y": cl_pi, "type": "scatter", "mode": "markers",
                "name": "CL Poles",
                "marker": {"color": "#ef4444", "size": 12, "symbol": "x"},
            },
        ]
        if cl_zr:
            data.append({
                "x": cl_zr, "y": cl_zi, "type": "scatter", "mode": "markers",
                "name": "CL Zeros",
                "marker": {"color": "#3b82f6", "size": 10, "symbol": "circle-open",
                           "line": {"width": 2, "color": "#3b82f6"}},
            })
        return {
            "id": "pole_zero_map",
            "title": "Closed-Loop Pole-Zero Map",
            "data": data,
            "layout": {
                "xaxis": {"title": "Real", "range": [-max_range, max_range]},
                "yaxis": {"title": "Imaginary", "scaleanchor": "x",
                          "range": [-max_range, max_range]},
            },
        }

    @staticmethod
    def _build_control_effort_plot(t: np.ndarray, u: np.ndarray) -> dict:
        """Build control effort plot."""
        return {
            "id": "control_effort",
            "title": "Control Effort u(t)",
            "data": [{
                "x": t.tolist(), "y": u.tolist(), "type": "scatter", "mode": "lines",
                "name": "u(t)", "line": {"color": "#8b5cf6", "width": 2},
            }],
            "layout": {
                "xaxis": {"title": "Time (s)"},
                "yaxis": {"title": "Control Signal"},
            },
        }

    def _build_error_signal_plot(self, t: np.ndarray, e: np.ndarray) -> dict:
        """Build error signal plot."""
        duration = float(self.parameters.get("sim_duration", 10))
        return {
            "id": "error_signal",
            "title": "Error Signal e(t)",
            "data": [
                {
                    "x": t.tolist(), "y": e.tolist(), "type": "scatter", "mode": "lines",
                    "name": "e(t)", "line": {"color": "#f59e0b", "width": 2},
                },
                {
                    "x": [0, duration], "y": [0, 0], "type": "scatter", "mode": "lines",
                    "line": {"color": "#94a3b8", "width": 0.5, "dash": "dot"},
                    "showlegend": False,
                },
            ],
            "layout": {
                "xaxis": {"title": "Time (s)"},
                "yaxis": {"title": "Error"},
            },
        }

    @staticmethod
    def _build_nyquist_plot(real: np.ndarray, imag: np.ndarray) -> dict:
        """Build Nyquist plot."""
        return {
            "id": "nyquist",
            "title": "Nyquist Plot",
            "data": [
                {
                    "x": real.tolist(), "y": imag.tolist(), "type": "scatter", "mode": "lines",
                    "name": "L(j\u03c9)", "line": {"color": "#3b82f6", "width": 2},
                },
                {
                    "x": real.tolist(), "y": (-imag).tolist(),
                    "type": "scatter", "mode": "lines",
                    "name": "L(-j\u03c9)",
                    "line": {"color": "#3b82f6", "width": 1, "dash": "dash"},
                    "showlegend": False,
                },
                {
                    "x": [-1], "y": [0], "type": "scatter", "mode": "markers",
                    "name": "(-1, 0)",
                    "marker": {"color": "#ef4444", "size": 10, "symbol": "x"},
                },
            ],
            "layout": {
                "xaxis": {"title": "Real", "scaleanchor": "y"},
                "yaxis": {"title": "Imaginary"},
            },
        }

    # =========================================================================
    # Main interface
    # =========================================================================

    def get_plots(self) -> list[dict]:
        """Return all plots (called by get_state)."""
        self._build_plant_tf()
        self._build_controller_tf()
        self._compute_closed_loop()

        t, y = self._compute_step_response()
        t_u, u = self._compute_control_effort(t, y)
        e = self._compute_error_signal(y)
        w, mag_db, phase_deg = self._compute_bode()
        nyq_real, nyq_imag = self._compute_nyquist()
        pz_data = self._compute_pole_zero_map()
        metrics = self._compute_performance_metrics(t, y, e, w, mag_db, phase_deg)
        tf_strings = self._compute_tf_strings()

        # Store metadata for get_state
        self._last_metrics = metrics
        self._last_tf_strings = tf_strings

        return [
            self._build_step_response_plot(t, y, metrics),
            self._build_bode_magnitude_plot(w, mag_db, metrics),
            self._build_bode_phase_plot(w, phase_deg, metrics),
            self._build_pole_zero_plot(pz_data),
            self._build_control_effort_plot(t_u, u),
            self._build_error_signal_plot(t, e),
            self._build_nyquist_plot(nyq_real, nyq_imag),
        ]

    def get_state(self) -> dict:
        """Return full simulation state."""
        plots = self.get_plots()
        return {
            "parameters": self.parameters.copy(),
            "plots": plots,
            "metadata": {
                "simulation_type": "controller_tuning_lab",
                "has_custom_viewer": True,
                "performance": getattr(self, "_last_metrics", {}),
                "tf_strings": getattr(self, "_last_tf_strings", {}),
                "reference_responses": self._reference_responses,
                "tuning_info": self._tuning_info,
                "block_diagram": {
                    "plant_label": getattr(self, "_last_tf_strings", {}).get("plant_tf_latex", "G(s)"),
                    "controller_label": getattr(self, "_last_tf_strings", {}).get("controller_tf_latex", "C(s)"),
                    "feedback_gain": "1",
                },
                "is_controllable": getattr(self, '_is_controllable', True),
                "plant_order": getattr(self, '_plant_order', 1),
                "state_feedback_K": (
                    self._state_feedback_K.tolist()
                    if getattr(self, '_state_feedback_K', None) is not None else None
                ),
                "state_feedback_K_str": (
                    f"K = [{', '.join(f'{k:.4g}' for k in self._state_feedback_K)}]"
                    if getattr(self, '_state_feedback_K', None) is not None else None
                ),
                "ss_matrices": (
                    {
                        "A": self._A.tolist(),
                        "B": self._B.tolist(),
                        "C": self._C.tolist(),
                        "D": self._D.tolist(),
                    }
                    if self.parameters.get("controller_type") in ("state_feedback", "pole_placement", "lqr")
                    else None
                ),
            },
        }

    def handle_action(self, action: str, params: dict | None = None) -> dict:
        """Handle button press actions."""
        if action == "apply_tuning":
            gains = self._auto_tune()
            if gains:
                for key, value in gains.items():
                    self.parameters[key] = value
        elif action == "save_reference":
            self._build_plant_tf()
            self._build_controller_tf()
            self._compute_closed_loop()
            self._save_reference()
        elif action == "clear_references":
            self._reference_responses = []
        elif action == "apply_pole_placement":
            self._build_plant_tf()
            K_vec = self._get_state_feedback_K()
            if K_vec is not None:
                for i, k_val in enumerate(K_vec):
                    self.parameters[f"sf_k{i+1}"] = float(k_val)
                self._tuning_info = f"Pole Placement \u2192 K = [{', '.join(f'{k:.4g}' for k in K_vec)}]"
        elif action == "apply_lqr":
            self._build_plant_tf()
            K_vec = self._get_state_feedback_K()
            if K_vec is not None:
                for i, k_val in enumerate(K_vec):
                    self.parameters[f"sf_k{i+1}"] = float(k_val)
                self._tuning_info = f"LQR \u2192 K = [{', '.join(f'{k:.4g}' for k in K_vec)}]"
        return self.get_state()
