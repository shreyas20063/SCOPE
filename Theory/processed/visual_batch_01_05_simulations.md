# Novel Simulation Ideas from Lectures 01-05
## Visual Analysis & Pedagogical Innovation

Generated from comprehensive visual inspection of MIT 6.003 lecture slides showing diagrams, block diagrams, and interactive concepts suitable for dynamic simulation.

---

## Simulation 1: Leaky Tank Water Dynamics
### Lecture Source: Lecture 01, Pages 25-36
### Visual Cues Observed
The leaky tank system appears as a central visual metaphor throughout Lecture 01, with:
- Animated water level diagrams showing h(t) changing over time
- Visual comparison of four different tank configurations to understand time constants
- Progressive filling/draining behavior shown as curves rising/flattening
- Multiple tank sizes with identical hole sizes (illustrating how surface area affects flow)
- Clear cause-effect visualization: larger tanks = longer time constants

### Learning Objective
Develop intuition for first-order continuous-time systems through a tangible physical metaphor. Students learn how physical parameters (tank size, hole diameter, fluid viscosity) determine the rate of change through experiential manipulation and observation.

### Theoretical Foundation
The leaky tank obeys a first-order linear differential equation:
$$\frac{dh(t)}{dt} = \frac{1}{\tau}[r_0(t) - r_1(t)]$$

where:
- $r_0(t)$ = input flow rate
- $r_1(t) \propto h(t)$ = output flow rate (linear leakage)
- $\tau$ = time constant (dimensions: inverse frequency)

The solution to constant input $r_0(t) = R_0$ starting from empty tank:
$$h(t) = \tau R_0 (1 - e^{-t/\tau})$$

Time constant $\tau$ determines both settling time and initial slope: $\left.\frac{dh}{dt}\right|_{t=0} = \frac{R_0}{\tau}$

### System Architecture
**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|------------|
| Tank Area (A) | 0.5 - 5 m² | Cross-sectional area of tank | Slider with visual tank width |
| Hole Area (a) | 0.001 - 0.1 m² | Diameter of leak opening | Slider with visual hole size |
| Input Flow (r₀) | 0 - 2 m³/s | Pump rate into tank | Slider or step input button |
| Leak Coefficient (c) | 0.5 - 1.0 | Proportionality constant for leakage | Advanced slider |
| Initial Height (h₀) | 0 - 2 m | Starting water level | Slider |

**Output Observables:**
| Observable | Visualization | Purpose |
|-----------|----------------|---------|
| Water Height h(t) | Animated tank with rising/falling water level + Plotly time-series | Shows exponential approach to equilibrium |
| Time Constant τ | Numeric display + horizontal reference line at 63.2% | Teaches what τ means: time to reach 63% of final value |
| Output Flow r₁(t) | Separate plot showing proportional relationship to h(t) | Demonstrates feedback: higher tank → faster leak |
| Phase Portrait | h(t) vs dh/dt plot | Shows how velocity decreases as height increases |

### Visualization Strategy
**Main Panel Layout:**
- Left: Animated 2D side-view of tank filling with water (cyan/blue gradient). Hole shown at bottom with proportional leak stream visualization.
- Right: Three Plotly subplots arranged vertically:
  1. **h(t)** with exponential curve reaching steady state; shaded area under curve shows integral (volume accumulated)
  2. **r₁(t)** following h(t) with constant proportionality
  3. **Phase plane**: h vs dh/dt trajectory spiraling toward equilibrium point

**Interaction Flow:**
1. User adjusts A and hole size → see how tank shape changes on screen
2. User hits "Open Valve" button → r₀ jumps to selected value
3. Tank animates filling in real-time with curve updating live
4. Instant visual feedback: bigger hole = faster leak, larger tank = longer fill time
5. User can pause and examine point on curve to read h(t), dh/dt, τ numerically

**Key "Aha Moments":**
- Time constant τ is visually marked on both tank and curve; student sees that τ appears as a *distance* on the t-axis at which the exponential curve reaches 63%
- Comparison slider: put two tanks side-by-side with same input but different areas; watch one settle faster
- Phase plane loop back to origin visually demonstrates convergence

### Implementation Notes
**Complexity:** Low

**Key Algorithms:**
- Analytical solution: $h(t) = \tau r_0(1 - e^{-t/\tau})$ evaluated at high resolution
- Derivative: $\frac{dh}{dt} = r_0 e^{-t/\tau}$ for phase plane
- Equilibrium analysis: $h_{eq} = \tau r_0$ when $\frac{dh}{dt} = 0$
- Animation: interpolate h(t) over 0-5τ timespan to show natural settling

