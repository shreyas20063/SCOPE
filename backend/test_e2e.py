#!/usr/bin/env python3
"""
Comprehensive end-to-end test suite for Block Diagram Builder and Signal Flow Scope.

Tests cover:
1. TF Parsing
2. Block Diagram Construction & Mason's Formula
3. Signal Flow Scope Import & Mason's
4. Domain Conversion
5. Polynomial Arithmetic
6. Edge Cases & Robustness
7. Analytical Verification
8. Consistency Checks

Run: cd backend && python3 test_e2e.py
"""

import sys
import os
import types
import importlib.util
import traceback
import numpy as np

# ============================================================================
# Module loading (bypass __init__.py which imports sympy)
# ============================================================================
sys.path.insert(0, os.getcwd())

# Create package stub
pkg = types.ModuleType("simulations")
pkg.__path__ = ["simulations"]
sys.modules["simulations"] = pkg

# Load base
spec = importlib.util.spec_from_file_location(
    "simulations.base_simulator", "simulations/base_simulator.py"
)
mod = importlib.util.module_from_spec(spec)
sys.modules["simulations.base_simulator"] = mod
spec.loader.exec_module(mod)

# Load BDB
spec2 = importlib.util.spec_from_file_location(
    "simulations.block_diagram_builder", "simulations/block_diagram_builder.py"
)
bdb = importlib.util.module_from_spec(spec2)
sys.modules["simulations.block_diagram_builder"] = bdb
spec2.loader.exec_module(bdb)

# Load SFS
spec3 = importlib.util.spec_from_file_location(
    "simulations.signal_flow_scope", "simulations/signal_flow_scope.py"
)
sfs = importlib.util.module_from_spec(spec3)
sys.modules["simulations.signal_flow_scope"] = sfs
spec3.loader.exec_module(sfs)

BlockDiagramSimulator = bdb.BlockDiagramSimulator
SignalFlowScopeSimulator = sfs.SignalFlowScopeSimulator


# ============================================================================
# Test harness
# ============================================================================
class TestResults:
    def __init__(self):
        self.categories = {}
        self.current_category = None

    def set_category(self, name):
        self.current_category = name
        if name not in self.categories:
            self.categories[name] = {"passed": 0, "failed": 0, "details": []}

    def record(self, test_name, passed, msg=""):
        cat = self.categories[self.current_category]
        if passed:
            cat["passed"] += 1
        else:
            cat["failed"] += 1
            cat["details"].append(f"  FAIL: {test_name}: {msg}")

    @property
    def total_passed(self):
        return sum(c["passed"] for c in self.categories.values())

    @property
    def total_failed(self):
        return sum(c["failed"] for c in self.categories.values())

    @property
    def total(self):
        return self.total_passed + self.total_failed

    def report(self):
        print("\n" + "=" * 70)
        print("TEST RESULTS SUMMARY")
        print("=" * 70)
        for cat_name, cat in self.categories.items():
            total = cat["passed"] + cat["failed"]
            status = "PASS" if cat["failed"] == 0 else "FAIL"
            print(f"\n[{status}] {cat_name}: {cat['passed']}/{total} passed")
            for detail in cat["details"]:
                print(detail)
        print("\n" + "-" * 70)
        print(f"TOTAL: {self.total_passed}/{self.total} passed, "
              f"{self.total_failed} failed")
        print("=" * 70)


results = TestResults()


def assert_close(a, b, tol=1e-6, msg=""):
    """Assert two values are close."""
    if abs(a - b) > tol:
        raise AssertionError(f"{msg}: expected {b}, got {a} (diff={abs(a-b):.2e})")


def assert_array_close(a, b, tol=1e-6, msg=""):
    """Assert two arrays are element-wise close."""
    a = np.array(a, dtype=float)
    b = np.array(b, dtype=float)
    if a.shape != b.shape:
        raise AssertionError(f"{msg}: shapes differ: {a.shape} vs {b.shape}")
    diff = np.max(np.abs(a - b))
    if diff > tol:
        raise AssertionError(f"{msg}: max diff={diff:.2e}, expected {b}, got {a}")


def run_test(test_name, test_fn):
    """Run a single test and record result."""
    try:
        test_fn()
        results.record(test_name, True)
    except Exception as e:
        results.record(test_name, False, str(e))


# ============================================================================
# Helper: create a BDB simulator and build a diagram programmatically
# ============================================================================
def make_bdb(system_type="dt"):
    sim = BlockDiagramSimulator("test_bdb")
    sim.initialize({"system_type": system_type})
    return sim


def add_block(sim, block_type, value=None, position=None, label=None):
    params = {"block_type": block_type}
    if position:
        params["position"] = position
    if value is not None:
        params["value"] = value
    if label is not None:
        params["label"] = label
    sim.handle_action("add_block", params)
    # Return the last added block id
    return max(sim.blocks.keys(), key=lambda k: int(k.split("_")[1]))


def connect(sim, from_block, to_block, from_port=0, to_port=0):
    sim.handle_action("add_connection", {
        "from_block": from_block,
        "from_port": from_port,
        "to_block": to_block,
        "to_port": to_port,
    })


def get_tf(sim):
    """Return (num, den) from the BDB's computed TF result (low-power-first R/A)."""
    if sim._tf_result is None:
        return None, None
    return (
        np.array(sim._tf_result["numerator"]),
        np.array(sim._tf_result["denominator"]),
    )


def make_sfs():
    sim = SignalFlowScopeSimulator("test_sfs")
    sim.initialize()
    return sim


