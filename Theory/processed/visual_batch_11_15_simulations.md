# Simulation Ideas from MIT 6.003 Lectures 11-15
## Visual Analysis: DT Feedback, CT Feedback, and Fourier Series

### Context
Lectures 11-15 cover discrete-time feedback systems, continuous-time feedback control, and Fourier representations. Visual analysis of 28 contact sheet slides + raw transcripts identified key pedagogical structures and interactive opportunities.

---

## Simulation 1: High-Q Resonant System Explorer

### Lecture Source
**Lecture 11-2, Pages 8-10 (Sheets 8-11)**
"Frequency Response of a High-Q System"

### Visual Cues Observed
- Repeated s-plane plots showing pole pair migration as Q increases
- Pole pair location: `σ = -1/(2Q)` ± j√(1 - 1/(4Q²))
- Narrowing resonance peaks in frequency response magnitude plots (log scale)
- Phase response transitions becoming sharper with increasing Q
- Vector-based analysis showing angle relationships at resonance
- Bandwidth approximately equal to ω₀/Q (3dB bandwidth relationship)
- Phase change over 3dB bandwidth approximately π/2

### Learning Objective
Understand the relationship between pole location in the s-plane and frequency response characteristics. Develop intuition about quality factor (Q), resonance sharpness, peak magnitude scaling, and bandwidth.

### Theoretical Foundation
For a second-order system H(s) = 1 / (1 + (1/Q)(s/ω₀) + (s/ω₀)²):
- Poles at σ ± jω_d where σ = -ω₀/(2Q), ω_d = ω₀√(1 - 1/(4Q²))
- Peak response at resonance ≈ Q (for high Q)
- Bandwidth Δω ≈ ω₀/Q
- Phase varies over 3dB bandwidth by approximately π/2

### System Architecture

**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|------------|
| Q (Quality Factor) | 0.5 to 50 | Resonance sharpness; inverse relative bandwidth | Slider (log scale) |
| ω₀ (Natural Frequency) | 0.1 to 10 rad/s | Peak resonance location | Slider |
| Scale | 1-100 | Peak magnitude scaling | Slider |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|---|---------|
| Pole Locations | 2D s-plane plot with pole pair + dashed Q-contours | Show pole sensitivity to Q |
| Magnitude Response | Log-log Bode plot with peak highlighting | Illustrate sharpness and peak magnitude |
| Phase Response | Semi-log plot with phase gradient annotation | Show phase transition rate |
| 3dB Bandwidth Indicator | Horizontal span on magnitude plot (shaded region) | Quantify bandwidth = ω₀/Q |
| Vector Analysis Overlay | Optional: draw vectors from poles to frequency point | Explain magnitude via pole distances |

### Visualization Strategy
- **Main View**: Three synchronized plots (s-plane, magnitude Bode, phase Bode)
- **Interactive Synchronization**: Hover over s-plane pole → highlight corresponding frequency response region
- **Annotation Layer**: Automatically label peak magnitude, 3dB points, pole locations
- **Animation Option**: Sweep Q from low to high with real-time plot updates showing pole motion and response narrowing
- **Derived Metrics Panel**: Display Q, ω₀, peak magnitude estimate, 3dB bandwidth numerically

### Implementation Notes
**Complexity:** Medium

**Key Algorithms:**
- Pole calculation: σ = -ω₀/(2Q), ω_d = ω₀√(1 - 1/(4Q²))
- Frequency response: H(jω) via direct s-plane evaluation or second-order canonical form
- Vector magnitude: |H(jω)| = 1 / |1 + (jω/Q·ω₀) + (jω/ω₀)²|
- Bandwidth detection: Find frequencies where |H(jω)| = peak/√2 (3dB points)

**Backend Logic:**
```python
class HighQSystemSimulator(BaseSimulator):
    def _compute_response(self, Q, omega_0, scale):
        omega = np.logspace(-1, 2, 500)
        s = 1j * omega
        H = scale / (1 + (s / (Q * omega_0)) + (s / omega_0)**2)
        poles_real = -omega_0 / (2 * Q)
        poles_imag = omega_0 * np.sqrt(max(0, 1 - 1/(4*Q**2)))
        return {
            'magnitude': np.abs(H),
            'phase': np.angle(H),
            'omega': omega,
            'poles': [(poles_real, poles_imag), (poles_real, -poles_imag)]
        }
```