**Rendering:**
- Use SVG or Canvas for tank animation (water fills from bottom up, maintains aspect ratio)
- Plotly for curves with fixed x-axis range [0, 5τ] for consistency across different τ values
- Color change on water level: gradient from empty (gray) → full (bright cyan)

### Extension Ideas
**Beginner:**
- "Refill" scenario: when tank empties, toggle valve off/on to practice predicting when it reaches target height
- Dual-tank cascade: two leaky tanks in series; watch how the second tank's response lags and smooths the first
- Concrete example: relate tank area to real objects (swimming pool, bathtub, fountain basin)

**Advanced:**
- Input r₀(t) as arbitrary piecewise linear signal; predict h(t) analytically then check against simulation
- Nonlinear leakage: change leakage law to $r_1(t) \propto \sqrt{h(t)}$ (realistic for real-world orifices); see how equilibrium changes but exponential solution no longer holds
- Compare to RC circuit charging: superimpose voltage-charging curve alongside tank-filling curve to show mathematical equivalence

**Real-World Connections:**
- Battery charging dynamics (voltage vs. charge accumulation)
- Medication concentration in bloodstream (with constant intake from pills, metabolism as leak)
- Temperature equilibration: room heating with fixed power input and heat loss proportional to temperature difference
- Epidemic modeling: fraction of population infected follows similar curve

---

## Simulation 2: Step-by-Step Block Diagram Execution Animator
### Lecture Source: Lecture 02, Pages 9-17; Lecture 04, Pages 2-12
### Visual Cues Observed
Lectures 02 and 04 show extensive step-by-step animations of block diagrams:
- Frames labeled n=0, n=1, n=2, n=3, n=4 showing signal values propagating through delays
- Red numbers appear at node positions showing how a δ[n] pulse moves through the circuit
- Operator algebra equations displayed alongside the block diagram diagrams
- Visual distinction between "delay in DT" (box labeled with -1 or R) and "integrator in CT" (box with integral symbol)
- Check Yourself problems showing accumulator systems growing impulse responses

### Learning Objective
Transform the abstract notion of "operator" or "block diagram" into a *watchable, step-by-step execution* where students see exactly how signal values flow and combine at each time step. This is the critical bridge from intuitive block diagrams to mathematical operator expressions.

### Theoretical Foundation
For a discrete-time system represented as a block diagram with delay(s) and adder(s), the impulse response h[n] emerges from step-by-step evaluation of the difference equation:

Example (accumulator): $y[n] = x[n] + y[n-1]$

Starting from rest (y[-1] = 0), given input x[n] = δ[n]:
$$y[0] = 1 + 0 = 1$$
$$y[1] = 0 + 1 = 1$$
$$y[2] = 0 + 1 = 1$$
$$y[n] = \text{unit step } u[n]$$

Operator form: $(1 - R) Y = X$ → $Y = \frac{1}{1-R} X = (1 + R + R^2 + \ldots) X$

The series coefficients (1, 1, 1, ...) are the impulse response samples h[n].

### System Architecture
**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|------------|
| System Type | {Differencer, Accumulator, Custom} | Which block diagram to show | Dropdown selector |
| Input Signal | {δ[n], u[n], Custom} | Driving signal | Radio buttons or signal picker |
| Simulation Steps (N) | 1 - 15 | How many time steps to animate | Slider or number input |
| Animation Speed | 0.2 - 2.0 | Playback speed (steps/second) | Slider |
| Show Operator Form | True/False | Display (1-R)Y=X equation | Checkbox |
| Show Accumulating Impulse Response | True/False | Overlay h[n] on separate subplot | Checkbox |

**Output Observables:**
| Observable | Visualization | Purpose |
|-----------|----------------|---------|
| Block Diagram State | Animated nodes & edges with signal values | Shows input, intermediate, output values at current step |
| Node Value Tables | Text table: node names vs. values at each step | Precise numeric tracking across time |
| Impulse Response h[n] | Bar chart appended as steps execute | Visual accumulation of h[n] = (output when input=δ[n]) |
| Operator Expansion | LaTeX-rendered polynomial equation | Shows how step-by-step output builds the series |
| Phase Diagram | Optional: shows how poles determine h[n] growth | Advanced visualization |

