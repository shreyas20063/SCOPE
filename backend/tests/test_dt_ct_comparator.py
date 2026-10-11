"""Oracle tests for the DT <-> CT Comparator (simulation: ``dt_ct_comparator``).

Oracles (closed forms, independent of the simulator):
    DT  H(z) = 1/(1 - p z^-1)  ->  h[n] = p^n u[n]   stable <=> |p| < 1
    CT  H(s) = 1/(s - p)       ->  h(t) = e^{pt} u(t) stable <=> Re(p) < 0
    Sampling e^{pt} at period T gives the DT pole z = e^{pT}, so
    |e^{pT}| < 1 <=> p < 0 (sampling never changes stability).

Boundary points (Ogata / Oppenheim-Willsky): a simple pole on |z| = 1 or on
the jw-axis gives a bounded, non-decaying mode -- "marginal", not divergent.
p = 0 in DT is the impulse delta[n] (FIR, stable).
"""

import json
import math
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.data_handler import DataHandler  # noqa: E402
from simulations import SIMULATOR_REGISTRY  # noqa: E402
from simulations.dt_ct_comparator import DTCTComparatorSimulator  # noqa: E402

POLES = [-1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5]

# p -> (dt_status, ct_status, agreement)   [agreement = quiz answer key]
EXPECTED_CLASS = {
    -1.5: ("Unstable", "Stable", "ct_only"),
    -1.0: ("Marginal", "Stable", "ct_only"),
    -0.5: ("Stable", "Stable", "both_stable"),
    0.0: ("Stable", "Marginal", "dt_only"),
    0.5: ("Stable", "Unstable", "dt_only"),
    1.0: ("Marginal", "Unstable", "neither_stable"),
    1.5: ("Unstable", "Unstable", "neither_stable"),
}


def _sim(**params):
    sim = DTCTComparatorSimulator("dt_ct_comparator")
    sim.initialize(params or None)
    return sim


def _state(p, **params):
    sim = _sim(p=p, **params)
    return sim.get_state()


def _marker_trace(plot):
    """DT plot: the markers trace carries one y value per sample."""
    return next(t for t in plot["data"] if t.get("mode") == "markers")


def test_registered():
    assert SIMULATOR_REGISTRY["dt_ct_comparator"] is DTCTComparatorSimulator


@pytest.mark.parametrize("p", POLES)
@pytest.mark.parametrize("N", [5, 20, 30])
def test_dt_response_matches_closed_form_unclipped(p, N):
    state = _state(p, num_samples=N)
    dt_plot = next(pl for pl in state["plots"] if pl["id"] == "dt_response")
    markers = _marker_trace(dt_plot)
    n = np.arange(N)
    oracle = np.array([p ** k for k in n], dtype=float)  # Python: 0.0 ** 0 == 1.0
    assert markers["x"] == list(range(N))
    assert np.allclose(markers["y"], oracle, rtol=1e-12, atol=0.0)


def test_dt_unstable_is_not_clipped():
    # Former bug: values were clipped at +-50 -> fake plateau / constant amplitude.
    y = _marker_trace(_state(1.5)["plots"][0])["y"]
    assert math.isclose(y[-1], 1.5 ** 19, rel_tol=1e-12)
    assert all(b > a for a, b in zip(y, y[1:]))  # strictly increasing, no plateau
    y_neg = _marker_trace(_state(-1.5)["plots"][0])["y"]
    mags = [abs(v) for v in y_neg]
    assert all(b > a for a, b in zip(mags, mags[1:]))  # |y| keeps growing
    assert all(np.sign(y_neg[k]) == (-1) ** k for k in range(len(y_neg)))
    # Worst case in the schema: p = 2, N = 30 -> 2^29
    y_max = _marker_trace(_state(2.0, num_samples=30)["plots"][0])["y"]
    assert y_max[-1] == 2.0 ** 29


@pytest.mark.parametrize("p", POLES)
@pytest.mark.parametrize("duration", [1.0, 4.0, 8.0])
def test_ct_response_matches_closed_form_unclipped(p, duration):
    state = _state(p, ct_duration=duration)
    ct_plot = next(pl for pl in state["plots"] if pl["id"] == "ct_response")
    main = ct_plot["data"][0]
    t = np.asarray(main["x"])
    assert t[0] == 0.0 and math.isclose(t[-1], duration)
    assert np.allclose(main["y"], np.exp(p * t), rtol=1e-12, atol=0.0)


def test_ct_unstable_is_not_clipped():
    main = _state(1.5, ct_duration=4.0)["plots"][1]["data"][0]
    assert math.isclose(main["y"][-1], math.exp(6.0), rel_tol=1e-12)
    assert all(b > a for a, b in zip(main["y"], main["y"][1:]))
    worst = _state(2.0, ct_duration=8.0)["plots"][1]["data"][0]
    assert math.isclose(worst["y"][-1], math.exp(16.0), rel_tol=1e-12)


