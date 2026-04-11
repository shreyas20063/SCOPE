"""Math verification tests using known textbook answers.

Tests verify that simulator computations match analytical results
from Ogata, Nise, and standard signals & systems references.
"""

import sys
import os
import math

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.routh_hurwitz import compute_routh_array
from simulations import SIMULATOR_REGISTRY


# =========================================================================
# Routh-Hurwitz (core/routh_hurwitz.py)
# =========================================================================

class TestRouthHurwitz:
    """Routh-Hurwitz sign-change and stability tests."""

    def test_poly_1_2_3_4_stable(self):
        """s^3 + 2s^2 + 3s + 4: all roots have Re<0, so stable with 0 sign changes.

        Routh array first column: [1, 2, 1, 4] — no sign changes.
        Roots: -1.65, -0.17±1.55j (all in LHP).
        """
        result = compute_routh_array([1, 2, 3, 4])
        assert result["sign_changes"] == 0
        assert result["stable"] is True

    def test_poly_1_1_2_8_neg15_unstable(self):
        """s^4 + s^3 + 2s^2 + 8s - 15: unstable (negative constant term)."""
        result = compute_routh_array([1, 1, 2, 8, -15])
        assert result["sign_changes"] > 0
        assert result["stable"] is False

    def test_poly_stable_sixth_order(self):
        """s^6 + 2s^5 + 8s^4 + 12s^3 + 20s^2 + 16s + 16: 0 sign changes (stable)."""
        result = compute_routh_array([1, 2, 8, 12, 20, 16, 16])
        assert result["sign_changes"] == 0
        assert result["stable"] is True

    def test_simple_stable_polynomial(self):
        """s^2 + 3s + 2 = (s+1)(s+2): stable, 0 sign changes."""
        result = compute_routh_array([1, 3, 2])
        assert result["sign_changes"] == 0
        assert result["stable"] is True

    def test_first_column_values(self):
        """s^2 + 3s + 2: first column should be [1, 3, 2]."""
        result = compute_routh_array([1, 3, 2])
        fc = result["first_column"]
        assert len(fc) == 3
        assert abs(fc[0] - 1.0) < 1e-10
        assert abs(fc[1] - 3.0) < 1e-10
        assert abs(fc[2] - 2.0) < 1e-10


# =========================================================================
# Steady-State Error (simulations/steady_state_error.py)
# =========================================================================

