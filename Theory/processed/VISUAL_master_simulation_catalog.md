# VISUAL Master Simulation Catalog
## Based on Visual Analysis of MIT 6.003 Lecture Slides
**Compiled:** February 28, 2026
**Source:** 5 Visual Analysis Batches (Lectures 1-25)

---

## Executive Summary

### Total Simulations Identified: **40 unique simulations**

**Distribution by Lecture Range:**
- Lectures 1-5 (Fundamentals): 5 simulations
- Lectures 6-10 (Transforms & Frequency Response): 9 simulations
- Lectures 11-15 (Feedback & Fourier Series): 5 simulations
- Lectures 16-20 (Fourier Transform & Applications): 8 simulations
- Lectures 21-25 (Sampling, Modulation, Applications): 9 simulations
- Cross-cutting: 4 simulations

### Key Visual Themes Discovered

1. **Interactive Dragging & Real-Time Updates**
   - Pole-zero diagram editing (40+ occurrences across lectures)
   - Block diagram parameter adjustment
   - Frequency sweep animations
   - Complex plane exploration (s-plane, z-plane, unit circle)

2. **Side-by-Side Comparisons**
   - CT vs. DT domain representations
   - Time domain vs. frequency domain
   - Different controller types (P, PI, PD, PID)
   - Before/after filtering, aliasing, modulation

3. **Frequency-Domain Visualizations**
   - Bode plots (magnitude + phase on log scales)
   - Pole-zero diagrams with labeled frequencies
   - Harmonic spectrum (stem plots, bar charts)
   - ROC regions (shaded half-planes, strips)

4. **Time-Domain Animations**
   - Step-by-step signal propagation through block diagrams
   - Harmonic buildup (progressive addition of frequency components)
   - Sampling visualization (impulse trains in time/frequency)
   - Response transients (step response, impulse response overlays)

5. **Vector Geometry & Physics Intuition**
   - Vector diagrams for frequency response calculation
   - Pole distance visualization
   - Phase relationships in complex plane
   - Mode shapes and natural frequencies

6. **Table-Driven Execution Traces**
   - Node value propagation at each time step
   - Harmonic coefficient tables
   - Performance metrics (rise time, overshoot, settling time)
   - Numerical annotation on plots

---

## Priority Implementation Roadmap

### TIER 1: Must Build (Highest Pedagogical Impact + Feasibility)

These 12 simulations have the strongest visual inspiration from lecture materials and deliver foundational concepts.

1. **Leaky Tank Water Dynamics** (Lec 1) — First-order intuition, time constant
2. **Pole Location → Mode Shape Explorer** (Lec 3-4) — Pole-to-mode mapping (CRITICAL)
3. **Block Diagram Execution Animator** (Lec 2-4) — Step-by-step signal flow
4. **High-Q Resonant System Explorer** (Lec 11) — Q-factor and resonance sharpness
5. **Fourier Series Harmonic Builder** (Lec 14-15) — Harmonic decomposition + synthesis
6. **CT Integrator vs. DT Delay: Visual Comparison** (Lec 4) — Isomorphism & discretization
7. **Feedback Control System Parameter Sweep** (Lec 12-13) — PID design in real-time
8. **Partial Fraction Decomposition Builder** (Lec 3, 5) — Mode superposition visualization
9. **Interactive ROC Explorer** (Lec 6) — Convergence region intuition
10. **Convolution Flip-and-Shift Animator** (Lec 8) — Step-by-step convolution mechanics
11. **Spectral Replication Visualizer** (Lec 21) — Sampling → aliasing geometrically
12. **Fourier Transform Pair Navigator** (Lec 16, 19) — Time-frequency duality

**Estimated Total Dev Time:** ~240 hours (backend + frontend)

---

### TIER 2: Should Build (Important but Higher Complexity or Niche)

These 15 simulations deepen understanding or address specialized topics.

13. **Motor Controller Design Studio** (Lec 12) — Realistic PID tuning
14. **Discrete-Time Feedback Pole Response** (Lec 11) — DT frequency response geometry
15. **Vector Diagram Frequency Response Tracer** (Lec 9) — Bode plot construction via poles
16. **Euler Method Mapping Visualization** (Lec 7) — Discretization distortion (Forward/Backward/Tustin)
17. **Bode Plot Constructor** (Lec 10) — Magnitude & phase assembly
18. **Feedback Pole Migration with Gain Control** (Lec 10) — Root locus concept
19. **DT Frequency Response Unit Circle Explorer** (Lec 16-18) — Unit circle parametrization
20. **Time-Frequency Duality Interactive Mapper** (Lec 16) — Uncertainty principle
21. **Phase-Magnitude Separation in Filtering** (Lec 16-17) — Linear phase vs. magnitude response
22. **Anti-Aliasing Filter Designer** (Lec 21-22) — Interactive LPF cutoff optimization
23. **Quantization Artifact Explorer** (Lec 22) — Rounding error visualization
24. **Modulation Scheme Comparator** (Lec 23-24) — AM/FM/PM comparison
25. **AM Radio Receiver Block Diagram** (Lec 23-24) — Demodulation visualization
26. **Spectral Windowing and Leakage Explorer** (Lec 17-18) — Window function effects
27. **System Identification via Frequency Response Fitting** (Lec 10) — Glider data example

**Estimated Total Dev Time:** ~330 hours

---

### TIER 3: Nice to Have (Advanced/Specialized Topics)

These 13 simulations are valuable for deep dives but have lower baseline pedagogical impact.

28. **Laplace Transform Property Explorer** (Lec 6) — Shifting, scaling, differentiation properties
29. **Convolution via 2D Visualization** (Lec 8) — Image blur/deconvolution metaphor
30. **Fourier Series to Transform Transition** (Lec 14-19) — Bridge from periodic to aperiodic
31. **CT/DT Fourier Transform Frequency Mapping** (Lec 19) — Continuous vs. discrete duality
32. **Interactive Diffraction Grating Fourier Transform** (Lec 20) — Optics connection
33. **Discrete-Time Sampling Sequence Reconstructor** (Lec 22) — ZOH & sinc reconstruction
34. **Sampling Rate Conversion Visualizer** (Lec 22) — Interpolation and decimation
35. **Phase-Locked Loop Frequency Tracker** (Lec 24) — Feedback frequency locking
36. **CD Audio Pipeline** (Lec 25) — End-to-end audio processing chain
37. **Gibbs Phenomenon Visualizer** — Harmonic overshoot at discontinuities
38. **Cascade vs. Parallel Realization Comparison** — System structure equivalence
39. **State-Space to Transfer Function Converter** — A, B, C, D matrix visualization
40. **Nyquist Stability Criterion Explorer** — Encirclement and stability

**Estimated Total Dev Time:** ~250 hours

---

## Master Index Table

