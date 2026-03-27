"""
Tests for shared Delta denominator (MATH-01) and DFS forward-path enumeration (MATH-05).

MATH-01: All G_ij entries in the MIMO transfer matrix must share the same
graph determinant Delta as their denominator polynomial. Mason's Gain Formula
computes Delta once from the full graph; each entry's numerator differs but
the denominator is always Delta.

MATH-05: DFS forward-path enumeration must produce the correct number of
forward paths and loops, and the target node must never appear as an
intermediate node in a forward path.

These are test-first tests -- they define EXPECTED behavior. Some tests may
fail against the current implementation because the fix hasn't been applied
yet (that's plan 02-02). This is expected.

Requirements: MATH-01, MATH-05
"""

import numpy as np
import pytest

from conftest import assert_poly_equal, ToleranceTier


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def build_topology(sim, blocks, connections):
    """Programmatically build a block diagram topology.

    blocks: list of dicts, each passed as params to add_block action.
    connections: list of (from_block, from_port, to_block, to_port) tuples.
    """
    for b in blocks:
        sim.handle_action("add_block", b)
    for fb, fp, tb, tp in connections:
        sim.handle_action("add_connection", {
            "from_block": fb, "from_port": fp, "to_block": tb, "to_port": tp
        })


def _get_block_id(sim, block_type, index=1):
    """Find the block ID for the Nth block of a given type.

    Blocks are sorted by their auto-generated ID so the ordering matches
    the order of creation (ascending numeric suffix).
    """
    matches = sorted(
        [b for b in sim.blocks.values() if b["type"] == block_type],
        key=lambda b: b["id"],
    )
    if index > len(matches):
        raise ValueError(
            f"Only {len(matches)} blocks of type '{block_type}', asked for index {index}"
        )
    return matches[index - 1]["id"]


def _compute_and_get_result(sim):
    """Run compute_tf and return the _tf_result dict."""
    sim.handle_action("compute_tf", {})
    return sim._tf_result


# =========================================================================
# MATH-01: Shared Delta denominator across all G_ij entries
# =========================================================================

