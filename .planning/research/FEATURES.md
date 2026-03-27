# Feature Landscape: MIMO Block Diagram Builder Validation & Educational Content

**Domain:** Interactive MIMO control systems education tool (block diagram builder)
**Researched:** 2026-03-27
**Reference texts:** Ogata (Modern Control Engineering, 5e), Nise (Control Systems Engineering, 7e), Oppenheim (Signals & Systems)

---

## Table Stakes

Features users (students, instructors) expect from a tool claiming textbook-accurate MIMO block diagram analysis. Missing any of these means the tool cannot be cited in educational or publication contexts.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Correct superposition-based transfer matrix computation** | Ogata Ch.3: MIMO TF matrix G(s) is computed by setting all inputs except u_j to zero and computing each G_ij(s). This IS what the current `_solve_for_pair` does via signal isolation. Must be validated against textbook examples. | Med | Already implemented but unvalidated. The zero-gating approach (temporarily converting other input blocks to gain=0) is conceptually correct but needs edge-case testing (feedback loops across I/O pairs, algebraic loops). |
| **Transfer matrix display with correct dimensions** | Y(s) = G(s)U(s) where G is p x m. Every textbook shows G(s) as a matrix with row=output, col=input. Must show dimensions badge, row/column headers with u_i/y_j labels. | Low | Already implemented in frontend (`MIMOTransferMatrix` component). Validate notation matches Ogata convention: rows are outputs, columns are inputs. |
| **Non-commutativity awareness in cascade blocks** | MIMO cascade: Y = G2 * G1 * U (right-to-left). Students commonly mistake this as G1 * G2. Tool must compute in correct order or display a warning. Matrix multiplication order matters. | Med | Current Mason's gain per-pair approach sidesteps this by computing scalar paths, but any future matrix-level operations (e.g., state-space conversion of the whole diagram) must respect this. |
| **MIMO feedback loop formula: Y = (I + GH)^{-1} G R** | Textbook MIMO feedback: closed-loop TF is (I + G(s)H(s))^{-1} G(s) for negative feedback. This is the matrix generalization of G/(1+GH). Tool must handle MIMO feedback loops correctly. | High | Current per-pair Mason's approach may handle simple MIMO feedback, but complex cross-coupled feedback (u1 feeds back to y2's error) needs validation. This is the hardest validation target. |
| **Signal dimension annotations on wires** | Textbook convention (Ogata, Nise): MIMO block diagrams show signal dimension on wires. A wire carrying a 2-vector should show "/2" or a double-line. Tells students what dimension signals have at each point. | Med | NOT currently implemented. Critical for educational value -- without dimension annotations, students cannot verify their understanding of signal flow dimensions. |
| **Mason's Gain Formula correctness for MIMO** | Mason's formula applies per (input, output) pair via superposition. Each pair computation must find all forward paths, all loops, non-touching loop combinations, and compute cofactors correctly. | High | Already implemented for SISO. MIMO extends via superposition (zero other inputs). Must validate: (1) forward paths don't traverse zeroed-out inputs, (2) loop detection handles cross-coupled paths, (3) cofactor delta computation handles MIMO topologies. |
| **MIMO SFG (Signal Flow Graph) representation** | Oppenheim/Nise: SFGs are the canonical companion to block diagrams. For MIMO, the SFG should show all nodes and branches with correct gain labels. Toggle between block diagram and SFG views. | Med | SISO SFG toggle exists. MIMO SFG needs validation: are cross-coupling branches shown correctly? Are multi-input/multi-output nodes rendered with proper fan-in/fan-out? |
| **Stability assessment per entry and overall** | Each G_ij(s) has its own poles; the system's overall stability depends on the poles of the full system (which are the poles of det(denominator matrix), not just the union of individual entry poles). | High | Current implementation checks stability per-entry and ORs them. This is correct for open-loop transfer matrix entries but NOT correct for closed-loop MIMO systems where pole-zero cancellation can occur. Flag for deeper research. |
| **Textbook-matched presets with known answers** | Students need worked examples they can verify against their textbook. Presets must have analytically known transfer matrices so students can check the tool's output. | Med | Three MIMO presets exist (2x2 coupled, MISO, SIMO). All use simple gain blocks, no feedback. Need: (1) presets with MIMO feedback, (2) presets matching specific Ogata/Nise examples, (3) documented expected answers. |
| **Correct I/O labeling convention** | Ogata: inputs u_1...u_m, outputs y_1...y_p. Unicode subscripts. Consistent across diagram, matrix display, and SFG. | Low | Already implemented with Unicode subscripts. Verify consistency across all views. |
| **Step/impulse response for MIMO (response grid)** | For a p x m system, show a p x m grid of step responses (one per I/O pair). This is how MATLAB `step(sys)` displays MIMO responses and how Ogata presents them. | Med | Currently only shows G_11 response. A p x m response grid is table stakes for any MIMO tool. The MIMO Design Studio already has this pattern -- reuse it. |
| **State-space conversion G(s) -> (A,B,C,D)** | Ogata Ch.3: every MIMO transfer matrix has a state-space realization. Tool should offer conversion to SS form, or at minimum show it's possible via the System Hub. | High | Hub export exists but only exports per-entry TFs. A proper minimal realization of the full MIMO system requires controllable canonical form or balanced realization. Defer to Hub integration with MIMO Design Studio. |
| **Algebraic loop detection** | When a feedback path has no dynamics (direct feedthrough with D != 0), it creates an algebraic loop. Tool must detect this and either warn or handle it (implicit equation solve). | Med | Not currently implemented. Algebraic loops cause Mason's formula to produce incorrect results silently. Must detect and warn at minimum. |

