"""Tests for Fix 06 dispositions of 9 sims with non-standard hub schemas.

Each sim falls into one of three dispositions:

- VESTIGIAL: HUB_SLOTS removed; the sim does not appear in the hub UI
  at all. (cascade_parallel, dc_motor, dt_difference_equation,
  mass_spring_system, operator_algebra, phase_portrait)
- PRODUCER-ONLY: keeps HUB_SLOTS and to_hub_data, overrides
  from_hub_data to return False. (nonlinear_control_lab)
- CUSTOM CONSUMER: implements both to_hub_data and from_hub_data with
  sim-specific parameter mapping. (dt_system_representations,
  ode_laplace_solver)
"""
import pytest

from simulations import SIMULATOR_REGISTRY


# ---------------------------------------------------------------------------
# Vestigial: HUB_SLOTS must be empty (default from base class)
# ---------------------------------------------------------------------------

VESTIGIAL_SIMS = [
    "cascade_parallel",
    "dc_motor",
    "dt_difference_equation",
    "mass_spring_system",
    "operator_algebra",
    "phase_portrait",
]


@pytest.mark.parametrize("sim_id", VESTIGIAL_SIMS)
class TestVestigialDisposition:
    def test_hub_slots_empty(self, sim_id):
        cls = SIMULATOR_REGISTRY[sim_id]
        sim = cls(sim_id)
        sim.initialize()
        assert sim.HUB_SLOTS == [], (
            f"{sim_id} should have HUB_SLOTS = [] (inherited from base) "
            f"after Fix 06; got {sim.HUB_SLOTS}"
        )


# ---------------------------------------------------------------------------
# Producer-only: nonlinear_control_lab
# ---------------------------------------------------------------------------

CT_TF = {
    "source": "tf",
    "domain": "ct",
    "tf": {"num": [1.0], "den": [1.0, 2.0, 3.0]},
    "dimensions": {"n": 2, "m": 1, "p": 1},
}

CT_SS = {
    "source": "ss",
    "domain": "ct",
    "ss": {"A": [[0, 1], [-2, -3]], "B": [[0], [1]], "C": [[1, 0]], "D": [[0]]},
    "dimensions": {"n": 2, "m": 1, "p": 1},
}


class TestNonlinearControlLabProducerOnly:
    def test_from_hub_data_rejects_tf(self):
        cls = SIMULATOR_REGISTRY["nonlinear_control_lab"]
        sim = cls("ncl")
        sim.initialize()
        assert sim.from_hub_data(CT_TF) is False

    def test_from_hub_data_rejects_ss(self):
        cls = SIMULATOR_REGISTRY["nonlinear_control_lab"]
        sim = cls("ncl")
        sim.initialize()
        assert sim.from_hub_data(CT_SS) is False

    def test_parameters_unchanged_after_pull(self):
        cls = SIMULATOR_REGISTRY["nonlinear_control_lab"]
        sim = cls("ncl")
        sim.initialize()
        before = dict(sim.parameters)
        sim.from_hub_data(CT_TF)
        assert sim.parameters == before


# ---------------------------------------------------------------------------
# Custom consumer: dt_system_representations
# ---------------------------------------------------------------------------

DT_TF_PAYLOAD = {
    "source": "tf",
    "domain": "dt",
    "tf": {"num": [1.0, -0.5], "den": [1.0, -0.7, 0.1]},
    "dimensions": {"n": 2, "m": 1, "p": 1},
}


