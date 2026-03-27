# Domain Pitfalls: MIMO Block Diagram Validation

**Domain:** MIMO block diagram computation, transfer matrix, Mason's gain formula, state-space conversion
**Researched:** 2026-03-27
**Codebase:** `backend/simulations/block_diagram_builder.py`
**Confidence:** HIGH (code-verified against textbook definitions)

---

## Critical Pitfalls

Mistakes that produce wrong transfer functions, wrong stability conclusions, or wrong student understanding. Each of these can silently give incorrect answers.

---

### PITFALL-01: Superposition via Zero-Gating Mutates Graph Topology for Loop Detection

**What goes wrong:** The current `_solve_for_pair()` implements superposition by temporarily changing other input blocks to `type: "gain"` with `value: 0.0`. This changes the graph topology that `_dfs_loops()` traverses. An input block has 0 inputs and 1 output, but a gain block has 1 input and 1 output. If any connection feeds INTO an input block (which would be an illegal wiring but could exist in user-built diagrams), the zero-gated gain block now accepts that connection, potentially creating new loops that don't exist in the real system.

More subtly: even without illegal wiring, the zero-gain block still participates in path/loop enumeration. A loop passing through a zero-gain block produces a loop gain of zero, which is mathematically correct (the loop vanishes). However, the loop is still enumerated and included in the `all_loops` list. This means the cofactor computation may differ from the true graph because non-touching loop analysis includes "ghost loops" with zero gain. While the gain is zero and the math works out, it wastes computation and makes debugging harder.

**Why it happens:** Superposition was implemented by mutation rather than by filtering the signal flow graph.

**Consequences:** In the common case, results are correct because zero-gain loops contribute zero to Delta. But edge cases exist where the mutation creates spurious connectivity.

**Warning signs in code:** `self.blocks[bid]["type"] = "gain"` in `_solve_for_pair()` (line 1555).

