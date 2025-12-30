"""GUI components for modulation simulator."""

from .mainwindow import ModulationLab
from .components import CardWidget
from .styles import (
    COLORS,
    BUTTON_STYLE,
    SLIDER_STYLE,
    SPIN_STYLE,
    VALUE_LABEL_STYLE,
    style_slider,
    style_spinbox,
    style_button,
    make_label,
)

__all__ = [
    "ModulationLab",
    "CardWidget",
    "COLORS",
    "BUTTON_STYLE",
    "SLIDER_STYLE",
    "SPIN_STYLE",
    "VALUE_LABEL_STYLE",
    "style_slider",
    "style_spinbox",
    "style_button",
    "make_label",
]
