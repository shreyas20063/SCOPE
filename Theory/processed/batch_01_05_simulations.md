# MIT 6.003 Signals & Systems: Simulation Ideas from Lectures 1-5

Generated from Lectures 1-5 lecture notes. Focus on pedagogical innovation and visual intuition.

---

## Lecture 1: Signals and Systems (Abstraction & Fundamentals)

### Simulation 1: Signal Transformation Visualizer
**Lecture Source:** Lecture 1, Pages 1-37

**Learning Objective**
Develop intuitive understanding of signal operations (scaling, time-shifting, time-scaling) by simultaneously viewing the mathematical transformation and its effect on diverse real-world signal types.

**Theoretical Foundation**
- Time-domain signal operations: $x(t) \to y(t) = Ax(b(t - t_0))$
- Scaling: vertical ($A$) and horizontal ($1/b$) effects
- Time-shift linearity: $x(t - t_0)$ shifts right, $x(t + t_0)$ shifts left
- Multi-domain representation: CT vs. DT; signals as mathematical functions

**System Architecture**

**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|-----------------|------------|
| signal_type | {sine, speech, image, tank_inflow} | Which signal to transform | dropdown |
| amplitude | 0.1 to 3.0 | Vertical scaling factor | slider |
| time_stretch | 0.5 to 2.0 | Horizontal compression ($1/b$) | slider |
| time_shift | -5 to 5 (s/samples) | Delay or advance | slider |
| operation_sequence | {none, scale→shift, shift→scale, scale+shift} | Order of operations | radio |
| domain | {continuous, discrete} | CT or DT representation | toggle |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|---|---------|
| Original signal | Blue waveform + parametric plot | Reference ground truth |
| Transformed signal | Red waveform, overlaid or stacked | Direct visual comparison |
| Transformation matrix | 2D grid showing (t_old, t_new) mapping | Explain *why* shape changes |
| Speech spectrogram (if speech) | Time-frequency heatmap before/after | Reveal hidden structure |
| Image (if image) | 2D grid, transformations visible spatially | Extend abstraction to 2D |
| Operation log | Step-by-step list of transforms applied | Show commutativity violations |

**Visualization Strategy**

