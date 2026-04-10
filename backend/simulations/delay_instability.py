"""
Delay Effect: The Domino of Instability

Demonstrates how adding sensor delay destabilizes a perfectly-tuned dead-beat
controller.

Three robots approach a wall with the same KT gain product but different
sensor delays (0, 1, 2 steps). No delay = dead-beat convergence, 1-step
delay = marginal oscillation, 2-step delay = divergent instability.
"""

import time
from typing import Any, Dict, List, Optional

import numpy as np

from .base_simulator import BaseSimulator


class DelayInstabilitySimulator(BaseSimulator):
    """Simulator for delay-induced instability in feedback control."""

    # System constants
    T_STEP = 0.1  # Time step duration (locomotion period)
    MAX_POSITION = 50.0  # Clamp to prevent overflow

    PARAMETER_SCHEMA = {
        "kt_product": {
            "type": "slider",
            "min": -2.0,
            "max": -0.1,
            "step": 0.05,
            "default": -1.0,
        },
        "initial_distance": {
            "type": "slider",
            "min": 1.5,
            "max": 5.0,
            "step": 0.1,
            "default": 2.0,
        },
        "target_distance": {
            "type": "slider",
            "min": 0.5,
            "max": 3.0,
            "step": 0.1,
            "default": 1.0,
        },
        "num_steps": {
            "type": "slider",
            "min": 10,
            "max": 40,
            "step": 1,
            "default": 25,
        },
        "playback_speed": {
            "type": "select",
            "options": [
                {"value": "slow", "label": "Slow"},
                {"value": "normal", "label": "Normal"},
                {"value": "fast", "label": "Fast"},
            ],
            "default": "normal",
        },
    }

    DEFAULT_PARAMS = {
        "kt_product": -1.0,
        "initial_distance": 2.0,
        "target_distance": 1.0,
        "num_steps": 25,
        "playback_speed": "normal",
    }


    def __init__(self, simulation_id: str) -> None:
        super().__init__(simulation_id)
        self._animation_step: int = 0
        self._animation_active: bool = False
        # Cached computation results
        self._positions: Dict[str, List[float]] = {}
        self._poles: Dict[str, List[complex]] = {}
        self._crash_step: Optional[int] = None

    def initialize(self, params: Optional[Dict[str, Any]] = None) -> None:
        self.parameters = {**self.DEFAULT_PARAMS, **(params or {})}
        for name, value in self.parameters.items():
            if name in self.PARAMETER_SCHEMA:
                self.parameters[name] = self._validate_param(name, value)
        self._animation_step = 0
        self._animation_active = False
        self._initialized = True
        self._compute()

    def update_parameter(self, name: str, value: Any) -> Dict[str, Any]:
        if name in self.parameters:
            self.parameters[name] = self._validate_param(name, value)
        # Reset animation when system parameters change
        if name in ("kt_product", "initial_distance", "target_distance", "num_steps"):
            self._animation_step = 0
            self._animation_active = False
        self._compute()
        return self.get_state()

    def reset(self) -> Dict[str, Any]:
        self.parameters = self.DEFAULT_PARAMS.copy()
        self._animation_step = 0
        self._animation_active = False
        self._initialized = True
        self._compute()
        return self.get_state()

    def handle_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        N = int(self.parameters["num_steps"])

        if action == "step_forward":
            if self._animation_step < N - 1:
                self._animation_step += 1
                self._animation_active = True
        elif action == "step_backward":
            if self._animation_step > 0:
                self._animation_step -= 1
            if self._animation_step == 0:
                self._animation_active = False
        elif action == "reset_animation":
            self._animation_step = 0
            self._animation_active = False
        elif action == "play_animation":
            # Advance one step (frontend calls repeatedly via setInterval)
            if self._animation_step < N - 1:
                self._animation_step += 1
                self._animation_active = True
            # If we've reached the end, stop
        elif action == "init":
            self._compute()

        return self.get_state()

    def _compute(self) -> None:
        """Compute step responses for all three delay cases."""
        KT = float(self.parameters["kt_product"])
        d_initial = float(self.parameters["initial_distance"])
        d_target = float(self.parameters["target_distance"])
        N = int(self.parameters["num_steps"])
        T = self.T_STEP
        K = KT / T

        # Compute positions for each delay case
        self._positions = {
            "no_delay": self._simulate_system(K, T, d_initial, d_target, N, delay=0),
            "one_step": self._simulate_system(K, T, d_initial, d_target, N, delay=1),
            "two_step": self._simulate_system(K, T, d_initial, d_target, N, delay=2),
        }

        # Find crash step for 2-step delay (first n where d_o < 0, past the wall)
        self._crash_step = None
        for i, pos in enumerate(self._positions["two_step"]):
            if pos < -0.01:  # Small tolerance for floating point
                self._crash_step = i
                break

        # Compute poles
        self._poles = self._compute_poles(KT)

    def _simulate_system(
        self,
        K: float,
        T: float,
        d_initial: float,
        d_target: float,
        N: int,
        delay: int,
    ) -> List[float]:
        """Simulate the wallFinder system with given sensor delay.

        At each step n:
            1. Sensor reads: d_s[n] = d_o[n - delay]
            2. Controller: v[n] = K * (d_target - d_s[n])
            3. Next position: d_o[n+1] = d_o[n] - T * v[n]
        """
        d_o = [0.0] * N
        v = [0.0] * N
        d_o[0] = d_initial

        for n in range(N):
            # Sensor reading with delay
            past_idx = n - delay
            if past_idx < 0:
                d_s = d_initial  # Before sim started, sensor reads initial
            else:
                d_s = d_o[past_idx]

            # Controller command
            v[n] = K * (d_target - d_s)

            # Update position for next step
            if n + 1 < N:
                d_new = d_o[n] - T * v[n]
                d_o[n + 1] = max(-self.MAX_POSITION, min(self.MAX_POSITION, d_new))

        return d_o

    def _compute_poles(self, KT: float) -> Dict[str, List[complex]]:
        """Compute closed-loop poles for each delay case."""
        poles = {}

        # No delay: H(z) = -KTR / (1 - (1+KT)R)
        # Pole at z = 1 + KT
        poles["no_delay"] = [complex(1 + KT, 0)]

        # 1-step delay: z² - z - KT = 0
        coeffs_1 = [1, -1, -KT]
        roots_1 = np.roots(coeffs_1)
        poles["one_step"] = [complex(r) for r in roots_1]

        # 2-step delay: z³ - z² - KT = 0
        coeffs_2 = [1, -1, 0, -KT]
        roots_2 = np.roots(coeffs_2)
        poles["two_step"] = [complex(r) for r in roots_2]

        return poles

    def get_plots(self) -> List[Dict[str, Any]]:
        if not self._positions:
            self._compute()
        return [self._create_position_plot(), self._create_pole_plot()]

    def _create_position_plot(self) -> Dict[str, Any]:
        """Create the position vs time step stem plot."""
        d_target = float(self.parameters["target_distance"])
        N = int(self.parameters["num_steps"])
        KT = float(self.parameters["kt_product"])
        n_arr = list(range(N))

        traces = []

        # Color mapping
        colors = {
            "no_delay": "#10b981",
            "one_step": "#f59e0b",
            "two_step": "#ef4444",
        }
        labels = {
            "no_delay": "No Delay",
            "one_step": "1-Step Delay",
            "two_step": "2-Step Delay",
        }

        for key in ("no_delay", "one_step", "two_step"):
            pos = self._positions.get(key, [])
            color = colors[key]
            label = labels[key]

            # Stem lines
            stem_x: List = []
            stem_y: List = []
            for i in range(len(pos)):
                stem_x.extend([i, i, None])
                stem_y.extend([d_target, pos[i], None])

            traces.append({
                "x": stem_x,
                "y": stem_y,
                "type": "scatter",
                "mode": "lines",
                "name": f"{label} stems",
                "line": {"color": color, "width": 1.5},
                "showlegend": False,
                "hoverinfo": "skip",
            })

            # Marker dots
            traces.append({
                "x": n_arr[:len(pos)],
                "y": pos,
                "type": "scatter",
                "mode": "markers",
                "name": label,
                "marker": {
                    "color": color,
                    "size": 7,
                    "line": {"color": color, "width": 1},
                },
            })

        # Target distance reference line
        traces.append({
            "x": [0, N - 1],
            "y": [d_target, d_target],
            "type": "scatter",
            "mode": "lines",
            "name": f"Target (d = {d_target}m)",
            "line": {"color": "#3b82f6", "width": 2, "dash": "dash"},
        })

        # Wall position reference (d = 0)
        traces.append({
            "x": [0, N - 1],
            "y": [0, 0],
            "type": "scatter",
            "mode": "lines",
            "name": "Wall (d = 0)",
            "line": {"color": "#94a3b8", "width": 1, "dash": "dot"},
            "showlegend": True,
        })

        fingerprint = f"pos-{KT}-{d_target}-{self.parameters['initial_distance']}"
        return {
            "id": "position_timeline",
            "title": "Robot Position vs Time Step",
            "data": traces,
            "layout": {
                "xaxis": {
                    "title": {"text": "Time Step n", "font": {"color": "#f1f5f9", "size": 13}},
                    "gridcolor": "rgba(148,163,184,0.1)",
                    "zerolinecolor": "rgba(148,163,184,0.3)",
                    "color": "#94a3b8",
                    "dtick": 5 if N > 20 else 2,
                },
                "yaxis": {
                    "title": {"text": "Distance to Wall d_o [m]", "font": {"color": "#f1f5f9", "size": 13}},
                    "gridcolor": "rgba(148,163,184,0.1)",
                    "zerolinecolor": "rgba(148,163,184,0.3)",
                    "zerolinewidth": 2,
                    "color": "#94a3b8",
                    "autorange": True,
                },
                "paper_bgcolor": "rgba(0,0,0,0)",
                "plot_bgcolor": "rgba(0,0,0,0)",
                "font": {"family": "Inter, sans-serif", "size": 12, "color": "#f1f5f9"},
                "margin": {"t": 45, "r": 25, "b": 55, "l": 60},
                "showlegend": True,
                "legend": {
                    "font": {"color": "#94a3b8", "size": 11},
                    "bgcolor": "rgba(0,0,0,0)",
                },
                "datarevision": f"pos-{time.time()}",
                "uirevision": fingerprint,
            },
        }

    def _create_pole_plot(self) -> Dict[str, Any]:
        """Create the pole-zero map in the z-plane."""
        KT = float(self.parameters["kt_product"])

        # Unit circle
        theta = np.linspace(0, 2 * np.pi, 100)
        circle_x = np.cos(theta).tolist()
        circle_y = np.sin(theta).tolist()

        traces = [
            {
                "x": circle_x,
                "y": circle_y,
                "type": "scatter",
                "mode": "lines",
                "name": "Unit Circle",
                "line": {"color": "rgba(148,163,184,0.4)", "width": 1.5, "dash": "dash"},
                "showlegend": False,
                "hoverinfo": "skip",
            }
        ]

        colors = {
            "no_delay": "#10b981",
            "one_step": "#f59e0b",
            "two_step": "#ef4444",
        }
        labels = {
            "no_delay": "No Delay",
            "one_step": "1-Step Delay",
            "two_step": "2-Step Delay",
        }
        symbols = {
            "no_delay": "x",
            "one_step": "x",
            "two_step": "x",
        }

        for key in ("no_delay", "one_step", "two_step"):
            pole_list = self._poles.get(key, [])
            real_parts = [p.real for p in pole_list]
            imag_parts = [p.imag for p in pole_list]
            magnitudes = [abs(p) for p in pole_list]
            hover_text = [
                f"{labels[key]}<br>z = {p.real:.3f} + {p.imag:.3f}j<br>|z| = {abs(p):.3f}"
                for p in pole_list
            ]

            traces.append({
                "x": real_parts,
                "y": imag_parts,
                "type": "scatter",
                "mode": "markers",
                "name": labels[key],
                "marker": {
                    "color": colors[key],
                    "size": 12,
                    "symbol": "x",
                    "line": {"color": colors[key], "width": 2},
                },
                "text": hover_text,
                "hoverinfo": "text",
            })

        fingerprint = f"poles-{KT}"
        return {
            "id": "pole_zero_map",
            "title": "Pole-Zero Map (z-plane)",
            "data": traces,
            "layout": {
                "xaxis": {
                    "title": {"text": "Re(z)", "font": {"color": "#f1f5f9", "size": 13}},
                    "gridcolor": "rgba(148,163,184,0.1)",
                    "zerolinecolor": "rgba(148,163,184,0.3)",
                    "zerolinewidth": 1,
                    "color": "#94a3b8",
                    "range": [-2, 2],
                    "constrain": "domain",
                },
                "yaxis": {
                    "title": {"text": "Im(z)", "font": {"color": "#f1f5f9", "size": 13}},
                    "gridcolor": "rgba(148,163,184,0.1)",
                    "zerolinecolor": "rgba(148,163,184,0.3)",
                    "zerolinewidth": 1,
                    "color": "#94a3b8",
                    "range": [-2, 2],
                    "constrain": "domain",
                },
                "paper_bgcolor": "rgba(0,0,0,0)",
                "plot_bgcolor": "rgba(0,0,0,0)",
                "font": {"family": "Inter, sans-serif", "size": 12, "color": "#f1f5f9"},
                "margin": {"t": 45, "r": 25, "b": 55, "l": 60},
                "showlegend": True,
                "legend": {
                    "font": {"color": "#94a3b8", "size": 11},
                    "bgcolor": "rgba(0,0,0,0)",
                },
                "datarevision": f"poles-{time.time()}",
                "uirevision": fingerprint,
            },
        }

    def get_state(self) -> Dict[str, Any]:
        if not self._positions:
            self._compute()

        state = super().get_state()

        KT = float(self.parameters["kt_product"])

        # Determine stability for each case
        def classify_poles(pole_list: List[complex]) -> Dict[str, Any]:
            max_mag = max(abs(p) for p in pole_list) if pole_list else 0
            if max_mag < 0.999:
                return {"status": "stable", "label": "Stable", "max_magnitude": round(max_mag, 4)}
            elif max_mag < 1.001:
                return {"status": "marginal", "label": "Marginally Stable", "max_magnitude": round(max_mag, 4)}
            else:
                return {"status": "unstable", "label": "Unstable", "max_magnitude": round(max_mag, 4)}

        stability = {
            key: classify_poles(self._poles.get(key, []))
            for key in ("no_delay", "one_step", "two_step")
        }

        # Pole data as serializable dicts
        poles_serialized = {}
        for key, pole_list in self._poles.items():
            poles_serialized[key] = [
                {"real": round(p.real, 6), "imag": round(p.imag, 6), "magnitude": round(abs(p), 6)}
                for p in pole_list
            ]

        state["metadata"] = {
            "simulation_type": "delay_instability",
            "hub_slots": self.HUB_SLOTS,
            "hub_domain": self.HUB_DOMAIN,
            "hub_dimensions": self.HUB_DIMENSIONS,
            "kt_product": KT,
            "positions": {k: v for k, v in self._positions.items()},
            "stability": stability,
            "poles": poles_serialized,
            "crash_step": self._crash_step,
            "animation_step": self._animation_step,
            "animation_active": self._animation_active,
            "num_steps": int(self.parameters["num_steps"]),
            "target_distance": float(self.parameters["target_distance"]),
            "initial_distance": float(self.parameters["initial_distance"]),
        }

        return state