**Frontend Visualization:**
- s-plane: SVG background with grid, pole markers (circles/crosses), pole trajectory as Q varies
- Magnitude Bode: Plotly log-log with peak annotation and shaded 3dB bandwidth
- Phase Bode: Plotly semi-log with phase gradient color-coding
- Synchronization: useEffect hooks to share state across sub-components

### Extension Ideas
1. **Pole Zero Diagram Overlay**: Show poles + zeros (zeros at infinity with multiplicity)
2. **Group Delay Visualization**: Plot -dφ/dω to show frequency-dependent delay
3. **Step Response Animation**: Compute and animate time-domain step response as Q changes
4. **Comparison Tool**: Side-by-side Q values to compare response shapes
5. **Export Bode Diagram**: Download magnitude/phase plots in standard format
6. **Physical System Examples**: Link to RLC, mechanical resonance, acoustic cavities

---

## Simulation 2: Feedback Control System Parameter Sweep

### Lecture Source
**Lectures 12-13, Pages 3-7 (Sheets 1-6)**
"CT Feedback and Control: Dominant Pole Control, Motor Controller"

### Visual Cues Observed
- Block diagrams with feedback loops: X → +/- → Controller → Plant → Y
- Closed-loop pole location control via gain/controller design
- Multiple feedback topologies: proportional (P), integral (I), derivative (D), PI, PID
- Step response plots showing overshoot, settling time, steady-state error
- Pole migration diagrams as controller gain K varies
- Comparison of P, PI, PID responses with oscillations vs. smoothness trade-off
- Motor controller example: velocity feedback loop with integral action
- Closed-loop transfer function H_cl(s) = K·Plant / (1 + β·K·Plant)
- Root locus concept (implicit): as K increases, poles move through s-plane

### Learning Objective
Understand how feedback modifies system poles to achieve desired transient and steady-state characteristics. Develop intuition about trade-offs between speed (rise time), overshoot, and stability.

### Theoretical Foundation
For a feedback system with plant G_p(s) and controller C(s):
- Closed-loop TF: H_cl(s) = C(s)·G_p(s) / (1 + C(s)·G_p(s)·β)
- Pole locations determine stability (Re(poles) < 0) and dynamics (bandwidth, Q)
- Proportional gain K scales all poles uniformly (limited pole relocation)
- Integral term (∫ error dt) adds pole at origin, improves steady-state tracking
- Derivative term (d·error/dt) adds zero, can increase stability margin
- Motor model: dθ/dt = ω, dω/dt = (1/J)(τ - f·ω) where τ is torque command

### System Architecture

**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|------------|
| Controller Type | {P, PI, PD, PID} | Feedback law structure | Select/Radio buttons |
| K_p (Proportional Gain) | 0.1 to 10 | Amplification of error signal | Slider |
| K_i (Integral Gain) | 0 to 5 | Cumulative error compensation | Slider (hidden if not I term) |
| K_d (Derivative Gain) | 0 to 2 | Rate-of-change damping | Slider (hidden if not D term) |
| Plant Time Constant | 0.1 to 2 seconds | Motor inertia + friction effect | Slider |
| Reference Input | {step, ramp, sinusoid} | Desired trajectory | Select |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|---|---------|
| Closed-Loop Poles | s-plane plot; poles move as K_p, K_i, K_d vary | Show stability margin and dominant pole |
| Step Response | Time-domain plot with 0%, 2%, 10% settling band overlays | Visualize transient behavior |
| Error Signal | Time-domain error(t) = reference(t) - output(t) | Show steady-state error elimination via I term |
| Bode Plot (CL) | Magnitude + phase Bode of closed-loop TF | Compare bandwidth and phase margin |
| Control Effort | u(t) = output of controller | Show actuator saturation limits (optional) |
| Performance Metrics | Text panel: rise time, overshoot %, settling time, SSE | Quantify response quality |

### Visualization Strategy
- **Main Layout**: Two-column design
  - Left: Interactive block diagram with parameter sliders inline
  - Right: Four stacked time-domain plots (reference + output, error, poles in s-plane, control signal)
