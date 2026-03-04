# Interactive Tools Batch 01-09: MIT 6.003 Lectures 01-09
## Designed for Building, Constructing, and Discovering (NOT Passive Slider Demos)

This document outlines 12 new interactive tools inspired by MIT 6.003 Lectures 01-09 contact sheets. Each tool follows the paradigm of active engagement: students BUILD block diagrams, SOLVE challenges, ANIMATE processes, MANIPULATE representations, and DISCOVER relationships through interaction rather than observation.

---

## Tool 1: Leaky Tank Simulator with Continuous/Discrete Modes
### Inspired By (Visual)
Lecture 01, sheets 04-06: Multiple slides showing the leaky tank system with differential equation descriptions, "Check Yourself" challenges asking students to determine time constants and leak rates from tank diagrams, and step-by-step visual evolution of water level over time.

### What Students DO (not watch)
- Drag tank dimensions and drain holes to vary system parameters
- Choose between continuous-time (differential equation) and discrete-time (difference equation) representations
- Input a physical scenario (e.g., "a 1m³ tank with a 2cm drain hole") and have the tool AUTO-DERIVE the time constant and output equation
- Run the simulation and predict (then verify) water height after time T
- Compare side-by-side CT and DT responses to identical input profiles

### Tool Description
A hands-on physical system simulator where students build a leaky tank by adjusting physical parameters (tank cross-section area, drain radius, fluid viscosity). The tool immediately updates the mathematical representation: shows dy/dt = -(1/RC)·y for CT or y[n] = αy[n-1] for DT, with the coefficients computed from physical quantities. Students can input disturbances (refilling, blocking drain) and watch the response evolve both graphically and as an animated water level animation. Crucially, the tool forces students to recognize the deep connection between physical structure and mathematical equations—not as abstract magic, but as direct consequences of conservation laws.

### Interaction Model
- **Left panel:** Interactive 2D tank schematic. Drag tank height, diameter, and drain hole radius. Change fluid properties (viscosity dropdown). Buttons to switch CT/DT mode.
- **Middle panel:** Real-time display of derived system parameters (RC time constant, α decay factor) and corresponding equations.
- **Right panel:** Animated tank showing water level over time; below that, dual plots (CT on top, DT on bottom) showing y(t) and y[n] for the same input.
- **Input toolbar:** Presets (fill, drain, step input, pulse) or custom disturbance designer.

### Multi-Panel Layout
Three synchronized views:
1. **Physical schematic** (left) – tank diagram with draggable parameters
2. **Mathematical representations** (top right) – auto-updated equations and numerical parameters
3. **Simulation output** (bottom right) – animated tank + dual time-domain plots

Changes in the physical schematic instantly update equations and re-compute the animation.

### Key "Aha Moments"
- Students discover that the mathematical parameters (RC, α) emerge directly from physical dimensions and fluid properties—not handed down from on high
- Comparing CT and DT side-by-side on the same physical system reveals the Euler approximation visually: DT becomes CT as step size shrinks
- Students predict response behavior (monotonic decay, time to 63% settled value) before running the simulation, then verify their intuition