@pytest.mark.parametrize("p", POLES)
def test_y_axis_range_contains_all_data(p):
    for plot in _state(p)["plots"]:
        lo, hi = plot["layout"]["yaxis"]["range"]
        ys = [v for tr in plot["data"] for v in tr["y"] if v is not None]
        assert lo < min(ys) and hi > max(ys)


@pytest.mark.parametrize("p", POLES)
def test_classification(p):
    meta = _state(p)["metadata"]
    dt_status, ct_status, agreement = EXPECTED_CLASS[p]
    assert meta["dt_status"] == dt_status
    assert meta["ct_status"] == ct_status
    assert meta["agreement"] == agreement
    assert meta["dt_stable"] == (abs(p) < 1)
    assert meta["ct_stable"] == (p < 0)
    assert meta["dt_is_alternating"] == (p < 0)


def test_insight_text_at_marginal_and_special_points():
    insight = {p: _state(p)["metadata"]["insight"] for p in POLES}

    # p = 0: DT is delta[n] (stable FIR), CT is the constant 1 (marginal)
    assert "impulse" in insight[0.0] and "δ[n]" in insight[0.0]
    assert "CT stays constant" in insight[0.0] and "marginal" in insight[0.0]
    # p = 1: DT constant (marginal), CT grows
    assert "DT stays constant at 1 (marginal)" in insight[1.0]
    assert "CT grows without bound" in insight[1.0]
    # p = -1: DT alternates with constant amplitude (marginal), CT decays
    assert "DT alternates ±1 with constant amplitude (marginal)" in insight[-1.0]
    assert "CT decays to zero" in insight[-1.0]
    # Marginal / FIR responses are never described as divergent
    for p in (-1.0, 0.0, 1.0):
        dt_part = insight[p].split(", but ")[0]
        assert "grow" not in dt_part and "diverg" not in dt_part
    assert "diverg" not in insight[0.0]

    assert insight[-1.5] == "DT grows without bound (alternating sign), but CT decays to zero"
    assert insight[-0.5] == "Both decay to zero (DT alternates in sign)"
    assert insight[0.5] == "DT decays to zero, but CT grows without bound"
    assert insight[1.5] == "Both grow without bound"


@pytest.mark.parametrize("p", POLES)
def test_descriptions_match_closed_form_behaviour(p):
    meta = _state(p)["metadata"]
    dt_tail = abs(p) ** 50
    ct_tail = math.exp(p * 50)
    if p == 0:
        assert "impulse" in meta["dt_description"]
    elif dt_tail < 1e-6:
        assert "decays" in meta["dt_description"]
    elif dt_tail == 1.0:
        assert "marginal" in meta["dt_description"]
    else:
        assert "grows without bound" in meta["dt_description"]
    if ct_tail < 1e-6:
        assert "decays" in meta["ct_description"]
    elif ct_tail == 1.0:
        assert "marginal" in meta["ct_description"]
    else:
        assert "grows without bound" in meta["ct_description"]


@pytest.mark.parametrize("p", POLES)
def test_sampled_pole_is_exp_pT_and_preserves_ct_stability(p):
    meta = _state(p)["metadata"]
    T = meta["sampling_period"]
    assert T > 0
    z = math.exp(p * T)
    assert math.isclose(meta["sampled_pole"], round(z, 4), abs_tol=1e-12)
    expected_location = "inside" if p < 0 else ("on" if p == 0 else "outside")
    assert meta["sampled_pole_location"] == expected_location
    # |e^{pT}| < 1 exactly when CT is stable -- unlike reusing the number p
    assert (abs(z) < 1) == meta["ct_stable"]


@pytest.mark.parametrize("p", POLES)
def test_growth_annotation_only_when_unstable(p):
    dt_plot, ct_plot = _state(p)["plots"]
    dt_status, ct_status, _ = EXPECTED_CLASS[p]
    dt_ann = [a["text"] for a in dt_plot["layout"]["annotations"]]
    ct_ann = [a["text"] for a in ct_plot["layout"]["annotations"]]
    assert bool(dt_ann) == (dt_status == "Unstable")
    assert bool(ct_ann) == (ct_status == "Unstable")
    for text in dt_ann + ct_ann:
        assert "Grows without bound" in text


def test_growth_annotation_reports_true_final_value():
    dt_plot, ct_plot = _state(1.5, num_samples=20, ct_duration=4.0)["plots"]
    assert f"{1.5 ** 19:.4g}" in dt_plot["layout"]["annotations"][0]["text"]
    assert f"{math.exp(6.0):.4g}" in ct_plot["layout"]["annotations"][0]["text"]


