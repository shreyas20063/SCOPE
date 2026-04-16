"""End-to-end integration test for the System Hub TF propagation pipeline.

Pushes a canonical CT transfer function H(s) = 10 / (s² + 2s + 10) through
the validator and into every hub-aware consumer sim, verifying that:

1. The validator enriches the raw TF correctly (poles, stability, system type, SS).
2. The state endpoint exposes the has_custom_from_hub_data flag for sims that
   override BaseSimulator.from_hub_data.
3. The two production injection paths both work:
     - Path A (custom): frontend calls execute action=from_hub_data
     - Path B (standard): frontend maps NUM_KEYS/DEN_KEYS into update_parameter
4. Math spot-checks: where consumers expose poles, they match the expected
   locations -1 ± 3j of the test TF.
5. Producer-only sims correctly return 200 with {success:false} on from_hub_data.

This test simulates the exact flow from useSimulation.js and is the only
test that validates the full chain end-to-end. If any future change breaks
hub propagation for any sim, this test catches it.

Canonical TF: H(s) = 10 / (s² + 2s + 10)
  - Poles: -1 ± 3j (stable, underdamped, ωn=√10, ζ=1/√10)
  - Type 0 (no integrators)
  - DC gain = 1
"""
import logging

import pytest
from fastapi.testclient import TestClient

# Silence verbose httpx logging
logging.getLogger("httpx").setLevel(logging.WARNING)

from main import app
from core.hub_validator import validate_and_enrich_control


# ---------------------------------------------------------------------------
# Canonical TF and the production frontend's standard-path key lists
# (mirrored from useSimulation.js — these MUST stay in sync with the frontend)
# ---------------------------------------------------------------------------

RAW_TF = {
    "source": "tf",
    "domain": "ct",
    "num": [10.0],
    "den": [1.0, 2.0, 10.0],
}
EXPECTED_POLE_REAL = -1.0
EXPECTED_POLE_IMAG_ABS = 3.0

NUM_KEYS = ['numerator', 'num_coeffs', 'custom_num', 'plant_num', 'tf_numerator']
DEN_KEYS = [
    'denominator', 'den_coeffs', 'custom_den', 'plant_den',
    'tf_denominator', 'poly_coeffs',
]
PRESET_KEYS = ['preset', 'plant_preset', 'system_preset']


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def enriched_hub():
    """Validator output for the canonical TF — used as the hub payload."""
    result = validate_and_enrich_control(RAW_TF)
    assert result["success"], f"Validator failed: {result.get('error')}"
    return result["data"]


# ---------------------------------------------------------------------------
# 1. Validator: enrichment correctness
# ---------------------------------------------------------------------------


class TestValidatorEnrichment:
    """The hub_validator must produce a complete enriched payload from a
    raw TF, including derived poles, stability, system type, and SS form."""

    def test_validator_succeeds(self, enriched_hub):
        assert enriched_hub is not None
        assert enriched_hub.get("source") == "tf"
        assert enriched_hub.get("domain") == "ct"

    def test_dimensions_inferred(self, enriched_hub):
        dims = enriched_hub.get("dimensions") or {}
        assert dims.get("n") == 2
        assert dims.get("m") == 1
        assert dims.get("p") == 1

    def test_poles_at_minus_one_plus_minus_3j(self, enriched_hub):
        poles = enriched_hub.get("poles") or []
        assert len(poles) == 2
        for p in poles:
            assert abs(p["real"] - EXPECTED_POLE_REAL) < 1e-6
            assert abs(abs(p["imag"]) - EXPECTED_POLE_IMAG_ABS) < 1e-6

    def test_stable_and_type_zero(self, enriched_hub):
        assert enriched_hub.get("stable") is True
        assert enriched_hub.get("system_type") == 0
        assert enriched_hub.get("order") == 2

    def test_ss_realization_eigenvalues_match_poles(self, enriched_hub):
        import numpy as np
        ss = enriched_hub.get("ss")
        assert ss is not None
        A = np.array(ss["A"])
        eigs = np.linalg.eigvals(A)
        # eigenvalues of A should be the poles
        for ev in eigs:
            assert abs(ev.real - EXPECTED_POLE_REAL) < 1e-6
            assert abs(abs(ev.imag) - EXPECTED_POLE_IMAG_ABS) < 1e-6


# ---------------------------------------------------------------------------
# 2. State endpoint: has_custom_from_hub_data flag injection
# ---------------------------------------------------------------------------


