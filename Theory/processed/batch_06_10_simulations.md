# Simulation Ideas from Lectures 6-10

## Simulation: Laplace Transform Region of Convergence Explorer
### Lecture Source: Lecture 6, Pages 355-536
### Learning Objective
Develop intuition for how the Region of Convergence (ROC) relates to signal causality and properties in the time domain. Students learn that ROC isn't just an algebraic property—it reveals fundamental information about the signal: whether it's right-sided, left-sided, or both-sided.
### Theoretical Foundation
**Key equations:**
$$X(s) = \int_{-\infty}^{\infty} x(t) e^{-st} dt$$

**ROC patterns:**
- Right-sided signals: ROC is $Re(s) > \sigma_0$ (half-plane to the right)
- Left-sided signals: ROC is $Re(s) < \sigma_0$ (half-plane to the left)
- Two-sided signals: ROC is $\sigma_1 < Re(s) < \sigma_2$ (vertical strip)

**Related concepts:** Time-domain interpretation of convergence; pole-zero plots; causality from ROC

### System Architecture
**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|-----------------|-----------|
| Signal Type | {right-sided, left-sided, two-sided} | Which time domain signal class to explore | Radio buttons |
| Pole Position | -5 to 5 | Real pole location in s-plane | Slider |
| Signal Duration | [0,T], (-∞,0], (-∞,∞) | Support of time signal | Selection menu |
| Exponential Decay Rate | 0.1 to 3.0 | Controls convergence speed for $e^{-\alpha t}u(t)$ | Slider |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|---------------|---------|
| Time-Domain Signal | Line plot with explicit support interval | Shows causality visually |
| S-Plane ROC | Shaded region (half-plane or strip) with poles marked | Connects algebraic ROC to geometry |
| Convergence Region | 3D surface (s real and imaginary parts) showing magnitude decay | Intuition for why ROC exists |
| Pole-ROC Relationship | Animated movement of poles vs. ROC boundary | Cause-and-effect discovery |

### Visualization Strategy
**Primary interaction flow:**
1. User selects a signal class (e.g., "right-sided exponential")
2. Time-domain plot immediately updates showing $x(t) = e^{-\alpha t}u(t)$
3. S-plane appears with the pole at $s = -\alpha$ and ROC shaded as $Re(s) > -\alpha$
4. User drags the pole left/right; ROC boundary moves synchronously
5. 3D surface plot shows the magnitude $|X(s)|$ in the complex s-plane—students see the "wall" at the ROC boundary where the integral diverges
6. User switches to "left-sided" and sees the signal flip in time, the pole stays the same, but ROC flips to the left (with intuitive explanation)
7. "Two-sided" mode shows e.g. $e^{-|t|}$, revealing the vertical strip with poles on both sides

**Aha moments:**
- ROC boundary is determined *entirely* by pole locations
- Causality = ROC extends to infinity on the right
- Non-causal signals have ROC extending to infinity on the left
- The vertical strip in two-sided signals is the *intersection* of two half-planes—a pure visual insight

