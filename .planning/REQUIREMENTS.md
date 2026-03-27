# REQUIREMENTS — MIMO Block Diagram Builder Hardening

## v1 Requirements

### Mathematical Correctness (MATH)

- [x] **MATH-01**: Mason's graph determinant Delta is computed once from the full graph and shared across all transfer matrix entries G_ij — no per-pair recomputation
- [ ] **MATH-02**: Superposition (zero-gating) isolates signals at the flow level without mutating block types in-place — topology remains stable during computation
- [x] **MATH-03**: Polynomial coefficient convention is consistent throughout (high-power-first for scipy/np.roots compatibility) with explicit conversion at boundaries
- [ ] **MATH-04**: Adder block signs are correctly applied in all feedback configurations — verified against Nise block diagram reduction rules
- [x] **MATH-05**: DFS traversal correctly handles target node revisit in cyclic graphs — forward paths and loops enumerated per Mason's definition (Ogata Ch.3)
- [ ] **MATH-06**: Transfer matrix G(s) for standard textbook MIMO topologies matches hand-computed results within 1e-10 tolerance
- [ ] **MATH-07**: Feedback loop reduction for MIMO produces correct closed-loop transfer matrix — verified against Ogata MIMO feedback formula

### Validation Infrastructure (TEST)

- [x] **TEST-01**: Polynomial arithmetic unit tests cover convolution, addition, and scalar operations with edge cases (zero polynomial, unity, high-order)
- [ ] **TEST-02**: MIMO transfer matrix correctness tests use programmatically-built textbook topologies (not GUI interactions)
- [ ] **TEST-03**: SymPy symbolic oracle cross-validates numeric transfer function results for at least 5 textbook examples
- [ ] **TEST-04**: API contract tests verify `/api/simulations/block_diagram_builder/execute` returns correct MIMO response format
- [x] **TEST-05**: Test suite runs via pytest with clear pass/fail per textbook example — integrated into validation/ directory
- [x] **TEST-06**: Tolerance-tiered validation: exact (1e-10) for polynomial math, loose (1e-6) for frequency response, visual for plots

### Visual & Notation (VIS)

- [ ] **VIS-01**: Full p×m transfer matrix response grid displays all G_ij(s) step/impulse responses — not just G_11
- [ ] **VIS-02**: MIMO-aware Signal Flow Graph conversion correctly represents multi-input multi-output topology following Oppenheim/Mason conventions
- [ ] **VIS-03**: I/O port labels match Ogata/Nise notation (U_1, U_2, ... for inputs; Y_1, Y_2, ... for outputs)

### Educational Content (EDU)

- [ ] **EDU-01**: At least 5 textbook preset MIMO block diagrams loadable by students (sourced from Ogata and Nise examples)
- [ ] **EDU-02**: Each preset includes expected transfer matrix G(s) for self-verification
- [ ] **EDU-03**: Preset descriptions reference specific textbook chapter/example numbers

## v2 Requirements (Deferred)

- [ ] Dimension annotations on wires showing signal vector sizes
- [ ] Step-by-step Mason's Gain overlay animation
- [ ] Interactive superposition demo (toggle inputs on/off, watch G_ij change)
- [ ] Theory panels with full Mason's formula derivation
- [ ] MATLAB reference JSON test vectors for cross-platform validation
- [ ] Benchmark registration in existing validation/run_scope_benchmarks.py framework
- [ ] Matrix block algebra (true MIMO matrix gains, not scalar-per-channel)

## Out of Scope

- MIMO Design Studio changes — this milestone is BDB-specific
- New simulation types — hardening existing, not adding new
- Mobile optimization — correctness before responsiveness
- Performance optimization — correctness before speed (but document Mason's path enumeration ceiling)
- True matrix-valued blocks (PITFALL-10) — fundamental architecture change, needs separate milestone

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| MATH-01 | Phase 2 | Complete |
| MATH-02 | Phase 3 | Pending |
| MATH-03 | Phase 1 | Complete |
| MATH-04 | Phase 3 | Pending |
| MATH-05 | Phase 2 | Complete |
| MATH-06 | Phase 5 | Pending |
| MATH-07 | Phase 4 | Pending |
| TEST-01 | Phase 1 | Complete |
| TEST-02 | Phase 5 | Pending |
| TEST-03 | Phase 5 | Pending |
| TEST-04 | Phase 6 | Pending |
| TEST-05 | Phase 1 | Complete |
| TEST-06 | Phase 1 | Complete |
| VIS-01 | Phase 7 | Pending |
| VIS-02 | Phase 8 | Pending |
| VIS-03 | Phase 7 | Pending |
| EDU-01 | Phase 9 | Pending |
| EDU-02 | Phase 9 | Pending |
| EDU-03 | Phase 9 | Pending |

---
*Last updated: 2026-03-28 after roadmap creation*