# Sims with custom from_hub_data overrides (must have the flag = True).
# Producer-only sims return False from from_hub_data but still count as
# overriding the base method.
EXPECTED_CUSTOM_FLAG = {
    "block_diagram_builder": True,    # producer-only
    "dt_system_representations": True,# custom DT consumer (Fix 06)
    "laplace_roc": True,              # producer-only
    "mimo_design_studio": True,       # custom MIMO consumer (Fix 04)
    "nonlinear_control_lab": True,    # producer-only
    "ode_laplace_solver": True,       # custom CT consumer (Fix 06)
    "routh_hurwitz": True,            # producer-only
    "second_order_system": True,      # producer-only
    "signal_flow_scope": True,        # block_diagram-only consumer (BUG-057)
    "z_transform_roc": True,          # producer-only DT
    # Standard Tier 1 — no override
    "controller_tuning_lab": False,
    "eigenfunction_tester": False,
    "lead_lag_designer": False,
    "nyquist_bode_comparison": False,
    "nyquist_stability": False,
    "root_locus": False,
    "state_space_analyzer": False,
    "steady_state_error": False,
    "vector_freq_response": False,
}


class TestHasCustomFromHubDataFlag:
    """The state endpoint must inject metadata.has_custom_from_hub_data so
    the frontend's hub auto-pull can choose between the custom and standard
    injection paths."""

    @pytest.mark.parametrize("sim_id,expected", sorted(EXPECTED_CUSTOM_FLAG.items()))
    def test_flag_value(self, client, sim_id, expected):
        resp = client.get(f"/api/simulations/{sim_id}/state")
        assert resp.status_code == 200, f"GET state failed: {resp.text}"
        body = resp.json()
        meta = (body.get("data") or {}).get("metadata") or {}
        assert meta.get("has_custom_from_hub_data") is expected, (
            f"{sim_id}: expected has_custom_from_hub_data={expected} "
            f"but got {meta.get('has_custom_from_hub_data')}"
        )


# ---------------------------------------------------------------------------
# 3. Path A — custom from_hub_data via execute API
# ---------------------------------------------------------------------------


