# Quick Reference: 40 Simulations by Tier & Topic
**Generated:** February 28, 2026

---

## TIER 1: MUST BUILD (12 Simulations, ~195 hours, 8 custom viewers)

### Fundamentals (1 sim)
- **1. Leaky Tank Water Dynamics** (Lec 1) — Physical first-order intuition, animated water filling, time constant τ

### Systems & Operators (3 sims)
- **2. Block Diagram Execution Animator** (Lec 2-4) — Step-by-step signal flow, impulse response building
- **3. Pole Location → Mode Shape Explorer** (Lec 3-4) — Draggable poles, live mode curves (CRITICAL)
- **4. CT Integrator vs. DT Delay Comparison** (Lec 4) — Isomorphism revealed, side-by-side domains

### Frequency & Control (5 sims)
- **5. Partial Fraction Decomposition Builder** (Lec 3, 5) — Symbolic + colored mode stacking
- **6. Interactive ROC Explorer** (Lec 6) — Convergence region intuition
- **9. High-Q Resonant System Explorer** (Lec 11) — Q-factor and resonance sharpness
- **10. Feedback Control System Parameter Sweep** (Lec 12-13) — Real-time PID design
- **11. Spectral Replication Visualizer** (Lec 21) — Why sampling creates spectral copies (aliasing)

### Transforms & Signals (3 sims)
- **8. Convolution Flip-and-Shift Animator** (Lec 8) — Step-by-step convolution mechanics
- **12. Fourier Series Harmonic Builder** (Lec 14-15) — Harmonic buildup + synthesis
- **18. Fourier Transform Pair Navigator** (Lec 16, 19) — Time-frequency duality, uncertainty principle

---

## TIER 2: SHOULD BUILD (15 Simulations, ~210 hours, 6 custom viewers)

### Advanced Transforms (4 sims)
- **7. Euler Method Mapping Visualization** (Lec 7) — Discretization choices (Forward/Backward/Tustin)
- **15. Vector Diagram Frequency Response Tracer** (Lec 9) — Bode plot construction via poles
- **16. Bode Plot Constructor** (Lec 10) — Magnitude & phase assembly
- **26. Spectral Windowing and Leakage Explorer** (Lec 17-18) — Window function effects

### Feedback & Control (5 sims)
- **13. Motor Controller Design Studio** (Lec 12) — Realistic PID tuning
- **14. Discrete-Time Feedback Pole Response** (Lec 11) — DT frequency response geometry
- **17. Feedback Pole Migration with Gain Control** (Lec 10) — Root locus concept
- **25. AM Radio Receiver Block Diagram** (Lec 23-24) — Demodulation visualization
- **27. System Identification via Frequency Response Fitting** (Lec 10) — Glider data example

### Sampling & Filtering (3 sims)
- **19. DT Frequency Response Unit Circle Explorer** (Lec 16-18) — Unit circle parametrization
- **20. Time-Frequency Duality Interactive Mapper** (Lec 16) — Scaling and shifting symmetry
- **21. Phase-Magnitude Separation in Filtering** (Lec 16-17) — Linear phase independence
- **22. Anti-Aliasing Filter Designer** (Lec 21-22) — Interactive LPF cutoff optimization
- **23. Quantization Artifact Explorer** (Lec 22) — Rounding error visualization

### Modulation (1 sim)
- **24. Modulation Scheme Comparator** (Lec 23-24) — AM vs. FM vs. PM comparison

---

## TIER 3: NICE TO HAVE (13 Simulations, ~195 hours, 5 custom viewers)

### Transforms & Properties (5 sims)
- **28. Laplace Transform Property Explorer** (Lec 6) — Shifting, scaling, differentiation
- **30. Fourier Series to Transform Transition** (Lec 14-19) — Bridge from periodic to aperiodic
- **31. CT/DT Fourier Transform Frequency Mapping** (Lec 19) — Duality and sampling theorem
- **32. Interactive Diffraction Grating Fourier Transform** (Lec 20) — Optics connection
- **37. Gibbs Phenomenon Visualizer** — Harmonic overshoot at discontinuities