class TestSharedDelta:
    """All entries in the MIMO transfer matrix must share the same denominator
    polynomial (the graph determinant Delta).

    Requirement: MATH-01
    """

    def test_2x1_shared_denominator(self, bdb_simulator):
        """2-input, 1-output: both denominators must be identical.

        Topology:
            in1 -> gain(G1=2.0) -> adder(port 0) -> gain(G3=3.0) -> out1
            in2 -> gain(G2=4.0) -> adder(port 1)

        No feedback loops, so Delta = [1.0] for both entries.
        """
        sim = bdb_simulator

        # Add blocks -- we need to track IDs. The simulator auto-generates IDs.
        # Add in order and look them up by type+index.
        sim.handle_action("add_block", {"block_type": "input"})
        sim.handle_action("add_block", {"block_type": "input"})
        sim.handle_action("add_block", {"block_type": "gain", "value": 2.0})
        sim.handle_action("add_block", {"block_type": "gain", "value": 4.0})
        sim.handle_action("add_block", {"block_type": "adder"})
        sim.handle_action("add_block", {"block_type": "gain", "value": 3.0})
        sim.handle_action("add_block", {"block_type": "output"})

        in1 = _get_block_id(sim, "input", 1)
        in2 = _get_block_id(sim, "input", 2)
        g1 = _get_block_id(sim, "gain", 1)   # G1=2.0
        g2 = _get_block_id(sim, "gain", 2)   # G2=4.0
        adder = _get_block_id(sim, "adder", 1)
        g3 = _get_block_id(sim, "gain", 3)   # G3=3.0
        out1 = _get_block_id(sim, "output", 1)

        # Connect: in1 -> G1 -> adder(port0), in2 -> G2 -> adder(port1), adder -> G3 -> out1
        connections = [
            (in1, 0, g1, 0),       # in1 output -> G1 input
            (g1, 1, adder, 0),     # G1 output -> adder port 0
            (in2, 0, g2, 0),       # in2 output -> G2 input
            (g2, 1, adder, 1),     # G2 output -> adder port 1
            (adder, 2, g3, 0),     # adder output -> G3 input
            (g3, 1, out1, 0),      # G3 output -> out1 input
        ]
        for fb, fp, tb, tp in connections:
            sim.handle_action("add_connection", {
                "from_block": fb, "from_port": fp, "to_block": tb, "to_port": tp
            })

        result = _compute_and_get_result(sim)

        # MIMO: 2 inputs, 1 output -> transfer_matrix is 1x2
        assert result["mimo"] is True
        assert result["dimensions"] == {"inputs": 2, "outputs": 1}

        den_00 = result["transfer_matrix"][0][0]["denominator"]
        den_01 = result["transfer_matrix"][0][1]["denominator"]

        # MATH-01: Both denominators must be identical (shared Delta)
        assert_poly_equal(den_00, den_01, "MATH-01: 2x1 denominators must be shared Delta")
        # No loops -> Delta = [1.0]
        assert_poly_equal(den_00, [1.0], "No loops -> Delta should be [1.0]")

    def test_2x2_feedback_shared_denominator(self, bdb_simulator):
        """2-input, 2-output with feedback: all 4 denominators must be identical.

        Topology (two independent SISO loops):
            in1 -> adder1(port 0) -> custom_tf(integrator: num=[0,1], den=[1,0]) -> junction1 -> out1
            junction1 -> gain(H=0.5) -> adder1(port 1, sign "-")

            in2 -> adder2(port 0) -> gain(G2=2.0) -> junction2 -> out2
            junction2 -> gain(H2=0.3) -> adder2(port 1, sign "-")

        Delta is computed from the FULL graph, so all 4 entries G_ij must share
        the same denominator polynomial.

        MATH-01: expected to fail until Plan 02 refactors Delta computation
        """
        sim = bdb_simulator

        # Add blocks
        sim.handle_action("add_block", {"block_type": "input"})   # in1
        sim.handle_action("add_block", {"block_type": "input"})   # in2
        sim.handle_action("add_block", {"block_type": "adder", "signs": ["+", "-", "+"]})  # adder1
        sim.handle_action("add_block", {"block_type": "adder", "signs": ["+", "-", "+"]})  # adder2
        sim.handle_action("add_block", {"block_type": "custom_tf"})  # integrator TF
        sim.handle_action("add_block", {"block_type": "gain", "value": 2.0})   # G2
        sim.handle_action("add_block", {"block_type": "junction"})  # junction1
        sim.handle_action("add_block", {"block_type": "junction"})  # junction2
        sim.handle_action("add_block", {"block_type": "gain", "value": 0.5})   # H1
        sim.handle_action("add_block", {"block_type": "gain", "value": 0.3})   # H2
        sim.handle_action("add_block", {"block_type": "output"})   # out1
        sim.handle_action("add_block", {"block_type": "output"})   # out2

        in1 = _get_block_id(sim, "input", 1)
        in2 = _get_block_id(sim, "input", 2)
        adder1 = _get_block_id(sim, "adder", 1)
        adder2 = _get_block_id(sim, "adder", 2)
        ctf = _get_block_id(sim, "custom_tf", 1)
        g2 = _get_block_id(sim, "gain", 1)    # G2=2.0
        j1 = _get_block_id(sim, "junction", 1)
        j2 = _get_block_id(sim, "junction", 2)
        h1 = _get_block_id(sim, "gain", 2)    # H1=0.5
        h2 = _get_block_id(sim, "gain", 3)    # H2=0.3
        out1 = _get_block_id(sim, "output", 1)
        out2 = _get_block_id(sim, "output", 2)

        # Set custom_tf to integrator: num=[0,1], den=[1,0] (low-power-first)
        sim.blocks[ctf]["num_coeffs"] = [0.0, 1.0]
        sim.blocks[ctf]["den_coeffs"] = [1.0, 0.0]

        # Loop 1: in1 -> adder1 -> ctf -> junction1 -> out1, junction1 -> H1 -> adder1
        connections = [
            (in1, 0, adder1, 0),
            (adder1, 2, ctf, 0),
            (ctf, 1, j1, 0),
            (j1, 1, out1, 0),
            (j1, 1, h1, 0),
            (h1, 1, adder1, 1),
        ]
        # Loop 2: in2 -> adder2 -> G2 -> junction2 -> out2, junction2 -> H2 -> adder2
        connections += [
            (in2, 0, adder2, 0),
            (adder2, 2, g2, 0),
            (g2, 1, j2, 0),
            (j2, 1, out2, 0),
            (j2, 1, h2, 0),
            (h2, 1, adder2, 1),
        ]

        for fb, fp, tb, tp in connections:
            sim.handle_action("add_connection", {
                "from_block": fb, "from_port": fp, "to_block": tb, "to_port": tp
            })

        result = _compute_and_get_result(sim)

        # MIMO: 2 inputs, 2 outputs -> transfer_matrix is 2x2
        assert result["mimo"] is True
        assert result["dimensions"] == {"inputs": 2, "outputs": 2}

        # Extract all 4 denominators
        denoms = []
        for i in range(2):
            for j in range(2):
                denoms.append(result["transfer_matrix"][i][j]["denominator"])

        # MATH-01: ALL 4 denominators must be identical (shared graph Delta)
        for idx in range(1, 4):
            assert_poly_equal(
                denoms[idx], denoms[0],
                f"MATH-01: denominator [{idx // 2}][{idx % 2}] must equal [0][0]"
            )

    def test_1x2_shared_denominator(self, bdb_simulator):
        """1-input, 2-output: both denominators must be identical.

        Topology:
            in1 -> junction1 -> gain(G1=3.0) -> out1
            junction1 -> gain(G2=5.0) -> out2

        No loops, Delta = [1.0] for both entries.

        Requirement: MATH-01
        """
        sim = bdb_simulator

        sim.handle_action("add_block", {"block_type": "input"})
        sim.handle_action("add_block", {"block_type": "junction"})
        sim.handle_action("add_block", {"block_type": "gain", "value": 3.0})
        sim.handle_action("add_block", {"block_type": "gain", "value": 5.0})
        sim.handle_action("add_block", {"block_type": "output"})
        sim.handle_action("add_block", {"block_type": "output"})

        in1 = _get_block_id(sim, "input", 1)
        j1 = _get_block_id(sim, "junction", 1)
        g1 = _get_block_id(sim, "gain", 1)   # G1=3.0
        g2 = _get_block_id(sim, "gain", 2)   # G2=5.0
        out1 = _get_block_id(sim, "output", 1)
        out2 = _get_block_id(sim, "output", 2)

        connections = [
            (in1, 0, j1, 0),      # in1 -> junction
            (j1, 1, g1, 0),       # junction -> G1
            (j1, 1, g2, 0),       # junction -> G2
            (g1, 1, out1, 0),     # G1 -> out1
            (g2, 1, out2, 0),     # G2 -> out2
        ]
        for fb, fp, tb, tp in connections:
            sim.handle_action("add_connection", {
                "from_block": fb, "from_port": fp, "to_block": tb, "to_port": tp
            })

        result = _compute_and_get_result(sim)

        assert result["mimo"] is True
        assert result["dimensions"] == {"inputs": 1, "outputs": 2}

        den_00 = result["transfer_matrix"][0][0]["denominator"]
        den_10 = result["transfer_matrix"][1][0]["denominator"]

        # MATH-01: Both denominators must be identical
        assert_poly_equal(den_00, den_10, "MATH-01: 1x2 denominators must be shared Delta")
        # No loops -> Delta = [1.0]
        assert_poly_equal(den_00, [1.0], "No loops -> Delta should be [1.0]")

    def test_siso_still_works_after_refactor(self, bdb_simulator):
        """Regression: simple SISO negative feedback must produce correct TF.

        Topology:
            in1 -> adder(port 0) -> gain(G=2.0) -> junction -> out1
            junction -> gain(H=0.5) -> adder(port 1, sign "-")

        Mason's: forward path P1 = G = 2, loop L1 = -G*H = -1 (sign from adder).
        Delta = 1 - (-1) = 2. Cofactor Delta1 = 1.
        TF = P1*Delta1 / Delta = 2/2 = 1.

        Requirement: MATH-01 (regression safety net)
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
        g = _get_block_id(sim, "gain", 1)     # G=2.0
        j = _get_block_id(sim, "junction", 1)
        h = _get_block_id(sim, "gain", 2)     # H=0.5
        out1 = _get_block_id(sim, "output", 1)

        connections = [
            (in1, 0, adder, 0),    # in1 -> adder port 0
            (adder, 2, g, 0),      # adder output -> G
            (g, 1, j, 0),          # G -> junction
            (j, 1, out1, 0),       # junction -> out1
            (j, 1, h, 0),          # junction -> H (feedback)
            (h, 1, adder, 1),      # H -> adder port 1 (sign "-")
        ]
        for fb, fp, tb, tp in connections:
            sim.handle_action("add_connection", {
                "from_block": fb, "from_port": fp, "to_block": tb, "to_port": tp
            })

        result = _compute_and_get_result(sim)

        # SISO: 1x1 -> legacy flat format
        assert result["mimo"] is False

        # TF = G/(1+GH) = 2/(1+1) = 1.0
        # In polynomial form: num=[1.0], den=[1.0] after normalization
        assert_poly_equal(
            result["numerator"], [1.0],
            "MATH-01 regression: SISO numerator should be [1.0]"
        )
        assert_poly_equal(
            result["denominator"], [1.0],
            "MATH-01 regression: SISO denominator should be [1.0]"
        )
        assert result["num_forward_paths"] == 1
        assert result["num_loops"] == 1


# =========================================================================
# MATH-05: DFS forward-path and loop enumeration correctness
# =========================================================================

class TestDFSForwardPaths:
    """DFS-based forward path enumeration must:
    - Produce the correct number of forward paths for known topologies
    - Never include the target node as an intermediate node
    - Count loops correctly

    Requirement: MATH-05
    """

    def test_no_target_as_intermediate(self, bdb_simulator):
        """Target node must not appear as intermediate node in forward paths.

        Topology:
            in1 -> gain(G1=1.0) -> adder(port 0) -> gain(G2=3.0) -> junction -> out1
            junction -> gain(H=0.5) -> adder(port 1, sign "-")

        Forward paths from in1 to out1: exactly 1 (in1 -> G1 -> adder -> G2 -> junction -> out1).
        The junction participates in a loop but is NOT the target.

        Requirement: MATH-05
        """
        sim = bdb_simulator

        sim.handle_action("add_block", {"block_type": "input"})
        sim.handle_action("add_block", {"block_type": "gain", "value": 1.0})
        sim.handle_action("add_block", {"block_type": "adder", "signs": ["+", "-", "+"]})
        sim.handle_action("add_block", {"block_type": "gain", "value": 3.0})
        sim.handle_action("add_block", {"block_type": "junction"})
        sim.handle_action("add_block", {"block_type": "gain", "value": 0.5})
        sim.handle_action("add_block", {"block_type": "output"})

        in1 = _get_block_id(sim, "input", 1)
        g1 = _get_block_id(sim, "gain", 1)    # G1=1.0
        adder = _get_block_id(sim, "adder", 1)
        g2 = _get_block_id(sim, "gain", 2)    # G2=3.0
        j = _get_block_id(sim, "junction", 1)
        h = _get_block_id(sim, "gain", 3)     # H=0.5
        out1 = _get_block_id(sim, "output", 1)

        connections = [
            (in1, 0, g1, 0),
            (g1, 1, adder, 0),
            (adder, 2, g2, 0),
            (g2, 1, j, 0),
            (j, 1, out1, 0),
            (j, 1, h, 0),
            (h, 1, adder, 1),
        ]
        for fb, fp, tb, tp in connections:
            sim.handle_action("add_connection", {
                "from_block": fb, "from_port": fp, "to_block": tb, "to_port": tp
            })

        result = _compute_and_get_result(sim)

        # MATH-05: exactly 1 forward path
        assert result["num_forward_paths"] == 1, \
            "MATH-05: should have exactly 1 forward path"
        # Exactly 1 loop (junction -> H -> adder -> G2 -> junction)
        assert result["num_loops"] == 1, \
            "MATH-05: should have exactly 1 loop"

    def test_known_topology_path_count(self, bdb_simulator):
        """Two parallel forward paths, zero loops.

        Topology:
            in1 -> junction_in -> gain(G1=2.0) -> adder(port 0) -> out1
            junction_in -> gain(G2=3.0) -> adder(port 1)

        2 forward paths, 0 loops.

        Requirement: MATH-05
        """
        sim = bdb_simulator

        sim.handle_action("add_block", {"block_type": "input"})
        sim.handle_action("add_block", {"block_type": "junction"})
        sim.handle_action("add_block", {"block_type": "gain", "value": 2.0})
        sim.handle_action("add_block", {"block_type": "gain", "value": 3.0})
        sim.handle_action("add_block", {"block_type": "adder"})
        sim.handle_action("add_block", {"block_type": "output"})

        in1 = _get_block_id(sim, "input", 1)
        j_in = _get_block_id(sim, "junction", 1)
        g1 = _get_block_id(sim, "gain", 1)    # G1=2.0
        g2 = _get_block_id(sim, "gain", 2)    # G2=3.0
        adder = _get_block_id(sim, "adder", 1)
        out1 = _get_block_id(sim, "output", 1)

        connections = [
            (in1, 0, j_in, 0),     # in1 -> junction
            (j_in, 1, g1, 0),      # junction -> G1
            (j_in, 1, g2, 0),      # junction -> G2
            (g1, 1, adder, 0),     # G1 -> adder port 0
            (g2, 1, adder, 1),     # G2 -> adder port 1
            (adder, 2, out1, 0),   # adder -> out1
        ]
        for fb, fp, tb, tp in connections:
            sim.handle_action("add_connection", {
                "from_block": fb, "from_port": fp, "to_block": tb, "to_port": tp
            })

        result = _compute_and_get_result(sim)

        # MATH-05: 2 forward paths, 0 loops
        assert result["num_forward_paths"] == 2, \
            "MATH-05: two parallel paths should give num_forward_paths == 2"
        assert result["num_loops"] == 0, \
            "MATH-05: no feedback -> num_loops == 0"

    def test_known_topology_loop_count(self, bdb_simulator):
        """Two independent feedback loops in series, 1 forward path.

        Topology:
            in1 -> adder1(port 0) -> gain(G1=2.0) -> junction1 ->
                   adder2(port 0) -> gain(G2=3.0) -> junction2 -> out1
            junction1 -> gain(H1=0.4) -> adder1(port 1, sign "-")
            junction2 -> gain(H2=0.6) -> adder2(port 1, sign "-")

        1 forward path, 2 loops.

        Requirement: MATH-05
        """
        sim = bdb_simulator

        sim.handle_action("add_block", {"block_type": "input"})
        sim.handle_action("add_block", {"block_type": "adder", "signs": ["+", "-", "+"]})  # adder1
        sim.handle_action("add_block", {"block_type": "gain", "value": 2.0})   # G1
        sim.handle_action("add_block", {"block_type": "junction"})  # junction1
        sim.handle_action("add_block", {"block_type": "adder", "signs": ["+", "-", "+"]})  # adder2
        sim.handle_action("add_block", {"block_type": "gain", "value": 3.0})   # G2
        sim.handle_action("add_block", {"block_type": "junction"})  # junction2
        sim.handle_action("add_block", {"block_type": "gain", "value": 0.4})   # H1
        sim.handle_action("add_block", {"block_type": "gain", "value": 0.6})   # H2
        sim.handle_action("add_block", {"block_type": "output"})

        in1 = _get_block_id(sim, "input", 1)
        adder1 = _get_block_id(sim, "adder", 1)
        g1 = _get_block_id(sim, "gain", 1)     # G1=2.0
        j1 = _get_block_id(sim, "junction", 1)
        adder2 = _get_block_id(sim, "adder", 2)
        g2 = _get_block_id(sim, "gain", 2)     # G2=3.0
        j2 = _get_block_id(sim, "junction", 2)
        h1 = _get_block_id(sim, "gain", 3)     # H1=0.4
        h2 = _get_block_id(sim, "gain", 4)     # H2=0.6
        out1 = _get_block_id(sim, "output", 1)

        connections = [
            (in1, 0, adder1, 0),     # in1 -> adder1 port 0
            (adder1, 2, g1, 0),      # adder1 -> G1
            (g1, 1, j1, 0),          # G1 -> junction1
            (j1, 1, adder2, 0),      # junction1 -> adder2 port 0
            (adder2, 2, g2, 0),      # adder2 -> G2
            (g2, 1, j2, 0),          # G2 -> junction2
            (j2, 1, out1, 0),        # junction2 -> out1
            (j1, 1, h1, 0),          # junction1 -> H1 (feedback)
            (h1, 1, adder1, 1),      # H1 -> adder1 port 1 (sign "-")
            (j2, 1, h2, 0),          # junction2 -> H2 (feedback)
            (h2, 1, adder2, 1),      # H2 -> adder2 port 1 (sign "-")
        ]
        for fb, fp, tb, tp in connections:
            sim.handle_action("add_connection", {
                "from_block": fb, "from_port": fp, "to_block": tb, "to_port": tp
            })

        result = _compute_and_get_result(sim)

        # MATH-05: 1 forward path, 2 loops
        assert result["num_forward_paths"] == 1, \
            "MATH-05: cascaded system should have exactly 1 forward path"
        assert result["num_loops"] == 2, \
            "MATH-05: two independent feedback loops should give num_loops == 2"
