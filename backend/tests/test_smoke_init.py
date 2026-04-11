"""Smoke tests for 14 previously untested simulators.

For each simulator, verifies:
1. Instantiation succeeds
2. initialize() with default params succeeds
3. get_state() returns valid structure with parameters, plots, metadata
4. plots is a non-empty list
5. Each plot has id, title, data, layout keys
"""

import sys
import os

import pytest

# Ensure backend is on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from simulations import SIMULATOR_REGISTRY


SMOKE_SIM_IDS = [
    "root_locus",
    "nyquist_stability",
    "nyquist_bode_comparison",
    "state_space_analyzer",
    "steady_state_error",
    "lead_lag_designer",
    "nonlinear_control_lab",
    "phase_portrait",
    "dc_motor",
    "second_order_system",
    "mass_spring_system",
    "complex_poles_modes",
    "resonance_anatomy",
    "delay_instability",
]


@pytest.mark.parametrize("sim_id", SMOKE_SIM_IDS)
def test_smoke_init_and_state(sim_id):
    """Smoke test: instantiate, initialize, get_state for each sim."""
    cls = SIMULATOR_REGISTRY[sim_id]

    # 1. Instantiate
    sim = cls(sim_id)

    # 2. Initialize with defaults
    sim.initialize()

    # 3. Get state
    state = sim.get_state()

    # 4. Assert top-level keys
    assert "parameters" in state, f"{sim_id}: missing 'parameters' key"
    assert "plots" in state, f"{sim_id}: missing 'plots' key"
    assert "metadata" in state, f"{sim_id}: missing 'metadata' key"

    # 5. Plots is a non-empty list
    plots = state["plots"]
    assert isinstance(plots, list), f"{sim_id}: plots is not a list"
    assert len(plots) > 0, f"{sim_id}: plots list is empty"

    # 6. Each plot has required keys
    for i, plot in enumerate(plots):
        assert "id" in plot, f"{sim_id}: plot[{i}] missing 'id'"
        assert "title" in plot, f"{sim_id}: plot[{i}] missing 'title'"
        assert "data" in plot, f"{sim_id}: plot[{i}] missing 'data'"
        assert "layout" in plot, f"{sim_id}: plot[{i}] missing 'layout'"