- **Real-Time Updates**: Debounce slider changes (150ms) and re-compute closed-loop poles + step response
- **Pole Motion Trail**: Show recent pole locations as K varies (faint history)
- **Stability Region**: Shade s-plane left half-plane as "stable" region
- **Overlaid Comparisons**: Option to freeze one controller config and compare against variations

### Implementation Notes
**Complexity:** Medium-High

**Key Algorithms:**
- Plant model: e.g., G_p(s) = 1/(τ·s + 1) for first-order, or 1/(s(τ·s + 1)) for integrator + lag
- Controller: C(s) = K_p + K_i/s + K_d·s
- Closed-loop poles: roots of 1 + C(s)·G_p(s)·β = 0
- Step response: Inverse Laplace of H_cl(s) / s
- Performance metrics: Extract from step response via scipy.signal.step or custom time-domain solver

**Backend Logic:**
```python
class FeedbackControlSimulator(BaseSimulator):
    def _compute_cl_response(self, K_p, K_i, K_d, plant_type, ref_type):
        # Plant TF
        if plant_type == 'first_order':
            num_p, den_p = [1], [self.tau, 1]
        elif plant_type == 'integrator_lag':
            num_p, den_p = [1], [self.tau, 1, 0]

        # Controller TF: K_p + K_i/s + K_d*s
        num_c = [K_d, K_p, K_i]
        den_c = [1, 0]  # denominator for I term

        # Closed-loop: using feedback formula
        cl_num, cl_den = feedback(num_p, den_p, num_c, den_c, sign=-1)

        # Poles
        poles = np.roots(cl_den)

        # Step response
        t, y = step((cl_num, cl_den), T=np.linspace(0, 10, 1000))

        return {'poles': poles, 't': t, 'y': y}
```

**Frontend Component:**
- Block diagram rendered as SVG or Plotly shapes
- Sliders trigger onChange → API call to `/api/simulations/{id}/update`
- Pole plot uses same s-plane style as High-Q simulator
- Time-domain plots use Plotly with multiple traces (reference, output, error)

### Extension Ideas
1. **Root Locus Tool**: Animate pole movement as single gain K varies, visualize locus curve
2. **Frequency Domain Analysis**: Add Nyquist plot, gain/phase margin indicators
3. **State-Space Representation**: Show A, B, C, D matrices and eigenvalue/eigenvector analysis
4. **Closed-Loop Bode Plots**: Magnitude + phase vs. frequency, highlight bandwidth
5. **Disturbance Rejection**: Add step disturbance input and show rejection capability
6. **Saturation Effects**: Introduce nonlinear actuator saturation and show limiting behavior
7. **Physical System Modeling**: Link to DC motor, robotic arm, aircraft altitude hold examples

---

## Simulation 3: Motor Controller Design Studio

### Lecture Source
**Lecture 12, Pages 5-7 (Sheets 5-7)**
"Motor Controller: Proportional, Integral, Derivative Control Synthesis"

### Visual Cues Observed
- Motor block diagram: reference θ_desired → error → controller → motor plant → θ_actual
- Multiple controller variants shown side-by-side: proportional-only, integral-only, PID
- Step response overlays comparing overshoot and settling time
- Pole maps showing closed-loop pole locations for each controller type
- First-order motor model: (1 + τs)^(-1) with τ ~ 100 ms
- Integral control moving poles closer to imaginary axis, reducing steady-state error
- Derivative control adding damping (moving poles left), reducing overshoot
- Goal: achieve fast response with minimal overshoot and zero steady-state error to ramps

### Learning Objective
Design PID controllers for a realistic motor system. Understand trade-offs: integral action trades stability margin for zero SSE; derivative adds robustness but amplifies noise.

### Theoretical Foundation
**Motor model**: θ̈ + (b/J)θ̇ + (K_t/(J·R))i = (K_t/(J·R))u
Simplified as: ω_m(s) = K_m / (1 + τ_m·s) where K_m is motor gain, τ_m is time constant.

