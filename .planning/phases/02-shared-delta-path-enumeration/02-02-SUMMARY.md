---
phase: 02-shared-delta-path-enumeration
plan: 02
subsystem: math
tags: [mason-gain-formula, signal-flow-graph, delta, dfs, polynomial, mimo]

# Dependency graph
requires:
  - phase: 02-shared-delta-path-enumeration plan 01
    provides: Test-first validation suite for shared Delta and DFS path enumeration
provides:
  - Graph-level Delta computation shared across all G_ij entries (MATH-01)
  - Fixed DFS forward-path enumeration preventing target-as-intermediate (MATH-05)
  - Extracted graph-level helper methods on BlockDiagramSimulator
affects: [03-zero-gating-elimination, 04-mimo-feedback, 05-symbolic-verification]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Graph-level loop enumeration before I/O pair iteration"
    - "Shared (delta_num, delta_den) passed into per-pair solvers"
    - "conn_port_map built once and threaded through all gain computations"
    - "Zero-TF entries receive cleaned/normalized shared Delta as denominator"

key-files:
  created: []
  modified:
    - backend/simulations/block_diagram_builder.py

key-decisions:
  - "Extracted local closure functions (block_tf, compute_loop_gain, compute_path_gain, compute_delta, compute_cofactor) as class methods with explicit parameters instead of closures"
  - "Zero-TF entries (no forward paths) use _clean_poly on delta_num for denominator to match non-zero entry denominator normalization"
  - "Deleted legacy _solve_for_pair and _solve_signal_flow outright rather than keeping as _legacy suffix -- cleaner codebase, all behavior verified by 58 tests"

patterns-established:
  - "Graph-level Mason's: loops enumerated once, Delta computed once, passed to per-pair solvers"
  - "DFS target-node handling: target only as terminal, never intermediate (prevents spurious paths)"

requirements-completed: [MATH-01, MATH-05]

# Metrics
duration: 23min
completed: 2026-03-27
---

# Phase 2 Plan 2: Shared Delta & Path Enumeration Implementation Summary

**Refactored Mason's Gain Formula to compute graph determinant Delta once at graph level and share across all MIMO transfer matrix entries, with fixed DFS forward-path enumeration**

## Performance

- **Duration:** 23 min
- **Started:** 2026-03-27T21:12:48Z
- **Completed:** 2026-03-27T21:35:21Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Graph determinant Delta now computed once from the full unmodified graph before I/O pair iteration (MATH-01)
- All G_ij entries in the MIMO transfer matrix share the same denominator polynomial
- DFS forward-path enumeration fixed to prevent target node from appearing as intermediate (MATH-05)
- Extracted 7 graph-level helper methods from nested closures to proper class methods
- Full 58-test suite green including previously-failing test_2x2_feedback_shared_denominator

## Task Commits

Each task was committed atomically:

1. **Task 1: Extract graph-level helpers and refactor _compute_transfer_function** - `554d032f` (feat)

## Files Created/Modified
- `backend/simulations/block_diagram_builder.py` - Refactored Mason's Gain computation with shared Delta, extracted helper methods, fixed DFS

## Decisions Made
- Extracted all local closure functions (block_tf, compute_loop_gain, compute_path_gain, compute_delta, compute_cofactor) as class methods with explicit parameters. This makes them independently testable and avoids nested closure complexity.
- Zero-TF entries (no forward paths between an I/O pair) now receive `_clean_poly(delta_num)` normalized as their denominator, ensuring consistency with non-zero entries that also clean and normalize their denominators.
- Deleted old `_solve_for_pair` and `_solve_signal_flow` methods entirely rather than renaming to `_legacy`. All behavior is verified by the 58-test suite, so keeping dead code adds no value.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Zero-TF entries had hardcoded denominator [1.0] instead of shared Delta**
- **Found during:** Task 1 (verification step)
- **Issue:** When no forward path exists between an I/O pair, the except ValueError branch returned `denominator: [1.0]` instead of the shared graph Delta. This violated MATH-01 for cross-path entries.
- **Fix:** Changed zero-TF fallback to use `_clean_poly(delta_num)` normalized by its constant term, matching the normalization applied to non-zero entries. Also fixed `num_loops` to report `len(all_loops)` instead of hardcoded 0.
- **Files modified:** `backend/simulations/block_diagram_builder.py`
- **Verification:** `test_2x2_feedback_shared_denominator` now passes -- all 4 entries have identical denominators.
- **Committed in:** 554d032f (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Essential for MATH-01 correctness. The plan's pseudocode didn't account for the zero-path edge case.

## Issues Encountered
None beyond the deviation above.

## Known Stubs
None -- all code paths are fully implemented with no placeholder data.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Shared Delta infrastructure is complete and tested
- Phase 3 (zero-gating elimination) can now safely remove the mutation pattern knowing Delta is graph-level
- The extracted helper methods (_build_adjacency, _build_conn_port_map, _block_tf, etc.) provide clean API for Phase 3's refactoring

---
*Phase: 02-shared-delta-path-enumeration*
*Completed: 2026-03-27*
