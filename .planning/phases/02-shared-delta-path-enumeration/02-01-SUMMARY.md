---
phase: 02-shared-delta-path-enumeration
plan: 01
subsystem: validation
tags: [testing, mason-gain, mimo, math-correctness]
dependency_graph:
  requires: [01-01, 01-02]
  provides: [MATH-01-tests, MATH-05-tests]
  affects: [02-02]
tech_stack:
  added: []
  patterns: [test-first, programmatic-topology-building]
key_files:
  created:
    - validation/test_shared_delta.py
  modified: []
decisions:
  - "Used handle_action('add_block', params) + handle_action('add_connection', params) API for programmatic topology building"
  - "Input block from_port is 0 (not 1) -- input/output blocks only have port 0"
  - "Junction fan-out uses same from_port=1 for multiple targets (fan-out allowed)"
  - "Custom TF coefficients set directly on block dict rather than parsing expressions"
metrics:
  duration: 6min
  completed: 2026-03-27
---

# Phase 02 Plan 01: Shared Delta and DFS Path Tests Summary

Test-first safety net for MATH-01 (shared Delta denominator) and MATH-05 (DFS forward path/loop enumeration) -- 7 tests covering correct Mason's Gain Formula behavior for MIMO transfer matrices.

## What Was Done

Created `validation/test_shared_delta.py` with 514 lines containing:

**TestSharedDelta (MATH-01) -- 4 tests:**
1. `test_2x1_shared_denominator` -- 2-input 1-output, no loops, verifies both denominators are [1.0] -- PASSES
2. `test_2x2_feedback_shared_denominator` -- 2-input 2-output with two independent feedback loops, verifies all 4 denominators are identical -- FAILS (expected: current code computes Delta per-pair)
3. `test_1x2_shared_denominator` -- 1-input 2-output, no loops, verifies both denominators are [1.0] -- PASSES
4. `test_siso_still_works_after_refactor` -- SISO negative feedback regression test, G/(1+GH) = 1.0 -- PASSES

**TestDFSForwardPaths (MATH-05) -- 3 tests:**
5. `test_no_target_as_intermediate` -- Single forward path with feedback loop, 1 path 1 loop -- PASSES
6. `test_known_topology_path_count` -- Two parallel forward paths, 0 loops -- PASSES
7. `test_known_topology_loop_count` -- Two cascaded feedback loops, 1 path 2 loops -- PASSES

## Test Results

- 6 passed, 1 failed (expected)
- The `test_2x2_feedback_shared_denominator` failure confirms MATH-01 bug: current `_solve_for_pair` computes Delta independently per (input, output) pair, so G[0][0] gets denominator [1, 2] while G[0][1] gets [1, 0]
- Full validation suite: 57 passed, 1 failed (no regressions)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed handle_action call signature**
- **Found during:** Task 1
- **Issue:** Plan interface spec showed `sim.handle_action({"action": "...", "params": {...}})` but actual signature is `sim.handle_action(action_str, params_dict)` with two positional arguments
- **Fix:** Changed all calls to use correct 2-argument form
- **Files modified:** validation/test_shared_delta.py

**2. [Rule 3 - Blocking] Fixed action name for connections**
- **Found during:** Task 1
- **Issue:** Plan used action name "connect" but actual action name in the simulator is "add_connection"
- **Fix:** Changed all connect calls to use "add_connection"
- **Files modified:** validation/test_shared_delta.py

**3. [Rule 1 - Bug] Fixed input block port numbers**
- **Found during:** Task 1
- **Issue:** Plan used from_port=1 for input blocks, but input/output blocks only have port 0 (max_port_index returns 0). The error was silently swallowed by handle_action's try/except, causing 0 connections and 0 forward paths.
- **Fix:** Changed all input block from_port from 1 to 0
- **Files modified:** validation/test_shared_delta.py

## Decisions Made

1. Used `_get_block_id(sim, type, index)` helper to look up auto-generated block IDs by type and creation order, avoiding hardcoded IDs
2. Set custom TF coefficients directly on `sim.blocks[ctf]` dict rather than using `update_block_value` (which requires expression string parsing)
3. Did NOT use `pytest.mark.xfail` on the expected-to-fail test as instructed -- it fails naturally for Plan 02-02 to confirm the fix

## Known Stubs

None -- all tests are fully implemented and wired to the real simulator.

## Self-Check: PASSED
