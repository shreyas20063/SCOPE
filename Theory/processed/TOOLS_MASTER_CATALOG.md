# Interactive Tools Master Catalog
## Signals & Systems Web Textbook — Tool-Level Simulations

---

## Philosophy

These are **TOOLS**, not demos. Students build, construct, solve, and discover. Like mini-Simulink, mini-MATLAB experiences. Unlike passive slider-based simulations, these tools embed **active learning paradigms**:

- **Builder**: Compose systems from elements (poles, zeros, harmonics, signal components)
- **Explorer**: Manipulate rich multi-panel environments with real-time dual-domain feedback
- **Challenger**: Solve design problems, identify unknowns, predict then verify
- **Pipeline**: Connect processing stages end-to-end and watch data flow through
- **Workbench**: Open-ended experimentation with immediate visual consequences

Each tool is pedagogically grounded in specific MIT 6.003 lecture sequences. Each makes visible what is normally invisible (Fourier transforms, pole migration, spectral folding, sinc interpolation). Each includes prediction-then-verification mechanics to build intuition.

---

## Executive Summary

**Total unique tools: 25**

Distributed across 5 lectures ranges:
- **Lectures 01-09** (Time/Discrete Systems): 8 tools
- **Lectures 10-18** (Frequency Response, Control, Filtering): 8 tools
- **Lectures 19-25** (Sampling, Modulation, Applications): 6 tools
- **Integrated/Cross-Cutting**: 3 synthesis tools

### Categorized by Interaction Type

**Builder Tools** (students construct systems from components)
- Bode Plot Constructor
- Pole Migration Dashboard
- Fourier Series Harmonic Decomposer
- Fourier Domain Navigator
- Modulation & Demodulation Studio
- Block Diagram Assembly Station
- Transfer Function Design Workbench

**Explorer Tools** (students manipulate parameters in rich multi-panel environments)
- Fourier Transform Explorer
- Discrete-Time Pole/Zero Explorer
- Sampling Rate Explorer with Spectral Folding
- Bode Plot + Root Locus Combined Controller Design Studio
- Aliasing Discovery Lab
- Interactive Feedback Stability Debugger
- Fourier Filter Inspector

**Challenge Tools** (students solve problems, identify unknowns)
- System Identification from Response
- Pole Assignment Challenges
- Filter Design Challenges
- Aliasing Prediction Workbench
- Modulation Encoding/Decoding

**Pipeline Tools** (students connect processing stages end-to-end)
- Sampling & Reconstruction Pipeline
- CD Audio Processing Pipeline
- Complete LTI System Analysis Chain
- Signal Path Debugging Workbench

**Workbench Tools** (open-ended experimentation)
- Leaky Tank Simulator with Continuous/Discrete Modes
- Custom Signal Laboratory
- Real-World System Emulator

---

## Master Index

| # | Tool Name | Lectures | Interaction Type | What Students DO | Complexity | Priority |
|----|-----------|----------|------------------|------------------|------------|----------|
| 1 | Leaky Tank Simulator | 01-03 | Explorer | Drag tank → see time/discrete evolution | Low | Tier 1 |
| 2 | System Identification from Response | 02-03 | Challenge | Measure step response → deduce system order/poles | Medium | Tier 2 |
| 3 | Continuous/Discrete Equivalence Inspector | 04-06 | Explorer | Draw CT signal → see DT approximation | Medium | Tier 2 |
| 4 | Pole-Zero Magnitude/Phase Visualizer | 07-09 | Builder | Place poles/zeros → see magnitude/phase response | Medium | Tier 1 |
| 5 | Bode Plot Constructor | 10-11 | Builder | Drag poles/zeros → asymptotes build in real-time | Medium | **Tier 1** |
| 6 | Pole Migration Dashboard | 11-12 | Explorer | Slide K → watch poles move + step response evolve | Medium | **Tier 1** |
| 7 | Fourier Series Harmonic Decomposer | 14-15 | Builder | Adjust harmonics → signal reconstructs | Low-Medium | **Tier 1** |
| 8 | Fourier Transform Explorer | 16 | Explorer | Stretch/shift signal → spectrum morphs | Medium | Tier 2 |
| 9 | Bode + Root Locus Combined Designer | 10-12 | Pipeline | Build controller C(s) → see Bode + locus + response | High | Tier 2 |
| 10 | Discrete-Time Pole/Zero Explorer | 11, 18 | Builder | Place poles in z-plane → impulse response appears | Medium | Tier 2 |
| 11 | Interactive Feedback Stability Debugger | 11 | Challenge | Design K for robot → predict stability then verify | Medium | Tier 1 |
| 12 | Fourier Filter Inspector | 15 | Explorer | Adjust cutoff → see harmonics pass/block | Medium | Tier 2 |
| 13 | Fourier Domain Navigator | 19 | Builder | Drag signal between four representations | Medium | **Tier 1** |
| 14 | Aliasing Discovery Lab | 21 | Challenge | Compose frequencies → predict aliases → verify | Medium-High | **Tier 1** |
| 15 | Sampling & Reconstruction Pipeline | 21-22 | Pipeline | Draw signal → sample → quantize → reconstruct | High | Tier 2 |
| 16 | Sampling Rate Explorer | 21 | Explorer | Slide fs → watch spectral copies approach | Medium | Tier 2 |
| 17 | Modulation & Demodulation Studio | 23-24 | Pipeline | Build AM/PM/FM transmitter/receiver | High | Tier 2 |
| 18 | CD Audio Processing Pipeline | 25 | Pipeline | Record → filter → sample → quantize → play | Very High | Tier 3 |
| 19 | Custom Signal Laboratory | 06, 16 | Workbench | Draw arbitrary signals → compute transforms | Low-Medium | Tier 2 |
| 20 | System Identification from Frequency Response | 10 | Challenge | Given Bode plot → design poles/zeros to match | Medium | Tier 2 |
| 21 | Transfer Function Design Workbench | 10, 12 | Builder | Edit H(s) directly → plots update live | Medium | Tier 2 |
| 22 | Block Diagram Assembly Station | 01-02 | Builder | Drag blocks → connect → simulate | Medium | Tier 1 |
| 23 | Complete LTI System Analysis Chain | 07-10 | Pipeline | Input signal → impulse response → frequency response | Medium | Tier 2 |
| 24 | Real-World System Emulator | 11-12 | Workbench | Model and control realistic systems (motor, robot) | High | Tier 3 |
| 25 | Signal Path Debugging Workbench | 14-16 | Challenge | Trace signal through processing pipeline → find error | Medium | Tier 3 |

---

## Tier 1: Must Build (Top Priority)

These tools have **maximum pedagogical impact with feasible implementation**. They directly encode lecture sequences and are self-contained. **Recommend starting here.**

### Tool 1: Leaky Tank Simulator with Continuous/Discrete Modes

**Lectures Covered**: 01-03

**Inspired By**: Lecture 01-03, sheets 04-06 showing leaky tank system with visual evolution of water level, "Check Yourself" challenges asking students to determine time constants from tank diagrams.

**What Students DO**
- Drag tank dimensions (height, cross-section) and drain hole size to vary system parameters
- Toggle between continuous-time (differential equation) and discrete-time (difference equation) representations
- Input a physical scenario ("1m³ tank with 2cm drain") and have the tool **auto-derive** the time constant τ and output equation
- Adjust sampling period T in discrete mode
- Run simulation and **predict** water height at time T, then verify
- **Compare side-by-side** CT step response vs DT step response for identical input profiles
- Watch convergence: as T → 0, DT response approaches CT response

**Tool Description**

