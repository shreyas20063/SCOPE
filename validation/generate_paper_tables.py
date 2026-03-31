#!/usr/bin/env python3
"""
Generate LaTeX tables for SCOPE validation paper.

Reads comparison.json (output of compare.py) and produces paper-ready
LaTeX table blocks.

Usage:
    python -m validation.generate_paper_tables

Output:
    validation/results/validation_table.tex
    Prints tables to stdout
"""

import json
import sys
from pathlib import Path

RESULTS_DIR = Path(__file__).resolve().parent / "results"


def format_error(err: float) -> str:
    """Format error value for LaTeX."""
    if err == 0:
        return "0 (exact)"
    if err == float("inf"):
        return r"$\infty$"
    if err < 1e-14:
        return r"$<10^{-14}$"
    exp = int(f"{err:.0e}".split("e")[1])
    coeff = err / (10 ** exp)
    if abs(coeff - 1.0) < 0.05:
        return f"$10^{{{exp}}}$"
    return f"${coeff:.1f} \\times 10^{{{exp}}}$"


def format_value(val) -> str:
    """Format a value for display in the table."""
    if val is None:
        return "---"
    if isinstance(val, bool):
        return str(val)
    if isinstance(val, str):
        if val == "array" or val == "matrix":
            return val
        return val
    if isinstance(val, float):
        if val == float("inf") or val == float("-inf"):
            return r"$\infty$"
        if abs(val) < 0.001 and val != 0:
            return f"{val:.4e}"
        return f"{val:.6g}"
    if isinstance(val, (list, tuple)):
        if len(val) <= 4:
            formatted = ", ".join(f"{v:.4g}" if isinstance(v, float) else str(v) for v in val)
            return f"[{formatted}]"
        return f"array({len(val)})"
    return str(val)


def generate_summary_table(comparison: dict) -> str:
    """Generate the main validation summary table (Table 1 in paper)."""
    benchmarks = comparison.get("benchmarks", {})

    # Friendly names for benchmarks
    bench_names = {
        "SP01_rc_bode": "RC Filter Bode Response",
        "SP02_rc_bode_phase": "RC Filter Bode (Cross-check)",
        "CS01_2nd_order_underdamped": "2nd-Order Underdamped",
        "CS02_2nd_order_overdamped": "2nd-Order Overdamped",
        "CS01b_near_zero_damping": "2nd-Order Near-Zero Damping*",
        "CS03_routh_stable": "Routh-Hurwitz (Stable)",
        "CS04_routh_unstable": "Routh-Hurwitz (Unstable)",
        "CS04b_routh_5th_order": "Routh-Hurwitz 5th-Order*",
        "CS05_ess_type0": "Steady-State Error (Type 0)",
        "CS06_ess_type1": "Steady-State Error (Type 1)",
        "CS07_lqr": "LQR Controller Design",
        "CS08_pole_placement": "Pole Placement",
        "CS09_mimo_eigenvalues": "MIMO Eigenvalue Analysis",
        "CS10_mimo_lqr": "MIMO LQR Design",
        "RL01_root_locus": "Root Locus Analysis",
        "CD01_pid_step_response": "PID Step Response",
        "CD02_open_loop_margins": "Open-Loop Margins",
        "LL01_lead_compensator": "Lead Compensator Design",
        "NY01_nyquist_rhp_stable": "Nyquist (RHP Pole, Stable)",
        "NY02_nyquist_unstable": "Nyquist (Unstable, $K{=}10$)",
        "LG01_mimo_lqg": "MIMO LQG Design",
        "AT01_zn_closed_loop": "ZN Closed-Loop Auto-Tuning",
    }

    lines = []
    lines.append(r"\begin{table}[t]")
    lines.append(r"\centering")
    lines.append(r"\caption{Numerical validation of SCOPE against MATLAB R2024b.}")
    lines.append(r"\label{tab:validation}")
    lines.append(r"\begin{tabular}{llccc}")
    lines.append(r"\toprule")
    lines.append(r"\textbf{Benchmark} & \textbf{Metric} & \textbf{Error} & \textbf{Tol.} & \textbf{Pass} \\")
    lines.append(r"\midrule")

    for bench_id, metrics in benchmarks.items():
        name = bench_names.get(bench_id, bench_id)
        if not metrics:
            continue

        for i, m in enumerate(metrics):
            bench_col = name if i == 0 else ""
            metric_name = m["metric"].replace("_", r"\_")
            err_str = format_error(m["error"])
            tol_str = format_error(m["tolerance"])
            pass_str = r"\cmark" if m["pass"] else r"\xmark"

            lines.append(f"  {bench_col} & {metric_name} & {err_str} & {tol_str} & {pass_str} \\\\")

        lines.append(r"\addlinespace")

    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")

    # Summary footnote
    summary = comparison.get("summary", {})
    total = summary.get("total_metrics", 0)
    passed = summary.get("passed", 0)
    lines.append(f"\\vspace{{2pt}}")
    lines.append(f"\\footnotesize{{All {passed}/{total} metrics within tolerance.}}")
    lines.append(r"\end{table}")

    return "\n".join(lines)


