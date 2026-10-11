"""DT Difference Equation Solver (dt_difference_equation): initial conditions.

The reference below is an independent, clean-room transcription of the
textbook solution (Oppenheim & Willsky Sec. 2.4.2 and 1.6.6, Oppenheim &
Schafer Sec. 2.5, Lathi Ch. 3). It does not import or reuse any simulator
code. Four reference computations are used:

* ``_ref_recursion``  - the LCCDE solved forward from n = 0 sample by sample;
* ``_ref_lfilter``    - scipy.signal.lfilter with zi = lfiltic(b, a,
                        y=[y[-1], ...]);
* ``_ref_register``   - the feedback delay register of the block diagram
                        drawn from the equation, q[0] = y[-1];
* ``_ref_closed_form``- hand-derived unilateral-z closed forms of the
                        total, zero-input (ZIR) and zero-state (ZSR) responses.

Conventions: sum_k a_k y[n-k] = sum_k b_k x[n-k], a_0 = 1, causal input.
Initial conditions are the auxiliary conditions y[-1], ..., y[-N] of a
recursive equation. A non-recursive equation (N = 0: difference machine,
moving average) needs none (O&W Sec. 2.4.2): x[-1] is an input sample, 0 for
a causal input, so those presets take no IC and their ZIR is 0.

y[-1] = 0 is initial rest, which must reproduce the pre-change tool exactly:
``PRE_CHANGE_SHA256`` holds fingerprints of every observable output of the
simulator *before* the IC feature was added (metadata keys and plots that
existed then, over a forward / backward / advance / update / reset action
sequence), captured from git HEAD dt_difference_equation.py on 2026-10-11.

Run from backend/:  python -m pytest tests/test_dt_difference_equation_ic.py
"""

import hashlib
import json
import uuid
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pytest
from scipy.signal import lfilter, lfiltic

from simulations.dt_difference_equation import DifferenceEquationSimulator

SIM_ID = "dt_difference_equation"
N_MAX = 15
TOL = 1e-10
META_TOL = 5.1e-7          # metadata values are rounded to 6 decimals

# ---------------------------------------------------------------------------
# Independent reference (textbook; no simulator code)
# ---------------------------------------------------------------------------

# preset -> (b, a)
REF: Dict[str, Tuple[Tuple[float, ...], Tuple[float, ...]]] = {
    "difference_machine": ((1.0, -1.0), (1.0,)),
    "accumulator": ((1.0,), (1.0, -1.0)),
    "moving_average": ((0.5, 0.5), (1.0,)),
    "leaky_integrator": ((0.1,), (1.0, -0.9)),
}
PRESETS = list(REF)
RECURSIVE = ["accumulator", "leaky_integrator"]           # N = 1: need y[-1]
NON_RECURSIVE = ["difference_machine", "moving_average"]  # N = 0: need nothing
INPUTS = ["impulse", "step", "ramp"]
IC_VALUES = [0.5, -1.0, 1.0, 2.5, -0.3, 0.1, -5.0]
IC_PARAM = "ic_y_minus_1"
STRAY_PARAM = "ic_x_minus_1"   # an earlier draft offered x[-1]; must be inert


def _ref_input(kind: str, n_max: int = N_MAX) -> np.ndarray:
    """Causal x[0..n_max]; ramp[0] = 0."""
    n = np.arange(n_max + 1, dtype=float)
    return {"impulse": (n == 0).astype(float), "step": np.ones_like(n), "ramp": n}[kind]


def _ref_recursion(b: Sequence[float], a: Sequence[float], x: np.ndarray,
                   y_past: Sequence[float] = ()) -> np.ndarray:
    """y[n] = sum b_k x[n-k] - sum_{k>=1} a_k y[n-k], from n = 0; x[n<0] = 0."""
    N, M = len(a) - 1, len(b) - 1
    yp = list(y_past)[:N] + [0.0] * max(0, N - len(y_past))
    y: List[float] = []
    for n in range(len(x)):
        acc = sum(b[k] * (x[n - k] if n - k >= 0 else 0.0) for k in range(M + 1))
        acc -= sum(a[k] * (y[n - k] if n - k >= 0 else yp[k - n - 1]) for k in range(1, N + 1))
        y.append(acc / a[0])
    return np.array(y)


def _ref_lfilter(b: Sequence[float], a: Sequence[float], x: np.ndarray,
                 y_past: Sequence[float] = ()) -> np.ndarray:
    """lfilter with zi = lfiltic(b, a, y=[y[-1], ...]) (x[-k] = 0)."""
    yp = list(y_past)[: len(a) - 1] or [0.0]
    zi = lfiltic(b, a, y=yp)
    y, _ = lfilter(b, a, x, zi=zi)
    return np.asarray(y)