Three-panel interactive environment:
1. **Tank diagram editor**: Drag handles to adjust tank dimensions, drain hole size. Real-time equation display: τ = A·h₀ / (2·g·A_hole)^0.5 (derived from Torricelli's law)
2. **Continuous-time solver**: Shows differential equation dh/dt = -g·A_hole / A · √h. Plot of h(t) updating as parameters change
3. **Discrete-time solver**: Shows difference equation h[n+1] = h[n] - (g·A_hole / A)·√h[n] · T. Overlay both CT and DT responses. Show error: |h_CT(nT) - h_DT[n]|

**Interaction Model**
- Slider for tank radius, height, drain hole diameter
- Slider for sampling period T (from 0.01 to 1.0 seconds)
- Button to auto-compute time constant and display equation
- Dropdown for input profile: step (opening drain fully), ramp, sinusoid
- Play/pause to animate tank emptying in real-time
- Checkbox to overlay CT and DT responses

**Key "Aha Moments"**
- "The tank empties faster as it gets shallower (nonlinear dynamics)"
- "Time constant τ depends on tank geometry: bigger cross-section → slower drain"
- "Discrete time with small T approximates continuous time well; large T introduces error"
- "The feedback loop—water height → pressure → flow rate—is encoded in the differential equation"

**Technical Architecture**

*Backend*:
- Solve nonlinear ODE numerically using SciPy.integrate.odeint
- Discrete-time: explicit Euler method h[n+1] = h[n] + dt·f(h[n])
- Return {id: "leaky_tank", plots: [{id: "h_t", data: [...], layout: {...}}, ...]}

*Frontend*:
- SVG or Three.js canvas for tank visualization (fills with blue color as h decreases)
- Plotly for h(t) and h[n] overlay
- Sliders for geometric parameters
- Real-time computation with debounce (150ms)

**Complexity**: Low

**Why This Isn't Generic**
This is not "adjust gain and watch output change." Students **build the system from physical parameters** and watch the continuous/discrete relationship emerge. It directly teaches that discrete approximation quality depends on sampling period—a concept that runs through the entire course.

---

### Tool 2: Pole-Zero Magnitude/Phase Visualizer

**Lectures Covered**: 07-09

**Inspired By**: Lecture 07-09 showing how poles and zeros in the s-plane relate to magnitude and phase response. Visual progression from s-plane geometry to frequency response plots.

**What Students DO**
- **Drag poles** (red X) and **zeros** (blue O) anywhere in the s-plane
- Watch **magnitude response** |H(jω)| and **phase response** ∠H(jω) update in real-time
- See how pole distance from jω axis → magnitude of response at that frequency
- See how pole angle on s-plane → phase rotation
- **Understand**: a pole at s = -a gives a peak in magnitude at ω ≈ a with -90° phase transition
- **Predict**: "If I move this pole left, magnitude response will..." then verify
- **Challenge mode**: "Place poles/zeros to achieve magnitude peak at 5 rad/s"

**Tool Description**

Three-panel layout:
1. **S-plane editor**: Drag poles (X) and zeros (O). Gain K adjustable with dB slider. Show pole locations as text coordinates
2. **Magnitude response**: |H(jω)| in dB vs log ω. Real-time overlay of actual curve (from s-plane) + straight-line approximation (vector magnitude from poles/zeros)
3. **Phase response**: ∠H(jω) in degrees vs log ω. Shows phase contributions per pole/zero

**Interaction Model**
- Click to add pole (X) or zero (O)
- Drag to move; constrain to left half-plane (with toggle)
- Right-click to delete
- Slider for gain K (dB)
- "Show vectors" button: draws magnitude/phase vectors from poles/zeros to a point on jω axis
- Frequency range zoom: pan/zoom on Bode plot to see details

**Key "Aha Moments"**
- "A pole contributes a 'bump' in magnitude; a zero a 'dip'"
- "Pole distance = bandwidth; pole angle = resonance sharpness"
- "Moving a pole closer to the jω axis increases magnitude at ω ≈ |s_pole|"
- "Zeros cancel poles: place a zero exactly on a pole → magnitude response has a notch"

**Technical Architecture**

*Backend*:
- Receive pole/zero locations {p_i}, {z_j} and gain K
- Evaluate H(s) = K·∏(s - z_j) / ∏(s - p_i) at s = jω for ω = logspace(-1, 3, 500)
- Return magnitude and phase arrays

*Frontend*:
- Canvas (Konva.js) for interactive s-plane
- Plotly for Bode plots
- Vector visualization: draw arrows from each pole/zero to cursor location on jω axis, showing magnitude and phase

**Complexity**: Medium

**Why This Isn't Generic**
This is the bridge from s-plane algebra to frequency-domain intuition. Students don't just see Bode plots; they **see where they come from** (pole/zero locations). This is prerequisite understanding for all frequency-response tools.

---

### Tool 3: Bode Plot Constructor

**Lectures Covered**: 10-11

**Inspired By**: Lecture 10 sheets 15-30. Systematic construction of Bode plots from poles and zeros. Multi-panel progression showing individual asymptotes, layered addition, transition from s-plane to log-log Bode plot.

**What Students DO**
- **Draw** individual asymptotes for given poles and zeros on a blank log-log grid
- **Compose** complete Bode plot by layering asymptotes (superposition principle)
- **Test** predictions: input a transfer function H(s) as poles/zeros, sketch Bode plot asymptotes by hand, then reveal actual plot for comparison
- **Refine**: adjust pole/zero locations and see real-time impact on magnitude and phase plots
- **Challenge mode**: given a target Bode plot (e.g., "flat 0 dB passband, -40 dB/decade rolloff after 10 rad/s"), design poles/zeros to match it

**Tool Description**

Three side-by-side panels:
1. **S-plane editor**: Drag poles (red X) and zeros (blue O) anywhere in the complex plane. Adjustable gain K with dB slider. Show contributing elements clearly
2. **Asymptotic plot workspace**: Initially blank log-log grid for magnitude (dB vs log ω) and linear grid for phase (degrees vs log ω). As student places poles/zeros, colored asymptotic segments appear in real-time, color-coded per element (red for pole, blue for zero). Show slope: -20 dB/decade per pole, +20 dB/decade per zero
3. **Actual frequency response**: Updated in real time, overlaid on asymptotic approximation. Show corners where actual curve deviates from asymptotes (±3dB points, resonance peaks for complex poles)

**Interaction Model**

*Drag-and-drop editor with constraint-based feedback*:
- Click to add pole (X) or zero (O) to s-plane
- Drag to move; magenta highlight shows real-time impact on asymptotic plot
- Right-click to delete
- Slider to adjust K (gain) in dB
- **Guided mode**: step-by-step construction of a known transfer function (e.g., Lecture 10 example H(s) = s / [(s+1)(s+10)])
  - Hint 1: "You need one zero at..."
  - Hint 2: "Add poles at..."
  - Reveal button: show actual Bode plot for comparison
- **Challenge mode**: given target Bode magnitude/phase profile, design poles/zeros to match; show "distance" metric between student's asymptotes and target

**Multi-Panel Layout**
```
┌──────────────────────────────────────────────────┐
│ Bode Plot Constructor                            │
├──────────────┬──────────────────┬────────────────┤
│  S-plane     │  Asymptotes      │  Actual        │
│  Editor      │  (Built-up sum)  │  Frequency    │
│              │                  │  Response     │
│ (drag poles  │ Magnitude (dB)   │ (Real curve   │
│  and zeros)  │   |              │  with 3dB pts)│
│              │   |╲             │   |           │
│              │   | ╲___         │   |╲╲         │
│              │   └─────────── ω │   └──╲___     │
│              │                  │              │
│ [Add] [Mode] │ Phase (°)        │ Overlay      │
│ [K slider]   │   |              │ accuracy     │
│              │   └─╲───         │              │
│              │     ╲─╱          │              │
│              │      ╲           │              │
└──────────────┴──────────────────┴────────────────┘
```

**Key "Aha Moments**
- "A pole at s = -a contributes -20 dB/decade slope starting at ω = a. This is just the logarithm of the magnitude response 1/(jω+a)"
- "Poles and zeros in the s-plane are vectors; their magnitudes and angles compose to give Bode plot"
- "Bode plot is a compressed view: log transforms multiplication into addition, so asymptotes just add"
- "Shape of Bode plot is determined entirely by pole/zero locations; gain K only shifts magnitude vertically"

**Technical Architecture**

*Backend*:
- Evaluate H(s) at user's chosen s-plane poles/zeros (σ + jω)
- Compute magnitude |H(jω)| and phase ∠H(jω) across ω = logspace(-2, 3, 500)
- Asymptotic approximations: for pole at -a, contribute -20 dB/decade for ω > a; for zero at -b, contribute +20 dB/decade for ω > b
- Phase contributions: piecewise-linear approximation per pole/zero (using arctan approximation for smoothness)
- Return: magnitude array, phase array, asymptotic magnitude array, asymptotic phase array

*Frontend*:
- Konva.js canvas for s-plane dragging
- Plotly for magnitude and phase plots with live updating (debounce 150ms)
- SVG overlays for asymptotic line segments (color-coded per pole/zero)
- Real-time overlay of actual H(jω) curve to show accuracy of asymptotic approximation
- Annotation: show asymptote slopes (e.g., "-20 dB/dec" label on each segment)

**Complexity**: Medium

**Why This Isn't Generic**
This is not "adjust a parameter and see a plot change." Students actively **construct knowledge**: each placement teaches vector magnitude/phase, the composition of logarithms, and the direct read-off from s-plane geometry to frequency response shape. Lecture 10 dedicates 10+ slides to this exact progression. **The tool encodes the pedagogical sequence into interaction.**

---

### Tool 4: Pole Migration Dashboard (Closed-Loop Control Design)

**Lectures Covered**: 11-12

**Inspired By**: Lecture 11-12 sheets on root locus—how poles move as control parameter (gain K) varies. Key visuals show wall-finder robot pole trajectories, pole collision points, oscillation behavior, settling time trade-offs.

**What Students DO**
- **Draw** pole trajectories on the s-plane as gain K is varied interactively
- **Predict**: at what K value do poles become unstable (cross jω axis)?
- **Connect**: understand relationship between pole location (σ, ω_d) and time-domain response (damping ratio ζ, natural frequency ω_n, settling time)
- **Solve challenges**: "Find K to place poles at σ = -2 for desired settling time"; "Find maximum K that keeps system stable"
- **Visualize**: simultaneously watch step response evolve in real-time as pole positions change
- **Compare**: adjust damping contours and natural frequency circles to see design trade-offs

**Tool Description**

Dual-panel interactive environment for root locus design:
- **Left panel (s-plane)**: Root locus plot showing open-loop poles/zeros and closed-loop pole trajectories. Horizontal slider for gain K that moves poles along locus
- **Right panel (step response)**: Step response of closed-loop system with annotations: settling time (2% criterion), percent overshoot, oscillation frequency
- **Overlays**: Stability boundary (jω axis, red). Optional damping ratio ζ contours (family of parabolas) and natural frequency ω_n circles

Teaches fundamental trade-off: increasing K moves poles (faster response, risk of oscillation/instability). Complex poles → oscillations; real poles → smooth approach.

**Interaction Model**

*Parameter sweep with dual feedback*:
- Horizontal slider for K from 0 to some maximum (or scan negative K for integral action)
- As slider moves, closed-loop poles trace paths on s-plane (root locus)
- Overlay: jω axis (red, stability boundary), optional ζ contours and ω_n circles (toggleable)
- Right panel: live step response (unit step input) with computed metrics: settling time, overshoot %, oscillation frequency
- **Marker mode**: click on locus to lock K at a specific value and freeze design
- **Animate mode**: play button to scan K from 0 to max while watching poles trace and response evolve
- Optional: Bode plot overlay showing gain margin and phase margin at current K

**Multi-Panel Layout**
```
┌────────────────────────────────────────────────┐
│ Pole Migration Dashboard                       │
├──────────────────┬───────────────────────────┤
│ S-plane Root     │ Step Response (Closed-Loop)│
│ Locus            │                            │
│                  │ y(t)                       │
│ jω               │  |                         │
│  ↑               │ 1├─────────────────         │
│  │   ×           │  │    settling time        │
│  │  / \          │  │ ↑ overshoot            │
│  │ /   \         │  │                        │
│ ─┼──────→ σ      │ 0├────────────────────── t │
│  │    ×O         │                            │
│  │                │ [Osc freq, settling]     │
│  │ [K slider]    │ [ζ, ωₙ values]           │
│  │ [ζ contours]  │                            │
│  │ [ωₙ circles]  │ [Gain margin, Phase margin]
└──────────────────┴───────────────────────────┘
```

**Key "Aha Moments**
- "Gain K moves poles along a fixed path (locus); I don't choose individual pole locations, only K (which slides along the path)"
- "Poles on jω axis = marginally stable = constant oscillation"
- "Complex poles → oscillatory response; real poles → smooth exponential approach"
- "Delay in feedback pushes locus to the right (destabilizes); larger K needed to stabilize → trade-off between latency and stability"

**Technical Architecture**

*Backend*:
- Input: open-loop system function G(s), control gain K
- Compute closed-loop poles: roots of 1 + K·G(s) = 0 for swept K values (e.g., linspace(0, 5, 100))
- Store pole trajectories (root locus)
- For each K, compute step response of closed-loop system using SciPy
- Extract: overshoot, settling time (2% criterion), oscillation frequency (imaginary part of complex poles)

*Frontend*:
- Plotly for s-plane scatter (poles) + line traces (locus)
- Overlay jω axis (red), optional ζ contours (SVG or Plotly), optional ω_n circles
- Plotly for step response plot
- Slider component for K with real-time plot updates
- Annotations: "Stable region" (left half-plane), "Unstable" (right half-plane)
- Display current metrics: K value, pole locations, settling time, overshoot %

**Complexity**: Medium-High

**Why This Isn't Generic**
This encodes the **root locus method**—a classical control design technique central to feedback system design. Students don't just see plots; they learn to **read** the s-plane as a prediction tool for transient response. Lectures 11-12 show exactly this progression: from pole equations to space-time diagrams to practical control design.

---

### Tool 5: Fourier Series Harmonic Decomposer

**Lectures Covered**: 14-15

**Inspired By**: Lecture 14-15 showing progressive synthesis of periodic signals from harmonics. Multi-slide progression building square and triangle waves from cumulative harmonic sums. Gibb's phenomenon, convergence rates, orthogonal decomposition.

**What Students DO**
- **Add** harmonic components one at a time, watching signal converge from a blank canvas
- **Adjust** amplitude of individual harmonics and see signal reshape
- **Predict**: which harmonics are most important for a given waveform shape (square → odd harmonics only; triangle → k^-2 decay)?
- **Compare**: square wave (infinite harmonics, slow convergence, ringing) vs triangle (faster k^-2 decay, smoother)
- **Challenge**: "Build a sawtooth wave by choosing harmonic amplitudes"
- **Hear**: optionally play audio of partial sums (musical note becoming more complex as harmonics added)
- **Explore Gibb's phenomenon**: add more harmonics and see ringing near discontinuities

**Tool Description**

Three-panel layout showing harmonic synthesis:
1. **Time-domain signal** (top): x(t) = Σ aₖ e^(jkω₀t), displayed as continuous line. Update in real-time as harmonics adjusted
2. **Harmonic editor** (bottom-left): Vertical slider strip for each harmonic k (0, 1, 2, ..., up to ~30). Each harmonic has:
   - Magnitude slider (amplitude aₖ)
   - Phase slider (angle of e^(jkω₀t))
   - Checkbox to toggle on/off
3. **Frequency spectrum** (bottom-right): Bar chart of |aₖ| vs k, showing which harmonics are "on" and their magnitudes

**Preset buttons**: "Square Wave", "Triangle", "Sawtooth", "Custom" load known Fourier coefficients. **Guided mode**: highlight which harmonics are "active" in a target signal, then students tune amplitudes to match.

**Interaction Model**

*Additive synthesis with live feedback*:
- Harmonic sliders: one per k (amplitude and phase)
- Checkboxes to toggle harmonics on/off
- Preset buttons load standard Fourier coefficients
- **Convergence display**: "Using 5 harmonics" → "Using 15 harmonics" etc., showing how many terms needed for good fit
- **Reconstruction error**: show SNR or MSE between current partial sum and target waveform
- **Audio playback**: button to play audio of partial sum (Web Audio API)
- **Show Gibb's phenomenon**: toggle to highlight ringing near discontinuities

**Multi-Panel Layout**
```
┌────────────────────────────────────────────────┐
│ Fourier Series Harmonic Decomposer             │
├────────────────────────────────────────────────┤
│ [Presets: Square | Triangle | Sawtooth | ...]  │
├────────────────────────────────────────────────┤
│ Time-Domain Signal (Synthesis)                 │
│                                                │
│ x(t) = Σ aₖ e^(jkω₀t)                         │
│  |                                             │
│  |    ╱╲  ╱╲  ╱╲   (converging to target)   │
│  └────────────────── t                        │
│ [Convergence: 15 harmonics used]              │
├────────────────────────────────────────────────┤
│ Harmonic Editor (left) │ Spectrum (right)      │
│                        │                       │
│ k=0: [━━●━━] ph [●] ✓  │ |aₖ|                 │
│ k=1: [━━●━━] ph [●] ✓  │  |                   │
│ k=2: [━━●━━] ph [●] ✓  │  | ■                 │
│ k=3: [━━●━━] ph [●] ✓  │  | ■  ■              │
│ ...                     │  | ■  ■  ■           │
│                         │  └─────────────── k  │
│ [Play audio]            │ [RMS Error: 0.05]   │
└────────────────────────────────────────────────┘
```

**Key "Aha Moments**
- "Any periodic signal is just a weighted sum of sinusoids; the weights (aₖ) determine the shape"
- "Square wave has only odd harmonics (k = 1, 3, 5, ...) with magnitude ~ 4/(πk); triangle drops as k^-2"
- "Adding more harmonics makes the signal sharper (especially at discontinuities) but introduces ringing (Gibb's phenomenon, overshoot ~9%)"
- "Harmonics are orthogonal: turning up k=3 doesn't change contribution of k=1. They're independent basis functions"

**Technical Architecture**

*Backend*:
- Fourier series: x(t) = Σ aₖ e^(j2πkt/T) for k = -N to +N
- Evaluate x(t) at high temporal resolution (1000+ points per period) for smooth display
- Magnitude spectrum |aₖ| = √(real²_k + imag²_k) from slider values
- Pre-compute Fourier coefficients for preset waveforms:
  - Square: aₖ = 4/(πk) for odd k, 0 for even k
  - Triangle: aₖ = 8/(π²k²) for odd k, 0 for even k
  - Sawtooth: aₖ = 2/(πk)
- Optional: audio synthesis at 44.1 kHz sample rate
- Compute RMS error: √(∫|x_target - x_partial|² dt / T)

*Frontend*:
- React sliders for each harmonic amplitude and phase
- Plotly for time-domain signal (high-resolution line plot, 1000+ points)
- Plotly for frequency spectrum (stem/bar chart)
- Real-time update as any slider moves (debounce 150ms)
- Toggle harmonics on/off via checkboxes (gray out contribution to signal visually)
- Web Audio API for audio playback (resample to 44.1 kHz)

**Complexity**: Low-Medium

**Why This Isn't Generic**
This directly encodes **Fourier decomposition** as a student activity: seeing how signals emerge from harmonic sums. Lecture 14's 30-slide sequence of building square and triangle waves from incrementally added harmonics is pedagogically crying out for an interactive version. Students build muscle memory for which harmonics matter, and audio feedback makes it visceral (a square wave "sounds" very different from a triangle).

---

### Tool 6: Fourier Domain Navigator

**Lectures Covered**: 19

**Inspired By**: Lecture 19 showing the four Fourier representations as a 2×2 grid with transformation arrows. "Relations among Fourier Representations" diagram showing sampling ↔ spectral replication and periodic extension ↔ frequency sampling.

**What Students DO**
- **Drag a signal** in any of the four domains and watch all four update automatically
- **Click transformation arrows** to trigger sampling, periodic extension, interpolation
- **Watch domains morph** in real-time as they adjust signal properties (period T, sampling rate fs, signal duration)
- **Build intuition** about which representation reveals signal structure
- **Construct** their own signals in one domain and see what emerges in the other three
- **Understand** that the four representations are not separate tools—they're different lenses on the same signal

**Tool Description**

A four-panel interactive workspace where students explore **duality between time/frequency and continuous/discrete**. Central mechanic: **dragging a manipulable signal in any domain automatically updates the other three**.

Panel layout (2×2 grid):
- **Top-left**: CT Fourier Series (periodic time, discrete frequency) — CTFS: x(t) = Σ aₖ e^(j2πkt/T)
- **Top-right**: CT Fourier Transform (aperiodic time, continuous frequency) — CTFT: x(t) ↔ X(jω)
- **Bottom-left**: DT Fourier Series (periodic discrete time, periodic frequency) — DTFS: x[n] = Σ aₖ e^(j2πkn/N)
- **Bottom-right**: DT Fourier Transform (aperiodic discrete time, periodic frequency) — DTFT: x[n] ↔ X(e^jω)

Each panel has:
- Animated signal/spectrum plot (time and frequency side-by-side)
- Draggable control points to shape signal
- Sliders for period T, sampling rate fs, period length N
- Parameter read-outs: ω₀ = 2π/T, Ω = ωT, frequency spacing, aliasing indicators

**Interaction**: Drag a control point in any plot → all four update. Change T or fs → watch spectral spacing adjust. Draw a signal in time domain → see frequency content appear automatically in all four frequency domains.

**Multi-Panel Layout**
```
┌────────────────────────────────────────────────────────┐
│ Fourier Domain Navigator                               │
├──────────────────────┬────────────────────────────────┤
│ CT Fourier Series    │ CT Fourier Transform           │
│ (Periodic time)      │ (Aperiodic time)               │
│ [plot + draggable]   │ [plot + draggable]             │
│                      │                                │
│ ↓ aperiodic extend   │ ↓ sampling (÷T) ↓             │
├──────────────────────┼────────────────────────────────┤
│ DT Fourier Series    │ DT Fourier Transform           │
│ (Periodic discrete)  │ (Aperiodic discrete)           │
│ [plot + draggable]   │ [plot + draggable]             │
│                      │                                │
│ ↑ limit N→∞ ↑        │ ↑ interpolate ↑               │
└──────────────────────┴────────────────────────────────┘
Sliders: Period T | Sampling Rate fs | Window N
Read-outs: ω₀ = 2π/T, Ω = ωT, Δω = 2π/N, Δf = fs/N
```

**Key "Aha Moments**
1. **Sampling in time = replication in frequency.** Drag sampling rate slider down → watch spectral copies get closer → approaching Nyquist.
2. **Periodic extension = frequency sampling.** Make a signal periodic → frequency spectrum snaps to discrete impulses.
3. **Four representations are the same signal.** Modify one → all four change together. Pick whichever view makes the problem easiest.
4. **Relationships between parameters are not abstract.** Ω = ωT is not a formula—watch it happen live as you adjust fs.
5. **Limit behavior.** As N→∞, DTFS becomes DTFT. As T→∞, CTFS becomes CTFT.

**Technical Architecture**

*Backend*:
- Accept time-domain samples x[n] or parametric signal (sum of sinusoids, chirp, pulse, etc.)
- Compute all four representations from user-drawn signal:
  - CTFS: assume user's signal is one period of a periodic signal
  - CTFT: assume user's signal is aperiodic (pad with zeros)
  - DTFS: take samples, treat as periodic
  - DTFT: take samples, treat as aperiodic
- Return four sets of {id, title, data[], layout} for Plotly
- Handle aliasing visualization (spectral copies overlap warning)
- DataHandler serializes NumPy FFTs and frequency grids

*Frontend*:
- Split-pane layout with 2×2 Plotly plots
- Draggable control points on time-domain plots (x[n] or x(t))
- Sliders: T (period), fs (sampling rate), N (DT period length)
- Real-time computation + debounce (150ms)
- Synchronized zoom/pan across all four panes (uirevision sync)
- Read-out panel showing ω₀, Ω, Δω, Δf, fs, f_Nyquist, relationship equations

**Complexity**: Medium. Requires FFT computation for all four transforms, careful alignment of frequency axes, handling edge cases (very small/large T, fs near Nyquist).

**Why This Isn't Generic**
This is not "adjust slider, see plot change." It's a **constraint-based explorer** where each of the four domains is a valid "view" of the same signal; changes ripple across all four. This directly addresses Lecture 19's central claim: the four Fourier representations are not separate tools—they're different lenses on one underlying structure. Students don't memorize the four formulas; they **see why they're equivalent**.

---

### Tool 7: Aliasing Discovery Lab

**Lectures Covered**: 21

**Inspired By**: Lecture 21 showing extensive aliasing diagrams with spectral copies wrapping around ±ωs/2. Frequency mapping diagrams, anti-aliasing filter, music aliasing demonstration.

**What Students DO**
- **Compose a multi-frequency signal** by adding sinusoids at user-chosen frequencies (draggable on frequency axis)
- **Choose sampling rate** (slider to adjust fs)
- **Watch frequencies "wrap"** in real-time; anything above Nyquist folds back down
- **Predict aliases** before seeing them: "If I sample at 44.1 kHz, will a 100 kHz tone alias to 22 kHz?" Check by clicking button
- **Experiment with anti-aliasing filters** (drag cutoff frequency, see how it prevents wrapping)
- **Design a filter** to remove high frequencies before sampling
- **Challenge mode**: Given a downsampled signal, reverse-engineer the original by identifying which frequencies aliased

**Tool Description**

Highly interactive sandbox for exploring aliasing. Students build a signal from sinusoid components (draggable frequency sliders), set a sampling rate, and **watch frequency components map to their aliases in real-time**. Key mechanic: **sliding the sampling rate** causes frequencies to "slide along the frequency axis" as aliases appear and disappear.

Visualizes:
1. **Input spectrum** (before sampling): all components shown as vertical lines
2. **Sampling impulse train in frequency** (periodically spaced copies centered at integer multiples of fs)
3. **Output spectrum** (after sampling): the "folded" version where any frequency outside [-fs/2, fs/2] wraps back into passband
4. **Frequency mapping plot**: 2D diagram showing input frequency (x-axis) → output frequency (y-axis) with wrap-around geometry

Students can:
- Draw sinusoid frequencies by clicking on frequency axis (adds a component)
- Drag frequency markers to change them
- Drag Nyquist frequency slider (adjusts fs)
- Toggle anti-aliasing filter on/off (shows LPF before sampling)
- Play audio samples to hear aliasing distortion

**Multi-Panel Layout**
```
┌────────────────────────────────────────────────────────┐
│ Aliasing Discovery Lab                                 │
├────────────────────────────────────────────────────────┤
│ Input Signal Spectrum (add sinusoids by clicking)      │
│ [Frequency axis: 0 to 200 kHz, markers draggable]     │
│ │ o │    o     │        o          │                  │
│ │ 5│    47 │        100│           │                  │
├────────────────────────────────────────────────────────┤
│ After Sampling at fs = [slider 0-220 kHz]             │
│ │ o │    o     │        o          │                  │
│ │ 5│    47 │        100→44 (alias) │                  │
│                                                        │
│ Predicted aliases:    ☐ 5 kHz       ☑ 44 kHz         │
│ Click [Show] to verify → updates output spectrum     │
├────────────────────────────────────────────────────────┤
│ Frequency Mapping (input → output after sampling)      │
│ y=x (no wrap) vs. y = |x mod fs, fold at fs/2|        │
│ [2D plot showing wrapping geometry]                   │
├────────────────────────────────────────────────────────┤
│ ☐ Enable Anti-Aliasing Filter (cutoff = [slider])     │
│ [Shows LPF magnitude response overlaid on input]       │
├────────────────────────────────────────────────────────┤
│ Audio: [Play original] [Play sampled] [Play alias]    │
└────────────────────────────────────────────────────────┘
```

**Key "Aha Moments**
1. **Nyquist isn't magic; it's geometry.** Dragging fs slider shows frequencies literally wrapping around at Nyquist. Makes "folding" physically intuitive.
2. **Anti-aliasing is essential.** Toggle the LPF on/off → watch high-frequency components disappear before they can alias. Audio quality transforms.
3. **Aliasing is frequency modular arithmetic.** If fs = 44.1 kHz and you try to sample a 66 kHz tone, it wraps to 44.1 - 22 = 22 kHz. Makes the math concrete.
4. **You can construct indistinguishable signals.** Two completely different input signals can have identical samples if their frequency content differs by a multiple of fs.
5. **Prediction → verification loop.** Ask "Will a 100 kHz tone alias to 22 kHz at 44 kHz sampling?" Click check → immediate feedback.

**Technical Architecture**

*Backend*:
- Receive: list of sinusoid frequencies {f1, f2, ...}, amplitude, sampling rate fs
- Compute which frequencies alias to which output frequencies using folding formula:
  - If f < fs/2: output = f
  - If fs/2 < f < fs: output = fs - f
  - If f > fs: recursively apply wrapping rule
- Generate three spectrum plots: input, output, folding map
- Optionally apply LPF transfer function before computing aliases
- Synthesize audio: generate samples at fs, apply optional LPF, return WAV

*Frontend*:
- Interactive frequency axis: click to add sinusoid, drag to adjust frequency
- Large fs slider (horizontal) with visual Nyquist marker
- Real-time updates (debounce 150ms)
- Prediction input box: user types frequency → system computes alias, student confirms
- Audio playback of original and aliased signals (Web Audio API)
- Color coding: frequencies in passband (green), frequencies that will alias (red/orange)

**Complexity**: Medium-High. Requires accurate frequency wrapping logic, audio synthesis for playback, responsive UI for dragging/predicting.

**Why This Isn't Generic**
This tool makes aliasing **visceral and predictable**, not an abstract formula. Students see the geometry of wrapping, hear the aliasing distortion, and build mental models through prediction + verification. It's not a simulation of sampling; it's an **interactive algebra** of aliasing.

---

### Tool 8: Interactive Feedback Stability Debugger (Delay & Sensor Issues)

**Lectures Covered**: 11

**Inspired By**: Lecture 11 sheets 30-53 showing wall-finder robot with and without sensor delay. Dramatic visual progression showing how delay shifts pole locus toward instability.

**What Students DO**
- **Design** a proportional controller for a simple system (robot approach wall)
- **Toggle** sensor delay: 0, 1, 2, 3 samples
- **Adjust** gain K and see poles move on z-plane (closed-loop)
- **Predict**: at what K does the system oscillate? Become unstable?
- **Compare**: time-domain trajectory (position vs time) for different {K, delay} pairs
- **Solve**: "Find maximum K to keep system stable with 2-sample delay"
- **Visualize**: all consequences simultaneously—pole motion, stability boundary crossing, time-domain trajectory shape change

**Tool Description**

Four-panel environment:
1. **Block diagram**: P-D (proportional-delay) system with adjustable K and delay selector
2. **Z-plane pole map**: showing how poles move as K increases for fixed delay value
3. **Stability region**: shaded area (unit circle interior) vs unstable region
4. **Closed-loop step response**: position trajectory y[n] over time, with marked oscillations and settling time

Students adjust K and observe three consequences simultaneously: pole motion, stability boundary crossing, and time-domain trajectory shape change.

**Interaction Model**

*Control parameters*:
- Slider for proportional gain K (from 0 to 3, or user-adjustable range)
- Dropdown selector for sensor delay: 0, 1, 2, 3 samples
- Button to toggle "Zoom on poles" to see detail near unit circle
- Dropdown to switch between different plants: {integrator (velocity control), double integrator (position control), first-order lag (realistic system)}
- Play/pause button to animate K from 0 to max while watching poles trace locus
- Info panel showing: current K, pole locations, gain margin, stability status

**Multi-Panel Layout**
```
┌────────────────────────────────────────────────────┐
│ Feedback Stability Debugger                        │
├────────────────────────────────────────────────────┤
│ [System ▼] | Delay: [0] [1] [2] | K slider [●──]  │
├────────────────┬────────────────────────────────┤
│ Block Diagram  │ Z-plane (Root Locus)            │
│                │                                 │
│ ref ─┐  K      │ Im(z)                           │
│      ├──×──DT──┼──┐                              │
│ +   /  delay   │  |    ●● (poles, K increasing) │
│  \-/           │ ─┼──────→ Re(z)                 │
│      sensor    │  |    [unit circle]             │
│                │                                 │
└────────────────┴────────────────────────────────┘
│ Position Trajectory y[n]         Stability Status│
│ |y[n]                                            │
│  |  ╱╲                                           │
│  | ╱  ╲╲      (overshoot, oscillation)          │
│  │╱    ╲ ╲___                                    │
│  └────────────── n                              │
│                                                  │
│ [Settling time] [Peak overshoot] [Status: OK!]  │
└────────────────────────────────────────────────┘
```

**Key "Aha Moments**
- "Delay in feedback makes it harder to stabilize: sensor delay pushes the pole locus to the right"
- "More delay = smaller maximum stable gain: trade-off between control speed and latency"
- "At the stability boundary, poles hit the unit circle; any K increase → poles move outside → instability"

**Technical Architecture**

*Backend*:
- Model: θ[n+1] = θ[n] + K·e[n], where e[n] = ref[n] - y[n-d] (d-sample delay)
- Closed-loop: compute poles by finding roots of characteristic polynomial 1 + K·G_d(z) = 0 where G_d is plant with d-sample delay
- For each K, plot pole location; compute step response trajectory using simulation
- Detect stability: any pole with |z| ≥ 1.001?

*Frontend*:
- Plotly for z-plane (circle + poles + locus trace)
- Plotly for step response (stem or line plot of y[n])
- Sliders and dropdowns for K, delay, system selection
- Real-time update on parameter change

**Complexity**: Medium

**Why This Isn't Generic**
This directly addresses a common student misconception: "Why does delay break control?" The tool makes visible the abstract fact that sensor latency shifts the locus toward instability. Lecture 11 shows this is critical in robotics and other real-time systems.

---

## Tier 2: Should Build

These tools extend Tier 1 concepts and fill important pedagogical gaps. They are slightly more complex but highly valuable. **Implement after Tier 1 is stable.**

### Tool 9: Fourier Transform Explorer (Duality & Time-Frequency Trade-Off)

**Lectures Covered**: 16

**What Students DO**
- Draw or select a time-domain signal (pulse, Gaussian, exponential, chirp)
- Observe Fourier transform magnitude and phase in real-time
- Stretch or compress the signal in time, watching frequency spectrum compress or stretch
- Move signals in time (time shift), watching phase plot rotate
- Multiply by scale factors, watch magnitude scale
- Verify Parseval moment relationships: ∫x(t)dt vs X(j0), etc.

**Key Features**
- Dual-domain manipulator with draggable control points on time signal
- Sliders for: time scale a, time shift t₀, exponential damping e^(-αt)u(t)
- Real-time Fourier computation with linked zoom/pan
- Moment verification buttons with visual overlay
- Annotations showing Δt and Δω on respective axes

**Key "Aha Moments**
- "A narrow pulse in time has a wide spectrum; a broad signal has narrow spectrum"
- "Time shift doesn't change magnitude, only adds linear phase"
- "Δt · Δω is constant (uncertainty principle intuition)"

---

### Tool 10: Discrete-Time Pole/Zero Explorer (DT Systems)

**Lectures Covered**: 11, 18

**What Students DO**
- Place poles and zeros in z-plane (inside, on, or outside unit circle)
- Understand pole magnitude → decay rate, pole angle → oscillation frequency
- Predict impulse response shape from pole location
- Compare s-plane vs z-plane analogues (e.g., s = -0.5 in CT ~ z = 0.6 in DT)
- Challenge: "Design a DT notch filter to eliminate 0.1 cycles/sample sinusoid"

**Key Features**
- Z-plane editor with unit circle (red stability boundary)
- Draggable poles/zeros with color coding (red = stable, orange = marginal, purple = unstable)
- Sliders for polar coordinates (radius, angle) as alternative to dragging
- Impulse response h[n] display (stem plot)
- Magnitude response |H(e^jω)| for ω ∈ [0, π]

**Technical**
- Evaluate H(z) at z = e^(jω) for frequency response
- Compute impulse response via partial fractions or inverse Z-transform

---

### Tool 11: Fourier Filter Inspector (Time-Domain + Frequency-Domain Dual View)

**Lectures Covered**: 15

**What Students DO**
- Select periodic input signal (square, triangle, sawtooth)
- Adjust filter cutoff frequency (or coefficients)
- Observe which harmonics pass vs attenuate (spectrum panel)
- See time-domain output smoothing/rounding
- Predict: "If I increase ωc, which new harmonics will appear?"
- Compare ideal brick-wall vs realistic RC/Butterworth

**Key Features**
- Three-panel layout: time-domain (input + output), filter magnitude response, output spectrum
- Filter type dropdown: 1st-order RC, 2nd-order Butterworth, ideal brick-wall
- Cutoff frequency slider with real-time updates
- Color-coded spectrum: passed (green) vs attenuated (red)
- Phase response display

**Why Important**
Teaches **convolution theorem** and **frequency-domain filtering** by making both domains visible. Students see directly how filter magnitude response determines which harmonics survive.

---

### Tool 12: Bode Plot + Root Locus Combined Controller Design Studio

**Lectures Covered**: 10-12

**What Students DO**
- Design feedback controller C(s) given plant G(s)
- View simultaneously: Bode plot of L(s) = C(s)G(s) and pole locus
- Adjust controller parameters (proportional gain, lead/lag) and watch both update
- Analyze stability margins (gain margin, phase margin)
- Challenge: "Achieve phase margin > 45° and gain margin > 10 dB"

**Key Features**
- Plant selector dropdown (unstable system, integrator, time-delayed system)
- Controller structure selector (proportional, PI, lead-lag, PID) with tunable parameters
- Four synchronized panels: Bode magnitude, Bode phase, pole locus, step response
- Live margin computation and display
- Toggle asymptotes and iso-damping contours

**Complexity**: High

**Why Important**
This is the **synthesis tool** for feedback control design—unifies two classical analysis methods (Bode and root locus) that students often struggle to connect.

---

### Tool 13: Sampling & Reconstruction Pipeline

**Lectures Covered**: 21-22

**What Students DO**
- Draw a continuous signal (sketch, preset, or upload)
- Adjust sampling rate (slider or Hz input)
- Adjust bit depth (2-16 bits)
- Toggle dithering and observe noise-shaping effects
- Drag LPF cutoff for reconstruction
- Measure quality: SNR, MSE, frequency response
- Challenge: "Reconstruct signal with <2% error"

**Key Features**
- Five-stage pipeline: input → anti-aliasing filter → sampler → quantizer → reconstruction filter → output
- Synchronized plots: input, impulse samples, quantized samples, sinc interpolation, reconstructed signal
- Error visualization: input vs output overlay, error waveform
- Quality metrics: SNR [dB], SINAD, THD, correlation
- Audio playback at each stage

**Complexity**: High

**Why Important**
Makes **every step visible**. Not a black box—students see impulses, sinc functions, quantization levels, reconstruction error. Complete system explorer, not parameter-adjustment tool.

---

### Tool 14: Sampling Rate Explorer with Spectral Folding

**Lectures Covered**: 21

**What Students DO**
- Start with multi-frequency signal (up to 200 kHz)
- Slide fs from 10 kHz to 500 kHz, watch spectral copies approach/overlap
- Predict aliasing for selected frequency components
- Design anti-aliasing filter by dragging LPF cutoff
- Compare audio quality at different fs (44.1, 48, 96 kHz)
- Explore time-frequency relationship: Ω = ωT

**Key Features**
- Multi-panel synchronized plots: input spectrum, impulse train, optional LPF, output spectrum, DTFT
- Continuous fs slider with real-time updates
- Drag-to-place sinusoid markers on input spectrum
- Color highlighting: aliased vs non-aliased components
- Audio playback at selected fs
- Nyquist frequency readout

**Complexity**: Medium

**Why Important**
Makes **convolution-in-frequency visual and interactive**. Students see spectral copies approach and overlap as they drag slider—directly reinforces Lecture 21 core insight.

---

### Tool 15: Modulation & Demodulation Studio

**Lectures Covered**: 23-24

**What Students DO**
- Build a transmitter: choose message signal, modulation type (AM/PM/FM), carrier frequency
- Drag modulation parameters and watch spectrum shift and expand
- Build a receiver: choose demodulation method, adjust receiver carrier frequency
- Add phase error and see signal fade (cos φ factor)
- Multi-channel scenario: multiple transmitters, select one to demodulate
- Compare modulation schemes: AM vs FM bandwidth/noise trade-offs

**Key Features**
- Dual transmitter/receiver interface
- Message signal drawing canvas
- Modulation type buttons (AM, AM+C, PM, FM)
- Sliders: carrier frequency ωc, modulation index m, receiver phase error
- Time-domain and frequency-domain plots (synchronized)
- Quality metrics: SNR, correlation, demodulation error
- Multi-channel FDM demo
- Audio playback

**Complexity**: High

**Why Important**
Complete communication system simulator, not visualization. Students build transmitters and receivers, experience synchronization challenges.

---

## Tier 3: Nice to Have

These are specialized, advanced, or integration tools. Lower priority but valuable for completeness.

### Tool 16: CD Audio Processing Pipeline (System Integration)

**Lectures Covered**: 25

**What Students DO**
- Record audio (upload or record live)
- Design ADC filter chain (anti-aliasing cutoff)
- Choose sampling rate (44.1, 48, 96 kHz)
- Quantize to 16 bits
- Engineer playback: reconstruction filter design
- Measure quality metrics: SNR, frequency response, THD
- End-to-end challenge: minimize artifacts

**Key Features**
- Three main pages: ADC side, DAC side, quality metrics
- Upload or microphone input
- LPF cutoff sliders (record + playback)
- Quantization bit-depth selector
- Upsampling factor selector
- Spectrograms and frequency response plots
- A/B audio comparison slider
- File size calculator

**Complexity**: Very High

**Why Important**
Professional-grade audio engineering tool. Connects 6 lectures of theory into one coherent workflow.

---

### Tool 17: Custom Signal Laboratory

**Lectures Covered**: 06, 16

**What Students DO**
- Draw arbitrary signals (time-domain or frequency-domain)
- Compute all transforms (Fourier series, CTFT, DTFS, DTFT)
- Perform signal operations: convolution, multiplication, filtering
- Compute time-domain properties: energy, power, autocorrelation
- Explore spectral properties: bandwidth, frequency content

**Key Features**
- Signal drawing canvas (with grid/axes)
- Transform computation (all four representations)
- Operation selectors: convolution, modulation, filtering
- Property computed: energy, power, autocorrelation, RMS
- Export signals as CSV

---

### Tool 18: System Identification from Frequency Response

**Lectures Covered**: 10

**What Students DO**
- Given a Bode plot (magnitude/phase), design poles/zeros to match
- Interactive challenge: "Create this Bode plot shape"
- Feedback shows distance between student's design and target
- Guided hints: "You need a pole at ..."

---

### Tool 19: Transfer Function Design Workbench

**Lectures Covered**: 10, 12

**What Students DO**
- Edit H(s) directly (or via pole/zero locations)
- All plots update live: Bode, pole/zero map, step response, impulse response
- Toggle between s-plane and frequency views
- Analyze: gain margin, phase margin, bandwidth, damping ratio

---

### Tool 20: Block Diagram Assembly Station

**Lectures Covered**: 01-02

**What Students DO**
- Drag blocks (integrator, delay, gain, adder) onto canvas
- Connect them with wires
- Simulate system response to input signals
- Measure output and compare to theoretical predictions

**Key Features**
- Block library: integrators, delays, gains, summers, multipliers
- Visual feedback showing signal flow
- Real-time simulation

---

### Tool 21: Complete LTI System Analysis Chain

**Lectures Covered**: 07-10

**What Students DO**
- Input a transfer function H(s)
- Compute impulse response h(t)
- Compute frequency response H(jω)
- Display Bode plot
- Compute pole/zero locations
- Interactive filtering of input signals through system

---

### Tool 22: Real-World System Emulator

**Lectures Covered**: 11-12

**What Students DO**
- Model and control realistic systems: motor speed control, robot wall-finder, suspension system
- Tune controller parameters
- Predict and verify system behavior

---

### Tool 23: Signal Path Debugging Workbench

**Lectures Covered**: 14-16

**What Students DO**
- Trace signal through processing pipeline
- Identify where error is introduced
- Challenge: "The output is corrupted. Find the faulty filter."

---

## Development Dependency Graph

### Shared Infrastructure Components

Tools share these reusable React components and backend modules:

**Canvas Components**:
- **Pole-Zero Canvas** (Konva.js): Draggable poles/zeros with unit circle overlay, s-plane grid, z-plane grid. Shared by Bode Plot Constructor, Pole Migration Dashboard, Discrete-Time Pole/Zero Explorer, Transfer Function Design Workbench

**Plotly Renderers**:
- **Bode Plot Renderer**: Magnitude + phase subplots. Used by Bode Plot Constructor, Bode + Root Locus Designer, Transfer Function Design Workbench

- **Pole-Zero Map Renderer**: Scatter plot with locus. Used by Pole Migration Dashboard, Interactive Feedback Stability Debugger, Complete LTI System Analysis Chain

- **Frequency Response Renderer**: Magnitude and phase plots with optional asymptotes. Shared by multiple frequency-domain tools

- **Time-Domain Renderer**: Animated signal plots. Shared by nearly all tools

**Signal Processing Modules**:
- **Fourier Series Analyzer**: Compute aₖ, bₖ from signal. Shared by Fourier Series Decomposer, Fourier Filter Inspector

- **FFT Wrapper**: Fast Fourier transform with proper scaling. Shared by Fourier Domain Navigator, Aliasing Discovery Lab, Sampling & Reconstruction Pipeline

- **Pole/Zero Evaluator**: Compute H(s) and H(z) at arbitrary points. Shared by all frequency-response tools

- **Signal Generator**: Synthesize sine, square, triangle, sawtooth, chirp, pulses. Shared by nearly all tools

**Audio Processing**:
- **Web Audio Synthesizer**: Play signals with Web Audio API. Shared by Fourier Series Decomposer, Aliasing Discovery Lab, Modulation & Demodulation Studio, CD Audio Pipeline

- **Dithering & Quantization Module**: Quantize with optional dithering. Shared by Sampling & Reconstruction Pipeline, CD Audio Pipeline

**State Management Patterns**:
- Use React hooks (useState, useCallback, useMemo) consistently
- Debounce slider updates (150ms) to prevent excessive re-computation
- Cache FFT results and pole trajectories for performance

**Backend Endpoints** (FastAPI):
- `/api/fourier_series` — compute Fourier series coefficients
- `/api/bode_plot` — compute Bode plot from poles/zeros
- `/api/frequency_response` — evaluate H(jω) or H(e^jω)
- `/api/pole_trajectories` — compute root locus for swept K
- `/api/step_response` — compute time-domain step response
- `/api/fft` — compute FFT with optional windowing
- `/api/sampling_simulation` — compute aliasing and reconstruction
- `/api/modulation` — AM/FM modulation and demodulation

---

## Shared Component Library

### 1. Pole-Zero Canvas (Interactive)

**File**: `frontend/src/components/PoleZeroCanvas.jsx`

**Used By**: Bode Plot Constructor, Pole Migration Dashboard, Discrete-Time Pole/Zero Explorer, Transfer Function Design Workbench, System Identification from Response, Pole Assignment Challenges

**Props**:
- `poles` [array of {σ, ω} or {re, im}]: Initial pole locations
- `zeros` [array]: Initial zero locations
- `planeType` ['s' or 'z']: s-plane or z-plane
- `readonly` [bool]: Allow dragging or view-only
- `onPolesChange` [callback]: Update parent when poles move
- `showContours` [bool]: Display ζ contours or unit circle
- `highlightColor` [string]: Highlight color for stability regions

**Capabilities**:
- Drag poles/zeros with real-time feedback
- Click to add, right-click to delete
- Color-code by stability (red = unstable, green = stable)
- Optional overlay of locus (pole trajectories)
- Numerical readout of pole locations
- Constraint enforcement (e.g., complex conjugate pairs)

---

### 2. Bode Plot Renderer

**File**: `frontend/src/components/BodePlotter.jsx`

**Used By**: Bode Plot Constructor, Bode + Root Locus Designer, Transfer Function Design Workbench, Fourier Filter Inspector

**Props**:
- `magnitude` [array]: |H(jω)| in dB
- `phase` [array]: ∠H(jω) in degrees
- `frequency` [array]: ω values (log-spaced)
- `asymptotic_magnitude` [array, optional]: Straight-line approximation
- `asymptotic_phase` [array, optional]: Piecewise linear approx
- `margins` {gainMargin, phaseMargin, crossover, ...}: Stability metrics

**Capabilities**:
- Dual subplots: magnitude (log-log) and phase (semilog)
- Overlay actual + asymptotic curves
- Annotations: gain/phase margin, crossover frequencies
- Color-coded: asymptotic segments (per pole/zero)
- Linked zoom/pan between subplots

---

### 3. FFT Analyzer

**File**: `backend/core/fft_analyzer.py`

**Used By**: Aliasing Discovery Lab, Fourier Domain Navigator, Fourier Filter Inspector, Sampling & Reconstruction Pipeline, CD Audio Pipeline, Custom Signal Laboratory

**Methods**:
- `compute_fft(signal, fs)` → frequency array, magnitude, phase
- `compute_ifft(magnitude, phase, fs)` → time-domain signal
- `compute_fourier_series(signal, T, num_harmonics)` → aₖ, bₖ
- `apply_window(signal, window_type)` → windowed signal

---

### 4. Pole-Zero Evaluator

**File**: `backend/core/pole_zero_evaluator.py`

**Used By**: Nearly all frequency-response tools

**Methods**:
- `evaluate_transfer_function(poles, zeros, gain, frequency)` → H(jω)
- `compute_magnitude_phase(H)` → |H|, ∠H
- `compute_step_response(poles, zeros, t_array)` → y(t)
- `compute_impulse_response(poles, zeros, t_array)` → h(t)
- `find_poles_from_H_s(s_coefficients)` → pole locations

---

### 5. Signal Generator

**File**: `backend/core/signal_generator.py`

**Used By**: All tools

**Methods**:
- `sine(f, fs, duration, phase, amplitude)` → samples
- `square(f, fs, duration, duty_cycle)` → samples
- `triangle(f, fs, duration)` → samples
- `sawtooth(f, fs, duration)` → samples
- `pulse(f, fs, duration, width)` → samples
- `gaussian(f, fs, duration, sigma)` → samples
- `chirp(f_start, f_end, fs, duration)` → samples
- `step(fs, duration, t_transition)` → samples
- `superpose(signals)` → combined signal

---

### 6. Audio Playback Engine

**File**: `frontend/src/utils/audioPlayback.js`

**Used By**: Fourier Series Decomposer, Aliasing Discovery Lab, Modulation & Demodulation Studio, Sampling & Reconstruction Pipeline, CD Audio Pipeline

**Methods**:
- `playSignal(samples, fs)` → Web Audio playback
- `stopPlayback()` → stop
- `setVolume(dB)` → adjust volume
- `synthesizeFromFFT(freq, magnitude, phase, duration)` → audio

---

### 7. Dithering & Quantization Module

**File**: `backend/core/quantization.py`

**Used By**: Sampling & Reconstruction Pipeline, CD Audio Pipeline

**Methods**:
- `quantize(signal, num_bits)` → quantized signal
- `quantize_with_dither(signal, num_bits, dither_amount)` → dithered signal
- `compute_quantization_error(original, quantized)` → error metrics
- `shaped_dither(signal, num_bits)` → noise-shaped dither

---

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-3)

