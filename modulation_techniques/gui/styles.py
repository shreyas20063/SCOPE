from PyQt5 import QtCore, QtWidgets

COLORS = {
    "bg": "#F9FAFB",
    "panel": "#FFFFFF",
    "accent": "#2563EB",
    "accent_dark": "#1D4ED8",
    "success": "#16A34A",
    "warning": "#CA8A04",
    "danger": "#DC2626",
    "text_primary": "#0F172A",
    "text_secondary": "#475569",
    "grid": "#D1D5DB",
}

BUTTON_STYLE = (
    "QPushButton {{background-color:{color}; color:white; border:none; border-radius:6px;"
    "padding:8px 18px; font-weight:600;}}"
    "QPushButton:disabled {{background-color:{color}; color:#E5E7EB; opacity:0.45;}}"
)

SLIDER_STYLE = """
QSlider::groove:horizontal {
    border: 0px;
    height: 6px;
    margin: 0px;
    border-radius: 3px;
    background: #CBD5F5;
}
QSlider::sub-page:horizontal {
    background: #4C6EF5;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #2563EB;
    border: none;
    width: 16px;
    margin: -6px 0;
    border-radius: 8px;
}
"""

SPIN_STYLE = (
    "QSpinBox, QDoubleSpinBox {background-color:#FFFFFF; border:1px solid #CBD5F5;"
    "border-radius:6px; padding:4px 8px; font-weight:600; color:#0F172A; min-height:30px;}"
)

VALUE_LABEL_STYLE = "color:#1D4ED8; font-weight:700;"

def style_slider(slider: QtWidgets.QSlider) -> None:
    slider.setStyleSheet(SLIDER_STYLE)
    slider.setCursor(QtCore.Qt.PointingHandCursor)

def style_spinbox(spin: QtWidgets.QAbstractSpinBox) -> None:
    spin.setStyleSheet(SPIN_STYLE)
    spin.setButtonSymbols(QtWidgets.QAbstractSpinBox.PlusMinus)

def style_button(button: QtWidgets.QPushButton, color: str) -> None:
    button.setCursor(QtCore.Qt.PointingHandCursor)
    button.setStyleSheet(BUTTON_STYLE.format(color=color))

def make_label(text: str, *, bold: bool = False, secondary: bool = False) -> QtWidgets.QLabel:
    label = QtWidgets.QLabel(text)
    color = COLORS["text_secondary"] if secondary else COLORS["text_primary"]
    weight = "600" if bold else "500"
    label.setStyleSheet(f"color:{color}; font-weight:{weight};")
    return label