def _ref_register(preset: str, x: np.ndarray, c: float) -> Tuple[np.ndarray, np.ndarray]:
    """Recursive presets. (y, q): q[n] = feedback delay content at the START of step n."""
    q = c
    ys, qs = [], []
    for xn in x:
        qs.append(q)
        yn = xn + q if preset == "accumulator" else 0.9 * q + 0.1 * xn
        q = yn
        ys.append(yn)
    qs.append(q)
    return np.array(ys), np.array(qs)


def _ref_closed_form(preset: str, kind: str, c: float, n_max: int = N_MAX) -> Dict[str, np.ndarray]:
    """Closed-form ZIR / ZSR / total for n = 0..n_max (unilateral z), y[-1] = c."""
    n = np.arange(n_max + 1, dtype=float)
    d, d1, u1 = (n == 0) * 1.0, (n == 1) * 1.0, (n >= 1) * 1.0
    if preset in NON_RECURSIVE:
        assert c == 0.0, "a non-recursive equation has no initial condition"
        zir = np.zeros_like(n)
        if preset == "difference_machine":
            zsr = {"impulse": d - d1, "step": d, "ramp": u1}[kind]
        else:
            zsr = {"impulse": 0.5 * d + 0.5 * d1, "step": 1.0 - 0.5 * d, "ramp": (n - 0.5) * u1}[kind]
    elif preset == "accumulator":
        zir = c * np.ones_like(n)
        zsr = {"impulse": np.ones_like(n), "step": n + 1.0, "ramp": n * (n + 1.0) / 2.0}[kind]
    else:
        zir = c * 0.9 ** (n + 1)
        zsr = {"impulse": 0.1 * 0.9 ** n, "step": 1.0 - 0.9 ** (n + 1),
               "ramp": n - 9.0 + 9.0 * 0.9 ** n}[kind]
    return {"zir": zir, "zsr": zsr, "total": zir + zsr}


def _ref_total(preset: str, kind: str, c: float) -> np.ndarray:
    b, a = REF[preset]
    return _ref_recursion(b, a, _ref_input(kind), y_past=[c])


def test_reference_methods_agree() -> None:
    """Sanity check on the reference itself: the methods agree everywhere."""
    for preset, (b, a) in REF.items():
        h = _ref_recursion(b, a, _ref_input("impulse"))
        for kind in INPUTS:
            x = _ref_input(kind)
            for c in [0.0] + (IC_VALUES if preset in RECURSIVE else []):
                y1 = _ref_recursion(b, a, x, y_past=[c])
                y2 = _ref_lfilter(b, a, x, y_past=[c])
                cf = _ref_closed_form(preset, kind, c)
                assert np.allclose(y1, y2, atol=TOL, rtol=0)
                assert np.allclose(y1, cf["total"], atol=TOL, rtol=0)
                assert np.allclose(cf["zsr"], np.convolve(x, h)[: N_MAX + 1], atol=TOL, rtol=0)
                if preset in RECURSIVE:
                    y3, q = _ref_register(preset, x, c)
                    assert np.allclose(y1, y3, atol=TOL, rtol=0)
                    assert q[0] == c


# ---------------------------------------------------------------------------
# Helpers on the simulator (public API only, plus the raw y history)
# ---------------------------------------------------------------------------

def _make(preset: str, kind: str = "impulse", **params: Any) -> DifferenceEquationSimulator:
    sim = DifferenceEquationSimulator(SIM_ID)
    sim.initialize({"equation_preset": preset, "input_signal": kind, **params})
    return sim


def _run_to_end(sim: DifferenceEquationSimulator) -> Dict[str, Any]:
    state = sim.get_state()
    while state["metadata"]["can_step_forward"]:
        state = sim.step_forward()
    return state


def _traces_named(plot: Dict[str, Any], name: str) -> List[Dict[str, Any]]:
    return [t for t in plot["data"] if t.get("name") == name]


def _plot(state: Dict[str, Any], plot_id: str) -> Dict[str, Any]:
    return next(p for p in state["plots"] if p["id"] == plot_id)


# ---------------------------------------------------------------------------
# 1. Initial rest reproduces the pre-change tool exactly
# ---------------------------------------------------------------------------

PRE_CHANGE_SHA256 = {
    "difference_machine/impulse": "bf227a9a3a79328ed769dea7463ab3ab5119bad0d3e2e19df70e73d4174e47dd",
    "difference_machine/step": "e8edd07e1c4b2218dda0390c4958c10e255ea5abd59920ea8ecc579b9c86f307",
    "difference_machine/ramp": "5443e65cf8b7924ab6c7a830a23e3e54417a0de7a232b1b021299872d1378151",
    "accumulator/impulse": "7d4d6f4d61ca93d76865e6e41ee7f6f2e40df433a866f7a3aba86bd946311b5a",
    "accumulator/step": "1de35b448b4464f66d21578ab58d0a8f103d1c2ec7276f9fae003d5e4acdfa10",
    "accumulator/ramp": "d1b9f946b25d1fccdda22cb1094d8516eeb8b807e5046a2347de4acd31522aad",
    "moving_average/impulse": "3bfbdcff0a9b5de14348f421590d233e6947cf4a2315ffa3e0d9d9440bc7cb12",
    "moving_average/step": "26497edf4db4cecec9575e4d69dad219ab79164dc3734c0fcfa36050d4cfc368",
    "moving_average/ramp": "4c5825fcec16f23fcf299f734432b3451342fecd8f830ec2ac7bb0a3e4180c6a",
    "leaky_integrator/impulse": "1a2cb9f13f198d117b2e71fb458eb1181299d81596876eab8b3ff4465355b32f",
    "leaky_integrator/step": "4a7cf252b67c900febfa571b04e56aa81719a192484d2525752692a1e645c6cb",
    "leaky_integrator/ramp": "7e8a5cd5429e87cd6a5b2c5cc2532e18f27bbc3090a617a392aaf763dde9171b",
}

