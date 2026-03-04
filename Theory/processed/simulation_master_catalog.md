# Master Simulation Catalog
## MIT 6.003 Signals & Systems Interactive Simulations

**Generated:** February 28, 2026
**Source:** Comprehensive analysis of Lectures 1-25 batch specifications
**Status:** Complete deduplication and prioritization

---

## Executive Summary

### Overview Statistics
- **Total Unique Simulations Identified:** 48
- **Simulation Distribution by Category:**
  - Signal Fundamentals & Operations: 5
  - System Representations & Operators: 5
  - Transforms (Laplace, Z, Fourier): 10
  - Convolution & Response Analysis: 4
  - Frequency Response & Resonance: 8
  - Feedback & Control: 4
  - Fourier Series & Analysis: 6
  - Sampling, Reconstruction & Aliasing: 6
  - Modulation & Applications: 5
  - Miscellaneous (Pedagogical): 2

### Complexity Distribution
- **Low Complexity:** 8 simulations (13%)
- **Medium Complexity:** 25 simulations (52%)
- **Medium-High Complexity:** 12 simulations (25%)
- **High Complexity:** 3 simulations (6%)

### Visual "Wow Factor" & Pedagogical Impact
The catalog emphasizes **interactive discovery** through real-time parameter adjustment, coupled with synchronized multi-domain visualizations (time/frequency/pole-zero). Simulations featuring **audio playback**, **3D rendering**, or **animation** carry highest engagement value.

---

## Priority Implementation Roadmap

### TIER 1: Foundation & Highest Impact (Implement First)
**Rationale:** These form the conceptual bedrock. Students must master these before advancing to complex transforms and applications.

1. **Signal Transformation Visualizer** (Lecture 1)
2. **Leaky Tank / RC Circuit Interactive Explorer** (Lecture 1)
3. **Operator Algebra Block Diagram Equivalence Explorer** (Lecture 2)
4. **Feedback, Modes, and Stability Explorer** (Lecture 2)
5. **Fibonacci & Golden Ratio Mode Decomposition** (Lecture 3)
6. **Complex Poles & Oscillatory Modes** (Lecture 3)
7. **CT vs. DT Dual Evolution Engine** (Lecture 4)
8. **Impulse Response Decomposition & Modal Reconstruction** (Lecture 4)
9. **Pole-Zero Interactive Frequency Response Builder** (Lecture 9)
10. **Feedback Control Loop Stabilization Game** (Lecture 10)

**Estimated Team Effort:** 15-20 weeks (parallel teams of 2-3 developers)

### TIER 2: Extended Understanding (Next Wave)
**Rationale:** Build on Tier 1 foundations to explore deeper relationships and transform theory.

11. **Z Transform Region of Convergence (ROC) & Causality Explorer** (Lecture 5)
12. **Inverse Z Transform Partial Fractions & Convolution Explorer** (Lecture 5)
13. **Laplace Transform Region of Convergence Explorer** (Lecture 6)
14. **Numerical Approximation Method Comparison** (Lecture 7)
15. **Convolution Geometry in 2D** (Lecture 8)
16. **Bode Plot Constructor from Poles and Zeros** (Lecture 11)
17. **High-Q Resonator Response Landscape** (Lecture 11)
18. **Feedback Gain-Bandwidth Tradeoff Visualizer** (Lecture 12)
19. **Crossover Distortion Correction via Feedback** (Lecture 13)
20. **Harmonic Series Convergence and Gibbs Phenomenon** (Lecture 14)
21. **Formant Tracking and Vowel Synthesis** (Lecture 15)
22. **Eigenfunction Resonance Frequency Predictor** (Lecture 9)

**Estimated Team Effort:** 18-24 weeks (continued parallel development)

### TIER 3: Advanced & Specialized Topics (Future)
**Rationale:** High-value but more specialized; implement after students have mastered core concepts.

23. **Periodic Extension to Transform Converter** (Lecture 16)
24. **DT Frequency Response on the Unit Circle** (Lecture 17)
25. **Fourier Series Coefficients to Spectral Window** (Lecture 19)
26. **Discrete-Time Signal Aliasing via Frequency Wrapping** (Lecture 17)
27. **Custom Signal Design from Fourier Series Coefficients** (Lecture 16)
28. **Filtering Cascade and Frequency Response Chain** (Lecture 20)
29. **Spectral Convolution and Modulation Effects** (Lecture 19)
30. **Laplace → Fourier Transform via jω axis** (Lecture 16)
31. **Nyquist Paradox Explorer** (Lecture 21)
32. **Quantization & Perceptual Quality** (Lecture 22)
33. **Aliasing Frequency Mapper** (Lecture 21)
34. **FM Bandwidth Evolution** (Lecture 24)
35. **Dithering Artifact Explorer** (Lecture 22)
36. **CD Audio Pipeline** (Lecture 25)

**Estimated Team Effort:** 20-25 weeks

### Optional Enhancements & Extensions
- **Coupled Oscillators & Rabi Splitting** (Lecture 11 extension)
- **Bandpass Sampling & Sub-Nyquist Systems** (Lecture 21 extension)
- **JPEG/Compression via DCT** (Modulation extension)
- **Nyquist Criterion & Stability Margins** (Control extension)

---

## Master Index of All Simulations