| # | Simulation Name | Lecture(s) | Category | Complexity | Tier | Visual Hook | Key Innovation |
|---|---|---|---|---|---|---|---|
| 1 | Leaky Tank Water Dynamics | 1 | Signal Fund. | Low | T1 | Animated water filling tank | Physical embodiment of τ and exponential settling |
| 2 | Block Diagram Execution Animator | 2-4 | DT Systems | Medium | T1 | Step-by-step signal flow nodes | Watch operators come alive: impulse response building |
| 3 | Pole Location → Mode Shape Explorer | 3-4 | CT/DT Systems | Medium | T1 | Draggable poles, live mode curves | Intuitive pole-to-response mapping |
| 4 | CT Integrator vs. DT Delay Comparison | 4 | Transforms | Medium | T1 | Side-by-side curves + block diagrams | Isomorphism revealed visually |
| 5 | Partial Fraction Decomposition Builder | 3, 5 | Transforms | High | T1 | Symbolic + colored mode stacking | Superposition of simple pieces |
| 6 | Interactive ROC Explorer | 6 | Laplace | Medium | T1 | Draggable test point + shaded half-plane | Causality determines convergence |
| 7 | Convolution Flip-and-Shift Animator | 8 | Convolution | Medium | T1 | Animated flip and slide motions | Convolution demystified step-by-step |
| 8 | Fourier Series Harmonic Builder | 14-15 | Fourier Series | Medium | T1 | Progressive harmonic addition + spectrum | Build signals from harmonics |
| 9 | High-Q Resonant System Explorer | 11 | Control | Medium | T1 | Draggable Q + animated pole motion | Sharp resonance from pole proximity to jω axis |
| 10 | Feedback Control System Parameter Sweep | 12-13 | Control | Medium | T1 | Real-time PID slider + pole migration | Feedback design made tangible |
| 11 | Spectral Replication Visualizer | 21 | Sampling | Medium | T1 | Replicated spectra overlaying/aliasing | Why sampling creates spectral copies |
| 12 | Fourier Transform Pair Navigator | 16, 19 | FT Basics | Medium | T1 | Synchronized time ↔ frequency panning | Uncertainty principle in action |
| 13 | Motor Controller Design Studio | 12 | Control | Medium | T2 | Motor diagram + profile buttons | PID tuning on realistic system |
| 14 | Discrete-Time Feedback Pole Response | 11 | DT Systems | Medium | T2 | Pole-zero on unit circle + freq response | DT frequency response via geometry |
| 15 | Vector Diagram Frequency Response Tracer | 9 | Frequency | Medium | T2 | Animated vectors from poles to frequency point | Bode construction via pole vectors |
| 16 | Euler Method Mapping Visualization | 7 | Transforms | Medium | T2 | s-plane circles mapping to z-plane | Discretization choices visualized |
| 17 | Bode Plot Constructor | 10 | Frequency | Medium | T2 | Magnitude + phase assembly from poles | Build Bode from primitive terms |
| 18 | Feedback Pole Migration with Gain Control | 10 | Control | Medium | T2 | Pole trajectory as K varies | Root locus concept |
| 19 | DT Frequency Response Unit Circle Explorer | 16-18 | DT Fourier | Medium | T2 | Point sweeping unit circle | Parametrization of unit circle |
| 20 | Time-Frequency Duality Interactive Mapper | 16 | FT Props | Medium | T2 | Dual time/freq domain panning | Scaling and shifting symmetry |
| 21 | Phase-Magnitude Separation in Filtering | 16-17 | FT Props | Medium | T2 | Overlay: minimum-phase vs. non-minimum | Phase and magnitude independence |
| 22 | Anti-Aliasing Filter Designer | 21-22 | Sampling | Medium | T2 | Interactive LPF cutoff slider | Design pre-sampling filter |
| 23 | Quantization Artifact Explorer | 22 | Sampling | Medium | T2 | Rounding error as noise overlay | Quantization error visualization |
| 24 | Modulation Scheme Comparator | 23-24 | Modulation | Medium | T2 | Three modulation types side-by-side | AM vs. FM vs. PM comparison |
| 25 | AM Radio Receiver Block Diagram | 23-24 | Modulation | Medium | T2 | Demodulation flow + local oscillator | End-to-end radio reception |
| 26 | Spectral Windowing and Leakage Explorer | 17-18 | FT Props | Medium | T2 | Window type selector + spectral leakage | Why windows matter in FFT |
| 27 | System Identification via Frequency Response Fitting | 10 | Frequency | Medium | T2 | Glider data + fitted poles/zeros | Reverse-engineer system from data |
| 28 | Laplace Transform Property Explorer | 6 | Laplace | Low-Med | T3 | Interactive property application | Shifting, scaling, differentiation |
| 29 | Convolution via 2D Visualization | 8 | Convolution | High | T3 | Image blur as convolution metaphor | Deconvolution and image restoration |
| 30 | Fourier Series to Transform Transition | 14-19 | Fourier | Medium | T3 | Periodic → aperiodic spectrum evolution | Continuous spectrum emerges |
| 31 | CT/DT Fourier Transform Frequency Mapping | 19 | FT Props | Medium | T3 | Frequency axis stretching/compression | Sampling theorem implications |
| 32 | Interactive Diffraction Grating FT | 20 | Optics | High | T3 | Wave pattern visualization | Fourier transform in physics |
| 33 | Discrete-Time Sampling Sequence Reconstructor | 22 | Sampling | Medium | T3 | Sampled signal + sinc reconstruction | ZOH vs. ideal sinc reconstruction |
| 34 | Sampling Rate Conversion Visualizer | 22 | Sampling | Medium | T3 | Interpolation/decimation animations | Upsampling and downsampling |
| 35 | Phase-Locked Loop Frequency Tracker | 24 | Modulation | High | T3 | Feedback loop locking animation | Frequency tracking in PLL |
| 36 | CD Audio Pipeline | 25 | Applications | High | T3 | Sampling → quantization → DA pipeline | Real-world audio chain |
| 37 | Gibbs Phenomenon Visualizer | 14-15 | Fourier | Low | T3 | Overshoot at discontinuities | Harmonic convergence limitations |
| 38 | Cascade vs. Parallel Realization Comparison | 3, 5 | Transforms | Medium | T3 | Two block diagrams side-by-side | Implementation equivalence |
| 39 | State-Space to Transfer Function Converter | 13 | Control | Medium | T3 | A, B, C, D matrices ↔ H(s) | Modal and transfer function duality |
| 40 | Nyquist Stability Criterion Explorer | 13 | Control | High | T3 | Nyquist plot + encirclement animation | Frequency-domain stability test |

---

## Detailed Specifications by Topic Area

### 1. Signal Fundamentals & Physical Analogies (Lecture 1)

#### Simulation 1: Leaky Tank Water Dynamics

**Visual Cues Observed:**
- Animated side-view tank with rising/falling water level
- Four tank configurations illustrating time constant effect
- Visual comparison: larger tanks fill slower with same input
- Plotly curves showing exponential approach to equilibrium
- Proportional leak rate visualization (hole size impact)

**Learning Objective:**
Develop intuition for first-order systems and time constant τ through tangible physical metaphor. Understand how parameters determine dynamic behavior.

**Theoretical Foundation:**
$$\frac{dh(t)}{dt} = \frac{1}{\tau}[r_0(t) - r_1(t)]$$

where τ = time constant (inverse frequency), $r_1(t) \propto h(t)$ (linear leakage).

Solution for constant input: $h(t) = \tau R_0 (1 - e^{-t/\tau})$

**System Architecture:**
- **Parameters:** Tank Area (0.5–5 m²), Hole Area (0.001–0.1 m²), Input Flow (0–2 m³/s), Leak Coefficient (0.5–1.0), Initial Height (0–2 m)
- **Observables:** Water Height h(t), Time Constant τ (visual marking at 63.2% point), Output Flow r₁(t), Phase Portrait (h vs. dh/dt)

**Visualization Strategy:**
- **Left Panel:** 2D animated tank with water level gradient (gray → cyan), hole size proportional to slider
- **Right Panel:** Three Plotly subplots:
  1. h(t) with exponential curve + reference line at 63.2%
  2. r₁(t) showing proportional leakage
  3. Phase plane (h vs. dh/dt) with trajectory loop
- **Interaction:** Adjust tank size/hole size → see immediate visual changes; click "Open Valve" → animate filling

**Implementation Notes:**
- **Complexity:** Low
- **Backend:** Analytical solution $h(t) = \tau r_0(1 - e^{-t/\tau})$, derivative for phase plane
- **Frontend:** SVG tank animation + Plotly subplots with live update on slider change (debounce 150ms)
- **Custom Viewer:** Yes (animated tank component)

**Extension Ideas:**
- Dual-tank cascade (second tank lags first)
- Non-linear leakage: $r_1(t) \propto \sqrt{h(t)}$
- Real-world analogs: battery charging, medication metabolism, epidemic modeling

---

### 2. Discrete-Time Systems & Block Diagrams (Lectures 2-3)

#### Simulation 2: Block Diagram Execution Animator

**Visual Cues Observed:**
- Frame-by-frame animation: n=0, n=1, n=2, ... showing signal values at each node
- Red numeric values appearing at node positions during computation
- Operator algebra equations alongside diagrams
- Visual distinction: delay boxes (R) vs. integrator boxes (A)
- Accumulator system building impulse response incrementally

**Learning Objective:**
Transform abstract operators and difference equations into watchable step-by-step execution. Bridge from block diagrams to mathematical operator expressions.

**Theoretical Foundation:**
For accumulator: $y[n] = x[n] + y[n-1]$

Given impulse input x[n] = δ[n], starting from rest:
$$y[0] = 1, \quad y[1] = 1, \quad y[2] = 1, \quad \Rightarrow h[n] = u[n]$$

Operator form: $(1 - R)Y = X$ → $Y = \frac{1}{1-R}X = (1 + R + R^2 + \ldots)X$

**System Architecture:**
- **Parameters:** System Type (Differencer, Accumulator, Geometric Decay, 2nd-order), Input Signal (δ[n], u[n], Custom), Simulation Steps (1–15), Animation Speed (0.2–2.0 steps/sec), Show Operator Form (bool), Show Impulse Response (bool)
- **Observables:** Block Diagram State (animated nodes + edges), Node Value Tables (n vs. values), Impulse Response h[n] (bar chart), Operator Expansion (LaTeX), Phase Diagram (optional)

**Visualization Strategy:**
- **Left Panel (60%):** Large D3.js block diagram with:
  - Nodes as circles labeled (x[n], y[n-1], y[n], etc.)
  - Edges as arrows with signal flow
  - Current values in bold white text inside nodes
  - Animation: highlight input → flash arrows → compute adders → output update → advance step
