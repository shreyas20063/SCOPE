"""
Shared pytest configuration and fixtures for the SCOPE validation suite.

Provides:
- sys.path setup for importing backend modules
- ToleranceTier class with three precision levels
- Assertion helpers: assert_poly_equal, assert_freq_response_equal, assert_visual_equal
- bdb_simulator fixture for BlockDiagramSimulator
"""

import sys
from pathlib import Path

import numpy as np
import pytest
from numpy.testing import assert_allclose

# ---------------------------------------------------------------------------
# Path setup -- add backend to sys.path so simulators can be imported
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
VALIDATION_DIR = PROJECT_ROOT / "validation"
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(VALIDATION_DIR))


# ---------------------------------------------------------------------------
# Tolerance tiers
# ---------------------------------------------------------------------------
class ToleranceTier:
    """Tolerance presets for validation contexts.

    Three tiers reflecting the precision expected at each computation stage:
      - EXACT: polynomial coefficient math (convolution, addition)
      - LOOSE: frequency response, pole/zero locations
      - VISUAL: plot data, step response values
    """
    # Tier 1: Exact -- polynomial coefficient math
    EXACT_RTOL = 1e-10
    EXACT_ATOL = 1e-12
    # Tier 2: Loose -- frequency response, pole/zero locations
    LOOSE_RTOL = 1e-6
    LOOSE_ATOL = 1e-8
    # Tier 3: Visual -- plot data, step response values
    VISUAL_RTOL = 1e-3
    VISUAL_ATOL = 1e-4


# ---------------------------------------------------------------------------
# Assertion helpers
# ---------------------------------------------------------------------------
def assert_poly_equal(actual, expected, msg=""):
    """Assert two polynomial coefficient arrays are equal (EXACT tier).

    Pads the shorter array with trailing zeros before comparison,
    since [1, 2] and [1, 2, 0] represent the same polynomial.
    """
    actual = np.asarray(actual, dtype=float)
    expected = np.asarray(expected, dtype=float)
    # Pad shorter to match longer
    n = max(len(actual), len(expected))
    a = np.zeros(n)
    e = np.zeros(n)
    a[:len(actual)] = actual
    e[:len(expected)] = expected
    assert_allclose(
        a, e,
        rtol=ToleranceTier.EXACT_RTOL,
        atol=ToleranceTier.EXACT_ATOL,
        err_msg=msg or "Polynomial coefficients not equal (EXACT tier)",
    )


def assert_freq_response_equal(actual, expected, msg=""):
    """Assert two frequency response arrays are equal (LOOSE tier)."""
    actual = np.asarray(actual, dtype=complex)
    expected = np.asarray(expected, dtype=complex)
    assert_allclose(
        actual, expected,
        rtol=ToleranceTier.LOOSE_RTOL,
        atol=ToleranceTier.LOOSE_ATOL,
        err_msg=msg or "Frequency response not equal (LOOSE tier)",
    )


def assert_visual_equal(actual, expected, msg=""):
    """Assert two arrays are equal (VISUAL tier)."""
    actual = np.asarray(actual, dtype=float)
    expected = np.asarray(expected, dtype=float)
    assert_allclose(
        actual, expected,
        rtol=ToleranceTier.VISUAL_RTOL,
        atol=ToleranceTier.VISUAL_ATOL,
        err_msg=msg or "Values not equal (VISUAL tier)",
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def bdb_simulator():
    """Create a fresh BlockDiagramSimulator instance."""
    from simulations.block_diagram_builder import BlockDiagramSimulator
    sim = BlockDiagramSimulator("block_diagram_builder")
    sim.initialize()
    return sim
