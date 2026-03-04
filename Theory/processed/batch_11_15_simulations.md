# MIT 6.003 Lectures 11-15: New Simulation Specifications

## Simulation: Bode Plot Constructor from Poles and Zeros

### Lecture Source: Lecture 11-2, Pages 3-34

### Learning Objective
Build intuition for how individual poles and zeros contribute additively (in logarithmic space) to create complex frequency response Bode plots. Students discover the deep principle that pole/zero locations directly encode asymptotic behavior.

### Theoretical Foundation
$$H(s) = K \frac{\prod_{q} (s - z_q)}{\prod_{p} (s - p_p)}$$

Magnitude on log-log axes:
$$\log |H(j\omega)| = \log |K| + \sum_q \log|j\omega - z_q| - \sum_p \log|j\omega - p_p|$$

Phase:
$$\angle H(j\omega) = \angle K + \sum_q \angle(j\omega - z_q) - \sum_p \angle(j\omega - p_p)$$

Key relationships: asymptotic slopes (20 dB/decade per pole/zero), corner frequencies, high/low frequency limits.

### System Architecture

**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|-----------|
| num_zeros | 0-4 | Number of finite zeros | Stepper |
| num_poles | 1-4 | Number of finite poles | Stepper |
| zero_locations[i] | -10 to 10 (real), -5 to 5 (imag) | s-plane position of ith zero | Draggable point in s-plane |
| pole_locations[i] | -10 to 10 (real), -5 to 5 (imag) | s-plane position of ith pole | Draggable point in s-plane |
| DC_gain | 0.1 to 100 | Static gain at DC | Slider |
| frequency_decade | -2 to 4 | Log10 of frequency range | Auto or manual |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|----------------|---------|
| s-plane diagram | Interactive 2D plot with draggable poles (X) and zeros (O) | Spatial intuition for pole/zero placement |
| Magnitude Bode (exact) | Colored trace on log-log axes | Ground truth |
| Magnitude Bode (asymptotic) | Piecewise linear segments matching asymptotic behavior | Reveals approximation quality |
| Phase Bode (exact) | Colored trace on semilog axes | Ground truth |
| Phase Bode (asymptotic) | Piecewise linear segments with 45°/decade slopes near corners | Asymptotic approximation |
| Individual contributions | Stacked/toggleable traces for each pole and zero | Decomposition insight |
| Residual magnitude | Difference between exact and asymptotic | Error quantification |

### Visualization Strategy

**Main workflow:**
1. Student places 1-2 poles and zeros on the s-plane by dragging
2. Real-time Bode plots update with exact and asymptotic overlays
3. Colored bands highlight regions where asymptotes diverge significantly
4. Toggle individual pole/zero contributions to see how they sum (in dB space)
5. Vertical dashed lines mark corner frequencies (at pole/zero magnitudes)
6. The "aha moment" occurs when students realize:
   - Each pole/zero adds/subtracts 20 dB/decade at high frequencies
   - Phase response has characteristic shape: 90° transition centered at corner frequency
   - Multiple poles stack their effects: -40 dB/decade for double pole
   - Pole-zero cancellations create "missing" sections in the magnitude response

**Interactive affordances:**
- Snapping grid in s-plane to quantize positions
- Constraint: poles must have negative real parts (for stability in demo mode)
- Display pole/zero multiplicity if user tries to place two at same location
- Separate tabs for magnitude and phase, or vertically stacked in responsive layout

### Implementation Notes

**Complexity:** Medium

**Key Algorithms:**
- Vectorized pole/zero evaluation: $|j\omega - p| = \sqrt{\omega^2 + \mathrm{Re}(p)^2}$ at each frequency point
- Asymptotic approximation: detect which regime (low/high frequency relative to all corner frequencies)
- Magnitude sum in dB: $20\log_{10}|K| + \sum 20\log_{10}|j\omega - z_q| - \sum 20\log_{10}|j\omega - p_p|$
- Phase accumulation: vectorized arctan2 for each pole/zero contribution

**Dependencies:**
- NumPy for vectorized arithmetic
- SciPy.signal for optional validation (zpk2sos)
- Plotly for dual-panel Bode rendering with asymptotic overlays

### Extension Ideas

**Beginner:**
- "Design a low-pass filter": place single pole at $s = -\omega_c$, observe how magnitude falls 20 dB/decade
- "Create a notch": place pole-zero pair at same location, drag apart slightly to see bandwidth effect
- Presets: load classic filter topologies (Butterworth 2nd order, etc.)

