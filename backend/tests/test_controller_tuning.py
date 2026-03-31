"""Tests for Controller Tuning Lab — smoke, numerical accuracy, modern controllers.

Covers all 9 auto-tuning methods, 8 plant presets, plant type detection,
FOPDT fitting, and modern controller modes (state feedback, pole placement,
LQR, LQG).
"""

import numpy as np
import pytest
from scipy import signal

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from simulations.controller_tuning_lab import ControllerTuningLabSimulator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_sim(preset: str = "first_order", build_plant: bool = True,
             **overrides) -> ControllerTuningLabSimulator:
    """Factory: create an initialized simulator with given preset + overrides.

    Args:
        build_plant: If True (default), call _build_plant_tf() so that
            _plant_num/_plant_den and state-space (A,B,C,D) are populated.
            initialize() alone only sets defaults; the plant TF is built
            lazily in get_plots().
    """
    params = {
        "plant_preset": preset,
        "controller_type": "PID",
        "tuning_method": "manual",
        "plant_gain": 1.0,
        **overrides,
    }
    sim = ControllerTuningLabSimulator("controller_tuning_lab")
    sim.initialize(params)
    if build_plant:
        sim._build_plant_tf()
    return sim


def cl_is_stable(sim: ControllerTuningLabSimulator, gains: dict) -> bool:
    """Check if applying gains to sim produces a stable closed loop."""
    N = float(sim.parameters.get("deriv_filter_N", 20))
    kp = gains.get("Kp", 0)
    ki = gains.get("Ki", 0)
    kd = gains.get("Kd", 0)
    # Build PID TF: C(s) = ((Kp+Kd*N)s² + (Kp*N+Ki)s + Ki*N) / (s² + Ns)
    c_num = np.array([kp + kd * N, kp * N + ki, ki * N])
    c_den = np.array([1.0, N, 0.0])
    ol_n = np.convolve(c_num, sim._plant_num)
    ol_d = np.convolve(c_den, sim._plant_den)
    ml = max(len(ol_d), len(ol_n))
    cl_d = np.pad(ol_d, (ml - len(ol_d), 0)) + np.pad(ol_n, (ml - len(ol_n), 0))
    poles = np.roots(cl_d)
    if len(poles) == 0:
        return True
    return float(np.max(poles.real)) < 1e-4


# Reference FOPDT plant: K=1, tau=1, L=0.5
FOPDT_K, FOPDT_TAU, FOPDT_L = 1.0, 1.0, 0.5
FOPDT_PARAMS = {
    "plant_preset": "fopdt",
    "plant_gain": FOPDT_K,
    "plant_tau": FOPDT_TAU,
    "plant_delay": FOPDT_L,
}

# All plant presets
ALL_PRESETS = [
    "first_order", "second_order", "integrator", "double_integrator",
    "fopdt", "dc_motor", "unstable", "custom",
]

# Tuning methods that use FOPDT fitting
FOPDT_METHODS = ["zn_open", "cohen_coon", "lambda_tuning", "imc"]

# All tuning methods
ALL_METHODS = [
    "zn_open", "zn_closed", "cohen_coon", "lambda_tuning", "imc",
    "itae_optimal", "de_optimal", "es_adaptive", "ppo_rl",
]

# Plants classified by type
STABLE_PRESETS = ["first_order", "second_order", "fopdt"]
INTEGRATING_PRESETS = ["integrator", "double_integrator", "dc_motor"]
UNSTABLE_PRESETS = ["unstable"]


# ===========================================================================
# TestPlantTypeDetection
# ===========================================================================

