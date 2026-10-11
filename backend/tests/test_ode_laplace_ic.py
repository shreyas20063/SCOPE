"""Initial conditions in ode_laplace_solver, checked against an independent oracle.

What is checked
---------------
The ODE  a_n y^(n) + ... + a_0 y = b_m x^(m) + ... + b_0 x  with causal input and
initial conditions y(0⁻), y'(0⁻), ... is solved with the UNILATERAL Laplace
transform (lower limit 0⁻; Oppenheim & Willsky §9.9, Lathi §4.3):

    A(s)Y(s) - I(s) = B(s)X(s),   Y = B X / A (zero-state) + I / A (zero-input),
    I(s) = sum_{k=1}^{n} a_k sum_{j=0}^{k-1} s^(k-1-j) y^(j)(0⁻).

Reference implementations (none of them import or reuse simulator code):

* ``ref_solve``           exact-rational Laplace path with 50-digit residues and the
                          exact 1/s (Markov) expansion for the 0⁺ values. Copied from
                          the clean-room oracle (oracle.py, written from the textbooks
                          without reading the simulator).
* ``ref_state_space``     time-domain solution that never forms I(s): observable
                          canonical realisation, xi(0⁻) from the output ICs through
                          the observability matrix, matrix exponential (same oracle).
* ``ref_preset_closed``   hand-derived closed forms for every preset (derivation §5).
* literal worked numbers  values quoted from the derivation, typed in as constants.
* ``head_reference`` and ``GOLDEN_HEAD``  the pre-change (git HEAD a047e086) tool,
                          for the "all ICs = 0 behaves exactly as before" checks.

Run:  cd backend && python -m pytest tests/test_ode_laplace_ic.py -q
"""

import math
import re
from typing import Any, Dict, List, Sequence, Tuple

import mpmath as mp
import numpy as np
import pytest
import sympy as sp
from scipy.linalg import expm
from scipy.signal import residue

from simulations.catalog import SIMULATION_CATALOG
from simulations.ode_laplace_solver import ODELaplaceSolverSimulator as Sim

# =============================================================================
# Independent reference (copied from the clean-room oracle; no simulator code)
# =============================================================================

_s = sp.Symbol("s")

REF_PRESETS: Dict[str, Dict[str, Any]] = {
    "first_order_impulse": {"a": [1, 1], "b": [1], "input": "delta"},
    "second_order_impulse": {"a": [1, 3, 2], "b": [1], "input": "delta"},
    "second_order_step": {"a": [1, 3, 2], "b": [1], "input": "step"},
    "underdamped": {"a": [1, 2, 5], "b": [1], "input": "delta"},
    "repeated_poles": {"a": [1, 2, 1], "b": [1], "input": "delta"},
    "third_order": {"a": [1, 6, 11, 6], "b": [1], "input": "delta"},
    "exponential_input": {"a": [1, 2], "b": [1], "input": "exp", "alpha": 1.0},
}

IC_SETS = [(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1), (2, -1, 0.5), (-3, 4, -2), (3, -5, 0)]

INPUT_COMBOS = [("delta", 1.0, 2.0), ("step", 1.0, 2.0), ("exp", 0.5, 2.0), ("exp", 1.0, 2.0),
                ("exp", 2.0, 2.0), ("exp", 3.0, 2.0), ("cosine", 1.0, 2.0), ("cosine", 1.0, 0.7)]


def _to_rat(x: Any) -> sp.Expr:
    if isinstance(x, sp.Basic):
        return x
    if isinstance(x, int):
        return sp.Integer(x)
    if isinstance(x, float):
        return sp.Rational(repr(x))
    if isinstance(x, str):
        return sp.Rational(x.strip())
    raise TypeError(x)


def ref_parse(c: Any, allow_zero: bool = False) -> List[sp.Expr]:
    if isinstance(c, str):
        vals = [_to_rat(tok) for tok in re.split(r"[,\s;]+", c.strip()) if tok]
    else:
        vals = [_to_rat(v) for v in c]
    while len(vals) > 1 and vals[0] == 0:
        vals.pop(0)
    if vals == [0] and not allow_zero:
        raise ValueError("zero polynomial")
    return vals


def ref_ics_used(a: Any, ics: Sequence[Any]) -> List[sp.Expr]:
    n = len(ref_parse(a)) - 1
    vals = [_to_rat(v) for v in list(ics)[:n]]
    return vals + [sp.Integer(0)] * (n - len(vals))


def ref_ic_polynomial(a: Any, ics: Sequence[Any]) -> List[sp.Expr]:
    """I(s) descending, c_i = sum_{j=0}^{n-1-i} a_{i+j+1} y^(j)(0⁻)."""
    av = ref_parse(a)
    n = len(av) - 1
    y = ref_ics_used(av, ics)
    asc = av[::-1]
    c = [sp.expand(sum(asc[i + j + 1] * y[j] for j in range(n - i))) for i in range(n)]
    return c[::-1]


def ref_input_laplace(kind: str, alpha: Any, omega: Any) -> Tuple[sp.Poly, sp.Poly]:
    al, om = _to_rat(alpha), _to_rat(omega)
    if kind == "delta":
        return sp.Poly(1, _s), sp.Poly(1, _s)
    if kind == "step":
        return sp.Poly(1, _s), sp.Poly(_s, _s)
    if kind == "exp":
        return sp.Poly(1, _s), sp.Poly(_s + al, _s)
    if kind == "cosine":
        return sp.Poly(_s, _s), sp.Poly(_s**2 + om**2, _s)
    raise ValueError(kind)


def _ref_taylor(coeffs_asc, p, order):
    out = []
    for m in range(order + 1):
        acc = mp.mpc(0)
        for i in range(m, len(coeffs_asc)):
            acc += mp.binomial(i, m) * coeffs_asc[i] * p ** (i - m)
        out.append(acc)
    return out


def _ref_series_mul(u, v, order):
    w = [mp.mpc(0)] * (order + 1)
    for i, ui in enumerate(u[: order + 1]):
        for j, vj in enumerate(v[: order + 1 - i]):
            w[i + j] += ui * vj
    return w


def ref_partial_fractions(num: sp.Poly, den: sp.Poly, dps: int = 50):
    """num/den = Q + sum c/(s-p)^k; exact multiplicities from factor_list over Q."""
    q, r = sp.div(num, den, _s)
    if r.is_zero:
        return q, []
    _, factors = sp.factor_list(den)
    roots = []
    with mp.workdps(dps + 10):
        for f, e in factors:
            fp = sp.Poly(f, _s)
            if fp.degree() <= 0:
                continue
            for rt in fp.nroots(n=dps + 10, maxsteps=500):
                roots.append((mp.mpc(mp.mpf(str(sp.re(rt))), mp.mpf(str(sp.im(rt)))), int(e)))
        lc = mp.mpf(str(sp.N(sp.Poly(den, _s).LC(), dps + 10)))
        r_asc = [mp.mpf(str(sp.N(cf, dps + 10))) for cf in reversed(sp.Poly(r, _s).all_coeffs())]
        terms = []
        for idx, (p, mult) in enumerate(roots):
            order = mult - 1
            g = _ref_taylor(r_asc, p, order)
            for jdx, (qr, qm) in enumerate(roots):
                if jdx == idx:
                    continue
                d = p - qr
                ser = [((-1) ** m) * mp.binomial(qm + m - 1, m) * d ** (-qm - m) for m in range(order + 1)]
                g = _ref_series_mul(g, ser, order)
            g = [gi / lc for gi in g]
            for k in range(1, mult + 1):
                c = g[mult - k]
                if abs(c) > mp.mpf("1e-40"):
                    terms.append((complex(p), k, complex(c)))
    return q, terms


def ref_eval_terms(terms, t):
    t = np.asarray(t, dtype=float)
    y = np.zeros_like(t, dtype=complex)
    for p, k, c in terms:
        y += c * t ** (k - 1) / math.factorial(k - 1) * np.exp(p * t)
    return y.real


def ref_markov_0plus(num: sp.Poly, den: sp.Poly, count: int) -> List[sp.Expr]:
    _, r = sp.div(num, den, _s)
    d = sp.Poly(den, _s).all_coeffs()
    N = len(d) - 1
    rc = sp.Poly(r, _s).all_coeffs() if not r.is_zero else [0]
    rc = [sp.Integer(0)] * (N - len(rc)) + list(rc)
    h: List[sp.Expr] = []
    for j in range(count):
        rj = rc[j] if j < N else sp.Integer(0)
        acc = rj - sum((d[i] if i <= N else 0) * h[j - i] for i in range(1, j + 1))
        h.append(acc / d[0])
    return h


def ref_solve(a, b, input_type, ics, alpha, omega, t) -> Dict[str, Any]:
    av = ref_parse(a)
    bv = ref_parse(b, allow_zero=True)
    n = len(av) - 1
    y_ic = ref_ics_used(av, ics)
    A = sp.Poly(av, _s)
    B = sp.Poly(bv, _s)
    Ic = ref_ic_polynomial(av, y_ic)
    I = sp.Poly(Ic, _s) if Ic else sp.Poly(0, _s)
    Xn, Xd = ref_input_laplace(input_type, alpha, omega)
    Nzs, Dzs = B * Xn, A * Xd
    Ntot = B * Xn + I * Xd
    q_zs, pf_zs = ref_partial_fractions(Nzs, Dzs)
    _, pf_zi = ref_partial_fractions(I, A) if not I.is_zero else (None, [])
    cnt = max(n, 1)
    y0p = ref_markov_0plus(Ntot, Dzs, cnt)
    t = np.asarray(t, dtype=float)
    y_zs = ref_eval_terms(pf_zs, t)
    y_zi = ref_eval_terms(pf_zi, t)
    return {
        "order": n,
        "ics_used": [float(v) for v in y_ic],
        "I_coeffs": [float(v) for v in Ic],
        "impulses_zs": [float(v) for v in reversed(q_zs.all_coeffs())] if not q_zs.is_zero else [],
        "y0plus": [float(v) for v in y0p],
        "jumps": [float(y0p[j] - y_ic[j]) for j in range(n)],
        "y_zs": y_zs,
        "y_zi": y_zi,
        "y": y_zs + y_zi,
    }