PRE_CHANGE_META_KEYS = [
    "simulation_type", "hub_slots", "hub_domain", "hub_dimensions",
    "has_custom_viewer", "current_n", "is_at_rest", "can_step_back",
    "can_step_forward", "equation_text", "equation_preset",
    "equation_description", "diagram_type", "wire_values", "delay_states",
    "substitution_history", "x_values", "y_values", "input_signal_type",
]
PRE_CHANGE_PARAMS = ("equation_preset", "input_signal", "animation_speed")


def _snap(state: Dict[str, Any]) -> Dict[str, Any]:
    """Everything that was observable before the IC feature existed."""
    md = state["metadata"]
    sub = {k: md[k] for k in PRE_CHANGE_META_KEYS}
    sub["substitution_history"] = [
        {k: e[k] for k in ("n", "text", "result")} for e in md["substitution_history"]
    ]
    params = {k: state["parameters"][k] for k in PRE_CHANGE_PARAMS}
    plots = [{"id": p["id"], "title": p["title"], "data": p["data"], "layout": p["layout"]}
             for p in state["plots"]]
    return {"parameters": params, "metadata": sub, "plots": plots}


def _fingerprint(preset: str, kind: str, **params: Any) -> str:
    """SHA-256 of the observable outputs over a fixed action sequence."""
    sim = _make(preset, kind, **params)
    seq = [_snap(sim.get_state())]
    for _ in range(20):
        seq.append(_snap(sim.step_forward()))
    for _ in range(6):
        seq.append(_snap(sim.step_backward()))
    for _ in range(3):
        seq.append(_snap(sim.advance_frame()))
    for _ in range(30):
        seq.append(_snap(sim.step_backward()))
    seq.append(_snap(sim.step_forward()))
    seq.append(_snap(sim.update_parameter("input_signal", kind)))
    seq.append(_snap(sim.step_forward()))
    seq.append(_snap(sim.update_parameter("animation_speed", 2.0)))
    seq.append(_snap(sim.reset()))
    canon = json.dumps(seq, sort_keys=True, separators=(",", ":"), allow_nan=True)
    return hashlib.sha256(canon.encode()).hexdigest()


@pytest.mark.parametrize("preset", PRESETS)
@pytest.mark.parametrize("kind", INPUTS)
def test_initial_rest_is_byte_identical_to_pre_change(preset: str, kind: str) -> None:
    """Defaults (y[-1] = 0) reproduce every pre-change output exactly."""
    assert _fingerprint(preset, kind) == PRE_CHANGE_SHA256[f"{preset}/{kind}"]


@pytest.mark.parametrize("preset", PRESETS)
@pytest.mark.parametrize("kind", INPUTS)
def test_unused_ic_has_no_effect(preset: str, kind: str) -> None:
    """Non-recursive presets ignore a hidden y[-1] and the split checkbox;
    no preset reacts to a stray x[-1] parameter."""
    if preset in NON_RECURSIVE:
        params = {IC_PARAM: 3.7, STRAY_PARAM: 3.7, "show_decomposition": True}
    else:
        params = {IC_PARAM: 0.0, STRAY_PARAM: 3.7}
    assert _fingerprint(preset, kind, **params) == PRE_CHANGE_SHA256[f"{preset}/{kind}"]


@pytest.mark.parametrize("preset", PRESETS)
@pytest.mark.parametrize("kind", INPUTS)
def test_initial_rest_output_is_lfilter_without_zi(preset: str, kind: str) -> None:
    """Initial rest: y = 0 for n = -2, -1 and y = lfilter(b, a, x) for n >= 0."""
    b, a = REF[preset]
    state = _run_to_end(_make(preset, kind))
    md = state["metadata"]
    assert md["initial_conditions"]["mode"] == "initial_rest"
    assert md["initial_conditions"]["recursive"] is (preset in RECURSIVE)
    assert md["y_values"]["n"] == list(range(-2, N_MAX + 1))
    expected = np.concatenate([[0.0, 0.0], lfilter(b, a, _ref_input(kind))])
    assert np.allclose(md["y_values"]["values"], expected, atol=META_TOL, rtol=0)
    for p in state["plots"]:
        assert not _traces_named(p, "initial condition")