### Technical Architecture
**Backend:**
- Symbolic derivation of time constant from geometric and fluid parameters (SciPy's ODE solver for CT, difference equation evaluator for DT)
- Numerical integration using scipy.integrate.odeint for CT; direct iteration for DT
- Animation frame generation at 30 fps showing water level height as a function of time

**Frontend:**
- Canvas/SVG for tank schematic with draggable handles (radius, height sliders)
- Plotly for dual time-domain plots (CT above, DT below)
- Custom animator (requestAnimationFrame loop) rendering tank geometry and water fill level
- React state synchronizes physical parameters → equations → simulation output

**Complexity:** Medium

### Why This Isn't Generic
This is not "move a slider and watch the plot change." Instead, students start with a REAL PHYSICAL OBJECT, manipulate its dimensions, and have the system derive the mathematical model automatically. The insight is that equations come FROM structure, not from thin air. The CT/DT comparison is embedded in one unified physical system, not two separate sliders.

---

## Tool 2: Difference Equation Solver & Block Diagram Coach
### Inspired By (Visual)
Lecture 02, sheets 01-10: Dense slides showing step-by-step analysis of difference equations y[n] = ay[n-1] + bx[n] using block diagrams (delay, multiply, add), with "Check Yourself" panels asking students to trace signal flow and compute outputs sample by sample. Visual progression from equation → block diagram → signal flow.

### What Students DO (not watch)
- Type or paste a difference equation (e.g., y[n] - 0.8y[n-1] = x[n])
- Tool auto-generates the block diagram with labeled delay, gain, and adder blocks
- Students manually trace the signal path by clicking on nodes in order, predicting intermediate values
- Input an x[n] sequence (impulse, step, ramp, custom) and step through the simulation one sample at a time
- At each sample, the tool highlights the active block and shows which values flow where
- Verify predictions against the auto-computed output

### Tool Description
A scaffolded coaching tool that converts between difference equations and block diagrams while giving students a hands-on "signal flow trace" experience. When a student enters a difference equation, the tool parses it, builds the canonical form y[n] = ay[n-1] + bx[n], and generates a block diagram. Then students step through the computation: at n=0, x[0] enters the system, flows to gain block (if y[n-1] term exists), goes to adder, and produces y[0]. The tool highlights the signal path in red, shows intermediate values in floating labels, and requires students to predict the next output before stepping forward. Wrong predictions trigger a hint ("Remember to multiply by the gain factor before adding").

### Interaction Model
- **Top:** LaTeX input field for difference equation. Autocorrect suggestion for common forms.
- **Left:** Auto-generated block diagram (drag-free, just visual). Nodes are clickable to inspect their instantaneous values.
- **Right:** Signal trace log showing samples of x[n], intermediate values (delays, products), and y[n].
- **Bottom:** Input signal designer (presets or draw custom x[n] sequence). Step button advances by one sample. Play button runs the full simulation.
- **Feedback layer:** Floating prediction prompt ("Predict y[1] given x[1]=2 and y[0]=1.5") with input box and hint system.

### Multi-Panel Layout
Four regions:
1. **Equation editor** (top)
2. **Block diagram** (left, auto-generated from equation)
3. **Signal trace & values** (right, updates as simulation steps)
4. **Input signal designer & playback controls** (bottom)

All synchronized: equation changes regenerate the block diagram; stepping the simulation highlights the active blocks and updates the trace.

### Key "Aha Moments"
- Students viscerally understand that a difference equation IS a sequence of arithmetic operations, not an abstract formula
- The visual block diagram makes clear why a[n] appears at multiple places in the trace (it gets fed back to the adder)
- Students discover the transient response: impulse input produces a decaying sequence if |a| < 1
- Tracing manually a few times, then running full playback, students internalize the recursive structure

### Technical Architecture
**Backend:**
- SymPy parser to extract coefficients (a, b, feedback gains) from LaTeX equation input
- Validation that equations are realizable (linear, constant-coefficient DT systems)
- Difference equation evaluator in NumPy (vectorized for plotting, step-by-step for interactive trace)

**Frontend:**
- React component for equation editor (MathJax rendering)
- SVG/Canvas for block diagram generation (boxes for delays, multipliers, adders; edges traced on demand)
- Plotly for signal trace visualization
- State machine managing simulation step counter and highlighting active blocks
- Prediction input with hint triggers

**Complexity:** Medium

### Why This Isn't Generic
This tool FORCES the student to think like the system: what happens to a specific sample as it flows through the blocks. It's not "move a slider and watch the entire plot shift." It's "step through the computation, predict the value at this node, then verify." The block diagram is generated from the equation, not chosen from a menu.

---

## Tool 3: Convolution Machine with Animated Flip-Slide-Integrate
### Inspired By (Visual)
Lecture 08, sheets 06-10: Detailed visual sequence showing convolution structure, with explicit depiction of flipping h[k], sliding it over x[k], multiplying samples, and summing the products. Multiple "Check Yourself" panels asking which plot shows h[n-k] vs. h[k], and how many spikes appear in the output.

### What Students DO (not watch)
- Draw or select two finite signals x[n] and h[n] (impulse, step, ramp, custom spikes)
- Set a slider for the "current time index" m
- Watch the h[m-k] signal flip and slide in real time, with products x[k]·h[m-k] displayed as vertical bars
- Pause at any m and compute the sum manually (tooltip shows the arithmetic: "y[m] = Σ x[k]·h[m-k]")
- Compare predicted y[m] against the auto-computed full convolution result
- Replay the animation and observe how the output grows and decays

### Tool Description
An animated visualization of discrete convolution that makes the abstract flip-slide-multiply-sum algorithm visceral. Students begin by specifying or drawing two signals (e.g., x[n]={1,2,1} and h[n]={0.5, 1}). As they drag a slider for m from 0 to N+M-2, the visualization shows:
- Top subplot: x[n] (fixed, blue), h[m-k] (flipped and shifted, red)
- Middle subplot: products x[k]·h[m-k] as vertical bars
- Bottom subplot: cumulative sum up to current m, with the new contribution highlighted
- A numerical readout: "y[m] = 0.5 + 2 = 2.5"

Students can pause the animation, make a prediction, enter their predicted value, and verify. The animation then reveals the correct value and moves forward.

### Interaction Model
- **Input panel (top left):** x[n] signal designer (presets: impulse, step, ramp, or draw custom)
- **Input panel (top right):** h[n] signal designer
- **Central animation area (3 stacked plots):** signal overlap, product signal, cumulative sum. Index m controlled by slider below
- **Prediction prompt:** "What is y[3]?" Input box + reveal button
- **Playback controls:** Step, play, reset. Speed slider for animation playback

### Multi-Panel Layout
Three views arranged vertically in the animation area:
1. **Signal overlap:** x[n] and h[m-k] on the same axis
2. **Product sequence:** x[k]·h[m-k] as bars
3. **Cumulative result:** y[0], y[1], ..., y[m] with latest contribution highlighted

Slider for m spans horizontally below. Input/output designers on the sides.

### Key "Aha Moments"
- Students see that convolution requires FLIPPING h, not just shifting—a critical detail often missed
- The product signal clearly shows which samples contribute (non-zero products), aiding intuition about support
- Animating the slider slowly reveals that the output decays as h slides past x (if both are finite)
- Students predict the length of y[n]: it's |x| + |h| - 1, which they verify by observing where non-zero products appear

### Technical Architecture
**Backend:**
- NumPy's convolve() function for reference output
- Custom animator: for each m, compute products and partial sums
- Signal storage and shifting logic

**Frontend:**
- React state: x[n], h[n], current index m, predicted values
- Three Plotly traces (x, h_flipped, products, cumsum) updated on every slider/step change
- Custom SVG overlays to show the "flip" arrow and "slide" arrows during animation
- Prediction input with visual feedback (green checkmark or red X)

**Complexity:** Medium-High (animation synchronization across three plots)

### Why This Isn't Generic
This is not "type two arrays and see the convolution plot." It's an INTERACTIVE ANIMATION where students control the playback, predict outputs, and verify their understanding of the flip-and-slide algorithm step by step. The animation would be useless as a standalone video; the value is in the student's control and prediction.

---

## Tool 4: DT/CT Pole Mapper with Step Response Preview
### Inspired By (Visual)
Lecture 03, sheets 02-05: Visual depictions of pole locations on the complex plane for DT and CT systems, with corresponding time-domain responses (damped oscillations, growth, decay). "Check Yourself" panels asking which pole location produces which response shape.

### What Students DO (not watch)
- Click on the complex plane to place poles (drag to adjust)
- For DT: drag poles inside or outside the unit circle
- For CT: drag poles in left or right half-plane
- Watch the step response preview update in real time below the pole plot
- Predict whether the response is stable, oscillatory, or divergent
- Compare DT poles (unit circle) and CT poles (imaginary axis) on the SAME system, observing how CT poles map to DT poles via z = e^(sT)

### Tool Description
An interactive pole-plane editor where students place and manipulate poles while seeing real-time step response updates. The interface shows two synchronized views: (1) complex plane with unit circle (DT) or imaginary axis highlighted (CT), and (2) step response plot. Students drag poles around and feel the immediate impact on stability and response shape. A mode toggle switches between DT and CT representations. A tau slider (sampling period) shows how CT poles map to DT poles: as tau shrinks, the DT unit-circle pole moves toward the CT s-plane pole location.

### Interaction Model
- **Left panel:** Complex plane. For DT, unit circle boundary shown in green. For CT, imaginary axis shown in green. Click to place new pole, drag to move. Double-click to remove.
- **Mode selector:** Toggle DT/CT at top. Tau slider (sampling period) for CT↔DT mapping visualization.
- **Right panel:** Step response plot for the current pole set. Overlaid: stability boundary (red) outside which response diverges.
- **Info panel (bottom):** Shows pole locations, damping ratios, natural frequencies (for real poles); predicts response behavior in words ("Underdamped oscillation," "Critically damped," etc.)

### Multi-Panel Layout
Two main regions:
1. **Pole plane editor** (left, large)
2. **Step response preview** (right, equally large)

Small controls above (DT/CT mode, tau slider, clear poles button).
Info text below pole plane.

### Key "Aha Moments"
- Moving a pole slightly left/right or in/out of circle dramatically changes response shape—students feel the sensitivity
- Placing complex conjugate pairs shows oscillation frequency = angle from real axis
- Tau slider reveals the relationship between CT and DT: as sampling gets faster (tau → 0), DT poles approach corresponding CT poles
- Students discover that stability is a sharp boundary (unit circle edge in DT, imaginary axis in CT), not a smooth transition

### Technical Architecture
**Backend:**
- SciPy step response computation for given pole set
- Eigenvalue-to-transfer-function conversion
- Mapping formula z = e^(sT) for CT↔DT visualization

**Frontend:**
- Plotly for both pole plane and step response
- Custom drag-and-drop interaction for pole placement using mouse events
- Real-time recalculation of step response on every pole move (debounced to 50ms for performance)

**Complexity:** Medium

### Why This Isn't Generic
This is not "slide pole location and watch response" in isolation. It's an INTEGRATED EXPLORATION where students build spatial intuition: what region of the plane produces which behavior? The dual DT/CT view and tau slider expose the underlying continuous/discrete relationship, making it clear that DT is a discretization of CT, not a separate world.

---

## Tool 5: Signal Operations Algebra Workbench
### Inspired By (Visual)
Lecture 01, sheet 02: Examples showing a system as a black box with input x(t) and output y(t), emphasizing the signal transformation. Lecture 07, sheets 01-03: Transform properties (linearity, time shift, modulation) with visual examples.

### What Students DO (not watch)
- Enter a base signal expression as a mathematical formula or draw it (e.g., cos(2πt) or a custom waveform)
- Apply operations from a menu: time shift (τ), flip (t → -t), scale (at), amplitude scale (A·x), multiplication by exp or modulation
- See the result displayed graphically and as an updated formula
- Chain multiple operations and predict the final result before applying
- Compare their prediction (graphical sketch or formula) against the tool's result

### Tool Description
A signal algebra tool that plays the role of a graphing calculator for signals. Students build signal expressions by chaining operations: start with cos(t), time-shift by 1 second, then multiply by e^(-t/2). The tool displays the signal graphically and updates the mathematical expression in real time. Operation blocks can be drag-and-dropped to reorder (to explore commutativity: does shift then flip equal flip then shift?). A reference answer shows the correct result; students compare their chain to the reference to debug their intuition.

### Interaction Model
- **Top:** Expression editor (LaTeX or text input) or graphical signal drawer
- **Middle-left:** Operation palette (menus: Time shift, Flip, Scale amplitude, Multiply by exp/sinusoid, etc.)
- **Middle-right:** Current signal plot (auto-updated)
- **Bottom-left:** Operation chain (drag-and-drop blocks, each showing what it does)
- **Bottom-right:** Predicted vs. actual comparison (student's result vs. reference, overlaid or side-by-side)
- **Feedback:** Tooltip explanations and hints ("Flipping is equivalent to replacing t with -t")

### Multi-Panel Layout
Four regions:
1. **Expression or signal input** (top)
2. **Operation palette** (left side)
3. **Live preview of current signal** (right side, large)
4. **Operation chain & comparison** (bottom)

All updates in real time.

### Key "Aha Moments"
- Students discover that signal operations are FUNCTIONS that transform one signal into another, not abstract algebraic rules
- Comparing prediction vs. actual result, students notice mistakes: e.g., "I thought time-shift left by 2 and then flip would give x(-t-2), but actually it's x(-(t-2)) = x(-t+2)"
- Chaining operations reveals associativity and commutativity: some orders commute (shift then scale), others don't (shift then flip)
- Graphical representation makes the intuition clear: shifting right moves the plot right; flipping reflects across the y-axis

### Technical Architecture
**Backend:**
- SymPy symbolic manipulation for signal expressions
- NumPy vectorized evaluation for plotting
- Operation composition: each operation is a function x → x' that updates the expression and evaluates the result

**Frontend:**
- React component for operation blocks with drag-and-drop (react-beautiful-dnd or Konva)
- MathJax for LaTeX rendering of expressions
- Plotly for signal visualization
- Interactive signal drawing canvas (custom SVG/Canvas component) for freehand input

**Complexity:** Medium-High (expression parsing, operation composition, drag-and-drop UI)

### Why This Isn't Generic
This is not "move a slider and watch the plot shift." It's a tool for COMPOSING signal operations algebraically and seeing the results graphically. Students build expressions (like a mathematical sentence), and the tool validates their understanding by showing the result. The graphical comparison makes intuitive errors visible and correctable.

---

## Tool 6: System Identification Detective Challenge
### Inspired By (Visual)
Lecture 02, sheets 08-10: "Check Yourself" panels asking students to identify which system has which response, and examples of systems with different gain and delay.

### What Students DO (not watch)
- View a mystery "black box" system
- Provide test inputs (impulse, step, ramp, sinusoid) and observe outputs
- Propose a hypothesis about the system structure (first-order delay with gain, second-order with oscillation, etc.)
- Submit a candidate difference equation or block diagram
- Tool scores their answer and reveals the true system if incorrect, highlighting the discrepancy

### Tool Description
A challenge-based learning tool where students act like control engineers reverse-engineering a system. The tool generates a hidden discrete-time system (e.g., y[n] = 0.8y[n-1] + 0.5x[n] or y[n] = y[n-1] - 0.5y[n-2] + x[n]). Students can inject test signals and observe the response. They use deduction: an impulse response shows the mode behavior; a step response shows gain and settling time; a sinusoid reveals frequency-dependent gain and phase. They then guess the system structure by proposing a difference equation. The tool simulates their proposed system on the same test inputs and compares against the true system. A scoring system rewards efficient hypothesis testing (fewer experiments) and correct answers.

### Interaction Model
- **Top-left:** Input signal designer (impulse, step, ramp, sinusoid, custom)
- **Top-right:** Live plot of mystery system output in response to chosen input
- **Bottom-left:** Hypothesis editor (LaTeX field for difference equation or block diagram builder)
- **Bottom-right:** Comparison plot (mystery output vs. student's proposed system output on the same input)
- **Score panel:** Accuracy score, number of experiments used, hints remaining

### Multi-Panel Layout
Quad layout:
1. **Input designer** (top-left)
2. **Mystery system response** (top-right)
3. **Hypothesis editor** (bottom-left)
4. **Hypothesis vs. truth comparison** (bottom-right)

### Key "Aha Moments"
- Students learn that impulse response is the "fingerprint" of a linear system
- They discover that testing with multiple input types is more informative than one
- Seeing their proposed system plotted alongside the true system makes errors obvious (off by a factor of 2, oscillating when it should decay, etc.)
- The efficiency metric (experiments used) teaches good experimental design

### Technical Architecture
**Backend:**
- System generator: randomly create stable discrete-time systems (first-order, second-order, with realistic gains and time constants)
- Difference equation parser from student input
- Numerical simulation for both true and student systems
- Scoring: MSE between outputs, normalized by range

**Frontend:**
- React for layout and state management
- Input signal designer (dropdown + custom drawer)
- Equation editor (LaTeX)
- Plotly for side-by-side comparison plots
- Hint system (progressive disclosure of system properties)

**Complexity:** Medium

### Why This Isn't Generic
This is not "adjust sliders to match a curve." It's a DETECTIVE CHALLENGE where students form hypotheses based on evidence, test them, and iteratively refine. The tool forces active reasoning: what input should I use next to distinguish between my two candidate systems?

---

## Tool 7: Laplace Transform & Partial Fractions Solver (Interactive)
### Inspired By (Visual)
Lecture 05, sheets 01-09: Step-by-step derivation of Laplace transforms, region of convergence visualization (s-plane with ROC shaded), partial fractions decomposition examples.

### What Students DO (not watch)
- Enter a rational transfer function H(s) = P(s) / Q(s) (or paste an example)
- Tool marks poles on the s-plane and shades the ROC
- Choose "Expand Partial Fractions"
- Watch the decomposition unfold step-by-step: factoring Q(s), setting up residue equations, solving for coefficients
- Use the "Inverse Laplace" button to see the time-domain response h(t)
- Predict impulse response behavior before applying inverse transform
- Compare predicted stability/decay rate vs. actual result

### Tool Description
An interactive walkthrough of the Laplace transform and partial fractions process. Students enter a rational transfer function (or select from presets like low-pass RC filter, RLC circuit). The tool plots the poles in the s-plane with a shaded ROC region (right of rightmost pole). A step-by-step panel walks through partial fractions: "Factor denominator: (s+1)(s+2)... Assume expansion: A/(s+1) + B/(s+2)... Solve for residues..." At each step, students can try to predict the next coefficient before the tool reveals it. Once the expansion is complete, they can see the inverse Laplace transform (table lookup) and the time-domain h(t) plotted.

### Interaction Model
- **Top:** Transfer function input field (LaTeX). Presets dropdown (RC low-pass, RLC bandpass, etc.)
- **Left:** s-plane plot with poles marked (red X), ROC shaded (green region), and a vertical line at chosen σ for convergence check
- **Right:** Partial fractions decomposition steps (panels that expand/collapse). Current step highlighted. Predict input prompts.
- **Bottom:** Time-domain impulse response plot, auto-updated as decomposition progresses
- **Hint panel:** Explains ROC interpretation and inverse Laplace formula

### Multi-Panel Layout
Left-right layout:
1. **S-plane pole/ROC visualization** (left, medium)
2. **Partial fractions step-by-step** (center, tall, scrollable)
3. **Time-domain h(t) preview** (right, medium)

Transfer function input at top. Hints below.

### Key "Aha Moments"
- Poles in the complex plane DICTATE the ROC and ROC determines which h(t) is realized
- Real poles → exponential decay in h(t); complex pole pairs → damped oscillations
- Partial fractions convert a rational function into a sum of simple terms, each invertible via table lookup
- ROC determines causality: left-sided, two-sided, or right-sided h(t)—not just the transform formula

### Technical Architecture
**Backend:**
- SymPy symbolic algebra for pole/zero extraction, residue computation, partial fractions decomposition
- Step-by-step symbolic manipulation (show intermediate algebraic steps)
- Inverse Laplace using Bromwich integral or direct table lookup for standard forms

**Frontend:**
- React for state management (current step, predicted vs. actual)
- MathJax for LaTeX rendering of equations
- Plotly for s-plane and time-domain plots
- Collapsible step panels with input fields for predictions

**Complexity:** High (symbolic algebra, step-by-step symbolic simplification)

### Why This Isn't Generic
This is not "type a transfer function and see h(t)." It's an INTERACTIVE WALKTHROUGH that forces students to predict intermediate results (residues, factorizations) before the tool reveals them. The s-plane visualization ties poles to ROC to time-domain behavior, making abstract concepts concrete.

---

## Tool 8: Bode Diagram Explorer with Phasor Rotation
### Inspired By (Visual)
Lecture 09, sheets 01-12: Vector diagrams showing poles/zeros on complex plane, with corresponding Bode magnitude and phase plots. Progressive animation of frequency sweep.

### What Students DO (not watch)
- Design a system by placing poles and zeros on the complex plane (click to add, drag to adjust)
- Click a "Sweep" button to watch the Bode plot trace out in real time as frequency ω increases from 0 to ∞
- At any frequency, a phasor from each pole and each zero to the point jω is drawn, showing magnitudes and angles
- Pause the sweep and predict the Bode response at that frequency using the phasor magnitudes and angles
- Verify prediction against the Bode plot reveal

### Tool Description
An interactive Bode plot constructor where pole and zero locations directly determine the frequency response magnitude and phase. As frequency sweeps from 0 to high values, students see:
- **Complex plane view:** Green circle centered at each pole and zero, with phasors drawn from poles/zeros to the current frequency point jω on the imaginary axis
- **Bode plots (below):** Magnitude and phase updating in real time, traced by a red line as ω increases
- At any frequency, the tool computes |H(jω)| = (product of zero distances) / (product of pole distances) and ∠H(jω) = sum of zero angles - sum of pole angles

Students pause the sweep, predict the Bode value based on phasor geometry, and check their answer.

### Interaction Model
- **Top half:** Complex plane editor. Poles (red X) and zeros (blue O) placed by clicking. Drag to adjust. Right-click to remove.
- **Bottom half, left:** Bode magnitude plot (log-log with asymptotic lines). Overlay shows phasor-based prediction.
- **Bottom half, right:** Bode phase plot (semilog). Overlay shows angle sum prediction.
- **Controls:** Slider for current frequency ω (also traces the point jω on the complex plane). Play/pause for frequency sweep animation. Speed control for animation.
- **Prediction prompt (optional):** "At this frequency, predict |H(jω)| using phasor magnitudes." Input box + reveal.

### Multi-Panel Layout
Two main sections:
1. **Complex plane with phasors** (top, 60% height)
2. **Bode plots** (bottom, 40% height, side-by-side magnitude and phase)

Frequency slider and animation controls span the bottom.

### Key "Aha Moments"
- Phasor distances are NOT arbitrary; they're the geometric basis for Bode magnitude and phase
- Poles near the imaginary axis cause resonance peaks (phasor distance decreases to near zero)
- Zeros on the imaginary axis cause notches (zero distance goes to zero, numerator → 0)
- The relationship between pole/zero locations and frequency response shape becomes visceral through phasor geometry

### Technical Architecture
**Backend:**
- Numerator and denominator polynomial construction from pole/zero locations
- Frequency response H(jω) via polynomial evaluation
- Bode asymptotic approximations for reference comparison
- Phasor computation: distances from each pole/zero to jω, angles

**Frontend:**
- React state: poles array, zeros array, current frequency ω
- Plotly for Bode plots with frequency slider integration
- SVG/Canvas for complex plane with phasors (Konva or custom SVG)
- Animation loop updating ω and re-rendering phasors and Bode traces
- Prediction input UI (optional)

**Complexity:** High (real-time phasor rendering, Bode asymptotic calculations, animation synchronization)

### Why This Isn't Generic
This is not "move poles/zeros and see Bode plot." It's an ANIMATED FREQUENCY SWEEP with phasor visualization that teaches the geometric interpretation of frequency response. The phasors are not decoration; they're the central pedagogy. Students learn that Bode magnitude is literally the product of distances in the complex plane.

---

## Tool 9: Z-Transform & Inverse Transform Workshop
### Inspired By (Visual)
Lecture 06, sheets 01-07: Z-transform definition, pole-zero diagrams in the z-plane (unit circle boundary), inverse Z-transform via contour integration, examples of DT impulse responses.

### What Students DO (not watch)
- Enter a transfer function H(z) = (z-z₁)(z-z₂)/((z-p₁)(z-p₂)) as a rational function
- Tool plots poles (red X) and zeros (blue O) on the z-plane with the unit circle boundary highlighted
- Mark poles inside (causal/stable) vs. outside the unit circle
- Request "Inverse Z-Transform" and watch a step-by-step residue-based calculation
- Predict coefficients h[n] for specific values of n before the tool reveals them
- Verify stability by checking whether all poles are inside the unit circle

### Tool Description
A Z-transform workshop analogous to the Laplace tool but for discrete-time systems. Students input a rational z-domain transfer function. The tool plots poles and zeros on the z-plane with the unit circle boundary (green). It computes and displays the region of convergence (ROC) based on pole locations. A step-by-step panel walks through the residue-based inverse: contour integral set up, pole residues computed. For each pole, the corresponding h[n] term (geometric sequence r^n) is shown. Students predict the time-domain h[n] before the tool reveals it, then verify by comparing against a direct DT impulse response simulation.

### Interaction Model
- **Top:** H(z) input field (rational form). Presets (first-order, second-order, notch filter)
- **Left:** Z-plane plot with poles, zeros, unit circle (boundary), and ROC shaded
- **Center:** Inverse Z-transform step-by-step (residue calculation panels)
- **Right:** Time-domain h[n] bar plot, auto-updated
- **Bottom:** Stability verdict (all poles inside unit circle → stable, else unstable)
- **Prediction UI:** For a specific n (e.g., h[5]), student predicts the value before the tool computes it

### Multi-Panel Layout
Left-right-center layout:
1. **Z-plane pole/zero plot** (left)
2. **Inverse Z-transform steps** (center, tall and scrollable)
3. **Time-domain h[n]** (right)

Input at top, stability info below plot.

### Key "Aha Moments"
- Pole locations inside vs. outside unit circle determine stability (unlike CT, where the imaginary axis is the boundary)
- Poles on the unit circle correspond to sustained oscillations; inside → decay; outside → growth
- Residue-based inversion is the discrete analog of Laplace partial fractions
- ROC is even more important in Z-domain: same H(z) can invert to multiple h[n] if ROC is different (causal, anti-causal, two-sided)

### Technical Architecture
**Backend:**
- SymPy for rational function manipulation, pole/zero extraction, residue computation
- Step-by-step symbolic simplification for inversion
- Direct DT impulse response evaluation for verification

**Frontend:**
- React state management
- Plotly for z-plane and h[n] plots
- MathJax for LaTeX rendering
- Collapsible step panels with prediction inputs

**Complexity:** High (similar to Laplace tool, but with z-plane geometry)

### Why This Isn't Generic
This is not "type H(z) and see h[n]." It's a STEP-BY-STEP INVERSION WALKTHROUGH with stability verification and prediction challenges. The unit circle boundary is central pedagogy, not a decorative reference line.

---

## Tool 10: Fourier Series Composer with Harmonic Control
### Inspired By (Visual)
Lecture 07-09 references: Fourier series decomposition showing fundamental and harmonics. Earlier simulations (fourier_series, fourier_phase_vs_magnitude) in the existing catalog suggest this is a concept students need to manipulate.

### What Students DO (not watch)
- Adjust sliders for fundamental frequency, amplitude, and phase of each harmonic (1st, 2nd, 3rd, etc.)
- Watch the composite waveform update in real time
- Predict the resulting waveform shape before adjusting sliders (e.g., "What if I increase only the 3rd harmonic?")
- Challenge mode: given a target waveform, adjust harmonics to approximate it
- Compare time-domain waveform to frequency-domain magnitude and phase spectrum (side-by-side)

### Tool Description
A Fourier series composer where students build complex periodic signals from harmonic components. They control individual harmonic amplitudes and phases via sliders. The tool displays: (1) sum of selected harmonics in time domain, (2) magnitude spectrum, (3) phase spectrum, and (4) individual harmonic traces overlaid faintly. As students adjust sliders, all views update in real time. Challenge mode presents a target waveform (e.g., sawtooth, square wave) and asks students to approximate it with a finite harmonic set, showing error as they adjust.

### Interaction Model
- **Left panel:** Harmonic control sliders (amplitude and phase for each of first 10 harmonics)
- **Top-right:** Time-domain composite waveform plot. Individual harmonics drawn faintly in background.
- **Middle-right:** Magnitude spectrum (bar plot of harmonic amplitudes)
- **Bottom-right:** Phase spectrum (bar plot of phases)
- **Challenge mode toggle:** Overlay target waveform and show approximation error metric (RMS or L2 norm)

### Multi-Panel Layout
Left-right split:
1. **Harmonic controls** (left, tall, scrollable)
2. **Time, magnitude, and phase plots** (right, stacked vertically)

### Key "Aha Moments"
- Harmonic amplitudes directly control waveform shape; students see that removing high harmonics smooths the signal
- Phase shifts change the time-domain appearance but don't affect the magnitude spectrum (only phase spectrum)
- Square and sawtooth waves have distinctive harmonic structures: students discover that only odd harmonics contribute to square waves
- Finite harmonic truncation causes Gibbs phenomenon ripples; students see the trade-off between accuracy and complexity

### Technical Architecture
**Backend:**
- NumPy FFT for reference spectrum; direct Fourier series sum for display
- Waveform generation from harmonic coefficients (vectorized)

**Frontend:**
- React for slider state and parameter updates
- Plotly for time-domain and frequency-domain plots
- Custom SVG/Canvas for overlay of individual harmonics (faint traces)
- Real-time update on every slider change (debounced)

**Complexity:** Low-Medium (straightforward signal synthesis)

### Why This Isn't Generic
This is not "type a waveform and see its spectrum." It's a SIGNAL BUILDER where students compose waveforms from harmonics and see the spectrum emerge. The dual representation (time and frequency) is essential; they're linked by the sliders, not just two separate plots.

---

## Tool 11: State-Space Realization & Mode Decomposition Challenge
### Inspired By (Visual)
Lecture 03-04, sheets showing systems decomposed into fundamental modes (first-order and second-order modes), accumulator (integrator) blocks, and gain structures. "Check Yourself" panels asking students to identify modes from pole locations.

### What Students DO (not watch)
- Enter a transfer function H(s) (or H(z))
- Tool auto-generates a state-space realization (canonical form)
- Click "Decompose into Modes" to see the system decomposed as a sum of first-order and second-order subsystems
- Each subsystem corresponds to one pole (or pole pair)
- For each mode, predict the step response shape (exponential decay, damped oscillation, etc.) before simulation
- Verify predictions by running the simulation and observing the time-domain response
- Option to swap between different state-space realizations (controller canonical, observer canonical, diagonal) and see how the implementation changes while the input-output behavior remains the same

### Tool Description
A state-space decomposition tool that teaches systems as sums of fundamental modes. Students input a transfer function; the tool automatically constructs a minimal state-space realization A,B,C,D. It then decomposes the system by computing the diagonal form (or nearly diagonal form via Jordan canonical form). Each diagonal block corresponds to one pole (real pole → 1×1 block with exponential response; complex conjugate pair → 2×2 block with damped oscillation). Students see: (1) the transfer function, (2) the state-space matrices, (3) the decomposed mode blocks, and (4) the corresponding time-domain response of each mode. They predict which modes dominate the overall response based on pole locations.

### Interaction Model
- **Top-left:** Transfer function input. Presets (second-order underdamped, overdamped, etc.)
- **Top-right:** State-space matrices A, B, C, D (display only, read from H(s))
- **Bottom-left:** Mode decomposition: each mode visualized as a subsystem block with its pole location and characteristic response shape
- **Bottom-right:** Step response plot showing each mode's contribution as a faint trace, and the sum as the solid line
- **Control buttons:** "Decompose," "Show Modes," "Simulate." Checkbox for showing individual modal contributions.
- **Prediction prompt (optional):** "Which mode dominates the early response? Which mode is fastest?"

### Multi-Panel Layout
2×2 grid:
1. **Transfer function & matrices** (top-left)
2. **Mode visualization** (top-right)
3. **Modes as subsystem blocks** (bottom-left)
4. **Step response with modal contributions** (bottom-right)

### Key "Aha Moments"
- A system is a sum of independent modes, each with its own pole and characteristic behavior
- Real poles → exponential behavior; complex poles → oscillatory behavior
- The overall response is a weighted sum of modal responses; dominant modes (closest to imaginary axis or unit circle) respond longest
- Different state-space realizations (different A, B, C, D) represent the same input-output system—just different internal state variables
- State-space is not an alternative to transfer functions; it's a decomposition into modes with physical meaning

### Technical Architecture
**Backend:**
- SymPy for transfer function to state-space conversion
- NumPy eigenvalue decomposition (or Jordan canonical form) for modal decomposition
- SciPy step response for each modal subsystem and the sum
- Modal participation factors (eigenvector components) to explain which mode dominates

**Frontend:**
- React for layout and state management
- Plotly for step response plots with individual modes as faint overlays
- Custom SVG rendering of state-space matrices and mode blocks
- Interactive checkboxes to toggle modal contributions on/off

**Complexity:** Medium-High (state-space conversion, modal decomposition, overlaid plotting)

### Why This Isn't Generic
This is not "type a transfer function and see the step response." It's a DECOMPOSITION TOOL that reveals the internal structure (modes) and shows how each mode contributes. The modal decomposition is the key insight; students learn to think of systems as sums of elementary responses, not as black-box transfer functions.

---

## Tool 12: Frequency Selective Filtering Challenge (Real-time Audio)
### Inspired By (Visual)
Lecture 09 references frequency response and practical applications. The existing RC_lowpass_filter and modulation_techniques simulations are close, but this is a tool where students DESIGN and EVALUATE filters interactively on real audio.

### What Students DO (not watch)
- Load a sample audio signal (speech, music, or noise) or generate a test signal (mix of pure tones at 100 Hz, 1 kHz, 10 kHz)
- Adjust filter parameters (cutoff frequency, filter order, filter type: lowpass, highpass, bandpass)
- Hear the filtered audio play in real time and see the frequency spectrum before and after filtering
- Predict which frequencies will be attenuated based on the filter response (Bode plot)
- Verify predictions by observing the post-filter spectrum
- Challenge: design a filter to remove a specific frequency (notch filter) or isolate speech frequencies while attenuating high-frequency noise

### Tool Description
An interactive audio filter design and test tool. Students load an audio sample or generate a synthetic test signal (e.g., sum of sinusoids at specific frequencies). They design a filter by setting parameters (type, cutoff, order). The tool displays: (1) original audio waveform in time domain, (2) original frequency spectrum (FFT), (3) filter frequency response (Bode plot), (4) filtered audio waveform, and (5) filtered frequency spectrum. The audio can be played back (original and filtered) via HTML5 audio elements, allowing students to hear the effect. A challenge mode provides a target (e.g., "Remove frequencies above 2 kHz while preserving 0-1 kHz with <3dB attenuation") and scores the filter design.

### Interaction Model
- **Top-left:** Audio input selector (presets: speech, music, noise, or synthesize custom mix of sinusoids)
- **Top-right:** Filter design panel (type selector, cutoff slider, order slider)
- **Middle-left:** Original audio (time-domain waveform) and spectrum (Fourier magnitude)
- **Middle-right:** Filtered audio (time-domain waveform) and spectrum
- **Center:** Filter frequency response (Bode magnitude and phase)
- **Bottom:** Audio playback controls (original and filtered tracks side-by-side for comparison)
- **Challenge mode:** Overlay target specification on the Bode plot; show pass-band error and stop-band error

### Multi-Panel Layout
Three rows:
1. **Input & filter design controls** (top)
2. **Original signal (time + freq), filter response, filtered signal (time + freq)** (middle, 3 panels)
3. **Audio playback controls** (bottom)

### Key "Aha Moments"
- Frequency response (Bode) translates directly into which audio frequencies are preserved and which are removed
- Higher-order filters roll off faster but add more latency (phase shift)
- Hearing the effect of filtering on real audio (speech or music) is more convincing than abstract Bode plots
- Notch filters can surgically remove a specific frequency (e.g., 60 Hz hum) while leaving adjacent frequencies intact
- Students discover the trade-off between sharpness (order) and complexity (computational cost)

### Technical Architecture
**Backend:**
- SciPy butter, cheby1, ellip design for filter coefficients
- scipy.signal.lfilter for audio filtering
- NumPy FFT for spectrum computation
- Optional: WAV file I/O for loading real audio samples

**Frontend:**
- React for parameter controls and layout
- Plotly for time-domain and frequency-domain plots
- Web Audio API (HTMLAudioElement or Tone.js) for audio playback
- Real-time filtering: if the audio is short, filter on every parameter change; otherwise, pre-compute and cache
- Visualization of Bode plot with filter parameters mapped to response curve

**Complexity:** Medium-High (audio I/O, real-time FFT visualization, audio playback coordination)

### Why This Isn't Generic
This is not "move a slider and watch the Bode plot." It's an AUDIBLE FILTER DESIGN TOOL where students can hear the consequences of their design choices. The combination of frequency-domain (Bode, spectrum) and time-domain (audio waveform) visualizations, plus auditory feedback, makes the concept tangible. Challenge mode gamifies the design task: can you meet the specifications?

---

## Summary & Integration Notes

These 12 tools span the core content of MIT 6.003 Lectures 01-09:

- **Tools 1-2** (Leaky Tank, Difference Equation Coach): Foundation concepts (CT/DT, difference equations, block diagrams)
- **Tools 3-4** (Convolution Machine, DT/CT Pole Mapper): Signal processing and system analysis
- **Tool 5** (Signal Operations Algebra): Transforms and signal composition
- **Tools 6-7** (System Identification, Laplace Solver): Identification and transform methods
- **Tools 8-9** (Bode Explorer, Z-Transform Workshop): Frequency domain analysis
- **Tool 10** (Fourier Composer): Spectral representation
- **Tools 11-12** (State-Space Modes, Filtering Challenge): System structure and practical application

**Recommended implementation order (by dependencies & effort):**
1. Tool 1 (Leaky Tank) – foundational, medium effort
2. Tool 2 (Difference Equation Coach) – builds on Tool 1, medium effort
3. Tool 3 (Convolution Machine) – independent, high visual impact, medium-high effort
4. Tool 4 (DT/CT Pole Mapper) – independent, medium effort, high pedagogical value
5. Tool 5 (Signal Algebra) – independent, medium-high effort
6. Tools 6, 7, 8, 9 (Identification, Transforms) – higher effort, later in course
7. Tool 10 (Fourier Composer) – can leverage existing Fourier simulation
8. Tool 11 (State-Space Modes) – mid-course, ties together block diagrams and poles
9. Tool 12 (Filter Challenge) – capstone, uses frequency response concepts

Each tool emphasizes **active construction, prediction, and verification** rather than passive observation. The key pedagogy is iteration: students form a hypothesis, the tool shows the result, and students refine their mental model.
