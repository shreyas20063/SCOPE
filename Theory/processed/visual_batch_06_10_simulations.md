# Novel Simulation Ideas: Lectures 6-10 (Z Transforms, Properties, Convolution, Frequency Response, Feedback)

Visual analysis of MIT 6.003 lecture slides identifying 9 new simulation concepts with pedagogical depth.

---

## Simulation: Interactive ROC Explorer

### Lecture Source: Lecture 6, Pages 3-4 (Laplace Transform ROC)

### Visual Cues Observed
The slides show explicit time-domain interpretations of ROC regions through multiple stacked diagrams: finite-duration signals, left-sided exponentials, right-sided exponentials, and bilateral exponentials each mapped to corresponding ROC half-planes. The visual stacking demonstrates how pole location determines convergence region boundaries. The s-plane diagram shows the boundary between convergence and divergence as a vertical line (the half-plane boundary).

### Learning Objective
Understand how pole location constrains the region of convergence; develop intuition that ROC is not arbitrary but determined by signal causality and decay properties. The "aha moment" is seeing that moving a pole left (more negative) expands the right-half-plane ROC.

### Theoretical Foundation

For Laplace transforms, the ROC is the set of values $s = \sigma + j\omega$ where $\int_{-\infty}^{\infty} |x(t)e^{-\sigma t}| dt < \infty$.

- Right-sided causal signal (exponential decay): $x(t) = e^{-at}u(t) \Rightarrow X(s) = \frac{1}{s+a}$, ROC: $\sigma > -a$
- Left-sided signal: $x(t) = -e^{-at}u(-t) \Rightarrow X(s) = \frac{1}{s+a}$, ROC: $\sigma < -a$
- Bilateral signal: Two-sided exponential $\Rightarrow$ ROC is a vertical strip $-a < \sigma < -b$

The ROC boundary is determined by the pole locations: a right-half-plane pole at $-a$ means ROC must be to the right of the line $\sigma = -a$ for causal signals.

### System Architecture

**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|------------|
| Pole Real Part | -5 to 2 | Controls convergence boundary | Slider |
| Pole Imaginary Part | -5 to 5 | Oscillation frequency | Slider |
| Signal Type | {causal, anti-causal, bilateral} | Causality mode | Radio buttons |
| Test Frequency σ | -6 to 3 | Probing frequency to evaluate convergence | Draggable point on s-plane |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|---|---|
| ROC Region | Shaded half-plane/strip on s-plane | Shows where transform converges |
| Magnitude Response | Time-domain exponential magnitude over σ | Demonstrates why ROC exists |
| Pole Location | Red × on s-plane | Reference for ROC boundary |
| Convergence Status | Color change (red→green) as test point crosses boundary | Immediate feedback on membership |

### Visualization Strategy

Two-panel layout:
- **Left Panel**: Interactive s-plane with draggable pole, shaded ROC region, and a movable test frequency point ($\sigma$ slider). As pole moves, ROC boundary updates in real-time.
- **Right Panel**: Time-domain signal $x(t) = e^{-pt}u(t)$ where $p$ is the pole, shown with an overlay of the envelope $e^{-\sigma t}$ (where $\sigma$ is the test frequency). When the test point is inside ROC, the product decays to zero; outside, it grows. The shaded region under the decay curve represents the integral contribution.

**Interaction Flow:**
1. User sets pole position via slider.
2. ROC updates immediately; pole × appears on s-plane.
3. User drags test point along the $\sigma$-axis or adjusts it via slider.
4. Right panel updates time-domain view: if test point is in ROC, the signal decays; if outside, it diverges.
5. Switching signal type (causal ↔ anti-causal) flips the ROC to the opposite half-plane.

**Aha Moments:**
- Moving pole leftward (more negative) extends ROC rightward—causality wins.
- Same pole location, different signal type → opposite ROC regions.
- The boundary line passes through the pole; this is not coincidence but the mathematical boundary.

### Implementation Notes

**Complexity:** Medium

**Key Algorithms:**
- s-plane rendering with Plotly.js; pole/zero markers as scatter trace.
- ROC region: draw a semi-infinite shaded rectangle (half-plane) or a strip (bilateral).
- Time-domain signal generation: NumPy linspace for t, compute $e^{-pt}u(t)$, overlay $e^{-\sigma t}$ envelope.
- Convergence indicator: compute numerical integral (SciPy quad) at test $\sigma$ value; compare to threshold.

**Backend:**
```python
def compute_roc_region(pole_real, pole_imag, signal_type):
    # For standard Laplace: pole is at -a means ROC boundary at σ = -a
    boundary = -pole_real
    if signal_type == 'causal':
        return {'type': 'half-plane', 'side': 'right', 'boundary': boundary}
    elif signal_type == 'anti_causal':
        return {'type': 'half-plane', 'side': 'left', 'boundary': boundary}
    else:  # bilateral: pole pair needed, here assume two poles
        return {'type': 'strip', 'left': ..., 'right': ...}

def time_domain_signal(p, t_max=5, num_points=500):
    t = np.linspace(0, t_max, num_points)
    # x(t) = e^{-p*t} u(t) where p is complex pole location
    real_part = np.real(p)
    x = np.exp(real_part * t)
    return t, x
```

### Extension Ideas

**Beginner:**
- Start with real poles only; visualize pure exponential decay/growth.
- Provide preset pole locations (fast decay, slow decay, marginally stable).

**Advanced:**
- Introduce complex pole pairs; show effect of imaginary part on oscillation.
- Display the full transfer function $H(s) = \frac{1}{s - p}$ and its Fourier transform as $\sigma \to 0$.
- Show what happens when pole moves to the imaginary axis (marginally stable case).

**Real-world Connections:**
- Electrical circuit: pole location relates to RC time constant $\tau$; ROC determines circuit realizability.
- Control theory: unstable poles must be shifted left (into left half-plane) by feedback for stability.

---

## Simulation: Euler Method Mapping Visualization

### Lecture Source: Lecture 7, Pages 2-3 (Forward/Backward Euler Approximation)

### Visual Cues Observed
The slides show paired s-plane and z-plane diagrams with colored dots representing pole locations. For Forward Euler, dots form a circle in the z-plane; for Backward Euler, dots form another circle. The visual mapping between planes is shown explicitly: a pole at $s = -1/T$ in continuous time maps to different locations in the z-plane depending on method choice. Arrows indicate the direction of mapping; slopes and curvatures illustrate how quickly the mapping distorts high-frequency poles.

### Learning Objective
Understand that discretization is a nonlinear mapping from the s-plane to the z-plane; different methods (Forward, Backward, Tustin/Trapezoidal) produce different mappings. Develop intuition that Backward Euler is more stable than Forward Euler; Tustin preserves frequency response better. The visual breakthrough is seeing that poles near the imaginary axis (high frequency) map differently than low-frequency poles.

### Theoretical Foundation

**Forward Euler:** $s \approx \frac{z - 1}{T}$, inverse: $z \approx 1 + Ts$

- Continuous pole at $s = -1/T$ maps to $z = 1 - 1 = 0$ (good).
- Continuous pole at $s = -10/T$ maps to $z = 1 - 10 = -9$ (outside unit circle—unstable!).
- Circle in z-plane: $|z - 1| = 1$ (centered at $z = 1$ with radius 1); poles inside this circle are stable.

**Backward Euler:** $s \approx \frac{z - 1}{Tz}$, inverse: $z = \frac{1}{1 - Ts}$

- Continuous pole at $s = -1/T$ maps to $z = \frac{1}{1 + 1} = 0.5$ (inside unit circle ✓).
- Continuous pole at $s = -10/T$ maps to $z = \frac{1}{1 + 10} = 1/11 \approx 0.09$ (still inside ✓).
- All left-half-plane poles map to inside unit circle (unconditionally stable).

