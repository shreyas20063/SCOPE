# Lecture 07 — Detailed Simulation Implementation Prompts

## Source: MIT 6.003F11 Lecture 07 — Discrete Approximation of Continuous-Time Systems

---

## Simulation 1: Discretization Method Comparator

### One-Line Summary
Side-by-side comparison of Forward Euler, Backward Euler, and Trapezoidal (Bilinear) discretization applied to a user-chosen CT system, showing time-domain responses and z-plane pole locations.

### What It Teaches
Students struggle to understand *why* discretization method matters — they see the formulas but don't grasp the consequences. This sim lets them **watch** Forward Euler blow up while Trapezoidal stays accurate, building visceral intuition for stability and accuracy tradeoffs.

### Layout (Single Page, 3 Columns + Controls)

```
┌─────────────────────────────────────────────────────────────────┐
│  CONTROLS BAR (top)                                              │
│  [System Selector ▼] [T/τ Slider: 0.05──●──3.0]  [Animate ▶]  │
├───────────────────┬───────────────────┬─────────────────────────┤
│  FORWARD EULER    │  BACKWARD EULER   │  TRAPEZOIDAL (BILINEAR) │
│                   │                   │                         │
│  ┌─────────────┐  │  ┌─────────────┐  │  ┌─────────────┐       │
│  │ Time Domain │  │  │ Time Domain │  │  │ Time Domain │       │
│  │ CT: blue    │  │  │ CT: blue    │  │  │ CT: blue    │       │
│  │ DT: red ●   │  │  │ DT: red ●   │  │  │ DT: red ●   │       │
│  └─────────────┘  │  └─────────────┘  │  └─────────────┘       │
│                   │                   │                         │
│  ┌─────────────┐  │  ┌─────────────┐  │  ┌─────────────┐       │
│  │ z-plane     │  │  │ z-plane     │  │  │ z-plane     │       │
│  │ unit circle │  │  │ unit circle │  │  │ unit circle │       │
│  │ pole: ×     │  │  │ pole: ×     │  │  │ pole: ×     │       │
│  └─────────────┘  │  └─────────────┘  │  └─────────────┘       │
│                   │                   │                         │
│  Pole: z=1-T/τ   │  Pole: z=1/(1+T/τ)│  Pole: (2τ-T)/(2τ+T)  │
│  |z|= ___        │  |z|= ___         │  |z|= ___              │
│  STABLE/UNSTABLE  │  STABLE           │  STABLE                │
├───────────────────┴───────────────────┴─────────────────────────┤
│  ERROR PANEL: max|y_CT - y_DT| for each method                 │
│  Forward: 0.342   Backward: 0.089   Trapezoidal: 0.012         │
└─────────────────────────────────────────────────────────────────┘
```

### System Presets (dropdown)

1. **Leaky Tank (1st order)**: H(s) = 1/(1+τs), τ adjustable. The lecture's main example.
2. **Mass-Spring (2nd order, undamped)**: H(s) = 1/(s² + ω₀²), poles at ±jω₀. Shows Forward Euler diverging, Backward Euler overdamping, Trapezoidal preserving oscillation.
3. **Mass-Spring-Dashpot (2nd order, damped)**: H(s) = ω₀²/(s² + 2σs + ω₀²). Shows how damping interacts with discretization.
4. **Double Integrator**: H(s) = 1/s². Marginally stable CT system — great stress test.
5. **Custom**: User enters poles and zeros directly.

### Interactions

| Control | Type | Range | Effect |
|---------|------|-------|--------|
| T/τ ratio | Slider | 0.05 to 3.0 | Changes step size relative to time constant. Key moments: T/τ=1 (Forward Euler pole at 0), T/τ=2 (Forward Euler marginally stable), T/τ>2 (Forward Euler diverges) |
| System selector | Dropdown | 5 presets | Loads CT system and recomputes all three discretizations |
| τ (time constant) | Slider | 0.1 to 5.0 | For leaky tank — adjusts system speed |
| ω₀ (natural freq) | Slider | 0.5 to 10 | For mass-spring — adjusts oscillation frequency |
| Animate toggle | Button | On/Off | Slowly sweeps T/τ from 0.1 to 3.0 so student watches stability unfold |
| Input signal | Radio | Step / Impulse / Sinusoid | Changes the excitation signal |

