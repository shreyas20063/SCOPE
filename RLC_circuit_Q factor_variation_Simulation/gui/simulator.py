"""
Interactive GUI controller for the RLC frequency response simulator.

Developed for the Signals and Systems (EE204T) course project under
Prof. Ameer Mulla by Duggimpudi Shreyas Reddy and Prathamesh Nerpagar.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.widgets import Slider

from models.rlc_system import (
    RLCSystemParameters,
    analyze_system,
    frequency_response,
)
from plotting.visuals import display_system_info, plot_bode, plot_pole_zero


class RLCFrequencyResponseSimulator:
    """Facade that wires together the model computations and plotting helpers."""

    def __init__(self) -> None:
        plt.rcParams["figure.dpi"] = 100
        self.params = RLCSystemParameters()
        self._build_figure()
        self._connect_events()
        self.update_plot()

    def _build_figure(self) -> None:
        """Initialise the Matplotlib figure, axes, and UI controls."""
        self.fig = plt.figure(
            "RLC Frequency Response Simulator", figsize=(16, 10), constrained_layout=False
        )
        self.fig.suptitle(
            "Second-Order System: Effect of Q on Frequency Response",
            fontsize=14,
            fontweight="bold",
        )

        grid = GridSpec(
            3,
            2,
            figure=self.fig,
            left=0.08,
            right=0.96,
            top=0.92,
            bottom=0.15,
            hspace=0.40,
            wspace=0.35,
        )

        self.ax_poles = self.fig.add_subplot(grid[0, 0])
        self.ax_info = self.fig.add_subplot(grid[0, 1])
        self.ax_mag = self.fig.add_subplot(grid[1, :])
        self.ax_phase = self.fig.add_subplot(grid[2, :])

        slider_color = "lightblue"
        omega_ax = self.fig.add_axes([0.15, 0.06, 0.3, 0.025], facecolor=slider_color)
        self.slider_omega = Slider(
            omega_ax,
            "ω₀ (Natural Freq)",
            1.0,
            100.0,
            valinit=self.params.omega_0,
            valstep=0.5,
            color="steelblue",
        )

        q_ax = self.fig.add_axes([0.6, 0.06, 0.3, 0.025], facecolor=slider_color)
        self.slider_q = Slider(
            q_ax,
            "Q (Quality Factor)",
            0.1,
            20.0,
            valinit=self.params.Q,
            valstep=0.1,
            color="steelblue",
        )

    def _connect_events(self) -> None:
        """Bind UI callbacks."""
        self.slider_omega.on_changed(self._update_omega)
        self.slider_q.on_changed(self._update_q)
        self.fig.canvas.mpl_connect("draw_event", self._on_draw)

    def _update_omega(self, value: float) -> None:
        self.params.omega_0 = float(value)
        self.update_plot()

    def _update_q(self, value: float) -> None:
        self.params.Q = float(value)
        self.update_plot()

    def update_plot(self) -> None:
        """Refresh every panel based on the current parameters."""
        characteristics = analyze_system(self.params)
        omega, response = frequency_response(characteristics.transfer_function)

        plot_pole_zero(self.ax_poles, characteristics.poles, self.params.omega_0)
        display_system_info(self.ax_info, self.params, characteristics)
        plot_bode(self.ax_mag, self.ax_phase, omega, response, self.params)

        self.fig.canvas.draw_idle()

    def _on_draw(self, _event) -> None:
        """Placeholder hook retained for future layout tweaks."""
        return


def launch_simulator() -> None:
    """Entry point used by the CLI runner."""
    simulator = RLCFrequencyResponseSimulator()
    plt.show()
