import requests
import json
import numpy as np

BASE = "http://localhost:8000/api/simulations/ode_laplace_solver"

def get_state(params=None):
    if params:
        r = requests.post(f"{BASE}/update", json={"params": params})
    else:
        r = requests.get(f"{BASE}/state")
    resp = r.json()
    if "data" in resp and isinstance(resp["data"], dict) and "metadata" in resp["data"]:
        return resp["data"]
    return resp

def execute_action(action, params=None):
    body = {"action": action, "params": params or {}}
    r = requests.post(f"{BASE}/execute", json=body)
    return r.json()

def step_to(n):
    """Navigate to step n from step 0"""
    execute_action("reset_steps")
    for _ in range(n):
        execute_action("next_step")
    return get_state()

def pole_to_complex(pole):
    """Convert pole dict {real, imag} or string to complex number"""
    if isinstance(pole, dict):
        return complex(pole["real"], pole["imag"])
    elif isinstance(pole, str):
        return complex(pole.replace('i','j').replace(' ',''))
    else:
        return complex(pole)

def find_plot(data, plot_id):
    """Find a plot by ID in the data"""
    for p in data["plots"]:
        if p["id"] == plot_id:
            return p
    return None


# ==========================================
# TEST 1: First-order impulse: y' + y = d(t)
# Expected: y(t) = e^(-t)u(t)
# ==========================================
print("=" * 60)
print("TEST 1: First-order impulse -- y' + y = d(t)")
data = get_state({"preset": "first_order_impulse"})
sys_info = data["metadata"]["system_info"]

poles_c = [pole_to_complex(p) for p in sys_info["poles"]]
print(f"  Poles: {poles_c}")
assert len(poles_c) == 1, f"Expected 1 pole, got {len(poles_c)}"
assert abs(poles_c[0] - (-1)) < 0.01, f"Expected pole at -1, got {poles_c[0]}"
print("  [PASS] Pole at s=-1 correct")

assert sys_info["is_stable"] == True, "Should be stable"
print("  [PASS] System is stable")

data = step_to(5)
time_plot = find_plot(data, "time_response")
assert time_plot is not None, "time_response plot not found"

t_data = np.array(time_plot["data"][0]["x"])
y_data = np.array(time_plot["data"][0]["y"])
idx_t1 = np.argmin(np.abs(t_data - 1.0))
y_at_1 = y_data[idx_t1]
expected = np.exp(-1.0)
print(f"  y(1) = {y_at_1:.4f}, expected = {expected:.4f}")
assert abs(y_at_1 - expected) < 0.05, f"y(1) mismatch: got {y_at_1}, expected {expected}"
print("  [PASS] y(1) = e^(-1) verified")

idx_t0 = np.argmin(np.abs(t_data - 0.01))
y_at_0 = y_data[idx_t0]
print(f"  y(0+) ~ {y_at_0:.4f}, expected ~ 1.0")
assert abs(y_at_0 - 1.0) < 0.1, f"y(0+) mismatch"
print("  [PASS] y(0+) ~ 1.0 verified")


# ==========================================
# TEST 2: Second-order impulse: y'' + 3y' + 2y = d(t)
# y(t) = (e^(-t) - e^(-2t))u(t)
# ==========================================
print("\n" + "=" * 60)
print("TEST 2: Second-order impulse -- y'' + 3y' + 2y = d(t)")
data = get_state({"preset": "second_order_impulse"})
sys_info = data["metadata"]["system_info"]

poles_c = [pole_to_complex(p) for p in sys_info["poles"]]
print(f"  Poles: {poles_c}")
assert len(poles_c) == 2, f"Expected 2 poles, got {len(poles_c)}"
print("  [PASS] Two poles found")

data = step_to(5)
time_plot = find_plot(data, "time_response")
assert time_plot is not None, "time_response plot not found"

t_data = np.array(time_plot["data"][0]["x"])
y_data = np.array(time_plot["data"][0]["y"])

