"""
Tests for polynomial arithmetic helpers in BlockDiagramSimulator.

All polynomial operations use LOW-POWER-FIRST convention:
  coeffs[i] = coefficient of x^i
  e.g., [1, -0.5] represents 1 - 0.5x

Covers: _pmul, _padd, _psub, _pscale (static methods), _clean_poly (instance method).

Requirements: TEST-01 (edge cases), TEST-06 (tolerance tiers from conftest).
"""

import numpy as np
import pytest
from conftest import assert_poly_equal, ToleranceTier
from simulations.block_diagram_builder import BlockDiagramSimulator


# ---------------------------------------------------------------------------
# _pmul tests
# ---------------------------------------------------------------------------
class TestPmul:
    """Polynomial multiplication (np.convolve, low-power-first)."""

    @pytest.mark.parametrize("a, b, expected", [
        # unity * unity = [1]
        ([1.0], [1.0], [1.0]),
        # poly * unity = poly
        ([1.0, 2.0], [1.0], [1.0, 2.0]),
        # zero * poly = zeros (np.convolve pads with zeros)
        ([0.0], [1.0, 2.0, 3.0], [0.0, 0.0, 0.0]),
        # binomial squared: (1 + x)^2 = 1 + 2x + x^2
        ([1.0, 1.0], [1.0, 1.0], [1.0, 2.0, 1.0]),
        # difference of squares: (1+x)(1-x) = 1 - x^2
        ([1.0, 1.0], [1.0, -1.0], [1.0, 0.0, -1.0]),
        # high-order: (1 + x + x^2 + x^3 + x^4)(1 + x) -> degree 5
        ([1, 1, 1, 1, 1], [1, 1], [1, 2, 2, 2, 2, 1]),
    ], ids=[
        "unity_x_unity",
        "poly_x_unity",
        "zero_x_poly",
        "binomial_squared",
        "difference_of_squares",
        "high_order_deg4_x_deg1",
    ])
    def test_pmul(self, a, b, expected):
        result = BlockDiagramSimulator._pmul(np.array(a), np.array(b))
        assert_poly_equal(result, expected)

    def test_pmul_commutativity(self):
        """a * b == b * a for arbitrary polynomials."""
        a = np.array([1.0, 3.0, -2.0])
        b = np.array([2.0, -1.0])
        assert_poly_equal(
            BlockDiagramSimulator._pmul(a, b),
            BlockDiagramSimulator._pmul(b, a),
            "Multiplication should be commutative",
        )


# ---------------------------------------------------------------------------
# _padd tests
# ---------------------------------------------------------------------------
class TestPadd:
    """Polynomial addition (low-power-first, zero-padded)."""

    @pytest.mark.parametrize("a, b, expected", [
        # identity: p + 0 = p
        ([1.0, 2.0], [0.0], [1.0, 2.0]),
        # same length
        ([1.0, 2.0], [3.0, 4.0], [4.0, 6.0]),
        # different lengths
        ([1.0], [0.0, 0.0, 5.0], [1.0, 0.0, 5.0]),
        # cancellation
        ([1.0, 2.0], [-1.0, -2.0], [0.0, 0.0]),
        # adding zero polynomial
        ([0.0], [0.0], [0.0]),
    ], ids=[
        "identity_add_zero",
        "same_length",
        "different_lengths",
        "cancellation",
        "zero_plus_zero",
    ])
    def test_padd(self, a, b, expected):
        result = BlockDiagramSimulator._padd(np.array(a), np.array(b))
        assert_poly_equal(result, expected)

    def test_padd_commutativity(self):
        """a + b == b + a."""
        a = np.array([1.0, -3.0, 7.0])
        b = np.array([2.0, 5.0])
        assert_poly_equal(
            BlockDiagramSimulator._padd(a, b),
            BlockDiagramSimulator._padd(b, a),
        )


