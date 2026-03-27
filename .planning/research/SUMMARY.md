# Project Research Summary

**Project:** MIMO Block Diagram Builder Hardening
**Domain:** MIMO control systems validation for educational platform
**Researched:** 2026-03-27
**Confidence:** HIGH

## Executive Summary

This project hardens the MIMO transfer matrix computation in SCOPE's Block Diagram Builder (BDB). The BDB already computes MIMO transfer matrices via Mason's Gain Formula applied per (input, output) pair using superposition. The core algorithm is mathematically sound for LTI systems, but it has never been validated against textbook reference values and contains several implementation-level issues that can produce silently wrong results -- the worst possible outcome for an educational tool.

The recommended approach is a validation-first strategy: build a three-oracle test harness (SymPy symbolic exact, python-control numerical, MATLAB JSON gold standard), then systematically validate and fix the computation pipeline from polynomial primitives up through full MIMO transfer matrix assembly. The existing runtime stack (Python/FastAPI + React/Vite) does not change. The only new dependency is `python-control` as a dev/test-time oracle. SymPy, already a runtime dependency, provides the symbolic verification layer.

The highest-risk finding is PITFALL-02: Mason's graph determinant Delta should be computed once and shared across all transfer matrix entries, but the current code recomputes it per (input, output) pair after zero-gating mutations that may alter loop detection. This can produce entries with inconsistent denominators -- a mathematical impossibility for a true MIMO transfer matrix. Five critical pitfalls were identified in total (shared Delta, zero-gating mutation, adder sign handling, coefficient convention mismatch, DFS target revisit). All are addressable with targeted fixes and regression tests, but they must be fixed before any educational or visual features are built on top.

## Key Findings

### Recommended Stack

The existing runtime stack is unchanged. Validation tooling is dev-only.

**Core technologies (new, dev/test only):**
- **python-control (>=0.10.2):** MIMO transfer function oracle -- provides `control.tf()`, `control.feedback()`, `control.interconnect()` for numerical reference values. NOT a runtime dependency.
- **SymPy physics.control (already installed):** Symbolic exact verification via `TransferFunctionMatrix` and `MIMOFeedback`. Zero floating-point error for coefficient validation.
- **pytest + numpy.testing.assert_allclose:** Test framework with proper numerical comparison. Replaces the ad-hoc validation scripts.
- **pytest-timeout (>=2.2):** Prevents hanging tests on large Mason's graph enumerations.

**Tolerance strategy (from STACK.md):**
- TF coefficients vs symbolic oracle: rtol=1e-12
- Pole/zero locations: rtol=1e-6 (root-finding ill-conditioned)
- Step/impulse responses: rtol=1e-4 (ODE solver differences)
- Mason's path/loop enumeration: exact match (combinatorial, no tolerance)

**What NOT to use:** Slycot (FORTRAN dependency pain), harold (small community), Jest/Vitest for math (math lives in Python), NetworkX (parallel graph representation would drift), Hypothesis (textbook known-answer tests, not random property checks).

### Expected Features