class TestSteadyStateError:
    """Steady-state error tests using textbook G(s) examples."""

    def _get_sim(self, preset, gain_K, input_type="step"):
        sim = SIMULATOR_REGISTRY["steady_state_error"]("steady_state_error")
        sim.initialize({
            "plant_preset": preset,
            "gain_K": gain_K,
            "input_type": input_type,
            "input_magnitude": 1.0,
            "feedback_type": "unity",
        })
        return sim

    def test_type0_Kp_and_ess_step(self):
        """Type 0: G(s) = 10/(s+2). Kp = 10/2 = 5, ess_step = 1/(1+5) = 1/6."""
        # Use type0_first preset: num=[1], den=[1,2], with K=10
        # G(s) = K*1/(s+2) = 10/(s+2)
        # Kp = lim s->0 G(s) = 10/2 = 5
        # ess_step = 1/(1+Kp) = 1/6
        sim = self._get_sim("type0_first", 10.0, "step")
        state = sim.get_state()
        meta = state["metadata"]

        Kp = meta["error_constants"]["Kp"]
        ess_step = meta["steady_state_errors"]["step"]

        assert abs(Kp - 5.0) < 0.01, f"Expected Kp=5, got {Kp}"
        assert abs(ess_step - 1.0 / 6.0) < 0.01, f"Expected ess=1/6, got {ess_step}"

    def test_type1_Kv_and_ess_ramp(self):
        """Type 1: G(s) = 10/(s(s+5)). Kv = lim s->0 s*G(s) = 10/5 = 2, ess_ramp = 1/2."""
        sim = self._get_sim("type1_standard", 10.0, "ramp")
        state = sim.get_state()
        meta = state["metadata"]

        Kv = meta["error_constants"]["Kv"]
        ess_ramp = meta["steady_state_errors"]["ramp"]

        assert abs(Kv - 2.0) < 0.01, f"Expected Kv=2, got {Kv}"
        assert abs(ess_ramp - 0.5) < 0.01, f"Expected ess_ramp=0.5, got {ess_ramp}"

    def test_type2_Ka_and_ess_parabolic(self):
        """Type 2: G(s) = 10/(s^2(s+10)). Ka = lim s->0 s^2*G(s) = 10/10 = 1, ess_para = 1/Ka = 1."""
        # type2_standard preset: num=[1], den=[1, 10, 0, 0], K=10
        # G(s) = 10/(s^2(s+10))
        # Ka = lim s->0 s^2 * G(s) = 10/10 = 1
        # ess_parabolic = A/Ka = 1/1 = 1
        sim = self._get_sim("type2_standard", 10.0, "parabolic")
        state = sim.get_state()
        meta = state["metadata"]

        Ka = meta["error_constants"]["Ka"]
        ess_para = meta["steady_state_errors"]["parabolic"]

        assert abs(Ka - 1.0) < 0.01, f"Expected Ka=1, got {Ka}"
        assert abs(ess_para - 1.0) < 0.05, f"Expected ess_parabolic=1.0, got {ess_para}"

    def test_type1_step_error_zero(self):
        """Type 1 system has zero steady-state error for step input."""
        sim = self._get_sim("type1_standard", 10.0, "step")
        state = sim.get_state()
        ess_step = state["metadata"]["steady_state_errors"]["step"]
        assert abs(ess_step) < 0.01, f"Type 1 step ess should be 0, got {ess_step}"

    def test_system_type_detection(self):
        """Verify system type is correctly detected."""
        for preset, expected_type in [
            ("type0_first", 0),
            ("type1_standard", 1),
            ("type2_standard", 2),
        ]:
            sim = self._get_sim(preset, 10.0)
            state = sim.get_state()
            sys_type = state["metadata"]["system_type"]
            assert sys_type == expected_type, (
                f"Preset {preset}: expected type {expected_type}, got {sys_type}"
            )


# =========================================================================
# Second-Order System (simulations/second_order_system.py)
# =========================================================================

class TestSecondOrderSystem:
    """Second-order system textbook formulas: wn, zeta, wd, overshoot, ts."""

    def _get_sim(self, omega_0, Q_slider):
        sim = SIMULATOR_REGISTRY["second_order_system"]("second_order_system")
        sim.initialize({"omega_0": omega_0, "Q_slider": Q_slider})
        return sim

    def test_damped_frequency(self):
        """wn=10, zeta=0.5: wd = wn*sqrt(1-zeta^2) = 10*sqrt(0.75) ~ 8.66."""
        # zeta = 1/(2Q), so Q = 1/(2*0.5) = 1.0 => Q_slider=50
        sim = self._get_sim(10.0, 50)
        state = sim.get_state()
        meta = state["metadata"]
        zeta = meta["system_info"]["zeta"]
        omega_0 = meta["system_info"]["omega_0"]

        # zeta should be 0.5 (Q=1 => zeta = 1/(2*1) = 0.5)
        assert abs(zeta - 0.5) < 0.01, f"Expected zeta=0.5, got {zeta}"

        # Check wd from poles
        poles_str = meta["system_info"]["poles"]
        # Poles are complex: s = -5 +/- 8.66j
        # wd = wn * sqrt(1 - zeta^2) = 10 * sqrt(0.75) ~ 8.66
        expected_wd = 10.0 * math.sqrt(1.0 - 0.5**2)

        # Extract imag part from the plots (pole-zero plot data)
        pole_plot = state["plots"][0]  # pole-zero plot is first
        # Find pole markers in plot data
        for trace in pole_plot["data"]:
            if "Poles" in trace.get("name", ""):
                y_vals = trace.get("y", [])
                if y_vals:
                    imag_part = max(abs(v) for v in y_vals if isinstance(v, (int, float)))
                    assert abs(imag_part - expected_wd) < 0.5, (
                        f"Expected wd~{expected_wd:.2f}, got imag={imag_part:.2f}"
                    )
                    break

    def test_zeta_mapping(self):
        """Q_slider=50 => Q=1.0 => zeta=0.5."""
        sim = self._get_sim(10.0, 50)
        state = sim.get_state()
        zeta = state["metadata"]["system_info"]["zeta"]
        Q = state["metadata"]["system_info"]["Q"]
        assert abs(Q - 1.0) < 0.01, f"Expected Q=1.0, got {Q}"
        assert abs(zeta - 0.5) < 0.01, f"Expected zeta=0.5, got {zeta}"

    def test_underdamped_classification(self):
        """Q > 0.5 should be underdamped."""
        sim = self._get_sim(10.0, 50)  # Q=1.0 > 0.5
        state = sim.get_state()
        damping = state["metadata"]["system_info"]["damping_type"]
        assert "Underdamped" in damping, f"Expected Underdamped, got {damping}"

    def test_overdamped_classification(self):
        """Q < 0.5 should be overdamped."""
        # Q=0.3 => Q_slider such that 10^((s/50)-1)=0.3 => s=50*(1+log10(0.3))
        slider = 50 * (1 + math.log10(0.3))
        sim = self._get_sim(10.0, slider)
        state = sim.get_state()
        damping = state["metadata"]["system_info"]["damping_type"]
        assert "Overdamped" in damping, f"Expected Overdamped, got {damping}"