# ---------------------------------------------------------------------------
# 2. Non-recursive presets need no auxiliary conditions (O&W Sec. 2.4.2)
# ---------------------------------------------------------------------------

def test_no_x_initial_condition_parameter() -> None:
    assert STRAY_PARAM not in DifferenceEquationSimulator.PARAMETER_SCHEMA
    assert STRAY_PARAM not in DifferenceEquationSimulator.DEFAULT_PARAMS
    assert list(DifferenceEquationSimulator.IC_PARAMS.values()) == [IC_PARAM]


@pytest.mark.parametrize("preset", NON_RECURSIVE)
@pytest.mark.parametrize("kind", INPUTS)
def test_non_recursive_presets_take_no_initial_conditions(preset: str, kind: str) -> None:
    b, a = REF[preset]
    sim = _make(preset, kind, **{IC_PARAM: 2.5, STRAY_PARAM: -2.5, "show_decomposition": True})
    md = sim.get_state()["metadata"]
    ic = md["initial_conditions"]
    assert ic["recursive"] is False and ic["mode"] == "initial_rest"
    assert ic["items"] == [] and ic["register"] is None and ic["zir_latex"] is None
    assert ic["start_n"] == -3 and md["current_n"] == -3 and md["is_at_rest"] is True
    assert md["delay_states"] == [0.0]
    assert md["show_decomposition"] is False and md["ic_samples"] == {"y": None}
    state = _run_to_end(sim)
    md = state["metadata"]
    assert [p["id"] for p in state["plots"]] == ["input_signal", "output_signal"]
    for p in state["plots"]:
        assert not _traces_named(p, "initial condition")
    expected = np.concatenate([[0.0, 0.0], lfilter(b, a, _ref_input(kind))])
    assert np.allclose(md["y_values"]["values"], expected, atol=META_TOL, rtol=0)
    assert np.allclose(md["y_values"]["values"][2:], _ref_closed_form(preset, kind, 0.0)["total"],
                       atol=META_TOL, rtol=0)
    assert md["decomposition"]["zir"] == [0.0] * (N_MAX + 1)          # ZIR of an FIR system is 0
    assert all("ic_terms" not in e for e in md["substitution_history"])
    # Moving the hidden y[-1] slider mid-run changes no number
    before = sim.get_state()["metadata"]
    after = sim.update_parameter(IC_PARAM, -4.0)["metadata"]
    for key in ("current_n", "y_values", "x_values", "substitution_history", "wire_values",
                "delay_states", "decomposition", "initial_conditions"):
        assert after[key] == before[key], key


@pytest.mark.parametrize("preset,kind,text", [
    ("difference_machine", "impulse", "y[0] = x[0] − x[-1] = 1 − 0 = 1"),
    ("moving_average", "step", "y[0] = (x[0] + x[-1]) / 2 = (1 + 0) / 2 = 0.5"),
])
def test_non_recursive_n0_uses_causal_input(preset: str, kind: str, text: str) -> None:
    """x[-1] is an input sample: 0 for the causal input, never a stored IC."""
    sim = _make(preset, kind, **{IC_PARAM: 1.5})
    for _ in range(3):                                   # n = -2, -1, 0
        md = sim.step_forward()["metadata"]
    assert md["current_n"] == 0
    assert md["substitution_history"][-1]["text"] == text


# ---------------------------------------------------------------------------
# 3. Recursive presets with y[-1] != 0: total, ZIR, ZSR against the reference
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("preset", RECURSIVE)
@pytest.mark.parametrize("kind", INPUTS)
@pytest.mark.parametrize("c", IC_VALUES)
@pytest.mark.parametrize("stray", [0.0, 7.0])
def test_total_zir_zsr_match_reference(preset: str, kind: str, c: float, stray: float) -> None:
    b, a = REF[preset]
    sim = _make(preset, kind, **{IC_PARAM: c, STRAY_PARAM: stray})
    state = _run_to_end(sim)
    md = state["metadata"]
    x = _ref_input(kind)
    ref_total = _ref_recursion(b, a, x, y_past=[c])
    cf = _ref_closed_form(preset, kind, c)

    # Recursion starts at n = 0: nothing at n < 0 is computed
    assert md["y_values"]["n"] == list(range(0, N_MAX + 1))
    assert md["x_values"]["n"] == list(range(0, N_MAX + 1))
    assert np.allclose(md["x_values"]["values"], x, atol=0, rtol=0)  # input stays causal
    raw_y = np.array([sim._y_history[n] for n in range(N_MAX + 1)])
    assert np.allclose(raw_y, ref_total, atol=TOL, rtol=0)
    assert np.allclose(raw_y, _ref_lfilter(b, a, x, y_past=[c]), atol=TOL, rtol=0)
    assert np.allclose(raw_y, cf["total"], atol=TOL, rtol=0)
    assert np.allclose(md["y_values"]["values"], ref_total, atol=META_TOL, rtol=0)

    dec = md["decomposition"]
    assert dec["n"] == list(range(0, N_MAX + 1))
    zir, zsr, total = (np.array(dec[k]) for k in ("zir", "zsr", "total"))
    assert np.allclose(zir, cf["zir"], atol=META_TOL, rtol=0)
    assert np.allclose(zsr, cf["zsr"], atol=META_TOL, rtol=0)
    assert np.allclose(total, ref_total, atol=META_TOL, rtol=0)
    # Linearity of the decomposition: total = zero-input + zero-state
    assert np.allclose(zir + zsr, total, atol=2 * META_TOL, rtol=0)
    # Zero-input part is nonzero (zero input, nonzero output -> not linear)
    assert abs(zir[0]) > 0


