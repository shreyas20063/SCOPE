# Simulation Ideas from Lectures 16-20
## MIT 6.003 Signals and Systems (Fourier Analysis & Applications)

---

## Simulation 1: Periodic Extension to Transform Converter
### Lecture Source: Lecture 16 (Fourier Transform), Pages 3-39; Lecture 19-2 (Relations), Pages 10-24
### Learning Objective
Develop intuition for **how finite signals evolve into infinite spectral representations** by observing the continuous transformation from an aperiodic signal to periodic extension, watching the Fourier transform transition from continuous to discrete (impulse train).

### Theoretical Foundation
As period T → ∞, a periodic signal with Fourier series coefficients {ak} converges to an aperiodic signal with continuous Fourier transform X(jω). The discrete frequency samples 2πak become impulse trains:

$$X(jω) = \lim_{T→∞} T a_k = \lim_{T→∞} \frac{1}{T} \int_{-T/2}^{T/2} x(t)e^{-jωt} dt$$

Periodic extension: $z(t) = \sum_{k=-∞}^{∞} x(t + kT)$ results in discrete frequency representation via impulse train convolution in frequency domain.

**Key equations:**
- Fourier series: $x(t) = \sum_{k=-∞}^{∞} a_k e^{j2πkt/T}$
- Fourier transform: $X(jω) = \int_{-∞}^{∞} x(t)e^{-jωt} dt$
- Impulse train: $p(t) = \sum_{k=-∞}^{∞} δ(t - kT)$ ↔ $P(jω) = \frac{2π}{T}\sum_{k=-∞}^{∞} δ(ω - k\frac{2π}{T})$

### System Architecture
**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|-----------|
| Base Signal | {pulse, triangular, sinc, gaussian} | Aperiodic signal to extend | Select dropdown |
| Signal Duration | 0.5 - 4 periods | T_sig parameter | Slider (log scale) |
| Extension Period | 1.0 - 20 | T_period (ratio) | Slider |
| Visualization Mode | {time, frequency, both} | Which domain(s) to show | Tab selector |
| Animation Speed | 0.5 - 2.0x | Time scaling factor | Slider |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|----------------|---------|
| Time-domain signal | Oscillating waveform with repeated copies | Show periodic extension filling time axis |
| Fourier series coefficients | Discrete vertical bars at ω = k(2π/T) | Visualize sampling of continuous transform |
| Continuous Fourier transform | Smooth curve overlay on discretized version | Show convergence as T increases |
| Frequency domain transition | Animated transform: impulses moving closer together | Demonstrate how impulses fill in as T → ∞ |
| Spectral density | Color-coded heatmap of magnitude evolution | Show continuous limit |

### Visualization Strategy

**Multi-panel responsive layout:**
1. **Time-Domain Panel (left):**
   - Background shows original aperiodic signal in light gray
   - Highlighted periodic repetitions in bold color
   - Animation reveals copies appearing as T_period slider increases
   - Vertical dashed lines mark period boundaries

2. **Frequency-Domain Panel (right):**
   - Blue impulse train for current period T
   - Overlaid continuous Fourier transform X(jω) in faint orange
   - As T increases, impulses move closer; continuous curve becomes visible underneath
   - X-axis shows frequency normalized to fundamental spacing
   - Zoom control to explore dense spectrum

3. **Interactive Discovery:**
   - Play button animates T increasing continuously (creates "aha moment" when discrete becomes continuous)
   - User can pause and compare Fourier series coefficients to X(jω) samples
   - Toggle overlay to isolate impulse train or continuous function
   - Crosshair tool: click frequency to show corresponding time-domain harmonic contribution

**Real-world connection:** Relate to why analog signals need sampling (periodic extension in frequency), why CDs/digital audio work (aliasing from periodicity).

### Implementation Notes
**Complexity:** Medium
- Requires FFT for continuous curve approximation
- Animation smoothness critical for pedagogy
- Need specialized colormaps for dual-representation clarity

**Key Algorithms:**
- FFT computation of base signal
- Periodic extension: convolve base signal with impulse train (frequency domain)
- Smooth interpolation of impulse train as T varies
- Real-time parameter updates with debouncing

**Dependencies:**
- NumPy (FFT, convolution)
- SciPy (signal processing utilities)
- Plotly (dual-panel synchronized plots)
- Custom animation module for smooth T scaling

### Extension Ideas
**Beginner:**
- Explore preset signals (square wave, sawtooth) and observe different spectral characteristics
- Measure spacing between impulses; verify inverse relationship with period

**Advanced:**
- Design custom signals and predict spectrum shape before animating
- Quantify error: ||continuous_transform - impulse_sum|| as function of T
- Investigate windowing effects (Gibbs phenomenon near discontinuities)

**Real-world:**
- Connect to music: perceive "aliasing artifacts" when T too small (beats, intermodulation)
- Design anti-aliasing filters: predict required frequency content from period choice
- Analyze actual ECG or audio data: find minimum T to preserve fidelity

---

## Simulation 2: DT Frequency Response on the Unit Circle
### Lecture Source: Lecture 17 (DT Frequency Representations), Pages 17-28; Lecture 18-2
### Learning Objective
Build geometric intuition for **why DT frequency response is evaluated on the unit circle** (not the entire s-plane like CT), and visualize how poles/zeros interact with the unit circle to shape magnitude and phase response.