class TestPlantTypeDetection:
    """Verify _detect_plant_type() classifies all presets correctly."""

    @pytest.mark.parametrize("preset", STABLE_PRESETS)
    def test_stable_plants(self, preset):
        sim = make_sim(preset)
        assert sim._detect_plant_type() == "stable"

    def test_integrator(self):
        sim = make_sim("integrator")
        assert sim._detect_plant_type() == "integrating"

    def test_double_integrator(self):
        sim = make_sim("double_integrator")
        assert sim._detect_plant_type() == "integrating"

    def test_dc_motor(self):
        # K/(Js + b) with pole at s=0 → integrating
        sim = make_sim("dc_motor")
        assert sim._detect_plant_type() == "integrating"

    def test_unstable(self):
        sim = make_sim("unstable", plant_a=1.0)
        assert sim._detect_plant_type() == "unstable"

    def test_custom_stable(self):
        sim = make_sim("custom", custom_num="1", custom_den="1, 2, 1")
        assert sim._detect_plant_type() == "stable"

    def test_custom_unstable(self):
        sim = make_sim("custom", custom_num="1", custom_den="1, -1")
        assert sim._detect_plant_type() == "unstable"


# ===========================================================================
# TestFOPDTFitting
# ===========================================================================

class TestFOPDTFitting:
    """Verify _fit_fopdt_model() returns correct values."""

    def test_fopdt_preset_exact_params(self):
        """BUG-050 regression: FOPDT preset must return exact user params."""
        sim = make_sim(**FOPDT_PARAMS)
        K, tau, L = sim._fit_fopdt_model()
        assert K == pytest.approx(FOPDT_K, abs=1e-10)
        assert tau == pytest.approx(FOPDT_TAU, abs=1e-10)
        assert L == pytest.approx(FOPDT_L, abs=1e-10)

    def test_fopdt_preset_varied_params(self):
        """FOPDT with non-default params returns those exact values."""
        sim = make_sim("fopdt", plant_gain=2.5, plant_tau=3.0, plant_delay=0.8)
        K, tau, L = sim._fit_fopdt_model()
        assert K == pytest.approx(2.5, abs=1e-10)
        assert tau == pytest.approx(3.0, abs=1e-10)
        assert L == pytest.approx(0.8, abs=1e-10)

    @pytest.mark.parametrize("preset", ["first_order", "second_order", "dc_motor"])
    def test_non_fopdt_returns_finite(self, preset):
        """Non-FOPDT presets go through fitting — results must be finite and positive."""
        sim = make_sim(preset)
        K, tau, L = sim._fit_fopdt_model()
        assert np.isfinite(K) and K > 0
        assert np.isfinite(tau) and tau > 0
        assert np.isfinite(L) and L > 0

    def test_unstable_returns_finite(self):
        sim = make_sim("unstable", plant_a=1.0)
        K, tau, L = sim._fit_fopdt_model()
        assert np.isfinite(K) and K > 0
        assert np.isfinite(tau) and tau > 0
        assert np.isfinite(L) and L > 0

    def test_integrator_returns_finite(self):
        sim = make_sim("integrator")
        K, tau, L = sim._fit_fopdt_model()
        assert np.isfinite(K) and K > 0
        assert np.isfinite(tau) and tau > 0
        assert np.isfinite(L) and L > 0


# ===========================================================================
# TestZNOpenLoop — exact textbook formulas
# ===========================================================================

class TestZNOpenLoop:
    """Ziegler-Nichols open-loop on reference FOPDT (K=1, tau=1, L=0.5).

    Textbook formulas (ratio = tau / (K * L)):
      P:   Kp = ratio
      PI:  Kp = 0.9 * ratio,  Ti = L/0.3
      PID: Kp = 1.2 * ratio,  Ti = 2*L,  Td = 0.5*L
    """

    @pytest.fixture
    def sim(self):
        return make_sim(**FOPDT_PARAMS)

    def test_p_gains(self, sim):
        gains = sim._zn_open_loop("P")
        ratio = FOPDT_TAU / (FOPDT_K * FOPDT_L)  # = 2.0
        assert gains["Kp"] == pytest.approx(ratio, abs=1e-10)
        assert gains["Ki"] == 0.0
        assert gains["Kd"] == 0.0

    def test_pi_gains(self, sim):
        gains = sim._zn_open_loop("PI")
        ratio = FOPDT_TAU / (FOPDT_K * FOPDT_L)
        expected_kp = 0.9 * ratio  # = 1.8
        Ti = FOPDT_L / 0.3  # = 5/3
        expected_ki = expected_kp / Ti  # = 1.08
        assert gains["Kp"] == pytest.approx(expected_kp, abs=1e-10)
        assert gains["Ki"] == pytest.approx(expected_ki, abs=1e-10)
        assert gains["Kd"] == 0.0

    def test_pid_gains(self, sim):
        gains = sim._zn_open_loop("PID")
        ratio = FOPDT_TAU / (FOPDT_K * FOPDT_L)
        expected_kp = 1.2 * ratio  # = 2.4
        Ti = 2.0 * FOPDT_L  # = 1.0
        Td = 0.5 * FOPDT_L  # = 0.25
        expected_ki = expected_kp / Ti  # = 2.4
        expected_kd = expected_kp * Td  # = 0.6
        assert gains["Kp"] == pytest.approx(expected_kp, abs=1e-10)
        assert gains["Ki"] == pytest.approx(expected_ki, abs=1e-10)
        assert gains["Kd"] == pytest.approx(expected_kd, abs=1e-10)