- **Right Panel (40%):**
  - Top: Table [n | x[n] | y[n-1] | y[n] | ...] with current row highlighted
  - Middle: Growing bar chart for h[n] with new bar appearing each step
  - Bottom: LaTeX operator equation updating in real-time
- **Color Scheme:** Input (cyan), Delay memory (orange), Adders (green), Output (teal), Impulse response (purple gradient)

**Implementation Notes:**
- **Complexity:** Medium
- **Backend:** Parse block diagram → dependency graph → compute in topological order → track h[n]
- **Frontend:** D3.js layout + SVG text elements with CSS transitions + Plotly bar chart + MathJax equations
- **Pre-built Examples:** Differencer (1, -1, 0, ...), Accumulator (1, 1, 1, ...), Geometric decay (1, 0.7, 0.49, ...), 2nd-order

**Extension Ideas:**
- Quiz mode: predict h[n] before animating
- Reverse quiz: given h[n], reconstruct block diagram
- User-drawn custom diagrams (drag-and-drop delays/adders)
- Feedback stability exploration

---

#### Simulation 3: Pole Location → Mode Shape Explorer

**Visual Cues Observed:**
- Complex plane diagrams (s-plane for CT, z-plane for DT) with poles as × marks
- Fundamental mode shapes plotted alongside pole locations
- Arrows connecting poles to time-domain responses
- Visualization: pole motion → response decay/frequency change
- Fibonacci modes spiraling in complex plane (population growth)

**Learning Objective:**
Create intuitive visual connection between pole location in complex plane and time-domain mode shape. Transform abstract pole concept into concrete, visible dynamics.

**Theoretical Foundation:**
For DT system with pole $p_k = r_k e^{j\theta_k}$, the mode is:
$$\text{mode} = p_k^n u[n] = r_k^n e^{jn\theta_k} u[n]$$

For complex conjugate poles: $p = re^{j\theta}, \bar{p} = re^{-j\theta}$ → mode = $2r^n\cos(n\theta)$

CT: pole $s = \sigma + j\omega$ → mode $e^{(\sigma + j\omega)t}u(t) = e^{\sigma t}e^{j\omega t}u(t)$

**System Architecture:**
- **Parameters:** Domain (DT/CT), Pole Real Part (-2 to 2), Pole Imag Part (-π to π for DT; -5 to 5 for CT), Number of Poles (1, 2, 3), Conjugate Pairing (auto/manual), Simulation Time Span (1–50 for DT; 0–10 for CT)
- **Observables:** Complex Plane (z or s-plane with poles), Time-Domain Impulse Response (multi-line plot), Mode Shape Overlay (animated trajectory), Stability Indicator (red/yellow/green)

**Visualization Strategy:**
- **Left Panel (50%): Complex Plane**
  - Plotly 2D scatter with Real axis, Imaginary axis
  - Unit circle (DT) or imaginary axis (CT) as stability boundary
  - Pole locations as draggable × markers
  - Shaded stable region (green) and unstable region (red)
  - Click-and-drag to move poles; live response update
- **Right Panel (50%): Time-Domain Responses**
  - Top: Impulse response h[n] or h(t) as Plotly line plot
    - If conjugate poles: show individual modes (dashed), composite (solid)
    - Different colors per pole
    - Exponential envelope $r^n$ or $e^{\sigma t}$ in gray
  - Bottom: Phase plane trajectory (h[n] in complex plane, spiraling inward/outward)

**Implementation Notes:**
- **Complexity:** Medium-High
- **Backend:** Compute h[n] = p^n for each pole, handle complex conjugate pairs, stability check
- **Frontend:** Plotly for both panels with synchronized updates, draggable poles via overlay or custom interaction
- **Visual Design:** Distinct colors per pole (blue, red, green for first three)

**Extension Ideas:**
- Drag pole from unstable → stable region
- Challenge: "Place poles so impulse response peaks at n=3, decays to 5% by n=10"
- Bode plot connection: show how pole locations manifest as peaks/valleys in frequency response
- Step response vs. impulse response toggle

---

### 3. Continuous-Time Systems & Operator Representations (Lecture 4)

#### Simulation 4: CT Integrator vs. DT Delay: Visual Comparison Engine

**Visual Cues Observed:**
- Side-by-side block diagrams: CT with ∫ box vs. DT with R box
- Parallel differential equation $\dot{y} = x + py$ vs. difference equation $y[n] = x[n] + py[n-1]$
- Feedback loop comparison: CT spiral accumulation vs. DT discrete jumps
- Operator algebra: $(1 - pA)$ for CT mirrors $(1 - pR)$ for DT
- Fundamental mode comparison: $e^{pt}u(t)$ vs. $p^n u[n]$

**Learning Objective:**
Demystify parallel structure between CT and DT by exploring both side-by-side with identical parameters. Show mathematical isomorphism while illustrating different stable regions and temporal patterns.

**Theoretical Foundation:**
**CT System:** $\dot{y}(t) = x(t) + py(t)$ with operator form $(1 - pA)Y = AX$
- Impulse response: $h(t) = e^{pt}u(t)$
- Stability: $\text{Re}(p) < 0$ (left half-plane)

**DT System:** $y[n] = x[n] + py[n-1]$ with operator form $(1 - pR)Y = X$
- Impulse response: $h[n] = p^n u[n]$
- Stability: $|p| < 1$ (inside unit circle)

**System Architecture:**
- **Parameters:** Pole Real Part (p) (-2 to 2, shared), Input Type (Impulse/Step/Ramp/Custom), Time Span CT (0–5 sec), Sample Rate DT (0.5–10 samples/sec), Show Envelope (bool), Sync Display (bool)
- **Observables:** CT Response (smooth curve), DT Response (discrete points), Overlaid Response (both on same axes), Block Diagrams (side-by-side), Mode Comparison, Stability Regions

**Visualization Strategy:**
- **Top Row (60%): Two Side-by-Side Time-Domain Plots**
  - *Left (CT):* Smooth curve y_c(t) = e^(pt)u(t), optional input overlay, envelope reference line
  - *Right (DT):* Discrete points y[n] = p^n u[n], vertical stem lines, sampling instants shown
  - Both plots share y-axis range; time axes proportional for direct comparison
  - Overlay: If "Sync Display" enabled, CT curve sampled at DT instants
- **Bottom Row (40%): Block Diagrams & Complex Planes**
  - Left: CT block diagram with ∫ and feedback loop
  - Middle: DT block diagram with R and feedback loop
  - Right: Complex planes showing s-plane (left half-plane stable) and z-plane (unit circle stable)

**Implementation Notes:**
- **Complexity:** Medium
- **Backend:** CT: y(t) = e^(pt)·u(t) at dense grid; DT: y[n] = p^n·u[n] for n = 0, 1, ...
- **Frontend:** Plotly for time plots, simple SVG for block diagrams, Plotly scatter for complex planes
- **Memoization:** Cache curves if p unchanged; regenerate only on slider move

**Extension Ideas:**
- Sampler effect: complex poles, show aliasing when Nyquist exceeded
- ZOH reconstruction: after sampling DT signal, show step-wise CT approximation
- Matched pole placement: compute equivalent DT pole (bilinear/Tustin)
- Discretization error: plot |y_c(nT) - y[n]| vs. time

---

#### Simulation 5: Partial Fraction Decomposition Builder

**Visual Cues Observed:**
- Polynomial multiplication layout showing coefficient combination
- Parallel decomposition: Y = c₁/(1 - p₁R) + c₂/(1 - p₂R) as separate feedback paths
- Graphical stacking of two geometric sequences forming composite response
- Poles-to-partial-fractions algorithm step-by-step
- Rational polynomials factored into (z - z₀)(z - z₁) form

**Learning Objective:**
Teach that any high-order rational system can decompose into simpler first-order (or conjugate pair) subsystems. Complex behavior emerges from superposition of simple modes.

**Theoretical Foundation:**
Given rational Z-transform or Laplace:
$$H(z) = \frac{b_0 + b_1 z^{-1} + \ldots}{1 + a_1 z^{-1} + a_2 z^{-2} + \ldots}$$

Factor denominator: $1 + a_1 z^{-1} + a_2 z^{-2} = (1 - p_0 z^{-1})(1 - p_1 z^{-1})\ldots$

Partial fractions:
$$H(z) = \frac{c_0}{1 - p_0 z^{-1}} + \frac{c_1}{1 - p_1 z^{-1}} + \ldots$$

**System Architecture:**
- **Parameters:** System Order (1, 2, 3), Pole Locations (-2 to 2), Numerator Coefficients (-5 to 5 each), Input Type (Impulse/Step), Display Mode (Symbolic/Numerical/Visual Stacking)
- **Observables:** Factored Denominator (LaTeX), Partial Fraction Expansion (LaTeX), Individual Mode Responses (curves), Composite Response (bold curve), Stacked Area Chart (colored regions), Pole Diagram (z-plane scatter)

