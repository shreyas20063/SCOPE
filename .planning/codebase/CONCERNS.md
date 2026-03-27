# Codebase Concerns

**Analysis Date:** 2026-03-27

## Tech Debt

**Duplicated Pade Approximation Implementation:**
- Issue: `_pade()` is copy-pasted in three locations with identical logic
- Files: `backend/simulations/controller_tuning_lab.py` (line 12), `backend/rl/es_policy.py` (line 18), `backend/simulations/nyquist_stability.py` (`_build_pade` at line 278)
- Impact: Bug fixes (e.g., BUG-012 coefficient ordering) must be applied in all three locations. Risk of divergence.
- Fix approach: Extract to `backend/core/math_utils.py` as a shared `pade_approximation()` function. Import everywhere.

**Duplicated trapz Compatibility Shim:**
- Issue: The `_trapz = np.trapezoid if hasattr(np, 'trapezoid') else np.trapz` one-liner is repeated in 5 files
- Files: `backend/core/controllers.py` (line 19), `backend/simulations/lead_lag_designer.py` (line 16), `backend/simulations/ivt_fvt_visualizer.py` (line 20), `backend/simulations/signal_operations.py` (line 17), `backend/simulations/convolution_simulator.py` (line 23)
- Impact: Minor, but unnecessary repetition. When NumPy 2.0+ becomes the minimum, all need updating.
- Fix approach: Move to `backend/core/compat.py` and import from there.

**Stale SIMULATION_LIST in config.py:**
- Issue: `backend/config.py` contains a hardcoded `SIMULATION_LIST` with 13 entries (lines 33-47) that is never imported or used anywhere. The real source of truth is `backend/simulations/catalog.py` (61+ simulations).
- Files: `backend/config.py` (lines 33-47)
- Impact: Confusing for new developers. May mislead someone into using the wrong list.
- Fix approach: Delete `SIMULATION_LIST` from `config.py`.

**CORS Config Unused:**
- Issue: `backend/config.py` defines `CORS_SETTINGS` with specific origins, but `backend/main.py` (line 109) overrides with `allow_origins=["*"]`. The config import is used only for `API_PREFIX`.
- Files: `backend/config.py` (lines 6-20), `backend/main.py` (line 109)
- Impact: False sense of CORS restriction. The `CORS_ORIGINS` list in config.py is dead code.
- Fix approach: Either use `CORS_SETTINGS` from config or delete the dead code. See Security section below.

**Giant SimulationViewer.jsx (2242 lines, 158 const/arrow declarations):**
- Issue: Single component handles viewer chain dispatch for 50+ simulation types via a massive if/else chain (lines 1739-2040+), plus 8 inline sub-components defined before the main export.
- Files: `frontend/src/components/SimulationViewer.jsx`
- Impact: Any new simulation requires editing this file. High merge conflict risk. Hard to reason about. The viewer chain alone is ~300 lines of ternary expressions.
- Fix approach: Extract the viewer chain into a `ViewerRegistry` lookup map (`{simulation_type: ComponentClass}`). Extract inline sub-components (ConvolutionInfo, DCMotorInfo, etc.) to separate files.

**Giant catalog.py (4083 lines):**
- Issue: Every simulation's full metadata (controls, plots, descriptions, tags) lives in a single Python file.
- Files: `backend/simulations/catalog.py`
- Impact: Merge conflicts when multiple simulations are added simultaneously. File is hard to navigate.
- Fix approach: Consider co-locating catalog entries with their simulator files (e.g., `CATALOG_ENTRY` class attribute on each simulator) and auto-collecting them in `catalog.py`.