**Tustin (Trapezoidal):** $s \approx \frac{2}{T} \frac{z - 1}{z + 1}$, inverse: $z = \frac{1 + Ts/2}{1 - Ts/2}$

- Preserves frequency response: $s = j\omega$ maps to $z = e^{j\omega T}$ exactly at low frequencies.
- Left-half-plane poles map to inside unit circle.
- Circle: $|z| = 1$ is the image of $\Re(s) = 0$ (imaginary axis in s-plane).

### System Architecture

**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|------------|
| Continuous Pole Real | -10 to 0.5 | Exponential decay rate | Slider |
| Continuous Pole Imaginary | -5 to 5 | Oscillation frequency | Slider |
| Sampling Period T | 0.01 to 1 | Discretization step | Slider (log scale) |
| Method | {Forward, Backward, Tustin} | Discretization rule | Dropdown |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|---|---|
| Mapped Pole Location | Blue dot on z-plane | Shows where discrete pole lands |
| Stability Circle | Unit circle on z-plane | Stability boundary in discrete domain |
| Mapping Curve | Parametric curve in z-plane | Shows how entire s-plane maps |
| Method Comparison | Overlay of three mapped locations | Direct comparison of methods |

### Visualization Strategy

Three-panel layout:
- **Left Panel (s-plane):** Vertical line of poles (varying imaginary part, fixed real part). Pole location set by sliders. Highlighted pole marked with red ×.
- **Middle Panel (Mapping Display):** Shows the mapping equation and method name. Can toggle between Forward/Backward/Tustin to see all three at once or one at a time.
- **Right Panel (z-plane):** Unit circle (stability boundary); three dots representing mapped locations of the continuous pole under each method. Regions inside/outside circle shaded. When a pole is inside circle, dot glows green; outside, red.

**Interaction Flow:**
1. User adjusts continuous pole via slider (real and imaginary parts).
2. All three method circles/curves update in left panel; the specific pole location animates as it traces the circle.
3. User can vary sampling period $T$ to see how step size affects mapping severity.
4. Aha moment: As $T \to 0$ (infinitely fine sampling), all three methods converge to same z-plane location.
5. Toggling method switches which of the three dots is highlighted.

**Aha Moments:**
- Forward Euler: fast decay poles can flip to the right half-plane (instability). High-frequency content blows up.
- Backward Euler: unconditional stability—any left-half-plane pole maps inside unit circle. Trade-off: high-frequency response is distorted.
- Tustin: a "sweet spot"—preserves low-frequency response well, maps left-half-plane stably, but still some distortion at high frequencies.
- Smaller $T$ brings all three methods together; larger $T$ shows maximum divergence.

### Implementation Notes

**Complexity:** Medium

**Key Algorithms:**
- For a given continuous pole $s = \sigma + j\omega$ and method, compute the three mapped z values:
  - Forward: $z = 1 + Ts$
  - Backward: $z = \frac{1}{1 - Ts}$
  - Tustin: $z = \frac{1 + Ts/2}{1 - Ts/2}$
- Plot circles in z-plane for each method:
  - Forward Euler: circle centered at $(1, 0)$ radius $1$.
  - Backward Euler: entire left half-plane s maps inside unit circle (draw unit circle only, no specific mapping circle).
  - Tustin: unit circle is the image of imaginary axis.
- Sweep continuous pole along vertical line (increasing imaginary part) to trace the circles.

**Backend:**
```python
def forward_euler_map(s, T):
    z = 1 + T * s
    return z

def backward_euler_map(s, T):
    z = 1 / (1 - T * s)
    return z

def tustin_map(s, T):
    z = (1 + T * s / 2) / (1 - T * s / 2)
    return z

def compute_mapping_circle(T, method):
    # Parametrize continuous pole along a vertical line (imaginary axis sweep)
    omega = np.linspace(-10, 10, 200)
    s = -1 + 1j * omega  # Fixed real part, varying imaginary

    if method == 'forward':
        z_vals = [forward_euler_map(s_val, T) for s_val in s]
    elif method == 'backward':
        z_vals = [backward_euler_map(s_val, T) for s_val in s]
    else:  # tustin
        z_vals = [tustin_map(s_val, T) for s_val in s]

    return z_vals
```

### Extension Ideas

**Beginner:**
- Fix sampling period; vary continuous pole; observe mapping circles.
- Provide visual legend showing which method is which color.

**Advanced:**
- Extend to pole pairs (complex conjugate); show how natural frequency $\omega_n$ and damping $\zeta$ transform.
- Demonstrate frequency warping: for Tustin, show the warping of frequency axis (higher frequencies get compressed near $\omega = \pi/T$).
- Include zero mapping; show how a continuous zero maps under each method.

**Real-world Connections:**
- Digital filter design: choosing sampling period to ensure stability and frequency response fidelity.
- Control implementation: converting continuous-time controller to discrete-time; method choice affects closed-loop stability and bandwidth.

---

## Simulation: Convolution Flip-and-Shift Animator

### Lecture Source: Lecture 8, Pages 5-7 (Structure of Convolution)

### Visual Cues Observed
The slides show a systematic decomposition of convolution into three steps: **flip** the impulse response $h[k]$ about the origin to get $h[-k]$, **shift** by $n$ samples to get $h[n - k]$, **multiply** element-wise with input $x[k]$, and **sum**. This is shown across 4 consecutive frames, each illustrating one step of the operation for increasing $n$ values. The visual clarity is in the color-coded alignment: input samples in blue, flipped-shifted impulse response in red, products at each index highlighted.

### Learning Objective
Develop intuitive understanding of convolution as a "flipped slide" operation; understand why the flip is necessary (it's the mathematical definition, but the intuition is that we're looking backward in time for the influence of past inputs). The aha moment is realizing that convolution is correlation with the flipped signal. Seeing the shift animate left-to-right helps students internalize causality (output depends only on present and past inputs).

### Theoretical Foundation

Convolution of discrete signals:
$$y[n] = \sum_{k=-\infty}^{\infty} x[k] h[n - k]$$

Breaking it down:
1. **Flip:** Define $h_f[k] = h[-k]$ (reflection about origin).
2. **Shift:** Define $h_{n}[k] = h_f[k - n] = h[-(k - n)] = h[n - k]$ (shift by $n$).
3. **Multiply:** Compute $p_n[k] = x[k] \cdot h_n[k]$ for each $k$.
4. **Sum:** $y[n] = \sum_k p_n[k]$.

For the continuous-time analog:
$$y(t) = \int_{-\infty}^{\infty} x(\tau) h(t - \tau) d\tau$$

The shift operation $(t - \tau)$ creates the causal dependence: the output at time $t$ depends on the input from time $\tau < t$ (the past).

### System Architecture

**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|------------|
| Output Time Index n | 0 to 15 | Which output sample to compute | Slider |
| Input Signal | Preset or user-drawn | Signal being filtered | Dropdown presets (pulse, square, exponential) |
| Impulse Response | Preset (moving average, differentiator, single pulse) | System characteristic | Dropdown |
| Animation Speed | 0.5x to 2x | Slow-motion to fast replay | Slider |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|---|---|
| Input Signal x[k] | Blue stem plot, indexed by k | Shows current input |
| Impulse Response h[k] | Purple stem plot | System response (fixed reference) |
| Flipped h[-k] | Red stem plot, x-axis flipped | Step 1 visualization |
| Shifted h[n-k] | Red stem plot, shifted right by n | Step 2 visualization |
| Products x[k]·h[n-k] | Green dots/bars at each k | Step 3 visualization |
| Sum y[n] | Large number displayed; bar in output plot | Step 4 result |

### Visualization Strategy

