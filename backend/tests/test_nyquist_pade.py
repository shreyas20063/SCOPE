"""Regression tests for nyquist_stability's Padé delay approximation (BUG-096).

_build_pade had an extra 1/k! factor in the coefficient formula. Magnitude is
all-pass (~1) so Bode |H| looked fine, but the phase lagged the true delay
e^{-sT} (-121.5 deg vs -143 deg at wT=2.5), corrupting the time_delay preset's
delay-induced-instability demonstration. The fixed coefficients must match the
standard Padé[n/n] of e^{-x} (as implemented independently by python-control).
"""
import os
import sys

import control
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from simulations.nyquist_stability import NyquistStabilitySimulator


def test_pade_matches_python_control():
    for order in (1, 2, 3, 4):
        num, den = NyquistStabilitySimulator._build_pade(1.0, order)
        onum, oden = control.pade(1.0, order)
        num, den = np.asarray(num, float), np.asarray(den, float)
        onum, oden = np.asarray(onum, float), np.asarray(oden, float)
        assert np.allclose(num / den[0], onum / oden[0], rtol=1e-12)
        assert np.allclose(den / den[0], oden / oden[0], rtol=1e-12)


def test_pade_phase_tracks_ideal_delay():
    # Padé[3/3] should track the ideal phase -wT to within ~1 deg for wT <= 2.5
    num, den = NyquistStabilitySimulator._build_pade(1.0, 3)
    for w in (0.5, 1.0, 2.0, 2.5):
        h = np.polyval(num, 1j * w) / np.polyval(den, 1j * w)
        assert abs(np.degrees(np.angle(h)) - np.degrees(-w)) < 1.0
        assert abs(abs(h) - 1.0) < 1e-9  # all-pass


def test_time_delay_preset_margin_matches_oracle():
    # L(s) = K e^{-sT}/(s+a) with the preset defaults (K=1, a=1, T=0.5):
    # the sim's reported gain margin must match python-control's margin().
    sim = NyquistStabilitySimulator("nyquist_stability")
    sim.initialize({"preset": "time_delay"})
    gm_sim = sim.get_state()["metadata"]["stability_info"]["gain_margin_db"]

    pn, pd = control.pade(0.5, 3)
    L = control.tf(pn, pd) * control.tf([1.0], [1.0, 1.0])
    gm, _, _, _ = control.margin(L)
    assert abs(gm_sim - 20 * np.log10(gm)) < 0.05