Core "aha moments":
1. **Commutative vs. non-commutative:** Scale then shift produces different result than shift then scale. Animated comparison shows why (area under curve changes vs. doesn't).
2. **Time-stretch intuition:** Slider for $1/b$ reveals that smaller $b$ = more compression = faster playback. Real-time audio pitch shift for speech input.
3. **2D signal insight:** Loading an image (e.g., grayscale photograph) and applying transformations shows how scaling and shifting apply to spatial dimensions—bridges to image processing.
4. **Signal invariants:** Highlight properties that *don't* change (e.g., sum of absolute values for $|A|$ scaling, causality for time-shift).

**Implementation Notes**

**Complexity:** Medium
- Requires real-time plotting of two overlaid signals; need responsive sliders.
- Speech input: pre-computed spectrograms (fast) or librosa.js (slower, but doable).
- Image support: canvas-based 2D visualization, NumPy operations trivial.

**Key Algorithms:**
- CT: interpolation-based evaluation; DT: direct indexing.
- Fast commutative check: apply both orderings, compare L2 distance.
- Spectrogram: STFT via NumPy, then display as Plotly heatmap.

**Dependencies:**
- Backend: NumPy, SciPy (resampling), librosa (optional, for speech).
- Frontend: Plotly (dual-axis plots), canvas (2D image), Plotly heatmap.

**Extension Ideas**
- **Beginner:** Add a "guess the transformation" quiz mode. Show original and transformed; user adjusts sliders to match.
- **Advanced:** Multi-signal operations: $y(t) = A_1 x_1(t) + A_2 x_2(t)$. Explore linearity.
- **Real-world:** Load audio file, apply time-stretch, play back (time-warping via librosa's phase vocoder).

---

### Simulation 2: Leaky Tank / RC Circuit Interactive Explorer
**Lecture Source:** Lecture 1, Pages 25-37

**Learning Objective**
Build intuition for first-order linear differential equations and time constants through direct physical intuition: watching water drain from tanks or capacitors charging.

**Theoretical Foundation**
$$\frac{dr_1}{dt} = \frac{r_0(t) - r_1(t)}{\tau}$$
where $\tau$ is the time constant, $r_1(t)$ is leak rate, $r_0(t)$ is inflow.

Solution for constant inflow: $r_1(t) = r_0(1 - e^{-t/\tau})$

**System Architecture**

**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|-----------------|------------|
| tank_type | {leaky_tank, RC_circuit, thermal_system} | Physical system | dropdown |
| hole_size | 1 (small) to 10 (large) | Hole area → inverse $\tau$ | slider |
| tank_height | 0.5 to 2.0 m | Tank scale | slider |
| inflow_rate | 0 to 1.0 m³/s | $r_0(t)$ profile | function selector |
| inflow_profile | {constant, pulse, ramp, sine} | Time-varying input | dropdown |
| simulation_speed | 0.1 to 3.0x | Playback speed | slider |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|---|---------|
| Tank height over time | Animated 3D tank + time-domain plot | Intuitive physical behavior |
| Leak rate vs. inflow | Stacked area chart or difference plot | Show approach to equilibrium |
| Phase portrait | $(h_1, \dot{h}_1)$ plot | Reveal exponential convergence |
| Time constant τ | Highlighted on time axis (63% mark) | Quantify system speed |
| Waterfall effect (optional) | Animated particles showing water trajectory | Extreme visual feedback |

**Visualization Strategy**

Core "aha moments":
1. **Time constant discovery:** Slider for hole size instantly adjusts response speed. Students see $\tau \propto 1/\text{hole\_size}$.
2. **Exponential approach:** Phase portrait clearly shows curvature; approaching equilibrium exponentially, not linearly.
3. **Input-output lag:** Pulse input reveals system cannot instantly respond; there's always a delay proportional to $\tau$.
4. **System ubiquity:** Switch between leaky tank, RC circuit, and thermal system; equations identical, just relabel variables.

**Implementation Notes**

**Complexity:** Medium
- ODE integration (scipy.integrate.odeint) is simple.
- 3D tank rendering: Three.js or Plotly 3D scatter (slower but easier).
- Phase portrait: standard 2D Plotly line plot.

**Key Algorithms:**
- Solve leaky tank ODE: $\frac{dh}{dt} = \frac{1}{A}(r_0 - r_1)$, where $r_1 = h/R$ (resistance analogy).
- Compute $\tau = RC$ for each parameter set.
- Phase portrait: parametric $(h, \dot{h})$ plot from solution.

**Dependencies:**
- Backend: NumPy, SciPy (odeint), Matplotlib (if batch plotting).
- Frontend: Plotly 3D or Three.js (tank rendering), Plotly line plots.

**Extension Ideas**
- **Beginner:** Prediction game: "What height will tank reach if hole size is X and inflow is Y?" Real-time feedback.
- **Advanced:** Coupled tanks (Lecture 1, tanks system): two leaky tanks with flow between them. Explore modal decomposition.
- **Real-world:** Show thermal RC response of a building: outdoor temperature input, indoor response. Adjust insulation (R) and heat capacity (C).

---

## Lecture 2: Discrete-Time Systems

### Simulation 1: Operator Algebra Block Diagram Equivalence Explorer
**Lecture Source:** Lecture 2, Pages 4-57

**Learning Objective**
Develop algebraic fluency with discrete-time operator notation (R = right-shift) by visually demonstrating that algebraically equivalent operator expressions yield identical input-output behavior when systems are at rest.

**Theoretical Foundation**
- Right-shift operator: $Y = RX \iff y[n] = x[n-1]$.
- Operator algebra: $(1-R)^2 = 1 - 2R + R^2$; multiplication corresponds to cascade; addition corresponds to parallel.
- Causality: acyclic diagrams are causal; cyclic diagrams have feedback.
- Commutativity, distributivity, associativity apply to operators (under initial rest condition).

**System Architecture**

**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|-----------------|------------|
| operator_expr | text | e.g., "(1-R)^2", "R(1-R)", "(1-0.5R)" | text input + parser |
| input_signal | {delta, step, ramp, custom_sequence} | Excitation | dropdown |
| display_mode | {block_diagram, operator_form, difference_eq, sequence} | Representation | tabs |
| canonical_form | {cascade, parallel, direct_1, direct_2} | Factorization style | radio |
| show_equivalence | {off, highlight_equal, show_alternatives} | Compare to algebraic form | checkbox |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|---|---------|
| Parsed block diagram | Interactive SVG with delay/adder/gain blocks | Concretize operator expression |
| Equivalent forms | Multiple algebraic expansions (cascade, parallel) | Show commutativity |
| Difference equation | Auto-derived from operator expression | Bridge to next representation |
| Step-by-step execution | Animated table of [n, x[n], y[n]] | Trace signal through system |
| Pole diagram | Zero-pole plot if factored | Predict stability/modes |
| Output waveform | Blue input, red output, sampled | Compare signals |

**Visualization Strategy**

Core "aha moments":
1. **Polynomial multiplication → cascade:** $(1-R)(1-R)$ expanded step-by-step, then shown as cascade of two delay-subtractors. Student sees why order doesn't matter.
2. **Partial fractions → parallel:** Complex operator expressions can be decomposed into simple geometric modes. Slider to blend contributions.
3. **Acyclic vs. cyclic:** Toggle feedback path on/off; acyclic gives finite-duration impulse response (FIR), cyclic gives infinite (IIR).
4. **Equivalence discovery:** Input two "different-looking" operators; system shows they're algebraically equivalent and produce identical outputs.

**Implementation Notes**

**Complexity:** High
- Requires symbolic parsing of operator expressions (SymPy or custom parser).
- Block diagram generation: SVG templating.
- Factorization and partial fractions: SymPy.
- Step-by-step execution: table rendering + animation.

**Key Algorithms:**
- Parse operator expression (e.g., "1 - R - R^2") → polynomial.
- Factor polynomial → find roots (poles).
- Generate block diagram from factored form.
- Simulate system: convolve input with impulse response, or solve recurrence.

**Dependencies:**
- Backend: SymPy (symbolic algebra), NumPy, SciPy.
- Frontend: Plotly, SVG (block diagram).

**Extension Ideas**
- **Beginner:** Pre-built library of common operators (delay, accumulator, differencer); student drags to canvas to build diagram.
- **Advanced:** Canonical realization forms (direct form I/II): show state variables, implement and compare computational efficiency.
- **Real-world:** Digital audio filters: students design lowpass filter using operator algebra, listen to filtered signal.

---

### Simulation 2: Feedback, Modes, and Stability Explorer
**Lecture Source:** Lecture 2, Pages 58-90

**Learning Objective**
Intuitively understand how feedback creates modes (poles) and determines stability, by tracing cyclic signal paths and watching fundamental modes govern the response.

**Theoretical Foundation**
- Feedback: presence of cyclic signal flow path.
- Poles: characterize fundamental modes. Pole value $p$ gives mode $p^n u[n]$.
- Stability: all poles must lie inside unit circle ($|p| < 1$ for DT).
- Geometric growth/decay: rate determined by pole magnitude.

**System Architecture**

**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|-----------------|------------|
| feedback_coeff | -1.5 to 1.5 | Pole location (for simple feedback) | slider |
| num_poles | 1 to 3 | System order | radio |
| pole_locations | complex (if 2nd order) | Poles in z-plane | interactive plot or sliders |
| input_type | {impulse, step, sine} | Excitation type | dropdown |
| show_cycles | {off, highlight, trace_animation} | Visualize cyclic paths | checkbox |
| show_modes | {off, fundamental_modes, mode_combination} | Show decomposition | checkbox |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|---|---------|
| Pole-zero diagram (z-plane) | Interactive plot; poles as red X, zeros as blue O | Predict stability at a glance |
| Block diagram with feedback | SVG diagram with cyclic path highlighted | Show structure visually |
| Fundamental modes | One plot per pole; $p^n u[n]$ for each | Decompose response |
| Output as superposition | Stacked area chart combining modes | Show weighted sum |
| Time-domain response | Single trace showing actual output | Verify superposition matches |
| Stability region | Shaded unit circle in z-plane | Instant visual feedback |

**Visualization Strategy**

Core "aha moments":
1. **Pole crossing unit circle:** Drag a pole in z-plane; watch output switch from convergent to divergent. Magical moment of understanding stability.
2. **Complex pole pairs:** Real second-order poles give exponential decay; complex conjugate poles give oscillatory decay. Slider to morph between them.
3. **Mode superposition:** Decompose output into constituent modes; student sees that one pole = one exponential, two poles = two interacting exponentials.
4. **Cycle tracing:** Animate the feedback loop; show how each cycle adds another term to the infinite sum $(1 + pA + p^2A^2 + \ldots)$.

**Implementation Notes**

**Complexity:** High
- Interactive z-plane with draggable poles requires custom SVG/canvas.
- ODE/recurrence solver for each pole configuration.
- Partial fractions decomposition.
- Animation of cycle tracing.

**Key Algorithms:**
- Compute system response as sum of modes: $y[n] = \sum c_i p_i^n u[n]$.
- Use partial fractions to find $c_i$.
- Animate pole motion in z-plane; update response in real-time.
- Check stability: all poles inside unit circle?

**Dependencies:**
- Backend: NumPy, SciPy, SymPy.
- Frontend: Custom D3.js or Plotly for interactive z-plane, Plotly for mode plots.

**Extension Ideas**
- **Beginner:** Pre-set stable/unstable pole locations; student clicks to see response.
- **Advanced:** Design feedback controller: place poles at desired locations to meet performance specs.
- **Real-world:** Population dynamics (Fibonacci): poles determine long-term growth rate; students predict population growth from pole locations.

---

## Lecture 3: Feedback, Poles, and Fundamental Modes

### Simulation 1: Fibonacci & Golden Ratio Mode Decomposition
**Lecture Source:** Lecture 3, Pages 1-47

**Learning Objective**
Understand how system poles decompose the unit-sample response into fundamental modes, using the famous Fibonacci sequence as the central example to reveal the golden ratio's mathematical inevitability.

**Theoretical Foundation**
Fibonacci system: $y[n] = x[n] + y[n-1] + y[n-2]$

System functional: $H(R) = \frac{1}{1 - R - R^2}$

Poles at golden ratio $\phi = \frac{1+\sqrt{5}}{2} \approx 1.618$ and $-1/\phi \approx -0.618$.

Unit-sample response: $h[n] = \frac{1}{\sqrt{5}}\left(\phi^n - (-1/\phi)^n\right)$ for $n \geq 0$.

**System Architecture**

**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|-----------------|------------|
| sequence_length | 5 to 30 | Number of Fibonacci terms to compute | slider |
| show_mode_1 | {off, φ^n, φ^n scaled} | Dominant exponential mode | toggle + slider (amplitude) |
| show_mode_2 | {off, (-1/φ)^n, (-1/φ)^n scaled} | Oscillating, decaying mode | toggle + slider |
| show_ratio | {off, h[n]/φ^n} | Ratio of actual to dominant | checkbox |
| input_signal | {impulse, step} | Excitation | radio |
| animation_speed | 0.5 to 2.0x | Playback rate | slider |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|---|---------|
| Fibonacci sequence | Animated table [n, F[n], φ^n, (-1/φ)^n] | Show numerical growth |
| Pole-zero plot (z-plane) | Two poles marked; golden ratio highlighted | Explain *why* Fibonacci grows |
| Mode 1 (φ^n) | Red curve, exponential | Dominant behavior for large n |
| Mode 2 (oscillating) | Blue curve, decaying with sign flip | Subtle, gets tiny fast |
| Sum of modes | Magenta curve overlaid on actual h[n] | Verify decomposition |
| Binet's formula vs. recurrence | Dual computation, side-by-side results | Alternative perspective |
| Phase portrait | (h[n], h[n+1]) plot revealing spiral | Geometric understanding |

**Visualization Strategy**

Core "aha moments":
1. **Golden ratio appearance:** Student computed Fibonacci recursively; suddenly sees $\phi$ emerge from the formula. *Why does nature love this number?*
2. **Mode dominance:** The $(-1/\phi)^n$ term decays so fast (magnitude < 0.618) that for $n > 20$, it's invisible. But for small $n$, it causes the oscillation vs. smooth growth.
3. **Binet's formula vs. recurrence:** Two completely different approaches yield identical sequences. Philosophical moment: systems have multiple valid representations.
4. **Phase spiral:** Plotting consecutive Fibonacci pairs reveals a logarithmic spiral in state space, asymptotic to the golden ratio direction.

**Implementation Notes**

**Complexity:** Medium-High
- Integer arithmetic for Fibonacci (high precision needed for $n > 30$).
- Floating-point for $\phi$ and modes; careful about numerical stability.
- Phase portrait: parametric plot of $(h[n], h[n+1])$.

**Key Algorithms:**
- Fibonacci: either recurrence or explicit Binet formula.
- Mode decomposition: coefficients from partial fractions.
- Phase portrait: compute successive pairs, plot on 2D plane.

**Dependencies:**
- Backend: NumPy (high-precision arithmetic optional), SciPy.
- Frontend: Plotly (line + area plots, 2D phase portrait).

**Extension Ideas**
- **Beginner:** Predict Fibonacci value at $n=30$ by visual extrapolation of $\phi^n$ curve.
- **Advanced:** Generalized Fibonacci: change feedback coefficients, explore poles for different initial conditions.
- **Real-world:** Plant spiral phyllotaxis, shell spirals, galaxy spirals—all governed by ratio close to golden ratio.

---

### Simulation 2: Complex Poles & Oscillatory Modes
**Lecture Source:** Lecture 3, Pages 38-47

**Learning Objective**
Visualize complex conjugate poles and their fundamental modes (oscillating, decaying exponentials), and understand how they combine to produce real-valued outputs.

**Theoretical Foundation**
System: $y[n] = x[n] + y[n-1] - y[n-2]$

Poles at $e^{\pm j\pi/3}$ (complex conjugates on unit circle → marginally stable).

Fundamental modes: $e^{jn\pi/3}$ (cosine + jj sine) and $e^{-jn\pi/3}$ (cosine - jj sine). Weighted sum is real.

**System Architecture**

**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|-----------------|------------|
| pole_magnitude | 0.3 to 1.2 | Radius $r$ in z-plane | slider |
| pole_frequency | 0 to π | Angle $\Omega$ in z-plane | slider (display as rad or Hz) |
| input_type | {impulse, step, cosine} | Excitation | dropdown |
| show_complex_modes | {off, real_imag, magnitude_phase} | Mode representation | radio |
| show_real_output | {off, superposition} | Real-valued combination | checkbox |
| animation_mode | {trace_poles, rotate_modes, show_spiral} | Visual mode | radio |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|---|---------|
| Pole-zero diagram (z-plane) | Complex plane; poles as red X on unit circle (or inside) | Show pole position |
| Mode 1 (complex exponential) | Real and imaginary parts as separate traces | Cosine/sine oscillation at $\Omega$ |
| Mode 2 (conjugate) | Real and imaginary parts (conjugate of mode 1) | Same frequency, opposite imaginary |
| Weighted sum | Red curve as superposition of modes | Real-valued output emerges |
| Magnitude envelope | Dashed line showing $r^n$ decay/growth | Stability envelope |
| Frequency content | Magnitude spectrum showing peak at $\Omega$ | Frequency interpretation |

**Visualization Strategy**

Core "aha moments":
1. **Unit circle stability:** Drag pole on unit circle; output oscillates at constant amplitude. Inside circle → decays. Outside → diverges.
2. **Conjugate necessity:** Start with one pole; output has imaginary part. Add conjugate pole; imaginary parts cancel, output is real.
3. **Frequency from angle:** Pole angle directly encodes oscillation frequency. Slider for angle instantly changes oscillation rate.
4. **Spiral in phase space:** Plot complex mode over time as point rotating on circle, decaying; as 3D helix in $(n, \text{Re}, \text{Im})$; shows both oscillation and decay.

**Implementation Notes**

**Complexity:** Medium
- Complex-valued arithmetic and visualization (2D scatter for real/imag parts).
- Rotation animation: update pole angle in real-time, recompute response.
- Phase portrait: 3D plot or 2D time-varying spiral.

**Key Algorithms:**
- Poles at $r e^{j\Omega}$; modes $r^n e^{jn\Omega}$ and conjugate.
- Real output from weighted sum.
- Magnitude spectrum from FFT or direct formula.

**Dependencies:**
- Backend: NumPy (complex arithmetic), SciPy.
- Frontend: Plotly 3D (helix) or custom 2D (real/imag), interactive z-plane.

**Extension Ideas**
- **Beginner:** Match visual oscillation to frequency slider value; quiz mode.
- **Advanced:** Higher-order systems with multiple complex pole pairs; visualize beat patterns.
- **Real-world:** Underdamped mechanical oscillator (mass-spring-damper): pole position → natural frequency and damping ratio.

---

## Lecture 4: Continuous-Time Systems

### Simulation 1: CT vs. DT Dual Evolution Engine
**Lecture Source:** Lecture 4, Pages 1-50

**Learning Objective**
Develop parallel intuition for continuous-time and discrete-time systems by running equivalent systems side-by-side, revealing similarities (poles determine modes) and differences (integration vs. delays, exponential vs. geometric growth).

**Theoretical Foundation**

**CT system:** $\dot{y}(t) = x(t) + py(t)$ with operator $A$ (integrate), impulse response $e^{pt}u(t)$.

**DT system:** $y[n] = x[n] + py[n-1]$ with operator $R$ (right-shift), impulse response $p^n u[n]$.

Mapping: $A \leftrightarrow R$, $s \leftrightarrow z$ (via $s = \ln(z) / T$ or $z = e^{sT}$).

**System Architecture**

**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|-----------------|------------|
| pole_value_p | -2 to 2 (shared) | Pole location (CT and DT) | slider |
| sampling_period_T | 0.01 to 1.0 s | DT sample interval | slider |
| input_signal | {impulse, step, ramp, sine} | Excitation (both domains) | dropdown |
| simulation_time | 1 to 20 s | Duration | slider |
| show_discretization | {off, points, reconstruction} | DT samples overlaid on CT | checkbox |
| show_alignment | {off, pole_position, mode_comparison} | Highlight correspondences | radio |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|---|---------|
| CT response | Smooth blue curve | Continuous evolution |
| DT response (overlaid) | Red points/staircase | Discrete snapshots |
| Pole location (CT) | s-plane diagram; pole at real(p) | Left/right half-plane = stable/unstable |
| Pole location (DT) | z-plane diagram; equivalent pole | Inside/outside unit circle = stable/unstable |
| Fundamental mode (CT) | $e^{pt}$ envelope | Exponential |
| Fundamental mode (DT) | $p^n$ discrete points | Geometric |
| Sampling effect | Aliased frequency if DT undersamples | Nyquist violation visible |
| Phase portrait | $(y, \dot{y})$ for CT, $(y[n], y[n-1])$ for DT | Reveal system structure |

**Visualization Strategy**

Core "aha moments":
1. **Exponential vs. geometric:** CT has smooth exponential curves; DT has discrete jumps following geometric sequence. Same pole value, different *flavors* of growth/decay.
2. **Sampling introduces new poles:** DT pole at $z = e^{pT}$. If $T$ changes, DT pole moves along ray from origin; pole always on ray from $p$ in CT.
3. **Stability boundary shift:** CT stability (Re$(p) < 0$) ≠ DT stability ($|z| < 1$). Choose $T$ small enough, DT can be stable when CT is unstable (and vice versa).
4. **Under-sampling catastrophe:** Set $T$ too large; DT response oscillates wildly (aliasing). Reduce $T$; aliasing disappears.

**Implementation Notes**

**Complexity:** High
- Dual ODE/recurrence solver.
- Real-time z-plane and s-plane updates.
- Sampling visualization and reconstruction.

**Key Algorithms:**
- CT: scipy.integrate.odeint for $\dot{y} = x + py$.
- DT: recurrence $y[n] = x[n] + py[n-1]$.
- Mapping: $z = e^{pT}$, $p = \ln(z)/T$.

**Dependencies:**
- Backend: NumPy, SciPy.
- Frontend: Plotly (dual plots + dual pole diagrams), D3.js for interactive z/s-planes.

**Extension Ideas**
- **Beginner:** Fixed $T$; adjust pole slider; see CT smooth, DT jumpy, but same fundamental behavior.
- **Advanced:** Second-order systems (mass-spring) in both domains; compare underdamped CT vs. underdamped DT.
- **Real-world:** Digital controller design: must choose sampling period to match CT plant dynamics without aliasing.

---

### Simulation 2: Impulse Response Decomposition & Modal Reconstruction
**Lecture Source:** Lecture 4, Pages 41-50 (Mass-Spring System Example)

**Learning Objective**
Understand how the impulse response of a CT system emerges from its poles (fundamental modes) by visually decomposing and reconstructing the response as a weighted sum of exponential (real poles) or oscillating exponential (complex poles) terms.

**Theoretical Foundation**

**Mass-spring system:**
$$M\ddot{y} = K(x - y) \implies \ddot{y} + \frac{K}{M}y = \frac{K}{M}x$$

Poles at $\pm j\omega_0$ where $\omega_0 = \sqrt{K/M}$ (imaginary axis in s-plane, marginally stable).

Impulse response: $h(t) = \frac{\omega_0}{1} \sin(\omega_0 t) u(t)$ (pure oscillation, no decay).

**System Architecture**

**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|-----------------|------------|
| mass_M | 0.1 to 5.0 kg | Mass | slider |
| spring_K | 1 to 100 N/m | Spring constant | slider |
| damping_B | 0 to 10 N·s/m | Damping coefficient (if enabled) | slider |
| system_type | {undamped, underdamped, critically_damped, overdamped} | Pole location type | radio |
| show_poles | {off, on_s_plane} | Pole location | checkbox |
| show_modes | {off, individual_modes, cumulative} | Decompose into exponentials/oscillations | tabs |
| num_modes_displayed | 1 to 4 | How many modes to show | slider |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|---|---------|
| s-plane pole diagram | Poles and zero locations | Predict impulse response shape |
| Pole locus (damping sweep) | Animated path as damping increases | Show transition through stability types |
| Impulse response h(t) | Main black trace | Ground truth |
| Mode 1 (real or oscillatory) | Colored trace with envelope | First fundamental mode |
| Mode 2 (conjugate or decay) | Separate colored trace | Second fundamental mode |
| Weighted sum | Dashed overlay, reconstructs h(t) | Verify superposition |
| Phase portrait | $(y, \dot{y})$ trajectory | Show spiral convergence to origin |
| Energy plot | Kinetic + potential, conserved (undamped) or dissipated | Physical insight |

**Visualization Strategy**

Core "aha moments":
1. **Undamped oscillation discovery:** Mass-spring with no damping gives pure imaginary poles on jω axis. Impulse response oscillates forever (no decay).
2. **Adding damping:** Move poles left of imaginary axis; oscillation now decays exponentially. Slider controls damping → visually adjusts pole position.
3. **Critical damping:** Find the threshold where poles become a repeated real pole. Response is no longer oscillatory but asymptotically approaches zero.
4. **Energy conservation → pole location:** Undamped (energy conserved) → poles on imaginary axis. Damped (energy dissipates) → poles in left half-plane.

**Implementation Notes**

**Complexity:** Medium-High
- ODE solver for mass-spring-damper.
- Partial fractions decomposition to extract modes (automated via SymPy).
- Phase portrait plotting.

**Key Algorithms:**
- Solve $M\ddot{y} + B\dot{y} + Ky = \delta(t)$ using Laplace transform or ODE integration.
- Extract poles from characteristic equation $Ms^2 + Bs + K = 0$.
- Partial fractions: $H(s) = \frac{c_1}{s - p_1} + \frac{c_2}{s - p_2}$ (or complex conjugate form).
- Reconstruct: $h(t) = c_1 e^{p_1 t} + c_2 e^{p_2 t}$.

**Dependencies:**
- Backend: NumPy, SciPy, SymPy (partial fractions).
- Frontend: Plotly (multi-line plots with envelopes), D3.js for s-plane.

**Extension Ideas**
- **Beginner:** Predict oscillation frequency from $\sqrt{K/M}$; verify with slider.
- **Advanced:** Second-order DT systems (sampled mass-spring); compare CT vs. DT response.
- **Real-world:** Vehicle suspension tuning: adjust K and B (spring stiffness, shock damping) to achieve desired response (fast settling, no overshoot).

---

## Lecture 5: Z Transform

### Simulation 1: Z Transform Region of Convergence (ROC) & Causality Explorer
**Lecture Source:** Lecture 5, Pages 1-42

**Learning Objective**
Understand that the same rational Z transform can correspond to multiple different time-domain signals, distinguished solely by the region of convergence (ROC), and that ROC determines causality and stability.

**Theoretical Foundation**

Z transform: $X(z) = \sum_{n=-\infty}^{\infty} x[n] z^{-n}$

ROC is delimited by circles passing through poles in z-plane.

**Causality:** ROC is exterior of a circle (includes $|z| = \infty$).

**Stability:** ROC includes unit circle ($|z| = 1$).

Example: $X(z) = \frac{z}{z - \alpha}$ has two interpretations:
- ROC: $|z| > |\alpha|$ → $x[n] = \alpha^n u[n]$ (causal, right-sided).
- ROC: $|z| < |\alpha|$ → $x[n] = -\alpha^n u[-n-1]$ (anti-causal, left-sided).

**System Architecture**

**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|---|---|
| transfer_function | text | e.g., "z/(z-0.5)", "z/(z-0.8)/(z-0.3)" | text input + parser |
| roc_region | text or picker | e.g., "\|z\| > 0.5" or "\|z\| < 0.8" | radio or manual text |
| pole_mode | {auto_detect, manual_draw} | Let system find poles or draw them | toggle |
| num_poles | 1 to 3 | System order | slider |
| show_causality | {off, highlight_causal, both} | Visual feedback | checkbox |
| show_stability | {off, highlight_stable, both} | Stable ROC highlight | checkbox |

**Output Observables:**
| Observable | Visualization | Purpose |
|-----------|---|---------|
| z-plane pole/zero plot | Poles (red X), zeros (blue O) | Show locations |
| ROC region | Shaded area in z-plane | Delimit causality/stability |
| Possible ROCs | Multiple circles/regions overlaid lightly | Show all valid choices |
| Time-domain signal #1 | Table + plot of causal (right-sided) signal | One interpretation |
| Time-domain signal #2 | Table + plot of anti-causal (left-sided) signal | Another interpretation |
| Causality label | "CAUSAL" or "ANTI-CAUSAL" | Clear text feedback |
| Stability check | "STABLE" (ROC includes unit circle) or "UNSTABLE" | Pass/fail indicator |
| Convergence annotation | Colored shading on time-domain plot | Show where signal is nonzero |

**Visualization Strategy**

Core "aha moments":
1. **Multiple time-domain signals, one Z transform:** Parser accepts same $X(z)$ with different ROC; generates two completely different signals. Shocking and clarifying.
2. **ROC determines everything:** The algebraic form $X(z) = \frac{z}{z - 0.8}$ is ambiguous; only ROC specification resolves the ambiguity.
3. **Causality requirement:** Practical systems are typically causal (output doesn't depend on future input). ROC must extend to infinity.
4. **Stability requires unit circle:** System must be stable (bounded output for bounded input). ROC must include unit circle. Both conditions must hold for practical feedback systems.

**Implementation Notes**

**Complexity:** Medium
- Symbolic parsing of rational functions (SymPy).
- Pole/zero finding.
- ROC visualization (draw circles in z-plane).
- Signal generation from ROC and poles (inverse Z transform via partial fractions).

**Key Algorithms:**
- Parse rational function → extract numerator, denominator, find poles/zeros.
- Given ROC region, determine causality (extends to $\infty$?) and stability (includes unit circle?).
- Inverse Z transform: partial fractions + table lookup.

**Dependencies:**
- Backend: SymPy (symbolic), NumPy, SciPy.
- Frontend: Plotly (z-plane + time-domain plots), D3.js (interactive z-plane).

**Extension Ideas**
- **Beginner:** Pre-built Z transforms with multiple ROC choices; student selects ROC and guesses time-domain signal, gets feedback.
- **Advanced:** Cascade systems: given two systems with specified ROCs, predict cascade stability and causality.
- **Real-world:** IIR filter design: choose pole locations to achieve desired frequency response while maintaining stability and causality.

---

### Simulation 2: Inverse Z Transform Partial Fractions & Convolution Explorer
**Lecture Source:** Lecture 5, Pages 34-50

**Learning Objective**
Master the process of finding time-domain signals from Z transforms by partial fractions decomposition, recognizing standard table entries, and understanding convolution in the z-domain as multiplication.

**Theoretical Foundation**

**Partial fractions:**
$$X(z) = \frac{z}{(z-a)(z-b)} = \frac{A}{z-a} + \frac{B}{z-b}$$

**Standard Z transform pairs:**
- $\alpha^n u[n] \leftrightarrow \frac{z}{z - \alpha}$ (causal exponential).
- $n\alpha^n u[n] \leftrightarrow \frac{\alpha z}{(z-\alpha)^2}$ (multiplication by n property).
- $\delta[n] \leftrightarrow 1$.

**Convolution:** $x_1[n] * x_2[n] \leftrightarrow X_1(z) X_2(z)$.

**System Architecture**

**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|---|---|
| x1_func | text | Z transform (e.g., "z/(z-0.5)") | text input |
| x2_func | text | Second Z transform for convolution | text input |
| operation | {inverse_transform, convolution, cascade} | What to compute | radio |
| decomposition_method | {partial_fractions, power_series, table_lookup} | Inversion strategy | radio |
| show_steps | {off, abbreviated, detailed} | Solution verbosity | radio |
| num_terms_series | 5 to 30 | Number of terms for power series | slider |

**Output Observables:**
| Observable | Visualization | Purpose |
|-----------|---|---|
| Original Z transform | Mathematical expression | Reference |
| Poles/zeros | z-plane diagram | Identify for partial fractions |
| Partial fraction decomposition | Step-by-step algebra (if "detailed" mode) | Educational breakdown |
| Standard table entries | Color-coded partial fractions matched to table | Connect to known inverse transforms |
| Inverse signal x[n] | Table of samples [n, x[n]] | Time-domain result |
| Signal waveform | Stem plot of x[n] | Visualize signal |
| Power series (alternative) | Coefficients of $z^{-n}$ expansion | Direct inverse method |
| Convergence region | Shaded ROC in z-plane | Confirm causality |
| (For convolution) | Product Z transform + inverse | Combined operation |

**Visualization Strategy**

Core "aha moments":
1. **Partial fractions unlock standard forms:** Complex $X(z) = \frac{z^2}{(z-0.5)(z-0.8)}$ decomposes into sum of two known forms; inverse immediately obvious.
2. **Power series coefficient interpretation:** Expand $X(z) = \sum a_k z^{-k}$; coefficients ARE $x[n]$. Magical insight: Z transform is literally a generating function for the sequence.
3. **Convolution simplifies to multiplication:** Instead of convolving two sequences (tedious), multiply Z transforms (algebra), then invert. Huge simplification.
4. **Table lookup speed:** Most practical signals are linear combinations of standard forms. Student learns to *recognize* forms and instantly read off time-domain answer.

**Implementation Notes**

**Complexity:** Medium-High
- SymPy partial fractions decomposition.
- Inverse Z transform recognition (lookup table or formula).
- Power series expansion.
- Convolution multiplication.

**Key Algorithms:**
- Parse rational Z transform.
- Find poles/zeros.
- Partial fractions: solve linear system for residues.
- Recognize standard forms or apply inverse formulas.
- Power series: polynomial long division or series expansion.

**Dependencies:**
- Backend: SymPy, NumPy, SciPy.
- Frontend: Plotly (time-domain stem plots), MathJax or similar for step-by-step algebra display.

**Extension Ideas**
- **Beginner:** Provide Z transform; student selects from multiple-choice answers for time-domain signal.
- **Advanced:** Cascade of two systems: given $H_1(z)$ and $H_2(z)$, find overall impulse response by Z transform multiplication.
- **Real-world:** Digital filter frequency response: given filter Z transform, compute $H(e^{j\omega})$ by evaluating on unit circle; plot magnitude and phase response.

---

## Summary of Pedagogical Themes Across All Five Lectures

1. **Visual Correspondence:** Every representation (block diagram, difference equation, operator algebra, Z transform) is visualized and linked interactively.

2. **Pole-Centric Understanding:** Poles (fundamental modes) emerge as the unifying concept across DT, CT, and transform domains.

3. **Stability Criteria:** Regions of stability are highlighted geometrically (inside unit circle for DT, left half-plane for CT, ROC includes unit circle for Z transforms).

4. **Interactive Slider Exploration:** Students adjust parameters (feedback, pole location, damping, sampling rate) and instantly see consequences in time-domain, frequency-domain, and pole-zero plots.

5. **Real-World Grounding:** Each simulation has a physical analog (leaky tanks, mass-spring, population dynamics, audio filtering) to motivate the mathematics.

6. **Constructivist Learning:** Rather than "here is a formula," simulations encourage students to discover relationships by experimentation (e.g., dragging poles and watching stability boundaries).