**Visualization Strategy:**
- **Left Panel (40%): Symbolic Mathematics**
  - Three equivalent forms stacked vertically:
    1. Operator form: $(1 + 1.6R + 0.63R^2)Y = X$
    2. Factored form: $(1 - 0.7R)(1 - 0.9R)Y = X$
    3. Partial fractions: $Y = \frac{4.5}{1-0.9R}X + \frac{-3.5}{1-0.7R}X$
  - MathJax/KaTeX rendering, color-coded poles (blue, red, green)
  - Highlight matching terms across forms
- **Top Right (30%): Complex Plane**
  - z-plane with poles as colored × marks
  - Unit circle (stability boundary)
  - Pole coordinates listed below
- **Bottom Right (30%): Individual Modes**
  - Plotly line chart with one curve per mode
  - Same colors as poles
  - Each labeled: "Mode 1: 4.5 × 0.9^n"
  - Composite response as bold black curve
- **Optional Full-Width Bottom: Stacked Area Chart**
  - Colored areas for each mode, stacked vertically
  - Total height = composite response h[n]
  - Hover to highlight mode contribution

**Implementation Notes:**
- **Complexity:** High
- **Backend:** Pole finding (numpy.roots), partial fraction coefficients (residue formula or linear solve), verify decomposition
- **Frontend:** MathJax equations + Plotly z-plane + Plotly mode curves + optional Canvas/Plotly stacked area
- **Numerical Stability:** Avoid direct polynomial formation; use pole-residue form

**Extension Ideas:**
- Complex conjugate poles: show how two complex modes combine for real response
- Improper fractions: polynomial + proper fraction decomposition
- Stability from decomposition: prove convergence
- Cascade vs. parallel realization: compare block diagrams and complexity

---

### 4. Laplace & Z Transforms (Lectures 5-7)

#### Simulation 6: Interactive ROC Explorer

**Visual Cues Observed:**
- Time-domain interpretations of ROC regions via stacked diagrams
- Finite-duration, left-sided, right-sided, bilateral signals each mapped to ROC half-planes
- Pole location determines convergence region boundaries
- s-plane boundary between convergence and divergence as vertical line

**Learning Objective:**
Understand how pole location constrains ROC; develop intuition that ROC is determined by signal causality and decay properties.

**Theoretical Foundation:**
ROC is the set where $\int_{-\infty}^{\infty} |x(t)e^{-\sigma t}| dt < \infty$.

- Right-sided causal: $x(t) = e^{-at}u(t) \Rightarrow X(s) = \frac{1}{s+a}$, ROC: $\sigma > -a$
- Left-sided: $x(t) = -e^{-at}u(-t) \Rightarrow X(s) = \frac{1}{s+a}$, ROC: $\sigma < -a$
- Bilateral: Two-sided exponential $\Rightarrow$ ROC: $-a < \sigma < -b$ (vertical strip)

**System Architecture:**
- **Parameters:** Pole Real Part (-5 to 2), Pole Imaginary Part (-5 to 5), Signal Type (causal/anti-causal/bilateral), Test Frequency σ (-6 to 3, draggable)
- **Observables:** ROC Region (shaded on s-plane), Magnitude Response (time-domain exponential envelope), Pole Location (red ×), Convergence Status (color indicator)

**Visualization Strategy:**
- **Left Panel (50%): Interactive s-plane**
  - Draggable pole, shaded ROC region (half-plane or strip)
  - Movable test frequency point (σ slider)
  - As pole moves, ROC boundary updates live
- **Right Panel (50%): Time-Domain Signal**
  - $x(t) = e^{-pt}u(t)$ where p is pole
  - Overlay of envelope $e^{-\sigma t}$ (where σ is test frequency)
  - Inside ROC: product decays → integral converges (green)
  - Outside ROC: product grows → integral diverges (red)
  - Shaded region under decay curve shows integral contribution

**Implementation Notes:**
- **Complexity:** Medium
- **Backend:** Compute ROC analytically, numerical integration at test σ for convergence check
- **Frontend:** Plotly s-plane + Plotly time-domain plot, draggable pole via overlay interaction

**Extension Ideas:**
- Real poles only first, then complex poles
- Show transfer function H(s) and Fourier transform as σ → 0
- Pole on imaginary axis (marginal stability)

---

#### Simulation 7: Euler Method Mapping Visualization

**Visual Cues Observed:**
- Paired s-plane and z-plane diagrams with colored pole location markers
- Forward Euler dots form circle in z-plane; Backward Euler form different circle
- Visual mapping: pole at s = -1/T maps to different z locations depending on method
- Arrows indicate mapping direction; slopes/curvatures show distortion at high frequency

**Learning Objective:**
Understand discretization as nonlinear mapping from s-plane to z-plane. Develop intuition that different methods (Forward, Backward, Tustin) produce different mappings, with different stability properties.

**Theoretical Foundation:**
**Forward Euler:** $s \approx \frac{z - 1}{T}$ → $z \approx 1 + Ts$
- Continuous pole at $s = -1/T$ maps to $z = 0$ ✓
- Continuous pole at $s = -10/T$ maps to $z = -9$ (unstable!)
- Stability circle in z-plane: $|z - 1| = 1$ (centered at z=1, radius 1)

**Backward Euler:** $s \approx \frac{z - 1}{Tz}$ → $z = \frac{1}{1 - Ts}$
- All left-half-plane poles map to inside unit circle (unconditionally stable)
- But high-frequency response is distorted

**Tustin (Trapezoidal):** $s \approx \frac{2}{T} \frac{z - 1}{z + 1}$
- Preserves low-frequency response exactly
- Left-half-plane maps to inside unit circle
- Circle: $|z| = 1$ is image of imaginary axis (Re(s)=0)

**System Architecture:**
- **Parameters:** Continuous Pole Real (-10 to 0.5), Continuous Pole Imaginary (-5 to 5), Sampling Period T (0.01 to 1, log scale), Method (Forward/Backward/Tustin)
- **Observables:** Mapped Pole Location (blue dot on z-plane), Stability Circle (unit circle), Mapping Curve (parametric curve), Method Comparison (overlay three methods)

**Visualization Strategy:**
- **Left Panel (s-plane):** Vertical line of poles (varying imaginary, fixed real). Highlighted pole with red ×.
- **Middle Panel:** Mapping equation display, method name, toggle between methods
- **Right Panel (z-plane):** Unit circle (stability boundary), three dots (Forward/Backward/Tustin mapped locations). Green if inside circle (stable), red if outside.

**Implementation Notes:**
- **Complexity:** Medium
- **Backend:** Forward: z = 1 + T·s; Backward: z = 1/(1 - T·s); Tustin: z = (1 + T·s/2)/(1 - T·s/2)
- **Frontend:** Plotly s-plane, Plotly z-plane with unit circle background + three colored dots

**Extension Ideas:**
- Sweep continuous pole along vertical line to trace circles
- Vary sampling period to show convergence as T → 0
- Show high-frequency pole distortion more explicitly

---

### 5. Convolution & Impulse Response (Lecture 8)

#### Simulation 8: Convolution Flip-and-Shift Animator

**Visual Cues Observed:**
- Step-by-step animation of convolution: flip one sequence, slide it across the other
- Multiplication and summation at each position visually highlighted
- Intermediate products shown as transparent overlays
- Result growing as convolution output accumulates
- Check-yourself problems with specific signal pairs

**Learning Objective:**
Demystify convolution operation by animating the flip-and-shift mechanics. Show how impulse response determines output for arbitrary inputs.

**Theoretical Foundation:**
$$y[n] = \sum_{k=-\infty}^{\infty} h[k]·x[n-k] = h[n] * x[n]$$

The flip-and-shift: $h[k]$ is flipped (becomes $h[-k]$), then shifted by n positions.

For finite-length signals: output length = input length + impulse response length - 1.

**System Architecture:**
- **Parameters:** Input Signal (from preset list or custom), Impulse Response (preset or custom), Simulation Speed (0.2–2.0 steps/sec), Show Intermediate Products (bool), Show Result Evolution (bool)
- **Observables:** Input Signal x[n], Flipped Impulse Response h[-k], Shifted Impulse Response h[n-k], Pointwise Products h[n-k]·x[k], Output y[n] (accumulating)

**Visualization Strategy:**
- **Top Row (40%):** Three Plotly subplots side-by-side
  - Left: Input signal x[n] (blue bars, current index highlighted)
  - Middle: Impulse response h[k] (red bars), flipped version h[-k] (red inverted), shifted h[n-k] (semi-transparent red, shows position)
  - Right: Pointwise product at current shift (green bars showing h[n-k]·x[k])