**Giant block_diagram_builder.py (3366 lines):**
- Issue: Single file contains the entire BDB simulator: parser, graph algorithms (Mason's, SFG conversion, loop detection), block models, connection logic, layout engine.
- Files: `backend/simulations/block_diagram_builder.py`
- Impact: Hard to test individual components. High cognitive load for modifications.
- Fix approach: Extract graph algorithms to `backend/core/graph_utils.py`, parser to `backend/simulations/bdb_parser.py`.

**main.py Contains RL Training Endpoints (896 lines total):**
- Issue: `backend/main.py` includes RL-specific training endpoints (ES, PPO) with global mutable state (`_es_training_task`, `_es_training_status`, `_ppo_trainer`) at lines 710-896. These are domain-specific and don't belong in the main app file.
- Files: `backend/main.py` (lines 700-896)
- Impact: Bloats the main entry point. Global state is hard to reason about.
- Fix approach: Move to `backend/routes/rl_training.py` as a FastAPI router.

**sys.path Manipulation at Runtime:**
- Issue: `controller_tuning_lab.py` manipulates `sys.path` in three places (lines 1593, 1604, 1633) to import RL modules at runtime.
- Files: `backend/simulations/controller_tuning_lab.py`
- Impact: Fragile import mechanism. Path is inserted at position 0, potentially shadowing other modules.
- Fix approach: Structure RL as a proper Python package with `__init__.py` and use relative imports or configure `PYTHONPATH` at startup.

**Massive CSS Files:**
- Issue: `SimulationViewer.css` is 3390 lines, `App.css` is 2077 lines, `BlockDiagramViewer.css` is 1662 lines. Total CSS: ~25,000 lines across all files.
- Files: `frontend/src/styles/SimulationViewer.css`, `frontend/src/styles/App.css`, `frontend/src/styles/BlockDiagramViewer.css`
- Impact: Specificity conflicts, dead CSS rules likely accumulating. No CSS modules or scoping.
- Fix approach: Consider CSS modules per component, or at minimum split `SimulationViewer.css` per viewer.

## Known Bugs

**Tracked in `.claude/bugs.md`:**
- 20+ bugs documented (BUG-001 through BUG-020+), all marked as Fixed
- Recurring themes: JSON serialization of NaN/inf (BUG-006, BUG-019), Plotly `scaleanchor` axis rescaling (BUG-007, BUG-020), polynomial coefficient ordering (BUG-002, BUG-012), stale state on mode switches (BUG-018)
- No currently open bugs recorded, but the pattern of NaN/inf bugs suggests more may lurk in newer simulators

**Tracked in `.claude/mistakes.md`:**
- MISTAKE-001 through MISTAKE-004 documented
- Critical pattern: soft assertions hiding test failures, same-session code+test having shared wrong assumptions, CSS opacity hiding child elements

## Security Considerations

**CORS Wildcard in Production:**
- Risk: `backend/main.py` line 109 sets `allow_origins=["*"]` -- any website can make API requests to the backend
- Files: `backend/main.py` (line 109)
- Current mitigation: The platform is educational with no user data or authentication. No state-changing operations beyond simulation parameter updates.
- Recommendations: For production deployment, restrict to the actual frontend origin. Use the `CORS_SETTINGS` from `backend/config.py` instead of the wildcard.

**Expression Evaluation via Python eval():**
- Risk: Multiple files use Python's `eval()` built-in for user-supplied mathematical expressions. The `__builtins__={}` sandbox is not fully secure in CPython -- attribute access on allowed objects can potentially escape the sandbox.
- Files: `backend/simulations/signal_parser.py` (lines 222, 240, 286, 301), `backend/simulations/phase_portrait.py` (line 101), `backend/simulations/nonlinear_control_lab.py` (uses expression validation with blocked keywords at line 41)
- Current mitigation: `__builtins__` set to `{}`, keyword blocklist (`import`, `exec`, `__`, `open`, `os.`, `subprocess`, etc.), restricted namespace with only numpy math functions
- Recommendations: Consider using SymPy `parse_expr` with `_ALLOWED_SYMBOLS` and `_SAFE_TRANSFORMATIONS` (already used in `backend/simulations/state_space_analyzer.py` lines 22-28) as the standard approach for all expression parsing. The AST-based approach in `backend/simulations/operator_algebra.py` (line 93, `_SAFE_NODES` whitelist) is another safer pattern.

**No Authentication or Authorization:**
- Risk: All API endpoints are publicly accessible. RL training endpoints can be triggered by anyone.
- Files: `backend/main.py` (all routes)
- Current mitigation: Educational platform, no sensitive data
- Recommendations: If deploying publicly, add rate limiting (already implemented but disabled at line 154) and consider API keys for training endpoints.

**No Content-Security-Policy or HSTS Headers:**
- Risk: Missing CSP header allows XSS via injected scripts. No HSTS for HTTPS enforcement.
- Files: `backend/main.py` (lines 124-151 -- security headers middleware)
- Current mitigation: X-XSS-Protection and X-Content-Type-Options are set
- Recommendations: Add `Content-Security-Policy` header. Add `Strict-Transport-Security` if serving over HTTPS.

**Hardcoded WebSocket URL:**
- Risk: Frontend WebSocket hook hardcodes `localhost:8000` for development
- Files: `frontend/src/hooks/useWebSocketSimulation.js` (line 22)
- Current mitigation: Only affects development mode
- Recommendations: Use environment variable or derive from `window.location` for production.

## Performance Bottlenecks

**Unbounded Simulator Instance Cache:**
- Problem: `active_simulators` dict in `backend/main.py` (line 172) grows without bound -- one entry per unique `sim_id` accessed. Simulators are never evicted.
- Files: `backend/main.py` (lines 172-197)
- Cause: No eviction policy, no max size, no cleanup in periodic_cleanup
- Improvement path: Add LRU eviction or TTL-based cleanup. With 61+ simulators and potential custom TF variants, memory grows indefinitely.

**Thread-Based Execution with Global Lock:**
- Problem: `SimulationExecutor` uses a threading lock (line 79) and spawns a new thread per execution. The lock serializes all simulation computations.
- Files: `backend/core/executor.py` (lines 49, 79-99)
- Cause: Single `_lock` on the executor instance means only one simulation can compute at a time across all users.
- Improvement path: Use per-simulator locks instead of a global executor lock, or use `asyncio` with `run_in_executor` and a thread pool.

**Region of Attraction Grid Computation:**
- Problem: Nonlinear Control Lab computes a 25x25 grid of initial conditions (625 ODE solves) for region of attraction analysis, using `ThreadPoolExecutor(max_workers=8)`.
- Files: `backend/simulations/nonlinear_control_lab.py` (line 895)
- Cause: Each IC requires a full ODE integration. 625 solves at ~10ms each = ~800ms blocking.
- Improvement path: Reduce grid resolution for initial response, allow user to request higher resolution. Cache results per (plant, controller) pair.

**Large JSON Payloads:**
- Problem: Some simulations return large plot data (thousands of points per trace, multiple traces). GZip helps but serialization cost remains.
- Files: `backend/core/data_handler.py` (LTTB subsampling exists but may not be applied uniformly)
- Cause: Plotly traces can have 1000+ points. Simulations with 6-8 plots multiply this.
- Improvement path: Ensure LTTB downsampling is applied consistently across all simulators. Consider binary protocols for WebSocket data.

**SymPy Symbolic Solve Timeout:**
- Problem: `state_space_analyzer.py` spawns a background thread for SymPy symbolic solving with a 6-second timeout. If SymPy hangs, the thread is abandoned (daemon thread, not killed).
- Files: `backend/simulations/state_space_analyzer.py` (lines 1213-1221)
- Cause: SymPy `solve()` can hang indefinitely on complex expressions. Python threads cannot be forcefully killed.
- Improvement path: Use `multiprocessing` with `terminate()` for true cancellation, or limit expression complexity before attempting symbolic solve.

## Fragile Areas

**SimulationViewer.jsx Viewer Chain:**
- Files: `frontend/src/components/SimulationViewer.jsx` (lines 1739-2040+)
- Why fragile: 50+ simulation types dispatched via a single if/else ternary chain. Adding a new simulation requires finding the right insertion point. Missing an entry means the simulation silently falls through to `PlotDisplay`.
- Safe modification: Add new entries at the end of the chain, before the final `PlotDisplay` fallback. Always test that the custom viewer actually renders.
- Test coverage: No automated tests for viewer dispatch.

**Block Diagram Builder State Machine:**
- Files: `backend/simulations/block_diagram_builder.py`
- Why fragile: `handle_action()` catches ALL exceptions into `self._error` (line 261). Silent failures mean connections, blocks, or computations can fail without the caller knowing. Graph algorithms (Mason's, loop detection) depend on correct connection topology.
- Safe modification: Always check `state["metadata"]["error"]` after any `handle_action()` call. Verify connection counts after building diagrams. See `.claude/bugs.md` BUG-001 through BUG-004 and `.claude/mistakes.md` MISTAKE-002.
- Test coverage: `backend/test_multiloop.py` covers multi-loop topologies. `backend/test_e2e.py` covers basic flows.

**Mode-Switching in Stateful Simulators:**
- Files: `backend/simulations/controller_tuning_lab.py`, `backend/simulations/steady_state_error.py`, `backend/simulations/nonlinear_control_lab.py`
- Why fragile: Simulators with multiple modes (controller type, plant preset, tuning method) must reset dependent state when modes change. BUG-018 documents a case where stale `_tuning_info`, `_cl_num`, `_cl_den` persisted across mode switches.
- Safe modification: When adding a new mode-select parameter, audit all `update_parameter()` branches to reset derived state. Add reset logic for every new dependent field.
- Test coverage: Minimal -- most mode-switch bugs were found manually.

**Frontend Parameter Flush Race Condition:**
- Files: `frontend/src/hooks/useSimulation.js`
- Why fragile: `flushUpdates()` drops parameter changes queued during in-flight requests. BUG-018 item 4 documents the fix (retry after flush completes), but the pattern of debounced updates + in-flight guards is inherently race-prone.
- Safe modification: Test rapid parameter changes (slider dragging) to verify all updates reach the backend.
- Test coverage: No automated tests.

**JSON Serialization Edge Cases:**
- Files: `backend/core/data_handler.py`
- Why fragile: Python 3.13+ rejects NaN/inf in JSON. BUG-006 and BUG-019 fixed known paths, but any new simulator returning NaN/inf in a dict that bypasses `DataHandler.serialize_result()` will crash.
- Safe modification: Always route simulator output through `DataHandler.serialize_result()`. Never return `float("inf")` or `float("nan")` in early-return paths. Test with `json.dumps(state).encode('utf-8')`.
- Test coverage: No systematic test for NaN/inf in all simulator outputs.

## Scaling Limits

**In-Memory Simulator State:**
- Current capacity: One `active_simulators` dict per process. All simulator instances live in memory.
- Limit: With 61+ simulators and stateful instances, memory grows linearly. No horizontal scaling possible -- simulators are not serializable.
- Scaling path: Stateless computation model where simulators re-initialize from parameters on each request, or external state store (Redis).

**Single-Process Architecture:**
- Current capacity: One uvicorn process (or gunicorn with workers, but simulator state is per-process)
- Limit: Cannot share simulator state across workers. Each worker has its own `active_simulators` dict.
- Scaling path: Make simulators stateless (re-compute from params each time) or use shared state backend.

## Dependencies at Risk

**NumPy <2.0 Pin:**
- Risk: `requirements.txt` pins `numpy>=1.24.0,<2.0.0`. NumPy 2.0+ is already released and brings breaking changes (`np.trapz` removal, `np.float_` removal). The pin prevents security patches from NumPy 2.x.
- Impact: The `_trapz` compatibility shim exists but the pin blocks adoption. Other NumPy 2.0 deprecations may exist.
- Migration plan: Remove the `<2.0.0` pin, test all simulators, replace `_trapz` shim with direct `np.trapezoid` calls.

**SciPy <2.0 Pin:**
- Risk: `scipy>=1.10.0,<2.0.0` pin. SciPy 2.0 removed `scipy.signal.pade` (replaced by custom `_pade` implementations -- see BUG-012).
- Impact: Already mitigated for pade, but other SciPy 2.0 removals may surface.
- Migration plan: Test with SciPy 2.0+. The custom `_pade` already exists.

**No Frontend Test Framework:**
- Risk: `package.json` has no test dependencies (no jest, vitest, or testing-library). Zero frontend test coverage.
- Impact: All frontend changes rely on manual testing. Regressions in viewer chain, parameter handling, or 3D components go undetected.
- Migration plan: Add vitest + @testing-library/react. Start with critical paths: `useSimulation` hook, `SimulationViewer` dispatch, `ControlPanel` rendering.

## Missing Critical Features

**No Frontend Tests:**
- Problem: Zero test files in `frontend/src/`. No test runner configured.
- Blocks: Automated regression detection for UI changes. CI/CD pipeline cannot verify frontend.

**No CI/CD Pipeline:**
- Problem: No `.github/workflows/`, no `Jenkinsfile`, no CI configuration detected.
- Blocks: Automated testing, deployment, and code quality checks on pull requests.

**Rate Limiting Disabled:**
- Problem: Rate limiting middleware exists (`backend/utils/rate_limiter.py`) but is commented out in `backend/main.py` (lines 154-165).
- Blocks: Protection against abuse if deployed publicly. RL training endpoints are especially vulnerable to DoS.

**No Input Validation at API Layer:**
- Problem: Parameter validation relies on per-simulator `_validate_param()` methods, but there is no schema-level validation at the API layer. Malformed or out-of-range values reach the simulator.
- Blocks: Consistent error messages. Defense in depth.

## Test Coverage Gaps

**Frontend -- Zero Coverage:**
- What's not tested: All React components, hooks, services, routing
- Files: All of `frontend/src/`
- Risk: Any refactor can break the UI silently
- Priority: High

**Backend Simulators -- Minimal Coverage:**
- What's not tested: Most of the 61 simulator files have no dedicated unit tests. Only `backend/test_e2e.py` (1959 lines) and `backend/test_multiloop.py` (1245 lines) exist, plus `backend/tests/test_hub_validator.py`.
- Files: All of `backend/simulations/` except what `test_e2e.py` covers
- Risk: Algorithm correctness, edge cases (NaN/inf, degenerate inputs), mode switching
- Priority: High -- given the 20+ bugs found in `.claude/bugs.md`, many from missing test coverage

**WebSocket Communication:**
- What's not tested: WebSocket real-time update flow, reconnection, message serialization
- Files: `backend/main.py` (WebSocket endpoints), `frontend/src/hooks/useWebSocketSimulation.js`
- Risk: Silent failures in real-time updates
- Priority: Medium

**3D Visualizations:**
- What's not tested: Three.js components (Furuta Pendulum, Ball and Beam, Coupled Tanks, Inverted Pendulum, Mass-Spring)
- Files: `frontend/src/components/*3D*.jsx` (8 files)
- Risk: Memory leaks from unreleased Three.js resources, rendering errors on different devices
- Priority: Medium -- manual testing currently required

---

*Concerns audit: 2026-03-27*