### Backend Computation (FastAPI endpoint)

```
POST /api/discretization/compare
Request:
{
  "system_type": "leaky_tank" | "mass_spring" | "mass_spring_damped" | "double_integrator" | "custom",
  "ct_poles": [complex],         // for custom mode
  "ct_zeros": [complex],         // for custom mode
  "tau": float,                   // time constant (1st order)
  "omega_0": float,               // natural frequency (2nd order)
  "sigma": float,                 // damping (2nd order)
  "T_over_tau": float,            // step size ratio
  "input_type": "step" | "impulse" | "sinusoid",
  "num_samples": int              // default 100
}

Response:
{
  "t_ct": [float],                // CT time vector (dense)
  "y_ct": [float],                // CT response (exact)
  "n_dt": [int],                  // DT sample indices
  "forward_euler": {
    "y": [float],                 // DT response
    "poles_z": [complex],         // z-plane poles
    "pole_magnitudes": [float],
    "stable": bool,
    "max_error": float
  },
  "backward_euler": { ... same structure ... },
  "trapezoidal": { ... same structure ... },
  "ct_poles_s": [complex]         // s-plane poles for reference
}
```

**CT exact response**: Use `scipy.signal.step` / `scipy.signal.impulse` for the CT system.

**DT responses**: For each method, construct the DT transfer function:
- Forward Euler: substitute s = (z-1)/T into H(s), get H_fe(z), then use `scipy.signal.dlti` + `dstep`/`dimpulse`
- Backward Euler: substitute s = (z-1)/(Tz) into H(s)
- Trapezoidal: substitute s = (2/T)(z-1)/(z+1) into H(s)

### Key Pedagogical Moments to Highlight
- When T/τ = 2.0 exactly: Forward Euler pole at z = -1 → alternating ±1 output (marginally stable)
- When T/τ > 2.0: Forward Euler pole |z| > 1 → diverging oscillation (flash the border red)
- Mass-spring with Forward Euler at any T: poles outside unit circle → always unstable for undamped oscillator
- Trapezoidal with mass-spring: poles exactly on unit circle → persistent oscillation (correct!)

### Frontend Notes
- Use Plotly.js for all plots (consistent with existing stack)
- Time-domain plots: CT as solid blue line, DT as red dots connected by thin red lines
- z-plane plots: unit circle as dashed gray, poles as red ×, shade interior green (stable region)
- When a method goes unstable, the time-domain plot should auto-scale but also flash a red "UNSTABLE" badge
- The error panel at the bottom computes max absolute error over the first 50 samples

---

## Simulation 2: s-to-z Mapping Visualizer

### One-Line Summary
Interactive visualization of how geometric regions in the s-plane transform to the z-plane under Forward Euler, Backward Euler, and Trapezoidal mappings.

### What It Teaches
The lecture's slides 20, 31, and 35-38 show static images of how the left half-plane maps under each method. Students memorize these but don't develop intuition for *how* the mapping distorts space. This sim makes it dynamic — drag a pole around the s-plane and watch its image move in the z-plane in real-time.

### Layout

```
┌──────────────────────────────────────────────────────────────┐
│  CONTROLS: [Method: ○ FE  ○ BE  ● Trap  ○ All Three]       │
│            [T slider: 0.01──●──2.0]  [Show Grid ☑]          │
│            [Mode: ○ Single Pole  ○ Region  ○ Grid Lines]    │
├────────────────────────────┬─────────────────────────────────┤
│     s-PLANE                │     z-PLANE                     │
│                            │                                 │
│     ← σ →                  │     unit circle (dashed)        │
│     ↑ jω                   │                                 │
│                            │                                 │
│  ──────────┼──────────     │     ────────○────────           │
│            │               │            │                    │
│     LHP    │    RHP        │    inside  │  outside           │
│  (stable)  │ (unstable)    │   (stable) │ (unstable)         │
│            │               │            │                    │
│                            │                                 │
│  [draggable pole ×]        │  [mapped pole(s) ×]             │
│  [draggable region □]      │  [mapped region]                │
│                            │                                 │
├────────────────────────────┴─────────────────────────────────┤
│  INFO: s = -2+3j → z_FE = 0.1+0.6j (|z|=0.61, stable)     │
│        Mapping: z = 1 + sT = 1 + (-2+3j)(0.2) = 0.6+0.6j  │
└──────────────────────────────────────────────────────────────┘
```