idx_t1 = np.argmin(np.abs(t_data - 1.0))
y_at_1 = y_data[idx_t1]
expected = np.exp(-1.0) - np.exp(-2.0)
print(f"  y(1) = {y_at_1:.4f}, expected = {expected:.4f}")
assert abs(y_at_1 - expected) < 0.05, f"y(1) mismatch"
print("  [PASS] y(1) verified")

idx_t0 = np.argmin(np.abs(t_data - 0.0))
y_at_0 = y_data[idx_t0]
print(f"  y(0) = {y_at_0:.4f}, expected ~ 0")
assert abs(y_at_0) < 0.15, f"y(0) should be ~0"
print("  [PASS] y(0) ~ 0 verified")


# ==========================================
# TEST 3: Step response: y'' + 3y' + 2y = u(t)
# y(t) = (0.5 - e^(-t) + 0.5*e^(-2t))u(t)
# ==========================================
print("\n" + "=" * 60)
print("TEST 3: Step response -- y'' + 3y' + 2y = u(t)")
data = get_state({"preset": "second_order_step"})

data = step_to(5)
time_plot = find_plot(data, "time_response")
assert time_plot is not None, "time_response plot not found"

t_data = np.array(time_plot["data"][0]["x"])
y_data = np.array(time_plot["data"][0]["y"])

idx_late = np.argmin(np.abs(t_data - 7.0))
y_ss = y_data[idx_late]
print(f"  y(inf) ~ {y_ss:.4f}, expected ~ 0.5 (DC gain = 1/a0 = 1/2)")
assert abs(y_ss - 0.5) < 0.05, f"Steady state mismatch"
print("  [PASS] Steady state verified")

idx_t1 = np.argmin(np.abs(t_data - 1.0))
y_at_1 = y_data[idx_t1]
expected = 0.5 - np.exp(-1.0) + 0.5 * np.exp(-2.0)
print(f"  y(1) = {y_at_1:.4f}, expected = {expected:.4f}")
assert abs(y_at_1 - expected) < 0.05, f"y(1) mismatch"
print("  [PASS] y(1) verified")


# ==========================================
# TEST 4: Underdamped: y'' + 2y' + 5y = d(t)
# y(t) = 0.5*e^(-t)*sin(2t)*u(t)
# ==========================================
print("\n" + "=" * 60)
print("TEST 4: Underdamped -- y'' + 2y' + 5y = d(t)")
data = get_state({"preset": "underdamped"})
sys_info = data["metadata"]["system_info"]
poles_c = [pole_to_complex(p) for p in sys_info["poles"]]
print(f"  Poles: {poles_c}")
assert sys_info["is_stable"] == True
print("  [PASS] System is stable")

data = step_to(5)
time_plot = find_plot(data, "time_response")
assert time_plot is not None, "time_response plot not found"

t_data = np.array(time_plot["data"][0]["x"])
y_data = np.array(time_plot["data"][0]["y"])

t_test = np.pi / 4
idx = np.argmin(np.abs(t_data - t_test))
y_val = y_data[idx]
expected = 0.5 * np.exp(-t_test) * np.sin(2 * t_test)
print(f"  y(pi/4) = {y_val:.4f}, expected = {expected:.4f}")
assert abs(y_val - expected) < 0.05, f"y(pi/4) mismatch"
print("  [PASS] y(pi/4) verified (oscillatory response)")


# ==========================================
# TEST 5: Repeated poles: y'' + 2y' + y = d(t)
# y(t) = t*e^(-t)*u(t)
# ==========================================
print("\n" + "=" * 60)
print("TEST 5: Repeated poles -- y'' + 2y' + y = d(t)")
data = get_state({"preset": "repeated_poles"})
sys_info = data["metadata"]["system_info"]
poles_c = [pole_to_complex(p) for p in sys_info["poles"]]
print(f"  Poles: {poles_c}")

data = step_to(5)
time_plot = find_plot(data, "time_response")
assert time_plot is not None, "time_response plot not found"