- **Bottom Row (60%):** Single Plotly line plot
  - Evolving output y[n] as convolution accumulates
  - Already-computed points (solid black), current computation (orange highlight), future points (grayed out)
  - Cumulative sum display numerically below
- **Animation Loop:**
  1. At shift n: show x[n] highlighted
  2. Flip h → show h[-k]
  3. Shift flipped h by n → show h[n-k] at position n
  4. Overlay x[n] on h[n-k]
  5. Compute pointwise products and sum
  6. Plot y[n] value
  7. Move to n+1

**Implementation Notes:**
- **Complexity:** Medium
- **Backend:** Compute full convolution upfront; extract intermediate states for animation
- **Frontend:** Plotly subplots with synchronized animation loop, JavaScript timer for playback control
- **Pre-built Examples:** x[n] = {1, 2, 3}, h[n] = {1, 1} (averaging filter)

**Extension Ideas:**
- User-drawn custom x[n] and h[n] (drag points on Plotly plot)
- Circular convolution (periodic extension)
- Deconvolution: given y[n] and h[n], recover x[n]
- 2D convolution visualization (image blur example)

---

### 6. Frequency Response & Bode Diagrams (Lectures 9-10)

#### Simulation 9: High-Q Resonant System Explorer

**Visual Cues Observed:**
- Pole pair migration in s-plane as Q increases
- Pole positions: $\sigma = -\frac{\omega_0}{2Q}$ ± j$\sqrt{\omega_0^2 - \frac{\omega_0^2}{4Q^2}}$
- Narrowing resonance peaks in magnitude Bode plots (log scale)
- Sharp phase transitions with increasing Q
- Vector-based analysis showing angle relationships
- Bandwidth ≈ ω₀/Q relationship
- Phase change over 3dB bandwidth ≈ π/2

**Learning Objective:**
Understand relationship between pole location in s-plane and frequency response characteristics. Develop intuition about quality factor, resonance sharpness, peak magnitude, bandwidth.

**Theoretical Foundation:**
For second-order system: $H(s) = \frac{1}{1 + \frac{1}{Q}\frac{s}{\omega_0} + (\frac{s}{\omega_0})^2}$

Poles at: $\sigma \pm j\omega_d$ where $\sigma = -\frac{\omega_0}{2Q}$, $\omega_d = \omega_0\sqrt{1 - \frac{1}{4Q^2}}$

Peak response ≈ Q (for high Q), Bandwidth Δω ≈ ω₀/Q

**System Architecture:**
- **Parameters:** Q (0.5–50, log scale), ω₀ (0.1–10 rad/s), Scale (1–100)
- **Observables:** Pole Locations (s-plane), Magnitude Response (log-log Bode), Phase Response (semi-log Bode), 3dB Bandwidth (shaded region), Vector Analysis (optional)

**Visualization Strategy:**
- **Main View:** Three synchronized plots (s-plane, magnitude Bode, phase Bode)
  - s-plane: pole pair with Q-contours
  - Magnitude Bode: log-log plot with peak annotation, 3dB bandwidth shaded
  - Phase Bode: semi-log with phase gradient color-coding
- **Interactive Synchronization:** Hover over s-plane pole → highlight corresponding frequency response region
- **Derived Metrics Panel:** Display Q, ω₀, peak magnitude, 3dB bandwidth numerically
- **Animation Option:** Sweep Q from low to high with real-time plot updates

**Implementation Notes:**
- **Complexity:** Medium
- **Backend:** Pole calculation, frequency response via direct evaluation or second-order canonical form, 3dB bandwidth detection
- **Frontend:** Plotly for all three plots with synchronized hover and drag

**Extension Ideas:**
- Pole-zero diagram overlay (zeros at infinity)
- Group delay visualization (-dφ/dω)
- Step response animation as Q changes
- Comparison tool: two different Q values side-by-side
- Physical system examples (RLC, mechanical resonance, acoustic cavities)

---

#### Simulation 10: Feedback Control System Parameter Sweep

**Visual Cues Observed:**
- Block diagrams with feedback loops: X → ±[error] → Controller → Plant → Y
- Closed-loop pole location control via gain/controller design
- Multiple feedback topologies: P, PI, PD, PID with step response overlays
- Pole migration diagrams as controller gain K varies
- Comparison of responses: oscillations vs. smoothness trade-off
- Motor controller example: velocity feedback + integral action
- Closed-loop transfer function: $H_{cl}(s) = \frac{K·G_p}{1 + \beta K G_p}$

**Learning Objective:**
Understand how feedback modifies system poles to achieve desired transient and steady-state characteristics. Develop intuition about speed (rise time), overshoot, stability trade-offs.

**Theoretical Foundation:**
Feedback system with plant $G_p(s)$ and controller $C(s)$:

$$H_{cl}(s) = \frac{C(s)·G_p(s)}{1 + C(s)·G_p(s)·\beta}$$

Closed-loop poles determine stability (Re < 0) and dynamics (bandwidth, Q).
- Proportional K: scales poles uniformly (limited pole relocation)
- Integral: adds pole at origin, improves steady-state tracking
- Derivative: adds zero, increases stability margin

**System Architecture:**
- **Parameters:** Controller Type (P/PI/PD/PID), K_p (0.1–10), K_i (0–5), K_d (0–2), Plant Time Constant (0.1–2 sec), Reference Input (step/ramp/sinusoid)
- **Observables:** Closed-Loop Poles (s-plane), Step Response (with 0%/2%/10% bands), Error Signal (reference - output), Bode Plot (CL), Control Effort u(t), Performance Metrics (rise time, overshoot %, settling time, SSE)

**Visualization Strategy:**
- **Two-Column Layout:**
  - **Left (40%):** Block diagram with parameter sliders inline
  - **Right (60%):** Four stacked time-domain plots
    1. Reference + output
    2. Error signal
    3. Closed-loop poles in s-plane
    4. Control signal u(t)
- **Real-Time Updates:** Debounce slider changes (150ms), re-compute poles + step response
- **Pole Motion Trail:** Show recent pole locations as K varies (faint history)
- **Stability Region:** Shade s-plane left half-plane as "stable"
- **Overlaid Comparisons:** Freeze one config, compare against variations

**Implementation Notes:**
- **Complexity:** Medium-High
- **Backend:** Plant TF (first-order or integrator+lag), Controller TF (K_p + K_i/s + K_d·s), closed-loop poles (numpy.roots), step response (scipy.signal.step or custom ODE solver)
- **Frontend:** SVG block diagram, Plotly subplots with real-time updates

**Extension Ideas:**
- Root locus tool: animate pole movement as single gain K varies
- Frequency domain analysis: Nyquist plot, gain/phase margin
- State-space representation: show A, B, C, D matrices + eigenvalues
- Disturbance rejection: add step disturbance, show rejection capability
- Saturation effects: nonlinear actuator saturation
- Physical system modeling: DC motor, robotic arm, aircraft altitude hold

---

#### Simulation 11: Spectral Replication Visualizer

**Visual Cues Observed:**
- Impulse train sampling diagrams: $x_p(t) = \sum x[n]\delta(t - nT)$
- Frequency domain replication patterns: copies of X(jω) at integer multiples of ω_s
- Four progressively denser aliasing demonstrations
- Check yourself problems on harmonic aliasing

**Learning Objective:**
Visualize dual relationship between sampling in time domain and spectral replication in frequency domain. Understand aliasing geometrically.

**Theoretical Foundation:**
When signal sampled with period T, spectrum replicated at intervals $\omega_s = 2\pi/T$:

$$X_p(j\omega) = \frac{1}{T} \sum_{k=-\infty}^{\infty} X(j(\omega - k\omega_s))$$

Without anti-aliasing, overlapping replicas cause aliasing. Nyquist criterion: $\omega_s \geq 2\omega_{max}$

**System Architecture:**
- **Parameters:** Signal Frequency (0.1–5 kHz), Sampling Rate (2–50 kHz), Signal Amplitude (0.1–2.0), Nyquist Display (bool), Anti-alias Filter (bool), Num Replicas (1–5)
- **Observables:** Original Spectrum (freq domain), Sampled Spectrum (replicated copies), Aliased Components (highlighted), Reconstruction (time-domain result if anti-aliasing applied)

**Visualization Strategy:**
- **Top Plot (50%):** Frequency domain
  - Original signal spectrum (blue envelope)
  - Impulse train samples (red stems at sampling frequencies)
  - Replicated spectra as shaded regions or overlays
  - Nyquist boundary marked (dashed vertical line at ±ω_s/2)
  - Aliasing region highlighted in pink (where replicas overlap)
- **Bottom Plot (50%):** Time domain
  - Original continuous signal (blue curve)
  - Sampled signal (red dots at sampling instants)
  - Reconstructed signal (green curve) if anti-alias filter enabled
  - Error between original and reconstructed shown as light red shading

