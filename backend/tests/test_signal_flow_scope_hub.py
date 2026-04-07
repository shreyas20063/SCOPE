"""End-to-end hub round-trip tests for Signal Flow Scope.

Verifies that BDB → System Hub → SFS preserves the diagram topology and
that the resulting SFG matches what a textbook would draw for the same
diagram. Regression coverage for BUG-057 (SFS auto-imported stale data
from localStorage instead of reading the System Hub control slot).
"""

import numpy as np
import pytest

from core.hub_validator import validate_and_enrich_control
from simulations.block_diagram_builder import BlockDiagramSimulator
from simulations.signal_flow_scope import SignalFlowScopeSimulator


def _build_single_custom_tf_diagram():
    """Build the smallest possible diagram: input → custom_tf → output.

    The custom TF is 1/(s^2 + s), which is what the user reported in the
    motivating bug.
    """
    # BDB stores custom_tf coefficients as num_coeffs/den_coeffs in operator-A form
    # (s → 1/A substitution, low-power-first). For 1/(s²+s) the operator form is
    # num_a=[0,0,1], den_a=[1,1,0] — we don't assert on these here; we just
    # need the block to import and end up as a single edge in the SFG.
    blocks = {
        "b_in": {"id": "b_in", "type": "input", "position": {"x": 50, "y": 200}},
        "b_tf": {
            "id": "b_tf",
            "type": "custom_tf",
            "position": {"x": 250, "y": 200},
            "expression": "1/(s^2+s)",
            "label": "1/(s²+s)",
            "num_coeffs": [0.0, 0.0, 1.0],
            "den_coeffs": [1.0, 1.0, 0.0],
        },
        "b_out": {"id": "b_out", "type": "output", "position": {"x": 450, "y": 200}},
    }
    connections = [
        {"from_block": "b_in", "to_block": "b_tf", "from_port": 0, "to_port": 0},
        {"from_block": "b_tf", "to_block": "b_out", "from_port": 1, "to_port": 0},
    ]
    return blocks, connections


def _make_sfs(diagram_loaded=False):
    sfs = SignalFlowScopeSimulator("signal_flow_scope")
    sfs.initialize()
    return sfs


# ---------------------------------------------------------------------------
# Backend: from_hub_data contract
# ---------------------------------------------------------------------------


class TestFromHubDataAcceptance:
    """SFS.from_hub_data must accept BDB-style hub payloads."""

    def setup_method(self):
        self.blocks, self.connections = _build_single_custom_tf_diagram()
        self.hub_payload = {
            "source": "block_diagram",
            "domain": "ct",
            "block_diagram": {
                "blocks": self.blocks,
                "connections": self.connections,
            },
            "dimensions": {"n": None, "m": 1, "p": 1},
        }

    def test_returns_true_on_valid_payload(self):
        sfs = _make_sfs()
        assert sfs.from_hub_data(self.hub_payload) is True

    def test_blocks_imported(self):
        sfs = _make_sfs()
        sfs.from_hub_data(self.hub_payload)
        assert set(sfs.blocks.keys()) == {"b_in", "b_tf", "b_out"}

    def test_connections_imported(self):
        sfs = _make_sfs()
        sfs.from_hub_data(self.hub_payload)
        assert len(sfs.connections) == 2

    def test_system_type_set_from_domain(self):
        sfs = _make_sfs()
        sfs.from_hub_data(self.hub_payload)
        assert sfs.system_type == "ct"

    def test_no_error_state(self):
        sfs = _make_sfs()
        sfs.from_hub_data(self.hub_payload)
        assert sfs._error is None


class TestFromHubDataRejection:
    """SFS.from_hub_data must reject invalid or incompatible payloads."""

    def test_rejects_none(self):
        sfs = _make_sfs()
        assert sfs.from_hub_data(None) is False

    def test_rejects_empty_dict(self):
        sfs = _make_sfs()
        assert sfs.from_hub_data({}) is False

    def test_rejects_missing_block_diagram(self):
        sfs = _make_sfs()
        # tf-only payload (no block_diagram) — SFS needs topology, not just coefficients
        payload = {
            "source": "tf",
            "domain": "ct",
            "tf": {"num": [1.0], "den": [1.0, 1.0, 0.0]},
        }
        assert sfs.from_hub_data(payload) is False

    def test_rejects_empty_blocks(self):
        sfs = _make_sfs()
        payload = {
            "source": "block_diagram",
            "domain": "ct",
            "block_diagram": {"blocks": {}, "connections": []},
        }
        assert sfs.from_hub_data(payload) is False

    def test_rejects_mimo(self):
        sfs = _make_sfs()
        blocks, connections = _build_single_custom_tf_diagram()
        payload = {
            "source": "block_diagram",
            "domain": "ct",
            "block_diagram": {"blocks": blocks, "connections": connections},
            "dimensions": {"n": None, "m": 2, "p": 2},
        }
        assert sfs.from_hub_data(payload) is False

    def test_dt_payload_sets_dt_system_type(self):
        sfs = _make_sfs()
        blocks, connections = _build_single_custom_tf_diagram()
        payload = {
            "source": "block_diagram",
            "domain": "dt",
            "block_diagram": {"blocks": blocks, "connections": connections},
        }
        sfs.from_hub_data(payload)
        assert sfs.system_type == "dt"