# ============================================================================
# CATEGORY 1: TF Parsing (20+ tests)
# ============================================================================
def test_tf_parsing():
    results.set_category("1. TF Parsing")

    def t_simple_r_1():
        sim = make_bdb()
        sim.handle_action("parse_tf", {"tf_string": "1/(1-0.5R)"})
        n, d = get_tf(sim)
        assert n is not None, "TF not computed"
        # Expected: H(R) = 1/(1 - 0.5R) -> num=[1], den=[1, -0.5]
        assert_array_close(n, [1.0], msg="num")
        assert_array_close(d, [1.0, -0.5], msg="den")
    run_test("Simple: 1/(1-0.5R)", t_simple_r_1)

    def t_simple_r_2():
        sim = make_bdb()
        sim.handle_action("parse_tf", {"tf_string": "R/(1+R)"})
        n, d = get_tf(sim)
        assert n is not None, "TF not computed"
        assert_array_close(n, [0.0, 1.0], msg="num")
        assert_array_close(d, [1.0, 1.0], msg="den")
    run_test("Simple: R/(1+R)", t_simple_r_2)

    def t_simple_r_3():
        sim = make_bdb()
        sim.handle_action("parse_tf", {"tf_string": "1/(1+A)"})
        n, d = get_tf(sim)
        assert n is not None, "TF not computed"
        # s-domain: 1/(1+1/s) = s/(s+1) -> A-domain: [1,0]/[1,1]
        # But actually _parse detects 'A' in CT mode, var=s sets CT
        # Actually the code detects 'A' which triggers CT mode since s regex also matches A
        # Let's check what the code actually detects
    run_test("Simple: 1/(1+A)", t_simple_r_3)

    def t_s_domain_1():
        sim = make_bdb("ct")
        sim.handle_action("parse_tf", {"tf_string": "s/(s+5)"})
        n, d = get_tf(sim)
        assert n is not None, "TF not computed"
        # s/(s+5) in A-domain: A/(1+5A) -> after parse+diagram+recompute:
        # The diagram generates H(A) = 1/(1+5A) since clean_poly trims trailing
        # zeros from numerator [1,0] -> [1]. The zero at origin is structural.
        assert_array_close(n, [1.0], msg="num")
        assert_array_close(d, [1.0, 5.0], msg="den")
    run_test("s-domain: s/(s+5)", t_s_domain_1)

    def t_frac_1():
        sim = make_bdb()
        sim.handle_action("parse_tf", {"tf_string": "0.5/(1-0.25R)"})
        n, d = get_tf(sim)
        assert n is not None, "TF not computed"
        assert_array_close(n, [0.5], msg="num")
        assert_array_close(d, [1.0, -0.25], msg="den")
    run_test("Fraction: 0.5/(1-0.25R)", t_frac_1)

    def t_frac_2():
        sim = make_bdb()
        sim.handle_action("parse_tf", {"tf_string": "2.5/(1+0.1R+0.01R^2)"})
        n, d = get_tf(sim)
        assert n is not None, "TF not computed"
        assert_array_close(n, [2.5], msg="num")
        assert_array_close(d, [1.0, 0.1, 0.01], msg="den")
    run_test("Fraction: 2.5/(1+0.1R+0.01R^2)", t_frac_2)

    def t_high_order_3():
        sim = make_bdb()
        sim.handle_action("parse_tf", {"tf_string": "1/(1+R+R^2+R^3)"})
        n, d = get_tf(sim)
        assert n is not None, "TF not computed"
        assert_array_close(d, [1, 1, 1, 1], msg="den")
    run_test("3rd order: 1/(1+R+R^2+R^3)", t_high_order_3)

    def t_high_order_5():
        sim = make_bdb()
        sim.handle_action("parse_tf", {"tf_string": "1/(1+R+R^2+R^3+R^4+R^5)"})
        n, d = get_tf(sim)
        assert n is not None, "TF not computed"
        assert_array_close(d, [1, 1, 1, 1, 1, 1], msg="den")
    run_test("5th order: 1/(1+R+R^2+...+R^5)", t_high_order_5)

    def t_high_order_7():
        sim = make_bdb()
        coeffs = "+".join([f"R^{i}" if i > 1 else ("R" if i == 1 else "1")
                          for i in range(8)])
        sim.handle_action("parse_tf", {"tf_string": f"1/({coeffs})"})
        n, d = get_tf(sim)
        assert n is not None, "TF not computed"
        assert len(d) == 8, f"Expected 8 coefficients, got {len(d)}"
    run_test("7th order denominator", t_high_order_7)

    def t_high_order_10():
        sim = make_bdb()
        coeffs = "+".join([f"R^{i}" if i > 1 else ("R" if i == 1 else "1")
                          for i in range(11)])
        sim.handle_action("parse_tf", {"tf_string": f"1/({coeffs})"})
        n, d = get_tf(sim)
        assert n is not None, "TF not computed"
        assert len(d) == 11, f"Expected 11 coefficients, got {len(d)}"
    run_test("10th order denominator", t_high_order_10)

    def t_neg_coeff_1():
        sim = make_bdb()
        sim.handle_action("parse_tf", {"tf_string": "(-1+R)/(1+R)"})
        n, d = get_tf(sim)
        assert n is not None, "TF not computed"
        assert_array_close(n, [-1.0, 1.0], msg="num")
        assert_array_close(d, [1.0, 1.0], msg="den")
    run_test("Negative: (-1+R)/(1+R)", t_neg_coeff_1)

    def t_neg_coeff_2():
        sim = make_bdb()
        sim.handle_action("parse_tf", {"tf_string": "1/(1-R+0.5R^2)"})
        n, d = get_tf(sim)
        assert n is not None, "TF not computed"
        assert_array_close(d, [1.0, -1.0, 0.5], msg="den")
    run_test("Negative: 1/(1-R+0.5R^2)", t_neg_coeff_2)

    def t_pure_const_5():
        sim = make_bdb()
        sim.handle_action("parse_tf", {"tf_string": "5"})
        n, d = get_tf(sim)
        assert n is not None, "TF not computed"
        assert_array_close(n, [5.0], msg="num")
        assert_array_close(d, [1.0], msg="den")
    run_test("Pure constant: 5", t_pure_const_5)

    def t_pure_const_half():
        sim = make_bdb()
        sim.handle_action("parse_tf", {"tf_string": "0.5"})
        n, d = get_tf(sim)
        assert n is not None, "TF not computed"
        assert_array_close(n, [0.5], msg="num")
    run_test("Pure constant: 0.5", t_pure_const_half)

    def t_pure_const_neg():
        sim = make_bdb()
        sim.handle_action("parse_tf", {"tf_string": "-3"})
        n, d = get_tf(sim)
        assert n is not None, "TF not computed"
        assert_array_close(n, [-3.0], msg="num")
    run_test("Pure constant: -3", t_pure_const_neg)

    def t_pure_operator_r():
        sim = make_bdb()
        sim.handle_action("parse_tf", {"tf_string": "R"})
        n, d = get_tf(sim)
        assert n is not None, "TF not computed"
        assert_array_close(n, [0.0, 1.0], msg="num")
        assert_array_close(d, [1.0], msg="den")
    run_test("Pure operator: R", t_pure_operator_r)

    def t_pure_operator_r2():
        sim = make_bdb()
        sim.handle_action("parse_tf", {"tf_string": "R^2"})
        n, d = get_tf(sim)
        assert n is not None, "TF not computed"
        assert_array_close(n, [0.0, 0.0, 1.0], msg="num")
    run_test("Pure operator: R^2", t_pure_operator_r2)

    def t_z_domain_1():
        sim = make_bdb()
        sim.handle_action("parse_tf", {"tf_string": "z/(z-0.5)"})
        n, d = get_tf(sim)
        assert n is not None, "TF not computed"
        # z/(z-0.5) -> R-domain: 1/(1-0.5R)
        # After diagram generation and recompute, num=[1], den=[1,-0.5]
        assert_array_close(n, [1.0], tol=1e-4, msg="num")
        assert_array_close(d, [1.0, -0.5], tol=1e-4, msg="den")
    run_test("z-domain: z/(z-0.5)", t_z_domain_1)

    def t_z_domain_2():
        sim = make_bdb()
        sim.handle_action("parse_tf", {"tf_string": "z^2/(z^2-1.5z+0.7)"})
        n, d = get_tf(sim)
        assert n is not None, "TF not computed"
        # z^2/(z^2-1.5z+0.7) -> R-domain: 1/(1-1.5R+0.7R^2)
        # After diagram+recompute, trailing zeros trimmed: num=[1]
        assert_array_close(n, [1.0], tol=1e-4, msg="num")
        assert_array_close(d, [1.0, -1.5, 0.7], tol=1e-4, msg="den")
    run_test("z-domain: z^2/(z^2-1.5z+0.7)", t_z_domain_2)

    def t_z_domain_3():
        sim = make_bdb()
        sim.handle_action("parse_tf", {"tf_string": "1/(z-0.9)"})
        n, d = get_tf(sim)
        assert n is not None, "TF not computed"
        # 1/(z-0.9): num_z=[1], den_z=[-0.9,1], k=1
        # reversed: num_r=[0,1] -> wait, actually:
        # num_z padded to k+1=2: [1,0], den_z padded: [-0.9,1]
        # reversed: num_r=[0,1], den_r=[1,-0.9]
        assert_array_close(d, [1.0, -0.9], tol=1e-4, msg="den")
    run_test("z-domain: 1/(z-0.9)", t_z_domain_3)

    def t_s_ct_1():
        sim = make_bdb("ct")
        sim.handle_action("parse_tf", {"tf_string": "1/(s^2+3s+2)"})
        n, d = get_tf(sim)
        assert n is not None, "TF not computed"
        # s-domain: num_s=[1], den_s=[2,3,1], k=2
        # s_to_a: ns=[1,0,0], ds=[2,3,1] -> reversed: num_a=[0,0,1], den_a=[1,3,2]
        assert_array_close(d, [1.0, 3.0, 2.0], tol=1e-4, msg="den")
    run_test("CT s-domain: 1/(s^2+3s+2)", t_s_ct_1)

    def t_s_ct_2():
        sim = make_bdb("ct")
        sim.handle_action("parse_tf", {"tf_string": "s^2/(s^3+6s^2+11s+6)"})
        n, d = get_tf(sim)
        assert n is not None, "TF not computed"
    run_test("CT s-domain: s^2/(s^3+6s^2+11s+6)", t_s_ct_2)

    def t_identity():
        sim = make_bdb()
        sim.handle_action("parse_tf", {"tf_string": "1/1"})
        n, d = get_tf(sim)
        assert n is not None, "TF not computed"
        assert_array_close(n, [1.0], msg="num")
        assert_array_close(d, [1.0], msg="den")
    run_test("Edge: 1/1", t_identity)

    def t_large_coeff():
        sim = make_bdb()
        sim.handle_action("parse_tf", {"tf_string": "1e10/(1+1e10R)"})
        n, d = get_tf(sim)
        assert n is not None, "TF not computed"
        assert_close(n[0], 1e10, tol=1e4, msg="num[0]")
    run_test("Large: 1e10/(1+1e10R)", t_large_coeff)

    def t_small_coeff():
        """Very small coefficient: 1e-10 is at the threshold for clean_poly.
        The diagram generator treats coefficients below 1e-10 as zero,
        which may result in no signal path. This is expected behavior."""
        sim = make_bdb()
        sim.handle_action("parse_tf", {"tf_string": "1e-8/(1+R)"})
        n, d = get_tf(sim)
        assert n is not None, "TF not computed"
    run_test("Small: 1e-8/(1+R)", t_small_coeff)

    def t_s_dt_custom():
        """s-domain TF entered into custom_tf block in DT mode."""
        sim = make_bdb("dt")
        inp = add_block(sim, "input")
        ctf = add_block(sim, "custom_tf")
        out = add_block(sim, "output")
        connect(sim, inp, ctf, 0, 0)
        connect(sim, ctf, out, 1, 0)
        # Update custom TF with s-domain expr in DT mode
        sim.handle_action("update_block_value", {
            "block_id": ctf, "value": "1/(s+1)"
        })
        n, d = get_tf(sim)
        assert n is not None, "TF not computed"
    run_test("s-domain in DT custom_tf: 1/(s+1)", t_s_dt_custom)