### Visualization Strategy
**Main Display (left 60%):**
- Large, clean block diagram rendered with D3.js or custom Canvas
- Nodes (circles) labeled with signal names: x[n], y[n-1], y[n], etc.
- Edges (arrows) with signal flow directions
- Each node shows current numeric value in bold white text
- **Animation sequence:**
  1. At step n, highlight input node(s) showing x[n]
  2. Flash arrows moving input values through delays
  3. Highlight adder/multiplier nodes as they compute
  4. Show output node updating with y[n]
  5. Move forward to step n+1

**Right Panel (40%):**
- Top: A table showing [n | x[n] | y[n-1] | y[n] | ...] with current row highlighted
- Middle: Bar chart growing with h[n] samples; new bar appears and animates up at each step
- Bottom: Operator form equation updating in real-time (e.g., "Y = (1 + R + R² + ...) X")

**Color Scheme:**
- Input signals: bright cyan
- Delay memory (stored values): orange
- Adder/computation nodes: green with yellow highlight during computation
- Output: teal/bright blue
- Completed impulse response bars: purple gradient darkening over time

**Interaction:**
- Play/Pause button to control animation
- Step Forward / Step Backward buttons for manual exploration
- Slider to jump to specific time step
- Reset button to restart from n=0
- Change System dropdown → diagram updates immediately
- Toggle checkboxes → visualizations appear/disappear

### Implementation Notes
**Complexity:** Medium

**Key Algorithms:**
- Parse block diagram structure (delays, adders, gains) into dependency graph
- For each step n, compute node values in topological order (respecting feedback)
- Track y[n-1] in buffer for delay nodes; update buffer after each step
- Collect y[n] for each step → build h[n] array
- Compute operator polynomial coefficients from h[n] via polynomial fit or direct construction

**Rendering:**
- D3.js force-directed layout for automatic diagram positioning
- SVG text elements for node values, animated with CSS transitions for smooth value updates
- Plotly bar chart for h[n] with live update on each step
- MathJax or KaTeX for rendering LaTeX operator equations

**Pre-built Examples:**
1. y[n] = x[n] - x[n-1] (Differencer) → h[n] = (1, -1, 0, 0, ...)
2. y[n] = x[n] + y[n-1] (Accumulator) → h[n] = (1, 1, 1, 1, ...)
3. y[n] = x[n] + 0.7·y[n-1] (Geometric decay) → h[n] = (1, 0.7, 0.49, 0.343, ...)
4. y[n] = x[n] + 1.6·y[n-1] - 0.63·y[n-2] (Second-order) → h[n] = (1, 1.6, 1.6² - 0.63, ...)

### Extension Ideas
**Beginner:**
- Quiz mode: show a block diagram and ask students to predict h[n] before running animation
- Reverse quiz: give h[n] sequence and ask what block diagram produces it
- Comparison view: run two systems side-by-side with same input to see how poles affect response

**Advanced:**
- Allow user to draw custom block diagrams (drag-and-drop delays, adders, gains)
- Cascaded systems: connect two diagrams in series and watch composite h[n] emerge
- Feedback loop stability: adjust gain in a feedback path; watch h[n] for divergence vs. convergence (relate to pole magnitude)
- Continuous-time version: replace Delay box with Integrator (A operator); animate flow of area accumulation

**Real-World Connections:**
- Financial modeling: compound interest (accumulator with gain p = 1.05)
- Viral spread: SIR model where y[n] = infected count, feedback from recovered individuals
- Audio processing: implement common DSP filters (low-pass, high-pass) and see impulse responses
- Control systems: PID controller as cascaded block diagram with tunable gains

---

## Simulation 3: Pole Location → Mode Shape Explorer
### Lecture Source: Lecture 03, Pages 9-46; Lecture 04, Pages 33-43
### Visual Cues Observed
Lectures 03 and 04 extensively use:
- Complex plane diagrams (s-plane for CT, z-plane for DT) with poles plotted as × marks
- Fundamental mode shapes (exponentials, sinusoids, damped oscillations) plotted alongside pole locations
- Arrows connecting poles to their corresponding time-domain responses
- Visual demonstration: moving a pole left/right → response decays faster/slower; moving pole up/down → frequency changes
- Population growth visualization showing Fibonacci modes spiraling in complex plane

### Learning Objective
Create an intuitive visual connection between **where a pole sits in the complex plane** and **what the corresponding time-domain mode looks like**. This is one of the most abstract and important concepts in signals & systems; making it interactive and explorable can transform understanding.