| # | Simulation Name | Lecture(s) | Category | Complexity | Priority Tier | Key Innovation | Custom Viewer Required |
|---|---|---|---|---|---|---|---|
| 1 | Signal Transformation Visualizer | 1 | Signal Fundamentals | Medium | T1 | Multi-domain transform visualization | Yes |
| 2 | Leaky Tank / RC Circuit Interactive Explorer | 1 | System Basics | Medium | T1 | Unified physical system modeling | Yes |
| 3 | Operator Algebra Block Diagram Equivalence Explorer | 2 | System Representations | High | T1 | Interactive equation parsing & diagramming | Yes |
| 4 | Feedback, Modes, and Stability Explorer | 2 | Stability Analysis | High | T1 | Interactive pole dragging in z-plane | Yes |
| 5 | Fibonacci & Golden Ratio Mode Decomposition | 3 | Fundamental Modes | Medium-High | T1 | Mode superposition with famous sequence | No |
| 6 | Complex Poles & Oscillatory Modes | 3 | Oscillations | Medium | T1 | Conjugate pair visualization with spiral | Yes |
| 7 | CT vs. DT Dual Evolution Engine | 4 | CT/DT Mapping | High | T1 | Parallel system evolution comparison | Yes |
| 8 | Impulse Response Decomposition & Modal Reconstruction | 4 | Response Analysis | Medium-High | T1 | Mode extraction from mass-spring | Yes |
| 9 | Z Transform Region of Convergence Explorer | 5 | Transforms | Medium | T2 | Interactive ROC determination | Yes |
| 10 | Inverse Z Transform Partial Fractions & Convolution Explorer | 5 | Transforms | Medium-High | T2 | Step-by-step algebraic breakdown | Yes |
| 11 | Laplace Transform Region of Convergence Explorer | 6 | Transforms | Medium | T2 | 3D s-plane magnitude surface | Yes |
| 12 | Numerical Approximation Method Comparison | 7 | Discretization | Medium-High | T2 | Forward/Backward/Trapezoidal pole mapping | Yes |
| 13 | Convolution Geometry in 2D | 8 | Convolution | Medium | T2 | Interactive flip-shift-multiply visualization | Yes |
| 14 | Pole-Zero Interactive Frequency Response Builder | 9 | Frequency Response | High | T1 | Draggable pole/zero with real-time Bode | Yes |
| 15 | Eigenfunction Resonance Frequency Predictor | 9 | Frequency Response | Medium | T2 | Complex exponential input/output scaling | Yes |
| 16 | Feedback Control Loop Stabilization Game | 10 | Control Systems | High | T1 | Gamified root locus exploration | Yes |
| 17 | Bode Plot Constructor from Poles and Zeros | 11 | Frequency Response | Medium | T2 | Asymptotic Bode construction | Yes |
| 18 | High-Q Resonator Response Landscape | 11 | Resonance | Medium | T2 | Q factor control with heatmap | Yes |
| 19 | Feedback Gain-Bandwidth Tradeoff Visualizer | 12 | Feedback | Low-Medium | T2 | GBW product invariant discovery | Yes |
| 20 | Crossover Distortion Correction via Feedback | 13 | Nonlinearity | Medium | T2 | FFT + THD analysis with distortion | Yes |
| 21 | Harmonic Series Convergence and Gibbs Phenomenon | 14 | Fourier Series | Low-Medium | T2 | Progressive harmonic addition | No |
| 22 | Formant Tracking and Vowel Synthesis | 15 | Speech Processing | Medium-High | T2 | Real-time audio synthesis + spectrogram | Yes |
| 23 | Periodic Extension to Transform Converter | 16 | Fourier Transform | Medium | T3 | Animated transition to continuous spectrum | No |
| 24 | DT Frequency Response on the Unit Circle | 17 | DT Frequency | Medium-High | T3 | Interactive vector diagram | Yes |
| 25 | Fourier Series Coefficients to Spectral Window | 19 | Windowing | Medium | T3 | Window design & leakage visualization | No |
| 26 | Discrete-Time Signal Aliasing via Frequency Wrapping | 17 | Aliasing | Medium-High | T3 | Unit circle animation with folding | Yes |
| 27 | Custom Signal Design from Fourier Series Coefficients | 16 | Fourier Series | Medium | T3 | Interactive coefficient editor + synthesis | Yes |
| 28 | Filtering Cascade and Frequency Response Chain | 20 | Filtering | High | T3 | Multi-stage filter composition | Yes |
| 29 | Spectral Convolution and Modulation Effects | 19 | Modulation | High | T3 | Frequency-domain convolution animation | Yes |
| 30 | Laplace → Fourier Transform via jω axis | 16 | Transforms | High | T3 | 3D s-plane to Fourier extraction | Yes |
| 31 | Nyquist Paradox Explorer | 21 | Sampling | Medium | T3 | Aliased signal ambiguity demonstration | No |
| 32 | Quantization & Perceptual Quality | 22 | Quantization | Medium-High | T3 | Audio playback + spectrogram analysis | Yes |
| 33 | Aliasing Frequency Mapper | 21 | Sampling | Low-Medium | T3 | Frequency folding game/calculator | No |
| 34 | FM Bandwidth Evolution | 24 | Modulation | Medium-High | T3 | Bessel function visualization + Carson's rule | No |
| 35 | Dithering Artifact Explorer | 22 | Quantization | Medium | T3 | Visual + auditory dual-domain comparison | Yes |
| 36 | CD Audio Pipeline | 25 | Signal Chain | High | T3 | Complete encoding pipeline visualization | Yes |

---

## Detailed Specifications by Topic Area

### Section 1: Signal Fundamentals (Lectures 1-3)

#### 1. Signal Transformation Visualizer
- **Lecture Source:** Lecture 1, Pages 1-37
- **Learning Objective:** Build intuitive understanding of signal operations (scaling, time-shifting, time-scaling)
- **System Architecture:**
  - Input: Signal type, amplitude, time stretch, time shift, operation sequence
  - Outputs: Original & transformed waveform, spectrogram (if speech), transformation matrix
- **Key Parameters:** signal_type (sine/speech/image), amplitude (0.1-3.0), time_stretch (0.5-2.0), time_shift (-5 to 5)
- **Visualization:** Dual waveforms overlaid, optional spectrogram heatmap, operation log
- **Custom Viewer:** YES - Multi-panel with synchronized scroll and zoom
- **Implementation Complexity:** Medium
- **Backend Estimate:** 8-10 hours
- **Frontend Estimate:** 12-15 hours
- **Notes:** Supports speech (pre-computed spectrograms) and image transformations for spatial intuition

---

#### 2. Leaky Tank / RC Circuit Interactive Explorer
- **Lecture Source:** Lecture 1, Pages 25-37
- **Learning Objective:** Build physical intuition for first-order linear differential equations through tank water dynamics
- **System Architecture:**
  - Input: tank_type, hole_size, inflow_rate, inflow_profile (constant/pulse/ramp/sine)
  - Outputs: 3D animated tank height, leak vs. inflow stacked area chart, phase portrait
- **Key Insight:** Time constant τ discovery, exponential convergence, system ubiquity
- **Visualization:** 3D tank animation (Three.js or Plotly 3D), parametric phase portrait
- **Custom Viewer:** YES
- **Implementation Complexity:** Medium
- **Backend Estimate:** 6-8 hours (ODE integration)
- **Frontend Estimate:** 10-12 hours (3D rendering)
- **Notes:** Extensible to RC circuit and thermal system analogues

---

#### 3. Fibonacci & Golden Ratio Mode Decomposition
- **Lecture Source:** Lecture 3, Pages 1-47
- **Learning Objective:** Discover how system poles decompose responses into fundamental modes using famous sequence
- **System Architecture:**
  - Input: sequence_length, show_mode toggles, animation_speed
  - Outputs: Animated table of [n, F[n], φ^n, (-1/φ)^n], pole-zero diagram, mode convergence plot
- **Key Discovery:** Mode dominance, Binet's formula equivalence, phase spiral
- **Visualization:** Animated table with numerical precision, 2D phase portrait spiral
- **Custom Viewer:** NO (standard Plotly suffices)
- **Implementation Complexity:** Medium-High
- **Backend Estimate:** 4-5 hours
- **Frontend Estimate:** 6-8 hours

---

#### 4. Complex Poles & Oscillatory Modes
- **Lecture Source:** Lecture 3, Pages 38-47
- **Learning Objective:** Visualize complex conjugate poles and their oscillating-decaying modes
- **System Architecture:**
  - Input: pole_magnitude (0.3-1.2), pole_frequency (0-π), input_type, animation_mode
  - Outputs: z-plane pole diagram, mode 1 (real/imag), mode 2 (conjugate), weighted sum, envelope
- **Key Insights:** Unit circle stability boundary, conjugate necessity, frequency from angle
- **Visualization:** Interactive z-plane with draggable poles, 3D helix or 2D spiral
- **Custom Viewer:** YES
- **Implementation Complexity:** Medium
- **Backend Estimate:** 6-7 hours
- **Frontend Estimate:** 10-12 hours

---

#### 5. CT vs. DT Dual Evolution Engine
- **Lecture Source:** Lecture 4, Pages 1-50
- **Learning Objective:** Develop parallel intuition for CT and DT systems showing pole mapping similarity and differences
- **System Architecture:**
  - Input: pole_value_p, sampling_period_T, input_signal, simulation_time
  - Outputs: Dual CT smooth curve + DT discrete samples overlaid, dual pole diagrams, mode comparison
