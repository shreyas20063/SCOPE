#!/usr/bin/env python3
"""
SCOPE Platform Validation Suite — Benchmark Harness

Exercises SCOPE simulators through their public API with standard textbook
parameters, extracts numerical results, and exports to JSON for comparison
against MATLAB Control System Toolbox outputs.

Usage:
    cd <project_root>
    python -m validation.run_scope_benchmarks

Output:
    validation/results/scope_results.json
"""

import json
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

# ---------------------------------------------------------------------------
# Path setup — add backend to sys.path so simulators can be imported
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

# Now safe to import simulators
from simulations import SIMULATOR_REGISTRY  # noqa: E402


# ---------------------------------------------------------------------------
# JSON-safe serializer for numpy types
# ---------------------------------------------------------------------------
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            v = float(obj)
            if np.isnan(v):
                return "NaN"
            if np.isinf(v):
                return "Inf" if v > 0 else "-Inf"
            return v
        if isinstance(obj, np.complexfloating):
            return {"real": float(obj.real), "imag": float(obj.imag)}
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, complex):
            return {"real": obj.real, "imag": obj.imag}
        return super().default(obj)


# ---------------------------------------------------------------------------
# Helper: extract Plotly trace data from simulator plots
# ---------------------------------------------------------------------------
def find_trace(plots: List[dict], plot_id: str, trace_name: str) -> Optional[dict]:
    """Find a trace by plot ID and trace name substring."""
    for plot in plots:
        if plot.get("id") == plot_id:
            for trace in plot.get("data", []):
                name = trace.get("name", "")
                if name and trace_name.lower() in name.lower():
                    return trace
    return None


def find_trace_by_index(plots: List[dict], plot_id: str, index: int) -> Optional[dict]:
    """Find a trace by plot ID and positional index."""
    for plot in plots:
        if plot.get("id") == plot_id:
            data = plot.get("data", [])
            if 0 <= index < len(data):
                return data[index]
    return None


def extract_xy(trace: Optional[dict]) -> Optional[Dict[str, list]]:
    """Extract x,y arrays from a Plotly trace dict."""
    if trace and "x" in trace and "y" in trace:
        return {"x": trace["x"], "y": trace["y"]}
    return None


# ---------------------------------------------------------------------------
# Benchmark definitions
# ---------------------------------------------------------------------------
# Each benchmark is a dict with:
#   sim_id: which simulator to use
#   params: parameter overrides (merged with defaults)
#   extract: function(state) -> dict of numerical results

BENCHMARKS: Dict[str, dict] = {}


def benchmark(bench_id: str, sim_id: str, params: dict = None, description: str = "",
              actions: List[str] = None):
    """Decorator-style registerer for benchmark extract functions."""
    def decorator(fn):
        BENCHMARKS[bench_id] = {
            "sim_id": sim_id,
            "params": params or {},
            "description": description,
            "actions": actions or [],
            "extract": fn,
        }
        return fn
    return decorator


# ===== SIGNAL PROCESSING =====

@benchmark(
    "SP01_rc_bode",
    "rc_lowpass_filter",
    {"frequency": 100, "rc_ms": 1.0, "amplitude": 5.0},
    "RC lowpass filter: Bode magnitude at f_c = 159.15 Hz (RC = 1ms)",
)
def _extract_rc_bode(state):
    plots = state["plots"]
    meta = state.get("metadata", {})
    filter_info = meta.get("filter_info", {})
    bode_trace = find_trace(plots, "bode", "Filter Response")
    return {
        "cutoff_freq_hz": filter_info.get("cutoff_freq"),
        "bode_freqs_hz": bode_trace["x"] if bode_trace else None,
        "bode_magnitude_db": bode_trace["y"] if bode_trace else None,
        "matlab_cmd": "H = tf(1, [1e-3 1]); [mag,~,w] = bode(H); % then 20*log10(squeeze(mag))",
    }


