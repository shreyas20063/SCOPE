# Fourier Transform Lecture Series (16-20) - Simulation Ideas
**Analysis Date:** February 28, 2026
**Source Lectures:** MIT 6.003 Lectures 16-20 (CT/DT Fourier Transforms & Applications)

---

## Simulation 1: Fourier Transform Pair Navigator

### Lecture Source
Lecture 16, Pages 1-39 (CT Fourier Transform fundamentals)
Lecture 19, Pages 1-35 (CT/DT Transform Relations)

### Visual Cues Observed
- Bidirectional time ↔ frequency domain visualizations (Lecture 16, slides 3-8)
- Periodic extension from aperiodic signals creating impulse trains in frequency (Lecture 16, slides 6-7)
- Stretching time compresses frequency with amplitude preservation (Lecture 16, slides 22-26)
- Duality property showing symmetry between time and frequency domains (Lecture 16, slides 34-35)
- Check-yourself problems showing square pulses and their Fourier transforms (Lecture 16, slides 14-21)

### Learning Objective
Students will develop intuition for how changes in the time-domain signal directly map to frequency-domain characteristics, and vice versa. Interactive exploration of the uncertainty principle embedded in signal processing: narrower time signals → wider frequency content.

### Theoretical Foundation
The Fourier transform relationship:
- Analysis: X(jω) = ∫ x(t) e^(-jωt) dt
- Synthesis: x(t) = (1/2π) ∫ X(jω) e^(jωt) dω
- Time scaling: x(at) ↔ (1/|a|) X(jω/a)
- Time shift: x(t-t₀) ↔ e^(-jωt₀) X(jω)
- Moments: X(jω)|_{ω=0} = ∫ x(t) dt (area under x(t))

### System Architecture

**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|-----------|
| pulse_width | 0.5-4.0 | Duration of rectangular pulse in time | slider |
| time_stretch | 0.25-4.0 | Scaling factor a in x(at) | slider |
| frequency_scale | 0.1-10 | Visual zoom on frequency axis | logarithmic slider |
| signal_type | {rect, tri, gaussian, sinc} | Signal morphology | dropdown |
| center_frequency | 0-5 (Hz) | Modulation center (for chirp variant) | slider |
| phase_offset | 0-2π | Initial phase in complex representation | slider |

**Output Observables:**
| Observable | Visualization | Purpose |
|-----------|----------------|---------|
| Time-domain signal | Line plot with shaded area | Visual time localization |
| Magnitude spectrum | Bar/line plot (log scale) | Frequency content distribution |
| Phase spectrum | Wrapped angle plot (-π to π) | Phase information across frequencies |
| Spectral moments | Vertical cursors on both domains | Demonstrate moment calculations |
| Time-frequency product | Text readout + shading | Illustrate uncertainty principle |
| 3D surface (optional) | Height = magnitude, color = phase | Complex plane visualization |

### Visualization Strategy

**Main Layout:**
1. **Left Panel (Time Domain):**
   - Top: Adjustable time-domain signal with fill showing area
   - Middle: Slider controls for pulse_width and time_stretch
   - Bottom: Numerical readout of time-domain moments and signal energy

2. **Right Panel (Frequency Domain):**
   - Top: Magnitude spectrum (log scale, dB) with peak frequency marker
   - Middle: Phase spectrum with phase coherence indicator
   - Bottom: Frequency domain statistics (bandwidth, -3dB cutoff)

3. **Linking Visualization:**
   - Hovering over time-domain point shows corresponding frequency components
   - Hovering over frequency component shows time-domain contribution
   - Animation slider plays through time to show signal evolution

4. **Educational Annotations:**
   - Display derived properties: signal area = DC component
   - Show time-bandwidth product continuously
   - Highlight which time-domain features create which frequency peaks

### Implementation Notes

**Complexity:** High
**Estimated Effort:** 80-100 hours

**Key Algorithms:**
1. Fast Fourier Transform (NumPy FFT) for efficient spectrum computation
2. Numerical integration (scipy.integrate.quad) for moment calculation
3. Analytical solutions for standard signals (rect, tri, gaussian, sinc)
4. Windowing functions (Hann, Hamming) for spectral smoothing
5. Peak detection (scipy.signal.find_peaks) for feature highlighting
6. Numerical differentiation for group delay visualization

**Frontend Components:**
- Dual-synchronized plots (Plotly) with linked hover effects
- Logarithmic frequency axis with grid at octave intervals
- 3D surface plot option (Three.js) for magnitude/phase visualization
- Animation timeline slider for "watching" frequency spectrum evolve as signal stretches
- Custom legend showing theoretical vs. computed values

**Backend Considerations:**
- Cache precomputed FFTs for responsive slider interaction
- Use analytical formulas where available (sinc, gaussian) for exact values
- Support custom signal input via expression parser (already in codebase)
- Debounce parameter updates to avoid excessive computation

### Extension Ideas

1. **Modulation Explorer:** Add AM/FM modulation with sidebands visualization showing frequency shift property
2. **Convolution Visualization:** Interactive convolution in time domain with real-time frequency multiplication display
3. **Window Functions:** Compare rectangular vs. Hann vs. Hamming windowing effects on spectral leakage
4. **Uncertainty Trade-off:** Show Gaussian envelope and demonstrate minimum time-bandwidth product
5. **Multi-signal Composition:** Overlay multiple signals and watch their spectra combine
6. **Phase Importance:** Show how phase errors affect signal reconstruction from magnitude-only spectra
7. **Chirp Signals:** Add linear/exponential chirp with instantaneous frequency visualization

---

## Simulation 2: DT Frequency Response Unit Circle Explorer

### Lecture Source
Lecture 17, Pages 1-26 (DT Frequency Response with Vector Diagrams)
Lecture 18, Pages 1-18 (DT Fourier Representations & Effects)

### Visual Cues Observed
- Z-plane with unit circle prominently displayed (Lecture 17, slides 18-27)
- Vector diagrams from poles/zeros to evaluation point on unit circle (Lecture 17, slides 18-27)
- Magnitude response showing frequency-dependent gain (Lecture 17, slides 18-27)
- Phase response showing angle variation around unit circle (Lecture 17, slides 18-27)
- Pole/zero locations creating resonances and notches in frequency response (Lecture 17, slides 3-5)
- Effects of pole proximity to unit circle on response peaking (Lecture 17, slide 5)