- **Key Insights:** Exponential vs. geometric growth, sampling introduces new poles, stability boundary shift
- **Visualization:** Dual plots with synchronized time axis, dual pole diagrams (s-plane + z-plane)
- **Custom Viewer:** YES
- **Implementation Complexity:** High
- **Backend Estimate:** 10-12 hours (dual solvers)
- **Frontend Estimate:** 14-16 hours (dual interactive planes)
- **Notes:** Critical simulation bridging foundational concept gap

---

### Section 2: System Representations (Lecture 2)

#### 6. Operator Algebra Block Diagram Equivalence Explorer
- **Lecture Source:** Lecture 2, Pages 4-57
- **Learning Objective:** Develop algebraic fluency with operator notation through visual block diagram equivalence
- **System Architecture:**
  - Input: operator_expr (text), input_signal, display_mode, canonical_form
  - Outputs: Parsed SVG block diagram, difference equation, pole-zero plot, step-by-step execution table
- **Key Challenge:** Symbolic parsing and LaTeX rendering
- **Visualization:** Interactive SVG block diagram, animated signal flow with step-by-step tables
- **Custom Viewer:** YES (extensive SVG/LaTeX work)
- **Implementation Complexity:** High
- **Backend Estimate:** 12-15 hours (SymPy parsing, pole/zero factorization)
- **Frontend Estimate:** 16-18 hours (SVG generation, animation)
- **Notes:** Consider using SymPy for symbolic algebra; may require pre-parsing library

---

#### 7. Feedback, Modes, and Stability Explorer
- **Lecture Source:** Lecture 2, Pages 58-90
- **Learning Objective:** Intuitively understand feedback effects on poles and stability via interactive pole manipulation
- **System Architecture:**
  - Input: feedback_coeff (-1.5 to 1.5), num_poles, pole_locations, input_type, show_cycles/show_modes
  - Outputs: Interactive z-plane pole diagram, fundamental modes, output as superposition, step response
- **Key Pedagogical Moments:** Pole crossing unit circle (stability boundary), mode superposition, cycle tracing animation
- **Visualization:** Draggable poles in z-plane with real-time response update, stacked area chart of modes
- **Custom Viewer:** YES
- **Implementation Complexity:** High
- **Backend Estimate:** 8-10 hours (pole computation, mode decomposition)
- **Frontend Estimate:** 12-14 hours (interactive z-plane, animation)

---

### Section 3: System Response Analysis (Lectures 4-8)

#### 8. Impulse Response Decomposition & Modal Reconstruction
- **Lecture Source:** Lecture 4, Pages 41-50
- **Learning Objective:** Understand impulse response emergence from poles via modal decomposition
- **System Architecture:**
  - Input: mass_M, spring_K, damping_B, system_type (undamped/underdamped/etc.)
  - Outputs: s-plane pole diagram, impulse response h(t), individual mode traces, weighted sum overlay
- **Key Insights:** Undamped oscillation (poles on jω axis), adding damping shifts poles left, energy conservation → pole location
- **Visualization:** Mode envelope curves, phase portrait (y, ẏ), energy conservation plot
- **Custom Viewer:** YES
- **Implementation Complexity:** Medium-High
- **Backend Estimate:** 8-10 hours (ODE solver, partial fractions)
- **Frontend Estimate:** 10-12 hours

---

#### 9. Convolution Geometry in 2D
- **Lecture Source:** Lecture 8, Pages 271-1439
- **Learning Objective:** Make "flip-shift-multiply" operation visual and intuitive through interactive animation
- **System Architecture:**
  - Input: x[n] (graphical editor), h[n] (preset or custom), output_index_n, view_mode
  - Outputs: Animated flip/shift, pointwise product region, accumulated sum, full output
- **Key Features:** Draggable signal editor, real-time convolution computation, 3D surface optional
- **Visualization:** Color-coded overlays showing h[-k] flipped, h[n-k] shifted, product x[k]×h[n-k]
- **Custom Viewer:** YES
- **Implementation Complexity:** Medium
- **Backend Estimate:** 6-8 hours (convolution + canvas rendering)
- **Frontend Estimate:** 10-12 hours (interactive editor)

---

### Section 4: Transforms (Lectures 5-7, 16)

#### 10. Z Transform Region of Convergence (ROC) & Causality Explorer
- **Lecture Source:** Lecture 5, Pages 1-42
- **Learning Objective:** Understand how ROC specifies time-domain signal and determines causality/stability
- **System Architecture:**
  - Input: transfer_function (text), roc_region (text or picker), num_poles
  - Outputs: z-plane pole/zero plot, multiple ROC regions, causal/anti-causal time-domain signals
- **Key Insight:** Same X(z) with different ROCs → different time-domain signals; ROC determines everything
- **Visualization:** Interactive z-plane with multiple ROC highlighting, dual time-domain signal tables/plots
- **Custom Viewer:** YES
- **Implementation Complexity:** Medium
- **Backend Estimate:** 8-10 hours (SymPy parsing, inverse Z-transform)
- **Frontend Estimate:** 10-12 hours

---

#### 11. Inverse Z Transform Partial Fractions & Convolution Explorer
- **Lecture Source:** Lecture 5, Pages 34-50
- **Learning Objective:** Master finding time-domain signals via partial fractions and table lookup
- **System Architecture:**
  - Input: x1_func, x2_func, operation (inverse_transform/convolution/cascade), decomposition_method
  - Outputs: Partial fractions breakdown, standard table entries, inverse signal, power series
- **Key Pedagogical Feature:** Step-by-step algebraic breakdown with color-coded form matching
- **Visualization:** MathJax-rendered step-by-step derivation, stem plots of resulting x[n]
- **Custom Viewer:** YES (custom MathJax panel)
- **Implementation Complexity:** Medium-High
- **Backend Estimate:** 10-12 hours
- **Frontend Estimate:** 12-14 hours

---

#### 12. Laplace Transform Region of Convergence Explorer
- **Lecture Source:** Lecture 6, Pages 355-536
- **Learning Objective:** Develop intuition for Laplace ROC relating to signal causality and time-domain properties
- **System Architecture:**
  - Input: Signal_type (right/left/two-sided), Pole_position (-5 to 5), Exponential_decay_rate (0.1-3.0)
  - Outputs: Time-domain signal, s-plane ROC (shaded), 3D convergence surface, pole-ROC relationship
- **Key Visual Feature:** 3D surface showing |X(s)| magnitude with "wall" at ROC boundary where divergence occurs
- **Visualization:** 3D Plotly surface, animated pole movement synchronized with ROC boundary shift
- **Custom Viewer:** YES
- **Implementation Complexity:** Medium
- **Backend Estimate:** 8-10 hours (3D surface computation)
- **Frontend Estimate:** 10-12 hours

---

#### 13. Numerical Approximation Method Comparison (Forward/Backward Euler & Trapezoidal)
- **Lecture Source:** Lecture 7, Pages 276-1095
- **Learning Objective:** Understand how discretization methods map s-plane poles to z-plane and affect stability
- **System Architecture:**
  - Input: CT_pole_location (-5 to 0), Sampling_period_T (0.01-2.0 s), Method (Forward/Backward/Trapezoidal)
  - Outputs: s-plane pole, z-plane pole (three methods), step response comparison, stability boundary animation