# ===========================================================================
# TestCohenCoon — exact textbook formulas
# ===========================================================================

class TestCohenCoon:
    """Cohen-Coon on reference FOPDT (K=1, tau=1, L=0.5).

    Formulas use r = L/tau, base = tau/(K*L):
      P:   Kp = base * (1 + r/3)
      PI:  Kp = base * (0.9 + r/12),  Ti = L*(30+3r)/(9+20r)
      PID: Kp = base * (4/3 + r/4),   Ti = L*(32+6r)/(13+8r),  Td = L*4/(11+2r)
    """

    @pytest.fixture
    def sim(self):
        return make_sim(**FOPDT_PARAMS)

    @pytest.fixture
    def r(self):
        return FOPDT_L / FOPDT_TAU  # 0.5

    @pytest.fixture
    def base(self):
        return FOPDT_TAU / (FOPDT_K * FOPDT_L)  # 2.0

    def test_p_gains(self, sim, r, base):
        gains = sim._cohen_coon("P")
        expected_kp = base * (1 + r / 3)  # 2.0 * 7/6 ≈ 2.3333
        assert gains["Kp"] == pytest.approx(expected_kp, abs=1e-10)
        assert gains["Ki"] == 0.0
        assert gains["Kd"] == 0.0

    def test_pi_gains(self, sim, r, base):
        gains = sim._cohen_coon("PI")
        expected_kp = base * (0.9 + r / 12)  # 2.0 * (0.9 + 1/24)
        Ti = FOPDT_L * (30 + 3 * r) / (9 + 20 * r)
        expected_ki = expected_kp / Ti
        assert gains["Kp"] == pytest.approx(expected_kp, abs=1e-10)
        assert gains["Ki"] == pytest.approx(expected_ki, abs=1e-10)
        assert gains["Kd"] == 0.0

    def test_pid_gains(self, sim, r, base):
        gains = sim._cohen_coon("PID")
        expected_kp = base * (4 / 3 + r / 4)  # 2.0 * (4/3 + 1/8)
        Ti = FOPDT_L * (32 + 6 * r) / (13 + 8 * r)
        Td = FOPDT_L * 4 / (11 + 2 * r)
        expected_ki = expected_kp / Ti
        expected_kd = expected_kp * Td
        assert gains["Kp"] == pytest.approx(expected_kp, abs=1e-10)
        assert gains["Ki"] == pytest.approx(expected_ki, abs=1e-10)
        assert gains["Kd"] == pytest.approx(expected_kd, abs=1e-10)


# ===========================================================================
# TestLambdaIMC — exact textbook formulas
# ===========================================================================