t_data = np.array(time_plot["data"][0]["x"])
y_data = np.array(time_plot["data"][0]["y"])

idx_t1 = np.argmin(np.abs(t_data - 1.0))
y_at_1 = y_data[idx_t1]
expected = 1.0 * np.exp(-1.0)
print(f"  y(1) = {y_at_1:.4f}, expected = {expected:.4f}")
assert abs(y_at_1 - expected) < 0.05, f"y(1) mismatch"
print("  [PASS] y(1) = t*e^(-t)|_{t=1} verified")

idx_05 = np.argmin(np.abs(t_data - 0.5))
idx_2 = np.argmin(np.abs(t_data - 2.0))
assert y_data[idx_t1] > y_data[idx_05] and y_data[idx_t1] > y_data[idx_2], "Peak should be at t=1"
print("  [PASS] Peak at t=1 verified")


# ==========================================
# TEST 6: Third-order: y''' + 6y'' + 11y' + 6y = d(t)
# y(t) = 0.5*e^(-t) - e^(-2t) + 0.5*e^(-3t)
# ==========================================
print("\n" + "=" * 60)
print("TEST 6: Third-order -- y''' + 6y'' + 11y' + 6y = d(t)")
data = get_state({"preset": "third_order"})
sys_info = data["metadata"]["system_info"]
poles_c = [pole_to_complex(p) for p in sys_info["poles"]]
print(f"  Poles: {poles_c}")
print(f"  Order: {sys_info['order']}")
assert sys_info["order"] == 3
print("  [PASS] Third-order system confirmed")

data = step_to(5)
time_plot = find_plot(data, "time_response")
assert time_plot is not None, "time_response plot not found"

t_data = np.array(time_plot["data"][0]["x"])
y_data = np.array(time_plot["data"][0]["y"])

idx_t1 = np.argmin(np.abs(t_data - 1.0))
y_at_1 = y_data[idx_t1]
expected = 0.5 * np.exp(-1.0) - np.exp(-2.0) + 0.5 * np.exp(-3.0)
print(f"  y(1) = {y_at_1:.4f}, expected = {expected:.4f}")
assert abs(y_at_1 - expected) < 0.05, f"y(1) mismatch"
print("  [PASS] y(1) verified")


# ==========================================
# TEST 7: Exponential input: y' + 2y = e^(-t)u(t)
# y(t) = (e^(-t) - e^(-2t))u(t)
# ==========================================
print("\n" + "=" * 60)
print("TEST 7: Exponential input -- y' + 2y = e^(-t)u(t)")
data = get_state({"preset": "exponential_input"})

data = step_to(5)
time_plot = find_plot(data, "time_response")
assert time_plot is not None, "time_response plot not found"

t_data = np.array(time_plot["data"][0]["x"])
y_data = np.array(time_plot["data"][0]["y"])

idx_t1 = np.argmin(np.abs(t_data - 1.0))
y_at_1 = y_data[idx_t1]
expected = np.exp(-1.0) - np.exp(-2.0)
print(f"  y(1) = {y_at_1:.4f}, expected = {expected:.4f}")
assert abs(y_at_1 - expected) < 0.05, f"y(1) mismatch"
print("  [PASS] y(1) verified")


# ==========================================
# TEST 8: Step navigation
# ==========================================
print("\n" + "=" * 60)
print("TEST 8: Step navigation")
execute_action("reset_steps")
data = get_state()
assert data["metadata"]["current_step"] == 0, "Reset should go to step 0"
print("  [PASS] Reset to step 0")

for i in range(5):
    execute_action("next_step")
data = get_state()
assert data["metadata"]["current_step"] == 5, "Should be at step 5"
print("  [PASS] Navigated to step 5")

execute_action("next_step")
data = get_state()
assert data["metadata"]["current_step"] == 5, "Should stay at step 5"
print("  [PASS] Cannot exceed max step")

