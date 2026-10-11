"""
CT/DT Poles Conversion Simulator

First-order CT system  tau*y'(t) + y(t) = x(t),  initially at rest,  pole s_p = -1/tau.

Sampling with period T maps a CT pole exactly to z = e^{sT} (ZOH / impulse
invariance).  Forward Euler, Backward Euler and Trapezoidal (Tustin) are
numerical-integration approximations of that map.  The tool shows:
- CT -> DT: the method's DT pole next to the exact pole e^{sT}
- DT -> CT: the equivalent CT pole s_eq = ln(z)/T of the method's DT pole
- the difference equation each method produces and its unit-step response.

Every recursion started at rest has the closed form y[n] = 1 - z^n, the DT
image of the CT step response y(t) = 1 - e^{s_p t}.
"""

import cmath
import math
from typing import Any, Dict, List, Optional

import numpy as np

from .base_simulator import BaseSimulator


class CTDTPolesSimulator(BaseSimulator):
    """CT -> DT pole conversion and the step response of the resulting difference equation."""

    TAU = 1.0
    T_HORIZON = 6.0          # CT transient window (6 tau)
    MIN_SAMPLES = 10         # always show at least this many steps after y[0]
    MAX_SAMPLES = 600
    STEM_LIMIT = 60          # draw stems up to this many samples, markers only beyond
    H_GRID = np.linspace(0.005, 3.0, 600)
    TOL = 1e-9

    S_VIEW = {"x": [-4.5, 1.5], "y": [-3.4, 3.4]}
    Z_VIEW = {"x": [-2.25, 1.75], "y": [-1.6, 1.6]}

    COLORS = {
        "ct": "#3b82f6",
        "stable": "#14b8a6",
        "marginal": "#f59e0b",
        "unstable": "#ef4444",
        "boundary": "#8b5cf6",
        "image": "#f59e0b",
        "reference": "#10b981",
        "fill_stable": "rgba(16, 185, 129, 0.12)",
        "fill_image": "rgba(245, 158, 11, 0.05)",
        "grid": "rgba(148, 163, 184, 0.2)",
        "axis": "rgba(148, 163, 184, 0.55)",
    }

    METHODS: Dict[str, Dict[str, str]] = {
        "forward_euler": {
            "name": "Forward Euler",
            "derivative": r"\dot y(nT) \approx \dfrac{y[n+1]-y[n]}{T}",
            "substitution": r"s \;\to\; \dfrac{z-1}{T}",
            "pole_map": r"z = 1 + sT",
            "inverse_map": r"s = \dfrac{z-1}{T}",
            "region": "The jω axis maps to the vertical line Re z = 1, so the left half-plane maps to Re z < 1, "
                      "which reaches outside the unit circle. A CT pole lands inside the unit circle only if it lies "
                      "in the disk |s + 1/T| < 1/T. For s = −1/τ this means T/τ < 2.",
            "concept": "Uses the slope at the start of each step to predict the next sample (explicit).",
            "strength": "Simplest possible update; no equation to solve each step.",
            "weakness": "The DT pole 1 − T/τ turns negative for T > τ (alternating samples) and leaves the unit "
                        "circle for T > 2τ, although the CT system is stable.",
        },
        "backward_euler": {
            "name": "Backward Euler",
            "derivative": r"\dot y(nT) \approx \dfrac{y[n]-y[n-1]}{T}",
            "substitution": r"s \;\to\; \dfrac{z-1}{zT}",
            "pole_map": r"z = \dfrac{1}{1 - sT}",
            "inverse_map": r"s = \dfrac{z-1}{zT}",
            "region": "The jω axis maps to the circle |z − ½| = ½ and the whole left half-plane maps inside it, "
                      "so a stable CT system always gives a stable DT system. It also maps the right half-plane "
                      "outside the disk |s − 1/T| < 1/T inside the unit circle, so an unstable CT system can "
                      "look stable.",
            "concept": "Uses the slope at the end of each step (implicit).",
            "strength": "Stable for every T when the CT system is stable; real poles stay positive (no alternation).",
            "weakness": "The DT pole 1/(1 + T/τ) is larger than e^(−T/τ), so the response decays too slowly "
                        "(over-damped) for large T.",
        },
        "trapezoidal": {
            "name": "Trapezoidal (Tustin)",
            "derivative": r"\dfrac{y[n]-y[n-1]}{T} \approx \tfrac{1}{2}\big(\dot y(nT) + \dot y((n-1)T)\big)",
            "substitution": r"s \;\to\; \dfrac{2}{T}\,\dfrac{z-1}{z+1}",
            "pole_map": r"z = \dfrac{1 + sT/2}{1 - sT/2}",
            "inverse_map": r"s = \dfrac{2}{T}\,\dfrac{z-1}{z+1}",
            "region": "The jω axis maps exactly onto the unit circle and the left half-plane onto the unit disk, "
                      "so stability is preserved in both directions. Frequencies are warped: "
                      "ω = (2/T)·tan(Ω/2).",
            "concept": "Averages the slopes at both ends of each step (bilinear transform).",
            "strength": "Second-order accurate; preserves stability exactly.",
            "weakness": "For s = −1/τ the DT pole (2τ − T)/(2τ + T) turns negative for T > 2τ, giving alternating "
                        "samples the CT system does not have.",
        },
        "exact_zoh": {
            "name": "Exact sampling (ZOH)",
            "derivative": r"y\big((n+1)T\big) = e^{-T/\tau}\,y(nT) + \big(1-e^{-T/\tau}\big)\,x[n]",
            "substitution": r"\text{solve the ODE exactly over each step with } x \text{ held constant}",
            "pole_map": r"z = e^{sT}",
            "inverse_map": r"s = \dfrac{\ln z}{T}",
            "region": "The left half-plane maps into the unit disk and the jω axis onto the unit circle, but the map "
                      "is many-to-one: s and s + j2πk/T give the same z (aliasing; primary strip |ω| < π/T).",
            "concept": "This is the true CT → DT pole conversion: every exact sampled-data equivalent "
                       "(zero-order hold, impulse invariance) has its poles at z = e^(sT).",
            "strength": "With the input held between samples the samples equal y(nT) exactly, for any T.",
            "weakness": "Needs the exponential e^(sT); the input must really be piecewise constant for the "
                        "match to be exact.",
        },
    }

    GUIDED_SCENARIOS: List[Dict[str, Any]] = [
        {"title": "Small step (stable)", "t_tau_ratio": 0.3, "method": "forward_euler",
         "message": "Small T: the Forward-Euler pole 1 − T/τ = 0.70 is close to the exact pole "
                    "e^(−T/τ) = 0.741, so the samples track the CT curve closely."},
        {"title": "Deadbeat at T = τ", "t_tau_ratio": 1.0, "method": "forward_euler",
         "message": "At T = τ the Forward-Euler pole is z = 0: the response reaches 1 in a single step. "
                    "The true sampled pole is e^(−1) = 0.368."},
        {"title": "Near the FE limit", "t_tau_ratio": 1.8, "method": "forward_euler",
         "message": "z = −0.8 is still inside the unit circle, but it is negative, so the samples alternate around "
                    "the final value. A real CT pole never maps to a negative z under exact sampling."},
        {"title": "FE unstable", "t_tau_ratio": 2.2, "method": "forward_euler",
         "message": "z = −1.2 is outside the unit circle: the difference equation diverges although the CT system "
                    "is stable. Its equivalent CT pole ln(z)/T lies in the right half-plane."},
        {"title": "Backward Euler, same T", "t_tau_ratio": 2.2, "method": "backward_euler",
         "message": "Backward Euler maps the whole left half-plane inside |z − ½| = ½: z = 0.3125 is stable, "
                    "but slower than the exact pole e^(−2.2) = 0.111."},
        {"title": "Trapezoidal, same T", "t_tau_ratio": 2.2, "method": "trapezoidal",
         "message": "Tustin keeps the pole inside the unit circle for every T, but z = −0.0476 is negative, "
                    "so the samples alternate slightly. Exact pole: 0.111."},
        {"title": "Exact sampling", "t_tau_ratio": 2.2, "method": "exact_zoh",
         "message": "z = e^(sT) = 0.1108: the ZOH difference equation reproduces y(nT) exactly at every sample, "
                    "for any step size."},
    ]

    PARAMETER_SCHEMA = {
        "t_tau_ratio": {"type": "slider", "min": 0.01, "max": 3.0, "step": 0.01, "default": 0.5},
        "method": {"type": "select", "options": ["forward_euler", "backward_euler", "trapezoidal", "exact_zoh"],
                   "default": "forward_euler"},
        "guided_scenario": {"type": "select",
                            "options": ["none"] + [str(i) for i in range(len(GUIDED_SCENARIOS))],
                            "default": "none"},
    }

    DEFAULT_PARAMS = {
        "t_tau_ratio": 0.5,
        "method": "forward_euler",
        "guided_scenario": "none",
    }

    SCENARIO_KEYS = ("t_tau_ratio", "method")

    def __init__(self, simulation_id: str):
        super().__init__(simulation_id)
        self._r: Dict[str, Any] = {}

    # ------------------------------------------------------------------ params

    def initialize(self, params: Optional[Dict[str, Any]] = None) -> None:
        self.parameters = self.DEFAULT_PARAMS.copy()
        for name, value in (params or {}).items():
            if name in self.parameters:
                self.parameters[name] = self._validate_param(name, value)
        if self.parameters["guided_scenario"] != "none":
            self._apply_scenario(self.parameters["guided_scenario"])
        self._initialized = True
        self._compute()

    def update_parameter(self, name: str, value: Any) -> Dict[str, Any]:
        if name == "guided_scenario":
            value = self._validate_param(name, value)
            if value == "none":
                self.parameters["guided_scenario"] = "none"
            else:
                self._apply_scenario(value)
        elif name in self.parameters:
            self.parameters[name] = self._validate_param(name, value)
            self.parameters["guided_scenario"] = "none"
        return self.get_state()

    def reset(self) -> Dict[str, Any]:
        self.initialize()
        return self.get_state()

    def _apply_scenario(self, key: str) -> None:
        scenario = self.GUIDED_SCENARIOS[int(key)]
        for k in self.SCENARIO_KEYS:
            self.parameters[k] = scenario[k]
        self.parameters["guided_scenario"] = key

    # ------------------------------------------------------------------- math

    @staticmethod
    def _s_to_z(s: Any, T: float, method: str) -> Any:
        """CT -> DT pole map of the given method (vectorised over complex s)."""
        sT = s * T
        if method == "forward_euler":
            return 1 + sT
        if method == "backward_euler":
            return 1 / (1 - sT)
        if method == "trapezoidal":
            return (1 + sT / 2) / (1 - sT / 2)
        return np.exp(sT)

    @classmethod
    def _equivalent_s(cls, z: float, T: float) -> Dict[str, Any]:
        """DT -> CT: s_eq = ln(z)/T (principal branch; a negative real z gives the pair (ln|z| +- j*pi)/T)."""
        if abs(z) < cls.TOL:
            return {"kind": "deadbeat", "re": None, "im": 0.0}
        log_z = cmath.log(complex(z))
        s = log_z / T
        im = abs(s.imag) if abs(s.imag) > cls.TOL else 0.0
        return {"kind": "pair" if im else "real", "re": s.real, "im": im}

    def _classify(self, z: float) -> str:
        mag = abs(z)
        if mag < 1 - self.TOL:
            return "stable"
        if mag > 1 + self.TOL:
            return "unstable"
        return "marginal"

    def _mode_text(self, z: float) -> str:
        if abs(z) < self.TOL:
            return "deadbeat: the transient vanishes after one step"
        if z > 0:
            return "monotonic decay" if z < 1 - self.TOL else (
                "constant (marginal)" if z <= 1 + self.TOL else "monotonic growth")
        if z > -1 + self.TOL:
            return "alternating decay: the sign of the transient flips every sample"
        if z >= -1 - self.TOL:
            return "alternating with constant amplitude (marginal)"
        return "alternating growth: the samples diverge"

    def _compute(self) -> None:
        p = self.parameters
        tau = self.TAU
        h = float(p["t_tau_ratio"])
        T = h * tau
        method = p["method"]

        s_p = -1.0 / tau
        z_d = float(self._s_to_z(s_p, T, method))
        z_exact = math.exp(s_p * T)

        # Difference equation started at rest: y[0] = y(0) = 0, x[n] = u(nT) = 1 for n >= 0
        n_steps = int(min(self.MAX_SAMPLES, max(self.MIN_SAMPLES, math.floor(self.T_HORIZON / T + 1e-9))))
        n = np.arange(n_steps + 1)
        x = np.ones(n_steps + 1)
        a = math.exp(-h)
        y = np.empty(n_steps + 1)
        y[0] = 0.0
        with np.errstate(over="ignore", invalid="ignore"):
            for k in range(1, n_steps + 1):
                if method == "forward_euler":
                    y[k] = (1 - h) * y[k - 1] + h * x[k - 1]
                elif method == "backward_euler":
                    y[k] = (y[k - 1] + h * x[k]) / (1 + h)
                elif method == "trapezoidal":
                    y[k] = ((2 - h) * y[k - 1] + h * (x[k] + x[k - 1])) / (2 + h)
                else:
                    y[k] = a * y[k - 1] + (1 - a) * x[k - 1]

        t_n = n * T
        t_end = float(t_n[-1])
        t_ct = np.linspace(0.0, t_end, 1201)
        y_ct = 1 - np.exp(s_p * t_ct)
        y_ct_n = 1 - np.exp(s_p * t_n)

        stability = self._classify(z_d)
        window = t_n <= self.T_HORIZON + 1e-9
        err = y[window] - y_ct_n[window]
        if stability != "stable":
            rms, rating = None, stability.upper()
        else:
            rms = float(np.sqrt(np.mean(err ** 2)))
            if rms < 1e-9:
                rating = "EXACT"
            elif rms < 0.05:
                rating = "EXCELLENT"
            elif rms < 0.15:
                rating = "GOOD"
            elif rms < 0.3:
                rating = "FAIR"
            else:
                rating = "POOR"

        self._r = {
            "h": h, "T": T, "tau": tau, "method": method,
            "s_p": s_p, "z_d": z_d, "z_exact": z_exact, "s_eq": self._equivalent_s(z_d, T),
            "stability": stability, "n": n, "t_n": t_n, "y": y, "t_ct": t_ct, "y_ct": y_ct,
            "y_ct_n": y_ct_n, "rms": rms, "rating": rating,
        }

    # --------------------------------------------------------------- formatting

    @staticmethod
    def _f(v: float, d: int = 4) -> str:
        """Fixed-decimal format with '-0.0000' normalised to '0.0000'."""
        if v is None or not math.isfinite(v):
            return "∞" if v is not None and v > 0 else ("−∞" if v is not None else "—")
        s = f"{v:.{d}f}"
        return s[1:] if s.startswith("-") and float(s) == 0 else s

    def _equations(self) -> Dict[str, str]:
        r = self._r
        h, T, z, method = r["h"], r["T"], r["z_d"], r["method"]
        f = self._f
        m = self.METHODS[method]

        if method == "forward_euler":
            diff_sym = r"y[n+1] = \Big(1-\tfrac{T}{\tau}\Big)\,y[n] + \tfrac{T}{\tau}\,x[n]"
            diff_num = rf"y[n+1] = {f(1 - h)}\,y[n] + {f(h)}\,x[n]"
        elif method == "backward_euler":
            diff_sym = r"y[n] = \dfrac{\tau}{\tau+T}\,y[n-1] + \dfrac{T}{\tau+T}\,x[n]"
            diff_num = rf"y[n] = {f(1 / (1 + h))}\,y[n-1] + {f(h / (1 + h))}\,x[n]"
        elif method == "trapezoidal":
            diff_sym = (r"y[n] = \dfrac{2\tau-T}{2\tau+T}\,y[n-1] + "
                        r"\dfrac{T}{2\tau+T}\,\big(x[n]+x[n-1]\big)")
            diff_num = rf"y[n] = {f((2 - h) / (2 + h))}\,y[n-1] + {f(h / (2 + h))}\,\big(x[n]+x[n-1]\big)"
        else:
            diff_sym = r"y[n+1] = e^{-T/\tau}\,y[n] + \big(1-e^{-T/\tau}\big)\,x[n]"
            diff_num = rf"y[n+1] = {f(math.exp(-h))}\,y[n] + {f(1 - math.exp(-h))}\,x[n]"

        s_eq = r["s_eq"]
        if s_eq["kind"] == "deadbeat":
            inverse = rf"z = 0 \;\Rightarrow\; s_{{eq}} = \tfrac{{\ln z}}{{T}} \to -\infty"
        elif s_eq["kind"] == "pair":
            inverse = (rf"s_{{eq}} = \dfrac{{\ln|z| \pm j\pi}}{{T}} = {f(s_eq['re'])} \pm j\,{f(s_eq['im'])}"
                       rf"\quad (s_p = {f(r['s_p'])})")
        else:
            inverse = rf"s_{{eq}} = \dfrac{{\ln z}}{{T}} = {f(s_eq['re'])}\quad (s_p = {f(r['s_p'])})"

        return {
            "ct_ode": r"\tau\,\dot y(t) + y(t) = x(t),\qquad y(0) = 0 \;\text{(at rest)}",
            "ct_tf": r"H(s) = \dfrac{1}{\tau s + 1},\qquad s_p = -\dfrac{1}{\tau}",
            "params": rf"\tau = 1\,\text{{s}},\;\; T = {f(T, 2)}\,\text{{s}}",
            "input": r"x(t) = u(t),\;\; x[n] = 1\;(n \ge 0)",
            "derivative": m["derivative"],
            "substitution": m["substitution"],
            "pole_map": m["pole_map"],
            "pole_map_num": rf"z_d = {f(z)}",
            "exact_map": rf"z_{{exact}} = e^{{s_p T}} = e^{{{f(-h, 2)}}} = {f(r['z_exact'])}",
            "diff_sym": diff_sym,
            "diff_num": diff_num,
            "ic": r"y[0] = y(0) = 0",
            "dt_sym": r"y[n] = 1 - z_d^{\,n}",
            "dt_closed": rf"y[n] = 1 - ({f(z)})^{{n}}",
            "ct_closed": r"y(t) = 1 - e^{-t/\tau}",
            "inverse_map": m["inverse_map"],
            "inverse_num": inverse,
        }

    # ------------------------------------------------------------------- plots

    def get_plots(self) -> List[Dict[str, Any]]:
        if not self._initialized:
            self.initialize()
        return [self._s_plane_plot(), self._z_plane_plot(), self._response_plot(), self._pole_vs_step_plot()]


    @staticmethod
    def _axis(title: str, rng: List[float], **extra: Any) -> Dict[str, Any]:
        return {"title": title, "range": rng, "autorange": False, "showgrid": True, "zeroline": True, **extra}

    @staticmethod
    def _legend() -> Dict[str, Any]:
        return {"orientation": "h", "x": 0.5, "xanchor": "center", "y": -0.18, "yanchor": "top",
                "font": {"size": 11}}

    def _circle(self, cx: float, cy: float, r: float, n: int = 721, reverse: bool = False) -> Dict[str, List[float]]:
        th = np.linspace(0, 2 * np.pi, n)
        if reverse:
            th = th[::-1]
        return {"x": (cx + r * np.cos(th)).tolist(), "y": (cy + r * np.sin(th)).tolist()}

    def _s_plane_plot(self) -> Dict[str, Any]:
        r = self._r
        T, method = r["T"], r["method"]
        (x0, x1), (y0, y1) = self.S_VIEW["x"], self.S_VIEW["y"]
        c = self.COLORS
        traces: List[Dict[str, Any]] = []
        region_name = "Maps inside |z| < 1"

        if method == "forward_euler":
            circ = self._circle(-1 / T, 0, 1 / T, n=2001)
            traces.append({"x": circ["x"], "y": circ["y"], "type": "scatter", "mode": "lines", "fill": "toself",
                           "fillcolor": c["fill_stable"], "line": {"color": c["image"], "width": 2, "dash": "dash"},
                           "name": f"{region_name}: |s + 1/T| < 1/T", "hoverinfo": "skip"})
        elif method == "backward_euler":
            # View rectangle with the disk |s - 1/T| < 1/T cut out (slit polygon, opposite orientation).
            hole = self._circle(1 / T, 0, 1 / T, n=2001, reverse=True)
            xs = [x0, x1, x1, x0, x0, 0.0] + hole["x"] + [0.0, x0]
            ys = [y0, y0, y1, y1, y0, 0.0] + hole["y"] + [0.0, y0]
            traces.append({"x": xs, "y": ys, "type": "scatter", "mode": "lines", "fill": "toself",
                           "fillcolor": c["fill_stable"], "line": {"width": 0, "color": "rgba(0,0,0,0)"},
                           "name": f"{region_name}: |s − 1/T| > 1/T", "hoverinfo": "skip"})
            circ = self._circle(1 / T, 0, 1 / T, n=2001)
            traces.append({"x": circ["x"], "y": circ["y"], "type": "scatter", "mode": "lines",
                           "line": {"color": c["image"], "width": 2, "dash": "dash"},
                           "name": "Boundary |s − 1/T| = 1/T", "hoverinfo": "skip"})
        else:
            traces.append({"x": [x0, 0, 0, x0, x0], "y": [y0, y0, y1, y1, y0], "type": "scatter", "mode": "lines",
                           "fill": "toself", "fillcolor": c["fill_stable"], "line": {"width": 0},
                           "name": f"{region_name}: Re s < 0", "hoverinfo": "skip"})
            if method == "exact_zoh" and math.pi / T < y1:
                w = math.pi / T
                traces.append({"x": [x0, x1, None, x0, x1], "y": [w, w, None, -w, -w], "type": "scatter",
                               "mode": "lines", "line": {"color": c["axis"], "width": 1.5, "dash": "dot"},
                               "name": f"Aliasing strip |ω| = π/T = {self._f(w, 2)}", "hoverinfo": "skip"})

        traces.append({"x": [0, 0], "y": [y0, y1], "type": "scatter", "mode": "lines",
                       "line": {"color": c["boundary"], "width": 2.5}, "name": "jω axis", "hoverinfo": "skip"})

        traces.append({"x": [r["s_p"]], "y": [0], "type": "scatter", "mode": "markers",
                       "marker": {"symbol": "x", "size": 15, "color": c["ct"], "line": {"width": 2, "color": c["ct"]}},
                       "name": f"CT pole s_p = {self._f(r['s_p'])}",
                       "hovertemplate": f"CT pole<br>s_p = −1/τ = {self._f(r['s_p'])}<extra></extra>"})

        annotations = []
        s_eq = r["s_eq"]
        color = self.COLORS[r["stability"]]
        if method != "exact_zoh":
            label = "s_eq = ln(z_d)/T"
            if s_eq["kind"] == "deadbeat" or s_eq["re"] < x0:
                txt = "s_eq → −∞ (z_d = 0)" if s_eq["kind"] == "deadbeat" else f"s_eq = {self._f(s_eq['re'])} (off-scale)"
                ys = [s_eq["im"], -s_eq["im"]] if s_eq["im"] else [0.0]
                traces.append({"x": [x0] * len(ys), "y": ys, "type": "scatter", "mode": "markers",
                               "marker": {"symbol": "triangle-left", "size": 13, "color": color},
                               "cliponaxis": False, "name": f"{label} (off-scale)",
                               "hovertemplate": f"{txt}<extra></extra>"})
                annotations.append({"x": x0, "y": ys[0], "xref": "x", "yref": "y", "text": txt, "showarrow": False,
                                    "xanchor": "left", "yanchor": "bottom", "xshift": 10, "yshift": 4,
                                    "font": {"size": 11, "color": color}})
            else:
                ys = [s_eq["im"], -s_eq["im"]] if s_eq["im"] else [0.0]
                pair = f" ± j{self._f(s_eq['im'])}" if s_eq["im"] else ""
                traces.append({"x": [s_eq["re"]] * len(ys), "y": ys, "type": "scatter", "mode": "markers",
                               "marker": {"symbol": "x-open", "size": 13, "color": color,
                                          "line": {"width": 2, "color": color}},
                               "name": f"{label} = {self._f(s_eq['re'])}{pair}",
                               "hovertemplate": (f"Equivalent CT pole of the DT approximation<br>"
                                                 f"s_eq = {self._f(s_eq['re'])}{pair}<extra></extra>")})

        return {
            "id": "s_plane",
            "title": "s-plane: CT pole and the region mapped inside |z| < 1",
            "data": traces,
            "layout": {
                "xaxis": self._axis("Re(s)  [1/s]", self.S_VIEW["x"], constrain="domain"),
                "yaxis": self._axis("Im(s)  [rad/s]", self.S_VIEW["y"], scaleanchor="x", scaleratio=1,
                                    constrain="domain"),
                "annotations": annotations,
                "legend": self._legend(),
                "margin": {"l": 60, "r": 20, "t": 20, "b": 60},
                "uirevision": "s_plane",
            },
        }

    def _z_plane_plot(self) -> Dict[str, Any]:
        r = self._r
        method, z, z_ex, h = r["method"], r["z_d"], r["z_exact"], r["h"]
        c = self.COLORS
        color = self.COLORS[r["stability"]]
        traces: List[Dict[str, Any]] = []

        unit = self._circle(0, 0, 1)
        traces.append({"x": unit["x"], "y": unit["y"], "type": "scatter", "mode": "lines", "fill": "toself",
                       "fillcolor": c["fill_stable"], "line": {"color": c["boundary"], "width": 2.5},
                       "name": "Unit circle |z| = 1", "hoverinfo": "skip"})

        (x0, x1), (y0, y1) = self.Z_VIEW["x"], self.Z_VIEW["y"]
        if method == "forward_euler":
            traces.append({"x": [x0, 1, 1, x0, x0], "y": [y0, y0, y1, y1, y0], "type": "scatter", "mode": "lines",
                           "fill": "toself", "fillcolor": c["fill_image"], "line": {"width": 0},
                           "name": "Image of Re s < 0: Re z < 1", "hoverinfo": "skip"})
            traces.append({"x": [1, 1], "y": [y0, y1], "type": "scatter", "mode": "lines",
                           "line": {"color": c["image"], "width": 2, "dash": "dash"},
                           "name": "Image of jω axis: Re z = 1", "hoverinfo": "skip"})
        elif method == "backward_euler":
            img = self._circle(0.5, 0, 0.5)
            traces.append({"x": img["x"], "y": img["y"], "type": "scatter", "mode": "lines", "fill": "toself",
                           "fillcolor": c["fill_image"], "line": {"color": c["image"], "width": 2, "dash": "dash"},
                           "name": "Image of jω axis: |z − ½| = ½", "hoverinfo": "skip"})
        else:
            traces.append({"x": [None], "y": [None], "type": "scatter", "mode": "lines",
                           "line": {"color": c["boundary"], "width": 2.5},
                           "name": "Image of jω axis = unit circle", "hoverinfo": "skip"})

        zeros = {"backward_euler": 0.0, "trapezoidal": -1.0}.get(method)
        if zeros is not None:
            traces.append({"x": [zeros], "y": [0], "type": "scatter", "mode": "markers",
                           "marker": {"symbol": "circle-open", "size": 12, "color": color, "line": {"width": 2}},
                           "name": f"DT zero z = {self._f(zeros, 0)}",
                           "hovertemplate": f"Zero of H(z) ({self.METHODS[method]['name']})<br>z = "
                                            f"{self._f(zeros, 0)}<extra></extra>"})

        traces.append({"x": [z_ex], "y": [0], "type": "scatter", "mode": "markers",
                       "marker": {"symbol": "diamond-open", "size": 14, "color": c["ct"],
                                  "line": {"width": 2.5, "color": c["ct"]}},
                       "name": f"Exact e^(s_p T) = {self._f(z_ex)}",
                       "hovertemplate": f"Exact sampled pole<br>z = e^(s_p T) = e^({self._f(-h, 2)}) = "
                                        f"{self._f(z_ex)}<extra></extra>"})
        if method != "exact_zoh":
            traces.append({"x": [z], "y": [0], "type": "scatter", "mode": "markers",
                           "marker": {"symbol": "x", "size": 15, "color": color, "line": {"width": 2, "color": color}},
                           "cliponaxis": False,
                           "name": f"{self.METHODS[method]['name']} z_d = {self._f(z)}",
                           "hovertemplate": (f"{self.METHODS[method]['name']} pole<br>z_d = {self._f(z)}"
                                             f"<br>|z_d| = {self._f(abs(z))}<br>error vs exact = "
                                             f"{self._f(z - z_ex)}<extra></extra>")})

        return {
            "id": "z_plane",
            "title": "z-plane: method pole vs exact pole e^(sT)",
            "data": traces,
            "layout": {
                "xaxis": self._axis("Re(z)", self.Z_VIEW["x"], constrain="domain"),
                "yaxis": self._axis("Im(z)", self.Z_VIEW["y"], scaleanchor="x", scaleratio=1, constrain="domain"),
                "legend": self._legend(),
                "margin": {"l": 55, "r": 20, "t": 20, "b": 60},
                "uirevision": "z_plane",
            },
        }

    def _response_plot(self) -> Dict[str, Any]:
        r = self._r
        c = self.COLORS
        color = self.COLORS[r["stability"]]
        t_n, y = r["t_n"], r["y"]
        name = self.METHODS[r["method"]]["name"]

        base_lo, base_hi = 0.0, 1.0
        bound = 3.0
        finite = np.isfinite(y)
        inside = finite & (np.abs(y) <= bound)
        lo = min(base_lo, float(np.min(y[inside])) if inside.any() else base_lo)
        hi = max(base_hi, float(np.max(y[inside])) if inside.any() else base_hi)
        clipped = ~inside
        if clipped.any():
            lo = min(lo, -bound) if np.any(~finite | (y < -bound)) else lo
            hi = max(hi, bound) if np.any(~finite | (y > bound)) else hi
        pad = 0.08 * (hi - lo if hi > lo else 1.0)
        y_lo, y_hi = lo - pad, hi + pad
        y_draw = np.where(inside, y, np.where(np.nan_to_num(y, nan=bound, posinf=bound, neginf=-bound) > 0,
                                              y_hi, y_lo))

        traces: List[Dict[str, Any]] = [
            {"x": r["t_ct"].tolist(), "y": r["y_ct"].tolist(), "type": "scatter", "mode": "lines",
             "line": {"color": c["ct"], "width": 2.5}, "name": "CT step response y(t)",
             "hovertemplate": "t = %{x:.3f} s<br>y(t) = %{y:.4f}<extra>CT</extra>"},
        ]
        traces.append({"x": [0, float(t_n[-1])], "y": [1, 1], "type": "scatter", "mode": "lines",
                       "line": {"color": c["reference"], "width": 1.5, "dash": "dash"},
                       "name": "Steady state y = 1", "hoverinfo": "skip"})


        stems = len(t_n) <= self.STEM_LIMIT
        if stems:
            sx: List[Any] = []
            sy: List[Any] = []
            for tk, yk in zip(t_n.tolist(), y_draw.tolist()):
                sx += [tk, tk, None]
                sy += [0.0, yk, None]
            traces.append({"x": sx, "y": sy, "type": "scatter", "mode": "lines",
                           "line": {"color": color, "width": 1.5}, "showlegend": False, "hoverinfo": "skip"})
        hover = [f"n = {k}<br>n·T = {tk:.3f} s<br>y[n] = {self._f(yk) if np.isfinite(yk) else 'overflow'}"
                 f"<br>y(nT) = {self._f(yc)}" for k, tk, yk, yc in zip(r["n"].tolist(), t_n.tolist(), y.tolist(),
                                                                       r["y_ct_n"].tolist())]
        traces.append({"x": t_n[inside].tolist(), "y": y[inside].tolist(), "type": "scatter", "mode": "markers",
                       "marker": {"color": color, "size": 8 if stems else 5}, "name": f"{name}: y[n]",
                       "text": [hv for hv, ok in zip(hover, inside) if ok],
                       "hovertemplate": "%{text}<extra></extra>"})
        annotations = []
        if clipped.any():
            up = clipped & (np.nan_to_num(y, nan=bound, posinf=bound, neginf=-bound) > 0)
            for mask, sym, yy in ((up, "triangle-up", y_hi), (clipped & ~up, "triangle-down", y_lo)):
                if mask.any():
                    traces.append({"x": t_n[mask].tolist(), "y": [yy] * int(mask.sum()), "type": "scatter",
                                   "mode": "markers", "cliponaxis": False,
                                   "marker": {"symbol": sym, "size": 10, "color": color},
                                   "name": "off-scale y[n]", "showlegend": bool(sym == "triangle-up" or not up.any()),
                                   "text": [hv for hv, ok in zip(hover, mask) if ok],
                                   "hovertemplate": "%{text}<extra>off-scale</extra>"})
            annotations.append({"x": 1.0, "y": 1.0, "xref": "paper", "yref": "paper", "xanchor": "right",
                                "yanchor": "bottom", "yshift": 10, "showarrow": False,
                                "font": {"size": 11, "color": color},
                                "text": f"|y[n]| grows like |z_d|ⁿ = {self._f(abs(r['z_d']), 2)}ⁿ — "
                                        f"▲▼ mark off-scale samples"})

        return {
            "id": "response",
            "title": "Step response of the difference equation: y[n] vs y(nT)",
            "data": traces,
            "layout": {
                "xaxis": self._axis("t = nT  [s]", [0, float(t_n[-1])]),
                "yaxis": self._axis("y", [y_lo, y_hi]),
                "annotations": annotations,
                "legend": self._legend(),
                "margin": {"l": 60, "r": 20, "t": 38, "b": 60},
                "uirevision": "response",
            },
        }

    def _pole_vs_step_plot(self) -> Dict[str, Any]:
        r = self._r
        c = self.COLORS
        method = r["method"]
        hg = self.H_GRID
        z_m = np.real(self._s_to_z(-1.0, hg, method)).astype(float)
        z_e = np.exp(-hg)
        y_lo = min(-1.25, float(np.min(z_m)) - 0.15)
        y_hi = 1.15
        name = self.METHODS[method]["name"]
        color = self.COLORS[r["stability"]]
        traces: List[Dict[str, Any]] = [
            {"x": [0, 3.05, 3.05, 0, 0], "y": [-1, -1, 1, 1, -1], "type": "scatter", "mode": "lines",
             "fill": "toself", "fillcolor": c["fill_stable"], "line": {"width": 0},
             "name": "Stable band −1 < z < 1", "hoverinfo": "skip"},
            {"x": [0, 3.05, None, 0, 3.05], "y": [1, 1, None, -1, -1], "type": "scatter", "mode": "lines",
             "line": {"color": c["boundary"], "width": 1.5, "dash": "dash"}, "name": "|z| = 1",
             "hoverinfo": "skip"},
            {"x": hg.tolist(), "y": z_e.tolist(), "type": "scatter", "mode": "lines",
             "line": {"color": c["ct"], "width": 2, "dash": "dash"}, "name": "Exact e^(−T/τ)",
             "hovertemplate": "T/τ = %{x:.2f}<br>e^(−T/τ) = %{y:.4f}<extra></extra>"},
        ]
        if method != "exact_zoh":
            traces.append({"x": hg.tolist(), "y": z_m.tolist(), "type": "scatter", "mode": "lines",
                           "line": {"color": c["stable"] if method != "forward_euler" else c["image"], "width": 2.5},
                           "name": f"{name} z_d(T/τ)",
                           "hovertemplate": "T/τ = %{x:.2f}<br>z_d = %{y:.4f}<extra></extra>"})
        if method == "forward_euler":
            traces.append({"x": [2, 2], "y": [y_lo, y_hi], "type": "scatter", "mode": "lines",
                           "line": {"color": c["unstable"], "width": 1.5, "dash": "dot"},
                           "name": "FE limit T/τ = 2", "hoverinfo": "skip"})
        traces.append({"x": [r["h"]], "y": [r["z_exact"]], "type": "scatter", "mode": "markers", "cliponaxis": False,
                       "marker": {"symbol": "diamond-open", "size": 12, "color": c["ct"], "line": {"width": 2.5}},
                       "name": "Exact (current T/τ)",
                       "hovertemplate": f"T/τ = {self._f(r['h'], 2)}<br>e^(−T/τ) = {self._f(r['z_exact'])}"
                                        f"<extra></extra>"})
        if method != "exact_zoh":
            traces.append({"x": [r["h"]], "y": [r["z_d"]], "type": "scatter", "mode": "markers",
                           "cliponaxis": False,
                           "marker": {"symbol": "circle", "size": 11, "color": color,
                                      "line": {"width": 1.5, "color": "#ffffff"}},
                           "name": f"{name} (current T/τ)",
                           "hovertemplate": f"T/τ = {self._f(r['h'], 2)}<br>z_d = {self._f(r['z_d'])}"
                                            f"<extra></extra>"})
        return {
            "id": "pole_vs_step",
            "title": "DT pole vs step size T/τ",
            "data": traces,
            "layout": {
                "xaxis": self._axis("T/τ", [0, 3.05]),
                "yaxis": self._axis("DT pole z (real)", [y_lo, y_hi]),
                "legend": self._legend(),
                "margin": {"l": 60, "r": 20, "t": 20, "b": 60},
                "uirevision": "pole_vs_step",
            },
        }

    # ------------------------------------------------------------------- state

    def get_state(self) -> Dict[str, Any]:
        if not self._initialized:
            self.initialize()
        self._compute()
        r = self._r
        method_info = self.METHODS[r["method"]]
        s_eq = r["s_eq"]
        samples = [{"n": int(k), "t": float(r["t_n"][k]), "y_dt": float(r["y"][k]),
                    "y_ct": float(r["y_ct_n"][k]), "error": float(r["y"][k] - r["y_ct_n"][k])}
                   for k in range(min(6, len(r["n"])))]
        scenario_key = self.parameters["guided_scenario"]
        guided = None
        if scenario_key != "none":
            sc = self.GUIDED_SCENARIOS[int(scenario_key)]
            guided = {"index": int(scenario_key), "title": sc["title"], "message": sc["message"]}

        state = super().get_state()
        state["metadata"] = {
            "simulation_type": "ct_dt_poles",
            "hub_slots": self.HUB_SLOTS,
            "hub_domain": self.HUB_DOMAIN,
            "hub_dimensions": self.HUB_DIMENSIONS,
            "sticky_controls": True,
            "system_info": {
                "method": r["method"],
                "method_name": method_info["name"],
                "t_tau_ratio": r["h"],
                "T": r["T"],
                "tau": r["tau"],
                "s_pole": r["s_p"],
                "z_method": r["z_d"],
                "z_exact": r["z_exact"],
                "pole_error": r["z_d"] - r["z_exact"],
                "z_magnitude": abs(r["z_d"]),
                "s_equivalent": s_eq,
                "stability": r["stability"],
                "is_stable": r["stability"] == "stable",
                "mode_behavior": self._mode_text(r["z_d"]),
                "rms_error": r["rms"],
                "performance_rating": r["rating"],
            },
            "method_info": method_info,
            "equations": self._equations(),
            "samples": samples,
            "guided": guided,
        }
        return state
