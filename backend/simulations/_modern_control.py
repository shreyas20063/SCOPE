"""Modern control mixin — state feedback, pole placement, LQR, LQG.

Contains: state-feedback gain computation, pole placement via scipy,
LQR/LQG design with Riccati equations, reference feedforward (N_bar),
conjugate pair enforcement, and LQG augmented state-space construction.

Mixed into ControllerTuningLabSimulator via multiple inheritance.
All methods use `self.` to access the host class's attributes:
    self._A, self._B, self._C, self._D, self._plant_order, etc.
"""

import numpy as np
from scipy import signal


class ModernControlMixin:
    """Mixin providing modern control methods for ControllerTuningLabSimulator."""

    # ------------------------------------------------------------------
    # State-feedback gain
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # LQG controller
    # ------------------------------------------------------------------

    def _build_lqg_controller(self) -> None:
        """Build LQG closed-loop via augmented state-space (plant + observer).

        Uses separation principle: LQR gain K from performance Riccati,
        Kalman gain L from estimator (dual) Riccati. The augmented 2n-order
        system shows both controlled-plant poles and observer poles.

        Reference feedforward N_bar = -1/(C*(A-BK)^{-1}*B) ensures unit
        DC gain for step tracking.
        """
        p = self.parameters
        n = self._plant_order
        Q = np.diag([float(p.get(f"lqr_q{i + 1}", 1.0)) for i in range(n)])
        R_ctrl = np.atleast_2d(float(p.get("lqr_r", 1.0)))
        Qw = np.diag([float(p.get(f"lqg_qw{i + 1}", 1.0)) for i in range(n)])
        Rv_scalar = max(float(p.get("lqg_rv", 0.1)), 1e-6)
        Rv = np.atleast_2d(Rv_scalar)

        try:
            from scipy.linalg import solve_continuous_are

            # LQR Riccati: A'P + PA - PBR⁻¹B'P + Q = 0 → K = R⁻¹B'P
            P_lqr = solve_continuous_are(self._A, self._B, Q, R_ctrl)
            K_vec = np.linalg.solve(R_ctrl, self._B.T @ P_lqr).flatten()

            # Kalman Riccati (dual): AΣ + ΣA' - ΣC'Rv⁻¹CΣ + Qw = 0 → L = ΣC'Rv⁻¹
            P_kal = solve_continuous_are(self._A.T, self._C.T, Qw, Rv)
            L = (P_kal @ self._C.T / Rv_scalar).reshape(-1, 1)

            # Reference feedforward for unit step tracking:
            # N_bar = -1/(C * (A-BK)^{-1} * B) so CL DC gain = 1
            A_sf = self._A - self._B @ K_vec.reshape(1, -1)
            dc_sf = float((self._C @ np.linalg.solve(A_sf, self._B)).item())
            N_bar = -1.0 / dc_sf if abs(dc_sf) > 1e-6 else 1.0
            # Guard: N_bar must be positive and bounded for physical tracking.
            # Non-minimum-phase plants (Padé RHP zeros) can produce negative
            # or extreme N_bar; fall back to N_bar=1 (accept SSE).
            if N_bar <= 0 or N_bar > 20.0:
                N_bar = 1.0

            # Augmented 2n-order state-space: z = [x (plant); x̂ (observer)]
            # ẋ  = Ax - BKx̂ + BN_bar*r
            # x̂̇ = LCx + (A-BK-LC)x̂ + BN_bar*r
            # y  = Cx
            A_aug = np.block([
                [self._A, -self._B @ K_vec.reshape(1, -1)],
                [L @ self._C, self._A - self._B @ K_vec.reshape(1, -1) - L @ self._C],
            ])
            B_aug = np.vstack([self._B, self._B]) * N_bar
            C_aug = np.hstack([self._C, np.zeros_like(self._C)])
            D_aug = self._D

            cl_ss = signal.StateSpace(A_aug, B_aug, C_aug, D_aug)
            cl_tf = cl_ss.to_tf()
            self._cl_num = np.atleast_1d(cl_tf.num)
            self._cl_den = np.atleast_1d(cl_tf.den)

            # Dummy controller TF (not used in state_feedback_mode)
            self._ctrl_num = np.array([1.0])
            self._ctrl_den = np.array([1.0])
            self._state_feedback_K = K_vec
            self._kalman_L = L.flatten()
            self._state_feedback_mode = True
        except Exception:
            self._ctrl_num = np.array([1.0])
            self._ctrl_den = np.array([1.0])
            self._cl_num = self._plant_num.copy()
            self._cl_den = self._plant_den.copy()
            self._state_feedback_K = None
            self._kalman_L = None
            self._state_feedback_mode = True

    # ------------------------------------------------------------------
    # Conjugate pair enforcement
    # ------------------------------------------------------------------

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