### Theoretical Foundation
For DT systems, poles and zeros in the z-plane determine frequency response by evaluating H(z) on the unit circle z = e^{jΩ}:

$$H(e^{jΩ}) = K \frac{\prod_i (e^{jΩ} - q_i)}{\prod_j (e^{jΩ} - p_j)}$$

Magnitude: $|H(e^{jΩ})| = |K| \frac{\prod_i |e^{jΩ} - q_i|}{\prod_j |e^{jΩ} - p_j|}$ (product of vector magnitudes)
Phase: $∠H(e^{jΩ}) = ∠K + \sum_i ∠(e^{jΩ} - q_i) - \sum_j ∠(e^{jΩ} - p_j)$ (sum of angles)

Unlike CT, DT frequency response is **periodic in Ω with period 2π** because $e^{j(Ω+2π)} = e^{jΩ}$.

### System Architecture
**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|-----------|
| Zero Location(s) | Unit circle interior | q_i placement | Draggable points |
| Pole Location(s) | Unit circle interior | p_j placement | Draggable points |
| DC Gain | 0.1 - 10 | Scaling constant K | Slider (log) |
| Num Zeros | 1 - 4 | Multiplicity control | Spinner |
| Num Poles | 1 - 4 | System order | Spinner |
| Show Vectors | true/false | Display construction lines | Toggle |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|----------------|---------|
| z-plane diagram | Unit circle with poles/zeros, construction vectors | See pole-zero geometry |
| Magnitude response | Plot of $\|H(e^{jΩ})\|$ vs Ω | Understand filtering behavior |
| Phase response | Plot of $∠H(e^{jΩ})$ vs Ω | Show phase shift across frequencies |
| Vector traces | Animated vectors from each pole/zero to cursor | Build intuition for magnitude/phase calculation |
| Frequency response overlay | Magnitude and phase on same panel as z-plane | Connect geometric to spectral view |

### Visualization Strategy

**Three-panel synchronized display:**
1. **Z-Plane Panel (top-left):**
   - Unit circle as reference (thick black circle)
   - Red X markers for poles (⊗ symbol)
   - Blue O markers for zeros (○ symbol)
   - Draggable: click and drag poles/zeros interactively
   - When hovering over unit circle, show corresponding frequency Ω annotation
   - Construction lines: vectors from poles/zeros to cursor position on circle

2. **Magnitude Response (bottom-left):**
   - Y-axis: |H(e^jΩ)| in dB
   - X-axis: Ω from 0 to 2π
   - Vertical dashed line shows current frequency (synced to cursor on unit circle)
   - Color-coded regions: green (passband), yellow (transition), red (stopband)
   - Peak/notch indicators (circles at extrema)

3. **Phase Response (bottom-right):**
   - Y-axis: ∠H(e^jΩ) in radians (-π to π)
   - X-axis: Ω from 0 to 2π
   - Phase wrapping visualization (continuous unwrapped option)
   - Group delay annotation for linear phase systems

**Interactive "Vector Sum" Mode:**
- Cursor moves around unit circle
- Vectors from each pole/zero to cursor update in real-time
- Text overlay shows: magnitude calculation = (product of zero vectors) / (product of pole vectors)
- Phase calculation = sum of angles with interactive color coding

**Aha moments:**
- Dragging pole near unit circle → dramatic magnitude peak at that frequency
- Placing zero on unit circle → notch (zero magnitude) at that frequency
- Pole inside vs outside circle → unstable (divergent) vs stable systems
- Periodicity: H(e^jΩ) repeats every 2π; show reflected pattern in [π, 2π]

### Implementation Notes
**Complexity:** Medium-High
- Requires real-time vector diagram updates
- Complex number arithmetic for magnitude/phase computation
- Synchronized multi-panel rendering

**Key Algorithms:**
- Vector magnitude and angle calculation
- Efficient frequency response sampling (FFT-based or direct)
- Drag-and-drop constraint to unit circle interior (for poles)
- Magnitude/phase calculation via vectorized NumPy operations

**Dependencies:**
- NumPy (complex arithmetic)
- Plotly (synchronized plots with custom event handlers)
- JavaScript (drag interaction layer)

### Extension Ideas
**Beginner:**
- Design simple filters (low-pass, high-pass, notch)
- Observe Bode plot shape changes with pole/zero movement
- Relate to circuit design (RC filters, delay networks)

**Advanced:**
- Design IIR filters with specified magnitude response (interactive pole-zero placement)
- Investigate stability: how far inside unit circle must poles be?
- Minimum phase systems: zeros inside vs outside unit circle

**Real-world:**
- Audio equalization: design graphic EQ by placing poles/zeros
- Control system design: loop shaping in z-domain
- Digital filter synthesis from magnitude specifications

---

## Simulation 3: Fourier Series Coefficients to Spectral Window
### Lecture Source: Lecture 19-2 (Relations), Pages 5-24; Lecture 20 (Applications), Pages 35-39
### Learning Objective
Visualize **how finite-length signals create spectral windows and sidelobes** in Fourier analysis. Develop intuition for spectral leakage, windowing trade-offs, and why rectangular windows have poor side-lobe behavior while Hamming/Blackman windows offer better frequency resolution.

### Theoretical Foundation
A finite-duration signal x[n] of length N is equivalent to an infinite signal multiplied by a rectangular window:
$$x[n] = x_{full}[n] \cdot w_{rect}[n]$$