**Goal**: Establish shared infrastructure and Tier 1 tools.

1. **Shared Components** (Week 1)
   - Pole-Zero Canvas with s-plane and z-plane modes
   - Bode Plot Renderer with live asymptote overlay
   - FFT Analyzer backend module
   - Pole-Zero Evaluator backend module
   - Signal Generator with preset waveforms

2. **Tier 1 Tool 1: Leaky Tank Simulator** (Week 1)
   - Tank geometry editor
   - CT/DT ODE solver
   - Side-by-side response plots

3. **Tier 1 Tool 2: Pole-Zero Magnitude/Phase Visualizer** (Week 1-2)
   - S-plane editor (poles/zeros)
   - Real-time magnitude/phase computation
   - Vector visualization

4. **Tier 1 Tool 3: Bode Plot Constructor** (Week 2-3)
   - S-plane editor
   - Asymptotic plot builder
   - Actual vs asymptotic overlay

**Deliverable**: Three working tools with shared backend/frontend infrastructure

### Phase 2: Extension (Weeks 4-6)

**Goal**: Build remaining Tier 1 tools and begin Tier 2.

5. **Tier 1 Tool 4: Pole Migration Dashboard** (Week 3)
   - K slider with root locus computation
   - Step response animation
   - Design metrics display

6. **Tier 1 Tool 5: Fourier Series Harmonic Decomposer** (Week 3-4)
   - Harmonic editor sliders
   - Preset waveforms
   - Audio playback (Web Audio API)
   - Gibb's phenomenon visualization