**Advanced:**
- Stability margin visualization: shading in s-plane showing gain margin and phase margin
- Nyquist plot generation from same pole-zero set
- Time-domain step/impulse response synced with pole location
- Phase margin indicator: draw tangent line to Nyquist at critical frequency

**Real-world:**
- Audio equalizer design: place peaks (pole-zero pairs with imaginary parts) at specific audio frequencies
- Control system compensator tuning: observe how lead/lag networks (first-order poles and zeros) modify Bode plots
- Filter rolloff comparison: explore why 4th-order filters have steeper slopes than 2nd-order

---

## Simulation: High-Q Resonator Response Landscape

### Lecture Source: Lecture 11-2, Pages 43-62

### Learning Objective
Understand how the Q factor controls peak height and phase transition sharpness in resonant systems. Build geometric intuition by visualizing how pole locations in the s-plane translate to frequency-domain peaking and phase behavior.

### Theoretical Foundation

$$H(s) = \frac{1}{1 + \frac{1}{Q}\frac{s}{\omega_0} + \left(\frac{s}{\omega_0}\right)^2}$$

Pole locations (for Q > 0.5):
$$s = -\frac{\omega_0}{2Q} \pm j\omega_0\sqrt{1 - \frac{1}{4Q^2}}$$

Peak magnitude (Q >> 1): $|H(j\omega_0)| \approx Q$

Bandwidth (3dB): $\Delta\omega \approx \frac{\omega_0}{Q}$

Phase transition: $\approx \frac{\pi}{2}$ over one octave centered at $\omega_0$

### System Architecture

**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|-----------|
| quality_factor | 0.5 to 50 | Q = ω₀ / bandwidth | Slider (logarithmic) |
| center_frequency | 0.1 to 10 Hz | ω₀ / (2π) | Slider (logarithmic) |
| input_amplitude | 0 to 2 | Drive level for sinusoidal input | Slider |
| input_frequency | 0.01 to 100 Hz | Frequency of input tone | Slider or expression |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|----------------|---------|
| s-plane poles | 2D scatter plot with conjugate pair highlighted | Spatial relationship: higher Q = closer to imaginary axis |
| Magnitude response | Log-linear plot with peak height label | Frequency selectivity |
| Phase response | Semilog plot with -90° crossover at ω₀ | Phase delay over bandwidth |
| Time-domain waveform | Real signal: input (faint) + output (bright) overlaid | Observing resonance buildup and phase lag |
| Input vs output phasor | Rotating vectors showing magnitude ratio and phase difference | Instantaneous amplitude and lag |
| Resonance map heatmap | 2D grid: frequency (x-axis) vs. Q (y-axis), color = magnitude | Landscape view of how Q shapes response |

### Visualization Strategy

The core "aha" comes from linking three representations:
1. **S-plane view**: Drag poles around a circle centered at origin; as Q increases, poles approach the imaginary axis
2. **Frequency response**: In real-time, see peak height *increase* and bandwidth *narrow* as poles move closer to axis
3. **Time-domain sinusoid**: Show a sinusoidal input at variable frequency; when sweeping through resonance, output amplitude peaks dramatically

**Interactive flow:**
- Slider controlling Q: watch poles spiral inward toward jω axis; watch peak sharpen; watch bandwidth label shrink as 1/Q
- Display "residence time" metric: τ = Q / ω₀ (how long transients persist)
- Show **resonance map** as background heatmap: frequency on x, Q on y; color = magnitude response; user's current state highlighted
- Overlay the 3dB bandwidth as a shaded region on magnitude plot
- Animated frequency sweep: show a moving vertical line on Bode plot while sinusoid response animates in time domain

**Pedagogical moments:**
- "High Q = narrow peak": compare Q=1 vs Q=10 response side-by-side
- "Phase transitions sharply near resonance": phase changes from +90° to -90° in roughly one octave
- "Residence time τ scales with Q": after input is removed, oscillation decays exponentially with time constant τ = Q/ω₀

### Implementation Notes

**Complexity:** Medium

**Key Algorithms:**
- Second-order system transfer function evaluation at complex frequency s = σ + jω
- Pole locations: $p = -\frac{\omega_0}{2Q} \pm j\omega_0\sqrt{1 - \frac{1}{4Q^2}}$
- Time-domain convolution or direct filter application to input sinusoid
- Resonance map generation: 2D grid of (freq, Q) pairs → magnitude evaluation