**PID Controller**: C(s) = K_p + K_i/s + K_d·s
- K_p: Direct proportional response (stiffness)
- K_i: Integral of error (eliminates constant offsets, unstable if too large)
- K_d: Derivative of error (increases damping, sensitive to noise)

**Closed-loop response to step**: Combination of overshoot, rise time, settling time
- Overshoot related to damping ratio ζ of dominant poles
- Rise time inversely related to bandwidth
- Settling time inversely related to slowest pole magnitude

### System Architecture

**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|------------|
| K_p | 0 to 5 | Proportional gain (stiffness) | Slider |
| K_i | 0 to 3 | Integral gain (error accumulation) | Slider |
| K_d | 0 to 1 | Derivative gain (damping) | Slider |
| τ_motor (motor time constant) | 0.05 to 0.5 sec | Motor response speed | Slider |
| Reference Type | {step, ramp} | Desired input trajectory | Select |
| Disturbance | {none, step, constant torque} | Load disturbance | Select |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|---|---------|
| Motor Speed Response | Time plot: ω_ref, ω_actual vs. t | Show tracking accuracy and transients |
| Steady-State Error | Numeric indicator + zoomed tail region | SSE to step = 0, SSE to ramp = 0 with I term |
| Control Signal u(t) | Time plot: motor command voltage | Show magnitude and saturation limits |
| Step Response Metrics Panel | Table: Rise Time, Overshoot %, Settling Time, SSE | Quantify performance |
| Closed-Loop Poles | s-plane: pole locations color-coded by dominance | Show stability margins |
| PID Tuning Guidance | Visual indicator: "Aggressive" → "Conservative" based on K_p, K_i, K_d ratios | Intuitive feedback |

### Visualization Strategy
- **Central Plot Area**: Large time-domain comparison (reference vs. actual output)
- **Parameter Panel**: Three large sliders (K_p, K_i, K_d) with numeric input boxes
- **Pre-tuned Profiles**: Buttons for "Conservative," "Moderate," "Aggressive," "Custom"
- **Live Pole Display**: Small s-plane inset, poles update in real-time
- **Error & Effort Subplots**: Expandable accordion sections for detailed analysis
- **Responsive Labels**: Annotations on plots showing settling band, overshoot threshold, rise time window
- **Comparison Mode**: Save current tuning, load reference, show both step responses

### Implementation Notes
**Complexity:** Medium

**Key Algorithms:**
- Motor plant: G_p(s) = K_m / (1 + τ_m·s) or second-order for more realism
- PID controller in s-domain: C(s) = K_p + K_i/s + K_d·s
- Closed-loop transfer function via feedback()
- Step response via scipy.signal.step() or custom ODE solver
- Performance metrics extraction: find overshoot %, rise time (10%-90%), settling time (2% band)

**Backend Code Sketch:**
```python
class MotorControllerSimulator(BaseSimulator):
    def _compute_response(self, K_p, K_i, K_d, tau_motor, ref_type):
        # Motor plant: G_m(s) = 1 / (1 + tau_motor*s)
        num_m = [1]
        den_m = [tau_motor, 1]

        # PID controller: C(s) = K_p + K_i/s + K_d*s
        # Convert to proper rational form: (K_d*s^2 + K_p*s + K_i) / s
        num_c = [K_d, K_p, K_i]
        den_c = [1, 0]

        # Closed-loop: H_cl = C * G_m / (1 + C * G_m)
        num_ol, den_ol = signal.polymul(num_c, num_m)
        num_ol = signal.polymul(num_ol, [1])
        den_ol_plus_num = np.polyadd(den_ol, num_ol)

        # Poles
        poles = np.roots(den_ol_plus_num)

        # Step response
        t = np.linspace(0, 5, 1000)
        t_out, y_out = signal.step((num_ol, den_ol_plus_num), T=t)

        return {'poles': poles, 't': t_out, 'y': y_out}
```

### Extension Ideas
1. **Ziegler-Nichols Tuning**: Auto-compute K_p, K_i, K_d based on plant parameters
2. **Bode Plot Display**: Show frequency response of controller and closed-loop system
3. **Sensitivity Analysis**: Show how SSE and overshoot vary with plant parameter uncertainty
4. **Disturbance Rejection**: Add load disturbance and show transient response
5. **Anti-Windup Logic**: Implement integral windup prevention and show effect
6. **State-Space Design**: Transition to pole placement via A, B, C, D matrices
7. **Noise Filtering**: Add measurement noise, show D term amplification problem + low-pass filter solution