### Learning Objective
Students will develop geometric intuition for how pole and zero positions in the z-plane determine the system's frequency response when evaluated on the unit circle. Interactive exploration of DT filter design through pole-zero placement.

### Theoretical Foundation
For a DT system:
- H(z) = (Product of (z - q_i)) / (Product of (z - p_j)) where q_i = zeros, p_j = poles
- Frequency response: H(e^(jΩ)) = H(z) evaluated at z = e^(jΩ)
- Magnitude: |H(e^(jΩ))| = (Product of |e^(jΩ) - q_i|) / (Product of |e^(jΩ) - p_j|)
- Phase: ∠H(e^(jΩ)) = Sum of ∠(e^(jΩ) - q_i) - Sum of ∠(e^(jΩ) - p_j)
- Periodicity: H(e^(jΩ)) has period 2π in Ω

### System Architecture

**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|-----------|
| num_poles | 1-4 | Number of poles in z-plane | spinner |
| num_zeros | 0-4 | Number of zeros in z-plane | spinner |
| pole_radius[i] | 0.1-0.99 | Distance from origin for pole i | slider (per pole) |
| pole_angle[i] | 0-2π | Angle in z-plane for pole i | angle slider (per pole) |
| zero_radius[i] | 0-0.99 | Distance from origin for zero i | slider (per zero) |
| zero_angle[i] | 0-2π | Angle in z-plane for zero i | angle slider (per zero) |
| eval_frequency | 0-π | Current Ω for evaluation on unit circle | draggable point on circle |
| gain_constant | 0.1-10 | Overall system gain K | logarithmic slider |

**Output Observables:**
| Observable | Visualization | Purpose |
|-----------|----------------|---------|
| Z-plane diagram | Complex plane showing poles (×), zeros (○), unit circle | System structure visualization |
| Magnitude response |Plotly trace |H(e^(jΩ))| vs. Ω | Frequency selectivity |
| Phase response | Plotly trace | ∠H(e^(jΩ)) vs. Ω | Phase characteristics |
| Vector diagram | Arrows from poles/zeros to evaluation point | Geometric magnitude/phase interpretation |
| Group delay | -d(∠H)/dΩ computed numerically | Phase distortion characterization |
| Numerical readout | |H(e^(jΩ))|, ∠H(e^(jΩ)), pole Q-factor | Quantitative values |

### Visualization Strategy

**Three-Panel Layout:**
1. **Left Panel (Z-Plane):**
   - Unit circle (radius 1, blue)
   - Pole markers (red ×) with labels
   - Zero markers (blue ○) with labels
   - Current evaluation point (Ω) highlighted on unit circle
   - Vector arrows from each pole/zero to evaluation point
   - Real/Imaginary axes with grid

2. **Top-Right Panel (Magnitude Response):**
   - Frequency Ω from 0 to π on x-axis
   - Magnitude (dB or linear) on y-axis
   - Current frequency position marked with vertical line
   - Resonance peaks and notches highlighted
   - -3dB line for bandwidth reference

3. **Bottom-Right Panel (Phase Response):**
   - Frequency Ω from 0 to π on x-axis
   - Phase angle (-π to π) on y-axis
   - Phase discontinuities at notches
   - Current phase angle marked
   - Group delay (secondary axis) in sample units

**Interaction Model:**
- Drag poles/zeros in z-plane to adjust frequency response interactively
- Click on unit circle to evaluate response at that frequency
- Double-click poles/zeros to toggle stability warning
- Hover over magnitude peaks to show -3dB bandwidth

### Implementation Notes

**Complexity:** Medium-High
**Estimated Effort:** 60-80 hours

**Key Algorithms:**
1. Vector magnitude/angle calculation from z-plane points
2. Frequency response synthesis: evaluate H(e^(jΩ)) for dense Ω grid
3. Magnitude/phase extraction from complex H(e^(jΩ))
4. Group delay computation via numerical differentiation: -d(phase)/dΩ
5. Stability checking: ensure all poles have |p| < 1
6. Filter cascade: support series connection of multiple stages

**Frontend Components:**
- Draggable point elements in SVG canvas for pole/zero placement
- Synchronized 3-panel view with linked frequency markers
- Plotly traces for magnitude and phase with custom hover
- Animated "sweep" mode to show how vector magnitudes/angles vary around circle
- Preset filter templates (Butterworth low-pass, notch, etc.)

**Backend Considerations:**
- Efficient polynomial multiplication for cascaded systems
- Cache frequency response evaluations for responsive interaction
- Support direct form and cascade form transfer function entry
- Validate pole placement for causality/stability
- Support both causal and non-causal systems

### Extension Ideas

1. **Filter Design Wizard:** Specify desired -3dB bandwidth and peaking, auto-place poles/zeros
2. **Cascade Connection:** Connect two stages and show composite frequency response
3. **Difference Equation Viewer:** Show h[n] (impulse response) and difference equation for current pole-zero configuration
4. **Step Response:** Simulate system response to unit step input
5. **Stability Region Overlay:** Highlight stable region (inside unit circle) vs. unstable
6. **All-Pass Filter:** Demonstrate constant magnitude but varying phase
7. **Inverse System Design:** Find H^(-1)(z) to invert filtering operation
8. **IIR vs. FIR:** Compare infinite impulse response pole-based design with FIR zero-only design

---

## Simulation 3: Spectral Windowing and Leakage Explorer

### Lecture Source
Lecture 18, Pages 4-7 (Fast Fourier Transform with windowing implications)
Lecture 20, Pages 1-24 (Applications: ECG filtering, CD diffraction)

### Visual Cues Observed
- ECG signal with low-frequency and high-frequency noise components (Lecture 20, slide 14)
- Magnitude spectrum in dB showing noise floor and cardiac signal peaks (Lecture 20, slide 14)
- Filter cascade design: low-pass + high-pass + notch filter (Lecture 20, slide 15)
- 60 Hz powerline interference as narrow notch in ECG (Lecture 20, slides 12-17)
- Spectral leakage effects when signals don't align with FFT bins (implied in Lecture 18, slides 4-7)

### Learning Objective
Students will understand how windowing functions trade spectral resolution for leakage reduction, and see practical application in ECG filtering. Interactive design of realistic filter cascades to suppress noise while preserving signal.

