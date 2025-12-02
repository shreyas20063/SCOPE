#!/usr/bin/env python3
import os
import sys
import platform
import numpy as np
from PyQt5 import QtWidgets
from mainwindow import ModulationLab

# Suppress numpy warnings
np.seterr(all="ignore")

# Platform specific optimization settings
if platform.system() == "Darwin":
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    os.environ.setdefault("MKL_NUM_THREADS", "1")
    os.environ.setdefault("VECLIB_MAXIMUM_THREADS", "1")
    os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

def main() -> int:
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    window = ModulationLab()
    window.show()
    return app.exec_()

if __name__ == "__main__":
    sys.exit(main())