**Must have (table stakes):**
- Correct superposition-based MIMO transfer matrix computation, validated against Ogata/Nise examples
- MIMO feedback loop correctness: Y = (I + GH)^{-1} G R for cross-coupled feedback
- Algebraic loop detection (prevents silent wrong answers from Mason's)
- Consistent shared denominator across all transfer matrix entries
- Signal dimension annotations on wires (educational requirement)
- p x m step/impulse response grid (not just G_11)
- Textbook-matched presets with documented expected answers
- Correct stability assessment (system-level, not per-entry OR)

**Should have (differentiators):**
- Step-by-step Mason's derivation overlay (flagship educational feature)
- Click-to-trace signal path with MIMO color-coding
- Interactive superposition demonstration (toggle inputs on/off)
- Export to MIMO Design Studio via System Hub
- Theory panels with KaTeX derivations

**Defer (v2+):**
- Decoupling analysis / RGA (graduate-level)
- Full symbolic matrix algebra engine
- Matrix-valued wire signals (bus signals)
- State-space conversion from transfer matrix (major architectural change)
- Validation mode (student-entered expected answer comparison)

### Architecture Approach

The validation architecture is three layers deep: (1) unit tests on polynomial primitives and single-pair Mason's gain, (2) MIMO system tests on full transfer matrix correctness for canonical topologies, (3) integration tests on API round-trips and frontend rendering contracts. Tests build diagrams programmatically (not via presets) to decouple test correctness from preset wiring. The production computation remains purely numeric (NumPy float64); SymPy is used only in the test harness as an independent oracle.

**Major components under test:**
1. **Polynomial helpers (`_pmul`, `_padd`, `_psub`)** -- low-power-first arithmetic, must be verified against both conventions
2. **`_solve_signal_flow()` / Mason's Gain** -- DFS path/loop enumeration, Delta/cofactor computation, single (input, output) pair
3. **`_solve_for_pair()` / Signal isolation** -- zero-gating mutation of other inputs, block state restoration
4. **`_compute_transfer_function()` / MIMO orchestrator** -- p*m pair iteration, transfer matrix assembly, shared denominator enforcement
5. **Domain conversion (`_operator_to_z`, `_operator_to_s`)** -- low-power-first to high-power-first, pole/zero extraction
6. **`to_hub_data()` / Hub export** -- MIMO TF serialization for cross-simulation transfer

### Critical Pitfalls

Ranked by severity and likelihood of producing wrong results:

1. **PITFALL-02: Shared denominator violation** -- Each I/O pair computes its own Delta independently. For MIMO, Delta is a graph property and must be identical across all entries. Fix: compute Delta once from the full graph before any zero-gating, share it. This is the highest-priority fix.

2. **PITFALL-01: Zero-gating mutates graph topology** -- Superposition implemented by mutating block types in-place creates "ghost loops" and fragile state. Fix: filter the adjacency list instead of mutating blocks. At minimum, add exhaustive before/after state verification tests.

3. **PITFALL-04: Coefficient convention mismatch** -- Internal low-power-first vs ecosystem high-power-first (NumPy, SciPy). Already caused BUG-001 and BUG-002. Fix: regression tests for every conversion path; consider a tagged Polynomial wrapper.

4. **PITFALL-03: Adder sign handling obscures feedback polarity** -- Negative feedback sign is baked into coefficient arrays, making debugging impossible. Fix: explicit positive/negative feedback classification in output metadata; test cases from Nise Ch. 5.

5. **PITFALL-05: Only G_11 plotted for MIMO** -- `get_plots()` hardcodes `matrix[0][0]`. Students cannot see cross-coupling. Fix: generate p x m response grid matching MIMO Design Studio pattern.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Mathematical Correctness Audit

**Rationale:** Nothing else matters if the math is wrong. All visual features, educational content, and Hub integration depend on correct transfer matrix computation. Five critical pitfalls live here.
**Delivers:** Validated, correct MIMO transfer matrix computation with comprehensive test suite.
**Addresses:** Mason's Gain correctness, MIMO feedback loops, algebraic loop detection, shared denominator enforcement, signal isolation correctness, adder sign handling, coefficient convention regression tests.
**Avoids:** PITFALL-01 (zero-gating), PITFALL-02 (shared Delta), PITFALL-03 (adder signs), PITFALL-04 (convention mismatch), PITFALL-08 (DFS target revisit).
**Test layers:** Layer 1 (polynomial unit tests) and Layer 2 (MIMO system tests).
**Stack needed:** python-control, pytest, numpy.testing, SymPy physics.control.

### Phase 2: Visual and Notation Accuracy

**Rationale:** With correct math established, fix how results are displayed. Educational tools must show correct notation or they teach wrong concepts.
**Delivers:** Full p x m response grid, signal dimension annotations, correct I/O labeling, MIMO SFG validation.
**Addresses:** MIMO response grid (table stake), dimension annotations on wires, index convention standardization (1-indexed labels vs 0-indexed arrays), transfer matrix display validation, notation corrections (G/H/T labeling).
**Avoids:** PITFALL-05 (only G_11 plotted), PITFALL-09 (index convention mismatch).
**Depends on:** Phase 1 (correct TF entries are prerequisite for correct plots).

### Phase 3: Textbook Presets and Integration Hardening

**Rationale:** With correct and well-displayed results, add reference examples and ensure cross-tool integration works.
**Delivers:** Ogata/Nise textbook presets with documented expected answers, API contract tests, Hub export for MIMO, benchmark registration.
**Addresses:** Textbook-matched presets, validation test suite (Layer 3), Hub MIMO export format, numerical drift mitigation for complex diagrams.
**Avoids:** PITFALL-06 (no SS conversion -- document limitation), PITFALL-07 (numerical drift), PITFALL-10 (dimensional consistency -- document limitation), PITFALL-11 (algebraic loop edge case), PITFALL-13 (Hub export format).
**Depends on:** Phase 1 (math correct) and Phase 2 (display correct).

### Phase 4: Educational Differentiators

**Rationale:** With a solid, validated foundation, build the features that make this tool uniquely valuable.
**Delivers:** Step-by-step Mason's derivation overlay, interactive superposition demo, theory panels, MIMO-specific educational presets with guided explanations.
**Addresses:** Flagship differentiators from FEATURES.md.
**Depends on:** All prior phases. Mason's overlay requires validated Mason's computation. Superposition demo requires validated signal isolation.

### Phase Ordering Rationale

- **Math before display:** PITFALL-02 (shared denominator) and PITFALL-01 (zero-gating) can produce structurally wrong transfer matrices. Building response grids or theory panels on top of wrong math wastes effort and teaches wrong concepts.
- **Display before presets:** Presets need correct display to be useful as reference examples. A preset with the right math but wrong labeling (PITFALL-09) or missing response plots (PITFALL-05) fails its educational purpose.
- **Presets before educational features:** Theory panels and step-by-step overlays reference specific examples. The presets must exist and be validated first.
- **Integration (Hub) is Phase 3 not Phase 1:** Hub export is important but not blocking. Students can use the BDB standalone. Hub integration needs the math to be correct first anyway.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 1:** PITFALL-02 fix (shared Delta computation) requires understanding how zero-gating interacts with loop enumeration. The fix approach (compute Delta from full graph) needs validation that it produces correct cofactors when inputs are isolated. Recommend `/gsd:research-phase` before implementation.
- **Phase 2:** MIMO SFG rendering (`convertToSFG()` is SISO-oriented). How to correctly render cross-coupling branches in the SFG view needs investigation. Current code may need significant rework.
- **Phase 3:** Hub MIMO format -- the Hub validator and MIMO Design Studio import paths need investigation to ensure format compatibility.

Phases with standard patterns (skip research-phase):
- **Phase 1 (test infrastructure):** pytest + python-control + SymPy oracle pattern is well-documented. Tolerance tiers are established.
- **Phase 2 (response grid):** MIMO Design Studio already implements p x m grids. Reuse the pattern directly.
- **Phase 4 (theory panels, KaTeX):** Established pattern across Controller Tuning Lab, Steady-State Error, and other simulations.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | python-control is the de facto Python standard for MIMO. SymPy physics.control confirmed in 1.14 docs. No novel dependencies. |
| Features | HIGH | Table stakes derived directly from Ogata/Nise textbook expectations. Differentiators identified by gap analysis vs MATLAB/Simulink. |
| Architecture | HIGH | Three-layer test architecture follows established patterns. Component boundaries mapped from direct codebase analysis of 3380+ line BDB. |
| Pitfalls | HIGH | All 13 pitfalls verified against actual code (line numbers cited). PITFALL-02 and PITFALL-04 corroborated by existing bug tracker entries (BUG-001, BUG-002). |

**Overall confidence:** HIGH

### Gaps to Address

- **Shared Delta computation fix:** The recommended fix (compute Delta once from full graph) has not been prototyped. It is theoretically sound but needs implementation validation -- cofactors must still be computed per-pair with the correct subset of non-touching loops relative to each forward path.
- **MIMO SFG rendering:** Current `convertToSFG()` was designed for SISO. No research was done on how to correctly render MIMO SFGs with cross-coupling branches. This needs dedicated investigation in Phase 2 planning.
- **Dimensional consistency (PITFALL-10):** The BDB treats all signals as scalars. True matrix-valued block transfer functions would require a major architectural change. The recommendation is to document this as a known limitation, not fix it in this milestone. Validate that the "superposition of SISO paths" interpretation is clearly communicated to students.
- **Tolerance tuning:** The tolerance tiers in STACK.md are based on general numerical analysis principles. Specific ill-conditioned test cases (repeated poles, near-cancellation) may need looser tolerances. Tune during Phase 1 implementation.

## Sources

### Primary (HIGH confidence)
- python-control docs (0.10.2) -- MIMO TF, interconnect, feedback
- SymPy Control API (1.14) -- TransferFunctionMatrix, MIMOFeedback
- NumPy testing docs -- assert_allclose specification
- Ogata, *Modern Control Engineering*, 5e -- Ch. 3 (TF/SS), Ch. 11 (MIMO)
- Nise, *Control Systems Engineering*, 7e -- Ch. 5 (Mason's rule)
- Direct codebase analysis -- `block_diagram_builder.py` (3380+ lines), `mimo_utils.py` (460 lines)

### Secondary (MEDIUM confidence)
- Duke University MIMO TF conventions PDF
- Lehigh Multivariable Robust Control lecture notes
- ETH Zurich CS2 MIMO introduction slides
- MATLAB Control System Toolbox documentation

### Tertiary (LOW confidence)
- andypfau/sfg library -- independent Mason's implementation, reference only
- Control Systems Academy web simulator -- competitor analysis

---
*Research completed: 2026-03-27*
*Ready for roadmap: yes*
