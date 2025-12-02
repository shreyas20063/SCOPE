import traceback
from typing import List
from PyQt5 import QtCore, QtGui, QtWidgets

from styles import COLORS
from components import CardWidget
from demos.base import DemoWindowBase
from demos.am import DemoWindowAM
from demos.fm import DemoWindowFM
from demos.fdm import DemoWindowFDM

class ModulationLab(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Modulation Techniques Simulator")
        self.resize(1280, 860)
        central = QtWidgets.QWidget()
        central.setStyleSheet(f"background-color:{COLORS['bg']}")
        self.setCentralWidget(central)
        self._child_windows: List[QtWidgets.QWidget] = []

        layout = QtWidgets.QVBoxLayout(central)
        title = QtWidgets.QLabel("Modulation Techniques Simulator")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setFont(QtGui.QFont("Inter", 26, QtGui.QFont.Bold))
        title.setStyleSheet(f"color:{COLORS['text_primary']}")
        layout.addWidget(title)

        cards_layout = QtWidgets.QHBoxLayout()
        cards_layout.setSpacing(18)
        layout.addLayout(cards_layout)

        cards = [
            (
                "Amplitude Modulation",
                "Explore DSB-SC, AM with carrier, envelope detection, and recovered audio.",
                COLORS["accent"],
                self.launch_am_demo,
            ),
            (
                "Frequency & Phase Modulation",
                "Visualize FM/PM instant frequency, Carson bandwidth, and recovered signal.",
                COLORS["success"],
                self.launch_fm_demo,
            ),
            (
                "Frequency Division Multiplexing",
                "Experiment with arbitrary channel counts, spacing, and demodulated outputs.",
                COLORS["warning"],
                self.launch_fdm_demo,
            ),
        ]
        for title_text, desc, color, callback in cards:
            card = CardWidget(title_text, desc, color, callback)
            cards_layout.addWidget(card)

        status_frame = QtWidgets.QFrame()
        status_layout = QtWidgets.QHBoxLayout(status_frame)
        status_layout.addStretch(1)
        self.status_label = QtWidgets.QLabel("[Ready]")
        self.status_label.setStyleSheet(f"color:{COLORS['success']}; font-weight:600;")
        status_layout.addWidget(self.status_label)
        layout.addWidget(status_frame)

    def _register_child(self, window: QtWidgets.QWidget) -> None:
        self._child_windows.append(window)
        window.destroyed.connect(lambda _=None, w=window: self._child_windows.remove(w) if w in self._child_windows else None)

    def update_status(self, message: str, level: str = "success") -> None:
        color_map = {
            "success": COLORS["success"],
            "info": COLORS["accent"],
            "warning": COLORS["warning"],
            "danger": COLORS["danger"],
        }
        icon_map = {
            "success": "[OK]",
            "info": "[i]",
            "warning": "[!]",
            "danger": "[x]",
        }
        icon = icon_map.get(level, "")
        self.status_label.setText(f"{icon} {message}")
        self.status_label.setStyleSheet(f"color:{color_map.get(level, COLORS['text_primary'])}; font-weight:600;")

    def _launch_demo(self, cls: type[DemoWindowBase], title: str) -> None:
        try:
            self.update_status(f"Opening {title}...", "info")
            window = cls(self, title)
            window.show()
            self._register_child(window)
            self.update_status("Demo ready", "success")
        except Exception as exc:
            self.update_status("Failed to launch demo", "danger")
            QtWidgets.QMessageBox.critical(self, "Error", f"Could not launch demo: {exc}")
            traceback.print_exc()

    def launch_am_demo(self) -> None:
        self._launch_demo(DemoWindowAM, "Amplitude Modulation")

    def launch_fm_demo(self) -> None:
        self._launch_demo(DemoWindowFM, "Frequency & Phase Modulation")

    def launch_fdm_demo(self) -> None:
        self._launch_demo(DemoWindowFDM, "Frequency Division Multiplexing")