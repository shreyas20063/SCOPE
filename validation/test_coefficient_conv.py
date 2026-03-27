"""
Tests for coefficient convention conversion in BlockDiagramSimulator.

_operator_to_z: R-domain (R=z^{-1}, low-power-first) -> z-domain (high-power-first)
_operator_to_s: A-domain (A=1/s, low-power-first) -> s-domain (high-power-first)

The output convention (high-power-first) is compatible with np.roots, np.polyval,
and scipy.signal, which all expect [a_n, a_{n-1}, ..., a_0].

Requirements: MATH-03 (convention correctness), TEST-06 (tolerance tiers).
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
        """H(R) = R/(1 - 0.5R) -> H(z) = 1/(1 - 0.5/z) * z/z = z/(z - 0.5).
        After trim: z_num=[1], z_den=[1, -0.5]. Pole at z=0.5."""
        num = np.array([0.0, 1.0])   # R
        den = np.array([1.0, -0.5])  # 1 - 0.5R
        z_num, z_den = bdb_simulator._operator_to_z(num, den)
        assert_poly_equal(z_num, [1.0])
        assert_poly_equal(z_den, [1.0, -0.5])
        # Verify pole location
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
        """H(R) = 1/(1-R) -> H(z) = z/(z-1).
        num=[1], den=[1,-1]. k=1.
        z_num=[1, 0] (high-power-first), z_den=[1, -1]."""
        z_num, z_den = bdb_simulator._operator_to_z(np.array([1.0]), np.array([1.0, -1.0]))
        assert_poly_equal(z_num, [1.0, 0.0])
        assert_poly_equal(z_den, [1.0, -1.0])

    def test_zero_numerator(self, bdb_simulator):
        """H(R) = 0/(1+R) -> H(z) = 0/(...). z_num should be [0]."""
        z_num, z_den = bdb_simulator._operator_to_z(np.array([0.0]), np.array([1.0, 1.0]))
        assert_poly_equal(z_num, [0.0])

    def test_leading_zeros_stripped(self, bdb_simulator):
        """num=[0,0,1] (R^2), den=[1]. k=max(0,2)=2.
        z_num=[0,0,1] -> trim leading -> [1]. z_den=[1,0,0] -> trim -> [1].
        Result: H(z)=1/1 -- correct since R^2/1 * z^2/z^2 = 1."""
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
        """H(A) = A/1 = (1/s)/1. num=[0,1], den=[1].
        k=max(0,1)=1. s_num=[0,1] -> trim -> [1]. s_den=[1,0] -> trim -> [1,0].
        H(s) = 1/s. Correct integrator."""
        s_num, s_den = bdb_simulator._operator_to_s(np.array([0.0, 1.0]), np.array([1.0]))
        assert_poly_equal(s_num, [1.0])
        assert_poly_equal(s_den, [1.0, 0.0])

    def test_unity(self, bdb_simulator):
        """H(A) = 1/1 -> H(s) = 1/1."""
        s_num, s_den = bdb_simulator._operator_to_s(np.array([1.0]), np.array([1.0]))
        assert_poly_equal(s_num, [1.0])
        assert_poly_equal(s_den, [1.0])

    def test_second_order_research_example(self, bdb_simulator):
        """Research example: H(A) = (1 + 2A) / (1 + 3A + A^2).
        num_a=[1,2], den_a=[1,3,1]. k=max(2,1)=2.
        s_num=[1,2,0] -> trim -> [1,2]. Wait, actually:
        s_num=zeros(3); s_num[:2]=[1,2] -> [1,2,0] -> trim('f') -> [1,2,0]...
        No, trim_zeros('f') removes LEADING zeros. [1,2,0] has no leading zeros.
        So s_num=[1,2,0], s_den=[1,3,1].

        H(s) = (s^2 + 2s) / (s^2 + 3s + 1).  Hmm, let me re-derive.

        Actually the high-power-first output means [1,2,0] = 1*s^2 + 2*s + 0.
        And [1,3,1] = s^2 + 3s + 1.

        Evaluate at s=2: (4+4)/(4+6+1) = 8/11.
        But the plan says 4/11. Let me check: the plan expects
        polyval(s_num,2)/polyval(s_den,2) = 4/11.

        With s_num=[1,2], polyval([1,2],2) = 1*2+2 = 4.
        With s_den=[1,3,1], polyval([1,3,1],2) = 4+6+1 = 11.

        So the plan expects s_num=[1,2] which means the trailing zero IS trimmed.
        But trim_zeros('f') only strips LEADING zeros. [1,2,0] has a TRAILING zero.
        trim_zeros('f') won't remove it.

        So actual s_num=[1,2,0] and polyval([1,2,0],2) = 4+4+0 = 8. 8/11 != 4/11.

        The plan's expected value is wrong. Let me test the actual behavior.
        """
        num_a = np.array([1.0, 2.0])
        den_a = np.array([1.0, 3.0, 1.0])
        s_num, s_den = bdb_simulator._operator_to_s(num_a, den_a)

        # Actual output: s_num=[1,2,0], s_den=[1,3,1]
        # H(s) = (s^2 + 2s) / (s^2 + 3s + 1)
        assert_poly_equal(s_num, [1.0, 2.0, 0.0])
        assert_poly_equal(s_den, [1.0, 3.0, 1.0])

        # Evaluate at s=2: (4+4+0)/(4+6+1) = 8/11
        val = np.polyval(s_num, 2.0) / np.polyval(s_den, 2.0)
        assert abs(val - 8.0 / 11.0) < ToleranceTier.EXACT_ATOL

    def test_zero_numerator(self, bdb_simulator):
        """H(A) = 0/1 -> H(s) = 0/1."""
        s_num, s_den = bdb_simulator._operator_to_s(np.array([0.0]), np.array([1.0]))
        assert_poly_equal(s_num, [0.0])
        assert_poly_equal(s_den, [1.0])

    def test_roundtrip_evaluation(self, bdb_simulator):
        """For multiple TFs, convert to s-domain and verify H(s)|_{s=v} == H(A)|_{A=1/v}.

        Tests at multiple s-values to catch convention errors.
        """
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
# Convention consistency tests (MATH-03)
# ---------------------------------------------------------------------------
class TestConventionConsistency:
    """Verify that coefficient convention conversions produce arrays compatible
    with numpy/scipy high-power-first expectations."""

    def test_lowpower_to_highpower_meaning(self):
        """Low-power-first [a0, a1, a2] represents a0 + a1*x + a2*x^2.
        High-power-first [a2, a1, a0] represents a2*x^2 + a1*x + a0.
        Both should evaluate to the same value at any x."""
        a0, a1, a2 = 3.0, -1.0, 2.0
        x = 3.0
        low_power = np.array([a0, a1, a2])
        high_power = np.array([a2, a1, a0])

        # np.polyval uses high-power-first
        val_hp = np.polyval(high_power, x)
        # Manual evaluation of low-power-first
        val_lp = sum(c * x**i for i, c in enumerate(low_power))

        assert abs(val_hp - val_lp) < ToleranceTier.EXACT_ATOL, (
            f"Low-power eval ({val_lp}) != high-power eval ({val_hp})"
        )

    def test_scipy_roots_expects_highpower(self):
        """np.roots([1, -3, 2]) should give roots of x^2 - 3x + 2 = (x-1)(x-2).
        Roots are 1 and 2."""
        roots = np.sort(np.roots([1.0, -3.0, 2.0]))
        expected = np.array([1.0, 2.0])
        assert abs(roots[0] - expected[0]) < ToleranceTier.EXACT_ATOL
        assert abs(roots[1] - expected[1]) < ToleranceTier.EXACT_ATOL

    def test_operator_conversion_outputs_highpower(self, bdb_simulator):
        """After _operator_to_s, output works directly with np.roots.

        H(A) = 1 / (1 + 3A + 2A^2) -> s-domain denominator should have
        poles matching the roots of 2A^2 + 3A + 1 = 0 mapped through A=1/s.

        A-domain: den=[1, 3, 2]. k=2.
        s_den = [1, 3, 2] (padded to 3, no leading zeros to trim).
        Represents s^2 + 3s + 2 = (s+1)(s+2). Poles at s=-1, s=-2.
        """
        num_a = np.array([1.0])
        den_a = np.array([1.0, 3.0, 2.0])
        s_num, s_den = bdb_simulator._operator_to_s(num_a, den_a)

        # np.roots works directly on high-power-first s_den
        poles = np.sort(np.roots(s_den))
        expected_poles = np.array([-2.0, -1.0])
        assert abs(poles[0] - expected_poles[0]) < ToleranceTier.LOOSE_ATOL
        assert abs(poles[1] - expected_poles[1]) < ToleranceTier.LOOSE_ATOL

    def test_z_conversion_roots_compatible(self, bdb_simulator):
        """After _operator_to_z, output works directly with np.roots.

        H(R) = 1 / (1 - 0.8R + 0.15R^2). den=[1, -0.8, 0.15].
        k=2. z_den=[1, -0.8, 0.15]. Poles at z = roots of z^2 - 0.8z + 0.15.
        """
        num_r = np.array([1.0])
        den_r = np.array([1.0, -0.8, 0.15])
        z_num, z_den = bdb_simulator._operator_to_z(num_r, den_r)

        poles = np.sort(np.roots(z_den))
        # z^2 - 0.8z + 0.15 = 0 -> z = (0.8 +/- sqrt(0.64 - 0.6))/2 = (0.8 +/- 0.2)/2
        expected = np.array([0.3, 0.5])
        assert abs(poles[0] - expected[0]) < ToleranceTier.LOOSE_ATOL
        assert abs(poles[1] - expected[1]) < ToleranceTier.LOOSE_ATOL