def _ref_input_generator(kind, alpha, omega):
    if kind == "step":
        return np.array([[0.0]]), np.array([1.0]), np.array([1.0])
    if kind == "exp":
        return np.array([[-alpha]]), np.array([1.0]), np.array([1.0])
    if kind == "cosine":
        return np.array([[0.0, -omega], [omega, 0.0]]), np.array([1.0, 0.0]), np.array([1.0, 0.0])
    raise ValueError(kind)


def ref_state_space(a, b, input_type, ics, alpha, omega, t) -> Tuple[np.ndarray, np.ndarray]:
    """Zero-state / zero-input for t > 0 without I(s) (observable canonical form)."""
    av = np.array([float(v) for v in ref_parse(a)])
    bv = np.array([float(v) for v in ref_parse(b, allow_zero=True)])
    n = len(av) - 1
    t = np.asarray(t, dtype=float)
    y_ic = np.array([float(v) for v in ref_ics_used(list(av), ics)])
    a_m, b_m = av / av[0], bv / av[0]
    if len(b_m) > n:
        qdesc, rdesc = np.polydiv(b_m, a_m)
    else:
        qdesc, rdesc = np.array([0.0]), b_m
    q_asc = qdesc[::-1]
    rpad = np.zeros(n)
    if n > 0:
        rr = np.atleast_1d(rdesc)[-n:]
        rpad[n - len(rr):] = rr
    y_zs = np.zeros_like(t)
    y_zi = np.zeros_like(t)
    if n > 0:
        Ao = np.zeros((n, n))
        Ao[:, 0] = -a_m[1:]
        Ao[:-1, 1:] += np.eye(n - 1)
        C = np.zeros(n)
        C[0] = 1.0
        O = np.array([C @ np.linalg.matrix_power(Ao, j) for j in range(n)])
        xi0 = np.linalg.solve(O, y_ic)
        for idx, tk in enumerate(t):
            y_zi[idx] = C @ expm(Ao * tk) @ xi0
        if input_type == "delta":
            for idx, tk in enumerate(t):
                y_zs[idx] = C @ expm(Ao * tk) @ rpad
        else:
            F, w0, cw = _ref_input_generator(input_type, alpha, omega)
            nw = F.shape[0]
            Aa = np.zeros((n + nw, n + nw))
            Aa[:n, :n] = Ao
            Aa[:n, n:] = np.outer(rpad, cw)
            Aa[n:, n:] = F
            z0 = np.concatenate([np.zeros(n), w0])
            Ca = np.concatenate([C, np.zeros(nw)])
            for idx, tk in enumerate(t):
                y_zs[idx] = Ca @ expm(Aa * tk) @ z0
    if input_type != "delta" and np.any(q_asc != 0):
        F, w0, cw = _ref_input_generator(input_type, alpha, omega)
        for idx, tk in enumerate(t):
            E = expm(F * tk) @ w0
            y_zs[idx] += sum(qk * (cw @ np.linalg.matrix_power(F, k) @ E) for k, qk in enumerate(q_asc))
    return y_zs, y_zi


def ref_preset_closed(name: str, ics: Sequence[float], t: np.ndarray, alpha: float = 1.0):
    """Hand-derived closed forms (derivation §5), nominal input of each preset."""
    y0, y1, y2 = (list(ics) + [0.0, 0.0, 0.0])[:3]
    e = np.exp
    if name == "first_order_impulse":
        return e(-t), y0 * e(-t)
    if name == "second_order_impulse":
        return e(-t) - e(-2 * t), (2 * y0 + y1) * e(-t) - (y0 + y1) * e(-2 * t)
    if name == "second_order_step":
        return 0.5 - e(-t) + 0.5 * e(-2 * t), (2 * y0 + y1) * e(-t) - (y0 + y1) * e(-2 * t)
    if name == "underdamped":
        return 0.5 * e(-t) * np.sin(2 * t), e(-t) * (y0 * np.cos(2 * t) + 0.5 * (y0 + y1) * np.sin(2 * t))
    if name == "repeated_poles":
        return t * e(-t), y0 * e(-t) + (y0 + y1) * t * e(-t)
    if name == "third_order":
        zs = 0.5 * e(-t) - e(-2 * t) + 0.5 * e(-3 * t)
        zi = (0.5 * (6 * y0 + 5 * y1 + y2) * e(-t) - (3 * y0 + 4 * y1 + y2) * e(-2 * t)
              + 0.5 * (2 * y0 + 3 * y1 + y2) * e(-3 * t))
        return zs, zi
    if name == "exponential_input":
        zs = t * e(-2 * t) if abs(alpha - 2.0) < 1e-15 else (e(-alpha * t) - e(-2 * t)) / (2.0 - alpha)
        return zs, y0 * e(-2 * t)
    raise KeyError(name)


# =============================================================================
# Helpers
# =============================================================================

def relerr(u: np.ndarray, v: np.ndarray) -> float:
    return float(np.max(np.abs(np.asarray(u) - np.asarray(v))) / max(1.0, float(np.max(np.abs(v)))))


def make_sim(params: Dict[str, Any], kind: str = None, alpha: float = None, omega: float = None,
             ics: Sequence[float] = (0, 0, 0), t_max: float = 8.0, show_all: bool = True) -> Sim:
    """Drive the simulator the way the frontend does (initialize, then /update calls)."""
    sim = Sim("test")
    sim.initialize({**params, "t_max": t_max})
    if kind is not None:
        sim.update_parameter("input_signal", kind)
    if alpha is not None:
        sim.update_parameter("alpha", alpha)
    if omega is not None:
        sim.update_parameter("omega", omega)
    for name, v in zip(("ic_y0", "ic_y1", "ic_y2"), (list(ics) + [0, 0, 0])[:3]):
        sim.update_parameter(name, v)
    if show_all:
        sim.handle_action("show_all", {})
    return sim


def plot(state: Dict[str, Any], pid: str) -> Dict[str, Any]:
    found = [p for p in state["plots"] if p["id"] == pid]
    assert len(found) == 1, f"plot {pid} missing"
    return found[0]


def assert_matches_oracle(sim: Sim, a, b, kind, alpha, omega, ics, tol: float = 1e-8) -> Dict[str, Any]:
    t = sim._t
    L = ref_solve(a, b, kind, ics, alpha, omega, t)
    assert sim._order == L["order"]
    assert len(sim._ics_used) == L["order"]
    assert np.allclose(sim._ics_used, L["ics_used"], atol=1e-14)
    assert len(sim._I_poly) == len(L["I_coeffs"])
    assert np.allclose(sim._I_poly, L["I_coeffs"], atol=1e-12, rtol=1e-12)
    assert relerr(sim._y_zs_raw, L["y_zs"]) < tol, relerr(sim._y_zs_raw, L["y_zs"])
    assert relerr(sim._y_zi_raw, L["y_zi"]) < tol, relerr(sim._y_zi_raw, L["y_zi"])
    assert relerr(sim._y_raw, L["y"]) < tol, relerr(sim._y_raw, L["y"])
    assert len(sim._y0plus) == len(L["y0plus"])
    assert np.allclose(sim._y0plus, L["y0plus"], atol=1e-10, rtol=1e-10)
    jumps = [v["jump"] for v in sim._initial_values()]
    assert np.allclose(jumps, L["jumps"], atol=1e-10, rtol=1e-10)
    assert len(sim._direct_terms) == len(L["impulses_zs"])
    assert np.allclose(sim._direct_terms, L["impulses_zs"], atol=1e-12)
    return L


# =============================================================================
# 1. Every preset × every input × several IC vectors vs the oracle
# =============================================================================

PRESET_INPUT_CASES = [
    (name, kind, al, om)
    for name, P in REF_PRESETS.items()
    for (kind, al, om) in [(P["input"], P.get("alpha", 1.0), 2.0)] + INPUT_COMBOS
]


@pytest.mark.parametrize("name,kind,alpha,omega", PRESET_INPUT_CASES)
def test_presets_all_inputs_all_ics_match_oracle(name, kind, alpha, omega):
    P = REF_PRESETS[name]
    for ics in IC_SETS:
        sim = make_sim({"preset": name}, kind, alpha, omega, ics)
        assert_matches_oracle(sim, P["a"], P["b"], kind, alpha, omega, ics)
        # zero-state + zero-input = total, where the total comes from the
        # partial fractions of the UNREDUCED total Y(s) (independent path)
        assert relerr(sim._y_zs_raw + sim._y_zi_raw, sim._y_total_pf_raw) < 1e-9


@pytest.mark.parametrize("name", list(REF_PRESETS))
def test_presets_match_hand_closed_forms(name):
    P = REF_PRESETS[name]
    for ics in IC_SETS:
        sim = make_sim({"preset": name}, ics=ics)
        zs, zi = ref_preset_closed(name, ics, sim._t, P.get("alpha", 1.0))
        assert relerr(sim._y_zs_raw, zs) < 1e-10
        assert relerr(sim._y_zi_raw, zi) < 1e-10
        assert relerr(sim._y_raw, zs + zi) < 1e-10


def test_exponential_preset_coincident_alpha_two():
    for ics in IC_SETS:
        sim = make_sim({"preset": "exponential_input"}, "exp", 2.0, None, ics)
        zs, zi = ref_preset_closed("exponential_input", ics, sim._t, 2.0)
        assert relerr(sim._y_raw, zs + zi) < 1e-10