### Theoretical Foundation
- Rectangular window: sinc(ω) main lobe, high side lobes (-13 dB) → spectral leakage
- Hann window: wider main lobe, low side lobes (-32 dB) → better leakage suppression
- Hamming window: intermediate trade-off
- Cascaded filters: H_total(jω) = H_LP(jω) × H_HP(jω) × H_notch(jω)
- Notch filter centered at ω₀: zeros at ±jω₀, poles nearby for sharpness
- ECG characteristics: 0.5-100 Hz cardiac signal, 60 Hz powerline, 0.1 Hz baseline wander

### System Architecture

**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|-----------|
| input_signal | {ecg_synthetic, square_wave, sine_chirp} | Test signal choice | dropdown |
| noise_type | {none, white, powerline_60hz, baseline_wander} | Noise source | checkbox array |
| noise_level | 0-1 | SNR in dB (mapped) | slider |
| window_type | {rect, hann, hamming, blackman} | FFT window function | dropdown |
| lp_cutoff | 50-200 Hz | Low-pass filter cutoff | slider |
| lp_order | 1-4 | Low-pass filter order | spinner |
| hp_cutoff | 0.01-1 Hz | High-pass filter cutoff | slider |
| hp_order | 1-4 | High-pass filter order | spinner |
| notch_freq | 50-70 Hz | Powerline notch center | slider |
| notch_Q | 5-50 | Notch sharpness (Q-factor) | slider |

**Output Observables:**
| Observable | Visualization | Purpose |
|-----------|----------------|---------|
| Input signal | Time-domain plot | Raw signal with noise |
| Windowed signal | Time-domain with window envelope | Effect of windowing |
| Magnitude spectrum (raw) | Log-scale with window shape overlay | Before filtering |
| Magnitude spectrum (filtered) | Log-scale post-cascaded filters | After noise suppression |
| Window function | Magnitude response in frequency | Spectral leakage characteristics |
| Cascaded filter response | Combined magnitude response | Overall cascade effect |
| Filtered time-domain | Time series after all processing | Final cleaned signal |
| SNR indicator | Numerical dB value pre/post filter | Quantitative improvement |

### Visualization Strategy

**Multi-Row Layout:**
1. **Row 1 (Input Signals):**
   - Left: Clean signal in time domain
   - Right: Noisy signal overlaid or stacked

2. **Row 2 (Window Functions):**
   - Left: Time-domain window (Hann, Hamming, etc.)
   - Right: Frequency magnitude response of window function
   - Interactive selection of window type

3. **Row 3 (Spectral Views):**
   - Left: Raw signal magnitude spectrum (dB) with window shape overlay
   - Right: Filtered signal magnitude spectrum
   - Annotations for 60 Hz powerline, cardiac band (0.5-100 Hz), noise floor

4. **Row 4 (Filter Controls & Cascade Response):**
   - Sliders for LP, HP, notch parameters
   - Center panel: Combined cascade magnitude response
   - Right panel: Phase response of cascade

5. **Row 5 (Output Time Domain):**
   - Full-screen time plot of filtered signal
   - Overlay of original clean signal as reference
   - MSE or SNR improvement metric

### Implementation Notes

**Complexity:** High
**Estimated Effort:** 70-90 hours

**Key Algorithms:**
1. Window function generation (Hann, Hamming, Blackman)
2. FFT with windowing (scipy.fft with window parameter)
3. Cascaded IIR filter design (scipy.signal.butter, iirnotch)
4. Frequency response synthesis for cascade H(jω) = H_LP × H_HP × H_notch
5. Synthetic ECG generation (using sum of harmonics or realistic QRS template)
6. 60 Hz sine injection for powerline noise
7. SNR calculation: 10*log10(signal_power / noise_power)

**Frontend Components:**
- Synchronized time-domain and frequency-domain plots
- Real-time filter response update as sliders change
- Toggle visibility of window overlay on spectrum
- Hover to show exact frequency/magnitude values
- A/B comparison mode to show before/after filtering
- Playback of filtered vs. unfiltered audio (optional)

**Backend Considerations:**
- Pre-compute analytical window transforms for fast redraw
- Support both FIR (window-based) and IIR (pole-zero) filter implementations
- Validate filter stability (poles inside unit circle for DT, left half-plane for CT)
- Cache filter coefficients to avoid recomputation
- Support filter order up to ~8 to keep system stable

### Extension Ideas

1. **Adaptive Filtering:** LMS or RLS algorithm to track time-varying noise (baseline wander)
2. **Multi-Rate Processing:** Decimation after LP filter to reduce computation
3. **Custom Noise Profile:** User uploads their own noise signal to filter
4. **Real ECG Data:** Load actual patient ECG recordings (with patient consent/privacy)
5. **Spectral Masking:** Visual indication of which frequency bands are being attenuated
6. **Filter Stability Analyzer:** Plot pole locations as filter order increases
7. **Optimal Window Selection:** Algorithm to recommend window based on signal characteristics
8. **Cepstral Analysis:** Show cepstrum for pitch detection or formant analysis

---

## Simulation 4: Time-Frequency Duality Interactive Mapper

### Lecture Source
Lecture 16, Pages 33-35 (Duality in Fourier Transform)
Lecture 19, Pages 1-39 (Relations among CT/DT Fourier Representations)

### Visual Cues Observed
- Duality transformation rules: t → ω, ω → -t, multiply by 2π (Lecture 16, slide 33)
- Converting from one Fourier pair to another using duality (Lecture 16, slides 34-35)
- Four representations: CTFS, CTFT, DTFS, DTFT (Lecture 19, slides 1-5)
- Relationships: sampling in time ↔ replication in frequency (Lecture 19, slides 26-32)
- Periodic extension in time ↔ sampling in frequency (Lecture 19, slides 10-21)
- Impulsive Fourier series transitions to Fourier transform (Lecture 16, slide 37)

### Learning Objective
Students will develop a conceptual framework for understanding all four Fourier representations as special cases of a unified transform. Interactive transformation explorer showing how modifications in one domain cascade to another.

