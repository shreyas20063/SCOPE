# Architecture Patterns: MIMO Block Diagram Validation

**Domain:** MIMO block diagram computation and validation for educational platform
**Researched:** 2026-03-27

## Recommended Architecture

### Overview

The validation architecture has three layers, each with a distinct responsibility. The key insight driving this design is that the existing `BlockDiagramSimulator` computes MIMO transfer matrices by iterating over all (input, output) pairs and calling Mason's Gain Formula per pair via `_solve_for_pair()`. This superposition-based approach is mathematically sound for LTI systems but has specific failure modes that each validation layer must target.

```
Layer 3: Integration Tests (API round-trip, frontend rendering contracts)
Layer 2: MIMO System Tests (transfer matrix correctness, preset validation)
Layer 1: Unit Tests (polynomial arithmetic, Mason's gain, domain conversion)
```

### Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| `BlockDiagramSimulator._solve_signal_flow()` | Mason's Gain Formula for single (input, output) pair | Polynomial helpers (`_pmul`, `_padd`, `_psub`, `_pscale`) |
| `BlockDiagramSimulator._solve_for_pair()` | Signal isolation (zero-gating other inputs) + delegates to `_solve_signal_flow()` | `_solve_signal_flow()`, block state mutation/restore |
| `BlockDiagramSimulator._compute_transfer_function()` | Orchestrates p*m calls to `_solve_for_pair()`, assembles transfer matrix | `_solve_for_pair()`, I/O block enumeration |
| `_operator_to_z()` / `_operator_to_s()` | Domain conversion (R->z or A->s) for poles/zeros/display | NumPy `np.roots()` |
| `to_hub_data()` | Serializes MIMO TF matrix for cross-simulation transfer | Hub validator, System Hub |
| Frontend `MIMOTransferMatrix` component | Renders p*m grid of TF entries with LaTeX | Backend `transfer_function` in metadata |
| Frontend `convertToSFG()` | Converts block diagram to Signal Flow Graph view | Block/connection state from metadata |

### Data Flow

```
User builds diagram (frontend canvas)
    |
    v
handle_action("compute_tf", {}) -> _recompute_tf()
    |
    v
_compute_transfer_function()
    |-- enumerate input_blocks (m) and output_blocks (p)
    |-- for each (output_i, input_j) pair:
    |       |
    |       v
    |   _solve_for_pair(input_id, output_id, all_input_ids)
    |       |-- zero-gate other input blocks (type -> "gain", value -> 0.0)
    |       |-- _solve_signal_flow(input_id, output_id)
    |       |       |-- build adjacency (incoming, outgoing)
    |       |       |-- DFS: find all forward paths
    |       |       |-- DFS: find all loops
    |       |       |-- Mason's: compute_delta, compute_path_gain, compute_cofactor
    |       |       |-- TF = sum(P_k * Delta_k) / Delta
    |       |       |-- _operator_to_z() or _operator_to_s()
    |       |       |-- stability classification
    |       |       +-- return {numerator, denominator, poles, zeros, latex, ...}
    |       |-- restore zero-gated blocks
    |       +-- return tf_entry dict
    |
    +-- assemble transfer_matrix[p][m]
    +-- return {mimo: true, dimensions, transfer_matrix, labels, system_stable}
    |
    v
get_state() embeds transfer_function in metadata
    |
    v
Frontend receives via API -> SimulationViewer -> BlockDiagramViewer
    |-- if mimo: render MIMOTransferMatrix grid
    |-- if sfg mode: convertToSFG() for visualization
    +-- to_hub_data() if System Hub push requested
```

## Validation Test Architecture

### Layer 1: Unit Tests -- Polynomial and Mason's Primitives

**What:** Verify the mathematical building blocks in isolation.
**Where:** `validation/tests/test_bdb_unit.py`
**Dependencies:** None (pure math)
**Build first.**

#### 1A. Polynomial Arithmetic (LOW-POWER-FIRST convention)

The BDB uses a nonstandard low-power-first convention where `coeffs[i]` = coefficient of R^i. This is the opposite of NumPy's `np.poly1d` convention. Every polynomial helper must be tested against this convention.

```python
# Tests to write:
def test_pmul_constants():
    # [2.0] * [3.0] = [6.0]
    assert_array_close(_pmul([2.0], [3.0]), [6.0])

def test_pmul_polynomial():
    # (1 + 2R)(1 - R) = 1 + R - 2R^2 -> [1, 1, -2]
    assert_array_close(_pmul([1, 2], [1, -1]), [1, 1, -2])

def test_padd_different_lengths():
    # [1, 2] + [3] = [4, 2]
    assert_array_close(_padd([1, 2], [3]), [4, 2])

def test_psub_identity():
    # a - a = 0
    a = np.array([1.0, -0.5, 0.3])
    assert_array_close(_psub(a, a), [0, 0, 0])

def test_clean_poly_trailing_zeros():
    # [1, 2, 0, 0] -> [1, 2]
    ...
```