@pytest.mark.parametrize("name", list(REF_PRESETS))
def test_presets_match_state_space_without_I_of_s(name):
    """Independent time-domain check that never forms I(s)."""
    P = REF_PRESETS[name]
    idx = np.arange(0, Sim.NUM_POINTS, 25)
    for kind, al, om in [(P["input"], P.get("alpha", 1.0), 2.0), ("step", 1.0, 2.0), ("cosine", 1.0, 0.7)]:
        for ics in [(1, 0, 0), (2, -1, 0.5), (-3, 4, -2)]:
            sim = make_sim({"preset": name}, kind, al, om, ics)
            zs, zi = ref_state_space(P["a"], P["b"], kind, ics, al, om, sim._t[idx])
            assert relerr(sim._y_zs_raw[idx], zs) < 1e-8
            assert relerr(sim._y_zi_raw[idx], zi) < 1e-8


# =============================================================================
# 2. Edge cases (custom coefficients)
# =============================================================================

EDGE_CASES = [
    # (label, a, b, input, alpha, omega, ics)
    ("Lathi 4.3 example", "1, 5, 6", "1, 1", "exp", 4.0, 2.0, (2, 1)),
    ("O&W 9.38 structure", "1, 3, 2", "2", "step", 1.0, 2.0, (3, -5)),
    ("B and A share s+1", "1, 3, 2", "1, 1", "delta", 1.0, 2.0, (1, 0)),
    ("improper: y = delta(t)", "1, 1", "1, 0", "delta", 1.0, 2.0, (1,)),
    ("improper with s term", "1, 2", "1, 0, 0", "delta", 1.0, 2.0, (0.5,)),
    ("non-monic", "2, 1", "1", "delta", 1.0, 2.0, (3,)),
    ("non-monic scaled", "2, 6, 4", "2", "delta", 1.0, 2.0, (1, 0)),
    ("resonance", "1, 0, 4", "1", "cosine", 1.0, 2.0, (1, 0)),
    ("(s+1)^4, y'''(0-) = 0", "1, 4, 6, 4, 1", "1", "delta", 1.0, 2.0, (1, 1, 1)),
    ("5-fold pole (s+1)^4 with e^-t", "1, 4, 6, 4, 1", "1", "exp", 1.0, 2.0, (1, 1, 1)),
    ("triple pole", "1, 2, 1", "1", "exp", 1.0, 2.0, (1, 1)),
    ("order 0", "2", "1, 3", "step", 1.0, 2.0, (5, 5)),
    ("order 0 with impulse", "2", "1", "delta", 1.0, 2.0, (1,)),
    ("leading zero", "0, 1, 2", "1", "delta", 1.0, 2.0, (1, 7, 7)),
    ("unstable", "1, -1", "1", "step", 1.0, 2.0, (1,)),
    ("x' of a step", "1, 3, 2", "1, 0", "step", 1.0, 2.0, (0, 0)),
    ("single mode (1,-1)", "1, 3, 2", "1", "delta", 1.0, 2.0, (1, -1)),
    ("single mode (1,-2)", "1, 3, 2", "1", "delta", 1.0, 2.0, (1, -2)),
    ("marginal + cosine", "1, 0, 1, 0", "1", "cosine", 1.0, 1.0, (1, -1, 2)),
    ("decimals", "0.5, 1.5, 1", "2, 0.1", "exp", 0.3, 2.0, (0.1, 0.2)),
    ("4th order, B degree 2", "3, 1, 4, 1, 5", "9, 2, 6", "cosine", 1.0, 0.7, (0.5, -1.5, 2.5)),
]


@pytest.mark.parametrize("label,a,b,kind,alpha,omega,ics", EDGE_CASES, ids=[c[0] for c in EDGE_CASES])
def test_edge_cases_match_oracle(label, a, b, kind, alpha, omega, ics):
    sim = make_sim({"preset": "custom", "output_coeffs": a, "input_coeffs": b}, kind, alpha, omega, ics)
    assert_matches_oracle(sim, a, b, kind, alpha, omega, ics)
    assert relerr(sim._y_zs_raw + sim._y_zi_raw, sim._y_total_pf_raw) < 1e-9
    idx = np.arange(0, Sim.NUM_POINTS, 50)
    zs, zi = ref_state_space(a, b, kind, ics, alpha, omega, sim._t[idx])
    assert relerr(sim._y_zs_raw[idx], zs) < 1e-7
    assert relerr(sim._y_zi_raw[idx], zi) < 1e-7


# =============================================================================
# 3. Worked numbers typed in from the derivation (t grid with step 0.01)
# =============================================================================

def _at(sim: Sim, arr: np.ndarray, t: float) -> float:
    k = int(round(t / (sim._t[1] - sim._t[0])))
    assert abs(sim._t[k] - t) < 1e-12
    return float(arr[k])


def test_worked_numbers_presets():
    T = 4.99  # linspace(0, 4.99, 500) has step 0.01
    s = make_sim({"preset": "first_order_impulse"}, ics=(2,), t_max=T)
    assert s._I_poly == [2.0]
    assert abs(_at(s, s._y_zs_raw, 0.5) - 0.6065306597) < 1e-9
    assert abs(_at(s, s._y_zi_raw, 0.5) - 1.2130613194) < 1e-9
    assert abs(_at(s, s._y_raw, 0.5) - 1.8195919791) < 1e-9
    assert abs(_at(s, s._y_raw, 2.0) - 0.4060058497) < 1e-9
    assert s._y0plus == [3.0]

    s = make_sim({"preset": "second_order_impulse"}, ics=(2, -1), t_max=T)
    assert s._I_poly == [2.0, 5.0]
    assert abs(_at(s, s._y_zs_raw, 0.5) - 0.2386512185) < 1e-9
    assert abs(_at(s, s._y_zi_raw, 0.5) - 1.4517125380) < 1e-9
    assert abs(_at(s, s._y_raw, 1.0) - 1.2008471982) < 1e-9
    assert s._y0plus == [2.0, 0.0]
    assert [v["jump"] for v in s._initial_values()] == [0.0, 1.0]

    s = make_sim({"preset": "second_order_impulse"}, ics=(1, -1), t_max=T)
    assert abs(_at(s, s._y_raw, 1.0) - 0.6004235991) < 1e-9

    s = make_sim({"preset": "second_order_step"}, ics=(3, -5), t_max=T)
    assert s._I_poly == [3.0, 4.0]
    assert abs(_at(s, s._y_zs_raw, 0.5) - 0.0774090609) < 1e-9
    assert abs(_at(s, s._y_zi_raw, 0.5) - 1.3422895421) < 1e-9
    assert abs(_at(s, s._y_raw, 2.0) - 0.5457890972) < 1e-9

    s = make_sim({"preset": "underdamped"}, ics=(1, 0), t_max=T)
    assert s._I_poly == [1.0, 2.0]
    assert abs(_at(s, s._y_raw, 0.5) - 0.8380878656) < 1e-9
    assert abs(_at(s, s._y_raw, 2.0) - (-0.1908831246)) < 1e-9
    assert s._y0plus == [1.0, 1.0]

    s = make_sim({"preset": "repeated_poles"}, ics=(1, 1), t_max=T)
    assert s._I_poly == [1.0, 3.0]
    assert abs(_at(s, s._y_raw, 1.0) - 1.4715177647) < 1e-9

    s = make_sim({"preset": "third_order"}, ics=(1, 0, -1), t_max=T)
    assert s._I_poly == [1.0, 6.0, 10.0]
    assert abs(_at(s, s._y_zs_raw, 1.0) - 0.0734979715) < 1e-9
    assert abs(_at(s, s._y_zi_raw, 1.0) - 0.6739215706) < 1e-9
    assert abs(_at(s, s._y_raw, 1.0) - 0.7474195422) < 1e-9
    assert s._y0plus == [1.0, 0.0, 0.0]
    assert [v["jump"] for v in s._initial_values()] == [0.0, 0.0, 1.0]

    s = make_sim({"preset": "exponential_input"}, ics=(3,), t_max=T)
    assert abs(_at(s, s._y_raw, 1.0) - 0.6385500076) < 1e-9
    s = make_sim({"preset": "exponential_input"}, "exp", 2.0, None, ics=(1,), t_max=T)
    assert abs(_at(s, s._y_raw, 1.0) - 0.2706705665) < 1e-9


def test_worked_numbers_custom():
    T = 4.99
    s = make_sim({"preset": "custom", "output_coeffs": "1, 5, 6", "input_coeffs": "1, 1"}, "exp", 4.0, None,
                 ics=(2, 1), t_max=T)
    assert s._I_poly == [2.0, 11.0]
    assert abs(_at(s, s._y_raw, 1.0) - 0.7028446776) < 1e-9
    assert s._y0plus == [2.0, 2.0]

    s = make_sim({"preset": "custom", "output_coeffs": "1, 3, 2", "input_coeffs": "2"}, "step", ics=(3, -5), t_max=T)
    assert abs(_at(s, s._y_raw, 1.0) - 1.0381264085) < 1e-9

    s = make_sim({"preset": "custom", "output_coeffs": "2, 1", "input_coeffs": "1"}, "delta", ics=(3,), t_max=T)
    assert s._I_poly == [6.0]  # a_1·y(0⁻), NOT y(0⁻)
    assert s._y0plus == [3.5]

    s = make_sim({"preset": "custom", "output_coeffs": "1, 1", "input_coeffs": "1, 0"}, "delta", ics=(1,), t_max=T)
    assert s._direct_terms == [1.0]  # y(t) = δ(t)
    assert np.max(np.abs(s._y_raw)) < 1e-12
    assert s._y0plus == [0.0]

    s = make_sim({"preset": "third_order"}, "cosine", None, 2.0, ics=(1, 0, -1), t_max=T)
    assert abs(_at(s, s._y_raw, 1.0) - 0.7041089530) < 1e-9


# =============================================================================
# 4. Backwards compatibility: all ICs = 0 behaves exactly as before
# =============================================================================

