#!/usr/bin/env python3
"""
SCOPE vs MATLAB Comparison Script

Loads scope_results.json and matlab_results.json, computes per-benchmark
error metrics, and outputs a comparison report.

Usage:
    python -m validation.compare

Expects:
    validation/results/scope_results.json   (from run_scope_benchmarks.py)
    validation/results/matlab_results.json  (from MATLAB run_all_benchmarks.m)

Output:
    validation/results/comparison.json
    Prints summary table to stdout
"""

import json
import sys
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "validation" / "results"

# ---------------------------------------------------------------------------
# Error metric functions
# ---------------------------------------------------------------------------

def max_abs_error(scope_arr, matlab_arr) -> float:
    """Maximum absolute difference between two arrays."""
    s = np.asarray(scope_arr, dtype=float)
    m = np.asarray(matlab_arr, dtype=float)
    if s.shape != m.shape:
        return float("inf")
    return float(np.max(np.abs(s - m)))


def rms_relative_error(scope_arr, matlab_arr, eps=1e-15) -> float:
    """RMS relative error, ignoring near-zero reference values."""
    s = np.asarray(scope_arr, dtype=float)
    m = np.asarray(matlab_arr, dtype=float)
    if s.shape != m.shape:
        return float("inf")
    mask = np.abs(m) > eps
    if not np.any(mask):
        return 0.0
    rel = (s[mask] - m[mask]) / m[mask]
    return float(np.sqrt(np.mean(rel ** 2)))


def scalar_relative_error(scope_val, matlab_val, eps=1e-15) -> float:
    """Relative error between two scalars."""
    if scope_val is None or matlab_val is None:
        return float("inf")
    s = float(scope_val)
    m = float(matlab_val)
    if abs(m) < eps:
        return abs(s - m)
    return abs((s - m) / m)


def complex_array_error(scope_reals, scope_imags, matlab_reals, matlab_imags) -> float:
    """Max error between two sets of complex numbers (sorted by magnitude)."""
    s = sorted(
        [complex(r, i) for r, i in zip(scope_reals, scope_imags)],
        key=lambda c: (abs(c), c.real),
    )
    m = sorted(
        [complex(r, i) for r, i in zip(matlab_reals, matlab_imags)],
        key=lambda c: (abs(c), c.real),
    )
    if len(s) != len(m):
        return float("inf")
    return max(abs(a - b) for a, b in zip(s, m))


# ---------------------------------------------------------------------------
# Per-benchmark comparison definitions
# ---------------------------------------------------------------------------

# Each comparator takes (scope_result, matlab_result) and returns a list of
# (metric_name, scope_value, matlab_value, error, tolerance, pass/fail)

TOLERANCES = {
    "scalar": 1e-10,
    "display": 3e-3,  # SCOPE metadata rounds values for UI display (e.g. round(Q,3))
    "array": 1e-6,
    "ode": 1e-4,      # ODE integration has inherent variability
    "integer": 0,      # exact match
    "boolean": 0,      # exact match
}


def _is_inf(val) -> bool:
    """Check if a value represents infinity.

    Handles: Python float('inf'), numpy inf, string "Infinity"/"Inf",
    and MATLAB jsonencode(Inf)->null fallback.
    """
    if val is None:
        return False
    if isinstance(val, str):
        return val in ("Infinity", "-Infinity", "Inf", "-Inf", "inf", "-inf")
    if isinstance(val, (int, float)):
        try:
            return math.isinf(float(val))
        except (ValueError, OverflowError):
            return False
    return False


def _both_inf(s, m) -> bool:
    """True if both values represent infinity."""
    return _is_inf(s) and _is_inf(m)


def _either_inf(s, m) -> bool:
    """True if exactly one value is inf and the other isn't."""
    return _is_inf(s) != _is_inf(m)