class TestDtSystemRepresentationsConsumer:
    def test_pull_returns_true(self):
        cls = SIMULATOR_REGISTRY["dt_system_representations"]
        sim = cls("dtsr")
        sim.initialize()
        assert sim.from_hub_data(DT_TF_PAYLOAD) is True

    def test_pull_injects_b_and_a_coefficients(self):
        cls = SIMULATOR_REGISTRY["dt_system_representations"]
        sim = cls("dtsr")
        sim.initialize()
        sim.from_hub_data(DT_TF_PAYLOAD)
        # Hub TF is high-power-first; sim stores low-power-first
        # num=[1, -0.5] (high-power) → b_coefficients="-0.5, 1.0" (low-power)
        b_coeffs = sim.parameters["b_coefficients"]
        a_coeffs = sim.parameters["a_coefficients"]
        # Parse and compare numerically (whitespace-tolerant)
        b = [float(x) for x in b_coeffs.split(",")]
        a = [float(x) for x in a_coeffs.split(",")]
        assert b == [-0.5, 1.0]
        assert a == [0.1, -0.7, 1.0]

    def test_round_trip_via_hub(self):
        """Push then pull on a fresh instance should yield equivalent state."""
        cls = SIMULATOR_REGISTRY["dt_system_representations"]
        producer = cls("p")
        producer.initialize()
        producer.parameters["b_coefficients"] = "0.5, -0.2"
        producer.parameters["a_coefficients"] = "1.0, -0.8, 0.16"
        payload = producer.to_hub_data()
        assert payload is not None

        consumer = cls("c")
        consumer.initialize()
        assert consumer.from_hub_data(payload) is True
        # Parsed numerical content should match (string formatting may
        # differ but the polynomials must be the same).
        b_p = [float(x) for x in producer.parameters["b_coefficients"].split(",")]
        a_p = [float(x) for x in producer.parameters["a_coefficients"].split(",")]
        b_c = [float(x) for x in consumer.parameters["b_coefficients"].split(",")]
        a_c = [float(x) for x in consumer.parameters["a_coefficients"].split(",")]
        assert b_p == b_c
        assert a_p == a_c

    def test_rejects_ct_payload(self):
        cls = SIMULATOR_REGISTRY["dt_system_representations"]
        sim = cls("dtsr")
        sim.initialize()
        assert sim.from_hub_data(CT_TF) is False


# ---------------------------------------------------------------------------
# Custom consumer: ode_laplace_solver
# ---------------------------------------------------------------------------

class TestOdeLaplaceSolverConsumer:
    def test_pull_returns_true(self):
        cls = SIMULATOR_REGISTRY["ode_laplace_solver"]
        sim = cls("ols")
        sim.initialize()
        assert sim.from_hub_data(CT_TF) is True

    def test_pull_injects_input_and_output_coeffs(self):
        cls = SIMULATOR_REGISTRY["ode_laplace_solver"]
        sim = cls("ols")
        sim.initialize()
        sim.from_hub_data(CT_TF)
        in_coeffs = [float(x) for x in sim.parameters["input_coeffs"].split(",")]
        out_coeffs = [float(x) for x in sim.parameters["output_coeffs"].split(",")]
        assert in_coeffs == [1.0]
        assert out_coeffs == [1.0, 2.0, 3.0]

    def test_round_trip_via_hub(self):
        cls = SIMULATOR_REGISTRY["ode_laplace_solver"]
        producer = cls("p")
        producer.initialize()
        producer.parameters["input_coeffs"] = "2"
        producer.parameters["output_coeffs"] = "1, 4, 5"
        payload = producer.to_hub_data()
        assert payload is not None

        consumer = cls("c")
        consumer.initialize()
        assert consumer.from_hub_data(payload) is True
        in_p = [float(x) for x in producer.parameters["input_coeffs"].split(",")]
        out_p = [float(x) for x in producer.parameters["output_coeffs"].split(",")]
        in_c = [float(x) for x in consumer.parameters["input_coeffs"].split(",")]
        out_c = [float(x) for x in consumer.parameters["output_coeffs"].split(",")]
        assert in_p == in_c
        assert out_p == out_c

    def test_rejects_dt_payload(self):
        cls = SIMULATOR_REGISTRY["ode_laplace_solver"]
        sim = cls("ols")
        sim.initialize()
        assert sim.from_hub_data(DT_TF_PAYLOAD) is False
