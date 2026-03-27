# Technology Stack: MIMO Validation & Educational Control Systems Tooling

**Project:** MIMO Block Diagram Builder Hardening
**Researched:** 2026-03-27
**Focus:** Libraries and frameworks for validating MIMO control system computations against textbook results

---

## Executive Decision

**The existing runtime stack (Python 3.11/FastAPI + React 18/Vite) does not change.** This document focuses on what to ADD for validation, testing, and reference computation -- the tooling that ensures every MIMO computation matches Ogata, Nise, and Oppenheim.

---

## Recommended Stack

### Validation Oracle: python-control (NEW -- dev dependency only)

| Technology | Version | Purpose | Confidence |
|------------|---------|---------|------------|
| `control` | 0.10.2+ | MIMO transfer function oracle, reference computations for test assertions | HIGH |

**Why:** python-control is the Python equivalent of MATLAB's Control System Toolbox. It provides:
- `control.tf()` for MIMO transfer function matrices (2D arrays of num/den polynomials)
- `control.ss()` for MIMO state-space models
- `control.interconnect()` for building block diagrams from named signal connections -- directly comparable to what SCOPE's BDB does
- `control.feedback()` for MIMO feedback loops implementing Y = (I + GH)^{-1} G R
- `control.step_response()`, `control.impulse_response()` for MIMO response grids
- `control.tf2ss()`, `control.ss2tf()` for conversion validation
- `control.minreal()` for minimal realization (pole-zero cancellation)
- Pole/zero computation, stability checks, controllability/observability matrices

**How to use it:** python-control is NOT a runtime dependency. It is a test-time oracle. The pattern is:

```python
# In validation test:
import control
import numpy as np
from numpy.testing import assert_allclose

# Build reference system using python-control
G11 = control.tf([1], [1, 2])
G12 = control.tf([1], [1, 3])
G21 = control.tf([2], [1, 4])
G22 = control.tf([1, 1], [1, 5, 6])
G_ref = control.tf([[G11.num[0][0], G12.num[0][0]],
                     [G21.num[0][0], G22.num[0][0]]],
                    [[G11.den[0][0], G12.den[0][0]],
                     [G21.den[0][0], G22.den[0][0]]])

# Build same system in SCOPE's BDB, extract computed TF matrix
scope_result = run_bdb_computation(diagram_json)

# Compare
for i in range(2):
    for j in range(2):
        assert_allclose(scope_result.num[i][j], G_ref.num[i][j], rtol=1e-10)
        assert_allclose(scope_result.den[i][j], G_ref.den[i][j], rtol=1e-10)
```

**Installation note:** `pip install control` pulls in NumPy and SciPy (already present). Slycot is optional -- needed only for some advanced MIMO routines (balanced realization, H-infinity). For validation purposes, base python-control without Slycot is sufficient.

**Do NOT install Slycot** unless you specifically need balanced truncation or H-infinity synthesis. Slycot requires FORTRAN compilers and BLAS/LAPACK, making CI/CD setup painful. The base python-control covers all validation needs for this milestone.

### Symbolic Verification: SymPy physics.control (ALREADY INSTALLED)

| Technology | Version | Purpose | Confidence |
|------------|---------|---------|------------|
| `sympy` | >=1.12 (pinned in requirements.txt) | Symbolic MIMO TF verification, exact rational arithmetic | HIGH |

**Why:** SymPy 1.12+ includes `sympy.physics.control` with:
- `TransferFunction` -- symbolic SISO transfer functions in Laplace domain
- `TransferFunctionMatrix` -- symbolic MIMO TF matrices with exact rational coefficients
- `MIMOSeries`, `MIMOParallel`, `MIMOFeedback` -- symbolic interconnection classes
- `.doit()` method to simplify interconnections to a single `TransferFunctionMatrix`
- `TransferFunctionMatrix.from_Matrix()` to convert SymPy Matrix of rational expressions

**Critical advantage over python-control:** SymPy computes EXACT symbolic results with no floating-point error. For validating Mason's Gain Formula outputs, this is invaluable:

```python
from sympy import symbols, Rational
from sympy.physics.control import TransferFunction, TransferFunctionMatrix, MIMOFeedback

s = symbols('s')
G11 = TransferFunction(1, s + 2, s)
G12 = TransferFunction(1, s + 3, s)
# Build MIMO TF matrix, apply feedback symbolically
# Compare exact rational result against SCOPE's numerical output
```