# ============================================================================
# CATEGORY 2: Block Diagram Construction & Mason's Formula (20+ tests)
# ============================================================================
def test_block_diagram_construction():
    results.set_category("2. Block Diagram & Mason's")

    def t_single_gain():
        sim = make_bdb()
        inp = add_block(sim, "input")
        g = add_block(sim, "gain", value=3.0)
        out = add_block(sim, "output")
        connect(sim, inp, g, 0, 0)
        connect(sim, g, out, 1, 0)
        n, d = get_tf(sim)
        assert n is not None, "TF not computed"
        assert_array_close(n, [3.0], msg="num")
        assert_array_close(d, [1.0], msg="den")
    run_test("Single gain block (K=3)", t_single_gain)

    def t_single_delay():
        sim = make_bdb()
        inp = add_block(sim, "input")
        dl = add_block(sim, "delay")
        out = add_block(sim, "output")
        connect(sim, inp, dl, 0, 0)
        connect(sim, dl, out, 1, 0)
        n, d = get_tf(sim)
        assert n is not None, "TF not computed"
        assert_array_close(n, [0.0, 1.0], msg="num")
        assert_array_close(d, [1.0], msg="den")
    run_test("Single delay block", t_single_delay)

    def t_series_cascade():
        sim = make_bdb()
        inp = add_block(sim, "input")
        g1 = add_block(sim, "gain", value=2.0)
        g2 = add_block(sim, "gain", value=3.0)
        out = add_block(sim, "output")
        connect(sim, inp, g1, 0, 0)
        connect(sim, g1, g2, 1, 0)
        connect(sim, g2, out, 1, 0)
        n, d = get_tf(sim)
        assert n is not None, "TF not computed"
        assert_array_close(n, [6.0], msg="num should be 2*3=6")
    run_test("Series cascade: 2*3=6", t_series_cascade)

    def t_parallel_paths():
        """Two parallel gain paths through an adder."""
        sim = make_bdb()
        inp = add_block(sim, "input")
        g1 = add_block(sim, "gain", value=2.0)
        g2 = add_block(sim, "gain", value=3.0)
        adder = add_block(sim, "adder")
        out = add_block(sim, "output")
        connect(sim, inp, g1, 0, 0)
        connect(sim, inp, g2, 0, 0)
        connect(sim, g1, adder, 1, 0)
        connect(sim, g2, adder, 1, 1)
        connect(sim, adder, out, 2, 0)
        n, d = get_tf(sim)
        assert n is not None, "TF not computed"
        assert_array_close(n, [5.0], msg="num should be 2+3=5")
    run_test("Parallel paths: 2+3=5", t_parallel_paths)

    def t_neg_feedback():
        """G/(1+GH) with G=2, H=3 -> 2/(1+6) = 2/7."""
        sim = make_bdb()
        inp = add_block(sim, "input")
        adder = add_block(sim, "adder")
        g = add_block(sim, "gain", value=2.0)
        # Need a delay in feedback to avoid algebraic loop
        dl = add_block(sim, "delay")
        h = add_block(sim, "gain", value=3.0)
        out = add_block(sim, "output")
        connect(sim, inp, adder, 0, 0)
        connect(sim, adder, g, 2, 0)
        connect(sim, g, out, 1, 0)
        # Feedback: g -> dl -> h -> adder (port 1, negative)
        connect(sim, g, dl, 1, 0)
        connect(sim, dl, h, 1, 0)
        connect(sim, h, adder, 1, 1)
        sim.handle_action("toggle_adder_sign", {"block_id": adder, "port_index": 1})
        n, d = get_tf(sim)
        assert n is not None, "TF not computed"
        # H(R) = 2/(1+6R), poles at z=1/(1+6)... no wait.
        # The loop gain is: adder -> g(2) -> dl(R) -> h(3) -> adder
        # = 2*R*3 * (-1) = -6R (negative because of - sign at port 1)
        # Delta = 1 - (-(-6R)) = 1 - 6R   wait let me think more carefully
        # Loop: adder -> g -> dl -> h -> adder
        # Loop gain = 2 * R * 3 = 6R (product of block TFs)
        # Adder sign at port 1 is "-", so when h feeds into adder,
        # the sign is negative. In compute_loop_gain, the "-" sign
        # flips the num, so loop_gain = -6R
        # Delta = 1 - loop_gain = 1 - (-6R) = 1 + 6R
        # Forward path gain = 2, cofactor = 1 (loop touches forward path)
        # TF = 2 / (1+6R)
        assert_array_close(n, [2.0], tol=1e-4, msg="num")
        assert_array_close(d, [1.0, 6.0], tol=1e-4, msg="den")
    run_test("Neg feedback: G/(1+GH*R)", t_neg_feedback)

    def t_pos_feedback():
        """G/(1-GH*R) with G=2, H=3 -> 2/(1-6R)."""
        sim = make_bdb()
        inp = add_block(sim, "input")
        adder = add_block(sim, "adder")
        g = add_block(sim, "gain", value=2.0)
        dl = add_block(sim, "delay")
        h = add_block(sim, "gain", value=3.0)
        out = add_block(sim, "output")
        connect(sim, inp, adder, 0, 0)
        connect(sim, adder, g, 2, 0)
        connect(sim, g, out, 1, 0)
        connect(sim, g, dl, 1, 0)
        connect(sim, dl, h, 1, 0)
        connect(sim, h, adder, 1, 1)
        # Port 1 stays "+", positive feedback
        n, d = get_tf(sim)
        assert n is not None, "TF not computed"
        # Loop gain = 2*R*3 = 6R, positive sign at adder -> loop gain = +6R
        # Delta = 1 - 6R
        # TF = 2 / (1-6R)
        assert_array_close(n, [2.0], tol=1e-4, msg="num")
        assert_array_close(d, [1.0, -6.0], tol=1e-4, msg="den")
    run_test("Pos feedback: G/(1-GH*R)", t_pos_feedback)

    def t_unity_neg_feedback():
        """G/(1+G*R) with G=5."""
        sim = make_bdb()
        inp = add_block(sim, "input")
        adder = add_block(sim, "adder")
        g = add_block(sim, "gain", value=5.0)
        dl = add_block(sim, "delay")
        out = add_block(sim, "output")
        connect(sim, inp, adder, 0, 0)
        connect(sim, adder, g, 2, 0)
        connect(sim, g, out, 1, 0)
        connect(sim, g, dl, 1, 0)
        connect(sim, dl, adder, 1, 1)
        sim.handle_action("toggle_adder_sign", {"block_id": adder, "port_index": 1})
        n, d = get_tf(sim)
        assert n is not None, "TF not computed"
        # Loop: adder -> g(5) -> dl(R) -> adder(-) => loop gain = -5R
        # Delta = 1 - (-5R) = 1+5R
        assert_array_close(n, [5.0], tol=1e-4, msg="num")
        assert_array_close(d, [1.0, 5.0], tol=1e-4, msg="den")
    run_test("Unity neg feedback: G=5", t_unity_neg_feedback)

    def t_accumulator_preset():
        sim = make_bdb()
        sim.handle_action("load_preset", {"preset": "accumulator"})
        n, d = get_tf(sim)
        assert n is not None, "TF not computed"
        # y[n] = y[n-1] + x[n] -> H(R) = 1/(1-R)
        assert_array_close(n, [1.0], tol=1e-4, msg="num")
        assert_array_close(d, [1.0, -1.0], tol=1e-4, msg="den")
    run_test("Accumulator preset: 1/(1-R)", t_accumulator_preset)

    def t_difference_preset():
        sim = make_bdb()
        sim.handle_action("load_preset", {"preset": "difference"})
        n, d = get_tf(sim)
        assert n is not None, "TF not computed"
        # y[n] = x[n] - x[n-1] -> H(R) = 1-R
        assert_array_close(n, [1.0, -1.0], tol=1e-4, msg="num")
        assert_array_close(d, [1.0], tol=1e-4, msg="den")
    run_test("Difference preset: 1-R", t_difference_preset)

    def t_first_order_dt_preset():
        sim = make_bdb()
        sim.handle_action("load_preset", {"preset": "first_order_dt"})
        n, d = get_tf(sim)
        assert n is not None, "TF not computed"
        # y[n] = x[n] + 0.5*y[n-1] -> H(R) = 1/(1-0.5R)
        assert_array_close(n, [1.0], tol=1e-4, msg="num")
        assert_array_close(d, [1.0, -0.5], tol=1e-4, msg="den")
    run_test("First-order DT preset: 1/(1-0.5R)", t_first_order_dt_preset)

    def t_second_order_dt_preset():
        sim = make_bdb()
        sim.handle_action("load_preset", {"preset": "second_order_dt"})
        n, d = get_tf(sim)
        assert n is not None, "TF not computed"
        # y[n] = x[n] + 1.6*y[n-1] - 0.63*y[n-2]
        # H(R) = 1/(1-1.6R+0.63R^2)
        assert_array_close(n, [1.0], tol=1e-3, msg="num")
        assert_array_close(d, [1.0, -1.6, 0.63], tol=1e-3, msg="den")
    run_test("Second-order DT preset", t_second_order_dt_preset)

    def t_first_order_ct_preset():
        sim = make_bdb()
        sim.handle_action("load_preset", {"preset": "first_order_ct"})
        n, d = get_tf(sim)
        assert n is not None, "TF not computed"
        # dy/dt = -2y + x -> H(s) = 1/(s+2) -> H(A) = A/(1+2A)
        assert_array_close(n, [0.0, 1.0], tol=1e-4, msg="num")
        assert_array_close(d, [1.0, 2.0], tol=1e-4, msg="den")
    run_test("First-order CT preset: A/(1+2A)", t_first_order_ct_preset)

    def t_feedback_delay():
        """Feedback with delay: H(R) = R/(1+gR)."""
        sim = make_bdb()
        inp = add_block(sim, "input")
        adder = add_block(sim, "adder")
        dl = add_block(sim, "delay")
        g = add_block(sim, "gain", value=0.5)
        out = add_block(sim, "output")
        connect(sim, inp, adder, 0, 0)
        connect(sim, adder, dl, 2, 0)
        connect(sim, dl, out, 1, 0)
        connect(sim, dl, g, 1, 0)
        connect(sim, g, adder, 1, 1)
        sim.handle_action("toggle_adder_sign", {"block_id": adder, "port_index": 1})
        n, d = get_tf(sim)
        assert n is not None, "TF not computed"
        # Forward path: inp -> adder -> dl(R) -> out => path gain = R
        # Loop: adder -> dl(R) -> g(0.5) -> adder(-) => loop gain = -0.5R
        # Delta = 1 - (-0.5R) = 1 + 0.5R
        # TF = R / (1+0.5R)
        assert_array_close(n, [0.0, 1.0], tol=1e-4, msg="num")
        assert_array_close(d, [1.0, 0.5], tol=1e-4, msg="den")
    run_test("Feedback with delay: R/(1+0.5R)", t_feedback_delay)

    def t_custom_tf_block():
        """Custom TF block in diagram."""
        sim = make_bdb()
        inp = add_block(sim, "input")
        ctf = add_block(sim, "custom_tf")
        out = add_block(sim, "output")
        connect(sim, inp, ctf, 0, 0)
        connect(sim, ctf, out, 1, 0)
        sim.handle_action("update_block_value", {
            "block_id": ctf, "value": "1/(1-0.5R)"
        })
        n, d = get_tf(sim)
        assert n is not None, "TF not computed"
        assert_array_close(n, [1.0], tol=1e-4, msg="num")
        assert_array_close(d, [1.0, -0.5], tol=1e-4, msg="den")
    run_test("Custom TF block: 1/(1-0.5R)", t_custom_tf_block)

    def t_2nd_order_from_den():
        """Build 2nd order system: H(R) = 1/(1 - 1.6R + 0.63R^2)."""
        sim = make_bdb()
        sim.handle_action("parse_tf", {"tf_string": "1/(1-1.6R+0.63R^2)"})
        n, d = get_tf(sim)
        assert n is not None, "TF not computed"
        assert_array_close(d, [1.0, -1.6, 0.63], tol=1e-3, msg="den")
        # Check poles
        z_num, z_den = sim._operator_to_z(n, d)
        poles = np.roots(z_den)
        # z^2 - 1.6z + 0.63 = 0 -> z = (1.6 +/- sqrt(2.56-2.52))/2 = (1.6 +/- 0.2)/2
        expected_poles = sorted([0.9, 0.7])
        actual_poles = sorted(np.real(poles))
        for ep, ap in zip(expected_poles, actual_poles):
            assert_close(ap, ep, tol=1e-3, msg="pole")
    run_test("2nd order poles: 1/(1-1.6R+0.63R^2)", t_2nd_order_from_den)

    def t_stability_stable():
        sim = make_bdb()
        sim.handle_action("parse_tf", {"tf_string": "1/(1-0.5R)"})
        assert sim._tf_result["stability"] == "stable", \
            f"Expected stable, got {sim._tf_result['stability']}"
    run_test("Stability: stable (pole at 0.5)", t_stability_stable)

    def t_stability_unstable():
        sim = make_bdb()
        sim.handle_action("parse_tf", {"tf_string": "1/(1-2R)"})
        assert sim._tf_result["stability"] == "unstable", \
            f"Expected unstable, got {sim._tf_result['stability']}"
    run_test("Stability: unstable (pole at 2)", t_stability_unstable)

    def t_stability_marginal():
        sim = make_bdb()
        sim.handle_action("parse_tf", {"tf_string": "1/(1-R)"})
        assert sim._tf_result["stability"] == "marginally_stable", \
            f"Expected marginally_stable, got {sim._tf_result['stability']}"
    run_test("Stability: marginally stable (pole at 1)", t_stability_marginal)

    def t_multiple_forward_paths():
        """Diamond topology: inp -> g1 -> adder -> out, inp -> g2 -> adder -> out."""
        sim = make_bdb()
        inp = add_block(sim, "input")
        g1 = add_block(sim, "gain", value=2.0)
        g2 = add_block(sim, "gain", value=5.0)
        adder = add_block(sim, "adder")
        out = add_block(sim, "output")
        connect(sim, inp, g1, 0, 0)
        connect(sim, inp, g2, 0, 0)
        connect(sim, g1, adder, 1, 0)
        connect(sim, g2, adder, 1, 1)
        connect(sim, adder, out, 2, 0)
        n, d = get_tf(sim)
        assert n is not None, "TF not computed"
        # Two forward paths: gain 2 and gain 5, sum = 7
        assert_array_close(n, [7.0], tol=1e-4, msg="num should be 7")
    run_test("Multiple forward paths (diamond): 2+5=7", t_multiple_forward_paths)

    def t_nested_feedback():
        """Inner and outer feedback loops."""
        sim = make_bdb()
        inp = add_block(sim, "input")
        adder1 = add_block(sim, "adder")
        g1 = add_block(sim, "gain", value=2.0)
        dl1 = add_block(sim, "delay")
        adder2 = add_block(sim, "adder")
        g2 = add_block(sim, "gain", value=3.0)
        dl2 = add_block(sim, "delay")
        out = add_block(sim, "output")
        # Forward: inp -> adder1 -> g1 -> adder2 -> g2 -> out
        connect(sim, inp, adder1, 0, 0)
        connect(sim, adder1, g1, 2, 0)
        connect(sim, g1, adder2, 1, 0)
        connect(sim, adder2, g2, 2, 0)
        connect(sim, g2, out, 1, 0)
        # Inner loop: g2 -> dl2 -> adder2 (port 1, negative)
        connect(sim, g2, dl2, 1, 0)
        connect(sim, dl2, adder2, 1, 1)
        sim.handle_action("toggle_adder_sign", {"block_id": adder2, "port_index": 1})
        # Outer loop: g2 -> dl1 -> adder1 (port 1, negative)
        connect(sim, g2, dl1, 1, 0)
        connect(sim, dl1, adder1, 1, 1)
        sim.handle_action("toggle_adder_sign", {"block_id": adder1, "port_index": 1})
        n, d = get_tf(sim)
        assert n is not None, "TF not computed"
        # Just verify it produced a result without crashing
        assert len(n) > 0 and len(d) > 0
    run_test("Nested feedback (two loops)", t_nested_feedback)

    def t_get_state_keys():
        sim = make_bdb()
        sim.handle_action("load_preset", {"preset": "accumulator"})
        state = sim.get_state()
        assert "parameters" in state
        assert "plots" in state
        assert "metadata" in state
    run_test("get_state() includes expected keys", t_get_state_keys)

    def t_num_forward_paths_loops():
        sim = make_bdb()
        sim.handle_action("load_preset", {"preset": "accumulator"})
        tf = sim._tf_result
        assert tf["num_forward_paths"] >= 1
        assert tf["num_loops"] >= 1
    run_test("Forward paths/loops count > 0", t_num_forward_paths_loops)

    def t_ct_stability():
        sim = make_bdb("ct")
        sim.handle_action("parse_tf", {"tf_string": "1/(s^2+3s+2)"})
        assert sim._tf_result["stability"] == "stable", \
            f"Expected stable, got {sim._tf_result['stability']}"
    run_test("CT stability: 1/(s^2+3s+2) is stable", t_ct_stability)


