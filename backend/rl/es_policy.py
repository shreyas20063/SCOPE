"""Evolution Strategies for plant-adaptive PID tuning.

Theory (CMU 16-745 Lecture 18 — ILC connection):
Each ES generation perturbs the policy, evaluates on random plants,
and updates toward the best perturbations — analogous to Iterative
Learning Control where each iteration refines control from trial data.
"""
from __future__ import annotations

import json
from math import factorial
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from scipy import signal as sig


def _pade(T: float, n: int = 3) -> tuple[list[float], list[float]]:
    """Padé approximation of e^(-sT). Returns (num, den) polynomials.

    Replaces scipy.signal.pade which was removed in SciPy 1.17.
    """
    num = [0.0] * (n + 1)
    den = [0.0] * (n + 1)
    for k in range(n + 1):
        coeff = factorial(2 * n - k) * factorial(n) / (
            factorial(2 * n) * factorial(k) * factorial(n - k)
        )
        val = coeff * T**k
        den[k] = val
        num[k] = val * (-1)**k
    return num, den

if TYPE_CHECKING:
    pass

_trapz = np.trapezoid if hasattr(np, "trapezoid") else np.trapz


class LinearPolicy:
    """Linear mapping: [Kp, Ki, Kd] = sigmoid(W @ features + b) * scales."""

    def __init__(self, n_features: int = 8, n_actions: int = 3):
        self.n_features = n_features
        self.n_actions = n_actions
        self.W = np.random.randn(n_actions, n_features) * 0.1
        self.b = np.zeros(n_actions)
        self.scales = np.array([50.0, 20.0, 10.0])

    @property
    def params(self) -> np.ndarray:
        return np.concatenate([self.W.ravel(), self.b])

    @params.setter
    def params(self, flat: np.ndarray) -> None:
        n_w = self.n_features * self.n_actions
        self.W = flat[:n_w].reshape(self.n_actions, self.n_features)
        self.b = flat[n_w:]

    def predict(self, features: np.ndarray) -> dict[str, float]:
        raw = self.W @ features + self.b
        normalized = 1.0 / (1.0 + np.exp(-np.clip(raw, -10, 10)))
        gains = normalized * self.scales
        return {
            "Kp": float(max(gains[0], 0.001)),
            "Ki": float(max(gains[1], 0)),
            "Kd": float(max(gains[2], 0)),
        }

    def save(self, path: str) -> None:
        data = {"W": self.W.tolist(), "b": self.b.tolist(), "scales": self.scales.tolist()}
        Path(path).write_text(json.dumps(data))

    def load(self, path: str) -> None:
        data = json.loads(Path(path).read_text())
        self.W = np.array(data["W"])
        self.b = np.array(data["b"])
        self.scales = np.array(data["scales"])


class ESOptimizer:
    """(mu+lambda) Evolution Strategy for training LinearPolicy."""

    def __init__(self, policy: LinearPolicy, pop_size: int = 50,
                 elite_frac: float = 0.2, sigma: float = 0.1, lr: float = 0.01):
        self.policy = policy
        self.pop_size = pop_size
        self.n_elite = max(1, int(pop_size * elite_frac))
        self.sigma = sigma
        self.lr = lr
        self.n_params = len(policy.params)

    def ask(self) -> tuple[list[np.ndarray], np.ndarray]:
        base = self.policy.params
        noise = np.random.randn(self.pop_size, self.n_params) * self.sigma
        candidates = [base + n for n in noise]
        return candidates, noise

    def tell(self, noise: np.ndarray, fitness: list[float]) -> None:
        order = np.argsort(fitness)[::-1]
        elite_noise = np.array([noise[i] for i in order[:self.n_elite]])
        elite_fit = np.array([fitness[i] for i in order[:self.n_elite]])

        weights = elite_fit - elite_fit.mean()
        if weights.std() > 1e-8:
            weights = weights / weights.std()
        else:
            weights = np.ones_like(weights) / len(weights)
        weights = np.maximum(weights, 0)
        if weights.sum() > 0:
            weights /= weights.sum()

        grad = weights @ elite_noise
        self.policy.params = self.policy.params + self.lr * grad