### Modes

**Mode 1 — Single Pole**: User clicks/drags a pole in the s-plane. The z-plane shows where it maps under the selected method(s). If "All Three" is selected, show three differently-colored × markers in the z-plane (red=FE, blue=BE, green=Trap).

**Mode 2 — Region**: User draws a rectangle or circle in the s-plane (click-drag). The z-plane shows the mapped region as a filled shape. Key insight: FE maps the jω axis to a circle of radius 1/T centered at z=1 (not the unit circle!), while Trapezoidal maps jω axis exactly to the unit circle.

**Mode 3 — Grid Lines**: Show a grid of constant-σ (vertical) and constant-ω (horizontal) lines in the s-plane. The z-plane shows how this grid warps under each mapping. Toggle between methods to see the distortion.

### Interactions

| Control | Type | Effect |
|---------|------|--------|
| Method selector | Radio buttons | FE / BE / Trap / All Three |
| T (step size) | Slider 0.01–2.0 | Changes the mapping. As T grows, FE stability region shrinks |
| Pole position | Click-drag on s-plane | Real-time update of z-plane position |
| Region draw | Click-drag rectangle | Draws region in s-plane, shows mapped region in z-plane |
| Show stability boundary | Checkbox | In s-plane, shade the region that maps inside the unit circle |
| Show jω→unit circle | Checkbox | Highlight the jω axis in s-plane and its image in z-plane |
| Animate T sweep | Button | Sweep T from 0.01 to 2.0, watch the stability region shrink/grow |

### Backend Computation

```
POST /api/discretization/s_to_z_map
Request:
{
  "mode": "single_pole" | "region" | "grid",
  "method": "forward_euler" | "backward_euler" | "trapezoidal" | "all",
  "T": float,
  "s_points": [complex],        // for single pole or grid of points
  "region": {                    // for region mode
    "type": "rectangle" | "circle",
    "center": complex,
    "width": float, "height": float  // or "radius": float
  },
  "grid_resolution": int         // for grid mode, points per axis
}

Response:
{
  "forward_euler": {
    "z_points": [complex],       // mapped points
    "stability_boundary_s": [complex],  // curve in s-plane that maps to unit circle
  },
  "backward_euler": { ... },
  "trapezoidal": { ... },
  "unit_circle": [complex],     // for reference plotting
}
```

**Mapping formulas** (core computation):
- Forward Euler: z = 1 + sT
- Backward Euler: z = 1/(1 - sT)
- Trapezoidal: z = (2 + sT)/(2 - sT)

**Stability boundary in s-plane** (the curve in s-plane that maps to |z|=1):
- FE: circle |1+sT|=1, centered at s = -1/T, radius 1/T
- BE: line Re(s) = -1/(2T) — a vertical line (the entire LHP and more maps inside)
- Trap: the jω axis itself (exactly Re(s)=0)

Most of this can be computed **client-side** (the mappings are simple algebra), but a backend endpoint is useful for generating dense grids for region mapping.

### Key Pedagogical Moments
- FE with large T: the stability circle in the s-plane becomes tiny → only poles very close to origin stay stable
- BE: even very negative poles (fast dynamics) map inside unit circle → always stable but potentially inaccurate
- Trapezoidal: jω axis → unit circle is the key insight. Place a pole on the jω axis → it maps exactly to the unit circle under Trap, but outside under FE

---

## Simulation 3: Numerical Integration Explorer