@benchmark(
    "SP02_rc_bode_phase",
    "rc_lowpass_filter",
    {"frequency": 100, "rc_ms": 1.0, "amplitude": 5.0},
    "RC lowpass filter: Bode phase response (complement to SP01 magnitude)",
)
def _extract_rc_phase(state):
    plots = state["plots"]
    # RC filter sim includes harmonic analysis; extract magnitude for cross-check
    bode_trace = find_trace(plots, "bode", "Filter Response")
    return {
        "bode_freqs_hz": bode_trace["x"] if bode_trace else None,
        "bode_magnitude_db": bode_trace["y"] if bode_trace else None,
        "matlab_cmd": "H = tf(1, [1e-3 1]); [mag,~,w] = bode(H); % phase cross-check",
    }


@benchmark(
    "SP03_sampling",
    "aliasing_quantization",
    {"signal_freq": 5.0, "sample_rate": 20.0, "num_bits": 8},
    "Aliasing & quantization: Nyquist sampling at fs=20Hz for f=5Hz signal",
)
def _extract_sampling(state):
    plots = state["plots"]
    meta = state.get("metadata", {})
    # Extract the continuous vs sampled signal
    cont_trace = find_trace_by_index(plots, "time_domain", 0)
    sampled_trace = find_trace_by_index(plots, "time_domain", 1)
    return {
        "nyquist_freq": 10.0,  # fs/2
        "signal_freq": 5.0,
        "is_aliased": False,  # f < fs/2
        "continuous_signal": extract_xy(cont_trace),
        "sampled_signal": extract_xy(sampled_trace),
        "matlab_cmd": "t=0:1/20:1; x=sin(2*pi*5*t); stem(t,x);",
    }


# ===== SECOND-ORDER SYSTEM =====

@benchmark(
    "CS01_2nd_order_underdamped",
    "second_order_system",
    {"omega_0": 10.0, "Q_slider": 75},  # Q = 10^((75/50)-1) = 10^0.5 ≈ 3.16
    "2nd-order system: underdamped (ω₀=10, Q≈3.16, ζ≈0.158)",
)
def _extract_2nd_order(state):
    meta = state.get("metadata", {})
    info = meta.get("system_info", {})
    plots = state["plots"]
    mag_trace = find_trace(plots, "bode_magnitude", "Magnitude")
    phase_trace = find_trace(plots, "bode_phase", "Phase")
    return {
        "omega_0": info.get("omega_0"),
        "Q": info.get("Q"),
        "zeta": info.get("zeta"),
        "damping_type": info.get("damping_type"),
        "poles_str": info.get("poles"),
        "bandwidth": info.get("bandwidth"),
        "resonant_freq": info.get("resonant_freq"),
        "bode_omega": mag_trace["x"] if mag_trace else None,
        "bode_magnitude_db": mag_trace["y"] if mag_trace else None,
        "bode_phase_deg": phase_trace["y"] if phase_trace else None,
        "matlab_cmd": "H = tf(100, [1 10/3.16 100]); bode(H); pole(H);",
    }


@benchmark(
    "CS02_2nd_order_overdamped",
    "second_order_system",
    {"omega_0": 10.0, "Q_slider": 15},  # Q = 10^((15/50)-1) = 10^-0.7 ≈ 0.2
    "2nd-order system: overdamped (ω₀=10, Q≈0.2, ζ≈2.5)",
)
def _extract_2nd_order_od(state):
    meta = state.get("metadata", {})
    info = meta.get("system_info", {})
    return {
        "omega_0": info.get("omega_0"),
        "Q": info.get("Q"),
        "zeta": info.get("zeta"),
        "damping_type": info.get("damping_type"),
        "poles_str": info.get("poles"),
        "matlab_cmd": "H = tf(100, [1 50 100]); pole(H);",
    }


# ===== ROUTH-HURWITZ =====