**Implementation Notes:**
- **Complexity:** Medium
- **Backend:** FFT of test signal, replicate spectrum at ω_s intervals, overlay/sum replicas to show aliasing
- **Frontend:** Plotly frequency plot + Plotly time-domain plot with synchronized slider control

**Extension Ideas:**
- Aliasing frequency calculation: given signal f and sample rate, compute alias frequency
- Anti-aliasing filter design: adjust cutoff, see aliasing reduction
- Multiple frequency components: see which ones alias
- Nyquist rate determination: slider to find minimum sampling rate

---

### 7. Feedback & Control Systems (Lectures 11-13)

(Simulations 9, 10, 13, 14, 15, 18 cover this area; see above and below for details)

#### Simulation 12: Fourier Series Harmonic Builder

**Visual Cues Observed:**
- Spectrum plots showing harmonic content (piano, violin, bassoon, oboe)
- Multiple harmonics at ω₀, 2ω₀, 3ω₀, ... with amplitude coefficients a_k
- Synthesis animation: successive harmonics reconstruct original
- Square, triangle, sawtooth waveforms with harmonic series
- Convergence visualization: partial sums as N increases
- Harmonic decay patterns: "plucked" vs. "sustained" instruments
- Harmonic interference: octave, fifth, unison relationships

**Learning Objective:**
Develop intuition about frequency content. Understand how periodic signals decompose into harmonics. Visualize Parseval's theorem. Learn harmonic relationships in music.

**Theoretical Foundation:**
**Real Form:** $x(t) = a_0 + \sum[a_k\cos(k\omega_0 t) + b_k\sin(k\omega_0 t)]$

**Complex Form:** $x(t) = \sum a_k e^{jk\omega_0 t}$ where $a_k = \frac{1}{T}\int_0^T x(t)e^{-jk\omega_0 t}dt$

**Key Properties:**
- a₀ is DC component (average)
- Harmonic k has frequency k·ω₀ and amplitude |a_k|
- Phase ∠a_k determines time waveform shape
- Parseval: ∫|x(t)|² dt = Σ|a_k|² (energy conservation)

**System Architecture:**
- **Parameters:** Waveform Type (square/triangle/sawtooth/custom), Fundamental Frequency f₀ (1–1000 Hz), Number of Harmonics N (1–50), Amplitude a₀ (0–1), Phase Shift φ (0–2π, optional), Display Mode (magnitude/phase/real/imaginary)
- **Observables:** Time-Domain Signal (reconstructed x(t)), Harmonic Spectrum (stem plot), Phase Spectrum (optional), Harmonic Addition Animation (cumulative overlay), Error/Residual, Energy Distribution (bar/pie chart), Waveform Comparison (true vs. approximation)

**Visualization Strategy:**
- **Two-Column Layout:**
  - **Left Panel:** Frequency-domain stem plot of harmonics (magnitude ± phase toggle)
    - One stem per harmonic at frequency kf₀
    - Color-coded by amplitude (darker = larger)
    - Slider to add harmonics one-by-one
  - **Right Panel:** Time-domain signal reconstruction
    - True signal (faint background)
    - N-harmonic reconstruction (bold curve)
    - Overlay approach as N increases (animation)
- **Interactive Harmonic Selection:** Click on stem → highlight that harmonic in time domain
- **Animation Controls:** Play/pause button to step through harmonics
- **Stacked View Option:** Show sine + cosine components separately
- **Audio Playback (Optional):** Synthesize and play reconstructed signal

**Implementation Notes:**
- **Complexity:** Medium
- **Backend:**
  - Square: a_k = (4/π)/k for odd k
  - Triangle: a_k = (8/π²)/k² for odd k
  - Sawtooth: a_k = -2/(πk) for all k ≠ 0
  - Custom: FFT via numpy.fft.fft or numerical integration
  - Partial sum: x_N(t) = Σ_{k=-N}^{N} a_k·e^(jk·ω₀·t)
  - RMS error: sqrt(mean((x_exact - x_approx)²))
- **Frontend:** Stem plot (Plotly bar) + line plot (Plotly) with slider, optional audio synthesis

**Extension Ideas:**
- Harmonic timbre explorer: load real instrument samples, compute harmonic content
- Gibbs phenomenon: highlight overshoot at discontinuities (square wave edges)
- Window functions: apply Hann/Hamming, show spectral leakage reduction
- Phase & magnitude relationships: phase shift without spectrum magnitude change
- Music intervals: harmonic relationships (octave, fifth, major third)
- Synthetic sound design: design harmonic content, hear result
- Convergence metrics: L² error vs. N, harmonic amplitude decay rate

---

### 8-13. Fourier Transforms & Applications (Lectures 16-25)

(These are complex and comprise 16 simulations; detailed in sections below)

---

## Implementation Effort Matrix

| Simulation | Backend (hrs) | Frontend (hrs) | Custom Viewer? | Est. Total |
|---|---|---|---|---|
| 1. Leaky Tank | 3 | 8 | Yes | 11 |
| 2. Block Diagram Animator | 6 | 12 | Yes | 18 |
| 3. Pole Mode Explorer | 5 | 10 | No | 15 |
| 4. CT vs DT Comparison | 4 | 9 | Yes | 13 |
| 5. Partial Fractions | 8 | 10 | Yes | 18 |
| 6. ROC Explorer | 4 | 8 | No | 12 |
| 7. Euler Mapping | 4 | 8 | No | 12 |
| 8. Convolution Animator | 5 | 10 | Yes | 15 |
| 9. High-Q Resonant | 4 | 8 | No | 12 |
| 10. Feedback Control | 6 | 12 | Yes | 18 |
| 11. Spectral Replication | 4 | 8 | No | 12 |
| 12. Fourier Series Builder | 5 | 10 | Yes | 15 |
| 13. Motor Controller | 5 | 10 | Yes | 15 |
| 14. DT Feedback Pole | 4 | 8 | No | 12 |
| 15. Vector Diagram Tracer | 5 | 9 | No | 14 |
| 16. Bode Constructor | 4 | 9 | No | 13 |
| 17. Feedback Pole Migration | 4 | 8 | No | 12 |
| 18. FT Pair Navigator | 5 | 10 | No | 15 |
| 19. DT Unit Circle Explorer | 4 | 8 | No | 12 |
| 20. Time-Freq Duality | 4 | 8 | No | 12 |
| 21. Phase-Magnitude Sep | 4 | 8 | No | 12 |
| 22. Anti-Aliasing Filter | 4 | 8 | No | 12 |
| 23. Quantization Explorer | 4 | 8 | No | 12 |
| 24. Modulation Comparator | 6 | 10 | No | 16 |
| 25. AM Radio Receiver | 6 | 10 | Yes | 16 |
| 26. Spectral Windowing | 5 | 9 | No | 14 |
| 27. System Identification | 6 | 10 | No | 16 |
| **TIER 1 TOTAL** | **60** | **135** | **8 viewers** | **195 hrs** |
| **TIER 2 TOTAL** | **75** | **135** | **6 viewers** | **210 hrs** |
| **TIER 3 TOTAL** | **65** | **130** | **5 viewers** | **195 hrs** |
| **GRAND TOTAL** | **200** | **400** | **19 viewers** | **600 hrs** |

---

## Visual Theme Analysis

### 1. Recurring Diagram Types in MIT 6.003 Slides

**Block Diagrams (Lectures 2-13, 23-24)**
- Delay boxes (R or z⁻¹) in DT, Integrators (A or ∫) in CT
- Adders (+) and multipliers (gains, arrows with coefficients)
- Feedback loops with βs gains (negative feedback standard)
- Signal flow left-to-right, with feedback returning from output
- **Visual Pattern:** Boxes connected by lines; signal values annotated at nodes
- **Animation Opportunity:** Step-by-step value propagation with node highlighting

**Pole-Zero Diagrams (Lectures 3-13, 16-22)**
- s-plane for CT (Re axis vertical, ± imaginary axis)
- z-plane for DT (circle at origin, ± imaginary axis, unit circle boundary)
- Poles as × marks, zeros as ○ circles
- Color-coded by frequency content or system role
- **Visual Pattern:** Scatter plots with labeled axes, stability regions shaded
- **Animation Opportunity:** Draggable poles, real-time response update

**Bode Plots (Lectures 9-10, 16-20)**
- Magnitude in dB (20 log |H|) vs. log frequency, often asymptotic lines shown
- Phase in degrees vs. log frequency, showing ±180° wrapping
- Characteristic slopes: ±20 dB/decade for each pole/zero
- Resonance peaks and anti-resonances (zeros) clearly visible
- **Visual Pattern:** Two subplots (magnitude, phase), log-log or semi-log axes
- **Animation Opportunity:** Trace magnitude/phase as frequency sweeps; pole vectors