Four-panel vertical stack, each showing one convolution step:
1. **Top Panel:** Input $x[k]$ (blue) and original impulse response $h[k]$ (purple) at the same x-axis scale. Legend labels them.
2. **Second Panel:** Input $x[k]$ (blue) and flipped impulse response $h[-k]$ (red, mirrored). Flip annotation with arrow showing the reflection.
3. **Third Panel:** Input $x[k]$ (blue) and shifted impulse response $h[n - k]$ (red, shifted right by $n$ samples). A slider or stepper control the value of $n$.
4. **Bottom Panel:** Product array $x[k] \cdot h[n - k]$ shown as green vertical bars; sum $y[n]$ displayed as a bold number and added to the bottom of the output trace plot.

**Interaction Flow:**
1. User selects a preset impulse response and input signal (or draws them interactively if time permits).
2. User adjusts slider for $n$ (current output index).
3. All four panels update in real-time: the flipped and shifted signals adjust their positions; products recalculate.
4. Optional "Animate" button: automatically advances $n$ from 0 to N, replaying the entire convolution process at controlled speed.
5. Animation pauses at each $n$ for a brief moment, then advances.

**Aha Moments:**
- The flip is not intuitive until you see it: show why it's needed (mathematical definition).
- The shift operation marches the "window" through the signal; students see causality in action.
- When $h[n - k]$ is shifted far right, it overlaps less with $x[k]$; output diminishes (edge effect).
- Convolving a pulse (single sample) with any $h$ reproduces $h$ at that location: the impulse response emerges.

### Implementation Notes

**Complexity:** High (due to animation and interactive panel updates)

**Key Algorithms:**
- Precompute or compute on-the-fly convolution for all $n$: $y = x * h$.
- For each displayed $n$: display flipped and shifted impulse response, compute products, display sum.
- Animation loop: increment $n$ by 1, wait for user-set delay, repeat.

**Backend:**
```python
def discrete_convolution(x, h):
    """Compute full convolution y[n] = sum_k x[k] h[n - k]"""
    N = len(x) + len(h) - 1
    y = np.convolve(x, h, mode='full')
    return y

def convolution_step(x, h, n):
    """Return components for display at step n"""
    h_flipped = np.flip(h)
    h_shifted = np.zeros(len(x) + len(h) - 1)
    h_shifted[n:n+len(h)] = h_flipped

    products = x * h_shifted[:len(x)]
    total = np.sum(products)

    return {
        'h_flipped': h_flipped,
        'h_shifted': h_shifted,
        'products': products,
        'sum': total
    }
```

### Extension Ideas

**Beginner:**
- Provide 2-3 preset signal pairs (e.g., pulse + moving average filter).
- Hide the flip initially; ask students to predict the output shape.

**Advanced:**
- Allow manual drawing of input and impulse response signals.
- Extend to 2D convolution (images): show how microscope blur or edge detection arises.
- Connect to Fourier domain: display FFT of $x$, $h$, and product; show $y = \text{IFFT}(X \cdot H)$.

**Real-world Connections:**
- Image processing: blurring is convolution with a blurred kernel (Gaussian).
- Audio processing: reverb is convolution with room impulse response.
- Optics (Hubble Space Telescope): deblurring images by deconvolution (inverse of convolution).

---

## Simulation: Vector Diagram Frequency Response Tracer

### Lecture Source: Lecture 9, Pages 5-8 (Vector Diagrams and Frequency Response)

### Visual Cues Observed
The slides show paired diagrams: on the left, the s-plane with a pole location marked; on the right, the magnitude and phase plots of $H(j\omega) = |H(j\omega)| \angle H(j\omega)$. As $\omega$ increases from 0 to $\infty$, a vector is drawn from the pole to the point $j\omega$ on the imaginary axis. The length and angle of this vector directly determine the magnitude and phase of the frequency response. Multiple frames show the vector at different frequencies; the magnitude plot shows that as the pole approaches the imaginary axis (near resonance), the magnitude peaks. The phase wraps from 0° to -180° as frequency sweeps. The visual power is in the geometric correspondence: a short vector means low magnitude (far from pole); a long vector at grazing angle means high magnitude and phase lag.

### Learning Objective
Understand that frequency response can be computed graphically from pole-zero locations via vector method; develop geometric intuition for how poles affect magnitude and phase. The breakthrough is realizing that a pole close to the imaginary axis creates a sharp resonance peak in the magnitude response (the vector becomes very short when $\omega$ passes near the pole). Phase response is the angle of the vector; proximity to pole inverts the angle relationship (leads to phase lag).

### Theoretical Foundation

For a transfer function $H(s) = \frac{N(s)}{D(s)}$, the frequency response is $H(j\omega) = \frac{N(j\omega)}{D(j\omega)}$.

**Magnitude:**
$$|H(j\omega)| = \frac{|N(j\omega)|}{|D(j\omega)|}$$

which is the product of distances from $j\omega$ to all zeros, divided by product of distances to all poles.

**Phase:**
$$\angle H(j\omega) = \angle N(j\omega) - \angle D(j\omega)$$

For a single pole at $s = -a$ (real pole):
$$H(s) = \frac{1}{s + a}, \quad H(j\omega) = \frac{1}{j\omega + a} = \frac{1}{\sqrt{a^2 + \omega^2}} e^{-j \arctan(\omega/a)}$$

- Magnitude decreases as $\omega$ increases (1/distance from pole to $j\omega$).
- Phase decreases from 0° to -90° as $\omega$ goes from 0 to $\infty$.

For a complex pole pair at $s = -a \pm j b$:
- Resonance peak occurs near $\omega = b$ (the imaginary part of the pole).
- Peak magnitude is inversely proportional to the real part $a$ (damping); lower $a$ = higher Q.

### System Architecture

**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|------------|
| Pole Real Part (Real Pole) | -5 to -0.1 | Damping coefficient | Slider |
| Pole Imaginary Part (Complex Pair) | -5 to 5 | Resonance frequency | Slider (for second pole; first is conjugate) |
| Frequency ω | 0.01 to 10 | Current frequency being evaluated | Draggable on imaginary axis or slider |
| Zero Location (Optional) | -5 to 5 | Adds zero to transfer function | Checkbox + slider |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|---|---|
| Pole Location | Red × on s-plane | Reference for vector drawing |
| Vector from Pole to jω | Blue arrow from pole to $j\omega$ | Determines magnitude and phase |
| Magnitude Trace | Green curve in magnitude plot | $\|H(j\omega)\|$ vs $\omega$ |
| Phase Trace | Purple curve in phase plot | $\angle H(j\omega)$ vs $\omega$ |
| Current Point | Red dot on magnitude/phase plots | Where we are on the sweep |
| Frequency Slider | Interactive slider or draggable point | Control which frequency we're evaluating |

### Visualization Strategy

Three-panel layout:
- **Left Panel (s-plane):** Show poles as red ×, zeros as red ○. Draw the vector from pole(s) to the point $j\omega$ (current frequency). Annotate vector with its length (magnitude) and angle (phase). Grid and axes labeled.
- **Middle Panel (Magnitude Response):** Plot $|H(j\omega)|$ vs $\omega$ (log-log or linear-linear; default linear). Mark current frequency with vertical dashed line and red dot on the curve.
- **Right Panel (Phase Response):** Plot $\angle H(j\omega)$ vs $\omega$. Mark current frequency similarly.

**Interaction Flow:**
1. User adjusts pole positions via sliders.
2. Magnitude and phase curves update immediately (computed via vector method or via direct formula).
3. User adjusts the frequency slider or drags the point on the imaginary axis (s-plane).
4. Blue vector updates; its length and angle directly set the magnitude and phase curve positions.
5. Optional: "Sweep" button animates frequency from 0 to max, showing the vector tracing an arc from the pole location.