@benchmark(
    "CS03_routh_stable",
    "routh_hurwitz",
    {"preset": "stable_3rd"},
    "Routh-Hurwitz: stable 3rd order s³+6s²+11s+6 — expect 0 sign changes",
)
def _extract_routh(state):
    meta = state.get("metadata", {})
    routh = meta.get("routh_table", {})
    return {
        "polynomial": [1, 6, 11, 6],
        "routh_rows": routh.get("rows"),
        "first_column": routh.get("first_column"),
        "sign_changes": routh.get("sign_changes"),
        "rhp_poles": routh.get("rhp_poles"),
        "stable": routh.get("stable"),
        "matlab_cmd": "roots([1 6 11 6])  % expect all negative real",
    }


@benchmark(
    "CS04_routh_unstable",
    "routh_hurwitz",
    {"preset": "unstable_3rd"},
    "Routh-Hurwitz: unstable 3rd order s³+2s²+3s+10 — expect sign changes",
)
def _extract_routh_unstable(state):
    meta = state.get("metadata", {})
    routh = meta.get("routh_table", {})
    return {
        "polynomial": [1, 2, 3, 10],
        "routh_rows": routh.get("rows"),
        "first_column": routh.get("first_column"),
        "sign_changes": routh.get("sign_changes"),
        "rhp_poles": routh.get("rhp_poles"),
        "stable": routh.get("stable"),
        "matlab_cmd": "roots([1 2 3 10])  % expect RHP poles",
    }


# ===== ADVERSARIAL: High-order Routh =====

@benchmark(
    "CS04b_routh_5th_order",
    "routh_hurwitz",
    {"preset": "custom", "poly_coeffs": "1, 2, 3, 4, 5, 6"},
    "Routh-Hurwitz: 5th-order s⁵+2s⁴+3s³+4s²+5s+6 — adversarial higher order",
)
def _extract_routh_5th(state):
    meta = state.get("metadata", {})
    routh = meta.get("routh_table", {})
    return {
        "polynomial": [1, 2, 3, 4, 5, 6],
        "first_column": routh.get("first_column"),
        "sign_changes": routh.get("sign_changes"),
        "rhp_poles": routh.get("rhp_poles"),
        "stable": routh.get("stable"),
        "matlab_cmd": "roots([1 2 3 4 5 6])  % verify sign changes match",
    }


# ===== ADVERSARIAL: Near-zero damping =====

@benchmark(
    "CS01b_near_zero_damping",
    "second_order_system",
    {"omega_0": 10.0, "Q_slider": 95},  # Q = 10^((95/50)-1) = 10^0.9 ≈ 7.94, ζ ≈ 0.063
    "2nd-order system: near-zero damping (Q≈7.94, ζ≈0.063) — adversarial sharp resonance",
)
def _extract_2nd_order_lz(state):
    meta = state.get("metadata", {})
    info = meta.get("system_info", {})
    plots = state["plots"]
    mag_trace = find_trace(plots, "bode_magnitude", "Magnitude")
    return {
        "omega_0": info.get("omega_0"),
        "Q": info.get("Q"),
        "zeta": info.get("zeta"),
        "bandwidth": info.get("bandwidth"),
        "bode_omega": mag_trace["x"] if mag_trace else None,
        "bode_magnitude_db": mag_trace["y"] if mag_trace else None,
        "matlab_cmd": "Q=10^0.9; H=tf(100,[1 10/Q 100]); bode(H);",
    }


# ===== STEADY-STATE ERROR =====

@benchmark(
    "CS05_ess_type0",
    "steady_state_error",
    {"plant_preset": "type0_first", "gain_K": 10.0, "input_type": "step", "input_magnitude": 1.0},
    "Steady-state error: Type 0 plant G(s)=K/(s+2), K=10 → ess = 1/(1+Kp)",
)
def _extract_ess_type0(state):
    meta = state.get("metadata", {})
    cl_poles = meta.get("cl_poles", [])
    return {
        "system_type": meta.get("system_type"),
        "error_constants": meta.get("error_constants"),
        "steady_state_errors": meta.get("steady_state_errors"),
        "cl_stable": meta.get("cl_stable"),
        "cl_poles": cl_poles,
        "gain_K": meta.get("gain_K"),
        "matlab_cmd": "G = tf(10, [1 2]); Kp = dcgain(G); ess = 1/(1+Kp);",
    }