### Sampling & Reconstruction (3 sims)
- **29. Convolution via 2D Visualization** (Lec 8) — Image blur as convolution metaphor
- **33. Discrete-Time Sampling Sequence Reconstructor** (Lec 22) — ZOH vs. sinc reconstruction
- **34. Sampling Rate Conversion Visualizer** (Lec 22) — Interpolation and decimation
- **36. CD Audio Pipeline** (Lec 25) — End-to-end audio processing chain (capstone)

### System Representations (2 sims)
- **35. Phase-Locked Loop Frequency Tracker** (Lec 24) — Feedback frequency locking
- **38. Cascade vs. Parallel Realization Comparison** (Lec 3, 5) — System structure equivalence
- **39. State-Space to Transfer Function Converter** (Lec 13) — A, B, C, D matrix visualization

### Advanced Control (1 sim)
- **40. Nyquist Stability Criterion Explorer** (Lec 13) — Encirclement and stability

---

## Master Index: All 40 by Lecture

| Lec | Simulation | Tier | Category | Complexity |
|---|---|---|---|---|
| 1 | Leaky Tank | T1 | Fund. | Low |
| 2-4 | Block Diagram Animator | T1 | Operators | Medium |
| 3-4 | Pole Mode Explorer | T1 | Systems | Medium |
| 3-4 | CT vs DT Comparison | T1 | Systems | Medium |
| 3, 5 | Partial Fractions | T1 | Transforms | High |
| 6 | ROC Explorer | T1 | Laplace | Medium |
| 6 | Laplace Property Explorer | T3 | Laplace | Low-Med |
| 7 | Euler Mapping | T2 | Transforms | Medium |
| 8 | Convolution Animator | T1 | Convolution | Medium |
| 8 | Convolution 2D Visualization | T3 | Convolution | High |
| 9 | Vector Diagram Tracer | T2 | Frequency | Medium |
| 10 | Feedback Pole Migration | T2 | Control | Medium |
| 10 | Bode Constructor | T2 | Frequency | Medium |
| 10 | System Identification | T2 | Frequency | Medium |
| 11 | High-Q Resonant | T1 | Control | Medium |
| 11 | DT Feedback Pole | T2 | DT Systems | Medium |
| 12 | Motor Controller | T2 | Control | Medium |
| 12-13 | Feedback Control | T1 | Control | Medium |
| 13 | State-Space to TF | T3 | Systems | Medium |
| 13 | Nyquist Stability | T3 | Control | High |
| 14-15 | Fourier Series Builder | T1 | Fourier | Medium |
| 14-19 | FS to Transform | T3 | Fourier | Medium |
| 16 | FT Pair Navigator | T1 | FT | Medium |
| 16-18 | DT Unit Circle Explorer | T2 | DT FT | Medium |
| 16 | Time-Freq Duality | T2 | FT Props | Medium |
| 16-17 | Phase-Magnitude Sep | T2 | FT Props | Medium |
| 17-18 | Spectral Windowing | T2 | FT Props | Medium |
| 19 | CT/DT FT Mapping | T3 | FT Props | Medium |
| 20 | Diffraction Grating FT | T3 | Optics | High |
| 21 | Spectral Replication | T1 | Sampling | Medium |
| 21-22 | Anti-Aliasing Filter | T2 | Sampling | Medium |
| 22 | Quantization Explorer | T2 | Sampling | Medium |
| 22 | Sampling Reconstructor | T3 | Sampling | Medium |
| 22 | Sampling Rate Conversion | T3 | Sampling | Medium |
| 23-24 | Modulation Comparator | T2 | Modulation | Medium |
| 23-24 | AM Radio Receiver | T2 | Modulation | Medium |
| 24 | Phase-Locked Loop | T3 | Modulation | High |
| 25 | CD Audio Pipeline | T3 | Applications | High |
| Any | Cascade vs Parallel | T3 | Systems | Medium |
| Any | Gibbs Phenomenon | T3 | Fourier | Low |