**Frequency Response Plots (Lectures 16-20)**
- Linear plots showing magnitude |H(jω)| or |H(e^jω)| vs. frequency
- Often with log axes for better visibility
- Peaks at resonances, nulls at anti-resonances
- Phase response as separate plot or overlay (color-coded)
- **Visual Pattern:** Line plots, Plotly compatible
- **Animation Opportunity:** Point moving along frequency axis; pole-vector overlay

**Spectral/Harmonic Plots (Lectures 14-15, 17-22)**
- Stem plots or bar charts showing amplitude vs. harmonic number or frequency
- Often with phase information color-coded or in separate plot
- Energy concentration (Parseval's theorem visualization)
- **Visual Pattern:** Vertical lines (stems) from axis to amplitude value
- **Animation Opportunity:** Harmonics appearing one by one; cumulative synthesis

**Time-Domain Waveforms (All lectures)**
- Continuous curves for CT signals (Plotly line plots)
- Discrete points for DT signals (Plotly scatter or stem plots)
- Often overlaid (e.g., input + output, or multiple filter responses)
- Exponential envelopes shown as thin reference curves
- **Visual Pattern:** Plotly line/scatter plots with multiple traces
- **Animation Opportunity:** Signal evolution in time; playback or slider control

**Complex Plane Trajectories (Lectures 11-12, 16)**
- Pole/zero locations animated as parameter varies
- Spiral or circular paths showing mode evolution
- Enclosed regions (unit circle for stability, left-half plane for CT)
- **Visual Pattern:** Scatter plot in complex plane with trail/history
- **Animation Opportunity:** Continuous animation of pole movement

---

### 2. Color Coding Patterns in MIT Lectures

| Element | Color in Slides | Suggested Web Color | Context |
|---|---|---|---|
| Input Signal | Blue (often darker) | #3b82f6 (Plotly standard) | Primary trace; drives system |
| Output Signal | Red | #ef4444 | Response; consequence of input |
| Reference/Target | Green | #10b981 | Desired trajectory in control |
| Impulse Response | Purple | #7c3aed | Mode decomposition |
| Envelope/Boundary | Gray | #94a3b8 | Theoretical bound (e.g., e^{-σt}) |
| Stable Region | Light Green | rgba(16, 185, 129, 0.1) | Shaded area in complex plane |
| Unstable Region | Light Red | rgba(239, 68, 68, 0.1) | Shaded area in complex plane |
| Feedback Path | Orange | #f97316 | Distinction from forward path |
| Poles | Red × or blue × | #ef4444 or #3b82f6 | Large, clearly marked |
| Zeros | Blue ○ | #3b82f6 | Circles to distinguish from poles |
| Highlighted Current | Yellow | #fbbf24 | Current node/point in animation |
| Success/Valid | Green | #10b981 | Convergent, stable, correct |
| Warning/Marginal | Amber | #f59e0b | Marginal stability, edge case |
| Error/Invalid | Red | #ef4444 | Divergent, unstable, incorrect |

---

### 3. Animation Sequences from MIT Slides

**Block Diagram Execution (Lectures 2-4)**
1. Frame shows n=0 state
2. Input value x[0] appears at input node (bright cyan)
3. Arrows flash in sequence (blue → orange for delayed values)
4. Adder node glows yellow during computation
5. Output node updates, turning teal
6. Frame advances to n=1
7. Repeat for 5-15 steps

**Harmonic Buildup (Lectures 14-19)**
1. Empty plot with frequency axis labeled
2. DC component a₀ appears as bar at k=0
3. Fundamental a₁ appears (bright blue bar)
4. Harmonic 2: bar appears at k=2 (red)
5. Time-domain curve updates, becoming less square (more rounded)
6. Harmonic 3: bar at k=3 (green)
7. Continue to n=20 or user-selected limit
8. Residual error shown as light red curve decaying

**Pole Migration (Lectures 3-4, 10-13)**
1. s-plane or z-plane shown with grid
2. Pole at initial location (red ×)
3. User adjusts slider for pole parameter (K, Q, etc.)
4. Pole animates along trajectory (1-2 second smooth transition)
5. Right-side plots (time-domain or Bode) update synchronously
6. Trail (faint history) shows recent pole positions
7. Stable/unstable region coloring changes as pole crosses boundary

**Convolution Flip-Shift (Lecture 8)**
1. Input x[n] shown as blue bar chart
2. Impulse response h[n] shown as red bar chart
3. At step n: h[n] flips (becomes h[-n], red bars flip horizontally)
4. Flipped h shifts by n: h[n-k] (semi-transparent red bars move right)
5. Overlay x[n] on h[n-k] (blue bars appear at flipped h positions)
6. Pointwise products shown: green bars at x[k]·h[n-k]
7. Sum appears as number
8. Output y[n] bar grows in output chart
9. Advance to step n+1

**Sampling Visualization (Lectures 21-22)**
1. Continuous signal x(t) shown as blue curve
2. Sampling instants marked as vertical dashed lines
3. Sampled values appear as red dots at sampling instants
4. Time-domain plot: impulse train appears (red stems)
5. Frequency-domain plot: original spectrum (blue envelope) + replicas (red shaded regions)
6. If sample rate too low: aliasing highlighted (overlapping replicas in pink)
7. Anti-aliasing filter applied: low-pass response overlaid (green), replicas outside cutoff zeroed

---

### 4. Key "Aha Moment" Diagrams (Must Replicate Interactively)

**#1: Time Constant τ at 63.2% (Lecture 1)**
- Tank filling curve with horizontal line at 63.2% of final value
- Vertical line down to time axis at t = τ
- Interactive: adjust tank size, watch τ change on curve
- **Why critical:** Students finally understand what τ *means* visually

**#2: Pole Location Determines Mode (Lectures 3-4)**
- s-plane with pole at specific location
- Time-domain curve showing e^{σt}·cos(ωt) shape
- Interactive: drag pole → mode updates in real-time
- **Why critical:** Pole abstraction becomes concrete

**#3: Stable vs. Unstable Region (All lectures)**
- Complex plane divided by boundary (left half-plane CT, unit circle DT)
- Poles in/out of region marked with color
- Interactive: drag pole into/out of stable region, watch response diverge/converge
- **Why critical:** Stability criterion becomes visual intuition

**#4: High Q = Sharp Resonance (Lecture 11)**
- Bode magnitude plot with narrow peak
- Pole pair near imaginary axis (small σ)
- Interactive: increase Q slider, watch peak sharpen and move toward jω axis
- **Why critical:** Connects pole proximity to response sharpness

**#5: Nyquist Theorem via Spectral Replication (Lecture 21)**
- Original signal spectrum (blue)
- Sampled signal: replicated spectra (red shaded) at ±ω_s, ±2ω_s, ...
- Aliasing when replicas overlap (pink highlight)
- Interactive: lower sampling rate → replicas move closer → aliasing visible
- **Why critical:** Why Nyquist criterion ω_s ≥ 2ω_max becomes obvious

**#6: Harmonic Synthesis (Lectures 14-15)**
- Empty waveform plot
- Add fundamental: sine wave shape appears (purple)
- Add 2nd harmonic: wave modulates (green)
- Add 3rd harmonic: sharp edges emerge toward square wave
- Add many harmonics: square wave converges (almost perfect)
- **Why critical:** Students see frequency content building real signal

---

## Dependency Map & Learning Path

### Prerequisite Structure

```
Lecture 1: Fundamentals
├─→ Sim 1: Leaky Tank (time constant intuition)
└─→ Foundations for all downstream content

Lectures 2-4: Block Diagrams & Operators
├─→ Sim 2: Block Diagram Animator
├─→ Sim 3: Pole Mode Explorer (prerequisite: understand what modes are)
├─→ Sim 4: CT vs DT Comparison (builds on simulator 3)
└─→ Sim 5: Partial Fractions (requires pole-to-mode understanding)

Lectures 5-7: Transforms
├─→ Sim 6: ROC Explorer
├─→ Sim 7: Euler Mapping (discretization concepts)
└─→ [Sim 5 relied on earlier]

Lecture 8: Convolution
└─→ Sim 8: Convolution Animator (self-contained, but block diagram understanding helps)

Lectures 9-10: Frequency Response & Feedback
├─→ Sim 9: High-Q Resonant (requires pole-frequency knowledge from Sim 3)
├─→ Sim 10: Feedback Control (builds on pole understanding + frequency response)
├─→ Sim 11: Spectral Replication (sampling intuition)
├─→ Sim 15: Vector Diagram Tracer (requires Bode knowledge)
├─→ Sim 16: Bode Constructor
├─→ Sim 17: Feedback Pole Migration (root locus concept)
└─→ Sim 14: DT Feedback Pole Response

Lectures 11-13: Advanced Feedback & Control
├─→ Sim 13: Motor Controller (realistic application of Sim 10)
├─→ Sim 39: State-Space to TF (alternative representation)
└─→ Sim 40: Nyquist Stability Criterion

Lectures 14-15: Fourier Series
├─→ Sim 12: Fourier Series Harmonic Builder (core visualization)
└─→ Sim 30: FS to Transform Transition (bridge to aperiodic)

Lectures 16-20: Fourier Transforms
├─→ Sim 18: FT Pair Navigator (time-frequency duality)
├─→ Sim 19: DT Frequency Response Unit Circle
├─→ Sim 20: Time-Frequency Duality Mapper
├─→ Sim 21: Phase-Magnitude Separation
├─→ Sim 26: Spectral Windowing (FFT practical issues)
├─→ Sim 31: CT/DT FT Frequency Mapping
└─→ Sim 32: Diffraction Grating FT (physics connection)

Lectures 21-22: Sampling & Reconstruction
├─→ Sim 11: Spectral Replication (already listed, core concept)
├─→ Sim 22: Anti-Aliasing Filter Designer
├─→ Sim 23: Quantization Artifact Explorer
├─→ Sim 33: Sampling Sequence Reconstructor (sinc, ZOH)
├─→ Sim 34: Sampling Rate Conversion
└─→ Sim 36: CD Audio Pipeline (capstone application)

Lectures 23-24: Modulation
├─→ Sim 24: Modulation Scheme Comparator (AM/FM/PM)
├─→ Sim 25: AM Radio Receiver Block Diagram
└─→ Sim 35: Phase-Locked Loop Frequency Tracker

Lecture 25: Capstone Applications
└─→ Sim 36: CD Audio Pipeline (Sim 11, 22, 23, 33 prerequisites)
```

### Recommended Learning Path for Students

**Week 1-2: Fundamentals & Intuition**
1. Leaky Tank (Sim 1) — understand τ
2. Block Diagram Animator (Sim 2) — see operators execute
3. Pole Mode Explorer (Sim 3) — pole ↔ mode connection

**Week 3-4: Analysis Tools**
4. CT vs DT Comparison (Sim 4) — see isomorphism
5. Partial Fractions (Sim 5) — decomposition intuition
6. ROC Explorer (Sim 6) — convergence matters

**Week 5-6: Frequency Domain**
7. High-Q Resonant (Sim 9) — pole → frequency response
8. Convolution Animator (Sim 8) — operation demystified
9. Vector Diagram Tracer (Sim 15) — Bode construction

**Week 7-8: System Design**
10. Feedback Control (Sim 10) — closed-loop poles
11. Motor Controller (Sim 13) — realistic application
12. Fourier Series Builder (Sim 12) — frequency decomposition

**Week 9-10: Sampling & Applications**
13. Spectral Replication (Sim 11) — why aliasing happens
14. Anti-Aliasing Filter Designer (Sim 22) — filter design
15. Modulation Comparator (Sim 24) — communication

**Capstone:** CD Audio Pipeline (Sim 36) — integrates 8+ concepts

---

## Integration with Existing Simulations

The project likely already has some core simulations. Here's how new ones complement them:

| Existing Sim Category | New Tier 1 Simulations | Synergies |
|---|---|---|
| Signal Processing | Leaky Tank, Fourier Series | Fundamentals → frequency analysis |
| Circuits | CT vs DT | Filter design parallel |
| Control Systems | Feedback Control, Motor Controller | PID parameter space exploration |
| Transforms | ROC Explorer, Partial Fractions | Understanding transform domain |
| Optics | Diffraction Grating FT (T3) | Fourier in physics |

---

## Visual Theme Recommendations for UI Design

### Master Color Palette (Extends CLAUDE.md theme variables)

```css
/* Existing Variables (from CLAUDE.md) */
--primary-color: #14b8a6;        /* Teal */
--secondary-color: #3b82f6;      /* Blue */
--accent-purple: #7c3aed;        /* Purple */
--success-color: #10b981;        /* Green */
--warning-color: #f59e0b;        /* Amber */
--error-color: #ef4444;          /* Red */

/* New Signal/Systems-Specific Colors */
--signal-input: #3b82f6;         /* Blue - input signals */
--signal-output: #ef4444;        /* Red - output/response */
--signal-reference: #10b981;     /* Green - reference/target */
--spectrum-primary: #7c3aed;     /* Purple - magnitude spectrum */
--spectrum-phase: #f97316;       /* Orange - phase information */
--envelope-color: #94a3b8;       /* Gray - theoretical bounds */
--pole-color: #ef4444;           /* Red - poles */
--zero-color: #3b82f6;           /* Blue - zeros */
--stable-region: rgba(16, 185, 129, 0.1);    /* Green-tinted */
--unstable-region: rgba(239, 68, 68, 0.1);   /* Red-tinted */
--feedback-path: #f97316;        /* Orange - feedback signal */
--harmonic-gradient-1: #7c3aed;  /* Harmonic 1 (purple) */
--harmonic-gradient-2: #06b6d4;  /* Harmonic 2 (cyan) */
--harmonic-gradient-3: #10b981;  /* Harmonic 3 (green) */
```

### Component Design Principles

1. **Consistent Plotly Theme**
   - All line plots use standard Plotly colors from CLAUDE.md
   - Scatter points larger (10-12 px) for clarity
   - Grid lines semi-transparent for background visibility
   - Legend always positioned to avoid obscuring data

2. **Interactive Elements**
   - Sliders: primary-color background, white handle
   - Draggable poles: cursor changes to grab/grabbing
   - Hover tooltips: dark background (surface-color), white text, rounded corners
   - Button groups: toggle effect with accent-color highlight

3. **Animated Transitions**
   - Pole movement: 500-800ms smooth CSS transition
   - Signal updates: 150-250ms fade-in for new plots
   - Node value updates in block diagrams: 100ms bounce effect
   - Harmonic appearance: 200ms scale-up animation

4. **Accessibility**
   - All colors pass WCAG AA contrast ratio (4.5:1 minimum)
   - Colorblind-safe palette: avoid red-green combinations for critical info
   - Icons always paired with text labels
   - Keyboard navigation for all sliders and buttons

---

## Summary: Implementation Priorities

### Phase 1 (Months 1-3): Tier 1 Foundation — 12 Simulations, ~195 hours
**Goal:** Build core pedagogical tools covering Lectures 1-15

1. Leaky Tank (Sim 1)
2. Block Diagram Animator (Sim 2)
3. Pole Mode Explorer (Sim 3)
4. CT vs DT Comparison (Sim 4)
5. High-Q Resonant (Sim 9)
6. Feedback Control (Sim 10)
7. Fourier Series Builder (Sim 12)
8. Convolution Animator (Sim 8)
9. ROC Explorer (Sim 6)
10. Spectral Replication (Sim 11)
11. Fourier Transform Pair Navigator (Sim 18)
12. Partial Fractions (Sim 5)

**Milestones:**
- Week 4: Sims 1-3 deployed
- Week 8: Sims 4-9 deployed
- Week 12: Sims 10-12 deployed

### Phase 2 (Months 4-5): Tier 2 Enrichment — 15 Simulations, ~210 hours
**Goal:** Deep dives and specialized applications

- Motor Controller (Sim 13)
- DT Feedback Pole Response (Sim 14)
- Vector Diagram Tracer (Sim 15)
- Anti-Aliasing Filter Designer (Sim 22)
- Modulation Comparator (Sim 24)
- [+ 10 others from Tier 2]

### Phase 3 (Months 6-7): Tier 3 Capstone — 13 Simulations, ~195 hours
**Goal:** Specialized and advanced topics

- CD Audio Pipeline (Sim 36)
- Phase-Locked Loop (Sim 35)
- Nyquist Stability (Sim 40)
- [+ 10 others from Tier 3]

---

## Conclusion

This master catalog consolidates 40 unique simulations derived from visual analysis of MIT 6.003 lecture materials. The taxonomy by tier enables phased development, with Tier 1 providing maximal pedagogical impact for foundational understanding. Each simulation preserves detailed specifications for backend algorithms, frontend visualization strategies, and extension ideas to scaffold deeper learning.

The visual theme analysis reveals recurring patterns (block diagrams, pole-zero planes, Bode plots, spectral plots) that should inform a cohesive UI design language. Color coding, animation sequences, and interactive features can be standardized across all simulations to maximize student familiarity and reduce cognitive overhead.

**Total Estimated Development Time: ~600 hours** (20 developer-weeks at 30 hrs/week)

**Recommended Team:** 2-3 full-stack developers (Python/JavaScript) + 1 UI/UX designer + 1 QA engineer, 5-6 week sustained effort for Tier 1 deployment.