def evaluate_policy_on_plant(
    policy: LinearPolicy,
    features: np.ndarray,
    plant_num: np.ndarray,
    plant_den: np.ndarray,
    sim_duration: float = 10.0,
) -> float:
    """Evaluate policy's PID gains on a given plant. Returns fitness (higher = better)."""
    gains = policy.predict(features)
    kp, ki, kd = gains["Kp"], gains["Ki"], gains["Kd"]
    N = 20.0

    # Build PID TF
    if ki > 1e-12 and kd > 1e-12:
        ctrl_num = np.array([kp + kd * N, kp * N + ki, ki * N])
        ctrl_den = np.array([1.0, N, 0.0])
    elif ki > 1e-12:
        ctrl_num = np.array([kp, ki])
        ctrl_den = np.array([1.0, 0.0])
    elif kd > 1e-12:
        ctrl_num = np.array([kp + kd * N, kp * N])
        ctrl_den = np.array([1.0, N])
    else:
        ctrl_num = np.array([kp])
        ctrl_den = np.array([1.0])

    # Closed-loop TF
    ol_num = np.convolve(plant_num, ctrl_num)
    ol_den = np.convolve(plant_den, ctrl_den)
    ml = max(len(ol_den), len(ol_num))
    cl_den = np.pad(ol_den, (ml - len(ol_den), 0)) + np.pad(ol_num, (ml - len(ol_num), 0))

    # Stability
    try:
        poles = np.roots(cl_den)
        if len(poles) > 0 and np.max(poles.real) > 0:
            return -100.0
    except Exception:
        return -100.0

    # Step response
    try:
        sys_cl = sig.TransferFunction(ol_num, cl_den)
        t = np.linspace(0, sim_duration, 500)
        t_out, y = sig.step(sys_cl, T=t)
        if not np.all(np.isfinite(y)):
            return -100.0
    except Exception:
        return -100.0

    # Fitness: negative ITAE + penalties
    e = np.abs(1.0 - y)
    itae = float(_trapz(t_out * e, t_out))
    peak = float(np.max(y))
    final = float(y[-1]) if np.isfinite(y[-1]) else 0.0
    overshoot = max(0, (peak - final) / max(abs(final), 1e-6) * 100)

    return float(10.0 - np.log1p(itae) - 0.5 * max(0, overshoot - 5) / 100 - 2.0 * abs(1.0 - final))


def generate_random_plant(rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray, str]:
    """Generate a random plant from 6 trainable presets."""
    preset = rng.choice(["first_order", "second_order", "integrator",
                         "fopdt", "dc_motor", "unstable"])

    if preset == "first_order":
        K = rng.uniform(0.5, 10)
        tau = rng.uniform(0.1, 5)
        return np.array([K]), np.array([tau, 1.0]), str(preset)

    elif preset == "second_order":
        K = rng.uniform(0.5, 5)
        wn = rng.uniform(1, 20)
        zeta = rng.uniform(0.1, 2)
        return np.array([K * wn**2]), np.array([1, 2 * zeta * wn, wn**2]), str(preset)

    elif preset == "integrator":
        K = rng.uniform(0.5, 10)
        return np.array([K]), np.array([1, 0]), str(preset)

    elif preset == "fopdt":
        K = rng.uniform(0.5, 5)
        tau = rng.uniform(0.5, 5)
        delay = rng.uniform(0.1, 2)
        pade_num, pade_den = _pade(delay, 3)
        num = np.convolve([K], pade_num)
        den = np.convolve([tau, 1.0], pade_den)
        return num, den, str(preset)

    elif preset == "dc_motor":
        K = rng.uniform(0.5, 10)
        J = rng.uniform(0.005, 0.05)
        b = rng.uniform(0.05, 0.5)
        return np.array([K]), np.array([J, b, 0]), str(preset)

    else:  # unstable
        K = rng.uniform(0.5, 5)
        a = rng.uniform(0.5, 5)
        return np.array([K]), np.array([1, -a]), str(preset)