### Theoretical Foundation
Duality property:
- If x(t) ↔ X(jω), then X(t) ↔ 2πx(-ω)
- Sampling in time (period T): x_s(t) = x(t) × p(t) → X_s(jω) = (1/T) X(jω) * P(jω)
- Periodic extension in time (period T): x_p(t) = x(t) * p(t) → X_p(jω) = 2π X(jω) · P(jω)
- Where p(t) is impulse train with period T
- Four combinations: (periodic, aperiodic) × (time discrete, time continuous)

### System Architecture

**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|-----------|
| signal_type | {pulse, gaussian, sinc, triangle, custom} | Base signal morphology | dropdown |
| periodic_in_time | {yes, no} | Make signal periodic T=4 | checkbox |
| discrete_in_time | {yes, no} | Sample signal with period Ts=0.5 | checkbox |
| time_scale_factor | 0.5-4 | Scaling a in x(at) | slider |
| period_T | 1-8 | Period if periodic_in_time=yes | slider |
| sampling_Ts | 0.1-1 | Sampling interval if discrete_in_time=yes | slider |
| frequency_zoom | 0.1-10 | Zoom on frequency axis | logarithmic slider |
| annotation_mode | {properties, duality_rules, impulse_locations} | Info overlay | radio buttons |

**Output Observables:**
| Observable | Visualization | Purpose |
|-----------|----------------|---------|
| Time-domain signal | Top plot showing x(t) or x[n] | Signal in time |
| Frequency-domain representation | Bottom plot showing X(jω), X(e^jΩ), or impulse train | Frequency content |
| 2×2 Representation Matrix | Small icons showing all 4 Fourier types | Context of current selection |
| Property indicators | Text: energy, DC value, periodicity, sampling info | Signal characteristics |
| Duality annotation | Arrows and labels showing which transformation was applied | Transformation history |
| Impulse locations (if applicable) | Vertical markers with ω values and amplitudes | Discrete spectral components |
| Numerical summary | Table of key properties before/after transformation | Quantitative changes |

### Visualization Strategy

**Layout Design:**
1. **Central 2×2 Grid:**
   - Each cell represents one Fourier representation (CTFS, CTFT, DTFS, DTFT)
   - Current representation highlighted with border
   - Arrows between cells labeled with transformation rules
   - Click cells to switch representations

2. **Main Display (Center-Right):**
   - Top panel: Time-domain signal visualization
   - Bottom panel: Corresponding frequency-domain representation
   - Synchronized time/frequency cursors

3. **Left Control Panel:**
   - Signal morphology selector
   - Checkboxes for periodic/discrete
   - Period and sampling interval sliders
   - Duality rule dropdown to apply specific transformation

4. **Right Info Panel:**
   - Properties table (period, sampling rate, frequency discretization, etc.)
   - Duality transformation rules as equations
   - Impulse locations table (if applicable)

5. **Bottom Transformation History:**
   - Breadcrumb showing applied transformations
   - Undo/reset buttons

### Implementation Notes

**Complexity:** High
**Estimated Effort:** 80-100 hours

**Key Algorithms:**
1. Signal generation for each morphology (pulse, gaussian, sinc, triangle)
2. Periodic extension via convolution with impulse train in time
3. Sampling via multiplication with impulse train in time
4. FFT for continuous-signal approximation
5. Duality transformation: swap time/frequency, negate frequency, scale by 2π
6. Impulse train Fourier transform (analytical)
7. Numerical integration for arbitrary signal analysis
8. Visualization of complex-valued signals (magnitude + phase or real + imaginary)

**Frontend Components:**
- 2×2 grid selector for representation choice
- Synchronized dual-axis plots (time and frequency)
- Animated transformation arrows between grid cells
- Overlay toggle for duality rules as equations
- Breadcrumb navigation of applied transformations
- 3D visualization option (magnitude and phase as height and color)

**Backend Considerations:**
- Pre-compute analytical Fourier pairs for standard signals
- Cache FFT results to avoid recomputation
- Support symbolic computation (SymPy) for exact analytical forms
- Validate that shown representations are mathematically consistent
- Handle edge cases: periodic extension beyond typical period, very high sampling rates

### Extension Ideas

1. **Transformation Wizard:** Step-by-step guide through which operations lead to each representation
2. **Constraint Solver:** Given desired properties in one domain, find necessary time-domain signal
3. **Interactive Equation Builder:** Build custom signals from basis functions and see result in all 4 representations
4. **Frequency Tiling Visualizer:** Show how impulse trains in frequency create periodic extensions
5. **Scaling Property Explorer:** Show how a in x(at) affects both time and frequency domains
6. **Convolution Visualization:** Two signals convolve in time → multiply in frequency
7. **Energy Parseval Visualization:** Show energy equivalence across domains
8. **Real vs. Complex:** Toggle between real signals and analytic signals (complex representation)

---

## Simulation 5: Phase-Magnitude Separation in Filtering

### Lecture Source
Lecture 18, Pages 2-3 (Effects of Phase in DT Filtering)
Lecture 20, Pages 2-18 (ECG Filtering with Magnitude and Phase Control)

### Visual Cues Observed
- Effects of phase on filtered speech: "artificial speech synthesized" (Lecture 18, slides 2-3)
- Magnitude-only vs. phase-preserving filtering comparison (Lecture 18, slides 2-3)
- ECG signal filtering with low-pass, high-pass, and notch components (Lecture 20, slide 15)
- Filter cascade showing pole locations for each component (Lecture 20, slide 17)
- Before/after ECG showing noise suppression (Lecture 20, slide 18)

### Learning Objective
Students will understand that filtering involves both magnitude and phase manipulation, and that phase distortion can be perceptually devastating even when magnitudes are preserved. Interactive exploration of minimum-phase vs. linear-phase filters.

### Theoretical Foundation
- Frequency response: H(jω) = |H(jω)| × e^(j∠H(jω))
- Magnitude response: Attenuation of each frequency component
- Phase response: ∠H(jω) determines temporal alignment
- Group delay: -d(∠H)/dω measures dispersion of frequencies
- Minimum-phase system: All zeros inside unit circle (or left half-plane in CT)
- Linear-phase system: ∠H(jω) = -ωτ (constant group delay, no dispersion)
- Zero-padding effect on phase reconstruction in frequency domain

### System Architecture