@pytest.mark.parametrize("preset", RECURSIVE)
def test_decomposition_exact_on_raw_values(preset: str) -> None:
    """ZIR + ZSR from the simulator equals its own step-by-step total to 1e-12."""
    for kind in INPUTS:
        for c in IC_VALUES:
            sim = _make(preset, kind, **{IC_PARAM: c})
            _run_to_end(sim)
            dec = sim._decomposition()
            assert np.allclose(np.add(dec["zir"], dec["zsr"]), dec["total"], atol=1e-12, rtol=0)


@pytest.mark.parametrize("preset", RECURSIVE)
def test_incrementally_linear(preset: str) -> None:
    """O&W 1.6.6: output differences depend only on input differences, and
    the zero-input response is linear in the IC."""
    c = 0.8
    tot = {k: np.array(_run_to_end(_make(preset, k, **{IC_PARAM: c}))
                       ["metadata"]["y_values"]["values"]) for k in INPUTS}
    zsr = {k: _ref_closed_form(preset, k, 0.0)["total"] for k in INPUTS}
    assert np.allclose(tot["step"] - tot["impulse"], zsr["step"] - zsr["impulse"], atol=2 * META_TOL)
    assert np.allclose(tot["ramp"] - tot["step"], zsr["ramp"] - zsr["step"], atol=2 * META_TOL)
    z1 = np.array(_run_to_end(_make(preset, "step", **{IC_PARAM: c}))["metadata"]["decomposition"]["zir"])
    z2 = np.array(_run_to_end(_make(preset, "step", **{IC_PARAM: 2 * c}))["metadata"]["decomposition"]["zir"])
    assert np.allclose(z2, 2 * z1, atol=2 * META_TOL)


def test_worked_examples_from_derivation() -> None:
    """Spot values quoted in the derivation (y[-1] = 0.5, n = 0..5)."""
    cases = {
        ("accumulator", "impulse"): [1.5, 1.5, 1.5, 1.5, 1.5, 1.5],
        ("accumulator", "step"): [1.5, 2.5, 3.5, 4.5, 5.5, 6.5],
        ("accumulator", "ramp"): [0.5, 1.5, 3.5, 6.5, 10.5, 15.5],
        ("leaky_integrator", "impulse"): [0.55, 0.495, 0.4455, 0.40095, 0.360855, 0.32477],
        ("leaky_integrator", "step"): [0.55, 0.595, 0.6355, 0.67195, 0.704755, 0.734279],
    }
    for (preset, kind), expected in cases.items():
        y = _run_to_end(_make(preset, kind, **{IC_PARAM: 0.5}))["metadata"]["y_values"]["values"][:6]
        assert np.allclose(y, expected, atol=1e-6), (preset, kind, y)
    # Edge cases: an IC that cancels or continues the input
    edge = [("accumulator", "impulse", -1.0, 0.0), ("leaky_integrator", "step", 1.0, 1.0)]
    for preset, kind, c, const in edge:
        y = _run_to_end(_make(preset, kind, **{IC_PARAM: c}))["metadata"]["y_values"]["values"]
        assert np.allclose(y, const, atol=1e-6), (preset, kind, c, y)


# ---------------------------------------------------------------------------
# 4. Step-by-step substitution uses the IC at n = 0
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("preset,kind,c,text", [
    ("accumulator", "impulse", 0.5, "y[0] = x[0] + y[-1] = 1 + 0.5 = 1.5"),
    ("accumulator", "impulse", -0.5, "y[0] = x[0] + y[-1] = 1 + (-0.5) = 0.5"),
    ("accumulator", "ramp", 0.5, "y[0] = x[0] + y[-1] = 0 + 0.5 = 0.5"),
    ("leaky_integrator", "impulse", 0.5, "y[0] = 0.9·y[-1] + 0.1·x[0] = 0.9·0.5 + 0.1·1 = 0.55"),
    ("leaky_integrator", "impulse", -2.0, "y[0] = 0.9·y[-1] + 0.1·x[0] = 0.9·(-2) + 0.1·1 = -1.7"),
    ("leaky_integrator", "ramp", 0.5, "y[0] = 0.9·y[-1] + 0.1·x[0] = 0.9·0.5 + 0.1·0 = 0.45"),
])
def test_substitution_at_n0_uses_initial_condition(preset: str, kind: str, c: float, text: str) -> None:
    sim = _make(preset, kind, **{IC_PARAM: c})
    md = sim.step_forward()["metadata"]
    first = md["substitution_history"][0]
    assert md["current_n"] == 0
    assert first["n"] == 0
    assert first["text"] == text
    assert first["ic_terms"] == [{"symbol": "y[-1]", "value": c}]
    md = sim.step_forward()["metadata"]
    assert md["substitution_history"][1]["ic_terms"] == []