In frequency domain, multiplication becomes convolution:
$$X(e^{jΩ}) = X_{full}(e^{jΩ}) * W_{rect}(e^{jΩ})$$

The rectangular window has poor frequency characteristics (narrow main lobe, high side-lobes). Windowing theory provides alternatives (Hamming, Blackman, Hann) trading main-lobe width for side-lobe suppression.

Main-lobe width: $Δω ≈ \frac{4π}{N}$ (rectangular)
Side-lobe level: -13 dB (rectangular), -43 dB (Hamming), -58 dB (Blackman)

### System Architecture
**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|-----------|
| Base Signal | {sinusoid, multi-tone, chirp, AM} | Signal to window | Select dropdown |
| Signal Length N | 32 - 256 | Number of samples | Slider |
| Window Type | {rect, hamming, blackman, hann, bartlett} | Windowing function | Select dropdown |
| Frequency (for sinusoid) | 0.1 - 0.45 | Normalized frequency | Slider |
| Display Mode | {magnitude, log magnitude, phase} | Frequency scale | Radio buttons |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|----------------|---------|
| Time-domain signal | Waveform with window envelope overlay | Show time-domain windowing effect |
| Window function | Plot of w[n] | Inspect window shape |
| DFT of signal | Magnitude spectrum in linear scale | See actual spectral leakage |
| Windowed spectrum | Log-magnitude spectrum with dB scale | Identify main lobe and side lobes |
| Window spectrum | Frequency response of window itself | Explain leakage mechanism |
| Spectral comparison | Multiple windows overlaid | Compare trade-offs |

### Visualization Strategy

**Four-panel grid layout:**
1. **Time Domain (top-left):**
   - Blue plot: x[n] (signal being windowed)
   - Red envelope: w[n] (window function)
   - Highlights spectral leakage: how rectangular window truncates signal abruptly
   - Vertical grid lines show sample indices

2. **Window Function (top-right):**
   - Dedicated plot showing w[n] in time domain
   - Log-magnitude plot of W(e^jΩ) on same panel (dB scale)
   - Annotations: main-lobe width (-3dB bandwidth), side-lobe level
   - Table comparing different windows (width, side-lobe)

3. **Signal Spectrum (bottom-left):**
   - Linear magnitude |X(e^jΩ)|
   - Dashed vertical lines at expected signal frequencies
   - Shade regions under window response contribution
   - Toggle: show windowed vs unwindowed comparison

4. **Log-Magnitude Spectrum (bottom-right):**
   - Primary visualization: 20 log|X(e^jΩ)| in dB
   - Horizontal dashed lines at -13dB, -43dB, -58dB (common side-lobe levels)
   - Frequency grid normalized to bin width (2π/N)
   - Peak markers with frequency/magnitude readout
   - Main-lobe extent highlighted with shaded region

**Interactive exploration:**
- Slider to change N in real-time: observe narrowing main lobe as N increases
- Window selector: watch spectrum change without recomputing signal
- Zoom control: inspect side-lobe structure (logarithmic scale essential)
- Crosshair mode: click frequency to measure spectral properties (SNR, leakage power)

**Key insight:**
- Main lobe width inversely proportional to N (Rayleigh resolution criterion)
- Side-lobe suppression property of each window (fundamental trade-off: narrow main lobe ↔ low side lobes)
- Demonstrate spectral leakage: off-bin tone "spreads" across spectrum via window

### Implementation Notes
**Complexity:** Medium
- Window function library (rectangular, Hamming, Blackman, Hann, Bartlett)
- FFT computation for DFT
- Log-scale rendering with careful dB floor handling

**Key Algorithms:**
- NumPy window generation and FFT
- Proper zero-padding for fine spectral grid
- dB conversion with floor clipping
- Real-time parameter updates

**Dependencies:**
- NumPy (FFT, window functions via scipy.signal)
- SciPy (advanced windows: Kaiser, Nuttall)
- Plotly (log-magnitude rendering)

### Extension Ideas
**Beginner:**
- Compare spectral leakage for signals at bin centers vs between bins
- Measure actual side-lobe levels for each window type
- Relate window width to frequency resolution needed for task

**Advanced:**
- Design custom Kaiser window for specified side-lobe level
- Investigate spectral flatness (amplitude modulation distortion)
- Overlap-add windows for continuous signal processing

**Real-world:**
- Audio analysis: spectral leakage in music analysis (tuner, EQ software)
- Radar: range resolution limited by pulse width (window main lobe)
- Medical imaging: artifact suppression via windowing

---

## Simulation 4: Discrete-Time Signal Aliasing via Frequency Wrapping
### Lecture Source: Lecture 17 (DT Frequency), Pages 29-42; Lecture 19-2 (Relations), Pages 25-32
### Learning Objective
Develop deep intuition for **DT frequency periodicity and aliasing** by showing how CT signals are "wrapped" onto the unit circle when sampled. Observe that frequencies above π (or equivalently ω_s/2 in CT) wrap back into the Nyquist band, creating ambiguity.

### Theoretical Foundation
When sampling a CT signal x(t) at rate T_s, the DT frequency Ω relates to CT frequency ω via:
$$Ω = ωT_s = \frac{2πf}{f_s}$$

The frequency interval [0, f_s) in CT maps to [0, 2π) in DT (periodic with period 2π). Frequencies above f_s/2 alias:
$$f_{alias} = f - kf_s$$ (nearest multiple of f_s)

