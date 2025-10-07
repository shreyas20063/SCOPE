"""
Plotting helpers for the interactive RLC frequency response simulator.

Developed for the Signals and Systems (EE204T) course project under
Prof. Ameer Mulla by Duggimpudi Shreyas Reddy and Prathamesh Nerpagar.
"""

from __future__ import annotations

import numpy as np
from matplotlib.axes import Axes
from matplotlib.patches import Circle

from models.rlc_system import RLCSystemParameters, SystemCharacteristics


def plot_pole_zero(ax: Axes, poles: np.ndarray, omega_0: float) -> None:
    """Render the pole locations in the complex s-plane."""
    ax.clear()
    ax.set_title("Pole-Zero Map (s-plane)", fontweight="bold", fontsize=11, pad=10)
    ax.set_xlabel("Real (σ)", fontsize=10)
    ax.set_ylabel("Imaginary (ω)", fontsize=10)
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.axhline(y=0, color="k", linewidth=0.8)
    ax.axvline(x=0, color="k", linewidth=0.8)

    ax.set_xlim(-600, 50)
    ax.set_ylim(-120, 120)

    ax.fill_betweenx([-1000, 1000], -1000, 0, alpha=0.1, color="green", label="Stable region")

    plotted = False
    for pole in poles:
        if np.iscomplex(pole):
            ax.plot(
                pole.real,
                pole.imag,
                "rx",
                markersize=15,
                markeredgewidth=3,
                label="Poles" if not plotted else None,
                zorder=5,
            )
        else:
            ax.plot(
                pole,
                0,
                "rx",
                markersize=15,
                markeredgewidth=3,
                label="Poles" if not plotted else None,
                zorder=5,
            )
        plotted = True

    circle = Circle(
        (0, 0),
        omega_0,
        color="orange",
        fill=False,
        linestyle="--",
        linewidth=1.5,
        alpha=0.5,
        label=f"|ω₀| = {omega_0:.1f}",
    )
    ax.add_patch(circle)
    ax.legend(loc="upper left", fontsize=8, framealpha=0.9)
    ax.tick_params(axis="both", which="major", labelsize=9)


def display_system_info(
    ax: Axes,
    params: RLCSystemParameters,
    characteristics: SystemCharacteristics,
) -> None:
    """Draw textual summary of the current system configuration."""
    ax.clear()
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    info_text = "RLC Circuit Parameters:\n\n"
    info_text += f"Natural Frequency: ω₀ = {params.omega_0:.2f} rad/s\n"
    info_text += f"Quality Factor: Q = {params.Q:.2f}\n"
    info_text += f"Damping Ratio: ζ = {characteristics.zeta:.3f}\n\n"
    info_text += f"System Type:\n{characteristics.damping_type}\n\n"

    poles = characteristics.poles
    if np.iscomplex(poles[0]):
        info_text += (
            f"Poles: s = {poles[0].real:.2f} ± {abs(poles[0].imag):.2f}j\n"
            f"Pole magnitude: |p| = {abs(poles[0]):.2f}\n"
        )
    else:
        info_text += f"Poles: s₁ = {poles[0]:.2f}, s₂ = {poles[1]:.2f}\n"

    if characteristics.resonant_frequency is not None:
        info_text += (
            f"\nResonant Frequency: ωᵣ = {characteristics.resonant_frequency:.2f} rad/s\n"
        )

    info_text += f"3dB Bandwidth: Δω ≈ {characteristics.bandwidth:.2f} rad/s"

    ax.text(
        0.05,
        0.95,
        info_text,
        ha="left",
        va="top",
        fontsize=9,
        bbox=dict(
            boxstyle="round",
            facecolor="lightblue",
            edgecolor="blue",
            linewidth=2,
            pad=0.8,
        ),
        family="monospace",
    )


def plot_bode(
    ax_mag: Axes,
    ax_phase: Axes,
    omega: np.ndarray,
    response: np.ndarray,
    params: RLCSystemParameters,
) -> None:
    """Render the Bode magnitude and phase plots."""
    ax_mag.clear()
    ax_mag.set_title("Bode Plot - Magnitude", fontweight="bold", fontsize=11, pad=10)
    ax_mag.set_xlabel("Frequency (rad/s)", fontsize=10)
    ax_mag.set_ylabel("Magnitude (dB)", fontsize=10)
    ax_mag.grid(True, alpha=0.3, which="both", linestyle="--")
    ax_mag.set_xscale("log")

    magnitude_db = 20 * np.log10(np.abs(response))
    ax_mag.semilogx(omega, magnitude_db, "b-", linewidth=2.5, label="|H(jω)|")

    ax_mag.set_xlim(0.1, 10000)
    ax_mag.set_ylim(-80, 40)

    ax_mag.axvline(
        x=params.omega_0,
        color="r",
        linestyle="--",
        linewidth=1.5,
        alpha=0.7,
        label=f"ω₀ = {params.omega_0:.1f}",
    )
    ax_mag.axhline(y=0, color="gray", linestyle=":", linewidth=1, alpha=0.5)

    if params.Q > 0.707:
        peak_db = 20 * np.log10(params.Q / np.sqrt(1.0 - 1.0 / (2.0 * params.Q) ** 2))
        ax_mag.axhline(
            y=peak_db - 3.0,
            color="g",
            linestyle=":",
            linewidth=1.5,
            alpha=0.7,
            label="-3dB from peak",
        )

    ax_mag.legend(loc="upper right", fontsize=8, framealpha=0.9)
    ax_mag.tick_params(axis="both", which="major", labelsize=9)

    ax_phase.clear()
    ax_phase.set_title("Bode Plot - Phase", fontweight="bold", fontsize=11, pad=10)
    ax_phase.set_xlabel("Frequency (rad/s)", fontsize=10)
    ax_phase.set_ylabel("Phase (degrees)", fontsize=10)
    ax_phase.grid(True, alpha=0.3, which="both", linestyle="--")
    ax_phase.set_xscale("log")

    phase_deg = np.angle(response, deg=True)
    ax_phase.semilogx(omega, phase_deg, "b-", linewidth=2.5, label="∠H(jω)")

    ax_phase.set_xlim(0.1, 10000)
    ax_phase.set_ylim(-200, 10)

    ax_phase.axvline(
        x=params.omega_0,
        color="r",
        linestyle="--",
        linewidth=1.5,
        alpha=0.7,
        label=f"ω₀ = {params.omega_0:.1f}",
    )
    ax_phase.axhline(y=0, color="gray", linestyle=":", linewidth=1, alpha=0.5)
    ax_phase.axhline(y=-90, color="gray", linestyle=":", linewidth=1, alpha=0.5, label="-90°")
    ax_phase.axhline(y=-180, color="gray", linestyle=":", linewidth=1, alpha=0.5)

    ax_phase.legend(loc="upper right", fontsize=8, framealpha=0.9)
    ax_phase.tick_params(axis="both", which="major", labelsize=9)
