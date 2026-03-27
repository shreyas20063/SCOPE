# SCOPE — MIMO Block Diagram Builder Hardening

## What This Is

SCOPE is an interactive web platform for learning signals and systems through simulations. This milestone focuses on hardening the MIMO functionality in the Block Diagram Builder — auditing every line of vibe-coded implementation, fixing math and rendering errors, building validation tests from scratch, and adding educational content (theory sections, derivations) that maps directly to textbook conventions.

## Core Value

**Every MIMO computation must be mathematically correct and match textbook definitions from Ogata, Nise, and Oppenheim.** If the math is wrong, nothing else matters — students will learn incorrect concepts.

## Requirements

### Validated

- ✓ Block Diagram Builder core functionality — existing
- ✓ Single-input single-output (SISO) block diagram algebra — existing
- ✓ Mason's Gain Formula for SISO systems — existing
- ✓ Signal Flow Graph toggle view — existing
- ✓ Custom TF blocks with KaTeX rendering — existing
- ✓ Wire routing with A* pathfinding — existing
- ✓ JSON export for Signal Flow Scope import — existing
- ✓ 20+ simulations across Signal Processing, Circuits, Control Systems, Transforms, Optics — existing
- ✓ MIMO Design Studio (standalone state-space tool) — existing
- ✓ System Hub for cross-simulation data transfer — existing

### Active

- [ ] MIMO block diagram computation correctness (transfer matrix, state-space conversion)
- [ ] MIMO visual/notation accuracy (port labels, signal dimensions, matrix annotations)
- [ ] MIMO edge case handling (feedback loops, algebraic loops, singular systems, improper TFs)
- [ ] Validation test suite for MIMO BDB (built from scratch, math-first)
- [ ] Educational content: theory sections with textbook-accurate derivations
- [ ] Educational mapping: what each interaction teaches, aligned to Ogata/Nise/Oppenheim

### Out of Scope

- New simulation types — this milestone is about hardening existing MIMO, not adding new sims
- MIMO Design Studio changes — focus is Block Diagram Builder specifically
- Mobile optimization — correctness before responsiveness
- Performance optimization — correctness before speed

## Context

- **Current state**: MIMO support in BDB was vibe-coded — implementation exists but has not been tested or validated
- **Validation infrastructure**: No test suite exists yet; `validation/` directory needs to be built from scratch
- **Reference texts**: Ogata (Modern Control Engineering) for state-space/MIMO, Nise (Control Systems Engineering) for block diagram algebra/Mason's, Oppenheim (Signals & Systems) for signal flow graphs/LTI
- **Priority order**: Math correctness first, then visual/notation, then edge cases, then educational content
- **Existing bug tracking**: `.claude/bugs.md` has documented bugs (BDB-related: BUG-001 through BUG-007)
- **CDC paper**: Platform is associated with a research paper — educational accuracy is publication-grade requirement

## Constraints

- **Tech stack**: Python 3.11/FastAPI backend, React 18/Vite frontend — no changes to stack
- **Textbook fidelity**: All notation, conventions, and derivations must match Ogata/Nise/Oppenheim — no invented conventions
- **Math first**: Every fix starts with verifying the math before touching UI code
- **Existing architecture**: Must work within BaseSimulator pattern and existing viewer chain in SimulationViewer.jsx

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Math-first priority order | Wrong math teaches wrong concepts — visual bugs are cosmetic, math bugs are pedagogical | — Pending |
| Build validation from scratch | No existing test infrastructure; need purpose-built tests that verify against textbook examples | — Pending |
| Three textbook references | Ogata for MIMO/SS, Nise for block diagrams, Oppenheim for SFG — covers all aspects | — Pending |
| Full package deliverable | Audit + fix + tests + educational content — publication-grade quality required | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-27 after initialization*