### One-Line Summary
Geometric visualization of how Forward Euler, Backward Euler, and Trapezoidal rules approximate integrals, showing the actual rectangular/trapezoidal areas being computed.

### What It Teaches
Discretization methods come from approximating the integral ∫y(t)dt. Forward Euler uses left-endpoint rectangles, Backward Euler uses right-endpoint rectangles, and Trapezoidal uses trapezoids. Students who see the geometry understand *why* trapezoidal is more accurate and *why* forward Euler overshoots on convex curves.

### Layout

```
┌──────────────────────────────────────────────────────────────┐
│  CONTROLS: [Signal ▼] [N steps: 3──●──50] [Step ◀ ▶] [Auto]│
├──────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌────────────────────────────────────────────────────┐     │
│   │          MAIN PLOT (large, takes ~60% height)      │     │
│   │                                                    │     │
│   │  y(t) ─── continuous curve (blue)                  │     │
│   │  ███████ colored rectangles/trapezoids              │     │
│   │  ─ ─ ─ ─ true integral area (light gray fill)     │     │
│   │                                                    │     │
│   │  Three overlaid layers (togglable):                │     │
│   │    Red rectangles = Forward Euler (left-endpoint)  │     │
│   │    Blue rectangles = Backward Euler (right-endpt)  │     │
│   │    Green trapezoids = Trapezoidal rule             │     │
│   └────────────────────────────────────────────────────┘     │
│                                                              │
│   ┌──────────┬──────────┬──────────┐                         │
│   │  FE      │  BE      │  TRAP    │  ← integral estimates   │
│   │  Area:   │  Area:   │  Area:   │                         │
│   │  2.341   │  1.892   │  2.105   │                         │
│   │  Err: 12%│  Err: 8% │  Err: 0.3%│                        │
│   │  [████ ] │  [███  ] │  [█████] │  ← accuracy bars        │
│   └──────────┴──────────┴──────────┘                         │
│   True integral: 2.112                                       │
└──────────────────────────────────────────────────────────────┘
```

### Signal Presets

1. **Exponential decay**: y(t) = e^{-t}, t ∈ [0, 5]. Convex curve — FE overestimates, BE underestimates.
2. **Exponential growth**: y(t) = e^{0.5t}, t ∈ [0, 3]. Concave — FE underestimates.
3. **Sinusoid**: y(t) = sin(2πt), t ∈ [0, 1]. Shows how all methods handle sign changes.
4. **Step response**: y(t) = (1 - e^{-t})u(t). The leaky tank step response from the lecture.
5. **Custom**: User draws a curve with mouse (interpolated with cubic spline).

### Interactions

| Control | Type | Effect |
|---------|------|--------|
| Signal | Dropdown | Select signal to integrate |
| N (number of steps) | Slider 3–50 | Fewer steps = bigger rectangles = more visible error |
| Step forward/back | Buttons ◀ ▶ | Animate one rectangle at a time (builds up the approximation incrementally) |
| Auto animate | Toggle | Steps through automatically at 0.5s intervals |
| Show/hide methods | 3 checkboxes | Toggle visibility of FE/BE/Trap overlays |
| Show error curve | Checkbox | Below main plot, show cumulative error vs. step number |

### Backend Computation

```
POST /api/discretization/integration
Request:
{
  "signal": "exp_decay" | "exp_growth" | "sinusoid" | "step_response" | "custom",
  "custom_points": [[t, y], ...],  // for custom mode
  "n_steps": int,
  "t_range": [float, float]
}

Response:
{
  "t_continuous": [float],
  "y_continuous": [float],
  "t_samples": [float],           // sample points
  "y_samples": [float],
  "true_integral": float,
  "forward_euler": {
    "rectangles": [{"x": float, "width": float, "height": float}, ...],
    "cumulative_area": [float],   // running sum at each step
    "total_area": float,
    "error_pct": float
  },
  "backward_euler": { ... },
  "trapezoidal": {
    "trapezoids": [{"x1": float, "x2": float, "y1": float, "y2": float}, ...],
    "cumulative_area": [float],
    "total_area": float,
    "error_pct": float
  }
}
```