7. **Tier 1 Tool 6: Fourier Domain Navigator** (Week 4)
   - Four-panel split layout
   - Draggable signal with four simultaneous FFTs
   - Aliasing visualization

8. **Tier 1 Tool 7: Aliasing Discovery Lab** (Week 4-5)
   - Multi-frequency sinusoid composition
   - fs slider with spectral folding
   - Prediction/verification loop
   - Audio playback of aliases

9. **Tier 1 Tool 8: Interactive Feedback Stability Debugger** (Week 5)
   - K slider with z-plane pole computation
   - Step response overlay
   - Delay selector

10. **Tier 2 Tool 1: Fourier Transform Explorer** (Week 5-6)
    - Time/frequency dual domain
    - Draggable signal with live FT
    - Property verification buttons

**Deliverable**: Eight working tools, foundation for Tier 2

### Phase 3: Completion (Weeks 7-10)

**Goal**: Complete remaining Tier 2 and integrate all tools.

11-13. **Remaining Tier 2 tools** (Weeks 6-8)
    - Discrete-Time Pole/Zero Explorer
    - Fourier Filter Inspector
    - Bode + Root Locus Designer
    - Sampling & Reconstruction Pipeline
    - Sampling Rate Explorer
    - Modulation & Demodulation Studio

14. **Integration & Refinement** (Weeks 8-10)
    - Connect all tools to main catalog interface
    - Cross-tool navigation
    - Tutorial walkthroughs per tool
    - Performance optimization (caching, lazy-loading)
    - Mobile responsive design