def generate_key_results_table(comparison: dict) -> str:
    """Generate a condensed table showing key scalar comparisons."""
    benchmarks = comparison.get("benchmarks", {})

    lines = []
    lines.append(r"\begin{table}[t]")
    lines.append(r"\centering")
    lines.append(r"\caption{Key numerical results: SCOPE vs MATLAB.}")
    lines.append(r"\label{tab:key-results}")
    lines.append(r"\begin{tabular}{llrrl}")
    lines.append(r"\toprule")
    lines.append(r"\textbf{Test Case} & \textbf{Quantity} & \textbf{SCOPE} & \textbf{MATLAB} & \textbf{Rel.\ Error} \\")
    lines.append(r"\midrule")

    # Handpick the most impactful comparisons for the paper
    key_rows = [
        ("SP01_rc_bode", "cutoff_freq_hz", "$f_c$ (Hz)"),
        ("CS01_2nd_order_underdamped", "zeta", r"$\zeta$"),
        ("CS03_routh_stable", "sign_changes", "Sign Changes"),
        ("CS04_routh_unstable", "sign_changes", "Sign Changes"),
        ("CS05_ess_type0", "error_constant_Kp", "$K_p$"),
        ("CS05_ess_type0", "ess_step", "$e_{ss}$ (step)"),
        ("CS07_lqr", "K_gain (max abs)", "$\\|K_{\\text{SCOPE}} - K_{\\text{MATLAB}}\\|_\\infty$"),
        ("CS09_mimo_eigenvalues", "controllability_rank", "Controllability Rank"),
        ("CS09_mimo_eigenvalues", "eigenvalues (max complex err)", "$\\max|\\lambda_{\\text{SCOPE}} - \\lambda_{\\text{MATLAB}}|$"),
        ("NY01_nyquist_rhp_stable", "N", "Nyquist $N$ (encirclements)"),
        ("NY01_nyquist_rhp_stable", "phase_margin_deg", "Nyquist PM (deg)"),
        ("LG01_mimo_lqg", "K_gain (max abs)", "$\\|K_{\\text{SCOPE}} - K_{\\text{MATLAB}}\\|_\\infty$"),
        ("LG01_mimo_lqg", "cl_eigs (max complex err)", "LQG $\\max|\\lambda_{\\text{CL}}|$ error"),
        ("AT01_zn_closed_loop", "Kp", "ZN $K_p$"),
    ]

    for bench_id, metric_name, display_name in key_rows:
        if bench_id not in benchmarks:
            continue
        metrics = benchmarks[bench_id]
        for m in metrics:
            if m["metric"] == metric_name:
                s_str = format_value(m["scope"])
                m_str = format_value(m["matlab"])
                err_str = format_error(m["error"])
                lines.append(f"  {display_name} & & {s_str} & {m_str} & {err_str} \\\\")
                break

    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    lines.append(r"\end{table}")

    return "\n".join(lines)


def generate_preamble() -> str:
    """Generate LaTeX preamble for checkmarks."""
    return r"""% Add to preamble:
% \usepackage{booktabs}
% \usepackage{pifont}
% \newcommand{\cmark}{\textcolor{green!70!black}{\ding{51}}}
% \newcommand{\xmark}{\textcolor{red}{\ding{55}}}
"""


def main():
    comp_path = RESULTS_DIR / "comparison.json"
    if not comp_path.exists():
        print(f"ERROR: {comp_path} not found. Run compare.py first.")
        sys.exit(1)

    with open(comp_path) as f:
        comparison = json.load(f)

    preamble = generate_preamble()
    table1 = generate_summary_table(comparison)
    table2 = generate_key_results_table(comparison)

    full_output = f"{preamble}\n\n% === Table 1: Full Validation Summary ===\n{table1}\n\n% === Table 2: Key Results ===\n{table2}\n"

    # Save
    out_path = RESULTS_DIR / "validation_table.tex"
    with open(out_path, "w") as f:
        f.write(full_output)

    print(full_output)
    print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    main()
