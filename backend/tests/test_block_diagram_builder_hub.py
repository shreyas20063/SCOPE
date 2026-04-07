"""BDB hub contract tests.

Block Diagram Builder is producer-only with respect to the System Hub:
it pushes constructed diagrams (and their computed transfer functions)
via to_hub_data, but it does NOT auto-import TFs from the hub. Auto-
importing would require either replacing the current canvas (destroying
user work) or auto-realizing a canonical-form diagram — both are
opinionated UX choices that should be explicit user actions, not
silent side-effects of a hub pull.

This file pins the producer-only contract so a future 'load TF from
hub' feature can't accidentally change BDB's auto-pull behavior
without a deliberate test update.
"""

from simulations.block_diagram_builder import BlockDiagramSimulator


CT_TF_PAYLOAD = {
    "source": "tf",
    "domain": "ct",
    "tf": {"num": [1.0], "den": [1.0, 3.0, 2.0]},
    "dimensions": {"n": 2, "m": 1, "p": 1},
}

DT_TF_PAYLOAD = {
    "source": "tf",
    "domain": "dt",
    "tf": {"num": [1.0], "den": [1.0, -0.5]},
    "dimensions": {"n": 1, "m": 1, "p": 1},
}


class TestBdbProducerOnly:
    def test_from_hub_data_returns_false_on_ct_tf(self):
        bdb = BlockDiagramSimulator("bdb")
        bdb.initialize()
        assert bdb.from_hub_data(CT_TF_PAYLOAD) is False

    def test_from_hub_data_returns_false_on_dt_tf(self):
        bdb = BlockDiagramSimulator("bdb")
        bdb.initialize()
        assert bdb.from_hub_data(DT_TF_PAYLOAD) is False

    def test_from_hub_data_returns_false_on_empty_payload(self):
        bdb = BlockDiagramSimulator("bdb")
        bdb.initialize()
        assert bdb.from_hub_data({}) is False

    def test_blocks_unchanged_after_pull(self):
        """A hub pull must not mutate the canvas — that's the whole point
        of being producer-only. The user's in-progress work is sacred."""
        bdb = BlockDiagramSimulator("bdb")
        bdb.initialize()
        blocks_before = {k: dict(v) for k, v in bdb.blocks.items()}
        connections_before = [dict(c) for c in bdb.connections]

        bdb.from_hub_data(CT_TF_PAYLOAD)

        assert bdb.blocks == blocks_before
        assert bdb.connections == connections_before

    def test_blocks_unchanged_with_user_diagram(self):
        """Same as above but with a non-empty user diagram on the canvas."""
        bdb = BlockDiagramSimulator("bdb")
        bdb.initialize()
        bdb.blocks = {
            "b_in": {"id": "b_in", "type": "input", "position": {"x": 50, "y": 200}},
            "b_gain": {"id": "b_gain", "type": "gain", "position": {"x": 250, "y": 200}, "gain": 2.0},
            "b_out": {"id": "b_out", "type": "output", "position": {"x": 450, "y": 200}},
        }
        bdb.connections = [
            {"from_block": "b_in", "to_block": "b_gain", "from_port": 0, "to_port": 0},
            {"from_block": "b_gain", "to_block": "b_out", "from_port": 1, "to_port": 0},
        ]
        blocks_snapshot = {k: dict(v) for k, v in bdb.blocks.items()}
        connections_snapshot = [dict(c) for c in bdb.connections]

        result = bdb.from_hub_data(CT_TF_PAYLOAD)

        assert result is False
        assert bdb.blocks == blocks_snapshot
        assert bdb.connections == connections_snapshot

    def test_to_hub_data_still_works(self):
        """Producer side must remain functional — we're only overriding
        the consumer direction."""
        bdb = BlockDiagramSimulator("bdb")
        bdb.initialize()
        # to_hub_data on a fresh empty diagram returns a dict with the
        # block_diagram payload but no 'tf' key (nothing computed yet).
        # It must not raise.
        result = bdb.to_hub_data()
        assert result is not None
        assert result.get("source") == "block_diagram"