---

## Development Timeline Estimate

### Phase 1 (Tier 1): Months 1-3
**Goal:** 12 core pedagogical tools
- **Week 1-2:** Sims 1-3 (Leaky Tank, Block Diagram, Pole Mode)
- **Week 3-4:** Sims 4-6 (CT vs DT, Partial Fractions, ROC)
- **Week 5-6:** Sims 8-12 (Convolution, Fourier Series, FT Pair, Spectral Replication)
- **Week 7-8:** Sims 9-10 (High-Q, Feedback Control)
- **Testing & Polish:** Week 9-12

### Phase 2 (Tier 2): Months 4-5
**Goal:** 15 enrichment simulations
- **Week 13-20:** Deploy Tier 2 batch (3-4 per week)
- **Focus:** Motor Controller, Modulation, Filtering, Advanced Control

### Phase 3 (Tier 3): Months 6-7
**Goal:** 13 capstone/specialized
- **Week 21-28:** Deploy Tier 3 batch as resources permit
- **Capstone:** CD Audio Pipeline integration

---

## Custom Viewer Priority

### Tier 1 Custom Viewers (8 required)
1. Leaky Tank (animated SVG tank)
2. Block Diagram Animator (D3.js diagram + animation)
3. CT vs DT Comparison (animated curves)
4. Partial Fractions (symbolic + stacked area)
5. Fourier Series Builder (harmonic buildup animation)
6. Convolution Animator (flip-shift visualization)
7. Feedback Control (block diagram + metrics)
8. Motor Controller (profile-based UI)

### Tier 2 Custom Viewers (6)
- AM Radio Receiver (demodulation flow)
- Modulation Comparator (3-way overlay)
- Spectral Windowing (before/after window overlay)
- [3 others as needed]

### Tier 3 Custom Viewers (5)
- CD Audio Pipeline (end-to-end chain)
- Diffraction Grating (2D wave visualization)
- Phase-Locked Loop (feedback loop animation)
- [2 others as needed]

---

## Key Dependencies for Successful Implementation

### Backend Requirements
- NumPy, SciPy, Sympy (polynomial roots, symbolic algebra)
- scipy.signal (transfer functions, pole-zero analysis)
- numpy.fft (FFT for Fourier analysis)
- Custom ODE solver or scipy.integrate for CT simulations

### Frontend Requirements
- Plotly.js (mandatory for all 40 simulations)
- D3.js (block diagrams, custom visualizations)
- Three.js (3D visualizations if extended)
- MathJax/KaTeX (LaTeX rendering for equations)
- Canvas/SVG (custom animated graphics)

### Testing Coverage
- Unit tests for all simulator backend math
- Visual regression tests for plot rendering
- Interactive gameplay tests (drag/drop, slider ranges)
- Performance tests (real-time update responsiveness <200ms)

---

## Success Criteria

### Tier 1 Completion
✓ All 12 simulations deployed and tested
✓ Consistent UI/UX across all simulations
✓ Real-time interaction <150ms response time
✓ Comprehensive documentation for each simulator
✓ Student feedback loop integrated for refinement

### Full Catalog Completion (all 40)
✓ Every MIT 6.003 lecture topic has ≥1 corresponding simulation
✓ Visual design language unified across all viewers
✓ Learning path documented with recommended sequence
✓ Integration with existing textbook/course materials
✓ Scalability for future extensions (new simulators, topics)

---

## Quick Start for Development Team

1. **Read** CLAUDE.md for stack, conventions, design system
2. **Review** this document for tier structure and dependencies
3. **Read** VISUAL_master_simulation_catalog.md for detailed specs
4. **Start** with Tier 1, one simulator per week
5. **Test** each simulator against learning objectives from specs
6. **Iterate** on UI/UX based on pedagogical feedback

**Estimated effort:** 600 developer-hours, 20 weeks with 2-3 full-time developers.

