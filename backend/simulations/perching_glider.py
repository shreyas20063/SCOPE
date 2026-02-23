"""
2D Perching Glider Simulator

Simulates a fixed-wing glider performing a perching maneuver using flat-plate
aerodynamics and Euler integration.  Three control modes demonstrate why
feedback is essential for agile flight: open-loop (manual elevator), proportional
controller (user tunes gain K), and optimal (pre-tuned PD + feedforward).

Based on MIT 6.003 Lecture 10 — Feedback and Control, and
Cory & Tedrake (2008) "Experiments in Fixed-Wing UAV Perching."
"""

from typing import Any, Dict, List, Optional
import numpy as np

from .base_simulator import BaseSimulator


class PerchingGliderSimulator(BaseSimulator):
    """2D perching glider with flat-plate aerodynamics and feedback control."""

    # ── Physical constants (MIT glider, Cory & Tedrake 2008) ──────────
    MASS = 0.08            # kg
    WING_AREA = 0.0885     # m² — wing planform area
    ELEV_AREA = 0.0147     # m² — elevator planform area
    WING_DIST = 0.025      # m — wing aerodynamic centre to CG
    ELEV_DIST = 0.19       # m — elevator AC to CG (behind)
    INERTIA = 0.00024      # kg·m² — pitch moment of inertia
    RHO = 1.225            # kg/m³ — air density at sea level
    G = 9.81               # m/s² — gravity
    CHORD = 0.15           # m — representative chord for streamline model
    PITCH_DAMP = 0.0008    # N·m·s/rad — aerodynamic pitch damping

    # ── Integration ───────────────────────────────────────────────────
    DT_PHYSICS = 0.001     # 1 kHz Euler integration
    MAX_TIME = 2.5         # seconds
    OUTPUT_SKIP = 10       # subsample → 100 Hz output

    # ── Actuator limits ───────────────────────────────────────────────
    PHI_DOT_MAX = 8.0      # rad/s — max elevator deflection rate
    PHI_MAX = np.pi / 2    # rad — max elevator deflection

    # ── Optimal controller gains (pre-tuned) ──────────────────────────
    OPT_KP = 30.0
    OPT_KD = 4.0
    OPT_THETA_TARGET = 1.40  # rad ≈ 80°
    OPT_TRIGGER = 2.2       # m — optimal trigger distance

    PARAMETER_SCHEMA: Dict[str, Dict] = {
        "control_mode": {
            "type": "select",
            "options": [
                {"value": "open_loop", "label": "Open-Loop (Manual)"},
                {"value": "p_controller", "label": "P-Controller (Tune K)"},
                {"value": "optimal", "label": "Optimal (Pre-tuned)"},
            ],
            "default": "open_loop",
        },
        "elevator_rate": {
            "type": "slider", "min": -5.0, "max": 5.0,
            "step": 0.1, "default": 0.0, "unit": "rad/s",
        },
        "Kp": {
            "type": "slider", "min": 0.0, "max": 30.0,
            "step": 0.5, "default": 5.0,
        },
        "initial_speed": {
            "type": "slider", "min": 3.0, "max": 8.0,
            "step": 0.1, "default": 6.0, "unit": "m/s",
        },
        "initial_altitude": {
            "type": "slider", "min": 0.5, "max": 3.0,
            "step": 0.1, "default": 2.0, "unit": "m",
        },
        "show_forces": {
            "type": "checkbox", "default": False,
        },
        "show_velocity": {
            "type": "checkbox", "default": True,
        },
        "show_aoa": {
            "type": "checkbox", "default": False,
        },
        "animation_speed": {
            "type": "slider", "min": 0.1, "max": 4.0,
            "step": 0.1, "default": 1.0, "unit": "×",
        },
    }

    DEFAULT_PARAMS: Dict[str, Any] = {
        "control_mode": "open_loop",
        "elevator_rate": 0.0,
        "Kp": 5.0,
        "initial_speed": 6.0,
        "initial_altitude": 2.0,
        "show_forces": False,
        "show_velocity": True,
        "show_aoa": False,
        "animation_speed": 1.0,
    }

    def __init__(self, simulation_id: str) -> None:
        super().__init__(simulation_id)
        self._trajectory: Optional[Dict[str, np.ndarray]] = None
        self._outcome: Dict[str, Any] = {}
        self._actual_gains: Dict[str, float] = {}

    # ── BaseSimulator interface ───────────────────────────────────────

    def initialize(self, params: Optional[Dict[str, Any]] = None) -> None:
        self.parameters = self.DEFAULT_PARAMS.copy()
        if params:
            for name, value in params.items():
                if name in self.PARAMETER_SCHEMA:
                    self.parameters[name] = self._validate_param(name, value)
        self._initialized = True
        self._compute()

    def update_parameter(self, name: str, value: Any) -> Dict[str, Any]:
        if name in self.parameters:
            self.parameters[name] = self._validate_param(name, value)
            self._compute()
        return self.get_state()

    def reset(self) -> Dict[str, Any]:
        self.parameters = self.DEFAULT_PARAMS.copy()
        self._initialized = True
        self._compute()
        return self.get_state()

    def get_plots(self) -> List[Dict[str, Any]]:
        if self._trajectory is None:
            self._compute()
        plots = [
            self._plot_trajectory(),
            self._plot_state_history(),
            self._plot_aero(),
        ]
        if self.parameters["control_mode"] == "p_controller":
            plots.append(self._plot_poles())
        return plots

    def get_state(self) -> Dict[str, Any]:
        if self._trajectory is None:
            self._compute()

        traj = self._trajectory
        skip = self.OUTPUT_SKIP
        idx = slice(0, None, skip)

        return {
            "parameters": self.parameters.copy(),
            "plots": self.get_plots(),
            "metadata": {
                "simulation_type": "perching_glider",
                "visualization_2d": {
                    "time": traj["time"][idx].tolist(),
                    "x": traj["x"][idx].tolist(),
                    "z": traj["z"][idx].tolist(),
                    "theta": traj["theta"][idx].tolist(),
                    "phi": traj["phi"][idx].tolist(),
                    "xdot": traj["xdot"][idx].tolist(),
                    "zdot": traj["zdot"][idx].tolist(),
                    "speed": traj["speed"][idx].tolist(),
                    "alpha_w": traj["alpha_w"][idx].tolist(),
                    "lift_x": traj["lift_x"][idx].tolist(),
                    "lift_z": traj["lift_z"][idx].tolist(),
                    "drag_x": traj["drag_x"][idx].tolist(),
                    "drag_z": traj["drag_z"][idx].tolist(),
                    "dt": float(self.DT_PHYSICS * skip),
                    "total_time": float(traj["time"][-1]),
                    "num_frames": len(traj["time"][idx]),
                },
                "outcome": self._outcome,
                "control_info": self._control_info(),
            },
        }

    # ── Core physics ──────────────────────────────────────────────────

    @staticmethod
    def _aero_coeffs(alpha: float):
        """Flat-plate CL and CD (lecture slide 9)."""
        cl = 2.0 * np.sin(alpha) * np.cos(alpha)   # = sin(2α)
        cd = 2.0 * np.sin(alpha) ** 2               # = 1 - cos(2α)
        return cl, cd

    def _compute(self) -> None:
        """Euler-integrate the 2-D glider dynamics."""
        mode = self.parameters["control_mode"]
        v0 = float(self.parameters["initial_speed"])
        z0 = float(self.parameters["initial_altitude"])

        n_max = int(self.MAX_TIME / self.DT_PHYSICS)
        dt = self.DT_PHYSICS

        # State arrays (pre-allocate)
        st_x = np.zeros(n_max)
        st_z = np.zeros(n_max)
        st_th = np.zeros(n_max)
        st_phi = np.zeros(n_max)
        st_xd = np.zeros(n_max)
        st_zd = np.zeros(n_max)
        st_thd = np.zeros(n_max)
        st_t = np.zeros(n_max)
        st_speed = np.zeros(n_max)
        st_alpha = np.zeros(n_max)
        st_lx = np.zeros(n_max)
        st_lz = np.zeros(n_max)
        st_dx = np.zeros(n_max)
        st_dz = np.zeros(n_max)

        m = self.MASS
        Sw = self.WING_AREA
        Se = self.ELEV_AREA
        lw = self.WING_DIST
        le = self.ELEV_DIST
        I = self.INERTIA
        rho = self.RHO
        g = self.G

        # Auto-trim: compute initial θ for level flight (lift = weight)
        q0 = 0.5 * rho * v0 * v0
        cl_needed = m * g / (q0 * Sw)
        if cl_needed < 1.0:
            alpha_trim = 0.5 * np.arcsin(cl_needed)
        else:
            alpha_trim = 0.35  # ~20° cap — glider descends at low speed

        # Initial conditions — flying RIGHT toward perch at x=0
        st_x[0] = -3.5
        st_z[0] = z0
        st_xd[0] = v0
        st_th[0] = alpha_trim  # trimmed for level flight
        st_speed[0] = v0

        # Controller setup
        theta_target = 1.4  # rad ≈ 80° — target pitch for perching
        if mode == "p_controller":
            kp = float(self.parameters["Kp"])
            trigger_dist = 2.0  # m — pitch-up triggers at this distance
        elif mode == "optimal":
            # Adapt gains to speed — tuned at v0=6 m/s
            speed_ratio = v0 / 6.0
            kp = self.OPT_KP / speed_ratio
            kd = self.OPT_KD / speed_ratio
            theta_target = self.OPT_THETA_TARGET
            # Scale trigger distance; ensure enough coast/pitch-up time
            trigger_dist = self.OPT_TRIGGER * speed_ratio
            self._actual_gains = {"Kp": round(kp, 1), "Kd": round(kd, 1)}
        else:
            trigger_dist = 2.0  # not used for open-loop

        last_step = n_max - 1

        for i in range(n_max - 1):
            t = i * dt
            st_t[i] = t

            x_i = st_x[i]
            z_i = st_z[i]
            th = st_th[i]
            phi = st_phi[i]
            xd = st_xd[i]
            zd = st_zd[i]
            thd = st_thd[i]

            # Airspeed
            V = np.sqrt(xd * xd + zd * zd)
            V = max(V, 1e-6)  # prevent division by zero
            st_speed[i] = V

            # Flight path angle & angles of attack
            gamma = np.arctan2(zd, xd)
            alpha_w = th - gamma
            # Elevator convention: positive φ deflects trailing edge UP,
            # reducing elevator AoA → downforce on tail → nose UP pitch.
            alpha_e = th - phi - gamma
            st_alpha[i] = alpha_w

            # Dynamic pressure
            q = 0.5 * rho * V * V

            # Aerodynamic forces — wing
            cl_w, cd_w = self._aero_coeffs(alpha_w)
            Lw = q * Sw * cl_w
            Dw = q * Sw * cd_w

            # Aerodynamic forces — elevator
            cl_e, cd_e = self._aero_coeffs(alpha_e)
            Le = q * Se * cl_e
            De = q * Se * cd_e

            # Total lift and drag in inertial frame
            cos_g = np.cos(gamma)
            sin_g = np.sin(gamma)
            L_total = Lw + Le
            D_total = Dw + De

            fx = -D_total * cos_g - L_total * sin_g
            fz = -D_total * sin_g + L_total * cos_g

            st_lx[i] = -L_total * sin_g
            st_lz[i] = L_total * cos_g
            st_dx[i] = -D_total * cos_g
            st_dz[i] = -D_total * sin_g

            # Accelerations
            xdd = fx / m
            zdd = fz / m - g
            # Pitching moment with aerodynamic damping
            moment_aero = (
                lw * (Lw * np.cos(alpha_w) + Dw * np.sin(alpha_w))
                - le * (Le * np.cos(alpha_e) + De * np.sin(alpha_e))
            )
            # Velocity-dependent pitch damping (increases with speed)
            moment_damp = -self.PITCH_DAMP * V * thd
            thdd = (moment_aero + moment_damp) / I

            # Control input u = phi_dot
            if mode == "open_loop":
                u = float(self.parameters["elevator_rate"])
            elif mode == "p_controller":
                # Coast until within trigger distance, then P-control on pitch
                dist_remaining = -x_i  # positive distance to perch
                if dist_remaining > trigger_dist:
                    u = 0.0  # coast
                else:
                    # Ramp reference from 0 to θ_target based on distance
                    frac = 1.0 - dist_remaining / trigger_dist
                    frac = min(1.0, frac * 1.5)
                    theta_ref = theta_target * frac
                    u = kp * (theta_ref - th)
            else:  # optimal
                # Position-triggered PD with feedforward
                dist_to_perch = -x_i  # positive distance remaining
                if dist_to_perch > trigger_dist:
                    u = 0.0  # coast phase
                else:
                    # Smooth ramp based on distance (closer = higher reference)
                    frac = 1.0 - dist_to_perch / trigger_dist
                    frac = min(1.0, frac * 1.5)  # reach target at 2/3 of trigger zone
                    theta_ref = theta_target * frac
                    u = kp * (theta_ref - th) + kd * (0.0 - thd)

            # Clamp actuator
            u = np.clip(u, -self.PHI_DOT_MAX, self.PHI_DOT_MAX)

            # Euler step
            st_x[i + 1] = x_i + xd * dt
            st_z[i + 1] = z_i + zd * dt
            st_th[i + 1] = th + thd * dt
            st_phi[i + 1] = np.clip(phi + u * dt, -self.PHI_MAX, self.PHI_MAX)
            st_xd[i + 1] = xd + xdd * dt
            st_zd[i + 1] = zd + zdd * dt
            st_thd[i + 1] = thd + thdd * dt

            # Termination checks
            next_x = st_x[i + 1]
            next_z = st_z[i + 1]
            next_V = np.sqrt(st_xd[i + 1] ** 2 + st_zd[i + 1] ** 2)
            dist_to_perch = np.sqrt(next_x ** 2 + (next_z - z0) ** 2)

            # Perch capture: close to perch, slow, nose up, not tumbling
            if (dist_to_perch < 0.5 and next_V < 2.5
                    and st_th[i + 1] > 0.35 and st_th[i + 1] < 2.5):
                last_step = i + 1
                break
            if next_z < -0.3:  # crashed below ground
                last_step = i + 1
                break
            if next_x > 2.0:  # overshot perch (flying right past x=0)
                last_step = i + 1
                break

        # Fill last timestep's derived quantities
        st_t[last_step] = last_step * dt
        V_last = np.sqrt(st_xd[last_step] ** 2 + st_zd[last_step] ** 2)
        st_speed[last_step] = V_last
        gamma_last = np.arctan2(st_zd[last_step], st_xd[last_step])
        st_alpha[last_step] = st_th[last_step] - gamma_last

        # Trim arrays
        n = last_step + 1
        self._trajectory = {
            "time": st_t[:n],
            "x": st_x[:n],
            "z": st_z[:n],
            "theta": st_th[:n],
            "phi": st_phi[:n],
            "xdot": st_xd[:n],
            "zdot": st_zd[:n],
            "speed": st_speed[:n],
            "alpha_w": st_alpha[:n],
            "lift_x": st_lx[:n],
            "lift_z": st_lz[:n],
            "drag_x": st_dx[:n],
            "drag_z": st_dz[:n],
        }

        # Evaluate outcome
        self._evaluate_outcome(v0, z0)

    def _evaluate_outcome(self, v0: float, z_perch: float) -> None:
        """Determine perching success/failure."""
        traj = self._trajectory
        x_f = float(traj["x"][-1])
        z_f = float(traj["z"][-1])
        V_f = float(traj["speed"][-1])
        th_f = float(traj["theta"][-1])
        dist = np.sqrt(x_f ** 2 + (z_f - z_perch) ** 2)

        success = dist < 0.5 and V_f < 2.5 and th_f > 0.35  # >20°

        if success:
            reason = "perched"
        elif z_f < -0.3:
            reason = "crashed"
        elif x_f > 1.5:
            reason = "overshot"
        else:
            reason = "timeout"

        self._outcome = {
            "success": success,
            "reason": reason,
            "final_speed": round(V_f, 3),
            "final_distance": round(dist, 3),
            "final_theta_deg": round(float(np.degrees(th_f)), 1),
            "perch_z": round(z_perch, 2),
        }

    def _control_info(self) -> Dict[str, Any]:
        """Return control mode details for the info panel."""
        mode = self.parameters["control_mode"]
        if mode == "open_loop":
            return {"mode": mode, "gains": {"elevator_rate": self.parameters["elevator_rate"]}}
        elif mode == "p_controller":
            return {"mode": mode, "gains": {"Kp": self.parameters["Kp"]}}
        else:
            return {
                "mode": mode,
                "gains": self._actual_gains if self._actual_gains else
                    {"Kp": self.OPT_KP, "Kd": self.OPT_KD},
            }

    # ── Plot builders ─────────────────────────────────────────────────

    def _base_layout(self) -> Dict[str, Any]:
        return {
            "margin": {"l": 60, "r": 30, "t": 50, "b": 50},
            "plot_bgcolor": "rgba(0,0,0,0)",
            "paper_bgcolor": "rgba(0,0,0,0)",
            "font": {"color": "#e2e8f0", "family": "Inter, sans-serif", "size": 12},
        }

    def _axis_style(self, title: str) -> Dict[str, Any]:
        return {
            "title": title,
            "showgrid": True,
            "gridcolor": "rgba(148,163,184,0.1)",
            "zerolinecolor": "rgba(148,163,184,0.3)",
            "color": "#f1f5f9",
        }

    def _plot_trajectory(self) -> Dict[str, Any]:
        """Flight path x vs z."""
        traj = self._trajectory
        x = traj["x"]
        z = traj["z"]
        success = self._outcome.get("success", False)
        z_perch = self._outcome.get("perch_z", float(self.parameters["initial_altitude"]))

        data = [
            # Ground line
            {
                "x": [-4.5, 2.5], "y": [0, 0],
                "type": "scatter", "mode": "lines",
                "name": "Ground",
                "line": {"color": "rgba(148,163,184,0.3)", "width": 1, "dash": "dot"},
                "showlegend": False,
            },
            # Flight path
            {
                "x": x.tolist(), "y": z.tolist(),
                "type": "scatter", "mode": "lines",
                "name": "Flight Path",
                "line": {"color": "#3b82f6", "width": 2.5},
            },
            # Start marker
            {
                "x": [float(x[0])], "y": [float(z[0])],
                "type": "scatter", "mode": "markers",
                "name": "Start",
                "marker": {"color": "#3b82f6", "size": 10, "symbol": "circle"},
            },
            # End marker
            {
                "x": [float(x[-1])], "y": [float(z[-1])],
                "type": "scatter", "mode": "markers",
                "name": "End",
                "marker": {
                    "color": "#10b981" if success else "#ef4444",
                    "size": 12,
                    "symbol": "star" if success else "x",
                },
            },
            # Perch target (at initial altitude)
            {
                "x": [0], "y": [z_perch],
                "type": "scatter", "mode": "markers",
                "name": "Perch",
                "marker": {"color": "#f59e0b", "size": 14, "symbol": "triangle-up"},
            },
        ]

        layout = {
            **self._base_layout(),
            "xaxis": {
                **self._axis_style("x (m)"),
                "range": [-4.5, 1.5],
                "scaleanchor": "y",
                "constrain": "domain",
            },
            "yaxis": {
                **self._axis_style("z (m)"),
                "autorange": True,
            },
            "legend": {"x": 0.02, "y": 0.98, "xanchor": "left", "yanchor": "top",
                       "font": {"color": "#94a3b8"}},
            "showlegend": True,
        }

        fp = f"traj-{self.parameters['control_mode']}-{self.parameters.get('Kp', 0)}-{self.parameters.get('elevator_rate', 0)}"
        layout["uirevision"] = fp

        return {"id": "trajectory_2d", "title": "Flight Path", "data": data, "layout": layout}

    def _plot_state_history(self) -> Dict[str, Any]:
        """Speed, pitch angle, elevator angle vs time."""
        traj = self._trajectory
        t = traj["time"]

        data = [
            {
                "x": t.tolist(),
                "y": traj["speed"].tolist(),
                "type": "scatter", "mode": "lines",
                "name": "|V| (m/s)",
                "line": {"color": "#3b82f6", "width": 2},
            },
            {
                "x": t.tolist(),
                "y": np.degrees(traj["theta"]).tolist(),
                "type": "scatter", "mode": "lines",
                "name": "θ (deg)",
                "line": {"color": "#ef4444", "width": 2},
                "yaxis": "y2",
            },
            {
                "x": t.tolist(),
                "y": np.degrees(traj["phi"]).tolist(),
                "type": "scatter", "mode": "lines",
                "name": "φ (deg)",
                "line": {"color": "#14b8a6", "width": 2, "dash": "dash"},
                "yaxis": "y2",
            },
        ]

        layout = {
            **self._base_layout(),
            "xaxis": self._axis_style("Time (s)"),
            "yaxis": {
                **self._axis_style("Speed (m/s)"),
                "autorange": True,
                "side": "left",
            },
            "yaxis2": {
                **self._axis_style("Angle (deg)"),
                "autorange": True,
                "side": "right",
                "overlaying": "y",
            },
            "legend": {
                "orientation": "h", "y": 1.12, "x": 0.5, "xanchor": "center",
                "font": {"color": "#94a3b8"},
            },
            "showlegend": True,
        }

        fp = f"state-{self.parameters['control_mode']}-{self.parameters.get('Kp', 0)}-{self.parameters.get('elevator_rate', 0)}"
        layout["uirevision"] = fp

        return {"id": "state_history", "title": "State History", "data": data, "layout": layout}

    def _plot_aero(self) -> Dict[str, Any]:
        """CL, CD, α vs time."""
        traj = self._trajectory
        t = traj["time"]
        alpha_deg = np.degrees(traj["alpha_w"])

        # Recompute CL, CD from stored alpha_w
        cl = 2.0 * np.sin(traj["alpha_w"]) * np.cos(traj["alpha_w"])
        cd = 2.0 * np.sin(traj["alpha_w"]) ** 2

        data = [
            {
                "x": t.tolist(), "y": cl.tolist(),
                "type": "scatter", "mode": "lines",
                "name": "C_L",
                "line": {"color": "#3b82f6", "width": 2},
            },
            {
                "x": t.tolist(), "y": cd.tolist(),
                "type": "scatter", "mode": "lines",
                "name": "C_D",
                "line": {"color": "#ef4444", "width": 2},
            },
            {
                "x": t.tolist(), "y": alpha_deg.tolist(),
                "type": "scatter", "mode": "lines",
                "name": "α (deg)",
                "line": {"color": "#10b981", "width": 2, "dash": "dash"},
                "yaxis": "y2",
            },
        ]

        layout = {
            **self._base_layout(),
            "xaxis": self._axis_style("Time (s)"),
            "yaxis": {
                **self._axis_style("Coefficient"),
                "autorange": True,
                "side": "left",
            },
            "yaxis2": {
                **self._axis_style("α (deg)"),
                "autorange": True,
                "side": "right",
                "overlaying": "y",
            },
            "legend": {
                "orientation": "h", "y": 1.12, "x": 0.5, "xanchor": "center",
                "font": {"color": "#94a3b8"},
            },
            "showlegend": True,
        }

        fp = f"aero-{self.parameters['control_mode']}-{self.parameters.get('Kp', 0)}"
        layout["uirevision"] = fp

        return {"id": "aero_forces", "title": "Aerodynamic Coefficients", "data": data, "layout": layout}

    def _plot_poles(self) -> Dict[str, Any]:
        """Closed-loop poles of linearised pitch dynamics (P-controller only).

        Simplified model around hover-ish trim:
            I·θ̈ + c_aero·θ̇ + Kp·θ = Kp·θ_ref
        where c_aero is an approximate aerodynamic pitch damping coefficient.
        Characteristic polynomial: I·s² + c_aero·s + Kp = 0
        """
        kp = float(self.parameters["Kp"])

        # Approximate aero damping from trim (q * Sw * dCL/dα * lw ≈ ...)
        v_trim = float(self.parameters["initial_speed"])
        q_trim = 0.5 * self.RHO * v_trim ** 2
        c_aero = q_trim * self.WING_AREA * 2.0 * self.WING_DIST  # ≈ dCL/dα * area * arm
        c_aero = max(c_aero, 1e-6)

        I = self.INERTIA

        # Compute poles for current Kp
        disc = c_aero ** 2 - 4.0 * I * kp
        if disc >= 0:
            s1 = (-c_aero + np.sqrt(disc)) / (2.0 * I)
            s2 = (-c_aero - np.sqrt(disc)) / (2.0 * I)
            poles_re = [s1, s2]
            poles_im = [0.0, 0.0]
        else:
            real_part = -c_aero / (2.0 * I)
            imag_part = np.sqrt(-disc) / (2.0 * I)
            poles_re = [real_part, real_part]
            poles_im = [imag_part, -imag_part]

        # Root locus — sweep Kp from 0 to 30
        kp_sweep = np.linspace(0.01, 30.0, 200)
        locus_re = []
        locus_im = []
        for k in kp_sweep:
            d = c_aero ** 2 - 4.0 * I * k
            if d >= 0:
                locus_re.append((-c_aero + np.sqrt(d)) / (2.0 * I))
                locus_im.append(0.0)
                locus_re.append((-c_aero - np.sqrt(d)) / (2.0 * I))
                locus_im.append(0.0)
            else:
                rp = -c_aero / (2.0 * I)
                ip = np.sqrt(-d) / (2.0 * I)
                locus_re.extend([rp, rp])
                locus_im.extend([ip, -ip])

        # Imaginary axis (stability boundary)
        im_axis_range = max(abs(v) for v in locus_im) * 1.2 if any(v != 0 for v in locus_im) else 100.0

        data = [
            # Root locus
            {
                "x": locus_re, "y": locus_im,
                "type": "scatter", "mode": "markers",
                "name": "Root Locus",
                "marker": {"color": "rgba(59,130,246,0.15)", "size": 3},
            },
            # Stability boundary
            {
                "x": [0, 0], "y": [-im_axis_range, im_axis_range],
                "type": "scatter", "mode": "lines",
                "name": "Stability Boundary",
                "line": {"color": "rgba(148,163,184,0.4)", "width": 1, "dash": "dash"},
                "showlegend": False,
            },
            # Current poles
            {
                "x": poles_re, "y": poles_im,
                "type": "scatter", "mode": "markers",
                "name": f"Poles (Kp={kp})",
                "marker": {"color": "#ef4444", "size": 12, "symbol": "x"},
            },
        ]

        layout = {
            **self._base_layout(),
            "xaxis": {
                **self._axis_style("Re(s)"),
                "zeroline": True,
            },
            "yaxis": {
                **self._axis_style("Im(s)"),
                "zeroline": True,
                "scaleanchor": "x",
                "constrain": "domain",
            },
            "legend": {"x": 0.02, "y": 0.98, "xanchor": "left", "yanchor": "top",
                       "font": {"color": "#94a3b8"}},
            "showlegend": True,
            "uirevision": f"poles-{kp}",
        }

        return {"id": "pole_plot", "title": "Closed-Loop Poles (s-plane)", "data": data, "layout": layout}
