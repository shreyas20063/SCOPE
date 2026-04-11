"""PID auto-tuning mixin — classical and optimization-based tuning methods.

Contains: Ziegler-Nichols (open/closed), Cohen-Coon, Lambda, IMC,
ITAE (Nelder-Mead), Differential Evolution, ES policy, PPO/A2C agent.
Also includes FOPDT model fitting and plant-type detection helpers.

Mixed into ControllerTuningLabSimulator via multiple inheritance.
All methods use `self.` to access the host class's attributes:
    self._plant_num, self._plant_den, self.parameters, self._tuning_info, etc.
"""

import numpy as np
from scipy import signal, optimize

# NumPy 2.0 compat
_trapz = np.trapezoid if hasattr(np, 'trapezoid') else np.trapz


class PIDTuningMixin:
    """Mixin providing PID auto-tuning methods for ControllerTuningLabSimulator."""

    # ------------------------------------------------------------------
    # PID TF helper
    # ------------------------------------------------------------------

    def _pid_to_tf(self, kp: float, ki: float, kd: float) -> tuple[np.ndarray, np.ndarray]:
        """Convert PID gains to TF numerator/denominator (reusable helper)."""
        N = float(self.parameters.get("deriv_filter_N", 20))
        if abs(ki) > 1e-12 and abs(kd) > 1e-12:
            num = np.array([kp + kd * N, kp * N + ki, ki * N])
            den = np.array([1.0, N, 0.0])
        elif abs(ki) > 1e-12:
            num = np.array([kp, ki])
            den = np.array([1.0, 0.0])
        elif abs(kd) > 1e-12:
            num = np.array([kp + kd * N, kp * N])
            den = np.array([1.0, N])
        else:
            num = np.array([kp])
            den = np.array([1.0])
        return num, den

    # ------------------------------------------------------------------
    # Auto-tune dispatcher
    # ------------------------------------------------------------------

    def _auto_tune(self) -> dict | None:
        """Run selected auto-tuning method, return gain dict or None.

        Classical FOPDT-based methods (ZN, Cohen-Coon, Lambda, IMC) assume
        a stable, self-regulating process.  For unstable or integrating
        plants these are meaningless, so we auto-redirect to DE optimization
        and tell the user why.
        """
        method = self.parameters.get("tuning_method", "manual")
        ctype = self.parameters.get("controller_type", "PID")

        plant_type = self._detect_plant_type()
        fopdt_methods = {"zn_open", "zn_closed", "cohen_coon", "lambda_tuning", "imc"}
        if plant_type in ("unstable", "integrating") and method in fopdt_methods:
            label = method.replace("_", " ").title()
            self._tuning_info = (
                f"{label} assumes a stable plant — redirecting to "
                f"Differential Evolution for this {plant_type} system"
            )
            method = "de_optimal"

        dispatch = {
            "zn_open": self._zn_open_loop,
            "zn_closed": self._zn_closed_loop,
            "cohen_coon": self._cohen_coon,
            "lambda_tuning": self._lambda_tuning,
            "imc": self._imc_tuning,
            "itae_optimal": self._itae_optimal,
            "de_optimal": self._de_optimal,
            "es_adaptive": self._es_tune,
            "ppo_rl": self._ppo_tune,
        }
        func = dispatch.get(method)
        if func is None:
            return None
        try:
            result = func(ctype)
            if result:
                info = f"{method.replace('_', ' ').title()} → Kp={result.get('Kp', 0):.4g}, Ki={result.get('Ki', 0):.4g}, Kd={result.get('Kd', 0):.4g}"
                # Prepend redirect note if we changed methods
                if self._tuning_info and "redirecting" in (self._tuning_info or ""):
                    self._tuning_info += f" | {info}"
                else:
                    self._tuning_info = info
            return result
        except Exception as ex:
            self._tuning_info = f"Auto-tune failed: {str(ex)[:100]}"
            return None

    # ------------------------------------------------------------------
    # Plant type detection
    # ------------------------------------------------------------------

    def _detect_plant_type(self) -> str:
        """Detect plant type from open-loop poles.

        Returns 'stable', 'integrating', or 'unstable'.
        """
        try:
            poles = np.roots(self._plant_den)
            if len(poles) == 0:
                return "stable"
            max_real = float(np.max(poles.real))
            if max_real > 1e-4:
                return "unstable"
            if np.any(np.abs(poles.real) < 1e-4):
                return "integrating"
            return "stable"
        except Exception:
            return "stable"

    def _compute_min_stabilizing_kp(self) -> float:
        """Binary search for minimum proportional gain that stabilizes CL.

        Returns the smallest Kp > 0 such that all CL poles of the
        unity-feedback system with P controller have Re < 0.
        Returns inf if P control alone cannot stabilize.
        """
        plant_num = self._plant_num
        plant_den = self._plant_den
        pad_len = len(plant_den) - len(plant_num)

        def _max_cl_real(kp: float) -> float:
            num_padded = np.pad(plant_num, (max(pad_len, 0), 0))
            den_padded = np.pad(plant_den, (max(-pad_len, 0), 0))
            cl_char = den_padded + kp * num_padded
            poles = np.roots(cl_char)
            return float(np.max(poles.real)) if len(poles) > 0 else -1.0

        # Check if high gain stabilizes at all
        if _max_cl_real(1000.0) > 0:
            return float("inf")

        lo, hi = 0.0, 1000.0
        for _ in range(60):
            mid = (lo + hi) / 2
            if _max_cl_real(mid) > 0:
                lo = mid
            else:
                hi = mid
        return hi

    # ------------------------------------------------------------------
    # FOPDT model fitting
    # ------------------------------------------------------------------

    def _fit_fopdt_model(self) -> tuple[float, float, float]:
        """Fit FOPDT model (K_p, tau_p, L) to plant step response.

        Returns (K_p, tau_p, L) — process gain, time constant, dead time.
        For FOPDT preset, returns the user's exact parameters (no fitting).
        For unstable plants, returns an approximation based on the dominant
        RHP pole (FOPDT is not physically meaningful but gives the tuning
        methods *something* reasonable to work with).
        """
        # ── FOPDT preset: use exact user parameters, skip lossy re-fitting ──
        if self.parameters.get("plant_preset") == "fopdt":
            K_p = float(self.parameters.get("plant_gain", 1.0))
            tau_p = float(self.parameters.get("plant_tau", 1.0))
            L = float(self.parameters.get("plant_delay", 0.5))
            return max(abs(K_p), 0.001), max(tau_p, 0.001), max(L, 0.001)

        plant_type = self._detect_plant_type()

        # ── Unstable plants: FOPDT from dominant RHP pole ──
        if plant_type == "unstable":
            try:
                poles = np.roots(self._plant_den)
                rhp = poles[poles.real > 1e-6]
                dominant = float(np.min(np.abs(rhp.real)))  # fastest unstable mode
                K_p = abs(float(
                    np.polyval(self._plant_num, 0)
                    / np.polyval(self._plant_den, 0)
                )) if abs(np.polyval(self._plant_den, 0)) > 1e-10 else 1.0
                tau_p = 1.0 / dominant
                L = max(0.1 * tau_p, 0.01)
                return max(K_p, 0.001), tau_p, L
            except Exception:
                return 1.0, 1.0, 0.1

        # ── Integrating plants: derive from ramp rate ──
        if plant_type == "integrating":
            try:
                plant_sys = signal.TransferFunction(self._plant_num, self._plant_den)
                T = np.linspace(0, 20, 2000)
                t, y = signal.step(plant_sys, T=T)
                # Steady-state ramp rate = lim_{s→0} s*G(s)
                mid = len(y) // 2
                if mid > 10 and np.all(np.isfinite(y[mid:])):
                    slope = float(np.mean(np.gradient(y[mid:], t[mid:])))
                    K_p = max(abs(slope), 0.001)
                else:
                    K_p = 1.0
                tau_p = 1.0  # conventional for integrating processes
                L = max(0.1 * tau_p, 0.01)
                return K_p, tau_p, L
            except Exception:
                return 1.0, 1.0, 0.1

        # ── Stable plants: standard tangent-line FOPDT fit ──
        try:
            plant_sys = signal.TransferFunction(self._plant_num, self._plant_den)
            T = np.linspace(0, 50, 2000)
            t, y = signal.step(plant_sys, T=T)
        except Exception:
            return 1.0, 1.0, 0.1

        if not np.isfinite(y[-1]) or abs(y[-1]) > 1e6:
            return 1.0, 1.0, 0.1

        K_p = float(y[-1])
        if abs(K_p) < 1e-10:
            K_p = 1.0

        dy = np.gradient(y, t)
        i_max = int(np.argmax(np.abs(dy)))
        max_slope = float(dy[i_max])
        if abs(max_slope) < 1e-10:
            return K_p, 1.0, 0.1

        # Dead time: x-intercept of tangent at max slope
        L = float(t[i_max] - y[i_max] / max_slope)

        # Time constant: K_p / max_slope
        tau_p = float(abs(K_p / max_slope))
        tau_p = max(tau_p, 0.001)

        # Clamp L: for plants with negligible dead time the tangent method
        # returns L ≈ 0, which makes ZN/CC formulas divide by ~0.
        # Use at least 10% of tau_p as effective dead time.
        L = max(L, 0.1 * tau_p, 0.01)

        return K_p, tau_p, L

    # ------------------------------------------------------------------
    # Classical tuning methods
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Optimization-based tuning
    # ------------------------------------------------------------------

    def _itae_optimal(self, ctype: str) -> dict:
        """ITAE-optimal tuning via numerical optimization.

        Uses Nelder-Mead to minimise ∫ t·|e(t)| dt subject to CL stability.
        For unstable plants the initial simplex is seeded above the minimum
        stabilising Kp so the optimizer starts in the feasible region.
        """
        plant_num = self._plant_num.copy()
        plant_den = self._plant_den.copy()
        duration = float(self.parameters.get("sim_duration", 10))
        N = float(self.parameters.get("deriv_filter_N", 20))
        T = np.linspace(0, duration, 500)

        def cost(gains: np.ndarray) -> float:
            kp, ki, kd = float(gains[0]), float(gains[1]), float(gains[2])
            # Clamp gains — Nelder-Mead has no bounds, so without this
            # the optimizer pushes gains to infinity (faster → lower ITAE).
            kp = np.clip(kp, 0.001, 100.0)
            ki = np.clip(ki, 0.0, 50.0)
            kd = np.clip(kd, 0.0, 30.0)
            c_num = np.array([kp + kd * N, kp * N + ki, ki * N])
            c_den = np.array([1.0, N, 0.0])
            ol_n = np.convolve(c_num, plant_num)
            ol_d = np.convolve(c_den, plant_den)
            ml = max(len(ol_d), len(ol_n))
            cl_d = np.pad(ol_d, (ml - len(ol_d), 0)) + np.pad(ol_n, (ml - len(ol_n), 0))
            poles = np.roots(cl_d)
            # Reject unstable OR marginally stable CL (pole at origin counts)
            if len(poles) > 0 and np.max(poles.real) > -1e-6:
                return 1e6
            try:
                sys_cl = signal.TransferFunction(ol_n, cl_d)
                t_sim, y_sim = signal.step(sys_cl, T=T)
                if not np.all(np.isfinite(y_sim)):
                    return 1e6
                e_sim = 1.0 - y_sim
                return float(_trapz(t_sim * np.abs(e_sim), t_sim))
            except Exception:
                return 1e6

        # Build initial point — ensure it's in the stable region
        kp0 = float(self.parameters.get("Kp", 1.0))
        ki0 = float(self.parameters.get("Ki", 0.0))
        kd0 = float(self.parameters.get("Kd", 0.0))

        plant_type = self._detect_plant_type()
        if plant_type in ("unstable", "integrating"):
            kp_min = self._compute_min_stabilizing_kp()
            if np.isfinite(kp_min):
                kp0 = max(kp0, kp_min * 2.0)
                ki0 = max(ki0, kp0 * 0.3)

        if kp0 < 0.001:
            kp0 = 1.0

        x0 = np.array([kp0, ki0, kd0])

        # If initial point is infeasible, try a few alternatives
        # (e.g. double integrator needs Kd > 0 to be stabilisable)
        if cost(x0) >= 1e6:
            alternatives = [
                np.array([kp0, ki0, max(kd0, 5.0)]),
                np.array([kp0 * 3, ki0, 10.0]),
                np.array([5.0, 2.0, 10.0]),
            ]
            for alt in alternatives:
                if cost(alt) < 1e6:
                    x0 = alt
                    break
            else:
                # All infeasible — fall back to DE which handles this better
                return self._de_optimal(ctype)

        result = optimize.minimize(
            cost, x0, method="Nelder-Mead",
            options={"maxiter": 200, "xatol": 0.01, "fatol": 0.001},
        )
        kp, ki, kd = float(result.x[0]), float(result.x[1]), float(result.x[2])
        # Apply same clamps as cost function so returned gains match
        kp = float(np.clip(kp, 0.001, 100.0))
        ki = float(np.clip(ki, 0.0, 50.0))
        kd = float(np.clip(kd, 0.0, 30.0))

        if ctype == "P":
            return {"Kp": kp, "Ki": 0.0, "Kd": 0.0}
        elif ctype == "PI":
            return {"Kp": kp, "Ki": ki, "Kd": 0.0}
        elif ctype == "PD":
            return {"Kp": kp, "Ki": 0.0, "Kd": kd}
        return {"Kp": kp, "Ki": ki, "Kd": kd}

    def _de_optimal(self, ctype: str) -> dict | None:
        """Differential Evolution global optimization for PID gains.

        Adapts search bounds to the plant type so that for unstable systems
        the Kp lower bound is above the minimum stabilising gain.
        """
        from scipy.optimize import differential_evolution

        plant_num = self._plant_num.copy()
        plant_den = self._plant_den.copy()
        duration = float(self.parameters.get("sim_duration", 10))
        T = np.linspace(0, duration, 500)

        has_ki = ctype in ("PI", "PID")
        has_kd = ctype in ("PD", "PID")

        # Adapt Kp lower bound for unstable/integrating plants
        plant_type = self._detect_plant_type()
        kp_min_bound = 0.001
        if plant_type in ("unstable", "integrating"):
            kp_min_stab = self._compute_min_stabilizing_kp()
            if np.isfinite(kp_min_stab):
                kp_min_bound = kp_min_stab * 1.1  # just above stability boundary

        bounds = [(kp_min_bound, 100)]
        if has_ki:
            bounds.append((0.01 if plant_type != "stable" else 0, 50))
        if has_kd:
            bounds.append((0, 30))

        pid_to_tf = self._pid_to_tf

        def cost(x: np.ndarray) -> float:
            kp = float(x[0])
            idx = 1
            ki = float(x[idx]) if has_ki else 0.0
            if has_ki:
                idx += 1
            kd = float(x[idx]) if has_kd else 0.0

            c_num, c_den = pid_to_tf(kp, ki, kd)
            ol_n = np.convolve(c_num, plant_num)
            ol_d = np.convolve(c_den, plant_den)
            ml = max(len(ol_d), len(ol_n))
            cl_d = np.pad(ol_d, (ml - len(ol_d), 0)) + np.pad(ol_n, (ml - len(ol_n), 0))

            try:
                poles = np.roots(cl_d)
                if len(poles) > 0 and np.max(poles.real) > -1e-6:
                    return 1e6
            except Exception:
                return 1e6

            try:
                sys_cl = signal.TransferFunction(ol_n, cl_d)
                t_sim, y_sim = signal.step(sys_cl, T=T)
                if not np.all(np.isfinite(y_sim)):
                    return 1e6
                # Reject diverging / wildly oscillating responses that
                # np.roots might miss (high-order Padé numerics).
                # Also reject growing envelope at end of window.
                if np.max(np.abs(y_sim)) > 10.0:
                    return 1e6
                e_sim = np.abs(1.0 - y_sim)
                return float(_trapz(t_sim * e_sim, t_sim))
            except Exception:
                return 1e6

        result = differential_evolution(
            cost, bounds,
            strategy="best1bin",
            maxiter=120,
            popsize=20,
            tol=0.001,
            mutation=(0.5, 1.5),
            recombination=0.7,
            seed=42,
            polish=True,
        )

        # DE reports success=True even when all candidates are infeasible
        # (cost=1e6). Check the cost directly.
        if result.fun >= 1e5:
            return None

        kp = float(result.x[0])
        idx = 1
        ki = float(result.x[idx]) if has_ki else 0.0
        if has_ki:
            idx += 1
        kd = float(result.x[idx]) if has_kd else 0.0

        return {"Kp": max(kp, 0.001), "Ki": max(ki, 0), "Kd": max(kd, 0)}

    # ------------------------------------------------------------------
    # RL / ES tuning
    # ------------------------------------------------------------------

    def _extract_plant_features(self) -> np.ndarray:
        """Extract 8D plant feature vector for RL/ES policies."""
        from pathlib import Path
        import sys
        backend_dir = str(Path(__file__).parent.parent)
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)
        from rl.plant_features import extract_plant_features
        fopdt = self._fit_fopdt_model()
        return extract_plant_features(self._plant_num, self._plant_den, fopdt)

    def _es_tune(self, ctype: str) -> dict | None:
        """Use trained ES policy to predict PID gains."""
        from pathlib import Path
        import sys
        backend_dir = Path(__file__).parent.parent
        if str(backend_dir) not in sys.path:
            sys.path.insert(0, str(backend_dir))

        try:
            from rl.es_policy import LinearPolicy
        except ImportError:
            self._tuning_info = "ES Policy: rl module not found."
            return None

        model_path = backend_dir / "assets" / "models" / "es_pid_policy.json"
        if not model_path.exists():
            self._tuning_info = "ES Policy: No trained model found. Train first."
            return None

        policy = LinearPolicy()
        policy.load(str(model_path))

        features = self._extract_plant_features()
        gains = policy.predict(features)

        self._tuning_info = (f"ES Adaptive → Kp={gains['Kp']:.4g}, "
                             f"Ki={gains['Ki']:.4g}, Kd={gains['Kd']:.4g}")
        return gains

    def _ppo_tune(self, ctype: str) -> dict | None:
        """Use trained A2C agent to predict PID gains via multi-step rollout."""
        from pathlib import Path
        import sys
        backend_dir = Path(__file__).parent.parent
        if str(backend_dir) not in sys.path:
            sys.path.insert(0, str(backend_dir))
        from rl.ppo_agent import PPOAgent

        agent = PPOAgent()
        if not agent.is_available():
            self._tuning_info = "A2C RL: No trained model. Train first."
            return None

        features = self._extract_plant_features()
        # Pass plant TF so the rollout can evaluate each refinement step
        gains = agent.predict(features, plant_num=self._plant_num, plant_den=self._plant_den)
        if gains is None:
            return None

        self._tuning_info = (f"A2C RL → Kp={gains['Kp']:.4g}, "
                             f"Ki={gains['Ki']:.4g}, Kd={gains['Kd']:.4g}")
        return gains
