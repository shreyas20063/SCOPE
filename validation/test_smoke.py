"""Smoke test: verify pytest infrastructure is functional."""
import numpy as np
import pytest

from conftest import (
    ToleranceTier,
    assert_freq_response_equal,
    assert_poly_equal,
    assert_visual_equal,
)


def test_tolerance_tiers_defined():
    assert ToleranceTier.EXACT_RTOL == 1e-10
    assert ToleranceTier.LOOSE_RTOL == 1e-6
    assert ToleranceTier.VISUAL_RTOL == 1e-3


def test_assert_poly_equal_passes_for_equal():
    assert_poly_equal(np.array([1.0, 2.0]), np.array([1.0, 2.0]))


def test_assert_poly_equal_pads_shorter():
    assert_poly_equal(np.array([1.0, 2.0]), np.array([1.0, 2.0, 0.0]))


def test_assert_poly_equal_fails_for_unequal():
    with pytest.raises(AssertionError):
        assert_poly_equal(np.array([1.0, 2.0]), np.array([1.0, 3.0]))


def test_bdb_simulator_initializes(bdb_simulator):
    assert bdb_simulator is not None
    assert hasattr(bdb_simulator, '_pmul')
    assert hasattr(bdb_simulator, '_operator_to_s')