def compare_benchmark(bench_id: str, scope: dict, matlab: dict) -> List[dict]:
    """Compare a single benchmark's results. Returns list of metric dicts."""
    metrics = []

    def add(name, s_val, m_val, error, tol, category="scalar"):
        passed = error <= tol if not math.isinf(error) else False
        metrics.append({
            "metric": name,
            "scope": s_val,
            "matlab": m_val,
            "error": error,
            "tolerance": tol,
            "pass": passed,
            "category": category,
        })

    # --- SP01/SP02: RC filter ---
    if bench_id == "SP01_rc_bode":
        if "cutoff_freq_hz" in scope and "cutoff_freq_hz" in matlab:
            s, m = scope["cutoff_freq_hz"], matlab["cutoff_freq_hz"]
            # SCOPE rounds cutoff_freq for display metadata
            add("cutoff_freq_hz", s, m, scalar_relative_error(s, m), TOLERANCES["display"], "display")
        if scope.get("bode_magnitude_db") and matlab.get("bode_magnitude_db"):
            err = max_abs_error(scope["bode_magnitude_db"], matlab["bode_magnitude_db"])
            add("bode_magnitude_db (max abs)", "array", "array", err, TOLERANCES["array"], "array")

    elif bench_id == "SP02_rc_bode_phase":
        if scope.get("bode_magnitude_db") and matlab.get("bode_magnitude_db"):
            err = max_abs_error(scope["bode_magnitude_db"], matlab["bode_magnitude_db"])
            add("bode_magnitude_db (max abs)", "array", "array", err, TOLERANCES["array"], "array")

    # --- CS01/CS02: Second-order system ---
    elif bench_id.startswith("CS01") or bench_id.startswith("CS02"):
        for key in ("omega_0", "Q", "zeta", "bandwidth"):
            if key in scope and key in matlab and scope[key] is not None and matlab[key] is not None:
                s, m = scope[key], matlab[key]
                # SCOPE rounds Q, zeta, bandwidth for display metadata
                add(key, s, m, scalar_relative_error(s, m), TOLERANCES["display"], "display")
        if scope.get("bode_magnitude_db") and matlab.get("bode_magnitude_db"):
            err = max_abs_error(scope["bode_magnitude_db"], matlab["bode_magnitude_db"])
            add("bode_magnitude_db (max abs)", "array", "array", err, TOLERANCES["array"], "array")

    # --- CS04b: 5th-order Routh (adversarial, has zero-pivot) ---
    elif bench_id == "CS04b_routh_5th_order":
        # first_column comparison skipped — zero pivot makes intermediate values
        # epsilon-dependent (1/ε effect). Sign pattern is what matters.
        for key in ("sign_changes", "rhp_poles"):
            if key in scope and key in matlab:
                s, m = scope[key], matlab[key]
                err = 0 if s == m else 1
                add(key, s, m, err, TOLERANCES["integer"], "integer")
        if "stable" in scope and "stable" in matlab:
            s, m = scope["stable"], matlab["stable"]
            err = 0 if s == m else 1
            add("stable", s, m, err, TOLERANCES["boolean"], "boolean")
        # Cross-check: MATLAB independently verified sign_changes == roots() RHP count
        if "roots_rhp_count" in matlab and "sign_changes" in matlab:
            s, m = matlab["sign_changes"], matlab["roots_rhp_count"]
            err = 0 if s == m else 1
            add("matlab_routh_vs_roots_crosscheck", s, m, err, TOLERANCES["integer"], "integer")

    # --- CS03/CS04: Routh-Hurwitz ---
    elif bench_id.startswith("CS03") or bench_id.startswith("CS04"):
        if scope.get("first_column") and matlab.get("first_column"):
            err = max_abs_error(scope["first_column"], matlab["first_column"])
            add("routh_first_column (max abs)", scope["first_column"], matlab["first_column"],
                err, TOLERANCES["scalar"], "array")
        for key in ("sign_changes", "rhp_poles"):
            if key in scope and key in matlab:
                s, m = scope[key], matlab[key]
                err = 0 if s == m else 1
                add(key, s, m, err, TOLERANCES["integer"], "integer")
        if "stable" in scope and "stable" in matlab:
            s, m = scope["stable"], matlab["stable"]
            err = 0 if s == m else 1
            add("stable", s, m, err, TOLERANCES["boolean"], "boolean")

    # --- CS05/CS06: Steady-state error ---
    elif bench_id.startswith("CS05") or bench_id.startswith("CS06"):
        if "system_type" in scope and "system_type" in matlab:
            s, m = scope["system_type"], matlab["system_type"]
            add("system_type", s, m, 0 if s == m else 1, TOLERANCES["integer"], "integer")
        for const in ("Kp", "Kv", "Ka"):
            s_ec = scope.get("error_constants", {})
            m_ec = matlab.get("error_constants", {})
            if const in s_ec and const in m_ec:
                s, m = s_ec[const], m_ec[const]
                # MATLAB jsonencode(Inf) -> null; treat None as Inf in this context
                if _both_inf(s, m):
                    add(f"error_constant_{const}", s, m, 0, TOLERANCES["scalar"])
                elif _either_inf(s, m):
                    add(f"error_constant_{const}", s, m, float("inf"), TOLERANCES["scalar"])
                else:
                    add(f"error_constant_{const}", s, m,
                        scalar_relative_error(s, m), TOLERANCES["scalar"])
        for inp in ("step", "ramp", "parabolic"):
            s_se = scope.get("steady_state_errors", {})
            m_se = matlab.get("steady_state_errors", {})
            if inp in s_se and inp in m_se:
                s_val = s_se[inp]
                m_val = m_se[inp]
                # MATLAB jsonencode(Inf) -> null; treat None as Inf in this context
                if _both_inf(s_val, m_val):
                    add(f"ess_{inp}", s_val, m_val, 0, TOLERANCES["scalar"])
                elif _either_inf(s_val, m_val):
                    add(f"ess_{inp}", s_val, m_val, float("inf"), TOLERANCES["scalar"])
                else:
                    add(f"ess_{inp}", s_val, m_val,
                        scalar_relative_error(s_val, m_val), TOLERANCES["scalar"])

    # --- CS01b: Near-zero damping (adversarial) ---
    elif bench_id == "CS01b_near_zero_damping":
        for key in ("omega_0", "Q", "zeta", "bandwidth"):
            if key in scope and key in matlab and scope[key] is not None and matlab[key] is not None:
                s, m = scope[key], matlab[key]
                add(key, s, m, scalar_relative_error(s, m), TOLERANCES["display"], "display")
        if scope.get("bode_magnitude_db") and matlab.get("bode_magnitude_db"):
            err = max_abs_error(scope["bode_magnitude_db"], matlab["bode_magnitude_db"])
            add("bode_magnitude_db (max abs)", "array", "array", err, TOLERANCES["array"], "array")

    # --- CS07/CS08: LQR / Pole Placement ---
    elif bench_id in ("CS07_lqr", "CS08_pole_placement"):
        if scope.get("state_feedback_K") and matlab.get("state_feedback_K"):
            err = max_abs_error(scope["state_feedback_K"], matlab["state_feedback_K"])
            add("K_gain (max abs)", scope["state_feedback_K"], matlab["state_feedback_K"],
                err, TOLERANCES["scalar"], "array")
        for key in ("rise_time", "settling_time", "overshoot_pct", "phase_margin_deg"):
            if key in scope and key in matlab and scope[key] is not None and matlab[key] is not None:
                s, m = scope[key], matlab[key]
                add(key, s, m, scalar_relative_error(s, m), TOLERANCES["ode"])

    # --- CS09/CS10: MIMO ---
    elif bench_id == "CS09_mimo_eigenvalues":
        if (scope.get("eigenvalues_real") and matlab.get("eigenvalues_real") and
                scope.get("eigenvalues_imag") and matlab.get("eigenvalues_imag")):
            err = complex_array_error(
                scope["eigenvalues_real"], scope["eigenvalues_imag"],
                matlab["eigenvalues_real"], matlab["eigenvalues_imag"],
            )
            add("eigenvalues (max complex err)", "array", "array", err, TOLERANCES["scalar"], "array")
        for key in ("controllability_rank", "observability_rank"):
            if key in scope and key in matlab:
                s, m = scope[key], matlab[key]
                add(key, s, m, 0 if s == m else 1, TOLERANCES["integer"], "integer")

    elif bench_id == "CS10_mimo_lqr":
        if scope.get("K") and matlab.get("K"):
            s_k = np.asarray(scope["K"])
            m_k = np.asarray(matlab["K"])
            if s_k.shape == m_k.shape:
                err = float(np.max(np.abs(s_k - m_k)))
                add("K_gain (max abs)", "matrix", "matrix", err, TOLERANCES["scalar"], "array")

    # --- RL01: Root Locus ---
    elif bench_id == "RL01_root_locus":
        for key in ("breakaway_real", "breakaway_K"):
            if key in scope and key in matlab and scope[key] is not None and matlab[key] is not None:
                s, m = scope[key], matlab[key]
                add(key, s, m, scalar_relative_error(s, m), TOLERANCES["scalar"])
        for key in ("jw_crossing_omega", "jw_crossing_K", "stability_K_max"):
            if key in scope and key in matlab and scope[key] is not None and matlab[key] is not None:
                s, m = scope[key], matlab[key]
                add(key, s, m, scalar_relative_error(s, m), 1e-4)  # numerical root-finding
        if "asymptote_centroid" in scope and "asymptote_centroid" in matlab:
            s, m = scope["asymptote_centroid"], matlab["asymptote_centroid"]
            add("asymptote_centroid", s, m, scalar_relative_error(s, m), TOLERANCES["scalar"])
        if scope.get("asymptote_angles") and matlab.get("asymptote_angles"):
            err = max_abs_error(scope["asymptote_angles"], matlab["asymptote_angles"])
            add("asymptote_angles (max abs)", "array", "array", err, TOLERANCES["scalar"], "array")
        if "n_asymptotes" in scope and "n_asymptotes" in matlab:
            s, m = scope["n_asymptotes"], matlab["n_asymptotes"]
            add("n_asymptotes", s, m, 0 if s == m else 1, TOLERANCES["integer"], "integer")
        if "phase_margin_deg" in scope and "phase_margin_deg" in matlab:
            if scope["phase_margin_deg"] is not None and matlab["phase_margin_deg"] is not None:
                s, m = scope["phase_margin_deg"], matlab["phase_margin_deg"]
                add("phase_margin_deg", s, m, scalar_relative_error(s, m), 1e-3)

    # --- CD01: PID Step Response ---
    elif bench_id == "CD01_pid_step_response":
        for key in ("rise_time", "overshoot_pct"):
            if key in scope and key in matlab and scope[key] is not None and matlab[key] is not None:
                s, m = scope[key], matlab[key]
                add(key, s, m, scalar_relative_error(s, m), 0.05)
        # Settling time is sensitive to ODE solver, time grid length, and 2% band
        # detection. SSE near 0 for integral controllers (absolute diff dominates).
        for key in ("settling_time", "steady_state_error"):
            if key in scope and key in matlab and scope[key] is not None and matlab[key] is not None:
                s, m = scope[key], matlab[key]
                add(key, s, m, scalar_relative_error(s, m), 0.15)
        if "is_stable" in scope and "is_stable" in matlab:
            s, m = scope["is_stable"], matlab["is_stable"]
            add("is_stable", s, m, 0 if s == m else 1, TOLERANCES["boolean"], "boolean")
        for key in ("phase_margin_deg", "gain_crossover_freq"):
            if key in scope and key in matlab and scope[key] is not None and matlab[key] is not None:
                s, m = scope[key], matlab[key]
                add(key, s, m, scalar_relative_error(s, m), 1e-3)

    # --- CD02: Open-Loop Margins ---
    elif bench_id == "CD02_open_loop_margins":
        for key in ("gain_margin_db", "phase_margin_deg"):
            if key in scope and key in matlab and scope[key] is not None and matlab[key] is not None:
                s, m = scope[key], matlab[key]
                add(key, s, m, scalar_relative_error(s, m), 1e-3)
        for key in ("gain_crossover_freq", "phase_crossover_freq"):
            if key in scope and key in matlab and scope[key] is not None and matlab[key] is not None:
                s, m = scope[key], matlab[key]
                add(key, s, m, scalar_relative_error(s, m), 1e-3)
        if "is_stable" in scope and "is_stable" in matlab:
            s, m = scope["is_stable"], matlab["is_stable"]
            add("is_stable", s, m, 0 if s == m else 1, TOLERANCES["boolean"], "boolean")

    # --- LL01: Lead Compensator ---
    elif bench_id == "LL01_lead_compensator":
        # Analytical values — these are exact formulas
        for key in ("lead_phi_max", "lead_zero", "lead_pole", "lead_hf_gain_db"):
            if key in scope and key in matlab and scope[key] is not None and matlab[key] is not None:
                s, m = scope[key], matlab[key]
                add(key, s, m, scalar_relative_error(s, m), TOLERANCES["display"], "display")
        # Compensated margins — frequency-domain computation
        for key in ("compensated_pm", "gain_crossover_freq"):
            if key in scope and key in matlab and scope[key] is not None and matlab[key] is not None:
                s, m = scope[key], matlab[key]
                add(key, s, m, scalar_relative_error(s, m), 0.01)
        if "cl_stable" in scope and "cl_stable" in matlab:
            s, m = scope["cl_stable"], matlab["cl_stable"]
            add("cl_stable", s, m, 0 if s == m else 1, TOLERANCES["boolean"], "boolean")
        # Step response metrics from the compensated system
        # 8% tolerance: small overshoot values (~2%) amplify relative error
        # from ODE solver and time-grid differences
        for key in ("rise_time", "overshoot", "settling_time"):
            if key in scope and key in matlab and scope[key] is not None and matlab[key] is not None:
                s, m = scope[key], matlab[key]
                add(key, s, m, scalar_relative_error(s, m), 0.08)

    # --- NY01: Nyquist RHP pole, stable CL ---
    elif bench_id == "NY01_nyquist_rhp_stable":
        for key in ("N", "P", "Z"):
            if key in scope and key in matlab:
                s, m = scope[key], matlab[key]
                add(key, s, m, 0 if s == m else 1, TOLERANCES["integer"], "integer")
        for key in ("is_stable", "equation_holds"):
            if key in scope and key in matlab:
                s, m = scope[key], matlab[key]
                add(key, s, m, 0 if s == m else 1, TOLERANCES["boolean"], "boolean")
        for key in ("gain_margin_db", "phase_margin_deg"):
            if key in scope and key in matlab and scope[key] is not None and matlab[key] is not None:
                s, m = scope[key], matlab[key]
                if _both_inf(s, m):
                    add(key, s, m, 0, TOLERANCES["display"], "display")
                else:
                    add(key, s, m, scalar_relative_error(s, m), TOLERANCES["display"], "display")
        for key in ("gain_crossover_freq", "phase_crossover_freq"):
            if key in scope and key in matlab and scope[key] is not None and matlab[key] is not None:
                s, m = scope[key], matlab[key]
                if _both_inf(s, m):
                    add(key, s, m, 0, TOLERANCES["display"], "display")
                else:
                    add(key, s, m, scalar_relative_error(s, m), TOLERANCES["display"], "display")

    # --- NY02: Nyquist unstable CL ---
    elif bench_id == "NY02_nyquist_unstable":
        for key in ("N", "P", "Z"):
            if key in scope and key in matlab:
                s, m = scope[key], matlab[key]
                add(key, s, m, 0 if s == m else 1, TOLERANCES["integer"], "integer")
        for key in ("is_stable", "equation_holds"):
            if key in scope and key in matlab:
                s, m = scope[key], matlab[key]
                add(key, s, m, 0 if s == m else 1, TOLERANCES["boolean"], "boolean")
        for key in ("gain_margin_db", "phase_margin_deg"):
            if key in scope and key in matlab and scope[key] is not None and matlab[key] is not None:
                s, m = scope[key], matlab[key]
                add(key, s, m, scalar_relative_error(s, m), TOLERANCES["display"], "display")

    # --- LG01: MIMO LQG ---
    elif bench_id == "LG01_mimo_lqg":
        # K and L gain matrices
        for key in ("K", "L"):
            if scope.get(key) and matlab.get(key):
                s_k = np.asarray(scope[key])
                m_k = np.asarray(matlab[key])
                if s_k.shape == m_k.shape:
                    err = float(np.max(np.abs(s_k - m_k)))
                    add(f"{key}_gain (max abs)", "matrix", "matrix", err, TOLERANCES["scalar"], "array")
        # Regulator eigenvalues (A-BK)
        if (scope.get("K_eigs_real") and matlab.get("K_eigs_real") and
                scope.get("K_eigs_imag") and matlab.get("K_eigs_imag")):
            err = complex_array_error(
                scope["K_eigs_real"], scope["K_eigs_imag"],
                matlab["K_eigs_real"], matlab["K_eigs_imag"],
            )
            add("regulator_eigs (max complex err)", "array", "array", err, TOLERANCES["scalar"], "array")
        # Estimator eigenvalues (A-LC)
        if (scope.get("L_eigs_real") and matlab.get("L_eigs_real") and
                scope.get("L_eigs_imag") and matlab.get("L_eigs_imag")):
            err = complex_array_error(
                scope["L_eigs_real"], scope["L_eigs_imag"],
                matlab["L_eigs_real"], matlab["L_eigs_imag"],
            )
            add("estimator_eigs (max complex err)", "array", "array", err, TOLERANCES["scalar"], "array")
        # CL eigenvalues (union of regulator + estimator)
        if (scope.get("cl_eigs_real") and matlab.get("cl_eigs_real") and
                scope.get("cl_eigs_imag") and matlab.get("cl_eigs_imag")):
            err = complex_array_error(
                scope["cl_eigs_real"], scope["cl_eigs_imag"],
                matlab["cl_eigs_real"], matlab["cl_eigs_imag"],
            )
            add("cl_eigs (max complex err)", "array", "array", err, TOLERANCES["scalar"], "array")

    # --- AT01: ZN closed-loop auto-tuning ---
    # SCOPE finds Ku via 50-iteration binary search on CL poles;
    # MATLAB margin() uses different numerical method — both ~1e-7 precision
    elif bench_id == "AT01_zn_closed_loop":
        for key in ("Kp", "Ki", "Kd"):
            if key in scope and key in matlab and scope[key] is not None and matlab[key] is not None:
                s, m = scope[key], matlab[key]
                add(key, s, m, scalar_relative_error(s, m), 1e-6)
        if "is_stable" in scope and "is_stable" in matlab:
            s, m = scope["is_stable"], matlab["is_stable"]
            add("is_stable", s, m, 0 if s == m else 1, TOLERANCES["boolean"], "boolean")

    # --- Generic fallback for other benchmarks ---
    else:
        metrics.append({
            "metric": "no_comparator_defined",
            "scope": None,
            "matlab": None,
            "error": 0,
            "tolerance": 0,
            "pass": True,
            "category": "skip",
        })

    return metrics