---

## Simulation 4: Fourier Series Harmonic Builder

### Lecture Source
**Lectures 14-15, Pages 1-9 (Sheets 1-9)**
"Fourier Representations, Harmonic Components, Orthogonal Decompositions"

### Visual Cues Observed
- Spectrum plots showing harmonic content of instruments: piano, violin, bassoon, oboe, etc.
- Multiple harmonics at ω₀, 2ω₀, 3ω₀, ... with amplitude coefficients a_k
- Synthesis animation: adding successive harmonics to reconstruct original signal
- Square wave, triangle wave, sawtooth waveforms with their harmonic series
- Convergence of partial sums as number of harmonics increases
- "Piano k" (plucked) vs. "Piano t" (sustained) showing different harmonic decay patterns
- Harmonic interference: octave (matching harmonics), fifth (nearby harmonics), unison
- Time-domain signal overlaid with frequency-domain (harmonic) representation
- Concept: periodic signal = DC + fundamental + harmonics, orthogonal basis

### Learning Objective
Develop intuition about frequency content. Understand how periodic signals decompose into harmonics. Visualize Parseval's theorem (energy in time = energy in frequency). Learn about harmonic relationships in music.

### Theoretical Foundation
**Fourier Series (real form):**
x(t) = a₀ + Σ[a_k·cos(kω₀t) + b_k·sin(kω₀t)]

**Complex exponential form:**
x(t) = Σ a_k·e^(jkω₀t) where a_k = (1/T) ∫₀^T x(t)·e^(-jkω₀t) dt

**Key Properties:**
- DC component a₀ is average value
- Harmonic k has frequency k·ω₀ and amplitude |a_k|
- Phase of each harmonic ∠a_k determines time waveform shape
- Real signals have conjugate symmetry: a_{-k} = a_k*
- Parseval: ∫|x(t)|² dt = Σ|a_k|²
- Convergence: more harmonics → better approximation of discontinuities

### System Architecture

**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|------------|
| Waveform Type | {square, triangle, sawtooth, custom} | Periodic signal to decompose | Select dropdown |
| Fundamental Frequency f₀ | 1 to 1000 Hz | ω₀ = 2πf₀ | Slider or number input |
| Number of Harmonics N | 1 to 50 | Truncation of Fourier series | Slider |
| Amplitude a₀ | 0 to 1 | DC component | Slider |
| Phase Shift φ | 0 to 2π | Global phase rotation | Slider (optional) |
| Display Mode | {magnitude, phase, real, imaginary} | Harmonic representation | Select buttons |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|---|---------|
| Time-Domain Signal | Line plot: reconstructed x(t) | Show waveform shape after N harmonics |
| Harmonic Spectrum | Stem plot: |a_k| vs. frequency kf₀ | Show which frequencies are present |
| Phase Spectrum | Stem plot: ∠a_k vs. frequency kf₀ | Show phase relationships (optional) |
| Harmonic Addition Animation | Cumulative waveform overlay as k=1,2,...,N | Build intuition about convergence |
| Error / Residual | Plot or RMS value: x_true(t) - x_approx(t) | Quantify approximation error |
| Energy Distribution | Bar chart or pie chart: fractional energy per harmonic | Show dominant frequencies |
| Waveform Comparison | Overlay: true signal vs. N-harmonic reconstruction | Visual convergence rate |

### Visualization Strategy
- **Two-Column Layout:**
  - **Left Panel**: Frequency-domain stem plot of harmonics (magnitude + phase toggle)
  - **Right Panel**: Time-domain signal reconstruction with slider to add harmonics one-by-one
- **Interactive Harmonic Selection**: Click on a stem to highlight that harmonic component in time domain
- **Animation Controls**: Play/pause button to step through harmonics k=1→N with dynamic waveform update
- **Stacked View Option**: Show decomposition into sine + cosine components
- **Audio Playback (Optional)**: Synthesize and play the reconstructed signal at chosen frequency
- **Harmonic Table**: List a_k, b_k, magnitude, phase for each k (scrollable)