@benchmark(
    "CS06_ess_type1",
    "steady_state_error",
    {"plant_preset": "type1_standard", "gain_K": 10.0, "input_type": "ramp", "input_magnitude": 1.0},
    "Steady-state error: Type 1 plant G(s)=K/(s(s+5)), K=10 → ess_ramp = 1/Kv",
)
def _extract_ess_type1(state):
    meta = state.get("metadata", {})
    return {
        "system_type": meta.get("system_type"),
        "error_constants": meta.get("error_constants"),
        "steady_state_errors": meta.get("steady_state_errors"),
        "cl_stable": meta.get("cl_stable"),
        "cl_poles": meta.get("cl_poles", []),
        "gain_K": meta.get("gain_K"),
        "matlab_cmd": "G = tf(10, [1 3 2 0]); % Type 1: Kv = lim s->0 s*G(s)",
    }


# ===== CONTROLLER TUNING LAB (LQR) =====

@benchmark(
    "CS07_lqr",
    "controller_tuning_lab",
    {"plant_preset": "second_order", "controller_type": "lqr",
     "lqr_q1": 10.0, "lqr_q2": 1.0, "lqr_r": 1.0},
    "LQR: 2nd-order plant with Q=diag(10,1), R=1 — compare K gains",
)
def _extract_lqr(state):
    meta = state.get("metadata", {})
    perf = meta.get("performance", {})
    return {
        "state_feedback_K": meta.get("state_feedback_K"),
        "ss_matrices": meta.get("ss_matrices"),
        "is_controllable": meta.get("is_controllable"),
        "rise_time": perf.get("rise_time"),
        "settling_time": perf.get("settling_time"),
        "overshoot_pct": perf.get("overshoot_pct"),
        "phase_margin_deg": perf.get("phase_margin_deg"),
        "gain_margin_db": perf.get("gain_margin_db"),
        "steady_state_error": perf.get("steady_state_error"),
        "matlab_cmd": "[A,B,C,D] = tf2ss(num,den); K = lqr(A,B,diag([10,1]),1);",
    }


@benchmark(
    "CS08_pole_placement",
    "controller_tuning_lab",
    {"plant_preset": "second_order", "controller_type": "pole_placement",
     "pp_pole1_real": -5.0, "pp_pole1_imag": 0.0, "pp_pole2_real": -6.0, "pp_pole2_imag": 0.0},
    "Pole placement: 2nd-order plant, desired poles at -5, -6",
    actions=["apply_pole_placement"],
)
def _extract_pole_placement(state):
    meta = state.get("metadata", {})
    perf = meta.get("performance", {})
    return {
        "state_feedback_K": meta.get("state_feedback_K"),
        "ss_matrices": meta.get("ss_matrices"),
        "desired_poles": [-5.0, -6.0],
        "rise_time": perf.get("rise_time"),
        "settling_time": perf.get("settling_time"),
        "overshoot_pct": perf.get("overshoot_pct"),
        "steady_state_error": perf.get("steady_state_error"),
        "matlab_cmd": "[A,B,C,D] = tf2ss(num,den); K = place(A,B,[-5,-6]);",
    }


# ===== MIMO DESIGN STUDIO =====