### Implementation Notes
**Complexity:** Medium
**Key Algorithms:**
- Parametric generation of exponential signals with optional time reversal
- Numerical integration (adaptive Simpson's rule) to validate Laplace transform magnitude in ROC and outside
- Automatic pole detection from user-drawn region; ROC boundary computation
- Plotly surface rendering for 3D s-plane magnitude visualization

**Dependencies:** NumPy (integration), SciPy (interpolation for ROC visualization), Plotly.js (3D surface), Three.js (optional, for interactive pole dragging in s-plane)

### Extension Ideas
**Beginner:** Compare ROC for $e^{-\alpha t}u(t)$, $e^{\alpha t}u(-t)$, and $e^{-|t|}$; predict ROC before computing.

**Advanced:** Load a composite signal (sum of exponentials); observe how ROC is the *intersection* of individual ROCs. What happens when intersections are empty? (Laplace transform doesn't exist.)

**Real-world:** Audio filtering—explain why an audio filter's impulse response must be causal (ROC extends to $+\infty$) to be realizable in hardware.

---

## Simulation: Numerical Approximation Method Comparison (Forward/Backward Euler & Trapezoidal)
### Lecture Source: Lecture 7-2, Pages 276-1095
### Learning Objective
Understand how different numerical discretization schemes map continuous-time poles to discrete-time poles, and how this mapping affects stability. Discover why backward Euler and trapezoidal methods are superior to forward Euler for stiff systems by visualizing the s-plane to z-plane mapping.
### Theoretical Foundation
**Key mappings:**

Forward Euler: $z = 1 + sT$

Backward Euler: $z = \frac{1}{1-sT}$

Trapezoidal (bilinear): $z = \frac{1 + sT/2}{1 - sT/2}$

**Stability criterion:** For a CT system to remain stable after discretization, poles in the left half-plane (LHP) must map inside the unit circle.

**Related concepts:** Stability boundaries; step-size selection; numerical stiffness; the leaky tank system as a pedagogical example

### System Architecture
**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|-----------|
| CT Pole Location | -5 to 0 (real axis) | Where poles live in CT; determines system dynamics | Slider (draggable in s-plane) |
| Sampling Period T | 0.01 to 2.0 seconds | Controls discretization coarseness | Slider |
| Method | {Forward, Backward, Trapezoidal} | Which s→z mapping to apply | Radio buttons |
| System Type | {leaky tank, mass-spring, damped oscillator} | Affects pole placement and visualization context | Selection menu |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|---------------|---------|
| CT Pole in S-Plane | Point on real axis with LHP region shaded | Shows where CT pole starts |
| DT Pole in Z-Plane | Point location relative to unit circle; color codes stability | Shows where pole maps under chosen method |
| Step Response Comparison | 3-panel time plots: CT, DT, and error | Intuitive feel for approximation quality |
| Stability Region Map | Shaded regions in z-plane for each method | Reveals max T before instability |
| Method Animation | Shows pole motion as T increases from 0 to T_max | **Aha moment:** forward Euler crosses unit circle fast; backward doesn't |

### Visualization Strategy
**Key interaction sequence:**
1. User places a CT pole at, e.g., $s = -1$ (stable exponential decay)
2. Three z-plane regions appear side-by-side: one for each method
3. As user slides T from 0 upward:
   - Forward Euler pole circles outward from z=1 along real axis; at T=2, it crosses the unit circle → instability
   - Backward Euler pole spirals *inward* toward origin; never leaves unit circle (always stable)
   - Trapezoidal pole orbits smoothly, staying on unit circle boundary (perfect for oscillatory modes)
4. User toggles between time-domain step responses and watches forward Euler blow up while backward Euler stays bounded
5. Overlaying the mapping curves (z = 1+sT vs. entire LHP mapped through the formula) shows the geometry

**Visual storytelling:**
- "Watch what happens to stability as you increase the sample period"
- "Why is backward Euler sometimes called 'A-stable'?"
- Interactive highlighting: hover over a z-pole location to see the corresponding s-plane origin

### Implementation Notes
**Complexity:** Medium-High
**Key Algorithms:**
- S-plane to z-plane coordinate transformation (three formulas)
- Pole location computation via eigenvalue analysis of DT system functional
- DT step response computation using difference equations and recursion (or direct z-transform inversion)
- CT step response via analytical impulse response + convolution or Laplace inversion
- Error metric (L2 norm between CT and DT step responses over discrete time)

**Dependencies:** NumPy (pole computation, convolution), SciPy (signal, lti; DT/CT system representation), Plotly (polar plot for z-plane with unit circle overlay)

### Extension Ideas
**Beginner:** Fix T = 0.1s, place a pole at s = -2, and predict which method will be most accurate without running simulation.

**Advanced:** Load a multi-pole system (mass-spring-damper); observe that *all* poles must map inside unit circle for stability. Find the critical T that causes the rightmost pole to hit the stability boundary.

**Real-world:** Embedded control systems—explain why DSP engineers use backward Euler or trapezoidal rules instead of forward Euler: they allow larger step sizes without instability, reducing computational overhead.

---

## Simulation: Convolution Geometry in 2D
### Lecture Source: Lecture 8-2, Pages 271-1439
### Learning Objective
Develop deep geometric intuition for convolution by making the "flip, shift, and multiply" operation visual and interactive. Most students find convolution algebraically opaque; a dynamic visualization transforms it into an obvious operation.
### Theoretical Foundation
**Key equation:**
$$y[n] = (x \ast h)[n] = \sum_{k=-\infty}^{\infty} x[k] h[n-k]$$

**Continuous analog:**
$$y(t) = (x \ast h)(t) = \int_{-\infty}^{\infty} x(\tau) h(t-\tau) d\tau$$

**Related concepts:** LTI system characterization; impulse response; superposition; time reversal and shifting; optical convolution (microscope/telescope blurring)

### System Architecture
**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|-----------|
| Input Signal x[n] | Graphical editor (drag points) or preset library | The driving signal | Canvas with edit tools |
| Impulse Response h[n] | Graphical editor or preset library (e.g., decay, pulse) | The system's characterization | Canvas with edit tools |
| Output Index n | 0 to max(support) | Which output sample to compute | Slider with real-time update |
| View Mode | {step-by-step, animated, 3D surface} | How to visualize the computation | Radio/tab selection |
| Display Format | {DT only, DT+CT overlay} | Show discrete and continuous analogs | Checkbox |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|---------------|---------|
| x[k] Plot | Blue line plot of input | Input signal (constant) |
| h[-k] (flipped) | Red line plot, reflected about k=0 | Shows the flip operation |
| h[n-k] (shifted) | Red line plot, horizontally shifted by n | Shows shift operation synchronously |
| Pointwise Product | Purple/overlaid region under product curve | x[k] × h[n-k] for each k |
| Accumulated Sum | Green shaded area or bar showing running integral/sum | Visual accumulation to y[n] |
| Full Convolution Output | Black line plot, grows as n slider moves | Entire output builds up |
| 3D Surface (optional) | 2D heatmap or 3D surface: y[n] as function of (x, h) shapes | Shows how output depends on both signals |

### Visualization Strategy
**Interactive narrative:**
1. User places x[n] on the canvas: e.g., a triangle-shaped pulse [1,2,1]
2. User places h[n]: e.g., a decay [1, 0.5, 0.25]
3. Click "Animate Convolution" or manually slide n=0→max
4. At n=0:
   - Input x[k] displays in blue from k=-∞ to ∞
   - h[k] flips to h[-k] (mirrored, shown in red)
   - Overlay with shift at n=0: h[0-k] = h[-k]
   - Product x[k]·h[-k] shows as filled area
   - Integral/sum = y[0] displays as a number and on the output plot
5. Slide to n=1:
   - h[-k] shifts right by 1 to become h[1-k]
   - Product x[k]·h[1-k] updates
   - y[1] computed and plotted
6. Repeat for all n
7. Final output y[n] is complete

**Aha moments:**
- "Flipping h is the key step—it doesn't commute, so convolution order matters algebraically"
- When supports don't overlap, y[n] = 0 (product is zero everywhere)
- Output length = input length + impulse response length - 1
- Smooth inputs and sharp impulses produce correspondingly smooth outputs

### Implementation Notes
**Complexity:** Medium
**Key Algorithms:**
- Graphical signal editor: 2D canvas with draggable points, interpolation (cubic spline or linear)
- Convolution computation: NumPy correlate or manual sum for pedagogical clarity
- Animation timing: Plotly or custom Canvas rendering with frame updates
- 3D heatmap: discretize (x shape, h shape) space; compute y for each pair; render with Plotly
- CT convolution overlay: scipy.integrate.quad for reference computation

**Dependencies:** NumPy, SciPy (interpolation, integration), Plotly.js (2D/3D plots), Canvas API or Three.js (interactive signal editor)

### Extension Ideas
**Beginner:** Predict the support (non-zero region) of y[n] = x[n] ∗ h[n] before computing.

**Advanced:** Convolve two smooth Gaussians; observe that the output is sharper (narrower support) than either input. Explain using frequency domain (convolution → multiplication in Fourier space).

**Real-world:** Image blurring—upload a 2D image and a 2D blur kernel (PSF); visualize 2D convolution in action (with 2D slider controls or 3D surface plot of the computation).

---

## Simulation: Pole-Zero Interactive Frequency Response Builder
### Lecture Source: Lecture 9, Pages 200-1567
### Learning Objective
Master frequency response by directly manipulating poles and zeros in the s-plane and observing the resulting magnitude and phase plots. This is the most direct path to internalizing the vector diagram method and the relationship between pole-zero locations and frequency response shapes (notches, peaks, roll-off).
### Theoretical Foundation
**Key equations:**

Magnitude: $|H(j\omega)| = |K| \frac{\prod_i |\omega - z_i|}{\prod_j |\omega - p_j|}$

Phase: $\angle H(j\omega) = \angle K + \sum_i \angle(\omega - z_i) - \sum_j \angle(\omega - p_j)$

Vector diagram: Each zero/pole contributes a vector from its location to the point $s = j\omega$ on the imaginary axis.

**Related concepts:** Bode plots; resonance; bandwidth; notches and peaks; eigenfunction property of complex exponentials

### System Architecture
**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|-----------|
| Poles | 2D canvas in s-plane | System dynamics; location determines response shape | Draggable points |
| Zeros | 2D canvas in s-plane | Numerator zeros; create notches | Draggable points |
| DC Gain K | 0.1 to 10 | Magnitude scaling | Slider |
| Add/Remove | buttons | Interactively build/modify system | +/- buttons + click canvas |
| Frequency Range | [0.01, 100] rad/s (or Hz) | Bandwidth to visualize | Slider pair (min, max) |
| Pole/Zero Pair Option | conjugate pair vs. real | Force conjugacy for complex poles | Checkbox |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|---------------|---------|
| S-Plane Diagram | 2D plot with poles (×) and zeros (○) interactively draggable | Spatial intuition |
| Magnitude Response | Log-log or linear-log Bode magnitude plot | Shows gain vs. frequency |
| Phase Response | Semilog phase plot in degrees or radians | Shows phase shift vs. frequency |
| Vector Diagram (real-time) | Arrows from poles/zeros to current j𝜔 point on imaginary axis | Live vector magnitude/angle computation |
| 3D Surface Optional | 3D plot of |H(j𝜔)| colored by frequency; viewable from s-plane angle | Holistic magnitude visualization |
| Step/Impulse Response | Time-domain plot showing system response | Causality and stability check |

### Visualization Strategy
**Primary workflow:**
1. Start with empty s-plane
2. User clicks to place a pole at, e.g., s = -1
   - Magnitude plot immediately shows a lowpass-like response with peak at DC
   - Phase plot shows -90° rotation from 0 to high frequency
3. User drags the pole left: cutoff frequency increases; response sharpens
4. User drags pole downward (away from real axis): system becomes underdamped; magnitude peak emerges (resonance!)
5. User adds a conjugate pole: biquad resonant system appears
6. User adds a zero directly above a pole: "notch filter" created—magnitude dips at that frequency
7. At any time, user can hover over frequency axis and see the vector diagram update: arrows from all poles/zeros to the current j𝜔 point, showing exactly how they contribute to magnitude and phase
8. User toggles to 3D view: sees the magnitude surface over the jω axis; poles create "pits" (peaks at resonance), zeros create "hills" (nulls)

**Aha moments:**
- Poles near the jω axis → large magnitude (resonance)
- Zeros on the jω axis → magnitude exactly zero (notch)
- Moving a pole toward jω from left side → magnitude peak moves up and rightward
- A pair of complex conjugate poles creates a "tunable resonance" as you vary the real part and imaginary part independently
- Phase response is cumulative: each pole contributes -90° asymptotically

### Implementation Notes
**Complexity:** High
**Key Algorithms:**
- Frequency response computation: Evaluate H(jω) for ω in range via rational function evaluation (roots and residues, or direct formula)
- Vector diagram: Compute vectors from each zero/pole to current jω
- 3D magnitude surface: Create meshgrid in (σ, ω) space; evaluate |H(σ + jω)|; render with Plotly surface
- Stability check: Verify all poles have Re(s) < 0
- Conjugate pair enforcement: If user drags a pole, automatically update its conjugate twin

**Dependencies:** NumPy, SciPy (signal.TransferFunction for impulse/step response), Plotly.js (interactive Bode + 3D surface), custom Canvas or SVG for s-plane editor

### Extension Ideas
**Beginner:** Design a simple lowpass filter by placing poles; measure -3dB bandwidth.

**Advanced:** Design a band-pass filter with 2 zeros and 4 poles; optimize pole positions to achieve a flat passband and steep roll-off.

**Real-world:** Audio equalizer—load a measured room frequency response (with peaks from resonances); place zeros to cancel problematic peaks; listen to the equalized signal in real-time (if audio output is feasible).

---

## Simulation: Feedback Control Loop Stabilization Game
### Lecture Source: Lecture 10, Pages 204-1100
### Learning Objective
Discover hands-on how feedback gain affects closed-loop pole locations, stability, and response speed. Most students find control system design abstract; this game makes it concrete: move a slider, watch poles move in real-time, and instantly see whether the system remains stable.
### Theoretical Foundation
**Key equations:**

Closed-loop pole location: $z = 1 + KT$ (from wallFinder system example)

More generally: closed-loop poles are roots of $1 + K \cdot H(s) = 0$ (characteristic equation)

**Stability criterion:** All closed-loop poles must lie in the left half-plane (CT) or inside unit circle (DT).

**Optimal control:** Fastest response without instability occurs when poles are positioned optimally (often at critical damping).

**Related concepts:** Pole-zero cancellation; feedback stability; delay and its destabilizing effect; PID control foundations

### System Architecture
**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|-----------|
| Proportional Gain K | -10 to 10 | Feedback strength; larger K → faster response but risk of instability | Slider |
| System Plant | {First-order (leaky tank), Second-order (mass-spring), Integrator} | The system being controlled | Selection menu |
| Sensor Delay | 0, 1, 2 time steps | How much delay in measurement feedback | Slider or steps |
| Setpoint/Reference | 0 to 10 units | Target value for system output | Slider or input field |
| Disturbance | 0 to 3 units | External load/noise to reject | Slider |
| View Mode | {pole-zero, step response, locus, real-time sim} | Different insights into system behavior | Tabs |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|---------------|---------|
| Closed-Loop Pole Locations | Z-plane (DT) or s-plane (CT) diagram with poles as points; color codes stability | Real-time feedback on stability |
| Root Locus | Curve showing how poles move as K varies from 0 to max | Strategic view: "What K values keep poles inside unit circle?" |
| Step Response | Time-domain plot of setpoint tracking | Intuition: oscillation, overshoot, settling time |
| Stability Indicator | Large green "STABLE" or red "UNSTABLE" badge + max safe K value | Immediate feedback |
| Error vs. Time | Plot of (setpoint - actual output); decreases or oscillates | Shows tracking quality |
| Pole Speed Vector | Arrows indicating pole motion direction as K increases | Anticipate instability before crossing boundary |

### Visualization Strategy
**Gameplay narrative:**
1. System presented: "Your job: make this leaky tank reach its setpoint as fast as possible without oscillating forever."
2. Initial state: K = 0 (no feedback), pole at z = 1 (marginally stable; no motion)
3. User slides K slightly negative (e.g., K = -0.5):
   - Pole moves into unit circle at z = 0.9
   - Step response shows slow exponential approach to setpoint
   - "You're stable, but slow. Can you do better?"
4. User increases K magnitude (K = -1):
   - Pole jumps to z = 0 (instant response in 1 step!)
   - Step response reaches setpoint in exactly 1 step
   - "Perfect! You've achieved dead-beat control!"
   - Display: "Fastest possible response for this system"
5. User overshoots to K = -2:
   - Pole exits unit circle on left side at z = -1.1
   - Step response oscillates and diverges
   - Red "UNSTABLE" label appears
   - Root locus shows the pole's path exiting the circle
6. User reduces K back to safe range, watches pole re-enter stable region
7. **Challenge mode:** Add sensor delay (1 step). Pole locus changes shape; K = -1 no longer stabilizes. User must find new optimal K (e.g., K = -0.25). Discover: delay makes it harder to control!
8. **Hard mode:** Second-order system (mass-spring-damper). Two poles. User sees complex locus as both poles move together; one always exits first (dominates stability). Teach dominating pole concept.

**Aha moments:**
- Pole location = response speed/stability trade-off
- Delay shifts the locus → smaller stable K range → slower achievable response
- Dead-beat control: pole at origin
- Oscillations: complex poles with non-zero imaginary part
- "Why can't I make this any faster without becoming unstable?" → Delay fundamental limit

### Implementation Notes
**Complexity:** High
**Key Algorithms:**
- Closed-loop characteristic equation derivation from plant + controller + delay block diagram
- Root finding: NumPy/SciPy roots() for characteristic polynomial
- Root locus generation: Sweep K, solve characteristic equation for each K, plot all poles
- Step response: System transfer function + inverse Laplace (analytical or numerical)
- Pole motion direction: Derivative of pole location w.r.t. K (numerical or analytical)

**Dependencies:** NumPy, SciPy (signal, optimize for root finding), Plotly.js (interactive z-plane + root locus), Matplotlib or custom Canvas for real-time updates

### Extension Ideas
**Beginner:** "Find the K that stabilizes the system with 1-step delay." (Intended K range: roughly -0.25 to -0.1)

**Advanced:** Implement a PI (proportional-integral) controller: $u[n] = K_p e[n] + K_i \sum_0^n e[\tau]$. See how adding integral action allows zero steady-state error and shifts the root locus.

**Real-world:** Cruise control system—user plays as the control engineer, tuning K to smoothly approach a speed limit despite disturbances (wind, hill). Excessive K → oscillation (uncomfortable for passengers); too low K → sluggish response.

---

## Simulation: Eigenfunction Resonance Frequency Predictor
### Lecture Source: Lecture 9, Pages 252-321
### Learning Objective
Develop intuition for why complex exponentials are eigenfunctions of LTI systems and how this property enables frequency response analysis. Many students memorize $e^{st}$ without understanding *why* it matters. This simulation makes it concrete: input a complex exponential, watch it scale by the eigenvalue, and discover that the magnitude and phase of the eigenvalue predict the system's frequency response.
### Theoretical Foundation
**Key insight:** If $x(t) = e^{st}$, then $y(t) = H(s) e^{st}$ (eigenfunction property).

For $x(t) = \cos(\omega_0 t)$, the output magnitude is $|H(j\omega_0)|$ and phase shift is $\angle H(j\omega_0)$.

**System function representation:**
$$H(s) = \frac{N(s)}{D(s)} \text{ (rational function)}$$

**Related concepts:** Eigenvalues; modal decomposition; natural frequencies; forced vs. natural response

### System Architecture
**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|-----------|
| System (Transfer Function) | Rational function (numerator/denominator polynomials) or preset library | LTI system to excite | Editable text field or preset buttons (lowpass, resonator, etc.) |
| Input Frequency ω₀ | 0.1 to 10 rad/s | Which eigenfrequency to test | Slider |
| Input Type | {real exponential $e^{-\alpha t}$, complex exponential $e^{j\omega t}$, cosine $\cos(\omega t)$} | Eigenfunctions vs. real signals | Radio buttons |
| Time Window | 0 to 10 seconds | How long to simulate response | Slider |
| Initial Condition | 0 or system-dependent | Natural response vs. forced response | Checkbox |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|---------------|---------|
| Input Signal x(t) | Animated line plot or static curve | The driving eigenfunction |
| Output Signal y(t) | Animated line plot synchronized with input | System's response (scales by H(s)) |
| Eigenvalue H(jω₀) | Complex number displayed as magnitude and phase | The scaling factor |
| Magnitude Comparison | Text or bar chart: input magnitude vs. output magnitude | Shows |H(jω₀)| directly |
| Phase Shift Indicator | Arc or angle display showing phase difference between input and output | Shows ∠H(jω₀) visually |
| Frequency Response at ω₀ | Highlighted point on magnitude and phase plots | Shows where current frequency sits on response curves |
| Pole-Zero Diagram | S-plane with poles, zeros, and current frequency marked on jω axis | Explains eigenvalue via vectors |
| Natural Response | Dashed curve overlaid on forced response | Contrast: eigenfunction is purely forced response |

### Visualization Strategy
**Guided discovery:**
1. Start with a simple system: $H(s) = \frac{1}{s+1}$ (first-order lowpass)
2. Set input frequency ω₀ = 0 (DC, real exponential $e^{0 \cdot t} = 1$)
   - Output instantly settles to scaled DC value
   - Magnitude of H(j·0) = |H(0)| = 1
   - Phase is 0° (no shift at DC)
   - Display: "DC passes through unchanged"
3. Increase ω₀ to 1 rad/s:
   - Input becomes $\cos(t)$
   - Output becomes $|H(j)| \cos(t + \angle H(j))$ where $|H(j)| \approx 0.707$ and $\angle H(j) \approx -45°$
   - Visual: output shrinks and lags input by 45°
   - Display the complex number $H(j) = 1/(1+j) = 0.5 - 0.5j$
4. Drag ω₀ upward: output magnitude decreases, phase lag increases toward -90°
5. Switch input type to "complex exponential $e^{j\omega_0 t}$":
   - Input is a rotating vector in the complex plane
   - Output is the same vector rotated and scaled by $H(j\omega_0)$
   - Highlight: the system doesn't change the frequency, only the amplitude and phase
6. Overlay the pole-zero diagram: show the vector from pole at s = -1 to current point $j\omega_0$
   - As ω₀ increases, vector length decreases (magnitude), angle changes (phase)
   - Explain: $|H(j\omega)| = 1/|j\omega - (-1)|$

**Aha moments:**
- Input and output have *same* frequency (eigenfunction property)
- The system's magnitude and phase at a frequency are completely determined by pole-zero geometry
- DC response often very different from high-frequency response (example: highpass filters)
- Pole near the jω axis → large magnitude at that frequency (resonance)

### Implementation Notes
**Complexity:** Medium
**Key Algorithms:**
- Rational transfer function evaluation at complex s
- ODE solver (scipy.integrate.odeint) for time-domain response simulation with initial condition
- Eigenfunction generation: parametric $\cos(\omega_0 t)$ or $e^{j\omega_0 t}$
- Pole-zero diagram with geometric vectors (matplotlib or Plotly)
- Real-time animation syncing input and output

**Dependencies:** NumPy, SciPy (odeint, signal), Plotly.js or Matplotlib (animated plots)

### Extension Ideas
**Beginner:** Predict magnitude and phase at a frequency before running simulation; compare prediction vs. actual.

**Advanced:** Load a system with multiple poles; observe that at low frequency, all poles contribute equally to the response; at high frequency, distant poles become negligible (high-frequency asymptote).

**Real-world:** Seismic isolation—explain why buildings are designed to have natural frequencies (poles on jω axis) far from typical earthquake frequencies; input earthquakes with various frequencies, watch magnitude response, and see why tall buildings are more vulnerable to low-frequency quakes.

