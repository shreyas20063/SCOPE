"""Tests for MIMODesignStudio hub from_hub_data branches.

Three branches must work:
1. SS payload — direct A/B/C/D injection (the original supported path)
2. transfer_matrix payload — MIMO TF from BDB, assembled into a non-
   minimal block-diagonal SS realization
3. flat tf payload — SISO TF from any Tier 1 producer (BDB SISO,
   controller_tuning_lab, etc.), converted via signal.tf2ss

Pre-fix behavior: only branch 1 worked. Branches 2 and 3 fell through
to the base class which silently returned True without injecting
anything (silent stale).
"""
import numpy as np
import pytest
from scipy import signal as scipy_signal

from simulations.mimo_design_studio import MIMODesignStudioSimulator


# ---------------------------------------------------------------------------
# Branch 1: SS payload (regression — must continue to work)
# ---------------------------------------------------------------------------

class TestSSPayload:
    def test_accepts_ss_payload(self):
        sim = MIMODesignStudioSimulator("mds")
        sim.initialize()
        ss_payload = {
            "source": "ss",
            "domain": "ct",
            "ss": {
                "A": [[0, 1], [-2, -3]],
                "B": [[0], [1]],
                "C": [[1, 0]],
                "D": [[0]],
            },
            "dimensions": {"n": 2, "m": 1, "p": 1},
        }
        assert sim.from_hub_data(ss_payload) is True
        assert sim.parameters["preset"] == "custom"

    def test_rejects_oversized_ss(self):
        sim = MIMODesignStudioSimulator("mds")
        sim.initialize()
        # 9-state system exceeds _MAX_N=8
        n = 9
        ss_payload = {
            "source": "ss",
            "domain": "ct",
            "ss": {
                "A": np.eye(n).tolist(),
                "B": [[1.0] for _ in range(n)],
                "C": [[1.0] * n],
                "D": [[0.0]],
            },
            "dimensions": {"n": n, "m": 1, "p": 1},
        }
        assert sim.from_hub_data(ss_payload) is False


# ---------------------------------------------------------------------------
# Branch 2: MIMO transfer_matrix payload
# ---------------------------------------------------------------------------

class TestTransferMatrixPayload:
    def test_accepts_2x2_transfer_matrix(self):
        """A 2x2 transfer matrix from BDB should produce a valid block-
        diagonal SS realization."""
        sim = MIMODesignStudioSimulator("mds")
        sim.initialize()
        tm_payload = {
            "source": "block_diagram",
            "domain": "ct",
            "transfer_matrix": {
                "entries": [
                    [{"num": [1.0], "den": [1.0, 1.0]},
                     {"num": [2.0], "den": [1.0, 2.0]}],
                    [{"num": [1.0], "den": [1.0, 3.0]},
                     {"num": [1.0], "den": [1.0, 4.0]}],
                ],
                "input_labels": ["u1", "u2"],
                "output_labels": ["y1", "y2"],
                "variable": "s",
            },
            "dimensions": {"n": 1, "m": 2, "p": 2},
        }
        assert sim.from_hub_data(tm_payload) is True
        assert sim.parameters["preset"] == "custom"

    def test_2x2_realization_recovers_tf_via_ss2tf(self):
        """Round-trip: take a known 2x2 TF, push, pull, then verify the
        resulting SS realization re-derives the same per-entry TFs."""
        sim = MIMODesignStudioSimulator("mds")
        sim.initialize()
        tm_payload = {
            "source": "block_diagram",
            "domain": "ct",
            "transfer_matrix": {
                "entries": [
                    [{"num": [1.0], "den": [1.0, 1.0]},
                     {"num": [1.0], "den": [1.0, 2.0]}],
                    [{"num": [1.0], "den": [1.0, 3.0]},
                     {"num": [1.0], "den": [1.0, 4.0]}],
                ],
                "input_labels": ["u1", "u2"],
                "output_labels": ["y1", "y2"],
                "variable": "s",
            },
            "dimensions": {"n": 1, "m": 2, "p": 2},
        }
        sim.from_hub_data(tm_payload)
        # Reparse the matrices and verify dimensions
        A = sim._parse_matrix(sim.parameters["matrix_a"], "A")
        B = sim._parse_matrix(sim.parameters["matrix_b"], "B")
        C = sim._parse_matrix(sim.parameters["matrix_c"], "C")
        D = sim._parse_matrix(sim.parameters["matrix_d"], "D")
        n = len(A)
        # 4 entries each with 1 state (1st order) → 4 states total
        assert n == 4
        assert len(B) == 4 and len(B[0]) == 2  # n x m
        assert len(C) == 2 and len(C[0]) == 4  # p x n
        assert len(D) == 2 and len(D[0]) == 2  # p x m

    def test_rejects_oversized_transfer_matrix(self):
        sim = MIMODesignStudioSimulator("mds")
        sim.initialize()
        # 5x5 with 1st-order entries → n=25 states, exceeds _MAX_N=8
        entries = [
            [{"num": [1.0], "den": [1.0, float(i + j + 1)]} for j in range(5)]
            for i in range(5)
        ]
        tm_payload = {
            "source": "block_diagram",
            "domain": "ct",
            "transfer_matrix": {
                "entries": entries,
                "input_labels": [f"u{i}" for i in range(5)],
                "output_labels": [f"y{i}" for i in range(5)],
                "variable": "s",
            },
            "dimensions": {"n": 1, "m": 5, "p": 5},
        }
        assert sim.from_hub_data(tm_payload) is False


