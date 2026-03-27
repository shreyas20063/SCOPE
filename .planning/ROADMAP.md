# Roadmap: MIMO Block Diagram Builder Hardening

## Overview

This milestone hardens the MIMO transfer matrix computation in SCOPE's Block Diagram Builder. The work proceeds bottom-up: fix polynomial foundations and set up test infrastructure, then fix Mason's Gain computation (shared Delta, DFS traversal, signal isolation, adder signs, MIMO feedback), validate end-to-end against textbook examples with SymPy oracle, harden the API contract, fix visual/notation issues (response grid, SFG, labels), and finally add educational presets. Every fix is test-backed. Math correctness is the gating requirement -- nothing ships without validated computation.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Test Infrastructure & Polynomial Foundation** - Set up pytest framework, tolerance tiers, and fix coefficient convention with polynomial arithmetic tests
- [ ] **Phase 2: Shared Delta & Path Enumeration** - Fix Mason's graph determinant to compute once and share across all transfer matrix entries; fix DFS traversal for cyclic graphs
- [ ] **Phase 3: Signal Isolation & Adder Signs** - Fix zero-gating to not mutate topology; fix adder sign handling for all feedback configurations
- [ ] **Phase 4: MIMO Feedback Correctness** - Fix closed-loop transfer matrix computation for MIMO feedback systems
- [ ] **Phase 5: Transfer Matrix End-to-End Validation** - Validate full MIMO transfer matrix against hand-computed textbook results using SymPy oracle
- [ ] **Phase 6: API Contract & Integration Tests** - Verify API round-trip correctness for MIMO execute/update endpoints
- [ ] **Phase 7: MIMO Response Grid & Port Labels** - Display full p x m transfer matrix response grid with correct I/O labeling
- [ ] **Phase 8: MIMO Signal Flow Graph** - Fix SFG conversion for MIMO topology following Oppenheim/Mason conventions
- [ ] **Phase 9: Textbook Presets & Educational Content** - Add loadable Ogata/Nise preset MIMO diagrams with expected transfer matrices and textbook references

## Phase Details

### Phase 1: Test Infrastructure & Polynomial Foundation
**Goal**: Developers can run a pytest suite with tolerance-tiered assertions, and polynomial arithmetic is correct across all coefficient conventions
**Depends on**: Nothing (first phase)
**Requirements**: MATH-03, TEST-01, TEST-05, TEST-06
**Success Criteria** (what must be TRUE):
  1. Running `pytest validation/` from project root executes all tests with clear pass/fail output per test case
  2. Polynomial multiplication, addition, and subtraction produce correct coefficients for zero polynomial, unity, and high-order edge cases
  3. Coefficient convention (low-power-first internal vs high-power-first for scipy/np.roots) is consistent -- converting back and forth produces identical results
  4. Tolerance tiers are defined and enforced: exact (1e-10) for polynomial math, loose (1e-6) for frequency response, visual for plots
**Plans**: 2 plans

Plans:
- [x] 01-01-PLAN.md -- Test infrastructure: pytest config, dev dependencies, conftest.py with tolerance tiers and BDB fixture
- [x] 01-02-PLAN.md -- Polynomial arithmetic tests and coefficient convention conversion tests

### Phase 2: Shared Delta & Path Enumeration
**Goal**: Mason's graph determinant Delta is computed once from the full graph and correctly shared across all G_ij entries, with DFS correctly handling cycles
**Depends on**: Phase 1
**Requirements**: MATH-01, MATH-05
**Success Criteria** (what must be TRUE):
  1. For any MIMO diagram, all transfer matrix entries G_ij share the same denominator polynomial (the graph determinant Delta)
  2. DFS traversal enumerates all forward paths and loops per Mason's definition, including when the target node participates in a cycle
  3. A test case with known loops and forward paths produces exact match on enumerated paths/loops count and Delta polynomial
**Plans**: 2 plans

Plans:
- [x] 02-01-PLAN.md -- Tests for shared Delta denominator (MATH-01) and DFS path/loop enumeration (MATH-05)
- [x] 02-02-PLAN.md -- Refactor Mason's computation: graph-level Delta, extracted helpers, fixed DFS forward paths

### Phase 3: Signal Isolation & Adder Signs
**Goal**: Superposition isolates signals without mutating block types, and adder signs are correct for all feedback configurations
**Depends on**: Phase 2
**Requirements**: MATH-02, MATH-04
**Success Criteria** (what must be TRUE):
  1. After computing any G_ij via superposition, the block diagram topology is identical to before computation -- no block types or connections mutated
  2. Negative feedback loops produce the correct sign in the transfer function denominator (verified against Nise block diagram reduction rules)
  3. A mixed-feedback topology (positive and negative feedback in same diagram) produces correct transfer function for each path
**Plans**: 2 plans

Plans:
- [ ] 03-01-PLAN.md -- Test-first: MATH-02 signal isolation tests and MATH-04 adder sign verification tests
- [ ] 03-02-PLAN.md -- Replace block mutation with signal-level zero_inputs parameter threading

