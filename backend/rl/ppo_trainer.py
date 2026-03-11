"""A2C training orchestration with async/background-thread support.

The Actor-Critic policy is trained by collecting 20 episodes per batch,
computing MC returns, then updating both actor and critic via Adam.
Estimated training time at 5000 episodes: ~60-90 seconds on CPU.

All heavy computation runs in a thread pool (run_in_executor) so the
FastAPI event loop stays responsive during training.
"""
from __future__ import annotations

import asyncio
import threading
from pathlib import Path
from typing import Optional, Callable

from .mlp_policy import A2CTrainer


class PPOTrainer:
    """Async wrapper around A2CTrainer. Keeps the same public interface
    as before so no changes are needed in main.py endpoints."""

    def __init__(self) -> None:
        self.state = "idle"
        self._cancel_flag = threading.Event()
        self._progress: dict = {}
        self.model_path = (
            Path(__file__).parent.parent / "assets" / "models" / "a2c_pid_tuner.json"
        )
        self.model_path.parent.mkdir(parents=True, exist_ok=True)

    async def start_training(
        self,
        total_timesteps: int = 5_000,
        callback: Optional[Callable] = None,
    ) -> None:
        """Start A2C training in a thread pool. total_timesteps = number of episodes."""
        if self.state == "training":
            raise RuntimeError("Training already in progress")

        self.state = "training"
        self._cancel_flag.clear()
        self._progress = {"episode": 0, "reward_mean": 0.0, "progress_pct": 0.0}

        loop = asyncio.get_running_loop()
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
        total_episodes: int,
        callback: Optional[Callable],
        loop: asyncio.AbstractEventLoop,
    ) -> dict:
        """Synchronous A2C training (runs in thread pool)."""
        trainer = A2CTrainer(total_episodes=total_episodes)

        def progress_cb(progress_dict: dict) -> None:
            self._progress = progress_dict
            if callback and loop:
                asyncio.run_coroutine_threadsafe(callback(progress_dict), loop)

        best_return = trainer.run(
            total_episodes=total_episodes,
            cancel_flag=self._cancel_flag,
            model_path=str(self.model_path),
            progress_cb=progress_cb,
        )

        if self._cancel_flag.is_set():
            self.state = "cancelled"

        return {
            "final_reward": float(best_return),
            "model_path": str(self.model_path),
        }

    def cancel_training(self) -> None:
        self._cancel_flag.set()
        self.state = "cancelled"

    def get_status(self) -> dict:
        return {"state": self.state, **self._progress}