**Aha Moments:**
- When frequency slider approaches the pole's location on imaginary axis, the vector becomes very short (magnitude spikes).
- A damped pole (real part $< 0$) causes a broadening of the resonance peak; higher damping = flatter response.
- Phase lag increases from 0° to -90° for a single real pole; for complex poles, the lag can reach -180° at resonance.
- The vector method makes it obvious why unstable poles (right-half-plane) cause peaking at negative frequencies.

### Implementation Notes

**Complexity:** High (real-time curve updates and animated vector drawing)

**Key Algorithms:**
- Vector method: for pole at $p$ and frequency $\omega$, compute vector $v = j\omega - p$. Magnitude is $|v|$; phase is $\arg(v)$.
- Frequency response via vector product/quotient of all pole and zero contributions.
- SciPy signal processing: use `scipy.signal.freqs()` to compute frequency response, or implement vector method manually.

**Backend:**
```python
def frequency_response_vector_method(poles, zeros, omega):
    """Compute H(jw) using vector method"""
    H_mag = 1.0
    H_phase = 0.0

    # Numerator: product of distances to zeros
    for z in zeros:
        dist_z = abs(1j * omega - z)
        H_mag /= dist_z if dist_z > 1e-10 else 1e-10
        H_phase -= np.angle(1j * omega - z)

    # Denominator: product of distances to poles
    for p in poles:
        dist_p = abs(1j * omega - p)
        H_mag *= dist_p
        H_phase += np.angle(1j * omega - p)

    return H_mag, H_phase

def compute_magnitude_phase_curves(poles, zeros, omega_vals):
    """Sweep over frequency range"""
    mags = []
    phases = []
    for omega in omega_vals:
        mag, phase = frequency_response_vector_method(poles, zeros, omega)
        mags.append(mag)
        phases.append(np.degrees(phase))
    return np.array(mags), np.array(phases)
```

### Extension Ideas

**Beginner:**
- Start with a single real pole; show how magnitude decreases monotonically.
- Add a zero; show how zero creates a minimum (magnitude goes to zero at zero frequency if zero is on $j\omega$ axis).

**Advanced:**
- Butterworth filter: add multiple poles in a circle; show how magnitude flattens in passband.
- Notch filter: place pole and zero at same frequency to create deep notch in magnitude response.
- Display group delay: $\tau_g(\omega) = -d(\angle H) / d\omega$; show how poles affect delay.

**Real-world Connections:**
- Audio equalizer: adjust pole/zero locations to boost/cut frequency bands.
- RF filter design: place poles and zeros to achieve desired passband/stopband characteristics.
- Optics (transfer function in frequency domain): how aperture size (pole location) affects diffraction pattern.

---

## Simulation: Convolution via 2D Visualization (Flip-Shift-Multiply in Space)

### Lecture Source: Lecture 8, Pages 10-12 (Microscope and Hubble Space Telescope)

### Visual Cues Observed
The slides show a real-world application: microscope and Hubble telescope point-spread functions (PSF) are visualized as 2D images. The blurred image is the convolution of the true object with the 2D PSF. Four image pairs are shown: original and blurred under different PSF diameters. The visual impact is immediate: larger PSF → more blur. The slides also show the deconvolution process (solving the inverse problem), which is essential context for understanding why convolution matters in practice.

### Learning Objective
Understand that convolution in 2D is the mathematical model of optical blurring; develop intuition that a larger PSF (wider impulse response) causes more severe blurring. The aha moment is realizing that image sharpness is limited by the diameter of the lens (related to Airy disk diffraction pattern). Deconvolution (inverting the convolution) is possible but ill-conditioned, especially if PSF is large.

### Theoretical Foundation

For 2D images, convolution is:
$$y[m,n] = \sum_{k=-\infty}^{\infty} \sum_{l=-\infty}^{\infty} x[k, l] h[m - k, n - l]$$

In the Fourier domain (convolution theorem):
$$Y(f_x, f_y) = X(f_x, f_y) \cdot H(f_x, f_y)$$

where $H(f_x, f_y)$ is the optical transfer function (OTF).

For a circular aperture of diameter $D$, the PSF is the Airy disk:
$$\text{PSF}(r) = \left[ \frac{2 J_1(r)}{r} \right]^2$$

where $r$ is the normalized radial coordinate and $J_1$ is the Bessel function of the first kind.

The Hubble Space Telescope's spherical aberration was corrected by replacing the PSF with a corrected optical system (COSTAR); the before/after images show dramatic sharpening.

### System Architecture

**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|------------|
| PSF Diameter (pixels) | 1 to 20 | Blur kernel size | Slider |
| PSF Shape | {circular, gaussian, diffraction} | Type of blurring | Dropdown |
| Input Image | Preset (test pattern, galaxy, text) | Object being imaged | Dropdown |
| Noise Level | 0 to 0.2 | Added Gaussian noise (for deconvolution challenge) | Slider |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|---|---|
| Original Image | Small thumbnail on left | Ground truth; shows what we're trying to recover |
| Blurred Image | Center large display | Result of convolution |
| Point-Spread Function (PSF) | Small thumbnail, color-coded intensity | Visualization of blurring kernel |
| Deconvolution Attempt | Small thumbnail on right | Result of inverse filtering (Wiener or regularized) |
| Frequency Domain | Magnitude of FFT before/after (optional) | Shows how blur suppresses high frequencies |

### Visualization Strategy

Horizontal layout with 4 panels:
1. **PSF Panel (small):** Display 2D PSF as a heatmap. Slider below adjusts PSF diameter; as you drag, PSF updates (recomputed as 2D Gaussian or Airy disk).
2. **Original Image Panel (medium):** Shows the true object image (e.g., a galaxy, or a test pattern like a checkerboard).
3. **Blurred Image Panel (large, center):** The convolved result; this is what the camera or telescope records. Convolve original with PSF in real-time (or pre-compute for speed).
4. **Deconvolved Image Panel (medium):** Attempt to recover original via deconvolution. Use regularized inverse filtering (Tikhonov) or Wiener filter to avoid noise amplification.

**Interaction Flow:**
1. User selects input image from dropdown.
2. User adjusts PSF diameter slider; the blurred image updates in real-time (or with a brief lag if GPU-accelerated FFT is used).
3. Optional: User adjusts noise level; deconvolution becomes noisier (demonstrating the ill-conditioned nature of deconvolution).
4. User toggles between different deconvolution methods (Wiener, regularized inverse, Lucy-Richardson) to see trade-offs.
5. Display PSNR or SSIM metric comparing deconvolved to original to quantify quality.

**Aha Moments:**
- As PSF diameter increases, blurring becomes more severe; fine details disappear.
- The Fourier domain shows that blur suppresses high frequencies (steep roll-off).
- Deconvolution can partially restore the image but introduces noise; trade-off between sharpness and noise.
- Hubble images before/after COSTAR correction: before is blurry (large PSF), after is sharp (corrected PSF).

### Implementation Notes

**Complexity:** Very High (2D FFT convolution, image processing, real-time updates)

**Key Algorithms:**
- 2D convolution via FFT (scipy.signal.convolve2d or direct FFT using numpy.fft.fft2).
- PSF generation: Gaussian (scipy.ndimage.gaussian_filter), Airy disk (scipy.special.j1), or analytical formulas.
- Deconvolution: Wiener filter, Tikhonov regularization, or Lucy-Richardson iteration.
- Image quality metrics: PSNR, SSIM (use scikit-image).