@pytest.mark.parametrize("N", list(range(5, 31)))
def test_dt_x_axis_ticks_stay_within_samples(N):
    # Former bug: dtick=1 with Plotly's padded autorange -> 22 rotated labels
    # including -1 and N, outside the samples n = 0..N-1.
    xaxis = _state(0.5, num_samples=N)["plots"][0]["layout"]["xaxis"]
    lo, hi = xaxis["range"]
    assert lo == -0.5 and hi == N - 0.5
    assert xaxis["tickangle"] == 0
    if N <= 10:
        assert xaxis["tickmode"] == "linear"
        ticks = np.arange(xaxis["tick0"], hi, xaxis["dtick"])
        assert ticks.min() >= 0 and ticks.max() <= N - 1
        assert len(ticks) <= 10
    else:
        # Plotly auto ticks: 5..10 ticks over a span of N >= 11 -> integer step >= 2
        assert xaxis["tickmode"] == "auto"
        assert "dtick" not in xaxis
        assert (hi - lo) / 10 > 1


def test_trace_colour_tracks_status():
    colors = DTCTComparatorSimulator.STATUS_COLORS
    for p in POLES:
        dt_plot, ct_plot = _state(p)["plots"]
        dt_status, ct_status, _ = EXPECTED_CLASS[p]
        assert _marker_trace(dt_plot)["marker"]["color"] == colors[dt_status]
        assert ct_plot["data"][0]["line"]["color"] == colors[ct_status]


def test_quiz_answer_key_matches_classification():
    sim = _sim()
    sim.update_parameter("mode", "quiz")
    for _ in range(40):
        sim.handle_action("new_quiz", {})
        q = sim.get_state()["metadata"]
        assert q["quiz"]["quiz_p"] == q["pole_value"]
        assert sim._quiz_answer == sim._classify_stability(sim._quiz_p)["agreement"]


def _plot_cues(state):
    """(trace colours, annotation texts) for both response plots."""
    dt_plot, ct_plot = state["plots"]
    colours = {
        "dt_stems": dt_plot["data"][0]["line"]["color"],
        "dt_markers": _marker_trace(dt_plot)["marker"]["color"],
        "ct_line": ct_plot["data"][0]["line"]["color"],
    }
    texts = [a["text"] for pl in (dt_plot, ct_plot) for a in pl["layout"]["annotations"]]
    return colours, texts


@pytest.mark.parametrize("idx", range(12))
def test_open_quiz_question_hides_stability_cues(idx, monkeypatch):
    # Former leak: in quiz mode the plots (built for the quiz pole) carried the
    # "Grows without bound" note on exactly the unstable panel(s) and
    # status-coloured traces, i.e. the answer to "which system(s) are stable?".
    import simulations.dt_ct_comparator as mod
    monkeypatch.setattr(mod.random, "choice", lambda seq: seq[idx])
    neutral = DTCTComparatorSimulator.QUIZ_NEUTRAL_COLOR
    assert neutral not in DTCTComparatorSimulator.STATUS_COLORS.values()

    sim = _sim()
    state = sim.update_parameter("mode", "quiz")
    meta = state["metadata"]
    assert meta["quiz"]["answered"] is False
    colours, texts = _plot_cues(state)
    assert texts == []
    assert set(colours.values()) == {neutral}

    # Once the answer is checked, the plots reveal the status cues as feedback
    state = sim.handle_action("check_quiz", {"answer": "both_stable"})
    colours, texts = _plot_cues(state)
    status = DTCTComparatorSimulator.STATUS_COLORS
    assert colours["dt_stems"] == colours["dt_markers"] == status[meta["dt_status"]]
    assert colours["ct_line"] == status[meta["ct_status"]]
    expected_notes = [meta["dt_status"], meta["ct_status"]].count("Unstable")
    assert len(texts) == expected_notes
    assert all("Grows without bound" in t for t in texts)

    # A new question hides them again
    colours, texts = _plot_cues(sim.handle_action("new_quiz", {}))
    assert texts == [] and set(colours.values()) == {neutral}


def test_explore_mode_keeps_stability_cues():
    # The quiz rule must not leak into explore mode (or survive leaving quiz mode)
    sim = _sim(p=1.5)
    sim.update_parameter("mode", "quiz")
    state = sim.update_parameter("mode", "explore")
    colours, texts = _plot_cues(state)
    red = DTCTComparatorSimulator.STATUS_COLORS["Unstable"]
    assert set(colours.values()) == {red}
    assert len(texts) == 2


@pytest.mark.parametrize("p", [-2.0, -1.0, 0.0, 1.0, 2.0])
def test_state_serializes_to_json(p):
    state = DataHandler.serialize_result(_state(p, num_samples=30, ct_duration=8.0))
    text = json.dumps(state, allow_nan=False)
    assert "Infinity" not in text and "NaN" not in text