#### 1B. Domain Conversion

```python
def test_operator_to_z_accumulator():
    # H(R) = R/(1-R), low-power-first num=[0,1] den=[1,-1]
    # Expected H(z) = 1/(z-1) high-power-first
    z_num, z_den = sim._operator_to_z(np.array([0,1]), np.array([1,-1]))
    # z_num should be [1, 0], z_den should be [1, -1] (high-power-first)

def test_operator_to_s_integrator():
    # H(A) = A, low-power-first num=[0,1] den=[1]
    # H(s) = 1/s
    s_num, s_den = sim._operator_to_s(np.array([0,1]), np.array([1]))
    # s_num = [1], s_den = [1, 0]
```

#### 1C. Single-Pair Mason's Gain (SISO pathfinding)

Test the DFS path/loop finding and Mason's formula assembly on small hand-built graphs.

```python
def test_cascade_gain():
    # Input -> Gain(3) -> Output
    # Expected: H = 3

def test_feedback_loop():
    # Classic unity negative feedback: H = G/(1+G)
    # Input -> Adder -> Gain(G) -> Junction -> Output
    #                    ^-(-)----- Junction ---|
    # With G=10, integrator in feedback: H(s) = 10/(s+10)

def test_two_forward_paths():
    # Input -> Junction -> G1 -> Adder -> Output
    #                   +-> G2 ---^
    # H = G1 + G2
```

### Layer 2: MIMO System Tests -- Transfer Matrix Correctness

**What:** Verify that the full MIMO pipeline produces correct transfer matrices for textbook-standard topologies.
**Where:** `validation/tests/test_bdb_mimo.py`
**Dependencies:** Layer 1 must pass.
**Build second.**

#### 2A. Textbook Test Cases (Canonical MIMO Topologies)

Each test programmatically builds a diagram (no presets -- tests should not depend on preset wiring which could change), computes the TF, and asserts against hand-computed expected values.

| Test Case | Topology | Expected Transfer Matrix | Source |
|-----------|----------|-------------------------|--------|
| `test_2x2_open_loop` | u1->G11->y1, u1->G21->y2, u2->G12->y1, u2->G22->y2 | G(s) = [[G11, G12], [G21, G22]] | Ogata Ch. 3 |
| `test_2x1_miso` | u1->G1->adder->y, u2->G2->adder->y | G(s) = [[G1, G2]] | Nise Ch. 5 |
| `test_1x2_simo` | u->junction->G1->y1, junction->G2->y2 | G(s) = [[G1], [G2]] | Ogata Ch. 3 |
| `test_2x2_with_feedback` | 2x2 plant with output-to-input feedback | Closed-loop via Mason's per pair | Ogata Ch. 11 |
| `test_diagonal_decoupled` | Two independent SISO channels | G = [[G1, 0], [0, G2]] | Standard |
| `test_triangular_coupling` | Upper triangular: G12 != 0, G21 = 0 | G = [[G11, G12], [0, G22]] | Standard |

#### 2B. Signal Isolation Correctness

The most critical MIMO-specific mechanism: `_solve_for_pair()` zero-gates other inputs. This must be tested explicitly.

```python
def test_signal_isolation_no_crosstalk():
    """Build 2x2 with independent paths. G12 and G21 must be zero."""
    # u1 -> G1 -> y1 (no connection to y2)
    # u2 -> G2 -> y2 (no connection to y1)
    # Expected: transfer_matrix = [[G1, 0], [0, G2]]

def test_signal_isolation_with_shared_node():
    """Shared junction between paths -- isolation must still work."""
    # u1 -> junction -> G1 -> adder -> y1
    # u2 -> G2 -----------> adder
    # When computing G11: u2 is zero-gated, so adder sees only G1*u1
    # When computing G12: u1 is zero-gated, so adder sees only G2*u2

def test_signal_isolation_restores_blocks():
    """After _solve_for_pair, block types must be restored to 'input'."""
    # Verify blocks dict is unchanged after compute_transfer_function()
```

#### 2C. Preset Validation (Smoke Tests)

Verify the three existing MIMO presets produce expected results.

