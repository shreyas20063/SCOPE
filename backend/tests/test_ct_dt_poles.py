"""
Oracle tests for ct_dt_poles (CT/DT Poles Conversion).

Oracles are derived independently of the implementation:
- exact sampled pole: python-control ZOH discretization of 1/(s+1)  ->  e^{-T/tau}
- approximation poles: textbook substitutions (Franklin-Powell-Workman ch. 6)
- step response from rest: closed form y[n] = 1 - z^n with y[0] = y(0) = 0
"""

import itertools
import json
import math

import control
import numpy as np
import pytest

from core.data_handler import DataHandler
from simulations.ct_dt_poles import CTDTPolesSimulator

METHODS = ["forward_euler", "backward_euler", "trapezoidal", "exact_zoh"]
H_VALUES = [0.01, 0.3, 0.5, 1.0, 1.5, 1.99, 2.0, 2.01, 2.2, 3.0]


def oracle_pole(method: str, h: float) -> float:
    return {"forward_euler": 1 - h, "backward_euler": 1 / (1 + h),
            "trapezoidal": (2 - h) / (2 + h), "exact_zoh": math.exp(-h)}[method]


def make(**params):
    sim = CTDTPolesSimulator("ct_dt_poles")
    sim.initialize(params)
    return sim, sim.get_state()


@pytest.mark.parametrize("method,h", list(itertools.product(METHODS, H_VALUES)))
def test_poles_match_oracles(method, h):
    _, state = make(t_tau_ratio=h, method=method)
    info = state["metadata"]["system_info"]
    exact = control.sample_system(control.tf([1], [1, 1]), h, method="zoh").poles()[0].real
    assert abs(info["z_method"] - oracle_pole(method, h)) < 1e-12
    assert abs(info["z_exact"] - exact) < 1e-9
    assert abs(info["pole_error"] - (info["z_method"] - exact)) < 1e-9


@pytest.mark.parametrize("method,h", list(itertools.product(METHODS, [0.01, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0])))
def test_step_response_starts_at_rest_and_matches_closed_form(method, h):
    sim, _ = make(t_tau_ratio=h, method=method)
    r = sim._r
    n = r["n"].astype(float)
    with np.errstate(over="ignore", invalid="ignore"):
        closed = 1 - oracle_pole(method, h) ** n
    ok = np.isfinite(closed) & (np.abs(closed) < 1e12)
    assert r["y"][0] == 0.0
    assert r["t_n"][0] == 0.0 and abs(r["t_n"][1] - h) < 1e-12
    assert np.allclose(r["y"][ok], closed[ok], rtol=1e-9, atol=1e-9)
    assert np.allclose(r["y_ct"], 1 - np.exp(-r["t_ct"]))
    assert len(r["n"]) >= 11


def test_default_forward_euler_is_not_shifted():
    # Regression: the old recursion stored y[1] at t = 0 (y = T/tau instead of y(0) = 0).
    sim, state = make()
    samples = state["metadata"]["samples"]
    assert samples[0]["y_dt"] == 0.0 and samples[0]["t"] == 0.0
    assert abs(samples[1]["y_dt"] - 0.5) < 1e-12 and abs(samples[1]["t"] - 0.5) < 1e-12
    assert abs(samples[2]["y_dt"] - 0.75) < 1e-12


@pytest.mark.parametrize("h", H_VALUES)
def test_exact_zoh_reproduces_ct_samples(h):
    sim, state = make(t_tau_ratio=h, method="exact_zoh")
    assert np.allclose(sim._r["y"], sim._r["y_ct_n"], atol=1e-12)
    assert state["metadata"]["system_info"]["performance_rating"] == "EXACT"
    assert abs(state["metadata"]["system_info"]["pole_error"]) < 1e-12


@pytest.mark.parametrize("method,h", list(itertools.product(METHODS, H_VALUES)))
def test_stability_classification_and_rating(method, h):
    _, state = make(t_tau_ratio=h, method=method)
    info = state["metadata"]["system_info"]
    z = oracle_pole(method, h)
    expected = "stable" if abs(z) < 1 - 1e-9 else ("unstable" if abs(z) > 1 + 1e-9 else "marginal")
    assert info["stability"] == expected
    if expected != "stable":
        assert info["performance_rating"] == expected.upper()
        assert info["rms_error"] is None


def test_forward_euler_at_two_is_marginal():
    _, state = make(t_tau_ratio=2.0, method="forward_euler")
    info = state["metadata"]["system_info"]
    assert info["z_method"] == -1.0
    assert info["stability"] == "marginal"
    assert "constant amplitude" in info["mode_behavior"]