**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|-----------|
| input_signal | {speech, ecg, music_extract, synthetic} | Audio/signal type | dropdown |
| filter_type | {butterworth_lp, chebyshev_lp, linear_phase_lp, min_phase_lp} | Filter design method | dropdown |
| cutoff_freq | 100-4000 Hz | Filter cutoff frequency | slider |
| filter_order | 1-8 | Filter order / steepness | spinner |
| phase_mode | {magnitude_only, phase_only, combined} | Which component to apply | radio buttons |
| phase_distortion_severity | 0-1 | Synthetic phase warping for demo | slider |
| group_delay_visualization | {hide, show, animate} | Display group delay vs. frequency | dropdown |
| playback_speed | 0.5-2.0 | Audio playback rate (if applicable) | slider |

**Output Observables:**
| Observable | Visualization | Purpose |
|-----------|----------------|---------|
| Original signal (time) | Waveform plot | Input reference |
| Filtered signal (time) | Waveform plot | Magnitude filtering result |
| Magnitude-only filtered | Waveform plot | Result of applying \|H\| only |
| Phase-only filtered | Waveform plot | Result of applying ∠H only |
| Magnitude response | dB vs. frequency | Attenuation of each frequency |
| Phase response | Radians vs. frequency (wrapped) | Phase delay/lead |
| Group delay | Samples/seconds vs. frequency | Dispersion characteristic |
| Spectrogram (optional) | Time-frequency heatmap | Evolution of spectral content |
| SNR / quality metric | Numerical score | Perceptual quality comparison |

### Visualization Strategy

**Dual-Column Layout:**
1. **Left Column (Magnitude Filtering):**
   - Time plot: Original vs. magnitude-only filtered
   - Frequency plot: Magnitude response |H(jω)|
   - Listen button (for audio)
   - Quality metric

2. **Right Column (Full Filtering - Magnitude + Phase):**
   - Time plot: Original vs. fully filtered
   - Frequency plot: Magnitude response (same as left)
   - Phase response ∠H(jω) overlay
   - Group delay -d(∠H)/dω trace
   - Listen button (for audio)
   - Quality metric (higher SNR typically)

3. **Phase Response Details:**
   - Separate plot showing ∠H(jω) unwrapped
   - Group delay computed numerically
   - Linear-phase reference line (if applicable)
   - Annotation showing phase distortion severity

4. **Control Panel:**
   - Filter type dropdown
   - Cutoff frequency slider
   - Order spinner
   - Phase mode selector (magnitude only / phase only / combined)
   - Playback controls if audio

### Implementation Notes

**Complexity:** Medium
**Estimated Effort:** 50-70 hours

**Key Algorithms:**
1. Filter design: Butterworth, Chebyshev, linear-phase FIR (scipy.signal.butter, iirfilter, firwin)
2. Magnitude response extraction: |H(e^(jΩ))| computation
3. Phase response extraction: ∠H(e^(jΩ)) with unwrapping
4. Group delay: Numerical differentiation of unwrapped phase
5. Magnitude-only filtering: Apply magnitude, preserve original phase
6. Phase-only filtering: Keep original magnitude, apply only phase change
7. Audio synthesis: scipy.io.wavfile or librosa for speech/audio
8. Spectrogram: scipy.signal.spectrogram for time-frequency visualization

**Frontend Components:**
- Side-by-side magnitude-only and full-filtered plots
- Interactive phase response with group delay overlay
- Play/pause audio buttons with phase mode toggle
- Phase unwrapping visualization
- Slider to continuously vary filter cutoff with real-time update
- A/B listening comparison (if audio data)

**Backend Considerations:**
- Pre-compute filter coefficients for efficient convolution
- Support both IIR (causal, faster) and FIR (linear-phase option)
- Filter order limits: ensure stability for IIR
- Handle edge cases: very low cutoff frequencies, high-order filters
- Support audio file input (WAV, MP3 via librosa)
- Pre-compute group delay analytically where possible

### Extension Ideas

1. **Minimum-Phase vs. Maximum-Phase Comparison:** Show same magnitude with different phase characteristics
2. **Allpass Phase Warper:** Allpass filter with constant magnitude but variable phase
3. **Phase Reconstruction:** Given magnitude spectrum, explore different phase options and listen to result
4. **Linear-Phase FIR Design:** Interactive FIR design tool ensuring zero phase distortion
5. **Hilbert Transform:** Complex analytic signal representation with envelope vs. phase
6. **Speech Intelligibility Study:** Quantify how phase distortion affects speech recognition
7. **Music Genre Comparison:** Compare filtering effects on speech vs. music
8. **Interactive Pole-Zero to Phase:** Show how pole/zero locations determine phase response

---

## Simulation 6: Fourier Series to Transform Transition

### Lecture Source
Lecture 16, Pages 1-7 (Transition from Fourier Series to Fourier Transform)
Lecture 20, Pages 7-8 (Relation between Fourier Series and Transform)

### Visual Cues Observed
- Periodic extension with increasing period T showing convergence to Fourier transform (Lecture 16, slides 3-7)
- Impulse amplitude reduction as period increases: a_k → 0 as T → ∞ (Lecture 16, slides 3-7)
- Discrete frequency spacing ω₀ = 2π/T shrinking with increasing period (Lecture 16, slide 4)
- Limit process: continuous Fourier transform appears as envelope of discrete Fourier series (Lecture 16, slide 6)
- Relation between series coefficients a_k and transform X(jω): X(jω) = 2π a_k δ(ω - kω₀) (Lecture 16, slide 38 and Lecture 20, slide 8)

### Learning Objective
Students will visualize the conceptual limit process where periodic signals with increasingly long periods approach aperiodic signals, with their Fourier series converging pointwise to the Fourier transform. This builds intuition for how the two representations are intimately related.

### Theoretical Foundation
Periodic signal: x_T(t) = x(t) extended with period T
Fourier series coefficients: a_k = (1/T) ∫_{-T/2}^{T/2} x_T(t) e^(-j2πkt/T) dt
As T → ∞:
- Fundamental frequency ω₀ = 2π/T → dω (differential)
- Discrete frequencies kω₀ become continuous ω
- Impulse train in frequency: X(jω) = 2π Σ a_k δ(ω - kω₀)
- Synthesis: x(t) = (1/2π) ∫ X(jω) e^(jωt) dω

### System Architecture

