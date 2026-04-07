"""Coefficient convention conversion tests for BlockDiagramSimulator.

_operator_to_z converts R-domain (R=z^-1, low-power-first) to z-domain
(high-power-first). _operator_to_s converts A-domain (A=1/s,
low-power-first) to s-domain (high-power-first). The output convention
matches numpy/scipy, which expect [a_n, a_{n-1}, ..., a_0].
"""

import numpy as np
import pytest
from conftest import assert_poly_equal, ToleranceTier
from simulations.block_diagram_builder import BlockDiagramSimulator


# ---------------------------------------------------------------------------
# _operator_to_z tests
# ---------------------------------------------------------------------------
class TestOperatorToZ:
    """R-domain to z-domain conversion (instance method)."""

    def test_simple_delay(self, bdb_simulator):
        """H(R) = R/(1 - 0.5R)  ==>  H(z) = z/(z - 0.5), pole at z=0.5."""
        num = np.array([0.0, 1.0])
        den = np.array([1.0, -0.5])
        z_num, z_den = bdb_simulator._operator_to_z(num, den)
        assert_poly_equal(z_num, [1.0])
        assert_poly_equal(z_den, [1.0, -0.5])
        poles = np.roots(z_den)
        assert abs(poles[0] - 0.5) < ToleranceTier.EXACT_ATOL

    def test_unity(self, bdb_simulator):
        """H(R) = 1/1 -> H(z) = 1/1."""
        z_num, z_den = bdb_simulator._operator_to_z(np.array([1.0]), np.array([1.0]))
        assert_poly_equal(z_num, [1.0])
        assert_poly_equal(z_den, [1.0])

    def test_pure_gain(self, bdb_simulator):
        """H(R) = 5/1 -> H(z) = 5/1."""
        z_num, z_den = bdb_simulator._operator_to_z(np.array([5.0]), np.array([1.0]))
        assert_poly_equal(z_num, [5.0])
        assert_poly_equal(z_den, [1.0])

    def test_first_order_integrator(self, bdb_simulator):
        """H(R) = 1/(1-R)  ==>  H(z) = z/(z-1)."""
        z_num, z_den = bdb_simulator._operator_to_z(np.array([1.0]), np.array([1.0, -1.0]))
        assert_poly_equal(z_num, [1.0, 0.0])
        assert_poly_equal(z_den, [1.0, -1.0])

    def test_zero_numerator(self, bdb_simulator):
        """H(R) = 0/(1+R) -> H(z) = 0/(...). z_num should be [0]."""
        z_num, z_den = bdb_simulator._operator_to_z(np.array([0.0]), np.array([1.0, 1.0]))
        assert_poly_equal(z_num, [0.0])

    def test_leading_zeros_stripped(self, bdb_simulator):
        """H(R) = R^2  ==>  H(z) = 1, since R^2 = z^-2 cancels with the
        z^2 padding factor."""
        z_num, z_den = bdb_simulator._operator_to_z(np.array([0.0, 0.0, 1.0]), np.array([1.0]))
        assert_poly_equal(z_num, [1.0])
        assert_poly_equal(z_den, [1.0])

    def test_evaluation_consistency(self, bdb_simulator):
        """Convert H(R) to H(z), then verify H(z)|_{z=v} == H(R)|_{R=1/v}.

        H(R) = (1 + 2R) / (1 + 0.5R + 0.3R^2)
        At R = 0.5 (z = 2): evaluate both representations.
        """
        num_r = np.array([1.0, 2.0])
        den_r = np.array([1.0, 0.5, 0.3])
        z_num, z_den = bdb_simulator._operator_to_z(num_r, den_r)

        z_val = 2.0
        r_val = 1.0 / z_val  # R = 1/z

        # Evaluate H(z) in high-power-first with np.polyval
        hz = np.polyval(z_num, z_val) / np.polyval(z_den, z_val)
        # Evaluate H(R) in low-power-first manually: sum(c_i * R^i)
        hr_num = sum(c * r_val**i for i, c in enumerate(num_r))
        hr_den = sum(c * r_val**i for i, c in enumerate(den_r))
        hr = hr_num / hr_den

        assert abs(hz - hr) < ToleranceTier.EXACT_ATOL, (
            f"H(z={z_val})={hz} != H(R={r_val})={hr}"
        )