### Frontend Notes
- Rectangles should be semi-transparent (alpha=0.3) so overlapping methods are visible
- Trapezoidal areas are drawn as actual trapezoid shapes (not rectangles)
- Step-through mode: each click adds one more rectangle/trapezoid with a brief fade-in animation
- The accuracy bars at the bottom are colored green→yellow→red based on error percentage
- Consider adding a convergence plot: error vs. N on a log-log scale (should show FE/BE = O(h) slope, Trap = O(h²) slope)

---

## Simulation 4: Leaky Tank Simulator

### One-Line Summary
Animated physical simulation of water flowing into and leaking out of a tank, with side-by-side comparison of exact CT response vs. discretized DT approximations.

### What It Teaches
The leaky tank is the lecture's central metaphor. Students understand the physical system intuitively (water in, water leaks out proportionally to level). This sim connects that physical intuition to the math — they see τ as "how fast the tank drains" and T as "how often we check the water level." When T is too large relative to τ, the Forward Euler approximation "overshoots" because it doesn't check often enough.

### Layout

```
┌──────────────────────────────────────────────────────────────┐
│  CONTROLS: [τ: 0.5──●──5.0] [T/τ: 0.1──●──3.0] [▶ Play]   │
│            [Input: ○ Step  ○ Pulse  ○ Sinusoidal]            │
├──────────────────────┬───────────────────────────────────────┤
│                      │                                       │
│   TANK ANIMATION     │   TIME-DOMAIN PLOT                    │
│                      │                                       │
│   ┌──────────┐       │   y(t) ──── exact CT (blue solid)    │
│   │ ↓ x(t)   │       │   y_fe[n] ● Forward Euler (red)     │
│   │ ════════ │       │   y_be[n] ● Backward Euler (green)  │
│   │ ░░░░░░░░ │       │   y_tr[n] ● Trapezoidal (orange)    │
│   │ ░░░░░░░░ │       │                                       │
│   │ ░░WATER░░ │       │        ╱‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾             │
│   │ ░░░░░░░░ │       │       ╱   ← step response            │
│   │ ░░░░░░░░ │       │      ╱                                │
│   └────┬─────┘       │   ──╱─────────────────────────        │
│        │ → y(t)      │   0                           t       │
│     (leak out)       │                                       │
│                      │                                       │
│   Water level: 0.63  │                                       │
│   Inflow rate: 1.0   │                                       │
├──────────────────────┴───────────────────────────────────────┤
│  EQUATION PANEL:                                             │
│  CT: τ·dy/dt = x(t) - y(t)    →    H(s) = 1/(1+τs)        │
│  FE: y[n+1] = (1-T/τ)y[n] + (T/τ)x[n]   pole: z = 1-T/τ  │
│  BE: y[n] = (1/(1+T/τ))y[n-1] + (T/τ/(1+T/τ))x[n]        │
│  TR: bilinear transform applied                              │
├──────────────────────────────────────────────────────────────┤
│  QUIZ MODE: "Which method is shown?" [FE] [BE] [TR] [Reveal]│
└──────────────────────────────────────────────────────────────┘
```

### Tank Animation Details
- SVG or Canvas-based tank: a rectangle with animated blue water fill
- Water level = y(t) normalized to tank height
- Inflow arrow at top with thickness proportional to x(t)
- Outflow arrow at bottom with thickness proportional to y(t)/τ
- When Forward Euler goes unstable: water level goes negative → tank flashes red, "water" becomes red and oscillates above/below zero to show the unphysical result
- Discrete sampling markers: vertical dashed lines on the time plot at each nT, with dots on the tank animation "pulsing" at each sample instant

### Interactions

| Control | Type | Effect |
|---------|------|--------|
| τ (time constant) | Slider 0.5–5.0 | Larger τ = slower tank drain. Changes how long it takes to reach steady state |
| T/τ ratio | Slider 0.1–3.0 | The key parameter. At T/τ=2, Forward Euler pole at z=-1 (oscillation). Above 2, divergence |
| Input signal | Radio buttons | Step (constant inflow), Pulse (brief inflow burst), Sinusoidal (oscillating inflow) |
| Play/Pause | Button | Animates the tank filling in real-time, with DT samples appearing at each nT |
| Playback speed | Slider 0.25x–4x | Control animation speed |
| Show/hide methods | 3 checkboxes | Toggle which DT approximations appear on the time plot |
| Quiz mode | Toggle | Hides method labels, shows only one random DT response, student guesses which method |