**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|-----------|
| base_signal_type | {rect, tri, gaussian, sinc, sawtooth} | Core signal to extend periodically | dropdown |
| signal_duration | 0.5-2 | Initial signal extent in time | slider |
| period_T | 2-32 | Repetition period (multiples of signal duration) | slider |
| num_periods_shown | 1-4 | How many periods to display | spinner |
| frequency_axis_zoom | 0.5-4 | Vertical scale for impulse heights | slider |
| animation_speed | 0.1-2 | Rate of period increase in animation | slider |
| show_envelope | {on, off} | Display Fourier transform envelope | checkbox |
| view_mode | {series_only, transform_only, overlay} | Comparison mode | radio buttons |

**Output Observables:**
| Observable | Visualization | Purpose |
|-----------|----------------|---------|
| Time-domain signal | Extended periodic signal | Visualization of periodically extended x(t) |
| Fourier series coefficients | Impulse train at kω₀ = 2πk/T | Discrete frequency content |
| Fourier transform envelope | Smooth curve through impulse tops | Limiting case as T → ∞ |
| Frequency spacing | Annotation Δω = 2π/T | Decreases as period increases |
| Impulse height a_k | Labeled on each impulse | Decreases as period increases |
| Area preservation | X(jω) impulse area = 2πa_k | Maintains energy as T increases |
| Animation trajectory | Series → transform as T increases | Visual limit process |
| Numerical comparison | Table of a_k vs. envelope value at kω₀ | Quantitative convergence |

### Visualization Strategy

**Four-Panel Layout:**
1. **Top-Left (Time Domain):**
   - Signal x(t) shown in one "cell"
   - Periodically extended x_T(t) shown with period T
   - Shaded region indicating one period
   - Slider below to adjust T in real-time

2. **Bottom-Left (Frequency Domain - Series):**
   - Impulse train showing a_k at frequencies kω₀
   - Scaling on vertical axis auto-adjusts to show first few impulses clearly
   - Dashed envelope showing the Fourier transform X(jω)
   - Frequency axis with markings every ω₀

3. **Right (Comparison View - Optional):**
   - Small stacked plot showing evolution of series as T increases
   - Animation button to sweep period from small to large
   - Play/pause controls

4. **Control Panel (Below):**
   - Period slider T (drives all visualizations)
   - Signal type dropdown
   - Show/hide Fourier transform envelope checkbox
   - Play animation button
   - Reset button

### Implementation Notes

**Complexity:** Medium
**Estimated Effort:** 50-70 hours

**Key Algorithms:**
1. Periodic extension via numpy tile or repeat operations
2. Fourier series coefficient calculation (DFT via FFT, or analytical for standard signals)
3. Fourier transform computation (FFT as approximation, or analytical formula)
4. Envelope curve fitting (interpolation through impulse heights)
5. Limit behavior visualization: plot series for T = 2, 4, 8, 16, 32, ... showing convergence
6. Impulse train generation for frequency-domain plot
7. Area preservation visualization: highlight 2πa_k relationship

**Frontend Components:**
- Interactive slider to adjust period with smooth redraw
- Synchronized time and frequency plots
- Envelope curve overlay on impulse train
- Animated "morphing" from series to transform via increasing T
- Frequency axis with automatic rescaling
- Hover tooltip showing a_k values and envelope height at each impulse location
- Numerical readout of ω₀, ω_max shown, first N impulse values

**Backend Considerations:**
- For analytical signals (rect, tri, sinc, gaussian), provide exact Fourier pairs
- For others, use DFT with zero-padding to approximate transform
- Cache computations for multiple period values to enable smooth animation
- Normalization: ensure energy conservation as T increases
- Handle aliasing in frequency display (show only relevant frequency range)

### Extension Ideas

1. **Parseval's Theorem Visualization:** Show energy equivalence: Σ|a_k|² = ∫ |X(jω)|² dω/(2π)
2. **Time-Bandwidth Product:** Illustrate how narrow signal → wide spectrum, vice versa
3. **Windowing Effects:** Apply window (Hann, Hamming) and see leakage reduction
4. **Multiple Signals:** Superpose multiple signals and show series/transform for composite
5. **Frequency Domain Filtering:** Apply filter to series coefficients and inverse-transform
6. **Gibb's Phenomenon:** Truncate Fourier series and show oscillations near discontinuities
7. **Spectral Leakage from Truncation:** Show what happens if signal is cut off mid-period
8. **Phase Visualization:** Animate both magnitude and phase of a_k as T changes

---

## Simulation 7: CT/DT Fourier Transform Frequency Mapping

### Lecture Source
Lecture 19, Pages 26-32 (Relations between CT and DT transforms)
Lecture 20, Pages 26-32 (Sampling and Frequency Domain Aliasing)

### Visual Cues Observed
- Sampling in time: x[n] = x(nT) creates periodic replication in frequency (Lecture 19, slides 26-32)
- Frequency scaling: Ω = ωT relates DT frequency Ω to CT frequency ω (Lecture 19, slide 31-32, Lecture 20, slide 32)
- Periodicity of DT Fourier transform: period 2π in Ω (Lecture 17, slide 29)
- Aliasing when ω_max > π/T (Lecture 19, slides 26-32)
- Impulse train multiplication in time ↔ convolution in frequency (Lecture 19, slide 29)
- Impulse train FT creates periodic replicas with spacing 2π/T (Lecture 19, slide 30)

### Learning Objective
Students will develop intuition for the relationship between CT and DT frequency representations. Interactive exploration of how choosing a sampling rate affects the spectrum, including aliasing visualization.

### Theoretical Foundation
Sampling theorem:
- Sampled signal: x_p(t) = x(t) × Σ δ(t - nT)
- Sampled spectrum: X_p(jω) = (1/T) Σ X(j(ω - k·2π/T))
- DT Fourier transform: X(e^(jΩ)) where Ω = ωT
- Nyquist rate: f_N = 1/(2T) requires |ω| < π/T
- Aliasing: When ω_max > π/T, spectral replicas overlap

### System Architecture

