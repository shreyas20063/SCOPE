# Interactive Tools: Lectures 10-18 Analysis
## MIT 6.003 Signals and Systems

Extracted from visual analysis of lecture contact sheets and raw transcripts, Fall 2011.

---

## Tool 1: Bode Plot Constructor

### Inspired By (Visual)
Lecture 10 sheets 15-30: Systematic construction of Bode plots from poles and zeros. Multi-panel progression showing:
- Individual pole/zero asymptotes (magnitude and phase)
- Layered addition of asymptotes to build complete Bode plot
- Transition from linear s-plane to logarithmic magnitude/phase vs ω

### What Students DO (not watch)
- **Draw** individual asymptotes for given poles and zeros on a blank log-log grid
- **Compose** complete Bode plot by layering asymptotes (superposition)
- **Test** predictions: input a transfer function H(s), sketch Bode plot, then reveal actual plot for comparison
- **Refine**: adjust pole/zero locations and see real-time impact on magnitude and phase plots
- **Challenge mode**: given a target Bode plot, design poles/zeros to match it

### Tool Description
A visual construction environment where students build Bode plots from first principles by dragging poles and zeros onto the s-plane, watching asymptotes appear and combine in real time. The tool teaches the fundamental insight that Bode plots are simply sums of logarithms—each pole contributes a -20 dB/decade slope and -π/2 phase shift, each zero contributes +20 dB/decade and +π/2. Students see the connection between the s-plane geometry (pole/zero locations and distances) and frequency response (magnitude and phase across ω).

Three side-by-side panels:
1. **S-plane editor**: drag poles (red X) and zeros (blue O) anywhere in the complex plane. Adjustable gain K with dB slider.
2. **Asymptotic plot workspace**: initially blank log-log grid for magnitude (dB vs log ω) and linear grid for phase (degrees vs log ω). As student places poles/zeros, colored asymptotic segments appear corresponding to each element.
3. **Actual frequency response**: updated in real time, overlaid on asymptotic approximation. Shows where the actual curve deviates from straight-line approximation (especially near pole/zero frequencies, at ±3dB points).