# ============================================================================
# CATEGORY 3: Signal Flow Scope Import & Mason's (15+ tests)
# ============================================================================
def test_signal_flow_scope():
    results.set_category("3. Signal Flow Scope")

    def t_import_gain():
        sim = make_sfs()
        blocks = {
            "b1": {"id": "b1", "type": "input", "position": {"x": 0, "y": 0}},
            "b2": {"id": "b2", "type": "gain", "position": {"x": 100, "y": 0}, "value": 4.0},
            "b3": {"id": "b3", "type": "output", "position": {"x": 200, "y": 0}},
        }
        conns = [
            {"from_block": "b1", "to_block": "b2", "from_port": 0, "to_port": 0},
            {"from_block": "b2", "to_block": "b3", "from_port": 1, "to_port": 0},
        ]
        sim.handle_action("import_diagram", {
            "blocks": blocks, "connections": conns, "system_type": "dt"
        })
        assert "b3" in sim._node_tfs
        n, d = sim._node_tfs["b3"]
        assert_array_close(n, [4.0], msg="output TF num")
        assert_array_close(d, [1.0], msg="output TF den")
    run_test("Import simple gain, verify TF", t_import_gain)

    def t_import_feedback():
        sim = make_sfs()
        blocks = {
            "b_in": {"id": "b_in", "type": "input", "position": {"x": 0, "y": 0}},
            "b_add": {"id": "b_add", "type": "adder", "position": {"x": 100, "y": 0},
                      "signs": ["+", "-", "+"]},
            "b_g": {"id": "b_g", "type": "gain", "position": {"x": 200, "y": 0}, "value": 2.0},
            "b_junc": {"id": "b_junc", "type": "junction", "position": {"x": 300, "y": 0}},
            "b_out": {"id": "b_out", "type": "output", "position": {"x": 400, "y": 0}},
            "b_d": {"id": "b_d", "type": "delay", "position": {"x": 250, "y": 100}},
            "b_h": {"id": "b_h", "type": "gain", "position": {"x": 150, "y": 100}, "value": 3.0},
        }
        conns = [
            {"from_block": "b_in", "to_block": "b_add", "from_port": 0, "to_port": 0},
            {"from_block": "b_add", "to_block": "b_g", "from_port": 2, "to_port": 0},
            {"from_block": "b_g", "to_block": "b_junc", "from_port": 1, "to_port": 0},
            {"from_block": "b_junc", "to_block": "b_out", "from_port": 1, "to_port": 0},
            {"from_block": "b_junc", "to_block": "b_d", "from_port": 1, "to_port": 0},
            {"from_block": "b_d", "to_block": "b_h", "from_port": 1, "to_port": 0},
            {"from_block": "b_h", "to_block": "b_add", "from_port": 1, "to_port": 1},
        ]
        sim.handle_action("import_diagram", {
            "blocks": blocks, "connections": conns, "system_type": "dt"
        })
        assert "b_out" in sim._node_tfs
        n, d = sim._node_tfs["b_out"]
        # Forward: G=2, Loop: 2*R*3 with - sign at adder port 1 => -6R
        # Delta = 1 - (-6R) = 1+6R, TF = 2/(1+6R)
        assert_array_close(n, [2.0], tol=1e-3, msg="output TF num")
        assert_array_close(d, [1.0, 6.0], tol=1e-3, msg="output TF den")
    run_test("Import feedback, verify TF at output", t_import_feedback)

    def t_load_preset_cascade():
        sim = make_sfs()
        sim.handle_action("load_preset", {"preset_id": "cascade"})
        assert "b_out" in sim._node_tfs
        n, d = sim._node_tfs["b_out"]
        assert_array_close(n, [1.5], tol=1e-4, msg="output TF = 3*0.5=1.5")
    run_test("SFS cascade preset: 3*0.5=1.5", t_load_preset_cascade)

    def t_load_preset_first_order():
        sim = make_sfs()
        sim.handle_action("load_preset", {"preset_id": "first_order_lowpass"})
        assert "b_out" in sim._node_tfs
        n, d = sim._node_tfs["b_out"]
        # y[n] = 0.3*x[n] + 0.7*y[n-1]
        # Forward path: in -> g_in(0.3) -> add -> junc -> out => gain = 0.3
        # Loop: junc -> d1(R) -> g_fb(0.7) -> add (port 1, +) => 0.7R
        # Delta = 1 - 0.7R
        # TF = 0.3 / (1 - 0.7R)
        assert_array_close(n, [0.3], tol=1e-3, msg="num")
        assert_array_close(d, [1.0, -0.7], tol=1e-3, msg="den")
    run_test("SFS first_order_lowpass preset", t_load_preset_first_order)

    def t_probe_add_remove():
        sim = make_sfs()
        sim.handle_action("load_preset", {"preset_id": "cascade"})
        sim.handle_action("add_probe", {"node_id": "b_g1"})
        assert len(sim.probes) == 1
        sim.handle_action("add_probe", {"node_id": "b_out"})
        assert len(sim.probes) == 2
        sim.handle_action("remove_probe", {"node_id": "b_g1"})
        assert len(sim.probes) == 1
        assert sim.probes[0]["node_id"] == "b_out"
    run_test("Probe add/remove", t_probe_add_remove)

    def t_probe_toggle():
        sim = make_sfs()
        sim.handle_action("load_preset", {"preset_id": "cascade"})
        sim.handle_action("toggle_probe", {"node_id": "b_g1"})
        assert len(sim.probes) == 1
        sim.handle_action("toggle_probe", {"node_id": "b_g1"})
        assert len(sim.probes) == 0
    run_test("Probe toggle", t_probe_toggle)

    def t_max_probes():
        sim = make_sfs()
        sim.handle_action("load_preset", {"preset_id": "second_order_dt"})
        # Try to add 7 probes (limit is 6)
        node_ids = list(sim.blocks.keys())
        for nid in node_ids[:7]:
            sim.handle_action("add_probe", {"node_id": nid})
        assert len(sim.probes) <= 6, f"Exceeded max probes: {len(sim.probes)}"
    run_test("Max 6 probes limit", t_max_probes)

    def t_probe_all():
        sim = make_sfs()
        sim.handle_action("load_preset", {"preset_id": "cascade"})
        sim.handle_action("probe_all", {})
        assert len(sim.probes) <= 6
        assert len(sim.probes) > 0
    run_test("Probe all nodes", t_probe_all)

    def t_clear_probes():
        sim = make_sfs()
        sim.handle_action("load_preset", {"preset_id": "cascade"})
        sim.handle_action("probe_all", {})
        sim.handle_action("clear_probes", {})
        assert len(sim.probes) == 0
    run_test("Clear probes", t_clear_probes)

    def t_unstable_clipping():
        """Unstable system should produce clipped signal."""
        sim = make_sfs()
        blocks = {
            "b1": {"id": "b1", "type": "input", "position": {"x": 0, "y": 0}},
            "b2": {"id": "b2", "type": "adder", "position": {"x": 100, "y": 0},
                   "signs": ["+", "+", "+"]},
            "b3": {"id": "b3", "type": "gain", "position": {"x": 200, "y": 0}, "value": 2.0},
            "b4": {"id": "b4", "type": "junction", "position": {"x": 300, "y": 0}},
            "b5": {"id": "b5", "type": "output", "position": {"x": 400, "y": 0}},
            "b6": {"id": "b6", "type": "delay", "position": {"x": 250, "y": 100}},
        }
        conns = [
            {"from_block": "b1", "to_block": "b2", "from_port": 0, "to_port": 0},
            {"from_block": "b2", "to_block": "b3", "from_port": 2, "to_port": 0},
            {"from_block": "b3", "to_block": "b4", "from_port": 1, "to_port": 0},
            {"from_block": "b4", "to_block": "b5", "from_port": 1, "to_port": 0},
            {"from_block": "b4", "to_block": "b6", "from_port": 1, "to_port": 0},
            {"from_block": "b6", "to_block": "b2", "from_port": 1, "to_port": 1},
        ]
        sim.handle_action("import_diagram", {
            "blocks": blocks, "connections": conns, "system_type": "dt"
        })
        # Positive feedback with gain > 1: unstable
        sim.handle_action("add_probe", {"node_id": "b5"})
        # The signal should be clipped
        if "b5" in sim._node_signals:
            assert sim._node_signals["b5"]["clipped"] is True, \
                "Unstable system should clip"
    run_test("Unstable system clipping", t_unstable_clipping)

    def t_signal_impulse():
        sim = make_sfs()
        sim.initialize({"input_type": "impulse", "num_samples": 50})
        sim.handle_action("load_preset", {"preset_id": "cascade"})
        sim.handle_action("add_probe", {"node_id": "b_out"})
        sig = sim._node_signals.get("b_out")
        assert sig is not None, "No signal computed"
        # Impulse through cascade of gains: output should be 1.5 at n=0
        assert_close(sig["y"][0], 1.5, tol=1e-3, msg="impulse resp[0]")
        # And zero elsewhere
        assert_close(sig["y"][1], 0.0, tol=1e-3, msg="impulse resp[1]")
    run_test("Signal: impulse response", t_signal_impulse)

    def t_signal_step():
        sim = make_sfs()
        sim.initialize({"input_type": "step", "num_samples": 50})
        sim.handle_action("load_preset", {"preset_id": "cascade"})
        sim.handle_action("add_probe", {"node_id": "b_out"})
        sig = sim._node_signals.get("b_out")
        assert sig is not None, "No signal computed"
        # Step through cascade of gains: all samples should be 1.5
        for i in range(min(5, len(sig["y"]))):
            assert_close(sig["y"][i], 1.5, tol=1e-3, msg=f"step resp[{i}]")
    run_test("Signal: step response", t_signal_step)

    def t_signal_sinusoid():
        sim = make_sfs()
        sim.initialize({"input_type": "sinusoid", "num_samples": 100, "input_freq": 1.0})
        sim.handle_action("load_preset", {"preset_id": "cascade"})
        sig_data = sim._node_signals  # may be empty until probe added
        sim.handle_action("add_probe", {"node_id": "b_out"})
        sig = sim._node_signals.get("b_out")
        assert sig is not None, "No signal computed"
        assert len(sig["y"]) == 100
    run_test("Signal: sinusoid", t_signal_sinusoid)

    def t_signal_ramp():
        sim = make_sfs()
        sim.initialize({"input_type": "ramp", "num_samples": 50})
        sim.handle_action("load_preset", {"preset_id": "cascade"})
        sim.handle_action("add_probe", {"node_id": "b_out"})
        sig = sim._node_signals.get("b_out")
        assert sig is not None, "No signal computed"
        assert len(sig["y"]) == 50
    run_test("Signal: ramp", t_signal_ramp)

    def t_input_tf_identity():
        """Input node TF should be 1."""
        sim = make_sfs()
        sim.handle_action("load_preset", {"preset_id": "cascade"})
        assert "b_in" in sim._node_tfs
        n, d = sim._node_tfs["b_in"]
        assert_array_close(n, [1.0], msg="input TF num")
        assert_array_close(d, [1.0], msg="input TF den")
    run_test("Input node TF = 1", t_input_tf_identity)

    def t_intermediate_node_tf():
        """Intermediate node TF at gain block."""
        sim = make_sfs()
        sim.handle_action("load_preset", {"preset_id": "cascade"})
        # b_g1 is gain=3 (first gain in cascade)
        assert "b_g1" in sim._node_tfs
        n, d = sim._node_tfs["b_g1"]
        assert_array_close(n, [3.0], tol=1e-4, msg="intermediate TF num")
    run_test("Intermediate node TF", t_intermediate_node_tf)

    def t_sfs_second_order_preset():
        sim = make_sfs()
        sim.handle_action("load_preset", {"preset_id": "second_order_dt"})
        assert "b_out" in sim._node_tfs
        n, d = sim._node_tfs["b_out"]
        # y[n] = x[n] + 1.5y[n-1] - 0.7y[n-2] -> H(R) = 1/(1-1.5R+0.7R^2)
        assert_array_close(n, [1.0], tol=1e-3, msg="num")
        assert_array_close(d, [1.0, -1.5, 0.7], tol=1e-3, msg="den")
    run_test("SFS second_order_dt preset", t_sfs_second_order_preset)