**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|-----------|
| input_signal | {sinusoid, multi_tone, chirp, gaussian_pulse, custom} | CT signal to sample | dropdown |
| signal_freq_1 | 10-500 Hz | Frequency of primary sinusoid | slider |
| signal_freq_2 | 0-500 Hz (optional) | Frequency of secondary sinusoid | slider (if multi_tone) |
| sampling_rate | 100-2000 Hz | f_s = 1/T | slider |
| duration | 1-10 s | Display duration | spinner |
| spectrum_zoom | {full_ct, nyquist_zone, multiple_zones} | Frequency axis view | dropdown |
| aliasing_highlight | {off, on} | Color regions with aliased frequencies | checkbox |
| animation_mode | {none, sweep_freq, sweep_rate} | Animate over signal frequency or sample rate | radio buttons |

**Output Observables:**
| Observable | Visualization | Purpose |
|-----------|----------------|---------|
| CT signal | Time plot x(t) with sample marks | Original continuous signal |
| DT signal | Stem plot showing samples x[n] | Discrete-time representation |
| CT Fourier magnitude | Continuous spectrum |X(jω)| vs. ω (full range) | Input signal spectral content |
| CT sampled spectrum | X_p(jω) showing periodic replicas | Effect of sampling in frequency |
| DT Fourier magnitude | |X(e^(jΩ))| vs. Ω ∈ [-π, π] | DT spectrum in one Nyquist zone |
| Aliasing indicator | Shaded regions where aliasing occurs | Frequency overlap visualization |
| Nyquist rate marker | Vertical line at π/T on frequency axis | Critical sampling rate threshold |
| DT frequency label | Ω values converted to Hz via Ω = ωT | Frequency correlation display |
| Numerical readout | f_s, f_N, signal frequencies, aliased frequencies | Key parameters |

### Visualization Strategy

**Two-Column, Multi-Row Layout:**

**Left Column (CT Domain):**
1. Time plot: x(t) with sample markers at intervals T
2. CT Fourier magnitude: |X(jω)| vs. ω (continuous axis)
3. Nyquist rate indicator: vertical line at ωπ/T

**Right Column (DT Domain):**
1. Stem plot: x[n] samples
2. DT Fourier magnitude: |X(e^(jΩ))| vs. Ω ∈ [-π, π]
3. Frequency mapping annotation: Ω = ωT reference

**Frequency Axis Details:**
- Show actual frequency in Hz
- Highlight Nyquist zone boundaries
- Shade regions where aliasing occurs (when replicas overlap)
- Draw periodic replicas as dashed curves at multiples of f_s

**Interaction:**
- Slider for sampling rate continuously updates DT representation
- Signal frequency slider updates CT spectrum
- Animation mode sweeps signal frequency or sampling rate to show aliasing onset
- Hover on CT spectrum to see which DT frequency it maps to (via Ω = ωT)

### Implementation Notes

**Complexity:** Medium-High
**Estimated Effort:** 60-80 hours

**Key Algorithms:**
1. CT signal generation for standard types (sinusoid, chirp, gaussian pulse)
2. Sampling: x[n] = x(nT) at specified rate
3. FFT for both CT (zero-padded) and DT representations
4. Periodic replica generation: X_p(jω) with spacing 2π/T
5. Frequency mapping: ω ↔ Ω via Ω = ωT
6. Aliasing detection: identify overlapping spectral regions
7. Nyquist rate computation: f_N = 1/(2T) and corresponding ω_N = π/T
8. Animation: smoothly vary sampling rate or signal frequency

**Frontend Components:**
- Two-column synchronized plots (time and frequency domains)
- Interactive sampling rate slider with real-time DT update
- Periodic replica visualization via dashed curves at ±2π/T, ±4π/T, ...
- Color gradient for aliasing regions
- Tooltip showing Ω = ωT correspondence on hover
- Animation playback to show aliasing onset as sampling rate decreases
- Nyquist rate and maximum frequency numeric display

**Backend Considerations:**
- FFT zero-padding for high-resolution frequency representation
- Efficient numerical computation of periodic replicas
- Validation that displayed signal is actually realizable at given sample rate
- Handling of edge cases: very high frequencies, very low sampling rates
- Support both real and complex-valued signals

### Extension Ideas

1. **Reconstruction from Samples:** Show ideal lowpass filter reconstruction (sinc interpolation)
2. **Anti-Aliasing Filter Design:** Allow user to design and apply LP filter before sampling
3. **Multi-Rate Cascade:** Cascade sampling stages with different rates
4. **Quantization Effects:** Add quantization noise visualization alongside aliasing
5. **Spectrum Analyzer Mode:** Real-time spectrum display as signal frequency sweeps
6. **Undersampling Visualization:** Show aliased frequencies in DT domain when f_s < 2f_max
7. **Nyquist Instability:** Show what happens at exactly the Nyquist frequency
8. **Phase Alignment:** Show phase relationships between CT and DT representations

---

## Simulation 8: Interactive Diffraction Grating Fourier Transform

### Lecture Source
Lecture 20, Pages 19-35 (Fourier Transforms in Physics: Diffraction & Crystallography)
Lecture 20, Pages 36-41 (DNA X-ray Crystallography Application)

### Visual Cues Observed
- Diffraction grating creating periodic impulse train in spatial domain (Lecture 20, slides 19-20)
- Far-field diffraction pattern showing impulse train with reciprocal spacing 1/D (Lecture 20, slides 20-24)
- CD and DVD diffraction demonstrations with track spacing calculations (Lecture 20, slides 22-28)
- X-ray crystallography of DNA showing Fourier transform of helical structure (Lecture 20, slides 37-41)
- High-frequency bands indicating base-pair repeating structure (Lecture 20, slide 39)
- Low-frequency band tilt indicating double-helix pitch (Lecture 20, slide 41)

### Learning Objective
Students will see concrete physical applications of Fourier transforms in optics and X-ray crystallography. Interactive exploration of how object structure determines far-field intensity pattern through Fourier transform relationship.

### Theoretical Foundation
Fraunhofer diffraction (far-field approximation):
- Object transmission: f(x)
- Phase at angle θ: φ(x) = -2πx sin(θ)/λ
- Far-field intensity: F(θ) = ∫ f(x) e^(-j2πx sin(θ)/λ) dx
- Under small angle approximation: sin(θ) ≈ θ, so F(ω) = ∫ f(x) e^(-jωx) dx (Fourier transform!)
- Grating impulse train: f(x) = Σ δ(x - nD) → F(ω) = Σ δ(ω - n·2π/D) (reciprocal spacing)
- Periodic structure: high-frequency components indicate fine features; low-frequency tilt indicates overall shape

### System Architecture