**Deliverable**: 15+ working tools with seamless integration

### Phase 4: Polish & Specialization (Weeks 11-12)

**Goal**: Tier 3 tools and final refinement.

15. **Tier 3 Tools** (Weeks 10-12)
    - CD Audio Processing Pipeline
    - System Identification from Frequency Response
    - Transfer Function Design Workbench
    - Block Diagram Assembly Station
    - Complete LTI System Analysis Chain
    - Real-World System Emulator
    - Signal Path Debugging Workbench

16. **Final Polish**
    - Pedagogical walkthroughs and hints
    - Error handling and edge cases
    - Documentation
    - User testing and feedback

**Deliverable**: Complete tool suite with 25+ interactive tools

---

## What Makes This Different from Generic Simulations

### Comparison: Generic Slider Demo vs. Tool-Based Learning

| Aspect | Generic Slider Demo | Tool-Based Approach |
|--------|------------------|-------------------|
| **Interaction** | "Adjust slider, watch plot" | "Build system, predict, then verify" |
| **Student Role** | Passive observer | Active constructor/designer |
| **Cognitive Load** | High (many dials, little guidance) | Lower (guided challenges, progressions) |
| **Feedback** | Visual plot changes | Immediate consequences on multiple domains |
| **Transferability** | Low (students don't retain mechanism) | High (students understand *why* system behaves this way) |
| **Engagement** | Decreases over time | Stays high (challenges + discovery) |
| **Example: Bode Plot** | "Move slider, see magnitude change" | "Place poles/zeros, watch asymptotes appear + verify against actual curve, solve challenge to match target" |
| **Example: Fourier Series** | "Slider for N harmonics, see signal converge" | "Turn on harmonics one-by-one, hear audio, predict convergence rate, challenge to reconstruct sawtooth" |
| **Example: Sampling** | "Adjust fs, see aliasing appear" | "Compose multi-frequency signal, predict which frequencies alias, design anti-aliasing filter, play audio to hear distortion" |
| **Example: Control Design** | "Slide K, see pole locations move" | "Control robot wall-finder, predict stability with different delays, design K to achieve desired settling time, measure margins" |
| **Connection to Lecture** | Loose (tool designed after lecture concept) | **Tight** (tool *encodes* the lecture pedagogical sequence) |

### Why Tools Win for Learning

1. **Prediction-then-Verification**: Students predict outcomes before seeing them ("Will this alias?", "Will it oscillate?"), building predictive intuition.

2. **Multi-Domain Visibility**: Time, frequency, s-plane, z-plane all visible simultaneously. Students learn to think across domains.

3. **Construction, Not Consumption**: Students *build* Bode plots asymptote-by-asymptote, *compose* signals from harmonics, *design* controllers—not just watch them change.

4. **Immediate Consequences**: Every action (drag pole, add harmonic, adjust fs) shows result across multiple plots instantly. Builds causality understanding.

5. **Challenge-Driven**: Tools include design challenges ("Create a system with 45° phase margin", "Reconstruct this waveform") that motivate exploration.

6. **Grounded in Real Systems**: Each tool references physical/practical context (robot control, audio CDs, radio modulation) that students recognize.

7. **Convergence & Limits**: Tools like Fourier Series Decomposer make visible how partial sums converge, how continuous-time arises as limit of discrete-time as T → 0.

---

## Final Notes for Implementation

### Performance Optimization

- **Debounce all slider updates** (150ms) to prevent excessive re-computation
- **Cache FFT results** (keyed by signal hash)
- **Cache pole trajectories** (keyed by plant parameters)
- **Lazy-load heavy tools** (Three.js for 3D viewers only on demand)
- **Use NumPy vectorization** exclusively; never Python loops on arrays
- **Offload to backend**: FFT, pole computation, differential equation solving

### Responsive Design

- **Tablet/mobile**: Stack panels vertically, hide optional overlays
- **Small screens**: Fold four-panel Fourier Domain Navigator into tabbed interface
- **Touch-friendly**: Large slider handles, bigger clickable regions for poles/zeros

### Accessibility

- **All plots**: include text alt-text for key quantities (e.g., "Pole at σ = -1, ω = 2")
- **Color-blind friendly**: Use distinct patterns + colors (not just red/blue)
- **Keyboard shortcuts**: Tab to move focus, arrow keys to adjust sliders

### Documentation per Tool

Each tool should have:
- **Conceptual overview**: "This tool teaches X from Lecture Y"
- **Quick start**: 30-second walkthrough showing one interaction
- **Guided challenges**: 3-5 progressive challenges with hints
- **Optional deep dive**: Video walkthrough, theory references

### Testing Strategy

- **Unit tests**: Backend FFT, pole evaluation, signal generation
- **Integration tests**: End-to-end tool workflows (draw signal → compute FT → verify moments)
- **Pedagogical validation**: Pre-test with students; measure learning gains vs. lecture alone

---

## Conclusion

This master catalog defines **25 interactive tools** spanning MIT 6.003, organized by pedagogical impact and implementation complexity. **Tier 1 (8 tools)** should be built first and form the foundation. **Tier 2 (11 tools)** extends understanding to advanced topics. **Tier 3 (6 tools)** provides specialized applications.

The tools share **common React/backend infrastructure** (Pole-Zero Canvas, Bode Renderer, FFT Analyzer, Audio Playback) enabling rapid development. Each tool is **pedagogically self-contained**, directly encoding lecture sequences and teaching through active construction, prediction, and verification—not passive observation.

This approach transforms the textbook from a **collection of passive simulations** into a **mini-Simulink ecosystem** where students **build, discover, and ultimately understand** signals and systems deeply.

---

**Total Development Estimate**: 12-16 weeks for full implementation of all 25 tools, assuming 2-3 developers.

**Highest-Impact Quick Win**: Build Tier 1 tools 1-5 (Leaky Tank, Pole-Zero Visualizer, Bode Constructor, Pole Migration, Fourier Decomposer) in first 4 weeks. These five alone cover lectures 01-03, 07-12, 14-15—approximately 40% of the course.