def head_reference(a, b, kind, alpha, omega, t):
    """The pre-change pipeline (git HEAD a047e086): Y = B·X/(A·X_den) normalised,
    scipy.signal.residue, poles grouped with tolerance 1e-8, summed r t^k/k! e^{pt},
    clipped to ±200."""
    A = np.array(a, float)
    B = np.array(b, float)
    Xn, Xd = {"delta": ([1.0], [1.0]), "step": ([1.0], [1.0, 0.0]), "exp": ([1.0], [1.0, alpha]),
              "cosine": ([1.0, 0.0], [1.0, 0.0, omega ** 2])}[kind]
    num = np.polymul(B, Xn)
    den = np.polymul(A, Xd)
    num, den = num / den[0], den / den[0]
    r, p, _ = residue(num, den)
    y = np.zeros(len(t), dtype=complex)
    used = set()
    for i in range(len(p)):
        if i in used:
            continue
        ids = [j for j in range(len(p)) if j not in used and abs(p[j] - p[i]) < 1e-8]
        used.update(ids)
        for k, j in enumerate(ids):
            y += r[j] * (t ** k / math.factorial(k)) * np.exp(p[i] * t)
    return np.clip(np.real(y), -200.0, 200.0), p, r, num, den


HEAD_CUSTOM = [("1, 5, 6", "1, 1", "exp", 4.0, 2.0), ("2, 1", "1", "delta", 1.0, 2.0),
               ("1, 0, 4", "1", "cosine", 1.0, 2.0), ("1, -1", "1", "step", 1.0, 2.0),
               ("1, 3, 2", "2", "step", 1.0, 2.0), ("1, 2, 5", "3, 1", "cosine", 1.0, 0.7),
               ("0.5, 1.5, 1", "2", "step", 1.0, 2.0), ("1, 2, 2", "1", "exp", 1.5, 2.0)]


def test_zero_ics_reproduce_pre_change_numbers():
    cases = [({"preset": n}, P["a"], P["b"], k, al, om)
             for n, P in REF_PRESETS.items() for (k, al, om) in INPUT_COMBOS]
    cases += [({"preset": "custom", "output_coeffs": a, "input_coeffs": b}, ref_parse(a), ref_parse(b), k, al, om)
              for (a, b, k, al, om) in HEAD_CUSTOM]
    for params, a, b, kind, al, om in cases:
        sim = make_sim(params, kind, al, om, (0, 0, 0))
        a_f = [float(v) for v in a]
        b_f = [float(v) for v in b]
        y_old, p_old, r_old, num_old, den_old = head_reference(a_f, b_f, kind, al, om, sim._t)
        st = sim.get_state()
        y_plot = np.array(plot(st, "time_response")["data"][0]["y"])
        assert np.max(np.abs(y_plot - y_old)) < 1e-10 * max(1.0, np.max(np.abs(y_old))), params
        assert np.allclose(sim._Y_num, num_old, atol=1e-12) and len(sim._Y_num) == len(num_old)
        assert np.allclose(sim._Y_den, den_old, atol=1e-12) and len(sim._Y_den) == len(den_old)
        assert len(sim._poles) == len(p_old)
        assert np.max(np.abs(np.array(sim._poles) - p_old)) < 1e-9  # same values, same order
        assert np.max(np.abs(np.array(sim._residues) - r_old)) < 1e-9
        assert np.array_equal(sim._y_zi_raw, np.zeros_like(sim._t))