# ---------------------------------------------------------------------------
# 5. Block diagram: the feedback delay holds y[-1] at the start of step 0
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("preset", RECURSIVE)
@pytest.mark.parametrize("kind", INPUTS)
def test_delay_register_holds_ic_then_tracks_reference(preset: str, kind: str) -> None:
    c = 0.5
    sim = _make(preset, kind, **{IC_PARAM: c})
    _, q = _ref_register(preset, _ref_input(kind), c)
    md = sim.get_state()["metadata"]
    # Before the first step: start state holds the IC
    assert md["at_start"] is True and md["current_n"] == -1
    assert md["can_step_back"] is False and md["is_at_rest"] is False
    assert md["delay_states"] == [pytest.approx(c)]
    reg = md["initial_conditions"]["register"]
    assert reg["initial_value"] == pytest.approx(c) and reg["scale"] == 1.0
    assert reg["ic_symbol"] == "y[−1]"
    assert md["wire_values"]["delay_out"] == pytest.approx(c)
    assert md["wire_values"]["x_in"] is None and md["wire_values"]["adder_out"] is None
    for n in range(N_MAX + 1):
        md = sim.step_forward()["metadata"]
        assert md["wire_values"]["delay_out"] == pytest.approx(q[n], abs=META_TOL)
        assert md["delay_states"][0] == pytest.approx(q[n + 1], abs=META_TOL)
        assert md["wire_values"]["adder_out"] == pytest.approx(md["y_values"]["values"][-1], abs=META_TOL)


def test_start_wire_values() -> None:
    """Before x[0]: only wires fed by the delay are known; the rest are None."""
    md = _make("leaky_integrator", **{IC_PARAM: 0.5}).get_state()["metadata"]
    assert md["wire_values"] == {"x_in": None, "gain_x_out": None, "delay_out": 0.5,
                                 "gain_fb_out": pytest.approx(0.45), "adder_out": None,
                                 "delay_in": None}
    md = _make("accumulator", **{IC_PARAM: -0.5}).get_state()["metadata"]
    assert md["wire_values"] == {"x_in": None, "delay_out": -0.5, "adder_out": None,
                                 "delay_in": None}


# ---------------------------------------------------------------------------
# 6. Plots: IC marker at n = -1 on the output plot only
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("preset", RECURSIVE)
def test_ic_marker_on_the_output_plot_only(preset: str) -> None:
    c = -1.5
    sim = _make(preset, "step", **{IC_PARAM: c, STRAY_PARAM: 4.0})
    for state in (sim.get_state(), sim.step_forward(), sim.step_forward()):
        markers = _traces_named(_plot(state, "output_signal"), "initial condition")
        assert len(markers) == 1
        assert markers[0]["x"] == [-1] and markers[0]["y"] == [c]
        assert markers[0]["marker"]["symbol"] == "diamond-open"
        assert not _traces_named(_plot(state, "input_signal"), "initial condition")
        y_range = _plot(state, "output_signal")["layout"]["yaxis"]["range"]
        assert y_range[0] < c < y_range[1]
        # No computed (non-IC) stem at n < 0 when an IC is given
        for p in (_plot(state, "input_signal"), _plot(state, "output_signal")):
            for t in p["data"]:
                if t.get("name") == "initial condition" or t.get("line", {}).get("dash") == "dot":
                    continue
                assert all(v is None or v >= 0 for v in t["x"]), (p["id"], t)
    md = sim.get_state()["metadata"]
    assert md["ic_samples"] == {"y": {"n": -1, "value": c, "label": "initial condition"}}