**Dependencies:**
- NumPy for transfer function evaluation
- SciPy.signal.lfilter for time-domain filtering
- Plotly for heatmap rendering

### Extension Ideas

**Beginner:**
- "Find the peak": given an unknown Q, predict the peak magnitude and compare to measured
- Presets: mechanical oscillator, RLC circuit, microwave cavity resonator with realistic Q values
- Label important Q milestones: Q=0.5 (critically damped), Q=0.707 (Butterworth), Q=10 (high selectivity)

**Advanced:**
- Coupled oscillators: two resonators with adjustable coupling; observe split resonance peaks (Rabi splitting)
- Driving a resonator and measure transient buildup time vs. Q
- Phase margin analysis: Nyquist plot showing how close poles are to instability

**Real-world:**
- Audio speaker crossover network design: placing resonances at specific frequencies
- RF circuit design: Q factor of antennas and filters at GHz frequencies
- Seismic resonance of buildings: how to design structures to avoid earthquakes matching building's natural frequency

---

## Simulation: Feedback Gain-Bandwidth Tradeoff Visualizer

### Lecture Source: Lecture 12, Pages 14-23

### Learning Objective
Demonstrate the fundamental principle that negative feedback trades DC gain for bandwidth. By varying the feedback factor β and observing how the closed-loop pole moves along the real axis, students internalize why high gain and wide bandwidth are mutually exclusive in a single-loop feedback system.

### Theoretical Foundation

Open-loop system:
$$H_o(s) = \frac{\alpha K_0}{s + \alpha}$$

Closed-loop system with feedback β:
$$H_c(s) = \frac{H_o(s)}{1 + \beta H_o(s)} = \frac{\alpha K_0}{s + \alpha + \alpha\beta K_0} = \frac{\alpha K_0}{s + \alpha(1 + \beta K_0)}$$

Closed-loop pole: $s_p = -\alpha(1 + \beta K_0)$

Closed-loop DC gain: $H_c(0) = \frac{K_0}{1 + \beta K_0}$

Bandwidth (3dB): $\omega_{3dB} = \alpha(1 + \beta K_0) = |s_p|$

Product (gain-bandwidth product is constant):
$$\text{DC Gain} \times \text{Bandwidth} = \frac{K_0}{1 + \beta K_0} \times \alpha(1 + \beta K_0) = \alpha K_0 = \text{constant}$$

### System Architecture

**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|-----------|
| feedback_beta | 0 to 1 | Feedback fraction; β=0 is open-loop | Slider |
| op_amp_gain | 1e4 to 1e6 | K₀ in open-loop DC gain | Slider (logarithmic) |
| op_amp_pole | 10 to 1000 rad/s | α in single pole model | Slider |
| input_signal | sine/step/chirp | Test signal type | Dropdown |
| signal_frequency | 1 to 1e6 Hz | For sinusoid or chirp starting frequency | Slider |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|----------------|---------|
| s-plane poles | Open-loop pole (gray X) and closed-loop pole (red X) | Show how feedback moves pole further left |
| Magnitude Bode (magnitude) | Overlaid open-loop (faint) and closed-loop (bright) | Demonstrate bandwidth expansion |
| Magnitude Bode (DC gain) | Value label for open-loop and closed-loop gain | Quantify gain reduction |
| Phase response | Overlaid open-loop and closed-loop phase | Phase delay reduction via feedback |
| Gain-bandwidth product | Bar chart or numeric display: (open-loop GBW) = (closed-loop GBW) | Verify invariant |
| Step response time domain | Overlaid open-loop and closed-loop step responses | Transient speed improvement |
| Pole trajectory | Animated path as β sweeps 0→1; pole moves from origin to -α(1+K₀) | Geometric intuition |
| Sensitivity to parameter change | Heat map: perturbation in K₀ → change in loop gain | Feedback reduces sensitivity |

### Visualization Strategy

**Pedagogical arc:**
1. **Start with β=0**: Open-loop system has high DC gain K₀ but narrow bandwidth
2. **Increase β slowly**: Watch the closed-loop pole move left (more negative) in real-time
   - S-plane plot shows this migration
   - Magnitude plot shows DC gain shrinking (proportionally as 1/(1+βK₀))
   - Bandwidth expanding (proportionally as α(1+βK₀))