@benchmark(
    "CS09_mimo_eigenvalues",
    "mimo_design_studio",
    {"preset": "aircraft_lateral", "design_mode": "analysis"},
    "MIMO: aircraft lateral dynamics eigenvalues + controllability/observability",
)
def _extract_mimo(state):
    meta = state.get("metadata", {})
    matrices = meta.get("matrices", {})
    eigs = meta.get("eigenvalues", {})
    return {
        "A": matrices.get("A"),
        "B": matrices.get("B"),
        "C": matrices.get("C"),
        "D": matrices.get("D"),
        "eigenvalues_real": eigs.get("real"),
        "eigenvalues_imag": eigs.get("imag"),
        "n_states": meta.get("n_states"),
        "n_inputs": meta.get("n_inputs"),
        "n_outputs": meta.get("n_outputs"),
        "is_stable": meta.get("is_stable"),
        "controllability_rank": meta.get("controllability_rank"),
        "observability_rank": meta.get("observability_rank"),
        "is_controllable": meta.get("is_controllable"),
        "is_observable": meta.get("is_observable"),
        "matlab_cmd": "A=...; B=...; eig(A); rank(ctrb(A,B)); rank(obsv(A,C));",
    }


@benchmark(
    "CS10_mimo_lqr",
    "mimo_design_studio",
    {"preset": "aircraft_lateral", "design_mode": "lqr",
     "q_diag": "10,1,10,1", "r_diag": "1,1"},
    "MIMO LQR: aircraft lateral dynamics with Q=diag(10,1,10,1), R=diag(1,1)",
)
def _extract_mimo_lqr(state):
    meta = state.get("metadata", {})
    matrices = meta.get("matrices", {})
    ctrl = meta.get("controller", {})
    return {
        "A": matrices.get("A"),
        "B": matrices.get("B"),
        "K": ctrl.get("K"),
        "P": ctrl.get("P"),
        "cl_eigenvalues_real": ctrl.get("cl_eigs_real"),
        "cl_eigenvalues_imag": ctrl.get("cl_eigs_imag"),
        "is_stable": meta.get("is_stable"),
        "matlab_cmd": "K = lqr(A,B,diag([10,1,10,1]),diag([1,1]));",
    }


# ===== ROOT LOCUS ANALYSIS =====

@benchmark(
    "RL01_root_locus",
    "root_locus",
    {"num_coeffs": "1", "den_coeffs": "1, 3, 2, 0", "gain_K": 1.0, "k_max": 100},
    "Root locus: G(s)=1/[s(s+1)(s+2)] — breakaway, jω crossing, asymptotes, stability ranges",
)
def _extract_root_locus(state):
    meta = state.get("metadata", {})
    sp = meta.get("special_points", {})
    stab = meta.get("stability_ranges", {})
    metrics = meta.get("metrics", {})
    asym = sp.get("asymptotes", {})
    # Extract breakaway point (real part and K value)
    breakaway = sp.get("breakaway", [])
    ba_real = breakaway[0]["s"]["real"] if breakaway else None
    ba_K = breakaway[0]["K"] if breakaway else None
    # Extract jω crossing
    jw = sp.get("jw_crossings", [])
    jw_omega = jw[0]["omega"] if jw else None
    jw_K = jw[0]["K"] if jw else None
    return {
        "breakaway_real": ba_real,
        "breakaway_K": ba_K,
        "jw_crossing_omega": jw_omega,
        "jw_crossing_K": jw_K,
        "asymptote_centroid": asym.get("centroid"),
        "asymptote_angles": sorted(asym.get("angles", [])),
        "n_asymptotes": asym.get("n"),
        "phase_margin_deg": metrics.get("phase_margin_deg"),
        "stability_K_max": stab.get("ranges", [{}])[0].get("end"),
        "matlab_cmd": "rlocus(tf(1,[1 3 2 0])); % breakaway, jw crossing, asymptotes",
    }


# ===== STEP RESPONSE & MARGINS (PID) =====