class TestLambdaIMC:
    """Lambda and IMC tuning on reference FOPDT (K=1, tau=1, L=0.5)."""

    @pytest.fixture
    def sim(self):
        return make_sim(**FOPDT_PARAMS, lambda_cl_tau=1.0)

    def test_lambda_pi(self, sim):
        """Lambda: Kp = tau/(K*(lambda+L)), Ti = tau."""
        gains = sim._lambda_tuning("PI")
        lambda_cl = 1.0
        expected_kp = FOPDT_TAU / (FOPDT_K * (lambda_cl + FOPDT_L))  # 1/(1.5) ≈ 0.6667
        expected_ki = expected_kp / FOPDT_TAU  # same as Kp since tau=1
        assert gains["Kp"] == pytest.approx(expected_kp, abs=1e-10)
        assert gains["Ki"] == pytest.approx(expected_ki, abs=1e-10)
        assert gains["Kd"] == 0.0

    def test_lambda_pid(self, sim):
        """Lambda PID has Ki but Kd=0 (Lambda is PI-only by design)."""
        gains = sim._lambda_tuning("PID")
        assert gains["Kd"] == 0.0
        assert gains["Kp"] > 0
        assert gains["Ki"] > 0

    def test_imc_pid(self, sim):
        """IMC: tau_c = max(0.25*tau, 1.5*L), then standard IMC formulas."""
        gains = sim._imc_tuning("PID")
        tau_c = max(0.25 * FOPDT_TAU, 1.5 * FOPDT_L)  # max(0.25, 0.75) = 0.75
        expected_kp = (FOPDT_TAU + 0.5 * FOPDT_L) / (FOPDT_K * (tau_c + 0.5 * FOPDT_L))
        Ti = FOPDT_TAU + 0.5 * FOPDT_L  # 1.25
        Td = FOPDT_TAU * FOPDT_L / (2 * FOPDT_TAU + FOPDT_L)  # 0.5/2.5 = 0.2
        expected_ki = expected_kp / Ti
        expected_kd = expected_kp * Td
        assert gains["Kp"] == pytest.approx(expected_kp, abs=1e-10)
        assert gains["Ki"] == pytest.approx(expected_ki, abs=1e-10)
        assert gains["Kd"] == pytest.approx(expected_kd, abs=1e-10)

    def test_imc_pi(self, sim):
        """IMC PI: same Kp/Ki, Kd forced to 0."""
        gains = sim._imc_tuning("PI")
        assert gains["Kd"] == 0.0
        assert gains["Kp"] > 0
        assert gains["Ki"] > 0


# ===========================================================================
# TestZNClosedLoop
# ===========================================================================

class TestZNClosedLoop:
    """ZN closed-loop: verify Ku/Pu-based formulas on a plant that has
    imaginary-axis crossings (second_order with low damping)."""

    def test_second_order_finds_ku(self):
        """Second-order underdamped should have imaginary axis crossings."""
        sim = make_sim("second_order", plant_zeta=0.3, plant_omega=5.0)
        gains = sim._zn_closed_loop("PID")
        # Should produce finite gains (not fall back to open-loop)
        assert np.isfinite(gains["Kp"]) and gains["Kp"] > 0
        assert np.isfinite(gains["Ki"]) and gains["Ki"] > 0
        assert np.isfinite(gains["Kd"]) and gains["Kd"] > 0

    def test_first_order_falls_back(self):
        """First-order has no imaginary crossings — should fall back to ZN open."""
        sim = make_sim("first_order")
        gains = sim._zn_closed_loop("PID")
        # Shouldn't crash; should return finite gains via fallback
        assert np.isfinite(gains["Kp"])


# ===========================================================================
# TestSmokeAllCombinations — method × plant matrix
# ===========================================================================

# Which (method, plant) combinations are expected to produce valid gains
# vs None/crash. FOPDT methods redirect to DE for unstable/integrating.
SKIP_COMBOS = {
    # ZN closed-loop might not find Ku on simple plants — it falls back to
    # open-loop, which in turn redirects for unstable/integrating. These
    # still shouldn't crash.
}


