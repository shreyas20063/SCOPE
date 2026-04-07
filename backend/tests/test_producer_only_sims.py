"""Producer-only sims must reject hub pulls cleanly.

These sims have custom to_hub_data (they generate TFs from their own
parameters) but the inherited from_hub_data must be overridden to
return False, otherwise the inherited base method silently 'succeeds'
without mutating any parameters and the frontend incorrectly marks the
sim as hub-synced.
"""
import pytest

from simulations.routh_hurwitz import RouthHurwitzSimulator
from simulations.second_order_system import SecondOrderSystemSimulator
from simulations.laplace_roc import LaplaceROCSimulator
from simulations.z_transform_roc import ZTransformROCSimulator


CT_PAYLOAD = {
    "source": "tf",
    "domain": "ct",
    "tf": {"num": [42.0], "den": [1.0, 99.0, 7.0]},
    "dimensions": {"n": 2, "m": 1, "p": 1},
}

DT_PAYLOAD = {**CT_PAYLOAD, "domain": "dt"}


@pytest.mark.parametrize("cls,sim_id,payload", [
    (RouthHurwitzSimulator, "routh_hurwitz", CT_PAYLOAD),
    (SecondOrderSystemSimulator, "second_order_system", CT_PAYLOAD),
    (LaplaceROCSimulator, "laplace_roc", CT_PAYLOAD),
    (ZTransformROCSimulator, "z_transform_roc", DT_PAYLOAD),
])
class TestProducerOnly:
    def test_from_hub_data_returns_false(self, cls, sim_id, payload):
        sim = cls(sim_id)
        sim.initialize()
        assert sim.from_hub_data(payload) is False

    def test_parameters_unchanged_after_pull(self, cls, sim_id, payload):
        sim = cls(sim_id)
        sim.initialize()
        before = dict(sim.parameters)
        sim.from_hub_data(payload)
        assert sim.parameters == before

    def test_to_hub_data_still_works(self, cls, sim_id, payload):
        # Producer side must still work — these sims are valid hub
        # exporters even though they reject hub imports.
        sim = cls(sim_id)
        sim.initialize()
        data = sim.to_hub_data()
        assert data is not None
        assert data.get("source") == "tf"
        assert "tf" in data