This is a **rotation on the unit circle**: as ω increases beyond π/T_s, the point e^{jωT_s} continues around the circle, wrapping back to lower Ω values.

### System Architecture
**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|-----------|
| CT Frequency f | 0.1 - 10 kHz | Analog signal frequency | Slider (log) |
| Sampling Rate f_s | 1 - 20 kHz | Digital sampling rate | Slider (log) |
| Animation Speed | 0.5 - 3x | Playback speed | Slider |
| Signal Type | {sinusoid, swept (chirp)} | Test signal | Radio buttons |
| Waveform Display | {time, frequency, unit circle} | Main view | Tab selector |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|----------------|---------|
| CT waveform | Continuous curve x(t) | Show original analog signal |
| Sampled waveform | Discrete points overlaid on CT curve | Show sampling process |
| Unit circle | e^{jΩ} trace as Ω varies | Demonstrate periodic wrapping |
| Discrete-time sequence | Stem plot x[n] | See aliased signal in time |
| Nyquist folding | Frequency reflection at f_s/2 | Visualize aliasing mechanism |
| Frequency domain | Both CT (Fourier) and DT (z-transform) | Compare representations |

### Visualization Strategy

**Three-panel interactive layout:**
1. **CT Signal and Sampling (top-left):**
   - Smooth curve: x(t) = A sin(2πft)
   - Vertical needle lines at t = nT_s showing sample values
   - Filled circles at sample points x[n]
   - Animation: point moves along CT signal; sampling "freezes" values
   - Text readout: current time t, frequency f, sampled value x[n]

2. **Unit Circle Mapping (top-right, large):**
   - Unit circle (reference circle)
   - Spiral or trajectory showing e^{jΩn} as time progresses
   - Color gradient: red at Ω = 0, blue at Ω = π (Nyquist), red again at Ω = 2π (wrapped)
   - Annotations: f_s/2 line (Nyquist), aliasing direction arrows
   - As f increases, rotation speed around circle increases
   - When f > f_s/2, circle rotation reverses (aliasing visualization)

3. **Frequency Domain Comparison (bottom-left + right):**
   - Left: CT Fourier Transform |X(f)| with impulses at f, 2f_s - f, 2f_s + f, ... (replicated spectrum)
   - Right: DT unit-circle frequency response |X(e^{jΩ})| showing wrapped spectrum
   - Overlay box: highlight aliased frequency and its true identity
   - Example: f = 7 kHz sampled at f_s = 10 kHz → wraps to Ω = 0.4π (alias = 3 kHz)

**Interactive Features:**
- **Play button:** animates time progression, continuous sine wave wrapping on unit circle
- **Drag CT frequency:** watch rotation speed change; see aliasing occur when f > f_s/2
- **Adjust f_s:** compress/expand unit circle mapping; show margin to Nyquist
- **Aliasing calculator:** hover over unit circle point to see corresponding CT frequencies
- **Magnitude plot toggle:** switch between linear/log scale to see alias contributions

**"Aha" Moment Sequence:**
1. Low f, high f_s: point moves slowly around circle, sampled values form obvious sinusoid
2. Increase f while keeping f_s constant: rotation speed increases, still unambiguous
3. Reach f = f_s/2: point sticks at Ω = π (Nyquist limit), sampled values alternate ±A
4. Exceed f_s/2: point rotates backward on circle (aliasing!), identical samples to lower frequency
5. Show multiple CT frequencies mapping to same Ω value

### Implementation Notes
**Complexity:** Medium-High
- Real-time animation of CT signal and unit circle trajectory
- Frequency-domain synchronization across multiple views
- Circular coordinate transformations

**Key Algorithms:**
- CT signal generation: x(t) = A sin(2πft)
- Sampling: x[n] = x(nT_s)
- Unit circle parametrization: e^{jΩn} where Ω = 2πfT_s
- Frequency aliasing formula: f_alias = ((f mod f_s) + f_s/2) mod f_s - f_s/2

**Dependencies:**
- NumPy (trigonometry, modular arithmetic)
- Plotly (animated scatter traces)
- Custom animation controller for synchronized updates

### Extension Ideas
**Beginner:**
- Predict aliased frequency for given f, f_s pair
- Identify minimum f_s needed to avoid aliasing for given signal bandwidth
- Observe that sampled signals are indistinguishable only up to aliasing

**Advanced:**
- Multi-tone signals: visualize which frequency components alias to same Ω
- Bandpass sampling: sample signals at rates < 2×bandwidth (sub-Nyquist, non-intuitive)
- Anti-aliasing filter design: preview how pre-filtering prevents aliasing artifacts

**Real-world:**
- Audio: explain "Phantom Frequencies" in undersampled recordings (e.g., audio at 8kHz sampled from 44.1kHz source)
- Instrumentation: choose sampling rate for measurement equipment (ADC specs)
- Radar/Sonar: velocity ambiguity from PRF (pulse repetition frequency)

---

## Simulation 5: Custom Signal Design from Fourier Series Coefficients
### Lecture Source: Lecture 16 (Fourier Transform duality), Pages 34-35; Lecture 17 (DT Fourier Series), Pages 45-53
### Learning Objective
Build intuition for **how Fourier series coefficients control waveform shape** through interactive coefficient editing. See harmonic content directly map to time-domain features (smoothness, discontinuities, oscillations).

### Theoretical Foundation
A periodic signal is uniquely determined by its Fourier series coefficients:
$$x[n] = \sum_{k=0}^{N-1} a_k e^{j2πkn/N}$$