```python
def test_preset_2x2_coupled():
    """Load mimo_2x2_coupled preset, compute TF, verify matrix entries."""
    sim = BlockDiagramSimulator("test")
    sim.initialize()
    sim.handle_action("load_preset", {"preset": "mimo_2x2_coupled"})
    sim.handle_action("compute_tf", {})
    tf = sim._tf_result
    assert tf["mimo"] is True
    assert tf["dimensions"] == {"inputs": 2, "outputs": 2}
    # G11 = 2.0, G12 = 0.5, G21 = 0.3, G22 = 1.5 (pure gains, no dynamics)
    assert_close(tf["transfer_matrix"][0][0]["numerator"], [2.0])
    assert_close(tf["transfer_matrix"][0][1]["numerator"], [0.5])
    assert_close(tf["transfer_matrix"][1][0]["numerator"], [0.3])
    assert_close(tf["transfer_matrix"][1][1]["numerator"], [1.5])
```

#### 2D. Edge Cases

| Case | What to Test | Why It Matters |
|------|-------------|----------------|
| Zero entry in matrix | Path from u_j to y_i does not exist | Must return `{numerator: [0.0], denominator: [1.0]}`, not throw |
| Single input, single output (1x1 MIMO) | Legacy compat: `result.update(transfer_matrix[0][0])` | Must behave identically to SISO code path |
| 3x3 or larger | Combinatorial path explosion in Mason's | Performance + correctness with many loops |
| Feedback around MIMO plant | Shared feedback path affects multiple pairs | Signal isolation must handle feedback correctly |
| Algebraic loop in MIMO | Feedback without delay/integrator | Error detection must still trigger per-pair |
| Custom TF blocks in MIMO | Non-trivial num/den polynomials per block | Polynomial arithmetic compounds across paths |

### Layer 3: Integration Tests -- API and Frontend Contract

**What:** Verify the full round-trip from API call to serialized response, and that the frontend contract is satisfied.
**Where:** `validation/tests/test_bdb_integration.py`
**Dependencies:** Layers 1 and 2 must pass.
**Build third.**

#### 3A. API Contract Tests

```python
def test_api_compute_tf_returns_mimo_structure():
    """POST /api/simulations/block_diagram_builder/execute with compute_tf action."""
    # Build diagram via API calls, then compute
    # Assert response.data.metadata.transfer_function has:
    #   - mimo: bool
    #   - dimensions: {inputs: int, outputs: int}
    #   - transfer_matrix: list[list[dict]]
    #   - input_labels: list[str]
    #   - output_labels: list[str]
    #   - system_stable: bool

def test_api_state_includes_transfer_function():
    """GET /api/simulations/block_diagram_builder/state after compute."""
    # Assert metadata.transfer_function is populated
```

#### 3B. Hub Export Contract

```python
def test_hub_export_mimo_structure():
    """to_hub_data() for MIMO produces expected schema."""
    # Assert: transfer_matrix.entries, input_labels, output_labels, variable

def test_hub_export_siso_fallback():
    """to_hub_data() for 1x1 produces legacy tf.num/tf.den format."""
```

#### 3C. Frontend Rendering Contract (Schema Validation, not Visual)

The frontend `MIMOTransferMatrix` component expects specific fields in each transfer matrix entry. These tests verify the backend produces the right shape, not that pixels render correctly.

```python
def test_entry_has_required_fields():
    """Each entry in transfer_matrix must have: numerator, denominator,
    latex, domain_latex, stability, is_stable, poles, zeros."""
    for row in tf["transfer_matrix"]:
        for entry in row:
            assert "numerator" in entry
            assert "denominator" in entry
            assert "domain_latex" in entry
            assert "stability" in entry
            assert "is_stable" in entry

def test_labels_match_dimensions():
    """input_labels length == dimensions.inputs, output_labels == dimensions.outputs."""
```

## Patterns to Follow

### Pattern 1: Programmatic Diagram Construction for Tests

**What:** Build diagrams by calling simulator methods directly, not by loading presets.
**When:** All Layer 2 tests.
**Why:** Tests must not depend on preset wiring (which is an implementation detail that can change). Constructing diagrams programmatically makes the test self-documenting and resilient.

```python
def build_2x2_open_loop(sim, g11=2.0, g12=0.5, g21=0.3, g22=1.5):
    """Programmatically build a 2x2 open-loop MIMO system."""
    sim.initialize({"system_type": "ct"})

    # Add blocks
    sim.handle_action("add_block", {"type": "input", "position": {"x": 100, "y": 100}})
    sim.handle_action("add_block", {"type": "input", "position": {"x": 100, "y": 300}})
    sim.handle_action("add_block", {"type": "output", "position": {"x": 700, "y": 100}})
    sim.handle_action("add_block", {"type": "output", "position": {"x": 700, "y": 300}})

    # Add gains, junctions, adders, connections...
    # (full wiring code)

    sim.handle_action("compute_tf", {})
    return sim._tf_result
```