3. **Verify GBW invariant**: Dynamically compute and display the product; student observes it stays constant
4. **Compare transient responses**: Step response becomes faster but smaller in amplitude
5. **Stability insight**: Pole always remains on negative real axis (for this 1st-order system), so system cannot become unstable via positive feedback (highlight this safety)

**Interactive elements:**
- Slider β from 0 to 1 with smooth animation of all plots
- Dual slider controls: one for β (feedback), one for op-amp gain K₀
- Comparison mode: side-by-side open-loop vs. closed-loop Bode and step response
- Frequency sweep: play an input sinusoid whose frequency sweeps; watch amplitude response change in frequency-domain and see transient in time-domain simultaneously
- Highlight the 3dB point with vertical dashed line; show bandwidth = 3dB point frequency
- Numerical annotations: "DC Gain = X dB", "Bandwidth = Y Hz", "GBW = Z Hz"

### Implementation Notes

**Complexity:** Low-Medium

**Key Algorithms:**
- First-order system transfer function: $H(s) = \frac{K}{s + p}$ where p changes with β
- Magnitude at frequency ω: $|H(jω)| = \frac{K}{\sqrt{\omega^2 + p^2}}$
- 3dB bandwidth: solve $|H(j\omega_{3dB})|^2 = \frac{1}{2}|H(0)|^2$ → $\omega_{3dB} = p\sqrt{2|H(0)|^2 - 1} / |H(0)|$ (for low-pass)
- Simplified: for high-gain closed loop, $\omega_{3dB} \approx p = \alpha(1 + \beta K_0)$
- Step response: $s(t) = H(0)(1 - e^{-pt})$ for first-order system

**Dependencies:**
- NumPy for evaluations
- SciPy.signal.step for time-domain response
- Plotly for dual-axis (left: magnitude in dB, right: frequency in Hz on log scale)

### Extension Ideas

**Beginner:**
- "Predict the bandwidth": given K₀ and α, and choosing β, compute expected 3dB frequency and verify in simulation
- "Match the target": set a target closed-loop bandwidth, solve for required β
- Presets: op-amp models (LM741, NE5532) with realistic parameter values

**Advanced:**
- Introduce a second pole in open-loop system; observe that feedback can destabilize (phase margin concept)
- Stability criterion via Nyquist: plot open-loop Nyquist diagram; as β increases, show how Nyquist curve scales
- Sensor noise analysis: inject noise into feedback path; show how high loop gain attenuates noise at low frequencies

**Real-world:**
- Op-amp circuit design: design a transimpedance amplifier with specified gain and bandwidth
- Servo motor control: feedback around motor to improve speed regulation
- Power supply feedback: feedback error amplifier controlling output voltage

---

## Simulation: Crossover Distortion Correction via Feedback

### Lecture Source: Lecture 13-2, Pages 9-17

### Learning Objective
Visualize how nonlinear distortion (crossover distortion in push-pull transistor stages) can be reduced dramatically using negative feedback. Quantify the distortion reduction as a function of loop gain, and appreciate the practical power of feedback in compensating for component nonlinearity.

### Theoretical Foundation

Nonlinear characteristic (transistor pair with threshold VT):
$$V_o = \begin{cases}
0 & |V_i| < V_T \\
(V_i - V_T \text{ sgn}(V_i)) & |V_i| \geq V_T
\end{cases}$$

With feedback loop gain L = K:
$$V_o \approx \frac{K V_i}{1 + K} \approx V_i \quad \text{(for large K)}$$

Error signal in feedback: $E = V_i - \beta V_o$, where β is feedback fraction.
For high loop gain L = βK >> 1: error E is driven small, forcing $V_o \approx V_i/\beta$ despite nonlinearity.

Total harmonic distortion (THD):
$$\text{THD} = \frac{\sqrt{V_2^2 + V_3^2 + \ldots}}{V_1} \times 100\%$$

With feedback, THD scales roughly as: $\text{THD}_{\text{closed-loop}} \approx \frac{\text{THD}_{\text{open-loop}}}{1 + L}$

### System Architecture