### Phase 4: MIMO Feedback Correctness
**Goal**: Closed-loop MIMO transfer matrix matches Ogata's MIMO feedback formula
**Depends on**: Phase 3
**Requirements**: MATH-07
**Success Criteria** (what must be TRUE):
  1. A 2x2 MIMO feedback system produces closed-loop transfer matrix matching Y = (I + GH)^{-1} G R within 1e-10 tolerance
  2. Cross-coupled feedback paths (where G_12 and G_21 are nonzero) produce correct off-diagonal closed-loop entries
**Plans**: TBD

Plans:
- [ ] 04-01: TBD

### Phase 5: Transfer Matrix End-to-End Validation
**Goal**: Full MIMO transfer matrix for standard textbook topologies matches hand-computed results, cross-validated by SymPy symbolic oracle
**Depends on**: Phase 4
**Requirements**: MATH-06, TEST-02, TEST-03
**Success Criteria** (what must be TRUE):
  1. At least 5 textbook MIMO topologies (programmatically built, not from presets) produce transfer matrices matching hand-computed results within 1e-10
  2. SymPy symbolic oracle independently confirms numeric results for all 5 topologies -- symbolic and numeric transfer functions have identical coefficients
  3. Test cases cover: parallel paths, nested feedback, cross-coupling, cascade MIMO, and single-loop MIMO
**Plans**: TBD

Plans:
- [ ] 05-01: TBD
- [ ] 05-02: TBD

### Phase 6: API Contract & Integration Tests
**Goal**: The BDB API endpoints return correct MIMO response format and handle edge cases gracefully
**Depends on**: Phase 5
**Requirements**: TEST-04
**Success Criteria** (what must be TRUE):
  1. POST `/api/simulations/block_diagram_builder/execute` with a MIMO diagram returns a response containing the full p x m transfer matrix in the expected format
  2. API returns appropriate error responses (not 500) for malformed diagrams, algebraic loops, and empty topologies
  3. Round-trip test: build diagram via API actions, compute transfer matrix, verify result matches direct computation
**Plans**: TBD

Plans:
- [ ] 06-01: TBD

### Phase 7: MIMO Response Grid & Port Labels
**Goal**: Users see all p x m transfer function responses and correct I/O labels matching textbook notation
**Depends on**: Phase 5
**Requirements**: VIS-01, VIS-03
**Success Criteria** (what must be TRUE):
  1. A 2-input 3-output MIMO diagram displays a 3x2 grid of step/impulse response plots (all G_ij, not just G_11)
  2. Input ports are labeled U_1, U_2, ... and output ports are labeled Y_1, Y_2, ... matching Ogata/Nise notation
  3. Each subplot in the response grid is labeled with its corresponding G_ij(s) entry
**Plans**: TBD

Plans:
- [ ] 07-01: TBD
- [ ] 07-02: TBD
**UI hint**: yes

### Phase 8: MIMO Signal Flow Graph
**Goal**: SFG toggle correctly renders MIMO topology with cross-coupling branches following Oppenheim/Mason conventions
**Depends on**: Phase 7
**Requirements**: VIS-02
**Success Criteria** (what must be TRUE):
  1. A MIMO block diagram with cross-coupling produces an SFG with all input-to-output signal paths visible as directed branches
  2. SFG nodes represent signals (not blocks) and branches carry transfer function gains, consistent with Mason's SFG definition
  3. Multi-input signals at summing junctions are rendered as separate incoming branches (not merged)
**Plans**: TBD

Plans:
- [ ] 08-01: TBD
**UI hint**: yes

### Phase 9: Textbook Presets & Educational Content
**Goal**: Students can load textbook MIMO examples, see expected transfer matrices, and trace results back to specific textbook sections
**Depends on**: Phase 7, Phase 8
**Requirements**: EDU-01, EDU-02, EDU-03
**Success Criteria** (what must be TRUE):
  1. At least 5 MIMO preset diagrams are loadable from the BDB preset menu, each sourced from a specific Ogata or Nise example
  2. Each preset displays its expected transfer matrix G(s) so students can compare against computed results
  3. Each preset description includes the textbook name, edition, chapter, and example number (e.g., "Ogata, 5e, Ch. 3, Example 3.5")
**Plans**: TBD

Plans:
- [ ] 09-01: TBD
- [ ] 09-02: TBD
**UI hint**: yes

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8 -> 9

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Test Infrastructure & Polynomial Foundation | 2/2 | Complete | 2026-03-27 |
| 2. Shared Delta & Path Enumeration | 0/2 | Not started | - |
| 3. Signal Isolation & Adder Signs | 0/2 | Not started | - |
| 4. MIMO Feedback Correctness | 0/1 | Not started | - |
| 5. Transfer Matrix End-to-End Validation | 0/2 | Not started | - |
| 6. API Contract & Integration Tests | 0/1 | Not started | - |
| 7. MIMO Response Grid & Port Labels | 0/2 | Not started | - |
| 8. MIMO Signal Flow Graph | 0/1 | Not started | - |
| 9. Textbook Presets & Educational Content | 0/2 | Not started | - |
