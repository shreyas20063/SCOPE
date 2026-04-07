"""Tests for BaseSimulator hub data methods.

Regression coverage for two related bugs in the base hub plumbing:

1. from_hub_data returned True even when no parameters were injected
   (silent-success). Subclasses with vestigial HUB_SLOTS but no
   recognized num/den parameter names accepted hub data and lied
   about it.
2. to_hub_data read self.parameters while from_hub_data read
   self.PARAMETER_SCHEMA (asymmetric source). Sims that declared
   numerator/denominator in PARAMETER_SCHEMA but omitted them from
   DEFAULT_PARAMS could not push despite being valid consumers.
"""
from typing import Any, Dict, Optional

import pytest

from simulations.base_simulator import BaseSimulator


# ---------------------------------------------------------------------------
# Test fixtures: minimal BaseSimulator subclasses
# ---------------------------------------------------------------------------

class _NoTFParamsSim(BaseSimulator):
    """Sim that declares hub support but has no TF parameter names —
    represents the vestigial-declaration pattern that triggered the
    silent-success bug."""
    PARAMETER_SCHEMA = {"freq": {"type": "slider", "min": 0, "max": 100, "default": 10}}
    DEFAULT_PARAMS = {"freq": 10}
    HUB_SLOTS = ['control']

    def initialize(self, params=None):
        self.parameters = {**self.DEFAULT_PARAMS, **(params or {})}
        self._initialized = True

    def update_parameter(self, name, value):
        if name in self.parameters:
            self.parameters[name] = value
        return self.get_state()

    def get_plots(self):
        return []

    def get_state(self):
        return {"parameters": self.parameters.copy(), "plots": [], "metadata": {}}


class _StandardTFSim(BaseSimulator):
    """Sim with standard num/den parameter names in both PARAMETER_SCHEMA
    and DEFAULT_PARAMS — the happy path."""
    PARAMETER_SCHEMA = {
        "numerator": {"type": "expression", "default": "1"},
        "denominator": {"type": "expression", "default": "1, 1"},
    }
    DEFAULT_PARAMS = {"numerator": "1", "denominator": "1, 1"}
    HUB_SLOTS = ['control']

    def initialize(self, params=None):
        self.parameters = {**self.DEFAULT_PARAMS, **(params or {})}
        self._initialized = True

    def update_parameter(self, name, value):
        if name in self.parameters:
            self.parameters[name] = value
        return self.get_state()

    def get_plots(self):
        return []

    def get_state(self):
        return {"parameters": self.parameters.copy(), "plots": [], "metadata": {}}


class _SchemaOnlyTFSim(BaseSimulator):
    """Sim that declares numerator/denominator in PARAMETER_SCHEMA but not
    in DEFAULT_PARAMS — the dc_motor / ode_laplace_solver pattern that
    triggered the asymmetric-source bug."""
    PARAMETER_SCHEMA = {
        "speed": {"type": "slider", "min": 0, "max": 100, "default": 50},
        "numerator": {"type": "expression", "default": "1"},
        "denominator": {"type": "expression", "default": "1, 2, 3"},
    }
    DEFAULT_PARAMS = {"speed": 50}  # numerator/denominator deliberately omitted
    HUB_SLOTS = ['control']

    def initialize(self, params=None):
        self.parameters = {**self.DEFAULT_PARAMS, **(params or {})}
        self._initialized = True

    def update_parameter(self, name, value):
        if name in self.parameters:
            self.parameters[name] = value
        return self.get_state()

    def get_plots(self):
        return []

    def get_state(self):
        return {"parameters": self.parameters.copy(), "plots": [], "metadata": {}}


VALID_TF_PAYLOAD = {
    "source": "tf",
    "domain": "ct",
    "tf": {"num": [42.0], "den": [1.0, 99.0, 7.0]},
    "dimensions": {"n": 2, "m": 1, "p": 1},
}


# ---------------------------------------------------------------------------
# from_hub_data: silent-success regression
# ---------------------------------------------------------------------------