def test_decomposition_plot_toggle() -> None:
    sim = _make("leaky_integrator", "step", **{IC_PARAM: 1.0})
    for _ in range(5):
        state = sim.step_forward()
    assert [p["id"] for p in state["plots"]] == ["input_signal", "output_signal"]
    state = sim.update_parameter("show_decomposition", True)
    assert state["metadata"]["current_n"] == 4          # toggling keeps the position
    assert state["metadata"]["show_decomposition"] is True
    assert [p["id"] for p in state["plots"]] == ["input_signal", "output_signal", "decomposition"]
    dec_plot = _plot(state, "decomposition")
    zir_tr = next(t for t in dec_plot["data"] if t.get("name", "").startswith("y<sub>zi</sub>"))
    zsr_tr = next(t for t in dec_plot["data"] if t.get("name", "").startswith("y<sub>zs</sub>"))
    tot_tr = next(t for t in dec_plot["data"] if t.get("name", "").startswith("y[n] ="))
    assert zir_tr["customdata"] == [0, 1, 2, 3, 4] and zsr_tr["customdata"] == [0, 1, 2, 3, 4]
    assert all(xo < n for xo, n in zip(zir_tr["x"], zir_tr["customdata"]))
    assert all(xo > n for xo, n in zip(zsr_tr["x"], zsr_tr["customdata"]))
    cf = _ref_closed_form("leaky_integrator", "step", 1.0)
    assert np.allclose(zir_tr["y"], cf["zir"][:5], atol=TOL)
    assert np.allclose(zsr_tr["y"], cf["zsr"][:5], atol=TOL)
    assert tot_tr["x"] == [0, 1, 2, 3, 4]
    assert np.allclose(tot_tr["y"], cf["total"][:5], atol=TOL)   # y = 1 (IC at DC steady state)
    assert len(_traces_named(dec_plot, "initial condition")) == 1
    # Switching to a non-recursive preset hides the split; switching back restores it
    state = sim.update_parameter("equation_preset", "moving_average")
    assert [p["id"] for p in state["plots"]] == ["input_signal", "output_signal"]
    assert state["metadata"]["show_decomposition"] is False
    state = sim.update_parameter("equation_preset", "accumulator")
    assert [p["id"] for p in state["plots"]] == ["input_signal", "output_signal", "decomposition"]


# ---------------------------------------------------------------------------
# 7. Navigation: back, IC changes, restart, reset
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("preset", RECURSIVE)
def test_step_back_equals_stepping_forward(preset: str) -> None:
    params = {IC_PARAM: 0.7}
    a = _make(preset, "ramp", **params)
    for _ in range(7):
        a.step_forward()
    for _ in range(3):
        st_back = a.step_backward()
    b = _make(preset, "ramp", **params)
    for _ in range(4):
        st_fwd = b.step_forward()
    assert st_back["metadata"] == st_fwd["metadata"]
    # back all the way: start state holds the IC again
    for _ in range(10):
        st = a.step_backward()
    assert st["metadata"] == _make(preset, "ramp", **params).get_state()["metadata"]


@pytest.mark.parametrize("preset", RECURSIVE)
def test_ic_change_recomputes_up_to_current_n(preset: str) -> None:
    sim = _make(preset, "step")
    for _ in range(8):                      # initial rest: n = -2 .. 5
        sim.step_forward()
    md = sim.update_parameter(IC_PARAM, 0.6)["metadata"]
    assert md["current_n"] == 5
    assert np.allclose(md["y_values"]["values"], _ref_total(preset, "step", 0.6)[:6], atol=META_TOL)
    # back to 0: initial rest again, same position, identical to a fresh run
    md = sim.update_parameter(IC_PARAM, 0.0)["metadata"]
    fresh = _make(preset, "step")
    for _ in range(8):
        fresh_md = fresh.step_forward()["metadata"]
    assert md == fresh_md
    # IC mode at n = 0, IC back to 0: stays at n = 0 (n = -2, -1, 0 computed)
    sim = _make(preset, "step", **{IC_PARAM: 0.6})
    sim.step_forward()
    md = sim.update_parameter(IC_PARAM, 0.0)["metadata"]
    assert md["current_n"] == 0 and md["y_values"]["n"] == [-2, -1, 0]


@pytest.mark.parametrize("preset", RECURSIVE)
def test_ic_change_at_start_stays_at_start(preset: str) -> None:
    """Changing y[-1] before the first step never invents steps."""
    fresh_rest = _make(preset, "step").get_state()["metadata"]
    fresh_ic = _make(preset, "step", **{IC_PARAM: 0.5}).get_state()["metadata"]
    # nonzero -> 0 at the start: back to the initial-rest start (current_n = -3)
    sim = _make(preset, "step", **{IC_PARAM: 0.5})
    md = sim.update_parameter(IC_PARAM, 0.0)["metadata"]
    assert md["current_n"] == -3 and md["at_start"] is True and md["can_step_back"] is False
    assert md["substitution_history"] == [] and md["y_values"]["n"] == []
    assert md == fresh_rest
    # 0 -> nonzero at the start: IC start state (current_n = -1), nothing computed
    md = sim.update_parameter(IC_PARAM, 0.5)["metadata"]
    assert md == fresh_ic
    # nonzero -> other nonzero at the start
    md = sim.update_parameter(IC_PARAM, -0.5)["metadata"]
    assert md["current_n"] == -1 and md["at_start"] is True and md["substitution_history"] == []
    # initial rest after one step (n = -2), then an IC: n < 0 is not determined -> start
    sim = _make(preset, "step")
    sim.step_forward()
    md = sim.update_parameter(IC_PARAM, 0.5)["metadata"]
    assert md == fresh_ic
    md = sim.update_parameter(IC_PARAM, 0.0)["metadata"]
    assert md == fresh_rest