class TestSmokeAllCombinations:
    """Every tuning method × every plant preset: no crash, gains finite."""

    @pytest.mark.parametrize("method", ALL_METHODS)
    @pytest.mark.parametrize("preset", ALL_PRESETS)
    def test_no_crash(self, method, preset):
        """Method runs without exception on every plant."""
        extra = {}
        if preset == "custom":
            extra = {"custom_num": "1", "custom_den": "1, 1"}
        sim = make_sim(preset, tuning_method=method, **extra)

        # Run auto-tune
        result = sim._auto_tune()

        # ML methods may return None if model not found — that's OK
        if method in ("es_adaptive", "ppo_rl") and result is None:
            return

        # DE/ITAE may return None for very hard plants — that's OK
        if method in ("de_optimal", "itae_optimal") and result is None:
            return

        # For methods that return gains, verify they're finite
        if result is not None:
            assert np.isfinite(result["Kp"]), f"Kp not finite: {result}"
            assert np.isfinite(result["Ki"]), f"Ki not finite: {result}"
            assert np.isfinite(result["Kd"]), f"Kd not finite: {result}"

    @pytest.mark.parametrize("method", FOPDT_METHODS)
    @pytest.mark.parametrize("preset", STABLE_PRESETS)
    def test_stable_plant_cl_stability(self, method, preset):
        """FOPDT methods on stable plants should produce stabilizing gains."""
        sim = make_sim(preset, tuning_method=method)
        result = sim._auto_tune()
        if result is not None:
            assert cl_is_stable(sim, result), (
                f"{method} on {preset}: CL not stable with {result}"
            )

    @pytest.mark.parametrize("method", FOPDT_METHODS)
    @pytest.mark.parametrize("preset", INTEGRATING_PRESETS + UNSTABLE_PRESETS)
    def test_auto_redirect_to_de(self, method, preset):
        """FOPDT methods on unstable/integrating plants redirect to DE."""
        sim = make_sim(preset, tuning_method=method)
        result = sim._auto_tune()
        # Should have tuning_info mentioning redirect
        assert sim._tuning_info is not None
        # Result can be None (DE failed) or valid gains
        if result is not None:
            assert np.isfinite(result["Kp"])


# ===========================================================================
# TestModernControllers
# ===========================================================================

class TestModernControllers:
    """State feedback, pole placement, LQR, LQG on known plants."""

    def test_pole_placement_first_order(self):
        """Place CL pole at s=-5 for K/(tau*s+1), verify CL pole location."""
        sim = make_sim("first_order", controller_type="pole_placement",
                       pp_pole1_real=-5.0, pp_pole1_imag=0.0)
        K = sim._get_state_feedback_K()
        assert K is not None, "Pole placement should succeed for first_order"
        # Verify CL pole: A_cl = A - B*K
        A_cl = sim._A - sim._B @ K.reshape(1, -1)
        cl_poles = np.linalg.eigvals(A_cl)
        assert np.allclose(np.sort(cl_poles.real), [-5.0], atol=0.1)

    def test_pole_placement_second_order(self):
        """Place CL poles at s=-3±2j for second_order plant."""
        sim = make_sim("second_order", controller_type="pole_placement",
                       plant_zeta=0.3, plant_omega=5.0,
                       pp_pole1_real=-3.0, pp_pole1_imag=2.0,
                       pp_pole2_real=-3.0, pp_pole2_imag=-2.0)
        K = sim._get_state_feedback_K()
        assert K is not None, "Pole placement should succeed for second_order"
        A_cl = sim._A - sim._B @ K.reshape(1, -1)
        cl_poles = np.linalg.eigvals(A_cl)
        # Both CL poles should be in LHP
        assert np.all(cl_poles.real < 0), f"CL poles not stable: {cl_poles}"
        # Check approximate locations
        desired = np.array([-3 + 2j, -3 - 2j])
        for d in desired:
            dists = np.abs(cl_poles - d)
            assert np.min(dists) < 0.5, f"Desired pole {d} not found in {cl_poles}"

    def test_lqr_first_order(self):
        """LQR on first_order: should return finite K and stable CL."""
        sim = make_sim("first_order", controller_type="lqr",
                       lqr_q1=10.0, lqr_r=1.0)
        K = sim._get_state_feedback_K()
        assert K is not None, "LQR should succeed for first_order"
        assert np.all(np.isfinite(K))
        A_cl = sim._A - sim._B @ K.reshape(1, -1)
        cl_poles = np.linalg.eigvals(A_cl)
        assert np.all(cl_poles.real < 0), f"LQR CL not stable: {cl_poles}"

    def test_lqr_second_order(self):
        """LQR on second_order: higher Q pushes poles further left."""
        sim_low = make_sim("second_order", controller_type="lqr",
                           lqr_q1=1.0, lqr_q2=1.0, lqr_r=1.0)
        sim_low._build_plant_tf()
        K_low = sim_low._get_state_feedback_K()

        sim_high = make_sim("second_order", controller_type="lqr",
                            lqr_q1=100.0, lqr_q2=100.0, lqr_r=1.0)
        sim_high._build_plant_tf()
        K_high = sim_high._get_state_feedback_K()

        assert K_low is not None and K_high is not None
        # Higher Q → larger K gains
        assert np.linalg.norm(K_high) > np.linalg.norm(K_low)

    def test_lqg_first_order(self):
        """LQG on first_order: augmented system should be stable."""
        sim = make_sim("first_order", controller_type="lqg",
                       lqr_q1=10.0, lqr_r=1.0,
                       lqg_qw1=1.0, lqg_rv=0.1)
        sim._build_lqg_controller()
        # Check that CL num/den were set and CL is stable
        assert hasattr(sim, "_cl_num") and sim._cl_num is not None
        assert hasattr(sim, "_cl_den") and sim._cl_den is not None
        cl_poles = np.roots(sim._cl_den)
        assert np.all(cl_poles.real < 1e-4), f"LQG CL not stable: {cl_poles}"

    def test_state_feedback_manual(self):
        """Manual state feedback K on first_order."""
        sim = make_sim("first_order", controller_type="state_feedback",
                       sf_k1=5.0)
        K = sim._get_state_feedback_K()
        assert K is not None
        assert K[0] == pytest.approx(5.0)

    def test_controllability_check(self):
        """Verify controllability is detected for standard plants."""
        for preset in ["first_order", "second_order"]:
            sim = make_sim(preset)
            assert sim._is_controllable, f"{preset} should be controllable"