### Pattern 2: Numerical Tolerance Assertions

**What:** Use `np.allclose` with explicit tolerances for all polynomial comparisons.
**When:** Any test comparing numerator/denominator coefficients.
**Why:** Floating-point arithmetic in Mason's formula compounds rounding errors, especially with polynomial multiplication chains.

```python
def assert_tf_entry(entry, expected_num, expected_den, atol=1e-10):
    """Assert a single TF entry matches expected coefficients."""
    np.testing.assert_allclose(entry["numerator"], expected_num, atol=atol)
    np.testing.assert_allclose(entry["denominator"], expected_den, atol=atol)
```

### Pattern 3: Benchmark Registration (Extending Existing Infrastructure)

**What:** Register MIMO BDB benchmarks in the existing `validation/run_scope_benchmarks.py` pattern.
**When:** After Layer 2 correctness is established.
**Why:** The project already has a SCOPE-vs-MATLAB benchmark framework. MIMO BDB tests should plug into it.

```python
@benchmark(
    "BDB_MIMO_2x2_open_loop",
    "block_diagram_builder",
    {},
    "2x2 open-loop MIMO: verify transfer matrix entries",
    actions=["load_preset:mimo_2x2_coupled", "compute_tf"],
)
def _extract_bdb_mimo_2x2(state):
    tf = state["metadata"]["transfer_function"]
    return {
        "G11_num": tf["transfer_matrix"][0][0]["numerator"],
        "G12_num": tf["transfer_matrix"][0][1]["numerator"],
        "matlab_cmd": "G = [tf(2,1) tf(0.5,1); tf(0.3,1) tf(1.5,1)]",
    }
```

## Anti-Patterns to Avoid

### Anti-Pattern 1: Testing via Presets Only
**What:** Only testing by loading presets and checking output.
**Why bad:** Presets can change wiring/gains independently of algorithm correctness. A preset change would break tests even though the algorithm is fine.
**Instead:** Build diagrams programmatically in tests. Use presets only as smoke tests (Layer 2C).

### Anti-Pattern 2: Visual Regression as Primary Validation
**What:** Screenshot-comparing rendered block diagrams or TF matrices.
**Why bad:** CSS changes, layout shifts, font rendering differences produce false failures. The math could be perfect but tests fail due to a spacing change.
**Instead:** Test the data contract (JSON structure, numerical values). Visual testing is supplementary, not primary.

### Anti-Pattern 3: Monolithic Test Functions
**What:** One test that builds a diagram, computes TF, checks all matrix entries, verifies stability, and checks hub export.
**Why bad:** When it fails, you don't know which part broke. Debugging requires reading the entire test.
**Instead:** Separate construction, computation, and assertion. Use fixtures for diagram setup.

### Anti-Pattern 4: Testing Internal State Instead of Public Interface
**What:** Directly inspecting `sim.blocks`, `sim.connections`, intermediate DFS results.
**Why bad:** Internal representation can change without affecting correctness.
**Instead:** Test through `handle_action()` and `get_state()` / `_tf_result`. The only exception is signal isolation restoration (which is a correctness invariant).

## Computation Architecture: Symbolic vs Numeric

### Current State: Purely Numeric

The existing BDB is purely numeric -- all polynomial operations use NumPy float64 arrays. There is no symbolic computation layer. Mason's formula is evaluated numerically:

- Path gains: `np.convolve` for polynomial multiplication
- Loop gains: same `np.convolve` chains
- Delta/cofactors: polynomial add/subtract/multiply
- Domain conversion: array padding and reversal
- Poles/zeros: `np.roots()` (numerical eigenvalue computation)

### Assessment: Numeric Is Sufficient for This Milestone

A symbolic layer (e.g., SymPy) would provide:
- Exact rational polynomial arithmetic (no floating-point error)
- Simplified/factored expressions
- Symbolic verification of identities

However, adding SymPy would be:
1. **Over-engineered** for the current scope (block diagrams with constant gains and simple TFs)
2. **Performance-costly** for interactive use (SymPy is orders of magnitude slower than NumPy)
3. **Architecturally invasive** (would require rewriting all polynomial helpers)

**Recommendation:** Keep the numeric approach. Use SymPy only in the *test harness* as an independent oracle to verify BDB's numeric results. This gives symbolic verification without changing production code.

