"""PPO training orchestration with async support.

Theory (CMU 16-745 Lectures 21+24):
PPO uses clipped surrogate objective to safely update neural policy
parameters. The agent discovers optimal PID gains from experience
across diverse plant dynamics — analogous to LQG's optimal control
under uncertainty but without requiring a known noise model.
"""
from __future__ import annotations

import asyncio
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Callable

if TYPE_CHECKING:
    pass

try:
    from stable_baselines3 import PPO
    from stable_baselines3.common.callbacks import BaseCallback
    HAS_SB3 = True
except ImportError:
    HAS_SB3 = False


class PPOTrainer:
    """PPO trainer with async training + progress callbacks."""

    def __init__(self) -> None:
        self.state = "idle"
        self._model = None
        self._cancel_flag = threading.Event()
        self._progress: dict = {}
        self.model_path = Path(__file__).parent.parent / "assets" / "models" / "ppo_pid_tuner.zip"
        self.model_path.parent.mkdir(parents=True, exist_ok=True)

    async def start_training(
        self,
        total_timesteps: int = 100_000,
        callback: Optional[Callable] = None,
    ) -> None:
        """Start PPO training in thread pool."""
        if not HAS_SB3:
            raise RuntimeError(
                "PPO requires: pip install stable-baselines3 gymnasium torch"
            )
        if self.state == "training":
            raise RuntimeError("Training already in progress")

        self.state = "training"
        self._cancel_flag.clear()
        self._progress = {"episode": 0, "reward_mean": 0, "progress_pct": 0}

        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                None, self._train_sync, total_timesteps, callback, loop
            )
            self.state = "complete"
            self._progress = {**self._progress, **result}
            if callback:
                await callback({"type": "rl_training_complete", **result})
        except Exception as e:
            self.state = "error"
            self._progress["error"] = str(e)
            if callback:
                await callback({"type": "rl_training_error", "error": str(e)})

    def _train_sync(
        self,
        total_timesteps: int,
        callback: Optional[Callable],
        loop: asyncio.AbstractEventLoop,
    ) -> dict:
        """Synchronous training (runs in thread pool)."""
        from .ppo_env import PIDTuningEnv

        env = PIDTuningEnv()
        model = PPO(
            "MlpPolicy",
            env,
            learning_rate=3e-4,
            n_steps=256,
            batch_size=64,
            n_epochs=10,
            gamma=0.99,
            verbose=0,
            device="cpu",
        )

        trainer = self

        class ProgressCallback(BaseCallback):
            def __init__(self) -> None:
                super().__init__()
                self._last_broadcast = 0

            def _on_step(self) -> bool:
                if trainer._cancel_flag.is_set():
                    return False

                step = self.num_timesteps
                if step - self._last_broadcast >= 500:
                    self._last_broadcast = step
                    reward_mean = 0.0
                    if hasattr(self.logger, "name_to_value"):
                        reward_mean = float(
                            self.logger.name_to_value.get("rollout/ep_rew_mean", 0)
                        )
                    progress = {
                        "type": "rl_training_progress",
                        "timestep": step,
                        "total_timesteps": total_timesteps,
                        "progress_pct": step / total_timesteps * 100,
                        "reward_mean": reward_mean,
                    }
                    trainer._progress = progress
                    if callback and loop:
                        asyncio.run_coroutine_threadsafe(callback(progress), loop)
                return True

        model.learn(total_timesteps=total_timesteps, callback=ProgressCallback())
        model.save(str(self.model_path))
        self._model = model

        return {
            "final_reward": float(trainer._progress.get("reward_mean", 0)),
            "model_path": str(self.model_path),
        }

    def cancel_training(self) -> None:
        """Cancel ongoing training."""
        self._cancel_flag.set()
        self.state = "cancelled"

    def get_status(self) -> dict:
        """Get current training status."""
        return {"state": self.state, **self._progress}