- **Key Discovery:** Forward Euler unstable for large T; Backward Euler always stable; Trapezoidal optimal
- **Visualization:** Animated pole locus as T increases, side-by-side step response comparison
- **Custom Viewer:** YES
- **Implementation Complexity:** Medium-High
- **Backend Estimate:** 8-10 hours
- **Frontend Estimate:** 12-14 hours

---

#### 14. Periodic Extension to Transform Converter
- **Lecture Source:** Lecture 16, Pages 3-39; Lecture 19-2, Pages 10-24
- **Learning Objective:** Visualize how aperiodic signals evolve into discrete spectrum through periodic extension
- **System Architecture:**
  - Input: Base_signal (pulse/triangle/sinc/gaussian), Signal_duration, Extension_period, Animation_speed
  - Outputs: Time-domain periodic extension, Fourier series coefficients as impulse train, continuous Fourier overlay
- **Key Insight:** As T → ∞, discrete impulses → continuous function; animated convergence
- **Visualization:** Dual panels (time/frequency) with animated impulse train moving closer together
- **Custom Viewer:** NO (Plotly dual-axis suffices)
- **Implementation Complexity:** Medium
- **Backend Estimate:** 6-8 hours (FFT, periodic extension)
- **Frontend Estimate:** 8-10 hours

---

#### 15. Laplace → Fourier Transform via jω axis
- **Lecture Source:** Lecture 16-2, Pages 9-13
- **Learning Objective:** Visualize relationship between 2D Laplace (s-plane) and 1D Fourier (jω-axis) via cross-section
- **System Architecture:**
  - Input: System (preset or custom), Pole_real_part, Pole_imaginary_part, Display_mode, Frequency_range
  - Outputs: s-plane pole/zero diagram, 3D Laplace magnitude surface, jω-axis cross-section, frequency response
- **Key Insight:** Fourier is 1D slice of 2D Laplace; ROC must include jω axis for Fourier to exist
- **Visualization:** 3D surface with highlighted jω axis trace, vertical "curtain" showing extraction
- **Custom Viewer:** YES
- **Implementation Complexity:** High
- **Backend Estimate:** 10-12 hours (3D surface generation)
- **Frontend Estimate:** 12-14 hours (interactive 3D visualization)

---

### Section 5: Frequency Response & Resonance (Lectures 9-11)

#### 16. Pole-Zero Interactive Frequency Response Builder
- **Lecture Source:** Lecture 9, Pages 200-1567
- **Learning Objective:** Master frequency response via direct pole/zero manipulation and vector diagram visualization
- **System Architecture:**
  - Input: Draggable poles/zeros in s-plane, DC_gain_K, Add/Remove buttons, Frequency_range
  - Outputs: s-plane diagram, magnitude Bode, phase Bode, vector diagram (real-time), 3D surface optional
- **Key Pedagogical Features:** Real-time vector feedback showing how each pole/zero contributes to magnitude/phase
- **Visualization:** Interactive s-plane with draggable controls, synchronized Bode plots with vector overlays
- **Custom Viewer:** YES (custom s-plane editor + vector diagram)
- **Implementation Complexity:** High
- **Backend Estimate:** 10-12 hours (frequency response computation, vector math)
- **Frontend Estimate:** 14-16 hours (interactive s-plane, real-time updates)
- **Notes:** High pedagogical value; strong "aha moment" potential

---

#### 17. Eigenfunction Resonance Frequency Predictor
- **Lecture Source:** Lecture 9, Pages 252-321
- **Learning Objective:** Develop intuition for eigenfunctions of LTI systems and frequency response via eigenvalue scaling
- **System Architecture:**
  - Input: System (transfer function), Input_frequency_ω₀, Input_type (real exponential/complex/cosine), Time_window
  - Outputs: Input waveform, output waveform, eigenvalue H(jω₀), magnitude/phase comparison, pole-zero diagram
- **Key Discovery:** Input and output have same frequency; magnitude/phase determined by pole-zero geometry
- **Visualization:** Animated input/output synchronized, animated complex eigenvalue vector
- **Custom Viewer:** YES
- **Implementation Complexity:** Medium
- **Backend Estimate:** 6-8 hours (ODE solver, eigenvalue calculation)
- **Frontend Estimate:** 10-12 hours

---

#### 18. Bode Plot Constructor from Poles and Zeros
- **Lecture Source:** Lecture 11, Pages 3-34
- **Learning Objective:** Build Bode plots by adding individual pole/zero contributions (in dB space)
- **System Architecture:**
  - Input: num_zeros, num_poles, draggable zero/pole locations, DC_gain, frequency_decade
  - Outputs: s-plane diagram, exact Bode magnitude, asymptotic Bode, phase, individual contributions, residual error
- **Key Discovery:** Additivity in dB space; asymptotic slopes (+20/-20 dB/decade); corner frequencies
- **Visualization:** Stacked/toggleable traces for each pole/zero, colored band showing asymptote error region
- **Custom Viewer:** YES
- **Implementation Complexity:** Medium
- **Backend Estimate:** 8-10 hours
- **Frontend Estimate:** 10-12 hours

---

#### 19. High-Q Resonator Response Landscape
- **Lecture Source:** Lecture 11, Pages 43-62
- **Learning Objective:** Understand Q factor control over peak height and phase transition sharpness
- **System Architecture:**
  - Input: quality_factor (0.5-50, logarithmic), center_frequency (0.1-10 Hz), input_amplitude, input_frequency
  - Outputs: s-plane poles, magnitude response with peak label, phase response, time-domain sinusoid, input/output phasor
- **Key Insight:** Higher Q → poles closer to jω axis → sharper peak → narrower bandwidth
- **Visualization:** 2D "resonance map" heatmap showing magnitude vs. frequency and Q, animated frequency sweep
- **Custom Viewer:** YES
- **Implementation Complexity:** Medium
- **Backend Estimate:** 6-8 hours
- **Frontend Estimate:** 10-12 hours

---

### Section 6: Feedback & Control (Lectures 10-13)

#### 20. Feedback Control Loop Stabilization Game
- **Lecture Source:** Lecture 10, Pages 204-1100
- **Learning Objective:** Discover hands-on how feedback gain affects closed-loop poles, stability, and response speed
- **System Architecture:**
  - Input: Proportional_gain_K (-10 to 10), System_plant (1st/2nd-order options), Sensor_delay (0-2 steps), Setpoint, Disturbance
  - Outputs: Closed-loop pole locations, root locus, step response, stability indicator, error vs. time, pole speed vector
- **Gamification:** "Dead-beat control" achievement (pole at origin), stability margins display
- **Visualization:** Interactive z-plane root locus with pole animation as K varies, step response superposition
- **Custom Viewer:** YES
- **Implementation Complexity:** High
- **Backend Estimate:** 10-12 hours (root locus generation, characteristic polynomial)
- **Frontend Estimate:** 12-14 hours (game mechanics, animations)
- **Notes:** Engagement driver; consider adding difficulty levels (Challenge: with sensor delay)

---