# Outputs of the pre-change tool (git HEAD a047e086), ICs = 0, show_all.
# y = time_response trace at indices IDX (must be unchanged).
# eq_head = equations of steps 0, 2, 3, 4, 5 verbatim from HEAD (kept for the record);
# eq = the same equations now. They differ only in typography (review fix): signed
# terms joined with ' − ' instead of '+ -1·…', typographic minus, unit coefficients
# dropped (1·e⁻ᵗ → e⁻ᵗ), t/1! → t, complex residues parenthesised, (s) → s,
# (s − (2j)) → (s − 2j), single-term numerators without parentheses, and
# e^(-1t)·(0.5sin(2t)) → 0.5·e⁻ᵗ·sin(2t). Every number is the same.
IDX = [0, 1, 10, 50, 100, 150, 200, 300, 400, 499]
GOLDEN_HEAD = {
    'first_order_impulse': {'params': {'preset': 'first_order_impulse'},
        'y': [1.0, 0.984095765377, 0.851870600289, 0.448609174181, 0.201250191159, 0.0902826820595, 0.0405016394415, 0.00815096267986, 0.00164038279745, 0.000335462627903],
        'eq_head': ['ẏ(t) + y(t) = x(t)', 'Y(s) = (1) / (s + 1)', 'Y(s) = 1 / (s + 1)', 'y(t) = 1·e⁻ᵗ·u(t)', 'y(t) = (1·e⁻ᵗ)·u(t)'],
        'eq': ['ẏ(t) + y(t) = x(t)', 'Y(s) = 1 / (s + 1)', 'Y(s) = 1 / (s + 1)', 'y(t) = e⁻ᵗ·u(t)', 'y(t) = e⁻ᵗ·u(t)']},
    'second_order_impulse': {'params': {'preset': 'second_order_impulse'},
        'y': [0.0, 0.0156512899445, 0.126187080652, 0.247358983022, 0.160748551717, 0.0821317193797, 0.0388612566441, 0.00808452448725, 0.00163769194173, 0.000335350092728],
        'eq_head': ['ÿ(t) + 3ẏ(t) + 2y(t) = x(t)', 'Y(s) = (1) / (s² + 3s + 2)', 'Y(s) = 1 / (s + 1) + -1 / (s + 2)', 'y(t) = 1·e⁻ᵗ·u(t) + -1·e^(−2t)·u(t)', 'y(t) = (1·e⁻ᵗ -1·e^(−2t))·u(t)'],
        'eq': ['ÿ(t) + 3ẏ(t) + 2y(t) = x(t)', 'Y(s) = 1 / (s² + 3s + 2)', 'Y(s) = 1 / (s + 1) − 1 / (s + 2)', 'y(t) = e⁻ᵗ·u(t) − e^(−2t)·u(t)', 'y(t) = (e⁻ᵗ − e^(−2t))·u(t)']},
    'second_order_step': {'params': {'preset': 'second_order_step'},
        'y': [0.0, 0.000126472339479, 0.0109711595294, 0.152015921399, 0.319000628562, 0.41379279928, 0.460318551957, 0.491882256416, 0.49836096263, 0.49966459364],
        'eq_head': ['ÿ(t) + 3ẏ(t) + 2y(t) = x(t)', 'Y(s) = (1) / (s³ + 3s² + 2s)', 'Y(s) = 0.5 / (s) + -1 / (s + 1) + 0.5 / (s + 2)', 'y(t) = 0.5·u(t) + -1·e⁻ᵗ·u(t) + 0.5·e^(−2t)·u(t)', 'y(t) = (0.5 -1·e⁻ᵗ + 0.5·e^(−2t))·u(t)'],
        'eq': ['ÿ(t) + 3ẏ(t) + 2y(t) = x(t)', 'Y(s) = 1 / (s³ + 3s² + 2s)', 'Y(s) = 0.5 / s − 1 / (s + 1) + 0.5 / (s + 2)', 'y(t) = 0.5·u(t) − e⁻ᵗ·u(t) + 0.5·e^(−2t)·u(t)', 'y(t) = (0.5 − e⁻ᵗ + 0.5·e^(−2t))·u(t)']},
    'underdamped': {'params': {'preset': 'underdamped'},
        'y': [0.0, 0.0157743831322, 0.13424425364, 0.224186791099, -0.00651796939462, -0.0449281322083, 0.00261797561337, -0.000787534796166, 0.000210285058644, -4.82904015952e-05],
        # step 4: the old text 'e^(-1+2jt)' read as e^(−1 + 2j·t); now 'e^((−1+2j)t)' (bug fix)
        'eq_head': ['ÿ(t) + 2ẏ(t) + 5y(t) = x(t)', 'Y(s) = (1) / (s² + 2s + 5)', 'Y(s) = −0.25j / (s − (-1+2j)) + 0.25j / (s − (-1−2j))', 'y(t) = −0.25j·e^((-1+2j)t)·u(t) + 0.25j·e^((-1−2j)t)·u(t)', 'y(t) = (e^(-1t)·(0.5sin(2t)))·u(t)'],
        'eq': ['ÿ(t) + 2ẏ(t) + 5y(t) = x(t)', 'Y(s) = 1 / (s² + 2s + 5)', 'Y(s) = −0.25j / (s − (−1+2j)) + 0.25j / (s − (−1−2j))', 'y(t) = −0.25j·e^((−1+2j)t)·u(t) + 0.25j·e^((−1−2j)t)·u(t)', 'y(t) = 0.5·e⁻ᵗ·sin(2t)·u(t)']},
    'repeated_poles': {'params': {'preset': 'repeated_poles'},
        'y': [0.0, 0.0157770864189, 0.136572440928, 0.359606552449, 0.322645597048, 0.217112662267, 0.129864976165, 0.0392030269172, 0.0105194888815, 0.00268370102322],
        'eq_head': ['ÿ(t) + 2ẏ(t) + y(t) = x(t)', 'Y(s) = (1) / (s² + 2s + 1)', 'Y(s) = 1 / (s + 1)²', 'y(t) = 1·t·e⁻ᵗ·u(t)', 'y(t) = (1·t/1!·e⁻ᵗ)·u(t)'],
        'eq': ['ÿ(t) + 2ẏ(t) + y(t) = x(t)', 'Y(s) = 1 / (s² + 2s + 1)', 'Y(s) = 1 / (s + 1)²', 'y(t) = t·e⁻ᵗ·u(t)', 'y(t) = t·e⁻ᵗ·u(t)']},
    'third_order': {'params': {'preset': 'third_order'},
        'y': [2.22044604925e-16, 0.000124460893718, 0.00934600825416, 0.0681957369611, 0.0641989374779, 0.0373583237359, 0.0186436560196, 0.00400931391494, 0.00081750275002, 0.000167618797652],
        'eq_head': ['y‴(t) + 6ÿ(t) + 11ẏ(t) + 6y(t) = x(t)', 'Y(s) = (1) / (s³ + 6s² + 11s + 6)', 'Y(s) = 0.5 / (s + 1) + -1 / (s + 2) + 0.5 / (s + 3)', 'y(t) = 0.5·e⁻ᵗ·u(t) + -1·e^(−2t)·u(t) + 0.5·e^(−3t)·u(t)', 'y(t) = (0.5·e⁻ᵗ -1·e^(−2t) + 0.5·e^(−3t))·u(t)'],
        'eq': ['y‴(t) + 6ÿ(t) + 11ẏ(t) + 6y(t) = x(t)', 'Y(s) = 1 / (s³ + 6s² + 11s + 6)', 'Y(s) = 0.5 / (s + 1) − 1 / (s + 2) + 0.5 / (s + 3)', 'y(t) = 0.5·e⁻ᵗ·u(t) − e^(−2t)·u(t) + 0.5·e^(−3t)·u(t)', 'y(t) = (0.5·e⁻ᵗ − e^(−2t) + 0.5·e^(−3t))·u(t)']},
    'exponential_input': {'params': {'preset': 'exponential_input'},
        'y': [0.0, 0.0156512899445, 0.126187080652, 0.247358983022, 0.160748551717, 0.0821317193797, 0.0388612566441, 0.00808452448725, 0.00163769194173, 0.000335350092728],
        'eq_head': ['ẏ(t) + 2y(t) = x(t)', 'Y(s) = (1) / (s² + 3s + 2)', 'Y(s) = 1 / (s + 1) + -1 / (s + 2)', 'y(t) = 1·e⁻ᵗ·u(t) + -1·e^(−2t)·u(t)', 'y(t) = (1·e⁻ᵗ -1·e^(−2t))·u(t)'],
        'eq': ['ẏ(t) + 2y(t) = x(t)', 'Y(s) = 1 / (s² + 3s + 2)', 'Y(s) = 1 / (s + 1) − 1 / (s + 2)', 'y(t) = e⁻ᵗ·u(t) − e^(−2t)·u(t)', 'y(t) = (e⁻ᵗ − e^(−2t))·u(t)']},
    'exponential_input|exp|2.0': {'params': {'preset': 'exponential_input', 'input_signal': 'exp', 'alpha': 2.0},
        'y': [0.0, 0.0155261639348, 0.116342047236, 0.161322798524, 0.0649324880826, 0.0196015134586, 0.00525974444073, 0.000319542409339, 1.72559885991e-05, 9.00281397754e-07],
        'eq_head': ['ẏ(t) + 2y(t) = x(t)', 'Y(s) = (1) / (s² + 4s + 4)', 'Y(s) = 1 / (s + 2)²', 'y(t) = 1·t·e^(−2t)·u(t)', 'y(t) = (1·t/1!·e^(−2t))·u(t)'],
        'eq': ['ẏ(t) + 2y(t) = x(t)', 'Y(s) = 1 / (s² + 4s + 4)', 'Y(s) = 1 / (s + 2)²', 'y(t) = t·e^(−2t)·u(t)', 'y(t) = t·e^(−2t)·u(t)']},
    'third_order|cosine|2.0': {'params': {'preset': 'third_order', 'input_signal': 'cosine', 'omega': 2.0},
        'y': [-1.52655665886e-16, 6.70447177289e-07, 0.000538710001717, 0.023065026999, 0.0218586475349, -0.0372317157811, -0.0344920937559, 0.0279618654648, -0.0267190368218, 0.0253649899676],
        'eq_head': ['y‴(t) + 6ÿ(t) + 11ẏ(t) + 6y(t) = x(t)', 'Y(s) = (s) / (s⁵ + 6s⁴ + 15s³ + 30s² + 44s + 24)', 'Y(s) = -0.1 / (s + 1) + 0.25 / (s + 2) + -0.01731−0.01346j / (s − (2j)) + -0.01731+0.01346j / (s − (−2j)) + -0.1154 / (s + 3)', 'y(t) = -0.1·e⁻ᵗ·u(t) + 0.25·e^(−2t)·u(t) + -0.01731−0.01346j·e^(2jt)·u(t) + -0.01731+0.01346j·e^(−2jt)·u(t) + -0.1154·e^(−3t)·u(t)', 'y(t) = (-0.1·e⁻ᵗ + 0.25·e^(−2t) -0.03462cos(2t) + 0.02692sin(2t) -0.1154·e^(−3t))·u(t)'],
        'eq': ['y‴(t) + 6ÿ(t) + 11ẏ(t) + 6y(t) = x(t)', 'Y(s) = s / (s⁵ + 6s⁴ + 15s³ + 30s² + 44s + 24)', 'Y(s) = −0.1 / (s + 1) + 0.25 / (s + 2) + (−0.01731−0.01346j) / (s − 2j) + (−0.01731+0.01346j) / (s + 2j) − 0.1154 / (s + 3)', 'y(t) = −0.1·e⁻ᵗ·u(t) + 0.25·e^(−2t)·u(t) + (−0.01731−0.01346j)·e^(2jt)·u(t) + (−0.01731+0.01346j)·e^(−2jt)·u(t) − 0.1154·e^(−3t)·u(t)', 'y(t) = (−0.1·e⁻ᵗ + 0.25·e^(−2t) − 0.03462·cos(2t) + 0.02692·sin(2t) − 0.1154·e^(−3t))·u(t)']},
    'repeated_poles|exp|1.0': {'params': {'preset': 'repeated_poles', 'input_signal': 'exp', 'alpha': 1.0},
        'y': [0.0, 0.000126469630612, 0.0109476906556, 0.144130882745, 0.258633745129, 0.26105730934, 0.20820036259, 0.0942758162336, 0.0337298240688, 0.0107348040929],
        'eq_head': ['ÿ(t) + 2ẏ(t) + y(t) = x(t)', 'Y(s) = (1) / (s³ + 3s² + 3s + 1)', 'Y(s) = 1 / (s + 1)³', 'y(t) = 1·t²/2!·e⁻ᵗ·u(t)', 'y(t) = (1·t^2/2!·e⁻ᵗ)·u(t)'],
        'eq': ['ÿ(t) + 2ẏ(t) + y(t) = x(t)', 'Y(s) = 1 / (s³ + 3s² + 3s + 1)', 'Y(s) = 1 / (s + 1)³', 'y(t) = t²/2!·e⁻ᵗ·u(t)', 'y(t) = t²/2!·e⁻ᵗ·u(t)']},
    'custom Lathi': {'params': {'preset': 'custom', 'output_coeffs': '1, 5, 6', 'input_coeffs': '1, 1', 'input_signal': 'exp', 'alpha': 4.0},
        'y': [1.55431223448e-15, 0.0150349238417, 0.0836102951587, 0.0191878093772, -0.00640946855722, -0.00270335708463, -0.000691351297092, -3.21426468974e-05, -1.33661065527e-06, -5.6192103665e-08],
        'eq_head': ['ÿ(t) + 5ẏ(t) + 6y(t) = ẋ(t) + x(t)', 'Y(s) = (s + 1) / (s³ + 9s² + 26s + 24)', 'Y(s) = -0.5 / (s + 2) + 2 / (s + 3) + -1.5 / (s + 4)', 'y(t) = -0.5·e^(−2t)·u(t) + 2·e^(−3t)·u(t) + -1.5·e^(−4t)·u(t)', 'y(t) = (-0.5·e^(−2t) + 2·e^(−3t) -1.5·e^(−4t))·u(t)'],
        'eq': ['ÿ(t) + 5ẏ(t) + 6y(t) = ẋ(t) + x(t)', 'Y(s) = (s + 1) / (s³ + 9s² + 26s + 24)', 'Y(s) = −0.5 / (s + 2) + 2 / (s + 3) − 1.5 / (s + 4)', 'y(t) = −0.5·e^(−2t)·u(t) + 2·e^(−3t)·u(t) − 1.5·e^(−4t)·u(t)', 'y(t) = (−0.5·e^(−2t) + 2·e^(−3t) − 1.5·e^(−4t))·u(t)']},
    'custom unstable': {'params': {'preset': 'custom', 'output_coeffs': '1, -1', 'input_coeffs': '1', 'input_signal': 'step'},
        'y': [0.0, 0.0161612672089, 0.173887207354, 1.22911179163, 3.96893937959, 10.0763213629, 23.690358558, 121.684894935, 200.0, 200.0],
        'eq_head': ['ẏ(t) − y(t) = x(t)', 'Y(s) = (1) / (s² − s)', 'Y(s) = -1 / (s) + 1 / (s − 1)', 'y(t) = -1·u(t) + 1·eᵗ·u(t)', 'y(t) = (-1 + 1·eᵗ)·u(t)'],
        'eq': ['ẏ(t) − y(t) = x(t)', 'Y(s) = 1 / (s² − s)', 'Y(s) = −1 / s + 1 / (s − 1)', 'y(t) = −u(t) + eᵗ·u(t)', 'y(t) = (−1 + eᵗ)·u(t)']},
    'custom decimals': {'params': {'preset': 'custom', 'output_coeffs': '0.5, 1.5, 1', 'input_coeffs': '2', 'input_signal': 'step'},
        'y': [0.0, 0.000505889357914, 0.0438846381175, 0.608063685596, 1.27600251425, 1.65517119712, 1.84127420783, 1.96752902567, 1.99344385052, 1.99865837456],
        'eq_head': ['0.5ÿ(t) + 1.5ẏ(t) + y(t) = 2x(t)', 'Y(s) = (4) / (s³ + 3s² + 2s)', 'Y(s) = 2 / (s) + -4 / (s + 1) + 2 / (s + 2)', 'y(t) = 2·u(t) + -4·e⁻ᵗ·u(t) + 2·e^(−2t)·u(t)', 'y(t) = (2 -4·e⁻ᵗ + 2·e^(−2t))·u(t)'],
        'eq': ['0.5ÿ(t) + 1.5ẏ(t) + y(t) = 2x(t)', 'Y(s) = 4 / (s³ + 3s² + 2s)', 'Y(s) = 2 / s − 4 / (s + 1) + 2 / (s + 2)', 'y(t) = 2·u(t) − 4·e⁻ᵗ·u(t) + 2·e^(−2t)·u(t)', 'y(t) = (2 − 4·e⁻ᵗ + 2·e^(−2t))·u(t)']},
}