@pytest.mark.parametrize("method,h", list(itertools.product(METHODS, H_VALUES)))
def test_equivalent_ct_pole_round_trips(method, h):
    _, state = make(t_tau_ratio=h, method=method)
    info = state["metadata"]["system_info"]
    s_eq = info["s_equivalent"]
    if s_eq["kind"] == "deadbeat":
        assert abs(info["z_method"]) < 1e-9
        return
    assert abs(np.exp(complex(s_eq["re"], s_eq["im"]) * h) - info["z_method"]) < 1e-9
    assert (s_eq["kind"] == "pair") == (info["z_method"] < 0)
    if method == "exact_zoh":
        assert abs(s_eq["re"] + 1.0) < 1e-9 and s_eq["im"] == 0.0


def test_equivalent_pole_crosses_jw_axis_exactly_at_fe_limit():
    _, state = make(t_tau_ratio=2.0, method="forward_euler")
    s_eq = state["metadata"]["system_info"]["s_equivalent"]
    assert abs(s_eq["re"]) < 1e-12 and abs(s_eq["im"] - math.pi / 2) < 1e-12


def test_unstable_case_shows_enough_samples_and_marks_off_scale():
    _, state = make(t_tau_ratio=2.2, method="forward_euler")
    response = next(p for p in state["plots"] if p["id"] == "response")
    off = [t for t in response["data"] if t.get("name") == "off-scale y[n]"]
    shown = next(t for t in response["data"] if t.get("name", "").endswith("y[n]") and t.get("name") != "off-scale y[n]")
    assert len(shown["x"]) + sum(len(t["x"]) for t in off) >= 11
    assert off, "diverging samples must be marked, not hidden"
    ylo, yhi = response["layout"]["yaxis"]["range"]
    assert all(ylo <= v <= yhi for v in shown["y"])


def test_axis_ranges_are_explicit():
    _, state = make()
    for plot in state["plots"]:
        for ax in ("xaxis", "yaxis"):
            assert plot["layout"][ax]["autorange"] is False
            lo, hi = plot["layout"][ax]["range"]
            assert lo < hi


def test_guided_scenario_sets_all_state_and_manual_change_clears_it():
    sim, _ = make(t_tau_ratio=0.7, method="trapezoidal")
    state = sim.update_parameter("guided_scenario", "3")
    assert state["parameters"] == {"t_tau_ratio": 2.2, "method": "forward_euler", "guided_scenario": "3"}
    assert state["metadata"]["guided"]["index"] == 3
    state = sim.update_parameter("method", "backward_euler")
    assert state["parameters"]["guided_scenario"] == "none" and state["metadata"]["guided"] is None
    assert state["parameters"]["t_tau_ratio"] == 2.2


# (method pole, exact pole) quoted in each guided-scenario message; None = not quoted.
SCENARIO_CLAIMS = {0: (0.70, 0.741), 1: (0.0, 0.368), 2: (-0.8, None), 3: (-1.2, None), 4: (0.3125, 0.111),
                   5: (-0.0476, 0.111), 6: (0.1108, 0.1108)}


@pytest.mark.parametrize("idx", range(len(CTDTPolesSimulator.GUIDED_SCENARIOS)))
def test_every_guided_scenario_message_numbers_are_true(idx):
    assert set(SCENARIO_CLAIMS) == set(range(len(CTDTPolesSimulator.GUIDED_SCENARIOS)))
    _, state = make(guided_scenario=str(idx))
    info = state["metadata"]["system_info"]
    z_claim, exact_claim = SCENARIO_CLAIMS[idx]
    assert abs(info["z_method"] - z_claim) < 5e-4
    if exact_claim is not None:
        assert abs(info["z_exact"] - exact_claim) < 5e-4


def test_initial_condition_controls_are_not_part_of_this_tool():
    # Initial conditions live in dt_difference_equation / ode_laplace_solver, not here.
    sim, state = make(y0=1.5, input_type="zero")
    assert set(state["parameters"]) == {"t_tau_ratio", "method", "guided_scenario"}
    assert sim._r["y"][0] == 0.0


def test_state_serializes_and_reset_restores_defaults():
    sim, _ = make(t_tau_ratio=2.7, method="trapezoidal")
    json.dumps(DataHandler.serialize_result(sim.get_state()))
    state = sim.reset()
    assert state["parameters"] == CTDTPolesSimulator.DEFAULT_PARAMS