#### 21. Feedback Gain-Bandwidth Tradeoff Visualizer
- **Lecture Source:** Lecture 12, Pages 14-23
- **Learning Objective:** Demonstrate fundamental feedback principle: trading DC gain for bandwidth (GBW invariant)
- **System Architecture:**
  - Input: feedback_beta (0 to 1), op_amp_gain (1e4-1e6, logarithmic), op_amp_pole (10-1000 rad/s), input_signal
  - Outputs: s-plane poles (open/closed), magnitude Bode overlaid, DC gain values, bandwidth values, GBW product, step response
- **Key Invariant:** DC_gain × Bandwidth = constant (product never changes)
- **Visualization:** Overlaid open-loop (faint) vs. closed-loop (bold) Bode, animated pole trajectory as β sweeps
- **Custom Viewer:** YES
- **Implementation Complexity:** Low-Medium
- **Backend Estimate:** 6-8 hours
- **Frontend Estimate:** 8-10 hours

---

#### 22. Crossover Distortion Correction via Feedback
- **Lecture Source:** Lecture 13, Pages 9-17
- **Learning Objective:** Visualize how nonlinear distortion (crossover distortion) reduces dramatically with feedback
- **System Architecture:**
  - Input: transistor_threshold (0.2-1 V), loop_gain_K (1-100), feedback_fraction (0-1), input_amplitude, input_frequency
  - Outputs: Transfer characteristic (s-curve), open-loop output, closed-loop output (variable K), FFT spectrum, THD meter, loop gain indicator
- **Key Metric:** Total harmonic distortion (THD) scaling as 1/(1+L) with loop gain
- **Visualization:** Time-domain waveform comparison, FFT bar chart showing harmonic reduction, THD reduction curve
- **Custom Viewer:** YES
- **Implementation Complexity:** Medium
- **Backend Estimate:** 8-10 hours (nonlinear iteration, FFT)
- **Frontend Estimate:** 10-12 hours

---

### Section 7: Fourier Series & Analysis (Lectures 14-15)

#### 23. Harmonic Series Convergence and Gibbs Phenomenon
- **Lecture Source:** Lecture 14, Pages 22-40
- **Learning Objective:** Build intuition for Fourier series convergence and Gibbs phenomenon through incremental harmonic addition
- **System Architecture:**
  - Input: waveform_type (square/triangle/sawtooth/pulse), num_harmonics (1-99), duty_cycle, frequency, animation_mode
  - Outputs: Target waveform (gray), partial sum reconstruction, harmonic spectrum, reconstruction error, ripple magnitude
- **Key Discovery:** 1/k decay → slow convergence + Gibbs overshoot (~9%); 1/k² decay → smooth, faster convergence
- **Visualization:** Animated harmonic addition with progressive convergence, error integral display, zoomed discontinuity view
- **Custom Viewer:** NO (Plotly line plots sufficient)
- **Implementation Complexity:** Low-Medium
- **Backend Estimate:** 4-6 hours
- **Frontend Estimate:** 6-8 hours

---

#### 24. Formant Tracking and Vowel Synthesis
- **Lecture Source:** Lecture 15, Pages 27-34
- **Learning Objective:** Understand source-filter model through real-time vowel synthesis; manipulate formants to morph vowels
- **System Architecture:**
  - Input: vowel_preset (ah/eh/ee/oh/oo/custom), formant_1/2/3_freq (sliders or spectrum dragging), formant_bandwidth, glottis_frequency, glottis_shape, output_level
  - Outputs: Input spectrum (comb), vocal tract filter response, output spectrum (filtered), time-domain waveform, formant trajectory plot, spectrogram, real-time audio
- **Key Insight:** Formants (not harmonics) are filter peaks; moving F₁ changes openness, F₂ changes front/back
- **Visualization:** 2D vowel space plot (F₁ vs. F₂) with vowel trajectories, animated spectrogram during morphing
- **Custom Viewer:** YES (specialized for audio analysis + interactive spectrum dragging)
- **Implementation Complexity:** Medium-High
- **Backend Estimate:** 10-12 hours (audio synthesis, filter design, spectrogram)
- **Frontend Estimate:** 12-14 hours (spectrum dragging, vowel space visualization)
- **Notes:** Audio playback required; may use Web Audio API frontend + scipy backend

---

#### 25. Custom Signal Design from Fourier Series Coefficients
- **Lecture Source:** Lecture 16-17
- **Learning Objective:** Build intuition for how coefficients control waveform shape through interactive editing
- **System Architecture:**
  - Input: Period_N (8-32), Harmonic_index_k (0 to N-1), Magnitude_|a_k| (0-2), Phase_∠a_k (0-2π), Symmetry_mode
  - Outputs: Coefficient editor (sliders), magnitude spectrum, phase spectrum, time-domain waveform, constituent harmonics, cumulative synthesis animation
- **Key Discovery:** Zero coefficients → missing harmonics → smooth signals; high-k energy → discontinuities
- **Visualization:** Dual-domain split screen: left (coefficient editor), right (time-domain synthesis with animation)
- **Custom Viewer:** YES
- **Implementation Complexity:** Medium
- **Backend Estimate:** 6-8 hours (IFFT synthesis, constraint enforcement)
- **Frontend Estimate:** 10-12 hours (slider array UI, real-time synthesis)

---

### Section 8: Sampling, Reconstruction & Aliasing (Lectures 17, 19, 21-22)

#### 26. Discrete-Time Signal Aliasing via Frequency Wrapping
- **Lecture Source:** Lecture 17, Pages 29-42; Lecture 19-2, Pages 25-32
- **Learning Objective:** Develop intuition for DT frequency periodicity and aliasing through unit circle rotation
- **System Architecture:**
  - Input: CT_frequency_f (0.1-10 kHz), Sampling_rate_f_s (1-20 kHz), Animation_speed, Signal_type (sinusoid/chirp), Waveform_display
  - Outputs: CT waveform with sampling points, unit circle trajectory (e^{jΩn}), DT sequence stem plot, frequency domain comparison, Nyquist folding visualization
- **Key Pedagogical Feature:** Animated rotation on unit circle; when f > f_s/2, rotation reverses (aliasing)
- **Visualization:** Three-panel: CT signal, unit circle with animated point, frequency-domain comparison
- **Custom Viewer:** YES
- **Implementation Complexity:** Medium-High
- **Backend Estimate:** 8-10 hours (aliasing formula, animation sequencing)
- **Frontend Estimate:** 10-12 hours

---

#### 27. DT Frequency Response on the Unit Circle
- **Lecture Source:** Lecture 17, Pages 17-28
- **Learning Objective:** Build geometric intuition for why DT frequency response evaluated on unit circle (not entire z-plane)
- **System Architecture:**
  - Input: Zero_locations (interior/circle), Pole_locations (interior), DC_gain_K, Num_zeros/poles, Show_vectors
  - Outputs: z-plane diagram with unit circle, magnitude response (0 to 2π), phase response, vector traces, frequency response overlay
- **Key Insight:** Periodicity: H(e^{j(Ω+2π)}) = H(e^{jΩ}); poles inside → stable; outside → unstable
- **Visualization:** Three-panel synchronized: z-plane (top-left), magnitude (bottom-left), phase (bottom-right); draggable poles with real-time response update
- **Custom Viewer:** YES
- **Implementation Complexity:** Medium-High
- **Backend Estimate:** 8-10 hours (vector calculation, frequency response)
- **Frontend Estimate:** 12-14 hours (synchronized multi-panel)

