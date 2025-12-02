from PyQt5 import QtCore, QtGui, QtWidgets
from typing import Callable
from styles import COLORS

class CardWidget(QtWidgets.QFrame):
    def __init__(self, title: str, description: str, color: str, callback: Callable[[], None]):
        super().__init__()
        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setStyleSheet(
            f"background-color:{COLORS['panel']}; border:1px solid {COLORS['grid']};"
            "border-radius:12px;"
        )
        layout = QtWidgets.QVBoxLayout(self)
        title_lbl = QtWidgets.QLabel(title)
        title_lbl.setFont(QtGui.QFont("Inter", 18, QtGui.QFont.Bold))
        title_lbl.setStyleSheet(f"color:{COLORS['text_primary']}")
        desc_lbl = QtWidgets.QLabel(description)
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:13px;")
        button = QtWidgets.QPushButton("Launch Demo")
        button.setCursor(QtCore.Qt.PointingHandCursor)
        button.setStyleSheet(
            f"background-color:{color}; color:white; border:none; border-radius:6px;"
            "padding:10px 18px; font-weight:600;"
        )
        button.clicked.connect(callback)
        layout.addWidget(title_lbl)
        layout.addWidget(desc_lbl)
        layout.addStretch(1)
        layout.addWidget(button, alignment=QtCore.Qt.AlignRight)