# ---------------------------------------------------------------------------
# _psub tests
# ---------------------------------------------------------------------------
class TestPsub:
    """Polynomial subtraction (low-power-first)."""

    @pytest.mark.parametrize("a, b, expected", [
        # self-subtraction = zero
        ([1.0, 2.0, 3.0], [1.0, 2.0, 3.0], [0.0, 0.0, 0.0]),
        # different lengths
        ([1.0, 2.0, 3.0], [1.0], [0.0, 2.0, 3.0]),
        # subtract from zero
        ([0.0], [1.0, 2.0], [-1.0, -2.0]),
        # subtract zero = identity
        ([5.0, -3.0], [0.0], [5.0, -3.0]),
    ], ids=[
        "self_subtraction",
        "different_lengths",
        "subtract_from_zero",
        "subtract_zero_identity",
    ])
    def test_psub(self, a, b, expected):
        result = BlockDiagramSimulator._psub(np.array(a), np.array(b))
        assert_poly_equal(result, expected)

    def test_psub_is_add_negation(self):
        """a - b == a + (-b)."""
        a = np.array([3.0, 1.0, 4.0])
        b = np.array([1.0, 5.0])
        sub_result = BlockDiagramSimulator._psub(a, b)
        add_neg_result = BlockDiagramSimulator._padd(a, -b)
        assert_poly_equal(sub_result, add_neg_result)


# ---------------------------------------------------------------------------
# _pscale tests
# ---------------------------------------------------------------------------
class TestPscale:
    """Polynomial scaling by scalar."""

    @pytest.mark.parametrize("a, scalar, expected", [
        # scale by zero
        ([1.0, 2.0, 3.0], 0.0, [0.0, 0.0, 0.0]),
        # scale by one (identity)
        ([1.0, 2.0, 3.0], 1.0, [1.0, 2.0, 3.0]),
        # scale by -2
        ([1.0, 2.0], -2.0, [-2.0, -4.0]),
        # scale by fractional
        ([4.0, 6.0], 0.5, [2.0, 3.0]),
    ], ids=[
        "scale_by_zero",
        "scale_by_one_identity",
        "scale_by_neg2",
        "scale_by_half",
    ])
    def test_pscale(self, a, scalar, expected):
        result = BlockDiagramSimulator._pscale(np.array(a), scalar)
        assert_poly_equal(result, expected)


# ---------------------------------------------------------------------------
# _clean_poly tests
# ---------------------------------------------------------------------------
class TestCleanPoly:
    """Trailing coefficient cleanup (instance method, low-power-first).

    _clean_poly strips trailing coefficients whose absolute value is below
    a relative threshold of 1e-10 * max(|coeffs|).
    """

    def test_already_clean(self, bdb_simulator):
        """No trailing zeros -- returns unchanged."""
        result = bdb_simulator._clean_poly(np.array([1.0, 2.0, 3.0]))
        assert_poly_equal(result, [1.0, 2.0, 3.0])

    def test_trailing_zeros(self, bdb_simulator):
        """Trailing exact zeros stripped."""
        result = bdb_simulator._clean_poly(np.array([1.0, 2.0, 0.0, 0.0]))
        assert_poly_equal(result, [1.0, 2.0])

    def test_trailing_near_zeros(self, bdb_simulator):
        """Trailing near-zero (1e-15) stripped at relative threshold."""
        result = bdb_simulator._clean_poly(np.array([1.0, 2.0, 1e-15]))
        assert_poly_equal(result, [1.0, 2.0])

    def test_all_zeros(self, bdb_simulator):
        """All-zero array returns [0.0]."""
        result = bdb_simulator._clean_poly(np.array([0.0, 0.0, 0.0]))
        assert_poly_equal(result, [0.0])

    def test_empty_array(self, bdb_simulator):
        """Empty array returns [0.0]."""
        result = bdb_simulator._clean_poly(np.array([]))
        assert_poly_equal(result, [0.0])

    def test_single_element(self, bdb_simulator):
        """Single non-zero element preserved."""
        result = bdb_simulator._clean_poly(np.array([5.0]))
        assert_poly_equal(result, [5.0])

    def test_relative_threshold_pitfall(self, bdb_simulator):
        """PITFALL-02: Large dynamic range causes meaningful small coefficients
        to be dropped.

        For [1e6, 1e-5]:
          threshold = 1e-10 * 1e6 = 1e-4
          |1e-5| = 1e-5 < 1e-4 (threshold)
        So the second coefficient gets STRIPPED even though it may be meaningful.
        This is a known limitation of the relative threshold approach.
        """
        result = bdb_simulator._clean_poly(np.array([1e6, 1e-5]))
        # The 1e-5 coefficient IS stripped due to relative threshold
        assert_poly_equal(result, [1e6])

    def test_small_but_above_threshold(self, bdb_simulator):
        """Coefficient just above relative threshold is preserved."""
        # threshold = 1e-10 * 10.0 = 1e-9
        # 1e-8 > 1e-9, so it survives
        result = bdb_simulator._clean_poly(np.array([10.0, 1e-8]))
        assert_poly_equal(result, [10.0, 1e-8])