---

#### 28. Fourier Series Coefficients to Spectral Window
- **Lecture Source:** Lecture 19-2, Pages 5-24; Lecture 20, Pages 35-39
- **Learning Objective:** Visualize spectral leakage and windowing trade-offs (main-lobe width vs. side-lobe suppression)
- **System Architecture:**
  - Input: Base_signal (sinusoid/multi-tone/chirp/AM), Signal_length_N (32-256), Window_type (rect/hamming/blackman/hann), Frequency, Display_mode
  - Outputs: Time-domain signal with window envelope, window function plot, DFT magnitude, windowed spectrum, window comparison table
- **Key Trade-off:** Narrow main-lobe ↔ high side-lobes (rectangular); wider main-lobe ↔ low side-lobes (Hamming/Blackman)
- **Visualization:** Four-panel: time-domain, window function, linear magnitude, log-magnitude with dB scale and side-lobe markers
- **Custom Viewer:** NO (Plotly grid layout)
- **Implementation Complexity:** Medium
- **Backend Estimate:** 6-8 hours (window functions, FFT, dB conversion)
- **Frontend Estimate:** 8-10 hours

---

#### 29. Nyquist Paradox Explorer
- **Lecture Source:** Lecture 21, Pages 12-19
- **Learning Objective:** Intuitively understand why different CT signals produce identical samples above Nyquist rate
- **System Architecture:**
  - Input: Signal_frequency (0.5-8 kHz), Sampling_rate (1-16 kHz), Number_of_periods, Phase (0-2π)
  - Outputs: Continuous signal (blue), discrete samples (orange), aliased reconstructed signal (red dashed), frequency domain (original + sampled copies)
- **Key Insight:** Same samples at boundary → ambiguity; user reduces f_s and watches as original and alternative signals produce identical samples
- **Visualization:** Dual time/frequency panels; frequency-domain shows replica copies at ±nf_s intervals
- **Custom Viewer:** NO (Plotly dual-axis)
- **Implementation Complexity:** Medium
- **Backend Estimate:** 4-6 hours
- **Frontend Estimate:** 6-8 hours

---

#### 30. Aliasing Frequency Mapper
- **Lecture Source:** Lecture 21, Pages 31-40
- **Learning Objective:** Master the aliasing wrapping mechanism; predict alias frequency given input frequency and sampling rate
- **System Architecture:**
  - Input: Input_frequency (0-100 kHz, text/slider), Sampling_rate (1-50 kHz), Number_of_replicas (1-5)
  - Outputs: Frequency axis diagram with Nyquist zones, input frequency marker, aliased frequency marker, animated folding path, formula display
- **Key Feature:** Interactive "fold and wrap" animation showing how frequency bounces at Nyquist boundaries
- **Visualization:** Extended frequency axis with colored Nyquist zones, animated arrow tracing folding path, equation breakdown
- **Custom Viewer:** NO (Plotly annotation sufficient)
- **Implementation Complexity:** Low-Medium
- **Backend Estimate:** 3-4 hours (aliasing formula)
- **Frontend Estimate:** 5-6 hours

---

#### 31. Quantization & Perceptual Quality
- **Lecture Source:** Lecture 22, Pages 8-30
- **Learning Objective:** Understand amplitude quantization error, why bit depth affects quality nonlinearly, and how dithering helps
- **System Architecture:**
  - Input: Bit_depth (1-16), Dithering_mode (None/Random/Roberts), Signal_complexity (Sine/Speech/Music), Audio_playback
  - Outputs: Original signal (blue), quantized signal (stepped), error signal, spectrogram, quality metrics (SNR/SINAD/Noise_floor)
- **Key Metric:** SNR ≈ 6.02b + 1.76 dB; dithering trades SNR for perceptual smoothness
- **Visualization:** Waveform overlay, stepped staircase, error heatmap, spectrogram showing noise distribution
- **Custom Viewer:** YES (custom quantization panel)
- **Implementation Complexity:** Medium-High
- **Backend Estimate:** 8-10 hours (quantization, dithering, spectrogram)
- **Frontend Estimate:** 10-12 hours (audio playback, waveform rendering)

---

#### 32. Dithering Artifact Explorer
- **Lecture Source:** Lecture 22, Pages 23-45
- **Learning Objective:** Understand how dithering trades error patterns (banding) for white noise; discover Roberts' optimization
- **System Architecture:**
  - Input: Bit_depth (2-8), Dithering_method (None/Random/Roberts/Triangular), Test_pattern (Gradient/Sine_Sweep/Speech), Zoom_level
  - Outputs: Original image/signal (smooth), quantized output (with/without dithering), error spectrogram, comparison views (3-panel), perceptual quality slider
- **Key Discovery:** Visual banding eliminated; replaced with visible noise (often perceptually preferable)
- **Visualization:** Dual-domain (visual gradient + auditory waveform), zoomed pixel-level detail, error spectrum heatmap
- **Custom Viewer:** YES (image + audio comparison panel)
- **Implementation Complexity:** Medium
- **Backend Estimate:** 8-10 hours (dithering algorithms, spectrogram)
- **Frontend Estimate:** 10-12 hours (image/audio rendering)

---

### Section 9: Modulation & Applications (Lectures 19, 20, 24-25)

#### 33. FM Bandwidth Evolution
- **Lecture Source:** Lecture 24, Pages 99-43
- **Learning Objective:** Viscerally understand how modulation index controls bandwidth and sideband distribution via Bessel functions
- **System Architecture:**
  - Input: Modulation_index_m (0.1-20, logarithmic), Message_frequency_f_m (100 Hz-10 kHz), Carrier_frequency_f_c (10-100 kHz), Modulation_regime_toggle
  - Outputs: Time-domain waveform, frequency spectrum with sideband bars, Bessel function overlay, instantaneous frequency plot, Carson's bandwidth indicator, occupied bandwidth % display
- **Key Discovery:** Narrowband FM (m < 1) ~ AM bandwidth; Wideband FM (m > 1) bandwidth grows as m increases
- **Visualization:** Animated Bessel function curves J_k(m) as m varies, spectrum update with sideband highlighting
- **Custom Viewer:** YES (Bessel function overlay panel)
- **Implementation Complexity:** Medium-High
- **Backend Estimate:** 8-10 hours (FM synthesis, Bessel functions, instantaneous frequency)
- **Frontend Estimate:** 10-12 hours

---

#### 34. Spectral Convolution and Modulation Effects
- **Lecture Source:** Lecture 19-2, Pages 15-20; Lecture 20
- **Learning Objective:** Visualize frequency-domain convolution through time-domain multiplication (modulation, windowing)
- **System Architecture:**
  - Input: Signal_type (sinusoid/AM/window/impulse_train/chirp), Signal_frequency (0.1-10), Modulation_type (AM/PM/pulse), Modulation_parameter, Signal_duration, Zoom_frequency
  - Outputs: Time-domain (x, m, product), individual frequency responses, convolution result, decomposition animation
- **Key Insight:** Multiplication in time → convolution in frequency; window convolution explains leakage
- **Visualization:** Three stacked time-domain waveforms, individual magnitude spectra, animated sliding convolution with area accumulation
- **Custom Viewer:** YES (convolution animation panel)
- **Implementation Complexity:** High
- **Backend Estimate:** 10-12 hours (FFT-based convolution, animation sequencing)
- **Frontend Estimate:** 12-14 hours