**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|-----------|
| object_type | {single_slit, double_slit, grating, custom_pattern, dna_helix_approx} | Physical object structure | dropdown |
| grating_period_D | 100 nm - 10 μm | Spacing between grating lines | slider |
| slit_width | 50 nm - 5 μm | Width of single or double slit | slider |
| num_slits | 1-10 | Number of grating lines (for grating) | spinner |
| wavelength_lambda | 100 nm - 1000 nm (visible to IR) | Light wavelength | slider |
| observation_distance | 0.1-10 m | Distance from object to screen | slider |
| screen_width | 0.1-2 m | Width of observation screen | slider |
| helix_pitch (DNA only) | 3-5 nm | Pitch angle for helical structure | slider |
| helix_radius (DNA only) | 0.5-1.5 nm | Helix radius | slider |

**Output Observables:**
| Observable | Visualization | Purpose |
|-----------|----------------|---------|
| Object structure | Transmission function f(x) or 2D image | Physical object |
| Far-field intensity pattern | Grayscale image or 2D surface plot | Diffraction pattern |
| Fourier magnitude spectrum | |F(ω)| in frequency domain | Spectral representation of object |
| Phase (optional) | Color-coded phase angle | Full complex Fourier information |
| Reciprocal spacing | Annotation showing 2π/D | Validates grating formula |
| Wavelength effect | Parametric curves for different λ | Scaling relationship λ ↔ pattern size |
| Track spacing (CD/DVD) | Calculated spacing in nm/μm | Real-world grating applications |
| Helix visualization (DNA) | 3D helix with major/minor grooves | Molecular structure |

### Visualization Strategy

**Three-Panel Arrangement:**

1. **Left Panel (Object Domain):**
   - Spatial transmission function f(x) or 2D image
   - For gratings: periodic lines with spacing D labeled
   - For DNA: 2D projection or 3D helix display
   - Sliders to adjust object parameters (D, slit width, etc.)

2. **Center Panel (Far-Field Pattern):**
   - Grayscale intensity image or false-color visualization
   - Diffraction spots/fringes corresponding to |F(ω)|²
   - Scale bar showing distances
   - Numerical annotations of peak separations

3. **Right Panel (Fourier Domain):**
   - Magnitude spectrum |F(ω)| on log scale
   - Impulse locations marked for periodic structures
   - Reciprocal spacing annotation
   - Optional phase visualization

**Interactive Elements:**
- Drag sliders to change D, λ, slit width
- Real-time update of far-field pattern
- Zoom on far-field image to show detailed structure
- Toggle between intensity I ∝ |F|² and complex magnitude |F|
- Animation: sweep wavelength to see pattern scaling

### Implementation Notes

**Complexity:** High
**Estimated Effort:** 70-90 hours

**Key Algorithms:**
1. Single slit Fourier transform: sinc(ωa/2) where a = slit width
2. Multiple slit/grating Fourier transform: sinc(ωa/2) × Σ e^(-jωnD)
3. Fraunhofer diffraction integral (FFT on discretized object)
4. Reciprocal space mapping: ω = 2πθ/λ ≈ 2πsin(θ)/λ
5. 3D DNA helix model: parametric helical coordinates with groove visualization
6. Fourier transform of helix structure (analytical or numerical)
7. Intensity pattern: log scale for dynamic range

**Frontend Components:**
- Three-column layout with synchronized displays
- Grayscale or false-color heatmap for far-field pattern (Plotly or Three.js)
- 2D/3D visualization toggle for DNA structure
- Real-time slider updates with smooth animation
- Measurement tools: click points to measure distances in pattern
- Wavelength/distance calculator showing how pattern scales
- Reference marks on far-field screen (e.g., 1 mm grid)

**Backend Considerations:**
- Pre-compute analytical Fourier transforms for standard objects
- For arbitrary patterns, use 2D FFT on object grid
- Efficient convolution for multiple slits (shift property)
- Support both 1D (grating, slits) and 2D (DNA) transforms
- Physical unit conversions: nm, μm, m, Hz, rad/m

### Extension Ideas

1. **X-Ray Crystallography Suite:** Upload crystal structure and compute diffraction pattern
2. **Interactive Slit Width:** Show how slit width affects fringe contrast (visibility)
3. **Coherence Effects:** Partial coherence reducing contrast with increasing distance
4. **Multiple Wavelengths:** Polychromatic light creating color separation
5. **Aperture Diffraction:** Circular or elliptical apertures
6. **Lens Fourier Transform Property:** Lens in optical system directly computes Fourier transform
7. **Holography Simulation:** Recording and reconstructing from interference patterns
8. **Real Experimental Data:** Compare simulation with actual CD/DVD measurements

---

## Summary of Simulation Ideas

| # | Title | Complexity | Key Feature | Lecture Focus |
|---|-------|-----------|-------------|----------------|
| 1 | Fourier Transform Pair Navigator | High | Bidirectional time-frequency exploration | Lecture 16 (CT FT) |
| 2 | DT Frequency Response Unit Circle Explorer | Medium-High | Pole-zero → frequency response mapping | Lecture 17 (DT FR) |
| 3 | Spectral Windowing and Leakage | High | ECG filtering with cascade design | Lecture 18, 20 (DT Repr, Apps) |
| 4 | Time-Frequency Duality Mapper | High | Unified 4-representation framework | Lecture 19, 16 (Relations) |
| 5 | Phase-Magnitude Separation | Medium | Minimum-phase vs. linear-phase | Lecture 18, 20 (ECG demo) |
| 6 | Fourier Series to Transform Transition | Medium | Limit process as period → ∞ | Lecture 16, 20 (Introduction) |
| 7 | CT/DT Fourier Frequency Mapping | Medium-High | Aliasing and sampling visualization | Lecture 19, 20 (Sampling) |
| 8 | Interactive Diffraction Grating | High | Physics application with real measurements | Lecture 20 (Diffraction, DNA) |

All eight simulations are **novel** and do not duplicate existing simulations in the codebase. They collectively provide comprehensive interactive exploration of:
- Fourier Transform pair relationships (time-frequency duality)
- DT frequency response and filter design via pole-zero placement
- Practical filtering with windowing and spectral analysis
- Sampling theorem and aliasing mechanisms
- Real-world applications (ECG, diffraction, X-ray crystallography)
