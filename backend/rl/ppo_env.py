"""Gymnasium environment for PID tuning via PPO.

Theory (CMU 16-745 Lectures 21+24):
PPO learns a neural policy pi(obs)->action, analogous to LQG's
optimal control under uncertainty but without requiring a known
noise model. The agent discovers optimal PID gains from experience.
"""
from __future__ import annotations

import numpy as np

try:
    import gymnasium as gym
    from gymnasium import spaces
    HAS_GYM = True
except ImportError:
    HAS_GYM = False

from .plant_features import extract_plant_features
from .es_policy import generate_random_plant

_trapz = np.trapezoid if hasattr(np, "trapezoid") else np.trapz


def _build_pid_tf(kp: float, ki: float, kd: float, N: float = 20.0):
    """Build PID controller TF from gains."""
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


if HAS_GYM:
    class PIDTuningEnv(gym.Env):
        """Single-step MDP for plant-adaptive PID tuning.

        Observation: 8D plant feature vector
        Action: 3D continuous [Kp_norm, Ki_norm, Kd_norm] in [-1, 1]
        Reward: Multi-objective fitness
        Episode: Always 1 step (terminates after action)
        """
        metadata = {"render_modes": []}

        def __init__(self, sim_duration: float = 10.0):
            super().__init__()
            self.observation_space = spaces.Box(low=-1, high=1, shape=(8,), dtype=np.float64)
            self.action_space = spaces.Box(low=-1, high=1, shape=(3,), dtype=np.float32)
            self.sim_duration = sim_duration
            self.rng = np.random.default_rng()
            self._current_plant = None
            self._current_features = None
            self._scales = np.array([50.0, 20.0, 10.0])

        def reset(self, seed=None, options=None):
            super().reset(seed=seed)
            if seed is not None:
                self.rng = np.random.default_rng(seed)
            plant_num, plant_den, preset = generate_random_plant(self.rng)
            self._current_plant = (plant_num, plant_den)
            self._current_features = extract_plant_features(plant_num, plant_den)
            return self._current_features.astype(np.float64), {"preset": preset}

        def step(self, action):
            normalized = (np.asarray(action, dtype=np.float64) + 1) / 2
            gains = normalized * self._scales
            kp = float(max(gains[0], 0.001))
            ki = float(max(gains[1], 0))
            kd = float(max(gains[2], 0))

            plant_num, plant_den = self._current_plant
            fitness = self._evaluate(kp, ki, kd, plant_num, plant_den)

            info = {"Kp": kp, "Ki": ki, "Kd": kd, "fitness": fitness}
            return self._current_features, float(fitness), True, False, info

        def _evaluate(self, kp, ki, kd, plant_num, plant_den):
            from scipy import signal as sig

            ctrl_num, ctrl_den = _build_pid_tf(kp, ki, kd)
            ol_num = np.convolve(plant_num, ctrl_num)
            ol_den = np.convolve(plant_den, ctrl_den)
            ml = max(len(ol_den), len(ol_num))
            cl_den = np.pad(ol_den, (ml - len(ol_den), 0)) + np.pad(ol_num, (ml - len(ol_num), 0))

            try:
                poles = np.roots(cl_den)
                if len(poles) > 0 and np.max(poles.real) > 0:
                    return -100.0
            except Exception:
                return -100.0

            try:
                sys_cl = sig.TransferFunction(ol_num, cl_den)
                t = np.linspace(0, self.sim_duration, 500)
                t_out, y = sig.step(sys_cl, T=t)
                if not np.all(np.isfinite(y)):
                    return -100.0
            except Exception:
                return -100.0

            e = np.abs(1.0 - y)
            itae = float(_trapz(t_out * e, t_out))
            peak = float(np.max(y))
            final = float(y[-1]) if np.isfinite(y[-1]) else 0.0
            overshoot = max(0, (peak - final) / max(abs(final), 1e-6) * 100)

            return 10.0 - np.log1p(itae) - 0.5 * max(0, overshoot - 5) / 100 - 2.0 * abs(1.0 - final)