**Backend:**
```python
def gaussian_psf(size, sigma):
    """Generate 2D Gaussian PSF"""
    x = np.linspace(-size//2, size//2, size)
    xx, yy = np.meshgrid(x, x)
    psf = np.exp(-(xx**2 + yy**2) / (2 * sigma**2))
    return psf / np.sum(psf)

def convolve_image_fft(image, psf):
    """Convolve image with PSF using FFT"""
    padded_psf = np.zeros_like(image)
    padded_psf[:psf.shape[0], :psf.shape[1]] = psf
    img_fft = np.fft.fft2(image)
    psf_fft = np.fft.fft2(np.fft.ifftshift(padded_psf))
    blurred_fft = img_fft * psf_fft
    blurred = np.fft.ifft2(blurred_fft).real
    return np.clip(blurred, 0, 1)

def wiener_deconvolution(blurred, psf, noise_var=0.01):
    """Wiener filter for deconvolution"""
    img_fft = np.fft.fft2(blurred)
    psf_fft = np.fft.fft2(np.fft.ifftshift(psf))
    wiener_filter = np.conj(psf_fft) / (np.abs(psf_fft)**2 + noise_var)
    deconv_fft = img_fft * wiener_filter
    deconv = np.fft.ifft2(deconv_fft).real
    return np.clip(deconv, 0, 1)
```

### Extension Ideas

**Beginner:**
- Static PSF and image pair; user observes blur effect of changing PSF size.
- No deconvolution; focus on understanding convolution via visual comparison.

**Advanced:**
- Interactive image drawing or upload (if time permits).
- Compare different deconvolution algorithms (Wiener, Lucy-Richardson, regularized inverse).
- 3D confocal microscopy: show how z-stack (depth) convolution affects 3D reconstruction.

**Real-world Connections:**
- Hubble Space Telescope: spherical aberration corrected by COSTAR; restored images of galaxies.
- Medical imaging (CT, MRI): reconstruction algorithms invert the forward model (convolution with scanner PSF).
- Photography: software deblurring (Unsharp Mask, high-pass filtering) approximate deconvolution.

---

## Simulation: Feedback Pole Migration with Gain Control

### Lecture Source: Lecture 10, Pages 4-7 (Feedback and Control; Poles Under Feedback)

### Visual Cues Observed
The slides show a closed-loop control system block diagram with a proportional feedback gain $K$. As $K$ varies, the closed-loop poles migrate in the s-plane. Four root locus diagrams are displayed, each showing pole trajectories for different system configurations (real poles, complex poles, system with added sensor delay). The visual power is in watching the poles move: initially (K=0), they are at open-loop locations; as K increases, poles move toward zeros; at high K, poles can move to the right (instability) or split into complex conjugates (oscillation). The slides also show pole trajectories as K increases continuously, forming elegant curves (the root locus).

### Learning Objective
Understand that feedback gain controls closed-loop pole locations; develop intuition that high gain can cause instability (poles move right). The breakthrough is realizing that there's an optimal gain that achieves fast response without instability or excessive overshoot. Visualizing pole movement in real-time (as K is adjusted via slider) makes abstract transfer function poles concrete and interactive.

### Theoretical Foundation

**Open-loop transfer function:**
$$H_{\text{open}}(s) = K H_{\text{process}}(s) H_{\text{sensor}}(s)$$

**Closed-loop transfer function:**
$$H_{\text{closed}}(s) = \frac{K H_{\text{process}}(s)}{1 + K H_{\text{process}}(s) H_{\text{sensor}}(s)}$$

The closed-loop poles are the roots of:
$$1 + K H_{\text{open}}(s) = 0 \quad \Rightarrow \quad H_{\text{open}}(s) = -\frac{1}{K}$$

**Root Locus Rules:**
- Number of branches = number of open-loop poles.
- Branches start at open-loop poles (K=0) and end at open-loop zeros or infinity (K→∞).
- Branches on real axis lie left of an even number of poles/zeros.
- Asymptotes radiate from centroid of poles/zeros at angles $\pi(2m+1) / (n-m)$ where $n$ = # poles, $m$ = # zeros.

**Example: Proportional Controller on First-Order Process**
Process: $H_p(s) = \frac{1}{s + a}$ (real pole at $s = -a$)
Controller: $K$ (proportional gain)
Sensor: unity feedback
Closed-loop poles: $1 + \frac{K}{s + a} = 0 \Rightarrow s = -a - K$

As $K$ increases from 0 to $\infty$, the pole moves from $-a$ to $-\infty$ along the negative real axis. More bandwidth, faster response, but no instability (first-order system is always stable).

**Complex System Example: Second-Order With Oscillation**
Process: $H_p(s) = \frac{\omega_n^2}{(s + a)^2}$ (two poles at $s = -a$, repeated)
Closed-loop poles move as K increases:
- K=0: both poles at $-a$.
- K increases: poles move along the real axis, approaching each other.
- K = some critical value: poles become complex conjugates (Butterworth point).
- K > critical: poles move along circular arcs into the complex plane; damping decreases, oscillation increases.

### System Architecture

**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|------------|
| Feedback Gain K | 0 to 20 | Closed-loop gain | Slider |
| Process Pole(s) | Preset configurations | System dynamics | Dropdown (real, complex, multiple) |
| Sensor Delay | 0 to 1 second | Communication/measurement latency | Slider (adds $e^{-sT_d}$ term) |
| Disturbance Type | {step, impulse, sinusoid} | Test input to the system | Dropdown |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|---|---|
| Root Locus Curve | Gray curve in s-plane | Shows all possible pole locations as K varies |
| Current Pole Location | Blue dot on root locus | Where poles are at current K value |
| Closed-Loop Pole Locations | Labeled on s-plane | For checking stability (left-half-plane ✓) |
| Step Response | Time-domain plot on right panel | System output to unit step input |
| Phase Margin / Gain Margin | Text display | Stability metrics |

### Visualization Strategy

Two-panel layout:
- **Left Panel (s-plane with Root Locus):** Draw the root locus curve (gray); plot open-loop poles (red ×) and zeros (red ○). As K slider moves, a blue dot traces along the root locus, showing the current closed-loop pole location(s). Annotate the dot with the current K value and pole coordinates.
- **Right Panel (Time Domain Response):** Plot the step response $y(t)$ for current K. Overlay reference curves for comparison: underdamped, critically damped, overdamped (if applicable). Display rise time, settling time, overshoot as numerical readouts.

**Interaction Flow:**
1. User selects a process configuration (e.g., "Two Real Poles", "Complex Pole Pair").
2. Root locus curve is drawn for the selected process.
3. User adjusts the feedback gain K via slider.
4. Blue dot moves along root locus in real-time.
5. Step response updates in real-time (computed via closed-loop transfer function).
6. As K increases past a critical threshold, pole crosses into right-half-plane; step response overshoots or diverges; system becomes unstable (color change or warning).
7. Optional: sensor delay slider adds a $e^{-sT_d}$ factor, which causes pole locus to spiral (advanced).

**Aha Moments:**
- For a first-order system, increasing K always stabilizes; poles move left (faster response).
- For a second-order system, there's a range of K where response is well-damped; too much K causes oscillation or instability.
- Root locus is a powerful design tool: by adjusting a single parameter (K), you can see exactly how the system's dynamics change.
- Sensor delay destabilizes the system: root locus branches move rightward; critical gain K_crit decreases.

### Implementation Notes

**Complexity:** High (root locus computation, real-time pole tracking, step response simulation)

**Key Algorithms:**
- Root locus: for each K in range, find roots of $1 + K H_{\text{open}}(s) = 0$ using numpy.roots() or scipy.optimize.fsolve.
- Alternatively, sample the root locus: for given K, find roots of characteristic polynomial.
- Step response: compute closed-loop transfer function, use scipy.signal.step() or scipy.signal.lti.step().
- Display root locus as parametric curve (K as parameter).