@pytest.mark.parametrize("key", list(GOLDEN_HEAD))
def test_zero_ics_reproduce_pre_change_golden(key):
    G = GOLDEN_HEAD[key]
    p = G["params"]
    base = {k: v for k, v in p.items() if k in ("preset", "output_coeffs", "input_coeffs")}
    sim = make_sim(base, p.get("input_signal"), p.get("alpha"), p.get("omega"), (0, 0, 0))
    st = sim.get_state()
    y = plot(st, "time_response")["data"][0]["y"]
    for i, ref in zip(IDX, G["y"]):
        assert abs(y[i] - ref) <= 1e-10 * max(1.0, abs(ref))
    steps = st["metadata"]["solution_steps"]
    assert [steps[i]["equation"] for i in (0, 2, 3, 4, 5)] == G["eq"]
    assert "All initial conditions are zero (system at rest)." in steps[0]["description"]


def test_unused_and_hidden_ic_sliders_have_no_effect():
    ref = make_sim({"preset": "first_order_impulse"}, ics=(1, 0, 0))
    hid = make_sim({"preset": "first_order_impulse"}, ics=(1, 5, 5))
    assert np.array_equal(ref._y_raw, hid._y_raw)
    assert ref._I_poly == hid._I_poly == [1.0]
    ref = make_sim({"preset": "underdamped"}, ics=(1, -2, 0))
    hid = make_sim({"preset": "underdamped"}, ics=(1, -2, 4.5))
    assert np.array_equal(ref._y_raw, hid._y_raw)
    ref = make_sim({"preset": "custom", "output_coeffs": "1, 3, 2"}, ics=(1, 2, 0))
    hid = make_sim({"preset": "custom", "output_coeffs": "1, 3, 2"}, ics=(1, 2, 3))
    assert np.array_equal(ref._y_raw, hid._y_raw)
    zero = make_sim({"preset": "second_order_step"}, ics=(0, 0, 0))
    hid0 = make_sim({"preset": "second_order_step"}, ics=(0, 0, 3))
    assert np.array_equal(zero._y_raw, hid0._y_raw)
    assert hid0._ics_zero


# =============================================================================
# 5. Decomposition, poles/zeros, 0⁻ vs 0⁺
# =============================================================================

def test_decomposition_view_traces_sum_to_total():
    sim = make_sim({"preset": "third_order"}, ics=(1, 0, -1))
    sim.update_parameter("response_view", "decomposition")
    data = plot(sim.get_state(), "time_response")["data"]
    by = {d["name"]: np.array(d["y"]) for d in data if "name" in d}
    zi = by["y<sub>zi</sub>(t) zero-input"]
    zs = by["y<sub>zs</sub>(t) zero-state"]
    tot = by["y(t) = y<sub>zi</sub> + y<sub>zs</sub>"]
    assert np.max(np.abs(zi + zs - tot)) < 1e-12
    sim.update_parameter("response_view", "total")
    names = [d.get("name") for d in plot(sim.get_state(), "time_response")["data"]]
    assert names[0] == "y(t)" and "y<sub>zi</sub>(t) zero-input" not in names


def test_zero_input_depends_only_on_A_and_ics():
    zis = []
    for kind, al, om in INPUT_COMBOS:
        sim = make_sim({"preset": "second_order_impulse"}, kind, al, om, (2, -1))
        zis.append(sim._y_zi_raw)
    sim = make_sim({"preset": "custom", "output_coeffs": "1, 3, 2", "input_coeffs": "4, 1"}, "delta", ics=(2, -1))
    zis.append(sim._y_zi_raw)
    for z in zis[1:]:
        assert np.max(np.abs(z - zis[0])) < 1e-12
    # y_zi(0⁺) = y(0⁻): the zero-input part carries the ICs continuously
    assert abs(zis[0][0] - 2.0) < 1e-12


def test_ics_move_zeros_not_poles_and_cancellation_is_flagged():
    base = make_sim({"preset": "second_order_impulse"}, ics=(0, 0))
    moved = make_sim({"preset": "second_order_impulse"}, ics=(2, -1))
    assert np.allclose(sorted(base._poles, key=lambda z: z.real), sorted(moved._poles, key=lambda z: z.real))
    assert len(base._zeros) == 0 and len(moved._zeros) == 1
    assert abs(moved._zeros[0] - (-3.0)) < 1e-12  # Y = (2s + 6)/((s+1)(s+2))

    # I(s) = s + 2 shares the root −2 with A(s): the ICs excite only e^{-t} in y_zi,
    # but the impulse still excites e^{-2t} in y_zs, so the total keeps both modes.
    single = make_sim({"preset": "second_order_impulse"}, ics=(1, -1))
    ic = single.get_state()["metadata"]["initial_conditions"]
    assert ic["cancellations"] == []
    assert len(ic["zi_cancellations"]) == 1 and abs(ic["zi_cancellations"][0]["pole"]["real"] + 2.0) < 1e-12
    assert relerr(single._y_zi_raw, np.exp(-single._t)) < 1e-12
    assert relerr(single._y_raw, 2 * np.exp(-single._t) - np.exp(-2 * single._t)) < 1e-12

    # Total cancellation: O&W 9.38 ODE with the unit step and (3, −5):
    # Y = (3s + 1)(s + 1) / (s (s + 1)(s + 2)) → the e^{-t} mode is absent from y(t).
    canc = make_sim({"preset": "second_order_step"}, ics=(3, -5))
    st = canc.get_state()
    c = st["metadata"]["initial_conditions"]["cancellations"]
    assert len(c) == 1 and abs(c[0]["pole"]["real"] + 1.0) < 1e-12
    pz = plot(st, "pole_zero_splane")
    assert any(tr.get("name") == "Pole-zero cancellation" for tr in pz["data"])
    assert relerr(canc._y_raw, 0.5 + 2.5 * np.exp(-2 * canc._t)) < 1e-12
    assert "e⁻ᵗ" not in st["metadata"]["solution_steps"][5]["equation"]


def test_initial_value_markers_and_text():
    sim = make_sim({"preset": "first_order_impulse"}, ics=(2,))
    st = sim.get_state()
    names = [d.get("name") for d in plot(st, "time_response")["data"]]
    assert "y(0⁻) = 2" in names and "y(0⁺) = 3" in names
    ic = st["metadata"]["initial_conditions"]
    assert ic["has_jump"] is True
    assert ic["initial_values"][0]["minus"] == 2.0 and ic["initial_values"][0]["plus"] == 3.0
    assert "δ(t)" in ic["jump_text"]
    assert "y(0⁺)" in ic["ivt_text"] and "= 3" in ic["ivt_text"]
    assert "0⁻" in ic["explanation"] and "y(0⁺)" in ic["explanation"]
    assert "causal" in ic["causal_note"]
    # no jump at IC level for a step input: no y(0⁻) marker
    st = make_sim({"preset": "second_order_step"}, ics=(1, 2)).get_state()
    names = [d.get("name") for d in plot(st, "time_response")["data"]]
    assert not any(n and n.startswith("y(0⁻)") for n in names)
    assert st["metadata"]["initial_conditions"]["has_jump"] is False


def test_impulse_terms_reported():
    sim = make_sim({"preset": "custom", "output_coeffs": "1, 2", "input_coeffs": "1, 0, 0"}, "delta", ics=(0.5,))
    assert sim._direct_terms == [-2.0, 1.0]  # Q(s) = s − 2 ↔ δ′(t) − 2δ(t)
    st = sim.get_state()
    steps = st["metadata"]["solution_steps"]
    assert steps[3]["equation"] == "Y(s) = 4.5 / (s + 2) + (s − 2)"  # (s² + 0.5)/(s + 2)
    assert "δ′(t)" in st["metadata"]["initial_conditions"]["impulse_text"]
    assert "δ′(t)" in steps[5]["equation"]


# =============================================================================
# 6. Step text and the transformed equation
# =============================================================================

def test_transformed_equation_shows_ic_terms_and_I_of_s():
    st = make_sim({"preset": "second_order_impulse"}, ics=(2, -1)).get_state()
    steps = st["metadata"]["solution_steps"]
    assert steps[1]["equation"] == "[s²Y(s) − s·y(0⁻) − y′(0⁻)] + 3[sY(s) − y(0⁻)] + 2Y(s) = 1"
    assert "causal" in steps[1]["description"]
    ic = st["metadata"]["initial_conditions"]
    assert ic["I_symbolic"] == "y(0⁻)·s + [y′(0⁻) + 3y(0⁻)]"
    assert ic["I_numeric"] == "2s + 5"
    texts = [ln["text"] for ln in steps[2]["details"]["lines"]]
    assert "I(s) = y(0⁻)·s + [y′(0⁻) + 3y(0⁻)] = 2s + 5" in texts
    assert steps[5]["equation"] == "y(t) = 4·e⁻ᵗ − 2·e^(−2t),  t > 0"
    third = make_sim({"preset": "third_order"}, ics=(1, 0, -1)).get_state()
    assert third["metadata"]["initial_conditions"]["I_symbolic"] == (
        "y(0⁻)·s² + [y′(0⁻) + 6y(0⁻)]·s + [y″(0⁻) + 6y′(0⁻) + 11y(0⁻)]")
    nm = make_sim({"preset": "custom", "output_coeffs": "2, 1"}, "delta", ics=(3,)).get_state()
    assert nm["metadata"]["initial_conditions"]["I_symbolic"] == "2y(0⁻)"