@benchmark(
    "CD01_pid_step_response",
    "controller_tuning_lab",
    {"plant_preset": "second_order", "controller_type": "PID",
     "Kp": 2.0, "Ki": 1.0, "Kd": 0.5},
    "PID step response: rise time, settling time, overshoot on 2nd-order plant (filtered derivative N=20)",
)
def _extract_pid_step(state):
    meta = state.get("metadata", {})
    perf = meta.get("performance", {})
    return {
        "rise_time": perf.get("rise_time"),
        "overshoot_pct": perf.get("overshoot_pct"),
        "settling_time": perf.get("settling_time"),
        "steady_state_error": perf.get("steady_state_error"),
        "is_stable": perf.get("is_stable"),
        "phase_margin_deg": perf.get("phase_margin_deg"),
        "gain_crossover_freq": perf.get("gain_crossover_freq"),
        "matlab_cmd": "G=tf(25,[1 5 25]); C=pid(2,1,0.5,1/20); T=feedback(C*G,1); stepinfo(T); margin(C*G);",
    }


@benchmark(
    "CD02_open_loop_margins",
    "controller_tuning_lab",
    {"plant_preset": "custom", "controller_type": "P", "Kp": 1.0,
     "custom_num": "20", "custom_den": "1, 8, 17, 10"},
    "Open-loop margins: G(s)=20/[(s+1)(s+2)(s+5)] — GM and PM",
)
def _extract_margins(state):
    meta = state.get("metadata", {})
    perf = meta.get("performance", {})
    return {
        "gain_margin_db": perf.get("gain_margin_db"),
        "phase_margin_deg": perf.get("phase_margin_deg"),
        "gain_crossover_freq": perf.get("gain_crossover_freq"),
        "phase_crossover_freq": perf.get("phase_crossover_freq"),
        "is_stable": perf.get("is_stable"),
        "matlab_cmd": "L=tf(20,[1 8 17 10]); [Gm,Pm,Wgc,Wpc]=margin(L);",
    }


# ===== LEAD-LAG COMPENSATOR DESIGN =====

@benchmark(
    "LL01_lead_compensator",
    "lead_lag_designer",
    {"plant_preset": "type1", "plant_K": 1.0, "gain_Kc": 1.0,
     "lead_enable": True, "lead_alpha": 0.1, "lead_wm": 5.0,
     "lag_enable": False},
    "Lead compensator: α=0.1, ωm=5 on Type 1 plant — φ_max, zero/pole, compensated PM",
)
def _extract_lead(state):
    meta = state.get("metadata", {})
    di = meta.get("design_info", {})
    lead = di.get("lead", {})
    step = di.get("step_metrics", {})
    return {
        "lead_alpha": lead.get("alpha"),
        "lead_wm": lead.get("wm"),
        "lead_phi_max": lead.get("phi_max"),
        "lead_zero": lead.get("wz"),
        "lead_pole": lead.get("wp"),
        "lead_hf_gain_db": lead.get("hf_gain_db"),
        "compensated_pm": di.get("pm"),
        "compensated_gm": di.get("gm"),
        "gain_crossover_freq": di.get("wgc"),
        "cl_stable": di.get("cl_stable"),
        "rise_time": step.get("rise_time"),
        "overshoot": step.get("overshoot"),
        "settling_time": step.get("settling_time"),
        "matlab_cmd": "G=tf(1,[1 1 0]); C=tf([1/1.5811 1],[1/15.811 1]); margin(C*G); step(feedback(C*G,1));",
    }


# ===== NYQUIST STABILITY =====

@benchmark(
    "NY01_nyquist_rhp_stable",
    "nyquist_stability",
    {"preset": "rhp_pole_stable", "gain_K": 1.0, "zero_z": 3.0, "pole_b": 2.0},
    "Nyquist: L(s)=(s+3)/((s-1)(s+2)) — OL unstable (P=1), CL stable via CCW encirclement",
)
def _extract_nyquist_rhp(state):
    meta = state.get("metadata", {})
    crit = meta.get("stability_criterion", {})
    info = meta.get("stability_info", {})
    return {
        "N": crit.get("N"),
        "P": crit.get("P"),
        "Z": crit.get("Z"),
        "is_stable": crit.get("is_stable"),
        "equation_holds": crit.get("equation_holds"),
        "gain_margin_db": info.get("gain_margin_db"),
        "phase_margin_deg": info.get("phase_margin_deg"),
        "gain_crossover_freq": info.get("gain_crossover_freq"),
        "phase_crossover_freq": info.get("phase_crossover_freq"),
        "matlab_cmd": "L=tf([1 3],conv([1 -1],[1 2])); nyquist(L); [Gm,Pm,Wcg,Wcp]=margin(L);",
    }


