"""Regression test for BUG-098: discrete-time sims must declare HUB_DOMAIN = "dt".

Seven purely discrete-time simulators (y[n]-based math, Oppenheim DTSP topics)
silently inherited BaseSimulator's HUB_DOMAIN = "ct" and reported a continuous-
time hub domain in metadata. Dual-domain sims (block_diagram_builder,
signal_flow_scope, convolution_simulator, dt_ct_comparator, ct_dt_poles) are
intentionally NOT pinned here — they either set domain at runtime or span both.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from simulations import SIMULATOR_REGISTRY

DT_SIMS = [
    "cascade_parallel",       # 2nd-order DT system (Oppenheim DTSP 6.3)
    "cyclic_path_detector",   # FIR/IIR block-diagram classification
    "delay_instability",      # dead-beat control with step delays
    "feedback_convergence",   # y[n] = x[n] + p0*y[n-1]
    "fundamental_modes",      # y[n] = sum A_k p_k^n
    "operator_algebra",       # R-operator (delay) algebra
    "pole_behavior",          # y[n] = p0^n u[n]
]


def test_dt_sims_declare_dt_domain():
    for sim_id in DT_SIMS:
        cls = SIMULATOR_REGISTRY[sim_id]
        assert cls.HUB_DOMAIN == "dt", f"{sim_id}: HUB_DOMAIN={cls.HUB_DOMAIN!r}, expected 'dt'"


def test_dt_sims_report_dt_in_metadata():
    for sim_id in DT_SIMS:
        sim = SIMULATOR_REGISTRY[sim_id](sim_id)
        sim.initialize({})
        domain = sim.get_state()["metadata"].get("hub_domain")
        assert domain == "dt", f"{sim_id}: metadata.hub_domain={domain!r}, expected 'dt'"