---

#### 35. Filtering Cascade and Frequency Response Chain
- **Lecture Source:** Lecture 20, Pages 1-18
- **Learning Objective:** Develop understanding of cascade system behavior through frequency response multiplication and phase addition
- **System Architecture:**
  - Input: Cascade_stages (1-4), per-stage type (LP/HP/BP/notch), per-stage cutoff_freq, per-stage Q_factor, Input_signal, Frequency_scale
  - Outputs: Individual Bode plots, cascade magnitude (product in dB), cascade phase (sum), time-domain I/O, pole-zero diagram, frequency zoom controls
- **Key Principle:** Cascade magnitude (dB) = sum of individual magnitudes; phase (rad) = sum of phases
- **Visualization:** Filter block diagram (top), waveform comparison (middle), stacked Bode panels with toggleable traces, pole-zero superposition
- **Custom Viewer:** YES (filter block diagram + analysis dashboard)
- **Implementation Complexity:** High
- **Backend Estimate:** 10-12 hours (cascade TF computation, pole/zero tracking)
- **Frontend Estimate:** 12-14 hours

---

#### 36. CD Audio Pipeline
- **Lecture Source:** Lecture 25, Pages 136-31
- **Learning Objective:** Understand complete signal processing chain from analog to CD bitstream: anti-aliasing, oversampling, downsampling, quantization
- **System Architecture:**
  - Input: Original_sample_rate (preset), Anti_aliasing_cutoff (18-22 kHz), Intermediate_sample_rate (slider), Quantization_bits (16-24), Test_signal, Animate_pipeline
  - Outputs: Original spectrum, anti-aliased spectrum, 176.4 kHz sampled spectrum, downsampled spectrum, quantized waveform, quality metrics (SNR/THD/Nyquist_margin)
- **Key Takeaway:** 44.1 kHz chosen because Nyquist = 22.05 kHz > 20 kHz (human hearing); 16-bit ~ 96 dB SNR (sufficient)
- **Visualization:** Five-panel story-driven layout: orignal → anti-aliased → oversampled → downsampled → quantized; each with spectrum and time-domain views
- **Custom Viewer:** YES (multi-stage pipeline visualization with annotations)
- **Implementation Complexity:** High
- **Backend Estimate:** 12-14 hours (full pipeline implementation, filter design, downsampling)
- **Frontend Estimate:** 14-16 hours (story-driven narrative UI)
- **Notes:** Capstone simulation integrating sampling, filtering, quantization concepts

---

---

## Dependency Map & Recommended Learning Path

### Prerequisite Hierarchy

```
Tier 1 (Foundation)
├── Signal Transformation Visualizer (1)
├── Leaky Tank Explorer (2)
├── Operator Algebra (3)
├── Feedback & Modes Explorer (4)
├── Fibonacci Mode Decomposition (5)
├── Complex Poles & Oscillations (6)
├── CT vs. DT Dual Evolution (7)
└── Impulse Response Decomposition (8)
         ↓ (All students must complete Tier 1 first)

Tier 2 (Extended Understanding)
├── Z Transform ROC (9) ← Requires: (7)
├── Inverse Z Transform (10) ← Requires: (9)
├── Laplace ROC (11) ← Requires: (8)
├── Numerical Approximation (12) ← Requires: (7)
├── Convolution Geometry (13) ← Requires: (8)
├── Pole-Zero Frequency Builder (14) ← Requires: (4), (8)
├── Eigenfunction Predictor (15) ← Requires: (8)
├── Bode Plot Constructor (16) ← Requires: (14)
├── High-Q Resonator (17) ← Requires: (14)
├── Feedback Gain-Bandwidth (18) ← Requires: (2), (14)
├── Crossover Distortion (19) ← Requires: (18)
├── Harmonic Series Convergence (20) ← Requires: (5)
└── Formant Tracking (21) ← Requires: (20), (audio synthesis)
         ↓ (Students should complete most of Tier 2 before Tier 3)

Tier 3 (Advanced & Specialized)
├── Periodic Extension Converter (22) ← Requires: (20)
├── DT Frequency on Unit Circle (23) ← Requires: (7), (14)
├── Spectral Window (24) ← Requires: (20), (13)
├── DT Aliasing (25) ← Requires: (7), (23)
├── Fourier Coefficient Designer (26) ← Requires: (20)
├── Filter Cascade (27) ← Requires: (16), (24)
├── Spectral Convolution (28) ← Requires: (13), (24)
├── Laplace→Fourier (29) ← Requires: (11), (14)
├── Nyquist Paradox (30) ← Requires: (7)
├── Quantization & Quality (31) ← Requires: (30)
├── Aliasing Mapper (32) ← Requires: (25)
├── FM Bandwidth (33) ← Requires: (16)
├── Dithering Artifacts (34) ← Requires: (31)
└── CD Audio Pipeline (35) ← Requires: (31), (27), (24)
```

### Suggested Weekly Sequencing (15-Week Course)

**Week 1-2:** Signal Transformation Visualizer, Leaky Tank
**Week 3:** Operator Algebra, Feedback & Modes
**Week 4:** Fibonacci Modes, Complex Poles
**Week 5:** CT vs. DT Dual Engine, Impulse Response
**Week 6:** Z Transform ROC, Inverse Z Transform
**Week 7:** Laplace ROC, Numerical Approximation
**Week 8:** Convolution Geometry, Pole-Zero Frequency Builder
**Week 9:** Eigenfunction Predictor, Bode Constructor
**Week 10:** High-Q Resonator, Feedback Gain-Bandwidth
**Week 11:** Crossover Distortion, Harmonic Series
**Week 12:** Formant Tracking, Periodic Extension
**Week 13:** DT Unit Circle, Spectral Window, DT Aliasing
**Week 14:** Filter Cascade, Spectral Convolution, Laplace→Fourier
**Week 15:** Nyquist Paradox, Quantization, FM Bandwidth, Dithering, CD Pipeline (review)

---

## Implementation Effort Estimates

### Summary Table by Simulation