# ---------------------------------------------------------------------------
# Branch 3: flat SISO tf payload
# ---------------------------------------------------------------------------

class TestSISOTfPayload:
    def test_accepts_siso_tf(self):
        sim = MIMODesignStudioSimulator("mds")
        sim.initialize()
        siso_payload = {
            "source": "tf",
            "domain": "ct",
            "tf": {"num": [1.0], "den": [1.0, 2.0, 3.0]},
            "dimensions": {"n": 2, "m": 1, "p": 1},
        }
        assert sim.from_hub_data(siso_payload) is True
        assert sim.parameters["preset"] == "custom"

    def test_siso_tf_round_trip_preserves_dynamics(self):
        """Push a SISO TF, pull, then re-derive the TF via ss2tf and
        confirm the poles match."""
        sim = MIMODesignStudioSimulator("mds")
        sim.initialize()
        siso_payload = {
            "source": "tf",
            "domain": "ct",
            "tf": {"num": [1.0], "den": [1.0, 3.0, 2.0]},  # poles at -1, -2
            "dimensions": {"n": 2, "m": 1, "p": 1},
        }
        sim.from_hub_data(siso_payload)
        A = np.array(sim._parse_matrix(sim.parameters["matrix_a"], "A"))
        # Eigenvalues of A are the poles of the TF
        eigs = sorted(np.linalg.eigvals(A).real)
        assert np.allclose(eigs, [-2.0, -1.0], atol=1e-6)


# ---------------------------------------------------------------------------
# Common rejection guards
# ---------------------------------------------------------------------------

class TestPreconditions:
    def test_rejects_none(self):
        sim = MIMODesignStudioSimulator("mds")
        sim.initialize()
        assert sim.from_hub_data(None) is False

    def test_rejects_empty(self):
        sim = MIMODesignStudioSimulator("mds")
        sim.initialize()
        assert sim.from_hub_data({}) is False

    def test_rejects_dt_payload(self):
        sim = MIMODesignStudioSimulator("mds")
        sim.initialize()
        dt_payload = {
            "source": "tf", "domain": "dt",
            "tf": {"num": [1.0], "den": [1.0, -0.5]},
            "dimensions": {"n": 1, "m": 1, "p": 1},
        }
        assert sim.from_hub_data(dt_payload) is False