class TestFromHubDataSilentSuccess:
    """from_hub_data must return False when it cannot inject any params."""

    def test_returns_false_when_no_matching_params(self):
        sim = _NoTFParamsSim("noparams")
        sim.initialize()
        assert sim.from_hub_data(VALID_TF_PAYLOAD) is False, (
            "from_hub_data must return False when PARAMETER_SCHEMA has no "
            "TF-recognized keys, otherwise the frontend incorrectly marks "
            "the sim as hub-synced."
        )

    def test_parameters_unchanged_when_no_matching_params(self):
        sim = _NoTFParamsSim("noparams")
        sim.initialize()
        before = dict(sim.parameters)
        sim.from_hub_data(VALID_TF_PAYLOAD)
        assert sim.parameters == before

    def test_returns_true_when_params_injected(self):
        sim = _StandardTFSim("std")
        sim.initialize()
        assert sim.from_hub_data(VALID_TF_PAYLOAD) is True

    def test_parameters_actually_change_when_pull_succeeds(self):
        sim = _StandardTFSim("std")
        sim.initialize()
        sim.from_hub_data(VALID_TF_PAYLOAD)
        assert sim.parameters["numerator"] == "42.0"
        assert sim.parameters["denominator"] == "1.0, 99.0, 7.0"


class TestFromHubDataPreconditions:
    """Pre-existing acceptance/rejection guards must still work."""

    def test_rejects_none(self):
        sim = _StandardTFSim("std")
        sim.initialize()
        assert sim.from_hub_data(None) is False

    def test_rejects_empty_dict(self):
        sim = _StandardTFSim("std")
        sim.initialize()
        assert sim.from_hub_data({}) is False

    def test_rejects_domain_mismatch(self):
        sim = _StandardTFSim("std")  # default HUB_DOMAIN = "ct"
        sim.initialize()
        dt_payload = {**VALID_TF_PAYLOAD, "domain": "dt"}
        assert sim.from_hub_data(dt_payload) is False

    def test_rejects_mimo_payload_to_siso_sim(self):
        sim = _StandardTFSim("std")
        sim.initialize()
        mimo_payload = {**VALID_TF_PAYLOAD, "dimensions": {"n": 2, "m": 2, "p": 2}}
        assert sim.from_hub_data(mimo_payload) is False


# ---------------------------------------------------------------------------
# to_hub_data: schema-as-source-of-truth regression
# ---------------------------------------------------------------------------

class TestToHubDataSchemaSource:
    """to_hub_data must consult PARAMETER_SCHEMA, not just self.parameters."""

    def test_exports_when_keys_in_schema_only(self):
        sim = _SchemaOnlyTFSim("schema_only")
        sim.initialize()
        data = sim.to_hub_data()
        assert data is not None, (
            "to_hub_data must succeed when PARAMETER_SCHEMA declares "
            "num/den even if DEFAULT_PARAMS omits them"
        )
        assert data["source"] == "tf"
        assert data["tf"]["num"] == [1.0]
        assert data["tf"]["den"] == [1.0, 2.0, 3.0]

    def test_uses_runtime_value_over_schema_default(self):
        sim = _SchemaOnlyTFSim("schema_only")
        sim.initialize()
        sim.parameters["numerator"] = "5, 6"
        sim.parameters["denominator"] = "1, 0, 1"
        data = sim.to_hub_data()
        assert data["tf"]["num"] == [5.0, 6.0]
        assert data["tf"]["den"] == [1.0, 0.0, 1.0]

    def test_returns_none_when_no_tf_keys_in_schema(self):
        sim = _NoTFParamsSim("noparams")
        sim.initialize()
        assert sim.to_hub_data() is None

    def test_standard_sim_still_works(self):
        """Regression: sims with keys in both schema AND defaults still work."""
        sim = _StandardTFSim("std")
        sim.initialize()
        data = sim.to_hub_data()
        assert data is not None
        assert data["tf"]["num"] == [1.0]
        assert data["tf"]["den"] == [1.0, 1.0]