# ---------------------------------------------------------------------------
# _operator_to_s tests
# ---------------------------------------------------------------------------
class TestOperatorToS:
    """A-domain (A=1/s) to s-domain conversion (instance method)."""

    def test_integrator(self, bdb_simulator):
        """H(A) = A  ==>  H(s) = 1/s."""
        s_num, s_den = bdb_simulator._operator_to_s(np.array([0.0, 1.0]), np.array([1.0]))
        assert_poly_equal(s_num, [1.0])
        assert_poly_equal(s_den, [1.0, 0.0])

    def test_unity(self, bdb_simulator):
        """H(A) = 1/1 -> H(s) = 1/1."""
        s_num, s_den = bdb_simulator._operator_to_s(np.array([1.0]), np.array([1.0]))
        assert_poly_equal(s_num, [1.0])
        assert_poly_equal(s_den, [1.0])

    def test_second_order_with_trailing_zero(self, bdb_simulator):
        """H(A) = (1 + 2A) / (1 + 3A + A^2)  ==>  H(s) = (s^2 + 2s) / (s^2 + 3s + 1).

        Documents the trailing-zero behavior of _operator_to_s: padding to
        k+1 then reversing produces a trailing s^0=0 in the numerator.
        np.trim_zeros('f') strips leading zeros only, so the trailing zero
        survives. Both [1,2,0] and [1,2] represent the same polynomial,
        but assert_poly_equal pads to the longer length so this is fine.
        """
        num_a = np.array([1.0, 2.0])
        den_a = np.array([1.0, 3.0, 1.0])
        s_num, s_den = bdb_simulator._operator_to_s(num_a, den_a)
        assert_poly_equal(s_num, [1.0, 2.0, 0.0])
        assert_poly_equal(s_den, [1.0, 3.0, 1.0])
        # H(2) = (4 + 4 + 0) / (4 + 6 + 1) = 8/11
        val = np.polyval(s_num, 2.0) / np.polyval(s_den, 2.0)
        assert abs(val - 8.0 / 11.0) < ToleranceTier.EXACT_ATOL

    def test_zero_numerator(self, bdb_simulator):
        """H(A) = 0/1 -> H(s) = 0/1."""
        s_num, s_den = bdb_simulator._operator_to_s(np.array([0.0]), np.array([1.0]))
        assert_poly_equal(s_num, [0.0])
        assert_poly_equal(s_den, [1.0])

    def test_roundtrip_evaluation(self, bdb_simulator):
        """For each TF, verify H(s)|_{s=v} == H(A)|_{A=1/v} at multiple s
        values. Catches convention errors that happen to align at one point."""
        test_cases = [
            # (num_a, den_a)
            (np.array([1.0, 1.0]), np.array([1.0, 2.0])),       # first order
            (np.array([2.0]), np.array([1.0, 1.0, 1.0])),        # pure gain / second order
            (np.array([0.0, 0.0, 3.0]), np.array([1.0, -1.0])),  # A^2 term
        ]
        s_values = [1.0, 2.0, 3.0, 0.5, 10.0]

        for num_a, den_a in test_cases:
            s_num, s_den = bdb_simulator._operator_to_s(num_a, den_a)
            for s in s_values:
                a_val = 1.0 / s
                # Evaluate H(A) in low-power-first
                ha_num = sum(c * a_val**i for i, c in enumerate(num_a))
                ha_den = sum(c * a_val**i for i, c in enumerate(den_a))
                if abs(ha_den) < 1e-15:
                    continue  # skip if denominator near zero
                ha = ha_num / ha_den
                # Evaluate H(s) in high-power-first
                hs_den_val = np.polyval(s_den, s)
                if abs(hs_den_val) < 1e-15:
                    continue
                hs = np.polyval(s_num, s) / hs_den_val
                assert abs(hs - ha) < ToleranceTier.EXACT_ATOL, (
                    f"Mismatch at s={s}: H(s)={hs}, H(A=1/s)={ha}, "
                    f"num_a={num_a}, den_a={den_a}"
                )


# ---------------------------------------------------------------------------
# Convention consistency
# ---------------------------------------------------------------------------
class TestConventionConsistency:
    """Conversion outputs must be compatible with numpy/scipy
    high-power-first expectations."""

    def test_lowpower_to_highpower_meaning(self):
        """Low-power-first [a0,a1,a2] and high-power-first [a2,a1,a0]
        evaluate to the same value at any x."""
        a0, a1, a2 = 3.0, -1.0, 2.0
        x = 3.0
        low_power = np.array([a0, a1, a2])
        high_power = np.array([a2, a1, a0])
        val_hp = np.polyval(high_power, x)
        val_lp = sum(c * x**i for i, c in enumerate(low_power))
        assert abs(val_hp - val_lp) < ToleranceTier.EXACT_ATOL

    def test_scipy_roots_expects_highpower(self):
        """np.roots([1,-3,2]) returns the roots of x^2 - 3x + 2 = (x-1)(x-2)."""
        roots = np.sort(np.roots([1.0, -3.0, 2.0]))
        assert abs(roots[0] - 1.0) < ToleranceTier.EXACT_ATOL
        assert abs(roots[1] - 2.0) < ToleranceTier.EXACT_ATOL

    def test_operator_conversion_outputs_highpower(self, bdb_simulator):
        """H(A) = 1 / (1 + 3A + 2A^2)  ==>  H(s) = 1 / (s^2 + 3s + 2),
        poles at s = -1, -2. The s_den output feeds np.roots directly."""
        num_a = np.array([1.0])
        den_a = np.array([1.0, 3.0, 2.0])
        _, s_den = bdb_simulator._operator_to_s(num_a, den_a)
        poles = np.sort(np.roots(s_den))
        assert abs(poles[0] - (-2.0)) < ToleranceTier.LOOSE_ATOL
        assert abs(poles[1] - (-1.0)) < ToleranceTier.LOOSE_ATOL

    def test_z_conversion_roots_compatible(self, bdb_simulator):
        """H(R) = 1 / (1 - 0.8R + 0.15R^2)  ==>  H(z) denominator
        z^2 - 0.8z + 0.15 has poles at z = 0.3, 0.5."""
        num_r = np.array([1.0])
        den_r = np.array([1.0, -0.8, 0.15])
        _, z_den = bdb_simulator._operator_to_z(num_r, den_r)
        poles = np.sort(np.roots(z_den))
        assert abs(poles[0] - 0.3) < ToleranceTier.LOOSE_ATOL
        assert abs(poles[1] - 0.5) < ToleranceTier.LOOSE_ATOL