### Theoretical Foundation
For a discrete-time system, the poles $p_k$ determine the fundamental modes. If the system is excited by an impulse, the response is a linear combination of modes:
$$h[n] = \sum_{k} c_k p_k^n u[n]$$

Each pole $p_k = r_k e^{j\theta_k}$ produces a mode:
- **Real pole** ($\theta_k = 0$): geometric sequence $p_k^n = r_k^n$ (exponential growth/decay)
- **Complex conjugate poles** ($p_k = r e^{j\theta}$, $\bar{p_k} = r e^{-j\theta}$): damped oscillation
  $$\text{mode} = r^n e^{jn\theta} + r^n e^{-jn\theta} = 2r^n\cos(n\theta)$$
  - Magnitude $r$ controls decay rate ($r < 1$ → stable)
  - Frequency $\theta$ (radians/sample) controls oscillation rate

Similarly, for CT, poles in s-plane: $p = \sigma + j\omega$ produce mode $e^{(\sigma + j\omega)t} = e^{\sigma t} e^{j\omega t}$

### System Architecture
**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|------------|
| Domain | {DT, CT} | Discrete or continuous time | Radio buttons |
| Pole Real Part (σ or Re(p)) | -2 to 2 | Decay/growth rate | Slider |
| Pole Imag Part (ω or Im(p)) | -π to π (DT), -5 to 5 (CT) | Oscillation frequency | Slider |
| Number of Poles | 1, 2, 3 | Single pole, conjugate pair, or triplet | Buttons/dropdown |
| Conjugate Pairing | Auto/Manual | Auto-pair complex poles or allow independent poles | Checkbox |
| Simulation Time Span | 1 - 50 (steps for DT), 0-10 (seconds for CT) | Duration to compute response | Slider |

**Output Observables:**
| Observable | Visualization | Purpose |
|-----------|----------------|---------|
| Complex Plane (z or s-plane) | Plotly scatter plot with pole markers | Shows pole locations; unit circle (DT) or Re=0 (CT) stability boundary |
| Time-Domain Impulse Response | Multi-line Plotly plot, one curve per mode | Shows individual modes and composite response |
| Mode Shape Overlay | Animated trajectory in complex plane | Traces the mode as n increases (for complex poles) |
| Stability Indicator | Color change: red (unstable), yellow (marginal), green (stable) | Quick visual check of pole regions |

### Visualization Strategy
**Left Panel (50%): Complex Plane**
- Plotly interactive 2D plot with:
  - Real axis (σ or Re), Imaginary axis (ω or Im)
  - Unit circle (DT) or imaginary axis (CT) as stability boundary
  - Pole locations as draggable × markers (or large red dots)
  - Click-and-drag to move poles; response updates live in right panel
- Shaded regions:
  - Stable region (left of Re=0 for CT, inside unit circle for DT): light green
  - Unstable region: light red
- Optional: show closed contours of constant settling time or constant frequency

**Right Panel (50%): Time-Domain Responses**
- Top subplot: Impulse response h[n] or h(t) as continuous line plot (Plotly)
  - If two conjugate poles: show their individual modes as dashed lines, composite response as solid line
  - Different colors per pole
  - Overlay exponential envelope $r^n$ or $e^{\sigma t}$ in gray for reference
- Bottom subplot (optional): Phase plane trajectory in complex plane
  - Plot h[n] in complex plane as points spiraling inward/outward depending on pole location
  - Animated spiral growing as simulation progresses

**Interaction:**
1. User drags pole(s) on left panel
2. System recomputes modes and roots → right panel updates instantly
3. Hovering over a pole shows its properties: r, θ, τ_settling, f_natural
4. Click pole to "lock" it; or "Create Conjugate" button to pair with complex conjugate
5. Toggle "Show Individual Modes" → reveals how each pole contributes

### Implementation Notes
**Complexity:** Medium-High

**Key Algorithms:**
- For DT with pole p: compute h[n] = p^n · u[n] for n = 0, ..., N
- For complex conjugate pair p = r·e^(jθ), inverse pair: h[n] includes 2·r^n·cos(nθ + φ)
- For CT with pole s: compute h(t) = e^(st) · u(t)
- Stability check: |p| < 1 (DT) or Re(s) < 0 (CT)
- Settling time approximation: n_settling ≈ -ln(tolerance) / ln(|p|) or t_settling ≈ -ln(tolerance) / σ