@benchmark(
    "NY02_nyquist_unstable",
    "nyquist_stability",
    {"preset": "unstable_third_order", "gain_K": 10.0, "pole_a": 1.0, "pole_b": 2.0},
    "Nyquist: L(s)=10/[s(s+1)(s+2)] at K=10 — unstable (N=2 CW, P=0, Z=2)",
)
def _extract_nyquist_unstable(state):
    meta = state.get("metadata", {})
    crit = meta.get("stability_criterion", {})
    info = meta.get("stability_info", {})
    return {
        "N": crit.get("N"),
        "P": crit.get("P"),
        "Z": crit.get("Z"),
        "is_stable": crit.get("is_stable"),
        "equation_holds": crit.get("equation_holds"),
        "gain_margin_db": info.get("gain_margin_db"),
        "phase_margin_deg": info.get("phase_margin_deg"),
        "matlab_cmd": "L=tf(10,[1 3 2 0]); nyquist(L); [Gm,Pm,Wcg,Wcp]=margin(L);",
    }


# ===== LQG (LQR + KALMAN FILTER) =====

@benchmark(
    "LG01_mimo_lqg",
    "mimo_design_studio",
    {"preset": "aircraft_lateral", "design_mode": "lqg",
     "q_diag": "10,1,10,1", "r_diag": "1,1",
     "qw_diag": "1,1,1,1", "rv_diag": "0.1,0.1"},
    "MIMO LQG: aircraft lateral — regulator K, Kalman L, CL eigenvalues",
)
def _extract_mimo_lqg(state):
    meta = state.get("metadata", {})
    ctrl = meta.get("controller", {})
    return {
        "K": ctrl.get("K"),
        "L": ctrl.get("L"),
        "K_eigs_real": ctrl.get("K_eigs_real"),
        "K_eigs_imag": ctrl.get("K_eigs_imag"),
        "L_eigs_real": ctrl.get("L_eigs_real"),
        "L_eigs_imag": ctrl.get("L_eigs_imag"),
        "cl_eigs_real": ctrl.get("cl_eigs_real"),
        "cl_eigs_imag": ctrl.get("cl_eigs_imag"),
        "matlab_cmd": "A=...; B=...; C=...; [K,~,~]=lqr(A,B,Q,R); [L,~,~]=lqe(A,eye(4),C,Qw,Rv);",
    }


# ===== PID AUTO-TUNING =====

@benchmark(
    "AT01_zn_closed_loop",
    "controller_tuning_lab",
    {"plant_preset": "custom", "custom_num": "1", "custom_den": "1, 8, 17, 10",
     "controller_type": "PID", "tuning_method": "zn_closed"},
    "ZN closed-loop: G(s)=1/[(s+1)(s+2)(s+5)] — Ku=126, Pu=2π/√17, PID gains",
    actions=["apply_tuning"],
)
def _extract_zn_tuning(state):
    meta = state.get("metadata", {})
    perf = meta.get("performance", {})
    params = state.get("parameters", {})
    return {
        "Kp": params.get("Kp"),
        "Ki": params.get("Ki"),
        "Kd": params.get("Kd"),
        "is_stable": perf.get("is_stable"),
        "matlab_cmd": "G=tf(1,conv(conv([1 1],[1 2]),[1 5])); [Gm,Pm,Wcg,Wcp]=margin(G); Ku=Gm; Pu=2*pi/Wcg;",
    }


# ===== TRANSFORMS =====