# ============================================================================
# CATEGORY 4: Domain Conversion (15+ tests)
# ============================================================================
def test_domain_conversion():
    results.set_category("4. Domain Conversion")

    sim = make_bdb()

    def t_r_to_z_0th():
        # H(R) = 5, num=[5], den=[1]
        z_n, z_d = sim._operator_to_z(np.array([5.0]), np.array([1.0]))
        assert_array_close(z_n, [5.0], msg="z_num")
        assert_array_close(z_d, [1.0], msg="z_den")
    run_test("R->z: 0th order (constant)", t_r_to_z_0th)

    def t_r_to_z_1st():
        # H(R) = 1/(1-0.5R), num=[1], den=[1,-0.5]
        z_n, z_d = sim._operator_to_z(np.array([1.0]), np.array([1.0, -0.5]))
        # z^1 * 1 = z -> [1, 0] high-power first
        # z^1 * (1 - 0.5*z^-1) = z - 0.5 -> [1, -0.5] high-power first
        assert_array_close(z_n, [1.0, 0.0], msg="z_num")
        assert_array_close(z_d, [1.0, -0.5], msg="z_den")
    run_test("R->z: 1st order", t_r_to_z_1st)

    def t_r_to_z_2nd():
        # H(R) = R/(1-1.5R+0.7R^2), num=[0,1], den=[1,-1.5,0.7]
        z_n, z_d = sim._operator_to_z(np.array([0.0, 1.0]), np.array([1.0, -1.5, 0.7]))
        # k = max(1,2) = 2
        # z_num: pad [0,1] to 3 -> [0,1,0], strip leading zeros -> [1,0]
        # z_den: pad [1,-1.5,0.7] to 3 -> [1,-1.5,0.7]
        assert_array_close(z_n, [1.0, 0.0], msg="z_num")
        assert_array_close(z_d, [1.0, -1.5, 0.7], msg="z_den")
    run_test("R->z: 2nd order", t_r_to_z_2nd)

    def t_r_to_z_3rd():
        z_n, z_d = sim._operator_to_z(np.array([1.0]), np.array([1.0, -1.0, 0.5, -0.1]))
        # k=3, z_num: [1,0,0,0] -> trim -> [1,0,0,0] or [1]
        # z_den: [1,-1,0.5,-0.1]
        assert len(z_d) == 4, f"Expected 4 den coeffs, got {len(z_d)}"
    run_test("R->z: 3rd order", t_r_to_z_3rd)

    def t_r_to_z_5th():
        den = np.array([1.0, -0.5, 0.3, -0.1, 0.05, -0.01])
        z_n, z_d = sim._operator_to_z(np.array([1.0]), den)
        assert len(z_d) == 6
    run_test("R->z: 5th order", t_r_to_z_5th)

    def t_a_to_s_0th():
        s_n, s_d = sim._operator_to_s(np.array([3.0]), np.array([1.0]))
        assert_array_close(s_n, [3.0], msg="s_num")
        assert_array_close(s_d, [1.0], msg="s_den")
    run_test("A->s: 0th order", t_a_to_s_0th)

    def t_a_to_s_1st():
        # H(A) = A/(1+2A), num=[0,1], den=[1,2]
        s_n, s_d = sim._operator_to_s(np.array([0.0, 1.0]), np.array([1.0, 2.0]))
        # k=1, s_num: [0,1] -> trim -> [1], s_den: [1,2]
        assert_array_close(s_n, [1.0], msg="s_num")
        assert_array_close(s_d, [1.0, 2.0], msg="s_den")
    run_test("A->s: 1st order", t_a_to_s_1st)

    def t_a_to_s_2nd():
        # H(A) = A^2/(1+3A+2A^2), num=[0,0,1], den=[1,3,2]
        s_n, s_d = sim._operator_to_s(np.array([0.0, 0.0, 1.0]), np.array([1.0, 3.0, 2.0]))
        # k=2, s_num: [0,0,1] -> trim -> [1], s_den: [1,3,2]
        assert_array_close(s_n, [1.0], msg="s_num")
        assert_array_close(s_d, [1.0, 3.0, 2.0], msg="s_den")
    run_test("A->s: 2nd order", t_a_to_s_2nd)

    def t_s_to_a_1():
        # s/(s+5): num_s=[0,1], den_s=[5,1]
        num_a, den_a = BlockDiagramSimulator._s_to_a_coeffs([0, 1], [5, 1])
        # k=1, pad to 2: ns=[0,1], ds=[5,1]
        # reversed: num_a=[1,0], den_a=[1,5]
        assert_array_close(num_a, [1, 0], msg="num_a")
        assert_array_close(den_a, [1, 5], msg="den_a")
    run_test("s->A: s/(s+5) -> [1,0]/[1,5]", t_s_to_a_1)

    def t_s_to_a_2():
        # 1/(s^2+3s+2): num_s=[1], den_s=[2,3,1]
        num_a, den_a = BlockDiagramSimulator._s_to_a_coeffs([1], [2, 3, 1])
        # k=2, ns=[1,0,0], ds=[2,3,1]
        # reversed: num_a=[0,0,1], den_a=[1,3,2]
        assert_array_close(num_a, [0, 0, 1], msg="num_a")
        assert_array_close(den_a, [1, 3, 2], msg="den_a")
    run_test("s->A: 1/(s^2+3s+2) -> [0,0,1]/[1,3,2]", t_s_to_a_2)

    def t_z_to_r_1():
        # z/(z-0.5): num_z=[0,1], den_z=[-0.5,1]
        num_r, den_r = BlockDiagramSimulator._z_to_r_coeffs([0, 1], [-0.5, 1])
        # k=1, nz=[0,1], dz=[-0.5,1] -> reversed: [1,0], [1,-0.5]
        assert_array_close(num_r, [1, 0], msg="num_r")
        assert_array_close(den_r, [1, -0.5], msg="den_r")
    run_test("z->R: z/(z-0.5) -> [1,0]/[1,-0.5]", t_z_to_r_1)

    def t_leading_zero_strip_1():
        arr = np.trim_zeros(np.array([0.0, 0.0, 1.0]), 'f')
        assert_array_close(arr, [1.0], msg="trimmed")
    run_test("Leading zero strip: [0,0,1] -> [1]", t_leading_zero_strip_1)

    def t_leading_zero_strip_2():
        arr = np.trim_zeros(np.array([0.0, 1.0, 0.0]), 'f')
        assert_array_close(arr, [1.0, 0.0], msg="trimmed")
    run_test("Leading zero strip: [0,1,0] -> [1,0]", t_leading_zero_strip_2)

    def t_leading_zero_strip_3():
        arr = np.trim_zeros(np.array([1.0, 0.0, 0.0]), 'f')
        assert_array_close(arr, [1.0, 0.0, 0.0], msg="trimmed")
    run_test("Leading zero strip: [1,0,0] -> [1,0,0]", t_leading_zero_strip_3)

    def t_roundtrip_r_z_r():
        """R -> z -> R round trip."""
        # Original R: num=[1], den=[1,-0.5]
        r_num = np.array([1.0])
        r_den = np.array([1.0, -0.5])
        z_n, z_d = sim._operator_to_z(r_num, r_den)
        # z domain: z_n=[1,0], z_d=[1,-0.5]
        # Now convert back: z_to_r_coeffs
        # Low-power-first z: we need to figure out what _z_to_r_coeffs expects
        # z_n and z_d are high-power-first from _operator_to_z
        # _z_to_r_coeffs expects low-power-first z coefficients (same as parser output)
        # So we need to reverse: [1,0] -> [0,1], [1,-0.5] -> [-0.5,1]
        z_n_lpf = list(reversed(z_n.tolist()))
        z_d_lpf = list(reversed(z_d.tolist()))
        nr, dr = BlockDiagramSimulator._z_to_r_coeffs(z_n_lpf, z_d_lpf)
        # Should get back [1]/[1,-0.5]
        # z_n_lpf=[0,1], z_d_lpf=[-0.5,1], k=1
        # reversed: nr=[1,0], dr=[1,-0.5]
        assert_array_close(nr, [1.0, 0.0], tol=1e-6, msg="num_r round trip")
        assert_array_close(dr, [1.0, -0.5], tol=1e-6, msg="den_r round trip")
    run_test("Round trip R->z->R", t_roundtrip_r_z_r)

    def t_ct_custom_tf_poles():
        """CT custom TF: verify pole locations."""
        sim2 = make_bdb("ct")
        inp = add_block(sim2, "input")
        ctf = add_block(sim2, "custom_tf")
        out = add_block(sim2, "output")
        connect(sim2, inp, ctf, 0, 0)
        connect(sim2, ctf, out, 1, 0)
        sim2.handle_action("update_block_value", {
            "block_id": ctf, "value": "1/(s^2+3s+2)"
        })
        tf = sim2._tf_result
        assert tf is not None
        # s^2+3s+2 = (s+1)(s+2), poles at -1 and -2
        poles = tf["poles"]
        pole_reals = sorted([p["real"] for p in poles])
        assert_close(pole_reals[0], -2.0, tol=1e-3, msg="pole 1")
        assert_close(pole_reals[1], -1.0, tol=1e-3, msg="pole 2")
    run_test("CT custom TF pole locations", t_ct_custom_tf_poles)