## Differentiators

Features that go beyond what MATLAB/Simulink or standard textbook tools offer. These make the tool uniquely valuable for education.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Step-by-step Mason's derivation overlay** | Show students HOW the transfer function was computed: forward paths highlighted, loops identified, cofactors computed step by step. No textbook tool does this interactively. | High | The static computation exists. Adding an animated/step-by-step visualization would be a flagship educational feature. Show: (1) enumerate forward paths with path gain, (2) enumerate loops with loop gain, (3) show non-touching loop groups, (4) compute Delta and cofactors, (5) final result. |
| **Click-to-trace signal path** | Click any wire to see where the signal came from and where it goes. Highlight the complete signal path from input to that point. For MIMO, color-code by source input. | Med | Would make debugging student-built diagrams much faster. Also useful for understanding superposition visually. |
| **Cross-coupling visualization** | For MIMO diagrams, visually distinguish direct paths (u_i -> y_i) from cross-coupling paths (u_i -> y_j, i != j). Use color or line style. Teaches students to see coupling structure at a glance. | Low | Simple visual enhancement with high educational value. Color direct paths one way, cross-coupling another. |
| **Interactive superposition demonstration** | Toggle individual inputs on/off to show how the total output is the sum of individual contributions. Animates the superposition principle. | Med | Unique to a web tool -- textbooks can only show this statically. Toggle u_1 on/u_2 off, see Y = G(:,1)*u_1. Toggle both on, see full Y. |
| **Transfer matrix to/from state-space live conversion** | Show the equivalence G(s) = C(sI-A)^{-1}B + D in real time as the student modifies the block diagram. | High | Bridges the gap between transfer function and state-space representations, which is a core learning objective in Ogata Ch.3-4. |
| **Decoupling analysis** | For a MIMO system, show the RGA (Relative Gain Array) to indicate interaction/coupling between loops. Helps students understand when MIMO controllers are needed vs. decentralized SISO. | High | Graduate-level feature. RGA = G .* (G^{-1})^T for square systems. Would be unique among educational tools. Defer unless targeting graduate courses. |
| **Theory panel with KaTeX derivations** | Inline educational content: expandable panels showing the theory behind MIMO block diagram algebra, with rendered equations. Context-sensitive -- shows relevant theory for the current diagram topology. | Med | Platform already has KaTeX infrastructure. Theory panels exist in other simulations (Controller Tuning Lab, Steady-State Error). Pattern is established. |
| **MIMO-specific educational presets** | Presets designed to teach specific concepts: (1) cross-coupling, (2) MIMO feedback, (3) diagonal/triangular systems, (4) systems with RHP zeros. Each with guided explanations. | Med | More valuable than generic presets. Each preset should teach one concept and have a "what to observe" guide. |
| **Validation mode: student-entered expected answer** | Student enters what they think G(s) should be, tool compares with computed result, highlights where they went wrong. | Med | Turns the tool from a calculator into an exam prep tool. Unique differentiator for education. |
| **Export to MIMO Design Studio** | Push the computed transfer matrix to MIMO Design Studio for controller design. Completes the "model -> design -> validate" workflow. | Med | Hub infrastructure exists. Need to ensure MIMO transfer matrix format is compatible with MIMO Design Studio's import. Currently only SISO Hub export is well-tested. |