**Rendering:**
- Plotly for both panels (interactive, live update)
- Makefile-style dependency: if pole changes → recompute h[n], update both plots
- Draggable pole markers via Plotly click/drag (or Plotly annotations with custom JavaScript overlay)
- Smooth curve rendering with high point density (200+ points in time domain)

**Visual Design:**
- Use distinct colors per pole: pole 1 (blue), pole 2 (red), pole 3 (green), composite (black)
- Envelope curves as thin gray lines for reference
- Animated drawing of curves as sliders move (CSS animations or Plotly frame-by-frame)

### Extension Ideas
**Beginner:**
- Drag a pole from unstable region to stable region; watch response change from divergent to convergent
- Challenge: "Place poles so the impulse response peaks at n=3 and decays to 5% by n=10"
- Pole location quiz: given an impulse response curve, identify likely pole location

**Advanced:**
- Bode plot connection: show magnitude response |H(e^(jω))| and how pole locations manifest as peaks/valleys
- Step response (versus impulse): user can toggle input type; step response shows pole as DC gain contribution
- Design a system: specify desired settling time and overshoot (or damping ratio); show where to place poles
- Eigenvalue decomposition: for second-order system, show modal decomposition explicitly

**Real-World Connections:**
- Mechanical oscillator: two conjugate poles represent underdamped resonance (like car suspension)
- Electrical RLC circuit: poles determine whether circuit rings, oscillates, or overdamps
- Control stability: closed-loop control system poles must be in stable region (BIBO stability)
- Oscillating populations: Fibonacci mode structure revealed by complex conjugate poles at golden ratio

---

## Simulation 4: CT Integrator vs. DT Delay: Visual Comparison Engine
### Lecture Source: Lecture 04, Pages 1-9; Lecture 04, Pages 33-49
### Visual Cues Observed
Lecture 04 extensively contrasts:
- Block diagram pairs: CT system with ∫ box vs. DT system with R box
- Side-by-side differential equation y˙ = x + py versus difference equation y[n] = x[n] + py[n-1]
- Feedback loop comparison: CT shows continuous spiral accumulation, DT shows discrete jumps
- Operator algebra: (1 - pA) for CT mirrors (1 - pR) for DT
- Fundamental mode comparison: e^(pt) u(t) vs. p^n u[n]
- Both subject to same pole location analysis but with different stable regions (Re(p)<0 for CT, |p|<1 for DT)

### Learning Objective
Demystify the parallel structure between continuous-time and discrete-time systems by letting students explore both side-by-side with identical parameters. Show that the mathematics is isomorphic, but the stable regions differ, and the fundamental modes look different (continuous curve vs. discrete points).

### Theoretical Foundation
**CT System:** $\dot{y}(t) = x(t) + py(t)$ with operator form $(1 - pA)Y = AX$, where $A$ is integration operator.
- Impulse response: $h(t) = e^{pt}u(t)$
- Pole location: $s = p$ in s-plane; stable if $\text{Re}(p) < 0$ (left half-plane)

**DT System:** $y[n] = x[n] + py[n-1]$ with operator form $(1 - pR)Y = X$, where $R$ is delay operator.
- Impulse response: $h[n] = p^n u[n]$
- Pole location: $z = p$ in z-plane; stable if $|p| < 1$ (inside unit circle)

**Transformation:** Replace $A \to \frac{1}{T_s}$ (with sampling interval $T_s$) in CT to approximate first-order DT. Euler forward: $\dot{y}(nT_s) \approx \frac{y[n] - y[n-1]}{T_s}$.

### System Architecture
**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|------------|
| Pole Real Part (p) | -2 to 2 | Decay/growth constant | Shared slider (affects both CT & DT) |
| Input Type | {Impulse, Step, Ramp, Custom} | Driving signal | Radio buttons |
| Time Span (CT) | 0 - 5 | Duration in seconds | Slider |
| Sample Rate (DT) | 0.5 - 10 samples/sec | Sampling frequency relative to CT | Slider |
| Show Envelope | True/False | Overlay exponential e^(pt) on discrete points | Checkbox |
| Sync Display | True/False | Align time axes so DT samples overlay CT curve at measurement instants | Checkbox |