### Implementation Notes
**Complexity:** Medium

**Key Algorithms:**
- **Square Wave**: a_k = (4/π) / k for odd k, 0 for even k (except k=0)
- **Triangle Wave**: a_k = (8/π²) / k² for odd k, scaled
- **Sawtooth Wave**: a_k = -2/(πk) for all k ≠ 0
- **Arbitrary Custom Waveform**: Use FFT (numpy.fft.fft) or numerical integration (scipy.integrate.quad)
- **Partial Sum Reconstruction**: x_N(t) = Σ_{k=-N}^{N} a_k·e^(jkω₀t) evaluated on time grid
- **RMS Error**: sqrt(mean((x_exact - x_approx)²))

**Backend Code:**
```python
class FourierSeriesSimulator(BaseSimulator):
    def _compute_harmonics(self, waveform_type, f0, num_harmonics, amplitude_dc):
        frequencies = np.arange(-num_harmonics, num_harmonics + 1) * f0

        if waveform_type == 'square':
            # Square wave: a_k = (4/pi) / k for odd k
            a_k = np.zeros(2*num_harmonics + 1)
            for i, k in enumerate(frequencies):
                if k == 0:
                    a_k[i] = amplitude_dc
                elif k % 2 != 0:  # odd harmonic
                    a_k[i] = (4/np.pi) / np.abs(k)
        elif waveform_type == 'triangle':
            # Triangle: a_k = (8/pi^2) / k^2 for odd k
            a_k = np.zeros(2*num_harmonics + 1)
            for i, k in enumerate(frequencies):
                if k == 0:
                    a_k[i] = amplitude_dc
                elif k % 2 != 0:
                    a_k[i] = (8 / np.pi**2) / (k**2)

        # Reconstruct in time domain
        t = np.linspace(0, 1/f0, 1000)  # One period
        x_t = np.zeros_like(t)
        for k, amp in zip(frequencies, a_k):
            x_t += np.real(amp * np.exp(2j * np.pi * k * f0 * t))

        return {
            'frequencies': frequencies,
            'amplitudes': np.abs(a_k),
            'phases': np.angle(a_k),
            'time': t,
            'signal': x_t
        }
```

**Frontend:**
- Stem plot for spectrum (Plotly bar chart or custom SVG)
- Time-domain plot with Plotly line
- Slider for N with onChange → re-compute and update both plots
- Animation loop for cumulative harmonic addition

### Extension Ideas
1. **Harmonic Timbre Explorer**: Load real instrument samples, compute and display their harmonic content
2. **Fourier Transform (DT)**: Extend to discrete-time Fourier transform and FFT
3. **Gibbs Phenomenon**: Highlight overshoot at discontinuities as N increases (square wave edges)
4. **Window Functions**: Apply Hann, Hamming, etc. windows and show spectral leakage reduction
5. **Phase & Magnitude Relationships**: Show how phase shift affects time waveform without changing spectrum magnitude
6. **Music Intervals**: Display harmonic relationships for common musical intervals (octave, fifth, major third)
7. **Synthetic Sound Design**: Allow user to design harmonic content, hear the result
8. **Convergence Metrics**: Display L² error vs. N, rate of decay of harmonic amplitudes

---

## Simulation 5: Discrete-Time Feedback Pole Response

### Lecture Source
**Lectures 11, Pages 1-7 (Sheets 1-7)**
"DT Frequency Response and Bode Plots, Asymptotic Behavior, Pole/Zero Analysis"

### Visual Cues Observed
- Pole/zero plots in z-plane with frequency response derivations
- Isolated poles and zeros at positions z_p, z_z with frequency response curves
- Log-log (Bode-like) magnitude plots for DT systems
- Phase vs. log frequency showing asymptotic behavior
- Check-yourself questions comparing systems with different pole/zero placements
- Concept: magnitude of DT frequency response determined by distances from z_p, z_z to point e^(jω) on unit circle
- Unit circle as locus of ω ∈ [0, π] for DT systems
- Asymptotic approximations for magnitude at low/high frequencies

### Learning Objective
Understand DT system frequency response via pole-zero geometry. Develop intuition about how pole/zero locations affect magnitude and phase responses in DT domain.