def test_order_notes_for_custom_coefficients():
    def note(a):
        return make_sim({"preset": "custom", "output_coeffs": a}).get_state()["metadata"]["initial_conditions"]["note"]
    assert "only y(0⁻)" in note("1, 1")
    assert "y″(0⁻) slider is ignored" in note("1, 3, 2")
    assert "all used" in note("1, 6, 11, 6")
    assert "y‴(0⁻) = y⁽⁴⁾(0⁻) = 0" in note("1, 5, 10, 10, 5, 1")
    assert "no initial conditions" in note("2")
    assert make_sim({"preset": "third_order"}).get_state()["metadata"]["initial_conditions"]["note"] is None


def test_ic_change_keeps_step_but_ode_change_resets_it():
    sim = make_sim({"preset": "underdamped"})
    assert sim._current_step == Sim.MAX_STEP
    sim.update_parameter("ic_y0", 1.5)
    sim.update_parameter("response_view", "decomposition")
    assert sim._current_step == Sim.MAX_STEP
    sim.update_parameter("input_signal", "step")
    assert sim._current_step == 0


# =============================================================================
# 7. Pre-existing defects fixed along the way
# =============================================================================

def test_preexisting_coefficient_bugs_fixed():
    # leading zero: "0, 1, 2" is s + 2 (was silently turned into s² + s + 2)
    s = make_sim({"preset": "custom", "output_coeffs": "0, 1, 2"})
    assert s._output_poly == [1.0, 2.0] and s._order == 1
    # order 0 is solved as the algebraic equation 2y = x (was silently ẏ + y = x)
    s = make_sim({"preset": "custom", "output_coeffs": "2", "input_coeffs": "1, 3"}, "step")
    assert s._order == 0 and s._I_poly == [] and np.allclose(s._y_raw[1:], 1.5)
    # non-finite / unreadable coefficients: no crash, warning, fallback ẏ + y
    for bad in ("1, inf", "abc", "0, 0"):
        s = make_sim({"preset": "custom", "output_coeffs": bad})
        assert s._output_poly == [1.0, 1.0]
        assert s.get_state()["metadata"]["warnings"]


def test_preexisting_display_bugs_fixed():
    # step 1 right-hand side used X(s) and dropped B(s)
    st = make_sim({"preset": "custom", "output_coeffs": "1, 3, 2", "input_coeffs": "2"}, "step").get_state()
    assert st["metadata"]["solution_steps"][1]["equation"].endswith("= 2/s")
    st = make_sim({"preset": "custom", "output_coeffs": "1, 5, 6", "input_coeffs": "1, 1"}, "exp", 4.0).get_state()
    assert st["metadata"]["solution_steps"][1]["equation"].endswith("= (s + 1)/(s + 4)")
    # 4-fold root: factored form came from unclustered np.roots, e.g. '(s − (-0.9998))'
    st = make_sim({"preset": "custom", "output_coeffs": "1, 4, 6, 4, 1"}).get_state()
    assert "Factored: Y(s) = 1 / (s + 1)⁴." in st["metadata"]["solution_steps"][2]["description"]
    st = make_sim({"preset": "second_order_step"}).get_state()
    assert "Factored: Y(s) = 1 / [s(s + 2)(s + 1)]." in st["metadata"]["solution_steps"][2]["description"]
    # resonance: no stray '0 +' term (and no 't^1/1!·0.25sin(2t)')
    st = make_sim({"preset": "custom", "output_coeffs": "1, 0, 4"}, "cosine", None, 2.0).get_state()
    assert st["metadata"]["solution_steps"][5]["equation"] == "y(t) = 0.25·t·sin(2t)·u(t)"


def test_stability_judged_from_characteristic_roots():
    st = make_sim({"preset": "second_order_step"}).get_state()
    md = st["metadata"]
    assert md["system_info"]["stability"] == "stable"
    assert "Re(s) < 0" in md["solution_steps"][5]["description"]
    assert "steady-state term" in md["solution_steps"][5]["description"]  # the step's pole at s = 0
    st = make_sim({"preset": "custom", "output_coeffs": "1, 0, 4"}).get_state()
    assert st["metadata"]["system_info"]["stability"] == "marginally_stable"
    assert st["metadata"]["system_info"]["is_stable"] is False
    st = make_sim({"preset": "custom", "output_coeffs": "1, 0, 4"}, "cosine", None, 2.0).get_state()
    assert "resonance" in st["metadata"]["solution_steps"][5]["description"]
    st = make_sim({"preset": "custom", "output_coeffs": "1, -1"}, "step").get_state()
    assert st["metadata"]["system_info"]["stability"] == "unstable"
    assert "does not grow" not in st["metadata"]["solution_steps"][5]["description"]  # y = eᵗ − 1 grows


def _step5(sim: Sim) -> str:
    return sim.get_state()["metadata"]["solution_steps"][5]["description"]


def test_stability_text_uses_poles_left_after_cancellation():
    """Review finding: the y(t) sentence must use the poles that survive in the reduced
    Y(s) (multiplicity mult_D − cancel), not every pole of A(s)X_den(s)."""
    # RC high-pass y′ + y = x′, step: Y = s/(s(s + 1)) = 1/(s + 1), y = e^{-t} → 0
    sim = make_sim({"preset": "custom", "output_coeffs": "1, 1", "input_coeffs": "1, 0"}, "step")
    txt = _step5(sim)
    assert "does not decay" not in txt
    assert "cancelled by zero(s) of H(s) = B(s)/A(s)" in txt and "y(t) → 0" in txt
    assert relerr(sim._y_raw, np.exp(-sim._t)) < 1e-12
    # notch y″ + 3y′ + 2y = x″ + 4x with cos 2t: the ±2j poles cancel, y = −e^{-t} + 2e^{-2t} → 0
    sim = make_sim({"preset": "custom", "output_coeffs": "1, 3, 2", "input_coeffs": "1, 0, 4"}, "cosine", None, 2.0)
    txt = _step5(sim)
    assert "does not decay" not in txt and "y(t) → 0" in txt
    assert relerr(sim._y_raw, -np.exp(-sim._t) + 2 * np.exp(-2 * sim._t)) < 1e-12
    # y″ + 4y = x″ + 4x, cos 2t, y(0⁻) = 1: Y = 2s/(s² + 4), y = 2cos 2t stays bounded
    sim = make_sim({"preset": "custom", "output_coeffs": "1, 0, 4", "input_coeffs": "1, 0, 4"}, "cosine", None, 2.0, (1, 0))
    txt = _step5(sim)
    assert "grows" not in txt and "no resonance" in txt
    assert relerr(sim._y_raw, 2 * np.cos(2 * sim._t)) < 1e-12
    # genuine resonance is still reported: y″ + 4y = x, cos 2t → (t/4) sin 2t
    sim = make_sim({"preset": "custom", "output_coeffs": "1, 0, 4"}, "cosine", None, 2.0)
    assert "y(t) grows (resonance" in _step5(sim)
    # marginally stable, input pole elsewhere on the axis: y″ + 4y = x, step → (1 − cos 2t)/4
    sim = make_sim({"preset": "custom", "output_coeffs": "1, 0, 4"}, "step")
    txt = _step5(sim)
    assert "add a term that does not decay" in txt and "grows" not in txt
    # unstable system whose growing mode is cancelled: y′ − y = x, step, y(0⁻) = −1 → y = −1
    sim = make_sim({"preset": "custom", "output_coeffs": "1, -1"}, "step", ics=(-1,))
    txt = _step5(sim)
    assert txt.startswith("UNSTABLE") and "this y(t) does not grow" in txt
    assert relerr(sim._y_raw, -np.ones_like(sim._t)) < 1e-12
    # Y(s) ≡ 0: y′ − y = x, δ(t), y(0⁻) = −1
    sim = make_sim({"preset": "custom", "output_coeffs": "1, -1"}, "delta", ics=(-1,))
    assert "Y(s) = 0 exactly" in _step5(sim)
    assert np.max(np.abs(sim._y_raw)) < 1e-12


def test_cancellation_text_names_the_constant_mode():
    """Review finding: s = 0 read 'so the mode a constant is absent'."""
    st = make_sim({"preset": "custom", "output_coeffs": "1, 1", "input_coeffs": "1, 0"}, "step").get_state()
    text = "s = 0: a zero of Y(s) cancels this pole, so the constant mode is absent from y(t)."
    assert [c["text"] for c in st["metadata"]["initial_conditions"]["cancellations"]] == [text]
    assert text in [ln["text"] for ln in st["metadata"]["solution_steps"][2]["details"]["lines"]]
    # zero-input version: A = s(s + 1), ICs (1, −1) give I(s) = s, which shares s = 0 with A
    st = make_sim({"preset": "custom", "output_coeffs": "1, 1, 0"}, "delta", ics=(1, -1)).get_state()
    zi = [c["text"] for c in st["metadata"]["initial_conditions"]["zi_cancellations"]]
    assert zi == ["s = 0: I(s) shares this root with A(s), so these initial conditions do not "
                  "excite the constant mode — it is absent from y_zi(t)."]
    st = make_sim({"preset": "second_order_step"}, ics=(3, -5)).get_state()
    assert st["metadata"]["initial_conditions"]["cancellations"][0]["text"] == (
        "s = −1: a zero of Y(s) cancels this pole, so the mode e⁻ᵗ is absent from y(t).")


def test_partial_cancellation_is_not_called_absent():
    """Found while re-verifying: a zero that cancels only some factors of a repeated pole
    removes only the highest t-powers, not the mode (y″ + 4y = x″ + 4x, cos 2t, y(0⁻) = 1
    gives y = 2cos 2t, so cos/sin(2t) is present)."""
    sim = make_sim({"preset": "custom", "output_coeffs": "1, 0, 4", "input_coeffs": "1, 0, 4"}, "cosine", None, 2.0, (1, 0))
    st = sim.get_state()
    texts = [c["text"] for c in st["metadata"]["initial_conditions"]["cancellations"]]
    assert texts == ["s = 2j and its conjugate: a zero of Y(s) cancels 1 of the 2 repeated factors of this pole, "
                     "so y(t) has no t·cos/sin(2t) term (the mode cos/sin(2t) remains)."]
    hover = [tr for tr in plot(st, "pole_zero_splane")["data"] if tr.get("name") == "Pole-zero cancellation"][0]["text"]
    assert all("multiplicity 1 left" in h for h in hover)
    # zero-input: A = (s + 1)³, ICs (1, −1, 1) give I = (s + 1)², so y_zi = e^{-t} only
    sim = make_sim({"preset": "custom", "output_coeffs": "1, 3, 3, 1"}, "delta", ics=(1, -1, 1))
    zi = [c["text"] for c in sim.get_state()["metadata"]["initial_conditions"]["zi_cancellations"]]
    assert zi == ["s = −1: I(s) shares 2 of the 3 repeated factors of this root with A(s), so y_zi(t) has no "
                  "t·e⁻ᵗ and t²·e⁻ᵗ terms (the mode e⁻ᵗ remains)."]
    assert relerr(sim._y_zi_raw, np.exp(-sim._t)) < 1e-12