### Backend Computation

```
POST /api/discretization/leaky_tank
Request:
{
  "tau": float,
  "T_over_tau": float,
  "input_type": "step" | "pulse" | "sinusoid",
  "sinusoid_freq": float,        // only for sinusoidal input
  "pulse_duration": float,       // only for pulse input
  "duration": float,             // total simulation time
  "num_ct_points": int           // resolution of CT curve
}

Response:
{
  "t_ct": [float],
  "y_ct": [float],
  "x_ct": [float],               // input signal (for animation)
  "T": float,                     // actual step size = T_over_tau * tau
  "n_samples": int,
  "t_dt": [float],               // sample times
  "forward_euler": {
    "y": [float],
    "pole_z": complex,
    "stable": bool
  },
  "backward_euler": {
    "y": [float],
    "pole_z": complex,
    "stable": bool
  },
  "trapezoidal": {
    "y": [float],
    "pole_z": complex,
    "stable": bool
  },
  "equations": {                  // formatted strings for display
    "ct_ode": "τ·dy/dt = x(t) - y(t)",
    "ct_tf": "H(s) = 1/(1 + τs)",
    "fe_diff_eq": "y[n+1] = (1-T/τ)y[n] + (T/τ)x[n]",
    "be_diff_eq": "...",
    "tr_diff_eq": "..."
  }
}
```

### Quiz Mode Details
- Randomly picks one of the three methods
- Shows only that method's DT response (unlabeled, all in gray dots)
- Three buttons: [Forward Euler] [Backward Euler] [Trapezoidal]
- On correct guess: green flash + short explanation of the telltale sign
- On wrong guess: red flash + shows the correct answer with explanation
- Telltale signs to teach:
  - FE with large T/τ: oscillations / divergence (overshoots then undershoots)
  - BE: overly smooth, approaches steady state faster than it should, never oscillates
  - Trap: closest to CT curve, slight frequency warping for sinusoidal inputs
- Score tracker: 0/0 correct, running tally

### Frontend Animation Notes
- The tank fill should use CSS transitions or requestAnimationFrame for smooth water level animation
- Consider adding "ripple" effects on the water surface when inflow changes
- The sample instants (nT) should be marked with brief visual pulses on the tank (like a camera flash) to reinforce "we only check the water level at these moments"
- Use Plotly.js `animation` frames for the time-domain plot, adding points incrementally as the simulation progresses

---

## General Implementation Notes (All 4 Sims)

### Shared Components
All four simulations share the theme of comparing three discretization methods. Consider building:
- A reusable `MethodColorLegend` component (FE=red, BE=blue/green, Trap=orange)
- A reusable `StabilityBadge` component that shows STABLE (green) / MARGINAL (yellow) / UNSTABLE (red)
- A shared `ZPlane` plot component with unit circle, pole markers, and stability shading
- Common backend utilities for the three s-to-z mappings

### Color Scheme (Consistent Across All Sims)
- CT exact: `#2196F3` (blue, solid line)
- Forward Euler: `#F44336` (red)
- Backward Euler: `#4CAF50` (green)
- Trapezoidal: `#FF9800` (orange)
- Stable region: light green fill with alpha=0.15
- Unstable region: light red fill with alpha=0.15

### API Structure
```
/api/discretization/compare       → Sim 1
/api/discretization/s_to_z_map    → Sim 2
/api/discretization/integration   → Sim 3
/api/discretization/leaky_tank    → Sim 4
```

### Dependencies
- Backend: `numpy`, `scipy.signal` (for CT/DT system construction and simulation)
- Frontend: `plotly.js` (all plots), `react` (UI), optionally `d3` for the tank SVG animation