**Backend:**
```python
def closed_loop_poles(open_loop_poles, open_loop_zeros, K):
    """Find closed-loop poles for given K"""
    # Characteristic equation: 1 + K * H_open(s) = 0
    # If H_open(s) = prod(s - z) / prod(s - p), then
    # prod(s - p) + K * prod(s - z) = 0
    # Expand and solve
    num_coef, den_coef = sp.signal.zpk2tf(open_loop_zeros, open_loop_poles, K)
    char_poly = np.polyadd(den_coef, num_coef)  # 1 + K H_open
    poles = np.roots(char_poly)
    return poles

def root_locus(open_loop_poles, open_loop_zeros, K_range):
    """Compute root locus for range of K values"""
    locus_points = []
    for K in K_range:
        poles = closed_loop_poles(open_loop_poles, open_loop_zeros, K)
        locus_points.append(poles)
    return locus_points

def step_response_closed_loop(open_loop_tf, K):
    """Compute step response of closed-loop system"""
    num, den = open_loop_tf
    closed_loop_num = K * num
    closed_loop_den = np.polyadd(den, K * num)
    t, y = sp.signal.step((closed_loop_num, closed_loop_den))
    return t, y
```

### Extension Ideas

**Beginner:**
- Single real pole only; show how K moves pole along negative real axis.
- Provide presets: "underdamped", "critically damped", "overdamped" configurations.

**Advanced:**
- Bode plot overlay: show gain margin and phase margin (stability metrics).
- Lead-compensator: add a zero in the s-plane (via slider) and show how it changes root locus and step response.
- Sensor delay: show root locus for different delays; demonstrate destabilization.

**Real-world Connections:**
- Cruise control: maintaining vehicle speed via feedback; too high gain causes oscillation (hunting).
- Temperature control: thermostat gain tuning; overshooting damages equipment.
- Robot arm: position control; high gain causes vibration and instability.
- Aircraft autopilot: control loop with communication delay; must maintain phase margin to prevent instability.

---

## Simulation: Bode Plot Constructor (Magnitude & Phase Assembly)

### Lecture Source: Lecture 10, Pages 1-9 (Bode Diagrams; Feedback and Control Summary)

### Visual Cues Observed
The slides show the methodology for constructing Bode plots: break the transfer function into poles and zeros, plot each contribution separately (as straight lines on log-log and semi-log plots), then add them up. The magnitude Bode plot is in dB (20 log10|H|); the phase plot is in degrees. Asymptotic approximations (corner frequencies at pole/zero locations, slopes of ±20 dB/decade for single poles/zeros) are shown. The visual insight is watching how multiple poles and zeros combine to form the overall response shape.

### Learning Objective
Understand the method for manually sketching Bode plots without a computer; develop intuition for how poles and zeros affect the magnitude and phase at different frequencies. The aha moment is realizing that Bode plots can be hand-drawn using simple rules (straight-line asymptotes, corner frequencies, slopes). This builds confidence that transfer function analysis is tractable without simulation.

### Theoretical Foundation

**Magnitude (in dB):**
$$20 \log_{10} |H(j\omega)| = 20 \log_{10} |K| + \sum_k 20 \log_{10} |1 + j\omega/z_k| - \sum_j 20 \log_{10} |1 + j\omega/p_j|$$

Each term $20 \log_{10} |1 + j\omega/a|$ (for pole at $-a$ or zero at $-a$) contributes:
- At low frequencies ($\omega \ll a$): 0 dB.
- At corner frequency $\omega = a$: 3 dB.
- At high frequencies ($\omega \gg a$): asymptotic slope of ±20 dB/decade (−20 for pole, +20 for zero).

**Phase (in degrees):**
$$\angle H(j\omega) = \angle K + \sum_k \angle(1 + j\omega/z_k) - \sum_j \angle(1 + j\omega/p_j)$$

where $\angle(1 + j\omega/a) = \arctan(\omega/a)$ ranges from 0° (at $\omega = 0$) to 90° (at $\omega \to \infty$) for zeros, and from 0° to −90° for poles.

**Composite Bode Plot:**
- Add contributions from all poles and zeros.
- Use asymptotic straight lines between corner frequencies.
- Mark corner frequencies with circle markers or annotations.

### System Architecture

**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|------------|
| Pole 1 Real Part | -10 to 0 | First pole location (s = -a) | Slider |
| Pole 2 Real Part | -10 to 0 | Second pole location | Slider (optional, if enabled) |
| Zero 1 Real Part | -10 to 0 | First zero location | Slider (optional) |
| DC Gain K | 0.1 to 100 | Constant gain factor | Slider |
| Display Mode | {Magnitude only, Phase only, Both} | Which curves to show | Radio buttons |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|---|---|
| Individual Pole/Zero Contributions | Colored straight-line asymptotes | Deconstruction of overall response |
| Composite Magnitude Plot | Bold black curve, semi-log (frequency log) | Combined magnitude response |
| Asymptotic Approximation | Gray dashed line | Hand-drawn estimate |
| Corner Frequencies | Circle markers on x-axis | Reference frequencies |
| Composite Phase Plot | Bold black curve, semi-log | Combined phase response |
| Exact Curve (optional) | Thin blue overlay | Precise numerical computation for comparison |

### Visualization Strategy

Two vertically stacked panels:
- **Top Panel (Magnitude Bode Plot):** X-axis is log frequency (rad/s); y-axis is magnitude in dB. Plot individual pole and zero contributions as colored straight-line asymptotes. Sum them to get the composite (bold black curve). Overlay the exact curve in a different color to show accuracy of asymptotic approximation. Mark corner frequencies with circle markers.
- **Bottom Panel (Phase Bode Plot):** X-axis is log frequency; y-axis is phase in degrees. Plot individual contributions (each pole/zero contributes 0° at DC, ramping to ±90° at high frequency). Sum contributions for composite phase. Overlay exact curve.

**Interaction Flow:**
1. User adjusts pole and zero sliders.
2. Individual contribution curves update in real-time (recompute asymptotes, recompute exact curves).
3. Composite curves update by summing contributions.
4. User can toggle "Show Exact vs. Asymptotic" to compare hand-drawn vs. computed accuracy.
5. User hovers over corner frequency markers to see frequency value and dB/decade slope.
6. Optional: "Animate Assembly" button plays a video of contributions being added one by one.

**Aha Moments:**
- Each pole at $s = -a$ contributes −20 dB/decade slope above corner frequency $\omega = a$.
- Multiple poles stack: two poles give −40 dB/decade, etc.
- Zeros do the opposite: +20 dB/decade slope.
- Phase response lags for poles, leads for zeros; understanding this geometrically is powerful.
- Asymptotic approximation (straight lines) is surprisingly accurate except near corner frequencies (±3 dB at corner, smooth curve vs. abrupt corner).

### Implementation Notes

**Complexity:** Medium (Bode plot computation, line drawing, overlays)

**Key Algorithms:**
- Asymptotic Bode plot: identify all corner frequencies, compute slopes between corners, draw straight lines.
- Exact Bode plot: evaluate $H(j\omega)$ at many frequency points; use numpy.abs() and numpy.angle() for magnitude and phase.
- Log-log and semi-log axes: use matplotlib's LogScale for x-axis, linear for magnitude (dB) and phase (deg) y-axes.