# Defects the review listed in the time-domain / partial-fraction strings
_BAD_TYPOGRAPHY = [
    (re.compile(r"\+ [−-]"), "'+ −' instead of ' − '"),
    (re.compile(r"(?<![\d.])1·"), "unit coefficient 1·"),
    (re.compile(r"(?<![\d.])1(cos|sin)\("), "unit coefficient 1cos/1sin"),
    (re.compile(r"/1!|t\^\d"), "t/1! or t^k"),
    (re.compile(r"e\^\(-|e\^\(−?0t\)|e\^\(−?1t\)"), "e^(-…t), e^(0t) or e^(1t)"),
    (re.compile(r"(?<![\w.^])-\d"), "ASCII hyphen as minus"),
    (re.compile(r"\(s − \([−-]?\d+(\.\d+)?\)\)|\(s − \([−-]?\d*j\)\)|/ \(s\)"), "unsimplified pole factor"),
    (re.compile(r"(?<![\d.])1jt|\(1t\)|(?<![\d.])1j\b"), "1j / 1t"),
    (re.compile(r"(?<![\w(])[−-]?\d+(\.\d+)?[+−]\d*(\.\d+)?j [/·]"), "unparenthesised complex residue"),
    (re.compile(r"mode a constant"), "'the mode a constant'"),
]


def _display_strings(st: Dict[str, Any]) -> List[str]:
    md = st["metadata"]
    out: List[str] = []
    for step in md["solution_steps"]:
        d = step["details"]
        out += [step["equation"], step["description"]]
        out += [ln["text"] for ln in d.get("lines", [])]
        out += [p["s_domain"] for p in d.get("pairs", [])] + [p["time_domain"] for p in d.get("pairs", [])]
        out += [a["explanation"] for a in d.get("algebra_steps", [])]
    ic = md["initial_conditions"]
    out += [ic["expression_zs"], ic["expression_zi"], ic["impulse_text"] or ""]
    out += [c["text"] for c in ic["cancellations"] + ic["zi_cancellations"]]
    cl = md["classical_solution"]
    if cl:
        out += cl["roots"] + [cl["homogeneous_form"], cl["particular_form"], cl["summary"]]
    return out


def test_display_typography_sweep():
    cases = [({"preset": n}, k, al, om, ics) for n in Sim.PRESETS for (k, al, om) in INPUT_COMBOS
             for ics in ((0, 0, 0), (2, -1, 0.5), (1, -1, 0))]
    for a, b in [("1, 1", "1, 0"), ("1, 0, 4", "1"), ("1, 0, 1", "1, 0"), ("1, -1", "1"), ("1, 2", "1, 0, 0"),
                 ("1, 4, 6, 4, 1", "1"), ("1, 0, 0", "1"), ("1, 2, 5", "3, 1"), ("2", "1, 3"), ("1, 2, 2", "1")]:
        for k, al, om in (("delta", 1.0, 2.0), ("step", 1.0, 2.0), ("cosine", 1.0, 1.0), ("cosine", 1.0, 2.0), ("exp", 1.0, 2.0)):
            for ics in ((0, 0, 0), (-1, 0, 0), (1, 2, 0)):
                cases.append(({"preset": "custom", "output_coeffs": a, "input_coeffs": b}, k, al, om, ics))
    checked = 0
    for params, k, al, om, ics in cases:
        st = make_sim({**params, "show_compare": True}, k, al, om, ics).get_state()
        for text in _display_strings(st):
            for pat, what in _BAD_TYPOGRAPHY:
                m = pat.search(text)
                assert m is None, f"{what}: {m.group(0)!r} in {text!r} ({params}, {k}, {ics})"
            checked += 1
    assert checked > 10000


def test_typography_examples():
    st = make_sim({"preset": "second_order_impulse"}, ics=(2, -1)).get_state()
    steps = st["metadata"]["solution_steps"]
    assert steps[3]["equation"] == "Y(s) = 4 / (s + 1) − 2 / (s + 2)"
    assert "y_zs(t) = e⁻ᵗ − e^(−2t)" in [ln["text"] for ln in steps[4]["details"]["lines"]]
    st = make_sim({"preset": "custom", "output_coeffs": "1, 2, 5"}, ics=(1, 1)).get_state()
    # I(s) = s + 3, Y = (s + 4)/((s + 1)² + 4) = (s + 1)/(…) + (3/2)·2/(…): y = e^{-t}(cos 2t + 1.5 sin 2t)
    assert st["metadata"]["solution_steps"][5]["equation"] == "y(t) = e⁻ᵗ·(cos(2t) + 1.5·sin(2t)),  t > 0"
    st = make_sim({"preset": "third_order"}, "cosine", None, 2.0).get_state()
    assert "(−0.01731−0.01346j) / (s − 2j)" in st["metadata"]["solution_steps"][3]["equation"]
    st = make_sim({"preset": "custom", "output_coeffs": "1, 0, 1"}, "cosine", None, 1.0).get_state()
    assert st["metadata"]["solution_steps"][5]["equation"] == "y(t) = 0.5·t·sin(t)·u(t)"


def test_classical_panel_text():
    def cl(params, kind=None, omega=None):
        return make_sim({**params, "show_compare": True}, kind, None, omega).get_state()["metadata"]["classical_solution"]
    c = cl({"preset": "custom", "output_coeffs": "1, 4, 6, 4, 1"})
    assert c["roots"] == ["s₁ = −1", "s₂ = −1", "s₃ = −1", "s₄ = −1"]
    assert c["homogeneous_form"] == "C₁·e⁻ᵗ + C₂·t·e⁻ᵗ + C₃·t²·e⁻ᵗ + C₄·t³·e⁻ᵗ"
    assert c["summary"].startswith("Classical method, 6 steps: (1)") and "(6)" in c["summary"]
    assert cl({"preset": "underdamped"})["homogeneous_form"] == "e⁻ᵗ·(C₁·cos(2t) + C₂·sin(2t))"
    c = cl({"preset": "custom", "output_coeffs": "1, 0, 4"}, "cosine", 2.0)
    assert c["homogeneous_form"] == "C₁·cos(2t) + C₂·sin(2t)"  # was 'e^(-0t)(C₁cos(2t) + …)'
    assert "multiply it by t" in c["particular_form"]  # undetermined coefficients, duplicated mode
    assert "multiply" not in cl({"preset": "second_order_step"})["particular_form"]
    assert cl({"preset": "second_order_step"})["homogeneous_form"] == "C₁·e⁻ᵗ + C₂·e^(−2t)"
    assert cl({"preset": "custom", "output_coeffs": "2", "input_coeffs": "1"})["summary"].startswith("Order 0")


# =============================================================================
# 8. Catalog contract and API round trip
# =============================================================================

def test_catalog_ic_controls():
    entry = next(e for e in SIMULATION_CATALOG if e["id"] == "ode_laplace_solver")
    ctrls = {c["name"]: c for c in entry["controls"]}
    for name in ("ic_y0", "ic_y1", "ic_y2", "response_view"):
        assert name in ctrls and name in Sim.PARAMETER_SCHEMA and name in Sim.DEFAULT_PARAMS
        assert entry["default_params"][name] == Sim.DEFAULT_PARAMS[name]
    assert [ctrls[n]["label"] for n in ("ic_y0", "ic_y1", "ic_y2")] == ["y(0⁻)", "y′(0⁻)", "y″(0⁻)"]
    assert all(ctrls[n]["default"] == 0 for n in ("ic_y0", "ic_y1", "ic_y2"))
    assert "visible_when" not in ctrls["ic_y0"]
    second = {"second_order_impulse", "second_order_step", "underdamped", "repeated_poles", "third_order", "custom"}
    assert set(ctrls["ic_y1"]["visible_when"]["preset"]) == second
    assert set(ctrls["ic_y2"]["visible_when"]["preset"]) == {"third_order", "custom"}
    # every preset shows exactly as many IC sliders as its order (custom: 3)
    for preset, P in Sim.PRESETS.items():
        shown = sum(1 for n in ("ic_y0", "ic_y1", "ic_y2")
                    if "visible_when" not in ctrls[n] or preset in ctrls[n]["visible_when"]["preset"])
        assert shown == len(P["output_coeffs"]) - 1, preset


def test_api_round_trip():
    from fastapi.testclient import TestClient
    from main import app

    client = TestClient(app)
    sid = "ode-ic-test"
    r = client.post("/api/simulations/ode_laplace_solver/update", headers={"X-Session-ID": sid},
                    json={"params": {"preset": "second_order_impulse", "ic_y0": 2, "ic_y1": -1}})
    assert r.status_code == 200 and r.json()["success"]
    r = client.post("/api/simulations/ode_laplace_solver/execute", headers={"X-Session-ID": sid},
                    json={"action": "show_all", "params": {}})
    md = r.json()["data"]["metadata"]
    assert md["initial_conditions"]["ics_used"] == [2.0, -1.0]
    assert md["initial_conditions"]["I_coeffs"] == [2.0, 5.0]
    assert md["solution_steps"][5]["equation"] == "y(t) = 4·e⁻ᵗ − 2·e^(−2t),  t > 0"
