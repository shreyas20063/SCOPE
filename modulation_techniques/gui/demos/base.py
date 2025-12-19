import warnings
import numpy as np
from PyQt5 import QtCore, QtWidgets
from gui.styles import COLORS

# Matplotlib imports
import matplotlib
matplotlib.use("Qt5Agg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar,
)

# Audio Backend
try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except Exception:
    sd = None
    SOUNDDEVICE_AVAILABLE = False
    warnings.warn(
        "sounddevice is not available; playback buttons will be disabled.",
        RuntimeWarning,
        stacklevel=0,
    )

class DemoWindowBase(QtWidgets.QWidget):
    update_delay_ms = 40

    def __init__(self, parent: QtWidgets.QWidget | None, title: str):
        super().__init__(parent, QtCore.Qt.Window)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle(title)
        self.setAutoFillBackground(True)
        self.setStyleSheet(f"background-color:{COLORS['bg']}")
        self.resize(1180, 820)
        self.original_sr: int = 0
        self.audio = np.zeros(1, dtype=np.float64)
        self.time = np.zeros(1, dtype=np.float64)
        self._update_pending = False
        self._is_updating = False

    def schedule_update(self) -> None:
        if self._update_pending:
            return
        self._update_pending = True
        QtCore.QTimer.singleShot(self.update_delay_ms, self._trigger_update)

    def _trigger_update(self) -> None:
        self._update_pending = False
        self.update_plot()

    def update_plot(self) -> None:
        raise NotImplementedError

    def _play_buffer(self, buffer: np.ndarray, gain: float = 1.0) -> None:
        if not SOUNDDEVICE_AVAILABLE:
            QtWidgets.QMessageBox.warning(self, "Playback unavailable", "sounddevice module is missing.")
            return
        if self.original_sr <= 0 or buffer.size == 0:
            return
        sd.stop()
        norm = buffer / (np.max(np.abs(buffer)) + 1e-10)
        sd.play((norm * gain).astype(np.float32), int(self.original_sr))

    def stop_audio(self) -> None:
        if SOUNDDEVICE_AVAILABLE:
            sd.stop()