```python
# In test harness only:
import sympy as sp

def symbolic_mason_verify(blocks, connections, input_id, output_id):
    """Independent symbolic computation for oracle comparison."""
    s = sp.Symbol('s')
    # Build symbolic graph, compute Mason's symbolically
    # Compare numerically against BDB result at test points
```

### Where Symbolic Would Matter (Future)

If the project later needs:
- Automatic simplification of TF expressions for display
- Exact pole/zero cancellation detection
- Symbolic state-space realization from block diagrams

Then a symbolic layer would be warranted. Flag this as a future architecture decision, not a current requirement.

## Scalability Considerations

| Concern | Current (3x3 max) | Future (NxN) | Mitigation |
|---------|-------------------|--------------|------------|
| Mason's path enumeration | Fast (<10ms) | Exponential for dense graphs | Already capped at 20 loops, k>4 groups |
| Transfer matrix computation | p*m calls to Mason's | O(p*m) calls, each with full DFS | Acceptable up to ~8x8; cache shared loops |
| Signal isolation overhead | Negligible block mutation | Same O(1) per call | No change needed |
| Frontend matrix rendering | 2x2 grid trivial | 8x8 grid = 64 LaTeX cells | Virtualize or paginate for >5x5 |
| SFG conversion for MIMO | Untested | MIMO SFG is non-trivial | Needs dedicated research for MIMO SFG |

## Build Order Implications

### Phase 1: Foundation (Layer 1 Tests)
- Write polynomial arithmetic unit tests
- Write domain conversion unit tests
- Write single-pair Mason's gain tests against hand-computed examples
- **Gate:** All Layer 1 tests pass before proceeding

### Phase 2: MIMO Correctness (Layer 2 Tests)
- Build programmatic diagram construction helpers
- Write 2x2/MISO/SIMO open-loop tests
- Write signal isolation tests (the most MIMO-critical code)
- Write edge case tests (zero entries, 1x1 fallback, algebraic loops)
- **Gate:** Transfer matrices match textbook values for all canonical topologies

### Phase 3: Integration and Hardening (Layer 3 Tests)
- API round-trip tests
- Hub export contract tests
- Frontend schema validation tests
- Register MIMO benchmarks in existing validation framework
- **Gate:** Full stack produces correct, well-formed MIMO data

### Phase 4: Educational Content and MIMO SFG (if in scope)
- Theory sections for MIMO block diagram algebra
- MIMO SFG conversion (requires separate research -- current `convertToSFG()` is SISO-oriented)
- Textbook equation derivation display

## Existing Code Risks Identified During Research

### Risk 1: Zero-Gating Mutation Pattern
`_solve_for_pair()` mutates the `self.blocks` dict in-place (changing input blocks to gain blocks with value 0) and restores them in a finally block. This is fragile:
- If an exception occurs during restoration, blocks remain corrupted
- Thread safety: concurrent calls would corrupt state (mitigated by GIL + single-threaded executor)
- The restoration logic checks `info["has_value"]` but doesn't restore the original value field

**Validation test needed:** Verify block state is identical before and after `_compute_transfer_function()`.

### Risk 2: Adder Sign Handling in Paths
`compute_path_gain()` looks up the `to_port` for adder sign application via `conn_port_map`. For MIMO with shared adders (e.g., two inputs feeding the same adder through different paths), the sign must be correctly determined per path traversal. The current code uses `conn_port_map[(prev_bid, bid)]` which is correct for a single connection but could fail if there are parallel connections from the same source to the same adder.

**Validation test needed:** Adder with both + and - inputs from different MIMO paths.

### Risk 3: Low-Power-First Convention Mismatch
The BDB uses low-power-first internally but `np.roots()` and `scipy.signal` expect high-power-first. The `_operator_to_z()` and `_operator_to_s()` methods handle this conversion, but a sign error or off-by-one in the padding would silently produce wrong poles/zeros.

**Validation test needed:** Known polynomial with known roots, verified through the full pipeline.

## Sources

- Codebase analysis: `backend/simulations/block_diagram_builder.py` (3380+ lines)
- Codebase analysis: `backend/core/mimo_utils.py` (460 lines) -- separate MIMO math module
- Codebase analysis: `frontend/src/components/BlockDiagramViewer.jsx` -- MIMO rendering and SFG conversion
- Codebase analysis: `validation/run_scope_benchmarks.py` -- existing benchmark framework pattern
- Codebase analysis: `validation/compare.py` -- existing SCOPE-vs-MATLAB comparison infrastructure
- Project context: `.planning/PROJECT.md` -- milestone requirements and constraints
- Reference texts (per PROJECT.md): Ogata (Modern Control Engineering), Nise (Control Systems Engineering), Oppenheim (Signals & Systems)
