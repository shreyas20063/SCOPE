"""Actor-Critic (A2C) inference wrapper for PID tuning.

Provides the same predict(features) interface as before, but now runs
a 12-step deterministic rollout: the actor observes the current gains
and performance metrics at each step and refines the gains incrementally.

This is analogous to an iterative Newton step in nonlinear optimal control:
each actor query produces a descent direction in gain space.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from .mlp_policy import (
    A2CActor, A2CCritic, load_a2c,
    evaluate_gains, build_state, _tanh,
    GAIN_LO, GAIN_HI, DELTA_SCALES, MAX_STEPS,
)


class PPOAgent:
    """Loads a trained A2C model and runs multi-step deterministic inference."""

    def __init__(self, model_path: str | None = None) -> None:
        self._actor: A2CActor | None = None
        self._critic: A2CCritic | None = None
        self.model_path = Path(
            model_path
            or Path(__file__).parent.parent / "assets" / "models" / "a2c_pid_tuner.json"
        )

    def _load(self) -> None:
        if self._actor is not None:
            return
        if not self.model_path.exists():
            return
        try:
            self._actor, self._critic = load_a2c(str(self.model_path))
        except Exception:
            self._actor = None
            self._critic = None

    def is_available(self) -> bool:
        self._load()
        return self._actor is not None

    def predict(
        self,
        features: np.ndarray,
        plant_num: np.ndarray | None = None,
        plant_den: np.ndarray | None = None,
    ) -> dict[str, float] | None:
        """Run 12-step deterministic rollout.

        If plant_num/plant_den are provided, each step actually simulates
        the closed-loop response (accurate feedback). Otherwise, uses
        a fixed perf estimate based only on features (fast approximation).
        """
        self._load()
        if self._actor is None:
            return None

        gains = np.array([5.0, 2.0, 1.0], dtype=np.float64)

        # Initialise performance metrics
        if plant_num is not None and plant_den is not None:
            itae, overshoot, rise_time, sse, _ = evaluate_gains(
                gains[0], gains[1], gains[2], plant_num, plant_den
            )
        else:
            itae, overshoot, rise_time, sse = 5.0, 10.0, 2.0, 0.1
        perf = (itae, overshoot, rise_time, sse)

        for step in range(MAX_STEPS):
            s = build_state(features, gains, perf, step)
            mu, _ = self._actor.forward(s)         # deterministic: no noise
            delta = _tanh(mu)
            new_gains = np.clip(gains + DELTA_SCALES * delta, GAIN_LO, GAIN_HI)

            if plant_num is not None and plant_den is not None:
                new_itae, new_os, new_rt, new_sse, stable = evaluate_gains(
                    new_gains[0], new_gains[1], new_gains[2], plant_num, plant_den
                )
                if stable:
                    gains = new_gains
                    perf = (new_itae, new_os, new_rt, new_sse)
            else:
                gains = new_gains  # no feedback — apply unconditionally

        return {
            "Kp": float(gains[0]),
            "Ki": float(gains[1]),
            "Kd": float(gains[2]),
        }
