"""
Tests for signal isolation / non-mutation during MIMO computation (MATH-02).

MATH-02: The MIMO compute_tf path must NOT mutate sim.blocks. Currently the
implementation zeros out input blocks to compute per-input transfer functions,
which corrupts shared state. These tests define the expected non-mutation
contract so that the fix in Plan 03-02 can be validated.

Note: test_blocks_unchanged_after_mimo and test_block_types_preserved are
EXPECTED TO FAIL until Plan 03-02 removes the mutation-based approach.
test_blocks_unchanged_after_siso and test_mimo_results_correct_values should
pass against the current code.

Requirements: MATH-02
"""

import copy

import numpy as np
import pytest

from conftest import assert_poly_equal

from test_shared_delta import _get_block_id, _compute_and_get_result


class TestSignalIsolation:
    """MIMO compute_tf must not mutate sim.blocks.

    Requirement: MATH-02
    """

    def test_blocks_unchanged_after_siso(self, bdb_simulator):
        """SISO compute_tf must not mutate sim.blocks.

        Topology (negative feedback):
            in -> adder(+,-) -> G(2) -> junction -> out
            junction -> H(0.5) -> adder(port 1, sign "-")

        SISO has only 1 input so no mutation is needed. This should PASS
        even with the current mutation-based code.
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
            "MATH-02: sim.blocks must not be mutated after SISO compute_tf"

    def test_blocks_unchanged_after_mimo(self, bdb_simulator):
        """MIMO compute_tf must not mutate sim.blocks.

        Topology (2-input 1-output):
            in1 -> G1(2) -> adder(port 0)
            in2 -> G2(4) -> adder(port 1)
            adder -> G3(3) -> out

        The current mutation-based code changes in2's type from "input" to
        "gain" during computation. This test catches that mutation.

        # EXPECTED FAIL until Plan 03-02 removes mutation
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
            "MATH-02: sim.blocks must not be mutated after MIMO compute_tf"

    def test_block_types_preserved(self, bdb_simulator):
        """Every block's type field must be unchanged after MIMO compute_tf.

        Same 2x1 MIMO topology as test_blocks_unchanged_after_mimo.
        This test specifically checks the "type" field which the current
        mutation changes from "input" to "gain".

        # EXPECTED FAIL until Plan 03-02 removes mutation
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
                f"MATH-02: block {bid} type changed from '{types_before[bid]}' to '{types_after[bid]}'"

    def test_mimo_results_correct_values(self, bdb_simulator):
        """MIMO results must have correct transfer function values.

        Same 2x1 MIMO topology:
            in1 -> G1(2) -> adder(port 0)
            in2 -> G2(4) -> adder(port 1)
            adder -> G3(3) -> out

        Expected: G_11 = G1*G3 = 6.0, G_12 = G2*G3 = 12.0, shared den=[1.0]

        This should PASS with current code (mutation restores correctly for
        the result computation).
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

        # G_11 = G1*G3 = 2*3 = 6.0
        assert_poly_equal(
            result["transfer_matrix"][0][0]["numerator"], [6.0],
            "G_11 numerator should be [6.0]"
        )
        # G_12 = G2*G3 = 4*3 = 12.0
        assert_poly_equal(
            result["transfer_matrix"][0][1]["numerator"], [12.0],
            "G_12 numerator should be [12.0]"
        )
        # Shared denominator = [1.0] (no loops)
        assert_poly_equal(
            result["transfer_matrix"][0][0]["denominator"], [1.0],
            "G_11 denominator should be [1.0]"
        )
        assert_poly_equal(
            result["transfer_matrix"][0][1]["denominator"], [1.0],
            "G_12 denominator should be [1.0]"
        )
