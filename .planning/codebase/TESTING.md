# Testing Patterns

**Analysis Date:** 2026-03-27

## Test Framework

**Runner:**
- pytest (version 9.0.2 detected from bytecode cache)
- No `pytest.ini`, `setup.cfg`, or `pyproject.toml` test config found
- Tests run from `backend/` directory with `PYTHONPATH` set to include backend

**Assertion Library:**
- Plain `assert` statements (project rule: never use soft assertion wrappers)
- `numpy.testing` not used; manual `abs(a - b) < tol` patterns instead
- `np.allclose()` used in custom helpers

**Run Commands:**
```bash
# Hub validator tests (pytest, structured)
cd backend && python -m pytest tests/test_hub_validator.py -v

# E2E Block Diagram / Signal Flow tests (custom runner)
cd backend && python3 test_e2e.py

# Multi-loop topology tests (custom runner)
cd backend && python3 test_multiloop.py

# Validation benchmarks (SCOPE vs MATLAB comparison)
cd <project_root> && python -m validation.run_scope_benchmarks
cd <project_root> && python -m validation.compare
```

**No frontend tests exist.** No jest, vitest, or testing-library configured. `frontend/package.json` has no test script.

## Test File Organization

**Location:** Mixed -- no single convention enforced

- `backend/tests/test_hub_validator.py` -- pytest, in dedicated `tests/` directory
- `backend/test_e2e.py` -- custom runner, in backend root
- `backend/test_multiloop.py` -- custom runner, in backend root
- `validation/run_scope_benchmarks.py` -- benchmark harness, in `validation/` directory
- `validation/compare.py` -- SCOPE vs MATLAB comparison, in `validation/` directory

**Naming:**
- Pytest files: `test_*.py` prefix
- Custom test scripts: `test_*.py` prefix (same convention, different runner)
- Validation scripts: descriptive names (`run_scope_benchmarks.py`, `compare.py`)

## Test Structure

**Pytest Pattern (hub validator):**
```python
class TestTFFirstOrder:
    """First-order TF: G(s) = 1 / (s + 2). One real pole at -2, stable, type 0."""

    def setup_method(self) -> None:
        self.result = validate_and_enrich_control({
            "source": "tf",
            "num": [1.0],
            "den": [1.0, 2.0],
        })

    def test_success(self) -> None:
        assert self.result["success"] is True

    def test_order(self) -> None:
        d = self.result["data"]
        assert d["order"] == 1

    def test_single_real_pole(self) -> None:
        poles = self.result["data"]["poles"]
        assert len(poles) == 1
        assert abs(poles[0]["real"] - (-2.0)) < 1e-8
```

**Key patterns in pytest tests:**
- Class-based grouping: one class per scenario/system configuration
- `setup_method()` computes result once, individual `test_*` methods assert specific properties
- Descriptive class docstrings with mathematical context (transfer function, expected behavior)
- Type hints on all test methods (`: None` return type)
- Numerical tolerances: `1e-8` for exact computations, `1e-6` for computed values
- Section separators with comment blocks (`# ------- TF tests -------`)

**Custom Runner Pattern (e2e, multiloop):**
```python
# Global counters
passed = 0
failed = 0
errors = []

def check(name, condition, msg=""):
    global passed, failed
    if condition:
        passed += 1
    else:
        failed += 1
        errors.append(f"  FAIL: {name} -- {msg}")
        assert condition, f"{name} -- {msg}"

def assert_close(a, b, tol=1e-6, name="", msg=""):
    diff = abs(a - b)
    check(name, diff < tol, f"expected {b}, got {a}, diff={diff}. {msg}")

def assert_poly_close(p1, p2, tol=1e-4, name=""):
    """Compare two polynomials (low-power-first) allowing different lengths."""
    n = max(len(p1), len(p2))
    a = np.zeros(n)
    b = np.zeros(n)
    a[:len(p1)] = p1
    b[:len(p2)] = p2
    check(name, np.allclose(a, b, atol=tol), ...)
```

**Critical rule:** Custom test scripts use `assert` inside `check()` -- a green exit code alone is not proof of success. Always read stdout for internal pass/fail summaries.

## Mocking

**Framework:** No mocking framework used

**Patterns:**
- Tests directly instantiate simulator classes: `sim = BlockDiagramSimulator("test")`
- No HTTP mocking -- tests bypass the API layer and call simulator methods directly
- Module loading hacks in `test_e2e.py` and `test_multiloop.py` bypass `__init__.py` imports (to avoid SymPy dependency):

```python
# Create package stub to avoid importing all simulators
pkg = types.ModuleType("simulations")
pkg.__path__ = ["simulations"]
sys.modules["simulations"] = pkg

# Load specific modules via importlib
spec = importlib.util.spec_from_file_location(
    "simulations.base_simulator", "simulations/base_simulator.py"
)
mod = importlib.util.module_from_spec(spec)
sys.modules["simulations.base_simulator"] = mod
spec.loader.exec_module(mod)
```

**What to Mock:**
- Currently nothing is mocked -- all tests are integration-level against real simulator logic