**Output Observables:**
| Observable | Visualization | Purpose |
|-----------|----------------|---------|
| CT Response y_c(t) | Smooth continuous curve (Plotly) | Shows exponential growth/decay |
| DT Response y[n] | Discrete points connected by vertical lines (Plotly) | Shows geometric growth/decay |
| CT & DT Overlaid | Both on same axes for direct comparison | Reveals discretization approximation error |
| Block Diagrams | Side-by-side: CT with ∫ vs. DT with R box | Visual correspondence |
| Mode Comparison | CT: e^(pt)u(t) curve vs. DT: p^n u[n] bars | Same pole → different temporal patterns |
| Stability Region | Shaded on s-plane vs. z-plane | Left half-plane vs. unit circle |

### Visualization Strategy
**Top Row (60%): Two Side-by-Side Time-Domain Plots**

*Left plot (CT):*
- Smooth curve for y_c(t) = e^(pt)u(t)
- Optional overlay of input signal x(t)
- Time axis labeled in seconds
- Reference line at y=0 and envelope y=e^(pt)

*Right plot (DT):*
- Discrete points for y[n] = p^n u[n]
- Vertical stem lines from y-axis to points
- Time axis labeled in sample number (or seconds if sync-enabled)
- Same scale as CT for easy comparison
- Optional: gray vertical lines showing sampling instants from CT

*Alignment:* Both plots share same y-axis range; time axes proportional so DT samples appear at positions corresponding to CT curve values.

**Bottom Row (40%): Block Diagrams & Complex Plane**

*Left (20%):* CT block diagram:
```
X ──→ [+] ──→ [∫] ──→ Y
      ↑
      └─── p ──┘
```

*Middle (20%):* DT block diagram:
```
X[n] ──→ [+] ──→ [R] ──→ Y[n]
         ↑
         └─── p ──┘
```

*Right (40%):* Complex plane showing:
- s-plane: pole at p, shaded left-half-plane (stable)
- z-plane: pole at p, shaded unit-circle interior (stable)
- Both poles at same real value p (for DT, interpret as z=p on real axis)

**Interaction:**
1. Slider changes p (shared between both systems)
2. Both responses update live: CT curve smoothly, DT points discretely
3. Toggle "Sync Display" → CT curve sampled at DT instants visually
4. Change sample rate → DT points move to new positions; more/fewer samples shown
5. Hover over point on DT plot → tooltip shows n, y[n], approximation error vs. CT(nT_s)

### Implementation Notes
**Complexity:** Medium

**Key Algorithms:**
- CT: y(t) = e^(pt) · u(t) evaluated at dense grid (e.g., 1000 points over [0, 5])
- DT: y[n] = p^n · u[n] for n = 0, 1, 2, ..., floor(time_span · sample_rate)
- Discretization error: |y_c(nT_s) - y[n]| visualized via light red shading between curves
- Stability regions: analytical (Re(p) < 0 vs. |p| < 1)

**Rendering:**
- Plotly for both time plots; add custom SVG overlays for DT stem lines if needed
- Block diagrams as simple SVG drawn dynamically
- Complex planes: simple Plotly scatter plots with filled regions for stability

**Dynamic Updates:**
- Parameter change → recompute both curves, all 4 visualizations update within 100ms
- Use memoization: if p unchanged, reuse cached curves; only regenerate when slider moves

### Extension Ideas
**Beginner:**
- "Predict the future:" give CT curve, ask user to predict where DT samples land before clicking
- Stability line chase: user moves slider left (p negative) and right (p positive); must keep pole in stable region
- Sampler effect: show Nyquist theorem in action: make p large imaginary part (if complex poles allowed), show aliasing

**Advanced:**
- Multi-step integration: cascade two integrators (CT) or delays (DT); see how order increases
- ZOH (zero-order hold) reconstruction: after sampling DT signal, show reconstructed CT signal using step-wise approximation
- Matched pole placement: given desired CT response, compute equivalent DT pole using bilinear transform or Tustin's method
- Simulation error analysis: vary sample rate; plot truncation/discretization error vs. sample_rate

**Real-World Connections:**
- Digital control: show why controller implemented on microprocessor (DT) can approximate analog controller (CT) with high sample rate
- Audio processing: show why CD quality 44.1 kHz sampling captures music frequencies but misses ultrasonic content (Nyquist)
- Numerical integration: Euler's method (forward difference) approximating ODE solution; investigate stability

---