### Interaction Model
**Drag-and-drop editor** with constraint-based feedback:
- Click to add pole (X) or zero (O) to s-plane
- Drag to move; magenta highlight shows real-time impact
- Right-click to delete
- Slider to adjust K (gain) in dB
- **Challenge mode**: given target Bode magnitude/phase profile, design poles/zeros to match
- **Guided mode**: step-by-step construction of a known transfer function (e.g., Lecture 10's example H(s) = s / [(s+1)(s+10)])

### Multi-Panel Layout
```
┌─────────────────────────────────────────────────┐
│ Bode Plot Constructor                           │
├──────────────────┬──────────────────┬───────────┤
│   S-plane        │  Asymptotes      │  Actual   │
│   Editor         │  (Built-up sum)  │  Freq.    │
│                  │                  │  Response │
│  (drag poles     │  (Add line       │  (Real    │
│   and zeros)     │   segments in    │   curve   │
│                  │   real-time)     │   with    │
│                  │                  │   3dB pts)│
│                  │                  │           │
│   [Add] [Mode]   │  dB/decade      │  Overlay  │
│   [Gain slider]  │  slopes visible  │  accuracy │
│                  │                  │           │
└──────────────────┴──────────────────┴───────────┘
        Visualization of phase as angle on s-plane vs phase on plot
```

### Key "Aha Moments"
- "A pole at s = -a contributes -20 dB/decade, which is just log(magnitude) of 1/(jω+a)"
- "Poles and zeros in the s-plane are vectors; their angles and magnitudes compose"
- "Bode plot is a compressed view: log lets us add asymptotes instead of multiplying magnitudes"
- "The shape of Bode plot is determined entirely by pole/zero locations; gain K only shifts the magnitude plot vertically"

### Technical Architecture
**Backend:**
- Evaluate H(s) at user's chosen s-plane location (σ + jω)
- Compute magnitude |H(jω)| and phase ∠H(jω) across ω (e.g., 0.01 to 100 rad/s, log-spaced)
- Asymptotic approximations: for each pole at -a, contribute -20 dB/decade for ω > a; for each zero at -b, contribute +20 dB/decade for ω > b
- Phase contributions: piecewise-linear approximation per pole/zero

**Frontend:**
- React canvas for s-plane dragging (Konva.js or similar)
- Plotly for magnitude and phase plots with live updating
- SVG overlays for asymptotic line segments (drawn from asymptotic rules, color-coded per pole/zero)
- Real-time overlay of actual H(jω) curve to show accuracy of approximation

**Complexity:** Medium

### Why This Isn't Generic
This is not "adjust a parameter and see a plot change." Students actively **construct knowledge**: each placement teaches vector magnitude/phase, the composition of logarithms, and the direct read-off from s-plane geometry to frequency response shape. Lecture 10 dedicates 10+ slides to this exact progression. The tool encodes the pedagogical sequence into interaction.

---

## Tool 2: Pole Migration Dashboard (Closed-Loop Control Design)

### Inspired By (Visual)
Lecture 11 sheets 40-52, Lecture 12 sheets 8-34: Root locus—how poles move as a control parameter (gain) varies. Key slides show:
- Wall-finder robot system pole trajectories as K changes from 0 to -∞
- Transition from open-loop to closed-loop stability
- Pole collision points where real poles become complex
- Space-time diagrams showing how oscillation period changes with pole location
- Motor control: poles moving from origin, colliding, then splitting into complex conjugates

### What Students DO (not watch)
- **Draw** pole trajectories on the s-plane as gain K is varied interactively
- **Predict**: at what gain value do poles become unstable?
- **Connect**: understand relationship between pole location (σ, ω_d) and time-domain response (damping, oscillation frequency)
- **Solve challenges**: "Find K to place poles at specific location for desired settling time"
- **Visualize**: simultaneously watch step response evolve as pole positions change

### Tool Description
A dual-panel interactive environment for root locus design. Left panel: s-plane with pole/zero locations of the open-loop system and a **slider for gain K**. As K varies, poles move along their locus. Right panel: step response of the **closed-loop** system. Student manipulates K to move poles, watching in real time how the transient response (overshoot, settling time, oscillation) changes.

Teaches the fundamental trade-off: increasing K moves poles left (faster, potentially unstable) and can create oscillations (complex poles). Reference circles show iso-damping and iso-natural-frequency lines to guide design choices.

### Interaction Model
**Parameter sweep with dual feedback**:
- Horizontal slider for K from 0 to some maximum (or negative K for proportional feedback)
- As slider moves, poles trace paths on s-plane (their locus)
- Overlay showing stability boundary (jω axis) in red
- Togglable: damping ratio ζ contours and natural frequency ω_n circles (helpful design tools)
- Right panel: live step response (unit step input) with annotations: settling time, percent overshoot, oscillation frequency
- **Marker mode**: click on locus to lock K at a specific value and freeze the design

### Multi-Panel Layout
```
┌─────────────────────────────────────────────────┐
│ Pole Migration Dashboard                        │
├──────────────────┬──────────────────────────────┤
│  S-plane Root    │  Step Response (Closed-Loop) │
│  Locus           │                              │
│                  │  y(t)                        │
│  jω              │   |                          │
│   ↑              │  1├─────────────────         │
│   │   ×          │   │      settling time      │
│   │  / \         │   │ ↑ overshoot            │
│   │ /   \        │   │                        │
│  ─┼─────→ σ      │ 0 └────────────────────── t │
│   │    ×O        │                            │
│   │     ↑        │  [Osc. freq, settling time]│
│   │              │  [Damping ζ, ωₙ labels]   │
│                  │                              │
│ K slider ←→      │  Phase margin, gain margin  │
│ [Stability]      │  [computed from poles]      │
│ [ζ contours]     │                              │
│ [ωₙ circles]     │                              │
└──────────────────┴──────────────────────────────┘
```

### Key "Aha Moments"
- "Gain K moves poles along a fixed path (locus); I don't choose individual pole locations, only their path"
- "Poles on the jω axis = marginally stable = constant oscillation (e.g., wall-finder with sensor delay)"
- "Complex poles → oscillatory response; real poles → smooth approach"
- "Delay in the feedback loop pushes the locus to the right (destabilizes); larger gain K needed to stabilize"

### Technical Architecture
**Backend:**
- Compute open-loop system function H(s) = K × G(s)
- Find closed-loop poles: roots of 1 + H(s) = 0 for each K
- Sweep K across a range (e.g., -3 to +3) and store pole trajectories
- For each pole location, compute step response of closed-loop system
- Extract: overshoot, settling time, oscillation frequency (from imaginary part of complex poles)

**Frontend:**
- Plotly for s-plane (scatter for pole locations, line traces for locus)
- Overlay: jω axis (red, stability boundary), optional ζ contours (family of parabolas), optional ω_n circles
- Plotly for step response
- Slider component with real-time plot update on value change
- Annotations: "Stable region" (left half-plane), "Unstable region" (right half-plane)

**Complexity:** Medium-High

### Why This Isn't Generic
This encodes the **root locus method**—a classical control design technique spanning decades of engineering practice. Students don't just see plots; they learn to *read* the s-plane as a prediction tool for transient response. Lectures 11-12 show exactly this progression: from pole equations to space-time diagrams to practical control design.

---

## Tool 3: Fourier Series Harmonic Decomposer

### Inspired By (Visual)
Lecture 14 sheets 3-30, Lecture 15 sheets 1-6: Progressive synthesis of periodic signals from harmonics. Slides show:
- Square and triangle waves built from cumulative harmonic sums (k = 0, 1, 3, 5, ..., up to 39)
- Gibb's phenomenon ringing near discontinuities
- Orthogonal decomposition analogy (Fourier coefficients = vector dot products)
- Convergence behavior: triangle (fast, k^-2) vs square (slow, k^-1)

### What Students DO (not watch)
- **Add** harmonic components one at a time, watching signal converge
- **Adjust** amplitude of individual harmonics and see signal reshape
- **Predict**: which harmonics are most important for a given waveform?
- **Compare**: square wave (infinite harmonics, slow convergence) vs triangle (drops off faster)
- **Challenge**: "Build a sawtooth wave by choosing harmonic amplitudes"
- **Hear**: optionally play audio of partial sums (musical note becoming more complex as harmonics added)

### Tool Description
A dual-view tool where students incrementally compose a periodic signal from sinusoidal components. Top panel: individual harmonic sliders (amplitude and phase for each k). Middle panel: cumulative signal reconstruction (sum of selected harmonics). Bottom panel: frequency spectrum showing which harmonics are "on" and their magnitudes.

Key insight: decompose a periodic signal into harmonics (analysis), then rebuild it from harmonics (synthesis). Students feel the trade-off between frequency resolution (number of harmonics needed) and time-domain shape (smoothness, sharpness at discontinuities).

### Interaction Model
**Additive synthesis with live feedback**:
- Vertical strip: slider for each harmonic k (0, 1, 2, 3, ..., up to ~30)
- Checkboxes to toggle harmonics on/off
- Magnitude slider per harmonic (amplitude a_k)
- Phase slider per harmonic (angle of e^(jkω₀t))
- **Preset buttons**: "Square Wave", "Triangle", "Sawtooth", "Sine", "Saw-up"—loads known Fourier coefficients
- **Guided mode**: highlight which harmonics are "active" in a target signal, then students tune amplitudes to match

### Multi-Panel Layout
```
┌──────────────────────────────────────────────────┐
│ Fourier Series Harmonic Decomposer               │
├──────────────────────────────────────────────────┤
│ [Presets: Square | Triangle | Sawtooth | ...]   │
├──────────────────────────────────────────────────┤
│  Time-Domain Signal (Synthesis)                  │
│                                                  │
│  x(t) = Σ aₖ e^(jkω₀t)                          │
│   |                                              │
│   |    ╱╲  ╱╲                                     │
│   └────────────────── t                          │
│  [Convergence: N harmonics used]                 │
├──────────────────────────────────────────────────┤
│  Harmonic Editor (left) | Spectrum (right)       │
│  k=0: [━━●━━]  [phase] ✓ | Magnitude plot       │
│  k=1: [━━●━━]  [phase] ✓ |                      │
│  k=2: [━━●━━]  [phase] ✓ |                      │
│  k=3: [━━●━━]  [phase] ✓ | ■                    │
│  ...                      | ■  ■                 │
│                           | ■  ■  ■             │
│                           └────────────          │
└──────────────────────────────────────────────────┘
```

### Key "Aha Moments"
- "Any periodic signal is just a weighted sum of harmonics; the weights (a_k) determine the signal shape"
- "Square wave has all odd harmonics (k = 1, 3, 5, ...) with magnitude ~ 1/k; triangle drops as 1/k²"
- "Adding more harmonics makes the signal sharper (especially at discontinuities) but introduces ringing (Gibb's phenomenon)"
- "Orthogonal: turning up one harmonic doesn't mess with others; they're independent basis functions"

### Technical Architecture
**Backend:**
- Define Fourier series: x(t) = Σ a_k e^(j2πkt/T) for k = -N to +N
- Evaluate x(t) at high temporal resolution for display
- Compute magnitude spectrum |a_k| from sliders
- Optional: pre-compute Fourier coefficients for preset waveforms (square, triangle, sawtooth)
- Optional: audio synthesis (resample to 44.1 kHz, play via Web Audio API)

**Frontend:**
- React sliders for each harmonic amplitude and phase
- Plotly for time-domain signal (high-res line plot)
- Plotly for frequency spectrum (stem/bar chart)
- Real-time update as any slider moves
- Toggling harmonics on/off via checkboxes (gray out contribution to signal)

**Complexity:** Low-Medium

### Why This Isn't Generic
This directly encodes **Fourier decomposition** as a student activity: seeing how signals emerge from harmonic sums. Lecture 14's 30-slide sequence of building square and triangle waves is begging for an interactive version. Students build muscle memory for which harmonics matter, and audio feedback makes it visceral (a square wave "sounds" different from a triangle).

---

## Tool 4: Fourier Transform Explorer (Duality & Time-Frequency Trade-Off)

### Inspired By (Visual)
Lecture 16 sheets 1-30: Fourier transform derivation by taking T → ∞ limit of Fourier series. Key visuals:
- Periodic extension of a finite pulse: discrete harmonics → continuous spectrum
- Stretching time compresses frequency (and vice versa): x(t) → x(at) gives 1/|a| × X(jω/a)
- Square pulse (time domain) ↔ sinc function (frequency domain)
- "Moments": X(jω)|ω=0 = ∫x(t)dt; x(0) = 1/(2π) ∫X(jω)dω

### What Students DO (not watch)
- **Draw** or select a time-domain signal (pulse, Gaussian, exponential)
- **Observe** its Fourier transform magnitude and phase in real time
- **Stretch or compress** the signal in time, watching frequency spectrum get compressed or stretched
- **Move signals in time** (time shift), watching phase plot rotate
- **Multiply by scale factor** K, watching magnitude scale by K
- **Verify moments**: click to show integral of x(t), click to show area under X(jω)/2π, confirm they match

### Tool Description
A side-by-side panel showing time-domain signal and frequency-domain Fourier transform. Students can manipulate the time-domain signal (via draggable waypoints or preset shapes) and see the transform update live. Sliders for time stretch/scale, time shift, multiplication by exponential, etc. show how basic properties reflect in both domains.

Key insight: time-domain and frequency-domain representations are complementary—narrow in one is wide in the other. A signal that is tightly localized in time has a broad Fourier transform (and vice versa).

### Interaction Model
**Dual-domain manipulator**:
- **Left panel**: time-domain signal x(t). Draggable control points to sketch a custom signal, or dropdown for presets: "Pulse", "Gaussian", "Exponential", "Cosine burst"
- **Right panel**: Fourier transform X(jω), magnitude and phase (dual subplots)
- **Sliders**:
  - Time scale a: x(t) → x(at). Text label: "Stretching time by a compresses frequency by 1/a"
  - Time shift t₀: x(t) → x(t - t₀). Shows phase rotation in X(jω)
  - Multiplication by e^(-αt): damps signal, shows frequency response shift and broadening
  - Frequency zoom: pan and zoom on X(jω) to see details
- **Verify moments buttons**:
  - "Compute ∫x(t)dt and compare to X(j0)"
  - "Compute ∫X(jω)dω/2π and compare to x(0)"

### Multi-Panel Layout
```
┌────────────────────────────────────────────────┐
│ Fourier Transform Explorer                      │
├────────────────┬────────────────────────────────┤
│  Time Domain   │  Frequency Domain              │
│  x(t)          │  |X(jω)|                       │
│   |            │   |                            │
│   |  ╱╲        │   |  ╱╲╲                       │
│   | ╱  ╲       │   | ╱    ╲╲                    │
│   └─────────── t │  └──────────── ω             │
│                  │                              │
│  [Presets ▼]    │  ∠X(jω)                      │
│  [Custom edit]   │   |                          │
│                  │   |╱─╲                       │
│ Stretch: [●──]   │   |   ╲─╱                    │
│ Shift: [────●]   │   └──────────── ω             │
│ Decay: [──●──]   │                              │
│                  │  [Time-freq product: Δt·Δω] │
│ [Moment 1]       │  [Area under curves]         │
│ [Moment 2]       │                              │
└────────────────┴────────────────────────────────┘
```

### Key "Aha Moments"
- "A narrow pulse in time has a wide spectrum in frequency; a long, spread-out signal has a narrow spectrum"
- "Time shift (delay) doesn't change magnitude of Fourier transform, only adds linear phase rotation"
- "The area under x(t) equals X(j0); the average height of x(t) is 1/(2π) times the area under X(jω)"
- "Stretching time by a factor a compresses frequency by 1/a: Δt · Δω = constant (uncertainty principle intuition)"

### Technical Architecture
**Backend:**
- Numerical integration for Fourier transform: X(jω) = ∫ x(t) e^(-jωt) dt
- Evaluate x(t) at user-defined control points (cubic interpolation between points)
- Compute X(jω) at dense ω grid (e.g., -20 to +20 rad/s, 500+ points)
- Apply transformations: time scale a, time shift t₀, exponential decay
- Compute moments: area under |x(t)|, area under |X(jω)|

**Frontend:**
- Plotly for time and frequency plots (with linked zoom/pan)
- Draggable control points on time-domain plot using React+Plotly interactions
- Sliders for scale, shift, decay parameters
- Annotations showing Δt and Δω on the respective axes
- Optional dashed vertical line at ω = 0 to show X(j0)

**Complexity:** Medium

### Why This Isn't Generic
This directly teaches **time-frequency duality**—a cornerstone concept spanning signal processing, quantum mechanics, and information theory. Lecture 16's visual progression from periodic to aperiodic is made interactive: students literally see the transformation as they manipulate the signal.

---

## Tool 5: Bode Plot + Root Locus Combined Controller Design Studio

### Inspired By (Visual)
Lecture 10-12 combined: students need to understand that Bode plots (frequency response) and pole locations (root locus) are two views of the same system. Slides show both representations of control systems.

### What Students DO (not watch)
- **Design** a feedback controller C(s) given a plant model G(s)
- **View** simultaneously: Bode plot of the open-loop system L(s) = C(s)G(s) and the pole locus
- **Adjust** controller parameters (proportional gain, lead/lag) and watch both representations update
- **Analyze** stability margins (gain margin, phase margin from Bode) and confirm poles stay in left half-plane
- **Challenge**: "Design C(s) to achieve ±3 dB phase margin and -20 dB gain margin"

### Tool Description
Unified interface showing:
1. **Plant selector**: dropdown with pre-defined G(s) models (unstable system, integrator, time-delayed system)
2. **Controller editor**: structure (proportional, PI, lead-lag, PID) with tunable parameters
3. **Open-loop Bode plot**: magnitude and phase vs ω
4. **Closed-loop pole locations**: root locus with current pole positions marked
5. **Stability metric displays**: gain margin, phase margin, dominant pole damping ratio, settling time

### Interaction Model
**Multi-parameter design space**:
- Dropdown for plant G(s) and controller structure C(s)
- Parameter sliders: K (gain), τ (time constants), ζ (damping ratio for lead-lag)
- Toggle: "Show Bode asymptotes" and "Show iso-damping contours"
- Live updates to all four panels as any slider moves
- **Guided challenges**: "Achieve phase margin > 45° and gain margin > 10 dB"

### Multi-Panel Layout
```
┌──────────────────────────────────────────────────┐
│ Controller Design Studio                         │
├──────────────────────────────────────────────────┤
│ Plant: [Unstable ▼] Controller: [Lead-Lag ▼]    │
├──────────────────┬──────────────────────────────┤
│ Parameter Sliders│  Bode Plot (L(s) = CG)      │
│                  │  |L(jω)| [dB]                │
│ K: [────●────]   │   |                          │
│ τ₁: [───●──]     │   |╲                         │
│ τ₂: [──●───]     │   │ ╲___                     │
│ ζ: [────●────]   │   └─────────── ω [log]      │
│                  │                              │
│ Gain Margin: 15dB│  ∠L(jω)                      │
│ Phase Margin: 52°│   |                          │
│                  │   └─╲___────── ω [log]       │
└──────────────────┴──────────────────────────────┘
│ Pole Locations (Root Locus)  │  Step Response   │
│  jω                          │  y(t)            │
│   |      ×                    │   |              │
│   | ×  / \  × (closed-loop)   │   |─────────     │
│  ─┼──────── σ                 │   └──────────── t│
│   |     ×                      │                 │
│                                │  [Labels: peak, │
│                                │   settling]     │
└────────────────────────────────────────────────┘
```

### Key "Aha Moments"
- "The Bode plot and pole locations tell the same story: poles in left half-plane = negative phase rotation at ω = 0 means stable system"
- "Gain margin and phase margin are margins to instability; large margins mean robust design"
- "Lead-lag controller can reshape Bode plot: add phase near crossover frequency to improve margin"

### Technical Architecture
**Backend:**
- Symbolic pole/zero representations of controller C(s) and plant G(s)
- Compute L(s) = C(s) × G(s)
- Evaluate at jω for Bode plot; find roots of 1 + L(s) for pole locations
- Extract gain and phase margins using standard definitions
- Compute step response of closed-loop system

**Frontend:**
- Two Plotly plots (Bode magnitude/phase, pole map)
- Sliders using React state management
- Real-time updates on slider change (debounced for performance)

**Complexity:** High

### Why This Isn't Generic
This is the **final synthesis tool** for feedback control design—it unifies two classical analysis methods (Bode and root locus) that students often struggle to connect. The tool is project-scale (could be a semester capstone).

---

## Tool 6: Discrete-Time Pole/Zero Explorer (DT Systems)

### Inspired By (Visual)
Lecture 11 sheets 15-50, Lecture 18 sheets 1-9: Discrete-time systems with poles and zeros in the z-plane (unit circle is the stability boundary, not jω axis). Key slides:
- z-plane diagram showing convergent, oscillating, divergent pole locations
- Pole-to-response mapping: |z| < 1 → decaying, |z| = 1 → constant/oscillatory, |z| > 1 → exploding
- Period of oscillation from angle of z = re^(jθ): frequency = θ/2π cycles per sample
- Digital filter design: place poles/zeros in z-plane to achieve desired magnitude response

### What Students DO (not watch)
- **Place** poles and zeros in the z-plane (inside, on, or outside the unit circle)
- **Understand**: pole/zero magnitude → decay rate, pole/zero angle → oscillation frequency
- **Predict**: impulse response shape from pole location
- **Compare**: analogous locations in s-plane vs z-plane (e.g., s = -0.5 in CT ~ z = 0.6 in DT at T = 1)
- **Challenge**: "Design a DT notch filter to eliminate a sinusoid at frequency f = 0.1 cycles/sample"

### Tool Description
Similar to the Bode Plot Constructor but for discrete time. Single panel: z-plane with unit circle highlighted in red (stability boundary). Students drag poles (red X) and zeros (blue O) around, and a secondary panel shows the impulse response h[n] and the magnitude response |H(e^jω)|.

### Interaction Model
**DT pole/zero placement**:
- Click to add pole or zero to z-plane
- Drag to move; constrain or allow placement outside unit circle (with warning)
- Right-click to delete
- Slider for z-plane radius and angle (alternative to dragging)
- Slider for gain K
- **Impulse response panel**: showing h[n] for n = 0 to 50 (or user-defined range)
- **Magnitude response panel**: |H(e^jω)| for ω ∈ [0, π] (normalized frequency)

### Multi-Panel Layout
```
┌──────────────────────────────────────────────────┐
│ Discrete-Time Pole/Zero Explorer                 │
├──────────────────┬──────────────────────────────┤
│  Z-plane         │  Impulse Response h[n]       │
│  (Unit Circle)   │                              │
│                  │  |                           │
│  Im(z)           │  |    ╱╲  ╱╲                 │
│   ↑              │  |   ╱  ╲╱                   │
│   │    ×(pole)   │  └───────────────── n       │
│  ─┼─○──→ Re(z)   │  [Decay rate: r^n]          │
│   │     O(zero)  │  [Oscillation: θ/2π]        │
│   │              │                              │
│   └──unit circle  │  Magnitude Response         │
│                  │  |H(e^jω)|[dB]              │
│  [Add] [Gain]    │   |                         │
│  [Constraints]   │   | ╲    ╱                  │
│                  │   │  \__/                   │
│                  │   └─────────── ω/π          │
└──────────────────┴──────────────────────────────┘
```

### Key "Aha Moments"
- "Poles outside the unit circle → exponential blowup; inside → exponential decay"
- "Pole angle = oscillation frequency in Hz; |pole| = decay rate per sample"
- "For a pole at z = re^(jθ), the impulse response is h[n] = r^n e^(jθn), which decays or grows like r^n"

### Technical Architecture
**Backend:**
- Evaluate H(z) = K ∏(z - z_i) / ∏(z - p_i) at z = e^(jω) for ω ∈ [0, π]
- Compute impulse response by inverse Z-transform (or partial fractions → exponentials)
- Mark poles/zeros in z-plane with color: red for inside unit circle (stable), orange for on boundary (marginally stable), purple for outside (unstable)

**Frontend:**
- Plotly z-plane (scatter and circle for unit circle)
- Plotly impulse response (stem plot)
- Plotly magnitude response (frequency response)
- Sliders for radius and angle (polar coordinates)

**Complexity:** Medium

### Why This Isn't Generic
Discrete-time systems are structurally different from continuous-time (unit circle vs jω axis). Students often confuse DT and CT pole locations. This tool makes the DT-specific intuition concrete.

---

## Tool 7: Interactive Feedback Stability Debugger (Delay & Sensor Issues)

### Inspired By (Visual)
Lecture 11 sheets 30-53: Wall-finder robot with and without sensor delay. Dramatic visual progression:
- No delay: pole at z = 0 (instantaneous response)
- With 1-sample delay: poles at z = 1/2 (slower response)
- With 2-sample delay: poles converge, then split into complex pair (oscillations appear)
- Space-time diagrams showing position trajectories with different K and delay values

### What Students DO (not watch)
- **Design** a proportional controller for a simple system (robot approach wall)
- **Toggle** sensor delay: 0, 1, 2, 3 samples
- **Adjust** gain K and see poles move on z-plane (closed-loop)
- **Predict**: at what gain does the system oscillate? Become unstable?
- **Compare**: time-domain trajectory (position vs time) for different {K, delay} pairs
- **Solve**: "Find maximum K to keep system stable with 2-sample delay"

### Tool Description
Four-panel environment:
1. **Block diagram**: P-D (proportional-delay) system with adjustable K and delay selector
2. **Z-plane pole map**: showing how poles move as K increases for fixed delay value
3. **Stability region**: shaded area (unit circle interior) vs unstable region
4. **Closed-loop step response**: position trajectory y[n] over time, with marked oscillations and settling time

Students adjust K and observe the three consequences simultaneously: pole motion, stability boundary crossing, and time-domain trajectory shape change.

### Interaction Model
**Control parameters**:
- Slider for proportional gain K (from 0 to 3, or user-adjustable range)
- Dropdown selector for sensor delay: 0, 1, 2, 3 samples
- Button to toggle "Zoom on poles" to see detail near unit circle
- Dropdown to switch between different plants: {integrator (velocity control), double integrator (position control), first-order lag (realistic system)}
- Play/pause button to animate K from 0 to max while watching poles trace locus
- Info panel showing: current K, pole locations, gain margin, stability status

### Multi-Panel Layout
```
┌──────────────────────────────────────────────────┐
│ Feedback Stability Debugger                      │
├──────────────────────────────────────────────────┤
│ [System ▼] | Delay: [0] [1] [2] | K slider [●──]│
├────────────────┬────────────────────────────────┤
│ Block Diagram  │  Z-plane (Root Locus)          │
│                │                                │
│ ref ─┐  K      │  Im(z)                         │
│      ├──×──DT──┼──┐                             │
│ +   /  delay   │  |    ●● (poles, K increasing)│
│  \-/           │ ─┼──────→ Re(z)                │
│      sensor    │  |    [unit circle]           │
│                │                                │
└────────────────┴────────────────────────────────┘
│ Position Trajectory y[n]              Stability │
│ |y[n]                                 Status    │
│  |  ╱╲                                           │
│  | ╱  ╲╲        (overshoot, oscillation)        │
│  │╱    ╲ ╲___                                    │
│  └────────────── n                              │
│                                                  │
│ [Settling time] [Peak overshoot] [Status: OK!]  │
└──────────────────────────────────────────────────┘
```

### Key "Aha Moments"
- "Delay in feedback makes it harder to stabilize: sensor delay pushes the pole locus to the right"
- "More delay = smaller maximum stable gain: trade-off between control speed and latency"
- "At the stability boundary, poles hit the unit circle; any increase in K → poles move outside → instability"

### Technical Architecture
**Backend:**
- Model: e.g., integrator θ[n+1] = θ[n] + K·e[n], where e[n] = ref[n] - y[n-d] (d-sample delay)
- Closed-loop: compute poles by finding roots of characteristic polynomial
- For each K, plot pole location; compute step response trajectory
- Detect stability: any pole with |z| ≥ 1.001?

**Frontend:**
- Plotly for z-plane (circle + poles + locus trace)
- Plotly for step response (stem or line plot of y[n])
- Sliders and dropdowns for K, delay, system selection
- Real-time update on parameter change

**Complexity:** Medium

### Why This Isn't Generic
This directly addresses a common student misconception: "Why does delay break control?" The tool makes visible the abstract fact that sensor latency shifts the locus toward instability. Lecture 11 shows this is critical in robotics and other real-time systems.

---

## Tool 8: Fourier Filter Inspector (Time-Domain + Frequency-Domain Dual View)

### Inspired By (Visual)
Lecture 15 sheets 20-30: Lowpass filtering of square and triangle waves at different frequencies. Slides show:
- Square wave input with all harmonics
- RC lowpass filter frequency response
- Filtered output with high harmonics removed
- Progressive smoothing as filter cutoff frequency decreases

### What Students DO (not watch)
- **Select** a periodic input signal (square, triangle, sawtooth)
- **Adjust** filter cutoff frequency (or filter coefficients)
- **Observe**:
  - Which harmonics pass vs attenuate (spectrum panel)
  - How the time-domain output is smoothed/rounded
  - Phase shift introduced by the filter
- **Predict**: "If I increase cutoff frequency, which new harmonics will appear in output?"
- **Compare**: ideal lowpass (brick-wall) vs realistic filter (gradual roll-off)

### Tool Description
Dual-domain view of filtering:
1. **Time domain** (top): input signal (periodic) and filtered output y(t), plotted together so students see the smoothing
2. **Frequency domain** (middle): spectrum of input (all harmonics) and filter magnitude response |H(jω)|, with highlight showing which input harmonics are attenuated
3. **Filtered spectrum** (bottom): output spectrum (input harmonics × filter response)

Students adjust filter cutoff frequency and type (RC, RL, 2nd-order Butterworth) and watch both domains update.

### Interaction Model
**Filter design parameters**:
- Dropdown: filter type {1st-order RC, 2nd-order Butterworth, ideal brick-wall}
- Slider: cutoff frequency ω_c (from 0.1 × ω₀ to 10 × ω₀, where ω₀ is input fundamental)
- Dropdown: input signal {square, triangle, sawtooth, custom}
- Toggle: show/hide input spectrum, output spectrum, filter response
- Zoom controls on frequency axis to focus on passing vs attenuated harmonics

### Multi-Panel Layout
```
┌──────────────────────────────────────────────────┐
│ Fourier Filter Inspector                         │
├──────────────────────────────────────────────────┤
│ Input: [Square ▼] | Filter: [RC ▼] | ωc [●───] │
├──────────────────────────────────────────────────┤
│  Time Domain: Input (red) vs Output (blue)       │
│  x(t), y(t)                                      │
│   |  ╱╲  ╱╲  ╱╲       (sharp input)              │
│   | ╱  ╲╱  ╲╱  ╲                                 │
│   └─────────────────── t                         │
│       ╱  ╲   ╱  ╲   ╱  ╲    (smooth output)      │
│      ╱    ╲ ╱    ╲ ╱    ╲                        │
│     ╱      ╱      ╱                              │
├──────────────────────────────────────────────────┤
│  Magnitude Response: |H(jω)|                     │
│   |                                              │
│   |■─────────                                    │
│   │         ╲___                                 │
│   └──────────────── ω                            │
│      pass-band │ stop-band                       │
├──────────────────────────────────────────────────┤
│  Output Spectrum: X_out(jω) = H(jω)·X_in(jω)    │
│  Magnitude plot with highlighted attenuated bins │
│   |■  ■  ■                                        │
│   │     ■                                        │
│   └──────────── ω                                │
│  [Attenuation at k·ω₀]                           │
└──────────────────────────────────────────────────┘
```

### Key "Aha Moments"
- "A filter can't create new frequencies; it only scales the input harmonics"
- "Lowpass filter removes high harmonics, which are responsible for sharp features (discontinuities)"
- "As cutoff frequency decreases, more harmonics are blocked; the output becomes smoother"
- "Phase shift from filter is different at each frequency; high harmonics are delayed more"

### Technical Architecture
**Backend:**
- Compute Fourier series of input signal (use analytical formulas for square, triangle, sawtooth)
- Define filter H(jω) for chosen type (RC, Butterworth, etc.)
- Multiply: X_out(jω) = H(jω) × X_in(jω) for each harmonic
- Reconstruct time-domain output by inverse Fourier series
- Compute phase response arg(H(jω))

**Frontend:**
- Plotly for time-domain overlay (input and output)
- Plotly for filter magnitude and phase response (on same ω axis)
- Plotly for input, filter, and output spectra (side-by-side stem plots)
- Slider for ω_c with real-time update
- Color-coded highlighting: attenuated vs passed harmonics

**Complexity:** Medium

### Why This Isn't Generic
This teaches the **convolution theorem** and **frequency-domain filtering** by making both domains visible. Students see directly how the filter's magnitude response determines which harmonics survive. Lecture 15's multi-slide progression is made interactive and explorable.

---

## Summary: Design Principles Across All Tools

1. **Dual-Domain Representation**: Nearly all tools show simultaneous time and frequency views (Bode + pole locations, Fourier series + time signal, filter magnitude + time response). This embeds the principle that signals and systems have multiple, equally valid descriptions.

2. **Interactive Parameter Sweep**: Sliders and drag-and-drop allow parameter variation with live feedback. Students develop intuition by seeing immediate consequences, not by reading equations.

3. **Challenge Mode**: Each tool includes a "design challenge" (e.g., "achieve phase margin > 45°"). This reframes the tool as a design instrument, not a calculator.

4. **Guided/Preset Mode**: For students new to the topic, presets (e.g., "Square Wave", "Butterworth Filter") help them bootstrap understanding; they then modify to explore.

5. **Visualization of Convergence**: Tools like Fourier Series Decomposer explicitly show how partial sums converge, making abstract limits concrete.

6. **Connection to Physical Systems**: Each tool is grounded in a real system (robot wall-finder, audio speaker, music synthesis) to motivate the theory.

---

## Implementation Notes

- **Backend**: All computation can be done in Python (NumPy/SciPy) with FastAPI endpoints
- **Frontend**: React + Plotly.js for interactive plots; Canvas (Konva.js) for drag-and-drop geometry
- **Integration**: These tools fit naturally into the existing Block Diagram Builder ecosystem; they should share state management patterns and color schemes
- **Pedagogy**: Each tool should include **tooltips** and optional **walkthroughs** to guide first-time users
- **Validation**: Pre-test with students to ensure sliders and interaction paradigms match mental models

---

## Priority for Development

**Phase 1 (High Impact, Medium Effort)**:
1. Bode Plot Constructor
2. Fourier Series Harmonic Decomposer
3. Pole Migration Dashboard (Closed-Loop Control)

**Phase 2 (Deeper Learning, Higher Effort)**:
4. Fourier Transform Explorer
5. Feedback Stability Debugger
6. Fourier Filter Inspector

**Phase 3 (Specialization)**:
7. Bode Plot + Root Locus Combined Designer
8. Discrete-Time Pole/Zero Explorer

Each tool is self-contained and can be developed independently, then integrated into the main platform.