**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|-----------|
| transistor_threshold | 0.2 to 1 V | V_T crossing voltage | Slider |
| loop_gain_K | 1 to 100 | Forward amplifier gain | Slider (logarithmic) |
| feedback_fraction | 0 to 1 | β in 1 + βK | Slider (linked to net loop gain) |
| input_amplitude | 1 to 50 V | Peak sinusoid amplitude | Slider |
| input_frequency | 10 Hz to 10 kHz | Frequency of test signal | Slider |
| supply_rails | ±5 to ±100 V | Power supply limits (symmetric) | Dropdown presets |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|----------------|---------|
| Input sinusoid | Clean sine wave | Reference signal |
| Nonlinear transfer characteristic | s-curve with dead-zone near zero (bent around ±V_T) | Show saturation/threshold nonlinearity |
| Open-loop output (no feedback) | Distorted waveform with flat region near zero crossings | Crossover distortion visible |
| Closed-loop output (with feedback, variable K) | Progressively less distorted as loop gain increases | Demonstrate distortion reduction |
| Output spectrum (FFT) | Bar chart: fundamental + harmonics (2nd, 3rd, 5th, etc.) | Quantify harmonic content |
| THD meter | Numeric display: open-loop THD vs. closed-loop THD | Show dramatic reduction factor |
| Loop gain indicator | Visual bar: L = βK | Tie to distortion reduction |
| Error signal | Difference V_i - V_o (or after feedback path) | Show how feedback minimizes error |

### Visualization Strategy

The core demonstration:
1. **Open-loop mode (K fixed, β=0)**:
   - Input is a sinusoid around the crossing point (amplitude comparable to V_T)
   - Output shows clear "flat spot" at zero crossings where transistor threshold prevents conduction
   - FFT shows strong 2nd and 3rd harmonics
   - Display THD_open_loop

2. **Gradually increase feedback β** (or equivalently, loop gain L = βK):
   - Output waveform smooths out in real-time
   - Flat spot shrinks; output approaches input sine shape
   - Harmonics in FFT shrink
   - THD_closed_loop meter shows 1/(1+L) scaling
   - At high β, waveforms are nearly identical (only high-frequency difference visible)

3. **Comparison view**:
   - Side-by-side output waveforms for several loop gain values (K=1, K=5, K=20, etc.)
   - THD comparison bar chart
   - Phasor diagram showing phase lag reduction as well

**Interactive affordances:**
- Animated waveform update as sliders move (smooth playback at 1-10x speed showing oscillations)
- Highlight the crossing region with vertical dashed lines at ±V_T on the transfer curve
- Toggle labels: show which trace is "ideal" vs. "with threshold" vs. "closed-loop"
- Cursor on waveform: hover to see instantaneous value and error in dB
- Real-world audio example: play synthesized distorted bass and apply feedback correction in real-time (low-res demonstration)

### Implementation Notes

**Complexity:** Medium

**Key Algorithms:**
- Nonlinear function evaluation: apply transistor characteristic to each sample
- Feedback loop iteration:
  ```python
  error = input - beta * output
  output = saturate(K * error, ±V_supply)
  ```
- FFT for harmonic analysis: numpy.fft.fft on output waveform
- THD calculation: $\sqrt{\sum_{n=2}^\infty |a_n|^2} / |a_1|$
- Time-domain filtering if applying feedback with dynamics (pole in feedback path)

**Dependencies:**
- NumPy for FFT and nonlinear arithmetic
- SciPy for optional filtering/distortion metrics
- Plotly for waveform rendering and spectrum bar chart

### Extension Ideas

**Beginner:**
- "Find the threshold": given a distorted waveform, estimate V_T
- Presets: audio power amplifier, DC power supply, speaker driver
- Listen to audio effect: synthesize tone with/without distortion and play back

**Advanced:**
- Frequency-dependent distortion: explore how feedback pole location affects high-frequency distortion
- Intermodulation distortion: input two sinusoids; observe cross-modulation products
- Stability under feedback: show how excessive feedback gain can cause oscillation if phase margin is poor

**Real-world:**
- Audio power amplifier design: minimize THD for high-fidelity sound
- Class-D amplifier: PWM modulation + feedback for digital audio
- High-voltage power supply: feedback control loop stabilizing output despite load variation

---

## Simulation: Harmonic Series Convergence and Gibbs Phenomenon

### Lecture Source: Lecture 14-3, Pages 22-40 (Fourier Series visualization)

### Learning Objective
Build visual intuition for how Fourier series converge by incrementally adding harmonics. Discover the Gibbs phenomenon (ringing near discontinuities) and understand why it arises from slow convergence (1/k decay) of square-wave harmonics vs. faster convergence (1/k² decay) of triangle-wave harmonics.

### Theoretical Foundation

Fourier series synthesis:
$$x(t) = \sum_{k=-\infty}^{\infty} a_k e^{j k \omega_0 t}$$

