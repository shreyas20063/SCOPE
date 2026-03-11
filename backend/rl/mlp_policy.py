"""Actor-Critic (A2C) for plant-adaptive PID tuning.

Connection to optimal control:
LQR minimizes J = ∫(x'Qx + u'Ru)dt analytically via Riccati equations.
A2C learns the same type of optimal policy from simulation experience,
without requiring an explicit plant model. Both minimize a quadratic cost;
RL generalises this to arbitrary (learnable) cost functions. This places
A2C in the Adaptive Dynamic Programming (ADP) lineage of optimal control.

Architecture:
  Actor  : 16D state → 32 tanh → 3D (Gaussian policy, outputs Δgains)
  Critic : 16D state → 32 tanh → 1D (value function V(s))

Multi-step MDP (12 steps per episode):
  s_t = [plant_features(8D), norm_gains(3D), perf_metrics(4D), step_frac(1D)]
  a_t = tanh(mu(s_t) + sigma*noise)   — delta-gain adjustment
  r_t = ITAE_prev - ITAE_new          — reward = improvement
  G_t = Σ_{j>=t} γ^j r_{t+j}         — Monte-Carlo return

Pure NumPy/SciPy — no PyTorch, stable-baselines3, or gymnasium required.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

# ============================================================
# Shared constants
# ============================================================

GAIN_LO = np.array([0.01, 0.0, 0.0])
GAIN_HI = np.array([20.0, 8.0, 4.0])
DELTA_SCALES = np.array([0.80, 0.32, 0.16])  # max ΔKp, ΔKi, ΔKd per step
MAX_STEPS = 12
GAMMA = 0.99

_trapz = np.trapezoid if hasattr(np, "trapezoid") else np.trapz


# ============================================================
# Environment helpers
# ============================================================

def evaluate_gains(
    kp: float,
    ki: float,
    kd: float,
    plant_num: np.ndarray,
    plant_den: np.ndarray,
    sim_duration: float = 10.0,
) -> tuple[float, float, float, float, bool]:
    """Simulate closed-loop PID response. Returns (itae, overshoot%, rise_time, sse, stable)."""
    from scipy import signal as sig

    N = 20.0
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

    ol_num = np.convolve(ctrl_num, plant_num)
    ol_den = np.convolve(ctrl_den, plant_den)
    ml = max(len(ol_den), len(ol_num))
    cl_den = np.pad(ol_den, (ml - len(ol_den), 0)) + np.pad(ol_num, (ml - len(ol_num), 0))

    _UNSTABLE = (3000.0, 200.0, 30.0, 2.0, False)

    try:
        poles = np.roots(cl_den)
        if len(poles) > 0 and np.max(poles.real) > 0:
            return _UNSTABLE
    except Exception:
        return _UNSTABLE

    try:
        T = np.linspace(0, sim_duration, 500)
        t_out, y = sig.step(sig.TransferFunction(ol_num, cl_den), T=T)
        if not np.all(np.isfinite(y)):
            return _UNSTABLE
    except Exception:
        return _UNSTABLE

    itae = float(_trapz(t_out * np.abs(1.0 - y), t_out))
    ss = float(y[-1]) if np.isfinite(y[-1]) else 0.0
    overshoot = max(0.0, (float(np.max(y)) - ss) / max(abs(ss), 1e-6) * 100.0)
    thresh = 0.9 * ss
    idx = int(np.argmax(y >= thresh)) if np.any(y >= thresh) else len(t_out) - 1
    rise_time = float(t_out[idx])
    sse = abs(1.0 - ss)

    return itae, overshoot, rise_time, sse, True


def build_state(
    plant_feats: np.ndarray,
    gains: np.ndarray,
    perf: tuple[float, float, float, float],
    step: int,
    max_steps: int = MAX_STEPS,
) -> np.ndarray:
    """Build 16D state vector: [plant(8), gains_norm(3), perf_norm(4), step_frac(1)]."""
    itae, overshoot, rise_time, sse = perf
    s = np.empty(16, dtype=np.float64)
    s[:8] = plant_feats
    s[8] = gains[0] / 10.0
    s[9] = gains[1] / 4.0
    s[10] = gains[2] / 2.0
    s[11] = np.log1p(itae) / 8.0
    s[12] = min(overshoot, 200.0) / 200.0
    s[13] = np.log1p(rise_time) / np.log1p(30.0)
    s[14] = min(sse, 2.0) / 2.0
    s[15] = step / max_steps
    return np.clip(s, -5.0, 5.0)


def compute_mc_returns(rewards: list[float], gamma: float = GAMMA) -> np.ndarray:
    """Discounted MC return G_t = Σ_{j>=t} γ^{j-t} r_{t+j}."""
    G = np.zeros(len(rewards))
    running = 0.0
    for t in reversed(range(len(rewards))):
        running = rewards[t] + gamma * running
        G[t] = running
    return G


# ============================================================
# Adam optimizer (per-network state)
# ============================================================

class AdamOptimizer:
    """Stateful Adam optimizer (Kingma & Ba, 2014) for one network."""

    def __init__(self, lr: float = 1e-3, beta1: float = 0.9, beta2: float = 0.999, eps: float = 1e-8):
        self.lr = lr
        self.beta1 = beta1
        self.beta2 = beta2
        self.eps = eps
        self._m: dict[str, np.ndarray] = {}
        self._v: dict[str, np.ndarray] = {}
        self._t = 0

    def step(self, params: dict[str, np.ndarray], grads: dict[str, np.ndarray], max_norm: float = 0.5) -> None:
        """Update params in-place. Applies global gradient norm clipping first."""
        # Gradient clipping
        total_sq = sum(float(np.sum(g ** 2)) for g in grads.values())
        global_norm = float(np.sqrt(total_sq))
        if global_norm > max_norm and global_norm > 0:
            coef = max_norm / global_norm
            grads = {k: g * coef for k, g in grads.items()}

        self._t += 1
        for key, g in grads.items():
            if key not in self._m:
                self._m[key] = np.zeros_like(g)
                self._v[key] = np.zeros_like(g)
            self._m[key] = self.beta1 * self._m[key] + (1.0 - self.beta1) * g
            self._v[key] = self.beta2 * self._v[key] + (1.0 - self.beta2) * g ** 2
            m_hat = self._m[key] / (1.0 - self.beta1 ** self._t)
            v_hat = self._v[key] / (1.0 - self.beta2 ** self._t)
            params[key] -= self.lr * m_hat / (np.sqrt(v_hat) + self.eps)


# ============================================================
# Network primitives
# ============================================================

def _tanh(x: np.ndarray) -> np.ndarray:
    return np.tanh(np.clip(x, -10.0, 10.0))


def _tanh_grad(h: np.ndarray) -> np.ndarray:
    return 1.0 - h ** 2


# ============================================================
# Actor network
# ============================================================

class A2CActor:
    """Actor: 16D → 32 tanh → 3 linear + 3 log_std (Gaussian policy).

    Outputs delta-gain adjustments [ΔKp, ΔKi, ΔKd] via tanh squashing.
    Training objective: maximise E[A_t * log π(a_t|s_t)] + entropy bonus.
    Inference: deterministic (mu only, no noise).
    """

    def __init__(self, n_state: int = 16, hidden: int = 32, n_actions: int = 3):
        self.n_state = n_state
        self.hidden = hidden
        self.n_actions = n_actions
        rng = np.random.default_rng(42)
        scale1 = np.sqrt(2.0 / n_state)
        scale2 = np.sqrt(2.0 / hidden) * 0.1  # small output init
        self.W1 = rng.standard_normal((hidden, n_state)) * scale1
        self.b1 = np.zeros(hidden)
        self.W2 = rng.standard_normal((n_actions, hidden)) * scale2
        self.b2 = np.zeros(n_actions)
        self.log_std = np.full(n_actions, -1.0)  # initial σ ≈ 0.37

    # --- Forward ---

    def forward(self, s: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Single-state forward. Returns (mu: (n_actions,), h: (hidden,))."""
        h = _tanh(self.W1 @ s + self.b1)
        mu = self.W2 @ h + self.b2
        return mu, h

    def forward_batch(self, S: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Batch forward. S: (N, n_state) → MU: (N, n_actions), H: (N, hidden)."""
        H = _tanh(S @ self.W1.T + self.b1)
        MU = H @ self.W2.T + self.b2
        return MU, H

    def sample(self, s: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Sample action (with exploration noise). Returns (action, pre_tanh_action)."""
        mu, _ = self.forward(s)
        std = np.exp(np.clip(self.log_std, -3.0, 0.0))
        noise = np.random.standard_normal(self.n_actions)
        pre_tanh = mu + std * noise
        return _tanh(pre_tanh), pre_tanh

    # --- Gradients ---

    def compute_gradients(
        self,
        S: np.ndarray,
        A_pre: np.ndarray,
        advantages: np.ndarray,
        entropy_coef: float = 0.005,
    ) -> dict[str, np.ndarray]:
        """Compute gradients of loss L = -E[A * log_π] - entropy_coef * H[π].

        Args:
            S:          (N, 16) state batch
            A_pre:      (N, 3)  pre-tanh actions (stored during collection)
            advantages: (N,)    normalised advantage estimates A_t = G_t - V(s_t)
            entropy_coef: scalar entropy regularisation coefficient
        Returns:
            Gradient dict (dL/d_param) — Adam subtracts these, yielding ascent on E[R].
        """
        N = S.shape[0]
        MU, H = self.forward_batch(S)                            # (N,3), (N,32)
        std = np.exp(np.clip(self.log_std, -3.0, 0.0))          # (3,)
        var = std ** 2 + 1e-8                                    # (3,)

        adv = advantages[:, np.newaxis]                          # (N, 1) for broadcasting

        # dL/d_MU[i,j] = -advantages[i] * (A_pre[i,j] - MU[i,j]) / var[j] / N
        d_MU = -adv * (A_pre - MU) / var / N                    # (N, 3)

        # Backprop through W2, b2
        grad_W2 = d_MU.T @ H                                    # (3, 32) = dL/dW2
        grad_b2 = d_MU.sum(axis=0)                              # (3,)    = dL/db2

        # Backprop through hidden layer
        d_H = d_MU @ self.W2                                     # (N, 32)
        d_H_pre = d_H * _tanh_grad(H)                           # (N, 32)

        grad_W1 = d_H_pre.T @ S                                  # (32, 16)
        grad_b1 = d_H_pre.sum(axis=0)                           # (32,)

        # dL/d_log_std[j] = -mean_i[A_i * ((a_ij - mu_ij)^2/var_j - 1)] - entropy_coef
        # (derivative of log-prob w.r.t. log_std, plus entropy gradient)
        grad_log_std = (
            -np.mean(adv * ((A_pre - MU) ** 2 / var - 1.0), axis=0)
            - entropy_coef
        )                                                         # (3,)

        return {
            "W1": grad_W1, "b1": grad_b1,
            "W2": grad_W2, "b2": grad_b2,
            "log_std": grad_log_std,
        }

    def apply_gradients(self, grads: dict[str, np.ndarray], optimizer: AdamOptimizer) -> None:
        params = {"W1": self.W1, "b1": self.b1, "W2": self.W2, "b2": self.b2, "log_std": self.log_std}
        optimizer.step(params, grads)
        self.log_std = np.clip(self.log_std, -3.0, 0.0)

    # --- Serialisation ---

    def to_dict(self) -> dict:
        return {
            "W1a": self.W1.tolist(), "b1a": self.b1.tolist(),
            "W2a": self.W2.tolist(), "b2a": self.b2.tolist(),
            "log_std": self.log_std.tolist(),
        }

    def from_dict(self, d: dict) -> None:
        self.W1 = np.array(d["W1a"])
        self.b1 = np.array(d["b1a"])
        self.W2 = np.array(d["W2a"])
        self.b2 = np.array(d["b2a"])
        self.log_std = np.array(d["log_std"])


# ============================================================
# Critic network
# ============================================================

class A2CCritic:
    """Critic: 16D → 32 tanh → 1 linear. Estimates V(s).

    Trained via MSE: L_c = 0.5 * E[(V(s_t) - G_t)^2].
    Linear output head (no activation) is essential for value function regression.
    """

    def __init__(self, n_state: int = 16, hidden: int = 32):
        self.n_state = n_state
        self.hidden = hidden
        rng = np.random.default_rng(43)
        self.W1 = rng.standard_normal((hidden, n_state)) * np.sqrt(2.0 / n_state)
        self.b1 = np.zeros(hidden)
        self.W2 = rng.standard_normal((1, hidden)) * np.sqrt(2.0 / hidden) * 0.01
        self.b2 = np.zeros(1)

    def forward(self, s: np.ndarray) -> float:
        h = _tanh(self.W1 @ s + self.b1)
        return float((self.W2 @ h + self.b2)[0])

    def forward_batch(self, S: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Returns (V: (N,), H: (N, hidden))."""
        H = _tanh(S @ self.W1.T + self.b1)
        V = (H @ self.W2.T + self.b2)[:, 0]
        return V, H

    def compute_gradients(self, S: np.ndarray, targets: np.ndarray) -> dict[str, np.ndarray]:
        """Gradient of L_c = 0.5 * mean((V - G)^2) w.r.t. all params."""
        N = S.shape[0]
        V, H = self.forward_batch(S)

        # dL_c/dV[i] = (V[i] - G[i]) / N
        d_V = (V - targets) / N                                  # (N,)

        grad_W2 = d_V[np.newaxis, :] @ H                        # (1, hidden) = dL_c/dW2
        grad_b2 = np.array([d_V.sum()])                         # (1,)

        d_H = np.outer(d_V, self.W2[0])                         # (N, hidden)
        d_H_pre = d_H * _tanh_grad(H)

        grad_W1 = d_H_pre.T @ S                                  # (hidden, n_state)
        grad_b1 = d_H_pre.sum(axis=0)

        return {"W1": grad_W1, "b1": grad_b1, "W2": grad_W2, "b2": grad_b2}

    def apply_gradients(self, grads: dict[str, np.ndarray], optimizer: AdamOptimizer) -> None:
        params = {"W1": self.W1, "b1": self.b1, "W2": self.W2, "b2": self.b2}
        optimizer.step(params, grads)

    def to_dict(self) -> dict:
        return {
            "W1c": self.W1.tolist(), "b1c": self.b1.tolist(),
            "W2c": self.W2.tolist(), "b2c": self.b2.tolist(),
        }

    def from_dict(self, d: dict) -> None:
        self.W1 = np.array(d["W1c"])
        self.b1 = np.array(d["b1c"])
        self.W2 = np.array(d["W2c"])
        self.b2 = np.array(d["b2c"])


# ============================================================
# Model I/O
# ============================================================

MODEL_TYPE_KEY = "a2c_v1"


def save_a2c(actor: A2CActor, critic: A2CCritic, path: str) -> None:
    data = {**actor.to_dict(), **critic.to_dict(), "model_type": MODEL_TYPE_KEY}
    Path(path).write_text(json.dumps(data))


def load_a2c(path: str) -> tuple[A2CActor, A2CCritic]:
    data = json.loads(Path(path).read_text())
    if data.get("model_type") != MODEL_TYPE_KEY:
        raise ValueError(f"Expected model_type={MODEL_TYPE_KEY!r}, got {data.get('model_type')!r}")
    actor = A2CActor()
    critic = A2CCritic()
    actor.from_dict(data)
    critic.from_dict(data)
    return actor, critic


# ============================================================
# A2C training loop
# ============================================================

class A2CTrainer:
    """Multi-step Actor-Critic (A2C) trainer.

    Each episode: sample random plant → iteratively refine gains over 12 steps.
    Reward = ITAE improvement per step. Monte-Carlo returns used for critic targets.
    Advantage = G_t - V(s_t) used to scale actor gradient.
    """

    def __init__(
        self,
        lr_actor: float = 1e-3,
        lr_critic: float = 2e-3,
        n_batch: int = 20,
        entropy_coef_start: float = 0.005,
        entropy_coef_end: float = 0.001,
        total_episodes: int = 5000,
    ):
        self.actor = A2CActor()
        self.critic = A2CCritic()
        self._actor_opt = AdamOptimizer(lr=lr_actor)
        self._critic_opt = AdamOptimizer(lr=lr_critic)
        self.n_batch = n_batch
        self.entropy_start = entropy_coef_start
        self.entropy_end = entropy_coef_end
        self.total_episodes = total_episodes
        self.best_mean_return = float("-inf")
        self._return_window: list[float] = []

    def _entropy_coef(self, episode: int) -> float:
        frac = min(episode / max(self.total_episodes, 1), 1.0)
        return self.entropy_start + (self.entropy_end - self.entropy_start) * frac

    def collect_episode(
        self,
        plant_num: np.ndarray,
        plant_den: np.ndarray,
        plant_feats: np.ndarray,
    ) -> list[tuple[np.ndarray, np.ndarray, float]]:
        """Run one 12-step episode. Returns list of (state, pre_tanh_action, reward)."""
        gains = np.array([5.0, 2.0, 1.0], dtype=np.float64)
        itae, overshoot, rise_time, sse, _ = evaluate_gains(
            gains[0], gains[1], gains[2], plant_num, plant_den
        )
        perf = (itae, overshoot, rise_time, sse)
        transitions: list[tuple[np.ndarray, np.ndarray, float]] = []

        for step in range(MAX_STEPS):
            s = build_state(plant_feats, gains, perf, step)
            action, pre_tanh = self.actor.sample(s)

            new_gains = np.clip(gains + DELTA_SCALES * action, GAIN_LO, GAIN_HI)
            new_itae, new_os, new_rt, new_sse, stable = evaluate_gains(
                new_gains[0], new_gains[1], new_gains[2], plant_num, plant_den
            )

            if stable:
                reward = float(np.clip(itae - new_itae, -50.0, 50.0))
                if step == MAX_STEPS - 1 and new_itae < 2.0:
                    reward += 10.0
                gains = new_gains
                perf = (new_itae, new_os, new_rt, new_sse)
                itae = new_itae
            else:
                reward = -10.0  # instability penalty; keep current gains

            transitions.append((s, pre_tanh, reward))

        return transitions

    def _update_batch(
        self,
        buffer: list[tuple[np.ndarray, np.ndarray, float]],
        episode_idx: int,
    ) -> float:
        """Update actor and critic from a batch of transitions."""
        entropy_coef = self._entropy_coef(episode_idx)

        S = np.array([t[0] for t in buffer], dtype=np.float64)        # (N, 16)
        A_pre = np.array([t[1] for t in buffer], dtype=np.float64)    # (N, 3)
        G = np.array([t[2] for t in buffer], dtype=np.float64)        # (N,)

        # Critic forward (detached from actor graph)
        V, _ = self.critic.forward_batch(S)                           # (N,)

        # Advantages with normalisation
        advantages = G - V                                             # (N,)
        adv_std = advantages.std() + 1e-8
        advantages = (advantages - advantages.mean()) / adv_std

        # Critic update — minimise MSE(V, G)
        critic_grads = self.critic.compute_gradients(S, G)
        self.critic.apply_gradients(critic_grads, self._critic_opt)

        # Actor update — maximise E[A * log π] + entropy
        actor_grads = self.actor.compute_gradients(S, A_pre, advantages, entropy_coef)
        self.actor.apply_gradients(actor_grads, self._actor_opt)

        return float(G.mean())

    def run(
        self,
        total_episodes: int,
        cancel_flag,               # threading.Event
        model_path: str,
        progress_cb=None,          # callable(dict) or None
    ) -> float:
        """Main training loop. Returns best mean episodic return."""
        from .es_policy import generate_random_plant
        from .plant_features import extract_plant_features
        rng = np.random.default_rng()

        buffer: list[tuple[np.ndarray, np.ndarray, float]] = []
        episode_returns: list[float] = []
        episode_idx = 0

        while episode_idx < total_episodes:
            if cancel_flag.is_set():
                break

            plant_num, plant_den, _ = generate_random_plant(rng)
            plant_feats = extract_plant_features(plant_num, plant_den)

            transitions = self.collect_episode(plant_num, plant_den, plant_feats)
            rewards = [t[2] for t in transitions]
            G_t = compute_mc_returns(rewards)

            for (s, a_pre, _), g in zip(transitions, G_t):
                buffer.append((s, a_pre, float(g)))
            episode_returns.append(float(sum(rewards)))

            episode_idx += 1

            if len(episode_returns) >= self.n_batch:
                mean_return = self._update_batch(buffer, episode_idx)

                self._return_window.extend(episode_returns)
                if len(self._return_window) > 100:
                    self._return_window = self._return_window[-100:]
                smoothed = float(np.mean(self._return_window))

                if smoothed > self.best_mean_return:
                    self.best_mean_return = smoothed
                    save_a2c(self.actor, self.critic, model_path)

                if progress_cb:
                    progress_cb({
                        "type": "rl_training_progress",
                        "timestep": episode_idx,
                        "total_timesteps": total_episodes,
                        "progress_pct": episode_idx / total_episodes * 100.0,
                        "reward_mean": smoothed,
                    })

                buffer = []
                episode_returns = []

        return self.best_mean_return