## Simulation 5: Partial Fraction Decomposition Interactive Builder
### Lecture Source: Lecture 03, Pages 27-38; Lecture 05, Pages 1-30
### Visual Cues Observed
Lectures 03 and 05 show extensive use of:
- Second-order system factorization: (1 - 0.7R)(1 - 0.9R) = 1 - 1.6R + 0.63R²
- Tabular polynomial multiplication layout showing how coefficients combine
- Parallel decomposition: Y = 4.5/(1 - 0.9R) - 3.5/(1 - 0.7R) shown as two separate feedback paths
- Graphical stacking of two geometric sequences to form composite response
- Poles-to-partial-fractions algorithm visualized step-by-step
- Rational polynomials factored into (z - z₀)(z - z₁) form

### Learning Objective
Teach students that any high-order rational system function can be decomposed into a sum of simpler first-order (or conjugate pair) subsystems. This enables solving otherwise intractable systems by leveraging the known impulse response of each simple piece. The visual decomposition shows that complex behavior emerges from superposition of simple modes.

### Theoretical Foundation
Given a rational Z-transform or Laplace transform:
$$H(z) = \frac{b_0 + b_1 z^{-1} + \ldots}{1 + a_1 z^{-1} + a_2 z^{-2} + \ldots}$$

Factor the denominator into poles: $1 + a_1 z^{-1} + a_2 z^{-2} = (1 - p_0 z^{-1})(1 - p_1 z^{-1})\ldots$

Use partial fraction decomposition:
$$H(z) = \frac{c_0}{1 - p_0 z^{-1}} + \frac{c_1}{1 - p_1 z^{-1}} + \ldots$$

Each term corresponds to a pole; the coefficient $c_k$ determines the amplitude of mode $p_k^n$.

### System Architecture
**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|------------|
| System Order | 1, 2, 3 | Denominator degree | Radio buttons |
| Pole 1 Location | -2 to 2 | Real part of first pole | Slider (DT: -1 to 1.5 for stability) |
| Pole 2 Location | -2 to 2 (if order ≥ 2) | Real part of second pole | Slider |
| Numerator Coefficients | -5 to 5 each | Adjustable b₀, b₁, etc. | Sliders or text inputs |
| Input Type | {Impulse, Step} | What input to decompose for | Radio buttons |
| Display Mode | {Symbolic, Numerical, Visual Stacking} | How to show decomposition | Tabs |

**Output Observables:**
| Observable | Visualization | Purpose |
|-----------|----------------|---------|
| Factored Denominator | LaTeX: (1 - p₀R)(1 - p₁R)... | Shows poles at a glance |
| Partial Fraction Expansion | LaTeX: c₀/(1-p₀R) + c₁/(1-p₁R) + ... | Shows decomposition into first-order terms |
| Individual Mode Responses | Separate Plotly curves, one per pole | Each mode's contribution to total response |
| Composite Response | Bold Plotly curve showing sum of modes | Final impulse response h[n] |
| Stacked Area Chart | Colored regions showing mode contributions over time | Visual proof of superposition |
| Pole Diagram | Plotly scatter on z-plane showing pole locations | Stability check |

### Visualization Strategy
**Left Panel (40%): Symbolic Mathematics**
- Display system in three equivalent forms, stacked vertically:
  1. **Operator form:** $(1 + 1.6R + 0.63R^2)Y = X$
  2. **Factored form:** $(1 - 0.7R)(1 - 0.9R)Y = X$
  3. **Partial fractions:** $Y = \frac{4.5}{1-0.9R}X + \frac{-3.5}{1-0.7R}X$

- Use MathJax/KaTeX for crisp LaTeX rendering
- Color-code pole values: pole p₀ in blue, p₁ in red, p₂ in green, etc.
- Highlight matching terms across the three forms (e.g., "0.7" appears in factors AND denominator)

**Top Right (30%): Complex Plane**
- z-plane with poles plotted as colored × marks (same color as mode)
- Unit circle shown (stability boundary)
- Pole coordinates listed numerically below the plot
- Optional: show zeros of numerator as circles (o marks)

**Bottom Right (30%): Individual Mode Responses**
- Plotly line chart with one curve per mode
- Same colors as poles on z-plane
- Each curve labeled, e.g., "Mode 1: 4.5 × 0.9^n" with coefficient and pole
- Dashed lines for reference
- Composite response as bold black curve on top

**Full-Width Bottom Panel (optional): Stacked Area Chart**
- Horizontal axis: n = 0, 1, 2, ..., 20
- Colored areas for each mode, stacked vertically
- Total height = composite response h[n]
- Interaction: hover over area to highlight that mode's contribution