### Theoretical Foundation
**DT Frequency Response**: H(e^(jω)) = product of (e^(jω) - z_k) / product of (e^(jω) - p_k)

**Magnitude**: |H(e^(jω))| = ∏|e^(jω) - z_k| / ∏|e^(jω) - p_k| = product of distances from zeros to point on unit circle / product of distances from poles

**Phase**: ∠H(e^(jω)) = Σ∠(e^(jω) - z_k) - Σ∠(e^(jω) - p_k) = sum of angles to zeros minus sum of angles to poles

**Asymptotic Behavior**:
- At ω = 0: H(e^(j·0)) = H(1) = product of (1 - z_k) / product of (1 - p_k)
- At ω = π: H(e^(j·π)) = H(-1) = product of (-1 - z_k) / product of (-1 - p_k)

### System Architecture

**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|------------|
| Pole Location (real part) | -0.9 to 0.9 | z_p,real ∈ (-1, 1) for stability | Slider |
| Pole Location (imag part) | -0.9 to 0.9 | z_p,imag for complex pole pair | Slider |
| Zero Location (real part) | -0.9 to 0.9 | z_z,real | Slider |
| Zero Location (imag part) | -0.9 to 0.9 | z_z,imag | Slider |
| Gain K | 0.1 to 10 | Scale factor for magnitude | Slider |
| Display Type | {magnitude, phase, both} | Frequency response type | Select |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|---|---------|
| Pole-Zero Diagram | Complex plane: unit circle outline, pole ×, zero ○ | Show system structure |
| Magnitude Response | Semi-log or log-log plot: \|H(e^(jω))\| vs. ω | Show frequency selectivity |
| Phase Response | Linear vs. log-log: ∠H(e^(jω)) vs. ω | Show phase progression |
| Vector Geometry Overlay | Arrows from poles/zeros to point on unit circle (at selected ω) | Illustrate distance/angle calculations |
| Frequency Sweep Animation | Point moves around unit circle, frequency response traces out in real-time | Build intuition |
| Magnitude at Key Points | Text: \|H(e^(j·0))\|, \|H(e^(j·π))\|, \|H(e^(j·π/2))\| | Quantify response values |

### Visualization Strategy
- **Main Plotting Area**: Left side = pole-zero diagram (complex plane), right side = magnitude + phase (frequency)
- **Interactive Unit Circle**: Hover over unit circle point → show corresponding ω, display vectors to poles/zeros, highlight magnitude/phase values
- **Vector Visualization**: Draw lines from poles and zeros to current frequency point, show magnitudes and angles
- **Synchronized Animation**: Play button to sweep ω from 0 to π, animating frequency response trace
- **Slider-Driven Updates**: Change pole/zero positions → immediate re-computation and plot updates
- **Constraint Indicators**: Pole position highlighted in red if outside unit circle (unstable)

### Implementation Notes
**Complexity:** Medium

**Key Algorithms:**
- Pole/zero to frequency response: Direct evaluation of H(e^(jω)) = K·∏(e^(jω) - z_k) / ∏(e^(jω) - p_k)
- Distance and angle calculations: |e^(jω) - p| = √((cos(ω) - p_real)² + (sin(ω) - p_imag)²)
- Magnitude: |H(e^(jω))| = K·∏|e^(jω) - z_k| / ∏|e^(jω) - p_k|
- Phase: ∠H(e^(jω)) = ∠K + Σ∠(e^(jω) - z_k) - Σ∠(e^(jω) - p_k)
- Unwrap phase to avoid discontinuities: numpy.unwrap()

**Backend:**
```python
class DTFeedbackPoleSimulator(BaseSimulator):
    def _compute_response(self, pole_real, pole_imag, zero_real, zero_imag, gain):
        pole = pole_real + 1j * pole_imag
        zero = zero_real + 1j * zero_imag

        omega = np.linspace(0, np.pi, 500)
        H = []

        for w in omega:
            z_point = np.exp(1j * w)  # Point on unit circle
            num = gain * np.abs(z_point - zero)
            den = np.abs(z_point - pole)
            if den == 0:
                magnitude = np.inf
            else:
                magnitude = num / den
            H.append(magnitude)

        H = np.array(H)
        phase = np.angle(gain * (np.exp(1j * omega) - zero) / (np.exp(1j * omega) - pole))
        phase = np.unwrap(phase)

        return {
            'omega': omega,
            'magnitude': np.abs(H),
            'phase': phase,
            'pole': pole,
            'zero': zero
        }
```

