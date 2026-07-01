"""Regression tests for signal_operations' formula label (BUG-097).

With time_reverse=True, time_scale=a not in {0, 1, -1}, and time_shift=0, the
label concatenated "{a}{-t}" and rendered "f(2-t)" (reads as 2 minus t) while
the compute chain g(t) = A*f(a*(-t - t0)) + dc actually plots f(-2t). The
shipped "Compress + Reverse" preset (scale=2, reverse, shift=0) hit this
directly. The label must fold the reversal sign into the coefficient: f(-2t).
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from simulations.signal_operations import SignalOperationsSimulator


F = SignalOperationsSimulator._build_formula


def test_reverse_scale_label_folds_sign():
    assert F(1.0, 2.0, 0.0, True, 0.0) == "f(-2t)"      # was "f(2-t)"
    assert F(1.0, 0.5, 0.0, True, 0.0) == "f(-0.5t)"    # was "f(0.5-t)"
    assert F(1.0, -2.0, 0.0, True, 0.0) == "f(2t)"      # was "f(-2-t)"


def test_unaffected_branches_unchanged():
    assert F(1.0, 2.0, 0.0, False, 0.0) == "f(2t)"
    assert F(1.0, 2.0, 1.0, True, 0.0) == "f(2(-t - 1))"
    assert F(1.0, 1.0, 0.0, True, 0.0) == "f(-t)"
    assert F(1.0, -1.0, 0.0, True, 0.0) == "f(t)"
    assert F(2.0, 2.0, 0.0, False, 1.0) == "2 · f(2t) + 1"


def test_plotted_signal_matches_labeled_transform():
    # Asymmetric signal (right-sided exponential decay): f(-2t) is left-sided,
    # while the old label's meaning f(2-t) is a shifted reversal — they differ
    # grossly, so this pins the plot to the (fixed) label's meaning.
    sim = SignalOperationsSimulator("signal_operations")
    sim.initialize({
        "signal_type": "exponential_decay",
        "time_scale": 2.0,
        "time_reverse": True,
        "time_shift": 0.0,
    })
    assert "f(-2t)" in sim._formula

    t = sim._t
    f = lambda x: sim._generate_signal("exponential_decay", sim.parameters["frequency"], x)
    assert np.allclose(sim._transformed, f(-2.0 * t))          # matches the label
    assert not np.allclose(sim._transformed, f(2.0 - t))       # NOT the old label's meaning