**When to use SymPy vs python-control:**
- **SymPy:** Verify algebraic correctness of Mason's formula (exact rational coefficients, no tolerance needed)
- **python-control:** Verify numerical behavior (step responses, frequency responses, stability margins)

SymPy is already a runtime dependency (used in `nonlinear_control_lab.py` for Jacobians and `state_space_analyzer.py`). No new installation needed.

### Testing Framework

| Technology | Version | Purpose | Confidence |
|------------|---------|---------|------------|
| `pytest` | >=7.0 | Test runner, fixtures, parametrize | HIGH |
| `numpy.testing` | (bundled with NumPy) | `assert_allclose` for numerical comparison | HIGH |
| `pytest-timeout` | >=2.2 | Prevent hanging tests (Mason's on large graphs) | MEDIUM |

**Why pytest:** Standard Python testing. The existing `validation/` directory already uses a benchmark-comparison pattern (SCOPE vs MATLAB JSON). pytest adds structured test discovery, parametrized test cases (one test function, many textbook examples), and clear failure output.

**Why `numpy.testing.assert_allclose`:** This is the correct function for control systems numerical comparison. NOT `assert_array_almost_equal` (legacy, deprecated). NOT `pytest.approx` (less informative for arrays).

```python
# Correct
from numpy.testing import assert_allclose
assert_allclose(actual_poles, expected_poles, rtol=1e-6, atol=1e-10)

# Wrong -- legacy
np.testing.assert_array_almost_equal(actual, expected, decimal=6)  # Don't use

# Wrong -- less informative for arrays
assert actual == pytest.approx(expected, rel=1e-6)  # Don't use for numpy arrays
```

### Numerical Tolerance Strategy

| Comparison Type | rtol | atol | Rationale |
|----------------|------|------|-----------|
| TF coefficients (symbolic oracle) | 1e-12 | 1e-15 | SymPy gives exact; only float conversion error |
| TF coefficients (python-control oracle) | 1e-10 | 1e-12 | Both numerical; small accumulation |
| Pole/zero locations | 1e-6 | 1e-10 | Root-finding is ill-conditioned for repeated roots |
| Step/impulse response values | 1e-4 | 1e-6 | ODE solver differences (RK45 vs lsim) |
| Frequency response (Bode) | 1e-6 | 1e-8 | Direct evaluation, well-conditioned |
| Gain/phase margins | 1e-3 | 1e-4 | Interpolation-dependent |
| Mason's path/loop enumeration | exact | 0 | Combinatorial -- must be exactly right |

### Signal Flow Graph Reference: andypfau/sfg (EVALUATE ONLY)

| Technology | Version | Purpose | Confidence |
|------------|---------|---------|------------|
| `sfg` (GitHub) | latest | Independent Mason's Gain Formula implementation for cross-validation | LOW |

**Why mentioned:** The `andypfau/sfg` library on GitHub implements Mason's Gain Formula independently with SymPy symbolic support. It could serve as a THIRD oracle (alongside python-control and SymPy) for Mason's formula validation.

**Why LOW confidence:** Small library, single maintainer, no PyPI release. Use only for spot-checking, not as primary oracle. If SCOPE's Mason's and SymPy's symbolic computation agree, that is sufficient.

**Recommendation:** Do NOT add as dependency. Clone and reference for spot-checks if Mason's results are suspicious. The primary validation path is SymPy symbolic (exact) + python-control numerical (behavioral).

### MATLAB Cross-Validation (ALREADY SET UP)

| Technology | Purpose | Confidence |
|------------|---------|------------|
| MATLAB Control System Toolbox | Gold-standard reference values for comparison | HIGH |

The existing `validation/` directory already has the pattern:
- `run_scope_benchmarks.py` -- exercises SCOPE simulators, exports JSON
- `matlab/` -- MATLAB scripts that produce reference JSON
- `compare.py` -- computes error metrics (max abs error, RMS relative error)

**For MIMO validation, extend this pattern:**
1. Add MATLAB scripts that compute MIMO TF matrices for standard topologies
2. Add SCOPE benchmark cases that build the same diagrams via BDB API
3. Compare entry-by-entry using existing `compare.py` infrastructure

This is the highest-confidence validation path but requires MATLAB access. python-control + SymPy provide the CI-friendly alternative.

---

## Core Framework (EXISTING -- NO CHANGES)

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11 | Backend runtime |
| FastAPI | 0.109 | API framework |
| NumPy | >=1.24, <2.0 | Array operations, polynomial math |
| SciPy | >=1.10, <2.0 | signal processing, linalg, integrate |
| SymPy | >=1.12 | Symbolic math (Jacobians, control module) |
| React | 18.2 | Frontend framework |
| Vite | 5 | Build tool |
| Plotly.js | 2.28 | Response plots |
| Three.js | 0.182 | 3D visualizations |

---

## What NOT to Use

| Library | Why Not |
|---------|---------|
| **Slycot** | FORTRAN dependency. Requires compilers and BLAS/LAPACK to install. Needed only for H-infinity and balanced realization, which are out of scope for this milestone. If you see `ImportError: slycot` in python-control, the function you called is not needed for validation. |
| **MATLAB Engine for Python** | Requires MATLAB license and installation on every dev machine. The existing JSON-comparison pattern in `validation/` is better -- generate MATLAB results once, commit JSON, compare in CI. |
| **harold** (Python control library) | Alternative to python-control with arguably better MIMO support, but much smaller community, less documentation, and less active maintenance. python-control is the standard. |
| **scipy.signal.TransferFunction** for MIMO | SciPy's `TransferFunction` is SISO only. `StateSpace` supports MIMO but `ss2tf` returns per-output rows, not a proper MIMO TF matrix. Use python-control for MIMO TF operations. |
| **Jest / Vitest** for math validation | Math validation belongs in Python where the computation happens. Frontend tests are for UI behavior, not numerical correctness. Do not test Mason's formula in JavaScript. |
| **Hypothesis** (property-based testing) | Overkill for textbook validation. We need specific known-answer tests from Ogata/Nise, not random property checks. Property-based testing is useful for fuzz-testing edge cases AFTER known-answer tests pass. |
| **NetworkX** for graph algorithms | The BDB already has its own graph traversal for Mason's formula. Adding NetworkX would create a parallel graph representation that drifts from the source of truth. Validate the existing implementation, don't replace it. |

---

## Textbook Reference Values

The most critical "tool" for validation is having correct reference values. Sources:

| Source | What It Provides | How to Use |
|--------|-----------------|------------|
| **Ogata, Modern Control Engineering, 5e** | MIMO TF matrices (Ch. 3), state-space (Ch. 3-4), block diagram algebra (Ch. 3) | Hand-compute reference TFs for 2x2, 3x2 examples. Hardcode in test fixtures. |
| **Nise, Control Systems Engineering, 7e** | Mason's Gain Formula worked examples (Ch. 5), SISO block diagram reduction | Use Mason's examples as test cases. Compare forward paths, loops, cofactors. |
| **Oppenheim, Signals & Systems** | Signal flow graph conventions, LTI system properties | Verify SFG rendering matches conventions. |
| **[Nise solutions in Python (GitHub)](https://github.com/clintschad/control_systems_engineering_nise)** | Python implementations of Nise textbook problems | Cross-reference for known-answer values |
| **MATLAB documentation examples** | `connect`, `feedback`, `tf`, `ss` for MIMO systems | Generate reference JSON using existing `validation/matlab/` pattern |

---

## Validation Architecture

```
Test Layer                  Oracle Layer              Reference Layer
-----------                 ------------              ---------------
pytest tests         -->    python-control            Ogata examples
  parametrized               (numerical MIMO TF)      (hardcoded fixtures)
  per textbook example
                     -->    SymPy physics.control     Nise examples
pytest tests                 (symbolic exact TF)      (hardcoded fixtures)
  Mason's formula
  specific
                     -->    MATLAB JSON               MATLAB scripts
pytest tests                 (gold standard)           (run once, commit JSON)
  behavioral
  (step, Bode)
```

**Three-oracle strategy:** For any critical computation (e.g., MIMO feedback TF matrix), validate against all three:
1. SymPy symbolic (exact rational) -- catches coefficient errors
2. python-control numerical -- catches implementation differences
3. MATLAB JSON (when available) -- catches both

If all three agree, HIGH confidence. If two agree, investigate the outlier. If none agree, the test fixture is probably wrong.

---

## Installation

```bash
# Dev/test dependencies ONLY (not runtime)
pip install control>=0.10.2    # MIMO TF oracle
pip install pytest>=7.0         # Test runner
pip install pytest-timeout>=2.2 # Timeout protection

# Already installed (runtime):
# numpy, scipy, sympy -- no changes needed
```

**Recommended: add a `requirements-dev.txt`:**

```
# requirements-dev.txt -- validation and testing
control>=0.10.2
pytest>=7.0
pytest-timeout>=2.2
```

---

## Key Implementation Notes

### python-control MIMO TF Creation

python-control uses a 3D nested list structure for MIMO TFs:
- `num[i][j]` = numerator polynomial coefficients from input j to output i
- `den[i][j]` = denominator polynomial coefficients from input j to output i

This matches Ogata's convention: G_ij(s) = Y_i(s) / U_j(s) with all other inputs zero.

SCOPE's BDB computes per-pair TFs via Mason's formula using the same superposition principle (zero-gating other inputs). The output format must be mapped to this same [i][j] convention for comparison.

### SymPy physics.control MIMO Operations

```python
from sympy import symbols
from sympy.physics.control import (
    TransferFunction, TransferFunctionMatrix,
    MIMOSeries, MIMOParallel, MIMOFeedback
)

s = symbols('s')
# Build 2x2 plant
G = TransferFunctionMatrix([
    [TransferFunction(1, s+1, s), TransferFunction(2, s+3, s)],
    [TransferFunction(s, s**2+2*s+1, s), TransferFunction(1, s+2, s)]
])

# Unity feedback: CL = (I + G)^{-1} * G
I = TransferFunctionMatrix.eye(2, s)  # 2x2 identity TFM
cl = MIMOFeedback(G, I, sign=-1)
cl_tfm = cl.doit()  # Returns TransferFunctionMatrix with simplified entries
```

### scipy.signal Limitations for MIMO

- `scipy.signal.TransferFunction` -- SISO only, raises error for MIMO
- `scipy.signal.StateSpace` -- supports MIMO (arbitrary A,B,C,D matrices)
- `scipy.signal.ss2tf` -- returns numerator array with one row per output, but only for a SINGLE input at a time (must loop over inputs)
- `scipy.signal.lsim` -- works with MIMO StateSpace objects

**Bottom line:** Use SciPy for state-space operations and time-domain simulation. Use python-control for MIMO transfer function operations. Do not try to force SciPy's signal module into MIMO TF work.

---

## Confidence Assessment

| Recommendation | Confidence | Rationale |
|---------------|------------|-----------|
| python-control as MIMO oracle | HIGH | De facto Python standard for control systems, active development (0.10.2 as of 2025), MIMO TF + interconnect support verified in docs |
| SymPy physics.control for symbolic verification | HIGH | TransferFunctionMatrix, MIMOFeedback confirmed in SymPy 1.14 docs. Already a runtime dependency. |
| `numpy.testing.assert_allclose` for comparisons | HIGH | NumPy official recommendation, replaces deprecated alternatives |
| Tolerance tiers (see table above) | MEDIUM | Based on general numerical analysis principles. May need tuning per test case -- ill-conditioned systems need looser tolerances. |
| Skip Slycot | HIGH | Confirmed: only needed for H-infinity/balanced realization. Base python-control covers all validation needs. |
| Skip harold | HIGH | Confirmed: smaller community, less documentation. python-control is the standard. |
| andypfau/sfg for spot-checks | LOW | Small single-maintainer library. Not on PyPI. Reference only, not a dependency. |
| MATLAB JSON comparison pattern | HIGH | Already implemented in `validation/`. Extend, don't replace. |

---

## Sources

- [python-control TransferFunction docs (0.10.2)](https://python-control.readthedocs.io/en/latest/generated/control.TransferFunction.html)
- [python-control Interconnected I/O Systems (0.10.2)](https://python-control.readthedocs.io/en/0.10.2/iosys.html)
- [python-control interconnect() function](https://python-control.readthedocs.io/en/0.10.2/generated/control.interconnect.html)
- [python-control GitHub](https://github.com/python-control/python-control)
- [python-control PyPI](https://pypi.org/project/control/)
- [SymPy Control API (1.14)](https://docs.sympy.org/latest/modules/physics/control/lti.html)
- [SymPy TransferFunctionMatrix examples](https://gist.github.com/akshanshbhatt/8d8175b6d899114da960c8dae934ed5a)
- [SymPy Control Module overview](https://docs.sympy.org/latest/modules/physics/control/control.html)
- [NumPy assert_allclose docs](https://numpy.org/doc/stable/reference/generated/numpy.testing.assert_allclose.html)
- [SciPy ss2tf docs](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.ss2tf.html)
- [SciPy StateSpace docs](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.StateSpace.html)
- [Slycot GitHub](https://github.com/python-control/Slycot)
- [Nise Control Systems solutions in Python](https://github.com/clintschad/control_systems_engineering_nise)
- [andypfau/sfg - Signal Flow Graph library](https://github.com/andypfau/sfg)
- [MIMO robust control example (python-control)](https://python-control.readthedocs.io/en/latest/examples/robust_mimo.html)