# ===========================================================================
# TestGetState — integration: full pipeline produces valid output
# ===========================================================================

class TestGetState:
    """Verify get_state() returns well-formed output for key configurations."""

    def test_default_state(self):
        sim = make_sim("first_order")
        state = sim.get_state()
        assert "parameters" in state
        assert "plots" in state
        assert "metadata" in state
        assert isinstance(state["plots"], list)
        assert len(state["plots"]) > 0

    def test_state_after_auto_tune(self):
        """Apply ZN tuning then get_state — plots should contain step response."""
        sim = make_sim(**FOPDT_PARAMS, tuning_method="zn_open")
        sim._auto_tune()
        # Apply the gains
        if sim._tuning_info:
            state = sim.get_state()
            assert len(state["plots"]) > 0
            plot_ids = [p["id"] for p in state["plots"]]
            assert "step_response" in plot_ids

    @pytest.mark.parametrize("preset", ALL_PRESETS)
    def test_get_state_no_crash(self, preset):
        """get_state() should never crash for any preset."""
        extra = {}
        if preset == "custom":
            extra = {"custom_num": "1", "custom_den": "1, 1"}
        sim = make_sim(preset, **extra)
        state = sim.get_state()
        assert "plots" in state


# ===========================================================================
# TestPerformanceMetrics
# ===========================================================================

class TestPerformanceMetrics:
    """Verify step response metrics are reasonable for known configurations."""

    def test_first_order_no_overshoot(self):
        """First-order with P-only: no overshoot expected."""
        sim = make_sim("first_order", controller_type="P", Kp=1.0)
        sim._build_controller_tf()
        sim._compute_closed_loop()
        t, y = sim._compute_step_response()
        assert len(t) > 0 and len(y) > 0
        # P-only on first order: CL = K*Kp / (tau*s + 1 + K*Kp)
        # No overshoot for first-order CL
        overshoot = (np.max(y) - y[-1]) / max(abs(y[-1]), 1e-10) * 100
        assert overshoot < 1.0, f"First-order P-only should have no overshoot: {overshoot}%"

    def test_high_gain_pid_has_response(self):
        """PID with reasonable gains should reach near setpoint."""
        sim = make_sim("first_order", Kp=5.0, Ki=2.0, Kd=0.5)
        sim._build_controller_tf()
        sim._compute_closed_loop()
        t, y = sim._compute_step_response()
        # With integral action, steady-state should approach 1.0
        assert abs(y[-1] - 1.0) < 0.1, f"Expected ~1.0 final value, got {y[-1]}"