**Frontend:**
- z-plane rendered as SVG or Plotly scatter (unit circle as background, poles/zeros as draggable points)
- Magnitude/phase plots with Plotly line traces
- Vector overlay as SVG lines drawn on top of z-plane
- Slider controls for pole/zero positions

### Extension Ideas
1. **Second-Order Sections**: Build cascade of first-order sections, observe overall response
2. **Pole Pair (Complex Conjugate)**: Special case with real-valued coefficients
3. **Root Locus for DT**: Show pole movement as a feedback gain varies
4. **Notch & Peak Filters**: Place poles and zeros to create notches or resonances
5. **Stability Criterion**: Automatic red highlighting if any pole |z_p| > 1
6. **Phase Unwrapping Visualization**: Show discontinuities and unwrapped phase
7. **Group Delay**: Plot -dφ/dω to show frequency-dependent delay in DT systems

---

## Summary: Pedagogical Value and Implementation Priority

### High-Priority (Core Concept Coverage)
1. **Fourier Series Harmonic Builder** - Fundamental tool for understanding frequency content; direct support for Lectures 14-15
2. **High-Q Resonant System Explorer** - Critical for pole-placement intuition; bridges Bode plots and s-plane geometry
3. **Feedback Control System Parameter Sweep** - Unifies PID controller design with closed-loop pole location

### Medium-Priority (Enrichment & Practical Skills)
4. **Motor Controller Design Studio** - Realistic application of feedback control; motivating example
5. **Discrete-Time Feedback Pole Response** - Completes DT system understanding from Lecture 11

### Implementation Recommendations
- **Phase 1**: Develop Fourier Series and High-Q simulators (medium complexity, high educational impact)
- **Phase 2**: Feedback Control and Motor Controller (integrate into Control Systems category)
- **Phase 3**: DT Feedback Pole Response (DT domain visualization)

### Integration with Existing Simulations
- **Fourier Series**: Complements `fourier_series` (which is complex exponential based) by adding synthesis and harmonic buildup animation
- **High-Q System**: Natural follow-up to `second_order_system` and `resonance_anatomy` with interactive Q variation
- **Feedback Control**: Extends `feedback_system_analysis` with real-time PID tuning interface
- **Motor Controller**: Physical system example pairing with `dc_motor` and `perching_glider`
- **DT Feedback**: Parallel to `dt_system_representations` with explicit pole-zero geometry

---

## Visual Elements Present in Source Material

### Recurring Diagrams
1. **s-plane and z-plane plots** with pole/zero markers
2. **Bode plots** (magnitude and phase vs. frequency on log scales)
3. **Block diagrams** with feedback loops, controller, plant, sensor blocks
4. **Time-domain waveforms** (step, ramp, sinusoidal, exponential responses)
5. **Harmonic spectrum plots** (stem/bar charts of coefficients)
6. **Transient response comparisons** (overshoot, settling time overlays)
7. **Vector diagrams** showing pole/zero distances and phase angles
8. **Frequency-domain vector analysis** for Bode plot construction

### Key Mathematical Structures
- Second-order system transfer functions and characteristic equations
- Pole location relationships with Q, natural frequency, damping
- PID controller synthesis and gain tuning
- Fourier series decomposition (real and complex exponential forms)
- Frequency response via s-plane evaluation
- Feedback loop equations: H_cl = H_open / (1 + H_open·β)

### Physical Systems Illustrated
- RC lowpass filters
- Op-amp circuits (with frequency-dependent gain)
- DC motor with velocity/position control
- Magnetic levitation (stabilizing unstable pole)
- Inverted pendulum (classic unstable system)
- Harmonic content of musical instruments (piano, violin, oboe, etc.)

All 5 proposed simulations derive directly from these visual and conceptual elements present in the MIT 6.003 lecture materials.