# =========================================================================
# Root Locus Breakaway (simulations/root_locus.py)
# =========================================================================

class TestRootLocusBreakaway:
    """Root locus breakaway point verification."""

    def test_breakaway_at_s_neg1(self):
        """G(s) = 1/(s(s+2)): breakaway at s = -1.

        N(s)D'(s) - N'(s)D(s) = 0
        N=1, D=s^2+2s => D'=2s+2
        1*(2s+2) - 0*(s^2+2s) = 2s+2 = 0 => s = -1
        """
        sim = SIMULATOR_REGISTRY["root_locus"]("root_locus")
        sim.initialize({
            "num_coeffs": "1",
            "den_coeffs": "1, 2, 0",
            "gain_K": 1.0,
            "preset": "custom",
        })
        state = sim.get_state()
        special = state["metadata"]["special_points"]
        breakaway_pts = special.get("breakaway", [])

        assert len(breakaway_pts) > 0, "No breakaway points found"

        # At least one breakaway point should be near s = -1
        s_values = [bp["s"]["real"] for bp in breakaway_pts]
        closest = min(s_values, key=lambda s: abs(s - (-1.0)))
        assert abs(closest - (-1.0)) < 0.1, (
            f"Expected breakaway near s=-1, closest was s={closest}"
        )


# =========================================================================
# DC Motor (simulations/dc_motor.py)
# =========================================================================

class TestDCMotor:
    """DC Motor steady-state gain verification."""

    def test_first_order_steady_state_gain(self):
        """First-order DC motor: H(s) = ag/(s + abg).

        Steady-state gain = H(0) = ag/(abg) = 1/b.
        Default: beta=0.5, so gain = 1/0.5 = 2.0.
        """
        sim = SIMULATOR_REGISTRY["dc_motor"]("dc_motor")
        sim.initialize()  # defaults: alpha=10, beta=0.5, gamma=1, model_type=first_order
        state = sim.get_state()

        beta = state["parameters"]["beta"]
        expected_gain = 1.0 / beta

        # The steady-state value is nested in metadata.system_info
        sys_info = state["metadata"]["system_info"]
        ss_value = sys_info.get("steady_state_value")
        assert ss_value is not None, "DC motor system_info missing steady_state_value"
        assert abs(ss_value - expected_gain) < 0.01, (
            f"Expected SS gain = {expected_gain}, got {ss_value}"
        )

    def test_second_order_steady_state_gain(self):
        """Second-order DC motor: H(s) = agp/(s^2 + ps + abgp).

        Steady-state gain = H(0) = agp/(abgp) = 1/b.
        """
        sim = SIMULATOR_REGISTRY["dc_motor"]("dc_motor")
        sim.initialize({"model_type": "second_order"})
        state = sim.get_state()

        beta = state["parameters"]["beta"]
        expected_gain = 1.0 / beta

        sys_info = state["metadata"]["system_info"]
        ss_value = sys_info.get("steady_state_value")
        assert ss_value is not None, "DC motor system_info missing steady_state_value"
        assert abs(ss_value - expected_gain) < 0.01, (
            f"Expected SS gain = {expected_gain}, got {ss_value}"
        )
