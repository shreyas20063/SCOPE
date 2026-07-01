"""Regression tests for laplace_roc two_sided family (BUG-095).

Two-sided e^{-a|t|} (Oppenheim & Willsky, Signals and Systems, Table 9.2, a>0) is an
EVEN function. With symmetric poles at +/-a it must satisfy x(-t) == x(t) and have
H(s) = 1/(s+a) - 1/(s-a). Previously the left lobe was negative (the ODD signal
e^{-t}u(t) - e^{t}u(-t)) and H(s) printed 1/(s+a) + 1/(s-a).
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from simulations.laplace_roc import LaplaceROCSimulator


def _run(p1, p2):
    sim = LaplaceROCSimulator("laplace_roc")
    sim.initialize({"signal_family": "two_sided", "pole1_real": p1, "pole2_real": p2})
    return sim


def test_two_sided_symmetric_is_even_and_matches_exp_abs_t():
    sim = _run(-1.0, 1.0)
    t = np.asarray(sim._t, float)
    x = np.asarray(sim._x_t, float)
    for tt in (0.3, 0.7, 1.5, 2.5):
        ip = int(np.argmin(np.abs(t - tt)))
        im = int(np.argmin(np.abs(t + tt)))
        assert np.isclose(x[ip], x[im], atol=1e-6)      # x(-t) == x(t)
    assert np.allclose(x, np.exp(-np.abs(t)), atol=1e-6)  # equals e^{-|t|}


def test_two_sided_left_lobe_is_positive():
    # BUG-095: the left lobe used to be -e^{-|t|} (odd). e^{-a|t|} is non-negative.
    sim = _run(-1.0, 2.0)
    x = np.asarray(sim._x_t, float)
    assert np.all(x >= -1e-9)


def test_two_sided_hs_shows_difference():
    hs = _run(-1.0, 1.0)._format_hs()
    assert "-" in hs and hs.count("1/") == 2   # 1/(s+1) - 1/(s-1), not a sum