**What NOT to Mock:**
- Simulator math (NumPy/SciPy computations) -- always test real computation
- Parameter validation -- test against actual schema

## Fixtures and Factories

**Test Data:**
- Hub validator tests use inline dict literals for TF and SS data
- E2E tests use helper factory functions:

```python
def make_bdb_diagram(blocks_spec, connections_spec, system_type="dt"):
    """Build a BDB diagram from a spec and return the simulator + TF result."""
    sim = BlockDiagramSimulator("test")
    sim.initialize()
    sim.handle_action("clear", {})
    # ... add blocks and connections from spec
```

**Location:**
- No shared fixtures directory
- Each test file defines its own helpers inline
- No `conftest.py` file exists

## Coverage

**Requirements:** None enforced. No coverage tool configured.

**Gaps are significant** -- see below.

## Test Types

**Unit Tests:**
- `backend/tests/test_hub_validator.py` -- 572 lines, 15 test classes
- Tests the hub validation/enrichment pipeline: TF enrichment, SS-to-TF derivation, MIMO handling, discrete-time, stability, slot validators
- Purely computational -- no I/O, no API calls

**Integration Tests (Custom Runners):**
- `backend/test_e2e.py` -- comprehensive BDB + SFS end-to-end tests
- `backend/test_multiloop.py` -- multi-loop Mason's Gain Formula topology tests
- Both bypass the API layer; test simulator classes directly with complex multi-step scenarios
- Include analytical verification against hand-computed results

**Validation / Benchmark Tests:**
- `validation/run_scope_benchmarks.py` -- 712 lines, ~20 benchmarks
- Exercises simulators through their public API with textbook parameters
- Extracts numerical results to JSON for cross-platform comparison
- Benchmarks cover: RC filter Bode, 2nd-order systems, Routh-Hurwitz, steady-state error, LQR, pole placement, MIMO eigenvalues, root locus, PID step response, lead-lag compensator

- `validation/compare.py` -- 486 lines
- Compares SCOPE results against MATLAB Control System Toolbox outputs
- Per-benchmark tolerance tiers: `scalar` (1e-10), `display` (3e-3), `array` (1e-6), `ode` (1e-4), `integer` (exact), `boolean` (exact)
- Generates `validation/results/comparison.json` report

**E2E Tests (Frontend):**
- Not implemented. No browser-level or component-level tests exist.

## Common Patterns

**Numerical Testing:**
```python
# Exact value comparison with tolerance
assert abs(poles[0]["real"] - (-2.0)) < 1e-8
assert abs(poles[0]["imag"]) < 1e-8

# Boolean/integer exact match
assert self.result["data"]["stable"] is True
assert self.result["data"]["system_type"] == 0

# Error message content check
assert "empty" in result["error"].lower()

# Polynomial comparison (custom helper)
assert_poly_close(computed_num, expected_num, tol=1e-4, name="numerator")
```

**Validation Benchmark Pattern:**
```python
@benchmark(
    "CS01_2nd_order_underdamped",
    "second_order_system",
    {"omega_0": 10.0, "Q_slider": 75},
    "2nd-order system: underdamped",
)
def _extract_2nd_order(state):
    meta = state.get("metadata", {})
    info = meta.get("system_info", {})
    return {
        "omega_0": info.get("omega_0"),
        "Q": info.get("Q"),
        "zeta": info.get("zeta"),
        "matlab_cmd": "H = tf(100, [1 10/3.16 100]); bode(H);",
    }
```

Each benchmark:
1. Specifies simulator ID and parameter overrides
2. Defines an extract function that pulls numerical results from simulator state
3. Includes the equivalent MATLAB command for manual verification

**Simulator Instantiation Pattern:**
```python
sim = SimulatorClass("test_id")
sim.initialize()
for name, value in params.items():
    sim.update_parameter(name, value)
state = sim.get_state()
# Assert on state["plots"], state["parameters"], state["metadata"]
```

## What Is NOT Tested

**Frontend:** Zero test coverage. No component tests, no hook tests, no E2E browser tests.

**API Layer:** No tests for FastAPI endpoints, middleware, WebSocket connections, rate limiting, caching, or CORS.

**Most Simulators:** Only Block Diagram Builder and Signal Flow Scope have dedicated test files. The remaining ~45 simulators have no unit tests -- only partial coverage via validation benchmarks (~20 of them).

**Error Paths:** Limited testing of edge cases like malformed input, concurrent access, timeout behavior, or large payloads (except hub validator invalid input tests).

## Adding New Tests

**For a new simulator (pytest style):**
1. Create `backend/tests/test_<sim_id>.py`
2. Import the simulator class directly
3. Use class-based grouping with `setup_method()` for shared state
4. Assert on `get_state()` output: parameters, plot structure, metadata values
5. Use plain `assert` with numerical tolerances

**For validation benchmarks:**
1. Add a `@benchmark()` decorated function in `validation/run_scope_benchmarks.py`
2. Add a comparator branch in `validation/compare.py` `compare_benchmark()` function
3. Add corresponding MATLAB benchmark in `validation/matlab/run_all_benchmarks.m`

---

*Testing analysis: 2026-03-27*
