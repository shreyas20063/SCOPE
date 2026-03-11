"""PPO inference for PID tuning.

Loads a trained PPO model and maps plant features to PID gains.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np


class PPOAgent:
    """Load and run inference on a trained PPO model."""

    def __init__(self, model_path: str | None = None) -> None:
        self._model = None
        self.model_path = Path(
            model_path
            or Path(__file__).parent.parent / "assets" / "models" / "ppo_pid_tuner.zip"
        )

    def _load(self) -> None:
        if self._model is not None:
            return
        if not self.model_path.exists():
            return
        try:
            from stable_baselines3 import PPO

            self._model = PPO.load(str(self.model_path), device="cpu")
        except (ImportError, Exception):
            self._model = None

    def is_available(self) -> bool:
        """Check if a trained model is available."""
        self._load()
        return self._model is not None

    def predict(self, features: np.ndarray) -> dict[str, float] | None:
        """Run inference. Returns {"Kp", "Ki", "Kd"} or None."""
        self._load()
        if self._model is None:
            return None

        action, _ = self._model.predict(features.astype(np.float64), deterministic=True)
        scales = np.array([50.0, 20.0, 10.0])
        normalized = (np.asarray(action, dtype=np.float64) + 1) / 2
        gains = normalized * scales

        return {
            "Kp": float(max(gains[0], 0.001)),
            "Ki": float(max(gains[1], 0)),
            "Kd": float(max(gains[2], 0)),
        }