**Prevention:**
- **Test case:** Create a diagram where input u2 has a wire feeding INTO it from some block (illegal but possible in the UI). Verify that `_solve_for_pair(u1, y1, ...)` does not find loops involving the mutated u2.
- **Better approach:** Instead of mutating block types, filter the adjacency at the signal flow level. When computing G_ij, only allow signal to originate from input_i. Other inputs contribute zero signal without changing the graph structure.
- **Textbook reference:** Ogata Ch. 3.7 (MIMO transfer functions via superposition); Nise Ch. 5 (Mason's rule applied per I/O pair).

**Phase:** Phase 1 (Math correctness audit)

---

### PITFALL-02: Mason's Gain Formula Applied Per-Element Misses Shared Denominator Requirement

**What goes wrong:** The current implementation computes each G_ij(s) independently via Mason's formula, yielding potentially different denominators for each entry in the transfer matrix. For a true MIMO system, the denominator polynomial (the graph determinant Delta) should be THE SAME for all entries in the transfer matrix, because Delta depends only on the loops in the graph, not on which input-output pair you are evaluating. Only the cofactors Delta_k differ per forward path.

If the superposition zero-gating actually changes loop detection (see PITFALL-01), different I/O pairs could compute different Delta values, producing a transfer matrix where entries have inconsistent denominators. This is mathematically wrong -- G(s) = N(s)/Delta(s) where N(s) is a polynomial matrix but Delta(s) is a single scalar polynomial.

**Why it happens:** Each call to `_solve_signal_flow()` independently discovers loops via `_dfs_loops()`, then computes its own Delta. The zero-gating mutation may alter which loops are discovered.

**Consequences:**
- Transfer matrix entries with different denominators cannot be correctly combined into a state-space realization.
- MIMO stability analysis requires a single characteristic polynomial. Different denominators per entry make this impossible.
- Students learn the wrong mental model: that each G_ij has its own independent characteristic equation.

**Warning signs in code:** Each `_solve_for_pair()` call invokes `_solve_signal_flow()` which runs its own `_dfs_loops()` and `compute_delta()` (lines 1652-1656, 1810). No shared Delta across pairs.

**Prevention:**
- **Test case:** Build the 2x2 coupled preset. Extract denominators from all four G_ij entries. Assert they are identical polynomials (up to normalization).
  ```python
  # Expected: all entries share denominator
  G = sim._compute_transfer_function()
  denoms = [G["transfer_matrix"][i][j]["denominator"] for i in range(2) for j in range(2)]
  for d in denoms[1:]:
      assert np.allclose(d, denoms[0]), f"Denominator mismatch: {d} vs {denoms[0]}"
  ```
- **Fix approach:** Compute Delta ONCE from the full graph (no zero-gating), then use it as the shared denominator for all entries. Only paths and cofactors change per I/O pair.
- **Textbook reference:** Ogata Ch. 3.7, Eq. (3-38): G(s) = adj(sI-A) / det(sI-A), showing single denominator. Nise Ch. 5 Example 5.9 (Mason's: Delta is graph-level, not path-level).

**Phase:** Phase 1 (Math correctness audit) -- this is the highest-priority fix.

---

### PITFALL-03: Adder Sign Handling in Loop Gain Misses the Negative Feedback Convention

**What goes wrong:** In `compute_loop_gain()`, adder signs are applied based on which port the previous block in the loop connects to. The code checks `signs[port_idx]` and negates the gain if the sign is `"-"`. This is correct for the path traversal order, but there is a subtle issue: a loop's gain sign determines whether it is negative or positive feedback. If the loop wraps around and re-enters the adder on a negative port, the loop gain should be NEGATIVE, meaning it is negative feedback and the characteristic equation is `1 + |L|` not `1 - |L|`.

The current implementation handles this correctly in isolation, but the sign is baked into the loop gain polynomial rather than being tracked separately. This makes it impossible to verify the classic textbook identity: for negative feedback, `T = G/(1+GH)`. The sign is hidden inside the coefficient array.

**Why it happens:** The implementation conflates the loop gain magnitude with the feedback sign.

**Consequences:**
- Debugging is extremely difficult because you cannot inspect whether a loop is positive or negative feedback without tracing through the polynomial coefficients.
- If adder signs are misconfigured (e.g., default `["+", "+", "+"]` when user intended negative feedback), the error is silent -- no warning, just wrong results.

**Warning signs in code:** `signs = block.get("signs", ["+", "+", "+"])` (line 1694, 1715). Default is all-positive, meaning a standard negative-feedback loop requires the user to explicitly set `"-"` on the correct port.

**Prevention:**
- **Test case:** Build a unity negative feedback loop: `u -> adder(-) -> G -> y`, with `y -> adder(port1, sign="-")`. Verify loop gain is `-G` (negative). Then verify the closed-loop TF is `G/(1+G)`.
  ```python
  # Classic unity feedback: G/(1+G)
  # G = 2.0 => TF = 2/3
  sim.handle_action({"action": "load_preset", "params": {"preset": "first_order_ct"}})
  tf = sim._compute_transfer_function()
  # Verify: numerator evaluates to G at s=0, denominator to 1+G
  ```
- **Better approach:** Log whether each loop is positive or negative feedback explicitly in the output metadata. Show this in the UI so students can verify their wiring.
- **Textbook reference:** Nise Ch. 5.2 (negative feedback sign convention); Ogata Ch. 3.5 (closed-loop TF derivation, sign conventions).

**Phase:** Phase 1 (Math correctness audit)

---

### PITFALL-04: Polynomial Coefficient Convention Mismatch (Low-Power-First vs High-Power-First)

**What goes wrong:** The internal representation uses low-power-first: `coeffs[i]` = coefficient of R^i (or A^i). But `np.roots()`, `np.poly()`, `scipy.signal`, and standard textbooks all use high-power-first (descending powers). The code has `_operator_to_z()` and `_operator_to_s()` conversion methods, but any new code that forgets to convert will silently produce wrong results.

This is not hypothetical -- BUG-001 and BUG-002 in the bug tracker are both consequences of coefficient convention confusion.

**Why it happens:** Low-power-first is natural for the operator representation (building up polynomials term by term), but the rest of the scientific Python ecosystem uses high-power-first.

**Consequences:**
- Poles and zeros computed from unconverted polynomials are wrong.
- Stability conclusions based on wrong poles are wrong.
- The error is SILENT -- no exception, just wrong numbers.

**Warning signs in code:** Any call to `np.roots()`, `np.poly()`, `scipy.signal.*` that does not go through `_operator_to_z()` or `_operator_to_s()` first.

**Prevention:**
- **Test case:** For every polynomial operation that produces poles/zeros, verify against a known system.
  ```python
  # First-order system: H(z) = 1/(1 - 0.5z^-1)
  # Low-power-first operator: num=[0,1], den=[1,-0.5] (R-domain)
  # High-power-first z-domain: num=[1,0], den=[1,-0.5]
  # Pole should be at z=0.5
  z_num, z_den = sim._operator_to_z(np.array([0., 1.]), np.array([1., -0.5]))
  poles = np.roots(z_den)
  assert np.isclose(poles[0], 0.5)
  ```
- **Structural fix:** Add a `Polynomial` wrapper class or named tuple that carries its convention tag, making it impossible to accidentally pass low-power-first to `np.roots()`.
- **Textbook reference:** Oppenheim Ch. 10 (z-transform conventions); Ogata Ch. 2.4 (transfer function representation).

**Phase:** Phase 1 (Math correctness audit) -- add regression tests for every conversion path.

---

### PITFALL-05: MIMO Plot Generation Only Shows G_11

**What goes wrong:** `get_plots()` (line 3113-3128) checks `tf.get("mimo")` and then uses `matrix[0][0]` as the entry for plotting. This means for a 2x2 MIMO system, only the first input to first output transfer function is plotted. The student sees one step/impulse response and has no way to visualize G_12, G_21, or G_22 from the Block Diagram Builder.

**Why it happens:** The plotting code was written for SISO and minimally extended for MIMO without generating the full response grid.

**Consequences:**
- Students cannot verify their MIMO block diagram by comparing step responses across all I/O pairs.
- Cross-coupling effects (G_12, G_21) -- the most important aspect of MIMO systems -- are invisible.
- The MIMO Design Studio generates full p x m response grids, creating an inconsistency where the same system shows different information in different tools.

**Warning signs in code:** `entry = matrix[0][0]` (line 3117). Hardcoded index, no iteration over the matrix.

**Prevention:**
- **Test case:** Load the `mimo_2x2_coupled` preset. Call `get_plots()`. Assert the result contains 4 response traces (or 4 subplots), not 1.
- **Fix:** Generate a subplot grid with `p * m` panels, each showing step/impulse response for G_ij. Match the layout used by MIMO Design Studio's response grid.
- **Textbook reference:** Ogata Ch. 11.2 (MIMO step response interpretation); standard MATLAB `step(G)` for MIMO shows all I/O pairs.

**Phase:** Phase 2 (Visual/notation accuracy)

---

## Moderate Pitfalls

---

### PITFALL-06: No State-Space Conversion from Transfer Matrix

**What goes wrong:** The Block Diagram Builder computes a transfer function matrix G(s), but never converts it to state-space form (A, B, C, D). This means:
- No controllability/observability analysis is available.
- The System Hub exports `transfer_matrix` entries but cannot export state-space matrices.
- The MIMO Design Studio (which works in state-space) cannot receive systems from the BDB.

**Why it happens:** The BDB was designed for SISO TF computation. MIMO support added the matrix structure but stopped at the TF level.

**Consequences:**
- Students cannot bridge between the block diagram (TF domain) and modern control tools (state-space domain).
- The pedagogical flow Ogata builds in chapters 3-12 (TF -> SS -> design) is broken.

**Prevention:**
- **Implementation:** Use `scipy.signal.tf2ss()` per entry, then combine into a MIMO state-space realization. Or use the common-denominator approach (see PITFALL-02) to build a single realization.
  ```python
  from scipy.signal import tf2ss
  # For each G_ij, get (A_ij, B_ij, C_ij, D_ij)
  # Then combine using series/parallel connection rules
  ```
- **Test case:** For the 2x2 coupled preset (pure gains, no dynamics), verify that `D = [[2, 0.5], [0.3, 1.5]]` and `A, B, C` are empty/zero (static system).
- **Textbook reference:** Ogata Ch. 3.8 (TF matrix to SS); Ch. 11.3 (MIMO realizations). Also: `scipy.signal.StateSpace` documentation.

**Phase:** Phase 3 (Edge cases / System Hub integration)

---

### PITFALL-07: Delta Accumulation Uses Repeated Polynomial Division, Risks Numerical Drift

**What goes wrong:** The `compute_delta()` function accumulates the graph determinant by repeatedly multiplying and adding rational polynomials. Each step does `d_den = self._pmul(d_den, prod_den)`, growing the denominator polynomial with every non-touching loop combination. For diagrams with many loops, this produces very high-order polynomials where small coefficients may accumulate rounding errors.

The `_clean_poly()` method strips trailing near-zero coefficients (threshold 1e-10), but this only addresses trailing zeros, not interior coefficient drift.

**Why it happens:** Polynomial arithmetic in floating-point is inherently ill-conditioned. Each convolution (`np.convolve`) amplifies rounding errors, especially for polynomials with roots near the unit circle or imaginary axis.

**Consequences:**
- For systems with 5+ loops, the denominator polynomial may have coefficients that are off by 1e-6 or more, leading to shifted poles.
- Stability classification (stable/marginal/unstable) depends on pole locations, so numerical drift can flip a marginally stable system to stable or unstable.
- The 1e-6 epsilon in stability classification (line 1887) provides some buffer, but is arbitrary.

**Warning signs in code:** `d_den = self._pmul(d_den, prod_den)` inside a loop over combinations (line 1792). Polynomial degree grows combinatorially.

**Prevention:**
- **Test case:** Build a system with 4+ non-touching loops. Compare computed poles against MATLAB/scipy `signal.tf2zpk()` for the same system. Assert pole locations agree to within 1e-8.
- **Mitigation:** After final Delta computation, use `np.polynomial.polynomial.polyfromroots()` to reconstruct from roots, verifying coefficient stability. Or switch to root-based (ZPK) representation earlier.
- **Textbook reference:** Numerical methods texts (Higham, "Accuracy and Stability of Numerical Algorithms") -- polynomial rootfinding is ill-conditioned for degree > 10.

**Phase:** Phase 3 (Edge cases)

---

### PITFALL-08: Forward Path DFS Allows Revisiting the Target Node

**What goes wrong:** In `_dfs_forward_paths()` (line 1940-1954), the stopping condition is `if current == target and len(path) > 1`. The guard `next_block not in visited or next_block == target` (line 1948) means the target node can be revisited. This is correct for finding forward paths, BUT if the output block has outgoing connections (which it shouldn't, but the UI might allow), the DFS could find paths that pass through the output block mid-path and continue to other blocks before returning to it.

**Why it happens:** The DFS makes a special exception for the target node to allow path completion, but this exception also allows the target to appear mid-path.

**Consequences:**
- Spurious forward paths that include the output block as an intermediate node.
- These produce incorrect path gains (output blocks are treated as unity pass-through).

**Warning signs in code:** `next_block == target` exception in visited check (line 1948).

**Prevention:**
- **Test case:** Create an output block with an outgoing wire (illegal but constructable). Verify no forward paths pass through the output block before the final step.
- **Fix:** Add a check: if `next_block == target`, only allow it as the LAST step. Do not continue DFS from the target.
- **Textbook reference:** Nise Ch. 5 (signal flow graph: sink nodes have no outgoing branches).

**Phase:** Phase 1 (Math correctness audit)

---

### PITFALL-09: MIMO Index Conventions (1-indexed Labels vs 0-indexed Arrays)

**What goes wrong:** The preset builders use `"index": 1` for the first input and `"index": 2` for the second (1-indexed, matching textbook convention u_1, u_2). But the transfer matrix is built as a Python list-of-lists with 0-indexed access: `transfer_matrix[0][0]` is G_11. Meanwhile, `sorted(blocks, key=lambda b: b.get("index", 0))` means a block with no `"index"` key sorts BEFORE index 1, potentially misordering inputs.

**Why it happens:** Mixing mathematical notation (1-indexed subscripts) with Python data structures (0-indexed arrays).

**Consequences:**
- If a user adds input blocks without setting an index, they sort to position 0, displacing existing blocks.
- Transfer matrix entries may be assigned to the wrong I/O pairs.
- Display labels say u_1 but the array position says column 0 -- confusion when exporting to other tools.

**Warning signs in code:** `key=lambda b: b.get("index", 0)` (line 1487). Default index 0 conflicts with explicit index 1.

**Prevention:**
- **Test case:** Add two input blocks: one with `index=1`, one with no index. Call `_compute_transfer_function()`. Verify the ordering matches what the student sees in the UI.
- **Fix:** Either default to `index=float('inf')` (sort unindexed blocks last) or require all I/O blocks to have explicit indices. Validate uniqueness.
- **Textbook reference:** Ogata Ch. 11 uses 1-indexed throughout (u_1, ..., u_m; y_1, ..., y_p).

**Phase:** Phase 2 (Visual/notation accuracy)

---

### PITFALL-10: No Validation of MIMO Dimensional Consistency

**What goes wrong:** When a user constructs a MIMO block diagram, there is no validation that signal dimensions are consistent through the diagram. For example, if u_1 connects to a 2x1 MIMO subsystem block, the output is a 2-vector, but the next block (say, an adder) expects a scalar. The system silently treats everything as SISO scalars.

**Why it happens:** All blocks produce scalar transfer functions. There is no concept of vector-valued signals or matrix-valued block transfer functions in the block diagram builder.

**Consequences:**
- Students build diagrams that look like MIMO systems but are actually collections of independent SISO paths.
- The transfer matrix is correct for the open-loop "superposition of SISO paths" interpretation, but this is NOT the same as a true MIMO system with internal state coupling.
- A student who builds a state-feedback block diagram (plant + K matrix + adder) gets wrong results because K is a matrix, not a scalar.

**Warning signs in code:** `block_tf()` (line 1625) always returns scalar `(num, den)` polynomials, never matrix-valued.

**Prevention:**
- **Test case:** Build a state-feedback diagram with a 2x2 plant and a 2x2 K gain. Verify the closed-loop transfer matrix matches `(sI - A + BK)^{-1} B` computed symbolically. (This test will FAIL with current code, documenting the limitation.)
- **Short-term fix:** Add a warning in the UI when blocks that should be matrix-valued (custom_tf with MIMO dimensions) are used in a scalar context.
- **Long-term fix:** Extend block_tf to return matrix-valued transfer functions. This is a major architectural change.
- **Textbook reference:** Ogata Ch. 11.4 (MIMO block diagram algebra requires matrix operations); Nise Ch. 12 (state-space design with matrix gains).

**Phase:** Phase 3 (Edge cases) -- document as a known limitation for now, full fix is a separate milestone.

---

## Minor Pitfalls

---

### PITFALL-11: Algebraic Loop Detection Misses Custom TF Blocks with Unity Denominator

**What goes wrong:** The algebraic loop detector (line 1672-1682) checks for "memory" elements (delay, integrator, or custom_tf with `len(den_coeffs) > 1`). A custom_tf block with `den_coeffs=[1.0]` (constant denominator) and `num_coeffs=[5.0]` (pure gain) is NOT flagged as having memory, correctly. But a custom_tf with `den_coeffs=[1.0, 0.0]` (which looks like it has memory because `len > 1` but the higher-order coefficient is zero) is flagged as having memory, incorrectly.

**Prevention:**
- **Test case:** Create a feedback loop with a custom_tf block having `den_coeffs=[1.0, 0.0]`. Verify it IS detected as an algebraic loop (the zero coefficient means no actual dynamics).
- **Fix:** Strip trailing zeros from `den_coeffs` before checking length, or check if `np.roots(den_coeffs)` has any roots (actual dynamics).
- **Textbook reference:** Oppenheim Ch. 5 (proper vs improper systems).

**Phase:** Phase 3 (Edge cases)

---

### PITFALL-12: Loop Normalization May Miss Reversed Loops

**What goes wrong:** Loop deduplication in `_dfs_loops()` normalizes by rotating to the smallest block ID. But a loop `[A, B, C]` and the reverse traversal `[A, C, B]` are DIFFERENT loops with potentially different gains (if directed edges have different gains in each direction). In the current directed-graph implementation this is correct -- reversed traversal would follow different edges. However, if a loop CAN be traversed in both directions (bidirectional connections), both traversals should be found and counted as separate loops.

**Prevention:**
- **Test case:** Verify that loops are directed: `[A -> B -> C -> A]` and `[A -> C -> B -> A]` produce different loop gains if the edge gains differ.
- **Note:** Current implementation only follows outgoing edges, so reverse traversal is impossible unless there are bidirectional connections. This is correct for signal flow graphs (directed edges only).

**Phase:** Phase 1 (verify correctness, likely already correct)

---

### PITFALL-13: Hub Export Missing MIMO State-Space Format

**What goes wrong:** `to_hub_data()` (line 3292) exports MIMO systems as `transfer_matrix.entries` but the System Hub validator (`hub_validator.py`) and the MIMO Design Studio expect state-space format `(A, B, C, D)`. There is no conversion bridge, so MIMO systems computed in the BDB cannot flow to the MIMO Design Studio via the Hub.

**Prevention:**
- **Test case:** Export a MIMO BDB system to Hub. Import into MIMO Design Studio. Assert matrices are received correctly.
- **Fix:** Add TF-to-SS conversion in `to_hub_data()` when MIMO flag is set. Include both TF matrix and SS representation.
- **Textbook reference:** Ogata Ch. 3.8 (converting between representations).

**Phase:** Phase 3 (System Hub integration)

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Phase 1: Math audit | PITFALL-02 (shared Delta) | Compute Delta once, share across all I/O pairs |
| Phase 1: Math audit | PITFALL-01 (zero-gating mutation) | Filter adjacency instead of mutating blocks |
| Phase 1: Math audit | PITFALL-04 (coefficient convention) | Add regression tests for every conversion path |
| Phase 1: Math audit | PITFALL-03 (adder sign) | Build explicit +/- feedback test cases from Nise Ch. 5 |
| Phase 1: Math audit | PITFALL-08 (DFS target revisit) | Guard target node to only appear as final path step |
| Phase 2: Visual/notation | PITFALL-05 (only G_11 plotted) | Generate full p x m response grid |
| Phase 2: Visual/notation | PITFALL-09 (index convention) | Standardize on 1-indexed with validation |
| Phase 3: Edge cases | PITFALL-10 (no dimensional consistency) | Document limitation, add UI warning |
| Phase 3: Edge cases | PITFALL-07 (numerical drift) | Compare against scipy.signal for verification |
| Phase 3: Edge cases | PITFALL-06 (no SS conversion) | Implement TF-to-SS bridge |
| Phase 3: Edge cases | PITFALL-11 (algebraic loop false negative) | Strip trailing zeros before memory check |
| Phase 3: Hub integration | PITFALL-13 (Hub export format) | Add SS representation to hub data |

---

## Notation Mistakes That Confuse Students

These are not code bugs but pedagogical errors that teach wrong concepts.

### NOTATION-01: G(s) vs H(s) vs L(s) Ambiguity

**What goes wrong:** The BDB labels computed transfer functions as `H(R)` or `H(A)` generically. In standard textbook notation (Nise, Ogata), `G(s)` is the forward-path plant, `H(s)` is the feedback-path sensor, and `L(s) = G(s)H(s)` is the loop transfer function. Using `H` for the overall closed-loop transfer function `T(s) = G/(1+GH)` contradicts textbook convention.

**Prevention:** Label as `T(s)` or `T(z)` for the closed-loop transfer function. Use `G(s)` for open-loop forward path only.

### NOTATION-02: Transfer Matrix Should Show G(s) Not Individual Entries

**What goes wrong:** The transfer matrix is displayed as individual rational expressions per entry. Students should also see the matrix form:
```
G(s) = [ G_11(s)  G_12(s) ]
       [ G_21(s)  G_22(s) ]
```
with a SINGLE expression for the characteristic polynomial det(sI - A) or equivalently the common denominator.

**Prevention:** Add a matrix display mode in the MIMO viewer showing the full G(s) matrix with KaTeX rendering.

### NOTATION-03: Subscript Ordering (Row-Column vs Input-Output)

**What goes wrong:** G_ij means "output i, input j" (row i, column j of the transfer matrix). The code correctly uses `transfer_matrix[output_idx][input_idx]`, but the display labels might confuse this if `input_labels` and `output_labels` are not clearly associated with columns and rows respectively.

**Prevention:** Display header: "G_ij: output y_i due to input u_j". Match Ogata notation exactly.

---

## Sources

- [Mason's gain formula - Wikipedia](https://en.wikipedia.org/wiki/Mason's_gain_formula) -- Delta is a property of the graph, not per-path
- [MIMO Transfer Functions - Duke University](https://people.duke.edu/~hpgavin/MultivariableControl/MIMOtf.pdf) -- Transfer matrix conventions
- [Multivariable Robust Control - Lehigh](https://www.lehigh.edu/~eus204/teaching/ME450_MRC/lectures/lecture04.pdf) -- (I+GH)^-1 vs (I+HG)^-1 distinction
- [ETH Zurich CS2 Lecture 6 - MIMO Intro](https://ethz.ch/content/dam/ethz/special-interest/mavt/dynamic-systems-n-control/idsc-dam/Lectures/Control-Systems-2/lecture_slides/2019-03-29-ETHZ-CS2-6-mimo-intro.pdf) -- Matrix commutativity in feedback
- [Minimal State-Space Realization - MIT OCW](https://ocw.mit.edu/courses/6-241j-dynamic-systems-and-control-spring-2011/760782bd5ceefacb37bf8719dc23dfcb_MIT6_241JS11_chap25.pdf) -- MIMO realization theory
- [Matrix Approach for Signal Flow Graphs - MDPI](https://www.mdpi.com/2078-2489/11/12/562) -- Alternative to Mason's for MIMO
- Ogata, *Modern Control Engineering*, 5th ed. -- Ch. 3 (TF/SS), Ch. 11 (MIMO design)
- Nise, *Control Systems Engineering*, 8th ed. -- Ch. 5 (Mason's rule, block diagram reduction)
- Oppenheim & Willsky, *Signals and Systems*, 2nd ed. -- Ch. 10 (z-transform), Ch. 5 (system properties)