Each coefficient a_k (complex amplitude and phase) contributes a harmonic at frequency Ω_0 = 2π/N. Magnitude |a_k| controls harmonic strength; phase ∠a_k controls relative timing.

Real signals have conjugate-symmetric coefficients: a_{-k} = a_k*. Non-smooth signals (discontinuities, sharp corners) require high-frequency content (large |a_k| for large k).

### System Architecture
**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|-----------|
| Period N | 8 - 32 | Number of harmonics | Slider |
| Harmonic Index k | 0 - N-1 | Which harmonic to edit | Spinner |
| Magnitude |a_k| | 0 - 2 | Harmonic amplitude | Slider with dB option |
| Phase ∠a_k | 0 - 2π | Harmonic phase shift | Angle dial or slider |
| Symmetry Mode | {free, conjugate} | Real/complex signal constraint | Radio button |
| Preset | {square, triangle, sawtooth, custom} | Quick-load templates | Dropdown |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|----------------|---------|
| Coefficient editor | Interactive magnitude/phase for each k | Manipulate spectral content |
| Magnitude spectrum | Bar chart of |a_k| | See harmonic contribution |
| Phase spectrum | Plot of ∠a_k | Show phase relationships |
| Time-domain waveform | Animated synthesis x[n] | Watch signal build from harmonics |
| Constituent harmonics | Individual traces for selected k values | See individual frequency components |
| Sum/partial sum | Cumulative trace as harmonics added | Observe convergence to target shape |

### Visualization Strategy

**Split-screen dual-domain interface:**

**Left Panel: Coefficient Editor**
- Vertical slider array (one per harmonic k = 0 to N-1)
- Each slider: magnitude 0 to 2, color-coded magnitude
- Tap slider to open phase dialog (angle wheel with 0-2π range)
- Below sliders: magnitude spectrum bar chart (blue bars)
- Right of bars: phase spectrum (angles, red/negative phase shown differently)
- Magnitude spectrum in dB toggle for better resolution at low levels

**Right Panel: Time-Domain Synthesis**
- Large primary plot: reconstructed signal x[n]
- Step/continuous plot options for waveform appearance
- Overlay checkbox: show selected harmonic contribution only
- Constituent harmonics view: smaller subplots for k = 0, 1, 2, ... (with toggles)
- Cumulative sum animation: play button starts adding harmonics one-by-one; watch shape converge
- Time-domain grid showing one period [0, N-1]

**Interactive Discovery Workflow:**
1. Start with preset (square wave): see all odd harmonics, zero even harmonics
2. Edit k=1 magnitude: DC offset changes
3. Increase k=3 magnitude: sharper transitions appear in time domain
4. Toggle high harmonics (k > N/2) on/off: see Gibbs ripple appear/disappear near discontinuities
5. Adjust phase of single harmonic: entire waveform shifts/rotates without changing shape

**Aha Moments:**
- Zero out all harmonics except k=0: pure DC (constant line)
- Non-zero only k=1: pure sinusoid (fundamental frequency)
- Add k=3, 5, 7, ... with decreasing magnitude: square wave approximation improves with each odd harmonic
- Swap phase of two harmonics: symmetric vs antisymmetric waveforms result

### Implementation Notes
**Complexity:** Medium
- Real-time IDFT (inverse discrete Fourier transform) computation
- Synchronized magnitude/phase editing
- Harmonic constraint enforcement (conjugate symmetry for real signals)

**Key Algorithms:**
- IFFT (inverse FFT) for synthesis from coefficients
- Magnitude/phase ↔ rectangular complex conversion
- Harmonic constraint: a_{N-k} = a_k* for real-valued signals

**Dependencies:**
- NumPy (FFT/IFFT)
- Plotly (synchronized plots)
- React hooks (state management for coefficient array)

### Extension Ideas
**Beginner:**
- Explore presets and identify harmonic patterns
- Create approximations of given waveforms (e.g., ECG signal, speech sample)
- Measure how many harmonics needed for target error threshold

**Advanced:**
- Inverse problem: given target time-domain waveform, design coefficients for best fit
- Exploit Parseval's theorem: energy in time ↔ energy in frequency (sum of |a_k|^2)
- Design band-limited signals (zero coefficients for k > k_max)

**Real-world:**
- Audio synthesis: create custom tones for music/tone generation
- Signal generation: design test signals matching real-world characteristics
- Compression: decide which harmonics to keep vs discard (MP3-like compression)

---

## Simulation 6: Filtering Cascade and Frequency Response Chain
### Lecture Source: Lecture 20 (Applications), Pages 1-18
### Learning Objective
Develop understanding of **cascade system behavior** by showing how filtering stages compose in both time and frequency domains. Observe magnitude response multiplication and phase addition.

### Theoretical Foundation
When LTI systems cascade, the overall system function is the product of individual transfer functions:
$$H_{total}(jω) = H_1(jω) × H_2(jω) × H_3(jω) × ...$$

In dB scale (magnitude):
$$|H_{total}(jω)|_{dB} = |H_1(jω)|_{dB} + |H_2(jω)|_{dB} + ...$$

Phase:
$$∠H_{total}(jω) = ∠H_1(jω) + ∠H_2(jω) + ...$$

This allows "filter design by composition": combine simple stages (1st-order, 2nd-order sections) to achieve complex response.