class TestPathACustomFromHubData:
    """Sims with has_custom_from_hub_data=True go through the execute API
    action=from_hub_data, and the backend's override is the single source
    of truth for injection."""

    def test_mimo_design_studio_accepts_siso_tf(self, client, enriched_hub):
        """SISO TF should be converted to controller-canonical SS via tf2ss."""
        resp = client.post(
            "/api/simulations/mimo_design_studio/execute",
            json={"action": "from_hub_data", "params": {"hub_data": enriched_hub}},
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        params = (resp.json().get("data") or {}).get("parameters") or {}
        assert params.get("preset") == "custom"
        assert params.get("matrix_a")  # non-empty
        assert params.get("matrix_b")
        assert params.get("matrix_c")
        assert params.get("matrix_d")

    def test_mimo_design_studio_eigenvalues_match_canonical_poles(
        self, client, enriched_hub
    ):
        """The realized SS A matrix's eigenvalues must match the original
        TF's poles to within 1e-6."""
        import numpy as np
        from simulations.mimo_design_studio import MIMODesignStudioSimulator
        # Use the simulator instance to parse the matrix string back
        sim = MIMODesignStudioSimulator("test")
        sim.initialize()
        resp = client.post(
            "/api/simulations/mimo_design_studio/execute",
            json={"action": "from_hub_data", "params": {"hub_data": enriched_hub}},
        )
        params = (resp.json().get("data") or {}).get("parameters") or {}
        A = sim._parse_matrix(params["matrix_a"], "A")
        eigs = sorted(np.linalg.eigvals(np.array(A)).tolist(),
                      key=lambda z: (z.real, z.imag))
        for ev in eigs:
            assert abs(ev.real - EXPECTED_POLE_REAL) < 1e-6
            assert abs(abs(ev.imag) - EXPECTED_POLE_IMAG_ABS) < 1e-6

    def test_ode_laplace_solver_accepts_ct_tf(self, client, enriched_hub):
        """CT consumer with non-standard input_coeffs/output_coeffs schema."""
        resp = client.post(
            "/api/simulations/ode_laplace_solver/execute",
            json={"action": "from_hub_data", "params": {"hub_data": enriched_hub}},
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        params = (resp.json().get("data") or {}).get("parameters") or {}
        # input_coeffs ← num, output_coeffs ← den (high-power-first)
        assert params.get("input_coeffs") == "10.0"
        assert params.get("output_coeffs") == "1.0, 2.0, 10.0"

    def test_dt_consumer_rejects_ct_payload(self, client, enriched_hub):
        """dt_system_representations is DT-only; a CT TF must be rejected
        with 422 (not silently no-opped)."""
        resp = client.post(
            "/api/simulations/dt_system_representations/execute",
            json={"action": "from_hub_data", "params": {"hub_data": enriched_hub}},
        )
        # BUG-083 (2026-04-17): changed from 422 to 200 + {success:False} so
        # the browser console doesn't log "Failed to load resource" on every
        # sim page that tries auto-hub-import on mount against a producer-only
        # or incompatible consumer. The rejection is semantic, not protocol.
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("success") is False
        assert "not compatible" in (body.get("error") or "").lower()

    @pytest.mark.parametrize("sim_id", [
        "block_diagram_builder",
        "routh_hurwitz",
        "second_order_system",
        "laplace_roc",
        "nonlinear_control_lab",
    ])
    def test_producer_only_sims_reject_with_success_false(self, client, enriched_hub, sim_id):
        """Producer-only sims must reject hub TF pulls with {success: False} —
        that's the whole point of overriding from_hub_data to return False
        instead of inheriting the base method. Post-BUG-083 we return HTTP
        200 + {success: false} (was HTTP 422) to keep the browser console
        clean on auto-import-on-mount."""
        resp = client.post(
            f"/api/simulations/{sim_id}/execute",
            json={"action": "from_hub_data", "params": {"hub_data": enriched_hub}},
        )
        # BUG-083 (2026-04-17): changed from 422 to 200 + {success:False} so
        # the browser console doesn't log "Failed to load resource" on every
        # sim page that tries auto-hub-import on mount against a producer-only
        # or incompatible consumer. The rejection is semantic, not protocol.
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("success") is False
        assert "not compatible" in (body.get("error") or "").lower(), (
            f"{sim_id} should reject CT TF with success=False "
            f"but got error={body.get('error')!r}"
        )

    def test_z_transform_roc_dt_producer_rejects_ct(self, client, enriched_hub):
        """DT producer-only sim rejects CT payload."""
        resp = client.post(
            "/api/simulations/z_transform_roc/execute",
            json={"action": "from_hub_data", "params": {"hub_data": enriched_hub}},
        )
        # BUG-083 (2026-04-17): changed from 422 to 200 + {success:False} so
        # the browser console doesn't log "Failed to load resource" on every
        # sim page that tries auto-hub-import on mount against a producer-only
        # or incompatible consumer. The rejection is semantic, not protocol.
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("success") is False
        assert "not compatible" in (body.get("error") or "").lower()

    def test_signal_flow_scope_rejects_flat_tf(self, client, enriched_hub):
        """SFS only accepts block_diagram payloads, not flat tf — this is
        the BUG-057 contract."""
        resp = client.post(
            "/api/simulations/signal_flow_scope/execute",
            json={"action": "from_hub_data", "params": {"hub_data": enriched_hub}},
        )
        # BUG-083 (2026-04-17): changed from 422 to 200 + {success:False} so
        # the browser console doesn't log "Failed to load resource" on every
        # sim page that tries auto-hub-import on mount against a producer-only
        # or incompatible consumer. The rejection is semantic, not protocol.
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("success") is False
        assert "not compatible" in (body.get("error") or "").lower()


# ---------------------------------------------------------------------------
# 4. Path B — standard frontend mapping via update action
# ---------------------------------------------------------------------------


def _build_standard_hub_params(controls, hub_data):
    """Mirror the frontend's standard-path mapping logic exactly."""
    hub_params = {}
    if hub_data.get("tf"):
        for ctrl in controls:
            name = ctrl.get("name")
            if name in NUM_KEYS:
                hub_params[name] = ", ".join(str(c) for c in hub_data["tf"]["num"])
            if name in DEN_KEYS:
                hub_params[name] = ", ".join(str(c) for c in hub_data["tf"]["den"])
    # Auto-switch preset
    for ctrl in controls:
        name = ctrl.get("name")
        opts = ctrl.get("options") or []
        if name in PRESET_KEYS:
            opt_values = [
                (o.get("value") if isinstance(o, dict) else o) for o in opts
            ]
            if "custom" in opt_values and hub_params:
                hub_params[name] = "custom"
    return hub_params


class TestPathBStandardMapping:
    """Sims with standard schemas go through the frontend's NUM_KEYS/DEN_KEYS
    mapping into update_parameter. Each must end up with the canonical TF
    in its parameters."""

    @pytest.mark.parametrize("sim_id", [
        "controller_tuning_lab",
        "eigenfunction_tester",
        "lead_lag_designer",
        "nyquist_bode_comparison",
        "nyquist_stability",
        "root_locus",
        "state_space_analyzer",
        "steady_state_error",
        "vector_freq_response",
    ])
    def test_standard_path_injects_tf(self, client, enriched_hub, sim_id):
        """The standard frontend path produces a non-empty hub_params dict
        and the update call succeeds with 200."""
        cat_resp = client.get(f"/api/simulations/{sim_id}")
        controls = cat_resp.json().get("controls") or []
        hub_params = _build_standard_hub_params(controls, enriched_hub)
        assert hub_params, (
            f"{sim_id}: standard path produced no params — its schema lacks "
            f"any of NUM_KEYS={NUM_KEYS} / DEN_KEYS={DEN_KEYS}"
        )
        resp = client.post(
            f"/api/simulations/{sim_id}/execute",
            json={"action": "update", "params": hub_params},
        )
        assert resp.status_code == 200, f"update failed: {resp.text}"

    def test_eigenfunction_tester_uses_system_preset(self, client, enriched_hub):
        """Regression for the system_preset bug: eigenfunction_tester uses
        'system_preset' as its preset key (not 'preset' or 'plant_preset').
        The frontend's PRESET_KEYS list must include it so the auto-switch
        flips to 'custom' after injection."""
        cat_resp = client.get("/api/simulations/eigenfunction_tester")
        controls = cat_resp.json().get("controls") or []
        hub_params = _build_standard_hub_params(controls, enriched_hub)
        assert hub_params.get("system_preset") == "custom", (
            "system_preset must be auto-switched to 'custom' so the injected "
            "TF is used instead of the default preset's 1/(s+2)"
        )


# ---------------------------------------------------------------------------
# 5. Math spot-checks: poles propagate correctly through Path B sims
# ---------------------------------------------------------------------------


def _find_field(d, *names):
    if not isinstance(d, dict):
        return None
    for n in names:
        if n in d:
            return d[n]
    for v in d.values():
        if isinstance(v, dict):
            r = _find_field(v, *names)
            if r is not None:
                return r
    return None


def _poles_match_canonical(poles_obj):
    """Normalize various pole shapes and check for -1 +- 3j."""
    if poles_obj is None:
        return False
    if isinstance(poles_obj, list) and poles_obj and isinstance(poles_obj[0], dict):
        return any(
            abs(p.get("real", 0) - EXPECTED_POLE_REAL) < 1e-3
            and abs(abs(p.get("imag", 0)) - EXPECTED_POLE_IMAG_ABS) < 1e-3
            for p in poles_obj
        )
    if isinstance(poles_obj, list) and poles_obj and isinstance(poles_obj[0], (list, tuple)):
        return any(
            abs(p[0] - EXPECTED_POLE_REAL) < 1e-3
            and abs(abs(p[1]) - EXPECTED_POLE_IMAG_ABS) < 1e-3
            for p in poles_obj
        )
    if isinstance(poles_obj, dict) and "real" in poles_obj and "imag" in poles_obj:
        return any(
            abs(r - EXPECTED_POLE_REAL) < 1e-3
            and abs(abs(i) - EXPECTED_POLE_IMAG_ABS) < 1e-3
            for r, i in zip(poles_obj["real"], poles_obj["imag"])
        )
    return False


class TestMathPropagation:
    """For sims that expose poles in their metadata, the canonical TF's
    poles -1 ± 3j must propagate end-to-end through the new flow.

    Not every consumer exposes poles — controller_tuning_lab exposes loop
    margins, lead_lag_designer exposes compensator design, etc. We only
    test the ones that do.
    """

    @pytest.mark.parametrize("sim_id", [
        "eigenfunction_tester",
        "nyquist_bode_comparison",
        "state_space_analyzer",
        "vector_freq_response",
    ])
    def test_poles_match_canonical(self, client, enriched_hub, sim_id):
        cat_resp = client.get(f"/api/simulations/{sim_id}")
        controls = cat_resp.json().get("controls") or []
        hub_params = _build_standard_hub_params(controls, enriched_hub)
        resp = client.post(
            f"/api/simulations/{sim_id}/execute",
            json={"action": "update", "params": hub_params},
        )
        assert resp.status_code == 200
        meta = ((resp.json().get("data") or {}).get("metadata") or {})
        poles = _find_field(meta, "poles", "open_loop_poles", "eigenvalues")
        assert _poles_match_canonical(poles), (
            f"{sim_id}: expected poles at -1 ± 3j but got {poles}"
        )
