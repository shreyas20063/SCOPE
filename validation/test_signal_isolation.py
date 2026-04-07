"""Signal isolation / non-mutation tests for MIMO compute_tf.

The MIMO compute_tf path must not mutate sim.blocks. An earlier
implementation zeroed out input blocks to compute per-input transfer
functions, which corrupted shared state. These tests pin the
non-mutation contract so future refactors can't regress it.
"""

import copy

import numpy as np
import pytest

from conftest import assert_poly_equal

from test_shared_delta import _get_block_id, _compute_and_get_result


class TestSignalIsolation:
    """MIMO compute_tf must not mutate sim.blocks."""

    def test_blocks_unchanged_after_siso(self, bdb_simulator):
        """SISO negative feedback diagram: blocks dict must be byte-identical
        before and after compute_tf.
            in -> adder(+,-) -> G(2) -> j -> out
            j  -> H(0.5) -> adder(1, "-")
        """
        sim = bdb_simulator

        sim.handle_action("add_block", {"block_type": "input"})
        sim.handle_action("add_block", {"block_type": "adder", "signs": ["+", "-", "+"]})
        sim.handle_action("add_block", {"block_type": "gain", "value": 2.0})
        sim.handle_action("add_block", {"block_type": "junction"})
        sim.handle_action("add_block", {"block_type": "gain", "value": 0.5})
        sim.handle_action("add_block", {"block_type": "output"})

        in1 = _get_block_id(sim, "input", 1)
        adder = _get_block_id(sim, "adder", 1)
        g = _get_block_id(sim, "gain", 1)      # G=2.0
        j = _get_block_id(sim, "junction", 1)
        h = _get_block_id(sim, "gain", 2)      # H=0.5
        out1 = _get_block_id(sim, "output", 1)

        connections = [
            (in1, 0, adder, 0),
            (adder, 2, g, 0),
            (g, 1, j, 0),
            (j, 1, out1, 0),
            (j, 1, h, 0),
            (h, 1, adder, 1),
        ]
        for fb, fp, tb, tp in connections:
            sim.handle_action("add_connection", {
                "from_block": fb, "from_port": fp, "to_block": tb, "to_port": tp
            })

        blocks_before = copy.deepcopy(sim.blocks)
        _compute_and_get_result(sim)

        assert sim.blocks == blocks_before, \
            "sim.blocks must not be mutated after SISO compute_tf"

    def test_blocks_unchanged_after_mimo(self, bdb_simulator):
        """2x1 MIMO diagram: regression for the bug where compute_tf
        rewrote in2's type from 'input' to 'gain' to compute per-input TFs.
            in1 -> G1(2) -> adder(0)
            in2 -> G2(4) -> adder(1)
            adder -> G3(3) -> out
        """
        sim = bdb_simulator

        sim.handle_action("add_block", {"block_type": "input"})
        sim.handle_action("add_block", {"block_type": "input"})
        sim.handle_action("add_block", {"block_type": "gain", "value": 2.0})
        sim.handle_action("add_block", {"block_type": "gain", "value": 4.0})
        sim.handle_action("add_block", {"block_type": "adder"})
        sim.handle_action("add_block", {"block_type": "gain", "value": 3.0})
        sim.handle_action("add_block", {"block_type": "output"})

        in1 = _get_block_id(sim, "input", 1)
        in2 = _get_block_id(sim, "input", 2)
        g1 = _get_block_id(sim, "gain", 1)     # G1=2.0
        g2 = _get_block_id(sim, "gain", 2)     # G2=4.0
        adder = _get_block_id(sim, "adder", 1)
        g3 = _get_block_id(sim, "gain", 3)     # G3=3.0
        out1 = _get_block_id(sim, "output", 1)

        connections = [
            (in1, 0, g1, 0),
            (g1, 1, adder, 0),
            (in2, 0, g2, 0),
            (g2, 1, adder, 1),
            (adder, 2, g3, 0),
            (g3, 1, out1, 0),
        ]
        for fb, fp, tb, tp in connections:
            sim.handle_action("add_connection", {
                "from_block": fb, "from_port": fp, "to_block": tb, "to_port": tp
            })

        blocks_before = copy.deepcopy(sim.blocks)
        _compute_and_get_result(sim)

        assert sim.blocks == blocks_before, \
            "sim.blocks must not be mutated after MIMO compute_tf"

    def test_block_types_preserved(self, bdb_simulator):
        """Same 2x1 MIMO topology as the previous test, but specifically
        asserts on the `type` field — which is what the historical bug
        rewrote (input -> gain)."""
        sim = bdb_simulator

        sim.handle_action("add_block", {"block_type": "input"})
        sim.handle_action("add_block", {"block_type": "input"})
        sim.handle_action("add_block", {"block_type": "gain", "value": 2.0})
        sim.handle_action("add_block", {"block_type": "gain", "value": 4.0})
        sim.handle_action("add_block", {"block_type": "adder"})
        sim.handle_action("add_block", {"block_type": "gain", "value": 3.0})
        sim.handle_action("add_block", {"block_type": "output"})

        in1 = _get_block_id(sim, "input", 1)
        in2 = _get_block_id(sim, "input", 2)
        g1 = _get_block_id(sim, "gain", 1)
        g2 = _get_block_id(sim, "gain", 2)
        adder = _get_block_id(sim, "adder", 1)
        g3 = _get_block_id(sim, "gain", 3)
        out1 = _get_block_id(sim, "output", 1)

        connections = [
            (in1, 0, g1, 0),
            (g1, 1, adder, 0),
            (in2, 0, g2, 0),
            (g2, 1, adder, 1),
            (adder, 2, g3, 0),
            (g3, 1, out1, 0),
        ]
        for fb, fp, tb, tp in connections:
            sim.handle_action("add_connection", {
                "from_block": fb, "from_port": fp, "to_block": tb, "to_port": tp
            })

        types_before = {bid: block["type"] for bid, block in sim.blocks.items()}
        _compute_and_get_result(sim)
        types_after = {bid: block["type"] for bid, block in sim.blocks.items()}

        for bid in types_before:
            assert types_after[bid] == types_before[bid], \
                f"block {bid} type changed from '{types_before[bid]}' to '{types_after[bid]}'"

    def test_mimo_results_correct_values(self, bdb_simulator):
        """Same 2x1 MIMO topology produces the right TF values:
        G_11 = G1*G3 = 6, G_12 = G2*G3 = 12, shared den = [1]."""
        sim = bdb_simulator

        sim.handle_action("add_block", {"block_type": "input"})
        sim.handle_action("add_block", {"block_type": "input"})
        sim.handle_action("add_block", {"block_type": "gain", "value": 2.0})
        sim.handle_action("add_block", {"block_type": "gain", "value": 4.0})
        sim.handle_action("add_block", {"block_type": "adder"})
        sim.handle_action("add_block", {"block_type": "gain", "value": 3.0})
        sim.handle_action("add_block", {"block_type": "output"})

        in1 = _get_block_id(sim, "input", 1)
        in2 = _get_block_id(sim, "input", 2)
        g1 = _get_block_id(sim, "gain", 1)
        g2 = _get_block_id(sim, "gain", 2)
        adder = _get_block_id(sim, "adder", 1)
        g3 = _get_block_id(sim, "gain", 3)
        out1 = _get_block_id(sim, "output", 1)

        connections = [
            (in1, 0, g1, 0),
            (g1, 1, adder, 0),
            (in2, 0, g2, 0),
            (g2, 1, adder, 1),
            (adder, 2, g3, 0),
            (g3, 1, out1, 0),
        ]
        for fb, fp, tb, tp in connections:
            sim.handle_action("add_connection", {
                "from_block": fb, "from_port": fp, "to_block": tb, "to_port": tp
            })

        result = _compute_and_get_result(sim)

        assert result["mimo"] is True
        assert result["dimensions"] == {"inputs": 2, "outputs": 1}

        assert_poly_equal(result["transfer_matrix"][0][0]["numerator"], [6.0])
        assert_poly_equal(result["transfer_matrix"][0][1]["numerator"], [12.0])
        assert_poly_equal(result["transfer_matrix"][0][0]["denominator"], [1.0])
        assert_poly_equal(result["transfer_matrix"][0][1]["denominator"], [1.0])