| # | Simulation Name | Backend (hrs) | Frontend (hrs) | Custom Viewer | Total (hrs) | Difficulty |
|---|---|---|---|---|---|---|
| 1 | Signal Transformation Visualizer | 9 | 13 | YES | 22 | Medium |
| 2 | Leaky Tank Explorer | 7 | 11 | YES | 18 | Medium |
| 3 | Operator Algebra Explorer | 13 | 17 | YES | 30 | High |
| 4 | Feedback & Modes Explorer | 9 | 13 | YES | 22 | High |
| 5 | Fibonacci Mode Decomposition | 4 | 7 | NO | 11 | Medium |
| 6 | Complex Poles & Oscillations | 6 | 11 | YES | 17 | Medium |
| 7 | CT vs. DT Dual Engine | 11 | 15 | YES | 26 | High |
| 8 | Impulse Response Decomposition | 9 | 11 | YES | 20 | Medium-High |
| 9 | Z Transform ROC | 9 | 11 | YES | 20 | Medium |
| 10 | Inverse Z Transform | 11 | 13 | YES | 24 | Medium-High |
| 11 | Laplace ROC | 9 | 11 | YES | 20 | Medium |
| 12 | Numerical Approximation | 9 | 13 | YES | 22 | Medium-High |
| 13 | Convolution Geometry | 7 | 11 | YES | 18 | Medium |
| 14 | Pole-Zero Frequency Builder | 11 | 15 | YES | 26 | High |
| 15 | Eigenfunction Predictor | 7 | 11 | YES | 18 | Medium |
| 16 | Feedback Control Stabilization | 11 | 13 | YES | 24 | High |
| 17 | Bode Plot Constructor | 9 | 11 | YES | 20 | Medium |
| 18 | High-Q Resonator | 7 | 11 | YES | 18 | Medium |
| 19 | Feedback Gain-Bandwidth Tradeoff | 7 | 9 | YES | 16 | Low-Medium |
| 20 | Crossover Distortion Correction | 9 | 11 | YES | 20 | Medium |
| 21 | Harmonic Series Convergence | 5 | 7 | NO | 12 | Low-Medium |
| 22 | Formant Tracking & Vowel Synthesis | 11 | 13 | YES | 24 | Medium-High |
| 23 | Periodic Extension Converter | 7 | 9 | NO | 16 | Medium |
| 24 | DT Frequency on Unit Circle | 9 | 13 | YES | 22 | Medium-High |
| 25 | Spectral Window | 7 | 9 | NO | 16 | Medium |
| 26 | DT Aliasing via Wrapping | 9 | 11 | YES | 20 | Medium-High |
| 27 | Fourier Coefficient Designer | 7 | 11 | YES | 18 | Medium |
| 28 | Filter Cascade | 11 | 13 | YES | 24 | High |
| 29 | Spectral Convolution | 11 | 13 | YES | 24 | High |
| 30 | Laplace→Fourier Transform | 11 | 13 | YES | 24 | High |
| 31 | Nyquist Paradox Explorer | 5 | 7 | NO | 12 | Medium |
| 32 | Quantization & Perceptual Quality | 9 | 11 | YES | 20 | Medium-High |
| 33 | Aliasing Frequency Mapper | 3 | 6 | NO | 9 | Low-Medium |
| 34 | FM Bandwidth Evolution | 9 | 11 | NO | 20 | Medium-High |
| 35 | Dithering Artifact Explorer | 9 | 11 | YES | 20 | Medium |
| 36 | CD Audio Pipeline | 13 | 15 | YES | 28 | High |

### Team Composition Recommendations

**Tier 1 Execution (15-20 weeks):**
- 2x Backend Engineers (Python/NumPy/SciPy expertise)
- 2x Frontend Engineers (React/Plotly expertise)
- 1x Custom Visualization Specialist (Three.js, D3.js)
- 1x UI/UX Designer
- 1x QA Engineer

**Tier 2 Execution (18-24 weeks):**
- Increase backend team to 3 (specialized in audio processing for Formant simulation)
- Increase frontend to 3 (one dedicated to complex interactive components)
- Add Audio Engineer (Web Audio API, real-time synthesis)

**Tier 3 Execution (20-25 weeks):**
- Maintain team size but rotate specialization (some Tier 1 simulations may need refinement)

### Shared Infrastructure Requirements

**Backend:**
- NumPy/SciPy scientific computing stack (already core to project)
- SymPy for symbolic algebra (Operator Algebra, Inverse Z Transform)
- librosa for audio analysis (Formant, Quantization, CD Pipeline)
- SciPy.signal for advanced filtering (Numerical Approximation, CD Pipeline)

**Frontend:**
- Plotly.js 2.28+ for most frequency-domain plots (already in project)
- Three.js 0.182 for 3D visualizations (already available, use sparingly)
- Tone.js or Web Audio API for real-time audio (Formant, Quantization, FM, CD)
- D3.js for interactive pole/zero editors (Custom Visualization)

**Database/Persistence:**
- Not required; all simulations compute on-demand (stateless)

---

## Pedagogical Principles Applied Across All Simulations

1. **Visual-Mathematical Linking:** Every concept represented in multiple domains simultaneously (time, frequency, pole-zero, phase space)
2. **Interactive Parameter Discovery:** Sliders/draggable controls encourage "what-if" exploration
3. **Real-Time Feedback:** Parameter changes update all plots synchronously (no lag)
4. **Progressive Complexity:** Start with single parameter; unlock advanced controls upon completion
5. **Scaffolded Learning:** Simulations reference previous concepts; build cognitive scaffolds
6. **Physical Grounding:** Abstract mathematics connected to real systems (tanks, springs, audio, radio)
7. **Failure Modes Highlighted:** Stability boundaries, aliasing artifacts, distortion reduction clearly marked
8. **Numerical Verification:** Algebraic solutions checked against simulation results (builds trust)

---

## Risk Mitigation & Known Challenges

### Technical Risks
- **3D Rendering Performance:** Three.js 3D surfaces (Laplace ROC, s-plane magnitude) may stutter on low-end devices. **Mitigation:** Implement fallback 2D heatmap visualization; optimize mesh resolution.
- **Audio Playback Latency:** Web Audio API cannot guarantee sub-100ms latency. **Mitigation:** Pre-render and cache audio buffers; provide "play/pause" controls with progress indicator.
- **Large FFT Computations:** Real-time FFT for high-resolution spectrograms may block UI thread. **Mitigation:** Use Web Workers for FFT; implement downsampling for preview.
- **Symbolic Algebra Parsing:** SymPy parsing (Operator Algebra) may timeout on complex expressions. **Mitigation:** Provide regex-based pre-processing; add expression length limit; pre-compile common forms.

### Pedagogical Risks
- **Overload:** Students with weak prerequisites may struggle with Tier 1 simulations. **Mitigation:** Provide "guided mode" tutorials; optional prerequisite review modules.
- **Over-Reliance on Visualization:** Students may develop intuition without understanding algebra. **Mitigation:** Require problem-set exercises linking simulation outputs to hand calculations.
- **Engagement Dropoff:** Novel simulations lose impact after repeated use. **Mitigation:** Implement difficulty progression, achievements/badges, leaderboards for control loop game.

### Maintenance & Scalability
- **Version Control:** Maintain separate "main" branch for stable simulations; "dev" branch for new features. Automated testing for numerical correctness.
- **Documentation:** API docs for backend endpoints; component storybook for frontend reusable components.
- **Extensibility:** Design simulator interface to accept plugin-like custom solvers; enable easy addition of new systems without core refactoring.

---

## Conclusion

This master catalog represents a comprehensive, pedagogically-sound collection of 36 interactive simulations spanning the full scope of MIT 6.003 Signals & Systems. The **Tier 1 foundation** (10 simulations) should be prioritized for immediate implementation, as they establish the conceptual bedrock upon which all advanced topics depend.

By phased deployment across three tiers, the project achieves:
- **Immediate Impact:** Core concepts (Tier 1) deployed within 4-5 months
- **Continued Growth:** Extended understanding (Tier 2) deployed within 8-10 months
- **Complete Coverage:** Advanced topics (Tier 3) deployed within 12-15 months

**Total Project Timeline:** 15 weeks (Tier 1), 18 weeks (Tier 2), 20 weeks (Tier 3) = **~1 year to full implementation** with modest team (5-6 FTE).

**Expected Learning Outcome:** Students completing this curriculum will achieve intuitive mastery of signals & systems through **visual discovery**, **interactive exploration**, and **real-time feedback**—transforming abstract mathematics into visceral understanding.