### System Architecture
**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|-----------|
| Cascade Stages | 1 - 4 | Number of filters in series | Spinner |
| Stage k: Filter Type | {LP, HP, BP, notch} | kth stage type | Dropdown per stage |
| Stage k: Cutoff Freq | 0.01 - 10 ω_0 | Critical frequency (normalized) | Slider per stage |
| Stage k: Q Factor | 0.5 - 10 | Resonance/selectivity (for BP, notch) | Slider per stage |
| Input Signal | {sinusoid, multi-tone, white noise, chirp} | Test signal | Select dropdown |
| Frequency Scale | {linear, log} | Bode plot axis | Radio button |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|----------------|---------|
| Individual filter responses | Separate Bode plots for H_1, H_2, ... | Understand each stage |
| Cascade magnitude | Product of magnitudes (log-scale) | See composition behavior |
| Cascade phase | Sum of phases | Show cumulative phase shift |
| Time-domain input/output | Waveforms before and after cascade | See filtering in action |
| Pole-zero diagram | All poles/zeros from cascade superimposed | Understand system stability, order |
| Frequency zoom | Pan/zoom controls for Bode plots | Explore transition regions |

### Visualization Strategy

**Dashboard with filter blocks and analysis:**
1. **Filter Block Diagram (top):**
   - Visual signal flow: Input → [Stage 1] → [Stage 2] → ... → Output
   - Each stage is a colored box with type label and cutoff frequency
   - Curved arrows between stages showing signal flow
   - Click stage to edit parameters in sidebar

2. **Time-Domain Traces (middle-left):**
   - Input signal (thin gray)
   - Output signal (bold color, synchronized with Bode plots)
   - Side-by-side waveforms for easy comparison
   - Time scale covering several periods

3. **Bode Plot Stacking (middle-right, critical area):**
   - **Magnitude panel (top):** Log scale, linear frequency or log frequency
     - Separate traces for each H_k(jω) (light colors, thin lines)
     - Overlay total cascade |H_total(jω)| (bold black line)
     - Grid showing filter cutoffs as vertical dashed lines
   - **Phase panel (bottom):** Linear scale
     - Individual ∠H_k(jω) (light colored, thin)
     - Sum ∠H_total(jω) (bold color)
     - Wrap mode toggle: continuous vs modulo 2π
   - Synchronized vertical line showing current analysis frequency

4. **Pole-Zero Diagram (middle-right bottom):**
   - All poles and zeros plotted in s-plane or z-plane
   - Color-coded by originating stage
   - Circled group of poles/zeros for each filter
   - Stability region shaded (left half-plane for s, unit circle interior for z)

5. **Filter Specification Table (bottom sidebar):**
   - Row per stage: Type, Cutoff, Q, α (time constant)
   - Editable inline
   - Quick presets: "Standard 2nd-order low-pass," etc.

**Interactive Exploration:**
- Drag filter cutoff slider: watch Bode plots update in real-time
- Toggle individual stage on/off: see contribution to cascade
- Change filter order: compare 1st vs 2nd-order sections
- Input frequency sweep (chirp): animated trace following Bode response
- Phase unwrap toggle: see continuous phase accumulation

**Aha Moments:**
- Series LPF + HPF (band-pass): see magnitude multiplication create bandpass characteristic
- Cascade identical filters: steeper roll-off than single stage
- Phase accumulation: high-order systems have significant phase lag near cutoff
- Notch filter in cascade: create narrow rejection band while preserving overall gain

### Implementation Notes
**Complexity:** High
- Real-time computation of cascade transfer function
- Bode plot magnitude/phase extraction
- Pole-zero placement and stability monitoring

**Key Algorithms:**
- Transfer function multiplication (polynomial or state-space)
- Frequency response evaluation on jω axis
- Bode plot generation (log magnitude, unwrapped phase)
- Cascade stability: all poles in LHP (or z-domain: inside unit circle)

**Dependencies:**
- SciPy (signal.TransferFunction, signal.bode)
- NumPy (polynomial operations)
- Plotly (Bode plots with synchronized grids)

### Extension Ideas
**Beginner:**
- Design simple 1st-order cascades for target passband/stopband
- Relate cutoff frequency to time-domain rise time, settling time
- Observe Bode asymptotes behavior

**Advanced:**
- Second-order sections (SOS) design: stability, peaking behavior
- Filter sensitivity: how pole movement affects response
- Allpass filters: constant magnitude, varying phase (group delay design)

**Real-world:**
- ECG filtering: cascade high-pass (remove DC), low-pass (remove noise), notch (50/60 Hz)
- Audio graphic equalizer: cascade band-pass filters
- Control systems: cascade compensators (lead, lag filters) for loop shaping

---

## Simulation 7: Spectral Convolution and Modulation Effects
### Lecture Source: Lecture 19-2 (Relations), Pages 15-20 (impulse train multiplication/convolution); Lecture 20 (Applications)
### Learning Objective
Visualize **frequency-domain convolution** by showing how multiplication in time domain (modulation, windowing) becomes convolution in frequency domain. Develop intuition for spectral broadening, sidebands, and modulation sidebands.

### Theoretical Foundation
A fundamental duality: multiplication in one domain is convolution in the other.
$$x(t) × m(t) ↔ X(jω) * M(jω)$$