**Interaction:**
1. Slider moves pole position → all three equations update, colors flow through the display
2. Change numerator coefficient → partial fraction coefficients c₀, c₁ recalculate and reflow
3. Click "Decompose" button → reveals the factorization and decomposition step-by-step (optional animation)
4. Toggle "Show Stacking" → bottom panel slides in with area chart
5. Hover over colored mode area → that mode's curve highlights in all panels

### Implementation Notes
**Complexity:** High

**Key Algorithms:**
- **Pole finding:** Given polynomial denominator coefficients, find roots (use numpy.roots in Python backend)
- **Partial fraction coefficients:** Use residue formula or solve linear system
  - For simple poles: $c_k = \frac{\text{numerator}(p_k)}{(\text{prod}(1 - p_j p_k^{-1}), j \neq k)}$
  - Implement via residue calculation (symbolic or numeric)
- **Verify decomposition:** Check that sum of partial fractions equals original rational function
- **Mode response:** h[n] = Σ c_k p_k^n u[n] for each pole p_k

**Rendering:**
- MathJax for LaTeX equations (auto-render on parameter change)
- Plotly for both z-plane and mode curves (synchronize colors)
- Custom Canvas/SVG for stacked area chart (or use Plotly stacked area if performance permits)
- Backend: symbolic algebra (SymPy) for exact coefficients, numeric fallback for root-finding

**Numerical Stability:**
- Avoid forming high-order polynomials directly; use pole-residue form instead
- For ill-conditioned systems, use QR or SVD for partial fraction linear solve

### Extension Ideas
**Beginner:**
- "Match the decomposition:" show three partial fractions and ask which corresponds to which pole
- Adjust one pole at a time; see how its mode changes independently
- Reverse quiz: given h[n] curve, reconstruct the poles and coefficients

**Advanced:**
- Complex conjugate poles: show how two complex-valued modes combine to give real-valued response
- Improper fractions: if degree(numerator) ≥ degree(denominator), show polynomial + proper fraction decomposition
- Stability from decomposition: prove that all |c_k p_k^n| → 0 iff all |p_k| < 1
- Cascade vs. parallel realization: show block diagram for cascade (factored form) vs. parallel (partial fractions); compare computational complexity

**Real-World Connections:**
- System identification: given measured impulse response curve, fit poles and residues to data
- Filter design: specify pole locations to achieve desired frequency response (low-pass, band-pass)
- Transient response analysis: identify which mode dominates settling behavior
- Debugging control instability: pole creeping outside unit circle explains oscillation/divergence

---

## Summary Table: Simulation Ideas at a Glance

| Simulation | Source Lectures | Core Concept | Visual Hook | Complexity |
|-----------|-----------------|--------------|-------------|-----------|
| Leaky Tank Water Dynamics | 01: 25-36 | First-order systems, time constant τ | Animated water level in tank | Low |
| Block Diagram Execution Animator | 02: 9-17, 04: 2-12 | Operators, impulse response, difference equations | Step-by-step signal flow with highlighted values | Medium |
| Pole Location → Mode Shape Explorer | 03: 9-46, 04: 33-43 | Poles determine fundamental modes; stable vs. unstable regions | Draggable poles in complex plane with live mode curves | Medium-High |
| CT Integrator vs. DT Delay | 04: 1-9, 33-49 | Isomorphism between CT and DT; discretization effects | Side-by-side continuous curve vs. discrete points | Medium |
| Partial Fraction Decomposition Builder | 03: 27-38, 05: 1-30 | Complex responses decompose into simple modes; superposition | Symbolic equations + colored mode curves + stacked area chart | High |

---

## Pedagogical Principles Applied

Each simulation embodies one or more key learning principles from 3Blue1Brown-style visual mathematics:

1. **Embodied Understanding:** Leaky Tank lets students physically manipulate parameters and watch water level change—not just read an equation.

2. **Progressive Disclosure:** Block Diagram Animator reveals step-by-step execution; students can pause and inspect intermediate values.

3. **Multiple Representations:** Pole Explorer shows poles, modes, time-domain curves, and phase planes simultaneously—student picks which mental model resonates.

4. **Symmetry & Structure:** CT vs. DT Comparison reveals the parallel mathematical structure, demystifying why the same concepts appear in both domains.

5. **Composition from Parts:** Partial Fractions Builder shows how complex systems decompose into simple pieces; students viscerally understand superposition.

All five simulations prioritize **interactivity, color, animation, and live feedback** to transform abstract concepts into concrete, manipulable objects.