def test_restart_keeps_parameters() -> None:
    params = {"show_decomposition": True, IC_PARAM: 0.5}
    sim = _make("accumulator", "ramp", **params)
    for _ in range(4):
        sim.step_forward()
    state = sim.handle_action("restart", {})
    assert state["metadata"]["at_start"] is True
    assert state["metadata"]["current_n"] == -1
    assert state["parameters"][IC_PARAM] == 0.5
    assert state["parameters"]["input_signal"] == "ramp"
    assert state["parameters"]["show_decomposition"] is True
    with pytest.raises(ValueError):
        sim.handle_action("no_such_action", {})


def test_can_reset_follows_settings_and_position() -> None:
    """Reset restores all defaults: enabled whenever there is something to undo."""
    sim = _make("difference_machine", "impulse")
    md = sim.get_state()["metadata"]
    assert md["is_at_rest"] is True and md["can_reset"] is False
    assert sim.step_forward()["metadata"]["can_reset"] is True
    assert sim.reset()["metadata"]["can_reset"] is False
    # at rest at the start, but the settings differ from the defaults
    sim = _make("accumulator", "step", show_decomposition=True)
    md = sim.get_state()["metadata"]
    assert md["is_at_rest"] is True and md["can_reset"] is True
    md = sim.reset()["metadata"]
    assert md["can_reset"] is False and sim.parameters == DifferenceEquationSimulator.DEFAULT_PARAMS
    assert _make("leaky_integrator", **{IC_PARAM: 0.5}).get_state()["metadata"]["can_reset"] is True
    assert _make("difference_machine", animation_speed=2.0).get_state()["metadata"]["can_reset"] is True


def test_ic_controls_clamped() -> None:
    sim = _make("accumulator", **{IC_PARAM: 99})
    assert sim.parameters[IC_PARAM] == 5.0


# ---------------------------------------------------------------------------
# 8. Catalog: the y[-1] control and the split exist for recursive presets only
# ---------------------------------------------------------------------------

def test_catalog_ic_controls() -> None:
    from simulations.catalog import SIMULATION_CATALOG

    entry = next(e for e in SIMULATION_CATALOG if e["id"] == SIM_ID)
    controls = {c["name"]: c for c in entry["controls"]}
    assert STRAY_PARAM not in controls and STRAY_PARAM not in entry["default_params"]
    for name in (IC_PARAM, "show_decomposition"):
        assert controls[name]["visible_when"] == {"equation_preset": RECURSIVE}
        assert controls[name]["group"] == "Initial Conditions"
    assert controls["show_decomposition"]["type"] == "checkbox"
    assert entry["default_params"] == DifferenceEquationSimulator.DEFAULT_PARAMS
    for name, value in DifferenceEquationSimulator.DEFAULT_PARAMS.items():
        assert controls[name]["default"] == value
    assert entry["default_params"][IC_PARAM] == 0.0


# ---------------------------------------------------------------------------
# 9. HTTP path (the one the web frontend uses)
# ---------------------------------------------------------------------------

def test_http_update_step_restart() -> None:
    from fastapi.testclient import TestClient
    from main import app

    client = TestClient(app)
    headers = {"X-Session-ID": f"test-dteq-ic-{uuid.uuid4().hex[:12]}"}
    base = f"/api/simulations/{SIM_ID}"

    def execute(action: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        resp = client.post(f"{base}/execute", headers=headers,
                           json={"action": action, "params": params or {}})
        assert resp.status_code == 200, resp.text
        return resp.json()["data"]

    def update(params: Dict[str, Any]) -> Dict[str, Any]:
        resp = client.post(f"{base}/update", headers=headers, json={"params": params})
        assert resp.status_code == 200, resp.text
        return resp.json()["data"]

    execute("init", {"equation_preset": "accumulator", "input_signal": "impulse"})
    md = update({IC_PARAM: 0.5})["metadata"]
    assert md["initial_conditions"]["mode"] == "ic" and md["current_n"] == -1
    data = execute("step_forward")
    assert data["metadata"]["substitution_history"][-1]["text"] == "y[0] = x[0] + y[-1] = 1 + 0.5 = 1.5"
    for _ in range(3):
        data = execute("step_forward")
    assert data["metadata"]["y_values"]["values"] == [1.5, 1.5, 1.5, 1.5]
    assert data["metadata"]["decomposition"]["zir"] == [0.5, 0.5, 0.5, 0.5]
    data = execute("restart")
    assert data["metadata"]["current_n"] == -1
    assert data["parameters"][IC_PARAM] == 0.5
    # IC back to 0 at the start: initial-rest start, no invented steps
    md = update({IC_PARAM: 0.0})["metadata"]
    assert md["current_n"] == -3 and md["substitution_history"] == []
    # Non-recursive preset: the y[-1] value is ignored
    md = update({IC_PARAM: 2.0, "equation_preset": "difference_machine"})["metadata"]
    assert md["initial_conditions"]["recursive"] is False and md["initial_conditions"]["mode"] == "initial_rest"