Examples:
- **Windowing:** x(t) × w(t) → X(jω) * W(jω) (spectral leakage from window sidelob)
- **Modulation (AM):** x(t) × e^{jω_c t} → X(j(ω - ω_c)) (frequency shift)
- **Sampling:** x(t) × p(t) → X(jω) * P(jω) (periodic repetition)

The convolution spreads narrowband signals across frequency.

### System Architecture
**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|-----------|
| Signal Type | {sinusoid, AM, window, impulse train, chirp} | x(t) to modulate/window | Select dropdown |
| Signal Frequency | 0.1 - 10 | f_signal (normalized) | Slider |
| Modulation Type | {amplitude (AM), phase (PM), pulse} | Operation applied | Select dropdown |
| Modulation Parameter | Varies | Carrier frequency, window width, pulse width | Slider per type |
| Signal Duration | 0.5 - 4 periods | Time extent | Slider |
| Zoom Frequency | 0 - 2 ω_max | Center frequency for detailed view | Slider |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|----------------|---------|
| Input signal x(t) | Time-domain waveform | Show original signal |
| Modulation signal m(t) | Envelope or modulating function | Show what's being applied |
| Product x(t)×m(t) | Modulated time-domain result | See time-domain multiplication |
| X(jω) | Original spectrum | Reference spectrum |
| M(jω) | Modulating spectrum | Show modulation function frequency content |
| Y(jω) = X(jω)*M(jω) | Convolution result spectrum | Primary pedagogical output |
| Decomposition | Animated sequence: X * M step-by-step | Build intuition for convolution |

### Visualization Strategy

**Multi-panel convolution exploration:**

1. **Time-Domain Section (top):**
   - Three stacked waveforms:
     - x(t): Original signal (blue)
     - m(t): Modulation/window function (red)
     - y(t) = x(t) × m(t): Product (green)
   - Aligned time axes; synchronized scroll
   - Annotation: highlight regions where m(t) is small (expect spectrum broadening)

2. **Individual Frequency Responses (middle-left):**
   - Top subplot: |X(jω)| (blue)
   - Bottom subplot: |M(jω)| (red)
   - Both on same frequency axis, amplitude scale
   - Narrow peaks for sinusoids, broad humps for windows/modulation signals

3. **Convolution Result (middle-right, large):**
   - |Y(jω)| = |X(jω) * M(jω)| (bold green)
   - Overlay faint outlines of X(jω) and M(jω) for reference
   - Annotations: original peaks, new sidebands, spectral spreading
   - Frequency axis with zoom capability

4. **Convolution Decomposition Animation (bottom):**
   - Step-by-step visualization of convolution:
     - Flip and slide M(jω) across ω axis
     - Shade region of overlap between X(jω) and flipped M(jω)
     - Accumulate area-under-product as convolution value
     - Animated trace of Y(jω) building point-by-point
   - Play/pause controls, step forward/backward buttons

**Interactive Discovery:**
- **AM Modulation:** Start with sinusoid, apply AM with low modulation frequency
  - See sidebands appear at ω_c ± ω_m
  - Increase modulation depth: sidebands grow
  - Increase modulation frequency: sidebands spread further apart

- **Windowing:** Start with sharp impulse, apply windowing
  - See impulse narrow in frequency (mainlobe shrinks)
  - Wider window → narrower mainlobe, higher sidelobes
  - Demonstrate frequency leakage

- **Chirp × Window:** Apply rectangular vs Hamming window to chirp
  - Rectangular: sharp cutoff, high sidelobes
  - Hamming: smoother edges, lower sidelobes but wider mainlobe

**Aha Moments:**
- Narrowband signal × narrowband modulation → sideband generation (BW expands)
- Broadband signal × narrowband modulation → broadband spectrum shifts/spreads
- Convolution with impulse train creates periodic repetition (sampling/aliasing)
- Window convolution explains spectral leakage origin

### Implementation Notes
**Complexity:** High
- FFT of both signals and their product
- Convolution in frequency (multiplication of FFTs)
- Animation of convolution sliding operation

**Key Algorithms:**
- FFT-based convolution
- Proper zero-padding for clean convolution display
- Frequency-domain integration for convolution value accumulation
- AM/PM modulation: x(t) × e^{jω_c t} or x(t) × cos(ω_m t)

**Dependencies:**
- NumPy/SciPy (FFT, convolution)
- Plotly (animated convolution slider visualization)
- Custom animation sequencer

### Extension Ideas
**Beginner:**
- Predict sideband frequencies for AM signal (ω_c ± ω_m)
- Measure bandwidth expansion from modulation
- Observe trade-off: deeper modulation → wider bandwidth

**Advanced:**
- SSB (single-sideband) AM: design filters to suppress one sideband
- Multi-tone modulation: cascade AM signals
- Phase modulation (FM): connect phase variation to frequency content

**Real-world:**
- Radio transmission: AM broadcast (modulating audio onto RF carrier)
- Communications: bandwidth expansion from digital modulation (PSK, QAM)
- Radar: Doppler shift (modulation from relative motion)

---

## Simulation 8: Laplace → Fourier Transform via jω axis
### Lecture Source: Lecture 16-2 (Fourier Transform), Pages 9-13
### Learning Objective
Visualize the geometric relationship between **Laplace transform (s-plane) and Fourier transform (jω axis)** by showing how evaluating H(s) along the imaginary axis gives frequency response. Understand region of convergence (ROC) role.

### Theoretical Foundation
The Fourier transform is a special case of the Laplace transform evaluated on the jω axis:
$$X(jω) = X(s)|_{s=jω}$$