Square wave (discontinuous):
$$a_k = \begin{cases} \frac{1}{j\pi k} & \text{k odd} \\ 0 & \text{k even} \end{cases}$$
Magnitude decays as $1/|k|$ → slower convergence → Gibbs overshoot ≈ 9%

Triangle wave (continuous, discontinuous derivative):
$$a_k = \begin{cases} \frac{-1}{2k^2\pi^2} & \text{k odd} \\ 0 & \text{k even} \end{cases}$$
Magnitude decays as $1/k^2$ → faster convergence → no Gibbs overshoot

Gibbs phenomenon: Partial sums overshoot by ~9% at discontinuity, regardless of number of harmonics (overshoot doesn't vanish, but moves closer to discontinuity).

### System Architecture

**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|-----------|
| waveform_type | square, triangle, sawtooth, pulse | Periodic signal shape | Radio buttons |
| num_harmonics | 1, 3, 5, 7, ..., 99 | Number of terms in partial sum | Slider or stepper |
| duty_cycle | 0.1 to 0.9 | For pulse: fraction of period high | Slider (conditional on pulse) |
| frequency_fund | 1 to 100 Hz | Fundamental f₀ | Slider |
| animation_mode | on/off | Auto-increment harmonics | Toggle |
| animation_speed | 0.5x to 4x | Playback speed for harmonic progression | Slider |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|----------------|---------|
| Target waveform | Gray reference trace (ideal square/triangle/etc.) | Ground truth |
| Partial sum reconstruction | Colored trace; updated as harmonics change | Show progressive convergence |
| Harmonic spectrum | Bar chart or stem plot of |a_k| vs. k | Visualize decay rate |
| Reconstruction error | Absolute error between target and partial sum (shaded region) | Quantify goodness of fit |
| Ripple magnitude (Gibbs) | Peak overshoot at discontinuities (labeled) | Track Gibbs phenomenon |
| Convergence metric | E = ∫|error|² dt or max|error| vs. harmonic number | Graph showing convergence rate |
| Animating harmonics | Optional: show individual k-th harmonic as it's added | Decomposition insight |
| Phase alignment | Animated rotating phasors for leading harmonics | Vector addition intuition |

### Visualization Strategy

The progression toward discovery:
1. **Start with 1 fundamental harmonic**: Very rough approximation, immediately shows inadequacy
2. **Add harmonics incrementally** (with slider or auto-animation):
   - Watch corners of square wave sharpen
   - Watch ripples appear near discontinuity (Gibbs phenomenon)
   - For triangle wave, observe overshoot-free convergence
3. **Compare side-by-side**: Square wave (1/k decay, Gibbs) vs. triangle wave (1/k² decay, smooth)
4. **Spectrum view**: Show bar chart of |a_k| magnitude; square wave bars tall at all k (slow decay), triangle wave bars drop rapidly (fast decay)
5. **Gibbs quantification**:
   - Measure peak overshoot as % of discontinuity jump
   - Annotation: "Gibbs overshoot ≈ 9% (never vanishes!)"
   - Show overshoot moving closer to discontinuity as more harmonics added (but magnitude stays ~9%)

**Interactive affordances:**
- **Slider** to control num_harmonics: watch in real-time as harmonics accumulate
- **Animated play**: auto-increment harmonics with adjustable speed; pause at interesting points
- **Toggle target waveform visibility**: compare directly with ideal
- **Zoom into discontinuity**: magnify region near corner to observe Gibbs ringing detail
- **Spectral view tab**: switch between time-domain waveform and frequency-domain spectrum
- **Decay rate label**: annotate spectrum with "1/k" or "1/k²" trend line
- **Error integral display**: show cumulative L² energy in reconstruction error

### Implementation Notes

**Complexity:** Low-Medium

**Key Algorithms:**
- Fourier coefficient computation: analytic formulas for square, triangle, sawtooth
- Synthesis: $x(t) = \sum_{k=1}^{N} a_k \cos(k\omega_0 t + \phi_k)$
- FFT-based spectrum (or direct formula for standard waveforms)
- Error metric: $E = \int_0^T |x_{\text{target}}(t) - x_{\text{partial}}(t)|^2 dt$ (numerical integration or closed form)

**Dependencies:**
- NumPy for harmonic synthesis and error computation
- SciPy for optional Gibbs phenomenon analysis (windowing functions like Fejer, Lanczos for ringing reduction)
- Plotly for animated line plots and bar charts

### Extension Ideas

**Beginner:**
- "Predict the harmonic": given a waveform, which harmonic number best matches the visual curvature?
- Window function experiment: apply Fejer or Lanczos windowing to harmonics; observe how it reduces Gibbs ringing
- Presets: instrument waveforms (sawtooth from synthesizer, duty-cycle modulated pulse), musical notes

**Advanced:**
- Time-frequency analysis: show how harmonics contribute at different times (wavelet-like decomposition)
- Orthogonal decomposition in vector space: Fourier basis as orthonormal vectors; project waveform onto basis
- Apodization techniques: experiment with different window functions to control Gibbs phenomenon

**Real-world:**
- Musical timbre: explain why square-wave synthesizers sound hollow (missing even harmonics) vs. sawtooth (bright, all harmonics)
- Image compression: JPEG/PNG use similar harmonic/frequency decomposition (DCT); observe Gibbs ringing artifacts at sharp edges
- Antenna design: radiation pattern as Fourier sum; harmonics control side-lobe structure

---

## Simulation: Formant Tracking and Vowel Synthesis

### Lecture Source: Lecture 15-2, Pages 27-34

### Learning Objective
Understand how the human vocal tract acts as a filter, selecting resonant frequencies (formants) to sculpt a periodic buzz (from vocal cords) into distinct vowel sounds. Manipulate formant frequencies in real-time to morph vowels and gain intuition for speech signal processing.

### Theoretical Foundation

Source-filter model:
$$Y(s) = X(s) \cdot H(s)$$

where:
- X(s): periodic pulse train from vocal cords (harmonically rich, like sawtooth)
- H(s): vocal tract filter with resonances (formants)

Formants are peaks in the vocal tract transfer function:
$$H(s) = K \prod_{i=1}^{3} \frac{\omega_{F_i}^2}{s^2 + 2\zeta\omega_{F_i}s + \omega_{F_i}^2}$$

For vowel "ah": F₁ ≈ 700 Hz, F₂ ≈ 1220 Hz, F₃ ≈ 2600 Hz
For vowel "ee": F₁ ≈ 270 Hz, F₂ ≈ 2290 Hz, F₃ ≈ 3010 Hz

Each vowel has characteristic formant triplet. Formant bandwidth ≈ 50-150 Hz (controlled by damping ζ).

### System Architecture

**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|-----------|
| vowel_preset | ah, eh, ee, oh, oo, uh, neutral | Phonetic label or custom | Dropdown or buttons |
| formant_1_freq | 200 to 1200 Hz | F₁ center frequency | Slider or draggable on spectrum |
| formant_2_freq | 600 to 3000 Hz | F₂ center frequency | Slider or draggable on spectrum |
| formant_3_freq | 1500 to 4000 Hz | F₃ center frequency | Slider or draggable on spectrum |
| formant_bandwidth | 50 to 300 Hz | Q ≈ f/BW for each formant | Slider (global or per-formant) |
| glottis_frequency | 50 to 300 Hz | Pitch of vocal cord buzz | Slider |
| glottis_shape | pulse width / duty cycle | Brightness of buzz (more/fewer harmonics) | Slider |
| output_level | 0 to 1 | Volume (avoid clipping) | Slider |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|----------------|---------|
| Input spectrum (glottis buzz) | Sparse comb of harmonics (lines at multiples of pitch) | Show harmonic richness |
| Vocal tract filter response | Magnitude response with three peaking bumps (formants) | Show filter transfer function |
| Output spectrum (vowel) | Comb filtered by formant response; peaks enhanced/suppressed | Demonstrate filtering action |
| Waveform time-domain | Audio signal: glottis (hidden), output (audible) | Perceptual quality |
| Formant trajectory plot | 3D or 2D (F₁ vs F₂) with vowel trajectories and preset points | Vowel space geometry |
| Spectrogram (time-frequency) | Colormap showing energy at each frequency over ~1 sec | Formant stability and pitch |
| Real-time audio | Playback with low latency | Hear the vowel being synthesized |
| Vowel morphing path | Animated trajectory through vowel space (e.g., "ah" → "ee") | Observe smooth vowel transitions |

### Visualization Strategy

**Core experience:**
1. **Load a vowel preset** (e.g., "ah"):
   - Formant frequencies are set to realistic values
   - Vocal tract filter is displayed with three peaks
   - Audio plays back synthesized "ah" sound

2. **Drag a formant frequency** (interactive slider or point on spectrum):
   - In real-time, the vowel sound morphs
   - Filter response updates
   - Output spectrum updates to show how harmonics are now being amplified/attenuated differently
   - Audio feedback is immediate: student hears the vowel change

3. **Explore vowel space**:
   - 2D scatter plot: F₁ on y-axis (inverted: high F₁ = low pitch vowel), F₂ on x-axis
   - Presets marked (e.g., "ah", "ee", "oh")
   - Student's current formants highlighted
   - Drag the point; hear the sound morph; see the label change or request "identify this vowel"

4. **Morphing animation**:
   - Play a trajectory through vowel space: "ah" → "eh" → "ee"
   - Smooth animation of formant frequencies
   - Continuous audio playback (no clicks/pops)
   - Demonstrates how formants transition during natural speech

5. **Spectrogram view**:
   - Time on x-axis, frequency on y-axis, color = magnitude
   - Three horizontal stripes at F₁, F₂, F₃
   - As user adjusts formants, stripes move up/down in real-time
   - Pitch contour (fundamental frequency) visible as dashed line

**Aha moments:**
- "Moving F₁ changes vowel openness (low F₁ = closed vowels like 'ee', high F₁ = open vowels like 'ah')"
- "Moving F₂ changes front vs. back: high F₂ = front vowels ('ee', 'ae'), low F₂ = back vowels ('oh', 'oo')"
- "Same buzz with three different formant sets sounds completely different"
- "Formants are NOT harmonics; they're peaks in the filter, which happens to enhance certain harmonics"

### Implementation Notes

**Complexity:** Medium-High (real-time audio, spectrogram)

**Key Algorithms:**
- Glottis model: impulse train or pulse wave (sawtooth or controlled duty-cycle)
- Formant resonator: 2nd-order peaking filter
  ```python
  H_i(s) = (omega_i² / Q_i) / (s² + (omega_i / Q_i)s + omega_i²)
  ```
  Cascade three formant filters
- Time-domain filtering: scipy.signal.lfilter on audio samples
- Spectrogram: scipy.signal.spectrogram or Short-Time Fourier Transform (STFT)
- Real-time audio synthesis: generate audio at sample rate (44.1 or 48 kHz) and play via browser Web Audio API

**Dependencies:**
- NumPy for signal generation and filtering
- SciPy.signal for filter design and spectrogram
- Plotly for spectrum and formant trajectory visualization
- **tone.js** or Web Audio API for real-time audio playback (frontend)
- Backend must compute and stream audio buffer or precompute waveforms

### Extension Ideas

**Beginner:**
- "Guess the vowel": play a synthesized vowel and pick from preset list
- "Vowel matching": given formant frequencies, identify which vowel it corresponds to
- Presets from actual speech samples (extract formants via LPC analysis)

**Advanced:**
- Pitch accent: vary glottis frequency over time; observe pitch contour on spectrogram
- Coarticulation: model formant transitions between vowels (F₁ and F₂ don't change instantaneously)
- Speaker variation: scale formants by 10-20% to simulate male/female/child speakers

**Real-world:**
- Speech synthesis (TTS): formant-based synthesis method (still used in some systems for efficiency)
- Hearing aid tuning: adjust amplification peaks for specific frequency ranges (like formant frequencies)
- Accent transformation: shift formants to transform one accent to another (partially)
- Voice disorder diagnosis: clinicians measure formant frequencies to detect pathology

---

## Summary

These five simulations target key pedagogical moments from Lectures 11-15:

1. **Bode Plot Constructor** (Lecture 11): Demystifies the link between pole/zero locations and frequency response via interactive pole-zero dragging.

2. **High-Q Resonator** (Lecture 11): Visualizes Q factor's control over peak height and bandwidth, with pole trajectories in the s-plane.

3. **Feedback Gain-Bandwidth Tradeoff** (Lecture 12): Demonstrates the fundamental feedback principle via real-time Bode plot and step response comparisons.

4. **Crossover Distortion Correction** (Lecture 13): Quantifies nonlinear distortion reduction via feedback, with FFT and THD metrics.

5. **Harmonic Series Convergence** (Lecture 14): Builds intuition for Fourier synthesis and Gibbs phenomenon through incremental harmonic addition.

6. **Formant Tracking and Vowel Synthesis** (Lecture 15): Brings signals & systems to life through real-time speech synthesis, enabling visceral understanding of the source-filter model.

Each simulation emphasizes interactive discovery, visual-mathematical linking, and real-time feedback (audio or graphical) to create "aha moments" in student learning.