execute_action("prev_step")
data = get_state()
assert data["metadata"]["current_step"] == 4, "Should be at step 4"
print("  [PASS] Step backward works")

execute_action("reset_steps")
execute_action("show_all")
data = get_state()
assert data["metadata"]["current_step"] == 5, "Show all should go to step 5"
print("  [PASS] Show all works")


# ==========================================
# TEST 9: Custom coefficients
# ==========================================
print("\n" + "=" * 60)
print("TEST 9: Custom coefficients")
data = get_state({"preset": "custom", "output_coeffs": "1, 3, 2", "input_coeffs": "1"})
sys_info = data["metadata"]["system_info"]
print(f"  Poles: {[pole_to_complex(p) for p in sys_info['poles']]}")
print(f"  Order: {sys_info['order']}")
assert sys_info["order"] == 2, "Custom 1,3,2 should be 2nd order"
print("  [PASS] Custom coefficients parsed correctly")


# ==========================================
# TEST 10: Classical comparison toggle
# ==========================================
print("\n" + "=" * 60)
print("TEST 10: Classical comparison")
data = get_state({"preset": "second_order_impulse", "show_compare": True})
meta = data["metadata"]
assert meta.get("classical_solution") is not None, "Classical solution should be present"
assert "characteristic_eq" in meta["classical_solution"], \
    f"Missing characteristic_eq, keys: {list(meta['classical_solution'].keys())}"
assert "homogeneous_form" in meta["classical_solution"], "Missing homogeneous_form"
print(f"  Char. eq: {meta['classical_solution']['characteristic_eq']}")
print(f"  Homo. form: {meta['classical_solution']['homogeneous_form']}")
print("  [PASS] Classical comparison data present")

data = get_state({"show_compare": False})
meta = data["metadata"]
assert meta.get("classical_solution") is None, "Classical solution should be absent when toggled off"
print("  [PASS] Classical comparison toggles off correctly")


# ==========================================
# TEST 11: Cosine input via custom preset
# y' + y = cos(2t)u(t) using custom mode
# System pole: s = -1, Input poles: s = +/-2j
# Combined Y(s) has 3 poles total
# ==========================================
print("\n" + "=" * 60)
print("TEST 11: Cosine input -- y' + y = cos(2t)u(t) [custom mode]")
data = get_state({
    "preset": "custom",
    "output_coeffs": "1, 1",
    "input_coeffs": "1",
    "input_signal": "cosine",
    "omega": 2.0
})
sys_info = data["metadata"]["system_info"]
poles_c = [pole_to_complex(p) for p in sys_info["poles"]]
print(f"  Poles: {poles_c}")
print(f"  Input signal: {data['metadata'].get('input_signal_text')}")

# Should have 3 poles: -1 (system), ~+2j and ~-2j (from cosine input)
assert len(poles_c) == 3, f"Expected 3 poles (1 system + 2 input), got {len(poles_c)}"
print("  [PASS] 3 poles found (system + input)")

# Verify pole locations
sys_pole = [p for p in poles_c if abs(p.imag) < 0.1]
input_poles = [p for p in poles_c if abs(p.imag) > 1.0]
assert len(sys_pole) == 1, f"Expected 1 real system pole"
assert abs(sys_pole[0].real - (-1.0)) < 0.01, f"System pole should be at -1"
print("  [PASS] System pole at s=-1 verified")

assert len(input_poles) == 2, "Expected 2 imaginary input poles"
imag_vals = sorted([abs(p.imag) for p in input_poles])
assert abs(imag_vals[0] - 2.0) < 0.01 and abs(imag_vals[1] - 2.0) < 0.01, \
    f"Input poles should be at +/-2j, got imag parts {imag_vals}"
print("  [PASS] Input poles at s=+/-2j verified")
print("  [PASS] Cosine input produces correct pole structure")


# ==========================================
# SUMMARY
# ==========================================
print("\n" + "=" * 60)
print("ALL 11 TESTS PASSED")
print("=" * 60)