This relationship only holds if the ROC of X(s) includes the jω axis.
- ROC: right half-plane (RHP) poles at σ = σ_p → ROC is Re(s) > σ_p
- For Fourier transform to exist: ROC must include jω axis (σ = 0)

**Key insight:** Laplace is 2D (complex plane s = σ + jω); Fourier is 1D (real frequency ω). Restricting to imaginary axis loses information about pole/zero location away from jω.

### System Architecture
**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|-----------|
| System | {1st-order LP, 2nd-order resonant, 3rd-order, custom} | Transfer function H(s) | Select dropdown |
| Pole Real Part σ_1 | -5 to 0 | Pole location (σ component) | Slider per pole |
| Pole Imaginary Part ω_1 | -5 to 5 | Pole location (ω component) | Slider per pole |
| Zero Location (similar) | Variable | Zeros in s-plane | Draggable on plane |
| Display Mode | {3D magnitude, contour, cross-section, animated} | Visualization style | Radio buttons |
| Frequency Range | [0, 5] or [-5, 5] | ω axis extent for Fourier view | Radio |
| Slice Frequency | 0 - 5 | Current frequency for cross-section | Slider |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|----------------|---------|
| s-plane diagram | Pole-zero plot with ROC shaded | Show system geometry |
| 3D Laplace magnitude | Surface |H(s)| in s-plane | Visualize full 2D transfer function |
| jω-axis slice | Cross-section of 3D surface along imaginary axis | Show Fourier transform extraction |
| Frequency response | |H(jω)| vs ω | Conventional Fourier magnitude |
| Phase response | ∠H(jω) vs ω | Phase of extracted Fourier transform |
| ROC indicator | Shaded region where H(s) converges | Determine Fourier transform existence |
| Pole stability | Poles in LHP vs RHP | Stability and causality implications |

### Visualization Strategy

**Three-part unified display:**

1. **S-Plane (left, large):**
   - Real axis (σ) horizontal; imaginary axis (ω) vertical
   - Red X for poles, blue O for zeros
   - Shaded ROC region (typically RHP, LHP, or strip)
   - **Bold imaginary axis (jω)** highlighted in green: "This is where Fourier is evaluated"
   - Draggable poles/zeros to adjust system
   - Crosshair tool: click on jω axis to select frequency for analysis
   - Pole locations constrained for causality (LHP for causal, stable systems)

2. **3D Magnitude Surface (middle, large):**
   - Surface plot: Z = |H(σ + jω)| over 2D s-plane
   - Color map: intensity ∝ magnitude (use viridis or similar)
   - Jω axis trace highlighted in bold (extracted curve)
   - Vertical plane along jω axis shows Fourier magnitude extraction
   - Rotation controls: inspect surface from multiple angles
   - Zoom/pan to focus on interesting regions (poles, zeros, ROC boundary)

3. **Right Panel: Comparative Plots (top to bottom):**
   - **Fourier Magnitude:** |H(jω)| vs ω (extracted from jω axis)
   - **Fourier Phase:** ∠H(jω) vs ω
   - **Pole/Zero Distance:** Visual representation of how each pole/zero contributes to magnitude at current frequency

**Interactive Exploration:**
- **Drag pole σ_1 slider:** Watch 3D surface peak move left/right; see how pole further from jω axis reduces frequency response magnitude
- **Drag pole ω_1 slider:** Move pole up/down; frequency response develops resonance at nearby ω
- **Pole crossing jω axis → ROC problem:** UI highlights warning, frequency response becomes undefined (Fourier doesn't exist)
- **Crosshair on jω at frequency ω_0:** Vertical plane shows contribution from all s = σ + jω_0 values; highlight the single point s = jω_0

**Aha Moments:**
- Poles far in LHP (large negative σ) → low influence on frequency response (already attenuated)
- Poles near jω axis (σ ≈ 0) → strong resonance peaks in Fourier transform
- Poles in RHP (σ > 0) → ROC doesn't include jω axis, Fourier transform doesn't exist (unstable system)
- Comparing σ-plane cross-sections: higher frequency ω requires evaluating at s = jω farther from poles

### Implementation Notes
**Complexity:** High
- 3D surface rendering with appropriate color mapping
- Magnitude computation across 2D s-plane (can be slow)
- Interactive pole/zero dragging with constraints
- Frequency response extraction along jω line

**Key Algorithms:**
- Evaluate H(s) at grid of s = σ + jω points
- Magnitude |H(s)| and angle ∠H(s) computation
- Constraint enforcement: poles in LHP, ROC verification
- Efficient computation: use logarithmic spacing for s-plane grid

**Dependencies:**
- NumPy (complex arithmetic)
- Plotly 3D (surface plot)
- Scipy (pole-zero placement utilities)

### Extension Ideas
**Beginner:**
- Explore stable vs unstable systems (pole locations)
- Observe how pole position affects resonance frequency and magnitude peak
- Compare Laplace (full 2D information) vs Fourier (1D slice)

**Advanced:**
- Design systems with specified frequency response: place poles/zeros to match
- Investigate Nyquist criterion using pole/zero information
- ROC analysis: determine causality and stability from Laplace transform

**Real-world:**
- Filter design: specify frequency response (Bode plot), design poles/zeros
- Control systems: pole placement for desired closed-loop response
- System identification: infer pole/zero locations from measured frequency response

