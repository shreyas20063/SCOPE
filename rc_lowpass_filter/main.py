"""Entry point for the RC Lowpass Filter simulator."""

import sys
from PyQt5.QtWidgets import QApplication

from gui import RCFilterSimulator
from utils.constants import project_banner


def main() -> None:
    print(project_banner())

    app = QApplication(sys.argv)
    app.setApplicationName("RC Lowpass Filter Simulator")

    simulator = RCFilterSimulator()
    simulator.run()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