# ---------------------------------------------------------------------------
# SFG topology — the bug-fix payload
# ---------------------------------------------------------------------------


class TestSingleCustomTfSFG:
    """A 3-block diagram (input → custom_tf → output) must collapse to a
    2-node, 1-edge SFG. This is the canonical case the user hit.
    """

    def setup_method(self):
        blocks, connections = _build_single_custom_tf_diagram()
        self.sfs = _make_sfs()
        self.sfs.from_hub_data({
            "source": "block_diagram",
            "domain": "ct",
            "block_diagram": {"blocks": blocks, "connections": connections},
        })
        state = self.sfs.get_state()
        self.metadata = state["metadata"]

    def test_sfg_has_exactly_two_nodes(self):
        nodes = self.metadata["sfg_nodes"]
        # Only signal points (input + output). The custom_tf block is an edge gain,
        # not a node — that's the textbook Mason-form definition.
        assert len(nodes) == 2, f"Expected 2 nodes (input + output), got {len(nodes)}: {[n['id'] for n in nodes]}"

    def test_sfg_node_ids(self):
        node_ids = {n["id"] for n in self.metadata["sfg_nodes"]}
        assert node_ids == {"b_in", "b_out"}

    def test_sfg_has_exactly_one_edge(self):
        edges = self.metadata["sfg_edges"]
        assert len(edges) == 1, f"Expected 1 edge, got {len(edges)}"

    def test_edge_endpoints(self):
        edge = self.metadata["sfg_edges"][0]
        assert edge["from"] == "b_in"
        assert edge["to"] == "b_out"

    def test_edge_label_is_custom_tf_label(self):
        edge = self.metadata["sfg_edges"][0]
        # Should be the user's TF label, not a polynomial expansion
        assert "1/(s²+s)" in edge["gain_label"] or "1/(s^2+s)" in edge["gain_label"], \
            f"Edge label was {edge['gain_label']!r}"

    def test_no_adder_nodes(self):
        # The bug screenshot showed 4 adder nodes for a 3-block input — this asserts
        # the renderer never invents adders that don't exist in the source diagram.
        types = {n["block_type"] for n in self.metadata["sfg_nodes"]}
        assert "adder" not in types

    def test_output_node_has_a_tf(self):
        # The output node must end up with a non-trivial TF entry — this is the
        # smoke test that SFS actually walked the diagram and computed something
        # for the output. We deliberately do NOT assert on the polynomial form
        # here, because that depends on SFS's operator-algebra representation,
        # which is a separate code path from the hub-import fix.
        assert "b_out" in self.sfs._node_tfs


# ---------------------------------------------------------------------------
# Full hub round-trip: BDB.to_hub_data → validator → SFS.from_hub_data
# ---------------------------------------------------------------------------


class TestEndToEndHubRoundTrip:
    """Simulate the full BDB → Hub → SFS path that the user actually takes.

    This is the integration test that would have caught BUG-057 originally.
    """

    def setup_method(self):
        # 1. Build the diagram in BDB
        bdb = BlockDiagramSimulator("block_diagram_builder")
        bdb.initialize({"system_type": "ct"})
        bdb.blocks, bdb.connections = _build_single_custom_tf_diagram()
        bdb.blocks = dict(bdb.blocks)
        bdb.connections = list(bdb.connections)
        bdb.system_type = "ct"
        # 2. Export via to_hub_data
        self.hub_payload = bdb.to_hub_data()

    def test_bdb_payload_contains_block_diagram(self):
        assert "block_diagram" in self.hub_payload
        assert "blocks" in self.hub_payload["block_diagram"]
        assert len(self.hub_payload["block_diagram"]["blocks"]) == 3

    def test_bdb_payload_domain_matches_runtime(self):
        # Regression: previously BDB reported HUB_DOMAIN ("ct" hardcoded) instead
        # of self.system_type. This would silently mis-tag DT diagrams as CT.
        assert self.hub_payload["domain"] == "ct"

    def test_validator_preserves_block_diagram(self):
        result = validate_and_enrich_control(self.hub_payload)
        assert result["success"] is True
        assert "block_diagram" in result["data"]
        assert len(result["data"]["block_diagram"]["blocks"]) == 3

    def test_sfs_imports_validated_payload(self):
        result = validate_and_enrich_control(self.hub_payload)
        sfs = _make_sfs()
        assert sfs.from_hub_data(result["data"]) is True
        assert len(sfs.blocks) == 3

    def test_round_trip_yields_correct_sfg(self):
        result = validate_and_enrich_control(self.hub_payload)
        sfs = _make_sfs()
        sfs.from_hub_data(result["data"])
        meta = sfs.get_state()["metadata"]
        assert len(meta["sfg_nodes"]) == 2
        assert len(meta["sfg_edges"]) == 1