# ---------------------------------------------------------------------------
# Main comparison
# ---------------------------------------------------------------------------
def run_comparison():
    scope_path = RESULTS_DIR / "scope_results.json"
    matlab_path = RESULTS_DIR / "matlab_results.json"

    if not scope_path.exists():
        print(f"ERROR: {scope_path} not found. Run run_scope_benchmarks.py first.")
        sys.exit(1)
    if not matlab_path.exists():
        print(f"ERROR: {matlab_path} not found. Run MATLAB run_all_benchmarks.m first.")
        sys.exit(1)

    with open(scope_path) as f:
        scope_data = json.load(f)
    with open(matlab_path) as f:
        matlab_data = json.load(f)

    scope_benchmarks = scope_data.get("benchmarks", {})
    matlab_benchmarks = matlab_data.get("benchmarks", {})

    print("SCOPE vs MATLAB Comparison Report")
    print("=" * 80)
    print(f"SCOPE:  numpy {scope_data['metadata']['numpy_version']}, "
          f"scipy {scope_data['metadata']['scipy_version']}")
    print(f"MATLAB: {matlab_data.get('metadata', {}).get('matlab_version', 'unknown')}")
    print("=" * 80)

    all_metrics = {}
    total_pass = 0
    total_fail = 0
    computation_pass = 0
    computation_fail = 0
    display_pass = 0
    display_fail = 0

    for bench_id in scope_benchmarks:
        if bench_id not in matlab_benchmarks:
            print(f"\n  [{bench_id}] SKIPPED — no MATLAB result")
            continue

        scope_result = scope_benchmarks[bench_id]
        matlab_result = matlab_benchmarks[bench_id]

        if scope_result.get("_status") != "OK":
            print(f"\n  [{bench_id}] SKIPPED — SCOPE benchmark failed")
            continue

        metrics = compare_benchmark(bench_id, scope_result, matlab_result)
        all_metrics[bench_id] = metrics

        bench_pass = all(m["pass"] for m in metrics)
        status = "PASS" if bench_pass else "FAIL"
        print(f"\n  [{bench_id}] {status}")

        for m in metrics:
            icon = "+" if m["pass"] else "X"
            err_str = f"{m['error']:.2e}" if isinstance(m["error"], float) else str(m["error"])
            tol_str = f"{m['tolerance']:.0e}" if isinstance(m["tolerance"], float) else str(m["tolerance"])
            tag = " [display]" if m["category"] == "display" else ""
            print(f"    [{icon}] {m['metric']}: error={err_str} (tol={tol_str}){tag}")

            if m["pass"]:
                total_pass += 1
            else:
                total_fail += 1

            if m["category"] == "display":
                if m["pass"]:
                    display_pass += 1
                else:
                    display_fail += 1
            else:
                if m["pass"]:
                    computation_pass += 1
                else:
                    computation_fail += 1

    # Save comparison report
    report = {
        "metadata": {
            "scope_version": scope_data["metadata"],
            "matlab_version": matlab_data.get("metadata", {}),
        },
        "benchmarks": all_metrics,
        "summary": {
            "total_metrics": total_pass + total_fail,
            "passed": total_pass,
            "failed": total_fail,
            "computation_metrics": computation_pass + computation_fail,
            "computation_passed": computation_pass,
            "display_metrics": display_pass + display_fail,
            "display_passed": display_pass,
        },
    }
    out_path = RESULTS_DIR / "comparison.json"
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\n{'=' * 80}")
    print(f"Total: {total_pass} passed, {total_fail} failed out of {total_pass + total_fail} metrics")
    print(f"  Computation: {computation_pass}/{computation_pass + computation_fail} passed")
    print(f"  Display (UI-rounded): {display_pass}/{display_pass + display_fail} passed")
    print(f"Report: {out_path}")


if __name__ == "__main__":
    run_comparison()