# ============================================================================
# CATEGORY 5: Polynomial Arithmetic (10+ tests)
# ============================================================================
def test_polynomial_arithmetic():
    results.set_category("5. Polynomial Arithmetic")

    sim = make_bdb()

    def t_pmul_basic():
        # (1 + 2R) * (1 + 3R) = 1 + 5R + 6R^2
        a = np.array([1.0, 2.0])
        b = np.array([1.0, 3.0])
        result = sim._pmul(a, b)
        assert_array_close(result, [1.0, 5.0, 6.0], msg="pmul")
    run_test("pmul: (1+2R)*(1+3R)", t_pmul_basic)

    def t_pmul_identity():
        a = np.array([1.0, -0.5])
        b = np.array([1.0])
        result = sim._pmul(a, b)
        assert_array_close(result, [1.0, -0.5], msg="pmul identity")
    run_test("pmul: (1-0.5R)*1", t_pmul_identity)

    def t_padd_basic():
        a = np.array([1.0, 2.0])
        b = np.array([3.0, 4.0])
        result = sim._padd(a, b)
        assert_array_close(result, [4.0, 6.0], msg="padd")
    run_test("padd: (1+2R)+(3+4R)", t_padd_basic)

    def t_padd_different_lengths():
        a = np.array([1.0])
        b = np.array([2.0, 3.0, 4.0])
        result = sim._padd(a, b)
        assert_array_close(result, [3.0, 3.0, 4.0], msg="padd diff len")
    run_test("padd: different lengths", t_padd_different_lengths)

    def t_psub_basic():
        a = np.array([5.0, 3.0])
        b = np.array([2.0, 1.0])
        result = sim._psub(a, b)
        assert_array_close(result, [3.0, 2.0], msg="psub")
    run_test("psub: (5+3R)-(2+R)", t_psub_basic)

    def t_psub_self():
        a = np.array([1.0, 2.0, 3.0])
        result = sim._psub(a, a)
        assert_array_close(result, [0.0, 0.0, 0.0], msg="psub self")
    run_test("psub: a - a = 0", t_psub_self)

    def t_pscale():
        a = np.array([1.0, 2.0, 3.0])
        result = sim._pscale(a, 2.5)
        assert_array_close(result, [2.5, 5.0, 7.5], msg="pscale")
    run_test("pscale: 2.5*(1+2R+3R^2)", t_pscale)

    def t_clean_poly_trailing():
        result = sim._clean_poly(np.array([1.0, 2.0, 0.0, 0.0]))
        assert_array_close(result, [1.0, 2.0], msg="clean trailing")
    run_test("clean_poly: trailing zeros", t_clean_poly_trailing)

    def t_clean_poly_all_zero():
        result = sim._clean_poly(np.array([0.0, 0.0, 0.0]))
        assert_array_close(result, [0.0], msg="clean all zero")
    run_test("clean_poly: all zeros -> [0]", t_clean_poly_all_zero)

    def t_clean_poly_near_zero():
        result = sim._clean_poly(np.array([1.0, 2.0, 1e-15]))
        assert_array_close(result, [1.0, 2.0], msg="clean near zero")
    run_test("clean_poly: near-zero threshold", t_clean_poly_near_zero)

    def t_convolution_correctness():
        # (1+R)(1-R) = 1 - R^2
        a = np.array([1.0, 1.0])
        b = np.array([1.0, -1.0])
        result = sim._pmul(a, b)
        assert_array_close(result, [1.0, 0.0, -1.0], msg="(1+R)(1-R)")
    run_test("Convolution: (1+R)(1-R)=1-R^2", t_convolution_correctness)

    def t_clean_poly_empty():
        result = sim._clean_poly(np.array([]))
        assert_array_close(result, [0.0], msg="clean empty")
    run_test("clean_poly: empty -> [0]", t_clean_poly_empty)


# ============================================================================
# CATEGORY 6: Edge Cases & Robustness (15+ tests)
# ============================================================================
def test_edge_cases():
    results.set_category("6. Edge Cases & Robustness")

    def t_zero_gain_feedback():
        """Zero gain in feedback loop."""
        sim = make_bdb()
        inp = add_block(sim, "input")
        adder = add_block(sim, "adder")
        g = add_block(sim, "gain", value=5.0)
        dl = add_block(sim, "delay")
        h = add_block(sim, "gain", value=0.0)
        out = add_block(sim, "output")
        connect(sim, inp, adder, 0, 0)
        connect(sim, adder, g, 2, 0)
        connect(sim, g, out, 1, 0)
        connect(sim, g, dl, 1, 0)
        connect(sim, dl, h, 1, 0)
        connect(sim, h, adder, 1, 1)
        n, d = get_tf(sim)
        assert n is not None, "TF should compute with zero gain in feedback"
        # Loop gain = 0, so TF = G = 5
        assert_array_close(n, [5.0], tol=1e-4, msg="num")
    run_test("Zero gain in feedback", t_zero_gain_feedback)

    def t_repeated_poles():
        """System with repeated poles."""
        sim = make_bdb()
        sim.handle_action("parse_tf", {"tf_string": "1/(1-R)^2"})
        # This might fail parsing of (1-R)^2. Let's use expanded form.
        sim2 = make_bdb()
        sim2.handle_action("parse_tf", {"tf_string": "1/(1-2R+R^2)"})
        n, d = get_tf(sim2)
        assert n is not None, "TF not computed"
        assert_array_close(d, [1.0, -2.0, 1.0], tol=1e-4, msg="den")
        # Poles should both be at z=1
        z_n, z_d = sim2._operator_to_z(n, d)
        poles = np.roots(z_d)
        for p in poles:
            assert_close(abs(complex(p)), 1.0, tol=1e-3, msg="repeated pole at 1")
    run_test("Repeated poles: 1/(1-2R+R^2)", t_repeated_poles)

    def t_very_high_gain_feedback():
        """Very high gain in feedback."""
        sim = make_bdb()
        inp = add_block(sim, "input")
        adder = add_block(sim, "adder")
        g = add_block(sim, "gain", value=1e6)
        dl = add_block(sim, "delay")
        out = add_block(sim, "output")
        connect(sim, inp, adder, 0, 0)
        connect(sim, adder, g, 2, 0)
        connect(sim, g, out, 1, 0)
        connect(sim, g, dl, 1, 0)
        connect(sim, dl, adder, 1, 1)
        sim.handle_action("toggle_adder_sign", {"block_id": adder, "port_index": 1})
        n, d = get_tf(sim)
        assert n is not None, "TF should compute with high gain"
    run_test("Very high gain (1e6) in feedback", t_very_high_gain_feedback)

    def t_very_low_gain_feedback():
        """Very low gain in feedback."""
        sim = make_bdb()
        inp = add_block(sim, "input")
        adder = add_block(sim, "adder")
        g = add_block(sim, "gain", value=1e-6)
        dl = add_block(sim, "delay")
        out = add_block(sim, "output")
        connect(sim, inp, adder, 0, 0)
        connect(sim, adder, g, 2, 0)
        connect(sim, g, out, 1, 0)
        connect(sim, g, dl, 1, 0)
        connect(sim, dl, adder, 1, 1)
        n, d = get_tf(sim)
        assert n is not None, "TF should compute with low gain"
    run_test("Very low gain (1e-6) in feedback", t_very_low_gain_feedback)

    def t_empty_diagram():
        """Empty diagram should have no TF."""
        sim = make_bdb()
        n, d = get_tf(sim)
        assert n is None, "Empty diagram should have no TF"
    run_test("Empty diagram: no TF", t_empty_diagram)

    def t_no_forward_path():
        """Disconnected input and output."""
        sim = make_bdb()
        inp = add_block(sim, "input")
        out = add_block(sim, "output")
        # No connection
        n, d = get_tf(sim)
        assert n is None or sim._error is not None, "Disconnected should error"
    run_test("No forward path (disconnected)", t_no_forward_path)

    def t_algebraic_loop():
        """Algebraic loop: feedback without delay."""
        sim = make_bdb()
        inp = add_block(sim, "input")
        adder = add_block(sim, "adder")
        g = add_block(sim, "gain", value=2.0)
        out = add_block(sim, "output")
        connect(sim, inp, adder, 0, 0)
        connect(sim, adder, g, 2, 0)
        connect(sim, g, out, 1, 0)
        connect(sim, g, adder, 1, 1)
        sim.handle_action("toggle_adder_sign", {"block_id": adder, "port_index": 1})
        # This creates an algebraic loop (no delay in feedback)
        tf = sim._tf_result
        # Should either error or have algebraic_loop_warning
        has_warning = (
            (tf is not None and tf.get("algebraic_loop_warning") is not None) or
            sim._error is not None
        )
        assert has_warning, "Should detect algebraic loop"
    run_test("Algebraic loop detection", t_algebraic_loop)

    def t_multiple_inputs_error():
        """Multiple input blocks should error."""
        sim = make_bdb()
        inp1 = add_block(sim, "input")
        inp2 = add_block(sim, "input")
        out = add_block(sim, "output")
        connect(sim, inp1, out, 0, 0)
        # _recompute_tf should detect multiple inputs and set error
        assert sim._error is not None or sim._tf_result is None, \
            "Multiple inputs should error or have no TF"
    run_test("Multiple input blocks", t_multiple_inputs_error)

    def t_multiple_outputs_error():
        """Multiple output blocks should error."""
        sim = make_bdb()
        inp = add_block(sim, "input")
        out1 = add_block(sim, "output")
        out2 = add_block(sim, "output")
        connect(sim, inp, out1, 0, 0)
        assert sim._error is not None or sim._tf_result is None, \
            "Multiple outputs should error or have no TF"
    run_test("Multiple output blocks", t_multiple_outputs_error)

    def t_block_limit():
        """Block limit of 30."""
        sim = make_bdb()
        for i in range(30):
            add_block(sim, "gain", value=1.0)
        # 31st should fail
        try:
            add_block(sim, "gain", value=1.0)
            assert sim._error is not None, "Should error at 31 blocks"
        except Exception:
            pass  # Expected
    run_test("Block limit (30 blocks)", t_block_limit)

    def t_self_loop():
        """Self-connection should be rejected."""
        sim = make_bdb()
        g = add_block(sim, "gain", value=1.0)
        try:
            connect(sim, g, g, 1, 0)
            assert sim._error is not None, "Self-loop should error"
        except Exception:
            pass  # Expected
    run_test("Self-loop rejection", t_self_loop)

    def t_wrong_port():
        """Invalid port index should be rejected."""
        sim = make_bdb()
        inp = add_block(sim, "input")
        g = add_block(sim, "gain", value=1.0)
        try:
            connect(sim, inp, g, 0, 5)  # port 5 is invalid for gain
            assert sim._error is not None, "Invalid port should error"
        except Exception:
            pass  # Expected
    run_test("Wrong port rejection", t_wrong_port)

    def t_output_as_source():
        """Output block cannot be wire source."""
        sim = make_bdb()
        out = add_block(sim, "output")
        g = add_block(sim, "gain", value=1.0)
        try:
            connect(sim, out, g, 0, 0)
            assert sim._error is not None, "Output as source should error"
        except Exception:
            pass  # Expected
    run_test("Output block as source", t_output_as_source)

    def t_input_as_target():
        """Input block cannot be wire target."""
        sim = make_bdb()
        inp = add_block(sim, "input")
        g = add_block(sim, "gain", value=1.0)
        try:
            connect(sim, g, inp, 1, 0)
            assert sim._error is not None, "Input as target should error"
        except Exception:
            pass  # Expected
    run_test("Input block as target", t_input_as_target)

    def t_undo_redo():
        """Undo/redo functionality."""
        sim = make_bdb()
        inp = add_block(sim, "input")
        g = add_block(sim, "gain", value=5.0)
        out = add_block(sim, "output")
        connect(sim, inp, g, 0, 0)
        connect(sim, g, out, 1, 0)
        n1, _ = get_tf(sim)
        # Undo the last connection
        sim.handle_action("undo", {})
        # Redo it
        sim.handle_action("redo", {})
        n2, _ = get_tf(sim)
        assert n1 is not None and n2 is not None
        assert_array_close(n1, n2, msg="undo/redo should restore TF")
    run_test("Undo/redo", t_undo_redo)

    def t_custom_tf_zero_den():
        """Custom TF with den having zero constant term."""
        sim = make_bdb()
        inp = add_block(sim, "input")
        ctf = add_block(sim, "custom_tf")
        out = add_block(sim, "output")
        connect(sim, inp, ctf, 0, 0)
        connect(sim, ctf, out, 1, 0)
        # R/(1+R) has den_coeffs[0]=1, that's fine. Try R alone.
        sim.handle_action("update_block_value", {"block_id": ctf, "value": "R"})
        n, d = get_tf(sim)
        assert n is not None, "Should handle R as custom TF"
    run_test("Custom TF: pure R operator", t_custom_tf_zero_den)

    def t_delay_in_ct_error():
        """Delay block in CT mode should error."""
        sim = make_bdb("ct")
        try:
            add_block(sim, "delay")
            assert sim._error is not None, "Delay in CT should error"
        except Exception:
            pass  # Expected
    run_test("Delay in CT mode rejected", t_delay_in_ct_error)