**Backend:**
```python
def bode_asymptotic(poles, zeros, K, frequencies):
    """Compute asymptotic Bode plot (straight-line approximation)"""
    # Collect all corner frequencies (pole and zero locations)
    corners = np.sort(np.abs(np.concatenate([poles, zeros])))

    magnitude_db = 20 * np.log10(K)  # Start with DC gain
    phase_deg = 0.0  # Start with zero phase

    # For each segment between corners, compute slope
    # Magnitude: -20 dB/decade per pole, +20 dB/decade per zero
    # Phase: -90 deg/decade per pole, +90 deg/decade per zero

    slopes_mag = {}
    slopes_phase = {}

    for freq in frequencies:
        mag = 20 * np.log10(K)
        phase = 0.0

        for p in poles:
            mag -= 20 * np.log10(np.abs(freq / p)) if freq > np.abs(p) else 0
            phase -= 90.0 if freq > np.abs(p) else 45 * (np.log10(freq) - np.log10(np.abs(p)))

        for z in zeros:
            mag += 20 * np.log10(np.abs(freq / z)) if freq > np.abs(z) else 0
            phase += 90.0 if freq > np.abs(z) else 45 * (np.log10(freq) - np.log10(np.abs(z)))

        # Refined asymptotic: linear interpolation around corners

    return magnitude_db, phase_deg

def bode_exact(poles, zeros, K, frequencies):
    """Compute exact Bode plot numerically"""
    num = K * np.poly(zeros)  # Transfer function numerator (K * prod(s - z))
    den = np.poly(poles)      # Denominator: prod(s - p)

    w, mag, phase = sp.signal.bode((num, den), w=frequencies)
    return w, mag, np.degrees(phase)
```

### Extension Ideas

**Beginner:**
- Provide presets: single pole, two poles, pole-zero pair.
- Hide exact curve initially; ask user to sketch asymptotic approximation by hand, then reveal exact curve for comparison.

**Advanced:**
- Extend to complex poles; show resonance peaks and peaking correction.
- Relate Bode plot to stability: show gain margin and phase margin graphically.
- Design a compensator: add a lead zero; show how it improves phase margin.

**Real-world Connections:**
- Op-amp circuit design: RC filter poles determine rolloff frequency; Bode plot predicts circuit gain vs. frequency.
- Power supply feedback loop: Bode plot margin analysis predicts instability or oscillation.
- Audio speaker: frequency response (Bode plot) determines tonal balance; crossover design uses Bode analysis.

---

## Simulation: System Identification via Frequency Response Fitting

### Lecture Source: Lecture 10, Pages 2-3 (System Identification; Perching Glider Data)

### Visual Cues Observed
The slides show experimental Lift Coefficient and Drag Coefficient curves as functions of Angle of Attack (α). The data is plotted against theoretical flat-plate theory curves. The visual cue is that experimental data often deviates from simple models, requiring system identification to extract true parameters. The Perching Problem is a real application where control design depends on knowing the true system model; the slides show how coefficient data is extracted from flight experiments.

### Learning Objective
Understand that real systems are more complex than textbook models; system identification is the art of inferring a system model from input-output data. The learning objective bridges theory (transfer functions, differential equations) with practice (fitting data to models). The aha moment is realizing that a good model is a compromise between simplicity and accuracy; overfit models are useless for control design.

### Theoretical Foundation

**System Identification Problem:**
Given input signal $u(t)$ and output signal $y(t)$, find a transfer function $H(s) = \frac{N(s)}{D(s)}$ that best predicts the output.

**Frequency Response Fitting:**
1. Apply sinusoidal inputs at multiple frequencies $\omega_1, \omega_2, \ldots, \omega_N$.
2. For each frequency, measure magnitude $|H(j\omega_i)|$ and phase $\angle H(j\omega_i)$.
3. Fit a rational transfer function model to the frequency response data using least-squares optimization.

**Example: First-Order Lag**
Assume a model: $H(s) = \frac{K}{1 + \tau s}$ (two parameters: gain $K$ and time constant $\tau$).
Frequency response: $|H(j\omega)| = \frac{K}{\sqrt{1 + (\omega \tau)^2}}$
Fit $K$ and $\tau$ to minimize: $\sum_i (|H(j\omega_i)|_{\text{measured}} - |H(j\omega_i)|_{\text{model}}|)^2$

### System Architecture

