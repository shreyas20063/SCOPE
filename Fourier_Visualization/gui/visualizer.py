"""Matplotlib-based GUI for exploring Fourier series approximations."""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
import matplotlib.gridspec as gridspec

from core.series import describe_series, fourier_series
from core.waveforms import (
    square_wave,
    triangle_wave,
    square_wave_harmonic,
    triangle_wave_harmonic,
)


class FourierSeriesVisualizer:
    """Interactive Fourier series visualizer with a modern theme."""

    def __init__(self) -> None:
        self.colors = {
            "bg": "#f8fafc",
            "fig_bg": "#ffffff",
            "panel": "#f0fdf4",
            "panel_border": "#86efac",
            "text": "#1e293b",
            "text_muted": "#64748b",
            "accent": "#22c55e",
            "original": "#ef4444",
            "fourier": "#3b82f6",
            "grid": "#e2e8f0",
        }
        plt.rcParams["font.family"] = "STIXGeneral"
        plt.rcParams["mathtext.fontset"] = "stix"

        self.fig = plt.figure(figsize=(14, 8), facecolor=self.colors["fig_bg"])

        layout = gridspec.GridSpec(
            2,
            2,
            figure=self.fig,
            left=0.10,
            right=0.95,
            top=0.93,
            bottom=0.20,
            width_ratios=[3, 1],
            height_ratios=[1.3, 1],
            hspace=0.30,
            wspace=0.15,
        )

        self.ax_main = self.fig.add_subplot(layout[0, 0])
        self.ax_harmonics = self.fig.add_subplot(layout[1, 0], sharex=self.ax_main)
        self.ax_controls = self.fig.add_subplot(layout[:, 1])
        self.ax_slider = self.fig.add_axes([0.10, 0.04, 0.64, 0.03])

        self.fig.suptitle(
            "Interactive Fourier Series Visualization",
            fontsize=20,
            color=self.colors["text"],
            y=0.97,
            weight="bold",
        )

        for ax in [self.ax_main, self.ax_harmonics, self.ax_slider]:
            ax.set_facecolor(self.colors["fig_bg"])

        self.ax_controls.set_facecolor(self.colors["panel"])
        self.ax_controls.tick_params(axis="both", which="both", length=0)
        self.ax_controls.set_xticklabels([])
        self.ax_controls.set_yticklabels([])
        for spine in self.ax_controls.spines.values():
            spine.set_edgecolor(self.colors["panel_border"])
            spine.set_linewidth(2)

        self.t = np.linspace(0, 2, 3000)
        self.max_harmonics = 50
        self.current_harmonics = 1
        self.wave_type: str = "Square Wave"

        self.button_ax1 = self.ax_controls.inset_axes([0.1, 0.82, 0.35, 0.05])
        self.button_ax2 = self.ax_controls.inset_axes([0.55, 0.82, 0.35, 0.05])
        self.button1 = Button(self.button_ax1, "Square Wave")
        self.button2 = Button(self.button_ax2, "Triangle Wave")
        self.button1.label.set_fontsize(10)
        self.button2.label.set_fontsize(10)
        self.button1.on_clicked(lambda _: self.change_wave_type("Square Wave"))
        self.button2.on_clicked(lambda _: self.change_wave_type("Triangle Wave"))

        self.create_controls()
        self.update_display(self.slider.val)

    def create_controls(self) -> None:
        """Configure the global slider control."""
        self.slider = Slider(
            ax=self.ax_slider,
            label="harmonics(n)",
            valmin=1,
            valmax=self.max_harmonics,
            valinit=1,
            valstep=1,
            color=self.colors["accent"],
        )
        self.slider.label.set_color(self.colors["text"])
        self.slider.label.set_fontsize(12)
        self.slider.valtext.set_color(self.colors["text"])
        self.slider.valtext.set_fontsize(11)
        self.slider.on_changed(self.update_display)

    def update_button_styles(self) -> None:
        """Highlight the active waveform button."""
        if self.wave_type == "Square Wave":
            self.button_ax1.set_facecolor(self.colors["accent"])
            self.button1.label.set_color("white")
            self.button1.label.set_weight("bold")
            self.button_ax2.set_facecolor(self.colors["bg"])
            self.button2.label.set_color(self.colors["text"])
            self.button2.label.set_weight("normal")
        else:
            self.button_ax2.set_facecolor(self.colors["accent"])
            self.button2.label.set_color("white")
            self.button2.label.set_weight("bold")
            self.button_ax1.set_facecolor(self.colors["bg"])
            self.button1.label.set_color(self.colors["text"])
            self.button1.label.set_weight("normal")

    def change_wave_type(self, wave_type: str) -> None:
        """Switch the source waveform and refresh the plots."""
        self.wave_type = wave_type
        self.update_display(self.current_harmonics)

    def update_display(self, val: float) -> None:
        """Redraw the plots and informational panel when the slider changes."""
        del val  # Slider callback passes value, but we query slider directly
        n = int(self.slider.val)
        self.current_harmonics = n

        self.ax_main.clear()
        self.ax_harmonics.clear()

        for txt in self.ax_controls.texts[:]:
            txt.remove()

        for ax in [self.ax_main, self.ax_harmonics]:
            ax.set_facecolor(self.colors["fig_bg"])
            ax.grid(True, color=self.colors["grid"], linestyle="--", linewidth=0.6, alpha=0.9)
            ax.tick_params(axis="both", colors=self.colors["text_muted"], labelsize=11)
            for spine in ["left", "bottom"]:
                ax.spines[spine].set_color(self.colors["text_muted"])
            for spine in ["right", "top"]:
                ax.spines[spine].set_visible(False)

        self.update_button_styles()

        if self.wave_type == "Square Wave":
            original = square_wave(self.t)
            harmonic_fn = square_wave_harmonic
        else:
            original = triangle_wave(self.t)
            harmonic_fn = triangle_wave_harmonic

        approximation = fourier_series(self.t, n, self.wave_type)

        self.ax_main.set_xlim(0, 2)
        self.ax_main.set_ylim(-1.5, 1.5)
        self.ax_main.tick_params(axis="x", labelbottom=False)
        self.ax_main.set_ylabel("Amplitude", fontsize=13, color=self.colors["text"])
        self.ax_main.plot(self.t, original, color=self.colors["original"], lw=2.3, label="Original Wave")
        self.ax_main.plot(
            self.t,
            approximation,
            color=self.colors["fourier"],
            lw=2.5,
            label=f"Fourier Series (n={n})",
        )
        legend = self.ax_main.legend(loc="upper right", fontsize=11, fancybox=True, framealpha=0.7)
        legend.get_frame().set_facecolor(self.colors["panel"])
        legend.get_frame().set_edgecolor(self.colors["panel_border"])
        for text in legend.get_texts():
            text.set_color(self.colors["text"])

        self.ax_harmonics.set_ylim(-1.4, 1.4)
        self.ax_harmonics.set_xlabel("Time (periods)", fontsize=13, color=self.colors["text"])
        self.ax_harmonics.set_ylabel("Amplitude", fontsize=13, color=self.colors["text"])

        colors = plt.cm.viridis(np.linspace(0, 1, n))
        for k in range(1, n + 1):
            harmonic = harmonic_fn(self.t, k)
            self.ax_harmonics.plot(self.t, harmonic, color=colors[k - 1], alpha=0.9, lw=1.3)

        self.ax_controls.text(
            0.5,
            0.95,
            "Control Panel",
            ha="center",
            va="top",
            fontsize=17,
            color=self.colors["text"],
            weight="bold",
        )
        self.ax_controls.text(
            0.5,
            0.73,
            "Fourier Series Formula",
            ha="center",
            va="top",
            fontsize=13,
            color=self.colors["text_muted"],
            weight="bold",
        )

        formula_main, expanded, properties = describe_series(n, self.wave_type)

        self.ax_controls.text(
            0.5,
            0.65,
            formula_main,
            ha="center",
            va="center",
            fontsize=11,
            color=self.colors["text"],
        )
        self.ax_controls.text(
            0.5,
            0.55,
            expanded,
            ha="center",
            va="center",
            fontsize=8.5,
            color=self.colors["text"],
        )
        self.ax_controls.text(
            0.5,
            0.45,
            properties,
            ha="center",
            va="center",
            fontsize=9,
            style="italic",
            color=self.colors["text_muted"],
        )

        mse = np.mean((original - approximation) ** 2)
        max_error = np.max(np.abs(original - approximation))
        info_text = (
            r"$\mathbf{{Analysis}}$"
            + "\n\n"
            + f"Wave Type: {self.wave_type}\n"
            + f"Harmonics: $n = {n}$\n\n"
            + r"$\mathbf{{Error~Metrics}}$"
            + "\n\n"
            + f"Mean Squared Error:\n${mse:.5f}$\n\n"
            + f"Max Absolute Error:\n${max_error:.4f}$"
        )

        self.ax_controls.text(
            0.5,
            0.23,
            info_text,
            ha="center",
            va="center",
            fontsize=11,
            color=self.colors["text"],
            bbox=dict(
                boxstyle="round,pad=0.7",
                fc=self.colors["bg"],
                ec=self.colors["panel_border"],
                lw=2,
            ),
        )

        self.fig.canvas.draw_idle()

    def show(self) -> None:
        """Block until the visualization window is closed."""
        plt.show()