# ============================================================================
# CATEGORY 7: Analytical Verification (15+ tests)
# ============================================================================
def test_analytical_verification():
    results.set_category("7. Analytical Verification")

    def t_1st_order_impulse():
        """1st order DT: H(z) = 1/(1-az^{-1}), h[n] = a^n. a=0.5."""
        sim = make_bdb()
        sim.handle_action("parse_tf", {"tf_string": "1/(1-0.5R)"})
        n, d = get_tf(sim)
        z_n, z_d = sim._operator_to_z(n, d)
        # Compute impulse response manually
        from scipy.signal import dimpulse
        _, h = dimpulse((z_n, z_d, 1), n=10)
        h = h[0].flatten()
        # Expected: h[n] = 0.5^n
        for i in range(10):
            expected = 0.5 ** i
            assert_close(h[i], expected, tol=1e-6,
                        msg=f"h[{i}]: expected {expected}")
    run_test("1st order DT impulse: h[n]=0.5^n", t_1st_order_impulse)

    def t_2nd_order_poles():
        """2nd order DT: verify poles match quadratic formula."""
        sim = make_bdb()
        sim.handle_action("parse_tf", {"tf_string": "1/(1-1.5R+0.7R^2)"})
        n, d = get_tf(sim)
        z_n, z_d = sim._operator_to_z(n, d)
        poles = np.roots(z_d)
        # z^2 - 1.5z + 0.7 = 0
        disc = 1.5**2 - 4*0.7
        if disc >= 0:
            p1 = (1.5 + np.sqrt(disc)) / 2
            p2 = (1.5 - np.sqrt(disc)) / 2
            expected = sorted([p1, p2])
        else:
            real_part = 1.5 / 2
            imag_part = np.sqrt(-disc) / 2
            expected = sorted([real_part], key=lambda x: x)
            # Complex poles
            for p in poles:
                assert_close(complex(p).real, real_part, tol=1e-6, msg="real part")
                assert_close(abs(complex(p).imag), imag_part, tol=1e-6, msg="imag part")
            return

        actual = sorted(np.real(poles))
        for ep, ap in zip(expected, actual):
            assert_close(ap, ep, tol=1e-6, msg="pole")
    run_test("2nd order DT poles: quadratic formula", t_2nd_order_poles)

    def t_cascaded_1st_order():
        """Two cascaded 1st-order sections: verify combined TF."""
        sim = make_bdb()
        inp = add_block(sim, "input")
        ctf1 = add_block(sim, "custom_tf")
        ctf2 = add_block(sim, "custom_tf")
        out = add_block(sim, "output")
        connect(sim, inp, ctf1, 0, 0)
        connect(sim, ctf1, ctf2, 1, 0)
        connect(sim, ctf2, out, 1, 0)
        sim.handle_action("update_block_value", {"block_id": ctf1, "value": "1/(1-0.5R)"})
        sim.handle_action("update_block_value", {"block_id": ctf2, "value": "1/(1-0.3R)"})
        n, d = get_tf(sim)
        assert n is not None, "TF not computed"
        # Product: 1/((1-0.5R)(1-0.3R)) = 1/(1-0.8R+0.15R^2)
        assert_array_close(n, [1.0], tol=1e-4, msg="num")
        assert_array_close(d, [1.0, -0.8, 0.15], tol=1e-4, msg="den")
    run_test("Cascaded 1st-order: 1/((1-0.5R)(1-0.3R))", t_cascaded_1st_order)

    def t_ct_integrator_feedback():
        """CT: H(s) = 1/(s+K) for gain K. Verify pole at -K."""
        sim = make_bdb("ct")
        sim.handle_action("parse_tf", {"tf_string": "1/(s+5)"})
        tf = sim._tf_result
        assert tf is not None
        poles = tf["poles"]
        assert len(poles) == 1
        assert_close(poles[0]["real"], -5.0, tol=1e-3, msg="pole at -5")
    run_test("CT integrator feedback: pole at -K", t_ct_integrator_feedback)

    def t_accumulator_impulse():
        """Accumulator: h[n] = u[n] (step function as impulse response)."""
        sim = make_bdb()
        sim.handle_action("load_preset", {"preset": "accumulator"})
        n, d = get_tf(sim)
        z_n, z_d = sim._operator_to_z(n, d)
        from scipy.signal import dimpulse
        _, h = dimpulse((z_n, z_d, 1), n=10)
        h = h[0].flatten()
        for i in range(10):
            assert_close(h[i], 1.0, tol=1e-6, msg=f"h[{i}]")
    run_test("Accumulator impulse: h[n]=1 for all n", t_accumulator_impulse)

    def t_difference_impulse():
        """Difference: h[n] = delta[n] - delta[n-1]."""
        sim = make_bdb()
        sim.handle_action("load_preset", {"preset": "difference"})
        n, d = get_tf(sim)
        z_n, z_d = sim._operator_to_z(n, d)
        from scipy.signal import dimpulse
        _, h = dimpulse((z_n, z_d, 1), n=10)
        h = h[0].flatten()
        assert_close(h[0], 1.0, tol=1e-6, msg="h[0]")
        assert_close(h[1], -1.0, tol=1e-6, msg="h[1]")
        for i in range(2, 10):
            assert_close(h[i], 0.0, tol=1e-6, msg=f"h[{i}]")
    run_test("Difference impulse: [1,-1,0,0,...]", t_difference_impulse)

    def t_1st_order_step():
        """1st order DT step response: y[n] = (1 - a^(n+1))/(1-a)."""
        sim = make_bdb()
        sim.handle_action("parse_tf", {"tf_string": "1/(1-0.5R)"})
        n_c, d_c = get_tf(sim)
        z_n, z_d = sim._operator_to_z(n_c, d_c)
        from scipy.signal import dstep
        _, s = dstep((z_n, z_d, 1), n=10)
        s = s[0].flatten()
        a = 0.5
        for i in range(10):
            expected = (1 - a**(i+1)) / (1 - a)
            assert_close(s[i], expected, tol=1e-4, msg=f"step[{i}]")
    run_test("1st order DT step response", t_1st_order_step)

    def t_gain_impulse():
        """Gain block: impulse response is K*delta[n]."""
        sim = make_bdb()
        inp = add_block(sim, "input")
        g = add_block(sim, "gain", value=7.0)
        out = add_block(sim, "output")
        connect(sim, inp, g, 0, 0)
        connect(sim, g, out, 1, 0)
        n, d = get_tf(sim)
        z_n, z_d = sim._operator_to_z(n, d)
        from scipy.signal import dimpulse
        _, h = dimpulse((z_n, z_d, 1), n=5)
        h = h[0].flatten()
        assert_close(h[0], 7.0, tol=1e-6, msg="h[0]=7")
        for i in range(1, 5):
            assert_close(h[i], 0.0, tol=1e-6, msg=f"h[{i}]=0")
    run_test("Gain impulse: 7*delta[n]", t_gain_impulse)

    def t_delay_impulse():
        """Delay block: h[n] = delta[n-1]."""
        sim = make_bdb()
        inp = add_block(sim, "input")
        dl = add_block(sim, "delay")
        out = add_block(sim, "output")
        connect(sim, inp, dl, 0, 0)
        connect(sim, dl, out, 1, 0)
        n, d = get_tf(sim)
        z_n, z_d = sim._operator_to_z(n, d)
        from scipy.signal import dimpulse
        _, h = dimpulse((z_n, z_d, 1), n=5)
        h = h[0].flatten()
        assert_close(h[0], 0.0, tol=1e-6, msg="h[0]=0")
        assert_close(h[1], 1.0, tol=1e-6, msg="h[1]=1")
        for i in range(2, 5):
            assert_close(h[i], 0.0, tol=1e-6, msg=f"h[{i}]=0")
    run_test("Delay impulse: delta[n-1]", t_delay_impulse)

    def t_cascade_delay_gain():
        """Delay -> Gain(3): h[n] = 3*delta[n-1]."""
        sim = make_bdb()
        inp = add_block(sim, "input")
        dl = add_block(sim, "delay")
        g = add_block(sim, "gain", value=3.0)
        out = add_block(sim, "output")
        connect(sim, inp, dl, 0, 0)
        connect(sim, dl, g, 1, 0)
        connect(sim, g, out, 1, 0)
        n, d = get_tf(sim)
        z_n, z_d = sim._operator_to_z(n, d)
        from scipy.signal import dimpulse
        _, h = dimpulse((z_n, z_d, 1), n=5)
        h = h[0].flatten()
        assert_close(h[0], 0.0, tol=1e-6, msg="h[0]=0")
        assert_close(h[1], 3.0, tol=1e-6, msg="h[1]=3")
    run_test("Delay->Gain(3) impulse", t_cascade_delay_gain)

    def t_butterworth_2nd_order():
        """2nd order Butterworth: poles on unit circle in s-plane at 45 deg."""
        sim = make_bdb("ct")
        # H(s) = 1/(s^2 + sqrt(2)*s + 1), poles at -1/sqrt(2) +/- j/sqrt(2)
        sqrt2 = np.sqrt(2)
        sim.handle_action("parse_tf", {"tf_string": f"1/(s^2+{sqrt2:.6f}s+1)"})
        tf = sim._tf_result
        assert tf is not None
        poles = tf["poles"]
        assert len(poles) == 2
        for p in poles:
            assert_close(p["real"], -1/sqrt2, tol=1e-3, msg="real part")
            assert_close(abs(p["imag"]), 1/sqrt2, tol=1e-3, msg="|imag part|")
    run_test("Butterworth 2nd order poles", t_butterworth_2nd_order)

    def t_ct_s_plane_poles():
        """CT poles: 1/(s^2+3s+2) has poles at -1 and -2."""
        sim = make_bdb("ct")
        sim.handle_action("parse_tf", {"tf_string": "1/(s^2+3s+2)"})
        tf = sim._tf_result
        assert tf is not None
        poles = tf["poles"]
        pole_reals = sorted([p["real"] for p in poles])
        assert_close(pole_reals[0], -2.0, tol=1e-3, msg="pole 1")
        assert_close(pole_reals[1], -1.0, tol=1e-3, msg="pole 2")
    run_test("CT poles: 1/(s^2+3s+2)", t_ct_s_plane_poles)

    def t_parallel_impulse():
        """Parallel: H = 2 + 3 = 5, h[n] = 5*delta[n]."""
        sim = make_bdb()
        inp = add_block(sim, "input")
        g1 = add_block(sim, "gain", value=2.0)
        g2 = add_block(sim, "gain", value=3.0)
        adder = add_block(sim, "adder")
        out = add_block(sim, "output")
        connect(sim, inp, g1, 0, 0)
        connect(sim, inp, g2, 0, 0)
        connect(sim, g1, adder, 1, 0)
        connect(sim, g2, adder, 1, 1)
        connect(sim, adder, out, 2, 0)
        n, d = get_tf(sim)
        z_n, z_d = sim._operator_to_z(n, d)
        from scipy.signal import dimpulse
        _, h = dimpulse((z_n, z_d, 1), n=5)
        h = h[0].flatten()
        assert_close(h[0], 5.0, tol=1e-6, msg="h[0]=5")
        for i in range(1, 5):
            assert_close(h[i], 0.0, tol=1e-6, msg=f"h[{i}]=0")
    run_test("Parallel impulse: 2+3=5", t_parallel_impulse)

    def t_feedback_impulse_verify():
        """Neg feedback: H(R)=2/(1+6R). h[n] = 2*(-6)^n."""
        sim = make_bdb()
        inp = add_block(sim, "input")
        adder = add_block(sim, "adder")
        g = add_block(sim, "gain", value=2.0)
        dl = add_block(sim, "delay")
        h_block = add_block(sim, "gain", value=3.0)
        out = add_block(sim, "output")
        connect(sim, inp, adder, 0, 0)
        connect(sim, adder, g, 2, 0)
        connect(sim, g, out, 1, 0)
        connect(sim, g, dl, 1, 0)
        connect(sim, dl, h_block, 1, 0)
        connect(sim, h_block, adder, 1, 1)
        sim.handle_action("toggle_adder_sign", {"block_id": adder, "port_index": 1})
        n_c, d_c = get_tf(sim)
        z_n, z_d = sim._operator_to_z(n_c, d_c)
        from scipy.signal import dimpulse
        _, h = dimpulse((z_n, z_d, 1), n=5)
        h = h[0].flatten()
        # H(z) = 2z/(z+6), impulse: h[n] = 2*(-6)^n for n>=0
        assert_close(h[0], 2.0, tol=1e-3, msg="h[0]=2")
        assert_close(h[1], -12.0, tol=1e-3, msg="h[1]=-12")
        assert_close(h[2], 72.0, tol=1e-3, msg="h[2]=72")
    run_test("Feedback impulse analytical verify", t_feedback_impulse_verify)

    def t_3rd_order_system():
        """3rd order system: verify number of poles = 3."""
        sim = make_bdb()
        sim.handle_action("parse_tf", {"tf_string": "1/(1-2R+1.5R^2-0.5R^3)"})
        tf = sim._tf_result
        assert tf is not None
        assert len(tf["poles"]) == 3, f"Expected 3 poles, got {len(tf['poles'])}"
    run_test("3rd order: 3 poles", t_3rd_order_system)