**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|------------|
| Model Order (# poles) | 1 to 4 | Complexity of assumed system | Slider or dropdown |
| Model Type | {Real poles, Complex poles, Mixed} | Pole configuration | Dropdown |
| Input Signal | {Sinusoidal sweep, White noise, Chirp} | Excitation signal | Dropdown |
| Noise Level | 0 to 0.2 | SNR of measurement | Slider |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|---|---|
| Measured Frequency Response | Blue dots on Bode plot | Experimental data |
| Fitted Model Response | Red curve on Bode plot | Best-fit transfer function |
| Fitted Poles/Zeros | × and ○ on s-plane | Identified system dynamics |
| Residual Error | Bode plot error bands or separate curve | Goodness of fit |
| Model Parameters | Text display (K, τ, ω_n, ζ, etc.) | Extracted parameters and uncertainties |

### Visualization Strategy

Three-panel layout:
- **Left Panel (s-plane):** Show fitted poles (red ×) and zeros (red ○). As fitting algorithm runs, poles animate toward converged locations.
- **Center Panel (Magnitude Bode):** Plot measured frequency response data as blue dots; overlay the fitted transfer function as a red curve. Fill error band (±1 std) around measured data.
- **Right Panel (Phase Bode):** Similar to magnitude; phase data points and fitted model.

**Interaction Flow:**
1. User selects model order (e.g., "Second-Order" = 2 poles) and type (e.g., "Complex Pole Pair").
2. User simulates the system or uploads pre-recorded input-output data.
3. Backend computes frequency response via FFT or step response.
4. Fitting algorithm (least-squares, maximum likelihood) optimizes pole locations to minimize error.
5. Fitted model converges; poles/zeros move to final locations on s-plane.
6. User can adjust model order; refitting recomputes poles and updates all views.
7. Display metrics: fit quality (R², RMSE), pole/zero locations with confidence intervals.

**Aha Moments:**
- Model order trade-off: higher order fits data better but risks overfitting (poor generalization).
- Adding noise to measurements makes fitting harder; algorithm must balance fit quality vs. robustness.
- Perching glider example: real lift and drag data deviate from simple theory; identified model is essential for control design.
- Visual inspection of residuals (measured vs. fitted) reveals whether model is adequate.

### Implementation Notes

**Complexity:** Very High (optimization, statistical analysis, real-time refitting)

**Key Algorithms:**
- Frequency response from data: scipy.signal.freqs() or manual FFT.
- Curve fitting: scipy.optimize.least_squares() or scipy.signal.lti.fit_freq_response() (if available).
- Uncertainty quantification: bootstrap or asymptotic Cramér-Rao bounds.

**Backend:**
```python
def fit_transfer_function(freq_data, mag_data, phase_data, poles_init):
    """Fit TF model to frequency response data via least-squares"""
    def error_func(poles_zeros):
        # Unpack poles and zeros from parameter vector
        poles = poles_zeros[:len(poles_init)]
        zeros = poles_zeros[len(poles_init):]

        # Compute model frequency response
        mag_model = compute_mag_bode(poles, zeros, freq_data)
        phase_model = compute_phase_bode(poles, zeros, freq_data)

        # Compute error
        error = np.sum((mag_model - mag_data)**2 + (phase_model - phase_data)**2)
        return error

    # Optimize
    result = sp.optimize.least_squares(error_func, poles_init)
    return result.x

def compute_mag_bode(poles, zeros, freq):
    """Compute magnitude response at given frequencies"""
    mag = np.ones_like(freq)
    for p in poles:
        mag /= np.abs(1j * freq - p)
    for z in zeros:
        mag *= np.abs(1j * freq - z)
    return 20 * np.log10(mag)
```

### Extension Ideas

**Beginner:**
- Provide pre-fitted models for comparison (overfitted vs. good fit).
- Show only magnitude fitting initially; add phase fitting as an advanced option.

**Advanced:**
- Time-domain fitting: use ARMA model (autoregressive moving-average) and fit difference equations directly.
- Stability-constrained fitting: ensure all fitted poles are in left-half-plane (required for passive systems).
- Bayesian model selection: automatically choose model order to balance fit quality and complexity (MDL criterion).

**Real-world Connections:**
- Aircraft dynamics: fit from flight test data to obtain transfer functions for autopilot design.
- Robotics: identify motor dynamics (inductance, damping) from step response measurements.
- Power systems: identify generator and grid models from disturbance response.

---

## Simulation: Laplace Transform Property Explorer (Shifting, Scaling, Differentiation)

### Lecture Source: Lecture 6, Pages 5-6 (Laplace Transform Properties)

### Visual Cues Observed
The slides show a comprehensive table of Laplace transform properties: linearity, time shift, frequency shift, differentiation, integration, convolution, initial value theorem, final value theorem. Each property is accompanied by a mathematical statement and sometimes a graphical illustration of the effect (e.g., time shift causes a phase delay in frequency domain, differentiation causes pole migration). The visual organization makes it clear that these properties are interrelated and form a coherent system.

### Learning Objective
Understand the fundamental properties of the Laplace transform and how they relate time-domain and frequency-domain manipulations. The aha moment is realizing that complex time-domain operations (differentiation, convolution) become simple algebraic operations in the Laplace domain. This is the power of the transform: it converts hard differential equations into polynomial equations.

### Theoretical Foundation

**Key Properties:**

1. **Linearity:** $\mathcal{L}\{a x(t) + b y(t)\} = a X(s) + b Y(s)$

2. **Time Shift:** $\mathcal{L}\{x(t - T) u(t - T)\} = e^{-sT} X(s)$

3. **Frequency Shift (Modulation):** $\mathcal{L}\{e^{-at} x(t)\} = X(s + a)$

4. **Differentiation:** $\mathcal{L}\{x'(t)\} = s X(s) - x(0^-)$

5. **Integration:** $\mathcal{L}\{\int_0^t x(\tau) d\tau\} = \frac{X(s)}{s}$

6. **Convolution (Time Domain):** $\mathcal{L}\{(x * h)(t)\} = X(s) H(s)$

7. **Initial Value Theorem:** $x(0^+) = \lim_{s \to \infty} s X(s)$

8. **Final Value Theorem:** $x(\infty) = \lim_{s \to 0} s X(s)$ (if limit exists and $x(\infty)$ exists)

### System Architecture

**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|------------|
| Base Signal | {Exponential, Sine, Ramp, Impulse, Step} | Reference signal to which properties apply | Dropdown |
| Property to Apply | {Shift, Scale, Differentiate, Integrate, etc.} | Which property to demonstrate | Dropdown |
| Property Parameter | Variable (delay, damping factor, etc.) | Specific value for property | Slider |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|---|---|
| Original Signal x(t) | Time-domain plot, left panel | Reference |
| Transformed Signal (property applied) | Time-domain plot, middle panel | Result of property in time domain |
| Original Transform X(s) | s-plane pole-zero diagram + formula | Reference |
| Transformed Transform | s-plane diagram + formula, right panel | Result in frequency domain |
| Property Statement | Equation displayed at top | Mathematical definition |

### Visualization Strategy

Three-column layout:
- **Left Column (Original Signal):** Time-domain plot of base signal $x(t)$; pole-zero diagram of $X(s)$.
- **Center Column (Property Details):** Display the property equation in LaTeX. Show the specific parameter value being applied (e.g., delay $T = 1$ second, damping $a = 2$).
- **Right Column (Transformed Signal):** Time-domain plot of the result after applying the property; pole-zero diagram of transformed $X_{\text{new}}(s)$.

**Interaction Flow:**
1. User selects a base signal (e.g., exponential decay).
2. Original signal plot and Laplace transform appear (poles/zeros).
3. User selects a property (e.g., "Time Shift").
4. Property equation and parameter slider appear.
5. User adjusts the slider (e.g., delay time $T$).
6. Transformed signal and transform update in real-time.
7. Right column shows how the time-domain signal shifts and how the pole-zero diagram changes (poles move due to $e^{-sT}$ multiplication).

**Aha Moments:**
- Time shift: signal is delayed in time; in frequency domain, it's multiplied by $e^{-sT}$ (a phase lag of magnitude 1, phase angle −$sT$).
- Frequency shift: signal is damped exponentially in time; in frequency domain, poles shift left by the damping coefficient.
- Differentiation: slopes are steeper; in frequency domain, transfer function gains an 's' factor (pole at origin removed, one-order increase).
- Integration: signal is smoothed; in frequency domain, a pole is added at origin.
- The same symbol 's' appears in both property equations and pole-zero diagrams, making the connection clear.

### Implementation Notes

**Complexity:** Medium (interactive parameter updates, real-time signal/pole-zero recomputation)

**Key Algorithms:**
- Precompute a library of base signals and their Laplace transforms (poles, zeros, formula).
- For each property applied, compute the transformed signal and transform analytically or numerically.
- Update pole-zero diagram dynamically (add/remove/shift poles).

**Backend:**
```python
def apply_property(signal_type, property_name, parameter):
    """Apply a Laplace property to a base signal"""

    if signal_type == 'exponential':  # x(t) = e^{-at} u(t), X(s) = 1/(s+a)
        poles_original = [-1.0]  # Default a=1
        X_original = lambda s: 1 / (s + 1)
    # ... other signal types

    if property_name == 'time_shift':  # x(t-T) -> e^{-sT} X(s)
        T = parameter
        X_new = lambda s: np.exp(-s * T) * X_original(s)
        poles_new = poles_original  # Poles don't move; gain gets e^{-sT}
        phase_shift = -parameter * np.real(poles_original[0])  # Illustrative

    elif property_name == 'frequency_shift':  # e^{-at} x(t) -> X(s+a)
        a = parameter
        X_new = lambda s: X_original(s + a)
        poles_new = [p - a for p in poles_original]  # Poles shift left

    elif property_name == 'differentiation':  # x'(t) -> s X(s) - x(0)
        X_new = lambda s: s * X_original(s)  # Ignore initial condition for simplicity
        poles_new = poles_original  # Add pole at origin if not already there

    # ... other properties

    return X_new, poles_new
```

### Extension Ideas

**Beginner:**
- Start with time shift and frequency shift (simplest properties).
- Provide a "Property Reference Card" showing all 8 properties with visual examples.

**Advanced:**
- Combine multiple properties: apply time shift then differentiation; show that order matters (commutative vs. non-commutative).
- Prove a property numerically: compute Laplace transform directly via integration, compare to property prediction.

**Real-world Connections:**
- Control system design: use properties to convert differential equations into algebraic equations, solve for closed-loop transfer function.
- Circuit analysis: differentiation property converts capacitor voltage-current relationship into algebraic form (impedance model).
- Signal processing: convolution property enables filter implementation via Laplace (transfer function).

---

## Summary

This batch of 8 novel simulations spans Lectures 6–10, addressing:

1. **ROC Explorer** (Lecture 6): Interactive s-plane with dynamic ROC region shading.
2. **Euler Mapping** (Lecture 7): Discretization method comparison, pole movement visualization.
3. **Convolution Animator** (Lecture 8): Step-by-step flip-shift-multiply-sum breakdown.
4. **2D Convolution (Optics)** (Lecture 8): Microscope/Hubble blurring and deconvolution.
5. **Vector Diagram Tracer** (Lecture 9): Pole-to-jω vector determines magnitude and phase.
6. **Bode Constructor** (Lecture 10): Asymptotic vs. exact Bode plot assembly.
7. **Feedback Pole Migration** (Lecture 10): Root locus with real-time gain adjustment.
8. **System Identification** (Lecture 10): Fit transfer function model to frequency response data.
9. **Laplace Properties** (Lecture 6): Interactive property demonstrations (shift, scale, differentiate, integrate).

All simulations prioritize visual intuition, interactive exploration, and real-world grounding. Implementation spans Medium to Very High complexity; suitable for phased development.
