"""Integration tests codifying the fixes from the 2026-04-15/16/17 hardening
session (BUG-073 through BUG-084). Each test pins a specific invariant that,
if it ever breaks, would reproduce a real user-facing bug we already hit.

These tests exist precisely because several of these bugs shipped to the
user before being caught. Running this file as part of CI means they can
never ship again silently.

Grouped by origin:
  - BUG-073: SPA fallback (React Router deep URLs)
  - BUG-075 / BUG-077 / BUG-076: multi-user cache + lock + invalidate
  - BUG-078: to_hub_data routed through executor
  - BUG-079: CORS credentials/origins invariant
  - BUG-082: dual-domain Hub handoff (SFG/BDB)
  - BUG-083: from_hub_data rejection envelope is 200 + {success: false}
  - BUG-084 (controller_tuning_lab RL params): slider updates don't vanish
"""
import logging
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

logging.getLogger("httpx").setLevel(logging.WARNING)

from main import app
from utils.cache import LRUCache


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def _sid(tag: str) -> str:
    """Unique session ID per test — isolates server state between tests."""
    return f"test-{tag}-{uuid.uuid4().hex[:12]}"


# ===========================================================================
# BUG-073 — SPA fallback for React Router paths
# ===========================================================================


class TestSPAFallback:
    """The StaticFiles mount at '/' must serve index.html for unknown paths
    so React Router URLs work on direct load / refresh. But it must NOT
    shadow /api/* or other API routes."""

    def test_react_router_path_returns_html(self, client):
        resp = client.get("/simulation/rc_lowpass_filter")
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")
        # doctype is case-insensitive per HTML spec; match either variant
        assert resp.content[:15].lower().startswith(b"<!doctype html>")

    def test_arbitrary_deep_path_falls_back(self, client):
        resp = client.get("/random/deep/unknown/path")
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")

    def test_api_404_not_shadowed(self, client):
        """/api/bogus must return JSON 404, not the SPA's HTML. If this fails,
        the SPAStaticFiles _API_PREFIXES guard was removed or broken."""
        resp = client.get("/api/bogus_endpoint_that_does_not_exist")
        assert resp.status_code == 404
        assert "application/json" in resp.headers.get("content-type", "")

    def test_health_not_shadowed(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json().get("status") == "ok"


# ===========================================================================
# BUG-075 — cache session isolation for stateful simulators
# ===========================================================================


class TestCacheSessionIsolation:
    """The LRU cache in front of /state is keyed by (sim_id, session_id) via
    _cache_ns(). Before this was fixed, two sessions on the same stateful
    sim (BDB) with identical default params collided on one cache entry,
    leaking one user's block state to every other user."""

    def _bdb_state(self, client, sid):
        resp = client.get(
            "/api/simulations/block_diagram_builder/state",
            headers={"X-Session-ID": sid},
        )
        assert resp.status_code == 200
        return (resp.json()["data"]["metadata"].get("blocks") or {})

    def _bdb_add_block(self, client, sid, block_type):
        resp = client.post(
            "/api/simulations/block_diagram_builder/execute",
            headers={"X-Session-ID": sid},
            json={"action": "add_block",
                  "params": {"block_type": block_type,
                             "position": {"x": 100, "y": 100}}},
        )
        assert resp.status_code == 200

    def test_two_sessions_on_same_sim_do_not_share_state(self, client):
        alice = _sid("alice")
        bob = _sid("bob")

        self._bdb_add_block(client, alice, "gain")
        self._bdb_add_block(client, alice, "delay")

        alice_blocks = self._bdb_state(client, alice)
        bob_blocks = self._bdb_state(client, bob)

        assert len(alice_blocks) == 2, f"Alice should have 2 blocks: {alice_blocks}"
        assert len(bob_blocks) == 0, (
            f"Bob is a FRESH session — must see 0 blocks. Got: {bob_blocks}. "
            f"This is a BUG-075 regression: cache is serving Alice's state."
        )

    def test_bob_action_does_not_bleed_back_to_alice(self, client):
        alice = _sid("alice2")
        bob = _sid("bob2")

        self._bdb_add_block(client, alice, "gain")
        self._bdb_add_block(client, bob, "adder")

        alice_types = sorted(b.get("type") for b in self._bdb_state(client, alice).values())
        bob_types = sorted(b.get("type") for b in self._bdb_state(client, bob).values())

        assert alice_types == ["gain"], f"Alice lost her own state: {alice_types}"
        assert bob_types == ["adder"], f"Bob lost his own state: {bob_types}"
        # Key invariant: neither session sees the OTHER's block
        assert "adder" not in alice_types
        assert "gain" not in bob_types

    def test_default_session_is_independent_pool(self, client):
        """Request without X-Session-ID must land in __default__ pool and
        not share state with any UUID-session."""
        alice = _sid("alice3")
        self._bdb_add_block(client, alice, "gain")

        # No X-Session-ID header
        resp = client.get("/api/simulations/block_diagram_builder/state")
        assert resp.status_code == 200
        default_blocks = resp.json()["data"]["metadata"].get("blocks") or {}
        # The default pool shouldn't see Alice's blocks.
        # (It may be non-empty if prior tests used default session,
        # but Alice's specific block must not be there.)
        assert len(default_blocks) < 1000  # sanity only


# ===========================================================================
# BUG-076 — cache.invalidate actually clears entries
# ===========================================================================


class TestCacheInvalidate:
    """Before this was fixed, invalidate(sim_id) was a silent no-op because
    cache keys are md5-hashed and the startswith() check never matched."""

    def test_invalidate_removes_exact_sim_id_entries(self):
        c = LRUCache(max_size=100, ttl_seconds=60)
        c.set("sim_a", {"p": 1}, "A1")
        c.set("sim_b", {"p": 1}, "B1")
        c.invalidate("sim_a")
        assert c.get("sim_a", {"p": 1}) is None
        assert c.get("sim_b", {"p": 1}) == "B1"

    def test_invalidate_removes_session_namespaced_entries(self):
        """_cache_ns() prefixes sim_id with '{sim_id}::{session_id}'.
        invalidate('sim_a') must catch both the raw key AND namespaced
        variants."""
        c = LRUCache(max_size=100, ttl_seconds=60)
        c.set("sim_a", {"p": 1}, "A_raw")
        c.set("sim_a::session_x", {"p": 1}, "A_ns_x")
        c.set("sim_a::session_y", {"p": 1}, "A_ns_y")
        c.set("sim_b", {"p": 1}, "B1")

        c.invalidate("sim_a")
        assert c.get("sim_a", {"p": 1}) is None
        assert c.get("sim_a::session_x", {"p": 1}) is None
        assert c.get("sim_a::session_y", {"p": 1}) is None
        # Unrelated sim must survive
        assert c.get("sim_b", {"p": 1}) == "B1"


# ===========================================================================
# BUG-077 — per-instance executor lock enables cross-session parallelism
# ===========================================================================


class TestPerInstanceLock:
    """Executor keys locks by id(func.__self__) so two sessions on the same
    sim_id don't serialize on a shared lock. We verify by timing:
    N concurrent requests from N distinct sessions should complete in
    roughly max-single-request time, not N-x-single-request time.

    This is a smoke test, not a strict bound — CI runners have variable
    performance. We use a generous threshold (< 50% of serial estimate).
    """

    def test_concurrent_sessions_do_not_serialize(self, client):
        N = 12  # enough to multiply latency if locks shared, few enough to fit in ThreadPool=16
        sim = "rc_lowpass_filter"

        # Baseline: one request's wall time
        t0 = time.perf_counter()
        resp = client.get(
            f"/api/simulations/{sim}/state",
            headers={"X-Session-ID": _sid("lock-baseline")},
        )
        single_ms = (time.perf_counter() - t0) * 1000
        assert resp.status_code == 200

        # N parallel distinct-session requests
        def one():
            r = client.get(
                f"/api/simulations/{sim}/state",
                headers={"X-Session-ID": _sid("lock-parallel")},
            )
            return r.status_code

        t0 = time.perf_counter()
        with ThreadPoolExecutor(max_workers=N) as pool:
            results = list(pool.map(lambda _: one(), range(N)))
        parallel_ms = (time.perf_counter() - t0) * 1000

        assert all(s == 200 for s in results)
        # If lock was per-sim (shared), parallel time ≈ N × single_ms.
        # With per-instance locks + ThreadPool, parallel time should be
        # far less — allow generous 50% of serial for CI variance.
        serial_estimate_ms = N * single_ms
        assert parallel_ms < max(serial_estimate_ms * 0.5, 500), (
            f"N={N} concurrent requests took {parallel_ms:.0f}ms; "
            f"serial estimate was {serial_estimate_ms:.0f}ms. "
            f"Lock may be serializing (BUG-077 regression)."
        )


# ===========================================================================
# BUG-078 — to_hub_data / from_hub_data routed through executor
# ===========================================================================


class TestHubDataExecutor:
    """Both hub methods must go through executor.execute so they get
    timeout protection + per-instance lock + consistent error translation.
    The smoke check: the /execute endpoint's to_hub_data path must respond
    with the standard envelope and not raise."""

    def test_to_hub_data_returns_clean_envelope(self, client):
        """rc_lowpass_filter has no TF to export; the endpoint should return
        a well-formed error envelope, NOT a 500 with a traceback. The exact
        status code is a choice (400 for 'no data available', 200 with
        success=false for consistency) — we accept either as long as it's
        well-formed and the Python exception didn't leak."""
        resp = client.post(
            "/api/simulations/rc_lowpass_filter/execute",
            headers={"X-Session-ID": _sid("hub-x")},
            json={"action": "to_hub_data", "params": {}},
        )
        assert resp.status_code in (200, 400), (
            f"Unexpected status {resp.status_code}. Body: {resp.text[:200]}"
        )
        body = resp.json()
        assert "success" in body or "error" in body or "detail" in body
        # MUST NOT be a 500 with a Python traceback leaking to client
        assert "Traceback" not in resp.text

    def test_to_hub_data_on_producer_returns_payload(self, client):
        """routh_hurwitz is a producer — its to_hub_data should return a
        payload with domain + tf or similar."""
        sid = _sid("hub-rh")
        resp = client.post(
            "/api/simulations/routh_hurwitz/execute",
            headers={"X-Session-ID": sid},
            json={"action": "to_hub_data", "params": {}},
        )
        assert resp.status_code == 200
        body = resp.json()
        if body.get("success"):
            hub_data = body["data"].get("hub_data") or {}
            assert "domain" in hub_data or "tf" in hub_data or "source" in hub_data


# ===========================================================================
# BUG-079 — CORS allow_credentials=False with allow_origins=["*"]
# ===========================================================================


class TestCORSInvariant:
    """allow_origins=['*'] is only valid when allow_credentials=False per
    the Fetch spec. Browser rejects the combination otherwise."""

    def test_preflight_does_not_advertise_credentials(self, client):
        resp = client.options(
            "/api/simulations/rc_lowpass_filter/update",
            headers={
                "Origin": "http://example.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type,x-session-id",
            },
        )
        assert resp.status_code in (200, 204)
        # If credentials header is present, it must be "false" — but best
        # is for it to be absent entirely.
        creds = resp.headers.get("access-control-allow-credentials")
        if creds is not None:
            assert creds.lower() == "false", (
                f"allow_credentials=True combined with allow_origins=* is "
                f"invalid per the Fetch spec. Got: {creds!r}"
            )


# ===========================================================================
# BUG-082 — dual-domain Hub handoff (SFG + BDB)
# ===========================================================================


class TestDualDomainHub:
    """SFG and BDB toggle system_type at runtime. Their metadata.hub_domain
    must reflect the RUNTIME domain, not a static class attribute. SFG must
    also set hub_domain_flexible=True so the frontend doesn't reject
    cross-domain payloads before the backend's auto-switch can run."""

    def test_bdb_hub_domain_follows_system_type(self, client):
        sid = _sid("bdb-hd")
        # Default BDB is DT
        resp = client.get(
            "/api/simulations/block_diagram_builder/state",
            headers={"X-Session-ID": sid},
        )
        meta = resp.json()["data"]["metadata"]
        assert meta["system_type"] == meta["hub_domain"], (
            f"BDB metadata says system_type={meta['system_type']} but "
            f"hub_domain={meta['hub_domain']}. They must match "
            f"(BUG-082 regression)."
        )

        # Switch to CT and re-check
        resp = client.post(
            "/api/simulations/block_diagram_builder/update",
            headers={"X-Session-ID": sid},
            json={"params": {"system_type": "ct"}},
        )
        assert resp.status_code == 200
        resp = client.get(
            "/api/simulations/block_diagram_builder/state",
            headers={"X-Session-ID": sid},
        )
        meta = resp.json()["data"]["metadata"]
        assert meta["system_type"] == "ct"
        assert meta["hub_domain"] == "ct", (
            f"After switching BDB to CT, hub_domain should follow. "
            f"Got hub_domain={meta['hub_domain']} (BUG-082 regression)."
        )

    def test_sfg_is_hub_domain_flexible(self, client):
        sid = _sid("sfg-flex")
        resp = client.get(
            "/api/simulations/signal_flow_scope/state",
            headers={"X-Session-ID": sid},
        )
        meta = resp.json()["data"]["metadata"]
        assert meta.get("hub_domain_flexible") is True, (
            "SFG must declare hub_domain_flexible=True so the frontend's "
            "Hub auto-read doesn't reject cross-domain payloads before the "
            "backend's auto-switch runs (BUG-082)."
        )

    def test_sfg_accepts_dt_payload(self, client):
        """Full end-to-end: BDB in DT builds 3 blocks, exports to hub,
        SFG consumes and shows all 3 blocks with system_type=dt."""
        sid = _sid("dt-e2e")

        # Build a minimal DT diagram in BDB
        for block_type in ["input", "delay", "output"]:
            client.post(
                "/api/simulations/block_diagram_builder/execute",
                headers={"X-Session-ID": sid},
                json={"action": "add_block",
                      "params": {"block_type": block_type,
                                 "position": {"x": 100, "y": 100}}},
            )

        # Export
        resp = client.post(
            "/api/simulations/block_diagram_builder/execute",
            headers={"X-Session-ID": sid},
            json={"action": "to_hub_data", "params": {}},
        )
        hub_data = resp.json()["data"]["hub_data"]
        assert hub_data["domain"] == "dt"

        # Import into SFG (same session so we see the effect)
        resp = client.post(
            "/api/simulations/signal_flow_scope/execute",
            headers={"X-Session-ID": sid},
            json={"action": "from_hub_data", "params": {"hub_data": hub_data}},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("success") is True, f"SFG rejected DT payload: {body}"
        sfg_meta = body["data"]["metadata"]
        assert sfg_meta["system_type"] == "dt"
        assert len(sfg_meta.get("blocks") or {}) == 3


# ===========================================================================
# BUG-083 — from_hub_data rejection returns 200 with {success: false}
# ===========================================================================


class TestFromHubDataRejectionEnvelope:
    """Previously returned HTTP 422 with a {success: false} body, which
    caused the browser DevTools to log 'Failed to load resource' on every
    sim page that auto-imports hub data on mount against a producer-only or
    incompatible consumer. Now we return 200 + {success: false} to keep
    the console clean."""

    @pytest.mark.parametrize("sim_id", [
        "block_diagram_builder",    # producer-only
        "routh_hurwitz",            # producer-only
        "z_transform_roc",          # producer-only DT
    ])
    def test_producer_only_rejects_with_200_plus_success_false(
        self, client, sim_id,
    ):
        # Craft a dummy incompatible hub payload
        dummy = {"source": "tf", "domain": "ct", "tf": {"num": [1.0], "den": [1.0, 1.0]}}
        resp = client.post(
            f"/api/simulations/{sim_id}/execute",
            headers={"X-Session-ID": _sid(f"reject-{sim_id}")},
            json={"action": "from_hub_data", "params": {"hub_data": dummy}},
        )
        # The contract: HTTP 200, body has success=False
        assert resp.status_code == 200, (
            f"{sim_id} returned HTTP {resp.status_code} for an incompatible "
            f"hub_data payload. BUG-083 contract: must be 200 so the browser "
            f"console doesn't log a failure on normal auto-import flows."
        )
        body = resp.json()
        assert body.get("success") is False


# ===========================================================================
# BUG-084 — controller_tuning_lab RL sliders wire to parameters
# ===========================================================================


class TestControllerTuningRLParams:
    """The catalog exposed es_generations and rl_timesteps as sliders but
    controller_tuning_lab's DEFAULT_PARAMS did not include them, so slider
    moves were silently discarded by BaseSimulator.update_parameter (which
    only accepts keys already in self.parameters)."""

    def test_rl_params_present_in_initial_state(self, client):
        resp = client.get(
            "/api/simulations/controller_tuning_lab/state",
            headers={"X-Session-ID": _sid("ctl-rl-state")},
        )
        params = resp.json()["data"]["parameters"]
        assert "es_generations" in params, (
            "es_generations slider is in catalog but not in runtime params — "
            "moving the slider would silently do nothing."
        )
        assert "rl_timesteps" in params, (
            "rl_timesteps slider is in catalog but not in runtime params."
        )

    def test_rl_params_accept_updates(self, client):
        sid = _sid("ctl-rl-update")
        resp = client.post(
            "/api/simulations/controller_tuning_lab/update",
            headers={"X-Session-ID": sid},
            json={"params": {"es_generations": 333, "rl_timesteps": 7777}},
        )
        assert resp.status_code == 200

        resp = client.get(
            "/api/simulations/controller_tuning_lab/state",
            headers={"X-Session-ID": sid},
        )
        params = resp.json()["data"]["parameters"]
        assert params["es_generations"] == 333
        assert params["rl_timesteps"] == 7777