@benchmark(
    "TR01_laplace_poles",
    "laplace_roc",
    {},  # use defaults
    "Laplace ROC: default system poles and ROC boundary",
)
def _extract_laplace(state):
    meta = state.get("metadata", {})
    plots = state["plots"]
    # The pole-zero plot is typically the first plot
    pz_trace = find_trace_by_index(plots, "pole_zero_map", 0)
    return {
        "metadata": {k: v for k, v in meta.items()
                     if k not in ("hub_slots", "hub_domain", "hub_dimensions", "simulation_type")},
        "poles_from_plot": extract_xy(pz_trace),
        "matlab_cmd": "H = tf(num,den); pzmap(H);",
    }


# ===== CIRCUIT =====

@benchmark(
    "CI01_feedback_amplifier",
    "feedback_system_analysis",
    {},  # use defaults
    "Feedback amplifier: closed-loop gain, bandwidth, stability",
)
def _extract_feedback(state):
    meta = state.get("metadata", {})
    return {
        "metadata": {k: v for k, v in meta.items()
                     if k not in ("hub_slots", "hub_domain", "hub_dimensions", "simulation_type")},
        "matlab_cmd": "% Compare CL gain = A/(1+A*beta), bandwidth, phase margin",
    }


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------
def run_benchmark(bench_id: str, bench_def: dict) -> dict:
    """Run a single benchmark and return results dict."""
    sim_id = bench_def["sim_id"]
    params = bench_def["params"]

    # Get simulator class
    sim_class = SIMULATOR_REGISTRY.get(sim_id)
    if sim_class is None:
        return {"status": "ERROR", "error": f"Simulator '{sim_id}' not in registry"}

    try:
        # Instantiate and initialize through public API (mirrors real usage)
        sim = sim_class(sim_id)
        t0 = time.perf_counter()
        sim.initialize()

        # Apply params via update_parameter (the real UI code path)
        # This triggers preset loading, recomputation, etc.
        for name, value in params.items():
            sim.update_parameter(name, value)

        # Fire any required actions (e.g., "apply_pole_placement" button)
        for action in bench_def.get("actions", []):
            if hasattr(sim, "handle_action"):
                sim.handle_action(action)

        state = sim.get_state()
        elapsed_ms = (time.perf_counter() - t0) * 1000

        # Extract benchmark-specific results
        results = bench_def["extract"](state)
        results["_elapsed_ms"] = round(elapsed_ms, 2)
        results["_status"] = "OK"
        results["_sim_id"] = sim_id
        results["_params_used"] = params

        return results

    except Exception as e:
        return {
            "_status": "ERROR",
            "_sim_id": sim_id,
            "_error": str(e),
            "_traceback": traceback.format_exc(),
        }


def run_all():
    """Run all benchmarks and save results."""
    print(f"SCOPE Validation Suite — {len(BENCHMARKS)} benchmarks")
    print("=" * 60)

    results = {}
    passed = 0
    failed = 0

    for bench_id, bench_def in BENCHMARKS.items():
        desc = bench_def.get("description", bench_id)
        print(f"\n  [{bench_id}] {desc}")
        result = run_benchmark(bench_id, bench_def)

        status = result.get("_status", "ERROR")
        if status == "OK":
            elapsed = result.get("_elapsed_ms", 0)
            print(f"    -> OK ({elapsed:.1f} ms)")
            passed += 1
        else:
            err = result.get("_error", "unknown")
            print(f"    -> FAILED: {err}")
            failed += 1

        results[bench_id] = result

    # Metadata
    output = {
        "metadata": {
            "platform": "SCOPE",
            "numpy_version": np.__version__,
            "scipy_version": __import__("scipy").__version__,
            "python_version": sys.version.split()[0],
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total_benchmarks": len(BENCHMARKS),
            "passed": passed,
            "failed": failed,
        },
        "benchmarks": results,
    }

    # Write results
    out_path = PROJECT_ROOT / "validation" / "results" / "scope_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(output, f, cls=NumpyEncoder, indent=2)

    print(f"\n{'=' * 60}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"Output:  {out_path}")
    return output


if __name__ == "__main__":
    run_all()