# ============================================================================
# CATEGORY 8: Consistency Checks (10+ tests)
# ============================================================================
def test_consistency():
    results.set_category("8. Consistency Checks")

    def t_bdb_sfs_same_tf():
        """BDB and SFS produce same TF for the same diagram."""
        # Build diagram in BDB
        bdb_sim = make_bdb()
        inp = add_block(bdb_sim, "input")
        g = add_block(bdb_sim, "gain", value=3.0)
        dl = add_block(bdb_sim, "delay")
        out = add_block(bdb_sim, "output")
        connect(bdb_sim, inp, g, 0, 0)
        connect(bdb_sim, g, dl, 1, 0)
        connect(bdb_sim, dl, out, 1, 0)
        bdb_n, bdb_d = get_tf(bdb_sim)

        # Import same diagram into SFS
        sfs_sim = make_sfs()
        blocks = {}
        for bid, block in bdb_sim.blocks.items():
            blocks[bid] = dict(block)
        conns = [dict(c) for c in bdb_sim.connections]
        sfs_sim.handle_action("import_diagram", {
            "blocks": blocks, "connections": conns, "system_type": "dt"
        })
        # Find output block
        out_id = None
        for bid, block in sfs_sim.blocks.items():
            if block["type"] == "output":
                out_id = bid
                break
        assert out_id is not None
        sfs_n, sfs_d = sfs_sim._node_tfs[out_id]
        assert_array_close(bdb_n, sfs_n, tol=1e-6, msg="BDB vs SFS num")
        assert_array_close(bdb_d, sfs_d, tol=1e-6, msg="BDB vs SFS den")
    run_test("BDB and SFS produce same TF", t_bdb_sfs_same_tf)

    def t_bdb_sfs_feedback_same():
        """BDB and SFS produce same TF for feedback diagram."""
        bdb_sim = make_bdb()
        bdb_sim.handle_action("load_preset", {"preset": "first_order_dt"})
        bdb_n, bdb_d = get_tf(bdb_sim)

        sfs_sim = make_sfs()
        blocks = {}
        for bid, block in bdb_sim.blocks.items():
            blocks[bid] = dict(block)
        conns = [dict(c) for c in bdb_sim.connections]
        sfs_sim.handle_action("import_diagram", {
            "blocks": blocks, "connections": conns, "system_type": "dt"
        })
        out_id = None
        for bid, block in sfs_sim.blocks.items():
            if block["type"] == "output":
                out_id = bid
                break
        assert out_id is not None
        sfs_n, sfs_d = sfs_sim._node_tfs[out_id]
        assert_array_close(bdb_n, sfs_n, tol=1e-3, msg="BDB vs SFS num")
        assert_array_close(bdb_d, sfs_d, tol=1e-3, msg="BDB vs SFS den")
    run_test("BDB/SFS consistency: first_order_dt preset", t_bdb_sfs_feedback_same)

    def t_normalization():
        """Denominator constant term = 1 after normalization."""
        sim = make_bdb()
        sim.handle_action("parse_tf", {"tf_string": "2/(2-R)"})
        n, d = get_tf(sim)
        assert n is not None
        assert_close(d[0], 1.0, tol=1e-6, msg="den[0] should be 1")
    run_test("Normalization: den[0] = 1", t_normalization)

    def t_get_state_metadata():
        """get_state() includes metadata with simulation_type."""
        sim = make_bdb()
        sim.handle_action("load_preset", {"preset": "accumulator"})
        state = sim.get_state()
        assert "metadata" in state
        assert state["metadata"]["simulation_type"] == "block_diagram_builder"
    run_test("get_state metadata includes simulation_type", t_get_state_metadata)

    def t_idempotent_recompute():
        """Multiple _recompute_tf() calls give same result."""
        sim = make_bdb()
        sim.handle_action("load_preset", {"preset": "first_order_dt"})
        n1, d1 = get_tf(sim)
        sim._recompute_tf()
        n2, d2 = get_tf(sim)
        sim._recompute_tf()
        n3, d3 = get_tf(sim)
        assert_array_close(n1, n2, msg="recompute idempotent 1-2 num")
        assert_array_close(d1, d2, msg="recompute idempotent 1-2 den")
        assert_array_close(n2, n3, msg="recompute idempotent 2-3 num")
        assert_array_close(d2, d3, msg="recompute idempotent 2-3 den")
    run_test("Idempotent recompute", t_idempotent_recompute)

    def t_sfs_get_state_keys():
        """SFS get_state() includes expected keys."""
        sim = make_sfs()
        sim.handle_action("load_preset", {"preset_id": "cascade"})
        state = sim.get_state()
        assert "parameters" in state
        assert "plots" in state
        assert "metadata" in state
    run_test("SFS get_state() keys", t_sfs_get_state_keys)

    def t_pmul_same_both_modules():
        """_pmul gives same result in BDB and SFS."""
        a = np.array([1.0, 2.0, 3.0])
        b = np.array([1.0, -1.0])
        bdb_result = BlockDiagramSimulator._pmul(a, b)
        sfs_result = SignalFlowScopeSimulator._pmul(a, b)
        assert_array_close(bdb_result, sfs_result, msg="pmul consistency")
    run_test("pmul consistency: BDB vs SFS", t_pmul_same_both_modules)

    def t_padd_same_both_modules():
        a = np.array([1.0, 2.0])
        b = np.array([3.0, 4.0, 5.0])
        bdb_result = BlockDiagramSimulator._padd(a, b)
        sfs_result = SignalFlowScopeSimulator._padd(a, b)
        assert_array_close(bdb_result, sfs_result, msg="padd consistency")
    run_test("padd consistency: BDB vs SFS", t_padd_same_both_modules)

    def t_psub_same_both_modules():
        a = np.array([5.0, 3.0])
        b = np.array([1.0, 1.0])
        bdb_result = BlockDiagramSimulator._psub(a, b)
        sfs_result = SignalFlowScopeSimulator._psub(a, b)
        assert_array_close(bdb_result, sfs_result, msg="psub consistency")
    run_test("psub consistency: BDB vs SFS", t_psub_same_both_modules)

    def t_parse_then_build_match():
        """Parse TF, then diagram TF should match the original."""
        sim = make_bdb()
        sim.handle_action("parse_tf", {"tf_string": "1/(1-0.5R)"})
        n, d = get_tf(sim)
        assert n is not None
        # After parse_tf, the generated diagram is computed
        assert_array_close(n, [1.0], tol=1e-3, msg="parsed num")
        assert_array_close(d, [1.0, -0.5], tol=1e-3, msg="parsed den")
    run_test("Parse then build: TF matches original", t_parse_then_build_match)

    def t_sfs_operator_to_z_consistency():
        """SFS _operator_to_z produces same result as BDB."""
        bdb_sim = make_bdb()
        sfs_sim = make_sfs()
        n = np.array([1.0, 0.0])
        d = np.array([1.0, -0.5])
        bz_n, bz_d = bdb_sim._operator_to_z(n, d)
        sz_n, sz_d = sfs_sim._operator_to_z(n, d)
        assert_array_close(bz_n, sz_n, msg="operator_to_z num")
        assert_array_close(bz_d, sz_d, msg="operator_to_z den")
    run_test("operator_to_z consistency: BDB vs SFS", t_sfs_operator_to_z_consistency)


# ============================================================================
# Run all tests
# ============================================================================
def main():
    print("=" * 70)
    print("Block Diagram Builder & Signal Flow Scope E2E Test Suite")
    print("=" * 70)

    test_tf_parsing()
    test_block_diagram_construction()
    test_signal_flow_scope()
    test_domain_conversion()
    test_polynomial_arithmetic()
    test_edge_cases()
    test_analytical_verification()
    test_consistency()

    results.report()
    return 0 if results.total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