## Anti-Features

Things to explicitly NOT build because they would confuse students, deviate from textbook conventions, or add complexity without educational value.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Matrix-valued wires (bus signals)** | Simulink allows bus signals where a single wire carries a vector. This is an implementation convenience, NOT a textbook convention. Textbooks show individual scalar signals, each with its own wire. Students should see every signal path explicitly. | Keep individual scalar wires. Show dimension annotations as labels, not as wire thickness/multiplicity changes. |
| **Automatic block diagram simplification/reduction** | Block diagram reduction is a core skill students must learn. Automating it removes the learning. | Show the computed TF as the result, but preserve the student's diagram topology exactly as they built it. Never auto-simplify. |
| **Symbolic matrix algebra engine** | Computing (I + GH)^{-1}G symbolically for arbitrary rational matrices is a compiler-level problem. Not worth the complexity for education. | Use numerical Mason's per-pair (current approach) which is correct by superposition. Show the formula symbolically in theory panels but compute numerically. |
| **Non-linear blocks in MIMO diagrams** | Saturation, dead-zone, hysteresis blocks would be physically meaningful but break all LTI analysis (Mason's, TF computation, stability). | Keep MIMO diagrams purely LTI. Nonlinear analysis belongs in Nonlinear Control Lab (which already exists). |
| **Arbitrary signal routing (no port constraints)** | Simulink allows connecting any output to any input. For educational clarity, enforce port semantics: inputs on left, outputs on right. | Maintain current port structure. Students should think about signal flow direction, not fight the tool. |
| **MIMO with mixed CT/DT blocks** | Mixing continuous and discrete time in one diagram requires sample-and-hold blocks and is a hybrid systems topic beyond introductory MIMO. | Enforce single system_type per diagram (already done). Mixed CT/DT is a separate advanced topic. |
| **More than 4 inputs or 4 outputs** | Educational MIMO examples rarely exceed 3x3. Supporting 8x8 adds complexity to layout, matrix display, and response grids without educational benefit. | Keep current max_inputs=4, max_outputs=4 limit. Sufficient for all textbook examples. |
| **Drag-to-rearrange transfer matrix rows/columns** | Permuting rows/columns of G(s) changes the I/O pairing. Students should understand that G_ij means "input j to output i" and reordering changes meaning. | Matrix display order matches block index order. No rearrangement. Relabeling inputs/outputs changes the pairing explicitly. |

## Feature Dependencies

```
Signal dimension annotations -> Correct MIMO wire rendering (prerequisite: know how many signals each wire carries)

Step-by-step Mason's overlay -> Mason's Gain correctness validation (validate first, then visualize)

MIMO response grid -> Per-pair TF computation correctness (must have correct G_ij to plot responses)

Export to MIMO Design Studio -> Hub MIMO format validation (must agree on transfer matrix serialization)

Interactive superposition demo -> Correct superposition/signal isolation (current zero-gating approach must be validated)

Algebraic loop detection -> Mason's Gain correctness (algebraic loops break Mason's; detect before computing)

Theory panels -> Presets with known answers (theory content references specific examples)

MIMO SFG correctness -> SISO SFG correctness (MIMO SFG extends SISO SFG; fix SISO bugs first)

State-space conversion -> Transfer matrix correctness (can't convert to SS if TF matrix is wrong)
```

## MVP Recommendation

**Priority order based on project constraint "math correctness first":**

### Phase 1: Validate and Fix Math (must-have)
1. **Mason's Gain correctness for MIMO** -- validate with textbook examples, fix any bugs found
2. **MIMO feedback loop correctness** -- test cross-coupled feedback topologies
3. **Algebraic loop detection** -- detect and warn, prevents silent wrong answers
4. **Stability assessment correctness** -- per-entry vs system-level distinction

### Phase 2: Visual/Notation Accuracy (table stakes)
5. **Signal dimension annotations on wires** -- educational requirement
6. **Transfer matrix display validation** -- verify row/column convention matches textbooks
7. **MIMO SFG correctness** -- validate cross-coupling rendering
8. **MIMO response grid** -- p x m grid instead of just G_11

### Phase 3: Textbook Presets and Validation Tests
9. **Textbook-matched presets with known answers** -- add Ogata/Nise examples
10. **Validation test suite** -- automated tests comparing against hand-computed results

### Phase 4: Educational Content
11. **Theory panels with KaTeX derivations** -- MIMO-specific content
12. **Step-by-step Mason's overlay** -- flagship educational differentiator
13. **Interactive superposition demo** -- unique to web tools

**Defer:** Decoupling analysis (RGA), full state-space conversion, validation mode (student answer comparison). These are valuable but not critical for the hardening milestone.

## Sources

- [MIMO Transfer Function Matrix - Duke University](https://people.duke.edu/~hpgavin/MultivariableControl/MIMOtf.pdf) -- MIMO TF matrix conventions and computation
- [MIMO Transfer Functions Lecture - UW Madison ECE 332](https://www.12000.org/my_courses/univ_wisconsin_madison/fall_2015/ECE_332_feedback/inse7.htm) -- Superposition principle for MIMO, signal isolation
- [Block Diagram Algebra Reduction Rules - TheLinuxCode](https://thelinuxcode.com/block-diagram-algebra-reduction-rules-for-control-systems-with-worked-examples/) -- SISO/MIMO reduction rule reference
- [MATLAB MIMO Control System](https://www.mathworks.com/help/control/ug/build-a-model-of-a-multi-input-multi-output-mimo-control-system.html) -- MATLAB's MIMO block diagram approach
- [MATLAB MIMO Feedback Loop](https://www.mathworks.com/help/control/ug/build-a-model-of-a-multi-input-multi-output-mimo-feedback-loop.html) -- MATLAB's MIMO feedback conventions
- [MATLAB MIMO Models](https://www.mathworks.com/help/control/getstart/mimo-models.html) -- MATLAB's MIMO model representation
- [Mason's Gain Formula - Wikipedia](https://en.wikipedia.org/wiki/Mason%27s_gain_formula) -- Mason's formula reference
- [Multivariable Robust Control Lecture - Lehigh](https://www.lehigh.edu/~eus204/teaching/ME450_MRC/lectures/lecture04.pdf) -- MIMO block diagram matrix algebra, (I-L)^{-1} convention
- [Control Systems Academy - Web Simulator](https://controlsystemsacademy.com/sim_examples.html) -- Competitor: web-based control systems simulator
- [Block Diagram Algebra - GeeksforGeeks](https://www.geeksforgeeks.org/block-diagram-algebra/) -- Educational reference for block diagram rules
